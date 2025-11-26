import pcbnew
import wx
import os

class KiNotesFrame(wx.Frame):
    def __init__(self, parent=None, title="KiNotes - PCB Notes"):
        super(KiNotesFrame, self).__init__(parent, title=title, size=(400, 500))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_RICH2)
        vbox.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)
        self.Layout()

        # Load notes AFTER UI exists
        self.notes_path = self.get_notes_file_path()
        self.ensure_folder_exists()
        self.load_notes()

        self.text_ctrl.Bind(wx.EVT_TEXT, self.on_text_changed)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def get_project_dir(self):
        board = pcbnew.GetBoard()
        return os.path.dirname(board.GetFileName())

    def get_notes_file_path(self):
        project_dir = self.get_project_dir()
        notes_dir = os.path.join(project_dir, ".kinotes")
        return os.path.join(notes_dir, "notes.md")

    def ensure_folder_exists(self):
        folder = os.path.dirname(self.notes_path)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def load_notes(self):
        if os.path.exists(self.notes_path):
            with open(self.notes_path, "r", encoding="utf-8") as f:
                self.text_ctrl.SetValue(f.read())

    def on_text_changed(self, event):
        self.save_notes()
        event.Skip()

    def on_close(self, event):
        self.save_notes()
        self.Destroy()

    def save_notes(self):
        with open(self.notes_path, "w", encoding="utf-8") as f:
            f.write(self.text_ctrl.GetValue())



class KiNotesActionPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiNotes"
        self.category = "Utilities"
        self.description = "Smart PCB Notes linked to your design"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "resources", "icon.png")

    def Run(self):
        board = pcbnew.GetBoard()
        if not board:
            wx.MessageBox("Please open a PCB layout first.", "KiNotes", wx.OK | wx.ICON_WARNING)
            return

        project_path = board.GetFileName()

        if not project_path or project_path.strip() == "":
            wx.MessageBox("Please save your PCB layout before using KiNotes.", "KiNotes", wx.OK | wx.ICON_WARNING)
            return

        project_path_lower = project_path.lower()
        if project_path_lower.startswith("c:\\program files") or "kicad\\demos" in project_path_lower:
            wx.MessageBox("Read-only project location detected.\nPlease save the PCB project to a writable location (e.g., Documents).",
                          "KiNotes", wx.OK | wx.ICON_ERROR)
            return

        frame = KiNotesFrame(None)
        frame.Show(True)


KiNotesActionPlugin().register()