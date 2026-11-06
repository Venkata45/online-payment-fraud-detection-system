import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from src.config import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ENGINEERED_NUMERICAL_FEATURES,
    TARGET_COL,
    ID_COL,
)


def load_data(filepath: str) -> pd.DataFrame:
    """Load raw transaction dataset from CSV."""
    df = pd.read_csv(filepath)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values and invalid/sentinel values.
    - Transaction_Amount_INR <= 0 (e.g. -999.0) treated as NaN.
    """
    df_clean = df.copy()

    # Sentinel value handling: replace negative amounts with NaN so imputer handles them cleanly
    if "Transaction_Amount_INR" in df_clean.columns:
        df_clean.loc[df_clean["Transaction_Amount_INR"] <= 0, "Transaction_Amount_INR"] = np.nan

    return df_clean


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate domain-specific features for fraud detection.
    """
    df_feat = df.copy()

    # 1. Ratio of transaction amount to account age (high amount on new account = higher risk)
    account_age = df_feat["Account_Age_Days"].fillna(df_feat["Account_Age_Days"].median())
    amt = df_feat["Transaction_Amount_INR"].fillna(df_feat["Transaction_Amount_INR"].median())
    df_feat["Amount_to_Account_Age_Ratio"] = amt / (account_age + 1.0)

    # 2. Combined Risk Signal & OTP Failure interaction
    risk_sig = df_feat["Fraud_Risk_Signal"].fillna(df_feat["Fraud_Risk_Signal"].median())
    otp_fail = df_feat["Failed_OTP_Attempts"].fillna(0)
    df_feat["Risk_OTP_Interaction"] = risk_sig * (otp_fail + 1.0)

    # 3. Velocity ratio: transactions per unit time since last txn
    mins = df_feat["Minutes_Since_Last_Transaction"].fillna(df_feat["Minutes_Since_Last_Transaction"].median())
    txns_last_hr = df_feat["Transactions_Last_Hour"].fillna(df_feat["Transactions_Last_Hour"].median())
    df_feat["Velocity_Ratio"] = txns_last_hr / ((mins / 60.0) + 0.1)

    # 4. Night transaction indicator (Transactions between 11 PM and 5 AM)
    hour = df_feat["Transaction_Hour"].fillna(12)
    df_feat["Night_Transaction"] = ((hour >= 23) | (hour <= 5)).astype(int)

    # 5. High risk alert flag (high risk signal + failed OTP attempts)
    df_feat["High_Risk_Flag"] = ((risk_sig > 75) & (otp_fail > 0)).astype(int)

    # 6. Prior dispute indicator
    disputes = df_feat["Previous_Disputes"].fillna(0)
    df_feat["Dispute_History_Flag"] = (disputes > 0).astype(int)

    return df_feat


def get_feature_lists():
    """Return all numerical (base + engineered) and categorical feature names."""
    all_num_features = NUMERICAL_FEATURES + ENGINEERED_NUMERICAL_FEATURES
    return all_num_features, CATEGORICAL_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """
    Construct scikit-learn ColumnTransformer for preprocessing.
    - Imputes and standardizes numerical features
    - Imputes and one-hot encodes categorical features
    """
    all_num_features, cat_features = get_feature_lists()

    num_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    cat_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, all_num_features),
            ("cat", cat_pipeline, cat_features),
        ]
    )

    return preprocessor


def prepare_data(filepath: str):
    """
    Complete data preparation workflow: load, clean, feature engineer, and extract X, y.
    """
    df = load_data(filepath)
    df_clean = clean_data(df)
    df_feat = engineer_features(df_clean)

    all_num_features, cat_features = get_feature_lists()
    all_features = all_num_features + cat_features

    X = df_feat[all_features]

    y = None
    if TARGET_COL in df_feat.columns:
        # Encode Fraudulent as 1, Legitimate as 0
        y = (df_feat[TARGET_COL] == "Fraudulent").astype(int)

    return X, y, df_feat
