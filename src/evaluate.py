#!/usr/bin/env python3
"""Quality gate: fail (non-zero exit) if the model misses thresholds, so CI won't ship it."""
import json
import os
import sys

MIN_ACC = float(os.getenv("MIN_ACCURACY", "0.76"))
MIN_F1 = float(os.getenv("MIN_F1", "0.60"))


def main():
    m = json.load(open("models/metrics.json"))
    print("metrics:", m)
    print(f"gate: accuracy>={MIN_ACC}  f1>={MIN_F1}")
    ok = m["accuracy"] >= MIN_ACC and m["f1"] >= MIN_F1
    if not ok:
        print("❌ GATE FAILED — model will NOT be promoted/deployed.")
        sys.exit(1)
    print("✅ GATE PASSED — model approved for promotion.")


if __name__ == "__main__":
    main()
