from django.conf import settings
from django.db import models


class Notice(models.Model):
    title = models.CharField(max_length=150)
    body = models.TextField()
    is_important = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_important", "-created_at"]

    def __str__(self):
        return self.title