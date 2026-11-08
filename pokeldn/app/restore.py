"""Restoring a backup zip made by pokeldn.app.backup.

The archive is read into the app's folders again: plugins, plugin data, created Pokemon, bank,
received, saves, GTS and macros. settings.json is staged as settings.restore.json and applied by
the next launch (pokeldn.app.settings.load), so the running app cannot overwrite it. prod.keys is
written to the key path this computer already uses.

A restore overwrites the current data; the interface asks for confirmation with an "I understand"
tick first. A member outside its category, or one with an absolute or ".." path, is refused rather
than extracted.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from pokeldn.app.paths import BANK, DATA, GTS, MACROS, POKEMON, RECEIVED, SAVES

MANIFEST = "manifest.json"
STAGED_SETTINGS = "settings.restore.json"
# Device-local settings the archive must not replace: paths, the board and network, the WebDAV
# account and the backup choices themselves.
LOCAL_FIELDS = frozenset({
    "keys", "received", "radio_port", "radio", "baud", "tx_power", "github_mirror",
    "check_updates", "backup_mode", "backup_dir", "webdav_url", "webdav_user",
    "webdav_password", "backup_keys", "larger_text", "board_screen",
    "capture", "private_logs", "sprites", "board_names",
})


class RestoreError(Exception):
    """A file that cannot be restored; the message is shown to the player."""


@dataclass
class Backup:
    path: Path
    top: str
    manifest: dict
    categories: dict[str, int]
    files: int
    bytes: int
    has_keys: bool
    has_settings: bool

    @property
    def created(self) -> str:
        return str(self.manifest.get("created") or "")


@dataclass
class Outcome:
    files: int
    categories: dict[str, int]
    settings: bool
    keys: str


def destinations() -> dict[str, Path]:
    """Archive folder -> the folder it is written back to."""
    return {
        "plugins": DATA / "plugins",
        "plugin-data": DATA / "plugin-data",
        "pokemon": POKEMON,
        "bank": BANK,
        "received": RECEIVED,
        "saves": SAVES,
        "gts": GTS,
        "macros": MACROS,
    }


def inspect(path) -> Backup:
    """Reads a backup's manifest and counts its members without writing anything."""
    source = Path(path)
    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile) as error:
        raise RestoreError(f"not a zip file: {error}") from error
    with archive:
        names = archive.namelist()
        top, manifest = "", {}
        for name in names:
            parts = PurePosixPath(name).parts
            if len(parts) != 2 or parts[1] != MANIFEST:
                continue
            try:
                data = json.loads(archive.read(name))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict) and data.get("app") == "pokeldn":
                top, manifest = parts[0], data
                break
        if not top:
            raise RestoreError("this zip is not a pokeldn backup")
        categories: dict[str, int] = {}
        files = size = 0
        has_keys = has_settings = False
        for name in names:
            parts = PurePosixPath(name).parts
            if len(parts) < 3 or parts[0] != top or name.endswith("/"):
                continue
            category = parts[1]
            categories[category] = categories.get(category, 0) + 1
            files += 1
            try:
                size += archive.getinfo(name).file_size
            except KeyError:
                pass
            has_keys = has_keys or category == "keys"
            has_settings = has_settings or name == f"{top}/config/settings.json"
    return Backup(source, top, manifest, categories, files, size, has_keys, has_settings)


def apply(path, info: Backup, mode: str, current, progress=None) -> Outcome:
    """Writes the archive back. `mode` is "cloud" (the archive wins) or "local" (the computer wins:
    only files it does not have are added). `current` is the running Settings, whose local fields
    are kept."""
    cloud = mode != "local"
    source = _copy_if_inside(Path(path))
    try:
        with zipfile.ZipFile(source) as archive:
            settings = _stage_settings(archive, info, current) if cloud else False
            keys = _restore_keys(archive, info, current, cloud)
            counts: dict[str, int] = {}
            for category, folder in destinations().items():
                members = _members(archive, info.top, category)
                if not members:
                    continue        # a folder the backup never had stays as it is
                written = _extract(archive, members, info.top, category, folder, cloud)
                if written:
                    counts[category] = written
                    if progress:
                        progress(category, written)
    finally:
        if source != Path(path):
            source.unlink(missing_ok=True)
    total = sum(counts.values()) + (1 if settings else 0) + (1 if keys else 0)
    return Outcome(total, counts, settings, str(keys or ""))


def _members(archive: zipfile.ZipFile, top: str, category: str) -> list[str]:
    prefix = f"{top}/{category}/"
    found = []
    for name in archive.namelist():
        if not name.startswith(prefix) or name.endswith("/"):
            continue
        relative = PurePosixPath(name[len(prefix):])
        if (not relative.parts or relative.is_absolute() or ".." in relative.parts
                or any(part in ("", ".") for part in relative.parts) or "\\" in name):
            continue
        found.append(name)
    return found


def _extract(archive: zipfile.ZipFile, members: list[str], top: str, category: str,
             folder: Path, cloud: bool) -> int:
    """-> how many files were written. With `cloud`, the folder is cleared first; without, a file
    the computer already has is left alone."""
    if cloud:
        _clear(folder)
    folder.mkdir(parents=True, exist_ok=True)
    prefix = f"{top}/{category}/"
    written = 0
    for name in members:
        relative = PurePosixPath(name[len(prefix):])
        target = folder.joinpath(*relative.parts)
        if not cloud and target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(name) as source, open(target, "wb") as out:
            shutil.copyfileobj(source, out)
        written += 1
    return written


def _clear(folder: Path) -> None:
    """Removes the folder's contents, never the folder itself; only a known destination is cleared."""
    known = {path.resolve() for path in destinations().values()}
    resolved = folder.resolve()
    if resolved not in known:
        raise RestoreError(f"refusing to clear {folder}")
    if not folder.is_dir():
        return
    for child in folder.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink(missing_ok=True)


def _stage_settings(archive: zipfile.ZipFile, info: Backup, current) -> bool:
    name = f"{info.top}/config/settings.json"
    try:
        data = json.loads(archive.read(name))
    except KeyError:
        return False
    except (OSError, ValueError) as error:
        raise RestoreError(f"settings.json in the backup is unreadable: {error}") from error
    if not isinstance(data, dict):
        raise RestoreError("settings.json in the backup is not an object")
    local = asdict(current)
    for field in LOCAL_FIELDS:
        if field in local:
            data[field] = local[field]
    target = DATA / STAGED_SETTINGS
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)
    return True


def _restore_keys(archive: zipfile.ZipFile, info: Backup, current, cloud: bool) -> Path | None:
    prefix = f"{info.top}/keys/"
    members = [name for name in archive.namelist() if name.startswith(prefix) and not name.endswith("/")]
    if not members:
        return None
    source = next((name for name in members if name.lower().endswith(".keys")), members[0])
    configured = str(getattr(current, "keys", "") or "").strip()
    target = Path(os.path.expanduser(configured or "~/.switch/prod.keys"))
    if target.is_dir():
        raise RestoreError(f"the key path is a folder: {target}")
    if not cloud and target.exists():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(source) as data, open(target, "wb") as out:
        shutil.copyfileobj(data, out)
    return target


def _copy_if_inside(path: Path) -> Path:
    """A zip chosen from a folder a restore clears is copied out first, or Windows refuses to delete it."""
    resolved = path.resolve()
    if any(resolved.is_relative_to(folder.resolve()) for folder in destinations().values()):
        handle, name = tempfile.mkstemp(prefix="pokeldn-restore-", suffix=".zip")
        os.close(handle)
        shutil.copyfile(path, name)
        return Path(name)
    return path
