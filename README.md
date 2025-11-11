# WhatsApp Chatbot

A production-ready WhatsApp chatbot built with FastAPI, Redis, and the WhatsApp Business API. This application provides a scalable foundation for building WhatsApp-based automation and customer service solutions.

## 🚀 Features

- **WhatsApp Business API Integration**: Full webhook support for receiving and sending messages
- **Async Message Processing**: Background job processing with Redis queues using ARQ
- **Type-Safe Message Handling**: Enum-based message type system for better maintainability
- **Multi-Customer Support**: Isolated customer environments with API key authentication
- **Car Media Management**: Store and manage images, videos, and documents for cars
- **Media Management CLI**: Command-line tool for managing customers, cars, and media
- **Comprehensive Logging**: Structured logging with Sentry integration
- **Production Ready**: Docker support, environment-based configuration, and error handling
- **Dependency Injection**: Testable architecture with proper separation of concerns

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [WhatsApp Integration](#whatsapp-integration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Integration](#database-integration)
- [Authentication & Security](#authentication--security)
- [Deployment](#deployment)
- [Testing](#testing)
- [Common Pitfalls](#common-pitfalls)
- [Contributing](#contributing)

## 🏗️ Architecture

### Project Structure
```
whatsapp-chatbot/
├── app/
│   ├── api/v1/routers/          # API route handlers
│   ├── core/                    # Core configuration and utilities
│   ├── models/                  # Pydantic data models
│   ├── services/                # Business logic services
│   └── workers/                 # Background job workers
├── tests/                       # Test suites
├── examples/                    # Usage examples
├── redis/                       # Redis configuration
├── specs/                       # Project specifications
└── docker-compose.yml          # Docker orchestration
```

### Core Components

1. **FastAPI Application** (`app/create_app.py`)
   - RESTful API endpoints
   - Global exception handling
   - Request validation
   - Sentry integration

2. **WhatsApp Service** (`app/services/whatsapp.py`)
   - Message sending/receiving
   - Webhook processing
   - Message type filtering
   - API response handling

3. **Background Workers** (`app/workers/tasks.py`)
   - Async message processing
   - Queue management with ARQ
   - Job scheduling and retry logic

4. **Message Processing System**
   - Type-safe message handling with enums
   - Configurable message type support
   - Dependency injection for testability
   - Job deduplication for exactly-once processing

### Docker Architecture

The application uses a multi-container architecture:

1. **API Container** (`Dockerfile`)
   - FastAPI application with uvloop
   - Handles WhatsApp webhooks
   - Enqueues jobs to Redis
   - Exposes port 8000

2. **Worker Container** (`Dockerfile.worker`)
   - ARQ background workers
   - Processes queued messages
   - Calls inventory search API
   - Sends WhatsApp responses
   - Scalable (multiple replicas)

3. **Redis Container**
   - Message queue (ARQ)
   - Job deduplication cache
   - Session storage
   - Native TCP/TLS connections (development uses `redis://`, production uses `rediss://`)

4. **Redis Commander** (dev/docker only)
   - Web UI for Redis inspection
   - Available at port 8081

**Job Flow:**
```
WhatsApp → API Container → Redis Queue → Worker Container → Inventory Search API
                                                           ↓
                                                   WhatsApp API (send response)
```

**Key Features:**
- Separate API and worker processes
- Horizontal scaling of workers
- Job deduplication prevents duplicate processing
- Environment-specific configurations
- Resource limits in production

## 📋 Prerequisites

- **For Docker deployment**: Docker and Docker Compose
- **For local development**: Python 3.13+, Redis server
- WhatsApp Business API account
- Supabase account (for database)
- Inventory Search API endpoint (configured in env files)

## 🛠️ Installation

### Docker Setup (Recommended)

The easiest way to run the application is using Docker. We provide environment-specific configurations:

```bash
# Quick start - Development mode (detached, hot reload)
make dev-build

# View logs
make logs ENV=dev
```

**Available environments:**
- **Development** (`docker-compose.dev.yml`) - Hot reload, runs in detached mode, uses `.env.docker.dev`
- **Production** (`docker-compose.prod.yml`) - Production ready, runs in detached mode, uses `.env.docker.prod`

**All Docker commands run in detached mode** - containers start in the background and return your terminal prompt. Use `make logs ENV=<env>` to view output.

See [docs/DOCKER-QUICKSTART.md](docs/DOCKER-QUICKSTART.md) for quick reference or [docs/DOCKER.md](docs/DOCKER.md) for complete Docker documentation.

### Local Development (Without Docker)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whatsapp-chatbot
   ```

2. **Install UV package manager** (recommended)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Activate virtual environment**
   ```bash
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

5. **Start Redis locally**
   ```bash
   redis-server
   ```

## ⚙️ Configuration

### Environment Variables

The application supports multiple environments with Docker-specific configurations:

```bash
# For Docker development environment (hot reload, detached)
cp .env.example .env.docker.dev

# For Docker production environment (optimized, detached)
cp .env.example .env.docker.prod

# For local development (non-Docker)
cp .env.example .env.development

# For local production (non-Docker)
cp .env.example .env.production
```

**Environment file usage:**
- `.env.docker.dev` - Used by `docker-compose.dev.yml` for development (hot reload, detached mode)
- `.env.docker.prod` - Used by `docker-compose.prod.yml` for production (optimized, detached mode)
- `.env.development` - Used for local development without Docker
- `.env.production` - Used for local production without Docker

> 📖 See [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) for detailed environment configuration guide, migration instructions, and troubleshooting.

#### Required Configuration

**WhatsApp API Settings:**
```bash
WHATSAPP_ACCESS_TOKEN="your_access_token"
WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id"
WHATSAPP_WEBHOOK_VERIFICATION_TOKEN="your_verification_token"
WHATSAPP_APP_SECRET="your_app_secret"
```

**Redis Configuration:**
```bash
# Development (local Redis)
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD="your-password"

# Production (Upstash Redis with TLS)
REDIS_HOST="your-redis-host.upstash.io"
REDIS_PORT="6379"
REDIS_PASSWORD="your-upstash-password"
```

**Note:** The application automatically uses secure TLS connections (`rediss://`) in production mode and regular TCP (`redis://`) in development mode.

**Database Configuration:**
```bash
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_key"
```

**Optional - Monitoring:**
```bash
SENTRY_DSN="your_sentry_dsn"  # For error tracking
SENTRY_ENABLED="true"
```

### Environment Files

- `.env.development` - Local development (non-Docker)
- `.env.production` - Local production (non-Docker)
- `.env.docker.dev` - Docker development (hot reload, detached mode)
- `.env.docker.prod` - Docker production (optimized, detached mode)

## 📱 WhatsApp Integration

### 1. Setting Up WhatsApp Business API

1. **Create a Meta Developer Account**
   - Go to [Meta for Developers](https://developers.facebook.com/)
   - Create a new app with WhatsApp Business API

2. **Configure WhatsApp Business API**
   - Add WhatsApp product to your app
   - Get your access token and phone number ID
   - Set up webhook verification token

3. **Phone Number Setup**
   - Verify your business phone number
   - Complete business verification process

### 2. Webhook Configuration

**Webhook URL Format:**
```
https://your-domain.com/api/v1/hook/{customer_id}
```

**Required Webhook Events:**
- `messages` - For receiving messages
- `message_deliveries` - For delivery status (optional)

**Webhook Verification:**
The application automatically handles Meta's webhook verification process using the verification token.

### 3. Testing Webhook Locally

Use ngrok for local development:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Use the ngrok URL in Meta's webhook configuration
# Example: https://abc123.ngrok.io/api/v1/hook/your-customer-id
```

## 🚀 Running the Application

### Using Docker (Recommended)

**Quick Start with Makefile:**
```bash
# View all available commands
make help

# Development environment (hot reload, detached mode)
make dev-build

# Production environment (detached mode)
make prod-build

# View logs (since containers run in background)
make logs ENV=dev
make logs-api ENV=prod
make logs-worker ENV=prod

# Scale workers
make scale-workers WORKERS=5 ENV=prod
```

**Note:** All Docker commands run in **detached mode** - containers start in the background and your terminal prompt returns immediately. Use `make logs ENV=<env>` to view output.

**Using Docker Compose directly:**
```bash
# Development (runs in detached mode)
docker-compose -f docker-compose.dev.yml up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Production (detached mode)
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

**Note:** Both dev and prod environments run in detached mode. Use `docker-compose logs -f` to follow logs.

### Local Development (Without Docker)

```bash
# Start Redis
redis-server

# Start the API server (uses uvloop for better performance)
uv run python -m app.main

# Start background workers (separate terminal)
uv run arq app.workers.tasks.WorkerSettings
```

### VS Code Debugging

Use the provided launch configurations in `.vscode/launch.json`:
- **FastAPI: Development** - Debug API with hot reload
- **Arq Worker** - Debug background workers

## 📚 API Documentation

### Health Check
```http
GET /api/v1/health
```

### WhatsApp Webhook
```http
# Webhook verification (GET)
GET /api/v1/hook/{customer_id}?hub.verify_token={token}&hub.challenge={challenge}

# Receive messages (POST)
POST /api/v1/hook/{customer_id}
Content-Type: application/json
X-Hub-Signature-256: sha256={signature}
```

### Interactive API Documentation

When running locally, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🗄️ Database Integration

### Why Database is Needed

The application uses Supabase (PostgreSQL) for:

1. **Customer Management**: Store customer profiles and API keys
2. **Message History**: Log incoming/outgoing messages for audit
3. **User Sessions**: Track conversation states
4. **Configuration**: Store customer-specific settings

### Database Models

**Customer Model** (`app/models/customer.py`):
```python
class Customer(BaseModel):
    id: UUID | None = None
    name: str
    contact_email: str | None = None
    is_active: bool = True
    api_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### Database Setup

1. **Create Supabase Project**
   - Sign up at [Supabase](https://supabase.com/)
   - Create a new project
   - Get your project URL and API key

2. **Run Migrations**
   ```bash
   # Install Supabase CLI
   npm install -g supabase

   # Login and link project
   supabase login
   supabase link --project-ref your-project-ref

   # Run migrations
   supabase db push
   ```

## 🔐 Authentication & Security

### Customer Authentication

Each customer has a unique API key used in the webhook URL:
```
/api/v1/hook/{customer_api_key}
```

### Webhook Security

1. **Signature Verification**: All webhook requests are verified using Meta's signature
2. **Token Validation**: Webhook verification tokens prevent unauthorized access
3. **HTTPS Required**: Production deployments must use HTTPS

### Security Best Practices

- Store sensitive tokens in environment variables
- Use strong, unique verification tokens
- Enable HTTPS in production
- Implement rate limiting (recommended)
- Monitor failed authentication attempts

## 🚀 Deployment

### Docker Deployment (Recommended)

The application uses separate Dockerfiles for API and workers:
- **`Dockerfile`** - FastAPI API server with uvloop
- **`Dockerfile.worker`** - ARQ background workers

**Quick deployment:**
```bash
# Production deployment
make prod-build

# Or with docker-compose
docker-compose -f docker-compose.prod.yml up -d --build

# Scale workers for high load
make scale-workers WORKERS=5 ENV=prod
```

**Production features:**
- 2 worker replicas by default (configurable)
- Resource limits (CPU/Memory)
- Persistent Redis data volume
- Automatic restart policies
- No volume mounting (images are self-contained)
- Job deduplication for exactly-once processing

### Docker Images

**Build separate images:**
```bash
# API image
docker build -t whatsapp-chatbot-api -f Dockerfile .

# Worker image
docker build -t whatsapp-chatbot-worker -f Dockerfile.worker .
```

### Cloud Deployment Options

#### Docker-based Platforms

**AWS ECS/Fargate:**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-ecr-uri

# Push API image
docker build -t whatsapp-chatbot-api -f Dockerfile .
docker tag whatsapp-chatbot-api:latest your-ecr-uri/whatsapp-chatbot-api:latest
docker push your-ecr-uri/whatsapp-chatbot-api:latest

# Push Worker image
docker build -t whatsapp-chatbot-worker -f Dockerfile.worker .
docker tag whatsapp-chatbot-worker:latest your-ecr-uri/whatsapp-chatbot-worker:latest
docker push your-ecr-uri/whatsapp-chatbot-worker:latest
```

**DigitalOcean App Platform:**
- Use `docker-compose.prod.yml` as reference
- Deploy API and worker as separate services
- Connect to managed Redis database

**Google Cloud Run:**
- Deploy API container (scales to zero)
- Use Cloud Tasks or Pub/Sub for workers
- Connect to Redis via Memorystore

### Environment-Specific Configurations

**Production Checklist:**
- [ ] Update `.env.docker.prod` with production credentials
- [ ] Use managed Redis with TLS support (Upstash/AWS ElastiCache/Cloud Memorystore)
- [ ] Ensure `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` are set (app automatically uses TLS in production)
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up monitoring and logging (Sentry configured)
- [ ] Configure backup strategies for Redis
- [ ] Set resource limits in `docker-compose.prod.yml`
- [ ] Enable health checks and auto-restart
- [ ] Test webhook URLs are publicly accessible
- [ ] Scale workers based on expected message volume
- [ ] Configure rate limiting and DDoS protection

**Note on Redis Connection:**
The application automatically selects the appropriate connection protocol:
- **Development:** `redis://` (unencrypted TCP)
- **Production:** `rediss://` (TLS-encrypted TCP)

No additional configuration needed - just set `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.

### Kubernetes Deployment

See `docker-compose.prod.yml` for reference. Convert to Kubernetes manifests:
```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.31.2/kompose-linux-amd64 -o kompose

# Convert docker-compose to k8s
kompose convert -f docker-compose.prod.yml
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_whatsapp_service.py

# Run with verbose output
uv run pytest -v
```

### Test Structure

```
tests/
├── test_whatsapp_service.py    # WhatsApp service tests
├── api/
│   └── v1/
│       ├── contract/           # API contract tests
│       ├── integration/        # Integration tests
│       └── unit/              # Unit tests
```

### Testing Best Practices

1. **Mock External Services**: WhatsApp API, Redis, Database
2. **Test Message Processing**: Different message types and error cases
3. **Test Authentication**: Valid/invalid tokens and signatures
4. **Test Edge Cases**: Malformed webhooks, network failures

## ⚠️ Common Pitfalls

### WhatsApp API Issues

1. **Rate Limiting**
   - Meta enforces rate limits (1000 messages/day for test numbers)
   - Implement exponential backoff for failed requests
   - Monitor API usage in Meta Business Manager

2. **Webhook Verification**
   - Ensure verification token matches exactly
   - Webhook URL must be publicly accessible
   - Use HTTPS in production

3. **Message Format Errors**
   - Follow Meta's message format specifications
   - Validate phone number formats (+1234567890)
   - Handle different message types properly

### Redis/Queue Issues

2. **Worker Not Processing Jobs**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Monitor queue
   redis-cli monitor
   
   # Check worker logs (Docker - runs in detached mode)
   make logs-worker ENV=dev
   docker-compose -f docker-compose.dev.yml logs -f worker
   
   # Check worker logs (local)
   # View terminal where arq is running
   ```

2. **Duplicate Job Processing**
   - Job deduplication is enabled by default
   - Jobs are tracked in Redis with 1-hour TTL
   - Multiple workers are safe with deduplication

3. **Memory Issues**
   - Configure Redis memory limits in `redis.conf`
   - Monitor queue size: `redis-cli info memory`
   - Adjust worker resource limits in `docker-compose.prod.yml`

### Docker Issues

1. **Environment Variables**
   - Use correct env file for each environment:
     - `.env.development` for local dev
     - `.env.docker.dev` for Docker dev
     - `.env.docker.prod` for Docker production
     - `.env.production` for local production
   - Never commit `.env.*` files to git

2. **Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   make dev-build
   docker-compose -f docker-compose.dev.yml build --no-cache
   
   # Check container logs (runs in detached mode)
   make logs ENV=dev
   docker-compose -f docker-compose.dev.yml logs -f
   ```

3. **Worker Not Starting**
   ```bash
   # Verify worker is running ARQ (not API)
   docker-compose -f docker-compose.dev.yml logs worker
   
   # Should see: "Starting worker for 3 functions..."
   # NOT: "Uvicorn running on..."
   
   # Rebuild worker if needed
   docker-compose -f docker-compose.dev.yml build worker
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Stop conflicting services or change port in docker-compose
   ```

### Development Issues

1. **Database Connections**
   - Ensure Supabase project is active
   - Check connection strings and credentials
   - Monitor connection pool usage

2. **Hot Reload Not Working**
   - Ensure using development compose file: `make dev-build`
   - Check volume mounting in `docker-compose.dev.yml`
   - View logs to see if changes are detected: `make logs ENV=dev`
   - Restart containers if needed: `make dev-down && make dev-build`

## 🔧 Message Type Configuration

### Available Message Types

The application supports various WhatsApp message types:

```python
from app.services.whatsapp import WhatsAppMessageType

# Available types:
WhatsAppMessageType.TEXT        # Text messages
WhatsAppMessageType.IMAGE       # Image files
WhatsAppMessageType.VIDEO       # Video files  
WhatsAppMessageType.AUDIO       # Audio files
WhatsAppMessageType.DOCUMENT    # Documents (PDF, etc.)
WhatsAppMessageType.LOCATION    # Location sharing
WhatsAppMessageType.CONTACT     # Contact cards
WhatsAppMessageType.STICKER     # Stickers
WhatsAppMessageType.INTERACTIVE # Interactive messages
WhatsAppMessageType.BUTTON      # Button responses
WhatsAppMessageType.ORDER       # Order messages
WhatsAppMessageType.SYSTEM      # System messages
WhatsAppMessageType.UNKNOWN     # Unknown types
```

### Configuring Supported Types

```python
from app.services.whatsapp import WhatsAppMessageProcessor, WhatsAppMessageType

# Text only (default)
processor = WhatsAppMessageProcessor({WhatsAppMessageType.TEXT})

# Multiple types
processor = WhatsAppMessageProcessor({
    WhatsAppMessageType.TEXT,
    WhatsAppMessageType.IMAGE,
    WhatsAppMessageType.VIDEO,
    WhatsAppMessageType.AUDIO
})
```

## 🤝 Contributing

### Development Setup

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd whatsapp-chatbot
   uv sync --dev
   ```

2. **Start development environment**
   ```bash
   # Using Docker (recommended) - runs in detached mode
   make dev-build
   
   # View logs
   make logs ENV=dev
   
   # Or locally
   redis-server  # Terminal 1
   uv run python -m app.main  # Terminal 2
   uv run arq app.workers.tasks.WorkerSettings  # Terminal 3
   ```

3. **Run linting and formatting**
   ```bash
   make lint
   # or
   uvx ruff check . --fix
   uvx ruff format .
   ```

4. **Run tests before committing**
   ```bash
   make test
   # or
   uv run pytest
   ```

5. **View Docker logs (since containers run in background)**
   ```bash
   make logs ENV=dev
   ```

### Code Standards

- Follow PEP 8 style guidelines
- Add type annotations to all functions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages
- Test with Docker before submitting PR

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run linting and tests: `make lint && make test`
5. Test with Docker: `make docker-build`
6. Submit a pull request with description

### Docker Development Tips

- Use `make dev-build` for hot-reload development (runs in detached mode)
- View logs: `make logs ENV=dev`
- Check logs after starting: `make logs-api ENV=dev` or `make logs-worker ENV=dev`
- Rebuild after dependency changes: `make dev-down && make dev-build`
- Test workers separately: `docker-compose -f docker-compose.dev.yml logs -f worker`

## 📊 Quick Reference

### Media Management CLI

The project includes a powerful CLI tool for managing customers, cars, and media:

```bash
# Quick usage
./media list-customers
./media list-cars -c "CUSTOMER-UUID"
./media list-media -c "CUSTOMER-UUID" -i CAR-ID
./media upsert-media -c "CUSTOMER-UUID" -i CAR-ID -u "https://cdn.com/car.jpg" --primary

# Interactive mode
./media upsert-media -c "CUSTOMER-UUID" -i CAR-ID --interactive
```

See [docs/MEDIA_CLI.md](docs/MEDIA_CLI.md) for complete CLI documentation and [docs/CAR_MEDIA.md](docs/CAR_MEDIA.md) for car media system details.

### Environment Files Quick Guide

```bash
# Which file should I use?
Local dev (no Docker)    → .env.development
Local production         → .env.production
Docker development       → .env.docker.dev (detached mode)
Docker production        → .env.docker.prod (detached mode)
```

See [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) for complete environment configuration guide.

### Docker Commands Cheat Sheet

| Task | Command |
|------|---------|
| Start development (detached) | `make dev-build` |
| Start production (detached) | `make prod-build` |
| View dev logs | `make logs ENV=dev` |
| View prod logs | `make logs ENV=prod` |
| Scale workers | `make scale-workers WORKERS=5 ENV=prod` |
| Stop services | `make dev-down` / `make prod-down` |
| Clean everything | `make clean` |
| Run tests | `make test` |
| Format code | `make lint` |

**Note:** All Docker commands run in detached mode. Use `make logs` to view output.

### Environment Files

| File | Purpose | Usage |
|------|---------|-------|
| `.env.development` | Local dev (non-Docker) | Hot reload, local services |
| `.env.production` | Local production (non-Docker) | Production without Docker |
| `.env.docker.dev` | Docker development | Hot reload in containers (detached) |
| `.env.docker.prod` | Docker production | Production deployment (detached) |

### Service URLs

| Service | Development | Docker | Production |
|---------|------------|--------|------------|
| API | localhost:8000 | localhost:8000 | your-domain.com |
| Docs | localhost:8000/docs | localhost:8000/docs | your-domain.com/docs |
| Redis Commander | localhost:8081 | localhost:8081 | N/A |
| Redis | localhost:6379 | redis:6379 | managed service |

### Key Files

| File | Description |
|------|-------------|
| `Dockerfile` | API container definition |
| `Dockerfile.worker` | Worker container definition |
| `docker-compose.dev.yml` | Development environment (detached) |
| `docker-compose.prod.yml` | Production environment (detached) |
| `Makefile` | Quick commands |
| `.env.docker.dev` | Docker dev configuration |
| `.env.docker.prod` | Docker prod configuration |

### Documentation

| File | Description |
|------|-------------|
| [README.md](README.md) | Project overview and getting started |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operational guide and workflows |
| [docs/DOCKER.md](docs/DOCKER.md) | Complete Docker deployment guide |
| [docs/DOCKER-QUICKSTART.md](docs/DOCKER-QUICKSTART.md) | Quick Docker reference |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | Environment variables guide |
| [docs/AGENTS.md](docs/AGENTS.md) | Agent configuration and architecture |
| [docs/CAR_MEDIA.md](docs/CAR_MEDIA.md) | Car media system documentation |
| [docs/MEDIA_CLI.md](docs/MEDIA_CLI.md) | Media management CLI tool guide |

## �📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/examples` directory for usage examples
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

## 🔗 Related Resources

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ARQ (Redis Queue) Documentation](https://arq-docs.helpmanual.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [UV Package Manager](https://docs.astral.sh/uv/)
