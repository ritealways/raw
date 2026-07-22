"""
data_prep.py
------------
Turns raw claim-level rows into a clean monthly Region x Specialty table.
Every cleaning decision below is one a real claims dataset forces on you --
see the inline "why" comments.
"""
import numpy as np
import pandas as pd
from config import RAW_CLAIMS_PATH, NETWORK_PATH, MODELING_TABLE_PATH


def load_raw():
    claims = pd.read_csv(RAW_CLAIMS_PATH, parse_dates=["service_date"])
    network = pd.read_csv(NETWORK_PATH, parse_dates=["month"])
    return claims, network


def clean_claims(claims: pd.DataFrame) -> pd.DataFrame:
    n0 = len(claims)

    # 1. Duplicate claims double-count cost -> drop by claim_id.
    claims = claims.drop_duplicates(subset="claim_id")

    # 2. Negative allowed_amount = a reversal/adjustment, not new spend.
    #    We floor at 0 rather than dropping, so claim_count stays consistent
    #    with allowed_amount for that row.
    claims["allowed_amount"] = claims["allowed_amount"].clip(lower=0)

    # 3. Missing region: real pipelines would look it up via provider_id;
    #    here we bucket to UNKNOWN so the row isn't silently lost and doesn't
    #    pollute a real region's trend.
    claims["region"] = claims["region"].fillna("UNKNOWN")
    claims = claims[claims["region"] != "UNKNOWN"]  # drop from modeling grain

    # 4. Winsorize extreme single claims (e.g. one catastrophic surgery) at
    #    the 99th percentile. A single $40k claim shouldn't look like a
    #    network trend to the model.
    cap = claims["allowed_amount"].quantile(0.99)
    n_capped = (claims["allowed_amount"] > cap).sum()
    claims["allowed_amount"] = claims["allowed_amount"].clip(upper=cap)

    print(f"clean_claims: {n0} -> {len(claims)} rows, capped {n_capped} outlier claims at {cap:.0f}")
    return claims


def aggregate_to_monthly(claims: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate OON claims to monthly Region x Specialty grain.
    Why freq='MS' (month-start): every lag/rolling feature downstream assumes
    a perfectly regular monthly index. Any other granularity breaks lag
    alignment silently.
    """
    oon = claims[claims["is_oon"] == 1].copy()
    monthly = (
        oon.groupby(["region", "specialty", pd.Grouper(key="service_date", freq="MS")])
        .agg(oon_cost=("allowed_amount", "sum"), oon_claims=("claim_id", "count"))
        .reset_index()
        .rename(columns={"service_date": "month"})
    )

    # also need total claims (in+out of network) per segment/month, to build
    # the OON *rate* as a secondary signal (per the design doc, section 4)
    total = (
        claims.groupby(["region", "specialty", pd.Grouper(key="service_date", freq="MS")])
        .agg(total_claims=("claim_id", "count"))
        .reset_index()
        .rename(columns={"service_date": "month"})
    )
    monthly = monthly.merge(total, on=["region", "specialty", "month"], how="left")
    monthly["oon_rate"] = monthly["oon_claims"] / monthly["total_claims"]
    return monthly


def reindex_full_calendar(monthly: pd.DataFrame) -> pd.DataFrame:
    """
    Why: trees compute lag/rolling features off a positional shift. If a
    segment has a gap month, a naive .shift(1) would silently pull in the
    wrong month's value. We reindex every (region, specialty) pair to a
    continuous monthly range and fill true gaps with 0 cost (no OON claims
    that month is a real, meaningful zero -- not missing data).
    """
    full_frames = []
    for (region, specialty), g in monthly.groupby(["region", "specialty"]):
        g = g.set_index("month").sort_index()
        full_idx = pd.date_range(g.index.min(), g.index.max(), freq="MS")
        g = g.reindex(full_idx)
        g["region"] = region
        g["specialty"] = specialty
        for col in ["oon_cost", "oon_claims", "total_claims"]:
            g[col] = g[col].fillna(0)
        g["oon_rate"] = g["oon_rate"].fillna(0)
        g.index.name = "month"
        full_frames.append(g.reset_index())
    return pd.concat(full_frames, ignore_index=True)


def drop_sparse_series(df: pd.DataFrame, min_months: int = 24) -> pd.DataFrame:
    """Segments with < min_months of history can't support reliable lag_12
    features; the design doc's answer is to group them into a hierarchy
    fallback (handled at forecast time), but for training we simply exclude
    them so they don't inject noisy near-empty series into the global model."""
    counts = df.groupby(["region", "specialty"])["month"].transform("count")
    kept = df[counts >= min_months]
    print(f"drop_sparse_series: {df[['region','specialty']].drop_duplicates().shape[0]} "
          f"-> {kept[['region','specialty']].drop_duplicates().shape[0]} segments kept (>= {min_months} months)")
    return kept


def merge_network_features(df: pd.DataFrame, network: pd.DataFrame) -> pd.DataFrame:
    return df.merge(network, on=["region", "specialty", "month"], how="left")


def build_modeling_table() -> pd.DataFrame:
    claims, network = load_raw()
    claims = clean_claims(claims)
    monthly = aggregate_to_monthly(claims)
    monthly = reindex_full_calendar(monthly)
    monthly = merge_network_features(monthly, network)
    monthly = drop_sparse_series(monthly, min_months=24)

    # Target transform: OON cost is right-skewed & multiplicative -> log1p
    # stabilizes variance so a few huge segments don't dominate the loss.
    monthly["y"] = np.log1p(monthly["oon_cost"])

    monthly = monthly.sort_values(["region", "specialty", "month"]).reset_index(drop=True)
    monthly.to_csv(MODELING_TABLE_PATH, index=False)
    print(f"modeling table: {monthly.shape} -> {MODELING_TABLE_PATH}")
    return monthly


if __name__ == "__main__":
    build_modeling_table()
