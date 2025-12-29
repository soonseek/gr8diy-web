# 프론트엔드 아키텍처 (Frontend Architecture)

## 개요
Next.js 14 App Router 기반의 SPA로, TypeScript와 Tailwind CSS를 사용하여 모던하고 반응형인 UI를 제공합니다.

## 디렉토리 구조
```
src/
├── app/                    # Next.js App Router 페이지
│   ├── (auth)/            # 인증 관련 페이지 그룹
│   │   ├── login/         # 로그인
│   │   └── register/      # 회원가입
│   ├── strategies/        # 전략 관리
│   ├── backtest/          # 백테스팅
│   ├── marketplace/       # 템플릿 마켓플레이스
│   ├── profile/           # 사용자 프로필
│   └── admin/             # 관리자 페이지
├── components/            # React 컴포넌트
│   ├── home/              # 홈페이지 컴포넌트
│   ├── strategies/        # 전략 에디터
│   ├── backtest/          # 백테스트 결과
│   ├── ui/                # 공용 UI 컴포넌트
│   └── admin/             # 관리자 컴포넌트
├── services/              # API 호출 함수
├── stores/                # Zustand 상태 관리
│   └── auth.ts            # 인증 상태
├── hooks/                 # 커스텀 React 훅
│   └── use-auth.ts        # 인증 훅
├── lib/                   # 유틸리티
│   ├── api.ts             # API 클라이언트
│   ├── axios.ts           # Axios 설정
│   └── contracts.ts       # Web3 컨트랙트 (thirdweb)
└── types/                 # TypeScript 타입
```

## 주요 페이지
| 페이지 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| HomePage | `/` | 랜딩 페이지 | - |
| LoginPage | `/login` | 로그인 | - |
| RegisterPage | `/register` | 회원가입 | - |
| StrategiesPage | `/strategies` | 내 전략 목록 | Required |
| StrategyEditor | `/strategies/new` | 전략 생성 | Required |
| BacktestPage | `/backtest` | 백테스팅 | Required |
| MarketplacePage | `/marketplace` | 템플릿 마켓 | Required |
| ProfilePage | `/profile` | 프로필 설정 | Required |
| AdminDashboard | `/admin` | 관리자 대시보드 | Admin |

## 홈페이지 컴포넌트
- **Header**: 고정 네비게이션, 로그인/회원가입 버튼, 모바일 반응형 메뉴
- **Hero**: 프롬프트 입력 폼, 예시 버튼, 배경 애니메이션
- **HowItWorks**: 4단계 프로세스 설명
- **Gallery**: 알고리즘 갤러리 (카테고리 필터, 카드)
- **Footer**: 브랜드 정보, 링크

## 인증 및 권한
```typescript
// lib/api.ts - 인증된 API 호출
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// 토큰 자동 주입
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 응답 시 토큰 갱신
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // 토큰 refresh 로직
      const refreshToken = localStorage.getItem('refresh_token');
      const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
      localStorage.setItem('access_token', data.access_token);
      return api.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

## UI 컴포넌트
CVA(class-variance-authority) 기반의 shadcn/ui 패턴:
- Button (variants: default, outline, ghost, etc.)
- Card (Header, Title, Content, Footer)
- Input, Textarea, Select
- Modal, Dialog
- Table, Pagination

## Web3 연동 (선택적)
```typescript
// lib/contracts.ts - 블록체인 연동
import { getContract } from "thirdweb";
import { thirdwebClient, monad } from "./thirdweb";

// 블록체인 비활성화 모드 체크
export const isBlockchainEnabled = () => {
  return process.env.NEXT_PUBLIC_BLOCKCHAIN_ENABLED === 'true';
};

// 월렛 연결 (블록체인 활성화 시에만 표시)
export function useWalletConnection() {
  if (!isBlockchainEnabled()) {
    return {
      address: null,
      connect: null,
      isConnected: false
    };
  }

  // thirdweb SDK 사용
  // ...
}
```

## 환경별 설정
```typescript
// next.config.js - 환경 변수
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV, // development | production
    NEXT_PUBLIC_BLOCKCHAIN_ENABLED: process.env.NEXT_PUBLIC_BLOCKCHAIN_ENABLED, // true | false
  }
}
```

## 상태 관리
```typescript
// stores/auth.ts - Zustand 스토어
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const { data } = await api.post('/api/v1/auth/login', { email, password });
    set({
      user: data.user,
      isAuthenticated: true
    });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, isAuthenticated: false });
  }
}));
```

## 라우트 가드
```typescript
// middleware.ts - 인증 가드
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 인증 필요한 페이지
  const protectedPaths = ['/strategies', '/backtest', '/marketplace', '/profile'];
  const adminPaths = ['/admin'];

  const token = request.cookies.get('access_token');

  if (protectedPaths.some(path => pathname.startsWith(path))) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  if (adminPaths.some(path => pathname.startsWith(path))) {
    // 관리자 권한 확인은 페이지에서 수행
  }

  return NextResponse.next();
}
```

## 관련 문서
- **[./02-authentication/](./02-authentication/)** - 인증 시스템
- **[./03-strategy/](./03-strategy/)** - 전략 관리
- **[./05-blockchain/specs/web3-integration.md](./05-blockchain/specs/web3-integration.md)** - Web3 연동 상세

---

*최종 업데이트: 2025-12-29*
