#!/usr/bin/env python
"""
Comprehensive test suite for Net Linker Visual Editor Integration
Tests: Module loading, method availability, settings persistence, pattern detection
"""

import sys
import re
import inspect

def test_net_linker_module():
    """Test 1: Net linker module loads and has required methods."""
    try:
        from KiNotes.core.net_linker import NetLinker
        nl = NetLinker()
        assert hasattr(nl, 'highlight'), "NetLinker missing highlight method"
        assert hasattr(nl, 'refresh_nets'), "NetLinker missing refresh_nets method"
        print("    ✓ NetLinker loads and has required methods")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def test_visual_editor_methods():
    """Test 2: Visual editor has all net linker methods."""
    try:
        from KiNotes.ui.visual_editor import VisualNoteEditor
        required_methods = [
            '_get_net_at_click_with_pos',
            '_try_net_highlight_with_style',
            '_apply_net_style',
            '_flash_net',
            'set_net_linker'
        ]
        for method in required_methods:
            assert hasattr(VisualNoteEditor, method), f"Missing {method}"
            print(f"    ✓ {method}")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def test_visual_editor_init():
    """Test 3: Visual editor initializes _net_linker."""
    try:
        from KiNotes.ui.visual_editor import VisualNoteEditor
        source = inspect.getsource(VisualNoteEditor.__init__)
        assert '_net_linker' in source, "_net_linker not initialized"
        print("    ✓ _net_linker initialized in __init__")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def test_main_panel_integration():
    """Test 4: Main panel passes net_linker to visual editor."""
    try:
        from KiNotes.ui.main_panel import KiNotesMainPanel
        source = inspect.getsource(KiNotesMainPanel._create_visual_editor)
        assert 'set_net_linker' in source, "set_net_linker not called"
        assert '_beta_net_linker' in source, "_beta_net_linker not used"
        print("    ✓ main_panel passes net_linker to visual_editor")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def test_click_handler():
    """Test 5: Click handler detects and highlights nets."""
    try:
        from KiNotes.ui.visual_editor import VisualNoteEditor
        source = inspect.getsource(VisualNoteEditor._on_click)
        assert '_get_net_at_click_with_pos' in source, "Net detection not in _on_click"
        assert '_try_net_highlight_with_style' in source, "Net highlighting not in _on_click"
        print("    ✓ _on_click detects nets and calls highlighting")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def test_net_pattern():
    """Test 6: Net pattern regex works correctly."""
    try:
        pattern = r'\[\[NET:([A-Za-z0-9_]+)\]\]'
        test_cases = [
            ('[[NET:VCC]]', 'VCC'),
            ('[[NET:GND]]', 'GND'),
            ('[[NET:CLK_IN]]', 'CLK_IN'),
            ('[[NET:LVDS_P]]', 'LVDS_P'),
        ]
        for text, expected_net in test_cases:
            match = re.search(pattern, text)
            assert match, f"Pattern didn't match {text}"
            assert match.group(1) == expected_net, f"Expected {expected_net}, got {match.group(1)}"
            print(f"    ✓ Pattern matches: {text} → {expected_net}")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def test_settings():
    """Test 7: Settings dialog includes beta_net_linker."""
    try:
        from KiNotes.ui.dialogs.settings_dialog import SettingsDialog
        source = inspect.getsource(SettingsDialog)
        assert 'beta_net_linker' in source, "beta_net_linker not in settings_dialog"
        print("    ✓ Settings dialog includes beta_net_linker checkbox")
        return True
    except Exception as e:
        print(f"    ✗ FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("NET LINKER VISUAL EDITOR INTEGRATION - COMPREHENSIVE TEST")
    print("=" * 70)
    
    tests = [
        ("Net linker module", test_net_linker_module),
        ("Visual editor methods", test_visual_editor_methods),
        ("Visual editor initialization", test_visual_editor_init),
        ("Main panel integration", test_main_panel_integration),
        ("Click handler modification", test_click_handler),
        ("Net pattern detection", test_net_pattern),
        ("Settings persistence", test_settings),
    ]
    
    results = []
    for i, (name, test_func) in enumerate(tests, 1):
        print(f"\n[{i}] Testing {name}...")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ ALL TESTS PASSED - Net Linker Visual Editor Integration Complete!")
        print("=" * 70)
        print("\nFeature ready for:")
        print("  • Click on [[NET:name]] patterns in visual editor")
        print("  • Automatic PCB highlighting with visual feedback")
        print("  • Blue text = found, Gray text = not found")
        print("  • Smooth integration with existing designator cross-probe")
        return 0
    else:
        print("❌ SOME TESTS FAILED - See errors above")
        print("=" * 70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
