#!/usr/bin/env python3
"""Train the churn model, log everything to MLflow, and save a servable artifact."""
import json
import os
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

FEATURES = ["tenure", "monthly_charges", "support_calls", "contract_type"]
MODEL_DIR = "models"


def main():
    df = pd.read_csv("data/train.csv")
    X, y = df[FEATURES], df["churn"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    n_estimators = int(os.getenv("N_ESTIMATORS", "200"))
    max_depth = int(os.getenv("MAX_DEPTH", "8"))

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns"))
    mlflow.set_experiment("churn-prediction")

    with mlflow.start_run() as run:
        model = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=max_depth, random_state=42,
            n_jobs=-1, class_weight="balanced")
        model.fit(Xtr, ytr)

        pred = model.predict(Xte)
        proba = model.predict_proba(Xte)[:, 1]
        metrics = {
            "accuracy": accuracy_score(yte, pred),
            "f1": f1_score(yte, pred),
            "roc_auc": roc_auc_score(yte, proba),
        }
        mlflow.log_params({"n_estimators": n_estimators, "max_depth": max_depth})
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, artifact_path="model", registered_model_name="churn-model")

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, f"{MODEL_DIR}/model.pkl")
        json.dump({"features": FEATURES}, open(f"{MODEL_DIR}/schema.json", "w"))
        json.dump(metrics, open(f"{MODEL_DIR}/metrics.json", "w"), indent=2)

        print("run_id:", run.info.run_id)
        print("metrics:", json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
