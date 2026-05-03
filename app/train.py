import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib

df = pd.read_csv("fraudTrain.csv")

df["hour"] = pd.to_datetime(df["trans_date_trans_time"]).dt.hour

df["distance"] = np.sqrt(
    (df["lat"] - df["merch_lat"])**2 + (df["long"] - df["merch_long"])**2
) * 111  # approx km

le = LabelEncoder()
df["category_enc"] = le.fit_transform(df["category"])

joblib.dump(le, "category_encoder.pkl")

FEATURE_COLS = ["amt", "category_enc", "hour", "distance", "is_fraud"]
X = df[FEATURE_COLS].dropna()

model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
model.fit(X[FEATURE_COLS])

joblib.dump(model, "fraud_model.pkl")
print(f"Model trained on {len(FEATURE_COLS)} features: {FEATURE_COLS}")
print("Saved as fraud_model.pkl")
