from django.conf import settings
from django.db import models
from django.utils import timezone

import uuid

class GatePass(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        OUT = "OUT", "Out"
        RETURNED = "RETURNED", "Returned"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="gate_passes")
    reason = models.CharField(max_length=200)
    out_time = models.DateTimeField(help_text="When are you leaving")
    expected_return = models.DateTimeField(help_text="When will you return")
    token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="approved_passes",
    )
    actual_out = models.DateTimeField(null=True, blank=True)
    actual_return = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pass #{self.pk} - {self.tenant}"

    @property
    def is_late(self):
        if self.status == self.Status.OUT:
            return timezone.now() > self.expected_return
        if self.status == self.Status.RETURNED and self.actual_return:
            return self.actual_return > self.expected_return
        return False

    @property
    def badge_class(self):
        return {
            "PENDING": "bg-warning text-dark",
            "APPROVED": "bg-info text-dark",
            "REJECTED": "bg-secondary",
            "OUT": "bg-primary",
            "RETURNED": "bg-success",
        }[self.status]


class Visitor(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="visitors")
    visitor_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    purpose = models.CharField(max_length=150, blank=True)
    in_time = models.DateTimeField(auto_now_add=True)
    out_time = models.DateTimeField(null=True, blank=True)
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-in_time"]

    def __str__(self):
        return f"{self.visitor_name} -> {self.tenant}"