import joblib
from django.conf import settings

_models = {}

# Safety layer: dangerous words always mean HIGH priority
DANGER_WORDS = (
    "fire", "smoke", "spark", "short circuit", "burning", "gas leak", "gas smell",
    "electric shock", "flood", "injured", "collapse", "stolen", "broke into", "break-in",
)


def _load(name):
    if name not in _models:
        _models[name] = joblib.load(settings.BASE_DIR / "ml" / name)
    return _models[name]


def predict_category(text):
    """Returns (category_code, confidence). If anything fails, returns (None, 0)."""
    try:
        model = _load("complaint_model.joblib")
        probs = model.predict_proba([text])[0]
        best = probs.argmax()
        return model.classes_[best], float(probs[best])
    except Exception:
        return None, 0.0


def predict_priority(text):
    """Returns (priority_code, confidence). Danger words override the model."""
    lowered = text.lower()
    if any(word in lowered for word in DANGER_WORDS):
        return "HIGH", 1.0
    try:
        model = _load("priority_model.joblib")
        probs = model.predict_proba([text])[0]
        best = probs.argmax()
        return model.classes_[best], float(probs[best])
    except Exception:
        return None, 0.0