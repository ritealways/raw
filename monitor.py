"""
monitor.py
----------
Two things can go wrong silently after deployment:
1. The world changes and the model's error creeps up (concept drift) --
   caught by comparing realized MAPE against the offline baseline.
2. The input feature distributions shift (e.g. a new region added, a data
   source changes units) even before errors show up -- caught by PSI
   (Population Stability Index) on each feature.

This script is meant to run monthly, right after realized actuals for last
month's forecast become available.
"""
import numpy as np
import pandas as pd
from config import FEATURE_TABLE_PATH

DRIFT_ALERT_THRESHOLD = 0.2  # PSI > 0.2 is the common industry rule-of-thumb for "material drift"


def population_stability_index(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """
    Standard PSI: bucket the reference ("expected"/training) distribution
    into deciles, then compare the % of the new ("actual"/production) data
    falling in each bucket. Large mismatches -> large PSI.
    PSI < 0.1: no significant shift. 0.1-0.2: moderate. > 0.2: investigate.
    """
    expected, actual = expected.dropna(), actual.dropna()
    breakpoints = np.quantile(expected, np.linspace(0, 1, bins + 1))
    breakpoints[0], breakpoints[-1] = -np.inf, np.inf

    expected_pct = pd.cut(expected, breakpoints).value_counts(normalize=True).sort_index()
    actual_pct = pd.cut(actual, breakpoints).value_counts(normalize=True).sort_index()

    eps = 1e-4
    psi = np.sum((actual_pct - expected_pct) * np.log((actual_pct + eps) / (expected_pct + eps)))
    return float(psi)


def check_feature_drift(reference_window_months: int = 24, recent_window_months: int = 3):
    """
    Compares the most recent `recent_window_months` of feature values
    against the `reference_window_months` used at training time, per
    feature, and flags any with PSI above threshold.
    """
    df = pd.read_csv(FEATURE_TABLE_PATH, parse_dates=["month"])
    numeric_features = ["lag_1", "roll_mean_3", "roll_mean_12", "in_network_providers",
                         "avg_appointment_wait_days", "oon_rate"]

    max_month = df["month"].max()
    reference = df[df["month"] <= max_month - pd.DateOffset(months=recent_window_months)]
    reference = reference[reference["month"] > max_month - pd.DateOffset(months=reference_window_months)]
    recent = df[df["month"] > max_month - pd.DateOffset(months=recent_window_months)]

    report = {}
    for feat in numeric_features:
        psi = population_stability_index(reference[feat], recent[feat])
        report[feat] = psi
        flag = "🔴 DRIFT" if psi > DRIFT_ALERT_THRESHOLD else "🟢 stable"
        print(f"{feat:28s} PSI={psi:.3f}  {flag}")

    drifted = {k: v for k, v in report.items() if v > DRIFT_ALERT_THRESHOLD}
    if drifted:
        print(f"\n⚠️  {len(drifted)} feature(s) drifted beyond {DRIFT_ALERT_THRESHOLD}: {list(drifted.keys())}")
        # In production: post to Slack/PagerDuty here rather than just print.
    return report


if __name__ == "__main__":
    check_feature_drift()
