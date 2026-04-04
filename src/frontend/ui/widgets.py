from contextlib import contextmanager

import dearpygui.dearpygui as dpg

from ..styling import theme as T
from ..styling.fonts import bind_icon_font


def popup_pos(trigger_tag: str | int | None = None, width: int = 300, height: int = 200):
    """Return (x, y) near *trigger_tag* (below-right of its rect), clamped to viewport.

    Falls back to the current mouse position when *trigger_tag* is None or
    the item doesn't exist yet.
    """
    vp_w = dpg.get_viewport_width()
    vp_h = dpg.get_viewport_height()

    if trigger_tag and dpg.does_item_exist(trigger_tag):
        try:
            mn = dpg.get_item_rect_min(trigger_tag)
            mx = dpg.get_item_rect_max(trigger_tag)
            x = int(mn[0])
            y = int(mx[1]) + 4  # just below the trigger
        except Exception:
            x, y = dpg.get_mouse_pos(local=False)
    else:
        x, y = dpg.get_mouse_pos(local=False)

    # Clamp so the popup stays inside the viewport
    x = max(0, min(x, vp_w - width))
    y = max(0, min(y, vp_h - height))
    return[x, y]


def add_icon_button(icon: str, is_danger: bool = False, is_primary: bool = False, **kwargs) -> int:
    """Create a standardized icon button, automatically binding the icon font and applying the proper theme."""
    if "width" not in kwargs and "width=-1" not in str(kwargs):
        kwargs["width"] = T.ICON_BTN_W

    btn = dpg.add_button(label=icon, **kwargs)
    bind_icon_font(btn)
    
    if is_danger:
        dpg.bind_item_theme(btn, "danger_btn_theme")
    elif is_primary:
        dpg.bind_item_theme(btn, "primary_btn_theme")
        
    return btn

def add_primary_button(label: str, **kwargs) -> int:
    """Create a standard primary button with the primary theme applied."""
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "primary_btn_theme")
    return btn

def add_success_button(label: str, **kwargs) -> int:
    """Create a standard success button with the success theme applied."""
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "success_btn_theme")
    return btn

def add_danger_button(label: str, **kwargs) -> int:
    """Create a standard danger button with the danger theme applied."""
    btn = dpg.add_button(label=label, **kwargs)
    dpg.bind_item_theme(btn, "danger_btn_theme")
    return btn

def add_styled_combo(**kwargs) -> int:
    """Create a dropdown combo box."""
    return dpg.add_combo(**kwargs)


@contextmanager
def section(app, section_id: str, label: str, default_open: bool = True):
    """Collapsible drawer section. Use as a context manager.

    Creates a single bordered container (table) where the toggle header 
    is the first row and the content is the second row, making them 
    visually connected.
    """
    wrapper_tag = f"sect_{section_id}"
    content_tag = f"sect_c_{section_id}"
    
    collapsed = app._section_collapsed.get(section_id, not default_open)
    icon = "\u25ba" if collapsed else "\u25bc"
    app._section_labels[section_id] = label

    # ── The Drawer Container (Table with outer borders) ──
    # Using a table ensures the border wraps both the header and content.
    dpg.add_table(
        tag=wrapper_tag,
        header_row=False,
        borders_outerH=True,
        borders_outerV=True,
        borders_innerH=False,
        borders_innerV=False,
        pad_outerX=False,  # We handle internal padding manually
        width=-6,         # Pull away from panel edge
    )
    dpg.push_container_stack(dpg.last_item())
    dpg.add_table_column()

    # ── Row 1: The Connected Header ──
    with dpg.table_row():
        # Theme override for the header row to remove cell padding so the button fits edge-to-edge
        with dpg.theme() as header_row_theme:
            with dpg.theme_component(dpg.mvTable):
                dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0)
        dpg.bind_item_theme(dpg.last_item(), header_row_theme)

        btn = dpg.add_button(
            label=f"  {icon}  {label}",
            tag=f"sect_btn_{section_id}",
            callback=lambda: app._toggle_section(section_id),
            width=-1,
            height=28
        )
        dpg.bind_item_theme(btn, "section_btn_theme")

    # ── Row 2: The Content ──
    with dpg.table_row(tag=content_tag, show=not collapsed):
        with dpg.group():
            # Reduced breathing room for tighter vertical density
            dpg.add_spacer(height=1)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=4)
                with dpg.group():
                    try:
                        yield content_tag
                    finally:
                        dpg.add_spacer(height=2)
                dpg.add_spacer(width=4)

    # Pop the table
    dpg.pop_container_stack()
    dpg.add_spacer(height=2) # Tighter space between drawers