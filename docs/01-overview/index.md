# 시스템 개요 (System Overview)

## 1. 시스템 아키텍처

gr8diy-web는 **Monorepo + Microservices** 하이브리드 아키텍처를 따릅니다.

### 1.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Next.js 14      │  프론트엔드 (:3000)
                    │   (App Router)    │
                    └─────────┬─────────┘
                              │ HTTP/REST
                    ┌─────────▼─────────┐
                    │   FastAPI         │  백엔드 (:8000)
                    │   (API Gateway)   │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐    ┌───────▼────────┐    ┌───────▼────────┐
│  PostgreSQL    │    │  Redis         │    │  Blockchain    │
│  (데이터 저장)  │    │  (캐시/세션)   │    │  (온체인 기록)  │
└────────────────┘    └────────────────┘    └────────────────┘
```

---

## 2. 모듈 구성

### 2.1 apps/ 구조

```
apps/
├── web/                 # 프론트엔드 (Next.js)
│   ├── src/
│   │   ├── app/        # App Router pages
│   │   ├── components/ # React 컴포넌트
│   │   ├── lib/        # 유틸리티 (axios)
│   │   ├── hooks/      # React Hooks (use-auth)
│   │   ├── services/   # API 클라이언트
│   │   └── stores/     # Zustand 상태
│   └── package.json
│
└── api/                # 백엔드 (FastAPI)
    ├── app/
    │   ├── api/        # API 엔드포인트
    │   ├── core/       # 설정, 보안, 의존성
    │   ├── db/         # DB 세션
    │   ├── models/     # SQLAlchemy 모델
    │   ├── schemas/    # Pydantic 스키마
    │   └── services/   # 비즈니스 로직
    └── pyproject.toml
```

### 2.2 packages/ 구조

```
packages/
├── ui/                 # 공유 UI 컴포넌트 (@gr8diy/ui)
└── types/              # 공유 TypeScript 타입 (@gr8diy/types)
```

### 2.3 최상위 설정 파일

| 파일 | 설명 |
|------|------|
| `pnpm-workspace.yaml` | pnpm 워크스페이스 설정 |
| `turbo.json` | Turborepo 빌드 캐싱 설정 |
| `docker-compose.yml` | 개발 환경 컨테이너编排 |
| `package.json` | Monorepo 루트 패키지 |

---

## 3. 개발 환경

### 3.1 Monorepo 설정

**pnpm workspaces**:
```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**Turborepo**:
```json
// turbo.json
{
  "tasks": {
    "build": { "dependsOn": ["^build"] },
    "dev": { "cache": false, "persistent": true }
  }
}
```

### 3.2 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `pnpm dev` | 전체 서비스 실행 (:3000, :8000) |
| `pnpm --filter @gr8diy-web dev` | 프론트엔드만 실행 |
| `pnpm --filter @gr8diy-api dev` | 백엔드만 실행 |
| `pnpm build` | 전체 빌드 |
| `pnpm typecheck` | 전체 타입 검사 |

### 3.3 환경변수

**백엔드 (`apps/api/.env`)**:
- `DATABASE_URL` - PostgreSQL 연결 URL
- `REDIS_URL` - Redis 연결 URL
- `JWT_SECRET_KEY` - JWT 서명 키
- `ENVIRONMENT` - development/staging/production

**프론트엔드 (`apps/web/.env`)**:
- `NEXT_PUBLIC_API_URL` - 백엔드 API URL

---

## 4. 요청-응답 사이클

### 4.1 인증 요청

```
1. Client → POST /api/v1/auth/login
2. FastAPI → PostgreSQL (user 조회)
3. FastAPI → bcrypt (비밀번호 검증)
4. FastAPI → JWT 생성 (access_token, refresh_token)
5. FastAPI → Redis (refresh_token 저장)
6. Client ← 토큰 응답
7. Client → localStorage 저장
8. Client → Axios 인터셉터 (Bearer token 자동 주입)
```

### 4.2 전략 생성 요청

```
1. Client → POST /api/v1/strategies (전략 JSON)
2. FastAPI → Pydantic (요청 검증)
3. FastAPI → PostgreSQL (strategies 테이블 저장)
4. Client ← 생성된 전략 ID
```

### 4.3 백테스트 요청

```
1. Client → POST /api/v1/backtests
2. FastAPI → Celery/Background Task (비동기 작업)
3. FastAPI → "QUEUED" 상태 반환
4. Worker → OHLCV 데이터 조회
5. Worker → 캔들 순회 → 조건 평가
6. Worker → PostgreSQL (결과 저장)
7. Client → GET /api/v1/backtests/{id} (폴링)
```

---

## 5. 문서 네비게이션

이 개요 문서를 읽은 후, 작업하려는 도메인에 따라 다음 문서를 참고하세요:

| 작업 내용 | 참조할 문서 |
|-----------|------------|
| **로그인/회원가입 구현** | [../02-authentication/index.md](../02-authentication/index.md) |
| **전략 에디터 개발** | [../03-strategy/index.md](../03-strategy/index.md) → `specs/node-types.md` |
| **백테스팅 엔진 개발** | [../04-backtesting/index.md](../04-backtesting/index.md) → `specs/simulation.md` |
| **스마트 컨트랙트 개발** | [../05-blockchain/index.md](../05-blockchain/index.md) → `specs/smart-contracts.md` |
| **DB 스키마 수정** | [../06-data/index.md](../06-data/index.md) → `specs/table-schemas.md` |

### 문서 찾기 팁

```
docs/
├── 01-overview/           # ← 현재 위치 (전체 시스템)
├── 02-authentication/     # 인증 시스템
│   ├── index.md           # ← 인증 개요 + 설계
│   └── specs/             # ← API 엔드포인트, 토큰 관리 등
├── 03-strategy/           # 전략 에디터
│   ├── index.md           # ← 에디터 개요 + 설계
│   └── specs/             # ← 노드 타입, 검증 규칙 등
├── 04-backtesting/        # 백테스팅
│   ├── index.md           # ← 백테스팅 개요 + 설계
│   └── specs/             # ← 시뮬레이션, 지표 등
├── 05-blockchain/         # 블록체인
│   ├── index.md           # ← 블록체인 개요 + 설계
│   └── specs/             # ← 스마트 컨트랙트, 크레딧 등
└── 06-data/               # 데이터 모델
    ├── index.md           # ← 데이터 개요 + ERD
    └── specs/             # ← 테이블 스키마, 인덱스 등
```

**작업 흐름 예시**:
1. "전략 에디터의 RSI 노드를 구현해" → `docs/03-strategy/`를 먼저 읽고 → `specs/node-types.md` 참조
2. "백테스팅의 수수료 계산을 수정해" → `docs/04-backtesting/`를 먼저 읽고 → `specs/commission-slippage.md` 참조

---

*최종 업데이트: 2025-12-29*
