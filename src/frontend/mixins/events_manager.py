import copy
import datetime
import os

import dearpygui.dearpygui as dpg

from ..styling.fonts import BODY, LABEL, MUTED, Icon, bind_icon_font, styled_text
from ..ui.widgets import add_icon_button, popup_pos
from ..ui.toast import show_toast


class EventsMixin:
    """Manages saved event lineups: save, load, delete, duplicate, and UI refresh."""
    
    def _get_full_title(self, title: str, vol: str) -> str:
        vol_prefix = getattr(self, "settings", {}).get("vol_prefix", " VOL.")
        return f"{title}{vol_prefix}{vol}" if str(vol).strip() else title

    def _get_current_event_state(self):
        title = self.event_title_var.get().strip()
        vol = self.event_vol_var.get().strip()
        event_data = {
            "title": title,
            "vol": vol,
            "group_name": self.group_name_var.get().strip(),
            "collab": bool(self.collab_with_var.get().strip()),
            "collab_with": self.collab_with_var.get().strip(),
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": self.event_timestamp.get(),
            "genres": self.active_genres.copy(),
            "names_only": self.names_only.get(),
            "social_links": dict(getattr(self, "social_links", {})),
            "discord_embed_image": getattr(self, "discord_embed_image", ""),
            "slots":[]
        }

        for slot in self.slots:
            try:
                dur = int(slot.duration_var.get())
            except (ValueError, TypeError):
                dur = 60
            event_data["slots"].append({
                "name": slot.name_var.get().strip(),
                "genre": slot.genre_var.get().strip(),
                "club": slot.club_var.get().strip(),
                "duration": dur
            })
        return event_data

    def _save_current_state_to_auto_save(self):
        if getattr(self, "_is_dirty", False):
            state = self._get_current_event_state()
            if hasattr(self, "db"):
                self.db.kv_set("auto_save", state)

    def _clear_auto_save(self):
        if hasattr(self, "db"):
            self.db.kv_delete("auto_save")

    def _is_event_data_empty(self, event_data: dict) -> bool:
        """Check if the event data is completely empty (no title, no slots, etc)."""
        if event_data.get("title", "").strip(): return False
        if str(event_data.get("vol", "")).strip(): return False
        if event_data.get("group_name", "").strip(): return False
        if event_data.get("collab_with", "").strip(): return False
        if event_data.get("discord_embed_image", "").strip(): return False
        if event_data.get("genres"): return False
        
        if any(str(v).strip() for v in event_data.get("social_links", {}).values()):
            return False
            
        for slot in event_data.get("slots", []):
            if slot.get("name", "").strip(): return False
            if slot.get("genre", "").strip(): return False
            
        return True

    def _prompt_auto_save_recovery(self, auto_save_data):
        wt = "recovery_confirm_win"
        if dpg.does_item_exist(wt):
            dpg.delete_item(wt)
            
        def _recover():
            self.load_event_lineup(auto_save_data, is_recovery=True)
            dpg.delete_item(wt)
            show_toast("Recovered unsaved lineup.", severity="success")

        def _discard():
            self._clear_auto_save()
            self.add_initial_slots()
            self.update_output()
            dpg.delete_item(wt)

        vp_w = dpg.get_viewport_width()
        vp_h = dpg.get_viewport_height()
        pos =[max(0, (vp_w - 350) // 2), max(0, (vp_h - 150) // 2)]

        with dpg.window(tag=wt, label="Crash Recovery", modal=True,
                        autosize=True, no_resize=True, no_scrollbar=True,
                        pos=pos):
            dpg.add_text("An unsaved lineup was found from a previous session.\nWould you like to recover it?")
            dpg.add_spacer(height=8)
            with dpg.group(horizontal=True):
                btn = dpg.add_button(label="Recover", width=140, callback=_recover)
                dpg.bind_item_theme(btn, "success_btn_theme")
                btn2 = dpg.add_button(label="Discard", width=140, callback=_discard)
                dpg.bind_item_theme(btn2, getattr(self, "_danger_btn_theme", ""))

    def save_event_lineup(self):
        event_data = self._get_current_event_state()
        title = event_data["title"]
        vol = event_data["vol"]
        if not title:
            _warn_win = "save_warn_win"
            if not dpg.does_item_exist(_warn_win):
                with dpg.window(tag=_warn_win, label="Warning", modal=True,
                                autosize=True, no_resize=True, no_scrollbar=True,
                                pos=popup_pos()):
                    dpg.add_text("Please set an Event Title before saving the lineup.")
                    dpg.add_button(label="OK", width=-1, user_data=_warn_win,
                                   callback=lambda s, a, u: dpg.delete_item(u))
            return

        full_title = self._get_full_title(title, vol)

        existing_idx = None
        for i, ev in enumerate(self.saved_events):
            saved_full_title = self._get_full_title(ev['title'], ev.get('vol', ''))
            if saved_full_title == full_title:
                existing_idx = i
                break

        def _do_save(_wt=None):
            if existing_idx is not None:
                self.saved_events[existing_idx] = event_data
            else:
                self.saved_events.append(event_data)
            self.saved_events.sort(key=lambda e: e.get('created_at', ''), reverse=True)
            self._current_event_key = (title, vol)
            self._save_events()
            self.refresh_saved_events_ui()
            
            self._is_dirty = False
            self._clear_auto_save()
            show_toast("Event Saved", severity="success")
            
            if _wt and dpg.does_item_exist(_wt):
                dpg.delete_item(_wt)

        if existing_idx is not None:
            wt = "overwrite_confirm_win"
            if dpg.does_item_exist(wt):
                dpg.delete_item(wt)
            with dpg.window(tag=wt, label="Update Event", modal=True,
                            autosize=True, no_resize=True, no_scrollbar=True,
                            pos=popup_pos()):
                dpg.add_text(f"'{full_title}' already exists. Overwrite?")
                with dpg.group(horizontal=True):
                    yes_btn = dpg.add_button(label="Yes", width=140, user_data=wt,
                                   callback=lambda s, a, u: _do_save(u))
                    dpg.bind_item_theme(yes_btn, "primary_btn_theme")
                    dpg.add_button(label="No", width=140, user_data=wt,
                                   callback=lambda s, a, u: dpg.delete_item(u))
        else:
            _do_save()

    def new_event(self):
        """Reset all event fields and slots to a blank state."""
        has_content = any(s.name_var.get().strip() or s.genre_var.get().strip() for s in self.slots)

        def _do_new(_wt=None):
            self._current_event_key = None
            import datetime as _dt
            now = _dt.datetime.now()
            self.event_title_var.set("")
            self.event_vol_var.set("")
            self.group_name_var.set("")
            self.collab_var.set(False)
            self.collab_with_var.set("")
            self.event_timestamp.set(now.strftime("%Y-%m-%d") + " 20:00")
            self.active_genres =[]
            self.refresh_genre_tags()
            self.names_only.set(False)
            self.social_links = {}
            self._sync_social_link_inputs()
            self.discord_embed_image = ""
            if dpg.does_item_exist("embed_image_browse_btn"):
                dpg.set_item_label("embed_image_browse_btn", "Select Image...")
            for slot in self.slots:
                slot.destroy()
            self.slots.clear()
            self.add_slot()
            if dpg.does_item_exist("left_tabs"):
                dpg.set_value("left_tabs", "Event")
                
            self.update_output()
            self._is_dirty = False
            self._clear_auto_save()
            
            if _wt and dpg.does_item_exist(_wt):
                dpg.delete_item(_wt)

        if self._is_dirty:
            from ..ui.confirm_dialog import confirm
            confirm(
                "You have unsaved changes. Discard them and start fresh?",
                on_confirm=_do_new,
                title="Unsaved Changes",
                confirm_label="Discard",
                danger=True
            )
        elif has_content:
            from ..ui.confirm_dialog import confirm
            confirm(
                "Clear the current lineup and start fresh?",
                on_confirm=_do_new,
                title="New Event",
                confirm_label="Clear",
                danger=True
            )
        else:
            _do_new()

    def _load_last_event(self):
        """Load the most recently saved event, or the current event if set."""
        if self._current_event_key:
            title, vol = self._current_event_key
            for ev in self.saved_events:
                ev_full = self._get_full_title(ev['title'], ev.get('vol', ''))
                cur_full = self._get_full_title(title, vol)
                if ev_full == cur_full:
                    self.load_event_lineup(ev)
                    return
        if self.saved_events:
            self.load_event_lineup(self.saved_events[0])

    def load_event_lineup(self, event_data, is_recovery=False):
        def _do_load():
            self.event_title_var.set(event_data.get("title", ""))
            self.event_vol_var.set(event_data.get("vol", ""))
            self.group_name_var.set(event_data.get("group_name", ""))
            self.collab_var.set(event_data.get("collab", False))
            self.collab_with_var.set(event_data.get("collab_with", ""))
            self.event_timestamp.set(event_data.get("timestamp", ""))

            self.active_genres = event_data.get("genres",[]).copy()
            self.refresh_genre_tags()

            self.names_only.set(event_data.get("names_only", False))
            self.social_links = event_data.get("social_links", {}).copy()
            self._sync_social_link_inputs()

            img_path = event_data.get("discord_embed_image", "")
            
            # Check if the image path is broken
            if img_path and not os.path.exists(img_path):
                from ..ui.confirm_dialog import confirm
                confirm(
                    f"The image file for this event could not be found:\n{img_path}\n\nWould you like to select a new image?",
                    on_confirm=lambda: self._browse_embed_image(),
                    title="Missing Image",
                    confirm_label="Select Image"
                )
                img_path = ""
                
            self.discord_embed_image = img_path
            if dpg.does_item_exist("embed_image_browse_btn"):
                if img_path:
                    dpg.set_item_label("embed_image_browse_btn", os.path.basename(img_path))
                else:
                    dpg.set_item_label("embed_image_browse_btn", "Select Image...")

            for slot in self.slots:
                slot.destroy()
            self.slots.clear()

            for slot_data in event_data.get("slots",[]):
                try:
                    dur = int(slot_data.get("duration", 60))
                except (ValueError, TypeError):
                    dur = 60
                self.add_slot(
                    slot_data.get("name", ""),
                    slot_data.get("genre", ""),
                    slot_data.get("club", ""),
                    dur,
                    refresh=False
                )

            if dpg.does_item_exist("left_tabs"):
                dpg.set_value("left_tabs", "Event")
                
            self.refresh_slots()
            self.update_output()
            self._current_event_key = (event_data.get("title", ""), event_data.get("vol", ""))
            
            if is_recovery:
                self._is_dirty = True
                if hasattr(self, "_schedule_auto_save"):
                    self._schedule_auto_save()
            else:
                self._is_dirty = False
                self._clear_auto_save()

        if self._is_dirty and not is_recovery:
            from ..ui.confirm_dialog import confirm
            confirm(
                "You have unsaved changes. Discard them and load this event?",
                on_confirm=_do_load,
                title="Unsaved Changes",
                confirm_label="Discard & Load",
                danger=True
            )
        else:
            _do_load()

    def delete_event_lineup(self, event_data):
        full_title = self._get_full_title(event_data['title'], event_data.get('vol', ''))
        wt = "delete_event_confirm"
        if dpg.does_item_exist(wt):
            dpg.delete_item(wt)
            
        def _do_delete(_wt=wt, _ev=event_data):
            if _ev in self.saved_events:
                self.saved_events.remove(_ev)
            self._save_events()
            self.refresh_saved_events_ui()
            
            # Only reset UI to a blank slate if the deleted event is the currently loaded one
            if self._current_event_key == (_ev.get("title", ""), _ev.get("vol", "")):
                self._current_event_key = None
                import datetime as _dt
                now = _dt.datetime.now()
                self.event_title_var.set("")
                self.event_vol_var.set("")
                self.group_name_var.set("")
                self.collab_var.set(False)
                self.collab_with_var.set("")
                self.event_timestamp.set(now.strftime("%Y-%m-%d") + " 20:00")
                self.active_genres =[]
                self.refresh_genre_tags()
                self.names_only.set(False)
                self.social_links = {}
                self._sync_social_link_inputs()
                self.discord_embed_image = ""
                if dpg.does_item_exist("embed_image_browse_btn"):
                    dpg.set_item_label("embed_image_browse_btn", "Select Image...")
                for slot in self.slots:
                    slot.destroy()
                self.slots.clear()
                self.add_slot()
                if dpg.does_item_exist("left_tabs"):
                    dpg.set_value("left_tabs", "Event")
                self.update_output()
                self._is_dirty = False
                self._clear_auto_save()
            
            if dpg.does_item_exist(_wt):
                dpg.delete_item(_wt)
                
        with dpg.window(tag=wt, label="Confirm Delete", modal=True,
                        autosize=True, no_resize=True, no_scrollbar=True,
                        pos=popup_pos()):
            dpg.add_text(f"Delete saved event '{full_title}'?")
            with dpg.group(horizontal=True):
                _yes = dpg.add_button(label="Yes", width=140, callback=lambda s, a, u=None: _do_delete())
                dpg.bind_item_theme(_yes, self._danger_btn_theme)
                dpg.add_button(label="No", width=140, user_data=wt,
                               callback=lambda s, a, u: dpg.delete_item(u))

    def duplicate_event_lineup(self, event_data):
        def _do_dupe():
            dupe = copy.deepcopy(event_data)
            
            title = dupe.get("title", "").strip()
            
            dupe["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Clear slots, genres, and embed image
            dupe["slots"] = []
            dupe["genres"] =[]
            dupe["discord_embed_image"] = ""
            
            # Shift timestamp by 1 week
            old_timestamp = dupe.get("timestamp", "")
            if old_timestamp:
                try:
                    dt = datetime.datetime.strptime(old_timestamp, "%Y-%m-%d %H:%M")
                    dt += datetime.timedelta(days=7)
                    dupe["timestamp"] = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass
                    
            # Keep only DISCORD and VRC GROUP links
            old_links = dupe.get("social_links", {})
            new_links = {}
            for key in ["DISCORD", "VRC GROUP"]:
                if key in old_links:
                    new_links[key] = old_links[key]
            dupe["social_links"] = new_links

            # Find a unique volume IMMEDIATELY before appending to prevent race conditions
            all_vols = [
                int(ev["vol"]) for ev in self.saved_events
                if ev.get("title", "").strip() == title and str(ev.get("vol", "")).isdigit()
            ]
            if all_vols:
                dupe["vol"] = str(max(all_vols) + 1)
            else:
                dupe["vol"] = "2"

            self.saved_events.append(dupe)
            self.saved_events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
            self._save_events()
            self.refresh_saved_events_ui()
            
            # Since we confirmed (if dirty), clear dirty state so load_event_lineup doesn't prompt again
            self._is_dirty = False
            self.load_event_lineup(dupe)

        if self._is_dirty:
            from ..ui.confirm_dialog import confirm
            confirm(
                "You have unsaved changes. Discard them to duplicate and load this event?",
                on_confirm=_do_dupe,
                title="Unsaved Changes",
                confirm_label="Discard & Duplicate",
                danger=True
            )
        else:
            _do_dupe()

    def refresh_saved_events_ui(self):
        if not dpg.does_item_exist("saved_events_drawer_content"):
            return
        dpg.delete_item("saved_events_drawer_content", children_only=True)
        if not self.saved_events:
            with dpg.group(parent="saved_events_drawer_content"):
                dpg.add_spacer(height=6)
                styled_text("No saved events yet.", LABEL)
                dpg.add_spacer(height=6)
            return

        for ev in self.saved_events:
            full_title = self._get_full_title(ev['title'], ev.get('vol', ''))
            slots_count = len(ev.get("slots",[]))
            timestamp = ev.get("timestamp", "")

            # Matches the DJ roster card look (1x1 table for border)
            with dpg.group(parent="saved_events_drawer_content"):
                dpg.add_spacer(height=2)  # Tighter spacing between cards
                with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                               borders_outerH=True, borders_outerV=True, pad_outerX=True, width=-6):
                    dpg.add_table_column()
                    with dpg.table_row():
                        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                                       borders_outerH=False, borders_outerV=False, pad_outerX=False):
                            dpg.add_table_column(width_stretch=True)
                            dpg.add_table_column(width_fixed=True)
                            with dpg.table_row():
                                with dpg.group():
                                    styled_text(full_title, BODY)
                                    styled_text(f"{timestamp}  |  {slots_count} slots", MUTED)
                                with dpg.group(horizontal=True):
                                    def _load(s, a, u):
                                        if not self._section_collapsed.get("saved_events", True):
                                            self._toggle_section("saved_events")
                                        self.load_event_lineup(u)

                                    def _dupe(s, a, u):
                                        if not self._section_collapsed.get("saved_events", True):
                                            self._toggle_section("saved_events")
                                        self.duplicate_event_lineup(u)

                                    add_icon_button(Icon.DOWNLOAD, width=28, height=20, user_data=ev, callback=_load)
                                    add_icon_button(Icon.COPY, width=28, height=20, user_data=ev, callback=_dupe)
                                    add_icon_button(Icon.DELETE, width=28, height=20, is_danger=True, user_data=ev, callback=lambda s, a, u: self.delete_event_lineup(u))