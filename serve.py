#!/usr/bin/env python3
"""Serve the churn model over HTTP with Prometheus instrumentation."""
import json
import os
import time
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

MODEL_DIR = os.getenv("MODEL_DIR", "models")
model = joblib.load(f"{MODEL_DIR}/model.pkl")
FEATURES = json.load(open(f"{MODEL_DIR}/schema.json"))["features"]

app = FastAPI(title="Churn MLOps API", version=os.getenv("MODEL_VERSION", "1.0.0"))

PRED = Counter("model_predictions_total", "Predictions served", ["label"])
LAT = Histogram("model_inference_seconds", "Inference latency (s)")
POS_RATE = Gauge("model_positive_rate", "Rolling share of churn=1 predictions")
_pos, _tot = 0, 0


class Customer(BaseModel):
    tenure: int
    monthly_charges: float
    support_calls: int
    contract_type: int


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/predict")
def predict(c: Customer):
    global _pos, _tot
    with LAT.time():
        row = pd.DataFrame([[getattr(c, f) for f in FEATURES]], columns=FEATURES)
        label = int(model.predict(row)[0])
        proba = float(model.predict_proba(row)[0][1])
    PRED.labels(str(label)).inc()
    _tot += 1
    _pos += label
    POS_RATE.set(_pos / _tot)
    return {"churn": label, "probability": round(proba, 4), "model_version": app.version}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
