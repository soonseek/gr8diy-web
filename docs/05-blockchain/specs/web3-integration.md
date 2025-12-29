# Web3 통합 (Web3 Integration)

Great DIY 프로토콜의 Web3 프론트엔드 연동 상세 명세입니다. **thirdweb**을 사용하여 Monad L1 체인과 연동합니다.

---

## 1. 개요

### 1.1 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              thirdweb SDK                          │   │
│  │  ├─ useActiveAccount    (지갑 연결)                │   │
│  │  ├─ useActiveWalletChain   (체인 확인)            │   │
│  │  └─ useSendTransaction      (트랜잭션 전송)       │   │
│  └─────────────────────────────────────────────────────┘   │
│                              ↓                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Smart Contracts (Monad L1)               │   │
│  │  ├─ G8DStaking          (스테이킹)                 │   │
│  │  ├─ StrategyRegistry    (전략 등록)                │   │
│  │  └─ SettlementManager   (정산)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| **thirdweb** | 최신 | Web3 SDK |
| **Next.js** | 14 | 프론트엔드 프레임워크 |
| **TypeScript** | 5 | 타입 안전성 |
| **React Query** | 5 | 서버 상태 관리 |
| **Zustand** | 4 | 클라이언트 상태 관리 |

---

## 2. thirdweb 설정

### 2.1 프로젝트 설정

```bash
# thirdweb SDK 설치
pnpm add thirdweb @thirdweb-dev/react @thirdweb-dev/sdk
```

### 2.2 Monad L1 네트워크 설정

```typescript
// libs/thirdweb.ts
import { createThirdwebClient, getContract } from "thirdweb";
import { defineChain } from "thirdweb/chains";

// Monad L1 체인 정의
export const monad = defineChain({
  id: 43114, // Monad L1 Chain ID (예시)
  name: "Monad",
  nativeCurrency: {
    name: "Monad",
    symbol: "MONAD",
    decimals: 18,
  },
  rpcUrls: {
    default: {
      http: ["https://rpc.monad.xyz"],
    },
  },
  blockExplorers: {
    default: {
      name: "Monad Explorer",
      url: "https://explorer.monad.xyz",
    },
  },
});

// Thirdweb 클라이언트 생성
export const thirdwebClient = createThirdwebClient({
  clientId: process.env.NEXT_PUBLIC_THIRDWEB_CLIENT_ID!,
  secretKey: process.env.THIRDWEB_SECRET_KEY,
});
```

### 2.3 환경 변수

```bash
# .env.local
NEXT_PUBLIC_THIRDWEB_CLIENT_ID=your_thirdweb_client_id
THIRDWEB_SECRET_KEY=your_thirdweb_secret_key
NEXT_PUBLIC_MONAD_CHAIN_ID=43114
```

---

## 3. 지갑 연결 (Wallet Connection)

### 3.1 ThirdwebProvider 설정

```typescript
// app/providers.tsx
"use client";

import { ThirdwebProvider } from "thirdweb/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { thirdwebClient } from "@/lib/thirdweb";

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThirdwebProvider>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </ThirdwebProvider>
  );
}
```

### 3.2 지갑 연결 컴포넌트

```typescript
// components/wallet/ConnectWallet.tsx
"use client";

import { useActiveAccount, useConnect, useDisconnect } from "thirdweb/react";
import { client } from "@/lib/thirdweb";
import { createWallet } from "thirdweb/wallets";

export function ConnectWallet() {
  const account = useActiveAccount();
  const { connect, isConnecting } = useConnect();
  const { disconnect } = useDisconnect();

  if (account) {
    return (
      <div className="flex items-center gap-4">
        <span className="text-sm">
          {account.address.slice(0, 6)}...{account.address.slice(-4)}
        </span>
        <button
          onClick={() => disconnect()}
          className="px-4 py-2 bg-red-500 text-white rounded-lg"
        >
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => connect(createWallet("io.metamask"))}
      disabled={isConnecting}
      className="px-4 py-2 bg-blue-500 text-white rounded-lg"
    >
      {isConnecting ? "Connecting..." : "Connect Wallet"}
    </button>
  );
}
```

### 3.3 체인 전환 (Switch to Monad)

```typescript
// hooks/useSwitchChain.ts
"use client";

import { useActiveWalletChain, useSwitchChain } from "thirdweb/react";
import { monad } from "@/lib/thirdweb";

export function useEnsureMonadChain() {
  const currentChain = useActiveWalletChain();
  const { switchChain, isSwitching } = useSwitchChain();

  const ensureMonad = async () => {
    if (currentChain?.id !== monad.id) {
      await switchChain(monad);
    }
  };

  return {
    isCorrectChain: currentChain?.id === monad.id,
    ensureMonad,
    isSwitching,
  };
}

// 사용 예시
function MyComponent() {
  const { isCorrectChain, ensureMonad } = useEnsureMonadChain();

  const handleClick = async () => {
    if (!isCorrectChain) {
      await ensureMonad();
    }
    // 이후 로직...
  };

  return <button onClick={handleClick}>Action</button>;
}
```

---

## 4. 컨트랙트 연동

### 4.1 컨트랙트 인스턴스 생성

```typescript
// lib/contracts.ts
import { getContract } from "thirdweb";
import { thirdwebClient, monad } from "./thirdweb";

// 컨트랙트 주소 (환경 변수 또는 config)
const G8D_TOKEN_ADDRESS = "0x...";
const G8D_STAKING_ADDRESS = "0x...";
const STRATEGY_REGISTRY_ADDRESS = "0x...";
const SETTLEMENT_MANAGER_ADDRESS = "0x...";

export const g8dTokenContract = getContract({
  client: thirdwebClient,
  chain: monad,
  address: G8D_TOKEN_ADDRESS,
});

export const g8dStakingContract = getContract({
  client: thirdwebClient,
  chain: monad,
  address: G8D_STAKING_ADDRESS,
});

export const strategyRegistryContract = getContract({
  client: thirdwebClient,
  chain: monad,
  address: STRATEGY_REGISTRY_ADDRESS,
});

export const settlementManagerContract = getContract({
  client: thirdwebClient,
  chain: monad,
  address: SETTLEMENT_MANAGER_ADDRESS,
});
```

### 4.2 TypeScript 타입 정의

```typescript
// types/contracts.ts
import { prepareContractCall } from "thirdweb";

// G8DStaking ABI (일부)
export const G8D_STAKING_ABI = [
  {
    type: "function",
    name: "stake",
    inputs: [{ name: "amount", type: "uint256" }],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "requestUnstake",
    inputs: [{ name: "amount", type: "uint256" }],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "withdraw",
    inputs: [],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "tierOf",
    inputs: [{ name: "user", type: "address" }],
    outputs: [{ name: "", type: "uint8" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "getStakedBalance",
    inputs: [{ name: "user", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
] as const;

// StrategyRegistry ABI (일부)
export const STRATEGY_REGISTRY_ABI = [
  {
    type: "function",
    name: "createStrategy",
    inputs: [{ name: "metadataURI", type: "string" }],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "getStrategy",
    inputs: [{ name: "strategyId", type: "uint256" }],
    outputs: [{ name: "", type: "tuple" }],
    stateMutability: "view",
  },
] as const;

// Enums
export enum StrategyStatus {
  Draft = 0,
  PendingReview = 1,
  Verified = 2,
  ActivationRequested = 3,
  Active = 4,
  Suspended = 5,
  Rejected = 6,
}

export enum FollowStatus {
  None = 0,
  Active = 1,
  Paused = 2,
  Stopped = 3,
}

// Structs
export interface Strategy {
  id: bigint;
  author: string;
  metadataURI: string;
  verificationHash: string;
  verificationScore: bigint;
  status: StrategyStatus;
  createdAt: bigint;
  updatedAt: bigint;
}

export interface Follow {
  status: FollowStatus;
  sinceDay: bigint;
  lastSettledDay: bigint;
}
```

---

## 5. G8D 스테이킹 (Staking)

### 5.1 스테이킹 Hook

```typescript
// hooks/useG8DStaking.ts
"use client";

import { useReadContract, useSendTransaction } from "thirdweb/react";
import { g8dStakingContract } from "@/lib/contracts";
import { G8D_STAKING_ABI } from "@/types/contracts";
import { prepareContractCall } from "thirdweb";
import { useState } from "react";

export function useG8DStaking(account?: string) {
  const [isStaking, setIsStaking] = useState(false);
  const [isUnstaking, setIsUnstaking] = useState(false);
  const [isWithdrawing, setIsWithdrawing] = useState(false);

  // 스테이킹 잔액 조회
  const { data: stakedBalance, refetch: refetchBalance } = useReadContract({
    contract: g8dStakingContract,
    method: "getStakedBalance",
    params: account ? [account as unknown as `0x${string}`] : undefined,
    abi: G8D_STAKING_ABI,
  });

  // Tier 조회
  const { data: tier } = useReadContract({
    contract: g8dStakingContract,
    method: "tierOf",
    params: account ? [account as unknown as `0x${string}`] : undefined,
    abi: G8D_STAKING_ABI,
  });

  // 스테이킹
  const { mutateAsync: sendTransaction } = useSendTransaction();

  const stake = async (amount: bigint) => {
    if (!account) throw new Error("Wallet not connected");

    setIsStaking(true);
    try {
      const transaction = prepareContractCall({
        contract: g8dStakingContract,
        method: "stake",
        params: [amount],
        abi: G8D_STAKING_ABI,
      });

      await sendTransaction(transaction);
      await refetchBalance();
    } finally {
      setIsStaking(false);
    }
  };

  // 언스테이킹 요청
  const requestUnstake = async (amount: bigint) => {
    if (!account) throw new Error("Wallet not connected");

    setIsUnstaking(true);
    try {
      const transaction = prepareContractCall({
        contract: g8dStakingContract,
        method: "requestUnstake",
        params: [amount],
        abi: G8D_STAKING_ABI,
      });

      await sendTransaction(transaction);
    } finally {
      setIsUnstaking(false);
    }
  };

  // 출금
  const withdraw = async () => {
    if (!account) throw new Error("Wallet not connected");

    setIsWithdrawing(true);
    try {
      const transaction = prepareContractCall({
        contract: g8dStakingContract,
        method: "withdraw",
        params: [],
        abi: G8D_STAKING_ABI,
      });

      await sendTransaction(transaction);
      await refetchBalance();
    } finally {
      setIsWithdrawing(false);
    }
  };

  return {
    stakedBalance: stakedBalance || 0n,
    tier: tier || 0,
    stake,
    requestUnstake,
    withdraw,
    isStaking,
    isUnstaking,
    isWithdrawing,
    refetchBalance,
  };
}
```

### 5.2 스테이킹 UI 컴포넌트

```typescript
// components/staking/StakingPanel.tsx
"use client";

import { useG8DStaking } from "@/hooks/useG8DStaking";
import { useActiveAccount } from "thirdweb/react";
import { parseUnits } from "viem";
import { useState } from "react";

export function StakingPanel() {
  const account = useActiveAccount();
  const { stakedBalance, tier, stake, requestUnstake, withdraw, isStaking, isUnstaking, isWithdrawing } =
    useG8DStaking(account?.address);

  const [amount, setAmount] = useState("");

  const handleStake = async () => {
    if (!amount) return;

    const amountInWei = parseUnits(amount, 18);
    await stake(amountInWei);
    setAmount("");
  };

  const handleRequestUnstake = async () => {
    if (!amount) return;

    const amountInWei = parseUnits(amount, 18);
    await requestUnstake(amountInWei);
    setAmount("");
  };

  const tierLabels = ["T0", "T1", "T2", "T3", "T4", "T5"];

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">G8D Staking</h2>

      {/* 현재 스테이킹 정보 */}
      <div className="mb-6 p-4 bg-gray-100 rounded">
        <p className="text-lg">
          Staked: {(Number(stakedBalance) / 1e18).toFixed(2)} G8D
        </p>
        <p className="text-lg">
          Tier: {tierLabels[tier]}
        </p>
      </div>

      {/* 스테이킹 입력 */}
      <div className="mb-4">
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Amount (G8D)"
          className="w-full p-2 border rounded"
        />
      </div>

      {/* 버튼들 */}
      <div className="flex gap-2">
        <button
          onClick={handleStake}
          disabled={isStaking || !amount}
          className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
        >
          {isStaking ? "Staking..." : "Stake"}
        </button>

        <button
          onClick={handleRequestUnstake}
          disabled={isUnstaking || !amount}
          className="px-4 py-2 bg-yellow-500 text-white rounded disabled:opacity-50"
        >
          {isUnstaking ? "Requesting..." : "Request Unstake"}
        </button>

        <button
          onClick={withdraw}
          disabled={isWithdrawing}
          className="px-4 py-2 bg-red-500 text-white rounded disabled:opacity-50"
        >
          {isWithdrawing ? "Withdrawing..." : "Withdraw"}
        </button>
      </div>
    </div>
  );
}
```

---

## 6. 전략 관리 (Strategy Management)

### 6.1 전략 생성 Hook

```typescript
// hooks/useStrategyRegistry.ts
"use client";

import { useReadContract, useSendTransaction } from "thirdweb/react";
import { strategyRegistryContract } from "@/lib/contracts";
import { STRATEGY_REGISTRY_ABI, Strategy } from "@/types/contracts";
import { prepareContractCall } from "thirdweb";

export function useStrategyRegistry() {
  const { mutateAsync: sendTransaction } = useSendTransaction();

  // 전략 생성
  const createStrategy = async (metadataURI: string) => {
    const transaction = prepareContractCall({
      contract: strategyRegistryContract,
      method: "createStrategy",
      params: [metadataURI],
      abi: STRATEGY_REGISTRY_ABI,
    });

    const result = await sendTransaction(transaction);

    // receipt에서 strategyId 추출
    if (result) {
      // strategyId는 이벤트에서 가져오거나, 트랜잭션 결과에서 확인
      console.log("Strategy created:", result);
    }

    return result;
  };

  // 전략 조회
  const getStrategy = async (strategyId: bigint): Promise<Strategy> => {
    const result = await useReadContract({
      contract: strategyRegistryContract,
      method: "getStrategy",
      params: [strategyId],
      abi: STRATEGY_REGISTRY_ABI,
    });

    return result as unknown as Strategy;
  };

  // 활성화된 전략 목록
  const { data: activeStrategies } = useReadContract({
    contract: strategyRegistryContract,
    method: "getActiveStrategies",
    params: [],
    abi: STRATEGY_REGISTRY_ABI,
  });

  return {
    createStrategy,
    getStrategy,
    activeStrategies: activeStrategies || [],
  };
}
```

### 6.2 전략 생성 UI

```typescript
// components/strategy/CreateStrategyForm.tsx
"use client";

import { useStrategyRegistry } from "@/hooks/useStrategyRegistry";
import { useState } from "react";

export function CreateStrategyForm() {
  const { createStrategy } = useStrategyRegistry();
  const [metadataURI, setMetadataURI] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!metadataURI) return;

    setIsCreating(true);
    try {
      await createStrategy(metadataURI);
      alert("Strategy created successfully!");
      setMetadataURI("");
    } catch (error) {
      console.error("Failed to create strategy:", error);
      alert("Failed to create strategy");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">Create Strategy</h2>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Metadata URI (IPFS)
        </label>
        <input
          type="text"
          value={metadataURI}
          onChange={(e) => setMetadataURI(e.target.value)}
          placeholder="ipfs://Qm..."
          className="w-full p-2 border rounded"
          required
        />
      </div>

      <button
        type="submit"
        disabled={isCreating || !metadataURI}
        className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
      >
        {isCreating ? "Creating..." : "Create Strategy"}
      </button>
    </form>
  );
}
```

---

## 7. 트랜잭션 관리

### 7.1 트랜잭션 상태 추적

```typescript
// hooks/useTransaction.ts
"use client";

import { useSendTransaction } from "thirdweb/react";
import { prepareContractCall } from "thirdweb";
import { BaseTransaction } from "thirdweb/wallets";
import { useState } from "react";

type TransactionStatus = "idle" | "pending" | "success" | "error";

export function useTransaction() {
  const { mutateAsync: sendTransaction } = useSendTransaction();
  const [status, setStatus] = useState<TransactionStatus>("idle");
  const [hash, setHash] = useState<string | undefined>();
  const [error, setError] = useState<Error | undefined>();

  const executeTransaction = async (transaction: BaseTransaction) => {
    setStatus("pending");
    setHash(undefined);
    setError(undefined);

    try {
      const result = await sendTransaction(transaction);

      if (result) {
        setHash(result.transactionHash || undefined);
        setStatus("success");
      }

      return result;
    } catch (err) {
      const error = err as Error;
      setError(error);
      setStatus("error");
      throw error;
    }
  };

  return {
    status,
    hash,
    error,
    executeTransaction,
    isPending: status === "pending",
  };
}
```

### 7.2 트랜잭션 알림

```typescript
// components/transaction/TransactionNotification.tsx
"use client";

import { useTransaction } from "@/hooks/useTransaction";
import { useEffect } from "react";
import { toast } from "sonner";

export function TransactionNotification({ status, hash, error }: {
  status: "idle" | "pending" | "success" | "error";
  hash?: string;
  error?: Error;
}) {
  useEffect(() => {
    if (status === "pending") {
      toast.loading("Transaction pending...");
    } else if (status === "success") {
      toast.success("Transaction successful!", {
        description: hash ? `Hash: ${hash.slice(0, 10)}...` : undefined,
      });
    } else if (status === "error") {
      toast.error("Transaction failed", {
        description: error?.message,
      });
    }
  }, [status, hash, error]);

  return null;
}
```

---

## 8. React Query 통합

### 8.1 컨트랙트 데이터 Query

```typescript
// hooks/useContractData.ts
"use client";

import { useReadContract } from "thirdweb/react";
import { g8dStakingContract } from "@/lib/contracts";
import { G8D_STAKING_ABI } from "@/types/contracts";
import { useQueryClient } from "@tanstack/react-query";

export function useContractData(account?: string) {
  const queryClient = useQueryClient();

  // 스테이킹 잔액
  const { data: stakedBalance } = useReadContract({
    contract: g8dStakingContract,
    method: "getStakedBalance",
    params: account ? [account as unknown as `0x${string}`] : undefined,
    abi: G8D_STAKING_ABI,
    queryOptions: {
      enabled: !!account,
      refetchInterval: 10000, // 10초마다 리프레시
    },
  });

  // 수동 리프레시
  const refetch = () => {
    queryClient.refetchQueries({ queryKey: ["g8dStaking"] });
  };

  return {
    stakedBalance: stakedBalance || 0n,
    refetch,
  };
}
```

### 8.2 Mutation Wrapper

```typescript
// hooks/useContractMutation.ts
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSendTransaction } from "thirdweb/react";
import { prepareContractCall } from "thirdweb";
import { BaseTransaction } from "thirdweb/wallets";
import { toast } from "sonner";

export function useContractMutation() {
  const { mutateAsync: sendTransaction } = useSendTransaction();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (transaction: BaseTransaction) => {
      return await sendTransaction(transaction);
    },
    onSuccess: () => {
      toast.success("Transaction successful");
      queryClient.invalidateQueries();
    },
    onError: (error: Error) => {
      toast.error(`Transaction failed: ${error.message}`);
    },
  });

  return mutation;
}
```

---

## 9. Zustand Store

### 9.1 Web3 Store

```typescript
// stores/web3Store.ts
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface Web3State {
  isConnected: boolean;
  address: string | null;
  chainId: number | null;
  tier: number;
  stakedBalance: bigint;

  setConnected: (connected: boolean) => void;
  setAddress: (address: string | null) => void;
  setChainId: (chainId: number | null) => void;
  setTier: (tier: number) => void;
  setStakedBalance: (balance: bigint) => void;
}

export const useWeb3Store = create<Web3State>()(
  devtools(
    persist(
      (set) => ({
        isConnected: false,
        address: null,
        chainId: null,
        tier: 0,
        stakedBalance: 0n,

        setConnected: (connected) => set({ isConnected: connected }),
        setAddress: (address) => set({ address }),
        setChainId: (chainId) => set({ chainId }),
        setTier: (tier) => set({ tier }),
        setStakedBalance: (balance) => set({ stakedBalance: balance }),
      }),
      {
        name: "web3-storage",
      }
    )
  )
);
```

### 9.2 Store 사용

```typescript
// components/staking/TierDisplay.tsx
"use client";

import { useWeb3Store } from "@/stores/web3Store";

export function TierDisplay() {
  const { tier, stakedBalance } = useWeb3Store();

  const tierLabels = ["T0", "T1", "T2", "T3", "T4", "T5"];

  return (
    <div className="p-4 bg-blue-100 rounded">
      <p className="text-lg font-semibold">
        Your Tier: {tierLabels[tier]}
      </p>
      <p className="text-sm">
        Staked: {(Number(stakedBalance) / 1e18).toFixed(2)} G8D
      </p>
    </div>
  );
}
```

---

## 10. 에러 처리

### 10.1 일반적인 Web3 에러

```typescript
// utils/web3Errors.ts
export class Web3Error extends Error {
  constructor(
    message: string,
    public code?: number,
    public data?: unknown
  ) {
    super(message);
    this.name = "Web3Error";
  }
}

export function handleWeb3Error(error: unknown): string {
  if (error instanceof Web3Error) {
    switch (error.code) {
      case 4001:
        return "Transaction rejected by user";
      case 4100:
        return "Unauthorized account";
      case -32603:
        return "Internal JSON-RPC error";
      default:
        return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unknown error occurred";
}
```

### 10.2 에러 바운더리

```typescript
// components/ErrorBoundary.tsx
"use client";

import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class Web3ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-100 text-red-700 rounded">
          <h2 className="text-lg font-bold">Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 11. 배포 시 고려사항

### 11.1 성능 최적화

| 항목 | 설명 |
|------|------|
| **Polling 간격** | 중요 데이터: 10초, 덜 중요: 30초~1분 |
| **Cache 설정** | staleTime: 60s, gcTime: 5분 |
| **Batch 요청** | Multicall 사용하여 여러 조회를 하나의 트랜잭션으로 |

### 11.2 보안

| 항목 | 설명 |
|------|------|
| **RPC Endpoint** | thirdweb의 관리형 RPC 사용 |
| **Private Key** | 절대 프론트엔드에 노출하지 않음 |
| **사용자 권한** | 최소한의 권한만 요청 (approve 등) |

---

## 12. 상위/관련 문서

- **[../index.md](../index.md)** - 블록체인 개요
- **[./smart-contracts.md](./smart-contracts.md)** - 스마트 컨트랙트 명세
- **[../design/](../design/)** - 프로토콜 설계 문서

---

*최종 업데이트: 2025-12-29*
