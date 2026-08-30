"""FastAPI app: on-demand refresh of ESPN ADP + sportsbook season props,
merged into one player table the frontend scores and ranks."""
import statistics
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from . import store
from .matching import normalize
from .sources import bovada, draftkings, espn, pinnacle

app = FastAPI(title="Draft Value")

STATIC = Path(__file__).resolve().parent.parent / "static"

BOOKS = {"draftkings": draftkings, "pinnacle": pinnacle, "bovada": bovada}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/refresh/{source}")
def refresh(source: str):
    """source: espn | vegas | all"""
    results, errors = {}, {}
    todo = []
    if source in ("espn", "all"):
        todo.append(("espn", espn.fetch))
    if source in ("vegas", "all"):
        todo += [(name, mod.fetch) for name, mod in BOOKS.items()]
    if not todo:
        raise HTTPException(404, f"unknown source '{source}'")
    for name, fn in todo:
        try:
            doc = store.save(name, fn())
            results[name] = doc["fetched_at"]
        except Exception as e:
            traceback.print_exc()
            errors[name] = f"{type(e).__name__}: {e}"
    status = 200 if results else 502
    return JSONResponse({"refreshed": results, "errors": errors}, status_code=status)


def _merged():
    espn_doc = store.load("espn")
    book_docs = {name: store.load(name) for name in BOOKS}

    # vegas[norm_name][stat] = {books: {book: row}, agg: median line}
    vegas: dict = {}
    display_name: dict = {}
    for book, doc in book_docs.items():
        if not doc:
            continue
        for stat, players in doc["data"].items():
            for raw_name, row in players.items():
                key = normalize(raw_name)
                display_name.setdefault(key, raw_name)
                vegas.setdefault(key, {}).setdefault(stat, {})[book] = row

    for key, stats in vegas.items():
        for stat, books in stats.items():
            lines = [r["line"] for r in books.values() if r.get("line") is not None]
            stats[stat] = {
                "agg": round(statistics.median(lines), 1) if lines else None,
                "books": books,
            }

    players, matched = [], set()
    if espn_doc:
        for p in espn_doc["data"]:
            key = normalize(p["name"])
            stats = vegas.get(key)
            if stats:
                matched.add(key)
            players.append({**p, "stats": stats or {}})

    unmatched = [
        {"name": display_name[k], "stats": {s: v["agg"] for s, v in vegas[k].items()}}
        for k in vegas
        if k not in matched
    ]

    return {
        "players": players,
        "unmatched_vegas": unmatched,
        "timestamps": {
            "espn": espn_doc["fetched_at"] if espn_doc else None,
            **{b: d["fetched_at"] if d else None for b, d in book_docs.items()},
        },
    }


@app.get("/api/data")
def data():
    return _merged()
