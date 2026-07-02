#!/usr/bin/env python3
"""탐색 리포트: 급변 감지 + 확률 추이 차트.

사용 예:
    python src/explore/report.py                    # 24h/7d 급변 마켓 리스트
    python src/explore/report.py --threshold 0.05   # 임계값 조정
    python src/explore/report.py --chart 3          # 24h 급변 상위 3개 차트 PNG 생성
    python src/explore/report.py --market kalshi:KXFED-26JUL-T4.00   # 지정 마켓 차트
"""
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "predmarket.sqlite"
REPORT_DIR = ROOT / "data" / "reports"


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_movers(conn, now, window_hours, threshold):
    """각 마켓의 최신 yes_price vs window 이전 값 비교. |Δ| >= threshold만 반환."""
    cutoff_recent = (now - timedelta(hours=12)).isoformat()
    past = (now - timedelta(hours=window_hours)).isoformat()
    rows = conn.execute(
        """
        WITH latest AS (
            SELECT platform, market_ref, yes_price, snapshot_at,
                   ROW_NUMBER() OVER (PARTITION BY platform, market_ref
                                      ORDER BY snapshot_at DESC) rn
            FROM prediction_snapshots
            WHERE yes_price IS NOT NULL AND snapshot_at >= ?
        ),
        past AS (
            SELECT platform, market_ref, yes_price,
                   ROW_NUMBER() OVER (PARTITION BY platform, market_ref
                                      ORDER BY snapshot_at DESC) rn
            FROM prediction_snapshots
            WHERE yes_price IS NOT NULL AND snapshot_at <= ?
        )
        SELECT l.platform, l.market_ref, p.yes_price, l.yes_price,
               m.title, m.subtitle
        FROM latest l
        JOIN past p ON p.platform = l.platform AND p.market_ref = l.market_ref AND p.rn = 1
        JOIN prediction_markets m ON m.platform = l.platform AND m.market_ref = l.market_ref
        WHERE l.rn = 1
        """,
        (cutoff_recent, past),
    ).fetchall()
    movers = []
    for platform, ref, old, new, title, subtitle in rows:
        delta = new - old
        if abs(delta) >= threshold:
            label = title or ref
            if subtitle and subtitle != title:
                label = f"{label} — {subtitle}"
            movers.append((delta, platform, ref, old, new, label))
    movers.sort(key=lambda x: -abs(x[0]))
    return movers


def print_movers(movers, window_hours, total_active):
    print(f"\n=== 급변 마켓 (최근 {window_hours}h, 활성 {total_active}개 중 {len(movers)}개) ===")
    if not movers:
        print("(없음)")
    for delta, platform, ref, old, new, label in movers:
        print(f"  {delta:+.2f}  {old:.2f} → {new:.2f}  [{platform}] {label}")
        print(f"          ({ref})")


def chart_market(conn, platform, ref):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = conn.execute(
        "SELECT snapshot_at, yes_price FROM prediction_snapshots "
        "WHERE platform=? AND market_ref=? AND yes_price IS NOT NULL ORDER BY snapshot_at",
        (platform, ref),
    ).fetchall()
    if not rows:
        print(f"! 스냅샷 없음: {platform}:{ref}")
        return
    title_row = conn.execute(
        "SELECT title, subtitle FROM prediction_markets WHERE platform=? AND market_ref=?",
        (platform, ref),
    ).fetchone()
    title = (title_row and title_row[0]) or ref
    if title_row and title_row[1] and title_row[1] != title:
        title = f"{title}\n{title_row[1]}"

    ts = [parse_ts(r[0]) for r in rows]
    ys = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ts, ys, lw=1.2)
    ax.set_ylim(0, 1)
    ax.set_ylabel("yes price")
    ax.set_title(f"[{platform}] {title}", fontsize=10)
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    safe = ref.replace("/", "_")
    out = REPORT_DIR / f"{platform}_{safe}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  차트 저장: {out.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description="급변 감지 + 추이 차트")
    ap.add_argument("--threshold", type=float, default=0.10, help="급변 임계값 (기본 0.10)")
    ap.add_argument("--chart", type=int, metavar="N", help="24h 급변 상위 N개 차트 생성")
    ap.add_argument("--market", metavar="PLATFORM:REF", help="지정 마켓 차트 생성")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    now = parse_ts(conn.execute("SELECT MAX(snapshot_at) FROM prediction_snapshots").fetchone()[0])
    total_active = conn.execute(
        "SELECT COUNT(DISTINCT platform || ':' || market_ref) FROM prediction_snapshots "
        "WHERE snapshot_at >= ?",
        ((now - timedelta(hours=12)).isoformat(),),
    ).fetchone()[0]
    print(f"기준 시각(최신 스냅샷): {now.isoformat()}")

    movers_24h = load_movers(conn, now, 24, args.threshold)
    print_movers(movers_24h, 24, total_active)
    print_movers(load_movers(conn, now, 24 * 7, args.threshold), 24 * 7, total_active)

    if args.market:
        platform, _, ref = args.market.partition(":")
        chart_market(conn, platform, ref)
    if args.chart:
        print(f"\n=== 24h 급변 상위 {args.chart}개 차트 ===")
        for _, platform, ref, *_ in movers_24h[: args.chart]:
            chart_market(conn, platform, ref)
    conn.close()


if __name__ == "__main__":
    main()
