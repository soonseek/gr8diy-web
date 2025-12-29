# LLM 연동 (LLM Integration)

전략 시스템에서 LLM(Large Language Model)을 통합하여 자연어 기반 전략 생성, 분석, 의사결정을 구현합니다.

---

## 1. 아키텍처 개요

### 1.1 Model Pool 방식

여러 LLM 제공자(OpenAI, Anthropic, GLM 등)를 통합하여 추상화된 인터페이스로 관리합니다.

```
┌─────────────────────────────────────────────────┐
│           Strategy LLM Service                  │
│  - 전략 생성                                    │
│  - 시장 분석                                    │
│  - 감성 분석                                    │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          LLM Provider Pool                      │
│  - Model Registry                               │
│  - Cost Tracker                                 │
│  - Rate Limiter                                 │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┬───────────┐
      ▼           ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ OpenAI   │ │Anthropic │ │  GLM     │ │Custom... │
│ Provider │ │Provider  │ │Provider  │ │Provider  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### 1.2 지원 모델

| 제공자 | 모델 | Context | 용도 |
|--------|------|---------|------|
| **OpenAI** | GPT-4 Turbo | 128K | 전략 생성, 복잡한 분석 |
| **OpenAI** | GPT-3.5 Turbo | 16K | 단순 분석, 감성 분석 |
| **Anthropic** | Claude 3 Opus | 200K | 장기 문맥 분석 |
| **Anthropic** | Claude 3 Sonnet | 200K | 비용 효율적 분석 |
| **GLM** | GLM-4 | 128K | 중국어 시장 분석 |
| **Custom** | Custom Endpoint | 가변 | 자체 호스팅 모델 |

---

## 2. 추상화된 Provider 인터페이스

### 2.1 Base Provider

모든 LLM 제공자가 따라야 하는 기본 인터페이스입니다.

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum

class LLMProviderType(str, Enum):
    """LLM 제공자 타입"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GLM = "glm"
    CUSTOM = "custom"

class MessageRole(str, Enum):
    """메시지 역할"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class LLMMessage:
    """LLM 메시지"""
    role: MessageRole
    content: str

@dataclass
class LLMResponse:
    """LLM 응답"""
    content: str
    model: str
    tokens_used: int
    cost: float
    provider: LLMProviderType
    finish_reason: str  # "stop", "length", "content_filter"

@dataclass
class LLMRequest:
    """LLM 요청"""
    model: str
    messages: List[LLMMessage]
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = False

class BaseLLMProvider(ABC):
    """LLM 제공자 기본 클래스"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """텍스트 완성 요청"""
        pass

    @abstractmethod
    async def stream_complete(self, request: LLMRequest):
        """스트리밍 텍스트 완성"""
        pass

    @abstractmethod
    def estimate_cost(self, model: str, tokens: int) -> float:
        """토큰 수에 따른 비용 추정"""
        pass

    @abstractmethod
    def get_max_context(self, model: str) -> int:
        """모델별 최대 컨텍스트 길이"""
        pass
```

---

### 2.2 OpenAI Provider

```python
import aiohttp
import tiktoken

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API 제공자"""

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )
        self.encoding = tiktoken.encoding_for_model("gpt-4")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": request.model,
            "messages": [
                {"role": m.role.value, "content": m.content}
                for m in request.messages
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {error_text}")

                data = await response.json()
                choice = data["choices"][0]

                # 토큰 수
                tokens_used = data["usage"]["total_tokens"]

                # 비용 계산
                cost = self.estimate_cost(request.model, tokens_used)

                return LLMResponse(
                    content=choice["message"]["content"],
                    model=request.model,
                    tokens_used=tokens_used,
                    cost=cost,
                    provider=LLMProviderType.OPENAI,
                    finish_reason=choice["finish_reason"]
                )

    def estimate_cost(self, model: str, tokens: int) -> float:
        """OpenAI 가격표 (2025년 기준)"""
        prices = {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},  # per 1K tokens
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }

        if model not in prices:
            # 기본가 (GPT-3.5)
            input_cost = tokens * 0.0005 / 1000
            output_cost = tokens * 0.0015 / 1000
            return input_cost + output_cost

        # 입력:출력 = 7:3 가정
        input_tokens = int(tokens * 0.7)
        output_tokens = tokens - input_tokens

        price = prices[model]
        input_cost = input_tokens * price["input"] / 1000
        output_cost = output_tokens * price["output"] / 1000

        return input_cost + output_cost

    def get_max_context(self, model: str) -> int:
        contexts = {
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385
        }
        return contexts.get(model, 4096)

    async def stream_complete(self, request: LLMRequest):
        """스트리밍 완성 (구현 생략)"""
        pass
```

---

### 2.3 Anthropic Provider

```python
class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API 제공자"""

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.anthropic.com/v1"
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        # Anthropic은 시스템 프롬프트를 별도로 처리
        system_message = ""
        messages = []

        for msg in request.messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }

        if system_message:
            payload["system"] = system_message

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {error_text}")

                data = await response.json()

                # Anthropic은 사용 토큰을 응답에 포함하지 않음
                tokens_used = self._estimate_tokens(request.messages + [
                    LLMMessage(role=MessageRole.ASSISTANT, content=data["content"][0]["text"])
                ])

                cost = self.estimate_cost(request.model, tokens_used)

                return LLMResponse(
                    content=data["content"][0]["text"],
                    model=request.model,
                    tokens_used=tokens_used,
                    cost=cost,
                    provider=LLMProviderType.ANTHROPIC,
                    finish_reason=data["stop_reason"]
                )

    def estimate_cost(self, model: str, tokens: int) -> float:
        """Anthropic 가격표 (2025년 기준)"""
        prices = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015}
        }

        if model not in prices:
            # 기본가 (Sonnet)
            price = prices["claude-3-sonnet"]
        else:
            price = prices[model]

        input_tokens = int(tokens * 0.7)
        output_tokens = tokens - input_tokens

        input_cost = input_tokens * price["input"] / 1000
        output_cost = output_tokens * price["output"] / 1000

        return input_cost + output_cost

    def get_max_context(self, model: str) -> int:
        return 200000  # Claude 3 시리즈

    def _estimate_tokens(self, messages: List[LLMMessage]) -> int:
        """토큰 수 추정 (간단: 문자 수 / 4)"""
        total_chars = sum(len(m.content) for m in messages)
        return total_chars // 4

    async def stream_complete(self, request: LLMRequest):
        pass
```

---

### 2.4 Model Registry & Pool

```python
from typing import Dict

class LLMModelRegistry:
    """LLM 모델 등록기"""

    _models: Dict[str, Dict[str, Any]] = {
        # OpenAI
        "gpt-4-turbo": {
            "provider": LLMProviderType.OPENAI,
            "max_tokens": 128000,
            "cost_per_1k": {"input": 0.01, "output": 0.03},
            "recommended_for": ["strategy_generation", "complex_analysis"]
        },
        "gpt-3.5-turbo": {
            "provider": LLMProviderType.OPENAI,
            "max_tokens": 16385,
            "cost_per_1k": {"input": 0.0005, "output": 0.0015},
            "recommended_for": ["sentiment", "simple_analysis"]
        },

        # Anthropic
        "claude-3-opus": {
            "provider": LLMProviderType.ANTHROPIC,
            "max_tokens": 200000,
            "cost_per_1k": {"input": 0.015, "output": 0.075},
            "recommended_for": ["strategy_generation", "long_context"]
        },
        "claude-3-sonnet": {
            "provider": LLMProviderType.ANTHROPIC,
            "max_tokens": 200000,
            "cost_per_1k": {"input": 0.003, "output": 0.015},
            "recommended_for": ["analysis", "cost_efficient"]
        },

        # GLM (확장 가능)
        "glm-4": {
            "provider": LLMProviderType.GLM,
            "max_tokens": 128000,
            "cost_per_1k": {"input": 0.001, "output": 0.002},
            "recommended_for": ["chinese_market"]
        }
    }

    @classmethod
    def get_model_info(cls, model: str) -> Dict[str, Any] | None:
        return cls._models.get(model)

    @classmethod
    def list_models(cls) -> List[str]:
        return list(cls._models.keys())

    @classmethod
    def get_models_by_provider(cls, provider: LLMProviderType) -> List[str]:
        return [
            model for model, info in cls._models.items()
            if info["provider"] == provider
        ]

    @classmethod
    def get_recommended_model(cls, use_case: str) -> str | None:
        for model, info in cls._models.items():
            if use_case in info["recommended_for"]:
                return model
        return "gpt-3.5-turbo"  # 기본 모델

class LLMProviderPool:
    """LLM 제공자 풀"""

    def __init__(self):
        self._providers: Dict[LLMProviderType, BaseLLMProvider] = {}

    def register(self, provider_type: LLMProviderType, provider: BaseLLMProvider):
        """제공자 등록"""
        self._providers[provider_type] = provider

    def get_provider(self, model: str) -> BaseLLMProvider:
        """모델에 해당하는 제공자 반환"""
        model_info = LLMModelRegistry.get_model_info(model)

        if not model_info:
            raise ValueError(f"Unknown model: {model}")

        provider_type = model_info["provider"]
        provider = self._providers.get(provider_type)

        if not provider:
            raise ValueError(f"Provider not registered: {provider_type}")

        return provider

    async def complete(
        self,
        model: str,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """모델 지정 완성"""
        provider = self.get_provider(model)

        request = LLMRequest(
            model=model,
            messages=messages,
            **kwargs
        )

        return await provider.complete(request)
```

---

## 3. 프롬프트 엔지니어링

### 3.1 전략 생성 프롬프트

```python
class PromptTemplates:
    """프롬프트 템플릿 모음"""

    STRATEGY_GENERATION = """당신은 암호화폐 자동매매 전략 생성 전문가입니다.

## 사용자 요청
{user_prompt}

## 요구사항
1. n8n/Zapier 스타일의 노드-엣지 구조로 생성
2. 트리거 노드는 정확히 1개
3. 최소 1개의 조건 노드 포함
4. 액션 노드 포함 (매수/매도/알림)

## 출력 형식 (JSON only)
```json
{{
  "name": "전략 이름",
  "description": "전략 설명 (1-2문장)",
  "nodes": [
    {{
      "id": "trigger_1",
      "type": "trigger",
      "config": {{
        "trigger_type": "time|price_change|volume",
        ...
      }}
    }},
    {{
      "id": "data_1",
      "type": "data_source",
      "config": {{
        "source_type": "ohlcv|orderbook|news",
        ...
      }}
    }},
    {{
      "id": "condition_1",
      "type": "condition",
      "config": {{
        "operator": "<|>|<=|>=|==|!=",
        "left": "참조",
        "right": "값"
      }}
    }},
    {{
      "id": "action_1",
      "type": "action",
      "config": {{
        "action_type": "buy|sell|notify",
        ...
      }}
    }}
  ],
  "edges": [
    {{"from": "trigger_1", "to": "data_1"}},
    {{"from": "data_1", "to": "condition_1"}},
    {{"from": "condition_1", "to": "action_1", "condition": "true"}}
  ]
}}
```

## 제약 조건
- 순환 구조 불가
- 노드 ID는 소문자 + 숫자 (예: trigger_1, data_1)
- symbol은 "BTC/USDT" 형식 (대문자)
- amount는 USDT 또는 base coin 단위
"""

    MARKET_ANALYSIS = """다음 시장 데이터를 분석하여 매매 추천을 제공하세요.

## 데이터
- 심볼: {symbol}
- 현재 가격: ${price}
- 24시간 변동률: {change_24h}%
- 거래량: {volume}
- RSI(14): {rsi}
- MACD: {macd_signal}
- 볼린저 밴드: {bb_position}

## 출력 형식 (JSON only)
```json
{{
  "analysis": "시장 상황 분석 (2-3문장)",
  "trend": "UPTREND|DOWNTREND|SIDEWAYS",
  "recommendation": "BUY|SELL|HOLD",
  "confidence": 0.75,
  "reason": "추천 이유 (1-2문장)",
  "risk_level": "LOW|MEDIUM|HIGH"
}}
```
"""

    NEWS_SENTIMENT = """다음 암호화폐 뉴스의 감성을 분석하세요.

## 뉴스
제목: {title}
내용: {content}
출처: {source}
시간: {published_at}

## 출력 형식 (JSON only)
```json
{{
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
  "score": 0.75,
  "keywords": ["비트코인", "ETF", "승인"],
  "summary": "뉴스 요약 (1문장)",
  "impact": "HIGH|MEDIUM|LOW",
  "price_implication": "BULLISH|BEARISH|NEUTRAL"
}}
```
"""

    STRATEGY_OPTIMIZATION = """다음 전략을 최적화하세요.

## 현재 전략
{current_strategy}

## 성능 이슈
- 수익률: {return_pct}%
- 최대 손실: {max_drawdown}%
- 승률: {win_rate}%
- 샤프 비율: {sharpe_ratio}

## 최적화 방향
1. 파라미터 조정 (RSI 기간, 임계값 등)
2. 필터 추가 (거래량, 변동률)
3. 리스크 관리 강화

## 출력 형식 (JSON only)
```json
{{
  "optimized_strategy": {{...}},
  "changes": ["RSI 기간 14→20", "거래량 필터 추가"],
  "expected_improvement": {{
    "return_pct": "+5%",
    "max_drawdown": "-3%",
    "win_rate": "+10%"
  }}
}}
```
"""
```

---

### 3.2 프롬프트 빌더

```python
from jinja2 import Template

class PromptBuilder:
    """프롬프트 빌더"""

    @staticmethod
    def build_strategy_generation(user_prompt: str) -> str:
        """전략 생성 프롬프트"""
        template = Template(PromptTemplates.STRATEGY_GENERATION)
        return template.render(user_prompt=user_prompt)

    @staticmethod
    def build_market_analysis(
        symbol: str,
        price: float,
        change_24h: float,
        volume: float,
        rsi: float,
        macd_signal: str,
        bb_position: str
    ) -> str:
        """시장 분석 프롬프트"""
        template = Template(PromptTemplates.MARKET_ANALYSIS)
        return template.render(
            symbol=symbol,
            price=price,
            change_24h=change_24h,
            volume=volume,
            rsi=rsi,
            macd_signal=macd_signal,
            bb_position=bb_position
        )

    @staticmethod
    def build_news_sentiment(
        title: str,
        content: str,
        source: str,
        published_at: str
    ) -> str:
        """뉴스 감성 분석 프롬프트"""
        template = Template(PromptTemplates.NEWS_SENTIMENT)
        return template.render(
            title=title,
            content=content,
            source=source,
            published_at=published_at
        )
```

---

## 4. 비용 관리

### 4.1 Token 사용량 추적

```python
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

class LLMUsage(Base):
    """LLM 사용량 추적 테이블"""
    __tablename__ = "llm_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    request_type = Column(String(50))  # strategy_generation, analysis, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class CostTracker:
    """비용 추적기"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_usage(
        self,
        user_id: str,
        response: LLMResponse,
        request_type: str
    ):
        """사용량 기록"""
        usage = LLMUsage(
            user_id=user_id,
            model=response.model,
            provider=response.provider.value,
            tokens_used=response.tokens_used,
            cost=response.cost,
            request_type=request_type
        )
        self.db.add(usage)
        await self.db.commit()

    async def get_user_monthly_cost(self, user_id: str) -> float:
        """사용자 월간 비용 조회"""
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)

        result = await self.db.execute(
            select(func.sum(LLMUsage.cost))
            .where(
                LLMUsage.user_id == user_id,
                LLMUsage.created_at >= start_of_month
            )
        )
        return result.scalar() or 0.0

    async def check_quota(self, user_id: str, estimated_cost: float) -> bool:
        """할당량 확인"""
        monthly_cost = await self.get_user_monthly_cost(user_id)
        monthly_limit = 10.0  # 월 $10 제한

        return (monthly_cost + estimated_cost) <= monthly_limit
```

---

### 4.2 캐싱 전략

```python
from app.core.redis import redis_client
import hashlib
import json

class LLMCache:
    """LLM 응답 캐싱"""

    def __init__(self, ttl_seconds: int = 900):  # 15분 기본
        self.ttl = ttl_seconds

    def _make_cache_key(
        self,
        model: str,
        messages: List[LLMMessage],
        temperature: float
    ) -> str:
        """캐시 키 생성"""
        content = f"{model}:{temperature}:{[m.content for m in messages]}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(
        self,
        model: str,
        messages: List[LLMMessage],
        temperature: float
    ) -> str | None:
        """캐시된 응답 조회"""
        key = self._make_cache_key(model, messages, temperature)
        cached = await redis_client.get(f"llm_cache:{key}")
        return cached

    async def set(
        self,
        model: str,
        messages: List[LLMMessage],
        temperature: float,
        response: str
    ):
        """응답 캐싱"""
        key = self._make_cache_key(model, messages, temperature)
        await redis_client.setex(
            f"llm_cache:{key}",
            self.ttl,
            response
        )
```

---

## 5. 응답 처리

### 5.1 응답 파서

```python
import json
from typing import TypeVar, Type

T = TypeVar('T', bound=BaseModel)

class LLMResponseParser:
    """LLM 응답 파서"""

    @staticmethod
    def extract_json(content: str) -> dict:
        """JSON 추출 (markdown code block 처리)"""
        content = content.strip()

        # ```json ... ``` 제거
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()

        return json.loads(content)

    @staticmethod
    def parse_as(content: str, model: Type[T]) -> T:
        """Pydantic 모델로 파싱"""
        data = LLMResponseParser.extract_json(content)
        return model(**data)

    @staticmethod
    def extract_code_blocks(content: str) -> list[str]:
        """코드 블록 추출"""
        import re
        pattern = r'```(?:json|python)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        return matches
```

---

### 5.2 에러 처리 및 재시도

```python
import asyncio
from enum import Enum

class RetryStrategy(Enum):
    """재시도 전략"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"

class LLMService:
    """LLM 서비스 (재시도 포함)"""

    def __init__(
        self,
        provider_pool: LLMProviderPool,
        max_retries: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    ):
        self.pool = provider_pool
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy

    async def complete_with_retry(
        self,
        model: str,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """재시도 포함 완성"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self.pool.complete(model, messages, **kwargs)

            except Exception as e:
                last_error = e

                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise Exception(
                        f"LLM request failed after {self.max_retries} attempts: {str(e)}"
                    ) from last_error

    def _calculate_delay(self, attempt: int) -> float:
        """재시도 딜레이 계산"""
        if self.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return 2 ** attempt  # 1, 2, 4초
        elif self.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            return (attempt + 1) * 1  # 1, 2, 3초
        else:  # FIXED_DELAY
            return 1.0
```

---

## 6. FastAPI 통합

### 6.1 Service 구현

```python
from app.core.config import settings
from app.db.session import get_db

class StrategyLLMService:
    """전략 LLM 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pool = self._init_provider_pool()
        self.cost_tracker = CostTracker(db)
        self.cache = LLMCache()
        self.service = LLMService(self.pool)

    def _init_provider_pool(self) -> LLMProviderPool:
        """제공자 풀 초기화"""
        pool = LLMProviderPool()

        # OpenAI
        if settings.OPENAI_API_KEY:
            pool.register(
                LLMProviderType.OPENAI,
                OpenAIProvider(api_key=settings.OPENAI_API_KEY)
            )

        # Anthropic
        if settings.ANTHROPIC_API_KEY:
            pool.register(
                LLMProviderType.ANTHROPIC,
                AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
            )

        return pool

    async def generate_strategy(
        self,
        user_id: str,
        prompt: str,
        model: str | None = None
    ) -> dict:
        """전략 생성"""
        # 모델 선택
        if not model:
            model = LLMModelRegistry.get_recommended_model("strategy_generation")

        # 프롬프트 빌드
        full_prompt = PromptBuilder.build_strategy_generation(prompt)

        # 캐시 확인
        cached = await self.cache.get(
            model,
            [LLMMessage(role=MessageRole.USER, content=full_prompt)],
            temperature=0.7
        )
        if cached:
            return json.loads(cached)

        # 비용 확인
        model_info = LLMModelRegistry.get_model_info(model)
        estimated_tokens = 2000  # 추정
        estimated_cost = (
            estimated_tokens * model_info["cost_per_1k"]["input"] / 1000
        )

        if not await self.cost_tracker.check_quota(user_id, estimated_cost):
            raise Exception("Monthly quota exceeded")

        # LLM 요청
        messages = [
            LLMMessage(role=MessageRole.USER, content=full_prompt)
        ]

        response = await self.service.complete_with_retry(
            model=model,
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        # 응답 파싱
        strategy_data = LLMResponseParser.extract_json(response.content)

        # 캐싱
        await self.cache.set(model, messages, 0.7, json.dumps(strategy_data))

        # 사용량 기록
        await self.cost_tracker.record_usage(user_id, response, "strategy_generation")

        return strategy_data
```

---

### 6.2 API 엔드포인트

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter()

class StrategyGenerationRequest(BaseModel):
    prompt: str
    model: str | None = None

class StrategyGenerationResponse(BaseModel):
    strategy: dict
    model: str
    tokens_used: int
    cost: float

@router.post("/llm/generate-strategy", response_model=StrategyGenerationResponse)
async def generate_strategy(
    request: StrategyGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """LLM 기반 전략 생성"""
    service = StrategyLLMService(db)

    try:
        strategy_data = await service.generate_strategy(
            user_id=str(current_user.id),
            prompt=request.prompt,
            model=request.model
        )

        return StrategyGenerationResponse(
            strategy=strategy_data,
            model=request.model or "gpt-4-turbo",
            tokens_used=0,  # 실제 응답에서 가져옴
            cost=0.0
        )

    except Exception as e:
        if "Monthly quota exceeded" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error_code": "QUOTA_EXCEEDED", "message": str(e)}
            )
        raise
```

---

## 7. Pydantic Schemas

```python
from pydantic import BaseModel, Field

class LLMMessageSchema(BaseModel):
    role: str
    content: str

class LLMRequestSchema(BaseModel):
    model: str = Field(..., description="LLM 모델")
    messages: list[LLMMessageSchema]
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)

class LLMResponseSchema(BaseModel):
    content: str
    model: str
    tokens_used: int
    cost: float
    provider: str
    finish_reason: str

class LLMUsageSchema(BaseModel):
    id: str
    user_id: str
    model: str
    provider: str
    tokens_used: int
    cost: float
    request_type: str
    created_at: datetime
```

---

## 8. 환경 변수

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GLM_API_KEY=...

# LLM 설정
LLM_DEFAULT_MODEL=gpt-4-turbo
LLM_MAX_RETRIES=3
LLM_REQUEST_TIMEOUT=30
LLM_CACHE_TTL=900

# 비용 제한
LLM_MONTHLY_QUOTA_USD=10.0
```

---

## 9. 상위/관련 문서

- **[../index.md](../index.md)** - 전략 시스템 개요
- **[node-types.md](./node-types.md)** - LLM 노드 타입 상세
- **[validation-rules.md](./validation-rules.md)** - 검증 규칙

---

*최종 업데이트: 2025-12-29*
