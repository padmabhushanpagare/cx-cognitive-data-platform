from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import our compiled LangGraph agent from agent.py
from agent import agent_app 

app = FastAPI(title="CX Cognitive Data Platform API")

# Define the structure of the data coming from the frontend
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    requires_human: bool

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Receives a user message, runs it through the LangGraph agent, and returns the answer.
    """
    # 1. Define the system prompt
    system_prompt = SystemMessage(content=(
        "You are a helpful customer service agent for a bookstore. "
        "Your job is to answer customer questions about books using the search_books tool. "
        "CRITICAL RULE 1: Once the search_books tool returns a result, you MUST immediately answer the customer. Do NOT call the tool again. "
        "CRITICAL RULE 2: If the customer asks for a refund, is angry, or asks to speak to a human, you MUST use the escalate_to_human tool. "
        "Do not try to solve refunds yourself."
    ))

    # 2. Package the messages
    inputs = {"messages": [system_prompt, HumanMessage(content=request.message)]}
    config = {"recursion_limit": 6}
    
    final_response = ""
    requires_human = False
    
    # 3. Run the graph
    for event in agent_app.stream(inputs, config=config):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][-1]
                # If the agent generated a final text response
                if msg.content:
                    final_response = msg.content
            elif key == "tools":
                # Check if the tool called was the escalation tool
                tool_messages = value["messages"]
                for tool_msg in tool_messages:
                    if "SYSTEM_OVERRIDE" in tool_msg.content:
                        requires_human = True
                        final_response = "I am transferring you to a human agent now. Please hold."
    
    return ChatResponse(response=final_response, requires_human=requires_human)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
