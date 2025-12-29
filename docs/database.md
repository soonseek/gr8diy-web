# 데이터베이스 (Database)

## 개요

PostgreSQL을 메인 데이터베이스로 사용하고, Redis를 캐시 및 세션 저장소로 활용합니다. SQLAlchemy 2.0의 비동기 기능을 최대한 활용합니다.

---

## PostgreSQL

### 설정
- **드라이버**: asyncpg (비동기)
- **ORM**: SQLAlchemy 2.0 (Async)
- **마이그레이션**: Alembic

### 환경별 설정
- `development`: SSL disable
- `production`: SSL prefer

---

## 데이터베이스 테이블

gr8diy-web은 총 **16개의 주요 테이블**로 구성됩니다.

### 사용자 및 인증 (1)
| 테이블 | 설명 |
|--------|------|
| **users** | 사용자 계정 정보 (이메일, 비밀번호, manual_tier) |

### 전략 관리 (2)
| 테이블 | 설명 |
|--------|------|
| **strategies** | 전략 정의 (노드-엣지 JSON 구조) |
| **backtests** | 백테스트 결과 (수익률, MDD, 승률 등) |

### 실행 및 거래 (1)
| 테이블 | 설명 |
|--------|------|
| **executions** | 전략 실행 내역 (실거래 주문) |

### 템플릿 시스템 (2)
| 테이블 | 설명 |
|--------|------|
| **templates** | 공개 템플릿 (가격, 복제 횟수) |
| **template_clones** | 템플릿 복제 이력 |

### 크레딧 시스템 (2)
| 테이블 | 설명 |
|--------|------|
| **credits** | 사용자 크레딧 잔액 |
| **credit_transactions** | 크레딧 충전/사용 내역 |

### API 및 데이터 (2)
| 테이블 | 설명 |
|--------|------|
| **credentials** | LLM/거래소 API 키 (암호화 저장) |
| **ohlcv_data** | 시장 데이터 (OHLCV) |

### 블록체인 (5)
| 테이블 | 설명 |
|--------|------|
| **wallets** | 사용자 Monad L1 월렛 주소 |
| **follows** | 사용자 팔로우/구독 관계 |
| **staking_records** | G8D 스테이킹 기록 |
| **strategy_registrations** | 전략 온체인 등록 기록 |
| **settlements** | 오프체인 정산 데이터 |

### 관리자 (1)
| 테이블 | 설명 |
|--------|------|
| **author_royalties** | 저작자 월별 저작권료 |

---

## 상세 스키마

모든 테이블의 상세 스키마는 **[docs/06-data/](./06-data/)** 를 참고하세요:

| 문서 | 설명 |
|------|------|
| **[docs/06-data/index.md](./06-data/index.md)** | 테이블 개요 및 요약 |
| **[docs/06-data/specs/table-schemas.md](./06-data/specs/table-schemas.md)** | 상세 컬럼 정의 |
| **[docs/06-data/specs/erd.md](./06-data/specs/erd.md)** | ERD 다이어그램 |

---

## Redis

### 용도
- **Refresh Token 저장**: httpOnly 쿠키와 함께 사용 (서버 측 검증용)
- **Access Token 블랙리스트**: 로그아웃 시 토큰 무효화
- **레이트 리밋**: API 요청 제어

### 드라이버
- **Python**: aioredis

### Key 패턴
| 패턴 | 용도 | TTL |
|------|------|-----|
| `refresh_token:{user_id}:{token_id}` | Refresh Token 저장 | 7일 (604800초) |
| `blacklist:{access_token}` | Access Token 블랙리스트 | 30분 (1800초) |
| `rate_limit:{ip}:{endpoint}` | 레이트 리밋 카운터 | 1분/5분 |
| `login_history:{user_id}` | 로그인 기록 | 30일 |

---

## 주요 파일

| 파일 | 설명 |
|------|------|
| `apps/api/app/db/session.py` | DB 세션 |
| `apps/api/app/models/` | SQLAlchemy 모델 |
| `apps/api/app/alembic/` | 마이그레이션 |
| `apps/api/app/core/redis.py` | Redis 클라이언트 |

---

## 관련 문서

- **[./06-data/](./06-data/)** - 데이터 모델 상세
- **[./02-authentication/](./02-authentication/)** - 인증 시스템
- **[./05-blockchain/](./05-blockchain/)** - 블록체인 연동

---

*최종 업데이트: 2025-12-29*
