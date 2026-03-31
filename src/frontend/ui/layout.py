import dearpygui.dearpygui as dpg

from ..styling import theme as T
from ..styling.fonts import styled_text, HEADER, Icon
from .widgets import add_icon_button, add_primary_button

class LayoutBuilderMixin:

    _LEFT_DEFAULT = 350
    _DRAWER_HEIGHT = 134
    _AUTH_BTN_HEIGHT = 54
    _AUTH_BTN_INNER  = 46

    def setup_ui(self):
        with dpg.window(tag="primary_window", no_title_bar=True, no_resize=True,
                        no_move=True, no_scrollbar=True,
                        no_scroll_with_mouse=True):
            with dpg.table(header_row=False, resizable=False,
                           scrollX=False, scrollY=False,
                           policy=dpg.mvTable_SizingFixedFit):
                dpg.add_table_column(tag="left_panel_column",
                                     init_width_or_weight=self._LEFT_DEFAULT,
                                     width_fixed=True)
                dpg.add_table_column(init_width_or_weight=1, width_fixed=True)
                dpg.add_table_column(width_stretch=True)
                with dpg.table_row():
                    with dpg.child_window(tag="left_panel", border=False,
                                          height=-1,
                                          no_scrollbar=True,
                                          no_scroll_with_mouse=True):
                        self._build_left_panel()
                    with dpg.child_window(tag="panel_divider", border=False,
                                          height=-1,
                                          no_scrollbar=True,
                                          no_scroll_with_mouse=True, width=1):
                        with dpg.theme() as _div_theme:
                            with dpg.theme_component(dpg.mvChildWindow):
                                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, T.DPG_BORDER)
                        dpg.bind_item_theme("panel_divider", _div_theme)
                    with dpg.child_window(tag="right_panel", border=False,
                                          height=-1,
                                          no_scrollbar=True,
                                          no_scroll_with_mouse=True):
                        self._build_right_panel()

        dpg.set_primary_window("primary_window", True)
        self._build_settings_tab()
        self.apply_theme()
        self._setup_wheel_handler()
        self._apply_section_order()

        # Track base dimensions for proportional resize of right_tabs_content
        self._base_vp_height = dpg.get_viewport_height()
        self._base_tabs_height = 360
        dpg.set_viewport_resize_callback(self._on_viewport_resize)

    def _build_left_panel(self):
        self._account_drawer_open = False

        with dpg.child_window(tag="left_tabs_wrapper", border=False,
                              autosize_x=True, height=-1,
                              no_scrollbar=True, no_scroll_with_mouse=True):
            with dpg.tab_bar(tag="left_tabs"):
                with dpg.tab(label="Event", tag="Event"):
                    self._build_event_tab()
                with dpg.tab(label="Roster", tag="Roster"):
                    self._build_dj_roster_tab()
                with dpg.tab(label="Settings", tag="Settings"):
                    with dpg.child_window(tag="settings_scroll", height=-1,
                                          border=False, autosize_x=True):
                        pass  # populated by _build_settings_tab()

        # ── Global Texture Registry (prevents anonymous registry leaks) ───
        with dpg.texture_registry(tag="global_texture_registry"):
            dpg.add_static_texture(1, 1,[0, 0, 0, 0], tag="auth_avatar_tex")

        # ── Account drawer (hidden by default) ───────────────────────────
        with dpg.child_window(tag="account_drawer", height=self._DRAWER_HEIGHT,
                              border=True, autosize_x=True, no_scrollbar=True,
                              show=False):
            self._build_account_drawer()

        # ── Auth card toggle button ───────────────────────────────────
        _btn_h = self._AUTH_BTN_INNER
        _av_sz = 24
        dpg.add_button(tag="auth_card_btn", label="      Local", width=-1,
                       height=_btn_h,
                       callback=lambda: self._toggle_account_drawer())
        dpg.add_image("auth_avatar_tex", tag="auth_card_avatar",
                      width=_av_sz, height=_av_sz, show=False)

    def _build_right_panel(self):
        # ── Timeslots (resizable container) ───────────────────────────────
        styled_text("   TIMESLOTS  ", HEADER)
        _saved_h = self.settings.get("divider_height", 500)
        with dpg.child_window(tag="right_tabs_content", height=_saved_h,
                              border=False, autosize_x=True, no_scrollbar=True,
                              no_scroll_with_mouse=True):
            with dpg.child_window(tag="slots_scroll", height=-1,
                                  border=True, autosize_x=True,
                                  payload_type="DJ_CARD",
                                  drop_callback=lambda s, a, u=None: self._drop_dj_on_lineup(s, a)):
                pass  # populated by slot_manager

        dpg.add_button(tag="resize_handle", label="", width=-1, height=4)
        dpg.bind_item_theme("resize_handle", "resize_handle_theme")
        with dpg.item_handler_registry(tag="resize_handle_hr"):
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Left,
                                         callback=self._resize_handle_click)
        dpg.bind_item_handler_registry("resize_handle", "resize_handle_hr")
        with dpg.handler_registry(tag="resize_global_hr"):
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left,
                                       callback=self._resize_handle_drag)
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left,
                                          callback=self._resize_handle_release)

        # ── Output preview ────────────────────────────────────────────────
        with dpg.tab_bar(tag="output_tabs", callback=self._on_output_tab_changed):
            with dpg.tab(label="TEXT", tag="output_tab_text"):
                with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                               borders_outerH=False, borders_outerV=False, pad_outerX=False):
                    for _ in range(5):
                        dpg.add_table_column()
                    with dpg.table_row():
                        dpg.add_button(tag="fmt_discord", label="Discord", width=-1,
                                       callback=lambda: self.toggle_format())
                        dpg.add_button(tag="fmt_plain",   label="Plain",   width=-1,
                                       callback=lambda: self.set_plain_text())
                        dpg.add_button(tag="fmt_quest",   label="Quest",   width=-1,
                                       callback=lambda: self._toggle_stream_links("quest"))
                        dpg.add_button(tag="fmt_pc",      label="PC",      width=-1,
                                       callback=lambda: self._toggle_stream_links("pc"))
                        dpg.add_button(tag="fmt_times",   label="Times",   width=-1,
                                       callback=lambda: self._toggle_times())

                with dpg.child_window(tag="output_text_scroll", height=-44,
                                      autosize_x=True, border=True):
                    dpg.add_input_text(
                        tag="output_text",
                        default_value="",
                        multiline=True,
                        width=-1,
                        height=-1,
                    )
                with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False,
                               borders_outerH=False, borders_outerV=False, pad_outerX=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    with dpg.table_row():
                        add_icon_button(Icon.REFRESH, tag="refresh_output_btn", width=-1,
                                        callback=lambda: self.update_output())
                        add_icon_button(Icon.COPY, tag="copy_output_btn", width=-1,
                                        callback=lambda: self._copy_output())

            with dpg.tab(label="VISUAL PREVIEW", tag="output_tab_visual"):
                with dpg.child_window(tag="visual_preview_scroll", height=-1, border=True, autosize_x=True):
                    self._build_visual_preview()