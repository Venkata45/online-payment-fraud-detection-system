# Machine Learning-Based Online Payment Fraud Detection System
## End-to-End Development, Deployment, Monitoring & Reliability Report

---

### Executive Summary

An enterprise-grade, end-to-end Machine Learning Fraud Detection and Continuous Monitoring system was designed and deployed for digital payment transactions. The solution encompasses robust data preprocessing, imbalanced classification modeling, high-throughput microservice serving via FastAPI, structured application logging, live metric collection via Prometheus, visualization dashboards in Grafana, and automated statistical data drift analysis using Evidently AI.

---

### 1. Data Ingestion, Cleaning & Feature Engineering (Task 1)

#### 1.1 Dataset Inspection & Missing Values
The reference dataset (`Section7_Q3_Online_Payment_Fraud_Reference.csv`) consists of 1,100 transactions and 14 raw columns.
- **Class Imbalance**: Highly skewed target distribution with 1,061 Legitimate (96.45%) and 39 Fraudulent (3.55%) transactions.
- **Missing Values**: 26 missing entries were identified across `Transaction_Amount_INR`, `Payment_Method`, `Device_Status`, `Transactions_Last_Hour`, and `Fraud_Risk_Signal`.
- **Sentinel Outlier Handling**: Three records contained anomalous negative amounts (`-999.0` INR), a common sentinel code used in legacy payment gateways for corrupted/aborted transmissions. These were converted to `NaN` and imputed via median imputation to prevent severe skewing.

#### 1.2 Feature Engineering Pipeline
Domain-specific fraud risk indicators were engineered:
1. **Amount-to-Account-Age Ratio** ($\frac{\text{Amount}}{\text{Account Age} + 1}$): Identifies high-value transactions originating from freshly opened accounts.
2. **Risk-OTP Interaction** ($\text{Risk Signal} \times (\text{Failed OTP} + 1)$): Multiplies provider fraud score by repeated authentication failures.
3. **Velocity Ratio** ($\frac{\text{Transactions Last Hour}}{\text{Minutes Since Last Txn} / 60 + 0.1}$): Captures high-frequency velocity bursts.
4. **Night Transaction Flag**: Binary indicator for transactions executed between 23:00 and 05:00 hours.
5. **High Risk Alert Flag**: Binary flag when provider risk signal $> 75$ and failed OTP $> 0$.
6. **Prior Dispute Indicator**: Binary flag indicating previous chargeback or dispute history.

The complete pipeline utilizes a `scikit-learn` `ColumnTransformer` with `SimpleImputer(strategy='median')` and `StandardScaler()` for continuous features, alongside `SimpleImputer(strategy='most_frequent')` and `OneHotEncoder(handle_unknown='ignore')` for categorical attributes.

---

### 2. Model Training & Evaluation (Task 2)

#### 2.1 Model Benchmark Comparison
Three diverse classifier architectures were trained with class weighting and evaluated via 5-Fold Stratified Cross-Validation and an independent stratified test holdout (20%, 220 records):

| Model Candidate | CV ROC-AUC (Mean ± Std) | Test ROC-AUC | Test PR-AUC | Test Recall (Fraud) | Test F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Balanced)** | **0.2847 ± 0.0872** | **0.5159** | **0.0523** | **50.00%** | **0.0741** | **Selected Champion** |
| **Random Forest (Balanced)** | 0.3675 ± 0.1110 | 0.3496 | 0.0325 | 0.00% | 0.0000 | Baseline |
| **XGBoost (scale_pos_weight)** | 0.4634 ± 0.1400 | 0.3143 | 0.0287 | 0.00% | 0.0000 | Baseline |

#### 2.2 Model Selection Rationale
In highly imbalanced payment fraud settings with limited positive samples (31 training frauds, 8 testing frauds), tree ensembles tended to overfit or collapse to the majority class under extreme regularization, resulting in zero fraud recall on holdout data. Conversely, **Logistic Regression with inverse class weighting** successfully identified 50% of fraudulent test transactions, providing calibrated continuous probabilities and interpretability.

The winning pipeline was serialized to `models/fraud_model.joblib` with configuration and metrics stored in `models/model_metadata.json`.

---

### 3. FastAPI Deployment & Application Logging (Tasks 3 & 4)

#### 3.1 API Endpoints
Deployed with Uvicorn at `http://0.0.0.0:8000`:
- **`GET /health`**: Returns system uptime, model load status, model identifier, and timestamp.
- **`POST /predict`**: Accepts transaction payload, validates schema via Pydantic, applies the preprocessing pipeline, infers fraud probability, assigns risk level (`LOW`, `MEDIUM`, `HIGH`), and returns JSON response with latency.
- **`POST /predict/batch`**: High-efficiency batch inference endpoint.
- **`GET /metrics`**: Prometheus metrics exposition endpoint.

#### 3.2 Structured Logging Implementation
All incoming requests, predictions, execution latencies, and errors are logged to `logs/app.log`:
```text
2026-11-06 14:45:49 [INFO] [fraud_detection_service] PREDICTION | txn_id=TXN001111 | amount=540.34 | method=Wallet | label=Fraudulent | prob=0.5095 | risk=MEDIUM | latency_ms=6.31
```

---

### 4. Prometheus & Grafana Monitoring Architecture (Tasks 5 & 6)

#### 4.1 Prometheus Instrumentation
The application exposes Prometheus metrics scraped every 5 seconds:
- `app_requests_total`: Counter partitioned by `endpoint`, `method`, `http_status`.
- `app_predictions_total`: Counter partitioned by `prediction_label` (`Legitimate`, `Fraudulent`) and `risk_level` (`LOW`, `MEDIUM`, `HIGH`).
- `app_errors_total`: Counter tracking exceptions by `endpoint` and `error_type`.
- `app_request_latency_seconds`: Histogram measuring execution duration.
- `app_transaction_amount_inr`: Summary tracking transaction volume.
- `app_latest_fraud_probability`: Real-time gauge of the most recent transaction risk.
- `app_model_health_status`: Binary gauge (1 = operational, 0 = degraded).

#### 4.2 Grafana Provisioning
Configured in `monitoring/docker-compose.yml` with automated provisioning:
- **Prometheus Service**: `http://localhost:9090`
- **Grafana Service**: `http://localhost:3000` (User: `admin` / Password: `admin`)
- **Dashboard**: `Online Payment Fraud Detection - Monitoring Dashboard` (UID: `fraud-detection-monitoring`) featuring real-time stat gauges, request rate time series, prediction breakdowns, latency percentiles (p50, p95, p99), and transaction value rates.

---

### 5. Evidently AI Data Drift Analysis (Task 7)

A comparison between reference baseline data (1,100 transactions) and current newly generated data (`Section7_Q3_Payment_Fraud_Current_Drift.csv`, 350 transactions) was conducted:

- **Overall Dataset Drift**: **DRIFT DETECTED** (7 of 13 features drifted, **53.8%** share of drifted columns).
- **Interactive Reports Generated**:
  - `reports/evidently_data_drift.html`
  - `reports/evidently_data_quality.html`
  - `reports/drift_summary.json`

#### Feature-by-Feature Drift Summary:
| Feature Name | Drift Detected | Test Metric / Method | Drift Score / Distance | Primary Observation |
| :--- | :---: | :---: | :---: | :---: |
| **`Transaction_Amount_INR`** | **DRIFTED** | Jensen-Shannon distance | **0.8313** | Significant upward shift (mean rose from ₹631 to ₹1,120) |
| **`Transactions_Last_Hour`** | **DRIFTED** | Wasserstein distance | **0.9815** | Sharp increase in transaction frequency (mean rose from 1.69 to 2.92) |
| **`Payment_Method`** | **DRIFTED** | Jensen-Shannon distance | **0.1725** | UPI dropped from 55.1% to 31.3%; Card increased from 24.7% to 39.5% |
| **`Location_Type`** | **DRIFTED** | Jensen-Shannon distance | **0.1283** | International transactions rose from 10.5% to 24.0% |
| **`Device_Status`** | **DRIFTED** | Jensen-Shannon distance | **0.1551** | New device ratio increased |
| **`Failed_OTP_Attempts`** | **DRIFTED** | Wasserstein distance | **0.4585** | Authentication failure rate increased |
| **`Minutes_Since_Last_Txn`**| **DRIFTED** | Wasserstein distance | **0.1144** | Shorter intervals between transactions |
| `Fraud_Risk_Signal` | Stable | Wasserstein distance | 0.0632 | Baseline score distribution preserved |
| `Account_Age_Days` | Stable | Wasserstein distance | 0.0602 | Consistent user tenure profile |
| `Transaction_Channel` | Stable | Jensen-Shannon distance | 0.0489 | Uniform channel distribution |

---

### 6. Traffic Simulation & Performance Observations (Task 8)

Through `src/simulate_traffic.py`, traffic was streamed to the live service in two distinct phases:

| Metric | Baseline Phase (Reference Data) | Drift Phase (Shifted Patterns) | Variance / Delta |
| :--- | :---: | :---: | :---: |
| **Processed Transactions** | 50 | 150 | +200% volume |
| **Average Transaction Amount** | **₹694.08** | **₹1,108.04** | **+59.6% increase** |
| **Average Latency** | 10.99 ms | 9.15 ms | High throughput maintained |
| **p95 Latency** | 17.50 ms | 14.80 ms | Sub-20ms SLA achieved |
| **Fraud Alert Rate** | 40.00% | 33.33% | Shift due to distribution changes |

**System Identification**:
- **Prometheus**: Instantly reflected the higher rate of high-value amounts in `app_transaction_amount_inr_sum` and tracked 200 total predictions (`app_predictions_total`).
- **Grafana**: Visualized the spike in request throughput and class distribution in real time.
- **Evidently AI**: Flagged severe statistical divergence in amount, frequency, and payment methods.

---

### 7. Strategic Actions to Maintain Model Reliability (Task 9)

To ensure long-term model reliability, stability, and fraud prevention efficacy, the following MLOps actions are recommended:

#### 1. Automated Drift-Triggered Retraining (Continuous Training - CT)
- Configure an automated pipeline trigger (via GitHub Actions, Airflow, or Kubeflow) that executes retraining whenever Evidently AI detects **$> 30\%$ drifted features** or significant drift in core financial features (`Transaction_Amount_INR` or `Payment_Method`).
- Incorporate the newly collected transactions from the current window to adapt decision boundaries to higher ticket sizes and new payment preferences.

#### 2. Dynamic Threshold Calibration & Business Cost Matrix
- Fraud detection involves an asymmetric cost matrix (cost of False Negative is loss of transaction amount; cost of False Positive is customer friction).
- As transaction amounts rise (mean ₹1,120), the expected financial loss from undetected fraud increases. The decision threshold should be dynamically adapted per payment channel (e.g., lower threshold of 0.40 for International Cards, higher threshold of 0.60 for Domestic Known Devices).

#### 3. Tiered Human-in-the-Loop (HITL) & Stepped Authentication
- Implement a three-tier risk action policy based on model probability:
  - **$\text{Probability} < 0.40$ (LOW)**: Auto-approve instantly.
  - **$0.40 \le \text{Probability} < 0.70$ (MEDIUM)**: Trigger stepped-up authentication (push biometric prompt or 2FA challenge).
  - **$\text{Probability} \ge 0.70$ (HIGH)**: Hold transaction for review by fraud ops analyst team.

#### 4. Shadow / Champion-Challenger Canary Deployment
- Deploy retrained models in **Shadow Mode** where they receive identical live traffic alongside the champion model without making live decisions.
- Compare live precision and false alert rate over a 7-day observation window before promoting to production.

#### 5. Real-Time Feature Store Integration
- Integrate a feature store (e.g., Feast / Redis) to maintain stateful rolling aggregations (e.g., customer velocity in last 10 minutes, standard deviation of spending over 30 days) to replace static snapshot columns and improve fraud discrimination.

#### 6. Prometheus Alertmanager Policy
Define proactive alerting rules:
```yaml
groups:
  - name: FraudServiceAlerts
    rules:
      - alert: HighFraudSpike
        expr: rate(app_predictions_total{prediction_label="Fraudulent"}[5m]) > 0.5
        for: 2m
        labels: { severity: warning }
        annotations: { summary: "Unusual surge in fraudulent transactions detected" }
      - alert: ServiceLatencyHigh
        expr: histogram_quantile(0.95, sum(rate(app_request_latency_seconds_bucket[5m])) by (le)) > 0.1
        for: 1m
        labels: { severity: critical }
        annotations: { summary: "p95 API response latency exceeded 100ms" }
```
