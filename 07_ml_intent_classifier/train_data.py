import random

random.seed(42)

# Base templates
order_templates = ["where is my order {}", "track package {}", "status of {}", "did {} ship", "check delivery for {}", "i need an update on {}", "what happened to order {}", "where is {}"]
refund_templates = ["i want a refund for {}", "cancel order {}", "this is broken {}", "i need my money back for {}", "return {}", "speak to a manager about {}", "furious with order {}", "damaged item {}"]
general_templates = ["what is your return policy", "do you ship internationally", "how do i contact support", "business hours", "how does warranty work", "can i change my address"]

data = []

# Generate order queries
for i in range(5000, 5100):
    for template in order_templates:
        data.append((template.format(f"ORD-{i}"), "check_order"))

# Generate refund/escalation queries
for i in range(5000, 5100):
    for template in refund_templates:
        data.append((template.format(f"ORD-{i}"), "escalate"))

# Generate general queries
for _ in range(100):
    for template in general_templates:
        data.append((template, "general"))

random.shuffle(data)

# Save to a CSV for proper splitting
import pandas as pd
df = pd.DataFrame(data, columns=["text", "intent"])
df.to_csv("intent_dataset.csv", index=False)

print(f"Generated {len(df)} rows of data and saved to intent_dataset.csv")