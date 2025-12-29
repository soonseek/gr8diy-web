# 전략 (Strategy)

## 1. 개요

**Strategy Editor**는 n8n, Zapier와 유사한 **Node-Edge 기반 비주얼 에디터**로, 사용자가 코딩 없이 자동매매 전략을 생성할 수 있습니다.

## 2. 에디터 구조

### 2.1 노드 (Node)
노드는 전략의 **개별 작업 단위**입니다.

| 노드 타입 | 설명 | 예시 |
|----------|------|------|
| **트리거** | 전략 실행 시작 조건 | 시간, 가격 변동률, 거래량 |
| **데이터 소스** | 시장 데이터 수집 | OHLCV, 호가, 거래량 |
| **조건** | 분기 로직 | RSI < 30, 볼린저 밴드 돌파 |
| **LLM** | 자연어 처리 | 뉴스 감성 분석, 시장 해석 |
| **액션** | 매수/매도 실행 | 시장가/지정가 주문 |
| **리스크 관리** | 손절/익절 | Stop Loss, Take Profit |

### 2.2 엣지 (Edge)
엣지는 노드 간 **데이터 흐름**을 정의합니다.
- **순서**: 트리거 → 데이터 → 조건 → 액션
- **분기**: 조건 노드에서 True/False 경로 분리
- **병합**: 여러 경로가 하나의 액션으로 수렴

### 2.3 검증 규칙
- **순환 불가**: 엣지가 순환 구조를 형성하면 안 됨
- **트리거 단일**: 전략에 트리거는 1개만 허용
- **타입 일치**: 노드 간 데이터 타입이 호환되어야 함

## 3. 전략 생성 플로우

### 3.1 수동 생성
```
1. 에디터 진입
2. 트리거 노드 배치 (예: "BTC 가격 1% 상승 시")
3. 데이터 소스 노드 연결 (예: "BTC/USDT 1시간봉")
4. 조건 노드 추가 (예: "RSI < 30")
5. 액션 노드 추가 (예: "매수 $1000")
6. 파라미터 설정 (각 노드별 상세값)
7. 저장 및 배포
```

### 3.2 LLM 자동 생성

**LLM 기반 전략 생성**은 자연어 프롬프트에서 전략 노드 구조를 자동으로 생성합니다.

```
1. 프롬프트 입력: "BTC가 떨어질 때 매수하는 전략 만들어줘"
2. LLM이 노드 구조 생성 (JSON 형식)
3. 사용자가 생성된 전략 검토 및 수정
4. 저장 및 배포
```

**프롬프트 예시**:
- "BTC가 5% 이상 하락하면 RSI 확인 후 매수"
- "이동평균선 골든크로스 발생 시 매수"
- "뉴스 감성 분석 결과가 긍정적일 때 매수"

**LLM 응답 형식**:
```json
{
  "name": "BTC Dip Buy Strategy",
  "description": "BTC가 5% 이상 하락 시 RSI 확인 후 매수",
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "config": {
        "trigger_type": "price_change",
        "symbol": "BTC/USDT",
        "threshold": -0.05,
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
        "operator": "AND",
        "conditions": [
          { "left": "indicator_1.value", "op": "<", "right": 30 }
        ]
      }
    },
    {
      "id": "action_1",
      "type": "action",
      "config": {
        "action_type": "buy",
        "order_type": "market",
        "amount": 1000,
        "amount_unit": "USDT"
      }
    }
  ],
  "edges": [
    { "from": "trigger_1", "to": "data_1" },
    { "from": "data_1", "to": "indicator_1" },
    { "from": "indicator_1", "to": "condition_1" },
    { "from": "condition_1", "to": "action_1", "condition": "true" }
  ]
}
```

## 4. 전략 실행

### 4.1 배포
```
Client → POST /api/v1/strategies/{id}/deploy
         ↓
FastAPI → 전략 검증 (노드 순환, 타입 체크)
         → 실행 스케줄러 등록
         → PostgreSQL에 상태 저장 (DEPLOYED)
         ↓
         ← 200 OK
```

### 4.2 실행
```
Scheduler → 트리거 조건 확인 (주기적)
          → 조건 충족 시 전략 실행
          → 노드 순서대로 처리
          → 결과 PostgreSQL 저장
          → (선택) 블록체인 기록
```

## 5. 데이터 모델

### 5.1 strategies 테이블
```sql
CREATE TABLE strategies (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR(255),
  description TEXT,
  definition JSONB,  -- 노드-엣지 구조
  status VARCHAR(50), -- DRAFT, DEPLOYED, PAUSED, ARCHIVED
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

### 5.2 strategy_definition 구조
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "trigger",
      "config": {
        "trigger_type": "price_change",
        "symbol": "BTC/USDT",
        "threshold": 0.01
      }
    },
    {
      "id": "node_2",
      "type": "condition",
      "config": {
        "indicator": "RSI",
        "operator": "<",
        "value": 30
      }
    }
  ],
  "edges": [
    {
      "from": "node_1",
      "to": "node_2"
    }
  ]
}
```

## 6. 프론트엔드 구현

### 6.1 에디터 라이브러리 고려
- **React Flow**: 유연한 커스터마이징
- **React Flow + DnD**: 드래그 앤 드롭 지원
- **Rete.js**: 더 복잡한 에디터 필요 시

### 6.2 상태 관리
```typescript
interface StrategyState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  addNode: (node: Node) => void;
  removeNode: (id: string) => void;
  updateNode: (id: string, config: any) => void;
}
```

## 7. LLM 연동 상세

### 7.1 LLM 노드 타입

**LLM 노드**는 전략 내에서 자연어 처리 및 의사결정을 수행합니다.

| 노드 타입 | 설명 | 사용 예시 |
|----------|------|----------|
| **LLM 분석** | 시장 데이터를 자연어로 해석 | "현재 시장 상황 분석" |
| **LLM 감성** | 뉴스/소셜 미디어 감성 분석 | "BTC 뉴스 감성 점수" |
| **LLM 의사결정** | 복잡한 조건을 LLM이 판단 | "매수/매도/홀드 추천" |
| **LLM 요약** | 전략 실행 결과 요약 | "오늘 거래 내역 요약" |

### 7.2 LLM 활용 시나리오

**시나리오 1: 뉴스 기반 매매**
```
1. Trigger: 1시간마다 실행
2. LLM 감성: 최신 BTC 뉴스 10개 수집 → 감성 분석
3. Condition: 감성 점수 > 0.7 (긍정)
4. Action: 매수 $1000
```

**시나리오 2: 시장 해석 기반 전략**
```
1. Trigger: BTC 가격 5% 변동
2. Data Source: 최근 24시간 OHLCV
3. LLM 분석: 차트 패턴, 거래량, 시장 상황 종합 분석
4. LLM 의사결정: "매수 추천", "매도 추천", "관망" 중 선택
5. Action: LLM 추천에 따라 주문 실행
```

**시나리오 3: 포트폴리오 리밸런싱**
```
1. Trigger: 매일 오전 9시
2. Data Source: 포트폴리오 현황, 24시간 변동률
3. LLM 분석: 리스크-리워드 평가
4. LLM 의사결정: 리밸런싱 비율 계산
5. Action: 여러 거래쌍 동시 리밸런싱
```

### 7.3 프롬프트 설계 가이드라인

**전략 생성 프롬프트**:
```
당신은 암호화폐 자동매매 전략 생성 전문가입니다.

사용자 요청: {user_prompt}

다음 JSON 형식으로 전략을 생성하세요:
{
  "name": "전략 이름",
  "description": "전략 설명",
  "nodes": [...],
  "edges": [...]
}

제약 조건:
- 트리거 노드는 1개만 포함
- 데이터 소스 노드는 트리거 다음에 위치
- 최소 1개의 조건 노드 포함
- 액션 노드는 실행 경로의 마지막에 위치
```

**시장 분석 프롬프트**:
```
다음 시장 데이터를 분석하여 매매 추천을 제공하세요.

데이터:
- 심볼: {symbol}
- 현재 가격: {price}
- 24시간 변동률: {change_24h}
- 거래량: {volume}
- RSI(14): {rsi}
- MACD: {macd}

출력 형식:
{
  "analysis": "시장 상황 분석 (2-3문장)",
  "recommendation": "BUY | SELL | HOLD",
  "confidence": 0.0~1.0,
  "reason": "추천 이유"
}
```

**뉴스 감성 분석 프롬프트**:
```
다음 뉴스 기사의 감성을 분석하세요.

뉴스: {news_title}
{news_content}

출력 형식:
{
  "sentiment": "POSITIVE | NEGATIVE | NEUTRAL",
  "score": -1.0~1.0,
  "keywords": ["키워드1", "키워드2"],
  "summary": "뉴스 요약 (1문장)"
}
```

### 7.4 LLM 노드 파라미터

**LLM 분석 노드**:
```json
{
  "type": "llm_analysis",
  "config": {
    "model": "gpt-4",
    "prompt_template": "시장 데이터 분석: {data}",
    "max_tokens": 500,
    "temperature": 0.7,
    "output_format": "json"
  }
}
```

**LLM 감성 노드**:
```json
{
  "type": "llm_sentiment",
  "config": {
    "model": "gpt-4",
    "source": "news",
    "source_count": 10,
    "sentiment_threshold": 0.6,
    "cache_minutes": 15
  }
}
```

### 7.5 LLM 연동 제약 사항

| 항목 | 제약 |
|------|------|
| **최대 토큰** | 4,000 tokens (입력 + 출력) |
| **타임아웃** | 30초 |
| **재시도** | 최대 3회 (exponential backoff) |
| **캐싱** | 동일 프롬프트 15분 캐싱 |
| **비용 제한** | 사용자별 월 $10 제한 |

---

## 8. 향후 확장

### 8.1 템플릿 마켓플레이스
- 사용자가 전략을 공개/판매
- 복제 시 저작자에게 크레딧 지불

### 8.2 전략 버전 관리
- Git처럼 전략 버전 관리
- 롤백, 비교 기능

---

## 9. 관련 문서 가이드

이 문서를 읽은 후, 작업하려는 내용에 따라 다음 specs 문서를 참고하세요:

| 작업 내용 | 참조할 specs 문서 |
|-----------|------------------|
| **노드 타입 구현** | `specs/node-types.md` (각 노드별 파라미터, 검증 규칙) |
| **전략 검증 로직** | `specs/validation-rules.md` (순환 감지, 타입 체크) |
| **실행 엔진 개발** | `specs/execution-engine.md` (스케줄러, 노드 처리) |
| **LLM 노드 통합** | `specs/llm-integration.md` (OpenAI API 연동) |

### 다른 도메인과의 연계

| 연계 작업 | 참조할 도메인 |
|-----------|--------------|
| **백테스팅과 연동** | [../04-backtesting/index.md](../04-backtesting/index.md) |
| **전략 실행 내역 온체인 기록** | [../05-blockchain/index.md](../05-blockchain/index.md) |
| **strategies 테이블 수정** | [../06-data/index.md](../06-data/index.md) |

---

*최종 업데이트: 2025-12-29*
