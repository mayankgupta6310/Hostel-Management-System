from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from billing.models import RentInvoice
from complaints.models import Complaint
from rooms.models import Bed
from tenants.models import Tenant

from datetime import timedelta

from django.utils import timezone
from django.views import View

from mess.models import MealOptOut, MealType
from .excel import make_xlsx_response


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

def _safe(text):
    """Excel formula injection se bachav: = + - @ se shuru hone wala text."""
    text = "" if text is None else str(text)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


class DuesExportView(RoleRequiredMixin, View):
    allowed_roles = ["ADMIN", "WARDEN"]

    def get(self, request):
        invoices = (
            RentInvoice.objects.exclude(status="PAID")
            .select_related("tenant__user").order_by("due_date")
        )
        rows = [
            [
                _safe(i.tenant.user.get_full_name() or i.tenant.user.username),
                i.month.strftime("%b %Y"),
                _safe(i.description),
                float(i.amount),
                i.due_date.strftime("%d %b %Y"),
                i.get_status_display(),
            ]
            for i in invoices
        ]
        return make_xlsx_response(
            "dues_report.xlsx", "Dues",
            ["Tenant", "Month", "Room / Bed", "Amount (Rs)", "Due Date", "Status"], rows,
        )


class TenantsExportView(RoleRequiredMixin, View):
    allowed_roles = ["ADMIN", "WARDEN"]

    def get(self, request):
        tenants = Tenant.objects.select_related("user").prefetch_related(
            "allotments__bed__room__hostel"
        )
        rows = []
        for t in tenants:
            a = t.current_allotment
            bed = f"{a.bed.room.hostel.name} / Room {a.bed.room.room_no} / {a.bed.bed_no}" if a else "Not allotted"
            rows.append([
                _safe(t.user.get_full_name() or t.user.username),
                _safe(t.user.username),
                _safe(t.user.phone),
                _safe(t.guardian_name),
                _safe(t.guardian_phone),
                bed,
                t.joined_on.strftime("%d %b %Y"),
            ])
        return make_xlsx_response(
            "tenants.xlsx", "Tenants",
            ["Name", "Username", "Phone", "Guardian", "Guardian Phone", "Current Bed", "Joined"], rows,
        )


class MealCountExportView(RoleRequiredMixin, View):
    allowed_roles = ["ADMIN", "WARDEN", "MESS"]

    def get(self, request):
        today = timezone.localdate()
        total = Tenant.objects.filter(allotments__is_active=True).distinct().count()
        rows = []
        for offset in range(3):
            d = today + timedelta(days=offset)
            for code, label in MealType.choices:
                off = (
                    MealOptOut.objects.filter(
                        date=d, meal_type=code, tenant__allotments__is_active=True
                    ).values("tenant").distinct().count()
                )
                rows.append([d.strftime("%d %b %Y"), label, total, off, total - off])
        return make_xlsx_response(
            "meal_count.xlsx", "Meal Count",
            ["Date", "Meal", "Total Tenants", "OFF", "Count"], rows,
        )