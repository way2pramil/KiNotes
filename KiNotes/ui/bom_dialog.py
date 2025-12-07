# KiNotes - BOM Configuration Dialog (IBOM-style)
"""
Interactive BOM dialog with column selection and grouping options.
Similar to Interactive BOM (IBOM) plugin functionality.
"""

import wx

try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False
    pcbnew = None


class BOMConfigDialog(wx.Dialog):
    """
    BOM configuration dialog with IBOM-style options.
    Allows selecting columns, grouping, sorting, and filtering.
    """
    
    # Available columns that can be included in BOM
    AVAILABLE_COLUMNS = [
        ('reference', 'Reference', True),
        ('value', 'Value', True),
        ('footprint', 'Footprint', True),
        ('quantity', 'Quantity', True),
        ('description', 'Description', False),
        ('manufacturer', 'Manufacturer', False),
        ('mpn', 'MPN (Mfr Part Number)', False),
        ('supplier', 'Supplier', False),
        ('spn', 'SPN (Supplier Part Number)', False),
        ('layer', 'Layer (Top/Bottom)', False),
        ('x_pos', 'X Position', False),
        ('y_pos', 'Y Position', False),
        ('rotation', 'Rotation', False),
        ('dnp', 'DNP Status', False),
    ]
    
    # Grouping options
    GROUP_OPTIONS = [
        ('value_footprint', 'Group by Value + Footprint'),
        ('value', 'Group by Value only'),
        ('footprint', 'Group by Footprint only'),
        ('none', 'No grouping (one row per component)'),
    ]
    
    # Sort options
    SORT_OPTIONS = [
        ('reference', 'Reference (R1, R2, C1...)'),
        ('value', 'Value'),
        ('footprint', 'Footprint'),
        ('quantity', 'Quantity (descending)'),
    ]
    
    def __init__(self, parent):
        super().__init__(
            parent,
            title="BOM Configuration",
            size=(500, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.selected_columns = []
        self.group_by = 'value_footprint'
        self.sort_by = 'reference'
        self.exclude_dnp = True
        self.exclude_fiducials = True
        self.exclude_testpoints = True
        self.include_headers = True
        self.table_style = 'markdown'  # or 'simple'
        
        self._init_ui()
        self.Centre()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === Columns Section ===
        col_box = wx.StaticBox(panel, label="Columns to Include")
        col_sizer = wx.StaticBoxSizer(col_box, wx.VERTICAL)
        
        self.column_checks = {}
        col_grid = wx.FlexGridSizer(rows=0, cols=2, hgap=20, vgap=5)
        
        for col_id, col_name, default in self.AVAILABLE_COLUMNS:
            cb = wx.CheckBox(panel, label=col_name)
            cb.SetValue(default)
            self.column_checks[col_id] = cb
            col_grid.Add(cb, 0, wx.ALL, 2)
        
        col_sizer.Add(col_grid, 0, wx.ALL | wx.EXPAND, 5)
        
        # Select All / None buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        select_all_btn = wx.Button(panel, label="Select All")
        select_none_btn = wx.Button(panel, label="Select None")
        select_all_btn.Bind(wx.EVT_BUTTON, self._on_select_all)
        select_none_btn.Bind(wx.EVT_BUTTON, self._on_select_none)
        btn_sizer.Add(select_all_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(select_none_btn, 0)
        col_sizer.Add(btn_sizer, 0, wx.ALL, 5)
        
        panel_sizer.Add(col_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # === Grouping Section ===
        group_box = wx.StaticBox(panel, label="Grouping")
        group_sizer = wx.StaticBoxSizer(group_box, wx.VERTICAL)
        
        self.group_choice = wx.Choice(panel)
        for group_id, group_name in self.GROUP_OPTIONS:
            self.group_choice.Append(group_name, group_id)
        self.group_choice.SetSelection(0)
        group_sizer.Add(self.group_choice, 0, wx.ALL | wx.EXPAND, 5)
        
        panel_sizer.Add(group_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # === Sorting Section ===
        sort_box = wx.StaticBox(panel, label="Sort By")
        sort_sizer = wx.StaticBoxSizer(sort_box, wx.VERTICAL)
        
        self.sort_choice = wx.Choice(panel)
        for sort_id, sort_name in self.SORT_OPTIONS:
            self.sort_choice.Append(sort_name, sort_id)
        self.sort_choice.SetSelection(0)
        sort_sizer.Add(self.sort_choice, 0, wx.ALL | wx.EXPAND, 5)
        
        panel_sizer.Add(sort_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # === Filters Section ===
        filter_box = wx.StaticBox(panel, label="Filters")
        filter_sizer = wx.StaticBoxSizer(filter_box, wx.VERTICAL)
        
        self.exclude_dnp_cb = wx.CheckBox(panel, label="Exclude DNP (Do Not Populate) components")
        self.exclude_dnp_cb.SetValue(True)
        filter_sizer.Add(self.exclude_dnp_cb, 0, wx.ALL, 5)
        
        self.exclude_fiducials_cb = wx.CheckBox(panel, label="Exclude fiducials (FID*)")
        self.exclude_fiducials_cb.SetValue(True)
        filter_sizer.Add(self.exclude_fiducials_cb, 0, wx.ALL, 5)
        
        self.exclude_testpoints_cb = wx.CheckBox(panel, label="Exclude test points (TP*)")
        self.exclude_testpoints_cb.SetValue(True)
        filter_sizer.Add(self.exclude_testpoints_cb, 0, wx.ALL, 5)
        
        panel_sizer.Add(filter_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # === Output Format Section ===
        format_box = wx.StaticBox(panel, label="Output Format")
        format_sizer = wx.StaticBoxSizer(format_box, wx.VERTICAL)
        
        self.include_headers_cb = wx.CheckBox(panel, label="Include column headers")
        self.include_headers_cb.SetValue(True)
        format_sizer.Add(self.include_headers_cb, 0, wx.ALL, 5)
        
        style_sizer = wx.BoxSizer(wx.HORIZONTAL)
        style_sizer.Add(wx.StaticText(panel, label="Table style:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.style_choice = wx.Choice(panel, choices=["Markdown Table", "Simple List", "CSV-style"])
        self.style_choice.SetSelection(0)
        style_sizer.Add(self.style_choice, 1)
        format_sizer.Add(style_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        panel_sizer.Add(format_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        panel.SetSizer(panel_sizer)
        main_sizer.Add(panel, 1, wx.EXPAND)
        
        # === Buttons ===
        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        self.SetSizer(main_sizer)
    
    def _on_select_all(self, event):
        """Select all columns."""
        for cb in self.column_checks.values():
            cb.SetValue(True)
    
    def _on_select_none(self, event):
        """Deselect all columns."""
        for cb in self.column_checks.values():
            cb.SetValue(False)
    
    def get_config(self):
        """Get the selected configuration."""
        return {
            'columns': [col_id for col_id, cb in self.column_checks.items() if cb.GetValue()],
            'group_by': self.group_choice.GetClientData(self.group_choice.GetSelection()),
            'sort_by': self.sort_choice.GetClientData(self.sort_choice.GetSelection()),
            'exclude_dnp': self.exclude_dnp_cb.GetValue(),
            'exclude_fiducials': self.exclude_fiducials_cb.GetValue(),
            'exclude_testpoints': self.exclude_testpoints_cb.GetValue(),
            'include_headers': self.include_headers_cb.GetValue(),
            'table_style': ['markdown', 'simple', 'csv'][self.style_choice.GetSelection()],
        }


class BOMGenerator:
    """
    Generate BOM with configurable columns, grouping, and formatting.
    IBOM-style functionality for KiNotes.
    """
    
    def __init__(self):
        self._board = None
    
    def _get_board(self):
        """Get current PCB board."""
        if HAS_PCBNEW:
            return pcbnew.GetBoard()
        return None
    
    def generate(self, config=None):
        """
        Generate BOM with given configuration.
        
        Args:
            config: Dict with columns, group_by, sort_by, filters, format options
                   If None, uses defaults (like IBOM)
        
        Returns:
            Formatted BOM string (Markdown table, simple list, or CSV)
        """
        if config is None:
            config = {
                'columns': ['reference', 'value', 'footprint', 'quantity'],
                'group_by': 'value_footprint',
                'sort_by': 'reference',
                'exclude_dnp': True,
                'exclude_fiducials': True,
                'exclude_testpoints': True,
                'include_headers': True,
                'table_style': 'markdown',
            }
        
        board = self._get_board()
        if not board:
            return "<!-- Error: No board loaded -->"
        
        # Extract all components
        components = self._extract_components(board, config)
        
        if not components:
            return "## Bill of Materials\n\n*No components found matching criteria*\n"
        
        # Group components
        grouped = self._group_components(components, config['group_by'])
        
        # Sort groups
        sorted_groups = self._sort_groups(grouped, config['sort_by'])
        
        # Format output
        return self._format_output(sorted_groups, config)
    
    def _extract_components(self, board, config):
        """Extract component data from board."""
        components = []
        
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            
            # Apply filters
            if config.get('exclude_dnp', True):
                # Check DNP attribute (KiCad 9+)
                try:
                    if hasattr(fp, 'GetAttributes'):
                        attrs = fp.GetAttributes()
                        if hasattr(attrs, 'IsExcludedFromBOM') and attrs.IsExcludedFromBOM():
                            continue
                    # Also check for DNP in reference or "DNP" field
                    if 'DNP' in ref.upper():
                        continue
                except:
                    pass
            
            if config.get('exclude_fiducials', True):
                if ref.upper().startswith('FID') or 'FIDUCIAL' in fp.GetValue().upper():
                    continue
            
            if config.get('exclude_testpoints', True):
                if ref.upper().startswith('TP') or 'TESTPOINT' in fp.GetValue().upper():
                    continue
            
            # Extract all possible fields
            comp = {
                'reference': ref,
                'value': fp.GetValue(),
                'footprint': self._get_footprint_name(fp),
                'quantity': 1,
                'description': self._get_field(fp, 'Description') or self._get_field(fp, 'Desc') or '',
                'manufacturer': self._get_field(fp, 'Manufacturer') or self._get_field(fp, 'Mfr') or '',
                'mpn': self._get_field(fp, 'MPN') or self._get_field(fp, 'Mfr_PN') or '',
                'supplier': self._get_field(fp, 'Supplier') or self._get_field(fp, 'Vendor') or '',
                'spn': self._get_field(fp, 'SPN') or self._get_field(fp, 'Supplier_PN') or '',
                'layer': 'Top' if fp.GetLayer() == pcbnew.F_Cu else 'Bottom',
                'x_pos': f"{pcbnew.ToMM(fp.GetPosition().x):.2f}",
                'y_pos': f"{pcbnew.ToMM(fp.GetPosition().y):.2f}",
                'rotation': f"{fp.GetOrientationDegrees():.1f}°",
                'dnp': 'Yes' if 'DNP' in ref.upper() else 'No',
            }
            
            components.append(comp)
        
        return components
    
    def _get_footprint_name(self, fp):
        """Get clean footprint name."""
        fpid = fp.GetFPIDAsString()
        if ':' in fpid:
            return fpid.split(':')[-1]
        return fpid
    
    def _get_field(self, fp, field_name):
        """Get a field value from footprint."""
        try:
            # KiCad 9+ field access
            if hasattr(fp, 'GetFieldByName'):
                field = fp.GetFieldByName(field_name)
                if field:
                    return field.GetText()
            
            # Try properties (KiCad 9+)
            if hasattr(fp, 'GetProperties'):
                props = fp.GetProperties()
                if field_name in props:
                    return props[field_name]
        except:
            pass
        return ''
    
    def _group_components(self, components, group_by):
        """Group components by specified criteria."""
        if group_by == 'none':
            # No grouping - each component is its own group
            return {comp['reference']: [comp] for comp in components}
        
        grouped = {}
        
        for comp in components:
            if group_by == 'value_footprint':
                key = (comp['value'], comp['footprint'])
            elif group_by == 'value':
                key = comp['value']
            elif group_by == 'footprint':
                key = comp['footprint']
            else:
                key = comp['reference']
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(comp)
        
        return grouped
    
    def _sort_groups(self, grouped, sort_by):
        """Sort grouped components."""
        def sort_key(item):
            key, comps = item
            if sort_by == 'quantity':
                return -len(comps)  # Descending
            elif sort_by == 'value':
                if isinstance(key, tuple):
                    return key[0]
                return key
            elif sort_by == 'footprint':
                if isinstance(key, tuple):
                    return key[1]
                return key
            else:  # reference
                # Sort by first reference in group
                refs = sorted(comps, key=lambda c: self._ref_sort_key(c['reference']))
                return self._ref_sort_key(refs[0]['reference'])
        
        return sorted(grouped.items(), key=sort_key)
    
    def _ref_sort_key(self, ref):
        """Sort key for references (R1 < R2 < R10 < C1)."""
        import re
        match = re.match(r'([A-Za-z]+)(\d+)', ref)
        if match:
            prefix, num = match.groups()
            return (prefix, int(num))
        return (ref, 0)
    
    def _format_output(self, sorted_groups, config):
        """Format the BOM output."""
        columns = config.get('columns', ['reference', 'value', 'footprint', 'quantity'])
        table_style = config.get('table_style', 'markdown')
        include_headers = config.get('include_headers', True)
        
        # Column display names
        col_names = {
            'reference': 'Reference',
            'value': 'Value',
            'footprint': 'Footprint',
            'quantity': 'Qty',
            'description': 'Description',
            'manufacturer': 'Manufacturer',
            'mpn': 'MPN',
            'supplier': 'Supplier',
            'spn': 'SPN',
            'layer': 'Layer',
            'x_pos': 'X (mm)',
            'y_pos': 'Y (mm)',
            'rotation': 'Rotation',
            'dnp': 'DNP',
        }
        
        lines = ["## Bill of Materials", ""]
        
        # Build rows
        rows = []
        total_qty = 0
        
        for key, comps in sorted_groups:
            row = {}
            
            # Combine references
            refs = sorted([c['reference'] for c in comps], key=self._ref_sort_key)
            row['reference'] = ', '.join(refs)
            
            # Use first component for other fields
            first = comps[0]
            for col in columns:
                if col == 'reference':
                    continue  # Already handled
                elif col == 'quantity':
                    row['quantity'] = str(len(comps))
                else:
                    row[col] = first.get(col, '')
            
            rows.append(row)
            total_qty += len(comps)
        
        # Format based on style
        if table_style == 'markdown':
            lines.extend(self._format_markdown_table(columns, col_names, rows, include_headers))
        elif table_style == 'simple':
            lines.extend(self._format_simple_list(columns, col_names, rows))
        elif table_style == 'csv':
            lines.extend(self._format_csv(columns, col_names, rows, include_headers))
        
        # Summary
        lines.extend([
            "",
            f"**Total unique items:** {len(rows)}",
            f"**Total components:** {total_qty}",
            ""
        ])
        
        return '\n'.join(lines)
    
    def _format_markdown_table(self, columns, col_names, rows, include_headers):
        """Format as Markdown table."""
        lines = []
        
        if include_headers:
            # Header row
            header = '| ' + ' | '.join(col_names.get(c, c) for c in columns) + ' |'
            lines.append(header)
            
            # Separator
            sep = '|' + '|'.join('---' for _ in columns) + '|'
            lines.append(sep)
        
        # Data rows
        for row in rows:
            cells = [str(row.get(c, '')) for c in columns]
            lines.append('| ' + ' | '.join(cells) + ' |')
        
        return lines
    
    def _format_simple_list(self, columns, col_names, rows):
        """Format as simple list."""
        lines = []
        
        for row in rows:
            parts = []
            for col in columns:
                val = row.get(col, '')
                if val:
                    parts.append(f"{col_names.get(col, col)}: {val}")
            lines.append('- ' + ', '.join(parts))
        
        return lines
    
    def _format_csv(self, columns, col_names, rows, include_headers):
        """Format as CSV-style (for copy/paste to spreadsheet)."""
        lines = ["```csv"]
        
        if include_headers:
            lines.append(','.join(col_names.get(c, c) for c in columns))
        
        for row in rows:
            cells = [f'"{row.get(c, "")}"' if ',' in str(row.get(c, '')) else str(row.get(c, '')) for c in columns]
            lines.append(','.join(cells))
        
        lines.append("```")
        return lines


def show_bom_dialog(parent):
    """
    Show BOM configuration dialog and return generated BOM.
    
    Args:
        parent: Parent window
    
    Returns:
        Generated BOM string, or None if cancelled
    """
    dialog = BOMConfigDialog(parent)
    
    if dialog.ShowModal() == wx.ID_OK:
        config = dialog.get_config()
        generator = BOMGenerator()
        bom = generator.generate(config)
        dialog.Destroy()
        return bom
    
    dialog.Destroy()
    return None
