import joblib
from django.conf import settings
from django.utils import timezone

from tenants.models import Tenant

FEATURES = ["invoices_total", "late_ratio", "unpaid_count", "max_days_overdue"]
MIN_INVOICES = 2          # below this there is not enough history
_model = None


def _load():
    global _model
    if _model is None:
        _model = joblib.load(settings.BASE_DIR / "ml" / "risk_model.joblib")
    return _model


def _features(tenant, today):
    total = late = unpaid = max_days = 0
    for inv in tenant.invoices.all():
        if inv.status == "PAID":
            total += 1
            pay = max(inv.payments.all(), key=lambda p: p.paid_at, default=None)
            if pay and timezone.localtime(pay.paid_at).date() > inv.due_date:
                late += 1
        elif inv.due_date < today:               # unpaid and past its due date
            total += 1
            late += 1
            unpaid += 1
            max_days = max(max_days, (today - inv.due_date).days)
        # pending and not yet due: not counted
    ratio = late / total if total else 0
    return total, [total, ratio, unpaid, max_days]


def level_for(prob):
    if prob >= 0.60:
        return "HIGH"
    if prob >= 0.35:
        return "MEDIUM"
    return "LOW"


def risk_for_tenants():
    """Returns (rows, available). Rows are sorted from highest risk to lowest."""
    try:
        model = _load()
    except Exception:
        return [], False

    today = timezone.localdate()
    tenants = (
        Tenant.objects.filter(allotments__is_active=True).distinct()
        .select_related("user").prefetch_related("invoices__payments")
    )
    rows = []
    for t in tenants:
        total, feats = _features(t, today)
        if total < MIN_INVOICES:
            rows.append({"tenant": t, "prob": None, "level": None,
                         "late_ratio": feats[1], "unpaid": feats[2], "total": total})
            continue
        prob = float(model.predict_proba([feats])[0][1])
        rows.append({"tenant": t, "prob": prob, "level": level_for(prob),
                     "late_ratio": feats[1], "unpaid": feats[2], "total": total})

    rows.sort(key=lambda r: (r["prob"] is None, -(r["prob"] or 0)))
    return rows, True
    