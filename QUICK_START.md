# Quick Start Guide - Restored Interface

## Your New Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Therapy Compliance Analyzer                                │
│  File  View  Tools  Admin  Help                            │
├─────────────────────────────────────────────────────────────┤
│  [Analysis] [Dashboard] [Mission Control] [Settings]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ANALYSIS TAB:                                              │
│  ┌──────────────┬──────────────────────────────────────┐   │
│  │ LEFT PANEL   │ RIGHT PANEL                          │   │
│  │              │                                      │   │
│  │ ┌──────────┐ │ [Analysis Results] [Detailed] [Chat]│   │
│  │ │ Rubric   │ │                                      │   │
│  │ │ Selection│ │  Analysis results display here       │   │
│  │ └──────────┘ │                                      │   │
│  │              │                                      │   │
│  │ ┌──────────┐ │                                      │   │
│  │ │ Report   │ │                                      │   │
│  │ │ Preview  │ │                                      │   │
│  │ └──────────┘ │                                      │   │
│  │              │                                      │   │
│  │ ┌──────────┐ │                                      │   │
│  │ │ Report   │ │                                      │   │
│  │ │ Outputs  │ │                                      │   │
│  │ └──────────┘ │                                      │   │
│  └──────────────┴──────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Keyboard Shortcuts

### Tab Navigation
- **Ctrl+1**: Switch to Analysis tab
- **Ctrl+2**: Switch to Dashboard tab
- **Ctrl+3**: Switch to Mission Control tab
- **Ctrl+4**: Switch to Settings tab

### Dock Widgets
- **Ctrl+Shift+A**: Toggle Meta Analytics dock
- **Ctrl+Shift+P**: Toggle Performance Status dock

## Features by Tab

### 📊 Analysis Tab
**Left Panel:**
- **Rubric Selection** (top): Choose compliance rubric, upload documents, run analysis
- **Report Preview** (middle): View generated compliance reports
- **Report Outputs** (bottom): Access previous analysis results

**Right Panel:**
- **Analysis Results**: View detailed compliance findings
- **Detailed Findings**: See raw analysis data
- **Chat**: AI assistant for compliance questions

### 📈 Dashboard Tab
- View compliance trends over time
- See performance metrics
- Track improvement progress
- Refresh data with latest analysis results

### 🎛️ Mission Control Tab
- Monitor active analysis tasks
- View system logs
- Check API status
- Manage background processes

### ⚙️ Settings Tab
- **User Preferences**: Theme selection, password change
- **Performance**: Cache and memory settings
- **Analysis**: Default rubric, batch options
- **Advanced (Admin)**: System configuration

## Tools Menu

### Meta Analytics
Access via: **Tools → Meta Analytics** or **Ctrl+Shift+A**
- Organizational-level analytics
- Trend analysis across multiple documents
- Discipline-specific insights
- Dockable widget (can be moved/resized)

### Performance Status
Access via: **Tools → Performance Status** or **Ctrl+Shift+P**
- System resource monitoring
- Processing speed metrics
- Memory usage tracking
- Dockable widget (can be moved/resized)

## Typical Workflow

1. **Start the application**
   ```bash
   python scripts/start_application.py
   ```

2. **Upload a document** (Analysis tab)
   - Click "Browse..." in Rubric Selection panel
   - Select your clinical document (PDF, DOCX, TXT)

3. **Select a rubric**
   - Choose appropriate compliance rubric from dropdown
   - (PT, OT, or SLP specific)

4. **Run analysis**
   - Click "Run Analysis" button
   - Wait for processing (progress shown in status bar)

5. **Review results**
   - View findings in right panel
   - Check report preview in left panel
   - Export report if needed

6. **Track progress** (Dashboard tab)
   - View compliance trends
   - Monitor improvement over time

7. **Monitor system** (Mission Control tab)
   - Check active tasks
   - View system logs
   - Verify API connectivity

## Tips & Tricks

### Window Layout
- **Dock widgets** can be dragged to different edges
- **Splitters** can be resized by dragging the divider
- **Window state** is saved automatically on exit

### Batch Processing
- Use **File → Open Folder** for batch analysis
- Queue multiple documents in Auto-Analysis dock
- Process sequentially with automatic results saving

### Theme Switching
- **View → Theme → Light/Dark**
- Theme preference persists across sessions
- All widgets adapt to selected theme

### Keyboard Navigation
- Use **Tab** to navigate between controls
- **Enter** to activate buttons
- **Ctrl+Tab** to cycle through tabs (standard Qt behavior)

## Troubleshooting

### API Not Connected
**Symptom**: "API server not accessible" error
**Solution**: 
```bash
# Start API server first
python scripts/run_api.py
```

### Widgets Not Showing
**Symptom**: Meta Analytics or Performance Status not visible
**Solution**: 
- Check **Tools** menu
- Click menu item to toggle visibility
- Widgets are hidden by default

### Settings Not Saving
**Symptom**: Preferences reset on restart
**Solution**: 
- Check write permissions in application directory
- Settings stored in: `~/.config/TherapyCo/ComplianceAnalyzer.conf`

### Analysis Fails
**Symptom**: Analysis doesn't complete
**Solution**:
1. Check Mission Control tab for errors
2. Verify document format is supported
3. Ensure rubric is selected
4. Check API server logs

## Need Help?

- **Documentation**: Check `docs/` folder
- **Logs**: View in Mission Control tab
- **Support**: Open issue on GitHub
- **About**: Help → About for version info

---

**Enjoy your restored interface! 🎉**
