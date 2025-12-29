# 데이터 모델 (Data Model)

## 1. 개요

gr8diy-web의 데이터베이스는 **PostgreSQL**을 사용하며, 주요 테이블은 사용자, 전략, 백테스트, 실행 내역, 크레딧으로 구성됩니다.

---

## 2. 주요 테이블

### 2.1 users (사용자)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| email | VARCHAR(255) | UK, 이메일 |
| hashed_password | VARCHAR(255) | bcrypt 해시 |
| full_name | VARCHAR(100) | 전체 이름 |
| is_active | BOOLEAN | 활성화 여부 |
| is_superuser | BOOLEAN | 관리자 여부 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**인덱스**: `idx_users_email (email)`

---

### 2.2 strategies (전략)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| name | VARCHAR(255) | 전략 이름 |
| description | TEXT | 설명 |
| definition | JSONB | 노드-엣지 구조 |
| status | VARCHAR(20) | DRAFT, DEPLOYED, PAUSED, ARCHIVED |
| is_public | BOOLEAN | 공개 여부 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**인덱스**: `idx_strategies_user_id`, `idx_strategies_status`, `idx_strategies_is_public`

---

### 2.3 backtests (백테스트)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| strategy_id | UUID | FK → strategies(id) |
| symbol | VARCHAR(20) | BTC/USDT |
| timeframe | VARCHAR(10) | 1h, 4h, 1d |
| start_date | TIMESTAMPTZ | 시작 날짜 |
| end_date | TIMESTAMPTZ | 종료 날짜 |
| initial_capital | DECIMAL(20, 8) | 초기 자본 |
| final_capital | DECIMAL(20, 8) | 최종 자본 |
| total_return_bp | INTEGER | 총 수익률 (basis point) |
| mdd_bp | INTEGER | MDD (basis point) |
| win_rate_bp | INTEGER | 승률 (basis point) |
| sharpe_ratio | DECIMAL(10, 4) | 샤프 비율 |
| trade_count | INTEGER | 거래 횟수 |
| status | VARCHAR(20) | QUEUED, RUNNING, COMPLETED, FAILED |
| error_message | TEXT | 에러 메시지 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| completed_at | TIMESTAMPTZ | 완료 일시 |

**인덱스**: `idx_backtests_user_id`, `idx_backtests_strategy_id`, `idx_backtests_status`

---

### 2.4 executions (전략 실행)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| strategy_id | UUID | FK → strategies(id) |
| symbol | VARCHAR(20) | BTC/USDT |
| side | VARCHAR(10) | BUY, SELL |
| order_type | VARCHAR(20) | MARKET, LIMIT |
| amount | DECIMAL(20, 8) | 수량 |
| price | DECIMAL(20, 8) | 지정 가격 |
| executed_price | DECIMAL(20, 8) | 체결 가격 |
| status | VARCHAR(20) | PENDING, FILLED, FAILED, CANCELLED |
| exchange_order_id | VARCHAR(100) | 거래소 주문 ID |
| fee | DECIMAL(20, 8) | 수수료 |
| error_message | TEXT | 에러 메시지 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| executed_at | TIMESTAMPTZ | 체결 일시 |

**인덱스**: `idx_executions_user_id`, `idx_executions_strategy_id`, `idx_executions_status`

---

### 2.5 templates (템플릿)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| strategy_id | UUID | FK → strategies(id), CASCADE |
| author_id | UUID | FK → users(id) |
| name | VARCHAR(255) | 템플릿 이름 |
| description | TEXT | 설명 |
| price_credits | INTEGER | 가격 (크레딧) |
| clone_count | INTEGER | 복제 횟수 |
| is_active | BOOLEAN | 활성화 여부 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**인덱스**: `idx_templates_author_id`, `idx_templates_is_active`

---

### 2.6 template_clones (템플릿 복제 이력)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| template_id | UUID | FK → templates(id) |
| author_id | UUID | FK → users(id) (저작자) |
| cloner_id | UUID | FK → users(id) (구매자) |
| cloned_strategy_id | UUID | FK → strategies(id) |
| price_credits | INTEGER | 구매 가격 |
| created_at | TIMESTAMPTZ | 생성 일시 |

**인덱스**: `idx_template_clones_template_id`, `idx_template_clones_author_id`, `idx_template_clones_cloner_id`

---

### 2.7 credits (크레딧 잔액)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id), UK, CASCADE |
| balance | INTEGER | 잔액 (음수 불가) |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**인덱스**: `idx_credits_user_id`

---

### 2.8 credit_transactions (크레딧 거래 내역)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| amount | INTEGER | 양수: 충전, 음수: 차감 |
| balance_after | INTEGER | 거래 후 잔액 |
| type | VARCHAR(50) | PURCHASE, BACKTEST, EXECUTION, TEMPLATE_CLONE |
| reference_id | UUID | 관련 테이블 ID |
| description | TEXT | 설명 |
| created_at | TIMESTAMPTZ | 생성 일시 |

**인덱스**: `idx_credit_transactions_user_id`, `idx_credit_transactions_type`, `idx_credit_transactions_created_at`

---

### 2.9 credentials (API 키)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id), CASCADE |
| type | VARCHAR(50) | LLM, EXCHANGE |
| provider | VARCHAR(50) | OPENAI, BINANCE, UPBIT |
| encrypted_api_key | TEXT | AES-256 암호화 |
| encrypted_api_secret | TEXT | AES-256 암호화 |
| nickname | VARCHAR(100) | 별칭 |
| is_active | BOOLEAN | 활성화 여부 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**인덱스**: `idx_credentials_user_id`, `idx_credentials_type`

---

### 2.10 ohlcv_data (시장 데이터)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | PK |
| symbol | VARCHAR(20) | BTC/USDT |
| timeframe | VARCHAR(10) | 1h, 4h, 1d |
| timestamp | TIMESTAMPTZ | 시간 |
| open | DECIMAL(20, 8) | 시가 |
| high | DECIMAL(20, 8) | 고가 |
| low | DECIMAL(20, 8) | 저가 |
| close | DECIMAL(20, 8) | 종가 |
| volume | DECIMAL(30, 8) | 거래량 |

**인덱스**: `idx_ohlcv_symbol_time (symbol, timeframe, timestamp DESC)`, `idx_ohlcv_timestamp`

---

### 2.11 wallets (월렛)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id), CASCADE |
| address | VARCHAR(42) | Monad L1 월렛 주소 (0x...) |
| is_verified | BOOLEAN | 서명 검증 완료 여부 |
| verification_signature | TEXT | 서명 데이터 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**인덱스**: `idx_wallets_user_id`, `idx_wallets_address`

---

### 2.12 follows (팔로우)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| follower_id | UUID | FK → users(id), CASCADE (팔로워) |
| following_id | UUID | FK → users(id), CASCADE (팔로잉) |
| strategy_id | UUID | FK → strategies(id) |
| is_active | BOOLEAN | 활성화 여부 |
| onchain_tx_hash | VARCHAR(66) | 온체인 트랜잭션 해시 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**제약조건**: `CHECK (follower_id != following_id)`, `UNIQUE (follower_id, following_id, strategy_id)`

**인덱스**: `idx_follows_follower_id`, `idx_follows_following_id`, `idx_follows_strategy_id`

---

### 2.13 staking_records (스테이킹)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id), CASCADE |
| amount | DECIMAL(30, 18) | 스테이킹 수량 |
| tier | INTEGER | T0~T5 (0~5) |
| type | VARCHAR(20) | STAKE, UNSTAKE |
| onchain_tx_hash | VARCHAR(66) | 온체인 트랜잭션 해시 |
| status | VARCHAR(20) | PENDING, CONFIRMED, FAILED |
| created_at | TIMESTAMPTZ | 생성 일시 |
| confirmed_at | TIMESTAMPTZ | 확인 일시 |

**인덱스**: `idx_staking_records_user_id`, `idx_staking_records_type`, `idx_staking_records_status`

---

### 2.14 strategy_registrations (전략 등록)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| strategy_id | UUID | FK → strategies(id), CASCADE, UNIQUE |
| author_id | UUID | FK → users(id) |
| onchain_strategy_id | INTEGER | 온체인 strategy ID |
| merkle_root | VARCHAR(66) | DecisionHistory Merkle Root |
| onchain_tx_hash | VARCHAR(66) | 등록 트랜잭션 해시 |
| status | VARCHAR(20) | PENDING, REGISTERED, FAILED |
| created_at | TIMESTAMPTZ | 생성 일시 |
| registered_at | TIMESTAMPTZ | 등록 일시 |

**인덱스**: `idx_strategy_registrations_strategy_id`, `idx_strategy_registrations_author_id`, `idx_strategy_registrations_status`

---

### 2.15 settlements (정산)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK → users(id) |
| strategy_id | UUID | FK → strategies(id) |
| author_id | UUID | FK → users(id) (저작자) |
| day_index | BIGINT | Unix timestamp / 86400 |
| total_volume | DECIMAL(30, 8) | 총 거래량 |
| fee_amount | DECIMAL(30, 8) | 수수료 (USDT0) |
| fee_credits | INTEGER | 수수료 (크레딧) |
| user_tier | INTEGER | T0~T5 |
| author_tier | INTEGER | T0~T5 |
| discount_bps | INTEGER | 할인율 (basis point) |
| author_fee_credits | INTEGER | 저작자 지급액 |
| platform_fee_credits | INTEGER | 플랫폼 수익 |
| status | VARCHAR(20) | PENDING, PAID, FAILED |
| created_at | TIMESTAMPTZ | 생성 일시 |
| paid_at | TIMESTAMPTZ | 지급 일시 |

**제약조건**: `UNIQUE (user_id, strategy_id, day_index)`

**인덱스**: `idx_settlements_user_id`, `idx_settlements_strategy_id`, `idx_settlements_author_id`, `idx_settlements_day_index`, `idx_settlements_status`

---

### 2.16 author_royalties (저작권료)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| author_id | UUID | FK → users(id), CASCADE |
| year | INTEGER | 년도 |
| month | INTEGER | 월 (1~12) |
| total_clones | INTEGER | 해당 월 복제 횟수 |
| total_revenue_credits | INTEGER | 총 수익 (크레딧) |
| royalty_rate_bps | INTEGER | 저작권료율 (1000 = 10%) |
| royalty_amount_credits | INTEGER | 지급할 저작권료 |
| status | VARCHAR(20) | PENDING, PAID, CANCELLED |
| paid_at | TIMESTAMPTZ | 지급 일시 |
| created_at | TIMESTAMPTZ | 생성 일시 |
| updated_at | TIMESTAMPTZ | 수정 일시 |

**제약조건**: `UNIQUE (author_id, year, month)`

**인덱스**: `idx_author_royalties_author_id`, `idx_author_royalties_year_month`, `idx_author_royalties_status`

---

## 3. 관계 정의

### 3.1 1:N 관계

| 부모 | 자식 | 관계 |
|------|------|------|
| users | strategies | 한 사용자는 여러 전략 보유 |
| users | backtests | 한 사용자는 여러 백테스트 실행 |
| users | executions | 한 사용자는 여러 실행 |
| users | credits | 한 사용자는 하나의 크레딧 계정 |
| users | credentials | 한 사용자는 여러 API 키 |
| users | templates | 한 사용자는 여러 템플릿 공개 |
| strategies | backtests | 한 전략은 여러 백테스트 가능 |
| strategies | executions | 한 전략은 여러 실행 가능 |
| templates | template_clones | 한 템플릿은 여러 복제 가능 |
| credits | credit_transactions | 한 계정은 여러 거래 내역 |
| users | wallets | 한 사용자는 하나의 월렛 보유 |
| users | follows (follower_id) | 한 사용자는 여러 팔로우 가능 |
| users | follows (following_id) | 한 사용자는 여러 팔로잉 가능 |
| users | staking_records | 한 사용자는 여러 스테이킹 기록 |
| strategies | strategy_registrations | 한 전략은 한 번 등록 |
| strategies | settlements | 한 전략은 여러 정산 가능 |
| users | settlements (author_id) | 한 저작자는 여러 정산 수령 |
| users | author_royalties | 한 저작자는 여러 저작권료 정산 |

### 3.2 1:1 관계

| 테이블 A | 테이블 B | 관계 |
|----------|----------|------|
| users | credits | 한 사용자 = 하나의 크레딧 계정 |
| strategies | templates | 한 전략 = 하나의 템플릿 (공개 시) |
| users | wallets | 한 사용자 = 하나의 월렛 |

---

## 4. 제약조건

### 4.1 FOREIGN KEY 제약조건

| 테이블 | 컬럼 | 참조 테이블 | onDelete |
|--------|------|-----------|----------|
| strategies | user_id | users(id) | CASCADE |
| backtests | user_id | users(id) | RESTRICT |
| backtests | strategy_id | strategies(id) | CASCADE |
| executions | user_id | users(id) | RESTRICT |
| executions | strategy_id | strategies(id) | CASCADE |
| templates | strategy_id | strategies(id) | CASCADE |
| templates | author_id | users(id) | CASCADE |
| credits | user_id | users(id) | CASCADE |
| credentials | user_id | users(id) | CASCADE |
| wallets | user_id | users(id) | CASCADE |
| follows | follower_id | users(id) | CASCADE |
| follows | following_id | users(id) | CASCADE |
| follows | strategy_id | strategies(id) | CASCADE |
| staking_records | user_id | users(id) | CASCADE |
| strategy_registrations | strategy_id | strategies(id) | CASCADE |
| strategy_registrations | author_id | users(id) | CASCADE |
| settlements | user_id | users(id) | CASCADE |
| settlements | strategy_id | strategies(id) | CASCADE |
| settlements | author_id | users(id) | CASCADE |
| author_royalties | author_id | users(id) | CASCADE |

**참고**: 백테스트, 실행 내역은 `RESTRICT`로 히스토리 보존

### 4.2 UNIQUE 제약조건

| 테이블 | 컬럼 |
|-------|------|
| users | email |
| credits | user_id |
| wallets | address |
| ohlcv_data | (symbol, timeframe, timestamp) |
| follows | (follower_id, following_id, strategy_id) |
| strategy_registrations | strategy_id |
| settlements | (user_id, strategy_id, day_index) |
| author_royalties | (author_id, year, month) |

### 4.3 CHECK 제약조건

| 테이블 | 조건 |
|-------|------|
| credits | balance >= 0 (음수 불가) |
| backtests | total_return_bp >= -10000 (-100% 이하) |
| executions | side IN ('BUY', 'SELL') |
| follows | follower_id != following_id (자기 팔로우 불가) |
| staking_records | type IN ('STAKE', 'UNSTAKE') |
| staking_records | tier BETWEEN 0 AND 5 |
| strategy_registrations | status IN ('PENDING', 'REGISTERED', 'FAILED') |
| settlements | user_tier BETWEEN 0 AND 5 |
| settlements | author_tier BETWEEN 0 AND 5 |
| settlements | status IN ('PENDING', 'PAID', 'FAILED') |
| author_royalties | month BETWEEN 1 AND 12 |
| author_royalties | status IN ('PENDING', 'PAID', 'CANCELLED') |

---

## 5. 인덱싱 전략

### 5.1 검색 최적화

- **user_id**: 모든 테이블 (사용자별 데이터 조회)
- **status**: backtests, executions (진행 상태 필터링)
- **is_public**: strategies (공개 템플릿 탐색)
- **type**: credentials, credit_transactions (타입 필터링)

### 5.2 시계열 데이터

- **timestamp DESC**: ohlcv_data, credit_transactions (최신순 조회)
- **created_at DESC**: 대부분의 테이블

### 5.3 복합 인덱스

- **ohlcv_data**: (symbol, timeframe, timestamp DESC)
- **credit_transactions**: (user_id, created_at DESC)

---

## 6. 데이터 보안

### 6.1 암호화

| 컬럼 | 방식 |
|------|------|
| users.hashed_password | bcrypt (cost=12) |
| credentials.encrypted_api_key | AES-256 |
| credentials.encrypted_api_secret | AES-256 |

### 6.2 접근 제어

- 사용자는 자신의 데이터만 접근 가능
- is_public=True인 strategies만 타인 접근 허용

---

## 7. 관련 문서 가이드

이 문서를 읽은 후, 작업하려는 내용에 따라 다음 specs 문서를 참고하세요:

| 작업 내용 | 참조할 specs 문서 |
|-----------|------------------|
| **ERD 다이어그램 확인** | `specs/erd.md` |
| **테이블별 상세 스키마** | `specs/table-schemas.md` |
| **제약조건 상세** | `specs/constraints.md` |
| **인덱스 설계** | `specs/indexes.md` |
| **마이그레이션 작성** | `specs/migrations.md` |

### 다른 도메인과의 연계

| 연계 작업 | 참조할 도메인 |
|-----------|--------------|
| **인증 구현** | [../02-authentication/index.md](../02-authentication/index.md) |
| **전략 저장** | [../03-strategy/index.md](../03-strategy/index.md) |
| **백테스트 결과 저장** | [../04-backtesting/index.md](../04-backtesting/index.md) |

---

*최종 업데이트: 2025-12-29*
