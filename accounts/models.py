from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin/Owner"
        WARDEN = "WARDEN", "Warden"
        TENANT = "TENANT", "Tenant"
        MESS = "MESS", "Mess Manager"
        GUARD = "GUARD", "Security Guard"
        STAFF = "STAFF", "Maintenance Staff"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.TENANT)
    phone = models.CharField(max_length=15, blank=True)