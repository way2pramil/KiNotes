# KiNotes AI Coding Agent Instructions

## Project Overview
KiNotes is a **KiCad 9+ action plugin** (v1.4.2) providing engineering notes inside pcbnew. Built with wxPython 4.2+, it runs in KiCad's embedded Python environment.

**Philosophy**: Notes belong with your PCB project, not in separate files. Smart-Link connects your notes to your design.

## Architecture

### Entry Points
- `kinotes_action.py` - Plugin registration, singleton frame management, `KiNotesFrame` class
- `KiNotesActionPlugin` class registers via `pcbnew.ActionPlugin`

### Core Components (`core/`)
| File | Purpose |
|------|---------|
| `notes_manager.py` | File I/O for `.kinotes/` folder (notes, todos, settings JSON) |
| `designator_linker.py` | Smart-Link: click `R1`, `C5`, `U3` → highlight component on PCB |
| `net_linker.py` | Smart-Link: click `GND`, `VCC`, `SDA` → highlight net on PCB |
| `net_cache_manager.py` | Caches net names from board for fast lookup |
| `metadata_extractor.py` | Extract BOM, stackup, netlist from active board |
| `pdf_exporter.py` | Export notes to PDF |
| `global_settings.py` | User-wide settings (not project-specific) |
| `crash_safety.py` | Error handling and recovery |

### UI Components (`ui/`)
| File | Purpose | Lines |
|------|---------|-------|
| `main_panel.py` | Main coordinator - tabs, theme, imports | ~1605 |
| `themes.py` | Color themes, hex_to_colour utility | ~111 |
| `scaling.py` | DPI scaling utilities | ~123 |
| `time_tracker.py` | TimeTracker class with session history | ~284 |
| `visual_editor.py` | WYSIWYG rich text editor | ~700 |
| `markdown_converter.py` | Bidirectional Markdown ↔ RichText | ~300 |
| `components/buttons.py` | RoundedButton, PlayPauseButton, ToggleSwitch | ~309 |
| `components/icons.py` | Unicode icon constants | ~48 |
| `dialogs/about_dialog.py` | About KiNotes dialog | ~182 |
| `dialogs/settings_dialog.py` | Settings configuration dialog (modular, ScrolledPanel) | ~750 |
| `tabs/todo_tab.py` | Todo list with time tracking (mixin) | ~400 |
| `tabs/bom_tab.py` | Bill of Materials generator (mixin) | ~280 |
| `tabs/version_log_tab.py` | Changelog/version tracking (mixin) | ~260 |

## 🧠 AI-Friendly Architecture Principle

KiNotes follows the **AI-Friendly Architecture** principle: **small, isolated, self-contained modules that AI can fully understand in one context window**.

### Design Rationale
Modern AI agents (like GitHub Copilot) have limited context windows (~200K tokens). Instead of forcing AI to understand a massive monolithic codebase, we deliberately structure code into modules that:
- Fit within a single AI context window
- Have clear, single purposes
- Minimize cross-dependencies
- Self-document through structure

### Before Refactoring (2024)
```
main_panel.py: 4016 lines ❌ Too large for AI to understand holistically
├─ Settings dialog logic
├─ About dialog logic  
├─ Tab implementations (Notes, Todo, BOM, Changelog)
├─ Theme application
├─ Import/export handlers
└─ UI component creation
```

### After Refactoring (Current)
```
main_panel.py: 1605 lines ✅ Coordinator only
├─ themes.py: 111 lines ✅ Color system
├─ scaling.py: 123 lines ✅ DPI utilities
├─ time_tracker.py: 284 lines ✅ Session tracking
├─ components/
│  ├─ buttons.py: 309 lines ✅ UI widgets
│  └─ icons.py: 48 lines ✅ Icon constants
├─ dialogs/
│  ├─ about_dialog.py: 170 lines ✅ About window
│  └─ settings_dialog.py: 625 lines ✅ Settings window
└─ tabs/
   ├─ todo_tab.py: 400 lines ✅ Todo mixin
   ├─ bom_tab.py: 280 lines ✅ BOM mixin
   └─ version_log_tab.py: 260 lines ✅ Changelog mixin
```

## 🏗️ Project Structure

```
KiNotes/
├── kinotes_action.py        # Plugin entry point
├── metadata.json            # KiCad PCM metadata
├── core/
│   ├── notes_manager.py     # File I/O for .kinotes/
│   ├── designator_linker.py # Smart-link: click → highlight component
│   ├── net_linker.py        # Smart-link: click → highlight net
│   ├── metadata_extractor.py# BOM, stackup extraction
│   └── pdf_exporter.py      # PDF export
├── ui/
│   ├── main_panel.py        # Main coordinator
│   ├── visual_editor.py     # Rich text editor
│   ├── themes.py            # Dark/Light color schemes
│   ├── dialogs/             # Settings, About
│   ├── tabs/                # Todo, BOM, Changelog
│   └── components/          # Buttons, icons
└── resources/
    └── icon.png             # Toolbar icon
```
### Architecture Benefits

**✅ AI-Friendly**
- Each module < 1000 lines fits in context windows
- Clear file organization enables quick navigation
- Single-purpose modules are self-explanatory

**✅ Maintainable**
- Changes localized to specific modules
- Easier debugging and testing
- Reduced cognitive load when making edits

**✅ Testable**
- Can test individual components in isolation
- Mixin pattern enables unit testing

**✅ Extensible**
- Easy to add new tabs (inherit from mixin pattern)
- Easy to add new dialogs or components
- Minimal ripple effects from changes

### Mixin Pattern for Tabs
Tabs are implemented as mixin classes that inherit into `KiNotesMainPanel`:
```python
class KiNotesMainPanel(TodoTabMixin, VersionLogTabMixin, BomTabMixin, wx.Panel):
    """Coordinator inherits tab functionality via mixins"""
```

Each mixin (`TodoTabMixin`, `BomTabMixin`, etc.) is self-contained in its own module and provides:
- `_create_<tab>_tab()` - Tab UI initialization
- Related event handlers
- Minimal state dependencies on main panel

## Key Patterns

### Theme System
Two theme dicts in `main_panel.py`: `DARK_THEME` and `LIGHT_THEME`
```python
# Theme keys (use these, NOT arbitrary keys):
"bg_panel", "bg_toolbar", "bg_button", "bg_button_hover", "bg_editor"
"text_primary", "text_secondary", "border"
"accent_blue", "accent_green", "accent_red"
```
**Always use `hex_to_colour()` to convert hex strings to `wx.Colour`**

### DPI Scaling
All sizes must use `scale_size()` or `scale_font_size()` for high-DPI support:
```python
scaled_size = scale_size((width, height), self)  # Returns tuple
btn.SetMinSize(scaled_size)
```

### Custom Buttons
Use `RoundedButton` class (not `wx.Button`) for themed buttons:
```python
btn = RoundedButton(parent, label="Save", size=(130, 48), 
                    bg_color=self._theme["accent_green"], fg_color="#FFFFFF")
btn.Bind_Click(lambda e: self._on_save())
```

### Visual Editor Theme Updates
When changing colors, must update **existing text** (not just default style):
```python
# In visual_editor.py _apply_visual_theme():
self._editor.SetStyleEx(rt.RichTextRange(0, text_length), color_attr, 
                        rt.RICHTEXT_SETSTYLE_WITH_UNDO)
```

### Cross-Probe (Smart Designator & Net Linking)

**Designators (Visual Editor + Markdown Mode):**
Click on designators like `R1`, `C12`, `U3` to highlight component on PCB:
```python
# Supported prefixes in designator_linker.py:
DESIGNATOR_PREFIXES = ['R', 'C', 'L', 'D', 'U', 'Q', 'J', 'P', 'K', 'SW', 
                       'LED', 'IC', 'CON', 'TP', 'FB', ...]

# Smart pattern matches: R1, R12A, LED5, SW10, etc.
# Explicit syntax for edge cases: [[CUSTOM_REF]]
# Legacy @R1 syntax still supported for backward compatibility
```

**Net Highlighting (Visual Editor Only, Beta):**
Click on net names using any of these syntaxes to highlight nets on PCB (requires beta feature enabled):
```python
# In visual_editor.py click handler:
# Syntax options:
#   [[NET:VCC]]   - Explicit (no false positives)
#   @VCC          - Short form (like designators @R1)
#   VCC           - Implicit (if VCC is a known net)

# Result: Blue bold = found, Gray bold = not found
# Visual feedback: Click anywhere in pattern to highlight

# Implementation in core/net_linker.py:
# - refresh_nets() caches net names → codes from board
# - is_valid_net(name) checks if net exists in cache
# - highlight(net_name) highlights via pcbnew.HighlightNet() or fallback selection
# - safe_pcbnew_call decorator wraps all board operations
```

### Settings Persistence
Settings saved via `notes_manager.save_settings(dict)` to `.kinotes/settings.json`
Key settings: `dark_mode`, `use_visual_editor`, `crossprobe_enabled`, `net_crossprobe_enabled`, `beta_net_linker`, `panel_width`, `panel_height`, `beta_debug_panel`

## Unicode Icon Rules

**IMPORTANT**: KiCad's embedded wxPython has limited Unicode emoji support. Only use icons that render correctly:

### ✅ Working Icons (use these)
- Section headers: 🔗 ⏱ 🔍 📐 🧪 💾 🌐 ⚙ ℹ️ ❓ 🤝 💝 🐛 🔧
- Simple Unicode symbols: ↻ ↺ ⟳ → ← ↑ ↓ ✓ ✕ • ─

### ❌ Broken Icons (avoid - show as square blocks)
- 🔄 (refresh arrows) - use ↻ instead
- Other newer Unicode 6.0+ emojis may not render

### Rule
When adding icons to buttons or menus, test in KiCad first. If it shows as a square block, replace with a simpler Unicode symbol or text.

## Testing Without KiCad
The `pcbnew` module only exists inside KiCad. For standalone testing:
- Mock `pcbnew` imports or use `try/except ImportError`
- Test UI with `python debug_standalone.py` (creates wx.App without pcbnew)

## Common Gotchas

1. **Module reloading**: KiCad caches Python modules. `kinotes_action.py` has `_force_reload_modules()` to reload UI modules during development.

2. **Singleton frame**: Only one KiNotes window allowed. `get_kinotes_frame()` returns existing frame or None.

3. **pcbnew import errors**: Expected in IDE - only resolves at runtime inside KiCad.

4. **Settings dialog crashes**: Often caused by missing theme keys. Always verify keys exist in `DARK_THEME`/`LIGHT_THEME` dicts.

5. **Sizer flags**: Don't combine `wx.EXPAND` with `wx.ALIGN_CENTER_VERTICAL` in box sizers.

## File Locations
- Notes: `<project>/.kinotes/KiNotes_<project>.md`
- Todos: `<project>/.kinotes/todos.json`  
- Settings: `<project>/.kinotes/settings.json`
- Icons: `KiNotes/resources/icon.png` (24x24), `KiNotes/resources/icons/icon.png` (64x64)

## Documentation Rules

**IMPORTANT**: Never mention AI, AI-generated, AI-friendly, or similar terms in user-facing documentation (README.md, About dialog, comments visible to end users). 

- ❌ "AI-friendly architecture"
- ❌ "Built with AI assistance"
- ❌ "Context window optimized"
- ✅ "Modular architecture"
- ✅ "Small, focused files"
- ✅ "Easy to understand"

This file (.github/copilot-instructions.md) is for developers/AI agents only and can reference AI concepts.
