from django.conf import settings
from django.db import models


class RentInvoice(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="invoices")
    month = models.DateField(help_text="First day of the month")
    description = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "month")
        ordering = ["-month", "tenant"]

    def __str__(self):
        return f"{self.tenant} - {self.month:%b %Y}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        UPI = "UPI", "UPI"
        ONLINE = "ONLINE", "Online (Razorpay)"

    invoice = models.ForeignKey(RentInvoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    txn_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.invoice} - Rs.{self.amount}"

class SecurityDeposit(models.Model):
    class Status(models.TextChoices):
        HELD = "HELD", "Held"
        REFUNDED = "REFUNDED", "Refunded"

    tenant = models.OneToOneField("tenants.Tenant", on_delete=models.CASCADE, related_name="deposit")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    collected_on = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.HELD)
    deduction = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deduction_reason = models.CharField(max_length=250, blank=True)
    refunded_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    refunded_on = models.DateField(null=True, blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        ordering = ["-collected_on"]

    def __str__(self):
        return f"Deposit {self.tenant} - Rs.{self.amount}"