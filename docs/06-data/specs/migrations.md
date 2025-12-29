# 마이그레이션 가이드 (Migrations)

## 1. Alembic 설정

### 1.1 Alembic이란?

- **데이터베이스 마이그레이션 도구**
- SQLAlchemy ORM과 연동
- 버전 관리 기능 제공
- Rollback 지원

### 1.2 초기 설정

**디렉토리 구조**:
```
apps/api/
├── alembic/
│   ├── versions/          # 마이그레이션 파일들
│   ├── env.py             # Alembic 환경 설정
│   ├── script.py.mako     # 마이그레이션 템플릿
│   └── ini                # Alembic 설정 파일
└── alembic.ini            # 최상위 설정 (선택)
```

### 1.3 env.py 설정

**핵심 설정**:
```python
# alembic/env.py

from sqlalchemy import engine_from_config, pool
from alembic import context

# SQLAlchemy 모델 임포트
from app.db.base import Base  # declarative_base
from app.models.user import User
from app.models.strategy import Strategy
# ... 다른 모델들 임포트

# target_metadata에 모델 등록
target_metadata = Base.metadata

# Async 설정
def run_migrations_online() -> None:
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async_migrations())
```

### 1.4 alembic.ini 설정

```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

---

## 2. 작성 가이드

### 2.1 마이그레이션 생성

**자동 생성 (autogenerate)**:
```bash
cd apps/api
alembic revision --autogenerate -m "create users table"
```

**수동 생성 (빈 템플릿)**:
```bash
alembic revision -m "add custom logic"
```

### 2.2 마이그레이션 파일 구조

```python
# alembic/versions/20250129_1234_abc123_create_users_table.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123'
down_revision = None  # 첫 번째는 None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """테이블 생성, 컬럼 추가 등"""
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMPTZ, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    """롤백: 테이블 삭제, 컬럼 삭제 등"""
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

### 2.3 upgrade() 작성 규칙

1. **순서**: 부모 테이블 → 자식 테이블
2. **FK 제약조건**: 자식 테이블 생성 후 FK 추가
3. **인덱스**: 테이블 생성 후 인덱스 생성
4. **초기 데이터**: `op.bulk_insert()`로 초기 데이터 삽입

### 2.4 downgrade() 작성 규칙

1. **순서**: 자식 테이블 → 부모 테이블 (upgrade 역순)
2. **FK 제약조건**: FK 먼저 삭제 → 테이블 삭제
3. **인덱스**: 인덱스 먼저 삭제 → 테이블 삭제

### 2.5 마이그레이션 예시

**예시 1: 테이블 생성**:
```python
def upgrade() -> None:
    op.create_table(
        'strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(20), server_default='DRAFT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_strategies_user_id', 'strategies', ['user_id'])
```

**예시 2: 컬럼 추가**:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(100), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

**예시 3: CHECK 제약조건 추가**:
```python
def upgrade() -> None:
    op.create_check_constraint(
        'credits_balance_check',
        'credits',
        'balance >= 0'
    )
```

---

## 3. 명령어

### 3.1 기본 명령어

| 명령어 | 설명 |
|--------|------|
| `alembic revision --autogenerate -m "message"` | 마이그레이션 자동 생성 |
| `alembic upgrade head` | 최신 버전으로 업그레이드 |
| `alembic downgrade` | 한 단계 롤백 |
| `alembic downgrade -1` | 한 단계 롤백 (동일) |
| `alembic downgrade base` | 초기 상태로 롤백 |
| `alembic current` | 현재 버전 확인 |
| `alembic history` | 마이그레이션 히스토리 |
| `alembic heads` | 최신 헤드 확인 |

### 3.2 명령어 예시

**마이그레이션 생성**:
```bash
# 자동 생성
alembic revision --autogenerate -m "add strategies table"

# 수동 생성
alembic revision -m "custom migration"
```

**업그레이드**:
```bash
# 최신으로
alembic upgrade head

# 특정 버전으로
alembic upgrade abc123

# N단계 업그레이드
alembic upgrade +2
```

**롤백**:
```bash
# 한 단계 롤백
alembic downgrade -1

# 특정 버전으로 롤백
alembic downgrade abc123

# 초기 상태로 (모든 테이블 삭제)
alembic downgrade base
```

### 3.3 개발 vs 프로덕션

**개발 환경**:
```bash
# 로컬 DB에 적용
alembic upgrade head
```

**프로덕션 환경**:
```bash
# 1. 리뷰: 마이그레이션 파일 검토
# 2. 백업: DB 백업
# 3. 테스트: 스테이징에서 먼저 테스트
# 4. 적용: 프로덕션에 적용
alembic upgrade head
```

---

## 4. 버전 관리

### 4.1 버전 식별자

**구조**: `YYYYMMDD_HHMM_<revision>_<message>`

**예시**:
- `20250129_1234_abc123_create_users_table.py`
- `20250129_1245_def456_add_strategies_table.py`

### 4.2 의존성 관리

**depends_on 사용**:
```python
revision = 'def456'
down_revision = 'abc123'  # 이전 버전
depends_on = ('abc123',)  # 명시적 의존성
```

**분기 마이그레이션**:
```python
# A분기
revision = 'branch_a'
down_revision = 'base'
branch_labels = ['branch_a']

# B분기 (A와 독립)
revision = 'branch_b'
down_revision = 'base'
branch_labels = ['branch_b']

# 병합
revision = 'merge'
down_revision = ('branch_a', 'branch_b')
```

### 4.3 롤백 전략

**단계별 롤백**:
```bash
# 한 단계씩 롤백
alembic downgrade -1

# N단계 롤백
alembic downgrade -3
```

**특정 시점으로 롤백**:
```bash
# 특정 버전으로
alembic downgrade abc123
```

### 4.4 데이터 마이그레이션

**데이터 변환**:
```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # 1. 컬럼 추가
    op.add_column('users', sa.Column('full_name', sa.String(100), nullable=True))

    # 2. 데이터 복사 (email → full_name)
    from sqlalchemy.orm import Session
    session = Session(bind=op.get_bind())
    session.execute(
        sa.update(sa.table('users'))
        .values(full_name=sa.column('email'))
    )
    session.commit()

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

---

## 5. 모범 사례

### 5.1 마이그레이션 원칙

1. **불변성**: 한 번 생성된 마이그레이션은 수정하지 않음
2. **순서**: FK는 자식 테이블 생성 후 추가
3. **가역성**: downgrade() 함수 항상 작성
4. **테스트**: 로컬에서 먼저 테스트

### 5.2 주의사항

| 상황 | 해결책 |
|------|--------|
| 프로덕션 데이터 삭제 | `op.execute()`로 데이터 백업 후 삭제 |
| 대용량 데이터 변경 | 배치 처리 (1000건씩) |
| FK 제약조건으로 인한 삭제 실패 | 임시로 FK 제거 후 삭제 |

### 5.3 대용량 마이그레이션

**배치 처리**:
```python
def upgrade() -> None:
    # 1000건씩 처리
    batch_size = 1000
    offset = 0

    while True:
        op.execute(f"""
            UPDATE users
            SET status = 'ACTIVE'
            WHERE id IN (
                SELECT id FROM users
                ORDER BY created_at
                LIMIT {batch_size} OFFSET {offset}
            );
        """)
        offset += batch_size
        if offset % 10000 == 0:
            print(f"Processed {offset} rows...")
```

---

## 6. 문제 해결

### 6.1 마이그레이션 충돌

**문제**: 두 개발자가 동시에 마이그레이션 생성

**해결**:
1. `down_revision` 충돌 확인
2. 리베이스(conflict) 해결
3. 충돌하는 마이그레이션 합치기

### 6.2 autogenerate가 동작하지 않음

**원인**: 모델이 `target_metadata`에 등록되지 않음

**해결**:
```python
# alembic/env.py
from app.models.user import User
from app.models.strategy import Strategy
# ... 모든 모델 임포트

target_metadata = Base.metadata
```

### 6.3 롤백 실패

**문제**: downgrade() 실행 시 데이터 무결성 오류

**해결**:
1. 데이터 수동 삭제
2. `op.execute()`로 강제 실행
3. DB 백업 후 `alembic downgrade base`

---

## 7. 상위/관련 문서

- **[../index.md](../index.md)** - 데이터 모델 개요
- **[erd.md](./erd.md)** - ERD 다이어그램
- **[table-schemas.md](./table-schemas.md)** - 테이블별 상세 스키마
- **[constraints.md](./constraints.md)** - 제약조건 상세

---

## 8. 참고 자료

- [Alembic 공식 문서](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)

---

*최종 업데이트: 2025-12-29*
