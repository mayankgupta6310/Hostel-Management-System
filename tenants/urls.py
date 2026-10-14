from django.urls import path
from . import views

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant_list"),
    path("add/", views.TenantCreateView.as_view(), name="tenant_add"),
    path("allot/", views.AllotBedView.as_view(), name="allot_bed"),
    path("allotments/<int:pk>/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("changes/my/", views.MyChangeRequestsView.as_view(), name="my_changes"),
    path("changes/new/", views.ChangeRequestCreateView.as_view(), name="change_add"),
    path("changes/", views.ChangeRequestListView.as_view(), name="change_list"),
    path("changes/<int:pk>/decide/", views.ChangeDecisionView.as_view(), name="change_decide"),
]