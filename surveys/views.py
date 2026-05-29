from __future__ import annotations

import json
from collections import Counter
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import QuestionForm, QuestionFormSet, SurveyForm
from .models import Answer, Question, Response, Survey


def _is_admin_user(user) -> bool:
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or getattr(user, "is_admin_member", False)
    )


def _admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _is_admin_user(request.user):
            raise PermissionDenied("Admin permission is required.")
        return view_func(request, *args, **kwargs)

    return wrapper


def _parse_scale(value: str | int | None) -> int | None:
    try:
        num = int(value)
    except (TypeError, ValueError):
        return None
    return num if 1 <= num <= 5 else None


def _normalize_answer(question: Question, raw_input: str | list[str] | None) -> str:
    if question.question_type == Question.Type.SCALE:
        score = _parse_scale(raw_input)
        return "" if score is None else str(score)

    if question.question_type == Question.Type.MULTIPLE:
        values = raw_input or []
        if isinstance(values, str):
            values = [v.strip() for v in values.split(",") if v.strip()]
        values = [v.strip() for v in values if str(v).strip()]
        if not values:
            return ""
        return json.dumps(values, ensure_ascii=False)

    return str(raw_input or "").strip()


def _build_results(survey: Survey) -> dict:
    questions = list(survey.questions.all())
    total_respondents = survey.responses.count()
    blocks = []

    for q in questions:
        answers = q.answers.select_related("response__respondent").all()
        records = []
        chart = []
        summary = None

        if q.question_type in {Question.Type.CHOICE, Question.Type.MULTIPLE}:
            counter = Counter()
            option_set = {str(v) for v in (q.options or [])}
            for answer in answers:
                if q.question_type == Question.Type.MULTIPLE:
                    try:
                        selected = json.loads(answer.answer_text or "[]")
                    except json.JSONDecodeError:
                        selected = []
                    for item in selected:
                        counter[str(item).strip()] += 1
                else:
                    counter[(answer.answer_text or "").strip()] += 1
            denom = total_respondents or 1
            chart = []
            for choice in q.options or []:
                cnt = counter.get(str(choice), 0)
                chart.append(
                    {
                        "label": str(choice),
                        "count": cnt,
                        "rate": round((cnt / denom) * 100, 1),
                    }
                )
            for choice, cnt in counter.items():
                if str(choice) not in option_set:
                    chart.append(
                        {
                            "label": choice,
                            "count": cnt,
                            "rate": round((cnt / denom) * 100, 1),
                        }
                    )

        elif q.question_type == Question.Type.SCALE:
            buckets = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            scores = []
            for answer in answers:
                score = _parse_scale(answer.answer_text)
                if score is not None:
                    scores.append(score)
                    buckets[score] += 1
            total_scores = len(scores) or 1
            avg = round(sum(scores) / total_scores, 2) if scores else 0.0
            chart = [
                {
                    "label": str(score),
                    "count": cnt,
                    "rate": round((cnt / total_scores) * 100, 1),
                }
                for score, cnt in buckets.items()
            ]
            summary = {
                "label": "Average score",
                "value": avg,
                "count": len(scores),
            }

        elif q.question_type in {Question.Type.TEXT, Question.Type.TEXTAREA}:
            for answer in answers:
                records.append(
                    {
                        "answer": answer.answer_text,
                        "user": (
                            None
                            if survey.is_anonymous
                            else answer.response.respondent.username
                        ),
                    }
                )
        else:
            for answer in answers:
                raw = answer.answer_text
                if q.question_type == Question.Type.MULTIPLE:
                    try:
                        values = json.loads(raw or "[]")
                    except json.JSONDecodeError:
                        values = []
                    display = ", ".join([str(v) for v in values]) if values else ""
                else:
                    display = raw
                records.append(
                    {
                        "answer": display,
                        "user": (
                            None
                            if survey.is_anonymous
                            else answer.response.respondent.username
                        ),
                    }
                )

        blocks.append(
            {
                "question": q,
                "chart": chart,
                "records": records,
                "summary": summary,
            }
        )

    return {
        "question_blocks": blocks,
        "total_respondents": total_respondents,
        "is_anonymous": survey.is_anonymous,
    }


def survey_list(request: HttpRequest) -> HttpResponse:
    now = timezone.now()
    base = (
        Survey.objects.prefetch_related("questions")
        .annotate(
            response_count=Count("responses", distinct=True),
            question_count=Count("questions"),
        )
    )
    active_surveys = base.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    ended_surveys = base.filter(expires_at__lte=now).exclude(expires_at__isnull=True)

    return render(
        request,
        "surveys/list.html",
        {
            "active_surveys": active_surveys,
            "ended_surveys": ended_surveys,
            "is_admin": _is_admin_user(request.user),
            "now": now,
        },
    )


def survey_respond(request: HttpRequest, pk: int) -> HttpResponse:
    survey = get_object_or_404(Survey.objects.prefetch_related("questions"), pk=pk)
    questions = list(survey.questions.all())

    if survey.expires_at and survey.expires_at <= timezone.now():
        messages.error(request, "This survey has already ended.")
        return redirect("surveys:list")

    if not request.user.is_authenticated:
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    if Response.objects.filter(survey=survey, respondent=request.user).exists():
        messages.info(request, "You already submitted this survey.")
        return redirect("surveys:list")

    if request.method == "POST":
        answer_map: dict[int, str] = {}
        has_error = False

        for question in questions:
            field_name = f"answer_{question.id}"
            if question.question_type == Question.Type.MULTIPLE:
                raw_value = request.POST.getlist(field_name)
            else:
                raw_value = request.POST.get(field_name)

            normalized = _normalize_answer(question, raw_value)

            if question.required and not normalized:
                has_error = True
                messages.error(
                    request,
                    f"Required question is missing: {question.text}",
                )

            if question.question_type == Question.Type.SCALE and normalized:
                if _parse_scale(normalized) is None:
                    has_error = True
                    messages.error(request, f"Invalid scale value for: {question.text}")

            answer_map[question.id] = normalized

        if not has_error:
            try:
                with transaction.atomic():
                    response = Response.objects.create(
                        survey=survey,
                        respondent=request.user,
                    )
                    for question in questions:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            answer_text=answer_map[question.id],
                        )
            except IntegrityError:
                messages.error(request, "This survey already has your response.")
            else:
                messages.success(request, "Survey submitted successfully.")
                return redirect("surveys:list")

    return render(
        request,
        "surveys/survey.html",
        {
            "survey": survey,
            "questions": questions,
            "question_types": Question.Type,
            "total_questions": len(questions),
            "is_create": False,
        },
    )


@login_required
@_admin_required
def survey_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        survey_form = SurveyForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix="question")

        if survey_form.is_valid() and question_formset.is_valid():
            question_payloads = [
                qf
                for qf in question_formset.cleaned_data
                if not qf.get("DELETE", False) and qf.get("text")
            ]

            if not question_payloads:
                messages.error(request, "At least one question is required.")
            else:
                survey = survey_form.save(commit=False)
                survey.created_by = request.user
                survey.save()

                for i, qf in enumerate(question_payloads):
                    Question.objects.create(
                        survey=survey,
                        text=qf["text"],
                        question_type=qf["question_type"],
                        required=bool(qf.get("required", True)),
                        options=qf.get("options", []),
                        order=i,
                    )

                messages.success(request, "Survey created.")
                return redirect("surveys:list")
    else:
        survey_form = SurveyForm()
        question_formset = QuestionFormSet(prefix="question")

    return render(
        request,
        "surveys/survey.html",
        {
            "title": "Create Survey",
            "survey_form": survey_form,
            "question_formset": question_formset,
            "is_create": True,
            "question_types": Question.Type,
        },
    )


@login_required
@_admin_required
def survey_results(request: HttpRequest, pk: int) -> HttpResponse:
    survey = get_object_or_404(Survey.objects.prefetch_related("questions"), pk=pk)
    return render(
        request,
        "surveys/results.html",
        {
            "survey": survey,
            "result": _build_results(survey),
        },
    )
