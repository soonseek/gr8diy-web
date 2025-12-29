# gr8diy-web

Full-stack application built with FastAPI + Next.js + Turborepo.

## Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| **UI Components** | shadcn/ui patterns |
| **State Management** | TanStack Query + Zustand |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy 2.0 (Async) |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **Auth** | JWT (access/refresh tokens) with Redis storage |
| **Build System** | Turborepo |
| **Container** | Docker Compose |

## Project Structure

```
gr8diy-web/
├── apps/
│   ├── web/              # Next.js frontend
│   └── api/              # FastAPI backend
├── packages/
│   ├── ui/               # Shared UI components
│   └── types/            # Shared TypeScript types
├── docker-compose.yml
├── turbo.json
└── package.json
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- pnpm 8+
- Docker (for PostgreSQL and Redis)

### Installation

```bash
# Install dependencies
pnpm install

# Setup environment files
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# Start services (PostgreSQL, Redis)
docker-compose up -d postgres redis

# Run database migrations (from apps/api directory)
cd apps/api
alembic upgrade head
cd ../..
```

### Development

```bash
# Start all services in development mode
pnpm dev

# Or start individually:
pnpm --filter @gr8diy-web dev     # Frontend at http://localhost:3000
pnpm --filter @gr8diy-api dev     # Backend at http://localhost:8000
```

### Building

```bash
## 터미널 1 - 프론트엔드:
  pnpm dev
  또는
  cd apps/web
  pnpm dev

## 터미널 2 - 백엔드:
  cd apps/api
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Build individually
pnpm --filter @gr8diy-web build
pnpm --filter @gr8diy-api build
```

## API Documentation

When the backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Backend (`apps/api/.env`)

See `apps/api/.env.example` for complete documentation with required/optional flags.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL URL with asyncpg driver |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis URL for sessions |
| `JWT_SECRET_KEY` | Yes | - | Secret key for JWT signing |
| `ENVIRONMENT` | No | `development` | Environment: development/staging/production |
| `DEBUG` | No | `false` | Enable debug mode |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins (comma-separated) |

**Important**: SSL is automatically configured based on `ENVIRONMENT`:
- Development: SSL disabled
- Production: SSL preferred

### Frontend (`apps/web/.env`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Documentation System

This project uses a **3-tier documentation structure** with an AI-powered doc-loader subagent.

### Document Structure

```
gr8diy-web/
├── PRD.md                           # L0: Product overview
├── docs/
│   ├── 01-overview/                 # L1: System overview
│   ├── 02-authentication/           # L2: Auth domain
│   ├── 03-strategy/                 # L2: Strategy domain
│   ├── 04-backtesting/              # L2: Backtesting domain
│   ├── 05-blockchain/               # L2: Blockchain domain
│   └── 06-data/                     # L2: Data domain
```

Each domain contains:
- `index.md` - Overview + design (specs routing guide included)
- `specs/` - Detailed implementation specs

### Doc-Loader Subagent

This project includes an **auto-loading documentation subagent** that:
1. Automatically loads relevant docs based on your task
2. Creates a todo list to track progress
3. Helps you stay organized during implementation

**How it works:**
1. You describe your task (e.g., "Implement RSI node for strategy editor")
2. Doc-loader analyzes keywords and identifies relevant domains
3. Automatically loads the appropriate `index.md` and `specs/*.md` files
4. **Creates a todo list** to track implementation steps
5. You can start working immediately with full context

**Example usage:**
```
# Just describe your task - doc-loader runs automatically
"전략 에디터의 RSI 노드를 구현해줘"
→ doc-loader loads: docs/03-strategy/index.md, specs/node-types.md
→ doc-loader creates todo list:
   [ ] RSI 노드 파라미터 정의
   [ ] RSI 지표 계산 로직 구현
   [ ] 노드 검증 규칙 추가
   [ ] 테스트 코드 작성
```

**Supported domain keywords:**
| Domain | Keywords |
|--------|----------|
| 01-overview | architecture, system, tech stack, overview |
| 02-authentication | login, register, auth, token, JWT, password |
| 03-strategy | strategy, editor, node, edge, workflow, trigger, LLM |
| 04-backtesting | backtest, simulation, indicator, RSI, MACD, fee |
| 05-blockchain | blockchain, smart contract, on-chain, credit, gas |
| 06-data | data, table, schema, ERD, migration, index |

**Benefits:**
- ✅ Works in new chat sessions (project structure embedded in subagent)
- ✅ No manual `@doc-loader` invocation needed (runs proactively)
- ✅ Automatically loads the right docs for your task
- ✅ Creates todo lists to track progress automatically
- ✅ Reduces context switching and documentation hunting

### Todo Management Commands

Manually manage your todo list with these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `/todo` | Show current todo list | `/todo` |
| `/todo clear` | Clear all todos | `/todo clear` |
| `/todo complete <n>` | Mark todo #n as completed | `/todo complete 1` |
| `/todo remove <n>` | Remove todo #n | `/todo remove 2` |
| `/todo add <task>` | Add new todo | `/todo add 테스트 코드 작성` |

**Example output:**
```
User: /todo

Bot: 📋 현재 작업 목록 (3개)
  [ ] 1. RSI 노드 파라미터 정의
  [ ] 2. RSI 지표 계산 로직 구현
  [✓] 3. 노드 검증 규칙 추가 ← 완료됨

User: /todo complete 2

Bot: ✅ "RSI 지표 계산 로직 구현" 완료! [1/3]
```

### Key Documentation Files

| File | Purpose |
|------|---------|
| `PRD.md` | Product requirements, features, user flows |
| `docs/01-overview/index.md` | System architecture, tech stack, module structure |
| `docs/03-strategy/index.md` | Strategy editor, node types, validation |
| `docs/04-backtesting/index.md` | Backtesting pipeline, indicators, performance metrics |
| `docs/05-blockchain/index.md` | Smart contracts, credit system, gas optimization |
| `docs/06-data/index.md` | Data models, ERD, table schemas |

## Detailed Documentation

- **Backend API**: See `apps/api/README.md` for:
  - Complete setup guide
  - API endpoints reference
  - Database migration guide
  - Authentication flow
  - Troubleshooting

- **Frontend**: See `apps/web/README.md` for:
  - Next.js App Router patterns
  - Component architecture
  - State management patterns

## Database Migrations

```bash
# Create a new migration
cd apps/api
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Docker

```bash
# Start all services
docker-compose up

# Start with development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v
```

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all services in development mode |
| `pnpm build` | Build all packages |
| `pnpm lint` | Lint all packages |
| `pnpm test` | Run all tests |
| `pnpm clean` | Clean build artifacts and node_modules |

## License

MIT
