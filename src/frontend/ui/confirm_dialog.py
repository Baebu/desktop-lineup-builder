"""
Module: confirm_dialog.py
Purpose: Reusable confirmation modal dialog for DearPyGui.
"""

import dearpygui.dearpygui as dpg
from ..styling import theme as T
from ..styling.fonts import styled_text, LABEL
from .widgets import add_primary_button, add_danger_button

_dialog_counter = 0


def confirm(message: str, on_confirm, title: str = "Confirm",
            confirm_label: str = "Confirm", danger: bool = False):
    """Show a modal confirmation dialog.

    Args:
        message:       Text to display in the dialog body.
        on_confirm:    Callable invoked (no args) when user clicks confirm.
        title:         Window title.
        confirm_label: Label for the confirm button.
        danger:        If True, the confirm button uses the danger theme.
    """
    global _dialog_counter
    _dialog_counter += 1
    tag = f"_confirm_dialog_{_dialog_counter}"

    def _on_confirm():
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        on_confirm()

    def _on_cancel():
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)

    # Center in viewport
    vp_w = dpg.get_viewport_width()
    vp_h = dpg.get_viewport_height()
    win_w, win_h = 320, 120
    pos = [(vp_w - win_w) // 2, (vp_h - win_h) // 2]

    with dpg.window(
        tag=tag, label=title, modal=True,
        no_resize=True, no_collapse=True,
        width=win_w, height=win_h,
        pos=pos,
        on_close=_on_cancel,
    ):
        dpg.add_text(message, wrap=win_w - 30)
        dpg.add_spacer(height=8)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=win_w - 200)
            dpg.add_button(label="Cancel", width=80, callback=_on_cancel)
            dpg.add_spacer(width=4)
            if danger:
                btn = add_danger_button(confirm_label, width=80, callback=_on_confirm)
            else:
                btn = add_primary_button(confirm_label, width=80, callback=_on_confirm)
