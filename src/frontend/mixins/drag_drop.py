"""
Module: drag_drop.py
Purpose: Slot reordering and DJ-to-lineup interaction helpers.
Architecture: Mixin for App class. Drag-and-drop for slot reordering
              and DJ roster → lineup insertion.
"""
import dearpygui.dearpygui as dpg

from ..styling import theme as T

_flash_theme_tag = "_dd_flash_theme"

def _ensure_flash_theme():
    """Flash theme is now managed globally by SettingsMixin.apply_theme()"""
    pass

class DragDropMixin:
    """Helpers for roster-to-lineup drag/drop and slot reordering."""

    def _add_dj_to_lineup(self, dj_name: str, index: int | None = None):
        """Add a DJ from the roster directly into a new lineup slot."""
        self.add_slot(dj_name, "", index=index)

    def _drop_dj_on_lineup(self, sender, app_data):
        """Handle DJ card dropped onto the slots panel — creates a new slot at the end."""
        if app_data and isinstance(app_data, str):
            self._add_dj_to_lineup(app_data)

    def _drop_on_gap(self, sender, app_data, target_index: int):
        """
        Handle a drop onto a specific insertion gap between slots.
        """
        if not app_data:
            return

        # Slot reorder
        if isinstance(app_data, (tuple, list)) and len(app_data) == 2 and app_data[0] == "slot_reorder":
            dragged_id = app_data[1]
            self._reorder_slot_to_index(dragged_id, target_index)
            return

        # DJ card drop — insert at gap index
        if isinstance(app_data, str):
            self._add_dj_to_lineup(app_data, index=target_index)
            # Flash the slot at the index we just inserted into
            if target_index < len(self.slots):
                self._flash_slot(self.slots[target_index])
            return

    def _reorder_slot_to_index(self, dragged_slot_id: int, target_index: int):
        """Move the dragged slot to the target index."""
        drag_idx = next((i for i, s in enumerate(self.slots) if s._id == dragged_slot_id), None)
        
        if drag_idx is None:
            return
            
        slot = self.slots.pop(drag_idx)
        
        # If we are moving it forward, the target index shifts down by 1 because we popped the item
        if drag_idx < target_index:
            target_index -= 1
            
        self.slots.insert(target_index, slot)
        self.refresh_slots()
        self.update_output()
        # Flash the moved slot
        self._flash_slot(slot)

    def _flash_slot(self, slot):
        """Briefly highlight a slot row with the accent theme, then revert."""
        tag = slot.row_tag
        if not tag or not dpg.does_item_exist(tag):
            return
        dpg.bind_item_theme(tag, _flash_theme_tag)
        # Remove the highlight after 400 ms
        self._timer("_flash_job", 0.4, lambda: self._clear_flash(tag))

    @staticmethod
    def _clear_flash(tag: str):
        if dpg.does_item_exist(tag):
            dpg.bind_item_theme(tag, 0)

    def _refresh_slot_combos(self):
        """Update suggestion list items on all existing slot rows after roster changes."""
        import dearpygui.dearpygui as dpg
        names = self.get_dj_names()
        for slot in self.slots:
            tag = f"slot_name_{slot._id}"
            if dpg.does_item_exist(tag):
                pass # Suggestion list logic is dynamic in slot_ui.py