# 배포 (Deployment)

## 개요
Turborepo + Docker Compose로 개발/프로덕션 환경을 구성합니다.

## 시작 방법
```bash
pnpm install                    # 의존성 설치
docker-compose up -d postgres redis  # DB/캐시 시작
cp apps/api/.env.example apps/api/.env   # 환경변수 설정
cp apps/web/.env.example apps/web/.env
cd apps/api && alembic upgrade head     # DB 마이그레이션
pnpm dev                        # 개발 서버 시작
```

## 서비스 포트
- Frontend: :3000, Backend: :8000
- PostgreSQL: :5432, Redis: :6379

## 빌드
```bash
pnpm build                      # 전체 빌드
pnpm --filter @gr8diy-web build # 프론트엔드만
pnpm --filter @gr8diy-api build # 백엔드만
```

## Docker 서비스
PostgreSQL 16, Redis 7, FastAPI (uvicorn), Next.js (standalone)

## 환경변수
**Backend**: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`
**Frontend**: `NEXT_PUBLIC_API_URL`

## 주요 파일
- `docker-compose.yml` - 서비스 정의
- `turbo.json` - 빌드 파이프라인
- `apps/api/Dockerfile`, `apps/web/Dockerfile`
