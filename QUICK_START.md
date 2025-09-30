# 🚀 Quick Start Guide

This guide provides step-by-step instructions to get the Therapy Compliance Analyzer installed and running on your local machine.

## 1. System Requirements

Before you begin, ensure your system meets the following requirements:

-   **Python**: Version 3.10 or newer.
-   **RAM**: A minimum of 6GB of RAM. The application will adapt its performance based on your system's available memory.
-   **Operating System**: Windows, macOS, or Linux.
-   **System Dependencies**:
    -   **Cairo**: Required for PDF and graphics functionality.
    -   **Tesseract**: Required for Optical Character Recognition (OCR).

## 2. Installation and Setup

Follow these steps to install the application and its dependencies.

### Step 1: Clone the Repository
First, clone the project repository to your local machine using Git:
```bash
git clone <repository-url>
cd <repository-directory>
```

### Step 2: Create a Virtual Environment (Recommended)
It is highly recommended to use a virtual environment to manage the project's dependencies.
```bash
# Create the virtual environment
python -m venv .venv

# Activate the environment
# On Windows:
.venv\Scripts\activate
# On macOS and Linux:
source .venv/bin/activate
```

### Step 3: Install System Dependencies
Install the required system libraries for your operating system.
-   **For Debian/Ubuntu-based systems:**
    ```bash
    sudo apt-get update && sudo apt-get install -y libcairo2-dev tesseract-ocr
    ```
-   **For other systems (macOS, Windows):**
    Use your system's package manager (e.g., Homebrew, Chocolatey) to install `cairo` and `tesseract`.

### Step 4: Install Python Dependencies
With your virtual environment activated, install the necessary Python packages.
```bash
# Install the main application dependencies
pip install -r requirements.txt

# For development, install the additional testing and linting tools
pip install -r requirements-dev.txt
```

## 3. Configuration

The application requires a secret key for secure token encoding.

### Step 1: Create a `.env` File
Create a file named `.env` in the root of the project directory. This file will store your secret key.

### Step 2: Set the Secret Key
Add the following line to your `.env` file. You can generate a new secret key using the command provided.
```.env
# Generate a new key with: openssl rand -hex 32
SECRET_KEY="YOUR_SUPER_SECRET_KEY_HERE"
```
**Note**: The application will automatically load this environment variable. It will take precedence over the placeholder key in `config.yaml`.

### Step 3: Create a Default User
For the first run, you will need to create a default user in the database to be able to log in.

## 4. Running the Application

You can run the application in several ways:

-   **Method 1: Simple Startup (Recommended)**
    This script automatically checks your environment and starts both the backend API and the frontend GUI.
    ```bash
    python start_app.py
    ```

-   **Method 2: Direct GUI Launch**
    ```bash
    python run_gui.py
    ```

-   **Method 3: Backend and Frontend Separately**
    This is useful for development and debugging.
    ```bash
    # Terminal 1: Start the backend API server
    python run_api.py

    # Terminal 2: Start the GUI application
    python -m src.gui.main
    ```

## 5. First Run Walkthrough

1.  **Launch the app** using one of the methods above.
2.  **Wait for AI models to load**. The first startup may take 30-60 seconds. You should see a "Models Ready" status in the application window.
3.  **Upload a document** by clicking the "Upload Document" button.
4.  **Select a rubric** (e.g., PT, OT, SLP) from the dropdown menu.
5.  **Run the analysis** by clicking the "Run Analysis" button.
6.  **View the report**. The analysis results will appear in the report panel.

## 6. Basic Troubleshooting

-   **Application Won't Start**:
    -   Make sure your virtual environment is activated.
    -   Verify that all dependencies from `requirements.txt` are installed (`pip list`).
    -   Ensure the system dependencies (Cairo, Tesseract) are installed correctly.

-   **"AI Models Failed" Error**:
    -   This typically happens on the first run if the models have not been downloaded.
    -   Ensure you have a stable internet connection and restart the application. The models will be downloaded and cached locally.