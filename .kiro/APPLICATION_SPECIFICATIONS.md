# 📊 Therapy Compliance Analyzer - Complete Application Specifications

## 🎯 System Overview

The Therapy Compliance Analyzer is a sophisticated AI-powered desktop application designed for clinical therapists to analyze documentation compliance with Medicare and regulatory guidelines. It employs a hybrid architecture with local AI processing to ensure HIPAA compliance and data privacy.

---

## 🏗️ Architecture Specifications

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Application                           │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   PySide6 GUI   │   FastAPI API   │    Local AI/ML Stack        │
│   (Frontend)    │   (Backend)     │    (Processing)             │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ • Main Window   │ • REST Endpoints│ • LLM Service (Meditron-7B) │
│ • 4 Main Tabs   │ • JWT Auth      │ • NER Ensemble (2 models)   │
│ • Dialogs       │ • Rate Limiting │ • Hybrid Retrieval (RAG)    │
│ • Workers       │ • Error Handling│ • Document Processing       │
│ • Components    │ • Background    │ • PHI Scrubbing             │
│ • Widgets       │   Tasks         │ • Compliance Analysis       │
└─────────────────┴─────────────────┴─────────────────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  SQLite Database    │
                │  (Local Storage)    │
                │  • Users & Auth     │
                │  • Analysis Results │
                │  • Rubrics & Rules  │
                │  • Chat History     │
                │  • Habit Tracking   │
                └─────────────────────┘
```

### Core Design Principles
- **Privacy-First**: All AI processing occurs locally
- **Modular Architecture**: Clear separation of concerns
- **Service Layer Pattern**: Business logic abstracted from UI/API
- **Dependency Injection**: FastAPI DI for service management
- **Background Processing**: Non-blocking operations with QThread workers
- **Hybrid Processing**: Desktop GUI + API backend for flexibility

---

## 💻 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space (for AI models and data)
- **CPU**: Dual-core 2.0GHz (Quad-core recommended)
- **Display**: 1024x768 minimum (1920x1080 recommended)

### Recommended Requirements
- **RAM**: 8-16GB for optimal AI model performance
- **Storage**: 4GB+ for models, cache, and analysis history
- **CPU**: Quad-core 3.0GHz+ for faster analysis
- **GPU**: Optional - CUDA-compatible for potential acceleration
- **Network**: Internet connection for initial model download only

### Performance Specifications
- **Startup Time**: <5 seconds (after initial model download)
- **Exit Time**: <500ms (optimized worker cleanup)
- **Analysis Time**: 30-60 seconds per document
- **Memory Usage**: 1-2GB during normal operation
- **Model Storage**: ~500MB for AI models (downloaded once)

---

## 🤖 AI/ML Specifications

### Language Model (LLM)
**Primary Model**: Meditron-7B (Medical Domain Specialized)
- **Repository**: TheBloke/meditron-7B-GGUF
- **File**: meditron-7b.Q4_K_M.gguf (4-bit quantized)
- **Size**: ~4.1GB
- **Context Length**: 4,096 tokens
- **Backend**: ctransformers (GGUF format)
- **Specialization**: Medical and clinical text analysis

**Model Profiles Available**:
1. **Clinical Q4 Balanced** (Default)
   - File: meditron-7b.Q4_K_M.gguf
   - RAM: 4-16GB systems
   - Balance of speed and quality

2. **Clinical Q5 Quality**
   - File: meditron-7b.Q5_K_M.gguf
   - RAM: 16-24GB systems
   - Higher quality analysis

3. **Clinical Q6 Precision**
   - File: meditron-7b.Q6_K.gguf
   - RAM: 24GB+ systems
   - Maximum precision

**Generation Parameters**:
```yaml
temperature: 0.1          # Low for consistent compliance analysis
max_new_tokens: 1024      # Sufficient for detailed findings
top_p: 0.9               # Nucleus sampling
repeat_penalty: 1.1      # Prevent repetition
stop_sequences:          # Analysis completion markers
  - "</analysis>"
  - "\n\n---"
```

### Named Entity Recognition (NER) Ensemble
**Dual-Model Ensemble for Maximum Coverage**:

1. **Primary NER Model**: d4data/biomedical-ner-all
   - **Specialization**: General biomedical entities
   - **Coverage**: Diseases, medications, procedures, anatomy
   - **Architecture**: BERT-based transformer
   - **Performance**: High recall for medical terms

2. **Secondary NER Model**: OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M
   - **Specialization**: Pathology and diagnostic entities
   - **Coverage**: Pathological conditions, diagnostic terms
   - **Architecture**: Optimized transformer (109M parameters)
   - **Performance**: High precision for diagnostic entities

**Ensemble Strategy**:
- **Parallel Processing**: Both models analyze text simultaneously
- **Entity Merging**: Sophisticated overlap resolution algorithm
- **Confidence Scoring**: Combined confidence from both models
- **Deduplication**: Intelligent removal of redundant entities

### Retrieval System (RAG)
**Hybrid Retrieval Architecture**:

**Dense Retrieval**:
- **Model**: pritamdeka/S-PubMedBert-MS-MARCO
- **Specialization**: Medical literature and clinical text
- **Embedding Dimension**: 768
- **Index**: FAISS for efficient similarity search
- **Top-K**: 10 most relevant rules retrieved

**Sparse Retrieval**:
- **Algorithm**: BM25 (Okapi variant)
- **Tokenization**: Medical-aware preprocessing
- **Scoring**: TF-IDF with medical term weighting

**Reranking** (Optional):
- **Model**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **Purpose**: Refine retrieval results for better relevance
- **Configuration**: Configurable enable/disable

**Fusion Strategy**:
- **RRF (Reciprocal Rank Fusion)**: k=60
- **Weighting**: Balanced dense/sparse combination
- **Caching**: Embedding cache for performance

### Document Processing Pipeline
**Multi-Stage Processing**:

1. **Document Classification**
   - **Purpose**: Identify document type (Progress Note, Evaluation, etc.)
   - **Method**: LLM-based classification with prompt engineering
   - **Accuracy**: >90% for standard clinical documents

2. **Text Preprocessing**
   - **Medical Spell-checking**: Clinical terminology correction
   - **Normalization**: Standardize medical abbreviations
   - **Cleaning**: Remove artifacts and formatting issues

3. **Smart Chunking**
   - **Strategy**: Context-aware segmentation
   - **Overlap**: 100 characters between chunks
   - **Max Length**: 50,000 characters per document
   - **Preservation**: Maintain clinical context across chunks

4. **PHI Scrubbing**
   - **Engine**: Microsoft Presidio (with fallbacks)
   - **Detection**: Names, dates, SSNs, addresses, phone numbers
   - **Replacement**: Configurable tokens (default: [REDACTED])
   - **Accuracy**: >95% PHI detection rate

### Fact Checking & Verification
**Model**: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext
- **Purpose**: Verify medical claims and compliance statements
- **Training**: PubMed abstracts and full-text articles
- **Confidence Scoring**: Uncertainty quantification for findings
- **Fallback**: Graceful degradation when model unavailable

---

## 🗄️ Database Specifications

### Database Engine
- **Type**: SQLite (local file-based)
- **File**: compliance.db
- **ORM**: SQLAlchemy 2.0 with async support
- **Connection Pool**: 10 connections, 20 max overflow
- **Optimizations**: SQLite-specific performance tuning enabled

### Schema Overview
**Core Tables**:
1. **Users**: Authentication and user management
2. **ComplianceRubric**: Regulatory guidelines and rules
3. **AnalysisReport**: Document analysis results and metadata
4. **Finding**: Individual compliance findings with evidence
5. **ChatSession**: AI chat conversations and history
6. **HabitGoal**: 7 Habits framework integration
7. **HabitAchievement**: Progress tracking and gamification

**Relationships**:
- Users → AnalysisReports (one-to-many)
- AnalysisReports → Findings (one-to-many)
- Users → ChatSessions (one-to-many)
- Users → HabitGoals (one-to-many)

### Data Storage
- **Analysis Results**: JSON format for flexibility
- **Document Embeddings**: Binary storage for vector search
- **User Preferences**: Encrypted sensitive data
- **Audit Logs**: Activity tracking without PHI

---

## 🔒 Security Specifications

### Authentication & Authorization
- **Method**: JWT (JSON Web Tokens)
- **Algorithm**: HS256
- **Token Expiry**: 30 minutes (configurable)
- **Password Hashing**: bcrypt with salt
- **Session Management**: Secure token storage and refresh

### Input Validation
**SecurityValidator Class**:
- **File Validation**: Extension, size, path traversal protection
- **Parameter Validation**: Discipline, analysis mode, user inputs
- **Text Sanitization**: XSS prevention, injection protection
- **Size Limits**: 50MB max file size, 10,000 char text inputs

### Privacy Protection
- **Local Processing**: All AI operations on-device
- **PHI Scrubbing**: Automatic PII detection and removal
- **Data Encryption**: Sensitive database fields encrypted
- **No External Calls**: Zero data transmission to external services
- **Audit Logging**: Activity tracking without PHI exposure

### Rate Limiting
- **API Protection**: slowapi middleware
- **Request Limits**: Configurable per-endpoint limits
- **Abuse Prevention**: Automatic blocking of excessive requests

---

## 📊 Performance Specifications

### Caching Strategy
**Multi-Level Caching**:
1. **LRU Cache**: Configuration and settings (@lru_cache)
2. **Disk Cache**: Embeddings and model outputs
3. **Memory Cache**: Frequently accessed analysis results
4. **Database Cache**: Query result caching

### Background Processing
**QThread Workers**:
- **AnalysisWorker**: Document analysis operations
- **DashboardWorker**: Analytics data loading
- **MetaAnalyticsWorker**: System metrics collection
- **ChatWorker**: AI conversation processing

**APScheduler Jobs**:
- **Database Maintenance**: Daily cleanup and optimization
- **File Cleanup**: Temporary file purging
- **Cache Management**: Memory pressure-based eviction

### Memory Management
- **Model Loading**: Lazy initialization of AI models
- **Garbage Collection**: Automatic cleanup of large objects
- **Memory Monitoring**: psutil-based resource tracking
- **Optimization**: Efficient data structures and algorithms

---

## 🎨 User Interface Specifications

### Main Window Layout
**Dimensions**:
- **Minimum Size**: 900x600 pixels
- **Default Size**: 1200x800 pixels
- **Scaling**: Responsive layout adapts to window size
- **DPI Awareness**: High-DPI display support

**Tab Structure**:
1. **Analysis Tab** (Primary workspace)
   - Left Column (25%): Document upload, rubric selection
   - Middle Column (30%): Settings, report sections
   - Right Column (45%): Results, integrated chat

2. **Dashboard Tab**: Historical analytics and trends
3. **Mission Control Tab**: System monitoring and health
4. **Settings Tab**: User preferences and configuration

### Visual Design
**Theme System**:
- **Medical Theme**: Professional healthcare color palette
- **Primary Color**: #4a90e2 (medical blue)
- **Secondary Colors**: Greens, grays for medical context
- **Typography**: Segoe UI, clean and readable
- **Icons**: Medical-themed emoji and professional icons

**Responsive Features**:
- **Adaptive Layout**: Columns resize based on window size
- **Scalable Components**: All UI elements scale proportionally
- **Theme Toggle**: Light/Dark mode with persistent preferences
- **Accessibility**: High contrast, keyboard navigation support

### Interactive Elements
**Modern Components**:
- **Animated Buttons**: Hover effects and micro-interactions
- **Loading Spinners**: Visual feedback for operations
- **Progress Bars**: Real-time analysis progress
- **Tooltips**: Contextual help and guidance
- **Modal Dialogs**: Settings, chat, report viewing

---

## 📈 Analytics & Reporting Specifications

### Report Generation
**HTML Reports**:
- **Template**: Professional medical document styling
- **Interactivity**: Click-to-highlight source text
- **Sections**: 8 configurable report sections
- **Navigation**: Table of contents and internal links
- **Export**: PDF generation with WeasyPrint

**Report Sections**:
1. **Executive Summary**: Overview and key metrics
2. **Detailed Findings**: Evidence-based compliance issues
3. **Risk Assessment**: Financial and regulatory risk analysis
4. **Recommendations**: Actionable improvement suggestions
5. **Regulatory Citations**: Specific regulation references
6. **Action Plan**: Step-by-step improvement guide
7. **AI Transparency**: Model confidence and limitations
8. **Improvement Strategies**: Long-term enhancement tips

### Dashboard Analytics
**Metrics Tracked**:
- **Compliance Scores**: Historical trends and patterns
- **Document Analysis**: Types, frequency, and outcomes
- **Risk Distribution**: High/Medium/Low risk findings
- **Performance Metrics**: Analysis speed and accuracy
- **Usage Statistics**: System utilization and patterns

**Visualizations**:
- **Line Charts**: Compliance trends over time
- **Bar Charts**: Finding distribution by category
- **Pie Charts**: Risk level proportions
- **Heatmaps**: Compliance patterns by document type

---

## 🔧 Configuration Specifications

### Configuration Files
**config.yaml** (Main configuration):
```yaml
database:
  url: sqlite:///./compliance.db
  echo: false

models:
  generator: TheBloke/meditron-7B-GGUF
  generator_filename: meditron-7b.Q4_K_M.gguf
  retriever: pritamdeka/S-PubMedBert-MS-MARCO
  ner_ensemble:
    - d4data/biomedical-ner-all
    - OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M

llm:
  model_type: ctransformers
  context_length: 4096
  generation_params:
    temperature: 0.1
    max_new_tokens: 1024

retrieval:
  similarity_top_k: 10
  rrf_k: 60
  batch_size: 16

analysis:
  confidence_threshold: 0.75
  max_document_length: 50000
```

**.env** (Environment variables):
```bash
DATABASE_URL="sqlite:///./compliance.db"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Feature Flags
- **Habits Framework**: Enable/disable 7 Habits integration
- **Director Dashboard**: Advanced analytics for administrators
- **AI Mocks**: Use mock services for testing
- **Reranker**: Enable/disable retrieval reranking

---

## 🧪 Testing Specifications

### Test Suite Structure
**Test Categories**:
1. **Unit Tests**: Individual component testing (fast)
2. **Integration Tests**: Service interaction testing (medium)
3. **GUI Tests**: User interface testing with pytest-qt (slow)
4. **Stability Tests**: Stress testing and edge cases (slow)

**Test Markers**:
- `@pytest.mark.slow`: Tests that take >5 seconds
- `@pytest.mark.stability`: Stress and edge case tests
- `@pytest.mark.skip`: Conditionally skipped tests
- `@pytest.mark.gui`: GUI-specific tests requiring display

### Expected Test Performance
**Timing Estimates**:
- **Unit Tests**: 30-60 seconds (fast, isolated)
- **Integration Tests**: 2-5 minutes (database, API)
- **GUI Tests**: 5-10 minutes (UI interactions)
- **Full Suite**: 10-15 minutes (all tests)
- **Excluding Slow**: 2-3 minutes (rapid development)

**Test Coverage**:
- **Target Coverage**: >80% for core functionality
- **Critical Paths**: >95% for security and compliance logic
- **GUI Coverage**: Basic functionality and error handling
- **Integration Coverage**: End-to-end workflow validation

---

## 🚀 Deployment Specifications

### Local Development
**Startup Commands**:
```bash
# API Server (Terminal 1)
python scripts/run_api.py
# or
uvicorn src.api.main:app --reload --port 8001

# GUI Application (Terminal 2)
python scripts/run_gui.py
```

### Production Deployment
**Requirements**:
- Python 3.11+ virtual environment
- All dependencies from requirements.txt
- Proper environment variables configured
- Sufficient system resources (4GB+ RAM)

**Startup Process**:
1. **Environment Setup**: Virtual environment activation
2. **Dependency Installation**: pip install requirements
3. **Configuration**: Environment variables and config files
4. **Database Initialization**: Automatic on first run
5. **Model Download**: AI models downloaded on first use
6. **Service Startup**: API server then GUI application

### Resource Monitoring
**System Metrics**:
- **CPU Usage**: Monitor during analysis operations
- **Memory Usage**: Track AI model memory consumption
- **Disk Usage**: Monitor cache and database growth
- **Network**: Initial model download only

---

## 📋 Maintenance Specifications

### Automated Maintenance
**Scheduled Jobs** (APScheduler):
- **Daily Database Cleanup**: Remove old temporary data
- **File Purging**: Clean temporary uploads and cache
- **Performance Optimization**: Database vacuum and analyze
- **Health Checks**: System status monitoring

### Manual Maintenance
**Periodic Tasks**:
- **Model Updates**: Check for newer AI model versions
- **Dependency Updates**: Security patches and improvements
- **Configuration Review**: Optimize settings for usage patterns
- **Performance Tuning**: Adjust cache sizes and worker counts

### Monitoring & Logging
**Log Categories**:
- **Application Logs**: General operation and errors
- **Security Logs**: Authentication and validation events
- **Performance Logs**: Timing and resource usage
- **Audit Logs**: User actions (without PHI)

**Log Levels**:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Potential issues and fallbacks
- **ERROR**: Error conditions requiring attention
- **CRITICAL**: Severe errors affecting functionality

---

This comprehensive specification document provides complete technical details for the Therapy Compliance Analyzer, covering all aspects from system requirements to deployment considerations.