# 성과 지표 (Performance Metrics)

백테스팅 결과 분석을 위한 성과 지표 계산 상세 명세입니다.

---

## 1. 지표 개요

### 1.1 지표 분류

| 분류 | 지표 |
|------|------|
| **수익성** | 총 수익률, CAGR, 평균 수익/손실 |
| **리스크** | MDD, 변동성, 칼마 비율 |
| **효율성** | 샤프 비율, 승률, 손익비, 기대값 |
| **거래 통계** | 총 거래 횟수, 평균 보유 기간 |

---

## 2. 수익성 지표

### 2.1 총 수익률 (Total Return)

**수식**:
```
Total Return = (V_f - V_0) / V_0

V_0: 초기 자산 (Initial Capital)
V_f: 최종 자산 (Final Value)
```

**Python 구현**:
```python
def total_return(initial_capital: float, final_value: float) -> float:
    """총 수익률 계산"""
    return (final_value - initial_capital) / initial_capital
```

### 2.2 CAGR (Compound Annual Growth Rate)

**수식**:
```
CAGR = (V_f / V_0)^(1/n) - 1

n: 연도 수 (Days / 365)
```

**Python 구현**:
```python
import math

def cagr(
    initial_capital: float,
    final_value: float,
    days: int
) -> float:
    """연간 수익률 계산"""
    years = days / 365.0
    return (final_value / initial_capital) ** (1 / years) - 1
```

### 2.3 평균 수익/손실 (Average Profit/Loss)

**수식**:
```
Avg Profit = Σ_profit / N_profit
Avg Loss = Σ_loss / N_loss
```

**Python 구현**:
```python
def avg_profit_loss(trades: list[dict]) -> tuple[float, float]:
    """
    평균 수익/손실 계산

    Returns:
        (avg_profit, avg_loss)
    """
    profits = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
    losses = [abs(t['pnl']) for t in trades if t.get('pnl', 0) < 0]

    avg_profit = sum(profits) / len(profits) if profits else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    return avg_profit, avg_loss
```

---

## 3. 리스크 지표

### 3.1 MDD (Maximum Drawdown)

**정의**: 최고점에서 최저점까지의 최대 낙폭

**수식**:
```
Drawdown(t) = (H_t - L_t) / H_t

H_t: 시점 t까지의 고점 (Peak)
L_t: 시점 t의 저점 (Trough)

MDD = max(Drawdown)
```

**Python 구현**:
```python
def max_drawdown(equity_curve: list[dict]) -> float:
    """
    최대 낙폭 계산

    Args:
        equity_curve: [{'timestamp': ..., 'total_value': ...}, ...]

    Returns:
        MDD (0 ~ 1)
    """
    peak = -float('inf')
    max_dd = 0.0

    for point in equity_curve:
        value = point['total_value']

        # 고점 업데이트
        if value > peak:
            peak = value

        # 드로다운 계산
        if peak > 0:
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)

    return max_dd
```

### 3.2 변동성 (Volatility)

**수식**:
```
σ = sqrt(Σ(R_i - R̄)^2 / (n - 1))

R_i: i번째 기간 수익률
R̄: 평균 수익률
```

**Python 구현**:
```python
import numpy as np

def volatility(equity_curve: list[dict]) -> float:
    """수익률 표준편차 계산"""
    returns = []
    for i in range(1, len(equity_curve)):
        r = (
            equity_curve[i]['total_value'] - equity_curve[i-1]['total_value']
        ) / equity_curve[i-1]['total_value']
        returns.append(r)

    return np.std(returns, ddof=1) if returns else 0.0
```

### 3.3 칼마 비율 (Calmar Ratio)

**수식**:
```
Calmar Ratio = CAGR / MDD
```

**Python 구현**:
```python
def calmar_ratio(
    initial_capital: float,
    final_value: float,
    days: int,
    mdd: float
) -> float:
    """칼마 비율 계산"""
    cagr_value = cagr(initial_capital, final_value, days)
    return cagr_value / mdd if mdd > 0 else 0
```

---

## 4. 효율성 지표

### 4.1 샤프 비율 (Sharpe Ratio)

**수식**:
```
Sharpe Ratio = (R̄ - R_f) / σ

R̄: 평균 수익률
R_f: 무위험 이자율 (Risk-free Rate)
σ: 수익률 표준편차
```

**Python 구현**:
```python
def sharpe_ratio(
    equity_curve: list[dict],
    risk_free_rate: float = 0.02
) -> float:
    """
    샤프 비율 계산

    Args:
        equity_curve: 자산 곡선
        risk_free_rate: 연간 무위험 이자율 (default: 2%)
    """
    # 일일 수익률 계산
    returns = []
    for i in range(1, len(equity_curve)):
        r = (
            equity_curve[i]['total_value'] - equity_curve[i-1]['total_value']
        ) / equity_curve[i-1]['total_value']
        returns.append(r)

    if not returns:
        return 0.0

    # 연간화
    avg_return = np.mean(returns) * 365
    std_return = np.std(returns, ddof=1) * np.sqrt(365)

    # 무위험 이자율 조정
    excess_return = avg_return - risk_free_rate

    return excess_return / std_return if std_return > 0 else 0.0
```

### 4.2 승률 (Win Rate)

**수식**:
```
Win Rate = N_profit / N_total

N_profit: 수익 거래수
N_total: 전체 거래수
```

**Python 구현**:
```python
def win_rate(trades: list[dict]) -> float:
    """승률 계산"""
    if not trades:
        return 0.0

    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    return len(winning_trades) / len(trades)
```

### 4.3 손익비 (Profit Factor)

**수식**:
```
Profit Factor = Σ_profit / |Σ_loss|

Σ_profit: 총 수익
Σ_loss: 총 손실
```

**Python 구현**:
```python
def profit_factor(trades: list[dict]) -> float:
    """손익비 계산"""
    total_profit = sum(t['pnl'] for t in trades if t.get('pnl', 0) > 0)
    total_loss = abs(sum(t['pnl'] for t in trades if t.get('pnl', 0) < 0))

    return total_profit / total_loss if total_loss > 0 else 0.0
```

### 4.4 기대값 (Expected Value)

**수식**:
```
EV = (WR × Avg Profit) - ((1 - WR) × Avg Loss)

WR: 승률 (Win Rate)
```

**Python 구현**:
```python
def expected_value(trades: list[dict]) -> float:
    """기대값 계산 (평균 거래 수익)"""
    wr = win_rate(trades)
    avg_profit, avg_loss = avg_profit_loss(trades)

    return (wr * avg_profit) - ((1 - wr) * avg_loss)
```

---

## 5. 거래 통계

### 5.1 총 거래 횟수

```python
def total_trades(trades: list[dict]) -> int:
    """총 거래 횟수 (완료된 거래만)"""
    return len([t for t in trades if 'pnl' in t])
```

### 5.2 평균 보유 기간

```python
from datetime import timedelta

def avg_holding_period(trades: list[dict]) -> timedelta:
    """평균 보유 기간"""
    completed_trades = [
        t for t in trades
        if 'entry_time' in t and 'exit_time' in t
    ]

    if not completed_trades:
        return timedelta(0)

    total_duration = sum(
        (t['exit_time'] - t['entry_time']).total_seconds()
        for t in completed_trades
    )

    avg_seconds = total_duration / len(completed_trades)
    return timedelta(seconds=avg_seconds)
```

### 5.3 최대 연속 승/패

```python
def max_consecutive_win_loss(trades: list[dict]) -> tuple[int, int]:
    """
    최대 연속 승/패 계산

    Returns:
        (max_win_streak, max_loss_streak)
    """
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0

    for trade in trades:
        pnl = trade.get('pnl', 0)

        if pnl > 0:
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        elif pnl < 0:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)

    return max_win_streak, max_loss_streak
```

---

## 6. 통합 계산기

### 6.1 PerformanceCalculator

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PerformanceMetrics:
    """성과 지표 결과"""
    # 수익성
    total_return: float
    cagr: float
    avg_profit: float
    avg_loss: float

    # 리스크
    mdd: float
    volatility: float
    calmar_ratio: float

    # 효율성
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    expected_value: float

    # 거래 통계
    total_trades: int
    avg_holding_period: str
    max_win_streak: int
    max_loss_streak: int

class PerformanceCalculator:
    """성과 지표 계산기"""

    def calculate_all(
        self,
        trades: List[dict],
        equity_curve: List[dict],
        initial_capital: float
    ) -> PerformanceMetrics:
        """모든 지표 계산"""
        # 기간 계산
        if len(equity_curve) >= 2:
            start = equity_curve[0]['timestamp']
            end = equity_curve[-1]['timestamp']
            days = (end - start).days / 86400  # 밀리초 -> 일
        else:
            days = 1

        final_value = equity_curve[-1]['total_value'] if equity_curve else initial_capital

        # 수익성 지표
        total_ret = total_return(initial_capital, final_value)
        cagr_value = cagr(initial_capital, final_value, days)
        avg_prof, avg_ls = avg_profit_loss(trades)

        # 리스크 지표
        mdd_value = max_drawdown(equity_curve)
        vol_value = volatility(equity_curve)
        calmar = calmar_ratio(initial_capital, final_value, days, mdd_value)

        # 효율성 지표
        sharpe = sharpe_ratio(equity_curve)
        wr = win_rate(trades)
        pf = profit_factor(trades)
        ev = expected_value(trades)

        # 거래 통계
        total_trades_count = total_trades(trades)
        avg_hp = avg_holding_period(trades)
        max_win, max_loss = max_consecutive_win_loss(trades)

        return PerformanceMetrics(
            # 수익성
            total_return=total_ret,
            cagr=cagr_value,
            avg_profit=avg_prof,
            avg_loss=avg_ls,

            # 리스크
            mdd=mdd_value,
            volatility=vol_value,
            calmar_ratio=calmar,

            # 효율성
            sharpe_ratio=sharpe,
            win_rate=wr,
            profit_factor=pf,
            expected_value=ev,

            # 거래 통계
            total_trades=total_trades_count,
            avg_holding_period=str(avg_hp),
            max_win_streak=max_win,
            max_loss_streak=max_loss
        )
```

---

## 7. Pydantic Schema

```python
from pydantic import BaseModel

class PerformanceMetricsResponse(BaseModel):
    """성과 지표 응답"""
    # 수익성
    total_return: float
    cagr: float
    avg_profit: float
    avg_loss: float

    # 리스크
    mdd: float
    volatility: float
    calmar_ratio: float

    # 효율성
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    expected_value: float

    # 거래 통계
    total_trades: int
    avg_holding_period: str
    max_win_streak: int
    max_loss_streak: int

    class Config:
        schema_extra = {
            "example": {
                "total_return": 0.25,
                "cagr": 0.18,
                "avg_profit": 150.0,
                "avg_loss": -80.0,
                "mdd": 0.15,
                "volatility": 0.12,
                "calmar_ratio": 1.2,
                "sharpe_ratio": 1.5,
                "win_rate": 0.55,
                "profit_factor": 1.8,
                "expected_value": 35.0,
                "total_trades": 50,
                "avg_holding_period": "2 days, 4:00:00",
                "max_win_streak": 5,
                "max_loss_streak": 3
            }
        }
```

---

## 8. 상위/관련 문서

- **[../index.md](../index.md)** - 백테스팅 개요
- **[simulation.md](./simulation.md)** - 시뮬레이션 엔진
- **[commission-slippage.md](./commission-slippage.md)** - 수수료/슬리피지

---

*최종 업데이트: 2025-12-29*
