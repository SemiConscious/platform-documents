# Configuration Guide for platform-dgapi

## Overview

The `platform-dgapi` service is a RESTful API platform built on the Kohana PHP framework, designed to handle data gateway operations with support for multiple database connections, XML document generation, and configurable caching mechanisms. This comprehensive configuration guide covers all aspects of setting up and customizing the platform for different environments.

### Configuration Approach

The platform-dgapi service uses a layered configuration approach:

1. **Environment Variables**: Primary method for sensitive and environment-specific settings
2. **Configuration Arrays**: PHP-based configuration files for framework settings
3. **Prefix-Based Database Configuration**: Dynamic multi-database support using configurable prefixes
4. **Runtime Configuration**: Some settings can be modified at runtime through the application

Configuration values are loaded in the following priority order (highest to lowest):
- Environment variables
- Configuration file overrides
- Default values defined in the codebase

---

## Database Configuration

The platform-dgapi service supports multiple database connections through a flexible prefix-based configuration system. This allows connecting to several MySQL databases simultaneously, each identified by a unique prefix.

### Database Connection Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `database.persistency` | Enable or disable persistent database connections. Persistent connections remain open between requests, reducing connection overhead. | Boolean | `True` | No | `True` |
| `database.prefixes` | Comma-separated list of database prefixes for configuring multiple database connections | String | None | Yes (if using multiple DBs) | `main,analytics,reporting` |
| `{prefix}.mysql_user` | MySQL username for the prefixed database connection | String | None | **Yes** | `dgapi_user` |
| `{prefix}.mysql_password` | MySQL password for the prefixed database connection | String | None | **Yes** | `SecureP@ssw0rd!` |
| `{prefix}.mysql_host` | MySQL host address for the prefixed database connection | String | None | **Yes** | `mysql.internal.example.com` |
| `{prefix}.mysql_schema` | MySQL database/schema name for the prefixed database connection | String | None | **Yes** | `dgapi_production` |

### Multi-Database Configuration Example

When configuring multiple databases, first define your prefixes, then configure each database using those prefixes:

```ini
# Define available database prefixes
database.prefixes=main,analytics,cache

# Main database configuration
main.mysql_user=dgapi_main_user
main.mysql_password=MainDbP@ssword123
main.mysql_host=main-mysql.internal.example.com
main.mysql_schema=dgapi_main

# Analytics database configuration
analytics.mysql_user=dgapi_analytics_user
analytics.mysql_password=AnalyticsP@ssword456
analytics.mysql_host=analytics-mysql.internal.example.com
analytics.mysql_schema=dgapi_analytics

# Cache database configuration
cache.mysql_user=dgapi_cache_user
cache.mysql_password=CacheP@ssword789
cache.mysql_host=cache-mysql.internal.example.com
cache.mysql_schema=dgapi_cache
```

### Database Connection Best Practices

1. **Persistent Connections**: Enable `database.persistency=True` in production environments with high traffic to reduce connection overhead. Disable in development to ensure clean connection states.

2. **Connection Pooling**: When using containerized deployments, consider using a connection pooler like ProxySQL to manage database connections efficiently.

3. **Read Replicas**: Configure separate prefixes for read and write operations to distribute database load:
   ```ini
   database.prefixes=write,read
   write.mysql_host=primary-mysql.internal.example.com
   read.mysql_host=replica-mysql.internal.example.com
   ```

---

## RESTful API Configuration

The platform-dgapi service provides extensive configuration options for its RESTful API layer, including MIME type handling, response formats, and caching behavior.

### RESTful API Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `restful.supported_mimes` | Set of supported MIME type extension patterns for API responses | Array/String | `html, xml, dbg enabled` | No | `html,xml,json,dbg` |
| `restful.default_response` | Default response content type when not specified in request | String | `html` | No | `xml` |
| `restful.auto_send_header` | Automatically send Content-Type header with responses | Boolean | None | No | `True` |
| `restful.caching` | Enable caching of RESTful calculation results | Boolean | None | No | `True` |
| `restful.caching_prefix` | Prefix for cached file names in local storage | String | `hook_restful_` | No | `api_cache_` |
| `restful.delete_args` | Array of argument names that trigger DELETE HTTP method detection | Array | `['delete']` | No | `['delete', 'remove', 'destroy']` |

### MIME Type Configuration

The `restful.supported_mimes` configuration accepts the following patterns:

| Extension | Content-Type | Use Case |
|-----------|--------------|----------|
| `html` | `text/html` | Browser-friendly responses, default web interface |
| `xml` | `application/xml` | Machine-readable responses, legacy integrations |
| `dbg` | `text/plain` | Debug output for development and troubleshooting |
| `json` | `application/json` | Modern API integrations (if enabled) |

### API Caching Configuration

When `restful.caching` is enabled, the service caches computed responses to improve performance:

```ini
# Enable API response caching
restful.caching=True

# Use a descriptive prefix for cache identification
restful.caching_prefix=dgapi_v2_cache_

# Ensure cache directory has proper permissions
kohana.internal_cache_path=/var/cache/dgapi/
```

---

## Internal Settings

### Kohana Framework Configuration

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `kohana.site_domain` | Base path/domain for URL generation throughout the application | String | `http://dgapi.redmatter.com/` | No | `https://api.example.com/` |
| `kohana.internal_cache` | Duration of internal cache in seconds. Set to `0` or `FALSE` to disable | Integer/Boolean | None | No | `3600` |
| `kohana.internal_cache_path` | Directory path for storing internal cache files | String | `APPPATH/cache/` | No | `/var/cache/dgapi/` |
| `kohana.internal_cache_encrypt` | Enable encryption for cached data | Boolean | None | No | `True` |
| `kohana.output_compression` | Enable gzip compression for output. Values 1-9 set compression level | Integer/Boolean | None | No | `6` |

### Application Core Settings

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `timezone.default` | Default timezone offset for date/time operations | String | `+00:00` | No | `-05:00` |
| `internal_cache_key` | Encryption key used for internal cache encryption | String | `qwf89phasvi1asdf22asdf132sadf134wsdfouhasd89pyg` | No | (Custom 48+ char key) |
| `site_protocol` | Force a specific protocol (http/https) for generated URLs | String | None | No | `https` |
| `index_page` | Name of the front controller file | String | None | No | `index.php` |
| `url_suffix` | Fake file extension appended to generated URLs | String | None | No | `.html` |
| `extension_prefix` | Filename prefix for identifying framework extensions | String | `RM_` | No | `DGAPI_` |

### Security and Debugging Settings

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `global_xss_filtering` | Enable global XSS filtering on GET, POST, and SERVER data | Boolean | None | No | `True` |
| `enable_hooks` | Enable or disable Kohana hooks system | Boolean | `True` | No | `True` |
| `log_threshold` | Logging verbosity level (0=disabled, 1=errors, 2=warnings, 3=notices, 4=debugging) | Integer | `2` | No | `1` |
| `log_directory` | Directory path for storing application log files | String | None | No | `/var/log/dgapi/` |
| `display_errors` | Display Kohana error pages (disable in production) | Boolean | `True` | No | `False` |
| `render_stats` | Include performance statistics in output | Boolean | `True` | No | `False` |

### XML Document Generation Settings

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `XMLVersion` | XML version declaration for generated documents | String | `1.0` | No | `1.1` |
| `XMLEncoding` | Character encoding for XML documents | String | `UTF-8` | No | `ISO-8859-1` |
| `XMLFormatOutput` | Format XML output with indentation and whitespace | Boolean | `True` | No | `False` |
| `XMLRecover` | Enable libxml recovery mode for parsing malformed XML | Boolean | `True` | No | `False` |

### Version Information

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `VERSION_MA` | Major version number | Integer | None | No | `2` |
| `VERSION_MI` | Minor version number | Integer | None | No | `5` |
| `VERSION_MIN` | Minimum/patch version number | Integer | None | No | `3` |
| `BUILD_ID` | Build identifier for deployment tracking | String/Integer | `0` | No | `20240115-abc123` |

---

## Routes Configuration

The routing system controls how URLs are mapped to controllers and actions within the platform.

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `routes._default` | Default controller for unmatched routes | String | `info` | No | `api` |

### Route Configuration Examples

```php
// Default route configuration
$config['routes']['_default'] = 'info';

// Custom API routes
$config['routes']['api/v1/(.*)'] = 'api_v1/$1';
$config['routes']['health'] = 'status/health';
$config['routes']['metrics'] = 'status/metrics';
```

---

## Environment Variables

### Complete Environment Variable Reference

The following table provides a comprehensive list of all environment variables with their configurations across different deployment scenarios:

| Environment Variable | Description | Type | Default | Required | Dev Example | Prod Example |
|---------------------|-------------|------|---------|----------|-------------|--------------|
| `DATABASE_PERSISTENCY` | Enable persistent DB connections | Boolean | `True` | No | `False` | `True` |
| `DATABASE_PREFIXES` | Comma-separated DB prefixes | String | None | Conditional | `dev` | `primary,replica` |
| `KOHANA_SITE_DOMAIN` | Base URL for the application | String | `http://dgapi.redmatter.com/` | No | `http://localhost:8080/` | `https://api.production.com/` |
| `KOHANA_INTERNAL_CACHE` | Cache duration in seconds | Integer | `0` | No | `0` | `3600` |
| `KOHANA_INTERNAL_CACHE_PATH` | Cache directory path | String | `APPPATH/cache/` | No | `/tmp/dgapi-cache/` | `/var/cache/dgapi/` |
| `KOHANA_INTERNAL_CACHE_ENCRYPT` | Enable cache encryption | Boolean | None | No | `False` | `True` |
| `KOHANA_OUTPUT_COMPRESSION` | Gzip compression level | Integer | None | No | `0` | `6` |
| `TIMEZONE_DEFAULT` | Default timezone | String | `+00:00` | No | `-05:00` | `+00:00` |
| `INTERNAL_CACHE_KEY` | Cache encryption key | String | (hardcoded) | No | (default) | (custom secure key) |
| `SITE_PROTOCOL` | Forced protocol | String | None | No | `http` | `https` |
| `GLOBAL_XSS_FILTERING` | Enable XSS filtering | Boolean | None | No | `True` | `True` |
| `ENABLE_HOOKS` | Enable Kohana hooks | Boolean | `True` | No | `True` | `True` |
| `LOG_THRESHOLD` | Logging level | Integer | `2` | No | `4` | `1` |
| `LOG_DIRECTORY` | Log file directory | String | None | No | `/tmp/logs/` | `/var/log/dgapi/` |
| `DISPLAY_ERRORS` | Show error pages | Boolean | `True` | No | `True` | `False` |
| `RENDER_STATS` | Show performance stats | Boolean | `True` | No | `True` | `False` |
| `RESTFUL_DEFAULT_RESPONSE` | Default API response type | String | `html` | No | `dbg` | `xml` |
| `RESTFUL_CACHING` | Enable API caching | Boolean | None | No | `False` | `True` |
| `RESTFUL_CACHING_PREFIX` | Cache filename prefix | String | `hook_restful_` | No | `dev_cache_` | `prod_cache_` |

---

## Environment-Specific Configurations

### Development Environment

```ini
# ===========================================
# platform-dgapi Development Configuration
# ===========================================

# Database Configuration
DATABASE_PERSISTENCY=False
DATABASE_PREFIXES=dev

# Development database
DEV_MYSQL_USER=dgapi_dev
DEV_MYSQL_PASSWORD=DevPassword123
DEV_MYSQL_HOST=localhost
DEV_MYSQL_SCHEMA=dgapi_development

# Kohana Framework Settings
KOHANA_SITE_DOMAIN=http://localhost:8080/
KOHANA_INTERNAL_CACHE=0
KOHANA_INTERNAL_CACHE_PATH=/tmp/dgapi-cache/
KOHANA_INTERNAL_CACHE_ENCRYPT=False
KOHANA_OUTPUT_COMPRESSION=0

# Application Settings
TIMEZONE_DEFAULT=-05:00
SITE_PROTOCOL=http
GLOBAL_XSS_FILTERING=True
ENABLE_HOOKS=True

# Debugging - Verbose for development
LOG_THRESHOLD=4
LOG_DIRECTORY=/tmp/dgapi-logs/
DISPLAY_ERRORS=True
RENDER_STATS=True

# RESTful API Settings
RESTFUL_DEFAULT_RESPONSE=dbg
RESTFUL_CACHING=False
RESTFUL_CACHING_PREFIX=dev_cache_
RESTFUL_AUTO_SEND_HEADER=True

# XML Settings
XML_FORMAT_OUTPUT=True
XML_RECOVER=True

# Version Info
VERSION_MA=2
VERSION_MI=5
VERSION_MIN=0
BUILD_ID=development
```

### Staging Environment

```ini
# ===========================================
# platform-dgapi Staging Configuration
# ===========================================

# Database Configuration
DATABASE_PERSISTENCY=True
DATABASE_PREFIXES=staging

# Staging database
STAGING_MYSQL_USER=dgapi_staging
STAGING_MYSQL_PASSWORD=${STAGING_DB_PASSWORD}
STAGING_MYSQL_HOST=staging-mysql.internal.example.com
STAGING_MYSQL_SCHEMA=dgapi_staging

# Kohana Framework Settings
KOHANA_SITE_DOMAIN=https://api-staging.example.com/
KOHANA_INTERNAL_CACHE=1800
KOHANA_INTERNAL_CACHE_PATH=/var/cache/dgapi/
KOHANA_INTERNAL_CACHE_ENCRYPT=True
KOHANA_OUTPUT_COMPRESSION=4

# Application Settings
TIMEZONE_DEFAULT=+00:00
SITE_PROTOCOL=https
GLOBAL_XSS_FILTERING=True
ENABLE_HOOKS=True

# Debugging - Moderate for staging
LOG_THRESHOLD=3
LOG_DIRECTORY=/var/log/dgapi/
DISPLAY_ERRORS=True
RENDER_STATS=True

# RESTful API Settings
RESTFUL_DEFAULT_RESPONSE=xml
RESTFUL_CACHING=True
RESTFUL_CACHING_PREFIX=staging_cache_
RESTFUL_AUTO_SEND_HEADER=True

# XML Settings
XML_FORMAT_OUTPUT=True
XML_RECOVER=True

# Version Info
VERSION_MA=2
VERSION_MI=5
VERSION_MIN=0
BUILD_ID=staging-${CI_COMMIT_SHORT_SHA}
```

### Production Environment

```ini
# ===========================================
# platform-dgapi Production Configuration
# ===========================================

# Database Configuration
DATABASE_PERSISTENCY=True
DATABASE_PREFIXES=primary,replica

# Primary database (read-write)
PRIMARY_MYSQL_USER=dgapi_primary
PRIMARY_MYSQL_PASSWORD=${PRIMARY_DB_PASSWORD}
PRIMARY_MYSQL_HOST=primary-mysql.internal.example.com
PRIMARY_MYSQL_SCHEMA=dgapi_production

# Replica database (read-only)
REPLICA_MYSQL_USER=dgapi_replica
REPLICA_MYSQL_PASSWORD=${REPLICA_DB_PASSWORD}
REPLICA_MYSQL_HOST=replica-mysql.internal.example.com
REPLICA_MYSQL_SCHEMA=dgapi_production

# Kohana Framework Settings
KOHANA_SITE_DOMAIN=https://api.example.com/
KOHANA_INTERNAL_CACHE=3600
KOHANA_INTERNAL_CACHE_PATH=/var/cache/dgapi/
KOHANA_INTERNAL_CACHE_ENCRYPT=True
KOHANA_OUTPUT_COMPRESSION=6

# Application Settings
TIMEZONE_DEFAULT=+00:00
SITE_PROTOCOL=https
INTERNAL_CACHE_KEY=${SECURE_CACHE_ENCRYPTION_KEY}
GLOBAL_XSS_FILTERING=True
ENABLE_HOOKS=True

# Debugging - Minimal for production
LOG_THRESHOLD=1
LOG_DIRECTORY=/var/log/dgapi/
DISPLAY_ERRORS=False
RENDER_STATS=False

# RESTful API Settings
RESTFUL_DEFAULT_RESPONSE=xml
RESTFUL_CACHING=True
RESTFUL_CACHING_PREFIX=prod_cache_
RESTFUL_AUTO_SEND_HEADER=True

# XML Settings
XML_FORMAT_OUTPUT=False
XML_RECOVER=False

# Version Info
VERSION_MA=2
VERSION_MI=5
VERSION_MIN=3
BUILD_ID=${RELEASE_TAG}
```

---

## Docker Configuration

### Dockerfile

```dockerfile
FROM php:8.1-apache

# Install required PHP extensions
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    && docker-php-ext-install xml \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure Apache
RUN a]mod rewrite
COPY apache-config.conf /etc/apache2/sites-available/000-default.conf

# Create cache and log directories
RUN mkdir -p /var/cache/dgapi /var/log/dgapi \
    && chown -R www-data:www-data /var/cache/dgapi /var/log/dgapi

# Copy application code
COPY --chown=www-data:www-data . /var/www/html/

# Set working directory
WORKDIR /var/www/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["apache2-foreground"]
```

### Docker Compose Configuration

```yaml
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
      # Database Configuration
      DATABASE_PERSISTENCY: "True"
      DATABASE_PREFIXES: "main"
      MAIN_MYSQL_USER: "${DB_USER:-dgapi}"
      MAIN_MYSQL_PASSWORD: "${DB_PASSWORD}"
      MAIN_MYSQL_HOST: "mysql"
      MAIN_MYSQL_SCHEMA: "${DB_SCHEMA:-dgapi}"
      
      # Kohana Settings
      KOHANA_SITE_DOMAIN: "http://localhost:8080/"
      KOHANA_INTERNAL_CACHE: "3600"
      KOHANA_INTERNAL_CACHE_PATH: "/var/cache/dgapi/"
      KOHANA_INTERNAL_CACHE_ENCRYPT: "True"
      KOHANA_OUTPUT_COMPRESSION: "6"
      
      # Application Settings
      TIMEZONE_DEFAULT: "+00:00"
      SITE_PROTOCOL: "http"
      GLOBAL_XSS_FILTERING: "True"
      LOG_THRESHOLD: "2"
      LOG_DIRECTORY: "/var/log/dgapi/"
      DISPLAY_ERRORS: "False"
      RENDER_STATS: "False"
      
      # RESTful API
      RESTFUL_DEFAULT_RESPONSE: "xml"
      RESTFUL_CACHING: "True"
      
      # Security
      INTERNAL_CACHE_KEY: "${CACHE_ENCRYPTION_KEY}"
    volumes:
      - dgapi-cache:/var/cache/dgapi
      - dgapi-logs:/var/log/dgapi
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - dgapi-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  mysql:
    image: mysql:8.0
    container_name: dgapi-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: "${MYSQL_ROOT_PASSWORD}"
      MYSQL_DATABASE: "${DB_SCHEMA:-dgapi}"
      MYSQL_USER: "${DB_USER:-dgapi}"
      MYSQL_PASSWORD: "${DB_PASSWORD}"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - dgapi-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

volumes:
  dgapi-cache:
  dgapi-logs:
  mysql-data:

networks:
  dgapi-network:
    driver: bridge
```

### Kubernetes Configuration

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: dgapi-config
  namespace: dgapi
data:
  DATABASE_PERSISTENCY: "True"
  DATABASE_PREFIXES: "primary,replica"
  KOHANA_SITE_DOMAIN: "https://api.example.com/"
  KOHANA_INTERNAL_CACHE: "3600"
  KOHANA_INTERNAL_CACHE_PATH: "/var/cache/dgapi/"
  KOHANA_INTERNAL_CACHE_ENCRYPT: "True"
  KOHANA_OUTPUT_COMPRESSION: "6"
  TIMEZONE_DEFAULT: "+00:00"
  SITE_PROTOCOL: "https"
  GLOBAL_XSS_FILTERING: "True"
  ENABLE_HOOKS: "True"
  LOG_THRESHOLD: "1"
  LOG_DIRECTORY: "/var/log/dgapi/"
  DISPLAY_ERRORS: "False"
  RENDER_STATS: "False"
  RESTFUL_DEFAULT_RESPONSE: "xml"
  RESTFUL_CACHING: "True"
  RESTFUL_CACHING_PREFIX: "prod_cache_"
  XML_FORMAT_OUTPUT: "False"
  XML_RECOVER: "False"

---
apiVersion: v1
kind: Secret
metadata:
  name: dgapi-secrets
  namespace: dgapi
type: Opaque
stringData:
  PRIMARY_MYSQL_USER: "dgapi_primary"
  PRIMARY_MYSQL_PASSWORD: "YourSecurePassword123!"
  PRIMARY_MYSQL_HOST: "primary-mysql.database.svc.cluster.local"
  PRIMARY_MYSQL_SCHEMA: "dgapi_production"
  REPLICA_MYSQL_USER: "dgapi_replica"
  REPLICA_MYSQL_PASSWORD: "YourSecurePassword456!"
  REPLICA_MYSQL_HOST: "replica-mysql.database.svc.cluster.local"
  REPLICA_MYSQL_SCHEMA: "dgapi_production"
  INTERNAL_CACHE_KEY: "your-secure-48-character-encryption-key-here-abc"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dgapi
  namespace: dgapi
  labels:
    app: dgapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dgapi
  template:
    metadata:
      labels:
        app: dgapi
    spec:
      containers:
        - name: dgapi
          image: your-registry/platform-dgapi:latest
          ports:
            - containerPort: 80
          envFrom:
            - configMapRef:
                name: dgapi-config
            - secretRef:
                name: dgapi-secrets
          volumeMounts:
            - name: cache-volume
              mountPath: /var/cache/dgapi
            - name: log-volume
              mountPath: /var/log/dgapi
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
      volumes:
        - name: cache-volume
          emptyDir: {}
        - name: log-volume
          emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: dgapi-service
  namespace: dgapi
spec:
  selector:
    app: dgapi
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
```

---

## Security Considerations

### Sensitive Configuration Values

The following configuration values contain sensitive information and require special handling:

| Variable | Sensitivity Level | Recommendations |
|----------|------------------|-----------------|
| `{prefix}.mysql_password` | **Critical** | Store in secrets manager (Vault, AWS Secrets Manager, K8s Secrets) |
| `{prefix}.mysql_user` | High | Use service accounts with minimal privileges |
| `internal_cache_key` | **Critical** | Generate unique key per environment, rotate regularly |
| `{prefix}.mysql_host` | Medium | Use internal DNS names, restrict network access |

### Security Best Practices

1. **Never Commit Secrets**: Use `.env.example` files with placeholder values. Add `.env` to `.gitignore`.

2. **Rotate Credentials Regularly**: Implement automated credential rotation for database passwords and encryption keys.

3. **Use Secrets Management**:
   ```bash
   # Example: Using HashiCorp Vault
   vault kv put secret/dgapi/production \
     PRIMARY_MYSQL_PASSWORD="NewSecurePassword" \
     INTERNAL_CACHE_KEY="$(openssl rand -hex 24)"
   ```

4. **Generate Secure Cache Keys**:
   ```bash
   # Generate a secure 48-character cache encryption key
   openssl rand -hex 24
   ```

5. **Disable Debug Features in Production**:
   ```ini
   DISPLAY_ERRORS=False
   RENDER_STATS=False
   LOG_THRESHOLD=1
   RESTFUL_DEFAULT_RESPONSE=xml  # Not 'dbg'
   ```

6. **Enable XSS Filtering**:
   ```ini
   GLOBAL_XSS_FILTERING=True
   ```

7. **Use HTTPS in Production**:
   ```ini
   SITE_PROTOCOL=https
   KOHANA_SITE_DOMAIN=https://api.example.com/
   ```

8. **Restrict Database Permissions**:
   ```sql
   -- Create read-only user for replica
   CREATE USER 'dgapi_replica'@'%' IDENTIFIED BY 'password';
   GRANT SELECT ON dgapi_production.* TO 'dgapi_replica'@'%';
   
   -- Create read-write user for primary
   CREATE USER 'dgapi_primary'@'%' IDENTIFIED BY 'password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON dgapi_production.* TO 'dgapi_primary'@'%';
   ```

---

## Troubleshooting Common Configuration Issues

### Database Connection Failures

**Symptom**: Application fails to connect to database with connection refused errors.

**Solutions**:
1. Verify MySQL host is accessible:
   ```bash
   telnet ${MYSQL_HOST} 3306
   ```
2. Check credentials are correct:
   ```bash
   mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_SCHEMA}
   ```
3. Ensure database prefix is included in `DATABASE_PREFIXES`:
   ```ini
   DATABASE_PREFIXES=main  # Must include all used prefixes
   MAIN_MYSQL_HOST=...     # Prefix must match
   ```

### Cache Permission Errors

**Symptom**: Application throws errors about unable to write to cache directory.

**Solutions**:
1. Verify cache directory exists and has correct permissions:
   ```bash
   mkdir -p /var/cache/dgapi
   chown -R www-data:www-data /var/cache/dgapi
   chmod 755 /var/cache/dgapi
   ```
2. Check `KOHANA_INTERNAL_CACHE_PATH` is set correctly
3. In containerized environments, ensure volume is mounted properly

### XML Parsing Errors

**Symptom**: XML responses are malformed or contain errors.

**Solutions**:
1. Enable XML recovery mode for tolerant parsing:
   ```ini
   XML_RECOVER=True
   ```
2. Verify encoding settings match your data:
   ```ini
   XML_ENCODING=UTF-8
   ```
3. For debugging, enable formatted output:
   ```ini
   XML_FORMAT_OUTPUT=True
   ```

### Performance Issues

**Symptom**: Slow API response times.

**Solutions**:
1. Enable caching:
   ```ini
   KOHANA_INTERNAL_CACHE=3600
   RESTFUL_CACHING=True
   ```
2. Enable output compression:
   ```ini
   KOHANA_OUTPUT_COMPRESSION=6
   ```
3. Use persistent database connections:
   ```ini
   DATABASE_PERSISTENCY=True
   ```
4. Reduce logging verbosity:
   ```ini
   LOG_THRESHOLD=1
   ```

### Missing Routes

**Symptom**: 404 errors for valid API endpoints.

**Solutions**:
1. Verify default route is configured:
   ```ini
   ROUTES_DEFAULT=info
   ```
2. Check `index_page` setting if using URL rewriting:
   ```ini
   INDEX_PAGE=
   ```
3. Ensure Apache/Nginx rewrite rules are configured correctly

---

## Example .env File

```ini
# ===========================================
# platform-dgapi Environment Configuration
# ===========================================
# Copy this file to .env and configure for your environment
# NEVER commit .env files containing real credentials

# -----------------------------------------
# Database Configuration
# -----------------------------------------
DATABASE_PERSISTENCY=True
DATABASE_PREFIXES=main

# Main Database Connection
MAIN_MYSQL_USER=dgapi_user
MAIN_MYSQL_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD
MAIN_MYSQL_HOST=localhost
MAIN_MYSQL_SCHEMA=dgapi

# -----------------------------------------
# Kohana Framework Settings
# -----------------------------------------
KOHANA_SITE_DOMAIN=http://localhost:8080/
KOHANA_INTERNAL_CACHE=3600
KOHANA_INTERNAL_CACHE_PATH=/var/cache/dgapi/
KOHANA_INTERNAL_CACHE_ENCRYPT=True
KOHANA_OUTPUT_COMPRESSION=6

# -----------------------------------------
# Application Settings
# -----------------------------------------
TIMEZONE_DEFAULT=+00:00
SITE_PROTOCOL=https
INDEX_PAGE=
URL_SUFFIX=
EXTENSION_PREFIX=RM_

# -----------------------------------------
# Security Settings
# -----------------------------------------
# Generate with: openssl rand -hex 24
INTERNAL_CACHE_KEY=CHANGE_ME_TO_48_CHARACTER_SECURE_KEY_HERE
GLOBAL_XSS_FILTERING=True
ENABLE_HOOKS=True

# -----------------------------------------
# Logging and Debugging
# -----------------------------------------
# 0=disabled, 1=errors, 2=warnings, 3=notices, 4=debugging
LOG_THRESHOLD=2
LOG_DIRECTORY=/var/log/dgapi/
DISPLAY_ERRORS=False
RENDER_STATS=False

# -----------------------------------------
# RESTful API Configuration
# -----------------------------------------
RESTFUL_DEFAULT_RESPONSE=xml
RESTFUL_AUTO_SEND_HEADER=True
RESTFUL_CACHING=True
RESTFUL_CACHING_PREFIX=dgapi_cache_

# -----------------------------------------
# XML Configuration
# -----------------------------------------
XML_VERSION=1.0
XML_ENCODING=UTF-8
XML_FORMAT_OUTPUT=True
XML_RECOVER=True

# -----------------------------------------
# Version Information
# -----------------------------------------
VERSION_MA=2
VERSION_MI=5
VERSION_MIN=0
BUILD_ID=local-dev

# -----------------------------------------
# Routes Configuration
# -----------------------------------------
ROUTES_DEFAULT=info
```

---

This configuration guide provides comprehensive documentation for deploying and configuring the platform-dgapi service across different environments. For additional support or questions, consult the development team or refer to the Kohana framework documentation.