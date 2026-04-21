import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib

# Load Sparkov dataset (download from Kaggle and place in this folder)
# kaggle.com/datasets/kartik2112/fraud-detection
df = pd.read_csv("fraudTrain.csv")

# Select meaningful features
features = ["amt", "category", "hour", "distance"]

# Engineer features
df["hour"] = pd.to_datetime(df["trans_date_trans_time"]).dt.hour

# Distance between cardholder and merchant
df["distance"] = np.sqrt(
    (df["lat"] - df["merch_lat"])**2 + (df["long"] - df["merch_long"])**2
) * 111  # approx km

# Encode merchant category
le = LabelEncoder()
df["category_enc"] = le.fit_transform(df["category"])

# Save encoder for use in API
joblib.dump(le, "category_encoder.pkl")

X = df[["amt", "category_enc", "hour", "distance", "is_fraud"]].dropna()

# Train Isolation Forest
model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
model.fit(X[["amt", "category_enc", "hour", "distance"]])

joblib.dump(model, "fraud_model.pkl")
print("Model trained and saved as fraud_model.pkl")
