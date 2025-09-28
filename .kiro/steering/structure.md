---
inclusion: always
---

# Project Structure & Architecture

## Architecture Patterns
- **Modular Monolith**: Single codebase with clear layer separation (API/GUI/Core)
- **Service Layer**: Business logic in dedicated service classes in `/src/core/`
- **Repository Pattern**: Database operations abstracted through CRUD modules
- **Dependency Injection**: Use FastAPI's DI system for services and database sessions

## Directory Structure & File Placement Rules

### `/src/api/` - FastAPI Backend
- `main.py` - App entry point with lifespan management
- `routers/{domain}.py` - Route handlers (auth, analysis, dashboard, admin)
- `dependencies.py` - DI setup and startup/shutdown logic
- **Rule**: New API endpoints go in domain-specific routers, not main.py

### `/src/core/` - Business Logic Services
- Analysis: `document_analysis_service.py`, `compliance_analyzer.py`
- AI/ML: `llm_service.py`, `ner.py`, `fact_checker_service.py`, `nlg_service.py`
- Processing: `preprocessing_service.py`, `parsing.py`, `smart_chunker.py`
- Retrieval: `hybrid_retriever.py`, `retriever.py`, `guideline_service.py`
- Utils: `prompt_manager.py`, `risk_scoring_service.py`, `phi_scrubber.py`
- **Rule**: All business logic must be in service classes, never in routers

### `/src/database/` - Data Layer
- `models.py` - SQLAlchemy ORM models only
- `schemas.py` - Pydantic validation schemas only
- `crud.py` - Database operations only
- `database.py` - Connection and session management
- **Rule**: No business logic in database layer, only data operations

### `/src/gui/` - PyQt6 Desktop Application
- `main.py` - GUI entry point
- `main_window.py` - Primary window
- `dialogs/` - Modal dialogs and forms
- `widgets/` - Custom UI components
- `workers/` - Background thread workers for async ops
- **Rule**: Use workers for any operation that might block the UI

## Code Organization Rules

### Service Classes
- Must be stateless and focused on single responsibility
- Use dependency injection for composition
- Import services in API routers, never instantiate directly
- Name pattern: `{domain}_service.py`

### Database Operations
- All database access through CRUD functions in `src/database/crud.py`
- Use Pydantic schemas for validation, SQLAlchemy models for ORM
- Never write raw SQL, use SQLAlchemy ORM methods
- Always use database sessions from dependency injection

### API Structure
- Group routes by domain (auth, analysis, dashboard, admin)
- Use FastAPI dependency injection for DB sessions and auth
- Apply rate limiting via slowapi middleware
- Return Pydantic schemas, never raw database models

### Configuration
- Main config in `config.yaml` with Pydantic models in `src/config.py`
- Secrets via environment variables (DATABASE_URL, SECRET_KEY)
- Cache settings using `@lru_cache()` decorator
- Never hardcode configuration values

## File Naming & Import Conventions

### Naming Rules
- Services: `{domain}_service.py` (e.g., `document_analysis_service.py`)
- Database: `models.py`, `schemas.py`, `crud.py`
- API routers: Domain name (e.g., `auth.py`, `analysis.py`)
- GUI: Descriptive names (`main_window.py`, `analysis_dialog.py`)

### Import Order
1. Standard library imports
2. Third-party imports (FastAPI, SQLAlchemy, etc.)
3. Local imports (relative imports within packages)
- Use `from .database import models` for relative imports
- Use `from src.core import analysis_service` for absolute imports

### Testing Structure
- Unit tests: `/tests/unit/{module}_test.py`
- Integration tests: `/tests/integration/`
- GUI tests: `/tests/gui/` using pytest-qt
- Test data: `/tests/test_data/`
- **Rule**: Mock external dependencies, never use real PHI data in tests

## Key Architectural Constraints
- **Local Processing Only**: All AI/ML operations must run locally for privacy
- **Async Patterns**: Use async/await for FastAPI endpoints and long operations
- **Background Processing**: Use APScheduler for maintenance, workers for GUI
- **Caching Strategy**: LRU cache for settings, database cache for embeddings
- **Error Handling**: Graceful degradation, meaningful user messages, proper logging