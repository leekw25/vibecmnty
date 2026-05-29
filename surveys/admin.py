from __future__ import annotations

from django.contrib import admin

from .models import Answer, Question, Response, Survey


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "is_anonymous", "expires_at", "created_at")
    list_filter = ("is_anonymous", "expires_at")
    search_fields = ("title", "description")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "survey", "question_type", "required", "order")
    list_filter = ("question_type", "required")
    inlines = [AnswerInline]


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "respondent", "submitted_at")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("response", "question", "answer_text")
