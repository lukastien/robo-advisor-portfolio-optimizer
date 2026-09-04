"""
generate_client_profiles.py
============================
Generates synthetic client risk profiles for the robo-advisor allocation
engine, with a fixed random seed for reproducibility.

IMPORTANT: Client profiles are entirely synthetic (no real client data
exists for this project). Stock price data used elsewhere in this project
(data/raw/stock_prices.csv) IS real -- see README.md "Data Note" for the
full breakdown of what's real vs. synthetic.

Usage:
    python generate_client_profiles.py
Outputs:
    data/raw/client_profiles.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_CLIENTS = 200
RISK_TIERS = ["Conservative", "Moderate", "Aggressive"]
TIER_PROBABILITIES = [0.35, 0.40, 0.25]


def generate_profiles(n=N_CLIENTS):
    rows = []
    for client_id in range(1, n + 1):
        risk_tier = rng.choice(RISK_TIERS, p=TIER_PROBABILITIES)

        # age and horizon loosely correlated with risk tier
        if risk_tier == "Conservative":
            age = int(rng.integers(50, 75))
            horizon_years = int(rng.integers(3, 10))
        elif risk_tier == "Moderate":
            age = int(rng.integers(35, 60))
            horizon_years = int(rng.integers(8, 20))
        else:
            age = int(rng.integers(22, 45))
            horizon_years = int(rng.integers(15, 35))

        income_bracket = rng.choice(
            ["<$50k", "$50k-$100k", "$100k-$200k", "$200k+"],
            p=[0.2, 0.35, 0.30, 0.15]
        )

        # risk tolerance score, 1-10, roughly aligned with tier but with noise
        base_score = {"Conservative": 3, "Moderate": 6, "Aggressive": 9}[risk_tier]
        risk_tolerance_score = int(np.clip(rng.normal(base_score, 1.2), 1, 10))

        rows.append({
            "client_id": client_id,
            "age": age,
            "income_bracket": income_bracket,
            "investment_horizon_years": horizon_years,
            "risk_tolerance_score": risk_tolerance_score,
            "risk_tier": risk_tier,
        })

    return pd.DataFrame(rows)


def main():
    profiles_df = generate_profiles()
    out_path = OUTPUT_DIR / "client_profiles.csv"
    profiles_df.to_csv(out_path, index=False)
    print(f"Wrote {len(profiles_df)} synthetic client profiles to {out_path}")


if __name__ == "__main__":
    main()
