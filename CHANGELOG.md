# Changelog

All notable changes to KiNotes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2025-06-17

### Added
- **Fab Summary Import**: One-click import of board fabrication info with section selection dialog
  - Board finish (ENIG, castellated holes, edge plating)
  - Track analysis (actual min/max widths and vias on board)
  - Fab capability checklist for easy quoting
- **Image Paste Support**: Ctrl+V to paste images from clipboard into notes
  - Images saved to `.kinotes/images/` folder
  - Automatic file naming with timestamps
- **Per-Module Debug System**: Granular debug logging for troubleshooting
- **Fab Import Selection Dialog**: Choose which sections to import (board size, layers, drill table, etc.)

### Changed
- Improved PDF export with better formatting
- Refactored metadata extraction to reuse existing methods (reduced code duplication)
- Enhanced visual editor paste handling

### Fixed
- Visual editor theme color application to existing text
- Settings dialog attribute reference (`_settings` → `_dark_mode`)

## [1.4.2] - 2025-05-15

### Added
- Time tracking with session history and work diary export
- Visual editor with rich text formatting (bold, italic, lists, headings)
- Smart-Link for nets (beta): Click net names to highlight traces
- BOM tab for Bill of Materials generation
- Version log tab for design revision tracking

### Changed
- Improved dark/light theme consistency
- Better DPI scaling for high-resolution displays

### Fixed
- Crash safety system for recovery after unexpected closures
- Module reloading for development workflow

## [1.4.0] - 2025-04-20

### Added
- Smart-Link designator linking: Click R1, C5, U3 → highlight on PCB
- Markdown editor mode (toggle between visual and raw)
- Auto-save on every change
- Import board metadata (BOM, stackup, netlist, layers, diff pairs)
- PDF export functionality

### Changed
- Migrated to modular architecture (small, focused files)
- Settings moved to `.kinotes/settings.json`

## [1.3.0] - 2025-03-10

### Added
- Todo list with task completion tracking
- Dark/Light theme support
- Custom color schemes

### Changed
- Notes stored in `.kinotes/` folder alongside project

## [1.0.0] - 2025-02-01

### Added
- Initial release
- Basic notes editor for KiCad 9.0+
- Project-local storage in Markdown format
- Toolbar integration in pcbnew

---

[1.5.0]: https://github.com/way2pramil/KiNotes/releases/tag/v1.5.0
[1.4.2]: https://github.com/way2pramil/KiNotes/releases/tag/v1.4.2
[1.4.0]: https://github.com/way2pramil/KiNotes/releases/tag/v1.4.0
[1.3.0]: https://github.com/way2pramil/KiNotes/releases/tag/v1.3.0
[1.0.0]: https://github.com/way2pramil/KiNotes/releases/tag/v1.0.0
