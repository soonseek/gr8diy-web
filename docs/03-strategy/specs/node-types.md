# 노드 타입 상세 (Node Types)

전략 에디터의 모든 노드 타입에 대한 상세 명세입니다.

---

## 1. 트리거 노드 (Trigger Nodes)

트리거 노드는 전략 실행을 시작하는 조건을 정의합니다.

### 1.1 시간 기반 트리거 (Time Trigger)

**설명**: 지정된 시간 간격으로 전략을 실행합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `trigger_type` | str | Yes | `"time"` 고정 | - |
| `interval` | str | Yes | 실행 간격 | `1m`, `5m`, `15m`, `1h`, `4h`, `1d` |
| `timezone` | str | No | 시간대 | default: `UTC` |

**JSON 예시**:
```json
{
  "id": "trigger_1",
  "type": "trigger",
  "config": {
    "trigger_type": "time",
    "interval": "1h",
    "timezone": "Asia/Seoul"
  }
}
```

**Pydantic Schema**:
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class TimeTriggerConfig(BaseModel):
    trigger_type: Literal["time"]
    interval: str = Field(..., pattern=r'^(\d+[mhd])$')
    timezone: str = Field(default="UTC")

    @field_validator('interval')
    def validate_interval(cls, v):
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if v not in valid_intervals:
            raise ValueError(f'interval must be one of {valid_intervals}')
        return v
```

**검증 규칙**:
- `interval`은 `^\d+[mhd]$` 정규식을 만족해야 함
- `timezone`은 IANA time zone 데이터베이스의 유효한 값이어야 함

---

### 1.2 가격 변동 트리거 (Price Change Trigger)

**설명**: 특정 심볼의 가격이 지정된 비율만큼 변동할 때 실행합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `trigger_type` | str | Yes | `"price_change"` 고정 | - |
| `symbol` | str | Yes | 거래쌍 심볼 | `BTC/USDT`, `ETH/USDT` 등 |
| `threshold` | float | Yes | 변동률 임계값 | -0.5 ~ 0.5 (음수: 하락, 양수: 상승) |
| `interval` | str | Yes | 가격 확인 간격 | `1m`, `5m`, `15m`, `1h` |
| `reference_price` | str | No | 기준 가격 | `"open"`, `"close"`, `"high"`, `"low"` |

**JSON 예시**:
```json
{
  "id": "trigger_1",
  "type": "trigger",
  "config": {
    "trigger_type": "price_change",
    "symbol": "BTC/USDT",
    "threshold": -0.05,
    "interval": "1h",
    "reference_price": "close"
  }
}
```

**Pydantic Schema**:
```python
class PriceChangeTriggerConfig(BaseModel):
    trigger_type: Literal["price_change"]
    symbol: str = Field(..., min_length=3, pattern=r'^[A-Z]+/[A-Z]+$')
    threshold: float = Field(..., ge=-0.5, le=0.5)
    interval: str = Field(..., pattern=r'^(\d+[m])$')
    reference_price: str = Field(default="close")

    @field_validator('symbol')
    def validate_symbol(cls, v):
        parts = v.split('/')
        if len(parts) != 2 or not all(p.isupper() for p in parts):
            raise ValueError('symbol must be in format BASE/QUOTE (e.g., BTC/USDT)')
        return v
```

**검증 규칙**:
- `threshold`는 -50% ~ +50% 범위 내
- `symbol`은 `BASE/QUOTE` 형식 (대문자)

---

### 1.3 거래량 트리거 (Volume Trigger)

**설명**: 거래량이 지정된 임계값을 초과할 때 실행합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `trigger_type` | str | Yes | `"volume"` 고정 | - |
| `symbol` | str | Yes | 거래쌍 심볼 | - |
| `threshold` | float | Yes | 거래량 임계값 | > 0 |
| `threshold_unit` | str | Yes | 단위 | `"base"`, `"quote"` |
| `period` | str | Yes | 기간 | `1m`, `5m`, `15m`, `1h` |

**JSON 예시**:
```json
{
  "id": "trigger_1",
  "type": "trigger",
  "config": {
    "trigger_type": "volume",
    "symbol": "BTC/USDT",
    "threshold": 100,
    "threshold_unit": "quote",
    "period": "1h"
  }
}
```

**Pydantic Schema**:
```python
class VolumeTriggerConfig(BaseModel):
    trigger_type: Literal["volume"]
    symbol: str
    threshold: float = Field(..., gt=0)
    threshold_unit: Literal["base", "quote"]
    period: str = Field(..., pattern=r'^(\d+[m])$')
```

---

## 2. 데이터 소스 노드 (Data Source Nodes)

데이터 소스 노드는 시장 데이터를 수집합니다.

### 2.1 OHLCV 데이터 소스 (OHLCV Source)

**설명**: 시가/고가/저가/종가/거래량 데이터를 수집합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `source_type` | str | Yes | `"ohlcv"` 고정 | - |
| `symbol` | str | Yes | 거래쌍 심볼 | - |
| `interval` | str | Yes | 캔들 간격 | `1m`, `5m`, `15m`, `1h`, `4h`, `1d` |
| `limit` | int | Yes | 데이터 개수 | 1 ~ 1000 |

**출력 데이터 타입**:
```python
from typing import TypedDict
from datetime import datetime

class OHLCVData(TypedDict):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
```

**JSON 예시**:
```json
{
  "id": "data_1",
  "type": "data_source",
  "config": {
    "source_type": "ohlcv",
    "symbol": "BTC/USDT",
    "interval": "1h",
    "limit": 100
  }
}
```

**Pydantic Schema**:
```python
class OHLCVSourceConfig(BaseModel):
    source_type: Literal["ohlcv"]
    symbol: str
    interval: str = Field(..., pattern=r'^(\d+[mhd])$')
    limit: int = Field(..., ge=1, le=1000)
```

**사용 예시**:
```json
[
  {
    "timestamp": "2025-12-29T12:00:00Z",
    "open": 95000.0,
    "high": 95500.0,
    "low": 94800.0,
    "close": 95200.0,
    "volume": 123.45
  }
]
```

---

### 2.2 호가 데이터 소스 (Order Book Source)

**설명**: 현재 호가(오더북) 데이터를 수집합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `source_type` | str | Yes | `"orderbook"` 고정 | - |
| `symbol` | str | Yes | 거래쌍 심볼 | - |
| `depth` | int | Yes | 호가 깊이 | 5 ~ 100 |

**출력 데이터 타입**:
```python
class OrderBookData(TypedDict):
    bids: list[tuple[float, float]]  # [(price, quantity), ...]
    asks: list[tuple[float, float]]
    timestamp: datetime
```

**JSON 예시**:
```json
{
  "id": "data_2",
  "type": "data_source",
  "config": {
    "source_type": "orderbook",
    "symbol": "BTC/USDT",
    "depth": 20
  }
}
```

**Pydantic Schema**:
```python
class OrderBookSourceConfig(BaseModel):
    source_type: Literal["orderbook"]
    symbol: str
    depth: int = Field(..., ge=5, le=100)
```

---

### 2.3 뉴스 데이터 소스 (News Source)

**설명**: 최근 암호화폐 뉴스를 수집합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `source_type` | str | Yes | `"news"` 고정 | - |
| `keywords` | list[str] | No | 검색 키워드 | 최대 10개 |
| `limit` | int | Yes | 뉴스 개수 | 1 ~ 50 |
| `language` | str | No | 언어 필터 | `"en"`, `"ko"`, `"ja"` |

**출력 데이터 타입**:
```python
class NewsData(TypedDict):
    title: str
    content: str
    url: str
    published_at: datetime
    source: str
```

**JSON 예시**:
```json
{
  "id": "data_3",
  "type": "data_source",
  "config": {
    "source_type": "news",
    "keywords": ["Bitcoin", "BTC"],
    "limit": 10,
    "language": "en"
  }
}
```

**Pydantic Schema**:
```python
class NewsSourceConfig(BaseModel):
    source_type: Literal["news"]
    keywords: list[str] = Field(default_factory=list)
    limit: int = Field(..., ge=1, le=50)
    language: str = Field(default="en")

    @field_validator('keywords')
    def validate_keywords(cls, v):
        if len(v) > 10:
            raise ValueError('keywords can have at most 10 items')
        return v
```

---

## 3. 지표 노드 (Indicator Nodes)

지표 노드는 기술적 지표를 계산합니다.

### 3.1 RSI 지표 (Relative Strength Index)

**설명**: RSI(상대강도지수)를 계산합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `indicator` | str | Yes | `"RSI"` 고정 | - |
| `period` | int | Yes | 기간 | 2 ~ 50 |
| `source` | str | No | 데이터 소스 | `"close"` (default) |

**출력 데이터 타입**:
```python
class RSIResult(TypedDict):
    value: float  # 0 ~ 100
    timestamp: datetime
```

**JSON 예시**:
```json
{
  "id": "indicator_1",
  "type": "indicator",
  "config": {
    "indicator": "RSI",
    "period": 14,
    "source": "close"
  }
}
```

**Pydantic Schema**:
```python
class RSIIndicatorConfig(BaseModel):
    indicator: Literal["RSI"]
    period: int = Field(..., ge=2, le=50)
    source: str = Field(default="close")
```

**사용 예시**:
```json
{
  "value": 28.5,
  "timestamp": "2025-12-29T12:00:00Z"
}
```

---

### 3.2 MACD 지표 (Moving Average Convergence Divergence)

**설명**: MACD를 계산합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `indicator` | str | Yes | `"MACD"` 고정 | - |
| `fast_period` | int | Yes | 빠른 EMA 기간 | default: 12 |
| `slow_period` | int | Yes | 느린 EMA 기간 | default: 26 |
| `signal_period` | int | Yes | 시그널 기간 | default: 9 |

**출력 데이터 타입**:
```python
class MACDResult(TypedDict):
    macd: float
    signal: float
    histogram: float  # macd - signal
    timestamp: datetime
```

**JSON 예시**:
```json
{
  "id": "indicator_2",
  "type": "indicator",
  "config": {
    "indicator": "MACD",
    "fast_period": 12,
    "slow_period": 26,
    "signal_period": 9
  }
}
```

**Pydantic Schema**:
```python
class MACDIndicatorConfig(BaseModel):
    indicator: Literal["MACD"]
    fast_period: int = Field(default=12, ge=1, le=100)
    slow_period: int = Field(default=26, ge=1, le=200)
    signal_period: int = Field(default=9, ge=1, le=50)

    @field_validator('slow_period')
    def validate_slow_period(cls, v, info):
        if 'fast_period' in info.data and v <= info.data['fast_period']:
            raise ValueError('slow_period must be greater than fast_period')
        return v
```

---

### 3.3 볼린저 밴드 (Bollinger Bands)

**설명**: 볼린저 밴드를 계산합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `indicator` | str | Yes | `"BB"` 고정 | - |
| `period` | int | Yes | 기간 | default: 20 |
| `std_dev` | float | Yes | 표준편차 배수 | default: 2.0 |

**출력 데이터 타입**:
```python
class BBResult(TypedDict):
    upper: float
    middle: float  # SMA
    lower: float
    bandwidth: float  # (upper - lower) / middle
    timestamp: datetime
```

**JSON 예시**:
```json
{
  "id": "indicator_3",
  "type": "indicator",
  "config": {
    "indicator": "BB",
    "period": 20,
    "std_dev": 2.0
  }
}
```

**Pydantic Schema**:
```python
class BBIndicatorConfig(BaseModel):
    indicator: Literal["BB"]
    period: int = Field(default=20, ge=2, le=100)
    std_dev: float = Field(default=2.0, ge=0.5, le=5.0)
```

---

## 4. 조건 노드 (Condition Nodes)

조건 노드는 분기 로직을 정의합니다.

### 4.1 단일 조건 (Single Condition)

**설명**: 단일 조건을 평가합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `operator` | str | Yes | 비교 연산자 | `>`, `<`, `>=`, `<=`, `==`, `!=` |
| `left` | str | Yes | 좌변 값 | 노드 ID 또는 리터럴 |
| `right` | str | Yes | 우변 값 | 노드 ID 또는 리터럴 |

**출력 데이터 타입**:
```python
class ConditionResult(TypedDict):
    result: bool  # True/False
    reason: str   # "RSI(28.5) < 30"
```

**JSON 예시**:
```json
{
  "id": "condition_1",
  "type": "condition",
  "config": {
    "operator": "<",
    "left": "indicator_1.value",
    "right": "30"
  }
}
```

**Pydantic Schema**:
```python
from enum import Enum

class Operator(str, Enum):
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="

class SingleConditionConfig(BaseModel):
    operator: Operator
    left: str
    right: str

    @field_validator('left', 'right')
    def validate_operand(cls, v):
        # 리터럴 값 또는 노드 참조 (node_id.field)
        if not (v.replace('.', '', 1).isdigit() or '.' in v):
            # 노드 참조 형식 검증
            if '.' not in v:
                raise ValueError('operand must be a literal or node.field reference')
        return v
```

---

### 4.2 복합 조건 (Compound Condition)

**설명**: AND/OR로 연결된 복수 조건을 평가합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `operator` | str | Yes | 논리 연산자 | `"AND"`, `"OR"` |
| `conditions` | list | Yes | 조건 리스트 | 2 ~ 10개 |

**JSON 예시**:
```json
{
  "id": "condition_2",
  "type": "condition",
  "config": {
    "operator": "AND",
    "conditions": [
      {
        "operator": "<",
        "left": "indicator_1.value",
        "right": "30"
      },
      {
        "operator": ">",
        "left": "data_1.close",
        "right": "90000"
      }
    ]
  }
}
```

**Pydantic Schema**:
```python
class SingleCondition(BaseModel):
    operator: Operator
    left: str
    right: str

class CompoundConditionConfig(BaseModel):
    operator: Literal["AND", "OR"]
    conditions: list[SingleCondition] = Field(..., min_length=2, max_length=10)
```

---

## 5. LLM 노드 (LLM Nodes)

LLM 노드는 자연어 처리를 수행합니다.

### 5.1 LLM 분석 노드 (LLM Analysis)

**설명**: 시장 데이터를 LLM으로 분석합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `llm_type` | str | Yes | `"analysis"` 고정 | - |
| `model` | str | Yes | LLM 모델 | `gpt-4`, `gpt-3.5-turbo` |
| `prompt_template` | str | Yes | 프롬프트 템플릿 | `{data}` 변수 사용 |
| `max_tokens` | int | Yes | 최대 토큰 | 100 ~ 4000 |
| `temperature` | float | No | 생성 온도 | 0.0 ~ 1.0 (default: 0.7) |
| `output_format` | str | No | 출력 형식 | `"json"`, `"text"` |

**출력 데이터 타입**:
```python
class LLMAnalysisResult(TypedDict):
    analysis: str      # 분석 결과
    recommendation: str  # BUY/SELL/HOLD
    confidence: float  # 0.0 ~ 1.0
    reason: str
```

**JSON 예시**:
```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "llm_type": "analysis",
    "model": "gpt-4",
    "prompt_template": "다음 시장 데이터를 분석하세요: {data}",
    "max_tokens": 500,
    "temperature": 0.7,
    "output_format": "json"
  }
}
```

**Pydantic Schema**:
```python
class LLMAnalysisConfig(BaseModel):
    llm_type: Literal["analysis"]
    model: Literal["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]
    prompt_template: str = Field(..., min_length=10)
    max_tokens: int = Field(..., ge=100, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    output_format: Literal["json", "text"] = Field(default="json")
```

---

### 5.2 LLM 감성 노드 (LLM Sentiment)

**설명**: 뉴스/소셜 미디어 감성을 분석합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `llm_type` | str | Yes | `"sentiment"` 고정 | - |
| `model` | str | Yes | LLM 모델 | - |
| `source` | str | Yes | 데이터 소스 | `"news"`, `"social"` |
| `source_count` | int | Yes | 분석할 문서 수 | 1 ~ 50 |
| `cache_minutes` | int | No | 캐싱 시간 (분) | default: 15 |

**출력 데이터 타입**:
```python
class LLMSentimentResult(TypedDict):
    sentiment: str      # POSITIVE/NEGATIVE/NEUTRAL
    score: float        # -1.0 ~ 1.0
    keywords: list[str]
    summary: str
    timestamp: datetime
```

**JSON 예시**:
```json
{
  "id": "llm_2",
  "type": "llm",
  "config": {
    "llm_type": "sentiment",
    "model": "gpt-4",
    "source": "news",
    "source_count": 10,
    "cache_minutes": 15
  }
}
```

**Pydantic Schema**:
```python
class LLMSentimentConfig(BaseModel):
    llm_type: Literal["sentiment"]
    model: str
    source: Literal["news", "social"]
    source_count: int = Field(..., ge=1, le=50)
    cache_minutes: int = Field(default=15, ge=0, le=60)
```

---

## 6. 액션 노드 (Action Nodes)

액션 노드는 실제 거래를 실행합니다.

### 6.1 매수 노드 (Buy Action)

**설명**: 시장가/지정가 매수를 실행합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `action_type` | str | Yes | `"buy"` 고정 | - |
| `symbol` | str | Yes | 거래쌍 심볼 | - |
| `order_type` | str | Yes | 주문 유형 | `"market"`, `"limit"` |
| `amount` | float | Yes | 수량/금액 | > 0 |
| `amount_unit` | str | Yes | 수량 단위 | `"base"`, `"quote"` |
| `price` | float | No | 지정가 (limit only) | > 0 |

**출력 데이터 타입**:
```python
class BuyActionResult(TypedDict):
    order_id: str
    symbol: str
    side: str  # "buy"
    order_type: str  # "market" or "limit"
    price: float | None
    amount: float
    executed: bool
    timestamp: datetime
```

**JSON 예시**:
```json
{
  "id": "action_1",
  "type": "action",
  "config": {
    "action_type": "buy",
    "symbol": "BTC/USDT",
    "order_type": "market",
    "amount": 1000,
    "amount_unit": "USDT"
  }
}
```

**지정가 예시**:
```json
{
  "id": "action_2",
  "type": "action",
  "config": {
    "action_type": "buy",
    "symbol": "BTC/USDT",
    "order_type": "limit",
    "amount": 0.01,
    "amount_unit": "BTC",
    "price": 95000
  }
}
```

**Pydantic Schema**:
```python
from typing import Literal

class BuyActionConfig(BaseModel):
    action_type: Literal["buy"]
    symbol: str
    order_type: Literal["market", "limit"]
    amount: float = Field(..., gt=0)
    amount_unit: Literal["base", "quote"]
    price: float | None = Field(default=None, gt=0)

    @field_validator('price')
    def validate_price(cls, v, info):
        if info.data.get('order_type') == 'limit' and v is None:
            raise ValueError('price is required for limit orders')
        return v
```

---

### 6.2 매도 노드 (Sell Action)

**설명**: 시장가/지정가 매도를 실행합니다.

**파라미터**: 매수 노드와 동일 (`action_type`: `"sell"`)

**JSON 예시**:
```json
{
  "id": "action_3",
  "type": "action",
  "config": {
    "action_type": "sell",
    "symbol": "BTC/USDT",
    "order_type": "market",
    "amount": 0.01,
    "amount_unit": "BTC"
  }
}
```

**Pydantic Schema**:
```python
class SellActionConfig(BaseModel):
    action_type: Literal["sell"]
    symbol: str
    order_type: Literal["market", "limit"]
    amount: float = Field(..., gt=0)
    amount_unit: Literal["base", "quote"]
    price: float | None = Field(default=None, gt=0)

    @field_validator('price')
    def validate_price(cls, v, info):
        if info.data.get('order_type') == 'limit' and v is None:
            raise ValueError('price is required for limit orders')
        return v
```

---

### 6.3 손절/익절 노드 (Stop Loss / Take Profit)

**설명**: 손절/익절 주문을 설정합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `action_type` | str | Yes | `"stop_loss"` 또는 `"take_profit"` | - |
| `symbol` | str | Yes | 거래쌍 심볼 | - |
| `trigger_price` | float | Yes | 발동 가격 | > 0 |
| `amount` | float | Yes | 수량/금액 | > 0 |
| `amount_unit` | str | Yes | 수량 단위 | `"base"`, `"quote"` |
| `order_type` | str | No | 실행 주문 유형 | default: `"market"` |

**JSON 예시**:
```json
{
  "id": "action_4",
  "type": "action",
  "config": {
    "action_type": "stop_loss",
    "symbol": "BTC/USDT",
    "trigger_price": 94000,
    "amount": 0.01,
    "amount_unit": "BTC",
    "order_type": "market"
  }
}
```

**Pydantic Schema**:
```python
class RiskManagementActionConfig(BaseModel):
    action_type: Literal["stop_loss", "take_profit"]
    symbol: str
    trigger_price: float = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    amount_unit: Literal["base", "quote"]
    order_type: Literal["market", "limit"] = Field(default="market")
```

---

### 6.4 알림 노드 (Notification Action)

**설명**: 사용자에게 알림을 전송합니다.

**파라미터**:
| 파라미터 | 타입 | 필수 | 설명 | 제약 |
|---------|------|------|------|------|
| `action_type` | str | Yes | `"notify"` 고정 | - |
| `message` | str | Yes | 알림 메시지 | 최대 1000자 |
| `channels` | list[str] | No | 알림 채널 | `["email"`, `"web"`, `"telegram"]` |

**JSON 예시**:
```json
{
  "id": "action_5",
  "type": "action",
  "config": {
    "action_type": "notify",
    "message": "BTC 매수 전략이 실행되었습니다.",
    "channels": ["email", "web"]
  }
}
```

**Pydantic Schema**:
```python
class NotifyActionConfig(BaseModel):
    action_type: Literal["notify"]
    message: str = Field(..., min_length=1, max_length=1000)
    channels: list[Literal["email", "web", "telegram"]] = Field(
        default_factory=lambda: ["web"]
    )
```

---

## 7. 통합 Pydantic Schema

모든 노드 타입을 통합한 Schema입니다.

```python
from pydantic import BaseModel, Field
from typing import Union, Literal

class NodeConfig(BaseModel):
    type: Literal[
        "trigger", "data_source", "indicator", "condition", "llm", "action"
    ]
    config: Union[
        TimeTriggerConfig,
        PriceChangeTriggerConfig,
        VolumeTriggerConfig,
        OHLCVSourceConfig,
        OrderBookSourceConfig,
        NewsSourceConfig,
        RSIIndicatorConfig,
        MACDIndicatorConfig,
        BBIndicatorConfig,
        SingleConditionConfig,
        CompoundConditionConfig,
        LLMAnalysisConfig,
        LLMSentimentConfig,
        BuyActionConfig,
        SellActionConfig,
        RiskManagementActionConfig,
        NotifyActionConfig,
    ]

class Node(BaseModel):
    id: str = Field(..., pattern=r'^[a-z_]+_[0-9]+$')
    type: str
    config: dict

class Edge(BaseModel):
    from: str  # 노드 ID
    to: str    # 노드 ID
    condition: str | None = Field(default=None)  # "true", "false" (조건 노드용)

class StrategyDefinition(BaseModel):
    nodes: list[Node] = Field(..., min_length=1)
    edges: list[Edge]

    @field_validator('nodes')
    def validate_single_trigger(cls, v):
        triggers = [n for n in v if n.type == "trigger"]
        if len(triggers) != 1:
            raise ValueError("strategy must have exactly one trigger node")
        return v
```

---

## 8. 사용 예시: 완전한 전략

### 8.1 RSI 과매도 전략

```json
{
  "name": "RSI Oversold Strategy",
  "description": "RSI가 30 이하일 때 매수",
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "config": {
        "trigger_type": "time",
        "interval": "1h"
      }
    },
    {
      "id": "data_1",
      "type": "data_source",
      "config": {
        "source_type": "ohlcv",
        "symbol": "BTC/USDT",
        "interval": "1h",
        "limit": 100
      }
    },
    {
      "id": "indicator_1",
      "type": "indicator",
      "config": {
        "indicator": "RSI",
        "period": 14
      }
    },
    {
      "id": "condition_1",
      "type": "condition",
      "config": {
        "operator": "<",
        "left": "indicator_1.value",
        "right": "30"
      }
    },
    {
      "id": "action_1",
      "type": "action",
      "config": {
        "action_type": "buy",
        "symbol": "BTC/USDT",
        "order_type": "market",
        "amount": 1000,
        "amount_unit": "USDT"
      }
    }
  ],
  "edges": [
    {"from": "trigger_1", "to": "data_1"},
    {"from": "data_1", "to": "indicator_1"},
    {"from": "indicator_1", "to": "condition_1"},
    {"from": "condition_1", "to": "action_1", "condition": "true"}
  ]
}
```

### 8.2 뉴스 감성 기반 전략

```json
{
  "name": "News Sentiment Strategy",
  "description": "긍정적 뉴스 시 매수",
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "config": {
        "trigger_type": "time",
        "interval": "1h"
      }
    },
    {
      "id": "llm_1",
      "type": "llm",
      "config": {
        "llm_type": "sentiment",
        "model": "gpt-4",
        "source": "news",
        "source_count": 10
      }
    },
    {
      "id": "condition_1",
      "type": "condition",
      "config": {
        "operator": ">",
        "left": "llm_1.score",
        "right": "0.7"
      }
    },
    {
      "id": "action_1",
      "type": "action",
      "config": {
        "action_type": "buy",
        "symbol": "BTC/USDT",
        "order_type": "market",
        "amount": 500,
        "amount_unit": "USDT"
      }
    }
  ],
  "edges": [
    {"from": "trigger_1", "to": "llm_1"},
    {"from": "llm_1", "to": "condition_1"},
    {"from": "condition_1", "to": "action_1", "condition": "true"}
  ]
}
```

---

## 9. 상위/관련 문서

- **[../index.md](../index.md)** - 전략 시스템 개요
- **[validation-rules.md](./validation-rules.md)** - 전략 검증 규칙
- **[execution-engine.md](./execution-engine.md)** - 실행 엔진 상세
- **[llm-integration.md](./llm-integration.md)** - LLM 연동 상세

---

*최종 업데이트: 2025-12-29*
