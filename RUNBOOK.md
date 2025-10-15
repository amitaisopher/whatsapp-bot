# Running the WhatsApp Chatbot Application

This document provides instructions on how to run the FastAPI application and the Arq workers for the WhatsApp Chatbot.

## Overview

The application consists of three main components:
1.  **FastAPI Application**: A web server that exposes an API to handle incoming WhatsApp webhooks and other HTTP requests.
2.  **Arq Workers**: Background workers that process tasks asynchronously. This is used to handle long-running or deferrable tasks, such as sending messages or processing incoming data, without blocking the API.
3.  **Redis**: An in-memory data store used as a message broker for Arq. The FastAPI application enqueues tasks into Redis, and the Arq workers pick them up from there.

## Prerequisites

- [Docker](httpss://www.docker.com/get-started) and [Docker Compose](httpss://docs.docker.com/compose/install/)
- [Visual Studio Code](httpss://code.visualstudio.com/)
- Python 3.13 or later
- `uv` package manager (`pip install uv`)

## Environment Configuration

The application uses `.env` files to manage environment variables. The configuration is loaded based on the `APP_ENV` environment variable.

1.  **Create Environment Files**:
    You'll need to create `.env` files for different environments. For local development, create a `.env.development` file in the project root.

    **Example `.env.development`:**
    ```env
    APP_ENV=development
    DEBUG=True

    # Redis config for docker-compose
    UPSTASH_REDIS_HOST=redis
    UPSTASH_REDIS_PORT=6379

    # WhatsApp config (replace with your actual credentials)
    WHATSAPP_ACCESS_TOKEN=your_access_token
    WHATSAPP_WEBHOOK_VERIFICATION_TOKEN=your_verification_token
    WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
    ```

2.  **For Production**:
    You can create a `.env.production` with production-specific settings.

## Running with Docker Compose

This is the recommended way to run the application locally, as it orchestrates the FastAPI app, Arq workers, and Redis container together.

1.  **Build and Run the Containers**:
    Open a terminal in the project root and run:
    ```bash
    docker-compose up --build
    ```
    This command builds the Docker images for the `api` and `worker` services and starts all services defined in `docker-compose.yml`.

2.  **Using Different Environments**:
    The `docker-compose.yml` is configured to use an `ENV_FILE` environment variable to specify which `.env` file to load. By default, it uses `.env.development`.

    To run with a different configuration, such as `.env.staging`, you can run:
    ```bash
    ENV_FILE=.env.staging docker-compose up
    ```

3.  **Running in Detached Mode**:
    To run the containers in the background, use the `-d` flag:
    ```bash
    docker-compose up -d
    ```

## Running with VSCode (for Development and Debugging)

For a more interactive development experience, you can run the services directly from VSCode. This is especially useful for debugging.

### 1. Running Redis with Docker
Even when running the app and worker locally, it's convenient to run Redis in a Docker container.
```bash
docker-compose up -d redis
```
This will start only the Redis service.

### 2. Setting up the Python Environment
Ensure you have a Python interpreter selected in VSCode and install the dependencies.
```bash
uv pip install -r requirements.txt
```

### 3. Create a `.env` file for local development
Create a `.env` file in the root of the project and set the `UPSTASH_REDIS_HOST` to `localhost`.

**Example `.env`:**
```env
APP_ENV=development
DEBUG=True

# Redis config for local development
UPSTASH_REDIS_HOST=localhost
UPSTASH_REDIS_PORT=6379

# WhatsApp config
WHATSAPP_ACCESS_TOKEN=your_access_token
# ... other variables
```
Your application will automatically load this `.env` file when running locally.

### 4. Running the FastAPI Application
You can run the FastAPI app using the VSCode debugger. Create a `launch.json` file in the `.vscode` directory with the following configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000"
            ],
            "jinja": true,
            "justMyCode": true
        }
    ]
}
```
You can now go to the "Run and Debug" panel in VSCode, select "Python: FastAPI", and press F5 to start the application with the debugger attached.

### 5. Running the Arq Worker
To run the Arq worker, open a new terminal in VSCode and run the following command:
```bash
arq app.workers.tasks.WorkerSettings
```
This will start a worker that listens for jobs on the Redis queue.

## Redis and Arq

- **Enqueuing Jobs**: The FastAPI application sends jobs to Redis using Arq's client.
- **Processing Jobs**: The Arq workers are constantly listening to the Redis queue for new jobs to process.
- **Isolation**: This setup decouples the API from the background tasks, ensuring that the API remains responsive even when long-running tasks are being executed.
