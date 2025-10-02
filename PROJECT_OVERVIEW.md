# Project Overview: Therapy Compliance Analyzer

This document provides a comprehensive overview of the Therapy Compliance Analyzer application, including its features, dependencies, workflow, and technical architecture.

## 1. Core Features and Functionality

The Therapy Compliance Analyzer is an advanced, AI-powered desktop application designed to help clinical therapists analyze documentation for compliance with Medicare and other regulatory guidelines.

### Secure User Authentication
- **Login System**: A robust login system ensures secure access to the application.
- **Password Management**: Features for password hashing and management are included to protect user credentials.
- **Admin Roles**: The application supports administrative roles with elevated privileges, such as access to the director's dashboard.

### Interactive Dashboard
- **Compliance Score Visualization**: A historical score chart visualizes compliance trends over time.
- **Common Issues Breakdown**: The dashboard provides a summary of the most common compliance issues identified across all analyses.
- **Director's Dashboard**: An admin-only view provides team-wide analytics, including habit summaries and clinician-specific breakdowns.

### AI-Powered Analysis Pipeline
- **Advanced Preprocessing**: Includes a medical spell-checker and other text-cleaning utilities to prepare documents for analysis.
- **Document Classification**: Automatically identifies the document type (e.g., "Progress Note," "Evaluation") to provide better context to the AI.
- **Hybrid Semantic Search (RAG)**: A sophisticated Retrieval-Augmented Generation (RAG) pipeline uses a hybrid of keyword-based (BM25) and semantic search to find the most relevant compliance rules for a given document.
- **NLG for Personalized Tips**: The AI generates personalized, actionable tips for each finding, offering more than just generic suggestions.

### Enhanced Risk Scoring
- **Weighted Algorithm**: A weighted algorithm calculates a more meaningful compliance score based on the severity and potential financial impact of each finding.

### Ethical & Transparent AI
- **Uncertainty Handling**: The system is designed to flag and visually highlight findings where the AI's confidence is low.
- **Formalized Limitations**: Every report includes a clear disclaimer about the capabilities and limitations of the AI models.

### Database-Backed Rubric Manager
- **Full CRUD Functionality**: A graphical user interface (GUI) allows users to add, edit, and delete compliance rubrics.
- **Immediate Reflection**: All changes to the rubrics are immediately reflected in the analysis engine.

### Automated Database Maintenance
- **Automated Purging**: The application automatically purges old reports to manage disk space usage effectively.

## 2. Project Dependencies

The application relies on a number of open-source libraries and frameworks, which can be categorized as follows:

### Core Web & API
- **FastAPI**: A modern, high-performance web framework for building APIs.
- **Uvicorn & Gunicorn**: ASGI servers used to run the FastAPI application.
- **SlowAPI**: A rate-limiting library to protect API endpoints from abuse.
- **Requests & HTTPX**: Libraries for making HTTP requests, used for communicating with external services or APIs.

### Graphical User Interface (GUI)
- **PyQt6**: A comprehensive set of Python bindings for the Qt application framework, used to build the desktop GUI.
- **PyQt6-WebEngine**: Provides a web browser engine for rendering dynamic, web-based content within the application.
- **Matplotlib**: A plotting library used to generate the charts and visualizations in the dashboard.
- **PyTesseract**: A Python wrapper for Google's Tesseract-OCR Engine, used for extracting text from images.

### Data & Parsing
- **PDFPlumber & PyPDFium2**: Libraries for extracting text and data from PDF files.
- **python-docx**: A library for creating and updating Microsoft Word (.docx) files.
- **Pandas**: A powerful data analysis and manipulation library.
- **OpenPyXL**: A library for reading and writing Excel 2010 xlsx/xlsm/xltx/xltm files.
- **PyYAML**: A YAML parser and emitter for Python, used for reading the `config.yaml` file.
- **Markdown**: A library for converting Markdown text to HTML.

### AI & Machine Learning
- **PyTorch**: A deep learning framework that serves as the foundation for many of the AI models.
- **Transformers**: Provides state-of-the-art machine learning models for natural language processing (NLP), including those from Hugging Face.
- **Sentence-Transformers**: A library for computing dense vector representations of sentences and text.
- **C Transformers**: A library providing Python bindings for the `ggml` library, enabling efficient execution of Large Language Models (LLMs) on CPU.
- **FAISS**: A library for efficient similarity search and clustering of dense vectors.
- **Rank-BM25**: A library for BM25 ranking, a keyword-based search algorithm.
- **NLTK**: The Natural Language Toolkit, a leading platform for building Python programs to work with human language data.
- **PySpellChecker**: A library for identifying and correcting misspelled words.
- **Hugging Face Transformers**: Modern transformer-based models for Named Entity Recognition (NER) and biomedical text analysis, replacing spaCy for better accuracy and flexibility.
- **Presidio**: Microsoft's data protection and de-identification SDK for detecting and anonymizing PII/PHI in text.

### Database
- **SQLAlchemy**: A SQL toolkit and Object-Relational Mapper (ORM) that gives application developers the full power and flexibility of SQL.
- **RDFLib**: A pure Python package for working with RDF, the Resource Description Framework.
- **aiosqlite**: Asynchronous access to SQLite databases.

### Security & Authentication
- **python-dotenv**: A library for reading key-value pairs from a `.env` file and setting them as environment variables.
- **Passlib**: A password hashing library for securely storing user passwords.
- **python-multipart**: A streaming multipart parser for Python, used by FastAPI for handling file uploads.
- **PyJWT & python-jose**: Libraries for encoding and decoding JSON Web Tokens (JWTs) for user authentication.

### Performance & Monitoring
- **psutil**: A cross-platform library for retrieving information on running processes and system utilization.
- **ONNX Runtime**: A performance-focused engine for ONNX models, used for optimizing and running machine learning models.
- **Optimum**: A library from Hugging Face for optimizing `Transformers` models for production.

## 3. Application Workflow

The application workflow describes the end-to-end process from user interaction to data processing and analysis.

1.  **User Authentication**: The user launches the PyQt6 desktop application and is prompted to log in. The credentials are sent to the FastAPI backend for verification.

2.  **Document Upload**: Once logged in, the user selects a clinical document (e.g., a PDF or DOCX file) for analysis through the GUI.

3.  **Backend Processing**: The document is sent to the backend API, which initiates the analysis pipeline managed by the `AnalysisService`.

4.  **Text Preprocessing**: The raw document undergoes several preprocessing steps:
    *   **Text Extraction**: Text is extracted from the document using libraries appropriate for the file type (e.g., `pdfplumber`).
    *   **Spell Checking**: A medical spell-checker corrects common misspellings.
    *   **PHI Scrubbing**: The `phi_scrubber` service removes Personal Health Information (PHI) to ensure privacy.

5.  **Document Classification**: The `DocumentClassifier` model analyzes the preprocessed text to determine the document's type (e.g., "Progress Note," "Evaluation"), which helps tailor the analysis.

6.  **Hybrid Retrieval (RAG)**: The `HybridRetriever` (the core of the RAG pipeline) identifies the most relevant compliance rules for the document by combining:
    *   **Keyword Search**: A BM25 algorithm performs a fast, keyword-based search.
    *   **Semantic Search**: A Sentence Transformer model converts the text and rules into vector embeddings, and a FAISS index finds the most similar rules based on semantic meaning.

7.  **LLM-Powered Analysis**: The preprocessed text and the retrieved compliance rules are formatted into a prompt and sent to a generative Large Language Model (LLM). The LLM analyzes the document in the context of the rules and generates compliance findings.

8.  **Risk Scoring & Reporting**:
    *   The `RiskScoringService` calculates a compliance score based on the number and severity of the findings.
    *   The `NLGService` generates personalized, actionable tips for each identified issue.
    *   A final analysis report is compiled.

9.  **Database Storage**: The complete analysis report, including the score, findings, and tips, is stored in the SQLite database using SQLAlchemy.

10. **Display to User**: The final report is sent back to the PyQt6 frontend and displayed to the user in a clear, easy-to-read format. The data also becomes available for visualization on the dashboard.

## 4. The AI/ML Ensemble Workflow

The application's intelligence comes from a sophisticated ensemble of Natural Language Processing (NLP) and Machine Learning (ML) models that work together in a pipeline. This approach allows the system to combine the strengths of different models to achieve a more accurate and nuanced analysis.

### a. Named Entity Recognition (NER)

- **Purpose**: To identify and categorize key entities within the clinical text. The NER models are configured in `config.yaml` under the `ner_ensemble` key.
- **Models**: The system uses an ensemble of pre-trained NER models (e.g., `OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M` and `d4data/biomedical-ner-all`) to recognize a wide range of clinical and biomedical entities, such as diagnoses, treatments, and dates.
- **Function**: This step provides structured data that can be used for more targeted rule-checking and analysis. For example, it can help verify if a specific treatment mentioned in the text is properly justified.

### b. Retrieval-Augmented Generation (RAG)

The RAG pipeline is the core of the compliance analysis, responsible for finding the most relevant compliance rules for a given clinical document. This ensures that the final analysis is grounded in specific, verifiable guidelines.

- **1. Hybrid Retrieval**: The `HybridRetriever` service combines two different search techniques to maximize accuracy:
    - **Keyword Search (BM25)**: This algorithm is highly effective at matching specific keywords, acronyms, and technical terms found in the document to the compliance rubrics.
    - **Semantic Search (Sentence-Transformers + FAISS)**: This technique captures the underlying meaning of the text. It uses a `SentenceTransformer` model to convert both the document text and the compliance rules into numerical vectors (embeddings). A `FAISS` index then performs a highly efficient search to find the rules that are semantically closest to the content of the document, even if they don't share the same keywords.

- **2. Augmentation**: The top-ranked rules from both search methods are collected and "augment" the original document by being added to the context that will be sent to the generative model.

### c. Generative Analysis (LLM/GPT)

- **Purpose**: To perform the final, high-level analysis and generate human-readable compliance findings.
- **Model**: The application uses a generative Large Language Model (LLM), such as `Phi-3` or `Llama-3`, executed locally via the `ctransformers` library. This ensures that all sensitive data remains on the user's machine.
- **Function**: The LLM receives a carefully crafted prompt containing the preprocessed document text and the most relevant compliance rules retrieved by the RAG pipeline. It then:
    - **Analyzes for Compliance**: It compares the document's content against the provided rules to identify potential compliance issues.
    - **Generates Findings**: It generates a structured list of findings, outlining each potential violation.
    - **Creates Personalized Tips**: For each finding, the `NLGService` (Natural Language Generation Service) uses the LLM to generate a personalized, actionable tip to help the therapist improve future documentation.

## 5. High-Level Architecture

The application is designed with a modular, service-oriented architecture that separates concerns and promotes maintainability.

### a. Client-Server Model
- **Backend**: A robust backend API built with **FastAPI**. It handles all the heavy lifting, including AI analysis, database interactions, and user authentication. The API is designed to be modular, with different functionalities separated into routers.
- **Frontend**: A native desktop application built with **PyQt6**. This provides a responsive and feature-rich user interface for document analysis, report viewing, and dashboard interaction. The frontend communicates with the backend via HTTP requests.

### b. Database
- **SQLAlchemy & SQLite**: The application uses **SQLAlchemy** as its Object-Relational Mapper (ORM) to interact with a **SQLite** database. This combination provides a lightweight, file-based database solution that is easy to manage and deploy with a desktop application, while the ORM allows for writing database queries in a more Pythonic way.

### c. Directory Structure (`src/`)

The `src` directory is organized into modules, each with a specific responsibility:

-   `src/api/`: Contains the FastAPI application.
    -   `routers/`: Holds the different API routers (e.g., `auth.py`, `analysis.py`), each corresponding to a different feature set.
    -   `main.py`: The entry point for the FastAPI application.
-   `src/core/`: Contains the core business logic and services of the application. This includes the `AnalysisService`, `LLMService`, `HybridRetriever`, and other key components of the AI pipeline.
-   `src/database/`: Manages all database-related code.
    -   `database.py`: Sets up the SQLAlchemy engine and database session.
    -   `models.py`: Defines the SQLAlchemy database models (tables).
    -   `crud.py`: Contains the functions for Creating, Reading, Updating, and Deleting data from the database.
    -   `schemas.py`: Defines the Pydantic schemas used for data validation and serialization in the API.
-   `src/gui/`: Contains all the code for the PyQt6 graphical user interface.
    -   `widgets/`: Reusable UI components.
    -   `dialogs/`: Different dialog windows used in the application (e.g., Login, Rubric Manager).
    -   `workers/`: `QThread` workers for running long-running tasks (like AI analysis) in the background without freezing the UI.
-   `src/resources/`: Stores static data files, such as prompts for the LLM, medical dictionaries, and compliance rubrics.
-   `src/auth.py`: Handles user authentication logic, including password hashing and JWT management.
-   `src/config.py`: Manages application configuration, loading settings from `config.yaml` and environment variables.