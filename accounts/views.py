from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

ROLE_DASHBOARDS = {
    "ADMIN": "dashboards/admin.html",
    "WARDEN": "dashboards/warden.html",
    "TENANT": "dashboards/tenant.html",
    "MESS": "dashboards/mess.html",
    "GUARD": "dashboards/guard.html",
    "STAFF": "dashboards/staff.html",
}


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard")


class RoleLogoutView(LogoutView):
    next_page = "login"


@login_required
def dashboard(request):
    template = ROLE_DASHBOARDS.get(request.user.role, "dashboards/tenant.html")
    return render(request, template)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")