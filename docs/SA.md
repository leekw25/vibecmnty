# SA (System Architecture)

## 1. 전체 시스템 구조
커뮤니티 시스템은 단일 Django 애플리케이션 안에서 UI, 인증, 배치 로직을 운용한다.

```text
Browser
  ↓ HTTPS
Django Project (Templates + Views)
  ↓ Django ORM
SQLite DB (초기) / PostgreSQL (확장)
  ↓
Object Storage (이미지 업로드, 추후 분리)
```

## 2. 주요 계층
- **Presentation Layer:** 페이지, 폼, 카드, 목록 UI
- **Application Layer:** URL/뷰(요청 매핑, 인증 검사)
- **Domain Layer:** 비즈니스 규칙 수행
- **Data Layer:** Django ORM을 통한 DB 접근

## 3. 데이터 흐름
### 게시글 작성
1. 사용자가 `/posts/`에서 글을 작성
2. 폼/모델 검증 수행
3. 인증/권한 체크
4. 비즈니스 규칙(삭제 금지어, 길이 제한, 첨부 유효성) 처리
5. DB 저장 후 ID 반환
6. UI 리다이렉트/재검증

### 조회수/좋아요
1. 상세 페이지 조회 요청
2. 서버에서 인증 토큰 유무로 조회 정책 분기(비로그인은 캐시 조회 허용 정책 적용)
3. 조회수 증가 로직: 동시성 충돌 완화를 위해 DB 트랜잭션/락 전략 적용
4. 좋아요는 사용자-게시글 유니크 제약으로 중복 차단

### 투표 처리
1. 사용자가 투표 제출
2. 마감일/중복/권한 검증
3. 트랜잭션으로 `vote` + 집계 처리
4. 결과 반영 및 집계 응답 반환

## 4. 보안 경로
- 모든 write 동작은 인증 미들웨어 통과 필요
- 관리자 라우트는 role 기반 접근제어 추가
- 파일 업로드 파이프라인: MIME + 확장자 + 용량 검사
- 사용자 제공 문자열은 서버에서 escape/정규화

## 5. 운영 구조
- 정적 자산: CDN/정적 호스팅 연결 고려
- 로그: 앱 로그 + 감사 로그 분리
- 장애 시나리오: 업로드 오류 시 글 작성은 실패하지 않도록 첨부 선택적 저장

## 6. 확장 아키텍처
- 장기적 분리안:
  - API 분리(관리자/일반 사용자), Upload Service 분리
  - WebSocket 기반 실시간 알림 채널
  - 검색 전용 서비스(Elasticsearch/MeiliSearch)
