from __future__ import annotations

from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Comment, Like, Post


def _is_admin_user(user) -> bool:
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or getattr(user, "is_admin_member", False)
    )


def _can_edit_obj(user, obj_author) -> bool:
    if not user.is_authenticated:
        return False
    return user == obj_author or _is_admin_user(user)


def _ensure_commenter(user, comment: Comment) -> None:
    if not _can_edit_obj(user, comment.author):
        raise PermissionDenied("Permission denied.")


def _ensure_poster(user, post: Post) -> None:
    if not _can_edit_obj(user, post.author):
        raise PermissionDenied("Permission denied.")


def _build_comment_threads(comments: list[Comment]) -> list[Comment]:
    comment_lookup: dict[int, Comment] = {comment.id: comment for comment in comments}
    children: dict[int, list[Comment]] = defaultdict(list)
    roots: list[Comment] = []

    for comment in comments:
        if comment.parent_id and comment.parent_id in comment_lookup:
            children[comment.parent_id].append(comment)
        else:
            roots.append(comment)

    ordered: list[Comment] = []

    def visit(comment: Comment, depth: int) -> None:
        comment.depth = depth
        ordered.append(comment)
        for child in children.get(comment.id, []):
            visit(child, depth + 1)

    for root in roots:
        visit(root, 0)

    return ordered


def _register_post_view_once(request, post: Post) -> None:
    viewed_ids = request.session.get("viewed_post_ids", [])
    if not isinstance(viewed_ids, list):
        viewed_ids = list(viewed_ids)

    if post.id not in viewed_ids:
        Post.objects.filter(id=post.id).update(views=F("views") + 1)
        viewed_ids.append(post.id)
        viewed_ids = viewed_ids[-200:]
        request.session["viewed_post_ids"] = viewed_ids
        request.session.modified = True


def _detail_context(request, post: Post) -> dict:
    comment_form = CommentForm()
    comment_qs = list(
        Comment.objects.filter(post=post).select_related("author").order_by("created_at")
    )
    comment_tree = _build_comment_threads(comment_qs)

    user = request.user
    for comment in comment_tree:
        comment.can_edit = _can_edit_obj(user, comment.author)

    user_liked = False
    if user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=user).exists()

    return {
        "post": post,
        "comment_form": comment_form,
        "comments": comment_tree,
        "comment_count": len(comment_tree),
        "likes_count": post.likes.count(),
        "user_liked": user_liked,
    }


def post_list(request):
    q = request.GET.get("q", "").strip()
    qs = Post.objects.select_related("author").annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
    )
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    qs = qs.order_by("-created_at")
    paginator = Paginator(qs, 15)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    return render(
        request,
        "posts/list.html",
        {
            "page_obj": page_obj,
            "q": q,
        },
    )


def post_detail(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    _register_post_view_once(request, post)
    post.refresh_from_db(fields=["views"])

    context = _detail_context(request, post)
    context["can_edit"] = _can_edit_obj(request.user, post.author)
    return render(request, "posts/detail.html", context)


@login_required(login_url="/login/")
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "게시글이 등록되었습니다.")
            return redirect("posts:detail", pk=post.pk)
    else:
        form = PostForm()

    return render(
        request,
        "posts/form.html",
        {
            "title": "글쓰기",
            "form": form,
            "submit_label": "등록",
        },
    )


@login_required(login_url="/login/")
def post_update(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    _ensure_poster(request.user, post)

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "게시글이 수정되었습니다.")
            return redirect("posts:detail", pk=post.pk)
    else:
        form = PostForm(instance=post)

    return render(
        request,
        "posts/form.html",
        {
            "title": "게시글 수정",
            "form": form,
            "submit_label": "저장",
            "cancel_url": f"/posts/{post.pk}/",
        },
    )


@login_required(login_url="/login/")
@require_POST
def post_delete(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    _ensure_poster(request.user, post)

    post.delete()
    messages.success(request, "게시글이 삭제되었습니다.")
    return redirect("posts:list")


@login_required(login_url="/login/")
@require_POST
def post_toggle_like(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)

    try:
        with transaction.atomic():
            like, created = Like.objects.get_or_create(post=post, user=request.user)
            if not created:
                like.delete()
            else:
                pass
    except IntegrityError:
        Like.objects.filter(post=post, user=request.user).delete()

    context = {
        "post": post,
        "likes_count": post.likes.count(),
        "user_liked": Like.objects.filter(post=post, user=request.user).exists(),
    }

    return render(request, "posts/partials/like_button.html", context)


@login_required(login_url="/login/")
@require_POST
def post_comment_create(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    parent_id = request.POST.get("parent_id") or ""

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        if parent_id:
            parent = Comment.objects.filter(pk=parent_id, post=post).first()
            comment.parent = parent
        comment.save()

    return render(
        request,
        "posts/partials/comment_section.html",
        _detail_context(request, post),
    )


@login_required(login_url="/login/")
def post_comment_update(request, post_id: int, comment_id: int):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    _ensure_commenter(request.user, comment)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "댓글이 수정되었습니다.")
            return redirect("posts:detail", pk=post.pk)
    else:
        form = CommentForm(instance=comment)

    return render(
        request,
        "posts/comment_form.html",
        {
            "title": "댓글 수정",
            "form": form,
            "post": post,
            "comment": comment,
            "submit_label": "수정",
            "cancel_url": f"/posts/{post.pk}/",
        },
    )


@login_required(login_url="/login/")
@require_POST
def post_comment_delete(request, post_id: int, comment_id: int):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    _ensure_commenter(request.user, comment)

    comment.delete()

    return render(
        request,
        "posts/partials/comment_section.html",
        _detail_context(request, post),
    )
