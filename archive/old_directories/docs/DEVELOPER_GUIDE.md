# 🛠️ Developer Guide - Therapy Compliance Analyzer

## 🎯 Overview

This guide provides comprehensive information for developers working on the Therapy Compliance Analyzer. The application uses a hybrid FastAPI backend + PySide6 frontend architecture with local AI processing.

---

## 🏗️ Architecture Overview

### System Design
```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Application                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   PySide6 GUI   │   FastAPI API   │    Local AI/ML Stack   │
│   (Frontend)    │   (Backend)     │    (Processing)         │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Main Window   │ • REST Endpoints│ • LLM Service           │
│ • Dialogs       │ • Authentication│ • NER Pipeline          │
│ • Widgets       │ • Rate Limiting │ • Hybrid Retrieval      │
│ • Workers       │ • Error Handling│ • Document Processing   │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  SQLite Database    │
                │  (Local Storage)    │
                └─────────────────────┘
```

### Key Principles
- **Local Processing**: All AI operations run locally for privacy
- **Modular Design**: Clear separation of concerns
- **Service Layer**: Business logic abstracted from UI and API
- **Dependency Injection**: FastAPI DI for service management
- **Background Processing**: Non-blocking operations with QThread workers

---

## 📁 Project Structure

```
therapy-compliance-analyzer/
├── src/                          # Source code
│   ├── api/                      # FastAPI backend
│   │   ├── routers/              # API route handlers
│   │   ├── dependencies.py       # DI configuration
│   │   └── main.py               # FastAPI app
│   ├── core/                     # Business logic services
│   │   ├── analysis_service.py   # Main analysis orchestrator
│   │   ├── llm_service.py        # Local LLM management
│   │   ├── ner.py                # Named entity recognition
│   │   ├── hybrid_retriever.py   # RAG system
│   │   └── ...                   # Other services
│   ├── database/                 # Data layer
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── schemas.py            # Pydantic validation
│   │   ├── crud.py               # Database operations
│   │   └── database.py           # Connection management
│   ├── gui/                      # PySide6 frontend
│   │   ├── components/           # Reusable UI components
│   │   ├── dialogs/              # Modal dialogs
│   │   ├── widgets/              # Custom widgets
│   │   ├── workers/              # Background thread workers
│   │   └── main_window.py        # Main application window
│   ├── resources/                # Static assets
│   │   ├── prompts/              # AI prompt templates
│   │   ├── *.ttl                 # Compliance rubrics
│   │   └── report_template.html  # Report template
│   └── utils/                    # Utility functions
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── gui/                      # GUI tests
├── scripts/                      # Runtime scripts
│   ├── run_api.py                # Start API server
│   └── run_gui.py                # Start GUI application
├── docs/                         # Documentation
├── .kiro/                        # Project management
│   └── steering/                 # Project guidance
├── requirements-optimized.txt    # Dependencies
├── config.yaml                   # Configuration
└── README.md                     # Project overview
```

---

## 🚀 Development Setup

### Prerequisites
- **Python 3.11+** (Required)
- **Git** (For version control)
- **4GB+ RAM** (For AI models)
- **2GB+ Storage** (For models and dependencies)

### Environment Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd therapy-compliance-analyzer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   # Production dependencies
   pip install -r requirements-optimized.txt
   
   # Development dependencies (optional)
   pip install -r requirements-dev.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your settings
   DATABASE_URL="sqlite:///./compliance.db"
   SECRET_KEY="your-super-secret-jwt-key"
   ```

5. **Initialize Database**
   ```bash
   # Database will be created automatically on first run
   python scripts/run_api.py
   ```

### Development Workflow

1. **Start Development Servers**
   ```bash
   # Terminal 1: API server with hot reload
   uvicorn src.api.main:app --reload --port 8001
   
   # Terminal 2: GUI application
   python scripts/run_gui.py
   ```

2. **Run Tests**
   ```bash
   # All tests
   pytest
   
   # Exclude slow tests
   pytest -m "not slow"
   
   # With coverage
   pytest --cov=src
   ```

3. **Code Quality**
   ```bash
   # Linting and formatting
   ruff check src/
   ruff format src/
   
   # Type checking
   mypy src/
   ```

---

## 🧩 Core Components

### FastAPI Backend (`src/api/`)

#### Main Application (`main.py`)
```python
from fastapi import FastAPI
from src.api.routers import analysis, auth, dashboard

app = FastAPI(title="Therapy Compliance Analyzer API")
app.include_router(analysis.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
```

#### Router Structure
- **`analysis.py`**: Document analysis endpoints
- **`auth.py`**: Authentication and user management
- **`dashboard.py`**: Analytics and reporting
- **`compliance.py`**: Compliance rule management
- **`chat.py`**: AI chat functionality

#### Key Features
- **Dependency Injection**: Services injected via FastAPI DI
- **Rate Limiting**: slowapi for abuse protection
- **Error Handling**: Comprehensive exception handling
- **Background Tasks**: Long-running operations in background

### Core Services (`src/core/`)

#### Analysis Service (`analysis_service.py`)
Main orchestrator for document analysis workflow:
```python
class AnalysisService:
    def __init__(self, llm_service, ner_service, retriever):
        self.llm_service = llm_service
        self.ner_service = ner_service
        self.retriever = retriever
    
    async def analyze_document(self, document, rubric):
        # 1. Document classification
        # 2. Text preprocessing
        # 3. Entity extraction
        # 4. Compliance analysis
        # 5. Report generation
```

#### LLM Service (`llm_service.py`)
Local language model management:
```python
class LLMService:
    def __init__(self, model_path):
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
    
    def generate_analysis(self, prompt, context):
        # Generate compliance analysis using local LLM
```

#### Hybrid Retriever (`hybrid_retriever.py`)
RAG system combining semantic and keyword search:
```python
class HybridRetriever:
    def __init__(self, vector_store, bm25_index):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
    
    def retrieve_relevant_rules(self, query):
        # Combine semantic and keyword search results
```

### PySide6 Frontend (`src/gui/`)

#### Main Window (`main_window.py`)
Primary application interface with tabbed layout:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._setup_workers()
    
    def _build_ui(self):
        # Create header, tabs, and layout
        # Analysis, Dashboard, Mission Control, Settings
```

#### Component Architecture
- **Components**: Reusable UI elements (header, status)
- **Dialogs**: Modal windows (chat, settings, reports)
- **Widgets**: Custom controls (dashboard, analytics)
- **Workers**: Background thread operations

#### Worker Pattern
```python
class AnalysisWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def run(self):
        try:
            result = self.analysis_service.analyze(self.document)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### Database Layer (`src/database/`)

#### Models (`models.py`)
SQLAlchemy ORM models:
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    # ... other fields

class AnalysisReport(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_name: Mapped[str] = mapped_column(String)
    # ... other fields
```

#### CRUD Operations (`crud.py`)
Database operations abstraction:
```python
async def create_analysis_report(db: AsyncSession, report_data: dict):
    report = AnalysisReport(**report_data)
    db.add(report)
    await db.commit()
    return report
```

---

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_llm_service.py
│   ├── test_ner.py
│   └── ...
├── integration/             # Integration tests (slower)
│   ├── test_analysis_flow.py
│   ├── test_api_endpoints.py
│   └── ...
├── gui/                     # GUI tests (pytest-qt)
│   ├── test_main_window.py
│   └── ...
└── conftest.py              # Test configuration
```

### Testing Best Practices

#### Unit Tests
```python
import pytest
from unittest.mock import Mock
from src.core.llm_service import LLMService

def test_llm_service_analysis():
    # Arrange
    mock_model = Mock()
    service = LLMService(mock_model)
    
    # Act
    result = service.analyze("test document")
    
    # Assert
    assert result is not None
    mock_model.generate.assert_called_once()
```

#### Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_analysis_endpoint(client):
    response = client.post("/analysis/analyze", 
                          json={"document": "test"})
    assert response.status_code == 200
```

#### GUI Tests
```python
import pytest
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

@pytest.fixture
def app():
    return QApplication([])

def test_main_window_creation(app):
    window = MainWindow()
    assert window.windowTitle() == "Therapy Compliance Analyzer"
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_llm_service.py

# With coverage
pytest --cov=src --cov-report=html

# Exclude slow tests
pytest -m "not slow"

# GUI tests (requires display)
pytest tests/gui/ -v
```

---

## 🔧 Configuration Management

### Configuration Files

#### `config.yaml`
Main application configuration:
```yaml
paths:
  temp_upload_dir: "tmp/uploads"
  api_url: "http://127.0.0.1:8001"
  rule_dir: "src/resources"

database:
  url: "sqlite:///./compliance.db"
  echo: false

models:
  generator: "microsoft/DialoGPT-medium"
  retriever: "sentence-transformers/all-MiniLM-L6-v2"
  ner_ensemble:
    - "d4data/biomedical-ner-all"
    - "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M"
```

#### `.env`
Environment variables and secrets:
```bash
DATABASE_URL="sqlite:///./compliance.db"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Configuration Loading
```python
from src.config import get_settings

settings = get_settings()
database_url = settings.database.url
api_url = settings.paths.api_url
```

---

## 🚀 Deployment

### Local Development
```bash
# Start both services
python scripts/run_api.py &
python scripts/run_gui.py
```

### Production Deployment
```bash
# Install production dependencies
pip install -r requirements-optimized.txt

# Set production environment
export ENVIRONMENT=production

# Start with gunicorn
gunicorn src.api.main:app --workers 4 --bind 0.0.0.0:8001
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-optimized.txt .
RUN pip install -r requirements-optimized.txt

COPY src/ src/
COPY config.yaml .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 🔒 Security Considerations

### Authentication
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: bcrypt for password storage
- **Session Management**: Secure token handling

### Input Validation
```python
from src.core.security_validator import SecurityValidator

# Validate all user inputs
is_valid, error = SecurityValidator.validate_filename(filename)
if not is_valid:
    raise HTTPException(400, detail=error)
```

### Privacy Protection
- **Local Processing**: All AI operations local
- **PHI Scrubbing**: Automatic PII detection and removal
- **Data Encryption**: Sensitive data encrypted at rest

---

## 📊 Performance Optimization

### Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_analysis_result(document_hash, rubric_id):
    # Cache expensive analysis results
    return analysis_service.analyze(document, rubric)
```

### Background Processing
```python
from PySide6.QtCore import QThread, Signal

class AnalysisWorker(QThread):
    finished = Signal(dict)
    
    def run(self):
        # Long-running analysis in background
        result = self.perform_analysis()
        self.finished.emit(result)
```

### Database Optimization
- **Connection Pooling**: SQLAlchemy connection pool
- **Query Optimization**: Efficient database queries
- **Indexing**: Proper database indexes for performance

---

## 🐛 Debugging

### Logging Configuration
```python
import structlog

logger = structlog.get_logger(__name__)

def analyze_document(document):
    logger.info("Starting analysis", document_name=document.name)
    try:
        result = perform_analysis(document)
        logger.info("Analysis completed", score=result.score)
        return result
    except Exception as e:
        logger.error("Analysis failed", error=str(e))
        raise
```

### Common Debug Scenarios

#### API Issues
```bash
# Check API server logs
python scripts/run_api.py

# Test endpoints directly
curl -X POST http://localhost:8001/analysis/analyze \
     -H "Content-Type: application/json" \
     -d '{"document": "test"}'
```

#### GUI Issues
```python
# Enable Qt debug output
import os
os.environ['QT_LOGGING_RULES'] = '*=true'

# Use Qt debugger
from PySide6.QtCore import qDebug
qDebug("Debug message")
```

#### Database Issues
```python
# Enable SQL logging
from src.database.database import engine
engine.echo = True  # Shows all SQL queries
```

---

## 🤝 Contributing

### Code Style
- **Formatting**: Use `ruff format` for consistent formatting
- **Linting**: Use `ruff check` for code quality
- **Type Hints**: Use type hints for all public functions
- **Documentation**: Docstrings for all classes and methods

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-analysis-method

# Make changes and commit
git add .
git commit -m "feat: add new analysis method"

# Push and create PR
git push origin feature/new-analysis-method
```

### Pull Request Process
1. **Create Branch**: Feature branch from main
2. **Write Tests**: Add tests for new functionality
3. **Update Docs**: Update relevant documentation
4. **Code Review**: Submit PR for review
5. **Merge**: Merge after approval and tests pass

---

## 📚 Additional Resources

### Documentation
- **API Reference**: Auto-generated from FastAPI
- **Architecture Decisions**: `.kiro/steering/ANALYSIS.md`
- **User Stories**: `.kiro/steering/user story.md`
- **Testing Guide**: `.kiro/steering/testing_guide.md`

### External Dependencies
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
- **PySide6**: [doc.qt.io/qtforpython](https://doc.qt.io/qtforpython/)
- **SQLAlchemy**: [sqlalchemy.org](https://www.sqlalchemy.org/)
- **Transformers**: [huggingface.co/transformers](https://huggingface.co/transformers/)

### Development Tools
- **VS Code**: Recommended IDE with Python extension
- **PyCharm**: Alternative IDE with excellent Python support
- **Git**: Version control system
- **Docker**: Optional containerization

---

## 🎯 Next Steps

### For New Developers
1. **Setup Environment**: Follow development setup guide
2. **Run Tests**: Ensure everything works locally
3. **Explore Codebase**: Start with main components
4. **Make Small Changes**: Begin with minor improvements
5. **Ask Questions**: Use team communication channels

### For Experienced Developers
1. **Architecture Review**: Understand system design
2. **Performance Analysis**: Identify optimization opportunities
3. **Feature Development**: Implement new capabilities
4. **Code Review**: Help maintain code quality
5. **Mentoring**: Guide new team members

---

*Happy coding! 🚀*