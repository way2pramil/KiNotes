"""
KiNotes Theme System - Apple-style Light/Dark themes with color presets.

This module provides:
- DARK_THEME / LIGHT_THEME: Main UI theme dictionaries
- Color presets for editor backgrounds and text
- hex_to_colour() utility for wx.Colour conversion

NOTE: Theme definitions are centralized in core/defaultsConfig.py
      This module re-exports them for backward compatibility.

Usage:
    from .themes import DARK_THEME, LIGHT_THEME, hex_to_colour
    theme = DARK_THEME if dark_mode else LIGHT_THEME
    panel.SetBackgroundColour(hex_to_colour(theme["bg_panel"]))
"""
import wx

# Import from centralized defaults
from ..core.defaultsConfig import THEMES, COLORS

# ============================================================
# RE-EXPORT FROM CENTRALIZED CONFIG (backward compatibility)
# ============================================================
BACKGROUND_COLORS = COLORS['light_backgrounds']
TEXT_COLORS = COLORS['light_text']
DARK_BACKGROUND_COLORS = COLORS['dark_backgrounds']
DARK_TEXT_COLORS = COLORS['dark_text']
DARK_THEME = THEMES['dark']
LIGHT_THEME = THEMES['light']


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
