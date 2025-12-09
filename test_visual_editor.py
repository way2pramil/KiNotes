"""
Test script for Visual Editor - Theme and Import functionality
"""
import sys
import os

# Add KiNotes to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'KiNotes'))

import wx
import wx.richtext as rt

# Import visual editor
from ui.visual_editor import VisualNoteEditor, VisualEditorStyles

class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Visual Editor Test", size=(900, 700))
        
        self._dark_mode = False
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Control buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Theme toggle
        self.theme_btn = wx.Button(panel, label="Toggle Dark Mode")
        self.theme_btn.Bind(wx.EVT_BUTTON, self._on_toggle_theme)
        btn_sizer.Add(self.theme_btn, 0, wx.ALL, 5)
        
        # Custom colors button
        self.colors_btn = wx.Button(panel, label="Apply Custom Colors")
        self.colors_btn.Bind(wx.EVT_BUTTON, self._on_custom_colors)
        btn_sizer.Add(self.colors_btn, 0, wx.ALL, 5)
        
        # Test import BOM button
        self.bom_btn = wx.Button(panel, label="Test BOM Import")
        self.bom_btn.Bind(wx.EVT_BUTTON, self._on_import_bom)
        btn_sizer.Add(self.bom_btn, 0, wx.ALL, 5)
        
        # Test import layers button
        self.layers_btn = wx.Button(panel, label="Test Layers Import")
        self.layers_btn.Bind(wx.EVT_BUTTON, self._on_import_layers)
        btn_sizer.Add(self.layers_btn, 0, wx.ALL, 5)
        
        # Insert table button
        self.table_btn = wx.Button(panel, label="Insert Table")
        self.table_btn.Bind(wx.EVT_BUTTON, self._on_insert_table)
        btn_sizer.Add(self.table_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND)
        
        # Visual Editor
        self.visual_editor = VisualNoteEditor(panel, dark_mode=self._dark_mode)
        sizer.Add(self.visual_editor, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Status bar
        self.CreateStatusBar()
        self.SetStatusText("Ready - Test visual editor features")
        
    def _on_toggle_theme(self, event):
        """Toggle between light and dark mode."""
        self._dark_mode = not self._dark_mode
        # Custom colors should persist after this!
        self.visual_editor.update_dark_mode(self._dark_mode, force_refresh=True)
        mode_name = "Dark" if self._dark_mode else "Light"
        self.SetStatusText(f"Theme changed to {mode_name} mode - custom colors should persist!")
        print(f"Theme toggled to: {mode_name}")
        print(f"  Current bg: {self.visual_editor._bg_color}")
        print(f"  Custom bg: {self.visual_editor._custom_bg_color}")
    
    def _on_custom_colors(self, event):
        """Apply custom colors."""
        # Test custom colors (sepia-like)
        if self._dark_mode:
            bg = wx.Colour(40, 35, 30)  # Dark brown
            fg = wx.Colour(255, 240, 200)  # Warm white
        else:
            bg = wx.Colour(255, 250, 240)  # Warm cream
            fg = wx.Colour(60, 40, 20)  # Dark brown
        
        self.visual_editor.set_custom_colors(bg, fg)
        self.SetStatusText(f"Custom colors applied - toggle theme to verify persistence!")
        print(f"Custom colors set: bg={bg}, fg={fg}")
        print(f"  Stored custom bg: {self.visual_editor._custom_bg_color}")
        print(f"  Stored custom fg: {self.visual_editor._custom_text_color}")
    
    def _on_import_bom(self, event):
        """Test BOM import with markdown table."""
        # Sample BOM markdown
        bom_text = """## Bill of Materials

| Ref | Value | Footprint | Qty |
|-----|-------|-----------|-----|
| R1, R2, R3 | 10K | 0603 | 3 |
| C1, C2 | 100nF | 0402 | 2 |
| U1 | ESP32-WROOM | QFN-48 | 1 |
| D1, D2 | LED_Green | 0805 | 2 |

*Total components: 8*
"""
        try:
            self.visual_editor.insert_markdown_as_formatted(bom_text)
            self.SetStatusText("BOM imported successfully!")
            print("BOM import successful")
        except Exception as e:
            self.SetStatusText(f"BOM import failed: {e}")
            print(f"BOM import error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_import_layers(self, event):
        """Test layers import with markdown table."""
        layers_text = """## Layer Information

| Layer Name | Type | Material | Color |
|------------|------|----------|-------|
| F.Cu | Copper | Cu | Red |
| In1.Cu | Copper | Cu | Yellow |
| In2.Cu | Copper | Cu | Orange |
| B.Cu | Copper | Cu | Blue |
| F.SilkS | Silkscreen | - | White |
| B.SilkS | Silkscreen | - | White |

*6 layers configured*
"""
        try:
            self.visual_editor.insert_markdown_as_formatted(layers_text)
            self.SetStatusText("Layers imported successfully!")
            print("Layers import successful")
        except Exception as e:
            self.SetStatusText(f"Layers import failed: {e}")
            print(f"Layers import error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_insert_table(self, event):
        """Test direct table insertion."""
        try:
            # Insert a table using the data table method
            headers = ["Name", "Value", "Unit"]
            data = [
                ["Voltage", "3.3", "V"],
                ["Current", "500", "mA"],
                ["Power", "1.65", "W"],
            ]
            self.visual_editor.insert_data_table(headers, data, "Test Data Table")
            self.SetStatusText("Table inserted successfully!")
            print("Table insert successful")
        except Exception as e:
            self.SetStatusText(f"Table insert failed: {e}")
            print(f"Table insert error: {e}")
            import traceback
            traceback.print_exc()


def main():
    app = wx.App()
    frame = TestFrame()
    frame.Show()
    print("Test frame opened. Test the following:")
    print("1. Toggle Dark Mode - switches theme")
    print("2. Apply Custom Colors - sets sepia-like colors")
    print("3. Test BOM Import - imports markdown table as visual table")
    print("4. Test Layers Import - imports markdown table as visual table")
    print("5. Insert Table - directly inserts a data table")
    app.MainLoop()


if __name__ == "__main__":
    main()
