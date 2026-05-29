from __future__ import annotations

from django.contrib import admin

from .models import Poll, PollOption, Vote


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 1


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    inlines = [PollOptionInline]
    list_display = ("question", "created_by", "expires_at", "created_at")
    list_filter = ("expires_at", "created_by")
    search_fields = ("question", "created_by__username")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("poll", "option", "user", "created_at")
    list_filter = ("poll", "created_at")
