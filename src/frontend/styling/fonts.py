"""
Module: fonts.py
Purpose: Central text style configuration and font management.
         Single source of truth for all text styling (colors, fonts).
         Provides Icon constants, text style presets, and a styled_text() helper.
"""
import os
import sys

import dearpygui.dearpygui as dpg

from . import theme as T


# ── Icon constants (plain text labels) ────────────────────────────────────────
class Icon:
    DRAG     = "\ue945"   # drag_indicator
    UP       = "\ue5ce"   # expand_less
    DOWN     = "\ue5cf"   # expand_more
    DROPDOWN = "\ue5c5"   # arrow_drop_down
    CLOSE    = "\ue5cd"   # close
    CHECK    = "\ue5ca"   # check
    ADD      = "\ue145"   # add
    EDIT     = "\ue3c9"   # edit
    DELETE   = "\ue872"   # delete
    SAVE     = "\ue161"   # save
    REFRESH  = "\ue5d5"   # refresh
    RESTORE  = "\ue8ba"   # restore
    SEARCH   = "\ue8b6"   # search
    DOWNLOAD = "\uf090"   # download
    UPLOAD   = "\ue2c6"   # upload
    COPY     = "\ue14d"   # content_copy
    FOLDER   = "\ue2c7"   # folder
    PREVIEW  = "\ue8f4"   # visibility
    LINK     = "\ue157"   # link
    NOTES    = "\ue873"   # description
    COMPUTER = "\ue30a"   # computer
    CHAT     = "\ue0b7"   # chat
    CODE     = "\ue86f"   # code
    HEADSET  = "\ue310"   # headset
    SETTINGS = "\ue8b8"   # settings
    VR       = "\ue3c7"   # vrpano
    SCHEDULE = "\ue8b5"   # schedule
    TUNE     = "\ue429"   # tune
    PASTE    = "\ue14f"   # content_paste
    IMAGE    = "\ue3f4"   # image
    PERSON   = "\ue7fd"   # person


# ── Font configuration ───────────────────────────────────────────────────────
FONT_SIZE_DEFAULT = 16    # base UI font size


# ── Text styles ──────────────────────────────────────────────────────────────
# Each style is a dict of kwargs forwarded to dpg.add_text().
# To change how any text category looks app-wide, edit its dict here.

HEADER  = {"theme": "text_header_theme"}      # section headers: "EVENT CONFIGURATION", "DJ ROSTER", etc.
LABEL   = {"theme": "text_label_theme"}       # field labels: "EVENT TITLE", "GENRES", etc.
BODY    = {}                                  # primary body text (uses global theme color)
MUTED   = {"theme": "text_muted_theme"}       # hints, disabled text, secondary info
ERROR   = {"theme": "text_error_theme"}       # validation / error messages
HINT    = {"theme": "text_hint_theme"}        # subtle drag-hint text
SUCCESS = {"theme": "text_success_theme"}     # success feedback messages


def styled_text(label: str, style: dict = None, **kwargs) -> int:
    """Create a dpg.add_text() with centralized styling.

    Usage::

        styled_text("EVENT CONFIG", HEADER)
        styled_text("field label", LABEL, tag="my_tag")
        styled_text("plain text")  # no style — uses DPG theme default
    """
    theme_tag = None
    if style and "theme" in style:
        theme_tag = style["theme"]
        
    color_val = None
    if style and "color" in style:
        color_val = style["color"]
        
    merged = kwargs.copy()
    if color_val:
        merged["color"] = color_val

    item = dpg.add_text(label, **merged)
    if theme_tag:
        dpg.bind_item_theme(item, theme_tag)
    return item


# ── Font loading ─────────────────────────────────────────────────────────────

def _find_system_font() -> str | None:
    """Return path to a suitable system sans-serif TTF."""
    if sys.platform == "win32":
        candidates =["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    elif sys.platform == "darwin":
        candidates =["/System/Library/Fonts/SFNS.ttf", "/Library/Fonts/Arial.ttf"]
    else:
        candidates =[
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _find_icon_font() -> str | None:
    """Return path to the Material Symbols Rounded TTF bundled in assets/."""
    if getattr(sys, "frozen", False):
        # When frozen, PyInstaller unpacks to sys._MEIPASS in one-file mode
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        # In development: desktop/src/frontend/styling/fonts.py
        # Up 4 levels: desktop/src/frontend/styling -> desktop -> find assets there
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    path = os.path.join(base, "assets", "Material_Symbols_Rounded", "static",
                        "MaterialSymbolsRounded-Regular.ttf")
    return path if os.path.exists(path) else None


# Module-level references to the loaded fonts
icon_font = None
h1_font = None
h2_font = None
h3_font = None


def setup_fonts(size: int = FONT_SIZE_DEFAULT) -> int | None:
    """Load a system sans-serif font, bold variants for headers, and a Material Symbols icon font.

    Call once after dpg.create_context() and before any widget creation.
    """
    global icon_font, h1_font, h2_font, h3_font
    font_path = _find_system_font()
    if not font_path:
        return None

    # Attempt to locate the bold variant of the system font
    bold_path = font_path
    dir_name = os.path.dirname(font_path)
    base_name = os.path.basename(font_path).lower()
    
    if base_name == "segoeui.ttf":
        bold_path = os.path.join(dir_name, "segoeuib.ttf")
    elif base_name == "arial.ttf":
        if os.path.exists(os.path.join(dir_name, "arialbd.ttf")):
            bold_path = os.path.join(dir_name, "arialbd.ttf")
        elif os.path.exists(os.path.join(dir_name, "Arial Bold.ttf")):
            bold_path = os.path.join(dir_name, "Arial Bold.ttf")
    elif base_name == "dejavusans.ttf":
        bold_path = os.path.join(dir_name, "DejaVuSans-Bold.ttf")
    elif base_name == "liberationsans-regular.ttf":
        bold_path = os.path.join(dir_name, "LiberationSans-Bold.ttf")
    
    if not os.path.exists(bold_path):
        bold_path = font_path

    icon_path = _find_icon_font()

    main_font = None
    with dpg.font_registry():
        with dpg.font(font_path, size) as main_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range(0x00A0, 0x02FF)   # Latin Extended
            dpg.add_font_chars([0x25BC, 0x25BA]) # ▼ and ► for collapsible headers
            
        with dpg.font(bold_path, int(size * 1.5)) as h1_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range(0x00A0, 0x02FF)
            
        with dpg.font(bold_path, int(size * 1.25)) as h2_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range(0x00A0, 0x02FF)
            
        with dpg.font(bold_path, int(size * 1.1)) as h3_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range(0x00A0, 0x02FF)

        if icon_path:
            with dpg.font(icon_path, size) as icon_font:
                dpg.add_font_range(0xE000, 0xF8FF)  # PUA icon range

    if main_font is not None:
        dpg.bind_font(main_font)

    return main_font


def bind_icon_font(item_id: int):
    """Bind the icon font to a specific widget. No-op if icon font not loaded."""
    if icon_font is not None:
        dpg.bind_item_font(item_id, icon_font)