from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import logging
import datetime

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

app = FastAPI(title="Fraud Detection API")
model = joblib.load("fraud_model.pkl")

class Transaction(BaseModel):
    amount: float
    merchant_category: str
    hour_of_day: int
    distance_from_home_km: float
    is_foreign_transaction: int

CATEGORY_MAP = {
    "grocery": 0, "online_retail": 1, "gas": 2,
    "entertainment": 3, "travel": 4, "other": 5
}

@app.get("/")
def root():
    return {"message": "Fraud Detection API is running"}

@app.post("/predict")
def predict(txn: Transaction):
    category = CATEGORY_MAP.get(txn.merchant_category, 5)
    features = np.array([[txn.amount, category, txn.hour_of_day,
                          txn.distance_from_home_km, txn.is_foreign_transaction]])
    score = model.decision_function(features)[0]
    prediction = int(model.predict(features)[0])
    is_fraud = prediction == -1

    logging.info({
        "timestamp": str(datetime.datetime.now()),
        "amount": txn.amount,
        "merchant_category": txn.merchant_category,
        "hour_of_day": txn.hour_of_day,
        "distance_from_home_km": txn.distance_from_home_km,
        "is_foreign_transaction": txn.is_foreign_transaction,
        "fraud_score": round(score, 4),
        "is_fraud": is_fraud
    })

    return {
        "is_fraud": is_fraud,
        "fraud_score": round(score, 4),
        "merchant_category": txn.merchant_category,
        "amount": txn.amount
    }

@app.get("/health")
def health():
    return {"status": "ok"}
