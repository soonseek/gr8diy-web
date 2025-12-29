# Merkle Tree (머클 트리)

Great DIY 프로토콜의 Merkle Tree 기반 데이터 압축 및 검증 시스템 상세 명세입니다.

---

## 1. 개요

### 1.1 Merkle Tree 활용 목적

| 목적 | 설명 |
|------|------|
| **가스비 절감** | 대용량 주문 로그를 Merkle Root로 압축하여 온체인 저장 |
| **무결성성 보장** | 주문 데이터의 위변조 방지 |
| **효율적 검증** | O(log n)의 복잡도로 데이터 존재 증명 |

### 1.2 데이터 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                     일일 주문 실행                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              오프체인 데이터베이스 저장                      │
│  (개별 주문: timestamp, symbol, side, price, quantity)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Merkle Tree 구성                          │
│                                                              │
│                        Root Hash                            │
│                       /        \                            │
│                    H01        H02                           │
│                   /  \        /  \                          │
│                 H1   H2    H3   H4                          │
│                 |    |     |    |                          │
│               Leaf1 Leaf2 Leaf3 Leaf4                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              DecisionHistory 온체인 커밋                    │
│         dayCommits[strategyId][dayIndex] = {               │
│           rootHash, timestamp, batchInfoHash               │
│         }                                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              사용자 검증 (Merkle Proof)                      │
│         verifyOrder(strategyId, dayIndex, leaf, proof)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Merkle Tree 구현

### 2.1 Python 구현

```python
# services/merkle/merkle_tree.py
from typing import List, Optional, Tuple
from dataclasses import dataclass
import hashlib

@dataclass
class MerkleProof:
    """Merkle Proof"""
    leaf: str
    leaf_index: int
    proof: List[str]  # sibling hashes
    root: str

class MerkleTree:
    """Merkle Tree 구현"""

    def __init__(self, leaves: List[bytes]):
        """
        Merkle Tree 생성

        Args:
            leaves: leaf 데이터 리스트
        """
        self.leaves = [self._hash(leaf) for leaf in leaves]
        self.root = self._build_tree()

    @staticmethod
    def _hash(data: bytes) -> str:
        """
        Keccak256 해시 (Solidity 호환)

        Args:
            data: 바이너리 데이터

        Returns:
            해시값 (hex string)
        """
        from eth_hash.auto import keccak
        return keccak(data).hex()

    def _build_tree(self) -> str:
        """
        Merkle Tree 빌드

        Returns:
            Root hash
        """
        if not self.leaves:
            return self._hash(b"")

        layer = self.leaves.copy()

        while len(layer) > 1:
            new_layer = []

            # 페어별 해시 계산
            for i in range(0, len(layer), 2):
                left = layer[i]

                # 홀수 개인 경우 마지막 요소 복제
                if i + 1 < len(layer):
                    right = layer[i + 1]
                else:
                    right = left

                # 정렬 후 해시 (작은 값이 왼쪽)
                if left < right:
                    combined = bytes.fromhex(left) + bytes.fromhex(right)
                else:
                    combined = bytes.fromhex(right) + bytes.fromhex(left)

                parent_hash = self._hash(combined)
                new_layer.append(parent_hash)

            layer = new_layer

        return layer[0] if layer else ""

    def get_proof(self, leaf_index: int) -> MerkleProof:
        """
        특정 leaf의 Merkle Proof 생성

        Args:
            leaf_index: leaf 인덱스

        Returns:
            MerkleProof
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise ValueError("Invalid leaf index")

        leaf = self.leaves[leaf_index]
        proof = []
        index = leaf_index

        layer = self.leaves.copy()

        while len(layer) > 1:
            # Sibling 찾기
            if index % 2 == 0:
                sibling_index = index + 1
            else:
                sibling_index = index - 1

            # Sibling이 없으면 자기 자신
            if sibling_index >= len(layer):
                sibling_hash = layer[index]
            else:
                sibling_hash = layer[sibling_index]

            proof.append(sibling_hash)

            # 다음 레이어로 이동
            index //= 2
            new_layer = []

            for i in range(0, len(layer), 2):
                left = layer[i]
                if i + 1 < len(layer):
                    right = layer[i + 1]
                else:
                    right = left

                if left < right:
                    combined = bytes.fromhex(left) + bytes.fromhex(right)
                else:
                    combined = bytes.fromhex(right) + bytes.fromhex(left)

                parent_hash = self._hash(combined)
                new_layer.append(parent_hash)

            layer = new_layer

        return MerkleProof(
            leaf=leaf,
            leaf_index=leaf_index,
            proof=proof,
            root=self.root
        )

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """
        Merkle Proof 검증

        Args:
            proof: MerkleProof

        Returns:
            검증 결과
        """
        computed_hash = proof.leaf

        for sibling in proof.proof:
            # 정렬 후 해시
            if computed_hash < sibling:
                combined = bytes.fromhex(computed_hash) + bytes.fromhex(sibling)
            else:
                combined = bytes.fromhex(sibling) + bytes.fromhex(computed_hash)

            computed_hash = MerkleTree._hash(combined)

        return computed_hash == proof.root
```

### 2.2 주문 → Leaf 변환

```python
# services/merkle/order_leaf.py
from typing import Dict
import json

def order_to_leaf(order: Dict) -> bytes:
    """
    주문을 Merkle Leaf로 변환

    Args:
        order: {
            'user': '0x...',
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'price': 50000,
            'quantity': 0.1,
            'timestamp': 1609459200
        }

    Returns:
        ABI 인코딩된 바이너리
    """
    from eth_abi import encode

    # ABI 인코딩 (Solidity 호환)
    encoded = encode(
        ['address', 'string', 'string', 'uint256', 'uint256', 'uint256'],
        [
            order['user'],
            order['symbol'],
            order['side'],
            int(order['price'] * 1e18),  # 18 decimals
            int(order['quantity'] * 1e18),
            order['timestamp']
        ]
    )

    return encoded

def leaf_to_order(leaf: bytes) -> Dict:
    """
    Merkle Leaf를 주문으로 디코딩

    Args:
        leaf: ABI 인코딩된 바이너리

    Returns:
        주문 딕셔너리
    """
    from eth_abi import decode

    decoded = decode(
        ['address', 'string', 'string', 'uint256', 'uint256', 'uint256'],
        leaf
    )

    return {
        'user': decoded[0],
        'symbol': decoded[1],
        'side': decoded[2],
        'price': decoded[3] / 1e18,
        'quantity': decoded[4] / 1e18,
        'timestamp': decoded[5]
    }
```

---

## 3. 온체인 검증

### 3.1 Solidity 검증 함수

```solidity
// DecisionHistory.sol
function verifyOrder(
    uint256 strategyId,
    uint256 dayIndex,
    bytes32 leaf,
    bytes32[] calldata proof
) external view returns (bool) {
    // DayCommit 조회
    DayCommit memory commit = dayCommits[strategyId][dayIndex];
    require(commit.rootHash != bytes32(0), "Commit not found");

    // Merkle Proof 검증
    bytes32 computedHash = leaf;

    for (uint256 i = 0; i < proof.length; i++) {
        bytes32 proofElement = proof[i];

        // 정렬 후 해시 (작은 값이 왼쪽)
        if (computedHash < proofElement) {
            computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
        } else {
            computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
        }
    }

    return computedHash == commit.rootHash;
}
```

### 3.2 TypeScript 검증 Hook

```typescript
// hooks/useMerkleProof.ts
"use client";

import { useReadContract } from "thirdweb/react";
import { decisionHistoryContract } from "@/lib/contracts";
import { encodePacked, keccak256 } from "viem";

export function useMerkleProof() {
  // 온체인 검증
  const { data: isValid, refetch } = useReadContract({
    contract: decisionHistoryContract,
    method: "verifyOrder",
    params: [
      strategyId,
      dayIndex,
      leafHash,
      proof,
    ],
    queryOptions: {
      enabled: false,  // 수동 호출
    },
  });

  // 클라이언트 사이드 검증 (옵션)
  const verifyProofClientSide = (
    leaf: string,
    proof: string[],
    root: string
  ): boolean => {
    let computedHash = leaf as `0x${string}`;

    for (const sibling of proof) {
      const siblingHash = sibling as `0x${string}`;

      // 정렬 후 해시
      if (computedHash < siblingHash) {
        computedHash = keccak256(
          encodePacked(computedHash, siblingHash)
        );
      } else {
        computedHash = keccak256(
          encodePacked(siblingHash, computedHash)
        );
      }
    }

    return computedHash === root;
  };

  return {
    isValid,
    verifyProofClientSide,
    refetch,
  };
}
```

---

## 4. 일일 커밋 프로세스

### 4.1 백엔드 커밋 서비스

```python
# services/merkle/commit_service.py
from typing import Dict, List
from services.merkle.merkle_tree import MerkleTree, order_to_leaf

class DailyCommitService:
    """일일 Merkle Commit 서비스"""

    async def create_daily_commit(
        self,
        strategy_id: int,
        day_index: int,
        orders: List[Dict]
    ) -> Dict:
        """
        일별 Merkle Commit 생성

        Args:
            strategy_id: 전략 ID
            day_index: 일자 인덱스
            orders: 주문 리스트

        Returns:
            {
                'merkle_root': str,
                'batch_info': {
                    'order_count': int,
                    'total_volume': float
                },
                'proofs': {
                    'order_id': MerkleProof
                }
            }
        """
        if not orders:
            return None

        # 1. Leaves 생성
        leaves = [order_to_leaf(order) for order in orders]

        # 2. Merkle Tree 빌드
        tree = MerkleTree(leaves)
        merkle_root = tree.root

        # 3. Batch Info 계산
        total_volume = sum(
            float(order['price']) * float(order['quantity'])
            for order in orders
        )

        batch_info = {
            'order_count': len(orders),
            'total_volume': total_volume
        }

        # 4. 각 주문별 Proof 생성
        proofs = {}
        for i, order in enumerate(orders):
            proof = tree.get_proof(i)
            proofs[order['id']] = proof

        return {
            'merkle_root': merkle_root,
            'batch_info': batch_info,
            'proofs': proofs
        }

    async def commit_onchain(
        self,
        web3: Web3,
        strategy_id: int,
        day_index: int,
        merkle_root: str,
        batch_info: Dict
    ) -> str:
        """
        온체인 커밋 실행

        Returns:
            트랜잭션 해시
        """
        # 컨트랙트 호출
        contract = web3.eth.contract(
            address=self.decision_history_address,
            abi=self.decision_history_abi
        )

        # Batch Info 해시
        batch_info_hash = web3.solidity.keccak3(
            abi.encode(
                ['uint256', 'uint256'],
                [batch_info['order_count'], int(batch_info['total_volume'] * 1e18)]
            )
        )

        # Commit 실행
        tx_hash = contract.functions.commitDay(
            strategy_id,
            day_index,
            web3.to_bytes(hexstr=merkle_root),
            batch_info_hash
        ).transact({'from': self.backend_relayer})

        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt['transactionHash'].hex()
```

### 4.2 환경별 Batch 크기

| 환경 | Max Batch Size | 설명 |
|------|----------------|------|
| **개발서버** | 100 | 테스트용 작은 배치 |
| **운영서버** | 1000 | 프로덕션용 대량 배치 |

```typescript
// config/merkle.ts
export const MERKLE_CONFIG = {
  development: {
    maxBatchSize: 100,
    commitInterval: 1 * 60 * 60 * 1000,  // 1시간 (테스트용)
  },
  production: {
    maxBatchSize: 1000,
    commitInterval: 24 * 60 * 60 * 1000,  // 24시간
  },
};
```

---

## 5. 사용자 조회 API

### 5.1 주문 증명 API

```python
# api/v1/merkle.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/merkle", tags=["merkle"])

@router.get("/orders/{order_id}/proof")
async def get_order_proof(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    주문의 Merkle Proof 조회

    Returns:
        {
            'order': 주문 정보,
            'proof': Merkle Proof,
            'root': Merkle Root
        }
    """
    # 주문 조회
    order = await order_repository.get_order(order_id, db)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 소유자 확인
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")

    # Merkle Proof 조회
    proof = await merkle_service.get_order_proof(order_id, db)

    return {
        'order': order,
        'proof': proof,
        'valid': True  # 온체인 검증 결과 (선택)
    }

@router.post("/verify")
async def verify_order_onchain(
    strategy_id: int,
    day_index: int,
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    온체인 주문 검증

    Returns:
        {
            'valid': bool,
            'tx_hash': str
        }
    """
    # 주문 조회
    order = await order_repository.get_order(order_id, db)

    # Leaf 생성
    leaf = order_to_leaf(order)

    # Proof 조회
    proof_data = await merkle_service.get_order_proof(order_id, db)
    proof = proof_data['proof']

    # 온체인 검증
    is_valid = await web3_service.verify_order(
        strategy_id=strategy_id,
        day_index=day_index,
        leaf=leaf,
        proof=proof
    )

    return {
        'valid': is_valid,
        'leaf': leaf.hex(),
        'root': proof_data['root']
    }
```

---

## 6. 프론트엔드 연동

### 6.1 주문 검증 컴포넌트

```typescript
// components/merkle/OrderVerification.tsx
"use client";

import { useState } from "react";
import { useMerkleProof } from "@/hooks/useMerkleProof";

export function OrderVerification({ orderId, strategyId, dayIndex }: {
  orderId: string;
  strategyId: bigint;
  dayIndex: bigint;
}) {
  const { verifyProofClientSide, isValid } = useMerkleProof();
  const [isVerifying, setIsVerifying] = useState(false);

  const handleVerify = async () => {
    setIsVerifying(true);

    try {
      // API로 Proof 조회
      const response = await fetch(`/api/v1/merkle/orders/${orderId}/proof`);
      const data = await response.json();

      // 클라이언트 사이드 검증
      const valid = verifyProofClientSide(
        data.proof.leaf,
        data.proof.proof,
        data.proof.root
      );

      // 온체인 검증 (선택)
      // const isValidOnchain = await isValid();

      alert(valid ? "Order verified!" : "Verification failed");
    } catch (error) {
      console.error("Verification failed:", error);
      alert("Verification failed");
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-bold mb-2">Order Verification</h3>
      <p className="text-sm text-gray-600 mb-4">
        Verify this order exists on-chain
      </p>

      <button
        onClick={handleVerify}
        disabled={isVerifying}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        {isVerifying ? "Verifying..." : "Verify Order"}
      </button>
    </div>
  );
}
```

---

## 7. 데이터 저장소

### 7.1 오프체인 저장 테이블

```sql
-- Merkle Proofs 저장
CREATE TABLE merkle_proofs (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id),
    strategy_id INTEGER NOT NULL,
    day_index INTEGER NOT NULL,
    leaf_hash TEXT NOT NULL,
    proof TEXT NOT NULL,  -- JSON 배열
    root_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(strategy_id, day_index, order_id)
);

-- Day Commits 저장
CREATE TABLE day_commits (
    id UUID PRIMARY KEY,
    strategy_id INTEGER NOT NULL,
    day_index INTEGER NOT NULL,
    merkle_root TEXT NOT NULL,
    order_count INTEGER NOT NULL,
    total_volume DECIMAL(20, 8) NOT NULL,
    batch_info_hash TEXT NOT NULL,
    committed_at TIMESTAMPTZ DEFAULT NOW(),
    tx_hash TEXT,
    UNIQUE(strategy_id, day_index)
);

CREATE INDEX idx_merkle_proofs_order ON merkle_proofs(order_id);
CREATE INDEX idx_day_commits_strategy ON day_commits(strategy_id, day_index);
```

### 7.2 Repository 구현

```python
# repositories/merkle_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class MerkleRepository:
    """Merkle 관련 데이터 Repository"""

    async def save_proof(
        self,
        order_id: str,
        strategy_id: int,
        day_index: int,
        proof: MerkleProof,
        db: AsyncSession
    ):
        """Merkle Proof 저장"""
        record = MerkleProofModel(
            order_id=order_id,
            strategy_id=strategy_id,
            day_index=day_index,
            leaf_hash=proof.leaf,
            proof=json.dumps(proof.proof),
            root_hash=proof.root
        )
        db.add(record)
        await db.commit()

    async def get_proof(
        self,
        order_id: str,
        db: AsyncSession
    ) -> Optional[MerkleProof]:
        """Merkle Proof 조회"""
        result = await db.execute(
            select(MerkleProofModel).where(
                MerkleProofModel.order_id == order_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        return MerkleProof(
            leaf=record.leaf_hash,
            leaf_index=0,  # 저장하지 않음
            proof=json.loads(record.proof),
            root=record.root_hash
        )

    async def save_day_commit(
        self,
        strategy_id: int,
        day_index: int,
        merkle_root: str,
        batch_info: Dict,
        tx_hash: str,
        db: AsyncSession
    ):
        """Day Commit 저장"""
        record = DayCommitModel(
            strategy_id=strategy_id,
            day_index=day_index,
            merkle_root=merkle_root,
            order_count=batch_info['order_count'],
            total_volume=batch_info['total_volume'],
            batch_info_hash=keccak256(abi.encode(['uint256', 'uint256'], [
                batch_info['order_count'],
                int(batch_info['total_volume'] * 1e18)
            ])).hex(),
            tx_hash=tx_hash
        )
        db.add(record)
        await db.commit()
```

---

## 8. 보안 고려사항

### 8.1 무결성 보장

| 위협 | 방어책 |
|------|--------|
| **데이터 위변조** | Merkle Root로 온체인 무결성 보장 |
| **Proof 위조** | Root 해시와 일치하는지 검증 |
| **Replay Attack** | dayIndex를 포함하여 일회성 보장 |

### 8.2 환경별 보안 설정

| 항목 | 개발서버 | 운영서버 |
|------|----------|----------|
| **Commit 권한** | BACKEND_RELAYER | BACKEND_RELAYER |
| **검증 허용** | 공개 | 공개 |
| **Batch Size** | 100 | 1000 |

---

## 9. 상위/관련 문서

- **[../index.md](../index.md)** - 블록체인 개요
- **[./smart-contracts.md](./smart-contracts.md)** - DecisionHistory 컨트랙트
- **[./settlement-system.md](./settlement-system.md)** - 정산 시스템
- **[../design/4_결정 기록, Commit Log.md](../design/4_결정 기록, Commit Log.md)** - 설계 문서

---

*최종 업데이트: 2025-12-29*
