"""
Module: database.py
Purpose: Single-file SQLite storage for all application data.
Replaces: settings.json, lineup_library.yaml, lineup_events.yaml,
          window_state.json, auto_save.json
"""

import json
import logging
import os
import sqlite3
import threading

log = logging.getLogger("database")

# Thread-local storage for per-thread connections
_local = threading.local()


class Database:
    """Manages a single SQLite database file for all application data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    # ── Connection management ─────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return a thread-local connection (one per thread)."""
        if not hasattr(_local, "connections"):
            _local.connections = {}
        conn = _local.connections.get(self.db_path)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            _local.connections[self.db_path] = conn
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS kv (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS djs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                stream     TEXT    NOT NULL DEFAULT '',
                exact_link INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS genres (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS titles (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS events (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                title               TEXT    NOT NULL DEFAULT '',
                vol                 TEXT    NOT NULL DEFAULT '',
                group_name          TEXT    NOT NULL DEFAULT '',
                collab              INTEGER NOT NULL DEFAULT 0,
                collab_with         TEXT    NOT NULL DEFAULT '',
                created_at          TEXT    NOT NULL DEFAULT '',
                timestamp           TEXT    NOT NULL DEFAULT '',
                names_only          INTEGER NOT NULL DEFAULT 0,
                social_links        TEXT    NOT NULL DEFAULT '{}',
                discord_embed_image TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS event_slots (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                name     TEXT    NOT NULL DEFAULT '',
                genre    TEXT    NOT NULL DEFAULT '',
                club     TEXT    NOT NULL DEFAULT '',
                duration INTEGER NOT NULL DEFAULT 60,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS event_genres (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                genre    TEXT    NOT NULL DEFAULT '',
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );
        """)
        # Safely add the club column if it doesn't exist for legacy DB users
        try:
            conn.execute("ALTER TABLE event_slots ADD COLUMN club TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        conn.commit()

    # ── Key-Value store (settings, window state, auto-save, etc.) ─────────

    def kv_get(self, key: str, default=None):
        """Retrieve a JSON-deserialized value from the kv table."""
        with self._lock:
            row = self._get_conn().execute(
                "SELECT value FROM kv WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return default

    def kv_set(self, key: str, value):
        """Store a JSON-serialized value into the kv table."""
        blob = json.dumps(value, ensure_ascii=False)
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                (key, blob),
            )
            conn.commit()

    def kv_delete(self, key: str):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            conn.commit()

    # ── DJs ───────────────────────────────────────────────────────────────

    def get_all_djs(self) -> list[dict]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT name, stream, exact_link FROM djs ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [
            {"name": r["name"], "stream": r["stream"],
             "exact_link": bool(r["exact_link"])}
            for r in rows
        ]

    def upsert_dj(self, name: str, stream: str = "", exact_link: bool = False):
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO djs (name, stream, exact_link) VALUES (?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET stream=excluded.stream,
                   exact_link=excluded.exact_link""",
                (name, stream, int(exact_link)),
            )
            conn.commit()

    def delete_dj(self, name: str):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM djs WHERE name = ?", (name,))
            conn.commit()

    def save_all_djs(self, djs: list[dict]):
        """Replace the entire djs table with the given list."""
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM djs")
            conn.executemany(
                "INSERT INTO djs (name, stream, exact_link) VALUES (?, ?, ?)",
                [(d["name"], d.get("stream", ""), int(d.get("exact_link", False)))
                 for d in djs if d.get("name")],
            )
            conn.commit()

    # ── Genres ────────────────────────────────────────────────────────────

    def get_all_genres(self) -> list[str]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT name FROM genres ORDER BY name"
            ).fetchall()
        return [r["name"] for r in rows]

    def save_all_genres(self, genres: list[str]):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM genres")
            conn.executemany(
                "INSERT OR IGNORE INTO genres (name) VALUES (?)",
                [(g,) for g in genres if g],
            )
            conn.commit()

    # ── Titles ────────────────────────────────────────────────────────────

    def get_all_titles(self) -> list[str]:
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT name FROM titles ORDER BY name"
            ).fetchall()
        return [r["name"] for r in rows]

    def save_all_titles(self, titles: list[str]):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM titles")
            conn.executemany(
                "INSERT OR IGNORE INTO titles (name) VALUES (?)",
                [(t,) for t in titles if t],
            )
            conn.commit()

    # ── Events ────────────────────────────────────────────────────────────

    def get_all_events(self) -> list[dict]:
        """Return all events with their slots and genres, sorted by created_at desc."""
        with self._lock:
            conn = self._get_conn()
            event_rows = conn.execute(
                "SELECT * FROM events ORDER BY created_at DESC"
            ).fetchall()

            events = []
            for er in event_rows:
                eid = er["id"]
                slot_rows = conn.execute(
                    "SELECT name, genre, club, duration FROM event_slots "
                    "WHERE event_id = ? ORDER BY position", (eid,)
                ).fetchall()
                genre_rows = conn.execute(
                    "SELECT genre FROM event_genres WHERE event_id = ?", (eid,)
                ).fetchall()

                events.append({
                    "_db_id": eid,
                    "title": er["title"],
                    "vol": er["vol"],
                    "group_name": er["group_name"],
                    "collab": bool(er["collab"]),
                    "collab_with": er["collab_with"],
                    "created_at": er["created_at"],
                    "timestamp": er["timestamp"],
                    "names_only": bool(er["names_only"]),
                    "social_links": json.loads(er["social_links"] or "{}"),
                    "discord_embed_image": er["discord_embed_image"],
                    "genres": [gr["genre"] for gr in genre_rows],
                    "slots": [
                        {"name": sr["name"], "genre": sr["genre"], "club": sr["club"],
                         "duration": sr["duration"]}
                        for sr in slot_rows
                    ],
                })
        return events

    def save_event(self, event_data: dict) -> int:
        """Insert or update an event. Returns the event's database ID."""
        with self._lock:
            conn = self._get_conn()
            db_id = event_data.get("_db_id")

            social = json.dumps(event_data.get("social_links", {}), ensure_ascii=False)
            params = (
                event_data.get("title", ""),
                event_data.get("vol", ""),
                event_data.get("group_name", ""),
                int(event_data.get("collab", False)),
                event_data.get("collab_with", ""),
                event_data.get("created_at", ""),
                event_data.get("timestamp", ""),
                int(event_data.get("names_only", False)),
                social,
                event_data.get("discord_embed_image", ""),
            )

            if db_id is not None:
                conn.execute(
                    """UPDATE events SET title=?, vol=?, group_name=?, collab=?,
                       collab_with=?, created_at=?, timestamp=?, names_only=?,
                       social_links=?, discord_embed_image=? WHERE id=?""",
                    params + (db_id,),
                )
            else:
                cur = conn.execute(
                    """INSERT INTO events (title, vol, group_name, collab,
                       collab_with, created_at, timestamp, names_only,
                       social_links, discord_embed_image)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    params,
                )
                db_id = cur.lastrowid
                event_data["_db_id"] = db_id

            # Replace slots
            conn.execute("DELETE FROM event_slots WHERE event_id = ?", (db_id,))
            for pos, slot in enumerate(event_data.get("slots", [])):
                conn.execute(
                    "INSERT INTO event_slots (event_id, position, name, genre, club, duration) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (db_id, pos, slot.get("name", ""), slot.get("genre", ""), slot.get("club", ""),
                     int(slot.get("duration", 60))),
                )

            # Replace genres
            conn.execute("DELETE FROM event_genres WHERE event_id = ?", (db_id,))
            for genre in event_data.get("genres", []):
                conn.execute(
                    "INSERT INTO event_genres (event_id, genre) VALUES (?, ?)",
                    (db_id, genre),
                )

            conn.commit()
        return db_id

    def delete_event(self, event_data: dict):
        """Delete an event by its _db_id."""
        db_id = event_data.get("_db_id")
        if db_id is None:
            return
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM events WHERE id = ?", (db_id,))
            conn.commit()

    def save_all_events(self, events: list[dict]):
        """Replace all events (used during migration)."""
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM event_genres")
            conn.execute("DELETE FROM event_slots")
            conn.execute("DELETE FROM events")
            conn.commit()
        # Re-insert each event (releases/re-acquires lock per event)
        for ev in events:
            ev.pop("_db_id", None)
            self.save_event(ev)

    # ── Migration from legacy files ───────────────────────────────────────

    def migrate_from_legacy(self, data_dir: str, sync_dir: str = ""):
        """Import data from old YAML/JSON files into SQLite, then rename them."""
        import yaml

        base = sync_dir if (sync_dir and os.path.isdir(sync_dir)) else data_dir
        migrated_any = False

        # ── Library (YAML) ────────────────────────────────────────────────
        for lib_file in [os.path.join(base, "lineup_library.yaml"),
                         os.path.join(base, "lineup_data.yaml")]:
            if os.path.isfile(lib_file):
                try:
                    with open(lib_file, "r", encoding="utf-8") as f:
                        lib = yaml.safe_load(f) or {}
                    # DJs
                    raw_djs = lib.get("djs", []) or []
                    djs = []
                    for _d in raw_djs:
                        if not isinstance(_d, dict):
                            name = _d or ""
                            if name:
                                djs.append({"name": name, "stream": ""})
                        else:
                            name = _d.get("name") or ""
                            if name:
                                stream = _d.get("stream") or _d.get("goggles") or _d.get("link") or ""
                                djs.append({"name": name, "stream": stream,
                                            "exact_link": _d.get("exact_link", False)})
                    if djs:
                        self.save_all_djs(djs)
                    # Genres
                    genres = lib.get("genres", [])
                    if genres:
                        self.save_all_genres(genres)
                    # Titles
                    titles = lib.get("titles", [])
                    if titles:
                        self.save_all_titles(titles)
                    os.rename(lib_file, lib_file + ".migrated")
                    migrated_any = True
                    log.info("Migrated library from %s", lib_file)
                    break
                except Exception as e:
                    log.warning("Failed to migrate %s: %s", lib_file, e)

        # ── Events (YAML) ────────────────────────────────────────────────
        for evt_file in [os.path.join(base, "lineup_events.yaml")]:
            if os.path.isfile(evt_file):
                try:
                    with open(evt_file, "r", encoding="utf-8") as f:
                        evts = yaml.safe_load(f) or {}
                    raw_events = evts.get("events", []) if isinstance(evts, dict) else []
                    if raw_events:
                        self.save_all_events(raw_events)
                    os.rename(evt_file, evt_file + ".migrated")
                    migrated_any = True
                    log.info("Migrated events from %s", evt_file)
                    break
                except Exception as e:
                    log.warning("Failed to migrate %s: %s", evt_file, e)

        # ── Settings (JSON) ──────────────────────────────────────────────
        settings_file = os.path.join(data_dir, "settings.json")
        if os.path.isfile(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.kv_set("settings", data)
                os.rename(settings_file, settings_file + ".migrated")
                migrated_any = True
                log.info("Migrated settings from %s", settings_file)
            except Exception as e:
                log.warning("Failed to migrate %s: %s", settings_file, e)

        # ── Window state (JSON) ──────────────────────────────────────────
        ws_file = os.path.join(data_dir, "window_state.json")
        if os.path.isfile(ws_file):
            try:
                with open(ws_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.kv_set("window_state", data)
                os.rename(ws_file, ws_file + ".migrated")
                migrated_any = True
                log.info("Migrated window state from %s", ws_file)
            except Exception as e:
                log.warning("Failed to migrate %s: %s", ws_file, e)

        # ── Auto-save (JSON) ─────────────────────────────────────────────
        auto_file = os.path.join(data_dir, "auto_save.json")
        if os.path.isfile(auto_file):
            try:
                with open(auto_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.kv_set("auto_save", data)
                os.rename(auto_file, auto_file + ".migrated")
                migrated_any = True
                log.info("Migrated auto-save from %s", auto_file)
            except Exception as e:
                log.warning("Failed to migrate %s: %s", auto_file, e)

        if migrated_any:
            log.info("Legacy migration complete. Old files renamed to *.migrated")

    def close(self):
        """Close all thread-local connections."""
        if hasattr(_local, "connections"):
            conn = _local.connections.pop(self.db_path, None)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
