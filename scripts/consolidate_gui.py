#!/usr/bin/env python3
"""
GUI Consolidation Script
Helps migrate from multiple main window implementations to the unified version.
"""

import shutil
from pathlib import Path
from datetime import datetime

def backup_old_implementations():
    """Backup old main window implementations."""
    gui_dir = Path("src/gui")
    backup_dir = Path("src/gui/archive") / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    old_files = [
        "main_window_enhanced.py",
        "main_window_fixed.py", 
        "main_window_modern.py",
        "main_window_ultimate.py",
        "main_window_working.py"
    ]
    
    print("🔄 Backing up old main window implementations...")
    
    for file_name in old_files:
        file_path = gui_dir / file_name
        if file_path.exists():
            backup_path = backup_dir / file_name
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ Backed up: {file_name}")
    
    print(f"📁 Backup created at: {backup_dir}")
    return backup_dir

def analyze_implementations():
    """Analyze existing implementations for unique features."""
    gui_dir = Path("src/gui")
    implementations = [
        "main_window.py",
        "main_window_enhanced.py", 
        "main_window_fixed.py",
        "main_window_modern.py",
        "main_window_ultimate.py",
        "main_window_working.py"
    ]
    
    print("\n📊 Analyzing existing implementations...")
    
    analysis = {}
    
    for impl in implementations:
        file_path = gui_dir / impl
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            analysis[impl] = {
                'lines': len(content.splitlines()),
                'classes': content.count('class '),
                'methods': content.count('def '),
                'has_easter_eggs': 'easter' in content.lower() or 'konami' in content.lower(),
                'has_themes': 'theme' in content.lower() and 'dark' in content.lower(),
                'has_chat': 'chat' in content.lower(),
                'has_dashboard': 'dashboard' in content.lower(),
                'has_ai_status': 'ai' in content.lower() and 'status' in content.lower()
            }
    
    # Print analysis
    for impl, data in analysis.items():
        print(f"\n   📄 {impl}:")
        print(f"      Lines: {data['lines']}")
        print(f"      Classes: {data['classes']}")
        print(f"      Methods: {data['methods']}")
        print("      Features: ", end="")
        features = []
        if data['has_easter_eggs']:
            features.append("Easter Eggs")
        if data['has_themes']:
            features.append("Themes")
        if data['has_chat']:
            features.append("Chat")
        if data['has_dashboard']:
            features.append("Dashboard")
        if data['has_ai_status']:
            features.append("AI Status")
        print(", ".join(features) if features else "Basic")
    
    return analysis

def create_migration_plan():
    """Create a migration plan."""
    print("\n📋 MIGRATION PLAN")
    print("=" * 50)
    
    plan = [
        "1. ✅ Created unified main window (main_window_unified.py)",
        "2. ✅ Updated run_gui.py to use unified implementation", 
        "3. 🔄 Backup old implementations (running now)",
        "4. ⏳ Test unified implementation",
        "5. ⏳ Remove old implementations after verification",
        "6. ⏳ Update documentation and imports"
    ]
    
    for step in plan:
        print(f"   {step}")
    
    print("\n💡 BENEFITS OF UNIFIED APPROACH:")
    benefits = [
        "Single source of truth for main window logic",
        "Easier maintenance and bug fixes",
        "Consistent user experience",
        "Reduced code duplication",
        "Cleaner project structure",
        "Better performance (no duplicate loading)"
    ]
    
    for benefit in benefits:
        print(f"   • {benefit}")

def verify_unified_implementation():
    """Verify the unified implementation has all necessary components."""
    unified_path = Path("src/gui/main_window_unified.py")
    
    if not unified_path.exists():
        print("❌ Unified implementation not found!")
        return False
    
    with open(unified_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_components = {
        'UnifiedMainWindow class': 'class UnifiedMainWindow',
        'Theme support': 'apply_theme',
        'AI model status': 'AIModelStatusWidget',
        'Easter eggs': 'EasterEggManager',
        'Analysis functionality': 'run_analysis',
        'Chat integration': 'open_chat',
        'Dashboard': 'dashboard_tab',
        'Settings': 'settings_tab'
    }
    
    print("\n🔍 Verifying unified implementation...")
    
    all_present = True
    for component, search_term in required_components.items():
        if search_term in content:
            print(f"   ✅ {component}")
        else:
            print(f"   ❌ {component} - MISSING")
            all_present = False
    
    return all_present

def main():
    """Main consolidation function."""
    print("🏥 THERAPY COMPLIANCE ANALYZER - GUI CONSOLIDATION")
    print("=" * 60)
    
    # Analyze current implementations
    analysis = analyze_implementations()
    if not analysis:
        print("\nNo GUI implementations found to analyze.")
        return

    # Create migration plan
    create_migration_plan()
    
    # Verify unified implementation
    if verify_unified_implementation():
        print("\n✅ Unified implementation verification passed!")
    else:
        print("\n❌ Unified implementation needs attention!")
        return
    
    # Backup old implementations
    backup_dir = backup_old_implementations()
    
    print("\n🎉 CONSOLIDATION COMPLETE!")
    print("\nNEXT STEPS:")
    print("1. Test the unified implementation: python run_gui.py")
    print("2. Verify all features work correctly")
    print("3. Remove old implementations if everything works")
    print(f"4. Old files are backed up in: {backup_dir}")
    
    print("\n📝 TESTING CHECKLIST:")
    checklist = [
        "Application starts without errors",
        "Document upload works",
        "Analysis runs successfully", 
        "Dashboard displays correctly",
        "Chat dialog opens",
        "Theme switching works",
        "Easter eggs function (Konami code)",
        "All menus and buttons respond",
        "Status indicators update properly"
    ]
    
    for item in checklist:
        print(f"   □ {item}")

if __name__ == "__main__":
    main()