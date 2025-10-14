# GUI Refactoring Implementation Plan

## 🎯 Objectives

1. **Remove "View Report" button** - Report should display inline, not require popup
2. **Reset document state** after analysis - Allow immediate next analysis
3. **Fix button overlaps** - Responsive layout that adapts to window resize
4. **Dark mode completion** - PyCharm-style colors, no light elements
5. **Status bar with health monitoring** - RAM/CPU/API status + Easter egg
6. **Enhanced strictness description** - Detailed criteria for each level
7. **Integrate new threading architecture** - Replace old workers with BaseWorker-based

---

## 📋 Task Breakdown

### **Task 1: Remove View Report Button** ✅
**Files:**
- `src/gui/components/analysis_tab_builder.py` (lines 626-631)
- `src/gui/main_window.py` (line 129)
- `src/gui/handlers/ui_handlers.py` (method `open_report_popup`)

**Changes:**
1. Remove `view_report_button` creation in `AnalysisTabBuilder._create_action_buttons_section()`
2. Remove attribute initialization in `MainApplicationWindow._initialize_ui_attributes()`
3. Remove/deprecate `UIHandlers.open_report_popup()` method
4. Ensure report displays inline in `analysis_summary_browser` or `detailed_results_browser`

**Rationale:**
- Inline display is more intuitive
- Reduces clicks
- Better UX flow

---

### **Task 2: Reset Document State After Analysis** ✅
**Files:**
- `src/gui/handlers/analysis_handlers.py`
- `src/gui/components/analysis_tab_builder.py`

**Changes:**
1. After analysis completes, add logic to:
   - Clear `file_display` text edit
   - Reset `run_analysis_button` state
   - Enable `open_file_button` 
   - Set status to "Ready for next analysis"
   - Clear `_selected_file` reference

**Implementation:**
```python
def _on_analysis_complete(self, result):
    # Display results
    self._display_results(result)
    
    # Reset for next analysis
    self._reset_document_state()

def _reset_document_state(self):
    """Reset UI state for next document analysis."""
    if self.file_display:
        self.file_display.clear()
        self.file_display.setPlaceholderText("Click 'Open File' to select a new document")
    
    self._selected_file = None
    
    if self.run_analysis_button:
        self.run_analysis_button.setEnabled(False)
    
    if self.open_file_button:
        self.open_file_button.setEnabled(True)
    
    self.statusBar().showMessage("Ready for next analysis", 3000)
```

---

### **Task 3: Fix Button Overlaps - Responsive Layout** ✅
**Files:**
- `src/gui/components/analysis_tab_builder.py`
- `src/gui/main_window.py`

**Problem:**
- Fixed-size buttons overlap when window resized
- No minimum sizes on containers
- Poor stretch factors

**Solution:**
1. Use `QSizePolicy` to make buttons respect parent constraints
2. Add minimum/maximum sizes
3. Use `QScrollArea` for overflow handling
4. Set proper stretch factors on layouts

**Code Pattern:**
```python
# In button creation
button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
button.setMinimumHeight(42)
button.setMaximumHeight(50)

# In layout
layout.setContentsMargins(10, 10, 10, 10)
layout.setSpacing(8)
layout.addStretch()  # Add stretch at end
```

---

### **Task 4: Complete Dark Mode** ✅
**Files:**
- `src/gui/widgets/medical_theme.py`
- `src/gui/main_window.py`
- All component files

**Requirements:**
- **Base color**: `#2B2B2B` (PyCharm dark grey)
- **Text color**: `#A9B7C6` (PyCharm light grey)
- **Accent**: `#4A9FD8` (PyCharm blue)
- **Error**: `#FF6B68`
- **Success**: `#6A8759`
- **Border**: `#323232`

**Remove:**
- All white/light backgrounds
- Light grey elements
- Bright status dots

**Status Indicators:**
- Use button-icon lighting only (green/red glow)
- No status dots
- Subtle animations

**Stylesheet Update:**
```python
PYCHARM_DARK = {
    'background': '#2B2B2B',
    'foreground': '#A9B7C6',
    'accent': '#4A9FD8',
    'error': '#FF6B68',
    'success': '#6A8759',
    'warning': '#FFC66D',
    'border': '#323232',
    'hover': '#3A3A3A',
    'selected': '#214283',
    'scrollbar': '#4D4D4D',
}
```

---

### **Task 5: Health Status Bar** ✅
**Files:**
- `src/gui/components/status_bar_builder.py` (new)
- `src/gui/main_window.py`

**Features:**
1. **RAM Usage**: Icon + percentage + bar
2. **CPU Usage**: Icon + percentage + bar
3. **API Status**: Green/red icon (no dot!)
4. **Active Tasks**: Count
5. **Easter Egg**: "Pacific Coast Therapy" in cursive font (bottom right)

**Layout:**
```
[RAM: 45% ▓▓▓░░░] [CPU: 23% ▓▓░░░░] [API: ●] [Tasks: 2]                    Pacific Coast Therapy
```

**Implementation:**
```python
class HealthStatusBar(QStatusBar):
    def __init__(self, resource_monitor):
        super().__init__()
        self.resource_monitor = resource_monitor
        
        # RAM widget
        self.ram_widget = QLabel()
        self.addWidget(self.ram_widget)
        
        # CPU widget
        self.cpu_widget = QLabel()
        self.addWidget(self.cpu_widget)
        
        # API status
        self.api_widget = QLabel()
        self.addWidget(self.api_widget)
        
        # Tasks
        self.tasks_widget = QLabel()
        self.addWidget(self.tasks_widget)
        
        # Easter egg (permanent widget on right)
        self.easter_egg = QLabel("Pacific Coast Therapy")
        self.easter_egg.setStyleSheet("font-family: 'Brush Script MT', cursive; color: #4A9FD8;")
        self.addPermanentWidget(self.easter_egg)
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_health)
        self.timer.start(1000)
    
    def _update_health(self):
        metrics = self.resource_monitor.get_current_metrics()
        
        # Update RAM
        ram_bar = self._create_mini_bar(metrics.ram_percent)
        self.ram_widget.setText(f"RAM: {metrics.ram_percent:.0f}% {ram_bar}")
        
        # Update CPU
        cpu_bar = self._create_mini_bar(metrics.cpu_percent)
        self.cpu_widget.setText(f"CPU: {metrics.cpu_percent:.0f}% {cpu_bar}")
    
    def _create_mini_bar(self, percent):
        """Create ASCII progress bar."""
        filled = int(percent / 20)  # 5 blocks max
        return "▓" * filled + "░" * (5 - filled)
```

---

### **Task 6: Enhanced Strictness Description** ✅
**Files:**
- `src/gui/components/analysis_tab_builder.py`
- `src/core/compliance_analyzer.py` (fetch criteria)

**Current:**
- Single sentence description

**New:**
- **Heading**: Level name (e.g., "Strict")
- **Compliance Threshold**: e.g., "90% required"
- **Word Count**: e.g., "Minimum 500 words"
- **Error Tolerance**: e.g., "Max 2 critical errors"
- **Scoring Logic**: Explanation of how score is calculated
- **Use Cases**: When to use this level

**Layout:**
```markdown
### Strict (90% threshold)
**Compliance Threshold:** 90% score required to pass
**Word Count Requirement:** Minimum 500 words
**Error Tolerance:** Maximum 2 critical errors, 5 warnings
**Scoring Logic:** Weighted average of all compliance criteria with penalties for missing required sections
**Use Cases:** 
- Billing/insurance submissions
- Legal documentation
- High-risk cases
**Why Strict:** Ensures all regulatory requirements met to avoid denials or legal issues
```

**Implementation:**
```python
STRICTNESS_CRITERIA = {
    "lenient": {
        "name": "Lenient",
        "threshold": 70,
        "min_words": 200,
        "max_critical_errors": 5,
        "max_warnings": 10,
        "scoring": "Basic compliance check, focuses on essential elements only",
        "use_cases": ["Quick notes", "Internal documentation", "Progress tracking"],
        "why": "Fast turnaround for routine documentation with lower risk"
    },
    "balanced": {
        "name": "Balanced",
        "threshold": 80,
        "min_words": 350,
        "max_critical_errors": 3,
        "max_warnings": 7,
        "scoring": "Standard compliance check with moderate rigor",
        "use_cases": ["Standard therapy notes", "Regular assessments", "Treatment plans"],
        "why": "Best balance of thoroughness and efficiency for routine clinical work"
    },
    "strict": {
        "name": "Strict",
        "threshold": 90,
        "min_words": 500,
        "max_critical_errors": 2,
        "max_warnings": 5,
        "scoring": "Comprehensive compliance check with all criteria weighted",
        "use_cases": ["Billing submissions", "Legal documentation", "High-risk cases"],
        "why": "Ensures full regulatory compliance to avoid denials or legal issues"
    },
}
```

---

### **Task 7: Integrate New Threading Architecture** ✅
**Files:**
- Replace: `src/gui/workers/analysis_worker.py` → Use `analysis_worker_v2.py`
- Update: `src/gui/view_models/main_view_model.py`
- Update: All worker instantiations

**Changes:**
1. Replace old `AnalysisWorker` with new `BaseWorker`-based version
2. Add `ResourceMonitor` to `MainViewModel`
3. Connect new signals (progress, error, resource_warning, etc.)
4. Remove old worker cleanup code (handled by `BaseWorker`)

**Migration:**
```python
# OLD
from src.gui.workers.analysis_worker import AnalysisWorker

worker = AnalysisWorker(file_path, strictness)
worker.started.connect(on_started)
# ... manual cleanup

# NEW
from src.gui.workers.analysis_worker_v2 import AnalysisWorker
from src.gui.core import ResourceMonitor

self.resource_monitor = ResourceMonitor()
self.resource_monitor.start_monitoring()

worker = AnalysisWorker(
    file_path=file_path,
    api_client=self.api_client,
    strictness=strictness,
    resource_monitor=self.resource_monitor
)
worker.signals.progress.connect(self.update_progress)
worker.signals.result.connect(self.on_complete)
worker.signals.error.connect(self.on_error)
worker.signals.resource_warning.connect(self.on_resource_warning)
# Cleanup automatic!
```

---

## 📊 Implementation Order

1. ✅ **Health Status Bar** (foundational, visible immediately)
2. ✅ **Dark Mode Completion** (polish all UI)
3. ✅ **Enhanced Strictness Description** (better UX)
4. ✅ **Fix Button Overlaps** (responsive layout)
5. ✅ **Remove View Report Button** (simplify)
6. ✅ **Reset Document State** (better workflow)
7. ✅ **Integrate New Threading** (stability)

---

## ✅ Success Criteria

- [ ] No "View Report" button visible
- [ ] Report displays inline after analysis
- [ ] Document input clears after analysis completes
- [ ] "Open File" button re-enabled after analysis
- [ ] All buttons resize correctly with window
- [ ] No overlap at any window size (minimum 800x600)
- [ ] All UI elements use PyCharm dark theme
- [ ] No light/white backgrounds anywhere
- [ ] Status indicators use icon lighting (no dots)
- [ ] Health status bar shows RAM/CPU/API status
- [ ] "Pacific Coast Therapy" visible in bottom right (cursive)
- [ ] Strictness description shows all criteria details
- [ ] Analysis uses new `BaseWorker` architecture
- [ ] GUI never freezes during analysis
- [ ] Resource warnings appear when RAM/CPU high
- [ ] All errors caught and displayed gracefully

---

**Status:** Ready to implement
**Est. Time:** ~2-3 hours for complete implementation
**Priority:** HIGH - User-facing improvements

