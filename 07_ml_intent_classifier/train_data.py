# A synthetic dataset of BPO customer queries
INTENT_DATA = [
    # Check Order Status
    ("where is my order", "check_order"),
    ("can you track my package", "check_order"),
    ("status of order ORD-5002", "check_order"),
    ("did my item ship yet", "check_order"),
    ("tracking number for my delivery", "check_order"),
    
    # Refund / Escalation
    ("I want a refund", "escalate"),
    ("this is unacceptable, give me my money back", "escalate"),
    ("let me speak to a manager", "escalate"),
    ("my item arrived damaged", "escalate"),
    ("I am furious, cancel my order", "escalate"),
    
    # General Info
    ("what is your return policy", "general"),
    ("do you ship internationally", "general"),
    ("how can I contact support", "general"),
    ("what are your business hours", "general")
]

def get_data():
    return INTENT_DATA
