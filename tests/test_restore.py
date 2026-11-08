import json
import zipfile
from pathlib import Path

import pytest

from pokeldn.app import backup, restore, settings as settings_module
from pokeldn.app.settings import Settings


@pytest.fixture
def local(tmp_path, monkeypatch):
    data = tmp_path / "data"
    paths = {"DATA": data, "POKEMON": data / "pokemon", "BANK": tmp_path / "Bank",
             "RECEIVED": tmp_path / "Received", "SAVES": tmp_path / "Saves",
             "GTS": tmp_path / "GTS", "MACROS": tmp_path / "Macros"}
    for module in (backup, restore):
        for name, folder in paths.items():
            monkeypatch.setattr(module, name, folder)
    monkeypatch.setattr(backup, "SETTINGS_PATH", data / "settings.json")
    monkeypatch.setattr(settings_module, "PATH", data / "settings.json")
    monkeypatch.setattr(settings_module, "STAGED", data / "settings.restore.json")
    (data / "plugins/community-zh-hans").mkdir(parents=True)
    (data / "plugins/community-zh-hans/plugin.toml").write_text("name = 'pack'\n", encoding="utf-8")
    (data / "plugin-data/pack").mkdir(parents=True)
    (data / "plugin-data/pack/state.json").write_text("{}", encoding="utf-8")
    (data / "pokemon/sv").mkdir(parents=True)
    (data / "pokemon/sv/Cloud-20260101-120000-11111111.pk9").write_bytes(b"cloud-pokemon")
    (tmp_path / "Bank").mkdir()
    (tmp_path / "Bank/Cloud.pk9").write_bytes(b"cloud-bank")
    (tmp_path / "Received").mkdir()
    (tmp_path / "Received/gift.pk9").write_bytes(b"gift")
    (tmp_path / "Saves").mkdir()
    (tmp_path / "Saves/cloud.sav").write_bytes(b"save")
    (tmp_path / "GTS").mkdir()
    (tmp_path / "GTS/cloud.json").write_text("{}", encoding="utf-8")
    (tmp_path / "Macros").mkdir()
    (tmp_path / "Macros/cloud.json").write_text("{}", encoding="utf-8")
    (data / "settings.json").write_text(json.dumps({"ot": "CLOUD", "webdav_password": "secret"}),
                                       encoding="utf-8")
    (tmp_path / "prod.keys").write_bytes(b"CLOUD-KEYS")
    return tmp_path


def make_backup(tmp_path):
    result = backup.create(include_keys=True, keys_path=str(tmp_path / "prod.keys"))
    return result, restore.inspect(result.path)


def cloud_settings(tmp_path):
    return Settings(ot="LOCAL", keys=str(tmp_path / "prod.keys"), backup_dir=str(tmp_path / "Backups"),
                    webdav_url="https://dav.example/dav/", webdav_user="me",
                    webdav_password="LOCAL-PASSWORD", backup_keys=True,
                    radio_port="COM9")


def test_cloud_restore_replaces_data_and_keeps_local_settings(local):
    result, info = make_backup(local)
    try:
        assert info.files == 10 and info.has_keys and info.has_settings
        assert info.categories["bank"] == 1 and info.categories["keys"] == 1
        (local / "Bank/LocalOnly.pk9").write_bytes(b"local-only")
        (local / "Bank/Cloud.pk9").write_bytes(b"changed-here")
        (local / "prod.keys").write_bytes(b"LOCAL-KEYS")
        current = cloud_settings(local)
        outcome = restore.apply(result.path, info, "cloud", current)
        assert outcome.files == 10 and outcome.settings and outcome.keys
        assert not (local / "Bank/LocalOnly.pk9").exists()
        assert (local / "Bank/Cloud.pk9").read_bytes() == b"cloud-bank"
        assert (local / "data/pokemon/sv/Cloud-20260101-120000-11111111.pk9").read_bytes() == b"cloud-pokemon"
        assert (local / "prod.keys").read_bytes() == b"CLOUD-KEYS"
        staged = json.loads((local / "data/settings.restore.json").read_text(encoding="utf-8"))
        assert staged["ot"] == "CLOUD"
        assert staged["keys"] == str(local / "prod.keys") and staged["radio_port"] == "COM9"
        assert staged["webdav_password"] == "LOCAL-PASSWORD"
        assert not any(local.rglob("pokeldn-before-restore.zip"))
    finally:
        result.discard()


def test_local_restore_only_adds_missing_files(local):
    result, info = make_backup(local)
    try:
        (local / "Bank/Cloud.pk9").write_bytes(b"local-version")
        (local / "Bank/LocalOnly.pk9").write_bytes(b"local-only")
        (local / "prod.keys").write_bytes(b"LOCAL-KEYS")
        (local / "data/pokemon/sv/Cloud-20260101-120000-11111111.pk9").unlink()
        outcome = restore.apply(result.path, info, "local", cloud_settings(local))
        assert not outcome.settings and not outcome.keys
        assert (local / "Bank/Cloud.pk9").read_bytes() == b"local-version"
        assert (local / "Bank/LocalOnly.pk9").read_bytes() == b"local-only"
        assert (local / "data/pokemon/sv/Cloud-20260101-120000-11111111.pk9").read_bytes() == b"cloud-pokemon"
        assert not (local / "data/settings.restore.json").exists()
        assert (local / "prod.keys").read_bytes() == b"LOCAL-KEYS"
        assert outcome.categories == {"pokemon": 1}
    finally:
        result.discard()


def test_settings_restore_file_is_applied_once(local):
    staged = local / "data/settings.restore.json"
    target = local / "data/settings.json"
    staged.write_text(json.dumps({"ot": "RESTORED", "webdav_password": "pw"}), encoding="utf-8")
    settings_module._apply_staged()
    assert json.loads(target.read_text(encoding="utf-8"))["ot"] == "RESTORED"
    assert not staged.exists()


def test_a_member_outside_its_folder_is_not_written(local, tmp_path):
    top = "pokeldn-backup-20260101-120000"
    archive = tmp_path / "sneaky.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(f"{top}/manifest.json", json.dumps({"app": "pokeldn", "files": 1}))
        z.writestr(f"{top}/bank/../../evil.pk9", b"outside")
        z.writestr(f"{top}/bank/ok.pk9", b"inside")
    info = restore.inspect(archive)
    outcome = restore.apply(archive, info, "cloud", cloud_settings(local))
    assert (local / "Bank/ok.pk9").read_bytes() == b"inside"
    assert not (tmp_path / "evil.pk9").exists() and not (local / "Bank/evil.pk9").exists()


def test_a_file_that_is_not_a_pokeldn_backup_is_refused(tmp_path):
    archive = tmp_path / "other.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("readme.txt", "hello")
    with pytest.raises(restore.RestoreError):
        restore.inspect(archive)
