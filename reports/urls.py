from django.urls import path
from . import views

urlpatterns = [
    path("", views.DashboardReportView.as_view(), name="reports"),
]