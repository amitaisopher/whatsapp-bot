# Docker Environment Guide

## Environment-Specific Docker Compose Files

The project includes three Docker Compose configurations for different environments:

### 1. **Development** (`docker-compose.dev.yml`)
- Uses `.env.docker.dev`
- Hot-reload enabled with volume mapping
- Redis Commander UI available
- Best for: Local development with code changes in containers

### 2. **Docker** (`docker-compose.docker.yml`)
- Uses `.env.docker`
- Standard local Docker setup
- Redis Commander UI available
- Best for: Testing Docker deployment locally

### 3. **Production** (`docker-compose.prod.yml`)
- Uses `.env.docker.prod`
- No volume mapping (baked into image)
- Resource limits configured
- Multiple worker replicas (default: 2)
- Persistent Redis data volume
- Custom network configuration
- Best for: Production deployment

## Quick Start Commands

### Using Docker Compose Directly

```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Docker (Local)
docker-compose -f docker-compose.docker.yml up --build

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

### Using Makefile (Recommended)

```bash
# Development
make dev-build
make dev

# Docker (Local)
make docker-build
make docker

# Production
make prod-build
make prod
```

## Common Operations

### Start Services

```bash
# Development
make dev
# or
docker-compose -f docker-compose.dev.yml up

# Production
make prod
# or
docker-compose -f docker-compose.prod.yml up -d
```

### View Logs

```bash
# All services
make logs ENV=dev
make logs ENV=docker
make logs ENV=prod

# Specific service
make logs-api ENV=prod
make logs-worker ENV=prod

# Or with docker-compose
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f worker
```

### Scale Workers

```bash
# Scale to 3 workers in production
make scale-workers WORKERS=3 ENV=prod

# Or with docker-compose
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

### Stop Services

```bash
# Development
make dev-down

# Production
make prod-down

# Or with docker-compose
docker-compose -f docker-compose.prod.yml down
```

### Restart Services

```bash
# Restart API
make restart-api ENV=prod

# Restart workers
make restart-worker ENV=prod
```

## Service Access

### API Endpoints
- Development: http://localhost:8000
- Docker: http://localhost:8000
- Production: http://localhost:8000 (configure nginx/load balancer)

### Redis Commander (Dev/Docker only)
- URL: http://localhost:8081
- Not included in production for security

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Files

Ensure you have the correct environment files:

```bash
.env.docker.dev    # Docker development settings
.env.docker        # Docker local testing settings
.env.docker.prod   # Docker production settings
```

Copy from example:
```bash
cp .env.example .env.docker.dev
cp .env.example .env.docker
cp .env.example .env.docker.prod
```

Then edit each file with environment-specific values.

**Important Notes:**
- Docker environments use `.env.docker.*` files
- Local (non-Docker) development uses `.env.development`
- Keep production credentials separate and secure
- Never commit `.env.*` files to version control

## Resource Management

### Production Resource Limits

**API Service:**
- CPU: 1.0 limit, 0.5 reserved
- Memory: 1GB limit, 512MB reserved

**Worker Service:**
- CPU: 0.5 limit, 0.25 reserved
- Memory: 512MB limit, 256MB reserved
- Default replicas: 2

Adjust in `docker-compose.prod.yml` based on your server capacity.

### Clean Up

```bash
# Remove all containers and volumes
make clean

# Or manually
docker-compose -f docker-compose.prod.yml down -v
docker system prune -f
```

## Testing

```bash
# Run tests
make test

# Run with coverage
make test-coverage

# Lint and format
make lint
```

## Shell Access

```bash
# Access API container
make shell-api ENV=prod

# Access worker container
make shell-worker ENV=prod

# Or with docker-compose
docker-compose -f docker-compose.prod.yml exec api /bin/bash
docker-compose -f docker-compose.prod.yml exec worker /bin/bash
```

## Troubleshooting

### Check Service Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### View Service Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Rebuild Specific Service
```bash
docker-compose -f docker-compose.prod.yml build api
docker-compose -f docker-compose.prod.yml build worker
```

### Remove and Recreate
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate
```

## Production Deployment Checklist

- [ ] Update `.env.docker.prod` with production credentials
- [ ] Configure proper Redis password in `redis.conf`
- [ ] Set up HTTPS/SSL (nginx, Caddy, or cloud load balancer)
- [ ] Configure domain names
- [ ] Set up monitoring (Sentry DSN configured)
- [ ] Configure backup strategy for Redis data
- [ ] Set appropriate resource limits
- [ ] Configure firewall rules
- [ ] Set up logging aggregation
- [ ] Test webhook URLs are accessible
- [ ] Verify WhatsApp API credentials
- [ ] Scale workers based on expected load

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Deploy to Production
  run: |
    docker-compose -f docker-compose.prod.yml pull
    docker-compose -f docker-compose.prod.yml up -d --build
```

### Manual Deployment

```bash
# On production server
git pull origin main
make prod-build
```
