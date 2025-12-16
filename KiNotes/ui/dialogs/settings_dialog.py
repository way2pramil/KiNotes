"""
KiNotes Settings Dialog - Modular, responsive, theme-aware configuration.

Refactored using:
- wx.lib.scrolledpanel.ScrolledPanel for robust cross-platform scrolling
- Flexible sizers with consistent margins
- Centralized theming with apply_theme_recursive()

Handles:
- Theme selection (Light/Dark)
- Color customization
- Time tracking options
- Cross-probe settings
- UI scale settings
- Panel size settings
- Beta features toggle

Usage:
    from .dialogs import show_settings_dialog
    result, save_mode = show_settings_dialog(parent, config)
    if result:
        # Apply settings from result dict
"""
import wx
import wx.adv
import wx.lib.scrolledpanel as scrolled

from ..themes import (
    hex_to_colour,
    BACKGROUND_COLORS, TEXT_COLORS,
    DARK_BACKGROUND_COLORS, DARK_TEXT_COLORS,
    DARK_THEME, LIGHT_THEME
)
from ..scaling import get_dpi_scale_factor, get_user_scale_factor, set_user_scale_factor
from ..components import RoundedButton

# Import centralized defaults
from ...core.defaultsConfig import (
    WINDOW_DEFAULTS, PERFORMANCE_DEFAULTS, DEFAULTS, BETA_DEFAULTS, TIME_TRACKER_DEFAULTS
)


# ------------------------------ Helpers ---------------------------------

def set_label_style(ctrl, theme, bold=False, size=10):
    """Apply consistent label styling."""
    weight = wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL
    font = wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, weight)
    ctrl.SetFont(font)
    ctrl.SetForegroundColour(hex_to_colour(theme.get('text_primary', '#000000')))


def apply_theme_recursive(widget, theme):
    """Apply theme colours recursively to widget and its children."""
    bg = hex_to_colour(theme.get('bg_panel', '#FFFFFF'))
    if bg.IsOk():
        try:
            widget.SetBackgroundColour(bg)
        except Exception:
            pass

    for child in widget.GetChildren():
        # Static text
        if isinstance(child, wx.StaticText):
            tp = hex_to_colour(theme.get('text_primary', '#000000'))
            if tp.IsOk():
                child.SetForegroundColour(tp)
        # Text controls
        if isinstance(child, (wx.TextCtrl, wx.SpinCtrl)):
            bg_editor = hex_to_colour(theme.get('bg_editor', '#FFFFFF'))
            if bg_editor.IsOk():
                try:
                    child.SetBackgroundColour(bg_editor)
                except Exception:
                    pass
            tp = hex_to_colour(theme.get('text_primary', '#000000'))
            if tp.IsOk():
                child.SetForegroundColour(tp)
        # Choice, Radio, Checkbox
        if isinstance(child, (wx.Choice, wx.RadioButton, wx.CheckBox)):
            tp = hex_to_colour(theme.get('text_primary', '#000000'))
            if tp.IsOk():
                child.SetForegroundColour(tp)
        # Recurse
        apply_theme_recursive(child, theme)


# Layout constants
SECTION_MARGIN = 24
SCROLLBAR_MARGIN = 30
SECTION_SPACING = 20


class SettingsDialog(wx.Dialog):
    """Settings configuration dialog with theme, color, and feature options.
    
    Uses ScrolledPanel for reliable cross-platform scrolling with flexible sizers.
    """
    
    def __init__(self, parent, config):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent window
            config: Dict with current settings:
                - theme: Current theme dict
                - dark_mode: bool
                - bg_color_name, text_color_name: Light theme colors
                - dark_bg_color_name, dark_text_color_name: Dark theme colors
                - time_tracker: TimeTracker instance
                - crossprobe_enabled: bool
                - use_visual_editor: bool
                - visual_editor_available: bool
                - beta_markdown: bool
                - beta_table, beta_bom, beta_version_log: bool
                - notes_manager: NotesManager instance
        """
        self._config = config
        self._theme = config['theme']
        
        super().__init__(parent, title="Settings",
                        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        
        # Get screen info and DPI scale
        display = wx.Display(wx.Display.GetFromWindow(parent) if parent else 0)
        screen_rect = display.GetClientArea()
        dpi_scale = get_dpi_scale_factor(parent) if parent else 1.0
        
        # Scale sizes based on DPI
        min_width = int(450 * dpi_scale)
        min_height = int(400 * dpi_scale)  # Enough for buttons to always show
        
        # Calculate preferred size (70% of screen, capped at reasonable max)
        preferred_width = min(int(650 * dpi_scale), int(screen_rect.width * 0.7))
        preferred_height = min(int(750 * dpi_scale), int(screen_rect.height * 0.8))
        
        # Ensure minimum size is not larger than screen
        min_width = min(min_width, screen_rect.width - 50)
        min_height = min(min_height, screen_rect.height - 100)
        
        # Set minimum and preferred sizes
        self.SetSizeHints(minW=min_width, minH=min_height)
        self.SetSize((preferred_width, preferred_height))
        
        # Center on screen
        self.CentreOnScreen()
        
        self.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        # Track selected theme state
        self._selected_theme_dark = config['dark_mode']
        self._save_mode = 'local'
        self._result = None
        
        self._build_ui()
        
        # Apply theme to all children
        apply_theme_recursive(self, self._theme)
    
    def _build_ui(self):
        """Build the dialog UI with ScrolledPanel for robust scrolling."""
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ScrolledPanel for robust cross-platform scrolling
        self._scroll_panel = scrolled.ScrolledPanel(self, style=wx.VSCROLL)
        self._scroll_panel.SetupScrolling(scroll_x=False, scroll_y=True, scrollToTop=True)
        self._scroll_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        # Content sizer inside scroll panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(SECTION_MARGIN)
        
        # Theme Selection Section
        self._build_theme_section(self._scroll_panel, sizer)
        
        # Time Tracking Section
        self._build_time_tracking_section(self._scroll_panel, sizer)
        
        # Cross-Probe Section
        self._build_crossprobe_section(self._scroll_panel, sizer)
        
        # UI Scale Section
        self._build_scale_section(self._scroll_panel, sizer)
        
        # Panel Size Section
        self._build_panel_size_section(self._scroll_panel, sizer)
        
        # Performance Section (Timer Interval)
        self._build_performance_section(self._scroll_panel, sizer)
        
        # Beta Features Section
        self._build_beta_section(self._scroll_panel, sizer)
        
        sizer.AddSpacer(SECTION_SPACING)
        
        # Add right margin for scrollbar breathing space
        outer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outer_sizer.Add(sizer, 1, wx.EXPAND)
        outer_sizer.AddSpacer(SCROLLBAR_MARGIN)
        
        self._scroll_panel.SetSizer(outer_sizer)
        self._scroll_panel.FitInside()
        dialog_sizer.Add(self._scroll_panel, 1, wx.EXPAND)
        
        # Buttons panel
        self._build_buttons(dialog_sizer)
        
        self.SetSizer(dialog_sizer)
    
    def _build_theme_section(self, parent, sizer):
        """Build theme selection section."""
        # Section header
        header = wx.StaticText(parent, label="Select Theme")
        set_label_style(header, self._theme, bold=True, size=12)
        sizer.Add(header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        # Dark Mode Toggle Section
        mode_panel = wx.Panel(parent)
        mode_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Light button
        is_dark = self._config['dark_mode']
        light_bg = self._theme["bg_button"] if is_dark else self._theme["accent_blue"]
        light_fg = self._theme["text_primary"] if is_dark else "#FFFFFF"
        self._light_btn = RoundedButton(
            mode_panel, label="Light", size=(90, 36),
            bg_color=light_bg, fg_color=light_fg, corner_radius=8, font_size=11,
            font_weight=wx.FONTWEIGHT_BOLD if not is_dark else wx.FONTWEIGHT_NORMAL
        )
        self._light_btn.Bind_Click(lambda e: self._on_theme_select(False))
        mode_sizer.Add(self._light_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Dark button
        dark_bg = self._theme["accent_blue"] if is_dark else self._theme["bg_button"]
        dark_fg = "#FFFFFF" if is_dark else self._theme["text_primary"]
        self._dark_btn = RoundedButton(
            mode_panel, label="Dark", size=(90, 36),
            bg_color=dark_bg, fg_color=dark_fg, corner_radius=8, font_size=11,
            font_weight=wx.FONTWEIGHT_BOLD if is_dark else wx.FONTWEIGHT_NORMAL
        )
        self._dark_btn.Bind_Click(lambda e: self._on_theme_select(True))
        mode_sizer.Add(self._dark_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        mode_panel.SetSizer(mode_sizer)
        sizer.Add(mode_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(16)
        
        # Colors panel
        self._colors_panel = wx.Panel(parent)
        self._colors_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self._rebuild_color_options(self._colors_panel, is_dark)
        sizer.Add(self._colors_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 0)
        
        sizer.AddSpacer(SECTION_SPACING)
        self._add_separator(parent, sizer)
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_time_tracking_section(self, parent, sizer):
        """Build time tracking settings section."""
        time_header = wx.StaticText(parent, label="⏱ Time Tracking Options")
        set_label_style(time_header, self._theme, bold=True, size=10)
        sizer.Add(time_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        time_track_panel = wx.Panel(parent)
        time_track_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        time_track_sizer = wx.BoxSizer(wx.VERTICAL)
        
        tracker = self._config.get('time_tracker')
        
        # Row 1: Enable time tracking + time format radio buttons
        row1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._enable_time_tracking = wx.CheckBox(time_track_panel, label="  Enable Time Tracking")
        self._enable_time_tracking.SetValue(tracker.enable_time_tracking if tracker else True)
        self._enable_time_tracking.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        row1_sizer.Add(self._enable_time_tracking, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 30)
        
        self._time_24h = wx.RadioButton(time_track_panel, label="24h", style=wx.RB_GROUP)
        self._time_12h = wx.RadioButton(time_track_panel, label="12h")
        self._time_24h.SetValue(tracker.time_format_24h if tracker else True)
        self._time_12h.SetValue(not (tracker.time_format_24h if tracker else True))
        self._time_24h.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        self._time_12h.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        row1_sizer.Add(self._time_24h, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        row1_sizer.Add(self._time_12h, 0, wx.ALIGN_CENTER_VERTICAL)
        
        time_track_sizer.Add(row1_sizer, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 8)
        
        # Show work diary button
        self._show_work_diary = wx.CheckBox(time_track_panel, label="  Show Work Diary Button")
        self._show_work_diary.SetValue(tracker.show_work_diary_button if tracker else True)
        self._show_work_diary.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        time_track_sizer.Add(self._show_work_diary, 0, wx.LEFT | wx.BOTTOM, 8)
        
        time_track_panel.SetSizer(time_track_sizer)
        sizer.Add(time_track_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(SECTION_SPACING)
        self._add_separator(parent, sizer)
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_crossprobe_section(self, parent, sizer):
        """Build cross-probe settings section."""
        crossprobe_header = wx.StaticText(parent, label="🔗 Smart-Link (Cross-Probe)")
        set_label_style(crossprobe_header, self._theme, bold=True, size=10)
        sizer.Add(crossprobe_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        # Section guideline
        guideline = wx.StaticText(parent, 
            label="Click on component designators or net names in your notes to instantly highlight them on the PCB.")
        guideline.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        guideline.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        sizer.Add(guideline, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        crossprobe_panel = wx.Panel(parent)
        crossprobe_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        crossprobe_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Enable Net Cross-Probe (first)
        self._enable_net_crossprobe = wx.CheckBox(crossprobe_panel, label="  Enable Net Cross-Probe")
        self._enable_net_crossprobe.SetValue(self._config.get('net_crossprobe_enabled', True))
        self._enable_net_crossprobe.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        crossprobe_sizer.Add(self._enable_net_crossprobe, 0, wx.TOP | wx.BOTTOM, 6)
        
        net_desc = wx.StaticText(crossprobe_panel, 
            label="Click on net names (GND, VCC) to highlight pads, tracks & zones.")
        net_desc.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        crossprobe_sizer.Add(net_desc, 0, wx.LEFT | wx.BOTTOM, 24)
        
        # Enable Designator Cross-Probe (second)
        self._enable_crossprobe = wx.CheckBox(crossprobe_panel, label="  Enable Designator Cross-Probe")
        self._enable_crossprobe.SetValue(self._config.get('crossprobe_enabled', True))
        self._enable_crossprobe.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        crossprobe_sizer.Add(self._enable_crossprobe, 0, wx.BOTTOM, 6)
        
        crossprobe_desc = wx.StaticText(crossprobe_panel, 
            label="Click on designators (R1, C5, U3) to highlight component on PCB.")
        crossprobe_desc.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        crossprobe_sizer.Add(crossprobe_desc, 0, wx.LEFT | wx.BOTTOM, 24)
        
        # Custom designator prefixes input
        custom_row = wx.BoxSizer(wx.HORIZONTAL)
        custom_label = wx.StaticText(crossprobe_panel, label="Custom Prefixes:")
        custom_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        custom_row.Add(custom_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self._custom_designators = wx.TextCtrl(crossprobe_panel, size=(200, -1))
        self._custom_designators.SetValue(self._config.get('custom_designators', ''))
        self._custom_designators.SetHint("MOV, PC, NTC, PTC")
        self._custom_designators.SetBackgroundColour(hex_to_colour(self._theme["bg_editor"]))
        self._custom_designators.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        custom_row.Add(self._custom_designators, 0)
        
        crossprobe_sizer.Add(custom_row, 0, wx.BOTTOM, 6)
        
        # Custom prefixes guideline
        custom_hint = wx.StaticText(crossprobe_panel, 
            label="Add non-standard prefixes (comma-separated). Built-in: R, C, L, D, U, Q, J, P, K, SW, LED, IC, TP, FB...")
        custom_hint.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        custom_hint.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        crossprobe_sizer.Add(custom_hint, 0, wx.LEFT | wx.BOTTOM, 4)
        
        crossprobe_panel.SetSizer(crossprobe_sizer)
        sizer.Add(crossprobe_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(SECTION_SPACING)
        self._add_separator(parent, sizer)
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_scale_section(self, parent, sizer):
        """Build UI scale settings section."""
        scale_header = wx.StaticText(parent, label="🔍 UI Scale (High-DPI)")
        set_label_style(scale_header, self._theme, bold=True, size=10)
        sizer.Add(scale_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        scale_panel = wx.Panel(parent)
        scale_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        scale_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Auto checkbox
        self._scale_auto_checkbox = wx.CheckBox(scale_panel, label="  Auto (Use System DPI)")
        current_scale = get_user_scale_factor()
        self._scale_auto_checkbox.SetValue(current_scale is None)
        self._scale_auto_checkbox.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        self._scale_auto_checkbox.Bind(wx.EVT_CHECKBOX, self._on_scale_auto_toggle)
        scale_sizer.Add(self._scale_auto_checkbox, 0, wx.ALL, 10)
        
        # Slider row - ensure consistent alignment
        slider_row = wx.BoxSizer(wx.HORIZONTAL)
        
        min_label = wx.StaticText(scale_panel, label="100%")
        min_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        slider_row.Add(min_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        self._scale_slider = wx.Slider(scale_panel, value=100, minValue=100, maxValue=200, style=wx.SL_HORIZONTAL)
        if current_scale is not None:
            self._scale_slider.SetValue(int(current_scale * 100))
        else:
            system_scale = get_dpi_scale_factor(self)
            self._scale_slider.SetValue(int(system_scale * 100))
        self._scale_slider.Enable(current_scale is not None)
        self._scale_slider.Bind(wx.EVT_SLIDER, self._on_scale_slider_change)
        slider_row.Add(self._scale_slider, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        
        max_label = wx.StaticText(scale_panel, label="200%")
        max_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        slider_row.Add(max_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        
        scale_sizer.Add(slider_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # Current value
        current_factor = get_dpi_scale_factor(self)
        self._scale_value_label = wx.StaticText(scale_panel, label=f"Current: {int(current_factor * 100)}%")
        self._scale_value_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self._scale_value_label.SetForegroundColour(hex_to_colour(self._theme["accent_blue"]))
        scale_sizer.Add(self._scale_value_label, 0, wx.ALIGN_CENTER | wx.TOP, 8)
        
        scale_hint = wx.StaticText(scale_panel, label="Restart KiNotes for changes to take effect")
        scale_hint.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        scale_sizer.Add(scale_hint, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        
        scale_panel.SetSizer(scale_sizer)
        sizer.Add(scale_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_panel_size_section(self, parent, sizer):
        """Build panel size settings section."""
        panel_size_header = wx.StaticText(parent, label="📐 Default Panel Size")
        set_label_style(panel_size_header, self._theme, bold=True, size=10)
        sizer.Add(panel_size_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        panel_size_panel = wx.Panel(parent)
        panel_size_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        panel_size_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Get current settings (use centralized defaults)
        notes_manager = self._config.get('notes_manager')
        current_settings = notes_manager.load_settings() if notes_manager else {}
        current_width = current_settings.get("panel_width", WINDOW_DEFAULTS['panel_width'])
        current_height = current_settings.get("panel_height", WINDOW_DEFAULTS['panel_height'])
        
        size_row = wx.BoxSizer(wx.HORIZONTAL)
        
        width_label = wx.StaticText(panel_size_panel, label="Width:")
        width_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        size_row.Add(width_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        self._panel_width_spin = wx.SpinCtrl(panel_size_panel, min=800, max=2000, initial=max(800, current_width))
        self._panel_width_spin.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        self._panel_width_spin.SetBackgroundColour(hex_to_colour(self._theme["bg_editor"]))
        size_row.Add(self._panel_width_spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        width_px_label = wx.StaticText(panel_size_panel, label="px")
        width_px_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        size_row.Add(width_px_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        
        sep_label = wx.StaticText(panel_size_panel, label="|")
        sep_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        size_row.Add(sep_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        
        height_label = wx.StaticText(panel_size_panel, label="Height:")
        height_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        size_row.Add(height_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        self._panel_height_spin = wx.SpinCtrl(panel_size_panel, min=600, max=2000, initial=max(600, current_height))
        self._panel_height_spin.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        self._panel_height_spin.SetBackgroundColour(hex_to_colour(self._theme["bg_editor"]))
        size_row.Add(self._panel_height_spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        height_px_label = wx.StaticText(panel_size_panel, label="px")
        height_px_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        size_row.Add(height_px_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        panel_size_sizer.Add(size_row, 0, wx.ALL, 10)
        
        panel_size_hint = wx.StaticText(panel_size_panel, 
            label="Restart KiNotes for size changes to take effect (Min: 800×600)")
        panel_size_hint.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        panel_size_sizer.Add(panel_size_hint, 0, wx.LEFT | wx.BOTTOM, 10)
        
        panel_size_panel.SetSizer(panel_size_sizer)
        sizer.Add(panel_size_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(SECTION_SPACING)
        self._add_separator(parent, sizer)
        sizer.AddSpacer(SECTION_SPACING)
        
        # PDF Export Format Section
        self._build_pdf_format_section(self._scroll_panel, sizer)
    
    def _build_performance_section(self, parent, sizer):
        """Build performance settings section (timer interval)."""
        perf_header = wx.StaticText(parent, label="⚡ Performance")
        set_label_style(perf_header, self._theme, bold=True, size=10)
        sizer.Add(perf_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        perf_panel = wx.Panel(parent)
        perf_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        perf_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Get current settings
        notes_manager = self._config.get('notes_manager')
        current_settings = notes_manager.load_settings() if notes_manager else {}
        current_interval_ms = current_settings.get('timer_interval_ms', PERFORMANCE_DEFAULTS['timer_interval_ms'])
        current_interval_sec = current_interval_ms // 1000  # Convert to seconds for UI
        
        # Timer interval row
        timer_row = wx.BoxSizer(wx.HORIZONTAL)
        
        timer_label = wx.StaticText(perf_panel, label="Auto-save interval:")
        timer_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        timer_row.Add(timer_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # SpinCtrl for interval (3-60 seconds)
        min_sec = PERFORMANCE_DEFAULTS['timer_min_ms'] // 1000
        max_sec = PERFORMANCE_DEFAULTS['timer_max_ms'] // 1000
        self._timer_interval_spin = wx.SpinCtrl(perf_panel, min=min_sec, max=max_sec, 
                                                 initial=max(min_sec, min(current_interval_sec, max_sec)))
        self._timer_interval_spin.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        self._timer_interval_spin.SetBackgroundColour(hex_to_colour(self._theme["bg_editor"]))
        timer_row.Add(self._timer_interval_spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        sec_label = wx.StaticText(perf_panel, label="seconds")
        sec_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        timer_row.Add(sec_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        perf_sizer.Add(timer_row, 0, wx.ALL, 10)
        
        perf_hint = wx.StaticText(perf_panel, 
            label="Higher values = better performance, lower = faster saves (Min: 3s)")
        perf_hint.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        perf_sizer.Add(perf_hint, 0, wx.LEFT | wx.BOTTOM, 10)
        
        perf_panel.SetSizer(perf_sizer)
        sizer.Add(perf_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(SECTION_SPACING)
        self._add_separator(parent, sizer)
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_pdf_format_section(self, parent, sizer):
        """Build PDF export format settings section."""
        pdf_header = wx.StaticText(parent, label="💾 PDF Export Format")
        set_label_style(pdf_header, self._theme, bold=True, size=10)
        sizer.Add(pdf_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        pdf_panel = wx.Panel(parent)
        pdf_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        pdf_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Get current setting from config (passed from main_panel)
        current_format = self._config.get('pdf_format', 'markdown')
        is_visual = (current_format == 'visual')
        
        # Radio buttons for PDF format
        self._pdf_markdown_radio = wx.RadioButton(pdf_panel, label="  📝 Markdown (Plain text, lightweight)", style=wx.RB_GROUP)
        self._pdf_markdown_radio.SetValue(not is_visual)
        self._pdf_markdown_radio.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        pdf_sizer.Add(self._pdf_markdown_radio, 0, wx.ALL, 8)
        
        self._pdf_visual_radio = wx.RadioButton(pdf_panel, label="  🎨 Formatted (Preserves bold, italic, lists)")
        self._pdf_visual_radio.SetValue(is_visual)
        self._pdf_visual_radio.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        pdf_sizer.Add(self._pdf_visual_radio, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Requirement note with help link
        req_row = wx.BoxSizer(wx.HORIZONTAL)
        req_note = wx.StaticText(pdf_panel, 
            label="       ℹ️ Formatted export requires 'reportlab'. Install: pip install reportlab")
        req_note.SetForegroundColour(hex_to_colour(self._theme.get("text_secondary", "#888888")))
        req_note.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        req_row.Add(req_note, 0, wx.ALIGN_CENTER_VERTICAL)
        
        help_link = wx.adv.HyperlinkCtrl(pdf_panel, label="  ❓ Help", url="https://pcbtools.xyz/tools/kinotes#requirements")
        help_link.SetNormalColour(hex_to_colour(self._theme.get("accent_blue", "#2196F3")))
        help_link.SetHoverColour(hex_to_colour(self._theme.get("accent_blue", "#2196F3")))
        req_row.Add(help_link, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        
        pdf_sizer.Add(req_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        pdf_panel.SetSizer(pdf_sizer)
        sizer.Add(pdf_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        
        sizer.AddSpacer(SECTION_SPACING)
        self._add_separator(parent, sizer)
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_beta_section(self, parent, sizer):
        """Build beta features section."""
        beta_header = wx.StaticText(parent, label="🧪 Beta Features (Experimental)")
        set_label_style(beta_header, self._theme, bold=True, size=10)
        sizer.Add(beta_header, 0, wx.LEFT | wx.BOTTOM, SECTION_MARGIN)
        
        beta_panel = wx.Panel(parent)
        beta_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        beta_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._beta_table_cb = wx.CheckBox(beta_panel, label="  📊 Insert Table (Visual Editor toolbar)")
        self._beta_table_cb.SetValue(self._config.get('beta_table', False))
        self._beta_table_cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        beta_sizer.Add(self._beta_table_cb, 0, wx.ALL, 8)
        
        self._beta_markdown_cb = wx.CheckBox(beta_panel, label="  📝 Markdown Editor Mode")
        self._beta_markdown_cb.SetValue(self._config.get('beta_markdown', False))
        self._beta_markdown_cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        beta_sizer.Add(self._beta_markdown_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        self._beta_bom_cb = wx.CheckBox(beta_panel, label="  📋 BOM Tab (Bill of Materials)")
        self._beta_bom_cb.SetValue(self._config.get('beta_bom', False))
        self._beta_bom_cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        beta_sizer.Add(self._beta_bom_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        self._beta_version_log_cb = wx.CheckBox(beta_panel, label="  📜 Changelog Tab (Version Log)")
        self._beta_version_log_cb.SetValue(self._config.get('beta_version_log', False))
        self._beta_version_log_cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        beta_sizer.Add(self._beta_version_log_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Hidden checkbox for backward compat - always enabled now
        self._beta_net_linker_cb = wx.CheckBox(beta_panel, label="")
        self._beta_net_linker_cb.SetValue(True)  # Always on since it's now a main feature
        self._beta_net_linker_cb.Hide()  # Hidden from UI
        self._beta_net_linker_cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        beta_sizer.Add(self._beta_net_linker_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Debug panel activation
        self._beta_debug_panel_cb = wx.CheckBox(beta_panel, label="  🪛 Debug Panel (Event Log, Beta)")
        self._beta_debug_panel_cb.SetValue(self._config.get('beta_debug_panel', False))
        self._beta_debug_panel_cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        beta_sizer.Add(self._beta_debug_panel_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Module checkboxes are now in the main debug panel itself
        self._debug_module_cbs = {}  # Keep empty dict for backward compatibility
        
        beta_warning = wx.StaticText(beta_panel, 
            label="⚠ Experimental features may be unstable. Save project before activation. Restart required after changes.")
        beta_warning.SetForegroundColour(wx.Colour(220, 53, 69))  # Bootstrap danger red
        beta_warning.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        beta_sizer.Add(beta_warning, 0, wx.ALL, 10)
        
        beta_panel.SetSizer(beta_sizer)
        sizer.Add(beta_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        sizer.AddSpacer(SECTION_SPACING)
    
    def _build_buttons(self, dialog_sizer):
        """Build dialog buttons with modern dropdown Save button.
        
        Industry standard: Buttons in a fixed panel at bottom, always visible,
        separated from scrolling content with a line.
        """
        # Separator line above buttons
        separator = wx.StaticLine(self)
        dialog_sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        btn_panel = wx.Panel(self)
        btn_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        # Fixed height for button area - ensures it's always visible
        btn_height = 70  # Generous space for buttons + padding
        btn_panel.SetMinSize((-1, btn_height))
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Reset to Defaults button (left side)
        reset_btn = RoundedButton(
            btn_panel, label="↻ Reset Defaults", size=(130, 40),
            bg_color=self._theme["accent_red"], fg_color="#FFFFFF",
            corner_radius=10, font_size=10, font_weight=wx.FONTWEIGHT_NORMAL
        )
        reset_btn.Bind_Click(lambda e: self._on_reset_defaults())
        reset_btn.SetToolTip("Reset all settings to factory defaults")
        btn_sizer.Add(reset_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, SECTION_MARGIN)
        
        btn_sizer.AddStretchSpacer()
        
        cancel_btn = RoundedButton(
            btn_panel, label="Cancel", size=(90, 40),
            bg_color=self._theme["bg_button"], fg_color=self._theme["text_primary"],
            corner_radius=10, font_size=11, font_weight=wx.FONTWEIGHT_NORMAL
        )
        cancel_btn.Bind_Click(lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.Add(cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Modern split button: "Save" + dropdown arrow
        split_panel = wx.Panel(btn_panel)
        split_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        split_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Main Save button (saves locally by default)
        self._save_main_btn = RoundedButton(
            split_panel, label="Save", size=(80, 40),
            bg_color=self._theme["accent_blue"], fg_color="#FFFFFF",
            corner_radius=10, font_size=11, font_weight=wx.FONTWEIGHT_BOLD,
            corner_flags=0x01 | 0x04  # Round left corners only
        )
        self._save_main_btn.Bind_Click(lambda e: self._on_save_locally())
        self._save_main_btn.SetToolTip("Save settings for this project")
        split_sizer.Add(self._save_main_btn, 0)
        
        # Dropdown arrow button
        self._save_dropdown_btn = RoundedButton(
            split_panel, label="▼", size=(32, 40),
            bg_color=self._theme["accent_blue"], fg_color="#FFFFFF",
            corner_radius=10, font_size=9, font_weight=wx.FONTWEIGHT_NORMAL,
            corner_flags=0x02 | 0x08  # Round right corners only
        )
        self._save_dropdown_btn.Bind_Click(lambda e: self._show_save_menu(e))
        self._save_dropdown_btn.SetToolTip("More save options")
        split_sizer.Add(self._save_dropdown_btn, 0, wx.LEFT, 1)
        
        split_panel.SetSizer(split_sizer)
        btn_sizer.Add(split_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, SCROLLBAR_MARGIN)
        
        btn_panel.SetSizer(btn_sizer)
        dialog_sizer.Add(btn_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, SECTION_MARGIN)
    
    def _show_save_menu(self, event):
        """Show dropdown menu with save options."""
        menu = wx.Menu()
        
        local_item = menu.Append(wx.ID_ANY, "💾  Save Locally\tThis project only")
        global_item = menu.Append(wx.ID_ANY, "🌐  Save Globally\tDefault for all projects")
        
        self.Bind(wx.EVT_MENU, lambda e: self._on_save_locally(), local_item)
        self.Bind(wx.EVT_MENU, lambda e: self._on_save_globally(), global_item)
        
        # Position menu below the dropdown button
        btn = self._save_dropdown_btn
        pos = btn.GetScreenPosition()
        size = btn.GetSize()
        self.PopupMenu(menu, self.ScreenToClient(wx.Point(pos.x - 100, pos.y + size.y)))
        menu.Destroy()
    
    def _on_save_locally(self):
        """Save settings locally (project-specific) and close dialog."""
        self._save_mode = 'local'
        self.EndModal(wx.ID_OK)
    
    def _on_save_globally(self):
        """Save settings globally (user-wide) and close dialog."""
        self._save_mode = 'global'
        self.EndModal(wx.ID_OK)
    
    def _on_reset_defaults(self):
        """Reset all settings to factory defaults."""
        # Confirm with user
        dlg = wx.MessageDialog(
            self,
            "This will reset ALL settings to factory defaults.\n\n"
            "Your notes and todos will NOT be affected.\n\n"
            "Continue?",
            "Reset to Defaults",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
        )
        
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()
        
        # Reset theme
        self._selected_theme_dark = DEFAULTS['dark_mode']
        self._on_theme_select(self._selected_theme_dark)
        
        # Reset time tracking
        self._enable_time_tracking.SetValue(TIME_TRACKER_DEFAULTS['enable_time_tracking'])
        self._time_24h.SetValue(TIME_TRACKER_DEFAULTS['time_format_24h'])
        self._show_work_diary.SetValue(TIME_TRACKER_DEFAULTS['show_work_diary_button'])
        
        # Reset cross-probe
        self._enable_crossprobe.SetValue(DEFAULTS['crossprobe_enabled'])
        self._enable_net_crossprobe.SetValue(DEFAULTS['net_crossprobe_enabled'])
        self._custom_designators.SetValue('')
        
        # Reset UI scale to auto
        self._scale_auto_checkbox.SetValue(True)
        self._scale_slider.SetValue(100)
        self._scale_slider.Disable()
        self._scale_value_label.SetLabel("100%")
        
        # Reset panel size
        self._panel_width_spin.SetValue(WINDOW_DEFAULTS['panel_width'])
        self._panel_height_spin.SetValue(WINDOW_DEFAULTS['panel_height'])
        
        # Reset timer interval
        self._timer_interval_spin.SetValue(PERFORMANCE_DEFAULTS['timer_interval_ms'] // 1000)
        
        # Reset beta features (all disabled except net_linker)
        self._beta_table_cb.SetValue(BETA_DEFAULTS['beta_table'])
        self._beta_markdown_cb.SetValue(BETA_DEFAULTS['beta_markdown'])
        self._beta_bom_cb.SetValue(BETA_DEFAULTS['beta_bom'])
        self._beta_version_log_cb.SetValue(BETA_DEFAULTS['beta_version_log'])
        self._beta_net_linker_cb.SetValue(BETA_DEFAULTS['beta_net_linker'])
        self._beta_debug_panel_cb.SetValue(BETA_DEFAULTS['beta_debug_panel'])
        
        # Reset PDF format
        self._pdf_markdown_radio.SetValue(True)
        self._pdf_visual_radio.SetValue(False)
        
        # Notify user
        wx.MessageBox(
            "Settings reset to defaults.\n\nClick 'Save' to apply changes.",
            "Reset Complete",
            wx.OK | wx.ICON_INFORMATION
        )
    
    def get_save_mode(self) -> str:
        """Return the save mode: 'local' or 'global'."""
        return getattr(self, '_save_mode', 'local')
    
    def _add_separator(self, parent, sizer):
        """Add a horizontal separator line with consistent margins."""
        sep = wx.StaticLine(parent)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, SECTION_MARGIN)
    
    def _on_theme_select(self, is_dark):
        """Handle theme button selection."""
        self._selected_theme_dark = is_dark
        
        if is_dark:
            self._dark_btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
            self._light_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        else:
            self._light_btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
            self._dark_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        
        self._rebuild_color_options(self._colors_panel, is_dark)
        self.Layout()
    
    def _rebuild_color_options(self, panel, is_dark):
        """Rebuild color options based on theme."""
        for child in panel.GetChildren():
            child.Destroy()
        
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        theme_name = "Dark" if is_dark else "Light"
        header = wx.StaticText(panel, label=f"{theme_name} Theme Colors")
        set_label_style(header, self._theme, bold=True, size=10)
        panel_sizer.Add(header, 0, wx.LEFT, SECTION_MARGIN)
        panel_sizer.AddSpacer(12)
        
        color_row = wx.BoxSizer(wx.HORIZONTAL)
        
        bg_label = wx.StaticText(panel, label="Background:")
        bg_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        bg_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        color_row.Add(bg_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        if is_dark:
            dark_bg_choices = list(DARK_BACKGROUND_COLORS.keys())
            self._bg_choice = wx.Choice(panel, choices=dark_bg_choices)
            dark_bg_name = self._config.get('dark_bg_color_name', 'Charcoal')
            self._bg_choice.SetSelection(dark_bg_choices.index(dark_bg_name) if dark_bg_name in dark_bg_choices else 0)
        else:
            bg_choices = list(BACKGROUND_COLORS.keys())
            self._bg_choice = wx.Choice(panel, choices=bg_choices)
            bg_name = self._config.get('bg_color_name', 'Ivory Paper')
            self._bg_choice.SetSelection(bg_choices.index(bg_name) if bg_name in bg_choices else 0)
        
        self._bg_choice.SetMinSize((140, -1))
        color_row.Add(self._bg_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 30)
        
        txt_label = wx.StaticText(panel, label="Text:")
        txt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        color_row.Add(txt_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        if is_dark:
            dark_txt_choices = list(DARK_TEXT_COLORS.keys())
            self._txt_choice = wx.Choice(panel, choices=dark_txt_choices)
            dark_txt_name = self._config.get('dark_text_color_name', 'Pure White')
            self._txt_choice.SetSelection(dark_txt_choices.index(dark_txt_name) if dark_txt_name in dark_txt_choices else 0)
        else:
            txt_choices = list(TEXT_COLORS.keys())
            self._txt_choice = wx.Choice(panel, choices=txt_choices)
            txt_name = self._config.get('text_color_name', 'Carbon Black')
            self._txt_choice.SetSelection(txt_choices.index(txt_name) if txt_name in txt_choices else 0)
        
        self._txt_choice.SetMinSize((140, -1))
        color_row.Add(self._txt_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        
        panel_sizer.Add(color_row, 0, wx.LEFT | wx.RIGHT, SECTION_MARGIN)
        panel.SetSizer(panel_sizer)
        panel.Layout()
    
    def _on_scale_auto_toggle(self, event):
        """Handle auto scale checkbox toggle."""
        is_auto = self._scale_auto_checkbox.GetValue()
        self._scale_slider.Enable(not is_auto)
        
        if is_auto:
            system_scale = get_dpi_scale_factor(self)
            self._scale_slider.SetValue(int(system_scale * 100))
            self._scale_value_label.SetLabel(f"Current: {int(system_scale * 100)}% (Auto)")
        else:
            slider_val = self._scale_slider.GetValue()
            self._scale_value_label.SetLabel(f"Current: {slider_val}%")
    
    def _on_scale_slider_change(self, event):
        """Handle scale slider value change."""
        slider_val = self._scale_slider.GetValue()
        self._scale_value_label.SetLabel(f"Current: {slider_val}%")
    
    def get_result(self):
        """
        Get settings result after dialog is closed.
        
        Returns:
            Dict with all settings values, or None if cancelled
        """
        if self._selected_theme_dark:
            dark_bg_choices = list(DARK_BACKGROUND_COLORS.keys())
            dark_txt_choices = list(DARK_TEXT_COLORS.keys())
            bg_color_name = dark_bg_choices[self._bg_choice.GetSelection()]
            text_color_name = dark_txt_choices[self._txt_choice.GetSelection()]
        else:
            bg_choices = list(BACKGROUND_COLORS.keys())
            txt_choices = list(TEXT_COLORS.keys())
            bg_color_name = bg_choices[self._bg_choice.GetSelection()]
            text_color_name = txt_choices[self._txt_choice.GetSelection()]
        
        return {
            'dark_mode': self._selected_theme_dark,
            'bg_color_name': bg_color_name if not self._selected_theme_dark else self._config.get('bg_color_name', 'Ivory Paper'),
            'text_color_name': text_color_name if not self._selected_theme_dark else self._config.get('text_color_name', 'Carbon Black'),
            'dark_bg_color_name': bg_color_name if self._selected_theme_dark else self._config.get('dark_bg_color_name', 'Charcoal'),
            'dark_text_color_name': text_color_name if self._selected_theme_dark else self._config.get('dark_text_color_name', 'Pure White'),
            'enable_time_tracking': self._enable_time_tracking.GetValue(),
            'time_format_24h': self._time_24h.GetValue(),
            'show_work_diary': self._show_work_diary.GetValue(),
            'use_visual_editor': self._config.get('use_visual_editor', True),
            'crossprobe_enabled': self._enable_crossprobe.GetValue(),
            'net_crossprobe_enabled': self._enable_net_crossprobe.GetValue(),
            'custom_designators': self._custom_designators.GetValue().strip(),
            'scale_auto': self._scale_auto_checkbox.GetValue(),
            'scale_factor': None if self._scale_auto_checkbox.GetValue() else self._scale_slider.GetValue() / 100.0,
            'panel_width': self._panel_width_spin.GetValue(),
            'panel_height': self._panel_height_spin.GetValue(),
            'timer_interval_ms': self._timer_interval_spin.GetValue() * 1000,  # Convert seconds to ms
            'beta_table': self._beta_table_cb.GetValue(),
            'beta_markdown': self._beta_markdown_cb.GetValue(),
            'beta_bom': self._beta_bom_cb.GetValue(),
            'beta_version_log': self._beta_version_log_cb.GetValue(),
            'beta_net_linker': self._beta_net_linker_cb.GetValue(),
            'beta_debug_panel': self._beta_debug_panel_cb.GetValue(),
            # Module filters are now in main debug panel, preserve existing settings
            'debug_modules': self._config.get('debug_modules', {'save': False, 'net': False, 'designator': False}),
            'pdf_format': 'visual' if self._pdf_visual_radio.GetValue() else 'markdown',
        }


def show_settings_dialog(parent, config):
    """
    Show settings dialog and return result.
    
    Args:
        parent: Parent window
        config: Current settings configuration dict
    
    Returns:
        Tuple of (settings_dict, save_mode) if OK clicked, (None, None) if cancelled.
        save_mode is 'local' or 'global'.
    """
    dlg = SettingsDialog(parent, config)
    result = None
    save_mode = None
    
    if dlg.ShowModal() == wx.ID_OK:
        result = dlg.get_result()
        save_mode = dlg.get_save_mode()
    
    dlg.Destroy()
    return result, save_mode
