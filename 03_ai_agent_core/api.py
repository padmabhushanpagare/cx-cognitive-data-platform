import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from agent import agent_app 

app = FastAPI(title="Enterprise CX Platform API")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    requires_human: bool

def log_to_db(user_msg: str, ai_msg: str, escalated: bool):
    """Saves the conversation to PostgreSQL for analytics."""
    try:
        conn = psycopg2.connect(
            host="localhost", port="5434", user="admin", 
            password="cx_secret_password", dbname="cx_platform"
        )
        cursor = conn.cursor()
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id SERIAL PRIMARY KEY,
                user_message TEXT,
                ai_response TEXT,
                escalated BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Insert the log
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
        "You are a helpful customer service agent for a bookstore. "
        "Your job is to answer customer questions about books using the search_books tool. "
        "CRITICAL RULE 1: Once the search_books tool returns a result, you MUST immediately answer the customer. Do NOT call the tool again. "
        "CRITICAL RULE 2: If the tool returns 'No books found', you MUST tell the customer we don't have it. Do NOT search again. "
        "CRITICAL RULE 3: If the customer asks for a refund, is angry, or asks to speak to a human, you MUST use the escalate_to_human tool. "
        "Do not try to solve refunds yourself."
    ))

    inputs = {"messages": [system_prompt, HumanMessage(content=request.message)]}
    config = {"recursion_limit": 6}
    
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
    
    # Log the interaction to PostgreSQL before returning
    log_to_db(request.message, final_response, requires_human)
    
    return ChatResponse(response=final_response, requires_human=requires_human)

@app.get("/health")
def health_check():
    return {"status": "healthy"}