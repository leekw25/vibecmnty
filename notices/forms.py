from __future__ import annotations

from django import forms

from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["title", "content", "is_important"]
        labels = {
            "is_important": "중요 공지",
            "title": "제목",
            "content": "내용",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "w-full rounded border px-3 py-2"},
            ),
            "content": forms.Textarea(
                attrs={"class": "w-full rounded border px-3 py-2 h-48"},
            ),
            "is_important": forms.CheckboxInput(
                attrs={"class": "h-4 w-4 rounded border-slate-300"},
            ),
        }
