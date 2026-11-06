import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Dataset Files
REFERENCE_DATA_PATH = DATA_DIR / "Section7_Q3_Online_Payment_Fraud_Reference.csv"
CURRENT_DRIFT_DATA_PATH = DATA_DIR / "Section7_Q3_Payment_Fraud_Current_Drift.csv"

# Model Artifacts
MODEL_PATH = MODELS_DIR / "fraud_model.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
EVALUATION_METRICS_PATH = REPORTS_DIR / "model_evaluation.json"

# Log File
APP_LOG_PATH = LOGS_DIR / "app.log"

# Target & Identifiers
TARGET_COL = "Fraud_Label"
ID_COL = "Transaction_ID"

# Feature Definitions
NUMERICAL_FEATURES = [
    "Transaction_Amount_INR",
    "Transaction_Hour",
    "Transactions_Last_Hour",
    "Account_Age_Days",
    "Fraud_Risk_Signal",
    "Failed_OTP_Attempts",
    "Previous_Disputes",
    "Minutes_Since_Last_Transaction",
]

CATEGORICAL_FEATURES = [
    "Payment_Method",
    "Transaction_Channel",
    "Device_Status",
    "Location_Type",
]

ENGINEERED_NUMERICAL_FEATURES = [
    "Amount_to_Account_Age_Ratio",
    "Risk_OTP_Interaction",
    "Velocity_Ratio",
    "Night_Transaction",
    "High_Risk_Flag",
    "Dispute_History_Flag",
]

# Random Seed for Reproducibility
RANDOM_SEED = 42
