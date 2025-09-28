# Therapy Compliance Analyzer - Complete Workflow Documentation

This document provides a comprehensive overview of the end-to-end workflow for the Therapy Compliance Analyzer, detailing both user interactions and system processes across the hybrid FastAPI backend + PyQt6 frontend architecture.

## System Architecture Overview

The Therapy Compliance Analyzer uses a modular architecture with clear separation of concerns:

- **Frontend**: PyQt6 desktop application with tabbed interface
- **Backend**: FastAPI with modular routers and dependency injection
- **Database**: SQLAlchemy ORM with local SQLite storage
- **AI/ML**: Local processing with ctransformers, sentence-transformers, and hybrid retrieval
- **Security**: JWT authentication, PHI scrubbing, and local-only processing

## 1. Application Startup & Initialization

### User Experience
- User launches the application via `python run_gui.py`
- Main window appears with "Loading AI models..." status indicator
- Application becomes ready when AI models are loaded successfully

### System Process
1. **GUI Initialization**: PyQt6 main window creates base UI components
2. **Backend Startup**: FastAPI server starts with lifespan management
3. **AI Model Loading**: Background worker loads local LLM and embedding models
4. **Database Connection**: SQLAlchemy establishes connection to local SQLite database
5. **Configuration Loading**: YAML config files parsed and validated
6. **Service Initialization**: All core services (analysis, retrieval, etc.) are instantiated

### Technical Components
- `src/gui/main_window.py`: Main application window and UI setup
- `src/api/main.py`: FastAPI application with lifespan management
- `src/core/analysis_service.py`: Core service coordination
- `src/database/database.py`: Database connection and session management

## 2. User Authentication & Session Management

### User Experience
- Application loads directly to main interface (authentication simplified for local use)
- User status displayed in status bar
- Secure session management for API calls

### System Process
1. **JWT Token Generation**: Secure tokens created for API authentication
2. **Session Persistence**: User preferences and session state maintained
3. **Role-based Access**: Admin vs. regular user permissions enforced
4. **Security Headers**: All API calls include proper authentication headers

### Technical Components
- `src/auth.py`: JWT token management and user authentication
- `src/database/models.py`: User model with encrypted password storage
- `src/api/routers/auth.py`: Authentication endpoints and middleware

## 3. Dashboard & Historical Analytics

### User Experience
- Dashboard tab shows compliance trends and performance metrics
- Interactive charts display historical analysis data
- Refresh capability to update with latest information

### System Process
1. **Data Aggregation**: Historical analysis results queried from database
2. **Metrics Calculation**: Compliance scores, trend analysis, and performance indicators
3. **Visualization Rendering**: Charts and graphs generated using matplotlib
4. **Background Updates**: Dashboard data refreshed via worker threads

### Technical Components
- `src/gui/widgets/dashboard_widget.py`: Dashboard UI components and charts
- `src/gui/workers/dashboard_worker.py`: Background data loading
- `src/api/routers/dashboard.py`: Dashboard data API endpoints

## 4. Document Upload & Preprocessing

### User Experience
- User clicks "Upload Document" and selects file via file dialog
- Document content preview appears in left panel
- Support for PDF, DOCX, and TXT formats with OCR for scanned documents

### System Process
1. **File Validation**: Document format verification and size limits
2. **Content Extraction**: 
   - PDF: `pdfplumber` for text extraction
   - DOCX: `python-docx` for Word document processing
   - Images/Scanned PDFs: `pytesseract` OCR processing
3. **Text Preprocessing**: Medical spell-checking, cleaning, and normalization
4. **PHI Scrubbing**: Automated detection and redaction of Protected Health Information
5. **Temporary Storage**: Secure temporary file management with automatic cleanup

### Technical Components
- `src/parsing.py`: Multi-format document parsing and text extraction
- `src/core/preprocessing_service.py`: Text cleaning and medical spell-checking
- `src/core/phi_scrubber.py`: PHI detection and anonymization
- `src/config.py`: File upload settings and temporary directory management

## 5. Rubric Selection & Management

### User Experience
- Dropdown selector shows available compliance rubrics (PT, OT, SLP)
- Rubric description displays when selected
- Tools menu provides rubric management interface

### System Process
1. **Rubric Loading**: TTL format compliance rules parsed and indexed
2. **Rule Validation**: Compliance rule syntax and structure verification
3. **Discipline Mapping**: Rubrics associated with appropriate therapy disciplines
4. **Version Control**: Rubric versioning and change tracking

### Technical Components
- `src/core/rubric_loader.py`: TTL format parsing and rule loading
- `src/gui/dialogs/rubric_manager_dialog.py`: Rubric management UI
- `src/resources/*.ttl`: Compliance rubric files in Turtle format
- `src/api/routers/compliance.py`: Rubric management API endpoints

## 6. AI-Powered Document Analysis Pipeline

### User Experience
- User selects rubric and clicks "Run Analysis"
- Progress bar shows analysis status
- Background processing allows continued UI interaction

### System Process

#### Step 6.1: Document Classification
- **Purpose**: Determine document type for context-aware analysis
- **Process**: Local LLM classifies document (Progress Note, Evaluation, Treatment Plan, etc.)
- **Output**: Document type with confidence score

#### Step 6.2: Smart Text Chunking
- **Purpose**: Segment document while preserving medical context
- **Process**: Intelligent chunking based on clinical structure and content
- **Output**: Contextually meaningful text segments for analysis

#### Step 6.3: Named Entity Recognition (NER)
- **Purpose**: Extract clinical concepts and medical terminology
- **Process**: Biomedical NER models identify entities, conditions, treatments
- **Output**: Structured entity list with confidence scores

#### Step 6.4: Hybrid Retrieval (RAG Pipeline)
- **Purpose**: Find relevant compliance rules for document content
- **Process**: 
  - Semantic search using sentence-transformers embeddings
  - Keyword search using BM25 algorithm
  - Hybrid ranking combines both approaches
- **Output**: Ranked list of applicable compliance rules

#### Step 6.5: Compliance Analysis
- **Purpose**: Identify compliance issues using retrieved rules
- **Process**: Local LLM analyzes document against compliance guidelines
- **Output**: Detailed findings with evidence and explanations

#### Step 6.6: Fact Checking & Verification
- **Purpose**: Validate AI-generated findings for accuracy
- **Process**: Secondary AI model verifies compliance findings
- **Output**: Confidence scores and dispute flags for uncertain findings

#### Step 6.7: Personalized Recommendation Generation
- **Purpose**: Create actionable improvement suggestions
- **Process**: NLG service generates context-specific recommendations
- **Output**: Personalized tips tailored to document type and findings

### Technical Components
- `src/core/document_classifier.py`: AI-powered document type detection
- `src/core/smart_chunker.py`: Context-aware text segmentation
- `src/core/ner.py`: Biomedical named entity recognition pipeline
- `src/core/hybrid_retriever.py`: Semantic + keyword search system
- `src/core/compliance_analyzer.py`: Core compliance analysis logic
- `src/core/fact_checker_service.py`: AI-powered finding verification
- `src/core/nlg_service.py`: Natural language generation for recommendations

## 7. Risk Scoring & Uncertainty Quantification

### User Experience
- Overall compliance score displayed prominently
- Individual findings show risk levels (High/Medium/Low)
- Confidence indicators highlight uncertain AI predictions

### System Process
1. **Risk Assessment**: Each finding evaluated for severity and financial impact
2. **Weighted Scoring**: Algorithm considers regulatory priority and reimbursement risk
3. **Confidence Calculation**: AI uncertainty quantified and displayed
4. **Aggregation**: Individual scores combined into overall compliance metric

### Technical Components
- `src/core/risk_scoring_service.py`: Weighted risk calculation algorithms
- `src/core/compliance_analyzer.py`: Confidence scoring and uncertainty handling

## 8. Interactive Report Generation

### User Experience
- Comprehensive HTML report displays in right panel
- Interactive elements allow navigation between report and source document
- Professional formatting suitable for compliance documentation

### System Process
1. **Report Compilation**: Analysis results structured into comprehensive report
2. **Template Rendering**: HTML template populated with findings and metadata
3. **Interactive Elements**: Click-to-highlight and chat integration links embedded
4. **Styling Application**: Professional medical document formatting applied

### Technical Components
- `src/core/report_generator.py`: Report compilation and HTML generation
- `src/resources/report_template.html`: Professional report template
- `src/core/habit_mapper.py`: 7 Habits framework for improvement strategies

## 9. Interactive Features & User Actions

### Source Document Highlighting
- **User Action**: Click highlight link in report findings
- **System Process**: 
  1. Parse URL to extract text location information
  2. Search document content for matching text
  3. Highlight and scroll to relevant section
  4. Switch to document view tab automatically

### AI Chat Integration
- **User Action**: Click "Discuss with AI" link for specific finding
- **System Process**:
  1. Open chat dialog with contextual information pre-loaded
  2. Enable conversation about specific compliance issue
  3. Provide additional clarification and guidance
  4. Maintain chat history for reference

### Finding Dispute Mechanism
- **User Action**: Flag incorrect or questionable findings
- **System Process**:
  1. Mark finding as disputed in database
  2. Visual indication in report (strikethrough, red background)
  3. Collect user feedback for model improvement
  4. Track dispute patterns for quality assurance

### Technical Components
- `src/gui/main_window.py`: URL handling and navigation logic
- `src/gui/dialogs/chat_dialog.py`: AI chat interface and conversation management
- `src/core/chat_service.py`: Contextual AI assistance backend

## 10. Data Persistence & Management

### User Experience
- Analysis history automatically saved and accessible via dashboard
- User preferences (theme, settings) persist across sessions
- Secure local storage with no external data transmission

### System Process
1. **Analysis Storage**: Complete analysis results saved to local database
2. **User Preferences**: Settings and customizations persisted locally
3. **Audit Logging**: User actions logged for compliance (without PHI)
4. **Data Cleanup**: Automated maintenance removes old temporary files
5. **Backup Preparation**: Analysis data structured for potential export

### Technical Components
- `src/database/models.py`: SQLAlchemy ORM models for all data entities
- `src/database/crud.py`: Database operations and query abstractions
- `src/core/database_maintenance_service.py`: Automated cleanup and optimization

## 11. Security & Privacy Workflow

### Privacy Protection
- **Local Processing**: All AI operations run locally, no external API calls
- **PHI Scrubbing**: Automated detection and redaction throughout pipeline
- **Secure Storage**: Database encryption and secure file handling
- **Audit Trail**: Comprehensive logging without sensitive data exposure

### Security Measures
- **Authentication**: JWT tokens with secure password hashing
- **Input Validation**: Pydantic schemas validate all data inputs
- **Rate Limiting**: API protection against abuse and overload
- **Error Handling**: Graceful degradation without information leakage

### Technical Components
- `src/core/phi_scrubber.py`: Comprehensive PHI detection and anonymization
- `src/auth.py`: Secure authentication and session management
- `src/database/schemas.py`: Input validation and data sanitization

## 12. System Maintenance & Health Monitoring

### Automated Maintenance
- **Scheduled Jobs**: APScheduler runs daily maintenance tasks
- **File Cleanup**: Temporary uploads and cache files automatically purged
- **Database Optimization**: Regular database maintenance and optimization
- **Health Checks**: System status monitoring and error detection

### Performance Monitoring
- **Resource Usage**: Memory and CPU monitoring during AI operations
- **Processing Times**: Analysis duration tracking and optimization
- **Error Rates**: System reliability and failure pattern analysis
- **User Experience**: Response time and UI performance metrics

### Technical Components
- `src/core/database_maintenance_service.py`: Automated system maintenance
- `src/api/routers/health.py`: System health monitoring endpoints
- `src/api/main.py`: Background scheduler and maintenance job coordination

## Error Handling & Recovery

### Graceful Degradation
- **AI Model Failures**: Fallback mechanisms when models unavailable
- **Network Issues**: Continued operation during connectivity problems
- **Resource Constraints**: Adaptive behavior under memory/CPU pressure
- **Data Corruption**: Recovery procedures for damaged files or database

### User Communication
- **Meaningful Messages**: Clear, actionable error messages for users
- **Progress Indicators**: Transparent communication of system status
- **Recovery Guidance**: Specific steps for resolving common issues
- **Support Information**: Contact details and troubleshooting resources

This comprehensive workflow ensures that the Therapy Compliance Analyzer provides a robust, secure, and user-friendly experience for clinical compliance analysis while maintaining the highest standards of privacy and data protection.