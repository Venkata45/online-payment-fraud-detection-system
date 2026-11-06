import json
import logging
from pathlib import Path
import pandas as pd

# Compatibility patch for Pandas >= 2.2 with Evidently legacy imports
import pandas.core.dtypes.common as pd_common
if not hasattr(pd_common, "infer_dtype_from_object"):
    pd_common.infer_dtype_from_object = pd.api.types.infer_dtype

from evidently.legacy.report import Report
from evidently.legacy.metric_preset import DataDriftPreset, DataQualityPreset

from src.config import (
    REFERENCE_DATA_PATH,
    CURRENT_DRIFT_DATA_PATH,
    REPORTS_DIR,
)

logger = logging.getLogger("drift_monitoring")
logging.basicConfig(level=logging.INFO)


def run_drift_analysis(
    reference_path: Path = REFERENCE_DATA_PATH,
    current_path: Path = CURRENT_DRIFT_DATA_PATH,
    output_dir: Path = REPORTS_DIR,
):
    """
    Execute Evidently AI Data Drift & Data Quality analysis.
    Compares reference baseline with newly generated current dataset.
    Generates interactive HTML reports and structured JSON summaries.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Loading reference data from: {reference_path}")
    logger.info(f"Loading current data from: {current_path}")

    ref = pd.read_csv(reference_path)
    curr = pd.read_csv(current_path)

    # Exclude non-feature identifier
    drop_cols = ["Transaction_ID"]
    ref_clean = ref.drop(columns=[c for c in drop_cols if c in ref.columns]).copy()
    curr_clean = curr.drop(columns=[c for c in drop_cols if c in curr.columns]).copy()

    # Clean sentinel values
    if "Transaction_Amount_INR" in ref_clean.columns:
        ref_clean["Transaction_Amount_INR"] = ref_clean["Transaction_Amount_INR"].replace(-999, None)
    if "Transaction_Amount_INR" in curr_clean.columns:
        curr_clean["Transaction_Amount_INR"] = curr_clean["Transaction_Amount_INR"].replace(-999, None)

    # 1. Run Data Drift Report
    logger.info("Running Evidently Data Drift Report...")
    drift_report = Report(metrics=[DataDriftPreset()])
    drift_report.run(reference_data=ref_clean, current_data=curr_clean)

    html_drift_path = output_dir / "evidently_data_drift.html"
    json_drift_path = output_dir / "evidently_data_drift.json"

    drift_report.save_html(str(html_drift_path))
    json_drift_str = drift_report.json()
    with open(json_drift_path, "w") as f:
        f.write(json_drift_str)

    logger.info(f"Saved Data Drift HTML report to: {html_drift_path}")
    logger.info(f"Saved Data Drift JSON report to: {json_drift_path}")

    # 2. Run Data Quality Report
    logger.info("Running Evidently Data Quality Report...")
    quality_report = Report(metrics=[DataQualityPreset()])
    quality_report.run(reference_data=ref_clean, current_data=curr_clean)

    html_quality_path = output_dir / "evidently_data_quality.html"
    quality_report.save_html(str(html_quality_path))
    logger.info(f"Saved Data Quality HTML report to: {html_quality_path}")

    # 3. Parse & Summarize Drift Findings
    drift_dict = json.loads(json_drift_str)
    summary = {
        "reference_rows": len(ref_clean),
        "current_rows": len(curr_clean),
        "dataset_drift_detected": False,
        "share_of_drifted_columns": 0.0,
        "number_of_drifted_columns": 0,
        "drift_details_by_column": {},
    }

    for metric in drift_dict.get("metrics", []):
        result = metric.get("result", {})
        if "dataset_drift" in result:
            summary["dataset_drift_detected"] = result.get("dataset_drift", False)
            summary["share_of_drifted_columns"] = result.get("share_of_drifted_columns", 0.0)
            summary["number_of_drifted_columns"] = result.get("number_of_drifted_columns", 0)

            for col_name, col_data in result.get("drift_by_columns", {}).items():
                summary["drift_details_by_column"][col_name] = {
                    "drift_detected": col_data.get("drift_detected"),
                    "drift_score": col_data.get("drift_score"),
                    "threshold": col_data.get("threshold"),
                    "stattest_name": col_data.get("stattest_name"),
                    "column_type": col_data.get("column_type"),
                }

    summary_path = output_dir / "drift_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("EVIDENTLY AI DRIFT ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Dataset Drift Detected: {summary['dataset_drift_detected']}")
    print(f"Drifted Columns: {summary['number_of_drifted_columns']} ({summary['share_of_drifted_columns']*100:.1f}%)")
    print("\nColumn-Level Drift Breakdown:")
    for col, det in summary["drift_details_by_column"].items():
        status = "DRIFT DETECTED" if det["drift_detected"] else "STABLE"
        print(f" - {col:<32}: [{status}] | Score: {det['drift_score']:.4f} | Test: {det['stattest_name']}")

    return summary


if __name__ == "__main__":
    run_drift_analysis()
