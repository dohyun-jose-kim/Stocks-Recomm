# 주식 뉴스 + 예측시장 수집 파이프라인 설계서 v2

## 목표
1. 한국 주식/금융 뉴스를 원천 소스에서 자동 수집
2. 미국 예측시장(Polymarket, Kalshi) 데이터를 수집하여 시장 센티먼트/확률 지표로 활용
3. 로컬에서 저장·분석하는 자동화 파이프라인 구축

## 환경
- macOS (Apple)
- Python 3.x
- 로컬 실행 (launchd 스케줄링)
- 저장: SQLite → 필요 시 PostgreSQL

---

## PART A: 한국 뉴스 수집

### A-1. 네이버 뉴스 검색 API (메인)
- 등록: https://developers.naver.com → Client ID/Secret 발급
- 엔드포인트: `GET https://openapi.naver.com/v1/search/news.json`
- 일 25,000회 무료, 한번에 최대 100건
- 파라미터: query, display(최대100), start(최대1000), sort(date|sim)
- 응답: title, description, originallink, link, pubDate

### A-2. RSS 피드 (보조, 키 불필요)
- 이투데이 증권: `https://www.etoday.co.kr/rss/section/stock.xml`
- 이데일리: `https://www.edaily.co.kr/rss/`
- 한국경제: `https://www.hankyung.com/feed/`
- 연합뉴스 경제: `https://www.yna.co.kr/rss/economy.xml`
- 수집: `feedparser`로 폴링

### A-3. 수집 전략
- 관심 키워드 리스트: config/watchlist.yaml에 정의
- 30분 간격 cron/launchd
- originallink URL 해시로 중복 제거

---

## PART B: 예측시장 데이터 수집

### B-1. Polymarket (탈중앙화 예측시장)

**API 구조 (3개 서비스, 전부 공개, 인증 불필요)**

| API | Base URL | 용도 |
|-----|----------|------|
| Gamma API | `https://gamma-api.polymarket.com` | 마켓 메타데이터, 이벤트, 카테고리, 검색 |
| CLOB API | `https://clob.polymarket.com` | 오더북, 가격, 미드포인트, 스프레드, 가격 히스토리 |
| Data API | `https://data-api.polymarket.com` | 유저 포지션, 트레이드, 오픈인터레스트, 리더보드 |

**핵심 엔드포인트**

```python
# 1. 활성 이벤트 목록 (인증 불필요)
GET https://gamma-api.polymarket.com/events?active=true&closed=false&limit=50

# 2. 특정 이벤트 (slug로 조회)
GET https://gamma-api.polymarket.com/events?slug=fed-decision-in-october

# 3. 태그/카테고리로 필터링
GET https://gamma-api.polymarket.com/events?tag_id={tag_id}&active=true

# 4. 마켓별 가격 (outcomePrices = 내재 확률)
# 응답 예: {"outcomes": "[\"Yes\",\"No\"]", "outcomePrices": "[\"0.65\",\"0.35\"]"}
# → Yes 확률 65%, No 확률 35%
```

**수집할 필드**
- title, slug, outcomes, outcomePrices (=내재확률)
- volume, volume24hr, liquidity
- startDate, endDate, closed
- 카테고리 태그 (Politics, Economics, Crypto, Tech 등)

**관심 카테고리 (금융 관련)**
- Fed 금리 결정, GDP, CPI, 고용지표
- 기업 실적 (AAPL/NVDA/TSLA earnings beat?)
- 지정학 (관세, 제재, 전쟁)
- 크립토 가격 마일스톤

---

### B-2. Kalshi (CFTC 규제 예측시장)

**API 구조 (마켓 데이터는 공개, 인증 불필요)**

| 엔드포인트 | 용도 |
|-----------|------|
| `GET /trade-api/v2/series` | 시리즈 목록 (반복 이벤트 템플릿) |
| `GET /trade-api/v2/events/{ticker}` | 이벤트 상세 |
| `GET /trade-api/v2/markets` | 마켓 목록 (필터링 가능) |
| `GET /trade-api/v2/markets/{ticker}` | 개별 마켓 상세 |
| `GET /trade-api/v2/markets/{ticker}/orderbook` | 오더북 |
| `GET /trade-api/v2/markets/trades` | 전체 거래 내역 |

**Base URL**: `https://api.elections.kalshi.com` (elections 서브도메인이지만 전체 마켓 접근 가능)

```python
# 1. 활성 마켓 목록
GET https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=100

# 2. 특정 시리즈 조회 (예: Fed 금리)
GET https://api.elections.kalshi.com/trade-api/v2/series/KXFED

# 3. 개별 마켓 상세
GET https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}
# 응답 핵심: yes_bid_dollars (=Yes 확률), volume_fp, open_interest_fp
```

**수집할 필드**
- ticker, title, event_ticker, status
- yes_bid_dollars, yes_ask_dollars (=내재확률, $0~$1)
- volume_fp, volume_24h_fp, open_interest_fp
- open_time, close_time, result
- category (Economics, Fed, GDP, Climate, Tech 등)

**관심 시리즈**
- KXFED: Fed 금리 결정
- KXCPI: CPI 인플레이션
- KXJOBS: 비농업 고용
- KXGDP: GDP 성장률
- KXRECESSION: 경기침체 여부
- KXSP500: S&P 500 가격 밴드

---

### B-3. Polymarket vs Kalshi 비교

| 항목 | Polymarket | Kalshi |
|------|-----------|--------|
| 인증 | 불필요 (마켓데이터) | 불필요 (마켓데이터) |
| API 키 | 없음 | 없음 (읽기용) |
| 마켓 범위 | 글로벌, 정치/경제/크립토/스포츠 | 미국 중심, 경제지표/날씨/정치 |
| 결제 | USDC (Polygon 체인) | USD (규제된 거래소) |
| 강점 | 유동성 높음, 글로벌 이벤트 커버 | 경제지표 시리즈 체계적, CFTC 규제 |
| 데이터 구조 | Event → Markets (binary) | Series → Events → Markets |

**둘 다 수집하는 이유**: 같은 이벤트(예: Fed 금리)에 대한 두 플랫폼의 내재확률을 비교하면 괴리 자체가 신호가 됨.

---

## PART C: 데이터 처리

### C-1. 뉴스 전처리
- HTML 태그 제거 (BeautifulSoup)
- 중복 제거 (URL 해시)
- 종목 태깅 (정규식 + 종목 사전)
- 타임스탬프 정규화 (KST)

### C-2. 예측시장 전처리
- 가격 → 확률 변환 (이미 $0~$1이 곧 확률)
- 시계열 스냅샷: 30분마다 현재 확률 기록 → 확률 변화 추이
- Polymarket-Kalshi 동일 이벤트 매칭 (수동 매핑 테이블)

---

## PART D: 저장 스키마

### 뉴스 테이블 (기존)
```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT UNIQUE NOT NULL,
    source TEXT,
    published_at DATETIME,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tickers TEXT,           -- JSON
    category TEXT,
    sentiment_score REAL
);
```

### 예측시장 마켓 테이블
```sql
CREATE TABLE prediction_markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,          -- 'polymarket' | 'kalshi'
    market_id TEXT NOT NULL,         -- slug 또는 ticker
    event_title TEXT,
    market_title TEXT,
    category TEXT,
    status TEXT,                     -- open/closed/settled
    open_time DATETIME,
    close_time DATETIME,
    result TEXT,                     -- yes/no/null
    UNIQUE(platform, market_id)
);
```

### 예측시장 가격 스냅샷 테이블 (시계열)
```sql
CREATE TABLE prediction_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_ref INTEGER REFERENCES prediction_markets(id),
    snapshot_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    yes_price REAL,                  -- 0.00 ~ 1.00 (=확률)
    no_price REAL,
    volume_24h REAL,
    open_interest REAL,
    liquidity REAL
);

CREATE INDEX idx_snap_market ON prediction_snapshots(market_ref, snapshot_at);
```

---

## PART E: 분석 레이어 (확장)

### E-1. 뉴스 분석 (기존)
- KR-FinBert 센티먼트
- BERTopic 토픽 모델링

### E-2. 예측시장 분석
- **확률 추이 차트**: 마켓별 yes_price 시계열 → matplotlib/plotly
- **급변 감지**: 1시간 내 확률 ±10%p 이상 변동 → 알림 트리거
- **크로스 플랫폼 괴리**: Polymarket vs Kalshi 동일 이벤트 확률 차이 모니터링
- **뉴스 ↔ 확률 상관**: 특정 뉴스 토픽 급등 시점 vs 예측시장 확률 변동 시차 분석

### E-3. 통합 대시보드 (최종)
- Streamlit 또는 Gradio로 로컬 웹 대시보드
- 패널 1: 최신 뉴스 + 센티먼트
- 패널 2: 예측시장 확률 추이 (Fed, CPI, GDP 등)
- 패널 3: 뉴스-확률 상관 히트맵

---

## PART F: 프로젝트 구조 (업데이트)

```
stock-news-pipeline/
├── config/
│   ├── config.yaml              # API 키, DB 경로, 스케줄 설정
│   ├── watchlist.yaml           # 뉴스 관심 키워드/종목
│   └── prediction_markets.yaml  # 추적할 마켓 slug/ticker 리스트
├── collector/
│   ├── naver_news.py            # 네이버 뉴스 API
│   ├── rss_feed.py              # RSS 피드
│   ├── polymarket.py            # Polymarket Gamma/CLOB API
│   └── kalshi.py                # Kalshi Markets API
├── processor/
│   ├── news_cleaner.py          # 뉴스 전처리
│   ├── market_snapshot.py       # 예측시장 스냅샷 처리
│   └── cross_platform.py        # Poly-Kalshi 매칭/비교
├── analyzer/
│   ├── sentiment.py             # FinBERT
│   ├── topic_model.py           # BERTopic
│   ├── probability_tracker.py   # 확률 추이/급변 감지
│   └── news_market_corr.py      # 뉴스↔확률 상관 분석
├── storage/
│   ├── db.py
│   └── schema.sql
├── dashboard/
│   └── app.py                   # Streamlit 대시보드
├── main.py                      # 수집 엔트리포인트
├── requirements.txt
└── README.md
```

---

## 구현 우선순위

| 순서 | 태스크 | 예상 시간 | 비고 |
|------|--------|-----------|------|
| 1 | 네이버 API 키 발급 + 뉴스 수집기 | 30분 | |
| 2 | SQLite 스키마 전체 생성 | 30분 | 뉴스 + 예측시장 |
| 3 | RSS 피드 수집기 | 30분 | |
| 4 | **Polymarket 수집기** | 1시간 | 키 불필요, 바로 가능 |
| 5 | **Kalshi 수집기** | 1시간 | 키 불필요, 바로 가능 |
| 6 | 중복 제거 + 전처리 | 30분 | |
| 7 | launchd 스케줄링 | 15분 | |
| 8 | 확률 추이 시각화 | 1시간 | matplotlib |
| 9 | 센티먼트 분석 | 1~2시간 | KR-FinBert |
| 10 | BERTopic 토픽 모델링 | 2~3시간 | PubMed 코드 재활용 |
| 11 | 뉴스↔확률 상관 분석 | 2~3시간 | |
| 12 | Streamlit 대시보드 | 2~3시간 | |

**MVP**: 1~7번 = 하루. 뉴스 + 예측시장 양쪽 다 수집 돌아감.
**Phase 2**: 8~10번 = 주말. 시각화 + 분석.
**Phase 3**: 11~12번 = 통합 대시보드.

---

## API 접근 요약

| 소스 | 인증 | 비용 | Rate Limit |
|------|------|------|-----------|
| 네이버 뉴스 API | Client ID/Secret 필요 | 무료 | 일 25,000회 |
| RSS 피드 | 불필요 | 무료 | 없음 (예의상 1분 간격) |
| Polymarket Gamma | 불필요 | 무료 | 미공개 (합리적 사용) |
| Polymarket CLOB | 불필요 (읽기) | 무료 | 미공개 |
| Kalshi Markets | 불필요 (읽기) | 무료 | 문서 참조 |

## 바로 시작 체크리스트
- [ ] 네이버 개발자센터 Client ID/Secret 발급
- [ ] `curl "https://gamma-api.polymarket.com/events?limit=3"` 테스트
- [ ] `curl "https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=3"` 테스트
- [ ] Python 환경 세팅 (requests, feedparser, sqlite3)
