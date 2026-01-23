# Configuration Reference

## Sapien Service Configuration Guide

This comprehensive guide documents all configuration variables for the **Sapien** service, a Symfony-based application that integrates with AWS services and provides API gateway functionality. This documentation covers environment variables, cache configuration, service container settings, and environment-specific deployment configurations.

---

## Overview of Configuration Approach

Sapien follows a layered configuration strategy that provides flexibility across different deployment environments while maintaining security best practices:

1. **Environment Variables**: Sensitive credentials and environment-specific values are stored as environment variables, never committed to version control
2. **Symfony Configuration**: Service container configuration uses YAML files with parameter binding and autowiring
3. **Cache Configuration**: File-based caching with configurable paths and TTL values
4. **Service Defaults**: Autowiring and autoconfiguration simplify dependency injection

The configuration hierarchy follows this precedence (highest to lowest):
- Environment variables (`.env.local`, system environment)
- Environment-specific files (`.env.prod`, `.env.staging`, `.env.dev`)
- Base configuration (`.env`)
- Application defaults (defined in `services.yaml` and bundle configurations)

---

## Environment Variables

### AWS Service Configuration

These variables configure authentication and access to AWS services used by Sapien for storage, compute, and other cloud resources.

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key ID for authenticating API requests to AWS services. This credential identifies the AWS account and IAM user/role making requests. | String | None | **Yes** | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key paired with the access key ID. This is a sensitive credential used to sign AWS API requests cryptographically. | String | None | **Yes** | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

#### AWS Configuration Details

The AWS credentials are used for multiple services within Sapien:

- **S3 Storage**: Document and asset storage
- **SQS Queues**: Asynchronous job processing
- **CloudWatch**: Logging and metrics
- **Secrets Manager**: Runtime secret retrieval (optional)

**Important**: These credentials should have the minimum required permissions following the principle of least privilege. Create a dedicated IAM user or role specifically for Sapien with policies scoped to only the necessary resources.

---

### Remote Debugging Configuration

These variables enable remote debugging capabilities, primarily used during development.

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `RM_LOC_IP` | Local IP address of the development machine for remote debugging connections. Xdebug will attempt to connect back to this IP address when debugging is initiated. | IPv4 Address | None | No (Dev only) | `192.168.1.100` |
| `RM_XDEBUG_PORT` | Port number that the Xdebug client (IDE) listens on for incoming debugging connections. Must match the port configured in your IDE's debugger settings. | Integer | `9003` | No (Dev only) | `9003` |

#### Xdebug Configuration Notes

When configuring remote debugging:

1. Ensure your firewall allows incoming connections on the Xdebug port
2. The `RM_LOC_IP` should be the IP address accessible from the Docker container or server running Sapien
3. For Docker environments, use the host machine's Docker bridge IP (typically `host.docker.internal` on Docker Desktop or `172.17.0.1` on Linux)

---

### API Gateway Configuration

These Symfony-specific parameters configure how Sapien connects to and routes through the API gateway.

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `SYMFONY__API_GATEWAY__HOST` | Hostname or domain name of the API gateway. This is where all gateway-routed requests will be directed. Can include port number if non-standard. | String (hostname) | None | **Yes** | `api.sapien.example.com` |
| `SYMFONY__API_GATEWAY__PREFIX` | URL path prefix prepended to all API gateway routes. Used for versioning or namespacing API endpoints. Must start with forward slash. | String (path) | `/api` | No | `/api/v1` |
| `SYMFONY__API_GATEWAY__PROTOCOL` | Protocol scheme for API gateway connections. Should be `https` in production environments to ensure encrypted communication. | Enum (http/https) | `https` | No | `https` |

#### API Gateway URL Construction

The full API gateway URL is constructed as:
```
{PROTOCOL}://{HOST}{PREFIX}/[endpoint]
```

**Example**: With the values `https`, `api.sapien.example.com`, and `/api/v1`, an endpoint `/users` would resolve to:
```
https://api.sapien.example.com/api/v1/users
```

---

## Bundle Configuration

### Cache Adapter Configuration

Sapien uses Symfony's cache component with file-based adapters for optimal performance without requiring external cache services.

| Parameter | Description | Type | Default | Required | Example |
|-----------|-------------|------|---------|----------|---------|
| `cache.adapter.php_array.path` | Filesystem path for the PHP array cache adapter's fallback storage. This adapter compiles cache data into a PHP array for opcache optimization, with file fallback for cache misses. | String (path) | `/tmp/cache/php_array_fallback` | No | `/var/cache/sapien/php_array` |
| `cache.adapter.php_file_cache.path` | Directory path where the filesystem cache adapter stores serialized cache entries. Each cache key becomes a file in this directory structure. | String (path) | `/tmp/cache/php_file` | No | `/var/cache/sapien/file_cache` |
| `cache.adapter.php_file_cache.ttl` | Default time-to-live (TTL) in seconds for cached entries. After this duration, cache entries are considered stale and will be regenerated on next access. | Integer (seconds) | `600` | No | `3600` |

#### Cache Configuration Best Practices

```yaml
# config/packages/cache.yaml
framework:
    cache:
        # Use PHP array adapter for compiled/static data
        app: cache.adapter.php_array
        
        # Configure the array adapter
        pools:
            cache.app:
                adapter: cache.adapter.php_array
                default_lifetime: '%cache.adapter.php_file_cache.ttl%'
                
        # Configure paths
        directory: '%cache.adapter.php_file_cache.path%'
```

**Cache Path Considerations**:

1. **Containerized Environments**: Mount a persistent volume to the cache directory if cache persistence across container restarts is required
2. **Permissions**: Ensure the web server user (typically `www-data`) has read/write access to cache directories
3. **Disk Space**: Monitor cache directory growth, especially in high-traffic scenarios
4. **TTL Tuning**: Adjust TTL based on data volatility—use longer TTL for static data, shorter for frequently changing data

---

### Service Container Configuration

These settings control Symfony's dependency injection container behavior.

| Parameter | Description | Type | Default | Required | Example |
|-----------|-------------|------|---------|----------|---------|
| `services._defaults.autowire` | When enabled, Symfony automatically injects service dependencies by analyzing constructor type-hints. Reduces boilerplate configuration significantly. | Boolean | `true` | No | `true` |
| `services._defaults.autoconfigure` | When enabled, Symfony automatically applies appropriate tags to services based on implemented interfaces (e.g., EventSubscriberInterface, Command). | Boolean | `true` | No | `true` |

#### Service Configuration Example

```yaml
# config/services.yaml
services:
    _defaults:
        autowire: '%services._defaults.autowire%'
        autoconfigure: '%services._defaults.autoconfigure%'
        public: false
        bind:
            $apiGatewayHost: '%env(SYMFONY__API_GATEWAY__HOST)%'
            $apiGatewayPrefix: '%env(SYMFONY__API_GATEWAY__PREFIX)%'
            $apiGatewayProtocol: '%env(SYMFONY__API_GATEWAY__PROTOCOL)%'

    App\:
        resource: '../src/'
        exclude:
            - '../src/DependencyInjection/'
            - '../src/Entity/'
            - '../src/Kernel.php'
```

---

## Database Configuration

While not explicitly listed in the discovered variables, Sapien typically requires database configuration. The standard Symfony database configuration applies:

```yaml
# config/packages/doctrine.yaml
doctrine:
    dbal:
        url: '%env(resolve:DATABASE_URL)%'
        server_version: '15'
        driver: 'pdo_pgsql'
```

| Variable | Description | Type | Required | Example |
|----------|-------------|------|----------|---------|
| `DATABASE_URL` | Full database connection URL including credentials, host, port, and database name | DSN String | **Yes** | `postgresql://user:pass@localhost:5432/sapien?serverVersion=15&charset=utf8` |

---

## Rate Limiting Settings

Configure rate limiting to protect API endpoints from abuse:

```yaml
# config/packages/rate_limiter.yaml
framework:
    rate_limiter:
        api_limiter:
            policy: 'sliding_window'
            limit: '%env(int:RATE_LIMIT_REQUESTS)%'
            interval: '%env(RATE_LIMIT_INTERVAL)%'
```

| Variable | Description | Type | Default | Example |
|----------|-------------|------|---------|---------|
| `RATE_LIMIT_REQUESTS` | Maximum requests allowed per interval | Integer | `100` | `1000` |
| `RATE_LIMIT_INTERVAL` | Time window for rate limiting | String | `1 minute` | `1 hour` |

---

## Blob Storage Configuration

For file and document storage beyond AWS S3:

| Variable | Description | Type | Default | Example |
|----------|-------------|------|---------|---------|
| `STORAGE_ADAPTER` | Storage backend adapter | Enum | `s3` | `s3`, `local`, `azure` |
| `S3_BUCKET` | AWS S3 bucket name | String | None | `sapien-documents-prod` |
| `S3_REGION` | AWS region for S3 bucket | String | `us-east-1` | `eu-west-1` |

---

## Logging Configuration

```yaml
# config/packages/monolog.yaml
monolog:
    handlers:
        main:
            type: stream
            path: '%env(LOG_PATH)%'
            level: '%env(LOG_LEVEL)%'
```

| Variable | Description | Type | Default | Example |
|----------|-------------|------|---------|---------|
| `LOG_LEVEL` | Minimum log level to record | Enum | `warning` | `debug`, `info`, `warning`, `error` |
| `LOG_PATH` | Path to log file or `php://stderr` | String | `php://stderr` | `/var/log/sapien/app.log` |

---

## Environment-Specific Configurations

### Development Environment

```bash
# .env.dev
APP_ENV=dev
APP_DEBUG=true

# AWS - Use localstack or development account
AWS_ACCESS_KEY_ID=dev_access_key
AWS_SECRET_ACCESS_KEY=dev_secret_key

# Remote debugging enabled
RM_LOC_IP=host.docker.internal
RM_XDEBUG_PORT=9003

# API Gateway - Local development
SYMFONY__API_GATEWAY__HOST=localhost:8080
SYMFONY__API_GATEWAY__PREFIX=/api
SYMFONY__API_GATEWAY__PROTOCOL=http

# Cache - Short TTL for development
cache.adapter.php_file_cache.ttl=60
cache.adapter.php_file_cache.path=/tmp/sapien/cache

# Logging - Verbose for debugging
LOG_LEVEL=debug
```

### Staging Environment

```bash
# .env.staging
APP_ENV=staging
APP_DEBUG=false

# AWS - Staging account credentials
AWS_ACCESS_KEY_ID=staging_access_key
AWS_SECRET_ACCESS_KEY=staging_secret_key

# Remote debugging disabled in staging
RM_LOC_IP=
RM_XDEBUG_PORT=

# API Gateway - Staging environment
SYMFONY__API_GATEWAY__HOST=api-staging.sapien.example.com
SYMFONY__API_GATEWAY__PREFIX=/api/v1
SYMFONY__API_GATEWAY__PROTOCOL=https

# Cache - Moderate TTL
cache.adapter.php_file_cache.ttl=1800
cache.adapter.php_file_cache.path=/var/cache/sapien

# Logging
LOG_LEVEL=info
```

### Production Environment

```bash
# .env.prod
APP_ENV=prod
APP_DEBUG=false

# AWS - Production credentials (ideally use IAM roles instead)
AWS_ACCESS_KEY_ID=prod_access_key
AWS_SECRET_ACCESS_KEY=prod_secret_key

# Remote debugging strictly disabled
RM_LOC_IP=
RM_XDEBUG_PORT=

# API Gateway - Production
SYMFONY__API_GATEWAY__HOST=api.sapien.example.com
SYMFONY__API_GATEWAY__PREFIX=/api/v1
SYMFONY__API_GATEWAY__PROTOCOL=https

# Cache - Long TTL for production
cache.adapter.php_file_cache.ttl=3600
cache.adapter.php_file_cache.path=/var/cache/sapien

# Logging - Errors and above only
LOG_LEVEL=error
```

---

## Security Considerations

### Sensitive Values Protection

The following variables contain sensitive information and require special handling:

| Variable | Sensitivity | Recommended Storage |
|----------|-------------|---------------------|
| `AWS_ACCESS_KEY_ID` | **High** | AWS Secrets Manager, Vault, or K8s Secrets |
| `AWS_SECRET_ACCESS_KEY` | **Critical** | AWS Secrets Manager, Vault, or K8s Secrets |
| `DATABASE_URL` | **Critical** | Environment variable, never in code |

### Security Best Practices

1. **Never Commit Secrets**: Add `.env.local` and any environment-specific files containing secrets to `.gitignore`

2. **Use Secret Management**: 
   ```yaml
   # Kubernetes secret example
   apiVersion: v1
   kind: Secret
   metadata:
     name: sapien-secrets
   type: Opaque
   stringData:
     AWS_ACCESS_KEY_ID: "your-access-key"
     AWS_SECRET_ACCESS_KEY: "your-secret-key"
   ```

3. **IAM Best Practices**:
   - Use IAM roles for EC2/ECS/EKS instead of access keys when possible
   - Rotate access keys regularly (90 days maximum)
   - Apply least-privilege permissions

4. **Disable Debugging in Production**:
   - Ensure `RM_LOC_IP` and `RM_XDEBUG_PORT` are empty in production
   - Never enable `APP_DEBUG=true` in production

5. **Use HTTPS**: Always set `SYMFONY__API_GATEWAY__PROTOCOL=https` in production

---

## Complete Example .env File

```bash
###############################################################################
#                         SAPIEN CONFIGURATION                                #
###############################################################################

# Application Environment
# Options: dev, staging, prod
APP_ENV=dev
APP_DEBUG=true
APP_SECRET=your-32-character-secret-here

###############################################################################
#                         AWS CONFIGURATION                                   #
###############################################################################

# AWS Credentials
# WARNING: Use IAM roles in production instead of access keys
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# AWS Region (optional - can also be set via AWS_DEFAULT_REGION)
AWS_REGION=us-east-1

###############################################################################
#                         API GATEWAY CONFIGURATION                           #
###############################################################################

# API Gateway Host (required)
# Examples: api.example.com, localhost:8080
SYMFONY__API_GATEWAY__HOST=api.sapien.example.com

# API Gateway URL Prefix (optional)
# Must start with forward slash
SYMFONY__API_GATEWAY__PREFIX=/api/v1

# API Gateway Protocol (optional)
# Options: http, https
# Default: https (always use https in production)
SYMFONY__API_GATEWAY__PROTOCOL=https

###############################################################################
#                         REMOTE DEBUGGING (DEV ONLY)                         #
###############################################################################

# Local IP for Xdebug connection
# Leave empty in production
RM_LOC_IP=192.168.1.100

# Xdebug port (default: 9003)
# Leave empty in production
RM_XDEBUG_PORT=9003

###############################################################################
#                         CACHE CONFIGURATION                                 #
###############################################################################

# PHP Array Cache Fallback Path
cache.adapter.php_array.path=/var/cache/sapien/php_array

# PHP File Cache Directory
cache.adapter.php_file_cache.path=/var/cache/sapien/file

# Cache TTL in seconds (default: 600)
cache.adapter.php_file_cache.ttl=600

###############################################################################
#                         DATABASE CONFIGURATION                              #
###############################################################################

# Database connection URL
# Format: driver://user:password@host:port/database?options
DATABASE_URL="postgresql://sapien_user:password@localhost:5432/sapien_db?serverVersion=15&charset=utf8"

###############################################################################
#                         LOGGING CONFIGURATION                               #
###############################################################################

# Minimum log level: debug, info, notice, warning, error, critical, alert, emergency
LOG_LEVEL=warning

# Log output path (use php://stderr for Docker/container environments)
LOG_PATH=php://stderr

###############################################################################
#                         RATE LIMITING                                       #
###############################################################################

# Maximum requests per interval
RATE_LIMIT_REQUESTS=100

# Rate limit time window
RATE_LIMIT_INTERVAL="1 minute"
```

---

## Troubleshooting Common Configuration Issues

### Issue: AWS Authentication Failures

**Symptoms**: 
- `Error: Unable to locate credentials`
- `InvalidAccessKeyId` errors

**Solutions**:
1. Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set correctly
2. Check for extra whitespace in credential values
3. Ensure IAM user has required permissions
4. Verify credentials haven't been rotated/invalidated

```bash
# Test AWS credentials
aws sts get-caller-identity
```

### Issue: API Gateway Connection Refused

**Symptoms**:
- `Connection refused` errors
- `Could not resolve host` errors

**Solutions**:
1. Verify `SYMFONY__API_GATEWAY__HOST` is correct and reachable
2. Check if the protocol matches the server configuration
3. Ensure firewall rules allow outbound connections
4. Test connectivity:
```bash
curl -I https://${SYMFONY__API_GATEWAY__HOST}${SYMFONY__API_GATEWAY__PREFIX}/health
```

### Issue: Cache Permission Denied

**Symptoms**:
- `Failed to create cache directory`
- `Permission denied` when writing cache files

**Solutions**:
1. Ensure cache directories exist and are writable:
```bash
mkdir -p /var/cache/sapien/{php_array,file}
chown -R www-data:www-data /var/cache/sapien
chmod -R 755 /var/cache/sapien
```
2. In Docker, verify volume mounts have correct permissions

### Issue: Xdebug Not Connecting

**Symptoms**:
- Breakpoints not hit
- No debugger connection established

**Solutions**:
1. Verify `RM_LOC_IP` is accessible from the PHP server
2. Confirm `RM_XDEBUG_PORT` matches IDE configuration
3. Check firewall allows incoming connections on debug port
4. Verify Xdebug extension is loaded:
```bash
php -m | grep xdebug
```

---

## Docker and Kubernetes Configuration

### Docker Compose Example

```yaml
version: '3.8'

services:
  sapien:
    image: sapien:latest
    environment:
      - APP_ENV=prod
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - SYMFONY__API_GATEWAY__HOST=${API_GATEWAY_HOST}
      - SYMFONY__API_GATEWAY__PREFIX=/api/v1
      - SYMFONY__API_GATEWAY__PROTOCOL=https
    volumes:
      - cache_data:/var/cache/sapien
    secrets:
      - aws_credentials

volumes:
  cache_data:

secrets:
  aws_credentials:
    external: true
```

### Kubernetes ConfigMap and Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sapien-config
data:
  APP_ENV: "prod"
  SYMFONY__API_GATEWAY__PREFIX: "/api/v1"
  SYMFONY__API_GATEWAY__PROTOCOL: "https"
  cache.adapter.php_file_cache.ttl: "3600"
---
apiVersion: v1
kind: Secret
metadata:
  name: sapien-secrets
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "your-access-key"
  AWS_SECRET_ACCESS_KEY: "your-secret-key"
  SYMFONY__API_GATEWAY__HOST: "api.sapien.example.com"
```

---

## Validation Checklist

Before deploying Sapien, verify the following:

- [ ] All required environment variables are set
- [ ] AWS credentials are valid and have appropriate permissions
- [ ] API gateway host is reachable from the deployment environment
- [ ] Cache directories exist with correct permissions
- [ ] Production environment has debugging disabled
- [ ] HTTPS is configured for API gateway in production
- [ ] Secrets are stored securely (not in version control)
- [ ] Logging is configured appropriately for the environment
- [ ] Rate limiting is configured to prevent abuse