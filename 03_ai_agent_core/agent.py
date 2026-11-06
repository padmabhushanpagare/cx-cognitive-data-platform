import os
from typing import Annotated, TypedDict
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from llm_factory import get_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver
from db import get_db_connection
from langchain_core.messages import SystemMessage

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tool_call_count: int

@tool
def check_order_status(order_id: str, config: RunnableConfig) -> str:
    """Use this tool to look up the status of an order. Requires the order_id (e.g., ORD-5001)."""
    customer_id = config.get("configurable", {}).get("customer_id", "UNKNOWN")
    
    # Normalize order ID to handle LLM hallucinations like "ORD 5003"
    clean_order_id = order_id.strip().upper().replace(" ", "-")
    print(f"\n[AGENT ACTION] Querying Order: '{clean_order_id}' for Customer: '{customer_id}'")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT o.order_id, c.name, o.status, o.amount, o.order_date 
                FROM fact_orders o
                JOIN dim_customers c ON o.customer_id = c.customer_id
                WHERE o.order_id = %s AND o.customer_id = %s;
            """
            cursor.execute(query, (clean_order_id, customer_id.strip().upper()))
            result = cursor.fetchone()
            cursor.close()
        
        if result:
            return f"Order {result[0]} for {result[1]}: Status is '{result[2]}'. Amount: ${result[3]}."
        else:
            return f"Order {clean_order_id} not found, or you are not authorized to view it."
    except Exception as e:
        return f"Database error: {e}"

@tool
def escalate_to_human(reason: str, config: RunnableConfig) -> str:
    """Use this tool ONLY if the customer is angry, requests a refund, or asks for a human."""
    customer_id = config.get("configurable", {}).get("customer_id", "UNKNOWN")
    print(f"\n[AGENT ACTION] ESCALATING TO HUMAN. Reason: {reason} for {customer_id}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO fact_handoffs (customer_message, status) VALUES (%s, 'OPEN')", 
                (f"[{customer_id}] Escalation: {reason}",)
            )
            conn.commit()
            cursor.close()
        return "SYSTEM_OVERRIDE: A ticket has been created. Tell the user they are being transferred."
    except Exception as e:
        print(f"CRITICAL: Ticket creation failed: {e}")
        return "SYSTEM_ERROR: The ticketing system is down. Apologize."

llm = get_chat_model()
tools = [check_order_status, escalate_to_human]
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    count = state.get("tool_call_count", 0)
    
    if count >= 1:
        print("\n--- LLM THINKING (Forcing Final Answer) ---")
        messages = state["messages"] + [SystemMessage(content="You have already used the tool. Do NOT use it again. Provide your final answer to the user based on the tool output.")]
        response = llm.invoke(messages)
        return {"messages": [response], "tool_call_count": count}
        
    print("\n--- LLM THINKING ---")
    response = llm_with_tools.invoke(state["messages"])
    if response.tool_calls:
        count += 1
    return {"messages": [response], "tool_call_count": count}

graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", ToolNode(tools))
graph_builder.add_edge(START, "agent")

def route_after_agent(state: AgentState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    return "tools"

graph_builder.add_conditional_edges("agent", route_after_agent)
graph_builder.add_edge("tools", "agent")

# STRICT URI CONSTRUCTION
DB_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    _memory_ctx = PostgresSaver.from_conn_string(DB_URI)
    memory = _memory_ctx.__enter__()
    memory.setup() 
    agent_app = graph_builder.compile(checkpointer=memory)
    print("✅ Agent successfully compiled with PostgresSaver!")
except Exception as e:
    print(f"⚠️ Failed to connect PostgresSaver: {e}. Falling back to in-memory.")
    from langgraph.checkpoint.memory import MemorySaver
    agent_app = graph_builder.compile(checkpointer=MemorySaver())