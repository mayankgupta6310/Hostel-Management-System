from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.emails import notify_user
from billing.models import RentInvoice


class Command(BaseCommand):
    help = "Due date se 3 din ke andar wale pending invoices ka reminder bhejta hai"

    def handle(self, *args, **options):
        today = timezone.localdate()
        upto = today + timedelta(days=3)

        invoices = RentInvoice.objects.filter(
            status=RentInvoice.Status.PENDING,
            due_date__gte=today,
            due_date__lte=upto,
        ).select_related("tenant__user")

        sent = 0
        for inv in invoices:
            ok = notify_user(
                inv.tenant.user,
                f"Rent reminder - due {inv.due_date:%d %b}",
                f"Rs. {inv.amount} rent is due by {inv.due_date:%d %b %Y}.\n"
                f"It will be marked overdue if paid late.\n\nHostel Management",
            )
            sent += int(ok)
        self.stdout.write(self.style.SUCCESS(f"{sent} reminder bheje."))