# DD (Database Design)

## 1. 설계 목표
- Django ORM 기준으로 핵심 도메인(User, Notice, Post, Event, Poll, Survey, 관리자 통계) 중심의 명확한 정합성 보장
- SQLite 기반 운영에서 제약조건·인덱스·잠금 정책을 우선 설정하고, PostgreSQL 이전이 쉬운 스키마 유지
- 커뮤니티 운영에서 자주 접근되는 목록/조회 경로를 우선적으로 인덱싱

## 2. ERD 개요
- `accounts.User` 1:N `notices.Notice`, `posts.Post`, `events.Event`, `polls.Poll`, `surveys.Survey`, `admin_dashboard.DashboardStat`, 댓글(`posts.PostComment`), 투표(`polls.PollVote`)
- `posts.Post` 1:N `posts.PostComment`, `posts.PostComment`는 self-relation 대댓글
- `polls.Poll` 1:N `polls.PollOption`, `polls.PollVote`
- `surveys.Survey` 1:N `surveys.SurveyQuestion`, `surveys.SurveyQuestion` 1:N `surveys.SurveyChoice`, `surveys.SurveyResponse`
- `events.Event`는 캘린더 렌더링용 기간 쿼리를 위한 시간 인덱스 적용

## 3. Django 모델 스키마 (핵심 필드)

```python
# accounts/models.py
class User(AbstractUser):
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True, max_length=1200)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/%d", null=True, blank=True)
```

```python
# notices/models.py
class Notice(models.Model):
    author = ForeignKey(User)
    title = CharField(max_length=160)
    content = TextField()
    is_pinned = BooleanField(default=False)
    is_published = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    class Meta:
        indexes = [Index(fields=["is_pinned", "is_published", "created_at"])]
```

```python
# posts/models.py
class Post(models.Model):
    author = ForeignKey(User)
    title = CharField(max_length=180)
    content = TextField()
    image = ImageField(blank=True, null=True)
    view_count = PositiveIntegerField(default=0)
    is_deleted = BooleanField(default=False)
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(auto_now=True)
    class Meta:
        indexes = [Index(fields=["author", "created_at"]), Index(fields=["is_deleted", "created_at"])]

class PostComment(MPTTModel):
    post = ForeignKey(Post)
    author = ForeignKey(User)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    content = TextField()
    is_deleted = BooleanField(default=False)
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(auto_now=True)
    class Meta:
        indexes = [Index(fields=["post", "parent", "created_at"])]
```

```python
# events/models.py
class Event(models.Model):
    CATEGORY_CHOICES = [("GENERAL", "일반"), ("NOTICE", "공지"), ("MEETING", "회의"), ("CAMP", "행사")]
    title = CharField(max_length=140)
    description = TextField(blank=True)
    category = CharField(max_length=20, choices=CATEGORY_CHOICES)
    start_at = DateTimeField()
    end_at = DateTimeField()
    is_all_day = BooleanField(default=False)
    is_published = BooleanField(default=True)
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(auto_now=True)
    class Meta:
        indexes = [Index(fields=["start_at", "end_at"])]
```

```python
# polls/models.py
class Poll(models.Model):
    title = CharField(max_length=160)
    description = TextField(blank=True)
    is_multiple = BooleanField(default=False)
    is_anonymous = BooleanField(default=False)
    starts_at = DateTimeField(default=timezone.now)
    ends_at = DateTimeField(null=True, blank=True)
    author = ForeignKey(User)

class PollOption(models.Model):
    poll = ForeignKey(Poll, related_name="options")
    text = CharField(max_length=120)
    order = PositiveIntegerField(default=0)
    class Meta:
        ordering = ["order"]
        unique_together = ("poll", "text")

class PollVote(models.Model):
    poll = ForeignKey(Poll, related_name="votes")
    option = ForeignKey(PollOption, related_name="votes")
    voter = ForeignKey(User, null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("poll", "voter")
```

```python
# surveys/models.py
class Survey(models.Model):
    title = CharField(max_length=160)
    target_audience = CharField(max_length=80, blank=True)
    created_by = ForeignKey(User)
    is_published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

class SurveyQuestion(models.Model):
    survey = ForeignKey(Survey, related_name="questions")
    text = CharField(max_length=240)
    order = PositiveIntegerField(default=0)

class SurveyChoice(models.Model):
    question = ForeignKey(SurveyQuestion, related_name="choices")
    text = CharField(max_length=160)

class SurveyResponse(models.Model):
    question = ForeignKey(SurveyQuestion, related_name="responses")
    choice = ForeignKey(SurveyChoice, null=True, blank=True, related_name="responses")
    respondent = ForeignKey(User)
    text_answer = TextField(blank=True)
    submitted_at = DateTimeField(auto_now_add=True)
```

```python
# admin_dashboard/models.py
class DashboardStat(models.Model):
    name = CharField(max_length=80, unique=True)
    value = BigIntegerField(default=0)
    updated_at = DateTimeField(auto_now=True)
```

## 4. 인덱스 전략
- 목록 노출/정렬 빈도 기준 인덱스 적용
  - `Notice(author_id, is_pinned, is_published, created_at)`
  - `Post(author_id, created_at DESC)`
  - `Post(is_deleted, created_at DESC)`
  - `PostComment(post_id, parent_id, created_at)`
  - `PostComment.tree_id/lft` (MPTT 기본)
  - `Event(start_at, end_at)`
  - `Poll(author_id, starts_at)`
  - `PostComment(post_id, created_at)`
  - `Survey(created_by_id, created_at)`
- 중복 방지 제약
  - 댓글은 `PostComment` parent-tree 기본 무결성 + soft-delete 정책으로 관리
  - `PollVote(poll_id, voter_id)` 유일성(`unique_together`)으로 동일 회원 중복투표 차단

## 5. SQLite 성능/안정성 반영
- `django.db.backends.sqlite3` 옵션
  - `timeout=20.0`
  - `isolation_level="IMMEDIATE"`
  - `check_same_thread=False`
- 연결 생성 시 PRAGMA
  - `journal_mode=WAL`
  - `synchronous=NORMAL`
  - `temp_store=MEMORY`
  - `busy_timeout=20000`
  - `foreign_keys=ON`
  - `wal_autocheckpoint=1000`
- 전환 시 고려
  - PostgreSQL 변경 시 `BigAutoField`, FK, 복합인덱스/유니크 제약은 유사하게 이식 가능
  - 필요 시 텍스트 검색은 PostgreSQL `trigram`/전용 검색 인덱스로 이전
