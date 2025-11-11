# Environment Files Guide

## Overview

This project uses different environment files for different deployment scenarios:

### Environment File Structure

```
.env.development     # Local development (non-Docker)
.env.docker.dev      # Docker development (with hot reload)
.env.docker          # Docker local testing
.env.docker.prod     # Docker production
.env.example         # Template file (committed to git)
```

## Environment File Usage

### 1. Local Development (Non-Docker)

**File:** `.env.development`

**Used by:**
- Local Python application
- VS Code debugging
- Direct `uv run` commands

**Example:**
```bash
# Uses local services
REDIS_HOST="localhost"
REDIS_PORT="6379"
SEARCH_API_URL="http://localhost:8005"
```

### 2. Docker Development

**File:** `.env.docker.dev`

**Used by:** `docker-compose.dev.yml`

**Features:**
- Hot reload enabled
- Volume mounted for code changes
- Redis Commander UI available

**Example:**
```bash
# Uses Docker service names
REDIS_HOST="redis"
REDIS_PORT="6379"
SEARCH_API_URL="http://host.docker.internal:8005"
```

### 3. Docker Local Testing

**File:** `.env.docker`

**Used by:** `docker-compose.docker.yml`

**Features:**
- Standard containerized setup
- No hot reload
- Redis Commander UI available

**Example:**
```bash
# Uses Docker service names
REDIS_HOST="redis"
REDIS_PORT="6379"
SEARCH_API_URL="http://host.docker.internal:8005"
```

### 4. Docker Production

**File:** `.env.docker.prod`

**Used by:** `docker-compose.prod.yml`

**Features:**
- Production credentials
- Managed Redis services
- No Redis Commander
- Resource limits enforced

**Example:**
```bash
# Uses production services
REDIS_HOST="production-redis.example.com"
REDIS_PORT="6379"
SEARCH_API_URL="https://api.production.example.com"
```

## Setup Instructions

### Initial Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env.docker.dev
   cp .env.example .env.docker
   cp .env.example .env.docker.prod
   cp .env.example .env.development  # Optional, for local dev
   ```

2. **Edit each file with appropriate values:**
   ```bash
   # Development files - use localhost or Docker service names
   nano .env.docker.dev
   nano .env.docker
   nano .env.development
   
   # Production file - use production credentials
   nano .env.docker.prod
   ```

### Key Differences Between Files

| Variable | Local Dev | Docker Dev | Docker Prod |
|----------|-----------|------------|-------------|
| `REDIS_HOST` | `localhost` | `redis` | `prod-redis.example.com` |
| `SEARCH_API_URL` | `http://localhost:8005` | `http://host.docker.internal:8005` | `https://api.prod.com` |
| `WHATSAPP_ACCESS_TOKEN` | Test token | Test token | Production token |
| `SENTRY_DSN` | Empty/test | Empty/test | Production DSN |

## Common Variables

All environment files should include:

### Required Variables

```bash
# Redis Configuration
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=

# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WEBHOOK_VERIFICATION_TOKEN=
WHATSAPP_APP_SECRET=

# Database
SUPABASE_URL=
SUPABASE_KEY=

# Search API
SEARCH_API_URL=
INVENTORY_SEARCH_TIMEOUT=
```

**Note on Redis Configuration:**
- **Development:** Uses regular TCP connection (`redis://`) to localhost or Docker service
- **Production:** Automatically uses secure TLS connection (`rediss://`) to managed Redis (e.g., Upstash)
- The application detects the environment and applies the appropriate connection protocol

### Optional Variables

```bash
# Monitoring (recommended for production)
SENTRY_DSN=
SENTRY_ENABLED=true

# Debug (development only)
DEBUG=true
LOG_LEVEL=DEBUG
```

## Security Best Practices

### ✅ Do's

- Copy `.env.example` as a starting point
- Use different credentials for each environment
- Keep production credentials separate and secure
- Use strong passwords for Redis
- Rotate tokens regularly
- Use managed services in production

### ❌ Don'ts

- Never commit `.env.*` files to git
- Don't use production credentials in development
- Don't share environment files
- Don't hardcode credentials in code
- Don't use the same tokens across environments

## Troubleshooting

### Issue: "Cannot connect to Redis"

**Local Dev:**
```bash
# Check if Redis is running
redis-cli ping
```

**Docker:**
```bash
# Check Redis service
docker-compose -f docker-compose.docker.yml logs redis

# Verify REDIS_HOST is set to "redis"
```

### Issue: "Search API timeout"

**Local Dev:**
```bash
# Ensure Search API is running
curl http://localhost:8005/health
```

**Docker:**
```bash
# Use host.docker.internal to reach host services
SEARCH_API_URL="http://host.docker.internal:8005"
```

### Issue: "WhatsApp webhook verification failed"

- Check `WHATSAPP_WEBHOOK_VERIFICATION_TOKEN` matches Meta configuration
- Ensure webhook URL is publicly accessible (use ngrok for local testing)

## Migration from Old Setup

If you're migrating from the old environment file structure:

### Recent Changes (November 2025)

**Removed Variables:**
- `UPSTASH_REDIS_REST_URL` - No longer needed
- `UPSTASH_REDIS_REST_TOKEN` - No longer needed

**Why:** The application now connects directly to Redis using TCP/TLS connections instead of HTTP REST API. This provides:
- Better performance (native Redis protocol)
- Lower latency
- Support for all Redis features
- Automatic TLS in production

**Migration Steps:**
1. Remove `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` from your environment files
2. Ensure `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` are set correctly
3. For Upstash Redis, use the native Redis endpoint (not the REST endpoint)
   - Example: `REDIS_HOST="your-instance.upstash.io"`
   - The application will automatically use `rediss://` (TLS) in production

### Old Structure
```
.env.development  # Used for everything
.env.production   # Used for production
```

### New Structure
```
.env.development    # Local dev only (non-Docker)
.env.docker.dev     # Docker development
.env.docker         # Docker local testing  
.env.docker.prod    # Docker production
```

### Migration Steps

1. **Backup existing files:**
   ```bash
   cp .env.development .env.development.backup
   cp .env.production .env.production.backup
   ```

2. **Create new Docker environment files:**
   ```bash
   # For Docker development (from old .env.development)
   cp .env.development .env.docker.dev
   # Edit REDIS_HOST to "redis" instead of "localhost"
   
   # For Docker production (from old .env.production)
   cp .env.production .env.docker.prod
   ```

3. **Update Redis host in Docker files:**
   ```bash
   # In .env.docker.dev and .env.docker
   sed -i 's/REDIS_HOST="localhost"/REDIS_HOST="redis"/' .env.docker.dev
   sed -i 's/REDIS_HOST="localhost"/REDIS_HOST="redis"/' .env.docker
   ```

4. **Test each environment:**
   ```bash
   make dev          # Should use .env.docker.dev
   make docker       # Should use .env.docker
   make prod         # Should use .env.docker.prod
   ```

## Quick Reference

### Which file to use?

```bash
# Running locally without Docker?
→ Use .env.development

# Running with docker-compose.dev.yml?
→ Use .env.docker.dev

# Running with docker-compose.docker.yml?
→ Use .env.docker

# Running with docker-compose.prod.yml?
→ Use .env.docker.prod
```

### Check which file is loaded

```bash
# Check dev environment
docker-compose -f docker-compose.dev.yml config | grep env_file

# Check prod environment
docker-compose -f docker-compose.prod.yml config | grep env_file
```
