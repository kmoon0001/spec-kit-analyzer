# Clinical Healthcare NLP Application

This project is a Python application for clinical healthcare, featuring a backend API and a frontend GUI.

## Structure 

- `backend/`: Contains the FastAPI backend application.
- `frontend/`: Contains the PySide6 frontend GUI application.
- `src/`: Contains shared logic and utilities.

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

1.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Download the `spacy` model:
    ```bash
    python -m spacy download en_core_web_sm
    ```

### Running the Application

**Backend API:**

To run the backend FastAPI server:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app.main:app
```
The API will be available at `http://localhost:8000`.

**Frontend GUI:**

To run the frontend GUI application:
```bash
python frontend/main.py
```
