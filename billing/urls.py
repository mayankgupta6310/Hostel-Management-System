from django.urls import path
from . import views

urlpatterns = [
    path("my/", views.MyInvoicesView.as_view(), name="my_invoices"),
    path("", views.InvoiceListView.as_view(), name="invoice_list"),
    path("generate/", views.GenerateInvoicesView.as_view(), name="generate_invoices"),
    path("<int:pk>/paid/", views.MarkPaidView.as_view(), name="mark_paid"),
    path("<int:pk>/receipt/", views.ReceiptView.as_view(), name="receipt"),
    path("deposits/", views.DepositListView.as_view(), name="deposit_list"),
    path("deposits/new/", views.DepositCreateView.as_view(), name="deposit_add"),
    path("deposits/<int:pk>/refund/", views.RefundView.as_view(), name="deposit_refund"),
    path("deposit/my/", views.MyDepositView.as_view(), name="my_deposit"),
]