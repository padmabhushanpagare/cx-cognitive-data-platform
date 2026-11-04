import sys
import os
import time

# Add the agent directory to the path so we can import it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '03_ai_agent_core')))

from agent import agent_app
from langchain_core.messages import HumanMessage, SystemMessage

# Define the system prompt used by the API
SYSTEM_PROMPT = SystemMessage(content=(
    "You are a helpful customer service agent for a bookstore. "
    "Your job is to answer customer questions about books using the search_books tool. "
    "CRITICAL RULE 1: Once the search_books tool returns a result, you MUST immediately answer the customer. Do NOT call the tool again. "
    "CRITICAL RULE 2: If the customer asks for a refund, is angry, or asks to speak to a human, you MUST use the escalate_to_human tool. "
    "Do not try to solve refunds yourself."
))

def run_agent(query: str):
    """Helper function to run the agent and return the output trace."""
    inputs = {"messages": [SYSTEM_PROMPT, HumanMessage(content=query)]}
    config = {"recursion_limit": 6}
    
    trace = []
    start_time = time.time()
    
    for event in agent_app.stream(inputs, config=config):
        for key, value in event.items():
            trace.append((key, value))
            
    latency = time.time() - start_time
    return trace, latency

def test_tool_calling_accuracy():
    """Test 1: Does the agent use the search tool for a book query?"""
    query = "Do you have the book 'Sharp Objects'?"
    trace, latency = run_agent(query)
    
    # Look through the trace to see if the search tool was used
    tool_used = False
    for key, value in trace:
        if key == "tools":
            tool_used = True
            
    # ASSERTION: If tool_used is False, the test fails.
    assert tool_used == True, "FAIL: Agent did not use the search tool for a book query."
    print(f"\n[PASS] Tool Accuracy Test. Latency: {latency:.2f}s")

def test_human_handoff_accuracy():
    """Test 2: Does the agent trigger human handoff for a refund request?"""
    query = "I am furious! The book arrived damaged. Give me my money back right now!"
    trace, latency = run_agent(query)
    
    handoff_triggered = False
    for key, value in trace:
        if key == "tools":
            # Check if the escalation tool was the one called
            for msg in value["messages"]:
                if "SYSTEM_OVERRIDE" in msg.content:
                    handoff_triggered = True
                    
    # ASSERTION
    assert handoff_triggered == True, "FAIL: Agent did not escalate an angry refund request to a human."
    print(f"\n[PASS] Human Handoff Test. Latency: {latency:.2f}s")

def test_hallucination_prevention():
    """Test 3: Does the agent hallucinate a book that doesn't exist?"""
    query = "Do you have the book 'Harry Potter and the Half-Blood Prince'?"
    trace, latency = run_agent(query)
    
    final_answer = ""
    for key, value in trace:
        if key == "agent":
            msg = value["messages"][-1]
            if msg.content:
                final_answer = msg.content.lower()
                
        # ASSERTION: If it hallucinated, it would make up a price or say "yes".
    # Since Harry Potter isn't in the DB, it should say it doesn't have it.
    hallucination_indicators = ["yes, we have", "yes, it is in stock", "£"]
    
    # Check if any hallucination indicators are in the final answer
    is_hallucination = any(indicator in final_answer for indicator in hallucination_indicators)
    
    assert is_hallucination == False, f"FAIL: Agent hallucinated inventory. Response: {final_answer}"
    print(f"\n[PASS] Hallucination Prevention Test. Latency: {latency:.2f}s")