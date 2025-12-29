# 보안 (Security)

## 개요
다층 보안 아키텍처로 사용자 데이터와 API를 보호합니다. 인증, 인가, 레이트 리밋, CORS 등 다양한 보안 계층을 적용합니다.

## 인증 보안
- **비밀번호 해싱**: bcrypt (cost=12)
- **복잡도 검증**: 대소문자+숫자+특수문자, 최소 8자
- **상수 시간 비교**: 타이밍 어택 방지
- **공통 비밀번호 차단**: "password", "12345678" 등
- **httpOnly 쿠키**: Refresh Token XSS 방지

## API 보안
- **JWT 서명**: HS256 알고리즘, 환경변수 기반 시크릿 키
- **토큰 만료**: Access 30분, Refresh 7일
- **레�이트 리밋**: Redis 기반 Sliding Window
  - /login: 5회/분
  - /register: 3회/5분
  - /refresh: 10회/분

## CORS
- 환경변수 `CORS_ORIGINS` 기반 화이트리스트
- Credentials 허용 (쿠키 전송)
- 개발: `localhost:3000`
- 프로덕션: 배포 도메인

## 환경별 SSL
- `development`: `ssl=disable`
- `production`: `ssl=prefer`

## 예외 처리
표준화된 에러 응답 포맷:
- AuthenticationError (401)
- PermissionError (403)
- NotFoundError (404)
- ValidationError (422)
- RateLimitError (429)

## 주요 파일
- `apps/api/app/core/security.py` - 보안 유틸
- `apps/api/app/core/rate_limit.py` - 레이트 리밋
- `apps/api/app/core/exceptions.py` - 예외 처리
