# 탐색 리포트 사용법 (`src/explore/report.py`)

v0.1.0 탐색 MVP. 쌓인 스냅샷 DB(`data/db/predmarket.sqlite`)를 읽어
**급변 마켓 리스트**와 **확률 추이 차트**를 뽑는 CLI 스크립트.

## 실행

```bash
# 기본: 24h / 7d 급변 마켓 리스트 출력
.venv/bin/python src/explore/report.py

# 임계값 조정 (기본 0.10 = ±10%p)
.venv/bin/python src/explore/report.py --threshold 0.05

# 24h 급변 상위 N개 추이 차트 PNG 생성
.venv/bin/python src/explore/report.py --chart 3

# 특정 마켓 차트 (platform:market_ref 형식)
.venv/bin/python src/explore/report.py --market kalshi:KXFED-27APR-T2.25
```

의존성: `matplotlib` (requirements.txt에 포함, `.venv`에 설치됨).

## 출력 읽는 법

```
=== 급변 마켓 (최근 24h, 활성 116개 중 4개) ===
  +0.29  0.66 → 0.95  [kalshi] Will the upper bound ... — 2.25%
          (KXFED-27APR-T2.25)
```

- `+0.29` — window 동안의 yes_price 변화량(Δ). 변동폭 큰 순으로 정렬.
- `0.66 → 0.95` — window 이전 값 → 최신 값.
- 괄호 줄 — `market_ref`. `--market` 옵션에 그대로 쓸 수 있다.
- "활성" = 최근 12시간 내 스냅샷이 있는 마켓. 그보다 오래된(닫혔거나 필터 탈락) 마켓은
  비교 대상에서 빠진다 — 리스트에 없다고 데이터가 없는 게 아님.

## 동작 방식

- 기준 시각 = DB의 최신 스냅샷 시각 (실행 시각 아님).
- 각 마켓의 최신 yes_price를 24h(및 7d) 전 가장 가까운 스냅샷과 비교, |Δ| ≥ 임계값만 출력.
- 차트는 해당 마켓의 전체 수집 기간 yes_price 시계열 (y축 0~1 고정).

## 산출물 위치

차트 PNG는 `data/reports/{platform}_{market_ref}.png` — gitignore 대상 (재현 가능 산출물은 비추적, CLAUDE.md §0).
