from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import calendar
from urllib.parse import quote_plus

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import EventForm
from .models import Event


def _is_admin_user(user) -> bool:
    return bool(
        user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "is_admin_member", False)
        )
    )


def _admin_blocked_response(request):
    messages.error(request, "관리자만 일정 추가가 가능합니다.")
    return redirect("events:calendar")


def _google_date_range(start_date: date, end_date: date | None) -> tuple[str, str]:
    start = start_date.strftime("%Y%m%d")
    end = (end_date or start_date) + timedelta(days=1)
    return start, end.strftime("%Y%m%d")


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    year = int(year)
    month = int(month)
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last


def _shift_month(current_year: int, current_month: int, delta: int) -> tuple[int, int]:
    y = current_year + ((current_month - 1 + delta) // 12)
    m = (current_month - 1 + delta) % 12 + 1
    return y, m


def _parse_date_param(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _build_month_payload(year: int, month: int) -> tuple[
    date, date, list[list[date]], int, int, int, int
]:
    first, last = _month_bounds(year, month)
    calendar_rows = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)
    prev_year, prev_month = _shift_month(year, month, -1)
    next_year, next_month = _shift_month(year, month, 1)
    return (
        first,
        last,
        calendar_rows,
        prev_year,
        prev_month,
        next_year,
        next_month,
    )


def _build_events_by_date(events: list[Event], first: date, last: date) -> dict[date, list[Event]]:
    by_date: dict[date, list[Event]] = defaultdict(list)
    for event in events:
        start = event.start_date
        end = event.end_date or event.start_date
        current = max(start, first)
        end = min(end, last)
        while current <= end:
            by_date[current].append(event)
            current += timedelta(days=1)
    return by_date


def _build_calendar_rows(
    calendar_rows: list[list[date]], events_by_date: dict[date, list[Event]]
) -> list[list[dict[str, object]]]:
    output_rows: list[list[dict[str, object]]] = []
    for week in calendar_rows:
        row: list[dict[str, object]] = []
        for day in week:
            row.append({"date": day, "events": events_by_date.get(day, [])})
        output_rows.append(row)
    return output_rows


def event_calendar(request):
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except ValueError:
        year, month = today.year, today.month
    if not (1 <= month <= 12):
        year, month = today.year, today.month

    first, last, calendar_rows, prev_year, prev_month, next_year, next_month = (
        _build_month_payload(year, month)
    )

    events = list(
        Event.objects.filter(
            Q(start_date__lte=last),
            Q(end_date__isnull=True) | Q(end_date__gte=first),
        ).order_by("start_date", "title")
    )
    by_date = _build_events_by_date(events, first, last)

    selected_day = _parse_date_param(request.GET.get("day"))
    if selected_day and (selected_day < first or selected_day > last):
        selected_day = None

    selected_day_events = []
    if selected_day:
        selected_day_events = by_date.get(selected_day, [])

    table_rows = _build_calendar_rows(calendar_rows, by_date)

    return render(
        request,
        "events/calendar.html",
        {
            "today": today,
            "year": year,
            "month": month,
            "weekdays": ["일", "월", "화", "수", "목", "금", "토"],
            "calendar_rows": table_rows,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "selected_day": selected_day,
            "selected_day_events": selected_day_events,
            "is_admin_user": _is_admin_user(request.user),
        },
    )


def event_detail(request, pk: int):
    event = get_object_or_404(Event, pk=pk)
    start, end = _google_date_range(event.start_date, event.end_date)
    google_url = (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE&text={quote_plus(event.title)}"
        f"&dates={start}/{end}"
        f"&details={quote_plus(event.description or '')}"
        f"&location={quote_plus(event.location or '')}"
        "&sf=true&output=xml"
        "&source=VibeCommunity"
    )
    event_url = request.build_absolute_uri(reverse("events:detail", args=[event.pk]))

    return render(
        request,
        "events/detail.html",
        {
            "event": event,
            "event_url": event_url,
            "google_url": google_url,
            "is_admin_user": _is_admin_user(request.user),
        },
    )


@login_required(login_url="/login/")
def event_create(request):
    if not _is_admin_user(request.user):
        return _admin_blocked_response(request)

    initial_date = _parse_date_param(request.GET.get("start_date"))
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Event created.")
            return redirect("events:detail", pk=event.pk)
    else:
        form = EventForm(initial={"start_date": initial_date})

    return render(
        request,
        "events/manage.html",
        {
            "title": "일정 등록",
            "form": form,
            "submit_label": "등록",
            "is_admin_user": True,
        },
    )


@login_required(login_url="/login/")
def event_update(request, pk: int):
    if not _is_admin_user(request.user):
        return _admin_blocked_response(request)

    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated.")
            return redirect("events:detail", pk=event.pk)
    else:
        form = EventForm(instance=event)

    return render(
        request,
        "events/manage.html",
        {
            "title": "일정 수정",
            "form": form,
            "submit_label": "저장",
            "is_admin_user": True,
            "event": event,
        },
    )


@login_required(login_url="/login/")
def event_delete(request, pk: int):
    if not _is_admin_user(request.user):
        return _admin_blocked_response(request)

    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted.")
        return redirect("events:calendar")

    return render(
        request,
        "events/form_confirm_delete.html",
        {"title": "일정 삭제", "event": event, "is_admin_user": True},
    )
