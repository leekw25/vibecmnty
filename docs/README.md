# Vibe Community

## 1. 프로젝트 비전
Vibe Community는 작은 커뮤니티 운영자가 쉽고 빠르게 운영할 수 있는 웹 커뮤니티 플랫폼이다.  
목표는 **공지/소통/일정/투표/회원관리/관리자 운영**의 전 과정을 하나의 시스템 안에서 처리하고, 초기에는 가볍게 시작해도 운영량이 늘면 안정적으로 확장되는 구조를 갖추는 것이다.

## 2. 핵심 설계 방향
- **프레임워크:** Django 5.2.4(LTS)
- **UI:** Tailwind CSS(CDN 기반, 추후 django-tailwind 빌드 확장)
- **데이터베이스:** SQLite (초기) → PostgreSQL 전환 가능
- **ORM:** Django ORM
- **인증:** allauth + Django Auth(User)
- **보안 원칙:** 입력 검증, 권한 검사, CSRF/Rate limit, 감사 로그

## 3. 프로젝트 현 상태(요구사항 반영 상태)
현재 단계는 설계 산출물 기반으로 Django 프로젝트 골격을 구축한 상태다. 
이미지 업로드, 게시판, 일정, 투표, 인증, 관리자 기능의 핵심 앱을 생성했으며,
아래 순서로 기능 구현을 진행한다.

1. 인증/권한/사용자 관리
2. 공지사항
3. 소통 게시판(댓글/좋아요/조회수)
4. 일정 캘린더
5. 투표
6. 설문/확장
7. 관리자 대시보드
8. 보안 가드 강화 및 테스트 확장

## 4. 핵심 데이터 도메인
- User (커스텀 User)
- Notice
- Post / PostComment
- Event
- Poll / PollOption / PollVote
- Survey / SurveyQuestion / SurveyChoice / SurveyResponse
- DashboardStat (관리자 확장용)

## 5. 기본 운영 규칙
- 기본 원칙: “작게 만들고, 빨리 확장”  
- 핵심 기능에 대한 인덱스 우선 설계
- 관리자 기능은 일반 사용자 기능보다 항상 상위 권한 정책 적용

## 6. 문서 목록
이 저장소는 아래 실행 가능한 문서들을 기반으로 운영한다.
- PRD.md: 제품 요구사항
- TCD.md: 기술 문맥/코딩 철학
- DP.md: UI/UX 디자인 원칙
- CBP.md: 코딩 표준·개발 규칙·TDD 방식
- TR.md: 테스트 리포트
- US.md: 사용자 스토리
- SA.md: 시스템 구조
- DD.md: 데이터베이스 설계

## 7. 시작 가이드(초안)
- Python 가상환경 생성 후 `pip install -r requirements.txt`
- `.env`에 시크릿 값(SECRET_KEY 등) 분리 관리
- `python manage.py migrate` 후 슈퍼유저 생성
- `python manage.py runserver`로 초기 라우팅 확인
- 관리자 인증/권한/메인 URL 부터 단계적으로 구현
