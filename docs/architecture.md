# Architecture & design notes

## The MLOps lifecycle, mapped to this repo
1. **Data** — `data/generate_data.py` creates train / reference / current splits
   (synthetic churn, so the repo is self-contained and free to run).
2. **Train + track** — `src/train.py` trains a RandomForest and logs params, metrics
   and the model to **MLflow** (experiment tracking + model registry).
3. **Evaluate + gate** — `src/evaluate.py` fails CI if accuracy/F1 miss thresholds, so a
   weak model is never promoted. This is the difference between "a notebook" and "MLOps".
4. **Package + serve** — `src/serve.py` (FastAPI) serves `/predict`, instrumented with
   Prometheus (`/metrics`). Containerised via `Dockerfile`.
5. **Deploy** — `k8s/deployment.yaml` runs the API on Kubernetes; image built and pushed
   by CI to GHCR.
6. **Monitor** — `src/monitor_drift.py` uses **Evidently** to compare live vs reference
   data and flags drift; `monitoring/` adds Prometheus alerts + a Grafana dashboard for
   latency and prediction-distribution shift.
7. **Orchestrate** — `orchestration/airflow_dag.py` shows how the same steps schedule on
   Airflow (the orchestrator layer job listings expect).

## Why these tools
This is the most-requested 2026 open-source combination: **MLflow + Docker + Kubernetes +
an orchestrator + Evidently**. All free, no GPU — the churn model trains in seconds on CPU.

## Continuous Training (CT)
`ci-train-eval.yml` retrains and re-gates on every change to `src/` or `data/`.
`drift-check.yml` runs daily; on detected drift it opens a GitHub issue recommending a
retrain — a minimal closed loop from monitoring back to training.

## What to measure (for your resume)
- Gate pass/fail rate and the metric thresholds you set.
- p95 inference latency of the served API.
- Time from drift detection to retrained-and-redeployed model.
Use the numbers you actually observe.
