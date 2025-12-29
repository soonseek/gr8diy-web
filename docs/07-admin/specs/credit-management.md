# 크레딧 관리 (Credit Management)

관리자의 크레딧 관리 기능 명세입니다.

---

## 1. 개요

### 1.1 기능

- **크레딧 충전** (사용자 계정)
- **크레딧 환불**
- **크레딧 내역 조회**
- **크레딧 통계**

---

## 2. API 명세

### 2.1 크레딧 충전

```python
# apps/api/app/api/v1/admin/credits.py
@router.post("/credits/charge")
async def charge_credits(
    user_id: UUID,
    amount: int,
    description: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    크레딧 충전

    Request Body:
    - user_id: 사용자 ID
    - amount: 충전할 크레딧 수량
    - description: 충전 사유

    Returns:
    - {success: bool, new_balance: int, transaction_id: UUID}
    """
    result = await credit_service.add_credits(
        db=db,
        user_id=user_id,
        amount=amount,
        type="ADMIN_CHARGE",
        description=description
    )

    # 알림 발송
    await notification_service.send_credits_charged(
        user_id=user_id,
        amount=amount,
        balance=result["new_balance"]
    )

    return result
```

### 2.2 크레딧 환불

```python
@router.post("/credits/refund")
async def refund_credits(
    user_id: UUID,
    amount: int,
    reason: str,
    reference_id: UUID | None = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    크레딧 환불

    Request Body:
    - user_id: 사용자 ID
    - amount: 환불할 크레딧 수량
    - reason: 환불 사유
    - reference_id: 관련 거래 ID (선택)

    Returns:
    - {success: bool, new_balance: int, transaction_id: UUID}
    """
    result = await credit_service.add_credits(
        db=db,
        user_id=user_id,
        amount=amount,
        type="ADMIN_REFUND",
        description=reason,
        reference_id=reference_id
    )

    return result
```

### 2.3 사용자 크레딧 내역

```python
@router.get("/credits/{user_id}/transactions", response_model=list[schemas.CreditTransactionOut])
async def get_user_credit_transactions(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 크레딧 거래 내역 조회

    Path Parameters:
    - user_id: 사용자 ID

    Query Parameters:
    - skip: 건너뛸 레코드 수
    - limit: 최대 반환 레코드 수

    Returns:
    - list[CreditTransactionOut]: 거래 내역
    """
    transactions = await credit_service.get_transactions(
        db, user_id, skip=skip, limit=limit
    )
    return transactions
```

### 2.4 크레딧 통계

```python
@router.get("/credits/stats")
async def get_credit_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    크레딧 통계 조회

    Returns:
    {
        total_users: int,           # 전체 사용자 수
        total_balance: int,         # 전체 크레딧 잔액
        total_charged: int,         # 누적 충전액
        total_consumed: int,        # 누적 소비액
        average_balance: float,     # 평균 잔액
        active_users: int           # 활성 사용자 (거래 1회 이상)
    }
    """
    stats = await credit_service.get_stats(db)
    return stats
```

---

## 3. 프론트엔드 연동

### 3.1 크레딧 관리 페이지

```typescript
// app/admin/credits/page.tsx
export default function AdminCreditsPage() {
  return (
    <div className="container">
      <h1>크레딧 관리</h1>

      {/* 통계 카드 */}
      <CreditStatsCards />

      {/* 충전/환불 폼 */}
      <CreditActionForm />

      {/* 거래 내역 검색 */}
      <TransactionSearch />
    </div>
  );
}
```

### 3.2 충전 폼

```typescript
// components/admin/CreditChargeForm.tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function CreditChargeForm() {
  const queryClient = useQueryClient();

  const chargeMutation = useMutation({
    mutationFn: (data: {
      userId: string;
      amount: number;
      description: string;
    }) => api.post("/admin/credits/charge", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credit-stats"] });
      alert("충전 완료");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        chargeMutation.mutate({
          userId: formData.get("userId") as string,
          amount: parseInt(formData.get("amount") as string),
          description: formData.get("description") as string,
        });
      }}
    >
      <input name="userId" placeholder="사용자 ID" required />
      <input
        name="amount"
        type="number"
        placeholder="충전할 크레딧"
        required
      />
      <input
        name="description"
        placeholder="사유"
        required
      />
      <button type="submit" disabled={chargeMutation.isPending}>
        충전
      </button>
    </form>
  );
}
```

---

## 4. 크레딧 정책

### 4.1 충전 기준

| 상황 | 크레딧 | 설명 |
|------|--------|------|
| **초기 가입** | 1000 | 신규 사용자 지급 |
| **이벤트 참여** | 100~500 | 프로모션 |
| **환불** | 거래액 전체 | 문제 발생 시 |
| **관리자 충전** | 가변 | 운영자 재량 |

### 4.2 차감 기준

| 항목 | 크레딧 | 설명 |
|------|--------|------|
| **백테스트** | 10 | 1회 실행 |
| **전략 실행** | 1 | 주문 1회당 |
| **템플릿 복제** | 100~500 | 저작권료 |

---

## 5. 상위/관련 문서

- **[../index.md](../index.md)** - 관리자 기능 개요
- **[../../06-data/specs/table-schemas.md](../../06-data/specs/table-schemas.md)** - credits, credit_transactions 테이블

---

*최종 업데이트: 2025-12-29*
