# OON Cost Forecasting — End-to-End Python Project + MLOps Guide

A working (not pseudocode) pipeline that forecasts out-of-network insurance
cost 1–6 months ahead per Region × Specialty, so a network team can recruit
doctors before costs spike instead of reading about it in a quarterly report.

Every file in `src/` runs on its own and was tested against ~720k synthetic
claims while writing this. Run the whole thing with:

```bash
pip install -r requirements.txt
cd src
python generate_data.py   # stands in for a warehouse query
python pipeline.py        # data_prep -> features -> train -> forecast
```

## 1. Project layout & why it's split this way

```
src/
  config.py       # single source of truth for paths/constants
  generate_data.py# synthetic claims+network tables (swap for a warehouse query)
  data_prep.py    # cleaning, monthly aggregation, calendar reindexing
  features.py     # lags, rolling stats, momentum, calendar, domain features
  train.py         # baselines, walk-forward CV + Optuna, direct multi-horizon XGBoost
  forecast.py     # 1-6mo forecasts + 80% intervals + alert logic
  pipeline.py     # orchestrates all of the above
  train_with_mlflow.py  # same training logic, wrapped with MLflow tracking/registry
  monitor.py      # realized-error + PSI feature-drift checks
dags/
  oon_forecast_dag.py   # Airflow DAG for the monthly production run
Dockerfile
```

**Why one file per stage instead of a notebook:** each stage has a single,
testable responsibility, and — this is the part that matters for
production — the exact same functions get imported by the Airflow DAG.
There's no "translate the notebook into production code" step, which is
where train/serve skew usually creeps in.

## 2. Why this modeling approach (and not ARIMA or LSTM)

| Option | Verdict | Reasoning |
|---|---|---|
| ARIMA/SARIMA per series | Baseline only | 100 Region×Specialty series = 100 models to maintain, and it can't use features like network density. |
| LSTM / N-BEATS | Overkill | ~40-60 monthly points per series is too little for deep learning to generalize; also hard to explain to a non-technical business team. |
| **Global XGBoost (chosen)** | ✅ | One model learns across *all* series, mixes numeric lags with categorical region/specialty, captures interactions ("cardiology + rural + low network density"), and gives feature importances the business actually trusts. |

This reframes forecasting as **supervised regression**: predict next-month
(log) cost from lagged/rolling/domain features. It's the same approach used
by the top solutions in the M5 forecasting competition.

The measured result in this repo (synthetic data, `artifacts/metrics.json`):
XGBoost beats the seasonal-naive baseline by roughly 6–8 MAPE points at
every horizon, with ~72–74% directional accuracy on "did cost go up or
down."

## 3. Key engineering decisions, and why

- **`log1p` target transform** — OON cost is right-skewed and multiplicative;
  this stabilizes variance so a few huge segments don't dominate the loss.
  Inverse with `expm1`.
- **`.shift(1)` before every rolling window** (`features.py`) — the #1
  leakage bug in time-series feature engineering: without the shift, a
  rolling mean at month *t* silently includes month *t*'s own value.
- **`TimeSeriesSplit` walk-forward CV, never random K-fold** (`train.py`) —
  random shuffling would validate on "past" data relative to what the model
  trained on.
- **Direct, not recursive, multi-horizon forecasting** — one model per
  horizon (`target_h1`...`target_h6`) rather than feeding today's
  prediction back in as tomorrow's input, which compounds error.
- **Quantile (pinball loss) models at q=0.1/0.9** — gives an 80% interval so
  the network team can require the *lower bound* to also be rising before
  triggering a HIGH alert (this is what keeps false-alarm rate down).
- **XGBoost native categoricals** for region/specialty instead of one-hot —
  fewer columns, and it handles unseen categories more gracefully at
  serving time.

## 4. Productionizing this with MLOps

A notebook that produces a good MAPE once is not a production system. Going
from "it worked when I ran it" to "it's still correct and running six
months from now, unattended" means adding four things: **automation,
tracking, monitoring, and a safety net.** Here's each one, mapped to an
actual file in this repo.

### 4.1 Automation — Airflow (`dags/oon_forecast_dag.py`)

Cron can run a script on a schedule; it can't express "retry twice with
backoff," "email on failure," or "only replace production if the new model
is actually better." The DAG:

```
build_modeling_and_feature_tables >> train_challenger >> promote_if_better >> generate_batch_forecasts >> check_feature_drift
```

runs on the 3rd of every month (after claims close for the prior month),
calling the *exact same* `data_prep.py` / `features.py` / `train.py` /
`forecast.py` functions you already ran locally — nothing is rewritten for
production.

**Why this ordering matters:** training happens before promotion, and
forecasting happens after promotion, so a bad retrain never reaches the
dashboard the network team looks at.

### 4.2 Tracking & registry — MLflow (`src/train_with_mlflow.py`)

Every run logs:
- **Params** — the Optuna-tuned hyperparameters, so you can answer "why did
  this model behave differently" six months later.
- **Metrics** — MAPE, baseline MAPE, train/test sizes — so runs are
  comparable in the MLflow UI, not scattered across notebook cell outputs.
- **The model artifact itself**, registered under a name like `oon_xgb_h1`.

Registering (rather than just saving to disk) is what makes **champion/
challenger promotion** possible: the DAG's `promote_if_better` task pulls
the currently-`Production`-staged model's logged MAPE, compares it to the
new challenger's, and only promotes if the challenger is not worse than a
small tolerance. This is the single control that prevents a bad data month
from silently degrading what the business sees.

### 4.3 Feature consistency — a feature store (conceptual next step)

Right now, `features.py` is imported by both training and forecasting, so
train/serve skew from *code* divergence isn't possible. The remaining risk
is *data* divergence — e.g., if a dashboard team recomputes "rolling 3-month
average" slightly differently for a different report. A feature store
(Feast is the common open-source choice) centralizes the computed lag/
rolling features in one place so every consumer reads the identical value.
Worth adding once more than one downstream system needs the same features;
not necessary for a single pipeline like this one.

### 4.4 Monitoring — realized error + drift (`src/monitor.py`)

Two independent failure modes, caught two different ways:

1. **Concept drift** — the relationship between features and target changes
   (e.g., a new regulation shifts OON behavior). Caught by comparing
   *realized* MAPE (once actuals come in) against the offline baseline
   month over month.
2. **Data/feature drift** — an input distribution shifts even before errors
   show up (a new region onboarded, a source system changes units, a
   pipeline bug). Caught with **PSI** (Population Stability Index) per
   feature: PSI < 0.1 is fine, 0.1–0.2 worth watching, > 0.2 needs
   investigation. Running `monitor.py` against this repo's own data
   actually flagged `avg_appointment_wait_days` at PSI=0.27 — correctly,
   since the synthetic data has a real network-density shock baked in.

In production, both checks post to Slack/PagerDuty rather than stdout.

### 4.5 The safety net — fallback and rollback

Two things that must be true regardless of how good the model is:
- **Fallback:** if the pipeline fails or the model can't load, the DAG
  should serve the seasonal-naive forecast rather than a blank dashboard.
  The business should always see *a* number, even a less accurate one.
- **Rollback:** because MLflow keeps every prior model version, reverting
  a bad promotion is a one-line `transition_model_version_stage` call, not
  a re-run of the whole training pipeline.

### 4.6 Containerization (`Dockerfile`)

One image, different `CMD` per task (`data_prep.py`, `train.py`,
`forecast.py`, `monitor.py`). This is what actually guarantees the code
that produced your offline MAPE is the code running in the DAG — pinned
Python version, pinned library versions, same OS.

### 4.7 CI/CD (what to add next)

Not built here, but the natural next layer: a GitHub Actions workflow that,
on every PR, runs `data_prep.py`/`features.py`/`train.py` against a small
fixture dataset and asserts the resulting MAPE doesn't regress beyond
tolerance — a regression test for model quality, not just code syntax.

## 5. Results reference

See `artifacts/metrics.json` for the exact per-horizon numbers from the
last run, and `artifacts/forecast_table.csv` for the full forecast +
alert-level table across every Region × Specialty segment.
