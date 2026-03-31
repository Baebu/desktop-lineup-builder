"""
Module: theme.py
Purpose: Single source of truth for all visual constants.
Dependencies: None
Architecture: Provides default colors and styles. SettingsManager overrides colors at runtime.
"""

import dearpygui.dearpygui as dpg

# ─────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────

# Background layers
APP_BG          = "#000000"   # root window
PANEL_BG        = "#1E293B"   # panels, tabviews, cards in foreground
CARD_BG         = "#090E1A"   # input fields, deep cards

# Borders & hover
BORDER          = "#334155"   # all borders, secondary button backgrounds
HOVER           = "#475569"   # general hover state
SCROLLBAR       = "#475569"   # scrollbar thumb

# Text
TEXT_PRIMARY    = "#CBD5E1"   # main text / values
TEXT_SECONDARY  = "#94A3B8"   # labels / muted
TEXT_MUTED      = "#475569"   # disabled / very muted

# Interactive
ACCENT          = "#818CF8"   # section headers / highlights
PRIMARY         = "#4F46E5"   # main action buttons
PRIMARY_HOVER   = "#4338CA"
DANGER          = "#B91C1C"   # delete / destructive
DANGER_HOVER    = "#DC2626"
SUCCESS         = "#0B6E4F"   # save / confirm
SUCCESS_HOVER   = "#00533C"
ERROR           = "#EF4444"   # validation errors
WHITE           = "#FFFFFF"   # checkmarks, active text on filled buttons
DRAG_HINT       = "#B9B9B9"   # subtle secondary hint text ("drag to add →")
LOAD_BTN        = "#3730A3"   # indigo load-event button
IMPORT_SUCCESS  = "#34D399"   # green preview-success feedback text


# ─────────────────────────────────────────────────────────────────
# Dimensions
# ─────────────────────────────────────────────────────────────────

WIDGET_H        = 20    # standard input / button height
WIDGET_H_SM     = 20    # compact buttons
WIDGET_H_XS     = 20    # tiny buttons (edit popups, pill rows)
WIDGET_H_PILL   = 20    # header action pills

ICON_BTN_W      = 34    # width of square icon-only buttons

CARD_RADIUS     = 12    # rounded corners for cards / slots
PANEL_RADIUS    = 5     # rounded corners for panels, tabviews
BORDER_W        = 1     # standard border width

SCROLL_PAD_X    = 6     # horizontal padding: scroll container ↔ card edge
CARD_PAD_INNER  = 10    # internal card padding (content from card edge)

# ─────────────────────────────────────────────────────────────────
# Standardized UI Style — single source of truth for all DPG sizing
# ─────────────────────────────────────────────────────────────────

class Style:
    """Fixed style constants applied to the global DPG theme.

    All values are in pixels. Nothing here scales with ui_scale —
    font_scale handles perceived size; these stay crisp and tight.
    """

    # Padding inside frames (buttons, inputs, combos)
    FRAME_PAD_X     = 8
    FRAME_PAD_Y     = 4

    # Spacing between consecutive items
    ITEM_SPACING_X  = 8
    ITEM_SPACING_Y  = 1

    # Spacing inside compound widgets (label↔checkbox, etc.)
    INNER_SPACING_X = 6
    INNER_SPACING_Y = 6

    # Padding inside child_windows / popups / panels
    WINDOW_PAD_X    = 8
    WINDOW_PAD_Y    = 8
    
    # Cell padding for tables (gives sections/panels internal breathing room)
    CELL_PAD_X      = 6
    CELL_PAD_Y      = 6

    # Rounding
    FRAME_ROUNDING    = CARD_RADIUS    # inputs, buttons, combos
    CHILD_ROUNDING    = PANEL_RADIUS   # child_window panels
    WINDOW_ROUNDING   = PANEL_RADIUS   # top-level / popup windows
    POPUP_ROUNDING    = CARD_RADIUS
    SCROLLBAR_ROUNDING = CARD_RADIUS
    GRAB_ROUNDING     = CARD_RADIUS
    TAB_ROUNDING      = PANEL_RADIUS

    # Scrollbar & grab
    SCROLLBAR_SIZE  = 12
    GRAB_MIN_SIZE   = 10

    # Borders
    WINDOW_BORDER   = 1
    CHILD_BORDER    = 1
    FRAME_BORDER    = 1

    # Button text alignment (centered)
    BTN_ALIGN_X     = 0.5
    BTN_ALIGN_Y     = 0.5

# ─────────────────────────────────────────────────────────────────
# Dear PyGui helpers
# ─────────────────────────────────────────────────────────────────

def hex_to_dpg(hex_color: str, alpha: int = 255) -> tuple:
    """Convert a CSS hex color string to a DearPyGui (R, G, B, A) tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


# Pre-converted DPG color tuples (used by DPG theme and widget calls)
DPG_APP_BG         = hex_to_dpg(APP_BG)
DPG_PANEL_BG       = hex_to_dpg(PANEL_BG)
DPG_CARD_BG        = hex_to_dpg(CARD_BG)
DPG_BORDER         = hex_to_dpg(BORDER)
DPG_HOVER          = hex_to_dpg(HOVER)
DPG_SCROLLBAR      = hex_to_dpg(SCROLLBAR)
DPG_TEXT_PRIMARY   = hex_to_dpg(TEXT_PRIMARY)
DPG_TEXT_SECONDARY = hex_to_dpg(TEXT_SECONDARY)
DPG_TEXT_MUTED     = hex_to_dpg(TEXT_MUTED)
DPG_ACCENT         = hex_to_dpg(ACCENT)
DPG_PRIMARY        = hex_to_dpg(PRIMARY)
DPG_PRIMARY_HOVER  = hex_to_dpg(PRIMARY_HOVER)
DPG_DANGER         = hex_to_dpg(DANGER)
DPG_DANGER_HOVER   = hex_to_dpg(DANGER_HOVER)
DPG_SUCCESS        = hex_to_dpg(SUCCESS)
DPG_SUCCESS_HOVER  = hex_to_dpg(SUCCESS_HOVER)
DPG_ERROR          = hex_to_dpg(ERROR)
DPG_WHITE          = hex_to_dpg(WHITE)
DPG_DRAG_HINT      = hex_to_dpg(DRAG_HINT)
DPG_LOAD_BTN       = hex_to_dpg(LOAD_BTN)
DPG_IMPORT_SUCCESS = hex_to_dpg(IMPORT_SUCCESS)


# ─────────────────────────────────────────────────────────────────
# Presets & Default Settings
# ─────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    # Fixed Button Colors (Theme independent)
    "primary_color":   "#4F46E5",
    "primary_hover":   "#4338CA",
    "secondary_color": "#334155",
    "secondary_hover": "#475569",
    "success_color":   "#059669",
    "success_hover":   "#047857",
    "danger_color":    "#DC2626",
    "danger_hover":    "#B91C1C",
    "accent_color":    "#818CF8",

    # Structural Colors (Vary by theme)
    "panel_bg":        "#1E293B",
    "card_bg":         "#0F172A",
    "border_color":    "#334155",
    "hover_color":     "#475569",
    "scrollbar_color": "#475569",
    "text_primary":    "#CBD5E1",
    "text_secondary":  "#94A3B8",
    
    # Formatting Dividers
    "time_dj_divider": " | ",
    "genre_divider":   " // ",
    "vol_prefix":      " VOL.",
}

BUILTIN_PRESETS =[
    # ── Cool / Neutral ────────────────────────────────────────────────────
    {
        "name": "Slate (Default)",
        "settings": dict(DEFAULT_SETTINGS),
    },
    {
        "name": "Midnight Blue",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#3B82F6",
            "primary_hover":   "#2563EB",
            "accent_color":    "#93C5FD",
            "panel_bg":        "#0D1526",
            "card_bg":         "#060D1A",
            "border_color":    "#1E3A5F",
            "hover_color":     "#1E3A5F",
            "scrollbar_color": "#1E3A5F",
            "text_primary":    "#E2E8F0",
            "text_secondary":  "#93C5FD",
        },
    },
    {
        "name": "OLED Black",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#6366F1",
            "primary_hover":   "#4F46E5",
            "accent_color":    "#A5B4FC",
            "panel_bg":        "#111111",
            "card_bg":         "#000000",
            "border_color":    "#27272A",
            "hover_color":     "#3F3F46",
            "scrollbar_color": "#27272A",
            "text_primary":    "#F4F4F5",
            "text_secondary":  "#A1A1AA",
        },
    },
    # ── Warm ─────────────────────────────────────────────────────────────
    {
        "name": "Crimson",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#E11D48",
            "primary_hover":   "#BE123C",
            "accent_color":    "#FDA4AF",
            "secondary_color": "#3D1F27",
            "secondary_hover": "#5C2D3A",
            "panel_bg":        "#1A0D11",
            "card_bg":         "#0D0608",
            "border_color":    "#4C1D30",
            "hover_color":     "#5C2D3A",
            "scrollbar_color": "#4C1D30",
            "text_primary":    "#FCE7F3",
            "text_secondary":  "#FDA4AF",
        },
    },
    {
        "name": "Amber",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#D97706",
            "primary_hover":   "#B45309",
            "accent_color":    "#FCD34D",
            "secondary_color": "#2D1F07",
            "secondary_hover": "#3D2C0E",
            "panel_bg":        "#1C1508",
            "card_bg":         "#0E0B04",
            "border_color":    "#44300A",
            "hover_color":     "#5C4114",
            "scrollbar_color": "#44300A",
            "text_primary":    "#FEF3C7",
            "text_secondary":  "#FCD34D",
        },
    },
    # ── Nature / Cool-Green ───────────────────────────────────────────────
    {
        "name": "Forest",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#059669",
            "primary_hover":   "#047857",
            "success_color":   "#D97706",
            "success_hover":   "#B45309",
            "accent_color":    "#6EE7B7",
            "secondary_color": "#0D2B1F",
            "secondary_hover": "#163D2C",
            "panel_bg":        "#0B1F17",
            "card_bg":         "#04100B",
            "border_color":    "#1A4030",
            "hover_color":     "#1E5039",
            "scrollbar_color": "#1A4030",
            "text_primary":    "#D1FAE5",
            "text_secondary":  "#6EE7B7",
        },
    },
    {
        "name": "Ocean",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#0891B2",
            "primary_hover":   "#0E7490",
            "accent_color":    "#67E8F9",
            "secondary_color": "#0C2233",
            "secondary_hover": "#14344D",
            "panel_bg":        "#091D2C",
            "card_bg":         "#040E16",
            "border_color":    "#164E63",
            "hover_color":     "#1A607A",
            "scrollbar_color": "#164E63",
            "text_primary":    "#CFFAFE",
            "text_secondary":  "#67E8F9",
        },
    },
    # ── Purple ────────────────────────────────────────────────────────────
    {
        "name": "Violet",
        "settings": {
            **DEFAULT_SETTINGS,
            "primary_color":   "#7C3AED",
            "primary_hover":   "#6D28D9",
            "accent_color":    "#C4B5FD",
            "secondary_color": "#2D1B5C",
            "secondary_hover": "#3D2475",
            "panel_bg":        "#160D2E",
            "card_bg":         "#09051A",
            "border_color":    "#3B1F6E",
            "hover_color":     "#4C288A",
            "scrollbar_color": "#3B1F6E",
            "text_primary":    "#EDE9FE",
            "text_secondary":  "#C4B5FD",
        },
    },
]