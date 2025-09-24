# Clinical Compliance Analyzer

This project is a desktop application for analyzing clinical documents for compliance with a set of rules.

## 🌟 Key Features

- **GUI Application**: A desktop application built with PySide6 for analyzing documents.
- **Document Parsing**: Supports parsing of various document formats, including PDF, DOCX, and plain text.
- **Compliance Analysis**: Analyzes documents against a set of rules defined in a rubric.
- **Medicare Guidelines**: Searches for relevant Medicare guidelines based on the analysis findings using a Retrieval-Augmented Generation (RAG) pipeline.
- **PHI Scrubbing**: Includes a feature to scrub Protected Health Information (PHI) from documents.

## 📂 Project Structure

The main application logic is contained within the `src/` directory.

```
.
├── src/
│   ├── core/              # Core application logic (compliance analysis, RAG, etc.)
│   ├── gui/               # GUI application code (PySide6)
│   ├── resources/         # Data files (rubrics, templates, etc.)
│   ├── main.py            # The GUI application entry point
│   └── ...
├── requirements.txt       # Project dependencies
└── ...
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** and **pip**: Ensure they are installed on your system.

### Running the Application

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the GUI Application:**
    ```bash
    python src/main.py
    ```

## 🧪 Running Tests

To run the test suite, you can use `pytest`:
```bash
pytest
```