import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from prometheus_client import (
    Counter,
    Histogram,
    Summary,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from src.config import (
    MODEL_PATH,
    METADATA_PATH,
    APP_LOG_PATH,
    LOGS_DIR,
)
from src.data_pipeline import clean_data, engineer_features, get_feature_lists

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# TASK 4: APPLICATION LOGGING SETUP
# ---------------------------------------------------------
logger = logging.getLogger("fraud_detection_service")
logger.setLevel(logging.INFO)

# Formatter
log_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# File Handler
file_handler = logging.FileHandler(APP_LOG_PATH)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Stream / Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# ---------------------------------------------------------
# TASK 5: PROMETHEUS METRICS SETUP
# ---------------------------------------------------------
REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total HTTP requests to the application",
    ["endpoint", "method", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Application request latency in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

PREDICTION_COUNT = Counter(
    "app_predictions_total",
    "Total transaction predictions made by the model",
    ["prediction_label", "risk_level"],
)

ERROR_COUNT = Counter(
    "app_errors_total",
    "Total error occurrences in the application",
    ["endpoint", "error_type"],
)

TRANSACTION_AMOUNT = Summary(
    "app_transaction_amount_inr",
    "Distribution of processed transaction amounts in INR",
)

FRAUD_PROBABILITY_GAUGE = Gauge(
    "app_latest_fraud_probability",
    "Fraud probability of the latest transaction evaluated",
)

MODEL_HEALTH_GAUGE = Gauge(
    "app_model_health_status",
    "Model health status (1 = healthy and loaded, 0 = unhealthy)",
)

# ---------------------------------------------------------
# FASTAPI APPLICATION & MODEL LOADING
# ---------------------------------------------------------
app = FastAPI(
    title="Online Payment Fraud Detection System",
    description="Production-grade ML API with Prometheus monitoring, structured logging, and Evidently AI drift integration.",
    version="1.0.0",
)

APP_START_TIME = time.time()
MODEL_PIPELINE = None
MODEL_METADATA: Dict[str, Any] = {}

try:
    if os.path.exists(MODEL_PATH):
        MODEL_PIPELINE = joblib.load(MODEL_PATH)
        MODEL_HEALTH_GAUGE.set(1.0)
        logger.info(f"Model successfully loaded from {MODEL_PATH}")
    else:
        logger.warning(f"Model file not found at {MODEL_PATH}. Run training first.")
        MODEL_HEALTH_GAUGE.set(0.0)

    if os.path.exists(METADATA_PATH):
        import json
        with open(METADATA_PATH, "r") as f:
            MODEL_METADATA = json.load(f)
except Exception as e:
    logger.error(f"Error loading model or metadata: {e}", exc_info=True)
    MODEL_HEALTH_GAUGE.set(0.0)


# ---------------------------------------------------------
# PYDANTIC DATA MODELS
# ---------------------------------------------------------
class TransactionInput(BaseModel):
    Transaction_ID: Optional[str] = Field("TXN_UNKNOWN", description="Unique transaction ID")
    Transaction_Amount_INR: Optional[float] = Field(None, description="Transaction amount in INR")
    Transaction_Hour: Optional[int] = Field(12, ge=0, le=23, description="Hour of the transaction (0-23)")
    Payment_Method: Optional[str] = Field("UPI", description="UPI, Card, Wallet, NetBanking")
    Transaction_Channel: Optional[str] = Field("Mobile App", description="POS, Web, Mobile App")
    Device_Status: Optional[str] = Field("Known", description="Known, New")
    Location_Type: Optional[str] = Field("Domestic", description="Domestic, International")
    Transactions_Last_Hour: Optional[float] = Field(1.0, ge=0, description="Transactions in last hour")
    Account_Age_Days: Optional[int] = Field(365, ge=0, description="Age of account in days")
    Fraud_Risk_Signal: Optional[float] = Field(20.0, ge=0, le=100, description="Risk signal (0-100)")
    Failed_OTP_Attempts: Optional[int] = Field(0, ge=0, description="Failed OTP attempts")
    Previous_Disputes: Optional[int] = Field(0, ge=0, description="Previous disputes count")
    Minutes_Since_Last_Transaction: Optional[int] = Field(60, ge=0, description="Minutes since last txn")

    model_config = {
        "json_schema_extra": {
            "example": {
                "Transaction_ID": "TXN_SAMPLE_001",
                "Transaction_Amount_INR": 850.50,
                "Transaction_Hour": 14,
                "Payment_Method": "UPI",
                "Transaction_Channel": "Mobile App",
                "Device_Status": "Known",
                "Location_Type": "Domestic",
                "Transactions_Last_Hour": 2.0,
                "Account_Age_Days": 450,
                "Fraud_Risk_Signal": 35.0,
                "Failed_OTP_Attempts": 0,
                "Previous_Disputes": 0,
                "Minutes_Since_Last_Transaction": 45,
            }
        }
    }


class PredictionResponse(BaseModel):
    Transaction_ID: str
    prediction: str
    is_fraud: int
    fraud_probability: float
    risk_level: str
    processing_time_ms: float
    timestamp: str


class BatchTransactionInput(BaseModel):
    transactions: List[TransactionInput]


class BatchPredictionResponse(BaseModel):
    total_transactions: int
    fraud_count: int
    legitimate_count: int
    predictions: List[PredictionResponse]
    total_processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    uptime_seconds: float
    timestamp: str


# ---------------------------------------------------------
# PROMETHEUS METRICS ENDPOINT
# ---------------------------------------------------------
@app.get("/metrics", tags=["Monitoring"])
def metrics():
    """Prometheus exposition endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------
# TASK 3: /health ENDPOINT
# ---------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to inspect application and model status."""
    start_time = time.time()
    endpoint = "/health"
    try:
        is_loaded = MODEL_PIPELINE is not None
        status = "healthy" if is_loaded else "degraded"
        uptime = round(time.time() - APP_START_TIME, 2)
        model_name = MODEL_METADATA.get("model_name", "LogisticRegression")

        REQUEST_COUNT.labels(endpoint=endpoint, method="GET", http_status="200").inc()
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        return HealthResponse(
            status=status,
            model_loaded=is_loaded,
            model_name=model_name,
            uptime_seconds=uptime,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        ERROR_COUNT.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# TASK 3 & 4: /predict ENDPOINT WITH APPLICATION LOGGING
# ---------------------------------------------------------
def _process_single_transaction(txn: TransactionInput) -> PredictionResponse:
    global MODEL_PIPELINE
    start_time = time.perf_counter()

    if MODEL_PIPELINE is None:
        raise ValueError("Model pipeline is not loaded on server.")

    # Convert Pydantic object to DataFrame
    data_dict = txn.model_dump()
    txn_id = data_dict.get("Transaction_ID") or "TXN_UNKNOWN"
    df_raw = pd.DataFrame([data_dict])

    # Record Prometheus transaction amount metric
    amt = data_dict.get("Transaction_Amount_INR")
    if amt is not None and amt > 0:
        TRANSACTION_AMOUNT.observe(amt)

    # Clean & feature engineer
    df_clean = clean_data(df_raw)
    df_feat = engineer_features(df_clean)

    num_cols, cat_cols = get_feature_lists()
    all_cols = num_cols + cat_cols
    X = df_feat[all_cols]

    # Model inference
    try:
        prob = float(MODEL_PIPELINE.predict_proba(X)[0, 1])
    except Exception:
        pred_raw = int(MODEL_PIPELINE.predict(X)[0])
        prob = 1.0 if pred_raw == 1 else 0.0

    # Decision threshold
    threshold = MODEL_METADATA.get("threshold", 0.5)
    is_fraud = int(prob >= threshold)
    prediction_label = "Fraudulent" if is_fraud == 1 else "Legitimate"

    # Risk level categorization
    if prob >= 0.70:
        risk_level = "HIGH"
    elif prob >= 0.40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Compute execution time
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    # Prometheus Metric Updates
    PREDICTION_COUNT.labels(prediction_label=prediction_label, risk_level=risk_level).inc()
    FRAUD_PROBABILITY_GAUGE.set(prob)

    response = PredictionResponse(
        Transaction_ID=txn_id,
        prediction=prediction_label,
        is_fraud=is_fraud,
        fraud_probability=round(prob, 4),
        risk_level=risk_level,
        processing_time_ms=elapsed_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Structured Application Logging
    logger.info(
        f"PREDICTION | txn_id={txn_id} | amount={amt} | method={data_dict.get('Payment_Method')} | "
        f"label={prediction_label} | prob={prob:.4f} | risk={risk_level} | latency_ms={elapsed_ms:.2f}"
    )

    return response


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(transaction: TransactionInput):
    """
    Classify a single transaction as Legitimate or Fraudulent.
    Records request, prediction, latency, and logs.
    """
    start_time = time.time()
    endpoint = "/predict"
    try:
        response = _process_single_transaction(transaction)
        REQUEST_COUNT.labels(endpoint=endpoint, method="POST", http_status="200").inc()
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        return response
    except Exception as e:
        REQUEST_COUNT.labels(endpoint=endpoint, method="POST", http_status="500").inc()
        ERROR_COUNT.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
        logger.error(
            f"ERROR during prediction for txn_id={transaction.Transaction_ID}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
def predict_batch(batch: BatchTransactionInput):
    """
    Classify multiple transactions in batch mode.
    """
    start_time = time.time()
    endpoint = "/predict/batch"
    try:
        predictions = []
        fraud_cnt = 0
        legit_cnt = 0

        for txn in batch.transactions:
            pred_resp = _process_single_transaction(txn)
            predictions.append(pred_resp)
            if pred_resp.is_fraud == 1:
                fraud_cnt += 1
            else:
                legit_cnt += 1

        total_elapsed_ms = round((time.time() - start_time) * 1000.0, 3)
        REQUEST_COUNT.labels(endpoint=endpoint, method="POST", http_status="200").inc()
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        logger.info(
            f"BATCH PREDICTION | total={len(predictions)} | fraud={fraud_cnt} | legit={legit_cnt} | total_latency_ms={total_elapsed_ms:.2f}"
        )

        return BatchPredictionResponse(
            total_transactions=len(predictions),
            fraud_count=fraud_cnt,
            legitimate_count=legit_cnt,
            predictions=predictions,
            total_processing_time_ms=total_elapsed_ms,
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint=endpoint, method="POST", http_status="500").inc()
        ERROR_COUNT.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
        logger.error(f"ERROR during batch prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")
