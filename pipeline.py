"""
pipeline.py
-----------
Single entrypoint that runs every stage in order. This is also, almost
verbatim, what an Airflow DAG or a `python -m pipeline` CI job would call --
see MLOPS_GUIDE.md for how this exact function gets wrapped for production.
"""
import time
from data_prep import build_modeling_table
from features import build_feature_table
from train import train_all_horizons
from forecast import generate_forecasts


def run_pipeline(n_trials: int = 15):
    t0 = time.time()
    print("== 1/4 building modeling table ==")
    build_modeling_table()
    print("== 2/4 building feature table ==")
    build_feature_table()
    print("== 3/4 training models ==")
    train_all_horizons(n_trials=n_trials)
    print("== 4/4 generating forecasts ==")
    forecasts = generate_forecasts()
    print(f"pipeline complete in {time.time() - t0:.1f}s")
    return forecasts


if __name__ == "__main__":
    run_pipeline()
