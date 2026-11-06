#!/usr/bin/env bash
set -e

echo "================================================================="
echo "ONLINE PAYMENT FRAUD DETECTION & MONITORING SYSTEM (E20 MLOPS)"
echo "================================================================="

# 1. Train Model
echo -e "\n[Step 1/5] Training ML Classification Model & Evaluating Metrics..."
python3 -m src.train

# 2. Run Test Suite
echo -e "\n[Step 2/5] Running Automated Test Suite..."
python3 -m pytest tests/test_api.py -v

# 3. Start Monitoring Containers (Prometheus & Grafana)
echo -e "\n[Step 3/5] Starting Prometheus & Grafana Containers via Docker Compose..."
docker compose -f monitoring/docker-compose.yml up -d

# 4. Run Evidently AI Drift Analysis
echo -e "\n[Step 4/5] Executing Evidently AI Data Drift Analysis..."
python3 -m src.monitoring

# 5. Simulate Traffic & Live Monitoring
echo -e "\n[Step 5/5] Streaming Simulated Traffic & Verifying Live Metrics..."
python3 -m src.simulate_traffic

echo -e "\n================================================================="
echo "ALL 9 TASKS COMPLETED SUCCESSFULLY!"
echo "FastAPI API:     http://localhost:8000 (docs at /docs, metrics at /metrics)"
echo "Prometheus:      http://localhost:9090"
echo "Grafana:         http://localhost:3000 (User: admin / Pass: admin)"
echo "Evidently HTML:  file://$(pwd)/reports/evidently_data_drift.html"
echo "Evidently Quality: file://$(pwd)/reports/evidently_data_quality.html"
echo "Logs:            $(pwd)/logs/app.log"
echo "================================================================="
