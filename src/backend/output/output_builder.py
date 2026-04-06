import dearpygui.dearpygui as dpg

from ..models.types import DJInfo, EventSnapshot, SlotData
from .output_generator import OutputGenerator


class OutputMixin:
    """Bridges the Tkinter UI with the pure-Python OutputGenerator.

    Reads widget state → builds an ``EventSnapshot`` → delegates text
    generation to ``OutputGenerator`` → writes the result back to the
    output textbox.  Copy helpers and format-button state remain here
    because they are inherently UI concerns.
    """

    # ── VRCDN link conversion (thin wrapper kept for backward compat) ─────

    @staticmethod
    def _vrcdn_convert(link: str, fmt: str) -> str:
        """Delegate to ``OutputGenerator.vrcdn_convert``."""
        return OutputGenerator.vrcdn_convert(link, fmt)

    # ── Snapshot builder ──────────────────────────────────────────────────

    def _build_snapshot(self) -> EventSnapshot:
        """Harvest the current UI state into an ``EventSnapshot``."""
        slots =[]
        for s in self.slots:
            try:
                dur = int(s.duration_var.get())
            except (ValueError, AttributeError):
                dur = 0
            slots.append(SlotData(
                name=s.name_var.get().strip(),
                genre=s.genre_var.get().strip(),
                club=s.club_var.get().strip(),
                duration=dur,
            ))

        dj_list =[
            DJInfo(
                name=d.get("name", ""),
                stream=d.get("stream", ""),
                exact_link=bool(d.get("exact_link")),
            )
            for d in self.saved_djs
        ]

        # Read social links directly from widgets for real-time values
        merged_social = {}
        
        # 1. Read VRC and Social fields
        vrc_fields = getattr(self, "_VRC_FIELDS",[])
        social_fields = getattr(self, "_SOCIAL_FIELDS",[])
        for label, _ in vrc_fields + social_fields:
            tag = f"social_input_{label.replace(' ', '_')}"
            if dpg.does_item_exist(tag):
                val = (dpg.get_value(tag) or "").strip()
                if val:
                    merged_social[label] = val
            elif label in getattr(self, "social_links", {}):
                val = self.social_links[label].strip()
                if val:
                    merged_social[label] = val
                    
        # 2. Read persistent links fallback
        for key, val in getattr(self, "persistent_links", {}).items():
            if isinstance(val, dict) and val.get("enabled") and val.get("link", "").strip():
                merged_social[key] = val["link"].strip()
                
        # 3. Read club link widgets directly for real-time values (overrides persistent if present)
        club_fields = getattr(self, "_CLUB_FIELDS",[])
        for label, _ in club_fields:
            tag = f"group_link_{label.replace(' ', '_')}"
            if dpg.does_item_exist(tag):
                val = (dpg.get_value(tag) or "").strip()
                if val:
                    merged_social[label] = val

        collab_with = self.collab_with_var.get().strip()

        return EventSnapshot(
            title=self.event_title_var.get().strip(),
            vol=self.event_vol_var.get().strip(),
            group_name=self.group_name_var.get().strip(),
            collab=bool(collab_with),
            collab_with=collab_with,
            timestamp=self.event_timestamp.get(),
            genres=list(self.active_genres),
            slots=slots,
            names_only=self.names_only.get(),
            output_format=self.output_format.get(),
            stream_link_format=self.stream_link_format.get(),
            time_dj_divider=self.settings.get("time_dj_divider", " | "),
            genre_divider=self.settings.get("genre_divider", " // "),
            vol_prefix=self.settings.get("vol_prefix", " VOL."),
            saved_djs=dj_list,
            social_links=merged_social,
        )

    # ── Main output builder ───────────────────────────────────────────────

    def update_output(self):
        snap = self._build_snapshot()

        # Always refresh slot start-time labels regardless of output format
        slot_times = OutputGenerator.compute_slot_times(snap)
        for _slot, time_str in zip(self.slots, slot_times):
            tag = f"slot_time_{_slot._id}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, time_str)

        # Sync button themes for formats, stream links, and times toggle
        if hasattr(self, "output_format") and hasattr(self, "names_only"):
            fmt = self.output_format.get()
            slf = self.stream_link_format.get()
            if dpg.does_item_exist("fmt_discord"):
                dpg.bind_item_theme("fmt_discord", "success_btn_theme" if fmt == "discord" else "secondary_btn_theme")
            if dpg.does_item_exist("fmt_plain"):
                dpg.bind_item_theme("fmt_plain", "success_btn_theme" if fmt == "local" else "secondary_btn_theme")
            if dpg.does_item_exist("fmt_quest"):
                dpg.bind_item_theme("fmt_quest", "success_btn_theme" if slf == "quest" else "secondary_btn_theme")
            if dpg.does_item_exist("fmt_pc"):
                dpg.bind_item_theme("fmt_pc", "success_btn_theme" if slf == "pc" else "secondary_btn_theme")
                
            if dpg.does_item_exist("fmt_times"):
                times_on = not self.names_only.get()
                dpg.configure_item("fmt_times", label="Times on" if times_on else "Times off")
                dpg.bind_item_theme("fmt_times", "success_btn_theme" if times_on else "secondary_btn_theme")

        # Delegate the heavy lifting to the pure-Python generator
        body = OutputGenerator.generate(snap)

        if dpg.does_item_exist("output_text"):
            dpg.set_value("output_text", body)
            
        if hasattr(self, "_update_visual_preview"):
            self._update_visual_preview()

    # ── Copy helpers ──────────────────────────────────────────────────────

    def copy_template(self):
        import threading
        text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        dpg.set_clipboard_text(text)

    def copy_quest_links(self):
        self.stream_link_format.set("quest")
        self.update_output()
        self._copy_output_to_clipboard()

    def copy_pc_links(self):
        self.stream_link_format.set("pc")
        self.update_output()
        self._copy_output_to_clipboard()

    def _copy_output_to_clipboard(self):
        text = dpg.get_value("output_text") if dpg.does_item_exist("output_text") else ""
        dpg.set_clipboard_text(text)

    # ── Format-button state ───────────────────────────────────────────────

    def toggle_format(self):
        self.output_format.set("discord")
        self.update_output()

    def set_plain_text(self):
        self.output_format.set("local")
        self.update_output()