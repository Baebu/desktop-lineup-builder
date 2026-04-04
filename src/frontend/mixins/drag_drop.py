"""
Module: drag_drop.py
Purpose: DJ-to-lineup drag-and-drop helpers.
Architecture: Mixin for App class. Handles DJ roster → lineup insertion.
"""

class DragDropMixin:
    """Helpers for roster-to-lineup drag/drop."""

    def _add_dj_to_lineup(self, dj_name: str):
        """Add a DJ from the roster directly into a new lineup slot."""
        self.add_slot(dj_name, "")

    def _drop_dj_on_lineup(self, sender, app_data):
        """Handle DJ card dropped onto the slots panel — creates a new slot at the end."""
        if app_data and isinstance(app_data, str):
            self._add_dj_to_lineup(app_data)

    def _refresh_slot_combos(self):
        """Update suggestion list items on all existing slot rows after roster changes."""
        import dearpygui.dearpygui as dpg
        for slot in self.slots:
            tag = f"slot_name_{slot._id}"
            if dpg.does_item_exist(tag):
                pass  # Suggestion list logic is dynamic in slot_ui.py
