# tasks.md

## [최초 기록] - 컨텍스트 정합성 점검
- 담당자: AI (Codex)
- 소요시간: 0.5h vs 0.5h
- 구현 기능: 없음 (요구사항/아키텍처 문서 정독, 실행 전 컨텍스트 정합성 점검)
- 테스트 결과: 해당 없음(코드 구현 전)
- 배운 점: 핵심 요구사항은 공지·소통·일정·투표·회원·관리자 기능이 MVP로 명확함.
- 어려웠던 점: 이전 산출물의 Next/Prisma 기반 표현과 현재 Django 전환 요구의 정합성 필요성
- 개선 아이디어: 핵심 스택 정합성 문서 갱신 후 구현
- 이슈 및 해결: `docs/START.md` 누락 확인 후 생성
- 다음 작업: Django 기반 프로젝트 골격 생성

## [2026-05-15] - Django 5.2.4 프로젝트 초기 뼈대 구성
- 담당자: AI
- 소요시간: 1.5h vs 1.0h
- 구현 기능: 7개 앱 생성, Django settings/urls 구성, Tailwind CDN 템플릿, SQLite PRAGMA 튜닝, 기본 모델·뷰·템플릿 뼈대 구성
- 테스트 결과: `python -m py_compile` 전체 모듈 통과
- 배운 점: Prisma 연동은 Django 전환으로 제외되고 SQLite 튜닝은 connection_created signal + IMMEDIATE isolation로 구현
- 어려웠던 점: `docs/START.md` 누락, allauth 기본 템플릿 의존성에 대한 초기 정합성
- 개선 아이디어: 인증/회원가입 플로우 보강, 좋아요·댓글·투표 write API 트랜잭션 강화, 테스트 추가
- 이슈 및 해결: `docs/START.md` 부재 → 신규 추가 후 작업 재개
- 다음 작업: 마이그레이션 생성/실행, 관리자 계정 구성, 핵심 기능 CRUD 구현

## [2026-05-15] - 인증/권한 기능 보강
- 담당자: AI (Codex)
- 소요시간: 0.8h vs 0.8h
- 구현 기능:
  - 회원가입/로그인/로그아웃 흐름 최적화 (django-allauth 기반)
  - `User.role` 기반 `USER`, `ADMIN` 권한체계 정리 및 프로필 편집 연동
  - `/signup` 직후 `/accounts:profile` 자동 이동
  - 프로필 수정(`profile_form`), 비밀번호 변경(`password_change`) 기능 추가
  - 관리자 비권한 진입 차단 UX 및 메시지 처리 강화
- 테스트 결과: `python manage.py check`, `python manage.py test accounts` (4/4 pass), 엔드포인트 상태 코드 확인
- 배운 점: allauth 뷰 상속 시 success URL/메시지 동작은 최소 변경으로 안정적으로 유지 가능
- 어려웠던 점: 테스트 환경에서 이미지 업로드 유효성 검증을 통과하려면 실제 이미지 바이너리 생성 필요
- 개선 아이디어: `Account` 연계 2차 인증, 비밀번호 정책 강화, 관리자 전용 대시보드 데이터 캐싱
- 이슈 및 해결: 회원가입 후 자동 로그인 동작은 allauth 기본 동작 + `get_success_url`로 처리
- 다음 작업: 공지/게시글/댓글/투표 기능의 핵심 CRUD에 인증/권한 테스트 범위 확장

## [2026-05-15] - 글/일정 등록 기능 구현
- 담당자: AI (Codex)
- 소요시간: 1.0h vs 1.0h
- 구현 기능:
  - `posts` 글 생성/수정/삭제 기능 추가 및 라우팅/템플릿 정비
  - `events` 일정 생성/수정/삭제 기능 추가, 관리자 전용 권한 제한 적용
  - 글 상세 조회수 자동 증가 및 작성자/관리자 권한 기반 수정·삭제 제어
  - 폼(`posts/forms.py`, `events/forms.py`) 및 CRUD 템플릿 추가
- 테스트 결과: `python manage.py check`, `python manage.py test posts events` (6/6 pass)
- 배운 점: 조회 전용 화면에서 쓰기 기능으로 확장할 때 인증 경로와 액션 버튼을 동시에 반영해야 UX 단절이 없다
- 어려웠던 점: 기존 템플릿 한글 인코딩 깨짐 상태에서 안전한 영문 UI 텍스트로 정리
- 개선 아이디어: 이벤트 반복 일정/월간 캘린더 뷰, Soft-delete 목록 필터, 알림 연동
- 이슈 및 해결: 일정/게시글 생성 시 권한 우선 분기 부재를 해결하고 메시지 피드백을 일괄화
- 다음 작업: 댓글(대댓글), 좋아요·조회수 정책, Poll/Survey 연동

## [2026-05-15] - ALLOWED_HOSTS 안정화
- 담당자: AI (Codex)
- 소요시간: 0.1h vs 0.1h
- 구현 기능:
  - `DEBUG` 환경에서 호스트 관련 400/비정상 응답 방지를 위해 `DJANGO_ALLOWED_HOSTS` 환경변수 기반 설정 + 기본 로컬 허용값 적용
- 테스트 결과: `python manage.py check`

## [2026-05-15] - Poll 등록 기능 보강
- 담당자: AI (Codex)
- 소요시간: 0.8h vs 0.8h
- 구현 기능:
  - `polls`에 등록 뷰/폼/템플릿/라우팅 추가 (`/polls/create/`)
- 권한: 관리자(ADMIN)만 작성 허용, 일반 사용자는 생성 시 리다이렉트
- 폼셋으로 투표 항목 최소 2개 이상 입력 강제
- `polls` 목록에 생성 버튼 추가
- 테스트 결과: `python manage.py test polls` (3/3), `python manage.py test accounts posts events polls` (13/13)

## [2026-05-15] - 관리자 계정 생성
- 담당자: AI (Codex)
- 소요시간: 0.1h vs 0.1h
- 구현 기능:
  - 테스트용 슈퍼유저 계정 `admin` 생성 및 `User.role = ADMIN`, `is_staff=True`, `is_superuser=True`로 설정
- 테스트 결과: 관리자 계정 존재 여부 확인
- 배운 점: 일반 사용자 대비 관리자 판별은 `is_admin_member`/`admin_required` 유틸과 호환되어 즉시 접근 제어에 반영됨
- 다음 작업: 기본 관리자 계정의 비밀번호 초기화 가이드 문서화(운영 전용)
