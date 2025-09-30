# 🚀 Quick Start Guide

## How to Run the Therapy Compliance Analyzer

### **Method 1: Simple Startup (Recommended)**
```bash
python start_app.py
```
This script will:
- ✅ Check your environment setup
- ✅ Install missing dependencies automatically
- ✅ Launch the GUI application

### **Method 2: Direct Launch**
```bash
# Make sure you're in the project directory
python run_gui.py
```

### **Method 3: Backend + Frontend Separately**
```bash
# Terminal 1 - Start FastAPI backend
python run_api.py

# Terminal 2 - Start GUI frontend
python -m src.gui.main
```

## Prerequisites

### **1. Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### **2. System Requirements**
- **Python 3.11+**
- **6-16GB RAM** (app auto-adapts to your system)
- **Windows/Linux/Mac** (cross-platform)

## First Run

1. **Launch the app**: `python start_app.py`
2. **Wait for AI models**: First startup takes 30-60 seconds to load models
3. **Upload a document**: Click "Upload Document" and select a clinical note
4. **Select rubric**: Choose PT/OT/SLP compliance rubric
5. **Run analysis**: Click "Run Analysis" and wait for results
6. **View report**: Interactive compliance report appears in right panel

## Performance Optimization

The app automatically detects your system and applies optimal settings:

- **6-8GB RAM**: Conservative mode (CPU-only, small cache)
- **8-12GB RAM**: Balanced mode (GPU optional, moderate cache)
- **12-16GB+ RAM**: Aggressive mode (full GPU, large cache)

Access performance settings via: `Tools → Performance Settings`

## Troubleshooting

### **App Won't Start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Try direct launch
python run_gui.py
```

### **"AI Models Failed" Error**
- **First run**: Models download automatically (requires internet)
- **Subsequent runs**: Models cached locally
- **Fix**: Restart app, models will reload

### **Performance Issues**
- **High memory usage**: Switch to Conservative profile in settings
- **Slow analysis**: Enable GPU acceleration if available
- **UI freezing**: Close other applications, restart app

### **Import Errors**
```bash
# Activate virtual environment
.venv\Scripts\activate

# Verify installation
python -c "import PyQt6; print('✅ GUI ready')"
python -c "import fastapi; print('✅ API ready')"
```

## Features Overview

### **📄 Document Analysis**
- Upload PDF, DOCX, TXT files
- OCR support for scanned documents
- AI-powered compliance checking
- Real-time progress indicators

### **📊 Performance Monitoring**
- Real-time memory usage in status bar
- Automatic performance optimization
- Hardware-adaptive settings
- System health monitoring

### **📈 Dashboard & Analytics**
- Historical compliance trends
- Performance metrics
- Exportable reports
- Drill-down capabilities

### **⚙️ Advanced Settings**
- Performance profile selection
- Cache management
- GPU acceleration toggle
- Custom compliance rules

## Getting Help

- **Performance Settings**: `Tools → Performance Settings`
- **Compliance Guide**: Built-in help system with Medicare guidelines
- **Chat Assistant**: AI-powered help for compliance questions
- **Documentation**: See README.md for detailed information

## Success Indicators

✅ **Application starts without errors**
✅ **"AI Models Ready" appears in status bar**
✅ **Performance widget shows system status**
✅ **Document upload and analysis work**
✅ **Interactive reports generate properly**

Your Therapy Compliance Analyzer is now ready for clinical documentation analysis! 🎯