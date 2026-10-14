from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from accounts.mixins import RoleRequiredMixin
from .models import RentInvoice, Payment
from .services import generate_monthly_invoices, mark_overdue

from accounts.emails import notify_user


class StaffMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "WARDEN"]


class MyInvoicesView(RoleRequiredMixin, ListView):
    allowed_roles = ["TENANT"]
    template_name = "billing/my_invoices.html"
    context_object_name = "invoices"

    def get_queryset(self):
        mark_overdue()
        return RentInvoice.objects.filter(tenant__user=self.request.user)


class InvoiceListView(StaffMixin, ListView):
    template_name = "billing/invoice_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        mark_overdue()
        qs = RentInvoice.objects.select_related("tenant__user")
        status = self.request.GET.get("status")
        if status in RentInvoice.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        unpaid = RentInvoice.objects.exclude(status=RentInvoice.Status.PAID)
        ctx["total_due"] = unpaid.aggregate(s=Sum("amount"))["s"] or 0
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["statuses"] = RentInvoice.Status.choices
        ctx["methods"] = Payment.Method.choices
        return ctx


class GenerateInvoicesView(StaffMixin, View):
    def post(self, request):
        n = generate_monthly_invoices()
        messages.success(request, f"{n} naye invoice bane.")
        return redirect("invoice_list")


class MarkPaidView(StaffMixin, View):
    def post(self, request, pk):
        method = request.POST.get("method", "CASH")
        if method not in (Payment.Method.CASH, Payment.Method.UPI):
            method = Payment.Method.CASH

        with transaction.atomic():
            invoice = get_object_or_404(RentInvoice.objects.select_for_update(), pk=pk)
            if invoice.status == RentInvoice.Status.PAID:
                messages.warning(request, "Yeh invoice pehle se paid hai.")
                return redirect("invoice_list")

            Payment.objects.create(
                invoice=invoice,
                amount=invoice.amount,
                method=method,
                received_by=request.user,
            )
            invoice.status = RentInvoice.Status.PAID
            invoice.save(update_fields=["status"])

        notify_user(
            invoice.tenant.user,
            f"Payment received - {invoice.month:%B %Y}",
            f"Rs. {invoice.amount} ka payment mil gaya ({method}).\n"
            f"Month: {invoice.month:%B %Y}\n"
            f"Receipt portal se download karo: My Rent.\n\nHostel Management",
        )

        messages.success(request, f"{invoice} paid mark ho gaya.")
        return redirect("invoice_list")


class ReceiptView(LoginRequiredMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(
            RentInvoice.objects.select_related("tenant__user"),
            pk=pk, status=RentInvoice.Status.PAID,
        )
        user = request.user
        is_staff = user.role in ("ADMIN", "WARDEN")
        if not is_staff and invoice.tenant.user_id != user.id:
            raise PermissionDenied

        payment = invoice.payments.order_by("-paid_at").first()
        tenant = invoice.tenant

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        y = h - 70

        c.setFont("Helvetica-Bold", 20)
        c.drawString(60, y, "Rent Receipt")
        y -= 12
        c.line(60, y, w - 60, y)
        y -= 35

        c.setFont("Helvetica", 12)
        rows = [
            ("Receipt No", f"RCP-{invoice.pk:05d}"),
            ("Tenant", tenant.user.get_full_name() or tenant.user.username),
            ("Room / Bed", invoice.description),
            ("Month", invoice.month.strftime("%B %Y")),
            ("Amount Paid", f"Rs. {invoice.amount}"),
            ("Method", payment.get_method_display() if payment else "-"),
            ("Paid On", timezone.localtime(payment.paid_at).strftime("%d %b %Y, %I:%M %p") if payment else "-"),
        ]
        for label, value in rows:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(60, y, f"{label}:")
            c.setFont("Helvetica", 12)
            c.drawString(190, y, str(value))
            y -= 26

        y -= 20
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(60, y, "Yeh computer-generated receipt hai.")
        c.showPage()
        c.save()
        buf.seek(0)

        return FileResponse(buf, as_attachment=True, filename=f"receipt_{invoice.pk}.pdf")