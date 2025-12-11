"""
KiNotes DPI Scaling Utilities - KiCad-compatible High-DPI support.

This module provides:
- get_dpi_scale_factor(): Get system/user DPI scale
- scale_size(): Scale UI element sizes for DPI
- scale_font_size(): Scale fonts (less aggressive than UI)
- set_user_scale_factor(): Override system DPI

Usage:
    from .scaling import scale_size, scale_font_size, get_dpi_scale_factor
    btn_size = scale_size((120, 44), self)
    font_size = scale_font_size(11, self)
"""
import wx

# Module-level cache
_dpi_scale_factor = None
_user_scale_factor = None  # User-configurable override

# Available scale options for settings UI
UI_SCALE_OPTIONS = {
    "Auto (System)": None,
    "100% (Standard)": 1.0,
    "110%": 1.1,
    "125%": 1.25,
    "150%": 1.5,
    "175%": 1.75,
    "200% (High-DPI)": 2.0,
}


def set_user_scale_factor(factor):
    """Set user-preferred UI scale factor.
    
    Args:
        factor: Scale factor (1.0 = 100%, 1.5 = 150%, etc.) or None for auto
    """
    global _user_scale_factor, _dpi_scale_factor
    _user_scale_factor = factor
    _dpi_scale_factor = None  # Reset cached value to recalculate


def get_user_scale_factor():
    """Get the current user scale factor setting."""
    return _user_scale_factor


def get_dpi_scale_factor(window=None):
    """Get the DPI scale factor for high-DPI displays.
    
    Returns a multiplier:
    - 1.0 = 96 DPI (standard)
    - 1.25 = 120 DPI
    - 1.5 = 144 DPI
    - 2.0 = 192 DPI (Retina)
    
    If user has set a manual scale, that takes priority.
    
    Args:
        window: Optional wx.Window to get DPI from
    
    Returns:
        float: Scale factor multiplier
    """
    global _dpi_scale_factor, _user_scale_factor
    
    # User override takes priority
    if _user_scale_factor is not None:
        return _user_scale_factor
    
    if _dpi_scale_factor is not None:
        return _dpi_scale_factor
    
    try:
        if window:
            # Try to get DPI from window's display
            display = wx.Display(wx.Display.GetFromWindow(window))
            scale = display.GetScaleFactor()
            if scale > 0:
                _dpi_scale_factor = scale
                return _dpi_scale_factor
        
        # Fallback: use screen DPI
        dc = wx.ScreenDC()
        dpi = dc.GetPPI()
        _dpi_scale_factor = dpi[0] / 96.0  # 96 DPI is standard
    except:
        _dpi_scale_factor = 1.0
    
    return _dpi_scale_factor


def scale_size(size, window=None):
    """Scale a size value for DPI.
    
    Args:
        size: Tuple (width, height) or single int
        window: Optional window to get DPI from
    
    Returns:
        Scaled size tuple or int
    """
    factor = get_dpi_scale_factor(window)
    if isinstance(size, tuple):
        return (int(size[0] * factor), int(size[1] * factor))
    return int(size * factor)


def scale_font_size(size, window=None):
    """Scale font size for DPI (slightly less aggressive than UI scaling).
    
    Args:
        size: Base font size in points
        window: Optional window to get DPI from
    
    Returns:
        int: Scaled font size
    """
    factor = get_dpi_scale_factor(window)
    # Font scaling is typically less than UI scaling (70% of delta)
    font_factor = 1.0 + (factor - 1.0) * 0.7
    return int(size * font_factor)
