# ERD (Entity Relationship Diagram)

## 1. 전체 ERD

```mermaid
erDiagram
    %% 사용자
    users ||--o{ strategies : "owns (1:N)"
    users ||--o{ backtests : "executes (1:N)"
    users ||--o{ executions : "executes (1:N)"
    users ||--|| credits : "has (1:1)"
    users ||--o{ credentials : "registers (1:N)"
    users ||--o{ templates : "creates (1:N)"
    users ||--o{ template_clones : "purchases as cloner (1:N)"
    users ||--o{ template_clones : "sells as author (1:N)"
    users ||--o{ credit_transactions : "has (1:N)"

    %% 전략
    strategies ||--o{ backtests : "tested in (1:N)"
    strategies ||--o{ executions : "executed in (1:N)"
    strategies ||--|| templates : "published as (1:1)"

    %% 템플릿
    templates ||--o{ template_clones : "cloned (1:N)"

    %% 크레딧
    credits ||--o{ credit_transactions : "recorded in (1:N)"

    %% 엔티티 정의
    users {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_superuser
        timestamptz created_at
        timestamptz updated_at
    }

    strategies {
        uuid id PK
        uuid user_id FK
        string name
        text description
        jsonb definition
        string status
        boolean is_public
        timestamptz created_at
        timestamptz updated_at
    }

    backtests {
        uuid id PK
        uuid user_id FK
        uuid strategy_id FK
        string symbol
        string timeframe
        timestamptz start_date
        timestamptz end_date
        decimal initial_capital
        decimal final_capital
        integer total_return_bp
        integer mdd_bp
        integer win_rate_bp
        decimal sharpe_ratio
        integer trade_count
        string status
        text error_message
        timestamptz created_at
        timestamptz completed_at
    }

    executions {
        uuid id PK
        uuid user_id FK
        uuid strategy_id FK
        string symbol
        string side
        string order_type
        decimal amount
        decimal price
        decimal executed_price
        string status
        string exchange_order_id
        decimal fee
        text error_message
        timestamptz created_at
        timestamptz executed_at
    }

    templates {
        uuid id PK
        uuid strategy_id FK
        uuid author_id FK
        string name
        text description
        integer price_credits
        integer clone_count
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    template_clones {
        uuid id PK
        uuid template_id FK
        uuid author_id FK
        uuid cloner_id FK
        uuid cloned_strategy_id FK
        integer price_credits
        timestamptz created_at
    }

    credits {
        uuid id PK
        uuid user_id UK,FK
        integer balance
        timestamptz created_at
        timestamptz updated_at
    }

    credit_transactions {
        uuid id PK
        uuid user_id FK
        integer amount
        integer balance_after
        string type
        uuid reference_id
        text description
        timestamptz created_at
    }

    credentials {
        uuid id PK
        uuid user_id FK
        string type
        string provider
        text encrypted_api_key
        text encrypted_api_secret
        string nickname
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    ohlcv_data {
        serial id PK
        string symbol
        string timeframe
        timestamptz timestamp
        decimal open
        decimal high
        decimal low
        decimal close
        decimal volume
    }
```

---

## 2. 관계 상세 설명

### 2.1 users (중심 테이블)

| 관계 | 카디널리티 | 설명 |
|------|-----------|------|
| users → strategies | 1:N | 한 사용자는 여러 전략을 보유할 수 있음 |
| users → backtests | 1:N | 한 사용자는 여러 백테스트를 실행할 수 있음 |
| users → executions | 1:N | 한 사용자는 여러 실행을 가질 수 있음 |
| users → credits | 1:1 | 한 사용자는 하나의 크레딧 계정을 가짐 |
| users → credentials | 1:N | 한 사용자는 여러 API 키를 등록할 수 있음 |
| users → templates | 1:N | 한 사용자는 여러 템플릿을 공개할 수 있음 |
| users → credit_transactions | 1:N | 한 사용자는 여러 크레딧 거래 내역을 가짐 |

### 2.2 strategies (전략)

| 관계 | 카디널리티 | 설명 |
|------|-----------|------|
| strategies → backtests | 1:N | 한 전략은 여러 백테스트를 가질 수 있음 |
| strategies → executions | 1:N | 한 전략은 여러 실행을 가질 수 있음 |
| strategies → templates | 1:1 | 한 전략은 하나의 템플릿으로 공개될 수 있음 |

### 2.3 templates (템플릿)

| 관계 | 카디널리티 | 설명 |
|------|-----------|------|
| templates → template_clones | 1:N | 한 템플릿은 여러 번 복제될 수 있음 |

### 2.4 credits (크레딧)

| 관계 | 카디널리티 | 설명 |
|------|-----------|------|
| credits → credit_transactions | 1:N | 한 크레딧 계정은 여러 거래 내역을 가짐 |

---

## 3. CASCADE 삭제 규칙

| 부모 테이블 | 자식 테이블 | 삭제 동작 |
|-----------|-----------|---------|
| users | strategies | CASCADE |
| users | credits | CASCADE |
| users | credentials | CASCADE |
| users | templates | CASCADE |
| strategies | templates | CASCADE |
| strategies | backtests | CASCADE |
| strategies | executions | CASCADE |

**참고**: backtests, executions, credit_transactions, template_clones은 `ON DELETE RESTRICT` 또는 `ON DELETE SET NULL`로 설계하여 **히스토리 보존** (삭제된 사용자/전략의 데이터라도 백테스트 결과는 유지)

---

## 4. UNIQUE 제약조건

| 테이블 | 컬럼 | 설명 |
|-------|------|------|
| users | email | 이메일 중복 가입 방지 |
| credits | user_id | 한 사용자당 하나의 크레딧 계정 |
| ohlcv_data | (symbol, timeframe, timestamp) | 중복 데이터 방지 |

---

## 5. 인덱스 요약

| 테이블 | 인덱스 | 용도 |
|-------|-------|------|
| users | email | 로그인 조회 |
| strategies | user_id, status, is_public | 사용자 전략 조회, 필터링 |
| backtests | user_id, strategy_id, status | 조회, 필터링 |
| executions | user_id, strategy_id, status | 조회, 필터링 |
| templates | author_id, is_active | 공개 템플릿 조회 |
| template_clones | template_id, author_id, cloner_id | 조회, 통계 |
| credits | user_id | 크레딧 잔액 조회 |
| credit_transactions | user_id, type, created_at | 거래 내역 조회 |
| credentials | user_id, type | API 키 조회 |
| ohlcv_data | (symbol, timeframe, timestamp), timestamp | 시계열 데이터 조회 |

---

## 6. 상위/관련 문서

- **[../index.md](../index.md)** - 데이터 모델 개요
- **[table-schemas.md](./table-schemas.md)** - 테이블별 상세 스키마
- **[constraints.md](./constraints.md)** - 제약조건 상세
- **[indexes.md](./indexes.md)** - 인덱스 설계 상세

---

*최종 업데이트: 2025-12-29*
