import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# 1. Load Data
df = pd.read_csv("intent_dataset.csv")
X_text = df["text"].values
y_labels = df["intent"].values

# 2. Train/Test Split (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X_text, y_labels, test_size=0.2, random_state=42, stratify=y_labels)

# 3. Vectorize
vectorizer = TfidfVectorizer(max_features=500)
X_train_vec = vectorizer.fit_transform(X_train).toarray()
X_test_vec = vectorizer.transform(X_test).toarray()

# 4. Encode Labels
label_encoder = LabelEncoder()
y_train_enc = label_encoder.fit_transform(y_train)
y_test_enc = label_encoder.transform(y_test)

# 5. Convert to Tensors
X_train_t = torch.FloatTensor(X_train_vec)
y_train_t = torch.LongTensor(y_train_enc)
X_test_t = torch.FloatTensor(X_test_vec)
y_test_t = torch.LongTensor(y_test_enc)

# 6. Define Model
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

model = IntentClassifier(X_train_vec.shape[1], 64, len(label_encoder.classes_))
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 7. Train
print("Training...")
for epoch in range(100):
    optimizer.zero_grad()
    outputs = model(X_train_t)
    loss = criterion(outputs, y_train_t)
    loss.backward()
    optimizer.step()

# 8. Evaluate on Test Set
print("\n--- EVALUATION ON HELD-OUT TEST SET ---")
model.eval()
with torch.no_grad():
    test_outputs = model(X_test_t)
    _, predicted = torch.max(test_outputs, 1)

print(classification_report(y_test_enc, predicted.numpy(), target_names=label_encoder.classes_))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test_enc, predicted.numpy()))

# 9. Save
torch.save(model.state_dict(), "intent_model.pth")
joblib.dump(vectorizer, "vectorizer.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
print("Model saved.")
