# 암호화 (Encryption)

## 1. 비밀번호 해싱

### 1.1 bcrypt

**알고리즘**: bcrypt
**cost factor**: 12
**이유**: GPU 공격 저항, 조정 가능한 계산 비용

### 1.2 구현

```python
import bcrypt

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

---

## 2. API 키 암호화

### 2.1 AES-256-GCM

**알고리즘**: AES-256-GCM (Galois/Counter Mode)
**용도**: LLM API 키, 거래소 API 키
**특징**: 인증된 암호화 (AEAD)

### 2.2 키 파생

```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os

def derive_key(secret: str, salt: bytes = None) -> bytes:
    """SECRET_KEY에서 AES 키 파생"""
    if salt is None:
        salt = b'salt_value'  # 환경변수에서 가져올 것

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=10000,
        backend=default_backend()
    )
    return kdf.derive(secret.encode('utf-8'))
```

### 2.3 암호화/복호화

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_api_key(api_key: str, key: bytes) -> bytes:
    """API 키 암호화"""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96 bits nonce
    ciphertext = aesgcm.encrypt(nonce, api_key.encode('utf-8'), None)
    return nonce + ciphertext

def decrypt_api_key(encrypted_key: bytes, key: bytes) -> str:
    """API 키 복호화"""
    aesgcm = AESGCM(key)
    nonce = encrypted_key[:12]
    ciphertext = encrypted_key[12:]
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode('utf-8')
```

### 2.4 Pydantic Schema

```python
from pydantic import BaseModel, Field

class CredentialCreate(BaseModel):
    type: str  # "LLM" or "EXCHANGE"
    provider: str  # "OPENAI", "BINANCE", etc.
    api_key: str
    api_secret: str | None = None

    class Config:
        schema_extra = {
            "example": {
                "type": "LLM",
                "provider": "OPENAI",
                "api_key": "sk-...",
                "api_secret": None
            }
        }
```

---

## 3. 키 관리

### 3.1 환경변수

**.env**:
```bash
# JWT 서명 키 (최소 32자, 권장 64자 이상)
JWT_SECRET_KEY=your-secret-key-min-32-characters-long

# 암호화 키 파생용
SECRET_KEY=another-secret-key-for-derivation
```

### 3.2 Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 3.3 키 관리 모범 사례

| 구분 | 방법 |
|------|------|
| **개발 환경** | .env 파일 (gitignore) |
| **프로덕션** | 환경변수 또는 Secret Manager (AWS Secrets Manager) |
| **키 교체** | 주기적 교체 (권장 90일) |
| **키 강도** | 최소 32자 (권장 64자 이상) |

---

## 4. FastAPI Service

```python
from app.core.security import get_password_hash, encrypt_api_key
from app.models.credential import Credential

class CredentialService:
    async def create_credential(
        self,
        user_id: str,
        type: str,
        provider: str,
        api_key: str,
        api_secret: str | None,
        db: AsyncSession
    ) -> Credential:
        # 암호화
        key = derive_key(settings.SECRET_KEY)
        encrypted_key = encrypt_api_key(api_key, key)
        encrypted_secret = encrypt_api_key(api_secret, key) if api_secret else None

        # DB 저장
        credential = Credential(
            user_id=user_id,
            type=type,
            provider=provider,
            encrypted_api_key=encrypted_key,
            encrypted_api_secret=encrypted_secret
        )
        db.add(credential)
        await db.commit()
        await db.refresh(credential)

        return credential
```

---

## 5. 상위/관련 문서

- **[../index.md](../index.md)** - 인증 시스템 개요
- **[api-endpoints.md](./api-endpoints.md)** - API 엔드포인트 상세
- **[token-management.md](./token-management.md)** - 토큰 관리 상세
- **[rate-limiting.md](./rate-limiting.md)** - 레이트 리밋 상세

---

*최종 업데이트: 2025-12-29*
