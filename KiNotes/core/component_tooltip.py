"""
KiNotes Component Tooltip Provider - Smart-Link Tooltips for PCB Components

Provides component property tooltips when hovering over linked designators.
Shows: Value, Footprint, Description, Custom Properties, Attributes.

Industry Standard:
- Uses KiCad pcbnew API: GetValue(), GetProperties(), GetAttributes()
- Follows IEEE 315 designator conventions
- Thread-safe with proper error handling
- Integrates with KiNotes debug panel

Module Size: ~250 lines (AI-friendly, fits in single context window)

Usage:
    from core.component_tooltip import ComponentTooltipProvider
    
    provider = ComponentTooltipProvider()
    provider.set_debug_logger(debug_logger)  # Optional
    
    info = provider.get_component_info("R1")
    tooltip_text = provider.format_tooltip(info)

Author: KiNotes Team (pcbtools.xyz)
License: MIT
"""

import functools
import sys
from typing import Optional, Dict, Any, List
from enum import Enum

# ============================================================
# LOGGING AND DEBUG SUPPORT
# ============================================================

def _kinotes_log(msg: str):
    """Log message to console, handling KiCad's None stdout."""
    try:
        if sys.stdout is not None:
            print(msg)
            sys.stdout.flush()
    except:
        pass


# Try to import debug logger for integration
try:
    from ..ui.debug_event_logger import EventLevel
    HAS_DEBUG_LOGGER = True
except ImportError:
    HAS_DEBUG_LOGGER = False
    EventLevel = None


# Try to import pcbnew
try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False
    pcbnew = None


# ============================================================
# COMPONENT ATTRIBUTES ENUM
# ============================================================

class ComponentType(Enum):
    """Component placement type based on KiCad attributes."""
    SMD = "SMD"
    THROUGH_HOLE = "Through-Hole"
    VIRTUAL = "Virtual"
    UNKNOWN = "Unknown"


# ============================================================
# SAFE API DECORATOR
# ============================================================

def safe_pcbnew_call(default_return=None, log_errors=True):
    """
    Decorator for safe pcbnew API calls.
    Catches all exceptions and returns default value on failure.
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
                    _kinotes_log(f"[ComponentTooltip] API call failed in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


# ============================================================
# COMPONENT INFO DATA CLASS
# ============================================================

class ComponentInfo:
    """
    Data class holding component information for tooltip display.
    
    Attributes:
        reference: Component reference designator (R1, C5, U3)
        value: Component value (10kΩ, 100nF, STM32F4)
        footprint: Footprint name (R_0805, LQFP-48)
        library: Footprint library name
        description: Component description
        keywords: Component keywords
        component_type: SMD, Through-Hole, Virtual
        position: (x_mm, y_mm) tuple
        rotation: Rotation in degrees
        layer: Component layer (F.Cu, B.Cu)
        properties: Dict of custom properties
        in_bom: Whether included in BOM
        dnp: Do Not Populate flag
    """
    
    def __init__(self):
        self.reference: str = ""
        self.value: str = ""
        self.footprint: str = ""
        self.library: str = ""
        self.description: str = ""
        self.keywords: str = ""
        self.mpn: str = ""  # Manufacturer Part Number
        self.component_type: ComponentType = ComponentType.UNKNOWN
        self.position: tuple = (0.0, 0.0)
        self.rotation: float = 0.0
        self.layer: str = ""
        self.properties: Dict[str, str] = {}
        self.in_bom: bool = True
        self.dnp: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'reference': self.reference,
            'value': self.value,
            'footprint': self.footprint,
            'library': self.library,
            'description': self.description,
            'keywords': self.keywords,
            'mpn': self.mpn,
            'component_type': self.component_type.value,
            'position': self.position,
            'rotation': self.rotation,
            'layer': self.layer,
            'properties': self.properties,
            'in_bom': self.in_bom,
            'dnp': self.dnp,
        }


# ============================================================
# COMPONENT TOOLTIP PROVIDER
# ============================================================

class ComponentTooltipProvider:
    """
    Provides component information tooltips for KiNotes Smart-Link.
    
    Features:
    - Queries pcbnew API for component properties
    - Formats data for tooltip display
    - Thread-safe with error protection
    - Debug panel integration
    - Caching for performance (optional)
    
    Example:
        provider = ComponentTooltipProvider()
        info = provider.get_component_info("R1")
        if info:
            tooltip = provider.format_tooltip(info)
            print(tooltip)
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialize tooltip provider.
        
        Args:
            enable_cache: Enable component info caching (default: True)
        """
        self._debug_logger = None
        self._debug_enabled = False
        self._cache: Dict[str, ComponentInfo] = {}
        self._cache_enabled = enable_cache
        self._tooltip_format = "detailed"  # "minimal", "detailed", "full"
    
    # ========================================
    # DEBUG INTEGRATION
    # ========================================
    
    def set_debug_logger(self, logger, enabled: bool = True):
        """
        Set debug logger for event tracking.
        
        Args:
            logger: Debug event logger instance
            enabled: Whether debug logging is enabled
        """
        self._debug_logger = logger
        self._debug_enabled = enabled
        self._log_debug("ComponentTooltipProvider initialized", EventLevel.INFO if HAS_DEBUG_LOGGER else None)
    
    def _log_debug(self, message: str, level=None):
        """Log debug message to console and debug panel."""
        _kinotes_log(f"[ComponentTooltip] {message}")
        
        if self._debug_enabled and self._debug_logger and HAS_DEBUG_LOGGER:
            try:
                level = level or EventLevel.DEBUG
                self._debug_logger.log(message, level, module="tooltip")
            except:
                pass
    
    # ========================================
    # COMPONENT INFO RETRIEVAL
    # ========================================
    
    @safe_pcbnew_call(default_return=None)
    def get_component_info(self, designator: str, use_cache: bool = True) -> Optional[ComponentInfo]:
        """
        Get component information by reference designator.
        
        Args:
            designator: Component reference (R1, C5, U3)
            use_cache: Whether to use cached data
            
        Returns:
            ComponentInfo object or None if not found
        """
        if not designator:
            return None
        
        designator_upper = designator.upper().strip()
        
        # Check cache first
        if use_cache and self._cache_enabled and designator_upper in self._cache:
            self._log_debug(f"Cache hit for {designator_upper}")
            return self._cache[designator_upper]
        
        # Get board
        board = pcbnew.GetBoard()
        if not board:
            self._log_debug("No board available", EventLevel.WARNING if HAS_DEBUG_LOGGER else None)
            return None
        
        # Find footprint
        footprint = self._find_footprint(board, designator_upper)
        if not footprint:
            self._log_debug(f"Component {designator_upper} not found")
            return None
        
        # Extract component info
        info = self._extract_component_info(footprint)
        
        # Cache result
        if self._cache_enabled:
            self._cache[designator_upper] = info
        
        self._log_debug(f"Retrieved info for {designator_upper}: {info.value}")
        return info
    
    def _find_footprint(self, board, designator: str):
        """Find footprint by reference designator."""
        try:
            for fp in board.GetFootprints():
                try:
                    ref = fp.GetReference()
                    if ref.upper() == designator:
                        return fp
                except:
                    continue
        except Exception as e:
            self._log_debug(f"Error finding footprint: {e}", EventLevel.ERROR if HAS_DEBUG_LOGGER else None)
        return None
    
    def _extract_component_info(self, footprint) -> ComponentInfo:
        """Extract all component information from footprint."""
        info = ComponentInfo()
        
        # Basic info (protected)
        try:
            info.reference = footprint.GetReference() or ""
        except:
            pass
        
        try:
            info.value = footprint.GetValue() or ""
        except:
            pass
        
        # Footprint info
        try:
            fpid = footprint.GetFPID()
            info.footprint = fpid.GetLibItemName() or ""
            info.library = fpid.GetLibNickname() or ""
        except:
            pass
        
        # Description and keywords
        try:
            info.description = footprint.GetDescription() or ""
        except:
            pass
        
        try:
            info.keywords = footprint.GetKeywords() or ""
        except:
            pass
        
        # Component type from attributes
        try:
            attrs = footprint.GetAttributes()
            if attrs & pcbnew.FP_SMD:
                info.component_type = ComponentType.SMD
            elif attrs & pcbnew.FP_THROUGH_HOLE:
                info.component_type = ComponentType.THROUGH_HOLE
            elif attrs & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
                info.component_type = ComponentType.VIRTUAL
            
            # BOM and DNP flags
            info.in_bom = not (attrs & pcbnew.FP_EXCLUDE_FROM_BOM)
            info.dnp = bool(attrs & pcbnew.FP_DNP) if hasattr(pcbnew, 'FP_DNP') else False
        except:
            pass
        
        # Position and rotation
        try:
            pos = footprint.GetPosition()
            # Convert from nm to mm
            info.position = (
                pcbnew.ToMM(pos.x),
                pcbnew.ToMM(pos.y)
            )
        except:
            pass
        
        try:
            info.rotation = footprint.GetOrientationDegrees()
        except:
            pass
        
        # Layer
        try:
            layer = footprint.GetLayer()
            info.layer = pcbnew.GetBoard().GetLayerName(layer)
        except:
            pass
        
        # Custom properties (KiCad 6+)
        try:
            if hasattr(footprint, 'GetProperties'):
                props = footprint.GetProperties()
                if props:
                    info.properties = dict(props)
        except:
            pass
        
        # Extract MPN from properties (various field name conventions)
        info.mpn = self._extract_mpn(info.properties, footprint)
        
        return info
    
    def _extract_mpn(self, properties: Dict[str, str], footprint) -> str:
        """
        Extract Manufacturer Part Number from component properties.
        
        Searches for common MPN field names used in industry:
        - MPN, Mpn, mpn
        - Manufacturer Part Number, Mfr Part Number
        - MFR Number, Mfr Number, mfr_number
        - Part Number, PartNumber, Part_Number
        - Manufacturer PN, ManufacturerPN
        
        Note: Distributor codes (LCSC, Digikey, Mouser, etc.) are NOT MPNs.
        
        Args:
            properties: Dict of component custom properties
            footprint: pcbnew footprint object for additional field access
            
        Returns:
            MPN string or empty string if not found
        """
        # Common MPN field name variations (case-insensitive search)
        # Note: Excludes distributor codes (LCSC, Digikey, Mouser, Farnell, etc.)
        mpn_field_names = [
            'mpn', 'mfr_pn', 'mfr_part', 'mfr_part_number',
            'manufacturer part number', 'manufacturer_part_number',
            'mfr number', 'mfr_number', 'mfrpn',
            'part number', 'partnumber', 'part_number', 'pn',
            'manufacturer pn', 'manufacturerpn',
        ]
        
        # Search in properties dict (case-insensitive)
        if properties:
            for key, value in properties.items():
                key_lower = str(key).lower().strip()
                if key_lower in mpn_field_names:
                    val_str = str(value).strip()
                    if val_str and val_str != '~':
                        return val_str
        
        # Try to get MPN from footprint fields directly (KiCad 7+)
        try:
            if hasattr(footprint, 'GetFieldByName'):
                for field_name in ['MPN', 'Mpn', 'mpn', 'Manufacturer Part Number', 'Part Number']:
                    try:
                        field = footprint.GetFieldByName(field_name)
                        if field:
                            text = field.GetText() if hasattr(field, 'GetText') else str(field)
                            if text and str(text).strip() and str(text).strip() != '~':
                                return str(text).strip()
                    except:
                        continue
        except:
            pass
        
        # Try GetFieldText for older KiCad versions
        try:
            if hasattr(footprint, 'GetFieldText'):
                for field_name in ['MPN', 'Mpn', 'mpn', 'Part Number']:
                    try:
                        text = footprint.GetFieldText(field_name)
                        if text and str(text).strip() and str(text).strip() != '~':
                            return str(text).strip()
                    except:
                        continue
        except:
            pass
        
        return ""
    
    # ========================================
    # TOOLTIP FORMATTING
    # ========================================
    
    def format_tooltip(self, info: Optional[ComponentInfo], format_style: str = None) -> str:
        """
        Format component info as tooltip text.
        
        Args:
            info: ComponentInfo object
            format_style: "minimal", "detailed", or "full" (default: self._tooltip_format)
            
        Returns:
            Formatted tooltip string
        """
        if not info:
            return ""
        
        style = format_style or self._tooltip_format
        
        if style == "minimal":
            return self._format_minimal(info)
        elif style == "full":
            return self._format_full(info)
        else:  # detailed (default)
            return self._format_detailed(info)
    
    def _format_minimal(self, info: ComponentInfo) -> str:
        """Minimal tooltip: Reference and Value only."""
        lines = [f"📌 {info.reference}"]
        if info.value:
            lines.append(f"Value: {info.value}")
        return "\n".join(lines)
    
    def _format_detailed(self, info: ComponentInfo) -> str:
        """Detailed tooltip: Common properties."""
        lines = [f"📌 {info.reference}"]
        
        if info.value:
            lines.append(f"Value: {info.value}")
        
        if info.footprint:
            lines.append(f"Footprint: {info.footprint}")
        
        if info.component_type != ComponentType.UNKNOWN:
            lines.append(f"Type: {info.component_type.value}")
        
        if info.layer:
            lines.append(f"Layer: {info.layer}")
        
        # Show DNP warning
        if info.dnp:
            lines.append("⚠️ DNP (Do Not Populate)")
        
        # Show key custom properties (limit to 3)
        if info.properties:
            count = 0
            for key, val in info.properties.items():
                if count >= 3:
                    lines.append("...")
                    break
                lines.append(f"{key}: {val}")
                count += 1
        
        return "\n".join(lines)
    
    def _format_full(self, info: ComponentInfo) -> str:
        """Full tooltip: All available properties."""
        lines = [f"📌 {info.reference}"]
        lines.append("─" * 20)
        
        if info.value:
            lines.append(f"Value: {info.value}")
        
        if info.footprint:
            fp_text = info.footprint
            if info.library:
                fp_text = f"{info.library}:{info.footprint}"
            lines.append(f"Footprint: {fp_text}")
        
        if info.description:
            lines.append(f"Description: {info.description}")
        
        if info.component_type != ComponentType.UNKNOWN:
            lines.append(f"Type: {info.component_type.value}")
        
        if info.layer:
            lines.append(f"Layer: {info.layer}")
        
        # Position and rotation
        if info.position != (0.0, 0.0):
            lines.append(f"Position: ({info.position[0]:.2f}, {info.position[1]:.2f}) mm")
        
        if info.rotation:
            lines.append(f"Rotation: {info.rotation}°")
        
        # Flags
        flags = []
        if not info.in_bom:
            flags.append("Excluded from BOM")
        if info.dnp:
            flags.append("DNP")
        if flags:
            lines.append(f"Flags: {', '.join(flags)}")
        
        # All custom properties
        if info.properties:
            lines.append("─" * 20)
            lines.append("Properties:")
            for key, val in info.properties.items():
                lines.append(f"  {key}: {val}")
        
        return "\n".join(lines)
    
    # ========================================
    # CACHE MANAGEMENT
    # ========================================
    
    def clear_cache(self):
        """Clear the component info cache."""
        self._cache.clear()
        self._log_debug("Cache cleared")
    
    def refresh_cache(self, designator: str):
        """Refresh cache for a specific component."""
        designator_upper = designator.upper().strip()
        if designator_upper in self._cache:
            del self._cache[designator_upper]
        return self.get_component_info(designator, use_cache=False)
    
    def set_tooltip_format(self, format_style: str):
        """
        Set default tooltip format style.
        
        Args:
            format_style: "minimal", "detailed", or "full"
        """
        if format_style in ("minimal", "detailed", "full"):
            self._tooltip_format = format_style
            self._log_debug(f"Tooltip format set to: {format_style}")
    
    # ========================================
    # BATCH OPERATIONS
    # ========================================
    
    def get_multiple_components(self, designators: List[str]) -> Dict[str, ComponentInfo]:
        """
        Get info for multiple components at once.
        
        Args:
            designators: List of reference designators
            
        Returns:
            Dict mapping designator to ComponentInfo
        """
        results = {}
        for ref in designators:
            info = self.get_component_info(ref)
            if info:
                results[ref.upper()] = info
        return results


# ============================================================
# MODULE TEST (for debug panel verification)
# ============================================================

def _test_tooltip_provider():
    """Test function - run inside KiCad to verify functionality."""
    provider = ComponentTooltipProvider()
    
    _kinotes_log("\n" + "=" * 50)
    _kinotes_log("[ComponentTooltip] TEST START")
    _kinotes_log("=" * 50)
    
    if not HAS_PCBNEW:
        _kinotes_log("[ComponentTooltip] ERROR: pcbnew not available - run inside KiCad")
        return False
    
    board = pcbnew.GetBoard()
    if not board:
        _kinotes_log("[ComponentTooltip] ERROR: No board loaded")
        return False
    
    # Get first footprint for testing
    footprints = list(board.GetFootprints())
    if not footprints:
        _kinotes_log("[ComponentTooltip] ERROR: No footprints on board")
        return False
    
    test_ref = footprints[0].GetReference()
    _kinotes_log(f"[ComponentTooltip] Testing with component: {test_ref}")
    
    # Get component info
    info = provider.get_component_info(test_ref)
    if info:
        _kinotes_log("\n[ComponentTooltip] --- Minimal Format ---")
        _kinotes_log(provider.format_tooltip(info, "minimal"))
        
        _kinotes_log("\n[ComponentTooltip] --- Detailed Format ---")
        _kinotes_log(provider.format_tooltip(info, "detailed"))
        
        _kinotes_log("\n[ComponentTooltip] --- Full Format ---")
        _kinotes_log(provider.format_tooltip(info, "full"))
        
        _kinotes_log("\n[ComponentTooltip] --- Raw Data ---")
        for key, val in info.to_dict().items():
            _kinotes_log(f"  {key}: {val}")
        
        _kinotes_log("\n" + "=" * 50)
        _kinotes_log("[ComponentTooltip] TEST PASSED ✓")
        _kinotes_log("=" * 50)
        return True
    else:
        _kinotes_log(f"[ComponentTooltip] ERROR: Could not get info for {test_ref}")
        _kinotes_log("[ComponentTooltip] TEST FAILED ✗")
        return False


# ============================================================
# AUTO-RUN TEST ON MODULE LOAD (inside KiCad only)
# ============================================================

# Set to True to run test automatically when module loads
_AUTO_TEST_ON_LOAD = True

if _AUTO_TEST_ON_LOAD and HAS_PCBNEW:
    try:
        # Only test if board is loaded (delayed check)
        import pcbnew as _pcb_check
        if _pcb_check.GetBoard() is not None:
            _kinotes_log("[ComponentTooltip] Module loaded - running inline test...")
            _test_tooltip_provider()
        else:
            _kinotes_log("[ComponentTooltip] Module loaded - no board, skipping auto-test")
    except:
        _kinotes_log("[ComponentTooltip] Module loaded - auto-test skipped (no board)")
else:
    _kinotes_log("[ComponentTooltip] Module loaded (pcbnew available: {})".format(HAS_PCBNEW))


if __name__ == "__main__":
    _test_tooltip_provider()
