# Configuration Guide

## Service: natterbox-wallboards

This comprehensive configuration guide documents all configuration variables, environment-specific settings, and best practices for deploying the natterbox-wallboards service across development, staging, and production environments.

---

## Configuration Overview

The natterbox-wallboards service is a real-time dashboard application designed to display call center metrics, agent status, queue information, and performance indicators from the Natterbox telephony platform. The service relies on a combination of environment variables, configuration files, and build-time settings to operate correctly.

### Configuration Architecture

The wallboards application follows a layered configuration approach:

1. **Environment Variables**: Runtime configuration for server settings, API endpoints, and feature flags
2. **Wallboard Configuration Files**: JSON/YAML files defining dashboard layouts, widgets, and data sources
3. **Build Configuration**: Webpack/Vite settings for bundling and optimization
4. **Theme Configuration**: Customizable styling and branding options

Configuration is loaded in the following priority order (highest to lowest):
- Environment variables
- `.env` files (environment-specific)
- Default configuration files
- Hardcoded defaults

---

## Environment Variables

### Core Application Settings

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `NODE_ENV` | Application environment mode | `string` | `development` | Yes | `production` |
| `PORT` | HTTP server listening port | `number` | `3000` | No | `8080` |
| `HOST` | Server bind address | `string` | `0.0.0.0` | No | `127.0.0.1` |
| `APP_NAME` | Application display name | `string` | `Natterbox Wallboards` | No | `Call Center Dashboard` |
| `APP_VERSION` | Application version identifier | `string` | `1.0.0` | No | `2.3.1` |
| `LOG_LEVEL` | Logging verbosity level | `string` | `info` | No | `debug`, `warn`, `error` |
| `LOG_FORMAT` | Log output format | `string` | `json` | No | `text`, `json` |
| `TIMEZONE` | Default timezone for displays | `string` | `UTC` | No | `Europe/London` |

### Natterbox API Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `NATTERBOX_API_URL` | Base URL for Natterbox API | `string` | - | Yes | `https://api.natterbox.com/v1` |
| `NATTERBOX_API_KEY` | API authentication key | `string` | - | Yes | `nb_live_xxxxxxxxxxxx` |
| `NATTERBOX_API_SECRET` | API secret for signing requests | `string` | - | Yes | `sk_xxxxxxxxxxxxxxxxxxxx` |
| `NATTERBOX_ORG_ID` | Organization identifier | `string` | - | Yes | `org_123456789` |
| `NATTERBOX_API_TIMEOUT` | API request timeout in milliseconds | `number` | `30000` | No | `60000` |
| `NATTERBOX_API_RETRY_ATTEMPTS` | Number of retry attempts for failed requests | `number` | `3` | No | `5` |
| `NATTERBOX_API_RETRY_DELAY` | Delay between retries in milliseconds | `number` | `1000` | No | `2000` |
| `NATTERBOX_WEBHOOK_SECRET` | Secret for validating incoming webhooks | `string` | - | No | `whsec_xxxxxxxxxxxx` |

### Real-Time Data Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `WEBSOCKET_URL` | WebSocket server URL for real-time updates | `string` | - | Yes | `wss://realtime.natterbox.com` |
| `WEBSOCKET_RECONNECT_INTERVAL` | Reconnection interval in milliseconds | `number` | `5000` | No | `3000` |
| `WEBSOCKET_MAX_RECONNECT_ATTEMPTS` | Maximum reconnection attempts | `number` | `10` | No | `20` |
| `WEBSOCKET_HEARTBEAT_INTERVAL` | Heartbeat ping interval in milliseconds | `number` | `30000` | No | `15000` |
| `DATA_REFRESH_INTERVAL` | Polling interval for non-realtime data | `number` | `60000` | No | `30000` |
| `CACHE_TTL` | Cache time-to-live in seconds | `number` | `300` | No | `600` |

### Database Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `DATABASE_URL` | Full database connection string | `string` | - | Yes | `postgresql://user:pass@host:5432/db` |
| `DATABASE_HOST` | Database server hostname | `string` | `localhost` | No | `db.example.com` |
| `DATABASE_PORT` | Database server port | `number` | `5432` | No | `5433` |
| `DATABASE_NAME` | Database name | `string` | `wallboards` | No | `natterbox_wallboards` |
| `DATABASE_USER` | Database username | `string` | - | Yes | `wallboards_user` |
| `DATABASE_PASSWORD` | Database password | `string` | - | Yes | `secure_password_123` |
| `DATABASE_SSL` | Enable SSL for database connections | `boolean` | `false` | No | `true` |
| `DATABASE_POOL_MIN` | Minimum connection pool size | `number` | `2` | No | `5` |
| `DATABASE_POOL_MAX` | Maximum connection pool size | `number` | `10` | No | `20` |

### Redis Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REDIS_URL` | Full Redis connection string | `string` | - | No | `redis://:password@host:6379/0` |
| `REDIS_HOST` | Redis server hostname | `string` | `localhost` | No | `redis.example.com` |
| `REDIS_PORT` | Redis server port | `number` | `6379` | No | `6380` |
| `REDIS_PASSWORD` | Redis authentication password | `string` | - | No | `redis_password_123` |
| `REDIS_DB` | Redis database index | `number` | `0` | No | `1` |
| `REDIS_TLS` | Enable TLS for Redis connections | `boolean` | `false` | No | `true` |
| `REDIS_KEY_PREFIX` | Prefix for all Redis keys | `string` | `wallboards:` | No | `nb_wb:` |

### Authentication Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `AUTH_ENABLED` | Enable authentication | `boolean` | `true` | No | `true` |
| `AUTH_PROVIDER` | Authentication provider type | `string` | `oauth2` | No | `saml`, `ldap`, `oauth2` |
| `AUTH_JWT_SECRET` | Secret key for JWT signing | `string` | - | Yes | `jwt_secret_key_min_32_chars` |
| `AUTH_JWT_EXPIRY` | JWT token expiry time | `string` | `24h` | No | `8h`, `7d` |
| `AUTH_SESSION_SECRET` | Secret for session encryption | `string` | - | Yes | `session_secret_min_32_chars` |
| `AUTH_SESSION_DURATION` | Session duration in seconds | `number` | `86400` | No | `43200` |
| `OAUTH_CLIENT_ID` | OAuth 2.0 client identifier | `string` | - | Conditional | `client_xxxxxxxxxxxx` |
| `OAUTH_CLIENT_SECRET` | OAuth 2.0 client secret | `string` | - | Conditional | `secret_xxxxxxxxxxxx` |
| `OAUTH_AUTHORIZE_URL` | OAuth authorization endpoint | `string` | - | Conditional | `https://auth.example.com/authorize` |
| `OAUTH_TOKEN_URL` | OAuth token endpoint | `string` | - | Conditional | `https://auth.example.com/token` |
| `OAUTH_CALLBACK_URL` | OAuth callback URL | `string` | - | Conditional | `https://wallboards.example.com/auth/callback` |
| `SAML_ENTRY_POINT` | SAML IdP entry point URL | `string` | - | Conditional | `https://idp.example.com/sso` |
| `SAML_ISSUER` | SAML service provider issuer | `string` | - | Conditional | `wallboards.example.com` |
| `SAML_CERT` | SAML IdP certificate (base64) | `string` | - | Conditional | `MIIC...` |

### Feature Flags

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `FEATURE_LIVE_CALLS` | Enable live call monitoring widget | `boolean` | `true` | No | `true` |
| `FEATURE_AGENT_STATUS` | Enable agent status display | `boolean` | `true` | No | `true` |
| `FEATURE_QUEUE_METRICS` | Enable queue metrics widgets | `boolean` | `true` | No | `true` |
| `FEATURE_HISTORICAL_DATA` | Enable historical data views | `boolean` | `true` | No | `false` |
| `FEATURE_ALERTS` | Enable alert notifications | `boolean` | `true` | No | `true` |
| `FEATURE_EXPORT` | Enable data export functionality | `boolean` | `false` | No | `true` |
| `FEATURE_CUSTOM_WIDGETS` | Allow custom widget creation | `boolean` | `false` | No | `true` |
| `FEATURE_MULTI_TENANT` | Enable multi-tenant mode | `boolean` | `false` | No | `true` |

### Display and Theming

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `DEFAULT_THEME` | Default color theme | `string` | `dark` | No | `light`, `dark`, `custom` |
| `CUSTOM_THEME_URL` | URL to custom theme CSS | `string` | - | No | `https://cdn.example.com/theme.css` |
| `LOGO_URL` | Custom logo URL | `string` | - | No | `https://cdn.example.com/logo.png` |
| `FAVICON_URL` | Custom favicon URL | `string` | - | No | `https://cdn.example.com/favicon.ico` |
| `DEFAULT_REFRESH_RATE` | Default widget refresh rate (seconds) | `number` | `30` | No | `15` |
| `MAX_WIDGETS_PER_BOARD` | Maximum widgets per wallboard | `number` | `20` | No | `30` |
| `DEFAULT_LANGUAGE` | Default display language | `string` | `en` | No | `de`, `fr`, `es` |

### Monitoring and Observability

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `METRICS_ENABLED` | Enable Prometheus metrics endpoint | `boolean` | `true` | No | `true` |
| `METRICS_PORT` | Port for metrics endpoint | `number` | `9090` | No | `9091` |
| `METRICS_PATH` | Path for metrics endpoint | `string` | `/metrics` | No | `/prometheus` |
| `TRACING_ENABLED` | Enable distributed tracing | `boolean` | `false` | No | `true` |
| `TRACING_ENDPOINT` | OpenTelemetry collector endpoint | `string` | - | Conditional | `http://otel-collector:4318` |
| `TRACING_SERVICE_NAME` | Service name for traces | `string` | `natterbox-wallboards` | No | `wallboards-prod` |
| `SENTRY_DSN` | Sentry error tracking DSN | `string` | - | No | `https://xxx@sentry.io/xxx` |
| `SENTRY_ENVIRONMENT` | Sentry environment tag | `string` | `development` | No | `production` |
| `HEALTH_CHECK_PATH` | Health check endpoint path | `string` | `/health` | No | `/healthz` |

---

## Wallboard Configuration Files

### Dashboard Layout Configuration

Wallboard layouts are defined in JSON configuration files located in the `config/dashboards/` directory.

#### File Structure

```
config/
├── dashboards/
│   ├── default.json
│   ├── call-center.json
│   ├── agent-performance.json
│   └── queue-overview.json
├── widgets/
│   ├── widget-defaults.json
│   └── custom-widgets/
├── themes/
│   ├── dark.json
│   ├── light.json
│   └── custom.json
└── alerts/
    └── alert-rules.json
```

#### Dashboard Configuration Schema

```json
{
  "id": "call-center-main",
  "name": "Call Center Overview",
  "description": "Main dashboard for call center operations",
  "version": "1.0.0",
  "layout": {
    "columns": 12,
    "rowHeight": 100,
    "margin": [10, 10],
    "containerPadding": [10, 10]
  },
  "widgets": [
    {
      "id": "widget-001",
      "type": "queue-status",
      "title": "Inbound Queue Status",
      "position": {
        "x": 0,
        "y": 0,
        "w": 4,
        "h": 3
      },
      "config": {
        "queueIds": ["queue_001", "queue_002"],
        "refreshInterval": 10,
        "showWaitTime": true,
        "showAgentCount": true,
        "thresholds": {
          "warning": 30,
          "critical": 60
        }
      }
    },
    {
      "id": "widget-002",
      "type": "agent-grid",
      "title": "Agent Status",
      "position": {
        "x": 4,
        "y": 0,
        "w": 8,
        "h": 6
      },
      "config": {
        "teamIds": ["team_sales", "team_support"],
        "displayMode": "grid",
        "sortBy": "status",
        "showCallDuration": true
      }
    }
  ],
  "theme": "dark",
  "autoRotate": {
    "enabled": false,
    "interval": 30
  },
  "permissions": {
    "viewRoles": ["viewer", "supervisor", "admin"],
    "editRoles": ["supervisor", "admin"]
  }
}
```

### Widget Types Reference

| Widget Type | Description | Required Configuration |
|------------|-------------|----------------------|
| `queue-status` | Real-time queue metrics | `queueIds`, `thresholds` |
| `agent-grid` | Agent status grid display | `teamIds`, `displayMode` |
| `agent-list` | Agent status list view | `teamIds`, `sortBy` |
| `live-calls` | Active calls display | `queueIds`, `maxDisplay` |
| `call-stats` | Call statistics summary | `timeRange`, `metrics` |
| `sla-gauge` | SLA performance gauge | `slaTarget`, `timeRange` |
| `wait-time` | Average wait time display | `queueIds`, `timeRange` |
| `call-volume` | Call volume chart | `timeRange`, `granularity` |
| `abandon-rate` | Abandon rate metric | `queueIds`, `threshold` |
| `custom-metric` | Custom metric display | `metricId`, `query` |

### Alert Rules Configuration

```json
{
  "alerts": [
    {
      "id": "alert-001",
      "name": "High Queue Wait Time",
      "enabled": true,
      "condition": {
        "metric": "queue.average_wait_time",
        "operator": "greater_than",
        "threshold": 120,
        "duration": 300
      },
      "actions": [
        {
          "type": "visual",
          "config": {
            "color": "red",
            "animation": "pulse"
          }
        },
        {
          "type": "sound",
          "config": {
            "sound": "alert-high",
            "repeat": false
          }
        },
        {
          "type": "webhook",
          "config": {
            "url": "https://hooks.example.com/alerts",
            "method": "POST"
          }
        }
      ],
      "cooldown": 600
    }
  ]
}
```

---

## Build Configuration

### Webpack/Vite Configuration

The build process is controlled by environment variables that affect bundling and optimization:

| Variable Name | Description | Type | Default | Example |
|--------------|-------------|------|---------|---------|
| `BUILD_MODE` | Build optimization mode | `string` | `development` | `production` |
| `PUBLIC_URL` | Base URL for static assets | `string` | `/` | `https://cdn.example.com/wallboards/` |
| `GENERATE_SOURCEMAP` | Generate source maps | `boolean` | `true` | `false` |
| `ANALYZE_BUNDLE` | Enable bundle analyzer | `boolean` | `false` | `true` |
| `INLINE_RUNTIME_CHUNK` | Inline webpack runtime | `boolean` | `true` | `false` |

### Build-Time Environment Injection

```javascript
// vite.config.js or webpack.config.js example
const buildConfig = {
  define: {
    'process.env.APP_VERSION': JSON.stringify(process.env.APP_VERSION),
    'process.env.BUILD_TIME': JSON.stringify(new Date().toISOString()),
    'process.env.BUILD_COMMIT': JSON.stringify(process.env.GIT_COMMIT_SHA),
  }
};
```

---

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
NODE_ENV=development
PORT=3000
HOST=localhost
LOG_LEVEL=debug
LOG_FORMAT=text

# Natterbox API (Sandbox)
NATTERBOX_API_URL=https://sandbox-api.natterbox.com/v1
NATTERBOX_API_KEY=nb_test_xxxxxxxxxxxx
NATTERBOX_API_SECRET=sk_test_xxxxxxxxxxxx
NATTERBOX_ORG_ID=org_test_123456

# WebSocket (Sandbox)
WEBSOCKET_URL=wss://sandbox-realtime.natterbox.com
WEBSOCKET_RECONNECT_INTERVAL=3000

# Local Database
DATABASE_URL=postgresql://wallboards:devpassword@localhost:5432/wallboards_dev
DATABASE_POOL_MIN=1
DATABASE_POOL_MAX=5

# Local Redis
REDIS_URL=redis://localhost:6379/0

# Authentication (Relaxed for development)
AUTH_ENABLED=false
AUTH_JWT_SECRET=development_jwt_secret_not_for_production_use
AUTH_SESSION_SECRET=development_session_secret_not_for_production

# Features (All enabled for testing)
FEATURE_LIVE_CALLS=true
FEATURE_AGENT_STATUS=true
FEATURE_QUEUE_METRICS=true
FEATURE_HISTORICAL_DATA=true
FEATURE_ALERTS=true
FEATURE_EXPORT=true
FEATURE_CUSTOM_WIDGETS=true

# Display
DEFAULT_THEME=light
DEFAULT_REFRESH_RATE=5

# Monitoring (Minimal)
METRICS_ENABLED=true
TRACING_ENABLED=false

# Build
BUILD_MODE=development
GENERATE_SOURCEMAP=true
```

### Staging Environment

```bash
# .env.staging
NODE_ENV=staging
PORT=8080
HOST=0.0.0.0
LOG_LEVEL=info
LOG_FORMAT=json

# Natterbox API (Staging)
NATTERBOX_API_URL=https://staging-api.natterbox.com/v1
NATTERBOX_API_KEY=${NATTERBOX_STAGING_API_KEY}
NATTERBOX_API_SECRET=${NATTERBOX_STAGING_API_SECRET}
NATTERBOX_ORG_ID=${NATTERBOX_STAGING_ORG_ID}
NATTERBOX_API_TIMEOUT=30000
NATTERBOX_API_RETRY_ATTEMPTS=3

# WebSocket (Staging)
WEBSOCKET_URL=wss://staging-realtime.natterbox.com
WEBSOCKET_RECONNECT_INTERVAL=5000
WEBSOCKET_MAX_RECONNECT_ATTEMPTS=15

# Database (Staging)
DATABASE_URL=${DATABASE_STAGING_URL}
DATABASE_SSL=true
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Redis (Staging)
REDIS_URL=${REDIS_STAGING_URL}
REDIS_TLS=true
REDIS_KEY_PREFIX=wallboards_staging:

# Authentication
AUTH_ENABLED=true
AUTH_PROVIDER=oauth2
AUTH_JWT_SECRET=${JWT_SECRET_STAGING}
AUTH_JWT_EXPIRY=12h
AUTH_SESSION_SECRET=${SESSION_SECRET_STAGING}
OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID_STAGING}
OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET_STAGING}
OAUTH_AUTHORIZE_URL=https://staging-auth.natterbox.com/authorize
OAUTH_TOKEN_URL=https://staging-auth.natterbox.com/token
OAUTH_CALLBACK_URL=https://staging-wallboards.natterbox.com/auth/callback

# Features
FEATURE_LIVE_CALLS=true
FEATURE_AGENT_STATUS=true
FEATURE_QUEUE_METRICS=true
FEATURE_HISTORICAL_DATA=true
FEATURE_ALERTS=true
FEATURE_EXPORT=true
FEATURE_CUSTOM_WIDGETS=false

# Display
DEFAULT_THEME=dark
DEFAULT_REFRESH_RATE=15

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=true
TRACING_ENDPOINT=http://otel-collector.monitoring:4318
TRACING_SERVICE_NAME=wallboards-staging
SENTRY_DSN=${SENTRY_DSN_STAGING}
SENTRY_ENVIRONMENT=staging

# Build
BUILD_MODE=production
PUBLIC_URL=https://staging-cdn.natterbox.com/wallboards/
GENERATE_SOURCEMAP=true
```

### Production Environment

```bash
# .env.production
NODE_ENV=production
PORT=8080
HOST=0.0.0.0
LOG_LEVEL=warn
LOG_FORMAT=json

# Natterbox API (Production)
NATTERBOX_API_URL=https://api.natterbox.com/v1
NATTERBOX_API_KEY=${NATTERBOX_PROD_API_KEY}
NATTERBOX_API_SECRET=${NATTERBOX_PROD_API_SECRET}
NATTERBOX_ORG_ID=${NATTERBOX_PROD_ORG_ID}
NATTERBOX_API_TIMEOUT=30000
NATTERBOX_API_RETRY_ATTEMPTS=5
NATTERBOX_API_RETRY_DELAY=2000
NATTERBOX_WEBHOOK_SECRET=${NATTERBOX_WEBHOOK_SECRET}

# WebSocket (Production)
WEBSOCKET_URL=wss://realtime.natterbox.com
WEBSOCKET_RECONNECT_INTERVAL=5000
WEBSOCKET_MAX_RECONNECT_ATTEMPTS=20
WEBSOCKET_HEARTBEAT_INTERVAL=15000

# Database (Production - High Availability)
DATABASE_URL=${DATABASE_PROD_URL}
DATABASE_SSL=true
DATABASE_POOL_MIN=5
DATABASE_POOL_MAX=25

# Redis (Production - Cluster)
REDIS_URL=${REDIS_PROD_URL}
REDIS_TLS=true
REDIS_KEY_PREFIX=wallboards_prod:

# Cache
CACHE_TTL=300
DATA_REFRESH_INTERVAL=30000

# Authentication (Strict)
AUTH_ENABLED=true
AUTH_PROVIDER=saml
AUTH_JWT_SECRET=${JWT_SECRET_PROD}
AUTH_JWT_EXPIRY=8h
AUTH_SESSION_SECRET=${SESSION_SECRET_PROD}
AUTH_SESSION_DURATION=28800
SAML_ENTRY_POINT=${SAML_ENTRY_POINT_PROD}
SAML_ISSUER=wallboards.natterbox.com
SAML_CERT=${SAML_CERT_PROD}

# Features (Production-approved only)
FEATURE_LIVE_CALLS=true
FEATURE_AGENT_STATUS=true
FEATURE_QUEUE_METRICS=true
FEATURE_HISTORICAL_DATA=true
FEATURE_ALERTS=true
FEATURE_EXPORT=false
FEATURE_CUSTOM_WIDGETS=false
FEATURE_MULTI_TENANT=true

# Display
DEFAULT_THEME=dark
DEFAULT_REFRESH_RATE=30
DEFAULT_LANGUAGE=en
LOGO_URL=https://cdn.natterbox.com/branding/logo.png
FAVICON_URL=https://cdn.natterbox.com/branding/favicon.ico

# Monitoring (Full observability)
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=true
TRACING_ENDPOINT=http://otel-collector.monitoring:4318
TRACING_SERVICE_NAME=wallboards-prod
SENTRY_DSN=${SENTRY_DSN_PROD}
SENTRY_ENVIRONMENT=production

# Build
BUILD_MODE=production
PUBLIC_URL=https://cdn.natterbox.com/wallboards/
GENERATE_SOURCEMAP=false
```

---

## Security Considerations

### Sensitive Values Protection

The following variables contain sensitive information and must be handled securely:

| Variable | Sensitivity Level | Recommended Storage |
|----------|------------------|---------------------|
| `NATTERBOX_API_KEY` | High | Secrets Manager |
| `NATTERBOX_API_SECRET` | Critical | Secrets Manager |
| `NATTERBOX_WEBHOOK_SECRET` | High | Secrets Manager |
| `DATABASE_PASSWORD` | Critical | Secrets Manager |
| `DATABASE_URL` | Critical | Secrets Manager |
| `REDIS_PASSWORD` | High | Secrets Manager |
| `AUTH_JWT_SECRET` | Critical | Secrets Manager |
| `AUTH_SESSION_SECRET` | Critical | Secrets Manager |
| `OAUTH_CLIENT_SECRET` | Critical | Secrets Manager |
| `SAML_CERT` | High | Secrets Manager |
| `SENTRY_DSN` | Medium | Environment Variable |

### Best Practices

1. **Never commit secrets to version control**
   ```bash
   # .gitignore
   .env
   .env.local
   .env.*.local
   *.pem
   *.key
   ```

2. **Use secret management systems**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Secret Manager

3. **Rotate secrets regularly**
   - API keys: Every 90 days
   - JWT secrets: Every 30 days
   - Database passwords: Every 60 days

4. **Minimum required permissions**
   - API keys should have read-only access where possible
   - Database users should have limited privileges

5. **Audit logging**
   - Enable audit logging for secret access
   - Monitor for unauthorized access attempts

### Kubernetes Secrets Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: wallboards-secrets
  namespace: natterbox
type: Opaque
stringData:
  NATTERBOX_API_KEY: "nb_live_xxxxxxxxxxxx"
  NATTERBOX_API_SECRET: "sk_xxxxxxxxxxxxxxxxxxxx"
  DATABASE_URL: "postgresql://user:password@host:5432/db"
  AUTH_JWT_SECRET: "your-256-bit-secret-key-here"
  AUTH_SESSION_SECRET: "your-session-secret-here"
```

### Docker Secrets Example

```yaml
# docker-compose.yml
version: '3.8'
services:
  wallboards:
    image: natterbox/wallboards:latest
    secrets:
      - natterbox_api_key
      - natterbox_api_secret
      - database_url
      - jwt_secret
    environment:
      NATTERBOX_API_KEY_FILE: /run/secrets/natterbox_api_key
      NATTERBOX_API_SECRET_FILE: /run/secrets/natterbox_api_secret
      DATABASE_URL_FILE: /run/secrets/database_url
      AUTH_JWT_SECRET_FILE: /run/secrets/jwt_secret

secrets:
  natterbox_api_key:
    external: true
  natterbox_api_secret:
    external: true
  database_url:
    external: true
  jwt_secret:
    external: true
```

---

## Troubleshooting Common Configuration Issues

### Issue: Application fails to start with "Missing required configuration"

**Symptoms:**
```
Error: Missing required configuration: NATTERBOX_API_URL
```

**Solution:**
1. Verify all required environment variables are set
2. Check for typos in variable names
3. Ensure `.env` file is in the correct location
4. Verify environment variable inheritance in Docker/K8s

### Issue: WebSocket connection failures

**Symptoms:**
```
WebSocket connection to 'wss://...' failed: Connection timeout
```

**Solution:**
1. Verify `WEBSOCKET_URL` is correct and accessible
2. Check firewall rules allow WebSocket connections
3. Verify SSL certificates if using `wss://`
4. Increase `WEBSOCKET_RECONNECT_INTERVAL` if network is unstable

### Issue: Database connection pool exhaustion

**Symptoms:**
```
Error: Connection pool exhausted, timeout waiting for available connection
```

**Solution:**
1. Increase `DATABASE_POOL_MAX` value
2. Review application for connection leaks
3. Add connection timeout settings
4. Consider read replicas for read-heavy workloads

### Issue: Authentication failures after deployment

**Symptoms:**
```
Error: Invalid JWT signature
```

**Solution:**
1. Ensure `AUTH_JWT_SECRET` is identical across all instances
2. Verify secret wasn't truncated during deployment
3. Check for encoding issues (base64 vs raw)
4. Ensure clock synchronization across servers

### Issue: Real-time data not updating

**Symptoms:**
- Widgets show stale data
- "Last updated" timestamp not changing

**Solution:**
1. Verify WebSocket connection is established
2. Check `DATA_REFRESH_INTERVAL` setting
3. Verify Natterbox API credentials are valid
4. Check browser developer console for errors
5. Verify Redis connection for cached data

---

## Complete Example .env File

```bash
# ===========================================
# Natterbox Wallboards - Complete Configuration
# ===========================================
# Environment: Production
# Last Updated: 2024-01-15
# ===========================================

# -----------------------------
# Core Application Settings
# -----------------------------
NODE_ENV=production
PORT=8080
HOST=0.0.0.0
APP_NAME=Natterbox Wallboards
APP_VERSION=2.3.1
LOG_LEVEL=warn
LOG_FORMAT=json
TIMEZONE=Europe/London

# -----------------------------
# Natterbox API Configuration
# -----------------------------
NATTERBOX_API_URL=https://api.natterbox.com/v1
NATTERBOX_API_KEY=${NATTERBOX_PROD_API_KEY}
NATTERBOX_API_SECRET=${NATTERBOX_PROD_API_SECRET}
NATTERBOX_ORG_ID=${NATTERBOX_PROD_ORG_ID}
NATTERBOX_API_TIMEOUT=30000
NATTERBOX_API_RETRY_ATTEMPTS=5
NATTERBOX_API_RETRY_DELAY=2000
NATTERBOX_WEBHOOK_SECRET=${NATTERBOX_WEBHOOK_SECRET}

# -----------------------------
# Real-Time Data Configuration
# -----------------------------
WEBSOCKET_URL=wss://realtime.natterbox.com
WEBSOCKET_RECONNECT_INTERVAL=5000
WEBSOCKET_MAX_RECONNECT_ATTEMPTS=20
WEBSOCKET_HEARTBEAT_INTERVAL=15000
DATA_REFRESH_INTERVAL=30000
CACHE_TTL=300

# -----------------------------
# Database Configuration
# -----------------------------
DATABASE_URL=${DATABASE_PROD_URL}
DATABASE_SSL=true
DATABASE_POOL_MIN=5
DATABASE_POOL_MAX=25

# -----------------------------
# Redis Configuration
# -----------------------------
REDIS_URL=${REDIS_PROD_URL}
REDIS_TLS=true
REDIS_KEY_PREFIX=wallboards_prod:

# -----------------------------
# Authentication Configuration
# -----------------------------
AUTH_ENABLED=true
AUTH_PROVIDER=saml
AUTH_JWT_SECRET=${JWT_SECRET_PROD}
AUTH_JWT_EXPIRY=8h
AUTH_SESSION_SECRET=${SESSION_SECRET_PROD}
AUTH_SESSION_DURATION=28800
SAML_ENTRY_POINT=${SAML_ENTRY_POINT_PROD}
SAML_ISSUER=wallboards.natterbox.com
SAML_CERT=${SAML_CERT_PROD}

# -----------------------------
# Feature Flags
# -----------------------------
FEATURE_LIVE_CALLS=true
FEATURE_AGENT_STATUS=true
FEATURE_QUEUE_METRICS=true
FEATURE_HISTORICAL_DATA=true
FEATURE_ALERTS=true
FEATURE_EXPORT=false
FEATURE_CUSTOM_WIDGETS=false
FEATURE_MULTI_TENANT=true

# -----------------------------
# Display and Theming
# -----------------------------
DEFAULT_THEME=dark
DEFAULT_REFRESH_RATE=30
MAX_WIDGETS_PER_BOARD=20
DEFAULT_LANGUAGE=en
LOGO_URL=https://cdn.natterbox.com/branding/logo.png
FAVICON_URL=https://cdn.natterbox.com/branding/favicon.ico

# -----------------------------
# Monitoring and Observability
# -----------------------------
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics
TRACING_ENABLED=true
TRACING_ENDPOINT=http://otel-collector.monitoring:4318
TRACING_SERVICE_NAME=wallboards-prod
SENTRY_DSN=${SENTRY_DSN_PROD}
SENTRY_ENVIRONMENT=production
HEALTH_CHECK_PATH=/health

# -----------------------------
# Build Configuration
# -----------------------------
BUILD_MODE=production
PUBLIC_URL=https://cdn.natterbox.com/wallboards/
GENERATE_SOURCEMAP=false
```

---

This configuration guide provides comprehensive documentation for deploying and managing the natterbox-wallboards service. For additional support, consult the Natterbox API documentation or contact the platform team.