# 제약조건 (Constraints)

## 1. FOREIGN KEY 제약조건

### 1.1 FK 규칙 목록

| 자식 테이블 | 컬럼 | 부모 테이블 | onDelete | 설명 |
|-----------|------|-----------|----------|------|
| strategies | user_id | users(id) | CASCADE | 사용자 삭제 시 전략 연쇄 삭제 |
| backtests | user_id | users(id) | RESTRICT | 히스토리 보존 (삭제 불가) |
| backtests | strategy_id | strategies(id) | CASCADE | 전략 삭제 시 백테스트 연쇄 삭제 |
| executions | user_id | users(id) | RESTRICT | 히스토리 보존 (삭제 불가) |
| executions | strategy_id | strategies(id) | CASCADE | 전략 삭제 시 실행 내역 연쇄 삭제 |
| templates | strategy_id | strategies(id) | CASCADE | 전략 삭제 시 템플릿 연쇄 삭제 |
| templates | author_id | users(id) | CASCADE | 사용자 삭제 시 템플릿 연쇄 삭제 |
| credits | user_id | users(id) | CASCADE | 사용자 삭제 시 크레딧 연쇄 삭제 |
| credentials | user_id | users(id) | CASCADE | 사용자 삭제시 Credential 연쇄 삭제 |
| credit_transactions | user_id | users(id) | RESTRICT | 히스토리 보존 (삭제 불가) |
| template_clones | template_id | templates(id) | RESTRICT | 히스토리 보존 (삭제 불가) |
| template_clones | author_id | users(id) | RESTRICT | 히스토리 보존 (삭제 불가) |
| template_clones | cloner_id | users(id) | RESTRICT | 히스토리 보존 (삭제 불가) |

### 1.2 CASCADE vs RESTRICT 정책

**CASCADE** (연쇄 삭제):
- 부모 삭제 시 자식도 함께 삭제
- 적용: `strategies`, `credits`, `credentials`, `templates`
- 이유: 사용자/전략 삭제 시 연관 데이터 불필요

**RESTRICT** (삭제 제한):
- 자식이 존재하면 부모 삭제 불가
- 적용: `backtests`, `executions`, `credit_transactions`, `template_clones`
- 이유: 히스토리 보존 (백테스트 결과, 실행 내역은 중요 데이터)

---

## 2. 일반 제약조건

### 2.1 UNIQUE 제약조건

| 테이블 | 컬럼 | 설명 |
|-------|------|------|
| users | email | 이메일 중복 가입 방지 |
| credits | user_id | 한 사용자당 하나의 크레딧 계정 |
| ohlcv_data | (symbol, timeframe, timestamp) | 중복 데이터 방지 |

### 2.2 CHECK 제약조건

| 테이블 | 컬럼 | 조건 | 설명 |
|-------|------|------|------|
| credits | balance | balance >= 0 | 음수 잔액 불가 |
| backtests | total_return_bp | total_return_bp >= -10000 | -100% 이하 불가 |
| strategies | status | IN ('DRAFT', 'DEPLOYED', 'PAUSED', 'ARCHIVED') | 상태 값 제한 |
| backtests | status | IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED') | 상태 값 제한 |
| executions | status | IN ('PENDING', 'FILLED', 'FAILED', 'CANCELLED') | 상태 값 제한 |
| executions | side | IN ('BUY', 'SELL') | 매수/매도만 가능 |
| executions | order_type | IN ('MARKET', 'LIMIT') | 시장가/지정가만 가능 |
| credentials | type | IN ('LLM', 'EXCHANGE') | 타입 제한 |
| credit_transactions | type | IN ('PURCHASE', 'BACKTEST', 'EXECUTION', 'TEMPLATE_CLONE') | 거래 유형 제한 |
| templates | price_credits | price_credits >= 0 | 가격 음수 불가 |
| templates | clone_count | clone_count >= 0 | 복제 횟수 음수 불가 |

### 2.3 NOT NULL 제약조건

모든 PK, FK 컬럼은 NOT NULL입니다.

주요 NOT NULL 컬럼:
- `users.email`, `users.hashed_password`
- `strategies.name`, `strategies.definition`, `strategies.status`
- `backtests.symbol`, `backtests.start_date`, `backtests.end_date`
- `credits.balance`

---

## 3. 트리거 (Triggers)

### 3.1 updated_at 자동 업데이트

모든 테이블의 `updated_at` 컬럼은 ROW 레벨 트리거로 자동 업데이트됩니다.

**PostgreSQL 함수**:
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**트리거 예시 (users)**:
```sql
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

적용 테이블:
- users
- strategies
- templates
- credits
- credentials

---

## 4. 비즈니스 규칙 (Business Rules)

### 4.1 크레딧 잔액 검증

**규칙**: 크레딧 차감 전 잔액 확인

트랜잭션 타입별 차감:
- `BACKTEST`: 100 크레딧
- `EXECUTION`: 10 크레딧
- `TEMPLATE_CLONE`: 템플릿 price_credits

**구현 방식**: 애플리케이션 레벨 검증 (Service Layer)

### 4.2 전략 상태 천이

**허용된 상태 천이**:
```
DRAFT → DEPLOYED → PAUSED → ARCHIVED
DRAFT → ARCHIVED
DEPLOYED → ARCHIVED
```

**금지된 천이**:
- `ARCHIVED` → 다른 상태 (복구 불가)
- `PAUSED` → `DRAFT` (되돌릴 수 없음)

### 4.3 백테스트 중복 실행 방지

**규칙**: 동일 전략, 동일 파라미터로 진행 중인 백테스트가 있으면 새 요청 거부

**구현 방식**:
- 애플리케이션 레벨에서 `backtests` 테이블 조회
- `status = 'RUNNING'` 인 동일 전략 확인

### 4.4 템플릿 복제 조건

**규칙**: 템플릿 복제 시
1. 템플릿이 `is_active = true` 여야 함
2. 구매자의 크레딧 잔액이 `price_credits` 이상이어야 함
3. 구매자 != 저작자 (자신의 템플릿 구매 불가)

### 4.5 Credential 수정 제한

**규칙**:
- `encrypted_api_key`, `encrypted_api_secret`는 직접 수정 불가
- 새로운 Credential 생성 후 기존 것 비활성화 (`is_active = false`)

### 4.6 OHLCV 데이터 중복 방지

**규칙**: `(symbol, timeframe, timestamp)` 조합으로 중복 방지

**구현 방식**: UNIQUE 제약조건 + `ON CONFLICT DO NOTHING`

---

## 5. 데이터 무결성 검증

### 5.1 참조 무결성 (Referential Integrity)

- 모든 FK는 부모 테이블에 존재하는 값이어야 함
- DB 레벨 FK 제약조건으로 보장

### 5.2 도메인 무결성 (Domain Integrity)

- 컬럼 타입, CHECK 제약조건으로 보장
- 예: `side` 컬럼은 'BUY' 또는 'SELL'만 가능

### 5.3 엔티티 무결성 (Entity Integrity)

- PK는 NULL 불가, 중복 불가
- 모든 테이블의 PK는 UUID

### 5.4 사용자 정의 무결성 (Custom Integrity)

애플리케이션 레벨에서 검증:
- 크레딧 잔액 검증
- 전략 상태 천이
- 백테스트 중복 실행 방지

---

## 6. 제약조건 위원 처리

### 6.1 FK 제약조건 위원

**에러 메시지 예시**:
```
insert or update on table "backtests" violates foreign key constraint "backtests_strategy_id_fkey"
Key (strategy_id)=(uuid) is not present in table "strategies".
```

**해결**: 유효한 strategy_id 사용

### 6.2 UNIQUE 제약조건 위원

**에러 메시지 예시**:
```
duplicate key value violates unique constraint "users_email_key"
Key (email)=(test@example.com) already exists.
```

**해결**: 다른 이메일 사용

### 6.3 CHECK 제약조건 위원

**에러 메시지 예시**:
```
new row violates check constraint "credits_balance_check"
Detail: Failing row contains (uuid, -100).
```

**해결**: balance >= 0 조건 만족

---

## 7. 상위/관련 문서

- **[../index.md](../index.md)** - 데이터 모델 개요
- **[erd.md](./erd.md)** - ERD 다이어그램
- **[table-schemas.md](./table-schemas.md)** - 테이블별 상세 스키마
- **[indexes.md](./indexes.md)** - 인덱스 설계 상세

---

*최종 업데이트: 2025-12-29*
