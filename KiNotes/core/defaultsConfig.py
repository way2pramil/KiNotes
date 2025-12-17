"""
KiNotes Defaults Configuration - Single Source of Truth
========================================================
ALL default values for KiNotes are defined here.
DO NOT hardcode defaults in other files - import from this module.

This ensures:
- Consistency across the codebase
- Easy maintenance and updates
- Clear documentation of all configurable values
- No duplicate/conflicting default values

Usage:
    from core.defaultsConfig import DEFAULTS, THEMES, COLORS, PREFIXES
    
    # Access settings defaults
    font_size = DEFAULTS['font_size']
    
    # Access theme colors
    dark_theme = THEMES['dark']
    
    # Access color presets
    bg_colors = COLORS['light_backgrounds']

Author: KiNotes Team (pcbtools.xyz)
License: MIT
"""

# ============================================================
# SETTINGS DEFAULTS - Core application settings
# ============================================================
DEFAULTS = {
    # General
    'autosave_interval': 5,          # seconds (min: 3, max: 60)
    'font_size': 11,                 # points (8-24)
    'pdf_format': 'markdown',        # 'markdown' or 'visual'
    'ui_scale_factor': 1.25,         # UI scale (1.25 = 125%, most stable)
    
    # Theme
    'dark_mode': False,
    'bg_color_name': 'Ivory Paper',
    'text_color_name': 'Carbon Black',
    'dark_bg_color_name': 'Charcoal',
    'dark_text_color_name': 'Pure White',
    
    # Features
    'use_visual_editor': True,       # WYSIWYG editor
    'crossprobe_enabled': True,      # Designator cross-probe
    'net_crossprobe_enabled': True,  # Net cross-probe
    
    # BOM Settings
    'bom_exclude_dnp': True,
    'bom_exclude_fid': True,
    'bom_exclude_tp': True,
    'bom_group': 0,
    'sort_order': ['C', 'R', 'L', 'D', 'U', 'Y', 'X', 'F', 'SW', 'A', 'J', 'TP'],
    'blacklist': '',
    'blacklist_virtual': True,
    'blacklist_empty': False,
    
    # Version Log
    'current_version': '0.1.0',
}

# ============================================================
# PERFORMANCE SETTINGS
# ============================================================
PERFORMANCE_DEFAULTS = {
    'timer_interval_ms': 5000,       # Auto-save timer interval (ms) - min: 3000
    'timer_min_ms': 3000,            # Minimum allowed interval
    'timer_max_ms': 60000,           # Maximum allowed interval
    'timer_display_divisor': 1,      # Update timer display every N ticks
}

# ============================================================
# DEBUG SETTINGS - Console output control
# ============================================================
DEBUG_ENABLED = False  # Master debug flag - set True for development only
DEPLOY_BUILD = 33      # Incremented by deploy script - verifies fresh deployment

def debug_print(msg: str) -> None:
    """Print debug message only if DEBUG_ENABLED is True."""
    if DEBUG_ENABLED:
        print(msg)

# ============================================================
# BETA FEATURES - Experimental features (disabled by default)
# ============================================================
BETA_DEFAULTS = {
    'beta_features_enabled': False,  # Master toggle
    'beta_markdown': False,          # Markdown editor mode
    'beta_bom': False,               # BOM tab
    'beta_version_log': False,       # Version Log tab
    'beta_net_linker': True,         # Net cross-probe (exception: enabled)
    'beta_debug_panel': False,       # Debug panel (never default on)
}

# ============================================================
# TIME TRACKER DEFAULTS
# ============================================================
TIME_TRACKER_DEFAULTS = {
    'enable_time_tracking': True,
    'time_format_24h': True,
    'show_work_diary_button': True,
}

# ============================================================
# WINDOW SIZING DEFAULTS
# ============================================================
WINDOW_DEFAULTS = {
    # Main panel
    'panel_width': 1000,
    'panel_height': 800,
    'min_width': 800,
    'min_height': 600,
    
    # Settings dialog
    'settings_min_width': 450,
    'settings_min_height': 400,
    'settings_preferred_width': 650,
    'settings_preferred_height': 750,
    
    # Debug panel
    'debug_sash_pos': 240,
}

# ============================================================
# FONT SIZE DEFAULTS (points)
# ============================================================
FONT_DEFAULTS = {
    'normal': 11,
    'h1': 22,
    'h2': 18,
    'h3': 14,
    'code': 10,
    'min': 8,
    'max': 24,
}

# ============================================================
# EDITOR LAYOUT DEFAULTS (pixels, DPI-scaled at runtime)
# Industry standard: 12-16px horizontal, 8px vertical for compact tools
# ============================================================
EDITOR_LAYOUT = {
    # Internal margins (inside editor control)
    'margin_left': 12,       # Left padding from text edge
    'margin_right': 8,       # Right padding from text edge
    
    # External padding (sizer padding around editor)
    'padding_horizontal': 4,  # Left/right gap between editor and panel
    'padding_bottom': 4,      # Bottom gap
}

# ============================================================
# IMAGE HANDLING DEFAULTS
# ============================================================
IMAGE_DEFAULTS = {
    'folder_name': 'images',           # Subfolder in .kinotes/
    'max_size_kb': 2048,               # Max image size (2MB)
    'max_dimension': 1920,             # Max width/height (resize if larger)
    'thumbnail_size': 400,             # Display size in editor
    'supported_formats': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
    'default_format': 'png',           # Save format for clipboard images
    'quality': 85,                     # JPEG quality (1-100)
}

# ============================================================
# DESIGNATOR PREFIXES (IEEE 315 / Industry Standard)
# ============================================================
DESIGNATOR_PREFIXES = [
    # Basic components
    'R', 'C', 'L', 'D', 'U', 'Q', 'J', 'P', 'K',
    # Switches, fuses, test points, crystals
    'SW', 'S', 'F', 'FB', 'TP', 'Y', 'X', 'T', 'M',
    # Common multi-letter prefixes
    'LED', 'IC', 'CON', 'RLY', 'XTAL', 'ANT', 'BT',
    # Variable, fiducials, jumpers, speakers
    'VR', 'RV', 'TR', 'FID', 'MH', 'JP', 'LS', 'SP', 'MIC',
]

# ============================================================
# VISUAL EDITOR MARKERS
# ============================================================
EDITOR_MARKERS = {
    'bullet_chars': ['•', '◦', '▪'],
    'checkbox_unchecked': '☐',
    'checkbox_checked': '☑',
    'divider_char': '─',
    'divider_length': 40,
}

# ============================================================
# COLOR THEMES - Apple-style UI
# ============================================================
THEMES = {
    'dark': {
        'bg_panel':         '#1C1C1E',   # Apple System Gray 6 (Dark)
        'bg_toolbar':       '#2C2C2E',   # Apple System Gray 5 (Dark)
        'bg_button':        '#3A3A3C',   # Apple System Gray 4 (Dark)
        'bg_button_hover':  '#48484A',
        'bg_editor':        '#1C1C1E',   # Matches panel
        'text_primary':     '#FFFFFF',   # Pure White
        'text_secondary':   '#98989D',   # Apple System Gray (Text)
        'border':           '#38383A',   # Subtle separators
        'accent_blue':      '#5A9BD5',   # Muted professional blue
        'accent_green':     '#6AAF6A',   # Muted professional green
        'accent_red':       '#FF453A',   # iOS Red (Dark Mode)
    },
    'light': {
        'bg_panel':         '#F2F2F7',   # Apple System Gray 6 (Light)
        'bg_toolbar':       '#FFFFFF',   # Pure white cards
        'bg_button':        '#E5E5EA',   # Apple System Gray 3 (Light)
        'bg_button_hover':  '#D1D1D6',
        'bg_editor':        '#FFFFFF',
        'text_primary':     '#000000',
        'text_secondary':   '#8E8E93',
        'border':           '#C6C6C8',
        'accent_blue':      '#3B82F6',   # Muted professional blue
        'accent_green':     '#10B981',   # Muted professional green
        'accent_red':       '#FF3B30',   # iOS Red
    },
}

# ============================================================
# EDITOR COLOR PRESETS
# ============================================================
COLORS = {
    # Light mode backgrounds
    'light_backgrounds': {
        'Snow Gray':    '#F8F9FA',
        'Ivory Paper':  '#FFFDF5',
        'Mint Mist':    '#EAF7F1',
        'Sakura Mist':  '#FAF1F4',
        'Storm Fog':    '#E4E7EB',
    },
    # Light mode text
    'light_text': {
        'Carbon Black':   '#2B2B2B',
        'Deep Ink':       '#1A1A1A',
        'Slate Night':    '#36454F',
        'Cocoa Brown':    '#4E342E',
        'Evergreen Ink':  '#004D40',
    },
    # Dark mode backgrounds
    'dark_backgrounds': {
        'Charcoal':    '#1C1C1E',
        'Obsidian':    '#0D0D0D',
        'Midnight':    '#121212',
        'Slate Dark':  '#1E1E2E',
        'Deep Space':  '#0F0F1A',
    },
    # Dark mode text
    'dark_text': {
        'Pure White':  '#FFFFFF',
        'Soft White':  '#E5E5E5',
        'Silver':      '#C0C0C0',
        'Light Gray':  '#A0A0A0',
        'Neon Blue':   '#00D4FF',
    },
    # Link colors
    'link_dark':  '#61AFEF',   # Light blue for dark mode
    'link_light': '#0066CC',   # Standard link blue for light mode
}

# ============================================================
# NOTES TEMPLATE - Default content for new projects
# ============================================================
NOTES_TEMPLATE = """# {project_name} - Design Notes

## Overview
<!-- Brief description of the PCB project -->

## Schematic Notes
<!-- Key circuit blocks, design rationale -->

## Layout Considerations
<!-- Layer stackup, impedance, keep-outs -->

## Component Notes
<!-- Click on designators like R1, C5, U3 to highlight on PCB -->

## Power Distribution
<!-- Power rails, decoupling strategy -->

## Signal Integrity
<!-- Critical nets, routing constraints -->

## References
<!-- Datasheets, application notes, calculations -->

---
*KiNotes - PCBtools.xyz*
"""

# ============================================================
# VERSION LOG TEMPLATE - Default structure for new projects
# ============================================================
VERSION_LOG_TEMPLATE = {
    'current_version': '0.1.0',
    'entries': []
}

# ============================================================
# DEBUG MODULES - Default states
# ============================================================
# Set True to enable debug output for specific modules
# This allows focused debugging without console spam
DEBUG_MODULES = {
    # Core modules
    'image': True,       # Image handler - paste, save, load
    'pdf': True,         # PDF export
    'md_export': True,   # Markdown export (RichText → MD)
    'md_import': True,   # Markdown import (MD → RichText)
    
    # UI modules
    'save': False,       # Save operations
    'click': False,      # Click events
    'size': False,       # Window sizing
    'editor': False,     # Visual editor operations
    
    # Crossprobe
    'net': False,        # Net linker
    'designator': False, # Designator linker
}


def debug_module(module: str, msg: str) -> None:
    """
    Print debug message only if module is enabled.
    
    Usage:
        debug_module('image', f"Saved: {filename}")
        debug_module('pdf', f"Exporting to: {path}")
    
    Args:
        module: Module key from DEBUG_MODULES
        msg: Message to print (without [KiNotes] prefix)
    """
    if DEBUG_ENABLED and DEBUG_MODULES.get(module, False):
        prefix = module.upper()
        print(f"[KiNotes {prefix}] {msg}")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_theme(dark_mode: bool = False) -> dict:
    """Get theme dictionary for dark or light mode."""
    return THEMES['dark'] if dark_mode else THEMES['light']


def get_default_settings() -> dict:
    """Get complete default settings dict for notes_manager."""
    return {
        'autosave_interval': DEFAULTS['autosave_interval'],
        'font_size': DEFAULTS['font_size'],
        'bom_exclude_dnp': DEFAULTS['bom_exclude_dnp'],
        'bom_exclude_fid': DEFAULTS['bom_exclude_fid'],
        'bom_exclude_tp': DEFAULTS['bom_exclude_tp'],
        'bom_group': DEFAULTS['bom_group'],
        'sort_order': DEFAULTS['sort_order'].copy(),
        'blacklist': DEFAULTS['blacklist'],
        'blacklist_virtual': DEFAULTS['blacklist_virtual'],
        'blacklist_empty': DEFAULTS['blacklist_empty'],
        'background_color': DEFAULTS['bg_color_name'],
        'text_color': DEFAULTS['text_color_name'],
    }


def get_notes_template(project_name: str) -> str:
    """Get default notes template with project name."""
    return NOTES_TEMPLATE.format(project_name=project_name)


def get_version_log_template() -> dict:
    """Get default version log structure."""
    return VERSION_LOG_TEMPLATE.copy()


























