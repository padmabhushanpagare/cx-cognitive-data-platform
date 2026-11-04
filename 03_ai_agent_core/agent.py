import os
from typing import Annotated, TypedDict
from langchain_chroma import Chroma
from langchain_core.tools import tool
from llm_factory import get_chat_model, get_embedding_model # <--- USE THE FACTORY

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

print("Loading Vector Database...")
embeddings = get_embedding_model()
# FORCE THE PATH TO BE RELATIVE TO THIS SCRIPT, NO MATTER WHERE IT IS RUN FROM
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

@tool
def search_books(query: str) -> str:
    """Search the bookstore inventory for books by title or topic."""
    print(f"\n[AGENT ACTION] Searching database for: '{query}'")
    results = vectorstore.similarity_search(query, k=3)
    
    # DEBUGGING: Print what the database actually found
    print(f"[DEBUG] Found {len(results)} raw results.")
    for i, doc in enumerate(results):
        print(f"[DEBUG] Result {i+1}: {doc.page_content}")
    
    if not results:
        return "No books found matching that query."
    
    formatted_results = "\n".join([doc.page_content for doc in results])
    return f"Found the following books in inventory:\n{formatted_results}"

@tool
def escalate_to_human(reason: str) -> str:
    """Use this tool ONLY if the customer is angry, requests a refund, or asks for a human/manager. Do NOT use this for simple book searches."""
    print(f"\n[AGENT ACTION] ESCALATING TO HUMAN. Reason: {reason}")
    # In a real system, this would trigger a webhook to Zendesk or Salesforce
    return "SYSTEM_OVERRIDE: The user has been transferred to a human agent. STOP generating text and end the conversation."

print("Initializing LLM via Factory...")
llm = get_chat_model() # <--- FACTORY DECIDES WHICH ONE
tools = [search_books, escalate_to_human] # <--- UPDATED
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    print("\n--- LLM THINKING ---")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

print("Building LangGraph...")
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", ToolNode(tools))

graph_builder.add_edge(START, "agent")

def route_after_agent(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

graph_builder.add_conditional_edges("agent", route_after_agent)
graph_builder.add_edge("tools", "agent")

agent_app = graph_builder.compile()
print("Agent successfully compiled!")

from langchain_core.messages import SystemMessage, HumanMessage

if __name__ == "__main__":
    print("\n--- STARTING CUSTOMER INTERACTION ---")
    #customer_query = "Hi, do you have the book Sapiens? And how much does it cost?"
    customer_query = "This is unacceptable! I want a refund right now and I want to speak to a manager!"
    print(f"Customer: {customer_query}")
    
    # 1. THE SYSTEM PROMPT (The Rulebook for the Agent)
    system_prompt = SystemMessage(content=(
        "You are a helpful customer service agent for a bookstore. "
        "Your job is to answer customer questions about books using the search_books tool. "
        "CRITICAL RULE 1: Once the search_books tool returns a result, you MUST immediately answer the customer. Do NOT call the tool again. "
        "CRITICAL RULE 2: If the tool returns 'No books found', you MUST tell the customer we don't have it. Do NOT search again. "
        "CRITICAL RULE 3: If the customer asks for a refund, is angry, or asks to speak to a human, you MUST use the escalate_to_human tool. "
        "Do not try to solve refunds yourself."
    ))
    
    # 2. Pack the state with the rules AND the user's question
    inputs = {"messages": [system_prompt, HumanMessage(content=customer_query)]}
    
    # 3. Add a recursion_limit (Safety Net: Max 5 steps)
    # If it hits 5 steps, it forces the graph to stop.
    config = {"recursion_limit": 5}
    
    for event in agent_app.stream(inputs, config=config):
        for key, value in event.items():
            if key == "agent":
                print(f"\n[{key.upper()}]")
                msg = value["messages"][-1]
                if msg.tool_calls:
                    print(f"Decided to use tool: {msg.tool_calls[0]['name']}")
                elif msg.content:
                    print(f"Final Answer to Customer:\n{msg.content}")
            elif key == "tools":
                print(f"\n[{key.upper()}] Output returned to agent.")