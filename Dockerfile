# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies that might be required by some Python packages
# (e.g., for certain NLP libraries or other compiled extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
# We do this in a separate step to leverage Docker's layer caching.
# This way, dependencies are only re-installed if the requirements.txt file changes.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . /app

# Make the entrypoint script executable
RUN chmod +x ./entrypoint.sh

# The entrypoint script will run any setup tasks (like building the vector store)
# and then execute the main command.
ENTRYPOINT ["./entrypoint.sh"]

# The default command to run when the container starts.
# This will be overridden in docker-compose.yml for the worker service.
# We use gunicorn here as a robust, production-ready WSGI server.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "src.api:app"]
