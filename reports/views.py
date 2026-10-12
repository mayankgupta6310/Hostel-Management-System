from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from billing.models import RentInvoice
from complaints.models import Complaint
from rooms.models import Bed
from tenants.models import Tenant


class DashboardReportView(RoleRequiredMixin, TemplateView):
    allowed_roles = ["ADMIN", "WARDEN"]
    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Occupancy
        total_beds = Bed.objects.count()
        occupied = Bed.objects.filter(is_occupied=True).count()
        ctx["total_beds"] = total_beds
        ctx["occupied"] = occupied
        ctx["vacant"] = total_beds - occupied
        ctx["occupancy_pct"] = round(occupied * 100 / total_beds) if total_beds else 0
        ctx["total_tenants"] = Tenant.objects.filter(allotments__is_active=True).distinct().count()

        # Rent
        paid = RentInvoice.objects.filter(status="PAID").aggregate(s=Sum("amount"))["s"] or 0
        pending = RentInvoice.objects.filter(status="PENDING").aggregate(s=Sum("amount"))["s"] or 0
        overdue = RentInvoice.objects.filter(status="OVERDUE").aggregate(s=Sum("amount"))["s"] or 0
        ctx["rent_paid"] = paid
        ctx["rent_pending"] = pending
        ctx["rent_overdue"] = overdue

        # Monthly collection (sirf paid invoices)
        monthly = (
            RentInvoice.objects.filter(status="PAID")
            .annotate(m=TruncMonth("month"))
            .values("m").annotate(total=Sum("amount")).order_by("m")
        )
        ctx["month_labels"] = [row["m"].strftime("%b %Y") for row in monthly]
        ctx["month_values"] = [float(row["total"]) for row in monthly]

        # Complaints by status
        status_map = dict(Complaint.Status.choices)
        by_status = {row["status"]: row["c"] for row in
                     Complaint.objects.values("status").annotate(c=Count("id"))}
        ctx["complaint_labels"] = [label for code, label in Complaint.Status.choices]
        ctx["complaint_values"] = [by_status.get(code, 0) for code, _ in Complaint.Status.choices]
        ctx["open_complaints"] = by_status.get("OPEN", 0) + by_status.get("ASSIGNED", 0) + by_status.get("IN_PROGRESS", 0)

        # Defaulters (overdue wale tenants)
        ctx["defaulters"] = (
            RentInvoice.objects.filter(status="OVERDUE")
            .select_related("tenant__user").order_by("due_date")[:10]
        )
        return ctx