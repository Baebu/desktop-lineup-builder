"""
Module: toast.py
Purpose: Non-blocking toast notification overlay for DearPyGui.

Creates a small floating bubble at the bottom-right of the viewport that
auto-dismisses after a configurable duration. Supports success, error,
info, and warning severity levels with distinct styling.
"""

import time
import dearpygui.dearpygui as dpg

from ..styling import theme as T

# ── Severity presets ──────────────────────────────────────────────────────────
_SEVERITY = {
    "success": {"bg": (11, 110, 79, 230), "border": (52, 211, 153, 255)},
    "error":   {"bg": (127, 29, 29, 230),  "border": (239, 68, 68, 255)},
    "info":    {"bg": (30, 41, 59, 230),   "border": (129, 140, 248, 255)},
    "warning": {"bg": (120, 83, 9, 230),   "border": (251, 191, 36, 255)},
}

# Track active toasts for stacking
_active_toasts: list[dict] =[]
_toast_counter = 0

_TOAST_WIDTH = 360
_TOAST_HEIGHT = 56
_TOAST_MARGIN_X = 32  # Distance from right edge
_TOAST_MARGIN_Y = 48  # Distance from bottom edge (client area)
_TOAST_GAP = 12       # Distance between stacked toasts


def _get_viewport_dims():
    """Safely get the true client area dimensions."""
    try:
        w = dpg.get_viewport_client_width()
        h = dpg.get_viewport_client_height()
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    return dpg.get_viewport_width(), dpg.get_viewport_height()


def _build_toast_theme(severity: str):
    """Create or return a cached DPG theme for the given severity."""
    tag = f"_toast_theme_{severity}"
    if dpg.does_item_exist(tag):
        return tag
    preset = _SEVERITY.get(severity, _SEVERITY["info"])
    with dpg.theme(tag=tag):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, preset["bg"])
            dpg.add_theme_color(dpg.mvThemeCol_Border, preset["border"])
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 2)  # Thicker border ensures it renders fully
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 28)   # Perfect pill shape for height 56
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 24, 18) # Centered text, prevents clipping
    return tag


def _reposition_toasts():
    """Stack active toasts from bottom-right of viewport."""
    vp_w, vp_h = _get_viewport_dims()
    y_offset = 0
    for toast in reversed(_active_toasts):
        tag = toast["tag"]
        if dpg.does_item_exist(tag):
            x = vp_w - _TOAST_WIDTH - _TOAST_MARGIN_X
            y = vp_h - _TOAST_HEIGHT - _TOAST_MARGIN_Y - y_offset
            dpg.configure_item(tag, pos=[x, y])
            y_offset += _TOAST_HEIGHT + _TOAST_GAP


def _dismiss_toast(tag: str):
    """Remove a toast by tag."""
    global _active_toasts
    _active_toasts = [t for t in _active_toasts if t["tag"] != tag]
    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)
    _reposition_toasts()


def tick_toasts():
    """Call once per frame (from App.process_queue / render loop) to auto-dismiss expired toasts."""
    now = time.time()
    expired = [t for t in _active_toasts if t["duration"] > 0 and now - t["time"] >= t["duration"]]
    for t in expired:
        _dismiss_toast(t["tag"])


def show_toast(message: str, severity: str = "info", duration: float = 3.0):
    """Show a toast notification.

    Args:
        message:  Text to display.
        severity: One of 'success', 'error', 'info', 'warning'.
        duration: Seconds before auto-dismiss (0 = sticky).
    """
    global _toast_counter
    _toast_counter += 1
    tag = f"_toast_win_{_toast_counter}"
    theme_tag = _build_toast_theme(severity)

    # Cap active toasts at 5
    while len(_active_toasts) >= 5:
        oldest = _active_toasts.pop(0)
        if dpg.does_item_exist(oldest["tag"]):
            dpg.delete_item(oldest["tag"])

    vp_w, vp_h = _get_viewport_dims()

    with dpg.window(
        tag=tag,
        label="",
        no_title_bar=True,
        no_resize=True,
        no_move=True,
        no_collapse=True,
        no_scrollbar=True,
        no_focus_on_appearing=True,
        width=_TOAST_WIDTH,
        height=_TOAST_HEIGHT,
        pos=[vp_w - _TOAST_WIDTH - _TOAST_MARGIN_X,
             vp_h - _TOAST_HEIGHT - _TOAST_MARGIN_Y],
    ):
        # Truncate long messages to ensure they fit on one line and don't clip the border
        display = message if len(message) <= 45 else message[:42] + "..."
        dpg.add_text(display)

    dpg.bind_item_theme(tag, theme_tag)

    toast_entry = {"tag": tag, "time": time.time(), "duration": duration}
    _active_toasts.append(toast_entry)
    _reposition_toasts()