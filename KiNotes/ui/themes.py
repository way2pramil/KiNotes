"""
KiNotes Theme System - Apple-style Light/Dark themes with color presets.

This module provides:
- DARK_THEME / LIGHT_THEME: Main UI theme dictionaries
- Color presets for editor backgrounds and text
- hex_to_colour() utility for wx.Colour conversion

Usage:
    from .themes import DARK_THEME, LIGHT_THEME, hex_to_colour
    theme = DARK_THEME if dark_mode else LIGHT_THEME
    panel.SetBackgroundColour(hex_to_colour(theme["bg_panel"]))
"""
import wx

# ============================================================
# COLOR PRESETS - Light Mode Editor Colors
# ============================================================
BACKGROUND_COLORS = {
    "Snow Gray": "#F8F9FA",
    "Ivory Paper": "#FFFDF5",
    "Mint Mist": "#EAF7F1",
    "Sakura Mist": "#FAF1F4",
    "Storm Fog": "#E4E7EB",
}

TEXT_COLORS = {
    "Carbon Black": "#2B2B2B",
    "Deep Ink": "#1A1A1A",
    "Slate Night": "#36454F",
    "Cocoa Brown": "#4E342E",
    "Evergreen Ink": "#004D40",
}

# ============================================================
# DARK MODE - Editor Colors (Blender-style)
# ============================================================
DARK_BACKGROUND_COLORS = {
    "Charcoal": "#1C1C1E",
    "Obsidian": "#0D0D0D",
    "Midnight": "#121212",
    "Slate Dark": "#1E1E2E",
    "Deep Space": "#0F0F1A",
}

DARK_TEXT_COLORS = {
    "Pure White": "#FFFFFF",
    "Soft White": "#E5E5E5",
    "Silver": "#C0C0C0",
    "Light Gray": "#A0A0A0",
    "Neon Blue": "#00D4FF",
}

# ============================================================
# APPLE-STYLE UI THEMES
# ============================================================
DARK_THEME = {
    "bg_panel":     "#1C1C1E",      # Apple System Gray 6 (Dark)
    "bg_toolbar":   "#2C2C2E",      # Apple System Gray 5 (Dark)
    "bg_button":    "#3A3A3C",      # Apple System Gray 4 (Dark)
    "bg_button_hover": "#48484A",
    "bg_editor":    "#1C1C1E",      # Matches panel for seamless look
    "text_primary": "#FFFFFF",      # Pure White
    "text_secondary": "#98989D",    # Apple System Gray (Text)
    "border":       "#38383A",      # Subtle separators
    "accent_blue":  "#5A9BD5",      # Muted professional blue
    "accent_green": "#6AAF6A",      # Muted professional green
    "accent_red":   "#FF453A",      # iOS Red (Dark Mode)
}

LIGHT_THEME = {
    "bg_panel":     "#F2F2F7",      # Apple System Gray 6 (Light)
    "bg_toolbar":   "#FFFFFF",      # Pure white cards
    "bg_button":    "#E5E5EA",      # Apple System Gray 3 (Light)
    "bg_button_hover": "#D1D1D6",
    "bg_editor":    "#FFFFFF",
    "text_primary": "#000000",
    "text_secondary": "#8E8E93",
    "border":       "#C6C6C8",
    "accent_blue":  "#3B82F6",      # Muted professional blue
    "accent_green": "#10B981",      # #10B981 Muted professional green
    "accent_red":   "#FF3B30",      # iOS Red
}


def hex_to_colour(hex_str):
    """Convert hex color string to wx.Colour.
    
    Args:
        hex_str: Hex color like "#FFFFFF" or "FFFFFF"
    
    Returns:
        wx.Colour object
    """
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return wx.Colour(r, g, b)


def get_theme(dark_mode=False):
    """Get the appropriate theme dictionary.
    
    Args:
        dark_mode: True for dark theme, False for light
    
    Returns:
        Theme dictionary with color keys
    """
    return DARK_THEME if dark_mode else LIGHT_THEME
