# KNOWN_LIMITATIONS.md — 런타임에서 발견된 이슈

append-only. 해결돼도 지우지 않고 ✅ 표시만 한다. (CLAUDE.md §1)

---

## 2026-07-08 — DB 단일 파일이 GitHub 100MB 한도로 성장 중 (수집 백업 중단 예정 리스크)

- **증상**: VM push 로그에 `GH001: Large files detected` 경고 (GitHub은 50MB 초과 경고, **100MB 초과는 push 거부**).
- **실측** (`data/db/predmarket.sqlite`): 16MB(06-05) → 50.7MB(07-02) → 57.7MB(07-08). 성장 ~1.2MB/일.
- **예상**: 이 속도면 **2026-08-중순 100MB 초과 → push 거부 → 크론의 GitHub 백업이 조용히 끊김** (VM 내 수집·DB 축적은 계속되지만 레포 동기화 중단, `run_fetch.sh`의 push 단계가 매번 실패).
- **원인 구조**: DB 파일 통짜를 repo에 커밋하는 방식(CLAUDE.md §0 "DB 커밋 예외")이 GitHub 파일 크기 상한과 구조적으로 충돌. push 델타 전송량(25~35KB/회)은 문제없음 — 문제는 단일 파일의 절대 크기.
- **대응 후보** (결정 필요, 8월 초 전):
  1. 스냅샷을 DB 통짜 커밋 대신 증분 파일(일자별 CSV/parquet append)로 — repo 히스토리도 가벼워짐
  2. DB는 git 추적 중단, 백업은 GCS 버킷/GitHub Release로 (egress 1GB/월 고려)
  3. Git LFS — 무료 한도(스토리지 1GB)가 곧 또 막혀 비추
  4. 오래된 스냅샷을 주기적으로 아카이브로 분리해 DB 슬림 유지
- **주의**: 어느 쪽이든 수집 파이프라인 가드레일(CLAUDE.md §0)과 VM 쪽 `run_fetch.sh` 배포가 걸림. 단 이 데드라인이 체험판 만료(#8, 9/4)보다 **먼저** 온다.
- **상태**: 미해결 (발견: `docs/vm_cron_migration/README.md` 2026-07-08 상태 점검)
