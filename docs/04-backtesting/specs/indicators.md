# 기술적 지표 (Technical Indicators)

백테스팅에 사용되는 기술적 지표 계산 상세 명세입니다.

---

## 1. 지표 개요

### 1.1 지표 분류

| 분류 | 지표 | 용도 |
|------|------|------|
| **추세 (Trend)** | SMA, EMA, MACD | 추세 방향 확인 |
| **모멘텀 (Momentum)** | RSI, Stochastic | 과매수/과매도 확인 |
| **변동성 (Volatility)** | 볼린저 밴드, ATR | 변동성 측정 |
| **거래량 (Volume)** | OBV, VWAP | 거래량 분석 |

---

## 2. 이동평균선 (Moving Averages)

### 2.1 SMA (Simple Moving Average)

**수식**:
```
SMA(n) = (P₁ + P₂ + ... + Pₙ) / n
```

**Python 구현**:
```python
import pandas as pd
import numpy as np

def sma(prices: pd.Series, period: int) -> pd.Series:
    """
    단순 이동평균

    Args:
        prices: 가격 시계열 (보통 종가)
        period: 기간

    Returns:
        SMA 시계열
    """
    return prices.rolling(window=period).mean()
```

### 2.2 EMA (Exponential Moving Average)

**수식**:
```
EMA(t) = α × P(t) + (1 - α) × EMA(t-1)
α = 2 / (period + 1)
```

**Python 구현**:
```python
def ema(prices: pd.Series, period: int) -> pd.Series:
    """
    지수 이동평균

    Args:
        prices: 가격 시계열
        period: 기간

    Returns:
        EMA 시계열
    """
    return prices.ewm(span=period, adjust=False).mean()
```

---

## 3. RSI (Relative Strength Index)

### 3.1 정의

상대강도지수로 과매수/과매도 상태를 나타냅니다.

**수식**:
```
RSI = 100 - (100 / (1 + RS))

RS = Average Gain / Average Loss

Average Gain: n기간 동안의 상승 평균
Average Loss: n기간 동안의 하락 평균
```

### 3.2 Python 구현

```python
def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI 계산

    Args:
        prices: 가격 시계열
        period: 기간 (default: 14)

    Returns:
        RSI 시계열 (0 ~ 100)
    """
    # 가격 변화 계산
    delta = prices.diff()

    # 상승/하락 분리
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # 평균 상승/하락 (Wilders smoothing)
    avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()

    # RS 계산
    rs = avg_gains / avg_losses

    # RSI 계산
    rsi_value = 100 - (100 / (1 + rs))

    return rsi_value
```

### 3.3 해석

| RSI 값 | 해석 |
|--------|------|
| **RSI > 70** | 과매수 (매도 신호) |
| **RSI < 30** | 과매도 (매수 신호) |
| **30 ~ 70** | 중립 |

---

## 4. MACD (Moving Average Convergence Divergence)

### 4.1 정의

이동평균 수렴확산 지표로 추세 전환을 포착합니다.

**구성 요소**:
```
MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(MACD Line, 9)
Histogram = MACD Line - Signal Line
```

### 4.2 Python 구현

```python
def macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> dict:
    """
    MACD 계산

    Args:
        prices: 가격 시계열
        fast_period: 빠른 EMA 기간
        slow_period: 느린 EMA 기간
        signal_period: 시그널 EMA 기간

    Returns:
        {
            'macd': MACD Line 시계열,
            'signal': Signal Line 시계열,
            'histogram': Histogram 시계열
        }
    """
    # EMA 계산
    ema_fast = ema(prices, fast_period)
    ema_slow = ema(prices, slow_period)

    # MACD Line
    macd_line = ema_fast - ema_slow

    # Signal Line
    signal_line = ema(macd_line, signal_period)

    # Histogram
    histogram = macd_line - signal_line

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }
```

### 4.3 해석

| 시그널 | 해석 |
|--------|------|
| **MACD > Signal, Histogram > 0** | 상승 추세 (매수) |
| **MACD < Signal, Histogram < 0** | 하락 추세 (매도) |
| **MACD가 Signal을 상향 돌파** | 골든크로스 (매수 강력 신호) |
| **MACD가 Signal을 하향 이탈** | 데드크로스 (매도 강력 신호) |

---

## 5. 볼린저 밴드 (Bollinger Bands)

### 5.1 정의

변동성을 기반으로 한 밴드 지표입니다.

**구성 요소**:
```
Middle Band = SMA(n)
Upper Band = SMA(n) + k × σ(n)
Lower Band = SMA(n) - k × σ(n)

σ(n): n기간 표준편차
k: 배수 (보통 2)
```

### 5.2 Python 구현

```python
def bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> dict:
    """
    볼린저 밴드 계산

    Args:
        prices: 가격 시계열
        period: 기간 (default: 20)
        std_dev: 표준편차 배수 (default: 2.0)

    Returns:
        {
            'upper': Upper Band,
            'middle': Middle Band (SMA),
            'lower': Lower Band,
            'bandwidth': (upper - lower) / middle,
            'percent_b': (price - lower) / (upper - lower)
        }
    """
    # Middle Band (SMA)
    middle = sma(prices, period)

    # 표준편차
    std = prices.rolling(window=period).std()

    # Upper/Lower Band
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    # Bandwidth (밴드 폭)
    bandwidth = (upper - lower) / middle

    # %B (가격이 밴드 내에서 어디에 위치하는지)
    percent_b = (prices - lower) / (upper - lower)

    return {
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'bandwidth': bandwidth,
        'percent_b': percent_b
    }
```

### 5.3 해석

| 시그널 | 해석 |
|--------|------|
| **가격 > Upper Band** | 강력한 상승 (과매수 가능성) |
| **가격 < Lower Band** | 강력한 하락 (과매도 가능성) |
| **밴드 축소 (Squeeze)** | 변동성 감소 → 추세 전환 가능성 |
| **%B > 1** | 가격이 상단 밴드 이탈 |
| **%B < 0** | 가격이 하단 밴드 이탈 |

---

## 6. ATR (Average True Range)

### 6.1 정의

평균 실제 변동폭으로 변동성을 측정합니다.

**수식**:
```
TR = max(H - L, |H - P₍₋₁₎|, |L - P₍₋₁₎|)
ATR(n) = SMA(TR, n)

H: 고가, L: 저가, P₍₋₁₎: 전일 종가
```

### 6.2 Python 구현

```python
def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    ATR 계산

    Args:
        high: 고가 시계열
        low: 저가 시계열
        close: 종가 시계열
        period: 기간 (default: 14)

    Returns:
        ATR 시계열
    """
    # True Range 계산
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR (Wilders smoothing)
    atr_value = tr.ewm(alpha=1/period, adjust=False).mean()

    return atr_value
```

---

## 7. Stochastic Oscillator

### 7.1 정의

**%K**와 **%D**로 구성된 모멘텀 지표입니다.

**수식**:
```
%K = 100 × (C - L₍₁₄₎) / (H₍₁₄₎ - L₍₁₄₎)

C: 현재 종가
L₍₁₄₎: 14기간 최저가
H₍₁₄₎: 14기간 최고가

%D = SMA(%K, 3)
```

### 7.2 Python 구현

```python
def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> dict:
    """
    Stochastic Oscillator 계산

    Returns:
        {
            'k': %K 시계열,
            'd': %D 시계열
        }
    """
    # 14기간 최고가/최저가
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    # %K 계산
    k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)

    # %D 계산 (%K의 3기간 SMA)
    d_percent = k_percent.rolling(window=d_period).mean()

    return {
        'k': k_percent,
        'd': d_percent
    }
```

---

## 8. 지표 계산 서비스

### 8.1 통합 서비스

```python
from typing import Dict, Any
import pandas as pd

class IndicatorService:
    """기술적 지표 계산 서비스"""

    def __init__(self):
        pass

    def calculate_all(
        self,
        df: pd.DataFrame,
        indicators: list[str]
    ) -> pd.DataFrame:
        """
        여러 지표 한 번에 계산

        Args:
            df: OHLCV DataFrame
            indicators: 계산할 지표 리스트

        Returns:
            지표가 추가된 DataFrame
        """
        result = df.copy()

        for indicator in indicators:
            if indicator == 'sma_20':
                result['sma_20'] = sma(result['close'], 20)
            elif indicator == 'ema_12':
                result['ema_12'] = ema(result['close'], 12)
            elif indicator == 'rsi':
                result['rsi'] = rsi(result['close'])
            elif indicator == 'macd':
                macd_data = macd(result['close'])
                result['macd'] = macd_data['macd']
                result['macd_signal'] = macd_data['signal']
                result['macd_histogram'] = macd_data['histogram']
            elif indicator == 'bollinger':
                bb_data = bollinger_bands(result['close'])
                result['bb_upper'] = bb_data['upper']
                result['bb_middle'] = bb_data['middle']
                result['bb_lower'] = bb_data['lower']
                result['bb_percent_b'] = bb_data['percent_b']
            elif indicator == 'atr':
                result['atr'] = atr(
                    result['high'],
                    result['low'],
                    result['close']
                )
            elif indicator == 'stochastic':
                stoch_data = stochastic(
                    result['high'],
                    result['low'],
                    result['close']
                )
                result['stoch_k'] = stoch_data['k']
                result['stoch_d'] = stoch_data['d']

        return result
```

### 8.2 FastAPI 엔드포인트

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/backtesting/indicators", tags=["indicators"])

class IndicatorRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    indicators: list[str]

@router.post("/calculate")
async def calculate_indicators(
    request: IndicatorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    기술적 지표 계산 엔드포인트

    - **indicators**: ['rsi', 'macd', 'bollinger', 'sma_20', 'ema_12', 'atr', 'stochastic']
    """
    # 1. OHLCV 데이터 조회
    repo = OHLCVRepository(db)
    ohlcv_data = await repo.fetch_date_range(
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date
    )

    # 2. DataFrame 변환
    df = pd.DataFrame([
        {
            'timestamp': d.timestamp,
            'open': d.open,
            'high': d.high,
            'low': d.low,
            'close': d.close,
            'volume': d.volume
        }
        for d in ohlcv_data
    ])

    # 3. 지표 계산
    service = IndicatorService()
    result_df = service.calculate_all(df, request.indicators)

    # 4. JSON 변환
    result = result_df.to_dict(orient='records')

    return {
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "indicators": request.indicators,
        "data": result
    }
```

---

## 9. Pydantic Schema

```python
from pydantic import BaseModel
from typing import Optional

class IndicatorValue(BaseModel):
    """단일 지표 값"""
    timestamp: int
    value: float

class IndicatorResult(BaseModel):
    """지표 계산 결과"""
    indicator: str
    data: list[IndicatorValue]

    class Config:
        schema_extra = {
            "example": {
                "indicator": "rsi",
                "data": [
                    {"timestamp": 1609459200000, "value": 45.2},
                    {"timestamp": 1609462800000, "value": 48.1}
                ]
            }
        }
```

---

## 10. 상위/관련 문서

- **[../index.md](../index.md)** - 백테스팅 개요
- **[data-processing.md](./data-processing.md)** - 데이터 처리
- **[simulation.md](./simulation.md)** - 시뮬레이션 엔진

---

*최종 업데이트: 2025-12-29*
