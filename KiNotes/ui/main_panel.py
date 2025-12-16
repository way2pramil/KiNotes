"""
KiNotes Main Panel - Modern UI with Dark Theme Toggle
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
User-selectable background and text colors with dark mode
Time tracking with per-task stopwatch and work diary export
Dual-Mode Note Editor: Visual (WYSIWYG) or Markdown
"""
import wx
import wx.lib.scrolledpanel as scrolled
import wx.richtext as rt
import os
import sys
import datetime
import json
import time
import re
import fnmatch

# Import centralized defaults - handle both KiCad plugin and standalone context
try:
    from ..core.defaultsConfig import (
        DEFAULTS, BETA_DEFAULTS, WINDOW_DEFAULTS, DEBUG_MODULES,
        PERFORMANCE_DEFAULTS, debug_print
    )
except ImportError:
    from core.defaultsConfig import (
        DEFAULTS, BETA_DEFAULTS, WINDOW_DEFAULTS, DEBUG_MODULES,
        PERFORMANCE_DEFAULTS, debug_print
    )

# Visual Note Editor for WYSIWYG mode
try:
    from .visual_editor import VisualNoteEditor
    from .markdown_converter import MarkdownToRichText, RichTextToMarkdown
    VISUAL_EDITOR_AVAILABLE = True
except ImportError:
    VISUAL_EDITOR_AVAILABLE = False

# Markdown Editor for power user mode
try:
    from .markdown_editor import MarkdownEditor
    MARKDOWN_EDITOR_AVAILABLE = True
except ImportError:
    MARKDOWN_EDITOR_AVAILABLE = False

# Import extracted modules
from .themes import (
    DARK_THEME, LIGHT_THEME,
    BACKGROUND_COLORS, TEXT_COLORS,
    DARK_BACKGROUND_COLORS, DARK_TEXT_COLORS,
    hex_to_colour
)

from .scaling import (
    get_dpi_scale_factor,
    scale_size,
    scale_font_size,
    get_user_scale_factor,
    set_user_scale_factor,
    UI_SCALE_OPTIONS
)

from .time_tracker import TimeTracker

from .components import (
    RoundedButton,
    PlayPauseButton,
    ToggleSwitch,
    Icons
)

from .dialogs import show_settings_dialog, show_about_dialog
from .tabs import VersionLogTabMixin, BomTabMixin, TodoTabMixin

# Debug logger panel (AI-friendly, modular)
from .debug_event_logger import (
    DebugEventLogger,
    DebugEventPanel,
    EventLevel,
    get_debug_logger,
)

# Import net linker for beta net cross-probe feature
try:
    from ..core.net_linker import NetLinker
    HAS_NET_LINKER = True
except ImportError:
    HAS_NET_LINKER = False

# Import net cache manager (centralized cache + board change detection)
try:
    from ..core.net_cache_manager import get_net_cache_manager
    HAS_NET_CACHE_MANAGER = True
except ImportError:
    HAS_NET_CACHE_MANAGER = False

# Import crash safety manager (optional)
try:
    from ..core.crash_safety import CrashSafetyManager, PLUGIN_VERSION
    HAS_CRASH_SAFETY = True
except ImportError:
    HAS_CRASH_SAFETY = False
    CrashSafetyManager = None


# ============================================================
# MAIN PANEL
# ============================================================
class KiNotesMainPanel(TodoTabMixin, VersionLogTabMixin, BomTabMixin, wx.Panel):
    """Main panel with tabs, color picker, dark mode toggle, and bottom action buttons."""
    
    def __init__(self, parent, notes_manager, designator_linker, metadata_extractor, pdf_exporter):
        wx.Panel.__init__(self, parent)
        
        self.notes_manager = notes_manager
        self.designator_linker = designator_linker
        self.metadata_extractor = metadata_extractor
        self.pdf_exporter = pdf_exporter
        
        self._auto_save_timer = None
        self._modified = False
        self._todo_items = []
        self._todo_id_counter = 0
        
        # Version log data
        self._version_log_items = []
        self._version_log_id_counter = 0
        self._current_version = DEFAULTS['current_version']
        self._current_tab = 0
        
        # Time tracking system
        self.time_tracker = TimeTracker()
        self._timer_update_tick = 0
        
        # Theme settings (from centralized defaults)
        self._dark_mode = DEFAULTS['dark_mode']
        self._bg_color_name = DEFAULTS['bg_color_name']
        self._text_color_name = DEFAULTS['text_color_name']
        self._dark_bg_color_name = DEFAULTS['dark_bg_color_name']
        self._dark_text_color_name = DEFAULTS['dark_text_color_name']
        self._use_visual_editor = DEFAULTS['use_visual_editor'] and VISUAL_EDITOR_AVAILABLE
        self._crossprobe_enabled = DEFAULTS['crossprobe_enabled']
        
        # Beta features (from centralized defaults)
        self._beta_features_enabled = BETA_DEFAULTS['beta_features_enabled']
        self._beta_markdown = BETA_DEFAULTS['beta_markdown']
        self._beta_bom = BETA_DEFAULTS['beta_bom']
        self._beta_version_log = BETA_DEFAULTS['beta_version_log']
        self._beta_net_linker = BETA_DEFAULTS['beta_net_linker']
        self._beta_debug_panel = BETA_DEFAULTS['beta_debug_panel']
        self._debug_modules = DEBUG_MODULES.copy()
        self._pdf_format = DEFAULTS['pdf_format']
        
        # Initialize net cache manager (centralized net caching + board change detection)
        self.net_cache_manager = get_net_cache_manager() if HAS_NET_CACHE_MANAGER else None
        
        # Initialize net linker (deprecated; use net_cache_manager instead)
        # Don't create linker at init—it requires a live KiCad board (will be created on demand when clicking nets)
        self.net_linker = None
        # Beta flag defaults to True; linker will be lazy-loaded when needed
        debug_print(f"[KiNotes] Net cache manager available: {bool(self.net_cache_manager)}. beta={self._beta_net_linker}")
        
        # Load timer interval from settings (default from PERFORMANCE_DEFAULTS)
        self._timer_interval_ms = PERFORMANCE_DEFAULTS['timer_interval_ms']

        # Debug logger (shared singleton)
        self.debug_logger: DebugEventLogger = get_debug_logger()
        
        # Crash safety manager (initialized after UI is ready)
        self.crash_safety = None
        self._safe_mode_active = False
        self._version_bumped = False
        
        self._load_color_settings()
        
        self._theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        self.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        debug_print(f"[KiNotes SIZE] MainPanel init, parent size: {parent.GetSize()}")
        
        try:
            self._init_ui()
            self._load_all_data()
            self._start_auto_save_timer()
            
            # Initialize crash safety AFTER UI is ready
            self._init_crash_safety()
            
            # Show recovery dialog if crash detected
            if self._safe_mode_active:
                wx.CallAfter(self._show_crash_recovery_dialog)
        except Exception as e:
            import traceback
            debug_print("KiNotes UI init error: " + str(e))
            traceback.print_exc()
    
    def _load_color_settings(self):
        """Load saved color and editor settings."""
        try:
            settings = self.notes_manager.load_settings()
            if settings:
                self._bg_color_name = settings.get("bg_color", "Ivory Paper")
                self._text_color_name = settings.get("text_color", "Carbon Black")
                self._dark_bg_color_name = settings.get("dark_bg_color", "Charcoal")
                self._dark_text_color_name = settings.get("dark_text_color", "Pure White")
                self._dark_mode = settings.get("dark_mode", False)
                # Visual Editor setting - default True if available
                self._use_visual_editor = settings.get("use_visual_editor", VISUAL_EDITOR_AVAILABLE)
                # Only use visual if available
                if self._use_visual_editor and not VISUAL_EDITOR_AVAILABLE:
                    self._use_visual_editor = False
                # UI Scale factor - None means auto
                ui_scale = settings.get("ui_scale_factor", None)
                set_user_scale_factor(ui_scale)
                # Cross-probe setting - default enabled
                self._crossprobe_enabled = settings.get("crossprobe_enabled", True)
                # Custom designator prefixes
                self._custom_designators = settings.get("custom_designators", "")
                if self.designator_linker and self._custom_designators:
                    self.designator_linker.set_custom_prefixes(self._custom_designators)
                # Net cross-probe - now a main feature (enabled by default)
                # Support both new and legacy setting names for backward compat
                self._net_crossprobe_enabled = settings.get("net_crossprobe_enabled", 
                    settings.get("beta_net_linker", True))
                # Beta features - default disabled
                self._beta_features_enabled = settings.get("beta_features_enabled", False)
                # Individual beta features
                self._beta_markdown = settings.get("beta_markdown", False)
                self._beta_bom = settings.get("beta_bom", False)
                self._beta_version_log = settings.get("beta_version_log", False)
                # Legacy: keep _beta_net_linker as alias for backward compat
                self._beta_net_linker = self._net_crossprobe_enabled
                self._beta_debug_panel = settings.get("beta_debug_panel", False)
                self._debug_modules = settings.get("debug_modules", self._debug_modules)
                # Ensure required module keys exist
                for key in ("save", "net", "designator"):
                    if key not in self._debug_modules:
                        self._debug_modules[key] = False
                # PDF export format setting
                self._pdf_format = settings.get("pdf_format", "markdown")
        except:
            pass
    
    def _handle_crash_and_version_check(self):
        """Handle crash detection and version bump checks at startup."""
        try:
            # Check for version bump
            version_changed, old_version, new_version = self.crash_safety.check_version()
            
            if version_changed and old_version:
                debug_print(f"[KiNotes] Version bump: {old_version} → {new_version}")
                self._version_bumped = True
                # Create backup before any changes
                backup_ok = self.crash_safety.backup_on_version_bump()
                if backup_ok:
                    debug_print(f"[KiNotes] Version backup created: {old_version} → {new_version}")
                else:
                    debug_print("[KiNotes] Version backup failed")
            
            # Mark startup and check for crash
            crashed = self.crash_safety.mark_startup()
            
            if crashed:
                debug_print("[KiNotes] ⚠ Previous session crashed")
                
                # Check if safe mode should be enabled
                if self.crash_safety.should_use_safe_mode():
                    self._safe_mode_active = True
                    safe_config = self.crash_safety.get_safe_mode_config()
                    # Apply safe configuration
                    self._use_visual_editor = safe_config.get('use_visual_editor', False)
                    self._beta_features_enabled = safe_config.get('beta_features_enabled', False)
                    self._beta_markdown = safe_config.get('beta_markdown', True)
                    self._beta_bom = safe_config.get('beta_bom', False)
                    self._beta_version_log = safe_config.get('beta_version_log', False)
                    self._beta_net_linker = safe_config.get('beta_net_linker', False)
                    self._beta_debug_panel = safe_config.get('beta_debug_panel', False)
                    debug_print("[KiNotes] Safe mode activated (beta features disabled)")
            
            # Update version file
            self.crash_safety.update_version()
            
        except Exception as e:
            debug_print(f"[KiNotes] Error in crash/version check: {e}")
            import traceback
            traceback.print_exc()
    
    def _init_crash_safety(self):
        """Initialize crash safety after UI is ready (non-blocking)."""
        if not HAS_CRASH_SAFETY or self.crash_safety is not None:
            return
        
        try:
            self.crash_safety = CrashSafetyManager(self.notes_manager.notes_dir)
            self._handle_crash_and_version_check()
            debug_print("[KiNotes] Crash safety initialized")
        except Exception as e:
            debug_print(f"[KiNotes] Crash safety init failed (non-critical): {e}")
            self.crash_safety = None

    def _save_color_settings(self, save_mode='local'):
        """
        Save color and editor settings.
        
        Args:
            save_mode: 'local' for project-specific, 'global' for user-wide defaults
        """
        try:
            settings = self.notes_manager.load_settings() or {}
            settings.update({
                "bg_color": self._bg_color_name,
                "text_color": self._text_color_name,
                "dark_bg_color": self._dark_bg_color_name,
                "dark_text_color": self._dark_text_color_name,
                "dark_mode": self._dark_mode,
                "use_visual_editor": self._use_visual_editor,
                "ui_scale_factor": get_user_scale_factor(),
                "crossprobe_enabled": self._crossprobe_enabled,
                "net_crossprobe_enabled": getattr(self, '_net_crossprobe_enabled', True),
                "custom_designators": getattr(self, '_custom_designators', ''),
                "beta_features_enabled": self._beta_features_enabled,
                "beta_markdown": self._beta_markdown,
                "beta_bom": self._beta_bom,
                "beta_version_log": self._beta_version_log,
                "beta_debug_panel": self._beta_debug_panel,
                "debug_modules": self._debug_modules,
                "pdf_format": getattr(self, '_pdf_format', 'markdown'),
            })
            # Save panel size from instance variables (set by settings dialog)
            if hasattr(self, '_panel_width') and self._panel_width:
                settings["panel_width"] = self._panel_width
            if hasattr(self, '_panel_height') and self._panel_height:
                settings["panel_height"] = self._panel_height
            
            # Save based on mode
            if save_mode == 'global':
                # Save to global settings (user-wide defaults)
                self.notes_manager.save_settings_globally(settings)
                debug_print("[KiNotes] Settings saved globally")
            else:
                # Save to local project settings
                self.notes_manager.save_settings(settings)
                debug_print("[KiNotes] Settings saved locally")
        except Exception as e:
            debug_print(f"[KiNotes] Error saving settings: {e}")

    def _get_editor_bg(self):
        if self._dark_mode:
            return hex_to_colour(DARK_BACKGROUND_COLORS.get(self._dark_bg_color_name, "#1C1C1E"))
        return hex_to_colour(BACKGROUND_COLORS.get(self._bg_color_name, "#FFFDF5"))
    
    def _get_editor_text(self):
        if self._dark_mode:
            return hex_to_colour(DARK_TEXT_COLORS.get(self._dark_text_color_name, "#FFFFFF"))
        return hex_to_colour(TEXT_COLORS.get(self._text_color_name, "#2B2B2B"))
    
    def _init_ui(self):
        """Initialize UI with new layout."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === TOP BAR: Tabs + Import + Settings ===
        self.top_bar = self._create_top_bar()
        main_sizer.Add(self.top_bar, 0, wx.EXPAND)
        
        # === CONTENT AREA ===
        self.content_panel = wx.Panel(self)
        # Use editor bg color to match notes panel and avoid gray strip
        self.content_panel.SetBackgroundColour(self._get_editor_bg())
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create all tab panels
        self.notes_panel = self._create_notes_tab(self.content_panel)
        self.todo_panel = self._create_todo_tab(self.content_panel)
        self.bom_panel = self._create_bom_tab(self.content_panel)
        self.version_log_panel = self._create_version_log_tab(self.content_panel)
        
        self.content_sizer.Add(self.notes_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.todo_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.bom_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.version_log_panel, 1, wx.EXPAND)
        
        self.content_panel.SetSizer(self.content_sizer)
        main_sizer.Add(self.content_panel, 1, wx.EXPAND)
        
        # === BOTTOM BAR: pcbtools.xyz + Save + Export PDF ===
        self.bottom_bar = self._create_bottom_bar()
        main_sizer.Add(self.bottom_bar, 0, wx.EXPAND)

        # === DEBUG PANEL (optional, beta) with drag resize ===
        self.debug_panel = None
        self._debug_sash_pos = 240  # Default height (doubled)
        if self._beta_debug_panel:
            self._create_resizable_debug_panel(main_sizer)
        
        self.SetSizer(main_sizer)
        self._show_tab(0)
    
    def _create_top_bar(self):
        """Create top bar with tabs + Import button on same line."""
        top_bar = wx.Panel(self)
        top_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        top_bar.SetMinSize((-1, scale_size(70, self)))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(scale_size(16, self))
        
        # Tab buttons - unified rounded style
        self.tab_buttons = []
        # Build tab list based on beta features enabled
        tabs = [("Notes", 0), ("Todo", 1)]
        if self._beta_bom:
            tabs.append(("BOM", 2))
        if self._beta_version_log:
            tabs.append(("VLog", 3))
        
        for label, idx in tabs:
            btn = RoundedButton(
                top_bar, 
                label=label,
                icon="",
                size=(100, 42),
                bg_color=self._theme["bg_button"],
                fg_color=self._theme["text_primary"],
                corner_radius=10,
                font_size=11,
                font_weight=wx.FONTWEIGHT_BOLD
            )
            btn.Bind_Click(lambda e, i=idx: self._on_tab_click(i))
            btn.tab_index = idx
            self.tab_buttons.append(btn)
            sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        sizer.AddSpacer(16)
        
        # Import button - unified style
        self.import_btn = RoundedButton(
            top_bar,
            label="Import",
            icon="",
            size=(120, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.import_btn.Bind_Click(self._on_import_click)
        sizer.Add(self.import_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddStretchSpacer()
        
        # Refresh Net Cache button (only show if beta net linker enabled)
        if self._beta_net_linker:
            self.refresh_net_btn = RoundedButton(
                top_bar,
                label="↻",
                icon="",
                size=(42, 42),
                bg_color=self._theme["accent_blue"],
                fg_color="#FFFFFF",
                corner_radius=10,
                font_size=14,
                font_weight=wx.FONTWEIGHT_NORMAL
            )
            self.refresh_net_btn.SetToolTip("Refresh Net Cache")
            self.refresh_net_btn.Bind_Click(self._on_refresh_nets)
            sizer.Add(self.refresh_net_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Help button with dropdown menu - before Settings
        self.help_btn = RoundedButton(
            top_bar,
            label="Help",
            icon="",
            size=(80, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.help_btn.Bind_Click(self._on_help_click)
        sizer.Add(self.help_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Settings button - centered icon
        self.settings_btn = RoundedButton(
            top_bar,
            label="Settings",
            icon="",
            size=(130, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.settings_btn.Bind_Click(self._on_settings_click)
        sizer.Add(self.settings_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        top_bar.SetSizer(sizer)
        wx.CallAfter(self._update_tab_styles, 0)
        return top_bar
    
    def _create_bottom_bar(self):
        """Create bottom bar with pcbtools.xyz link, Save and Export PDF buttons."""
        bottom_bar = wx.Panel(self)
        bottom_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        bottom_bar.SetMinSize((-1, scale_size(70, self)))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(scale_size(16, self))
        
        # pcbtools.xyz link on the left with globe icon
        link_text = wx.StaticText(bottom_bar, label="\U0001F310 pcbtools.xyz")
        link_text.SetForegroundColour(hex_to_colour(self._theme["accent_blue"]))
        link_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
        link_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_text.Bind(wx.EVT_LEFT_DOWN, self._on_website_click)
        link_text.SetToolTip("Visit pcbtools.xyz")
        sizer.Add(link_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddSpacer(20)
        
        # Open work logs folder link
        folder_text = wx.StaticText(bottom_bar, label="📁 Directory")
        folder_text.SetForegroundColour(hex_to_colour(self._theme["accent_blue"]))
        folder_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
        folder_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        folder_text.Bind(wx.EVT_LEFT_DOWN, self._on_open_work_logs_folder)
        folder_text.SetToolTip("Open work logs folder (.kinotes)")
        sizer.Add(folder_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddStretchSpacer()
        
        # Global time tracker display - right side before buttons
        self.global_time_label = wx.StaticText(bottom_bar, label="⏱ Total: 00:00:00")
        self.global_time_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        self.global_time_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.global_time_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Export work diary button - right side before Save/PDF
        self.export_diary_btn = RoundedButton(
            bottom_bar,
            label="Export Diary",
            icon="",
            size=(170, 48),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.export_diary_btn.Bind_Click(lambda e: self._on_export_work_diary())
        sizer.Add(self.export_diary_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Save button - unified rounded style
        self.save_btn = RoundedButton(
            bottom_bar,
            label="Save",
            icon="",
            size=(130, 48),
            bg_color=self._theme["accent_green"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=12,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.save_btn.Bind_Click(lambda e: self._on_manual_save())
        sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Export PDF button - unified rounded style with more space
        self.pdf_btn = RoundedButton(
            bottom_bar,
            label="Export PDF",
            icon="",
            size=(170, 48),
            bg_color=self._theme["accent_blue"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=12,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.pdf_btn.Bind_Click(lambda e: self._on_export_pdf())
        sizer.Add(self.pdf_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        bottom_bar.SetSizer(sizer)
        return bottom_bar

    def _create_resizable_debug_panel(self, main_sizer):
        """Create resizable debug panel with drag handle."""
        # Create a container with drag handle at top
        self.debug_container = wx.Panel(self)
        self.debug_container.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        self.debug_container.SetMinSize((-1, 80))
        
        container_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Drag handle bar (thicker for easier grabbing)
        self._drag_bar = wx.Panel(self.debug_container, size=(-1, 8))
        self._drag_bar.SetBackgroundColour(hex_to_colour(self._theme["border"]))
        self._drag_bar.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
        
        # Bind drag events to the drag bar
        self._drag_bar.Bind(wx.EVT_LEFT_DOWN, self._on_debug_drag_start)
        self._drag_bar.Bind(wx.EVT_LEFT_UP, self._on_debug_drag_end)
        self._drag_bar.Bind(wx.EVT_MOTION, self._on_debug_drag_move)
        self._drag_bar.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self._on_debug_capture_lost)
        
        self._debug_dragging = False
        self._debug_drag_start_y = 0
        self._debug_drag_start_height = 0
        
        container_sizer.Add(self._drag_bar, 0, wx.EXPAND)
        
        # Create the actual debug panel content
        self.debug_panel = self._create_debug_panel_content(self.debug_container)
        container_sizer.Add(self.debug_panel, 1, wx.EXPAND)
        
        self.debug_container.SetSizer(container_sizer)
        
        # Set initial height from saved settings or default
        initial_height = self._debug_sash_pos
        self.debug_container.SetMinSize((-1, initial_height))
        
        main_sizer.Add(self.debug_container, 0, wx.EXPAND)
    
    def _on_debug_drag_start(self, event):
        """Start dragging to resize debug panel."""
        self._debug_dragging = True
        # Use screen coordinates for reliable tracking
        self._debug_drag_start_y = wx.GetMousePosition().y
        self._debug_drag_start_height = self.debug_container.GetSize().height
        self._drag_bar.CaptureMouse()
        event.Skip()
    
    def _on_debug_capture_lost(self, event):
        """Handle mouse capture lost."""
        self._debug_dragging = False
    
    def _on_debug_drag_end(self, event):
        """End dragging."""
        if self._debug_dragging:
            self._debug_dragging = False
        if self._drag_bar.HasCapture():
            self._drag_bar.ReleaseMouse()
        event.Skip()
    
    def _on_debug_drag_move(self, event):
        """Handle drag motion to resize debug panel."""
        if not self._debug_dragging:
            event.Skip()
            return
        
        # Use screen coordinates for smooth tracking
        current_y = wx.GetMousePosition().y
        delta = self._debug_drag_start_y - current_y  # Positive = drag up = increase height
        new_height = self._debug_drag_start_height + delta
        
        # Clamp height between min and max
        new_height = max(80, min(500, new_height))
        
        self.debug_container.SetMinSize((-1, new_height))
        self._debug_sash_pos = new_height
        self.Layout()
        self.Refresh()

    def _create_debug_panel_content(self, parent):
        """Create debug panel content (used by resizable container)."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))

        wrapper = wx.BoxSizer(wx.VERTICAL)

        header = wx.BoxSizer(wx.HORIZONTAL)
        title = wx.StaticText(panel, label="🔍 Debug Panel (Beta)")
        title.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        title.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        header.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # Module toggles (select which modules emit logs)
        self._debug_module_checkboxes = {}
        module_labels = [
            ("net", "Net"),
            ("designator", "Designator"),
            ("save", "Save"),
        ]
        for key, label in module_labels:
            cb = wx.CheckBox(panel, label=label)
            cb.SetValue(self._debug_modules.get(key, False))
            cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            cb.Bind(wx.EVT_CHECKBOX, lambda evt, k=key: self._on_debug_module_toggle(k, evt.IsChecked()))
            self._debug_module_checkboxes[key] = cb
            header.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        header.AddStretchSpacer()

        wrapper.Add(header, 0, wx.EXPAND | wx.ALL, 6)

        # Event panel with filters (use dark_mode from settings)
        self.debug_event_panel = DebugEventPanel(panel, self.debug_logger, dark_mode=self._dark_mode)
        wrapper.Add(self.debug_event_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        panel.SetSizer(wrapper)
        return panel

    def _create_debug_panel(self):
        """Create lightweight debug event panel (legacy, for dynamic enable)."""
        return self._create_debug_panel_content(self)
    
    def _on_website_click(self, event):
        """Open pcbtools.xyz in browser."""
        try:
            import webbrowser
            webbrowser.open("https://pcbtools.xyz")
        except:
            pass
    
    def _on_help_click(self, event):
        """Show Help dropdown menu with KiCad-style options."""
        menu = wx.Menu()
        
        # Menu items with IDs
        help_id = wx.NewIdRef()
        involved_id = wx.NewIdRef()
        donate_id = wx.NewIdRef()
        bug_id = wx.NewIdRef()
        debug_id = wx.NewIdRef()
        about_id = wx.NewIdRef()
        
        # Add menu items with icons (using Unicode for consistency)
        help_item = menu.Append(help_id, "❓  Help")
        involved_item = menu.Append(involved_id, "🤝  Get Involved")
        donate_item = menu.Append(donate_id, "💝  Donate")
        bug_item = menu.Append(bug_id, "🐛  Report Bug")
        
        # Add debug option
        debug_item = menu.Append(debug_id, "🔧  Debug Info")
        
        menu.AppendSeparator()
        about_item = menu.Append(about_id, "ℹ️  About KiNotes")
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, lambda e: self._open_url("https://pcbtools.xyz/tools/kinotes"), help_item)
        self.Bind(wx.EVT_MENU, lambda e: self._open_url("https://github.com/way2pramil/KiNotes"), involved_item)
        self.Bind(wx.EVT_MENU, lambda e: self._open_url("https://pcbtools.xyz/donate"), donate_item)
        self.Bind(wx.EVT_MENU, lambda e: self._open_url("https://pcbtools.xyz/tools/kinotes#report-bug"), bug_item)
        self.Bind(wx.EVT_MENU, self._on_debug_info, debug_item)
        self.Bind(wx.EVT_MENU, self._show_about_dialog, about_item)
        
        # Position menu below the help button
        btn_pos = self.help_btn.GetScreenPosition()
        btn_size = self.help_btn.GetSize()
        self.PopupMenu(menu, self.ScreenToClient(wx.Point(btn_pos.x, btn_pos.y + btn_size.y)))
        menu.Destroy()

    def _on_debug_module_toggle(self, key: str, enabled: bool):
        """Update active debug modules from panel toggles."""
        self._debug_modules[key] = enabled
        self._apply_debug_logger_targets()
        self._save_color_settings()

    def _apply_debug_logger_targets(self):
        """Propagate debug logger module selections to subcomponents."""
        if hasattr(self, 'visual_editor') and self.visual_editor:
            if hasattr(self.visual_editor, 'set_debug_logging'):
                self.visual_editor.set_debug_logging(self.debug_logger, self._debug_modules)

    def _ensure_net_linker(self):
        """Get net linker from cache manager (lazy-loaded on demand inside KiCad)."""
        if not self.net_cache_manager:
            debug_print("[KiNotes] Net cache manager not available")
            return
        self.net_linker = self.net_cache_manager.get_linker()
        if self.net_linker:
            debug_print("[KiNotes] Net linker obtained from cache manager")
        else:
            debug_print("[KiNotes] Net linker unavailable (no KiCad board?)")

    def _attach_net_linker_to_editor(self):
        """Attach linker to visual editor if available. Linker may be None (lazy-loaded)."""
        if not hasattr(self, 'visual_editor') or not self.visual_editor:
            return
        # Pass linker (may be None; visual editor will use it if set)
        try:
            if self._beta_net_linker and self.net_linker:
                self.visual_editor.set_net_linker(self.net_linker)
                debug_print("[KiNotes] Net linker attached to visual editor")
            else:
                self.visual_editor.set_net_linker(None)
        except Exception as e:
            debug_print(f"[KiNotes] Net linker attach warning: {e}")

    def _should_log(self, module: str) -> bool:
        """Return True if debug logging for the module is enabled."""
        if not self._beta_debug_panel:
            return False
        return self._debug_modules.get(module, False)

    def _log_event(self, module: str, level: EventLevel, message: str):
        """Log event to debug panel if module is enabled."""
        if not self._should_log(module):
            return
        try:
            self.debug_logger.log(level, message)
        except Exception:
            pass
    
    def _open_url(self, url):
        """Open URL in default browser."""
        try:
            import webbrowser
            webbrowser.open(url)
        except:
            pass
    
    def _refresh_net_cache(self, show_message: bool = False):
        """Refresh net cache via cache manager."""
        if not self._beta_net_linker or not self.net_cache_manager:
            return
        try:
            success = self.net_cache_manager.refresh()
            if success:
                # Also update our local reference
                self.net_linker = self.net_cache_manager.get_linker()
                if show_message:
                    wx.MessageBox("Net cache refreshed. Ready for net cross-probe.", "Net Linker", wx.OK | wx.ICON_INFORMATION)
                self._log_event("net", EventLevel.SUCCESS, "Net cache refreshed")
            else:
                if show_message:
                    wx.MessageBox("Net cache refresh failed (no board or linker unavailable).", "Error", wx.OK | wx.ICON_ERROR)
                self._log_event("net", EventLevel.WARNING, "Net cache refresh failed")
        except Exception as e:
            if show_message:
                wx.MessageBox(f"Net refresh error: {e}", "Error", wx.OK | wx.ICON_ERROR)
            self._log_event("net", EventLevel.ERROR, f"Net cache refresh failed: {e}")

    def _on_refresh_nets(self, event):
        """Refresh net cache (beta feature) - show visual feedback."""
        debug_print("[KiNotes] Refresh button clicked")
        try:
            # Change button color to green to show active state
            if hasattr(self, 'refresh_net_btn') and self.refresh_net_btn:
                self.refresh_net_btn.SetBackgroundColour(hex_to_colour(self._theme["accent_green"]))
                self.refresh_net_btn.Refresh()
        except Exception:
            pass
        
        # Perform refresh with message
        self._refresh_net_cache(show_message=True)
        
        try:
            # Revert button color back to blue
            if hasattr(self, 'refresh_net_btn') and self.refresh_net_btn:
                wx.CallLater(1000, lambda: self._reset_refresh_btn_color())
        except Exception:
            pass

    def _reset_refresh_btn_color(self):
        """Reset refresh button color back to blue."""
        try:
            if hasattr(self, 'refresh_net_btn') and self.refresh_net_btn:
                self.refresh_net_btn.SetBackgroundColour(hex_to_colour(self._theme["accent_blue"]))
                self.refresh_net_btn.Refresh()
        except Exception:
            pass
    
    def _on_debug_info(self, event):
        """Show debug information popup."""
        debug_info = "KiNotes Debug Information\n"
        debug_info += "=" * 50 + "\n\n"
        
        # Editor mode
        debug_info += f"Editor Mode: {'Visual' if self._use_visual_editor else 'Markdown'}\n"
        debug_info += f"Visual Editor Available: {VISUAL_EDITOR_AVAILABLE}\n\n"
        
        # Cross-probe info
        debug_info += "Cross-Probe Status:\n"
        debug_info += f"  Designator Cross-Probe: {self._crossprobe_enabled}\n"
        debug_info += f"  Designator Linker: {'✓' if self.designator_linker else '✗'}\n\n"
        
        # Net linker info (Beta)
        debug_info += "Net Linker (Beta):\n"
        debug_info += f"  Net Linker Beta Enabled: {self._beta_net_linker}\n"
        debug_info += f"  Net Linker Instance: {'✓' if self.net_linker else '✗'}\n"
        
        if self.net_linker:
            net_cache_size = len(self.net_linker._net_map) if hasattr(self.net_linker, '_net_map') else 0
            debug_info += f"  Cached Nets: {net_cache_size}\n"
            if net_cache_size > 0 and net_cache_size <= 10:
                nets = list(self.net_linker._net_map.keys())
                debug_info += f"  Sample Nets: {', '.join(nets[:5])}\n"
        
        debug_info += f"  Visual Editor has Net Linker: {'✓' if (self.visual_editor and hasattr(self.visual_editor, '_net_linker') and self.visual_editor._net_linker) else '✗'}\n\n"
        
        # UI State
        debug_info += "UI State:\n"
        debug_info += f"  Dark Mode: {self._dark_mode}\n"
        debug_info += f"  Beta Markdown: {self._beta_markdown}\n"
        debug_info += f"  Beta BOM: {self._beta_bom}\n"
        debug_info += f"  Beta Version Log: {self._beta_version_log}\n\n"
        
        # Data files
        debug_info += "Data Storage:\n"
        try:
            kinotes_dir = os.path.join(os.path.dirname(self.current_project_path), '.kinotes')
            if os.path.exists(kinotes_dir):
                files = os.listdir(kinotes_dir)
                debug_info += f"  .kinotes folder: {len(files)} files\n"
                for f in files[:5]:
                    debug_info += f"    - {f}\n"
            else:
                debug_info += f"  .kinotes folder: NOT FOUND\n"
        except Exception as e:
            debug_info += f"  .kinotes folder: Error - {e}\n"
        
        # Show popup
        dlg = wx.Dialog(self, title="Debug Information", size=(600, 500))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Text control
        text_ctrl = wx.TextCtrl(dlg, value=debug_info, style=wx.TE_MULTILINE | wx.TE_READONLY)
        text_ctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        # Close button
        close_btn = wx.Button(dlg, wx.ID_CLOSE)
        sizer.Add(close_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        close_btn.Bind(wx.EVT_BUTTON, lambda e: dlg.Close())
        
        dlg.SetSizer(sizer)
        dlg.ShowModal()
        dlg.Destroy()
    
    def _show_about_dialog(self, event):
        """Show About KiNotes dialog with project story."""
        show_about_dialog(self, self._theme, self._open_url)
    
    def _show_crash_recovery_dialog(self):
        """Show crash recovery information dialog."""
        try:
            crash_summary = self.crash_safety.get_crash_summary()
            total_crashes = crash_summary.get('total_crashes', 0)
            
            dlg = wx.Dialog(self, title="Crash Recovery", size=(500, 400))
            dlg.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
            
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Warning icon and title
            title_sizer = wx.BoxSizer(wx.HORIZONTAL)
            warning_text = wx.StaticText(dlg, label="⚠")
            warning_text.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            warning_text.SetForegroundColour(hex_to_colour(self._theme["accent_red"]))
            title_sizer.Add(warning_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
            
            title_label = wx.StaticText(dlg, label="KiNotes Recovered from Crash")
            title_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            title_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            title_sizer.Add(title_label, 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(title_sizer, 0, wx.ALL, 20)
            
            # Message
            message = f"""The previous KiNotes session ended unexpectedly.

Safe Mode is now active:
• Beta features temporarily disabled
• Using stable Markdown editor
• All project data preserved

Crash count: {total_crashes} recent incident(s)

Your notes, todos, and settings have been automatically backed up.
You can safely continue working."""
            
            msg_text = wx.TextCtrl(dlg, value=message, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
            msg_text.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
            msg_text.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            msg_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            sizer.Add(msg_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
            
            # Buttons
            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            btn_sizer.AddStretchSpacer()
            
            clear_btn = RoundedButton(
                dlg, label="Clear Crash History", size=(180, 36),
                bg_color=self._theme["bg_button"], fg_color=self._theme["text_primary"],
                corner_radius=8, font_size=10
            )
            clear_btn.Bind_Click(lambda e: self._on_clear_crash_history(dlg))
            btn_sizer.Add(clear_btn, 0, wx.RIGHT, 10)
            
            ok_btn = RoundedButton(
                dlg, label="Continue", size=(120, 36),
                bg_color=self._theme["accent_blue"], fg_color="#FFFFFF",
                corner_radius=8, font_size=10, font_weight=wx.FONTWEIGHT_BOLD
            )
            ok_btn.Bind_Click(lambda e: dlg.Close())
            btn_sizer.Add(ok_btn, 0)
            
            sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 20)
            
            dlg.SetSizer(sizer)
            dlg.CenterOnParent()
            dlg.ShowModal()
            dlg.Destroy()
            
        except Exception as e:
            debug_print(f"[KiNotes] Error showing crash dialog: {e}")
    
    def _on_clear_crash_history(self, dialog):
        """Clear crash history and disable safe mode."""
        try:
            self.crash_safety.clear_crash_history()
            self.crash_safety.disable_safe_mode()
            self._safe_mode_active = False
            self._log_event("save", EventLevel.SUCCESS, "Crash history cleared")
            wx.MessageBox(
                "Crash history cleared. You can re-enable beta features in Settings.\n\nRestart KiNotes for changes to take effect.",
                "Cleared",
                wx.OK | wx.ICON_INFORMATION
            )
            dialog.Close()
        except Exception as e:
            debug_print(f"[KiNotes] Error clearing crash history: {e}")
    
    def _get_work_diary_path(self):
        """
        Get the work diary file path in .kinotes directory.
        Uses a SINGLE daily file per project - overwrites on each save.
        Format: <project>_worklog_<YYYYMMDD>.md
        """
        # Try to get KiCad project directory, fallback to home directory
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            if board and board.GetFileName():
                project_dir = os.path.dirname(board.GetFileName())
                project_name = os.path.splitext(os.path.basename(board.GetFileName()))[0]
            else:
                project_dir = os.path.expanduser("~")
                project_name = "kinotes"
        except:
            # Standalone mode: use home directory
            project_dir = os.path.expanduser("~")
            project_name = "kinotes"
        
        # Create .kinotes subdirectory
        kinotes_dir = os.path.join(project_dir, ".kinotes")
        os.makedirs(kinotes_dir, exist_ok=True)
        
        # Generate filename with DATE ONLY (not time) - one file per day
        # Format: <project_title>_worklog_<YYYYMMDD>.md
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"{project_name}_worklog_{date_str}.md"
        filepath = os.path.join(kinotes_dir, filename)
        
        return filepath, kinotes_dir
    
    def _on_export_work_diary(self):
        """Insert work diary at cursor position in notes and refresh display."""
        try:
            content = self.time_tracker.export_work_diary(format_24h=self.time_tracker.time_format_24h)
            if not content.strip():
                wx.MessageBox("No tasks to export.", "Export Diary", wx.OK | wx.ICON_INFORMATION)
                return
            
            # Switch to Notes tab
            self._show_tab(0)
            
            # Insert diary content at cursor position
            if hasattr(self, 'visual_editor') and self.visual_editor:
                # Get current content, insert diary, then reload to parse markdown
                current_md = self.visual_editor.GetValue()
                
                # Find insertion point - append at end with separator
                if current_md.strip():
                    new_content = current_md + "\n\n---\n\n" + content
                else:
                    new_content = content
                
                # Reload content to properly parse markdown formatting
                self.visual_editor.SetValue(new_content)
                
                # Scroll to bottom to show new content
                try:
                    editor = self.visual_editor._editor
                    editor.ShowPosition(editor.GetLastPosition())
                except:
                    pass
                
                self._modified = True
                wx.MessageBox("Work diary inserted in Notes.", "Export Diary", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("Visual editor not available.", "Export Error", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox(f"Error inserting diary: {str(e)}", "Export Error", wx.OK | wx.ICON_ERROR)
    
    def _auto_export_diary_on_close(self):
        """Automatically save work diary to file on close - safe, no UI operations."""
        try:
            # Only export to file, don't touch UI during close
            content = self.time_tracker.export_work_diary(format_24h=self.time_tracker.time_format_24h)
            if content and content.strip():
                filepath, kinotes_dir = self._get_work_diary_path()
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                debug_print(f"[KiNotes] Work diary auto-saved to: {filepath}")
        except Exception as e:
            debug_print(f"[KiNotes] Auto-save diary warning: {e}")
    
    def _on_open_work_logs_folder(self, event):
        """Open the .kinotes work logs folder in file explorer."""
        debug_print("[KiNotes Directory] Click handler called")
        
        # Get actual project directory from board (most reliable)
        kinotes_dir = None
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            debug_print(f"[KiNotes Directory] board: {board}")
            if board:
                board_file = board.GetFileName()
                debug_print(f"[KiNotes Directory] board.GetFileName(): {board_file}")
                if board_file:
                    project_dir = os.path.dirname(board_file)
                    kinotes_dir = os.path.join(project_dir, ".kinotes")
                    debug_print(f"[KiNotes Directory] From board: {kinotes_dir}")
        except Exception as e:
            debug_print(f"[KiNotes Directory] pcbnew error: {e}")
        
        # Fallback to notes_manager's notes_dir (canonical location)
        if not kinotes_dir:
            if hasattr(self, 'notes_manager') and self.notes_manager:
                if hasattr(self.notes_manager, 'notes_dir') and self.notes_manager.notes_dir:
                    kinotes_dir = self.notes_manager.notes_dir
                    debug_print(f"[KiNotes Directory] From notes_manager.notes_dir: {kinotes_dir}")
                elif hasattr(self.notes_manager, 'project_dir') and self.notes_manager.project_dir:
                    kinotes_dir = os.path.join(self.notes_manager.project_dir, ".kinotes")
                    debug_print(f"[KiNotes Directory] From notes_manager.project_dir: {kinotes_dir}")
        
        # Final fallback - should never reach here
        if not kinotes_dir:
            kinotes_dir = os.path.join(os.getcwd(), ".kinotes")
            debug_print(f"[KiNotes Directory] FALLBACK to cwd: {kinotes_dir}")
        
        debug_print(f"[KiNotes Directory] Final path: {kinotes_dir}")
        debug_print(f"[KiNotes Directory] Exists: {os.path.exists(kinotes_dir)}")
        
        # Normalize path for Windows (fix mixed / and \ separators)
        kinotes_dir = os.path.normpath(kinotes_dir)
        debug_print(f"[KiNotes Directory] Normalized path: {kinotes_dir}")
        
        # Ensure directory exists
        if not os.path.exists(kinotes_dir):
            try:
                os.makedirs(kinotes_dir, exist_ok=True)
                debug_print(f"[KiNotes Directory] Created folder")
            except Exception as e:
                wx.MessageBox(
                    f"Could not create .kinotes directory:\n{e}",
                    "Directory Error",
                    wx.OK | wx.ICON_ERROR
                )
                return
        
        # Open folder in system file explorer
        import subprocess
        try:
            debug_print(f"[KiNotes Directory] Opening: {kinotes_dir}")
            if sys.platform.startswith("win"):
                # Use os.startfile for most reliable Windows folder opening
                os.startfile(kinotes_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", kinotes_dir])
            else:
                subprocess.Popen(["xdg-open", kinotes_dir])
        except Exception as e:
            wx.MessageBox(
                f"Could not open directory:\n{kinotes_dir}\n\nError: {e}",
                "Directory Error",
                wx.OK | wx.ICON_ERROR
            )
    
    def _update_tab_styles(self, active_idx):
        """Update tab button styles."""
        for btn in self.tab_buttons:
            try:
                if btn.tab_index == active_idx:
                    btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
                else:
                    btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
            except:
                pass
    
    def _on_tab_click(self, idx):
        self._show_tab(idx)
    
    def _show_tab(self, idx):
        """Show selected tab."""
        self._current_tab = idx
        self._update_tab_styles(idx)
        
        self.notes_panel.Hide()
        self.todo_panel.Hide()
        self.bom_panel.Hide()
        self.version_log_panel.Hide()
        
        # Show/hide buttons based on tab
        if idx == 0:  # Notes tab
            self.notes_panel.Show()
            self.import_btn.Show()
            self.save_btn.Show()
            self.pdf_btn.Show()
            self.export_diary_btn.Hide()
            self.global_time_label.Hide()
        elif idx == 1:  # Todo tab
            self.todo_panel.Show()
            self.import_btn.Hide()
            self.save_btn.Hide()
            self.pdf_btn.Hide()
            self.export_diary_btn.Show()
            self.global_time_label.Show()
            try:
                self.todo_scroll.FitInside()
            except:
                pass
        elif idx == 2:  # BOM tab
            self.bom_panel.Show()
            self.import_btn.Hide()
            self.save_btn.Show()  # Keep Save for BOM settings
            self.pdf_btn.Hide()
            self.export_diary_btn.Hide()
            self.global_time_label.Hide()
            try:
                self.bom_panel.FitInside()
            except:
                pass
        elif idx == 3:  # Version Log tab
            self.version_log_panel.Show()
            self.import_btn.Hide()
            self.save_btn.Hide()
            self.pdf_btn.Hide()
            self.export_diary_btn.Hide()
            self.global_time_label.Hide()
            try:
                self.version_log_scroll.FitInside()
            except:
                pass
        
        self.top_bar.Layout()
        self.bottom_bar.Layout()
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
    
    # ============================================================
    # SETTINGS DIALOG
    # ============================================================
    
    def _on_settings_click(self, event):
        """Show settings dialog and apply changes."""
        # Build config dict for settings dialog
        config = {
            'theme': self._theme,
            'dark_mode': self._dark_mode,
            'bg_color_name': self._bg_color_name,
            'text_color_name': self._text_color_name,
            'dark_bg_color_name': self._dark_bg_color_name,
            'dark_text_color_name': self._dark_text_color_name,
            'time_tracker': self.time_tracker,
            'crossprobe_enabled': self._crossprobe_enabled,
            'net_crossprobe_enabled': getattr(self, '_net_crossprobe_enabled', True),
            'custom_designators': getattr(self, '_custom_designators', ''),
            'use_visual_editor': self._use_visual_editor,
            'visual_editor_available': VISUAL_EDITOR_AVAILABLE,
            'beta_markdown': self._beta_markdown,
            'beta_bom': self._beta_bom,
            'beta_version_log': self._beta_version_log,
            'beta_net_linker': True,  # Always on - no longer beta
            'beta_debug_panel': self._beta_debug_panel,
            'debug_modules': self._debug_modules,
            'notes_manager': self.notes_manager,
            'pdf_format': getattr(self, '_pdf_format', 'markdown'),
        }
        
        result, save_mode = show_settings_dialog(self, config)
        
        if result:
            self._apply_settings_result(result, save_mode)
    
    def _apply_settings_result(self, result, save_mode='local'):
        """Apply settings from dialog result.
        
        Args:
            result: Settings dict from dialog
            save_mode: 'local' for project-specific, 'global' for user-wide
        """
        # Store save mode for later use
        self._last_save_mode = save_mode
        
        # Update theme
        self._dark_mode = result['dark_mode']
        if self._dark_mode:
            self._dark_bg_color_name = result['dark_bg_color_name']
            self._dark_text_color_name = result['dark_text_color_name']
        else:
            self._bg_color_name = result['bg_color_name']
            self._text_color_name = result['text_color_name']
        
        # Update time tracking settings
        self.time_tracker.enable_time_tracking = result['enable_time_tracking']
        self.time_tracker.time_format_24h = result['time_format_24h']
        self.time_tracker.show_work_diary_button = result['show_work_diary']
        
        # Show/hide export diary button based on setting AND current tab
        if self.time_tracker.show_work_diary_button and self._current_tab == 1:
            self.export_diary_btn.Show()
        else:
            self.export_diary_btn.Hide()
        
        # Update cross-probe setting
        self._crossprobe_enabled = result['crossprobe_enabled']
        self._custom_designators = result.get('custom_designators', '')
        if self.designator_linker:
            self.designator_linker.set_custom_prefixes(self._custom_designators)
        if hasattr(self, 'visual_editor') and self.visual_editor:
            self.visual_editor.set_crossprobe_enabled(self._crossprobe_enabled)
            self.visual_editor.set_designator_linker(
                self.designator_linker if self._crossprobe_enabled else None
            )
        
        # Update editor mode setting
        old_visual_editor = self._use_visual_editor
        self._use_visual_editor = result['use_visual_editor']
        
        # Update UI scale factor
        old_scale_factor = get_user_scale_factor()
        new_scale_factor = result['scale_factor']
        set_user_scale_factor(new_scale_factor)
        
        # Check panel size changes and store new values
        current_settings = self.notes_manager.load_settings() or {}
        old_width = current_settings.get("panel_width", 1300)
        old_height = current_settings.get("panel_height", 1170)
        new_width = result['panel_width']
        new_height = result['panel_height']
        panel_size_changed = (old_width != new_width or old_height != new_height)
        
        # Store panel size for saving
        self._panel_width = new_width
        self._panel_height = new_height
        
        # Update beta feature settings
        old_beta_markdown = self._beta_markdown
        old_beta_bom = self._beta_bom
        old_beta_version_log = self._beta_version_log
        old_net_crossprobe = getattr(self, '_net_crossprobe_enabled', True)
        old_beta_debug_panel = self._beta_debug_panel
        old_use_visual_editor = self._use_visual_editor
        old_debug_modules = dict(self._debug_modules)
        
        self._beta_markdown = result['beta_markdown']
        self._beta_bom = result['beta_bom']
        self._beta_version_log = result['beta_version_log']
        # Net cross-probe is now a main feature
        self._net_crossprobe_enabled = result.get('net_crossprobe_enabled', True)
        self._beta_net_linker = self._net_crossprobe_enabled  # Legacy alias
        self._beta_debug_panel = result.get('beta_debug_panel', False)
        self._debug_modules = result.get('debug_modules', self._debug_modules)
        for key in ("save", "net", "designator"):
            if key not in self._debug_modules:
                self._debug_modules[key] = False
        
        # PDF format setting
        self._pdf_format = result.get('pdf_format', 'markdown')
        
        # IMPORTANT: beta_markdown checkbox controls the actual editor mode
        # If beta_markdown is enabled, use Markdown editor (set use_visual_editor to False)
        # If beta_markdown is disabled, use Visual editor (set use_visual_editor to True)
        if self._beta_markdown:
            self._use_visual_editor = False
        else:
            # If markdown beta is disabled but visual editor is available, use visual
            self._use_visual_editor = VISUAL_EDITOR_AVAILABLE
        
        # Refresh nets if net linker is enabled
        if self._beta_net_linker and self.net_linker:
            try:
                self.net_linker.refresh_nets()
                debug_print("[KiNotes] Net linker cache refreshed")
            except Exception as e:
                debug_print(f"[KiNotes] Net linker refresh warning: {e}")

        # Re-attach net linker to editor after settings changes
        self._attach_net_linker_to_editor()
        
        beta_features_changed = (
            old_beta_markdown != self._beta_markdown or
            old_beta_bom != self._beta_bom or
            old_beta_version_log != self._beta_version_log or
            old_net_crossprobe != self._net_crossprobe_enabled or
            old_beta_debug_panel != self._beta_debug_panel or
            old_debug_modules != self._debug_modules
        )
        
        # Check if restart is required
        needs_restart = False
        restart_reasons = []
        
        # Editor mode changed
        if old_use_visual_editor != self._use_visual_editor:
            needs_restart = True
            restart_reasons.append("Editor mode")
        
        if old_scale_factor != new_scale_factor:
            needs_restart = True
            restart_reasons.append("UI scale")
        
        if panel_size_changed:
            needs_restart = True
            restart_reasons.append("Panel size")
        
        if beta_features_changed:
            needs_restart = True
            restart_reasons.append("Beta features")
        
        if needs_restart:
            reasons_str = " and ".join(restart_reasons)
            wx.MessageBox(
                f"{reasons_str} change will take effect after restarting KiNotes.",
                "Restart Required",
                wx.OK | wx.ICON_INFORMATION
            )

        # Handle debug panel visibility and module toggles
        if old_beta_debug_panel != self._beta_debug_panel:
            if self._beta_debug_panel and not self.debug_panel:
                try:
                    # Create resizable debug panel
                    main_sizer = self.GetSizer()
                    self._create_resizable_debug_panel(main_sizer)
                    self.Layout()
                except Exception as e:
                    debug_print(f"[KiNotes] Debug panel create warning: {e}")
            elif not self._beta_debug_panel and self.debug_panel:
                try:
                    if hasattr(self, 'debug_container') and self.debug_container:
                        self.debug_container.Destroy()
                        self.debug_container = None
                    elif self.debug_panel:
                        self.debug_panel.Destroy()
                except Exception:
                    pass
                self.debug_panel = None
                self.Layout()

        # Sync module checkbox UI if panel exists
        if getattr(self, "_debug_module_checkboxes", None):
            for key, cb in self._debug_module_checkboxes.items():
                cb.SetValue(self._debug_modules.get(key, False))

        # Propagate logger targets to editors
        self._apply_debug_logger_targets()
        
        self._theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        self._apply_theme()
        self._apply_editor_colors()
        self._save_color_settings(save_mode)
        # Persist everything immediately to avoid data loss before restart/close
        try:
            self.force_save()
        except Exception as e:
            debug_print(f"[KiNotes] Settings apply save warning: {e}")
        self.Layout()
    
    def _apply_theme_to_panel(self, panel):
        """Apply current theme to a panel and all its children recursively."""
        if not panel:
            return
        
        try:
            panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
            
            # Recursively apply to all children
            for child in panel.GetChildren():
                if isinstance(child, wx.Panel):
                    self._apply_theme_to_panel(child)
                elif isinstance(child, wx.TextCtrl):
                    child.SetBackgroundColour(self._get_editor_bg())
                    child.SetForegroundColour(self._get_editor_text())
                elif isinstance(child, (wx.Choice, wx.ComboBox)):
                    child.SetBackgroundColour(hex_to_colour(self._theme["bg_button"]))
                    child.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                elif isinstance(child, wx.CheckBox):
                    child.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                elif isinstance(child, wx.StaticText):
                    child.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        except:
            pass
    
    def _apply_theme(self):
        """Apply current theme to all UI elements."""
        self.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self.top_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        self.bottom_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        # Use editor bg color for content area to avoid gray strip around notes
        self.content_panel.SetBackgroundColour(self._get_editor_bg())
        
        # Apply theme to formatting toolbar
        try:
            self.format_toolbar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
            for btn in self.format_buttons:
                btn.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
                btn.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        except:
            pass
        
        # Apply theme to all tab panels
        self._apply_theme_to_panel(self.notes_panel)
        self._apply_theme_to_panel(self.todo_panel)
        self._apply_theme_to_panel(self.bom_panel)
        self._apply_theme_to_panel(self.version_log_panel)
        
        # Update tab buttons
        for btn in self.tab_buttons:
            if btn.tab_index == self._current_tab:
                btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
            else:
                btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        
        # Update other buttons
        self.import_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        self.help_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        self.settings_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        self.save_btn.SetColors(self._theme["accent_green"], "#FFFFFF")
        self.pdf_btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
        self.export_diary_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        
        # Update global time label
        try:
            self.global_time_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        except:
            pass
        
        # Update todo counter
        try:
            self.todo_count.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        except:
            pass
        
        # Update all todo items
        for item in self._todo_items:
            try:
                item["panel"].SetBackgroundColour(
                    hex_to_colour(self._theme["bg_panel"]) if self._dark_mode else wx.WHITE
                )
                item["checkbox"].SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                item["text"].SetBackgroundColour(
                    hex_to_colour(self._theme["bg_panel"]) if self._dark_mode else wx.WHITE
                )
                item["text"].SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                item["timer_label"].SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
                item["del_btn"].SetBackgroundColour(
                    hex_to_colour(self._theme["bg_panel"]) if self._dark_mode else wx.WHITE
                )
            except:
                pass
        
        self.Refresh()
        self.Update()
    
    def _apply_editor_colors(self):
        """Apply selected colors to editor (supports both Visual and Markdown modes)."""
        try:
            bg = self._get_editor_bg()
            fg = self._get_editor_text()
            
            # Apply to Visual Editor if active
            if self._use_visual_editor and hasattr(self, 'visual_editor') and self.visual_editor:
                # Update dark mode first (sets base theme)
                self.visual_editor.update_dark_mode(self._dark_mode, force_refresh=True)
                # Then apply custom colors on top
                self.visual_editor.set_custom_colors(bg, fg)
                if self.visual_editor.IsShown():
                    self.visual_editor.Refresh()
                return
            
            # Apply to Markdown Editor if active
            if hasattr(self, 'text_editor') and self.text_editor:
                self.text_editor.SetBackgroundColour(bg)
                self.text_editor.SetForegroundColour(fg)
                
                # Apply to all text
                font = self.text_editor.GetFont()
                text_attr = wx.TextAttr(fg, bg, font)
                self.text_editor.SetDefaultStyle(text_attr)
                self.text_editor.SetStyle(0, self.text_editor.GetLastPosition(), text_attr)
                if self.text_editor.IsShown():
                    self.text_editor.Refresh()
        except Exception:
            # Silently handle editor color update errors
            pass
    
    # ============================================================
    # TAB 1: NOTES (Dual-Mode: Visual WYSIWYG or Markdown)
    # ============================================================
    
    def _create_notes_tab(self, parent):
        """Create Notes tab with dual-mode editor support (Visual/Markdown)."""
        panel = wx.Panel(parent)
        # Use editor background color (not panel bg) to avoid gray strip around editor
        panel.SetBackgroundColour(self._get_editor_bg())
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Store reference to notes panel sizer for editor switching
        self._notes_panel = panel
        self._notes_sizer = sizer
        
        # Create the appropriate editor based on settings
        if self._use_visual_editor and VISUAL_EDITOR_AVAILABLE:
            # Visual WYSIWYG Editor (Default)
            self._create_visual_editor(panel, sizer)
        else:
            # Markdown Text Editor (Fallback/Power User Mode)
            self._create_markdown_editor(panel, sizer)
        
        panel.SetSizer(sizer)
        return panel
    
    def _create_visual_editor(self, panel, sizer):
        """Create Visual WYSIWYG Note Editor."""
        try:
            # Visual Editor comes with its own toolbar
            self.visual_editor = VisualNoteEditor(
                panel,
                dark_mode=self._dark_mode,
                style=wx.BORDER_NONE,
                beta_features=False  # Reserved for future beta features
            )
            
            # Set project directory for file dialogs
            self.visual_editor.project_dir = self.notes_manager.project_dir
            
            debug_print("[KiNotes] Visual editor created successfully")
            
            # Apply user's custom colors immediately after creation
            try:
                bg = self._get_editor_bg()
                fg = self._get_editor_text()
                self.visual_editor.set_custom_colors(bg, fg)
                debug_print(f"[KiNotes] Custom colors applied: bg={bg}, fg={fg}")
            except Exception as e:
                debug_print(f"[KiNotes] Custom colors warning: {e}")
                import traceback
                traceback.print_exc()
            
            # Apply user's font size setting
            debug_print("[KiNotes] About to set font size...")
            try:
                settings = self.notes_manager.load_settings() or {}
                font_size = settings.get("font_size", 11)
                debug_print(f"[KiNotes] Font size setting: {font_size}")
                self.visual_editor.set_font_size(font_size)
                debug_print("[KiNotes] Font size applied")
            except Exception as e:
                debug_print(f"[KiNotes] Font size warning: {e}")
                import traceback
                traceback.print_exc()
            
            # Set up cross-probe functionality
            debug_print("[KiNotes] About to setup crossprobe...")
            try:
                self.visual_editor.set_crossprobe_enabled(self._crossprobe_enabled)
                if self._crossprobe_enabled and self.designator_linker:
                    self.visual_editor.set_designator_linker(self.designator_linker)
                debug_print("[KiNotes] Crossprobe setup complete")
            except Exception as e:
                debug_print(f"[KiNotes] Crossprobe setup warning: {e}")
                import traceback
                traceback.print_exc()
            
            # Set up net highlighting (Beta)
            # Note: net linker is lazy-loaded on first click (inside KiCad only)
            debug_print("[KiNotes] Net linker setup deferred to first click")
            try:
                self.visual_editor.set_net_linker(None)  # Start with no linker; will be created on demand
            except Exception as e:
                debug_print(f"[KiNotes] Net linker setup warning: {e}")

            # Attach debug logger if enabled
            debug_print("[KiNotes] About to setup debug logger...")
            try:
                self._apply_debug_logger_targets()
                debug_print("[KiNotes] Debug logger setup complete")
            except Exception as e:
                debug_print(f"[KiNotes] Debug logger setup warning: {e}")
                import traceback
                traceback.print_exc()
            
            # Reference for unified API
            self.text_editor = None  # Not using markdown editor
            self.format_toolbar = None  # Visual editor has integrated toolbar
            
            # Bind text change event for auto-save
            debug_print("[KiNotes] About to bind text change event...")
            try:
                self.visual_editor.editor.Bind(wx.EVT_TEXT, self._on_text_changed)
            except Exception as e:
                debug_print(f"[KiNotes] Text change binding warning: {e}")
            
            sizer.Add(self.visual_editor, 1, wx.EXPAND | wx.ALL, 0)
            debug_print("[KiNotes] Visual editor added to sizer")
        except Exception as e:
            import traceback
            debug_print(f"[KiNotes ERROR] Failed to create visual editor: {e}")
            traceback.print_exc()
            # Fall back to markdown editor
            self._create_markdown_editor(panel, sizer)
    
    def _create_markdown_editor(self, panel, sizer):
        """Create Markdown Text Editor (Power User Mode) using MarkdownEditor class."""
        from .markdown_editor import MarkdownEditor
        
        self.markdown_editor = MarkdownEditor(
            panel,
            dark_mode=self._dark_mode,
            bg_color=self._get_editor_bg(),
            text_color=self._get_editor_text(),
            designator_linker=self.designator_linker,
            on_text_changed=self._on_text_changed,
        )
        sizer.Add(self.markdown_editor, 1, wx.EXPAND)
        
        # Alias for unified API
        self.text_editor = self.markdown_editor._editor
        self.visual_editor = None  # Not using visual editor

    def _get_note_content(self):
        """Get note content from active editor (unified API)."""
        if self._use_visual_editor and hasattr(self, 'visual_editor') and self.visual_editor:
            return self.visual_editor.GetValue()
        elif hasattr(self, 'text_editor') and self.text_editor:
            return self.text_editor.GetValue()
        return ""
    
    def _set_note_content(self, content):
        """Set note content in active editor (unified API)."""
        if self._use_visual_editor and hasattr(self, 'visual_editor') and self.visual_editor:
            self.visual_editor.SetValue(content)
        elif hasattr(self, 'text_editor') and self.text_editor:
            self.text_editor.SetValue(content)
        elif hasattr(self, 'markdown_editor') and self.markdown_editor:
            self.markdown_editor.SetValue(content)
    
    # ============================================================
    # TAB 2: TODO LIST
    # ============================================================
    
    # TAB 2: TODO LIST - Implemented in TodoTabMixin (see tabs/todo_tab.py)
    
    # TAB 3: BOM TOOL - Implemented in BomTabMixin (see tabs/bom_tab.py)
    
    # Version Log Tab methods are provided by VersionLogTabMixin
    
    # ============================================================
    # IMPORT HANDLER
    # ============================================================
    
    def _on_import_click(self, event):
        """Handle import button click."""
        menu = wx.Menu()
        
        # Check if we're in Visual Editor mode
        # Table-based imports (BOM, Netlist, Layers, Stackup, Drill) are disabled
        # in Visual Editor mode as they don't render properly yet
        is_visual_mode = self._use_visual_editor and hasattr(self, 'visual_editor') and self.visual_editor
        
        if is_visual_mode:
            # Limited menu for Visual Editor - only non-table imports
            items = [
                (Icons.BOARD + "  Board Info", self._import_board_info),
                (Icons.NETLIST + "  Differential Pairs", self._import_diff_pairs),
                (Icons.RULES + "  Design Rules", self._import_design_rules),
                (None, None),
                ("⚠️  Table imports (BOM, Layers, etc.) require Markdown mode", None),
            ]
        else:
            # Full menu for Markdown mode
            items = [
                (Icons.BOARD + "  Board Info", self._import_board_info),
                (Icons.BOM + "  Bill of Materials (BOM)", self._import_bom),
                (Icons.LAYERS + "  Layer Stackup", self._import_stackup),
                (Icons.LAYERS + "  Layer Info", self._import_layers),
                (None, None),
                (Icons.NETLIST + "  Netlist", self._import_netlist),
                (Icons.NETLIST + "  Differential Pairs", self._import_diff_pairs),
                (Icons.RULES + "  Design Rules", self._import_design_rules),
                (Icons.DRILL + "  Drill Table", self._import_drill_table),
                (None, None),
                (Icons.ALL + "  Import All", self._import_all),
            ]
        
        for label, handler in items:
            if label is None:
                menu.AppendSeparator()
            else:
                item = menu.Append(wx.ID_ANY, label)
                if handler:
                    menu.Bind(wx.EVT_MENU, handler, item)
                else:
                    # Disabled item (info text)
                    item.Enable(False)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _get_import_header(self, title):
        """Generate header with title and date for imported content."""
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"## {title}\n**Imported:** {date_str}\n\n"
    
    def _import_board_info(self, event):
        """Import board size/info."""
        try:
            header = self._get_import_header("Board Information")
            info = self.metadata_extractor.extract('board_size')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing board info: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_bom(self, event):
        """Import Bill of Materials."""
        try:
            header = self._get_import_header("Bill of Materials")
            info = self.metadata_extractor.extract('bom')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing BOM: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_stackup(self, event):
        """Import layer stackup."""
        try:
            header = self._get_import_header("Layer Stackup")
            info = self.metadata_extractor.extract('stackup')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing stackup: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_layers(self, event):
        """Import layer information."""
        try:
            header = self._get_import_header("Layer Information")
            info = self.metadata_extractor.extract('layers')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing layers: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_netlist(self, event):
        """Import netlist summary."""
        try:
            header = self._get_import_header("Netlist Summary")
            info = self.metadata_extractor.extract('netlist')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing netlist: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_diff_pairs(self, event):
        """Import differential pairs."""
        try:
            header = self._get_import_header("Differential Pairs")
            info = self.metadata_extractor.extract('diff_pairs')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing differential pairs: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_design_rules(self, event):
        """Import design rules."""
        try:
            header = self._get_import_header("Design Rules")
            info = self.metadata_extractor.extract('design_rules')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing design rules: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_drill_table(self, event):
        """Import drill table."""
        try:
            header = self._get_import_header("Drill Table")
            info = self.metadata_extractor.extract('drill_table')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing drill table: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_all(self, event):
        """Import all metadata."""
        try:
            header = self._get_import_header("Complete Board Metadata")
            info = self.metadata_extractor.extract('all')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing all metadata: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _insert_text(self, text):
        """Insert text at cursor or end, handling markdown formatting for Visual Editor."""
        try:
            # Check if we're in Visual Editor mode
            if self._use_visual_editor and hasattr(self, 'visual_editor') and self.visual_editor:
                # Always use markdown formatter for proper rendering of headings, tables, bold, etc.
                try:
                    self.visual_editor.insert_markdown_as_formatted(text)
                except Exception as format_err:
                    # Fallback: insert as plain text if parsing fails
                    print(f"[KiNotes] Markdown format error: {format_err}")
                    self.visual_editor.editor.WriteText(text + "\n")
                    
                # Move cursor to end and mark as modified
                self.visual_editor.SetInsertionPointEnd()
                self.visual_editor._modified = True
            else:
                # Markdown mode - insert text as-is
                current = self._get_note_content()
                if current and not current.endswith("\n"):
                    current += "\n"
                current += "\n" + text
                self._set_note_content(current)
                if self.text_editor:
                    self.text_editor.SetInsertionPointEnd()
            
            # Switch to notes tab
            self._show_tab(0)
            
        except Exception as e:
            wx.MessageBox(f"Error inserting text: {e}", "Insert Error", wx.OK | wx.ICON_ERROR)

    def _on_export_pdf(self):
        """Export notes to PDF based on format setting."""
        try:
            # Check PDF format setting
            pdf_format = getattr(self, '_pdf_format', 'markdown')
            
            if pdf_format == 'visual' and self._use_visual_editor and hasattr(self, 'visual_editor') and self.visual_editor:
                # Export from Visual Editor with formatting
                filepath = self.pdf_exporter.export_visual(self.visual_editor.editor)
            else:
                # Export as Markdown (plain text)
                content = self._get_note_content()
                filepath = self.pdf_exporter.export(content)
            
            if filepath:
                wx.MessageBox("Exported to:\n" + filepath, "PDF Export", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox("Export failed: " + str(e), "Error", wx.OK | wx.ICON_ERROR)

    def _on_manual_save(self):
        """Manual save."""
        try:
            self._save_notes()
            self._save_todos()
            wx.MessageBox("Notes saved successfully!", "Saved", wx.OK | wx.ICON_INFORMATION)
            self._log_event("save", EventLevel.SAVE, "Manual save completed")
        except:
            self._log_event("save", EventLevel.ERROR, "Manual save failed")
            pass
    
    def _on_text_changed(self, event):
        self._modified = True
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle @REF clicks (Markdown mode only)."""
        if not self.text_editor:
            event.Skip()
            return
        try:
            pos = self.text_editor.HitTestPos(event.GetPosition())[1]
            if pos >= 0:
                text = self.text_editor.GetValue()
                word = self._get_word_at_pos(text, pos)
                if word.startswith("@"):
                    self._highlight_component(word[1:])
                    return
        except:
            pass
        event.Skip()
    
    def _get_word_at_pos(self, text, pos):
        if pos < 0 or pos >= len(text):
            return ""
        start = end = pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in "@_"):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in "@_"):
            end += 1
        return text[start:end]
    
    def _highlight_component(self, ref):
        """Highlight component in PCB."""
        try:
            if self.designator_linker.highlight(ref):
                pass
        except:
            pass
    
    # ============================================================
    # DATA MANAGEMENT
    # ============================================================
    
    def _start_auto_save_timer(self):
        """Start auto-save timer - uses configurable interval from settings."""
        try:
            # Load interval from settings, fallback to default
            settings = self.notes_manager.load_settings() or {}
            self._timer_interval_ms = settings.get('timer_interval_ms', PERFORMANCE_DEFAULTS['timer_interval_ms'])
            # Enforce min/max bounds
            self._timer_interval_ms = max(PERFORMANCE_DEFAULTS['timer_min_ms'], 
                                          min(self._timer_interval_ms, PERFORMANCE_DEFAULTS['timer_max_ms']))
            
            self._auto_save_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
            self._auto_save_timer.Start(self._timer_interval_ms)
            debug_print(f"[KiNotes] Auto-save timer started: {self._timer_interval_ms}ms interval")
        except:
            pass
    
    def _on_auto_save(self, event):
        """Auto-save if modified and update timer displays."""
        # Update timer displays
        self._timer_update_tick += 1
        
        # Update timer display every tick (timer already throttled by interval)
        self._update_timer_displays()
        
        # Update global timer display
        try:
            self.global_time_label.SetLabel(self.time_tracker.get_total_time_string())
        except:
            pass
        
        # Save if content modified
        if self._modified:
            try:
                self._save_notes()
                self._save_todos()
                self._modified = False
            except:
                pass
        self._timer_update_tick = 0
    
    def _load_all_data(self):
        """Load saved data."""
        try:
            content = self.notes_manager.load()
            if content:
                self._set_note_content(content)
                self._apply_editor_colors()
        except:
            pass
        
        try:
            todos = self.notes_manager.load_todos()
            if todos:
                for todo in todos:
                    time_spent = todo.get("time_spent", 0)
                    history = todo.get("history", [])
                    self._add_todo_item(
                        todo.get("text", ""), 
                        todo.get("done", False),
                        time_spent,
                        history
                    )
            else:
                # Create 3 default template tasks for new projects
                self._add_todo_item("Schematic Review", False)
                self._add_todo_item("Layout Check", False)
                self._add_todo_item("Design Verification", False)
                self._save_todos()  # Save defaults
        except:
            pass
        
        # Load version log
        try:
            self._load_version_log()
        except:
            pass
        
        self._modified = False
    
    def _save_notes(self):
        """Save notes."""
        try:
            self.notes_manager.save(self._get_note_content())
        except:
            pass
    
    def _save_todos(self):
        """Save todos with time tracking data."""
        try:
            todos = []
            for item in self._todo_items:
                item_id = item["id"]
                timer_data = self.time_tracker.task_timers.get(item_id, {})
                todos.append({
                    "text": item["text"].GetValue(),
                    "done": item["checkbox"].GetValue(),
                    "time_spent": timer_data.get("time_spent", 0),
                    "history": timer_data.get("history", []),
                    "is_running": timer_data.get("is_running", False)
                })
            self.notes_manager.save_todos(todos)
        except Exception as e:
            print(f"[KiNotes] Todo save warning: {e}")
    
    def force_save(self):
        """Force save all data with full error protection."""
        try:
            self._save_notes()
        except Exception as e:
            print(f"[KiNotes] Notes save error: {e}")
        
        try:
            self._save_todos()
        except Exception as e:
            print(f"[KiNotes] Todos save error: {e}")
        
        try:
            self._save_version_log()
        except Exception as e:
            print(f"[KiNotes] Version log save error: {e}")
        
        try:
            # CRITICAL: Save settings to prevent corruption on restart
            self._save_color_settings()
        except Exception as e:
            print(f"[KiNotes] Settings save error: {e}")
        
        try:
            # Auto-export work diary on save
            self._auto_export_diary_on_close()
        except Exception as e:
            print(f"[KiNotes] Diary export error: {e}")
    
    def cleanup(self):
        """Cleanup ALL resources - critical for repeated open/close cycles."""
        print("[KiNotes] Starting comprehensive cleanup...")
        
        # 1. Stop task timer
        try:
            if hasattr(self, 'time_tracker') and self.time_tracker:
                if self.time_tracker.current_running_task_id is not None:
                    self.time_tracker.stop_task(self.time_tracker.current_running_task_id)
                print("[KiNotes] Task timer stopped")
        except Exception as e:
            print(f"[KiNotes] Task timer cleanup error: {e}")
        
        # 2. Stop auto-save timer
        try:
            if hasattr(self, '_auto_save_timer') and self._auto_save_timer:
                self._auto_save_timer.Stop()
                self._auto_save_timer = None
                print("[KiNotes] Auto-save timer stopped")
        except Exception as e:
            print(f"[KiNotes] Auto-save timer cleanup error: {e}")
        
        # 3. Unbind all event handlers
        try:
            self.Unbind(wx.EVT_TIMER)
            self.Unbind(wx.EVT_TEXT)
            self.Unbind(wx.EVT_TEXT_ENTER)
            print("[KiNotes] Event handlers unbound")
        except Exception as e:
            print(f"[KiNotes] Event unbind warning: {e}")
        
        # 4. Save final data
        try:
            self.force_save()
            print("[KiNotes] Final data saved")
        except Exception as e:
            print(f"[KiNotes] Final save error: {e}")
        
        # 5. Cleanup visual editor (release wx resources)
        try:
            if hasattr(self, 'visual_editor') and self.visual_editor:
                # Call the visual editor's cleanup method
                try:
                    self.visual_editor.cleanup()
                except Exception as e:
                    print(f"[KiNotes] Visual editor cleanup method warning: {e}")
                
                # Destroy the editor
                try:
                    self.visual_editor.Destroy()
                except Exception as e:
                    print(f"[KiNotes] Visual editor destroy warning: {e}")
                
                self.visual_editor = None
                print("[KiNotes] Visual editor cleaned up")
        except Exception as e:
            print(f"[KiNotes] Visual editor cleanup warning: {e}")
        
        # 6. Cleanup markdown editor (release wx resources)
        try:
            if hasattr(self, '_text_control') and self._text_control:
                self._text_control.Unbind(wx.EVT_TEXT)
                print("[KiNotes] Markdown editor cleaned up")
        except Exception as e:
            print(f"[KiNotes] Markdown editor cleanup warning: {e}")
        
        # 7. Cleanup color picker (release wx resources)
        try:
            if hasattr(self, '_bg_color_picker'):
                if hasattr(self._bg_color_picker, 'Unbind'):
                    self._bg_color_picker.Unbind(wx.EVT_COLOURPICKER_CHANGED)
            if hasattr(self, '_text_color_picker'):
                if hasattr(self._text_color_picker, 'Unbind'):
                    self._text_color_picker.Unbind(wx.EVT_COLOURPICKER_CHANGED)
            print("[KiNotes] Color pickers cleaned up")
        except Exception as e:
            print(f"[KiNotes] Color picker cleanup warning: {e}")
        
        # 8. Cleanup net linker (if active)
        try:
            if hasattr(self, 'net_linker') and self.net_linker:
                self.net_linker = None
                print("[KiNotes] Net linker cleaned up")
        except Exception as e:
            print(f"[KiNotes] Net linker cleanup warning: {e}")
        
        # 9. Cleanup designator linker (if active)
        try:
            if hasattr(self, 'designator_linker') and self.designator_linker:
                self.designator_linker = None
                print("[KiNotes] Designator linker cleaned up")
        except Exception as e:
            print(f"[KiNotes] Designator linker cleanup warning: {e}")
        
        # 10. Cleanup notes manager
        try:
            if hasattr(self, 'notes_manager') and self.notes_manager:
                self.notes_manager = None
                print("[KiNotes] Notes manager cleaned up")
        except Exception as e:
            print(f"[KiNotes] Notes manager cleanup warning: {e}")
        
        # 11. Cleanup debug logger
        try:
            if hasattr(self, 'debug_logger') and self.debug_logger:
                self.debug_logger = None
                print("[KiNotes] Debug logger cleaned up")
        except Exception as e:
            print(f"[KiNotes] Debug logger cleanup warning: {e}")
        
        # 12. Mark clean shutdown for crash detection (last)
        try:
            if self.crash_safety and hasattr(self.crash_safety, 'mark_clean_shutdown'):
                self.crash_safety.mark_clean_shutdown()
                print("[KiNotes] Crash safety marked clean shutdown")
        except Exception as e:
            print(f"[KiNotes] Crash safety cleanup warning: {e}")
        
        # 13. Clear crash safety reference
        try:
            self.crash_safety = None
            print("[KiNotes] Crash safety reference cleared")
        except Exception as e:
            print(f"[KiNotes] Crash safety cleanup error: {e}")
        
        print("[KiNotes] Cleanup complete")

