# Disposition Gateway API Overview

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/)
[![PHP Version](https://img.shields.io/badge/PHP-7.4%2B-blue.svg)](https://php.net/)
[![Kohana Framework](https://img.shields.io/badge/Framework-Kohana-orange.svg)](https://kohanaframework.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

## Introduction

**platform-dgapi** (Disposition Gateway API) is a robust, CodeIgniter-based REST API service built on the Kohana framework that orchestrates task disposition workflows across multiple communication channels. This service acts as a central gateway for managing dispositions, handling SMS notifications, email delivery, voicemail processing, CDR (Call Detail Record) integration, and callback event management.

The Disposition Gateway API serves as the backbone for workflow automation, enabling seamless communication between various platform components while maintaining a consistent, token-authenticated interface for all operations.

### What is a Disposition?

In the context of this service, a **disposition** represents the outcome or status of a task, call, or interaction. The DGAPI processes these dispositions and triggers appropriate follow-up actions such as sending notifications, updating records, or initiating callbacks.

### Key Use Cases

- **Contact Center Operations**: Process call dispositions and trigger automated follow-ups
- **Multi-channel Notifications**: Send SMS, email, and voicemail notifications based on disposition rules
- **CDR Processing**: Transform and forward Call Detail Records to SGAPI for reporting
- **Callback Management**: Handle callback finish events and schedule follow-up tasks
- **Workflow Automation**: Execute generic task processing based on configurable rules

---

## Features

| Feature | Description |
|---------|-------------|
| 📋 **Task Disposition Management** | Comprehensive handling of task dispositions with configurable workflows |
| 📱 **SMS Sending Capabilities** | Integrated SMS delivery with status tracking and retry mechanisms |
| 📧 **Email Notification Handling** | Template-based email notifications with attachment support |
| 🎤 **Voicemail Processing** | Voicemail notification delivery and transcription support |
| 📊 **CDR to SGAPI Integration** | Seamless Call Detail Record transformation and forwarding |
| 🔄 **Callback Finish Events** | Event-driven callback completion handling |
| ⚙️ **Generic Task Processing** | Flexible task processing engine for custom workflows |
| 🔐 **Token-based Authentication** | Secure API access with token validation |
| 🔄 **DOM-based Request/Response** | XML/DOM processing for legacy system compatibility |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL CLIENTS                                │
│                    (Contact Centers, CRM Systems, etc.)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUTHENTICATION LAYER                                │
│                         (Token-based Auth Guard)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           platform-dgapi                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   SMS       │  │   Email     │  │  Voicemail  │  │    CDR      │        │
│  │  Handler    │  │  Handler    │  │  Handler    │  │  Processor  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐         │
│  │  Callback   │  │   Task      │  │     DOM Request/Response     │         │
│  │  Handler    │  │  Processor  │  │         Processor            │         │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
           │   Database   │  │    SGAPI     │  │  Notification │
           │   (MySQL)    │  │   Service    │  │   Services    │
           └──────────────┘  └──────────────┘  └──────────────┘
```

### Service Components

- **API Controllers**: Handle incoming HTTP requests and route to appropriate handlers
- **Disposition Handlers**: Process specific disposition types (SMS, Email, Voicemail)
- **CDR Processor**: Transforms and forwards call detail records
- **Task Queue**: Manages asynchronous task processing
- **Authentication Module**: Validates tokens and enforces access control
- **DOM Processor**: Handles XML-based request/response for legacy integrations

---

## Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **PHP 7.4+** with required extensions (curl, json, xml, mysql)
- **Composer** (PHP dependency manager)
- **Docker & Docker Compose** (for containerized deployment)
- **MySQL 5.7+** or compatible database
- **Git** for version control

### Installation

1. **Clone the Repository**

```bash
git clone https://github.com/your-org/platform-dgapi.git
cd platform-dgapi
```

2. **Install Dependencies via Composer**

```bash
composer install
```

3. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set Up Database**

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE dgapi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
php artisan migrate
```

5. **Generate Application Key**

```bash
php artisan key:generate
```

6. **Start the Development Server**

```bash
php -S localhost:8080 -t public/
```

### Verify Installation

```bash
curl -X GET http://localhost:8080/api/health \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

Expected response:

```json
{
  "status": "healthy",
  "service": "platform-dgapi",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Docker Setup

### Using Docker Compose (Recommended)

The service is fully containerized for consistent deployment across environments.

1. **Build and Start Containers**

```bash
docker-compose up -d --build
```

2. **View Container Logs**

```bash
docker-compose logs -f dgapi
```

3. **Execute Commands Inside Container**

```bash
docker-compose exec dgapi php artisan migrate
docker-compose exec dgapi composer install
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  dgapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: platform-dgapi
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      - APP_ENV=production
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_DATABASE=dgapi_db
      - DB_USERNAME=dgapi_user
      - DB_PASSWORD=${DB_PASSWORD}
      - SGAPI_ENDPOINT=${SGAPI_ENDPOINT}
      - SMS_PROVIDER_KEY=${SMS_PROVIDER_KEY}
    volumes:
      - ./storage/logs:/var/www/html/storage/logs
    depends_on:
      - mysql
    networks:
      - dgapi-network

  mysql:
    image: mysql:5.7
    container_name: dgapi-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: dgapi_db
      MYSQL_USER: dgapi_user
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql-data:/var/lib/mysql
    networks:
      - dgapi-network

volumes:
  mysql-data:

networks:
  dgapi-network:
    driver: bridge
```

### Dockerfile

```dockerfile
FROM php:7.4-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    zip \
    unzip

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd xml

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY . .

# Install dependencies
RUN composer install --no-dev --optimize-autoloader

# Set permissions
RUN chown -R www-data:www-data /var/www/html/storage

# Apache configuration
RUN a2enmod rewrite

EXPOSE 80

CMD ["apache2-foreground"]
```

---

## Configuration

### Environment Variables

The service is configured through environment variables. Below are the key configuration categories:

| Category | Variables | Description |
|----------|-----------|-------------|
| **Application** | `APP_ENV`, `APP_DEBUG`, `APP_KEY` | Core application settings |
| **Database** | `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` | Database connection |
| **Authentication** | `AUTH_TOKEN_LIFETIME`, `AUTH_SECRET_KEY` | Token authentication settings |
| **SMS Provider** | `SMS_PROVIDER_URL`, `SMS_PROVIDER_KEY`, `SMS_RETRY_COUNT` | SMS delivery configuration |
| **Email** | `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` | Email server settings |
| **SGAPI Integration** | `SGAPI_ENDPOINT`, `SGAPI_API_KEY`, `SGAPI_TIMEOUT` | SGAPI connection settings |

### Sample Environment File

```bash
# Application
APP_ENV=production
APP_DEBUG=false
APP_KEY=base64:your-generated-key-here
APP_URL=https://dgapi.example.com

# Database
DB_CONNECTION=mysql
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=dgapi_db
DB_USERNAME=dgapi_user
DB_PASSWORD=secure_password_here

# Authentication
AUTH_TOKEN_LIFETIME=3600
AUTH_SECRET_KEY=your-secret-key

# SMS Configuration
SMS_PROVIDER_URL=https://sms-provider.com/api
SMS_PROVIDER_KEY=your-sms-api-key
SMS_RETRY_COUNT=3
SMS_RETRY_DELAY=5

# Email Configuration
MAIL_HOST=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=notifications@example.com
MAIL_PASSWORD=email_password
MAIL_ENCRYPTION=tls

# SGAPI Integration
SGAPI_ENDPOINT=https://sgapi.example.com
SGAPI_API_KEY=your-sgapi-key
SGAPI_TIMEOUT=30

# Logging
LOG_LEVEL=info
LOG_CHANNEL=daily
```

For detailed configuration options, see the [Configuration Guide](docs/configuration.md).

---

## Documentation Index

Comprehensive documentation is available in the `docs/` directory:

### Core Documentation

| Document | Description |
|----------|-------------|
| 📘 [API Reference Overview](docs/api/README.md) | Complete API endpoint documentation with request/response examples |
| 📗 [Data Models Overview](docs/models/README.md) | Database schema and model relationship documentation |
| ⚙️ [Configuration Guide](docs/configuration.md) | Detailed configuration options and environment variables |
| 🔐 [Authentication & Authorization](docs/authentication.md) | Token-based auth implementation and security guidelines |

### Quick Reference

- **Total Endpoints**: 18 documented API endpoints
- **Data Models**: 12 database models
- **Configuration Variables**: 39 configurable options

---

## Development Setup

### Setting Up Local Development Environment

1. **Fork and Clone**

```bash
git clone https://github.com/your-username/platform-dgapi.git
cd platform-dgapi
```

2. **Install Development Dependencies**

```bash
composer install
```

3. **Set Up Test Database**

```bash
mysql -u root -p -e "CREATE DATABASE dgapi_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

4. **Configure Test Environment**

```bash
cp .env .env.testing
# Update .env.testing with test database credentials
```

5. **Run Tests**

```bash
# Run all tests
./vendor/bin/phpunit

# Run specific test suite
./vendor/bin/phpunit --testsuite=Unit

# Run with coverage
./vendor/bin/phpunit --coverage-html coverage/
```

### Code Quality Tools

```bash
# PHP CodeSniffer - Check coding standards
./vendor/bin/phpcs --standard=PSR12 app/

# PHP CodeSniffer - Auto-fix issues
./vendor/bin/phpcbf --standard=PSR12 app/

# PHPStan - Static analysis
./vendor/bin/phpstan analyse app/ --level=5
```

### Project Structure

```
platform-dgapi/
├── app/
│   ├── Controllers/         # API Controllers
│   ├── Models/              # Eloquent Models
│   ├── Services/            # Business Logic Services
│   ├── Handlers/            # Disposition Handlers
│   └── Middleware/          # Request Middleware
├── config/                  # Configuration Files
├── database/
│   ├── migrations/          # Database Migrations
│   └── seeds/               # Database Seeders
├── docs/                    # Documentation
├── public/                  # Public Entry Point
├── storage/
│   └── logs/               # Application Logs
├── tests/                   # Test Suites
├── .env.example            # Environment Template
├── composer.json           # PHP Dependencies
├── docker-compose.yml      # Docker Configuration
├── Dockerfile              # Container Definition
└── README.md               # This File
```

### Contributing

1. Create a feature branch from `develop`
2. Write tests for new functionality
3. Ensure all tests pass and code meets PSR-12 standards
4. Submit a pull request with a clear description

---

## Support

For issues, questions, or feature requests:

- **Internal**: Contact the Platform Engineering team
- **Issues**: Submit via GitHub Issues
- **Documentation**: Check the [docs/](docs/) directory

---

## License

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

*Last updated: January 2024 | Version 1.0.0*