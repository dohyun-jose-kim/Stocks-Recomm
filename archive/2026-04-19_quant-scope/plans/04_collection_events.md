# 04. 데이터 수집 — 이벤트 캘린더

**우선순위**: 높음 (이벤트 드리븐 분석의 기반)

---

## 태스크

### T4.1 데이터 소스 검증 (구현 전 필수)
- [ ] FRED 릴리즈 캘린더 API 테스트
  - `curl "https://api.stlouisfed.org/fred/releases/dates?api_key=...&limit=5"` 실행
  - → verify: CPI, 고용, GDP 발표일이 포함된 JSON 응답 확인
- [ ] 한국은행/통계청 캘린더 API 존재 여부 조사
  - → verify: API 있으면 엔드포인트 확인, 없으면 "수동 입력" 확정
- [ ] DART 공시 API 테스트
  - `curl` 로 최근 공시 목록 호출
  - → verify: 관심 종목의 공시 내역이 오는지 확인
- [ ] yfinance `.earnings_dates` 테스트
  - → verify: 빅테크 3개 종목 실적 발표일 가져와지는지 확인

**이 태스크 완료 후, 아래 구현 태스크의 범위가 결정됨.**

---

### T4.2 미국 경제 이벤트 캘린더 (T4.1 결과에 따라)
- [ ] FRED API로 주요 지표 발표일 수집: CPI, 고용, GDP
- [ ] FOMC 회의 일정 (Fed 공식 캘린더 — 연간 고정이라 수동 입력도 가능)
- [ ] 수집 대상: 이벤트명, 예정일, 실제 발표일
  - → verify: 향후 3개월 이벤트가 DB에 존재

### T4.3 한국 경제 이벤트 (T4.1 결과에 따라)
- [ ] API 있으면: 금통위, 주요 지표 발표일 자동 수집
- [ ] API 없으면: 한국은행/통계청 홈페이지에서 수동 입력 (연간 일정)
  - → verify: 향후 3개월 한국 경제 이벤트가 DB에 존재

### T4.4 한국 기업 공시 (DART)
- [ ] DART API 키 발급 (무료)
- [ ] 관심 종목 기준 최근 공시 수집
  - 실적 공시, 주요 경영사항
  - → verify: watchlist 종목의 최근 공시 3건 이상 DB에 존재

### T4.5 미국 기업 실적 캘린더 (T4.1 결과에 따라)
- [ ] yfinance 되면: 주요 종목 실적 발표일 수집
- [ ] 안 되면: 수동 입력 또는 대안 소스
  - → verify: 빅테크 5개 종목의 다음 실적 발표일이 DB에 존재

### T4.6 수동 데이터 보완 (필요 시)
- [ ] investing.com 캘린더 → CSV 다운로드 후 임포트
- [ ] 증권사 리포트 → 필요해지면 그때 PDF 구조 파악 후 파서 작성
- 범용 파서를 미리 만들지 않음. 실제 PDF를 보고 나서 결정.

---

## 의존성
- T4.1 검증 완료 → T4.2~T4.5 범위 결정
- DART API 키 발급 (수동)
- FRED API 키 (03 T3.3과 공유)

## 산출물
- `collector/event_calendar.py`
- `collector/dart_disclosure.py`
- `config/events_watchlist.yaml`
