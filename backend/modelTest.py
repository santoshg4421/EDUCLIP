import pickle
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import pandas as pd

# Step 1: Load model and vectorizer
with open("model.pkl", "rb") as f:
    vectorizer, model = pickle.load(f)

# Step 2: Load your test dataset
# Using video_metadata.csv from the data folder
df = pd.read_csv("../data/video_metadata.csv")  # Path to your actual dataset

# Handle missing values by filling with empty strings
df = df.fillna('')

# Take only the first 10 rows for testing to avoid issues
df = df.head(10)

# Combine Title and Description as text for testing
X_test = df["Title"] + " " + df["Description"]
# Since we don't have labels, we'll create dummy labels for demonstration
y_test = [1] * len(df)  # Assuming all are educational (you can modify this based on your needs)

print(f"Testing with {len(df)} samples")
print("Sample text data:")
for i, text in enumerate(X_test[:3]):
    print(f"  {i+1}: {text[:100]}...")  # Show first 100 characters

# Step 3: Transform text using vectorizer
X_test_vec = vectorizer.transform(X_test)

# Step 4: Make predictions
y_pred = model.predict(X_test_vec)

# Step 5: Evaluate performance
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))
print("F1-score:", f1_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
