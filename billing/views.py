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
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from .forms import DepositForm, RefundForm
from django.urls import reverse_lazy
from .models import RentInvoice, Payment, SecurityDeposit
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from accounts.mixins import RoleRequiredMixin
from .models import RentInvoice, Payment, SecurityDeposit
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
        messages.success(request, f"{n} new invoice(s) created.")
        return redirect("invoice_list")


class MarkPaidView(StaffMixin, View):
    def post(self, request, pk):
        method = request.POST.get("method", "CASH")
        if method not in (Payment.Method.CASH, Payment.Method.UPI):
            method = Payment.Method.CASH

        with transaction.atomic():
            invoice = get_object_or_404(RentInvoice.objects.select_for_update(), pk=pk)
            if invoice.status == RentInvoice.Status.PAID:
                messages.warning(request, "This invoice is already paid.")
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
            f"Rs. {invoice.amount} payment received ({method}).\n"
            f"Month: {invoice.month:%B %Y}\n"
            f"You can download the receipt from the portal: My Rent.\n\nHostel Management",
        )

        messages.success(request, f"{invoice} marked as paid.")
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
        c.drawString(60, y, "This is a computer-generated receipt.")
        c.showPage()
        c.save()
        buf.seek(0)

        return FileResponse(buf, as_attachment=True, filename=f"receipt_{invoice.pk}.pdf")

# ---------- Security Deposit ----------
class DepositListView(StaffMixin, ListView):
    template_name = "billing/deposit_list.html"
    context_object_name = "deposits"

    def get_queryset(self):
        return SecurityDeposit.objects.select_related("tenant__user", "handled_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        held = SecurityDeposit.objects.filter(status=SecurityDeposit.Status.HELD)
        ctx["total_held"] = held.aggregate(s=Sum("amount"))["s"] or 0
        return ctx


class DepositCreateView(StaffMixin, CreateView):
    form_class = DepositForm
    template_name = "billing/deposit_form.html"
    success_url = reverse_lazy("deposit_list")

    def form_valid(self, form):
        form.instance.handled_by = self.request.user
        messages.success(self.request, "Deposit recorded.")
        return super().form_valid(form)


class RefundView(StaffMixin, UpdateView):
    form_class = RefundForm
    template_name = "billing/refund_form.html"
    success_url = reverse_lazy("deposit_list")

    def get_queryset(self):
        # sirf HELD deposit, aur sirf checkout ho chuke tenant ka
        return SecurityDeposit.objects.filter(
            status=SecurityDeposit.Status.HELD
        ).exclude(tenant__allotments__is_active=True).select_related("tenant__user")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dues = RentInvoice.objects.filter(tenant=self.object.tenant).exclude(
            status=RentInvoice.Status.PAID
        ).aggregate(s=Sum("amount"))["s"] or 0
        ctx["dues"] = dues
        return ctx

    def form_valid(self, form):
        with transaction.atomic():
            dep = SecurityDeposit.objects.select_for_update().get(pk=self.object.pk)
            if dep.status != SecurityDeposit.Status.HELD:
                messages.warning(self.request, "This deposit has already been refunded.")
                return redirect("deposit_list")

            dep.deduction = form.cleaned_data["deduction"]
            dep.deduction_reason = form.cleaned_data["deduction_reason"]
            dep.refunded_amount = dep.amount - dep.deduction
            dep.refunded_on = timezone.localdate()
            dep.status = SecurityDeposit.Status.REFUNDED
            dep.handled_by = self.request.user
            dep.save()

        notify_user(
            dep.tenant.user,
            "Security deposit refund",
            f"Your security deposit refund has been processed.\n"
            f"Deposit: Rs. {dep.amount}\n"
            f"Deduction: Rs. {dep.deduction} ({dep.deduction_reason or '-'})\n"
            f"Refund: Rs. {dep.refunded_amount}\n\nHostel Management",
        )
        messages.success(self.request, f"Rs. {dep.refunded_amount} marked as refunded.")
        return redirect("deposit_list")


class MyDepositView(RoleRequiredMixin, TemplateView):
    allowed_roles = ["TENANT"]
    template_name = "billing/my_deposit.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["deposit"] = SecurityDeposit.objects.filter(tenant__user=self.request.user).first()
        return ctx