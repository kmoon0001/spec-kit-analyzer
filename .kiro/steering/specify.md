# Therapy Compliance Analyzer - Product Specification

## Overview
Build a privacy-first, desktop application for clinical therapists to analyze documentation compliance with Medicare and regulatory guidelines. The application uses a hybrid FastAPI backend + PyQt6 frontend architecture with all AI processing occurring locally to ensure HIPAA compliance and data privacy.

## Core Architecture
- **Backend**: FastAPI with modular router architecture, SQLAlchemy ORM, JWT authentication
- **Frontend**: PyQt6 desktop application with tabbed interface (Analysis, Dashboard)
- **Database**: Local SQLite with encrypted storage for user data and analysis history
- **AI/ML Stack**: Local LLMs (ctransformers), sentence-transformers, hybrid retrieval (FAISS + BM25)
- **Document Processing**: Multi-format support (PDF, DOCX, TXT) with OCR capabilities via pytesseract

## Key Features Implemented

### Document Analysis Pipeline
- **Multi-format Ingestion**: PDF (pdfplumber), DOCX (python-docx), TXT with OCR support
- **Preprocessing**: Medical spell-checking, text cleaning, PHI scrubbing (presidio)
- **Document Classification**: AI-powered document type detection (Progress Notes, Evaluations, etc.)
- **Smart Chunking**: Context-aware text segmentation for optimal AI processing
- **Hybrid Retrieval**: Semantic + keyword search for compliance rule matching
- **Compliance Analysis**: Local LLM analysis with confidence scoring and uncertainty handling

### Rubric Management System
- **TTL Format Support**: Structured compliance rules in Turtle/RDF format
- **Multi-discipline Support**: PT, OT, SLP-specific rubrics and guidelines
- **Version Control**: Rubric versioning and change tracking
- **Custom Rules**: User-defined compliance criteria and organizational policies

### Interactive Reporting
- **HTML Reports**: Comprehensive compliance reports with interactive elements
- **Source Highlighting**: Click-to-navigate from findings to source document text
- **AI Chat Integration**: Contextual assistance for finding clarification
- **Confidence Indicators**: Visual uncertainty markers for AI-generated insights
- **Personalized Recommendations**: NLG-generated, actionable improvement suggestions

### Security & Privacy
- **Local Processing**: All AI/ML operations run locally, no external API calls
- **PHI Protection**: Automated detection and scrubbing of Protected Health Information
- **JWT Authentication**: Secure user management with password hashing (bcrypt)
- **Audit Logging**: Comprehensive activity tracking without PHI exposure
- **Data Encryption**: Sensitive data encrypted at rest in local database

### User Experience
- **Dashboard Analytics**: Historical compliance trends and performance metrics
- **Background Processing**: Non-blocking UI with progress indicators for long operations
- **Theme Support**: Light/dark mode with persistent user preferences
- **Responsive Design**: Optimized for desktop workflow with future mobile considerations

## Technical Implementation

### AI/ML Components
- **Local LLMs**: ctransformers with GGUF models (Meditron-7B clinical model) for compliance analysis
- **Embeddings**: sentence-transformers for semantic document understanding
- **NER Pipeline**: Biomedical Named Entity Recognition for clinical concept extraction
- **Fact Checking**: AI-powered verification of compliance findings
- **Risk Scoring**: Weighted algorithm considering severity and financial impact

### Data Management
- **SQLAlchemy Models**: Users, Documents, Rubrics, Analysis Results, Chat Sessions
- **CRUD Operations**: Abstracted database operations with proper error handling
- **Maintenance Jobs**: Automated cleanup of old reports and temporary files
- **Export Capabilities**: PDF generation and data export for compliance documentation

### Quality Assurance
- **Comprehensive Testing**: Unit, integration, and GUI tests with pytest framework
- **Code Quality**: Enforced via ruff linting and mypy type checking
- **Performance Monitoring**: System health indicators and processing metrics
- **Error Recovery**: Graceful degradation when AI models fail or are unavailable

## Future Enhancements
- **Advanced Analytics**: Machine learning for compliance trend prediction
- **Plugin Architecture**: Extensible framework for custom analysis modules
- **Cloud Integration**: Optional secure backup while maintaining local processing
- **Mobile Support**: Responsive UI adaptation for tablet and mobile devices
- **EHR Integration**: API connections to existing clinical documentation systems
