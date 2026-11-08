"""One zip of the settings and Pokemon files, saved to a folder or uploaded to WebDAV.

The archive keeps a folder per kind of file (config, pokemon, bank, received, saves, gts, macros,
plugins and plugin-data) and a manifest.json at its root. The player's own prod.keys is added
under keys/ only when asked for, and the WebDAV password is left out of the settings.json inside
the archive, since the archive itself often goes to that server.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import ssl
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from pokeldn import __version__
from pokeldn.app import build_info
from pokeldn.app.paths import BANK, DATA, GTS, MACROS, POKEMON, RECEIVED, SAVES
from pokeldn.app.settings import PATH as SETTINGS_PATH

PREFIX = "pokeldn-backup-"
SINGLE = "pokeldn-backup.zip"          # the one file a WebDAV sync keeps
MANIFEST = "manifest.json"
SKIP_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = {".tmp", ".pyc"}
SECRET_FIELDS = ("webdav_password",)
# A backup saved into one of the folders being backed up must not swallow the older archives.
SKIP_ARCHIVE_SUFFIX = ".zip"


@dataclass
class Result:
    """A finished zip in a temporary folder; `discard` removes it once it was moved or uploaded."""
    path: Path
    files: int
    bytes: int
    categories: dict[str, int]
    skipped: int = 0

    def discard(self) -> None:
        shutil.rmtree(self.path.parent, ignore_errors=True)


class WebDAVError(Exception):
    """A failed WebDAV call; `kind` is what the view turns into a sentence."""

    def __init__(self, kind: str, detail: str = ""):
        super().__init__(kind, detail)
        self.kind, self.detail = kind, detail

    def __str__(self) -> str:
        return f"{self.kind}: {self.detail}" if self.detail else self.kind


def sources() -> list[tuple[str, Path]]:
    """(folder in the archive, file or folder on this computer), in the archive's order."""
    return [
        ("config", SETTINGS_PATH),
        ("plugins", DATA / "plugins"),
        ("plugin-data", DATA / "plugin-data"),
        ("pokemon", POKEMON),
        ("bank", BANK),
        ("received", RECEIVED),
        ("saves", SAVES),
        ("gts", GTS),
        ("macros", MACROS),
    ]


def key_file(path: str) -> Path | None:
    """The player's own prod.keys when it is readable, else None."""
    if not (path or "").strip():
        return None
    candidate = Path(os.path.expanduser(path.strip()))
    return candidate if candidate.is_file() and not candidate.is_symlink() else None


def _skip(path: Path) -> bool:
    return (path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES
            or (path.suffix.lower() == SKIP_ARCHIVE_SUFFIX
                and path.name.startswith(("pokeldn-backup", "pokeldn-before-restore"))))


def _settings_bytes() -> bytes:
    """settings.json without the WebDAV password, so a backup can safely sit on that server."""
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        settings = None
    if not isinstance(settings, dict):
        return SETTINGS_PATH.read_bytes()
    for field in SECRET_FIELDS:
        settings.pop(field, None)
    return json.dumps(settings, ensure_ascii=False, indent=2).encode("utf-8")


def create(include_keys: bool = False, keys_path: str = "", progress=None) -> Result:
    """Writes the zip into a new temporary folder. `progress(folder, files)` is called per folder.
    `include_keys` adds the player's own prod.keys under keys/; it is off unless asked for."""
    root = Path(tempfile.mkdtemp(prefix="pokeldn-backup-"))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = root / f"{PREFIX}{stamp}.zip"
    files = size = skipped = 0
    categories: dict[str, int] = {}
    keys = key_file(keys_path) if include_keys else None
    try:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for folder, source in sources():
                if not source.exists():
                    continue
                count = 0
                if source.is_file():
                    if source == SETTINGS_PATH:
                        data = _settings_bytes()
                    else:
                        try:
                            data = source.read_bytes()
                        except OSError:
                            skipped += 1
                            continue
                    archive.writestr(f"{PREFIX}{stamp}/{folder}/{source.name}", data)
                    files += 1
                    size += len(data)
                    count = 1
                elif source.is_dir():
                    for item in sorted(source.rglob("*")):
                        if (not item.is_file() or item.is_symlink() or _skip(item)
                                or any(_skip(parent) for parent in item.relative_to(source).parents
                                       if parent != Path("."))):
                            continue
                        relative = item.relative_to(source)
                        try:
                            archive.write(item, f"{PREFIX}{stamp}/{folder}/{relative.as_posix()}")
                            size += item.stat().st_size
                        except OSError:
                            skipped += 1
                            continue
                        files += 1
                        count += 1
                if count:
                    categories[folder] = categories.get(folder, 0) + count
                if progress:
                    progress(folder, count)
            key_added = False
            if keys is not None:
                try:
                    data = keys.read_bytes()
                    archive.writestr(f"{PREFIX}{stamp}/keys/{keys.name}", data)
                    files += 1
                    size += len(data)
                    categories["keys"] = 1
                    key_added = True
                except OSError:
                    skipped += 1
                if progress:
                    progress("keys", 1 if key_added else 0)
            manifest = {
                "app": "pokeldn",
                "format": 1,
                "pokeldn": __version__,
                "build_date": build_info.BUILD_DATE,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "files": files,
                "bytes": size,
                "skipped": skipped,
                "categories": categories,
                "includes_keys": key_added,
                "note": ("prod.keys is included." if key_added else "prod.keys is not included.")
                        + " settings.json has no WebDAV password.",
            }
            archive.writestr(f"{PREFIX}{stamp}/{MANIFEST}",
                             json.dumps(manifest, ensure_ascii=False, indent=2))
    except BaseException:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return Result(path, files, size, categories, skipped)


def save_local(archive: Path, folder: str, name: str | None = None, replace: bool = False) -> Path:
    """Moves a finished zip into `folder`. Without `name` the archive's own name is kept and an
    existing file is given a number; with replace, `name` is overwritten."""
    target = Path(os.path.expanduser(folder.strip())).resolve()
    if target.exists() and not target.is_dir():
        raise NotADirectoryError(str(target))
    target.mkdir(parents=True, exist_ok=True)
    destination = target / (name or Path(archive).name)
    if Path(destination.name).name != destination.name:
        raise ValueError("a backup name is a plain file name")
    if destination.exists():
        if not replace:
            number = 2
            while destination.exists():
                destination = target / f"{destination.stem}-{number}{destination.suffix}"
                number += 1
        else:
            destination.unlink()
    shutil.move(str(archive), str(destination))
    return destination


def normalize(url: str) -> str:
    """A WebDAV folder URL ending in '/', or ValueError. A user name in the address is refused."""
    value = (url or "").strip()
    parts = urllib.parse.urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("the WebDAV address starts with http:// or https://")
    if parts.username or parts.password:
        raise ValueError("put the account in the account field, not in the address")
    path = parts.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _context() -> ssl.SSLContext:
    # A frozen macOS build has no system certificate store that Python can read; certifi ships with flet.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _headers(user: str, password: str) -> dict[str, str]:
    headers = {"User-Agent": "pokeldn-desktop"}
    if user:
        token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    return headers


def _open(request: urllib.request.Request, timeout: float):
    return urllib.request.urlopen(request, timeout=timeout, context=_context())


def _kind(error: urllib.error.HTTPError) -> str:
    return {401: "auth", 403: "denied", 404: "missing", 507: "space"}.get(error.code, "server")


def _allowed(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def probe(url: str, user: str = "", password: str = "", timeout: float = 15.0) -> str:
    """Asks a WebDAV folder who may read it: "ok", "auth", "missing", "denied", "invalid" or "fail"."""
    try:
        base = normalize(url)
    except ValueError:
        return "invalid"
    body = (b'<?xml version="1.0" encoding="utf-8"?>'
            b'<d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>')
    headers = {**_headers(user, password), "Depth": "0", "Content-Type": "application/xml; charset=utf-8"}
    try:
        with _open(urllib.request.Request(base, data=body, method="PROPFIND", headers=headers), timeout) as reply:
            reply.read(512)
        return "ok"
    except urllib.error.HTTPError as error:
        if error.code == 405:     # no PROPFIND: an OPTIONS answer still tells whether the folder is there
            try:
                with _open(urllib.request.Request(base, method="OPTIONS", headers=_headers(user, password)),
                           timeout) as reply:
                    reply.read(512)
                return "ok"
            except urllib.error.HTTPError as fallback:
                return "fail" if fallback.code >= 500 else _kind(fallback)
            except Exception:
                return "fail"
        return "fail" if error.code >= 500 else _kind(error)
    except Exception:
        return "fail"


def upload(archive: Path, url: str, user: str = "", password: str = "", timeout: float = 300.0,
           name: str | None = None) -> str:
    """PUTs the zip into the WebDAV folder and returns its address. `name` replaces the file name."""
    if not _allowed(archive):
        raise WebDAVError("missing", str(archive))
    base = normalize(url)
    target_name = name or Path(archive).name
    if Path(target_name).name != target_name or not target_name:
        raise WebDAVError("missing", target_name)
    target = base + urllib.parse.quote(target_name)
    headers = {**_headers(user, password), "Content-Type": "application/zip",
               "Content-Length": str(archive.stat().st_size)}

    # An existing folder answers 405 and a missing one may be made when its parent exists; the PUT below
    # reports anything that still stops the upload.
    try:
        with _open(urllib.request.Request(base, method="MKCOL", headers=_headers(user, password)), 30) as reply:
            reply.read(256)
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise WebDAVError("auth", "MKCOL") from error
        if error.code >= 500:
            raise WebDAVError("server", str(error.code)) from error
    except Exception:
        pass

    try:
        with open(archive, "rb") as data, _open(
                urllib.request.Request(target, data=data, method="PUT", headers=headers), timeout) as reply:
            reply.read(256)
    except urllib.error.HTTPError as error:
        raise WebDAVError(_kind(error), str(error.code)) from error
    except OSError as error:
        raise WebDAVError("network", str(error)) from error
    return target


def list_backups(url: str, user: str = "", password: str = "", timeout: float = 20.0) -> list[dict]:
    """The pokeldn-backup-*.zip files in a WebDAV folder, newest name first."""
    import xml.etree.ElementTree as ET

    base = normalize(url)
    body = (b'<?xml version="1.0" encoding="utf-8"?>'
            b'<d:propfind xmlns:d="DAV:"><d:prop><d:getcontentlength/>'
            b'<d:getlastmodified/><d:resourcetype/></d:prop></d:propfind>')
    headers = {**_headers(user, password), "Depth": "1", "Content-Type": "application/xml; charset=utf-8"}
    try:
        with _open(urllib.request.Request(base, data=body, method="PROPFIND", headers=headers), timeout) as reply:
            data = reply.read(8 << 20)
    except urllib.error.HTTPError as error:
        raise WebDAVError(_kind(error), str(error.code)) from error
    except OSError as error:
        raise WebDAVError("network", str(error)) from error
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise WebDAVError("server", "PROPFIND did not return XML") from error
    namespace = {"d": "DAV:"}
    found = []
    for response in root.findall("d:response", namespace):
        href = response.findtext("d:href", default="", namespaces=namespace)
        name = urllib.parse.unquote(href.rstrip("/").rsplit("/", 1)[-1])
        if not (name.startswith(PREFIX) and name.endswith(SKIP_ARCHIVE_SUFFIX)) or name in ("", ".", ".."):
            continue
        length = response.findtext(".//d:getcontentlength", default="0", namespaces=namespace)
        modified = response.findtext(".//d:getlastmodified", default="", namespaces=namespace)
        try:
            size = int(length)
        except ValueError:
            size = 0
        found.append({"name": name, "size": size, "modified": modified})
    return sorted(found, key=lambda item: item["name"], reverse=True)


def download(name: str, url: str, user: str = "", password: str = "", timeout: float = 300.0) -> Path:
    """Fetches one backup zip from a WebDAV folder into a temporary file."""
    legacy = name.startswith(PREFIX) and name.endswith(SKIP_ARCHIVE_SUFFIX)
    if Path(name).name != name or not (name == SINGLE or legacy):
        raise WebDAVError("missing", name)
    base = normalize(url)
    target = base + urllib.parse.quote(name)
    handle, path = tempfile.mkstemp(prefix="pokeldn-restore-", suffix=".zip")
    os.close(handle)
    try:
        with _open(urllib.request.Request(target, headers=_headers(user, password)), timeout) as reply, \
                open(path, "wb") as out:
            while chunk := reply.read(1 << 16):
                out.write(chunk)
    except urllib.error.HTTPError as error:
        Path(path).unlink(missing_ok=True)
        raise WebDAVError(_kind(error), str(error.code)) from error
    except OSError as error:
        Path(path).unlink(missing_ok=True)
        raise WebDAVError("network", str(error)) from error
    return Path(path)
