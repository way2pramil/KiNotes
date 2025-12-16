"""
KiNotes Designator Linker - Smart Cross-Probe for PCB components

Supports smart detection of standard designator patterns:
- Resistors: R1, R12, R123
- Capacitors: C1, C12
- Inductors: L1, L12
- Diodes: D1, D12, LED1
- ICs/Chips: U1, U12, IC1
- Transistors: Q1, Q12
- Connectors: J1, P1, CON1
- Switches: SW1, S1
- Fuses: F1
- Ferrite Beads: FB1
- Test Points: TP1
- Crystals: Y1, X1, XTAL1
- Transformers: T1
- Relays: K1, RLY1

Also supports explicit [[DESIGNATOR]] syntax for edge cases.
"""
import re
import sys
import functools

from .defaultsConfig import DESIGNATOR_PREFIXES

def _kinotes_log(msg: str):
    """Log message to console, handling KiCad's None stdout."""
    try:
        if sys.stdout is not None:
            print(msg)
            sys.stdout.flush()
    except:
        pass  # Silently ignore if stdout not available

try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False
    pcbnew = None


# ============================================================
# SAFE PCBNEW API DECORATOR - Prevents crashes from API calls
# ============================================================

def safe_pcbnew_call(default_return=None, log_errors=True):
    """
    Decorator for safe pcbnew API calls.
    Catches all exceptions and returns default value on failure.
    Prevents KiCad crashes from invalid API states.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if not HAS_PCBNEW:
                    return default_return
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    _kinotes_log(f"[KiNotes] Safe API call failed in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


def safe_board_operation(func):
    """
    Decorator for operations requiring valid board.
    Validates board exists before executing.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if not HAS_PCBNEW:
                return None
            board = pcbnew.GetBoard()
            if board is None:
                _kinotes_log("[KiNotes] No board available for operation")
                return None
            return func(self, *args, board=board, **kwargs)
        except Exception as e:
            _kinotes_log(f"[KiNotes] Board operation failed in {func.__name__}: {e}")
            return None
    return wrapper


class DesignatorLinker:
    """Smart cross-probe linker for PCB component designators."""
    
    # Standard EE designator prefixes (from centralized config)
    DEFAULT_PREFIXES = DESIGNATOR_PREFIXES
    
    # Explicit syntax: [[CUSTOM_REF]] for edge cases
    EXPLICIT_PATTERN = re.compile(r'\[\[([A-Z0-9_-]+)\]\]', re.IGNORECASE)
    
    # Legacy @REF pattern (backward compatibility)
    LEGACY_PATTERN = re.compile(r'@([A-Z]+\d+[A-Z]?)\b', re.IGNORECASE)
    
    # Combined pattern for validation
    DESIGNATOR_PATTERN = re.compile(r'^[A-Z]+\d+[A-Z]?$', re.IGNORECASE)
    
    def __init__(self):
        """Initialize the linker."""
        self._board = None
        self._last_highlighted = []
        self._custom_prefixes = []
        self._rebuild_pattern()
    
    def _rebuild_pattern(self):
        """Rebuild the smart designator pattern with custom prefixes."""
        all_prefixes = self.DEFAULT_PREFIXES + self._custom_prefixes
        # Sort by length (longest first) to ensure MOV matches before M
        sorted_prefixes = sorted(set(all_prefixes), key=len, reverse=True)
        self.SMART_DESIGNATOR_PATTERN = re.compile(
            r'\b(' + '|'.join(sorted_prefixes) + r')(\d+[A-Z]?)\b',
            re.IGNORECASE
        )
        _kinotes_log(f"[KiNotes] Designator prefixes: {len(sorted_prefixes)} total ({len(self._custom_prefixes)} custom)")
    
    def set_custom_prefixes(self, prefixes_str):
        """
        Set custom designator prefixes from comma-separated string.
        Example: "MOV, PC, NTC, PTC"
        """
        if not prefixes_str:
            self._custom_prefixes = []
        else:
            # Parse comma-separated, strip whitespace, uppercase, filter empty
            self._custom_prefixes = [
                p.strip().upper() 
                for p in prefixes_str.split(',') 
                if p.strip() and p.strip().isalpha()
            ]
        self._rebuild_pattern()
        return self._custom_prefixes
    
    def get_custom_prefixes(self):
        """Return current custom prefixes as list."""
        return self._custom_prefixes.copy()
    
    def get_custom_prefixes_str(self):
        """Return current custom prefixes as comma-separated string."""
        return ', '.join(self._custom_prefixes)
    
    @safe_pcbnew_call(default_return=None)
    def _get_board(self):
        """Get current PCB board safely."""
        return pcbnew.GetBoard()
    
    def highlight(self, designator):
        """
        Highlight a component by its reference designator.
        Returns True if component found and highlighted.
        All pcbnew calls are protected against crashes.
        """
        if not HAS_PCBNEW:
            _kinotes_log(f"[KiNotes Cross-Probe] pcbnew not available - running outside KiCad")
            return False
        
        try:
            board = self._get_board()
            if not board:
                _kinotes_log("[KiNotes Cross-Probe] No board loaded in pcbnew")
                return False
            
            # Clear previous highlights (protected)
            self._clear_highlights()
            
            # Find footprint by reference (protected)
            footprint = self._find_footprint_safe(board, designator)
            if not footprint:
                _kinotes_log(f"[KiNotes Cross-Probe] Component '{designator}' not found on board")
                return False
            
            # Select and highlight the footprint (all calls protected)
            result = self._highlight_footprint_safe(board, footprint, designator)
            
            # === CONSOLE OUTPUT: Show component info in KiCad scripting console ===
            # Note: UI tooltip is handled separately by visual_editor.py
            if result:
                try:
                    from .component_tooltip import ComponentTooltipProvider
                    tooltip_provider = ComponentTooltipProvider()
                    info = tooltip_provider.get_component_info(designator)
                    if info:
                        # Combined output: highlight confirmation + component details
                        _kinotes_log(f"\n{'─' * 40}")
                        _kinotes_log(f"[Smart-Link] {designator} highlighted on PCB")
                        _kinotes_log(f"{'─' * 40}")
                        _kinotes_log(f"  Value:     {info.value or 'N/A'}")
                        if info.mpn:
                            _kinotes_log(f"  MPN:       {info.mpn}")
                        _kinotes_log(f"  Footprint: {info.footprint or 'N/A'}")
                        _kinotes_log(f"  Type:      {info.component_type.value}")
                        _kinotes_log(f"  Layer:     {info.layer or 'N/A'}")
                        if info.position != (0.0, 0.0):
                            _kinotes_log(f"  Position:  ({info.position[0]:.2f}, {info.position[1]:.2f}) mm")
                        if info.dnp:
                            _kinotes_log(f"  Status:    DNP (Do Not Populate)")
                        if info.properties:
                            for key, val in list(info.properties.items())[:3]:
                                _kinotes_log(f"  {key}: {val}")
                        _kinotes_log(f"{'─' * 40}\n")
                except Exception as tooltip_err:
                    _kinotes_log(f"[ComponentTooltip] Error: {tooltip_err}")
            
            return result
            
        except Exception as e:
            _kinotes_log(f"[KiNotes Cross-Probe] Highlight operation failed: {e}")
            return False
    
    def _highlight_footprint_safe(self, board, footprint, designator):
        """Safely highlight a footprint with full error protection."""
        try:
            # Clear previous selection on all footprints
            try:
                for fp in board.GetFootprints():
                    try:
                        fp.ClearSelected()
                    except:
                        pass
            except:
                pass
            
            # Select the target footprint
            try:
                footprint.SetSelected()
            except Exception as e:
                _kinotes_log(f"[KiNotes Cross-Probe] Could not select: {e}")
                return False
            
            # Center view on footprint
            try:
                pos = footprint.GetPosition()
                
                # Try to focus/zoom to footprint
                try:
                    # KiCad 9 uses FocusOnLocation
                    pcbnew.FocusOnLocation(pos)
                except:
                    try:
                        # Alternative: use Refresh with position
                        view = pcbnew.GetView()
                        if view:
                            view.SetCenter(pos)
                    except:
                        pass
            except:
                pass  # Position/focus failure is not critical
            
            # Refresh the view
            try:
                pcbnew.Refresh()
            except:
                pass  # Refresh failure is not critical
            
            self._last_highlighted.append(footprint)
            return True
            
        except Exception as e:
            _kinotes_log(f"[KiNotes Cross-Probe] Error highlighting {designator}: {e}")
            return False
    
    def _find_footprint_safe(self, board, designator):
        """Find footprint by reference designator with error protection."""
        try:
            designator_upper = designator.upper()
            
            for footprint in board.GetFootprints():
                try:
                    ref = footprint.GetReference()
                    if ref.upper() == designator_upper:
                        return footprint
                except:
                    continue  # Skip footprints that can't be read
            
            return None
        except Exception as e:
            _kinotes_log(f"[KiNotes Cross-Probe] Error finding footprint: {e}")
            return None
    
    def _clear_highlights(self):
        """Clear previous highlights."""
        if not HAS_PCBNEW:
            return
        
        try:
            for fp in self._last_highlighted:
                if fp:
                    fp.ClearSelected()
            self._last_highlighted = []
        except:
            self._last_highlighted = []
    
    def get_component_info(self, designator):
        """
        Get detailed information about a component.
        Returns dict with value, footprint, layer, nets, position.
        All pcbnew calls are protected against crashes.
        """
        if not HAS_PCBNEW:
            return None
        
        try:
            board = self._get_board()
            if not board:
                return None
            
            footprint = self._find_footprint_safe(board, designator)
            if not footprint:
                return None
            
            info = {
                "reference": self._safe_get_attr(footprint, 'GetReference', 'Unknown'),
                "value": self._safe_get_attr(footprint, 'GetValue', ''),
                "footprint": self._safe_get_attr(footprint, 'GetFPIDAsString', ''),
                "layer": '',
                "position": {"x": 0, "y": 0},
                "rotation": 0,
                "nets": [],
            }
            
            # Safely get layer name
            try:
                info["layer"] = board.GetLayerName(footprint.GetLayer())
            except:
                pass
            
            # Safely get position
            try:
                pos = footprint.GetPosition()
                info["position"] = {
                    "x": pcbnew.ToMM(pos.x),
                    "y": pcbnew.ToMM(pos.y),
                }
            except:
                pass
            
            # Safely get rotation
            try:
                info["rotation"] = footprint.GetOrientationDegrees()
            except:
                pass
            
            # Safely get connected nets
            try:
                for pad in footprint.Pads():
                    try:
                        net = pad.GetNet()
                        if net:
                            net_name = net.GetNetname()
                            if net_name and net_name not in info["nets"]:
                                info["nets"].append(net_name)
                    except:
                        continue
            except:
                pass
            
            return info
            
        except Exception as e:
            _kinotes_log(f"[KiNotes] Error getting info for {designator}: {e}")
            return None
    
    def _safe_get_attr(self, obj, method_name, default=''):
        """Safely call a method on an object, returning default on failure."""
        try:
            method = getattr(obj, method_name, None)
            if method:
                return method()
            return default
        except:
            return default
            return None
    
    def format_component_info(self, designator):
        """Format component info as markdown string."""
        info = self.get_component_info(designator)
        if not info:
            return f"Component {designator} not found"
        
        lines = [
            f"### {info['reference']}",
            f"- **Value:** {info['value']}",
            f"- **Footprint:** {info['footprint']}",
            f"- **Layer:** {info['layer']}",
            f"- **Position:** ({info['position']['x']:.2f}mm, {info['position']['y']:.2f}mm)",
            f"- **Rotation:** {info['rotation']}°",
        ]
        
        if info["nets"]:
            lines.append(f"- **Nets:** {', '.join(info['nets'][:5])}")
            if len(info["nets"]) > 5:
                lines.append(f"  *(+{len(info['nets']) - 5} more)*")
        
        return "\n".join(lines)
    
    def find_all_designators_in_text(self, text):
        """
        Find all component designators in text using smart detection.
        
        Returns list of tuples: [(designator, start_pos, end_pos), ...]
        Detects:
        1. Smart pattern: R1, C12, U3, LED5, SW10, etc.
        2. Explicit pattern: [[CUSTOM_REF]]
        3. Legacy pattern: @R1 (backward compatibility)
        """
        results = []
        seen = set()  # Avoid duplicates at same position
        
        # Smart detection - standard designator patterns
        for match in self.SMART_DESIGNATOR_PATTERN.finditer(text):
            designator = match.group(0).upper()
            start, end = match.span()
            key = (designator, start)
            if key not in seen:
                results.append((designator, start, end))
                seen.add(key)
        
        # Explicit [[REF]] syntax
        for match in self.EXPLICIT_PATTERN.finditer(text):
            designator = match.group(1).upper()
            start, end = match.span()
            key = (designator, start)
            if key not in seen:
                # Return inner designator but full span for replacement
                results.append((designator, start, end))
                seen.add(key)
        
        # Legacy @REF pattern (backward compat)
        for match in self.LEGACY_PATTERN.finditer(text):
            designator = match.group(1).upper()
            start, end = match.span()
            key = (designator, start)
            if key not in seen:
                results.append((designator, start, end))
                seen.add(key)
        
        # Sort by position
        results.sort(key=lambda x: x[1])
        return results
    
    def find_designators_simple(self, text):
        """
        Simple version - returns just list of unique designator strings.
        For backward compatibility.
        """
        found = self.find_all_designators_in_text(text)
        return list(set(d[0] for d in found))
    
    def validate_designator(self, designator):
        """Check if designator exists on board."""
        if not HAS_PCBNEW:
            return False
        
        board = self._get_board()
        if not board:
            return False
        
        return self._find_footprint(board, designator) is not None
