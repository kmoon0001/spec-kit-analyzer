# Advanced LLM Orchestration Framework for Clinical Healthcare (Containerized)

This project provides a production-ready, containerized framework for orchestrating multiple Large Language Models (LLMs) for clinical healthcare applications. It is designed to be modular, scalable, and compliant with healthcare industry best practices, and is now fully containerized with Docker for easy deployment and scalability.

## 🌟 Key Features

- **Service-Oriented API**: The entire framework is exposed via a **FastAPI** interface, making it easy to integrate with other applications.
- **Fully Containerized**: The entire application stack (API, Worker, Redis) is managed by **Docker Compose**, allowing for one-command setup and deployment.
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
├── Dockerfile             # Defines the application container
├── docker-compose.yml     # Orchestrates all services
├── entrypoint.sh          # Handles container startup logic
├── requirements.txt
└── src/
    ├── api.py               # The FastAPI application
    ├── celery_app.py
    └── ...
```

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose**: Ensure they are installed on your system.

### Running the Application

With Docker, running the entire application stack is as simple as a single command. From the root directory of the project, run:

```bash
docker-compose up --build
```

- `--build`: This flag tells Docker Compose to build the application image from the `Dockerfile` the first time you run it, or if any code changes have been made.

This command will:
1.  Pull the official Redis image.
2.  Build your application's Docker image, installing all Python dependencies.
3.  Start the **Redis**, **API**, and **Celery Worker** services and connect them.
4.  The `entrypoint.sh` script will automatically run `build_vector_store.py` inside the container to create the FAISS index.

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

### Stopping the Application

To stop all the running containers, press `Ctrl+C` in the terminal where `docker-compose` is running, and then run:
```bash
docker-compose down
```

## 🧪 Evaluating the NER Model

To run the evaluation script, you can execute it within the running `api` container:
```bash
docker-compose exec api python evaluate_ner_model.py
```