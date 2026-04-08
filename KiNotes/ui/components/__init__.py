"""
KiNotes UI Components - Reusable widgets.

Provides themed buttons, icons, autocomplete, and custom controls.
"""
from .buttons import RoundedButton, PlayPauseButton, ToggleSwitch
from .icons import Icons
try:
    from .autocomplete_popup import SnippetAutocompletePopup
except Exception:
    SnippetAutocompletePopup = None

__all__ = [
    'RoundedButton',
    'PlayPauseButton', 
    'ToggleSwitch',
    'Icons',
    'SnippetAutocompletePopup'
]
