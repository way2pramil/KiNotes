# KiNotes Default Settings Reference

This document lists all default settings and content for KiNotes when freshly installed.

---

## Default Settings (settings.json)

```json
{
    "autosave_interval": 5,
    "font_size": 11,
    "bom_exclude_dnp": true,
    "bom_exclude_fid": true,
    "bom_exclude_tp": true,
    "bom_group": 0,
    "sort_order": ["C", "R", "L", "D", "U", "Y", "X", "F", "SW", "A", "J", "TP"],
    "blacklist": "",
    "blacklist_virtual": true,
    "blacklist_empty": false,
    "background_color": "Snow Gray",
    "text_color": "Carbon Black"
}
```

---

## UI/Feature Settings (from main_panel.py)

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `use_visual_editor` | `true` | WYSIWYG editor (if available) |
| `crossprobe_enabled` | `true` | Designator cross-probe (R1, C5 → highlight) |
| `net_crossprobe_enabled` | `true` | Net cross-probe (GND, VCC → highlight) |
| `beta_features_enabled` | `false` | Beta features toggle |
| `beta_net_linker` | `true` | Net cross-probe linker (beta) |
| `beta_debug_panel` | `false` | Debug panel (never default on) |

---

## Time Tracker Settings

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `enable_time_tracking` | `true` | Enable per-task time tracking |
| `time_format_24h` | `true` | 24-hour format (vs 12-hour) |
| `show_work_diary_button` | `true` | Show Work Diary button |

---

## Default Notes Template (Fresh Project)

When opening a new project, KiNotes creates a notes file with this template:

```markdown
# {ProjectName} - Design Notes

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
```

---

## Default Tasks/Todo (Fresh Project)

Empty list: `[]`

No default tasks are created. Users add tasks manually.

---

## Default Version Log (Fresh Project)

```json
{
    "current_version": "0.1.0",
    "entries": []
}
```

---

## Theme Defaults

### Dark Theme (Apple-style)
```python
DARK_THEME = {
    "bg_panel":         "#1C1C1E",   # Apple System Gray 6 (Dark)
    "bg_toolbar":       "#2C2C2E",   # Apple System Gray 5 (Dark)
    "bg_button":        "#3A3A3C",   # Apple System Gray 4 (Dark)
    "bg_button_hover":  "#48484A",
    "bg_editor":        "#1C1C1E",   # Matches panel for seamless look
    "text_primary":     "#FFFFFF",   # Pure White
    "text_secondary":   "#98989D",   # Apple System Gray (Text)
    "border":           "#38383A",   # Subtle separators
    "accent_blue":      "#5A9BD5",   # Muted professional blue
    "accent_green":     "#6AAF6A",   # Muted professional green
    "accent_red":       "#FF453A",   # iOS Red (Dark Mode)
}
```

### Light Theme (Apple-style)
```python
LIGHT_THEME = {
    "bg_panel":         "#F2F2F7",   # Apple System Gray 6 (Light)
    "bg_toolbar":       "#FFFFFF",   # Pure white cards
    "bg_button":        "#E5E5EA",   # Apple System Gray 3 (Light)
    "bg_button_hover":  "#D1D1D6",
    "bg_editor":        "#FFFFFF",
    "text_primary":     "#000000",
    "text_secondary":   "#8E8E93",
    "border":           "#C6C6C8",
    "accent_blue":      "#3B82F6",   # Muted professional blue
    "accent_green":     "#5BBD5B",   # Muted professional green
    "accent_red":       "#FF3B30",   # iOS Red (Light Mode)
}
```

---

## Editor Color Presets

### Light Mode - Background Colors
| Name | Hex |
|------|-----|
| Snow Gray | `#F8F9FA` |
| Ivory Paper | `#FFFDF5` |
| Mint Mist | `#EAF7F1` |
| Sakura Mist | `#FAF1F4` |
| Storm Fog | `#E4E7EB` |

### Light Mode - Text Colors
| Name | Hex |
|------|-----|
| Carbon Black | `#2B2B2B` |
| Deep Ink | `#1A1A1A` |
| Slate Night | `#36454F` |
| Cocoa Brown | `#4E342E` |
| Evergreen Ink | `#004D40` |

### Dark Mode - Background Colors
| Name | Hex |
|------|-----|
| Charcoal | `#1C1C1E` |
| Obsidian | `#0D0D0D` |
| Midnight | `#121212` |
| Slate Dark | `#1E1E2E` |
| Deep Space | `#0F0F1A` |

### Dark Mode - Text Colors
| Name | Hex |
|------|-----|
| Pure White | `#FFFFFF` |
| Soft White | `#E5E5E5` |
| Silver | `#C0C0C0` |
| Light Gray | `#A0A0A0` |
| Neon Blue | `#00D4FF` |

---

## Designator Prefixes (Cross-Probe)

### Built-in Prefixes (IEEE 315 / Industry Standard)
```
R, C, L, D, U, Q, J, P, K          # Basic components
SW, S, F, FB, TP, Y, X, T, M       # Switches, fuses, test points
LED, IC, CON, RLY, XTAL, ANT, BT   # Common multi-letter
VR, RV, TR, FID, MH, JP, LS, SP, MIC  # Variable, fiducials, jumpers
```

### Default Custom Prefixes
Empty - users can add custom prefixes like: `MOV, PC, NTC, PTC`

---

## Visual Editor Font Sizes

| Element | Default Size (points) |
|---------|----------------------|
| Normal text | 11 |
| Heading 1 (H1) | 22 |
| Heading 2 (H2) | 18 |
| Heading 3 (H3) | 14 |
| Code | 10 |

---

## Window Sizing

### Main Panel
- Minimum: 800 × 600 px
- Default position: Right side of screen

### Settings Dialog
- Minimum: 450 × 400 px (DPI-scaled)
- Preferred: 650 × 750 px (or 70% of screen)
- Maximum: 650 × 750 px (capped)

---

## File Locations

| File | Location |
|------|----------|
| Notes | `<project>/.kinotes/KiNotes_<project>.md` |
| Todos | `<project>/.kinotes/todos.json` |
| Settings | `<project>/.kinotes/settings.json` |
| Version Log | `<project>/.kinotes/version_log.json` |
| Work Diary | `<project>/.kinotes/<project>_worklog_YYYYMMDD.md` |
| Backups | `<project>/.kinotes/backups/` |

---

## Settings Cascade

Settings are loaded in this priority order:
1. **Local settings** (`<project>/.kinotes/settings.json`) - Project-specific
2. **Global settings** (`~/.kinotes/global_settings.json`) - User-wide defaults
3. **Hardcoded defaults** - Built-in fallback values

---

*Generated for KiNotes v1.4.2 - PCBtools.xyz*
