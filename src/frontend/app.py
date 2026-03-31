"""
Module: app.py
Purpose: App class — composes all mixins, owns DPG lifecycle.
"""
import datetime
import logging
import os

import dearpygui.dearpygui as dpg

from ..backend.services.discord_service import DiscordService
from ..backend.services.discord_oauth import DiscordOAuth
from ..backend.models.event_bus import EventBus
from ..backend.models.lineup_model import LineupModel
from ..backend.output.output_builder import OutputMixin
from ..backend.data_manager import DataMixin
from ..backend.debounce import DebounceMixin
from ..backend.database import Database

from .mixins.drag_drop import DragDropMixin
from .mixins.events_manager import EventsMixin
from .mixins.keyboard_handler import KeyboardMixin
from .styling.fonts import setup_fonts
from .mixins.genre_manager import GenreMixin
from .mixins.import_parser import ImportMixin
from .mixins.roster import RosterMixin
from .mixins.sections import SectionsMixin
from .mixins.settings_manager import SettingsMixin
from .mixins.slot_manager import SlotMixin
from .ui.slot_ui import DPGBoolVar, DPGVar
from .ui import UISetupMixin
from .utils import get_data_dir, get_icon_path
from .ui.toast import tick_toasts

log = logging.getLogger("app")


class App(
    UISetupMixin,
    RosterMixin,
    DragDropMixin,
    EventsMixin,
    GenreMixin,
    SlotMixin,
    OutputMixin,
    DataMixin,
    SettingsMixin,
    SectionsMixin,
    DebounceMixin,
    ImportMixin,
    KeyboardMixin,
):
    """Main application class inheriting UI, Roster, and Logic mixins."""

    @property
    def DB_FILE(self) -> str:
        return os.path.join(get_data_dir(), "lineup_builder.db")

    def __init__(self):
        dpg.create_context()
        setup_fonts()

        self.db = Database(self.DB_FILE)
        self.db.migrate_from_legacy(get_data_dir())

        self.bus   = EventBus()
        self.model = LineupModel(self.bus)
        self._discord_service = DiscordService()
        self._oauth = DiscordOAuth()
        self._local_mode = True

        self.load_settings()

        saved_oauth = getattr(self, "discord_oauth", {})
        if saved_oauth.get("access_token"):
            self._oauth.restore(saved_oauth)
            if self._oauth.is_signed_in:
                self._local_mode = False

        _icon = get_icon_path() or ""
        dpg.create_viewport(
            title="Lineup Builder",
            width=1000,
            height=900,
            min_width=800,
            min_height=700,
            small_icon=_icon,
            large_icon=_icon,
        )
        self.apply_theme()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self._init_main_app()

    def _init_main_app(self):
        now = datetime.datetime.now()
        self.event_title_var  = DPGVar(default="")
        self.event_vol_var   = DPGVar(default="")
        self.group_name_var  = DPGVar(default="")
        self.collab_var      = DPGBoolVar(default=False)
        self.collab_with_var = DPGVar(default="")
        self.event_timestamp = DPGVar(default=now.strftime("%Y-%m-%d") + " 20:00")
        self.active_genres   =[]
        self.names_only      = DPGBoolVar(default=False)
        self.output_format   = DPGVar(default="discord")
        self.stream_link_format = DPGVar(default="")
        self.genre_entry_var  = DPGVar(default="")
        self.genre_search_var = DPGVar(default="")
        self.dj_search_var   = DPGVar(default="")
        self.slots           =[]
        self.social_links: dict[str, str] = {}

        self._init_debounce()
        self._current_event_key = None
        self._is_dirty = False
        self._init_keyboard_handler()

        self.load_data()
        self.setup_ui()
        self._restore_window_state()

        auto_save_data = self.db.kv_get("auto_save")
        if auto_save_data:
            self._prompt_auto_save_recovery(auto_save_data)
        else:
            self.add_initial_slots()
            self.update_output()
        
        dpg.set_frame_callback(3, lambda: self._schedule_genre_refresh())
        dpg.set_frame_callback(5, lambda: self._update_auth_card())

    def run(self):
        while dpg.is_dearpygui_running():
            self.process_queue()
            if hasattr(self, "check_scheduled_posts"):
                self.check_scheduled_posts()
            self._update_window_title()
            tick_toasts()
            dpg.render_dearpygui_frame()
        self._on_close()
        dpg.destroy_context()
    
    def _update_window_title(self):
        base_title = "Lineup Builder"
        if self._is_dirty:
            dpg.set_viewport_title(f"{base_title}[*]")
        else:
            dpg.set_viewport_title(base_title)

    def _save_window_state(self):
        try:
            state = {
                "pos":          list(dpg.get_viewport_pos()),
                "width":        dpg.get_viewport_width(),
                "height":       dpg.get_viewport_height(),
                "slots_height": dpg.get_item_height("slots_scroll") if dpg.does_item_exist("slots_scroll") else 320,
                "tabs_height":  dpg.get_item_height("right_tabs_content") if dpg.does_item_exist("right_tabs_content") else 360,
            }
            self.db.kv_set("window_state", state)
        except Exception as e:
            log.error(f"_save_window_state error: {e}")

    def _restore_window_state(self):
        try:
            state = self.db.kv_get("window_state")
            if not state: return
            if "pos" in state: dpg.set_viewport_pos(state["pos"])
            if "width" in state: dpg.set_viewport_width(state["width"])
            if "height" in state: dpg.set_viewport_height(state["height"])
            if "slots_height" in state and dpg.does_item_exist("slots_scroll"):
                dpg.configure_item("slots_scroll", height=int(state["slots_height"]))
            if "tabs_height" in state and dpg.does_item_exist("right_tabs_content"):
                self._base_tabs_height = int(state["tabs_height"])
                dpg.configure_item("right_tabs_content", height=self._base_tabs_height)
                self._base_vp_height = dpg.get_viewport_height()
        except Exception as e:
            log.error(f"_restore_window_state error: {e}")

    def _on_close(self):
        self._save_window_state()
        if getattr(self, "_is_dirty", False) and hasattr(self, "_save_current_state_to_auto_save"):
            self._save_current_state_to_auto_save()
        if getattr(self, "_save_lib_job", None):
            self._cancel("_save_lib_job")
            self._save_library()
        self.db.close()