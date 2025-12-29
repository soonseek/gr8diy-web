# API 라우트 (API Routes)

## 개요
FastAPI의 APIRouter를 사용하여 버전별로 라우트를 관리합니다. 현재 v1 API를 제공하며, RESTful 원칙을 따릅니다.

## 인증 (/api/v1/auth)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| POST | `/register` | 회원가입 | X |
| POST | `/login` | 로그인 | X |
| POST | `/refresh` | 토큰 갱신 | X |
| POST | `/logout` | 로그아웃 | O |

## 사용자 (/api/v1/users)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/me` | 내 정보 | O |
| GET | `/` | 사용자 목록 | X |

## 시스템
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 루트 (환영 메시지) |
| GET | `/health` | 헬스체크 (Redis 상태 포함) |

## 응답 포맷
### 성공
```json
{ "access_token": "...", "token_type": "bearer" }
```

### 에러
```json
{
  "error": {
    "message": "에러 메시지",
    "code": 422,
    "details": {}
  }
}
```

## 레이트 리밋
- `/login`: 5회/분
- `/register`: 3회/5분
- `/refresh`: 10회/분
- 기타: 100회/분

## 주요 파일
- `apps/api/app/api/v1/auth.py`
- `apps/api/app/api/v1/users.py`
- `apps/api/app/main.py`
