# 05. 인프라 — DB / 스케줄링

**우선순위**: 높음 (수집기가 돌려면 이게 먼저)

---

## 태스크

### T5.1 MVP 스키마 (예측시장 수집기용, 최우선)
- [ ] 예측시장 마켓 테이블 (`prediction_markets`)
- [ ] 예측시장 스냅샷 테이블 (`prediction_snapshots`)
- [ ] 인덱스: `(market_ref, snapshot_at)`
- [ ] `storage/schema.sql` 작성
  - → verify: `sqlite3 db.sqlite < schema.sql` 에러 없이 실행, 테이블 2개 생성 확인

### T5.2 확장 스키마 (해당 수집기 구현 시 추가)
- [ ] 뉴스 테이블 → 02 뉴스 수집기 구현 시
- [ ] 가격 테이블 (OHLCV) → 03 가격 수집기 구현 시
- [ ] 매크로 경제지표 테이블 → 03 매크로 수집기 구현 시
- [ ] 이벤트 캘린더 테이블 → 04 이벤트 수집기 구현 시
- [ ] 기업 공시 테이블 → 04 DART 수집기 구현 시

각 테이블은 해당 수집기 PR/커밋에 포함. 미리 전부 설계하지 않음.

### T5.3 스케줄링 (launchd)
- [ ] 수집 주기 설계:
  - 예측시장: 30분
  - 뉴스: 30분
  - 가격(일봉): 1일 1회 (장 마감 후)
  - 매크로: 1일 1회
  - 이벤트 캘린더: 1일 1회
- [ ] launchd plist 파일 작성
- [ ] 로그 저장 경로 설정
  - → verify: launchd 등록 후 30분 뒤 DB에 새 스냅샷 존재

### T5.4 프로젝트 구조 초기화
- [ ] 디렉토리 생성:
  ```
  src/
  ├── collector/
  ├── processor/
  ├── analyzer/
  ├── storage/
  ├── dashboard/
  └── config/
  ```
- [ ] requirements.txt 초안
- [ ] .env 파일 (API 키 관리, .gitignore에 추가)
  - → verify: `pip install -r requirements.txt` 성공

---

## 산출물
- `storage/schema.sql`
- `storage/db.py`
- `config/config.yaml`
- `.env` / `.env.example`
- launchd plist 파일
- `requirements.txt`
