import pytest
from fastapi.testclient import TestClient
from src.app import app
import os
from src.config import APP_LOG_PATH

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "model_loaded" in data
    assert "uptime_seconds" in data
    assert "timestamp" in data


def test_predict_endpoint_legitimate():
    payload = {
        "Transaction_ID": "TXN_TEST_001",
        "Transaction_Amount_INR": 150.0,
        "Transaction_Hour": 14,
        "Payment_Method": "UPI",
        "Transaction_Channel": "POS",
        "Device_Status": "Known",
        "Location_Type": "Domestic",
        "Transactions_Last_Hour": 1.0,
        "Account_Age_Days": 1200,
        "Fraud_Risk_Signal": 15.0,
        "Failed_OTP_Attempts": 0,
        "Previous_Disputes": 0,
        "Minutes_Since_Last_Transaction": 120,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["Transaction_ID"] == "TXN_TEST_001"
    assert data["prediction"] in ["Legitimate", "Fraudulent"]
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert data["processing_time_ms"] > 0


def test_predict_endpoint_high_risk():
    payload = {
        "Transaction_ID": "TXN_TEST_HIGH_RISK",
        "Transaction_Amount_INR": 9850.0,
        "Transaction_Hour": 2,
        "Payment_Method": "Card",
        "Transaction_Channel": "Web",
        "Device_Status": "New",
        "Location_Type": "International",
        "Transactions_Last_Hour": 8.0,
        "Account_Age_Days": 5,
        "Fraud_Risk_Signal": 99.0,
        "Failed_OTP_Attempts": 3,
        "Previous_Disputes": 2,
        "Minutes_Since_Last_Transaction": 2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["Transaction_ID"] == "TXN_TEST_HIGH_RISK"
    assert "fraud_probability" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]


def test_predict_batch_endpoint():
    payload = {
        "transactions": [
            {
                "Transaction_ID": "TXN_BATCH_1",
                "Transaction_Amount_INR": 200.0,
                "Transaction_Hour": 10,
                "Payment_Method": "UPI",
                "Transaction_Channel": "Mobile App",
                "Device_Status": "Known",
                "Location_Type": "Domestic",
            },
            {
                "Transaction_ID": "TXN_BATCH_2",
                "Transaction_Amount_INR": 4500.0,
                "Transaction_Hour": 23,
                "Payment_Method": "Card",
                "Transaction_Channel": "Web",
                "Device_Status": "New",
                "Location_Type": "International",
            },
        ]
    }
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 2
    assert len(data["predictions"]) == 2


def test_prometheus_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "app_requests_total" in text
    assert "app_predictions_total" in text
    assert "app_request_latency_seconds" in text


def test_logging_file_generation():
    assert os.path.exists(APP_LOG_PATH)
    with open(APP_LOG_PATH, "r") as f:
        content = f.read()
    assert len(content) > 0
    assert "PREDICTION" in content or "Model successfully loaded" in content
