# WhatsApp Chatbot

A production-ready WhatsApp chatbot built with FastAPI, Redis, and the WhatsApp Business API. This application provides a scalable foundation for building WhatsApp-based automation and customer service solutions.

## 🚀 Features

- **WhatsApp Business API Integration**: Full webhook support for receiving and sending messages
- **Async Message Processing**: Background job processing with Redis queues using ARQ
- **Type-Safe Message Handling**: Enum-based message type system for better maintainability
- **Multi-Customer Support**: Isolated customer environments with API key authentication
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

## 📋 Prerequisites

- Python 3.13+
- Redis server
- WhatsApp Business API account
- Supabase account (for database)
- Upstash Redis (optional, for production)

## 🛠️ Installation

### Local Development

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

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   # Development environment
   docker-compose up --build
   
   # Production environment
   ENV_FILE=.env.production docker-compose up --build
   ```

## ⚙️ Configuration

### Environment Variables

Copy the example environment file and configure:

```bash
cp .env.example .env.development
```

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
# Local Redis
UPSTASH_REDIS_HOST="localhost"
UPSTASH_REDIS_PORT="6379"
UPSTASH_REDIS_PASSWORD="your-password"

# Or Upstash Redis (production)
UPSTASH_REDIS_REST_URL="your_upstash_url"
UPSTASH_REDIS_REST_TOKEN="your_upstash_token"
```

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

- `.env.development` - Local development
- `.env.production` - Production deployment
- `.env.docker` - Docker containerized environments

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

### Development Mode

```bash
# Start Redis (if not using Docker)
redis-server

# Start the API server
uv run uvicorn app.main:main --reload --host 0.0.0.0 --port 8000

# Start background workers (separate terminal)
uv run arq app.workers.tasks.WorkerSettings
```

### Docker Mode

```bash
# Start all services
docker-compose up

# View logs
docker-compose logs -f api
docker-compose logs -f worker
```

### Production Mode

```bash
# Set environment
export ENV_FILE=.env.production

# Start with production settings
docker-compose -f docker-compose.yml up -d
```

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

### Docker Deployment

1. **Build Production Image**
   ```bash
   docker build -t whatsapp-chatbot .
   ```

2. **Deploy with Docker Compose**
   ```bash
   ENV_FILE=.env.production docker-compose up -d
   ```

### Cloud Deployment Options

#### AWS ECS/Fargate
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-ecr-uri
docker build -t whatsapp-chatbot .
docker tag whatsapp-chatbot:latest your-ecr-uri/whatsapp-chatbot:latest
docker push your-ecr-uri/whatsapp-chatbot:latest
```

#### Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set WHATSAPP_ACCESS_TOKEN=your_token

# Deploy
git push heroku main
```

#### DigitalOcean App Platform
Use the provided `docker-compose.yml` or create an app spec:

```yaml
name: whatsapp-chatbot
services:
- name: api
  image:
    registry_type: DOCKER_HUB
    registry: your-username
    repository: whatsapp-chatbot
    tag: latest
  http_port: 8000
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
```

### Environment-Specific Configurations

**Production Checklist:**
- [ ] Use managed Redis (Upstash/AWS ElastiCache)
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies
- [ ] Set resource limits and scaling policies
- [ ] Enable health checks

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

1. **Worker Not Processing Jobs**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Monitor queue
   redis-cli monitor
   
   # Check worker logs
   docker-compose logs worker
   ```

2. **Memory Issues**
   - Configure Redis memory limits
   - Implement job cleanup policies
   - Monitor queue size

### Development Issues

1. **Environment Variables**
   - Always use `.env.development` for local development
   - Never commit sensitive tokens to git
   - Use different tokens for dev/staging/production

2. **Database Connections**
   - Ensure Supabase project is active
   - Check connection strings and credentials
   - Monitor connection pool usage

3. **Docker Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker-compose build --no-cache
   
   # Check container logs
   docker-compose logs api
   ```

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

1. **Install development dependencies**
   ```bash
   uv sync --dev
   ```

2. **Run linting and formatting**
   ```bash
   uvx ruff check . --fix
   uvx ruff format .
   ```

3. **Run tests before committing**
   ```bash
   uv run pytest
   ```

### Code Standards

- Follow PEP 8 style guidelines
- Add type annotations to all functions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run linting and tests
5. Submit a pull request with description

## 📄 License

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
