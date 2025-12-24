# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository serves two purposes:

1. **Claude Code Extension Project** - Contains AI agent configurations, skills, and tools for extending Claude Code's capabilities
2. **Full-Stack Application** - A Turborepo monorepo with FastAPI backend + Next.js frontend

### Claude Code Extension

- **Skills** (.claude/skills/) - Modular capabilities that extend Claude's functionality
- **Subagents** (.claude/agents/) - Specialized AI assistants for specific tasks
- **Documentation** (docs/cc/) - Reference materials for hooks, slash commands, and subagents
- **Prompts** (prompt/) - Prompt templates and design patterns

### Full-Stack Application

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Redis
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + TanStack Query + Zustand
- **Build**: Turborepo with pnpm workspaces

## Architecture

### Monorepo Structure

```
gr8diy-web/
├── apps/
│   ├── web/              # Next.js frontend (App Router)
│   │   ├── src/
│   │   │   ├── app/      # Next.js App Router pages
│   │   │   ├── components/
│   │   │   ├── lib/      # Utilities (axios, utils)
│   │   │   ├── hooks/    # React hooks (use-auth)
│   │   │   ├── services/ # API services
│   │   │   └── stores/   # Zustand stores
│   │   └── package.json
│   └── api/              # FastAPI backend
│       ├── app/
│       │   ├── api/v1/   # API endpoints
│       │   ├── core/     # Config, security, deps
│       │   ├── db/       # Database (base, session)
│       │   ├── models/   # SQLAlchemy models
│       │   ├── schemas/  # Pydantic schemas
│       │   └── services/ # Business logic
│       ├── alembic/      # Database migrations
│       └── pyproject.toml
├── packages/
│   ├── ui/               # Shared UI components (@gr8diy/ui)
│   └── types/            # Shared TypeScript types (@gr8diy/types)
├── docker-compose.yml
├── turbo.json
└── package.json
```

### Tech Stack Details

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| UI Library | shadcn/ui patterns (class-variance-authority based) |
| State | TanStack Query (server) + Zustand (client) |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0 (Async) |
| Database | PostgreSQL (asyncpg driver) |
| Cache | Redis (refresh tokens, sessions) |
| Auth | JWT access/refresh tokens with Redis storage |
| Build | Turborepo with pnpm workspaces |

## Common Commands

### Development

```bash
# Start all services
pnpm dev

# Start specific apps
pnpm --filter @gr8diy-web dev     # Frontend at :3000
pnpm --filter @gr8diy-api dev     # Backend at :8000

# Docker services
docker-compose up -d postgres redis
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Build & Test

```bash
pnpm build           # Build all
pnpm lint            # Lint all
pnpm typecheck       # Type check all
```

### Database Migrations

```bash
cd apps/api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Key Patterns

### API Client Setup

Frontend uses axios with interceptors for:
- Automatic Bearer token injection from localStorage
- Token refresh on 401 responses
- Base URL from `NEXT_PUBLIC_API_URL` env var

### Authentication Flow

1. Client POSTs `/api/v1/auth/login` with email/password
2. Server returns access_token (30min) and refresh_token (7 days)
3. Client stores both in localStorage and Zustand store
4. Axios interceptor adds `Authorization: Bearer {access_token}` to requests
5. On 401, interceptor calls `/api/v1/auth/refresh` automatically
6. New tokens stored and original request retried

### State Management

- **Server State**: TanStack Query with 60s staleTime
- **Client State**: Zustand with localStorage persistence (auth store)

### Component Patterns

UI components use `class-variance-authority` for variant props:
```tsx
const buttonVariants = cva("base-classes", {
  variants: {
    variant: { default: "...", outline: "..." },
    size: { default: "...", sm: "..." }
  }
})
```

## Claude Code Extension (Original)

### Skill Structure

Each skill follows this structure:
```
skill-name/
├── SKILL.md (required) - Main skill file with YAML frontmatter
├── scripts/ (optional) - Executable Python/Bash scripts
├── references/ (optional) - Documentation loaded as needed
└── assets/ (optional) - Files used in output
```

### Available Skills

| Skill | Purpose |
|-------|---------|
| hook-creator | Create and configure Claude Code hooks |
| skill-creator | Guide for creating effective skills |
| slash-command-creator | Guide for creating custom slash commands |
| subagent-creator | Create specialized Claude Code sub-agents |
| youtube-collector | YouTube channel registration and content collection (Korean) |

### File Locations

| Type | Location |
|------|----------|
| Project skills | `.claude/skills/` |
| Project agents | `.claude/agents/` |
| User skills | `~/.claude/skills/` |
| User agents | `~/.claude/agents/` |
| YouTube data | `.reference/` |

## Environment Variables

### Backend (`apps/api/.env`)
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gr8diy
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000
```

### Frontend (`apps/web/.env`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Language Context

The project includes both English and Korean content:
- Full-stack app: English
- Documentation and skills: English
- youtube-collector skill: Korean

When working on this project, respect the existing language conventions.
