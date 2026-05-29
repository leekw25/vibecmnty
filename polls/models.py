from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Poll(models.Model):
    question = models.CharField(max_length=240)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="polls",
    )
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_closed(self) -> bool:
        if self.expires_at is None:
            return False
        return self.expires_at <= timezone.now()

    @property
    def status_label(self) -> str:
        return "마감됨" if self.is_closed else "진행중"

    def __str__(self) -> str:
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=160)
    votes_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]
        unique_together = ("poll", "text")

    def __str__(self) -> str:
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("poll", "user")

    def __str__(self) -> str:
        return f"{self.poll_id}:{self.user_id}"
