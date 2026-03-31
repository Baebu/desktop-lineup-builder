import json
import logging
import os

import dearpygui.dearpygui as dpg

from ..styling import theme as T
from ..styling.fonts import ERROR, HEADER, LABEL, MUTED, SUCCESS, Icon, styled_text
from ..styling.theme import DEFAULT_SETTINGS, BUILTIN_PRESETS
from ..utils import get_data_dir
from ..ui.widgets import add_icon_button

log = logging.getLogger("settings")


def _load_dotenv() -> dict[str, str]:
    """Read key=value pairs from .env in the data directory (no third-party dep)."""
    env: dict[str, str] = {}
    env_path = os.path.join(get_data_dir(), ".env")
    if not os.path.isfile(env_path):
        return env
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    except Exception:
        pass
    return env


class SettingsMixin:
    """Manages application settings: persistence, theme application, and Settings UI tab."""

    # ── Init & persistence ────────────────────────────────────────────────

    def load_settings(self):
        """Load settings from SQLite DB, falling back to defaults. Must be called before setup_ui."""
        self.settings = dict(DEFAULT_SETTINGS)
        self.user_presets: list =[]
        self.sync_data_dir: str = ""
        self.persistent_links: dict = {
            "DISCORD":   {"link": "", "enabled": False},
            "VRC GROUP": {"link": "", "enabled": False},
        }
        self.dj_profile: dict = {
            "name": "",
            "links": {},
            "logo": "",
            "availability":[],
        }
        self.discord_channels: dict = {
            "events": "",
            "popup": "",
            "signups": "",
        }
        self.discord_bot_token: str = ""
        self.discord_client_id: str = ""
        self.discord_embed_image: str = ""
        self.discord_ping_server: str = ""
        self.discord_ping_roles: str = ""
        self.discord_channel_id: str = ""
        self.discord_oauth: dict = {}
        self.discord_scheduled_posts: list =[]

        # Section layout state (collapsible drawers)
        self._section_collapsed: dict[str, bool] = {}
        self._section_labels: dict[str, str] = {}

        # Load .env defaults
        env = _load_dotenv()
        if env.get("DISCORD_BOT_TOKEN"):
            self.discord_bot_token = env["DISCORD_BOT_TOKEN"]
        if env.get("DISCORD_CLIENT_ID"):
            self.discord_client_id = env["DISCORD_CLIENT_ID"]

        data = self.db.kv_get("settings")
        if data:
            try:
                self.settings.update(
                    {k: v for k, v in data.items() if k in DEFAULT_SETTINGS}
                )
                self.user_presets = data.get("user_presets",[])
                self.sync_data_dir = data.get("sync_data_dir", "")
                
                for key in self.persistent_links:
                    saved = data.get("persistent_links", {}).get(key)
                    if isinstance(saved, dict):
                        self.persistent_links[key] = saved
                    elif isinstance(saved, str):
                        # Handle legacy settings where links were stored as plain strings
                        self.persistent_links[key] = {"link": saved, "enabled": True}
                        
                saved_profile = data.get("dj_profile", {})
                if isinstance(saved_profile, dict):
                    self.dj_profile.update(saved_profile)
                saved_channels = data.get("discord_channels", {})
                if isinstance(saved_channels, dict):
                    self.discord_channels.update(saved_channels)
                self.discord_bot_token = data.get("discord_bot_token", "")
                self.discord_client_id = data.get("discord_client_id", "")
                self.discord_ping_server = data.get("discord_ping_server", "")
                self.discord_ping_roles = data.get("discord_ping_roles", "")
                self.discord_channel_id = data.get("discord_channel_id", "")
                self.discord_oauth = data.get("discord_oauth", {})
                self.discord_scheduled_posts = data.get("discord_scheduled_posts",[])
                
                # Section layout persistence
                saved_collapsed = data.get("section_collapsed", {})
                if isinstance(saved_collapsed, dict):
                    self._section_collapsed.update(saved_collapsed)
            except Exception:
                pass

        # Tracks the last-applied color for each key
        self._applied_settings: dict = dict(self.settings)
        self._danger_btn_theme = None

    def save_settings(self):
        # ── SQLite DB (everything, including secrets) ────────────────────
        try:
            data = {
                **self.settings,
                "user_presets": self.user_presets,
                "sync_data_dir": getattr(self, "sync_data_dir", ""),
                "persistent_links": getattr(self, "persistent_links", {}),
                "dj_profile": getattr(self, "dj_profile", {}),
                "discord_channels": getattr(self, "discord_channels", {}),
                "discord_bot_token": getattr(self, "discord_bot_token", ""),
                "discord_client_id": getattr(self, "discord_client_id", ""),
                "discord_ping_server": getattr(self, "discord_ping_server", ""),
                "discord_ping_roles": getattr(self, "discord_ping_roles", ""),
                "discord_channel_id": getattr(self, "discord_channel_id", ""),
                "discord_oauth": getattr(self, "discord_oauth", {}),
                "discord_scheduled_posts": getattr(self, "discord_scheduled_posts",[]),
                "section_collapsed": getattr(self, "_section_collapsed", {})
            }
            self.db.kv_set("settings", data)
        except Exception as e:
            log.error(f"Error saving settings: {e}")

    # ── Theme application ─────────────────────────────────────────────────

    def apply_theme(self):
        """Build and bind a global DPG theme from current settings."""
        def _c(hex_val, alpha=255):
            h = hex_val.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return (r, g, b, alpha)

        s = self.settings
        
        # 1. Build/Update Global App Theme
        if not dpg.does_item_exist("global_app_theme"):
            dpg.add_theme(tag="global_app_theme")
        else:
            dpg.delete_item("global_app_theme", children_only=True)

        with dpg.theme_component(dpg.mvAll, parent="global_app_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,           _c(s.get("panel_bg",             "#1E293B")))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg,             _c(s.get("panel_bg",            "#1E293B")))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,             _c(s.get("card_bg",             "#0F172A")))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,      _c(s.get("hover_color",         "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,       _c(s.get("primary_color",       "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_Button,              _c(s.get("secondary_color",     "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,       _c(s.get("secondary_hover",     "#475569")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,        _c(s.get("secondary_color",     "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_Text,                _c(s.get("text_primary",        "#CBD5E1")))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled,        _c(s.get("text_secondary",      "#94A3B8")))
            
            # Borders
            dpg.add_theme_color(dpg.mvThemeCol_Border,              _c(s.get("border_color",        "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong,   _c(s.get("border_color",        "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight,    _c(s.get("border_color",        "#334155")))
            
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,         (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab,       _c(s.get("scrollbar_color",     "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered,_c(s.get("hover_color",         "#475569")))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, _c(s.get("primary_color",       "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_Header,              _c(s.get("primary_color",       "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,       _c(s.get("primary_hover_color", "#4338CA")))
            dpg.add_theme_color(dpg.mvThemeCol_Tab,                 _c(s.get("panel_bg",            "#1E293B")))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered,          _c(s.get("primary_hover_color", "#4338CA")))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive,           _c(s.get("primary_color",       "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg,             _c(s.get("panel_bg",            "#1E293B")))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive,       _c(s.get("primary_color",       "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg,             _c(s.get("card_bg",             "#0F172A"), 240))
            dpg.add_theme_color(dpg.mvThemeCol_Separator,           _c(s.get("border_color",        "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark,           _c(s.get("accent_color",        "#818CF8")))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,          _c(s.get("primary_color",       "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive,    _c(s.get("primary_hover_color", "#4338CA")))
            dpg.add_theme_color(dpg.mvThemeCol_DragDropTarget,      _c(s.get("accent_color",        "#818CF8"), 150))
            
            # Rounding
            S = T.Style
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,    S.FRAME_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding,     S.CHILD_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,    S.WINDOW_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding,     S.POPUP_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, S.SCROLLBAR_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding,      S.GRAB_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding,       S.TAB_ROUNDING)
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign,   S.BTN_ALIGN_X, S.BTN_ALIGN_Y)
            
            # Sizing
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding,     S.FRAME_PAD_X, S.FRAME_PAD_Y)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,      S.ITEM_SPACING_X, S.ITEM_SPACING_Y)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, S.INNER_SPACING_X, S.INNER_SPACING_Y)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize,    S.SCROLLBAR_SIZE)
            dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize,      S.GRAB_MIN_SIZE)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding,    S.WINDOW_PAD_X, S.WINDOW_PAD_Y)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, S.WINDOW_BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize,  S.CHILD_BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize,  S.FRAME_BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding,      S.CELL_PAD_X, S.CELL_PAD_Y)
                
        dpg.bind_theme("global_app_theme")

        # 2. Build/Update Explicit Themes in-place (preserves widget bindings)
        _explicit_themes =[
            "primary_btn_theme", "secondary_btn_theme", "success_btn_theme", "danger_btn_theme",
            "resize_handle_theme", "local_toggle_active_theme", "section_btn_theme",
            "text_header_theme", "text_label_theme", "text_muted_theme", 
            "text_error_theme", "text_success_theme", "text_hint_theme",
            "panel_divider_theme", "_dd_flash_theme", "cal_muted_theme"
        ]

        for t in _explicit_themes:
            if not dpg.does_item_exist(t):
                dpg.add_theme(tag=t)
            else:
                dpg.delete_item(t, children_only=True)

        with dpg.theme_component(dpg.mvButton, parent="primary_btn_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("primary_color", "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("primary_hover", "#4338CA")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("primary_color", "#4F46E5")))

        with dpg.theme_component(dpg.mvButton, parent="secondary_btn_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("secondary_color", "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("secondary_hover", "#475569")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("secondary_color", "#334155")))

        with dpg.theme_component(dpg.mvButton, parent="success_btn_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("success_color", "#059669")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("success_hover", "#047857")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("success_color", "#059669")))
            dpg.add_theme_color(dpg.mvThemeCol_Text,          (10, 10, 10, 255))

        with dpg.theme_component(dpg.mvButton, parent="danger_btn_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("danger_color", "#DC2626")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("danger_hover", "#B91C1C")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("danger_color", "#DC2626")))
            dpg.add_theme_color(dpg.mvThemeCol_Text,          (10, 10, 10, 255))

        with dpg.theme_component(dpg.mvButton, parent="resize_handle_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("border_color", "#334155")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("accent_color", "#818CF8")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("accent_color", "#818CF8")))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding,  0, 0)

        with dpg.theme_component(dpg.mvButton, parent="local_toggle_active_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("accent_color", "#818CF8")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("primary_color", "#4F46E5")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("accent_color", "#818CF8")))

        with dpg.theme_component(dpg.mvButton, parent="section_btn_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        _c(s.get("panel_bg", "#1E293B")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _c(s.get("hover_color", "#475569")))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  _c(s.get("hover_color", "#475569")))
            dpg.add_theme_color(dpg.mvThemeCol_Text,          _c(s.get("accent_color", "#818CF8")))
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.0, 0.5)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, T.PANEL_RADIUS)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)

        with dpg.theme_component(dpg.mvText, parent="text_header_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("accent_color", "#818CF8")))

        with dpg.theme_component(dpg.mvText, parent="text_label_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("text_secondary", "#94A3B8")))

        with dpg.theme_component(dpg.mvText, parent="text_muted_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("text_secondary", "#94A3B8"), 180))

        with dpg.theme_component(dpg.mvText, parent="text_error_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("danger_color", "#DC2626")))

        with dpg.theme_component(dpg.mvText, parent="text_success_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("success_color", "#059669")))

        with dpg.theme_component(dpg.mvText, parent="text_hint_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("text_secondary", "#94A3B8"), 120))

        with dpg.theme_component(dpg.mvChildWindow, parent="panel_divider_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, _c(s.get("border_color", "#334155")))

        with dpg.theme_component(dpg.mvAll, parent="_dd_flash_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("accent_color", "#818CF8")))

        with dpg.theme_component(dpg.mvButton, parent="cal_muted_theme"):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 255, 255, 20))
            dpg.add_theme_color(dpg.mvThemeCol_Text, _c(s.get("text_secondary", "#94A3B8"), 150))

        self._danger_btn_theme = "danger_btn_theme"
        
        # Reschedule output update so format buttons get their themes rebound
        if dpg.does_item_exist("fmt_discord"):
            if hasattr(self, "_schedule_update"):
                self._schedule_update()

        self._applied_settings = dict(self.settings)
        dpg.set_global_font_scale(1.0)
        self._set_titlebar_color(
            bg=s.get("card_bg",       "#0F172A"),
            text=s.get("text_primary", "#CBD5E1"),
            border=s.get("primary_color", "#4F46E5"),
        )

    def _set_titlebar_color(self, bg: str, text: str, border: str):
        """Set the Windows title bar background, text, and border color via DWM API (Windows 11+)."""
        import sys
        if sys.platform != "win32":
            return
        import ctypes

        def _colorref(hex_val):
            h = hex_val.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return ctypes.c_ulong(b | (g << 8) | (r << 16))  # DWM expects BGR

        DWMWA_BORDER_COLOR  = 34
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR    = 36
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Lineup Builder")
            if hwnd:
                for attr, val in[
                    (DWMWA_BORDER_COLOR,  _colorref(border)),
                    (DWMWA_CAPTION_COLOR, _colorref(bg)),
                    (DWMWA_TEXT_COLOR,    _colorref(text)),
                ]:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
                    )
        except Exception:
            pass

    # ── Preset helpers ────────────────────────────────────────────────────

    def apply_preset(self, preset_settings: dict):
        """Load a preset's color/font values and rebuild the settings tab."""
        self._applied_settings = dict(self.settings)
        self.settings.update(
            {k: v for k, v in preset_settings.items() if k in DEFAULT_SETTINGS}
        )
        self.save_settings()
        self.apply_theme()
        self._build_settings_tab()

    def save_current_as_preset(self, name: str):
        name = name.strip()
        if not name:
            return
        # Overwrite if same name exists
        self.user_presets =[p for p in self.user_presets if p["name"] != name]
        self.user_presets.append({"name": name, "settings": dict(self.settings)})
        self.save_settings()

    def delete_preset(self, name: str):
        self.user_presets =[p for p in self.user_presets if p["name"] != name]
        self.save_settings()

    # ── Settings tab builder ──────────────────────────────────────────────

    def _build_settings_tab(self):
        container = "settings_scroll"
        if not dpg.does_item_exist(container):
            return
        dpg.delete_item(container, children_only=True)

        # ── Theme Selection ───────────────────────────────────────────────
        styled_text("   THEME SELECTION", HEADER, parent=container)
        preset_names =[p["name"] for p in BUILTIN_PRESETS]
        current_selection = preset_names[0]
        for p in BUILTIN_PRESETS:
            if p["settings"].get("panel_bg") == self.settings.get("panel_bg"):
                current_selection = p["name"]
                break

        def _on_theme_change(s, a):
            choice = dpg.get_value(s)
            preset = next((p for p in BUILTIN_PRESETS if p["name"] == choice), None)
            if not preset:
                return
            self.apply_preset(preset["settings"])

        _theme_combo = dpg.add_combo(items=preset_names, default_value=current_selection,
                      parent=container, width=-1, callback=_on_theme_change)
        with dpg.theme() as _center_theme:
            with dpg.theme_component(dpg.mvCombo):
                dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5)
        dpg.bind_item_theme(_theme_combo, _center_theme)
        dpg.add_separator(parent=container)

        # ── Output Formatting ─────────────────────────────────────────────
        styled_text("   OUTPUT FORMATTING", HEADER, parent=container)
        def _on_divider_change(s, a, u):
            self.settings[u] = a
            self.save_settings()
            if hasattr(self, "_schedule_update"):
                self._schedule_update()

        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                       borders_outerH=False, borders_outerV=False, pad_outerX=False, parent=container):
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_fixed=True)
            
            with dpg.table_row():
                styled_text("   Time/DJ Divider", LABEL)
                dpg.add_input_text(
                    default_value=self.settings.get("time_dj_divider", " | "),
                    width=60,
                    user_data="time_dj_divider",
                    callback=_on_divider_change
                )
                styled_text("   Genre Divider", LABEL)
                dpg.add_input_text(
                    default_value=self.settings.get("genre_divider", " // "),
                    width=60,
                    user_data="genre_divider",
                    callback=_on_divider_change
                )
                
            with dpg.table_row():
                styled_text("   Volume Prefix", LABEL)
                dpg.add_input_text(
                    default_value=self.settings.get("vol_prefix", " VOL."),
                    width=60,
                    user_data="vol_prefix",
                    callback=_on_divider_change
                )
        dpg.add_separator(parent=container)

        dpg.add_button(
            label="Reset to Defaults", parent=container, width=-1,
            callback=lambda: self._reset_to_defaults(),
        )

    def _reset_to_defaults(self):
        self._applied_settings = dict(self.settings)
        self.settings = dict(DEFAULT_SETTINGS)
        self.save_settings()
        self.apply_theme()
        self._build_settings_tab()