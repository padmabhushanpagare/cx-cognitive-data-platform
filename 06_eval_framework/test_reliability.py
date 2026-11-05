import sys
import os
import pytest
from unittest.mock import patch

# Add the agent directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '03_ai_agent_core')))

# Import the ML Router
from ml_router import predict_intent

def test_ml_router_escalation():
    """Test 1: Does the PyTorch model correctly identify angry/refund messages?"""
    queries = [
        "I want a refund right now!",
        "This is unacceptable, let me speak to a manager.",
        "My item arrived damaged, give me my money back."
    ]
    for q in queries:
        intent, confidence = predict_intent(q)  # <--- UNPACK TUPLE
        assert intent == "escalate", f"FAIL: ML Router did not escalate query: '{q}'"

def test_ml_router_order_status():
    """Test 2: Does the PyTorch model correctly identify order tracking?"""
    queries = [
        "Where is my order ORD-5003?",
        "Can you track my package?",
        "Did my item ship yet?"
    ]
    for q in queries:
        intent, confidence = predict_intent(q)  # <--- UNPACK TUPLE
        assert intent == "check_order", f"FAIL: ML Router did not route to check_order: '{q}'"

def test_ml_router_general():
    """Test 3: Does the PyTorch model correctly identify general questions?"""
    queries = [
        "What is your return policy?",
        "Do you ship internationally?"
    ]
    for q in queries:
        intent, confidence = predict_intent(q)  # <--- UNPACK TUPLE
        assert intent == "general", f"FAIL: ML Router did not route to general: '{q}'"
def test_agent_order_tool():
    """Test 4: Does the database tool correctly retrieve order data from PostgreSQL?"""
    # Import the tool directly
    from agent import check_order_status
    
    # Test a known order from our synthetic data
    result = check_order_status.invoke("ORD-5003")
    
    # Assert that the tool found the order and returned the correct status
    assert "Order ORD-5003" in result
    assert "Delayed" in result
    assert "not found" not in result