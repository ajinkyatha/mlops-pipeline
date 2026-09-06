#!/usr/bin/env python3
"""Generate a synthetic customer-churn dataset (no external download needed).

Produces:
  data/train.csv      - training data
  data/reference.csv  - baseline distribution for drift monitoring
  data/current.csv    - 'live' data; pass --drift to inject drift for a demo
"""
import argparse
import numpy as np
import pandas as pd


def make(n, seed, drift=False):
    rng = np.random.default_rng(seed)
    tenure = rng.integers(0, 72, n)
    monthly = rng.normal(70 + (20 if drift else 0), 25, n).clip(15, 150)  # drift shifts spend up
    support_calls = rng.poisson(2 + (2 if drift else 0), n)
    contract = rng.choice([0, 1, 2], n, p=[0.5, 0.3, 0.2])  # 0=monthly,1=1yr,2=2yr
    # churn likelier for high spend, many calls, short tenure, monthly contract
    logit = (-3.2 + 0.05 * monthly + 0.6 * support_calls - 0.06 * tenure - 1.3 * contract)
    p = 1 / (1 + np.exp(-logit))
    churn = (rng.random(n) < p).astype(int)
    return pd.DataFrame({
        "tenure": tenure, "monthly_charges": monthly.round(2),
        "support_calls": support_calls, "contract_type": contract, "churn": churn,
    })


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--drift", action="store_true", help="inject drift into current.csv")
    a = ap.parse_args()
    make(4000, 1).to_csv("data/train.csv", index=False)
    make(1000, 2).to_csv("data/reference.csv", index=False)
    make(1000, 3, drift=a.drift).drop(columns=["churn"]).to_csv("data/current.csv", index=False)
    print("wrote data/train.csv, data/reference.csv, data/current.csv (drift=%s)" % a.drift)
