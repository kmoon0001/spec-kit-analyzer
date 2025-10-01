# Therapy Compliance Analyzer

This project is an advanced, AI-powered desktop application designed to help clinical therapists analyze documentation for compliance with Medicare and other regulatory guidelines. It uses a suite of local AI models to provide in-depth analysis, personalized feedback, and historical trend tracking, all while ensuring data privacy by processing everything on the user's machine.

## 🌟 Key Features

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



3
## 📂 Project Architecture

The application is composed of a Python backend API and a desktop GUI.

- **Backend**: A modular API built with **FastAPI** that handles the AI analysis, database interactions, and user authentication.
- **Frontend**: A desktop application built with **PyQt6** that provides the user interface for document analysis and dashboard visualization.
- **Database**: Uses **SQLAlchemy** with a SQLite database to store user data, rubrics, and historical analysis reports.

```
.
├── src/
│   ├── api/                 # FastAPI application, broken into modular routers
│   │   ├── routers/
│   │   └── main.py
│   ├── core/                # Core services (Analysis, AI models, etc.)
│   ├── gui/                 # PyQt6 GUI application code
│   ├── resources/           # Data files (dictionaries, prompts, etc.)
│   ├── crud.py              # Database CRUD functions
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # SQLAlchemy database models
│   └── schemas.py           # Pydantic data validation schemas
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

Clone the repository and install the required dependencies for running the application:

```bash
pip install -r requirements.txt
```

For development, which includes running tests and linters, install the additional development dependencies:
```bash
pip install -r requirements-dev.txt
```

### 2. Configuration (Crucial Step)

The application uses `config.yaml` for most settings, but sensitive data like the `SECRET_KEY` should be handled securely using environment variables.

1.  **Set the Secret Key**: For production, set the `SECRET_KEY` as an environment variable. For local development, you can create a `.env` file in the project root. The application uses `python-dotenv` to load this file automatically.

2.  **Create a `.env` file** with the following content:
    ```.env
    # A secret key for encoding JWT tokens. Generate a new one for your instance.
    # You can generate one with: openssl rand -hex 32
    SECRET_KEY="YOUR_SUPER_SECRET_KEY_HERE"
    ```
    **Note**: The `secret_key` value in `config.yaml` is a placeholder and should not be used for production. The environment variable will always take precedence.

3.  **Create a default user**: The application requires at least one user to log in. You will need to create one manually in the database for the first run.

### 3. Running the Application

The application is launched using a single script that starts both the backend API server and the frontend GUI.

Run the following command from the project root:
```bash
python start_app.py
```
The GUI application will start, and you will be prompted to log in. The backend API will run in the background, and its logs will be saved to `api_server.log` and `api_server.err.log`.

## 🧪 Running Tests

To run the full suite of fast, isolated unit tests, use `pytest`:

```bash
pytest
```

## 📖 API Documentation

The API documentation is automatically generated by FastAPI and is available at `http://127.0.0.1:8000/docs` after you have started the backend API.
