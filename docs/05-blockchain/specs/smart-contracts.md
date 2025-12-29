# 스마트 컨트랙트 (Smart Contracts)

GreatDIY 프로토콜의 스마트 컨트랙트 구현 상세 명세입니다.

---

## 1. 컨트랙트 개요

### 1.1 컨트랙트 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    GreatDIY Protocol                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Core Layer: AccessControl, Config                          │
│  ├─ StrategyRegistry, FollowRegistry                        │
│  ├─ DecisionHistory, SettlementManager                      │
│  └─ FeeDistributor, BuybackTreasury                         │
│                                                             │
│  Token Layer: G8DToken, G8DStaking                          │
│  └─ VestingVault                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 의존성 라이브러리

| 라이브러리 | 버전 | 용도 |
|----------|------|------|
| **OpenZeppelin** | ^5.0 | ERC20, AccessControl, Burnable |
| **Solidity** | ^0.8.20 | 컨트랙트 언어 |

---

## 2. AccessControl / Config

### 2.1 개요

권한 관리와 글로벌 파라미터를 관리하는 중앙 설정 컨트랙트입니다.

### 2.2 데이터 구조

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

contract GreatDIYAccessControl is AccessControl {
    // Roles
    bytes32 public constant ADMIN = keccak256("ADMIN");
    bytes32 public constant SETTLEMENT_OPERATOR = keccak256("SETTLEMENT_OPERATOR");
    bytes32 public constant VERIFIER = keccak256("VERIFIER");
    bytes32 public constant BACKEND_RELAYER = keccak256("BACKEND_RELAYER");
    bytes32 public constant TREASURY = keccak256("TREASURY");

    // FeeConfig
    uint256 public baseFeeBps;          // 200 bps (0.2%)
    uint256 public platformFeeBps;      // 100 bps (0.1%)
    uint256 public buybackFeeBps;       // 50 bps (0.05%)
    uint256 public baseAuthorFeeBps;    // 1000 bps (10%)

    // SettlementConfig
    uint256 public settlementWindow;    // 1 day
    uint256 public expiryPeriod;        // 7 days

    // StakingTierConfig
    uint256[] public tierThresholds;    // [0, 5000, 20000, 50000, 200000, 1000000]
    uint256[] public tierDiscountBps;   // [0, 20, 40, 60, 80, 100] (0%, 10%, 20%, 30%, 40%, 50%)
    uint256[] public tierAuthorBoostBps; // [0, 50, 100, 250, 500, 1000] (0%, 5%, 10%, 25%, 50%, 100%)

    // uint256[] public followQuota;       // [1, 3, 10, 25, 50, 100]
}
```

### 2.3 함수

```solidity
// constructor
constructor() {
    _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    _grantRole(ADMIN, msg.sender);

    // 초기값 설정
    baseFeeBps = 200;          // 0.2%
    platformFeeBps = 100;      // 0.1%
    buybackFeeBps = 50;        // 0.05%
    baseAuthorFeeBps = 1000;   // 10%

    settlementWindow = 1 days;
    expiryPeriod = 7 days;

    // T0 ~ T5
    tierThresholds = [0, 5000 ether, 20000 ether, 50000 ether, 200000 ether, 1000000 ether];
    tierDiscountBps = [0, 20, 40, 60, 80, 100];      // 0%, 10%, 20%, 30%, 40%, 50%
    tierAuthorBoostBps = [0, 50, 100, 250, 500, 1000]; // 0%, 5%, 10%, 25%, 50%, 100%
}

// FeeConfig 업데이트 (ADMIN only)
function setFeeConfig(
    uint256 _baseFeeBps,
    uint256 _platformFeeBps,
    uint256 _buybackFeeBps,
    uint256 _baseAuthorFeeBps
) external onlyRole(ADMIN) {
    baseFeeBps = _baseFeeBps;
    platformFeeBps = _platformFeeBps;
    buybackFeeBps = _buybackFeeBps;
    baseAuthorFeeBps = _baseAuthorFeeBps;
}

// SettlementConfig 업데이트 (ADMIN only)
function setSettlementConfig(
    uint256 _settlementWindow,
    uint256 _expiryPeriod
) external onlyRole(ADMIN) {
    settlementWindow = _settlementWindow;
    expiryPeriod = _expiryPeriod;
}

// TierConfig 업데이트 (ADMIN only)
function setTierConfig(
    uint256[] calldata _tierThresholds,
    uint256[] calldata _tierDiscountBps,
    uint256[] calldata _tierAuthorBoostBps
) external onlyRole(ADMIN) {
    require(_tierThresholds.length == 6, "Invalid thresholds");
    require(_tierDiscountBps.length == 6, "Invalid discounts");
    require(_tierAuthorBoostBps.length == 6, "Invalid boosts");

    tierThresholds = _tierThresholds;
    tierDiscountBps = _tierDiscountBps;
    tierAuthorBoostBps = _tierAuthorBoostBps;
}

// Tier 조회 (T0 ~ T5)
function getTierDiscount(uint8 tier) external view returns (uint256) {
    require(tier < 6, "Invalid tier");
    return tierDiscountBps[tier];
}

function getTierAuthorBoost(uint8 tier) external view returns (uint256) {
    require(tier < 6, "Invalid tier");
    return tierAuthorBoostBps[tier];
}

function getFollowQuota(uint8 tier) external view returns (uint256) {
    require(tier < 6, "Invalid tier");
    // T0: 1, T1: 3, T2: 10, T3: 25, T4: 50, T5: 100
    uint256[6] memory quotas = [1, 3, 10, 25, 50, 100];
    return quotas[tier];
}
```

### 2.4 이벤트

```solidity
event FeeConfigUpdated(
    uint256 baseFeeBps,
    uint256 platformFeeBps,
    uint256 buybackFeeBps,
    uint256 baseAuthorFeeBps
);

event SettlementConfigUpdated(
    uint256 settlementWindow,
    uint256 expiryPeriod
);

event TierConfigUpdated(
    uint256[] tierThresholds,
    uint256[] tierDiscountBps,
    uint256[] tierAuthorBoostBps
);

event RoleGranted(bytes32 indexed role, address indexed account);
```

---

## 3. StrategyRegistry

### 3.1 개요

전략(Strategy) 등록 및 검증 정보를 관리합니다.

### 3.2 데이터 구조

```solidity
import "./GreatDIYAccessControl.sol";

enum StrategyStatus {
    Draft,              // 작성 중
    PendingReview,      // 검증 대기
    Verified,           // 검증 완료
    ActivationRequested, // 활성화 요청
    Active,             // 활성화
    Suspended,          // 정지
    Rejected            // 거절
}

struct Strategy {
    uint256 id;                  // Strategy ID
    address author;              // 작성자
    string metadataURI;          // IPFS hash
    bytes32 verificationHash;    // 검증 데이터 해시
    uint256 verificationScore;   // 검증 점수
    StrategyStatus status;       // 상태
    uint256 createdAt;           // 생성 시간
    uint256 updatedAt;           // 업데이트 시간
}

contract StrategyRegistry is GreatDIYAccessControl {
    uint256 private _nextStrategyId;
    mapping(uint256 => Strategy) public strategies;  // id => Strategy
    mapping(address => uint256[]) public authorStrategies;  // author => strategyIds

    uint256[] public allStrategyIds;
}
```

### 3.3 함수

```solidity
// 전략 생성 (Draft)
function createStrategy(string calldata metadataURI) external returns (uint256) {
    uint256 strategyId = _nextStrategyId++;

    strategies[strategyId] = Strategy({
        id: strategyId,
        author: msg.sender,
        metadataURI: metadataURI,
        verificationHash: bytes32(0),
        verificationScore: 0,
        status: StrategyStatus.Draft,
        createdAt: block.timestamp,
        updatedAt: block.timestamp
    });

    authorStrategies[msg.sender].push(strategyId);
    allStrategyIds.push(strategyId);

    emit StrategyCreated(strategyId, msg.sender, metadataURI);
    return strategyId;
}

// 전략 메타데이터 업데이트 (Draft only)
function updateStrategy(uint256 strategyId, string calldata metadataURI) external {
    Strategy storage s = strategies[strategyId];
    require(s.author == msg.sender, "Not author");
    require(s.status == StrategyStatus.Draft, "Not draft");

    s.metadataURI = metadataURI;
    s.updatedAt = block.timestamp;

    emit StrategyUpdated(strategyId, metadataURI);
}

// 검증 요청 (VERIFIER only)
function requestVerification(uint256 strategyId) external {
    Strategy storage s = strategies[strategyId];
    require(s.author == msg.sender, "Not author");
    require(s.status == StrategyStatus.Draft, "Not draft");

    s.status = StrategyStatus.PendingReview;
    s.updatedAt = block.timestamp;

    emit VerificationRequested(strategyId);
}

// 전략 검증 (VERIFIER only)
function verifyStrategy(
    uint256 strategyId,
    bytes32 verificationHash,
    uint256 verificationScore
) external onlyRole(VERIFIER) {
    Strategy storage s = strategies[strategyId];
    require(s.status == StrategyStatus.PendingReview, "Not pending");

    s.verificationHash = verificationHash;
    s.verificationScore = verificationScore;
    s.status = StrategyStatus.Verified;
    s.updatedAt = block.timestamp;

    emit StrategyVerified(strategyId, verificationHash, verificationScore);
}

// 활성화 요청
function requestActivation(uint256 strategyId) external {
    Strategy storage s = strategies[strategyId];
    require(s.author == msg.sender, "Not author");
    require(s.status == StrategyStatus.Verified, "Not verified");

    s.status = StrategyStatus.ActivationRequested;
    s.updatedAt = block.timestamp;

    emit ActivationRequested(strategyId);
}

// 전략 활성화 (ADMIN only)
function activateStrategy(uint256 strategyId) external onlyRole(ADMIN) {
    Strategy storage s = strategies[strategyId];
    require(s.status == StrategyStatus.ActivationRequested, "Not requested");

    s.status = StrategyStatus.Active;
    s.updatedAt = block.timestamp;

    emit StrategyActivated(strategyId);
}

// 전략 정지 (ADMIN only)
function suspendStrategy(uint256 strategyId) external onlyRole(ADMIN) {
    Strategy storage s = strategies[strategyId];
    require(s.status == StrategyStatus.Active, "Not active");

    s.status = StrategyStatus.Suspended;
    s.updatedAt = block.timestamp;

    emit StrategySuspended(strategyId);
}

// 전략 거절 (VERIFIER only)
function rejectStrategy(uint256 strategyId) external onlyRole(VERIFIER) {
    Strategy storage s = strategies[strategyId];
    require(
        s.status == StrategyStatus.PendingReview ||
        s.status == StrategyStatus.ActivationRequested,
        "Invalid status"
    );

    s.status = StrategyStatus.Rejected;
    s.updatedAt = block.timestamp;

    emit StrategyRejected(strategyId);
}

// 전략 조회
function getStrategy(uint256 strategyId) external view returns (Strategy memory) {
    return strategies[strategyId];
}

// 작성자의 전략 목록
function getAuthorStrategies(address author) external view returns (uint256[] memory) {
    return authorStrategies[author];
}

// 전체 전략 목록
function getAllStrategies() external view returns (uint256[] memory) {
    return allStrategyIds;
}

// 활성화된 전략 목록
function getActiveStrategies() external view returns (uint256[] memory) {
    uint256[] memory activeIds = new uint256[](allStrategyIds.length);
    uint256 count = 0;

    for (uint256 i = 0; i < allStrategyIds.length; i++) {
        if (strategies[allStrategyIds[i]].status == StrategyStatus.Active) {
            activeIds[count++] = allStrategyIds[i];
        }
    }

    // Resize array
    uint256[] memory result = new uint256[](count);
    for (uint256 i = 0; i < count; i++) {
        result[i] = activeIds[i];
    }

    return result;
}
```

### 3.4 이벤트

```solidity
event StrategyCreated(
    uint256 indexed strategyId,
    address indexed author,
    string metadataURI
);

event StrategyUpdated(
    uint256 indexed strategyId,
    string metadataURI
);

event VerificationRequested(uint256 indexed strategyId);

event StrategyVerified(
    uint256 indexed strategyId,
    bytes32 verificationHash,
    uint256 verificationScore
);

event ActivationRequested(uint256 indexed strategyId);

event StrategyActivated(uint256 indexed strategyId);

event StrategySuspended(uint256 indexed strategyId);

event StrategyRejected(uint256 indexed strategyId);
```

---

## 4. FollowRegistry

### 4.1 개요

사용자별 구독(팔로우) 상태를 관리합니다.

### 4.2 데이터 구조

```solidity
enum FollowStatus {
    None,       // 구독하지 않음
    Active,     // 활성 구독
    Paused,     // 일시 정지
    Stopped     // 구독 종료
}

struct Follow {
    FollowStatus status;      // 상태
    uint256 sinceDay;         // 구독 시작일 (dayIndex)
    uint256 lastSettledDay;   // 마지막 정산일
}

contract FollowRegistry is GreatDIYAccessControl {
    // user => strategyId => Follow
    mapping(address => mapping(uint256 => Follow)) public follows;

    // strategyId => follower count
    mapping(uint256 => uint256) public followerCount;

    // user => following count
    mapping(address => uint256) public followingCount;
}
```

### 4.3 함수

```solidity
// 구독 시작
function startFollow(uint256 strategyId, uint256 dayIndex) external {
    require(follows[msg.sender][strategyId].status == FollowStatus.None, "Already following");

    follows[msg.sender][strategyId] = Follow({
        status: FollowStatus.Active,
        sinceDay: dayIndex,
        lastSettledDay: dayIndex - 1  // 첫 정산은 dayIndex부터
    });

    followerCount[strategyId]++;
    followingCount[msg.sender]++;

    emit FollowStarted(msg.sender, strategyId, dayIndex);
}

// 구독 일시 정지
function pauseFollow(uint256 strategyId) external {
    Follow storage f = follows[msg.sender][strategyId];
    require(f.status == FollowStatus.Active, "Not active");

    f.status = FollowStatus.Paused;

    emit FollowPaused(msg.sender, strategyId);
}

// 구독 재개
function resumeFollow(uint256 strategyId) external {
    Follow storage f = follows[msg.sender][strategyId];
    require(f.status == FollowStatus.Paused, "Not paused");

    f.status = FollowStatus.Active;

    emit FollowResumed(msg.sender, strategyId);
}

// 구독 종료
function stopFollow(uint256 strategyId) external {
    Follow storage f = follows[msg.sender][strategyId];
    require(f.status != FollowStatus.None && f.status != FollowStatus.Stopped, "Invalid status");

    f.status = FollowStatus.Stopped;

    followerCount[strategyId]--;
    followingCount[msg.sender]--;

    emit FollowStopped(msg.sender, strategyId);
}

// 정산일 업데이트 (SETTLEMENT_OPERATOR only)
function updateLastSettledDay(
    address user,
    uint256 strategyId,
    uint256 dayIndex
) external onlyRole(SETTLEMENT_OPERATOR) {
    Follow storage f = follows[user][strategyId];
    require(f.status == FollowStatus.Active, "Not active");
    require(dayIndex > f.lastSettledDay, "Invalid dayIndex");

    f.lastSettledDay = dayIndex;

    emit LastSettledDayUpdated(user, strategyId, dayIndex);
}

// 구독 상태 조회
function getFollow(address user, uint256 strategyId) external view returns (Follow memory) {
    return follows[user][strategyId];
}

// 전략의 팔로워 목록 (페이지네이션 필요 시 구현)
function getFollowers(uint256 strategyId) external view returns (uint256) {
    return followerCount[strategyId];
}

// 사용자의 팔로잉 수
function getFollowingCount(address user) external view returns (uint256) {
    return followingCount[user];
}
```

### 4.4 이벤트

```solidity
event FollowStarted(
    address indexed user,
    uint256 indexed strategyId,
    uint256 dayIndex
);

event FollowPaused(
    address indexed user,
    uint256 indexed strategyId
);

event FollowResumed(
    address indexed user,
    uint256 indexed strategyId
);

event FollowStopped(
    address indexed user,
    uint256 indexed strategyId
);

event LastSettledDayUpdated(
    address indexed user,
    uint256 indexed strategyId,
    uint256 dayIndex
);
```

---

## 5. DecisionHistory

### 5.1 개요

일자별 주문 커밋(Merkle Root)을 저장하여 대용량 주문 데이터를 압축 관리합니다.

### 5.2 데이터 구조

```solidity
struct DayCommit {
    bytes32 rootHash;         // Merkle Root
    uint256 timestamp;        // 커밋 시간
    bytes32 batchInfoHash;    // {count, totalVolume, avgPrice} 해시
}

struct BatchInfo {
    uint256 orderCount;       // 주문 개수
    uint256 totalVolume;      // 총 거래량 (USDT0)
    uint256 avgPrice;         // 평균 가격
}

contract DecisionHistory is GreatDIYAccessControl {
    // strategyId => dayIndex => DayCommit
    mapping(uint256 => mapping(uint256 => DayCommit)) public dayCommits;

    // strategyId => latest dayIndex
    mapping(uint256 => uint256) public latestDayIndex;
}
```

### 5.3 함수

```solidity
// 일자별 커밋 생성 (BACKEND_RELAYER only)
function commitDay(
    uint256 strategyId,
    uint256 dayIndex,
    bytes32 rootHash,
    BatchInfo calldata batchInfo
) external onlyRole(BACKEND_RELAYER) {
    // dayIndex 순서 검증
    require(dayIndex == latestDayIndex[strategyId] + 1, "Invalid dayIndex");

    // batchInfo 해시 계산
    bytes32 batchInfoHash = keccak256(abi.encode(batchInfo));

    dayCommits[strategyId][dayIndex] = DayCommit({
        rootHash: rootHash,
        timestamp: block.timestamp,
        batchInfoHash: batchInfoHash
    });

    latestDayIndex[strategyId] = dayIndex;

    emit DayCommitted(strategyId, dayIndex, rootHash, batchInfo);
}

// 커밋 조회
function getCommit(uint256 strategyId, uint256 dayIndex) external view returns (DayCommit memory) {
    return dayCommits[strategyId][dayIndex];
}

// 최신 dayIndex 조회
function getLatestDayIndex(uint256 strategyId) external view returns (uint256) {
    return latestDayIndex[strategyId];
}

// Merkle Proof 검증
function verifyOrder(
    uint256 strategyId,
    uint256 dayIndex,
    bytes32 leaf,
    bytes32[] calldata proof
) external view returns (bool) {
    DayCommit memory commit = dayCommits[strategyId][dayIndex];
    require(commit.rootHash != bytes32(0), "Commit not found");

    bytes32 computedHash = leaf;
    for (uint256 i = 0; i < proof.length; i++) {
        bytes32 proofElement = proof[i];

        if (computedHash < proofElement) {
            computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
        } else {
            computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
        }
    }

    return computedHash == commit.rootHash;
}
```

### 5.4 이벤트

```solidity
event DayCommitted(
    uint256 indexed strategyId,
    uint256 indexed dayIndex,
    bytes32 rootHash,
    BatchInfo batchInfo
);
```

---

## 6. SettlementManager

### 6.1 개요

수수료 정산 데이터를 관리합니다.

### 6.2 데이터 구조

```solidity
enum SettlementStatus {
    Pending,    // 정산 대기
    Paid,       // 지급 완료
    Expired     // 만료
}

struct Settlement {
    uint256 id;                // Settlement ID
    address user;              // 사용자
    uint256 strategyId;        // 전략 ID
    uint256 dayIndex;          // 정산일
    uint256 feeAmount;         // 수수료 금액 (USDT0)
    uint256 discountBps;       // 적용된 할인율
    uint8 userTierSnapshot;    // 정산 시점 사용자 Tier
    uint8 authorTierSnapshot;  // 정산 시점 저작자 Tier
    SettlementStatus status;   // 상태
    uint256 createdAt;         // 생성 시간
    uint256 paidAt;            // 지급 시간
}

contract SettlementManager is GreatDIYAccessControl {
    IERC20 public usdt0;  // USDT0 토큰

    uint256 private _nextSettlementId;
    mapping(uint256 => Settlement) public settlements;

    // Primary Key: (user, strategyId, dayIndex) => settlementId
    mapping(address => mapping(uint256 => mapping(uint256 => uint256))) public settlementIds;

    // user => unpaid settlement amount
    mapping(address => uint256) public unpaidAmounts;

    // strategyId => author => unpaid amount
    mapping(uint256 => mapping(address => uint256)) public authorUnpaidAmounts;
}
```

### 6.3 함수

```solidity
constructor(address _usdt0) {
    usdt0 = IERC20(_usdt0);
}

// 정산 생성 (SETTLEMENT_OPERATOR only)
function createSettlement(
    address user,
    uint256 strategyId,
    uint256 dayIndex,
    uint256 feeAmount,
    uint256 discountBps,
    uint8 userTierSnapshot,
    uint8 authorTierSnapshot
) external onlyRole(SETTLEMENT_OPERATOR) returns (uint256) {
    uint256 settlementId = _nextSettlementId++;

    settlements[settlementId] = Settlement({
        id: settlementId,
        user: user,
        strategyId: strategyId,
        dayIndex: dayIndex,
        feeAmount: feeAmount,
        discountBps: discountBps,
        userTierSnapshot: userTierSnapshot,
        authorTierSnapshot: authorTierSnapshot,
        status: SettlementStatus.Pending,
        createdAt: block.timestamp,
        paidAt: 0
    });

    settlementIds[user][strategyId][dayIndex] = settlementId;
    unpaidAmounts[user] += feeAmount;

    emit SettlementCreated(settlementId, user, strategyId, dayIndex, feeAmount);
    return settlementId;
}

// 정산 지급 (USDT0 전송)
function paySettlement(uint256 settlementId) external {
    Settlement storage s = settlements[settlementId];
    require(s.user == msg.sender, "Not owner");
    require(s.status == SettlementStatus.Pending, "Not pending");

    s.status = SettlementStatus.Paid;
    s.paidAt = block.timestamp;

    unpaidAmounts[msg.sender] -= s.feeAmount;

    // USDT0 전송 (이 컨트랙트에 충분한 잔액이 있어야 함)
    require(usdt0.transfer(msg.sender, s.feeAmount), "Transfer failed");

    emit SettlementPaid(settlementId, msg.sender, s.feeAmount);
}

// 정산 만료 (SETTLEMENT_OPERATOR only)
function expireSettlement(uint256 settlementId) external onlyRole(SETTLEMENT_OPERATOR) {
    Settlement storage s = settlements[settlementId];
    require(s.status == SettlementStatus.Pending, "Not pending");
    require(block.timestamp >= s.createdAt + expiryPeriod, "Not expired");

    s.status = SettlementStatus.Expired;

    unpaidAmounts[s.user] -= s.feeAmount;

    emit SettlementExpired(settlementId);
}

// 정산 조회
function getSettlement(uint256 settlementId) external view returns (Settlement memory) {
    return settlements[settlementId];
}

// 사용자의 미지급 정산금
function getUnpaidAmount(address user) external view returns (uint256) {
    return unpaidAmounts[user];
}

// (user, strategyId, dayIndex)로 조회
function getSettlementByIds(
    address user,
    uint256 strategyId,
    uint256 dayIndex
) external view returns (Settlement memory) {
    uint256 settlementId = settlementIds[user][strategyId][dayIndex];
    return settlements[settlementId];
}

// USDT0 입금 (FeeDistributor에서 분배된 금액)
function depositUSDT0(uint256 amount) external {
    require(usdt0.transferFrom(msg.sender, address(this), amount), "Transfer failed");
}

// USDT0 잔액 조회
function getUSDT0Balance() external view returns (uint256) {
    return usdt0.balanceOf(address(this));
}
```

### 6.4 이벤트

```solidity
event SettlementCreated(
    uint256 indexed settlementId,
    address indexed user,
    uint256 indexed strategyId,
    uint256 dayIndex,
    uint256 feeAmount
);

event SettlementPaid(
    uint256 indexed settlementId,
    address indexed user,
    uint256 amount
);

event SettlementExpired(uint256 indexed settlementId);
```

---

## 7. FeeDistributor

### 7.1 개요

수수료 분배 및 G8D 바이백 몫을 누적합니다.

### 7.2 데이터 구조

```solidity
struct DailyFeeDistribution {
    uint256 platformFee;      // 플랫폼 몫
    uint256 buybackFee;       // 바이백 재무로 이체
    uint256 authorFee;        // 저작자 분배
    uint256 dayIndex;
}

contract FeeDistributor is GreatDIYAccessControl {
    IERC20 public usdt0;  // USDT0 토큰

    // dayIndex => DailyFeeDistribution
    mapping(uint256 => DailyFeeDistribution) public dailyDistributions;

    // strategyId => author => accumulated fee
    mapping(uint256 => mapping(address => uint256)) public authorAccumulatedFees;

    // 총 누적 바이백 재무
    uint256 public totalBuybackAccumulated;

    // 바이백 재무 주소
    address public buybackTreasury;
}
```

### 7.3 함수

```solidity
constructor(address _usdt0, address _buybackTreasury) {
    usdt0 = IERC20(_usdt0);
    buybackTreasury = _buybackTreasury;
}

// 바이백 재무 주소 설정 (ADMIN only)
function setBuybackTreasury(address _buybackTreasury) external onlyRole(ADMIN) {
    buybackTreasury = _buybackTreasury;
}

// 일일 수수료 분배 (SETTLEMENT_OPERATOR only)
function distributeDailyFees(
    uint256 dayIndex,
    uint256 totalFees,
    uint256[] calldata strategyIds,
    address[] calldata authors,
    uint256[] calldata authorFeeAmounts
) external onlyRole(SETTLEMENT_OPERATOR) {
    require(strategyIds.length == authors.length, "Length mismatch");
    require(strategyIds.length == authorFeeAmounts.length, "Length mismatch");

    // 각 파트 계산
    uint256 platformFee = (totalFees * platformFeeBps) / 10000;
    uint256 buybackFee = (totalFees * buybackFeeBps) / 10000;
    uint256 totalAuthorFee = totalFees - platformFee - buybackFee;

    // 저작자별 분배
    for (uint256 i = 0; i < strategyIds.length; i++) {
        authorAccumulatedFees[strategyIds[i]][authors[i]] += authorFeeAmounts[i];
        emit AuthorFeeDistributed(strategyIds[i], authors[i], authorFeeAmounts[i], dayIndex);
    }

    // 바이백 재무로 이체
    if (buybackFee > 0) {
        totalBuybackAccumulated += buybackFee;
        require(usdt0.transfer(buybackTreasury, buybackFee), "Transfer failed");
    }

    // 기록
    dailyDistributions[dayIndex] = DailyFeeDistribution({
        platformFee: platformFee,
        buybackFee: buybackFee,
        authorFee: totalAuthorFee,
        dayIndex: dayIndex
    });

    emit DailyFeesDistributed(dayIndex, platformFee, buybackFee, totalAuthorFee);
}

// 저작자 출금
function withdrawAuthorFees(uint256 strategyId, uint256 amount) external {
    uint256 accumulated = authorAccumulatedFees[strategyId][msg.sender];
    require(accumulated >= amount, "Insufficient balance");

    authorAccumulatedFees[strategyId][msg.sender] = accumulated - amount;

    require(usdt0.transfer(msg.sender, amount), "Transfer failed");

    emit AuthorFeesWithdrawn(strategyId, msg.sender, amount);
}

// 저작자 누적 수수료 조회
function getAuthorAccumulatedFees(uint256 strategyId, address author) external view returns (uint256) {
    return authorAccumulatedFees[strategyId][author];
}

// 일일 분배 내역 조회
function getDailyDistribution(uint256 dayIndex) external view returns (DailyFeeDistribution memory) {
    return dailyDistributions[dayIndex];
}
```

### 7.4 이벤트

```solidity
event DailyFeesDistributed(
    uint256 indexed dayIndex,
    uint256 platformFee,
    uint256 buybackFee,
    uint256 authorFee
);

event AuthorFeeDistributed(
    uint256 indexed strategyId,
    address indexed author,
    uint256 amount,
    uint256 dayIndex
);

event AuthorFeesWithdrawn(
    uint256 indexed strategyId,
    address indexed author,
    uint256 amount
);
```

---

## 8. BuybackTreasury

### 8.1 개요

바이백 실행 및 G8D 소각/LP 공급을 관리합니다.

### 8.2 데이터 구조

```solidity
struct BuybackExecution {
    uint256 usdt0Spent;       // 사용된 USDT0
    uint256 g8dReceived;      // 획득한 G8D
    uint256 burnedAmount;     // 소각된 G8D
    uint256 lpAmount;         // LP에 공급된 G8D
    uint256 timestamp;
}

contract BuybackTreasury is GreatDIYAccessControl {
    IERC20 public usdt0;  // USDT0 토큰
    IERC20 public g8d;    // G8D 토큰

    // Uniswap V3 Router (또는 Swap Aggregator)
    ISwapRouter public swapRouter;

    // Uniswap V3 Pool (G8D/USDT0)
    address public g8dUsdt0Pool;

    uint256 public burnRateBps = 7000;   // 70% 소각
    uint256 public lpRateBps = 3000;     // 30% LP

    uint256[] public buybackHistory;
    mapping(uint256 => BuybackExecution) public buybackExecutions;
}
```

### 8.3 함수

```solidity
constructor(address _usdt0, address _g8d, address _swapRouter, address _g8dUsdt0Pool) {
    usdt0 = IERC20(_usdt0);
    g8d = IERC20(_g8d);
    swapRouter = ISwapRouter(_swapRouter);
    g8dUsdt0Pool = _g8dUsdt0Pool;
}

// 바이백 비율 설정 (ADMIN only)
function setBuybackRates(uint256 _burnRateBps, uint256 _lpRateBps) external onlyRole(ADMIN) {
    require(_burnRateBps + _lpRateBps == 10000, "Invalid rates");
    burnRateBps = _burnRateBps;
    lpRateBps = _lpRateBps;
}

// 바이백 실행 (TREASURY only)
function executeBuyback(
    uint256 usdt0Amount,
    uint256 minG8dAmount,
    bytes calldata swapData
) external onlyRole(TREASURY) {
    require(usdt0.balanceOf(address(this)) >= usdt0Amount, "Insufficient USDT0");

    // USDT0 → G8D Swap
    uint256 g8dBalanceBefore = g8d.balanceOf(address(this));

    // Swap 실행 (Uniswap V3)
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

    // LP 공급 (Uniswap V3)
    if (lpAmount > 0) {
        g8d.approve(g8dUsdt0Pool, lpAmount);
        // LP 공급 로직 (별도 함수)
        _provideLiquidity(lpAmount);
    }

    // 기록
    uint256 executionId = buybackHistory.length;
    buybackExecutions[executionId] = BuybackExecution({
        usdt0Spent: usdt0Amount,
        g8dReceived: g8dReceived,
        burnedAmount: burnAmount,
        lpAmount: lpAmount,
        timestamp: block.timestamp
    });
    buybackHistory.push(executionId);

    emit BuybackExecuted(executionId, usdt0Amount, g8dReceived, burnAmount, lpAmount);
}

// LP 공급 (내부 함수)
function _provideLiquidity(uint256 g8dAmount) internal {
    // Uniswap V3에 G8D/USDT0 LP 공급
    // (실제 구현 시 NonFungiblePositionManager 사용)
}

// 바이백 기록 조회
function getBuybackExecution(uint256 executionId) external view returns (BuybackExecution memory) {
    return buybackExecutions[executionId];
}

// USDT0 입금
function depositUSDT0(uint256 amount) external {
    require(usdt0.transferFrom(msg.sender, address(this), amount), "Transfer failed");
}

// G8D 잔액 조회 (LP용)
function getG8DBalance() external view returns (uint256) {
    return g8d.balanceOf(address(this));
}

// USDT0 잔액 조회
function getUSDT0Balance() external view returns (uint256) {
    return usdt0.balanceOf(address(this));
}
```

### 8.4 이벤트

```solidity
event BuybackExecuted(
    uint256 indexed executionId,
    uint256 usdt0Spent,
    uint256 g8dReceived,
    uint256 burnedAmount,
    uint256 lpAmount
);

event BuybackRatesUpdated(uint256 burnRateBps, uint256 lpRateBps);
```

---

## 9. G8DToken

### 9.1 개요

G8D ERC20 토큰 컨트랙트입니다.

### 9.2 데이터 구조

```solidity
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";

contract G8DToken is ERC20, ERC20Burnable {
    uint256 public constant TOTAL_SUPPLY = 1_000_000_000 * 10**18;  // 10억 G8D

    constructor() ERC20("G8D Token", "G8D") {
        _mint(msg.sender, TOTAL_SUPPLY);
    }
}
```

### 9.3 함수

```solidity
// mint 없음 (고정 공급량)
// burn은 ERC20Burnable 상속

// decimals override (18)
function decimals() public pure override returns (uint8) {
    return 18;
}

// symbol override
function symbol() public pure override returns (string memory) {
    return "G8D";
}

// name override
function name() public pure override returns (string memory) {
    return "G8D Token";
}
```

---

## 10. G8DStaking

### 10.1 개요

G8D 스테이킹 및 Tier 관리 컨트랙트입니다.

### 10.2 데이터 구조

```solidity
contract G8DStaking is GreatDIYAccessControl {
    IERC20 public g8d;

    mapping(address => uint256) public stakedBalance;
    mapping(address => uint256) public cooldownStart;
    mapping(address => uint256) public stakeTimestamp;

    uint256 public constant MIN_LOCK_PERIOD = 15 days;
    uint256 public constant COOLDOWN_PERIOD = 7 days;

    uint256[] public tierThresholds;  // [0, 5000, 20000, 50000, 200000, 1000000] * 10**18
}
```

### 10.3 함수

```solidity
constructor(address _g8d) {
    g8d = IERC20(_g8d);

    // T0 ~ T5 (18 decimals)
    tierThresholds = [
        0,
        5000 * 10**18,
        20000 * 10**18,
        50000 * 10**18,
        200000 * 10**18,
        1000000 * 10**18
    ];
}

// 스테이킹
function stake(uint256 amount) external {
    require(amount > 0, "Invalid amount");
    require(g8d.transferFrom(msg.sender, address(this), amount), "Transfer failed");

    stakedBalance[msg.sender] += amount;

    // 처음 스테이킹하면 타이머 시작
    if (stakeTimestamp[msg.sender] == 0) {
        stakeTimestamp[msg.sender] = block.timestamp;
    }

    emit Staked(msg.sender, amount, block.timestamp);
}

// 언스테이킹 요청
function requestUnstake(uint256 amount) external {
    require(stakedBalance[msg.sender] >= amount, "Insufficient balance");
    require(block.timestamp >= stakeTimestamp[msg.sender] + MIN_LOCK_PERIOD, "Lock period not met");
    require(cooldownStart[msg.sender] == 0, "Already requested");

    cooldownStart[msg.sender] = block.timestamp;

    emit UnstakeRequested(msg.sender, amount, block.timestamp);
}

// 출금
function withdraw() external {
    require(cooldownStart[msg.sender] > 0, "Not requested");
    require(block.timestamp >= cooldownStart[msg.sender] + COOLDOWN_PERIOD, "Cooldown not met");

    uint256 amount = stakedBalance[msg.sender];

    stakedBalance[msg.sender] = 0;
    cooldownStart[msg.sender] = 0;
    stakeTimestamp[msg.sender] = 0;

    require(g8d.transfer(msg.sender, amount), "Transfer failed");

    emit Withdrawn(msg.sender, amount, block.timestamp);
}

// Tier 조회 (T0 ~ T5)
function tierOf(address user) public view returns (uint8) {
    uint256 balance = stakedBalance[user];

    for (uint8 i = 5; i > 0; i--) {
        if (balance >= tierThresholds[i]) {
            return i;
        }
    }

    return 0;  // T0
}

// 스테이킹 잔액 조회
function getStakedBalance(address user) external view returns (uint256) {
    return stakedBalance[user];
}

// 최소 보유기간 충족 여부
function isLockPeriodMet(address user) external view returns (bool) {
    if (stakeTimestamp[user] == 0) return true;  // 스테이킹 없음
    return block.timestamp >= stakeTimestamp[user] + MIN_LOCK_PERIOD;
}

// 쿨다운 완료 여부
function isCooldownMet(address user) external view returns (bool) {
    if (cooldownStart[user] == 0) return false;
    return block.timestamp >= cooldownStart[user] + COOLDOWN_PERIOD;
}
```

### 10.4 이벤트

```solidity
event Staked(
    address indexed user,
    uint256 amount,
    uint256 timestamp
);

event UnstakeRequested(
    address indexed user,
    uint256 amount,
    uint256 timestamp
);

event Withdrawn(
    address indexed user,
    uint256 amount,
    uint256 timestamp
);
```

---

## 11. 배포 순서

### 11.1 컨트랙트 배포 순서

```
1. G8DToken
   └─ 토큰 컨트랙트

2. GreatDIYAccessControl (Config)
   └─ 권한 및 설정

3. StrategyRegistry
   └─ AccessControl 상속

4. FollowRegistry
   └─ AccessControl 상속

5. DecisionHistory
   └─ AccessControl 상속

6. SettlementManager
   └─ AccessControl 상속, USDT0 주소 필요

7. FeeDistributor
   └─ AccessControl 상속, USDT0, BuybackTreasury 주소 필요

8. BuybackTreasury
   └─ AccessControl 상속, USDT0, G8D, SwapRouter, Pool 주소 필요

9. G8DStaking
   └─ G8D 주소 필요
```

### 11.2 초기 설정

```solidity
// 1. G8D 배포 후
G8DToken g8d = new G8DToken();

// 2. AccessControl 배포
GreatDIYAccessControl accessControl = new GreatDIYAccessControl();

// 3. Registry 배포
StrategyRegistry strategyRegistry = new StrategyRegistry();
FollowRegistry followRegistry = new FollowRegistry();
DecisionHistory decisionHistory = new DecisionHistory();

// 4. USDT0 주소 설정 (기존 토큰)
address usdt0 = 0x...;  // Monad L1 USDT0

// 5. SettlementManager 배포
SettlementManager settlementManager = new SettlementManager(usdt0);

// 6. BuybackTreasury 배포 (나중에 주소 설정)
BuybackTreasury buybackTreasury = new BuybackTreasury(
    usdt0,
    address(g8d),
    swapRouter,
    g8dUsdt0Pool
);

// 7. FeeDistributor 배포
FeeDistributor feeDistributor = new FeeDistributor(usdt0, address(buybackTreasury));

// 8. G8DStaking 배포
G8DStaking staking = new G8DStaking(address(g8d));

// 9. Role 부여
accessControl.grantRole(accessControl.SETTLEMENT_OPERATOR(), backendRelayer);
accessControl.grantRole(accessControl.VERIFIER(), verifierAddress);
accessControl.grantRole(accessControl.TREASURY(), treasuryAddress);
```

---

## 12. 상위/관련 문서

- **[../index.md](../index.md)** - 블록체인 개요
- **[../design/](../design/)** - 프로토콜 설계 문서
- **[./web3-integration.md](./web3-integration.md)** - Web3 프론트엔드 연동 (thirdweb)
- **[./settlement-system.md](./settlement-system.md)** - 정산 시스템 상세

---

*최종 업데이트: 2025-12-29*
