"""
forecast_engine.py

Swap-in point for the production forecasting model. Contract: takes the
long-format DataFrame Anaplan's export produces (dimension columns + a time
column + a value column) and returns the same shape, because that is what
an Anaplan import action expects on the other side   the import maps
columns to the target module's line items and dimensions by name.

Replace `forecast_series()` with the real model call (e.g. a saved
LightGBM/XGBoost pipeline's .predict()). Everything else in this file is
plumbing to get data into and out of that call.
"""

import pandas as pd
import numpy as np


def forecast_series(history: pd.Series, periods_ahead: int = 3) -> pd.Series:
    """One (Region, Product) series in -> forecasted future periods out.
    Placeholder: linear trend. Swap for the production model's predict()
    call   keep the same Series-in, Series-out contract."""
    y = history.values.astype(float)
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y) + periods_ahead)
    return pd.Series(slope * future_x + intercept)


def run_forecast(export_df: pd.DataFrame, periods_ahead: int = 3,
                  dim_cols=("Region", "Product"), time_col="Month",
                  value_col="Actual Demand", output_value_col="Forecast Demand") -> pd.DataFrame:
    """Anaplan export DataFrame -> forecast DataFrame shaped for Anaplan import."""
    df = export_df.copy()
    df[time_col] = pd.to_datetime(df[time_col])

    results = []
    for key, grp in df.groupby(list(dim_cols)):
        grp = grp.sort_values(time_col)
        preds = forecast_series(grp[value_col], periods_ahead)
        last = grp[time_col].max()
        future_periods = pd.date_range(last, periods=periods_ahead + 1, freq="MS")[1:]
        dims = key if isinstance(key, tuple) else (key,)
        for period, pred in zip(future_periods, preds):
            row = dict(zip(dim_cols, dims))
            row[time_col] = period.strftime("%Y-%m")
            row[output_value_col] = round(float(pred), 1)
            results.append(row)

    return pd.DataFrame(results)
