from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import NoticeForm
from .models import Notice


def _is_admin_user(user) -> bool:
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or getattr(user, "is_admin_member", False)
    )


def _admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _is_admin_user(request.user):
            raise PermissionDenied("Admin permission is required.")
        return view_func(request, *args, **kwargs)

    return wrapper


def notice_list(request):
    qs = Notice.objects.all().select_related("author").order_by("-is_important", "-created_at")
    page = request.GET.get("page", "1")
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page)

    return render(request, "notices/list.html", {"page_obj": page_obj})


def notice_detail(request, pk: int):
    notice = get_object_or_404(Notice, pk=pk)
    can_manage = _is_admin_user(request.user)
    return render(request, "notices/detail.html", {"notice": notice, "can_manage": can_manage})


@_admin_required
def notice_create(request):
    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.author = request.user
            notice.save()
            messages.success(request, "Notice created.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm()

    return render(
        request,
        "notices/form.html",
        {
            "title": "공지사항 작성",
            "submit_label": "등록",
            "form": form,
        },
    )


@_admin_required
def notice_update(request, pk: int):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == "POST":
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, "Notice updated.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)

    return render(
        request,
        "notices/form.html",
        {
            "title": "공지사항 수정",
            "submit_label": "수정",
            "form": form,
            "cancel_url": f"/notices/{notice.pk}/",
        },
    )


@_admin_required
@require_POST
def notice_delete(request, pk: int):
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    messages.success(request, "Notice deleted.")
    return redirect("notices:list")
