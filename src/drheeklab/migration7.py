STATEMENTS = (
    "CREATE TABLE generated_documents(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT NOT NULL UNIQUE,kind TEXT NOT NULL CHECK(kind IN('finance','production','catalog')),stream TEXT NOT NULL,version INTEGER NOT NULL CHECK(version>0),title TEXT NOT NULL,path TEXT NOT NULL UNIQUE,sha256 TEXT NOT NULL,snapshot TEXT NOT NULL,created_at TEXT NOT NULL,archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN(0,1)),UNIQUE(kind,stream,version))",
    "CREATE TABLE notification_states(key TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,active INTEGER NOT NULL CHECK(active IN(0,1)),seen_at TEXT,snoozed_until TEXT)",
    "ALTER TABLE product_photos ADD COLUMN archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN(0,1))",
    "ALTER TABLE project_versions ADD COLUMN archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN(0,1))",
    "INSERT INTO settings VALUES('notification_days','7') ON CONFLICT(key) DO NOTHING",
)
