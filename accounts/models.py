from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "USER", "User"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True, max_length=1200)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/%d", null=True, blank=True)

    def __str__(self) -> str:
        return self.get_short_name() or self.username

    @property
    def is_admin_member(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser

    def get_absolute_url(self) -> str:
        return reverse("accounts:profile")
