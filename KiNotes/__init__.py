"""
KiNotes - Smart Engineering Notes for KiCad 9+
A PCBtools.xyz Plugin

Features:
- Markdown-based notes with auto-save
- @REF designator linking to highlight PCB components
- Import board metadata (BOM, stackup, netlist, etc.)
- Export notes to PDF
- iOS-inspired modern UI
- Dockable panel or popup window

Target: KiCad 9.0+ (Python 3.9+, wxPython 4.2+)
Website: https://pcbtools.xyz
Repository: https://github.com/way2pramil/KiNotes
License: MIT
"""

__version__ = "1.0.0"
__author__ = "PCBtools.xyz"
__license__ = "MIT"

# Package metadata
__all__ = [
    "KiNotesActionPlugin",
    "KiNotesFrame", 
    "KiNotesDockablePanel",
]

# Import and register the action plugin when loaded by KiCad
try:
    from .kinotes_action import (
        KiNotesActionPlugin,
        KiNotesFrame,
        KiNotesDockablePanel,
    )
except ImportError:
    # Module imports fail outside KiCad (no pcbnew/wx)
    # This is expected during development/testing
    pass
