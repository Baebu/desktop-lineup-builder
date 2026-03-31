from datetime import datetime, timedelta
import dearpygui.dearpygui as dpg

from .toast import show_toast

class InteractionsBuilderMixin:
    def _toggle_stream_links(self, fmt: str):
        """Toggle stream link format — only one active at a time, or none."""
        current = self.stream_link_format.get()
        self.stream_link_format.set("" if current == fmt else fmt)
        self.update_output()

    def _toggle_times(self):
        self.names_only.set(not self.names_only.get())
        self.update_output()

    def _copy_output(self):
        """Copy the output text to the system clipboard."""
        if dpg.does_item_exist("output_text"):
            text = dpg.get_value("output_text")
            if text:
                dpg.set_clipboard_text(text)
                show_toast("Copied to clipboard!", severity="success", duration=2.0)

    # ── Scroll-wheel helpers ─────────────────────────────────────────
    # One global handler checks is_item_hovered for every registered item.

    def _shift_timestamp(self, delta_mins: int):
        """Shift the event timestamp by *delta_mins* minutes."""
        raw = self.event_timestamp.get()
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            return
        dt += timedelta(minutes=delta_mins)
        new_str = dt.strftime("%Y-%m-%d %H:%M")
        self.event_timestamp.set(new_str)
        if dpg.does_item_exist("event_timestamp_input"):
            dpg.set_value("event_timestamp_input", new_str)
        self._schedule_update()

    def _setup_wheel_handler(self):
        if not hasattr(self, '_scroll_combos'):
            self._scroll_combos = {}
        if not hasattr(self, '_scroll_ints'):
            self._scroll_ints = {}
        if not dpg.does_item_exist("global_wheel_hr"):
            with dpg.handler_registry(tag="global_wheel_hr"):
                dpg.add_mouse_wheel_handler(callback=self._on_mouse_wheel)
                dpg.add_key_press_handler(dpg.mvKey_Up, callback=self._on_arrow_key)
                dpg.add_key_press_handler(dpg.mvKey_Down, callback=self._on_arrow_key)

    def _register_scroll_combo(self, tag: str, items: list, on_change):
        if not hasattr(self, '_scroll_combos'):
            self._scroll_combos = {}
        self._scroll_combos[tag] = (list(items), on_change)

    def _register_scroll_int(self, tag: str, min_val: int = 0,
                             max_val: int = 9999, on_change=None):
        if not hasattr(self, '_scroll_ints'):
            self._scroll_ints = {}
        self._scroll_ints[tag] = (min_val, max_val, on_change)

    def _on_arrow_key(self, sender, app_data):
        """Arrow Up/Down on the timestamp input shifts time."""
        if not (dpg.does_item_exist("event_timestamp_input")
                and dpg.is_item_hovered("event_timestamp_input")):
            return
        shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
        step = 1440 if shift else 15
        if app_data == dpg.mvKey_Up:
            self._shift_timestamp(step)
        else:
            self._shift_timestamp(-step)

    def _on_mouse_wheel(self, sender, app_data):
        # app_data is positive when scrolling up, negative when down.
        # We invert so scroll-up = higher value.
        delta = 1 if app_data > 0 else -1

        # ── Timestamp scroll ──────────────────────────────────────────
        if (dpg.does_item_exist("event_timestamp_input")
                and dpg.is_item_hovered("event_timestamp_input")):
            shift = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
            step = 1440 if shift else 15
            self._shift_timestamp(delta * step)
            return

        # Clean up dead scroll items to prevent memory leaks
        dead_combos =[t for t in getattr(self, '_scroll_combos', {}) if not dpg.does_item_exist(t)]
        for t in dead_combos:
            del self._scroll_combos[t]

        for tag, (items, cb) in list(getattr(self, '_scroll_combos', {}).items()):
            if dpg.does_item_exist(tag) and dpg.is_item_hovered(tag):
                itype = dpg.get_item_info(tag).get("type", "")
                if "Button" in itype:
                    cur = dpg.get_item_configuration(tag).get("label")
                else:
                    cur = str(dpg.get_value(tag))
                try:
                    idx = items.index(str(cur))
                except ValueError:
                    idx = 0
                new_idx = max(0, min(len(items) - 1, idx - delta))
                if "Button" in itype:
                    dpg.configure_item(tag, label=items[new_idx])
                else:
                    dpg.set_value(tag, items[new_idx])
                cb()
                return

        # Clean up dead int items to prevent memory leaks
        dead_ints =[t for t in getattr(self, '_scroll_ints', {}) if not dpg.does_item_exist(t)]
        for t in dead_ints:
            del self._scroll_ints[t]

        for tag, (mn, mx, cb) in list(getattr(self, '_scroll_ints', {}).items()):
            if dpg.does_item_exist(tag) and dpg.is_item_hovered(tag):
                try:
                    cur = int(dpg.get_value(tag))
                except (ValueError, TypeError):
                    cur = mn
                new_val = max(mn, min(mx, cur + delta))
                dpg.set_value(tag, str(new_val))
                if cb:
                    cb()
                return

    def _is_over_slots_panel(self, x_root: int, y_root: int) -> bool:
        try:
            mn = dpg.get_item_rect_min("slots_scroll")
            mx = dpg.get_item_rect_max("slots_scroll")
        except Exception:
            return False
        return mn[0] <= x_root <= mx[0] and mn[1] <= y_root <= mx[1]

    # ── Resize handle logic ───────────────────────────────────────────

    _resize_dragging = False
    _resize_start_y = 0
    _resize_start_h = 360

    def _resize_handle_click(self, sender, app_data):
        self._resize_dragging = True
        self._resize_start_y = dpg.get_mouse_pos(local=False)[1]
        try:
            self._resize_start_h = dpg.get_item_height("right_tabs_content")
        except Exception:
            self._resize_start_h = 360

    def _resize_handle_drag(self, sender, app_data):
        if not self._resize_dragging:
            return
        current_y = dpg.get_mouse_pos(local=False)[1]
        delta = current_y - self._resize_start_y
        new_h = max(80, self._resize_start_h + int(delta))
        max_h = dpg.get_viewport_height() - 200
        new_h = min(new_h, max_h)
        dpg.configure_item("right_tabs_content", height=new_h)

    def _resize_handle_release(self, sender, app_data):
        self._resize_dragging = False
        # Update base dimensions so viewport resize scales from the user-set height
        if dpg.does_item_exist("right_tabs_content"):
            self._base_tabs_height = dpg.get_item_height("right_tabs_content")
            self._base_vp_height = dpg.get_viewport_height()
            # Persist divider position
            self.settings["divider_height"] = self._base_tabs_height
            self.save_settings()

    def _on_viewport_resize(self, sender=None, app_data=None):
        """Scale right panel contents when the viewport is resized."""
        vp_h = dpg.get_viewport_height()
        base_vp = getattr(self, "_base_vp_height", 600)
        base_tabs = getattr(self, "_base_tabs_height", 360)

        if base_vp <= 0 or not dpg.does_item_exist("right_tabs_content"):
            return
        new_h = max(80, int(base_tabs * vp_h / base_vp))
        max_h = vp_h - 200
        new_h = min(new_h, max_h)
        dpg.configure_item("right_tabs_content", height=new_h)