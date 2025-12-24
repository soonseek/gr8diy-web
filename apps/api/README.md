# gr8diy-api

FastAPI backend application with async PostgreSQL, Redis, and JWT authentication.

## Tech Stack

- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy 2.0 (Async)
- **Cache**: Redis for session and refresh token storage
- **Authentication**: JWT with access/refresh token pattern
- **Migrations**: Alembic with async support

## Project Structure

```
apps/api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps.py       # FastAPI dependencies (auth, db)
│   │       └── endpoints/    # API route handlers
│   ├── alembic/
│   │   ├── env.py           # Alembic async configuration
│   │   └── versions/        # Migration files
│   ├── core/
│   │   ├── config.py        # Settings and configuration
│   │   ├── deps.py          # Common dependencies
│   │   └── security.py      # JWT and password utilities
│   ├── db/
│   │   └── base.py          # Database engine and base class
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
├── alembic.ini              # Alembic configuration
├── .env                     # Environment variables (create this)
├── .env.example             # Environment variables template
└── pyproject.toml           # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker (optional, for containerized services)

### 1. Environment Setup

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL URL with asyncpg driver |
| `REDIS_URL` | No | Redis URL (default: `redis://localhost:6379/0`) |
| `JWT_SECRET_KEY` | Yes | Secret for JWT signing (change in production!) |
| `ENVIRONMENT` | No | `development`, `staging`, or `production` |
| `DEBUG` | No | Enable debug mode (default: `false`) |

### 2. Install Dependencies

```bash
cd apps/api
pip install -e .
```

Or using Poetry (if configured):

```bash
poetry install
```

### 3. Database Migrations

Run migrations to create database tables:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Rollback
alembic downgrade -1
```

### 4. Start the Server

Development mode with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the CLI:

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## Database Migrations (Alembic)

### Creating Migrations

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Add users table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Running Migrations

```bash
# Apply all migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one step
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Migration History

```bash
# Show migration history
alembic history

# Show current version
alembic current
```

## Environment Variables Reference

See `.env.example` for complete documentation with required/optional flags.

### Database Configuration

```bash
# PostgreSQL connection string
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# SSL is auto-configured based on ENVIRONMENT:
# - development: ssl=disable
# - production: ssl=prefer
```

### JWT Configuration

```bash
# IMPORTANT: Change this in production!
JWT_SECRET_KEY=your-secret-key-here

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### CORS Configuration

```bash
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000,https://example.com
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_auth.py
```

### Code Quality

```bash
# Format code
black app/
ruff app/

# Type checking
mypy app/
```

### Database Access

```python
from app.db.base import async_session_maker
from sqlalchemy import select

async with async_session_maker() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (invalidate refresh token)

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update current user profile

## Authentication Flow

1. **Register/Login**: Client sends credentials to `/auth/register` or `/auth/login`
2. **Tokens**: Server returns `access_token` (30min) and `refresh_token` (7 days)
3. **Request**: Include `Authorization: Bearer {access_token}` header
4. **Refresh**: On 401 error, call `/auth/refresh` with `refresh_token`
5. **Logout**: Call `/auth/logout` to invalidate refresh token in Redis

## Docker Support

### Using Docker Compose

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Stop services
docker-compose down
```

### Running API in Docker

```bash
# Build image
docker build -t gr8diy-api .

# Run container
docker run -p 8000:8000 --env-file .env gr8diy-api
```

## Production Deployment

### Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Use production PostgreSQL with SSL
- [ ] Configure Redis for persistence
- [ ] Set up proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging

### Running with Gunicorn

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Troubleshooting

### Alembic SSL Errors

If you encounter SSL errors with PostgreSQL:

1. For local development: Ensure `ENVIRONMENT=development` in `.env`
2. For production: Check SSL certificate configuration
3. Override SSL mode: Add `?ssl=disable` or `?ssl=require` to `DATABASE_URL`

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql postgresql://user:pass@localhost:5432/dbname
```

### Redis Connection Issues

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
```

## License

MIT
