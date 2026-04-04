"""
Module: date_time_picker.py
Purpose: DPG date/time input helper with a custom Sun-Sat Calendar popout.
         Supports full date+time, date-only, and time-only picker modes.
"""
import calendar
from datetime import datetime, timedelta

import dearpygui.dearpygui as dpg

from .widgets import popup_pos


# ── Full date+time picker ─────────────────────────────────────


def add_datetime_row(tag: str, var, parent: str = "", callback=None):
    """Add a DPG input_text for date/time that opens the picker on click."""
    grp_kwargs = {"horizontal": True}
    if parent:
        grp_kwargs["parent"] = parent

    with dpg.group(**grp_kwargs):
        dpg.add_input_text(
            tag=tag,
            default_value=var.get() if var is not None else "",
            width=-1,
            hint="YYYY-MM-DD HH:MM",
            callback=callback,
            readonly=True,
        )
        if var is not None:
            var._tag = tag

        # Click handler on the text box opens the picker
        _hr_tag = f"{tag}_click_hr"
        with dpg.item_handler_registry(tag=_hr_tag):
            dpg.add_item_clicked_handler(
                callback=lambda s, a, u=None: open_datetime_picker(var, callback)
            )
        dpg.bind_item_handler_registry(tag, _hr_tag)


def open_datetime_picker(var, callback=None):
    """Open a modal DPG window with a Sun-Sat calendar and time picker."""
    current_str = var.get() if var is not None else ""
    try:
        current_dt = datetime.strptime(current_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            current_dt = datetime.strptime(current_str, "%Y-%m-%d")
        except ValueError:
            current_dt = datetime.now()

    win_tag = "dt_picker_modal"
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)
    if dpg.does_item_exist("dt_picker_key_hr"):
        dpg.delete_item("dt_picker_key_hr")
    if dpg.does_item_exist("dt_picker_wheel_hr"):
        dpg.delete_item("dt_picker_wheel_hr")
    if dpg.does_item_exist("dt_hour_hover_hr"):
        dpg.delete_item("dt_hour_hover_hr")
    if dpg.does_item_exist("dt_min_hover_hr"):
        dpg.delete_item("dt_min_hover_hr")

    state = {
        "view_year": current_dt.year,
        "view_month": current_dt.month,
        "sel_year": current_dt.year,
        "sel_month": current_dt.month,
        "sel_day": current_dt.day,
        "hour": current_dt.hour,
        "minute": current_dt.minute,
        "cal_btns": []
    }

    months =["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def _rebuild_calendar():
        """Logic to update calendar labels and themes based on state."""
        if not dpg.does_item_exist(win_tag):
            return

        header_text = f"{months[state['view_month']-1]} {state['view_year']}"
        if dpg.does_item_exist("cal_month_year_text"):
            dpg.set_value("cal_month_year_text", header_text.center(22))

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdatescalendar(state["view_year"], state["view_month"])
        
        days =[]
        for week in month_days:
            days.extend(week)

        def _select_date(s, a, u):
            state["sel_year"] = u.year
            state["sel_month"] = u.month
            state["sel_day"] = u.day
            state["view_year"] = u.year
            state["view_month"] = u.month
            _rebuild_calendar()

        for i, btn in enumerate(state["cal_btns"]):
            if i < len(days):
                dt = days[i]
                dpg.configure_item(btn, label=str(dt.day), show=True)
                dpg.set_item_user_data(btn, dt)
                dpg.set_item_callback(btn, _select_date)
                
                is_current_month = (dt.month == state["view_month"])
                is_selected = (
                    dt.year == state["sel_year"]
                    and dt.month == state["sel_month"]
                    and dt.day == state["sel_day"]
                )
                
                dpg.bind_item_theme(btn, 0)
                if is_selected:
                    dpg.bind_item_theme(btn, "primary_btn_theme")
                elif not is_current_month:
                    dpg.bind_item_theme(btn, "cal_muted_theme")
            else:
                dpg.configure_item(btn, show=False)

    with dpg.window(tag=win_tag, label="Select Date & Time", modal=True,
                    no_resize=True, autosize=True, no_scrollbar=True,
                    pos=popup_pos(width=340, height=420)):

        with dpg.group(horizontal=True):
            def _prev():
                state["view_month"] -= 1
                if state["view_month"] < 1:
                    state["view_month"] = 12
                    state["view_year"] -= 1
                _rebuild_calendar()
            def _next():
                state["view_month"] += 1
                if state["view_month"] > 12:
                    state["view_month"] = 1
                    state["view_year"] += 1
                _rebuild_calendar()

            dpg.add_button(label="<", width=40, callback=_prev)
            dpg.add_text("", tag="cal_month_year_text")
            dpg.add_button(label=">", width=40, callback=_next)

        dpg.add_separator()
        dpg.add_spacer(height=5)
        
        # Calendar grid construction
        with dpg.table(header_row=True, borders_innerH=False, borders_innerV=False):
            for day_name in["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
                dpg.add_table_column(label=day_name, width_fixed=True, init_width_or_weight=42)
            for r in range(6):
                with dpg.table_row():
                    for c in range(7):
                        # Init with '00' label so autosize accounts for text width immediately
                        btn = dpg.add_button(label="00", width=40, height=28, show=True)
                        state["cal_btns"].append(btn)
                        
        dpg.add_spacer(height=5)
        dpg.add_separator()
        dpg.add_spacer(height=5)

        # ── Time Picker ──
        dpg.add_text("Time (HH : MM)")
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=30)
            hour_tag = dpg.add_input_int(
                default_value=state["hour"], min_value=0, max_value=23,
                step=1, width=90)
            dpg.add_text(":")
            minute_tag = dpg.add_input_int(
                default_value=state["minute"], min_value=0, max_value=59,
                step=15, width=90)

        # Scroll-wheel support
        _hour_hovered = {"v": False}
        _min_hovered = {"v": False}
        def _hour_hover(s, a): _hour_hovered["v"] = (a == 1)
        def _min_hover(s, a): _min_hovered["v"] = (a == 1)

        with dpg.item_handler_registry(tag="dt_hour_hover_hr"):
            dpg.add_item_hover_handler(callback=_hour_hover)
        dpg.bind_item_handler_registry(hour_tag, "dt_hour_hover_hr")
        with dpg.item_handler_registry(tag="dt_min_hover_hr"):
            dpg.add_item_hover_handler(callback=_min_hover)
        dpg.bind_item_handler_registry(minute_tag, "dt_min_hover_hr")

        def _on_wheel(s, a):
            delta = int(a)
            if _hour_hovered["v"]:
                h = (dpg.get_value(hour_tag) + delta) % 24
                dpg.set_value(hour_tag, h)
            elif _min_hovered["v"]:
                m = dpg.get_value(minute_tag) + delta * 15
                h = dpg.get_value(hour_tag)
                if m > 59: m, h = 0, (h + 1) % 24
                elif m < 0: m, h = 45, (h - 1) % 24
                dpg.set_value(minute_tag, m)
                dpg.set_value(hour_tag, h)

        with dpg.handler_registry(tag="dt_picker_wheel_hr"):
            dpg.add_mouse_wheel_handler(callback=_on_wheel)

        dpg.add_spacer(height=10)
        
        def _confirm():
            dt_str = (
                f"{state['sel_year']}-{state['sel_month']:02d}-{state['sel_day']:02d} "
                f"{dpg.get_value(hour_tag):02d}:{dpg.get_value(minute_tag):02d}"
            )
            if var is not None:
                var.set(dt_str)
                if hasattr(var, "_tag") and dpg.does_item_exist(var._tag):
                    dpg.set_value(var._tag, dt_str)
            if callback: callback(None, None, None)
            dpg.delete_item(win_tag)

        from .widgets import add_primary_button
        add_primary_button("OK", width=-1, callback=_confirm)

    # ── KEY FIX ──
    # DPG can be finicky about configuring items inside a table/window 
    # immediately during creation. We force the rebuild to happen on 
    # the next frame so the UI items are fully 'settled' in the backend.
    dpg.set_frame_callback(dpg.get_frame_count() + 1, _rebuild_calendar)

    # Arrow-key handlers
    def _on_key(sender, app_data):
        key = app_data
        if key == dpg.mvKey_Up:
            m = (dpg.get_value(minute_tag) + 15)
            h = dpg.get_value(hour_tag)
            if m > 59: m, h = 0, (h + 1) % 24
            dpg.set_value(minute_tag, m); dpg.set_value(hour_tag, h)
        elif key == dpg.mvKey_Down:
            m = (dpg.get_value(minute_tag) - 15)
            h = dpg.get_value(hour_tag)
            if m < 0: m, h = 45, (h - 1) % 24
            dpg.set_value(minute_tag, m); dpg.set_value(hour_tag, h)
        elif key in (dpg.mvKey_Left, dpg.mvKey_Right):
            delta = 1 if key == dpg.mvKey_Right else -1
            cur = datetime(state["sel_year"], state["sel_month"], state["sel_day"])
            nxt = cur + timedelta(days=delta)
            state["sel_year"], state["sel_month"], state["sel_day"] = nxt.year, nxt.month, nxt.day
            state["view_year"], state["view_month"] = nxt.year, nxt.month
            _rebuild_calendar()

    with dpg.handler_registry(tag="dt_picker_key_hr"):
        dpg.add_key_press_handler(callback=_on_key)