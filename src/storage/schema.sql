-- prediction market 시계열 저장 스키마
-- 두 플랫폼(Polymarket, Kalshi) 공통 형태로 정규화

CREATE TABLE IF NOT EXISTS prediction_markets (
    platform        TEXT NOT NULL,    -- 'polymarket' | 'kalshi'
    market_ref      TEXT NOT NULL,    -- 플랫폼 native id (Kalshi ticker, Polymarket market.id)
    event_ref       TEXT,             -- event 묶음 id (Kalshi event_ticker, Polymarket event.id)
    title           TEXT,
    subtitle        TEXT,             -- Polymarket question, Kalshi subtitle
    end_time        TEXT,             -- ISO8601 UTC
    first_seen_at   TEXT NOT NULL,
    last_seen_at    TEXT NOT NULL,
    raw_json        TEXT NOT NULL,
    PRIMARY KEY (platform, market_ref)
);

CREATE TABLE IF NOT EXISTS prediction_snapshots (
    platform        TEXT NOT NULL,
    market_ref      TEXT NOT NULL,
    snapshot_at     TEXT NOT NULL,    -- UTC ISO8601
    yes_price       REAL,             -- 0~1, mid(bid,ask) 또는 last_price
    yes_bid         REAL,             -- Kalshi만 채워짐 (Polymarket NULL)
    yes_ask         REAL,
    last_price      REAL,
    volume          REAL,             -- 누적 거래량
    volume_24h      REAL,
    raw_json        TEXT,
    PRIMARY KEY (platform, market_ref, snapshot_at),
    FOREIGN KEY (platform, market_ref) REFERENCES prediction_markets(platform, market_ref)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_time
    ON prediction_snapshots(snapshot_at);

-- 이벤트 단위 정보화 (derived). 같은 event_ref에 묶인 여러 마켓을
-- 분포로 합쳐서 한 행으로 요약. 시계열 누적.
CREATE TABLE IF NOT EXISTS event_summaries (
    platform        TEXT NOT NULL,
    event_ref       TEXT NOT NULL,
    snapshot_at     TEXT NOT NULL,
    market_count    INTEGER NOT NULL,    -- 묶인 마켓 수
    total_prob      REAL,                -- 합. ~1이면 categorical, >1이면 cumulative 형태
    top_label       TEXT,                -- 최고 확률 마켓의 라벨
    top_prob        REAL,                -- 그 확률
    distribution    TEXT NOT NULL,       -- {label: yes_price} JSON
    PRIMARY KEY (platform, event_ref, snapshot_at)
);

CREATE INDEX IF NOT EXISTS idx_summaries_time
    ON event_summaries(snapshot_at);
