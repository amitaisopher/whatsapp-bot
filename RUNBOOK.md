<!-- ...existing code... -->
## Environment Configuration

The application uses `.env` files to manage environment variables.

### 1. For Docker Compose

When running with Docker Compose, the services will load the file specified by the `ENV_FILE` environment variable, which defaults to `.env.docker`.

Create a `.env.docker` file in the project root. This file should configure the application to connect to the `redis` service by its service name.

**Example `.env.docker`:**
```env
APP_ENV=development
DEBUG=True

# Redis config for docker-compose
UPSTASH_REDIS_HOST=redis
UPSTASH_REDIS_PORT=6379
UPSTASH_REDIS_PASSWORD=your-very-strong-password

# WhatsApp config (replace with your actual credentials)
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_WEBHOOK_VERIFICATION_TOKEN=your_verification_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

**Important**: The `UPSTASH_REDIS_PASSWORD` must match the password set in `redis/redis.conf` and in `docker-compose.yml` for the `redis-commander` service.

### 2. For Local Development (e.g., with VSCode)

When running the services directly on your host machine (not in Docker), you can use a `.env` file. The application will connect to the Redis container via its mapped port on `localhost`.

**Example `.env`:**
```env
APP_ENV=development
DEBUG=True

# Redis config for local development
UPSTASH_REDIS_HOST=localhost
UPSTASH_REDIS_PORT=6379
UPSTASH_REDIS_PASSWORD=your-very-strong-password

# WhatsApp config
WHATSAPP_ACCESS_TOKEN=your_access_token
# ... other variables
```

## Running with Docker Compose

This is the recommended way to run the application, as it orchestrates the FastAPI app, Arq workers, and a password-protected Redis container.

1.  **Configure Redis Password**:
    Before you start, ensure you have set a strong password in the following three places:
    -   `redis/redis.conf`
    -   `docker-compose.yml` (for the `redis-commander` service)
    -   Your `.env.docker` file (`UPSTASH_REDIS_PASSWORD`)

2.  **Build and Run the Containers**:
    Open a terminal in the project root and run:
    ```bash
    docker-compose up --build
    ```
    This command builds the Docker images and starts all services.

3.  **Accessing Services**:
    -   **API**: `http://localhost:8000`
    -   **Redis Commander**: `http://localhost:8081` (A web UI for managing Redis)

4.  **Using Different Environments**:
    The `docker-compose.yml` is configured to use an `ENV_FILE` environment variable. By default, it uses `.env.docker`.

    To run with a different configuration, such as `.env.staging`, you can run:
    ```bash
    ENV_FILE=.env.staging docker-compose up
    ```

5.  **Running in Detached Mode**:
    To run the containers in the background, use the `-d` flag:
    ```bash
    docker-compose up -d
    ```

## Running with VSCode (for Development and Debugging)

For a more interactive development experience, you can run the services directly from VSCode while using Docker for Redis.

### 1. Running Redis with Docker
Start the Redis and Redis Commander services using Docker Compose.
```bash
docker-compose up -d redis redis-commander
```
This will start a password-protected Redis instance accessible at `localhost:6379`.

### 2. Setting up the Python Environment
Ensure you have a Python interpreter selected in VSCode and install the dependencies.
```bash
uv pip install --system .
```

### 3. Create a `.env` file for local development
Create a `.env` file in the root of the project as described in the "Environment Configuration" section above. Make sure `UPSTASH_REDIS_HOST` is set to `localhost` and the password is correct.

### 4. Running the FastAPI Application
You can run the FastAPI app using the VSCode debugger. Create a `launch.json` file in the `.vscode` directory with the following configuration:

```json
// filepath: .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.create_app:create_app",
                "--factory",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000"
            ],
            "jinja": true,
            "justMyCode": true,
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```
You can now go to the "Run and Debug" panel in VSCode, select "Python: FastAPI", and press F5 to start the application with the debugger attached.

### 5. Running the Arq Worker
To run the Arq worker, open a new terminal in VSCode (which will load the `.env` file if you have the Python extension configured correctly) and run the following command:
```bash
arq app.workers.tasks.WorkerSettings
```
This will start a worker that connects to Redis on `localhost` and listens for jobs.

## Redis and Arq
<!-- ...existing code... -->