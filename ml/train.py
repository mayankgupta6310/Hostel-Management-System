import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

df = pd.read_csv("ml/complaints.csv")

X_train, X_test, y_train, y_test = train_test_split(
    df.text, df.category, test_size=0.2, random_state=42, stratify=df.category
)

model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), lowercase=True),
    LogisticRegression(max_iter=1000),
)
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test)))
joblib.dump(model, "ml/complaint_model.joblib")
print("Model saved: ml/complaint_model.joblib")