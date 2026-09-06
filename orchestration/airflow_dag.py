"""Reference Airflow DAG for the churn MLOps lifecycle.

Shows the orchestration layer job listings ask for (Airflow/Kubeflow). The same
steps run in GitHub Actions for the free demo; this DAG is how you'd schedule them
on a real Airflow deployment.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="churn_mlops_pipeline",
    schedule="0 3 * * 1",          # weekly Monday 03:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["mlops", "churn"],
) as dag:
    gen = BashOperator(task_id="generate_data", bash_command="python data/generate_data.py")
    train = BashOperator(task_id="train", bash_command="python src/train.py")
    gate = BashOperator(task_id="evaluate_gate", bash_command="python src/evaluate.py")
    deploy = BashOperator(task_id="deploy",
                          bash_command="kubectl set image deployment/churn-api churn-api=$IMAGE -n mlops")
    monitor = BashOperator(task_id="monitor_drift", bash_command="python src/monitor_drift.py")

    gen >> train >> gate >> deploy >> monitor
