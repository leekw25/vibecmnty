from __future__ import annotations

from django.conf import settings
from django.db import models


class Survey(models.Model):
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="surveys",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class Question(models.Model):
    class Type(models.TextChoices):
        TEXT = "TEXT", "Text"
        TEXTAREA = "TEXTAREA", "Long text"
        CHOICE = "CHOICE", "Single choice"
        MULTIPLE = "MULTIPLE", "Multiple choice"
        SCALE = "SCALE", "Scale 1-5"

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=240)
    question_type = models.CharField(max_length=12, choices=Type.choices)
    required = models.BooleanField(default=True)
    options = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.text


class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    respondent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="survey_responses",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("survey", "respondent")

    def __str__(self) -> str:
        return f"{self.survey_id}:{self.respondent_id}"


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    answer_text = models.TextField()

    class Meta:
        unique_together = ("response", "question")

    def __str__(self) -> str:
        return f"{self.response_id}:{self.question_id}"
