"""
KiNotes Main Panel - Modern UI with Dark Theme Toggle
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
User-selectable background and text colors with dark mode
Time tracking with per-task stopwatch and work diary export
"""
import wx
import wx.lib.scrolledpanel as scrolled
import os
import sys
import datetime
import json
import time
import re
import fnmatch


# ============================================================
# COLOR PRESETS - Light Mode
# ============================================================
BACKGROUND_COLORS = {
    "Snow Gray": "#F8F9FA",
    "Ivory Paper": "#FFFDF5",
    "Mint Mist": "#EAF7F1",
    "Sakura Mist": "#FAF1F4",
    "Storm Fog": "#E4E7EB",
}

TEXT_COLORS = {
    "Carbon Black": "#2B2B2B",
    "Deep Ink": "#1A1A1A",
    "Slate Night": "#36454F",
    "Cocoa Brown": "#4E342E",
    "Evergreen Ink": "#004D40",
}

# Dark Mode Colors
# ============================================================
# IMPROVED APPLE-STYLE THEME
# ============================================================
DARK_THEME = {
    "bg_panel":     "#1C1C1E",  # Apple System Gray 6 (Dark)
    "bg_toolbar":   "#2C2C2E",  # Apple System Gray 5 (Dark) - Slightly lighter for contrast
    "bg_button":    "#3A3A3C",  # Apple System Gray 4 (Dark)
    "bg_button_hover": "#48484A",
    "bg_editor":    "#1C1C1E",  # Matches panel for seamless look
    "text_primary": "#FFFFFF",  # Pure White
    "text_secondary": "#98989D",# Apple System Gray (Text)
    "border":       "#38383A",  # Subtle separators
    "accent_blue":  "#0A84FF",  # iOS Blue (Dark Mode)
    "accent_green": "#30D158",  # iOS Green (Dark Mode)
    "accent_red":   "#FF453A",  # iOS Red (Dark Mode)
}

LIGHT_THEME = {
    "bg_panel":     "#F2F2F7",  # Apple System Gray 6 (Light) - Not pure white!
    "bg_toolbar":   "#FFFFFF",  # Pure white cards on light gray bg
    "bg_button":    "#E5E5EA",  # Apple System Gray 3 (Light)
    "bg_button_hover": "#D1D1D6",
    "bg_editor":    "#FFFFFF",
    "text_primary": "#000000",
    "text_secondary": "#8E8E93",
    "border":       "#C6C6C8",
    "accent_blue":  "#007AFF",  # iOS Blue
    "accent_green": "#34C759",  # iOS Green
    "accent_red":   "#FF3B30",  # iOS Red
}

# Dark Mode Background Colors (Blender-style)
DARK_BACKGROUND_COLORS = {
    "Charcoal": "#1C1C1E",
    "Obsidian": "#0D0D0D",
    "Midnight": "#121212",
    "Slate Dark": "#1E1E2E",
    "Deep Space": "#0F0F1A",
}

DARK_TEXT_COLORS = {
    "Pure White": "#FFFFFF",
    "Soft White": "#E5E5E5",
    "Silver": "#C0C0C0",
    "Light Gray": "#A0A0A0",
    "Neon Blue": "#00D4FF",
}


def hex_to_colour(hex_str):
    """Convert hex color to wx.Colour."""
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return wx.Colour(r, g, b)


# ============================================================
# TIME TRACKER - Per-task stopwatch with RTC logging
# ============================================================
class TimeTracker:
    """Manages per-task time tracking with session history and persistence."""
    
    def __init__(self):
        self.enable_time_tracking = True
        self.time_format_24h = True
        self.show_work_diary_button = True
        self.current_running_task_id = None
        self.task_timers = {}  # {task_id: {"time_spent": seconds, "is_running": bool, ...}}
    
    def create_task_timer(self, task_id):
        """Initialize timer data for a new task."""
        self.task_timers[task_id] = {
            "text": "",
            "done": False,
            "time_spent": 0,
            "is_running": False,
            "last_start_time": None,
            "history": []  # [{"start": timestamp, "stop": timestamp}, ...]
        }
    
    def start_task(self, task_id):
        """Start timer for a task. Auto-stop any other running task."""
        if self.current_running_task_id is not None and self.current_running_task_id != task_id:
            self.stop_task(self.current_running_task_id)
        
        if task_id in self.task_timers:
            self.task_timers[task_id]["is_running"] = True
            self.task_timers[task_id]["last_start_time"] = time.time()
            self.current_running_task_id = task_id
    
    def stop_task(self, task_id):
        """Stop timer for a task and accumulate time_spent."""
        if task_id in self.task_timers and self.task_timers[task_id]["is_running"]:
            start = self.task_timers[task_id]["last_start_time"]
            if start is not None:
                elapsed = time.time() - start
                self.task_timers[task_id]["time_spent"] += elapsed
                
                # Log session history
                self.task_timers[task_id]["history"].append({
                    "start": int(start),
                    "stop": int(time.time())
                })
            
            self.task_timers[task_id]["is_running"] = False
            self.task_timers[task_id]["last_start_time"] = None
            
            if self.current_running_task_id == task_id:
                self.current_running_task_id = None
    
    def get_task_time_string(self, task_id):
        """Return formatted time string for a task."""
        if task_id not in self.task_timers:
            return "⏱ 00:00:00"
        
        data = self.task_timers[task_id]
        total_seconds = int(data["time_spent"])
        
        # Add running time if currently active
        if data["is_running"] and data["last_start_time"]:
            total_seconds += int(time.time() - data["last_start_time"])
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"⏱ {hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_total_time_string(self):
        """Return total time across all tasks."""
        total_seconds = 0
        
        for data in self.task_timers.values():
            total_seconds += int(data["time_spent"])
            
            # Add running time if currently active
            if data["is_running"] and data["last_start_time"]:
                total_seconds += int(time.time() - data["last_start_time"])
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"⏱ Total Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_total_seconds(self):
        """Get total time in seconds."""
        total_seconds = 0
        for data in self.task_timers.values():
            total_seconds += int(data["time_spent"])
            if data["is_running"] and data["last_start_time"]:
                total_seconds += int(time.time() - data["last_start_time"])
        return total_seconds
    
    def mark_task_done(self, task_id):
        """Mark task as done and stop timer."""
        if task_id in self.task_timers:
            self.task_timers[task_id]["done"] = True
            self.stop_task(task_id)
    
    def delete_task(self, task_id):
        """Remove task and subtract from total if running."""
        if task_id in self.task_timers:
            self.stop_task(task_id)
            del self.task_timers[task_id]
    
    def export_work_diary(self):
        """Generate Markdown work diary content."""
        total_sec = self.get_total_seconds()
        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        
        lines = [
            "# Work Log — KiCad Project",
            f"**Total: {hours}h {minutes}m**",
            ""
        ]
        
        for task_id, data in self.task_timers.items():
            if data["history"]:
                task_sec = int(data["time_spent"])
                t_hours = task_sec // 3600
                t_minutes = (task_sec % 3600) // 60
                
                lines.append(f"## Task: {data['text']}")
                
                for session in data["history"]:
                    start_dt = datetime.datetime.fromtimestamp(session['start']).strftime("%H:%M")
                    stop_dt = datetime.datetime.fromtimestamp(session['stop']).strftime("%H:%M")
                    sess_sec = session['stop'] - session['start']
                    sess_min = sess_sec // 60
                    lines.append(f"- Session: {start_dt} → {stop_dt} ({sess_min} min)")
                
                lines.append(f"**Total: {t_hours}h {t_minutes}m**")
                lines.append("")
        
        return "\n".join(lines)
    
    def get_last_session_string(self, task_id, format_24h=True):
        """
        Get last completed session as inline display string.
        Only returns string if session exists and is completed (not running).
        Format: "10:12 → 10:40 (28min)"
        Returns: "" if no sessions or task is running
        """
        if task_id not in self.task_timers:
            return ""
        
        data = self.task_timers[task_id]
        history = data.get("history", [])
        
        # Only show if task has completed sessions and is NOT running
        if not history or data.get("is_running", False):
            return ""
        
        # Get last session
        last_session = history[-1]
        start_ts = last_session.get("start", 0)
        stop_ts = last_session.get("stop", 0)
        
        if not start_ts or not stop_ts:
            return ""
        
        # Format times based on format_24h
        if format_24h:
            start_time = datetime.datetime.fromtimestamp(start_ts).strftime("%H:%M")
            stop_time = datetime.datetime.fromtimestamp(stop_ts).strftime("%H:%M")
        else:
            start_time = datetime.datetime.fromtimestamp(start_ts).strftime("%I:%M %p")
            stop_time = datetime.datetime.fromtimestamp(stop_ts).strftime("%I:%M %p")
        
        # Calculate duration
        duration = stop_ts - start_ts
        if duration < 60:
            duration_str = f"{duration}s"
        elif duration < 3600:
            minutes = duration // 60
            duration_str = f"{minutes}m"
        else:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            duration_str = f"{hours}h {minutes}m" if minutes else f"{hours}h"
        
        return f"({start_time} → {stop_time} {duration_str})"
    
    def get_session_history_tooltip(self, task_id, format_24h=True):
        """
        Generate full session history for tooltip display.
        Returns formatted list of all sessions with total.
        """
        if task_id not in self.task_timers:
            return ""
        
        data = self.task_timers[task_id]
        history = data.get("history", [])
        
        if not history:
            return ""
        
        lines = []
        total_seconds = 0
        
        for session in history:
            start_ts = session.get("start", 0)
            stop_ts = session.get("stop", 0)
            
            if not start_ts or not stop_ts:
                continue
            
            if format_24h:
                start_time = datetime.datetime.fromtimestamp(start_ts).strftime("%H:%M")
                stop_time = datetime.datetime.fromtimestamp(stop_ts).strftime("%H:%M")
            else:
                start_time = datetime.datetime.fromtimestamp(start_ts).strftime("%I:%M %p")
                stop_time = datetime.datetime.fromtimestamp(stop_ts).strftime("%I:%M %p")
            
            duration = stop_ts - start_ts
            total_seconds += duration
            
            if duration < 60:
                duration_str = f"{duration}s"
            elif duration < 3600:
                minutes = duration // 60
                duration_str = f"{minutes}m"
            else:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                duration_str = f"{hours}h {minutes}m" if minutes else f"{hours}h"
            
            lines.append(f"• {start_time} → {stop_time} ({duration_str})")
        
        # Add total
        if total_seconds > 0:
            t_hours = total_seconds // 3600
            t_minutes = (total_seconds % 3600) // 60
            total_str = f"{t_hours}h {t_minutes}m" if t_minutes else f"{t_hours}h"
            
            header = f"Work Sessions ({len(history)})"
            lines.insert(0, header)
            lines.append(f"Total: {total_str}")
        
        return "\n".join(lines)
    
    def to_json_data(self):
        """Convert timer data to JSON-serializable format."""
        return {
            "current_running_task_id": self.current_running_task_id,
            "task_timers": self.task_timers
        }
    
    def from_json_data(self, data):
        """Load timer data from JSON."""
        if data:
            self.current_running_task_id = data.get("current_running_task_id")
            self.task_timers = data.get("task_timers", {})



# ROUNDED BUTTON CLASS - Modern Unified Buttons
# ============================================================
class RoundedButton(wx.Panel):
    """Custom rounded button with hover and press effects - KiCad DPI aware."""
    
    def __init__(self, parent, label="", size=(120, 44), bg_color="#4285F4", 
                 fg_color="#FFFFFF", icon="", corner_radius=8, font_size=11,
                 font_weight=wx.FONTWEIGHT_BOLD):
        super().__init__(parent, size=size)
        
        self.label = label
        self.icon = icon
        self.bg_color = hex_to_colour(bg_color) if isinstance(bg_color, str) else bg_color
        self.fg_color = hex_to_colour(fg_color) if isinstance(fg_color, str) else fg_color
        self.corner_radius = corner_radius
        self.is_hovered = False
        self.is_pressed = False
        self.callback = None
        self.button_size = size
        self.base_font_size = font_size
        self.font_weight = font_weight
        
        # Don't force max size - let parent control height via DPI
        self.SetMinSize(size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.font = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, font_weight)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_press)
        self.Bind(wx.EVT_LEFT_UP, self._on_release)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _darken_color(self, color, amount):
        """Darken a color by amount."""
        r = max(0, color.Red() - amount)
        g = max(0, color.Green() - amount)
        b = max(0, color.Blue() - amount)
        return wx.Colour(r, g, b)

    def _on_press(self, event):
        self.is_pressed = True
        self.Refresh()
        event.Skip()

    def _on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.Refresh()
            pos = event.GetPosition()
            rect = self.GetClientRect()
            if rect.Contains(pos) and self.callback:
                self.callback(event)

    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        # Use actual rendered size (respects KiCad DPI scaling)
        w, h = self.GetSize()
        
        # Ensure minimum dimensions
        if w <= 0 or h <= 0:
            return
        
        # Clear background completely
        parent = self.GetParent()
        if parent:
            parent_bg = parent.GetBackgroundColour()
        else:
            parent_bg = wx.Colour(255, 255, 255)
        
        gc.SetBrush(wx.Brush(parent_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        
        # Determine button color based on state
        if self.is_pressed:
            bg = self._darken_color(self.bg_color, 40)
        elif self.is_hovered:
            bg = self._darken_color(self.bg_color, 15)
        else:
            bg = self.bg_color
        
        # Draw rounded button - scale corner radius to height
        corner = min(self.corner_radius, h // 3)
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, corner)
        
        # Draw text with icon - scale font dynamically
        gc.SetFont(self.font, self.fg_color)
        display_text = self.icon + "  " + self.label if self.icon else self.label
        text_w, text_h = gc.GetTextExtent(display_text)[:2]
        
        # Add padding compensation
        x = (w - text_w) / 2
        y = (h - text_h) / 2
        gc.DrawText(display_text, x, y)
    
    def _on_enter(self, event):
        self.is_hovered = True
        self.Refresh()
    
    def _on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.Refresh()
    
    def Bind_Click(self, callback):
        """Bind click callback."""
        self.callback = callback
    
    def SetColors(self, bg_color, fg_color):
        """Update button colors."""
        self.bg_color = hex_to_colour(bg_color) if isinstance(bg_color, str) else bg_color
        self.fg_color = hex_to_colour(fg_color) if isinstance(fg_color, str) else fg_color
        self.Refresh()


# ============================================================
# TOGGLE SWITCH - Dark Mode Toggle
# ============================================================
class PlayPauseButton(wx.Panel):
    """Play/Pause button for timer control - official wxPython compatible."""
    
    def __init__(self, parent, size=(42, 28), is_on=False):
        super().__init__(parent, size=size)
        
        self.is_on = is_on
        self.callback = None
        
        self.color_running = hex_to_colour("#34C759")  # Green when running
        self.color_paused = hex_to_colour("#8E8E93")   # Gray when paused
        self.text_color = wx.WHITE
        
        # Use MinSize but let parent control via DPI
        self.SetMinSize(size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        # Use actual rendered size (respects DPI)
        w, h = self.GetSize()
        
        # Ensure minimum dimensions
        if w <= 0 or h <= 0:
            return
        
        # Clear background with parent's background color
        parent = self.GetParent()
        if parent:
            parent_bg = parent.GetBackgroundColour()
        else:
            parent_bg = wx.Colour(255, 255, 255)
        gc.SetBrush(wx.Brush(parent_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        
        # Draw rounded rectangle button
        bg_color = self.color_running if self.is_on else self.color_paused
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        corner_radius = h // 3
        gc.DrawRoundedRectangle(0, 0, w, h, corner_radius)
        
        # Draw icon: ▶ (play) or ❚❚ (pause)
        icon = "❚❚" if self.is_on else "▶"
        
        # Calculate text metrics
        dc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        text_w, text_h = dc.GetTextExtent(icon)
        
        # Center text
        text_x = (w - text_w) / 2
        text_y = (h - text_h) / 2
        
        # Draw icon
        gc.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD), self.text_color)
        gc.DrawText(icon, text_x, text_y)
    
    def _on_click(self, event):
        self.is_on = not self.is_on
        self.Refresh()
        if self.callback:
            self.callback(self.is_on)
    
    def SetValue(self, value):
        self.is_on = value
        self.Refresh()
    
    def GetValue(self):
        return self.is_on
    
    def Bind_Change(self, callback):
        self.callback = callback


class ToggleSwitch(wx.Panel):
    """Simple toggle switch for settings - iOS-style."""
    
    def __init__(self, parent, size=(50, 26), is_on=False):
        super().__init__(parent, size=size)
        
        self.is_on = is_on
        self.callback = None
        
        self.track_color_on = hex_to_colour("#4285F4")
        self.track_color_off = hex_to_colour("#CCCCCC")
        self.knob_color = wx.WHITE
        
        # Use MinSize but let parent control via DPI
        self.SetMinSize(size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        # Use actual rendered size (respects DPI)
        w, h = self.GetSize()
        
        # Ensure minimum dimensions
        if w <= 0 or h <= 0:
            return
        
        # Clear background with parent's background color
        parent = self.GetParent()
        if parent:
            parent_bg = parent.GetBackgroundColour()
        else:
            parent_bg = wx.Colour(255, 255, 255)
        gc.SetBrush(wx.Brush(parent_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        
        # Scale track to height
        track_h = max(h - 4, 4)
        track_y = (h - track_h) / 2
        knob_size = max(track_h - 4, 2)
        
        # Draw track
        track_color = self.track_color_on if self.is_on else self.track_color_off
        gc.SetBrush(wx.Brush(track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, track_y, w, track_h, track_h / 2)
        
        # Draw knob
        knob_x = w - knob_size - 4 if self.is_on else 4
        knob_y = track_y + 2
        gc.SetBrush(wx.Brush(self.knob_color))
        gc.DrawEllipse(knob_x, knob_y, knob_size, knob_size)
    
    def _on_click(self, event):
        self.is_on = not self.is_on
        self.Refresh()
        if self.callback:
            self.callback(self.is_on)
    
    def SetValue(self, value):
        self.is_on = value
        self.Refresh()
    
    def GetValue(self):
        return self.is_on
    
    def Bind_Change(self, callback):
        self.callback = callback


# ============================================================
# ICONS - Simple ASCII/Unicode icons (cross-platform compatible)
# ============================================================
class Icons:
    # Tab icons
    NOTES = "\u270F"        # 📝 Notes / Pencil
    TODO = "\u2611"             # ☑️ Checkbox (checked)
    BOM = "\u2630"              # ☰ Menu/List
    
    # Action icons
    IMPORT = "\u21E9"           # ⇩ Import (down arrow)
    SAVE = "\u2713"             # 💾 Save
    PDF = "\u21B5"              # ↵ Enter-style Export
    ADD = "+"                   # +
    DELETE = "\U0001F5D1"       # 🗑 Delete (trash)
    CLEAR = "\u2716"            # ✖ Clear/Remove
    SETTINGS = "\u2699"         # ⚙ Settings
    GENERATE = "\u25B6"         # ▶ Generate / Play
    
    # Theme icons
    DARK = "\U0001F319"         # 🌙 Crescent moon
    LIGHT = "\u2600"            # ☀ Sun
    
    # Import menu icons
    BOARD = "\u25A1"            # □ Square board
    LAYERS = "\u2261"           # ≡ Layers
    NETLIST = "\u2194"          # ↔ Bidirectional
    RULES = "\u2263"            # ≣ Rules / tolerance lines
    DRILL = "\u25CE"            # ◎ Drill/Bullseye
    ALL = "\u2606"              # ☆ Star
    GLOBE = "\U0001F310"        # 🌐 Web/Globe



# ============================================================
# MAIN PANEL
# ============================================================
class KiNotesMainPanel(wx.Panel):
    """Main panel with tabs, color picker, dark mode toggle, and bottom action buttons."""
    
    def __init__(self, parent, notes_manager, designator_linker, metadata_extractor, pdf_exporter):
        super().__init__(parent)
        
        self.notes_manager = notes_manager
        self.designator_linker = designator_linker
        self.metadata_extractor = metadata_extractor
        self.pdf_exporter = pdf_exporter
        
        self._auto_save_timer = None
        self._modified = False
        self._todo_items = []
        self._todo_id_counter = 0
        self._current_tab = 0
        
        # Time tracking system
        self.time_tracker = TimeTracker()
        self._timer_update_tick = 0
        
        # Theme settings
        self._dark_mode = False
        self._bg_color_name = "Ivory Paper"
        self._text_color_name = "Carbon Black"
        self._dark_bg_color_name = "Charcoal"
        self._dark_text_color_name = "Pure White"
        self._load_color_settings()
        
        self._theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        self.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        try:
            self._init_ui()
            self._load_all_data()
            self._start_auto_save_timer()
        except Exception as e:
            print("KiNotes UI init error: " + str(e))
    
    def _load_color_settings(self):
        """Load saved color settings."""
        try:
            settings = self.notes_manager.load_settings()
            if settings:
                self._bg_color_name = settings.get("bg_color", "Ivory Paper")
                self._text_color_name = settings.get("text_color", "Carbon Black")
                self._dark_bg_color_name = settings.get("dark_bg_color", "Charcoal")
                self._dark_text_color_name = settings.get("dark_text_color", "Pure White")
                self._dark_mode = settings.get("dark_mode", False)
        except:
            pass
    
    def _save_color_settings(self):
        """Save color settings."""
        try:
            settings = self.notes_manager.load_settings() or {}
            settings.update({
                "bg_color": self._bg_color_name,
                "text_color": self._text_color_name,
                "dark_bg_color": self._dark_bg_color_name,
                "dark_text_color": self._dark_text_color_name,
                "dark_mode": self._dark_mode
            })
            self.notes_manager.save_settings(settings)
        except:
            pass
    
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
        self.content_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create all tab panels
        self.notes_panel = self._create_notes_tab(self.content_panel)
        self.todo_panel = self._create_todo_tab(self.content_panel)
        self.bom_panel = self._create_bom_tab(self.content_panel)
        
        self.content_sizer.Add(self.notes_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.todo_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.bom_panel, 1, wx.EXPAND)
        
        self.content_panel.SetSizer(self.content_sizer)
        main_sizer.Add(self.content_panel, 1, wx.EXPAND)
        
        # === BOTTOM BAR: pcbtools.xyz + Save + Export PDF ===
        self.bottom_bar = self._create_bottom_bar()
        main_sizer.Add(self.bottom_bar, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self._show_tab(0)
    
    def _create_top_bar(self):
        """Create top bar with tabs + Import button on same line."""
        top_bar = wx.Panel(self)
        top_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        top_bar.SetMinSize((-1, 70))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(16)
        
        # Tab buttons - unified rounded style
        self.tab_buttons = []
        tabs = [
            ("Notes", 0),
            ("Todo", 1),
            ("BOM", 2)
        ]
        
        for label, idx in tabs:
            btn = RoundedButton(
                top_bar, 
                label=label,
                icon="",
                size=(110, 42),
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
            size=(130, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.import_btn.Bind_Click(self._on_import_click)
        sizer.Add(self.import_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddStretchSpacer()
        
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
        bottom_bar.SetMinSize((-1, 70))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(16)
        
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
        folder_text = wx.StaticText(bottom_bar, label="📁 Work Logs")
        folder_text.SetForegroundColour(hex_to_colour(self._theme["accent_blue"]))
        folder_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
        folder_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        folder_text.Bind(wx.EVT_LEFT_DOWN, self._on_open_work_logs_folder)
        folder_text.SetToolTip("Open work logs folder (.kinotes)")
        sizer.Add(folder_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddSpacer(20)
        
        # Global time tracker display
        self.global_time_label = wx.StaticText(bottom_bar, label="⏱ Total Time: 00:00:00")
        self.global_time_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        self.global_time_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.global_time_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Export work diary button
        self.export_diary_btn = RoundedButton(
            bottom_bar,
            label="Export Diary",
            icon="",
            size=(180, 48),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.export_diary_btn.Bind_Click(lambda e: self._on_export_work_diary())
        sizer.Add(self.export_diary_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
        
        sizer.AddStretchSpacer()
        
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
    
    def _on_website_click(self, event):
        """Open pcbtools.xyz in browser."""
        try:
            import webbrowser
            webbrowser.open("https://pcbtools.xyz")
        except:
            pass
    
    def _get_work_diary_path(self):
        """
        Get the work diary file path in .kinotes directory.
        Uses project name (or generic name) and date/time.
        Creates .kinotes directory if it doesn't exist.
        Handles duplicate files by appending -01, -02, etc.
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
        
        # Generate filename with date and time
        # Format: <project_title>_worklog_<YYYYMMDD_HHMMSS>.md
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{project_name}_worklog_{timestamp}.md"
        base_path = os.path.join(kinotes_dir, base_filename)
        
        # Handle duplicate files by appending -01, -02, etc.
        filepath = base_path
        counter = 0
        
        # If exact file already exists (rare but possible), add counter
        while os.path.exists(filepath) and counter < 100:
            counter += 1
            # Insert counter before .md extension
            name_without_ext = base_path[:-3]  # Remove .md
            filepath = f"{name_without_ext}-{counter:02d}.md"
        
        return filepath, kinotes_dir
    
    def _on_export_work_diary(self):
        """Export work diary to .kinotes directory with smart naming."""
        try:
            content = self.time_tracker.export_work_diary()
            filepath, kinotes_dir = self._get_work_diary_path()
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            wx.MessageBox(f"Work diary exported to:\n{filepath}", "Export Success", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Error exporting diary: {str(e)}", "Export Error", wx.OK | wx.ICON_ERROR)
    
    def _on_open_work_logs_folder(self, event):
        """Open the .kinotes work logs folder in file explorer."""
        try:
            _, kinotes_dir = self._get_work_diary_path()
            
            # Windows
            if sys.platform.startswith("win"):
                import subprocess
                subprocess.Popen(f'explorer "{kinotes_dir}"')
            # Mac
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", kinotes_dir])
            # Linux
            else:
                import subprocess
                subprocess.Popen(["xdg-open", kinotes_dir])
        except Exception as e:
            wx.MessageBox(f"Error opening folder: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
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
        
        # Show/hide buttons based on tab
        if idx == 0:  # Notes tab
            self.notes_panel.Show()
            self.import_btn.Show()
            self.save_btn.Show()
            self.pdf_btn.Show()
        elif idx == 1:  # Todo tab
            self.todo_panel.Show()
            self.import_btn.Hide()
            self.save_btn.Hide()
            self.pdf_btn.Hide()
            try:
                self.todo_scroll.FitInside()
            except:
                pass
        elif idx == 2:  # BOM tab
            self.bom_panel.Show()
            self.import_btn.Hide()
            self.save_btn.Show()  # Keep Save for BOM settings
            self.pdf_btn.Hide()
            try:
                self.bom_panel.FitInside()
            except:
                pass
            try:
                self.bom_panel.FitInside()
            except:
                pass
        
        self.top_bar.Layout()
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
    
    # ============================================================
    # SETTINGS DIALOG - With Dark Mode Toggle
    # ============================================================
    
    def _on_settings_click(self, event):
        """Show color settings dialog with dark mode toggle and time tracking options."""
        dlg = wx.Dialog(self, title="Settings", size=(450, 650),
                       style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dlg.SetMinSize((400, 550))
        dlg.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(24)
        
        # Dark Mode Toggle Section
        mode_panel = wx.Panel(dlg)
        mode_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        mode_label = wx.StaticText(mode_panel, label= " Theme")
        mode_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        mode_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        mode_sizer.AddStretchSpacer()
        
        self._dark_toggle = ToggleSwitch(mode_panel, size=(54, 28), is_on=self._dark_mode)
        self._dark_toggle.Bind_Change(lambda is_on: self._on_theme_toggle(dlg, sizer, is_on))
        mode_sizer.Add(self._dark_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        mode_panel.SetSizer(mode_sizer)
        sizer.Add(mode_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddSpacer(24)
        
        # Separator
        sep = wx.StaticLine(dlg)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddSpacer(20)
        
        # Time Tracking Settings Section
        time_header = wx.StaticText(dlg, label="⏱ Time Tracking Options")
        time_header.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        time_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        sizer.Add(time_header, 0, wx.LEFT | wx.BOTTOM, 24)
        
        # Enable time tracking checkbox
        time_track_panel = wx.Panel(dlg)
        time_track_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        time_track_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._enable_time_tracking = wx.CheckBox(time_track_panel, label="  Enable Time Tracking")
        self._enable_time_tracking.SetValue(self.time_tracker.enable_time_tracking)
        self._enable_time_tracking.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        time_track_sizer.Add(self._enable_time_tracking, 0, wx.ALL, 10)
        
        # Time format option
        format_panel = wx.Panel(time_track_panel)
        format_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        format_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        format_label = wx.StaticText(format_panel, label="Time Format:")
        format_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        format_sizer.Add(format_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self._time_format_choice = wx.Choice(format_panel, choices=["24-hour", "12-hour (AM/PM)"])
        self._time_format_choice.SetSelection(0 if self.time_tracker.time_format_24h else 1)
        format_sizer.Add(self._time_format_choice, 1, wx.EXPAND)
        
        format_panel.SetSizer(format_sizer)
        time_track_sizer.Add(format_panel, 0, wx.EXPAND | wx.ALL, 10)
        
        # Show work diary button checkbox
        self._show_work_diary = wx.CheckBox(time_track_panel, label="  Show Work Diary Button")
        self._show_work_diary.SetValue(self.time_tracker.show_work_diary_button)
        self._show_work_diary.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        time_track_sizer.Add(self._show_work_diary, 0, wx.ALL, 10)
        
        time_track_panel.SetSizer(time_track_sizer)
        sizer.Add(time_track_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)
        
        sizer.AddSpacer(20)
        # Separator
        sep = wx.StaticLine(dlg)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddSpacer(20)
        
        # Colors panel - will be replaced based on theme
        self._colors_panel = wx.Panel(dlg)
        self._colors_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self._rebuild_color_options(self._colors_panel, self._dark_mode)
        sizer.Add(self._colors_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 0)
        
        # Buttons - unified rounded style with clear Save action
        btn_panel = wx.Panel(dlg)
        btn_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        
        # Store result for dialog
        self._settings_result = None
        
        def on_cancel(e):
            self._settings_result = wx.ID_CANCEL
            dlg.EndModal(wx.ID_CANCEL)
        
        def on_apply(e):
            self._settings_result = wx.ID_OK
            dlg.EndModal(wx.ID_OK)
        
        cancel_btn = RoundedButton(
            btn_panel,
            label="Cancel",
            icon="",
            size=(110, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        cancel_btn.Bind_Click(on_cancel)
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 12)
        
        apply_btn = RoundedButton(
            btn_panel,
            label="Save & Apply",
            icon="",
            size=(220, 42),
            bg_color=self._theme["accent_blue"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        apply_btn.Bind_Click(on_apply)
        btn_sizer.Add(apply_btn, 0)
        
        btn_panel.SetSizer(btn_sizer)
        sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 24)
        
        dlg.SetSizer(sizer)
        
        if dlg.ShowModal() == wx.ID_OK:
            # Update theme
            self._dark_mode = self._dark_toggle.GetValue()
            if self._dark_mode:
                # Get dark theme color selections
                dark_bg_choices = list(DARK_BACKGROUND_COLORS.keys())
                dark_txt_choices = list(DARK_TEXT_COLORS.keys())
                self._dark_bg_color_name = dark_bg_choices[self._bg_choice.GetSelection()]
                self._dark_text_color_name = dark_txt_choices[self._txt_choice.GetSelection()]
            else:
                # Get light theme color selections
                bg_choices = list(BACKGROUND_COLORS.keys())
                txt_choices = list(TEXT_COLORS.keys())
                self._bg_color_name = bg_choices[self._bg_choice.GetSelection()]
                self._text_color_name = txt_choices[self._txt_choice.GetSelection()]
            
            # Update time tracking settings
            self.time_tracker.enable_time_tracking = self._enable_time_tracking.GetValue()
            self.time_tracker.time_format_24h = self._time_format_choice.GetSelection() == 0
            self.time_tracker.show_work_diary_button = self._show_work_diary.GetValue()
            
            # Show/hide export diary button based on setting
            if self.time_tracker.show_work_diary_button:
                self.export_diary_btn.Show()
            else:
                self.export_diary_btn.Hide()
            
            self._theme = DARK_THEME if self._dark_mode else LIGHT_THEME
            self._apply_theme()
            self._apply_editor_colors()
            self._save_color_settings()
            self.Layout()
        
        dlg.Destroy()
    
    def _on_theme_toggle(self, dlg, sizer, is_dark):
        """Handle theme toggle in settings dialog - rebuild color options."""
        self._rebuild_color_options(self._colors_panel, is_dark)
        dlg.Layout()
    
    def _rebuild_color_options(self, panel, is_dark):
        """Rebuild color options based on theme."""
        # Clear existing children
        for child in panel.GetChildren():
            child.Destroy()
        
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        if is_dark:
            # Dark Theme Colors
            header = wx.StaticText(panel, label="Dark Theme Colors")
            header.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
            panel_sizer.Add(header, 0, wx.LEFT, 24)
            panel_sizer.AddSpacer(12)
            
            # Background color
            bg_label = wx.StaticText(panel, label="Background:")
            bg_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            bg_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            panel_sizer.Add(bg_label, 0, wx.LEFT, 24)
            panel_sizer.AddSpacer(6)
            
            dark_bg_choices = list(DARK_BACKGROUND_COLORS.keys())
            self._bg_choice = wx.Choice(panel, choices=dark_bg_choices)
            dark_bg_name = getattr(self, '_dark_bg_color_name', 'Charcoal')
            self._bg_choice.SetSelection(dark_bg_choices.index(dark_bg_name) if dark_bg_name in dark_bg_choices else 0)
            panel_sizer.Add(self._bg_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
            
            panel_sizer.AddSpacer(16)
            
            # Text color
            txt_label = wx.StaticText(panel, label="Text:")
            txt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            txt_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            panel_sizer.Add(txt_label, 0, wx.LEFT, 24)
            panel_sizer.AddSpacer(6)
            
            dark_txt_choices = list(DARK_TEXT_COLORS.keys())
            self._txt_choice = wx.Choice(panel, choices=dark_txt_choices)
            dark_txt_name = getattr(self, '_dark_text_color_name', 'Pure White')
            self._txt_choice.SetSelection(dark_txt_choices.index(dark_txt_name) if dark_txt_name in dark_txt_choices else 0)
            panel_sizer.Add(self._txt_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        else:
            # Light Theme Colors
            header = wx.StaticText(panel, label="Light Theme Colors")
            header.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
            panel_sizer.Add(header, 0, wx.LEFT, 24)
            panel_sizer.AddSpacer(12)
            
            # Background color
            bg_label = wx.StaticText(panel, label="Background:")
            bg_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            bg_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            panel_sizer.Add(bg_label, 0, wx.LEFT, 24)
            panel_sizer.AddSpacer(6)
            
            bg_choices = list(BACKGROUND_COLORS.keys())
            self._bg_choice = wx.Choice(panel, choices=bg_choices)
            self._bg_choice.SetSelection(bg_choices.index(self._bg_color_name) if self._bg_color_name in bg_choices else 0)
            panel_sizer.Add(self._bg_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
            
            panel_sizer.AddSpacer(16)
            
            # Text color
            txt_label = wx.StaticText(panel, label="Text:")
            txt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            txt_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
            panel_sizer.Add(txt_label, 0, wx.LEFT, 24)
            panel_sizer.AddSpacer(6)
            
            txt_choices = list(TEXT_COLORS.keys())
            self._txt_choice = wx.Choice(panel, choices=txt_choices)
            self._txt_choice.SetSelection(txt_choices.index(self._text_color_name) if self._text_color_name in txt_choices else 0)
            panel_sizer.Add(self._txt_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        panel.SetSizer(panel_sizer)
        panel.Layout()
    
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
        self.content_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        # Apply theme to all tab panels
        self._apply_theme_to_panel(self.notes_panel)
        self._apply_theme_to_panel(self.todo_panel)
        self._apply_theme_to_panel(self.bom_panel)
        
        # Update tab buttons
        for btn in self.tab_buttons:
            if btn.tab_index == self._current_tab:
                btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
            else:
                btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        
        # Update other buttons
        self.import_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
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
        """Apply selected colors to editor."""
        bg = self._get_editor_bg()
        fg = self._get_editor_text()
        
        self.text_editor.SetBackgroundColour(bg)
        self.text_editor.SetForegroundColour(fg)
        
        # Apply to all text
        font = self.text_editor.GetFont()
        text_attr = wx.TextAttr(fg, bg, font)
        self.text_editor.SetDefaultStyle(text_attr)
        self.text_editor.SetStyle(0, self.text_editor.GetLastPosition(), text_attr)
        self.text_editor.Refresh()
    
    # ============================================================
    # TAB 1: NOTES
    # ============================================================
    
    def _create_notes_tab(self, parent):
        """Create Notes tab with editor."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Text editor
        self.text_editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.BORDER_NONE
        )
        self.text_editor.SetBackgroundColour(self._get_editor_bg())
        self.text_editor.SetForegroundColour(self._get_editor_text())
        self.text_editor.SetFont(wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Set default text style
        font = self.text_editor.GetFont()
        text_attr = wx.TextAttr(self._get_editor_text(), self._get_editor_bg(), font)
        self.text_editor.SetDefaultStyle(text_attr)
        
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        return panel
    
    # ============================================================
    # TAB 2: TODO LIST
    # ============================================================
    
    def _create_todo_tab(self, parent):
        """Create Todo tab with checkboxes."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        toolbar.SetMinSize((-1, 60))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(16)
        
        # Add task button - unified rounded style
        self.add_todo_btn = RoundedButton(
            toolbar,
            label="Add Task",
            icon="",
            size=(130, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.add_todo_btn.Bind_Click(self._on_add_todo)
        tb_sizer.Add(self.add_todo_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Clear task button - unified rounded style
        self.clear_done_btn = RoundedButton(
            toolbar,
            label="Clear Task",
            icon="",
            size=(140, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.clear_done_btn.Bind_Click(self._on_clear_done)
        tb_sizer.Add(self.clear_done_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        
        # Counter
        self.todo_count = wx.StaticText(toolbar, label="0 / 0")
        self.todo_count.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        self.todo_count.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(self.todo_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Todo list scroll area
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_sizer.AddSpacer(12)
        self.todo_scroll.SetSizer(self.todo_sizer)
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_todo_item(self, text="", done=False, time_spent=0, history=None):
        """Add a todo item with time tracking."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        # Initialize timer for this task
        self.time_tracker.create_task_timer(item_id)
        if time_spent > 0:
            self.time_tracker.task_timers[item_id]["time_spent"] = time_spent
        if history:
            self.time_tracker.task_timers[item_id]["history"] = history
        if text:
            self.time_tracker.task_timers[item_id]["text"] = text
        if done:
            self.time_tracker.task_timers[item_id]["done"] = done
        
        item_panel = wx.Panel(self.todo_scroll)
        # Use theme-appropriate background for todo items
        if self._dark_mode:
            item_panel.SetBackgroundColour(hex_to_colour("#2D2D2D"))
        else:
            item_panel.SetBackgroundColour(wx.WHITE)
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 14)
        
        # Spacing between checkbox and timer button
        item_sizer.AddSpacer(12)
        
        # Timer play/pause button
        timer_btn = PlayPauseButton(item_panel, size=(42, 28), is_on=False)
        timer_btn.Bind_Change(lambda is_on, iid=item_id: self._on_timer_toggle(iid, is_on))
        item_sizer.Add(timer_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Text input with strikethrough support
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        # Match item panel background
        if self._dark_mode:
            txt.SetBackgroundColour(hex_to_colour("#2D2D2D"))
        else:
            txt.SetBackgroundColour(wx.WHITE)
        
        # Apply strikethrough font if done
        if done:
            font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            font.SetStrikethrough(True)
            txt.SetFont(font)
            txt.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        else:
            txt.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            txt.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        
        txt.Bind(wx.EVT_TEXT, lambda e, iid=item_id: self._on_todo_text_change(iid))
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 12)
        
        # Timer label - fixed width display
        timer_label = wx.StaticText(item_panel, label="⏱ 00:00:00")
        timer_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        timer_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        timer_label.SetMinSize((110, -1))
        item_sizer.Add(timer_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # RTC inline session label - shows last completed session if exists
        # Format: "(10:12 → 10:40 28min)"
        rtc_label = wx.StaticText(item_panel, label="")
        rtc_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        rtc_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        rtc_label.SetMinSize((120, -1))  # Fixed width for stable layout
        
        # Add tooltip for full session history
        if history and len(history) > 0:
            tooltip_text = self.time_tracker.get_session_history_tooltip(item_id, self.time_tracker.time_format_24h)
            if tooltip_text:
                rtc_label.SetToolTip(tooltip_text)
        
        item_sizer.Add(rtc_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Delete button with icon
        del_btn = wx.Button(item_panel, label=Icons.DELETE, size=(40, 40), style=wx.BORDER_NONE)
        # Match item panel background
        if self._dark_mode:
            del_btn.SetBackgroundColour(hex_to_colour("#2D2D2D"))
        else:
            del_btn.SetBackgroundColour(wx.WHITE)
        del_btn.SetForegroundColour(hex_to_colour(self._theme["accent_red"]))
        del_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 14)
        
        item_panel.SetSizer(item_sizer)
        
        self._todo_items.append({
            "id": item_id,
            "panel": item_panel,
            "checkbox": cb,
            "timer_switch": timer_btn,
            "text": txt,
            "timer_label": timer_label,
            "rtc_label": rtc_label,
            "del_btn": del_btn,
            "done": done
        })
        
        self.todo_sizer.Add(item_panel, 0, wx.EXPAND | wx.BOTTOM, 8)

        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_todo_count()
        return txt
    
    def _on_add_todo(self, event):
        txt = self._add_todo_item()
        txt.SetFocus()
        self._save_todos()
    
    def _on_timer_toggle(self, item_id, is_on):
        """
        Handle timer start/stop for a task.
        If turning ON: auto-stop any other running task + update its toggle switch.
        If turning OFF: normal pause + log session.
        """
        if is_on:
            # Starting new task timer
            prev_running = self.time_tracker.current_running_task_id
            
            # This will auto-stop any other running task
            self.time_tracker.start_task(item_id)
            
            # If we just auto-stopped another task, update its toggle switch UI
            if prev_running is not None and prev_running != item_id:
                for item in self._todo_items:
                    if item["id"] == prev_running:
                        item["timer_switch"].SetValue(False)
                        break
        else:
            # Stopping current task timer
            self.time_tracker.stop_task(item_id)
        
        # Force immediate UI refresh of timer displays
        self._update_timer_displays()
        self._save_todos()
    
    def _on_todo_text_change(self, item_id):
        """Update timer text data when task text changes."""
        for item in self._todo_items:
            if item["id"] == item_id:
                self.time_tracker.task_timers[item_id]["text"] = item["text"].GetValue()
                break
        self._save_todos()
    
    def _on_todo_toggle(self, item_id):
        for item in self._todo_items:
            if item["id"] == item_id:
                item["done"] = item["checkbox"].GetValue()
                
                # Stop timer if marking as done
                if item["done"]:
                    self.time_tracker.mark_task_done(item_id)
                    item["timer_switch"].SetValue(False)
                
                # Apply strikethrough when done
                font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                if item["done"]:
                    font.SetStrikethrough(True)
                    item["text"].SetFont(font)
                    item["text"].SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
                else:
                    font.SetStrikethrough(False)
                    item["text"].SetFont(font)
                    item["text"].SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                
                item["text"].Refresh()
                break
        self._update_todo_count()
        self._save_todos()
    
    def _on_delete_todo(self, item_id):
        for i, item in enumerate(self._todo_items):
            if item["id"] == item_id:
                item["panel"].Destroy()
                self._todo_items.pop(i)
                self.time_tracker.delete_task(item_id)
                break
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _on_clear_done(self, event):
        to_remove = [item for item in self._todo_items if item["done"]]
        for item in to_remove:
            item["panel"].Destroy()
            self.time_tracker.delete_task(item["id"])
            self._todo_items.remove(item)
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _update_todo_count(self):
        total = len(self._todo_items)
        done = sum(1 for item in self._todo_items if item["done"])
        self.todo_count.SetLabel(str(done) + " / " + str(total))
    
    def _update_timer_displays(self):
        """Update all timer labels and RTC inline displays with current state."""
        for item in self._todo_items:
            item_id = item["id"]
            
            # Update live timer display
            time_str = self.time_tracker.get_task_time_string(item_id)
            item["timer_label"].SetLabel(time_str)
            
            # Update RTC inline session display (only when task is not running)
            rtc_str = self.time_tracker.get_last_session_string(item_id, self.time_tracker.time_format_24h)
            item["rtc_label"].SetLabel(rtc_str)
            
            # Update tooltip if history exists
            task_data = self.time_tracker.task_timers.get(item_id, {})
            history = task_data.get("history", [])
            if history and len(history) > 0:
                tooltip_text = self.time_tracker.get_session_history_tooltip(item_id, self.time_tracker.time_format_24h)
                if tooltip_text:
                    item["rtc_label"].SetToolTip(tooltip_text)

    
    # ============================================================
    # TAB 3: BOM TOOL
    # ============================================================
    
    def _create_bom_tab(self, parent):
        """Create BOM Tool tab."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        
        # Section helper
        def add_section(title, checkboxes):
            header = wx.StaticText(panel, label=title)
            header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
            header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            sizer.Add(header, 0, wx.LEFT | wx.BOTTOM, 16)
            
            opt_panel = wx.Panel(panel)
            # Use darker shade for section panels in both modes
            if self._dark_mode:
                opt_panel.SetBackgroundColour(hex_to_colour("#2D2D2D"))
            else:
                opt_panel.SetBackgroundColour(hex_to_colour("#F5F5F5"))
            opt_sizer = wx.BoxSizer(wx.VERTICAL)
            
            widgets = []
            for label, default in checkboxes:
                cb = wx.CheckBox(opt_panel, label="  " + label)
                cb.SetValue(default)
                cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                cb.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                opt_sizer.Add(cb, 0, wx.ALL, 12)
                widgets.append(cb)
            
            opt_panel.SetSizer(opt_sizer)
            sizer.Add(opt_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
            return widgets
        
        # Columns section
        cols = add_section("COLUMNS", [
            ("Show quantity", True),
            ("Show value", True),
            ("Show footprint", True),
            ("Show references", True),
        ])
        self.bom_show_qty, self.bom_show_value, self.bom_show_fp, self.bom_show_refs = cols
        
        # Filters section
        filters = add_section("FILTERS", [
            ("Exclude DNP", True),
            ("Exclude virtual", True),
            ("Exclude fiducials (FID*)", True),
            ("Exclude test points (TP*)", True),
            ("Exclude mounting holes (MH*)", True),
        ])
        self.bom_exclude_dnp, self.bom_exclude_virtual, self.bom_exclude_fid, self.bom_exclude_tp, self.bom_exclude_mh = filters
        
        # Grouping
        grp_header = wx.StaticText(panel, label="GROUPING")
        grp_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        grp_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(grp_header, 0, wx.LEFT | wx.BOTTOM, 16)
        
        self.bom_group_by = wx.Choice(panel, choices=[
            "Value + Footprint",
            "Value only",
            "Footprint only",
            "No grouping"
        ])
        self.bom_group_by.SetSelection(0)
        self.bom_group_by.SetBackgroundColour(hex_to_colour(self._theme["bg_button"]))
        self.bom_group_by.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        sizer.Add(self.bom_group_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        
        # Sort
        sort_header = wx.StaticText(panel, label="SORT BY")
        sort_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        sort_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(sort_header, 0, wx.LEFT | wx.BOTTOM, 16)
        
        self.bom_sort_by = wx.Choice(panel, choices=[
            "Reference (natural)",
            "Value",
            "Footprint",
            "Quantity"
        ])
        self.bom_sort_by.SetSelection(0)
        self.bom_sort_by.SetBackgroundColour(hex_to_colour(self._theme["bg_button"]))
        self.bom_sort_by.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        sizer.Add(self.bom_sort_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        
        # Blacklist
        bl_header = wx.StaticText(panel, label="CUSTOM BLACKLIST (one per line)")
        bl_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        bl_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(bl_header, 0, wx.LEFT | wx.BOTTOM, 16)
        
        self.bom_blacklist = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 80))
        self.bom_blacklist.SetBackgroundColour(self._get_editor_bg())
        self.bom_blacklist.SetForegroundColour(self._get_editor_text())
        self.bom_blacklist.SetHint("e.g. LOGO*, H*")
        sizer.Add(self.bom_blacklist, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        
        # Export BOM button - unified rounded style
        self.gen_bom_btn = RoundedButton(
            panel,
            label="Export BOM -> Notes",
            icon="",
            size=(-1, 52),
            bg_color=self._theme["accent_blue"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=12,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.gen_bom_btn.Bind_Click(self._on_generate_bom)
        sizer.Add(self.gen_bom_btn, 0, wx.EXPAND | wx.ALL, 20)
        
        panel.SetSizer(sizer)
        return panel
    
    def _on_generate_bom(self, event):
        """Generate BOM and insert into Notes."""
        try:
            bom_text = self._generate_bom_text()
            if bom_text:
                current = self.text_editor.GetValue()
                if current and not current.endswith("\n"):
                    current += "\n"
                current += "\n" + bom_text
                self.text_editor.SetValue(current)
                self.text_editor.SetInsertionPointEnd()
                self._apply_editor_colors()
                self._show_tab(0)
        except Exception as e:
            pass
    
    def _generate_bom_text(self):
        """Generate BOM text."""
        try:
            import pcbnew
            import fnmatch
        except ImportError:
            return "## BOM\n\n*pcbnew not available*\n"
        
        try:
            board = pcbnew.GetBoard()
            if not board:
                return "## BOM\n\n*No board loaded*\n"
        except:
            return "## BOM\n\n*Could not access board*\n"
        
        blacklist = []
        if self.bom_exclude_fid.GetValue():
            blacklist.append("FID*")
        if self.bom_exclude_tp.GetValue():
            blacklist.append("TP*")
        if self.bom_exclude_mh.GetValue():
            blacklist.append("MH*")
        
        custom_bl = self.bom_blacklist.GetValue().strip()
        if custom_bl:
            blacklist.extend([p.strip() for p in custom_bl.split("\n") if p.strip()])
        
        components = []
        try:
            for fp in board.GetFootprints():
                ref = fp.GetReference()
                value = fp.GetValue()
                footprint = fp.GetFPIDAsString().split(":")[-1] if fp.GetFPIDAsString() else ""
                
                if self.bom_exclude_dnp.GetValue():
                    try:
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, "FP_EXCLUDE_FROM_BOM") and (attrs & pcbnew.FP_EXCLUDE_FROM_BOM):
                            continue
                    except:
                        pass
                
                if self.bom_exclude_virtual.GetValue():
                    try:
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, "FP_BOARD_ONLY") and (attrs & pcbnew.FP_BOARD_ONLY):
                            continue
                    except:
                        pass
                
                skip = False
                for pattern in blacklist:
                    if fnmatch.fnmatch(ref.upper(), pattern.upper()):
                        skip = True
                        break
                if skip:
                    continue
                
                components.append({"ref": ref, "value": value, "footprint": footprint})
        except:
            return "## BOM\n\n*Error reading components*\n"
        
        if not components:
            return "## BOM\n\n*No components found*\n"
        
        # Group
        group_mode = self.bom_group_by.GetSelection()
        grouped = {}
        
        for comp in components:
            if group_mode == 0:
                key = (comp["value"], comp["footprint"])
            elif group_mode == 1:
                key = (comp["value"], "")
            elif group_mode == 2:
                key = ("", comp["footprint"])
            else:
                key = (comp["ref"], comp["value"], comp["footprint"])
            
            if key not in grouped:
                grouped[key] = {"refs": [], "value": comp["value"], "footprint": comp["footprint"]}
            grouped[key]["refs"].append(comp["ref"])
        
        # Sort refs naturally
        import re
        def natural_key(s):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", s)]
        
        for data in grouped.values():
            data["refs"].sort(key=natural_key)
        
        # Sort groups
        sort_mode = self.bom_sort_by.GetSelection()
        items = list(grouped.values())
        
        if sort_mode == 0:
            items.sort(key=lambda x: natural_key(x["refs"][0]))
        elif sort_mode == 1:
            items.sort(key=lambda x: x["value"].lower())
        elif sort_mode == 2:
            items.sort(key=lambda x: x["footprint"].lower())
        elif sort_mode == 3:
            items.sort(key=lambda x: -len(x["refs"]))
        
        # Build output
        lines = ["## BOM - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
        
        # Header
        header_parts = []
        if self.bom_show_qty.GetValue():
            header_parts.append("Qty")
        if self.bom_show_value.GetValue():
            header_parts.append("Value")
        if self.bom_show_fp.GetValue():
            header_parts.append("Footprint")
        if self.bom_show_refs.GetValue():
            header_parts.append("References")
        
        lines.append("| " + " | ".join(header_parts) + " |")
        lines.append("|" + "|".join(["---"] * len(header_parts)) + "|")
        
        for item in items:
            row = []
            if self.bom_show_qty.GetValue():
                row.append(str(len(item["refs"])))
            if self.bom_show_value.GetValue():
                row.append(item["value"])
            if self.bom_show_fp.GetValue():
                row.append(item["footprint"])
            if self.bom_show_refs.GetValue():
                refs_str = ", ".join(["@" + r for r in item["refs"][:5]])
                if len(item["refs"]) > 5:
                    refs_str += " +" + str(len(item["refs"])-5) + " more"
                row.append(refs_str)
            lines.append("| " + " | ".join(row) + " |")
        
        lines.append("")
        lines.append("**Total unique groups:** " + str(len(items)))
        lines.append("**Total components:** " + str(sum(len(i["refs"]) for i in items)))
        
        return "\n".join(lines)
    
    # ============================================================
    # IMPORT HANDLER
    # ============================================================
    
    def _on_import_click(self, event):
        """Handle import button click."""
        menu = wx.Menu()
        
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
        """Insert text at cursor or end."""
        try:
            current = self.text_editor.GetValue()
            if current and not current.endswith("\n"):
                current += "\n"
            current += "\n" + text
            self.text_editor.SetValue(current)
            self.text_editor.SetInsertionPointEnd()
            self._apply_editor_colors()
            self._show_tab(0)
        except:
            pass
    
    def _on_export_pdf(self):
        """Export notes to PDF."""
        try:
            content = self.text_editor.GetValue()
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
        except:
            pass
    
    def _on_text_changed(self, event):
        self._modified = True
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle @REF clicks."""
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
        """Start auto-save timer - runs every 1 second for time tracking updates."""
        try:
            self._auto_save_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
            self._auto_save_timer.Start(1000)  # 1 second for timer updates
        except:
            pass
    
    def _on_auto_save(self, event):
        """Auto-save if modified and update timer displays."""
        # Update timer displays every tick
        self._timer_update_tick += 1
        self._update_timer_displays()
        
        # Update global timer display
        try:
            self.global_time_label.SetLabel(self.time_tracker.get_total_time_string())
        except:
            pass
        
        # Full save only every 5 ticks (5 seconds)
        if self._timer_update_tick >= 5 or self._modified:
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
                self.text_editor.SetValue(content)
                self._apply_editor_colors()
        except:
            pass
        
        try:
            todos = self.notes_manager.load_todos()
            for todo in todos:
                time_spent = todo.get("time_spent", 0)
                history = todo.get("history", [])
                self._add_todo_item(
                    todo.get("text", ""), 
                    todo.get("done", False),
                    time_spent,
                    history
                )
        except:
            pass
        
        self._modified = False
    
    def _save_notes(self):
        """Save notes."""
        try:
            self.notes_manager.save(self.text_editor.GetValue())
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
        except:
            pass
    
    def force_save(self):
        """Force save all data."""
        self._save_notes()
        self._save_todos()
    
    def cleanup(self):
        """Cleanup timer resources and stop running timers."""
        # Stop any running task timers
        if self.time_tracker.current_running_task_id is not None:
            self.time_tracker.stop_task(self.time_tracker.current_running_task_id)
        
        # Save any pending data
        self.force_save()
        
        try:
            if self._auto_save_timer:
                self._auto_save_timer.Stop()
        except:
            pass
