# Prediction Market Tracker

예측시장(Polymarket, Kalshi)의 확률 시계열을 수집·축적하고, 군중이 어떤 이슈를 어떻게 보는지 따라가는 개인 프로젝트.

## 시작점

- **현재 상태·다음 할 일**: [PLAN.md](PLAN.md) (마스터 설계) + [TODO.md](TODO.md) (Phase 진행 로그)
- 프로젝트 개요: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- 수집 인프라(GCP VM cron) 배경·운영: [docs/vm_cron_migration/](docs/vm_cron_migration/README.md)
- 알려진 리스크: [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md)
- 초기 계획 문서(참고용 보존): [plans/00_overview.md](plans/00_overview.md) / 이전 (퀀트급) 계획 아카이브: [archive/](archive/)

## 구조

```
plans/       계획 문서
src/         코드 (collector / storage / explore / config)
data/        SQLite DB + 로그 (gitignore)
notebooks/   탐색용 노트북
archive/     이전 계획 (참고용)
```

## 상태 (2026-07-08 현행화)

- **수집**: GCP VM(e2-micro) cron이 **6시간 간격으로 자동 수집·push 가동 중** (2026-05-21부터 누적 — 마켓 140개, 스냅샷 2만+ 건). 헬스체크 = 이 레포의 마지막 `data: snapshot` 커밋 시각이 6시간 이내면 정상.
- **탐색**: v0.1.0 탐색 MVP 완료 (급변 감지 + 추이 차트, `src/explore/report.py` — 사용법: [docs/explore_report.md](docs/explore_report.md)). v0.1.1 이벤트 오버레이 작업 중.
- **주의**: DB 파일이 GitHub 100MB 한도를 향해 성장 중 — [#10](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/10) (8월 중순 전 저장 방식 재설계, [상세](docs/KNOWN_LIMITATIONS.md)), GCP 체험판 만료 대응은 [#8](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/8) (8월 초).

> 구버전 안내: 이 절이 "계획 단계, 코드 없음"이던 시기의 다음 단계 메모는 폐기됨 (2026-05-21 시점 정보).
