from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView

from accounts.mixins import RoleRequiredMixin
from .forms import ComplaintForm
from .models import Complaint

from accounts.emails import notify_user



from django.db.models import Case, IntegerField, Value, When

from .ml import predict_category, predict_priority
User = get_user_model()


class StaffMixin(RoleRequiredMixin):
    allowed_roles = ["ADMIN", "WARDEN"]


# ---------- Tenant ----------
class MyComplaintsView(RoleRequiredMixin, ListView):
    allowed_roles = ["TENANT"]
    template_name = "complaints/my_complaints.html"
    context_object_name = "complaints"

    def get_queryset(self):
        return Complaint.objects.filter(tenant__user=self.request.user).select_related("assigned_to")


class ComplaintCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["TENANT"]
    form_class = ComplaintForm
    template_name = "complaints/complaint_form.html"
    success_url = reverse_lazy("my_complaints")

    def form_valid(self, form):
        tenant = getattr(self.request.user, "tenant_profile", None)
        if tenant is None:
            messages.error(self.request, "Your tenant profile is not created. Please contact the warden.")
            return redirect("dashboard")

        # AI: if the tenant left the category as "Other", try to detect it
        text = f"{form.cleaned_data['title']} {form.cleaned_data['description']}"
        category, confidence = predict_category(text)
        if category and confidence >= 0.5 and form.cleaned_data["category"] == Complaint.Category.OTHER:
            form.instance.category = category
            label = dict(Complaint.Category.choices).get(category, category)
            messages.info(self.request, f"AI detected category: {label} ({confidence:.0%} confident)")

        form.instance.tenant = tenant
        messages.success(self.request, "Complaint submitted successfully.")
        return super().form_valid(form)


# ---------- Admin / Warden ----------
class ComplaintListView(StaffMixin, ListView):
    template_name = "complaints/complaint_list.html"
    context_object_name = "complaints"

    def get_queryset(self):
        qs = Complaint.objects.select_related("tenant__user", "assigned_to")
        status = self.request.GET.get("status")
        if status in Complaint.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["staff_users"] = User.objects.filter(role="STAFF", is_active=True)
        ctx["statuses"] = Complaint.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class AssignComplaintView(StaffMixin, View):
    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        staff = User.objects.filter(
            pk=request.POST.get("staff_id"), role="STAFF", is_active=True
        ).first()

        if complaint.status == Complaint.Status.RESOLVED:
            messages.warning(request, "A resolved complaint cannot be assigned.")
        elif staff is None:
            messages.error(request, "Please select a staff member.")
        else:
            complaint.assigned_to = staff
            if complaint.status == Complaint.Status.OPEN:
                complaint.status = Complaint.Status.ASSIGNED
            complaint.save()
            messages.success(request, f"{complaint} assigned to {staff.username}.")
        return redirect("complaint_list")


# ---------- Maintenance Staff ----------
class StaffTasksView(RoleRequiredMixin, ListView):
    allowed_roles = ["STAFF"]
    template_name = "complaints/staff_tasks.html"
    context_object_name = "complaints"

    def get_queryset(self):
        return Complaint.objects.filter(
            assigned_to=self.request.user
        ).select_related("tenant__user").order_by("status", "-created_at")


class UpdateStatusView(RoleRequiredMixin, View):
    allowed_roles = ["STAFF"]

    def post(self, request, pk):
        # staff sirf apni assigned complaint hi update kar sakta hai
        complaint = get_object_or_404(Complaint, pk=pk, assigned_to=request.user)
        new_status = request.POST.get("status")

        if new_status not in (Complaint.Status.IN_PROGRESS, Complaint.Status.RESOLVED):
            messages.error(request, "Invalid status.")
            return redirect("staff_tasks")

        complaint.status = new_status
        complaint.staff_remark = request.POST.get("remark", "")[:255]
        complaint.resolved_at = timezone.now() if new_status == Complaint.Status.RESOLVED else None
        complaint.save()
        if new_status == Complaint.Status.RESOLVED:
            notify_user(
                complaint.tenant.user,
                f"Complaint #{complaint.pk} has been resolved",
                f"Your complaint \"{complaint.title}\" has been resolved.\n"
                f"Staff remark: {complaint.staff_remark or '-'}\n\nHostel Management",
            )
        messages.success(request, f"{complaint} updated.")
        return redirect("staff_tasks")