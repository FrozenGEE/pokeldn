"""Pokemon the program created: the records pokeldn.pokemon.Service.keep writes under DATA/pokemon.

A new record carries a `.json` beside it with what the builder replied. An older record without one
is read from its name (species and time) and its game folder.
"""
from dataclasses import dataclass
import json
import os
import re
import time
from pathlib import Path

from pokeldn.app.paths import POKEMON
from pokeldn.pokemon import EXTENSIONS

STAMP = re.compile(r"-(\d{8}-\d{6})-([0-9a-fA-F]{8})$")
# Imports and bank moves write records too, but they are not creations; the history leaves them out.
NOT_CREATED = {"imported", "trade"}


@dataclass(frozen=True)
class Entry:
    id: str
    path: str
    game: str
    species: str
    species_id: int
    shiny: bool
    summary: str
    legal: bool
    created: float
    source: str


def folder() -> Path:
    return POKEMON


def _meta(path: Path) -> dict:
    try:
        data = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _stamp(path: Path) -> tuple[str, str]:
    """(name, "YYYYmmdd-HHMMSS") from the record's file name, or ("", "") for another name."""
    match = STAMP.search(path.stem)
    return (path.stem[:match.start()], match.group(1)) if match else ("", "")


def _when(path: Path, stamp: str) -> float:
    if stamp:
        try:
            return time.mktime(time.strptime(stamp, "%Y%m%d-%H%M%S"))
        except ValueError:
            pass
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _entry(path: Path, game: str) -> Entry | None:
    meta = _meta(path)
    source = str(meta.get("source") or "")
    if source in NOT_CREATED:
        return None
    name, stamp = _stamp(path)
    species = str(meta.get("species") or name.replace("-", " ") or name or path.stem)
    created = float(meta.get("created") or _when(path, stamp))
    when = time.strftime("%d %b %Y, %H:%M", time.localtime(created))
    try:
        species_id = int(meta.get("species_id") or 0)
    except (TypeError, ValueError):
        species_id = 0
    return Entry(path.stem, str(path), str(meta.get("game") or game), species,
                 species_id, bool(meta.get("shiny")),
                 str(meta.get("summary") or f"{species} · {when}"),
                 meta.get("legal") is not False, created, source)


def entries() -> list[Entry]:
    """Every recorded creation, newest first."""
    root = POKEMON
    if not root.is_dir():
        return []
    found = []
    for game, extension in EXTENSIONS.items():
        game_folder = root / game
        if not game_folder.is_dir():
            continue
        for path in game_folder.iterdir():
            if path.is_file() and path.suffix[1:].lower() == extension:
                if entry := _entry(path, game):
                    found.append(entry)
    return sorted(found, key=lambda e: (e.created, e.id), reverse=True)


FAVORITES = POKEMON / ".favorites.json"


def favorites() -> set[str]:
    """The records the player starred, by file name."""
    try:
        data = json.loads(FAVORITES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {item for item in data if isinstance(item, str)} if isinstance(data, list) else set()


def save_favorites(ids: set[str]) -> None:
    try:
        POKEMON.mkdir(parents=True, exist_ok=True)
        tmp = FAVORITES.with_suffix(".tmp")
        tmp.write_text(json.dumps(sorted(ids), ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, FAVORITES)
    except OSError:
        pass


def clear(items) -> int:
    """Deletes the given records and their sidecars; returns how many files went. A record still
    queued for a trade is deleted too, so the trade needs it added again."""
    removed = 0
    for entry in items:
        path = Path(entry.path)
        if path.parent.parent != POKEMON:
            continue
        try:
            path.unlink(missing_ok=True)
            path.with_suffix(".json").unlink(missing_ok=True)
            removed += 1
        except OSError:
            continue
    if removed:
        save_favorites(favorites() - {entry.id for entry in items})
    return removed
