# 인증 시스템 (Authentication)

## 1. 인증 시스템 개요

### 1.1 JWT 방식

gr8diy-web는 **JWT (JSON Web Token)** 기반의 이중 토큰 방식을 사용합니다.

**토큰 구조**:
- **Access Token**: 짧은 유효기간, API 요청 시 사용
- **Refresh Token**: 긴 유효기간, Access Token 갱신 시 사용

**이중 토큰 장점**:
- Access Token 탈취 시 피해 최소화 (짧은 유효기간)
- Refresh Token은 서버(Redis)에서 관리하여 무효화 가능
- 보안성과 사용자 경험의 균형

### 1.2 토큰 만료 정책

| 토큰 | 만료 기간 | 설명 |
|------|-----------|------|
| **Access Token** | 30분 | API 요청 시 사용 |
| **Refresh Token** | 7일 | Access Token 갱신 시 사용 |

**정책 이유**:
- 적절한 길이의 Access Token: 탈취 시 피해 최소화 + 사용자 경험
- 7일 Refresh Token: 사용자가 1주일에 한 번만 재로그인

### 1.3 토큰 저장 위치

| 토큰 | 저장 위치 | 설명 |
|------|-----------|------|
| Access Token | localStorage | 프론트엔드에서 관리 |
| Refresh Token | Redis (서버) + httpOnly 쿠키 | 서버에서 유효성 검증, 쿠키로 전송 (XSS 방지) |

## 2. 인증 플로우

### 2.1 회원가입 플로우
```
1. Client → POST /api/v1/auth/register
   { email, password, full_name (optional) }

2. FastAPI → 이메일 중복 검증 (PostgreSQL)
          → 비밀번호 복잡도 검증
          → bcrypt 해싱 (cost=12)
          → users 테이블 생성
          → credits 테이블에 0 크레딧 초기 계정 생성

3. Client ← 201 Created { id, email, created_at }
```

**비밀번호 복잡도 요구사항**:
- 최소 8자 이상
- 대문자 포함 (A-Z)
- 소문자 포함 (a-z)
- 숫자 포함 (0-9)
- 특수문자 포함 (!@#$%^&*)

### 2.2 로그인 플로우
```
1. Client → POST /api/v1/auth/login
   { email, password }

2. FastAPI → 이메일 조회 (PostgreSQL)
          → bcrypt 비밀번호 검증
          → access_token 생성 (30분, JWT)
          → refresh_token 생성 (7일, UUID)
          → refresh_token 저장 (Redis, TTL 7일)
          → refresh_token을 httpOnly 쿠키로 설정

3. Client ← {
     access_token,
     token_type: "bearer",
     expires_in: 1800
   }
   + Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=604800

4. Client → localStorage에 access_token 저장
           → httpOnly 쿠키는 자동 전송됨
```

### 2.3 토큰 갱신 플로우
```
1. Client → POST /api/v1/auth/refresh
   (httpOnly 쿠키가 자동으로 refresh_token 전송)

2. FastAPI → 쿠키에서 refresh_token 추출
          → Redis에서 refresh_token 조회 및 유효성 검증
          → 새 access_token 생성 (30분)
          → 새 refresh_token 생성 (Rotation, 7일)
          → 기존 refresh_token 삭제 (Redis)

3. Client ← {
     access_token,
     token_type: "bearer",
     expires_in: 1800
   }
   + Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=604800
```

### 2.4 로그아웃 플로우
```
1. Client → POST /api/v1/auth/logout
   Authorization: Bearer {access_token}
   (httpOnly 쿠키가 자동으로 refresh_token 전송)

2. FastAPI → 현재 user 식별 (access_token)
          → Redis에서 refresh_token 삭제
          → httpOnly 쿠키 만료 처리
          → (선택) access_token 블랙리스트 추가

3. Client ← 204 No Content
   + Set-Cookie: refresh_token=; Max-Age=0

4. Client → localStorage에서 access_token 삭제
```

## 3. 보안 전략

### 3.1 비밀번호 해싱

**알고리즘**: bcrypt
**cost factor**: 12
**이유**: GPU 공격 저항, 조정 가능한 계산 비용

### 3.2 API 키 암호화

**알고리즘**: AES-256-GCM
**용도**: LLM API 키, 거래소 API 키
**키 관리**: `SECRET_KEY` 환경변수에서 PBKDF2로 파생

### 3.3 JWT 서명

**알고리즘**: HS256 (HMAC-SHA256)
**서명 키**: `JWT_SECRET_KEY` 환경변수
**키 길이**: 최소 32자 (권장 64자 이상)

### 3.4 토큰 Rotation

- Refresh Token 사용 시 새 토큰 발급
- 기존 토큰 Redis에서 삭제 (재사용 공격 방지)
- 탈취 토큰 사용 시도 감지 가능

### 3.5 레이트 리밋

- `/login`: 5회/분 (IP 기반)
- `/register`: 3회/5분 (IP 기반)
- `/refresh`: 10회/분 (IP 기반)

---

## 4. Redis 활용

### 4.1 Redis 데이터 구조

**refresh_token 저장**:
```
Key: refresh_token:{user_id}:{token_id}
Value: {
  "expires_at": "2025-02-05T12:00:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
TTL: 7일 (604800초)
```

**access_token 블랙리스트** (선택):
```
Key: blacklist:{access_token}
Value: "revoked"
TTL: 30분 (1800초)
```

**로그인 기록** (선택):
```
Key: login_history:{user_id}
Value: [
  {
    "ip": "127.0.0.1",
    "timestamp": "2025-01-29T12:00:00Z"
  }
]
TTL: 30일
```

### 4.2 세션 관리

**Refresh Token Rotation**:
- 토큰 갱신 시 기존 refresh_token 폐기
- Redis에서 삭제 후 새 토큰 발급
- 탈취 토큰 사용 방지

---

## 5. API 설계 (개요)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/auth/register` | POST | 회원가입 |
| `/api/v1/auth/login` | POST | 로그인 |
| `/api/v1/auth/refresh` | POST | 토큰 갱신 |
| `/api/v1/auth/logout` | POST | 로그아웃 |
| `/api/v1/users/me` | GET | 내 정보 조회 |
| `/api/v1/users/` | GET | 사용자 목록 (페이지네이션) |

## 5. Redis 데이터 구조

```
refresh_token:{user_id}:{token_id} = {
  "user_id": 123,
  "expires_at": "2025-02-05T00:00:00Z",
  "created_at": "2024-12-29T00:00:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}

TTL: 7일 (604800초)
```

## 6. 프론트엔드 구현

### 6.1 Axios 인터셉터
```typescript
// Request: Bearer token 자동 주입
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response: 401 시 자동 토큰 갱신
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const newToken = await refreshToken();
      if (newToken) {
        return axios.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

### 6.2 Zustand Store
```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  login: (email, password) => Promise<void>;
  logout: () => void;
}
```

---

## 7. 관련 문서 가이드

이 문서를 읽은 후, 작업하려는 내용에 따라 다음 specs 문서를 참고하세요:

| 작업 내용 | 참조할 specs 문서 |
|-----------|------------------|
| **API 엔드포인트 구현** | `specs/api-endpoints.md` |
| **토큰 관리 로직 수정** | `specs/token-management.md` |
| **레이트 리밋 설정** | `specs/rate-limiting.md` |
| **암호화 방식 확인** | `specs/encryption.md` |

### 다른 도메인과의 연계

| 연계 작업 | 참조할 도메인 |
|-----------|--------------|
| **거래소 API 키 암호화 저장** | [../06-data/index.md](../06-data/index.md) → `credentials` 테이블 |
| **클레이튼 지갑 연동** | [../05-blockchain/index.md](../05-blockchain/index.md) |

---

*최종 업데이트: 2025-12-29*
