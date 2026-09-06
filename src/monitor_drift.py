#!/usr/bin/env python3
"""Compare live data against the training-time reference and flag data drift.

Uses Evidently to build a data-drift report (HTML for humans + a dataset-level
drift flag for CI). Exits non-zero when drift is detected so a scheduled job can
alert / open an issue / trigger retraining.
"""
import sys
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

FEATURES = ["tenure", "monthly_charges", "support_calls", "contract_type"]


def main():
    ref = pd.read_csv("data/reference.csv")[FEATURES]
    cur = pd.read_csv("data/current.csv")[FEATURES]

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)
    report.save_html("drift_report.html")

    result = report.as_dict()
    summary = result["metrics"][0]["result"]
    drifted = summary["number_of_drifted_columns"]
    share = summary["share_of_drifted_columns"]
    dataset_drift = summary["dataset_drift"]

    print(f"drifted columns: {drifted}  share: {share:.2f}  dataset_drift: {dataset_drift}")
    print("HTML report written to drift_report.html")

    if dataset_drift:
        print("🚨 DATASET DRIFT DETECTED — recommend retraining.")
        sys.exit(2)
    print("✅ No significant drift.")


if __name__ == "__main__":
    main()
