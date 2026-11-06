from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from agent import agent_app 
from ml_router import predict_intent
from db import get_db_connection

app = FastAPI(title="Enterprise CX Platform API")

class ChatRequest(BaseModel):
    message: str
    session_id: str
    # Must be provided by the authenticated frontend
    customer_id: str 

class ChatResponse(BaseModel):
    response: str
    requires_human: bool

def log_to_db(user_msg: str, ai_msg: str, escalated: bool):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversation_logs (user_message, ai_response, escalated) VALUES (%s, %s, %s);",
                (user_msg, ai_msg, escalated)
            )
            conn.commit()
            cursor.close()
    except Exception as e:
        print(f"Database logging failed: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    predicted_intent, confidence = predict_intent(request.message)
    
    # 1. ML Router (Fast Path)
    if predicted_intent == "escalate" or confidence < 0.60:
        print(f"\n[ML ROUTER] Escalation triggered for {request.customer_id} (Confidence: {confidence:.2f})")
        final_response = "I understand you are frustrated. I am transferring you to a human agent immediately."
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                ticket_msg = f"[{request.customer_id}] [ML Router] {request.message}"
                cursor.execute("INSERT INTO fact_handoffs (customer_message, status) VALUES (%s, 'OPEN')", (ticket_msg,))
                conn.commit()
                cursor.close()
            
            log_to_db(request.message, final_response, True)
            return ChatResponse(response=final_response, requires_human=True)
            
        except Exception as e:
            print(f"CRITICAL: Ticket creation failed: {e}")
            final_response = "I apologize, but our ticketing system is currently down. Please try again later."
            log_to_db(request.message, final_response, True)
            return ChatResponse(response=final_response, requires_human=False)

    # 2. General Path (FAQ)
    if predicted_intent == "general":
        final_response = "For general inquiries, please visit our FAQ page at example.com/faq."
        log_to_db(request.message, final_response, False)
        return ChatResponse(response=final_response, requires_human=False)

    # 3. LLM Agent Path
    system_prompt = SystemMessage(content=(
        "You are a helpful e-commerce customer service agent. "
        "Your job is to answer questions about their orders using the check_order_status tool. "
        "CRITICAL RULE 1: You must use the check_order_status tool **only once** per user query. "
        "After the tool returns a result, you must immediately provide a final answer. "
        "CRITICAL RULE 2: If the tool returns 'not found' or 'unauthorized', say exactly: 'I could not find that order associated with your account.' Do not use the word 'error'. "
        "CRITICAL RULE 3: If the customer asks for a refund or human, use the escalate_to_human tool. "
    ))

    config = {
        "configurable": {
            "thread_id": request.session_id,
            "customer_id": request.customer_id 
        }, 
        "recursion_limit": 10
    }
    
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
    
    # Fallback if LLM fails to generate text
    if not final_response:
        final_response = "I apologize, but I am having trouble processing that request. Could you please provide the order ID clearly?"

    log_to_db(request.message, final_response, requires_human)
    return ChatResponse(response=final_response, requires_human=requires_human)

@app.get("/health")
def health_check():
    return {"status": "healthy"}