from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from allauth.account.forms import LoginForm, SignupForm


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["display_name", "bio", "avatar", "first_name", "last_name"]


class TailwindAuthMixin:
    """Apply consistent Tailwind classes to auth form fields."""

    _TW_INPUT_CLASS = (
        "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
        " focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
    )

    def _set_tailwind_widget_attrs(self) -> None:
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = self._TW_INPUT_CLASS


class LoginFormWithStyle(TailwindAuthMixin, LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_tailwind_widget_attrs()


class SignupFormWithStyle(TailwindAuthMixin, SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_tailwind_widget_attrs()


class PasswordChangeFormWithStyle(TailwindAuthMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_tailwind_widget_attrs()
