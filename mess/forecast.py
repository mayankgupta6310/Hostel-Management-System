import math

import joblib
import pandas as pd
from django.conf import settings

MEAL_CODES = {"BREAKFAST": 0, "LUNCH": 1, "DINNER": 2}
_model = None


def _load():
    global _model
    if _model is None:
        _model = joblib.load(settings.BASE_DIR / "ml" / "meal_model.joblib")
    return _model


def forecast_count(date, meal_type, total, known_off):
    """How many people to cook for. Returns None if the model is unavailable."""
    try:
        features = pd.DataFrame([{"weekday": date.weekday(), "meal_code": MEAL_CODES[meal_type]}])
        fraction = float(_load().predict(features)[0])
    except Exception:
        return None

    max_possible = max(total - known_off, 0)     # people who have not turned the meal OFF
    expected = min(total * fraction, max_possible)
    return min(math.ceil(expected * 1.05), max_possible)   # 5% buffer