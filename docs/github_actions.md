# GitHub Actions로 스케줄링하기

이 문서는 우리 프로젝트에서 GitHub Actions를 왜, 어떻게 쓰는지 설명한다. 처음 보는 입장에서 풀어 쓴 것.

---

## 한 줄 요약

**GitHub가 제공하는 "정해진 시간에 코드를 대신 실행해주는 서비스".** 우리 컴퓨터가 꺼져 있어도 GitHub 서버에서 fetch_once.py를 돌리고, 결과 SQLite 파일을 repo에 다시 커밋해 보관한다.

---

## 왜 launchd 대신 GitHub Actions인가

| | macOS launchd (로컬) | GitHub Actions (클라우드) |
|---|---|---|
| 동작 환경 | 내 컴퓨터 | GitHub 서버 |
| 컴퓨터 꺼져 있을 때 | 멈춤 (빵꾸) | 정상 동작 |
| 비용 | 0 | 0 (public repo는 무제한, private는 월 2,000분 무료) |
| 설정 복잡도 | plist 파일 1개 | yml 파일 1개 |
| 시간 정확도 | 정시에 정확 | ±15분 정도 지연 가능 |

이 프로젝트는 "이슈 파악" 용도라 ±15분 지연은 무시할 수 있고, **컴퓨터 꺼두기 자유**가 훨씬 더 가치 있다.

---

## 우리 워크플로우가 하는 일

`.github/workflows/fetch.yml`에 정의된 절차:

```
1. cron으로 정해진 시간이 되면 GitHub가 깨움
2. 우리 repo 최신 코드를 받아옴 (git clone)
3. Python 3.11 + requirements.txt 설치
4. src/collector/fetch_once.py 실행
   → Polymarket, Kalshi 두드림
   → data/db/predmarket.sqlite에 누적
5. 변경된 sqlite을 자동 commit & push
6. 끝
```

다음번 cron 시간에 처음부터 다시. 끝없이 반복.

---

## cron 표현식

`cron: '0 0,12 * * *'` 같은 형태. 다섯 자리: `분 시 일 월 요일`.

예시:
| 표현 | 의미 |
|---|---|
| `0 */6 * * *` | 6시간마다 (하루 4회) |
| `0 0,12 * * *` | 매일 00시, 12시 UTC = **한국시간 09시, 21시** (하루 2회) |
| `30 8 * * *` | 매일 08:30 UTC = 한국시간 17:30 |
| `*/15 * * * *` | 15분마다 |

**주의: GitHub Actions cron은 UTC 기준.** 한국시간 - 9시간.

---

## 이 프로젝트의 빈도

**현재**: 하루 2회 (`0 0,12 * * *` = 한국시간 오전 9시 + 오후 9시)

이유:
- 이슈 파악용으로 충분
- 매번 sqlite을 commit하므로 너무 잦으면 repo가 binary 커밋으로 부풀어오름
- 늘리고 싶으면 yml의 cron만 바꾸면 끝

---

## 데이터는 어디 쌓이나

**`data/db/predmarket.sqlite`** 파일이 매 실행 후 repo에 커밋된다.

- 누구나 `git clone` 후 `sqlite3 data/db/predmarket.sqlite` 열어보면 시계열 다 들어있음
- 로컬에서도 같은 파일 갱신 가능 — push하면 cloud 다음 실행이 이어서 누적
- repo가 public이라 데이터도 공개. **예측시장 가격은 어차피 공개 정보**라 문제 없음

### binary commit 누적 부담

sqlite은 binary라 git diff가 비효율. 1년 후 repo 사이즈가 수백 MB로 부풀 가능성. 그때 가서:
- a) sqlite을 .gitignore에 넣고 GitHub Releases나 S3로 옮기기
- b) sqlite 대신 매 실행 결과를 csv/jsonl로 append (텍스트 diff 잘 됨)

지금은 단순함이 우선. 나중에 부담 되면 그때 처리.

---

## 모니터링

### 워크플로우 실행 결과 확인

```
# CLI
gh run list --workflow=fetch.yml --limit 10
gh run view <run-id> --log

# 또는 브라우저
https://github.com/dohyun-jose-kim/Stocks-Recomm/actions
```

### 실패하면 어떻게 알 수 있나

기본적으로 GitHub은 workflow가 실패하면 **소유자의 이메일로 알림**을 보낸다. (Notification 설정에서 켜져 있어야 함)

또는 수동으로 `gh run list`에서 빨간 X 보면 실패. 클릭해서 로그 확인.

### 수동 실행 (테스트용)

workflow에 `workflow_dispatch:` 트리거가 있어서:

```
gh workflow run fetch.yml
```

또는 브라우저의 Actions 탭에서 "Run workflow" 버튼 클릭.

---

## 한계점 / 알아야 할 것

1. **cron 정확도가 낮다** — 정시에 ±15분 지연 흔함. GitHub 부하 따라 더 늦을 수도. 정시 정확이 필요하면 외부 cron 서비스 (EasyCron 등) + webhook 방식 고려.

2. **public repo는 데이터도 공개**. 예측시장 가격은 OK지만, 만약 미래에 개인 데이터(API 키, watchlist 등)가 들어가면 private 전환 또는 `.env`로 분리 필수.

3. **API 키 같은 비밀**은 `.env` 파일이 아니라 GitHub Secrets에 저장하고 workflow에서 환경변수로 주입. 현재 두 API 모두 키 불필요라서 무관하지만 나중에 필요해지면.

4. **push 권한** — workflow가 commit/push를 하려면 `permissions: contents: write`가 필요. fetch.yml에 명시해 둠.

5. **workflow가 너무 잦으면 GitHub이 자동 비활성화** — public repo의 cron은 **60일 동안 repo에 활동이 없으면 자동 중단**됨. 60일 내 push나 PR이 있으면 OK. (수동 실행이나 코드 변경으로 충분)

---

## 첫 실행 흐름

1. 워크플로우 파일을 main 브랜치에 push (또는 branch에 push 후 PR/merge)
2. GitHub Actions 탭 가서 `fetch.yml` 보임
3. 수동으로 "Run workflow" 한 번 눌러 동작 확인
4. 성공하면 `data/db/predmarket.sqlite`가 GitHub bot 명의로 새 커밋으로 올라옴
5. 이후 cron 시간마다 자동 반복

---

## 끄고 싶을 때

옵션:
- `.github/workflows/fetch.yml` 파일 삭제
- 또는 yml 안의 `schedule:` 블록만 제거 (수동 실행은 유지)
- 또는 GitHub Actions 탭에서 워크플로우 자체를 disable

---

## 관련 파일

- `.github/workflows/fetch.yml` — 실제 workflow 정의
- `src/collector/fetch_once.py` — 실행되는 스크립트
- `data/db/predmarket.sqlite` — 누적되는 데이터
- `requirements.txt` — 워크플로우가 설치하는 패키지
