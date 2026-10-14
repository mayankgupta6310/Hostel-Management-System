from django.conf import settings
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_profile"
    )
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    id_proof = models.ImageField(upload_to="id_proofs/")
    joined_on = models.DateField(default=timezone.now)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def current_allotment(self):
        return self.allotments.filter(is_active=True).select_related("bed__room__hostel").first()


class Allotment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="allotments")
    bed = models.ForeignKey("rooms.Bed", on_delete=models.PROTECT, related_name="allotments")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tenant} -> {self.bed}"
class RoomChangeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="change_requests")
    current_bed = models.ForeignKey("rooms.Bed", on_delete=models.PROTECT, related_name="+")
    requested_bed = models.ForeignKey("rooms.Bed", on_delete=models.PROTECT, related_name="change_requests")
    reason = models.CharField(max_length=250)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    remark = models.CharField(max_length=250, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Change #{self.pk} - {self.tenant}"

    @property
    def badge_class(self):
        return {
            "PENDING": "bg-warning text-dark",
            "APPROVED": "bg-success",
            "REJECTED": "bg-secondary",
        }[self.status]