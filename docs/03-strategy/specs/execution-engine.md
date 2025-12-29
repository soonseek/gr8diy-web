# 실행 엔진 (Execution Engine)

전략을 실행하고 노드 순서대로 처리하는 실행 엔진에 대한 상세 명세입니다.

---

## 1. 아키텍처 개요

### 1.1 실행 엔진 구조

```
┌─────────────────────────────────────────────────────┐
│              Strategy Execution Engine               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐      ┌──────────────┐           │
│  │   Scheduler  │──────│  Dispatcher  │           │
│  │  (Triggers)  │      │  (Executor)  │           │
│  └──────────────┘      └──────┬───────┘           │
│                                │                    │
│                       ┌────────▼────────┐          │
│                       │  Node Executor  │          │
│                       │  - Data Flow    │          │
│                       │  - Conditions   │          │
│                       │  - Actions      │          │
│                       └────────┬────────┘          │
│                                │                    │
│                       ┌────────▼────────┐          │
│                       │ Result Handler  │          │
│                       │  - DB Save      │          │
│                       │  - Blockchain   │          │
│                       └─────────────────┘          │
└─────────────────────────────────────────────────────┘
```

### 1.2 실행 흐름

```
1. Scheduler: 트리거 조건 모니터링
   ↓
2. Dispatcher: 전략 검증 → 실행 큐에 추가
   ↓
3. Node Executor: 노드 순서대로 처리
   - DataSource 노드: 외부 API 호출
   - Indicator 노드: 기술적 지표 계산
   - Condition 노드: 분기 판단
   - LLM 노드: LLM API 호출
   - Action 노드: 거래소 주문 실행
   ↓
4. Result Handler: 결과 저장
   - PostgreSQL: 실행 기록
   - (선택) Blockchain: 온체인 기록
```

---

## 2. 스케줄러 (Scheduler)

### 2.1 Trigger Scheduler

트리거 조건을 주기적으로 확인합니다.

```python
import asyncio
from typing import Dict, List
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

class TriggerType:
    TIME = "time"
    PRICE_CHANGE = "price_change"
    VOLUME = "volume"

class TriggerScheduler:
    """트리거 스케줄러"""

    def __init__(self, execution_engine: "ExecutionEngine"):
        self.scheduler = AsyncIOScheduler()
        self.execution_engine = execution_engine
        self._trigger_jobs: Dict[str, str] = {}  # strategy_id -> job_id

    async def start(self):
        """스케줄러 시작"""
        self.scheduler.start()

    async def stop(self):
        """스케줄러 중지"""
        self.scheduler.shutdown()

    async def register_strategy(self, strategy_id: str, strategy: dict):
        """전략 등록 (트리거 기반 스케줄링)"""
        trigger_node = self._find_trigger_node(strategy["nodes"])

        if trigger_node["config"]["trigger_type"] == TriggerType.TIME:
            await self._register_time_trigger(strategy_id, trigger_node)

        elif trigger_node["config"]["trigger_type"] == TriggerType.PRICE_CHANGE:
            await self._register_price_trigger(strategy_id, trigger_node)

        elif trigger_node["config"]["trigger_type"] == TriggerType.VOLUME:
            await self._register_volume_trigger(strategy_id, trigger_node)

    async def unregister_strategy(self, strategy_id: str):
        """전략 제거"""
        if strategy_id in self._trigger_jobs:
            self.scheduler.remove_job(self._trigger_jobs[strategy_id])
            del self._trigger_jobs[strategy_id]

    def _find_trigger_node(self, nodes: List[dict]) -> dict:
        """트리거 노드 찾기"""
        for node in nodes:
            if node["type"] == "trigger":
                return node
        raise ValueError("No trigger node found")

    async def _register_time_trigger(self, strategy_id: str, trigger_node: dict):
        """시간 기반 트리거 등록"""
        config = trigger_node["config"]
        interval = config["interval"]

        # interval 파싱 (예: "1h" → 3600초)
        seconds = self._parse_interval(interval)

        job = self.scheduler.add_job(
            self.execution_engine.execute_strategy,
            trigger=IntervalTrigger(seconds=seconds),
            args=[strategy_id],
            id=f"trigger_{strategy_id}",
            replace_existing=True
        )

        self._trigger_jobs[strategy_id] = job.id

    async def _register_price_trigger(self, strategy_id: str, trigger_node: dict):
        """가격 변동 트리거 등록 (1분마다 체크)"""
        job = self.scheduler.add_job(
            self._check_price_trigger,
            trigger=IntervalTrigger(seconds=60),
            args=[strategy_id, trigger_node],
            id=f"trigger_{strategy_id}",
            replace_existing=True
        )

        self._trigger_jobs[strategy_id] = job.id

    async def _check_price_trigger(self, strategy_id: str, trigger_node: dict):
        """가격 변동 체크"""
        config = trigger_node["config"]
        symbol = config["symbol"]
        threshold = config["threshold"]

        # 현재 가격 조회 (외부 API)
        current_price = await self._get_current_price(symbol)

        # 1시간 전 가격 조회
        previous_price = await self._get_price_1h_ago(symbol)

        # 변동률 계산
        change_rate = (current_price - previous_price) / previous_price

        # 임계값 확인
        if threshold < 0 and change_rate <= threshold:
            # 하락 트리거 발동
            await self.execution_engine.execute_strategy(strategy_id)
        elif threshold > 0 and change_rate >= threshold:
            # 상승 트리거 발동
            await self.execution_engine.execute_strategy(strategy_id)

    async def _register_volume_trigger(self, strategy_id: str, trigger_node: dict):
        """거래량 트리거 등록 (1분마다 체크)"""
        # 가격 트리거와 유사하게 구현
        pass

    def _parse_interval(self, interval: str) -> int:
        """interval 파싱 (1m, 5m, 1h, 1d)"""
        unit = interval[-1]
        value = int(interval[:-1])

        multipliers = {
            "m": 60,
            "h": 3600,
            "d": 86400
        }

        return value * multipliers.get(unit, 60)

    async def _get_current_price(self, symbol: str) -> float:
        """현재 가격 조회 (구현 필요)"""
        # 거래소 API 호출
        pass

    async def _get_price_1h_ago(self, symbol: str) -> float:
        """1시간 전 가격 조회 (구현 필요)"""
        # OHLCV 데이터 조회
        pass
```

---

## 3. 노드 실행기 (Node Executor)

### 3.1 Executor 기본 구조

```python
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from enum import Enum

class ExecutionStatus(str, Enum):
    """실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class NodeExecutionResult:
    """노드 실행 결과"""
    def __init__(
        self,
        node_id: str,
        status: ExecutionStatus,
        data: Any = None,
        error: str | None = None
    ):
        self.node_id = node_id
        self.status = status
        self.data = data
        self.error = error

class BaseNodeExecutor(ABC):
    """노드 실행자 기본 클래스"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """노드 실행"""
        pass

    async def validate(self) -> bool:
        """설정 검증"""
        return True
```

---

### 3.2 DataSource 노드 실행

```python
import aiohttp
from app.services.exchange import ExchangeService

class DataSourceExecutor(BaseNodeExecutor):
    """데이터 소스 실행"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.exchange = ExchangeService()

    async def execute(self, context: Dict[str, Any]) -> Any:
        source_type = self.config["source_type"]

        if source_type == "ohlcv":
            return await self._fetch_ohlcv()
        elif source_type == "orderbook":
            return await self._fetch_orderbook()
        elif source_type == "news":
            return await self._fetch_news()
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    async def _fetch_ohlcv(self) -> List[dict]:
        """OHLCV 데이터 조회"""
        symbol = self.config["symbol"]
        interval = self.config["interval"]
        limit = self.config["limit"]

        # 거래소 API 호출
        data = await self.exchange.fetch_ohlcv(
            symbol=symbol,
            interval=interval,
            limit=limit
        )

        return [
            {
                "timestamp": d[0],
                "open": d[1],
                "high": d[2],
                "low": d[3],
                "close": d[4],
                "volume": d[5]
            }
            for d in data
        ]

    async def _fetch_orderbook(self) -> dict:
        """호가 데이터 조회"""
        symbol = self.config["symbol"]
        depth = self.config["depth"]

        return await self.exchange.fetch_order_book(symbol, depth)

    async def _fetch_news(self) -> List[dict]:
        """뉴스 데이터 조회"""
        # 뉴스 API 호출
        pass
```

---

### 3.3 Indicator 노드 실행

```python
import pandas as pd
import ta

class IndicatorExecutor(BaseNodeExecutor):
    """지표 실행"""

    async def execute(self, context: Dict[str, Any]) -> Any:
        indicator = self.config["indicator"]

        if indicator == "RSI":
            return await self._calculate_rsi(context)
        elif indicator == "MACD":
            return await self._calculate_macd(context)
        elif indicator == "BB":
            return await self._calculate_bollinger_bands(context)
        else:
            raise ValueError(f"Unknown indicator: {indicator}")

    async def _calculate_rsi(self, context: Dict[str, Any]) -> dict:
        """RSI 계산"""
        period = self.config.get("period", 14)

        # 이전 노드에서 OHLCV 데이터 가져오기
        ohlcv_data = context.get("ohlcv")
        if not ohlcv_data:
            raise ValueError("OHLCV data not found in context")

        # DataFrame 변환
        df = pd.DataFrame(ohlcv_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # RSI 계산
        rsi = ta.momentum.RSIIndicator(df['close'], window=period)
        current_rsi = rsi.rsi.iloc[-1]

        return {
            "value": float(current_rsi),
            "timestamp": df['timestamp'].iloc[-1].isoformat()
        }

    async def _calculate_macd(self, context: Dict[str, Any]) -> dict:
        """MACD 계산"""
        fast = self.config.get("fast_period", 12)
        slow = self.config.get("slow_period", 26)
        signal = self.config.get("signal_period", 9)

        ohlcv_data = context.get("ohlcv")
        df = pd.DataFrame(ohlcv_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # MACD 계산
        macd = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)

        return {
            "macd": float(macd.macd().iloc[-1]),
            "signal": float(macd.macd_signal().iloc[-1]),
            "histogram": float(macd.macd_diff().iloc[-1]),
            "timestamp": df['timestamp'].iloc[-1].isoformat()
        }

    async def _calculate_bollinger_bands(self, context: Dict[str, Any]) -> dict:
        """볼린저 밴드 계산"""
        period = self.config.get("period", 20)
        std_dev = self.config.get("std_dev", 2.0)

        ohlcv_data = context.get("ohlcv")
        df = pd.DataFrame(ohlcv_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # 볼린저 밴드 계산
        bb = ta.volatility.BollingerBands(df['close'], window=period, window_dev=std_dev)

        return {
            "upper": float(bb.bollinger_hband().iloc[-1]),
            "middle": float(bb.bollinger_mavg().iloc[-1]),
            "lower": float(bb.bollinger_lband().iloc[-1]),
            "bandwidth": float(bb.bollinger_wband().iloc[-1]),
            "timestamp": df['timestamp'].iloc[-1].isoformat()
        }
```

---

### 3.4 Condition 노드 실행

```python
class ConditionExecutor(BaseNodeExecutor):
    """조건 실행"""

    async def execute(self, context: Dict[str, Any]) -> Any:
        if "operator" in self.config:
            return await self._evaluate_single(context)
        elif "conditions" in self.config:
            return await self._evaluate_compound(context)

    async def _evaluate_single(self, context: Dict[str, Any]) -> dict:
        """단일 조건 평가"""
        operator = self.config["operator"]
        left = self._resolve_value(self.config["left"], context)
        right = self._resolve_value(self.config["right"], context)

        # 비교 연산
        result = self._compare(left, operator, right)

        return {
            "result": result,
            "reason": f"{left} {operator} {right} = {result}"
        }

    async def _evaluate_compound(self, context: Dict[str, Any]) -> dict:
        """복합 조건 평가"""
        logic_op = self.config["operator"]  # AND or OR
        conditions = self.config["conditions"]

        results = []
        for cond in conditions:
            result = await self._evaluate_single_cond(cond, context)
            results.append(result)

        if logic_op == "AND":
            final_result = all(r["result"] for r in results)
        else:  # OR
            final_result = any(r["result"] for r in results)

        return {
            "result": final_result,
            "conditions": results
        }

    def _resolve_value(self, operand: str, context: Dict[str, Any]) -> float:
        """피연산자 해석"""
        # 리터럴 값
        try:
            return float(operand)
        except ValueError:
            pass

        # 노드 참조: "node_id.field"
        if '.' in operand:
            node_id, field = operand.split('.', 1)
            if node_id in context:
                return float(context[node_id].get(field, 0))
        else:
            # 노드 전체 참조
            if operand in context:
                return float(context[operand].get("value", 0))

        raise ValueError(f"Cannot resolve operand: {operand}")

    def _compare(self, left: float, operator: str, right: float) -> bool:
        """비교 연산"""
        ops = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: abs(x - y) < 1e-9,
            "!=": lambda x, y: abs(x - y) >= 1e-9
        }
        return ops[operator](left, right)

    async def _evaluate_single_cond(self, cond: dict, context: Dict[str, Any]) -> dict:
        """단일 조건 평가 (내부용)"""
        left = self._resolve_value(cond["left"], context)
        right = self._resolve_value(cond["right"], context)
        result = self._compare(left, cond["operator"], right)

        return {
            "result": result,
            "left": left,
            "operator": cond["operator"],
            "right": right
        }
```

---

### 3.5 LLM 노드 실행

```python
from app.services.llm import LLMService, LLMMessage, MessageRole

class LLMExecutor(BaseNodeExecutor):
    """LLM 실행"""

    def __init__(self, config: dict, llm_service: LLMService):
        super().__init__(config)
        self.llm_service = llm_service

    async def execute(self, context: Dict[str, Any]) -> Any:
        llm_type = self.config["llm_type"]

        if llm_type == "analysis":
            return await self._execute_analysis(context)
        elif llm_type == "sentiment":
            return await self._execute_sentiment(context)
        else:
            raise ValueError(f"Unknown LLM type: {llm_type}")

    async def _execute_analysis(self, context: Dict[str, Any]) -> dict:
        """시장 분석 실행"""
        model = self.config["model"]
        prompt_template = self.config["prompt_template"]

        # 프롬프트 빌드 (context 데이터로 치환)
        prompt = self._build_prompt(prompt_template, context)

        # LLM 요청
        messages = [LLMMessage(role=MessageRole.USER, content=prompt)]

        response = await self.llm_service.complete_with_retry(
            model=model,
            messages=messages,
            max_tokens=self.config.get("max_tokens", 500),
            temperature=self.config.get("temperature", 0.7)
        )

        # JSON 파싱
        from app.services.llm import LLMResponseParser
        result = LLMResponseParser.extract_json(response.content)

        return result

    async def _execute_sentiment(self, context: Dict[str, Any]) -> dict:
        """감성 분석 실행"""
        source = self.config["source"]
        source_count = self.config["source_count"]

        # 뉴스 데이터 가져오기
        news_data = context.get("news", [])[:source_count]

        # 감성 분석 프롬프트
        prompt = self._build_sentiment_prompt(news_data)

        messages = [LLMMessage(role=MessageRole.USER, content=prompt)]

        response = await self.llm_service.complete_with_retry(
            model=self.config["model"],
            messages=messages
        )

        from app.services.llm import LLMResponseParser
        result = LLMResponseParser.extract_json(response.content)

        return result

    def _build_prompt(self, template: str, context: Dict[str, Any]) -> str:
        """프롬프트 빌드"""
        from jinja2 import Template
        tmpl = Template(template)
        return tmpl.render(**context)

    def _build_sentiment_prompt(self, news_data: List[dict]) -> str:
        """감성 분석 프롬프트 빌드"""
        # 프롬프트 템플릿 적용
        pass
```

---

### 3.6 Action 노드 실행

```python
class ActionExecutor(BaseNodeExecutor):
    """액션 실행"""

    def __init__(self, config: dict, exchange: ExchangeService):
        super().__init__(config)
        self.exchange = exchange

    async def execute(self, context: Dict[str, Any]) -> Any:
        action_type = self.config["action_type"]

        if action_type == "buy":
            return await self._execute_buy()
        elif action_type == "sell":
            return await self._execute_sell()
        elif action_type == "stop_loss":
            return await self._execute_stop_loss(context)
        elif action_type == "take_profit":
            return await self._execute_take_profit(context)
        elif action_type == "notify":
            return await self._execute_notify(context)
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def _execute_buy(self) -> dict:
        """매수 실행"""
        symbol = self.config["symbol"]
        order_type = self.config["order_type"]
        amount = self.config["amount"]
        amount_unit = self.config["amount_unit"]

        if order_type == "market":
            # 시장가 주문
            order = await self.exchange.create_market_buy_order(
                symbol=symbol,
                amount=amount,
                amount_unit=amount_unit
            )
        else:
            # 지정가 주문
            price = self.config.get("price")
            order = await self.exchange.create_limit_buy_order(
                symbol=symbol,
                amount=amount,
                amount_unit=amount_unit,
                price=price
            )

        return {
            "order_id": order["id"],
            "symbol": symbol,
            "side": "buy",
            "order_type": order_type,
            "price": order.get("price") or order.get("average_price"),
            "amount": order["filled"],
            "executed": order["status"] == "closed",
            "timestamp": order["timestamp"]
        }

    async def _execute_sell(self) -> dict:
        """매도 실행"""
        # 매수와 유사하게 구현
        pass

    async def _execute_stop_loss(self, context: Dict[str, Any]) -> dict:
        """손절 주문 설정"""
        symbol = self.config["symbol"]
        trigger_price = self.config["trigger_price"]
        amount = self.config["amount"]

        # 손절 주문 생성 (거래소 지원 OCO/Stop-Limit)
        order = await self.exchange.create_stop_loss_order(
            symbol=symbol,
            trigger_price=trigger_price,
            amount=amount
        )

        return {
            "order_id": order["id"],
            "type": "stop_loss",
            "trigger_price": trigger_price,
            "timestamp": order["timestamp"]
        }

    async def _execute_take_profit(self, context: Dict[str, Any]) -> dict:
        """익절 주문 설정"""
        # 손절과 유사하게 구현
        pass

    async def _execute_notify(self, context: Dict[str, Any]) -> dict:
        """알림 전송"""
        message = self.config["message"]
        channels = self.config.get("channels", ["web"])

        # 알림 서비스 호출
        from app.services.notification import NotificationService
        notify_service = NotificationService()

        for channel in channels:
            await notify_service.send(channel, message)

        return {
            "channels": channels,
            "message": message,
            "sent_at": datetime.utcnow().isoformat()
        }
```

---

## 4. 흐름 제어 (Flow Control)

### 4.1 Execution Engine

```python
import asyncio
from typing import Dict, List, Set

class ExecutionEngine:
    """전략 실행 엔진"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: LLMService,
        exchange: ExchangeService
    ):
        self.db = db
        self.llm_service = llm_service
        self.exchange = exchange
        self.scheduler = TriggerScheduler(self)
        self._executors = self._init_executors()
        self._running_executions: Dict[str, asyncio.Task] = {}

    def _init_executors(self) -> Dict[str, type]:
        """노드 실행자 초기화"""
        return {
            "data_source": DataSourceExecutor,
            "indicator": IndicatorExecutor,
            "condition": ConditionExecutor,
            "llm": lambda cfg: LLMExecutor(cfg, self.llm_service),
            "action": lambda cfg: ActionExecutor(cfg, self.exchange)
        }

    async def execute_strategy(self, strategy_id: str):
        """전략 실행"""
        # 전략 조회
        strategy = await self._load_strategy(strategy_id)

        # 실행 기록 생성
        execution = await self._create_execution(strategy_id)

        try:
            # 노드 실행 순서 계산 (위상 정렬)
            execution_order = self._calculate_execution_order(strategy)

            # 컨텍스트 초기화
            context = {}

            # 노드 순서대로 실행
            results = []
            for node_id in execution_order:
                node = self._get_node_by_id(strategy, node_id)

                # 조건 노드 분기 처리
                if node["type"] == "condition":
                    result = await self._execute_condition_with_branching(
                        node, context, strategy, results
                    )
                    if result["stop"]:
                        break
                else:
                    result = await self._execute_node(node, context)
                    results.append(result)

                # 컨텍스트 업데이트
                if result["status"] == ExecutionStatus.SUCCESS:
                    context[node_id] = result["data"]

            # 실행 상태 업데이트
            await self._update_execution_status(
                execution["id"],
                ExecutionStatus.SUCCESS,
                results=results
            )

        except Exception as e:
            await self._update_execution_status(
                execution["id"],
                ExecutionStatus.FAILED,
                error=str(e)
            )
            raise

    async def _execute_node(
        self,
        node: dict,
        context: Dict[str, Any]
    ) -> NodeExecutionResult:
        """단일 노드 실행"""
        node_type = node["type"]
        config = node["config"]

        # 실행자 생성
        executor_class = self._executors.get(node_type)
        if not executor_class:
            return NodeExecutionResult(
                node_id=node["id"],
                status=ExecutionStatus.FAILED,
                error=f"Unknown node type: {node_type}"
            )

        executor = executor_class(config)

        # 실행 (재시도 포함)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = await executor.execute(context)
                return NodeExecutionResult(
                    node_id=node["id"],
                    status=ExecutionStatus.SUCCESS,
                    data=data
                )
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return NodeExecutionResult(
                        node_id=node["id"],
                        status=ExecutionStatus.FAILED,
                        error=str(e)
                    )

    async def _execute_condition_with_branching(
        self,
        node: dict,
        context: Dict[str, Any],
        strategy: dict,
        results: list
    ) -> dict:
        """조건 노드 실행 후 분기 처리"""
        # 조건 실행
        result = await self._execute_node(node, context)
        results.append(result)

        if result["status"] != ExecutionStatus.SUCCESS:
            return {"stop": True}

        condition_result = result["data"]["result"]

        # 분기 경로 찾기
        edges = self._find_edges_from_node(strategy, node["id"])

        true_edges = [e for e in edges if e.get("condition") == "true"]
        false_edges = [e for e in edges if e.get("condition") == "false"]

        # 분기 실행
        target_edges = true_edges if condition_result else false_edges

        for edge in target_edges:
            next_node_id = edge["to"]
            next_node = self._get_node_by_id(strategy, next_node_id)

            # 다음 노드 실행
            next_result = await self._execute_node(next_node, context)
            results.append(next_result)

            if next_result["status"] == ExecutionStatus.SUCCESS:
                context[next_node_id] = next_result["data"]

        return {"stop": False}

    def _calculate_execution_order(self, strategy: dict) -> List[str]:
        """위상 정렬로 실행 순서 계산"""
        from .validation import TopologicalSort

        nodes = [Node(**n) for n in strategy["nodes"]]
        edges = [
            Edge(from_node=e["from"], to_node=e["to"])
            for e in strategy["edges"]
        ]

        topo_sort = TopologicalSort(nodes, edges)
        return topo_sort.sort()

    def _get_node_by_id(self, strategy: dict, node_id: str) -> dict:
        """ID로 노드 찾기"""
        for node in strategy["nodes"]:
            if node["id"] == node_id:
                return node
        raise ValueError(f"Node not found: {node_id}")

    def _find_edges_from_node(self, strategy: dict, node_id: str) -> List[dict]:
        """노드에서 나가는 엣지 찾기"""
        return [
            edge for edge in strategy["edges"]
            if edge["from"] == node_id
        ]

    async def _load_strategy(self, strategy_id: str) -> dict:
        """전략 로드 (DB에서)"""
        from app.models.strategy import Strategy
        from sqlalchemy import select

        result = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise ValueError(f"Strategy not found: {strategy_id}")

        return strategy.definition

    async def _create_execution(self, strategy_id: str) -> dict:
        """실행 기록 생성"""
        from app.models.execution import Execution

        execution = Execution(
            strategy_id=strategy_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def _update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        results: list | None = None,
        error: str | None = None
    ):
        """실행 상태 업데이트"""
        from app.models.execution import Execution
        from sqlalchemy import select

        result = await self.db.execute(
            select(Execution).where(Execution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if execution:
            execution.status = status
            if status == ExecutionStatus.SUCCESS:
                execution.completed_at = datetime.utcnow()
            if error:
                execution.error = error
            if results:
                execution.results = results

            await self.db.commit()
```

---

## 5. 결과 처리 (Result Handler)

### 5.1 실행 결과 저장

```python
class ResultHandler:
    """결과 처리기"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_execution_results(
        self,
        execution_id: str,
        results: List[NodeExecutionResult]
    ):
        """실행 결과 저장"""
        from app.models.execution_result import ExecutionResult

        for result in results:
            execution_result = ExecutionResult(
                execution_id=execution_id,
                node_id=result.node_id,
                status=result.status.value,
                result_data=result.data,
                error=result.error
            )
            self.db.add(execution_result)

        await self.db.commit()

    async def publish_events(
        self,
        strategy_id: str,
        execution_id: str,
        results: List[NodeExecutionResult]
    ):
        """이벤트 발행 (WebSocket, Redis Pub/Sub 등)"""
        # 액션 결과만 필터링
        actions = [r for r in results if r.data and "order_id" in r.data]

        if actions:
            event = {
                "type": "strategy_execution",
                "strategy_id": strategy_id,
                "execution_id": execution_id,
                "actions": [r.data for r in actions],
                "timestamp": datetime.utcnow().isoformat()
            }

            # Redis Pub/Sub
            await redis_client.publish(
                f"strategy:{strategy_id}",
                json.dumps(event)
            )
```

---

## 6. FastAPI 엔드포인트

### 6.1 전략 배포/중지

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/strategies/{strategy_id}/deploy")
async def deploy_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """전략 배포"""
    # 전략 조회 및 검증
    strategy = await get_strategy_with_auth(strategy_id, current_user.id, db)

    # 실행 엔진에 등록
    engine = get_execution_engine()
    await engine.scheduler.register_strategy(strategy_id, strategy.definition)

    # 상태 업데이트
    strategy.status = "deployed"
    await db.commit()

    return {"status": "deployed", "strategy_id": strategy_id}

@router.post("/strategies/{strategy_id}/pause")
async def pause_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """전략 일시 중지"""
    strategy = await get_strategy_with_auth(strategy_id, current_user.id, db)

    # 스케줄러에서 제거
    engine = get_execution_engine()
    await engine.scheduler.unregister_strategy(strategy_id)

    # 상태 업데이트
    strategy.status = "paused"
    await db.commit()

    return {"status": "paused", "strategy_id": strategy_id}
```

---

### 6.2 실행 기록 조회

```python
@router.get("/strategies/{strategy_id}/executions")
async def get_strategy_executions(
    strategy_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """전략 실행 기록 조회"""
    from sqlalchemy import select
    from app.models.execution import Execution

    result = await db.execute(
        select(Execution)
        .where(Execution.strategy_id == strategy_id)
        .order_by(Execution.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    executions = result.scalars().all()

    return {
        "items": executions,
        "total": len(executions),
        "limit": limit,
        "offset": offset
    }
```

---

## 7. 환경 변수

```bash
# .env
# 스케줄러
SCHEDULER_MAX_WORKERS=10
SCHEDULER_JOB_DEFAULTS='{"coalesce": true, "max_instances": 1}'

# 실행 엔진
EXECUTION_TIMEOUT=300
NODE_EXECUTION_MAX_RETRIES=3
NODE_EXECUTION_RETRY_DELAY=1

# 거래소
EXCHANGE_API_KEY=...
EXCHANGE_API_SECRET=...
EXCHANGE_SANDBOX=false
```

---

## 8. 상위/관련 문서

- **[../index.md](../index.md)** - 전략 시스템 개요
- **[node-types.md](./node-types.md)** - 노드 타입 상세
- **[validation-rules.md](./validation-rules.md)** - 검증 규칙
- **[llm-integration.md](./llm-integration.md)** - LLM 연동

---

*최종 업데이트: 2025-12-29*
