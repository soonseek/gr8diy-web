# 토큰 경제 (Tokenomics)

Great DIY 프로토콜의 G8D 토큰 경제 모델 상세 명세입니다.

---

## 1. 개요

### 1.1 G8D 토큰 개요

| 속성 | 값 |
|------|-----|
| **토큰 이름** | G8D Token |
| **심볼** | G8D |
| **표준** | ERC20 |
| **체인** | Monad L1 |
| **총 공급량** | 10억 G8D (고정) |
| **소각 가능** | Yes |
| **추가 발행** | 없음 |

### 1.2 토큰 용도

| 용도 | 설명 |
|------|------|
| **스테이킹** | Tier 혜택 획득 (수수료 할인, 저작료 증가) |
| **거버넌스** | 향후 거버넌스 투표권 |
| **바이백** | 프로토콜 수익으로 바이백 및 소각 |

---

## 2. 토큰 분배 (Token Distribution)

### 2.1 초기 분배

| 범주 | 비율 | 수량 | 잠금 기간 |
|------|------|------|-----------|
| **팀 & 어드바이저** | 20% | 2억 G8D | 12개월 클라임, 36개월 베스팅 |
| **투자자** | 15% | 1.5억 G8D | 6개월 클라임, 24개월 베스팅 |
| **에어드랍 & 마케팅** | 10% | 1억 G8D | 즉시 해제 |
| **생태계 펀드** | 25% | 2.5억 G8D | 6개월 클라임, 48개월 베스팅 |
| **바이백 & 유동성** | 30% | 3억 G8D | 프로토콜 수익으로 바이백 |

### 2.2 베스팅 스케줄

```solidity
// VestingVault.sol
struct VestingSchedule {
    uint256 totalAmount;     // 총 베스팅 금액
    uint256 startTime;       // 시작 시간
    uint256 cliffDuration;   // 클리프 기간
    uint256 duration;        // 총 베스팅 기간
    uint256 claimedAmount;   // 클레임된 금액
}

// 클레임 가능 금액 계산
function claimableAmount(address beneficiary) public view returns (uint256) {
    VestingSchedule memory schedule = vestingSchedules[beneficiary];

    uint256 elapsedTime = block.timestamp - schedule.startTime;

    // 클리프 기간 전에는 클레임 불가
    if (elapsedTime < schedule.cliffDuration) {
        return 0;
    }

    // 베스팅 기간 경과 비율
    uint256 vestedTime = elapsedTime - schedule.cliffDuration;
    uint256 totalVestingTime = schedule.duration - schedule.cliffDuration;

    uint256 vestedAmount = (schedule.totalAmount * vestedTime) / totalVestingTime;

    return vestedAmount - schedule.claimedAmount;
}
```

---

## 3. Tier 시스템

### 3.1 Tier별 혜택

| Tier | 최소 스테이킹 | 수수료 할인 | 팔로우 쿼타 | 저작료 증가 |
|------|--------------|-------------|--------------|-------------|
| **T0** | 0 | 0% | 1개 | 0% |
| **T1** | 5,000 | 10% | 3개 | +5% |
| **T2** | 20,000 | 20% | 10개 | +10% |
| **T3** | 50,000 | 30% | 25개 | +25% |
| **T4** | 200,000 | 40% | 50개 | +50% |
| **T5** | 1,000,000 | 50% | 100개 | +100% |

### 3.2 Tier 계산 로직

```solidity
// G8DStaking.sol
function tierOf(address user) public view returns (uint8) {
    uint256 balance = stakedBalance[user];

    // 역순 검색 (높은 Tier부터)
    for (uint8 i = 5; i > 0; i--) {
        if (balance >= tierThresholds[i]) {
            return i;
        }
    }

    return 0;  // T0
}
```

### 3.3 Tier 스냅샷

정산 생성 시점의 Tier를 스냅샷으로 저장하여 조작 방지:

```solidity
struct Settlement {
    // ...
    uint8 userTierSnapshot;    // 정산 시점 사용자 Tier
    uint8 authorTierSnapshot;  // 정산 시점 저작자 Tier
    // ...
}
```

---

## 4. 스테이킹 정책

### 4.1 최소 보유기간 (Minimum Lock Period)

| 항목 | 값 |
|------|-----|
| **기간** | 15일 |
| **목적** | 단기 스테이킹 후 즉시 언스테이킹 방지 |
| **Tier 유효성** | 최소 보유기간 충족 시 Tier 혜택 적용 |

```solidity
uint256 public constant MIN_LOCK_PERIOD = 15 days;

function stake(uint256 amount) external {
    // ...
    stakeTimestamp[msg.sender] = block.timestamp;
}

// 최소 보유기간 충족 여부 확인
function isLockPeriodMet(address user) external view returns (bool) {
    if (stakeTimestamp[user] == 0) return true;
    return block.timestamp >= stakeTimestamp[user] + MIN_LOCK_PERIOD;
}
```

### 4.2 언스테이킹 쿨다운 (Cooldown Period)

| 항목 | 값 |
|------|-----|
| **기간** | 7일 |
| **목적** | 정산 직전 Tier Boost 후 즉시 출금 방지 |

```solidity
uint256 public constant COOLDOWN_PERIOD = 7 days;

function requestUnstake(uint256 amount) external {
    require(
        block.timestamp >= stakeTimestamp[msg.sender] + MIN_LOCK_PERIOD,
        "Lock period not met"
    );

    cooldownStart[msg.sender] = block.timestamp;

    emit UnstakeRequested(msg.sender, amount, block.timestamp);
}

function withdraw() external {
    require(cooldownStart[msg.sender] > 0, "Not requested");
    require(
        block.timestamp >= cooldownStart[msg.sender] + COOLDOWN_PERIOD,
        "Cooldown not met"
    );

    uint256 amount = stakedBalance[msg.sender];
    stakedBalance[msg.sender] = 0;

    require(g8d.transfer(msg.sender, amount), "Transfer failed");
}
```

---

## 5. 바이백 메커니즘

### 5.1 바이백 흐름

```
프로토콜 수수료 (USDT0)
    ↓
FeeDistributor 분배
    ↓
BuybackTreasury 이체 (30%)
    ↓
DEX Swap (USDT0 → G8D)
    ↓
분배
    ├── 70% 소각 (Burn)
    └── 30% Auto-LP 공급
```

### 5.2 바이백 비율 설정

```solidity
// BuybackTreasury.sol
uint256 public burnRateBps = 7000;   // 70% 소각
uint256 public lpRateBps = 3000;     // 30% LP

function setBuybackRates(uint256 _burnRateBps, uint256 _lpRateBps)
    external onlyRole(ADMIN)
{
    require(_burnRateBps + _lpRateBps == 10000, "Invalid rates");
    burnRateBps = _burnRateBps;
    lpRateBps = _lpRateBps;

    emit BuybackRatesUpdated(_burnRateBps, _lpRateBps);
}
```

### 5.3 바이백 실행

```solidity
function executeBuyback(
    uint256 usdt0Amount,
    uint256 minG8dAmount,
    bytes calldata swapData
) external onlyRole(TREASURY) {
    require(usdt0.balanceOf(address(this)) >= usdt0Amount, "Insufficient USDT0");

    // USDT0 → G8D Swap (Uniswap V3)
    uint256 g8dBalanceBefore = g8d.balanceOf(address(this));

    usdt0.approve(address(swapRouter), usdt0Amount);
    swapRouter.exactInputSingle(
        ISwapRouter.ExactInputSingleParams({
            tokenIn: address(usdt0),
            tokenOut: address(g8d),
            fee: 3000,  // 0.3% pool
            recipient: address(this),
            deadline: block.timestamp,
            amountIn: usdt0Amount,
            amountOutMinimum: minG8dAmount,
            sqrtPriceLimitX96: 0
        })
    );

    uint256 g8dReceived = g8d.balanceOf(address(this)) - g8dBalanceBefore;

    // 소각 및 LP 분배
    uint256 burnAmount = (g8dReceived * burnRateBps) / 10000;
    uint256 lpAmount = g8dReceived - burnAmount;

    // G8D 소각
    if (burnAmount > 0) {
        G8DToken(address(g8d)).burn(burnAmount);
    }

    // LP 공급
    if (lpAmount > 0) {
        _provideLiquidity(lpAmount);
    }

    emit BuybackExecuted(
        executionId,
        usdt0Amount,
        g8dReceived,
        burnAmount,
        lpAmount
    );
}
```

---

## 6. 수수료 구조

### 6.1 기본 수수료

| 항목 | 개발서버 | 운영서버 |
|------|----------|----------|
| **기본 수수료** | 0.01% (10 bps) | 0.2% (200 bps) |
| **플랫폼 몫** | 0.005% (50 bps) | 0.1% (100 bps) |
| **바이백 몫** | 0.0025% (25 bps) | 0.05% (50 bps) |
| **저작자 몫** | 기본 10% | 기본 10% |

### 6.2 Tier별 할인

| Tier | 할인율 | 개발서버 최종 | 운영서버 최종 |
|------|--------|--------------|--------------|
| **T0** | 0% | 0.01% | 0.2% |
| **T1** | 10% | 0.009% | 0.18% |
| **T2** | 20% | 0.008% | 0.16% |
| **T3** | 30% | 0.007% | 0.14% |
| **T4** | 40% | 0.006% | 0.12% |
| **T5** | 50% | 0.005% | 0.10% |

### 6.3 저작료 분배

```
최종 수수료 (할인 적용 후)
    ├── Platform Fee (플랫폼)
    ├── Buyback Fee (바이백 재무)
    └── Author Fee (저작자)
        ├── Base Author Fee: 10%
        └── Tier Boost: 0% ~ 100%
```

| 저작자 Tier | Base | Boost | 총 저작료 |
|------------|------|-------|----------|
| **T0** | 10% | 0% | 10% |
| **T1** | 10% | 5% | 15% |
| **T2** | 10% | 10% | 20% |
| **T3** | 10% | 25% | 35% |
| **T4** | 10% | 50% | 60% |
| **T5** | 10% | 100% | 110% |

---

## 7. 환경별 설정

### 7.1 개발서버 (Development)

```typescript
// config/development.ts
export const tokenomicsConfig = {
  fees: {
    baseFeeBps: 100,       // 0.01%
    platformFeeBps: 50,    // 0.005%
    buybackFeeBps: 25,     // 0.0025%
    baseAuthorFeeBps: 1000, // 10%
  },
  staking: {
    minLockPeriod: 1 * 60 * 60 * 24, // 1일 (테스트용 단축)
    cooldownPeriod: 1 * 60 * 60 * 24, // 1일
  },
  tierThresholds: [
    0,
    5000 * 1e18,
    20000 * 1e18,
    50000 * 1e18,
    200000 * 1e18,
    1000000 * 1e18,
  ],
  buyback: {
    burnRateBps: 7000,  // 70%
    lpRateBps: 3000,   // 30%
  },
};
```

### 7.2 운영서버 (Production)

```typescript
// config/production.ts
export const tokenomicsConfig = {
  fees: {
    baseFeeBps: 200,       // 0.2%
    platformFeeBps: 100,   // 0.1%
    buybackFeeBps: 50,     // 0.05%
    baseAuthorFeeBps: 1000, // 10%
  },
  staking: {
    minLockPeriod: 15 * 60 * 60 * 24, // 15일
    cooldownPeriod: 7 * 60 * 60 * 24,  // 7일
  },
  tierThresholds: [
    0,
    5000 * 1e18,
    20000 * 1e18,
    50000 * 1e18,
    200000 * 1e18,
    1000000 * 1e18,
  ],
  buyback: {
    burnRateBps: 7000,  // 70%
    lpRateBps: 3000,   // 30%
  },
};
```

---

## 8. 토큰 순환 모델

### 8.1 순환 구조

```
┌─────────────────────────────────────────────────────────┐
│                   Great DIY Token Cycle                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   사용자 ──스테이킹──> G8DStaking ──Tier혜택──> 사용자  │
│      │                                              │   │
│      ├─수수료 할인                                  │   │
│      └─저작료 증가                                  │   │
│                                                    │    │
│   저작자 ──전략 제공──> Great DIY ──저작료──> 저작자     │
│                                    │                  │
│                                    ↓                  │
│                         프로토콜 수수료 (USDT0)          │
│                                    │                  │
│                                    ↓                  │
│                        FeeDistributor 분배              │
│                         │              │               │
│                Platform Fee    Buyback Fee              │
│                    │                 │                 │
│                    ↓                 ↓                 │
│                 운영비        BuybackTreasury            │
│                                     │                 │
│                                     ↓                 │
│                            USDT0 → G8D Swap              │
│                                     │                 │
│                    ┌────────────────┴────────────────┐ │
│                    ↓                                 ↓ │
│                  70% 소각                        30% LP │
│                 (Burn)                         (Auto-LP) │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 8.2 수요 창출 요인

| 요인 | 설명 | 효과 |
|------|------|------|
| **스테이킹 수요** | Tier 혜택 (할인, 쿼타) | 토큰 락업 |
| **저작자 보상** | Tier가 높을수록 저작료 증가 | 저작자 스테이킹 유도 |
| **바이백** | 수익의 30%를 바이백 | 지속적인 매수 수요 |
| **소각** | 70% 소각으로 공급 감소 | 디플레이션 압력 |

---

## 9. 지표 대시보드

### 9.1 토큰 관련 지표

```typescript
// hooks/useTokenMetrics.ts
"use client";

import { useReadContract } from "thirdweb/react";
import { g8dTokenContract, g8dStakingContract, buybackTreasuryContract } from "@/lib/contracts";

export function useTokenMetrics() {
  // 총 공급량 (고정)
  const totalSupply = 1_000_000_000 * 1e18;

  // 스테이킹总量
  const { data: totalStaked } = useReadContract({
    contract: g8dStakingContract,
    method: "getTotalStaked",
    params: [],
  });

  // 스테이킹 비율
  const stakingRatio = totalStaked ? Number(totalStaked) / totalSupply : 0;

  // 바이백 누적량
  const { data: totalBuyback } = useReadContract({
    contract: buybackTreasuryContract,
    method: "getTotalBuyback",
    params: [],
  });

  // 소각 누적량
  const { data: totalBurned } = useReadContract({
    contract: g8dTokenContract,
    method: "getTotalBurned",
    params: [],
  });

  // 순환 공급량 = 총 공급 - 소각 - 스테이킹
  const circulatingSupply = totalSupply - (totalBurned || 0n) - (totalStaked || 0n);

  return {
    totalSupply,
    totalStaked: totalStaked || 0n,
    stakingRatio,
    totalBuyback: totalBuyback || 0n,
    totalBurned: totalBurned || 0n,
    circulatingSupply,
  };
}
```

### 9.2 대시보드 UI

```typescript
// components/token/TokenDashboard.tsx
"use client";

import { useTokenMetrics } from "@/hooks/useTokenMetrics";

export function TokenDashboard() {
  const metrics = useTokenMetrics();

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">G8D Token Metrics</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-blue-50 rounded">
          <p className="text-sm text-gray-600">Total Supply</p>
          <p className="text-2xl font-bold">
            {(Number(metrics.totalSupply) / 1e18).toLocaleString()} G8D
          </p>
        </div>

        <div className="p-4 bg-green-50 rounded">
          <p className="text-sm text-gray-600">Total Staked</p>
          <p className="text-2xl font-bold">
            {(Number(metrics.totalStaked) / 1e18).toLocaleString()} G8D
          </p>
          <p className="text-sm text-gray-500">
            Staking Ratio: {(metrics.stakingRatio * 100).toFixed(2)}%
          </p>
        </div>

        <div className="p-4 bg-red-50 rounded">
          <p className="text-sm text-gray-600">Total Burned</p>
          <p className="text-2xl font-bold">
            {(Number(metrics.totalBurned) / 1e18).toLocaleString()} G8D
          </p>
        </div>

        <div className="p-4 bg-purple-50 rounded">
          <p className="text-sm text-gray-600">Circulating Supply</p>
          <p className="text-2xl font-bold">
            {(Number(metrics.circulatingSupply) / 1e18).toLocaleString()} G8D
          </p>
        </div>
      </div>
    </div>
  );
}
```

---

## 10. 스마트 컨트랙트

### 10.1 G8DToken (ERC20 + Burnable)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";

contract G8DToken is ERC20, ERC20Burnable {
    uint256 public constant TOTAL_SUPPLY = 1_000_000_000 * 10**18;  // 10억
    uint256 public totalBurned;

    constructor() ERC20("G8D Token", "G8D") {
        _mint(msg.sender, TOTAL_SUPPLY);
    }

    function burn(uint256 amount) public override {
        super.burn(amount);
        totalBurned += amount;
        emit TokensBurned(msg.sender, amount);
    }

    event TokensBurned(address indexed burner, uint256 amount);
}
```

### 10.2 G8DStaking (Tier 관리)

```solidity
contract G8DStaking is GreatDIYAccessControl {
    IERC20 public g8d;

    mapping(address => uint256) public stakedBalance;
    mapping(address => uint256) public cooldownStart;
    mapping(address => uint256) public stakeTimestamp;

    uint256 public constant MIN_LOCK_PERIOD = 15 days;
    uint256 public constant COOLDOWN_PERIOD = 7 days;

    uint256[] public tierThresholds;
    uint256 public totalStaked;

    // ... (전체 코드는 smart-contracts.md 참조)
}
```

---

## 11. 상위/관련 문서

- **[../index.md](../index.md)** - 블록체인 개요
- **[./smart-contracts.md](./smart-contracts.md)** - 스마트 컨트랙트 명세
- **[./settlement-system.md](./settlement-system.md)** - 정산 시스템
- **[../design/8_토큰 발행.md](../design/8_토큰 발행.md)** - 토큰 설계
- **[../design/9_토큰 스테이킹 및 언스테이킹.md](../design/9_토큰 스테이킹 및 언스테이킹.md)** - 스테이킹 설계

---

*최종 업데이트: 2025-12-29*
