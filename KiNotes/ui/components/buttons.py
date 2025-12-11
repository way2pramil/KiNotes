"""
KiNotes Custom Buttons - Themed UI button widgets.

Provides:
- RoundedButton: Primary styled button with rounded corners
- PlayPauseButton: Timer start/stop toggle button
- ToggleSwitch: iOS-style toggle switch

All buttons support DPI scaling and theme colors.

Usage:
    from .buttons import RoundedButton, PlayPauseButton, ToggleSwitch
    btn = RoundedButton(parent, "Save", size=(100, 40), bg_color="#4CAF50")
    btn.Bind_Click(on_click_handler)
"""
import wx
from ..themes import hex_to_colour
from ..scaling import scale_size, scale_font_size


class RoundedButton(wx.Panel):
    """
    Custom rounded button with hover effects.
    Industry-standard button with modern styling.
    
    corner_flags: Controls which corners are rounded (for split buttons)
        0x01 = top-left, 0x02 = top-right, 0x04 = bottom-left, 0x08 = bottom-right
        Default: all corners rounded (0x0F)
    """
    
    # Corner flags for split buttons
    CORNER_TL = 0x01
    CORNER_TR = 0x02
    CORNER_BL = 0x04
    CORNER_BR = 0x08
    CORNER_ALL = 0x0F
    
    def __init__(self, parent, label="", icon="", size=(100, 36),
                 bg_color="#4285F4", fg_color="#FFFFFF", corner_radius=8,
                 font_size=10, font_weight=wx.FONTWEIGHT_NORMAL, corner_flags=0x0F):
        
        scaled_size = scale_size(size, parent)
        super().__init__(parent, size=scaled_size)
        
        self.label = label
        self.icon = icon
        self.bg_color = hex_to_colour(bg_color) if isinstance(bg_color, str) else bg_color
        self.fg_color = hex_to_colour(fg_color) if isinstance(fg_color, str) else fg_color
        self.corner_radius = scale_size(corner_radius, parent)
        self.corner_flags = corner_flags
        self.is_hovered = False
        self.is_pressed = False
        self.callback = None
        self.button_size = scaled_size
        self.base_font_size = scale_font_size(font_size, parent)
        self.font_weight = font_weight
        
        self.SetMinSize(scaled_size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.font = wx.Font(self.base_font_size, wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL, font_weight)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_press)
        self.Bind(wx.EVT_LEFT_UP, self._on_release)
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
        
        w, h = self.GetSize()
        if w <= 0 or h <= 0:
            return
        
        # Clear with parent background
        parent = self.GetParent()
        parent_bg = parent.GetBackgroundColour() if parent else wx.WHITE
        gc.SetBrush(wx.Brush(parent_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        
        # Button color based on state
        if self.is_pressed:
            bg = self._darken_color(self.bg_color, 40)
        elif self.is_hovered:
            bg = self._darken_color(self.bg_color, 15)
        else:
            bg = self.bg_color
        
        # Draw button with selective corner rounding
        corner = min(self.corner_radius, h // 3)
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        
        if self.corner_flags == self.CORNER_ALL:
            # All corners rounded - use standard method
            gc.DrawRoundedRectangle(0, 0, w, h, corner)
        else:
            # Selective corners - build custom path
            path = gc.CreatePath()
            tl = corner if (self.corner_flags & self.CORNER_TL) else 0
            tr = corner if (self.corner_flags & self.CORNER_TR) else 0
            bl = corner if (self.corner_flags & self.CORNER_BL) else 0
            br = corner if (self.corner_flags & self.CORNER_BR) else 0
            
            # Start from top-left, go clockwise
            path.MoveToPoint(tl, 0)
            path.AddLineToPoint(w - tr, 0)
            if tr > 0:
                path.AddArc(w - tr, tr, tr, -3.14159/2, 0, True)
            path.AddLineToPoint(w, h - br)
            if br > 0:
                path.AddArc(w - br, h - br, br, 0, 3.14159/2, True)
            path.AddLineToPoint(bl, h)
            if bl > 0:
                path.AddArc(bl, h - bl, bl, 3.14159/2, 3.14159, True)
            path.AddLineToPoint(0, tl)
            if tl > 0:
                path.AddArc(tl, tl, tl, 3.14159, 3.14159 * 1.5, True)
            path.CloseSubpath()
            gc.DrawPath(path)
        
        # Draw text with icon
        gc.SetFont(self.font, self.fg_color)
        display_text = f"{self.icon}  {self.label}" if self.icon else self.label
        text_w, text_h = gc.GetTextExtent(display_text)[:2]
        
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


class PlayPauseButton(wx.Panel):
    """
    Industry-standard Play/Stop timer button.
    Green (Play) / Red (Stop) toggle with clear visual states.
    """
    
    def __init__(self, parent, size=(50, 32), is_on=False):
        scaled_size = scale_size(size, parent)
        super().__init__(parent, size=scaled_size)
        
        self._is_on = is_on
        self._callback = None
        self._hover = False
        
        # Colors - green/red for start/stop
        self._color_play = "#4CAF50"
        self._color_play_hover = "#66BB6A"
        self._color_stop = "#F44336"
        self._color_stop_hover = "#EF5350"
        
        self.SetMinSize(scaled_size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        
        w, h = self.GetSize()
        if w <= 0 or h <= 0:
            return
        
        # Clear with parent background
        parent = self.GetParent()
        parent_bg = parent.GetBackgroundColour() if parent else wx.WHITE
        gc.SetBrush(wx.Brush(parent_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        
        # Color and icon based on state
        if self._is_on:
            bg_color = hex_to_colour(self._color_stop_hover if self._hover else self._color_stop)
            icon = "■"  # Stop
        else:
            bg_color = hex_to_colour(self._color_play_hover if self._hover else self._color_play)
            icon = "▶"  # Play
        
        # Draw rounded button
        corner_radius = min(h // 3, 8)
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(2, 2, w - 4, h - 4, corner_radius)
        
        # Draw icon centered
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        gc.SetFont(font, wx.WHITE)
        dc.SetFont(font)
        text_w, text_h = dc.GetTextExtent(icon)
        gc.DrawText(icon, (w - text_w) / 2, (h - text_h) / 2)
    
    def _on_click(self, event):
        self._is_on = not self._is_on
        self.Refresh()
        if self._callback:
            self._callback(self._is_on)
    
    def _on_enter(self, event):
        self._hover = True
        self.Refresh()
    
    def _on_leave(self, event):
        self._hover = False
        self.Refresh()
    
    def SetValue(self, value):
        """Set the on/off state."""
        self._is_on = bool(value)
        self.Refresh()
    
    def GetValue(self):
        """Get the on/off state."""
        return self._is_on
    
    def Bind_Change(self, callback):
        """Bind a callback for state changes."""
        self._callback = callback
    
    @property
    def is_on(self):
        return self._is_on
    
    @is_on.setter
    def is_on(self, value):
        self._is_on = bool(value)
        self.Refresh()


class ToggleSwitch(wx.Panel):
    """iOS-style toggle switch for settings."""
    
    def __init__(self, parent, size=(50, 26), is_on=False):
        scaled_size = scale_size(size, parent)
        super().__init__(parent, size=scaled_size)
        
        self.is_on = is_on
        self.callback = None
        
        self.track_color_on = hex_to_colour("#4285F4")
        self.track_color_off = hex_to_colour("#CCCCCC")
        self.knob_color = wx.WHITE
        
        self.SetMinSize(scaled_size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        w, h = self.GetSize()
        if w <= 0 or h <= 0:
            return
        
        # Clear with parent background
        parent = self.GetParent()
        parent_bg = parent.GetBackgroundColour() if parent else wx.WHITE
        gc.SetBrush(wx.Brush(parent_bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)
        
        # Track dimensions
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
