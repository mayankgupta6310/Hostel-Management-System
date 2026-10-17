import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from billing.models import Payment, RentInvoice
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Create 6 months of DEMO rent history for active tenants (for testing the risk model)."

    def handle(self, *args, **options):
        random.seed(11)
        today = timezone.localdate()
        tenants = Tenant.objects.filter(allotments__is_active=True).distinct().order_by("pk")
        created = 0

        for i, tenant in enumerate(tenants):
            late_chance = 0.8 if i % 2 else 0.1       # alternate: habitual late payer / good payer
            allot = tenant.current_allotment
            for k in range(6, 0, -1):
                year, mon = divmod(today.year * 12 + today.month - 1 - k, 12)
                month = today.replace(year=year, month=mon + 1, day=1)
                due = month.replace(day=10)

                inv, was_created = RentInvoice.objects.get_or_create(
                    tenant=tenant, month=month,
                    defaults={
                        "amount": allot.bed.room.rent_per_bed,
                        "due_date": due,
                        "status": RentInvoice.Status.PAID,
                        "description": f"Room {allot.bed.room.room_no} / {allot.bed.bed_no}",
                    },
                )
                if not was_created:
                    continue
                late = random.random() < late_chance
                paid_on = due + timedelta(days=random.randint(1, 12)) if late else due - timedelta(days=random.randint(0, 5))
                pay = Payment.objects.create(invoice=inv, amount=inv.amount, method=Payment.Method.CASH)
                Payment.objects.filter(pk=pay.pk).update(
                    paid_at=timezone.make_aware(datetime.combine(paid_on, time(12, 0)))
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} demo invoices created."))