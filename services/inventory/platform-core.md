# Platform Core Services Repository Inventory

> **Last Updated**: 2026-01-20  
> **Document Status**: Active  
> **Owner**: Platform Engineering

## Overview

This document provides a comprehensive inventory of all core platform service repositories, including their tech stacks, API endpoints, database dependencies, message queue usage, caching mechanisms, authentication patterns, and inter-service communication.

---

## Table of Contents

1. [Platform-API (Core API)](#1-platform-api-core-api)
2. [Platform-Sapien](#2-platform-sapien)
3. [Platform-CDRMunch](#3-platform-cdrmunch)
4. [Platform-Archiving](#4-platform-archiving)
5. [Inter-Service Communication Patterns](#5-inter-service-communication-patterns)
6. [Shared Database Infrastructure](#6-shared-database-infrastructure)

---

## 1. Platform-API (Core API)

### Repository Information

| Field | Value |
|-------|-------|
| **Repository** | `redmatter/platform-api` |
| **Primary Language** | PHP 5.4+ (CodeIgniter 2.x Framework) |
| **Database** | MySQL/MariaDB (Multiple databases) |
| **Deployment** | RPM packages, Docker containers |
| **Docker Image** | `docker-registry.redmatter.com/redmatter/core-api` |

### Tech Stack

- **Framework**: CodeIgniter 2.x (PHP MVC)
- **PHP Version**: 5.4+
- **Web Server**: Apache with mod_fcgid
- **Database ORM**: CodeIgniter Active Record
- **Authentication**: Custom hash-based authentication, API keys
- **Caching**: File-based caching, Redis (optional)

### Directory Structure

```
platform-api/
├── application/
│   ├── config/           # Configuration files
│   │   ├── coreapi.php   # Core API settings
│   │   ├── database.php  # Database connections
│   │   ├── routes.php    # URL routing
│   │   └── redis.php     # Redis configuration
│   ├── controllers/      # API endpoints
│   ├── models/           # Data models
│   ├── libraries/        # Shared libraries
│   └── views/            # Response templates
├── system/               # CodeIgniter core
└── public/               # Web root
```

### Database Configuration

The platform-api connects to multiple MySQL databases:

| Database | Purpose | Configuration Key |
|----------|---------|-------------------|
| `default` | Primary API data | `database.php['default']` |
| `apidata` | Extended API data | `database.php['apidata']` |
| `cdrdb` | CDR/Call records | `database.php['cdrdb']` |
| `lcrdb` | LCR routing data | `database.php['lcrdb']` |
| `billing` | Billing records | `database.php['billing']` |
| `logs` | Application logs | `database.php['logs']` |

**Connection Configuration Pattern**:
```php
$db['default'] = array(
    'dsn'      => '',
    'hostname' => getenv('DB_HOST') ?: 'core-sql-rw',
    'username' => getenv('DB_USER') ?: 'coreapi',
    'password' => getenv('DB_PASS'),
    'database' => 'API',
    'dbdriver' => 'mysqli',
    'dbprefix' => '',
    'pconnect' => FALSE,
    'db_debug' => FALSE,
    'cache_on' => FALSE,
    'cachedir' => '/tmp/db_cache',
    'char_set' => 'utf8',
    'dbcollat' => 'utf8_general_ci',
    'swap_pre' => '',
    'encrypt'  => FALSE,
    'compress' => FALSE,
    'stricton' => FALSE,
    'failover' => array()
);
```

### API Endpoints Overview

The Core API provides REST endpoints for core platform functionality:

#### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User authentication |
| POST | `/auth/logout` | Session termination |
| POST | `/auth/refresh` | Token refresh |
| GET | `/auth/validate` | Token validation |

#### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List users |
| GET | `/users/{id}` | Get user details |
| POST | `/users` | Create user |
| PUT | `/users/{id}` | Update user |
| DELETE | `/users/{id}` | Delete user |

#### Organization/Account Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orgs` | List organizations |
| GET | `/orgs/{id}` | Get organization |
| POST | `/orgs` | Create organization |
| PUT | `/orgs/{id}` | Update organization |
| GET | `/orgs/{id}/users` | Get org users |

#### Telephony Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/extensions` | List extensions |
| GET | `/dids` | List DIDs |
| GET | `/queues` | List call queues |
| GET | `/ivrs` | List IVR configurations |
| GET | `/routes` | List routing rules |

### Authentication Mechanisms

1. **API Key Authentication**:
   - Header: `X-API-Key: <api_key>`
   - Used for service-to-service communication

2. **Hash-Based Authentication**:
   - Header: `Authorization: <auth_hash>`
   - Format: `base64(username:password_hash)`

3. **Session-Based Authentication**:
   - Cookie-based sessions for web UI
   - Session stored in database/file

### Caching Layer

- **File Cache**: `/tmp/db_cache/` for query results
- **Redis** (optional): Session storage, API rate limiting

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | MySQL hostname | `core-sql-rw` |
| `DB_USER` | Database username | `coreapi` |
| `DB_PASS` | Database password | - |
| `ALLOWED_HOSTS` | Allowed host patterns | - |
| `API_ENV` | Environment (dev/qa/prod) | `prod` |

### Deployment Configuration

**Docker Compose Integration**:
```yaml
core-api:
  image: docker-registry.redmatter.com/redmatter/core-api:1.218.0
  container_name: core-api
  environment:
    - ALLOWED_HOSTS=all
  networks:
    core-api:
      aliases:
        - api
    sapien-database:
  depends_on:
    - sapien-database
    - syslog
```

---

## 2. Platform-Sapien

### Repository Information

| Field | Value |
|-------|-------|
| **Repository** | `redmatter/platform-sapien` |
| **Primary Language** | PHP 8.x (Symfony 4.x/5.x Framework) |
| **Database** | MySQL/MariaDB via Doctrine ORM |
| **Message Queue** | RabbitMQ |
| **Deployment** | Docker containers |

### Tech Stack

- **Framework**: Symfony 4.x/5.x
- **PHP Version**: 8.0+
- **ORM**: Doctrine 2.x
- **Template Engine**: Twig
- **Authentication**: OAuth 2.0 (FOS OAuthServerBundle)
- **API Documentation**: OpenAPI/Swagger
- **Testing**: PHPUnit, Codeception

### Directory Structure

```
platform-sapien/
├── core/
│   └── project/
│       ├── app/
│       │   └── config/
│       │       ├── config.yml        # Main Symfony config
│       │       ├── security.yml      # Security configuration
│       │       └── parameters.yml    # Environment parameters
│       ├── src/
│       │   └── Redmatter/
│       │       └── SapienBundle/
│       │           ├── Controller/   # API controllers
│       │           ├── Entity/       # Doctrine entities
│       │           ├── Repository/   # Data repositories
│       │           ├── Service/      # Business logic
│       │           └── Resources/
│       │               └── config/
│       │                   ├── routing.yml
│       │                   └── services.yml
│       └── vendor/                   # Composer dependencies
├── front-end/                        # Nginx reverse proxy
├── sandbox/                          # API sandbox/testing
├── mq/
│   ├── consumer/                     # RabbitMQ consumers
│   ├── publisher/                    # RabbitMQ publishers
│   └── server/                       # RabbitMQ server config
├── storage-gateway/                  # MinIO S3 gateway
├── esl-listener-server/              # FreeSWITCH ESL listener
├── mock-server/                      # Test mock server
└── docker-compose.yml
```

### Doctrine Entity Models

The Sapien bundle contains the following key entities:

#### Core Entities
| Entity | Table | Description |
|--------|-------|-------------|
| `User` | `users` | User accounts |
| `Organisation` | `organisations` | Organizations/Accounts |
| `Customer` | `customers` | End customers |
| `Extension` | `extensions` | Phone extensions |
| `DID` | `dids` | Direct Inward Dial numbers |
| `Queue` | `queues` | Call queues |
| `IVR` | `ivrs` | IVR menus |
| `Voicemail` | `voicemails` | Voicemail boxes |
| `Recording` | `recordings` | Call recordings |

#### OAuth Entities
| Entity | Table | Description |
|--------|-------|-------------|
| `Client` | `oauth_clients` | OAuth clients |
| `AccessToken` | `oauth_access_tokens` | Access tokens |
| `RefreshToken` | `oauth_refresh_tokens` | Refresh tokens |
| `AuthCode` | `oauth_auth_codes` | Authorization codes |

### API Controllers

| Controller | Base Path | Description |
|------------|-----------|-------------|
| `OAuthController` | `/oauth` | OAuth authentication |
| `OAuthTokenController` | `/oauth/token` | Token management |
| `CustomerController` | `/customers` | Customer management |
| `AudioController` | `/audio` | Audio file management |
| `UserController` | `/users` | User management |
| `ExtensionController` | `/extensions` | Extensions |
| `QueueController` | `/queues` | Call queues |
| `RecordingController` | `/recordings` | Call recordings |
| `VoicemailController` | `/voicemails` | Voicemail |

### Authentication Configuration

**Security Configuration** (`security.yml`):
```yaml
security:
    encoders:
        FOS\UserBundle\Model\UserInterface: bcrypt

    providers:
        fos_userbundle:
            id: fos_user.user_provider.username

    firewalls:
        oauth_token:
            pattern: ^/oauth/v2/token
            security: false
            
        api:
            pattern: ^/api
            fos_oauth: true
            stateless: true
            anonymous: false

    access_control:
        - { path: ^/oauth/v2/token, roles: IS_AUTHENTICATED_ANONYMOUSLY }
        - { path: ^/api, roles: IS_AUTHENTICATED_FULLY }
```

### Service Configuration

**Services** (`services.yml`):
```yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true
        public: false

    Redmatter\SapienBundle\:
        resource: '../../*'
        exclude: '../../{Entity,Migrations,Tests}'

    # OAuth server
    fos_oauth_server.server:
        class: OAuth2\OAuth2
        arguments:
            - '@fos_oauth_server.storage'
            - '%fos_oauth_server.server.options%'
```

### Message Queue (RabbitMQ)

**Queue Configuration** (`definitions.json`):
```json
{
    "exchanges": [
        {"name": "events", "type": "topic", "durable": true}
    ],
    "queues": [
        {"name": "user-events", "durable": true},
        {"name": "call-events", "durable": true},
        {"name": "recording-events", "durable": true}
    ],
    "bindings": [
        {"source": "events", "destination": "user-events", "routing_key": "user.*"},
        {"source": "events", "destination": "call-events", "routing_key": "call.*"},
        {"source": "events", "destination": "recording-events", "routing_key": "recording.*"}
    ]
}
```

**Event Types**:
- `user.created`, `user.updated`, `user.deleted`
- `call.started`, `call.ended`, `call.transferred`
- `recording.created`, `recording.ready`, `recording.deleted`
- `voicemail.received`, `voicemail.listened`

### Database Configuration

**Doctrine Configuration** (`config.yml`):
```yaml
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
                charset: UTF8
            
            big_data:
                driver: pdo_mysql
                host: '%big_database_host%'
                dbname: '%big_database_name%'
                
    orm:
        default_entity_manager: default
        entity_managers:
            default:
                connection: default
                mappings:
                    SapienBundle:
                        type: annotation
                        dir: '%kernel.root_dir%/../src/Redmatter/SapienBundle/Entity'
```

### Docker Deployment

**Main Service Configuration**:
```yaml
sapien-core:
  container_name: sapien-core
  build: ./core
  environment:
    - RM_LOC_IP=${RM_LOC_IP}
    - RM_XDEBUG_PORT=${RM_XDEBUG_PORT}
    - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
    - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    - SAPIEN_GOOGLE_TTS_KEY=${SAPIEN_GOOGLE_TTS_KEY}
    - API_GATEWAY__PROTOCOL=${SYMFONY__API_GATEWAY__PROTOCOL}
    - API_GATEWAY__HOST=${SYMFONY__API_GATEWAY__HOST}
  volumes:
    - ./core/project/src:/var/www/sapien/src
    - ./core/project/web:/var/www/sapien/web
  networks:
    - sapien-core
    - core-api
    - sapien-database
    - storage-gateway
    - mq
  depends_on:
    - syslog
    - sapien-database
    - core-api
    - storage-gateway
    - mq
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SYMFONY__API_GATEWAY__PROTOCOL` | API protocol | `https` |
| `SYMFONY__API_GATEWAY__HOST` | API gateway host | - |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret | - |
| `SAPIEN_GOOGLE_TTS_KEY` | Google TTS API key | - |
| `DATABASE_URL` | Doctrine database URL | - |

---

## 3. Platform-CDRMunch

### Repository Information

| Field | Value |
|-------|-------|
| **Repository** | `redmatter/platform-cdrmunch` |
| **Primary Languages** | C++ (services), PHP (cron tasks) |
| **Database** | MySQL/MariaDB |
| **Deployment** | RPM packages |

### Tech Stack

- **C++ Components**: Built with GCC 4.4, Boost 1.54
- **PHP Components**: PHP 5.4+ for cron scripts
- **XML Processing**: Zorba XQuery engine
- **Database**: MySQL++ connector
- **Build System**: Make, CMake

### Component Overview

CDRMunch is a CDR (Call Detail Record) processing system consisting of multiple components:

| Component | Type | Description |
|-----------|------|-------------|
| `rmdistiller` | C++ Daemon | CDR normalization and processing |
| `rmdistillery` | C++ Binary | CDR XQuery transformation |
| `rmcdrgateway` | C++ FCGI | HTTP gateway for CDR ingestion |
| `rmhurler` | C++ Daemon | Ships call-analysis tasks to AWS |
| `billing-feeder` | PHP Cron | Feeds billing records |
| `emailer` | PHP Cron | Email notification service |
| `task-executor` | PHP Cron | Task execution service |
| `rmtaskexslow` | PHP Cron | Slow task executor |

### Directory Structure

```
platform-cdrmunch/
├── distiller/           # CDR distiller daemon
│   ├── distiller.conf   # Configuration
│   └── rmdistiller.service
├── distillery/          # XQuery CDR transformer
│   └── normalize.xq     # Normalization queries
├── gateway/             # HTTP CDR gateway
│   ├── gateway.conf
│   └── apache.conf
├── hurler/              # AWS task hurler
│   └── rmhurler.conf
├── billing-feeder/      # Billing cron job
├── emailer/             # Email service
├── task-executor/       # Task processor
├── task-executor-slow/  # Slow task processor
├── phplib/              # Shared PHP libraries
├── tasksd/              # Legacy task daemon
└── RM-cdrmunch.spec     # RPM build specification
```

### Database Connections

CDRMunch connects to multiple databases:

| Config File | Database | Purpose |
|-------------|----------|---------|
| `database.conf` | default | Main CDR data |
| `database_cdrdb.conf` | cdrdb | CDR records |
| `database_cdrdb_ro.conf` | cdrdb (readonly) | CDR reads |
| `database_lcrdb_ro.conf` | lcrdb | LCR routing |
| `database_billing.conf` | billing | Billing data |
| `database_logs.conf` | logs | Application logs |

### Service Configuration

#### Distiller Configuration (`rmdistiller.conf`)
```ini
# Distiller service settings
distiller.listen_port = 10001
distiller.worker_threads = 8
distiller.queue_size = 1000

# Database connection
database.host = cdrdb.{hapi:SearchDomain}
database.user = cdrmunch
database.name = CDRs

# Cache settings
cache.dir = /var/spool/cdrtmp/cdrmunch-cache
cache.max_size_mb = 1024

# Logging
log.level = 4
log.file = syslog
```

#### Gateway Configuration (`rmcdrgateway.conf`)
```ini
# Gateway service settings
gateway.listen_socket = :80
gateway.worker_threads = 16
gateway.max_request_size_mb = 10

# Distiller connection
distiller.host = cdrmunch.{hapi:SearchDomain}
distiller.port = 10001

# Logging
log.file = syslog
log.level = 4
```

#### Hurler Configuration (`rmhurler.conf`)
```ini
# AWS S3 settings
s3.bucket = rm-call-analysis
s3.region = eu-west-1

# Task queue settings
queue.batch_size = 100
queue.poll_interval_ms = 1000

# Worker threads
worker.threads = 8
```

### Cron Services

#### Billing Feeder
```ini
# billing-feeder.conf
poll_interval = 60
batch_size = 100
billing_api_url = http://billing.internal/api
retry_count = 3
```

#### Task Executor
```ini
# task-executor.conf
poll_interval = 5
max_concurrent_tasks = 10
task_timeout = 300
estuary_cache_dir = /var/lib/cdrmunch-task-executor-estuary-cache
```

### Task Classes (PHP)

| Class | File | Description |
|-------|------|-------------|
| `BillingFeederTasks` | `class.BillingFeederTasks.php` | Billing record processing |
| `EmailRecordingTask` | `class.EmailRecordingTask.php` | Email call recordings |
| `NotifyVoicemailViaEmailTask` | `class.NotifyVoicemailViaEmailTask.php` | Voicemail email notifications |
| `NotifyVoicemailViaSMSTask` | `class.NotifyVoicemailViaSMSTask.php` | Voicemail SMS notifications |
| `SendSMSTask` | `class.SendSMSTask.php` | SMS sending |
| `CallLogsJSONExportTask` | `class.CallLogsJSONExportTask.php` | Call log export |
| `LogActivityTask` | `class.LogActivityTask.php` | Activity logging |

### SMS Providers

The task executor supports multiple SMS providers:

| Provider | Class | Description |
|----------|-------|-------------|
| TextMarketer | `TextMarketerSmsProvider` | TextMarketer API |
| MessageBird | `MessageBirdSmsProvider` | MessageBird API |
| Bandwidth | `BandwidthSmsProvider` | Bandwidth API |
| AutoSelect | `AutoSelectSmsProvider` | Automatic provider selection |

### Deployment (RPM Packages)

CDRMunch is deployed as multiple RPM packages:

| Package | Contents |
|---------|----------|
| `RM-cdrmunch` | Distiller daemon |
| `RM-cdrmunch-gateway` | HTTP gateway |
| `RM-cdrmunch-cron` | Cron scripts |
| `RM-cdrmunch-phplib` | PHP libraries |
| `RM-cdrmunch-common` | Common files |
| `RM-cdrmunch-hurler` | AWS hurler |
| `RM-cdrmunch-scripts` | Utility scripts |

### Systemd Services

```
rmdistiller.service      # CDR Distiller
rmcdrgateway.service     # CDR Gateway
rmhurler.service         # AWS Hurler
cdrmunch-billing-feeder.service
cdrmunch-emailer.service
cdrmunch-task-executor.service
rmtaskexslow.service
```

---

## 4. Platform-Archiving

### Repository Information

| Field | Value |
|-------|-------|
| **Repository** | `redmatter/platform-archiving` |
| **Primary Language** | C++ |
| **Database** | MySQL/MariaDB |
| **Storage** | AWS S3 |
| **Deployment** | RPM packages |

### Tech Stack

- **Language**: C++ (GCC 4.4)
- **Libraries**: Boost, MySQL++, libs3
- **Storage**: AWS S3 via libs3
- **Protocol**: FastCGI for HTTP interface

### Component Overview

| Component | Type | Description |
|-----------|------|-------------|
| `rmarchived` | C++ Daemon | Main archiving service |
| `rmestuary` | C++ Daemon | Estuary data retrieval |

### Directory Structure

```
platform-archiving/
├── archived/
│   ├── rmarchived.conf      # Archive daemon config
│   ├── rmarchived.service   # Systemd service
│   └── src/                 # C++ source
├── estuary/
│   ├── rmestuary.conf       # Estuary daemon config
│   ├── rmestuary.service    # Systemd service
│   └── src/                 # C++ source
├── common/                  # Shared code
└── RM-archiving.spec        # RPM spec
```

### Archived Service Configuration

**`rmarchived.conf`**:
```ini
# Process settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch
app.work_dir = /var/lib/archiving
app.max_core_size_mega_bytes = 1024
app.max_file_handles = 4096
app.niceness = 10

# Service threads
archived.service_threads = 64
converter.threads = 8

# Queue settings
archived.queue_combined_watermark = 1500

# Call buffering
call_buffering.base_dir = /mnt/rmfs/call-buffering

# S3 Backend
s3_backend.ssl_enabled = true
s3_runner.threads = 24

# CoreAPI Integration
coreapi.url = http://cdr.coreapi.{hapi:SearchDomain}
coreapi.auth_creds = <base64_encoded_credentials>

# Distiller Integration
distiller_client.server_port = 10001
distiller_client.server_host = cdrmunch.{hapi:SearchDomain}

# FastCGI Server
fcgi_server.listen_socket = :10101
fcgi_server.listen_queue_depth = 100
fcgi_server.handler_threads = 8

# Ports
archived.put_port = 10100

# Cache directories
archived.cache_dir = /var/lib/archiving/cache
clear_cache.base_directory = /var/lib/archiving/archived/clear-cache
distiller_client.base_dir = /var/spool/cdrtmp/cdrmunch-cache

# Logging
log.file_path = syslog
log.level = 4
```

### Estuary Service Configuration

**`rmestuary.conf`**:
```ini
# Process settings
app.run_as_user = cdrmunch
app.run_as_group = cdrmunch
app.work_dir = /var/lib/archiving

# FastCGI Server
fcgi_server.listen_socket = :10102
fcgi_server.handler_threads = 4

# S3 Settings
s3_backend.ssl_enabled = true

# Cache
estuary.cache_dir = /var/lib/archiving/estuary-cache

# Logging
log.file_path = syslog
log.level = 4
```

### Storage Architecture

```
┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  FreeSWITCH  │────▶│  rmarchived │────▶│   AWS S3    │
│  Call Files  │     │   Daemon    │     │   Bucket    │
└──────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                     ┌─────────────┐
                     │   CoreAPI   │
                     │  (Metadata) │
                     └─────────────┘
```

### Features

1. **Call Recording Archiving**: Archives call recordings to S3
2. **AES Encryption**: Optional AES encryption for recordings
3. **Retention Management**: Manages recording retention policies
4. **Clear Cache**: Maintains local cache of unencrypted recordings
5. **Watermark Protection**: Queue watermarking to prevent overload

### Environment-Specific Settings

| Setting | Dev | QA | Production |
|---------|-----|----|-----------| 
| `archived.queue_combined_watermark` | 100 | 100 | 1500 |
| `s3_runner.threads` | 2 | 2 | 24 |
| `log.level` | 6 | 6 | 4 |
| `debug.disable_restart` | true | true | false |

---

## 5. Inter-Service Communication Patterns

### Service Communication Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    Service Communication                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    HTTP/REST    ┌────────────┐                   │
│  │  Sapien  │◄───────────────▶│  Core-API  │                   │
│  └────┬─────┘                 └─────┬──────┘                   │
│       │                             │                           │
│       │ RabbitMQ                    │ MySQL                     │
│       ▼                             ▼                           │
│  ┌──────────┐                 ┌────────────┐                   │
│  │    MQ    │                 │  Database  │                   │
│  └────┬─────┘                 └─────┬──────┘                   │
│       │                             │                           │
│       │ AMQP                        │ MySQL                     │
│       ▼                             ▼                           │
│  ┌──────────┐    TCP:10001   ┌────────────┐                   │
│  │ CDRMunch │◄──────────────▶│ Archiving  │                   │
│  └──────────┘                └────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Communication Protocols

| From | To | Protocol | Port |
|------|-----|----------|------|
| Sapien | Core-API | HTTP/REST | 80/443 |
| Sapien | Database | MySQL | 3306 |
| Sapien | RabbitMQ | AMQP | 5672 |
| Sapien | S3/MinIO | HTTP | 80 |
| CDRMunch Gateway | Distiller | TCP | 10001 |
| CDRMunch | Database | MySQL | 3306 |
| CDRMunch | Archiving | TCP | 10100 |
| Archiving | S3 | HTTPS | 443 |
| Archiving | Core-API | HTTP | 80 |
| Archiving | Distiller | TCP | 10001 |

### Event Flow Examples

#### Call Recording Flow
```
1. Call ends on FreeSWITCH
2. Recording file written to call-buffering directory
3. rmarchived picks up the file
4. rmarchived uploads to S3
5. rmarchived notifies Core-API of recording availability
6. Core-API updates CDR record
7. Sapien receives webhook/event
8. User can access recording via Sapien API
```

#### CDR Processing Flow
```
1. CDR received by rmcdrgateway (HTTP)
2. Gateway forwards to rmdistiller (TCP)
3. Distiller normalizes CDR using XQuery
4. Distiller writes to database
5. Task executor picks up tasks
6. Billing feeder sends to billing system
7. Emailer sends notifications
```

---

## 6. Shared Database Infrastructure

### Database Servers

| Alias | Purpose | Connection Type |
|-------|---------|-----------------|
| `core-sql-rw` | Core databases (read-write) | Primary |
| `core-sql-ro` | Core databases (read-only) | Replica |
| `big-sql-rw` | Large data (CDRs, logs) (read-write) | Primary |
| `big-sql-ro` | Large data (read-only) | Replica |

### Database Schema Overview

#### API Database
| Table | Description |
|-------|-------------|
| `users` | User accounts |
| `organisations` | Organizations |
| `extensions` | Phone extensions |
| `dids` | DID numbers |
| `queues` | Call queues |
| `ivrs` | IVR configurations |
| `oauth_clients` | OAuth clients |
| `oauth_access_tokens` | Access tokens |

#### CDR Database
| Table | Description |
|-------|-------------|
| `cdrs` | Call detail records |
| `cdr_legs` | Individual call legs |
| `recordings` | Recording metadata |
| `voicemails` | Voicemail records |

#### Billing Database
| Table | Description |
|-------|-------------|
| `billing_records` | Billing entries |
| `invoices` | Generated invoices |
| `rates` | Call rates |

### Database Migration Management

Database schemas are managed through:
- `dbmigrate` tool for schema versioning
- RPM packages for schema distribution
- Migration scripts in respective schema repositories

---

## Quick Reference: Service Ports

| Service | Port | Protocol |
|---------|------|----------|
| Sapien Front-End | 80 | HTTP |
| Sapien Core | - | Internal |
| Core-API | 80 | HTTP |
| RabbitMQ | 5672 | AMQP |
| RabbitMQ Management | 15672 | HTTP |
| MySQL/MariaDB | 3306 | MySQL |
| MinIO/S3 | 80 | HTTP |
| CDR Gateway | 80 | HTTP |
| Distiller | 10001 | TCP |
| Archived PUT | 10100 | TCP |
| Archived FCGI | 10101 | FastCGI |
| Estuary FCGI | 10102 | FastCGI |
| ESL Listener | 4444 | TCP |

---

## Related Documentation

- [Database Schema Reference](../database/schema-reference.md)
- [Message Queue Patterns](../integration/message-queues.md)
- [Deployment Guide](../operations/deployment-guide.md)
- [Monitoring & Alerting](../operations/monitoring.md)
