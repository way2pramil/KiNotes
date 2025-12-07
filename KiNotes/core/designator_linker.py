"""
KiNotes Designator Linker - Link @REF to PCB components
"""
import re

try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False
    pcbnew = None


class DesignatorLinker:
    """Links designator references (@R1, @U3) to PCB components."""
    
    # Pattern for valid designators
    DESIGNATOR_PATTERN = re.compile(r'^[A-Z]+\d+[A-Z]?$', re.IGNORECASE)
    
    def __init__(self):
        """Initialize the linker."""
        self._board = None
        self._last_highlighted = []
    
    def _get_board(self):
        """Get current PCB board."""
        if HAS_PCBNEW:
            return pcbnew.GetBoard()
        return None
    
    def highlight(self, designator):
        """
        Highlight a component by its reference designator.
        Returns True if component found and highlighted.
        """
        if not HAS_PCBNEW:
            print("KiNotes: pcbnew not available")
            return False
        
        board = self._get_board()
        if not board:
            print("KiNotes: No board loaded")
            return False
        
        # Clear previous highlights
        self._clear_highlights()
        
        # Find footprint by reference
        footprint = self._find_footprint(board, designator)
        if not footprint:
            print(f"KiNotes: Component {designator} not found")
            return False
        
        # Select and highlight the footprint
        try:
            # Clear current selection
            pcbnew.ClearSelection()
            
            # Select the footprint
            footprint.SetSelected()
            
            # Center view on footprint
            pos = footprint.GetPosition()
            
            # Try to zoom to footprint (KiCad 9+ API)
            try:
                view = pcbnew.GetView()
                if view:
                    view.SetCenter(pos)
            except:
                pass
            
            # Refresh the view
            pcbnew.Refresh()
            
            self._last_highlighted.append(footprint)
            return True
            
        except Exception as e:
            print(f"KiNotes: Error highlighting {designator}: {e}")
            return False
    
    def _find_footprint(self, board, designator):
        """Find footprint by reference designator."""
        designator_upper = designator.upper()
        
        for footprint in board.GetFootprints():
            ref = footprint.GetReference()
            if ref.upper() == designator_upper:
                return footprint
        
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
        """
        if not HAS_PCBNEW:
            return None
        
        board = self._get_board()
        if not board:
            return None
        
        footprint = self._find_footprint(board, designator)
        if not footprint:
            return None
        
        try:
            info = {
                "reference": footprint.GetReference(),
                "value": footprint.GetValue(),
                "footprint": footprint.GetFPIDAsString(),
                "layer": board.GetLayerName(footprint.GetLayer()),
                "position": {
                    "x": pcbnew.ToMM(footprint.GetPosition().x),
                    "y": pcbnew.ToMM(footprint.GetPosition().y),
                },
                "rotation": footprint.GetOrientationDegrees(),
                "nets": [],
            }
            
            # Get connected nets
            for pad in footprint.Pads():
                net = pad.GetNet()
                if net:
                    net_name = net.GetNetname()
                    if net_name and net_name not in info["nets"]:
                        info["nets"].append(net_name)
            
            return info
            
        except Exception as e:
            print(f"KiNotes: Error getting info for {designator}: {e}")
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
        """Find all @designator references in text."""
        pattern = r'@([A-Z]+\d+[A-Z]?)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches))
    
    def validate_designator(self, designator):
        """Check if designator exists on board."""
        if not HAS_PCBNEW:
            return False
        
        board = self._get_board()
        if not board:
            return False
        
        return self._find_footprint(board, designator) is not None
