# Platform API Overview

[![API Version](https://img.shields.io/badge/API-v1.0-blue.svg)]()
[![PHP](https://img.shields.io/badge/PHP-7.4+-purple.svg)]()
[![Framework](https://img.shields.io/badge/Framework-Kohana-orange.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)]()
[![Endpoints](https://img.shields.io/badge/Endpoints-150-green.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

The **Platform API** is the core service powering our telecommunications/VoIP platform, serving as the central hub for both machine and human interfacing. It provides unified, RESTful access to all platform resources including user management, billing, dialplans, SIP/VoIP configurations, and telephony operations.

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Authentication Summary](#authentication-summary)
- [Documentation Index](#documentation-index)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

---

## Introduction

The Platform API acts as the backbone of the telecommunications platform, centralizing all data operations and business logic into a single, well-documented interface. Whether you're building integrations, developing administrative dashboards, or automating telephony workflows, this API provides the foundation you need.

### Who Is This For?

| Audience | Use Case |
|----------|----------|
| **Developers** | Building integrations, custom applications, or extending platform functionality |
| **Operators** | Deploying, configuring, and maintaining the service in production environments |
| **System Integrators** | Connecting third-party systems with the telecommunications platform |
| **DevOps Engineers** | Managing containerized deployments and CI/CD pipelines |

### Platform Capabilities

The API manages **100 data models** across **150 endpoints**, providing comprehensive coverage of:

- **User & Organization Management** — Multi-tenant user hierarchies, roles, and permissions
- **Billing & Subscriptions** — Plans, invoicing, payment processing, and usage tracking
- **Dialplan Configuration** — Call routing rules, IVR flows, and time-based routing
- **SIP/VoIP Resources** — Trunks, gateways, devices, and endpoint registration
- **CDR Processing** — Call detail records, analytics, and reporting
- **Domain & DNS Management** — SIP domains, DNS records, and service discovery
- **Rate & Tariff Management** — Call rating, tariff plans, and cost calculations

---

## Key Features

```
┌─────────────────────────────────────────────────────────────────┐
│                      PLATFORM API FEATURES                       │
├─────────────────────┬─────────────────────┬─────────────────────┤
│   User Management   │   Billing Engine    │   Telephony Core    │
│   • Organizations   │   • Subscriptions   │   • SIP Trunks      │
│   • Users & Roles   │   • Invoicing       │   • Gateways        │
│   • Permissions     │   • Rate Plans      │   • Devices         │
├─────────────────────┼─────────────────────┼─────────────────────┤
│   Call Routing      │   CDR & Analytics   │   Infrastructure    │
│   • Dialplans       │   • Call Logs       │   • Domains         │
│   • IVR Flows       │   • Reports         │   • DNS Records     │
│   • Time Rules      │   • Real-time       │   • OAuth Clients   │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

---

## Quick Start

Get up and running with the Platform API in minutes using Docker.

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **PHP** (v7.4+ for local development)
- **Composer** (v2.0+ for dependency management)
- **Git** for cloning the repository

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/platform-api.git
cd platform-api
```

### 2. Install Dependencies

```bash
# Install PHP dependencies using Composer
composer install

# For production environments, optimize autoloader
composer install --no-dev --optimize-autoloader
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit configuration (database, cache, API keys)
nano .env
```

**Essential Configuration Variables:**

```ini
# Application
APP_ENV=development
APP_DEBUG=true
APP_URL=http://localhost:8080

# Database
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=platform_api
DB_USERNAME=platform_user
DB_PASSWORD=secure_password

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# OAuth Settings
OAUTH_TOKEN_LIFETIME=3600
OAUTH_REFRESH_LIFETIME=86400
```

### 4. Start with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f platform-api

# Verify the service is running
curl http://localhost:8080/api/v1/health
```

### 5. Make Your First API Call

```bash
# Authenticate and get an access token
curl -X POST http://localhost:8080/api/v1/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }'

# Use the token to fetch organizations
curl http://localhost:8080/api/v1/organizations \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Architecture Overview

The Platform API follows a layered architecture built on the **Kohana PHP framework**, designed for scalability, maintainability, and high performance.

### System Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Load Balancer │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
           ┌────────▼────────┐      ┌────────▼────────┐      ┌────────▼────────┐
           │  Platform API   │      │  Platform API   │      │  Platform API   │
           │   Instance 1    │      │   Instance 2    │      │   Instance N    │
           └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
        ┌────────────────┬───────────────────┼───────────────┬────────────────┐
        │                │                   │               │                │
┌───────▼───────┐ ┌──────▼──────┐    ┌───────▼───────┐ ┌─────▼─────┐ ┌────────▼────────┐
│   MySQL/      │ │   Redis     │    │  Message      │ │   CDR     │ │   External      │
│   PostgreSQL  │ │   Cache     │    │  Queue        │ │   Storage │ │   Services      │
└───────────────┘ └─────────────┘    └───────────────┘ └───────────┘ └─────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | Kohana 3.x | MVC architecture, routing, request handling |
| **Database ORM** | Kohana ORM | Object-relational mapping for 100 models |
| **Caching Layer** | Redis | Session storage, API response caching |
| **Authentication** | OAuth 2.0 | Token-based API authentication |
| **Queue System** | RabbitMQ/Redis | Async job processing (CDR, billing) |
| **Containerization** | Docker | Consistent deployment environments |

### Request Flow

```
1. HTTP Request → Nginx/Apache
2. → Kohana Router (route matching)
3. → Authentication Middleware (OAuth validation)
4. → Controller (business logic)
5. → Model/ORM (database operations)
6. → Response formatting (JSON)
7. → HTTP Response
```

### Directory Structure

```
platform-api/
├── application/
│   ├── classes/
│   │   ├── Controller/          # API Controllers
│   │   ├── Model/               # ORM Models (100 models)
│   │   ├── Service/             # Business Logic Services
│   │   └── Helper/              # Utility Classes
│   ├── config/                  # Configuration files
│   ├── routes/                  # API route definitions
│   └── views/                   # Response templates
├── modules/
│   ├── oauth/                   # OAuth authentication module
│   ├── billing/                 # Billing engine module
│   └── telephony/               # VoIP/SIP integration module
├── system/                      # Kohana framework core
├── docker/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── php.ini
├── tests/                       # PHPUnit test suites
├── docs/                        # Documentation
├── composer.json
├── docker-compose.yml
└── .env.example
```

---

## Authentication Summary

The Platform API uses **OAuth 2.0** for authentication, supporting multiple grant types to accommodate different integration scenarios.

### Supported Grant Types

| Grant Type | Use Case | Token Lifetime |
|------------|----------|----------------|
| **Client Credentials** | Server-to-server integrations | 1 hour |
| **Authorization Code** | User-facing applications | 1 hour |
| **Refresh Token** | Token renewal | 24 hours |
| **Password** | Legacy/trusted applications | 1 hour |

### Authentication Flow

```php
<?php
// Example: Authenticating with Client Credentials in PHP

$client = new GuzzleHttp\Client(['base_uri' => 'https://api.platform.com']);

// Step 1: Obtain access token
$response = $client->post('/api/v1/oauth/token', [
    'json' => [
        'grant_type' => 'client_credentials',
        'client_id' => getenv('API_CLIENT_ID'),
        'client_secret' => getenv('API_CLIENT_SECRET'),
        'scope' => 'users:read organizations:write billing:read'
    ]
]);

$tokenData = json_decode($response->getBody(), true);
$accessToken = $tokenData['access_token'];

// Step 2: Make authenticated API requests
$response = $client->get('/api/v1/users', [
    'headers' => [
        'Authorization' => 'Bearer ' . $accessToken,
        'Accept' => 'application/json'
    ]
]);

$users = json_decode($response->getBody(), true);
```

### API Scopes

| Scope | Description |
|-------|-------------|
| `users:read` | Read user information |
| `users:write` | Create/update users |
| `organizations:read` | Read organization data |
| `organizations:write` | Manage organizations |
| `billing:read` | View billing information |
| `billing:write` | Manage subscriptions and payments |
| `telephony:read` | Read SIP/VoIP configurations |
| `telephony:write` | Manage telephony resources |
| `cdr:read` | Access call detail records |
| `admin` | Full administrative access |

---

## Documentation Index

Comprehensive documentation is organized into the following sections:

### 📚 Core Documentation

| Document | Description |
|----------|-------------|
| **[API Reference Overview](docs/api/README.md)** | Complete API endpoint documentation covering all 150 endpoints with request/response examples |
| **[Data Models Overview](docs/models/README.md)** | Detailed documentation of all 100 data models, relationships, and schemas |
| **[Configuration Reference](docs/configuration.md)** | Complete guide to all 50 configuration variables and environment setup |
| **[Deployment Guide](docs/deployment.md)** | Production deployment instructions, scaling strategies, and infrastructure requirements |

### 📖 Additional Resources

```
docs/
├── api/
│   ├── README.md                 # API Reference Overview
│   ├── authentication.md         # OAuth implementation details
│   ├── users.md                  # User management endpoints
│   ├── organizations.md          # Organization endpoints
│   ├── billing.md                # Billing and subscription APIs
│   ├── dialplans.md              # Dialplan configuration APIs
│   ├── telephony.md              # SIP/VoIP resource APIs
│   └── cdr.md                    # CDR and reporting APIs
├── models/
│   ├── README.md                 # Data Models Overview
│   ├── user-models.md            # User-related models
│   ├── billing-models.md         # Billing data models
│   └── telephony-models.md       # Telephony models
├── configuration.md              # Configuration Reference
├── deployment.md                 # Deployment Guide
├── CHANGELOG.md                  # Version history
└── CONTRIBUTING.md               # Contribution guidelines
```

---

## Development Setup

Set up a complete local development environment for contributing to or extending the Platform API.

### System Requirements

| Requirement | Minimum Version | Recommended |
|-------------|-----------------|-------------|
| PHP | 7.4 | 8.1+ |
| MySQL | 5.7 | 8.0+ |
| Redis | 5.0 | 6.0+ |
| Composer | 2.0 | Latest |
| Docker | 20.10 | Latest |
| Node.js (for tooling) | 14.x | 18.x |

### Local Development Setup

#### Option 1: Docker-Based Development (Recommended)

```bash
# Clone and enter directory
git clone https://github.com/your-org/platform-api.git
cd platform-api

# Copy environment configuration
cp .env.example .env

# Start development stack
docker-compose -f docker-compose.dev.yml up -d

# Install dependencies inside container
docker-compose exec app composer install

# Run database migrations
docker-compose exec app php kohana migrate

# Seed development data
docker-compose exec app php kohana seed

# The API is now available at http://localhost:8080
```

#### Option 2: Native PHP Setup

```bash
# Install PHP dependencies
composer install

# Configure your local environment
cp .env.example .env
# Edit .env with your local database credentials

# Create the database
mysql -u root -p -e "CREATE DATABASE platform_api CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
php kohana migrate

# Start PHP's built-in server (development only)
php -S localhost:8080 -t public/

# Or configure Apache/Nginx to serve the public/ directory
```

### Development Tools

```bash
# Install development dependencies
composer install --dev

# Code style checking (PSR-12)
composer run cs-check

# Automatically fix code style issues
composer run cs-fix

# Static analysis with PHPStan
composer run analyse

# Generate API documentation
composer run docs:generate
```

### IDE Configuration

**Recommended VS Code Extensions:**
- PHP Intelephense
- PHP Debug (Xdebug)
- EditorConfig
- Docker

**PhpStorm Setup:**
1. Configure PHP interpreter (Docker or local)
2. Enable Kohana framework support
3. Configure Xdebug for debugging
4. Import code style settings from `.editorconfig`

---

## Testing

The Platform API includes comprehensive test coverage using PHPUnit.

### Running Tests

```bash
# Run all tests
composer test

# Or using PHPUnit directly
./vendor/bin/phpunit

# Run specific test suite
./vendor/bin/phpunit --testsuite=Unit
./vendor/bin/phpunit --testsuite=Integration
./vendor/bin/phpunit --testsuite=API

# Run tests with coverage report
./vendor/bin/phpunit --coverage-html coverage/

# Run specific test file
./vendor/bin/phpunit tests/Unit/Models/UserTest.php

# Run tests matching a filter
./vendor/bin/phpunit --filter=testUserCreation
```

### Test Suites

| Suite | Description | Execution Time |
|-------|-------------|----------------|
| **Unit** | Model logic, helpers, services | ~30 seconds |
| **Integration** | Database operations, service interactions | ~2 minutes |
| **API** | Full endpoint testing | ~5 minutes |

### Writing Tests

```php
<?php
// tests/Unit/Models/UserTest.php

namespace Tests\Unit\Models;

use PHPUnit\Framework\TestCase;
use App\Model\User;

class UserTest extends TestCase
{
    public function testUserCreation(): void
    {
        $user = new User([
            'email' => 'test@example.com',
            'name' => 'Test User',
            'organization_id' => 1
        ]);
        
        $this->assertEquals('test@example.com', $user->email);
        $this->assertFalse($user->is_admin);
    }
    
    public function testUserValidation(): void
    {
        $this->expectException(\Validation_Exception::class);
        
        $user = new User(['email' => 'invalid-email']);
        $user->save();
    }
}
```

### Test Database

```bash
# Create test database
mysql -u root -p -e "CREATE DATABASE platform_api_test;"

# Run migrations on test database
APP_ENV=testing php kohana migrate

# Tests will automatically use the test database
```

---

## Deployment

Deploy the Platform API to production using Docker and orchestration tools.

### Docker Production Build

```bash
# Build production image
docker build -t platform-api:latest -f docker/Dockerfile.prod .

# Run with production settings
docker run -d \
  --name platform-api \
  -p 8080:80 \
  -e APP_ENV=production \
  -e DB_HOST=your-db-host \
  -e REDIS_HOST=your-redis-host \
  platform-api:latest
```

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: platform-api:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.prod.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/ingress.yml

# Check deployment status
kubectl get pods -n platform-api
kubectl logs -f deployment/platform-api -n platform-api
```

### Health Checks

```bash
# Application health
curl https://api.yourplatform.com/api/v1/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "queue": "ok"
  }
}
```

For complete deployment instructions, see the **[Deployment Guide](docs/deployment.md)**.

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check database connectivity
docker-compose exec app php -r "new PDO('mysql:host=db;dbname=platform_api', 'user', 'pass');"

# Verify environment variables
docker-compose exec app env | grep DB_
```

#### Composer Dependency Issues

```bash
# Clear Composer cache
composer clear-cache

# Reinstall dependencies
rm -rf vendor/ composer.lock
composer install
```

#### OAuth Token Issues

```bash
# Clear OAuth tokens cache
docker-compose exec app php kohana cache:clear oauth

# Regenerate OAuth keys
docker-compose exec app php kohana oauth:keys
```

#### Permission Issues

```bash
# Fix storage permissions
chmod -R 775 application/cache application/logs
chown -R www-data:www-data application/cache application/logs
```

### Debug Mode

```bash
# Enable debug mode (development only!)
APP_DEBUG=true APP_ENV=development php kohana serve

# View detailed error logs
tail -f application/logs/$(date +%Y)/$(date +%m)/$(date +%d).php
```

---

## Support

### Getting Help

- **Documentation**: Start with the [API Reference](docs/api/README.md) and [Configuration Guide](docs/configuration.md)
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join our developer community for questions and feature requests

### Contributing

We welcome contributions! Please read our [Contributing Guidelines](docs/CONTRIBUTING.md) before submitting pull requests.

```bash
# Fork and clone
git clone https://github.com/your-username/platform-api.git

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, add tests, commit
composer test
git commit -m "feat: add your feature"

# Push and create PR
git push origin feature/your-feature-name
```

---

## License

This project is proprietary software. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Platform API</strong> — Powering telecommunications at scale<br>
  <sub>Built with ❤️ using Kohana PHP Framework</sub>
</p>