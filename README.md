# KiNotes — Smart Notes for KiCad PCB Designers

KiNotes brings real engineering notes **directly inside KiCad**.  
Write and link decisions to actual components, layers, stack-up, and BOM — all while designing.

---

## ✨ Key Features

- Markdown-based notes
- Link references like `U3`, `R10`, `Net-(J1-Pad1)` → highlight in pcbnew
- Show metadata: footprint, value, net, layer
- Auto-load notes per KiCad project
- Access from KiCad Plugin Manager
- External full-editor mode powered by MarkText (MIT)

| Feature | Status |
|--------|:-----:|
| Notes panel inside pcbnew | 🟢 Working |
| Component-link support | 🔄 Planned |
| Metadata preview | 🔄 Planned |
| Stack-up reference | 🔄 Planned |
| BOM integration | 🔄 Planned |
| Git diff-friendly storage | 🟢 Markdown |

---

## 🔧 Architecture

- KiCad Action Plugin (Python)
- Markdown files stored in project folder: `.kinotes/notes.md`
- JSON/IPC bridge for PCB metadata linking
- Calls MarkText for full editing (optional)

Structure:
pcbnew
└── KiNotes Panel
├── Markdown Notes
├── Component Link Resolver
└── Metadata Preview


---

## 📦 Installation (future)

1. KiCad → **Tools → Plugin and Content Manager**
2. Search **KiNotes**
3. Install

---

## 🛠 Roadmap

| Version | What’s Coming |
|--------|---------------|
| v0.1 | Notes panel embedded in pcbnew |
| v0.2 | Component linking & highlight |
| v0.3 | Metadata + layer view |
| v0.4 | BOM & stack-up integration |
| v1.0 | Production release with polish |

---

## 🤝 Contributing

Documentation and tasks coming soon.  
Feedback welcome!

---

## 📄 License
MIT — free for personal & commercial use.
---

## 👨‍💻 Author

KiNotes by **PCBtools.xyz**

Local Kicad install  di C:\Users\prami\AppData\Roaming\kicad\9.0\scripting\plugins