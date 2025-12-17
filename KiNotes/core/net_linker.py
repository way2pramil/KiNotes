"""
KiNotes Net Linker - Beta

Cross-probe nets by name using KiCad's pcbnew APIs. Designed to be AI-friendly
(single-purpose module, <200 lines) and safe against KiCad crashes via guarded
pcbnew calls.

Usage (beta-gated in callers):
    linker = NetLinker()
    linker.refresh_nets()           # cache net names -> codes/pads
    linker.highlight("GND")        # highlight a net by name
    linker.clear_highlight()

Supports two highlight strategies:
- Native highlight (preferred): board.HighlightNet / board.SetHighLight
- Fallback: select a sample of items on the net and refresh view
"""

from __future__ import annotations

import sys
import functools
from typing import Dict, Optional, List

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
    """Legacy log - use debug_module('net', msg) instead."""
    debug_module('net', msg.replace('[KiNotes] ', '').replace('[KiNotes NetLinker] ', ''))


def safe_pcbnew_call(default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not HAS_PCBNEW:
                return default
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _log(f"[KiNotes] NetLinker safe call failed in {func.__name__}: {e}")
                return default
        return wrapper
    return decorator


class NetLinker:
    """Cross-probe nets by name (beta)."""

    # Pattern for in-text tokens, e.g. [[NET:VCC]], @NET:VCC (used by callers)
    NET_TOKEN_PREFIX = "NET:"

    def __init__(self):
        self._net_map: Dict[str, int] = {}  # name -> net code
        self._sample_pads: Dict[str, List] = {}  # name -> list of pads for focus
        self._last_selected: List = []

    @safe_pcbnew_call(default=None)
    def _get_board(self):
        return pcbnew.GetBoard()

    @safe_pcbnew_call(default=None)
    def refresh_nets(self):
        """Cache net names to codes and a few pads for centering."""
        board = self._get_board()
        if not board:
            return None

        self._net_map.clear()
        self._sample_pads.clear()

        try:
            netinfo = board.GetNetInfo()
            net_count = netinfo.GetNetCount()
            _log(f"[KiNotes] Refreshing nets: Found {net_count} nets on board")
            
            for i in range(net_count):
                net = netinfo.GetNetItem(i)
                if not net:
                    continue
                name = str(net.GetNetname())
                code = net.GetNet() if hasattr(net, "GetNet") else net.GetNetCode()
                self._net_map[name] = code
                self._sample_pads[name] = []
                
                # Debug: show each net name (first 20 + any with AC_N2)
                if i < 20 or 'AC_N2' in name:
                    _log(f"[KiNotes] Net {i}: '{name}' (code: {code})")
            
            # Debug: Check if AC_N2 hierarchical net exists
            for net_name in self._net_map.keys():
                if 'AC_N2' in net_name:
                    _log(f"[KiNotes] Found AC_N2 variant: '{net_name}'")
                    
        except Exception as e:
            _log(f"[KiNotes] NetLinker refresh error: {e}")

        # Collect a few pads per net for centering
        try:
            for pad in board.GetPads():
                try:
                    net = pad.GetNet()
                    if not net:
                        continue
                    name = str(net.GetNetname())
                    if name in self._sample_pads and len(self._sample_pads[name]) < 3:
                        self._sample_pads[name].append(pad)
                except Exception:
                    continue
        except Exception as e:
            _log(f"[KiNotes] NetLinker pad sampling error: {e}")
        return True

    def highlight(self, net_name: str) -> bool:
        """Highlight a net by name. Returns True on success.
        
        Performs case-insensitive matching.
        """
        if not HAS_PCBNEW:
            _log("[KiNotes] NetLinker: pcbnew not available")
            return False

        board = self._get_board()
        if not board:
            return False

        net_name_upper = net_name.upper()
        code = None
        matched_name = None

        # Try exact match first
        code = self._net_map.get(net_name)
        if code is not None:
            matched_name = net_name
        
        # If not found, try case-insensitive and hierarchical match
        if code is None:
            for cached_name, cached_code in self._net_map.items():
                cached_upper = cached_name.upper()
                # Exact case-insensitive
                if cached_upper == net_name_upper:
                    code = cached_code
                    matched_name = cached_name
                    _log(f"[KiNotes] Found net (case-insensitive): {net_name} -> {cached_name}")
                    break
                # Hierarchical: ends with /NET_NAME
                if cached_upper.endswith('/' + net_name_upper):
                    code = cached_code
                    matched_name = cached_name
                    _log(f"[KiNotes] Found net (hierarchical): {net_name} -> {cached_name}")
                    break
        
        # If still not found, try refresh once
        if code is None:
            self.refresh_nets()
            
            for cached_name, cached_code in self._net_map.items():
                cached_upper = cached_name.upper()
                if cached_upper == net_name_upper:
                    code = cached_code
                    matched_name = cached_name
                    _log(f"[KiNotes] Found net after refresh: {net_name} -> {cached_name}")
                    break
                if cached_upper.endswith('/' + net_name_upper):
                    code = cached_code
                    matched_name = cached_name
                    _log(f"[KiNotes] Found net after refresh (hierarchical): {net_name} -> {cached_name}")
                    break
        
        if code is None:
            _log(f"[KiNotes] Net '{net_name}' not found after all attempts")
            return False

        self.clear_highlight()

        # Preferred native highlight API
        if hasattr(board, "HighlightNet"):
            try:
                board.HighlightNet(code)
                pcbnew.Refresh()
                _log(f"[KiNotes] ✓ Highlighted: {matched_name} (code: {code})")
                return True
            except Exception as e:
                _log(f"[KiNotes] Net highlight failed (HighlightNet): {e}")

        if hasattr(board, "SetHighLight"):
            try:
                board.SetHighLight(code)
                pcbnew.Refresh()
                _log(f"[KiNotes] ✓ Highlighted: {matched_name} (code: {code})")
                return True
            except Exception as e:
                _log(f"[KiNotes] Net highlight failed (SetHighLight): {e}")

        # Fallback: select pads/tracks on the net (lightweight sample)
        try:
            self._select_items_on_net(board, code)
            pcbnew.Refresh()
            _log(f"[KiNotes] ✓ Selected items on: {matched_name} (code: {code})")
            return True
        except Exception as e:
            _log(f"[KiNotes] Net highlight fallback failed: {e}")
            return False

    def is_valid_net(self, net_name: str) -> bool:
        """Check if a net name is valid (exists in board cache).
        
        Supports:
        - Exact match: 'GND' -> 'GND'
        - Case-insensitive: 'AC_N2' -> 'ac_n2'
        - Partial/hierarchical: 'AC_N2' -> '/01 - POWER SUPPLY/AC_N2'
        
        Force-refreshes on cache miss to handle board updates.
        """
        net_name_upper = net_name.upper()
        
        # First check cache (exact and case-insensitive)
        for cached_name in self._net_map.keys():
            if cached_name.upper() == net_name_upper:
                return True
            # Also match if user typed suffix and board has hierarchical name
            # e.g., user types 'AC_N2', board has '/01 - POWER/AC_N2'
            if cached_name.upper().endswith('/' + net_name_upper):
                _log(f"[KiNotes] Partial net match: {net_name} -> {cached_name}")
                return True
        
        # Cache miss: try refresh once to catch any new nets
        # (board may have been updated since last cache refresh)
        self.refresh_nets()
        
        # Check again after refresh (exact, case-insensitive, and partial)
        for cached_name in self._net_map.keys():
            if cached_name.upper() == net_name_upper:
                _log(f"[KiNotes] Found net after refresh: {net_name}")
                return True
            if cached_name.upper().endswith('/' + net_name_upper):
                _log(f"[KiNotes] Partial net match after refresh: {net_name} -> {cached_name}")
                return True
        
        return False

    def clear_highlight(self) -> None:
        """Clear any active highlight (native API or fallback selections)."""
        if not HAS_PCBNEW:
            _log("[KiNotes] NetLinker clear_highlight: pcbnew not available")
            return
        
        _log("[KiNotes] NetLinker clear_highlight: attempting to clear...")
        try:
            board = self._get_board()
            if not board:
                _log("[KiNotes] NetLinker clear_highlight: no board found")
                return
            
            # Try HighlightNet with different values
            if hasattr(board, 'HighlightNet'):
                try:
                    # Try -1 (most common unhighlight value)
                    board.HighlightNet(-1)
                    pcbnew.Refresh()
                    _log("[KiNotes] ✓ Highlight cleared (HighlightNet(-1))")
                    return
                except Exception as e:
                    _log(f"[KiNotes] HighlightNet(-1) failed: {e}")
                    try:
                        # Try 0 as fallback
                        board.HighlightNet(0)
                        pcbnew.Refresh()
                        _log("[KiNotes] ✓ Highlight cleared (HighlightNet(0))")
                        return
                    except Exception as e2:
                        _log(f"[KiNotes] HighlightNet(0) failed: {e2}")
            
            # Try SetHighLight
            if hasattr(board, 'SetHighLight'):
                try:
                    board.SetHighLight(0)
                    pcbnew.Refresh()
                    _log("[KiNotes] ✓ Highlight cleared (SetHighLight(0))")
                    return
                except Exception as e:
                    _log(f"[KiNotes] SetHighLight(0) failed: {e}")
            
            # Try ClearHighlight (alternative method)
            if hasattr(board, 'ClearHighlight'):
                try:
                    board.ClearHighlight()
                    pcbnew.Refresh()
                    _log("[KiNotes] ✓ Highlight cleared (ClearHighlight)")
                    return
                except Exception as e:
                    _log(f"[KiNotes] ClearHighlight failed: {e}")
            
            _log("[KiNotes] No native unhighlight API found, using fallback...")
        except Exception as e:
            _log(f"[KiNotes] Native unhighlight error: {e}")
        
        # Fallback: clear any selected items
        _log("[KiNotes] Fallback: clearing selected items...")
        try:
            board = self._get_board()
            if board:
                # Try to deselect all pads
                try:
                    for pad in board.GetPads():
                        try:
                            pad.ClearSelected()
                        except Exception:
                            pass
                except Exception:
                    pass
                
                # Try to deselect all tracks
                try:
                    for track in board.GetTracks():
                        try:
                            track.ClearSelected()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception as e:
            _log(f"[KiNotes] Error deselecting all items: {e}")
        
        # Also clear our tracked items
        try:
            for item in self._last_selected:
                try:
                    item.ClearSelected()
                except Exception:
                    continue
        except Exception:
            pass
        self._last_selected = []
        
        # Force refresh to show the deselection
        try:
            pcbnew.Refresh()
        except Exception:
            pass
        
        _log("[KiNotes] ✓ Highlight cleared (fallback method)")

    def _select_items_on_net(self, board, net_code: int, max_items: int = 500):
        """Select all items on a net: pads, tracks, vias, and zones."""
        count = 0
        try:
            # Select all pads on this net
            for pad in board.GetPads():
                try:
                    if pad.GetNetCode() == net_code:
                        pad.SetSelected()
                        self._last_selected.append(pad)
                        count += 1
                except Exception:
                    continue
            
            # Select all tracks and vias on this net
            # GetTracks() returns tracks AND vias in KiCad
            for track in board.GetTracks():
                try:
                    if track.GetNetCode() == net_code:
                        track.SetSelected()
                        self._last_selected.append(track)
                        count += 1
                except Exception:
                    continue
            
            # Select zones (copper pours/polygons) on this net
            try:
                zones = board.Zones() if hasattr(board, 'Zones') else []
                for zone in zones:
                    try:
                        if zone.GetNetCode() == net_code:
                            zone.SetSelected()
                            self._last_selected.append(zone)
                            count += 1
                    except Exception:
                        continue
            except Exception:
                pass
            
            _log(f"[KiNotes] Selected {count} items on net code {net_code}")
            
            # Center view on first selected item
            if self._last_selected:
                try:
                    pos = self._last_selected[0].GetPosition()
                    try:
                        pcbnew.FocusOnLocation(pos)
                    except Exception:
                        view = pcbnew.GetView()
                        if view:
                            view.SetCenter(pos)
                except Exception:
                    pass
        except Exception as e:
            _log(f"[KiNotes] Net selection error: {e}")


__all__ = ["NetLinker"]
