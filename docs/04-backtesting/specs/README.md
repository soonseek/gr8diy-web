# Backtesting Specs

이 디렉토리에는 백테스팅 시스템의 상세 명세가 작성됩니다.

## 예상 문서 목록

| 문서 | 설명 |
|------|------|
| `data-processing.md` | OHLCV 데이터 수집, 전처리 (결측치 처리, UTC 통일) |
| `indicators.md` | 기술적 지표 계산 (RSI, MACD, 볼린저 밴드, 이동평균선) |
| `simulation.md` | 시뮬레이션 엔진 (캔들 순회, 조건 평가, 매수/매도 시뮬레이션) |
| `performance-metrics.md` | 성과 지표 계산식 (총 수익률, MDD, 승률, 샤프 비율) |
| `commission-slippage.md` | 수수료, 슬리피지 모델 (Maker 0.1%, Taker 0.1%, 시장가 0.05%) |

## 상위 문서

- **[../index.md](../index.md)** - 백테스팅 개요 및 설계 통합
