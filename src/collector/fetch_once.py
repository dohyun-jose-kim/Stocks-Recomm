"""1회 fetch + insert. end-to-end 파이프라인 검증용."""

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "predmarket.sqlite"
CONFIG_PATH = ROOT / "src" / "config" / "markets.yaml"

POLYMARKET_EVENTS_URL = "https://gamma-api.polymarket.com/events"
KALSHI_MARKETS_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"

UPSERT_MARKET_SQL = """
INSERT INTO prediction_markets (
    platform, market_ref, event_ref, title, subtitle, end_time,
    first_seen_at, last_seen_at, raw_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(platform, market_ref) DO UPDATE SET
    event_ref = excluded.event_ref,
    title = excluded.title,
    subtitle = excluded.subtitle,
    end_time = excluded.end_time,
    last_seen_at = excluded.last_seen_at,
    raw_json = excluded.raw_json
"""

INSERT_SNAPSHOT_SQL = """
INSERT OR REPLACE INTO prediction_snapshots (
    platform, market_ref, snapshot_at,
    yes_price, yes_bid, yes_ask, last_price, volume, volume_24h, raw_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_SUMMARY_SQL = """
INSERT OR REPLACE INTO event_summaries (
    platform, event_ref, snapshot_at,
    market_count, total_prob, top_label, top_prob, distribution
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_polymarket(config: dict) -> list[dict]:
    """Polymarket events에서 화이트리스트 통과 마켓 추출."""
    keywords = [k.lower() for k in config.get("slug_keywords", [])]
    # 단어 경계 기반 매칭 — "microstrategy"의 "rate" 같은 부분문자열 오매칭 방지.
    # slug의 '-'와 title의 공백 모두 단어 분리자로 취급.
    keyword_re = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(k) for k in keywords) + r")(?![a-z0-9])") if keywords else None
    min_volume = float(config.get("min_volume", 0))

    resp = requests.get(
        POLYMARKET_EVENTS_URL,
        params={
            "active": "true",
            "closed": "false",
            "limit": 100,
            "order": "volume24hr",
            "ascending": "false",
        },
        timeout=30,
    )
    resp.raise_for_status()
    events = resp.json()

    rows = []
    for event in events:
        event_slug = (event.get("slug") or "").lower()
        event_title = (event.get("title") or "").lower()
        for market in event.get("markets", []):
            if not market.get("active") or market.get("closed"):
                continue
            try:
                volume = float(market.get("volume") or 0)
            except (TypeError, ValueError):
                volume = 0.0
            if volume < min_volume:
                continue
            slug = (market.get("slug") or "").lower()
            question = (market.get("question") or "").lower()
            haystack = " ".join([event_slug, event_title, slug, question])
            if keyword_re is None or not keyword_re.search(haystack):
                continue

            yes_price = _polymarket_yes_price(market)
            try:
                last_price = float(market.get("lastTradePrice")) if market.get("lastTradePrice") is not None else None
            except (TypeError, ValueError):
                last_price = None

            rows.append({
                "platform": "polymarket",
                "market_ref": str(market.get("id")),
                "event_ref": str(event.get("id")) if event.get("id") is not None else None,
                "title": event.get("title"),
                "subtitle": market.get("question"),
                "end_time": market.get("endDate"),
                "yes_price": yes_price,
                "yes_bid": None,
                "yes_ask": None,
                "last_price": last_price,
                "volume": volume,
                "volume_24h": None,
                "market_raw": market,
            })
    return rows


def _polymarket_yes_price(market: dict) -> float | None:
    """outcomes / outcomePrices에서 Yes 가격 추출. 둘 다 JSON 문자열."""
    try:
        outcomes = json.loads(market.get("outcomes") or "[]")
        prices = json.loads(market.get("outcomePrices") or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    for outcome, price in zip(outcomes, prices):
        if str(outcome).strip().lower() == "yes":
            try:
                return float(price)
            except (TypeError, ValueError):
                return None
    return None


def fetch_kalshi(config: dict) -> list[dict]:
    """Kalshi: 시리즈 화이트리스트별로 status=open 마켓 모음."""
    rows = []
    for series in config.get("series", []):
        cursor = None
        while True:
            params = {"series_ticker": series, "status": "open", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            resp = requests.get(KALSHI_MARKETS_URL, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            for market in payload.get("markets", []):
                rows.append(_kalshi_to_row(market))
            cursor = payload.get("cursor")
            if not cursor or not payload.get("markets"):
                break
    return rows


def _kalshi_to_row(market: dict) -> dict:
    yes_bid = _safe_float(market.get("yes_bid_dollars"))
    yes_ask = _safe_float(market.get("yes_ask_dollars"))
    last_price = _safe_float(market.get("last_price_dollars"))
    if yes_bid is not None and yes_ask is not None and yes_bid > 0 and yes_ask > 0:
        yes_price = (yes_bid + yes_ask) / 2
    else:
        yes_price = last_price

    return {
        "platform": "kalshi",
        "market_ref": market.get("ticker"),
        "event_ref": market.get("event_ticker"),
        "title": market.get("title"),
        "subtitle": market.get("subtitle"),
        "end_time": market.get("expiration_time"),
        "yes_price": yes_price,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "last_price": last_price,
        "volume": _safe_float(market.get("volume_fp")),
        "volume_24h": _safe_float(market.get("volume_24h_fp")),
        "market_raw": market,
    }


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_events(rows: list[dict], snapshot_at: str) -> list[tuple]:
    """event_ref 단위로 마켓을 묶어 분포 시계열로 정보화."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("event_ref"):
            groups[(row["platform"], row["event_ref"])].append(row)

    summaries = []
    for (platform, event_ref), markets in groups.items():
        distribution: dict[str, float] = {}
        for m in markets:
            if m.get("yes_price") is None:
                continue
            label = m.get("subtitle") or m.get("market_ref") or "?"
            distribution[label] = m["yes_price"]
        if not distribution:
            continue
        total_prob = sum(distribution.values())
        top_label, top_prob = max(distribution.items(), key=lambda kv: kv[1])
        summaries.append((
            platform, event_ref, snapshot_at,
            len(markets), total_prob, top_label, top_prob,
            json.dumps(distribution, ensure_ascii=False),
        ))
    return summaries


def write_rows(conn: sqlite3.Connection, rows: list[dict], snapshot_at: str) -> None:
    for row in rows:
        market_raw_json = json.dumps(row["market_raw"], ensure_ascii=False)
        conn.execute(
            UPSERT_MARKET_SQL,
            (
                row["platform"], row["market_ref"], row["event_ref"],
                row["title"], row["subtitle"], row["end_time"],
                snapshot_at, snapshot_at, market_raw_json,
            ),
        )
        conn.execute(
            INSERT_SNAPSHOT_SQL,
            (
                row["platform"], row["market_ref"], snapshot_at,
                row["yes_price"], row["yes_bid"], row["yes_ask"],
                row["last_price"], row["volume"], row["volume_24h"],
                market_raw_json,
            ),
        )


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text())
    snapshot_at = now_iso()

    print(f"[{snapshot_at}] fetching Polymarket ...")
    poly_rows = fetch_polymarket(config.get("polymarket", {}))
    print(f"  → {len(poly_rows)} markets passed filter")

    print(f"[{snapshot_at}] fetching Kalshi ...")
    kalshi_rows = fetch_kalshi(config.get("kalshi", {}))
    print(f"  → {len(kalshi_rows)} markets")

    summaries = summarize_events(poly_rows + kalshi_rows, snapshot_at)
    print(f"  → {len(summaries)} event summaries derived")

    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            write_rows(conn, poly_rows, snapshot_at)
            write_rows(conn, kalshi_rows, snapshot_at)
            conn.executemany(INSERT_SUMMARY_SQL, summaries)
        cur = conn.execute("SELECT platform, COUNT(*) FROM prediction_markets GROUP BY platform")
        print("DB rows per platform (prediction_markets):")
        for platform, count in cur.fetchall():
            print(f"  {platform}: {count}")
        cur = conn.execute("SELECT platform, COUNT(*) FROM prediction_snapshots GROUP BY platform")
        print("DB rows per platform (prediction_snapshots):")
        for platform, count in cur.fetchall():
            print(f"  {platform}: {count}")
        cur = conn.execute("SELECT platform, COUNT(*) FROM event_summaries GROUP BY platform")
        print("DB rows per platform (event_summaries):")
        for platform, count in cur.fetchall():
            print(f"  {platform}: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
