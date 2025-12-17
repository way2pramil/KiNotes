"""
KiNotes Todo Tab Mixin - Task list with time tracking.

Provides todo list functionality including:
- Add/delete tasks
- Task completion checkboxes
- Timer for each task with play/pause
- Session memos for active tasks
- Task counter
- Time tracking integration
"""
import wx
import wx.lib.scrolledpanel as scrolled

from ..themes import hex_to_colour
from ..components import RoundedButton, Icons


class TodoTabMixin:
    """Mixin for Todo tab functionality."""
    
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
        
        # Add task button
        self.add_todo_btn = RoundedButton(
            toolbar, label="Add Task", size=(130, 42),
            bg_color=self._theme["bg_button"], fg_color=self._theme["text_primary"],
            corner_radius=10, font_size=11, font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.add_todo_btn.Bind_Click(self._on_add_todo)
        tb_sizer.Add(self.add_todo_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
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
        """Add a todo item with time tracking and expandable session memo."""
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
        
        # Main container panel - use theme colors
        container_panel = wx.Panel(self.todo_scroll)
        container_bg = self._theme["bg_toolbar"]
        memo_bg = self._theme["bg_button"]
        
        # Get user's custom editor colors (same as Notes panel)
        editor_bg = self._get_editor_bg()
        editor_text = self._get_editor_text()
        
        container_panel.SetBackgroundColour(hex_to_colour(container_bg))
        container_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === ROW 1: Main task row ===
        item_panel = wx.Panel(container_panel)
        item_panel.SetBackgroundColour(hex_to_colour(container_bg))
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 14)
        item_sizer.AddSpacer(12)
        
        # Timer start/stop button - use theme accent colors
        timer_btn = RoundedButton(
            item_panel, label="Start", size=(60, 32),
            bg_color=self._theme["accent_green"],
            fg_color="#FFFFFF",
            corner_radius=6, font_size=10, font_weight=wx.FONTWEIGHT_BOLD
        )
        timer_btn.Bind_Click(lambda e, iid=item_id: self._on_timer_toggle(iid, None))
        item_sizer.Add(timer_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Text input - use user's custom editor colors (matches Notes panel)
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_SIMPLE | wx.TE_PROCESS_ENTER)
        txt.SetBackgroundColour(editor_bg)
        txt.SetForegroundColour(editor_text)  # Set default text color first
        
        if done:
            font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            font.SetStrikethrough(True)
            txt.SetFont(font)
            txt.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        else:
            txt.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        txt.Refresh()  # Force refresh to apply colors on Windows
        
        txt.Bind(wx.EVT_TEXT, lambda e, iid=item_id: self._on_todo_text_change(iid))
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 12)
        item_sizer.AddSpacer(12)
        
        # Timer label
        timer_label = wx.StaticText(item_panel, label="⏱ 00:00:00")
        timer_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        timer_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        timer_label.SetMinSize((100, -1))
        item_sizer.Add(timer_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # RTC session label
        rtc_label = wx.StaticText(item_panel, label="")
        rtc_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        rtc_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        rtc_label.SetMinSize((140, -1))
        
        if history and len(history) > 0:
            tooltip_text = self.time_tracker.get_session_history_tooltip(item_id, self.time_tracker.time_format_24h)
            if tooltip_text:
                rtc_label.SetToolTip(tooltip_text)
        
        item_sizer.Add(rtc_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Delete button - use theme colors
        del_btn = wx.Button(item_panel, label=Icons.DELETE, size=(40, 40), style=wx.BORDER_NONE)
        del_btn.SetBackgroundColour(hex_to_colour(container_bg))
        del_btn.SetForegroundColour(hex_to_colour(self._theme["accent_red"]))
        del_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        item_panel.SetSizer(item_sizer)
        container_sizer.Add(item_panel, 0, wx.EXPAND)
        
        # === ROW 2: Session memo row - use theme colors ===
        memo_panel = wx.Panel(container_panel)
        memo_panel.SetBackgroundColour(hex_to_colour(memo_bg))
        memo_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        memo_icon = wx.StaticText(memo_panel, label="📝")
        memo_icon.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        memo_sizer.Add(memo_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 76)
        
        memo_txt = wx.TextCtrl(memo_panel, value="", style=wx.BORDER_SIMPLE)
        memo_txt.SetHint("Session memo - what are you working on?")
        # Use user's custom editor colors (matches Notes panel and task text)
        memo_txt.SetBackgroundColour(editor_bg)
        memo_txt.SetForegroundColour(editor_text)
        memo_txt.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        memo_txt.Refresh()  # Force refresh to apply colors on Windows
        memo_txt.Bind(wx.EVT_TEXT, lambda e, iid=item_id: self._on_memo_change(iid))
        memo_sizer.Add(memo_txt, 1, wx.EXPAND | wx.ALL, 8)
        
        memo_panel.SetSizer(memo_sizer)
        memo_panel.Hide()
        container_sizer.Add(memo_panel, 0, wx.EXPAND)
        
        container_panel.SetSizer(container_sizer)
        
        self._todo_items.append({
            "id": item_id,
            "container": container_panel,
            "panel": item_panel,
            "memo_panel": memo_panel,
            "memo_text": memo_txt,
            "checkbox": cb,
            "timer_switch": timer_btn,
            "text": txt,
            "timer_label": timer_label,
            "rtc_label": rtc_label,
            "del_btn": del_btn,
            "done": done
        })
        
        self.todo_sizer.Add(container_panel, 0, wx.EXPAND | wx.BOTTOM, 8)
        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_todo_count()
        return txt
    
    def _on_add_todo(self, event):
        txt = self._add_todo_item()
        txt.SetFocus()
        self._save_todos()
    
    def _on_timer_toggle(self, item_id, _unused):
        """Handle timer start/stop for a task."""
        current_item = None
        for item in self._todo_items:
            if item["id"] == item_id:
                current_item = item
                break
        
        # Get current running state and toggle
        is_currently_running = self.time_tracker.is_task_running(item_id)
        is_on = not is_currently_running  # Toggle state
        
        if is_on:
            prev_running = self.time_tracker.current_running_task_id
            self.time_tracker.start_task(item_id)
            
            # Update button to show "Stop"
            if current_item:
                self._update_timer_button(current_item, True)
            
            if prev_running is not None and prev_running != item_id:
                for item in self._todo_items:
                    if item["id"] == prev_running:
                        self._update_timer_button(item, False)
                        if "memo_panel" in item and item["memo_panel"]:
                            memo_text = item["memo_text"].GetValue().strip()
                            if memo_text:
                                self._save_memo_to_last_session(prev_running, memo_text)
                            item["memo_text"].SetValue("")
                            item["memo_panel"].Hide()
                        break
            
            if current_item and "memo_panel" in current_item:
                current_item["memo_panel"].Show()
                current_item["container"].Layout()
        else:
            if current_item and "memo_text" in current_item:
                memo_text = current_item["memo_text"].GetValue().strip()
                if memo_text:
                    self.time_tracker.task_timers[item_id]["pending_memo"] = memo_text
            
            self.time_tracker.stop_task(item_id)
            
            # Update button to show "Start"
            if current_item:
                self._update_timer_button(current_item, False)
            
            if current_item and "memo_panel" in current_item:
                current_item["memo_text"].SetValue("")
                current_item["memo_panel"].Hide()
                current_item["container"].Layout()
        
        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_timer_displays()
        self._save_todos()
    
    def _update_timer_button(self, item, is_running):
        """Update timer button appearance based on running state using theme colors."""
        btn = item.get("timer_switch")
        if not btn:
            return
        
        if is_running:
            btn.label = "Stop"
            btn.bg_color = hex_to_colour(self._theme["accent_red"])
            btn.fg_color = hex_to_colour("#FFFFFF")
        else:
            btn.label = "Start"
            btn.bg_color = hex_to_colour(self._theme["accent_green"])
            btn.fg_color = hex_to_colour("#FFFFFF")
        btn.Refresh()
    
    def _save_memo_to_last_session(self, item_id, memo_text):
        """Save a memo to the last session in history."""
        if item_id in self.time_tracker.task_timers:
            history = self.time_tracker.task_timers[item_id].get("history", [])
            if history:
                history[-1]["memo"] = memo_text
    
    def _on_memo_change(self, item_id):
        """Handle memo text changes."""
        pass
    
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
                
                if item["done"]:
                    self.time_tracker.mark_task_done(item_id)
                    self._update_timer_button(item, False)  # Reset to "Start" state
                    if "memo_panel" in item and item["memo_panel"]:
                        item["memo_panel"].Hide()
                        item["container"].Layout()
                
                font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
                if item["done"]:
                    font.SetStrikethrough(True)
                    item["text"].SetFont(font)
                    item["text"].SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
                else:
                    font.SetStrikethrough(False)
                    item["text"].SetFont(font)
                    # Use custom editor text color when unchecked
                    item["text"].SetForegroundColour(self._get_editor_text())
                
                item["text"].Refresh()
                break
        self._update_todo_count()
        self._save_todos()
    
    def _on_delete_todo(self, item_id):
        for i, item in enumerate(self._todo_items):
            if item["id"] == item_id:
                if "container" in item:
                    item["container"].Destroy()
                else:
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
            if "container" in item:
                item["container"].Destroy()
            else:
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
            
            time_str = self.time_tracker.get_task_time_string(item_id)
            item["timer_label"].SetLabel(time_str)
            
            rtc_str = self.time_tracker.get_last_session_string(item_id, self.time_tracker.time_format_24h)
            item["rtc_label"].SetLabel(rtc_str)
            
            task_data = self.time_tracker.task_timers.get(item_id, {})
            history = task_data.get("history", [])
            if history and len(history) > 0:
                tooltip_text = self.time_tracker.get_session_history_tooltip(item_id, self.time_tracker.time_format_24h)
                if tooltip_text:
                    item["rtc_label"].SetToolTip(tooltip_text)
