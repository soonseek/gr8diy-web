# API 엔드포인트 (API Endpoints)

## 1. POST /api/v1/auth/register

회원가입

### Request

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Pydantic Schema**:
```python
from pydantic import BaseModel, EmailStr, field_validator
import re

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다')
        if not re.search(r'[A-Z]', v):
            raise ValueError('대문자를 포함해야 합니다')
        if not re.search(r'[a-z]', v):
            raise ValueError('소문자를 포함해야 합니다')
        if not re.search(r'[0-9]', v):
            raise ValueError('숫자를 포함해야 합니다')
        if not re.search(r'[!@#$%^&*]', v):
            raise ValueError('특수문자를 포함해야 합니다')
        return v
```

### Response

**201 Created**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2025-01-29T12:00:00Z"
}
```

**400 Bad Request**:
```json
{
  "detail": "이미 존재하는 이메일입니다."
}
```

```json
{
  "detail": "비밀번호는 8자 이상이어야 합니다."
}
```

---

## 2. POST /api/v1/auth/login

로그인

### Request

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Pydantic Schema**:
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

### Response

**200 OK**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Response Headers**:
```
Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=604800
```

**401 Unauthorized**:
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

---

## 3. POST /api/v1/auth/refresh

토큰 갱신

### Request

**Headers**:
```
Authorization: Bearer {access_token}
```

**Cookies**: httpOnly 쿠키에서 자동 전송
```
refresh_token={value}
```

**Body**: 없음

### Response

**200 OK**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Response Headers**:
```
Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=604800
```

**401 Unauthorized**:
```json
{
  "detail": "유효하지 않은 refresh_token입니다."
}
```

```json
{
  "detail": "refresh_token이 만료되었습니다. 다시 로그인해주세요."
}
```

---

## 4. POST /api/v1/auth/logout

로그아웃

### Request

**Headers**:
```
Authorization: Bearer {access_token}
```

**Cookies**: httpOnly 쿠키에서 자동 전송
```
refresh_token={value}
```

**Body**: 없음

### Response

**204 No Content**

**Response Headers**:
```
Set-Cookie: refresh_token=; Max-Age=0
```

**401 Unauthorized**:
```json
{
  "detail": "인증되지 않은 사용자입니다."
}
```

---

## 5. GET /api/v1/users/me

내 정보 조회

### Request

**Headers**:
```
Authorization: Bearer {access_token}
```

**Body**: 없음

### Response

**200 OK**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-29T12:00:00Z",
  "updated_at": "2025-01-29T12:00:00Z"
}
```

**401 Unauthorized**:
```json
{
  "detail": "인증되지 않은 사용자입니다."
}
```

---

## 6. GET /api/v1/users/

사용자 목록 (페이지네이션)

### Request

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | int | 아니오 | 페이지 번호 (default: 1) |
| size | int | 아니오 | 페이지 크기 (default: 20) |

### Response

**200 OK**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "created_at": "2025-01-29T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

**401 Unauthorized**:
```json
{
  "detail": "권한이 없습니다."
}
```

**403 Forbidden**:
```json
{
  "detail": "관리자만 접근할 수 있습니다."
}
```

---

## 7. Status Codes

| 코드 | 설명 |
|------|------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## 8. Error Codes

| 코드 | 설명 |
|------|------|
| `EMAIL_ALREADY_EXISTS` | 이미 존재하는 이메일 |
| `INVALID_PASSWORD` | 비밀번호 복잡도 불충족 |
| `INVALID_CREDENTIALS` | 이메일 또는 비밀번호 불일치 |
| `INVALID_TOKEN` | 유효하지 않은 토큰 |
| `TOKEN_EXPIRED` | 토큰 만료 |
| `USER_NOT_FOUND` | 사용자를 찾을 수 없음 |

---

## 9. FastAPI 구현 예시

### 9.1 회원가입

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # 이메일 중복 확인
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    # 사용자 생성
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user
```

### 9.2 로그인

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.redis import redis_client

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # 사용자 조회
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token()

    # Redis에 refresh_token 저장
    await redis_client.setex(
        f"refresh_token:{user.id}:{refresh_token}",
        604800,  # 7일
        json.dumps({
            "user_id": str(user.id),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        })
    )

    # httpOnly 쿠키로도 전송
    response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800  # 30분
    }

    # 쿠키 설정 (FastAPI Response 객체 사용 필요)
    # return JSONResponse(content=response, headers={
    #     "Set-Cookie": f"refresh_token={refresh_token}; HttpOnly; Secure; SameSite=Strict; Max-Age=604800"
    # })

    return response
```

### 9.3 종속성 (Dependencies)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증되지 않은 사용자입니다.",
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
```

---

## 10. 상위/관련 문서

- **[../index.md](../index.md)** - 인증 시스템 개요
- **[token-management.md](./token-management.md)** - 토큰 관리 상세
- **[encryption.md](./encryption.md)** - 암호화 상세
- **[rate-limiting.md](./rate-limiting.md)** - 레이트 리밋 상세

---

*최종 업데이트: 2025-12-29*
