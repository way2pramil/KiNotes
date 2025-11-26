import pcbnew
import wx

class KiNotesFrame(wx.Frame):
    def __init__(self, parent=None, title="KiNotes - PCB Notes"):
        super(KiNotesFrame, self).__init__(parent, title=title, size=(400, 500))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Temporary text area (Markdown later)
        self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_RICH2)

        # Subtle branding footer
        footer = wx.StaticText(panel, label="Powered by PCBtools.xyz")
        footer.SetForegroundColour(wx.Colour(100, 100, 100))

        vbox.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(footer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)

        panel.SetSizer(vbox)
        self.Layout()


class KiNotesActionPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiNotes"
        self.category = "Utilities"
        self.description = "Smart PCB Notes linked to your design"
        self.show_toolbar_button = True
        self.icon_file_name = self.get_icon()

    def get_icon(self):
        import os
        return os.path.join(os.path.dirname(__file__), "resources", "icon.png")

    def Run(self):
        frame = KiNotesFrame(parent=None)
        frame.Show(True)
