## **1. 컨트랙트 개요**

**DecisionHistory**는 GreatDIY 자동매매 엔진이 하루 동안 생성한  
"모든 주문·결정(orders/decisions)"을 **온체인에 직접 저장하지 않고**,  
**압축된 형태(Merkle Root / 해시 커밋)**로 기록하는 저장소다.

즉,

- **오프체인(Order Log) = 실제 모든 명령·주문**
- **온체인(DecisionHistory) = 그날의 Order Log 전체를 대표하는 단일 해시** 라는 구조를 가진다.

이를 통해:

- 온체인의 비용/데이터 효율성 유지
- SettlementManager에서 Settlement 생성 시  
    “이 날 자동매매가 어떤 근거로 정산되는지”  
    → **검증 가능한 감사(anchor) 역할** 수행
- 이후 분쟁·감사·백테스트 재현 등에서  
    “오프체인 로그 위조 방지”에 핵심적인 증명 체계 제공

---

## **2. 역할(Role) 연동**

DecisionHistory는 다음 역할을 사용한다:

|역할|권한|
|---|---|
|**BACKEND_RELAYER**|일일 주문 로그의 Merkle Root 커밋|
|**ADMIN**|비상 상황에서 기록 정정/취소(옵션), Pause 처리|
|**SETTLEMENT_OPERATOR**|Settlement 생성 시 조회만 수행|

**사용자(user) / 전략 저작자(author)는 write 권한 없음.**

자동매매 엔진(Backend Relayer)이

- 하루 매매 종료
- 또는 일정 batch 단위로 rootHash를 업로드한다.

---

## **3. 저장 구조 (Storage Structure)**

### **3-1. 핵심 저장 구조체**

`struct DayCommit {     bytes32 rootHash;      // (필수) 주문/결정 로그 전체의 Merkle Root 또는 hash     uint64  timestamp;     // commit 시각 (블록 타임 기준)     bytes32 batchInfoHash; // (선택) batch 메타데이터 요약값 }`

### **3-2. 매핑 구조**

`mapping(uint64 => DayCommit) public commits;`

- key = `dayIndex`  
    (UTC+0 이벤트 기준 daily 인덱스, SettlementManager와 동일 기준)

각 dayIndex에 대해 **하루에 한 번만 기록하는 것을 기본 정책**으로 한다.

### **3-3. 정책**

- “덮어쓰기(override)는 기본적으로 금지”
- 단, 예외적 상황(예: 백엔드 장애, 잘못된 commit)에서 ADMIN이 **force override** 기능을 쓸 수 있다면, 반드시 **이벤트로 남기고 프로토콜 운영 정책에 따른 기록** 필요

---

## **4. 동작 방식 (Operation)**

### **4-1. 오프체인 로그 생성 (자동매매 엔진)**

오프체인 자동매매 엔진은 하루 동안의 모든 로그를 내부 DB에 기록한다.

예:

`[   { timestamp: ..., decision: "BUY", amount: ..., price: ..., strategyId: 4 },   { timestamp: ..., decision: "CLOSE", ... },   { timestamp: ..., decision: "SELL", ... },   ... ]`

이 전체 리스트를

- Merkle Tree로 만들고 → Root 생성  
    또는
- Hash(chain-of-hash) 방식으로 압축

한다.

---

### **4-2. 온체인 커밋 (commitRoot)**

**호출 권한: BACKEND_RELAYER**

`commitRoot(uint64 dayIndex, bytes32 rootHash, bytes32 batchInfoHash)`

동작:

1. `commits[dayIndex]`가 비어 있는지 확인
2. 비어 있다면:
    - `commits[dayIndex] = DayCommit(rootHash, block.timestamp, batchInfoHash)`
3. `CommitRecorded(dayIndex, rootHash, batchInfoHash)` 이벤트 발생

> batchInfoHash는 선택적
> - 전략별 주문 개수 요약
> - batch 분할 개수
> - 거래소 응답 요약  
> 등 메타 데이터를 Bytes32로 압축해 저장

---

### **4-3. SettlementManager에서의 활용**

Settlement를 생성하는 시점에서:

- `(user, strategyId, dayIndex)`에 대한 정산액을 계산한 뒤
- DecisionHistory에서 commits[dayIndex].rootHash를 anchor로 사용하여
- 오프체인 로그와 일치하는지 검증 가능

**따라서 SettlementManager는 commitRoot가 존재하지 않는 날은 Settlement 생성 불가.**

---

### **4-4. 감사(Verification)**

검증자는(Verifier 또는 Admin):

- 오프체인 로그의 Merkle Proof를 제공받아
- 특정 주문·행위가 정말 commit되었는지 증명 가능

근거:

- `rootHash`가 해당 주문을 포함하는 Merkle Root인지
- Proof (Merkle Path)로 확인

이 구조 덕분에 자동매매 엔진이 로그를 조작할 여지가 거의 없음.

---

## **5. 기능(Function) 명세**

### **5-1. commitRoot**

`function commitRoot(     uint64 dayIndex,     bytes32 rootHash,     bytes32 batchInfoHash ) external onlyRole(BACKEND_RELAYER)`

- dayIndex에 해당하는 root가 이미 존재하면 revert
- 처음 업로드된 해시만 유효
- 이벤트 발생:  
    `CommitRecorded(dayIndex, rootHash, batchInfoHash)`

### **5-2. forceCommitRoot (옵션)**

`function forceCommitRoot(     uint64 dayIndex,     bytes32 rootHash,     bytes32 batchInfoHash ) external onlyRole(ADMIN)`

- 운영상 치명적 오류가 발생했을 때만 사용
- 기존 값을 덮어쓰고 `CommitOverridden(dayIndex, rootHash)` 이벤트 발생
- 정책 문서에서 어떤 경우에만 사용 가능한지 규정 필요

### **5-3. 조회 함수**

`function getCommit(uint64 dayIndex)     external     view     returns (DayCommit memory)`

- SettlementManager/백엔드가 조회할 때 사용

---

## **6. 이벤트(Event)**

|이벤트|설명|
|---|---|
|`CommitRecorded(dayIndex, rootHash, batchInfoHash)`|새로운 Merkle Root 커밋|
|`CommitOverridden(dayIndex, newRootHash)`|ADMIN에 의해 기존 커밋 덮어쓰기 (선택 기능)|

---

## **7. 보안(Security Notes)**

- ON-CHAIN WRITE는 반드시 백엔드 자동화 + BACKEND_RELAYER Role만 허용
- Merkle Root가 “하루 1회”만 기록되도록 제한하는 것이 바람직
- force override는 ADMIN만 가능하며, 반드시 이벤트 발생  
    → 사후 추적 가능
- 로그 조작을 방지하기 위해,  
    오프체인 로그 저장소는 immutability 또는 서명 기반 저장 방식 추천  
    (AWS S3 + Signature, IPFS, 혹은 내부 append-only DB 등)

---

## **8. 다른 컨트랙트와의 관계**

### **SettlementManager**

- Settlement 생성 시 `commits[dayIndex]` 조회
- 없는 경우 → Settlement 생성 불가
- Settlement 완료 시  
    → DecisionHistory 값과 오프체인 로그를 비교하여 정산 근거 완성

### **StrategyRegistry**

- 특정 전략이 어떤 날 어떤 주문을 실행했는지  
    → 오프체인에서 batchInfoHash와 결합해 빠르게 조회 가능

### **FollowRegistry**

- 팔로우 상태와 합쳐서  
    “이 유저가 이 날 실제로 전략을 실행했는가?”를 판단하는 근거 제공

---

## **9. 전체 흐름 요약**

`오프체인 자동매매 엔진    ↓ raw log (하루)    ↓ Merkle Tree 생성    ↓ Merkle Root    ↓ commitRoot(dayIndex, rootHash)  온체인 DecisionHistory    ↓ rootHash 저장 (영구 기록)    ↓ SettlementManager가 참조    ↓ Settlement 생성/검증에 사용    ↓ 투명성·감사 기반 확보`

---

## **10. 요약**

- DecisionHistory는 **온체인 감사·투명성**을 위한 핵심 컨트랙트
- 모든 주문/결정을 직접 저장하지 않고 **압축된 단일 해시로 기록**
- SettlementManager가 신뢰 기반으로 Settlement 생성 가능
- Merkle Proof를 통해 오프체인 로그 위조 방지
- Relayer → Root 커밋 → SettlementManager → 정산  
    이 흐름으로 GreatDIY의 완전한 **투명 자동매매 회계 시스템**을 형성한다.