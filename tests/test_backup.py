import json
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from pokeldn.app import backup


@pytest.fixture
def local(tmp_path, monkeypatch):
    data = tmp_path / "data"
    for name, folder in (("DATA", data), ("POKEMON", data / "pokemon"), ("BANK", tmp_path / "Bank"),
                         ("RECEIVED", tmp_path / "Received"), ("SAVES", tmp_path / "Saves"),
                         ("GTS", tmp_path / "GTS"), ("MACROS", tmp_path / "Macros")):
        monkeypatch.setattr(backup, name, folder)
    monkeypatch.setattr(backup, "SETTINGS_PATH", data / "settings.json")
    (data / "plugins/community-zh-hans").mkdir(parents=True)
    (data / "plugins/community-zh-hans/plugin.toml").write_text('name = "Chinese"\n', encoding="utf-8")
    (data / "plugins/community-zh-hans/__pycache__").mkdir()
    (data / "plugins/community-zh-hans/__pycache__/x.pyc").write_bytes(b"cache")
    (data / "plugin-data/community-zh-hans").mkdir(parents=True)
    (data / "plugin-data/community-zh-hans/state.json").write_text("{}", encoding="utf-8")
    (data / "settings.json").write_text(json.dumps(
        {"ot": "GEE", "webdav_url": "https://dav.example/dav/", "webdav_user": "link",
         "webdav_password": "secret"}), encoding="utf-8")
    (data / "pokemon/sv").mkdir(parents=True)
    (data / "pokemon/sv/Pikachu-20260101-120000-11111111.pk9").write_bytes(b"pk9")
    (tmp_path / "Bank").mkdir()
    (tmp_path / "Bank/Eevee.pk9").write_bytes(b"bank")
    (tmp_path / "Received").mkdir()
    (tmp_path / "Received/gift.pk9").write_bytes(b"gift")
    (tmp_path / "prod.keys").write_bytes(b"keys")
    return tmp_path


def test_backup_zip_keeps_folders_and_leaves_secrets_out(local):
    result = backup.create()
    try:
        assert result.files == 6 and result.skipped == 0
        assert result.path.name.startswith("pokeldn-backup-") and result.path.suffix == ".zip"
        with zipfile.ZipFile(result.path) as archive:
            names = set(archive.namelist())
            top = result.path.stem
            assert f"{top}/config/settings.json" in names
            assert f"{top}/pokemon/sv/Pikachu-20260101-120000-11111111.pk9" in names
            assert f"{top}/bank/Eevee.pk9" in names
            assert f"{top}/received/gift.pk9" in names
            assert f"{top}/plugins/community-zh-hans/plugin.toml" in names
            assert f"{top}/plugin-data/community-zh-hans/state.json" in names
            assert not any("__pycache__" in name for name in names)
            settings = json.loads(archive.read(f"{top}/config/settings.json"))
            assert settings["ot"] == "GEE" and "webdav_password" not in settings
            manifest = json.loads(archive.read(f"{top}/manifest.json"))
            assert manifest["files"] == result.files and manifest["categories"]["pokemon"] == 1
            assert "prod.keys" in manifest["note"]
    finally:
        result.discard()
    assert not result.path.parent.exists()


def test_prod_keys_is_added_only_when_asked(local):
    keys = local / "prod.keys"
    assert backup.key_file(str(keys)) == keys
    assert backup.key_file(str(local / "missing.keys")) is None
    result = backup.create(include_keys=True, keys_path=str(keys))
    try:
        assert result.files == 7 and result.categories["keys"] == 1
        with zipfile.ZipFile(result.path) as archive:
            top = result.path.stem
            assert archive.read(f"{top}/keys/prod.keys") == b"keys"
            manifest = json.loads(archive.read(f"{top}/manifest.json"))
            assert manifest["includes_keys"] is True and manifest["note"].startswith("prod.keys is included")
    finally:
        result.discard()
    missing = backup.create(include_keys=True, keys_path=str(local / "missing.keys"))
    try:
        assert missing.files == 6 and "keys" not in missing.categories
        with zipfile.ZipFile(missing.path) as archive:
            top = missing.path.stem
            assert not any(name.startswith(f"{top}/keys/") for name in archive.namelist())
            assert json.loads(archive.read(f"{top}/manifest.json"))["includes_keys"] is False
    finally:
        missing.discard()


def test_backups_of_the_same_name_do_not_replace_each_other(tmp_path):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    archive = tmp_path / "pokeldn-backup-20260101-120000.zip"
    (first / archive.name).write_bytes(b"one")
    (second / archive.name).write_bytes(b"two")
    target = tmp_path / "Backups"
    saved = backup.save_local(first / archive.name, str(target))
    again = backup.save_local(second / archive.name, str(target))
    assert saved.name == archive.name and again.name == "pokeldn-backup-20260101-120000-2.zip"
    assert saved.read_bytes() == b"one" and again.read_bytes() == b"two"


def test_the_single_backup_name_is_replaced(tmp_path):
    folder = tmp_path / "one"
    folder.mkdir()
    target = tmp_path / "Backups"
    first = folder / "pokeldn-backup-20260101-120000.zip"
    first.write_bytes(b"one")
    saved = backup.save_local(first, str(target), name=backup.SINGLE)
    assert saved == target / "pokeldn-backup.zip" and saved.read_bytes() == b"one"
    second = folder / "pokeldn-backup-20260102-120000.zip"
    second.write_bytes(b"two")
    again = backup.save_local(second, str(target), name=backup.SINGLE, replace=True)
    assert again == saved and again.read_bytes() == b"two"


@pytest.mark.parametrize("url,expected", [
    ("https://dav.example/dav", "https://dav.example/dav/"),
    ("http://127.0.0.1:8080/pokeldn/", "http://127.0.0.1:8080/pokeldn/"),
    ("https://dav.example", "https://dav.example/"),
])
def test_webdav_addresses_are_folders(url, expected):
    assert backup.normalize(url) == expected


@pytest.mark.parametrize("url", ["dav.example/dav", "ftp://dav.example/", "https://user:pw@dav.example/"])
def test_bad_webdav_addresses_are_refused(url):
    with pytest.raises(ValueError):
        backup.normalize(url)


def test_webdav_upload_puts_the_zip_with_basic_auth(tmp_path):
    seen = {}
    folder = tmp_path / "remote"
    folder.mkdir()
    archive = folder / "pokeldn-backup-20260101-120000.zip"
    archive.write_bytes(b"zip-bytes")

    class Handler(BaseHTTPRequestHandler):
        def do_MKCOL(self):
            self.send_response(405 if seen.get("made") else 201)
            self.end_headers()
            seen["made"] = True

        def do_PUT(self):
            seen["path"] = self.path
            seen["auth"] = self.headers.get("Authorization")
            seen["body"] = self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(201)
            self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/dav"
        target = backup.upload(archive, url, "link", "secret")
        assert target == f"http://127.0.0.1:{server.server_port}/dav/pokeldn-backup-20260101-120000.zip"
        assert seen["path"] == "/dav/pokeldn-backup-20260101-120000.zip"
        assert seen["auth"].startswith("Basic ")
        assert seen["body"] == b"zip-bytes"
    finally:
        server.shutdown()
        server.server_close()


def test_webdav_lists_only_pokeldn_backup_zips(tmp_path):
    body = b"""<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:">
  <d:response><d:href>/dav/</d:href><d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop></d:propstat></d:response>
  <d:response><d:href>/dav/pokeldn-backup-20260101-120000.zip</d:href><d:propstat><d:prop><d:getcontentlength>11</d:getcontentlength><d:getlastmodified>Thu, 01 Jan 2026 12:00:00 GMT</d:getlastmodified></d:prop></d:propstat></d:response>
  <d:response><d:href>/dav/pokeldn-backup-20260102-120000.zip</d:href><d:propstat><d:prop><d:getcontentlength>22</d:getcontentlength><d:getlastmodified>Fri, 02 Jan 2026 12:00:00 GMT</d:getlastmodified></d:prop></d:propstat></d:response>
  <d:response><d:href>/dav/notes.txt</d:href><d:propstat><d:prop><d:getcontentlength>3</d:getcontentlength></d:prop></d:propstat></d:response>
</d:multistatus>"""

    class Handler(BaseHTTPRequestHandler):
        def do_PROPFIND(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            self.send_response(207)
            self.send_header("Content-Type", "application/xml")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", "7")
            self.end_headers()
            self.wfile.write(b"zipdata")

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/dav/"
        items = backup.list_backups(url)
        assert [item["name"] for item in items] == [
            "pokeldn-backup-20260102-120000.zip", "pokeldn-backup-20260101-120000.zip"]
        assert [item["size"] for item in items] == [22, 11]
        fetched = backup.download(items[0]["name"], url)
        try:
            assert fetched.read_bytes() == b"zipdata"
        finally:
            fetched.unlink()
    finally:
        server.shutdown()
        server.server_close()


def test_connection_test_reads_a_webdav_answer(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_PROPFIND(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            self.send_response(207)
            self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/dav/"
        assert backup.probe(url) == "ok"
        assert backup.probe("not-a-url") == "invalid"
    finally:
        server.shutdown()
        server.server_close()
