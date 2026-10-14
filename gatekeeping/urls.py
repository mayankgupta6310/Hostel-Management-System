from django.urls import path
from . import views

urlpatterns = [
    path("my/", views.MyPassesView.as_view(), name="my_passes"),
    path("new/", views.PassCreateView.as_view(), name="pass_add"),
    path("", views.PassListView.as_view(), name="pass_list"),
    path("<int:pk>/decide/", views.PassDecisionView.as_view(), name="pass_decide"),
    path("guard/", views.GuardPanelView.as_view(), name="guard_panel"),
    path("<int:pk>/out/", views.MarkOutView.as_view(), name="pass_out"),
    path("<int:pk>/return/", views.MarkReturnView.as_view(), name="pass_return"),
    path("visitors/", views.VisitorListView.as_view(), name="visitor_list"),
    path("visitors/new/", views.VisitorCreateView.as_view(), name="visitor_add"),
    path("visitors/<int:pk>/out/", views.VisitorOutView.as_view(), name="visitor_out"),
    path("<int:pk>/qr/", views.PassQRView.as_view(), name="pass_qr"),
    path("scan/", views.ScanView.as_view(), name="scan"),
]