"""
Module: sections.py
Purpose: Collapsible section management for left-panel tabs.
Architecture: Mixin for App class.
"""
import dearpygui.dearpygui as dpg

# Default section order per tab (used as fallback when no saved order exists)
SECTION_DEFAULTS = {
    "Event": ["evt_config", "evt_genres", "evt_links"],
    "Club":["club_links", "club_vrchat", "club_sent"],
    "Roster":["roster_local", "roster_booked"],
    "DJ":["dj_links", "dj_logo", "dj_genres", "dj_avail", "dj_bookings"],
}


class SectionsMixin:
    """Manages collapsible UI sections in left-panel tabs."""

    def _toggle_section(self, section_id: str):
        """Toggle a section's collapsed/expanded state."""
        content_tag = f"sect_c_{section_id}"
        btn_tag = f"sect_btn_{section_id}"
        if not dpg.does_item_exist(content_tag):
            return
        currently_shown = dpg.get_item_configuration(content_tag).get("show", True)
        new_show = not currently_shown
        dpg.configure_item(content_tag, show=new_show)
        
        label = self._section_labels.get(section_id, "")
        icon = "\u25bc" if new_show else "\u25ba"
        dpg.configure_item(btn_tag, label=f" {icon}  {label}")
        
        self._section_collapsed[section_id] = not new_show
        
        self.save_settings()

    def _apply_section_order(self):
        """Restore saved collapsed state after UI construction."""
        for section_id, collapsed in self._section_collapsed.items():
            content_tag = f"sect_c_{section_id}"
            btn_tag = f"sect_btn_{section_id}"
            if dpg.does_item_exist(content_tag):
                dpg.configure_item(content_tag, show=not collapsed)
            if dpg.does_item_exist(btn_tag):
                label = self._section_labels.get(section_id, "")
                icon = "\u25ba" if collapsed else "\u25bc"
                dpg.configure_item(btn_tag, label=f" {icon}  {label}")