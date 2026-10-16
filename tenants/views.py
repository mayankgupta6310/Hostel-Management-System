from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, FormView

from accounts.mixins import RoleRequiredMixin
from rooms.models import Bed
from accounts.emails import notify_user
from .forms import TenantRegisterForm, AllotmentForm, RoomChangeForm
from .models import Tenant, Allotment, RoomChangeRequest

from django.views.generic import ListView, FormView, CreateView




class StaffMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "WARDEN"]


class TenantListView(StaffMixin, ListView):
    model = Tenant
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"

    def get_queryset(self):
        return Tenant.objects.select_related("user").prefetch_related(
            "allotments__bed__room__hostel"
        )


class TenantCreateView(StaffMixin, FormView):
    form_class = TenantRegisterForm
    template_name = "tenants/form.html"
    success_url = reverse_lazy("tenant_list")
    extra_context = {"title": "Register Tenant"}

    def form_valid(self, form):
        tenant = form.save()
        messages.success(self.request, f"Tenant {tenant} registered successfully.")
        return super().form_valid(form)


class AllotBedView(StaffMixin, FormView):
    form_class = AllotmentForm
    template_name = "tenants/form.html"
    success_url = reverse_lazy("tenant_list")
    extra_context = {"title": "Allot Bed"}

    def form_valid(self, form):
        tenant = form.cleaned_data["tenant"]
        bed_id = form.cleaned_data["bed"].pk
        start = form.cleaned_data["start_date"]

        with transaction.atomic():
            # row lock: dusra request isi bed ko ek saath nahi le payega
            bed = Bed.objects.select_for_update().get(pk=bed_id)

            if bed.is_occupied:
                form.add_error("bed", "This bed has just been allotted to someone else.")
                return self.form_invalid(form)

            if Allotment.objects.filter(tenant=tenant, is_active=True).exists():
                form.add_error("tenant", "This tenant already has a bed.")
                return self.form_invalid(form)

            Allotment.objects.create(tenant=tenant, bed=bed, start_date=start)
            bed.is_occupied = True
            bed.save(update_fields=["is_occupied"])

        messages.success(self.request, f"{tenant} has been allotted {bed}.")
        return super().form_valid(form)


class CheckoutView(StaffMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            allotment = get_object_or_404(
                Allotment.objects.select_for_update(), pk=pk, is_active=True
            )
            allotment.is_active = False
            allotment.end_date = timezone.localdate()
            allotment.save()

            bed = allotment.bed
            bed.is_occupied = False
            bed.save(update_fields=["is_occupied"])

        messages.success(request, f"{allotment.tenant} has been checked out. The bed is now free.")
        return redirect("tenant_list")

# ---------- Tenant ----------
class MyChangeRequestsView(RoleRequiredMixin, ListView):
    allowed_roles = ["TENANT"]
    template_name = "tenants/my_changes.html"
    context_object_name = "requests"

    def get_queryset(self):
        return RoomChangeRequest.objects.filter(
            tenant__user=self.request.user
        ).select_related("current_bed__room", "requested_bed__room")


class ChangeRequestCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["TENANT"]
    form_class = RoomChangeForm
    template_name = "tenants/change_form.html"
    success_url = reverse_lazy("my_changes")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request.user, "tenant_profile", None)
        return kwargs

    def form_valid(self, form):
        tenant = getattr(self.request.user, "tenant_profile", None)
        allotment = tenant.current_allotment if tenant else None
        if allotment is None:
            messages.error(self.request, "You have not been allotted a bed yet.")
            return redirect("dashboard")
        if form.cleaned_data["requested_bed"].pk == allotment.bed_id:
            form.add_error("requested_bed", "This is your current bed.")
            return self.form_invalid(form)

        form.instance.tenant = tenant
        form.instance.current_bed = allotment.bed
        messages.success(self.request, "Room change request submitted.")
        return super().form_valid(form)


# ---------- Admin / Warden ----------
class ChangeRequestListView(StaffMixin, ListView):
    template_name = "tenants/change_list.html"
    context_object_name = "requests"

    def get_queryset(self):
        return RoomChangeRequest.objects.select_related(
            "tenant__user", "current_bed__room__hostel",
            "requested_bed__room__hostel", "decided_by",
        )


class ChangeDecisionView(StaffMixin, View):
    def post(self, request, pk):
        action = request.POST.get("action")
        remark = request.POST.get("remark", "")[:250]
        if action not in ("approve", "reject"):
            messages.error(request, "Invalid action.")
            return redirect("change_list")

        with transaction.atomic():
            req = get_object_or_404(RoomChangeRequest.objects.select_for_update(), pk=pk)
            if req.status != RoomChangeRequest.Status.PENDING:
                messages.warning(request, "A decision has already been made on this request.")
                return redirect("change_list")

            if action == "reject":
                req.status = RoomChangeRequest.Status.REJECTED
                req.remark = remark
            else:
                new_bed = Bed.objects.select_for_update().get(pk=req.requested_bed_id)
                allot = Allotment.objects.select_for_update().filter(
                    tenant=req.tenant, is_active=True
                ).first()

                if allot is None:
                    req.status = RoomChangeRequest.Status.REJECTED
                    req.remark = "Tenant has no active allotment."
                elif new_bed.is_occupied:
                    req.status = RoomChangeRequest.Status.REJECTED
                    req.remark = "This bed is no longer vacant."
                else:
                    old_bed = Bed.objects.select_for_update().get(pk=allot.bed_id)
                    today = timezone.localdate()

                    allot.is_active = False
                    allot.end_date = today
                    allot.save()
                    old_bed.is_occupied = False
                    old_bed.save(update_fields=["is_occupied"])

                    Allotment.objects.create(tenant=req.tenant, bed=new_bed, start_date=today)
                    new_bed.is_occupied = True
                    new_bed.save(update_fields=["is_occupied"])

                    req.status = RoomChangeRequest.Status.APPROVED
                    req.remark = remark

            req.decided_by = request.user
            req.decided_at = timezone.now()
            req.save()

        notify_user(
            req.tenant.user,
            f"Room change request {req.get_status_display()}",
            f"Your room change request was {req.get_status_display()}.\n"
            f"New bed: {req.requested_bed}\n"
            f"Remark: {req.remark or '-'}\n\nHostel Management",
        )
        if req.status == RoomChangeRequest.Status.APPROVED:
            messages.success(request, f"{req.tenant} has been moved to {req.requested_bed}.")
        else:
            messages.warning(request, f"Request Rejected. {req.remark}")
        return redirect("change_list")