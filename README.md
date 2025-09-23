# Clinical Compliance Analyzer

This project is a desktop application for analyzing clinical documents for compliance with a set of rules. It also includes a backend API for a web-based version of the tool.

## 🌟 Key Features

- **GUI Application**: A desktop application built with PySide6 for analyzing documents.
- **Backend API**: A backend API built with FastAPI for a web-based version of the tool.
- **Document Parsing**: Supports parsing of various document formats, including PDF and DOCX.
- **Compliance Analysis**: Analyzes documents against a set of rules defined in a rubric.
- **Medicare Guidelines**: Searches for relevant Medicare guidelines based on the analysis findings.

## 📂 Project Structure

```
.
├── src/
│   ├── api/
│   │   └── main.py          # The FastAPI application
│   ├── core/
│   │   └── ...              # Core application logic
│   ├── gui/
│   │   └── ...              # GUI application code
│   ├── resources/
│   │   └── ...              # Data files (rubrics, etc.)
│   └── main.py              # The GUI application entry point
├── requirements.txt         # Project dependencies
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

3.  **Run the Backend API:**
    ```bash
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main:app
    ```
    The API will be accessible at `http://localhost:8000`.

## 🧪 Running Tests

To run the test suite, you can use `pytest`:
```bash
pytest
```
