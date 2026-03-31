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
        # Ctrl+S — Save event
        if key_code == dpg.mvKey_S and dpg.is_key_down(dpg.mvKey_Control):
            self._manual_save_event()
            return

        # Ctrl+Z — Undo (placeholder for future undo/redo)
        if key_code == dpg.mvKey_Z and dpg.is_key_down(dpg.mvKey_Control) and not dpg.is_key_down(dpg.mvKey_Shift):
            show_toast("Undo not yet implemented", severity="info", duration=2.0)
            return

        # Ctrl+Shift+Z — Redo
        if key_code == dpg.mvKey_Z and dpg.is_key_down(dpg.mvKey_Control) and dpg.is_key_down(dpg.mvKey_Shift):
            show_toast("Redo not yet implemented", severity="info", duration=2.0)
            return

        # Ctrl+N — New event
        if key_code == dpg.mvKey_N and dpg.is_key_down(dpg.mvKey_Control):
            self.new_event()
            return

    def _manual_save_event(self):
        """Manually save the current event."""
        title = self.event_title_var.get().strip()
        if not title:
            show_toast("Please set an Event Title before saving", severity="warning", duration=3.0)
            return
        
        # Trigger the existing save_event_lineup method
        self.save_event_lineup()
