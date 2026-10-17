import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["invoices_total", "late_ratio", "unpaid_count", "max_days_overdue"]

df = pd.read_csv("ml/rent_risk.csv")
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURES], df["will_be_late"], test_size=0.2, random_state=42, stratify=df["will_be_late"]
)

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)[:, 1]
baseline = max(y_test.mean(), 1 - y_test.mean())          # always predict the majority class

print(f"Baseline accuracy (majority class): {baseline:.2f}")
print(f"Model accuracy:                     {accuracy_score(y_test, pred):.2f}")
print(f"ROC AUC:                            {roc_auc_score(y_test, proba):.2f}")
print(classification_report(y_test, pred))

print("Feature weights (bigger = pushes risk up):")
for name, w in zip(FEATURES, model[-1].coef_[0]):
    print(f"  {name:18} {w:+.2f}")

joblib.dump(model, "ml/risk_model.joblib")
print("Model saved: ml/risk_model.joblib")