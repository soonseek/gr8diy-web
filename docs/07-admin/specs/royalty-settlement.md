# 저작권료 정산 (Royalty Settlement)

관리자의 월별 저작권료 정산 및 지급 기능 명세입니다.

---

## 1. 개요

### 1.1 기능

- **월별 저작권료 집계**
- **저작권료 정산 생성**
- **저작권료 지급 처리**
- **정산 내역 조회**

### 1.2 정산 주기

- **주기**: 매월 1일
- **대상**: 전월 템플릿 판매 수익
- **지급**: 크레딧으로 자동 지급

---

## 2. 데이터 모델

### 2.1 author_royalties 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| author_id | UUID | FK → users(id) |
| year | INTEGER | 년도 |
| month | INTEGER | 월 (1~12) |
| total_clones | INTEGER | 해당 월 복제 횟수 |
| total_revenue_credits | INTEGER | 총 수익 (크레딧) |
| royalty_rate_bps | INTEGER | 저작권료율 (1000 = 10%) |
| royalty_amount_credits | INTEGER | 지급할 저작권료 |
| status | VARCHAR(20) | PENDING, PAID, CANCELLED |
| paid_at | TIMESTAMPTZ | 지급 일시 |
| created_at | TIMESTAMPTZ | 생성 일시 |

---

## 3. API 명세

### 3.1 월별 저작권료 집계

```python
# apps/api/app/api/v1/admin/royalties.py
@router.post("/royalties/calculate")
async def calculate_monthly_royalties(
    year: int,
    month: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    월별 저작권료 집계

    Request Body:
    - year: 년도
    - month: 월 (1~12)

    Returns:
    {
        total_authors: int,        # 대상 저작자 수
        total_revenue: int,        # 총 수익
        total_royalties: int,      # 총 저작권료
        royalties: list[RoyaltySummary]
    }
    """
    result = await royalty_service.calculate_monthly(db, year, month)
    return result
```

### 3.2 정산 생성

```python
@router.post("/royalties/create")
async def create_royalty_settlements(
    year: int,
    month: int,
    confirm: bool = False,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    저작권료 정산 생성

    Request Body:
    - year: 년도
    - month: 월 (1~12)
    - confirm: 확정 여부 (True면 DB에 저장)

    Returns:
    {
        created_count: int,
        total_royalties: int,
        settlements: list[RoyaltyOut]
    }
    """
    # 1. 집계
    royalties = await royalty_service.calculate_monthly(db, year, month)

    if not confirm:
        # 미리보기만 반환
        return {
            "created_count": 0,
            "total_royalties": sum(r["royalty_amount"] for r in royalties),
            "settlements": royalties
        }

    # 2. DB 저장
    created = []
    for royalty in royalties:
        record = await royalty_service.create_settlement(
            db=db,
            author_id=royalty["author_id"],
            year=year,
            month=month,
            total_clones=royalty["total_clones"],
            total_revenue=royalty["total_revenue"],
            royalty_amount=royalty["royalty_amount"]
        )
        created.append(record)

    await db.commit()

    return {
        "created_count": len(created),
        "total_royalties": sum(r.royalty_amount_credits for r in created),
        "settlements": created
    }
```

### 3.3 저작권료 지급

```python
@router.post("/royalties/{royalty_id}/pay")
async def pay_royalty(
    royalty_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    저작권료 지급

    Path Parameters:
    - royalty_id: 저작권료 정산 ID

    Returns:
    {success: bool, transaction_id: UUID}
    """
    royalty = await royalty_service.get_royalty(db, royalty_id)

    if royalty.status != "PENDING":
        raise HTTPException(400, "Already paid or cancelled")

    # 크레딧 지급
    result = await credit_service.add_credits(
        db=db,
        user_id=royalty.author_id,
        amount=royalty.royalty_amount_credits,
        type="ROYALTY_PAYMENT",
        description=f"{royalty.year}년 {royalty.month}월 저작권료",
        reference_id=royalty_id
    )

    # 상태 업데이트
    royalty.status = "PAID"
    royalty.paid_at = datetime.now(tz=UTC)
    await db.commit()

    # 알림
    await notification_service.send_royalty_paid(
        user_id=royalty.author_id,
        year=royalty.year,
        month=royalty.month,
        amount=royalty.royalty_amount_credits
    )

    return result
```

### 3.4 일괄 지급

```python
@router.post("/royalties/batch-pay")
async def batch_pay_royalties(
    year: int,
    month: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    해당 월 모든 저작권료 일괄 지급

    Request Body:
    - year: 년도
    - month: 월 (1~12)

    Returns:
    {
        paid_count: int,
        total_amount: int,
        failed: list[failed_items]
    }
    """
    royalties = await royalty_service.get_pending_royalties(db, year, month)

    paid_count = 0
    total_amount = 0
    failed = []

    for royalty in royalties:
        try:
            await credit_service.add_credits(
                db=db,
                user_id=royalty.author_id,
                amount=royalty.royalty_amount_credits,
                type="ROYALTY_PAYMENT",
                description=f"{year}년 {month}월 저작권료",
                reference_id=royalty.id
            )

            royalty.status = "PAID"
            royalty.paid_at = datetime.now(tz=UTC)

            paid_count += 1
            total_amount += royalty.royalty_amount_credits

        except Exception as e:
            failed.append({
                "royalty_id": str(royalty.id),
                "author_id": str(royalty.author_id),
                "error": str(e)
            })

    await db.commit()

    return {
        "paid_count": paid_count,
        "total_amount": total_amount,
        "failed": failed
    }
```

### 3.5 정산 내역 조회

```python
@router.get("/royalties", response_model=list[schemas.RoyaltyOut])
async def list_royalties(
    year: int | None = None,
    month: int | None = None,
    author_id: UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    저작권료 정산 내역 조회

    Query Parameters:
    - year: 년도 필터
    - month: 월 필터
    - author_id: 저작자 필터
    - status: 상태 필터 (PENDING, PAID, CANCELLED)
    - skip: 건너뛸 레코드 수
    - limit: 최대 반환 레코드 수

    Returns:
    - list[RoyaltyOut]: 저작권료 정산 목록
    """
    royalties = await royalty_service.list_royalties(
        db,
        year=year,
        month=month,
        author_id=author_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return royalties
```

---

## 4. 프론트엔드 연동

### 4.1 저작권료 정산 페이지

```typescript
// app/admin/royalties/page.tsx
export default function RoyaltySettlementPage() {
  return (
    <div className="container">
      <h1>저작권료 정산</h1>

      {/* 월 선택 */}
      <MonthSelector
        onSelect={(year, month) => {
          // 해당 월 정산 내역 로드
        }}
      />

      {/* 정산 통계 */}
      <RoyaltyStatsCards />

      {/* 정산 목록 */}
      <RoyaltyTable />

      {/* 일괄 지급 버튼 */}
      <BatchPayButton />
    </div>
  );
}
```

### 4.2 정산 집계 모달

```typescript
// components/admin/RoyaltyCalculationModal.tsx
"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Props {
  year: number;
  month: number;
  onClose: () => void;
  onConfirm: () => void;
}

export function RoyaltyCalculationModal({
  year,
  month,
  onClose,
  onConfirm
}: Props) {
  const calculateMutation = useMutation({
    mutationFn: () =>
      api.post("/admin/royalties/calculate", { year, month }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post("/admin/royalties/create", {
        year,
        month,
        confirm: true,
      }),
    onSuccess: () => {
      onConfirm();
      onClose();
    },
  });

  return (
    <div className="modal">
      <h2>{year}년 {month}월 저작권료 정산</h2>

      {calculateMutation.data ? (
        <>
          <div className="summary">
            <p>대상 저작자: {calculateMutation.data.total_authors}명</p>
            <p>총 수익: {calculateMutation.data.total_revenue} 크레딧</p>
            <p>총 저작권료: {calculateMutation.data.total_royalties} 크레딧</p>
          </div>

          <table className="royalty-list">
            <thead>
              <tr>
                <th>저작자</th>
                <th>복제 횟수</th>
                <th>수익</th>
                <th>저작권료</th>
              </tr>
            </thead>
            <tbody>
              {calculateMutation.data.royalties.map((r: any) => (
                <tr key={r.author_id}>
                  <td>{r.author_name}</td>
                  <td>{r.total_clones}</td>
                  <td>{r.total_revenue}</td>
                  <td>{r.royalty_amount}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="actions">
            <button onClick={onClose}>취소</button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending}
            >
              정산 확정 생성
            </button>
          </div>
        </>
      ) : (
        <button onClick={() => calculateMutation.mutate()}>
          집계 시작
        </button>
      )}
    </div>
  );
}
```

---

## 5. 정산 스케줄러

### 5.1 월초 자동 집계

```python
# apps/api/app/tasks/royalty_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def monthly_royalty_calculation():
    """
    매월 1일 오전 2시에 저작권료 자동 집계
    """
    today = datetime.now(tz=UTC)
    last_month = today.replace(day=1) - timedelta(days=1)

    year = last_month.year
    month = last_month.month

    # 집계만 수행 (지급 X)
    result = await royalty_service.calculate_monthly(db, year, month)

    # 관리자에게 알림
    await notification_service.send_royalty_calculation_complete(
        total_authors=result["total_authors"],
        total_royalties=result["total_royalties"],
        year=year,
        month=month
    )

# 스케줄 등록: 매월 1일 02:00
scheduler.add_job(
    monthly_royalty_calculation,
    'cron',
    day=1,
    hour=2,
    minute=0
)
```

---

## 6. 알림 시스템

### 6.1 지급 완료 알림

```python
async def send_royalty_paid(
    user_id: UUID,
    year: int,
    month: int,
    amount: int
):
    """
    저작권료 지급 알림

    Notification:
    - {year}년 {month}월 저작권료 {amount} 크레딧이 지급되었습니다.
    """
    await create_notification(
        user_id=user_id,
        type="ROYALTY_PAID",
        title="저작권료 지급 완료",
        message=f"{year}년 {month}월 저작권료 {amount} 크레딧이 지급되었습니다.",
        link="/my-royalties"
    )
```

---

## 7. 상위/관련 문서

- **[../index.md](../index.md)** - 관리자 기능 개요
- **[../../06-data/specs/table-schemas.md](../../06-data/specs/table-schemas.md)** - author_royalties 테이블

---

*최종 업데이트: 2025-12-29*
