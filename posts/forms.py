from __future__ import annotations

from django import forms

from .models import Post
from .models import Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "w-full rounded border px-3 py-2", "placeholder": "제목"},
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "w-full rounded border px-3 py-2 h-40 resize-y",
                    "placeholder": "내용을 입력하세요",
                }
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "w-full rounded border px-3 py-2 h-20 resize-y",
                    "placeholder": "댓글을 입력하세요",
                }
            )
        }
