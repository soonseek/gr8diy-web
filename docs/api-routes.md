# API 라우트 (API Routes)

## 개요

FastAPI의 APIRouter를 사용하여 버전별로 라우트를 관리합니다. 현재 v1 API를 제공하며, RESTful 원칙을 따릅니다.

상세 API 명세는 각 도메인의 `specs/` 폴더를 참고하세요.

---

## API 엔드포인트 개요

### 1. 인증 (/api/v1/auth)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| POST | `/register` | 회원가입 | X |
| POST | `/login` | 로그인 | X |
| POST | `/refresh` | 토큰 갱신 (httpOnly 쿠키) | X |
| POST | `/logout` | 로그아웃 | O |

**상세**: [docs/02-authentication/specs/api-endpoints.md](./02-authentication/specs/api-endpoints.md)

---

### 2. 사용자 (/api/v1/users)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/me` | 내 정보 조회 | O |
| GET | `/` | 사용자 목록 (페이지네이션) | O (Admin) |
| PATCH | `/me` | 내 정보 수정 | O |
| DELETE | `/me` | 회원 탈퇴 | O |

---

### 3. 전략 (/api/v1/strategies)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/` | 전략 목록 (페이지네이션, 필터링) | O |
| POST | `/` | 전략 생성 | O |
| GET | `/{id}` | 전략 상세 조회 | O |
| PATCH | `/{id}` | 전략 수정 | O |
| DELETE | `/{id}` | 전략 삭제 | O |
| POST | `/{id}/deploy` | 전략 배포 | O |
| POST | `/{id}/pause` | 전략 일시정지 | O |

**상세**: [docs/03-strategy/specs/api-endpoints.md](./03-strategy/specs/api-endpoints.md)

---

### 4. 백테스트 (/api/v1/backtests)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| POST | `/` | 백테스트 요청 | O |
| GET | `/` | 백테스트 목록 조회 | O |
| GET | `/{id}` | 백테스트 결과 조회 | O |
| DELETE | `/{id}` | 백테스트 삭제 | O |

**상세**: [docs/04-backtesting/specs/api-endpoints.md](./04-backtesting/specs/api-endpoints.md)

---

### 5. 실행 (/api/v1/executions)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/` | 실행 내역 조회 (페이지네이션) | O |
| GET | `/{id}` | 실행 상세 조회 | O |
| POST | `/{id}/cancel` | 실행 취소 | O |

---

### 6. 템플릿 (/api/v1/templates)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/` | 공개 템플릿 목록 조회 | O |
| POST | `/strategies/{id}/publish` | 전략을 템플릿으로 공개 | O |
| POST | `/{id}/clone` | 템플릿 복제 (결제) | O |
| PATCH | `/{id}` | 템플릿 수정 (가격, 설명) | O (Author only) |
| DELETE | `/{id}` | 템플릿 삭제 | O (Author only) |

---

### 7. 크레딧 (/api/v1/credits)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/` | 내 크레딧 잔액 조회 | O |
| GET | `/transactions` | 거래 내역 조회 | O |
| POST | `/charge` | 크레딧 충전 (fiat/crypto) | O |

---

### 8. Credential (/api/v1/credentials)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/` | 등록된 Credential 목록 조회 | O |
| POST | `/` | Credential 등록 (암호화 저장) | O |
| PATCH | `/{id}` | Credential 수정 | O |
| DELETE | `/{id}` | Credential 삭제 | O |

---

### 9. 시장 데이터 (/api/v1/market)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/ohlcv` | OHLCV 데이터 조회 | O |
| GET | `/symbols` | 지원되는 거래쌍 목록 | O |

---

### 10. 관리자 (/api/v1/admin)
| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/users` | 사용자 관리 목록 | Admin |
| PATCH | `/users/{id}` | 사용자 정보/Tier 수정 | Admin |
| GET | `/strategies` | 전략 검토 목록 | Admin |
| PATCH | `/strategies/{id}/review` | 전략 승인/거절 | Admin |
| GET | `/credits` | 크레딧 관리 | Admin |
| POST | `/credits/{user_id}` | 크레딧 지급/차감 | Admin |
| GET | `/royalties` | 저작권료 정산 내역 | Admin |
| POST | `/royalties/{year}/{month}` | 월별 정산 실행 | Admin |

**상세**: [docs/07-admin/specs/](./07-admin/specs/)

---

## 시스템 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 루트 (환영 메시지) |
| GET | `/health` | 헬스체크 (Redis, DB 상태 포함) |

---

## 응답 포맷

### 성공
```json
{ "access_token": "...", "token_type": "bearer", "expires_in": 1800 }
```

### 에러
```json
{
  "detail": "에러 메시지"
}
```

### 페이지네이션
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

---

## 레이트 리밋

| 엔드포인트 | 제한 |
|-----------|------|
| `/login` | 5회/분 |
| `/register` | 3회/5분 |
| `/refresh` | 10회/분 |
| 기타 | 100회/분 |

---

## 인증 방식

### Bearer Token (Access Token)
```
Authorization: Bearer {access_token}
```

### httpOnly 쿠키 (Refresh Token)
```
Cookie: refresh_token={value}
```

---

## 주요 파일

| 파일 | 설명 |
|------|------|
| `apps/api/app/api/v1/auth.py` | 인증 API |
| `apps/api/app/api/v1/users.py` | 사용자 API |
| `apps/api/app/api/v1/strategies.py` | 전략 API |
| `apps/api/app/api/v1/backtests.py` | 백테스트 API |
| `apps/api/app/api/v1/executions.py` | 실행 API |
| `apps/api/app/api/v1/templates.py` | 템플릿 API |
| `apps/api/app/api/v1/credits.py` | 크레딧 API |
| `apps/api/app/api/v1/credentials.py` | Credential API |
| `apps/api/app/api/v1/market.py` | 시장 데이터 API |
| `apps/api/app/api/v1/admin.py` | 관리자 API |
| `apps/api/app/main.py` | FastAPI 앱 |

---

## 관련 문서

- **[./02-authentication/specs/api-endpoints.md](./02-authentication/specs/api-endpoints.md)** - 인증 API 상세
- **[./03-strategy/specs/api-endpoints.md](./03-strategy/specs/api-endpoints.md)** - 전략 API 상세
- **[./04-backtesting/specs/api-endpoints.md](./04-backtesting/specs/api-endpoints.md)** - 백테스트 API 상세
- **[./07-admin/specs/](./07-admin/specs/)** - 관리자 API 상세

---

*최종 업데이트: 2025-12-29*
