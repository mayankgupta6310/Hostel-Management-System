from django.conf import settings
from django.db import models


class Complaint(models.Model):
    class Category(models.TextChoices):
        ELECTRICAL = "ELECTRICAL", "Electrical"
        PLUMBING = "PLUMBING", "Plumbing"
        FURNITURE = "FURNITURE", "Furniture"
        CLEANING = "CLEANING", "Cleaning"
        INTERNET = "INTERNET", "Wi-Fi / Internet"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="complaints")
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.OTHER)
    title = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to="complaints/", blank=True, null=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="assigned_complaints",
    )
    staff_remark = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    @property
    def badge_class(self):
        return {
            "OPEN": "bg-danger",
            "ASSIGNED": "bg-info text-dark",
            "IN_PROGRESS": "bg-warning text-dark",
            "RESOLVED": "bg-success",
        }[self.status]
    @property
    def priority_badge(self):
        return {"HIGH": "bg-danger", 
                "MEDIUM": "bg-warning text-dark",
                 "LOW": "bg-secondary"
        }[self.priority]