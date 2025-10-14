# 🚀 Therapy Compliance Analyzer - One-Click Launcher

## Quick Start Options

### Option 1: Super Obvious (Recommended)
**Double-click:** `🚀 START THERAPY ANALYZER.bat`
- Beautiful ASCII art splash screen
- Automatically starts both API and GUI
- Handles all setup automatically

### Option 2: Standard Batch File
**Double-click:** `START_THERAPY_ANALYZER.bat`
- Simple batch file launcher
- Starts API server then GUI
- Basic error handling

### Option 3: PowerShell (Advanced)
**Right-click → Run with PowerShell:** `START_THERAPY_ANALYZER.ps1`
- Advanced error handling
- Better progress reporting
- Background job management

## What Happens When You Run It

1. **🔧 Setup** - Activates Python virtual environment
2. **🤖 AI Loading** - Loads Mistral 7B and other AI models (30-60 seconds)
3. **🌐 API Server** - Starts on http://127.0.0.1:8001
4. **🖥️ GUI Launch** - Opens the desktop application
5. **✅ Ready** - You can now analyze therapy documents!

## System Requirements

- **RAM**: 8GB+ (optimized for 8GB systems)
- **CPU**: Any modern processor (CPU-only, no GPU required)
- **Storage**: 5GB free space for AI models
- **OS**: Windows 10/11

## Troubleshooting

### If API Fails to Start:
- Check that port 8001 is not in use
- Ensure virtual environment exists (`venv_fresh` folder)
- Check Windows Firewall settings

### If GUI Won't Open:
- Ensure API server started successfully first
- Check that PySide6 is installed
- Try running as Administrator

### If Models Won't Load:
- Ensure internet connection for initial model download
- Check available RAM (close other applications)
- Verify `models/mistral7b` folder exists

## Manual Commands (If Needed)

```bash
# Start API only
python -c "import sys; sys.path.insert(0, '.'); from src.api.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8001)"

# Start GUI only (API must be running first)
python scripts/run_gui.py
```

## Features

- ✅ **Real AI Models** - Mistral 7B, NER, Presidio
- ✅ **Compliance Analysis** - Therapy documentation checking
- ✅ **Progress Tracking** - Real-time analysis status
- ✅ **Dark Theme** - PyCharm-style interface
- ✅ **Resource Management** - Optimized for 8GB RAM
- ✅ **Error Handling** - Graceful failure recovery

---

**Need Help?** Check the logs in the console window for detailed error messages.
