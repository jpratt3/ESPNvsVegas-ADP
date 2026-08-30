"""Player-name normalization so ESPN, DraftKings and Pinnacle rows join cleanly."""
import re
import unicodedata

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "lll"}  # "lll" = book typo for III

# Cross-source alias fixes (normalized form -> canonical normalized form).
ALIASES = {
    "hollywood brown": "marquise brown",
    "gabriel davis": "gabe davis",
    "joshua palmer": "josh palmer",
    "cam ward": "cameron ward",
    # Bovada quirks (checked against their posted lines, 2026-08)
    "bryce hall": "breece hall",  # 5.5 rush TDs -> the RB, not the CB
    "cameron skattebo": "cam skattebo",
    "jordin tyson": "jordyn tyson",
    "quentin johnson": "quentin johnston",
}


def normalize(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z\s]", "", s)
    parts = [p for p in s.split() if p not in _SUFFIXES]
    s = " ".join(parts)
    return ALIASES.get(s, s)
