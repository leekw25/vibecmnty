from __future__ import annotations

from django.conf import settings
from django.db import models


class Notice(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notices")
    title = models.CharField(max_length=160)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_important", "-created_at"]
        indexes = [
            models.Index(fields=["is_important", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title
