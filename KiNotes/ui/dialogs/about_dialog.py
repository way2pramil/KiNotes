"""
KiNotes About Dialog - Application information and story.

Shows:
- Version information
- Project story
- Links to website, GitHub, donations
- Copyright information

Usage:
    from .dialogs import show_about_dialog
    show_about_dialog(parent, theme, open_url_callback)
"""
import wx

from ..themes import hex_to_colour
from ..components import RoundedButton

# Import version from single source
try:
    from ...__version__ import __version__
except ImportError:
    __version__ = "1.4.2"  # Fallback


def show_about_dialog(parent, theme, open_url_callback):
    """
    Show About KiNotes dialog with project story.
    
    Args:
        parent: Parent window
        theme: Current theme dict (DARK_THEME or LIGHT_THEME)
        open_url_callback: Function to open URLs in browser
    """
    dlg = wx.Dialog(parent, title="About KiNotes", size=(800, 650),
                   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
    dlg.SetMinSize((700, 500))
    dlg.SetBackgroundColour(hex_to_colour(theme["bg_panel"]))
    
    main_sizer = wx.BoxSizer(wx.VERTICAL)
    
    # Scrolled content area
    scroll_win = wx.ScrolledWindow(dlg, style=wx.VSCROLL)
    scroll_win.SetScrollRate(0, 20)
    scroll_win.SetBackgroundColour(hex_to_colour(theme["bg_panel"]))
    
    content_sizer = wx.BoxSizer(wx.VERTICAL)
    content_sizer.AddSpacer(24)
    
    # Header with icon and title
    header_sizer = wx.BoxSizer(wx.HORIZONTAL)
    
    # KiNotes icon (using emoji as fallback)
    icon_label = wx.StaticText(scroll_win, label="📝")
    icon_label.SetFont(wx.Font(32, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    header_sizer.Add(icon_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
    
    # Title and version
    title_box = wx.BoxSizer(wx.VERTICAL)
    title = wx.StaticText(scroll_win, label="KiNotes")
    title.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    title.SetForegroundColour(hex_to_colour(theme["text_primary"]))
    title_box.Add(title, 0)
    
    version = wx.StaticText(scroll_win, label=f"Engineering Notes for KiCad • v{__version__}")
    version.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    version.SetForegroundColour(hex_to_colour(theme["text_secondary"]))
    title_box.Add(version, 0, wx.TOP, 4)
    
    header_sizer.Add(title_box, 1)
    content_sizer.Add(header_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(24)
    
    # Separator line
    sep = wx.StaticLine(scroll_win)
    content_sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(24)
    
    # Story section header
    story_header = wx.StaticText(scroll_win, label="The Story Behind the Tool")
    story_header.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    story_header.SetForegroundColour(hex_to_colour(theme["text_primary"]))
    content_sizer.Add(story_header, 0, wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(16)
    
    # The story - of KiNotes
    story_text = """Every hardware project starts with excitement—that rush when a new board idea clicks into place. But somewhere between the first schematic and the final layout, things get messy. You're routing traces at 2 AM, chasing DRC errors, fixing the same footprint issue for the third time. Sound familiar?

Here's what I noticed after years of PCB work: the projects that succeeded weren't always the most clever designs. They were the ones with clear notes. The ones where I could remember why I chose that capacitor value, or what test failed on Rev A.

KiNotes started as a simple text file I kept open next to KiCad. Nothing fancy—just a scratch pad for design decisions. But I kept losing it, forgetting to save, opening the wrong version. The notes lived outside the project, and that was the problem.

So I built this. A notes panel that lives inside KiCad, saves automatically with your project, and stays out of your way until you need it. No cloud accounts, no sync conflicts, no friction.

And yes—it auto-saves. Because let's be honest: when vias, traces, and layers are dancing in your head, Ctrl+S is the last thing you remember. Your notes survive your forgetting.

Over time, it grew. Task tracking for those TODO lists that always pile up. Time logging because clients ask "how long did that take?" BOM integration because you shouldn't need three tools open to design one board.

The philosophy hasn't changed though: a note written today saves hours tomorrow. A design decision documented now prevents the same argument six months from now. It's not about being organized—it's about not repeating your own mistakes.

KiNotes is open source because good tools should be shared. If it helps you ship better boards, that's the goal. If you want to make it better, the code is there.

Built for engineers who've learned that memory is unreliable, but good notes aren't."""
    
    story = wx.StaticText(scroll_win, label=story_text)
    story.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    story.SetForegroundColour(hex_to_colour(theme["text_primary"]))
    story.Wrap(700)  # Wrap text at 700px
    content_sizer.Add(story, 0, wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(24)
    
    # Separator
    sep2 = wx.StaticLine(scroll_win)
    content_sizer.Add(sep2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(16)
    
    # Links section
    links_sizer = wx.BoxSizer(wx.HORIZONTAL)
    
    website_link = wx.StaticText(scroll_win, label="🌐 pcbtools.xyz")
    website_link.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
    website_link.SetForegroundColour(hex_to_colour(theme["accent_blue"]))
    website_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    website_link.Bind(wx.EVT_LEFT_DOWN, lambda e: open_url_callback("https://pcbtools.xyz"))
    links_sizer.Add(website_link, 0, wx.RIGHT, 24)
    
    github_link = wx.StaticText(scroll_win, label="📦 GitHub")
    github_link.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
    github_link.SetForegroundColour(hex_to_colour(theme["accent_blue"]))
    github_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    github_link.Bind(wx.EVT_LEFT_DOWN, lambda e: open_url_callback("https://github.com/way2pramil/KiNotes"))
    links_sizer.Add(github_link, 0, wx.RIGHT, 24)
    
    donate_link = wx.StaticText(scroll_win, label="💝 Support Development")
    donate_link.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
    donate_link.SetForegroundColour(hex_to_colour(theme["accent_blue"]))
    donate_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    donate_link.Bind(wx.EVT_LEFT_DOWN, lambda e: open_url_callback("https://pcbtools.xyz/donate"))
    links_sizer.Add(donate_link, 0)
    
    content_sizer.Add(links_sizer, 0, wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(16)
    
    # Copyright
    copyright_text = wx.StaticText(scroll_win, label="© 2024-2025 PCBtools.xyz • Open Source (MIT License)")
    copyright_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    copyright_text.SetForegroundColour(hex_to_colour(theme["text_secondary"]))
    content_sizer.Add(copyright_text, 0, wx.LEFT | wx.RIGHT, 32)
    
    content_sizer.AddSpacer(24)
    
    scroll_win.SetSizer(content_sizer)
    scroll_win.FitInside()
    
    main_sizer.Add(scroll_win, 1, wx.EXPAND)
    
    # Close button panel - fixed at bottom
    btn_panel = wx.Panel(dlg)
    btn_panel.SetBackgroundColour(hex_to_colour(theme["bg_panel"]))
    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_sizer.AddStretchSpacer()
    
    close_btn = RoundedButton(
        btn_panel,
        label="Close",
        icon="",
        size=(120, 42),
        bg_color=theme["accent_blue"],
        fg_color="#FFFFFF",
        corner_radius=10,
        font_size=11,
        font_weight=wx.FONTWEIGHT_BOLD
    )
    close_btn.Bind_Click(lambda e: dlg.EndModal(wx.ID_OK))
    btn_sizer.Add(close_btn, 0)
    btn_sizer.AddStretchSpacer()
    
    btn_panel.SetSizer(btn_sizer)
    main_sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 20)
    
    dlg.SetSizer(main_sizer)
    dlg.ShowModal()
    dlg.Destroy()
