# Sapien Documentation

[![PHP](https://img.shields.io/badge/PHP-8.2+-777BB4?style=flat-square&logo=php&logoColor=white)](https://php.net)
[![Symfony](https://img.shields.io/badge/Symfony-6.x-000000?style=flat-square&logo=symfony&logoColor=white)](https://symfony.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![API](https://img.shields.io/badge/API-RESTful-009688?style=flat-square)](docs/api/README.md)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)]()

> A PHP-based REST API service built on Symfony, providing comprehensive CRUD operations for entity management with real-time event capabilities

---

## 📋 Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [API Quick Reference](#api-quick-reference)
- [Documentation Index](#documentation-index)
- [Related Resources](#related-resources)
- [Contributing](#contributing)

---

## Introduction

**Sapien** is a robust REST API service designed to manage entities such as `Person`, `Pet`, and `Toy` through a clean, well-documented API interface. Built on the Symfony framework, Sapien leverages modern PHP practices and provides a complete Docker-based development environment for seamless local development and deployment.

### What Sapien Provides

Sapien serves as a centralized backend service for applications requiring:

- **Entity Management**: Full CRUD (Create, Read, Update, Delete) operations for core business entities
- **Real-time Updates**: ESL (Event System Layer) integration for broadcasting availability changes and entity updates
- **Secure Authentication**: OAuth2-based authentication with access and refresh token support
- **Scalable Architecture**: Rate limiting per organization and blob storage integration for handling media assets

### Who Should Use Sapien

This service is designed for **developers** building applications that require:

- A reliable backend API for entity data management
- Real-time event notifications for state changes
- Multi-tenant support with organization-level rate limiting
- Secure, token-based authentication flows

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🔄 **RESTful CRUD API** | Complete entity management for Person, Pet, and Toy models |
| 🐳 **Docker Environment** | Fully containerized development setup with hot-reload |
| 🐛 **Xdebug Integration** | Full debugging support with PhpStorm configuration |
| 📡 **ESL Event System** | Real-time event broadcasting for availability updates |
| 🔐 **OAuth2 Authentication** | Secure access with token refresh capabilities |
| ⚡ **Rate Limiting** | Per-organization throttling for API protection |
| 📦 **Blob Storage** | Integrated file and media asset management |
| 📊 **Profiler Support** | Symfony Profiler for performance analysis |

---

## Quick Start

Get Sapien running locally in under 5 minutes with Docker.

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (v20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+) - Usually included with Docker Desktop
- **Git** - For cloning the repository
- **Make** (optional) - For using Makefile shortcuts

### Step 1: Clone the Repository

```bash
git clone <repository-url> sapien
cd sapien
```

### Step 2: Configure Environment

Copy the example environment file and configure your local settings:

```bash
cp .env.example .env
```

Edit `.env` with your preferred editor and configure the required variables:

```dotenv
# Application
APP_ENV=dev
APP_SECRET=your-secret-key-here

# Database
DATABASE_URL="mysql://sapien:sapien@database:3306/sapien?serverVersion=8.0"

# OAuth2
OAUTH_PRIVATE_KEY_PATH=/var/www/config/jwt/private.pem
OAUTH_PUBLIC_KEY_PATH=/var/www/config/jwt/public.pem
OAUTH_PASSPHRASE=your-passphrase

# Rate Limiting
RATE_LIMIT_DEFAULT=1000
RATE_LIMIT_WINDOW=3600
```

### Step 3: Start the Docker Environment

```bash
# Build and start all services
docker-compose up -d --build

# Verify all containers are running
docker-compose ps
```

Expected output:
```
NAME                SERVICE             STATUS
sapien-app          app                 running
sapien-database     database            running
sapien-redis        redis               running
sapien-nginx        nginx               running
```

### Step 4: Initialize the Database

```bash
# Run database migrations
docker-compose exec app php bin/console doctrine:migrations:migrate --no-interaction

# (Optional) Load sample data
docker-compose exec app php bin/console doctrine:fixtures:load --no-interaction
```

### Step 5: Generate OAuth2 Keys

```bash
# Create the JWT directory
docker-compose exec app mkdir -p config/jwt

# Generate private key
docker-compose exec app openssl genrsa -out config/jwt/private.pem -aes256 4096

# Generate public key
docker-compose exec app openssl rsa -pubout -in config/jwt/private.pem -out config/jwt/public.pem
```

### Step 6: Verify Installation

Test the API health endpoint:

```bash
curl -X GET http://localhost:8080/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

🎉 **Congratulations!** Sapien is now running. Visit the [Getting Started Guide](docs/getting-started.md) for detailed configuration options.

---

## Architecture Overview

Sapien follows a clean, layered architecture pattern built on Symfony best practices.

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Applications                          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Nginx Proxy                                │
│                    (SSL Termination, Load Balancing)                 │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Sapien API Service                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   OAuth2    │  │    Rate     │  │  Controller │  │    ESL      │ │
│  │   Guard     │  │   Limiter   │  │    Layer    │  │   Events    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │                │        │
│         └────────────────┴────────┬───────┴────────────────┘        │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │  Service Layer  │                        │
│                          └────────┬────────┘                        │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │ Repository Layer│                        │
│                          └────────┬────────┘                        │
└───────────────────────────────────┼─────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
    │    MySQL     │        │    Redis     │        │ Blob Storage │
    │   Database   │        │    Cache     │        │   Service    │
    └──────────────┘        └──────────────┘        └──────────────┘
```

### Component Overview

#### Controllers (24 Endpoints)

The API exposes 24 RESTful endpoints organized by entity type:

| Entity | Endpoints | Description |
|--------|-----------|-------------|
| Person | 8 | User profile management, relationships |
| Pet | 8 | Pet entity CRUD, availability status |
| Toy | 6 | Toy inventory management |
| Auth | 2 | OAuth2 token operations |

#### Models (44 Entities)

Sapien manages 44 data models, including:

- **Core Entities**: Person, Pet, Toy
- **Supporting Entities**: Address, Contact, Organization
- **System Entities**: Token, AuditLog, Event

#### Configuration (12 Variables)

Environment-based configuration supporting:

- Database connections
- Authentication settings
- Rate limiting parameters
- Storage configurations

### Request Flow

```
1. Request → Nginx (SSL/Routing)
2. OAuth2 Guard (Authentication)
3. Rate Limiter (Throttling Check)
4. Controller (Request Handling)
5. Service Layer (Business Logic)
6. Repository (Data Access)
7. ESL Events (Real-time Broadcast)
8. Response → Client
```

---

## API Quick Reference

### Authentication

All API requests require a valid Bearer token:

```bash
# Obtain access token
curl -X POST http://localhost:8080/api/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200..."
}
```

### Common Endpoints

```bash
# List all persons
curl -X GET http://localhost:8080/api/v1/persons \
  -H "Authorization: Bearer {access_token}"

# Create a new pet
curl -X POST http://localhost:8080/api/v1/pets \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Buddy",
    "species": "dog",
    "owner_id": "uuid-here"
  }'

# Get toy by ID
curl -X GET http://localhost:8080/api/v1/toys/{id} \
  -H "Authorization: Bearer {access_token}"
```

For complete API documentation, see the [API Reference](docs/api/README.md).

---

## Documentation Index

Navigate to detailed documentation for each aspect of the Sapien service:

### 📚 Core Documentation

| Document | Description |
|----------|-------------|
| [📖 Getting Started](docs/getting-started.md) | Comprehensive setup guide, IDE configuration, and first steps |
| [🔌 API Reference Overview](docs/api/README.md) | Complete API documentation with all 24 endpoints |
| [📊 Data Models Overview](docs/models/README.md) | Detailed schema documentation for all 44 models |
| [⚙️ Configuration Reference](docs/configuration.md) | All 12 configuration variables explained |
| [📡 ESL Events System](docs/events/README.md) | Real-time event system architecture and usage |

### 🔧 Development Resources

```
docs/
├── getting-started.md      # Initial setup and onboarding
├── configuration.md        # Environment and config reference
├── api/
│   └── README.md          # API endpoints and examples
├── models/
│   └── README.md          # Entity schemas and relationships
└── events/
    └── README.md          # ESL event system documentation
```

---

## Related Resources

### Development Tools

- **Symfony Documentation**: [symfony.com/doc](https://symfony.com/doc/current/index.html)
- **Docker Documentation**: [docs.docker.com](https://docs.docker.com/)
- **PhpStorm Xdebug Guide**: [JetBrains Xdebug](https://www.jetbrains.com/help/phpstorm/configuring-xdebug.html)

### Useful Commands

```bash
# View application logs
docker-compose logs -f app

# Access PHP container shell
docker-compose exec app bash

# Clear Symfony cache
docker-compose exec app php bin/console cache:clear

# Run tests
docker-compose exec app php bin/phpunit

# Open Symfony Profiler
# Visit: http://localhost:8080/_profiler

# Database operations
docker-compose exec app php bin/console doctrine:schema:validate
docker-compose exec app php bin/console doctrine:query:sql "SELECT * FROM person LIMIT 5"
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Container won't start | Run `docker-compose down -v` then `docker-compose up -d --build` |
| Database connection failed | Verify `DATABASE_URL` in `.env` and ensure database container is healthy |
| OAuth token invalid | Regenerate JWT keys and restart the application |
| Rate limit exceeded | Wait for the configured window to reset, or adjust `RATE_LIMIT_DEFAULT` |

---

## Contributing

We welcome contributions to Sapien! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes with clear messages
4. **Push** to your branch
5. **Open** a Pull Request

### Code Standards

- Follow PSR-12 coding standards
- Write PHPUnit tests for new features
- Update documentation for API changes
- Use meaningful commit messages

---

## Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check the [Documentation Index](#documentation-index)
- **Community**: Join discussions in the repository

---

<div align="center">

**Built with ❤️ using Symfony and PHP**

[Getting Started](docs/getting-started.md) · [API Reference](docs/api/README.md) · [Configuration](docs/configuration.md)

</div>