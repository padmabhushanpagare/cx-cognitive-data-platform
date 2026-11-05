import torch
import torch.nn as nn
import joblib
import os

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

# 1. Define absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "vectorizer.pkl")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "intent_model.pth")
ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "label_encoder.pkl")

# 2. Print diagnostics BEFORE loading
print(f"\n--- ML ROUTER DIAGNOSTICS ---")
print(f"Loading from: {ARTIFACTS_DIR}")
print(f"Vectorizer exists: {os.path.exists(VECTORIZER_PATH)}")
print(f"Model exists: {os.path.exists(MODEL_PATH)}")

# 3. Load the artifacts
vectorizer = joblib.load(VECTORIZER_PATH)
label_encoder = joblib.load(ENCODER_PATH)

# 4. Verify the feature size
input_size = len(vectorizer.get_feature_names_out())
print(f"--- ML ROUTER LOADED: {input_size} FEATURES ---\n")

# 5. Initialize and load the model weights
model = IntentClassifier(input_size, 64, len(label_encoder.classes_))
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
model.eval()

def predict_intent(text: str):
    X = vectorizer.transform([text]).toarray()
    X_tensor = torch.FloatTensor(X)
    
    with torch.no_grad():
        output = model(X_tensor)
        probabilities = torch.nn.functional.softmax(output, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
        
    intent = label_encoder.inverse_transform(predicted.numpy())[0]
    return intent, confidence.item()