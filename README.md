# KiNotes — Smart Engineering Notes for KiCad 9+

<p align="center">
  <img src="KiNotes/resources/icon.png" alt="KiNotes" width="64"/>
</p>

**KiNotes** brings real engineering notes **directly inside KiCad pcbnew** — with zero friction.  
Write design decisions, link components with `@R1` syntax, import board metadata, and export beautiful PDFs.

> 🎯 **Target:** KiCad 9.0+ only — built for modern KiCad with Python 3 and wxPython 4.

---

## ✨ Features

### 📝 Smart Notes Editor
- **Markdown-based** notes with live formatting
- **To-do lists** with `- [ ]` / `- [x]` checkboxes and strikethrough
- **Auto-link designators** — type `@R1`, `@U3`, `@C5` → highlights component on PCB
- **Insert images** — embed block diagrams, schematics, or screenshots
- **Auto-save** on every change, close, or outside click
- **Git-friendly** `.kinotes/` folder in project directory

### 🔗 PCB Integration (KiCad 9+)
- **Import Board Metadata** with one-click dropdown:
  - BOM (Bill of Materials)
  - Stackup configuration
  - Board size & parameters
  - Differential pairs
  - Netlist summary
  - Layer information
  - Drill table
  - Design rules
- **Click `@REF`** → jump to and highlight component in pcbnew
- **Component metadata preview** — value, footprint, layer, nets

### 📤 Export
- **Export to PDF** with PCB project name as filename
- **Export to Markdown** for documentation
- **Print-ready** formatting

### 🎨 Modern UI
- **iOS-inspired** clean, minimal interface
- **Follows KiCad UI** patterns for natural integration
- **Dockable panel** — dock left/right like Properties panel, or use popup
- **Icon-based toolbar** — intuitive buttons
- **Dark/Light mode** — respects system theme
- **PCBtools.xyz branding** in footer

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
│   ├── toolbar.py           # Icon toolbar
│   ├── todo_widget.py       # Checkbox to-do list
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
| **v0.1** | Notes panel, auto-save, basic Markdown | 🟢 Done |
| **v0.2** | `@REF` linking, component highlight | 🟡 In Progress |
| **v0.3** | Metadata import (BOM, stackup, etc.) | 🔄 Planned |
| **v0.4** | PDF export, image support | 🔄 Planned |
| **v0.5** | Dockable panel, iOS-like UI polish | 🔄 Planned |
| **v1.0** | Production release | 🔄 Planned |

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
