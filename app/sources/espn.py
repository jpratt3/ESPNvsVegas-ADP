"""ESPN fantasy ADP via the public league-defaults endpoint (no auth needed)."""
import json

from curl_cffi import requests

SEASON = 2026
URL = (
    "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/"
    f"{SEASON}/segments/0/leaguedefaults/3?view=kona_player_info"
)

POS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DST"}

# ESPN stat ids -> our canonical stat keys (season projection entry)
STAT_IDS = {
    "3": "pass_yds", "4": "pass_tds", "20": "ints",
    "24": "rush_yds", "25": "rush_tds",
    "42": "rec_yds", "43": "rec_tds", "53": "receptions",
}

TEAM = {
    0: "FA", 1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN",
    8: "DET", 9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR",
    15: "MIA", 16: "MIN", 17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI",
    22: "ARI", 23: "PIT", 24: "LAC", 25: "SF", 26: "SEA", 27: "TB", 28: "WSH",
    29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU",
}


def fetch(limit: int = 400) -> list[dict]:
    filt = {
        "players": {
            "limit": limit,
            "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "PPR"},
        }
    }
    r = requests.get(
        URL,
        impersonate="chrome",
        timeout=30,
        headers={"x-fantasy-filter": json.dumps(filt)},
    )
    r.raise_for_status()
    out = []
    for entry in r.json().get("players", []):
        p = entry.get("player", {})
        own = p.get("ownership") or {}
        adp = own.get("averageDraftPosition")
        pos = POS.get(p.get("defaultPositionId"))
        if adp is None or pos is None:
            continue
        proj = {}
        for st in p.get("stats", []):
            if (
                st.get("seasonId") == SEASON
                and st.get("statSourceId") == 1  # projection
                and st.get("statSplitTypeId") == 0  # full season
            ):
                for sid, key in STAT_IDS.items():
                    v = (st.get("stats") or {}).get(sid)
                    if v:
                        proj[key] = round(v, 1)
                break
        out.append(
            {
                "name": p.get("fullName", ""),
                "pos": pos,
                "team": TEAM.get(p.get("proTeamId"), "?"),
                "adp": round(adp, 1),
                "auction": (own.get("auctionValueAverage") or 0),
                "proj": proj,
            }
        )
    return out
