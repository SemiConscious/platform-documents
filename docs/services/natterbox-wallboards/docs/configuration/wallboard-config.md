# Wallboard Configuration Files

## Overview

Natterbox Wallboards is a real-time dashboard application designed to display call center metrics, agent status, and performance KPIs. The configuration system uses a combination of environment variables for runtime settings and JSON-based configuration files for individual wallboard definitions.

This documentation provides comprehensive guidance on configuring wallboards, creating new dashboard layouts, managing widgets, and customizing displays for different operational needs. The configuration approach follows a layered architecture where global settings are defined through environment variables, while individual wallboard configurations are stored as portable JSON files.

---

## Configuration File Structure

### Directory Layout

```
/app/
├── config/
│   ├── wallboards/           # Individual wallboard JSON files
│   │   ├── default.json
│   │   ├── sales-team.json
│   │   └── support-queue.json
│   ├── themes/               # Custom theme configurations
│   │   ├── default.json
│   │   └── dark-mode.json
│   └── widgets/              # Widget template definitions
│       ├── call-stats.json
│       └── agent-grid.json
├── .env                      # Environment variables
└── wallboards.config.js      # Main configuration file
```

### Main Configuration File (wallboards.config.js)

```javascript
module.exports = {
  server: {
    port: process.env.WALLBOARD_PORT || 3000,
    host: process.env.WALLBOARD_HOST || '0.0.0.0',
  },
  datasource: {
    natterboxApi: process.env.NATTERBOX_API_URL,
    refreshInterval: parseInt(process.env.DATA_REFRESH_INTERVAL) || 5000,
  },
  authentication: {
    enabled: process.env.AUTH_ENABLED === 'true',
    provider: process.env.AUTH_PROVIDER || 'oauth2',
  },
  storage: {
    type: process.env.STORAGE_TYPE || 'file',
    path: process.env.WALLBOARD_STORAGE_PATH || './config/wallboards',
  },
};
```

---

## Environment Variables

### Core Application Settings

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `WALLBOARD_PORT` | HTTP port for the wallboard server | Integer | `3000` | No | `8080` |
| `WALLBOARD_HOST` | Host address to bind the server | String | `0.0.0.0` | No | `127.0.0.1` |
| `NODE_ENV` | Application environment mode | String | `development` | Yes | `production` |
| `LOG_LEVEL` | Logging verbosity level | String | `info` | No | `debug`, `warn`, `error` |
| `LOG_FORMAT` | Log output format | String | `json` | No | `json`, `text`, `combined` |
| `TZ` | Timezone for date/time display | String | `UTC` | No | `America/New_York` |

### Natterbox API Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `NATTERBOX_API_URL` | Base URL for Natterbox API | URL | - | Yes | `https://api.natterbox.com/v1` |
| `NATTERBOX_API_KEY` | API key for authentication | String | - | Yes | `nb_live_xxxxxxxxxxxx` |
| `NATTERBOX_API_SECRET` | API secret for HMAC signing | String | - | Yes | `secret_xxxxxxxxxxxx` |
| `NATTERBOX_ORG_ID` | Organization identifier | String | - | Yes | `org_12345` |
| `NATTERBOX_API_TIMEOUT` | API request timeout in ms | Integer | `30000` | No | `60000` |
| `NATTERBOX_API_RETRY_COUNT` | Number of retry attempts | Integer | `3` | No | `5` |
| `NATTERBOX_API_RETRY_DELAY` | Delay between retries in ms | Integer | `1000` | No | `2000` |

### Data Refresh Settings

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `DATA_REFRESH_INTERVAL` | Global data refresh rate in ms | Integer | `5000` | No | `3000` |
| `REALTIME_ENABLED` | Enable WebSocket real-time updates | Boolean | `true` | No | `false` |
| `WEBSOCKET_URL` | WebSocket endpoint URL | URL | - | Conditional | `wss://realtime.natterbox.com` |
| `CACHE_TTL` | Cache time-to-live in seconds | Integer | `300` | No | `600` |
| `CACHE_ENABLED` | Enable data caching layer | Boolean | `true` | No | `false` |

### Authentication Configuration

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `AUTH_ENABLED` | Enable authentication | Boolean | `false` | No | `true` |
| `AUTH_PROVIDER` | Authentication provider type | String | `oauth2` | Conditional | `oauth2`, `saml`, `local` |
| `AUTH_CLIENT_ID` | OAuth2 client identifier | String | - | Conditional | `wallboard_client_id` |
| `AUTH_CLIENT_SECRET` | OAuth2 client secret | String | - | Conditional | `client_secret_xxx` |
| `AUTH_ISSUER_URL` | OAuth2/OIDC issuer URL | URL | - | Conditional | `https://auth.company.com` |
| `AUTH_CALLBACK_URL` | OAuth2 callback URL | URL | - | Conditional | `https://wallboard.company.com/callback` |
| `SESSION_SECRET` | Secret for session encryption | String | - | Yes | `random_64_char_string` |
| `SESSION_TIMEOUT` | Session timeout in minutes | Integer | `480` | No | `60` |

### Database Configuration (Optional)

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `STORAGE_TYPE` | Storage backend type | String | `file` | No | `file`, `redis`, `mongodb` |
| `WALLBOARD_STORAGE_PATH` | File storage path | String | `./config/wallboards` | Conditional | `/data/wallboards` |
| `REDIS_URL` | Redis connection URL | URL | - | Conditional | `redis://localhost:6379` |
| `REDIS_PASSWORD` | Redis authentication password | String | - | No | `redis_password` |
| `MONGODB_URI` | MongoDB connection string | URL | - | Conditional | `mongodb://localhost:27017/wallboards` |

### Display and Theme Settings

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `DEFAULT_THEME` | Default wallboard theme | String | `default` | No | `dark-mode` |
| `CUSTOM_CSS_PATH` | Path to custom CSS file | String | - | No | `/assets/custom.css` |
| `COMPANY_LOGO_URL` | Company logo URL for branding | URL | - | No | `https://cdn.company.com/logo.png` |
| `GRID_COLUMNS` | Default grid column count | Integer | `12` | No | `16` |
| `AUTO_ROTATE_INTERVAL` | Wallboard rotation interval in seconds | Integer | `30` | No | `60` |

---

## Creating a New Wallboard

### Wallboard JSON Structure

Each wallboard is defined by a JSON configuration file with the following structure:

```json
{
  "id": "sales-team-v1",
  "name": "Sales Team Dashboard",
  "description": "Real-time sales metrics and agent performance",
  "version": "1.0.0",
  "created": "2024-01-15T10:30:00Z",
  "modified": "2024-01-20T14:22:00Z",
  "author": "admin@company.com",
  "settings": {
    "refreshInterval": 5000,
    "theme": "dark-mode",
    "layout": {
      "columns": 12,
      "rowHeight": 100,
      "margin": [10, 10],
      "containerPadding": [10, 10]
    },
    "autoRotate": {
      "enabled": false,
      "interval": 30
    }
  },
  "filters": {
    "queues": ["sales-inbound", "sales-outbound"],
    "teams": ["team-alpha", "team-beta"],
    "dateRange": "today"
  },
  "widgets": []
}
```

### Configuration Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | String | Yes | Unique identifier for the wallboard |
| `name` | String | Yes | Display name for the wallboard |
| `description` | String | No | Detailed description of the wallboard purpose |
| `version` | String | No | Semantic version for change tracking |
| `created` | ISO 8601 | Auto | Creation timestamp |
| `modified` | ISO 8601 | Auto | Last modification timestamp |
| `author` | String | No | Creator email or identifier |
| `settings` | Object | Yes | Global wallboard settings |
| `filters` | Object | No | Data filtering configuration |
| `widgets` | Array | Yes | Array of widget configurations |

### Creating via API

```bash
# Create a new wallboard
curl -X POST https://wallboard.company.com/api/wallboards \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @new-wallboard.json
```

### Creating via File System

```bash
# Copy template and customize
cp /app/config/wallboards/template.json /app/config/wallboards/my-wallboard.json

# Edit the configuration
vim /app/config/wallboards/my-wallboard.json

# Validate the configuration
node /app/scripts/validate-wallboard.js /app/config/wallboards/my-wallboard.json
```

---

## Editing Wallboards

### Visual Editor

Access the visual editor at `https://wallboard.company.com/admin/editor` to make changes through a drag-and-drop interface.

### Direct JSON Editing

For advanced configurations, edit the JSON files directly:

```json
{
  "id": "support-queue",
  "name": "Support Queue Monitor",
  "settings": {
    "refreshInterval": 3000,
    "theme": "default",
    "layout": {
      "columns": 12,
      "rowHeight": 80,
      "margin": [8, 8],
      "containerPadding": [16, 16]
    },
    "alerts": {
      "enabled": true,
      "sound": "/assets/sounds/alert.mp3",
      "conditions": [
        {
          "metric": "queueWaitTime",
          "operator": "greaterThan",
          "value": 120,
          "severity": "warning"
        },
        {
          "metric": "queueWaitTime",
          "operator": "greaterThan",
          "value": 300,
          "severity": "critical"
        }
      ]
    }
  },
  "widgets": [
    {
      "id": "widget-1",
      "type": "call-stats",
      "title": "Calls Waiting",
      "position": { "x": 0, "y": 0, "w": 4, "h": 2 }
    }
  ]
}
```

### Version Control

Track changes using the built-in versioning system:

```json
{
  "history": [
    {
      "version": "1.0.0",
      "timestamp": "2024-01-15T10:30:00Z",
      "author": "admin@company.com",
      "changes": "Initial creation"
    },
    {
      "version": "1.1.0",
      "timestamp": "2024-01-20T14:22:00Z",
      "author": "manager@company.com",
      "changes": "Added SLA compliance widget"
    }
  ]
}
```

---

## Widget Configuration

### Available Widget Types

| Widget Type | Description | Data Source |
|-------------|-------------|-------------|
| `call-stats` | Numeric call statistics display | Natterbox API |
| `agent-grid` | Agent status grid view | Natterbox Real-time |
| `queue-status` | Queue metrics and wait times | Natterbox API |
| `sla-gauge` | SLA compliance gauge chart | Natterbox API |
| `call-volume-chart` | Time-series call volume | Natterbox API |
| `leaderboard` | Agent performance ranking | Natterbox API |
| `ticker` | Scrolling message ticker | Custom/API |
| `clock` | Date/time display | System |
| `iframe` | Embedded external content | External URL |

### Widget Configuration Schema

```json
{
  "id": "unique-widget-id",
  "type": "call-stats",
  "title": "Total Calls Today",
  "position": {
    "x": 0,
    "y": 0,
    "w": 4,
    "h": 2,
    "minW": 2,
    "maxW": 12,
    "minH": 1,
    "maxH": 4
  },
  "style": {
    "backgroundColor": "#1a1a2e",
    "textColor": "#ffffff",
    "borderRadius": "8px",
    "fontSize": "large",
    "icon": "phone"
  },
  "data": {
    "metric": "totalCalls",
    "aggregation": "sum",
    "filters": {
      "queue": "sales-inbound",
      "dateRange": "today"
    },
    "refreshInterval": 5000
  },
  "thresholds": [
    { "value": 0, "color": "#e74c3c" },
    { "value": 50, "color": "#f39c12" },
    { "value": 100, "color": "#27ae60" }
  ],
  "conditionalFormatting": {
    "enabled": true,
    "rules": [
      {
        "condition": "value < 10",
        "style": { "backgroundColor": "#e74c3c" }
      }
    ]
  }
}
```

### Agent Grid Widget Example

```json
{
  "id": "agent-status-grid",
  "type": "agent-grid",
  "title": "Agent Status",
  "position": { "x": 0, "y": 2, "w": 12, "h": 4 },
  "data": {
    "teams": ["sales", "support"],
    "showOffline": false,
    "sortBy": "status",
    "groupBy": "team"
  },
  "display": {
    "columns": ["name", "status", "duration", "extension", "currentCall"],
    "statusColors": {
      "available": "#27ae60",
      "onCall": "#3498db",
      "away": "#f39c12",
      "offline": "#95a5a6",
      "dnd": "#e74c3c"
    },
    "avatars": true,
    "compactMode": false
  }
}
```

### Queue Status Widget Example

```json
{
  "id": "queue-monitor",
  "type": "queue-status",
  "title": "Queue Overview",
  "position": { "x": 4, "y": 0, "w": 8, "h": 2 },
  "data": {
    "queues": ["main-support", "billing", "technical"],
    "metrics": ["waiting", "longestWait", "avgWaitTime", "abandoned"]
  },
  "display": {
    "layout": "horizontal",
    "showTrend": true,
    "trendPeriod": "1hour"
  },
  "alerts": {
    "waiting": { "warning": 5, "critical": 10 },
    "longestWait": { "warning": 120, "critical": 300 }
  }
}
```

---

## Examples

### Complete Development Environment (.env.development)

```bash
# ===========================================
# Natterbox Wallboards - Development Configuration
# ===========================================

# Application Settings
NODE_ENV=development
WALLBOARD_PORT=3000
WALLBOARD_HOST=127.0.0.1
LOG_LEVEL=debug
LOG_FORMAT=text
TZ=America/New_York

# Natterbox API Configuration
NATTERBOX_API_URL=https://sandbox-api.natterbox.com/v1
NATTERBOX_API_KEY=nb_sandbox_dev_key_12345
NATTERBOX_API_SECRET=nb_sandbox_secret_67890
NATTERBOX_ORG_ID=org_dev_sandbox
NATTERBOX_API_TIMEOUT=60000
NATTERBOX_API_RETRY_COUNT=5
NATTERBOX_API_RETRY_DELAY=2000

# Real-time Data
DATA_REFRESH_INTERVAL=10000
REALTIME_ENABLED=true
WEBSOCKET_URL=wss://sandbox-realtime.natterbox.com
CACHE_ENABLED=false
CACHE_TTL=60

# Authentication (disabled for development)
AUTH_ENABLED=false
SESSION_SECRET=dev_session_secret_change_in_production_12345

# Storage Configuration
STORAGE_TYPE=file
WALLBOARD_STORAGE_PATH=./config/wallboards

# Display Settings
DEFAULT_THEME=default
GRID_COLUMNS=12
AUTO_ROTATE_INTERVAL=0

# Development Features
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_PANEL=true
MOCK_DATA_ENABLED=true
```

### Complete Production Environment (.env.production)

```bash
# ===========================================
# Natterbox Wallboards - Production Configuration
# ===========================================

# Application Settings
NODE_ENV=production
WALLBOARD_PORT=8080
WALLBOARD_HOST=0.0.0.0
LOG_LEVEL=warn
LOG_FORMAT=json
TZ=UTC

# Natterbox API Configuration
NATTERBOX_API_URL=https://api.natterbox.com/v1
NATTERBOX_API_KEY=${NATTERBOX_API_KEY}
NATTERBOX_API_SECRET=${NATTERBOX_API_SECRET}
NATTERBOX_ORG_ID=${NATTERBOX_ORG_ID}
NATTERBOX_API_TIMEOUT=30000
NATTERBOX_API_RETRY_COUNT=3
NATTERBOX_API_RETRY_DELAY=1000

# Real-time Data
DATA_REFRESH_INTERVAL=5000
REALTIME_ENABLED=true
WEBSOCKET_URL=wss://realtime.natterbox.com
CACHE_ENABLED=true
CACHE_TTL=300

# Authentication
AUTH_ENABLED=true
AUTH_PROVIDER=oauth2
AUTH_CLIENT_ID=${AUTH_CLIENT_ID}
AUTH_CLIENT_SECRET=${AUTH_CLIENT_SECRET}
AUTH_ISSUER_URL=https://auth.company.com
AUTH_CALLBACK_URL=https://wallboard.company.com/auth/callback
SESSION_SECRET=${SESSION_SECRET}
SESSION_TIMEOUT=480

# Storage Configuration
STORAGE_TYPE=redis
REDIS_URL=redis://redis-cluster.internal:6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# Display Settings
DEFAULT_THEME=dark-mode
COMPANY_LOGO_URL=https://cdn.company.com/assets/logo-white.png
GRID_COLUMNS=12
AUTO_ROTATE_INTERVAL=30

# Security Headers
ENABLE_HTTPS_REDIRECT=true
ENABLE_HSTS=true
CSP_POLICY=default-src 'self'; img-src 'self' https://cdn.company.com;
```

### Complete Wallboard Configuration Example

```json
{
  "id": "call-center-main",
  "name": "Call Center Command Center",
  "description": "Primary wallboard for call center floor display",
  "version": "2.1.0",
  "settings": {
    "refreshInterval": 3000,
    "theme": "dark-mode",
    "layout": {
      "columns": 12,
      "rowHeight": 100,
      "margin": [10, 10],
      "containerPadding": [20, 20]
    },
    "autoRotate": {
      "enabled": true,
      "interval": 60,
      "pages": ["overview", "agents", "queues"]
    }
  },
  "filters": {
    "queues": ["all"],
    "teams": ["all"],
    "dateRange": "today"
  },
  "widgets": [
    {
      "id": "header-clock",
      "type": "clock",
      "position": { "x": 10, "y": 0, "w": 2, "h": 1 },
      "style": { "fontSize": "xlarge" }
    },
    {
      "id": "calls-waiting",
      "type": "call-stats",
      "title": "Calls Waiting",
      "position": { "x": 0, "y": 0, "w": 2, "h": 2 },
      "data": { "metric": "callsWaiting" },
      "thresholds": [
        { "value": 0, "color": "#27ae60" },
        { "value": 5, "color": "#f39c12" },
        { "value": 10, "color": "#e74c3c" }
      ]
    },
    {
      "id": "longest-wait",
      "type": "call-stats",
      "title": "Longest Wait",
      "position": { "x": 2, "y": 0, "w": 2, "h": 2 },
      "data": { "metric": "longestWaitTime", "format": "duration" },
      "thresholds": [
        { "value": 0, "color": "#27ae60" },
        { "value": 120, "color": "#f39c12" },
        { "value": 300, "color": "#e74c3c" }
      ]
    },
    {
      "id": "sla-compliance",
      "type": "sla-gauge",
      "title": "SLA Compliance",
      "position": { "x": 4, "y": 0, "w": 3, "h": 2 },
      "data": {
        "targetSla": 80,
        "targetTime": 30
      }
    },
    {
      "id": "call-volume",
      "type": "call-volume-chart",
      "title": "Call Volume (Last 8 Hours)",
      "position": { "x": 7, "y": 0, "w": 3, "h": 2 },
      "data": {
        "period": "8hours",
        "interval": "30min",
        "showForecast": true
      }
    },
    {
      "id": "agent-grid",
      "type": "agent-grid",
      "title": "Agent Status",
      "position": { "x": 0, "y": 2, "w": 12, "h": 4 },
      "data": {
        "teams": ["all"],
        "showOffline": false,
        "sortBy": "status"
      },
      "display": {
        "columns": ["name", "status", "duration", "currentCall"],
        "compactMode": true
      }
    },
    {
      "id": "leaderboard",
      "type": "leaderboard",
      "title": "Top Performers Today",
      "position": { "x": 0, "y": 6, "w": 4, "h": 3 },
      "data": {
        "metric": "callsHandled",
        "limit": 10,
        "period": "today"
      }
    },
    {
      "id": "queue-breakdown",
      "type": "queue-status",
      "title": "Queue Status",
      "position": { "x": 4, "y": 6, "w": 8, "h": 3 },
      "data": {
        "queues": ["sales", "support", "billing", "technical"],
        "metrics": ["waiting", "available", "avgWaitTime", "abandoned"]
      }
    }
  ]
}
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  wallboards:
    image: natterbox/wallboards:latest
    container_name: natterbox-wallboards
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - WALLBOARD_PORT=8080
    env_file:
      - .env.production
    volumes:
      - ./config/wallboards:/app/config/wallboards:ro
      - ./config/themes:/app/config/themes:ro
      - wallboard-logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - wallboard-network

  redis:
    image: redis:7-alpine
    container_name: wallboard-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - wallboard-network

volumes:
  wallboard-logs:
  redis-data:

networks:
  wallboard-network:
    driver: bridge
```

---

## Security Considerations

### Sensitive Values Protection

1. **Never commit secrets to version control**
   ```bash
   # Add to .gitignore
   .env
   .env.*
   !.env.example
   ```

2. **Use secret management services in production**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Kubernetes Secrets

3. **Rotate credentials regularly**
   - API keys: Every 90 days
   - Session secrets: Every 30 days
   - OAuth secrets: Every 180 days

### Environment Variable Security

```bash
# Use environment variable references in production
NATTERBOX_API_KEY=${NATTERBOX_API_KEY}  # Injected at runtime
NATTERBOX_API_SECRET=${NATTERBOX_API_SECRET}
AUTH_CLIENT_SECRET=${AUTH_CLIENT_SECRET}
SESSION_SECRET=${SESSION_SECRET}
REDIS_PASSWORD=${REDIS_PASSWORD}
```

### Network Security

- Always use HTTPS in production
- Configure proper CORS policies
- Implement rate limiting for API endpoints
- Use VPN or private networks for internal services

---

## Troubleshooting

### Common Configuration Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Wallboard not loading | Invalid JSON syntax | Validate JSON with `jq . wallboard.json` |
| Widgets showing "No Data" | Incorrect API credentials | Verify `NATTERBOX_API_KEY` and `NATTERBOX_API_SECRET` |
| Real-time updates not working | WebSocket connection failed | Check `WEBSOCKET_URL` and firewall rules |
| Authentication failures | Misconfigured OAuth | Verify `AUTH_CALLBACK_URL` matches registered redirect URI |
| High memory usage | Cache not configured | Enable Redis caching with `STORAGE_TYPE=redis` |
| Slow dashboard loading | Too many widgets | Reduce widgets or increase `DATA_REFRESH_INTERVAL` |

### Validation Commands

```bash
# Validate environment configuration
node /app/scripts/validate-config.js

# Test API connectivity
curl -H "Authorization: Bearer ${NATTERBOX_API_KEY}" \
  "${NATTERBOX_API_URL}/health"

# Validate wallboard JSON
node -e "JSON.parse(require('fs').readFileSync('wallboard.json'))"

# Check Redis connectivity
redis-cli -u ${REDIS_URL} ping
```