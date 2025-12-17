"""
Fab Import Selection Dialog - Simple checkbox selection.
"""
import wx


# Section options: (key, label)
FAB_SECTIONS = [
    ('board_size', 'Board Size'),
    ('board_finish', 'Board Finish'),
    ('track_analysis', 'Actual Track Analysis'),
    ('drill_table', 'Drill Table'),
    ('design_rules', 'Design Rules'),
    ('fab_checklist', 'Fab Capability Checklist'),
]


def show_fab_import_dialog(parent, dark_mode=False):
    """Show multi-choice dialog for fab section selection."""
    choices = [label for _, label in FAB_SECTIONS]
    
    # Default selections (all except design_rules)
    defaults = [0, 1, 2, 3, 5]  # indices
    
    dlg = wx.MultiChoiceDialog(
        parent,
        "Select sections to import:",
        "Fab Summary Import",
        choices
    )
    dlg.SetSelections(defaults)
    
    if dlg.ShowModal() == wx.ID_OK:
        indices = dlg.GetSelections()
        dlg.Destroy()
        return [FAB_SECTIONS[i][0] for i in indices]  # Return keys
    
    dlg.Destroy()
    return None

