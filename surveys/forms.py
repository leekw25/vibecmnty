from __future__ import annotations

from django import forms
from django.forms import formset_factory

from .models import Question, Survey


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ["title", "description", "is_anonymous", "expires_at"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "w-full rounded border px-3 py-2"},
            ),
            "description": forms.Textarea(
                attrs={"class": "w-full rounded border px-3 py-2 h-28"},
            ),
            "expires_at": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "w-full rounded border px-3 py-2",
                }
            ),
        }


class QuestionForm(forms.Form):
    text = forms.CharField(
        max_length=240,
        widget=forms.TextInput(attrs={"class": "w-full rounded border px-3 py-2"}),
        label="Question",
    )
    question_type = forms.ChoiceField(
        choices=Question.Type.choices,
        widget=forms.Select(attrs={"class": "w-full rounded border px-3 py-2 question-type-select"}),
        label="Type",
    )
    required = forms.BooleanField(required=False, initial=True, label="Required")
    options_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "w-full rounded border px-3 py-2 h-24",
                "rows": 3,
                "placeholder": "Choice options (one per line)",
            }
        ),
        label="Options",
    )

    def clean(self):
        cleaned = super().clean()
        q_type = cleaned.get("question_type")
        options_text = cleaned.get("options_text", "") or ""
        options = [line.strip() for line in options_text.splitlines() if line.strip()]

        if q_type in {Question.Type.CHOICE, Question.Type.MULTIPLE}:
            if len(options) < 2:
                raise forms.ValidationError(
                    "Single and multiple choice questions need at least 2 options."
                )
            if len(options) > 10:
                raise forms.ValidationError(
                    "Each choice question can include up to 10 options."
                )
            cleaned["options"] = options
        else:
            cleaned["options"] = []

        return cleaned


QuestionFormSet = formset_factory(
    QuestionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
