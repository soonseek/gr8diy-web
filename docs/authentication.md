# 인증 시스템 (Authentication)

## 개요
JWT 기반의 이중 토큰 인증 시스템으로, Access Token과 Refresh Token을 조합하여 보안과 사용자 경험을 최적화합니다.

## 토큰 구조
- **Access Token**: 30분 유효, API 요청에 사용
- **Refresh Token**: 7일 유효, 토큰 갱신에 사용
- **알고리즘**: HS256
- **Payload**: `sub`(user_id), `exp`, `type`

## 인증 흐름
1. 로그인 시 서버가 access_token과 refresh_token 생성
2. access_token은 응답 body로 전송 → 클라이언트 localStorage 저장
3. refresh_token은 httpOnly 쿠키로 전송 (XSS 방지)
4. API 요청 시 axios 인터셉터가 자동으로 Bearer 토큰 추가
5. 401 응답 시 자동으로 `/refresh` 호출하여 토큰 갱신

## 보안 기능
- bcrypt 비밀번호 해싱
- 비밀번호 복잡도 검증 (대소문자+숫자+특수문자)
- 상수 시간 비교로 타이밍 어택 방지
- 공통 비밀번호 차단

## 주요 파일
- `apps/api/app/core/security.py` - 토큰 생성/검증
- `apps/api/app/api/v1/auth.py` - 인증 API
- `apps/web/src/services/auth.ts` - 인증 서비스
- `apps/web/src/lib/axios.ts` - 인터셉터 설정
