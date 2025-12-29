## **1. 컨트랙트 개요**

**BuybackTreasury**는 FeeDistributor가 분배 과정에서 전달한 **바이백 몫(USDT0)**을 보관하고, 필요 시 이 자금으로 **USDT0 → G8D 스왑(Buyback)**을 실행한 뒤, 정책에 따라

1. **G8D를 소각(burn)**하거나
2. **일부는 G8D/USDT0 유니스왑 풀에 유동성(LP)으로 공급(Auto-LP)**

하는 실행 전담 컨트랙트다.

역할 요약:

1. FeeDistributor로부터 buyback 몫 USDT0 적립
2. 정해진 시점(epoch 또는 batch 단위)마다 buyback 실행
3. Uniswap Router를 통한 USDT0 → G8D 스왑
4. 정책 비율에 따라:
    - G8D 소각(burn)
    - G8D/USDT0 풀에 유동성 공급(addLiquidity)
5. LP 토큰 수령 및 지정된 보관 주소(Liquidity Vault 또는 본 컨트랙트)에 유지
6. 모든 buyback / Auto-LP 이벤트 온체인 기록
7. 운영용 multisig 또는 자동 실행 봇(keeper)에 의해 호출 가능

BuybackTreasury는 **실제 G8D 소각 및 Auto-LP 실행**을 담당하며,  
FeeDistributor는 **소각·Auto-LP에 사용할 재원을 적립**하는 역할만 담당한다.

---

# **2. Buyback & Auto-LP가 필요한 이유**

### 2-1. Buyback & Burn

- G8D 토큰의 **deflation 구조** 구현
- 프로토콜 매출 일부를 **G8D 홀더에게 가치 환원**
- 전략 Marketplace의 **프리미엄·희소성**을 강화하는 핵심 토크노믹스 요소

### 2-2. Auto-LP (자동 유동성 공급)

- DEX(유니스왑) 상에서 **G8D/USDT0 풀 유동성 확보**
- 대량 매수·매도 시 **가격 급변(슬리피지, price impact)** 완화
- CEX 상장 전까지 **온체인 가격 신뢰도**를 높여줌
- 거래가 많이 발생할수록 LP가 자동으로 쌓이는 구조 →  
    **“활성도↑ = 유동성↑ = 가격 안정성↑”**

정산되는 모든 Settlement의 일부가 자동으로 BuybackTreasury로 쌓이고,  
이 USDT0는 **Buyback(소각)**과 **Auto-LP(유동성 공급)**의 재원이 된다.

---

# **3. 적립 구조 (FeeDistributor → BuybackTreasury)**

FeeDistributor는 `distribute()` 실행 시  
**buybackShare** 만큼의 USDT0를 BuybackTreasury 주소로 전송한다.

BuybackTreasury는 다음과 같은 단일 역할을 수행한다:

- **단순 보관 및 누적** (FeeDistributor 외에는 임의 입금 없음)

`usdt0.transferFrom(treasury, address(this), buybackShare);`

적립된 USDT0는 이후 **executeBuyback 계열 함수**를 통해:

- 일정 비율은 **G8D 소각용(Buyback+Burn)**
- 일정 비율은 **Auto-LP(유니스왑 G8D/USDT0 풀 유동성 공급)**

용도로 사용된다.

---

# **4. Buyback 실행 및 정책 비율**

Buyback은 관리 정책에 따라 다음 방식으로 실행된다:

- **수동 멀티시그 호출 (권장)**
- **백엔드 스케줄러/옵서버 호출**
- **체인 자동화 서비스(Keeper) 호출**
- **온체인 거버넌스 호출**

실행 트리거 기준(예시):

- 매일/매주 1회
- Settlement batch 기준
- 적립된 USDT0가 일정 금액 이상(예: 10,000 USDT0 이상)일 때
- 긴급 시장 방어(시장 급락 시 buyback 강도 상향)

정책 비율(예시):

- `burnRateBps` : `lpRateBps` = 50 : 50 (즉, buyback으로 얻은 G8D의 절반은 소각, 절반은 LP로)
- 혹은 **USDT0 기준**으로 비율을 나눌 수도 있음
    - 예: 누적 USDT0 중 70%는 burn용, 30%는 Auto-LP 용

이 비율은 **거버넌스/멀티시그에 의해 변경 가능**하도록 설계한다.

---

# **5. DEX(유니스왑) 스왑 구조**

BuybackTreasury는 다음 구성 요소를 보유:

- `IERC20 public usdt0;` (입력 토큰)
- `IERC20 public g8b;` (출력 토큰)
- `IUniswapV2Router02 public dexRouter;` (유니스왑 v2 Router)
- `address public g8bUsdtPair;` (선택: G8D/USDT0 페어 주소 저장)

### 5-1. 기본 스왑 함수 (Buyback용)

`function _swapExactUSDT0ForG8D(uint256 amountIn, uint256 minOut)     internal     returns (uint256 amountOut);`

스왑 로직:

1. `dexRouter`에 USDT0 사용 승인(allowance)
2. Path: `[address(usdt0), address(g8b)]`
3. `swapExactTokensForTokens` 호출
4. 수령한 G8D 잔고 확인
5. 이후 **burn + Auto-LP 분배**에 사용

`minOut` 파라미터를 통해 슬리피지 관리 → 가격조작·MEV 공격 방지.

---

# **6. Auto-LP 구조 (Uniswap LP 자동 공급)**

Auto-LP는 **Buyback 이후 수령한 G8D와 USDT0 일부를 G8D/USDT0 풀에 addLiquidity** 하는 형태로 동작한다.

### 6-1. 기본 아이디어

1. Buyback으로 G8D를 구매한다.
2. 정책 비율에 따라 G8D 중 일부(or USDT0 일부)를 Auto-LP 용도로 분리한다.
3. Auto-LP 용도로 사용할 자산 쌍:
    - G8D LP용 수량
    - USDT0 LP용 수량
4. 유니스왑 Router의 `addLiquidity` 호출
5. LP 토큰 수령
6. LP 토큰은 **lpRecipient (예: LiquidityVault 컨트랙트)**에 보관
    - 필요시 타임락·멀티시그 락업

### 6-2. Auto-LP 절차 예시

**(1) Buyback 이후 수량 분리**

`uint256 g8bTotal = g8bBalanceAfterSwap;  // 비율 예: burn 50%, LP 50% uint256 g8bForBurn = (g8bTotal * burnRateBps) / 10_000; uint256 g8bForLP   = (g8bTotal * lpRateBps) / 10_000;`

**(2) LP용 USDT0 금액 계산**

- 정책에 따라 두 방식 중 선택 가능:

A. **USDT0도 같은 비율로 나누기**  
B. 또는 **LP에 필요한 만큼만 usdt0를 따로 유지**

예:

`uint256 usdtTotal = usdt0BalanceBeforeSwap; // 혹은 일부만 사용 uint256 usdtForLP = (usdtTotal * lpRateBps) / 10_000;`

**(3) addLiquidity 호출**

`function _addLiquidity(uint256 usdtAmount, uint256 g8bAmountMin)     internal     returns (uint256 lpMinted);`

- `dexRouter.addLiquidity` 호출 시:
    - tokenA = usdt0
    - tokenB = g8b
    - amountADesired = usdtAmount
    - amountBDesired = g8bForLP
    - amountAMin / amountBMin 으로 슬리피지 보호
    - `to = lpRecipient` (LP를 보관할 주소)

**(4) LP 토큰 보관 정책**

- 기본: `lpRecipient` = LiquidityVault 컨트랙트
- LiquidityVault는:
    - LP 토큰을 일정 기간 락업
    - 언락 시점·비율은 온체인에 미리 고지
    - 멀티시그 or 거버넌스에 의해만 조정 가능

---

# **7. G8D 소각 방식 (Burn)**

소각 방식은 두 가지 중 선택:

### **1) burn() 함수 직접 호출 (G8D 토큰이 burnable일 경우)**

`G8DToken(g8bToken).burn(amount);`

컨트랙트가 가진 G8D를 직접 소각.

### **2) dead address(0x000...dead)에 전송**

`G8DToken(g8bToken).transfer(deadAddress, amount);`

소각 효과 동일.

문서에서는 **burn() 기반**을 기본 가정하되,  
망 구성에 따라 dead address 방식으로 변경 가능.

---

# **8. BuybackTreasury 상태 변수 및 기록 구조**

`IERC20  public usdt0; IERC20  public g8b; address public dexRouter; address public treasury;      // FeeDistributor 등에서 들어오는 USDT0 송신자 address public deadAddress;   // burn address  // Auto-LP 관련 address public lpRecipient;   // LP 토큰을 받을 주소(보통 LiquidityVault) IERC20  public lpToken;       // 선택: G8D/USDT0 LP 토큰 인터페이스  // 비율 (bps: basis points, 1% = 100) uint16  public burnRateBps;   // buyback된 G8D 중 소각 비율 uint16  public lpRateBps;     // buyback된 G8D/USDT0 중 LP 비율  uint256 public totalBurned;       // 누적 소각량(G8D) uint256 public totalUSDTConsumed; // 누적 사용된 USDT0 (buyback+LP) uint256 public totalLpMinted;     // 누적 발행된 LP 토큰량`

### Buyback 이력 기록

`struct BuybackRecord {     uint256 usdtIn;      // 사용한 USDT0     uint256 g8bOut;      // buyback으로 받은 G8D 총량     uint256 g8bBurned;   // 그 중 소각된 G8D     uint256 usdtLpUsed;  // LP에 사용된 USDT0     uint256 g8bLpUsed;   // LP에 사용된 G8D     uint256 lpMinted;    // 발행된 LP 토큰 수량     uint64  timestamp; }  mapping(uint256 => BuybackRecord) public records; uint256 public buybackCount;`

---

# **9. 기능(Functions)**

## **9-1. executeBuyback**

`function executeBuyback(uint256 usdtAmountIn, uint256 minG8DOut)     external     onlyRole(OPERATOR);`

동작:

1. `usdtAmountIn` 만큼 BuybackTreasury가 보유한 USDT0를 사용
2. `usdt0 ≥ usdtAmountIn` 검증
3. `_swapExactUSDT0ForG8D(usdtAmountIn, minG8DOut)` 호출
4. 수령한 G8D 중:
    - `burnRateBps` 비율만큼 즉시 소각
    - `lpRateBps` 비율만큼 Auto-LP용으로 분리
5. Auto-LP 비율이 0이 아니면 `_addLiquidity` 실행
6. `BuybackRecord` 기록 및 이벤트 발생
7. 누적값 업데이트 (`totalBurned`, `totalUSDTConsumed`, `totalLpMinted`)

## **9-2. executeBuybackAll**

`function executeBuybackAll(uint256 minG8DOut)     external     onlyRole(OPERATOR);`

- 보유한 모든 USDT0를 buyback에 사용
- 이후 과정은 `executeBuyback`과 동일
- 운영자가 정산 주기마다 “전체 누적분 처리”할 때 사용
## **9-3. 관리자/운영 설정 함수**

- `setRates(uint16 burnRateBps, uint16 lpRateBps)`
- `setLpRecipient(address lpRecipient)`
- `setDexRouter(address newRouter)`
- `setDeadAddress(address newDead)`

모두 **onlyRole(ADMIN)** 또는 멀티시그 전용.

---

# **10. 이벤트(Event)**

|이벤트|설명|
|---|---|
|**BuybackExecuted(usdtIn, g8bOut, g8bBurned, timestamp)**|Buyback + Burn 실행|
|**AutoLpExecuted(usdtLpUsed, g8bLpUsed, lpMinted, timestamp)**|Auto-LP(addLiquidity) 실행|
|**RatesUpdated(oldBurnRate, oldLpRate, newBurnRate, newLpRate)**|burn/LP 비율 변경|
|**RouterUpdated(old, new)**|DEX router 변경|
|**LpRecipientUpdated(old, new)**|LP 토큰 수령 주소 변경|
|**DeadAddressUpdated(old, new)**|burn address 변경|

---

# **11. 보안 및 설계 상 주의 사항 (Security Notes)**

### **1) OPERATOR / ADMIN 권한 분리**

- `executeBuyback`은 **OPERATOR**(멀티시그, keeper 등)만 호출
- Rate 설정, Router·lpRecipient 변경 등은 **ADMIN** 또는 거버넌스 전용으로 제한

### **2) 슬리피지 및 가격조작 방지**

- 스왑 시 반드시 `minOut` 사용
- addLiquidity에서도 `amountAMin`, `amountBMin` 설정
- MEV/샌드위치 공격 방지 위해 백엔드에서 안전 구간 판단 후 호출

### **3) USDT0 탈취 및 LP 탈취 방지**

- 컨트랙트에 USDT0/G8D 외 자산 보관 최소화
- `nonReentrant` 적용
- LP 토큰은 `lpRecipient`에 모으고, 그 주소는 **타임락+멀티시그** 조합 권장

### **4) Auto-LP 과도한 집중 방지**

- 너무 작은 풀에 큰 Auto-LP 투입 시 가격 왜곡 발생 가능
- buyback/LP 비율은 단계적으로 조정(초기 50/50 → 나중에 30/70 등)
- CEX 상장 이후에는 Auto-LP 비율을 낮추는 정책 포함 가능

---

# **12. FeeDistributor와의 관계**

역할 구분:

|컨트랙트|역할|
|---|---|
|**FeeDistributor**|각 Settlement 분배 시 buyback 몫 USDT0를 BuybackTreasury로 “입금/적립”|
|**BuybackTreasury**|적립된 USDT0를 사용해 **(1) G8D Buyback + Burn**, **(2) G8D/USDT0 Auto-LP** 실행|

이 구분을 통해:

- **정산(매출) → FeeDistributor → BuybackTreasury → Buyback+Burn/LP**  
    라는 선형 구조로 흐름이 명확해진다.

---

# **13. 전체 흐름 요약**

`Settlement 정산     ↓ FeeDistributor     ↓ buybackShare (USDT0 전송) BuybackTreasury     ↓ executeBuyback(usdtAmountIn) Uniswap Router     ↓ USDT0 → G8D 스왑 BuybackTreasury     ├─ G8D 일부 소각 (burn)     └─ G8D + USDT0 일부로 Auto-LP(addLiquidity)             ↓          LP 토큰 → lpRecipient(LiquidityVault) 결과:     - G8D 공급 감소 (deflation)     - G8D/USDT0 풀 유동성 증가 (가격 안정성↑)`

---

# **14. 요약**

**BuybackTreasury**는 GreatDIY 토크노믹스에서 다음을 수행하는 실행 레이어다:

1. FeeDistributor에서 전달된 USDT0 누적
2. 정해진 정책에 따라 Buyback 실행
3. Uniswap(유니스왑)에서 USDT0 → G8D 스왑
4. 정책 비율에 따라:
    - G8D 소각(Burn)
    - G8D/USDT0 풀에 Auto-LP(addLiquidity)
5. LP 토큰은 지정된 Vault에 모아 락업 및 관리
6. 모든 과정은 온체인 이벤트와 기록으로 투명하게 남는다.

즉, BuybackTreasury는  
**“G8D의 가치 상승(소각) + 가격 안정성(유동성)”을 동시에 실현하는 토크노믹스 실행 컨트랙트**다.