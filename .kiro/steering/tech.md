# Technology Stack

## Core Framework
- **Backend**: FastAPI with modular router architecture
- **Frontend**: PyQt6 desktop application
- **Database**: SQLAlchemy with SQLite
- **Authentication**: JWT tokens with passlib/bcrypt

## AI/ML Stack
- **Local LLMs**: ctransformers with GGUF models (Phi-2, Mistral)
- **Embeddings**: sentence-transformers for semantic search
- **Search**: Hybrid approach using FAISS + BM25 (rank_bm25)
- **NLP**: NLTK, transformers, specialized biomedical NER models
- **Document Processing**: pdfplumber, python-docx, pytesseract

## Development Tools
- **Testing**: pytest with pytest-qt, pytest-asyncio, pytest-mock
- **Code Quality**: ruff for linting, mypy for type checking
- **Scheduling**: APScheduler for background tasks
- **Rate Limiting**: slowapi for API protection

## Common Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend API (development)
uvicorn src.api.main:app --reload

# Run GUI application
python -m src.main
```

### Testing
```bash
# Run all tests
pytest

# Run tests excluding slow ones
pytest -m "not slow"

# Run with coverage
pytest --cov=src
```

### Code Quality
```bash
# Lint code
ruff check src/

# Type checking
mypy src/

# Format code
ruff format src/
```

## Configuration
- Main config: `config.yaml` and `src/config.yaml`
- Environment variables via `.env` file for secrets
- Test config: `pytest.ini`, `mypy.ini`