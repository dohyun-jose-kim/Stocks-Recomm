# VM cron 이전 — 실행 가이드 (runbook)

[`README.md`](./README.md)의 결정을 실제로 따라 하는 단계별 가이드. 각 단계는 이슈 #2~#6에 대응한다.

---

## 0. 사전 확인 (#2 게이트)

VM의 IP가 Kalshi에 안 막히는지 먼저 확인한다. **이게 200이어야 나머지 단계가 의미 있다.**

VM에 SSH 접속 후:

```bash
curl -s -o /dev/null -w "STATUS: %{http_code}\n" \
  "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXFED&status=open&limit=2"
```

- `STATUS: 200` → 통과. 다음 단계로.
- `STATUS: 403` → 이 제공자도 막힘. Oracle 등 다른 곳으로.

---

## 1. VM 생성 & 과금 방지 (#3)

### Google Cloud 무료 가입
1. https://cloud.google.com → "무료로 시작하기"
2. 약관 + "상업적 목적" 체크박스 동의(형식 항목, 과금과 무관) → 카드 인증(본인확인용)
3. **"유료 계정 업그레이드/활성화" 버튼은 누르지 않는다** (트라이얼 중엔 자동청구 없음)
4. 결제 → 예산 및 알림 → **예산 $1 + 알림** 설정 (안전망)

### VM 사양 (무료 조건 — 벗어나면 과금)
| 항목 | 값 |
|---|---|
| 머신 | e2-micro |
| 리전 | us-west1 / us-central1 / us-east1 |
| 부팅 디스크 유형 | 표준 영구 디스크(Standard PD) |
| 디스크 크기 | 30GB 이하 |

> 견적이 $6~7로 떠도 무시 — Always Free 할인은 견적에 안 보인다.

### 기본 셋업 (SSH 접속 후)
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git
git clone https://github.com/dohyun-jose-kim/Stocks-Recomm.git
cd Stocks-Recomm
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python src/collector/fetch_once.py   # 로컬과 동일하게 수집되는지 확인
```

---

## 2. git push 인증 (#4)

VM이 main에 push하려면 자격증명이 필요하다. **fine-grained PAT** 방식:

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate
   - Repository access: **Only select repositories** → `Stocks-Recomm`
   - Permissions: **Contents → Read and write** (이거 하나면 됨)
   - 만료일 설정(예: 1년)
2. 토큰을 VM에 등록 (repo에 절대 커밋 금지):
   ```bash
   git config --global credential.helper store
   # 첫 push 때 username=GitHub아이디, password=발급한 토큰 입력 → 이후 저장됨
   git config --global user.name  "predmarket-vm"
   git config --global user.email "predmarket-vm@users.noreply.github.com"
   ```
3. 테스트 push로 origin/main 반영 확인.

> 토큰 만료 시 수집이 조용히 멈출 수 있으니 만료일을 캘린더에 적어둘 것.

---

## 3. cron + 래퍼 스크립트 (#5)

### 래퍼 스크립트 `scripts/run_fetch.sh` (예시)
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Stocks-Recomm"
exec 9>/tmp/predmarket-fetch.lock
flock -n 9 || { echo "already running"; exit 0; }   # 중복 실행 방지

. .venv/bin/activate
git pull --ff-only
python src/collector/fetch_once.py
git add data/db/predmarket.sqlite
if ! git diff --cached --quiet; then
  git commit -m "data: snapshot $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  git push
fi
```
로그는 cron 쪽에서 파일로 남긴다.

### crontab 등록
```bash
crontab -e
```
```
# UTC 0/6/12/18시 = 한국시간 09/15/21/03시 (기존 Actions와 동일 주기)
0 0,6,12,18 * * * /bin/bash $HOME/Stocks-Recomm/scripts/run_fetch.sh >> $HOME/fetch.log 2>&1
```

> ⚠️ VM 시스템 시계가 UTC인지 확인(`date`). GCP 기본은 UTC.

### 검증
- `bash scripts/run_fetch.sh` 수동 1회 → origin/main에 스냅샷 커밋 올라오면 OK.
- 다음 cron 시각에 자동으로 도는지 `fetch.log` 확인.

---

## 4. GitHub Actions 끄기 (cutover, #6)

VM cron이 수 사이클 안정적으로 돈 걸 확인한 **뒤에** 한다.

- `.github/workflows/fetch.yml`의 `schedule:` 블록 제거(또는 주석). `workflow_dispatch:`는 남겨 수동 실행은 유지.
- 이로써 수집 주체가 VM 단일 → 이중 push 충돌 없음.

---

## 트러블슈팅

| 증상 | 확인 |
|---|---|
| Kalshi 403 | VM IP가 막힘. `curl` 재확인, 다른 제공자 검토 |
| push 실패(인증) | PAT 만료/권한 확인 (Contents: write) |
| push 충돌 | Actions 스케줄이 아직 켜져 있지 않은지(#6 완료 여부) |
| cron 안 돔 | `crontab -l` 확인, 경로 절대경로인지, `fetch.log` 확인 |
| 과금 발생 | egress 1GB 초과 가능 → 수집 주기↓, 또는 예산알림 점검 |
