import random
import pandas as pd

random.seed(42)

BASE = {"BREAKFAST": 0.62, "LUNCH": 0.78, "DINNER": 0.92}
CODE = {"BREAKFAST": 0, "LUNCH": 1, "DINNER": 2}


def eat_rate(weekday, meal):
    rate = BASE[meal]
    if weekday in (5, 6):                      # weekend
        rate -= {"BREAKFAST": 0.12, "LUNCH": 0.08, "DINNER": 0.0}[meal]
    if weekday == 4 and meal == "DINNER":      # Friday: many go home
        rate -= 0.12
    if weekday == 6 and meal == "DINNER":      # Sunday: people return
        rate += 0.03
    rate += random.gauss(0, 0.03)              # random daily noise
    return min(max(rate, 0.3), 1.0)


rows = []
for date in pd.date_range("2026-01-01", periods=240):
    total = random.randint(50, 70)
    for meal in BASE:
        eating = round(total * eat_rate(date.weekday(), meal))
        rows.append({
            "date": date.date(), "weekday": date.weekday(), "meal": meal,
            "meal_code": CODE[meal], "total": total, "eating": eating,
            "fraction": eating / total,
        })

pd.DataFrame(rows).to_csv("ml/meals.csv", index=False)
print("Dataset created:", len(rows), "rows")