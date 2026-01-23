# Service Gateway Overview

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PHP](https://img.shields.io/badge/PHP-7.4+-777BB4?logo=php&logoColor=white)](https://www.php.net/)
[![Kohana](https://img.shields.io/badge/Framework-Kohana-4F5B93)](https://kohanaframework.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![API Endpoints](https://img.shields.io/badge/Endpoints-59-green)](docs/api/README.md)
[![Data Models](https://img.shields.io/badge/Models-100-blue)](docs/models/README.md)

A unified API gateway that provides seamless integration with multiple CRM and enterprise platforms including Salesforce, Microsoft Dynamics, Zendesk, SugarCRM, Oracle Fusion, and custom data sources. Built on the Kohana PHP framework with full Docker support for containerized deployments.

---

## Table of Contents

- [Introduction](#introduction)
- [Supported Platforms](#supported-platforms)
- [Quick Start](#quick-start)
- [Build and Run with Docker](#build-and-run-with-docker)
- [Architecture Overview](#architecture-overview)
- [Documentation Index](#documentation-index)
- [Development Mode](#development-mode)
- [Production Deployment](#production-deployment)
- [Contributing](#contributing)

---

## Introduction

**Service Gateway** solves the complex challenge of integrating with multiple CRM and enterprise platforms through a single, unified API interface. Instead of writing separate integration code for Salesforce, Microsoft Dynamics, Zendesk, and other platforms, developers can leverage Service Gateway's standardized RESTful API to query, create, update, and manage data across all supported platforms.

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Platform CRM Integration** | Connect to Salesforce, MS Dynamics, Zendesk, SugarCRM, Oracle Fusion, and more |
| **Unified Query Interface** | Single API syntax works across all connected data sources |
| **Flexible Authentication** | OAuth 2.0, token-based auth, LDAP, and GoodData authentication support |
| **Feed/Webhook Management** | Built-in system for managing real-time data feeds and webhooks |
| **Custom Data Connectors** | Extensible architecture for adding proprietary data sources |
| **Standardized Error Handling** | Consistent error responses regardless of underlying platform |

### Who Is This For?

- **Developers** building applications that need to integrate with multiple CRM systems
- **DevOps Engineers** deploying and managing enterprise integration infrastructure
- **Solution Architects** designing multi-platform data synchronization workflows
- **API Consumers** who need a simplified interface to complex enterprise systems

---

## Supported Platforms

Service Gateway provides native integration with the following platforms:

| Platform | Auth Methods | Features |
|----------|--------------|----------|
| **Salesforce** | OAuth 2.0, JWT Bearer | Full CRUD, SOQL queries, Bulk API |
| **Microsoft Dynamics 365** | OAuth 2.0, Client Credentials | OData queries, Entity operations |
| **Zendesk** | OAuth 2.0, API Token | Tickets, Users, Organizations |
| **SugarCRM** | OAuth 2.0, Password Grant | Modules, Relationships, Search |
| **Oracle Fusion** | OAuth 2.0, Basic Auth | REST resources, Business objects |
| **GoodData** | Token Auth | Analytics, Dashboards, Reports |
| **LDAP** | Simple Bind, SASL | Directory queries, User auth |
| **Custom Sources** | Configurable | Extensible connector framework |

---

## Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **PHP** 7.4 or higher
- **Composer** 2.x
- **Docker** and **Docker Compose** (for containerized deployment)
- **MySQL** 5.7+ or **PostgreSQL** 12+ (for persistence layer)

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/your-org/platform-service-gateway.git
cd platform-service-gateway
```

2. **Install PHP dependencies using Composer:**

```bash
composer install
```

3. **Copy and configure environment settings:**

```bash
cp .env.example .env
# Edit .env with your platform credentials and database settings
```

4. **Configure your first platform connection:**

```php
// application/config/platforms.php
return [
    'salesforce' => [
        'enabled' => true,
        'client_id' => getenv('SALESFORCE_CLIENT_ID'),
        'client_secret' => getenv('SALESFORCE_CLIENT_SECRET'),
        'instance_url' => getenv('SALESFORCE_INSTANCE_URL'),
        'api_version' => 'v56.0',
    ],
    // Add additional platforms as needed
];
```

5. **Run database migrations:**

```bash
php index.php migrate --up
```

6. **Start the development server:**

```bash
php -S localhost:8080 -t public/
```

7. **Verify the installation:**

```bash
curl http://localhost:8080/api/v1/health
```

Expected response:

```json
{
    "status": "healthy",
    "version": "2.4.1",
    "platforms": {
        "salesforce": "connected",
        "dynamics": "not_configured"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Build and Run with Docker

Docker is the recommended deployment method for Service Gateway, providing consistent environments across development, staging, and production.

### Building the Docker Image

```bash
# Build the production image
docker build -t platform-service-gateway:latest .

# Build with specific PHP version
docker build --build-arg PHP_VERSION=8.1 -t platform-service-gateway:php81 .
```

### Docker Compose Setup

Create or modify `docker-compose.yml`:

```yaml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: Dockerfile
    image: platform-service-gateway:latest
    container_name: service-gateway
    ports:
      - "8080:80"
    environment:
      - APP_ENV=production
      - DB_HOST=database
      - DB_NAME=gateway
      - DB_USER=gateway_user
      - DB_PASSWORD=${DB_PASSWORD}
      - SALESFORCE_CLIENT_ID=${SALESFORCE_CLIENT_ID}
      - SALESFORCE_CLIENT_SECRET=${SALESFORCE_CLIENT_SECRET}
      - REDIS_HOST=redis
    volumes:
      - ./logs:/var/www/html/application/logs
      - ./cache:/var/www/html/application/cache
    depends_on:
      - database
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  database:
    image: mysql:8.0
    container_name: gateway-db
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=gateway
      - MYSQL_USER=gateway_user
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
      - ./database/init:/docker-entrypoint-initdb.d
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: gateway-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  db_data:
  redis_data:
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f gateway

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build gateway
```

### Running Database Migrations in Docker

```bash
docker-compose exec gateway php index.php migrate --up
```

---

## Architecture Overview

Service Gateway follows a modular, layered architecture built on the Kohana PHP framework:

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   REST API  │  │  Webhooks   │  │  Feed Management        │  │
│  │  (59 endpoints)│ │  Handlers  │  │  System                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Authentication Layer                          │
│  ┌────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐ ┌─────────────┐  │
│  │ OAuth  │ │  Token   │ │ LDAP │ │ GoodData │ │   Custom    │  │
│  │  2.0   │ │  Auth    │ │      │ │   Auth   │ │   Providers │  │
│  └────────┘ └──────────┘ └──────┘ └──────────┘ └─────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Unified Query Engine (100 Models)              ││
│  │    Query Translation │ Response Normalization │ Caching    ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                    Platform Connector Layer                      │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ │
│  │Salesforce│ │ Dynamics │ │ Zendesk │ │ SugarCRM │ │ Oracle │ │
│  │Connector │ │ Connector│ │Connector│ │ Connector│ │Connector│ │
│  └──────────┘ └──────────┘ └─────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Controllers** | `application/classes/Controller/` | API endpoint handlers |
| **Models** | `application/classes/Model/` | Data model definitions (100 models) |
| **Connectors** | `application/classes/Connector/` | Platform-specific integration logic |
| **Auth Providers** | `application/classes/Auth/` | Authentication implementations |
| **Services** | `application/classes/Service/` | Business logic and orchestration |
| **Config** | `application/config/` | Configuration files (50 variables) |

### Request Flow

1. **Incoming Request** → API Gateway validates request format and authentication
2. **Authentication** → Appropriate auth provider validates credentials
3. **Routing** → Kohana router maps request to controller action
4. **Query Translation** → Unified query is translated to platform-specific format
5. **Platform Request** → Connector executes request against target platform
6. **Response Normalization** → Platform response is normalized to standard format
7. **Response** → Standardized JSON response returned to client

---

## Documentation Index

Comprehensive documentation is available for all aspects of Service Gateway:

### Core Documentation

| Document | Description |
|----------|-------------|
| [**API Reference Overview**](docs/api/README.md) | Complete API documentation covering all 59 endpoints, request/response formats, and examples |
| [**Authentication Guide**](docs/authentication/README.md) | Detailed guide to configuring OAuth, token auth, LDAP, and custom authentication providers |
| [**Data Models Overview**](docs/models/README.md) | Reference for all 100 data models, relationships, and field mappings |
| [**Configuration Reference**](docs/configuration.md) | Complete list of all 50 configuration variables with descriptions and defaults |
| [**Deployment Guide**](docs/deployment.md) | Production deployment instructions, scaling considerations, and infrastructure requirements |

### Quick Reference

- **Endpoints:** 59 RESTful API endpoints across all platform integrations
- **Models:** 100 data models covering CRM entities and custom objects
- **Config Variables:** 50 configurable options for customizing gateway behavior

---

## Development Mode

### Setting Up Local Development

1. **Install development dependencies:**

```bash
composer install --dev
```

2. **Enable development mode:**

```php
// application/bootstrap.php
Kohana::$environment = Kohana::DEVELOPMENT;
```

3. **Configure debug logging:**

```php
// application/config/logging.php
return [
    'level' => 'debug',
    'handlers' => [
        'file' => [
            'path' => APPPATH . 'logs/',
            'level' => 'debug',
        ],
        'stdout' => [
            'enabled' => true,
            'level' => 'info',
        ],
    ],
];
```

### Running Tests

```bash
# Run all tests
composer test

# Run specific test suite
composer test -- --testsuite=unit

# Run with coverage report
composer test:coverage

# Run integration tests (requires platform credentials)
composer test:integration
```

### Code Quality Tools

```bash
# Run PHP CodeSniffer
composer lint

# Run PHPStan static analysis
composer analyze

# Auto-fix coding standards
composer lint:fix
```

### Debugging Platform Connections

Enable connector debugging to troubleshoot platform integration issues:

```php
// application/config/platforms.php
return [
    'salesforce' => [
        'debug' => true,
        'log_requests' => true,
        'log_responses' => true,
        // ... other config
    ],
];
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Set `APP_ENV=production` in environment variables
- [ ] Configure all required platform credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configure database connection pooling
- [ ] Enable Redis caching for improved performance
- [ ] Set appropriate PHP memory limits and timeouts
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting

### Environment Variables

```bash
# Application
APP_ENV=production
APP_DEBUG=false
APP_KEY=your-secure-app-key

# Database
DB_HOST=your-db-host
DB_PORT=3306
DB_NAME=gateway_production
DB_USER=gateway_user
DB_PASSWORD=secure-password

# Redis Cache
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=redis-password

# Platform Credentials
SALESFORCE_CLIENT_ID=your-client-id
SALESFORCE_CLIENT_SECRET=your-client-secret
DYNAMICS_TENANT_ID=your-tenant-id
# ... additional platform credentials
```

### Performance Optimization

```php
// application/config/cache.php
return [
    'driver' => 'redis',
    'ttl' => 3600,
    'prefix' => 'gateway_',
    'query_cache' => [
        'enabled' => true,
        'ttl' => 300,
    ],
];
```

### Health Monitoring

Service Gateway provides health check endpoints for monitoring:

```bash
# Basic health check
GET /api/v1/health

# Detailed platform status
GET /api/v1/health/platforms

# Readiness probe (for Kubernetes)
GET /api/v1/ready
```

For complete production deployment instructions, including Kubernetes configurations and scaling strategies, see the [Deployment Guide](docs/deployment.md).

---

## Contributing

We welcome contributions to Service Gateway! Please follow these guidelines:

1. Fork the repository and create a feature branch
2. Ensure all tests pass: `composer test`
3. Follow PSR-12 coding standards: `composer lint`
4. Submit a pull request with a clear description

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Support

- **Documentation:** See the [Documentation Index](#documentation-index) above
- **Issues:** Report bugs and feature requests via GitHub Issues
- **Security:** Report security vulnerabilities to security@your-org.com

---

**Service Gateway** - Simplifying Enterprise Integration