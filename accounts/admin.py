from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("display_name", "bio", "avatar", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("권한", {"fields": ("role",)}),
    )
