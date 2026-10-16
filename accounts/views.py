from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

User = get_user_model()

# (code, title, description, bootstrap color)
ROLE_CARDS = [
    ("ADMIN", "Admin / Owner", "Hostel setup, rooms, billing, reports", "dark"),
    ("WARDEN", "Warden", "Allotment, complaints, gate pass approval", "primary"),
    ("TENANT", "Tenant / Student", "Rent, complaints, gate pass, mess", "success"),
    ("MESS", "Mess Manager", "Menu, meal count, feedback", "warning"),
    ("GUARD", "Security Guard", "Gate pass scan, visitor log", "secondary"),
    ("STAFF", "Maintenance Staff", "Assigned repair tasks", "danger"),
]

# (url_name, icon, title, description, color)
MENUS = {
    "ADMIN": [
        ("room_list", "🛏️", "Rooms & Beds", "Create rooms and view occupancy", "primary"),
        ("tenant_list", "🎓", "Tenants", "Register, allot beds, check out", "success"),
        ("invoice_list", "💰", "Rent / Invoices", "Generate invoices, mark payments", "warning"),
        ("deposit_list", "🏦", "Security Deposits", "Deposits and refunds", "warning"),
        ("complaint_list", "🛠️", "Complaints", "Assign to staff", "danger"),
        ("pass_list", "🚪", "Gate Passes", "Approve / reject", "secondary"),
        ("visitor_list", "👥", "Visitor Log", "Visitor entry and exit records", "dark"),
        ("change_list", "🔁", "Room Requests", "Approve room changes", "secondary"),
        ("mess_menu", "🍛", "Mess", "Menu and meal count", "warning"),
        ("reports", "📊", "Reports", "Charts and Excel export", "dark"),
        ("notice_list", "📢", "Notices", "Announcements", "primary"),
        ("/admin/", "⚙️", "Admin Panel", "Manage users and data", "dark"),
    ],
    "WARDEN": [
        ("room_list", "🛏️", "Rooms & Beds", "View occupancy", "primary"),
        ("tenant_list", "🎓", "Tenants", "Register, allot beds, check out", "success"),
        ("invoice_list", "💰", "Rent / Invoices", "Invoices and payments", "warning"),
        ("deposit_list", "🏦", "Security Deposits", "Deposits and refunds", "warning"),
        ("complaint_list", "🛠️", "Complaints", "Assign to staff", "danger"),
        ("pass_list", "🚪", "Gate Passes", "Approve / reject", "secondary"),
        ("visitor_list", "👥", "Visitor Log", "Visitor records", "dark"),
        ("change_list", "🔁", "Room Requests", "Approve room changes", "secondary"),
        ("mess_menu", "🍛", "Mess", "View menu", "warning"),
        ("reports", "📊", "Reports", "Charts and Excel export", "dark"),
        ("notice_list", "📢", "Notices", "Announcements", "primary"),
    ],
    "TENANT": [
        ("my_invoices", "💰", "My Rent", "Invoices and receipt PDF", "warning"),
        ("my_deposit", "🏦", "My Deposit", "Security deposit status", "warning"),
        ("my_complaints", "🛠️", "My Complaints", "Submit and track complaints", "danger"),
        ("my_passes", "🚪", "Gate Pass", "Request and QR code", "secondary"),
        ("my_changes", "🔁", "Room Change", "Request a different bed", "primary"),
        ("mess_menu", "🍛", "Mess", "Menu, meal ON/OFF, feedback", "success"),
        ("notice_list", "📢", "Notices", "Hostel announcements", "dark"),
    ],
    "STAFF": [
        ("staff_tasks", "🔧", "My Tasks", "Assigned work and status", "primary"),
        ("notice_list", "📢", "Notices", "Announcements", "dark"),
    ],
    "GUARD": [
        ("guard_panel", "💂", "Guard Panel", "Out / In and visitors", "primary"),
        ("scan", "📷", "QR Scan", "Scan gate passes", "success"),
        ("visitor_add", "➕", "Visitor Entry", "New visitor", "warning"),
        ("visitor_list", "👥", "Visitor Log", "Full record", "dark"),
        ("notice_list", "📢", "Notices", "Announcements", "secondary"),
    ],
    "MESS": [
        ("mess_menu", "🍛", "Menu", "View weekly menu", "primary"),
        ("menu_edit", "✏️", "Set Menu", "Menu by day and meal", "warning"),
        ("meal_count", "🔢", "Meal Count", "How many will eat tomorrow", "success"),
        ("feedback_list", "⭐", "Feedback", "Ratings and comments", "danger"),
        ("notice_list", "📢", "Notices", "Announcements", "dark"),
    ],
}


def build_stats(user):
    """Role ke hisaab se upar ke stat cards: (label, value, color)."""
    from billing.models import RentInvoice
    from complaints.models import Complaint
    from gatekeeping.models import GatePass, Visitor
    from rooms.models import Bed
    from tenants.models import RoomChangeRequest, Tenant

    role = user.role
    if role in ("ADMIN", "WARDEN"):
        beds = Bed.objects.count()
        occ = Bed.objects.filter(is_occupied=True).count()
        dues = RentInvoice.objects.exclude(status="PAID").aggregate(s=Sum("amount"))["s"] or 0
        return [
            ("Beds occupied", f"{occ} / {beds}", "primary"),
            ("Active tenants", Tenant.objects.filter(allotments__is_active=True).distinct().count(), "success"),
            ("Rent due", f"₹{dues}", "danger"),
            ("Open complaints", Complaint.objects.exclude(status="RESOLVED").count(), "warning"),
            ("Pending gate passes", GatePass.objects.filter(status="PENDING").count(), "secondary"),
            ("Room requests", RoomChangeRequest.objects.filter(status="PENDING").count(), "dark"),
        ]
    if role == "TENANT":
        unpaid = RentInvoice.objects.filter(tenant__user=user).exclude(status="PAID")
        due = unpaid.aggregate(s=Sum("amount"))["s"] or 0
        return [
            ("Rent due", f"₹{due}", "danger"),
            ("Unpaid invoices", unpaid.count(), "warning"),
            ("Open complaints", Complaint.objects.filter(tenant__user=user).exclude(status="RESOLVED").count(), "primary"),
            ("Active gate passes", GatePass.objects.filter(tenant__user=user, status__in=["APPROVED", "OUT"]).count(), "success"),
        ]
    if role == "STAFF":
        mine = Complaint.objects.filter(assigned_to=user)
        return [
            ("Pending tasks", mine.exclude(status="RESOLVED").count(), "danger"),
            ("Resolved", mine.filter(status="RESOLVED").count(), "success"),
        ]
    if role == "GUARD":
        return [
            ("Currently out", GatePass.objects.filter(status="OUT").count(), "primary"),
            ("Waiting to leave", GatePass.objects.filter(status="APPROVED").count(), "warning"),
            ("Visitors inside", Visitor.objects.filter(out_time__isnull=True).count(), "success"),
        ]
    if role == "MESS":
        return [
            ("Active tenants", Tenant.objects.filter(allotments__is_active=True).distinct().count(), "primary"),
        ]
    return []


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_role(self):
        role = self.request.POST.get("role") or self.request.GET.get("role", "")
        return role if role in User.Role.values else ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        role = self.get_role()
        ctx["role"] = role
        ctx["role_label"] = dict(User.Role.choices).get(role, "")
        return ctx

    def form_valid(self, form):
        role = self.get_role()
        user = form.get_user()
        if role and user.role != role:
            label = dict(User.Role.choices)[role]
            form.add_error(None, f"This account does not belong to {label}. Please choose the correct role.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard")


class RoleLogoutView(LogoutView):
    next_page = "home"


@login_required
def dashboard(request):
    cards = []
    for target, icon, title, desc, color in MENUS.get(request.user.role, MENUS["TENANT"]):
        url = target if target.startswith("/") else reverse(target)
        cards.append({"url": url, "icon": icon, "title": title, "desc": desc, "color": color})
    return render(request, "dashboards/home.html", {
        "cards": cards,
        "stats": build_stats(request.user),
    })


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html", {"roles": ROLE_CARDS})