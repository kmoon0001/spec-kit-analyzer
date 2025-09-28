# Therapy Compliance Analyzer - Development Guidelines

## Project Overview
AI-powered desktop application for clinical therapists to analyze documentation for compliance with Medicare and regulatory guidelines. Built with FastAPI backend + PyQt6 frontend, all processing occurs locally for data privacy.

## Project Structure & Module Organization

### Core Architecture
- **`src/api/`** - FastAPI backend with modular routers, dependency injection, and scheduled maintenance jobs
- **`src/core/`** - Business logic services (AI/ML, analysis, compliance, document processing)
- **`src/database/`** - Data layer with SQLAlchemy models, schemas, and CRUD operations
- **`src/gui/`** - PyQt6 desktop application with dialogs, widgets, and background workers
- **`src/resources/`** - Static assets (prompts, rubrics, templates, medical dictionaries)
- **`src/utils/`** - Cross-cutting utilities and helpers
- **`tests/`** - Comprehensive test suite (`unit/`, `integration/`, `gui/`) with fixtures in `test_data/`

### Key Service Components
- **Analysis Pipeline**: `document_analysis_service.py`, `compliance_analyzer.py`, `preprocessing_service.py`
- **AI/ML Stack**: `llm_service.py`, `ner.py`, `fact_checker_service.py`, `nlg_service.py`
- **Retrieval System**: `hybrid_retriever.py`, `guideline_service.py`, `smart_chunker.py`
- **Security & Privacy**: `phi_scrubber.py`, JWT authentication, local-only processing

## Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Running the Application
```bash
# Start FastAPI backend (development mode with hot-reload)
uvicorn src.api.main:app --reload

# Alternative: Use the run script
python run_api.py

# Start PyQt6 GUI application
python run_gui.py
```

### Testing & Quality Assurance
```bash
# Run full test suite
pytest

# Run tests excluding slow ones for rapid iteration
pytest -m "not slow"

# Run with coverage reporting
pytest --cov=src

# Code quality checks (must pass before commits)
ruff check src/ tests/
mypy src/
ruff format src/ tests/  # Auto-format code
```

## Coding Standards & Architecture Patterns

### Code Organization Rules
- **Service Layer Pattern**: All business logic in `src/core/` service classes, never in API routers
- **Repository Pattern**: Database operations abstracted through `src/database/crud.py`
- **Dependency Injection**: Use FastAPI's DI system for services and database sessions
- **Modular Monolith**: Single codebase with clear layer separation (API/GUI/Core/Database)

### Naming Conventions
- **Services**: `{domain}_service.py` (e.g., `document_analysis_service.py`)
- **Database**: `models.py`, `schemas.py`, `crud.py` (separate concerns)
- **API Routers**: Domain-based naming (`auth.py`, `analysis.py`, `dashboard.py`)
- **GUI Components**: Descriptive names (`main_window.py`, `analysis_dialog.py`)

### Import Organization
1. Standard library imports
2. Third-party imports (FastAPI, SQLAlchemy, PyQt6, etc.)
3. Local imports (relative within packages, absolute for cross-package)

### Type Hints & Documentation
- Add type hints to all public functions and class methods
- Use Pydantic schemas for API validation and data transfer
- Document complex business logic and AI model interactions
- Include docstrings for service classes and their key methods

## Testing Guidelines

### Test Structure & Organization
- **Unit Tests**: `tests/unit/{module}_test.py` - Mock external dependencies
- **Integration Tests**: `tests/integration/` - Test service interactions
- **GUI Tests**: `tests/gui/` - Use pytest-qt for UI component testing
- **Test Data**: `tests/test_data/` - Synthetic data only, never real PHI

### Testing Best Practices
- Use fixtures from `tests/conftest.py` for common setup
- Mark slow tests with `@pytest.mark.slow` for CI optimization
- Mock AI models and external services to ensure fast, reliable tests
- Test error conditions and edge cases, especially for AI uncertainty handling
- Include GUI interaction tests for critical user workflows

## Security & Privacy Requirements

### Data Protection
- **Local Processing Only**: All AI/ML operations must run locally, never send data to external APIs
- **PHI Scrubbing**: Implement proper data sanitization before any logging or error reporting
- **Secure Authentication**: JWT tokens with proper expiration and secure storage
- **Database Security**: Encrypt sensitive data at rest, use parameterized queries

### Medical Domain Compliance
- Use specialized biomedical NER models for accurate entity extraction
- Include medical disclaimers and AI limitation disclosures in all reports
- Provide clear uncertainty indicators for AI-generated insights
- Implement proper medical terminology validation

## Configuration Management

### Configuration Files
- **Main Config**: `config.yaml` with Pydantic models in `src/config.py`
- **Environment Variables**: Use `.env` file for secrets (DATABASE_URL, SECRET_KEY)
- **Cache Settings**: Use `@lru_cache()` decorator for performance optimization
- **Never hardcode**: Configuration values, file paths, or API endpoints

### Environment Variables Required
```bash
DATABASE_URL="sqlite:///./compliance.db"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Commit & Pull Request Guidelines

### Commit Standards
- Use Conventional Commit format: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Keep subject lines ≤72 characters, use imperative mood
- Reference issues with `Refs #123`, avoid bundling unrelated changes
- Include meaningful commit messages that explain the "why" not just the "what"

### Pull Request Requirements
- Include brief summary of changes and verification steps
- Add UI screenshots for visual changes (in PR description, not repo)
- Ensure all tests pass and code quality checks are green
- Document any new configuration options or breaking changes
- Include performance impact assessment for AI/ML changes

## Performance & Scalability Considerations

### Local Processing Constraints
- Optimize for limited local compute resources
- Implement progress indicators for long-running AI operations
- Use background processing (QThread workers) for non-blocking UI
- Cache frequently accessed data (embeddings, model outputs) appropriately

### Memory Management
- Monitor memory usage during document processing
- Implement proper cleanup for temporary files and model instances
- Use streaming for large document processing when possible
- Consider memory-efficient alternatives for large embedding operations
