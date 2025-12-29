# 수수료 & 슬리피지 (Commission & Slippage)

백테스팅 시뮬레이션의 수수료 및 슬리피지 모델링 상세 명세입니다.

---

## 1. 개요

### 1.1 거래 비용 구성

| 비용 | 설명 | 비율 |
|------|------|------|
| **Maker Fee** | 지정가 주문, 유동성 공급 | ~0.1% |
| **Taker Fee** | 시장가 주문, 유동성 소비 | ~0.1% |
| **Slippage** | 시장가 주문 시 가격 차이 | 0.05% ~ 0.1% |

---

## 2. 수수료 모델 (Commission Model)

### 2.1 Maker vs Taker

**Maker Fee**: 지정가 주문으로 오더북에 유동성을 공급할 때 부과

**Taker Fee**: 시장가 주문으로 오더북의 유동ity을 소비할 때 부과

| 거래소 | Maker Fee | Taker Fee |
|--------|-----------|-----------|
| **Binance** | 0.1% | 0.1% |
| **Coinbase Pro** | 0.15% | 0.25% |
| **Upbit** | 0.05% | 0.05% |

### 2.2 수수료 계산

**수식**:
```
Commission = Notional × Fee Rate

Notional = Price × Quantity
```

**Python 구현**:
```python
from decimal import Decimal
from enum import Enum

class FeeTier(str, Enum):
    """수수료 등급"""
    MAKER = "maker"
    TAKER = "taker"

class CommissionModel:
    """수수료 모델"""

    # 거래소별 기본 수수료율
    DEFAULT_RATES = {
        "binance": {
            FeeTier.MAKER: Decimal('0.001'),  # 0.1%
            FeeTier.TAKER: Decimal('0.001')
        },
        "upbit": {
            FeeTier.MAKER: Decimal('0.0005'),  # 0.05%
            FeeTier.TAKER: Decimal('0.0005')
        }
    }

    def __init__(
        self,
        exchange: str = "binance",
        maker_rate: Decimal | None = None,
        taker_rate: Decimal | None = None
    ):
        self.exchange = exchange

        # 사용자 정의 비율 또는 기본값
        rates = self.DEFAULT_RATES.get(exchange, self.DEFAULT_RATES["binance"])
        self.maker_rate = maker_rate or rates[FeeTier.MAKER]
        self.taker_rate = taker_rate or rates[FeeTier.TAKER]

    def calculate(
        self,
        price: Decimal,
        quantity: Decimal,
        tier: FeeTier = FeeTier.TAKER
    ) -> Decimal:
        """
        수수료 계산

        Args:
            price: 체결 가격
            quantity: 수량
            tier: Maker 또는 Taker

        Returns:
            수수료 (quote coin)
        """
        rate = self.maker_rate if tier == FeeTier.MAKER else self.taker_rate
        notional = price * quantity
        return notional * rate

    def calculate_market_order(
        self,
        price: Decimal,
        quantity: Decimal
    ) -> Decimal:
        """시장가 주문 수수료 (Taker)"""
        return self.calculate(price, quantity, FeeTier.TAKER)

    def calculate_limit_order(
        self,
        price: Decimal,
        quantity: Decimal
    ) -> Decimal:
        """지정가 주문 수수료 (Maker)"""
        return self.calculate(price, quantity, FeeTier.MAKER)
```

---

## 3. 슬리피지 모델 (Slippage Model)

### 3.1 슬리피지 정의

시장가 주문 시 실제 체결 가격이 예상 가격과 다른 현상

**원인**:
- 오더북 깊이 부족
- 시장 변동성
- 주문 규모

### 3.2 슬리피지 계산

**수식**:
```
Slippage Price = Current Price × (1 ± Slippage Rate)

+: 매수 (Buy)
-: 매도 (Sell)
```

**Python 구현**:
```python
class SlippageModel:
    """슬리피지 모델"""

    def __init__(
        self,
        base_rate: Decimal = Decimal('0.0005'),  # 0.05%
        volatility_adjustment: bool = True
    ):
        self.base_rate = base_rate
        self.volatility_adjustment = volatility_adjustment

    def calculate(
        self,
        side: str,
        current_price: Decimal,
        current_volatility: float | None = None
    ) -> Decimal:
        """
        슬리피지 계산

        Args:
            side: 'buy' or 'sell'
            current_price: 현재 가격
            current_volatility: 현재 변동성 (ATR 등)

        Returns:
            슬리피지가 적용된 가격
        """
        # 변동성 조정
        slippage_rate = self.base_rate

        if self.volatility_adjustment and current_volatility:
            # 변동성이 높을수록 슬리피지 증가
            slippage_rate = self.base_rate * (1 + current_volatility)

        # 매수/매도 방향
        if side == 'buy':
            return current_price * (1 + slippage_rate)
        else:  # 'sell'
            return current_price * (1 - slippage_rate)

    def calculate_slippage_amount(
        self,
        side: str,
        current_price: Decimal,
        current_volatility: float | None = None
    ) -> Decimal:
        """
        슬리피지 금액 계산

        Returns:
            슬리피지로 인한 가격 차이
        """
        adjusted_price = self.calculate(
            side,
            current_price,
            current_volatility
        )

        return abs(adjusted_price - current_price)
```

---

## 4. 종합 비용 모델

### 4.1 Transaction Cost Calculator

```python
from dataclasses import dataclass

@dataclass
class TransactionCost:
    """거래 비용"""
    price: Decimal
    commission: Decimal
    slippage: Decimal
    total_cost: Decimal

class TransactionCostCalculator:
    """종합 거래 비용 계산기"""

    def __init__(
        self,
        exchange: str = "binance",
        commission_rate: Decimal | None = None,
        slippage_rate: Decimal | None = None
    ):
        self.commission_model = CommissionModel(exchange, commission_rate)
        self.slippage_model = SlippageModel(slippage_rate or Decimal('0.0005'))

    def calculate_market_order_cost(
        self,
        side: str,
        quantity: Decimal,
        current_price: Decimal,
        current_volatility: float | None = None
    ) -> TransactionCost:
        """
        시장가 주문의 총 거래 비용 계산

        Returns:
            TransactionCost {
                price: 체결 가격 (슬리피지 포함),
                commission: 수수료,
                slippage: 슬리피지 금액,
                total_cost: 총 비용 (commission + slippage)
            }
        """
        # 1. 슬리피지 적용 가격 계산
        execution_price = self.slippage_model.calculate(
            side,
            current_price,
            current_volatility
        )

        # 2. 수수료 계산
        commission = self.commission_model.calculate_market_order(
            execution_price,
            quantity
        )

        # 3. 슬리피지 금액
        slippage_amount = abs(execution_price - current_price) * quantity

        # 4. 총 비용
        total_cost = commission + slippage_amount

        return TransactionCost(
            price=execution_price,
            commission=commission,
            slippage=slippage_amount,
            total_cost=total_cost
        )

    def calculate_limit_order_cost(
        self,
        side: str,
        limit_price: Decimal,
        quantity: Decimal
    ) -> TransactionCost:
        """
        지정가 주문의 총 거래 비용 계산

        지정가 주문은 슬리피지 없음
        """
        # 수수료만 적용
        commission = self.commission_model.calculate_limit_order(
            limit_price,
            quantity
        )

        return TransactionCost(
            price=limit_price,
            commission=commission,
            slippage=Decimal('0'),
            total_cost=commission
        )
```

---

## 5. 백테스팅 통합

### 5.1 Backtester에 통합

```python
class BacktesterWithCosts(Backtester):
    """거래 비용이 포함된 백테스터"""

    def __init__(
        self,
        exchange: str = "binance",
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 거래 비용 계산기
        self.cost_calculator = TransactionCostCalculator(
            exchange=exchange,
            commission_rate=Decimal(str(commission_rate)),
            slippage_rate=Decimal(str(slippage_rate))
        )

    async def _execute_buy(
        self,
        price: Decimal,
        candle: dict,
        signal_config: dict
    ):
        """매수 실행 (비용 포함)"""
        # 수량 계산
        amount = Decimal(str(signal_config.get('amount', 1000)))
        amount_unit = signal_config.get('amount_unit', 'USDT')

        if amount_unit == 'USDT':
            quantity = amount / price
        else:
            quantity = amount

        # 거래 비용 계산
        # ATR을 사용하여 변동성 기반 슬리피지 조정
        current_volatility = candle.get('atr_pct')  # ATR / current_price

        cost = self.cost_calculator.calculate_market_order_cost(
            side='buy',
            quantity=quantity,
            current_price=price,
            current_volatility=current_volatility
        )

        # 포지션 생성
        position = Position(
            symbol=candle.get('symbol', 'BTC/USDT'),
            side='long',
            entry_price=cost.price,  # 슬리피지 포함 가격
            quantity=cost.quantity,
            entry_time=datetime.utcnow()
        )

        self.portfolio.add_position(position)

        # 거래 기록 (비용 포함)
        self.trades.append({
            'timestamp': candle['timestamp'],
            'side': 'buy',
            'price': float(cost.price),
            'quantity': float(cost.quantity),
            'commission': float(cost.commission),
            'slippage': float(cost.slippage),
            'total_cost': float(cost.total_cost),
            'type': 'market'
        })
```

---

## 6. 비용 최적화

### 6.1 수수료 절감 전략

| 전략 | 설명 | 절감 효과 |
|------|------|----------|
| **지정가 주문 사용** | Maker Fee 적용 | ~50% |
| **거래소 VIP 등급** | 거래량 증가 시 할인 | ~10-25% |
| **BNB 보유 (Binance)** | BNB로 수수료 납부 시 25% 할인 | 25% |
| **LIMIT 사용** | 오더북에 걸어두고 기다림 | Maker Fee 적용 |

### 6.2 슬리피지 최소화

| 방법 | 설명 |
|------|------|
| **거래량이 많은 시간대 회피** | 변동성이 큰 시간은 슬리피지 증가 |
| **분할 주문** | 대량 주문을 나누어 체결 |
| **OCO 주문 사용** | One-Cancels-the-Other로 손절/익절 동시 설정 |

---

## 7. Pydantic Schema

```python
from pydantic import BaseModel, Field

class CommissionConfig(BaseModel):
    """수수료 설정"""
    exchange: str = Field(default="binance")
    maker_rate: float = Field(default=0.001, ge=0, le=0.01)
    taker_rate: float = Field(default=0.001, ge=0, le=0.01)

class SlippageConfig(BaseModel):
    """슬리피지 설정"""
    base_rate: float = Field(default=0.0005, ge=0, le=0.01)
    volatility_adjustment: bool = Field(default=True)

class BacktestCostConfig(BaseModel):
    """백테스팅 비용 설정"""
    commission: CommissionConfig
    slippage: SlippageConfig

    class Config:
        schema_extra = {
            "example": {
                "commission": {
                    "exchange": "binance",
                    "maker_rate": 0.001,
                    "taker_rate": 0.001
                },
                "slippage": {
                    "base_rate": 0.0005,
                    "volatility_adjustment": True
                }
            }
        }
```

---

## 8. 상위/관련 문서

- **[../index.md](../index.md)** - 백테스팅 개요
- **[simulation.md](./simulation.md)** - 시뮬레이션 엔진
- **[performance-metrics.md](./performance-metrics.md)** - 성과 지표

---

*최종 업데이트: 2025-12-29*
