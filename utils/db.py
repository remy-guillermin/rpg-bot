import sqlite3
import uuid
from utils.path import DB_FILE


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _migrate_inventories(conn: sqlite3.Connection) -> None:
    """Migrate old inventories table (PK: character_name, item_name) to new schema with entry_id and runes."""
    col_info = {row["name"]: row["pk"] for row in conn.execute("PRAGMA table_info(inventories)")}

    if "entry_id" not in col_info:
        # Phase 1: add entry_id and runes columns to the old schema
        conn.execute("ALTER TABLE inventories ADD COLUMN entry_id TEXT")
        conn.execute("ALTER TABLE inventories ADD COLUMN runes TEXT DEFAULT ''")
        rows = conn.execute("SELECT rowid, character_name, item_name FROM inventories").fetchall()
        for row in rows:
            conn.execute(
                "UPDATE inventories SET entry_id = ? WHERE rowid = ?",
                (str(uuid.uuid4()), row[0]),
            )
        col_info = {row["name"]: row["pk"] for row in conn.execute("PRAGMA table_info(inventories)")}

    # Phase 2: if entry_id is not the PRIMARY KEY the old composite PK is still in place.
    # SQLite does not support DROP PRIMARY KEY, so we recreate the table.
    if col_info.get("entry_id", 0) == 0:
        conn.execute("""
            CREATE TABLE inventories_new (
                entry_id          TEXT PRIMARY KEY,
                character_name    TEXT NOT NULL,
                item_name         TEXT NOT NULL,
                quantity          INTEGER DEFAULT 1,
                equipped_quantity INTEGER DEFAULT 0,
                runes             TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            INSERT INTO inventories_new
                (entry_id, character_name, item_name, quantity, equipped_quantity, runes)
            SELECT entry_id, character_name, item_name, quantity, equipped_quantity, runes
            FROM inventories
        """)
        conn.execute("DROP TABLE inventories")
        conn.execute("ALTER TABLE inventories_new RENAME TO inventories")


def _migrate_discovered_sets(conn: sqlite3.Connection) -> None:
    """Add discovered_sets column to character_status if it doesn't exist."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(character_status)")}
    if "discovered_sets" not in cols:
        conn.execute("ALTER TABLE character_status ADD COLUMN discovered_sets TEXT DEFAULT ''")


def load_location() -> tuple[str, str | None]:
    """Return (realm, city) from the location table. realm defaults to '' if no row exists."""
    with get_connection() as conn:
        row = conn.execute("SELECT realm, city FROM location WHERE id = 1").fetchone()
        if row:
            return row["realm"], row["city"] or None
        return "", None


def save_location(realm: str, city: str | None) -> None:
    """Upsert the single location row."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO location (id, realm, city) VALUES (1, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET realm = excluded.realm, city = excluded.city",
            (realm, city),
        )


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS character_assignments (
                character_name TEXT PRIMARY KEY,
                user_id        INTEGER
            );

            CREATE TABLE IF NOT EXISTS character_status (
                character_name   TEXT PRIMARY KEY,
                hp               INTEGER,
                mana             INTEGER,
                stamina          INTEGER,
                experience       INTEGER DEFAULT 0,
                kills            INTEGER DEFAULT 0,
                bosses_defeated  TEXT DEFAULT '',
                memory_fragments TEXT DEFAULT '',
                currency         INTEGER DEFAULT 0,
                discovered_sets  TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS inventories (
                entry_id          TEXT PRIMARY KEY,
                character_name    TEXT NOT NULL,
                item_name         TEXT NOT NULL,
                quantity          INTEGER DEFAULT 1,
                equipped_quantity INTEGER DEFAULT 0,
                runes             TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS power_assignments (
                character_name TEXT,
                power_name     TEXT,
                PRIMARY KEY (character_name, power_name)
            );

            CREATE TABLE IF NOT EXISTS buffs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                character_name TEXT NOT NULL,
                name           TEXT NOT NULL,
                description    TEXT,
                duration       INTEGER,
                effects        TEXT,
                source         TEXT
            );

            CREATE TABLE IF NOT EXISTS past_trades (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id                  TEXT,
                item_received_by_player   TEXT,
                item_received_by_merchant TEXT,
                currency                  INTEGER,
                player                    TEXT,
                timestamp                 TEXT
            );

            CREATE TABLE IF NOT EXISTS quest_progress (
                quest_id     TEXT PRIMARY KEY,
                status       TEXT NOT NULL,
                started_at   TEXT,
                completed_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS location (
                id    INTEGER PRIMARY KEY CHECK (id = 1),
                realm TEXT NOT NULL DEFAULT '',
                city  TEXT DEFAULT NULL
            );
        """)
        _migrate_inventories(conn)
        _migrate_discovered_sets(conn)
