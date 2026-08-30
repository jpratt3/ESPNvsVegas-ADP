"""Bovada season-long player props (/football/nfl-season-player-props).

Events group by stat ("NFL Receiving Yards 2026-27"); each market inside is one
player ("Puka Nacua Regular Season Receiving Yards") with Over/Under outcomes
whose description carries the line ("Over 1049½ yards").
"""
import re

from curl_cffi import requests

URL = (
    "https://www.bovada.lv/services/sports/event/v2/events/A/description/"
    "football/nfl-season-player-props"
)

EVENT_STATS = {
    "NFL Passing Yards": "pass_yds",
    "NFL Passing TD's": "pass_tds",
    "NFL Rushing Yards": "rush_yds",
    "NFL Rushing TD's": "rush_tds",
    "NFL Receiving Yards": "rec_yds",
    "NFL Receiving TD's": "rec_tds",
    "NFL Receptions": "receptions",
}

_PLAYER_RE = re.compile(r"^(.+?)\s+Regular Season\s+", re.I)
_LINE_RE = re.compile(r"(-?\d+(?:[.,]\d+)?)")


def _american(price) -> int | None:
    raw = (price or {}).get("american")
    if raw is None:
        return None
    if str(raw).upper() == "EVEN":
        return 100
    try:
        return int(str(raw).replace("−", "-").replace("+", ""))
    except ValueError:
        return None


def _line(desc: str) -> float | None:
    m = _LINE_RE.search(desc.replace("½", ".5").replace(",", ""))
    return float(m.group(1)) if m else None


def fetch() -> dict:
    """Return {stat: {player_name: {line, over, under}}}."""
    r = requests.get(URL, impersonate="chrome", timeout=30)
    r.raise_for_status()
    out: dict = {}
    for group in r.json():
        for ev in group.get("events", []):
            ev_desc = ev.get("description", "")
            stat = next(
                (v for k, v in EVENT_STATS.items() if ev_desc.startswith(k)), None
            )
            if not stat:
                continue
            for dg in ev.get("displayGroups", []):
                for mkt in dg.get("markets", []):
                    name_m = _PLAYER_RE.match(mkt.get("description", ""))
                    if not name_m:
                        continue
                    row: dict = {}
                    for oc in mkt.get("outcomes", []):
                        desc = oc.get("description", "")
                        side = desc.split()[0].lower() if desc else ""
                        line = _line(desc)
                        if side in ("over", "under") and line is not None:
                            row["line"] = line
                            row[side] = _american(oc.get("price"))
                    if "line" in row:
                        out.setdefault(stat, {})[name_m.group(1)] = row
    return out
