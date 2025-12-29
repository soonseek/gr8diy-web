# 레이트 리밋 (Rate Limiting)

## 1. 정책

### 1.1 레이트 리밋 규칙

| 엔드포인트 | 제한 | 기준 |
|-----------|------|------|
| `POST /api/v1/auth/login` | 5회 / 5분 | IP 주소 |
| `POST /api/v1/auth/register` | 3회 / 시간 | IP 주소 |
| `POST /api/v1/auth/refresh` | 10회 / 분 | IP 주소 |
| `POST /api/v1/auth/logout` | 20회 / 분 | 사용자 |

### 1.2 정책 이유

**login/register**: 무차별 대입 방지 (Brute Force 방지)
**refresh**: 토큰 무한 생성 방지
**logout**: DoS 방지

---

## 2. 구현

### 2.1 Redis 기반 카운터

```python
from app.core.redis import redis_client

async def is_rate_limited(
    key: str,
    max_requests: int,
    window_seconds: int
) -> bool:
    """레이트 리밋 확인"""
    current = await redis_client.incr(key)

    if current == 1:
        # 처음 요청: 윈도우 설정
        await redis_client.expire(key, window_seconds)

    return current > max_requests
```

### 2.2 IP 주소 추출

```python
from fastapi import Request

async def get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출"""
    # Proxy 뒤에 있는 경우 X-Forwarded-For 확인
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host
```

---

## 3. 라이브러리

**slowapi**: 레이트 리밋을 쉽게 구현하는 라이브러리

### 3.1 설치

```bash
pip install slowapi
```

### 3.1 설정

```python
from slowapi import Limiter, _rate
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
```

---

## 4. FastAPI 코드

### 4.1 전역 설정

```python
from fastapi import FastAPI, Request, HTTPException, status
from slowapi import Limiter, _rate
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# 예외 핸들러
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "너무 많은 요청을 보내셨습니다. 잠시 후 다시 시도해주세요."}
    )
```

### 4.2 엔드포인트 적용

```python
from fastapi import APIRouter, Depends, Request
from slowapi.util import get_remote_address

router = APIRouter()

@router.post("/login")
@limiter.limit(_rate(5, 5 * 60))  # 5회/5분
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # ... 로그인 로직
    pass

@router.post("/register")
@limiter.limit(_rate(3, 60 * 60))  # 3회/시간
async def register(
    request: Request,
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # ... 회원가입 로직
    pass
```

### 4.3 사용자 기반 제한

```python
from slowapi.util import get_remote_address
from app.core.security import get_current_user

@router.post("/logout")
@limiter.limit(_rate(20, 60))  # 20회/분 (사용자별)
async def logout(
    request: Request,
    user: User = Depends(get_current_user)
):
    # ... 로그아웃 로직
    pass
```

---

## 5. 커스텀 Limiter

### 5.1 IP + 사용자 혼합

```python
def get_ip_and_user(request: Request) -> str:
    """IP + 사용자 ID 조합"""
    ip = get_remote_address(request)
    user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
    return f"{ip}:{user_id}"

limiter_user = Limiter(key_func=get_ip_and_user)
```

### 5.2 사용

```python
@router.post("/refresh")
@limiter_user.limit(_rate(10, 60))
async def refresh_token():
    # ... 토큰 갱신 로직
    pass
```

---

## 6. Redis + Slowapi 통합

### 6.1 Redis Storage

```python
from slowapi.util import get_remote_address
from slowapi.storage import RedisStorage
from app.core.redis import redis_client

# Redis 스토리지 사용
storage = RedisStorage(redis_client)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

---

## 7. 에러 응답

### 7.1 429 Too Many Requests

```json
{
  "detail": "너무 많은 요청을 보내셨습니다. 잠시 후 다시 시도해주세요.",
  "retry_after": 120
}
```

### 7.2 Retry-After 헤더

```python
from fastapi import Response

@router.post("/login")
@limiter.limit(_rate(5, 5 * 60))
async def login(...):
    # ... 로그인 로직

    # 레이트 리밋 초과 시
    raise HTTPException(
        status_code=429,
        detail="너무 많은 요청을 보내셨습니다.",
        headers={"Retry-After": "120"}
    )
```

---

## 8. 모니터링

### 8.1 레이트 리밋 로그

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/login")
@limiter.limit(_rate(5, 5 * 60))
async def login(request: Request, ...):
    ip = get_client_ip(request)
    logger.warning(f"Rate limit exceeded for IP: {ip}")
```

### 8.2 Prometheus 메트릭

```python
from prometheus_client import Counter

rate_limit_counter = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit exceeded",
    ["endpoint", "ip"]
)

@router.post("/login")
@limiter.limit(_rate(5, 5 * 60))
async def login(request: Request, ...):
    try:
        # ... 로직
    except RateLimitExceeded:
        rate_limit_counter.labels(endpoint="/login", ip=get_client_ip(request)).inc()
        raise
```

---

## 9. 상위/관련 문서

- **[../index.md](../index.md)** - 인증 시스템 개요
- **[api-endpoints.md](./api-endpoints.md)** - API 엔드포인트 상세
- **[token-management.md](./token-management.md)** - 토큰 관리 상세
- **[encryption.md](./encryption.md)** - 암호화 상세

---

## 10. 참고 자료

- [slowapi 문서](https://slowapi.readthedocs.io/)
- [FastAPI Rate Limiting](https://fastapi.tiangolo.com/tutorial/tutorial-limiting-rate-limiter/)

---

*최종 업데이트: 2025-12-29*
