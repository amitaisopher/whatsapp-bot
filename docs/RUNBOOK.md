# WhatsApp Chatbot Runbook

This runbook provides operational guidance for running the WhatsApp chatbot in different environments using the Makefile and Docker Compose.

## Quick Start

```bash
# View all available commands
make help

# Development mode (with hot reload)
make dev-build

# Production mode (detached)
make prod-build
```

## Environment Configuration

The application supports 4 running modes:

| Mode | Description | Environment File | How to Run |
|------|-------------|------------------|------------|
| 1. Local Python Dev | Direct Python execution with debugger | `.env.development` | `uv run python -m app.main` |
| 2. Docker Dev Mode | Docker with hot reload & volume mounting | `.env.docker.dev` | `make dev-build` |
| 3. Docker Prod Mode | Docker optimized for production | `.env.docker.prod` | `make prod-build` |
| 4. Python Prod Mode | Direct Python in production | `.env.production` | `uv run python -m app.main` |

See [ENVIRONMENT.md](ENVIRONMENT.md) for detailed configuration guide.

## Running with Docker Compose (Recommended)

### Development Mode

Development mode provides hot-reload functionality with volume mounting. **Runs in detached mode** - containers run in the background and you get your terminal prompt back.

**Start development:**
```bash
make dev-build
```

**Features:**
- **Runs in detached mode** (background) - terminal prompt returns immediately
- Hot reload (code changes reflected immediately)
- Volume mounted for live editing
- Redis Commander UI at http://localhost:8081
- API at http://localhost:8000
- Uses `.env.docker.dev`
- View logs with `make logs ENV=dev`

**Stop development:**
```bash
make dev-down
```

**View logs:**
```bash
make logs ENV=dev
make logs-api ENV=dev
make logs-worker ENV=dev
```

### Production Mode

Production mode runs in detached mode with optimized settings.

**Start production:**
```bash
make prod-build
```

**Features:**
- Runs in detached mode (background)
- 2 worker replicas by default
- Resource limits configured
- No Redis Commander (security)
- Persistent Redis data volume
- Uses `.env.docker.prod`

**Stop production:**
```bash
make prod-down
```

**View logs:**
```bash
make logs ENV=prod
make logs-api ENV=prod
make logs-worker ENV=prod
```

**Scale workers:**
```bash
make scale-workers WORKERS=5 ENV=prod
```

## Running with Python Directly (Local Development)

For direct Python execution without Docker (useful for debugging):

### 1. Start Redis with Docker
```bash
# Start only Redis service
docker-compose -f docker-compose.dev.yml up -d redis
```

### 2. Setup Python Environment
```bash
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Configure Environment File
Create `.env.development` with localhost settings:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
# ... other settings
```

### 4. Run Services

**Option A: Using VS Code Debugger**

Use the launch configurations in `.vscode/launch.json`:
- **FastAPI: Development** - Debug API with hot reload
- **Arq Worker** - Debug background workers

**Option B: Using Terminal**
```bash
# Terminal 1: API
uv run python -m app.main

# Terminal 2: Worker
uv run arq app.workers.tasks.WorkerSettings
```

## Common Operations

### View Service Status

```bash
# Check running containers
make status ENV=prod

# Or
make ps ENV=prod
```

### Restart Services

```bash
# Restart API
make restart-api ENV=prod

# Restart workers
make restart-worker ENV=prod
```

### Access Container Shells

```bash
# API container
make shell-api ENV=prod

# Worker container
make shell-worker ENV=prod
```

### Stop/Start Individual Services

```bash
# Stop
make stop-api ENV=prod
make stop-worker ENV=prod
make stop-redis ENV=prod

# Start
make start-api ENV=prod
make start-worker ENV=prod
make start-redis ENV=prod
```

### Rebuild Individual Services

```bash
# Rebuild API
make rebuild-api ENV=prod

# Rebuild worker
make rebuild-worker ENV=prod
```

## Development Workflow

### Local Development with Hot Reload

1. **Start development environment:**
   ```bash
   make dev-build
   ```
   
   This runs in **detached mode** - containers start in the background and your terminal prompt returns immediately.

2. **View logs to monitor activity:**
   ```bash
   make logs ENV=dev
   ```

3. **Make code changes** - Changes are automatically reflected in the running containers

4. **If you change dependencies, rebuild:**
   ```bash
   make dev-down
   make dev-build
   ```

### Testing Changes

```bash
# Run tests
make test

# Run with coverage
make test-coverage

# Lint and format
make lint
```

## Monitoring and Logs

### View All Logs

```bash
# Follow all service logs
make logs ENV=prod

# Specific service
make logs-api ENV=prod
make logs-worker ENV=prod
```

### Redis Commander (Dev Mode Only)

Access at http://localhost:8081 when running in dev mode (`make dev-build`).

**Features:**
- Browse Redis keys
- View queue contents
- Monitor job processing
- Debug deduplication cache

**Note:** Redis Commander is not available in production mode for security reasons.

### API Documentation

When services are running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Scaling Workers

### Development
```bash
make scale-workers WORKERS=3 ENV=dev
```

### Production
```bash
# Scale based on load
make scale-workers WORKERS=5 ENV=prod

# Check status
make status ENV=prod

# Monitor worker logs
make logs-worker ENV=prod
```

## Job Deduplication

The application uses Redis-based job deduplication with a 1-hour TTL to prevent duplicate processing when multiple workers are running.

**How it works:**
- Each incoming message gets a unique job ID based on message content
- Before processing, workers check if job ID exists in Redis
- If exists, job is skipped (already processed or in progress)
- If not exists, job is marked in Redis with 1-hour expiration
- After 1 hour, same message can be processed again if needed

**Monitor deduplication:**
```bash
# Access Redis Commander (dev mode only)
# http://localhost:8081

# Or use Redis CLI
docker exec -it <redis-container> redis-cli
> KEYS job:*
> TTL job:<job-id>
```

## Troubleshooting

### API not responding

```bash
# Check if container is running
make status ENV=prod

# Check logs for errors
make logs-api ENV=prod

# Restart API
make restart-api ENV=prod
```

### Workers not processing jobs

```bash
# Check worker logs
make logs-worker ENV=prod

# Check Redis connection
docker exec -it <redis-container> redis-cli PING

# Scale workers
make scale-workers WORKERS=2 ENV=prod
```

### Redis connection issues

```bash
# Check Redis is running
make status ENV=prod

# Restart Redis
make stop-redis ENV=prod
make start-redis ENV=prod

# Check Redis logs
docker logs <redis-container>
```

### Port already in use

```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :6379

# Stop all services
make prod-down

# Start again
make prod-build
```

### Disk space issues

```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove old images
docker image prune -a

# Check disk usage
docker system df
```

## Performance Tuning

### API Performance
- Adjust worker replicas based on load
- Monitor CPU/memory with `docker stats`
- Review resource limits in `docker-compose.prod.yml`

### Worker Performance
```bash
# Scale workers dynamically
make scale-workers WORKERS=10 ENV=prod

# Monitor worker performance
make logs-worker ENV=prod

# Check Redis queue depth
docker exec -it <redis-container> redis-cli LLEN arq:queue
```

### Redis Performance
- Monitor memory usage with Redis Commander
- Adjust TTL for job deduplication if needed
- Consider Redis persistence settings in production

## Security Considerations

### Production Checklist
- [ ] Strong Redis password set in `.env.docker.prod`
- [ ] Redis Commander disabled (`docker-compose.prod.yml`)
- [ ] Environment variables not committed to git
- [ ] API exposed only through reverse proxy/load balancer
- [ ] Resource limits configured for all services
- [ ] Log rotation configured
- [ ] Regular backups of Redis data volume

### Environment Variables
Never commit these files:
- `.env.docker.dev`
- `.env.docker`
- `.env.docker.prod`
- `.env.development`

Use `.env.template` as reference for required variables.

## Additional Resources

- [README.md](../README.md) - Project overview and architecture
- [DOCKER.md](DOCKER.md) - Detailed Docker deployment guide
- [DOCKER-QUICKSTART.md](DOCKER-QUICKSTART.md) - Quick Docker reference
- [ENVIRONMENT.md](ENVIRONMENT.md) - Environment variables guide

## Support

For issues or questions:
1. Check logs: `make logs ENV=<env>`
2. Review documentation in this repository
3. Check Redis Commander for queue/cache state
4. Verify environment configuration matches requirements
