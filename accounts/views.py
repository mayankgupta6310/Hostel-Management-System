from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

User = get_user_model()

ROLE_DASHBOARDS = {
    "ADMIN": "dashboards/admin.html",
    "WARDEN": "dashboards/warden.html",
    "TENANT": "dashboards/tenant.html",
    "MESS": "dashboards/mess.html",
    "GUARD": "dashboards/guard.html",
    "STAFF": "dashboards/staff.html",
}

# (code, title, description, bootstrap color)
ROLE_CARDS = [
    ("ADMIN", "Admin / Owner", "Hostel setup, rooms, billing, reports", "dark"),
    ("WARDEN", "Warden", "Allotment, complaints, gate pass approval", "primary"),
    ("TENANT", "Tenant / Student", "Rent, complaints, gate pass, mess", "success"),
    ("MESS", "Mess Manager", "Menu, meal count, feedback", "warning"),
    ("GUARD", "Security Guard", "Gate pass scan, visitor log", "secondary"),
    ("STAFF", "Maintenance Staff", "Assigned repair tasks", "danger"),
]


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_role(self):
        role = self.request.POST.get("role") or self.request.GET.get("role", "")
        return role if role in User.Role.values else ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        role = self.get_role()
        ctx["role"] = role
        ctx["role_label"] = dict(User.Role.choices).get(role, "")
        return ctx

    def form_valid(self, form):
        role = self.get_role()
        user = form.get_user()
        if role and user.role != role:
            label = dict(User.Role.choices)[role]
            form.add_error(None, f"Yeh account {label} ka nahi hai. Sahi role chuno.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard")


class RoleLogoutView(LogoutView):
    next_page = "home"


@login_required
def dashboard(request):
    template = ROLE_DASHBOARDS.get(request.user.role, "dashboards/tenant.html")
    return render(request, template)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html", {"roles": ROLE_CARDS})