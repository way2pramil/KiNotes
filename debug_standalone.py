#!/usr/bin/env python3
"""
Standalone debugger for KiNotes UI (runs outside KiCad)
This allows testing UI components without needing KiCad running.
"""
import sys
import os

# Add the plugin directory to path
plugin_dir = os.path.join(os.path.dirname(__file__), "KiNotes")
sys.path.insert(0, plugin_dir)

# Mock pcbnew module (not available outside KiCad)
class MockPcbnew:
    def GetBoard(self):
        return None

sys.modules['pcbnew'] = MockPcbnew()

import wx

# Import after mocking pcbnew
from ui.main_panel import KiNotesMainPanel

# Mock managers for standalone testing
class MockNotesManager:
    def load(self): return "# Test Notes\n\nThis is a test."
    def save(self, content): print(f"[SAVE] Notes: {len(content)} chars")
    def load_todos(self): return [{"text": "Test task 1", "done": False}, {"text": "Done task", "done": True}]
    def save_todos(self, todos): print(f"[SAVE] Todos: {len(todos)} items")
    def load_settings(self): return {"bg_color": "Ivory Paper", "text_color": "Carbon Black", "dark_mode": False}
    def save_settings(self, settings): print(f"[SAVE] Settings: {settings}")

class MockDesignatorLinker:
    def highlight(self, ref): 
        print(f"[HIGHLIGHT] {ref}")
        return True

class MockMetadataExtractor:
    def extract(self, meta_type):
        return f"# Mock {meta_type}\n\nNo board loaded (running in debug mode)"

class MockPdfExporter:
    def export(self, content):
        print(f"[PDF] Would export {len(content)} chars")
        return "debug_export.pdf"


class DebugFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="KiNotes Debug", size=(840, 900))
        self.SetMinSize((600, 700))
        
        # Create the main panel with mock dependencies
        self.panel = KiNotesMainPanel(
            self,
            notes_manager=MockNotesManager(),
            designator_linker=MockDesignatorLinker(),
            metadata_extractor=MockMetadataExtractor(),
            pdf_exporter=MockPdfExporter()
        )
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Centre()
    
    def on_close(self, event):
        self.panel.cleanup()
        self.Destroy()


def main():
    print("=" * 50)
    print("KiNotes Standalone Debug Mode")
    print("=" * 50)
    print("Note: pcbnew features won't work (no board loaded)")
    print()
    
    app = wx.App()
    frame = DebugFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
