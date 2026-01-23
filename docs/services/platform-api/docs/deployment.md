# Deployment Guide

## Platform-API Service

### Overview

This comprehensive deployment guide provides detailed instructions for deploying, configuring, and operating the platform-api service in various environments. The platform-api is the core hub for the telecommunications/VoIP platform, managing users, organizations, billing, dialplans, and telephony resources. This guide covers Docker-based deployments, environment configuration, health monitoring, and troubleshooting procedures.

---

## Prerequisites

### System Requirements

Before deploying the platform-api service, ensure your infrastructure meets the following requirements:

#### Hardware Requirements

| Environment | CPU | RAM | Storage | Network |
|-------------|-----|-----|---------|---------|
| Development | 2 cores | 4 GB | 20 GB SSD | 100 Mbps |
| Staging | 4 cores | 8 GB | 50 GB SSD | 1 Gbps |
| Production | 8+ cores | 16+ GB | 100+ GB SSD | 1+ Gbps |

#### Software Dependencies

- **Docker Engine**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For version control and deployment workflows
- **PHP**: Version 8.1+ (for local development and Composer)
- **Composer**: Latest stable version for dependency management

#### Network Requirements

- Outbound HTTPS access for package repositories and external APIs
- Internal network access to database servers
- SIP/RTP ports if handling direct VoIP traffic (typically 5060-5061, 10000-20000)

### External Service Dependencies

The platform-api requires connectivity to the following services:

```yaml
# Required External Services
databases:
  - PostgreSQL 14+ (primary data store)
  - Redis 6+ (caching and session management)
  - MongoDB 5+ (CDR storage and analytics)

external_apis:
  - Payment gateways (Stripe, PayPal)
  - SMS providers
  - Email services (SMTP/API)
  - DNS management APIs

telephony:
  - SIP trunk providers
  - VoIP gateways
  - Media servers
```

### Access and Credentials

Ensure you have the following credentials ready:

- Docker registry access (if using private images)
- Database connection credentials
- OAuth provider secrets
- API keys for external services
- SSL/TLS certificates for production deployment

---

## Docker Compose Setup

### Basic Configuration

Create a `docker-compose.yml` file in your project root:

```yaml
version: '3.8'

services:
  platform-api:
    image: platform-api:latest
    container_name: platform-api
    restart: unless-stopped
    ports:
      - "8080:80"
      - "8443:443"
    environment:
      - APP_ENV=production
      - APP_DEBUG=false
      - APP_KEY=${APP_KEY}
      - DB_CONNECTION=pgsql
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_DATABASE=${DB_DATABASE}
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CACHE_DRIVER=redis
      - SESSION_DRIVER=redis
      - QUEUE_CONNECTION=redis
    volumes:
      - ./storage:/var/www/html/storage
      - ./logs:/var/www/html/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - platform-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:14-alpine
    container_name: platform-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${DB_DATABASE}
      - POSTGRES_USER=${DB_USERNAME}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - platform-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME} -d ${DB_DATABASE}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    container_name: platform-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - platform-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:5
    container_name: platform-mongodb
    restart: unless-stopped
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
    networks:
      - platform-network

volumes:
  postgres_data:
  redis_data:
  mongodb_data:

networks:
  platform-network:
    driver: bridge
```

### Multi-Service Architecture

For larger deployments, separate the API into multiple containers:

```yaml
version: '3.8'

services:
  # Main API Gateway
  api-gateway:
    image: platform-api:latest
    container_name: api-gateway
    command: php-fpm
    environment:
      - SERVICE_ROLE=gateway
    deploy:
      replicas: 3
    networks:
      - platform-network

  # Background Worker for Queue Processing
  queue-worker:
    image: platform-api:latest
    container_name: queue-worker
    command: php artisan queue:work --queue=high,default,low --tries=3
    environment:
      - SERVICE_ROLE=worker
    deploy:
      replicas: 2
    networks:
      - platform-network

  # Scheduler for Cron Jobs
  scheduler:
    image: platform-api:latest
    container_name: scheduler
    command: php artisan schedule:work
    environment:
      - SERVICE_ROLE=scheduler
    networks:
      - platform-network

  # CDR Processor
  cdr-processor:
    image: platform-api:latest
    container_name: cdr-processor
    command: php artisan cdr:process --daemon
    environment:
      - SERVICE_ROLE=cdr-processor
    networks:
      - platform-network

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    container_name: nginx-lb
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api-gateway
    networks:
      - platform-network
```

---

## Production Deployment

### Pre-Deployment Checklist

Before deploying to production, verify the following:

```bash
#!/bin/bash
# pre-deploy-check.sh

echo "=== Platform-API Pre-Deployment Checklist ==="

# 1. Verify environment file
if [ ! -f .env.production ]; then
    echo "❌ Missing .env.production file"
    exit 1
fi
echo "✅ Environment file exists"

# 2. Check required environment variables
required_vars=(
    "APP_KEY"
    "DB_PASSWORD"
    "REDIS_PASSWORD"
    "OAUTH_CLIENT_SECRET"
    "ENCRYPTION_KEY"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env.production; then
        echo "❌ Missing required variable: ${var}"
        exit 1
    fi
done
echo "✅ All required environment variables set"

# 3. Verify SSL certificates
if [ ! -f ./ssl/certificate.crt ] || [ ! -f ./ssl/private.key ]; then
    echo "❌ Missing SSL certificates"
    exit 1
fi
echo "✅ SSL certificates present"

# 4. Test database connectivity
docker-compose exec -T postgres pg_isready -U ${DB_USERNAME} -d ${DB_DATABASE}
if [ $? -ne 0 ]; then
    echo "❌ Database connection failed"
    exit 1
fi
echo "✅ Database connection verified"

echo "=== All pre-deployment checks passed ==="
```

### Deployment Steps

#### Step 1: Prepare the Environment

```bash
# Clone the repository
git clone https://github.com/your-org/platform-api.git
cd platform-api

# Checkout the release version
git checkout v2.5.0

# Copy and configure environment file
cp .env.example .env.production
nano .env.production
```

#### Step 2: Build Docker Images

```bash
# Build the production image
docker build \
    --target production \
    --build-arg APP_VERSION=2.5.0 \
    --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
    -t platform-api:2.5.0 \
    -t platform-api:latest \
    .

# Verify the build
docker images | grep platform-api
```

#### Step 3: Database Migrations

```bash
# Run migrations in a temporary container
docker-compose run --rm platform-api php artisan migrate --force

# Verify migration status
docker-compose run --rm platform-api php artisan migrate:status

# Seed essential data (first deployment only)
docker-compose run --rm platform-api php artisan db:seed --class=ProductionSeeder
```

#### Step 4: Deploy Services

```bash
# Pull latest images
docker-compose pull

# Start services with zero-downtime deployment
docker-compose up -d --scale api-gateway=3 --no-recreate

# Verify deployment
docker-compose ps
docker-compose logs -f --tail=100 platform-api
```

#### Step 5: Post-Deployment Verification

```bash
# Run health checks
curl -s http://localhost/health | jq .

# Verify API endpoints
curl -s http://localhost/api/v1/status | jq .

# Check application logs
docker-compose logs --tail=50 platform-api

# Verify queue processing
docker-compose exec platform-api php artisan queue:monitor
```

### Zero-Downtime Deployment Strategy

```bash
#!/bin/bash
# deploy.sh - Zero-downtime deployment script

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <version>"
    exit 1
fi

echo "Deploying platform-api version ${VERSION}"

# Pull new image
docker pull platform-api:${VERSION}

# Scale up new containers
docker-compose up -d --scale api-gateway=6 --no-recreate

# Wait for new containers to be healthy
echo "Waiting for new containers to become healthy..."
sleep 30

# Verify new containers
docker-compose exec api-gateway curl -s http://localhost/health

# Scale down to normal
docker-compose up -d --scale api-gateway=3

# Remove old containers
docker system prune -f

echo "Deployment complete!"
```

---

## Development Mode

### Local Development Setup

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  platform-api-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: platform-api-dev
    ports:
      - "8080:80"
      - "9003:9003"  # Xdebug port
    environment:
      - APP_ENV=local
      - APP_DEBUG=true
      - XDEBUG_MODE=develop,debug
      - XDEBUG_CONFIG=client_host=host.docker.internal
    volumes:
      - .:/var/www/html
      - ./vendor:/var/www/html/vendor
      - ~/.composer/cache:/root/.composer/cache
    networks:
      - dev-network

  mailhog:
    image: mailhog/mailhog
    container_name: mailhog
    ports:
      - "1025:1025"
      - "8025:8025"
    networks:
      - dev-network
```

### Development Commands

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Install dependencies
docker-compose exec platform-api-dev composer install

# Run tests
docker-compose exec platform-api-dev php artisan test

# Run specific test suite
docker-compose exec platform-api-dev php artisan test --testsuite=Feature

# Generate API documentation
docker-compose exec platform-api-dev php artisan scribe:generate

# Clear all caches
docker-compose exec platform-api-dev php artisan optimize:clear

# Watch logs in real-time
docker-compose exec platform-api-dev tail -f storage/logs/laravel.log
```

### Hot Reloading Configuration

For rapid development with hot reloading:

```php
// config/dev.php
return [
    'hot_reload' => [
        'enabled' => env('HOT_RELOAD_ENABLED', true),
        'watch_paths' => [
            'app/',
            'config/',
            'routes/',
            'resources/',
        ],
        'exclude_patterns' => [
            'storage/',
            'vendor/',
            'node_modules/',
        ],
    ],
];
```

---

## Environment Configuration

### Complete Environment Variables Reference

```bash
# .env.example - Complete configuration reference

#----------------------------------------------
# Application Settings
#----------------------------------------------
APP_NAME="Platform API"
APP_ENV=production
APP_KEY=base64:your-32-character-key-here
APP_DEBUG=false
APP_URL=https://api.yourplatform.com
APP_TIMEZONE=UTC

#----------------------------------------------
# Database Configuration
#----------------------------------------------
DB_CONNECTION=pgsql
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=platform
DB_USERNAME=platform_user
DB_PASSWORD=secure_password_here
DB_SCHEMA=public
DB_SSLMODE=require

# Read replica for scaling (optional)
DB_READ_HOST=postgres-replica
DB_READ_PORT=5432

#----------------------------------------------
# Redis Configuration
#----------------------------------------------
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password_here
REDIS_DB=0
REDIS_CACHE_DB=1
REDIS_SESSION_DB=2

#----------------------------------------------
# MongoDB Configuration (CDR Storage)
#----------------------------------------------
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=platform_cdr
MONGO_USERNAME=mongo_user
MONGO_PASSWORD=mongo_password_here
MONGO_AUTH_DATABASE=admin

#----------------------------------------------
# Cache and Session
#----------------------------------------------
CACHE_DRIVER=redis
CACHE_PREFIX=platform_
SESSION_DRIVER=redis
SESSION_LIFETIME=120
SESSION_ENCRYPT=true

#----------------------------------------------
# Queue Configuration
#----------------------------------------------
QUEUE_CONNECTION=redis
QUEUE_RETRY_AFTER=90
QUEUE_FAILED_DRIVER=database

#----------------------------------------------
# OAuth Configuration
#----------------------------------------------
OAUTH_ENABLED=true
OAUTH_TOKEN_EXPIRY=3600
OAUTH_REFRESH_TOKEN_EXPIRY=604800
OAUTH_PRIVATE_KEY=/var/www/html/storage/oauth/private.key
OAUTH_PUBLIC_KEY=/var/www/html/storage/oauth/public.key

#----------------------------------------------
# Billing and Payment
#----------------------------------------------
STRIPE_KEY=pk_live_xxx
STRIPE_SECRET=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
PAYPAL_MODE=live

#----------------------------------------------
# Telephony Configuration
#----------------------------------------------
SIP_DEFAULT_DOMAIN=sip.yourplatform.com
SIP_PROXY_HOST=sip-proxy.internal
SIP_PROXY_PORT=5060
RTP_PORT_MIN=10000
RTP_PORT_MAX=20000
CDR_PROCESSING_BATCH_SIZE=1000

#----------------------------------------------
# Email Configuration
#----------------------------------------------
MAIL_MAILER=smtp
MAIL_HOST=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=postmaster@yourplatform.com
MAIL_PASSWORD=mail_password_here
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@yourplatform.com
MAIL_FROM_NAME="${APP_NAME}"

#----------------------------------------------
# Logging Configuration
#----------------------------------------------
LOG_CHANNEL=stack
LOG_LEVEL=info
LOG_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

#----------------------------------------------
# Security Settings
#----------------------------------------------
ENCRYPTION_KEY=your-256-bit-encryption-key
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
CORS_ALLOWED_ORIGINS=https://app.yourplatform.com,https://admin.yourplatform.com
TRUSTED_PROXIES=*

#----------------------------------------------
# Feature Flags
#----------------------------------------------
FEATURE_MULTI_TENANT=true
FEATURE_CDR_REALTIME=true
FEATURE_BILLING_AUTO_CHARGE=true
FEATURE_SMS_NOTIFICATIONS=true
```

### Environment-Specific Configurations

```php
// config/platform.php
return [
    'api' => [
        'version' => env('API_VERSION', 'v1'),
        'rate_limit' => [
            'enabled' => env('RATE_LIMIT_ENABLED', true),
            'requests_per_minute' => env('RATE_LIMIT_PER_MINUTE', 60),
            'burst_limit' => env('RATE_LIMIT_BURST', 100),
        ],
        'pagination' => [
            'default_limit' => 25,
            'max_limit' => 100,
        ],
    ],
    
    'telephony' => [
        'sip' => [
            'domain' => env('SIP_DEFAULT_DOMAIN'),
            'proxy' => [
                'host' => env('SIP_PROXY_HOST'),
                'port' => env('SIP_PROXY_PORT', 5060),
            ],
        ],
        'rtp' => [
            'port_min' => env('RTP_PORT_MIN', 10000),
            'port_max' => env('RTP_PORT_MAX', 20000),
        ],
        'cdr' => [
            'batch_size' => env('CDR_PROCESSING_BATCH_SIZE', 1000),
            'retention_days' => env('CDR_RETENTION_DAYS', 365),
        ],
    ],
    
    'billing' => [
        'currency' => env('BILLING_DEFAULT_CURRENCY', 'USD'),
        'tax_enabled' => env('BILLING_TAX_ENABLED', true),
        'auto_charge' => env('FEATURE_BILLING_AUTO_CHARGE', false),
        'grace_period_days' => env('BILLING_GRACE_PERIOD', 7),
    ],
];
```

---

## Health Checks

### Health Check Endpoints

The platform-api exposes multiple health check endpoints:

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health` | Overall system health | JSON status object |
| `/health/live` | Kubernetes liveness probe | HTTP 200/503 |
| `/health/ready` | Kubernetes readiness probe | HTTP 200/503 |
| `/health/db` | Database connectivity | Connection status |
| `/health/redis` | Redis connectivity | Connection status |
| `/health/queue` | Queue worker status | Worker metrics |

### Health Check Response Format

```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "2.5.0",
    "checks": {
        "database": {
            "status": "healthy",
            "latency_ms": 5,
            "connection": "pgsql"
        },
        "redis": {
            "status": "healthy",
            "latency_ms": 2,
            "memory_used": "45MB"
        },
        "mongodb": {
            "status": "healthy",
            "latency_ms": 8
        },
        "queue": {
            "status": "healthy",
            "pending_jobs": 12,
            "failed_jobs": 0,
            "workers": 3
        },
        "storage": {
            "status": "healthy",
            "disk_free": "45GB"
        }
    },
    "uptime_seconds": 86400
}
```

### Implementing Custom Health Checks

```php
// app/Health/Checks/SipProxyCheck.php
namespace App\Health\Checks;

use Illuminate\Support\Facades\Http;

class SipProxyCheck
{
    public function check(): array
    {
        try {
            $start = microtime(true);
            $response = Http::timeout(5)->get(
                config('platform.telephony.sip.proxy.host') . '/status'
            );
            $latency = round((microtime(true) - $start) * 1000);
            
            return [
                'status' => $response->successful() ? 'healthy' : 'degraded',
                'latency_ms' => $latency,
                'active_calls' => $response->json('active_calls', 0),
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'unhealthy',
                'error' => $e->getMessage(),
            ];
        }
    }
}
```

### Monitoring Integration

```yaml
# prometheus/scrape-config.yml
scrape_configs:
  - job_name: 'platform-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['platform-api:80']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '([^:]+):\d+'
        replacement: '${1}'
```

### Alerting Rules

```yaml
# alertmanager/rules.yml
groups:
  - name: platform-api
    rules:
      - alert: PlatformAPIDown
        expr: up{job="platform-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Platform API is down"
          description: "Platform API has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10% for the last 5 minutes"

      - alert: QueueBacklog
        expr: platform_queue_pending_jobs > 10000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Queue backlog detected"
          description: "More than 10,000 jobs pending in queue"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Database Connection Failures

**Symptoms:**
- API returns 500 errors
- Logs show "SQLSTATE[08006] Connection refused"

**Diagnosis:**
```bash
# Check database container status
docker-compose ps postgres

# Test database connectivity
docker-compose exec platform-api php artisan db:monitor

# Check database logs
docker-compose logs postgres --tail=100

# Verify network connectivity
docker-compose exec platform-api ping -c 3 postgres
```

**Solutions:**
```bash
# 1. Restart database container
docker-compose restart postgres

# 2. Check connection limits
docker-compose exec postgres psql -U platform_user -c "SHOW max_connections;"

# 3. Clear connection pool
docker-compose exec platform-api php artisan db:reconnect

# 4. Verify credentials
docker-compose exec platform-api php artisan tinker
>>> DB::connection()->getPdo();
```

#### Issue 2: Redis Connection Issues

**Symptoms:**
- Sessions not persisting
- Cache misses
- Queue jobs not processing

**Diagnosis:**
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Monitor Redis connections
docker-compose exec redis redis-cli info clients

# Check memory usage
docker-compose exec redis redis-cli info memory
```

**Solutions:**
```bash
# Clear Redis cache
docker-compose exec platform-api php artisan cache:clear

# Flush all Redis data (caution in production)
docker-compose exec redis redis-cli FLUSHALL

# Restart Redis with more memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 2gb
```

#### Issue 3: Queue Workers Not Processing

**Symptoms:**
- Jobs stuck in pending state
- Delayed notifications
- CDR processing backlog

**Diagnosis:**
```bash
# Check queue status
docker-compose exec platform-api php artisan queue:monitor

# List failed jobs
docker-compose exec platform-api php artisan queue:failed

# Check worker processes
docker-compose exec queue-worker ps aux | grep queue:work
```

**Solutions:**
```bash
# Restart queue workers
docker-compose restart queue-worker

# Retry failed jobs
docker-compose exec platform-api php artisan queue:retry all

# Clear stuck jobs
docker-compose exec platform-api php artisan queue:flush

# Increase worker processes
docker-compose up -d --scale queue-worker=5
```

#### Issue 4: High Memory Usage

**Symptoms:**
- Container OOM kills
- Slow response times
- Swap usage increasing

**Diagnosis:**
```bash
# Check container memory
docker stats platform-api

# Check PHP memory usage
docker-compose exec platform-api php -i | grep memory_limit

# Monitor memory over time
docker-compose exec platform-api php artisan memory:profile
```

**Solutions:**
```bash
# Increase container memory limit
docker-compose up -d --memory=4g platform-api

# Optimize PHP memory
docker-compose exec platform-api php -d memory_limit=512M artisan optimize

# Enable OPcache
# In php.ini:
# opcache.enable=1
# opcache.memory_consumption=256
```

### Log Analysis

```bash
# View application logs
docker-compose exec platform-api tail -f storage/logs/laravel.log

# Search for specific errors
docker-compose exec platform-api grep -r "SQLSTATE" storage/logs/

# Analyze error patterns
docker-compose exec platform-api cat storage/logs/laravel.log | \
    grep -E "^\[.*\] (local|production)\.ERROR" | \
    awk '{print $4}' | sort | uniq -c | sort -rn

# Export logs for analysis
docker-compose logs --since="2024-01-15T00:00:00" > debug-logs.txt
```

### Performance Profiling

```bash
# Enable query logging
docker-compose exec platform-api php artisan db:query-log enable

# Profile specific endpoint
docker-compose exec platform-api php artisan route:profile /api/v1/users

# Generate performance report
docker-compose exec platform-api php artisan performance:report --format=html > report.html
```

### Emergency Recovery Procedures

```bash
#!/bin/bash
# emergency-recovery.sh

echo "=== Emergency Recovery Procedure ==="

# 1. Stop all containers
docker-compose down

# 2. Backup current data
./scripts/backup.sh emergency-$(date +%Y%m%d-%H%M%S)

# 3. Check system resources
df -h
free -m
docker system df

# 4. Clean up Docker resources
docker system prune -f
docker volume prune -f

# 5. Restart with minimal configuration
docker-compose -f docker-compose.minimal.yml up -d

# 6. Verify basic functionality
sleep 30
curl -s http://localhost/health | jq .

echo "=== Recovery complete. Verify functionality before scaling up ==="
```

---

## Additional Resources

### Related Documentation

- [API Reference Guide](./api-reference.md) - Complete API endpoint documentation
- [Data Models Reference](./data-models.md) - Database schema and model documentation
- [Configuration Reference](./configuration.md) - Detailed configuration options
- [Security Guide](./security.md) - Security best practices and hardening

### Support Channels

- **GitHub Issues**: For bug reports and feature requests
- **Slack Channel**: #platform-api-support for real-time assistance
- **Email**: support@yourplatform.com for critical issues

### Version History

| Version | Date | Notes |
|---------|------|-------|
| 2.5.0 | 2024-01-15 | Added CDR real-time processing |
| 2.4.0 | 2023-12-01 | Multi-tenant billing improvements |
| 2.3.0 | 2023-10-15 | OAuth 2.0 implementation |
| 2.2.0 | 2023-08-01 | SIP trunk management |