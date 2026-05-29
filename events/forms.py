from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "start_date",
            "end_date",
            "location",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "w-full rounded border px-3 py-2", "required": True}
            ),
            "description": forms.Textarea(
                attrs={"class": "w-full rounded border px-3 py-2 h-28"}
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded border px-3 py-2"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded border px-3 py-2"}
            ),
            "location": forms.TextInput(
                attrs={"class": "w-full rounded border px-3 py-2"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise ValidationError("종료일은 시작일보다 빠를 수 없습니다.")

        return cleaned_data
