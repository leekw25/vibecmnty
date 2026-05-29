from __future__ import annotations

from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "start_date", "end_date", "location")
    list_filter = ("start_date", "end_date")
    search_fields = ("title", "description")
