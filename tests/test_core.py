import json
import sqlite3
import zipfile
import pytest
from drheeklab.storage import Storage, FOLDERS, SCHEMA_VERSION
from drheeklab.security import Auth
from drheeklab.backup import create_backup, verify_backup, restore_backup, daily_backup

@pytest.fixture
def store(tmp_path):
    value = Storage(tmp_path, "test")
    yield value
    try:
        value.close()
    except sqlite3.ProgrammingError:
        pass

def test_initial_schema_and_idempotent_migration(store):
    assert store.db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert store.db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    count = store.db.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
    store.migrate()
    assert store.db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == count
    assert all((store.home / name).is_dir() for name in FOLDERS)

def test_environments_are_physically_separated(store):
    production = Storage(store.root, "production")
    store.set("theme", "light")
    store.save_draft("note", "fictício")
    assert production.path != store.path
    assert production.get("theme") is None
    assert production.load_draft("note") == ""
    assert not Auth(production).configured
    production.close()

def test_password_create_change_and_audit(store):
    auth = Auth(store)
    with pytest.raises(ValueError):
        auth.create("short")
    auth.create("senha original segura")
    assert auth.verify("senha original segura")
    assert not auth.verify("incorreta")
    with pytest.raises(ValueError):
        auth.change("incorreta", "nova senha segura")
    auth.change("senha original segura", "nova senha segura")
    assert not auth.verify("senha original segura")
    assert auth.verify("nova senha segura")
    with pytest.raises(ValueError):
        auth.create("outra senha segura")
    assert b"nova senha segura" not in store.path.read_bytes()
    assert b"senha original segura" not in store.path.read_bytes()
    rows = store.db.execute("SELECT operation FROM audit").fetchall()
    assert "alteração de senha" in [r[0] for r in rows]

def test_rate_limit(store):
    auth = Auth(store)
    auth.create("senha segura")
    for _ in range(5):
        assert not auth.verify("errada")
    with pytest.raises(ValueError, match="Aguarde"):
        auth.verify("senha segura")

def test_restart_persistence(store):
    store.set("theme", "light")
    store.set("sidebar_collapsed", True)
    store.save_draft("home_notes", "rascunho após reinício")
    root = store.root
    store.close()
    reopened = Storage(root)
    assert reopened.get("theme") == "light"
    assert reopened.get("sidebar_collapsed") is True
    assert reopened.load_draft("home_notes") == "rascunho após reinício"
    reopened.close()

def test_complete_backup_and_restore(store):
    Auth(store).create("senha segura")
    store.set("theme", "light")
    store.save_draft("home_notes", "original")
    photo = store.home / "Fotos dos Produtos" / "foto.jpg"
    photo.write_bytes(b"real linked file")
    path = create_backup(store)
    assert verify_backup(path, "test")
    store.set("theme", "dark")
    store.save_draft("home_notes", "alterado")
    photo.write_bytes(b"modified")
    rollback = restore_backup(store, path)
    reopened = Storage(store.root)
    assert reopened.get("theme") == "light"
    assert reopened.load_draft("home_notes") == "original"
    assert photo.read_bytes() == b"real linked file"
    assert Auth(reopened).verify("senha segura")
    assert rollback.is_dir()
    assert reopened.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    reopened.close()

def test_restore_rejects_other_environment(store):
    path = create_backup(store)
    production = Storage(store.root, "production")
    production.set("protected", 123)
    with pytest.raises(ValueError, match="outro ambiente"):
        restore_backup(production, path)
    assert production.get("protected") == 123
    production.close()

def test_corrupt_backup_is_rejected_without_data_loss(store, tmp_path):
    store.set("protected", 42)
    path = create_backup(store)
    corrupt = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(path) as original, zipfile.ZipFile(corrupt, "w") as output:
        for name in original.namelist():
            output.writestr(name, b"corrupted" if name.endswith("sqlite3") else original.read(name))
    with pytest.raises(ValueError, match="Checksum"):
        restore_backup(store, corrupt)
    assert store.get("protected") == 42

def test_unsafe_backup_path(store, tmp_path):
    path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../escape", "bad")
    with pytest.raises(ValueError, match="inseguro"):
        restore_backup(store, path)
    assert not (tmp_path.parent / "escape").exists()

def test_daily_backup_once_per_day(store):
    assert daily_backup(store) is not None
    assert daily_backup(store) is None
    assert len(list((store.home / "Backups").glob("*.zip"))) == 1

def test_newer_schema_is_rejected(store):
    store.db.execute("PRAGMA user_version=99")
    store.db.commit()
    with pytest.raises(RuntimeError, match="mais recente"):
        Storage(store.root)
    assert store.db.execute("PRAGMA user_version").fetchone()[0] == 99

def test_transaction_rolls_back_settings_on_failure(store, monkeypatch):
    store.set("theme", "light")
    def fail(*args):
        raise RuntimeError("simulated disk failure")
    monkeypatch.setattr(store, "audit", fail)
    with pytest.raises(RuntimeError):
        store.set("theme", "dark")
    assert store.get("theme") == "light"

def test_failed_migration_keeps_original_schema_and_records(store, monkeypatch):
    import drheeklab.storage as module
    store.set("protected", "original")
    monkeypatch.setattr(module, "SCHEMA_VERSION", SCHEMA_VERSION + 1)
    monkeypatch.setitem(module.MIGRATIONS, SCHEMA_VERSION + 1, ("CREATE TABLE upgrade_probe(id INTEGER)", "INVALID SQL"))
    with pytest.raises(sqlite3.OperationalError):
        store.migrate()
    assert store.db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert store.get("protected") == "original"
    assert store.db.execute("SELECT name FROM sqlite_master WHERE name='upgrade_probe'").fetchone() is None
    copies = list((store.home / "Backups").glob("pre-migration-*.sqlite3"))
    assert len(copies) == 1
    with sqlite3.connect(copies[0]) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute("SELECT value FROM settings WHERE key='protected'").fetchone()[0] == '"original"'

def test_successful_migration_preserves_existing_records(store, monkeypatch):
    import drheeklab.storage as module
    store.set("protected", "original")
    monkeypatch.setattr(module, "SCHEMA_VERSION", SCHEMA_VERSION + 1)
    monkeypatch.setitem(module.MIGRATIONS, SCHEMA_VERSION + 1, ("CREATE TABLE upgrade_probe(id INTEGER)",))
    store.migrate()
    assert store.db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION + 1
    assert store.get("protected") == "original"
    assert store.db.execute("SELECT name FROM sqlite_master WHERE name='upgrade_probe'").fetchone() is not None
