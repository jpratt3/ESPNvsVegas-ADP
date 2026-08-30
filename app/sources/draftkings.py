"""DraftKings season-long player futures (category 1759 "Player Futures").

Markets look like "NFL 2026/27 - Josh Allen Regular Season Passing Yards" with
Over/Under selections whose label carries the line ("Over 3949.5").
"""
import re

from curl_cffi import requests

BASE = "https://sportsbook-nash.draftkings.com/api/sportscontent/dkusil/v1/leagues/88808"
CATEGORY = 1759

SUBCATS = {
    17147: "pass_yds",
    17148: "pass_tds",
    17223: "rush_yds",
    17224: "rush_tds",
    17314: "rec_yds",
    17315: "rec_tds",
    20168: "receptions",
}

_NAME_RE = re.compile(r"NFL \d{4}/\d{2,4}\s*-\s*(.+?)\s+Regular Season", re.I)
_LINE_RE = re.compile(r"(-?\d+(?:\.\d+)?)")


def _american(sel) -> int | None:
    raw = (sel.get("displayOdds") or {}).get("american")
    if raw is None:
        return None
    try:
        return int(str(raw).replace("−", "-").replace("+", ""))
    except ValueError:
        return None


def fetch() -> dict:
    """Return {stat: {player_name: {line, over, under}}}."""
    out: dict = {}
    with requests.Session(impersonate="chrome", timeout=30) as s:
        for sub_id, stat in SUBCATS.items():
            r = s.get(f"{BASE}/categories/{CATEGORY}/subcategories/{sub_id}")
            r.raise_for_status()
            d = r.json()
            sels_by_market: dict = {}
            for sel in d.get("selections", []):
                sels_by_market.setdefault(sel.get("marketId"), []).append(sel)
            stat_out = out.setdefault(stat, {})
            for m in d.get("markets", []):
                name_m = _NAME_RE.search(m.get("name", ""))
                if not name_m:
                    continue
                player = name_m.group(1)
                row: dict = {}
                for sel in sels_by_market.get(m.get("id"), []):
                    label = sel.get("label", "")
                    side = label.split()[0].lower() if label else ""
                    line_m = _LINE_RE.search(label)
                    if side in ("over", "under") and line_m:
                        row["line"] = float(line_m.group(1))
                        row[side] = _american(sel)
                if "line" in row:
                    stat_out[player] = row
    return out
