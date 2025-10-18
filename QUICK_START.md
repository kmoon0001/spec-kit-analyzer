# Quick Start Guide - Therapy Compliance Analyzer

## Architecture
- **Backend**: Python FastAPI (port 8001)
- **Frontend**: Electron + React (port 3001)

## Prerequisites

### 1. Python Setup
```bash
# Check Python version (3.11+ required)
python --version

# Create virtual environment
python -m venv venv_fresh

# Activate virtual environment
venv_fresh\Scripts\activate  # Windows
# source venv_fresh/bin/activate  # Linux/Mac

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Node.js Setup
```bash
# Check Node version (16+ required)
node --version

# Install frontend dependencies
cd frontend/electron-react-app
npm install
cd ../..
```

## Running the Application

### Option 1: One-Click Launcher (Windows)
```bash
# PowerShell (Recommended)
.\START_APP.ps1

# OR Command Prompt
START_APP.bat
```

### Option 2: Manual Start (All Platforms)

**Terminal 1 - Start Python API:**
```bash
# Activate Python environment
venv_fresh\Scripts\activate  # Windows
# source venv_fresh/bin/activate  # Linux/Mac

# Start API server
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001 --reload
```

**Terminal 2 - Start Electron Frontend:**
```bash
cd frontend/electron-react-app
npm run dev
```

## Troubleshooting

### API won't start
```bash
# Check if port 8001 is in use
netstat -ano | findstr :8001

# Kill process if needed
taskkill /PID <PID> /F
```

### Frontend won't start
```bash
# Check if port 3001 is in use
netstat -ano | findstr :3001

# Reinstall dependencies
cd frontend/electron-react-app
rm -rf node_modules package-lock.json
npm install
```

### AI Models not loading
- First run downloads ~500MB of AI models
- Requires internet connection
- Models cached in `.cache` directory
- Check logs for download progress

## Default Login
- **Username**: `admin`
- **Password**: `admin123`

## API Documentation
Once running, visit: http://127.0.0.1:8001/docs

## Development Mode
- API auto-reloads on Python file changes
- Frontend hot-reloads on React file changes
- DevTools available in Electron (Ctrl+Shift+I)
