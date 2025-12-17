"""
KiNotes Net Cache Manager

Centralizes net caching and board change detection. Designed to be reused
by multiple components (visual_editor, net_linker, etc.) and respond to
live board changes in KiCad.

Usage:
    manager = NetCacheManager()
    manager.refresh()  # On demand or on board change
    manager.get_linker()  # Get or create net_linker
    manager.watch_board_changes(callback)  # Register for board change events
"""

from __future__ import annotations

import sys
import threading
from typing import Optional, Callable, List

try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    pcbnew = None
    HAS_PCBNEW = False

# Import debug_module for per-module debug control
try:
    from .defaultsConfig import debug_module
except ImportError:
    try:
        from defaultsConfig import debug_module
    except ImportError:
        def debug_module(module, msg):
            pass


def _log(msg: str) -> None:
    """Route to debug_module for 'net' category."""
    debug_module('net', msg.replace('[KiNotes NetCacheManager] ', '').replace('[KiNotes] ', ''))


class NetCacheManager:
    """
    Centralized net cache manager for KiNotes.
    
    - Lazy-loads net_linker when board is available
    - Detects board changes and auto-refreshes cache
    - Provides refresh-on-demand API
    - Notifies listeners when cache updates
    """

    def __init__(self):
        """Initialize cache manager."""
        self._net_linker = None
        self._last_board_id = None
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

    def get_linker(self):
        """
        Get or create net linker.
        Returns None if pcbnew not available (outside KiCad).
        """
        if self._net_linker:
            return self._net_linker

        if not HAS_PCBNEW:
            _log("[KiNotes NetCacheManager] pcbnew not available (expected outside KiCad)")
            return None

        try:
            from .net_linker import NetLinker
            self._net_linker = NetLinker()
            self.refresh()  # Populate cache immediately
            _log("[KiNotes NetCacheManager] Net linker created and cache initialized")
            return self._net_linker
        except Exception as e:
            _log(f"[KiNotes NetCacheManager] Failed to create net linker: {e}")
            return None

    def refresh(self) -> bool:
        """
        Refresh net cache from current board.
        Returns True on success, False if no board or linker unavailable.
        """
        if not self._net_linker:
            linker = self.get_linker()
            if not linker:
                return False
            self._net_linker = linker

        try:
            self._net_linker.refresh_nets()
            _log("[KiNotes NetCacheManager] Net cache refreshed")
            self._notify_listeners("refresh")
            return True
        except Exception as e:
            _log(f"[KiNotes NetCacheManager] Cache refresh failed: {e}")
            return False

    def watch_board_changes(self, callback: Callable) -> None:
        """
        Register a callback for board change events.
        Callback signature: callback(event_type: str)
          - event_type: "refresh" or "board_change"
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def unwatch(self, callback: Callable) -> None:
        """Unregister a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def _notify_listeners(self, event_type: str) -> None:
        """Notify all registered callbacks."""
        with self._lock:
            callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(event_type)
            except Exception as e:
                _log(f"[KiNotes NetCacheManager] Callback error: {e}")

    def check_board_change(self) -> bool:
        """
        Check if board has changed. If so, refresh cache and notify.
        Returns True if board changed, False otherwise.
        
        Call this periodically or on focus events to detect live changes.
        """
        if not HAS_PCBNEW:
            return False

        try:
            board = pcbnew.GetBoard()
            if not board:
                return False

            # Get a stable board ID (use object id as proxy)
            current_id = id(board)
            if current_id != self._last_board_id:
                self._last_board_id = current_id
                _log("[KiNotes NetCacheManager] Board change detected, refreshing cache")
                self.refresh()
                self._notify_listeners("board_change")
                return True
        except Exception as e:
            _log(f"[KiNotes NetCacheManager] Board change check failed: {e}")

        return False

    def clear(self) -> None:
        """Clear cache (e.g., when closing a board)."""
        if self._net_linker:
            try:
                self._net_linker.clear_highlight()
            except Exception:
                pass
        self._last_board_id = None
        _log("[KiNotes NetCacheManager] Cache cleared")


# Global singleton for KiNotes
_cache_manager: Optional[NetCacheManager] = None


def get_net_cache_manager() -> NetCacheManager:
    """Get or create the global net cache manager singleton."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = NetCacheManager()
    return _cache_manager


__all__ = ["NetCacheManager", "get_net_cache_manager"]
