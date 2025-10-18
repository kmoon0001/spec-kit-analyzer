# How to Run the Therapy Compliance Analyzer

## 🚀 Quick Start (Recommended)

### First Time Setup
```bash
# Run the diagnostic and fix script
DIAGNOSE_AND_FIX.bat
```

### Start the Application
```bash
# PowerShell (Recommended)
.\START_APP.ps1

# OR Command Prompt
START_APP.bat
```

## 📋 What Gets Started

The application consists of two parts that run together:

1. **Python FastAPI Backend** (Port 8001)
   - Handles AI/ML processing
   - Manages database
   - Provides REST API

2. **Electron/React Frontend** (Port 3001)
   - Desktop application UI
   - Communicates with backend API
   - Provides user interface

## 🔧 Troubleshooting

### Run Full Diagnostic
```powershell
.\RUN_FULL_DIAGNOSTIC.ps1
```

This checks:
- Python installation
- Node.js installation
- Virtual environment
- Node modules
- Port availability
- Database status
- API imports
- Configuration files

### Common Issues

#### "Port already in use"
```bash
# Kill processes on ports
netstat -ano | findstr ":8001"
taskkill /PID <PID> /F

netstat -ano | findstr ":3001"
taskkill /PID <PID> /F
```

#### "Virtual environment not found"
```bash
python -m venv venv_fresh
venv_fresh\Scripts\pip.exe install -r requirements.txt
```

#### "Node modules not installed"
```bash
cd frontend/electron-react-app
npm install
cd ../..
```

#### "API won't start"
```bash
# Test API separately
TEST_API.bat

# Check logs for errors
# API runs on http://127.0.0.1:8001
```

#### "Frontend won't start"
```bash
# Test frontend separately
TEST_FRONTEND.bat

# Reinstall if needed
cd frontend/electron-react-app
rm -rf node_modules package-lock.json
npm install
```

## 🧪 Testing Components Separately

### Test API Only
```bash
TEST_API.bat
```
Visit: http://127.0.0.1:8001/docs

### Test Frontend Only
```bash
# Make sure API is running first!
TEST_FRONTEND.bat
```

## 📚 Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

## 🔍 Ports Used

- **8001**: Python FastAPI backend
- **3001**: React development server
- **Electron**: Connects to port 3001 in dev mode

## 📁 Important Files

- `config.yaml` - Main application configuration
- `.env` - Backend environment variables
- `frontend/electron-react-app/.env` - Frontend configuration
- `compliance.db` - SQLite database

## 🎯 Architecture

```
┌─────────────────────┐
│  Electron Desktop   │
│  (React Frontend)   │
│  Port: 3001         │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  (Python)           │
│  Port: 8001         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SQLite Database    │
│  + AI Models        │
└─────────────────────┘
```

## 🛠️ Development Mode

Both components support hot-reload:
- **Backend**: Auto-reloads on Python file changes
- **Frontend**: Hot-reloads on React file changes
- **DevTools**: Press `Ctrl+Shift+I` in Electron

## 📦 First Run Notes

- First run downloads ~500MB of AI models
- Requires internet connection for initial model download
- Models are cached in `.cache` directory
- Subsequent runs are much faster

## ✅ Success Indicators

When running correctly, you should see:
1. API server starts and shows "Application startup complete"
2. React dev server compiles successfully
3. Electron window opens with login screen
4. No error messages in console

## 🆘 Still Having Issues?

1. Run `RUN_FULL_DIAGNOSTIC.ps1` to identify problems
2. Run `DIAGNOSE_AND_FIX.bat` to auto-fix common issues
3. Check the detailed guide in `QUICK_START.md`
4. Review logs in the console output
