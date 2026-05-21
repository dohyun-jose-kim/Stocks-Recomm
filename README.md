# Prediction Market Tracker

예측시장(Polymarket, Kalshi)의 확률 시계열을 수집·축적하고, 군중이 어떤 이슈를 어떻게 보는지 따라가는 개인 프로젝트.

## 시작점

- 프로젝트 개요: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- 계획 문서: [plans/00_overview.md](plans/00_overview.md)
- 이전 (퀀트급) 계획 아카이브: [archive/](archive/)

## 구조

```
plans/       계획 문서
src/         코드 (collector / storage / explore / config)
data/        SQLite DB + 로그 (gitignore)
notebooks/   탐색용 노트북
archive/     이전 계획 (참고용)
```

## 상태

계획 단계. 코드는 아직 없음. 다음 단계는 `plans/01_collectors.md`의 Polymarket Gamma API 응답 구조 확인.
