import os
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from agent import agent_app 
from ml_router import predict_intent

app = FastAPI(title="Enterprise CX Platform API")

# Read DB config from Environment Variables (Docker)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cx_secret_password")
DB_NAME = os.getenv("DB_NAME", "cx_platform")
class ChatRequest(BaseModel):
    message: str
    session_id: str  # <--- NEW: Required to track conversation memory
        customer_id: str = "CUST-1001" # Defaulting to a valid customer for testing

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


from ml_router import predict_intent

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. ML ROUTING with Confidence Threshold
    predicted_intent, confidence = predict_intent(request.message)
    print(f"\n[ML ROUTER] Detected Intent: {predicted_intent} (Confidence: {confidence:.2f})")
    
    # If the model is less than 60% sure, route to a human to be safe
    if confidence < 0.60:
        predicted_intent = "escalate"
        print("[ML ROUTER] Low confidence, forcing escalation.")

    # 2. DETERMINISTIC ROUTING: If angry, bypass LLM and escalate immediately
    if predicted_intent == "escalate":
        try:
            conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user="admin", password="cx_secret_password", dbname="cx_platform")
            cursor = conn.cursor()
            # Actually insert and commit
            cursor.execute("INSERT INTO fact_handoffs (customer_message, status) VALUES (%s, 'OPEN')", (request.message,))
            conn.commit()
            conn.close()
            
            # Only return success if the DB transaction succeeded
            final_response = "I understand you are frustrated. I am transferring you to a human agent immediately."
            log_to_db(request.message, final_response, True)
            return ChatResponse(response=final_response, requires_human=True)
            
        except Exception as e:
            print(f"CRITICAL: Ticket creation failed: {e}")
            # Honest failure to the user
            final_response = "I apologize, but our ticketing system is currently down. Please try again later or call our support line."
            log_to_db(request.message, final_response, True)
            return ChatResponse(response=final_response, requires_human=False) # Don't say we transferred if we didn't

    # 3. GENERAL ROUTING (No LLM needed for simple policy questions)
    if predicted_intent == "general":
        final_response = "For general inquiries, please visit our FAQ page at example.com/faq."
        log_to_db(request.message, final_response, False)
        return ChatResponse(response=final_response, requires_human=False)

    # 4. LLM ROUTING: For order tracking
    system_prompt = SystemMessage(content=(
        f"You are a helpful e-commerce customer service agent. The customer's ID is {request.customer_id}. "
        "Your job is to answer questions about their orders using the check_order_status tool. "
        "CRITICAL: You MUST use the customer's ID when checking order status. "
        "CRITICAL: Once the tool returns the order status, answer the customer immediately. "
        "Do not make up order statuses."
    ))

    config = {"configurable": {"thread_id": request.session_id}, "recursion_limit": 6}
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