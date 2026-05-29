# TCD (Technical Context Document)

## 1. 프로젝트 기술 배경
Vibe Community는 Django 기반 단일 모놀리식 구조를 채택한다. 
백엔드/템플릿 렌더링을 한 레포에서 운영하고, 보안과 유지보수성을 우선으로 잡는다.

## 2. 선정 스택
### Frontend
- Django Templates
- Tailwind CSS(CDN, 추후 django-tailwind로 빌드 확장)

### Backend
- Django 5.2.4(LTS)
- Django ORM
- django-allauth (인증)
- django-htmx (부분적 비동기 상호작용)
- django-crispy-forms (폼 스타일링 보조)

### Database
- SQLite (개발/초기 운영)
- PostgreSQL 전환 경로 확보

### Auth/Security
- 세션 기반 인증
- bcrypt 계열 해시(유저 패스워드 정책)
- CSRF 방어, Rate limit, 보안 헤더

### Testing
- Django TestCase 우선
- (필요시) Playwright E2E

## 3. 코딩 철학
1. **도메인 우선 설계**
   - 권한, 유효성, 감사로그가 기능의 핵심이다.
   - 기능은 `app` 단위로 분리하여 점진적으로 확장한다.

2. **입력 경계 수비**
   - 외부 입력은 Form/Serializer/모델 검증을 통과 후 비즈니스 로직 진입.
   - 동작별 권한 검사와 에러 경로를 명시한다.

3. **보안 우선**
   - 인증/권한은 UI 가시성 제어가 아니라 서버에서 강제.
   - 조작 가능성이 높은 동작은 로그를 남긴다.

4. **작은 순환, 자주 배포**
   - 핵심 기능부터 순차 구현하고, 각 단계별 검증 후 다음 기능을 추가.

## 4. 패턴
### 4.1 아키텍처 패턴
- **Layered Architecture:**
  - `views.py` (요청 바인딩)
  - `services/` (프로젝트 레벨로 분리 가능)
  - `models.py` (데이터)
  - `admin.py` (운영자 인터페이스)

### 4.2 데이터 패턴
- 모든 쓰기 동작은 트랜잭션 경계 하에서 수행
- 중복 동작 방지: 유니크 제약 및 적절한 인덱스 활용
- 소프트딜리트/하드딜리트 정책을 명확히 구분

## 5. 기술 의사결정 근거
- Django는 인증/권한/관리자 콘솔이 내장되어 있고 코드량을 줄여 빠른 MVP 구현이 가능하다.
- Tailwind CDN은 초기엔 간단하게 시작하고, 추후 빌드 시스템 연동으로 확장한다.
- SQLite는 초기 비용이 낮고, WAL+busy_timeout으로 운영 초기 동시성 개선이 가능하다.

## 6. 확장 포인트
- 알림 모듈(이메일/푸시) 추가
- 실시간 댓글/알림(SSE/WebSocket)
- 검색(全文텍스트), 추천/랭킹, 신고 자동 판별 정책
