# 02. 데이터 수집 — 뉴스

**우선순위**: 최우선 (예측시장과 병렬 진행)

---

## 스코프 결정

미국 뉴스 범위: **미국 시장은 예측시장(01) + 가격(03)으로 커버. 뉴스 수집은 한국 중심.**
미국 뉴스가 필요해지면 Phase 2에서 추가.

---

## 태스크

### T2.1 네이버 뉴스 검색 API
- [ ] 네이버 개발자센터 Client ID/Secret 발급
- [ ] 검색 키워드 리스트 확정 (config/watchlist.yaml)
  - 시장: "코스피", "코스닥", "금리", "환율"
  - 기관: "한국은행", "금융위", "연준", "FOMC"
  - 이슈: "트럼프", "관세", "반도체", "2차전지"
  - 종목: watchlist 기반
  - → verify: watchlist.yaml에 키워드 10개 이상, 카테고리 구분 존재
- [ ] 수집기 구현: 키워드별 최신 뉴스 가져오기
- [ ] 중복 제거: originallink URL 해시
- [ ] 30분 간격 스케줄
  - → verify: 수집 1회 실행 후 DB에 뉴스 10건 이상, 중복 URL 0건

**제약**: 일 25,000회, 한번에 최대 100건, start 최대 1000

### T2.2 RSS 피드 수집기
- [ ] feedparser로 RSS 폴링
- [ ] 소스 목록:
  - 이투데이 증권: `etoday.co.kr/rss/section/stock.xml`
  - 이데일리: `edaily.co.kr/rss/`
  - 한국경제: `hankyung.com/feed/`
  - 연합뉴스 경제: `yna.co.kr/rss/economy.xml`
- [ ] URL 기반 중복 제거 (네이버와도 교차 체크)
- [ ] 30분 간격
  - → verify: RSS 4개 소스 모두에서 기사 수집 확인

---

## 의존성
- 네이버 API 키 발급 (수동, 선행 필요)
- DB 스키마 → [05_infra.md](05_infra.md) T5.2 확장 스키마

## 산출물
- `collector/naver_news.py`
- `collector/rss_feed.py`
- `config/watchlist.yaml`
