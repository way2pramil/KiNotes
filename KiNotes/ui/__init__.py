# KiNotes - UI Package
"""
KiNotes UI Package - wxPython components for KiCad plugin.

Provides:
- themes: Color themes (Dark/Light) and hex_to_colour conversion
- scaling: DPI scaling utilities for high-DPI displays
- time_tracker: Task time tracking with session history
- components: Custom buttons, icons, and widgets
- main_panel: Main KiNotes panel
"""

# Core modules
from .themes import (
    DARK_THEME, LIGHT_THEME,
    BACKGROUND_COLORS, TEXT_COLORS,
    DARK_BACKGROUND_COLORS, DARK_TEXT_COLORS,
    hex_to_colour
)

from .scaling import (
    get_dpi_scale_factor,
    scale_size,
    scale_font_size,
    get_user_scale_factor,
    set_user_scale_factor,
    UI_SCALE_OPTIONS
)

from .time_tracker import TimeTracker

from .components import (
    RoundedButton,
    PlayPauseButton,
    ToggleSwitch,
    Icons
)

# Main panel (imports the above modules)
from .main_panel import KiNotesMainPanel
from .toolbar import KiNotesToolbar
from .styles import KiNotesStyles
from .bom_dialog import BOMConfigDialog, BOMGenerator, show_bom_dialog
from .markdown_editor import MarkdownEditor

__all__ = [
    # Themes
    'DARK_THEME', 'LIGHT_THEME',
    'BACKGROUND_COLORS', 'TEXT_COLORS',
    'DARK_BACKGROUND_COLORS', 'DARK_TEXT_COLORS',
    'hex_to_colour',
    
    # Scaling
    'get_dpi_scale_factor', 'scale_size', 'scale_font_size',
    'get_user_scale_factor', 'set_user_scale_factor',
    'UI_SCALE_OPTIONS',
    
    # Time Tracking
    'TimeTracker',
    
    # Components
    'RoundedButton', 'PlayPauseButton', 'ToggleSwitch', 'Icons',
    
    # Main UI
    'KiNotesMainPanel', 'KiNotesToolbar', 'KiNotesStyles',
    'BOMConfigDialog', 'BOMGenerator', 'show_bom_dialog',
    
    # Editors
    'MarkdownEditor',
]
