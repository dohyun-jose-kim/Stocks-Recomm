# 퀀트/주식 예측 프로젝트 컨텍스트 (Claude Code용)

## 배경
- 사용자: Insilicogen iFC 인턴 리서처. PubMed 텍스트마이닝, BERTopic 토픽모델링, Neo4j, Transformer 구현, RAG QA PoC 경험.
- 목표: 주식시장 뉴스 수집 → 분석/예측 파이프라인 탐색 중. 학습/포트폴리오 목적.

## 주식 뉴스 수집 API/도구 (GitHub)
- **TickerTick API** (github.com/hczhu/TickerTick-API): 미국 상장사 ~10k 티커, 무료, 분당 10req. spaCy Transformer NER 백엔드.
- **financial-news-api-python**: 5천만+ 기사, socket.io 실시간 스트리밍.
- **hgnx/automated-market-report**: Yahoo Finance+FRED+CNN+Reuters+FT → 일간 PDF 자동생성.
- **한국**: `pykrx`, `FinanceDataReader`, 네이버 뉴스 검색 API, 한경/연합 RSS.

## 주식 예측 접근법 5가지 & 데이터 설계

### 1. 가격 기반 예측 (LSTM, Up/Down 분류)
- 데이터: OHLCV 일봉 (yfinance/pykrx/FinanceDataReader)
- 피처: 지연 수익률(t-1,t-5,t-20), MA, RSI, MACD, 볼린저밴드
- 타겟: sign(close_{t+1} - close_t) 이진 분류
- 주의: 종목 1개×10년=2,500샘플 → 종목 풀링 필요. 반드시 walk-forward 분할.
- 참고 repo: chinuy/stock-price-prediction (Up/Down 분류, Sharpe ratio 평가)

### 2. 뉴스 센티먼트 + 가격 (FinBERT + XGBoost)
- 뉴스: NewsAPI, TickerTick, 네이버 뉴스 API
- 피처: 일별 기사 수, FinBERT 평균 센티먼트, 극단값 비율 + OHLCV 기술지표
- 시간 정렬 핵심: 장 마감(15:30 KST) 이전 기사만 당일 신호. 이후 기사는 다음 거래일.
- 현실 정확도: ~55%

### 3. BERTopic 토픽 모델링 (사용자 현재 스택과 가장 유사)
- 데이터: 금융 뉴스 제목+본문 10k~100k건
- 임베딩: ko-sbert-nli 또는 multilingual-e5
- 목적: 예측이 아닌 **분석** — 토픽 비중 시계열 vs 시장 변동성/섹터 수익률 상관
- 산출물: "토픽 X 증가 → 2일 후 해당 섹터 변동성 증가" 같은 상관 리포트
- PubMed 파이프라인 거의 그대로 재활용 가능

### 4. 팩터/퀀트 모델 (Qlib) — 성격 다름: "포트폴리오 구성" 문제
- 데이터: OHLCV + 재무제표(PER,PBR,ROE) + 공시. KRX/FnGuide/DART(한국), Compustat(해외).
- 타겟: 유니버스 내 상대 수익률 랭킹 (상위20% vs 하위20%)
- 평가: Sharpe ratio, MDD, IC, 알파/베타
- 산출물: 포트폴리오 비중 벡터
- 참고: Microsoft Qlib (Alpha158/360 팩터셋 내장)
- 함정: survivorship bias → point-in-time 유니버스 필요

### 5. 강화학습 트레이딩 (FinRL) — 성격 다름: "의사결정/제어" 문제
- State: 포트폴리오 + 시장 피처. Action: buy/sell/hold × 비중. Reward: Sharpe.
- 참고: AI4Finance-Foundation/FinRL
- 실전 채택 제한적, 연구 주제.

## 접근법 관계 정리
- 1~3 = "예측(prediction)" → 신호(signal) 발굴 = 퀀트 리서치의 알파 발굴 단계
- 4 = "최적화" → 신호 → 포트폴리오 구성/리스크 관리
- 5 = "의사결정(control)" → 정책(policy) 학습, 실행/타이밍
- 실무: 1~3의 신호가 4의 입력. 대체재가 아니라 보완재.

## 퀀트 개요
- 정의: 수학·통계·프로그래밍으로 금융시장 의사결정하는 방법론
- 핵심 명제: "시장에 통계적 반복 패턴 존재, 데이터로 찾아 체계적 거래하면 장기 수익"
- 역할: 퀀트 리서처 / 트레이더 / 디벨로퍼 / 리스크 퀀트
- 전략 스케일: HFT(초단타) → 스탯아브(분~일) → 팩터투자(주~월) → 글로벌매크로(월~년)
- 방법론: 룰 기반 → 통계 모델 → ML(XGBoost/LightGBM 주류) → RL
- 금융 데이터 특성: 비정상성, 낮은 SNR, 체제변화, 알파 붕괴 → "작은 엣지를 수천 번 반복"이 본질

## 공통 주의사항
- 수정주가(adjusted close) 필수
- 거래비용·슬리피지·세금 15~30bp 반영
- 한국: 가격제한폭(±30%), 공매도 제약
- Walk-forward 평가 (무작위 셔플 금지)
- Data leakage 방지 (look-ahead bias, train/test 시간 순서)

## 추천 방향
- 사용자 BERTopic 경험 → 3번(토픽×시장 반응 분석)이 가장 자연스러운 확장
- 포트폴리오용: "예측 정확도" 자랑보다 "방법론적으로 엄격한 분석/실패 리포트"가 인상적
