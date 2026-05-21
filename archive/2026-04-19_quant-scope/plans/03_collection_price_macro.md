# 03. 데이터 수집 — 가격/매크로

**우선순위**: 높음 (분석 시 반드시 필요, 수집기 자체는 간단)

---

## 태스크

### T3.0 결정: 한국 주식 데이터 라이브러리 선택
- [ ] pykrx, FinanceDataReader 둘 다 설치
- [ ] 동일 테스트: KOSPI 일봉 3년치 가져오기
- [ ] 비교 기준: 코드 간결함, 응답 속도, 수정주가 지원 여부
- [ ] 하나 선택
  - → verify: 선택한 라이브러리로 KOSPI 3년 일봉 DataFrame 출력 확인

### T3.1 한국 주식 가격 (OHLCV)
- [ ] 수집 대상 정의:
  - KOSPI/KOSDAQ 인덱스
  - 섹터 ETF (KODEX 200, 반도체, 2차전지 등)
  - 개별 종목 watchlist
- [ ] 일봉 기준, 장 마감 후 1회 수집
- [ ] 수정주가(adjusted close) 사용 필수
  - → verify: DB에 최근 거래일 OHLCV 존재, adjusted close 값이 close와 다른 종목 확인

### T3.2 미국 주식 가격 (OHLCV)
- [ ] yfinance 사용
- [ ] 수집 대상:
  - S&P 500, NASDAQ, DJI 인덱스
  - 주요 종목: AAPL, NVDA, TSLA, MSFT 등
  - 섹터 ETF: XLF, XLK, XLE 등
- [ ] 일봉 기준, 수정주가 필수
  - → verify: DB에 최근 거래일 미국 OHLCV 존재

### T3.3 매크로 경제지표 — 미국
- [ ] FRED API 키 발급 (무료)
- [ ] 수집 대상:
  - 금리: FEDFUNDS, DGS2, DGS10, T10Y2Y (장단기 스프레드)
  - 인플레이션: CPIAUCSL, CPILFESL (코어 CPI)
  - 고용: UNRATE, PAYEMS (비농업 고용)
  - GDP: GDP, GDPC1
  - VIX: VIXCLS
- [ ] 1일 1회 체크 (새 데이터 있으면 저장)
  - → verify: FRED에서 최신 FEDFUNDS 값이 DB에 존재

### T3.4 매크로 경제지표 — 한국
- [ ] 한국은행 ECOS API 키 발급 (무료)
- [ ] 수집 대상:
  - 기준금리
  - 소비자물가지수
  - GDP 성장률
  - 환율 (USD/KRW)
- [ ] 1일 1회 체크
  - → verify: ECOS에서 최신 기준금리가 DB에 존재

---

## 의존성
- T3.0 결정 완료 → T3.1 구현
- FRED API 키 발급 (수동)
- ECOS API 키 발급 (수동)
- DB 스키마 → [05_infra.md](05_infra.md) T5.2 확장 스키마

## 산출물
- `collector/price_kr.py`
- `collector/price_us.py`
- `collector/macro_fred.py`
- `collector/macro_ecos.py`
