# 토큰 관리 (Token Management)

## 1. 토큰 생성

### 1.1 Access Token 생성

```python
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

def create_access_token(data: dict) -> str:
    """Access Token 생성 (15분)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )
    return encoded_jwt
```

### 1.2 Refresh Token 생성

```python
import uuid

def create_refresh_token() -> str:
    """Refresh Token 생성 (UUID)"""
    return str(uuid.uuid4())
```

### 1.3 Pydantic Schema

```python
from pydantic import BaseModel, Field

class TokenPayload(BaseModel):
    sub: str = Field(..., alias="user_id")
    email: str
    exp: int
    iat: int
    type: str = "access"

    class Config:
        populate_by_name = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="초 단위")
```

---

## 2. 토큰 Rotation

### 2.1 Rotation 전략

1. Refresh Token 사용 시 새 토큰 발급
2. 기존 Refresh Token Redis에서 삭제
3. 탈취 토큰 재사용 방지

### 2.2 구현

```python
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.core.redis import redis_client

async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    # 1. refresh_token으로 user_id 조회
    # (Redis에서 확인)
    token_data = await redis_client.get(f"refresh_token:*:{refresh_token}")
    if not token_data:
        raise HTTPException(status_code=401, detail="유효하지 않은 refresh_token")

    user_id = extract_user_id_from_token(token_data)

    # 2. 새 토큰 생성
    access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token()

    # 3. 기존 토큰 삭제, 새 토큰 저장
    await redis_client.delete(f"refresh_token:{user_id}:{refresh_token}")
    await redis_client.setex(
        f"refresh_token:{user_id}:{new_refresh_token}",
        86400,
        "1"
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 900
    }
```

---

## 3. 블랙리스트 관리

### 3.1 블랙리스트 추가

로그아웃 시 Access Token을 블랙리스트에 추가:

```python
async def add_to_blacklist(access_token: str, expires_in: int):
    """Access Token 블랙리스트 추가"""
    await redis_client.setex(
        f"blacklist:{access_token}",
        expires_in,
        "revoked"
    )
```

### 3.2 블랙리스트 검증

```python
async def is_token_blacklisted(access_token: str) -> bool:
    """토큰 블랙리스트 확인"""
    result = await redis_client.get(f"blacklist:{access_token}")
    return result is not None
```

### 3.3 Deps에 통합

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    # 토큰 검증
    if await is_token_blacklisted(credentials.credentials):
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")

    # ... user 조회 로직
```

---

## 4. 토큰 검증

### 4.1 Access Token 검증

```python
from jose import jwt, JWTError
from app.core.config import settings

async def verify_access_token(token: str) -> TokenPayload:
    """Access Token 검증"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증되지 않은 사용자입니다.",
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)

        if token_data.type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return token_data
```

### 4.2 Refresh Token 검증

```python
async def verify_refresh_token(
    token: str,
    db: AsyncSession
) -> User:
    """Refresh Token 검증"""
    # Redis에서 확인
    result = await redis_client.get(f"refresh_token:*:{token}")
    if not result:
        raise HTTPException(status_code=401, detail="유효하지 않은 refresh_token")

    # User 조회
    token_data = json.loads(result)
    user = await db.get(User, token_data["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없음")

    return user
```

---

## 5. Redis 명령어

### 5.1 refresh_token 저장

```python
await redis_client.setex(
    f"refresh_token:{user_id}:{token_id}",
    86400,  # 1일
    json.dumps({
        "user_id": str(user_id),
        "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
    })
)
```

### 5.2 refresh_token 조회

```python
# 와일드카드로 user_id로 조회
keys = await redis_client.keys(f"refresh_token:{user_id}:*")
for key in keys:
    token_data = await redis_client.get(key)
```

### 5.3 refresh_token 삭제

```python
await redis_client.delete(f"refresh_token:{user_id}:{token_id}")
```

### 5.4 사용자의 모든 토큰 삭제 (로그아웃)

```python
keys = await redis_client.keys(f"refresh_token:{user_id}:*")
if keys:
    await redis_client.delete(*keys)
```

---

## 6. FastAPI Router

```python
from fastapi import APIRouter
from app.schemas.auth import TokenResponse
from app.services.token_service import refresh_token_service

router = APIRouter()

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    return await refresh_token_service(refresh_token, db)
```

---

## 7. 상위/관련 문서

- **[../index.md](../index.md)** - 인증 시스템 개요
- **[api-endpoints.md](./api-endpoints.md)** - API 엔드포인트 상세
- **[encryption.md](./encryption.md)** - 암호화 상세
- **[rate-limiting.md](./rate-limiting.md)** - 레이트 리밋 상세

---

*최종 업데이트: 2025-12-29*
