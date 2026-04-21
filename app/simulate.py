import requests
import random
import time

API_URL = "http://localhost:8000/predict"

CATEGORIES = ["grocery", "online_retail", "gas", "entertainment", "travel", "other"]

def generate_transaction():
    is_fraud_sim = random.random() < 0.1  # 10% fraud rate in simulation

    if is_fraud_sim:
        return {
            "amount": round(random.uniform(800, 5000), 2),
            "merchant_category": random.choice(["online_retail", "travel"]),
            "hour_of_day": random.randint(0, 4),       # unusual hour
            "distance_from_home_km": random.uniform(800, 3000),
            "is_foreign_transaction": 1
        }
    else:
        return {
            "amount": round(random.uniform(5, 300), 2),
            "merchant_category": random.choice(CATEGORIES),
            "hour_of_day": random.randint(8, 21),
            "distance_from_home_km": random.uniform(0, 50),
            "is_foreign_transaction": 0
        }

if __name__ == "__main__":
    print("Starting transaction simulation... Press Ctrl+C to stop.")
    while True:
        txn = generate_transaction()
        try:
            response = requests.post(API_URL, json=txn)
            result = response.json()
            status = "FRAUD" if result["is_fraud"] else "OK"
            print(f"[{status}] Amount: {txn['amount']} | Category: {txn['merchant_category']} | Score: {result['fraud_score']}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
