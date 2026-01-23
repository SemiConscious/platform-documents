# Configuration Reference

## Platform Service Gateway

This comprehensive configuration guide documents all configuration variables, settings, and environment-specific configurations for the Platform Service Gateway (platform-service-gateway). The Service Gateway acts as a centralized routing and API management layer, handling HTTP data connector requests, database connections, caching, and RESTful API responses.

---

## Table of Contents

1. [Configuration Files Overview](#configuration-files-overview)
2. [Environment Variables](#environment-variables)
3. [Database Configuration](#database-configuration)
4. [Cache Configuration](#cache-configuration)
5. [RESTful API Settings](#restful-api-settings)
6. [Route Configuration](#route-configuration)
7. [Platform-Specific Settings](#platform-specific-settings)
8. [Environment-Specific Configurations](#environment-specific-configurations)
9. [Security Considerations](#security-considerations)
10. [Example Configuration Files](#example-configuration-files)
11. [Troubleshooting](#troubleshooting)

---

## Configuration Files Overview

The Platform Service Gateway uses a multi-layered configuration approach combining environment variables, configuration files, and runtime settings accessed through the hAPI (Host API) interface.

### Configuration Sources

| Source | Priority | Description |
|--------|----------|-------------|
| Environment Variables | Highest | Override all other settings; used for deployment-specific values |
| hAPI Configuration | High | Runtime configuration accessed via `hAPI->Get()`, `hAPI->getDatabaseUser()`, etc. |
| Application Config Files | Medium | PHP configuration arrays in `APPPATH/config/` directory |
| Framework Defaults | Lowest | Built-in defaults provided by the Kohana framework |

### Configuration File Structure

```
APPPATH/
├── config/
│   ├── database.php      # Database connection settings
│   ├── cache.php         # Caching configuration
│   ├── restful.php       # RESTful API settings
│   └── routes.php        # URL routing configuration
├── cache/                # File-based cache storage
└── logs/                 # Application log files
```

---

## Environment Variables

### Complete Variable Reference

The following table documents all configuration variables available for the Platform Service Gateway:

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `RESTRICTED_HOSTS` | String (CSV) | `217.144.145.0/24,79.99.77.48/30,84.45.30.0/23,84.45.39.144/30,185.185.79.79/32,217.144.149.0/28,217.144.154.104/30` | **Yes** | Comma-separated list of IP ranges in CIDR notation to block for HTTP data connector requests |
| `LOG_LEVEL` | String | `DEBUG` (dev) / `INFO` (prod) | No | Syslog logging level controlling verbosity of output |
| `RM_SQL_RW_HOST` | String | None | **Yes** | SQL read/write host for primary database connections |
| `SearchDomain` | String | None | No | Domain suffix for service gateway URL construction |
| `packagename` | String | `rm-servicegateway` | No | Package name identifier for logging and metrics |

### Security-Sensitive Variables

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `ServiceGateway.database.user` | String | None | **Yes** | Database username for ServiceGateway connection |
| `ServiceGateway.database.pass` | String | None | **Yes** | Database password for ServiceGateway connection |
| `ServiceGateway.database.host` | String | None | **Yes** | Database host for ServiceGateway connection |
| `internal_cache_key` | String | `qwf89phasviouhasd89pyhq4wed…234123&$^&%^$` | No | Encryption key for internal cache (when encryption enabled) |

### Salesforce Integration Variables

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `enablesfauthcache` | Boolean | `True` | No | Enable Salesforce session ID caching for performance |
| `warnsfquerytime` | Integer | `5` | No | Maximum Salesforce query time (seconds) before raising syslog warnings |
| `sfauthcacheverifymins` | Integer | `0` | No | Minutes before verifying cached Salesforce session (0 = always verify) |

---

## Database Configuration

The Service Gateway supports multiple database connection configurations with connection pooling, benchmarking, and query caching capabilities.

### Primary Database Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `database.connection.type` | String | `mysqli` | No | Database connection driver type |
| `database.connection.database` | String | `ServiceGateway` | No | Database name to connect to |
| `database.character_set` | String | `utf8` | No | Character set encoding for database connections |
| `database.table_prefix` | String | Empty | No | Prefix for all database table names |
| `database.benchmark` | Boolean | `True` | No | Enable database query benchmarking for performance monitoring |
| `database.persistent` | Boolean | `True` | No | Enable persistent database connections |
| `database.object` | Boolean | `False` | No | Return query results as objects instead of arrays |
| `database.cache` | Boolean | `False` | No | Enable database query result caching |
| `database.escape` | Boolean | `True` | No | Enable automatic query builder escaping for SQL injection prevention |

### Database Configuration Example

```php
<?php
// APPPATH/config/database.php

return array(
    'default' => array(
        'benchmark'     => TRUE,
        'persistent'    => TRUE,
        'connection'    => array(
            'type'     => 'mysqli',
            'user'     => '', // Set via hAPI->getDatabaseUser('ServiceGateway')
            'pass'     => '', // Set via hAPI->getDatabasePass('ServiceGateway')
            'host'     => '', // Set via hAPI->getDatabaseHost('ServiceGateway')
            'port'     => 3306,
            'socket'   => FALSE,
            'database' => 'ServiceGateway',
        ),
        'character_set' => 'utf8',
        'table_prefix'  => '',
        'object'        => FALSE,
        'cache'         => FALSE,
        'escape'        => TRUE,
    ),
);
```

### Database Connection Flow

1. Application requests database credentials via hAPI
2. hAPI retrieves credentials from secure configuration store
3. Connection established using mysqli driver with persistent connections
4. Query benchmarking enabled for performance monitoring
5. Automatic escaping applied to prevent SQL injection

---

## Cache Configuration

The Service Gateway implements a dual-cache strategy with file-based caching for durability and memcache for high-performance scenarios.

### File-Based Cache Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `cache.sgapi_file.driver` | String | `file` | No | Cache backend driver identifier |
| `cache.sgapi_file.params` | String | `APPPATH/cache` | No | File system path for cache storage |
| `cache.sgapi_file.lifetime` | Integer | `600` | No | Cache entry lifetime in seconds (10 minutes) |
| `cache.sgapi_file.requests` | Integer | `-1` | No | Number of requests before garbage collection (-1 disables automatic GC) |

### Memcache Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `cache.sgapi_mem.driver` | String | `memcache` | No | Cache backend driver identifier |
| `cache.sgapi_mem.lifetime` | Integer | `600` | No | Cache entry lifetime in seconds |
| `cache.sgapi_mem.compression` | Boolean | `False` | No | Enable Zlib compression for stored values |
| `cache.sgapi_mem.servers.host` | String | `localhost` | No | Memcache server hostname |
| `cache.sgapi_mem.servers.port` | Integer | `11211` | No | Memcache server port |
| `cache.sgapi_mem.servers.persistent` | Boolean | `False` | No | Enable persistent memcache connections |

### Internal Cache Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `internal_cache` | Integer/Boolean | `0` | No | Internal framework cache duration in seconds (0 or false disables) |
| `internal_cache_path` | String | `APPPATH/cache/` | No | Directory path for internal cache storage |
| `internal_cache_encrypt` | Boolean | `False` | No | Enable encryption for internal cache files |
| `internal_cache_key` | String | See default | No | Encryption key for internal cache |

### Cache Configuration Example

```php
<?php
// APPPATH/config/cache.php

return array(
    'sgapi_file' => array(
        'driver'   => 'file',
        'params'   => APPPATH . 'cache',
        'lifetime' => 600,
        'requests' => -1,
    ),
    'sgapi_mem' => array(
        'driver'      => 'memcache',
        'lifetime'    => 600,
        'compression' => FALSE,
        'servers'     => array(
            array(
                'host'       => 'localhost',
                'port'       => 11211,
                'persistent' => FALSE,
            ),
        ),
    ),
);
```

---

## RESTful API Settings

The Service Gateway provides RESTful API capabilities with configurable MIME type handling and response formats.

### RESTful Configuration Variables

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `restful.supported_mimes` | Array | See below | No | Map of supported MIME type extensions and their regex patterns |
| `restful.default_response` | String | `html` | No | Default response format when no extension specified |
| `restful.auto_send_header` | Boolean | `True` | No | Automatically send appropriate Content-Type header |

### Default MIME Type Configuration

```php
<?php
// Default supported_mimes configuration

$supported_mimes = array(
    'html' => '/(.+)(\\.html?)/',  // Matches .htm and .html
    'xml'  => '/(.+)(\\.xml)/',    // Matches .xml
    'dbg'  => '/(.+)(\\.dbg)/',    // Matches .dbg (debug format)
);
```

### Adding Custom MIME Types

To add support for JSON responses, extend the configuration:

```php
<?php
// APPPATH/config/restful.php

return array(
    'supported_mimes' => array(
        'html' => '/(.+)(\\.html?)/',
        'xml'  => '/(.+)(\\.xml)/',
        'json' => '/(.+)(\\.json)/',
        'dbg'  => '/(.+)(\\.dbg)/',
    ),
    'default_response'  => 'html',
    'auto_send_header'  => TRUE,
);
```

---

## Route Configuration

### Site and URL Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `site_domain` | String | `http://servicegateway{SearchDomain}/` | No | Base URL path of the web site |
| `site_protocol` | String | None | No | Force a default protocol (http or https) |
| `index_page` | String | Empty | No | Front controller filename (empty when using URL rewriting) |
| `url_suffix` | String | Empty | No | Fake file extension added to generated URLs |

### URL Construction Example

```php
// With SearchDomain = ".example.com"
// site_domain becomes: http://servicegateway.example.com/

// URL generation example:
$url = url::site('api/v1/resource');
// Result: http://servicegateway.example.com/api/v1/resource
```

---

## Platform-Specific Settings

### Framework Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `enable_hooks` | Boolean | `True` | No | Enable Kohana hook system for extensibility |
| `extension_prefix` | String | `RM_` | No | Filename prefix for framework extension classes |
| `global_xss_filtering` | Boolean | `False` | No | Enable global XSS filtering of GET, POST, and SERVER data |
| `output_compression` | Integer/Boolean | `False` | No | Gzip compression level (1-9) or false to disable |
| `render_stats` | Boolean | `True` | No | Enable statistics rendering in final output |
| `StatisticsEnabled` | Boolean | `False` | No | Enable statistics collection using caching subsystem |

### Logging Settings

| Variable Name | Type | Default | Required | Description |
|---------------|------|---------|----------|-------------|
| `log_threshold` | Integer | `0` | No | Kohana log threshold: 0=disabled, 1=errors, 2=warnings, 3=notices, 4=debug |
| `log_directory` | String | `APPPATH/logs` | No | Directory path for Kohana message logs |
| `display_errors` | Boolean | `False` | No | Enable Kohana error page display in browser |

### Host Restriction Configuration

The `RESTRICTED_HOSTS` variable is critical for security, preventing the Service Gateway from making HTTP requests to internal network ranges:

```
# Default restricted IP ranges (CIDR notation)
RESTRICTED_HOSTS=217.144.145.0/24,79.99.77.48/30,84.45.30.0/23,84.45.39.144/30,185.185.79.79/32,217.144.149.0/28,217.144.154.104/30
```

| CIDR Range | IP Range | Purpose |
|------------|----------|---------|
| `217.144.145.0/24` | 217.144.145.0 - 217.144.145.255 | Internal infrastructure |
| `79.99.77.48/30` | 79.99.77.48 - 79.99.77.51 | Management network |
| `84.45.30.0/23` | 84.45.30.0 - 84.45.31.255 | Internal services |
| `84.45.39.144/30` | 84.45.39.144 - 84.45.39.147 | Administrative access |
| `185.185.79.79/32` | 185.185.79.79 (single IP) | Specific internal host |
| `217.144.149.0/28` | 217.144.149.0 - 217.144.149.15 | Database servers |
| `217.144.154.104/30` | 217.144.154.104 - 217.144.154.107 | Core infrastructure |

---

## Environment-Specific Configurations

### Development Environment

```ini
# Development Configuration
LOG_LEVEL=DEBUG
log_threshold=4
display_errors=TRUE
database.benchmark=TRUE
render_stats=TRUE
StatisticsEnabled=TRUE
internal_cache=0
cache.sgapi_file.lifetime=60
cache.sgapi_mem.lifetime=60
enablesfauthcache=FALSE
sfauthcacheverifymins=0
global_xss_filtering=FALSE
output_compression=FALSE

# Database (local development)
ServiceGateway.database.host=localhost
ServiceGateway.database.user=dev_user
ServiceGateway.database.pass=dev_password_here
RM_SQL_RW_HOST=localhost

# Cache (local memcache)
cache.sgapi_mem.servers.host=localhost
cache.sgapi_mem.servers.port=11211
```

### Staging Environment

```ini
# Staging Configuration
LOG_LEVEL=INFO
log_threshold=2
display_errors=FALSE
database.benchmark=TRUE
render_stats=FALSE
StatisticsEnabled=TRUE
internal_cache=300
cache.sgapi_file.lifetime=300
cache.sgapi_mem.lifetime=300
enablesfauthcache=TRUE
sfauthcacheverifymins=5
global_xss_filtering=TRUE
output_compression=6

# Database (staging cluster)
ServiceGateway.database.host=staging-db.internal
ServiceGateway.database.user=staging_user
ServiceGateway.database.pass=${STAGING_DB_PASSWORD}
RM_SQL_RW_HOST=staging-db-rw.internal

# Cache (staging memcache cluster)
cache.sgapi_mem.servers.host=staging-cache.internal
cache.sgapi_mem.servers.port=11211
cache.sgapi_mem.compression=TRUE
```

### Production Environment

```ini
# Production Configuration
LOG_LEVEL=INFO
log_threshold=1
display_errors=FALSE
database.benchmark=FALSE
render_stats=FALSE
StatisticsEnabled=TRUE
internal_cache=600
cache.sgapi_file.lifetime=600
cache.sgapi_mem.lifetime=600
enablesfauthcache=TRUE
sfauthcacheverifymins=10
warnsfquerytime=3
global_xss_filtering=TRUE
output_compression=9

# Database (production cluster)
ServiceGateway.database.host=prod-db.internal
ServiceGateway.database.user=prod_user
ServiceGateway.database.pass=${PROD_DB_PASSWORD}
RM_SQL_RW_HOST=prod-db-rw.internal

# Cache (production memcache cluster)
cache.sgapi_mem.servers.host=prod-cache.internal
cache.sgapi_mem.servers.port=11211
cache.sgapi_mem.compression=TRUE
cache.sgapi_mem.servers.persistent=TRUE

# Security
RESTRICTED_HOSTS=217.144.145.0/24,79.99.77.48/30,84.45.30.0/23,84.45.39.144/30,185.185.79.79/32,217.144.149.0/28,217.144.154.104/30,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
internal_cache_encrypt=TRUE
internal_cache_key=${INTERNAL_CACHE_ENCRYPTION_KEY}
```

---

## Security Considerations

### Sensitive Configuration Values

The following variables contain sensitive information and must be protected:

| Variable | Sensitivity | Protection Method |
|----------|-------------|-------------------|
| `ServiceGateway.database.pass` | **Critical** | Store in secrets manager, never commit to VCS |
| `ServiceGateway.database.user` | High | Use environment variables or secrets manager |
| `internal_cache_key` | **Critical** | Generate unique key per environment, store securely |
| `RM_SQL_RW_HOST` | Medium | Internal hostnames, restrict access to configuration |

### Security Best Practices

1. **Never commit credentials to version control**
   - Use environment variables or external secrets managers
   - Add `.env` files to `.gitignore`

2. **Use strong, unique values for encryption keys**
   ```bash
   # Generate a secure internal_cache_key
   openssl rand -base64 32
   ```

3. **Restrict host access appropriately**
   - Always include RFC 1918 private ranges in `RESTRICTED_HOSTS` for production
   - Add: `10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`

4. **Enable XSS filtering in production**
   ```ini
   global_xss_filtering=TRUE
   ```

5. **Disable error display in production**
   ```ini
   display_errors=FALSE
   log_threshold=1
   ```

6. **Use encrypted cache in production**
   ```ini
   internal_cache_encrypt=TRUE
   internal_cache_key=${SECURE_GENERATED_KEY}
   ```

### Database Security

- Use separate database users per environment
- Apply principle of least privilege to database accounts
- Enable SSL/TLS for database connections in production
- Regularly rotate database passwords

---

## Example Configuration Files

### Complete .env File

```ini
# =============================================================================
# Platform Service Gateway - Environment Configuration
# =============================================================================
# Environment: production
# Last Updated: 2024-01-15
# =============================================================================

# -----------------------------------------------------------------------------
# Core Settings
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO
packagename=rm-servicegateway
SearchDomain=.example.com

# -----------------------------------------------------------------------------
# Security - Host Restrictions
# -----------------------------------------------------------------------------
# Block internal network ranges and RFC 1918 private addresses
RESTRICTED_HOSTS=217.144.145.0/24,79.99.77.48/30,84.45.30.0/23,84.45.39.144/30,185.185.79.79/32,217.144.149.0/28,217.144.154.104/30,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
RM_SQL_RW_HOST=prod-db-rw.internal.example.com
ServiceGateway.database.host=prod-db.internal.example.com
ServiceGateway.database.user=sg_prod_user
ServiceGateway.database.pass=REPLACE_WITH_SECURE_PASSWORD

# Database connection settings
database.benchmark=FALSE
database.persistent=TRUE
database.connection.type=mysqli
database.connection.database=ServiceGateway
database.character_set=utf8
database.table_prefix=
database.object=FALSE
database.cache=FALSE
database.escape=TRUE

# -----------------------------------------------------------------------------
# Cache Configuration - File
# -----------------------------------------------------------------------------
cache.sgapi_file.driver=file
cache.sgapi_file.params=/var/www/app/cache
cache.sgapi_file.lifetime=600
cache.sgapi_file.requests=-1

# -----------------------------------------------------------------------------
# Cache Configuration - Memcache
# -----------------------------------------------------------------------------
cache.sgapi_mem.driver=memcache
cache.sgapi_mem.lifetime=600
cache.sgapi_mem.compression=TRUE
cache.sgapi_mem.servers.host=prod-cache.internal.example.com
cache.sgapi_mem.servers.port=11211
cache.sgapi_mem.servers.persistent=TRUE

# -----------------------------------------------------------------------------
# Internal Cache
# -----------------------------------------------------------------------------
internal_cache=600
internal_cache_path=/var/www/app/cache/
internal_cache_encrypt=TRUE
internal_cache_key=REPLACE_WITH_SECURE_32_BYTE_KEY

# -----------------------------------------------------------------------------
# Site Configuration
# -----------------------------------------------------------------------------
site_domain=https://servicegateway.example.com/
site_protocol=https
index_page=
url_suffix=

# -----------------------------------------------------------------------------
# RESTful API Settings
# -----------------------------------------------------------------------------
restful.default_response=html
restful.auto_send_header=TRUE

# -----------------------------------------------------------------------------
# Salesforce Integration
# -----------------------------------------------------------------------------
enablesfauthcache=TRUE
warnsfquerytime=3
sfauthcacheverifymins=10

# -----------------------------------------------------------------------------
# Framework Settings
# -----------------------------------------------------------------------------
enable_hooks=TRUE
extension_prefix=RM_
global_xss_filtering=TRUE
output_compression=9
render_stats=FALSE
StatisticsEnabled=TRUE

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
log_threshold=1
log_directory=/var/log/servicegateway
display_errors=FALSE
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  service-gateway:
    image: platform-service-gateway:latest
    container_name: service-gateway
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      - LOG_LEVEL=INFO
      - RESTRICTED_HOSTS=217.144.145.0/24,79.99.77.48/30,84.45.30.0/23,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
      - RM_SQL_RW_HOST=db
      - ServiceGateway.database.host=db
      - ServiceGateway.database.user=servicegateway
      - ServiceGateway.database.pass=${DB_PASSWORD}
      - cache.sgapi_mem.servers.host=memcached
      - cache.sgapi_mem.servers.port=11211
      - SearchDomain=.docker.local
    volumes:
      - cache_data:/var/www/app/cache
      - log_data:/var/log/servicegateway
    depends_on:
      - db
      - memcached
    networks:
      - service-network

  db:
    image: mysql:8.0
    container_name: service-gateway-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=ServiceGateway
      - MYSQL_USER=servicegateway
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    networks:
      - service-network

  memcached:
    image: memcached:1.6-alpine
    container_name: service-gateway-cache
    restart: unless-stopped
    command: memcached -m 256
    networks:
      - service-network

volumes:
  cache_data:
  log_data:
  db_data:

networks:
  service-network:
    driver: bridge
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: service-gateway-config
  namespace: platform
data:
  LOG_LEVEL: "INFO"
  RESTRICTED_HOSTS: "217.144.145.0/24,79.99.77.48/30,84.45.30.0/23,84.45.39.144/30,185.185.79.79/32,217.144.149.0/28,217.144.154.104/30,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
  SearchDomain: ".k8s.example.com"
  packagename: "rm-servicegateway"
  
  # Database settings (non-sensitive)
  database.benchmark: "FALSE"
  database.persistent: "TRUE"
  database.connection.type: "mysqli"
  database.connection.database: "ServiceGateway"
  database.character_set: "utf8"
  database.escape: "TRUE"
  
  # Cache settings
  cache.sgapi_file.driver: "file"
  cache.sgapi_file.lifetime: "600"
  cache.sgapi_mem.driver: "memcache"
  cache.sgapi_mem.lifetime: "600"
  cache.sgapi_mem.compression: "TRUE"
  
  # RESTful settings
  restful.default_response: "html"
  restful.auto_send_header: "TRUE"
  
  # Salesforce settings
  enablesfauthcache: "TRUE"
  warnsfquerytime: "3"
  sfauthcacheverifymins: "10"
  
  # Framework settings
  enable_hooks: "TRUE"
  global_xss_filtering: "TRUE"
  output_compression: "9"
  render_stats: "FALSE"
  log_threshold: "1"
  display_errors: "FALSE"
```

### Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: service-gateway-secrets
  namespace: platform
type: Opaque
stringData:
  ServiceGateway.database.user: "sg_prod_user"
  ServiceGateway.database.pass: "REPLACE_WITH_SECURE_PASSWORD"
  ServiceGateway.database.host: "mysql-primary.database.svc.cluster.local"
  RM_SQL_RW_HOST: "mysql-primary.database.svc.cluster.local"
  internal_cache_key: "REPLACE_WITH_SECURE_32_BYTE_KEY"
```

---

## Troubleshooting

### Common Configuration Issues

#### 1. Database Connection Failures

**Symptoms:**
- Application fails to start
- "Unable to connect to database" errors

**Diagnosis:**
```bash
# Check environment variables are set
env | grep -i servicegateway
env | grep -i RM_SQL

# Test database connectivity
mysql -h $ServiceGateway_database_host -u $ServiceGateway_database_user -p
```

**Solutions:**
- Verify `ServiceGateway.database.host`, `ServiceGateway.database.user`, and `ServiceGateway.database.pass` are correctly set
- Ensure the database server is accessible from the application server
- Check firewall rules allow connections on port 3306

#### 2. Cache Not Working

**Symptoms:**
- High database load
- Slow response times
- Cache hit rate of 0%

**Diagnosis:**
```bash
# Check memcache connectivity
echo "stats" | nc localhost 11211

# Verify cache directory permissions
ls -la /var/www/app/cache/
```

**Solutions:**
- Verify `cache.sgapi_mem.servers.host` and `cache.sgapi_mem.servers.port` are correct
- Ensure memcached service is running
- Check file cache directory has write permissions

#### 3. Restricted Hosts Blocking Legitimate Requests

**Symptoms:**
- HTTP data connector requests failing
- "Host restricted" error messages

**Diagnosis:**
```bash
# Review current RESTRICTED_HOSTS setting
echo $RESTRICTED_HOSTS

# Check if target IP falls within restricted ranges
# Use an online CIDR calculator to verify
```

**Solutions:**
- Review and adjust `RESTRICTED_HOSTS` to exclude legitimate external services
- Ensure internal ranges are still blocked for security

#### 4. Salesforce Authentication Issues

**Symptoms:**
- Frequent Salesforce re-authentication
- Slow Salesforce queries
- Syslog warnings about query times

**Diagnosis:**
```bash
# Check Salesforce cache settings
grep -i sfauth /var/log/servicegateway/*.log

# Review query timing warnings
grep -i warnsfquerytime /var/log/syslog
```

**Solutions:**
- Enable `enablesfauthcache=TRUE` for better performance
- Increase `sfauthcacheverifymins` to reduce verification overhead
- Review `warnsfquerytime` threshold and optimize slow queries

#### 5. XSS Filtering Causing Issues

**Symptoms:**
- Form submissions being rejected
- Data being incorrectly sanitized

**Diagnosis:**
```bash
# Check XSS filtering setting
grep -i xss_filtering /var/www/app/config/*.php
```

**Solutions:**
- For development, disable `global_xss_filtering`
- In production, review specific inputs that need raw handling
- Use framework-provided methods to bypass filtering for specific fields

### Log Analysis

Enable detailed logging for troubleshooting:

```ini
# Temporary debug settings
LOG_LEVEL=DEBUG
log_threshold=4
display_errors=TRUE
database.benchmark=TRUE
render_stats=TRUE
```

Review logs at:
- Syslog: `/var/log/syslog` or `/var/log/messages`
- Application logs: `APPPATH/logs/` (default: `/var/www/app/logs/`)

---

## Summary

This configuration reference provides comprehensive documentation for deploying and managing the Platform Service Gateway. Key points to remember:

1. **Always secure sensitive credentials** using environment variables or secrets managers
2. **Configure RESTRICTED_HOSTS** appropriately for your network topology
3. **Tune cache settings** based on your traffic patterns and infrastructure
4. **Use environment-specific configurations** for development, staging, and production
5. **Monitor logs and metrics** to identify configuration issues early

For additional support, consult the platform team or refer to the internal knowledge base.