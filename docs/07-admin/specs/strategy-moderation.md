# 전략 검토 (Strategy Moderation)

관리자의 전략 검토 및 승인 기능 명세입니다.

---

## 1. 개요

### 1.1 기능

- **전략 검토 대기 목록**
- **전략 상세 조회 및 검토**
- **승인/거절 처리**
- **비공개 처리**

### 1.2 전략 상태

| 상태 | 설명 | 다음 상태 |
|------|------|-----------|
| **DRAFT** | 작성 중 | PENDING_REVIEW |
| **PENDING_REVIEW** | 검토 대기 | VERIFIED, REJECTED |
| **VERIFIED** | 승인 완료 | ACTIVE |
| **ACTIVE** | 활성화 | PAUSED, SUSPENDED |
| **REJECTED** | 거절 | DRAFT (수정 후 재요청) |
| **SUSPENDED** | 정지 | ACTIVE |

---

## 2. API 명세

### 2.1 검토 대기 목록

```python
# apps/api/app/api/v1/admin/strategies.py
@router.get("/strategies/pending", response_model=list[schemas.StrategyOut])
async def list_pending_strategies(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    검토 대기 전략 목록 조회

    Query Parameters:
    - skip: 건너뛸 레코드 수
    - limit: 최대 반환 레코드 수

    Returns:
    - list[StrategyOut]: 검토 대기 전략 목록
    """
    strategies = await strategy_service.get_pending_strategies(
        db, skip=skip, limit=limit
    )
    return strategies
```

### 2.2 전략 상세 조회 (관리자용)

```python
@router.get("/strategies/{strategy_id}", response_model=schemas.AdminStrategyDetail)
async def get_strategy_detail(
    strategy_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    전략 상세 조회 (관리자용)

    Path Parameters:
    - strategy_id: 전략 ID

    Returns:
    - AdminStrategyDetail: 전략 상세 (검토 정보 포함)
    """
    strategy = await strategy_service.get_strategy_admin(db, strategy_id)

    # 검토 정보 추가
    review_info = {
        "author": strategy.user.full_name,
        "author_email": strategy.user.email,
        "submitted_at": strategy.created_at,
        "backtest_results": strategy.backtests,
        "clone_count": strategy.template.clone_count if strategy.template else 0,
    }

    return {**strategy.__dict__, "review_info": review_info}
```

### 2.3 전략 승인

```python
@router.post("/strategies/{strategy_id}/approve")
async def approve_strategy(
    strategy_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    전략 승인

    Path Parameters:
    - strategy_id: 전략 ID

    Returns:
    - {success: bool, message: str}
    """
    strategy = await strategy_service.get_strategy(db, strategy_id)

    # 상태 변경: PENDING_REVIEW -> VERIFIED
    strategy.status = "VERIFIED"
    await db.commit()

    # 저작자에게 알림
    await notification_service.send_strategy_approved(
        user_id=strategy.user_id,
        strategy_id=strategy_id,
        strategy_name=strategy.name
    )

    return {"success": True, "message": "Strategy approved"}
```

### 2.4 전략 거절

```python
@router.post("/strategies/{strategy_id}/reject")
async def reject_strategy(
    strategy_id: UUID,
    reason: str,  # 거절 사유
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    전략 거절

    Path Parameters:
    - strategy_id: 전략 ID

    Request Body:
    - reason: 거절 사유

    Returns:
    - {success: bool, message: str}
    """
    strategy = await strategy_service.get_strategy(db, strategy_id)

    # 상태 변경: PENDING_REVIEW -> REJECTED
    strategy.status = "REJECTED"

    # 거절 사유 저장
    await strategy_service.add_rejection_reason(
        db, strategy_id, reason
    )

    await db.commit()

    # 저작자에게 알림
    await notification_service.send_strategy_rejected(
        user_id=strategy.user_id,
        strategy_id=strategy_id,
        strategy_name=strategy.name,
        reason=reason
    )

    return {"success": True, "message": "Strategy rejected"}
```

### 2.5 전략 비공개 처리

```python
@router.post("/strategies/{strategy_id}/unlist")
async def unlist_strategy(
    strategy_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    전략 비공개 처리

    Path Parameters:
    - strategy_id: 전략 ID

    Returns:
    - {success: bool, message: str}
    """
    strategy = await strategy_service.get_strategy(db, strategy_id)

    # 템플릿 비활성화
    if strategy.template:
        strategy.template.is_active = False

    strategy.status = "SUSPENDED"
    await db.commit()

    return {"success": True, "message": "Strategy unlisted"}
```

---

## 3. 프론트엔드 연동

### 3.1 검토 대기 목록 페이지

```typescript
// app/admin/strategies/pending/page.tsx
export default function PendingStrategiesPage() {
  return (
    <div className="container">
      <h1>전략 검토 대기</h1>

      <StrategyList
        status="PENDING_REVIEW"
        showActions={true}
      />
    </div>
  );
}
```

### 3.2 전략 검토 모달

```typescript
// components/admin/StrategyReviewModal.tsx
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Props {
  strategyId: string;
  onClose: () => void;
}

export function StrategyReviewModal({ strategyId, onClose }: Props) {
  const queryClient = useQueryClient();

  const { data: strategy } = useQuery({
    queryKey: ["admin-strategy", strategyId],
    queryFn: () =>
      api.get(`/admin/strategies/${strategyId}`).then(r => r.data),
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      api.post(`/admin/strategies/${strategyId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-strategies"] });
      onClose();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (reason: string) =>
      api.post(`/admin/strategies/${strategyId}/reject`, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-strategies"] });
      onClose();
    },
  });

  if (!strategy) return <div>Loading...</div>;

  return (
    <div className="modal">
      <h2>{strategy.name}</h2>

      {/* 전략 정보 */}
      <StrategyInfo strategy={strategy} />

      {/* 백테스트 결과 */}
      <BacktestResults results={strategy.backtests} />

      {/* 승인/거절 버튼 */}
      <div className="actions">
        <button onClick={() => approveMutation.mutate()}>
          승인
        </button>
        <RejectButton
          onReject={(reason) => rejectMutation.mutate(reason)}
        />
      </div>
    </div>
  );
}
```

---

## 4. 검토 가이드라인

### 4.1 승인 기준

| 항목 | 기준 |
|------|------|
| **백테스트 결과** | 최소 6개월 데이터, 샤프 비율 1.0 이상 |
| **전략 안정성** | MDD 30% 이하 |
| **설명 명확성** | 전략 로직 설명 충분 |
| **저작권** | 타인의 전략 무단 복제 없음 |

### 4.2 거절 사유

| 사유 | 설명 |
|------|------|
| **데이터 부족** | 백테스트 기간 부족 |
| **성능 미달** | 샤프 비율 1.0 미만 |
| **리스크 과다** | MDD 30% 초과 |
| **설명 부족** | 전략 로직 설명 불충분 |
| **저작권 침해** | 타인의 전략 복제 의심 |

---

## 5. 알림 시스템

### 5.1 승인 알림

```python
# apps/api/app/services/notifications.py
async def send_strategy_approved(
    user_id: UUID,
    strategy_id: UUID,
    strategy_name: str
):
    """
    전략 승인 알림

    Notification:
    - 귀하의 전략 "{strategy_name}"이 승인되었습니다.
    - 마켓플레이스에 공개됩니다.
    """
    await create_notification(
        user_id=user_id,
        type="STRATEGY_APPROVED",
        title="전략 승인 완료",
        message=f'전략 "{strategy_name}"이 승인되었습니다.',
        link={`/strategies/${strategy_id}`
    )
```

### 5.2 거절 알림

```python
async def send_strategy_rejected(
    user_id: UUID,
    strategy_id: UUID,
    strategy_name: str,
    reason: str
):
    """
    전략 거절 알림

    Notification:
    - 귀하의 전략 "{strategy_name}"이 거절되었습니다.
    - 사유: {reason}
    """
    await create_notification(
        user_id=user_id,
        type="STRATEGY_REJECTED",
        title="전략 검토 결과",
        message=f'전략 "{strategy_name}"이 거절되었습니다. 사유: {reason}',
        link={`/strategies/${strategy_id}/edit`}
    )
```

---

## 6. 상위/관련 문서

- **[../index.md](../index.md)** - 관리자 기능 개요
- **[../../03-strategy/](../../03-strategy/)** - 전략 관리 시스템

---

*최종 업데이트: 2025-12-29*
