# 블록체인 (Blockchain)

Great DIY 프로토콜의 블록체인 인프라와 Web3 통합 아키텍처를 설명합니다.

---

## 1. 시스템 개요

### 1.1 아키텍처 개요

Great DIY는 **Monad L1** 체인을 기반으로 구축된 탈중앙화 자동매매 프로토콜입니다.

| 구성 요소 | 설명 |
|----------|------|
| **블록체인** | Monad L1 (고성능 EVM 호환 체인) |
| **정산 자산** | USDT0 (Monad L1 ERC20) |
| **네이티브 토큰** | G8D (Monad L1 ERC20) |
| **스마트 컨트랙트** | Solidity 구현 |

### 1.2 핵심 스마트 컨트랙트

```
┌─────────────────────────────────────────────────────────────┐
│                    Great DIY Protocol                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Access     │  │   Strategy   │  │    Follow    │      │
│  │   Control    │  │   Registry   │  │   Registry   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Decision   │  │  Settlement  │  │     Fee      │      │
│  │   History    │  │   Manager    │  │ Distributor  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Buyback     │  │     G8D      │  │    G8D       │      │
│  │  Treasury    │  │    Token     │  │   Staking    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 역할 (Roles)

| 역할 | 설명 |
|------|------|
| **ADMIN** | 전체 관리자 (글로벌 파라미터 변경) |
| **SETTLEMENT_OPERATOR** | 정산 실행 권한 |
| **VERIFIER** | 전략 검증 권한 |
| **BACKEND_RELAYER** | 백엔드 서버 트랜잭션 릴레이 |
| **TREASURY** | 바이백 재무 운영 권한 |

---

## 2. 데이터 기록 전략

### 2.1 온체인 데이터

**필수 데이터**: 스마트 컨트랙트에 영구 저장

| 데이터 | 저장소 | 설명 |
|--------|--------|------|
| **전략 정보** | StrategyRegistry | author, metadataURI, verificationHash, status |
| **구독 상태** | FollowRegistry | status, sinceDay, lastSettledDay |
| **결정 기록** | DecisionHistory | Merkle Root, timestamp, batchInfoHash |
| **정산 데이터** | SettlementManager | (user, strategyId, dayIndex) 단위 정산 |
| **수수료 분배** | FeeDistributor | platform, buyback, author 누적 금액 |
| **스테이킹** | G8DStaking | stakedBalance, tier, cooldown |

### 2.2 오프체인 데이터

**대용량 데이터**: IPFS/중앙화 서버 저장

| 데이터 | 저장소 | 설명 |
|--------|--------|------|
| **전략 메타데이터** | IPFS | 상세 설명, 파라미터, 백테스팅 결과 |
| **OHLCV 데이터** | DB | 거래소 원본 가격 데이터 |
| **주문 로그** | Backend | 개별 주문 내역 (압축하여 Merkle Root만 온체인) |
| **사용자 활동 로그** | Backend | 조회 기록, 설정 이력 등 |

### 2.3 Merkle Tree 기반 압축

개별 주문 로그는 오프체인에 저장하고, **Merkle Root만 온체인에 기록**:

```solidity
struct DayCommit {
    bytes32 rootHash;        // 해당 일자의 주문 Merkle Root
    uint256 timestamp;       // 커밋 시각
    bytes32 batchInfoHash;   // 배치 메타데이터 해시
}

mapping(uint256 => DayCommit) public dayCommits;  // dayIndex => DayCommit
```

---

## 3. Web3 통합

### 3.1 월렛 연결

| 지원 월렛 | 설명 |
|----------|------|
| **MetaMask** | Monad L1 네트워크 설정 |
| **WalletConnect** | 모바일 월렛 지원 |
| **Injected Providers** | 브라우저 확장 프로그램 |

### 3.2 네트워크 설정

```typescript
const MONAD_NETWORK = {
  chainId: '0x...',      // Monad L1 Chain ID
  chainName: 'Monad',
  nativeCurrency: {
    name: 'Monad',
    symbol: 'MONAD',
    decimals: 18
  },
  rpcUrls: ['https://rpc.monad.xyz'],
  blockExplorerUrls: ['https://explorer.monad.xyz']
}
```

### 3.3 프론트엔드 라이브러리

| 라이브러리 | 용도 |
|----------|------|
| **viem** | TypeScript 월렛 상호작용 |
| **wagmi** | React Hooks for Web3 |
| **ConnectKit** | 월렛 연결 UI |

---

## 4. 트랜잭션 관리

### 4.1 트랜잭션 유형

| 유형 | 설명 | 비용 부담 |
|------|------|----------|
| **사용자 트랜잭션** | 스테이킹, 언스테이킹, 전략 구독 | 사용자 (Native Token) |
| **백엔드 릴레이** | 정산 실행, 수수료 분배, 바이백 | 프로토콜 (Gasless) |

### 4.2 가스 최적화

**배치 처리**: 정산은 일일 단위로 배치 처리하여 가스 비용 절감

```solidity
function batchSettle(
    address[] calldata users,
    uint256[] calldata strategyIds,
    uint256[] calldata amounts
) external onlyRole(SETTLEMENT_OPERATOR) {
    for (uint i = 0; i < users.length; i++) {
        _createSettlement(users[i], strategyIds[i], amounts[i]);
    }
}
```

### 4.3 트랜잭션 상태 관리

| 상태 | 설명 |
|------|------|
| **Pending** | Mempool 대기 중 |
| **Confirmed** | 블록에 포함됨 |
| **Reverted** | 실행 실패 (Revert) |
| **Expired** | 시간 초과 (Nonce 문제 등) |

---

## 5. G8D 토큰 경제

### 5.1 토큰 사양

| 속성 | 값 |
|------|-----|
| **표준** | ERC20 |
| **체인** | Monad L1 |
| **총 공급량** | 고정 (추가 발행 없음) |
| **소각 가능** | Yes (burnable) |

### 5.2 토큰 용도

| 용도 | 설명 |
|------|------|
| **스테이킹** | Tier 혜택 (수수료 할인, 저작료 증가) |
| **거버넌스** | 향후 거버넌스 투표권 |
| **바이백** | 프로토콜 수익으로 G8D 매수 후 소각/LP |

### 5.3 Tier 시스템

| Tier | 최소 스테이킹 | 수수료 할인 | 팔로우 쿼타 | 저작료 증가 |
|------|--------------|-------------|--------------|-------------|
| **T0** | 0 | 없음 | 1개 | 0% |
| **T1** | 5,000 | 10% | 3개 | +5% |
| **T2** | 20,000 | 20% | 10개 | +10% |
| **T3** | 50,000 | 30% | 25개 | +25% |
| **T4** | 200,000 | 40% | 50개 | +50% |
| **T5** | 1,000,000 | 50% | 100개 | +100% |

### 5.4 스테이킹 정책

| 정책 | 내용 |
|------|------|
| **최소 보유기간** | 15일 |
| **언스테이킹 쿨다운** | 7일 |
| **Tier 스냅샷** | 정산 생성 시점 Tier 고정 |

---

## 6. 수수료 구조

### 6.1 기본 수수료

| 항목 | 비율 | 설명 |
|------|------|------|
| **기본 수수료** | 0.2% | 주문 금액 기준 |
| **Tier 할인** | 0~50% | 스테이킹 Tier에 따른 할인 |

### 6.2 수수료 분배

수수료는 다음과 같이 분배됩니다:

```
총 수수료
    ├── Platform Fee (플랫폼 운영)
    ├── Buyback Fee (G8D 바이백)
    └── Author Fee (저작자)
        ├── Base Author Fee (기본 10%)
        └── Tier Boost (Tier에 따른 증가)
```

### 6.3 바이백 메커니즘

1. **수수료 수취**: USDT0로 수수료 정산
2. **G8D 매수**: Uniswap 등 DEX를 통해 USDT0 → G8D 스왑
3. **분배**:
   - 일부 **소각** (Burn)
   - 일부 **Auto-LP** (유동성 공급)

---

## 7. Smart Contract 명세

### 7.1 AccessControl / Config

**역할**: 권한 관리 및 글로벌 파라미터 저장

```solidity
contract AccessControl is AccessControlManaged {
    // FeeConfig
    uint256 public baseFeeBps;          // 기본 수수료 200 bps (0.2%)
    uint256 public platformFeeBps;      // 플랫폼 몫
    uint256 public buybackFeeBps;       // 바이백 몫
    uint256 public baseAuthorFeeBps;    // 기본 저작료

    // SettlementConfig
    uint256 public settlementWindow;    // 정산 윈도우
    uint256 public expiryPeriod;        // 정산 만료 기간

    // StakingTierConfig
    uint256[] public tierThresholds;    // Tier별 스테이킹 기준
    uint256[] public tierDiscountBps;   // Tier별 할인율
}
```

### 7.2 StrategyRegistry

**역할**: 전략 등록 및 검증 정보 관리

```solidity
enum StrategyStatus {
    Draft, PendingReview, Verified,
    ActivationRequested, Active, Suspended, Rejected
}

struct Strategy {
    address author;
    string metadataURI;       // IPFS hash
    bytes32 verificationHash;
    uint256 verificationScore;
    StrategyStatus status;
    uint256 createdAt;
}
```

### 7.3 FollowRegistry

**역할**: 사용자별 구독(팔로우) 관리

```solidity
enum FollowStatus { None, Active, Paused, Stopped }

struct Follow {
    FollowStatus status;
    uint256 sinceDay;         // 구독 시작일
    uint256 lastSettledDay;   // 마지막 정산일
}

mapping(address => mapping(uint256 => Follow)) public follows;
// user => strategyId => Follow
```

### 7.4 DecisionHistory

**역할**: 일자별 주문 커밋 (Merkle Root)

```solidity
struct DayCommit {
    bytes32 rootHash;         // Merkle Root
    uint256 timestamp;
    bytes32 batchInfoHash;    // {count, totalVolume, etc.}
}

mapping(uint256 => mapping(uint256 => DayCommit)) public dayCommits;
// strategyId => dayIndex => DayCommit
```

### 7.5 SettlementManager

**역할**: 수수료 정산 데이터 관리

```solidity
enum SettlementStatus { Pending, Paid, Expired }

struct Settlement {
    address user;
    uint256 strategyId;
    uint256 dayIndex;
    uint256 feeAmount;
    uint256 discountBps;      // 적용된 할인율
    uint8 userTierSnapshot;   // 정산 시점 Tier
    SettlementStatus status;
}

// Primary Key: (user, strategyId, dayIndex)
```

### 7.6 FeeDistributor

**역할**: 수수료 분배 및 G8D 바이백 몫 누적

```solidity
struct DailyFeeDistribution {
    uint256 platformFee;      // 플랫폼 몫
    uint256 buybackFee;       // 바이백 재무로 이체
    uint256 authorFee;        // 저작자 분배
    uint256 dayIndex;
}

mapping(uint256 => DailyFeeDistribution) public dailyDistributions;
```

### 7.7 BuybackTreasury

**역할**: 바이백 실행 및 G8D 소각/LP 공급

```solidity
struct BuybackExecution {
    uint256 usdt0Spent;       // 사용된 USDT0
    uint256 g8bReceived;      // 획득한 G8D
    uint256 burnedAmount;     // 소각된 G8D
    uint256 lpAmount;         // LP에 공급된 G8D
    uint256 timestamp;
}

uint256 public burnRateBps;   // 소각 비율
uint256 public lpRateBps;     // LP 비율
```

### 7.8 G8DToken

**역할**: G8D ERC20 토큰

```solidity
contract G8DToken is ERC20, Burnable {
    constructor() ERC20("G8D Token", "G8D") {
        // 고정 공급량으로 초기 발행 (추가 발행 없음)
        _mint(msg.sender, TOTAL_SUPPLY);
    }
}
```

### 7.9 G8DStaking

**역할**: G8D 스테이킹 및 Tier 관리

```solidity
contract G8DStaking {
    IERC20 public g8b;

    mapping(address => uint256) public stakedBalance;
    mapping(address => uint256) public cooldownStart;
    mapping(address => uint256) public stakeTimestamp;

    uint256 public constant MIN_LOCK_PERIOD = 15 days;
    uint256 public constant COOLDOWN_PERIOD = 7 days;

    function stake(uint256 amount) external;
    function requestUnstake(uint256 amount) external;
    function withdraw() external;
    function tierOf(address user) public view returns (uint8);
}
```

---

## 8. 백엔드 연동

### 8.1 Backend Relayer 역할

**BACKEND_RELAYER** 권한을 가진 백엔드 서버가 다음 트랜잭션을 실행:

| 작업 | 설명 |
|------|------|
| **정산 생성** | 일일 정산 데이터 온체인 기록 |
| **수수료 분배** | FeeDistributor를 통해 분배 실행 |
| **바이백 실행** | BuybackTreasury에서 USDT0 → G8D 스왑 |

### 8.2 Gasless 경험

사용자는 백엔드 서버를 통해 **가스비 없이** 서비스 이용:

```
사용자 요청 → 백엔드 서버 → 스마트 컨트랙트 트랜잭션 실행
```

---

## 9. 오프체인 정산 시스템

### 9.1 하이브리드 아키텍처

Great DIY는 **온체인 + 오프체인 하이브리드** 정산 시스템을 사용합니다:

| 기능 | 온체인 | 오프체인 |
|------|--------|----------|
| **결제 수단** | USDT0 (블록체인) | 크레딧 (DB) |
| **스테이킹/Tier** | G8DStaking 컨트랙트 | 기본 Tier(T0) |
| **수수료 정산** | SettlementManager | settlements 테이블 |
| **저작권료** | FeeDistributor | author_royalties 테이블 |
| **팔로우 관리** | FollowRegistry | follows 테이블 |

### 9.2 오프체인 크레딧 시스템

**기본 동작 모드**: 개발/운영 모두 크레딧 기반으로 동작

```python
# 크레딧 기반 수수료 정산
def settle_execution(user_id, strategy_id, volume, tier):
    # 기본 수수료: 0.2%
    base_fee = volume * 0.002

    # Tier 할인 (오프체인에서도 적용)
    discount = get_tier_discount(tier)  # 0~50%
    final_fee = base_fee * (1 - discount)

    # 크레딧으로 차감
    credits_service.deduct(user_id, final_fee, 'EXECUTION')

    # 저작자 크레딧 지급 (10% + Tier Boost)
    author_fee = final_fee * (0.1 + get_tier_author_boost(author_tier))
    credits_service.add(author_id, author_fee, 'ROYALTY')

    return {
        'fee_credits': final_fee,
        'author_credits': author_fee,
        'platform_credits': final_fee - author_fee
    }
```

### 9.3 월별 저작권료 정산

**관리자 전용 기능**: 매월 저작권료 집계 및 수동 지급

```python
# 월별 저작권료 정산
def calculate_monthly_royalties(year, month):
    royalties = []

    for author in authors:
        # 해당 월 복제 횟수 집계
        clones = get_monthly_clones(author.id, year, month)

        # 총 수익 계산
        total_revenue = sum(c.price_credits for c in clones)

        # 저작권료 계산 (10%)
        royalty_amount = total_revenue * 0.1

        # author_royalties 테이블에 기록
        royalties.append({
            'author_id': author.id,
            'year': year,
            'month': month,
            'total_clones': len(clones),
            'total_revenue_credits': total_revenue,
            'royalty_amount_credits': royalty_amount,
            'status': 'PENDING'
        })

    return royalties
```

---

## 10. 블록체인 비활성화 모드

### 10.1 환경 설정

```bash
# .env
BLOCKCHAIN_ENABLED=false  # 블록체인 완전 비활성화
```

### 10.2 비활성화 모드 동작

| 기능 | 활성화 모드 | 비활성화 모드 |
|------|-----------|--------------|
| **월렛 연결** | MetaMask 등 연결 | 월렛 UI 숨김 |
| **스테이킹** | G8D 스테이킹 | 항상 T0 (기본) |
| **수수료 할인** | Tier 기반 0~50% | 0% (할인 없음) |
| **저작료 증가** | Tier 기반 0~100% | 기본 10%만 적용 |
| **팔로우** | 온체인 등록 | 오프체인 DB만 |
| **정산** | 온체인 Settlement | 오프체인 크레딧만 |
| **Web3 호출** | thirdweb SDK 사용 | 모두 건너뜀 |

### 10.3 코드 레벨 분기

```typescript
// lib/blockchain.ts
export const isBlockchainEnabled = () => {
  return process.env.NEXT_PUBLIC_BLOCKCHAIN_ENABLED === 'true';
}

// 훅에서 분기
export function useUserTier() {
  if (!isBlockchainEnabled()) {
    return { tier: 0, discount: 0 };  // 항상 T0
  }

  // 온체인 스테이킹 조회
  return useReadContract({...});
}
```

### 10.4 오픈소스 배려

**비활성화 모드 사용처**:
- 로컬 개발 (블록체인 없이 전체 기능 테스트)
- 오픈소스 사용자 (블록체인 설정 없이 배포 가능)
- CI/CD 파이프라인 (가스비 없이 테스트)

---

## 11. 상위/관련 문서

### 11.1 설계 문서

- **[design/0_프로토콜 개요.md](./design/0_프로토콜 개요.md)** - 프로토콜 전체 개요
- **[design/1_권한 및 글로벌 파라미터 관리.md](./design/1_권한 및 글로벌 파라미터 관리.md)** - AccessControl/Config
- **[design/2_전략 레지스트리 & 검증 정보.md](./design/2_전략 레지스트리 & 검증 정보.md)** - StrategyRegistry
- **[design/3_구독, 팔로우 관리.md](./design/3_구독, 팔로우 관리.md)** - FollowRegistry
- **[design/4_결정 기록, Commit Log.md](./design/4_결정 기록, Commit Log.md)** - DecisionHistory
- **[design/5_수수료 정산 데이터 관리.md](./design/5_수수료 정산 데이터 관리.md)** - SettlementManager
- **[design/6_수수료 분배 및 G8D 바이백 몫 누적.md](./design/6_수수료 분배 및 G8D 바이백 몫 누적.md)** - FeeDistributor
- **[design/7_바이백 실행 및 소각, LP 공급.md](./design/7_바이백 실행 및 소각, LP 공급.md)** - BuybackTreasury
- **[design/8_토큰 발행.md](./design/8_토큰 발행.md)** - G8DToken, VestingVault
- **[design/9_토큰 스테이킹 및 언스테이킹.md](./design/9_토큰 스테이킹 및 언스테이킹.md)** - G8DStaking

### 11.2 구현 명세 (specs)

- **[specs/smart-contracts.md](./specs/smart-contracts.md)** - 스마트 컨트랙트 구현 상세
- **[specs/web3-integration.md](./specs/web3-integration.md)** - Web3 프론트엔드 연동
- **[specs/settlement-system.md](./specs/settlement-system.md)** - 정산 시스템 상세
- **[specs/tokenomics.md](./specs/tokenomics.md)** - 토큰 경제 모델
- **[specs/merkle-tree.md](./specs/merkle-tree.md)** - Merkle Tree 데이터 압축

### 11.3 관련 시스템

- **[../03-strategy/](./../03-strategy/)** - 전략 관리 시스템
- **[../04-backtesting/](./../04-backtesting/)** - 백테스팅 시스템
- **[../02-authentication/](./../02-authentication/)** - 인증 시스템

---

*최종 업데이트: 2025-12-29*
