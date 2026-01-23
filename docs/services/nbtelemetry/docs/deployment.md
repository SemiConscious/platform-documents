# Deployment Guide

## NBTelemetry Service

### Complete Deployment Instructions Including Docker Setup and Environment Configuration

---

## Overview

This deployment guide provides comprehensive instructions for deploying the NBTelemetry service, a sophisticated telemetry platform for transcription and call analysis. The service integrates with multiple Natural Language Engine (NLE) providers including Watson, Google, and VoiceBase to process and analyze call recordings.

NBTelemetry offers features including talk time analysis, sentiment analysis, interactive transcript visualization, and robust user/organization management. This guide covers everything from initial prerequisites to production-ready deployment configurations.

---

## Prerequisites

Before deploying NBTelemetry, ensure your environment meets the following requirements:

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 100+ GB (depending on recording storage) |
| OS | Linux (Ubuntu 20.04+, CentOS 8+) | Ubuntu 22.04 LTS |

### Required Software

```bash
# Docker (version 20.10 or higher)
docker --version

# Docker Compose (version 2.0 or higher)
docker compose version

# PHP 8.1+ with Composer (for local development)
php --version
composer --version

# Node.js 18+ (for JavaScript UI components)
node --version
npm --version
```

### Installation Commands

#### Ubuntu/Debian

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### CentOS/RHEL

```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

### NLE Provider Credentials

Ensure you have valid API credentials for at least one of the following providers:

- **IBM Watson Speech to Text**: API Key and Service URL
- **Google Cloud Speech-to-Text**: Service Account JSON key file
- **VoiceBase**: API Key and Bearer Token

### Network Requirements

| Port | Service | Description |
|------|---------|-------------|
| 80 | HTTP | Web interface (redirect to HTTPS in production) |
| 443 | HTTPS | Secure web interface |
| 5432 | PostgreSQL | Database (internal only) |
| 6379 | Redis | Cache and queue (internal only) |
| 9000 | PHP-FPM | Application server (internal only) |

---

## Environment Variables Reference

Create a `.env` file in the project root with the following variables:

### Core Application Settings

```bash
# Application Configuration
APP_NAME=NBTelemetry
APP_ENV=production
APP_DEBUG=false
APP_URL=https://your-domain.com
APP_KEY=base64:your-generated-app-key-here

# Logging Configuration
LOG_CHANNEL=stack
LOG_LEVEL=info
LOG_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

### Database Configuration

```bash
# Primary Database
DB_CONNECTION=pgsql
DB_HOST=db
DB_PORT=5432
DB_DATABASE=nbtelemetry
DB_USERNAME=nbtelemetry_user
DB_PASSWORD=your-secure-database-password

# Read Replica (Optional - for high-availability)
DB_READ_HOST=db-replica
DB_READ_PORT=5432
```

### Cache and Queue Configuration

```bash
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# Cache Settings
CACHE_DRIVER=redis
CACHE_PREFIX=nbtelemetry_cache

# Queue Configuration
QUEUE_CONNECTION=redis
QUEUE_RETRY_AFTER=90
```

### NLE Provider Configuration

```bash
# IBM Watson Speech to Text
WATSON_API_KEY=your-watson-api-key
WATSON_SERVICE_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com
WATSON_REGION=us-south
WATSON_MODEL=en-US_BroadbandModel

# Google Cloud Speech-to-Text
GOOGLE_APPLICATION_CREDENTIALS=/app/config/google-credentials.json
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_SPEECH_LANGUAGE=en-US

# VoiceBase Configuration
VOICEBASE_API_KEY=your-voicebase-api-key
VOICEBASE_BEARER_TOKEN=your-bearer-token
VOICEBASE_API_URL=https://apis.voicebase.com/v3

# Default Provider (watson, google, or voicebase)
DEFAULT_NLE_PROVIDER=watson
```

### Storage Configuration

```bash
# File Storage
FILESYSTEM_DRIVER=s3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=nbtelemetry-recordings
AWS_URL=https://nbtelemetry-recordings.s3.amazonaws.com

# Local Storage (alternative)
# FILESYSTEM_DRIVER=local
# STORAGE_PATH=/app/storage/recordings
```

### Security Configuration

```bash
# JWT Authentication
JWT_SECRET=your-jwt-secret-key
JWT_TTL=60
JWT_REFRESH_TTL=20160

# Session Configuration
SESSION_DRIVER=redis
SESSION_LIFETIME=120
SESSION_SECURE_COOKIE=true

# CORS Settings
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOWED_HEADERS=Content-Type,Authorization,X-Requested-With
```

### Monitoring and Analytics

```bash
# Sentry Error Tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1

# Application Metrics
METRICS_ENABLED=true
METRICS_DRIVER=prometheus
STATSD_HOST=statsd
STATSD_PORT=8125
```

---

## Docker Build Process

### Project Structure

```
nbtelemetry/
├── docker/
│   ├── nginx/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   ├── php/
│   │   ├── Dockerfile
│   │   └── php.ini
│   └── node/
│       └── Dockerfile
├── src/
├── public/
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env
```

### PHP Application Dockerfile

```dockerfile
# docker/php/Dockerfile
FROM php:8.2-fpm-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    libpng-dev \
    libxml2-dev \
    zip \
    unzip \
    postgresql-dev \
    freetype-dev \
    libjpeg-turbo-dev \
    libzip-dev \
    ffmpeg

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        pdo \
        pdo_pgsql \
        pgsql \
        gd \
        zip \
        bcmath \
        opcache \
        pcntl

# Install Redis extension
RUN pecl install redis && docker-php-ext-enable redis

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY . .

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Set permissions
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache

# Copy custom PHP configuration
COPY docker/php/php.ini /usr/local/etc/php/conf.d/custom.ini

# Expose port
EXPOSE 9000

CMD ["php-fpm"]
```

### Nginx Dockerfile

```dockerfile
# docker/nginx/Dockerfile
FROM nginx:1.24-alpine

# Remove default configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom configuration
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/

# Create log directory
RUN mkdir -p /var/log/nginx

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
# docker/nginx/nginx.conf
server {
    listen 80;
    server_name _;
    root /var/www/html/public;
    index index.php index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # File upload size
    client_max_body_size 500M;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass app:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_read_timeout 300;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location ~ /\.ht {
        deny all;
    }
}
```

### Building Images

```bash
# Build all images
docker compose build

# Build specific service
docker compose build app

# Build with no cache (clean build)
docker compose build --no-cache

# Build with build arguments
docker compose build --build-arg APP_ENV=production
```

---

## Docker Compose Configuration

### Development Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    container_name: nbtelemetry-app
    restart: unless-stopped
    working_dir: /var/www/html
    volumes:
      - .:/var/www/html
      - ./docker/php/php.ini:/usr/local/etc/php/conf.d/custom.ini
    networks:
      - nbtelemetry-network
    depends_on:
      - db
      - redis

  nginx:
    build:
      context: .
      dockerfile: docker/nginx/Dockerfile
    container_name: nbtelemetry-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - .:/var/www/html
      - ./docker/nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    networks:
      - nbtelemetry-network
    depends_on:
      - app

  db:
    image: postgres:15-alpine
    container_name: nbtelemetry-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_DATABASE}
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - nbtelemetry-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME} -d ${DB_DATABASE}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: nbtelemetry-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - nbtelemetry-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  queue-worker:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    container_name: nbtelemetry-queue
    restart: unless-stopped
    command: php artisan queue:work --sleep=3 --tries=3 --max-time=3600
    volumes:
      - .:/var/www/html
    networks:
      - nbtelemetry-network
    depends_on:
      - db
      - redis

  scheduler:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    container_name: nbtelemetry-scheduler
    restart: unless-stopped
    command: /bin/sh -c "while true; do php artisan schedule:run; sleep 60; done"
    volumes:
      - .:/var/www/html
    networks:
      - nbtelemetry-network
    depends_on:
      - db
      - redis

networks:
  nbtelemetry-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
      args:
        APP_ENV: production
    container_name: nbtelemetry-app
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
    networks:
      - nbtelemetry-network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  nginx:
    build:
      context: .
      dockerfile: docker/nginx/Dockerfile
    container_name: nbtelemetry-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - nbtelemetry-network
    depends_on:
      - app

  db:
    image: postgres:15-alpine
    container_name: nbtelemetry-db
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    environment:
      POSTGRES_DB: ${DB_DATABASE}
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    networks:
      - nbtelemetry-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME} -d ${DB_DATABASE}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: nbtelemetry-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - nbtelemetry-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  queue-worker:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    container_name: nbtelemetry-queue
    restart: always
    command: php artisan queue:work redis --sleep=3 --tries=3 --max-time=3600
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    networks:
      - nbtelemetry-network
    depends_on:
      - db
      - redis

networks:
  nbtelemetry-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

---

## Running the Application

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/nbtelemetry.git
cd nbtelemetry

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env

# Generate application key
docker compose run --rm app php artisan key:generate

# Build and start containers
docker compose up -d --build

# Run database migrations
docker compose exec app php artisan migrate --force

# Seed initial data (optional)
docker compose exec app php artisan db:seed

# Install JavaScript dependencies and build assets
docker compose exec app npm install
docker compose exec app npm run build

# Set up storage link
docker compose exec app php artisan storage:link
```

### Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f app

# Execute commands in container
docker compose exec app php artisan <command>

# Run Composer commands
docker compose exec app composer install
docker compose exec app composer update

# Clear caches
docker compose exec app php artisan cache:clear
docker compose exec app php artisan config:clear
docker compose exec app php artisan view:clear

# Restart queue workers
docker compose restart queue-worker
```

### Starting in Production

```bash
# Use production configuration
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or set as default
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker compose up -d

# Optimize for production
docker compose exec app php artisan config:cache
docker compose exec app php artisan route:cache
docker compose exec app php artisan view:cache
```

---

## Health Checks

### Application Health Endpoint

The NBTelemetry service exposes health check endpoints for monitoring:

```bash
# Basic health check
curl -X GET http://localhost/api/health

# Expected response
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "2.1.0"
}

# Detailed health check
curl -X GET http://localhost/api/health/detailed

# Expected response
{
    "status": "healthy",
    "checks": {
        "database": {
            "status": "healthy",
            "response_time_ms": 5
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 2
        },
        "storage": {
            "status": "healthy",
            "available_space_gb": 85.5
        },
        "nle_providers": {
            "watson": "available",
            "google": "available",
            "voicebase": "available"
        }
    }
}
```

### Docker Health Checks

```bash
# Check container health status
docker compose ps

# Expected output
NAME                    STATUS                    PORTS
nbtelemetry-app        Up 2 hours (healthy)      9000/tcp
nbtelemetry-nginx      Up 2 hours                0.0.0.0:80->80/tcp
nbtelemetry-db         Up 2 hours (healthy)      5432/tcp
nbtelemetry-redis      Up 2 hours (healthy)      6379/tcp

# Inspect individual container health
docker inspect --format='{{json .State.Health}}' nbtelemetry-app | jq
```

### Monitoring Script

```bash
#!/bin/bash
# scripts/health-check.sh

HEALTH_URL="http://localhost/api/health"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"

response=$(curl -s -w "\n%{http_code}" "$HEALTH_URL")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" != "200" ]; then
    message="⚠️ NBTelemetry Health Check Failed\nHTTP Code: $http_code\nResponse: $body"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$SLACK_WEBHOOK"
    exit 1
fi

echo "Health check passed"
exit 0
```

---

## Production Considerations

### Security Best Practices

1. **SSL/TLS Configuration**

```nginx
# docker/nginx/nginx-ssl.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # ... rest of configuration
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

2. **Database Security**

```bash
# Use strong passwords
DB_PASSWORD=$(openssl rand -base64 32)

# Limit database access to application containers only
# In docker-compose, database should not expose ports externally
```

3. **Environment Variable Security**

```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use Docker secrets for sensitive data in Swarm mode
echo "your-db-password" | docker secret create db_password -
```

### Performance Optimization

```bash
# PHP OPcache configuration
opcache.enable=1
opcache.memory_consumption=256
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0

# Redis configuration for production
maxmemory 2gb
maxmemory-policy allkeys-lru

# PostgreSQL tuning
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
work_mem = 64MB
```

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/nbtelemetry"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker compose exec -T db pg_dump -U ${DB_USERNAME} ${DB_DATABASE} | \
    gzip > "${BACKUP_DIR}/db_${DATE}.sql.gz"

# Storage backup
tar -czf "${BACKUP_DIR}/storage_${DATE}.tar.gz" ./storage/app

# Keep only last 7 days
find "${BACKUP_DIR}" -name "*.gz" -mtime +7 -delete

echo "Backup completed: ${DATE}"
```

### Scaling Recommendations

```yaml
# For high-traffic deployments, consider:
services:
  app:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  queue-worker:
    deploy:
      replicas: 5  # Increase for heavy transcription workloads
```

### Logging and Monitoring

```bash
# Centralized logging with ELK stack
docker compose -f docker-compose.yml -f docker-compose.logging.yml up -d

# Prometheus metrics endpoint
curl http://localhost/metrics

# Recommended monitoring stack:
# - Prometheus for metrics collection
# - Grafana for visualization
# - AlertManager for alerting
# - Loki for log aggregation
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Database connection refused | Container not ready | Wait for health check or increase `depends_on` timeout |
| Permission denied on storage | Incorrect ownership | Run `chown -R www-data:www-data storage` |
| Queue jobs failing | Redis connection issue | Check Redis password and connectivity |
| NLE provider timeout | Network/API issues | Increase timeout values, check provider status |

### Debug Commands

```bash
# Check container logs
docker compose logs -f --tail=100 app

# Enter container shell
docker compose exec app sh

# Test database connection
docker compose exec app php artisan db:monitor

# Test Redis connection
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} ping

# List failed queue jobs
docker compose exec app php artisan queue:failed
```

---

## Support

For additional support or questions about deploying NBTelemetry:

- **Documentation**: https://docs.nbtelemetry.io
- **Issue Tracker**: https://github.com/your-org/nbtelemetry/issues
- **Email**: support@nbtelemetry.io