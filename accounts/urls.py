from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.RoleLoginView.as_view(), name="login"),
    path("logout/", views.RoleLogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
]