from __future__ import annotations

from django.shortcuts import render


def custom_permission_denied(request, exception=None):
    if not request.user.is_authenticated:
        message = "로그인이 필요합니다."
        help_text = "비회원은 관리자 페이지에 접근할 수 없습니다."
    else:
        message = "관리자 권한이 필요합니다."
        help_text = "현재 계정은 관리자 기능을 사용할 권한이 없습니다."

    return render(
        request,
        "403.html",
        {
            "exception": exception,
            "message": message,
            "help_text": help_text,
        },
        status=403,
    )

