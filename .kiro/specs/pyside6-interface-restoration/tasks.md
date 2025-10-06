# Implementation Plan

- [x] 1. Backup and analyze current implementation


  - Create backup of current main_window.py to archive folder
  - Document current widget structure and layout
  - Identify all UI components that need to be preserved
  - Map current functionality to restored layout
  - _Requirements: 1.1, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_





- [ ] 2. Create main window tab structure
  - [ ] 2.1 Modify _setup_ui() to create QTabWidget with exactly 4 tabs
    - Remove any additional tabs added by widget activation
    - Create Analysis tab container
    - Create Dashboard tab container

    - Create Mission Control tab container

    - Create Settings tab container
    - Set appropriate tab icons and tooltips
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_


- [ ] 3. Implement Analysis tab left panel layout
  - [ ] 3.1 Create vertical QSplitter for left panel
    - Initialize QSplitter with Qt.Vertical orientation
    - Set appropriate size policies
    - _Requirements: 2.1, 2.2_
  
  - [ ] 3.2 Create Rubric selection panel (top)
    - Create QWidget container with QVBoxLayout

    - Add "Select Rubric" label
    - Add rubric combo box (preserve existing functionality)
    - Add document upload button
    - Add "Run Analysis" button
    - Connect signals to existing handlers
    - _Requirements: 2.2, 2.5, 4.1, 4.3_
  

  - [ ] 3.3 Create Report preview panel (middle)
    - Create QWidget container with QVBoxLayout
    - Add "Report Preview" label
    - Add QTextBrowser for report display
    - Connect to existing report generation logic
    - Preserve HTML rendering and interactive features
    - _Requirements: 2.3, 2.5, 4.1, 4.7_

  
  - [ ] 3.4 Create Report outputs panel (bottom)
    - Create QWidget container with QVBoxLayout
    - Add "Report Outputs" label

    - Add QListWidget for output history

    - Connect to existing analysis results
    - Add context menu for export/delete actions
    - _Requirements: 2.4, 2.5, 4.1, 4.7_
  

  - [ ] 3.5 Assemble left panel components
    - Add all three panels to vertical splitter
    - Set initial splitter sizes (30%, 40%, 30%)
    - Configure stretch factors
    - _Requirements: 2.1, 2.2, 2.3, 2.4_


- [ ] 4. Implement Analysis tab right panel layout
  - [ ] 4.1 Create Chat/Analysis container
    - Create QWidget container with QVBoxLayout
    - Decide between QTabWidget or QStackedWidget approach

    - _Requirements: 3.1, 3.2_
  
  - [ ] 4.2 Integrate analysis results widget
    - Add existing analysis display widget to right panel

    - Preserve progress indicators and status messages

    - Maintain interactive report features (highlighting, links)
    - _Requirements: 3.2, 3.4, 4.1_
  
  - [ ] 4.3 Integrate chat widget
    - Add existing ChatDialog or chat widget to right panel
    - Preserve chat history and context
    - Maintain AI assistance functionality

    - _Requirements: 3.2, 3.3, 4.4_
  
  - [ ] 4.4 Add toggle mechanism between chat and analysis
    - Implement tab switching or stacked widget navigation

    - Add keyboard shortcuts for quick switching

    - Preserve state when switching views
    - _Requirements: 3.4_

- [ ] 5. Assemble Analysis tab main layout
  - [ ] 5.1 Create horizontal QSplitter for main layout
    - Initialize QSplitter with Qt.Horizontal orientation

    - Add left panel (3 vertical panels)
    - Add right panel (chat/analysis)
    - Set initial sizes (30% left, 70% right)
    - Configure stretch factors
    - _Requirements: 2.1, 3.1_
  
  - [x] 5.2 Set Analysis tab as main widget

    - Add horizontal splitter to Analysis tab
    - Set appropriate margins and spacing
    - Apply theme styling
    - _Requirements: 1.2_

- [x] 6. Implement Dashboard tab

  - [ ] 6.1 Integrate existing DashboardWidget
    - Add DashboardWidget to Dashboard tab container
    - Preserve all analytics and visualization features
    - Maintain data refresh functionality
    - Connect to existing ViewModel signals

    - _Requirements: 1.3, 4.2_

- [ ] 7. Implement Mission Control tab
  - [ ] 7.1 Integrate existing MissionControlWidget
    - Add MissionControlWidget to Mission Control tab container

    - Preserve all task monitoring features
    - Preserve log viewing and filtering functionality
    - Preserve settings editing capabilities
    - Connect to existing ViewModel signals
    - _Requirements: 1.4, 5.1, 5.5, 5.6_


- [ ] 8. Implement Settings tab
  - [ ] 7.1 Create Settings tab widget
    - Create QWidget container with QVBoxLayout

    - Add QTabWidget for settings categories
    - _Requirements: 1.4_

  
  - [ ] 8.2 Add User Preferences section
    - Theme selection (light/dark)
    - Notification preferences
    - UI customization options

    - _Requirements: 4.6, 7.1, 7.2_
  
  - [ ] 8.3 Add Performance Settings section
    - Cache configuration
    - Memory limits
    - Background worker settings

    - _Requirements: 4.6, 8.1, 8.2_
  
  - [x] 8.4 Add Analysis Settings section

    - Default rubric selection
    - Batch processing options
    - Auto-save preferences

    - _Requirements: 4.6, 7.2_
  
  - [ ] 8.5 Connect settings to existing configuration system
    - Wire settings changes to QSettings persistence
    - Apply settings changes immediately where appropriate

    - Add "Apply" and "Reset" buttons
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 9. Relocate Meta Analytics widget
  - [ ] 9.1 Create Tools menu item for Meta Analytics
    - Add "Meta Analytics" action to Tools menu

    - Set keyboard shortcut (e.g., Ctrl+Shift+A)
    - Add icon and tooltip

    - _Requirements: 5.2, 5.4_
  
  - [ ] 9.2 Implement Meta Analytics as dockable widget
    - Create QDockWidget wrapper for MetaAnalyticsWidget

    - Set dock area to Qt.BottomDockWidgetArea by default
    - Allow docking to any edge
    - Enable floating mode
    - _Requirements: 5.2, 5.4_
  

  - [ ] 9.3 Connect menu action to dock widget
    - Show/hide dock widget when menu item clicked
    - Toggle checked state of menu action
    - Preserve dock widget state across sessions
    - _Requirements: 5.2, 5.5_


- [ ] 10. Relocate Performance Status widget
  - [ ] 10.1 Create Tools menu item for Performance Status
    - Add "Performance Status" action to Tools menu
    - Set keyboard shortcut (e.g., Ctrl+Shift+P)
    - Add icon and tooltip
    - _Requirements: 5.3, 5.4_


  

  - [ ] 10.2 Implement Performance Status as dockable widget
    - Create QDockWidget wrapper for PerformanceStatusWidget
    - Set dock area to Qt.RightDockWidgetArea by default
    - Allow docking to any edge
    - Enable floating mode
    - _Requirements: 5.3, 5.4_

  
  - [ ] 10.3 Connect menu action to dock widget
    - Show/hide dock widget when menu item clicked
    - Toggle checked state of menu action
    - Preserve dock widget state across sessions

    - _Requirements: 5.3, 5.5_

- [ ] 11. Implement state persistence
  - [ ] 11.1 Save and restore window geometry
    - Save window size and position on close

    - Restore window geometry on startup
    - Handle multi-monitor scenarios
    - _Requirements: 7.1, 7.2_
  
  - [x] 11.2 Save and restore splitter positions

    - Save Analysis tab left splitter sizes
    - Save Analysis tab main splitter sizes
    - Restore splitter positions on startup
    - Use sensible defaults if no saved state exists
    - _Requirements: 7.1, 7.2_
  

  - [ ] 11.3 Save and restore dock widget states
    - Save visibility state of each dock widget
    - Save position and size of each dock widget
    - Save floating/docked state

    - Restore all dock widget states on startup

    - _Requirements: 5.5, 7.1, 7.2_
  
  - [ ] 11.4 Save and restore last active tab
    - Remember which main tab was active on close
    - Restore active tab on startup
    - _Requirements: 7.1, 7.2_


- [ ] 12. Preserve existing functionality
  - [ ] 12.1 Verify document upload and analysis workflow
    - Test file selection dialog
    - Test document parsing and preprocessing
    - Test analysis execution
    - Test result display in right panel
    - _Requirements: 4.1_

  
  - [ ] 12.2 Verify rubric management
    - Test rubric selection from combo box
    - Test rubric manager dialog access
    - Test custom rubric loading

    - _Requirements: 4.3_

  
  - [ ] 12.3 Verify chat functionality
    - Test chat dialog opening
    - Test AI assistance queries
    - Test chat history persistence
    - _Requirements: 4.4_

  
  - [ ] 12.4 Verify batch processing
    - Test batch analysis dialog access
    - Test multiple document processing
    - Test batch results display

    - _Requirements: 4.5_
  
  - [ ] 12.5 Verify reporting features
    - Test report generation
    - Test report preview in left panel

    - Test report export (PDF, HTML)

    - Test interactive report features
    - _Requirements: 4.7_
  
  - [ ] 12.6 Verify settings and configuration
    - Test theme switching

    - Test preference changes
    - Test configuration persistence
    - _Requirements: 4.6, 7.1, 7.2, 7.3_

- [x] 13. Maintain ViewModel integration

  - [ ] 13.1 Connect UI signals to ViewModel
    - Connect rubric selection to load_rubrics()
    - Connect analysis button to start_analysis()
    - Connect dashboard refresh to load_dashboard_data()
    - Connect meta analytics to load_meta_analytics()

    - _Requirements: 5.5, 5.6_
  
  - [ ] 13.2 Connect ViewModel signals to UI updates
    - Connect status_message_changed to status bar
    - Connect api_status_changed to status indicator
    - Connect rubrics_loaded to rubric combo box
    - Connect dashboard_data_loaded to dashboard widget
    - Connect meta_analytics_loaded to meta analytics widget
    - Connect analysis_result_received to results display
    - _Requirements: 5.5, 5.6_
  
  - [ ] 13.3 Preserve background worker functionality
    - Verify health check worker continues running
    - Verify task monitor worker continues running
    - Verify log stream worker continues running
    - Verify analysis workers function correctly
    - _Requirements: 5.5, 8.1, 8.2_

- [ ] 14. Apply visual consistency
  - [ ] 14.1 Apply theme styling to all widgets
    - Apply theme to left panel widgets
    - Apply theme to right panel widgets
    - Apply theme to dock widgets
    - Apply theme to Settings tab

    - _Requirements: 6.1, 6.2, 6.4_
  
  - [ ] 14.2 Set consistent spacing and margins
    - Use consistent padding in all panels

    - Set appropriate splitter handle sizes


    - Configure widget spacing according to design
    - _Requirements: 6.2_
  

  - [ ] 14.3 Add icons and visual elements
    - Add icons to tabs
    - Add icons to menu items

    - Add icons to buttons

    - Ensure icons work in both light and dark themes

    - _Requirements: 6.3_


- [ ] 15. Implement error handling
  - [ ] 15.1 Handle layout restoration errors
    - Catch exceptions during splitter size restoration

    - Use default sizes if saved sizes are invalid
    - Log errors without disrupting user experience

    - _Requirements: 8.1, 8.2_
  
  - [x] 15.2 Handle widget initialization errors

    - Catch exceptions during widget creation
    - Display placeholder widgets with error messages
    - Update status bar with error information
    - _Requirements: 8.1, 8.2_
  
  - [x] 15.3 Handle dock widget state restoration errors

    - Catch exceptions during dock state restoration
    - Reset to default positions if restoration fails
    - Continue application startup despite errors
    - _Requirements: 8.1, 8.2_
  


  - [ ] 15.4 Handle new widget loading errors
    - Disable menu items if widgets fail to import

    - Show tooltips explaining why widgets are unavailable
    - Provide graceful degradation
    - _Requirements: 8.1, 8.2_

- [x] 16. Add keyboard shortcuts and accessibility

  - [ ] 16.1 Add keyboard shortcuts for main tabs
    - Ctrl+1 for Analysis tab
    - Ctrl+2 for Dashboard tab
    - Ctrl+3 for Mission Control tab
    - Ctrl+4 for Settings tab

    - _Requirements: 6.4_
  
  - [ ] 16.2 Add keyboard shortcuts for dock widgets
    - Ctrl+Shift+A for Meta Analytics
    - Ctrl+Shift+P for Performance Status
    - _Requirements: 5.4_

  
  - [ ] 16.3 Ensure keyboard navigation works
    - Test tab navigation through all widgets
    - Test focus indicators are visible
    - Test all buttons are keyboard accessible
    - _Requirements: 6.4_
  
  - [ ] 16.4 Add tooltips and status tips
    - Add tooltips to all buttons and controls
    - Add status tips for menu items
    - Ensure tooltips are descriptive and helpful
    - _Requirements: 6.4_

- [ ] 17. Create migration notification
  - [ ] 17.1 Detect first launch after restoration
    - Check for migration flag in QSettings
    - Set flag after showing notification
    - _Requirements: 5.4_
  
  - [ ] 17.2 Show informational message
    - Display QMessageBox with migration information
    - Explain that Mission Control is now a main tab
    - Explain where to find Meta Analytics and Performance Status (Tools menu)
    - Provide "Don't show again" option
    - _Requirements: 5.4_

- [ ] 18. Testing and validation
  - [ ] 18.1 Run unit tests
    - Test UI component creation
    - Test widget integration
    - Test state persistence
    - Fix any failing tests
    - _Requirements: All_
  
  - [ ] 18.2 Run integration tests
    - Test analysis workflow end-to-end
    - Test dashboard workflow
    - Test new widget workflows
    - Fix any issues discovered
    - _Requirements: All_
  
  - [ ] 18.3 Perform manual testing
    - Complete manual testing checklist from design document
    - Test on different screen sizes and resolutions
    - Test with different themes
    - Test state persistence across restarts
    - _Requirements: All_
  
  - [ ] 18.4 Performance testing
    - Measure application startup time
    - Measure widget loading times
    - Verify no memory leaks
    - Optimize if performance issues found
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 19. Documentation and cleanup
  - [ ] 19.1 Update code documentation
    - Add docstrings to new methods
    - Update existing docstrings if changed
    - Document layout structure in comments
    - _Requirements: All_
  
  - [ ] 19.2 Update user documentation
    - Document new menu items for widgets
    - Document keyboard shortcuts
    - Update screenshots if needed
    - _Requirements: 5.4_
  
  - [ ] 19.3 Clean up code
    - Remove unused imports
    - Remove commented-out code
    - Format code with ruff
    - Run type checking with mypy
    - _Requirements: All_
  
  - [ ] 19.4 Archive old implementation
    - Move backup to archive folder with timestamp
    - Document what was changed
    - Keep rollback instructions
    - _Requirements: All_
