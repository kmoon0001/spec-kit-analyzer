# 🐛 THERAPY COMPLIANCE ANALYZER - DEBUGGING GUIDE

## 🚀 Quick Debug Commands

### **1. Full System Debug**
```bash
python debug_tools.py
```
**What it does**: Tests all components (API, GUI, AI models, endpoints, resources)
**Best for**: Complete system health check

### **2. Component-Specific Debug**
```bash
python debug_tools.py api      # API startup only
python debug_tools.py gui      # GUI components only  
python debug_tools.py endpoints # API endpoints only
python debug_tools.py ai       # AI models only
python debug_tools.py resources # System resources only
```

### **3. Real-Time Monitoring**
```bash
python monitor.py              # Continuous monitoring (5s intervals)
python monitor.py 10           # Continuous monitoring (10s intervals)
python monitor.py once         # Single status check
```
**What it shows**: API status, Python processes, CPU/RAM usage, response times

### **4. Log Analysis**
```bash
python analyze_logs.py
```
**What it does**: Analyzes all log files for errors, patterns, and performance issues

## 🔍 Debugging Strategies

### **Strategy 1: Systematic Component Testing**
1. **Start with**: `python debug_tools.py`
2. **Identify**: Which component is failing
3. **Focus**: Run specific component debug
4. **Fix**: Address the specific issue
5. **Verify**: Re-run full debug

### **Strategy 2: Real-Time Monitoring**
1. **Start**: `python monitor.py` in one terminal
2. **Launch**: Your application in another terminal
3. **Watch**: Monitor output for issues
4. **Identify**: Patterns in resource usage or errors

### **Strategy 3: Log-Based Debugging**
1. **Run**: Application normally
2. **Analyze**: `python analyze_logs.py`
3. **Review**: Error patterns and recommendations
4. **Fix**: Issues identified in analysis

## 🎯 Common Issues & Solutions

### **API Won't Start**
```bash
# Debug API startup
python debug_tools.py api

# Check port conflicts
netstat -an | findstr :8001

# Check Python processes
tasklist | findstr python
```

### **GUI Crashes**
```bash
# Debug GUI components
python debug_tools.py gui

# Check PySide6 installation
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"

# Check theme issues
python -c "from src.gui.widgets.pycharm_dark_theme import pycharm_theme; print('Theme OK')"
```

### **AI Models Won't Load**
```bash
# Debug AI models
python debug_tools.py ai

# Check model files
dir models\mistral7b

# Check memory usage
python debug_tools.py resources
```

### **Performance Issues**
```bash
# Monitor resources
python monitor.py

# Analyze performance logs
python analyze_logs.py

# Check system resources
python debug_tools.py resources
```

## 📊 Debug Output Interpretation

### **API Debug Output**
- ✅ **PASS**: Component loaded successfully
- ❌ **FAIL**: Component failed to load
- ⚠️ **WARNING**: Component loaded but with issues

### **Monitor Output**
- 🌐 **API Status**: Online/Offline with response time
- 🐍 **Python Processes**: PID, memory usage, CPU usage
- 💻 **System Resources**: CPU%, RAM%, disk usage
- ⏱️ **Uptime**: How long monitor has been running

### **Log Analysis Output**
- 🚨 **ERROR SUMMARY**: Count of different error types
- 🔍 **TOP ERRORS**: Most frequent issues with examples
- ⚡ **PERFORMANCE PATTERNS**: Duration and memory patterns
- 💡 **RECOMMENDATIONS**: Suggested fixes

## 🛠️ Advanced Debugging

### **Enable Verbose Logging**
```python
# In your application code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Debug Specific Components**
```python
# Debug API startup
from src.api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get("/health")
print(response.json())
```

### **Memory Profiling**
```python
# Add to your code
import psutil
import os
process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024**2:.1f}MB")
```

### **Performance Timing**
```python
# Add to your code
import time
start_time = time.time()
# Your code here
print(f"Duration: {time.time() - start_time:.3f}s")
```

## 📁 Debug Files Created

- `debug.log` - Detailed debug output
- `monitor.log` - Real-time monitoring data
- `temp_api_out.log` - API stdout logs
- `temp_api_err.log` - API stderr logs

## 🎯 Debugging Workflow

1. **🔍 Identify Issue**: Use `debug_tools.py` to find failing components
2. **📊 Monitor**: Use `monitor.py` to watch real-time behavior
3. **📄 Analyze**: Use `analyze_logs.py` to find patterns
4. **🔧 Fix**: Address specific issues found
5. **✅ Verify**: Re-run debug tools to confirm fixes

## 🚨 Emergency Debugging

### **Application Won't Start At All**
```bash
# Check Python installation
python --version

# Check virtual environment
venv_fresh\Scripts\activate.bat
python --version

# Check dependencies
pip list | findstr -i "fastapi pyside6"
```

### **Complete System Reset**
```bash
# Kill all Python processes
taskkill /f /im python.exe

# Clear temporary files
del debug.log monitor.log temp_*.log

# Restart fresh
python debug_tools.py
```

---

**💡 Pro Tip**: Always start with `python debug_tools.py` for a complete system overview!
