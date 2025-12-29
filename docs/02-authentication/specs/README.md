# Authentication Specs

이 디렉토리에는 인증 시스템의 상세 명세가 작성됩니다.

## 예상 문서 목록

| 문서 | 설명 |
|------|------|
| `api-endpoints.md` | 각 엔드포인트별 요청/응답 스펙 (register, login, refresh, logout) |
| `token-management.md` | 토큰 생성, 갱신, 폐기 정책, Rotation |
| `rate-limiting.md` | 레이트 리밋 규칙 (login: 5회/5분, register: 3회/시간) |
| `encryption.md` | 암호화 방식 (bcrypt cost=12, AES-256 for API keys) |

## 상위 문서

- **[../index.md](../index.md)** - 인증 개요 및 설계 통합
