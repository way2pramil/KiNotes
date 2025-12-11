# Net Linker Beta Feature

## Overview
**Net Cross-Probe (Beta)** allows you to highlight PCB nets by name directly from KiNotes, similar to how designator cross-probe works.

Instead of clicking on component references like `R1, C5, U3`, you can now reference and highlight nets like `GND, VCC, SIG_CLK` using the `[[NET:name]]` syntax.

## Architecture

### New Module: `core/net_linker.py` (~160 lines, AI-friendly)

- **Single Purpose**: Net name → highlighting via pcbnew APIs
- **Safe**: All pcbnew calls wrapped in `@safe_pcbnew_call` decorator
- **Two Strategies**:
  1. **Native Highlight** (preferred): Uses `board.HighlightNet(net_code)` when available
  2. **Fallback Selection**: Selects a bounded set of pads/tracks and recenters view on large boards

**Key Methods**:
- `refresh_nets()` - Cache net names → codes and sample pads (call on load or via "Refresh Nets" menu)
- `highlight(net_name)` - Highlight a net by name
- `clear_highlight()` - Clear previous selection/highlight

### Integration Points

#### 1. **Settings Dialog** (`ui/dialogs/settings_dialog.py`)
- Removed duplicate "Editor Mode" section (was shown if `beta_markdown` enabled)
- Consolidated all beta features into one **🧪 Beta Features** section
- Added checkbox: **🔗 Net Cross-Probe (Highlight by net name)**
- Fixed: Markdown editor checkbox now correctly stored/applied in beta section

#### 2. **Main Panel** (`ui/main_panel.py`)
- Imports net linker: `from ..core.net_linker import NetLinker`
- Initializes: `self.net_linker = NetLinker() if HAS_NET_LINKER else None`
- Tracks beta flag: `self._beta_net_linker`
- Loads/saves setting in notes manager
- Refreshes net cache when setting is applied
- Config dict includes `'beta_net_linker'` for settings dialog

#### 3. **Visual Editor Click Handler** (`ui/visual_editor.py`)
- Added `_get_net_at_click_with_pos()` method to detect `[[NET:name]]` patterns at click position
- Added `_try_net_highlight_with_style()` method to highlight and apply styling (blue=found, gray=not found)
- Added `_apply_net_style()` and `_flash_net()` for visual feedback
- Initialized `_net_linker` instance variable in `__init__` and `set_net_linker()` setter
- Modified `_on_click()` to check for net patterns **before** designators (net pattern takes priority)
- On click: Parses net name from `[[NET:name]]` and calls `net_linker.highlight(net_name)`
- Visual feedback: Blue bold text for found nets, gray bold for not found, with flash effect

**Note:** Net cross-probe is **Visual Editor exclusive** (not available in markdown mode) for consistency with the click-first interaction model.

#### 4. **Help Menu** (`_on_help_click` method)
- Added **🔄 Refresh Nets (Beta)** menu item when beta feature is enabled
- User can refresh net cache manually without restart

## Usage

### In Visual Editor (Recommended)

Three syntax options for net highlighting:

**Option 1: Explicit Syntax (Most Safe)**
```markdown
[[NET:VCC]] - Safe, no false positives
[[NET:GND]]
[[NET:CLK_IN]]
```

**Option 2: Short Form (Like Designators)**
```markdown
@VCC - Quick and familiar (like @R1 for designators)
@GND
@CLK_IN
```

**Option 3: Implicit (Shortest - If Net Exists)**
```markdown
VCC - Works directly if VCC is a known net
GND
CLK_IN
```

**Pick whichever feels natural:**
```markdown
# Power Distribution

Main supply: @VCC
Ground: [[NET:GND]]
Clock signal: CLK_IN
Differential: @LVDS_P and @LVDS_N
```

**Interaction:**
- Click anywhere in the net name pattern
- If net exists: Text turns **bold blue**, net highlighted on PCB
- If net not found: Text turns **bold gray**, no highlighting
- Visual effect persists for clarity; click elsewhere to deselect

### In Markdown Mode
Net highlighting is **not available** in markdown mode. Switch to visual editor to use this feature (via Settings → Editor Mode).

### Workflow

1. **Enable Feature** (first time):
   - Open Settings (gear icon in KiNotes window)
   - Scroll to **🧪 Beta Features**
   - Check ✓ **🔗 Net Cross-Probe (Highlight by net name)**
   - Click **Save & Apply** → Restart required
   
2. **Load Project**:
   - KiNotes caches net names from PCB on restart

   
3. **Use in Notes**:
   - Type `[[NET:VCC]]` in Markdown editor
   - Click on the token to highlight that net on PCB
   
4. **Refresh if Design Changes**:
   - If nets were added/removed: Help → **🔄 Refresh Nets (Beta)**
   - Re-caches all nets without restarting

## Implementation Details

### Safe Calls Pattern
```python
@safe_pcbnew_call(default=None)
def _get_board(self):
    return pcbnew.GetBoard()
```
All pcbnew API access is guarded; KiCad crashes are prevented.

### Highlight Strategy Selection
```python
def highlight(self, net_name: str) -> bool:
    # Try native HighlightNet first (fast, clean)
    if hasattr(board, "HighlightNet"):
        board.HighlightNet(code)
        return True
    
    # Fallback: select items on net (compatible, heavier)
    self._select_items_on_net(board, code)
    return True
```

### Bounded Item Selection
When falling back to selection, limits to first 200 items per net to avoid UI slowdown on very large boards.

## Syntax Options

### Standard Format (Recommended)
```
[[NET:VCC]]
[[NET:GND]]
[[NET:CLK_100MHz]]
```

### Notes
- Net names are case-sensitive (depends on KiCad project)
- Supports all valid net name characters: alphanumeric, `_`, `+`, `-`, `.`
- Special characters (like `/`, `:`) in net names use full `[[NET:...]]` syntax
- If net not found, console logs message; click handler safely returns

## Backward Compatibility

- **Designator cross-probe** (`@R1`, `[[CUSTOM_REF]]`) still works unchanged
- **Legacy syntax** `@R1` still supported
- Feature is **beta-gated**: disabled by default, opt-in via Settings

## Future Improvements

1. **Visual Editor Integration**: Parse `[[NET:...]]` tokens in visual editor (currently markdown-only)
2. **Regex Pattern Detection**: Auto-detect net names in notes (similar to designator auto-detection)
3. **Net Info Panel**: Show connected components when highlighting a net
4. **Bidirectional**: Clicking PCB net could insert `[[NET:name]]` at cursor
5. **Differential Pair Support**: Highlight both P and N nets together with `[[DIFF:LVDS]]`

## Testing Checklist

- [ ] Settings dialog shows net linker beta checkbox
- [ ] Checkbox state persists on reopen
- [ ] Restart shows "🔄 Refresh Nets (Beta)" in Help menu
- [ ] Manual refresh works (message confirms)
- [ ] Click `[[NET:VCC]]` in markdown notes highlights the net
- [ ] Console shows no crashes (wrapped calls protect KiCad)
- [ ] Works in both light/dark themes
- [ ] Fallback selection works on large boards

## Known Limitations

- **Markdown mode only** for now (Visual Editor doesn't parse tokens)
- **No net info tooltip** on hover
- **No undo/redo** for highlights (KiCad limitation)
- **Board-specific**: Net names cached per project load

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Net not found" | Check net name spelling/case; use Help → Refresh Nets |
| Highlight not working | Ensure beta feature is enabled in Settings |
| Nothing happens on click | Verify in Markdown mode (not Visual Editor) |
| Performance slow on large board | Fallback selection bounded to 200 items/net |
