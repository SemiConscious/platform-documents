# Getting Started with Sapien

## Overview

Sapien is a PHP-based REST API service built on the Symfony framework, designed to provide robust CRUD operations for managing entities such as Person, Pet, and Toy. This guide will walk you through the complete setup process, from initial environment configuration to making your first successful API request.

Sapien features a Docker-based development environment with integrated Xdebug support, OAuth2 authentication, rate limiting, and an ESL (Event Source Listener) system for real-time availability updates. Whether you're a new team member or setting up a fresh development environment, this guide provides everything you need to get up and running.

---

## Prerequisites

Before beginning the setup process, ensure your development machine meets the following requirements:

### Required Software

| Software | Minimum Version | Recommended Version | Purpose |
|----------|-----------------|---------------------|---------|
| Docker | 20.10+ | 24.0+ | Container runtime |
| Docker Compose | 2.0+ | 2.21+ | Multi-container orchestration |
| Git | 2.30+ | Latest | Version control |
| PHP (local) | 8.1+ | 8.2+ | CLI tools and IDE integration |
| Composer | 2.0+ | 2.6+ | PHP dependency management |

### System Requirements

- **Operating System**: macOS 11+, Ubuntu 20.04+, or Windows 10/11 with WSL2
- **Memory**: Minimum 8GB RAM (16GB recommended for running full stack)
- **Disk Space**: At least 10GB free space for Docker images and data volumes
- **CPU**: Multi-core processor (4+ cores recommended)

### Network Requirements

- Access to internal package registries
- Ports 80, 443, 3306, and 6379 available on localhost
- DNS resolution capability for local development domains

### IDE Recommendations

While Sapien can be developed with any text editor, we recommend:

- **PhpStorm** (preferred): Full Xdebug integration support with pre-configured settings
- **VS Code**: With PHP Intelephense and Docker extensions
- **Sublime Text**: With PHP-specific packages

### Required Credentials

Before starting, ensure you have:

1. Access to the Sapien Git repository
2. OAuth2 client credentials for API authentication
3. Database connection credentials (provided in environment setup)
4. Access to the internal Docker registry (if applicable)

---

## One-Time Setup

This section covers the initial setup steps that only need to be performed once per development machine.

### Step 1: Clone the Repository

```bash
# Clone the Sapien repository
git clone git@github.com:your-organization/sapien.git

# Navigate to the project directory
cd sapien

# Verify you're on the main branch
git checkout main
git pull origin main
```

### Step 2: Copy Environment Configuration

Sapien uses environment files to manage configuration across different environments:

```bash
# Copy the example environment file
cp .env.example .env

# Copy Docker-specific environment file
cp .env.docker.example .env.docker
```

### Step 3: Configure Environment Variables

Open the `.env` file and configure the following essential variables:

```ini
# Application Configuration
APP_ENV=dev
APP_SECRET=your-unique-secret-key-here
APP_DEBUG=1

# Database Configuration
DATABASE_URL="mysql://sapien_user:sapien_password@database:3306/sapien_db?serverVersion=8.0"

# OAuth2 Configuration
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_TOKEN_ENDPOINT=http://auth-server/oauth/token

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_ORGANIZATION=1000

# Blob Storage
BLOB_STORAGE_ENDPOINT=http://minio:9000
BLOB_STORAGE_BUCKET=sapien-files
BLOB_STORAGE_ACCESS_KEY=minioadmin
BLOB_STORAGE_SECRET_KEY=minioadmin

# ESL Event System
ESL_ENABLED=true
ESL_REDIS_URL=redis://redis:6379

# Profiler (development only)
PROFILER_ENABLED=true
```

### Step 4: Install PHP Dependencies

Even though the application runs in Docker, installing dependencies locally enables IDE autocompletion and static analysis:

```bash
# Install Composer dependencies
composer install

# Verify installation
composer validate
```

### Step 5: Generate Application Keys

```bash
# Generate OAuth2 keys for JWT token signing
mkdir -p config/jwt

# Generate private key
openssl genpkey -algorithm RSA -out config/jwt/private.pem -pkeyopt rsa_keygen_bits:4096

# Generate public key
openssl rsa -pubout -in config/jwt/private.pem -out config/jwt/public.pem

# Set appropriate permissions
chmod 600 config/jwt/private.pem
chmod 644 config/jwt/public.pem
```

### Step 6: Configure IDE for Xdebug (PhpStorm)

For PhpStorm users, configure Xdebug integration:

1. Open **Preferences > PHP > Servers**
2. Add a new server:
   - Name: `sapien-docker`
   - Host: `sapien.local`
   - Port: `80`
   - Debugger: `Xdebug`
3. Enable path mappings:
   - Map project root to `/var/www/html`
4. Set **Preferences > PHP > Debug > Xdebug** port to `9003`

---

## Docker Environment

Sapien uses Docker Compose to orchestrate multiple services including the PHP application, MySQL database, Redis cache, and supporting services.

### Understanding the Docker Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: sapien                    │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   nginx     │    php      │  database   │     redis        │
│   (web)     │   (app)     │  (mysql)    │    (cache)       │
│   :80/:443  │   :9000     │   :3306     │    :6379         │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

### Starting the Docker Environment

```bash
# Build Docker images (first time or after Dockerfile changes)
docker-compose build

# Start all services in detached mode
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

Expected output:

```
NAME                SERVICE     STATUS          PORTS
sapien-nginx-1      nginx       Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
sapien-php-1        php         Up              9000/tcp
sapien-database-1   database    Up              0.0.0.0:3306->3306/tcp
sapien-redis-1      redis       Up              0.0.0.0:6379->6379/tcp
```

### Docker Compose Services Reference

The `docker-compose.yml` file defines the following services:

```yaml
# docker-compose.yml (reference)
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./:/var/www/html
      - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - php

  php:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    volumes:
      - ./:/var/www/html
    environment:
      - PHP_IDE_CONFIG=serverName=sapien-docker
      - XDEBUG_MODE=debug,coverage
      - XDEBUG_CONFIG=client_host=host.docker.internal

  database:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: sapien_db
      MYSQL_USER: sapien_user
      MYSQL_PASSWORD: sapien_password
    volumes:
      - db_data:/var/lib/mysql

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  db_data:
  redis_data:
```

### Useful Docker Commands

```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f php

# Execute command in PHP container
docker-compose exec php bash

# Restart specific service
docker-compose restart php

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v

# Rebuild specific service
docker-compose build --no-cache php
```

---

## Database Setup

Sapien uses MySQL 8.0 as its primary database. Follow these steps to initialize and configure the database.

### Step 1: Wait for Database Readiness

After starting Docker, wait for MySQL to fully initialize:

```bash
# Check database logs
docker-compose logs database

# Wait for "ready for connections" message
# Or use the health check
docker-compose exec database mysqladmin ping -h localhost -u root -p
```

### Step 2: Run Database Migrations

Sapien uses Doctrine Migrations to manage database schema:

```bash
# Enter the PHP container
docker-compose exec php bash

# Inside the container, run migrations
php bin/console doctrine:migrations:migrate --no-interaction

# Verify migration status
php bin/console doctrine:migrations:status
```

Expected output:

```
 == Configuration

    >> Name:                                               Application Migrations
    >> Database Driver:                                    pdo_mysql
    >> Database Name:                                      sapien_db
    >> Configuration Source:                               manually configured
    >> Version Table Name:                                 doctrine_migration_versions
    >> Version Column Name:                                version
    >> Migrations Namespace:                               DoctrineMigrations
    >> Migrations Directory:                               /var/www/html/migrations
    >> Previous Version:                                   DoctrineMigrations\Version20231215000000
    >> Current Version:                                    DoctrineMigrations\Version20231220000000
    >> Next Version:                                       Already at latest version
    >> Latest Version:                                     DoctrineMigrations\Version20231220000000
    >> Executed Migrations:                                15
    >> Executed Unavailable Migrations:                    0
    >> Available Migrations:                               15
    >> New Migrations:                                     0
```

### Step 3: Load Development Fixtures (Optional)

For development purposes, you can load sample data:

```bash
# Load fixtures (inside PHP container)
php bin/console doctrine:fixtures:load --no-interaction

# Or load specific fixture groups
php bin/console doctrine:fixtures:load --group=dev --no-interaction
```

### Step 4: Verify Database Schema

```bash
# Validate schema
php bin/console doctrine:schema:validate

# View entity mappings
php bin/console doctrine:mapping:info
```

### Database Access

Connect to the database directly for debugging:

```bash
# Via Docker
docker-compose exec database mysql -u sapien_user -p sapien_db

# Via local MySQL client
mysql -h 127.0.0.1 -P 3306 -u sapien_user -p sapien_db
```

### Core Database Tables

| Table | Description |
|-------|-------------|
| `person` | Stores person entity records |
| `pet` | Stores pet entity records with owner relationships |
| `toy` | Stores toy entity records with pet relationships |
| `oauth2_access_token` | OAuth2 access token storage |
| `oauth2_refresh_token` | OAuth2 refresh token storage |
| `doctrine_migration_versions` | Migration tracking |

---

## DNS Configuration

To access Sapien using friendly URLs during development, configure local DNS resolution.

### Option 1: Edit Hosts File (Recommended)

Add the following entries to your hosts file:

**macOS/Linux** (`/etc/hosts`):

```bash
# Open hosts file with sudo
sudo nano /etc/hosts

# Add the following lines
127.0.0.1   sapien.local
127.0.0.1   api.sapien.local
```

**Windows** (`C:\Windows\System32\drivers\etc\hosts`):

```
127.0.0.1   sapien.local
127.0.0.1   api.sapien.local
```

### Option 2: Use dnsmasq (Advanced)

For more flexible DNS configuration:

```bash
# Install dnsmasq (macOS)
brew install dnsmasq

# Configure wildcard domain
echo 'address=/.local/127.0.0.1' >> /usr/local/etc/dnsmasq.conf

# Restart dnsmasq
sudo brew services restart dnsmasq

# Configure resolver
sudo mkdir -p /etc/resolver
echo "nameserver 127.0.0.1" | sudo tee /etc/resolver/local
```

### Verify DNS Configuration

```bash
# Test DNS resolution
ping sapien.local

# Should resolve to 127.0.0.1
PING sapien.local (127.0.0.1): 56 data bytes
```

---

## Running Your First Request

Now that your environment is fully configured, let's make your first API request to verify everything is working correctly.

### Step 1: Verify Service Health

```bash
# Check the health endpoint
curl -X GET http://sapien.local/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "blob_storage": "connected"
  }
}
```

### Step 2: Obtain Authentication Token

Before accessing protected endpoints, obtain an OAuth2 access token:

```bash
# Request access token
curl -X POST http://sapien.local/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=your-client-id" \
  -d "client_secret=your-client-secret" \
  -d "scope=read write"
```

Expected response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200a1b2c3d4e5f6...",
  "scope": "read write"
}
```

### Step 3: Create Your First Person Entity

```bash
# Set your access token as an environment variable
export ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."

# Create a new Person
curl -X POST http://sapien.local/api/v1/persons \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "dateOfBirth": "1990-05-15"
  }'
```

Expected response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "dateOfBirth": "1990-05-15",
  "createdAt": "2024-01-15T10:35:00Z",
  "updatedAt": "2024-01-15T10:35:00Z",
  "_links": {
    "self": "/api/v1/persons/550e8400-e29b-41d4-a716-446655440000",
    "pets": "/api/v1/persons/550e8400-e29b-41d4-a716-446655440000/pets"
  }
}
```

### Step 4: Retrieve the Created Person

```bash
# Fetch the person by ID
curl -X GET http://sapien.local/api/v1/persons/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Step 5: List All Persons

```bash
# Get paginated list of persons
curl -X GET "http://sapien.local/api/v1/persons?page=1&limit=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Expected response:

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@example.com"
    }
  ],
  "meta": {
    "currentPage": 1,
    "perPage": 10,
    "totalItems": 1,
    "totalPages": 1
  },
  "_links": {
    "self": "/api/v1/persons?page=1&limit=10",
    "first": "/api/v1/persons?page=1&limit=10",
    "last": "/api/v1/persons?page=1&limit=10"
  }
}
```

### Using the API with PHP

Here's an example of interacting with the Sapien API using PHP:

```php
<?php
// Example: PHP client for Sapien API

use GuzzleHttp\Client;

class SapienClient
{
    private Client $httpClient;
    private string $accessToken;
    
    public function __construct(string $baseUri, string $accessToken)
    {
        $this->httpClient = new Client([
            'base_uri' => $baseUri,
            'timeout' => 30.0,
        ]);
        $this->accessToken = $accessToken;
    }
    
    public function createPerson(array $data): array
    {
        $response = $this->httpClient->post('/api/v1/persons', [
            'headers' => [
                'Authorization' => 'Bearer ' . $this->accessToken,
                'Content-Type' => 'application/json',
            ],
            'json' => $data,
        ]);
        
        return json_decode($response->getBody()->getContents(), true);
    }
    
    public function getPerson(string $id): array
    {
        $response = $this->httpClient->get('/api/v1/persons/' . $id, [
            'headers' => [
                'Authorization' => 'Bearer ' . $this->accessToken,
            ],
        ]);
        
        return json_decode($response->getBody()->getContents(), true);
    }
}

// Usage
$client = new SapienClient('http://sapien.local', $accessToken);
$person = $client->createPerson([
    'firstName' => 'Jane',
    'lastName' => 'Smith',
    'email' => 'jane.smith@example.com',
]);
```

---

## Troubleshooting

This section addresses common issues you may encounter during setup and development.

### Docker Issues

#### Container Won't Start

**Symptom**: `docker-compose up` fails or containers exit immediately.

**Solutions**:

```bash
# Check container logs for errors
docker-compose logs php

# Verify Docker daemon is running
docker info

# Check for port conflicts
lsof -i :80
lsof -i :3306

# Remove orphaned containers and rebuild
docker-compose down --remove-orphans
docker-compose build --no-cache
docker-compose up -d
```

#### Permission Denied Errors

**Symptom**: File permission errors when writing to mounted volumes.

**Solution**:

```bash
# Fix permissions (Linux/macOS)
sudo chown -R $(whoami):$(whoami) .

# Inside container, fix var directory
docker-compose exec php chown -R www-data:www-data var/
```

### Database Issues

#### Connection Refused

**Symptom**: `SQLSTATE[HY000] [2002] Connection refused`

**Solutions**:

```bash
# Wait for database to fully start
docker-compose logs database | grep "ready for connections"

# Verify database container is healthy
docker-compose ps database

# Test connection from PHP container
docker-compose exec php php -r "new PDO('mysql:host=database;dbname=sapien_db', 'sapien_user', 'sapien_password');"
```

#### Migration Failures

**Symptom**: Doctrine migrations fail with schema errors.

**Solutions**:

```bash
# Check current migration status
docker-compose exec php php bin/console doctrine:migrations:status

# Force re-run a specific migration
docker-compose exec php php bin/console doctrine:migrations:execute 'DoctrineMigrations\Version20231220000000' --up

# Reset database (CAUTION: destroys data)
docker-compose exec php php bin/console doctrine:database:drop --force
docker-compose exec php php bin/console doctrine:database:create
docker-compose exec php php bin/console doctrine:migrations:migrate --no-interaction
```

### Authentication Issues

#### Invalid Token Errors

**Symptom**: `401 Unauthorized` with "Invalid token" message.

**Solutions**:

1. Verify JWT keys exist and have correct permissions:
   ```bash
   ls -la config/jwt/
   # Should show private.pem and public.pem
   ```

2. Regenerate tokens if keys were changed:
   ```bash
   # Request new access token
   curl -X POST http://sapien.local/oauth/token \
     -d "grant_type=client_credentials" \
     -d "client_id=your-client-id" \
     -d "client_secret=your-client-secret"
   ```

3. Check token expiration:
   ```bash
   # Decode JWT to check expiration (requires jq)
   echo $ACCESS_TOKEN | cut -d'.' -f2 | base64 -d | jq '.exp'
   ```

### Xdebug Issues

#### Debugger Not Connecting

**Symptom**: Breakpoints not hit in PhpStorm.

**Solutions**:

1. Verify Xdebug is enabled in container:
   ```bash
   docker-compose exec php php -v
   # Should show "with Xdebug"
   ```

2. Check Xdebug configuration:
   ```bash
   docker-compose exec php php -i | grep xdebug
   ```

3. Ensure PhpStorm is listening:
   - Click the "Start Listening for PHP Debug Connections" button
   - Verify port 9003 matches configuration

4. Test Xdebug connection:
   ```bash
   docker-compose exec php php -dxdebug.mode=debug -dxdebug.start_with_request=yes test.php
   ```

### Performance Issues

#### Slow Response Times

**Symptom**: API requests taking several seconds.

**Solutions**:

```bash
# Check container resource usage
docker stats

# Increase Docker memory allocation (Docker Desktop)
# Settings > Resources > Memory > 8GB minimum

# Enable OPcache in development
docker-compose exec php php -i | grep opcache

# Clear Symfony cache
docker-compose exec php php bin/console cache:clear
```

### Getting Help

If you continue experiencing issues:

1. Check the project's issue tracker for known issues
2. Review the Symfony logs: `docker-compose exec php tail -f var/log/dev.log`
3. Enable verbose output: Set `APP_DEBUG=1` in `.env`
4. Contact the development team with:
   - Error messages and stack traces
   - Steps to reproduce the issue
   - Output of `docker-compose logs`
   - Your environment details (`docker version`, OS, etc.)

---

## Next Steps

Congratulations! You now have a fully functional Sapien development environment. Here are recommended next steps:

1. **Explore the API Documentation**: Review the complete API reference for all 24 endpoints
2. **Understand Data Models**: Familiarize yourself with the 44 documented data models
3. **Configure ESL Events**: Set up real-time event subscriptions for availability updates
4. **Set Up Testing**: Run the test suite with `docker-compose exec php bin/phpunit`
5. **Review Security Guidelines**: Understand rate limiting and authentication best practices

For additional documentation, refer to:
- API Reference Guide
- Authentication & Authorization Guide
- Data Models Reference
- ESL Event System Documentation