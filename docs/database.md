# 데이터베이스 (Database)

## 개요
PostgreSQL을 메인 데이터베이스로 사용하고, Redis를 캐시 및 세션 저장소로 활용합니다. SQLAlchemy 2.0의 비동기 기능을 최대한 활용합니다.

## PostgreSQL
- **드라이버**: asyncpg (비동기)
- **ORM**: SQLAlchemy 2.0 (Async)
- **마이그레이션**: Alembic

## 현재 테이블
### users
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | Primary Key |
| email | String(255) | Unique, Indexed |
| hashed_password | String(255) | bcrypt 해시 |
| full_name | String(255) | Nullable |
| is_active | Boolean | Default: true |
| is_superuser | Boolean | Default: false |
| created_at | DateTime | 자동 생성 |
| updated_at | DateTime | 자동 갱신 |

## Redis
- **용도**: Refresh Token 저장, 레이트 리밋
- **드라이버**: aioredis
- **Key 패턴**: `refresh_token:{user_id}`, `rate_limit:{ip}:{endpoint}`

## 환경별 설정
- `development`: SSL disable
- `production`: SSL prefer

## 주요 파일
- `apps/api/app/db/session.py` - DB 세션
- `apps/api/app/models/user.py` - User 모델
- `apps/api/app/alembic/` - 마이그레이션
