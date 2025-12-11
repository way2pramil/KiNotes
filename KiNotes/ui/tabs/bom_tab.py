"""BOM Tab - Bill of Materials generation tab for KiNotes.

This mixin provides:
- BOM tab UI with column/filter/grouping options
- BOM generation from PCB board
- Export to notes functionality
"""

import wx
import wx.lib.scrolledpanel as scrolled
import datetime
import re

from ..themes import hex_to_colour
from ..components.buttons import RoundedButton


class BomTabMixin:
    """Mixin class providing BOM tab functionality.
    
    Requires parent class to have:
    - _theme: dict with theme colors
    - _dark_mode: bool for current mode
    - _get_editor_bg(): method returning editor background color
    - _get_editor_text(): method returning editor text color
    - _get_note_content(): method to get current note content
    - _set_note_content(content): method to set note content
    - text_editor: reference to text editor control
    - _apply_editor_colors(): method to apply editor colors
    - _show_tab(index): method to switch tabs
    """
    
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
                current = self._get_note_content()
                if current and not current.endswith("\n"):
                    current += "\n"
                current += "\n" + bom_text
                self._set_note_content(current)
                if self.text_editor:
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
