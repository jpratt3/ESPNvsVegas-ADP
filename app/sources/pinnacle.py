"""Pinnacle season-long player props via the guest Arcadia API.

Matchup specials carry descriptions like
"NFL 2026/2027 - Chris Olave Regular Season Receiving Yards"; the league-wide
straight-markets endpoint carries the prices keyed by matchupId/participantId.
"""
import re

from curl_cffi import requests

API = "https://guest.api.arcadia.pinnacle.com/0.1"
LEAGUE = 889  # NFL
HEADERS = {"x-api-key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R"}  # static guest key

STAT_MAP = {
    "passing yards": "pass_yds",
    "passing touchdowns": "pass_tds",
    "passing tds": "pass_tds",
    "rushing yards": "rush_yds",
    "rushing touchdowns": "rush_tds",
    "rushing tds": "rush_tds",
    "receiving yards": "rec_yds",
    "receiving touchdowns": "rec_tds",
    "receiving tds": "rec_tds",
    "receptions": "receptions",
    "interceptions": "ints",
}

_DESC_RE = re.compile(r"NFL \d{4}/\d{4}\s*-\s*(.+?)\s+Regular Season\s+(.+)$", re.I)
_LINE_RE = re.compile(r"(-?\d+(?:\.\d+)?)")


def fetch() -> dict:
    """Return {stat: {player_name: {line, over, under}}}."""
    with requests.Session(impersonate="chrome", timeout=30, headers=HEADERS) as s:
        r = s.get(f"{API}/leagues/{LEAGUE}/matchups")
        r.raise_for_status()
        matchups = r.json()
        r = s.get(f"{API}/leagues/{LEAGUE}/markets/straight")
        r.raise_for_status()
        markets = r.json()

    prices_by_matchup: dict = {}
    for m in markets:
        for p in m.get("prices", []):
            if p.get("participantId") is not None:
                prices_by_matchup.setdefault(m.get("matchupId"), {})[
                    p["participantId"]
                ] = p.get("price")

    out: dict = {}
    for mu in matchups:
        sp = mu.get("special")
        if not sp or sp.get("category") != "Season Long Player Props":
            continue
        desc_m = _DESC_RE.search(sp.get("description", ""))
        if not desc_m:
            continue
        player, stat_name = desc_m.group(1), desc_m.group(2).strip().lower()
        stat = STAT_MAP.get(stat_name)
        if not stat:
            continue
        prices = prices_by_matchup.get(mu.get("id"), {})
        row: dict = {}
        for part in mu.get("participants", []):
            pname = (part.get("name") or "").lower()
            side = "over" if pname.startswith("over") else "under" if pname.startswith("under") else None
            line_m = _LINE_RE.search(pname)
            if side and line_m:
                row["line"] = float(line_m.group(1))
                row[side] = prices.get(part.get("id"))
        if "line" in row:
            out.setdefault(stat, {})[player] = row
    return out
