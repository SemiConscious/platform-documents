# Configuration Guide: platform-cti-client

## Overview

The `platform-cti-client` service is a Computer Telephony Integration (CTI) client application designed to facilitate communication between contact center agents and telephony systems. This client handles real-time voice communications, agent state management, call controls, and integration with backend CTI servers.

This configuration guide provides comprehensive documentation for all configuration variables, environment-specific settings, and best practices for deploying the platform-cti-client across development, staging, and production environments.

---

## Configuration Files Overview

The platform-cti-client uses a layered configuration approach:

| File | Purpose | Priority |
|------|---------|----------|
| `.env` | Environment-specific variables | Highest |
| `.env.local` | Local overrides (not committed) | High |
| `.env.development` | Development environment defaults | Medium |
| `.env.staging` | Staging environment defaults | Medium |
| `.env.production` | Production environment defaults | Medium |
| `config/default.json` | Application defaults | Lowest |

Configuration is resolved in order of priority, with environment variables taking precedence over file-based configuration.

---

## Environment Configurations

### Base Configuration

These are the foundational configuration variables required for the platform-cti-client to operate.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_NAME` | Application display name | String | `"CTI Client"` | No | `"Contact Center CTI"` |
| `REACT_APP_VERSION` | Application version identifier | String | `"1.0.0"` | No | `"2.5.3"` |
| `REACT_APP_ENVIRONMENT` | Current deployment environment | String | `"development"` | Yes | `"production"` |
| `REACT_APP_BASE_URL` | Base URL for the application | URL | `"http://localhost:3000"` | Yes | `"https://cti.example.com"` |
| `REACT_APP_API_BASE_URL` | Backend API base URL | URL | `"http://localhost:8080/api"` | Yes | `"https://api.cti.example.com/v1"` |
| `REACT_APP_CTI_SERVER_URL` | CTI server WebSocket endpoint | URL | `"ws://localhost:8081"` | Yes | `"wss://cti-server.example.com"` |
| `REACT_APP_CTI_SERVER_PORT` | CTI server connection port | Number | `8081` | No | `443` |
| `REACT_APP_WEBSOCKET_PATH` | WebSocket connection path | String | `"/ws"` | No | `"/cti/websocket"` |
| `REACT_APP_RECONNECT_INTERVAL` | WebSocket reconnection interval (ms) | Number | `5000` | No | `3000` |
| `REACT_APP_MAX_RECONNECT_ATTEMPTS` | Maximum reconnection attempts | Number | `10` | No | `15` |
| `REACT_APP_HEARTBEAT_INTERVAL` | Keep-alive heartbeat interval (ms) | Number | `30000` | No | `25000` |
| `REACT_APP_CONNECTION_TIMEOUT` | Connection timeout (ms) | Number | `10000` | No | `15000` |
| `REACT_APP_DEFAULT_LOCALE` | Default application locale | String | `"en-US"` | No | `"es-MX"` |
| `REACT_APP_TIMEZONE` | Default timezone | String | `"UTC"` | No | `"America/New_York"` |

### Authentication Configuration

Configuration variables related to user authentication and authorization.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_AUTH_ENABLED` | Enable authentication | Boolean | `true` | No | `true` |
| `REACT_APP_AUTH_PROVIDER` | Authentication provider type | String | `"oauth2"` | Yes | `"saml"`, `"oauth2"`, `"ldap"` |
| `REACT_APP_AUTH_URL` | Authentication service URL | URL | None | Yes | `"https://auth.example.com"` |
| `REACT_APP_AUTH_CLIENT_ID` | OAuth2 client identifier | String | None | Yes* | `"cti-client-prod-12345"` |
| `REACT_APP_AUTH_REDIRECT_URI` | OAuth2 redirect URI | URL | None | Yes* | `"https://cti.example.com/callback"` |
| `REACT_APP_AUTH_SCOPE` | OAuth2 requested scopes | String | `"openid profile"` | No | `"openid profile email cti:agent"` |
| `REACT_APP_AUTH_RESPONSE_TYPE` | OAuth2 response type | String | `"code"` | No | `"token"` |
| `REACT_APP_TOKEN_STORAGE` | Token storage mechanism | String | `"sessionStorage"` | No | `"localStorage"`, `"memory"` |
| `REACT_APP_TOKEN_REFRESH_BUFFER` | Token refresh buffer time (seconds) | Number | `300` | No | `600` |
| `REACT_APP_SESSION_TIMEOUT` | Session timeout (minutes) | Number | `30` | No | `60` |
| `REACT_APP_IDLE_TIMEOUT` | Idle timeout before logout (minutes) | Number | `15` | No | `20` |
| `REACT_APP_SSO_ENABLED` | Enable Single Sign-On | Boolean | `false` | No | `true` |
| `REACT_APP_SSO_LOGOUT_URL` | SSO logout endpoint | URL | None | No | `"https://sso.example.com/logout"` |

*Required when `REACT_APP_AUTH_PROVIDER` is set to `"oauth2"`

### CTI Feature Configuration

Variables controlling CTI-specific features and capabilities.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_CTI_PROVIDER` | CTI platform provider | String | `"generic"` | Yes | `"avaya"`, `"genesys"`, `"cisco"`, `"asterisk"` |
| `REACT_APP_ENABLE_SOFTPHONE` | Enable built-in softphone | Boolean | `false` | No | `true` |
| `REACT_APP_SOFTPHONE_TRANSPORT` | Softphone transport protocol | String | `"wss"` | No | `"ws"`, `"wss"` |
| `REACT_APP_SIP_SERVER` | SIP server address | URL | None | Conditional | `"sip.example.com"` |
| `REACT_APP_SIP_PORT` | SIP server port | Number | `5060` | No | `5061` |
| `REACT_APP_ENABLE_SCREEN_POP` | Enable screen pop functionality | Boolean | `true` | No | `true` |
| `REACT_APP_SCREEN_POP_URL` | External screen pop URL template | String | None | No | `"https://crm.example.com/customer/{ani}"` |
| `REACT_APP_ENABLE_CALL_RECORDING` | Enable call recording controls | Boolean | `false` | No | `true` |
| `REACT_APP_RECORDING_CONSENT_REQUIRED` | Require consent for recording | Boolean | `true` | No | `true` |
| `REACT_APP_ENABLE_CALL_TRANSFER` | Enable call transfer feature | Boolean | `true` | No | `true` |
| `REACT_APP_ENABLE_CONFERENCE` | Enable conference calling | Boolean | `true` | No | `true` |
| `REACT_APP_MAX_CONFERENCE_PARTIES` | Maximum conference participants | Number | `5` | No | `8` |
| `REACT_APP_ENABLE_HOLD` | Enable call hold feature | Boolean | `true` | No | `true` |
| `REACT_APP_ENABLE_MUTE` | Enable mute functionality | Boolean | `true` | No | `true` |
| `REACT_APP_ENABLE_DTMF` | Enable DTMF tone sending | Boolean | `true` | No | `true` |
| `REACT_APP_ENABLE_CALLBACK` | Enable callback scheduling | Boolean | `false` | No | `true` |
| `REACT_APP_WRAP_UP_TIME` | Default wrap-up time (seconds) | Number | `30` | No | `60` |
| `REACT_APP_AUTO_ANSWER_ENABLED` | Enable auto-answer mode | Boolean | `false` | No | `true` |
| `REACT_APP_AUTO_ANSWER_DELAY` | Auto-answer delay (ms) | Number | `0` | No | `2000` |

### Agent State Configuration

Configuration for agent presence and state management.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_DEFAULT_AGENT_STATE` | Default agent state on login | String | `"not_ready"` | No | `"ready"` |
| `REACT_APP_AGENT_STATES` | Available agent states (JSON array) | JSON | See below | No | `'["ready","not_ready","break","lunch"]'` |
| `REACT_APP_NOT_READY_REASONS` | Not ready reason codes (JSON array) | JSON | `'[]'` | No | `'[{"code":"BRK","label":"Break"},{"code":"LUN","label":"Lunch"}]'` |
| `REACT_APP_REQUIRE_NOT_READY_REASON` | Require reason for not ready | Boolean | `false` | No | `true` |
| `REACT_APP_ENABLE_FORCED_LOGOUT` | Allow supervisors to force logout | Boolean | `true` | No | `true` |
| `REACT_APP_STATE_SYNC_INTERVAL` | State synchronization interval (ms) | Number | `10000` | No | `5000` |

Default agent states:
```json
["ready", "not_ready", "after_call_work", "on_call", "offline"]
```

### Debug Configuration

Configuration variables for debugging, logging, and development purposes.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_DEBUG_MODE` | Enable debug mode | Boolean | `false` | No | `true` |
| `REACT_APP_LOG_LEVEL` | Application log level | String | `"warn"` | No | `"debug"`, `"info"`, `"warn"`, `"error"` |
| `REACT_APP_ENABLE_CONSOLE_LOGS` | Enable console logging | Boolean | `false` | No | `true` |
| `REACT_APP_ENABLE_REMOTE_LOGGING` | Send logs to remote server | Boolean | `false` | No | `true` |
| `REACT_APP_REMOTE_LOG_URL` | Remote logging endpoint | URL | None | Conditional | `"https://logs.example.com/ingest"` |
| `REACT_APP_LOG_RETENTION_DAYS` | Local log retention (days) | Number | `7` | No | `30` |
| `REACT_APP_ENABLE_PERFORMANCE_MONITORING` | Enable performance metrics | Boolean | `false` | No | `true` |
| `REACT_APP_PERFORMANCE_SAMPLE_RATE` | Performance sampling rate (0-1) | Number | `0.1` | No | `0.5` |
| `REACT_APP_ENABLE_ERROR_REPORTING` | Enable error reporting service | Boolean | `true` | No | `true` |
| `REACT_APP_ERROR_REPORTING_DSN` | Error reporting service DSN | String | None | Conditional | `"https://abc123@sentry.io/12345"` |
| `REACT_APP_ENABLE_REDUX_DEVTOOLS` | Enable Redux DevTools | Boolean | `false` | No | `true` |
| `REACT_APP_MOCK_CTI_SERVER` | Use mock CTI server for testing | Boolean | `false` | No | `true` |
| `REACT_APP_SIMULATE_LATENCY` | Simulate network latency (ms) | Number | `0` | No | `500` |

### UI Configuration

Variables controlling the user interface appearance and behavior.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_THEME` | Application theme | String | `"light"` | No | `"dark"`, `"system"` |
| `REACT_APP_PRIMARY_COLOR` | Primary brand color | String | `"#1976d2"` | No | `"#ff5722"` |
| `REACT_APP_LOGO_URL` | Custom logo URL | URL | None | No | `"/assets/logo.png"` |
| `REACT_APP_FAVICON_URL` | Custom favicon URL | URL | None | No | `"/assets/favicon.ico"` |
| `REACT_APP_ENABLE_SOUND_NOTIFICATIONS` | Enable audio notifications | Boolean | `true` | No | `true` |
| `REACT_APP_ENABLE_DESKTOP_NOTIFICATIONS` | Enable desktop notifications | Boolean | `true` | No | `true` |
| `REACT_APP_NOTIFICATION_DURATION` | Notification display time (ms) | Number | `5000` | No | `8000` |
| `REACT_APP_RING_TONE_URL` | Custom ring tone audio URL | URL | None | No | `"/assets/ringtone.mp3"` |
| `REACT_APP_RING_VOLUME` | Default ring volume (0-100) | Number | `80` | No | `60` |
| `REACT_APP_ENABLE_KEYBOARD_SHORTCUTS` | Enable keyboard shortcuts | Boolean | `true` | No | `true` |
| `REACT_APP_SHOW_CALL_DURATION` | Display call duration timer | Boolean | `true` | No | `true` |
| `REACT_APP_DATE_FORMAT` | Date display format | String | `"MM/DD/YYYY"` | No | `"DD/MM/YYYY"` |
| `REACT_APP_TIME_FORMAT` | Time display format | String | `"12h"` | No | `"24h"` |

### Integration Configuration

Variables for third-party integrations and external services.

| Variable Name | Description | Type | Default | Required | Example |
|--------------|-------------|------|---------|----------|---------|
| `REACT_APP_CRM_INTEGRATION_ENABLED` | Enable CRM integration | Boolean | `false` | No | `true` |
| `REACT_APP_CRM_TYPE` | CRM system type | String | None | Conditional | `"salesforce"`, `"dynamics"`, `"zendesk"` |
| `REACT_APP_CRM_API_URL` | CRM API endpoint | URL | None | Conditional | `"https://crm-api.example.com"` |
| `REACT_APP_ANALYTICS_ENABLED` | Enable analytics tracking | Boolean | `false` | No | `true` |
| `REACT_APP_ANALYTICS_ID` | Analytics tracking ID | String | None | Conditional | `"UA-12345678-1"` |
| `REACT_APP_ENABLE_CHAT_INTEGRATION` | Enable chat channel support | Boolean | `false` | No | `true` |
| `REACT_APP_CHAT_SERVER_URL` | Chat server endpoint | URL | None | Conditional | `"wss://chat.example.com"` |
| `REACT_APP_ENABLE_EMAIL_INTEGRATION` | Enable email channel support | Boolean | `false` | No | `true` |
| `REACT_APP_EMAIL_API_URL` | Email service API endpoint | URL | None | Conditional | `"https://email-api.example.com"` |

---

## Building for Different Environments

### Development Environment

Create a `.env.development` file:

```bash
# ===========================================
# Development Environment Configuration
# Platform CTI Client
# ===========================================

# Application Settings
REACT_APP_NAME="CTI Client (Dev)"
REACT_APP_VERSION="1.0.0-dev"
REACT_APP_ENVIRONMENT="development"
REACT_APP_BASE_URL="http://localhost:3000"

# API Configuration
REACT_APP_API_BASE_URL="http://localhost:8080/api"
REACT_APP_CTI_SERVER_URL="ws://localhost:8081"
REACT_APP_CTI_SERVER_PORT="8081"
REACT_APP_WEBSOCKET_PATH="/ws"

# Connection Settings
REACT_APP_RECONNECT_INTERVAL="3000"
REACT_APP_MAX_RECONNECT_ATTEMPTS="5"
REACT_APP_HEARTBEAT_INTERVAL="30000"
REACT_APP_CONNECTION_TIMEOUT="10000"

# Authentication (Development - Relaxed)
REACT_APP_AUTH_ENABLED="true"
REACT_APP_AUTH_PROVIDER="oauth2"
REACT_APP_AUTH_URL="http://localhost:8082/auth"
REACT_APP_AUTH_CLIENT_ID="cti-client-dev"
REACT_APP_AUTH_REDIRECT_URI="http://localhost:3000/callback"
REACT_APP_AUTH_SCOPE="openid profile email"
REACT_APP_TOKEN_STORAGE="localStorage"
REACT_APP_SESSION_TIMEOUT="120"
REACT_APP_IDLE_TIMEOUT="60"

# CTI Features
REACT_APP_CTI_PROVIDER="generic"
REACT_APP_ENABLE_SOFTPHONE="false"
REACT_APP_ENABLE_SCREEN_POP="true"
REACT_APP_ENABLE_CALL_RECORDING="true"
REACT_APP_ENABLE_CALL_TRANSFER="true"
REACT_APP_ENABLE_CONFERENCE="true"
REACT_APP_WRAP_UP_TIME="30"

# Agent Configuration
REACT_APP_DEFAULT_AGENT_STATE="not_ready"
REACT_APP_REQUIRE_NOT_READY_REASON="false"

# Debug Settings (Verbose for development)
REACT_APP_DEBUG_MODE="true"
REACT_APP_LOG_LEVEL="debug"
REACT_APP_ENABLE_CONSOLE_LOGS="true"
REACT_APP_ENABLE_REMOTE_LOGGING="false"
REACT_APP_ENABLE_REDUX_DEVTOOLS="true"
REACT_APP_MOCK_CTI_SERVER="true"
REACT_APP_SIMULATE_LATENCY="200"

# UI Settings
REACT_APP_THEME="light"
REACT_APP_ENABLE_SOUND_NOTIFICATIONS="true"
REACT_APP_ENABLE_DESKTOP_NOTIFICATIONS="true"

# Integrations (Disabled for development)
REACT_APP_CRM_INTEGRATION_ENABLED="false"
REACT_APP_ANALYTICS_ENABLED="false"
```

### Staging Environment

Create a `.env.staging` file:

```bash
# ===========================================
# Staging Environment Configuration
# Platform CTI Client
# ===========================================

# Application Settings
REACT_APP_NAME="CTI Client (Staging)"
REACT_APP_VERSION="1.0.0-rc1"
REACT_APP_ENVIRONMENT="staging"
REACT_APP_BASE_URL="https://cti-staging.example.com"

# API Configuration
REACT_APP_API_BASE_URL="https://api-staging.example.com/v1"
REACT_APP_CTI_SERVER_URL="wss://cti-server-staging.example.com"
REACT_APP_CTI_SERVER_PORT="443"
REACT_APP_WEBSOCKET_PATH="/cti/ws"

# Connection Settings
REACT_APP_RECONNECT_INTERVAL="5000"
REACT_APP_MAX_RECONNECT_ATTEMPTS="10"
REACT_APP_HEARTBEAT_INTERVAL="25000"
REACT_APP_CONNECTION_TIMEOUT="15000"

# Authentication
REACT_APP_AUTH_ENABLED="true"
REACT_APP_AUTH_PROVIDER="oauth2"
REACT_APP_AUTH_URL="https://auth-staging.example.com"
REACT_APP_AUTH_CLIENT_ID="cti-client-staging-abc123"
REACT_APP_AUTH_REDIRECT_URI="https://cti-staging.example.com/callback"
REACT_APP_AUTH_SCOPE="openid profile email cti:agent"
REACT_APP_TOKEN_STORAGE="sessionStorage"
REACT_APP_SESSION_TIMEOUT="60"
REACT_APP_IDLE_TIMEOUT="30"
REACT_APP_SSO_ENABLED="true"
REACT_APP_SSO_LOGOUT_URL="https://sso-staging.example.com/logout"

# CTI Features
REACT_APP_CTI_PROVIDER="genesys"
REACT_APP_ENABLE_SOFTPHONE="true"
REACT_APP_SOFTPHONE_TRANSPORT="wss"
REACT_APP_SIP_SERVER="sip-staging.example.com"
REACT_APP_SIP_PORT="5061"
REACT_APP_ENABLE_SCREEN_POP="true"
REACT_APP_SCREEN_POP_URL="https://crm-staging.example.com/customer/{ani}"
REACT_APP_ENABLE_CALL_RECORDING="true"
REACT_APP_RECORDING_CONSENT_REQUIRED="true"
REACT_APP_ENABLE_CALL_TRANSFER="true"
REACT_APP_ENABLE_CONFERENCE="true"
REACT_APP_MAX_CONFERENCE_PARTIES="6"
REACT_APP_WRAP_UP_TIME="45"
REACT_APP_AUTO_ANSWER_ENABLED="false"

# Agent Configuration
REACT_APP_DEFAULT_AGENT_STATE="not_ready"
REACT_APP_AGENT_STATES='["ready","not_ready","after_call_work","break","lunch","meeting","training"]'
REACT_APP_NOT_READY_REASONS='[{"code":"BRK","label":"Break"},{"code":"LUN","label":"Lunch"},{"code":"MTG","label":"Meeting"},{"code":"TRN","label":"Training"}]'
REACT_APP_REQUIRE_NOT_READY_REASON="true"

# Debug Settings (Moderate logging)
REACT_APP_DEBUG_MODE="false"
REACT_APP_LOG_LEVEL="info"
REACT_APP_ENABLE_CONSOLE_LOGS="true"
REACT_APP_ENABLE_REMOTE_LOGGING="true"
REACT_APP_REMOTE_LOG_URL="https://logs-staging.example.com/ingest"
REACT_APP_ENABLE_PERFORMANCE_MONITORING="true"
REACT_APP_PERFORMANCE_SAMPLE_RATE="0.5"
REACT_APP_ENABLE_ERROR_REPORTING="true"
REACT_APP_ERROR_REPORTING_DSN="https://staging-key@sentry.io/staging-project"
REACT_APP_ENABLE_REDUX_DEVTOOLS="false"
REACT_APP_MOCK_CTI_SERVER="false"

# UI Settings
REACT_APP_THEME="light"
REACT_APP_PRIMARY_COLOR="#1976d2"
REACT_APP_LOGO_URL="/assets/logo-staging.png"
REACT_APP_ENABLE_SOUND_NOTIFICATIONS="true"
REACT_APP_ENABLE_DESKTOP_NOTIFICATIONS="true"
REACT_APP_NOTIFICATION_DURATION="5000"

# Integrations
REACT_APP_CRM_INTEGRATION_ENABLED="true"
REACT_APP_CRM_TYPE="salesforce"
REACT_APP_CRM_API_URL="https://crm-api-staging.example.com"
REACT_APP_ANALYTICS_ENABLED="true"
REACT_APP_ANALYTICS_ID="UA-STAGING-1"
```

### Production Environment

Create a `.env.production` file:

```bash
# ===========================================
# Production Environment Configuration
# Platform CTI Client
# ===========================================

# Application Settings
REACT_APP_NAME="Contact Center CTI"
REACT_APP_VERSION="1.0.0"
REACT_APP_ENVIRONMENT="production"
REACT_APP_BASE_URL="https://cti.example.com"

# API Configuration
REACT_APP_API_BASE_URL="https://api.example.com/v1"
REACT_APP_CTI_SERVER_URL="wss://cti-server.example.com"
REACT_APP_CTI_SERVER_PORT="443"
REACT_APP_WEBSOCKET_PATH="/cti/ws"

# Connection Settings (Optimized for reliability)
REACT_APP_RECONNECT_INTERVAL="3000"
REACT_APP_MAX_RECONNECT_ATTEMPTS="20"
REACT_APP_HEARTBEAT_INTERVAL="20000"
REACT_APP_CONNECTION_TIMEOUT="10000"

# Authentication (Production - Strict)
REACT_APP_AUTH_ENABLED="true"
REACT_APP_AUTH_PROVIDER="oauth2"
REACT_APP_AUTH_URL="https://auth.example.com"
REACT_APP_AUTH_CLIENT_ID="${CTI_CLIENT_ID}"
REACT_APP_AUTH_REDIRECT_URI="https://cti.example.com/callback"
REACT_APP_AUTH_SCOPE="openid profile email cti:agent cti:supervisor"
REACT_APP_TOKEN_STORAGE="sessionStorage"
REACT_APP_TOKEN_REFRESH_BUFFER="600"
REACT_APP_SESSION_TIMEOUT="30"
REACT_APP_IDLE_TIMEOUT="15"
REACT_APP_SSO_ENABLED="true"
REACT_APP_SSO_LOGOUT_URL="https://sso.example.com/logout"

# CTI Features (Full production capabilities)
REACT_APP_CTI_PROVIDER="genesys"
REACT_APP_ENABLE_SOFTPHONE="true"
REACT_APP_SOFTPHONE_TRANSPORT="wss"
REACT_APP_SIP_SERVER="sip.example.com"
REACT_APP_SIP_PORT="5061"
REACT_APP_ENABLE_SCREEN_POP="true"
REACT_APP_SCREEN_POP_URL="https://crm.example.com/customer/{ani}"
REACT_APP_ENABLE_CALL_RECORDING="true"
REACT_APP_RECORDING_CONSENT_REQUIRED="true"
REACT_APP_ENABLE_CALL_TRANSFER="true"
REACT_APP_ENABLE_CONFERENCE="true"
REACT_APP_MAX_CONFERENCE_PARTIES="8"
REACT_APP_ENABLE_HOLD="true"
REACT_APP_ENABLE_MUTE="true"
REACT_APP_ENABLE_DTMF="true"
REACT_APP_ENABLE_CALLBACK="true"
REACT_APP_WRAP_UP_TIME="60"
REACT_APP_AUTO_ANSWER_ENABLED="false"

# Agent Configuration
REACT_APP_DEFAULT_AGENT_STATE="not_ready"
REACT_APP_AGENT_STATES='["ready","not_ready","after_call_work","break","lunch","meeting","training","coaching"]'
REACT_APP_NOT_READY_REASONS='[{"code":"BRK","label":"Break"},{"code":"LUN","label":"Lunch"},{"code":"MTG","label":"Meeting"},{"code":"TRN","label":"Training"},{"code":"COA","label":"Coaching"},{"code":"ADM","label":"Administrative"},{"code":"SYS","label":"System Issues"}]'
REACT_APP_REQUIRE_NOT_READY_REASON="true"
REACT_APP_ENABLE_FORCED_LOGOUT="true"
REACT_APP_STATE_SYNC_INTERVAL="5000"

# Debug Settings (Minimal, security-focused)
REACT_APP_DEBUG_MODE="false"
REACT_APP_LOG_LEVEL="error"
REACT_APP_ENABLE_CONSOLE_LOGS="false"
REACT_APP_ENABLE_REMOTE_LOGGING="true"
REACT_APP_REMOTE_LOG_URL="https://logs.example.com/ingest"
REACT_APP_LOG_RETENTION_DAYS="90"
REACT_APP_ENABLE_PERFORMANCE_MONITORING="true"
REACT_APP_PERFORMANCE_SAMPLE_RATE="0.1"
REACT_APP_ENABLE_ERROR_REPORTING="true"
REACT_APP_ERROR_REPORTING_DSN="${SENTRY_DSN}"
REACT_APP_ENABLE_REDUX_DEVTOOLS="false"
REACT_APP_MOCK_CTI_SERVER="false"
REACT_APP_SIMULATE_LATENCY="0"

# UI Settings
REACT_APP_THEME="system"
REACT_APP_PRIMARY_COLOR="#0d47a1"
REACT_APP_LOGO_URL="/assets/logo.png"
REACT_APP_FAVICON_URL="/assets/favicon.ico"
REACT_APP_ENABLE_SOUND_NOTIFICATIONS="true"
REACT_APP_ENABLE_DESKTOP_NOTIFICATIONS="true"
REACT_APP_NOTIFICATION_DURATION="5000"
REACT_APP_RING_TONE_URL="/assets/ringtone.mp3"
REACT_APP_RING_VOLUME="80"
REACT_APP_ENABLE_KEYBOARD_SHORTCUTS="true"
REACT_APP_DATE_FORMAT="MM/DD/YYYY"
REACT_APP_TIME_FORMAT="12h"

# Integrations (Full production)
REACT_APP_CRM_INTEGRATION_ENABLED="true"
REACT_APP_CRM_TYPE="salesforce"
REACT_APP_CRM_API_URL="https://crm-api.example.com"
REACT_APP_ANALYTICS_ENABLED="true"
REACT_APP_ANALYTICS_ID="${ANALYTICS_ID}"
REACT_APP_ENABLE_CHAT_INTEGRATION="true"
REACT_APP_CHAT_SERVER_URL="wss://chat.example.com"
REACT_APP_ENABLE_EMAIL_INTEGRATION="true"
REACT_APP_EMAIL_API_URL="https://email-api.example.com"

# Localization
REACT_APP_DEFAULT_LOCALE="en-US"
REACT_APP_TIMEZONE="America/New_York"
```

---

## Security Considerations

### Sensitive Values

The following configuration variables contain sensitive information and should be handled securely:

| Variable | Sensitivity Level | Recommendation |
|----------|------------------|----------------|
| `REACT_APP_AUTH_CLIENT_ID` | High | Use environment variables, never commit |
| `REACT_APP_ERROR_REPORTING_DSN` | Medium | Use environment variables |
| `REACT_APP_ANALYTICS_ID` | Low | Can be public, but prefer env vars |
| `REACT_APP_CRM_API_URL` | Medium | Internal URLs should not be exposed |
| `REACT_APP_REMOTE_LOG_URL` | Medium | Internal URLs should not be exposed |

### Best Practices

1. **Never commit `.env` files to version control**
   ```gitignore
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Use environment variable substitution for sensitive values**
   ```bash
   REACT_APP_AUTH_CLIENT_ID="${CTI_CLIENT_ID}"
   ```

3. **Implement Content Security Policy (CSP) headers**
   ```javascript
   // Restrict WebSocket connections
   "connect-src 'self' wss://cti-server.example.com"
   ```

4. **Use sessionStorage over localStorage for tokens**
   - Prevents token persistence across browser sessions
   - Reduces XSS attack surface

5. **Enable HTTPS in production**
   - All URLs should use `https://` or `wss://`
   - Never use unencrypted connections for sensitive data

6. **Implement token refresh mechanisms**
   - Set appropriate `REACT_APP_TOKEN_REFRESH_BUFFER`
   - Handle token expiration gracefully

7. **Configure appropriate timeouts**
   - Short session timeouts for high-security environments
   - Implement idle timeout to protect unattended sessions

---

## Troubleshooting Common Configuration Issues

### WebSocket Connection Failures

**Symptoms:** CTI client cannot connect to the CTI server

**Possible Causes & Solutions:**

| Issue | Solution |
|-------|----------|
| Wrong protocol | Ensure `wss://` for production, `ws://` only for local development |
| Port blocked | Verify firewall rules allow WebSocket port (typically 443 or 8081) |
| Path mismatch | Check `REACT_APP_WEBSOCKET_PATH` matches server configuration |
| SSL certificate issues | Verify certificates are valid and trusted |

```bash
# Test WebSocket connectivity
wscat -c wss://cti-server.example.com/cti/ws
```

### Authentication Errors

**Symptoms:** Users cannot log in or receive 401 errors

**Possible Causes & Solutions:**

| Issue | Solution |
|-------|----------|
| Incorrect redirect URI | Ensure `REACT_APP_AUTH_REDIRECT_URI` matches OAuth configuration |
| Invalid client ID | Verify `REACT_APP_AUTH_CLIENT_ID` with identity provider |
| Scope mismatch | Check `REACT_APP_AUTH_SCOPE` is approved in OAuth application |
| Token storage issues | Try changing `REACT_APP_TOKEN_STORAGE` to `"memory"` for testing |

### Performance Issues

**Symptoms:** Slow UI, delayed call notifications, dropped connections

**Possible Causes & Solutions:**

| Issue | Solution |
|-------|----------|
| Aggressive heartbeat | Increase `REACT_APP_HEARTBEAT_INTERVAL` to reduce overhead |
| Excessive logging | Set `REACT_APP_LOG_LEVEL` to `"error"` in production |
| Debug mode enabled | Ensure `REACT_APP_DEBUG_MODE` is `"false"` in production |
| High reconnect frequency | Increase `REACT_APP_RECONNECT_INTERVAL` |

### Agent State Synchronization

**Symptoms:** Agent state doesn't update, shows incorrect status

**Possible Causes & Solutions:**

| Issue | Solution |
|-------|----------|
| Sync interval too long | Decrease `REACT_APP_STATE_SYNC_INTERVAL` |
| Missing state definitions | Verify `REACT_APP_AGENT_STATES` includes all required states |
| Server mismatch | Ensure state codes match backend configuration |

---

## Complete Example .env File

```bash
# ===========================================
# Platform CTI Client - Complete Configuration
# Environment: [REPLACE_WITH_ENVIRONMENT]
# Last Updated: [REPLACE_WITH_DATE]
# ===========================================

#-------------------------------------------
# Application Identity
#-------------------------------------------
REACT_APP_NAME="Contact Center CTI"
REACT_APP_VERSION="1.0.0"
REACT_APP_ENVIRONMENT="production"
REACT_APP_BASE_URL="https://cti.example.com"
REACT_APP_DEFAULT_LOCALE="en-US"
REACT_APP_TIMEZONE="America/New_York"

#-------------------------------------------
# API & Server Configuration
#-------------------------------------------
REACT_APP_API_BASE_URL="https://api.example.com/v1"
REACT_APP_CTI_SERVER_URL="wss://cti-server.example.com"
REACT_APP_CTI_SERVER_PORT="443"
REACT_APP_WEBSOCKET_PATH="/cti/ws"
REACT_APP_RECONNECT_INTERVAL="3000"
REACT_APP_MAX_RECONNECT_ATTEMPTS="20"
REACT_APP_HEARTBEAT_INTERVAL="20000"
REACT_APP_CONNECTION_TIMEOUT="10000"

#-------------------------------------------
# Authentication
#-------------------------------------------
REACT_APP_AUTH_ENABLED="true"
REACT_APP_AUTH_PROVIDER="oauth2"
REACT_APP_AUTH_URL="https://auth.example.com"
REACT_APP_AUTH_CLIENT_ID="${CTI_CLIENT_ID}"
REACT_APP_AUTH_REDIRECT_URI="https://cti.example.com/callback"
REACT_APP_AUTH_SCOPE="openid profile email cti:agent"
REACT_APP_AUTH_RESPONSE_TYPE="code"
REACT_APP_TOKEN_STORAGE="sessionStorage"
REACT_APP_TOKEN_REFRESH_BUFFER="600"
REACT_APP_SESSION_TIMEOUT="30"
REACT_APP_IDLE_TIMEOUT="15"
REACT_APP_SSO_ENABLED="true"
REACT_APP_SSO_LOGOUT_URL="https://sso.example.com/logout"

#-------------------------------------------
# CTI Features
#-------------------------------------------
REACT_APP_CTI_PROVIDER="genesys"
REACT_APP_ENABLE_SOFTPHONE="true"
REACT_APP_SOFTPHONE_TRANSPORT="wss"
REACT_APP_SIP_SERVER="sip.example.com"
REACT_APP_SIP_PORT="5061"
REACT_APP_ENABLE_SCREEN_POP="true"
REACT_APP_SCREEN_POP_URL="https://crm.example.com/customer/{ani}"
REACT_APP_ENABLE_CALL_RECORDING="true"
REACT_APP_RECORDING_CONSENT_REQUIRED="true"
REACT_APP_ENABLE_CALL_TRANSFER="true"
REACT_APP_ENABLE_CONFERENCE="true"
REACT_APP_MAX_CONFERENCE_PARTIES="8"
REACT_APP_ENABLE_HOLD="true"
REACT_APP_ENABLE_MUTE="true"
REACT_APP_ENABLE_DTMF="true"
REACT_APP_ENABLE_CALLBACK="true"
REACT_APP_WRAP_UP_TIME="60"
REACT_APP_AUTO_ANSWER_ENABLED="false"
REACT_APP_AUTO_ANSWER_DELAY="0"

#-------------------------------------------
# Agent State Management
#-------------------------------------------
REACT_APP_DEFAULT_AGENT_STATE="not_ready"
REACT_APP_AGENT_STATES='["ready","not_ready","after_call_work","break","lunch","meeting","training","coaching"]'
REACT_APP_NOT_READY_REASONS='[{"code":"BRK","label":"Break"},{"code":"LUN","label":"Lunch"},{"code":"MTG","label":"Meeting"},{"code":"TRN","label":"Training"},{"code":"COA","label":"Coaching"},{"code":"ADM","label":"Administrative"},{"code":"SYS","label":"System Issues"}]'
REACT_APP_REQUIRE_NOT_READY_REASON="true"
REACT_APP_ENABLE_FORCED_LOGOUT="true"
REACT_APP_STATE_SYNC_INTERVAL="5000"

#-------------------------------------------
# Debug & Monitoring
#-------------------------------------------
REACT_APP_DEBUG_MODE="false"
REACT_APP_LOG_LEVEL="error"
REACT_APP_ENABLE_CONSOLE_LOGS="false"
REACT_APP_ENABLE_REMOTE_LOGGING="true"
REACT_APP_REMOTE_LOG_URL="https://logs.example.com/ingest"
REACT_APP_LOG_RETENTION_DAYS="90"
REACT_APP_ENABLE_PERFORMANCE_MONITORING="true"
REACT_APP_PERFORMANCE_SAMPLE_RATE="0.1"
REACT_APP_ENABLE_ERROR_REPORTING="true"
REACT_APP_ERROR_REPORTING_DSN="${SENTRY_DSN}"
REACT_APP_ENABLE_REDUX_DEVTOOLS="false"
REACT_APP_MOCK_CTI_SERVER="false"
REACT_APP_SIMULATE_LATENCY="0"

#-------------------------------------------
# User Interface
#-------------------------------------------
REACT_APP_THEME="system"
REACT_APP_PRIMARY_COLOR="#0d47a1"
REACT_APP_LOGO_URL="/assets/logo.png"
REACT_APP_FAVICON_URL="/assets/favicon.ico"
REACT_APP_ENABLE_SOUND_NOTIFICATIONS="true"
REACT_APP_ENABLE_DESKTOP_NOTIFICATIONS="true"
REACT_APP_NOTIFICATION_DURATION="5000"
REACT_APP_RING_TONE_URL="/assets/ringtone.mp3"
REACT_APP_RING_VOLUME="80"
REACT_APP_ENABLE_KEYBOARD_SHORTCUTS="true"
REACT_APP_SHOW_CALL_DURATION="true"
REACT_APP_DATE_FORMAT="MM/DD/YYYY"
REACT_APP_TIME_FORMAT="12h"

#-------------------------------------------
# Integrations
#-------------------------------------------
REACT_APP_CRM_INTEGRATION_ENABLED="true"
REACT_APP_CRM_TYPE="salesforce"
REACT_APP_CRM_API_URL="https://crm-api.example.com"
REACT_APP_ANALYTICS_ENABLED="true"
REACT_APP_ANALYTICS_ID="${ANALYTICS_ID}"
REACT_APP_ENABLE_CHAT_INTEGRATION="true"
REACT_APP_CHAT_SERVER_URL="wss://chat.example.com"
REACT_APP_ENABLE_EMAIL_INTEGRATION="true"
REACT_APP_EMAIL_API_URL="https://email-api.example.com"
```

---

## Docker Configuration

For containerized deployments, use build arguments to inject environment variables:

```dockerfile
# Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# Build arguments for environment variables
ARG REACT_APP_ENVIRONMENT=production
ARG REACT_APP_API_BASE_URL
ARG REACT_APP_CTI_SERVER_URL
ARG REACT_APP_AUTH_URL
ARG REACT_APP_AUTH_CLIENT_ID

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build \
  --build-arg REACT_APP_ENVIRONMENT=production \
  --build-arg REACT_APP_API_BASE_URL=https://api.example.com/v1 \
  --build-arg REACT_APP_CTI_SERVER_URL=wss://cti-server.example.com \
  --build-arg REACT_APP_AUTH_URL=https://auth.example.com \
  --build-arg REACT_APP_AUTH_CLIENT_ID=$CTI_CLIENT_ID \
  -t platform-cti-client:latest .

docker run -p 80:80 platform-cti-client:latest
```

---

## Kubernetes Configuration

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cti-client-config
  namespace: contact-center
data:
  REACT_APP_ENVIRONMENT: "production"
  REACT_APP_API_BASE_URL: "https://api.example.com/v1"
  REACT_APP_CTI_SERVER_URL: "wss://cti-server.example.com"
  REACT_APP_WEBSOCKET_PATH: "/cti/ws"
  REACT_APP_CTI_PROVIDER: "genesys"
  REACT_APP_ENABLE_SOFTPHONE: "true"
  REACT_APP_LOG_LEVEL: "error"
---
# kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cti-client-secrets
  namespace: contact-center
type: Opaque
stringData:
  REACT_APP_AUTH_CLIENT_ID: "your-client-id"
  REACT_APP_ERROR_REPORTING_DSN: "https://key@sentry.io/project"
---
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cti-client
  namespace: contact-center
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cti-client
  template:
    metadata:
      labels:
        app: cti-client
    spec:
      containers:
      - name: cti-client
        image: platform-cti-client:latest
        ports:
        - containerPort: 80
        envFrom:
        - configMapRef:
            name: cti-client-config
        - secretRef:
            name: cti-client-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

---

This configuration guide provides comprehensive documentation for deploying and configuring the platform-cti-client across all environments. For additional support or custom configuration requirements, consult the platform architecture team.