# Quick Start Guide

## Launch the Complete Application

### Single Command Launch
```batch
LAUNCH_COMPLETE_APP.bat
```

This will:
1. ✅ Clean up any existing processes
2. ✅ Start the FastAPI backend (port 8001)
3. ✅ Wait for API initialization
4. ✅ Launch the Electron frontend
5. ✅ Open the application window

### What to Expect

**Backend Console:**
```
INFO: Application startup complete with mocked services.
INFO: Uvicorn running on http://127.0.0.1:8001
```

**Frontend Window:**
- Login screen appears
- Use credentials: `admin` / `admin123`
- Navigate to Analysis tab
- Upload a document
- Watch progress go from 0% → 100%

## Testing Without Frontend

### Test API + Analysis Flow
```batch
START_API_ONLY.bat
```
Then in another terminal:
```batch
python test_analysis_direct.py
```

Expected output:
```
✓ Logged in successfully
✓ Analysis started
[  0.0s]  10% | processing   | Preprocessing document text...
[  1.5s] 100% | analyzing    | Analysis complete.
✓ ANALYSIS COMPLETED SUCCESSFULLY
```

## Troubleshooting

### API Won't Start
- Check if port 8001 is already in use
- Kill existing Python processes: `taskkill /F /IM python.exe`

### Frontend Won't Connect
- Ensure API is running first
- Check API is on http://127.0.0.1:8001
- Verify frontend config points to correct port

### Analysis Stuck
- Check API console for errors
- Verify `use_ai_mocks: true` in config.yaml
- Restart both API and frontend

## Configuration

### Enable/Disable AI Mocks
Edit `config.yaml`:
```yaml
use_ai_mocks: true   # Fast, no model download
# OR
use_ai_mocks: false  # Real AI (requires model download)
```

### Change API Port
Edit `config.yaml` and frontend config:
```yaml
# Backend
api:
  port: 8001

# Frontend: frontend/electron-react-app/src/config.js
API_BASE_URL: 'http://127.0.0.1:8001'
```

## Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

## Key Features Working

✅ Document upload (PDF, DOCX, TXT)
✅ Progress tracking (0% → 100%)
✅ Compliance analysis with mock AI
✅ Results display with findings
✅ Dashboard analytics
✅ User authentication

## Need Help?

See `FIXES_APPLIED.md` for detailed technical information about recent fixes.
