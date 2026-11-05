import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import numpy as np
from train_data import get_data

# 1. Prepare Data
data = get_data()
texts = [x[0] for x in data]
labels = [x[1] for x in data]

# Convert text to numerical vectors using TF-IDF
vectorizer = TfidfVectorizer(max_features=100)
X = vectorizer.fit_transform(texts).toarray()

# Convert labels (strings) to integers (0, 1, 2)
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(labels)

# Convert to PyTorch Tensors
X_tensor = torch.FloatTensor(X)
y_tensor = torch.LongTensor(y)

# 2. Define the Neural Network Architecture
class IntentClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(IntentClassifier, self).__init__()
        # Layer 1: Input to Hidden
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        # Layer 2: Hidden to Output
        self.fc2 = nn.Linear(hidden_size, num_classes)
        
    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

# 3. Initialize Model, Loss Function, and Optimizer
input_size = X.shape[1]
hidden_size = 64
num_classes = len(label_encoder.classes_)

model = IntentClassifier(input_size, hidden_size, num_classes)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 4. Training Loop
print("Training PyTorch Intent Classifier...")
epochs = 200
for epoch in range(epochs):
    optimizer.zero_grad()
    outputs = model(X_tensor)
    loss = criterion(outputs, y_tensor)
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 50 == 0:
        print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

# 5. Save the Model and Vectorizer
print("Training complete! Saving model...")
torch.save(model.state_dict(), "intent_model.pth")
import joblib
joblib.dump(vectorizer, "vectorizer.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
print(f"Model saved. Classes: {label_encoder.classes_}")
