# Advanced LLM Orchestration Framework for Clinical Healthcare (Containerized)

This project provides a production-ready framework for orchestrating multiple Large Language Models (LLMs) for clinical healthcare applications. It is designed to be modular, scalable, and compliant with healthcare industry best practices.

## 🌟 Key Features

- **Service-Oriented API**: The entire framework is exposed via a **FastAPI** interface, making it easy to integrate with other applications.
- **Dynamic Workflows**: Orchestration is driven by a `config.yaml` file, allowing you to customize workflows without changing the code.
- **Advanced PII Detection**: Integrates **Microsoft's Presidio** for state-of-the-art, offline PII detection.
- **Retrieval-Augmented Generation (RAG)**: Includes a RAG pipeline powered by **FAISS** for question-answering against a local knowledge base.
- **Asynchronous Task Processing**: Uses **Celery** and **Redis** to offload long-running model inference tasks, ensuring the API remains responsive.
- **Model Evaluation Framework**: Includes a script to quantitatively evaluate the performance of the NER model.

## 📂 Project Structure

```
.
├── config/
│   └── config.yaml
├── data/
│   └── ner_evaluation_data.json
├── knowledge_base/
│   └── ...
├── build_vector_store.py
├── evaluate_ner_model.py
├── run_demo.py
├── requirements.txt
└── src/
    ├── api.py               # The FastAPI application
    ├── celery_app.py
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
    This will install all necessary packages for the application, including core logic, UI, and testing dependencies. The dependencies are managed in a modular way in the `requirements/` directory. The root `requirements.txt` file simply aggregates them.

2.  **Download Spacy Model:**
    The application uses the `en_core_web_sm` model from `spacy`. You may need to download it separately:
    ```bash
    python -m spacy download en_core_web_sm
    ```
2.  **Run the application:**
    ```bash
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api:app
    ```

Your API will now be running and accessible at `http://localhost:8000`. You can view the interactive API documentation (provided by Swagger UI) by navigating to `http://localhost:8000/docs` in your browser.

### Interacting with the API

You can use any HTTP client (like `curl` or Postman) or the interactive docs to interact with the API:

**1. Analyze Clinical Text:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '{"text": "The patient has a history of asthma and was given prednisone."}'
```
This will return a `task_id`.

**2. Check Task Status:**
Use the `task_id` from the previous step to check the result:
```bash
curl http://localhost:8000/tasks/{your_task_id}
```

## 🧪 Evaluating the NER Model

To run the evaluation script, you can execute it from your terminal:
```bash
python evaluate_ner_model.py
```