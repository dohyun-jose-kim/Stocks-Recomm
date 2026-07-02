# TODO.md — Phase 진행 로그

작업 단위마다: 목표 + 검증 기준 선언 → 구현 → 검증 → 완료 기록(+ commit hash).

## v0.1.0 — 탐색 MVP

### Phase 0: 문서/정책 부트스트랩
- 목표: CLAUDE_dh_v1 템플릿 채용, PLAN.md/TODO.md 작성
- 검증: 문서 존재, 방향 합의됨
- 상태: ✅ 완료 — commit 9381550

### Phase 1: 급변 감지 + 추이 차트 (`src/explore/report.py`)
- 목표: PLAN.md v0.1.0 산출물
- 검증: 실 DB 실행 → 급변 리스트 출력 + 마켓 추이 PNG 생성 확인
- 결과: 24h 급변 4개 / 7d 급변 20개 검출 (임계 0.10), 상위 2개 차트 PNG 생성·육안 확인
- 상태: ✅ 완료 — commit d2ca0e2, tag v0.1.0
