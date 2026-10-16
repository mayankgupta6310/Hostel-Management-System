import uuid
from io import BytesIO

import qrcode
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView

from accounts.mixins import RoleRequiredMixin
from .forms import GatePassForm, VisitorForm
from .models import GatePass, Visitor


class StaffMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "WARDEN"]


class GuardMixin(RoleRequiredMixin):
    allowed_roles = ["GUARD"]


# ---------- Tenant ----------
class MyPassesView(RoleRequiredMixin, ListView):
    allowed_roles = ["TENANT"]
    template_name = "gatekeeping/my_passes.html"
    context_object_name = "passes"

    def get_queryset(self):
        return GatePass.objects.filter(tenant__user=self.request.user)


class PassCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["TENANT"]
    form_class = GatePassForm
    template_name = "gatekeeping/form.html"
    success_url = reverse_lazy("my_passes")
    extra_context = {"title": "Gate Pass Request", "back_url": reverse_lazy("my_passes")}

    def form_valid(self, form):
        tenant = getattr(self.request.user, "tenant_profile", None)
        if tenant is None or tenant.current_allotment is None:
            messages.error(self.request, "You have not been allotted a bed yet.")
            return redirect("dashboard")
        form.instance.tenant = tenant
        messages.success(self.request, "Gate pass request submitted.")
        return super().form_valid(form)


# ---------- Admin / Warden ----------
class PassListView(StaffMixin, ListView):
    template_name = "gatekeeping/pass_list.html"
    context_object_name = "passes"

    def get_queryset(self):
        qs = GatePass.objects.select_related("tenant__user", "approved_by")
        status = self.request.GET.get("status")
        if status in GatePass.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = GatePass.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class PassDecisionView(StaffMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            gp = get_object_or_404(GatePass.objects.select_for_update(), pk=pk)
            if gp.status != GatePass.Status.PENDING:
                messages.warning(request, "A decision has already been made on this request.")
                return redirect("pass_list")

            action = request.POST.get("action")
            if action == "approve":
                gp.status = GatePass.Status.APPROVED
            elif action == "reject":
                gp.status = GatePass.Status.REJECTED
            else:
                messages.error(request, "Invalid action.")
                return redirect("pass_list")

            gp.approved_by = request.user
            gp.save()
        messages.success(request, f"{gp} is now {gp.get_status_display()}.")
        return redirect("pass_list")


class VisitorListView(RoleRequiredMixin, ListView):
    allowed_roles = ["ADMIN", "WARDEN", "GUARD"]
    template_name = "gatekeeping/visitor_list.html"
    context_object_name = "visitors"
    paginate_by = 50

    def get_queryset(self):
        return Visitor.objects.select_related("tenant__user", "logged_by")


# ---------- Security Guard ----------
class GuardPanelView(GuardMixin, ListView):
    template_name = "gatekeeping/guard_panel.html"
    context_object_name = "approved_passes"

    def get_queryset(self):
        return GatePass.objects.filter(status=GatePass.Status.APPROVED).select_related("tenant__user")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["out_passes"] = GatePass.objects.filter(
            status=GatePass.Status.OUT
        ).select_related("tenant__user")
        ctx["inside_visitors"] = Visitor.objects.filter(
            out_time__isnull=True
        ).select_related("tenant__user")
        return ctx


class MarkOutView(GuardMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            gp = get_object_or_404(
                GatePass.objects.select_for_update(), pk=pk, status=GatePass.Status.APPROVED
            )
            gp.status = GatePass.Status.OUT
            gp.actual_out = timezone.now()
            gp.save()
        messages.success(request, f"{gp.tenant} has gone out.")
        return redirect("guard_panel")


class MarkReturnView(GuardMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            gp = get_object_or_404(
                GatePass.objects.select_for_update(), pk=pk, status=GatePass.Status.OUT
            )
            gp.status = GatePass.Status.RETURNED
            gp.actual_return = timezone.now()
            gp.save()
        if gp.is_late:
            messages.warning(request, f"{gp.tenant} returned LATE.")
        else:
            messages.success(request, f"{gp.tenant} returned on time.")
        return redirect("guard_panel")


class VisitorCreateView(GuardMixin, CreateView):
    form_class = VisitorForm
    template_name = "gatekeeping/form.html"
    success_url = reverse_lazy("guard_panel")
    extra_context = {"title": "Visitor Entry", "back_url": reverse_lazy("guard_panel")}

    def form_valid(self, form):
        form.instance.logged_by = self.request.user
        messages.success(self.request, "Visitor entry recorded.")
        return super().form_valid(form)


class VisitorOutView(GuardMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            v = get_object_or_404(
                Visitor.objects.select_for_update(), pk=pk, out_time__isnull=True
            )
            v.out_time = timezone.now()
            v.save()
        messages.success(request, f"{v.visitor_name} has exited.")
        return redirect("guard_panel")

    
class PassQRView(RoleRequiredMixin, View):
    """Approved pass ka QR image. Sirf pass ka malik tenant ya staff dekh sakta hai."""
    allowed_roles = ["TENANT", "ADMIN", "WARDEN"]

    def get(self, request, pk):
        gp = get_object_or_404(GatePass, pk=pk)
        if request.user.role == "TENANT" and gp.tenant.user_id != request.user.id:
            raise PermissionDenied
        if gp.status in (GatePass.Status.PENDING, GatePass.Status.REJECTED):
            raise PermissionDenied

        img = qrcode.make(str(gp.token))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return HttpResponse(buf.getvalue(), content_type="image/png")


class ScanView(GuardMixin, View):
    """Token se pass dhundho: APPROVED -> OUT, OUT -> RETURNED."""

    def get(self, request):
        return render(request, "gatekeeping/scan.html")

    def post(self, request):
        raw = (request.POST.get("token") or "").strip()
        try:
            token = uuid.UUID(raw)
        except ValueError:
            messages.error(request, "Invalid QR / token.")
            return redirect("scan")

        with transaction.atomic():
            gp = (
                GatePass.objects.select_for_update()
                .select_related("tenant__user")
                .filter(token=token)
                .first()
            )
            if gp is None:
                messages.error(request, "Pass not found.")
                return redirect("scan")

            name = gp.tenant.user.get_full_name() or gp.tenant.user.username

            if gp.status == GatePass.Status.APPROVED:
                gp.status = GatePass.Status.OUT
                gp.actual_out = timezone.now()
                gp.save()
                messages.success(request, f"{name} has gone OUT.")
            elif gp.status == GatePass.Status.OUT:
                gp.status = GatePass.Status.RETURNED
                gp.actual_return = timezone.now()
                gp.save()
                if gp.is_late:
                    messages.warning(request, f"{name} returned LATE.")
                else:
                    messages.success(request, f"{name} has RETURNED on time.")
            elif gp.status == GatePass.Status.RETURNED:
                messages.warning(request, "This pass has already been used.")
            else:
                messages.error(request, f"Pass is {gp.get_status_display()} and cannot be scanned.")
        return redirect("scan")