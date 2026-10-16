import joblib
from django.conf import settings

_model = None


def predict_category(text):
    """Returns (category_code, confidence). If anything fails, returns (None, 0)."""
    global _model
    try:
        if _model is None:
            _model = joblib.load(settings.BASE_DIR / "ml" / "complaint_model.joblib")
        probs = _model.predict_proba([text])[0]
        best = probs.argmax()
        return _model.classes_[best], float(probs[best])
    except Exception:
        return None, 0.0
    