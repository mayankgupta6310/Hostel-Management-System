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