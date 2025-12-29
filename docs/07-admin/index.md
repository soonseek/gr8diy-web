# 관리자 기능 (Admin)

관리자 전용 기능과 운영 도구에 대한 문서입니다.

---

## 1. 개요

### 1.1 관리자 역할

Great DIY의 관리자는 시스템 운영과 사용자 지원을 담당합니다.

| 역할 | 권한 | 대상 |
|------|------|------|
| **Superuser** | 전체 권한 | 시스템 관리자 |
| **Moderator** | 콘텐츠 관리 | 전략 검토, 승인 |
| **Support** | 사용자 지원 | 크레딧 지급, 문제 해결 |

### 1.2 환경별 차이

| 기능 | 개발 서버 | 운영 서버 |
|------|-----------|-----------|
| **가입 승인** | 필요 (MANUAL_APPROVAL) | 불필요 (PUBLIC) |
| **전략 검토** | 필요 | 필요 |
| **저작권료 정산** | 월별 수동 | 월별 수동 |

---

## 2. 주요 기능

### 2.1 사용자 관리

- **가입 승인** (개발 서버 전용)
- **사용자 활성/비활성**
- **권한 변경**

### 2.2 전략 관리

- **전략 검토 및 승인**
- **전략 비공개 처리**
- **저작자 문의 처리**

### 2.3 크레딧 관리

- **크레딧 충전**
- **크레딧 환불**
- **크레딧 내역 조회**

### 2.4 정산 관리

- **월별 저작권료 정산**
- **저작권료 지급 처리**
- **정산 내역 조회**

### 2.5 시스템 모니터링

- **시스템 상태 확인**
- **사용자 통계**
- **거래 통계**

---

## 3. 관련 문서

### 3.1 상세 명세 (specs)

| 문서 | 설명 |
|------|------|
| **[specs/user-management.md](./specs/user-management.md)** | 사용자 관리 기능 |
| **[specs/strategy-moderation.md](./specs/strategy-moderation.md)** | 전략 검토/승인 |
| **[specs/credit-management.md](./specs/credit-management.md)** | 크레딧 관리 |
| **[specs/royalty-settlement.md](./specs/royalty-settlement.md)** | 저작권료 정산 |
| **[specs/system-monitoring.md](./specs/system-monitoring.md)** | 시스템 모니터링 |

### 3.2 관련 시스템

- **[../02-authentication/](./../02-authentication/)** - 인증 시스템
- **[../03-strategy/](./../03-strategy/)** - 전략 관리
- **[../06-data/](./../06-data/)** - 데이터 모델

---

## 4. API 개요

### 4.1 인증

모든 관리자 API는 **관리자 권한**이 필요합니다:

```python
# apps/api/app/api/v1/dependencies.py
async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin access required")
    return current_user
```

### 4.2 API 라우트

| 경로 | 설명 |
|------|------|
| `/api/v1/admin/users` | 사용자 관리 |
| `/api/v1/admin/strategies` | 전략 관리 |
| `/api/v1/admin/credits` | 크레딧 관리 |
| `/api/v1/admin/royalties` | 저작권료 정산 |
| `/api/v1/admin/stats` | 통계 조회 |

---

*최종 업데이트: 2025-12-29*
