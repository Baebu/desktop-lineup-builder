import queue
import threading


class DebounceMixin:
    """Thread-safe debounce helpers using threading.Timer + a per-frame work queue."""

    def _init_debounce(self):
        self._update_job       = None
        self._roster_job       = None
        self._save_lib_job     = None
        self._auto_save_job    = None
        self._work_queue: queue.SimpleQueue = queue.SimpleQueue()

    def _queue_on_main(self, fn):
        """Push *fn* onto the main-thread queue; executed in process_queue()."""
        self._work_queue.put(fn)

    def process_queue(self):
        """Call once per DPG frame from the main render loop."""
        while not self._work_queue.empty():
            try:
                self._work_queue.get_nowait()()
            except Exception:
                pass

    # ── Timer helpers ─────────────────────────────────────────────────────

    def _cancel(self, attr: str):
        job = getattr(self, attr, None)
        if job is not None:
            job.cancel()
            setattr(self, attr, None)

    def _timer(self, attr: str, delay_s: float, target):
        self._cancel(attr)
        
        timer_ref = []
        
        def on_timeout():
            t = timer_ref[0]
            def execute():
                # Only execute if this timer is STILL the active job
                if getattr(self, attr, None) is t:
                    setattr(self, attr, None)
                    target()
            self._queue_on_main(execute)
            
        t = threading.Timer(delay_s, on_timeout)
        timer_ref.append(t)
        t.daemon = True
        t.start()
        setattr(self, attr, t)

    # ── Public debounce gates ─────────────────────────────────────────────

    def _schedule_update(self, delay: int = 150):
        self._is_dirty = True
        self._timer("_update_job", delay / 1000, self._run_scheduled_update)
        self._schedule_auto_save()

    def _run_scheduled_update(self):
        self.update_output()

    def _schedule_auto_save(self, delay: int = 5000):
        self._timer("_auto_save_job", delay / 1000, self._run_scheduled_auto_save)

    def _run_scheduled_auto_save(self):
        if hasattr(self, "_save_current_state_to_auto_save"):
            self._save_current_state_to_auto_save()

    def _schedule_roster_refresh(self, delay: int = 120):
        self._timer("_roster_job", delay / 1000, self._run_scheduled_roster_refresh)

    def _run_scheduled_roster_refresh(self):
        self.refresh_dj_roster_ui()

    def _schedule_genre_refresh(self, delay: int = 120):
        self._timer("_genre_refresh_job", delay / 1000, self._run_scheduled_genre_refresh)

    def _run_scheduled_genre_refresh(self):
        self.refresh_genre_tags()

    def _schedule_save_library(self, delay: int = 500):
        self._timer("_save_lib_job", delay / 1000, self._run_scheduled_save_library)

    def _run_scheduled_save_library(self):
        self._save_library()

    def _refresh_slot_combos(self):
        """Update all slot name-entry dropdowns."""
        import dearpygui.dearpygui as dpg
        names = self.get_dj_names()
        for slot in self.slots:
            try:
                tag = f"slot_{slot.id}_name"
                if dpg.does_item_exist(tag):
                    dpg.configure_item(tag, items=names)
            except Exception:
                pass