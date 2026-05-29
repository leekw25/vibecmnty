from __future__ import annotations

from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_important", "created_at")
    list_filter = ("is_important", "created_at")
    search_fields = ("title", "content")
