# KiNotes — Smart Engineering Notes for KiCad 9+

<p align="center">
  <img src="KiNotes/resources/icon.png" alt="KiNotes" width="64"/>
</p>

**KiNotes** brings real engineering notes **directly inside KiCad pcbnew** — with zero friction.  
Write design decisions, link components with `@R1` syntax, import board metadata, and export beautiful PDFs.

> 🎯 **Target:** KiCad 9.0+ only — built for modern KiCad with Python 3 and wxPython 4.

---

## ✨ Features

### 📝 Dual-Mode Notes Editor
- **Visual Editor (WYSIWYG)** — Notion-like rich text editing with toolbar
  - Bold, Italic, Underline, Strikethrough formatting
  - Headings (H1, H2, H3)
  - Bullet lists, numbered lists, checkboxes
  - Insert tables, images, links, dividers, timestamps
  - Keyboard shortcuts (Ctrl+B, Ctrl+I, etc.)
- **Markdown Editor** — Power user mode with raw markdown
  - Live preview formatting
  - `- [ ]` / `- [x]` checkboxes with strikethrough
- **Auto-link designators** — type `@R1`, `@U3`, `@C5` → highlights component on PCB
- **Auto-save** on every change, close, or outside click
- **Git-friendly** `.kinotes/` folder in project directory

### 🎨 Modern UI & Theming
- **Dark/Light mode** toggle with custom color schemes
- **iOS-inspired** clean, minimal interface
- **User-selectable colors** — 5 background + 5 text color presets per theme
- **Dockable panel** — dock left/right like Properties panel, or use popup
- **Icon-based toolbar** — intuitive buttons

### 🔗 PCB Integration (KiCad 9+)
- **Import Board Metadata** with one-click dropdown:
  - **BOM (Interactive)** — IBOM-style dialog with column selection, grouping, and filtering
  - BOM (Quick Insert)
  - Stackup configuration
  - Board size & parameters
  - Differential pairs
  - Netlist summary
  - Layer information
  - Drill table
  - Design rules
- **Click `@REF`** → jump to and highlight component in pcbnew
- **Component metadata preview** — value, footprint, layer, nets

> **Note:** Table-based imports (BOM, Layers, Stackup, Drill Table) currently require Markdown mode

### 📋 IBOM-Style BOM Generator
- **Column Selection** — Reference, Value, Footprint, Qty, Description, Manufacturer, MPN, Supplier, SPN, Layer, Position, Rotation, DNP
- **Grouping Options** — By Value+Footprint, Value only, Footprint only, or No grouping
- **Sort Options** — By Reference, Value, Footprint, or Quantity
- **Filters** — Exclude DNP, Fiducials, Test Points
- **Output Formats** — Markdown Table, Simple List, CSV-style

### 📤 Export
- **Export to PDF** with PCB project name as filename
- **Export to Markdown** for documentation
- **Print-ready** formatting

### 🎨 Modern UI
- **iOS-inspired** clean, minimal interface
- **Follows KiCad UI** patterns for natural integration
- **Dockable panel** — dock left/right like Properties panel, or use popup
- **Icon-based toolbar** — intuitive buttons
- **Dark/Light mode** — with customizable color schemes
- **PCBtools.xyz branding** in footer
- **Time tracking** — per-task stopwatch with work diary export

---

## 📸 Screenshots

*(Coming soon)*

---

## 🚀 Quick Start

### Installation

**Option 1: KiCad Plugin Manager** *(Recommended)*
1. KiCad → **Tools → Plugin and Content Manager**
2. Search **KiNotes**
3. Click **Install**

**Option 2: Manual Installation**
1. Download the latest release
2. Copy `KiNotes/` folder to:
   - **Windows:** `%APPDATA%\kicad\9.0\scripting\plugins\`
   - **macOS:** `~/Library/Preferences/kicad/9.0/scripting/plugins/`
   - **Linux:** `~/.config/kicad/9.0/scripting/plugins/`
3. Restart KiCad

### Usage
1. Open a PCB in pcbnew
2. Click the **KiNotes** toolbar button (or **Tools → External Plugins → KiNotes**)
3. Start writing notes!

---

## 📖 Syntax Guide

### To-Do Lists
```markdown
- [ ] Review power section
- [x] Verify differential pairs
- [ ] Check thermal reliefs
```

### Component Links
```markdown
Check @U3 orientation before assembly.
The decoupling caps @C1 @C2 @C3 should be close to @U1.
```
> Click any `@REF` to highlight it on the PCB!

### Insert Metadata
Click the **Import Metadata** dropdown and select:
- `${BOM}` — Insert BOM table
- `${STACKUP}` — Insert layer stackup
- `${BOARD_SIZE}` — Insert board dimensions
- `${DIFF_PAIRS}` — Insert differential pairs
- `${NETLIST}` — Insert net summary
- `${DRILL_TABLE}` — Insert drill information

### Images
```markdown
![Block Diagram](./images/block_diagram.png)
```

---

## 🏗️ Architecture

```
KiNotes/
├── __init__.py              # Package init & plugin registration
├── kinotes_action.py        # Main action plugin entry point
├── ui/
│   ├── main_panel.py        # Main notes panel UI
│   ├── visual_editor.py     # WYSIWYG rich text editor
│   ├── markdown_converter.py# Markdown ↔ RichText conversion
│   ├── toolbar.py           # Icon toolbar
│   ├── bom_dialog.py        # IBOM-style BOM generator
│   └── styles.py            # iOS-like styling
├── core/
│   ├── notes_manager.py     # Load/save notes
│   ├── designator_linker.py # @REF → PCB highlight
│   ├── metadata_extractor.py# BOM, stackup, netlist extraction
│   └── pdf_exporter.py      # PDF export
├── resources/
│   ├── icon.png
│   ├── icons/               # Toolbar icons
│   └── styles.css           # UI styling
└── .kinotes/                # Per-project notes storage
    └── notes.md
```

---

## 🗺️ Roadmap

| Version | Features | Status |
|---------|----------|:------:|
| **v1.0** | Notes panel, auto-save, basic Markdown | 🟢 Done |
| **v1.1** | `@REF` linking, component highlight | 🟢 Done |
| **v1.2** | Metadata import (BOM, stackup, etc.) | 🟢 Done |
| **v1.3** | Dark/Light mode, custom colors, time tracking | 🟢 Done |
| **v1.4** | **Visual Editor (WYSIWYG)**, Markdown converter | 🟢 Done |
| **v1.5** | Table rendering in Visual Editor | 🔄 In Progress |
| **v2.0** | Production release, KiCad Plugin Manager | 🔄 Planned |

---

## 🔧 Requirements

- **KiCad 9.0+** (Python 3.9+, wxPython 4.2+)
- No external dependencies — pure Python + wxWidgets

---

## 🤝 Contributing

Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

**MIT License** — free for personal and commercial use.

See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**KiNotes** by [PCBtools.xyz](https://pcbtools.xyz)

---

<p align="center">
  <sub>Built with ❤️ by PCBtools.xyz</sub>
</p>
