from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from allauth.account.views import LoginView as AllauthLoginView
from allauth.account.views import LogoutView as AllauthLogoutView
from allauth.account.views import SignupView as AllauthSignupView

from .forms import LoginFormWithStyle, PasswordChangeFormWithStyle, ProfileForm, SignupFormWithStyle


class LoginView(AllauthLoginView):
    template_name = "accounts/login.html"
    form_class = LoginFormWithStyle

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Login completed.")
        return response

    def get_success_url(self):
        return super().get_success_url() or reverse_lazy("home")


class SignupView(AllauthSignupView):
    template_name = "accounts/signup.html"
    form_class = SignupFormWithStyle

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Account created and signed in.")
        return response

    def get_success_url(self):
        return reverse_lazy("accounts:profile")


class LogoutView(AllauthLogoutView):
    next_page = reverse_lazy("home")


@login_required(login_url=reverse_lazy("accounts:login"))
def profile_view(request):
    return render(
        request,
        "accounts/profile.html",
        {"title": "My Profile"},
    )


@login_required(login_url=reverse_lazy("accounts:login"))
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile_form.html",
        {
            "title": "Edit Profile",
            "form": form,
        },
    )


@login_required(login_url=reverse_lazy("accounts:login"))
def password_change_view(request):
    form = PasswordChangeFormWithStyle(request.user, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Password updated.")
        return redirect("accounts:profile")

    return render(
        request,
        "accounts/password_change.html",
        {
            "title": "Change Password",
            "form": form,
        },
    )


def is_admin_member(user):
    return user.is_authenticated and getattr(user, "is_admin_member", False)


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url=reverse_lazy("accounts:login"))
    def wrapped_view(request, *args, **kwargs):
        if not is_admin_member(request.user):
            messages.error(request, "Admin access is required.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapped_view


@admin_required
def admin_probe_view(request):
    """Simple admin gate endpoint."""
    return redirect("admin_dashboard:home")
