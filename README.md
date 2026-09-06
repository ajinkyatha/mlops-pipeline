# MLOps Pipeline — Churn Prediction, End to End

> A production-style **MLOps** pipeline: train with experiment tracking, gate on quality,
> serve on Kubernetes, and catch data drift automatically — retraining triggered from the
> monitoring signal. Built entirely on **free, open-source** tools, **no GPU**.

![stack](https://img.shields.io/badge/stack-MLflow%20%7C%20Docker%20%7C%20K8s%20%7C%20Evidently-informational) ![ci](https://img.shields.io/badge/CI-train%20%E2%86%92%20gate%20%E2%86%92%20deploy-brightgreen) ![license](https://img.shields.io/badge/license-MIT-blue)

## Why this matters
DevOps ships **code**. MLOps ships **code + data + models** — three artifacts that change
independently. This repo shows the operational layer companies pay a premium for: tracking,
a quality gate, model serving, and drift monitoring wired into a closed loop.

## The pipeline
```
 data/  ──▶ train.py (MLflow tracking + registry) ──▶ evaluate.py (quality GATE)
                                                             │ pass
                                                             ▼
                            Docker image ──▶ Kubernetes (FastAPI /predict + /metrics)
                                                             │
 Prometheus + Grafana ◀── latency / prediction-rate ────────┘
        ▲
        │ drift?                Evidently (reference vs live)
        └──────── monitor_drift.py ──▶ drift? ──▶ open issue ──▶ retrain (CI)
```

## Stack (all free / open-source)
| Stage | Tool |
|---|---|
| Experiment tracking + registry | **MLflow** |
| Training | scikit-learn |
| Serving | FastAPI + Docker |
| Orchestration | Kubernetes; **Airflow** DAG reference |
| CI/CD (Continuous Training) | GitHub Actions |
| Model/serving monitoring | **Prometheus + Grafana** |
| Data-drift monitoring | **Evidently AI** |

> This is the most-requested 2026 MLOps combination — MLflow + Docker + Kubernetes + an
> orchestrator + Evidently — and it reuses the Docker/K8s/Prometheus skills already on your CV.

## Run it locally (2 minutes, CPU only)
```bash
pip install -r requirements.txt
python data/generate_data.py       # create datasets
python src/train.py                # trains + logs to MLflow (./mlruns)
python src/evaluate.py             # quality gate
mlflow ui                          # browse experiments at http://localhost:5000

# serve
uvicorn src.serve:app --port 8080
curl -X POST localhost:8080/predict -H 'content-type: application/json' \
  -d '{"tenure":3,"monthly_charges":95.0,"support_calls":5,"contract_type":0}'
```

## Demo the drift alert (great interview moment)
```bash
python data/generate_data.py --drift    # shift the live distribution
python src/monitor_drift.py             # Evidently flags it, writes drift_report.html
```
Open `drift_report.html` and screenshot it for your README. In CI, `drift-check.yml` does
this on a schedule and **opens a GitHub issue** when drift appears.

## Deploy on Kubernetes (free: k3s on one EC2 box)
```bash
kubectl create namespace mlops
kubectl apply -f k8s/deployment.yaml     # image built + pushed by CI to GHCR
```

## Layout
```
data/generate_data.py   self-contained synthetic dataset
src/train.py            train + MLflow tracking/registry
src/evaluate.py         quality gate (fails CI on weak model)
src/serve.py            FastAPI model API + Prometheus metrics
src/monitor_drift.py    Evidently data-drift check
.github/workflows/      CI train→gate→build, scheduled drift check
k8s/                    serving Deployment + Service
orchestration/          Airflow DAG (orchestrator reference)
monitoring/             Prometheus alerts + Grafana dashboard
docs/architecture.md    full walkthrough
```

## License
MIT
