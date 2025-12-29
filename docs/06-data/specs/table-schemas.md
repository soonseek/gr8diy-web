# 테이블 스키마 상세 (Table Schemas)

## 1. 사용자 & 크레딧

### 1.1 users

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| email | VARCHAR(255) | NOT NULL | - | UNIQUE |
| hashed_password | VARCHAR(255) | NOT NULL | - | - |
| full_name | VARCHAR(100) | NULL | - | - |
| is_active | BOOLEAN | NOT NULL | true | - |
| is_superuser | BOOLEAN | NOT NULL | false | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_users_email` ON (email)

---

### 1.2 credits

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id), UNIQUE, CASCADE |
| balance | INTEGER | NOT NULL | 0 | CHECK (balance >= 0) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_credits_user_id` ON (user_id)

---

### 1.3 credit_transactions

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id) |
| amount | INTEGER | NOT NULL | - | - |
| balance_after | INTEGER | NOT NULL | - | - |
| type | VARCHAR(50) | NOT NULL | - | CHECK (type IN ('PURCHASE', 'BACKTEST', 'EXECUTION', 'TEMPLATE_CLONE')) |
| reference_id | UUID | NULL | - | - |
| description | TEXT | NULL | - | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_credit_transactions_user_id` ON (user_id)
- `idx_credit_transactions_type` ON (type)
- `idx_credit_transactions_created_at` ON (created_at DESC)

---

## 2. 전략

### 2.1 strategies

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| name | VARCHAR(255) | NOT NULL | - | - |
| description | TEXT | NULL | - | - |
| definition | JSONB | NOT NULL | - | - |
| status | VARCHAR(20) | NOT NULL | 'DRAFT' | CHECK (status IN ('DRAFT', 'DEPLOYED', 'PAUSED', 'ARCHIVED')) |
| is_public | BOOLEAN | NOT NULL | false | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_strategies_user_id` ON (user_id)
- `idx_strategies_status` ON (status)
- `idx_strategies_is_public` ON (is_public)

---

### 2.2 backtests

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id) |
| strategy_id | UUID | NOT NULL | - | FK → strategies(id), CASCADE |
| symbol | VARCHAR(20) | NOT NULL | - | - |
| timeframe | VARCHAR(10) | NOT NULL | - | - |
| start_date | TIMESTAMPTZ | NOT NULL | - | - |
| end_date | TIMESTAMPTZ | NOT NULL | - | - |
| initial_capital | DECIMAL(20, 8) | NOT NULL | - | - |
| final_capital | DECIMAL(20, 8) | NULL | - | - |
| total_return_bp | INTEGER | NULL | - | CHECK (total_return_bp >= -10000) |
| mdd_bp | INTEGER | NULL | - | - |
| win_rate_bp | INTEGER | NULL | - | - |
| sharpe_ratio | DECIMAL(10, 4) | NULL | - | - |
| trade_count | INTEGER | NULL | - | - |
| status | VARCHAR(20) | NOT NULL | 'QUEUED' | CHECK (status IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED')) |
| error_message | TEXT | NULL | - | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| completed_at | TIMESTAMPTZ | NULL | - | - |

**인덱스**:
- `idx_backtests_user_id` ON (user_id)
- `idx_backtests_strategy_id` ON (strategy_id)
- `idx_backtests_status` ON (status)

---

### 2.3 executions

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id) |
| strategy_id | UUID | NOT NULL | - | FK → strategies(id), CASCADE |
| symbol | VARCHAR(20) | NOT NULL | - | - |
| side | VARCHAR(10) | NOT NULL | - | CHECK (side IN ('BUY', 'SELL')) |
| order_type | VARCHAR(20) | NOT NULL | - | CHECK (order_type IN ('MARKET', 'LIMIT')) |
| amount | DECIMAL(20, 8) | NOT NULL | - | - |
| price | DECIMAL(20, 8) | NULL | - | - |
| executed_price | DECIMAL(20, 8) | NULL | - | - |
| status | VARCHAR(20) | NOT NULL | 'PENDING' | CHECK (status IN ('PENDING', 'FILLED', 'FAILED', 'CANCELLED')) |
| exchange_order_id | VARCHAR(100) | NULL | - | - |
| fee | DECIMAL(20, 8) | NULL | - | - |
| error_message | TEXT | NULL | - | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| executed_at | TIMESTAMPTZ | NULL | - | - |

**인덱스**:
- `idx_executions_user_id` ON (user_id)
- `idx_executions_strategy_id` ON (strategy_id)
- `idx_executions_status` ON (status)

---

## 3. 템플릿

### 3.1 templates

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| strategy_id | UUID | NOT NULL | - | FK → strategies(id), CASCADE |
| author_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| name | VARCHAR(255) | NOT NULL | - | - |
| description | TEXT | NULL | - | - |
| price_credits | INTEGER | NOT NULL | 0 | CHECK (price_credits >= 0) |
| clone_count | INTEGER | NOT NULL | 0 | CHECK (clone_count >= 0) |
| is_active | BOOLEAN | NOT NULL | true | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_templates_author_id` ON (author_id)
- `idx_templates_is_active` ON (is_active)

---

### 3.2 template_clones

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| template_id | UUID | NOT NULL | - | FK → templates(id) |
| author_id | UUID | NOT NULL | - | FK → users(id) |
| cloner_id | UUID | NOT NULL | - | FK → users(id) |
| cloned_strategy_id | UUID | NULL | - | FK → strategies(id) |
| price_credits | INTEGER | NOT NULL | - | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_template_clones_template_id` ON (template_id)
- `idx_template_clones_author_id` ON (author_id)
- `idx_template_clones_cloner_id` ON (cloner_id)

---

## 4. 기타

### 4.1 credentials

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| type | VARCHAR(50) | NOT NULL | - | CHECK (type IN ('LLM', 'EXCHANGE')) |
| provider | VARCHAR(50) | NOT NULL | - | - |
| encrypted_api_key | TEXT | NOT NULL | - | - |
| encrypted_api_secret | TEXT | NULL | - | - |
| nickname | VARCHAR(100) | NULL | - | - |
| is_active | BOOLEAN | NOT NULL | true | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_credentials_user_id` ON (user_id)
- `idx_credentials_type` ON (type)

---

### 4.2 ohlcv_data

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | SERIAL | NOT NULL | nextval('ohlcv_data_id_seq') | PK |
| symbol | VARCHAR(20) | NOT NULL | - | - |
| timeframe | VARCHAR(10) | NOT NULL | - | - |
| timestamp | TIMESTAMPTZ | NOT NULL | - | - |
| open | DECIMAL(20, 8) | NOT NULL | - | - |
| high | DECIMAL(20, 8) | NOT NULL | - | - |
| low | DECIMAL(20, 8) | NOT NULL | - | - |
| close | DECIMAL(20, 8) | NOT NULL | - | - |
| volume | DECIMAL(30, 8) | NOT NULL | - | - |

**제약조건**:
- UNIQUE (symbol, timeframe, timestamp)

**인덱스**:
- `idx_ohlcv_symbol_time` ON (symbol, timeframe, timestamp DESC)
- `idx_ohlcv_timestamp` ON (timestamp DESC)

---

## 5. 블록체인 (Blockchain)

### 5.1 wallets

사용자의 Monad L1 월렛 주소를 관리합니다. 블록체인 비활성화 모드에서는 사용되지 않습니다.

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| address | VARCHAR(42) | NOT NULL | - | UNIQUE (0x... 형식) |
| is_verified | BOOLEAN | NOT NULL | false | 서명 검증 완료 여부 |
| verification_signature | TEXT | NULL | - | 서명 데이터 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**인덱스**:
- `idx_wallets_user_id` ON (user_id)
- `idx_wallets_address` ON (address)

---

### 5.2 follows

사용자 간 팔로우 관계를 관리합니다. 온체인 FollowRegistry와 동기화됩니다.

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| follower_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| following_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| strategy_id | UUID | NULL | - | FK → strategies(id) |
| is_active | BOOLEAN | NOT NULL | true | - |
| onchain_tx_hash | VARCHAR(66) | NULL | - | 온체인 트랜잭션 해시 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**제약조건**:
- CHECK (follower_id != following_id) - 자기 자신 팔로우 불가
- UNIQUE (follower_id, following_id, strategy_id)

**인덱스**:
- `idx_follows_follower_id` ON (follower_id)
- `idx_follows_following_id` ON (following_id)
- `idx_follows_strategy_id` ON (strategy_id)

---

### 5.3 staking_records

G8D 토큰 스테이킹 기록을 관리합니다. 온체인 G8DStaking 컨트랙트와 동기화됩니다.

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| amount | DECIMAL(30, 18) | NOT NULL | - | 스테이킹 수량 |
| tier | INTEGER | NOT NULL | 0 | T0~T5 (0~5) |
| type | VARCHAR(20) | NOT NULL | - | CHECK (type IN ('STAKE', 'UNSTAKE')) |
| onchain_tx_hash | VARCHAR(66) | NULL | - | 온체인 트랜잭션 해시 |
| status | VARCHAR(20) | NOT NULL | 'PENDING' | CHECK (status IN ('PENDING', 'CONFIRMED', 'FAILED')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| confirmed_at | TIMESTAMPTZ | NULL | - | - |

**인덱스**:
- `idx_staking_records_user_id` ON (user_id)
- `idx_staking_records_type` ON (type)
- `idx_staking_records_status` ON (status)

---

### 5.4 strategy_registrations

전략의 온체인 등록 기록을 관리합니다. StrategyRegistry 컨트랙트와 동기화됩니다.

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| strategy_id | UUID | NOT NULL | - | FK → strategies(id), CASCADE |
| author_id | UUID | NOT NULL | - | FK → users(id) |
| onchain_strategy_id | INTEGER | NULL | - | 온체인 strategy ID |
| merkle_root | VARCHAR(66) | NULL | - | DecisionHistory Merkle Root |
| onchain_tx_hash | VARCHAR(66) | NULL | - | 등록 트랜잭션 해시 |
| status | VARCHAR(20) | NOT NULL | 'PENDING' | CHECK (status IN ('PENDING', 'REGISTERED', 'FAILED')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| registered_at | TIMESTAMPTZ | NULL | - | - |

**제약조건**:
- UNIQUE (strategy_id) - 하나의 전략은 한 번만 등록

**인덱스**:
- `idx_strategy_registrations_strategy_id` ON (strategy_id)
- `idx_strategy_registrations_author_id` ON (author_id)
- `idx_strategy_registrations_status` ON (status)

---

### 5.5 settlements

오프체인 정산 내역을 관리합니다. 크레딧 기반 결제 시스템의 핵심 테이블입니다.

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| user_id | UUID | NOT NULL | - | FK → users(id) |
| strategy_id | UUID | NOT NULL | - | FK → strategies(id) |
| author_id | UUID | NOT NULL | - | FK → users(id) (저작자) |
| day_index | BIGINT | NOT NULL | - | Unix timestamp / 86400 |
| total_volume | DECIMAL(30, 8) | NOT NULL | - | 총 거래량 |
| fee_amount | DECIMAL(30, 8) | NOT NULL | - | 수수료 (USDT0 기준) |
| fee_credits | INTEGER | NOT NULL | - | 수수료 (크레딧) |
| user_tier | INTEGER | NOT NULL | 0 | T0~T5 |
| author_tier | INTEGER | NOT NULL | 0 | T0~T5 |
| discount_bps | INTEGER | NOT NULL | 0 | 할인율 (basis point) |
| author_fee_credits | INTEGER | NOT NULL | 0 | 저작자 지급액 |
| platform_fee_credits | INTEGER | NOT NULL | 0 | 플랫폼 수익 |
| status | VARCHAR(20) | NOT NULL | 'PENDING' | CHECK (status IN ('PENDING', 'PAID', 'FAILED')) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| paid_at | TIMESTAMPTZ | NULL | - | - |

**제약조건**:
- UNIQUE (user_id, strategy_id, day_index)

**인덱스**:
- `idx_settlements_user_id` ON (user_id)
- `idx_settlements_strategy_id` ON (strategy_id)
- `idx_settlements_author_id` ON (author_id)
- `idx_settlements_day_index` ON (day_index)
- `idx_settlements_status` ON (status)

---

### 5.6 author_royalties

저작자에게 월별 지급할 저작권료를 관리합니다. 관리자가 수동 정산합니다.

| 컬럼 | 타입 | NULL | 기본값 | 제약조건 |
|------|------|------|--------|----------|
| id | UUID | NOT NULL | gen_random_uuid() | PK |
| author_id | UUID | NOT NULL | - | FK → users(id), CASCADE |
| year | INTEGER | NOT NULL | - | - |
| month | INTEGER | NOT NULL | - | 1~12 |
| total_clones | INTEGER | NOT NULL | 0 | 해당 월 복제 횟수 |
| total_revenue_credits | INTEGER | NOT NULL | 0 | 총 수익 (크레딧) |
| royalty_rate_bps | INTEGER | NOT NULL | 1000 | 저작권료율 (1000 = 10%) |
| royalty_amount_credits | INTEGER | NOT NULL | 0 | 지급할 저작권료 |
| status | VARCHAR(20) | NOT NULL | 'PENDING' | CHECK (status IN ('PENDING', 'PAID', 'CANCELLED')) |
| paid_at | TIMESTAMPTZ | NULL | - | - |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | - |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | - |

**제약조건**:
- UNIQUE (author_id, year, month)

**인덱스**:
- `idx_author_royalties_author_id` ON (author_id)
- `idx_author_royalties_year_month` ON (year, month)
- `idx_author_royalties_status` ON (status)

---

## 6. 컬럼 타입 설명

### 5.1 UUID
- PostgreSQL `gen_random_uuid()` 함수로 자동 생성
- PK, FK에 사용

### 5.2 TIMESTAMPTZ
- 타임존 인식 타임스탬프
- UTC로 저장

### 5.3 JSONB
- 이진 JSON 저장
- `strategies.definition`에 노드-엣지 구조 저장

### 5.4 DECIMAL(p, s)
- 정밀도 p, 소수점 자리 s
- 금융 데이터에 적합

### 5.5 VARCHAR(n)
- 가변 길이 문자열
- 최대 n자

---

## 6. 상위/관련 문서

- **[../index.md](../index.md)** - 데이터 모델 개요
- **[erd.md](./erd.md)** - ERD 다이어그램
- **[constraints.md](./constraints.md)** - 제약조건 상세
- **[indexes.md](./indexes.md)** - 인덱스 설계 상세

---

*최종 업데이트: 2025-12-29*
