"""
KiNotes Dialogs Package - Modal dialog windows.

Provides:
- SettingsDialog: Settings configuration dialog
- AboutDialog: About KiNotes information dialog
"""
from .settings_dialog import show_settings_dialog
from .about_dialog import show_about_dialog

__all__ = ['show_settings_dialog', 'show_about_dialog']
