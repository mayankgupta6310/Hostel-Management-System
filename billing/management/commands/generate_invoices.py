from django.core.management.base import BaseCommand
from billing.services import generate_monthly_invoices


class Command(BaseCommand):
    help = "Is mahine ke rent invoices generate karta hai"

    def handle(self, *args, **options):
        n = generate_monthly_invoices()
        self.stdout.write(self.style.SUCCESS(f"{n} new invoice(s) created."))