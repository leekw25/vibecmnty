from __future__ import annotations

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Poll, PollOption


class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ["question", "expires_at"]
        widgets = {
            "question": forms.TextInput(
                attrs={"class": "w-full rounded border px-3 py-2"}
            ),
            "expires_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "w-full rounded border px-3 py-2"}
            ),
        }


class _PollOptionBaseFormSet(BaseInlineFormSet):
    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return

        filled = [
            f.cleaned_data.get("text", "").strip()
            for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get("DELETE", False)
        ]
        selected = [text for text in filled if text]

        if len(selected) < 2:
            raise forms.ValidationError("최소 2개 이상의 선택지를 입력해주세요.")
        if len(selected) > 10:
            raise forms.ValidationError("최대 10개까지 등록 가능합니다.")


PollOptionFormSet = inlineformset_factory(
    Poll,
    PollOption,
    fields=["text"],
    extra=2,
    min_num=2,
    max_num=10,
    validate_min=True,
    validate_max=True,
    can_delete=False,
    formset=_PollOptionBaseFormSet,
    widgets={
        "text": forms.TextInput(attrs={"class": "w-full rounded border px-3 py-2"}),
    },
)
