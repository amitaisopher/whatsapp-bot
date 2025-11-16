# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Dead Letter Queue (DLQ)** for failed worker jobs with 7-day retention
- **DLQ Management CLI** (`python -m app.workers.dlq_manager`) with commands:
  - `count` - Show number of jobs in DLQ
  - `list` - List all failed jobs
  - `stats` - View statistics by function and error type
  - `get <job_key>` - View detailed job information
  - `remove <job_key>` - Remove specific job from DLQ
  - `clear` - Clear all jobs from DLQ
- **Car Media Management System**:
  - Database schema with RLS policies for multi-tenancy
  - Support for images and videos with metadata
  - Media ordering and primary image selection
  - Storage provider support (Cloudinary, S3, Azure, local)
- **Media CLI Tool** (`./media`) for managing car media:
  - List customers, cars, and media items
  - Upsert media with validation
  - Delete media items
  - Set primary images
- **Exponential Backoff Retry Logic** for worker jobs:
  - 30s, 60s, 120s delays (capped at 600s)
  - Automatic retry up to 3 attempts
  - Comprehensive failure logging
- **Job Deduplication** to prevent duplicate processing
- **Worker Error Handling Documentation** (`docs/WORKER_ERROR_HANDLING.md`)
- **Media CLI Documentation** (`docs/MEDIA_CLI.md`)
- **Car Media System Documentation** (`docs/CAR_MEDIA.md`)

### Changed
- **Refactored Worker Module** into focused, maintainable components:
  - `job_status.py` - Job status enum definitions
  - `job_deduplication.py` - Redis-based deduplication logic
  - `error_handling.py` - Error handling, retry, and DLQ operations
  - `task_functions.py` - Task implementations
  - `lifecycle.py` - Worker startup and shutdown
  - `tasks.py` - Main worker configuration
- **Improved Error Handling** with structured logging and detailed context
- **Enhanced Type Hints** throughout worker modules for better IDE support
- **Updated Datetime Usage** from deprecated `datetime.utcnow()` to `datetime.now(timezone.utc)`

### Fixed
- **Redis Connection** using `aclose()` instead of deprecated `close()`
- **UUID Serialization** in car media service using `model_dump(mode='json')`
- **Import Paths** updated in tests after worker refactoring
- **Test Coverage** for worker error handling (13 new tests, 45 total passing)

### Documentation
- Added comprehensive `app/workers/README.md` with:
  - Module structure explanation
  - Usage examples
  - Guide for adding new tasks
  - Configuration details
- Added worker module docstrings and type hints
- Created detailed documentation for all new features

## [1.0.0] - 2025-11-01

### Added
- Initial WhatsApp chatbot implementation
- ARQ worker queue system for async job processing
- Integration with inventory search service
- WhatsApp message handling (incoming and outgoing)
- Redis-based job queue with persistence
- Docker Compose setup for development and production
- FastAPI REST API with health checks
- PostgreSQL/Supabase integration with Row-Level Security
- Environment-based configuration management
- Structured logging with context
- Comprehensive test suite

### Infrastructure
- Multi-container Docker setup (API, Worker, Redis, PostgreSQL)
- Docker volumes for Redis and database persistence
- Environment-specific configuration (.env files)
- Makefile for common development tasks

### Security
- Row-Level Security (RLS) policies for multi-tenant data isolation
- API key authentication for WhatsApp webhooks
- Secure Redis connection with password authentication
- Environment variable management for secrets
