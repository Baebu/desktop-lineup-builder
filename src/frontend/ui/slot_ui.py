"""
Module: slot_ui.py
Purpose: DPG variable wrappers and slot row builder for the lineup editor.
Dependencies: dearpygui, theme
"""

import dearpygui.dearpygui as dpg

from ...backend.output.output_generator import OutputGenerator
from ..styling import theme as T
from ..styling.fonts import styled_text, bind_icon_font, Icon, HEADER, LABEL, MUTED, SUCCESS, ERROR
from .widgets import add_icon_button, add_primary_button
from .toast import show_toast
from ..types import DPGVar, DPGBoolVar, SlotState

# Re-export for backward compatibility
__all__ =["DPGVar", "DPGBoolVar", "SlotState", "build_slot_row", "build_add_slot_row"]


def _on_name_input(slot: SlotState, value: str, app):
    slot.name_var.set(value)
    app._schedule_update()
    _update_slot_info(slot, app)
    # Filter and show suggestions
    sid = slot._id
    suggest_tag = f"slot_suggest_{sid}"
    query = value.strip().lower()
    if query:
        matches =[n for n in app.get_dj_names() if query in n.lower()]
    else:
        matches =[]
    if matches and dpg.does_item_exist(suggest_tag):
        _show_suggestions(slot, matches)
    elif dpg.does_item_exist(suggest_tag):
        dpg.hide_item(suggest_tag)


def _maybe_add_dj_to_roster(slot: SlotState, app):
    """If the slot's DJ name is not already in the roster, add them silently."""
    name = slot.name_var.get().strip()
    if not name:
        return
    # Check if already in roster (case-insensitive)
    already_exists = any(
        d.get("name", "").lower() == name.lower() for d in app.saved_djs
    )
    if already_exists:
        return
    # Add with empty stream link
    app.saved_djs.append({"name": name, "stream": "", "exact_link": False})
    app._save_library()
    app.refresh_dj_roster_ui()
    app._work_queue.put(app._refresh_slot_combos)
    app._refresh_all_slot_info()


def _show_suggestions(slot: SlotState, items: list):
    sid = slot._id
    suggest_tag = f"slot_suggest_{sid}"
    list_tag = f"slot_suggest_list_{sid}"
    name_tag = f"slot_name_{sid}"
    num = min(5, len(items))
    # Align suggestion list with the name input
    if dpg.does_item_exist(name_tag) and dpg.does_item_exist(suggest_tag):
        name_pos = dpg.get_item_pos(name_tag)
        row_pos = dpg.get_item_pos(slot.row_tag) if slot.row_tag and dpg.does_item_exist(slot.row_tag) else [0, 0]
        # row_pos[0] is the table's X. Cell content starts at row_pos[0] + 6 (CELL_PAD_X).
        # To align the listbox exactly with the input text, we indent by the difference.
        indent = max(0, name_pos[0] - (row_pos[0] + 6))
        dpg.configure_item(suggest_tag, indent=int(indent))
    if dpg.does_item_exist(list_tag):
        w = dpg.get_item_width(name_tag) if dpg.does_item_exist(name_tag) else 175
        dpg.configure_item(list_tag, items=items, num_items=num, width=w)
    if dpg.does_item_exist(suggest_tag):
        dpg.show_item(suggest_tag)


def _navigate_suggestion(slot: SlotState, app, list_tag: str, direction: int):
    """Navigate the suggestion list with arrow keys by updating the selected index."""
    if not dpg.does_item_exist(list_tag):
        return
    items = dpg.get_value(list_tag)
    if not items:
        return
    current = dpg.get_item_configuration(list_tag).get("default_value", "")
    try:
        idx = items.index(current) if current in items else -1
    except (ValueError, KeyError):
        idx = -1
    new_idx = (idx + direction) % len(items)
    dpg.set_value(list_tag, items[new_idx])


def _copy_slot_link(sender, app_data, user_data):
    slot, app, fmt = user_data
    name = slot.name_var.get().strip()
    dj = next((d for d in app.saved_djs if d.get("name") == name), None)
    if not dj or not dj.get("stream", "").strip():
        show_toast("No stream link set for this DJ.", severity="warning")
        return
    link = dj.get("stream").strip()
    if dj.get("exact_link"):
        final_link = link
    else:
        final_link = OutputGenerator.vrcdn_convert(link, fmt)
    dpg.set_clipboard_text(final_link)
    show_toast(f"Copied {fmt.upper()} link!", severity="success")


def _select_dj_suggestion(slot: SlotState, app):
    sid = slot._id
    selected = dpg.get_value(f"slot_suggest_list_{sid}")
    if not selected:
        return
    name_tag = f"slot_name_{sid}"
    dpg.set_value(name_tag, selected)
    slot.name_var.set(selected)
    dpg.hide_item(f"slot_suggest_{sid}")
    app._schedule_update()
    _update_slot_info(slot, app)


def build_add_slot_row(app, parent_tag: str):
    """Render a placeholder row with a '+' button that adds a new slot."""
    with dpg.group(parent=parent_tag):
        if not app.slots:
            dpg.add_spacer(height=20)
            styled_text("  Your lineup is empty.", LABEL)
            styled_text("  Drag a DJ from the roster or", MUTED)
            styled_text("  click below to add a slot.", MUTED)
            dpg.add_spacer(height=10)

        with dpg.group(horizontal=True):
            add_primary_button(
                "+ Add DJ Slot",
                width=-1, height=24,
                callback=lambda: app.add_slot(),
            )



def build_slot_row(slot: SlotState, app, parent_tag: str):
    """Create DPG widgets for *slot* inside *parent_tag*."""
    sid = slot._id
    row_tag = f"slot_row_{sid}"
    slot.row_tag = row_tag

    dur_vals =[str(x) for x in range(15, 121, 15)]
    if slot.duration_var.get() not in dur_vals:
        dur_vals.append(slot.duration_var.get())
        dur_vals.sort(key=int)

    # ── Bordered Card using a 1x1 Table ──
    with dpg.table(tag=row_tag, parent=parent_tag, header_row=False,
                   borders_outerH=True, borders_outerV=True,
                   borders_innerH=False, borders_innerV=False,
                   pad_outerX=True, width=-6):
        dpg.add_table_column()
        with dpg.table_row():
            with dpg.group():
                dpg.add_spacer(height=2)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=4)
                    styled_text(
                        "--:--",
                        HEADER,
                        tag=f"slot_time_{sid}",
                    )
                    dpg.add_combo(
                        items=dur_vals,
                        default_value=slot.duration_var.get(),
                        tag=f"slot_dur_{sid}",
                        width=50,
                        user_data=slot,
                        callback=lambda s, a, u: (
                            u.duration_var.set(a),
                            app._schedule_update(),
                        ),
                    )
                    slot.duration_var._tag = f"slot_dur_{sid}"
                    app._register_scroll_combo(
                        f"slot_dur_{sid}", dur_vals,
                        on_change=lambda u=slot: (u.duration_var.set(
                            dpg.get_value(f"slot_dur_{u._id}")), app._schedule_update()),
                    )
                    dpg.add_input_text(
                        default_value=slot.name_var.get(),
                        tag=f"slot_name_{sid}",
                        hint="DJ name...",
                        width=100,
                        user_data=slot,
                        callback=lambda s, a, u: _on_name_input(u, a, app),
                    )
                    slot.name_var._tag = f"slot_name_{sid}"
                    
                    # Cleanup existing handler before creating a new one
                    hr_tag = f"slot_name_hr_{sid}"
                    if dpg.does_item_exist(hr_tag):
                        dpg.delete_item(hr_tag)
                        
                    with dpg.item_handler_registry(tag=hr_tag):
                        dpg.add_item_deactivated_after_edit_handler(
                            callback=lambda s, a, u=slot: _maybe_add_dj_to_roster(u, app)
                        )
                    dpg.bind_item_handler_registry(f"slot_name_{sid}", hr_tag)
                    
                    dpg.add_input_text(
                        default_value=slot.genre_var.get(),
                        tag=f"slot_genre_{sid}",
                        hint="Genre...",
                        width=90,
                        user_data=slot,
                        callback=lambda s, a, u: (u.genre_var.set(a), app._schedule_update()),
                    )
                    slot.genre_var._tag = f"slot_genre_{sid}"
                    
                    dpg.add_input_text(
                        default_value=slot.club_var.get(),
                        tag=f"slot_club_{sid}",
                        hint="Club...",
                        width=90,
                        user_data=slot,
                        callback=lambda s, a, u: (u.club_var.set(a), app._schedule_update()),
                    )
                    slot.club_var._tag = f"slot_club_{sid}"
                    
                    # Temporarily apply ERROR so it has a color before _update_slot_info applies the theme
                    styled_text("LINK", ERROR, tag=f"slot_info_{sid}")
                    
                    add_icon_button(Icon.VR, width=28, height=24, user_data=(slot, app, "quest"), callback=_copy_slot_link, tag=f"slot_quest_{sid}", show=False)
                    add_icon_button(Icon.COMPUTER, width=28, height=24, user_data=(slot, app, "pc"), callback=_copy_slot_link, tag=f"slot_pc_{sid}", show=False)
                    
                    _del_btn = add_icon_button(
                        Icon.CLOSE, is_danger=True,
                        width=28, height=24,
                        user_data=slot,
                        callback=lambda s, a, u: app.delete_slot(u),
                    )

                # ── Autocomplete suggestions ───────────────────────────────────────
                suggest_grp = f"slot_suggest_{sid}"
                if dpg.does_item_exist(suggest_grp):
                    dpg.delete_item(suggest_grp)
                    
                with dpg.group(tag=suggest_grp, show=False):
                    dpg.add_listbox(
                        tag=f"slot_suggest_list_{sid}",
                        items=[],
                        width=140,
                        num_items=4,
                        user_data=slot,
                        callback=lambda s, a, u: _select_dj_suggestion(u, app),
                    )
                    
                dpg.add_spacer(height=2)

    _update_slot_info(slot, app)


def _on_name_change(slot: SlotState, value: str, app):
    slot.name_var.set(value)
    app._schedule_update()
    _update_slot_info(slot, app)

def _update_slot_info(slot: SlotState, app):
    val = slot.name_var.get().strip()
    sid = slot._id
    dj = next((d for d in app.saved_djs if d.get("name") == val), None)
    has_stream = bool(dj and dj.get("stream"))
    info_tag = f"slot_info_{sid}"
    if dpg.does_item_exist(info_tag):
        dpg.configure_item(info_tag, color=T.DPG_IMPORT_SUCCESS if has_stream else T.DPG_ERROR)
    if dpg.does_item_exist(f"slot_quest_{sid}"):
        dpg.configure_item(f"slot_quest_{sid}", show=has_stream)
    if dpg.does_item_exist(f"slot_pc_{sid}"):
        dpg.configure_item(f"slot_pc_{sid}", show=has_stream)