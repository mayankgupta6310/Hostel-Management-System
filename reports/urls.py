from django.urls import path
from . import views

urlpatterns = [
    path("", views.DashboardReportView.as_view(), name="reports"),
    path("export/dues/", views.DuesExportView.as_view(), name="export_dues"),
    path("export/tenants/", views.TenantsExportView.as_view(), name="export_tenants"),
    path("export/meals/", views.MealCountExportView.as_view(), name="export_meals"),
]