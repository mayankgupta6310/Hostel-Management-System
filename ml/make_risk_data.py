import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
rows = []

for _ in range(1500):
    n = int(rng.integers(2, 13))                 # invoices so far
    habit = rng.beta(1.2, 2.5)                   # hidden "lateness habit" of the tenant
    late = int(rng.binomial(n, habit))           # how many were late
    unpaid = int(rng.choice([0, 1, 2], p=[0.6, 0.3, 0.1]))
    days = int(rng.integers(1, 30)) if unpaid else 0

    # Hidden rule: chance that the NEXT invoice is paid late
    z = -2.0 + 3.5 * habit + 0.5 * unpaid + 0.02 * days
    prob = 1 / (1 + np.exp(-z))
    rows.append({
        "invoices_total": n,
        "late_ratio": late / n,
        "unpaid_count": unpaid,
        "max_days_overdue": days,
        "will_be_late": int(rng.random() < prob),
    })

pd.DataFrame(rows).to_csv("ml/rent_risk.csv", index=False)
print("Dataset created:", len(rows), "rows")