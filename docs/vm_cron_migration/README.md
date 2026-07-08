# 수집을 무료 VM cron으로 이전하기

GitHub Actions가 Kalshi에 막혀서, 수집을 **무료 클라우드 VM의 cron**으로 옮기는 작업의 배경·결정·구조를 정리한 문서. 처음 보는 입장에서 풀어 썼다.

> 단계별로 따라 하는 실행 가이드는 [`runbook.md`](./runbook.md) 참고.
> 관련 이슈: [#1 Epic](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/1) (하위 #2~#6)

---

## 한 줄 요약

**GitHub Actions 러너의 IP가 Kalshi에서 차단(403)당했다.** 코드/계정 문제가 아니라 "어디서 요청하느냐(IP)" 문제라, 안 막히는 IP를 가진 **무료 상시 VM**에서 같은 수집 스크립트를 cron으로 돌리기로 했다.

---

## 무슨 일이 있었나

`fetch_once.py`는 Polymarket + Kalshi 두 곳을 두드린다. 그런데 어느 순간부터 GitHub Actions에서 **Kalshi만** 403 Forbidden으로 죽기 시작했다.

```
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url:
https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXFED&status=open&limit=200
```

- `2026-06-04 19:53` 런까지는 정상 → `2026-06-05 02:13` 런부터 실패.
- Kalshi가 죽으면 스크립트 전체가 crash → **Polymarket 데이터까지 통째로 유실**되고 커밋 자체가 안 됨.

### 원인 = 데이터센터 IP 차단 (인증 문제 아님)

같은 요청을 IP만 바꿔 던져보면 원인이 분명해진다:

| 요청 위치 | IP 종류 | Kalshi 응답 |
|---|---|---|
| 내 맥 (로컬) | 가정용 | **200** ✅ |
| GitHub Actions | Azure 데이터센터 | **403** ❌ |
| Google Colab | GCP 데이터센터 | **200** ✅ |

- `python-requests` 기본 User-Agent로도 로컬은 200 → **User-Agent 문제 아님.**
- Kalshi 이 엔드포인트는 **공개 API(인증 불필요)** → **인증 문제도 아님.**
- 결론: **Cloudflare 엣지에서 특정 데이터센터 IP 대역(Azure 등)을 막는 것.** 인증을 추가해도 엣지 차단은 못 뚫는다.

그리고 **Google(GCP) IP는 안 막힌다**는 걸 Colab으로 확인 → 무료 GCP VM 경로가 유효.

---

## 무엇을 결정했나

수집 주체를 **무료 GCP VM 한 곳으로 단일화**한다.

```
[무료 GCP VM]  --cron 6h-->  fetch_once.py  --변경 시 commit/push-->  origin/main
[GitHub Actions]  스케줄 OFF (수동 실행 버튼만 유지)
```

- VM이 안 막힌 IP에서 Polymarket + Kalshi 둘 다 수집.
- **수집 주체를 둘로 두지 않는다** — VM과 Actions가 동시에 main에 push하면 충돌하므로, VM이 안정화되면 Actions cron은 끈다.

### 왜 다른 방법은 안 골랐나

| 방법 | 기각 이유 |
|---|---|
| 그냥 재시도(re-run) | 수동 재실행해도 같은 403. 러너 IP 풀이 일관되게 막힘. |
| Kalshi 인증 추가 | Cloudflare 엣지 차단이라 인증으로 못 뚫음. |
| 프록시 경유 | 무료 프록시는 불안정, 유료는 비용. |
| 내 맥 cron | 맥이 꺼져/자고 있으면 빵꾸. 24시간 무인이 안 됨. |

---

## 왜 Google Cloud였나 (Oracle 대신)

| | Google e2-micro | Oracle Always Free |
|---|---|---|
| Kalshi IP | ✅ 사실상 확인됨(Colab=GCP 200) | ❓ 미확인(띄워서 테스트 필요) |
| egress(외부전송) | ⚠️ 1GB/월 (빡빡) | ✅ 10TB/월 |
| 가입 난이도 | 보통 | 까다로움(거부·용량부족 잦음) |
| 장기 무료 | 90일 후 pay-as-you-go 업그레이드 필요(그 후 한도 내 $0) | 업그레이드 없이 평생, 구조적으로 청구 불가 |

→ "IP가 검증됐다 + 가입이 덜 험하다"를 우선해 **Google로 시작**. 과금 리스크(egress 초과)는 수집 주기 조절 등으로 다룰 수 있는 작은 문제로 판단.

---

## 과금 안전: $300 크레딧 ≠ Always Free (중요)

헷갈리기 쉬운 핵심:

| | $300 무료 크레딧 | Always Free (e2-micro) |
|---|---|---|
| 기간 | **90일 한정** | **평생** |
| 정체 | 모든 유료 자원 체험용 | e2-micro 1대 등 특정 사양 |

- e2-micro **자체는 평생 무료 사양**이다. $300은 별개의 90일 체험 크레딧.
- 단, **90일 이후에도 VM을 계속 돌리려면 "유료(pay-as-you-go) 계정으로 업그레이드"가 필요**하다.
  - 업그레이드 **안 하면** → 90일 후 자원 정지/삭제(청구는 안 됨, 서비스도 멈춤).
  - 업그레이드 **하면** → e2-micro는 한도 내 계속 $0, **초과분(주로 egress 1GB)만** 소액 과금 위험.
- 즉 "카드로 절대 0원"을 90일 넘어서까지 보장하진 못한다. 다만 초과해도 실제론 푼돈 수준.

### 무료로 만드는 정확한 사양 (이거 벗어나면 과금)

- 머신: **e2-micro**
- 리전: **us-west1 / us-central1 / us-east1** 중 하나
- 부팅 디스크: **표준 영구 디스크(Standard PD)** — Balanced/SSD ❌
- 디스크 크기: **30GB 이하**

> ⚠️ 콘솔의 "월별 예상 가격"은 **항상 정가**를 보여주고 Always Free 할인을 반영하지 않는다. e2-micro도 견적엔 $6~7로 뜨지만 실제 청구는 $0. **견적 숫자에 겁먹지 말 것.**

---

## 진행 현황 (이슈)

- [#1 Epic](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/1) — 전체
- [x] [#2](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/2) [Spike] 무료 VM 제공자 선정 → **Google 확정**
- [x] [#3](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/3) VM 프로비저닝 & 과금 방지 설정
- [x] [#4](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/4) VM git push 인증 구성
- [x] [#5](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/5) cron + 수집 래퍼 스크립트
- [x] [#6](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/6) GitHub Actions 스케줄 OFF (cutover) — 2026-06-05 완료
- [ ] [#8](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/8) 체험판 만료(9/4) 대응 — pay-as-you-go 업그레이드, 8월 초까지

작업 브랜치: `dev-new-croning-meth`

---

## 실행 기록 (2026-06-05)

실제로 이날 한 작업 순서. 다음에 비슷한 걸 또 셋업하거나 문제 생겼을 때 참고용.

### 만든 것
- **VM**: Google Cloud `e2-micro`, 리전 `us-central1`, 표준 영구 디스크 10GB → Always Free. 인스턴스명 `pridiction-market-instance-...`
- **계정 안전**: Free Trial 유지(유료 업그레이드 안 함) + 예산 알림 $1.
- **repo 위치(VM)**: `~/01_/Stocks-Recomm` (홈: `/home/kimdohyun7942`)
- **git 신원(VM)**: `predmarket-vm-google`
- **push 인증**: fine-grained PAT(Contents: read/write, 이 repo만) + `credential.helper store` → `~/.git-credentials`에 저장
- **cron**: `0 0,6,12,18 * * *` (UTC) = 한국시간 09/15/21/03. 로그 `~/fetch.log`.

### IP 검증 결과 (#2)
| 위치 | IP | Kalshi |
|---|---|---|
| 로컬 맥 | 가정용 | 200 |
| GitHub Actions | Azure | **403** |
| Colab | GCP | 200 |
| GCP e2-micro VM | GCP | **200** ✅ |

### 검증된 것
- VM에서 `fetch_once.py` 정상 수집: Kalshi 109 / Polymarket 23.
- `scripts/run_fetch.sh` 수동 실행: pull → 수집 → commit → push 전 과정 성공.
- **git push 전송량이 작다**: 16MB DB인데도 델타 압축으로 push당 **~25~35KB**. → 앞서 걱정한 egress(월 1GB) 부담은 실제론 매우 작음.

### 겪은 함정 / 우회
- **이 repo는 PR이 비활성화**돼 있음 + 로컬에서 main 직접 push는 Claude Code 정책이 차단 → 그래서 **브랜치 머지는 VM에서 수행**한다:
  ```bash
  # VM에서 브랜치를 main에 머지·push (PR 우회)
  cd ~/01_/Stocks-Recomm
  git fetch origin
  git merge origin/<branch> -m "..."
  git push
  ```
- 콘솔 "월별 예상 가격"이 $6.11로 떠서 놀랐지만, **Always Free 할인은 견적에 안 보임** → 실제 청구 $0.

---

## 상태 점검 (2026-07-08 — 셋업 후 첫 확인)

한 달 무인 방치 후 SSH로 들어가 확인한 결과. 다음 점검 때 이 절에 이어서 기록.

### ✅ 정상인 것

- **크론 생존**: 2026-07-08T00:00Z 런까지 6시간 간격 수집·push 연속 성공 (`fetch.log` + `data: snapshot` 커밋 이력으로 확인). 셋업 이후 사람 손 없이 한 달 완주.
- **크레딧**: ₩448,276 / ₩448,796 잔여 — 한 달 소진 ~₩520. e2-micro Always Free 사양이 제대로 잡혔다는 방증.
- 크레딧 소멸 규칙 재확인: **"다 쓰거나 vs 9/4 기간만료" 중 먼저 오는 쪽에서 끝**, 잔액은 소멸(이월·환불 없음), 업그레이드해도 기간 연장 안 됨. 현 속도면 ~₩44만이 소멸하는 게 정상 (손해 아님 — 원래 그런 구조).

### ⚠️ 발견된 리스크 (신규)

- **push 로그에 GH001 대용량 경고 발생 중** — DB가 50MB를 넘었다 (16MB→57.7MB, 한 달 새). 이 속도(~1.2MB/일)면 **8월 중순 100MB 초과 → GitHub push 거부 → 수집 백업이 조용히 끊김.** 체험판 만료(9/4)보다 먼저 오는 데드라인. 상세·대응 후보: [`../KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md).
- **PAT 만료일이 어디에도 기록 안 됨** — fine-grained PAT는 만료가 필수라 언젠가 반드시 끊긴다. GitHub → Settings → Developer settings → Fine-grained tokens에서 확인해 여기와 캘린더에 기록할 것: **만료일 = (미기록)**.

### 다음 점검 때 볼 것

- 레포 마지막 `data: snapshot` 커밋이 6시간 이내인가 (SSH 불필요한 공짜 헬스체크)
- DB 크기 (100MB 카운트다운)
- #8 진행 (업그레이드 후라면 청구 $0 확인)

---

## FAQ

**Q. SSH 터미널(또는 브라우저)을 닫아도 수집이 도나?**
A. 돈다. cron은 VM 안에서 실행되고, SSH는 원격 접속 창일 뿐. VM은 24시간 켜져 있어서 창을 닫아도 6시간마다 자동 실행된다.

**Q. 과금됐는지 어떻게 확인하나?**
A. GCP 콘솔 → 결제(Billing) → 개요(현재 사용액/크레딧) 또는 보고서(SKU별). Always Free 사양이면 $0. 예산 알림 $1이 초과 시 메일로 통지.

**Q. 90일 뒤엔?**
A. $300 크레딧이 끝나면 e2-micro를 계속 쓰려면 "pay-as-you-go 업그레이드" 필요. 업그레이드 후에도 Always Free 한도 내면 $0, 초과분(주로 egress)만 소액. (위 "과금 안전" 섹션 참고)

**Q. 토큰(PAT) 만료되면?**
A. push가 조용히 실패 → `~/fetch.log`에 에러. 만료 전 새 토큰 발급 후 `~/.git-credentials` 갱신. 만료일을 캘린더에 적어둘 것.

---

## 관련 파일

- [`runbook.md`](./runbook.md) — 단계별 실행 가이드
- `docs/github_actions.md` — 기존 GitHub Actions 방식 설명 (대체 대상)
- `.github/workflows/fetch.yml` — 끌 워크플로우(스케줄)
- `src/collector/fetch_once.py` — VM에서도 그대로 돌릴 수집 스크립트
