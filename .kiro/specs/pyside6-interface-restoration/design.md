# Design Document

## Overview

This design document outlines the technical approach to restore the PySide6 interface to its pre-widget-activation state. The restoration will revert the main window layout to the original 3-tab structure with left-side panels (Rubric, Report, Report Outputs) and right-side Chat/Analysis window, while preserving all current functionality including the newly added Mission Control, Meta Analytics, and Performance Status widgets.

## Architecture

### High-Level Approach

The restoration will follow these principles:

1. **Minimal Code Changes**: Modify only the UI layout code, not the business logic or backend services
2. **Feature Preservation**: All existing functionality remains accessible through the restored interface
3. **Widget Relocation**: New widgets (Mission Control, Meta Analytics, Performance Status) will be made accessible via menu items or dock widgets rather than main tabs
4. **Backward Compatibility**: Maintain compatibility with existing configuration and user preferences

### Component Structure

```
MainApplicationWindow (QMainWindow)
├── Menu Bar
│   ├── File Menu
│   ├── Tools Menu (with Meta Analytics, Performance Status)
│   ├── Theme Menu
│   └── Help Menu
├── Tab Widget (4 tabs)
│   ├── Analysis Tab
│   │   ├── Left Panel (QSplitter - vertical)
│   │   │   ├── Rubric Selection Widget
│   │   │   ├── Report Preview Widget
│   │   │   └── Report Outputs Widget
│   │   └── Right Panel
│   │       └── Chat/Analysis Widget (QStackedWidget or QTabWidget)
│   ├── Dashboard Tab
│   │   └── Dashboard Widget (existing)
│   ├── Mission Control Tab
│   │   └── Mission Control Widget (existing)
│   └── Settings Tab
│       └── Settings Widget
├── Status Bar
└── Optional Dock Widgets
    ├── Meta Analytics (dockable)
    └── Performance Status (dockable)
```

## Components and Interfaces

### 1. MainApplicationWindow Modifications

**Current State Analysis:**
- The current `main_window.py` uses a ViewModel pattern with background workers
- It likely has additional tabs or a different layout structure due to widget activation
- The core functionality (analysis, dashboard, workers) is intact

**Required Changes:**
- Restore the `_setup_ui()` method to create a 4-tab layout
- Create tabs for Analysis, Dashboard, Mission Control, and Settings
- Restructure the Analysis tab to use a horizontal splitter with left (3 panels) and right (chat/analysis) sections
- Add Mission Control as a full tab
- Move Meta Analytics and Performance Status to Tools menu as dock widgets

### 2. Analysis Tab Layout

**Left Panel Structure (QSplitter - Vertical):**

```python
left_splitter = QSplitter(Qt.Vertical)

# Top: Rubric Selection Panel
rubric_panel = QWidget()
rubric_layout = QVBoxLayout()
rubric_layout.addWidget(QLabel("Select Rubric"))
rubric_layout.addWidget(self.rubric_combo)  # Existing combo box
rubric_layout.addWidget(self.upload_button)  # Document upload
rubric_panel.setLayout(rubric_layout)

# Middle: Report Preview Panel
report_preview_panel = QWidget()
report_preview_layout = QVBoxLayout()
report_preview_layout.addWidget(QLabel("Report Preview"))
report_preview_layout.addWidget(self.report_browser)  # QTextBrowser
report_preview_panel.setLayout(report_preview_layout)

# Bottom: Report Outputs Panel
report_outputs_panel = QWidget()
report_outputs_layout = QVBoxLayout()
report_outputs_layout.addWidget(QLabel("Report Outputs"))
report_outputs_layout.addWidget(self.outputs_list)  # QListWidget
report_outputs_panel.setLayout(report_outputs_layout)

left_splitter.addWidget(rubric_panel)
left_splitter.addWidget(report_preview_panel)
left_splitter.addWidget(report_outputs_panel)
```

**Right Panel Structure:**

```python
right_panel = QWidget()
right_layout = QVBoxLayout()

# Tab widget or stacked widget for Chat/Analysis
chat_analysis_tabs = QTabWidget()
chat_analysis_tabs.addTab(self.analysis_widget, "Analysis")
chat_analysis_tabs.addTab(self.chat_widget, "Chat")

right_layout.addWidget(chat_analysis_tabs)
right_panel.setLayout(right_layout)
```

**Main Splitter:**

```python
main_splitter = QSplitter(Qt.Horizontal)
main_splitter.addWidget(left_splitter)
main_splitter.addWidget(right_panel)
main_splitter.setStretchFactor(0, 1)  # Left panel
main_splitter.setStretchFactor(1, 2)  # Right panel (larger)
```

### 3. Dashboard Tab

**No Changes Required:**
- The existing `DashboardWidget` will remain as-is
- Simply ensure it's added as the second tab in the main tab widget

### 4. Mission Control Tab

**Implementation:**
- Add Mission Control as the third tab in the main tab widget
- Use the existing `MissionControlWidget` directly
- No wrapper or modification needed - full widget display
- Maintains all current features:
  - Task monitoring and management
  - Log viewing and filtering
  - Settings editing
  - System status indicators

### 5. Settings Tab

**Implementation:**
- Create a new `SettingsTabWidget` that consolidates all settings
- Include sections for:
  - User preferences (theme, notifications)
  - Performance settings (cache, memory limits)
  - Analysis settings (default rubric, batch options)
  - Advanced settings (API configuration, logging)

**Alternative:**
- If a Settings tab didn't exist before, use the existing `SettingsDialog` accessible via menu

### 6. New Widget Integration (Meta Analytics and Performance Status)

**Mission Control Widget:**
- **Access Method**: Main tab (third tab)
- **Display**: Full tab display
- **Functionality**: Maintains all current features (task monitoring, log viewing, settings editing)

**Meta Analytics Widget:**
- **Access Method**: Tools → Meta Analytics (menu item)
- **Display**: Opens as a dockable widget or separate dialog
- **Functionality**: Maintains all current analytics and visualization features

**Performance Status Widget:**
- **Access Method**: Tools → Performance Status (menu item) or status bar indicator
- **Display**: Opens as a dockable widget, popup, or embedded in status bar
- **Functionality**: Maintains all current performance monitoring features

## Data Models

### UI State Persistence

**QSettings Keys:**
```python
# Window geometry
"window/geometry"
"window/state"

# Splitter positions
"analysis/left_splitter_sizes"
"analysis/main_splitter_sizes"

# Tab preferences
"ui/last_active_tab"

# Dock widget states (for new widgets)
"docks/mission_control_visible"
"docks/meta_analytics_visible"
"docks/performance_status_visible"
"docks/mission_control_geometry"
"docks/meta_analytics_geometry"
"docks/performance_status_geometry"
```

### Widget State Management

The existing `MainViewModel` will continue to manage:
- API status and health checks
- Task monitoring
- Log streaming
- Rubric loading
- Dashboard data
- Meta analytics data

No changes required to the ViewModel pattern.

## Error Handling

### Layout Restoration Errors

**Scenario**: Saved splitter sizes are invalid or missing
- **Handling**: Use default sizes (e.g., left panel 30%, right panel 70%)
- **User Feedback**: Silent fallback, no error message needed

**Scenario**: Widget initialization fails
- **Handling**: Log error, display placeholder widget with error message
- **User Feedback**: Show message in status bar: "Failed to load [widget name]"

**Scenario**: Dock widget state restoration fails
- **Handling**: Reset to default positions
- **User Feedback**: Silent fallback

### Feature Compatibility

**Scenario**: New widgets fail to load
- **Handling**: Disable menu items for unavailable widgets
- **User Feedback**: Menu items show as disabled with tooltip explaining why

## Testing Strategy

### Unit Tests

1. **Test UI Component Creation**
   - Verify 3 tabs are created (Analysis, Dashboard, Settings)
   - Verify left panel has 3 sub-panels
   - Verify right panel contains chat/analysis widget
   - Verify splitter ratios are correct

2. **Test Widget Integration**
   - Verify Mission Control can be opened from menu
   - Verify Meta Analytics can be opened from menu
   - Verify Performance Status can be opened from menu
   - Verify dock widgets can be docked/undocked

3. **Test State Persistence**
   - Verify splitter positions are saved and restored
   - Verify dock widget positions are saved and restored
   - Verify last active tab is remembered

### Integration Tests

1. **Test Analysis Workflow**
   - Upload document → Select rubric → Run analysis → View results
   - Verify all steps work with restored layout

2. **Test Dashboard Workflow**
   - Switch to Dashboard tab → View analytics → Refresh data
   - Verify dashboard functionality is intact

3. **Test New Widget Workflows**
   - Open Mission Control → Monitor tasks → View logs
   - Open Meta Analytics → View trends → Filter data
   - Open Performance Status → Check metrics

### Manual Testing Checklist

- [ ] Application launches with 3-tab layout
- [ ] Left panel shows Rubric, Report, Report Outputs
- [ ] Right panel shows Chat/Analysis
- [ ] Document upload and analysis works
- [ ] Dashboard displays correctly
- [ ] Settings tab/dialog is accessible
- [ ] Mission Control opens from menu
- [ ] Meta Analytics opens from menu
- [ ] Performance Status opens from menu
- [ ] All themes apply correctly
- [ ] Window geometry persists across restarts
- [ ] Splitter positions persist across restarts

## Implementation Plan

### Phase 1: Backup and Analysis
1. Create backup of current `main_window.py`
2. Analyze current layout structure
3. Identify all widgets and their current locations
4. Document current functionality

### Phase 2: Layout Restoration
1. Modify `_setup_ui()` method to create 3-tab structure
2. Implement left panel with 3 sub-panels
3. Implement right panel with chat/analysis
4. Remove or relocate new widget tabs

### Phase 3: Widget Relocation
1. Add menu items for Mission Control, Meta Analytics, Performance Status
2. Implement dock widget functionality for new widgets
3. Connect menu items to widget display logic

### Phase 4: State Persistence
1. Implement QSettings save/restore for splitter positions
2. Implement QSettings save/restore for dock widget states
3. Implement QSettings save/restore for last active tab

### Phase 5: Testing and Refinement
1. Run unit tests
2. Run integration tests
3. Perform manual testing
4. Fix any issues discovered
5. Optimize performance if needed

## Migration Strategy

### User Experience

**First Launch After Restoration:**
1. Application opens with restored 3-tab layout
2. If user had Mission Control/Meta Analytics/Performance Status open, show notification:
   - "Interface layout has been restored. Access Mission Control, Meta Analytics, and Performance Status from the Tools menu."
3. User preferences and settings are preserved

**Rollback Plan:**
- Keep backup of current `main_window.py` in `src/gui/archive/`
- Document rollback procedure in case issues arise
- Provide configuration option to switch between layouts if needed

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Load dock widgets only when accessed from menu
2. **Widget Caching**: Cache created dock widgets to avoid recreation
3. **Efficient Layouts**: Use QSplitter for responsive resizing without performance overhead
4. **Background Loading**: Continue using existing worker pattern for data loading

### Memory Management

- Dock widgets should be properly deleted when closed (if not cached)
- Ensure no memory leaks from widget creation/destruction
- Monitor memory usage during testing

## Security Considerations

- No security implications as this is purely a UI layout change
- All existing security measures (JWT auth, PHI scrubbing, local processing) remain unchanged
- No new data storage or transmission introduced

## Accessibility

- Maintain keyboard navigation support
- Ensure all widgets are accessible via keyboard shortcuts
- Preserve screen reader compatibility
- Maintain high contrast theme support

## Future Enhancements

### Potential Improvements

1. **Layout Profiles**: Allow users to save and switch between different layout configurations
2. **Customizable Panels**: Let users rearrange panels via drag-and-drop
3. **Floating Widgets**: Allow any panel to be detached as a floating window
4. **Multi-Monitor Support**: Remember widget positions across multiple monitors
5. **Quick Access Toolbar**: Add customizable toolbar for frequently used features
