import time
import json
import logging
import random
from pathlib import Path
import pandas as pd
import requests

from src.config import (
    REFERENCE_DATA_PATH,
    CURRENT_DRIFT_DATA_PATH,
    REPORTS_DIR,
)

logger = logging.getLogger("traffic_simulator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

API_BASE_URL = "http://127.0.0.1:8000"


def check_api_readiness(max_retries: int = 15, delay: float = 1.0) -> bool:
    """Verify that the FastAPI service is running and healthy."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{API_BASE_URL}/health", timeout=2.0)
            if resp.status_code == 200:
                logger.info(f"API is ready and healthy: {resp.json()}")
                return True
        except Exception:
            pass
        time.sleep(delay)
    return False


def simulate_traffic(num_baseline: int = 50, num_drift: int = 100):
    """
    Simulates traffic through two phases:
    1. Baseline Phase (Reference Transactions)
    2. Drift Phase (Current Drift Transactions with shifted amounts, frequency, payment methods)
    """
    logger.info("=" * 60)
    logger.info("TASK 8: SIMULATING TRAFFIC TO DEMONSTRATE DRIFT & MONITORING")
    logger.info("=" * 60)

    if not check_api_readiness():
        logger.error(f"Cannot connect to API at {API_BASE_URL}. Ensure uvicorn is running.")
        return False

    ref_df = pd.read_csv(REFERENCE_DATA_PATH)
    drift_df = pd.read_csv(CURRENT_DRIFT_DATA_PATH)

    results = {
        "baseline": {
            "sent": 0,
            "fraud_detected": 0,
            "legit_detected": 0,
            "total_amount": 0.0,
            "latencies_ms": [],
        },
        "drift": {
            "sent": 0,
            "fraud_detected": 0,
            "legit_detected": 0,
            "total_amount": 0.0,
            "latencies_ms": [],
        },
    }

    # ---------------------------------------------------------
    # PHASE 1: Baseline Reference Traffic
    # ---------------------------------------------------------
    logger.info(f"\n--- [Phase 1] Sending {num_baseline} Baseline Reference Transactions ---")
    baseline_sample = ref_df.sample(min(num_baseline, len(ref_df)), random_state=42)

    for idx, row in baseline_sample.iterrows():
        payload = {
            "Transaction_ID": str(row["Transaction_ID"]),
            "Transaction_Amount_INR": None if pd.isna(row["Transaction_Amount_INR"]) or row["Transaction_Amount_INR"] <= 0 else float(row["Transaction_Amount_INR"]),
            "Transaction_Hour": int(row["Transaction_Hour"]) if not pd.isna(row["Transaction_Hour"]) else 12,
            "Payment_Method": None if pd.isna(row["Payment_Method"]) else str(row["Payment_Method"]),
            "Transaction_Channel": str(row["Transaction_Channel"]),
            "Device_Status": None if pd.isna(row["Device_Status"]) else str(row["Device_Status"]),
            "Location_Type": str(row["Location_Type"]),
            "Transactions_Last_Hour": None if pd.isna(row["Transactions_Last_Hour"]) else float(row["Transactions_Last_Hour"]),
            "Account_Age_Days": int(row["Account_Age_Days"]),
            "Fraud_Risk_Signal": None if pd.isna(row["Fraud_Risk_Signal"]) else float(row["Fraud_Risk_Signal"]),
            "Failed_OTP_Attempts": int(row["Failed_OTP_Attempts"]),
            "Previous_Disputes": int(row["Previous_Disputes"]),
            "Minutes_Since_Last_Transaction": int(row["Minutes_Since_Last_Transaction"]),
        }

        t0 = time.perf_counter()
        resp = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=5.0)
        dur_ms = (time.perf_counter() - t0) * 1000.0

        if resp.status_code == 200:
            res_data = resp.json()
            results["baseline"]["sent"] += 1
            results["baseline"]["latencies_ms"].append(dur_ms)
            if payload["Transaction_Amount_INR"]:
                results["baseline"]["total_amount"] += payload["Transaction_Amount_INR"]
            if res_data["prediction"] == "Fraudulent":
                results["baseline"]["fraud_detected"] += 1
            else:
                results["baseline"]["legit_detected"] += 1

        time.sleep(0.02)  # small pacing

    # ---------------------------------------------------------
    # PHASE 2: Drift & Shifted Pattern Traffic
    # (High amounts, increased transaction frequency, shifted payment methods)
    # ---------------------------------------------------------
    logger.info(f"\n--- [Phase 2] Sending {num_drift} Drifted Transactions (Shifted Patterns) ---")
    drift_sample = drift_df.sample(min(num_drift, len(drift_df)), random_state=42)

    for idx, row in drift_sample.iterrows():
        # Using drift dataset rows which embody the real-world shifts
        payload = {
            "Transaction_ID": str(row["Transaction_ID"]),
            "Transaction_Amount_INR": None if pd.isna(row["Transaction_Amount_INR"]) or row["Transaction_Amount_INR"] <= 0 else float(row["Transaction_Amount_INR"]),
            "Transaction_Hour": int(row["Transaction_Hour"]) if not pd.isna(row["Transaction_Hour"]) else 12,
            "Payment_Method": None if pd.isna(row["Payment_Method"]) else str(row["Payment_Method"]),
            "Transaction_Channel": str(row["Transaction_Channel"]),
            "Device_Status": None if pd.isna(row["Device_Status"]) else str(row["Device_Status"]),
            "Location_Type": str(row["Location_Type"]),
            "Transactions_Last_Hour": None if pd.isna(row["Transactions_Last_Hour"]) else float(row["Transactions_Last_Hour"]),
            "Account_Age_Days": int(row["Account_Age_Days"]),
            "Fraud_Risk_Signal": None if pd.isna(row["Fraud_Risk_Signal"]) else float(row["Fraud_Risk_Signal"]),
            "Failed_OTP_Attempts": int(row["Failed_OTP_Attempts"]),
            "Previous_Disputes": int(row["Previous_Disputes"]),
            "Minutes_Since_Last_Transaction": int(row["Minutes_Since_Last_Transaction"]),
        }

        t0 = time.perf_counter()
        resp = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=5.0)
        dur_ms = (time.perf_counter() - t0) * 1000.0

        if resp.status_code == 200:
            res_data = resp.json()
            results["drift"]["sent"] += 1
            results["drift"]["latencies_ms"].append(dur_ms)
            if payload["Transaction_Amount_INR"]:
                results["drift"]["total_amount"] += payload["Transaction_Amount_INR"]
            if res_data["prediction"] == "Fraudulent":
                results["drift"]["fraud_detected"] += 1
            else:
                results["drift"]["legit_detected"] += 1

        time.sleep(0.01)

    # Compute Summary Stats
    base_sent = results["baseline"]["sent"] or 1
    drift_sent = results["drift"]["sent"] or 1

    summary_comparison = {
        "baseline_phase": {
            "transactions_processed": results["baseline"]["sent"],
            "fraud_rate_percent": round((results["baseline"]["fraud_detected"] / base_sent) * 100, 2),
            "avg_transaction_amount_inr": round(results["baseline"]["total_amount"] / base_sent, 2),
            "avg_latency_ms": round(sum(results["baseline"]["latencies_ms"]) / len(results["baseline"]["latencies_ms"]), 2) if results["baseline"]["latencies_ms"] else 0,
            "p95_latency_ms": round(float(pd.Series(results["baseline"]["latencies_ms"]).quantile(0.95)), 2) if results["baseline"]["latencies_ms"] else 0,
        },
        "drift_phase": {
            "transactions_processed": results["drift"]["sent"],
            "fraud_rate_percent": round((results["drift"]["fraud_detected"] / drift_sent) * 100, 2),
            "avg_transaction_amount_inr": round(results["drift"]["total_amount"] / drift_sent, 2),
            "avg_latency_ms": round(sum(results["drift"]["latencies_ms"]) / len(results["drift"]["latencies_ms"]), 2) if results["drift"]["latencies_ms"] else 0,
            "p95_latency_ms": round(float(pd.Series(results["drift"]["latencies_ms"]).quantile(0.95)), 2) if results["drift"]["latencies_ms"] else 0,
        },
    }

    out_file = REPORTS_DIR / "simulation_results.json"
    with open(out_file, "w") as f:
        json.dump(summary_comparison, f, indent=2)

    logger.info("\n" + "=" * 60)
    logger.info("TRAFFIC SIMULATION RESULTS COMPARISON")
    logger.info("=" * 60)
    logger.info(f"Baseline Avg Amount:   INR {summary_comparison['baseline_phase']['avg_transaction_amount_inr']:.2f}")
    logger.info(f"Drift Avg Amount:      INR {summary_comparison['drift_phase']['avg_transaction_amount_inr']:.2f}")
    logger.info(f"Baseline Fraud Rate:   {summary_comparison['baseline_phase']['fraud_rate_percent']:.2f}%")
    logger.info(f"Drift Fraud Rate:      {summary_comparison['drift_phase']['fraud_rate_percent']:.2f}%")
    logger.info(f"Baseline Avg Latency:  {summary_comparison['baseline_phase']['avg_latency_ms']:.2f} ms")
    logger.info(f"Drift Avg Latency:     {summary_comparison['drift_phase']['avg_latency_ms']:.2f} ms")
    logger.info(f"Results saved to: {out_file}")

    return summary_comparison


if __name__ == "__main__":
    simulate_traffic(num_baseline=50, num_drift=150)
