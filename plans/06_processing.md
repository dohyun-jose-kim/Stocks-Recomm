# 06. 데이터 전처리

**우선순위**: 중간 (수집 시작 후, 분석 전)

---

## 태스크

### T6.1 뉴스 전처리
- [ ] HTML 태그 제거 (BeautifulSoup)
- [ ] 중복 제거 (URL 해시)
- [ ] 종목 태깅 (정규식 + 종목 사전)
  - "삼성전자" → 005930
  - "AAPL", "Apple" → AAPL
- [ ] 타임스탬프 정규화
  - KST 통일
  - 장중/장후 구분 (15:30 KST 기준)
  - → verify: 전처리 후 중복 URL 0건, 타임스탬프 전부 KST

### T6.2 예측시장 전처리
- [ ] 이상치 필터링 (유동성 극히 낮은 마켓 제외)
- [ ] Polymarket-Kalshi 동일 이벤트 시계열 정렬 (타임존 UTC 통일)
  - → verify: 동일 이벤트의 두 플랫폼 스냅샷이 같은 시간축에 정렬

### T6.3 가격 데이터 전처리
- [ ] 수정주가 검증
- [ ] 수익률 계산: 일간
- [ ] 거래일 정렬 (한국/미국 거래일 차이)
  - → verify: 한국/미국 휴장일에 데이터 없음 확인
- 기술지표(MA, RSI, MACD 등)는 분석 단계에서 필요해지면 추가

### T6.4 수동 데이터 임포트 (필요 시)
- CSV/Excel: pandas로 읽어서 DB에 넣는 스크립트
- PDF: 실제 파일을 보고 나서 파서 작성 여부 결정
  - → verify: CSV 1개 임포트 후 DB에 데이터 존재

---

## 산출물
- `processor/news_cleaner.py`
- `processor/market_snapshot.py`
- `processor/price_features.py`
