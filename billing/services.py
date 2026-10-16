from django.utils import timezone

from accounts.emails import notify_user
from tenants.models import Allotment
from .models import RentInvoice


def mark_overdue(today=None):
    today = today or timezone.localdate()
    return RentInvoice.objects.filter(
        status=RentInvoice.Status.PENDING, due_date__lt=today
    ).update(status=RentInvoice.Status.OVERDUE)


def generate_monthly_invoices(today=None):
    """Har active allotment ke liye is mahine ka invoice banao (duplicate nahi banega)."""
    today = today or timezone.localdate()
    month = today.replace(day=1)
    due = month.replace(day=10)

    allotments = Allotment.objects.filter(is_active=True).select_related(
        "tenant__user", "bed__room"
    )
    created = 0
    for a in allotments:
        invoice, was_created = RentInvoice.objects.get_or_create(
            tenant=a.tenant,
            month=month,
            defaults={
                "amount": a.bed.room.rent_per_bed,
                "due_date": due,
                "description": f"Room {a.bed.room.room_no} / {a.bed.bed_no}",
            },
        )
        if was_created:
            created += 1
            notify_user(
                a.tenant.user,
                f"Rent invoice - {month:%B %Y}",
                f"Hello {a.tenant.user.get_full_name() or a.tenant.user.username},\n\n"
                f"{month:%B %Y} rent invoice has been generated.\n"
                f"Amount: Rs. {invoice.amount}\n"
                f"Due date: {invoice.due_date:%d %b %Y}\n\n"
                f"Hostel Management",
            )

    mark_overdue(today)
    return created