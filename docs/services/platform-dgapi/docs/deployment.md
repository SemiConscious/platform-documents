# Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the **platform-dgapi** (Disposition Gateway API) service in production environments. The platform-dgapi is a CodeIgniter-based REST API service that handles critical task disposition workflows including SMS, email, and voicemail notifications, CDR processing, and callback finish events.

This guide covers Docker-based deployment, environment configuration, database setup, health monitoring, logging strategies, and troubleshooting common deployment issues. Following these guidelines ensures a reliable, scalable, and maintainable deployment of the Disposition Gateway API.

---

## Prerequisites

### System Requirements

Before deploying platform-dgapi, ensure your environment meets the following requirements:

| Component | Minimum Requirement | Recommended |
|-----------|---------------------|-------------|
| CPU | 2 cores | 4+ cores |
| Memory | 2 GB RAM | 4+ GB RAM |
| Disk Space | 10 GB | 50+ GB (for logs) |
| Operating System | Linux (Ubuntu 20.04+, CentOS 8+) | Ubuntu 22.04 LTS |
| Docker | 20.10+ | Latest stable |
| Docker Compose | 2.0+ | Latest stable |

### Required Software

Ensure the following software is installed on your deployment server:

```bash
# Verify Docker installation
docker --version
# Expected output: Docker version 20.10.x or higher

# Verify Docker Compose installation
docker compose version
# Expected output: Docker Compose version v2.x.x

# Verify Composer is available (for local builds)
composer --version
# Expected output: Composer version 2.x.x
```

### Network Requirements

The platform-dgapi service requires network access to:

- **Database Server**: MySQL/MariaDB on port 3306
- **SGAPI Service**: External API for CDR integration
- **SMS Gateway**: For sending SMS notifications
- **Email Server**: SMTP server for email notifications
- **Voicemail Service**: For voicemail notification processing

Ensure firewall rules allow:

```bash
# Inbound rules
- Port 80/443 (HTTP/HTTPS) for API access
- Port 8080 (optional) for health check endpoint

# Outbound rules
- Port 3306 (MySQL)
- Port 25/587/465 (SMTP)
- Port 443 (HTTPS for external APIs)
```

### Required Credentials and Access

Before deployment, gather the following:

- [ ] Database credentials (host, username, password, database name)
- [ ] API authentication tokens for external services
- [ ] SMTP server credentials
- [ ] SMS gateway API keys
- [ ] SSL certificates (for production)
- [ ] Container registry access (if using private registry)

---

## Docker Deployment

### Dockerfile Configuration

Create a production-ready Dockerfile for the platform-dgapi service:

```dockerfile
# Dockerfile for platform-dgapi
FROM php:8.1-apache

# Set environment variables
ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
ENV COMPOSER_ALLOW_SUPERUSER=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libzip-dev \
    zip \
    unzip \
    && docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Configure Apache
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf
RUN a2enmod rewrite headers

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY . /var/www/html

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Set permissions
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html/writable

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose port
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]
```

### Docker Compose Configuration

Create a comprehensive `docker-compose.yml` for orchestrating the service and its dependencies:

```yaml
version: '3.8'

services:
  platform-dgapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: platform-dgapi
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      - CI_ENVIRONMENT=production
      - DATABASE_HOST=${DATABASE_HOST}
      - DATABASE_NAME=${DATABASE_NAME}
      - DATABASE_USER=${DATABASE_USER}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - DATABASE_PORT=${DATABASE_PORT:-3306}
      - SMS_GATEWAY_URL=${SMS_GATEWAY_URL}
      - SMS_API_KEY=${SMS_API_KEY}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT:-587}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SGAPI_BASE_URL=${SGAPI_BASE_URL}
      - SGAPI_TOKEN=${SGAPI_TOKEN}
      - AUTH_TOKEN_SECRET=${AUTH_TOKEN_SECRET}
      - LOG_LEVEL=${LOG_LEVEL:-info}
    volumes:
      - ./logs:/var/www/html/writable/logs
      - ./uploads:/var/www/html/writable/uploads
    networks:
      - dgapi-network
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: mysql:8.0
    container_name: platform-dgapi-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${DATABASE_NAME}
      - MYSQL_USER=${DATABASE_USER}
      - MYSQL_PASSWORD=${DATABASE_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql
      - ./database/init:/docker-entrypoint-initdb.d
    networks:
      - dgapi-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: platform-dgapi-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - dgapi-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  dgapi-network:
    driver: bridge

volumes:
  db-data:
  redis-data:
```

### Building and Running

Execute the following commands to build and deploy:

```bash
# Clone the repository
git clone https://github.com/your-org/platform-dgapi.git
cd platform-dgapi

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env

# Build the Docker images
docker compose build --no-cache

# Start services in detached mode
docker compose up -d

# Verify services are running
docker compose ps

# Check logs
docker compose logs -f platform-dgapi
```

### Production Deployment with Docker Swarm

For high-availability deployments, use Docker Swarm:

```yaml
# docker-stack.yml
version: '3.8'

services:
  platform-dgapi:
    image: your-registry/platform-dgapi:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    ports:
      - "8080:80"
    secrets:
      - db_password
      - api_token
    configs:
      - source: app_config
        target: /var/www/html/.env

secrets:
  db_password:
    external: true
  api_token:
    external: true

configs:
  app_config:
    external: true
```

Deploy to swarm:

```bash
# Initialize swarm (if not already done)
docker swarm init

# Create secrets
echo "your-db-password" | docker secret create db_password -
echo "your-api-token" | docker secret create api_token -

# Deploy stack
docker stack deploy -c docker-stack.yml dgapi

# Check stack status
docker stack services dgapi
```

---

## Environment Configuration

### Configuration Variables Reference

The platform-dgapi service uses 39 configuration variables. Below are the critical ones organized by category:

#### Application Settings

```bash
# Application Environment
CI_ENVIRONMENT=production          # Options: development, testing, production
APP_BASE_URL=https://api.example.com
APP_TIMEZONE=UTC
APP_DEBUG=false                    # MUST be false in production

# Authentication
AUTH_TOKEN_SECRET=your-256-bit-secret-key
AUTH_TOKEN_EXPIRY=3600             # Token expiry in seconds
AUTH_ALLOWED_IPS=10.0.0.0/8,172.16.0.0/12  # Comma-separated CIDR blocks
```

#### Database Configuration

```bash
# Primary Database
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=dgapi_production
DATABASE_USER=dgapi_user
DATABASE_PASSWORD=secure-password-here
DATABASE_CHARSET=utf8mb4
DATABASE_COLLATION=utf8mb4_unicode_ci

# Connection Pool Settings
DATABASE_POOL_MIN=5
DATABASE_POOL_MAX=20
DATABASE_CONNECTION_TIMEOUT=30
```

#### External Service Integration

```bash
# SMS Gateway Configuration
SMS_GATEWAY_URL=https://sms-gateway.example.com/api/v1
SMS_API_KEY=your-sms-api-key
SMS_SENDER_ID=DGAPI
SMS_RETRY_ATTEMPTS=3
SMS_RETRY_DELAY=5

# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=smtp-password
SMTP_ENCRYPTION=tls                # Options: tls, ssl, none
SMTP_FROM_ADDRESS=noreply@example.com
SMTP_FROM_NAME=Disposition Gateway

# SGAPI Integration
SGAPI_BASE_URL=https://sgapi.example.com
SGAPI_TOKEN=your-sgapi-token
SGAPI_TIMEOUT=30
SGAPI_RETRY_ENABLED=true
SGAPI_RETRY_ATTEMPTS=3

# Voicemail Service
VOICEMAIL_SERVICE_URL=https://voicemail.example.com/api
VOICEMAIL_API_KEY=your-voicemail-key
```

#### Logging and Monitoring

```bash
# Logging Configuration
LOG_LEVEL=info                     # Options: debug, info, warning, error, critical
LOG_PATH=/var/www/html/writable/logs
LOG_MAX_FILES=30
LOG_MAX_SIZE=100M

# Performance Monitoring
ENABLE_APM=true
APM_SERVICE_NAME=platform-dgapi
APM_SERVER_URL=http://apm-server:8200
```

### Environment File Template

Create a complete `.env` file:

```bash
# .env.production
#==============================================================================
# APPLICATION SETTINGS
#==============================================================================
CI_ENVIRONMENT=production
APP_BASE_URL=https://dgapi.yourcompany.com
APP_TIMEZONE=UTC
APP_DEBUG=false
APP_KEY=base64:your-32-character-application-key-here

#==============================================================================
# DATABASE CONFIGURATION
#==============================================================================
DATABASE_HOST=db.yourcompany.internal
DATABASE_PORT=3306
DATABASE_NAME=dgapi_production
DATABASE_USER=dgapi_app
DATABASE_PASSWORD=${DB_PASSWORD}
DATABASE_CHARSET=utf8mb4
DATABASE_COLLATION=utf8mb4_unicode_ci
DATABASE_POOL_MIN=10
DATABASE_POOL_MAX=50

#==============================================================================
# AUTHENTICATION
#==============================================================================
AUTH_TOKEN_SECRET=${AUTH_SECRET}
AUTH_TOKEN_EXPIRY=3600
AUTH_RATE_LIMIT=1000
AUTH_RATE_WINDOW=60

#==============================================================================
# SMS GATEWAY
#==============================================================================
SMS_GATEWAY_URL=https://sms.provider.com/api/v2
SMS_API_KEY=${SMS_KEY}
SMS_SENDER_ID=YOURCOMPANY
SMS_RETRY_ATTEMPTS=3
SMS_RETRY_DELAY=5
SMS_QUEUE_ENABLED=true

#==============================================================================
# EMAIL CONFIGURATION
#==============================================================================
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=${SMTP_KEY}
SMTP_ENCRYPTION=tls
SMTP_FROM_ADDRESS=notifications@yourcompany.com
SMTP_FROM_NAME=Disposition Gateway
EMAIL_QUEUE_ENABLED=true

#==============================================================================
# SGAPI INTEGRATION
#==============================================================================
SGAPI_BASE_URL=https://sgapi.yourcompany.internal
SGAPI_TOKEN=${SGAPI_TOKEN}
SGAPI_TIMEOUT=30
SGAPI_RETRY_ENABLED=true

#==============================================================================
# VOICEMAIL SERVICE
#==============================================================================
VOICEMAIL_SERVICE_URL=https://vm.yourcompany.internal/api
VOICEMAIL_API_KEY=${VM_KEY}

#==============================================================================
# LOGGING
#==============================================================================
LOG_LEVEL=info
LOG_PATH=/var/www/html/writable/logs
LOG_MAX_FILES=30
LOG_CHANNEL=stack

#==============================================================================
# CACHE CONFIGURATION
#==============================================================================
CACHE_DRIVER=redis
REDIS_HOST=redis.yourcompany.internal
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DATABASE=0
```

### Secrets Management

For production deployments, use a secrets manager:

```bash
# Using Docker secrets
docker secret create dgapi_db_password ./secrets/db_password.txt
docker secret create dgapi_api_token ./secrets/api_token.txt

# Using HashiCorp Vault
vault kv put secret/dgapi \
    db_password="secure-password" \
    api_token="secure-token" \
    smtp_password="smtp-secret"

# Retrieve secrets in application
vault kv get -field=db_password secret/dgapi
```

---

## Database Setup

### Schema Initialization

The platform-dgapi service requires specific database tables. Create the initialization script:

```sql
-- database/init/001_create_schema.sql

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS dgapi_production
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE dgapi_production;

-- Task Dispositions Table
CREATE TABLE IF NOT EXISTS task_dispositions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    disposition_type ENUM('sms', 'email', 'voicemail', 'callback', 'generic') NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed', 'retry') DEFAULT 'pending',
    payload JSON NOT NULL,
    response JSON,
    retry_count INT UNSIGNED DEFAULT 0,
    max_retries INT UNSIGNED DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_disposition_type (disposition_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- CDR Records Table
CREATE TABLE IF NOT EXISTS cdr_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    call_id VARCHAR(128) NOT NULL UNIQUE,
    caller_number VARCHAR(32),
    callee_number VARCHAR(32),
    call_duration INT UNSIGNED,
    call_status VARCHAR(32),
    disposition_code VARCHAR(16),
    sgapi_sync_status ENUM('pending', 'synced', 'failed') DEFAULT 'pending',
    raw_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP NULL,
    INDEX idx_call_id (call_id),
    INDEX idx_sync_status (sgapi_sync_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Callback Events Table
CREATE TABLE IF NOT EXISTS callback_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    callback_id VARCHAR(64) NOT NULL,
    event_type ENUM('scheduled', 'started', 'finished', 'cancelled', 'failed') NOT NULL,
    agent_id VARCHAR(64),
    customer_number VARCHAR(32),
    notes TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_callback_id (callback_id),
    INDEX idx_event_type (event_type),
    INDEX idx_agent_id (agent_id)
) ENGINE=InnoDB;

-- API Tokens Table
CREATE TABLE IF NOT EXISTS api_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    permissions JSON,
    rate_limit INT UNSIGNED DEFAULT 1000,
    expires_at TIMESTAMP NULL,
    last_used_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_token_hash (token_hash),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB;

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64),
    actor_id VARCHAR(64),
    actor_ip VARCHAR(45),
    old_values JSON,
    new_values JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_action (action),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;
```

### Database Migrations

Run migrations using the CodeIgniter CLI:

```bash
# Run migrations inside the container
docker compose exec platform-dgapi php spark migrate

# Run specific migration
docker compose exec platform-dgapi php spark migrate:rollback

# Check migration status
docker compose exec platform-dgapi php spark migrate:status

# Seed initial data
docker compose exec platform-dgapi php spark db:seed InitialDataSeeder
```

### Database Optimization

Apply these optimizations for production:

```sql
-- Performance optimizations
SET GLOBAL innodb_buffer_pool_size = 1G;
SET GLOBAL innodb_log_file_size = 256M;
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL max_connections = 200;

-- Create read replica user (if using replication)
CREATE USER 'dgapi_readonly'@'%' IDENTIFIED BY 'readonly-password';
GRANT SELECT ON dgapi_production.* TO 'dgapi_readonly'@'%';
FLUSH PRIVILEGES;
```

### Backup Configuration

Set up automated backups:

```bash
#!/bin/bash
# scripts/backup-database.sh

BACKUP_DIR="/backups/dgapi"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup
docker compose exec -T db mysqldump \
    -u root \
    -p"${MYSQL_ROOT_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    dgapi_production > "${BACKUP_DIR}/dgapi_${DATE}.sql"

# Compress backup
gzip "${BACKUP_DIR}/dgapi_${DATE}.sql"

# Remove old backups
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup completed: dgapi_${DATE}.sql.gz"
```

---

## Health Checks

### Application Health Endpoint

Implement a comprehensive health check endpoint:

```php
<?php
// app/Controllers/Health.php

namespace App\Controllers;

use CodeIgniter\RESTful\ResourceController;

class Health extends ResourceController
{
    protected $format = 'json';

    public function index()
    {
        $health = [
            'status' => 'healthy',
            'timestamp' => date('c'),
            'version' => getenv('APP_VERSION') ?: '1.0.0',
            'checks' => []
        ];

        // Database check
        $health['checks']['database'] = $this->checkDatabase();

        // Redis check
        $health['checks']['redis'] = $this->checkRedis();

        // External services check
        $health['checks']['sms_gateway'] = $this->checkSmsGateway();
        $health['checks']['sgapi'] = $this->checkSgapi();

        // Disk space check
        $health['checks']['disk_space'] = $this->checkDiskSpace();

        // Determine overall status
        $failed = array_filter($health['checks'], fn($c) => $c['status'] !== 'healthy');
        if (!empty($failed)) {
            $health['status'] = 'degraded';
            return $this->respond($health, 503);
        }

        return $this->respond($health, 200);
    }

    private function checkDatabase(): array
    {
        try {
            $db = \Config\Database::connect();
            $db->query('SELECT 1');
            return ['status' => 'healthy', 'latency_ms' => 0];
        } catch (\Exception $e) {
            return ['status' => 'unhealthy', 'error' => $e->getMessage()];
        }
    }

    private function checkRedis(): array
    {
        try {
            $redis = new \Redis();
            $redis->connect(getenv('REDIS_HOST'), getenv('REDIS_PORT'));
            $redis->ping();
            return ['status' => 'healthy'];
        } catch (\Exception $e) {
            return ['status' => 'unhealthy', 'error' => $e->getMessage()];
        }
    }

    private function checkDiskSpace(): array
    {
        $free = disk_free_space('/var/www/html/writable');
        $total = disk_total_space('/var/www/html/writable');
        $usedPercent = (($total - $free) / $total) * 100;

        return [
            'status' => $usedPercent < 90 ? 'healthy' : 'warning',
            'free_gb' => round($free / 1073741824, 2),
            'used_percent' => round($usedPercent, 2)
        ];
    }
}
```

### Docker Health Check Configuration

Configure container health checks:

```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Kubernetes Probes (Optional)

If deploying to Kubernetes:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: platform-dgapi
spec:
  template:
    spec:
      containers:
        - name: dgapi
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 30
```

### Monitoring Integration

Set up external monitoring:

```bash
# Prometheus metrics endpoint (add to routes)
# GET /metrics

# Example Prometheus scrape config
scrape_configs:
  - job_name: 'platform-dgapi'
    static_configs:
      - targets: ['dgapi:8080']
    metrics_path: /metrics
    scrape_interval: 15s
```

---

## Logging

### Log Configuration

Configure comprehensive logging in CodeIgniter:

```php
<?php
// app/Config/Logger.php

namespace Config;

use CodeIgniter\Config\BaseConfig;

class Logger extends BaseConfig
{
    public $threshold = 4; // 1 = Error, 4 = Debug

    public $handlers = [
        'CodeIgniter\Log\Handlers\FileHandler' => [
            'handles' => ['critical', 'alert', 'emergency', 'debug', 'error', 'info', 'notice', 'warning'],
            'filePermissions' => 0644,
        ],
    ];
}
```

### Structured Logging

Implement structured JSON logging:

```php
<?php
// app/Libraries/StructuredLogger.php

namespace App\Libraries;

class StructuredLogger
{
    public static function log(string $level, string $message, array $context = []): void
    {
        $logEntry = [
            'timestamp' => date('c'),
            'level' => $level,
            'message' => $message,
            'service' => 'platform-dgapi',
            'environment' => getenv('CI_ENVIRONMENT'),
            'request_id' => $_SERVER['HTTP_X_REQUEST_ID'] ?? uniqid(),
            'context' => $context
        ];

        error_log(json_encode($logEntry));
    }

    public static function info(string $message, array $context = []): void
    {
        self::log('info', $message, $context);
    }

    public static function error(string $message, array $context = []): void
    {
        self::log('error', $message, $context);
    }
}
```

### Log Aggregation with ELK Stack

Configure Filebeat for log shipping:

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  indices:
    - index: "dgapi-logs-%{+yyyy.MM.dd}"
      when.contains:
        container.name: "platform-dgapi"

setup.kibana:
  host: "kibana:5601"
```

### Log Rotation

Configure log rotation:

```bash
# /etc/logrotate.d/dgapi
/var/www/html/writable/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        docker compose exec -T platform-dgapi kill -USR1 1
    endscript
}
```

---

## Troubleshooting

### Common Deployment Issues

#### 1. Container Fails to Start

**Symptoms**: Container exits immediately or restarts repeatedly.

**Diagnosis**:
```bash
# Check container logs
docker compose logs platform-dgapi

# Check container exit code
docker inspect platform-dgapi --format='{{.State.ExitCode}}'

# Check container events
docker events --filter container=platform-dgapi
```

**Common Causes and Solutions**:

| Exit Code | Cause | Solution |
|-----------|-------|----------|
| 1 | Application error | Check PHP error logs |
| 137 | OOM killed | Increase memory limit |
| 139 | Segmentation fault | Check PHP extensions |
| 255 | General error | Verify configuration |

```bash
# Fix: Increase memory limit
docker compose up -d --scale platform-dgapi=1 --no-recreate
docker update --memory=2g platform-dgapi
```

#### 2. Database Connection Failures

**Symptoms**: "Connection refused" or "Access denied" errors.

**Diagnosis**:
```bash
# Test database connectivity from container
docker compose exec platform-dgapi bash -c \
    "php -r \"new PDO('mysql:host=\$DATABASE_HOST;dbname=\$DATABASE_NAME', '\$DATABASE_USER', '\$DATABASE_PASSWORD');\""

# Check database container
docker compose exec db mysqladmin ping -h localhost -u root -p
```

**Solutions**:
```bash
# Verify environment variables
docker compose exec platform-dgapi env | grep DATABASE

# Check network connectivity
docker compose exec platform-dgapi ping -c 3 db

# Reset database password
docker compose exec db mysql -u root -p -e \
    "ALTER USER 'dgapi_user'@'%' IDENTIFIED BY 'new-password';"
```

#### 3. External API Integration Failures

**Symptoms**: SMS, email, or SGAPI integrations failing.

**Diagnosis**:
```bash
# Test external connectivity
docker compose exec platform-dgapi curl -v https://sms-gateway.example.com/health

# Check SSL certificates
docker compose exec platform-dgapi openssl s_client -connect sgapi.example.com:443

# Verify API credentials
docker compose exec platform-dgapi php spark test:api-connection
```

**Solutions**:
```bash
# Update CA certificates
docker compose exec platform-dgapi update-ca-certificates

# Test with verbose output
docker compose exec platform-dgapi curl -v -H "Authorization: Bearer ${SGAPI_TOKEN}" \
    https://sgapi.example.com/api/health
```

#### 4. Performance Issues

**Symptoms**: Slow response times, timeouts.

**Diagnosis**:
```bash
# Check container resource usage
docker stats platform-dgapi

# Profile PHP execution
docker compose exec platform-dgapi php spark profile:request

# Check database slow queries
docker compose exec db mysql -u root -p -e \
    "SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;"
```

**Solutions**:
```bash
# Enable OPcache
docker compose exec platform-dgapi bash -c \
    "echo 'opcache.enable=1' >> /usr/local/etc/php/conf.d/opcache.ini"

# Increase PHP memory
docker compose exec platform-dgapi bash -c \
    "echo 'memory_limit=512M' >> /usr/local/etc/php/conf.d/memory.ini"

# Restart container
docker compose restart platform-dgapi
```

### Debugging Tools

```bash
# Enter container shell
docker compose exec platform-dgapi bash

# Tail logs in real-time
docker compose logs -f --tail=100 platform-dgapi

# Run CodeIgniter commands
docker compose exec platform-dgapi php spark list

# Check PHP configuration
docker compose exec platform-dgapi php -i | grep -i "memory\|max"

# Database CLI access
docker compose exec db mysql -u root -p dgapi_production
```

### Recovery Procedures

#### Full Service Recovery

```bash
#!/bin/bash
# scripts/recover-service.sh

echo "Stopping all services..."
docker compose down

echo "Cleaning up volumes (optional)..."
# docker compose down -v  # Uncomment to remove volumes

echo "Pulling latest images..."
docker compose pull

echo "Rebuilding application..."
docker compose build --no-cache

echo "Starting services..."
docker compose up -d

echo "Running migrations..."
docker compose exec platform-dgapi php spark migrate

echo "Verifying health..."
sleep 30
curl -f http://localhost:8080/health && echo "Recovery complete!" || echo "Recovery failed!"
```

#### Database Recovery

```bash
#!/bin/bash
# scripts/restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file.sql.gz>"
    exit 1
fi

echo "Stopping application..."
docker compose stop platform-dgapi

echo "Restoring database from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | docker compose exec -T db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" dgapi_production

echo "Starting application..."
docker compose start platform-dgapi

echo "Verifying restoration..."
docker compose exec db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT COUNT(*) FROM dgapi_production.task_dispositions;"
```

---

## Summary

This deployment guide covered the essential aspects of deploying the platform-dgapi service:

1. **Prerequisites**: System requirements, software dependencies, and network configuration
2. **Docker Deployment**: Dockerfile creation, Docker Compose configuration, and production deployment strategies
3. **Environment Configuration**: Complete reference of 39+ configuration variables with examples
4. **Database Setup**: Schema initialization, migrations, optimization, and backup procedures
5. **Health Checks**: Application health endpoints, container health checks, and monitoring integration
6. **Logging**: Structured logging, log aggregation, and rotation strategies
7. **Troubleshooting**: Common issues, debugging tools, and recovery procedures

For additional support, consult the following resources:

- **API Documentation**: See the API Reference guide for all 18 endpoints
- **Data Models**: Review the 12 data model specifications
- **Configuration Reference**: Complete list of all 39 configuration variables

**Support Contacts**:
- Platform Team: platform-team@yourcompany.com
- On-call Support: +1-XXX-XXX-XXXX