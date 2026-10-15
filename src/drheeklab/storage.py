"""Isolated permanent data and transactional, versioned SQLite schema."""
from pathlib import Path
import os
import sqlite3
import json
from contextlib import closing
from datetime import datetime, timezone
from .migration3 import STATEMENTS
from .migration4 import STATEMENTS as SALES_STATEMENTS
from .migration5 import STATEMENTS as PRODUCTION_STATEMENTS
from .migration6 import STATEMENTS as FINANCE_STATEMENTS
from .migration7 import STATEMENTS as DOCUMENT_STATEMENTS
from .migration8 import STATEMENTS as RECIPE_STATEMENTS
from .migration9 import STATEMENTS as PURCHASED_STATEMENTS
from .migration10 import STATEMENTS as ACCESSORY_STATEMENTS

FOLDERS = ("Banco de Dados", "Projetos STL e 3MF", "Fotos dos Produtos", "Orçamentos",
           "Pedidos e Comprovantes", "Catálogos", "Relatórios", "Backups", "Logs", "Marca")
ENVIRONMENTS = {"test": "TESTES", "production": "PRODUÇÃO"}
SCHEMA_VERSION = 10
MIGRATIONS = {1: (
    "CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE users (id INTEGER PRIMARY KEY CHECK(id=1), salt TEXT NOT NULL, password_hash TEXT NOT NULL, iterations INTEGER NOT NULL)",
    "CREATE TABLE audit (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, operation TEXT NOT NULL, record TEXT NOT NULL, previous TEXT, current TEXT, reason TEXT)",
    "CREATE TABLE drafts (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)",
), 2: (
    "CREATE TABLE printers (id INTEGER PRIMARY KEY, manufacturer TEXT NOT NULL, model TEXT NOT NULL, identifier TEXT NOT NULL UNIQUE, acquired_on TEXT, purchase_cents INTEGER NOT NULL CHECK(purchase_cents>=0), accumulated_minutes INTEGER NOT NULL DEFAULT 0 CHECK(accumulated_minutes>=0), investment_hour_cents INTEGER NOT NULL CHECK(investment_hour_cents>=0), energy_hour_cents INTEGER NOT NULL CHECK(energy_hour_cents>=0), maintenance_hour_cents INTEGER NOT NULL CHECK(maintenance_hour_cents>=0), status TEXT NOT NULL CHECK(status IN ('operational','maintenance','inactive')), archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)))",
    "CREATE TABLE maintenance (id INTEGER PRIMARY KEY, printer_id INTEGER NOT NULL REFERENCES printers(id), performed_on TEXT NOT NULL, description TEXT NOT NULL, cost_cents INTEGER NOT NULL CHECK(cost_cents>=0), next_due TEXT)",
    "CREATE TABLE filaments (id INTEGER PRIMARY KEY, brand TEXT NOT NULL, material TEXT NOT NULL, color TEXT NOT NULL, name TEXT NOT NULL, purchase_cents INTEGER NOT NULL CHECK(purchase_cents>=0), initial_mg INTEGER CHECK(initial_mg>0), purchased_on TEXT, supplier TEXT NOT NULL, reference_per_g TEXT NOT NULL, remaining_mg INTEGER CHECK(remaining_mg>=0), state TEXT NOT NULL CHECK(state IN ('new','open','finished')), archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)))",
    "CREATE TABLE calculations (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, title TEXT NOT NULL, printer_id INTEGER NOT NULL REFERENCES printers(id), planned TEXT NOT NULL, actual TEXT, confirmed_at TEXT)",
    "CREATE TABLE filament_consumption (id INTEGER PRIMARY KEY, calculation_id INTEGER NOT NULL REFERENCES calculations(id), filament_id INTEGER NOT NULL REFERENCES filaments(id), consumed_mg INTEGER NOT NULL CHECK(consumed_mg>=0), previous_mg INTEGER, remaining_mg INTEGER, UNIQUE(calculation_id,filament_id))",
    "INSERT INTO printers(manufacturer,model,identifier,purchase_cents,investment_hour_cents,energy_hour_cents,maintenance_hour_cents,status) VALUES('Bambu Lab','A1 Mini','A1-MINI-01',240000,75,10,25,'operational')",
    "INSERT INTO settings VALUES('markup_percent','\"200\"') ON CONFLICT(key) DO NOTHING",
    "INSERT INTO settings VALUES('low_filament_grams','\"100\"') ON CONFLICT(key) DO NOTHING",
), 3: STATEMENTS, 4: SALES_STATEMENTS, 5: PRODUCTION_STATEMENTS, 6: FINANCE_STATEMENTS, 7: DOCUMENT_STATEMENTS, 8: RECIPE_STATEMENTS, 9: PURCHASED_STATEMENTS, 10: ACCESSORY_STATEMENTS}

def now():
    return datetime.now(timezone.utc).isoformat()

class Storage:
    def __init__(self, root=None, environment="test", *, migrate=True):
        if environment not in ENVIRONMENTS:
            raise ValueError("Ambiente inválido")
        self.root = Path(root or os.environ.get("DRHEEKLAB_DATA_DIR") or
                         (r"C:\DrHeekLab" if os.name == "nt" else Path.home() / "DrHeekLab"))
        self.environment = environment
        self.home = self.root / ENVIRONMENTS[environment]
        for name in FOLDERS:
            (self.home / name).mkdir(parents=True, exist_ok=True)
        self.path = self.home / "Banco de Dados" / "drheeklab.sqlite3"
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=5000")
        try:
            if migrate:
                self.migrate()
            else:
                version=self.db.execute('PRAGMA user_version').fetchone()[0]
                if not 1<=version<=SCHEMA_VERSION:
                    raise RuntimeError('Banco de recuperação incompatível.')
        except Exception:
            self.db.close()
            raise

    def migrate(self):
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError("Banco criado por versão mais recente. Atualize o aplicativo.")
        if version and version < SCHEMA_VERSION:
            from .backup import create_backup
            try:
                create_backup(self)
            except Exception as error:
                self._migration_failure(version,error)
                raise
            # Keep original consistent database before any upgrade.
            target = self.home / "Backups" / ("pre-migration-" + datetime.now().strftime("%Y%m%d%H%M%S%f") + ".sqlite3")
            with closing(sqlite3.connect(target)) as copy, copy:
                self.db.backup(copy)
                if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup anterior à migração inválido")
        try:
            with self.db:
                self.db.execute("BEGIN IMMEDIATE")
                for number in range(version + 1, SCHEMA_VERSION + 1):
                    for statement in MIGRATIONS[number]:
                        self.db.execute(statement)
                    self.db.execute(f"PRAGMA user_version={number}")
                    self.audit("migração", "schema", version, number)
        except Exception as error:
            self._migration_failure(version,error)
            raise

    def _migration_failure(self, version, error):
        target=self.home/'Logs'/('migration-failed-'+datetime.now().strftime('%Y%m%d%H%M%S%f')+'.json')
        target.write_text(json.dumps({'from':version,'to':SCHEMA_VERSION,'status':'failed','error':str(error)},ensure_ascii=False),encoding='utf-8')

    def audit(self, operation, record, previous=None, current=None, reason=None):
        self.db.execute("INSERT INTO audit(created_at,operation,record,previous,current,reason) VALUES(?,?,?,?,?,?)",
                        (now(), operation, record, json.dumps(previous, ensure_ascii=False),
                         json.dumps(current, ensure_ascii=False), reason))

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        with self.db:
            previous = self.get(key)
            self.db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (key, json.dumps(value, ensure_ascii=False)))
            self.audit("configuração", key, previous, value)

    def save_draft(self, key, value):
        with self.db:
            self.db.execute("INSERT INTO drafts VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                            (key, value, now()))

    def load_draft(self, key):
        row = self.db.execute("SELECT value FROM drafts WHERE key=?", (key,)).fetchone()
        return row[0] if row else ""

    def close(self):
        self.db.close()
