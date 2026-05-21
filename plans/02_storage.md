# 02. 저장 + 스케줄링

**우선순위**: 수집기와 동시. 이게 없으면 수집기가 돌 곳이 없음.

---

## T1. SQLite 스키마

- [ ] `prediction_markets` — 마켓 메타 (id, platform, slug, title, category, first_seen_at)
- [ ] `prediction_snapshots` — 시계열 스냅샷 (market_ref, snapshot_at, yes_price, no_price, volume, raw_json)
- [ ] 인덱스: `(market_ref, snapshot_at)`
- [ ] `src/storage/schema.sql` 작성

→ verify: `sqlite3 db.sqlite < schema.sql` 에러 없이 실행, 테이블 2개 생성

**원본 JSON은 `raw_json` 컬럼에 그대로 보관.** 스키마 변경/마켓 구조 변화에 대비.

## T2. DB 접근 헬퍼

- [ ] `src/storage/db.py` — 커넥션, upsert 마켓, insert 스냅샷
- [ ] 트랜잭션 단위: 한 수집 사이클 = 한 트랜잭션

→ verify: 단위 테스트 또는 REPL에서 insert/조회 동작

## T3. 스케줄링 (launchd)

- [ ] 수집 주기: 30분
- [ ] launchd plist 작성 (Polymarket, Kalshi 각각 또는 통합 1개 — 통합이 간단)
- [ ] 로그 경로 설정 (`logs/collector.log`, `logs/collector.err`)
- [ ] launchctl load 후 동작 확인

→ verify: 등록 후 30분 뒤 DB에 새 스냅샷 존재

## T4. 프로젝트 구조 초기화

- [ ] 디렉토리:
  ```
  src/
  ├── collector/
  ├── storage/
  ├── explore/
  └── config/
  ```
- [ ] `requirements.txt` (requests, python-dotenv 정도. 무거운 라이브러리는 필요해질 때)
- [ ] `.env` / `.env.example` — 키 필요해지면 사용. 현재는 사실상 비어 있음.

→ verify: `pip install -r requirements.txt` 성공

---

## 산출물

- `src/storage/schema.sql`
- `src/storage/db.py`
- `requirements.txt`
- `.env.example`
- launchd plist (`~/Library/LaunchAgents/com.user.predmarket.plist`)

## 의도적으로 안 한 것

- PostgreSQL 마이그레이션 계획 — SQLite로 충분. 막히면 그때 검토.
- 다른 테이블(뉴스/가격/매크로 등) — 스코프 밖.
- ORM — 단순 SQL로 충분.
