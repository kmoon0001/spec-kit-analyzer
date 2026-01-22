# ElectroAnalyzer Environment Setup Guide

## Quick Setup Options

### Option 1: PowerShell (Recommended for Windows)
```powershell
.\setup_env.ps1
```

### Option 2: Batch File (Windows)
```cmd
setup_env.bat
```

### Option 3: Manual Setup
1. Generate a secure SECRET_KEY:
   ```bash
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```

2. Install dependencies (note: `redis==5.2.1` is pinned because `5.2.2` is not
   published on some package indexes):
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export SECRET_KEY="your-generated-key-here"
   export USE_AI_MOCKS=false
   export API_HOST=127.0.0.1
   export API_PORT=8001
   export LOG_LEVEL=INFO
   ```

### Option 4: Create .env File
Create a `.env` file in your project root with:
```
SECRET_KEY=your-generated-key-here
USE_AI_MOCKS=false
API_HOST=127.0.0.1
API_PORT=8001
LOG_LEVEL=INFO
DEBUG=false
TESTING=false
```

## Verification
Test your setup:
```bash
python setup_env.py check
```

## Security Notes
- Keep your SECRET_KEY secure and never commit it to version control
- Use different SECRET_KEYs for development, staging, and production
- The SECRET_KEY is used for JWT token signing - it must be cryptographically secure

## Production Deployment
For production, set these environment variables in your deployment environment:
- SECRET_KEY (required)
- USE_AI_MOCKS=false
- LOG_LEVEL=WARNING or ERROR
- DEBUG=false
