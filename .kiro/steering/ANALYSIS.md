# Therapy Compliance Analyzer - Technical Analysis

## Project Overview

The Therapy Compliance Analyzer is a sophisticated AI-powered desktop application designed for clinical therapists to analyze documentation for compliance with Medicare and regulatory guidelines. The project has evolved into a hybrid architecture combining a FastAPI backend with a PyQt6 desktop frontend, ensuring all AI processing occurs locally for maximum data privacy and security.

## Architecture & Technology Stack

### Hybrid Desktop-API Architecture
- **Backend**: FastAPI application with modular router architecture for scalable API endpoints
- **Frontend**: PyQt6 desktop application providing rich user interface and local file management
- **Database**: SQLAlchemy with SQLite for local data persistence and user management
- **Communication**: HTTP API calls between GUI and local backend service

### Core Technology Dependencies

#### AI/ML Stack
- **Local LLMs**: `ctransformers` with GGUF models (Meditron-7B clinical model) for compliance analysis
- **Embeddings**: `sentence-transformers` for semantic document understanding
- **Search**: Hybrid approach using `FAISS` + `rank_bm25` for intelligent retrieval
- **NLP Processing**: `NLTK`, `transformers`, specialized biomedical NER models
- **Document Processing**: `pdfplumber`, `python-docx`, `pytesseract` for multi-format support

#### Security & Privacy
- **Authentication**: JWT tokens with `passlib`/`bcrypt` for secure user management
- **PHI Protection**: `presidio-analyzer` & `presidio-anonymizer` for PII detection and scrubbing
- **Local Processing**: All AI operations run locally, no external API calls

#### Development & Quality Tools
- **Testing**: `pytest` with `pytest-qt`, `pytest-asyncio`, `pytest-mock` for comprehensive coverage
- **Code Quality**: `ruff` for linting and formatting, `mypy` for type checking
- **Background Tasks**: `APScheduler` for maintenance jobs, `QThread` workers for GUI operations
- **API Protection**: `slowapi` for rate limiting and abuse prevention

## Key Components & Services

### Core Analysis Pipeline (`src/core/`)
- **`document_analysis_service.py`**: Main orchestrator for document processing workflow
- **`compliance_analyzer.py`**: Core compliance checking logic against regulatory guidelines
- **`preprocessing_service.py`**: Text cleaning, medical spell-checking, and normalization
- **`smart_chunker.py`**: Intelligent document segmentation for optimal AI processing
- **`hybrid_retriever.py`**: Advanced RAG system combining semantic and keyword search

### AI/ML Services
- **`llm_service.py`**: Local LLM management and inference coordination
- **`ner.py`**: Named Entity Recognition for medical terminology extraction
- **`fact_checker_service.py`**: Verification of medical claims and compliance statements
- **`nlg_service.py`**: Natural Language Generation for personalized compliance feedback
- **`risk_scoring_service.py`**: Weighted algorithm for meaningful compliance scoring

### Data & Security Layer (`src/database/`)
- **`models.py`**: SQLAlchemy ORM models for users, documents, rubrics, and analysis results
- **`schemas.py`**: Pydantic validation schemas for API data transfer and validation
- **`crud.py`**: Database operations abstraction layer with proper error handling
- **`database.py`**: Connection management and session handling

### User Interface (`src/gui/`)
- **`main_window.py`**: Primary application window with tabbed interface (Analysis, Dashboard)
- **`dialogs/`**: Modal dialogs for rubric management, user settings, and chat interactions
- **`widgets/`**: Custom UI components including dashboard visualizations
- **`workers/`**: Background thread workers for non-blocking AI operations and API calls

### API Layer (`src/api/`)
- **`main.py`**: FastAPI application setup with lifespan management and middleware
- **`routers/`**: Domain-specific route handlers (auth, analysis, dashboard, admin, chat, compliance)
- **`dependencies.py`**: Dependency injection setup for services and database sessions

## Advanced Features & Capabilities

### Intelligent Document Analysis
- **Multi-format Support**: PDF, DOCX, TXT with OCR capabilities for scanned documents
- **Document Classification**: Automatic detection of document types (Progress Notes, Evaluations, etc.)
- **Medical Spell-checking**: Specialized preprocessing for clinical terminology
- **Contextual Chunking**: Smart segmentation preserving medical context and meaning

### Compliance Intelligence
- **Hybrid Search System**: Combines semantic understanding with keyword matching for precise rule retrieval
- **Uncertainty Handling**: AI confidence scoring with visual indicators for uncertain findings
- **Personalized Feedback**: NLG-generated actionable tips specific to each compliance issue
- **Risk-weighted Scoring**: Financial impact and severity-based compliance scoring algorithm

### Privacy & Security Features
- **Local-only Processing**: All AI operations run on user's machine, no data leaves the system
- **PHI Scrubbing**: Automated detection and redaction of Protected Health Information
- **Secure Authentication**: JWT-based user management with password hashing
- **Audit Trail**: Comprehensive logging of analysis activities (without PHI exposure)

### User Experience Enhancements
- **Interactive Dashboard**: Historical compliance trends with drill-down capabilities
- **Real-time Chat**: AI-powered assistance for compliance questions and clarifications
- **Progress Tracking**: Visual indicators for long-running analysis operations
- **Theme Support**: Light/dark mode with persistent user preferences and toggleable features
- **Rubric Management**: Full CRUD interface for custom compliance rule creation

## Database Schema & Data Flow

### Core Entities
- **Users**: Authentication, roles (admin/therapist), preferences
- **Documents**: Uploaded files with metadata and processing status
- **Rubrics**: Compliance rules in TTL format with versioning support
- **Analysis Results**: Detailed findings with confidence scores and recommendations
- **Chat Sessions**: AI conversation history for context preservation

### Data Processing Workflow
1. **Document Upload**: File validation, format detection, temporary storage
2. **Preprocessing**: Text extraction, cleaning, medical spell-checking, PHI scrubbing
3. **Classification**: Document type detection for context-aware analysis
4. **Chunking**: Intelligent segmentation preserving medical context
5. **Retrieval**: Hybrid search for relevant compliance rules
6. **Analysis**: LLM-powered compliance checking with uncertainty quantification
7. **Scoring**: Risk-weighted compliance score calculation
8. **Report Generation**: Structured output with actionable recommendations

## Performance & Scalability Considerations

### Local Processing Optimization
- **Model Caching**: LRU cache for frequently accessed AI models and embeddings
- **Background Processing**: Non-blocking operations using QThread workers and APScheduler
- **Memory Management**: Efficient handling of large documents and model instances
- **Progressive Loading**: Lazy initialization of AI components for faster startup

### Maintenance & Reliability
- **Automated Cleanup**: Scheduled purging of old reports and temporary files
- **Error Recovery**: Graceful degradation when AI models fail or are unavailable
- **Health Monitoring**: System status indicators for AI model availability
- **Database Maintenance**: Automated optimization and cleanup routines

## Testing Strategy & Quality Assurance

### Comprehensive Test Coverage
- **Unit Tests**: Individual service and component testing with mocked dependencies
- **Integration Tests**: End-to-end workflow testing with real (synthetic) data
- **GUI Tests**: PyQt6 interface testing using pytest-qt framework
- **Performance Tests**: Load testing for document processing and AI inference

### Quality Standards
- **Code Quality**: Enforced via ruff linting and mypy type checking
- **Security Testing**: PHI scrubbing validation and authentication testing
- **Medical Accuracy**: Validation against known compliance scenarios
- **User Experience**: Accessibility and usability testing for clinical workflows

## Future Architecture Considerations

### Scalability Paths
- **Multi-user Support**: Enhanced database schema for organizational deployments
- **Plugin Architecture**: Extensible rubric and analysis engine framework
- **Cloud Integration**: Optional secure cloud backup while maintaining local processing
- **API Expansion**: RESTful API for integration with existing clinical systems

### Technology Evolution
- **Model Updates**: Framework for updating local AI models while maintaining compatibility
- **Performance Optimization**: GPU acceleration for larger model inference
- **Advanced Analytics**: Machine learning for compliance trend prediction
- **Regulatory Adaptation**: Flexible framework for new compliance requirements
