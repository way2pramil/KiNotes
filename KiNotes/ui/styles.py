"""
KiNotes Styles - iOS-inspired styling for KiCad integration
"""
import wx


class KiNotesStyles:
    """iOS-inspired styling that follows KiCad UI patterns."""
    
    # Colors - Light Theme
    LIGHT_BG = wx.Colour(250, 250, 250)
    LIGHT_PANEL_BG = wx.Colour(255, 255, 255)
    LIGHT_BORDER = wx.Colour(220, 220, 220)
    LIGHT_TEXT = wx.Colour(30, 30, 30)
    LIGHT_TEXT_SECONDARY = wx.Colour(120, 120, 120)
    LIGHT_ACCENT = wx.Colour(0, 122, 255)  # iOS blue
    LIGHT_SUCCESS = wx.Colour(52, 199, 89)  # iOS green
    LIGHT_WARNING = wx.Colour(255, 149, 0)  # iOS orange
    LIGHT_TOOLBAR_BG = wx.Colour(245, 245, 245)
    LIGHT_HOVER = wx.Colour(235, 235, 235)
    LIGHT_SELECTED = wx.Colour(0, 122, 255, 30)
    
    # Colors - Dark Theme
    DARK_BG = wx.Colour(28, 28, 30)
    DARK_PANEL_BG = wx.Colour(44, 44, 46)
    DARK_BORDER = wx.Colour(58, 58, 60)
    DARK_TEXT = wx.Colour(255, 255, 255)
    DARK_TEXT_SECONDARY = wx.Colour(142, 142, 147)
    DARK_ACCENT = wx.Colour(10, 132, 255)  # iOS blue (dark)
    DARK_SUCCESS = wx.Colour(48, 209, 88)  # iOS green (dark)
    DARK_WARNING = wx.Colour(255, 159, 10)  # iOS orange (dark)
    DARK_TOOLBAR_BG = wx.Colour(36, 36, 38)
    DARK_HOVER = wx.Colour(58, 58, 60)
    DARK_SELECTED = wx.Colour(10, 132, 255, 50)
    
    # Fonts
    FONT_SIZE_NORMAL = 11
    FONT_SIZE_SMALL = 9
    FONT_SIZE_LARGE = 13
    FONT_SIZE_TITLE = 15
    
    # Spacing
    PADDING_SMALL = 4
    PADDING_NORMAL = 8
    PADDING_LARGE = 12
    MARGIN_SMALL = 4
    MARGIN_NORMAL = 8
    MARGIN_LARGE = 16
    
    # Border radius (for custom drawing)
    BORDER_RADIUS = 8
    BORDER_RADIUS_SMALL = 4
    
    # Button sizes
    BUTTON_HEIGHT = 28
    ICON_BUTTON_SIZE = 28
    TOOLBAR_HEIGHT = 40
    
    # Checkbox styles
    CHECKBOX_UNCHECKED = "☐"
    CHECKBOX_CHECKED = "☑"
    
    @classmethod
    def is_dark_mode(cls):
        """Detect if system is in dark mode."""
        try:
            # Try to detect from system settings
            settings = wx.SystemSettings
            bg_colour = settings.GetColour(wx.SYS_COLOUR_WINDOW)
            # If background is dark, we're in dark mode
            luminance = (0.299 * bg_colour.Red() + 
                        0.587 * bg_colour.Green() + 
                        0.114 * bg_colour.Blue())
            return luminance < 128
        except:
            return False
    
    @classmethod
    def get_bg_color(cls):
        return cls.DARK_BG if cls.is_dark_mode() else cls.LIGHT_BG
    
    @classmethod
    def get_panel_bg_color(cls):
        return cls.DARK_PANEL_BG if cls.is_dark_mode() else cls.LIGHT_PANEL_BG
    
    @classmethod
    def get_border_color(cls):
        return cls.DARK_BORDER if cls.is_dark_mode() else cls.LIGHT_BORDER
    
    @classmethod
    def get_text_color(cls):
        return cls.DARK_TEXT if cls.is_dark_mode() else cls.LIGHT_TEXT
    
    @classmethod
    def get_text_secondary_color(cls):
        return cls.DARK_TEXT_SECONDARY if cls.is_dark_mode() else cls.LIGHT_TEXT_SECONDARY
    
    @classmethod
    def get_accent_color(cls):
        return cls.DARK_ACCENT if cls.is_dark_mode() else cls.LIGHT_ACCENT
    
    @classmethod
    def get_toolbar_bg_color(cls):
        return cls.DARK_TOOLBAR_BG if cls.is_dark_mode() else cls.LIGHT_TOOLBAR_BG
    
    @classmethod
    def get_hover_color(cls):
        return cls.DARK_HOVER if cls.is_dark_mode() else cls.LIGHT_HOVER
    
    @classmethod
    def get_normal_font(cls):
        return wx.Font(cls.FONT_SIZE_NORMAL, wx.FONTFAMILY_DEFAULT, 
                      wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    
    @classmethod
    def get_bold_font(cls):
        return wx.Font(cls.FONT_SIZE_NORMAL, wx.FONTFAMILY_DEFAULT, 
                      wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    
    @classmethod
    def get_title_font(cls):
        return wx.Font(cls.FONT_SIZE_TITLE, wx.FONTFAMILY_DEFAULT, 
                      wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    
    @classmethod
    def get_mono_font(cls):
        """Monospace font for code/notes."""
        return wx.Font(cls.FONT_SIZE_NORMAL, wx.FONTFAMILY_TELETYPE, 
                      wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    
    @classmethod
    def apply_panel_style(cls, panel):
        """Apply iOS-like styling to a panel."""
        panel.SetBackgroundColour(cls.get_panel_bg_color())
    
    @classmethod
    def apply_button_style(cls, button):
        """Apply iOS-like styling to a button."""
        button.SetBackgroundColour(cls.get_toolbar_bg_color())
        button.SetForegroundColour(cls.get_accent_color())
        button.SetFont(cls.get_normal_font())
    
    @classmethod
    def apply_text_style(cls, text_ctrl):
        """Apply styling to text control."""
        text_ctrl.SetBackgroundColour(cls.get_panel_bg_color())
        text_ctrl.SetForegroundColour(cls.get_text_color())
        text_ctrl.SetFont(cls.get_mono_font())
