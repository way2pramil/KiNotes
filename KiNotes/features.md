## ✅ Current Features (MVP)

- Standalone KiNotes window inside KiCad (pcbnew)
- Autosave notes to project folder (`.kinotes/notes.md`)
- Manual Save button
- Stable behavior (no crashes in normal use)

---

## 🟩 Phase 2 — Smart Notes (Inside KiCad UI)

- Detect component references in notes (e.g. `U3`, `R10`, `C5`)
- Click reference in notes → highlight component on PCB
- Show component metadata popup:
  - Reference (e.g. U3)
  - Value
  - Footprint
  - Layer
  - Nets
- Auto-insert project metadata from KiCad:
  - `${TITLE}`
  - `${REVISION}`
  - `${ISSUE_DATE}`
  - `${KICAD_VERSION}`
  - `${COMPANY}`
  - `${COMMENT1}`
  - `${FILENAME}`
- To-do list inside notes:
  - `- [ ] Task` / `- [x] Done`
- Time tracker:
  - Track time spent per PCB project when KiNotes is open
  - Store in `.kinotes/time.json`
- Basic Markdown-style formatting:
  - Bullet lists
  - Headings
  - Emphasis (bold/italic)
- Export notes to:
  - Markdown file
  - (Future) PDF

---

## 🟦 Phase 3 — PCB Navigation & Context

- Search notes for a reference and jump to that component on PCB
- Link notes to:
  - Nets
  - Layers
  - Tracks / vias
- Click a component in PCB → open related section in KiNotes
- Keep notes in sync when reference designators change

---

## 🟪 Phase 4 — Engineering Notebook Features

- Store design decisions and rationale per block
- Attach datasheet links or local file paths in notes
- Maintain revision / change logs inside KiNotes
- Document assembly instructions and test notes
- Risk / FMEA-style annotations for critical components

---

## 🟧 Phase 5 — KiNotes Pro (Local-First Enhancements)

- Multiple pages of notes per project (index of notes)
- Dashboard view of all notes for a project
- Basic project analytics:
  - Number of sessions
  - Time spent
- (Optional) Part information helpers:
  - Manual BOM tagging
  - Links to supplier pages

---

## 🟥 Phase 6 — Future Cloud / Team Collaboration (Optional)

- Optional PCBtools.xyz account integration
- Sync notes between machines / team members
- Web access to project notes
- Shared review / comment threads on notes
- AI-assisted summaries and design checks
