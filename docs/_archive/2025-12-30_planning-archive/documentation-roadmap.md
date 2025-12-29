# 문서화 로드맵 (Documentation Roadmap)

## 개요

gr8diy-web 프로젝트의 전체 문서화 작업 순서와 진척도를 관리하는 문서입니다.

## 작업 방식

**옵션 A: 순차적 완성**
- 한 도메인을 완전히 작성하고 다음 도메인으로 넘어감
- 문서 간 일관성 유지 용이

## 수정 정책

**유연한 반복 접근 (Flexible Iterative Approach)**
- PRD와 실제 비전이 다를 경우 → 즉시 수정 또는 changelog.md에 기록
- 상위 문서 수정 시 연계 문서 재검토
- 모든 문서는 최종 구현 전까지 자유로운 수정 허용

---

## Phase 1: 기반 설계 (Foundation)

### 1️⃣ PRD.md 확정 (L0)

**상태**: ✅ 완료
**우선순위**: 1
**의존**: 없음

**작업 내용**:
- [x] 제품 비전 명확화
- [x] 핵심 기능 정의
- [x] 사용자 플로우 작성
- [x] 기술 아키텍처 개요
- [x] API 설계 섹션 (초안)
- [x] 보안 요구사항 섹션 (초안)

**산출물**: `PRD.md` (최종본은 Phase 4에서 완성)

---

### 2️⃣ 01-overview (시스템 개요)

**상태**: ✅ 완료
**우선순위**: 2
**의존**: PRD.md (초안)

**작업 내용**:
- [ ] `index.md` 작성
  - [ ] 전체 아키텍처 다이어그램
  - [ ] 계층 구조 설명
  - [ ] 모듈 구성
  - [ ] 데이터 플로우
  - [ ] 기술 스택 선정 이유
  - [ ] 관련 문서 가이드

**산출물**:
- `docs/01-overview/index.md`

---

### 3️⃣ 06-data (데이터 모델)

**상태**: ✅ 완료
**우선순위**: 3
**의존**: 01-overview

**작업 내용**:
- [ ] `index.md` 작성
  - [ ] ERD 개요 (텍스트)
  - [ ] 주요 테이블 목록
  - [ ] 관계 정의
  - [ ] 인덱싱 전략 개요
  - [ ] 데이터 보안 개요
  - [ ] 관련 문서 가이드

- [ ] `specs/erd.md` 작성
  - [ ] Mermaid ERD 다이어그램
  - [ ] 테이블 관계 시각화

- [ ] `specs/table-schemas.md` 작성
  - [ ] users 테이블 상세
  - [ ] strategies 테이블 상세
  - [ ] backtests 테이블 상세
  - [ ] executions 테이블 상세
  - [ ] templates 테이블 상세
  - [ ] template_clones 테이블 상세
  - [ ] credits 테이블 상세
  - [ ] credit_transactions 테이블 상세
  - [ ] credentials 테이블 상세
  - [ ] ohlcv_data 테이블 상세

- [ ] `specs/constraints.md` 작성
  - [ ] FOREIGN KEY 제약조건
  - [ ] CASCADE 삭제 규칙
  - [ ] UNIQUE 제약조건
  - [ ] CHECK 제약조건
  - [ ] 트리거 정의

- [ ] `specs/indexes.md` 작성
  - [ ] 검색 최적화 인덱스
  - [ ] 시계열 데이터 인덱스
  - [ ] 복합 인덱스 전략
  - [ ] 쿼리 최적화 가이드

- [ ] `specs/migrations.md` 작성
  - [ ] Alembic 설정 가이드
  - [ ] 마이그레이션 작성 방법
  - [ ] 버전 관리 전략
  - [ ] Rollback 절차

**산출물**:
- `docs/06-data/index.md`
- `docs/06-data/specs/erd.md`
- `docs/06-data/specs/table-schemas.md`
- `docs/06-data/specs/constraints.md`
- `docs/06-data/specs/indexes.md`
- `docs/06-data/specs/migrations.md`

---

## Phase 2: 핵심 기능 설계 (Core Features)

### 4️⃣ 02-authentication (인증)

**상태**: ✅ 완료
**우선순위**: 4
**의존**: 06-data

**작업 내용**:
- [x] `index.md` 작성
  - [x] 인증 시스템 개요
  - [x] JWT 방식 설명
  - [x] 회원가입/로그인 플로우
  - [x] 토큰 갱신/로그아웃 플로우
  - [x] 보안 전략
  - [x] Redis 데이터 구조
  - [x] 관련 문서 가이드

- [x] `specs/api-endpoints.md` 작성
  - [x] POST /api/v1/auth/register
    - [x] Request 스펙
    - [x] Response 스펙
    - [x] Error Codes
  - [x] POST /api/v1/auth/login
  - [x] POST /api/v1/auth/refresh
  - [x] POST /api/v1/auth/logout
  - [x] GET /api/v1/users/me
  - [x] GET /api/v1/users/

- [x] `specs/token-management.md` 작성
  - [x] Access Token 생성
  - [x] Refresh Token 생성
  - [x] Token Rotation 전략
  - [x] Token 폐기 절차
  - [x] 만료 정책

- [x] `specs/encryption.md` 작성
  - [x] 비밀번호 해싱 (bcrypt cost=12)
  - [x] API 키 암호화 (AES-256)
  - [x] 복호화 절차
  - [x] 키 관리

- [x] `specs/rate-limiting.md` 작성
  - [x] /login 엔드포인트 (5회/5분)
  - [x] /register 엔드포인트 (3회/시간)
  - [x] 구현 방식
  - [x] Redis 기반 저장

**산출물**:
- `docs/02-authentication/index.md`
- `docs/02-authentication/specs/api-endpoints.md`
- `docs/02-authentication/specs/token-management.md`
- `docs/02-authentication/specs/encryption.md`
- `docs/02-authentication/specs/rate-limiting.md`

---

### 5️⃣ 03-strategy (전략 에디터)

**상태**: ✅ 완료
**우선순위**: 5
**의존**: 02-authentication, 06-data

**작업 내용**:
- [x] `index.md` 작성
  - [x] 에디터 개요
  - [x] 노드-엣지 구조
  - [x] 전략 생성 플로우 (수동/LLM)
  - [x] 전략 실행 플로우
  - [x] 데이터 모델 개요
  - [x] 관련 문서 가이드

- [x] `specs/node-types.md` 작성
  - [x] 트리거 노드
  - [x] 데이터 소스 노드
  - [x] 조건 노드
  - [x] LLM 노드
  - [x] 액션 노드
  - [x] 리스크 관리 노드

- [x] `specs/validation-rules.md` 작성
  - [x] 순환 감지 알고리즘
  - [x] 타입 체크 규칙
  - [x] 트리거 단일 확인
  - [x] 엣지 연결 규칙

- [x] `specs/llm-integration.md` 작성
  - [x] OpenAI API 연동
  - [x] 프롬프트 템플릿
  - [x] 응답 파싱
  - [x] 비용 관리

- [x] `specs/execution-engine.md` 작성
  - [x] 스케줄러 설계
  - [x] 노드 순서 처리
  - [x] 에러 핸들링
  - [x] 재시도 정책

**산출물**:
- `docs/03-strategy/index.md`
- `docs/03-strategy/specs/node-types.md`
- `docs/03-strategy/specs/validation-rules.md`
- `docs/03-strategy/specs/llm-integration.md`
- `docs/03-strategy/specs/execution-engine.md`

---

## Phase 3: 시뮬레이션 & 확장 (Simulation & Extension)

### 6️⃣ 04-backtesting (백테스팅)

**상태**: ✅ 완료
**우선순위**: 6
**의존**: 03-strategy, 06-data

**작업 내용**:
- [x] `index.md` 작성
  - [x] 백테스팅 개요
  - [x] 파이프라인 구조
  - [x] 성과 지표
  - [x] 데이터 소스
  - [x] 비동기 실행
  - [x] 결과 시각화
  - [x] 관련 문서 가이드

- [x] `specs/data-processing.md` 작성
  - [x] OHLCV 데이터 수집
  - [x] 결측치 처리
  - [x] 시간대 통일 (UTC)
  - [x] 데이터 저장

- [x] `specs/indicators.md` 작성
  - [x] RSI 계산
  - [x] MACD 계산
  - [x] 볼린저 밴드 계산
  - [x] 이동평균선 계산
  - [x] 사용자 정의 지표

- [x] `specs/simulation.md` 작성
  - [x] 캔들 순회 알고리즘
  - [x] 조건 평가
  - [x] 매수/매도 시뮬레이션
  - [x] 포트폴리오 관리

- [x] `specs/performance-metrics.md` 작성
  - [x] 총 수익률 계산
  - [x] MDD 계산
  - [x] 승률 계산
  - [x] 샤프 비율 계산
  - [x] 기타 지표

- [x] `specs/commission-slippage.md` 작성
  - [x] Maker/Taker 수수료 모델
  - [x] 슬리피지 모델
  - [x] 수수료 계산 로직

**산출물**:
- `docs/04-backtesting/index.md`
- `docs/04-backtesting/specs/data-processing.md`
- `docs/04-backtesting/specs/indicators.md`
- `docs/04-backtesting/specs/simulation.md`
- `docs/04-backtesting/specs/performance-metrics.md`
- `docs/04-backtesting/specs/commission-slippage.md`

---

### 7️⃣ 05-blockchain (블록체인)

**상태**: ✅ 완료
**우선순위**: 7
**의존**: 04-backtesting, 06-data

**작업 내용**:
- [x] `index.md` 작성
  - [x] 블록체인 개요
  - [x] 체인 선택 기준 (Monad L1)
  - [x] 온체인 데이터 모델
  - [x] 크레딧 시스템
  - [x] 템플릿 마켓플레이스
  - [x] 가스비 최적화
  - [x] 개발 단계 (Phase 1~3)
  - [x] 관련 문서 가이드

- [x] `specs/smart-contracts.md` 작성
  - [x] 9개 컨트랙트 정의
  - [x] AccessControl, StrategyRegistry, FollowRegistry
  - [x] DecisionHistory, SettlementManager, FeeDistributor
  - [x] BuybackTreasury, G8DToken, G8DStaking
  - [x] 함수/이벤트 정의

- [x] `specs/settlement-system.md` 작성
  - [x] 오프체인 크레딧 시스템
  - [x] 온체인 정산 시스템
  - [x] 하이브리드 아키텍처
  - [x] 배치 처리 및 Merkle Tree

- [x] `specs/marketplace.md` 작성
  - [x] 템플릿 공개 플로우
  - [x] 템플릿 복제 플로우
  - [x] 결제 처리
  - [x] 저작자 지급

- [x] `specs/tokenomics.md` 작성
  - [x] G8D 토큰 모델
  - [x] 스테이킹 Tier 시스템
  - [x] 수수료 할인 구조
  - [x] 저작권료 부스트

- [x] `specs/web3-integration.md` 작성
  - [x] thirdweb SDK 연동
  - [x] 월렛 연동
  - [x] 트랜잭션 서명
  - [x] 블록체인 비활성화 모드

- [x] `specs/gas-optimization.md` 작성
  - [x] 배치 처리 전략
  - [x] Lazy 평가
  - [x] 메타트랜잭션

- [x] `specs/indexing.md` 작성
  - [x] The Graph Subgraph
  - [x] 간단 인덱서 (Python)
  - [x] Event Log 수집

- [x] `specs/environment-config.md` 작성
  - [x] 개발 서버 설정
  - [x] 운영 서버 설정
  - [x] 환경 변수 정의

- [x] `specs/security-audits.md` 작성
  - [x] 스마트 컨트랙트 보안
  - [x] 접근 제어
  - [x] 재진입 방지
  - [x] 감사 절차

**산출물**:
- `docs/05-blockchain/index.md`
- `docs/05-blockchain/specs/smart-contracts.md`
- `docs/05-blockchain/specs/settlement-system.md`
- `docs/05-blockchain/specs/marketplace.md`
- `docs/05-blockchain/specs/tokenomics.md`
- `docs/05-blockchain/specs/web3-integration.md`
- `docs/05-blockchain/specs/gas-optimization.md`
- `docs/05-blockchain/specs/indexing.md`
- `docs/05-blockchain/specs/environment-config.md`
- `docs/05-blockchain/specs/security-audits.md`

---

### 8️⃣ 07-admin (관리자 기능)

**상태**: ✅ 완료
**우선순위**: 8
**의존**: 02-authentication, 05-blockchain

**작업 내용**:
- [x] `index.md` 작성
  - [x] 관리자 기능 개요
  - [x] 권한 체계
  - [x] 환경별 차이
  - [x] 관련 문서 가이드

- [x] `specs/user-management.md` 작성
  - [x] 사용자 목록 조회
  - [x] 가입 승인 (개발 서버)
  - [x] 활성/비활성 처리
  - [x] 슈퍼유저 권한 부여

- [x] `specs/strategy-moderation.md` 작성
  - [x] 검토 대기 목록
  - [x] 승인/거절 처리
  - [x] 비공개 처리
  - [x] 신고 처리

- [x] `specs/credit-management.md` 작성
  - [x] 크레딧 충전
  - [x] 크레딧 환불
  - [x] 거래 내역 조회
  - [x] 사용자별 잔액 관리

- [x] `specs/royalty-settlement.md` 작성
  - [x] 월별 저작권료 집계
  - [x] 정산 생성
  - [x] 배치 지급
  - [x] 지급 내역 조회

- [x] `specs/system-monitoring.md` 작성
  - [x] 시스템 상태 확인
  - [x] 사용자 통계
  - [x] 거래 통계
  - [x] 수익 통계

**산출물**:
- `docs/07-admin/index.md`
- `docs/07-admin/specs/user-management.md`
- `docs/07-admin/specs/strategy-moderation.md`
- `docs/07-admin/specs/credit-management.md`
- `docs/07-admin/specs/royalty-settlement.md`
- `docs/07-admin/specs/system-monitoring.md`

---

## Phase 4: 최종 정합

### 9️⃣ PRD.md 재수정

**상태**: ✅ 완료
**우선순위**: 9
**의존**: 모든 도메인 완료

**작업 내용**:
- [x] 모든 상세 문서와의 정합성 확인
- [x] 누락된 요구사항 반영
- [x] API 설계 섹션 완성
- [x] 보안 요구사항 섹션 완성
- [x] 기술 아키텍처 섹션 업데이트
- [x] 참조 문서 링크 검증
- [x] 2.4 탈중앙화 섹션 수정 (하이브리드 아키텍처)
- [x] 2.5 관리자 기능 섹션 추가
- [x] 7.3 환경별 설정 섹션 추가

**산출물**: `PRD.md` (최종본)

---

## 상태 범례

| 상태 | 의미 |
|------|------|
| ⏳ 진행 예정 | 아직 시작하지 않음 |
| 🔄 진행 중 | 현재 작업 중 |
| ✅ 완료 | 작업 완료 및 검토됨 |
| ⏸️ 보류 | 일시 중단됨 |
| ❌ 취소 | 더 이상 필요하지 않음 |

---

## 진척도 개요

| Phase | 도메인 | 문서 수 | 완료율 |
|-------|--------|---------|--------|
| Phase 1 | PRD.md (초안) | 1 | ✅ 100% |
| Phase 1 | 01-overview | 1 | ✅ 100% |
| Phase 1 | 06-data | 6 | ✅ 100% (6/6) |
| Phase 2 | 02-authentication | 5 | ✅ 100% (5/5) |
| Phase 2 | 03-strategy | 5 | ✅ 100% (5/5) |
| Phase 3 | 04-backtesting | 6 | ✅ 100% (6/6) |
| Phase 3 | 05-blockchain | 10 | ✅ 100% (10/10) |
| Phase 3 | 07-admin | 6 | ✅ 100% (6/6) |
| Phase 4 | PRD.md (재수정) | 1 | ✅ 100% |
| Phase 4 | frontend-architecture | 1 | ✅ 100% |
| **합계** | **10개 도메인** | **42개 문서** | **✅ 100%** |

---

*마지막 업데이트: 2025-12-29*
