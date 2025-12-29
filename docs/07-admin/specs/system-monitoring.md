# 시스템 모니터링 (System Monitoring)

관리자를 위한 시스템 모니터링 및 통계 기능 명세입니다.

---

## 1. 개요

### 1.1 기능

- **시스템 상태 확인**
- **사용자 통계**
- **거래 통계**
- **전략 통계**
- **수익 통계**

---

## 2. API 명세

### 2.1 시스템 상태

```python
# apps/api/app/api/v1/admin/stats.py
@router.get("/stats/system")
async def get_system_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    시스템 상태 조회

    Returns:
    {
        uptime: str,                    # 가동 시간
        version: str,                   # 버전
        environment: str,               # 환경 (development/production)
        blockchain_enabled: bool,       # 블록체인 활성화 여부
        database_status: str,           # DB 상태
        redis_status: str,              # Redis 상태
        last_cron_run: datetime | None  # 마지막 크론 작업 시각
    }
    """
    return {
        "uptime": str(datetime.now(tz=UTC) - settings.START_TIME),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "blockchain_enabled": settings.BLOCKCHAIN_ENABLED,
        "database_status": "healthy" if await check_db(db) else "error",
        "redis_status": "healthy" if await check_redis() else "error",
        "last_cron_run": await get_last_cron_run(),
    }
```

### 2.2 사용자 통계

```python
@router.get("/stats/users")
async def get_user_stats(
    period: str = "7d",  # 1d, 7d, 30d, all
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 통계 조회

    Query Parameters:
    - period: 기간 (1d, 7d, 30d, all)

    Returns:
    {
        total_users: int,              # 전체 사용자 수
        new_users: int,                # 신규 사용자 수 (기간 내)
        active_users: int,             # 활성 사용자 수 (로그인 1회 이상)
        pending_approvals: int,        # 가입 대기 수 (개발 서버)
        superusers: int,               # 관리자 수
        growth_rate: float,            # 성장률 (%)
        chart: list[DailyStats]        # 일별 사용자 수 추이
    }
    """
    since = get_period_start(period)

    stats = {
        "total_users": await user_service.count_all(db),
        "new_users": await user_service.count_since(db, since),
        "active_users": await user_service.count_active(db, since),
        "pending_approvals": await user_service.count_pending(db) if settings.ENVIRONMENT == "development" else 0,
        "superusers": await user_service.count_superusers(db),
        "growth_rate": await calculate_growth_rate(db, period),
        "chart": await user_service.get_daily_stats(db, period),
    }

    return stats
```

### 2.3 거래 통계

```python
@router.get("/stats/executions")
async def get_execution_stats(
    period: str = "7d",
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    거래 통계 조회

    Query Parameters:
    - period: 기간 (1d, 7d, 30d, all)

    Returns:
    {
        total_executions: int,         # 전체 거래 수
        period_executions: int,        # 기간 내 거래 수
        success_rate: float,           # 성공률 (%)
        total_volume: Decimal,         # 총 거래량 (USDT)
        total_fees: int,               # 총 수수료 (크레딧)
        chart: list[DailyStats]        # 일별 거래량 추이
    }
    """
    since = get_period_start(period)

    stats = {
        "total_executions": await execution_service.count_all(db),
        "period_executions": await execution_service.count_since(db, since),
        "success_rate": await execution_service.get_success_rate(db, since),
        "total_volume": await execution_service.get_total_volume(db),
        "total_fees": await execution_service.get_total_fees(db),
        "chart": await execution_service.get_daily_stats(db, period),
    }

    return stats
```

### 2.4 전략 통계

```python
@router.get("/stats/strategies")
async def get_strategy_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    전략 통계 조회

    Returns:
    {
        total_strategies: int,         # 전체 전략 수
        active_strategies: int,        # 활성 전략 수
        public_strategies: int,        # 공개 전략 수
        pending_review: int,           # 검토 대기 수
        total_clones: int,             # 전체 복제 수
        top_authors: list[AuthorStats] # 상위 저작자
    }
    """
    return {
        "total_strategies": await strategy_service.count_all(db),
        "active_strategies": await strategy_service.count_by_status(db, "ACTIVE"),
        "public_strategies": await strategy_service.count_public(db),
        "pending_review": await strategy_service.count_by_status(db, "PENDING_REVIEW"),
        "total_clones": await template_service.count_total_clones(db),
        "top_authors": await strategy_service.get_top_authors(db, limit=10),
    }
```

### 2.5 수익 통계

```python
@router.get("/stats/revenue")
async def get_revenue_stats(
    period: str = "30d",
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    수익 통계 조회

    Query Parameters:
    - period: 기간 (1d, 7d, 30d, all)

    Returns:
    {
        total_revenue: int,            # 전체 수익 (크레딧)
        period_revenue: int,           # 기간 내 수익
        revenue_sources: {
            backtest: int,             # 백테스트 수익
            execution: int,            # 실행 수익
            template_clone: int        # 템플릿 복제 수익
        },
        chart: list[DailyStats]        # 일별 수익 추이
    }
    """
    since = get_period_start(period)

    stats = {
        "total_revenue": await credit_service.get_total_revenue(db),
        "period_revenue": await credit_service.get_revenue_since(db, since),
        "revenue_sources": {
            "backtest": await credit_service.get_revenue_by_type(db, "BACKTEST", since),
            "execution": await credit_service.get_revenue_by_type(db, "EXECUTION", since),
            "template_clone": await credit_service.get_revenue_by_type(db, "TEMPLATE_CLONE", since),
        },
        "chart": await credit_service.get_daily_revenue(db, period),
    }

    return stats
```

---

## 3. 프론트엔드 연동

### 3.1 대시보드 페이지

```typescript
// app/admin/dashboard/page.tsx
export default function AdminDashboard() {
  return (
    <div className="container">
      <h1>관리자 대시보드</h1>

      {/* 시스템 상태 카드 */}
      <SystemStatusCard />

      {/* 통계 카드 그리드 */}
      <div className="stats-grid">
        <UserStatsCard period="7d" />
        <ExecutionStatsCard period="7d" />
        <StrategyStatsCard />
        <RevenueStatsCard period="30d" />
      </div>

      {/* 차트 섹션 */}
      <div className="charts-section">
        <UserGrowthChart period="30d" />
        <ExecutionVolumeChart period="7d" />
        <RevenueChart period="30d" />
      </div>
    </div>
  );
}
```

### 3.2 시스템 상태 카드

```typescript
// components/admin/SystemStatusCard.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function SystemStatusCard() {
  const { data: stats } = useQuery({
    queryKey: ["admin-stats-system"],
    queryFn: () => api.get("/admin/stats/system").then(r => r.data),
    refetchInterval: 60000, // 1분마다 갱신
  });

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="status-card">
      <h2>시스템 상태</h2>

      <div className="status-items">
        <StatusItem label="환경" value={stats.environment} />
        <StatusItem
          label="블록체인"
          value={stats.blockchain_enabled ? "활성" : "비활성"}
        />
        <StatusItem label="DB" value={stats.database_status} />
        <StatusItem label="Redis" value={stats.redis_status} />
        <StatusItem label="가동 시간" value={stats.uptime} />
        <StatusItem label="버전" value={stats.version} />
      </div>
    </div>
  );
}

function StatusItem({ label, value }: { label: string; value: string }) {
  const isHealthy = ["healthy", "active", "활성"].includes(value);

  return (
    <div className="status-item">
      <span className="label">{label}</span>
      <span
        className={`value ${isHealthy ? "healthy" : "error"}`}
      >
        {value}
      </span>
    </div>
  );
}
```

### 3.3 통계 카드

```typescript
// components/admin/UserStatsCard.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function UserStatsCard({ period }: { period: string }) {
  const { data: stats } = useQuery({
    queryKey: ["admin-stats-users", period],
    queryFn: () =>
      api.get("/admin/stats/users", { params: { period }})
        .then(r => r.data),
  });

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="stats-card">
      <h3>사용자</h3>

      <div className="stat-item">
        <span className="label">전체 사용자</span>
        <span className="value">{stats.total_users}</span>
      </div>

      <div className="stat-item">
        <span className="label">신규 ({period})</span>
        <span className="value highlight">{stats.new_users}</span>
      </div>

      <div className="stat-item">
        <span className="label">활성 사용자</span>
        <span className="value">{stats.active_users}</span>
      </div>

      <div className="stat-item">
        <span className="label">성장률</span>
        <span className={`value ${stats.growth_rate >= 0 ? "positive" : "negative"}`}>
          {stats.growth_rate >= 0 ? "+" : ""}{stats.growth_rate}%
        </span>
      </div>

      {stats.pending_approvals > 0 && (
        <div className="stat-item warning">
          <span className="label">가입 대기</span>
          <span className="value">{stats.pending_approvals}</span>
        </div>
      )}
    </div>
  );
}
```

---

## 4. 차트 시각화

### 4.1 사용자 성장 차트

```typescript
// components/admin/UserGrowthChart.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { LineChart } from "@/components/charts";

export function UserGrowthChart({ period }: { period: string }) {
  const { data: stats } = useQuery({
    queryKey: ["admin-stats-users", period],
    queryFn: () =>
      api.get("/admin/stats/users", { params: { period }})
        .then(r => r.data),
  });

  if (!stats) return <div>Loading...</div>;

  const chartData = stats.chart.map((item: any) => ({
    date: item.date,
    value: item.count,
  }));

  return (
    <div className="chart-container">
      <h3>사용자 성장 추이</h3>
      <LineChart data={chartData} />
    </div>
  );
}
```

---

## 5. 경고 알림

### 5.1 시스템 경고

```python
# apps/api/app/services/alerts.py
async def check_system_alerts(db: AsyncSession):
    """
    시스템 경고 확인
    """
    alerts = []

    # DB 연결 확인
    if not await check_db(db):
        alerts.append({
            "type": "CRITICAL",
            "message": "Database connection failed",
        })

    # Redis 연결 확인
    if not await check_redis():
        alerts.append({
            "type": "WARNING",
            "message": "Redis connection failed",
        })

    # 크레딧 잔액 부족 사용자
    low_balance_users = await credit_service.get_low_balance_users(db, threshold=100)
    if len(low_balance_users) > 0:
        alerts.append({
            "type": "INFO",
            "message": f"{len(low_balance_users)} users have low balance (< 100)",
        })

    # 검토 대기 전략
    pending_strategies = await strategy_service.count_by_status(db, "PENDING_REVIEW")
    if pending_strategies > 10:
        alerts.append({
            "type": "INFO",
            "message": f"{pending_strategies} strategies pending review",
        })

    return alerts
```

---

## 6. 상위/관련 문서

- **[../index.md](../index.md)** - 관리자 기능 개요
- **[../../06-data/](../../06-data/)** - 데이터 모델

---

*최종 업데이트: 2025-12-29*
