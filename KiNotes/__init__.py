"""
KiNotes - Smart Engineering Notes for KiCad 9+
A PCBtools.xyz Plugin

Features:
- Dual-Mode Editor: Visual WYSIWYG or Markdown
- @REF designator linking to highlight PCB components
- Import board metadata (BOM, stackup, netlist, etc.)
- Export notes to PDF
- Dark/Light themes with custom colors
- Per-task time tracking
- Git-friendly .kinotes/ folder storage

Target: KiCad 9.0+ (Python 3.9+, wxPython 4.2+)
Website: https://pcbtools.xyz
Repository: https://github.com/way2pramil/KiNotes
License: MIT
"""

# Import version from single source (metadata.json)
try:
    from .__version__ import __version__
except ImportError:
    __version__ = "1.5.0"  # Fallback

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
    
    # Register plugin with KiCad
    # The registration happens automatically at the bottom of kinotes_action.py
    # via: KiNotesActionPlugin().register()
    # This import triggers that registration
    
except ImportError as e:
    # Module imports fail outside KiCad (no pcbnew/wx)
    # This is expected during development/testing
    import sys
    if 'pcbnew' in sys.modules or 'wx' in sys.modules:
        # If inside KiCad but import failed, print error
        print(f"[KiNotes] Import error: {e}")
    pass
