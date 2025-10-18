# 🏥 Therapy Compliance Analyzer

> AI-powered desktop application for clinical therapists to analyze documentation compliance with Medicare and regulatory guidelines.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2.0-blue.svg)](https://reactjs.org/)
[![Electron](https://img.shields.io/badge/Electron-38.2.2-blue.svg)](https://www.electronjs.org/)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

## ✨ Features

### 🔍 **Document Analysis**
- **Multi-format Support**: PDF, DOCX, TXT with OCR capabilities
- **AI-Powered Analysis**: Local LLM processing for privacy compliance
- **Compliance Scoring**: Risk-weighted scoring with confidence indicators
- **Interactive Reports**: HTML reports with source highlighting

### 🎨 **Modern Interface**
- **Professional UI**: React-based medical-themed design with blue branding
- **Responsive Layout**: Modern Electron desktop application
- **Integrated Chat**: AI assistant for compliance questions
- **Theme Support**: Light/Dark mode with persistent preferences

### 🔒 **Privacy & Security**
- **Local Processing**: All AI operations run locally (HIPAA compliant)
- **PHI Protection**: Automated detection and scrubbing of sensitive data
- **Secure Authentication**: JWT-based user management
- **Encrypted Storage**: Local SQLite database with encryption

### 📊 **Analytics & Reporting**
- **Dashboard**: Historical compliance trends and metrics
- **Export Options**: PDF and HTML report generation
- **Rubric Management**: Custom compliance rules in TTL format
- **Performance Tracking**: System monitoring and optimization

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (Required for backend)
- **Node.js 18+** (Required for frontend)
- **4GB+ RAM** (Recommended for AI models)
- **2GB+ Storage** (For models and data)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd therapy-compliance-analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-optimized.txt
   ```

4. **Start the application**
   ```bash
   # Terminal 1: Start API server
   python scripts/run_api.py

   # Terminal 2: Start GUI
   python scripts/run_gui.py
   ```

6. **Login**
   - Username: `admin`
   - Password: `admin123`

## 📖 Documentation

### User Guides
- **[Quick Start Guide](.kiro/USER_GUIDE_QUICK_START.md)** - Get up and running in 5 minutes
- **[User Manual](.kiro/steering/user_story.md)** - Complete feature documentation
- **[Testing Guide](.kiro/TESTING_CHECKLIST_NOW.md)** - How to test all features

### Developer Resources
- **[Architecture Overview](.kiro/steering/ANALYSIS.md)** - System design and components
- **[Development Guide](.kiro/steering/AGENTS.md)** - Setup and contribution guidelines
- **[API Documentation](.kiro/steering/tech.md)** - Technical stack and APIs
- **[Testing Guide](.kiro/steering/testing_guide.md)** - Comprehensive testing procedures

### Project Management
- **[Workflow Documentation](.kiro/steering/WORKFLOW.md)** - Complete system workflow
- **[Feature Checklist](.kiro/steering/workflow_checklist.md)** - Development progress
- **[Security Guidelines](.kiro/steering/security_validation.md)** - Security best practices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   PySide6 GUI   │    │   FastAPI API   │
│   (Frontend)    │◄──►│   (Backend)     │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Local AI/ML    │    │ SQLite Database │
│  Processing     │    │ (Encrypted)     │
└─────────────────┘    └─────────────────┘
```

### Key Components
- **Frontend**: PySide6 desktop application with modern UI
- **Backend**: FastAPI with modular router architecture
- **AI/ML**: Local processing with ctransformers, sentence-transformers
- **Database**: SQLAlchemy ORM with SQLite storage
- **Security**: JWT authentication, PHI scrubbing, local-only processing

## 🎯 Usage

### Basic Workflow
1. **Upload Document** - Select PDF, DOCX, or TXT file
2. **Choose Rubric** - Select compliance guidelines (Medicare, Part B, etc.)
3. **Set Strictness** - Choose analysis level (Lenient, Standard, Strict)
4. **Run Analysis** - AI processes document for compliance issues
5. **Review Results** - Interactive report with findings and recommendations
6. **Export Report** - Generate PDF or HTML for documentation
7. **Ask Questions** - Use integrated chat for clarification

### Advanced Features
- **Dashboard Analytics** - View historical compliance trends
- **Custom Rubrics** - Create organization-specific rules
- **Batch Processing** - Analyze multiple documents
- **Performance Monitoring** - System health and optimization

## 🔧 Configuration

### Environment Variables
```bash
DATABASE_URL="sqlite:///./compliance.db"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Configuration Files
- `config.yaml` - Main application settings
- `.env` - Environment variables and secrets
- `pytest.ini` - Test configuration

## 🧪 Testing

```bash
# Run all tests
pytest

# Run tests excluding slow ones
pytest -m "not slow"

# Run with coverage
pytest --cov=src

# Code quality checks
ruff check src/
mypy src/
```

## 📊 Performance

### System Requirements
- **Startup Time**: <5 seconds
- **Analysis Time**: 30-60 seconds per document
- **Memory Usage**: <2GB during normal operation
- **Storage**: ~500MB for AI models (downloaded on first run)

### Optimization Features
- **Caching**: LRU cache for frequently accessed data
- **Background Processing**: Non-blocking UI operations
- **Model Optimization**: Efficient AI model loading and inference
- **Database Optimization**: Connection pooling and query optimization

## 🔒 Security & Privacy

### Privacy Protection
- **Local Processing**: All AI operations run on your machine
- **No External Calls**: No data sent to external APIs or services
- **PHI Scrubbing**: Automatic detection and redaction of sensitive information
- **Encrypted Storage**: Local database encryption for sensitive data

### Security Features
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive validation of all user inputs
- **Rate Limiting**: Protection against abuse and overload
- **Audit Logging**: Activity tracking without PHI exposure

## 🤝 Contributing

### Development Setup
1. Follow installation instructions above
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Run tests to ensure everything works: `pytest`
4. Follow coding standards: `ruff check src/`

### Code Quality
- **Linting**: Use `ruff` for code formatting and linting
- **Type Checking**: Use `mypy` for static type analysis
- **Testing**: Write tests for new features using `pytest`
- **Documentation**: Update documentation for any changes

## 📝 Changelog

### v1.1.0 (Current)
- ✅ Blue title color and modern UI improvements
- ✅ Reorganized layout with better scaling
- ✅ Integrated chat bar (removed separate chat tab)
- ✅ Enhanced color contrast and professional styling
- ✅ Comprehensive PDF export functionality
- ✅ Performance optimizations and fast exit

### v1.0.0
- ✅ Initial release with core functionality
- ✅ Document analysis and compliance scoring
- ✅ Interactive HTML reports
- ✅ Dashboard analytics and user management

## 📞 Support

### Getting Help
1. **Documentation**: Check the comprehensive docs in `.kiro/steering/`
2. **Testing**: Use the testing checklist in `.kiro/TESTING_CHECKLIST_NOW.md`
3. **Troubleshooting**: Common issues and solutions documented
4. **AI Assistant**: Use the integrated chat for compliance questions

### Known Issues
- **PDF Export**: Requires `weasyprint` for best results (`pip install weasyprint`)
- **OCR**: Requires `tesseract` for scanned document processing
- **First Run**: AI models download (~500MB) requires internet connection

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🎉 Ready to Analyze!

The Therapy Compliance Analyzer is ready to help you improve clinical documentation quality and ensure regulatory compliance.

**Start analyzing today!** 🏥✨

---

*For technical support or questions, refer to the documentation in `.kiro/steering/` or use the integrated AI assistant.*

## Core Module Overview

The `src/core` package contains the application’s analysis and ML services:
- Analysis pipeline (`analysis_service.py`): orchestrates ingestion → analysis → reporting with progress callbacks.
- Compliance analyzer (`compliance_analyzer.py`): rule/rubric evaluation and result shaping.
- Retrieval & embeddings (`hybrid_retriever.py`, `vector_store.py`): BM25 + dense retrieval, FAISS-backed vector index with graceful fallbacks.
- Guideline/rubric utilities (`guideline_service.py`, `rubric_loader.py`).
- NER and NLP (`ner.py`, Presidio integration) and model selection helpers.
- LLM integration (`llm_service.py`, `report_generator.py`, `pdf_export_service.py`).
- Performance integration (`performance_integration.py`) and utilities.

## Secrets and Startup (Best Practice)

1) Generate a strong SECRET_KEY and set it in the environment:
```powershell
# Generate a secure key
python scripts\generate_secret_key.py
# Set it for the current session
$env:SECRET_KEY = '<paste-generated-key>'
```

2) Start the API cleanly (frees port 8001, activates venv, sets env vars):
```powershell
./scripts/start_api_clean.ps1 -ApiHost '127.0.0.1' -ApiPort 8001 -LogLevel 'INFO'
```

3) Quick end-to-end smoke (token → rubrics → upload → status):
```powershell
python temp\dev_api_smoke.py
```

Notes:
- CORS is restricted to localhost by default.
- Mocks are disabled in `config.yaml` (`use_ai_mocks: false`). Enable via `USE_AI_MOCKS=1` if needed for fast demos.

## CI

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs tests on push/PR with a test secret and mocks enabled for reliability.