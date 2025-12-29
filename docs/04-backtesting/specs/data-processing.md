# 데이터 처리 (Data Processing)

백테스팅을 위한 OHLCV 데이터 수집 및 전처리 상세 명세입니다.

---

## 1. 데이터 수집 (Data Collection)

### 1.1 ccxt 라이브러리

**ccxt**는 100+ 거래소 API를 통합한 Python 라이브러리입니다.

**설치**:
```bash
pip install ccxt
```

**지원 거래소**:
- Binance, Coinbase Pro, Kraken, Bitfinex
- Upbit, Bithumb (한국)
- 기타 100+ 거래소

---

### 1.2 OHLCV 데이터 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| `timestamp` | int | 밀리초 단위 타임스탬프 |
| `open` | float | 시가 (Open Price) |
| `high` | float | 고가 (High Price) |
| `low` | float | 저가 (Low Price) |
| `close` | float | 종가 (Close Price) |
| `volume` | float | 거래량 (Base Coin) |

**예시**:
```python
ohlcv = [
    [1609459200000, 29000.0, 29500.0, 28800.0, 29200.0, 123.45],
    # [timestamp, open, high, low, close, volume]
]
```

---

### 1.3 Pydantic Schema

```python
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

class OHLCVData(BaseModel):
    """OHLCV 데이터 단일 건"""
    timestamp: int = Field(..., gt=0, description="밀리초 타임스탬프")
    open: float = Field(..., gt=0, description="시가")
    high: float = Field(..., gt=0, description="고가")
    low: float = Field(..., gt=0, description="저가")
    close: float = Field(..., gt=0, description="종가")
    volume: float = Field(..., ge=0, description="거래량")

    @field_validator('high')
    def validate_high(cls, v, info):
        if 'low' in info.data and v < info.data['low']:
            raise ValueError('high must be >= low')
        return v

    @field_validator('low')
    def validate_low(cls, v, info):
        if 'high' in info.data and v > info.data['high']:
            raise ValueError('low must be <= high')
        return v

    @field_validator('timestamp')
    def convert_timestamp(cls, v):
        """타임스탬프를 datetime으로 변환"""
        return datetime.fromtimestamp(v / 1000, tz=datetime.timezone.utc)

class OHLCVRequest(BaseModel):
    """OHLCV 데이터 요청"""
    symbol: str = Field(..., pattern=r'^[A-Z]+/[A-Z]+$')
    timeframe: str = Field(..., pattern=r'^(\d+[mhd])$')
    start_date: datetime
    end_date: datetime
    limit: int = Field(default=1000, ge=1, le=1000)

    @field_validator('timeframe')
    def validate_timeframe(cls, v):
        valid = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if v not in valid:
            raise ValueError(f'timeframe must be one of {valid}')
        return v

class OHLCVResponse(BaseModel):
    """OHLCV 데이터 응답"""
    symbol: str
    timeframe: str
    data: List[OHLCVData]
    total_count: int
```

---

## 2. 데이터 수집 구현

### 2.1 Exchange Service

```python
import ccxt
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta

class ExchangeService:
    """거래소 데이터 서비스"""

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        # ccxt 거래소 초기화
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # API Rate Limit 자동 관리
            'options': {
                'defaultType': 'spot',  # spot, margin, futures
            }
        })

        # 한글 거래소 시간대 설정
        if exchange_id in ['upbit', 'bithumb']:
            self.exchange.timezone = 'Asia/Seoul'

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: int = 1000
    ) -> List[List]:
        """
        OHLCV 데이터 조회

        Args:
            symbol: 거래쌍 (예: 'BTC/USDT')
            timeframe: 캔들 간격 (예: '1h', '1d')
            since: 시작 타임스탬프 (밀리초)
            limit: 가져올 데이터 개수

        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            return ohlcv

        except ccxt.RateLimitExceeded:
            raise Exception("API Rate Limit exceeded. Please retry later.")
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    async def fetch_ohlcv_date_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[List]:
        """
        날짜 범위로 OHLCV 데이터 조회

        Args:
            symbol: 거래쌍
            timeframe: 캔들 간격
            start_date: 시작일
            end_date: 종료일

        Returns:
            전체 기간 OHLCV 데이터
        """
        all_data = []
        current_since = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)

        while current_since < end_timestamp:
            # 데이터 조회
            ohlcv = await self.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_since,
                limit=1000
            )

            if not ohlcv:
                break

            all_data.extend(ohlcv)

            # 마지막 타임스탬프 가져오기
            last_timestamp = ohlcv[-1][0]

            # 종료일 도달 시 중지
            if last_timestamp >= end_timestamp:
                break

            # 다음 배치 시작점
            current_since = last_timestamp + 1

            # Rate Limit 방지 딜레이
            await asyncio.sleep(0.1)

        return all_data

    def get_supported_symbols(self) -> List[str]:
        """지원하는 거래쌍 조회"""
        return self.exchange.symbols

    def get_timeframes(self) -> List[str]:
        """지원하는 타임프레임 조회"""
        return list(self.exchange.timeframes.keys())
```

---

### 2.2 FastAPI 엔드포인트

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/backtesting/data", tags=["backtesting-data"])

@router.post("/ohlcv/fetch", response_model=OHLCVResponse)
async def fetch_ohlcv_data(
    request: OHLCVRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    OHLCV 데이터 조회 엔드포인트

    - **symbol**: 거래쌍 (예: BTC/USDT)
    - **timeframe**: 캔들 간격 (1m, 5m, 15m, 1h, 4h, 1d)
    - **start_date**: 시작일
    - **end_date**: 종료일
    - **limit**: 한 번에 가져올 최대 데이터 개수
    """
    # 거래소 서비스 초기화
    exchange_service = ExchangeService(
        exchange_id="binance",
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET
    )

    try:
        # 데이터 조회
        raw_data = await exchange_service.fetch_ohlcv_date_range(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Pydantic 변환
        ohlcv_data = [
            OHLCVData(
                timestamp=row[0],
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5]
            )
            for row in raw_data
        ]

        return OHLCVResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            data=ohlcv_data,
            total_count=len(ohlcv_data)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        )
```

---

## 3. 데이터 전처리 (Data Preprocessing)

### 3.1 결측치 처리

**결측치 유형**:
- 거래소 장 마감으로 인한 누락 캔들
- 네트워크 오류로 인한 수집 실패
- 거래량 부족으로 인한 미체결

**처리 방법**:

| 방법 | 설명 | 사용 경우 |
|------|------|----------|
| `ffill` | 이전 값으로 채우기 | 일시적인 누락 |
| `bfill` | 이후 값으로 채우기 | 일시적인 누락 |
| `interpolate` | 선형 보간 | 짧은 구간 누락 |
| `drop` | 결측치 행 삭제 | 장기간 누락 |

```python
import pandas as pd

def handle_missing_data(
    df: pd.DataFrame,
    method: str = "ffill"
) -> pd.DataFrame:
    """
    결측치 처리

    Args:
        df: OHLCV DataFrame
        method: 'ffill', 'bfill', 'interpolate', 'drop'

    Returns:
        처리된 DataFrame
    """
    # 타임스탬프 인덱스 변환
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)

    # 결측치 처리
    if method == "ffill":
        df.fillna(method='ffill', inplace=True)
    elif method == "bfill":
        df.fillna(method='bfill', inplace=True)
    elif method == "interpolate":
        df.interpolate(method='linear', inplace=True)
    elif method == "drop":
        df.dropna(inplace=True)
    else:
        raise ValueError(f"Unknown method: {method}")

    return df
```

---

### 3.2 시간대 통일 (Timezone Normalization)

모든 데이터를 **UTC**로 변환하여 일관성 유지.

```python
import pytz

def normalize_timezone(df: pd.DataFrame, timezone: str = 'UTC') -> pd.DataFrame:
    """
    시간대 통일

    Args:
        df: datetime 컬럼이 있는 DataFrame
        timezone: 목표 시간대 (default: UTC)

    Returns:
        시간대가 변환된 DataFrame
    """
    tz = pytz.timezone(timezone)

    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

    # 로컬 시간대인 경우 UTC로 변환
    if df['datetime'].dt.tz is None:
        df['datetime'] = df['datetime'].dt.tz_localize(tz)
    else:
        df['datetime'] = df['datetime'].dt.tz_convert(tz)

    return df
```

---

### 3.3 데이터 검증

```python
class DataValidator:
    """데이터 검증기"""

    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> List[str]:
        """
        OHLCV 데이터 검증

        Returns:
            에러 메시지 리스트 (empty면 유효)
        """
        errors = []

        # 필수 컬럼 확인
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")

        # 고가 >= 저가 확인
        invalid_high_low = df[df['high'] < df['low']]
        if not invalid_high_low.empty:
            errors.append(f"{len(invalid_high_low)} rows have high < low")

        # 종가 범위 확인 (low <= close <= high)
        invalid_close = df[
            (df['close'] < df['low']) | (df['close'] > df['high'])
        ]
        if not invalid_close.empty:
            errors.append(f"{len(invalid_close)} rows have close outside [low, high]")

        # 음수 가격 확인
        negative_prices = df[
            (df['open'] <= 0) | (df['high'] <= 0) |
            (df['low'] <= 0) | (df['close'] <= 0)
        ]
        if not negative_prices.empty:
            errors.append(f"{len(negative_prices)} rows have non-positive prices")

        # 거래량 음수 확인
        negative_volume = df[df['volume'] < 0]
        if not negative_volume.empty:
            errors.append(f"{len(negative_volume)} rows have negative volume")

        # 중복 타임스탬프 확인
        duplicates = df[df.duplicated(subset=['timestamp'], keep=False)]
        if not duplicates.empty:
            errors.append(f"{len(duplicates)} duplicate timestamps found")

        return errors

    @staticmethod
    def validate_date_range(
        df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """날짜 범위 검증"""
        errors = []

        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # 시작일 이전 데이터 확인
        before_start = df[df['datetime'] < start_date]
        if not before_start.empty:
            errors.append(f"{len(before_start)} rows before start_date")

        # 종료일 이후 데이터 확인
        after_end = df[df['datetime'] > end_date]
        if not after_end.empty:
            errors.append(f"{len(after_end)} rows after end_date")

        return errors
```

---

## 4. 데이터 저장 (Data Storage)

### 4.1 Database Schema

```sql
-- OHLCV 데이터 테이블
CREATE TABLE ohlcv_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,        -- BTC/USDT
    timeframe VARCHAR(10) NOT NULL,      -- 1h, 4h, 1d
    timestamp BIGINT NOT NULL,           -- 밀리초
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timeframe, timestamp)
);

-- 인덱스
CREATE INDEX idx_ohlcv_symbol_time
    ON ohlcv_data(symbol, timeframe, timestamp);

CREATE INDEX idx_ohlcv_date_range
    ON ohlcv_data(
        symbol,
        timeframe,
        to_timestamp(timestamp / 1000)
    );
```

---

### 4.2 Repository 구현

```python
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from app.models.ohlcv import OHLCVData

class OHLCVRepository:
    """OHLCV 데이터 Repository"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_many(
        self,
        symbol: str,
        timeframe: str,
        data: List[OHLCVData]
    ) -> int:
        """
        일괄 삽입/업데이트 (Upsert)

        Returns:
            삽입/업데이트된 행 수
        """
        values = [
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": d.timestamp,
                "open": d.open,
                "high": d.high,
                "low": d.low,
                "close": d.close,
                "volume": d.volume
            }
            for d in data
        ]

        stmt = insert(OHLCVData).values(values)
        stmt = stmt.on_conflict_do_update(
            index_params=['symbol', 'timeframe', 'timestamp'],
            set_={
                'open': stmt.excluded.open,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'close': stmt.excluded.close,
                'volume': stmt.excluded.volume
            }
        )

        await self.db.execute(stmt)
        await self.db.commit()

        return len(values)

    async def fetch_date_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLCVData]:
        """날짜 범위로 데이터 조회"""
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        result = await self.db.execute(
            select(OHLCVData).where(
                OHLCVData.symbol == symbol,
                OHLCVData.timeframe == timeframe,
                OHLCVData.timestamp >= start_ts,
                OHLCVData.timestamp <= end_ts
            ).order_by(OHLCVData.timestamp)
        )

        return result.scalars().all()

    async def delete_date_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """날짜 범위 데이터 삭제"""
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        result = await self.db.execute(
            delete(OHLCVData).where(
                OHLCVData.symbol == symbol,
                OHLCVData.timeframe == timeframe,
                OHLCVData.timestamp >= start_ts,
                OHLCVData.timestamp <= end_ts
            )
        )

        await self.db.commit()
        return result.rowcount
```

---

## 5. 파이프라인 구현

### 5.1 전체 데이터 처리 파이프라인

```python
from app.services.exchange import ExchangeService
from app.repositories.ohlcv import OHLCVRepository
from app.services.data_processor import DataProcessor

class BacktestDataPipeline:
    """백테스팅 데이터 파이프라인"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.exchange = ExchangeService()
        self.repository = OHLCVRepository(db)
        self.processor = DataProcessor()

    async def fetch_and_store(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        데이터 수집 → 전처리 → 저장 파이프라인

        Returns:
            처리 결과 통계
        """
        # 1. 데이터 수집
        raw_data = await self.exchange.fetch_ohlcv_date_range(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )

        if not raw_data:
            return {
                "status": "no_data",
                "message": "No data found for the given range"
            }

        # 2. Pydantic 변환
        ohlcv_data = [
            OHLCVData(
                timestamp=row[0],
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5]
            )
            for row in raw_data
        ]

        # 3. 데이터 검증
        df = pd.DataFrame([d.dict() for d in ohlcv_data])
        errors = DataValidator.validate_ohlcv(df)

        if errors:
            return {
                "status": "validation_failed",
                "errors": errors
            }

        # 4. 전처리
        df = self.processor.handle_missing_data(df, method="ffill")
        df = self.processor.normalize_timezone(df, timezone="UTC")

        # 5. 저장
        count = await self.repository.upsert_many(
            symbol=symbol,
            timeframe=timeframe,
            data=ohlcv_data
        )

        return {
            "status": "success",
            "symbol": symbol,
            "timeframe": timeframe,
            "records_processed": count,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
```

---

## 6. 환경 변수

```bash
# .env
# 거래소 API
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# 데이터 처리 설정
DEFAULT_TIMEZONE=UTC
MISSING_DATA_METHOD=ffill
MAX_FETCH_LIMIT=1000
RATE_LIMIT_DELAY=0.1  # 초
```

---

## 7. 상위/관련 문서

- **[../index.md](../index.md)** - 백테스팅 개요
- **[indicators.md](./indicators.md)** - 기술적 지표 계산
- **[simulation.md](./simulation.md)** - 시뮬레이션 엔진

---

*최종 업데이트: 2025-12-29*
