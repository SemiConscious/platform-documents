# Platform-Sapien (Public API)

> **Last Updated**: 2026-01-20  
> **Repository**: [redmatter/platform-sapien](https://github.com/redmatter/platform-sapien)  
> **Infrastructure**: [redmatter/aws-terraform-sapien-proxy](https://github.com/redmatter/aws-terraform-sapien-proxy)  
> **Language**: PHP 7.4+ (Symfony 3)  
> **Status**: Production - Primary Public API

## Overview

Platform-Sapien is the **public-facing REST API** for the Natterbox platform. It provides external access to platform functionality through a well-defined API exposed via AWS API Gateway. Unlike Platform-API (CoreAPI) which serves internal systems, Sapien is designed for external consumers including:

- Third-party integrations
- Customer-built applications
- Mobile applications
- Partner systems

### Key Responsibilities

- **Public API Gateway**: Exposes platform functionality through AWS API Gateway
- **Authentication**: Auth0 OAuth2/JWT-based authentication and authorization
- **User Management**: User CRUD operations, permissions, and profile management
- **Call Analytics**: Access to call data, recordings, and analytics
- **Organization Management**: Organization settings and configuration
- **Blob Storage**: File upload/download for recordings, voicemails, assets
- **Recording Archiving**: Archive policy management and recording retrieval
- **Health Monitoring**: Comprehensive health check endpoints

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         External API Architecture                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │   Partner    │   │   Mobile     │   │   Customer   │   │   Internal   │     │
│  │   Systems    │   │     Apps     │   │   Integrations   │   Systems    │     │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘     │
│         │                  │                  │                  │             │
│         └──────────────────┴────────┬─────────┴──────────────────┘             │
│                                     │                                           │
│                                     ▼                                           │
│         ┌─────────────────────────────────────────────────────────┐             │
│         │                  AWS API Gateway                         │             │
│         │      (sapien.natterbox.com / sapien-{region}.nb)        │             │
│         │  ┌─────────────────────────────────────────────────┐    │             │
│         │  │  • Rate limiting (100 req/sec default)          │    │             │
│         │  │  • Request validation                           │    │             │
│         │  │  • CORS handling                                │    │             │
│         │  │  • CloudWatch logging                           │    │             │
│         │  └─────────────────────────────────────────────────┘    │             │
│         └──────────────────────────┬──────────────────────────────┘             │
│                                    │                                            │
│                                    ▼                                            │
│         ┌─────────────────────────────────────────────────────────┐             │
│         │                   Platform-Sapien                        │             │
│         │                  (Symfony 3 PHP)                         │             │
│         │  ┌─────────────────────────────────────────────────────┐ │             │
│         │  │                   Bundles                            │ │             │
│         │  │  • SapienBundle      - Core API functionality       │ │             │
│         │  │  • UserBundle        - User & org management        │ │             │
│         │  │  • ArchivingBundle   - Recording archiving          │ │             │
│         │  │  • BlobStorageBundle - File storage                 │ │             │
│         │  │  • HelloBundle       - Health checks                │ │             │
│         │  │  • FreeswitchBundle  - FS integration               │ │             │
│         │  └─────────────────────────────────────────────────────┘ │             │
│         └──────────────────────────┬──────────────────────────────┘             │
│                                    │                                            │
│         ┌──────────────────────────┼──────────────────────────────┐             │
│         │                          │                              │             │
│         ▼                          ▼                              ▼             │
│  ┌──────────────┐         ┌──────────────┐              ┌──────────────┐        │
│  │   Auth0      │         │  Platform-API │              │   S3/Blob    │        │
│  │  (OAuth2)    │         │   (CoreAPI)   │              │   Storage    │        │
│  └──────────────┘         └──────────────┘              └──────────────┘        │
│                                    │                                            │
│                                    ▼                                            │
│  ┌──────────────┐         ┌──────────────┐              ┌──────────────┐        │
│  │   OrgDB      │         │    BigDB     │              │  FreeSWITCH  │        │
│  │  (MySQL)     │         │   (CDR)      │              │   Servers    │        │
│  └──────────────┘         └──────────────┘              └──────────────┘        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
platform-sapien/
├── core/
│   ├── Dockerfile                      # Production container
│   └── project/
│       ├── app/
│       │   ├── AppKernel.php           # Symfony kernel
│       │   └── config/
│       │       ├── config.yml          # Main Symfony config
│       │       ├── config_dev.yml      # Development overrides
│       │       ├── config_prod.yml     # Production overrides
│       │       ├── config_test.yml     # Test environment
│       │       ├── parameters.yml.dist # Parameter template
│       │       ├── parameters_local.yml # Local development
│       │       ├── routing.yml         # Route definitions
│       │       ├── security.yml        # Auth configuration
│       │       └── services.yml        # Service definitions
│       ├── src/
│       │   └── Redmatter/
│       │       ├── SapienBundle/       # Core API bundle
│       │       │   ├── Controller/     # API controllers
│       │       │   ├── Entity/         # Doctrine entities
│       │       │   ├── Repository/     # Data repositories
│       │       │   ├── Service/        # Business logic
│       │       │   ├── DependencyInjection/
│       │       │   └── Resources/config/
│       │       ├── UserBundle/         # User management
│       │       │   ├── Controller/     # User API endpoints
│       │       │   ├── Entity/         # User/Org entities
│       │       │   ├── Repository/
│       │       │   ├── Service/
│       │       │   └── Resources/config/
│       │       ├── ArchivingBundle/    # Recording archiving
│       │       ├── BlobStorageBundle/  # File storage
│       │       ├── HelloBundle/        # Health checks
│       │       └── FreeswitchBundle/   # FS integration
│       ├── composer.json               # PHP dependencies
│       └── composer.lock
├── sapien/                             # Additional sapien modules
├── docker-compose.yml                  # Local development
├── .env                                # Environment config
└── README.md
```

## Symfony Bundles

### SapienBundle (Core)

The main bundle providing core API functionality:

| Directory | Purpose |
|-----------|---------|
| `Controller/` | API endpoint handlers |
| `Entity/` | CallAnalytic, ArchivePolicy, ArchiveRecording, Blob, etc. |
| `Repository/` | Database queries and data access |
| `Service/` | Business logic services |
| `GraphQL/` | GraphQL schema and resolvers |
| `EventListener/` | Event handlers |
| `Command/` | Console commands |

### UserBundle

Comprehensive user and organization management:

| Controller | Description |
|------------|-------------|
| `AvailabilityController` | User availability/presence |
| `CallController` | Call history and records |
| `CallgroupController` | Call group management |
| `ContactController` | Contact management |
| `DialplanController` | Dialplan configuration |
| `DirectoryController` | Organization directory |
| `IntegrationController` | Third-party integrations |
| `OrganizationController` | Organization settings |
| `PermissionController` | Permission management |
| `ProfileController` | User profile operations |
| `QueueController` | Call queue management |
| `RecordingController` | Recording access |
| `UserController` | User CRUD operations |
| `VoicemailController` | Voicemail management |

### ArchivingBundle

Recording archiving and retention:

| Controller | Description |
|------------|-------------|
| `ArchivePolicyController` | Archive policy CRUD |
| `ArchiveRecordingController` | Recording archive operations |
| `ArchiverController` | Archive processing |

### BlobStorageBundle

File and blob storage management:

| Controller | Description |
|------------|-------------|
| `BlobController` | File upload/download |
| `StorageController` | Storage management |

### HelloBundle

Health and status endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /hello` | Basic health check |
| `GET /v1/hello` | API v1 health check |
| `GET /v1/hello/database` | Database connectivity check |
| `GET /v1/hello/memcache` | Memcache connectivity check |
| `GET /v1/hello/redis` | Redis connectivity check |
| `GET /v1/hello/dgapi` | Data Gateway API check |
| `GET /v1/hello/coreapi` | CoreAPI connectivity check |
| `GET /v1/hello/s3` | S3 storage check |
| `GET /v1/hello/sse` | Server-Sent Events check |
| `GET /v1/hello/all` | Comprehensive health check |

## API Endpoints

### Authentication

Sapien uses Auth0 for OAuth2/JWT authentication:

```
# OAuth2 Token Request
POST /oauth/token
Content-Type: application/json

{
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "audience": "https://sapien.natterbox.com",
  "grant_type": "client_credentials"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### User Management (`/v1/users`)

```yaml
# List users
GET /v1/users
Authorization: Bearer <token>
Query Parameters:
  - limit: int (default: 20, max: 100)
  - offset: int (default: 0)
  - search: string (search by name/email)
  - status: string (active|inactive|all)
Response: 200 OK
{
  "users": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}

# Get user by ID
GET /v1/users/{id}
Authorization: Bearer <token>
Response: 200 OK
{
  "id": 12345,
  "username": "john.doe",
  "email": "john.doe@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "organization": {...},
  "permissions": [...],
  "devices": [...],
  "createdAt": "2024-01-15T10:30:00Z"
}

# Create user
POST /v1/users
Authorization: Bearer <token>
Content-Type: application/json
{
  "username": "jane.smith",
  "email": "jane.smith@example.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "password": "SecurePassword123!",
  "organizationId": 100,
  "roles": ["user"]
}
Response: 201 Created
{
  "id": 12346,
  "username": "jane.smith",
  ...
}

# Update user
PUT /v1/users/{id}
Authorization: Bearer <token>
Content-Type: application/json
{
  "email": "jane.new@example.com",
  "firstName": "Janet"
}
Response: 200 OK

# Delete user
DELETE /v1/users/{id}
Authorization: Bearer <token>
Response: 204 No Content
```

### Organizations (`/v1/organizations`)

```yaml
# List organizations
GET /v1/organizations
Authorization: Bearer <token>
Response: 200 OK
{
  "organizations": [
    {
      "id": 100,
      "name": "Acme Corporation",
      "domain": "acme.natterbox.com",
      "status": "active",
      "settings": {...}
    }
  ]
}

# Get organization
GET /v1/organizations/{id}
Authorization: Bearer <token>
Response: 200 OK

# Update organization settings
PUT /v1/organizations/{id}/settings
Authorization: Bearer <token>
Content-Type: application/json
{
  "voicemailEnabled": true,
  "recordingEnabled": true,
  "maxRecordingDays": 90
}
Response: 200 OK
```

### Calls & Analytics (`/v1/calls`)

```yaml
# List calls
GET /v1/calls
Authorization: Bearer <token>
Query Parameters:
  - from: datetime (ISO 8601)
  - to: datetime (ISO 8601)
  - userId: int
  - direction: string (inbound|outbound|internal)
  - limit: int
  - offset: int
Response: 200 OK
{
  "calls": [
    {
      "id": "call-uuid-123",
      "direction": "inbound",
      "from": "+441onal234567",
      "to": "+441onal987654",
      "startTime": "2025-01-20T14:30:00Z",
      "endTime": "2025-01-20T14:35:00Z",
      "duration": 300,
      "status": "completed",
      "recording": {...}
    }
  ],
  "total": 1500,
  "limit": 20,
  "offset": 0
}

# Get call details
GET /v1/calls/{id}
Authorization: Bearer <token>
Response: 200 OK
{
  "id": "call-uuid-123",
  "legs": [...],
  "events": [...],
  "recording": {...}
}
```

### Recordings (`/v1/recordings`)

```yaml
# List recordings
GET /v1/recordings
Authorization: Bearer <token>
Query Parameters:
  - from: datetime
  - to: datetime
  - userId: int
  - callId: string
Response: 200 OK
{
  "recordings": [
    {
      "id": "rec-uuid-123",
      "callId": "call-uuid-123",
      "duration": 300,
      "size": 2457600,
      "format": "wav",
      "url": "https://...",
      "createdAt": "2025-01-20T14:35:00Z"
    }
  ]
}

# Download recording
GET /v1/recordings/{id}/download
Authorization: Bearer <token>
Response: 302 Redirect to signed S3 URL

# Delete recording
DELETE /v1/recordings/{id}
Authorization: Bearer <token>
Response: 204 No Content
```

### Archive Policies (`/v1/archive-policies`)

```yaml
# List archive policies
GET /v1/archive-policies
Authorization: Bearer <token>
Response: 200 OK
{
  "policies": [
    {
      "id": 1,
      "name": "90-day retention",
      "retentionDays": 90,
      "archiveDestination": "s3",
      "organizationId": 100
    }
  ]
}

# Create archive policy
POST /v1/archive-policies
Authorization: Bearer <token>
Content-Type: application/json
{
  "name": "Compliance Archive",
  "retentionDays": 365,
  "archiveDestination": "glacier",
  "organizationId": 100
}
Response: 201 Created
```

### Blob Storage (`/v1/blobs`)

```yaml
# Upload blob
POST /v1/blobs
Authorization: Bearer <token>
Content-Type: multipart/form-data
Form Fields:
  - file: binary
  - type: string (recording|voicemail|asset)
  - metadata: json
Response: 201 Created
{
  "id": "blob-uuid-123",
  "filename": "recording.wav",
  "size": 2457600,
  "mimeType": "audio/wav",
  "url": "https://..."
}

# Download blob
GET /v1/blobs/{id}
Authorization: Bearer <token>
Response: 200 OK (binary) or 302 Redirect

# Delete blob
DELETE /v1/blobs/{id}
Authorization: Bearer <token>
Response: 204 No Content
```

### Availability (`/v1/availability`)

```yaml
# Get user availability
GET /v1/users/{id}/availability
Authorization: Bearer <token>
Response: 200 OK
{
  "userId": 12345,
  "status": "available",
  "statusMessage": "In office",
  "dndEnabled": false,
  "forwardingEnabled": false,
  "forwardingNumber": null
}

# Update availability
PUT /v1/users/{id}/availability
Authorization: Bearer <token>
Content-Type: application/json
{
  "status": "busy",
  "statusMessage": "In meeting",
  "dndEnabled": true
}
Response: 200 OK
```

### Voicemail (`/v1/voicemail`)

```yaml
# List voicemails
GET /v1/voicemail
Authorization: Bearer <token>
Query Parameters:
  - userId: int
  - status: string (new|read|all)
Response: 200 OK
{
  "voicemails": [
    {
      "id": "vm-uuid-123",
      "from": "+44123456789",
      "duration": 45,
      "status": "new",
      "transcription": "Hi, this is...",
      "createdAt": "2025-01-20T09:00:00Z"
    }
  ]
}

# Mark as read
PUT /v1/voicemail/{id}/read
Authorization: Bearer <token>
Response: 200 OK

# Download voicemail
GET /v1/voicemail/{id}/download
Authorization: Bearer <token>
Response: 302 Redirect
```

## Configuration Reference

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | MySQL connection string | - |
| `DGAPI_URL` | Yes | Data Gateway API URL | - |
| `COREAPI_URL` | Yes | Platform-API URL | - |
| `AUTH0_DOMAIN` | Yes | Auth0 tenant domain | - |
| `AUTH0_CLIENT_ID` | Yes | Auth0 client ID | - |
| `AUTH0_CLIENT_SECRET` | Yes | Auth0 client secret | - |
| `AUTH0_AUDIENCE` | Yes | Auth0 API audience | - |
| `S3_BUCKET` | Yes | S3 bucket for blob storage | - |
| `S3_REGION` | Yes | AWS region | `eu-west-1` |
| `MEMCACHED_HOST` | No | Memcached host | `localhost` |
| `MEMCACHED_PORT` | No | Memcached port | `11211` |
| `REDIS_HOST` | No | Redis host | `localhost` |
| `REDIS_PORT` | No | Redis port | `6379` |
| `LOG_LEVEL` | No | Logging level | `warning` |
| `TRUSTED_PROXIES` | No | Trusted proxy IPs | - |
| `CORS_ALLOW_ORIGIN` | No | CORS allowed origins | `*` |

### Symfony Configuration (`config.yml`)

```yaml
# From core/project/app/config/config.yml
imports:
    - { resource: parameters.yml }
    - { resource: security.yml }
    - { resource: services.yml }

framework:
    secret: '%secret%'
    router:
        resource: '%kernel.project_dir%/app/config/routing.yml'
        strict_requirements: ~
    form: ~
    csrf_protection: ~
    validation: { enable_annotations: true }
    serializer: { enable_annotations: true }
    templating:
        engines: ['twig']
    default_locale: '%locale%'
    trusted_hosts: ~
    session:
        handler_id: session.handler.native_file
        save_path: '%kernel.project_dir%/var/sessions/%kernel.environment%'
    fragments: ~
    http_method_override: true
    assets: ~
    php_errors:
        log: true

# Doctrine Configuration
doctrine:
    dbal:
        driver: pdo_mysql
        host: '%database_host%'
        port: '%database_port%'
        dbname: '%database_name%'
        user: '%database_user%'
        password: '%database_password%'
        charset: UTF8
    orm:
        auto_generate_proxy_classes: '%kernel.debug%'
        naming_strategy: doctrine.orm.naming_strategy.underscore
        auto_mapping: true

# Nelmio CORS Configuration
nelmio_cors:
    defaults:
        origin_regex: true
        allow_origin: ['%cors_allow_origin%']
        allow_methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        allow_headers: ['Content-Type', 'Authorization']
        expose_headers: ['Link']
        max_age: 3600
    paths:
        '^/v1/':
            allow_origin: ['*']
            allow_headers: ['*']
            allow_methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
            max_age: 3600
```

### Security Configuration (`security.yml`)

```yaml
# From core/project/app/config/security.yml
security:
    providers:
        jwt_user_provider:
            id: redmatter_sapien.jwt_user_provider

    firewalls:
        dev:
            pattern: ^/(_(profiler|wdt)|css|images|js)/
            security: false

        hello:
            pattern: ^/hello
            security: false

        v1_hello:
            pattern: ^/v1/hello
            security: false

        oauth:
            pattern: ^/oauth
            security: false

        main:
            pattern: ^/
            stateless: true
            guard:
                authenticators:
                    - redmatter_sapien.jwt_authenticator
            provider: jwt_user_provider

    access_control:
        - { path: ^/hello, roles: IS_AUTHENTICATED_ANONYMOUSLY }
        - { path: ^/v1/hello, roles: IS_AUTHENTICATED_ANONYMOUSLY }
        - { path: ^/oauth, roles: IS_AUTHENTICATED_ANONYMOUSLY }
        - { path: ^/, roles: IS_AUTHENTICATED_FULLY }
```

## AWS API Gateway Infrastructure

Sapien is fronted by AWS API Gateway, managed via Terraform:

### API Gateway Configuration

```hcl
# From aws-terraform-sapien-proxy/api-gateway.tf
resource "aws_api_gateway_rest_api" "sapien" {
  name        = "sapien-api-${var.environment}"
  description = "Sapien Public API Gateway"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  body = templatefile("${path.module}/sapien.openapi30.yaml", {
    sapien_backend_url = var.sapien_backend_url
    aws_region         = var.aws_region
  })
}

resource "aws_api_gateway_deployment" "sapien" {
  rest_api_id = aws_api_gateway_rest_api.sapien.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.sapien.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "sapien" {
  deployment_id = aws_api_gateway_deployment.sapien.id
  rest_api_id   = aws_api_gateway_rest_api.sapien.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.sapien_api_gateway.arn
    format = jsonencode({
      requestId         = "$context.requestId"
      ip                = "$context.identity.sourceIp"
      caller            = "$context.identity.caller"
      user              = "$context.identity.user"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      resourcePath      = "$context.resourcePath"
      status            = "$context.status"
      protocol          = "$context.protocol"
      responseLength    = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
    })
  }
}
```

### Terraform Variables

```hcl
# From aws-terraform-sapien-proxy/variables.tf
variable "environment" {
  description = "Environment name (production, staging, etc.)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "sapien_backend_url" {
  description = "Backend URL for Sapien service"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name for API"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  type        = string
  default     = ""
}

variable "rate_limit" {
  description = "API Gateway rate limit (requests per second)"
  type        = number
  default     = 100
}

variable "burst_limit" {
  description = "API Gateway burst limit"
  type        = number
  default     = 200
}

variable "throttling_enabled" {
  description = "Enable API throttling"
  type        = bool
  default     = true
}

variable "logging_level" {
  description = "API Gateway logging level"
  type        = string
  default     = "INFO"
}

variable "xray_tracing_enabled" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

### OpenAPI Specification (Excerpt)

```yaml
# From aws-terraform-sapien-proxy/sapien.openapi30.yaml
openapi: 3.0.1
info:
  title: Sapien API
  description: Natterbox Public API
  version: 1.0.0

servers:
  - url: https://sapien.natterbox.com/v1
    description: Production

paths:
  /hello:
    get:
      summary: Health check
      operationId: hello
      responses:
        '200':
          description: OK
      x-amazon-apigateway-integration:
        uri: ${sapien_backend_url}/hello
        httpMethod: GET
        type: http_proxy

  /users:
    get:
      summary: List users
      operationId: listUsers
      security:
        - bearerAuth: []
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: User list
        '401':
          description: Unauthorized
      x-amazon-apigateway-integration:
        uri: ${sapien_backend_url}/v1/users
        httpMethod: GET
        type: http_proxy

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Docker Configuration

### Dockerfile

```dockerfile
# From core/Dockerfile
FROM php:7.4-apache

# Install dependencies
RUN apt-get update && apt-get install -y \
    libicu-dev \
    libpq-dev \
    libmcrypt-dev \
    libmemcached-dev \
    zlib1g-dev \
    git \
    unzip \
    && docker-php-ext-install \
    intl \
    opcache \
    pdo \
    pdo_mysql \
    && pecl install memcached \
    && docker-php-ext-enable memcached

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Configure Apache
RUN a2enmod rewrite
COPY apache.conf /etc/apache2/sites-available/000-default.conf

# Copy application
WORKDIR /var/www/html
COPY core/project/ .

# Install dependencies
RUN composer install --no-dev --optimize-autoloader

# Set permissions
RUN chown -R www-data:www-data /var/www/html/var

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/hello || exit 1

EXPOSE 80

CMD ["apache2-foreground"]
```

### Docker Compose (Development)

```yaml
# From docker-compose.yml
version: '3.8'

services:
  sapien:
    build:
      context: .
      dockerfile: core/Dockerfile
    ports:
      - "8081:80"
    environment:
      - DATABASE_URL=mysql://sapien:password@mysql:3306/sapien
      - DGAPI_URL=http://dgapi:8080
      - COREAPI_URL=http://coreapi:8080
      - AUTH0_DOMAIN=${AUTH0_DOMAIN}
      - AUTH0_CLIENT_ID=${AUTH0_CLIENT_ID}
      - AUTH0_CLIENT_SECRET=${AUTH0_CLIENT_SECRET}
      - AUTH0_AUDIENCE=${AUTH0_AUDIENCE}
      - S3_BUCKET=sapien-dev-blobs
      - S3_REGION=eu-west-1
      - MEMCACHED_HOST=memcached
      - REDIS_HOST=redis
      - LOG_LEVEL=debug
    depends_on:
      - mysql
      - memcached
      - redis
    volumes:
      - ./core/project:/var/www/html
    networks:
      - sapien-network

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: sapien
      MYSQL_USER: sapien
      MYSQL_PASSWORD: password
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - sapien-network

  memcached:
    image: memcached:1.6
    ports:
      - "11212:11211"
    networks:
      - sapien-network

  redis:
    image: redis:6
    ports:
      - "6380:6379"
    networks:
      - sapien-network

  dgapi:
    image: redmatter/dgapi:latest
    environment:
      - DATABASE_URL=mysql://dgapi:password@mysql:3306/dgapi
    networks:
      - sapien-network

  coreapi:
    image: redmatter/coreapi:latest
    environment:
      - ORGDB_HOST=mysql
      - ORGDB_NAME=natterbox_org
    networks:
      - sapien-network

networks:
  sapien-network:
    driver: bridge

volumes:
  mysql_data:
```

## Data Models

### User Entity

```php
// From core/project/src/Redmatter/UserBundle/Entity/User.php
/**
 * @ORM\Entity(repositoryClass="Redmatter\UserBundle\Repository\UserRepository")
 * @ORM\Table(name="users")
 */
class User implements UserInterface
{
    /**
     * @ORM\Id
     * @ORM\GeneratedValue
     * @ORM\Column(type="integer")
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=180, unique=true)
     */
    private $username;

    /**
     * @ORM\Column(type="string", length=255, unique=true)
     */
    private $email;

    /**
     * @ORM\Column(type="string", length=255)
     */
    private $firstName;

    /**
     * @ORM\Column(type="string", length=255)
     */
    private $lastName;

    /**
     * @ORM\Column(type="json")
     */
    private $roles = [];

    /**
     * @ORM\Column(type="string", nullable=true)
     */
    private $password;

    /**
     * @ORM\ManyToOne(targetEntity="Organization", inversedBy="users")
     * @ORM\JoinColumn(nullable=false)
     */
    private $organization;

    /**
     * @ORM\Column(type="string", length=50)
     */
    private $status = 'active';

    /**
     * @ORM\Column(type="datetime")
     */
    private $createdAt;

    /**
     * @ORM\Column(type="datetime", nullable=true)
     */
    private $lastLoginAt;

    // ... getters and setters
}
```

### CallAnalytic Entity

```php
// Inferred from SapienBundle/Entity structure
/**
 * @ORM\Entity(repositoryClass="Redmatter\SapienBundle\Repository\CallAnalyticRepository")
 * @ORM\Table(name="call_analytics")
 */
class CallAnalytic
{
    /**
     * @ORM\Id
     * @ORM\Column(type="string", length=36)
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=20)
     */
    private $direction;

    /**
     * @ORM\Column(type="string", length=50)
     */
    private $fromNumber;

    /**
     * @ORM\Column(type="string", length=50)
     */
    private $toNumber;

    /**
     * @ORM\Column(type="datetime")
     */
    private $startTime;

    /**
     * @ORM\Column(type="datetime", nullable=true)
     */
    private $endTime;

    /**
     * @ORM\Column(type="integer")
     */
    private $duration;

    /**
     * @ORM\Column(type="string", length=50)
     */
    private $status;

    /**
     * @ORM\ManyToOne(targetEntity="Redmatter\UserBundle\Entity\User")
     */
    private $user;

    /**
     * @ORM\ManyToOne(targetEntity="Redmatter\UserBundle\Entity\Organization")
     */
    private $organization;

    // ... getters and setters
}
```

## Caching Strategy

Sapien uses multi-layer caching:

### Cache Layers

| Layer | Technology | TTL | Use Case |
|-------|------------|-----|----------|
| L1 | OPcache | - | PHP bytecode |
| L2 | Memcached | 5-60min | Session, user data |
| L3 | Redis | 1-24hr | API responses, tokens |

### Cache Key Patterns

| Pattern | TTL | Description |
|---------|-----|-------------|
| `user:{id}` | 5min | User profile data |
| `org:{id}` | 10min | Organization settings |
| `token:{hash}` | 24hr | JWT token validation |
| `calls:{org}:{date}` | 1hr | Call analytics cache |
| `recording:{id}` | 30min | Recording metadata |

## Operational Procedures

### Deployment

```bash
# Build and push Docker image
docker build -t redmatter/sapien:latest -f core/Dockerfile .
docker push redmatter/sapien:latest

# Deploy to Kubernetes
kubectl set image deployment/sapien sapien=redmatter/sapien:latest -n production

# Verify deployment
kubectl rollout status deployment/sapien -n production
```

### Health Checks

```bash
# Basic health check
curl https://sapien.natterbox.com/hello
# Response: {"status":"ok","timestamp":"2025-01-20T10:00:00Z"}

# Comprehensive health check
curl https://sapien.natterbox.com/v1/hello/all
# Response: {"database":"ok","memcache":"ok","redis":"ok","dgapi":"ok","coreapi":"ok","s3":"ok"}

# Individual component checks
curl https://sapien.natterbox.com/v1/hello/database
curl https://sapien.natterbox.com/v1/hello/memcache
curl https://sapien.natterbox.com/v1/hello/redis
```

### Log Analysis

```bash
# View Sapien logs (Kubernetes)
kubectl logs -f deployment/sapien -n production

# Filter for errors
kubectl logs deployment/sapien -n production | grep -i error

# Search by request ID
kubectl logs deployment/sapien -n production | grep "request_id=abc123"

# CloudWatch Logs (API Gateway)
aws logs filter-log-events \
  --log-group-name /aws/api-gateway/sapien \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000)
```

### Cache Management

```bash
# Clear all caches
curl -X POST https://sapien.natterbox.com/admin/cache/clear \
  -H "Authorization: Bearer <admin_token>"

# Clear specific cache
curl -X POST https://sapien.natterbox.com/admin/cache/clear \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"type": "user", "id": 12345}'

# View cache stats
echo "stats" | nc memcached.internal 11211
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures (401 Unauthorized)

**Symptom**: API calls returning 401

**Diagnosis**:
```bash
# Verify token is valid
curl https://<auth0-domain>/userinfo \
  -H "Authorization: Bearer <token>"

# Check token expiration
echo <token> | cut -d'.' -f2 | base64 -d | jq '.exp'
```

**Resolution**:
- Refresh token if expired
- Verify Auth0 configuration
- Check audience matches API configuration

#### 2. Database Connection Errors

**Symptom**: 500 errors with database messages

**Diagnosis**:
```bash
# Test database connectivity from container
kubectl exec -it deployment/sapien -n production -- \
  php -r "new PDO('mysql:host=mysql;dbname=sapien', 'user', 'pass');"

# Check connection count
mysql -e "SHOW STATUS LIKE 'Threads_connected';"
```

**Resolution**:
- Verify database credentials in environment
- Check network connectivity
- Monitor connection pool usage

#### 3. Slow API Response Times

**Symptom**: High latency on API calls

**Diagnosis**:
```bash
# Check API Gateway latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=sapien-api \
  --start-time $(date -d '1 hour ago' -Iseconds) \
  --end-time $(date -Iseconds) \
  --period 300 \
  --statistics Average

# Check backend health
curl -w "@curl-format.txt" https://sapien.natterbox.com/v1/hello/all
```

**Resolution**:
- Check cache hit rates
- Review slow database queries
- Scale backend if needed

#### 4. Rate Limiting (429 Too Many Requests)

**Symptom**: 429 errors returned

**Diagnosis**:
```bash
# Check current rate limit usage
aws apigateway get-usage \
  --usage-plan-id <plan-id> \
  --key-id <api-key-id> \
  --start-date 2025-01-20 \
  --end-date 2025-01-21
```

**Resolution**:
- Implement exponential backoff in client
- Request rate limit increase
- Cache responses client-side

#### 5. S3 Upload/Download Failures

**Symptom**: Blob operations failing

**Diagnosis**:
```bash
# Test S3 connectivity
aws s3 ls s3://sapien-blobs/

# Check IAM permissions
aws sts get-caller-identity
```

**Resolution**:
- Verify S3 bucket exists and is accessible
- Check IAM role permissions
- Verify bucket CORS configuration

## Security Considerations

### API Security

- **Authentication**: All endpoints (except health checks) require valid JWT
- **Authorization**: Role-based access control (RBAC) enforced
- **Rate Limiting**: Default 100 req/sec per client
- **CORS**: Configured per environment
- **TLS**: All traffic encrypted (TLS 1.2+)

### Data Security

- **Encryption at Rest**: S3 buckets use SSE-S3
- **Encryption in Transit**: TLS for all communications
- **PII Protection**: Sensitive data masked in logs
- **Audit Logging**: All API calls logged to CloudWatch

## Related Services

| Service | Relationship | Description |
|---------|--------------|-------------|
| [Platform-API](./platform-api.md) | Backend | Internal API that Sapien proxies to |
| [cdrmunch](./cdrmunch.md) | Data Source | Provides call analytics data |
| [Auth0](../infrastructure/auth0.md) | Auth Provider | OAuth2/JWT authentication |
| [AWS API Gateway](../infrastructure/api-gateway.md) | Frontend | API management and routing |

## Source References

- **Repository**: https://github.com/redmatter/platform-sapien
- **Infrastructure**: https://github.com/redmatter/aws-terraform-sapien-proxy
- **Confluence**: [Sapien](https://natterbox.atlassian.net/wiki/spaces/EN/pages/939819009)
- **Key Files Reviewed**:
  - `core/project/app/config/config.yml` - Main configuration
  - `core/project/app/config/security.yml` - Security configuration
  - `core/project/app/config/routing.yml` - Route definitions
  - `core/project/composer.json` - PHP dependencies
  - `core/Dockerfile` - Container definition
  - `docker-compose.yml` - Development setup
  - `aws-terraform-sapien-proxy/api-gateway.tf` - API Gateway config
  - `aws-terraform-sapien-proxy/variables.tf` - Terraform variables
  - `aws-terraform-sapien-proxy/sapien.openapi30.yaml` - OpenAPI spec
  - `core/project/src/Redmatter/UserBundle/Resources/config/routing.yml` - User API routes
  - `core/project/src/Redmatter/SapienBundle/Resources/config/routing.yml` - Core API routes
  - `core/project/src/Redmatter/HelloBundle/Resources/config/routing.yml` - Health check routes
