"""
KiNotes Time Tracker - Per-task stopwatch with session history.

This module provides TimeTracker class for:
- Per-task time tracking with start/stop
- Session history with memos
- Work diary export to Markdown
- JSON serialization for persistence

Usage:
    from .time_tracker import TimeTracker
    tracker = TimeTracker()
    tracker.create_task_timer(task_id)
    tracker.start_task(task_id)
    tracker.stop_task(task_id)
"""
import time
import datetime

from ..core.defaultsConfig import TIME_TRACKER_DEFAULTS


class TimeTracker:
    """Manages per-task time tracking with session history and persistence."""
    
    def __init__(self):
        # Load defaults from centralized config
        self.enable_time_tracking = TIME_TRACKER_DEFAULTS['enable_time_tracking']
        self.time_format_24h = TIME_TRACKER_DEFAULTS['time_format_24h']
        self.show_work_diary_button = TIME_TRACKER_DEFAULTS['show_work_diary_button']
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
            "history": []  # [{"start": timestamp, "stop": timestamp, "memo": "..."}, ...]
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
                
                # Log session history with optional memo
                session_entry = {
                    "start": int(start),
                    "stop": int(time.time())
                }
                
                # Include pending memo if set
                pending_memo = self.task_timers[task_id].get("pending_memo", "")
                if pending_memo:
                    session_entry["memo"] = pending_memo
                    self.task_timers[task_id]["pending_memo"] = ""  # Clear after use
                
                self.task_timers[task_id]["history"].append(session_entry)
            
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
        total_seconds = self.get_total_seconds()
        
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
    
    def export_work_diary(self, format_24h=True):
        """Generate Markdown work diary content with session memos."""
        total_sec = self.get_total_seconds()
        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        
        # Choose time format based on setting
        time_fmt = "%H:%M" if format_24h else "%I:%M %p"
        
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
                    start_dt = datetime.datetime.fromtimestamp(session['start']).strftime(time_fmt)
                    stop_dt = datetime.datetime.fromtimestamp(session['stop']).strftime(time_fmt)
                    sess_sec = session['stop'] - session['start']
                    sess_min = sess_sec // 60
                    session_line = f"- Session: {start_dt} → {stop_dt} ({sess_min} min)"
                    
                    # Add memo if present
                    memo = session.get("memo", "")
                    if memo:
                        session_line += f" — *{memo}*"
                    
                    lines.append(session_line)
                
                lines.append(f"**Total: {t_hours}h {t_minutes}m**")
                lines.append("")
        
        return "\n".join(lines)
    
    def get_last_session_string(self, task_id, format_24h=True):
        """
        Get last completed session as inline display string.
        Format: "(10:12 → 10:40 28m)"
        Returns empty string if no sessions or task is running.
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
        
        # Format times
        if format_24h:
            start_time = datetime.datetime.fromtimestamp(start_ts).strftime("%H:%M")
            stop_time = datetime.datetime.fromtimestamp(stop_ts).strftime("%H:%M")
        else:
            start_time = datetime.datetime.fromtimestamp(start_ts).strftime("%I:%M %p")
            stop_time = datetime.datetime.fromtimestamp(stop_ts).strftime("%I:%M %p")
        
        # Calculate duration
        duration = stop_ts - start_ts
        duration_str = self._format_duration(duration)
        
        return f"({start_time} → {stop_time} {duration_str})"
    
    def get_session_history_tooltip(self, task_id, format_24h=True):
        """Generate full session history for tooltip display."""
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
            duration_str = self._format_duration(duration)
            
            line = f"• {start_time} → {stop_time} ({duration_str})"
            
            # Add memo if present
            memo = session.get("memo", "")
            if memo:
                # Truncate long memos for tooltip
                if len(memo) > 40:
                    memo = memo[:37] + "..."
                line += f"\n  📝 {memo}"
            
            lines.append(line)
        
        # Add header and total
        if total_seconds > 0:
            total_str = self._format_duration(total_seconds)
            header = f"Work Sessions ({len(history)})"
            lines.insert(0, header)
            lines.append(f"Total: {total_str}")
        
        return "\n".join(lines)
    
    def _format_duration(self, seconds):
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    
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
