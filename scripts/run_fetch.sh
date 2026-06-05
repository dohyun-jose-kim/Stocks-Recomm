#!/usr/bin/env bash
# 무료 VM의 cron에서 호출하는 수집 래퍼.
#   1) 중복 실행 방지(flock)  2) 최신 코드 pull  3) fetch_once 실행
#   4) DB 변경 시에만 commit & push
# cron 등록 예: 0 0,6,12,18 * * * /bin/bash <이 경로> >> $HOME/fetch.log 2>&1
set -euo pipefail

# 스크립트 위치 기준으로 repo 루트 찾기 (clone 경로와 무관하게 동작)
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# 중복 실행 방지: 이전 실행이 안 끝났으면 그냥 건너뜀
exec 9>/tmp/predmarket-fetch.lock
flock -n 9 || { echo "$(date -u +%FT%TZ) already running, skip"; exit 0; }

echo "=== $(date -u +%FT%TZ) run_fetch start ==="

source .venv/bin/activate
git pull --ff-only
python src/collector/fetch_once.py

git add data/db/predmarket.sqlite
if git diff --cached --quiet; then
  echo "$(date -u +%FT%TZ) no DB change — skip commit"
else
  git commit -m "data: snapshot $(date -u +%FT%TZ)"
  git push
  echo "$(date -u +%FT%TZ) pushed snapshot"
fi

echo "=== $(date -u +%FT%TZ) run_fetch done ==="
