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
        ("room_list", "🛏️", "Rooms & Beds", "Rooms banao, occupancy dekho", "primary"),
        ("tenant_list", "🎓", "Tenants", "Register, bed allot, checkout", "success"),
        ("invoice_list", "💰", "Rent / Invoices", "Invoice banao, payment mark karo", "warning"),
        ("deposit_list", "🏦", "Security Deposits", "Deposit aur refund", "warning"),
        ("complaint_list", "🛠️", "Complaints", "Staff ko assign karo", "danger"),
        ("pass_list", "🚪", "Gate Passes", "Approve / reject", "secondary"),
        ("visitor_list", "👥", "Visitor Log", "Visitor entry-exit record", "dark"),
        ("change_list", "🔁", "Room Requests", "Room change approve karo", "secondary"),
        ("mess_menu", "🍛", "Mess", "Menu aur meal count", "warning"),
        ("reports", "📊", "Reports", "Charts aur Excel export", "dark"),
        ("notice_list", "📢", "Notices", "Announcements", "primary"),
        ("/admin/", "⚙️", "Admin Panel", "Users aur data manage", "dark"),
    ],
    "WARDEN": [
        ("room_list", "🛏️", "Rooms & Beds", "Occupancy dekho", "primary"),
        ("tenant_list", "🎓", "Tenants", "Register, bed allot, checkout", "success"),
        ("invoice_list", "💰", "Rent / Invoices", "Invoice aur payment", "warning"),
        ("deposit_list", "🏦", "Security Deposits", "Deposit aur refund", "warning"),
        ("complaint_list", "🛠️", "Complaints", "Staff ko assign karo", "danger"),
        ("pass_list", "🚪", "Gate Passes", "Approve / reject", "secondary"),
        ("visitor_list", "👥", "Visitor Log", "Visitor record", "dark"),
        ("change_list", "🔁", "Room Requests", "Room change approve karo", "secondary"),
        ("mess_menu", "🍛", "Mess", "Menu dekho", "warning"),
        ("reports", "📊", "Reports", "Charts aur Excel export", "dark"),
        ("notice_list", "📢", "Notices", "Announcements", "primary"),
    ],
    "TENANT": [
        ("my_invoices", "💰", "My Rent", "Invoice aur receipt PDF", "warning"),
        ("my_deposit", "🏦", "My Deposit", "Security deposit status", "warning"),
        ("my_complaints", "🛠️", "My Complaints", "Complaint daalo aur track karo", "danger"),
        ("my_passes", "🚪", "Gate Pass", "Request aur QR code", "secondary"),
        ("my_changes", "🔁", "Room Change", "Dusre bed ki request", "primary"),
        ("mess_menu", "🍛", "Mess", "Menu, meal ON/OFF, feedback", "success"),
        ("notice_list", "📢", "Notices", "Hostel announcements", "dark"),
    ],
    "STAFF": [
        ("staff_tasks", "🔧", "Mere Tasks", "Assigned kaam aur status", "primary"),
        ("notice_list", "📢", "Notices", "Announcements", "dark"),
    ],
    "GUARD": [
        ("guard_panel", "💂", "Guard Panel", "Out / In aur visitors", "primary"),
        ("scan", "📷", "QR Scan", "Gate pass scan karo", "success"),
        ("visitor_add", "➕", "Visitor Entry", "Naya visitor", "warning"),
        ("visitor_list", "👥", "Visitor Log", "Poora record", "dark"),
        ("notice_list", "📢", "Notices", "Announcements", "secondary"),
    ],
    "MESS": [
        ("mess_menu", "🍛", "Menu", "Weekly menu dekho", "primary"),
        ("menu_edit", "✏️", "Menu Set Karo", "Din aur meal ka menu", "warning"),
        ("meal_count", "🔢", "Meal Count", "Kal kitne log khayenge", "success"),
        ("feedback_list", "⭐", "Feedback", "Ratings aur comments", "danger"),
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
            ("Beds bhare", f"{occ} / {beds}", "primary"),
            ("Active tenants", Tenant.objects.filter(allotments__is_active=True).distinct().count(), "success"),
            ("Rent baaki", f"₹{dues}", "danger"),
            ("Khuli complaints", Complaint.objects.exclude(status="RESOLVED").count(), "warning"),
            ("Pending gate pass", GatePass.objects.filter(status="PENDING").count(), "secondary"),
            ("Room requests", RoomChangeRequest.objects.filter(status="PENDING").count(), "dark"),
        ]
    if role == "TENANT":
        unpaid = RentInvoice.objects.filter(tenant__user=user).exclude(status="PAID")
        due = unpaid.aggregate(s=Sum("amount"))["s"] or 0
        return [
            ("Rent baaki", f"₹{due}", "danger"),
            ("Unpaid invoices", unpaid.count(), "warning"),
            ("Khuli complaints", Complaint.objects.filter(tenant__user=user).exclude(status="RESOLVED").count(), "primary"),
            ("Active gate pass", GatePass.objects.filter(tenant__user=user, status__in=["APPROVED", "OUT"]).count(), "success"),
        ]
    if role == "STAFF":
        mine = Complaint.objects.filter(assigned_to=user)
        return [
            ("Pending tasks", mine.exclude(status="RESOLVED").count(), "danger"),
            ("Resolved", mine.filter(status="RESOLVED").count(), "success"),
        ]
    if role == "GUARD":
        return [
            ("Abhi bahar", GatePass.objects.filter(status="OUT").count(), "primary"),
            ("Nikalne wale", GatePass.objects.filter(status="APPROVED").count(), "warning"),
            ("Andar visitors", Visitor.objects.filter(out_time__isnull=True).count(), "success"),
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
            form.add_error(None, f"Yeh account {label} ka nahi hai. Sahi role chuno.")
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