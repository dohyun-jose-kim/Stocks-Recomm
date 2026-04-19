# 01. 데이터 수집 — 예측시장

**우선순위**: 최우선 (과거 데이터 없음, 지금부터 쌓아야 함)

---

## 태스크

### T1.1 Polymarket 수집기
- [ ] Gamma API로 활성 이벤트 목록 가져오기
  ```
  GET https://gamma-api.polymarket.com/events?active=true&closed=false&limit=50
  ```
  인증: 불필요
- [ ] 관심 카테고리 필터링 (Economics, Politics, Fed, Geopolitics)
- [ ] 마켓별 outcomePrices(내재확률) 파싱
- [ ] 30분 간격 스냅샷 저장
- [ ] 에러 처리: API 응답 실패 시 로그 남기고 다음 주기에 재시도 (크래시 방지)
  - → verify: curl 테스트 성공 + DB에 스냅샷 2건 이상 + 30분 간격 확인

### T1.2 Kalshi 수집기
- [ ] Trade API로 활성 마켓 목록 가져오기
  ```
  GET https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=100
  ```
  인증: 불필요 (읽기)
- [ ] 관심 시리즈 필터링: KXFED, KXCPI, KXJOBS, KXGDP, KXRECESSION, KXSP500
- [ ] yes_bid/yes_ask(내재확률) 파싱
- [ ] 30분 간격 스냅샷 저장
- [ ] 에러 처리: 위와 동일
  - → verify: curl 테스트 성공 + DB에 스냅샷 2건 이상

### T1.3 크로스 플랫폼 매칭 (MVP 이후)
- [ ] Polymarket-Kalshi 동일 이벤트 수동 매핑 테이블 작성
  - Fed 금리, CPI, GDP 등 겹치는 이벤트 식별
- [ ] 매핑 테이블을 config/prediction_markets.yaml에 저장
- 수집이 안정적으로 돌아간 후 진행. 수집기 MVP에는 불필요.

### T1.4 수집 검증
- [ ] 24시간 운영 후 점검:
  - → verify: 48개 스냅샷(30분×24시간) ±10% 범위, 빈 스냅샷 없음

---

## 의존성
- DB 스키마 필요 → [05_infra.md](05_infra.md) T5.1
- 스케줄링 필요 → [05_infra.md](05_infra.md) T5.3

## 산출물
- `collector/polymarket.py`
- `collector/kalshi.py`
- `config/prediction_markets.yaml`
