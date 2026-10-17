import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

df = pd.read_csv("ml/meals.csv", parse_dates=["date"]).sort_values("date")
FEATURES = ["weekday", "meal_code"]

# Time-based split: train on the first 80% of days, test on the last 20%
cut = int(len(df) * 0.8)
train, test = df.iloc[:cut], df.iloc[cut:]

model = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=42)
model.fit(train[FEATURES], train["fraction"])

pred_people = model.predict(test[FEATURES]) * test["total"]
model_mae = mean_absolute_error(test["eating"], pred_people)
baseline_mae = mean_absolute_error(test["eating"], test["total"])   # "everybody eats"

print(f"Baseline MAE (assume everyone eats): {baseline_mae:.1f} people")
print(f"Model MAE:                           {model_mae:.1f} people")

# Retrain on all data for the final model
model.fit(df[FEATURES], df["fraction"])
joblib.dump(model, "ml/meal_model.joblib")
print("Model saved: ml/meal_model.joblib")