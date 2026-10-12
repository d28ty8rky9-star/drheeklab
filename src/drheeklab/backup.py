"""Consistent SQLite snapshots, linked files, checksums and safe staged restore."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime
from .storage import SCHEMA_VERSION

DB_PATH = "Banco de Dados/drheeklab.sqlite3"

class LinkedFileError(ValueError):
    """A readable database references a missing or externally changed owned file."""


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def check_db(path):
    with closing(sqlite3.connect(path)) as db, db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Integridade do banco inválida.")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Vínculos do banco inválidos.")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if not 1 <= version <= SCHEMA_VERSION:
            raise ValueError("Esquema de backup incompatível.")
        for name in ("settings", "users", "audit", "drafts"):
            db.execute(f"SELECT * FROM {name} LIMIT 0")
        if version >= 2:
            for name in ('printers', 'maintenance', 'filaments', 'calculations', 'filament_consumption'):
                db.execute(f"SELECT * FROM {name} LIMIT 0")
        if version >= 3:
            for name in ('products', 'variants', 'product_photos', 'project_versions', 'materials', 'receipts', 'reservations', 'pieces', 'piece_reviews', 'losses', 'loss_pieces', 'stock_movements'):
                db.execute(f'SELECT * FROM {name} LIMIT 0')
        if version >= 4:
            for name in ('clients','quotes','orders','order_items','order_fulfillment','installments','payments','payment_allocations','installment_allocations','client_credit','cancellations','refunds','deliveries','sales_attachments','sales_documents','order_item_calculations','document_sequences','order_returns'):
                db.execute(f'SELECT * FROM {name} LIMIT 0')
        if version >= 5:
            for name in ("production_orders", "production_entries", "production_attempts", "production_pieces", "inspections", "inspection_photos", "production_problems"):
                db.execute(f"SELECT * FROM {name} LIMIT 0")
        if version >= 6:
            for name in ("expense_categories","payables","payable_installments","payable_payments","finance_entries","finance_proofs","financial_costs","financial_returns","finance_purchases"):
                db.execute(f"SELECT * FROM {name} LIMIT 0")
        if version >= 7:
            for name in ("generated_documents","notification_states"):
                db.execute(f"SELECT * FROM {name} LIMIT 0")
        return version

def check_linked_files(db_path):
    root = Path(db_path).parent.parent.resolve()
    with closing(sqlite3.connect(db_path)) as db, db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version < 3:
            return
        media=[('product_photos', 'Fotos dos Produtos'), ('project_versions', 'Projetos STL e 3MF')]
        if version >= 4:
            media.extend([('sales_attachments',None),('sales_documents',None)])
        if version >= 5:
            media.append(('inspection_photos', 'Fotos dos Produtos'))
        if version >= 6:
            media.append(('finance_proofs', 'Pedidos e Comprovantes'))
        if version >= 7:
            media.append(('generated_documents',None))
        for table, folder in media:
            for relative, expected in db.execute(f'SELECT path,sha256 FROM {table}'):
                rel = PurePosixPath(relative)
                path = (root / relative).resolve()
                if rel.is_absolute() or len(rel.parts) != 2 or (rel.parts[0] != folder if folder else rel.parts[0] not in (('Catálogos','Relatórios') if table=='generated_documents' else ('Orçamentos','Pedidos e Comprovantes'))) or not path.is_relative_to(root):
                    raise ValueError('Referência de arquivo fora do armazenamento permitido.')
                if not path.is_file() or digest(path) != expected:
                    raise LinkedFileError('Arquivo vinculado ausente ou alterado; backup completo inválido.')

def create_backup(storage, destination=None, *, password=None):
    from uuid import uuid4
    from .backup_crypto import encrypt_file,validate_password
    if password is not None:validate_password(password)
    directory = Path(destination) if destination else storage.home / "Backups"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / ("drheeklab-" + storage.environment + "-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + (".hbk" if password is not None else ".zip"))
    partial=directory/('.'+uuid4().hex+'.part')
    try:
        with tempfile.TemporaryDirectory(prefix='drheek-backup-') as temporary:
            stage = Path(temporary)/'data';stage.mkdir()
            db_file = stage / DB_PATH
            db_file.parent.mkdir(parents=True)
            with closing(sqlite3.connect(db_file)) as copy, copy:storage.db.backup(copy)
            version = check_db(db_file)
            for name in ("Projetos STL e 3MF", "Fotos dos Produtos", "Orçamentos", "Pedidos e Comprovantes", "Catálogos", "Relatórios", "Marca"):
                source=storage.home/name
                if source.is_symlink() or any(p.is_symlink() for p in source.rglob('*')):
                    raise ValueError('Backup não aceita links simbólicos nas pastas gerenciadas.')
                shutil.copytree(source, stage / name)
            check_linked_files(db_file)
            files = {p.relative_to(stage).as_posix(): digest(p) for p in stage.rglob("*") if p.is_file()}
            manifest = {"format": 1, "environment": storage.environment, "schema": version, "files": files}
            archive_path=Path(temporary)/'snapshot.zip'
            with zipfile.ZipFile(archive_path, "x", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
                for name in files:archive.write(stage / name, name)
            verify_backup(archive_path, storage.environment)
            if password is not None:encrypt_file(archive_path,partial,password)
            else:
                with archive_path.open('rb') as source,partial.open('xb') as output:
                    shutil.copyfileobj(source,output);output.flush();os.fsync(output.fileno())
            verify_backup(partial,storage.environment,password=password)
            partial.replace(target)
        with storage.db:
            storage.audit("backup", target.name, None, {'encrypted':password is not None,'verified':True})
        return target
    finally:partial.unlink(missing_ok=True)

def unpack_verified(path, stage, environment, *, password=None):
    from .backup_crypto import is_encrypted,decrypt_file
    if is_encrypted(path):
        if password is None:raise ValueError('Este backup é criptografado. Informe a senha de backup, que pode ser diferente do login.')
        with tempfile.TemporaryDirectory(prefix='drheek-decrypt-') as temporary:
            plain=Path(temporary)/'verified.zip'
            decrypt_file(path,plain,password)
            return _unpack_zip_verified(plain,stage,environment)
    return _unpack_zip_verified(path,stage,environment)

def _unpack_zip_verified(path, stage, environment):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Entradas duplicadas no backup.")
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
                raise ValueError("Caminho inseguro no backup.")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest["format"] != 1 or not 1 <= manifest["schema"] <= SCHEMA_VERSION:
            raise ValueError("Formato de backup incompatível.")
        if manifest["environment"] != environment:
            raise ValueError("Backup pertence a outro ambiente. Testes e produção não podem ser misturados.")
        if set(names) != set(manifest["files"]) | {"manifest.json"} or DB_PATH not in manifest["files"]:
            raise ValueError("Conteúdo do backup não corresponde ao manifesto.")
        allowed = {"Banco de Dados", "Projetos STL e 3MF", "Fotos dos Produtos", "Orçamentos", "Pedidos e Comprovantes", "Catálogos", "Relatórios", "Marca"}
        for name, expected in manifest["files"].items():
            if PurePosixPath(name).parts[0] not in allowed or (name.startswith("Banco de Dados/") and name != DB_PATH):
                raise ValueError("Arquivo inesperado no backup.")
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, dest.open("wb") as output:
                shutil.copyfileobj(source, output)
            if digest(dest) != expected:
                raise ValueError("Checksum do backup inválido.")
        if check_db(stage / DB_PATH) != manifest["schema"]:
            raise ValueError("Versão do banco não corresponde ao manifesto.")
        check_linked_files(stage / DB_PATH)

def verify_backup(path, environment, *, password=None):
    with tempfile.TemporaryDirectory() as temp:
        unpack_verified(path, Path(temp), environment,password=password)
    return True

def restore_backup(storage, path, *, password=None):
    # Caller must obtain explicit confirmation and restart after restoration.
    previous_linked_files_complete = True
    previous_database_integrity = True
    try:
        current_version=storage.db.execute('PRAGMA user_version').fetchone()[0]
    except sqlite3.DatabaseError:
        current_version=None
    if current_version is not None and current_version>SCHEMA_VERSION:
        raise ValueError('Banco criado por versão mais recente; restauração não pode rebaixar o esquema.')
    with tempfile.TemporaryDirectory(dir=storage.root) as temp:
        stage = Path(temp)
        unpack_verified(path, stage, storage.environment,password=password)
        try:
            create_backup(storage)
        except (LinkedFileError,sqlite3.DatabaseError,ValueError):
            previous_linked_files_complete = False
            try:
                check_db(storage.path)
            except (sqlite3.DatabaseError,ValueError):
                previous_database_integrity = False
            if previous_database_integrity:
                preservation = storage.home / 'Backups' / ('pre-restore-' + datetime.now().strftime('%Y%m%d%H%M%S%f') + '.sqlite3')
                with closing(sqlite3.connect(preservation)) as copy, copy:
                    storage.db.backup(copy)
                check_db(preservation)
                with storage.db:
                    storage.audit('preservação antes da restauração', preservation.name, None,
                                  {'linked_files_complete': False}, 'Estado anterior incompleto; árvore original será preservada em rollback')
            # A damaged database is retained byte-for-byte in the rollback tree.
            # It is never described as a verified backup.
        storage.close()
        rollback = storage.home.with_name(storage.home.name + "-rollback-" + datetime.now().strftime("%Y%m%d%H%M%S%f"))
        storage.home.rename(rollback)
        try:
            shutil.copytree(rollback, storage.home)
            for name in ("Banco de Dados", "Projetos STL e 3MF", "Fotos dos Produtos", "Orçamentos", "Pedidos e Comprovantes", "Catálogos", "Relatórios", "Marca"):
                shutil.rmtree(storage.home / name)
                if (stage / name).exists():
                    shutil.copytree(stage / name, storage.home / name)
                else:
                    (storage.home / name).mkdir()
        except Exception:
            shutil.rmtree(storage.home, ignore_errors=True)
            rollback.rename(storage.home)
            raise
    # Record restoration in the restored database without logging private data.
    with closing(sqlite3.connect(storage.path)) as restored, restored:
        from .storage import now
        restored.execute("INSERT INTO audit(created_at,operation,record,previous,current,reason) VALUES(?,?,?,?,?,?)",
                         (now(), "restauração", "backup", json.dumps({"linked_files_complete": previous_linked_files_complete, "database_integrity": previous_database_integrity, "rollback_folder": rollback.name}), "null", "Restauração confirmada pelo usuário; estado anterior preservado em rollback"))
    # Retain rollback even on success for recovery.
    return rollback

def daily_backup(storage):
    today = datetime.now().date().isoformat()
    if storage.get("last_daily_backup") != today:
        result = create_backup(storage)
        storage.set("last_daily_backup", today)
        return result
