# Testing Guide - Therapy Compliance Analyzer

This document provides comprehensive testing procedures for the Therapy Compliance Analyzer application, covering both manual testing workflows and automated test execution.

## Test Environment Setup

### Prerequisites
1. Python 3.11+ with virtual environment activated
2. All dependencies installed via `pip install -r requirements.txt`
3. Test data available in `tests/test_data/` directory
4. Local AI models downloaded and configured

### Running Automated Tests

```bash
# Run full test suite
pytest

# Run tests excluding slow AI model tests
pytest -m "not slow"

# Run with coverage reporting
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/gui/          # GUI tests only

# Run tests with verbose output
pytest -v -s
```

## Manual Testing Procedures

### 1. Application Startup & Authentication

**Objective:** Verify the application launches correctly and user authentication works.

**Test Steps:**
1. Launch the application via `python run_gui.py`
2. **Expected Result:** Main window appears with "Loading AI models..." status
3. Wait for AI models to load (status should change to "AI Models Ready" in green)
4. **Expected Result:** Application is ready for use with Analysis and Dashboard tabs visible

**Validation Points:**
- Window title shows "Therapy Compliance Analyzer"
- Menu bar contains File, Tools, Theme menus
- Status bar shows AI model loading progress
- No error dialogs appear during startup

### 2. Document Upload & Processing

**Objective:** Test document upload functionality and format support.

**Test Steps:**
1. Click "Upload Document" button in Analysis tab
2. Select a test document from `test_data/` (try PDF, DOCX, TXT formats)
3. **Expected Result:** Document content appears in left panel
4. **Expected Result:** Status bar shows "Loaded document: [filename]"
5. **Expected Result:** "Run Analysis" button becomes enabled

**Test Cases:**
- **PDF Document:** Upload `test_data/good_note_1.txt` (rename to .pdf for testing)
- **DOCX Document:** Create a sample Word document with therapy notes
- **TXT Document:** Upload `test_data/fake_note.txt`
- **Large Document:** Test with documents >10MB
- **Invalid Format:** Try uploading an image file (should show preview error)

### 3. Rubric Selection & Management

**Objective:** Verify rubric selection and management functionality.

**Test Steps:**
1. In Analysis tab, click the rubric dropdown
2. **Expected Result:** Available rubrics are listed (PT, OT, SLP compliance rubrics)
3. Select "PT Compliance Rubric"
4. **Expected Result:** Description appears showing rubric details
5. Go to Tools → Manage Rubrics
6. **Expected Result:** Rubric management dialog opens

**Validation Points:**
- Rubric dropdown populates with available rubrics
- Rubric descriptions display correctly
- Rubric management dialog allows CRUD operations
- TTL format rubrics are properly parsed and displayed

### 4. Compliance Analysis Workflow

**Objective:** Test the complete document analysis pipeline.

**Test Steps:**
1. Upload a test document (`test_data/good_note_1.txt`)
2. Select "PT Compliance Rubric" from dropdown
3. Click "Run Analysis" button
4. **Expected Result:** Progress bar appears and analysis begins
5. **Expected Result:** Status shows "Analysis in progress..."
6. Wait for completion (may take 30-60 seconds)
7. **Expected Result:** Analysis results appear in right panel
8. **Expected Result:** Interactive HTML report is displayed

**Validation Points:**
- Progress indicators work correctly
- Analysis completes without errors
- Results contain findings with risk levels
- Interactive elements (highlight links, chat links) are functional
- Confidence indicators are displayed for uncertain findings

### 5. Interactive Report Features

**Objective:** Test report interactivity and navigation features.

**Test Steps:**
1. Complete an analysis to generate a report
2. Click on a "highlight" link in the findings
3. **Expected Result:** Corresponding text is highlighted in source document
4. **Expected Result:** Document panel scrolls to highlighted text
5. Click on a "Discuss with AI" link
6. **Expected Result:** Chat dialog opens with contextual information
7. Test dispute functionality (if available)

**Validation Points:**
- Text highlighting works accurately
- Navigation between report and source document is smooth
- Chat integration provides relevant context
- Report formatting is professional and readable

### 6. Dashboard & Analytics

**Objective:** Verify dashboard functionality and historical data display.

**Test Steps:**
1. Click on "Dashboard" tab
2. **Expected Result:** Dashboard loads with compliance metrics
3. **Expected Result:** Charts and visualizations display (may be empty for new installations)
4. Click "Refresh" if available
5. **Expected Result:** Dashboard updates with latest data

**Validation Points:**
- Dashboard loads without errors
- Visualizations render correctly
- Historical data is displayed appropriately
- Refresh functionality works

### 7. Theme & UI Customization

**Objective:** Test theme switching and UI preferences.

**Test Steps:**
1. Go to Theme → Light
2. **Expected Result:** Application switches to light theme
3. Go to Theme → Dark  
4. **Expected Result:** Application switches to dark theme
5. Restart application
6. **Expected Result:** Theme preference is preserved

**Validation Points:**
- Theme changes apply immediately
- All UI elements respect theme colors
- Theme preference persists across sessions
- Text remains readable in both themes

### 8. Error Handling & Edge Cases

**Objective:** Test application behavior under error conditions.

**Test Steps:**
1. **Invalid Document:** Try uploading a corrupted file
2. **Expected Result:** Graceful error message, no application crash
3. **Network Issues:** Disconnect internet during analysis
4. **Expected Result:** Analysis continues (local processing)
5. **Large Document:** Upload a very large document (>50MB)
6. **Expected Result:** Appropriate handling or warning message
7. **Memory Pressure:** Run multiple analyses simultaneously
8. **Expected Result:** System handles load gracefully

### 9. Security & Privacy Features

**Objective:** Verify PHI protection and security measures.

**Test Steps:**
1. Upload a document containing mock PHI (names, dates, SSNs)
2. Run analysis and generate report
3. **Expected Result:** PHI is scrubbed and replaced with [REDACTED] placeholders
4. Check log files for any PHI exposure
5. **Expected Result:** No PHI appears in logs or temporary files

**Validation Points:**
- PHI scrubbing works correctly
- No sensitive data in logs
- Temporary files are cleaned up
- Local processing maintains privacy

### 10. Performance & Stability

**Objective:** Test application performance under normal usage.

**Test Steps:**
1. **Startup Time:** Measure application launch time
2. **Expected Result:** Application starts within 30 seconds
3. **Analysis Speed:** Time document analysis completion
4. **Expected Result:** Analysis completes within 2 minutes for typical documents
5. **Memory Usage:** Monitor memory consumption during analysis
6. **Expected Result:** Memory usage remains reasonable (<2GB)
7. **Concurrent Operations:** Test multiple simultaneous analyses
8. **Expected Result:** System handles concurrent operations

## Automated Test Coverage

### Unit Tests (`tests/unit/`)
- **Service Layer:** Test individual service classes in isolation
- **Database Operations:** CRUD operations and model validation
- **AI Components:** Mock-based testing of LLM and NLP services
- **Utilities:** Helper functions and configuration management

### Integration Tests (`tests/integration/`)
- **API Endpoints:** FastAPI route testing with test client
- **Service Integration:** End-to-end service interaction testing
- **Database Integration:** Real database operations with test data
- **File Processing:** Document parsing and analysis pipeline

### GUI Tests (`tests/gui/`)
- **Widget Functionality:** PyQt6 component testing with pytest-qt
- **User Interactions:** Simulated clicks, inputs, and navigation
- **Dialog Testing:** Modal dialogs and form validation
- **Theme Testing:** UI appearance and theme switching

## Test Data Management

### Synthetic Test Data
- **Location:** `tests/test_data/`
- **Content:** Synthetic therapy notes without real PHI
- **Formats:** TXT, PDF, DOCX samples for different document types
- **Compliance Scenarios:** Documents with known compliance issues for validation

### Test Rubrics
- **Location:** `tests/` directory
- **Files:** `pt_compliance_rubric.ttl`, `ot_compliance_rubric.ttl`
- **Purpose:** Validate rubric parsing and compliance rule application

## Continuous Integration

### Pre-commit Checks
```bash
# Code quality checks (must pass)
ruff check src/ tests/
mypy src/
ruff format src/ tests/

# Security scanning
bandit -r src/

# Test execution
pytest -m "not slow"
```

### Performance Benchmarks
- **Startup Time:** < 30 seconds
- **Document Analysis:** < 2 minutes for typical documents
- **Memory Usage:** < 2GB during normal operation
- **Test Suite:** < 5 minutes for full execution

## Troubleshooting Common Issues

### AI Model Loading Failures
- **Symptom:** "AI Models Failed" status in red
- **Solution:** Check model files in cache, verify internet connection for initial download
- **Logs:** Check console output for specific model loading errors

### Document Processing Errors
- **Symptom:** "Could not display preview" message
- **Solution:** Verify file format support, check file permissions
- **Workaround:** Try converting document to supported format

### Analysis Timeout Issues
- **Symptom:** Analysis hangs or takes excessive time
- **Solution:** Check system resources, restart application
- **Prevention:** Avoid very large documents, ensure adequate RAM

### GUI Responsiveness Issues
- **Symptom:** UI freezes during analysis
- **Solution:** Verify background worker threads are functioning
- **Check:** Task Manager for CPU/memory usage patterns
