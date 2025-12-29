# 전략 검증 규칙 (Validation Rules)

전략 정의(Node-Edge 구조)의 유효성을 검증하는 규칙과 구현입니다.

---

## 1. 구조적 검증 (Structural Validation)

전략의 기본 구조가 유효한지 검증합니다.

### 1.1 트리거 노드 단일 확인

**규칙**: 전략에는 정확히 1개의 트리거 노드가 존재해야 합니다.

**에러 코드**: `MULTIPLE_TRIGGERS` 또는 `NO_TRIGGER`

**Python 구현**:
```python
from typing import List
from pydantic import BaseModel, field_validator, ValidationError

class Node(BaseModel):
    id: str
    type: str
    config: dict

class Edge(BaseModel):
    from_node: str
    to_node: str
    condition: str | None = None

class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_single_trigger(cls, v):
        triggers = [n for n in v if n.type == 'trigger']
        if len(triggers) == 0:
            raise ValueError(
                "전략에 트리거 노드가 없습니다. "
                "전략 실행을 시작하려면 트리거 노드가 필요합니다."
            )
        if len(triggers) > 1:
            raise ValueError(
                f"전략에 {len(triggers)}개의 트리거 노드가 있습니다. "
                "트리거 노드는 정확히 1개만 허용됩니다."
            )
        return v
```

**에러 응답**:
```json
{
  "error_code": "MULTIPLE_TRIGGERS",
  "message": "전략에 2개의 트리거 노드가 있습니다.",
  "details": {
    "trigger_nodes": ["trigger_1", "trigger_2"],
    "resolution": "하나의 트리거 노드만 유지하고 나머지를 삭제하세요."
  }
}
```

---

### 1.2 필수 노드 존재 확인

**규칙**: 전략에는 최소 1개의 액션 노드가 존재해야 합니다.

**에러 코드**: `NO_ACTION_NODE`

**Python 구현**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_action_exists(cls, v):
        actions = [n for n in v if n.type == 'action']
        if len(actions) == 0:
            raise ValueError(
                "전략에 액션 노드가 없습니다. "
                "매수/매도/알림 등 최소 1개의 액션이 필요합니다."
            )
        return v
```

**에러 응답**:
```json
{
  "error_code": "NO_ACTION_NODE",
  "message": "전략에 액션 노드가 없습니다.",
  "details": {
    "resolution": "매수/매도/알림 액션 노드를 추가하세요."
  }
}
```

---

### 1.3 노드 ID 유일성

**규칙**: 모든 노드 ID는 유일해야 합니다.

**에러 코드**: `DUPLICATE_NODE_ID`

**Python 구현**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_unique_ids(cls, v):
        ids = [n.id for n in v]
        duplicates = [id for id in ids if ids.count(id) > 1]

        if duplicates:
            unique_duplicates = list(set(duplicates))
            raise ValueError(
                f"중복된 노드 ID가 있습니다: {', '.join(unique_duplicates)}"
            )
        return v
```

---

### 1.4 엣지 노드 참조 유효성

**규칙**: 엣지의 `from`, `to`는 존재하는 노드 ID를 참조해야 합니다.

**에러 코드**: `INVALID_EDGE_REFERENCE`

**Python 구현**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('edges')
    def validate_edge_references(cls, v, info):
        if 'nodes' not in info.data:
            return v  # nodes 검증이 먼저 실행되므로

        node_ids = {n.id for n in info.data['nodes']}
        invalid_refs = []

        for edge in v:
            if edge.from_node not in node_ids:
                invalid_refs.append(f"{edge.from_node} (from)")
            if edge.to_node not in node_ids:
                invalid_refs.append(f"{edge.to_node} (to)")

        if invalid_refs:
            raise ValueError(
                f"엣지가 존재하지 않는 노드를 참조합니다: {', '.join(invalid_refs)}"
            )
        return v
```

**에러 응답**:
```json
{
  "error_code": "INVALID_EDGE_REFERENCE",
  "message": "엣지가 존재하지 않는 노드를 참조합니다.",
  "details": {
    "invalid_references": ["node_999 (from)", "node_888 (to)"],
    "resolution": "엣지를 삭제하거나 올바른 노드 ID로 수정하세요."
  }
}
```

---

## 2. 순환 감지 (Cycle Detection)

전략 그래프에 순환(cycle)이 존재하는지 감지합니다.

### 2.1 DFS (Depth-First Search) 기반 순환 감지

**규칙**: 전략 그래프는 DAG(Directed Acyclic Graph)여야 합니다.

**에러 코드**: `CYCLE_DETECTED`

**Python 구현**:
```python
from typing import Dict, List, Set
from collections import defaultdict

class CycleDetector:
    def __init__(self, nodes: List[Node], edges: List[Edge]):
        self.nodes = nodes
        self.edges = edges
        self.adj_list = self._build_adjacency_list()

    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """인접 리스트 구축"""
        adj = defaultdict(list)
        for edge in self.edges:
            adj[edge.from_node].append(edge.to_node)
        return dict(adj)

    def has_cycle(self) -> bool:
        """순환 존재 여부 확인 (DFS)"""
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            # 인접 노드 순회
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True  # 순환 발견

            rec_stack.remove(node)
            return False

        # 모든 노드에 대해 DFS 실행
        for node in self.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True
        return False

    def find_cycle_path(self) -> List[str] | None:
        """순환 경로 반환"""
        visited = set()
        rec_stack = {}
        path = []

        def dfs(node: str, current_path: List[str]) -> List[str] | None:
            visited.add(node)
            rec_stack[node] = len(current_path)
            current_path.append(node)

            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor, current_path[:])
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # 순환 발견: 경로 추적
                    cycle_start = rec_stack[neighbor]
                    return current_path[cycle_start:] + [neighbor]

            current_path.pop()
            del rec_stack[node]
            return None

        for node in self.nodes:
            if node.id not in visited:
                cycle = dfs(node.id, [])
                if cycle:
                    return cycle
        return None
```

**Pydantic 통합**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes', 'edges')
    def validate_no_cycle(cls, v, info):
        if not all(key in info.data for key in ['nodes', 'edges']):
            return v

        detector = CycleDetector(info.data['nodes'], info.data['edges'])

        if detector.has_cycle():
            cycle_path = detector.find_cycle_path()
            raise ValueError(
                f"전략 그래프에 순환이 감지되었습니다: {' → '.join(cycle_path)}"
            )
        return v
```

**에러 응답**:
```json
{
  "error_code": "CYCLE_DETECTED",
  "message": "전략 그래프에 순환이 감지되었습니다.",
  "details": {
    "cycle_path": ["condition_1", "indicator_1", "condition_1"],
    "resolution": "순환 경로의 엣지 중 하나를 삭제하여 순환을 제거하세요."
  }
}
```

---

### 2.2 위상 정렬 (Topological Sort)

**설명**: 순환 감지와 노드 실행 순서 결정을 동시에 수행합니다.

**Python 구현**:
```python
from collections import deque

class TopologicalSort:
    def __init__(self, nodes: List[Node], edges: List[Edge]):
        self.nodes = nodes
        self.edges = edges
        self.in_degree = self._calculate_in_degree()
        self.adj_list = self._build_adjacency_list()

    def _calculate_in_degree(self) -> Dict[str, int]:
        """진입 차수 계산"""
        in_degree = {n.id: 0 for n in self.nodes}
        for edge in self.edges:
            in_degree[edge.to_node] += 1
        return in_degree

    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """인접 리스트 구축"""
        adj = defaultdict(list)
        for edge in self.edges:
            adj[edge.from_node].append(edge.to_node)
        return dict(adj)

    def sort(self) -> List[str] | None:
        """위상 정렬 수행, 순환 시 None 반환"""
        queue = deque([node for node, degree in self.in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor in self.adj_list.get(node, []):
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            return None  # 순환 존재

        return result
```

---

## 3. 타입 검증 (Type Validation)

노드 간 데이터 흐름의 타입 호환성을 검증합니다.

### 3.1 노드 출력 타입 정의

**Python 구현**:
```python
from typing import TypedDict, Literal, Type, get_args, get_origin
from enum import Enum

class DataType(str, Enum):
    """노드 출력 데이터 타입"""
    # 기본 타입
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STR = "str"

    # 복합 타입
    OHLCV = "ohlcv"
    ORDERBOOK = "orderbook"
    NEWS = "news"
    INDICATOR = "indicator"
    LLM_ANALYSIS = "llm_analysis"
    LLM_SENTIMENT = "llm_sentiment"

    # 특수 타입
    ANY = "any"
    NULL = "null"

class NodeTypeOutput(TypedDict):
    """노드 타입별 출력 데이터"""
    main: DataType
    fields: dict[str, DataType]

# 노드 타입별 출력 정의
NODE_OUTPUTS: dict[str, NodeTypeOutput] = {
    "trigger": {
        "main": DataType.NULL,
        "fields": {}
    },
    "data_source": {
        "main": DataType.ANY,
        "fields": {
            "ohlcv": DataType.OHLCV,
            "orderbook": DataType.ORDERBOOK,
            "news": DataType.NEWS
        }
    },
    "indicator": {
        "main": DataType.INDICATOR,
        "fields": {
            "value": DataType.FLOAT
        }
    },
    "condition": {
        "main": DataType.BOOL,
        "fields": {
            "result": DataType.BOOL
        }
    },
    "llm": {
        "main": DataType.ANY,
        "fields": {
            "analysis": DataType.LLM_ANALYSIS,
            "sentiment": DataType.LLM_SENTIMENT
        }
    },
    "action": {
        "main": DataType.NULL,
        "fields": {}
    }
}
```

---

### 3.2 조건 노드 타입 검증

**규칙**: 조건 노드의 `left`, `right` 피연산자는 호환 가능한 타입이어야 합니다.

**에러 코드**: `TYPE_MISMATCH`

**Python 구현**:
```python
class TypeValidator:
    def __init__(self, nodes: List[Node], edges: List[Edge]):
        self.nodes = nodes
        self.edges = edges
        self.node_map = {n.id: n for n in nodes}

    def get_node_output_type(self, node_id: str, field: str | None = None) -> DataType:
        """노드의 출력 타입 조회"""
        node = self.node_map.get(node_id)
        if not node:
            return DataType.NULL

        output_def = NODE_OUTPUTS.get(node.type)
        if not output_def:
            return DataType.ANY

        if field:
            return output_def["fields"].get(field, DataType.ANY)
        return output_def["main"]

    def parse_operand(self, operand: str) -> tuple[str | None, str | None, DataType]:
        """피연산자 파싱: (node_id, field, type)"""
        # 리터럴 값 확인
        try:
            return None, None, DataType.FLOAT
        except:
            pass

        if operand.lower() in ['true', 'false']:
            return None, None, DataType.BOOL

        # 노드 참조: "node_id.field" 또는 "node_id"
        if '.' in operand:
            node_id, field = operand.split('.', 1)
            return node_id, field, self.get_node_output_type(node_id, field)
        else:
            return operand, None, self.get_node_output_type(operand)

    def validate_condition_node(self, node: Node) -> bool:
        """조건 노드 타입 검증"""
        if node.type != "condition":
            return True

        config = node.config

        # 단일 조건
        if "operator" in config:
            left_type = self.parse_operand(config["left"])[2]
            right_type = self.parse_operand(config["right"])[2]

            if not self.are_types_compatible(left_type, right_type):
                raise ValueError(
                    f"조건 노드 {node.id}: 타입 불일치. "
                    f"left={left_type}, right={right_type}"
                )

        # 복합 조건
        elif "conditions" in config:
            for cond in config["conditions"]:
                left_type = self.parse_operand(cond["left"])[2]
                right_type = self.parse_operand(cond["right"])[2]

                if not self.are_types_compatible(left_type, right_type):
                    raise ValueError(
                        f"조건 노드 {node.id}: 복합 조건 내 타입 불일치. "
                        f"left={left_type}, right={right_type}"
                    )

        return True

    @staticmethod
    def are_types_compatible(type1: DataType, type2: DataType) -> bool:
        """타입 호환성 확인"""
        if type1 == DataType.ANY or type2 == DataType.ANY:
            return True

        numeric_types = {DataType.FLOAT, DataType.INT, DataType.INDICATOR}
        if type1 in numeric_types and type2 in numeric_types:
            return True

        return type1 == type2
```

**Pydantic 통합**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_types(cls, v, info):
        if 'edges' not in info.data:
            return v

        validator = TypeValidator(info.data['nodes'], info.data['edges'])

        for node in v:
            validator.validate_condition_node(node)

        return v
```

**에러 응답**:
```json
{
  "error_code": "TYPE_MISMATCH",
  "message": "조건 노드에서 타입 불일치가 발생했습니다.",
  "details": {
    "node_id": "condition_1",
    "left": "indicator_1.value (indicator)",
    "right": "text_value (str)",
    "resolution": "피연산자의 타입을 일치시키세요."
  }
}
```

---

## 4. 비즈니스 규칙 (Business Rules)

비즈니스 로직과 관련된 제약 조건을 검증합니다.

### 4.1 리스크 관리 필수

**규칙**: 매수/매도 액션에는 반드시 손절(Stop Loss) 또는 익절(Take Profit)이 설정되어야 합니다.

**에러 코드**: `NO_RISK_MANAGEMENT`

**Python 구현**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_risk_management(cls, v):
        action_nodes = [n for n in v if n.type == 'action']

        for action in action_nodes:
            config = action.config

            # 매수/매도 액션 확인
            if config.get('action_type') in ['buy', 'sell']:
                # 리스크 관리 노드 확인 로직
                # (실제로는 엣지를 따라가면서 확인 필요)
                pass

        return v
```

---

### 4.2 최대 전략 복잡도

**규칙**: 전략의 복잡도를 제한하여 성능 문제 방지.

**제약**:
| 항목 | 제한 |
|------|------|
| 최대 노드 수 | 50 |
| 최대 엣지 수 | 100 |
| 최대 조건 깊이 | 10 |

**에러 코드**: `STRATEGY_TOO_COMPLEX`

**Python 구현**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_complexity(cls, v):
        if len(v) > 50:
            raise ValueError(
                f"전략이 너무 복잡합니다. 최대 50개 노드 허용, 현재 {len(v)}개"
            )
        return v

    @field_validator('edges')
    def validate_edge_count(cls, v):
        if len(v) > 100:
            raise ValueError(
                f"엣지가 너무 많습니다. 최대 100개 엣지 허용, 현재 {len(v)}개"
            )
        return v
```

---

### 4.3 LLM 사용량 제한

**규칙**: 전략 내 LLM 노드 수를 제한하여 비용 과다 지출 방지.

**제약**: 전략당 최대 5개 LLM 노드

**에러 코드**: `TOO_MANY_LLM_NODES`

**Python 구현**:
```python
class StrategyDefinition(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    @field_validator('nodes')
    def validate_llm_usage(cls, v):
        llm_nodes = [n for n in v if n.type == 'llm']

        if len(llm_nodes) > 5:
            raise ValueError(
                f"LLM 노드가 너무 많습니다. 최대 5개 허용, 현재 {len(llm_nodes)}개"
            )
        return v
```

---

## 5. 통합 검증기 (Integrated Validator)

모든 검증 규칙을 통합한 클래스입니다.

```python
from pydantic import BaseModel, ValidationError

class StrategyValidator:
    """전략 검증 통합 클래스"""

    def __init__(self, strategy_dict: dict):
        self.strategy_dict = strategy_dict
        self.errors = []

    def validate(self) -> tuple[bool, list[str]]:
        """모든 검증 규칙 실행"""
        try:
            # Pydantic 검증 (구조적 검증)
            strategy = StrategyDefinition(**self.strategy_dict)

            # 순환 감지
            detector = CycleDetector(strategy.nodes, strategy.edges)
            if detector.has_cycle():
                cycle_path = detector.find_cycle_path()
                self.errors.append(
                    f"CYCLE_DETECTED: {' → '.join(cycle_path)}"
                )

            # 타입 검증
            type_validator = TypeValidator(strategy.nodes, strategy.edges)
            for node in strategy.nodes:
                try:
                    type_validator.validate_condition_node(node)
                except ValueError as e:
                    self.errors.append(f"TYPE_MISMATCH: {str(e)}")

            return len(self.errors) == 0, self.errors

        except ValidationError as e:
            # Pydantic 검증 에러
            errors = []
            for error in e.errors():
                loc = " → ".join(str(l) for l in error['loc'])
                errors.append(f"{loc}: {error['msg']}")
            return False, errors

    def validate_for_deployment(self) -> tuple[bool, dict]:
        """배포 전 검증 (엄격 모드)"""
        is_valid, errors = self.validate()

        if not is_valid:
            return False, {
                "valid": False,
                "errors": errors,
                "resolution": "검증 에러를 수정한 후 다시 시도하세요."
            }

        # 배포 전 추가 검증
        # (예: 사용자 할당량, API 키 존재 등)

        return True, {
            "valid": True,
            "warnings": []
        }
```

---

## 6. FastAPI 엔드포인트 통합

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

class ValidateRequest(BaseModel):
    strategy: dict

class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] | None = None
    warnings: list[str] | None = None

@router.post("/validate", response_model=ValidateResponse)
async def validate_strategy(request: ValidateRequest):
    """전략 검증 엔드포인트"""
    validator = StrategyValidator(request.strategy)
    is_valid, errors = validator.validate()

    if not is_valid:
        return ValidateResponse(
            valid=False,
            errors=errors
        )

    return ValidateResponse(
        valid=True,
        warnings=[]
    )

class DeployRequest(BaseModel):
    strategy_id: str

@router.post("/strategies/{strategy_id}/deploy")
async def deploy_strategy(strategy_id: str, request: DeployRequest):
    """전략 배포 엔드포인트"""
    # DB에서 전략 조회
    strategy = await get_strategy(strategy_id)

    # 검증
    validator = StrategyValidator(strategy.definition)
    is_valid, result = validator.validate_for_deployment()

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "STRATEGY_VALIDATION_FAILED",
                "message": "전략 검증에 실패했습니다.",
                "details": result
            }
        )

    # 배포 로직 계속...
    return {"status": "deployed"}
```

---

## 7. 에러 코드 참조

| 에러 코드 | 설명 | 해결 방안 |
|----------|------|----------|
| `MULTIPLE_TRIGGERS` | 트리거 노드가 2개 이상 | 하나의 트리거만 유지 |
| `NO_TRIGGER` | 트리거 노드 없음 | 트리거 노드 추가 |
| `NO_ACTION_NODE` | 액션 노드 없음 | 매수/매도/알림 노드 추가 |
| `DUPLICATE_NODE_ID` | 중복된 노드 ID | 노드 ID 변경 |
| `INVALID_EDGE_REFERENCE` | 존재하지 않는 노드 참조 | 엣지 수정 또는 노드 추가 |
| `CYCLE_DETECTED` | 그래프 순환 존재 | 순환 경로의 엣지 삭제 |
| `TYPE_MISMATCH` | 조건 노드 타입 불일치 | 피연산자 타입 일치 |
| `STRATEGY_TOO_COMPLEX` | 전략 복잡도 초과 | 노드/엣지 수 줄이기 |
| `TOO_MANY_LLM_NODES` | LLM 노드 수 초과 | LLM 노드 수 줄이기 |
| `NO_RISK_MANAGEMENT` | 리스크 관리 미설정 | 손절/익절 설정 |

---

## 8. 상위/관련 문서

- **[../index.md](../index.md)** - 전략 시스템 개요
- **[node-types.md](./node-types.md)** - 노드 타입 상세
- **[execution-engine.md](./execution-engine.md)** - 실행 엔진 상세

---

*최종 업데이트: 2025-12-29*
