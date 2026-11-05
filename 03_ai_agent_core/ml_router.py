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

# Load artifacts relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
vectorizer = joblib.load(os.path.join(BASE_DIR, "vectorizer.pkl"))
label_encoder = joblib.load(os.path.join(BASE_DIR, "label_encoder.pkl"))

input_size = len(vectorizer.get_feature_names_out())
model = IntentClassifier(input_size, 64, len(label_encoder.classes_))
model.load_state_dict(torch.load(os.path.join(BASE_DIR, "intent_model.pth"), map_location=torch.device('cpu')))
model.eval()

def predict_intent(text: str) -> str:
    X = vectorizer.transform([text]).toarray()
    X_tensor = torch.FloatTensor(X)
    
    with torch.no_grad():
        output = model(X_tensor)
        _, predicted = torch.max(output.data, 1)
        
    return label_encoder.inverse_transform(predicted.numpy())[0]