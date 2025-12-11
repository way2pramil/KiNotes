"""
Debug Event Logger for KiNotes
Lightweight event tracking with color-coded messages (errors, success, warnings, events).
Industry-standard severity levels and timestamps.
"""

import wx
import datetime
from typing import Optional, List, Tuple
from enum import Enum

class EventLevel(Enum):
    """Standard event severity levels (industry-standard)."""
    DEBUG = ("DEBUG", wx.Colour(100, 100, 100))      # Gray
    INFO = ("INFO", wx.Colour(0, 100, 200))           # Blue
    SUCCESS = ("✓ SUCCESS", wx.Colour(0, 150, 0))     # Green
    WARNING = ("⚠ WARNING", wx.Colour(200, 120, 0))   # Orange
    ERROR = ("✗ ERROR", wx.Colour(220, 0, 0))         # Red
    SAVE = ("💾 SAVE", wx.Colour(100, 150, 200))      # Light Blue
    CROSSPROBE = ("🔗 XPROBE", wx.Colour(150, 0, 150)) # Purple


class DebugEventLogger:
    """
    Lightweight event logger for KiNotes.
    Tracks events with timestamps, severity levels, and color coding.
    Max 100 entries to keep memory footprint light.
    """
    
    MAX_ENTRIES = 100
    
    def __init__(self, parent: wx.Window = None):
        """
        Initialize the event logger.
        
        Args:
            parent: Parent window for UI components
        """
        self.parent = parent
        self._events: List[Tuple[datetime.datetime, EventLevel, str]] = []
        self._event_callbacks: List[callable] = []
    
    def log(self, level: EventLevel, message: str):
        """
        Log an event with timestamp and severity level.
        
        Args:
            level: EventLevel enum (DEBUG, INFO, SUCCESS, WARNING, ERROR, SAVE, CROSSPROBE)
            message: Event message (no timestamp needed, added automatically)
        """
        timestamp = datetime.datetime.now()
        self._events.append((timestamp, level, message))
        
        # Keep only last MAX_ENTRIES
        if len(self._events) > self.MAX_ENTRIES:
            self._events = self._events[-self.MAX_ENTRIES:]
        
        # Notify listeners
        for callback in self._event_callbacks:
            try:
                callback(timestamp, level, message)
            except Exception:
                pass
    
    # Convenience methods matching industry-standard naming
    def debug(self, message: str):
        """Log debug message."""
        self.log(EventLevel.DEBUG, message)
    
    def info(self, message: str):
        """Log info message."""
        self.log(EventLevel.INFO, message)
    
    def success(self, message: str):
        """Log success message."""
        self.log(EventLevel.SUCCESS, message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.log(EventLevel.WARNING, message)
    
    def error(self, message: str):
        """Log error message."""
        self.log(EventLevel.ERROR, message)
    
    def save(self, message: str):
        """Log save event."""
        self.log(EventLevel.SAVE, message)
    
    def crossprobe(self, message: str):
        """Log cross-probe event."""
        self.log(EventLevel.CROSSPROBE, message)
    
    def subscribe(self, callback: callable):
        """
        Subscribe to events.
        
        Args:
            callback: Function(timestamp, level, message) called for each event
        """
        if callback not in self._event_callbacks:
            self._event_callbacks.append(callback)
    
    def unsubscribe(self, callback: callable):
        """Unsubscribe from events."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
    
    def get_all_events(self) -> List[Tuple[str, EventLevel, str]]:
        """
        Get all logged events as formatted strings.
        
        Returns:
            List of (formatted_timestamp, level, message) tuples
        """
        result = []
        for timestamp, level, message in self._events:
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
            result.append((time_str, level, message))
        return result
    
    def clear(self):
        """Clear all logged events."""
        self._events.clear()
    
    def get_events_by_level(self, level: EventLevel) -> List[Tuple[str, str]]:
        """
        Get events filtered by severity level.
        
        Args:
            level: EventLevel to filter by
        
        Returns:
            List of (timestamp_str, message) tuples
        """
        result = []
        for timestamp, evt_level, message in self._events:
            if evt_level == level:
                time_str = timestamp.strftime("%H:%M:%S")
                result.append((time_str, message))
        return result
    
    def count_by_level(self) -> dict:
        """
        Count events by severity level.
        
        Returns:
            Dict of {EventLevel: count}
        """
        counts = {}
        for timestamp, level, message in self._events:
            counts[level] = counts.get(level, 0) + 1
        return counts


class DebugEventPanel(wx.Panel):
    """
    Lightweight debug event display panel.
    Shows real-time event log with color coding and filtering.
    Designed to be compact and easy to integrate.
    """
    
    def __init__(self, parent: wx.Window, logger: DebugEventLogger, 
                 dark_mode: bool = True):
        """
        Initialize debug event panel.
        
        Args:
            parent: Parent window
            logger: DebugEventLogger instance
            dark_mode: Whether to use dark theme
        """
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        
        self.logger = logger
        self.dark_mode = dark_mode
        self._init_theme()
        self._init_ui()
        
        # Subscribe to events
        self.logger.subscribe(self._on_event_logged)
    
    def _init_theme(self):
        """Initialize theme colors."""
        if self.dark_mode:
            self.bg_color = wx.Colour(30, 30, 30)
            self.text_color = wx.Colour(200, 200, 200)
            self.light_gray = wx.Colour(80, 80, 80)
            self.border_color = wx.Colour(60, 60, 60)
        else:
            self.bg_color = wx.Colour(245, 245, 245)
            self.text_color = wx.Colour(50, 50, 50)
            self.light_gray = wx.Colour(180, 180, 180)
            self.border_color = wx.Colour(200, 200, 200)
        
        self.SetBackgroundColour(self.bg_color)
    
    def _init_ui(self):
        """Initialize UI components."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header with title and filters
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        title = wx.StaticText(self, label="📋 Event Log")
        title.SetForegroundColour(self.text_color)
        font = title.GetFont()
        font.MakeBold()
        title.SetFont(font)
        header_sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Filter buttons - only show errors/warnings by default
        self._filter_all_btn = wx.ToggleButton(self, label="All")
        self._filter_all_btn.SetValue(False)
        self._filter_all_btn.Bind(wx.EVT_TOGGLEBUTTON, self._on_filter_changed)
        header_sizer.Add(self._filter_all_btn, 0, wx.RIGHT, 5)
        
        self._filter_errors_btn = wx.ToggleButton(self, label="Errors")
        self._filter_errors_btn.SetValue(True)
        self._filter_errors_btn.Bind(wx.EVT_TOGGLEBUTTON, self._on_filter_changed)
        header_sizer.Add(self._filter_errors_btn, 0, wx.RIGHT, 5)
        
        self._filter_warnings_btn = wx.ToggleButton(self, label="Warnings")
        self._filter_warnings_btn.SetValue(True)
        self._filter_warnings_btn.Bind(wx.EVT_TOGGLEBUTTON, self._on_filter_changed)
        header_sizer.Add(self._filter_warnings_btn, 0, wx.RIGHT, 5)
        
        clear_btn = wx.Button(self, label="Clear")
        clear_btn.Bind(wx.EVT_BUTTON, lambda e: self._clear_log())
        header_sizer.Add(clear_btn, 0, wx.RIGHT, 5)
        
        header_sizer.AddStretchSpacer()
        
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # Event list (read-only RichTextCtrl for better formatting)
        self._event_list = wx.TextCtrl(
            self, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(400, 150)
        )
        self._event_list.SetBackgroundColour(self.light_gray)
        self._event_list.SetForegroundColour(self.text_color)
        
        # Use monospace font for timestamps and alignment
        font = wx.Font(8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self._event_list.SetFont(font)
        
        main_sizer.Add(self._event_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Stats bar at bottom
        stats_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._stats_text = wx.StaticText(self, label="Events: 0 | Errors: 0 | Warnings: 0")
        self._stats_text.SetForegroundColour(self.light_gray)
        stats_sizer.Add(self._stats_text, 0, wx.ALIGN_CENTER_VERTICAL)
        stats_sizer.AddStretchSpacer()
        
        main_sizer.Add(stats_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        self.SetSizer(main_sizer)
    
    def _on_event_logged(self, timestamp: datetime.datetime, level: EventLevel, message: str):
        """Called when an event is logged."""
        self._refresh_display()
    
    def _on_filter_changed(self, event):
        """Called when filter buttons are toggled."""
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the event list display based on current filters."""
        all_events = self.logger.get_all_events()
        
        # Determine which events to show
        show_all = self._filter_all_btn.GetValue()
        show_errors = self._filter_errors_btn.GetValue()
        show_warnings = self._filter_warnings_btn.GetValue()
        
        # Collect events to display
        display_events = []
        for time_str, level, message in all_events:
            if show_all:
                display_events.append((time_str, level, message))
            elif show_errors and level == EventLevel.ERROR:
                display_events.append((time_str, level, message))
            elif show_warnings and level == EventLevel.WARNING:
                display_events.append((time_str, level, message))
        
        # Format display
        text_lines = []
        for time_str, level, message in display_events:
            # Format: [HH:MM:SS] [LEVEL] Message
            level_name, _ = level.value
            line = f"[{time_str}] [{level_name:10s}] {message}"
            text_lines.append(line)
        
        # Show last 20 events
        display_text = "\n".join(text_lines[-20:])
        self._event_list.SetValue(display_text)
        
        # Scroll to bottom
        self._event_list.SetInsertionPointEnd()
        
        # Update stats
        counts = self.logger.count_by_level()
        error_count = counts.get(EventLevel.ERROR, 0)
        warning_count = counts.get(EventLevel.WARNING, 0)
        total_count = len(all_events)
        
        stats = f"Events: {total_count} | Errors: {error_count} | Warnings: {warning_count}"
        self._stats_text.SetLabel(stats)
    
    def _clear_log(self):
        """Clear the event log."""
        self.logger.clear()
        self._refresh_display()
    
    def set_dark_mode(self, dark_mode: bool):
        """Update theme for dark/light mode."""
        self.dark_mode = dark_mode
        self._init_theme()
        self.SetBackgroundColour(self.bg_color)
        self._event_list.SetBackgroundColour(self.light_gray)
        self._event_list.SetForegroundColour(self.text_color)
        self._stats_text.SetForegroundColour(self.light_gray)
        self.Refresh()
        self._refresh_display()


# Global logger instance for convenient access
_global_logger: Optional[DebugEventLogger] = None


def get_debug_logger() -> DebugEventLogger:
    """Get or create the global debug logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = DebugEventLogger()
    return _global_logger


def init_debug_logger(logger: DebugEventLogger):
    """Initialize the global debug logger instance."""
    global _global_logger
    _global_logger = logger
