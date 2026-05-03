import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np

mock_model = MagicMock()
mock_model.decision_function.return_value = np.array([-0.25])
mock_model.predict.return_value = np.array([-1])

with patch("joblib.load", return_value=mock_model):
    from main import app

client = TestClient(app)

VALID_TRANSACTION = {
    "amount": 4500.0,
    "merchant_category": "online_retail",
    "hour_of_day": 2,
    "distance_from_home_km": 1200.0,
    "is_foreign_transaction": 1,
}

NORMAL_TRANSACTION = {
    "amount": 25.0,
    "merchant_category": "grocery",
    "hour_of_day": 14,
    "distance_from_home_km": 5.0,
    "is_foreign_transaction": 0,
}


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRootEndpoint:
    def test_root_returns_message(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Fraud Detection API" in response.json()["message"]


class TestPredictEndpoint:
    def test_predict_returns_200(self):
        response = client.post("/predict", json=VALID_TRANSACTION)
        assert response.status_code == 200

    def test_predict_response_fields(self):
        response = client.post("/predict", json=VALID_TRANSACTION)
        data = response.json()
        assert "is_fraud" in data
        assert "fraud_score" in data
        assert "merchant_category" in data
        assert "amount" in data

    def test_predict_fraud_detection(self):
        mock_model.predict.return_value = np.array([-1])
        mock_model.decision_function.return_value = np.array([-0.5])
        response = client.post("/predict", json=VALID_TRANSACTION)
        data = response.json()
        assert data["is_fraud"] is True

    def test_predict_normal_transaction(self):
        mock_model.predict.return_value = np.array([1])
        mock_model.decision_function.return_value = np.array([0.1])
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        data = response.json()
        assert data["is_fraud"] is False

    def test_predict_unknown_category_defaults(self):
        txn = VALID_TRANSACTION.copy()
        txn["merchant_category"] = "unknown_category"
        response = client.post("/predict", json=txn)
        assert response.status_code == 200

    def test_predict_model_receives_correct_features(self):
        mock_model.predict.return_value = np.array([1])
        mock_model.decision_function.return_value = np.array([0.05])
        client.post("/predict", json=VALID_TRANSACTION)
        call_args = mock_model.decision_function.call_args[0][0]
        assert call_args.shape == (1, 5)

    def test_predict_invalid_payload_returns_422(self):
        response = client.post("/predict", json={"amount": "not_a_number"})
        assert response.status_code == 422

    def test_predict_empty_payload_returns_422(self):
        response = client.post("/predict", json={})
        assert response.status_code == 422
