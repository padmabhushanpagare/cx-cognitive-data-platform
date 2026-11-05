import os
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from agent import agent_app 

app = FastAPI(title="Enterprise CX Platform API")

# Read DB config from Environment Variables (Docker)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")

class ChatRequest(BaseModel):
    message: str
    session_id: str  # <--- NEW: Required to track conversation memory

class ChatResponse(BaseModel):
    response: str
    requires_human: bool

def log_to_db(user_msg: str, ai_msg: str, escalated: bool):
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user="admin", 
            password="cx_secret_password", dbname="cx_platform"
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id SERIAL PRIMARY KEY,
                user_message TEXT,
                ai_response TEXT,
                escalated BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute(
            "INSERT INTO conversation_logs (user_message, ai_response, escalated) VALUES (%s, %s, %s);",
            (user_msg, ai_msg, escalated)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database logging failed: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    system_prompt = SystemMessage(content=(
        "You are a helpful e-commerce customer service agent. "
        "Your job is to answer customer questions about their orders using the check_order_status tool. "
        "CRITICAL RULE 1: Once the tool returns the order status, answer the customer immediately. Do not call the tool again. "
        "CRITICAL RULE 2: If the customer is angry, asks for a refund, or asks for a human, use the escalate_to_human tool. "
        "Do not make up order statuses. Only use the tool."
    ))

    # Pass the session_id as the thread_id to LangGraph memory
    config = {"configurable": {"thread_id": request.session_id}, "recursion_limit": 6}
    
    # If it's a new session, we inject the System Prompt. If not, LangGraph remembers it.
    state = agent_app.get_state(config)
    if not state.values:
        inputs = {"messages": [system_prompt, HumanMessage(content=request.message)]}
    else:
        inputs = {"messages": [HumanMessage(content=request.message)]}
    
    final_response = ""
    requires_human = False
    
    for event in agent_app.stream(inputs, config=config):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][-1]
                if msg.content:
                    final_response = msg.content
            elif key == "tools":
                for tool_msg in value["messages"]:
                    if "SYSTEM_OVERRIDE" in tool_msg.content:
                        requires_human = True
                        final_response = "I am transferring you to a human agent now. Please hold."
    
    log_to_db(request.message, final_response, requires_human)
    return ChatResponse(response=final_response, requires_human=requires_human)

@app.get("/health")
def health_check():
    return {"status": "healthy"}