# 01. 수집기 — Polymarket + Kalshi

**우선순위**: 최우선. 지금부터 안 쌓으면 시계열 분석 자체가 불가능.

---

## T1. Polymarket 수집기

- [ ] Gamma API로 활성 이벤트 목록 가져오기
  ```
  GET https://gamma-api.polymarket.com/events?active=true&closed=false&limit=50
  ```
  인증: 불필요
- [ ] 관심 카테고리 필터 (Economics, Politics, Fed, Geopolitics 등 — 처음엔 넓게)
- [ ] 마켓별 `outcomePrices`(내재확률) 파싱
- [ ] 30분 간격 스냅샷 저장
- [ ] 에러 처리: 응답 실패 시 로그 + 다음 주기 재시도 (크래시 방지)

→ verify: curl 테스트 성공 + DB에 스냅샷 2건 이상 + 30분 간격 확인

## T2. Kalshi 수집기

- [ ] Trade API로 활성 마켓 목록
  ```
  GET https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=100
  ```
  인증: 읽기는 불필요
- [ ] 관심 시리즈 필터: 후보 — `KXFED`, `KXCPI`, `KXJOBS`, `KXGDP`, `KXRECESSION`, `KXSP500`
  - 코드는 시간에 따라 바뀔 수 있음. 구현 직전 한 번 더 확인 필요.
- [ ] `yes_bid`/`yes_ask`(내재확률) 파싱
- [ ] 30분 간격 스냅샷 저장
- [ ] 에러 처리: 위와 동일

→ verify: curl 테스트 성공 + DB에 스냅샷 2건 이상

## T3. 운영 검증 (24시간)

- [ ] 24시간 무중단 실행 후 점검
  - 48개 스냅샷(30분 × 24시간) ±10% 범위
  - 빈 스냅샷 없음
  - 에러 로그 수동 검토

→ verify: 위 조건 통과

## T4. 크로스 플랫폼 매핑 (나중에)

수집이 안정적으로 돌고 나서:
- [ ] Polymarket–Kalshi 동일 이벤트 수동 매핑 테이블 (`config/cross_market.yaml`)
- 예: Fed 금리 결정, CPI 발표, GDP, 경기침체 확률

**MVP에서는 안 함.** 두 플랫폼 데이터가 따로 쌓여 있기만 하면 됨.

---

## 산출물

- `src/collector/polymarket.py`
- `src/collector/kalshi.py`
- `src/config/markets.yaml` (관심 카테고리/시리즈 화이트리스트)

## 의존성

- DB 스키마 → [02_storage.md](02_storage.md) T1
- 스케줄 → [02_storage.md](02_storage.md) T3
