# 문서 일관성 분석 보고서
# Documentation Consistency Analysis Report

**분석일**: 2025-12-29
**분석범위**: PRD.md vs docs/ (05-blockchain/design/ 제외)

---

## 1. 개요 (Overview)

이 보고서는 PRD와 도메인별로 재작성된 docs/ 내용 간의 논리적 일치성을 검토하고, 문서 간의 **conflict(충돌)**, **gray zone(모호함)**, **empty zone(누락)**을 식별합니다.

### 분석 대상 문서

| 구분 | 문서 |
|------|------|
| **PRD** | `PRD.md` |
| **루트 docs** | `docs/api-routes.md`, `docs/authentication.md`, `docs/database.md`, `docs/security.md`, `docs/frontend-architecture.md`, `docs/state-management.md`, `docs/ui-components.md`, `docs/deployment.md` |
| **도메인 docs** | `docs/01-overview/`, `docs/02-authentication/`, `docs/03-strategy/`, `docs/04-backtesting/`, `docs/05-blockchain/`, `docs/06-data/`, `docs/07-admin/` |

---

## 2. 주요 Conflicts (논리적 충돌)

### 2.1 토큰 만료 정책 불일치 [심각]

**위치**: PRD vs docs/02-authentication/index.md vs 루트 문서들

| 문서 | Access Token | Refresh Token |
|------|-------------|---------------|
| **PRD.md** (7.1) | 30분 | 7일 |
| **docs/authentication.md** | 30분 | 7일 |
| **docs/security.md** | 30분 | 7일 |
| **docs/02-authentication/index.md** (1.2) | **15분** | **1일** |
| **docs/02-authentication/specs/token-management.md** | 15분 | 1일 |

**문제점**: PRD와 루트 문서는 일치하나, 새로 작성된 도메인 문서와 다릅니다. 어느 쪽이 올바른지 결정이 필요합니다.

**권장사항**: PRD를 기준으로 통일 (Access: 30분, Refresh: 7일)

---

### 2.2 Refresh Token 저장 위치 불일치 [심각]

**위치**: PRD vs docs/02-authentication/index.md vs 루트 문서들

| 문서 | 저장 위치 |
|------|-----------|
| **PRD.md** (7.1) | httpOnly 쿠키로 Refresh Token 보안 |
| **docs/authentication.md** | httpOnly 쿠키로 전송 |
| **docs/security.md** | httpOnly 쿠키 (XSS 방지) |
| **docs/02-authentication/index.md** (1.3, 4.1) | **Redis (서버)에서 관리** |
| **docs/02-authentication/specs/token-management.md** | Redis에만 저장 |

**문제점**: PRD와 루트 문서는 "httpOnly 쿠키"를 명시하지만, 도메인 문서는 "Redis만" 언급합니다. 실제 구현에서는 **두 가지를 혼용**해야 할 수도 있습니다:
- Redis: 토큰 유효성 검증, 블랙리스트 관리
- httpOnly 쿠키: 클라이언트 전송 (XSS 방지)

**권장사항**: 두 방식의 혼용을 명확히 정의
1. 서버에서 Redis에 토큰 저장 (검증용)
2. 응답 시 httpOnly 쿠키로 전송 (클라이언트 XSS 방지)

---

### 2.3 레이트 리밋 설정 불일치 [중간]

**위치**: docs/api-routes.md vs docs/02-authentication/index.md vs docs/security.md

| 엔드포인트 | docs/api-routes.md | docs/02-authentication/ | docs/security.md |
|-----------|-------------------|------------------------|-----------------|
| `/login` | 5회/분 | 5회/5분 | 5회/분 |
| `/register` | 3회/5분 | 3회/시간 | 3회/5분 |
| `/refresh` | 10회/분 | 언급 없음 | 10회/분 |

**문제점**: `/register`의 레이트 리밋이 "5분" vs "시간"으로 다릅니다.

**권장사항**: PRD 기준으로 통일 (5분 기준)

---

## 3. Gray Zones (모호한 정의)

### 3.1 토큰 Rotation과 httpOnly 쿠키의 관계 [중간]

**위치**: docs/02-authentication/index.md

- 2.3절 "토큰 갱신 플로우"에서 refresh_token을 Authorization: Bearer 헤더로 보냄
- 하지만 PRD와 루트 문서는 httpOnly 쿠키로 전송한다고 명시

**문제점**:
1. httpOnly 쿠키를 사용하면 프론트엔드에서 JavaScript로 접근 불가
2. `/refresh` 요청 시 쿠키가 자동 전송되도록 해야 함
3. 현재 docs/02-authentication/specs/api-endpoints.md에서는 Authorization: Bearer로 되어 있음

**권장사항**: 토큰 갱신 방식을 명확히 정의
- httpOnly 쿠키 방식: 쿠키가 자동 전송됨 (프론트엔드에서手动 설정 불필요)
- Authorization 헤더 방식: 프론트엔드에서 localStorage에서 꺼내서 헤더에 담아야 함

---

### 3.2 블록체인 비활성화 모드에서의 Tier 처리 [중간]

**위치**: docs/05-blockchain/index.md (9.2, 10.2)

- 오프체인 크레딧 시스템에서도 Tier 할인을 적용한다고 명시
- 하지만 블록체인 비활성화 모드에서는 "항상 T0"이라고 명시 (10.2)
- 그러면 오프체인 정산 시 할인율은 어떻게 결정되는지?

**문제점**:
- docs/05-blockchain/specs/settlement-system.md (2.1, 2.2)에서 개발/운영 서버 설정에 Tier 할인율이 나옴
- 블록체인 비활성화 모드에서는 이 할인율을 어떻게 적용할지 명확하지 않음

**권장사항**:
- 옵션 A: 블록체인 비활성화 모드에서도 관리자가 수동으로 Tier 부여 가능
- 옵션 B: 항상 T0 (할인 없음)로 고정

---

### 3.3 Wallet의 1:1 관계 정의 [경미]

**위치**: docs/06-data/index.md (3.2)

- users와 wallets를 1:1 관계로 정의
- 하지만 중간에 "한 사용자는 하나의 월렛 보유"라고만 명시
- 사용자가 월렛을 변경할 수 있는지, 여러 월렛을 가질 수 있는지 불명확

**권장사항**: 월렛 변경/추가 정책 명시

---

### 3.4 Follow의 중간 테이블 여부 [경미]

**위치**: docs/06-data/index.md (2.12)

- follows 테이블을 별도로 정의
- strategy_id를 포함 (팔로워가 특정 전략을 팔로우)
- 이것이 "사용자 간 팔로우"인지 "전략 팔로우"인지 모호함

**문제점**:
- PRD에서는 "구독, 팔로우"를 언급하지만 명확한 정의 없음
- docs/05-blockchain/index.md에서는 FollowRegistry를 "사용자별 구독(팔로우) 관리"로 정의

**권장사항**: 팔로우의 정확한 의미를 명확히 (사용자 팔로우 vs 전략 구독)

---

## 4. Empty Zones (누락된 내용)

### 4.1 루트 문서들의 블록체인 관련 내용 누락 [중간]

**위치**: docs/frontend-architecture.md, docs/state-management.md 등

- 새로운 docs/05-blockchain/에서는 "블록체인 비활성화 모드"를 상세히 설명
- 하지만 루트 문서들에는 이 내용이 전혀 없음
- 특히 `docs/frontend-architecture.md`에서 `NEXT_PUBLIC_BLOCKCHAIN_ENABLED` 환경변수를 언급하지만, 이것이 무엇인지 설명 부족

**권장사항**: 루트 문서들에 블록체인 비활성화 모드에 대한 개요 추가

---

### 4.2 데이터 모델 ERD와 루트 문서의 불일치 [중간]

**위치**: docs/database.md vs docs/06-data/

| 테이블 | docs/database.md | docs/06-data/ |
|--------|-----------------|---------------|
| wallets | 없음 | 있음 |
| follows | 없음 | 있음 |
| staking_records | 없음 | 있음 |
| strategy_registrations | 없음 | 있음 |
| settlements | 없음 | 있음 |
| author_royalties | 없음 | 있음 |

**문제점**: 루트 `docs/database.md`는 users 테이블만 언급하고, 나머지는 누락되어 있습니다.

**권장사항**: `docs/database.md`를 최신 스키마로 업데이트하거나, `docs/06-data/index.md`로 대체

---

### 4.3 API 라우트 문서의 불완전성 [중간]

**위치**: docs/api-routes.md vs PRD.md 6장

- `docs/api-routes.md`에는 인증(/api/v1/auth)과 사용자(/api/v1/users)만 있음
- PRD 6장에는 전략, 백테스트, 실행, 템플릿, 크레딧, Credential, 시장 데이터 API까지 포함
- 도메인별 specs 문서에 API가 분산되어 있지만, 중앙 요약 문서가 부족

**권장사항**:
- `docs/api-routes.md`에 모든 주요 API 엔드포인트 추가
- 또는 도메인별 index.md에 API 개요 추가

---

### 4.4 관리자 API 명세 누락 [경미]

**위치**: docs/07-admin/index.md

- 관리자 기능 개요는 있지만, API 엔드포인트 명세가 없음
- `specs/` 하위에 문서가 있어야 하지만, 실제로는 존재하는지 확인 필요

**권장사항**: 관리자 API 엔드포인트 문서 작성

---

### 4.6 템플릿 마켓플레이스 문서 누락 [중간]

**위치**: 전체 docs/

- PRD 2.2절과 3.3절에 템플릿 기능이 있음
- 하지만 이에 대한 별도의 도메인 문서가 없음
- docs/03-strategy/index.md에 "8.1 템플릿 마켓플레이스"가 있지만 상세하지 않음
- docs/06-data/index.md에 templates, template_clones 테이블은 있음

**검토 결과**: 템플릿 시스템은 전략과 밀접하게 연관되어 있어 별도 도메인(05-templates/)로 분리하는 것보다 다음 중 하나 권장:

1. **docs/03-strategy/specs/templates.md** 생성 - 전략의 확장 기능으로
2. **docs/07-admin/specs/template-moderation.md** 생성 - 관리자 기능으로

**도메인 번호 재배치(05-templates, 06-blockchain...)는 권장하지 않음**:
- 기존 구조 유지 (blockchain이 05번인 이유: Monad L1 체인 기반)
- PRD의 도메인 순서와 일치
- 이미 배포된 문서들의 크스 레퍼런스 영향 최소화

**권장사항**: docs/03-strategy/specs/templates.md 또는 docs/07-admin/specs/template-moderation.md 생성

---

## 5. 도메인 간 연결 검토

### 5.1 인증 ↔ 블록체인 [양호]

- docs/02-authentication/와 docs/05-blockchain/의 연결이 명확함
- 월렛 연동, 스테이킹 등이 잘 설명됨

### 5.2 전략 ↔ 백테스팅 [양호]

- docs/03-strategy/와 docs/04-backtesting/의 연결이 명확함
- 전략 정의를 백테스트에서 사용하는 방법이 잘 설명됨

### 5.3 전략 ↔ 블록체인 [양호]

- 전략 등록, 온체인 기록이 잘 설명됨
- Merkle Tree 기반 커밋이 명확함

### 5.4 데이터 모델 ↔ 전체 도메인 [양호]

- docs/06-data/가 모든 테이블을 잘 정리함
- ERD가 제공됨

---

## 6. 우선순위별 수정 권장사항

### 🔴 높은 우선순위 (즉시 수정 필요)

1. **토큰 만료 정책 통일** (PRD 기준: Access 30분, Refresh 7일)
   - 대상: docs/02-authentication/index.md, specs/token-management.md

2. **Refresh Token 저장 방식 명확화**
   - Redis + httpOnly 쿠키 혼용 방식으로 문서 수정

3. **레이트 리밋 설정 통일**
   - /register: 3회/5분으로 통일

### 🟡 중간 우선순위 (다음 수정에서)

4. **블록체인 비활성화 모드에서의 Tier 처리 명확화**

5. **루트 문서들의 블록체인 관련 내용 추가**
   - docs/frontend-architecture.md
   - docs/state-management.md

6. **docs/database.md를 docs/06-data/ 기준으로 업데이트**

7. **API 라우트 문서 보완**
   - docs/api-routes.md에 전체 API 개요 추가

### 🟢 낮은 우선순위 (향후 개선)

8. **템플릿 시스템 별도 도메인 문서 작성**
   - docs/08-templates/ 생성

9. **전략 실행 엔진 상세 문서 작성**
   - docs/03-strategy/specs/execution-engine.md

10. **Wallet 1:1 관계 정책 명확화**

11. **Follow의 정확한 정의 명시**

---

## 7. 정리 (Summary)

### 7.1 전체 평가

- **PRD와 도메인 문서 간의 논리적 일치성**: 대체로 양호
- **루트 문서와 도메인 문서 간의 일치성**: 일부 불일치 존재 (특히 인증 관련)
- **도메인 간 연결**: 잘 정리됨
- **누락된 내용**: 템플릿, 실행 엔진, 관리자 API 등

### 7.2 주요 원인

1. **문서 작성 시점 차이**: 루트 문서는 이전에 작성되었고, 도메인 문서는 최근에 작성됨
2. **PRD 업데이트 반영 부족**: 도메인 문서 작성 시 PRD와의 정렬이 부분적으로 누락됨
3. **문서 간 참조 미약함**: 루트 문서가 도메인 문서를 충분히 참조하지 않음

### 7.3 다음 단계

1. 이 분석 보고서를 토대로 어떤 충돌을 해결할지 결정
2. 우선순위별로 문서 수정 진행
3. 수정 후 문서 간 크로스 레퍼런스 강화

---

*분석 완료일: 2025-12-29*
*분석자: Claude Code*
