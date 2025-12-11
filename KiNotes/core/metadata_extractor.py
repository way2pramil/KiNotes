"""
KiNotes Metadata Extractor - Extract BOM, Stackup, Netlist from KiCad 9+
With crash-safe pcbnew API wrappers
"""
import os
import sys
from datetime import datetime

def _kinotes_log(msg: str):
    """Log message to console, handling KiCad's None stdout."""
    try:
        if sys.stdout is not None:
            print(msg)
            sys.stdout.flush()
    except:
        pass

try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False
    pcbnew = None


class MetadataExtractor:
    """Extract metadata from KiCad PCB for insertion into notes."""
    
    def __init__(self):
        """Initialize the extractor."""
        self._board = None
    
    def _get_board(self):
        """Get current PCB board safely."""
        try:
            if HAS_PCBNEW:
                return pcbnew.GetBoard()
        except Exception as e:
            _kinotes_log(f"[KiNotes] Error getting board: {e}")
        return None
    
    def _safe_get_footprints(self, board):
        """Safely get footprints list from board."""
        try:
            return list(board.GetFootprints())
        except Exception as e:
            _kinotes_log(f"[KiNotes] Error getting footprints: {e}")
            return []
    
    def _safe_get_attr(self, obj, method_name, default=''):
        """Safely call a method on an object."""
        try:
            method = getattr(obj, method_name, None)
            if method:
                return method()
            return default
        except:
            return default
    
    def extract(self, meta_type):
        """
        Extract metadata of specified type with full crash protection.
        
        Args:
            meta_type: One of 'bom', 'stackup', 'board_size', 'diff_pairs',
                      'netlist', 'layers', 'drill_table', 'design_rules', 'all'
        
        Returns:
            Formatted markdown string
        """
        try:
            extractors = {
                'bom': self.extract_bom,
                'stackup': self.extract_stackup,
                'board_size': self.extract_board_size,
                'diff_pairs': self.extract_diff_pairs,
                'netlist': self.extract_netlist,
                'layers': self.extract_layers,
                'drill_table': self.extract_drill_table,
                'design_rules': self.extract_design_rules,
                'all': self.extract_all,
            }
            
            extractor = extractors.get(meta_type)
            if extractor:
                return extractor()
            return f"Unknown metadata type: {meta_type}"
        except Exception as e:
            _kinotes_log(f"[KiNotes] Metadata extraction error: {e}")
            return f"<!-- Error extracting {meta_type} -->"
    
    def extract_bom(self):
        """Extract Bill of Materials with crash protection."""
        try:
            board = self._get_board()
            if not board:
                return "<!-- Error: No board loaded -->"
            
            lines = [
                "## Bill of Materials",
                "",
                "| Ref | Value | Footprint | Qty |",
                "|-----|-------|-----------|-----|",
            ]
            
            # Group by value and footprint
            components = {}
            for fp in self._safe_get_footprints(board):
                try:
                    ref = self._safe_get_attr(fp, 'GetReference', 'Unknown')
                    value = self._safe_get_attr(fp, 'GetValue', '')
                    fpid = self._safe_get_attr(fp, 'GetFPIDAsString', '')
                    footprint = fpid.split(':')[-1] if ':' in fpid else fpid
                    
                    key = (value, footprint)
                    if key not in components:
                        components[key] = []
                    components[key].append(ref)
                except:
                    continue
            
            # Sort and format
            for (value, footprint), refs in sorted(components.items()):
                try:
                    refs_str = ", ".join(sorted(refs, key=lambda x: (x[0], int(''.join(filter(str.isdigit, x)) or 0))))
                    lines.append(f"| {refs_str} | {value} | {footprint} | {len(refs)} |")
                except:
                    refs_str = ", ".join(refs)
                    lines.append(f"| {refs_str} | {value} | {footprint} | {len(refs)} |")
            
            lines.extend(["", f"*Total components: {sum(len(r) for r in components.values())}*", ""])
            return "\n".join(lines)
            
        except Exception as e:
            _kinotes_log(f"[KiNotes] BOM extraction error: {e}")
            return "<!-- Error extracting BOM -->"
    
    def extract_stackup(self):
        """Extract layer stackup information."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = [
            "| Layer | Type | Material | Thickness | Epsilon |",
            "|-------|------|----------|-----------|---------|",
        ]
        
        stackup_found = False
        stackup = None
        
        try:
            # KiCad 9+ direct stackup accessor (new in KiCad 9)
            if hasattr(board, 'GetStackup'):
                stackup = board.GetStackup()
            
            # Fallback to older API via GetDesignSettings
            if stackup is None:
                ds = board.GetDesignSettings()
                if hasattr(ds, 'GetStackupDescriptor'):
                    stackup = ds.GetStackupDescriptor()
            
            if stackup is not None:
                # Try GetCount() + GetStackupLayer(i) (KiCad 9+)
                if hasattr(stackup, 'GetCount'):
                    count = stackup.GetCount()
                    for i in range(count):
                        item = stackup.GetStackupLayer(i)
                        if item is None:
                            continue
                        stackup_found = True
                        self._add_stackup_layer_row(lines, board, item, i)
                
                # Try iterating directly (some KiCad versions)
                elif hasattr(stackup, '__iter__'):
                    for i, item in enumerate(stackup):
                        stackup_found = True
                        self._add_stackup_layer_row(lines, board, item, i)
                
                # Try GetList() with list() conversion
                elif hasattr(stackup, 'GetList'):
                    try:
                        stack_list = list(stackup.GetList())
                        for i, item in enumerate(stack_list):
                            stackup_found = True
                            self._add_stackup_layer_row(lines, board, item, i)
                    except:
                        pass
                    
        except Exception as e:
            lines.append(f"| (Stackup API error: {e}) | | | | |")
        
        # Fallback: show basic copper layer info
        if not stackup_found:
            lines = [
                "| Layer | Type |",
                "|-------|------|",
            ]
            try:
                copper_count = board.GetCopperLayerCount()
                enabled = board.GetEnabledLayers()
                
                for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT):
                    if enabled.Contains(layer_id) and pcbnew.IsCopperLayer(layer_id):
                        layer_name = board.GetLayerName(layer_id)
                        lines.append(f"| {layer_name} | Copper |")
                
                lines.append("")
                lines.append(f"*Total copper layers: {copper_count}*")
            except Exception as e:
                lines.append(f"| (Error: {e}) | |")
        
        lines.append("")
        return "\n".join(lines)
    
    def _add_stackup_layer_row(self, lines, board, item, index):
        """Helper to add a stackup layer row."""
        # Get layer name
        try:
            layer_id = item.GetBrdLayerId()
            layer_name = board.GetLayerName(layer_id) if layer_id >= 0 else "Dielectric"
        except:
            layer_name = f"Layer {index}"
        
        # Get layer type
        try:
            type_name = item.GetTypeName()
        except:
            type_name = "Unknown"
        
        # Get material
        try:
            material = item.GetMaterial() or "-"
        except:
            material = "-"
        
        # Get thickness
        try:
            thickness_iu = item.GetThickness()
            thickness_mm = pcbnew.ToMM(thickness_iu)
            thickness_str = f"{thickness_mm:.3f}mm"
        except:
            thickness_str = "N/A"
        
        # Get epsilon_r
        try:
            epsilon = item.GetEpsilonR()
            epsilon_str = f"{epsilon:.2f}" if epsilon > 0 else "-"
        except:
            epsilon_str = "-"
        
        lines.append(f"| {layer_name} | {type_name} | {material} | {thickness_str} | {epsilon_str} |")
    
    def extract_board_size(self):
        """Extract board dimensions."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = ["## Board Size", ""]
        
        try:
            # Get board outline bounding box
            bbox = board.GetBoardEdgesBoundingBox()
            width_mm = pcbnew.ToMM(bbox.GetWidth())
            height_mm = pcbnew.ToMM(bbox.GetHeight())
            
            # Try to get board area
            try:
                area_mm2 = width_mm * height_mm
            except:
                area_mm2 = 0
            
            lines.extend([
                f"- **Width:** {width_mm:.2f} mm ({width_mm/25.4:.3f} in)",
                f"- **Height:** {height_mm:.2f} mm ({height_mm/25.4:.3f} in)",
                f"- **Area:** {area_mm2:.2f} mm² ({area_mm2/645.16:.3f} in²)",
            ])
            
            # Layer count
            layer_count = board.GetCopperLayerCount()
            lines.append(f"- **Copper Layers:** {layer_count}")
            
        except Exception as e:
            lines.append(f"*Error extracting board size: {e}*")
        
        lines.append("")
        return "\n".join(lines)
    
    def extract_diff_pairs(self):
        """Extract differential pair information using KiCad's IsDiffPair() API or pattern matching."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = [
            "## Differential Pairs",
            "",
        ]
        
        try:
            diff_pairs_found = []
            processed_nets = set()
            
            # Try KiCad's native IsDiffPair() detection first
            net_info = board.GetNetInfo()
            has_isdiffpair = False
            
            for i in range(net_info.GetNetCount()):
                net = net_info.GetNetItem(i)
                if net and hasattr(net, 'IsDiffPair'):
                    has_isdiffpair = True
                    try:
                        if net.IsDiffPair():
                            # Convert wxString to Python str
                            net_name = str(net.GetNetname())
                            
                            # Avoid duplicate pairs (both P and N will report as diff pair)
                            if net_name not in processed_nets:
                                # Try to get the coupled net
                                if hasattr(net, 'GetDiffPairCoupledNet'):
                                    coupled_net = net.GetDiffPairCoupledNet()
                                    if coupled_net:
                                        coupled_name = str(coupled_net.GetNetname())
                                        processed_nets.add(net_name)
                                        processed_nets.add(coupled_name)
                                        
                                        # Determine which is positive/negative based on naming
                                        if net_name.endswith('+') or net_name.endswith('_P') or net_name.endswith('P'):
                                            diff_pairs_found.append((net_name, coupled_name))
                                        else:
                                            diff_pairs_found.append((coupled_name, net_name))
                                else:
                                    # Fallback: just mark as diff pair without coupled info
                                    processed_nets.add(net_name)
                                    diff_pairs_found.append((net_name, "?"))
                    except:
                        pass  # IsDiffPair() call failed, will use fallback
            
            # Fallback to string pattern matching if no pairs found
            # This works regardless of whether IsDiffPair() exists
            if not diff_pairs_found:
                nets = {}
                for i in range(net_info.GetNetCount()):
                    net = net_info.GetNetItem(i)
                    if net:
                        net_name = str(net.GetNetname())
                        nets[net_name] = True
                
                # Common differential pair naming patterns
                for net_name in nets:
                    if net_name in processed_nets:
                        continue
                    
                    # Pattern: name+ / name- (USB_D+, USB_D-)
                    if net_name.endswith('+'):
                        base = net_name[:-1]
                        pair_name = base + '-'
                        if pair_name in nets and pair_name not in processed_nets:
                            diff_pairs_found.append((net_name, pair_name))
                            processed_nets.add(net_name)
                            processed_nets.add(pair_name)
                    
                    # Pattern: name_P / name_N (ETH_TX_P, ETH_TX_N)
                    elif net_name.endswith('_P'):
                        base = net_name[:-2]
                        pair_name = base + '_N'
                        if pair_name in nets and pair_name not in processed_nets:
                            diff_pairs_found.append((net_name, pair_name))
                            processed_nets.add(net_name)
                            processed_nets.add(pair_name)
                    
                    # Pattern: nameP / nameN (no underscore)
                    elif net_name.endswith('P') and not net_name.endswith('_P'):
                        base = net_name[:-1]
                        pair_name = base + 'N'
                        if pair_name in nets and pair_name not in processed_nets:
                            # Verify it looks like a diff pair (has signal-like base)
                            if any(c.isdigit() or c == '_' for c in base):
                                diff_pairs_found.append((net_name, pair_name))
                                processed_nets.add(net_name)
                                processed_nets.add(pair_name)
            
            if diff_pairs_found:
                lines.extend([
                    "| Positive | Negative |",
                    "|----------|----------|",
                ])
                for pos, neg in diff_pairs_found[:20]:  # Limit to 20
                    lines.append(f"| {pos} | {neg} |")
                
                if len(diff_pairs_found) > 20:
                    lines.append(f"| *...and {len(diff_pairs_found) - 20} more* | |")
            else:
                lines.append("*No differential pairs detected*")
            
        except Exception as e:
            lines.append(f"*Error extracting diff pairs: {e}*")
        
        lines.append("")
        return "\n".join(lines)
    
    def extract_netlist(self):
        """Extract netlist summary."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = [
            "## Netlist Summary",
            "",
        ]
        
        try:
            net_info = board.GetNetInfo()
            net_count = net_info.GetNetCount()
            
            lines.append(f"**Total Nets:** {net_count}")
            lines.append("")
            
            # List significant nets (exclude GND, VCC variations for brevity)
            lines.extend([
                "### Key Nets",
                "",
                "| Net Name | Pad Count |",
                "|----------|-----------|",
            ])
            
            nets_with_pads = []
            for i in range(net_count):
                net = net_info.GetNetItem(i)
                if net:
                    net_name = net.GetNetname()
                    if net_name and not net_name.startswith("unconnected"):
                        # Count pads on this net
                        pad_count = 0
                        for fp in board.GetFootprints():
                            for pad in fp.Pads():
                                if pad.GetNet() and pad.GetNet().GetNetname() == net_name:
                                    pad_count += 1
                        if pad_count > 0:
                            nets_with_pads.append((net_name, pad_count))
            
            # Sort by pad count descending
            nets_with_pads.sort(key=lambda x: -x[1])
            
            for net_name, pad_count in nets_with_pads[:15]:
                lines.append(f"| {net_name} | {pad_count} |")
            
            if len(nets_with_pads) > 15:
                lines.append(f"| *...and {len(nets_with_pads) - 15} more nets* | |")
            
        except Exception as e:
            lines.append(f"*Error extracting netlist: {e}*")
        
        lines.append("")
        return "\n".join(lines)
    
    def extract_layers(self):
        """Extract layer information."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = [
            "## Layer Information",
            "",
            "| Layer ID | Name | Type |",
            "|----------|------|------|",
        ]
        
        try:
            # Get enabled layers
            enabled_layers = board.GetEnabledLayers()
            
            for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT):
                if enabled_layers.Contains(layer_id):
                    layer_name = board.GetLayerName(layer_id)
                    layer_type = "Copper" if pcbnew.IsCopperLayer(layer_id) else "Technical"
                    lines.append(f"| {layer_id} | {layer_name} | {layer_type} |")
            
        except Exception as e:
            lines.append(f"| Error: {e} | | |")
        
        lines.append("")
        return "\n".join(lines)
    
    def extract_drill_table(self):
        """Extract drill/via information."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = [
            "## Drill Table",
            "",
            "| Drill Size | Count | Type |",
            "|------------|-------|------|",
        ]
        
        try:
            drills = {}
            
            # Count vias
            for track in board.GetTracks():
                if track.GetClass() == "PCB_VIA":
                    via = track.Cast_to_PCB_VIA() if hasattr(track, 'Cast_to_PCB_VIA') else track
                    drill = pcbnew.ToMM(via.GetDrillValue())
                    key = (drill, "Via")
                    drills[key] = drills.get(key, 0) + 1
            
            # Count pad holes
            for fp in board.GetFootprints():
                for pad in fp.Pads():
                    if pad.GetDrillSize().x > 0:
                        drill = pcbnew.ToMM(pad.GetDrillSize().x)
                        key = (drill, "PTH")
                        drills[key] = drills.get(key, 0) + 1
            
            # Sort and display
            for (drill_size, drill_type), count in sorted(drills.items()):
                lines.append(f"| {drill_size:.2f} mm | {count} | {drill_type} |")
            
            if not drills:
                lines.append("| *No drills found* | | |")
            
        except Exception as e:
            lines.append(f"| Error: {e} | | |")
        
        lines.append("")
        return "\n".join(lines)
    
    def extract_design_rules(self):
        """Extract design rules (KiCad 9 compatible)."""
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        lines = [
            "## Design Rules",
            "",
        ]
        
        try:
            ds = board.GetDesignSettings()
            
            lines.append("### Clearances")
            
            # KiCad 9 uses m_TrackMinWidth instead of GetTrackMinWidth()
            # Try multiple API patterns for compatibility
            
            # Min Track Width
            min_track = None
            for attr in ['m_TrackMinWidth', 'GetTrackMinWidth']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    min_track = val() if callable(val) else val
                    break
            if min_track is not None:
                lines.append(f"- **Min Track Width:** {pcbnew.ToMM(min_track):.3f} mm")
            
            # Min Clearance
            min_clearance = None
            for attr in ['m_MinClearance', 'GetMinClearance']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    min_clearance = val() if callable(val) else val
                    break
            if min_clearance is not None:
                lines.append(f"- **Min Clearance:** {pcbnew.ToMM(min_clearance):.3f} mm")
            
            # Min Via Size
            min_via = None
            for attr in ['m_ViasMinSize', 'GetViasMinSize']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    min_via = val() if callable(val) else val
                    break
            if min_via is not None:
                lines.append(f"- **Min Via Diameter:** {pcbnew.ToMM(min_via):.3f} mm")
            
            # Min Via Drill
            min_drill = None
            for attr in ['m_MinThroughDrill', 'GetMinThroughDrill', 'm_ViasMinDrill', 'GetViasMinDrill']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    min_drill = val() if callable(val) else val
                    break
            if min_drill is not None:
                lines.append(f"- **Min Via Drill:** {pcbnew.ToMM(min_drill):.3f} mm")
            
            # Microvia settings
            min_uvia = None
            for attr in ['m_MicroViasMinSize', 'GetMicroViasMinSize']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    min_uvia = val() if callable(val) else val
                    break
            if min_uvia is not None and min_uvia > 0:
                lines.append(f"- **Min µVia Diameter:** {pcbnew.ToMM(min_uvia):.3f} mm")
            
            lines.append("")
            lines.append("### Copper")
            lines.append(f"- **Copper Layers:** {board.GetCopperLayerCount()}")
            
            # Default track width
            track_width = None
            for attr in ['GetCurrentTrackWidth', 'm_CurrentTrackWidth']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    try:
                        track_width = val() if callable(val) else val
                        break
                    except:
                        pass
            if track_width is not None:
                lines.append(f"- **Default Track Width:** {pcbnew.ToMM(track_width):.3f} mm")
            
            # Default via size
            via_size = None
            for attr in ['GetCurrentViaSize', 'm_CurrentViaSize']:
                if hasattr(ds, attr):
                    val = getattr(ds, attr)
                    try:
                        via_size = val() if callable(val) else val
                        break
                    except:
                        pass
            if via_size is not None:
                lines.append(f"- **Default Via Size:** {pcbnew.ToMM(via_size):.3f} mm")
            
        except Exception as e:
            lines.append(f"*Error extracting design rules: {e}*")
        
        lines.append("")
        return "\n".join(lines)
    
    def extract_all(self):
        """Extract all metadata types."""
        sections = [
            self.extract_board_size(),
            self.extract_layers(),
            self.extract_bom(),
            self.extract_netlist(),
            self.extract_diff_pairs(),
            self.extract_drill_table(),
            self.extract_design_rules(),
            self.extract_stackup(),
        ]
        
        header = f"# Board Metadata\n*Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        return header + "\n---\n\n".join(sections)
