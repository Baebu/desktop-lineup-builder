import os
import logging
import dearpygui.dearpygui as dpg

from ..styling.fonts import styled_text, HEADER, LABEL, MUTED, ERROR, HINT, Icon
from .widgets import add_primary_button, add_icon_button, section, add_success_button
from .date_time_picker import add_datetime_row

log = logging.getLogger("tabs")

class TabsBuilderMixin:
    """Mixin providing specific tab content builders for the Event and Roster tabs."""

    _VRC_FIELDS =[
        ("TIMELINE",   "https://vrc.tl/event/"),
        ("VRCPOP",     "https://vrcpop.com/event/"),
    ]

    _SOCIAL_FIELDS =[
        ("X",          "https://x.com/"),
        ("IG",         "https://www.instagram.com/p/"),
    ]

    _CLUB_FIELDS =[
        ("DISCORD",    "https://discord.gg/"),
        ("VRC GROUP",  "https://vrc.group/"),
    ]

    def _build_event_tab(self):
        with dpg.child_window(tag="event_tab_inner", border=False,
                              autosize_x=True, height=-1):
            self._build_event_header()

            self._build_details_section()
            self._build_genres_section()
            self._build_links_section()
            self._build_image_section()
            self._build_discord_section()
        
        self.refresh_genre_tags()

    def _build_event_header(self):
        with dpg.table(header_row=False, borders_innerH=False,
                       borders_innerV=False, borders_outerH=False,
                       borders_outerV=False, pad_outerX=False):
            dpg.add_table_column(width_stretch=True)
            dpg.add_table_column(width_stretch=True)
            with dpg.table_row():
                dpg.add_button(label="+ New", width=-1,
                               callback=lambda: self.new_event())
                add_success_button("Save", tag="save_event_btn", width=-1,
                                   callback=lambda: self.save_event_lineup())

    def _build_saved_events_section(self):
        """Build the saved events button and drawer wrapped in a bordered container (matching section style)."""
        with dpg.table(
            header_row=False,
            borders_outerH=True,
            borders_outerV=True,
            borders_innerH=False,
            borders_innerV=False,
            pad_outerX=False,
            width=-6,
        ):
            dpg.add_table_column()
            # Row 1: The button (always visible)
            with dpg.table_row():
                with dpg.theme() as header_row_theme:
                    with dpg.theme_component(dpg.mvTable):
                        dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0)
                dpg.bind_item_theme(dpg.last_item(), header_row_theme)

                collapsed = self._section_collapsed.get("saved_events", False)
                icon = "\u25ba" if collapsed else "\u25bc"
                saved_events_btn = dpg.add_button(
                    label=f"  {icon}  SAVED EVENTS",
                    tag="saved_events_btn",
                    width=-1,
                    height=28,
                    callback=lambda: self._toggle_saved_events_drawer()
                )
                dpg.bind_item_theme(saved_events_btn, "section_btn_theme")

            # Row 2: The drawer content (toggled)
            with dpg.table_row(tag="saved_events_drawer_row", show=False):
                with dpg.child_window(
                    tag="saved_events_drawer",
                    height=200,
                    border=False,
                    show=False,
                ):
                    with dpg.child_window(
                        tag="saved_events_drawer_content",
                        height=-1,
                        border=False,
                        autosize_x=True,
                    ):
                        pass
        dpg.add_spacer(height=4)

    def _build_details_section(self):
        # Saved Events section (above the DETAILS section)
        self._build_saved_events_section()
        
        with section(self, "evt_config", "DETAILS"):
            with dpg.group():
                styled_text("TITLE", LABEL)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(
                        tag="event_title_input",
                        default_value=self.event_title_var.get(),
                        hint="Event title...", width=-56,
                        callback=lambda s, a, u=None: self._schedule_update(),
                    )
                    dpg.add_input_text(
                        tag="event_vol_input",
                        default_value=self.event_vol_var.get(),
                        hint="Vol",
                        width=44,
                        callback=lambda s, a, u=None: self._schedule_update(),
                    )
                    with dpg.theme() as _pill_theme:
                        with dpg.theme_component(dpg.mvInputText):
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 999)
                    dpg.bind_item_theme("event_vol_input", _pill_theme)
            
            dpg.add_spacer(height=4)

            with dpg.group():
                styled_text("START", LABEL)
                add_datetime_row(
                    "event_timestamp_input", self.event_timestamp,
                    callback=lambda s, a, u=None: self._schedule_update(),
                )

            self.event_title_var._tag = "event_title_input"
            self.event_vol_var._tag   = "event_vol_input"
            self._register_scroll_int("event_vol_input", min_val=1,
                                      on_change=lambda: self._schedule_update())

    def _build_genres_section(self):
        with section(self, "evt_genres", "GENRES"):
            dpg.add_input_text(
                tag="genre_entry",
                default_value=self.genre_entry_var.get(),
                hint="Search or press Enter to add...", width=-1,
                on_enter=True,
                callback=lambda s, a, u=None: self.add_genre_from_entry(),
            )
            dpg.add_spacer(height=4)
            add_primary_button("Edit Genres", width=-1, callback=self._toggle_genre_settings_drawer)

            with dpg.child_window(tag="genre_settings_drawer", height=200, border=True, show=False):
                self._build_genre_settings_drawer()
            
            self.genre_entry_var._tag = "genre_entry"
            self.genre_search_var._tag = "genre_entry"
            
            with dpg.item_handler_registry(tag="genre_entry_hr"):
                dpg.add_item_edited_handler(
                    callback=lambda s, a, u=None: self._schedule_genre_refresh()
                )
            dpg.bind_item_handler_registry("genre_entry", "genre_entry_hr")
            
            dpg.add_spacer(height=4)
            with dpg.child_window(tag="genre_tags_frame", height=90, border=False, autosize_x=True):
                pass

    def _build_links_section(self):
        with section(self, "evt_links", "LINKS"):
            # ── VRC Group ──
            styled_text("VRC", MUTED)
            for label, hint in self._VRC_FIELDS:
                tag_key = label.replace(' ', '_')
                dpg.add_input_text(
                    tag=f"social_input_{tag_key}",
                    default_value=self.social_links.get(label, ""),
                    hint=f"{label} ({hint})", width=-1,
                    user_data=label,
                    callback=lambda s, a, u: self._on_social_link_changed(u),
                )
            dpg.add_spacer(height=4)

            # ── Socials Group ──
            styled_text("SOCIALS", MUTED)
            for label, hint in self._SOCIAL_FIELDS:
                tag_key = label.replace(' ', '_')
                dpg.add_input_text(
                    tag=f"social_input_{tag_key}",
                    default_value=self.social_links.get(label, ""),
                    hint=f"{label} ({hint})", width=-1,
                    user_data=label,
                    callback=lambda s, a, u: self._on_social_link_changed(u),
                )
            dpg.add_spacer(height=4)

            # ── Club Group ──
            styled_text("CLUB", MUTED)
            for label, hint in self._CLUB_FIELDS:
                tag_key = label.replace(' ', '_')
                p = self.persistent_links.get(label, {})
                dpg.add_input_text(
                    tag=f"group_link_{tag_key}",
                    default_value=(p.get("link", "") if isinstance(p, dict) else ""),
                    hint=f"{label} ({hint})", width=-1,
                    user_data=label,
                    callback=lambda s, a, u: self._on_club_link_changed(u),
                )

    def _build_image_section(self):
        with section(self, "evt_image", "IMAGE"):
            _img_path = getattr(self, "discord_embed_image", "")
            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False, pad_outerX=False):
                dpg.add_table_column(width_stretch=True)
                dpg.add_table_column(width_fixed=True)
                with dpg.table_row():
                    _img_label = os.path.basename(_img_path) if _img_path else "Select Image..."
                    add_primary_button(_img_label, tag="embed_image_browse_btn", width=-1, callback=self._browse_embed_image)
                    dpg.add_button(label="X", width=35, callback=self._clear_embed_image)

    def _build_discord_section(self):
        with section(self, "evt_discord", "DISCORD"):
            with dpg.group(horizontal=True):
                styled_text("Bot", LABEL)
                styled_text("Not connected", MUTED, tag="discord_status_text")

            with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False, pad_outerX=False):
                dpg.add_table_column(); dpg.add_table_column()
                with dpg.table_row():
                    add_primary_button("Connect", width=-1, callback=self._connect_discord_bot)
                    dpg.add_button(label="Disconnect", width=-1, callback=self._disconnect_discord_bot)

            add_primary_button("Configure", width=-1, callback=self._toggle_discord_settings_drawer)
            with dpg.child_window(tag="discord_settings_drawer", height=220, border=True, show=False):
                self._build_discord_settings_drawer()

            dpg.add_spacer(height=8)
            styled_text("Server", LABEL)
            dpg.add_combo(tag="discord_ping_server", items=[], width=-1, callback=self._on_server_selected)

            dpg.add_spacer(height=8)
            styled_text("Channel", LABEL)
            dpg.add_combo(tag="discord_channel", items=[], width=-1, callback=self._save_discord_channel)
            
            dpg.add_spacer(height=8)
            styled_text("Ping Role", LABEL)
            dpg.add_combo(tag="discord_ping_roles", items=[], width=-1, callback=self._save_discord_ping_roles)

            dpg.add_spacer(height=8)
            add_primary_button("Post to Discord", width=-1, callback=self._confirm_post_to_discord)

    def _build_dj_roster_tab(self):
        """Constructs the sidebar interface for the DJ Roster."""
        add_primary_button("+ New DJ", tag="new_dj_btn", width=-1,
                           callback=lambda: self.add_new_dj_to_roster())
        dpg.add_input_text(
            tag="dj_search_input",
            default_value=self.dj_search_var.get(),
            hint="Search...", width=-11,
            callback=lambda s, a, u=None: self._schedule_roster_refresh(),
        )
        self.dj_search_var._tag = "dj_search_input"

        with dpg.child_window(tag="dj_roster_scroll", height=-1,
                              border=False, autosize_x=True):
            pass  # populated by refresh_dj_roster_ui()

        self.refresh_dj_roster_ui()

    def _on_social_link_changed(self, label: str):
        tag = f"social_input_{label.replace(' ', '_')}"
        if dpg.does_item_exist(tag):
            val = dpg.get_value(tag).strip()
            self.social_links[label] = val
            self._schedule_update()

    def _on_club_link_changed(self, label: str):
        tag = f"group_link_{label.replace(' ', '_')}"
        if dpg.does_item_exist(tag):
            value = dpg.get_value(tag).strip()
            self.persistent_links[label] = {"link": value, "enabled": True}
            self.save_settings()
            self._schedule_update()

    def _sync_social_link_inputs(self):
        for label, _ in self._VRC_FIELDS + self._SOCIAL_FIELDS:
            tag = f"social_input_{label.replace(' ', '_')}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, self.social_links.get(label, ""))
        
        for label, _ in self._CLUB_FIELDS:
            tag = f"group_link_{label.replace(' ', '_')}"
            if dpg.does_item_exist(tag):
                p = self.persistent_links.get(label, {})
                dpg.set_value(tag, p.get("link", "") if isinstance(p, dict) else "")