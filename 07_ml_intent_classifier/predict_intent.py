import torch
import torch.nn as nn
import joblib

# Load the saved artifacts
class IntentClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(IntentClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)
    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

vectorizer = joblib.load("vectorizer.pkl")
label_encoder = joblib.load("label_encoder.pkl")
input_size = len(vectorizer.get_feature_names_out())
model = IntentClassifier(input_size, 64, len(label_encoder.classes_))
model.load_state_dict(torch.load("intent_model.pth"))
model.eval()

def predict_intent(text):
    # Preprocess
    X = vectorizer.transform([text]).toarray()
    X_tensor = torch.FloatTensor(X)
    
    # Predict
    with torch.no_grad():
        output = model(X_tensor)
        _, predicted = torch.max(output.data, 1)
        
    return label_encoder.inverse_transform(predicted.numpy())[0]

if __name__ == "__main__":
    test_queries = [
        "I need a refund right now!",
        "where is my package?",
        "do you guys ship to Europe?"
    ]
    print("\n--- TESTING ML MODEL ---")
    for q in test_queries:
        print(f"Query: '{q}' -> Predicted Intent: {predict_intent(q)}")
