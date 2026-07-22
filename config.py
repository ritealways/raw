"""
config.py
---------
Why a config module at all?
Every stage (data prep, features, training, forecasting) needs the same paths
and constants. Hard-coding them in each script means they drift out of sync.
One config = one source of truth, and it's the first thing MLOps tooling
(Airflow, Docker, CI) will want to override via env vars later.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts")

RAW_CLAIMS_PATH = os.path.join(DATA_DIR, "claims.csv")
NETWORK_PATH = os.path.join(DATA_DIR, "network.csv")
MODELING_TABLE_PATH = os.path.join(DATA_DIR, "modeling_table.csv")
FEATURE_TABLE_PATH = os.path.join(DATA_DIR, "feature_table.csv")

MODEL_PATH_TEMPLATE = os.path.join(ARTIFACT_DIR, "xgb_h{h}.json")
QUANTILE_MODEL_TEMPLATE = os.path.join(ARTIFACT_DIR, "xgb_h{h}_q{q}.json")
METRICS_PATH = os.path.join(ARTIFACT_DIR, "metrics.json")
FORECAST_OUTPUT_PATH = os.path.join(ARTIFACT_DIR, "forecast_table.csv")

# Forecast horizons: 1..6 months, matching the business ask ("act 60+ days ahead")
HORIZONS = [1, 2, 3, 4, 5, 6]

# Lags chosen from ACF/PACF reasoning in the design doc:
# short memory (1-3) + half-year + yearly seasonality (12)
LAGS = [1, 2, 3, 6, 12]
ROLLING_WINDOWS = [3, 6, 12]

RANDOM_SEED = 42

# Alert thresholds — business-facing, not a modeling constant, but centralizing
# it here means the network team can tune it without touching pipeline code.
ALERT_HIGH_THRESHOLD = 0.20   # +20% 6-month growth => HIGH alert
ALERT_WATCH_THRESHOLD = 0.08  # +8%..+20% => WATCH

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)
