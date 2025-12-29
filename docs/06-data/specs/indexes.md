# 인덱스 설계 (Indexes)

## 1. 인덱스 목록

### 1.1 users

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_users_email | email | B-tree | 로그인 시 이메일 조회 |

### 1.2 strategies

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_strategies_user_id | user_id | B-tree | 사용자별 전략 조회 |
| idx_strategies_status | status | B-tree | 상태별 필터링 |
| idx_strategies_is_public | is_public | B-tree | 공개 템플릿 탐색 |

### 1.3 backtests

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_backtests_user_id | user_id | B-tree | 사용자별 백테스트 조회 |
| idx_backtests_strategy_id | strategy_id | B-tree | 전략별 백테스트 조회 |
| idx_backtests_status | status | B-tree | 진행 상태 필터링 |

### 1.4 executions

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_executions_user_id | user_id | B-tree | 사용자별 실행 조회 |
| idx_executions_strategy_id | strategy_id | B-tree | 전략별 실행 조회 |
| idx_executions_status | status | B-tree | 진행 상태 필터링 |

### 1.5 templates

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_templates_author_id | author_id | B-tree | 저작자별 템플릿 조회 |
| idx_templates_is_active | is_active | B-tree | 활성화 템플릿 필터링 |

### 1.6 template_clones

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_template_clones_template_id | template_id | B-tree | 템플릿별 복제 횟수 |
| idx_template_clones_author_id | author_id | B-tree | 저작자별 수익 |
| idx_template_clones_cloner_id | cloner_id | B-tree | 구매자별 구매 내역 |

### 1.7 credits

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_credits_user_id | user_id | B-tree | 크레딧 잔액 조회 |

### 1.8 credit_transactions

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_credit_transactions_user_id | user_id | B-tree | 사용자별 거래 내역 |
| idx_credit_transactions_type | type | B-tree | 거래 유형별 조회 |
| idx_credit_transactions_created_at | created_at DESC | B-tree | 최신순 조회 |

### 1.9 credentials

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_credentials_user_id | user_id | B-tree | 사용자별 Credential 조회 |
| idx_credentials_type | type | B-tree | 타입별 필터링 |

### 1.10 ohlcv_data

| 인덱스명 | 컬럼 | 타입 | 설명 |
|---------|------|------|------|
| idx_ohlcv_symbol_time | (symbol, timeframe, timestamp DESC) | B-tree | 특정 코인/타임프레임 조회 |
| idx_ohlcv_timestamp | timestamp DESC | B-tree | 전체 최신 데이터 조회 |

---

## 2. 전략별 인덱스

### 2.1 사용자별 데이터 조회 (user_id)

**목적**: "내 전략", "내 백테스트" 등 마이페이지 조회

**적용 테이블**:
- strategies (idx_strategies_user_id)
- backtests (idx_backtests_user_id)
- executions (idx_executions_user_id)
- credits (idx_credits_user_id)
- credentials (idx_credentials_user_id)
- templates (idx_templates_author_id)

**쿼리 예시**:
```sql
SELECT * FROM strategies WHERE user_id = $1;
```

### 2.2 상태별 필터링 (status)

**목적**: "진행 중인 백테스트", "배포된 전략" 등 상태 필터

**적용 테이블**:
- strategies (idx_strategies_status)
- backtests (idx_backtests_status)
- executions (idx_executions_status)

**쿼리 예시**:
```sql
SELECT * FROM backtests WHERE status = 'RUNNING';
```

### 2.3 시계열 데이터 (timestamp, created_at)

**목적**: 최신순 정렬, 날짜 범위 조회

**적용 테이블**:
- credit_transactions (created_at DESC)
- ohlcv_data (timestamp DESC)

**쿼리 예시**:
```sql
SELECT * FROM credit_transactions
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

---

## 3. 고급 최적화

### 3.1 복합 인덱스 (Composite Index)

**idx_ohlcv_symbol_time**:
```sql
CREATE INDEX idx_ohlcv_symbol_time
ON ohlcv_data (symbol, timeframe, timestamp DESC);
```

**효율성**:
- WHERE symbol = 'BTC/USDT' AND timeframe = '1h'
- ORDER BY timestamp DESC
- 두 조건을 모두 만족

**쿼리 예시**:
```sql
SELECT * FROM ohlcv_data
WHERE symbol = 'BTC/USDT' AND timeframe = '1h'
ORDER BY timestamp DESC
LIMIT 100;
```

### 3.2 부분 인덱스 (Partial Index)

**목적**: 활성화된 템플릿만 조회

**제안 인덱스**:
```sql
CREATE INDEX idx_templates_active
ON templates (author_id, price_credits)
WHERE is_active = true;
```

**장점**:
- 인덱스 크기 감소
- 비활성 템플릿 제외

### 3.3 covering 인덱스

**목적**: 테이블 접근 없이 인덱스만으로 조회

**제안 인덱스**:
```sql
CREATE INDEX idx_strategies_list
ON strategies (user_id, status, name, created_at);
```

**쿼리 예시**:
```sql
-- 테이블 접근 없이 인덱스만으로 조회 가능
SELECT status, name, created_at
FROM strategies
WHERE user_id = $1;
```

### 3.4 시계열 데이터 최적화

**문제**: ohlcv_data 테이블이 커질 수록 조회 느려짐

**해결 1: 파티셔닝 (Partitioning)**:
```sql
-- symbol별 파티션
CREATE TABLE ohlcv_data (
    -- 컬럼 정의
) PARTITION BY LIST (symbol);

-- 각 파티션 생성
CREATE TABLE ohlcv_data_btc PARTITION OF ohlcv_data
    FOR VALUES IN ('BTC/USDT');
```

**해결 2: Brin 인덱스 (대용량 시계열)**:
```sql
CREATE INDEX idx_ohlcv_timestamp_brin
ON ohlcv_data USING BRIN (timestamp);
```

---

## 4. 쿼리 최적화

### 4.1 EXPLAIN ANALYZE

**사용법**:
```sql
EXPLAIN ANALYZE
SELECT * FROM strategies
WHERE user_id = $1 AND status = 'DEPLOYED';
```

**출력 해석**:
- `Index Scan`: 인덱스 사용 (좋음)
- `Seq Scan`: 전체 테이블 스캔 (나쁨)
- `cost`: 비용 (낮을수록 좋음)
- `actual time`: 실제 실행 시간

### 4.2 느린 쿼리 진단

**단계 1**: EXPLAIN ANALYZE로 실행 계획 확인
**단계 2**: Seq Scan이 있으면 인덱스 추가 검토
**단계 3**: 복합 인덱스로 커버링 가능성 확인
**단계 4**: VACUUM ANALYZE로 통계 정보 업데이트

### 4.3 인덱스 사용 여부 확인

```sql
-- 인덱스 사용 횟수 확인
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'strategies';
```

### 4.4 미사용 인덱스 제거

```sql
-- 사용하지 않는 인덱스 확인
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE '%_pkey';
```

---

## 5. 인덱스 관리

### 5.1 인덱스 생성

```sql
CREATE INDEX idx_strategies_user_id
ON strategies (user_id);
```

### 5.2 인덱스 삭제

```sql
DROP INDEX idx_strategies_user_id;
```

### 5.3 인덱스 재구성 (REINDEX)

```sql
-- 특정 인덱스 재구성
REINDEX INDEX idx_strategies_user_id;

-- 테이블 전체 인덱스 재구성
REINDEX TABLE strategies;
```

### 5.4 동시 인덱스 생성 (CONCURRENTLY)

```sql
-- 테이블 잠금 없이 인덱스 생성 (프로덕션 권장)
CREATE INDEX CONCURRENTLY idx_strategies_status
ON strategies (status);
```

---

## 6. 모범 사례

### 6.1 인덱스를 사용해야 할 때

- 자주 조회하는 컬럼 (WHERE, JOIN, ORDER BY)
- 카디널리티가 높은 컬럼 (중복값이 적은)
- 복합 컬럼 조회 (WHERE a = x AND b = y)

### 6.2 인덱스를 사용하지 말아야 할 때

- 자주 변경되는 테이블 (INSERT/DELETE 많음)
- 카디널리티가 낮은 컬럼 (예: boolean, status)
- 작은 테이블 (전체 스캔이 빠른 경우)

### 6.3 인덱스 주의사항

- **너무 많은 인덱스**: INSERT/DELETE 느려짐
- **너무 적은 인덱스**: SELECT 느려짐
- **균형**: 읽기/쓰기 비율 고려 (본 프로젝트는 읽기가 많으므로 인덱스 적극 활용)

---

## 7. 상위/관련 문서

- **[../index.md](../index.md)** - 데이터 모델 개요
- **[erd.md](./erd.md)** - ERD 다이어그램
- **[table-schemas.md](./table-schemas.md)** - 테이블별 상세 스키마
- **[constraints.md](./constraints.md)** - 제약조건 상세

---

*최종 업데이트: 2025-12-29*
