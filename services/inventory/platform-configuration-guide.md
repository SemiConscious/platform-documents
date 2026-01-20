# Platform Core Services Configuration Guide

> **Last Updated**: 2026-01-20  
> **Document Status**: Active  
> **Owner**: Platform Engineering

## Overview

This guide provides comprehensive configuration details for all core platform services, including environment variables, configuration files, and deployment settings.

---

## Table of Contents

1. [Platform-API Configuration](#1-platform-api-configuration)
2. [Platform-Sapien Configuration](#2-platform-sapien-configuration)
3. [CDRMunch Configuration](#3-cdrmunch-configuration)
4. [Archiving Configuration](#4-archiving-configuration)
5. [Database Configuration](#5-database-configuration)
6. [Message Queue Configuration](#6-message-queue-configuration)

---

## 1. Platform-API Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | `core-sql-rw` | Primary MySQL host |
| `DB_USER` | Yes | `coreapi` | Database username |
| `DB_PASS` | Yes | - | Database password |
| `DB_NAME` | No | `API` | Default database name |
| `DB_PORT` | No | `3306` | MySQL port |
| `API_ENV` | No | `prod` | Environment: `dev`, `qa`, `staging`, `prod` |
| `ALLOWED_HOSTS` | No | - | Allowed host patterns (comma-separated) |
| `CACHE_DIR` | No | `/tmp/db_cache` | Query cache directory |
| `LOG_LEVEL` | No | `warning` | Log level |
| `SESSION_HANDLER` | No | `file` | Session storage: `file`, `redis`, `database` |
| `REDIS_HOST` | No | - | Redis host for caching/sessions |
| `REDIS_PORT` | No | `6379` | Redis port |

### Configuration Files

#### `application/config/coreapi.php`

```php
<?php
$config = array(
    // API Settings
    'api_version' => '1.0',
    'api_name' => 'RedMatter Core API',
    
    // Authentication
    'auth_method' => 'hash',  // hash, token, oauth
    'auth_header' => 'Authorization',
    'session_timeout' => 3600,
    
    // Rate Limiting
    'rate_limit_enabled' => true,
    'rate_limit_requests' => 100,
    'rate_limit_window' => 60,
    
    // CORS
    'cors_enabled' => true,
    'cors_origins' => array('*'),
    'cors_methods' => array('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'),
    'cors_headers' => array('Content-Type', 'Authorization', 'X-API-Key'),
    
    // Logging
    'log_requests' => true,
    'log_responses' => false,
    'log_sensitive_data' => false,
    
    // Timeouts
    'request_timeout' => 30,
    'db_query_timeout' => 10,
);
```

#### `application/config/database.php`

```php
<?php
$active_group = 'default';
$query_builder = TRUE;

// Primary API Database
$db['default'] = array(
    'dsn'       => '',
    'hostname'  => getenv('DB_HOST') ?: 'core-sql-rw',
    'username'  => getenv('DB_USER') ?: 'coreapi',
    'password'  => getenv('DB_PASS'),
    'database'  => getenv('DB_NAME') ?: 'API',
    'dbdriver'  => 'mysqli',
    'dbprefix'  => '',
    'pconnect'  => FALSE,
    'db_debug'  => (ENVIRONMENT !== 'production'),
    'cache_on'  => FALSE,
    'cachedir'  => getenv('CACHE_DIR') ?: '/tmp/db_cache',
    'char_set'  => 'utf8mb4',
    'dbcollat'  => 'utf8mb4_unicode_ci',
    'swap_pre'  => '',
    'encrypt'   => FALSE,
    'compress'  => FALSE,
    'stricton'  => FALSE,
    'failover'  => array(),
    'save_queries' => (ENVIRONMENT !== 'production'),
);

// CDR Database (Large Data)
$db['cdrdb'] = array(
    'dsn'       => '',
    'hostname'  => getenv('CDRDB_HOST') ?: 'big-sql-rw',
    'username'  => getenv('CDRDB_USER') ?: 'coreapi',
    'password'  => getenv('CDRDB_PASS') ?: getenv('DB_PASS'),
    'database'  => 'CDRs',
    'dbdriver'  => 'mysqli',
    'char_set'  => 'utf8mb4',
    'dbcollat'  => 'utf8mb4_unicode_ci',
);

// Read-Only Replica
$db['cdrdb_ro'] = array(
    'dsn'       => '',
    'hostname'  => getenv('CDRDB_RO_HOST') ?: 'big-sql-ro',
    'username'  => getenv('CDRDB_RO_USER') ?: 'coreapi_ro',
    'password'  => getenv('CDRDB_RO_PASS') ?: getenv('DB_PASS'),
    'database'  => 'CDRs',
    'dbdriver'  => 'mysqli',
    'char_set'  => 'utf8mb4',
    'dbcollat'  => 'utf8mb4_unicode_ci',
);

// Billing Database
$db['billing'] = array(
    'dsn'       => '',
    'hostname'  => getenv('BILLING_DB_HOST') ?: 'core-sql-rw',
    'username'  => getenv('BILLING_DB_USER') ?: 'billing',
    'password'  => getenv('BILLING_DB_PASS'),
    'database'  => 'Billing',
    'dbdriver'  => 'mysqli',
    'char_set'  => 'utf8mb4',
    'dbcollat'  => 'utf8mb4_unicode_ci',
);

// LCR Database
$db['lcrdb'] = array(
    'dsn'       => '',
    'hostname'  => getenv('LCRDB_HOST') ?: 'core-sql-rw',
    'username'  => getenv('LCRDB_USER') ?: 'lcr',
    'password'  => getenv('LCRDB_PASS'),
    'database'  => 'LCR',
    'dbdriver'  => 'mysqli',
    'char_set'  => 'utf8mb4',
    'dbcollat'  => 'utf8mb4_unicode_ci',
);
```

### Docker Configuration

```yaml
# docker-compose.yml
services:
  core-api:
    image: docker-registry.redmatter.com/redmatter/core-api:${API_VERSION:-latest}
    container_name: core-api
    restart: unless-stopped
    environment:
      - DB_HOST=${DB_HOST:-core-sql-rw}
      - DB_USER=${DB_USER:-coreapi}
      - DB_PASS=${DB_PASS}
      - DB_NAME=${DB_NAME:-API}
      - CDRDB_HOST=${CDRDB_HOST:-big-sql-rw}
      - BILLING_DB_HOST=${BILLING_DB_HOST:-core-sql-rw}
      - BILLING_DB_PASS=${BILLING_DB_PASS}
      - API_ENV=${API_ENV:-prod}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS:-all}
      - LOG_LEVEL=${LOG_LEVEL:-warning}
    volumes:
      - api-cache:/tmp/db_cache
      - api-logs:/var/log/coreapi
    networks:
      - core-api
      - database
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

volumes:
  api-cache:
  api-logs:

networks:
  core-api:
  database:
```

---

## 2. Platform-Sapien Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SYMFONY__DATABASE_HOST` | Yes | - | MySQL host |
| `SYMFONY__DATABASE_PORT` | No | `3306` | MySQL port |
| `SYMFONY__DATABASE_NAME` | Yes | `sapien` | Database name |
| `SYMFONY__DATABASE_USER` | Yes | - | Database username |
| `SYMFONY__DATABASE_PASSWORD` | Yes | - | Database password |
| `SYMFONY__SECRET` | Yes | - | Symfony secret key |
| `SYMFONY__MAILER_URL` | No | - | Mailer DSN |
| `SYMFONY__API_GATEWAY__PROTOCOL` | No | `https` | API protocol |
| `SYMFONY__API_GATEWAY__HOST` | Yes | - | API gateway hostname |
| `AWS_ACCESS_KEY_ID` | Yes | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | - | AWS secret key |
| `AWS_DEFAULT_REGION` | No | `eu-west-1` | AWS region |
| `S3_BUCKET` | No | - | S3 bucket name |
| `RABBITMQ_HOST` | No | `localhost` | RabbitMQ host |
| `RABBITMQ_PORT` | No | `5672` | RabbitMQ port |
| `RABBITMQ_USER` | No | `guest` | RabbitMQ username |
| `RABBITMQ_PASS` | No | `guest` | RabbitMQ password |
| `RABBITMQ_VHOST` | No | `/` | RabbitMQ vhost |
| `REDIS_HOST` | No | `localhost` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `SAPIEN_GOOGLE_TTS_KEY` | No | - | Google TTS API key |

### Symfony Configuration

#### `app/config/parameters.yml`

```yaml
parameters:
    database_host: '%env(SYMFONY__DATABASE_HOST)%'
    database_port: '%env(SYMFONY__DATABASE_PORT)%'
    database_name: '%env(SYMFONY__DATABASE_NAME)%'
    database_user: '%env(SYMFONY__DATABASE_USER)%'
    database_password: '%env(SYMFONY__DATABASE_PASSWORD)%'
    
    mailer_transport: smtp
    mailer_host: '%env(MAILER_HOST)%'
    mailer_user: '%env(MAILER_USER)%'
    mailer_password: '%env(MAILER_PASSWORD)%'
    
    secret: '%env(SYMFONY__SECRET)%'
    
    # API Gateway
    api_gateway_protocol: '%env(SYMFONY__API_GATEWAY__PROTOCOL)%'
    api_gateway_host: '%env(SYMFONY__API_GATEWAY__HOST)%'
    
    # AWS
    aws_access_key: '%env(AWS_ACCESS_KEY_ID)%'
    aws_secret_key: '%env(AWS_SECRET_ACCESS_KEY)%'
    aws_region: '%env(AWS_DEFAULT_REGION)%'
    s3_bucket: '%env(S3_BUCKET)%'
    
    # RabbitMQ
    rabbitmq_host: '%env(RABBITMQ_HOST)%'
    rabbitmq_port: '%env(RABBITMQ_PORT)%'
    rabbitmq_user: '%env(RABBITMQ_USER)%'
    rabbitmq_pass: '%env(RABBITMQ_PASS)%'
    rabbitmq_vhost: '%env(RABBITMQ_VHOST)%'
    
    # Redis
    redis_host: '%env(REDIS_HOST)%'
    redis_port: '%env(REDIS_PORT)%'
```

#### `app/config/config.yml`

```yaml
# Doctrine Configuration
doctrine:
    dbal:
        default_connection: default
        connections:
            default:
                driver: pdo_mysql
                host: '%database_host%'
                port: '%database_port%'
                dbname: '%database_name%'
                user: '%database_user%'
                password: '%database_password%'
                charset: UTF8MB4
                default_table_options:
                    charset: utf8mb4
                    collate: utf8mb4_unicode_ci
                server_version: '5.7'
                
    orm:
        auto_generate_proxy_classes: '%kernel.debug%'
        naming_strategy: doctrine.orm.naming_strategy.underscore
        auto_mapping: true
        
# FOS OAuth Server Bundle
fos_oauth_server:
    db_driver: orm
    client_class: Redmatter\SapienBundle\Entity\Client
    access_token_class: Redmatter\SapienBundle\Entity\AccessToken
    refresh_token_class: Redmatter\SapienBundle\Entity\RefreshToken
    auth_code_class: Redmatter\SapienBundle\Entity\AuthCode
    service:
        user_provider: fos_user.user_provider.username
        options:
            access_token_lifetime: 3600
            refresh_token_lifetime: 2592000
            
# Monolog Configuration
monolog:
    handlers:
        main:
            type: fingers_crossed
            action_level: error
            handler: nested
        nested:
            type: stream
            path: '%kernel.logs_dir%/%kernel.environment%.log'
            level: debug
        console:
            type: console
            process_psr_3_messages: false
            channels: ['!event', '!doctrine']
            
# Old Sound RabbitMQ Bundle
old_sound_rabbit_mq:
    connections:
        default:
            host: '%rabbitmq_host%'
            port: '%rabbitmq_port%'
            user: '%rabbitmq_user%'
            password: '%rabbitmq_pass%'
            vhost: '%rabbitmq_vhost%'
            lazy: true
            connection_timeout: 3
            read_write_timeout: 3
            keepalive: false
            heartbeat: 0
    producers:
        events:
            connection: default
            exchange_options:
                name: 'events'
                type: topic
    consumers:
        user_events:
            connection: default
            exchange_options:
                name: 'events'
                type: topic
            queue_options:
                name: 'user-events'
                routing_keys:
                    - 'user.*'
            callback: sapien.consumer.user_events
            qos_options:
                prefetch_size: 0
                prefetch_count: 10
                global: false
```

#### `app/config/security.yml`

```yaml
security:
    encoders:
        FOS\UserBundle\Model\UserInterface: bcrypt

    role_hierarchy:
        ROLE_ADMIN: ROLE_USER
        ROLE_SUPER_ADMIN: [ROLE_ADMIN, ROLE_ALLOWED_TO_SWITCH]

    providers:
        fos_userbundle:
            id: fos_user.user_provider.username_email

    firewalls:
        dev:
            pattern: ^/(_(profiler|wdt)|css|images|js)/
            security: false
            
        oauth_token:
            pattern: ^/oauth/v2/token
            security: false
            
        oauth_authorize:
            pattern: ^/oauth/v2/auth
            form_login:
                provider: fos_userbundle
                check_path: /oauth/v2/auth_login_check
                login_path: /oauth/v2/auth_login
            anonymous: true
            
        api:
            pattern: ^/api
            fos_oauth: true
            stateless: true
            anonymous: false
            
        main:
            pattern: ^/
            form_login:
                provider: fos_userbundle
                csrf_token_generator: security.csrf.token_manager
            logout: true
            anonymous: true

    access_control:
        - { path: ^/oauth/v2/token, roles: IS_AUTHENTICATED_ANONYMOUSLY }
        - { path: ^/oauth/v2/auth_login$, roles: IS_AUTHENTICATED_ANONYMOUSLY }
        - { path: ^/oauth/v2/auth, roles: IS_AUTHENTICATED_REMEMBERED }
        - { path: ^/api, roles: IS_AUTHENTICATED_FULLY }
        - { path: ^/admin, roles: ROLE_ADMIN }
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  sapien-core:
    container_name: sapien-core
    build:
      context: ./core
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - SYMFONY__DATABASE_HOST=${MYSQL_HOST:-sapien-database}
      - SYMFONY__DATABASE_PORT=${MYSQL_PORT:-3306}
      - SYMFONY__DATABASE_NAME=${MYSQL_DATABASE:-sapien}
      - SYMFONY__DATABASE_USER=${MYSQL_USER:-sapien}
      - SYMFONY__DATABASE_PASSWORD=${MYSQL_PASSWORD}
      - SYMFONY__SECRET=${SYMFONY_SECRET}
      - SYMFONY__API_GATEWAY__PROTOCOL=${API_PROTOCOL:-https}
      - SYMFONY__API_GATEWAY__HOST=${API_HOST}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_DEFAULT_REGION=${AWS_REGION:-eu-west-1}
      - S3_BUCKET=${S3_BUCKET}
      - RABBITMQ_HOST=${RABBITMQ_HOST:-mq}
      - RABBITMQ_USER=${RABBITMQ_USER:-sapien}
      - RABBITMQ_PASS=${RABBITMQ_PASSWORD}
      - REDIS_HOST=${REDIS_HOST:-redis}
    volumes:
      - ./core/project/src:/var/www/sapien/src
      - ./core/project/web:/var/www/sapien/web
      - sapien-logs:/var/www/sapien/var/logs
      - sapien-cache:/var/www/sapien/var/cache
    networks:
      - sapien-core
      - sapien-database
      - storage-gateway
      - mq
    depends_on:
      - sapien-database
      - mq
      - storage-gateway
    healthcheck:
      test: ["CMD", "php", "bin/console", "--env=prod", "cache:warmup"]
      interval: 60s
      timeout: 30s
      retries: 3

  sapien-database:
    image: mariadb:10.5
    container_name: sapien-database
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE:-sapien}
      - MYSQL_USER=${MYSQL_USER:-sapien}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - sapien-db-data:/var/lib/mysql
      - ./database/init:/docker-entrypoint-initdb.d
    networks:
      - sapien-database
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 30s
      timeout: 10s
      retries: 5

  mq:
    image: rabbitmq:3.9-management
    container_name: sapien-mq
    restart: unless-stopped
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER:-sapien}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
      - RABBITMQ_DEFAULT_VHOST=/
    volumes:
      - mq-data:/var/lib/rabbitmq
      - ./mq/definitions.json:/etc/rabbitmq/definitions.json
    ports:
      - "15672:15672"
    networks:
      - mq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_port_connectivity"]
      interval: 30s
      timeout: 10s
      retries: 5

  storage-gateway:
    image: minio/minio:latest
    container_name: sapien-storage
    restart: unless-stopped
    environment:
      - MINIO_ROOT_USER=${AWS_ACCESS_KEY_ID}
      - MINIO_ROOT_PASSWORD=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - storage-data:/data
    command: server /data --console-address ":9001"
    networks:
      - storage-gateway
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  sapien-db-data:
  sapien-logs:
  sapien-cache:
  mq-data:
  storage-data:

networks:
  sapien-core:
  sapien-database:
  storage-gateway:
  mq:
```

---

## 3. CDRMunch Configuration

### Service Configuration Files

#### `rmdistiller.conf`

```ini
# ======================
# Distiller Configuration
# ======================

# Process Settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch
app.work_dir = /var/lib/cdrmunch
app.max_core_size_mega_bytes = 1024
app.core_dump_dir = /tmp
app.max_file_handles = 4096
app.niceness = 10

# Distiller Service
distiller.listen_port = 10001
distiller.worker_threads = 8
distiller.worker_threads@dev = 2
distiller.worker_threads@qa = 4
distiller.queue_size = 1000

# Database Connections (via include files)
include_dir = /etc/cdrmunch/conf.d

# Cache Settings
cache.dir = /var/spool/cdrtmp/cdrmunch-cache
cache.max_size_mb = 1024
cache.max_size_mb@dev = 256
cache.max_size_mb@qa = 512

# Logging
log.file = syslog
log.level = 4
log.level@dev = 6
log.level@qa = 6

# Debug Options (non-production)
debug.disable_restart = false
debug.disable_restart@qa = true
debug.disable_restart@dev = true

# Watchdog
watchdog.enabled = true
watchdog.interval_seconds = 60
```

#### `rmcdrgateway.conf`

```ini
# =========================
# CDR Gateway Configuration
# =========================

# Process Settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch

# Gateway Service
gateway.listen_socket = :80
gateway.worker_threads = 16
gateway.worker_threads@dev = 4
gateway.worker_threads@qa = 8
gateway.max_request_size_mb = 10
gateway.request_timeout_seconds = 30

# Distiller Connection
distiller.host = cdrmunch.{hapi:SearchDomain}
distiller.port = 10001
distiller.connect_timeout_ms = 5000
distiller.read_timeout_ms = 30000

# Rate Limiting
rate_limit.enabled = true
rate_limit.requests_per_second = 100
rate_limit.requests_per_second@dev = 1000

# Logging
log.file = syslog
log.level = 4
log.level@dev = 6
```

#### `rmhurler.conf`

```ini
# =====================
# Hurler Configuration
# =====================

# Process Settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch
app.work_dir = /var/lib/cdrmunch/hurler

# AWS S3 Settings
s3.bucket = rm-call-analysis
s3.region = eu-west-1
s3.endpoint = 
s3.ssl_enabled = true

# AWS SQS Settings
sqs.queue_url = https://sqs.eu-west-1.amazonaws.com/123456789/call-analysis
sqs.region = eu-west-1

# Task Queue Settings
queue.poll_interval_ms = 1000
queue.batch_size = 100
queue.retry_count = 3
queue.retry_delay_ms = 5000

# Worker Settings
worker.threads = 8
worker.threads@dev = 2
worker.threads@qa = 4

# Logging
log.file = syslog
log.level = 4
```

#### Database Configuration (`/etc/cdrmunch/conf.d/database.conf`)

```ini
# Default Database
database.default.host = core-sql-rw
database.default.port = 3306
database.default.user = cdrmunch
database.default.pass = ${DB_PASS}
database.default.name = API
database.default.charset = utf8mb4

# CDR Database
database.cdrdb.host = big-sql-rw
database.cdrdb.port = 3306
database.cdrdb.user = cdrmunch
database.cdrdb.pass = ${CDRDB_PASS}
database.cdrdb.name = CDRs
database.cdrdb.charset = utf8mb4

# CDR Database (Read-Only)
database.cdrdb_ro.host = big-sql-ro
database.cdrdb_ro.port = 3306
database.cdrdb_ro.user = cdrmunch_ro
database.cdrdb_ro.pass = ${CDRDB_RO_PASS}
database.cdrdb_ro.name = CDRs
database.cdrdb_ro.charset = utf8mb4

# Billing Database
database.billing.host = core-sql-rw
database.billing.port = 3306
database.billing.user = billing
database.billing.pass = ${BILLING_PASS}
database.billing.name = Billing
database.billing.charset = utf8mb4

# LCR Database (Read-Only)
database.lcrdb_ro.host = core-sql-ro
database.lcrdb_ro.port = 3306
database.lcrdb_ro.user = lcr_ro
database.lcrdb_ro.pass = ${LCR_PASS}
database.lcrdb_ro.name = LCR
database.lcrdb_ro.charset = utf8mb4
```

### Cron Job Configurations

#### `billing-feeder.conf`

```ini
# =============================
# Billing Feeder Configuration
# =============================

# Poll Settings
poll_interval_seconds = 60
batch_size = 100
max_concurrent_batches = 5

# Billing API
billing.api_url = http://billing.internal/api/v1
billing.api_key = ${BILLING_API_KEY}
billing.timeout_seconds = 30

# Retry Settings
retry.count = 3
retry.delay_seconds = 5
retry.exponential_backoff = true

# Logging
log.file = /var/log/cdrmunch/billing-feeder.log
log.level = info
log.max_size_mb = 100
log.max_files = 5
```

#### `task-executor.conf`

```ini
# =============================
# Task Executor Configuration
# =============================

# Poll Settings
poll_interval_seconds = 5
max_concurrent_tasks = 10
task_timeout_seconds = 300

# Database
database.host = core-sql-rw
database.name = API
database.user = cdrmunch
database.pass = ${DB_PASS}

# Cache Settings
estuary_cache_dir = /var/lib/cdrmunch-task-executor-estuary-cache
cache_max_size_mb = 512

# CoreAPI Integration
coreapi.url = http://cdr.coreapi.internal
coreapi.auth = ${COREAPI_AUTH}
coreapi.timeout_seconds = 30

# SMS Providers
sms.default_provider = auto
sms.textmarketer.api_key = ${TEXTMARKETER_KEY}
sms.textmarketer.username = ${TEXTMARKETER_USER}
sms.messagebird.api_key = ${MESSAGEBIRD_KEY}
sms.bandwidth.api_key = ${BANDWIDTH_KEY}
sms.bandwidth.api_secret = ${BANDWIDTH_SECRET}

# Email Settings
email.smtp_host = smtp.internal
email.smtp_port = 25
email.from_address = noreply@redmatter.com
email.from_name = RedMatter Platform

# Logging
log.file = /var/log/cdrmunch/task-executor.log
log.level = info
```

---

## 4. Archiving Configuration

### `rmarchived.conf`

```ini
# ================================
# Archived Service Configuration
# ================================

# Process Settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch
app.work_dir = /var/lib/archiving
app.max_core_size_mega_bytes = 1024
app.core_dump_dir = /tmp
app.max_file_handles = 4096
app.niceness = 10

# Service Threads
archived.service_threads = 64
archived.service_threads@dev = 8
archived.service_threads@qa = 16

# Converter Settings
converter.threads = 8
converter.threads@dev = 2
converter.threads@qa = 4
converter.enable_aes_for_orgs = all

# Queue Water Marks
archived.queue_combined_watermark = 1500
archived.queue_combined_watermark@dev = 100
archived.queue_combined_watermark@qa = 100

# Call Buffering
call_buffering.base_dir = /mnt/rmfs/call-buffering
call_buffering.watch_interval_ms = 1000

# S3 Backend
s3_backend.ssl_enabled = true
s3_backend.region = eu-west-1
s3_backend.bucket = ${S3_BUCKET}
s3_backend.access_key = ${AWS_ACCESS_KEY}
s3_backend.secret_key = ${AWS_SECRET_KEY}

# S3 Runner Threads
s3_runner.threads = 24
s3_runner.threads@dev = 2
s3_runner.threads@qa = 2
s3_runner.threads@stage = 4

# CoreAPI Integration
coreapi.url = http://cdr.coreapi.{hapi:SearchDomain}
coreapi.auth_creds = ${COREAPI_AUTH}
coreapi.timeout_seconds = 30

# Distiller Client
distiller_client.server_host = cdrmunch.{hapi:SearchDomain}
distiller_client.server_port = 10001
distiller_client.connect_timeout_ms = 5000
distiller_client.base_dir = /var/spool/cdrtmp/cdrmunch-cache

# Retention Data
retention_data.flush_interval_seconds = 10

# Ports
archived.put_port = 10100

# FastCGI Server
fcgi_server.listen_socket = :10101
fcgi_server.listen_queue_depth = 100
fcgi_server.handler_threads = 8
fcgi_server.debug = false

# Cache Directories
archived.cache_dir = /var/lib/archiving/cache
archived.cache_dir.min_free_space_KB = 500000
archived.cache_dir.min_free_space_KB@qa = 50000
archived.cache_dir.min_free_space_KB@dev = 5000

clear_cache.enabled = false
clear_cache.base_directory = /var/lib/archiving/archived/clear-cache
clear_cache.base_directory.min_free_space_KB = 500000

distiller_client.base_dir.min_free_space_KB = 500000
distiller_client.base_dir.min_free_space_KB@qa = 50000
distiller_client.base_dir.min_free_space_KB@dev = 5000

# Watchdog Settings
watchdog.archived_filehandles_minimum_free_percent = 10
watchdog.archived_filehandles_free_percent_warning_threshold = 20
watchdog.system_filehandles_minimum_free_percent = 10
watchdog.system_filehandles_free_percent_warning_threshold = 20

# Logging
log.file_path = syslog
log.level = 4
log.level@qa = 6
log.level@dev = 6

# Include additional configuration
include_dir = /etc/archiving/conf.d

# Debug Options
debug.disable_restart = false
debug.disable_restart@qa = true
debug.valgrind_enabled = false

# Stop/Kill Settings
app.seconds_to_wait_before_kill = 30
app.sigkill_after_stop_wait = false
app.backtrace_filter = /usr/bin/archiving-backtrace-filter.sh
```

### `rmestuary.conf`

```ini
# ================================
# Estuary Service Configuration
# ================================

# Process Settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch
app.work_dir = /var/lib/archiving

# FastCGI Server
fcgi_server.listen_socket = :10102
fcgi_server.listen_queue_depth = 100
fcgi_server.handler_threads = 4
fcgi_server.handler_threads@dev = 2
fcgi_server.handler_threads@qa = 2

# S3 Backend
s3_backend.ssl_enabled = true
s3_backend.region = eu-west-1
s3_backend.bucket = ${S3_BUCKET}
s3_backend.access_key = ${AWS_ACCESS_KEY}
s3_backend.secret_key = ${AWS_SECRET_KEY}

# Cache Settings
estuary.cache_dir = /var/lib/archiving/estuary-cache
estuary.cache_max_size_mb = 1024
estuary.cache_max_size_mb@dev = 256
estuary.cache_max_size_mb@qa = 512

# Logging
log.file_path = syslog
log.level = 4
log.level@qa = 6
log.level@dev = 6
```

---

## 5. Database Configuration

### MySQL/MariaDB Server Configuration

#### `my.cnf` (Production)

```ini
[mysqld]
# Basic Settings
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
user=mysql
symbolic-links=0

# Character Set
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

# InnoDB Settings
innodb_buffer_pool_size=8G
innodb_buffer_pool_instances=8
innodb_log_file_size=1G
innodb_log_buffer_size=256M
innodb_flush_log_at_trx_commit=1
innodb_flush_method=O_DIRECT
innodb_file_per_table=1
innodb_io_capacity=2000
innodb_io_capacity_max=4000

# Query Cache (disabled for MySQL 8+)
query_cache_type=0
query_cache_size=0

# Connections
max_connections=500
max_connect_errors=10000
wait_timeout=28800
interactive_timeout=28800

# Temp Tables
tmp_table_size=256M
max_heap_table_size=256M

# Replication
server-id=1
log_bin=mysql-bin
binlog_format=ROW
expire_logs_days=7
sync_binlog=1

# Slow Query Log
slow_query_log=1
slow_query_log_file=/var/log/mysql/slow.log
long_query_time=2
log_queries_not_using_indexes=1

[mysqld_safe]
log-error=/var/log/mysql/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
```

### Connection Pool Settings

| Service | Pool Size | Max Overflow | Timeout |
|---------|-----------|--------------|---------|
| Core-API | 20 | 10 | 30s |
| Sapien | 30 | 15 | 30s |
| CDRMunch | 50 | 25 | 60s |
| Archiving | 20 | 10 | 30s |

---

## 6. Message Queue Configuration

### RabbitMQ Configuration

#### `rabbitmq.conf`

```ini
# Default user credentials
default_user = sapien
default_pass = ${RABBITMQ_PASSWORD}
default_vhost = /

# Networking
listeners.tcp.default = 5672
management.listener.port = 15672
management.listener.ssl = false

# Memory
vm_memory_high_watermark.relative = 0.6
vm_memory_high_watermark_paging_ratio = 0.75

# Disk
disk_free_limit.absolute = 2GB

# Cluster
cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config
cluster_formation.classic_config.nodes.1 = rabbit@mq1
cluster_formation.classic_config.nodes.2 = rabbit@mq2
cluster_formation.classic_config.nodes.3 = rabbit@mq3

# Queues
queue_master_locator = min-masters

# Management
management.load_definitions = /etc/rabbitmq/definitions.json
```

#### `definitions.json`

```json
{
    "rabbit_version": "3.9.0",
    "users": [
        {
            "name": "sapien",
            "password_hash": "${SAPIEN_PASSWORD_HASH}",
            "hashing_algorithm": "rabbit_password_hashing_sha256",
            "tags": "administrator"
        },
        {
            "name": "monitoring",
            "password_hash": "${MONITORING_PASSWORD_HASH}",
            "hashing_algorithm": "rabbit_password_hashing_sha256",
            "tags": "monitoring"
        }
    ],
    "vhosts": [
        {"name": "/"}
    ],
    "permissions": [
        {
            "user": "sapien",
            "vhost": "/",
            "configure": ".*",
            "write": ".*",
            "read": ".*"
        }
    ],
    "exchanges": [
        {
            "name": "events",
            "vhost": "/",
            "type": "topic",
            "durable": true,
            "auto_delete": false,
            "internal": false,
            "arguments": {}
        },
        {
            "name": "events.dlx",
            "vhost": "/",
            "type": "fanout",
            "durable": true,
            "auto_delete": false,
            "internal": false,
            "arguments": {}
        }
    ],
    "queues": [
        {
            "name": "user-events",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {
                "x-dead-letter-exchange": "events.dlx",
                "x-message-ttl": 86400000
            }
        },
        {
            "name": "call-events",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {
                "x-dead-letter-exchange": "events.dlx",
                "x-message-ttl": 86400000
            }
        },
        {
            "name": "recording-events",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {
                "x-dead-letter-exchange": "events.dlx",
                "x-message-ttl": 86400000
            }
        },
        {
            "name": "voicemail-events",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {
                "x-dead-letter-exchange": "events.dlx",
                "x-message-ttl": 86400000
            }
        },
        {
            "name": "events.dlq",
            "vhost": "/",
            "durable": true,
            "auto_delete": false,
            "arguments": {}
        }
    ],
    "bindings": [
        {
            "source": "events",
            "vhost": "/",
            "destination": "user-events",
            "destination_type": "queue",
            "routing_key": "user.*",
            "arguments": {}
        },
        {
            "source": "events",
            "vhost": "/",
            "destination": "call-events",
            "destination_type": "queue",
            "routing_key": "call.*",
            "arguments": {}
        },
        {
            "source": "events",
            "vhost": "/",
            "destination": "recording-events",
            "destination_type": "queue",
            "routing_key": "recording.*",
            "arguments": {}
        },
        {
            "source": "events",
            "vhost": "/",
            "destination": "voicemail-events",
            "destination_type": "queue",
            "routing_key": "voicemail.*",
            "arguments": {}
        },
        {
            "source": "events.dlx",
            "vhost": "/",
            "destination": "events.dlq",
            "destination_type": "queue",
            "routing_key": "",
            "arguments": {}
        }
    ],
    "policies": [
        {
            "vhost": "/",
            "name": "ha-all",
            "pattern": ".*",
            "apply-to": "queues",
            "definition": {
                "ha-mode": "all",
                "ha-sync-mode": "automatic"
            },
            "priority": 0
        }
    ]
}
```

---

## Environment-Specific Overrides

### Development Environment

```bash
# .env.dev
API_ENV=dev
LOG_LEVEL=debug
DEBUG=true
DB_HOST=localhost
DB_PORT=3306
RABBITMQ_HOST=localhost
REDIS_HOST=localhost
```

### QA Environment

```bash
# .env.qa
API_ENV=qa
LOG_LEVEL=info
DEBUG=false
DB_HOST=qa-core-sql-rw
RABBITMQ_HOST=qa-mq
REDIS_HOST=qa-redis
```

### Production Environment

```bash
# .env.prod
API_ENV=prod
LOG_LEVEL=warning
DEBUG=false
DB_HOST=core-sql-rw
RABBITMQ_HOST=mq1,mq2,mq3
REDIS_HOST=redis-cluster
```

---

## Related Documentation

- [Platform Core Services Inventory](platform-core.md)
- [API Reference](platform-sapien-api-reference.md)
- [Deployment Guide](../operations/deployment-guide.md)
- [Troubleshooting Guide](../operations/troubleshooting.md)
