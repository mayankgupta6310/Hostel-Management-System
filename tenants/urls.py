from django.urls import path
from . import views

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant_list"),
    path("add/", views.TenantCreateView.as_view(), name="tenant_add"),
    path("allot/", views.AllotBedView.as_view(), name="allot_bed"),
    path("allotments/<int:pk>/checkout/", views.CheckoutView.as_view(), name="checkout"),
]