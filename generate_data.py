"""
generate_data.py
----------------
Why this file exists:
You won't have the insurer's real claims warehouse, but the *shape* of the
pipeline is what matters for learning it end-to-end. This script builds
realistic-looking Claims and Network tables with genuine signal baked in
(a network-density shock that causes OON cost to rise), so every later
stage — cleaning, features, modeling, evaluation — has something real to
find. Swap this file for a warehouse query and nothing downstream changes.
"""
import numpy as np
import pandas as pd
from config import RAW_CLAIMS_PATH, NETWORK_PATH, RANDOM_SEED

rng = np.random.default_rng(RANDOM_SEED)

REGIONS = [f"{p}-{n:02d}" for p in ["NE", "SW", "MW", "SE", "W"] for n in range(1, 5)]
SPECIALTIES = ["Cardiology", "Orthopedics", "Dermatology", "Neurology", "Psychiatry"]
MONTHS = pd.date_range("2020-01-01", "2024-12-01", freq="MS")


def generate_network_table():
    """
    One row per region x specialty x month describing network health.
    Why simulate a "shock": a real project's tree model earns its keep by
    picking up exactly this kind of structural cause (docs leaving -> OON
    cost rises), not just calendar seasonality. Without a shock in the data,
    a model could look fine while ignoring the feature the business most
    cares about.
    """
    rows = []
    for region in REGIONS:
        for specialty in SPECIALTIES:
            base_providers = rng.integers(10, 40)
            wait = rng.uniform(8, 18)
            # Pick a random month (2/3 of the way through history) where a
            # network shock begins for ~40% of segments.
            shock_start = None
            if rng.random() < 0.4:
                shock_start = MONTHS[int(len(MONTHS) * rng.uniform(0.5, 0.8))]
            providers = base_providers
            for month in MONTHS:
                if shock_start is not None and month >= shock_start:
                    months_since = (month.year - shock_start.year) * 12 + (month.month - shock_start.month)
                    providers = max(3, base_providers - months_since * rng.uniform(0.3, 0.9))
                    wait_now = wait + months_since * rng.uniform(0.4, 1.1)
                else:
                    providers = base_providers + rng.normal(0, 0.5)
                    wait_now = wait + rng.normal(0, 0.5)
                rows.append({
                    "region": region, "specialty": specialty, "month": month,
                    "in_network_providers": max(1, round(providers)),
                    "avg_appointment_wait_days": max(1, round(wait_now, 1)),
                    "terminations_last_month": rng.poisson(0.3),
                })
    return pd.DataFrame(rows)


def generate_claims_table(network_df):
    """
    Simulate individual claims. OON probability and cost rise when network
    density falls and wait times rise -- the causal story the feature
    engineering step is designed to capture.
    """
    net_lookup = network_df.set_index(["region", "specialty", "month"])
    claim_rows = []
    claim_id = 0
    for (region, specialty, month), net_row in net_lookup.iterrows():
        # Seasonal + trend base volume of visits for this segment/month
        seasonal = 1 + 0.15 * np.sin(2 * np.pi * (month.month / 12))
        base_visits = rng.poisson(120 * seasonal)
        density_factor = 25 / net_row["in_network_providers"]  # fewer docs -> higher OON odds
        oon_prob = np.clip(0.08 * density_factor + net_row["avg_appointment_wait_days"] * 0.004, 0.03, 0.6)

        for _ in range(base_visits):
            is_oon = rng.random() < oon_prob
            base_cost = {"Cardiology": 900, "Orthopedics": 1100, "Dermatology": 350,
                         "Neurology": 800, "Psychiatry": 250}[specialty]
            cost_mult = 1.4 if is_oon else 1.0  # no negotiated discount -> insurer pays more
            amount = max(20, rng.gamma(4, base_cost * cost_mult / 4))
            # rare catastrophic claim, tests the winsorization step downstream
            if rng.random() < 0.001:
                amount *= rng.uniform(15, 40)
            claim_rows.append({
                "claim_id": f"C{claim_id}",
                "member_id": f"M{rng.integers(0, 50000)}",
                "service_date": month + pd.Timedelta(days=int(rng.integers(0, 27))),
                "provider_id": f"P{rng.integers(0, 5000)}",
                "region": region, "specialty": specialty,
                "is_oon": int(is_oon),
                "allowed_amount": round(amount, 2),
                "claim_count": 1,
            })
            claim_id += 1
    return pd.DataFrame(claim_rows)


if __name__ == "__main__":
    network_df = generate_network_table()
    claims_df = generate_claims_table(network_df)

    # inject a handful of dirty rows on purpose, so data_prep.py has real work to do
    dup = claims_df.sample(50, random_state=RANDOM_SEED)
    claims_df = pd.concat([claims_df, dup], ignore_index=True)
    claims_df.loc[claims_df.sample(20, random_state=1).index, "region"] = np.nan
    claims_df.loc[claims_df.sample(20, random_state=2).index, "allowed_amount"] *= -1

    network_df.to_csv(NETWORK_PATH, index=False)
    claims_df.to_csv(RAW_CLAIMS_PATH, index=False)
    print(f"claims: {claims_df.shape}, network: {network_df.shape}")
    print(f"written to {RAW_CLAIMS_PATH} and {NETWORK_PATH}")
