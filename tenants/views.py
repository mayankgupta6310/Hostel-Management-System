from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, FormView

from accounts.mixins import RoleRequiredMixin
from rooms.models import Bed
from .forms import TenantRegisterForm, AllotmentForm
from .models import Tenant, Allotment


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
        messages.success(self.request, f"Tenant {tenant} register ho gaya.")
        return super().form_valid(form)


class AllotBedView(StaffMixin, FormView):
    form_class = AllotmentForm
    template_name = "tenants/form.html"
    success_url = reverse_lazy("tenant_list")
    extra_context = {"title": "Bed Allot Karo"}

    def form_valid(self, form):
        tenant = form.cleaned_data["tenant"]
        bed_id = form.cleaned_data["bed"].pk
        start = form.cleaned_data["start_date"]

        with transaction.atomic():
            # row lock: dusra request isi bed ko ek saath nahi le payega
            bed = Bed.objects.select_for_update().get(pk=bed_id)

            if bed.is_occupied:
                form.add_error("bed", "Yeh bed abhi kisi aur ko mil chuka hai.")
                return self.form_invalid(form)

            if Allotment.objects.filter(tenant=tenant, is_active=True).exists():
                form.add_error("tenant", "Is tenant ko pehle se bed allotted hai.")
                return self.form_invalid(form)

            Allotment.objects.create(tenant=tenant, bed=bed, start_date=start)
            bed.is_occupied = True
            bed.save(update_fields=["is_occupied"])

        messages.success(self.request, f"{tenant} ko {bed} allot ho gaya.")
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

        messages.success(request, f"{allotment.tenant} ka checkout ho gaya, bed free hai.")
        return redirect("tenant_list")