from datetime import timedelta

from django.contrib import messages
from django.db.models import Avg, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from accounts.mixins import RoleRequiredMixin
from tenants.models import Tenant
from .forms import FeedbackForm, MenuItemForm
from .models import MealOptOut, MealType, MenuItem, MessFeedback
from .forecast import forecast_count

class MessManagerMixin(RoleRequiredMixin):
    allowed_roles = ["MESS", "ADMIN"]


# ---------- Menu (sab dekh sakte hain) ----------
class MenuView(RoleRequiredMixin, TemplateView):
    allowed_roles = ["MESS", "ADMIN", "WARDEN", "TENANT"]
    template_name = "mess/menu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = {(m.day, m.meal_type): m.items for m in MenuItem.objects.all()}
        rows = []
        for day_no, day_name in MenuItem.DAYS:
            rows.append({
                "day": day_name,
                "is_today": day_no == timezone.localdate().weekday(),
                "breakfast": items.get((day_no, "BREAKFAST"), "-"),
                "lunch": items.get((day_no, "LUNCH"), "-"),
                "dinner": items.get((day_no, "DINNER"), "-"),
            })
        ctx["rows"] = rows
        return ctx


class MenuEditView(MessManagerMixin, CreateView):
    form_class = MenuItemForm
    template_name = "mess/form.html"
    success_url = reverse_lazy("mess_menu")
    extra_context = {"title": "Set Menu", "back_url": reverse_lazy("mess_menu")}

    def form_valid(self, form):
        d = form.cleaned_data
        MenuItem.objects.update_or_create(
            day=d["day"], meal_type=d["meal_type"], defaults={"items": d["items"]}
        )
        messages.success(self.request, "Menu saved.")
        return redirect(self.success_url)


# ---------- Tenant: meal on/off ----------
class MyMealsView(RoleRequiredMixin, TemplateView):
    allowed_roles = ["TENANT"]
    template_name = "mess/my_meals.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        tenant = getattr(self.request.user, "tenant_profile", None)

        days = []
        for offset in range(0, 4):   # aaj se agle 3 din
            d = today + timedelta(days=offset)
            off = set()
            if tenant:
                off = set(
                    MealOptOut.objects.filter(tenant=tenant, date=d).values_list("meal_type", flat=True)
                )
            days.append({
                "date": d,
                "editable": offset >= 1,   # aaj ka meal change nahi hoga, kal se allowed
                "meals": [
                    {"code": code, "label": label, "on": code not in off}
                    for code, label in MealType.choices
                ],
            })
        ctx["days"] = days
        ctx["has_profile"] = tenant is not None
        return ctx


class ToggleMealView(RoleRequiredMixin, View):
    allowed_roles = ["TENANT"]

    def post(self, request):
        tenant = getattr(request.user, "tenant_profile", None)
        if tenant is None:
            messages.error(request, "Your tenant profile has not been created.")
            return redirect("dashboard")

        try:
            date = timezone.datetime.strptime(request.POST.get("date", ""), "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date.")
            return redirect("my_meals")

        meal = request.POST.get("meal")
        if meal not in MealType.values:
            messages.error(request, "Invalid meal.")
            return redirect("my_meals")

        today = timezone.localdate()
        if date <= today or date > today + timedelta(days=3):
            messages.error(request, "You can only change meals from tomorrow for the next 3 days.")
            return redirect("my_meals")

        obj = MealOptOut.objects.filter(tenant=tenant, date=date, meal_type=meal)
        if obj.exists():
            obj.delete()                       # OFF tha, ab ON
            messages.success(request, f"{date:%d %b} {meal.title()} is now ON.")
        else:
            MealOptOut.objects.create(tenant=tenant, date=date, meal_type=meal)   # ab OFF
            messages.success(request, f"{date:%d %b} {meal.title()} is now OFF.")
        return redirect("my_meals")


# ---------- Mess Manager: meal count ----------
class MealCountView(MessManagerMixin, TemplateView):
    template_name = "mess/meal_count.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        total = Tenant.objects.filter(allotments__is_active=True).distinct().count()

        days = []
        for offset in range(0, 7):
            d = today + timedelta(days=offset)
            off = dict(
                MealOptOut.objects.filter(date=d, tenant__allotments__is_active=True)
                .values("meal_type").annotate(c=Count("tenant", distinct=True))
                .values_list("meal_type", "c")
            )
            days.append({
                "date": d,
                "meals": [
                    {
                        "label": label,
                        "off": off.get(code, 0),
                        "count": total - off.get(code, 0),
                        "forecast": forecast_count(d, code, total, off.get(code, 0)),
                    }
                    for code, label in MealType.choices
                ],
            })
        ctx["days"] = days
        ctx["total"] = total
        return ctx


# ---------- Feedback ----------
class FeedbackCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["TENANT"]
    form_class = FeedbackForm
    template_name = "mess/form.html"
    success_url = reverse_lazy("mess_menu")
    extra_context = {"title": "Mess Feedback", "back_url": reverse_lazy("mess_menu")}

    def form_valid(self, form):
        tenant = getattr(self.request.user, "tenant_profile", None)
        if tenant is None:
            messages.error(self.request, "Your tenant profile has not been created.")
            return redirect("dashboard")
        form.instance.tenant = tenant
        messages.success(self.request, "Thank you for your feedback.")
        return super().form_valid(form)


class FeedbackListView(MessManagerMixin, ListView):
    template_name = "mess/feedback_list.html"
    context_object_name = "feedbacks"
    paginate_by = 50

    def get_queryset(self):
        return MessFeedback.objects.select_related("tenant__user")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["averages"] = (
            MessFeedback.objects.values("meal_type").annotate(avg=Avg("rating"), n=Count("id"))
        )
        return ctx