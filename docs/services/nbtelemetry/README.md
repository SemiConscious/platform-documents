# NBTelemetry Overview

![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![Multi-Language](https://img.shields.io/badge/Stack-Multi--Language-blueviolet)
![PHP](https://img.shields.io/badge/PHP-Backend-777BB4?logo=php&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-UI%20Components-F7DF1E?logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-Proprietary-red)
![API Endpoints](https://img.shields.io/badge/API%20Endpoints-19-green)

> **Enterprise-grade telemetry service for transcription and call analysis, integrating with multiple NLE providers to deliver actionable insights from call recordings.**

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Documentation Index](#documentation-index)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Introduction

NBTelemetry is a comprehensive telemetry and analytics service designed to process, analyze, and visualize call recordings at scale. The service acts as a unified integration layer for multiple Natural Language Engine (NLE) providers—including IBM Watson, Google Cloud Speech-to-Text, and VoiceBase—enabling organizations to extract valuable insights from their voice communications.

### What NBTelemetry Solves

Modern contact centers and communication platforms generate thousands of hours of call recordings daily. NBTelemetry addresses the challenge of:

- **Transcription at Scale**: Automatically converting audio recordings to searchable, analyzable text
- **Provider Flexibility**: Avoiding vendor lock-in by supporting multiple NLE providers
- **Actionable Analytics**: Extracting talk time metrics, sentiment analysis, and conversation patterns
- **Visualization**: Providing interactive UI components for exploring transcripts and analytics

### Who Should Use This Service

NBTelemetry is built for:

- **Backend Developers** integrating call analytics into existing platforms
- **DevOps Engineers** deploying and scaling transcription infrastructure
- **Data Engineers** building analytics pipelines from call data
- **Frontend Developers** implementing transcript visualization components

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Multi-Provider Transcription** | Seamlessly switch between Watson, Google, and VoiceBase NLE providers |
| 📊 **Talk Time Analysis** | Detailed breakdown of speaker participation and conversation dynamics |
| 💭 **Sentiment Analysis** | AI-powered emotional tone detection throughout conversations |
| 👥 **User & Organization Management** | Multi-tenant architecture with role-based access control |
| 🖥️ **Interactive Visualization** | JavaScript UI components for transcript exploration |
| 🐳 **Docker-Native** | Production-ready containerized deployment |
| 🔌 **RESTful API** | 19 well-documented endpoints for full programmatic access |

---

## Architecture Overview

NBTelemetry follows a modular, microservices-friendly architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Applications                          │
│              (Web Apps, Mobile Apps, Third-party Services)          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      NBTelemetry API Layer                          │
│                    (RESTful API - 19 Endpoints)                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Transcription│  │  Analytics   │  │   User & Organization    │  │
│  │   Service    │  │   Engine     │  │      Management          │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────────┘  │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              NLE Provider Abstraction Layer                  │   │
│  ├─────────────────┬─────────────────┬─────────────────────────┤   │
│  │  IBM Watson     │  Google Cloud   │      VoiceBase          │   │
│  │  Speech-to-Text │  Speech-to-Text │      API                │   │
│  └─────────────────┴─────────────────┴─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Storage Layer                           │
│            (Transcripts, Analytics, User Data, Metadata)            │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

1. **API Layer**: RESTful interface handling authentication, request routing, and response formatting
2. **Transcription Service**: Manages audio ingestion, provider selection, and transcript generation
3. **Analytics Engine**: Processes transcripts for talk time, sentiment, and pattern analysis
4. **NLE Abstraction Layer**: Unified interface for interacting with multiple speech-to-text providers
5. **UI Components**: JavaScript modules for interactive transcript visualization

---

## Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **PHP** (version 8.1 or higher) - for local development
- **Composer** (version 2.x) - PHP dependency manager
- **Git** for cloning the repository

### Installation

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd nbtelemetry
```

#### Step 2: Install PHP Dependencies

```bash
# Install production dependencies
composer install --no-dev --optimize-autoloader

# For development environment (includes testing tools)
composer install
```

#### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

#### Step 4: Start with Docker

```bash
# Build and start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f nbtelemetry
```

#### Step 5: Verify Installation

```bash
# Check API health endpoint
curl http://localhost:8080/api/health

# Expected response:
# {"status": "healthy", "version": "1.0.0", "providers": ["watson", "google", "voicebase"]}
```

### Quick API Test

Once the service is running, test the transcription endpoint:

```bash
curl -X POST http://localhost:8080/api/v1/transcriptions \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/recording.wav",
    "provider": "watson",
    "options": {
      "language": "en-US",
      "enable_sentiment": true,
      "enable_speaker_diarization": true
    }
  }'
```

---

## Environment Variables

NBTelemetry is configured through environment variables. Below is a comprehensive reference:

### Core Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_ENV` | Application environment (`production`, `staging`, `development`) | `production` | Yes |
| `APP_DEBUG` | Enable debug mode (set to `false` in production) | `false` | No |
| `APP_URL` | Base URL for the application | `http://localhost:8080` | Yes |
| `LOG_LEVEL` | Logging verbosity (`debug`, `info`, `warning`, `error`) | `info` | No |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_CONNECTION` | Database driver (`mysql`, `pgsql`) | `mysql` | Yes |
| `DB_HOST` | Database server hostname | `localhost` | Yes |
| `DB_PORT` | Database server port | `3306` | Yes |
| `DB_DATABASE` | Database name | `nbtelemetry` | Yes |
| `DB_USERNAME` | Database username | - | Yes |
| `DB_PASSWORD` | Database password | - | Yes |

### NLE Provider Credentials

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WATSON_API_KEY` | IBM Watson Speech-to-Text API key | - | Conditional |
| `WATSON_SERVICE_URL` | Watson service endpoint URL | - | Conditional |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud credentials JSON | - | Conditional |
| `VOICEBASE_API_KEY` | VoiceBase API key | - | Conditional |
| `VOICEBASE_API_SECRET` | VoiceBase API secret | - | Conditional |
| `DEFAULT_NLE_PROVIDER` | Default provider when not specified | `watson` | No |

### Storage Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STORAGE_DRIVER` | Storage backend (`local`, `s3`, `gcs`) | `local` | No |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 storage | - | Conditional |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 storage | - | Conditional |
| `AWS_DEFAULT_REGION` | AWS region for S3 | `us-east-1` | Conditional |
| `AWS_BUCKET` | S3 bucket name | - | Conditional |

### Example `.env` File

```env
# Application
APP_ENV=production
APP_DEBUG=false
APP_URL=https://telemetry.yourcompany.com
LOG_LEVEL=info

# Database
DB_CONNECTION=mysql
DB_HOST=db.internal
DB_PORT=3306
DB_DATABASE=nbtelemetry
DB_USERNAME=nbtelemetry_user
DB_PASSWORD=secure_password_here

# NLE Providers
WATSON_API_KEY=your_watson_api_key
WATSON_SERVICE_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-cloud.json
VOICEBASE_API_KEY=your_voicebase_key
VOICEBASE_API_SECRET=your_voicebase_secret
DEFAULT_NLE_PROVIDER=watson

# Storage
STORAGE_DRIVER=s3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=nbtelemetry-recordings
```

---

## Docker Deployment

NBTelemetry is designed for containerized deployment. The following sections cover various deployment scenarios.

### Basic Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  nbtelemetry:
    image: nbtelemetry:latest
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - APP_ENV=production
      - DB_HOST=database
      - DB_DATABASE=nbtelemetry
      - DB_USERNAME=nbtelemetry
      - DB_PASSWORD=${DB_PASSWORD}
    depends_on:
      database:
        condition: service_healthy
    volumes:
      - ./storage:/app/storage
      - ./credentials:/app/credentials:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  database:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=nbtelemetry
      - MYSQL_USER=nbtelemetry
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:
```

### Production Deployment Commands

```bash
# Build the production image
docker-compose build --no-cache

# Start services in detached mode
docker-compose up -d

# Run database migrations
docker-compose exec nbtelemetry php artisan migrate --force

# Scale the API service for high availability
docker-compose up -d --scale nbtelemetry=3

# View real-time logs
docker-compose logs -f nbtelemetry

# Graceful shutdown
docker-compose down
```

### Dockerfile Overview

```dockerfile
FROM php:8.2-fpm-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    libpng-dev \
    oniguruma-dev \
    libxml2-dev \
    zip \
    unzip

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /app

# Copy composer files first for better caching
COPY composer.json composer.lock ./

# Install dependencies
RUN composer install --no-dev --optimize-autoloader --no-scripts

# Copy application code
COPY . .

# Set permissions
RUN chown -R www-data:www-data /app/storage /app/bootstrap/cache

# Expose port
EXPOSE 8080

CMD ["php-fpm"]
```

---

## API Reference

NBTelemetry exposes 19 RESTful API endpoints organized into logical groups. Below is a quick reference:

### Transcription Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/transcriptions` | Submit a new transcription job |
| `GET` | `/api/v1/transcriptions/{id}` | Retrieve transcription status and results |
| `GET` | `/api/v1/transcriptions` | List all transcriptions with filtering |
| `DELETE` | `/api/v1/transcriptions/{id}` | Delete a transcription record |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/talk-time/{id}` | Get talk time analysis for a call |
| `GET` | `/api/v1/analytics/sentiment/{id}` | Retrieve sentiment analysis results |
| `GET` | `/api/v1/analytics/summary/{id}` | Get comprehensive call summary |

### Organization & User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/organizations` | List organizations |
| `POST` | `/api/v1/organizations` | Create new organization |
| `GET` | `/api/v1/users` | List users |
| `POST` | `/api/v1/users` | Create new user |

For complete API documentation including request/response schemas, see the [API Overview](docs/api/README.md).

---

## Documentation Index

Comprehensive documentation is available in the following sections:

| Document | Description |
|----------|-------------|
| 📘 [API Overview](docs/api/README.md) | Complete API reference with all 19 endpoints, request/response schemas, and authentication details |
| 🚀 [Deployment Guide](docs/deployment.md) | Production deployment strategies, scaling considerations, and infrastructure requirements |
| 🔌 [NLE Integrations Overview](docs/integrations/README.md) | Detailed guide for configuring Watson, Google, and VoiceBase providers |
| 🖥️ [UI Components Reference](docs/ui-components.md) | JavaScript component library for transcript visualization and interactive analytics |

### Additional Resources

- **Changelog**: Track version history and breaking changes
- **Migration Guide**: Instructions for upgrading between major versions
- **Security Policy**: Vulnerability reporting and security best practices

---

## Troubleshooting

### Common Issues

#### Connection Refused on Port 8080

```bash
# Check if the container is running
docker-compose ps

# Verify port binding
docker port nbtelemetry_nbtelemetry_1

# Check container logs for startup errors
docker-compose logs nbtelemetry | tail -50
```

#### Database Connection Failures

```bash
# Test database connectivity from the container
docker-compose exec nbtelemetry php -r "new PDO('mysql:host=database;dbname=nbtelemetry', 'nbtelemetry', 'password');"

# Verify database container is healthy
docker-compose exec database mysqladmin ping -h localhost
```

#### NLE Provider Authentication Errors

```bash
# Validate Watson credentials
curl -u "apikey:YOUR_API_KEY" \
  "https://api.us-south.speech-to-text.watson.cloud.ibm.com/v1/models"

# Test Google Cloud credentials
docker-compose exec nbtelemetry cat $GOOGLE_APPLICATION_CREDENTIALS | jq .project_id
```

#### Composer Dependency Issues

```bash
# Clear Composer cache and reinstall
composer clear-cache
rm -rf vendor/
composer install --no-dev --optimize-autoloader

# Verify autoload files are generated
composer dump-autoload --optimize
```

---

## Contributing

We welcome contributions to NBTelemetry! Please follow these guidelines:

1. Fork the repository and create a feature branch
2. Run the test suite: `composer test`
3. Ensure code style compliance: `composer cs-check`
4. Submit a pull request with a clear description

### Development Setup

```bash
# Install development dependencies
composer install

# Run tests
composer test

# Run code style fixer
composer cs-fix

# Run static analysis
composer analyse
```

---

## License

NBTelemetry is proprietary software. Please contact the team for licensing inquiries.

---

<p align="center">
  <strong>NBTelemetry</strong> — Transforming voice data into actionable insights
</p>