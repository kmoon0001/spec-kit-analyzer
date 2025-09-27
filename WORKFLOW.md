# High-Level Workflow Design: Therapy Compliance Analyzer

This document outlines the end-to-end workflow for the Therapy Compliance Analyzer, a desktop application designed to assist clinical therapists in ensuring their documentation meets regulatory standards.

## 1. User Authentication
- **Action**: The user launches the PyQt6 application and is presented with a secure login screen.
- **System Process**: The application authenticates the user against the local SQLite database. User credentials and session tokens are managed securely.

## 2. Main Dashboard
- **Action**: Upon successful login, the user is directed to the main dashboard.
- **System Process**: The dashboard provides a high-level overview of historical compliance data. It features visualizations like a compliance score trend chart and a summary of frequently identified issues, allowing users to track their performance over time.

## 3. Document Upload and Preprocessing
- **Action**: The user uploads a clinical document for analysis (e.g., PDF, DOCX, or plain text).
- **System Process**:
    - The system extracts the raw text from the uploaded document.
    - The text undergoes a preprocessing step, which includes cleaning and correction using a specialized medical spell-checker to improve the accuracy of the subsequent analysis.

## 4. AI-Powered Analysis Pipeline
This is the core of the application, where the document is analyzed for compliance.

- **Step 4.1: Document Classification**: The system first determines the type of document (e.g., "Progress Note," "Evaluation," "Discharge Summary"). This classification provides essential context to the AI, enabling a more targeted and accurate analysis.
- **Step 4.2: Hybrid Semantic Search (RAG)**: The application employs a sophisticated Retrieval-Augmented Generation (RAG) pipeline. It uses a hybrid search algorithm, combining keyword-based and semantic search, to query a vector database of compliance guidelines and rubrics. This ensures that the most relevant rules are retrieved for the given document context.
- **Step 4.3: Compliance Analysis**: The retrieved rules and the document text are fed into a Large Language Model (LLM). The LLM analyzes the document to identify any deviations from the compliance guidelines.
- **Step 4.4: Personalized Feedback**: For each identified issue, the AI generates a personalized, actionable tip. This feedback is designed to be constructive and educational, helping the therapist understand the specific nature of the compliance gap and how to remediate it.

## 5. Risk Scoring and Uncertainty
- **System Process**:
    - **Weighted Risk Scoring**: Each finding is assigned a risk score based on its potential severity and financial impact. These scores are aggregated into an overall compliance score for the document, providing a clear, quantitative measure of compliance.
    - **Uncertainty Handling**: The system identifies and flags any findings where the AI's confidence is low. These are visually distinguished in the final report, ensuring transparency and encouraging user discretion.

## 6. Interactive Report Generation
- **Action**: The user initiates the generation of the final report.
- **System Process**: The application compiles all the analysis data—including the compliance score, a detailed list of findings, personalized tips, and AI limitation disclaimers—into a comprehensive HTML report. The user can view this report within the application or export it.

## 7. User Review and Actions
- **Action**: The user reviews the generated report.
- **System Process**: The report provides an interactive interface where users can examine each finding. Future enhancements could allow users to dispute findings, which would tag them visually in the report and provide feedback to the model.