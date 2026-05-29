# START

## 실행 전 확인 체크리스트
- PRD / README / TCD / DP / CBP / TR / SA / DD 검토 완료
- docs/tasks.md의 이전 기록 확인
- `docs/troubleshooting.md` 존재 확인

## 현재 스택
- Django 5.2.4 기반 커뮤니티 프로젝트
- 앱: accounts, notices, posts, events, polls, surveys, admin_dashboard
- DB: SQLite (웹 운영용 PRAGMA 최적화 적용)

## 공통 실행 원칙
- 하나의 기능 단위만 수정
- 권한/입력 검증 우선
- 테스트 없는 동작 변경 금지
- 문서화 후 다음 단계 진행
