from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import F

from .forms import PollForm, PollOptionFormSet
from .models import Poll, PollOption, Vote


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


def _build_option_stats(poll: Poll, request_user) -> dict:
    options = list(poll.options.all().order_by("id"))
    total_votes = sum(option.votes_count for option in options)
    selected_option_id = None
    has_voted = False

    if request_user.is_authenticated:
        user_vote = (
            Vote.objects.filter(poll=poll, user=request_user)
            .select_related("option")
            .first()
        )
        if user_vote is not None:
            has_voted = True
            selected_option_id = user_vote.option_id

    for option in options:
        option.vote_rate = (
            round((option.votes_count / total_votes) * 100, 1) if total_votes else 0.0
        )

    return {
        "options": options,
        "total_votes": total_votes,
        "has_voted": has_voted,
        "selected_option_id": selected_option_id,
    }


def poll_list(request):
    now = timezone.now()
    base_qs = Poll.objects.select_related("created_by").annotate(
        participant_count=Count("votes", distinct=True)
    )

    active_polls = base_qs.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    ended_polls = base_qs.filter(expires_at__lte=now)

    return render(
        request,
        "polls/list.html",
        {
            "active_polls": active_polls,
            "ended_polls": ended_polls,
        },
    )


def poll_detail(request, pk: int):
    poll = get_object_or_404(Poll, pk=pk)
    option_context = _build_option_stats(poll, request.user)

    if request.method == "POST":
        if not request.user.is_authenticated:
            next_url = request.get_full_path()
            return redirect(f"{reverse('accounts:login')}?next={next_url}")

        if poll.is_closed:
            messages.error(request, "마감된 투표는 참여할 수 없습니다.")
            return redirect("polls:detail", pk=poll.pk)

        option_id = request.POST.get("option")
        if not option_id:
            messages.error(request, "투표할 선택지를 골라주세요.")
            return redirect("polls:detail", pk=poll.pk)

        option = get_object_or_404(PollOption, pk=option_id, poll=poll)
        if Vote.objects.filter(poll=poll, user=request.user).exists():
            messages.info(request, "이미 이 투표에 참여했습니다.")
            return redirect("polls:detail", pk=poll.pk)

        try:
            with transaction.atomic():
                Vote.objects.create(poll=poll, option=option, user=request.user)
                PollOption.objects.filter(pk=option.pk).update(votes_count=F("votes_count") + 1)
        except IntegrityError:
            messages.info(request, "이미 이 투표에 참여했습니다.")
        else:
            messages.success(request, "투표가 완료되었습니다. 결과를 확인합니다.")

        return redirect("polls:detail", pk=poll.pk)

    return render(
        request,
        "polls/detail.html",
        {
            "poll": poll,
            "can_vote": not poll.is_closed and request.user.is_authenticated and not option_context["has_voted"],
            **option_context,
        },
    )


@_admin_required
def poll_create(request):
    if request.method == "POST":
        poll_form = PollForm(request.POST)
        option_formset = PollOptionFormSet(request.POST)
        if poll_form.is_valid() and option_formset.is_valid():
            poll = poll_form.save(commit=False)
            poll.created_by = request.user
            poll.save()
            option_formset.instance = poll
            option_formset.save()
            messages.success(request, "투표를 생성했습니다.")
            return redirect("polls:list")
    else:
        poll_form = PollForm()
        option_formset = PollOptionFormSet(queryset=PollOption.objects.none())

    return render(
        request,
        "polls/form.html",
        {
            "title": "투표 만들기",
            "poll_form": poll_form,
            "option_formset": option_formset,
        },
    )


def poll_results(request, pk: int):
    poll = get_object_or_404(Poll, pk=pk)
    return render(
        request,
        "polls/result.html",
        {"poll": poll, **_build_option_stats(poll, request.user)},
    )


@_admin_required
@require_POST
def poll_delete(request, pk: int):
    poll = get_object_or_404(Poll, pk=pk)
    poll.delete()
    messages.success(request, "투표를 삭제했습니다.")
    return redirect("polls:list")
