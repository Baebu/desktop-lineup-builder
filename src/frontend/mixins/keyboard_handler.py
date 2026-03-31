"""
Module: keyboard_handler.py
Purpose: Keyboard shortcuts (Ctrl+S, Ctrl+Z/Y, Ctrl+N, Delete, etc.)
"""
import dearpygui.dearpygui as dpg
from ..ui.toast import show_toast


class KeyboardMixin:
    """Manages keyboard shortcuts and global key events."""

    def _init_keyboard_handler(self):
        """Initialize keyboard event handlers."""
        with dpg.handler_registry(tag="keyboard_handler_registry"):
            dpg.add_key_press_handler(callback=self._on_key_press)

    def _on_key_press(self, sender, key_code):
        """Handle global keyboard shortcuts."""
        # Check for suggestion list navigation first
        if self._handle_suggestion_navigation(key_code):
            return

        # Ctrl+S — Save event
        ctrl = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
        shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
        if key_code == dpg.mvKey_S and ctrl:
            self._manual_save_event()
            return

        # Ctrl+Z — Undo (placeholder for future undo/redo)
        if key_code == dpg.mvKey_Z and ctrl and not shift:
            show_toast("Undo not yet implemented", severity="info", duration=2.0)
            return

        # Ctrl+Shift+Z — Redo
        if key_code == dpg.mvKey_Z and ctrl and shift:
            show_toast("Redo not yet implemented", severity="info", duration=2.0)
            return

        # Ctrl+N — New event
        if key_code == dpg.mvKey_N and ctrl:
            self.new_event()
            return

    def _handle_suggestion_navigation(self, key_code):
        """Handle Up/Down/Enter/Escape for suggestion lists. Returns True if handled."""
        # Find any visible suggestion list
        for slot in self.slots:
            sid = slot._id
            suggest_grp = f"slot_suggest_{sid}"
            suggest_list = f"slot_suggest_list_{sid}"
            name_tag = f"slot_name_{sid}"
            
            if dpg.does_item_exist(suggest_grp) and dpg.is_item_visible(suggest_grp):
                if key_code == dpg.mvKey_Up:
                    self._navigate_suggestion(slot, suggest_list, -1)
                    return True
                elif key_code == dpg.mvKey_Down:
                    self._navigate_suggestion(slot, suggest_list, 1)
                    return True
                elif key_code in (dpg.mvKey_Return, dpg.mvKey_NumPadEnter):  # Enter keys
                    self._select_dj_suggestion(slot)
                    dpg.focus_item(name_tag)
                    return True
                elif key_code == dpg.mvKey_Escape:
                    dpg.hide_item(suggest_grp)
                    dpg.focus_item(name_tag)
                    return True
        
        return False

    def _navigate_suggestion(self, slot, list_tag: str, direction: int):
        """Navigate the suggestion list with arrow keys."""
        if not dpg.does_item_exist(list_tag):
            return
        # Get items from listbox configuration
        items = dpg.get_value(list_tag)  # This returns the list of items for listbox
        config = dpg.get_item_configuration(list_tag)
        if "items" in config:
            items = config["items"]
        if not items:
            return
        # Get current selection
        current = dpg.get_value(list_tag)
        try:
            idx = items.index(current) if current in items else -1
        except (ValueError, KeyError):
            idx = -1
        new_idx = (idx + direction) % len(items)
        dpg.set_value(list_tag, items[new_idx])

    def _select_dj_suggestion(self, slot):
        """Select the current suggestion and apply it to the slot."""
        sid = slot._id
        suggest_list = f"slot_suggest_list_{sid}"
        name_tag = f"slot_name_{sid}"
        selected = dpg.get_value(suggest_list)
        if not selected:
            return
        dpg.set_value(name_tag, selected)
        slot.name_var.set(selected)
        dpg.hide_item(f"slot_suggest_{sid}")
        self._schedule_update()
        # Update slot info
        from ..ui.slot_ui import _update_slot_info
        _update_slot_info(slot, self)

    def _manual_save_event(self):
        """Manually save the current event."""
        title = self.event_title_var.get().strip()
        if not title:
            show_toast("Please set an Event Title before saving", severity="warning", duration=3.0)
            return
        
        # Trigger the existing save_event_lineup method
        self.save_event_lineup()
