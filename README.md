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
# Build all packages
pnpm build

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
