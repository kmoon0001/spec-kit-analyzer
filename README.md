# Therapy Compliance Analyzer

This document provides a comprehensive overview of the Therapy Compliance Analyzer application, including its features, architecture, and instructions for getting started.

## 🌟 Features Overview

- **Secure User Authentication**: A robust login system with password management ensures secure access.
- **Interactive Dashboard**: Visualize compliance trends over time with a historical score chart and see a breakdown of the most common compliance issues.
- **AI-Powered Analysis Pipeline**:
    - **Advanced Preprocessing**: Includes a medical spell-checker to clean and correct text before analysis.
    - **Document Classification**: Automatically determines the document type (e.g., "Progress Note", "Evaluation") to provide better context to the AI.
    - **Hybrid Semantic Search**: A sophisticated RAG (Retrieval-Augmented Generation) pipeline uses a hybrid of keyword and semantic search to find the most relevant compliance rules for a given document.
    - **NLG for Personalized Tips**: The AI generates personalized, actionable tips for each finding, going beyond generic suggestions.
- **Enhanced Risk Scoring**: A weighted algorithm calculates a more meaningful compliance score based on the severity and financial impact of each finding.
- **Ethical & Transparent AI**:
    - **Uncertainty Handling**: The system flags and visually highlights findings the AI is not confident about.
    - **Formalized Limitations**: Every report includes a clear disclaimer about the capabilities and limitations of the AI models.
- **Database-Backed Rubric Manager**: A full GUI for adding, editing, and deleting compliance rubrics, with all changes immediately reflected in the analysis engine.
- **Automated Database Maintenance**: The application automatically purges old reports to manage disk space usage.
- **PDF Export**: Generates professional, audit-ready PDF reports of compliance analyses, complete with custom headers, footers, and HIPAA-compliant disclaimers. For more details, see the **[PDF Export Guide](docs/PDF_EXPORT_GUIDE.md)**.
- **Personal Development Framework**: Integrates the "7 Habits" framework to provide personalized feedback and track professional growth. This feature is fully configurable; see the **[Habits Framework Settings Guide](docs/HABITS_FRAMEWORK_SETTINGS.md)** for details.

## 📂 Project Architecture

The application is designed with a modular, service-oriented architecture that separates concerns and promotes maintainability.

- **Backend**: A robust backend API built with **FastAPI**. It handles all the heavy lifting, including AI analysis, database interactions, and user authentication.
- **Frontend**: A native desktop application built with **PyQt6**. This provides a responsive and feature-rich user interface.
- **Database**: Uses **SQLAlchemy** with a SQLite database to store user data, rubrics, and historical analysis reports.

### Directory Structure

The `src` directory is organized into modules, each with a specific responsibility:

```
.
├── src/
│   ├── api/                 # FastAPI application, broken into modular routers
│   │   ├── routers/
│   │   └── main.py
│   ├── core/                # Core services (Analysis, AI models, etc.)
│   ├── database/            # All database-related code (models, schemas, crud)
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── gui/                 # PyQt6 GUI application code
│   ├── resources/           # Data files (dictionaries, prompts, etc.)
│   ├── utils/               # Shared utility functions
│   ├── auth.py              # User authentication and JWT management
│   ├── config.py            # Application configuration management
│   └── logging_config.py    # Logging setup
├── tests/                   # A comprehensive suite of fast, isolated unit tests
├── config.yaml              # Main application configuration
└── requirements.txt         # Project dependencies
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** and **pip**.
- **Git** for cloning the repository.
- **System Dependencies**: This project relies on system-level libraries that must be installed before the Python packages.
  - **Cairo**: Required for `pycairo`, which is used for PDF and graphics functionality.
  - **Tesseract**: Required for `pytesseract`, used for Optical Character Recognition (OCR).

  For Debian/Ubuntu-based systems, install these with:
  ```bash
  sudo apt-get update && sudo apt-get install -y libcairo2-dev tesseract-ocr
  ```
  For other operating systems (e.g., macOS, Windows), please use your system's package manager (like Homebrew or Chocolatey) to install `cairo` and `tesseract`.

### 1. Installation

Clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

For development, which includes running tests and linters, install the additional development dependencies:
```bash
pip install -r requirements-dev.txt
```

### 2. Configuration and Setup

The application uses `config.yaml` for most settings, but sensitive data like the `SECRET_KEY` must be handled securely using environment variables.

1.  **Create a `.env` file**: In the project root, create a `.env` file to store your secret key. The application uses `python-dotenv` to load this file automatically.
    ```.env
    # Generate a new key for your instance using: openssl rand -hex 32
    SECRET_KEY="YOUR_SUPER_SECRET_KEY_HERE"
    ```
    **Note**: The environment variable will always take precedence over the `secret_key` value in `config.yaml`.

2.  **Initialize the Database**: Run the initialization script to set up the database schema.
    ```bash
    python initialize_db.py
    ```

3.  **Create a Default User**: Create a default user to log in to the application for the first time.
    ```bash
    python create_default_user.py
    ```

### 3. Running the Application

Launch the application using the main script, which starts both the backend API server and the frontend GUI.

```bash
python start_app.py
```
The GUI application will start, and you can log in with the default user credentials. The backend API will run in the background, with logs saved to `api_server.log` and `api_server.err.log`.

## 🧪 Running Tests

The project includes a comprehensive suite of unit, integration, and GUI tests to ensure code quality and stability.

To run the full test suite, use `pytest`:
```bash
python -m pytest
```

For more detailed information on the testing strategy, including how to run specific tests, generate coverage reports, or write new tests, please refer to the **[Comprehensive Testing Guide](docs/TESTING_GUIDE_COMPREHENSIVE.md)**.

## ⚙️ Performance Optimization

The application automatically detects your system and applies optimal settings based on available RAM:

- **6-8GB RAM**: Conservative mode (CPU-only, small cache)
- **8-12GB RAM**: Balanced mode (GPU optional, moderate cache)
- **12-16GB+ RAM**: Aggressive mode (full GPU, large cache)

You can access and change performance settings via the application menu: `Tools → Performance Settings`.

## 🤔 Troubleshooting

### App Won't Start
- **Check Python Version**: Ensure you are using Python 3.10 or newer (`python --version`).
- **Reinstall Dependencies**: If you suspect a corrupted package, you can force a re-installation:
  ```bash
  pip install -r requirements.txt --force-reinstall
  ```

### "AI Models Failed" Error
- **Internet Connection**: The first time you run the app, it needs to download the AI models. Ensure you have an internet connection.
- **Restart the App**: Subsequent runs use a local cache. If you see this error, try restarting the application.

### Performance Issues
- **High Memory Usage**: Switch to the "Conservative" profile in `Tools → Performance Settings`.
- **Slow Analysis**: If you have a dedicated GPU, ensure GPU acceleration is enabled in the performance settings.
- **UI Freezing**: Close other resource-intensive applications and restart the app.

### Import Errors
- **Virtual Environment**: Ensure your virtual environment is activated before running the application.
- **Verify Installation**: You can run these commands to quickly check if the core packages are installed correctly:
  ```bash
  python -c "import PyQt6; print('✅ GUI ready')"
  python -c "import fastapi; print('✅ API ready')"
  ```

## 📖 API Documentation

The API documentation is automatically generated by FastAPI and is available at `http://127.0.0.1:8000/docs` after you have started the application.