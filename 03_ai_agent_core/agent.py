import os
import psycopg2
from typing import Annotated, TypedDict
from langchain_core.tools import tool
from llm_factory import get_chat_model, get_embedding_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 1. NEW TOOL: Check Order Status
@tool
def check_order_status(order_id: str) -> str:
    """Use this tool to look up the status, amount, and customer of an order. The user must provide an order ID (e.g., ORD-5001)."""
    print(f"\n[AGENT ACTION] Querying PostgreSQL for Order: {order_id}")
    
    # Read DB config from environment variables (Docker)
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5434")
    
    try:
        conn = psycopg2.connect(
            host=db_host, port=db_port, user="admin", 
            password="cx_secret_password", dbname="cx_platform"
        )
        cursor = conn.cursor()
        
        # Use a JOIN to get both order info and customer name
        query = """
            SELECT o.order_id, c.name, o.status, o.amount, o.order_date 
            FROM fact_orders o
            JOIN dim_customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = %s;
        """
        # The comma after order_id is crucial for Python to pass it as a tuple
        cursor.execute(query, (order_id.strip().upper(),)) 
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return f"Order {result[0]} for {result[1]}: Status is '{result[2]}'. Amount: ${result[3]}. Ordered on: {result[4]}."
        else:
            return f"Order {order_id} not found in our system."
            
    except Exception as e:
        return f"Database error: {e}"

# 2. NEW TOOL: Escalate to Human
@tool
def escalate_to_human(reason: str) -> str:
    """Use this tool ONLY if the customer is angry, requests a refund, or asks for a human/manager."""
    print(f"\n[AGENT ACTION] ESCALATING TO HUMAN. Reason: {reason}")
    return "SYSTEM_OVERRIDE: The user has been transferred to a human agent. STOP generating text and end the conversation."

# 3. Initialize LLM and bind tools
print("Initializing LLM via Factory...")
llm = get_chat_model()
tools = [check_order_status, escalate_to_human] # <--- Updated tools list
llm_with_tools = llm.bind_tools(tools)

# 4. Define the Nodes
def agent_node(state: AgentState):
    print("\n--- LLM THINKING ---")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# 5. Build the Graph
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

memory = MemorySaver()
agent_app = graph_builder.compile(checkpointer=memory)
print("Agent successfully compiled!")

# 6. Local Testing
if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, SystemMessage
    
    print("\n--- STARTING CUSTOMER INTERACTION ---")
    # We are testing a specific order ID from our generated data
    customer_query = "Hi, can you check the status of my order ORD-5003?"
    print(f"Customer: {customer_query}")
    
    system_prompt = SystemMessage(content=(
        "You are a helpful e-commerce customer service agent. "
        "Your job is to answer customer questions about their orders using the check_order_status tool. "
        "CRITICAL RULE 1: Once the tool returns the order status, answer the customer immediately. Do not call the tool again. "
        "CRITICAL RULE 2: If the customer is angry, asks for a refund, or asks for a human, use the escalate_to_human tool. "
    ))
    
    config = {"configurable": {"thread_id": "test-123"}, "recursion_limit": 6}
    inputs = {"messages": [system_prompt, HumanMessage(content=customer_query)]}
    
    for event in agent_app.stream(inputs, config=config):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][-1]
                if msg.tool_calls:
                    print(f"Decided to use tool: {msg.tool_calls[0]['name']}")
                elif msg.content:
                    print(f"Final Answer to Customer:\n{msg.content}")
            elif key == "tools":
                print(f"[TOOLS] Output returned to agent.")