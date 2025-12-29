# gr8diy-web 제품 요구사항 문서 (PRD)

## 1. 제품 개요

### 1.1 제품명
**gr8diy-web** - 오픈소스 DIY 자동매매 플랫폼 dApp

### 1.2 비전
누구나 코딩 지식 없이 자연어(프롬프트)만으로 자동매매 알고리즘을 생성, 배포, 공유할 수 있는 100% 오픈소스 플랫폼 dApp을 구축함으로서, 자동매매 시장의 수요자 - 공급자 정보 격차를 해소한다.

### 1.3 타겟 사용자
- 코딩 경험이 없는 개인 투자자
- 자동매매에 관심있지만 진입장벽을 느끼는 사용자
- 자신의 투자 전략을 공유하고 싶은 트레이더

### 1.4 문제 정의
현재 자동매매 시장은 다음과 같은 문제가 있습니다:
- **진입장벽**: 프로그래밍 지식 없이는 자동매매 알고리즘을 구현할 수 없음
- **정보 비대칭**: 성공적인 전략을 가진 소수(공급자)와 이를 필요로 하는 다수(수요자) 사이의 정보 격차
- **플랫폼 종속**: 기존 플랫폼은 폐쇄적이며 사용자 간 전략 공유가 어려움
- **투명성/비용**: 백테스트 결과, 실제 실행 성과에 대한 검증 불가 및 높은 수수료

### 1.5 해결책
- **자연어 기반 전략 생성**: LLM과 협력하여 코딩 없이 자연어(프롬프트)로 전략 생성
- **노드-엣지 에디터**: 직관적인 시각적 인터페이스로 복잡한 로직 구성
- **오프체인 정산 시스템**: 크레딧 기반 간편 결제 (기본 모드)
- **선택적 온체인 검증**: 블록체인에 데이터 기록 (선택적 활성화)
- **하이브리드 아키텍처**: 온체인(선택) + 오프체인(기본) 유연 운용
- **오픈소스 배려**: 블록체인 비활성화 모드로 로컬/오픈소스 배포 지원
- **템플릿 마켓플레이스**: 성공적인 전략을 공유하고 복제할 수 있는 개방형 생태계

### 1.6 차별점
| 구분 | 기존 솔루션 | gr8diy-web |
|------|-----------|------------|
| **진입장벽** | 코딩 필수 | 자연어/노드 에디터 (No-Code) |
| **개방성** | 폐쇄적 플랫폼 | 100% 오픈소스 (MIT License) |
| **검증** | 센트럴리즘 | 탈중앙화 (블록체인 온체인 선택) |
| **생태계** | 단방향 (소비자 중심) | 양방향 (생산자+소비자) |
| **배포** | 상용 SaaS | 셀프호스팅 가능 (블록체인 비활성화 모드) |

---

## 2. 핵심 기능

### 2.1 전략 (Strategy)
- n8n, zapier와 같은 node-edge 기반의 **strategy 에디터**를 기반으로 전략을 생성
- LLM에게 전략 생성의 전 과정에 대한 협력을 받을 수 있다
- 생성한 전략을 플랫폼 내에서 백테스트 할 수 있다
- 연동된 거래소를 기반으로 생성한 전략을 실행할 수 있다
- 상세: [docs/03-strategy/overview.md](docs/03-strategy/overview.md)

**노드 타입**:
- **트리거 노드**: 시간, 가격 변동 등 시작 조건 설정
- **데이터 소스 노드**: 시장 데이터 조회 (OHLCV)
- **조건 노드**: IF/AND/OR 등 논리 연산
- **LLM 노드**: OpenAI API를 활용한 시장 분석
- **액션 노드**: 일반 주문(Buy/Sell), 주문 취소, TP/SL 설정, 리스크 관리

**전략 생성/실행 플로우**:
1. 에디터에서 노드-엣지 구성으로 전략 정의
2. (선택) LLM 프롬프트 입력 → 자동 전략 생성 파싱
3. 백테스트로 성과 검증
4. 실제 거래소 연동하여 자동 실행

### 2.2 템플릿
- 자신의 전략을 다른 사용자에게 공개할 수 있다
- 다른 사용자의 전략을 복제하여 사용할 수 있다

### 2.3 백테스팅
**시뮬레이션 방식**: 과거 OHLCV 데이터를 기반으로 캔들 순회하며 전략 조건 평가

**성과 지표**:
- **수익률**: 총 수익률 (%), CAGR
- **MDD**: 최대 낙폭 (Maximum Drawdown)
- **승률**: 승/패 횟수 비율
- **샤프 비율**: 리스크 조정 수익성 지표

### 2.4 탈중앙화 및 결제 시스템
- **기본 모드**: 오프체인 크레딧 기반 결제
  - 백테스트, 전략 실행, 템플릿 복제 비용을 크레딧으로 결제
  - 크레딧 충전 후 사용 (선결제)
  - 저작권료는 크레딧으로 지급 (월별 정산)

- **선택적 온체인** (BLOCKCHAIN_ENABLED=true):
  - Monad L1 블록체인에 데이터 기록
  - G8D 토큰 스테이킹으로 Tier 혜택
  - USDT0로 추가 결제 옵션

- **블록체인 비활성화 모드**:
  - 로컬 개발, 오픈소스 배포 시 블록체인 없이 전체 기능 사용 가능
  - 환경 변수 `BLOCKCHAIN_ENABLED=false`로 설정

- 상세:
  - [docs/05-blockchain/index.md](docs/05-blockchain/index.md)
  - [docs/05-blockchain/specs/settlement-system.md](docs/05-blockchain/specs/settlement-system.md)

### 2.5 관리자 기능
- **사용자 관리**: 가입 승인(개발 서버), 활성/비활성, 권한 관리
- **전략 검토**: 검토 대기 목록, 승인/거절, 비공개 처리
- **크레딧 관리**: 충전, 환불, 거래 내역 조회
- **저작권료 정산**: 월별 집계, 크레딧 지급 처리
- **시스템 모니터링**: 상태 확인, 사용자/거래/수익 통계
- 상세: [docs/07-admin/index.md](docs/07-admin/index.md)

---

## 3. 사용자 플로우

### 3.1 신규 사용자 온보딩
```
1. 랜딩 페이지 방문
2. Hero 섹션에서 전략 에디터 예시 및 템플릿 확인
3. 회원가입, 로그인
4. LLM Credential API 키 등록 (선택)
5. 거래소 Credential API 키 등록 (선택)
```

### 3.2 전략 기능 사용 플로우
```
1. 직접 전략 생성할지, LLM을 통해 자동 생성할지 선택
2. 그려진 노드 엣지의 상세 설정값을 편집 (LLM 노드 사용 시 LLM Credential 필수)
3. 편집 완료 후 배포된 전략에 대해 백테스트 수행
4. 백테스트 수행 완료 후 MDD, 승률, 수익률 결과 확인
5. 전략 실행 설정 (거래소 Credential 필수)
6. 전략 실행 히스토리 확인
```

### 3.3 템플릿 기능 사용 플로우
```
1. 템플릿 탐색
2. 마음에 드는 전략 발견
3. "복제" 클릭
4. 파라미터 조정 및 필요한 추가 Credential 등록
5. 자신의 전략으로 에디터 환경에 등록
```

---

## 4. 기술 아키텍처

### 4.1 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Next.js 14      │  프론트엔드 (:3000)
                    │   - TanStack Q.   │
                    │   - Zustand       │
                    └─────────┬─────────┘
                              │ HTTP/REST
                    ┌─────────▼─────────┐
                    │   FastAPI         │  백엔드 (:8000)
                    │   - Pydantic      │
                    │   - JWT Auth      │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐    ┌───────▼────────┐    ┌───────▼────────┐
│  PostgreSQL    │    │  Redis         │    │  LLM/거래소    │
│  - users       │    │  - sessions    │    │  - OpenAI      │
│  - strategies  │    │  - cache       │    │  - Binance     │
│  - backtests   │    │                │    │  - Upbit       │
└────────────────┘    └────────────────┘    └────────────────┘
```

### 4.2 계층별 구조

| 계층 | 기술 | 역할 |
|------|------|------|
| **프레젠테이션** | Next.js 14, React, Tailwind | UI/UX, 사용자 인터랙션 |
| **API/인증** | FastAPI, Pydantic, JWT | REST API, 요청 검증, 인증/인가 |
| **데이터 액세스** | SQLAlchemy 2.0, PostgreSQL, Redis | ORM, 데이터베이스 연동 |
| **외부 연동** | httpx, ccxt | LLM API, 거래소 API |

### 4.3 데이터 플로우

**인증 플로우**:
```
Client → FastAPI (login) → PostgreSQL (user 조회)
                     → Redis (refresh token 저장)
                     ← JWT access_token + refresh_token
Client → localStorage 토큰 저장
Client → Axios 인터셉터 (Bearer token 주입)
```

**백테스트 플로우**:
```
Client → 전략 정의 요청
        ↓
FastAPI → 전략 저장 (PostgreSQL)
        ↓
백테스팅 서비스 → OHLCV 데이터 조회 → 캔들 순회 → 조건 평가
                ↓
        결과 저장 (PostgreSQL) ← 성과 지표 계산
                ↓
        Client 결과 반환
```

**전략 실행 플로우**:
```
스케줄러 → 트리거 조건 확인
        ↓
FastAPI → 거래소 API (httpx/ccxt)
        ↓
주문 실행 → PostgreSQL (executions 기록)
        ↓
Client → 실시간 결과 표시
```

**LLM 전략 생성 플로우**:
```
Client → 프롬프트 입력
        ↓
FastAPI → OpenAI API 호출
        ↓
LLM 응답 파싱 → 노드-엣지 JSON 변환
        ↓
Client → 에디터에 자동 반영
```

### 4.4 백엔드 (FastAPI)
| 구성요소 | 기술 |
|---------|------|
| 웹 프레임워크 | FastAPI |
| 데이터베이스 | PostgreSQL (asyncpg) |
| 캐시 | Redis |
| ORM | SQLAlchemy 2.0 (Async) |
| 마이그레이션 | Alembic |
| 인증 | JWT (Access + Refresh) |

### 4.2 프론트엔드 (Next.js 14)
| 구성요소 | 기술 |
|---------|------|
| 프레임워크 | Next.js 14 (App Router) |
| 언어 | TypeScript |
| 스타일링 | Tailwind CSS |
| 상태 관리 | TanStack Query + Zustand |
| HTTP 클라이언트 | Axios (인터셉터 포함) |

### 4.3 배포
- 컨테이너: Docker Compose
- 인프라: PostgreSQL, Redis, FastAPI, Next.js
- 상세: [docs/01-overview/architecture.md](docs/01-overview/architecture.md)

---

## 5. 도메인별 상세 문서

| 도메인 | 경로 | 설명 |
|--------|------|------|
| 시스템 개요 | [docs/01-overview/](docs/01-overview/) | 아키텍처, 기술 스택 |
| 인증 | [docs/02-authentication/](docs/02-authentication/) | JWT, Redis, 보안 |
| 전략 | [docs/03-strategy/](docs/03-strategy/) | 에디터, 노드 타입 |
| 백테스팅 | [docs/04-backtesting/](docs/04-backtesting/) | 파이프라인, 지표 |
| 블록체인 | [docs/05-blockchain/](docs/05-blockchain/) | 스마트 컨트랙트, 크레딧 |
| 데이터 | [docs/06-data/](docs/06-data/) | 데이터 모델, ERD |

---

## 6. API 설계 (개요)

상세 API 명세는 [docs/02-authentication/specs/](docs/02-authentication/specs/) 참조

### 6.1 인증 (/api/v1/auth)
- `POST /register` - 회원가입
- `POST /login` - 로그인
- `POST /refresh` - 토큰 갱신
- `POST /logout` - 로그아웃

### 6.2 사용자 (/api/v1/users)
- `GET /me` - 내 정보 조회
- `GET /` - 사용자 목록 (페이지네이션)
- `PATCH /me` - 내 정보 수정
- `DELETE /me` - 회원 탈퇴

### 6.3 전략 (/api/v1/strategies)
- `GET /` - 전략 목록 조회 (페이지네이션, 필터링)
- `POST /` - 전략 생성
- `GET /{id}` - 전략 상세 조회
- `PATCH /{id}` - 전략 수정
- `DELETE /{id}` - 전략 삭제
- `POST /{id}/deploy` - 전략 배포
- `POST /{id}/pause` - 전략 일시정지

### 6.4 백테스트 (/api/v1/backtests)
- `POST /` - 백테스트 요청
- `GET /` - 백테스트 목록 조회
- `GET /{id}` - 백테스트 결과 조회
- `DELETE /{id}` - 백테스트 삭제

### 6.5 실행 (/api/v1/executions)
- `GET /` - 실행 내역 조회 (페이지네이션)
- `GET /{id}` - 실행 상세 조회
- `POST /{id}/cancel` - 실행 취소

### 6.6 템플릿 (/api/v1/templates)
- `GET /` - 공개 템플릿 목록 조회
- `POST /strategies/{id}/publish` - 전략을 템플릿으로 공개
- `POST /{id}/clone` - 템플릿 복제 (결제)
- `PATCH /{id}` - 템플릿 수정 (가격, 설명)
- `DELETE /{id}` - 템플릿 삭제

### 6.7 크레딧 (/api/v1/credits)
- `GET /` - 내 크레딧 잔액 조회
- `GET /transactions` - 거래 내역 조회
- `POST /charge` - 크레딧 충전 (fiat/crypto)

### 6.8 Credential (/api/v1/credentials)
- `GET /` - 등록된 Credential 목록 조회
- `POST /` - Credential 등록 (암호화 저장)
- `PATCH /{id}` - Credential 수정
- `DELETE /{id}` - Credential 삭제

### 6.9 시장 데이터 (/api/v1/market)
- `GET /ohlcv` - OHLCV 데이터 조회 (symbol, timeframe)
- `GET /symbols` - 지원되는 거래쌍 목록

---

## 7. 보안 요구사항 (개요)

상세 보안 정책은 [docs/02-authentication/overview.md](docs/02-authentication/overview.md) 참조

### 7.1 인증
- JWT Access Token (30분) + Refresh Token (7일)
- httpOnly 쿠키로 Refresh Token 보안
- bcrypt 비밀번호 해싱
- 비밀번호 복잡도 검증 (대소문자+숫자+특수문자)

### 7.2 API 보안
- 레이트 리밋 (엔드포인트별 제한)
- CORS 설정 (환경별 화이트리스트)
- 환경별 SSL 모드 (개발: disable, 프로덕션: prefer)

### 7.3 환경별 설정
| 구분 | 개발 서버 | 운영 서버 |
|------|-----------|-----------|
| **블록체인** | Testnet | Mainnet |
| **가입** | 승인제 (MANUAL_APPROVAL) | 공개 (PUBLIC) |
| **거래 모드** | 시뮬레이션 (PAPER_TRADING) | 실거래 (LIVE_TRADING) |

### 7.4 데이터 보안
- API 키 암호화 저장
- 로그인 기록
- 이상 탐지 (의심스러운 활동)

---

## 8. UI/UX 가이드라인

### 8.1 디자인 원칙
- 다크 모드 기본
- 모바일 우선 반응형 디자인
- 직관적인 프롬프트 입력 인터페이스
- 시각적인 백테스팅 결과

### 8.2 주요 페이지
| 페이지 | 경로 | 설명 |
|--------|------|------|
| 랜딩 | `/` | Hero, How It Works, templates |
| 대시보드 | `/dashboard` | 내 알고리즘, 실행 현황 |
| 에디터 | `/editor` | 노드 엣지 입력 및 수정 |
| 백테스트 | `/backtest` | 전략 백테스트 수행, 결과 확인 |
| 실행 | `/run` | 전략을 실행하고 히스토리와 결과 확인 |
| 템플릿 | `/templates` | 공개 알고리즘 탐색 |
| 설정 | `/settings` | 계정, LLM 및 거래소 Credential 관리 |

---

## 9. 성능 지표

### 9.1 기술 KPI
- API 응답 시간: < 200ms (p95)
- 웹페이지 로드: < 2초 (FCP)
- 가동 시간: 99.9%

### 9.2 비즈니스 KPI
- 회원가입 전환율
- 전략 생성 완료율
- 템플릿에서의 복제율

---

## 10. 오픈소스 라이선스

- **라이선스**: MIT License
- **기여**: PR 환영, 기여 가이드 준수
- **커뮤니티**: Discord, GitHub Discussions

---

*문서 버전: 2.0*
*최종 업데이트: 2025-12-29*
