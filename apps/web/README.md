# @gr8diy-web

Next.js 14 frontend application with App Router, TypeScript, and Tailwind CSS.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui patterns (class-variance-authority based)
- **State Management**:
  - Server State: TanStack Query (React Query)
  - Client State: Zustand with persistence
- **HTTP Client**: Axios with interceptors
- **Build Tool**: Turborepo

## Project Structure

```
apps/web/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   ├── ui/          # Reusable UI components
│   │   └── layout/      # Layout components
│   ├── lib/             # Utility functions
│   │   ├── axios.ts     # Axios instance with interceptors
│   │   └── utils.ts     # General utilities
│   ├── hooks/           # Custom React hooks
│   │   └── use-auth.ts  # Authentication hook
│   ├── services/        # API service functions
│   │   └── api.ts       # API endpoints wrapper
│   ├── stores/          # Zustand stores
│   │   └── auth.ts      # Auth state management
│   └── types/           # TypeScript type definitions
├── public/              # Static assets
├── .env                 # Environment variables
├── .env.example         # Environment variables template
├── next.config.js       # Next.js configuration
└── tailwind.config.js   # Tailwind CSS configuration
```

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm 8+

### Installation

```bash
# Install dependencies
pnpm install

# Setup environment file
cp .env.example .env
```

### Environment Variables

```bash
# API endpoint for backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
pnpm dev

# Or from root
pnpm --filter @gr8diy-web dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
# Production build
pnpm build

# Start production server
pnpm start
```

## Key Patterns

### Axios Configuration

Axios is configured with interceptors for automatic token handling:

```typescript
// lib/axios.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Request interceptor: Add Bearer token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
      const refreshToken = localStorage.getItem('refresh_token');
      const { data } = await axios.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });
      localStorage.setItem('access_token', data.access_token);
      // Retry original request
      return api.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

### Authentication Flow

1. **Login/Register**: Call API to get tokens
2. **Store Tokens**: Save to localStorage and Zustand store
3. **Auto-Refresh**: Axios interceptor handles 401 errors
4. **Logout**: Clear tokens and redirect

```typescript
// stores/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setAuth: (user, token) => set({ user, accessToken: token }),
      clearAuth: () => set({ user: null, accessToken: null }),
    }),
    { name: 'auth-storage' }
  )
);
```

### Server State with TanStack Query

```typescript
// hooks/use-users.ts
import { useQuery } from '@tanstack/react-query';
import { getUsers } from '@/services/api';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    staleTime: 60 * 1000, // 1 minute
  });
}
```

### Client State with Zustand

```typescript
// stores/ui.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
```

### UI Components with CVA

Components use `class-variance-authority` for variants:

```typescript
// components/ui/button.tsx
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'rounded-lg font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        outline: 'border border-input bg-background hover:bg-accent',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

interface ButtonProps extends VariantProps<typeof buttonVariants> {
  children: React.ReactNode;
}

export function Button({ variant, size, children }: ButtonProps) {
  return <button className={buttonVariants({ variant, size })}>{children}</button>;
}
```

## API Services

Centralized API service functions:

```typescript
// services/api.ts
import { api } from '@/lib/axios';

export const userService = {
  getProfile: () => api.get('/api/v1/users/me'),
  updateProfile: (data: UpdateUserDto) => api.patch('/api/v1/users/me', data),
};

export const authService = {
  login: (credentials: LoginDto) => api.post('/api/v1/auth/login', credentials),
  register: (data: RegisterDto) => api.post('/api/v1/auth/register', data),
  logout: () => api.post('/api/v1/auth/logout'),
  refresh: (token: string) => api.post('/api/v1/auth/refresh', { refresh_token: token }),
};
```

## App Router Patterns

### Route Structure

```
app/
├── (auth)/              # Auth group (no layout)
│   ├── login/
│   └── register/
├── (dashboard)/         # Dashboard group (with layout)
│   ├── layout.tsx       # Dashboard layout with nav
│   ├── page.tsx         # Dashboard home
│   └── settings/
├── layout.tsx           # Root layout
└── page.tsx             # Landing page
```

### Loading and Error States

```typescript
// app/dashboard/loading.tsx
export default function Loading() {
  return <div>Loading...</div>;
}

// app/dashboard/error.tsx
'use client';

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <p>{error.message}</p>
      <button onClick={reset}>Retry</button>
    </div>
  );
}
```

### Server Components vs Client Components

```typescript
// Server Component (default)
export default async function Page() {
  const data = await fetch('https://api.example.com/data').then(r => r.json());
  return <div>{data.title}</div>;
}

// Client Component
'use client';

export function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

## Styling

### Tailwind CSS

```tsx
<div className="flex items-center gap-4 rounded-lg bg-white p-4 shadow-md">
  <h2 className="text-lg font-semibold">Title</h2>
</div>
```

### Custom Components

```tsx
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

## TypeScript Types

Types are shared from `@gr8diy/types` package:

```typescript
import type { User, ApiResponse } from '@gr8diy/types';

const user: User = {
  id: '123',
  email: 'user@example.com',
  fullName: 'John Doe',
};
```

## Deployment

### Environment Variables

Set these in your deployment platform:

```bash
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### Build Command

```bash
pnpm build
```

### Start Command

```bash
pnpm start
```

## Troubleshooting

### API Connection Issues

1. Check `NEXT_PUBLIC_API_URL` is correct
2. Verify CORS is configured on backend
3. Check browser console for network errors

### State Not Persisting

1. Check localStorage is enabled in browser
2. Verify zustand persist middleware is configured
3. Check browser console for errors

### Styling Not Working

1. Ensure `tailwind.config.js` includes all paths
2. Check `globals.css` is imported in root layout
3. Verify PostCSS configuration

## License

MIT
