import logging
import threading
from .models.types import DJInfo

log = logging.getLogger("data")

class DataMixin:
    """Handles all persistence — uses SQLite for local storage with server-first cloud sync."""

    # ── Helpers ───────────────────────────────────────────────────────────

    def _discord_id(self) -> str:
        """Return the signed-in Discord user's ID, or empty string."""
        oauth = getattr(self, "_oauth", None)
        if oauth and oauth.user_info:
            return str(oauth.user_info.get("id", ""))
        return ""

    # ── Data loading ──────────────────────────────────────────────────────

    def load_data(self):
        """Load library + events from SQLite (with optional cloud override)."""
        discord_id = self._discord_id()
        server_data = {}

        # Try fetching everything from the server if connected
        if discord_id and getattr(self, "api", None):
            try:
                server_data = self.api.get_all_user_data(discord_id)
            except Exception as exc:
                log.warning("Could not fetch cloud data: %s", exc)

        # ── Library (Titles, DJs, Genres) ────────────────────────────────
        lib = server_data.get("library", {})
        if lib:
            # Cloud update
            self.saved_titles = lib.get("titles", [])
            self.saved_djs = lib.get("djs", [])
            self.saved_genres = lib.get("genres", [])
            # Sync to local DB
            self.db.save_all_titles(self.saved_titles)
            self.db.save_all_djs(self.saved_djs)
            self.db.save_all_genres(self.saved_genres)
        else:
            # Load from SQLite
            self.saved_titles = self.db.get_all_titles()
            self.saved_djs = self.db.get_all_djs()
            self.saved_genres = self.db.get_all_genres()

        # ── Events ───────────────────────────────────────────────────────
        evts = server_data.get("events", {})
        if evts:
            raw_events = evts.get("events", [])
            self.saved_events = sorted(
                raw_events, key=lambda e: e.get("created_at", ""), reverse=True
            )
            # Sync to local DB
            self.db.save_all_events(self.saved_events)
        else:
            # Load from SQLite
            self.saved_events = self.db.get_all_events()

    def get_dj_names(self):
        return [d["name"] for d in self.saved_djs if d.get("name")]

    # ── Persistence ───────────────────────────────────────────────────────

    def save_data(self):
        """Full flush to SQLite and Cloud."""
        self._save_library()
        self._save_events()

    def _save_library(self):
        """Save titles, DJs, and genres to SQLite and Cloud."""
        # 1. Save to SQLite
        self.db.save_all_titles(self.saved_titles)
        self.db.save_all_djs(self.saved_djs)
        self.db.save_all_genres(self.saved_genres)

        # 2. Push to Cloud
        data = {
            "titles": self.saved_titles,
            "djs": self.saved_djs,
            "genres": self.saved_genres,
        }
        self._push_to_server("library", data)

    def _save_events(self):
        """Save all events to SQLite and Cloud."""
        # 1. Save to SQLite
        self.db.save_all_events(self.saved_events)

        # 2. Push to Cloud
        data = {"events": self.saved_events}
        self._push_to_server("events", data)

    def _push_to_server(self, key: str, value):
        """Push a data blob to the server using a background thread."""
        discord_id = self._discord_id()
        api = getattr(self, "api", None)
        if not discord_id or not api:
            return

        import copy
        import queue

        if not hasattr(self, "_cloud_push_queue"):
            self._cloud_push_queue = queue.Queue()
            def _worker():
                while True:
                    task = self._cloud_push_queue.get()
                    if task is None:
                        break
                    _key, _val = task
                    try:
                        api.put_user_data(discord_id, _key, _val)
                    except Exception as exc:
                        log.warning("Cloud save (%s) failed: %s", _key, exc)
                    self._cloud_push_queue.task_done()
            self._cloud_push_worker = threading.Thread(target=_worker, daemon=True)
            self._cloud_push_worker.start()

        self._cloud_push_queue.put((key, copy.deepcopy(value)))