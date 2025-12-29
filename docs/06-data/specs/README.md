# Data Specs

이 디렉토리에는 데이터 모델의 상세 명세가 작성됩니다.

## 예상 문서 목록

| 문서 | 설명 |
|------|------|
| `erd.md` | 전체 ERD 다이어그램 (users, strategies, backtests, executions, credits, templates) |
| `table-schemas.md` | 각 테이블별 상세 스키마 (컬럼, 타입, 제약조건, 인덱스) |
| `constraints.md` | 제약조건, 트리거 (CASCADE 삭제, UNIQUE, CHECK) |
| `indexes.md` | 인덱스 설계, 쿼리 최적화 (user_id, status, timestamp) |
| `migrations.md` | 마이그레이션 계획 (Alembic 사용법, 버전 관리) |

## 상위 문서

- **[../index.md](../index.md)** - 데이터 모델 개요 및 ERD
