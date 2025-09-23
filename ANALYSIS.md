# Analysis of the Therapy Compliance Analyzer Project

## Project Overview

The project is a desktop application named "Therapy Compliance Analyzer" built with PyQt6. It allows users to upload various document formats (like PDF, DOCX, and images), extracts the text, and then analyzes it against user-defined rubrics. It includes features for scrubbing Protected Health Information (PHI) and generating reports.

**Note:** The `README.md` file is outdated and describes a FastAPI web application, which is no longer the case. The project has pivoted to a desktop PyQt6 application.

## Big Dependencies

Based on the analysis of the `requirements/` directory, here are the major dependencies of the project:

*   **`PyQt6`**: The core framework for the graphical user interface.
*   **`pandas`**, **`scikit-learn`**, and **`spacy`**: Essential Python libraries for data manipulation, machine learning, and natural language processing.
*   **`transformers`**, **`langchain`**, and **`llama_index`**: Frameworks and libraries for working with Large Language Models (LLMs).
*   **`faiss-cpu`**: A library for efficient similarity search, likely used for the Retrieval-Augmented Generation (RAG) pipeline.
*   **`presidio-analyzer` & `presidio-anonymizer`**: Used for detecting and removing Personally Identifiable Information (PII).

## File and Code

The main application logic is contained within the `src/` directory. The key file is `src/gui/main_window.py`, which defines the main application window and its functionality.

### `src/gui/main_window.py` Summary

*   It defines the `MainApplicationWindow` class, which is the main window of the application.
*   It sets up the UI, including buttons for uploading documents, managing rubrics, and running analysis.
*   It handles file uploads (including drag and drop).
*   It uses background threads (`QThread`) to process documents and run analysis without freezing the UI.
*   It has functionality to generate reports in PDF format.
*   It includes a basic PHI scrubber to redact sensitive information.
