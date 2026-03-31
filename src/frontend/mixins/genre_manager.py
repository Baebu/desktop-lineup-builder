import dearpygui.dearpygui as dpg

from ..styling.fonts import HEADER, MUTED, styled_text
from ..ui.widgets import popup_pos


class GenreMixin:
    """Manages active-genre tags and the saved-genres panel."""

    def add_genre_from_entry(self, event=None):
        val = self.genre_entry_var.get().strip()
        if val:
            self.genre_entry_var.set("")
            self.add_genre(val)

    def add_genre(self, genre):
        genre = genre.strip()
        if genre.lower() not in[g.lower() for g in self.active_genres]:
            self.active_genres.append(genre)

        if genre.lower() not in[g.lower() for g in self.saved_genres]:
            self.saved_genres.append(genre)
            self._save_library()

        self.refresh_genre_tags()
        self.update_output()

    def delete_saved_genre(self):
        val = self.genre_entry_var.get().strip()
        if val and val in self.saved_genres:
            win_tag = "del_genre_confirm"
            if dpg.does_item_exist(win_tag):
                dpg.delete_item(win_tag)
            def _do_del(_g=val, _wt=win_tag):
                self.saved_genres.remove(_g)
                if _g in self.active_genres:
                    self.active_genres.remove(_g)
                self._save_library()
                self.genre_entry_var.set("")
                if dpg.does_item_exist("genre_entry"):
                    dpg.set_value("genre_entry", "")
                self.refresh_genre_tags()
                self.update_output()
                if dpg.does_item_exist(_wt):
                    dpg.delete_item(_wt)
            with dpg.window(tag=win_tag, label="Confirm Delete", modal=True,
                            autosize=True, no_resize=True, no_scrollbar=True,
                            pos=popup_pos()):
                dpg.add_text(f"Remove '{val}' from saved genres?")
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Yes", width=140, callback=lambda s, a, u=None: _do_del())
                    dpg.bind_item_theme(dpg.last_item(), self._danger_btn_theme)
                    dpg.add_button(label="No", width=140, user_data=win_tag,
                                   callback=lambda s, a, u: dpg.delete_item(u))

    def remove_genre(self, genre):
        if genre in self.active_genres:
            self.active_genres.remove(genre)
        self.refresh_genre_tags()
        self.update_output()

    def _toggle_genre(self, genre: str, is_active: bool):
        if is_active:
            self.remove_genre(genre)
        else:
            if genre.lower() not in [g.lower() for g in self.active_genres]:
                self.active_genres.append(genre)
            self.refresh_genre_tags()
            self.update_output()

    def refresh_genre_tags(self):
        """Rebuild genre tags using a table-based layout to ensure wrapping."""
        if not dpg.does_item_exist("genre_tags_frame"):
            return
        dpg.delete_item("genre_tags_frame", children_only=True)
        
        if not self.saved_genres:
            styled_text("Type a genre above and press Enter to add it.",
                         MUTED, parent="genre_tags_frame")
            return
            
        query = self.genre_search_var.get().strip().lower() if hasattr(self, 'genre_search_var') else ""
        filtered = [g for g in self.saved_genres if not query or query in g.lower()]
        
        if not filtered and query:
            styled_text("No genres match your search.",
                         MUTED, parent="genre_tags_frame")
            return

        active_lower = {g.lower() for g in self.active_genres}

        # Available width
        usable_w = dpg.get_item_rect_size("genre_tags_frame")[0] or 300
        
        # Approximate button width calculation
        padding = 16
        char_width = 8
        
        row_items = []
        current_row_w = 0
        rows = []
        
        # Group items into rows that fit
        for genre in filtered:
            btn_w = (len(genre) * char_width) + padding
            if current_row_w + btn_w > usable_w and row_items:
                rows.append(row_items)
                row_items = []
                current_row_w = 0
            row_items.append(genre)
            current_row_w += btn_w + 6 # spacing
        if row_items:
            rows.append(row_items)

        # Render rows
        for row in rows:
            with dpg.group(parent="genre_tags_frame", horizontal=True):
                for genre in row:
                    is_active = genre.lower() in active_lower
                    btn = dpg.add_button(
                        label=genre, 
                        height=20,
                        user_data=(genre, is_active),
                        callback=lambda s, a, u: self._toggle_genre(u[0], u[1]),
                    )
                    if is_active:
                        dpg.bind_item_theme(btn, "success_btn_theme")

    # ── Genre editor drawer ───────────────────────────────────────────────

    def _toggle_genre_settings_drawer(self):
        """Toggle the inline genre settings drawer open/closed."""
        tag = "genre_settings_drawer"
        if not dpg.does_item_exist(tag):
            return
        currently_shown = dpg.is_item_shown(tag)
        dpg.configure_item(tag, show=not currently_shown)
        if not currently_shown:
            self._rebuild_genre_editor_list()

    def _build_genre_settings_drawer(self):
        """Populate the genre settings drawer."""
        dpg.add_spacer(height=2)
        with dpg.group(horizontal=True):
            def _add_new(s, a):
                val = dpg.get_value("drawer_new_genre_input").strip()
                if not val:
                    return
                dpg.set_value("drawer_new_genre_input", "")
                self.add_genre(val)
                self._rebuild_genre_editor_list()
                
            dpg.add_input_text(tag="drawer_new_genre_input", hint="New genre name...", width=-50,
                               on_enter=True, callback=_add_new)
            add_btn = dpg.add_button(label="Add", callback=_add_new, width=-1)
            dpg.bind_item_theme(add_btn, "primary_btn_theme")
            
        dpg.add_spacer(height=4)
        
        with dpg.child_window(tag="genre_editor_scroll", height=-1, border=False):
            dpg.add_group(tag="genre_editor_list")

    def _rebuild_genre_editor_list(self):
        _wg = "genre_editor_list"
        if not dpg.does_item_exist(_wg):
            return
        dpg.delete_item(_wg, children_only=True)
        if not self.saved_genres:
            styled_text("No genres saved yet.", MUTED, parent=_wg)
            return
            
        with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False, parent=_wg):
            dpg.add_table_column(width_stretch=True)
            dpg.add_table_column(width_fixed=True)
            for i, genre in enumerate(self.saved_genres):
                with dpg.table_row():
                    dpg.add_text(genre)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="^", small=True, user_data=i,
                                       callback=lambda s, a, u: self._move_saved_genre(u, -1))
                        dpg.add_button(label="v", small=True, user_data=i,
                                       callback=lambda s, a, u: self._move_saved_genre(u, 1))
                        dpg.add_button(label="X", small=True, user_data=genre,
                                       callback=lambda s, a, u: self._remove_saved_genre(u))

    def _move_saved_genre(self, idx, delta):
        ni = idx + delta
        if 0 <= ni < len(self.saved_genres):
            self.saved_genres[idx], self.saved_genres[ni] = (
                self.saved_genres[ni], self.saved_genres[idx])
            self._save_library()
            self.refresh_genre_tags()
            self._rebuild_genre_editor_list()

    def _remove_saved_genre(self, genre):
        if genre in self.saved_genres:
            self.saved_genres.remove(genre)
        if genre in self.active_genres:
            self.active_genres.remove(genre)
        self._save_library()
        self.refresh_genre_tags()
        self.update_output()
        self._rebuild_genre_editor_list()
