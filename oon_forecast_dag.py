"""
oon_forecast_dag.py
--------------------
Why Airflow and not cron: cron can't express "only promote the new model if
it beats the old one" or retry/alert on partial failure with visibility.
Airflow gives dependency ordering, retries, and a UI the team can check
without reading logs.

This DAG runs the SAME modules we already wrote and tested locally
(data_prep -> features -> train -> forecast). That's the point: nothing
about the modeling code changes when it goes to production, only how it's
invoked and scheduled.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "network-analytics",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": True,
    "email": ["network-analytics-alerts@company.com"],
}

with DAG(
    dag_id="oon_forecast_monthly",
    default_args=default_args,
    schedule_interval="0 6 3 * *",  # 3rd of every month, 6am -- after claims close for the prior month
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["forecasting", "network-analytics"],
) as dag:

    build_features = BashOperator(
        task_id="build_modeling_and_feature_tables",
        bash_command="python /app/src/data_prep.py && python /app/src/features.py",
    )

    def _train_and_evaluate(**context):
        """
        Wraps train.train_all_horizons and pushes the resulting metrics to
        XCom so the promotion-gate task can read them without re-computing.
        """
        import sys
        sys.path.insert(0, "/app/src")
        from train import train_all_horizons
        metrics = train_all_horizons(n_trials=25)
        context["ti"].xcom_push(key="metrics", value=metrics)

    train_task = PythonOperator(task_id="train_challenger", python_callable=_train_and_evaluate)

    def _promote_if_better(**context):
        """
        Champion/challenger gate: only replace the production model if the
        new one's MAPE is not worse than the old one plus a small tolerance.
        This is what prevents a bad retrain (e.g. from a data glitch) from
        silently degrading production forecasts.
        """
        import json
        import mlflow
        new_metrics = context["ti"].xcom_pull(key="metrics", task_ids="train_challenger")
        client = mlflow.tracking.MlflowClient()
        current_prod = client.get_latest_versions("oon_xgb_h1", stages=["Production"])
        tolerance = 0.5  # percentage points of MAPE the challenger is allowed to be worse by

        promote = True
        if current_prod:
            old_mape = float(client.get_run(current_prod[0].run_id).data.metrics.get("xgb_mape", 999))
            new_mape = new_metrics["h1"]["xgb_mape"]
            promote = new_mape <= old_mape + tolerance
            print(f"challenger MAPE={new_mape:.2f} vs champion={old_mape:.2f} -> promote={promote}")

        if promote:
            latest_version = client.get_latest_versions("oon_xgb_h1", stages=["None"])[0]
            client.transition_model_version_stage(
                name="oon_xgb_h1", version=latest_version.version, stage="Production",
                archive_existing_versions=True,
            )
        else:
            print("challenger did not beat champion -- keeping current production model")

    promote_task = PythonOperator(task_id="promote_if_better", python_callable=_promote_if_better)

    generate_forecasts = BashOperator(
        task_id="generate_batch_forecasts",
        bash_command="python /app/src/forecast.py",
    )

    check_drift = BashOperator(
        task_id="check_feature_drift",
        bash_command="python /app/src/monitor.py",
    )

    build_features >> train_task >> promote_task >> generate_forecasts >> check_drift
