from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import Event
from notices.models import Notice
from polls.models import Poll
from posts.models import Comment, Post
from surveys.models import Survey


User = get_user_model()


def is_admin_user(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_staff or user.is_superuser or getattr(user, "is_admin_member", False))
    )


def _require_admin(view_func):
    @wraps(view_func)
    @login_required(login_url=reverse_lazy("accounts:login"))
    def _wrapped(request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied("관리자 권한이 필요합니다.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def _safe_redirect_to_admin_users(request, default: str = "admin_dashboard:users"):
    next_url = request.POST.get("next", "")
    if next_url.startswith("/admin-dashboard/"):
        return next_url
    return reverse(default)


def _active_counts(now) -> dict[str, int]:
    today = timezone.localdate()
    return {
        "total_users": User.objects.count(),
        "today_posts": Post.objects.filter(created_at__date=today).count(),
        "open_polls": Poll.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).count(),
        "open_surveys": Survey.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).count(),
        "upcoming_events": Event.objects.filter(
            Q(end_date__isnull=True, start_date__gte=today) | Q(end_date__gte=today)
        ).count(),
    }


def _recent_items(limit: int = 8) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    for post in Post.objects.select_related("author").order_by("-created_at")[:limit]:
        items.append(
            {
                "kind": "게시글",
                "title": post.title,
                "actor": post.author.username,
                "time": post.created_at,
                "link": reverse("posts:detail", args=[post.pk]),
                "detail": f"작성자 {post.author.username}",
            }
        )

    for comment in Comment.objects.select_related("author", "post").order_by("-created_at")[:limit]:
        title = comment.content[:60] + "..." if len(comment.content) > 60 else comment.content
        items.append(
            {
                "kind": "댓글",
                "title": title,
                "actor": comment.author.username,
                "time": comment.created_at,
                "link": reverse("posts:detail", args=[comment.post.pk]),
                "detail": f"게시글 {comment.post.title}",
            }
        )

    for notice in Notice.objects.select_related("author").order_by("-created_at")[:limit]:
        items.append(
            {
                "kind": "공지사항",
                "title": notice.title,
                "actor": notice.author.username,
                "time": notice.created_at,
                "link": reverse("notices:detail", args=[notice.pk]),
                "detail": f"중요 여부: {'중요' if notice.is_important else '일반'}",
            }
        )

    for event in Event.objects.select_related("created_by").order_by("-created_at")[:limit]:
        items.append(
            {
                "kind": "일정",
                "title": event.title,
                "actor": event.created_by.username if event.created_by else "시스템",
                "time": event.created_at,
                "link": reverse("events:detail", args=[event.pk]),
                "detail": f"시작일 {event.start_date}",
            }
        )

    for poll in Poll.objects.select_related("created_by").order_by("-created_at")[:limit]:
        items.append(
            {
                "kind": "투표",
                "title": poll.question,
                "actor": poll.created_by.username,
                "time": poll.created_at,
                "link": reverse("polls:detail", args=[poll.pk]),
                "detail": f"상태: {'종료' if poll.is_closed else '진행중'}",
            }
        )

    for survey in Survey.objects.select_related("created_by").order_by("-created_at")[:limit]:
        items.append(
            {
                "kind": "설문조사",
                "title": survey.title,
                "actor": survey.created_by.username,
                "time": survey.created_at,
                "link": reverse("surveys:respond", args=[survey.pk]),
                "detail": f"문항 수 {survey.questions.count()}",
            }
        )

    items.sort(key=lambda item: item["time"], reverse=True)
    return items[:limit]


@_require_admin
def dashboard_home(request):
    now = timezone.now()
    return render(
        request,
        "admin_dashboard/home.html",
        {
            "section": "dashboard",
            "section_title": "메인 대시보드",
            "stats": _active_counts(now),
            "recent_activities": _recent_items(limit=8),
        },
    )


@_require_admin
def notice_management(request):
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        selected_ids = [item for item in request.POST.getlist("notice_ids") if item.isdigit()]
        if action == "delete":
            if selected_ids:
                Notice.objects.filter(pk__in=selected_ids).delete()
                messages.success(request, f"{len(selected_ids)}개의 공지사항을 삭제했습니다.")
            else:
                messages.warning(request, "삭제할 공지사항을 선택하세요.")
        return redirect("admin_dashboard:notices")

    q = request.GET.get("q", "").strip()
    queryset = Notice.objects.select_related("author").order_by("-created_at")
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(content__icontains=q)
            | Q(author__username__icontains=q)
        )

    return render(
        request,
        "admin_dashboard/notice_management.html",
        {
            "section": "notices",
            "section_title": "공지사항 관리",
            "notices": queryset,
            "q": q,
            "notice_count": queryset.count(),
        },
    )


@_require_admin
def post_management(request):
    tab = request.GET.get("tab", "posts")
    q = request.GET.get("q", "").strip()

    posts = Post.objects.select_related("author").annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
    ).order_by("-created_at")
    comments = Comment.objects.select_related("author", "post").order_by("-created_at")

    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(content__icontains=q))
        comments = comments.filter(
            Q(content__icontains=q)
            | Q(post__title__icontains=q)
            | Q(author__username__icontains=q)
        )

    return render(
        request,
        "admin_dashboard/post_management.html",
        {
            "section": "posts",
            "section_title": "게시글 및 댓글 관리",
            "tab": "comments" if tab == "comments" else "posts",
            "q": q,
            "posts": posts,
            "comments": comments,
        },
    )


@_require_admin
def event_management(request):
    q = request.GET.get("q", "").strip()
    events = Event.objects.select_related("created_by").order_by("-start_date")
    if q:
        events = events.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(location__icontains=q)
            | Q(created_by__username__icontains=q)
        )

    return render(
        request,
        "admin_dashboard/event_management.html",
        {
            "section": "events",
            "section_title": "일정 관리",
            "events": events,
            "q": q,
            "event_count": events.count(),
        },
    )


@_require_admin
def poll_management(request):
    q = request.GET.get("q", "").strip()
    now = timezone.now()

    queryset = Poll.objects.select_related("created_by").annotate(
        participant_count=Count("votes", distinct=True),
    ).order_by("-created_at")
    if q:
        queryset = queryset.filter(question__icontains=q)

    active_polls = queryset.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    closed_polls = queryset.filter(expires_at__lte=now).exclude(expires_at__isnull=True)

    return render(
        request,
        "admin_dashboard/poll_management.html",
        {
            "section": "polls",
            "section_title": "투표 관리",
            "q": q,
            "active_polls": active_polls,
            "closed_polls": closed_polls,
        },
    )


@_require_admin
def survey_management(request):
    q = request.GET.get("q", "").strip()
    now = timezone.now()

    queryset = Survey.objects.select_related("created_by").annotate(
        response_count=Count("responses", distinct=True),
        question_count=Count("questions"),
    ).order_by("-created_at")
    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))

    active_surveys = queryset.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    closed_surveys = queryset.filter(expires_at__lte=now).exclude(expires_at__isnull=True)

    return render(
        request,
        "admin_dashboard/survey_management.html",
        {
            "section": "surveys",
            "section_title": "설문조사 관리",
            "q": q,
            "active_surveys": active_surveys,
            "closed_surveys": closed_surveys,
        },
    )


@_require_admin
def user_management(request):
    q = request.GET.get("q", "").strip()
    users = User.objects.all().order_by("-date_joined")
    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(display_name__icontains=q)
        )

    return render(
        request,
        "admin_dashboard/user_management.html",
        {
            "section": "users",
            "section_title": "사용자 관리",
            "users": users,
            "q": q,
            "user_count": users.count(),
        },
    )


@_require_admin
@require_POST
def user_action(request):
    user_id = request.POST.get("user_id")
    action = request.POST.get("action", "")
    next_url = _safe_redirect_to_admin_users(request)
    target = get_object_or_404(User, id=user_id) if user_id else None

    if target is None:
        messages.error(request, "대상 사용자가 없습니다.")
        return redirect(next_url)

    if action == "set_role":
        role = request.POST.get("role", "").strip()
        if role not in dict(User.Role.choices):
            messages.error(request, "유효하지 않은 역할입니다.")
        else:
            if target.pk == request.user.pk and role == User.Role.USER and not target.is_superuser:
                messages.error(request, "본인 계정은 ADMIN에서 바로 USER로 변경할 수 없습니다.")
            else:
                target.role = role
                if not target.is_superuser:
                    target.is_staff = role == User.Role.ADMIN
                target.save(update_fields=["role", "is_staff"])
                messages.success(
                    request,
                    f"{target.username}의 역할을 {target.get_role_display()}로 변경했습니다.",
                )

    elif action == "toggle_status":
        if target.pk == request.user.pk and target.is_active:
            messages.error(request, "현재 로그인 중인 계정은 비활성화할 수 없습니다.")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            state_label = "활성화" if target.is_active else "비활성화"
            messages.success(request, f"{target.username} 계정을 {state_label}했습니다.")
    else:
        messages.error(request, "지원하지 않는 동작입니다.")

    return redirect(next_url)


@_require_admin
def system_management(request):
    return render(
        request,
        "admin_dashboard/system_management.html",
        {
            "section": "system",
            "section_title": "시스템 관리",
            "section_description": "기본 설정 관리와 백업 도구 확장을 위한 영역입니다.",
        },
    )
