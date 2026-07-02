# CLAUDE.md — 프로젝트 작업 정책 (CLAUDE_dh_v1 템플릿 기반)

전역 `~/.claude/CLAUDE.md`(단순성·외과적 수정·계획 먼저·검증 기준)를 전제한다. 여기엔 프로젝트별 사항만.

## 0. 프로젝트 가드레일 (불변, 최우선)

- **수집 파이프라인 보존.** `src/collector/fetch_once.py` + `scripts/run_fetch.sh`는 GCP VM cron이
  6시간 간격으로 실행 중. 시그니처·출력 경로·DB 스키마를 바꾸면 VM 쪽 배포 없이 수집이 조용히 깨진다.
- **DB 스키마 계약.** `data/db/predmarket.sqlite`의 `prediction_markets` / `prediction_snapshots` /
  `event_summaries` 스키마(`src/storage/schema.sql`)는 수집기·탐색 코드 양쪽이 의존. 변경 시 양쪽 동시 검토.
- **DB 커밋 예외.** `data/db/*`는 gitignore지만 `predmarket.sqlite`만 예외로 VM cron이 커밋한다
  (`data: snapshot ...` 커밋). 이 예외 규칙을 건드리지 않는다.
- **시크릿 정책.** 시크릿은 환경변수만. 현재 API 키 불필요(Polymarket Gamma, Kalshi public).
- **산출물 비추적.** 차트/리포트 등 재현 가능한 산출물은 `data/reports/` 등 gitignore 경로에만 생성.
- **조용한 누락 금지.** 필터 탈락·행 drop은 로그/출력으로 명시한다.

## 1. 문서 운영 (계획 먼저, 코드 나중)

| 파일 | 역할 |
|---|---|
| `README.md` | 외부 시점 요약 |
| `CLAUDE.md` (이 파일) | 작업 정책 — 규칙이 바뀌면 여기 먼저 |
| `PLAN.md` | 마스터 설계 (결정·버전 로드맵·검증 기준) |
| `TODO.md` | Phase 진행 로그 (완료 + commit hash) |
| `plans/`, `docs/` | 초기 계획·운영 문서 (보존, 참고용) |
| `docs/KNOWN_LIMITATIONS.md` | 런타임 발견 이슈 (append-only, 생기면 생성) |

순서: 계획을 먼저 문서화 → 구현. `KNOWN_LIMITATIONS.md`는 append-only(해결 시 ✅ 표시만).

## 2. 작업 단위 주도

작업 1개 = 목표 + 검증 기준을 `TODO.md`에 먼저 적고 → 구현 → 검증 → 결과 + commit hash 기록.
한 Phase = 한 클린 커밋. 단계 건너뛰지 않기.

## 3. 디렉터리 컨벤션

기존 `src/` 레이아웃(collector/storage/explore/config) 유지 — `NN_` prefix 컨벤션은 소급 적용하지 않는다.
`archive/`는 보존하되 손대지 않는다.

## 4. 커밋 규칙

- 한 커밋 = 한 논리 변경. 버그픽스/리팩터/기능/문서는 쪼개서 커밋.
- 커밋 메시지에 `Co-Authored-By: Claude ...` 라인 금지.
- `main`에 직접 커밋 (협업 필요해지면 브랜치 도입).
- 버전 완료 시 `vX.Y.Z` git tag.
