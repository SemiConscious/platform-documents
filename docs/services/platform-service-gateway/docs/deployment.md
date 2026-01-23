# Deployment Guide

## Overview

This comprehensive deployment guide provides detailed instructions for deploying the Service Gateway to various environments, from local development setups to production-ready configurations. The Service Gateway is a unified API gateway built on the CodeIgniter PHP framework with Docker support, providing integration with multiple CRM and enterprise platforms including Salesforce, Microsoft Dynamics, Zendesk, SugarCRM, Oracle Fusion, and custom data sources.

This guide covers all aspects of deployment including containerization, environment configuration, logging, monitoring, and scaling strategies to ensure your Service Gateway instance runs reliably and efficiently in any environment.

---

## Prerequisites

Before deploying the Service Gateway, ensure your environment meets the following requirements:

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 2 GB | 8+ GB |
| Disk Space | 10 GB | 50+ GB (includes logs) |
| Network | 100 Mbps | 1 Gbps |

### Software Dependencies

#### Required Software

```bash
# Docker (version 20.10 or higher)
docker --version

# Docker Compose (version 2.0 or higher)
docker-compose --version

# Git for repository access
git --version
```

#### PHP Requirements (for non-Docker deployments)

```bash
# PHP 8.1 or higher with required extensions
php -v
php -m | grep -E "(curl|json|mbstring|openssl|pdo|xml|ldap)"
```

#### Composer Dependencies

```bash
# Install Composer globally
curl -sS https://getcomposer.org/installer | php
mv composer.phar /usr/local/bin/composer

# Verify installation
composer --version
```

### Network Requirements

Ensure the following ports are available and not blocked by firewalls:

| Port | Service | Purpose |
|------|---------|---------|
| 80 | HTTP | Primary API traffic |
| 443 | HTTPS | Secure API traffic |
| 514 | Syslog | Remote logging (UDP/TCP) |
| 3306 | MySQL | Database connectivity |
| 6379 | Redis | Session/cache storage |

### External Service Access

The Service Gateway requires network access to external CRM platforms:

```yaml
# Required external endpoints (ensure firewall rules allow outbound)
external_endpoints:
  - login.salesforce.com (443)
  - *.my.salesforce.com (443)
  - login.microsoftonline.com (443)
  - *.dynamics.com (443)
  - *.zendesk.com (443)
  - *.sugarcrm.com (443)
  - *.oraclecloud.com (443)
```

---

## Docker Deployment

### Building the Docker Image

The Service Gateway includes a production-ready Dockerfile. Follow these steps to build and deploy the container:

#### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/platform-service-gateway.git
cd platform-service-gateway

# Checkout the desired release tag
git checkout v2.5.0
```

#### Step 2: Build the Docker Image

```dockerfile
# Dockerfile overview (already included in repository)
FROM php:8.1-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libldap2-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    && docker-php-ext-install pdo pdo_mysql ldap curl xml

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY . .

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader

# Configure Apache
RUN a2enmod rewrite headers
COPY docker/apache.conf /etc/apache2/sites-available/000-default.conf

# Set permissions
RUN chown -R www-data:www-data /var/www/html/writable

EXPOSE 80 443

CMD ["apache2-foreground"]
```

```bash
# Build the image with version tag
docker build -t platform-service-gateway:2.5.0 .

# Tag for your registry
docker tag platform-service-gateway:2.5.0 registry.example.com/platform-service-gateway:2.5.0

# Push to registry (if applicable)
docker push registry.example.com/platform-service-gateway:2.5.0
```

#### Step 3: Run the Container

```bash
# Basic container run
docker run -d \
  --name service-gateway \
  -p 80:80 \
  -p 443:443 \
  -e CI_ENVIRONMENT=production \
  -e DATABASE_HOST=db.example.com \
  -e DATABASE_NAME=gateway_db \
  -e DATABASE_USER=gateway_user \
  -e DATABASE_PASSWORD=secure_password \
  -v /var/log/gateway:/var/www/html/writable/logs \
  platform-service-gateway:2.5.0
```

### Environment Variables

The following environment variables are essential for Docker deployment:

```bash
# Core Configuration
CI_ENVIRONMENT=production|development|testing
APP_BASE_URL=https://gateway.example.com
APP_TIMEZONE=UTC

# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=service_gateway
DATABASE_USER=gateway_user
DATABASE_PASSWORD=secure_password
DATABASE_DRIVER=MySQLi

# Redis Configuration (optional but recommended)
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password

# Logging Configuration
LOG_LEVEL=info
LOG_PATH=/var/www/html/writable/logs
SYSLOG_ENABLED=true
SYSLOG_HOST=syslog.example.com
SYSLOG_PORT=514

# Authentication Providers
SALESFORCE_CLIENT_ID=your_sf_client_id
SALESFORCE_CLIENT_SECRET=your_sf_client_secret
DYNAMICS_CLIENT_ID=your_dynamics_client_id
DYNAMICS_CLIENT_SECRET=your_dynamics_client_secret
ZENDESK_API_TOKEN=your_zendesk_token
LDAP_HOST=ldap.example.com
LDAP_PORT=389
LDAP_BASE_DN=dc=example,dc=com
```

---

## Docker Compose Configuration

For multi-container deployments, Docker Compose provides an efficient orchestration solution.

### Basic Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: Dockerfile
    image: platform-service-gateway:latest
    container_name: service-gateway
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      - CI_ENVIRONMENT=production
      - DATABASE_HOST=db
      - DATABASE_NAME=gateway_db
      - DATABASE_USER=gateway_user
      - DATABASE_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
    volumes:
      - ./logs:/var/www/html/writable/logs
      - ./ssl:/etc/apache2/ssl:ro
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - gateway-network

  db:
    image: mysql:8.0
    container_name: gateway-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=gateway_db
      - MYSQL_USER=gateway_user
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql-data:/var/lib/mysql
      - ./docker/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - gateway-network

  redis:
    image: redis:7-alpine
    container_name: gateway-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - gateway-network

  nginx-proxy:
    image: nginx:alpine
    container_name: gateway-proxy
    restart: unless-stopped
    ports:
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - gateway
    networks:
      - gateway-network

volumes:
  mysql-data:
  redis-data:

networks:
  gateway-network:
    driver: bridge
```

### Environment File Configuration

```bash
# .env file for Docker Compose
# Copy this to .env and customize values

# Database
DB_ROOT_PASSWORD=strong_root_password_here
DB_PASSWORD=strong_user_password_here

# Redis
REDIS_PASSWORD=strong_redis_password_here

# Application
APP_KEY=base64:your_generated_app_key_here

# CRM Integrations
SALESFORCE_CLIENT_ID=your_salesforce_client_id
SALESFORCE_CLIENT_SECRET=your_salesforce_client_secret
DYNAMICS_CLIENT_ID=your_dynamics_client_id
DYNAMICS_CLIENT_SECRET=your_dynamics_client_secret
```

### Running Docker Compose

```bash
# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f gateway

# Scale the gateway service
docker-compose up -d --scale gateway=3

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: destroys data)
docker-compose down -v
```

---

## Production vs Development Mode

### Development Mode Configuration

Development mode enables verbose logging, debugging tools, and relaxed security for local development:

```php
<?php
// app/Config/Boot/development.php

// Enable detailed error reporting
error_reporting(E_ALL);
ini_set('display_errors', '1');

// Development-specific settings
defined('SHOW_DEBUG_BACKTRACE') || define('SHOW_DEBUG_BACKTRACE', true);
defined('CI_DEBUG') || define('CI_DEBUG', true);
```

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: Dockerfile.dev
    environment:
      - CI_ENVIRONMENT=development
      - LOG_LEVEL=debug
      - XDEBUG_MODE=debug,coverage
    volumes:
      - .:/var/www/html  # Mount source for live reload
      - ./writable/logs:/var/www/html/writable/logs
    ports:
      - "80:80"
      - "9003:9003"  # Xdebug port
```

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Production Mode Configuration

Production mode optimizes for performance, security, and stability:

```php
<?php
// app/Config/Boot/production.php

// Disable error display
error_reporting(E_ALL & ~E_NOTICE & ~E_DEPRECATED & ~E_STRICT);
ini_set('display_errors', '0');

// Production settings
defined('SHOW_DEBUG_BACKTRACE') || define('SHOW_DEBUG_BACKTRACE', false);
defined('CI_DEBUG') || define('CI_DEBUG', false);
```

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  gateway:
    image: registry.example.com/platform-service-gateway:2.5.0
    environment:
      - CI_ENVIRONMENT=production
      - LOG_LEVEL=warning
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

### Configuration Comparison

| Setting | Development | Production |
|---------|-------------|------------|
| `CI_ENVIRONMENT` | development | production |
| `LOG_LEVEL` | debug | warning/error |
| `display_errors` | On | Off |
| `CI_DEBUG` | true | false |
| `Composer install` | Full | `--no-dev` |
| `OpCache` | Disabled | Enabled |
| `Session handler` | Files | Redis |

---

## Logging Configuration

### Log Levels and Configuration

The Service Gateway supports multiple log levels and output destinations:

```php
<?php
// app/Config/Logger.php

namespace Config;

use CodeIgniter\Config\BaseConfig;

class Logger extends BaseConfig
{
    public $threshold = 4; // 1=Emergency, 4=Info, 8=Debug
    
    public $dateFormat = 'Y-m-d H:i:s';
    
    public $handlers = [
        'CodeIgniter\Log\Handlers\FileHandler' => [
            'handles'         => ['critical', 'alert', 'emergency', 'debug', 
                                  'error', 'info', 'notice', 'warning'],
            'fileExtension'   => 'log',
            'filePermissions' => 0644,
            'path'           => WRITEPATH . 'logs/',
        ],
    ];
}
```

### Environment-Based Log Configuration

```bash
# Environment variables for logging
LOG_THRESHOLD=4          # 1-8 (1=emergency only, 8=all including debug)
LOG_DATE_FORMAT="Y-m-d H:i:s"
LOG_FILE_PATH=/var/www/html/writable/logs/
LOG_FILE_EXTENSION=log
LOG_FILE_PERMISSIONS=0644
```

### Structured Logging Format

```php
<?php
// Custom log format for JSON output
// app/Config/Logger.php (extended)

public $handlers = [
    'App\Libraries\JsonLogHandler' => [
        'handles'     => ['critical', 'alert', 'emergency', 'error', 'warning'],
        'path'        => WRITEPATH . 'logs/',
        'format'      => 'json',
    ],
];
```

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "error",
  "message": "Failed to authenticate with Salesforce",
  "context": {
    "provider": "salesforce",
    "error_code": "INVALID_SESSION_ID",
    "request_id": "req_abc123",
    "user_id": "usr_xyz789"
  },
  "trace": "..."
}
```

### Log Rotation

```bash
# /etc/logrotate.d/service-gateway
/var/log/gateway/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        docker kill -s HUP service-gateway 2>/dev/null || true
    endscript
}
```

---

## Syslog Integration

### Configuring Syslog Output

The Service Gateway supports remote syslog for centralized log management:

```php
<?php
// app/Config/Logger.php - Syslog Handler

public $handlers = [
    'CodeIgniter\Log\Handlers\FileHandler' => [
        // ... file handler config
    ],
    
    'App\Libraries\SyslogHandler' => [
        'handles'     => ['critical', 'alert', 'emergency', 'error', 'warning'],
        'facility'    => LOG_LOCAL0,
        'identity'    => 'service-gateway',
        'options'     => LOG_PID | LOG_NDELAY,
    ],
];
```

### Custom Syslog Handler Implementation

```php
<?php
// app/Libraries/SyslogHandler.php

namespace App\Libraries;

use CodeIgniter\Log\Handlers\BaseHandler;

class SyslogHandler extends BaseHandler
{
    protected $facility = LOG_LOCAL0;
    protected $identity = 'service-gateway';
    protected $syslogHost;
    protected $syslogPort = 514;
    
    public function __construct(array $config = [])
    {
        parent::__construct($config);
        
        $this->syslogHost = env('SYSLOG_HOST', '127.0.0.1');
        $this->syslogPort = env('SYSLOG_PORT', 514);
        $this->identity = env('SYSLOG_IDENTITY', 'service-gateway');
        
        if (env('SYSLOG_ENABLED', false)) {
            openlog($this->identity, LOG_PID | LOG_NDELAY, $this->facility);
        }
    }
    
    public function handle($level, $message): bool
    {
        if (!env('SYSLOG_ENABLED', false)) {
            return false;
        }
        
        $priority = $this->mapLevelToPriority($level);
        
        // Format message with structured data
        $formattedMessage = sprintf(
            '[%s] [%s] %s',
            strtoupper($level),
            env('APP_INSTANCE_ID', gethostname()),
            $message
        );
        
        return syslog($priority, $formattedMessage);
    }
    
    protected function mapLevelToPriority(string $level): int
    {
        $priorities = [
            'emergency' => LOG_EMERG,
            'alert'     => LOG_ALERT,
            'critical'  => LOG_CRIT,
            'error'     => LOG_ERR,
            'warning'   => LOG_WARNING,
            'notice'    => LOG_NOTICE,
            'info'      => LOG_INFO,
            'debug'     => LOG_DEBUG,
        ];
        
        return $priorities[$level] ?? LOG_INFO;
    }
}
```

### Remote Syslog Configuration

```yaml
# docker-compose.yml - Syslog configuration
services:
  gateway:
    environment:
      - SYSLOG_ENABLED=true
      - SYSLOG_HOST=syslog.example.com
      - SYSLOG_PORT=514
      - SYSLOG_PROTOCOL=udp
      - SYSLOG_IDENTITY=service-gateway-prod
    logging:
      driver: syslog
      options:
        syslog-address: "udp://syslog.example.com:514"
        syslog-facility: "local0"
        tag: "service-gateway/{{.Name}}/{{.ID}}"
```

### Integration with Log Aggregators

```yaml
# Fluentd configuration example
# fluent.conf
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<filter service-gateway.**>
  @type parser
  key_name log
  <parse>
    @type json
  </parse>
</filter>

<match service-gateway.**>
  @type elasticsearch
  host elasticsearch.example.com
  port 9200
  index_name service-gateway
  type_name _doc
</match>
```

---

## Health Checks

### Implementing Health Check Endpoints

The Service Gateway provides comprehensive health check endpoints for monitoring:

```php
<?php
// app/Controllers/Health.php

namespace App\Controllers;

use CodeIgniter\RESTful\ResourceController;

class Health extends ResourceController
{
    /**
     * Basic liveness probe
     * GET /health
     */
    public function index()
    {
        return $this->respond([
            'status' => 'healthy',
            'timestamp' => date('c'),
            'version' => env('APP_VERSION', '2.5.0'),
        ]);
    }
    
    /**
     * Detailed readiness probe
     * GET /health/ready
     */
    public function ready()
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'filesystem' => $this->checkFilesystem(),
            'external_services' => $this->checkExternalServices(),
        ];
        
        $allHealthy = !in_array(false, array_column($checks, 'healthy'));
        
        return $this->respond([
            'status' => $allHealthy ? 'ready' : 'degraded',
            'checks' => $checks,
            'timestamp' => date('c'),
        ], $allHealthy ? 200 : 503);
    }
    
    /**
     * Detailed system status
     * GET /health/status
     */
    public function status()
    {
        return $this->respond([
            'status' => 'healthy',
            'version' => env('APP_VERSION', '2.5.0'),
            'environment' => env('CI_ENVIRONMENT', 'production'),
            'uptime' => $this->getUptime(),
            'memory' => [
                'used' => memory_get_usage(true),
                'peak' => memory_get_peak_usage(true),
                'limit' => ini_get('memory_limit'),
            ],
            'connections' => [
                'database' => $this->getDatabaseStats(),
                'redis' => $this->getRedisStats(),
            ],
            'endpoints' => [
                'total' => 59,
                'active' => $this->getActiveEndpoints(),
            ],
        ]);
    }
    
    protected function checkDatabase(): array
    {
        try {
            $db = \Config\Database::connect();
            $db->query('SELECT 1');
            return ['healthy' => true, 'latency_ms' => $db->getConnectDuration() * 1000];
        } catch (\Exception $e) {
            return ['healthy' => false, 'error' => $e->getMessage()];
        }
    }
    
    protected function checkRedis(): array
    {
        try {
            $redis = new \Redis();
            $redis->connect(env('REDIS_HOST', 'localhost'), env('REDIS_PORT', 6379));
            $start = microtime(true);
            $redis->ping();
            $latency = (microtime(true) - $start) * 1000;
            return ['healthy' => true, 'latency_ms' => round($latency, 2)];
        } catch (\Exception $e) {
            return ['healthy' => false, 'error' => $e->getMessage()];
        }
    }
    
    protected function checkFilesystem(): array
    {
        $logPath = WRITEPATH . 'logs/';
        $writable = is_writable($logPath);
        $freeSpace = disk_free_space($logPath);
        
        return [
            'healthy' => $writable && $freeSpace > 1073741824, // > 1GB
            'writable' => $writable,
            'free_space_gb' => round($freeSpace / 1073741824, 2),
        ];
    }
    
    protected function checkExternalServices(): array
    {
        // Check connectivity to CRM providers
        $services = [];
        
        // Salesforce check
        $services['salesforce'] = $this->pingEndpoint('https://login.salesforce.com');
        
        // Microsoft Dynamics check  
        $services['dynamics'] = $this->pingEndpoint('https://login.microsoftonline.com');
        
        return $services;
    }
    
    protected function pingEndpoint(string $url): array
    {
        $start = microtime(true);
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 5,
            CURLOPT_NOBODY => true,
        ]);
        curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $latency = (microtime(true) - $start) * 1000;
        curl_close($ch);
        
        return [
            'healthy' => $httpCode >= 200 && $httpCode < 400,
            'latency_ms' => round($latency, 2),
            'http_code' => $httpCode,
        ];
    }
}
```

### Docker Health Check Configuration

```dockerfile
# Dockerfile health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1
```

```yaml
# docker-compose.yml health check
services:
  gateway:
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Kubernetes Health Probes

```yaml
# kubernetes deployment health probes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-gateway
spec:
  template:
    spec:
      containers:
        - name: gateway
          image: platform-service-gateway:2.5.0
          ports:
            - containerPort: 80
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
              path: /health/ready
              port: 80
            initialDelaySeconds: 10
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

---

## Scaling Considerations

### Horizontal Scaling Architecture

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │    (HAProxy)    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Gateway 1   │  │   Gateway 2   │  │   Gateway 3   │
│  (Container)  │  │  (Container)  │  │  (Container)  │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌───────────────┐                   ┌───────────────┐
│ Redis Cluster │                   │ MySQL Cluster │
│   (Sessions)  │                   │   (Primary)   │
└───────────────┘                   └───────────────┘
```

### Docker Swarm Deployment

```yaml
# docker-stack.yml for Docker Swarm
version: '3.8'

services:
  gateway:
    image: registry.example.com/platform-service-gateway:2.5.0
    deploy:
      mode: replicated
      replicas: 5
      placement:
        constraints:
          - node.role == worker
      update_config:
        parallelism: 2
        delay: 10s
        failure_action: rollback
        order: start-first
      rollback_config:
        parallelism: 1
        delay: 10s
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    networks:
      - gateway-overlay
    secrets:
      - db_password
      - redis_password
      - salesforce_secret

networks:
  gateway-overlay:
    driver: overlay
    attachable: true

secrets:
  db_password:
    external: true
  redis_password:
    external: true
  salesforce_secret:
    external: true
```

### Kubernetes Deployment with Auto-scaling

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-gateway
  namespace: gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: service-gateway
  template:
    metadata:
      labels:
        app: service-gateway
    spec:
      containers:
        - name: gateway
          image: platform-service-gateway:2.5.0
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          envFrom:
            - configMapRef:
                name: gateway-config
            - secretRef:
                name: gateway-secrets
---
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: service-gateway-hpa
  namespace: gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: service-gateway
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### Load Balancer Configuration

```nginx
# nginx load balancer configuration
upstream service_gateway {
    least_conn;
    
    server gateway1:80 weight=5 max_fails=3 fail_timeout=30s;
    server gateway2:80 weight=5 max_fails=3 fail_timeout=30s;
    server gateway3:80 weight=5 max_fails=3 fail_timeout=30s;
    
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name gateway.example.com;
    
    ssl_certificate /etc/nginx/ssl/gateway.crt;
    ssl_certificate_key /etc/nginx/ssl/gateway.key;
    
    location / {
        proxy_pass http://service_gateway;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Health check endpoint bypass
        proxy_next_upstream error timeout http_503;
    }
    
    location /health {
        proxy_pass http://service_gateway;
        access_log off;
    }
}
```

### Session and State Management

For horizontal scaling, ensure sessions are stored externally:

```php
<?php
// app/Config/Session.php

namespace Config;

use CodeIgniter\Config\BaseConfig;

class Session extends BaseConfig
{
    public $driver = 'CodeIgniter\Session\Handlers\RedisHandler';
    public $cookieName = 'gateway_session';
    public $expiration = 7200;
    public $savePath = 'tcp://redis:6379';
    public $matchIP = false;
    public $timeToUpdate = 300;
    public $regenerateDestroy = false;
}
```

### Performance Tuning Recommendations

| Parameter | Development | Production | High-Traffic |
|-----------|-------------|------------|--------------|
| PHP Workers | 2 | 8 | 16+ |
| Max Connections | 100 | 500 | 2000+ |
| Memory per Instance | 512MB | 2GB | 4GB |
| Redis Connections | 10 | 50 | 200 |
| DB Connection Pool | 5 | 20 | 50 |
| Request Timeout | 60s | 30s | 15s |

---

## Troubleshooting

### Common Deployment Issues

#### Container Fails to Start

```bash
# Check container logs
docker logs service-gateway --tail 100

# Verify environment variables
docker exec service-gateway env | grep -E "(CI_|DATABASE_|REDIS_)"

# Test database connectivity
docker exec service-gateway php spark db:table users
```

#### Health Check Failures

```bash
# Manual health check
curl -v http://localhost/health/ready

# Check individual components
docker exec service-gateway php -r "
    \$redis = new Redis();
    \$redis->connect('redis', 6379);
    echo \$redis->ping();
"
```

#### Performance Issues

```bash
# Monitor container resources
docker stats service-gateway

# Check PHP-FPM status
docker exec service-gateway curl http://localhost/fpm-status

# Analyze slow queries
docker exec gateway-db mysql -e "SHOW PROCESSLIST;"
```

---

## Conclusion

This deployment guide covers the essential aspects of deploying the Service Gateway across various environments. Key takeaways include:

1. **Always use environment variables** for configuration to maintain portability
2. **Implement comprehensive health checks** for reliable orchestration
3. **Use external session storage** (Redis) for horizontal scaling
4. **Configure centralized logging** for operational visibility
5. **Plan for scaling** from the start with stateless container design

For additional support, refer to the API documentation for the 59 available endpoints, or consult the configuration reference for all 50 configuration variables.