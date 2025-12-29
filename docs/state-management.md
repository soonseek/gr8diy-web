# 상태 관리 (State Management)

## 개요
서버 상태는 TanStack Query, 클라이언트 상태는 Zustand로 관리하는 하이브리드 상태 관리 전략을 사용합니다.

## TanStack Query (서버 상태)
- **용도**: API 데이터 캐싱, 동기화
- **설정**: staleTime 60초, retry 1회
- **DevTools**: 개발 모드에서 활성화

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['users', page],
  queryFn: () => fetchUsers(page),
  staleTime: 60000
})
```

## Zustand (클라이언트 상태)
- **용도**: 인증 상태, UI 상태
- **지속성**: localStorage 미들웨어
- **스토어**: authStore, blockchainStore

```typescript
interface AuthState {
  user: User | null
  accessToken: string | null
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
}

// 블록체인 상태
interface BlockchainState {
  isEnabled: boolean
  userTier: number  // T0~T5
  walletAddress: string | null
  setIsEnabled: (enabled: boolean) => void
  setUserTier: (tier: number) => void
}
```

## Axios 인터셉터
자동 토큰 주입 및 갱신:
- 요청: localStorage의 access_token을 헤더에 추가
- 응답(401): /refresh 호출 후 원래 요청 재시도

## 상태 흐름
1. 로그인 성공 → access_token 저장
2. Zustand 스토어 업데이트
3. axios 인터셉터가 자동으로 토큰 첨부
4. 401 발생 시 토큰 갱신

## 블록체인 상태 관리

### 환경별 분기

```typescript
// stores/blockchain.ts
interface BlockchainState {
  isEnabled: boolean
  userTier: number
  walletAddress: string | null
}

export const useBlockchainStore = create<BlockchainState>((set) => ({
  isEnabled: process.env.NEXT_PUBLIC_BLOCKCHAIN_ENABLED === 'true',
  userTier: 0,
  walletAddress: null,

  setUserTier: (tier) => set({ userTier: tier })
}))

// 훅에서 환경별 분기
export function useUserTier() {
  const isEnabled = useBlockchainStore((state) => state.isEnabled)

  if (!isEnabled) {
    // 블록체인 비활성화 모드: API에서 manual_tier 조회
    const { data } = useQuery(['me'], fetchUser)
    return data?.manual_tier ?? 0
  }

  // 블록체인 활성화 모드: 온체인 G8DStaking 조회
  return useReadContract({...})
}
```

### Tier 할인율 조회

```typescript
// lib/tier.ts
export const TIER_DISCOUNTS = [0, 10, 20, 30, 40, 50]  // %
export const TIER_AUTHOR_BOOSTS = [0, 5, 10, 25, 50, 100]  // %

export function getDiscountBps(tier: number): number {
  return TIER_DISCOUNTS[tier] * 100  // basis point
}

export function getAuthorBoostBps(tier: number): number {
  return TIER_AUTHOR_BOOSTS[tier] * 100
}
```

## 주요 파일
- `apps/web/src/stores/auth.ts` - 인증 스토어
- `apps/web/src/stores/blockchain.ts` - 블록체인 상태
- `apps/web/src/lib/axios.ts` - 인터셉터
- `apps/web/src/app/providers.tsx` - Query Provider
