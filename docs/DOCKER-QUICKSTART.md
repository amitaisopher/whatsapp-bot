# Quick Start - Docker Environments

## 🚀 Quick Commands

```bash
# View all available commands
make help

# Development
make dev-build      # Start development with hot reload

# Docker (Local)
make docker-build   # Start local Docker environment

# Production
make prod-build     # Start production (detached mode)
make logs ENV=prod  # View production logs
```

## 📁 Docker Compose Files

| File | Environment | Config File | Use Case |
|------|------------|-------------|----------|
| `docker-compose.dev.yml` | Development | `.env.docker.dev` | Local dev with hot reload |
| `docker-compose.docker.yml` | Docker | `.env.docker` | Local Docker testing |
| `docker-compose.prod.yml` | Production | `.env.docker.prod` | Production deployment |

## 🔧 Environment Setup

1. **Copy environment files:**
   ```bash
   cp .env.example .env.docker.dev
   cp .env.example .env.docker
   cp .env.example .env.docker.prod
   ```

2. **Edit each file** with environment-specific values

3. **Start your environment:**
   ```bash
   make dev-build    # Development
   make docker-build # Docker
   make prod-build   # Production
   ```

## 📊 Common Tasks

```bash
# View logs
make logs ENV=prod
make logs-api ENV=prod
make logs-worker ENV=prod

# Scale workers
make scale-workers WORKERS=5 ENV=prod

# Restart services
make restart-api ENV=prod
make restart-worker ENV=prod

# Clean everything
make clean
```

## 📖 Full Documentation

See [DOCKER.md](DOCKER.md) for complete documentation.
