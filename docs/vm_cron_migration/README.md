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
- [#2](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/2) [Spike] 무료 VM 제공자 선정 ← 게이트
- [#3](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/3) VM 프로비저닝 & 과금 방지 설정
- [#4](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/4) VM git push 인증 구성
- [#5](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/5) cron + 수집 래퍼 스크립트
- [#6](https://github.com/dohyun-jose-kim/Stocks-Recomm/issues/6) GitHub Actions 스케줄 OFF (cutover)

작업 브랜치: `dev-new-croning-meth`

---

## 관련 파일

- [`runbook.md`](./runbook.md) — 단계별 실행 가이드
- `docs/github_actions.md` — 기존 GitHub Actions 방식 설명 (대체 대상)
- `.github/workflows/fetch.yml` — 끌 워크플로우(스케줄)
- `src/collector/fetch_once.py` — VM에서도 그대로 돌릴 수집 스크립트
