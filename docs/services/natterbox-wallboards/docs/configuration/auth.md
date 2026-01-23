# Authentication Configuration

## Natterbox Wallboards

### Overview

Natterbox Wallboards is a real-time call center monitoring and visualization service that integrates with the Natterbox telephony platform. This documentation provides comprehensive configuration guidance for authentication setup, covering Auth0 integration, OAuth token management, and environment-specific security configurations.

The authentication system uses Auth0 as the identity provider, implementing OAuth 2.0 with JWT tokens for secure API access. Proper configuration ensures secure user authentication, seamless session management, and appropriate access control for wallboard data.

---

## Auth0 Setup

### Prerequisites

Before configuring authentication, ensure you have:

1. An Auth0 tenant with administrative access
2. A registered application in Auth0 for Natterbox Wallboards
3. API credentials (Client ID and Client Secret)
4. Configured callback URLs for your deployment environments

### Auth0 Application Configuration

Create a new application in your Auth0 dashboard with the following settings:

| Setting | Value | Description |
|---------|-------|-------------|
| Application Type | Single Page Application | SPA for browser-based wallboard access |
| Token Endpoint Authentication | None | Public client configuration |
| Allowed Callback URLs | See environment section | OAuth redirect destinations |
| Allowed Logout URLs | See environment section | Post-logout redirect destinations |
| Allowed Web Origins | See environment section | CORS origins for token refresh |
| ID Token Expiration | 36000 | 10-hour token lifetime (seconds) |
| Refresh Token Rotation | Enabled | Enhanced security for long sessions |

### Auth0 API Configuration

Register an API in Auth0 for the Natterbox Wallboards backend:

| Setting | Value | Description |
|---------|-------|-------------|
| Identifier | `https://api.natterbox.com/wallboards` | Unique API identifier (audience) |
| Signing Algorithm | RS256 | RSA signature with SHA-256 |
| RBAC | Enabled | Role-based access control |
| Add Permissions in Token | Enabled | Include scopes in access token |

---

## Environment Variables

### Core Authentication Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `AUTH0_DOMAIN` | Auth0 tenant domain | String | None | **Yes** | `natterbox.eu.auth0.com` |
| `AUTH0_CLIENT_ID` | Application client identifier | String | None | **Yes** | `aB3cD4eF5gH6iJ7kL8mN9oP0` |
| `AUTH0_CLIENT_SECRET` | Application client secret | String | None | **Yes** | `xYz123AbC456DeF789GhI012JkL345` |
| `AUTH0_AUDIENCE` | API identifier for token validation | String | None | **Yes** | `https://api.natterbox.com/wallboards` |
| `AUTH0_ISSUER_BASE_URL` | Full issuer URL for token verification | String | None | **Yes** | `https://natterbox.eu.auth0.com` |
| `AUTH0_ALGORITHM` | JWT signing algorithm | String | `RS256` | No | `RS256` |
| `AUTH0_JWKS_URI` | JSON Web Key Set endpoint | String | Auto-derived | No | `https://natterbox.eu.auth0.com/.well-known/jwks.json` |

### URL Configuration Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `APP_BASE_URL` | Application base URL | URL | None | **Yes** | `https://wallboards.natterbox.com` |
| `AUTH0_CALLBACK_URL` | OAuth callback endpoint | URL | `${APP_BASE_URL}/callback` | No | `https://wallboards.natterbox.com/callback` |
| `AUTH0_LOGOUT_URL` | Post-logout redirect URL | URL | `${APP_BASE_URL}` | No | `https://wallboards.natterbox.com` |
| `AUTH0_LOGIN_URL` | Custom login page URL | URL | Auth0 hosted | No | `https://wallboards.natterbox.com/login` |
| `API_BASE_URL` | Backend API base URL | URL | None | **Yes** | `https://api.natterbox.com/wallboards/v1` |
| `WEBSOCKET_URL` | Real-time data WebSocket endpoint | URL | None | **Yes** | `wss://ws.natterbox.com/wallboards` |

### Token Management Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `TOKEN_EXPIRY_BUFFER` | Seconds before expiry to refresh token | Integer | `300` | No | `300` |
| `ACCESS_TOKEN_LIFETIME` | Access token validity period (seconds) | Integer | `7200` | No | `7200` |
| `REFRESH_TOKEN_LIFETIME` | Refresh token validity period (seconds) | Integer | `2592000` | No | `2592000` |
| `SESSION_COOKIE_SECRET` | Secret for session cookie encryption | String | None | **Yes** | `super-secret-key-min-32-chars!!!` |
| `SESSION_COOKIE_NAME` | Name of the session cookie | String | `appSession` | No | `natterbox_wallboards_session` |
| `SESSION_COOKIE_SECURE` | Require HTTPS for cookies | Boolean | `true` | No | `true` |
| `SESSION_COOKIE_HTTPONLY` | Prevent JavaScript cookie access | Boolean | `true` | No | `true` |
| `SESSION_COOKIE_SAMESITE` | SameSite cookie attribute | String | `Lax` | No | `Strict` |
| `SESSION_ABSOLUTE_DURATION` | Maximum session lifetime (seconds) | Integer | `86400` | No | `86400` |
| `SESSION_ROLLING_DURATION` | Inactivity timeout (seconds) | Integer | `3600` | No | `3600` |

### Security Configuration Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `ENABLE_PKCE` | Enable Proof Key for Code Exchange | Boolean | `true` | No | `true` |
| `ENABLE_STATE_PARAM` | Enable OAuth state parameter | Boolean | `true` | No | `true` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | String | None | **Yes** | `https://wallboards.natterbox.com,https://admin.natterbox.com` |
| `CSP_FRAME_ANCESTORS` | Content Security Policy frame ancestors | String | `'none'` | No | `'self'` |
| `RATE_LIMIT_AUTH_REQUESTS` | Max auth requests per minute per IP | Integer | `10` | No | `10` |
| `ENABLE_MFA` | Require multi-factor authentication | Boolean | `false` | No | `true` |
| `MFA_REMEMBER_DEVICE_DAYS` | Days to remember MFA device | Integer | `30` | No | `30` |

### Logging and Debugging Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `AUTH_LOG_LEVEL` | Authentication logging verbosity | String | `info` | No | `debug` |
| `LOG_TOKEN_EVENTS` | Log token refresh/expiry events | Boolean | `false` | No | `true` |
| `LOG_AUTH_FAILURES` | Log authentication failures | Boolean | `true` | No | `true` |
| `ENABLE_AUTH_DEBUG` | Enable detailed auth debugging | Boolean | `false` | No | `false` |

---

## authConfig Options

The `authConfig` object centralizes authentication configuration for the application:

```javascript
// config/auth.config.js
const authConfig = {
  // Auth0 Connection Settings
  auth0: {
    domain: process.env.AUTH0_DOMAIN,
    clientId: process.env.AUTH0_CLIENT_ID,
    clientSecret: process.env.AUTH0_CLIENT_SECRET,
    audience: process.env.AUTH0_AUDIENCE,
    issuerBaseUrl: process.env.AUTH0_ISSUER_BASE_URL,
    algorithm: process.env.AUTH0_ALGORITHM || 'RS256',
  },

  // URL Configuration
  urls: {
    baseUrl: process.env.APP_BASE_URL,
    callbackUrl: process.env.AUTH0_CALLBACK_URL || `${process.env.APP_BASE_URL}/callback`,
    logoutUrl: process.env.AUTH0_LOGOUT_URL || process.env.APP_BASE_URL,
    loginUrl: process.env.AUTH0_LOGIN_URL,
    apiBaseUrl: process.env.API_BASE_URL,
    websocketUrl: process.env.WEBSOCKET_URL,
  },

  // Token Management
  tokens: {
    expiryBuffer: parseInt(process.env.TOKEN_EXPIRY_BUFFER, 10) || 300,
    accessTokenLifetime: parseInt(process.env.ACCESS_TOKEN_LIFETIME, 10) || 7200,
    refreshTokenLifetime: parseInt(process.env.REFRESH_TOKEN_LIFETIME, 10) || 2592000,
  },

  // Session Configuration
  session: {
    secret: process.env.SESSION_COOKIE_SECRET,
    name: process.env.SESSION_COOKIE_NAME || 'appSession',
    cookie: {
      secure: process.env.SESSION_COOKIE_SECURE !== 'false',
      httpOnly: process.env.SESSION_COOKIE_HTTPONLY !== 'false',
      sameSite: process.env.SESSION_COOKIE_SAMESITE || 'Lax',
    },
    absoluteDuration: parseInt(process.env.SESSION_ABSOLUTE_DURATION, 10) || 86400,
    rollingDuration: parseInt(process.env.SESSION_ROLLING_DURATION, 10) || 3600,
  },

  // Security Options
  security: {
    enablePkce: process.env.ENABLE_PKCE !== 'false',
    enableStateParam: process.env.ENABLE_STATE_PARAM !== 'false',
    allowedOrigins: process.env.ALLOWED_ORIGINS?.split(',') || [],
    cspFrameAncestors: process.env.CSP_FRAME_ANCESTORS || "'none'",
    rateLimitAuthRequests: parseInt(process.env.RATE_LIMIT_AUTH_REQUESTS, 10) || 10,
    enableMfa: process.env.ENABLE_MFA === 'true',
    mfaRememberDeviceDays: parseInt(process.env.MFA_REMEMBER_DEVICE_DAYS, 10) || 30,
  },

  // Logging Configuration
  logging: {
    level: process.env.AUTH_LOG_LEVEL || 'info',
    tokenEvents: process.env.LOG_TOKEN_EVENTS === 'true',
    authFailures: process.env.LOG_AUTH_FAILURES !== 'false',
    enableDebug: process.env.ENABLE_AUTH_DEBUG === 'true',
  },
};

module.exports = authConfig;
```

### authConfig Options Reference

| Option Path | Description | Type | Default |
|-------------|-------------|------|---------|
| `auth0.domain` | Auth0 tenant domain | String | Required |
| `auth0.clientId` | OAuth client identifier | String | Required |
| `auth0.clientSecret` | OAuth client secret | String | Required |
| `auth0.audience` | API audience identifier | String | Required |
| `auth0.issuerBaseUrl` | Token issuer URL | String | Required |
| `auth0.algorithm` | JWT signing algorithm | String | `RS256` |
| `urls.baseUrl` | Application base URL | String | Required |
| `urls.callbackUrl` | OAuth callback URL | String | `{baseUrl}/callback` |
| `urls.logoutUrl` | Post-logout redirect | String | `{baseUrl}` |
| `urls.loginUrl` | Custom login URL | String | Auth0 hosted |
| `urls.apiBaseUrl` | Backend API URL | String | Required |
| `urls.websocketUrl` | WebSocket endpoint | String | Required |
| `tokens.expiryBuffer` | Pre-refresh buffer (seconds) | Integer | `300` |
| `tokens.accessTokenLifetime` | Access token TTL | Integer | `7200` |
| `tokens.refreshTokenLifetime` | Refresh token TTL | Integer | `2592000` |
| `session.secret` | Cookie encryption key | String | Required |
| `session.name` | Session cookie name | String | `appSession` |
| `session.cookie.secure` | HTTPS-only cookies | Boolean | `true` |
| `session.cookie.httpOnly` | HTTP-only cookies | Boolean | `true` |
| `session.cookie.sameSite` | SameSite attribute | String | `Lax` |
| `session.absoluteDuration` | Max session lifetime | Integer | `86400` |
| `session.rollingDuration` | Inactivity timeout | Integer | `3600` |
| `security.enablePkce` | Use PKCE flow | Boolean | `true` |
| `security.enableStateParam` | Use state parameter | Boolean | `true` |
| `security.allowedOrigins` | CORS origins | Array | `[]` |
| `security.rateLimitAuthRequests` | Auth rate limit | Integer | `10` |
| `security.enableMfa` | Require MFA | Boolean | `false` |
| `logging.level` | Log verbosity | String | `info` |
| `logging.tokenEvents` | Log token events | Boolean | `false` |
| `logging.authFailures` | Log auth failures | Boolean | `true` |

---

## Token Management

### Token Lifecycle

The authentication system manages three types of tokens:

1. **ID Token**: Contains user identity claims, used for UI personalization
2. **Access Token**: Bearer token for API authorization
3. **Refresh Token**: Long-lived token for obtaining new access tokens

### Token Refresh Strategy

```javascript
// services/tokenManager.js
class TokenManager {
  constructor(config) {
    this.expiryBuffer = config.tokens.expiryBuffer;
    this.refreshInterval = null;
  }

  shouldRefresh(tokenExpiry) {
    const now = Math.floor(Date.now() / 1000);
    return (tokenExpiry - now) <= this.expiryBuffer;
  }

  scheduleRefresh(tokenExpiry, refreshCallback) {
    const refreshTime = (tokenExpiry - this.expiryBuffer) * 1000 - Date.now();
    
    if (this.refreshInterval) {
      clearTimeout(this.refreshInterval);
    }

    this.refreshInterval = setTimeout(async () => {
      try {
        await refreshCallback();
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    }, Math.max(refreshTime, 0));
  }
}
```

### Token Storage Security

| Storage Method | Use Case | Security Level | Notes |
|----------------|----------|----------------|-------|
| HTTP-only Cookie | Session token | High | Preferred for refresh tokens |
| Memory | Access token | High | Lost on page refresh |
| Session Storage | Temporary state | Medium | Cleared on tab close |
| Local Storage | Not recommended | Low | Vulnerable to XSS |

---

## Environment-Specific Configurations

### Development Environment

```env
# .env.development

# Auth0 Configuration
AUTH0_DOMAIN=natterbox-dev.eu.auth0.com
AUTH0_CLIENT_ID=dev_aB3cD4eF5gH6iJ7kL8mN9oP0
AUTH0_CLIENT_SECRET=dev_xYz123AbC456DeF789GhI012JkL345MnO678PqR901StU234VwX567
AUTH0_AUDIENCE=https://api.natterbox.com/wallboards/dev
AUTH0_ISSUER_BASE_URL=https://natterbox-dev.eu.auth0.com

# URL Configuration
APP_BASE_URL=http://localhost:3000
AUTH0_CALLBACK_URL=http://localhost:3000/callback
AUTH0_LOGOUT_URL=http://localhost:3000
API_BASE_URL=http://localhost:8080/api/v1
WEBSOCKET_URL=ws://localhost:8080/ws

# Token Management
TOKEN_EXPIRY_BUFFER=60
ACCESS_TOKEN_LIFETIME=3600
REFRESH_TOKEN_LIFETIME=86400
SESSION_COOKIE_SECRET=dev-secret-key-for-local-development-only!!
SESSION_COOKIE_NAME=natterbox_dev_session
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_ABSOLUTE_DURATION=43200
SESSION_ROLLING_DURATION=1800

# Security (Relaxed for Development)
ENABLE_PKCE=true
ENABLE_STATE_PARAM=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
CSP_FRAME_ANCESTORS='self'
RATE_LIMIT_AUTH_REQUESTS=100
ENABLE_MFA=false

# Logging (Verbose for Development)
AUTH_LOG_LEVEL=debug
LOG_TOKEN_EVENTS=true
LOG_AUTH_FAILURES=true
ENABLE_AUTH_DEBUG=true
```

### Staging Environment

```env
# .env.staging

# Auth0 Configuration
AUTH0_DOMAIN=natterbox-staging.eu.auth0.com
AUTH0_CLIENT_ID=stg_aB3cD4eF5gH6iJ7kL8mN9oP0
AUTH0_CLIENT_SECRET=stg_xYz123AbC456DeF789GhI012JkL345MnO678PqR901StU234VwX567
AUTH0_AUDIENCE=https://api.natterbox.com/wallboards/staging
AUTH0_ISSUER_BASE_URL=https://natterbox-staging.eu.auth0.com

# URL Configuration
APP_BASE_URL=https://wallboards-staging.natterbox.com
AUTH0_CALLBACK_URL=https://wallboards-staging.natterbox.com/callback
AUTH0_LOGOUT_URL=https://wallboards-staging.natterbox.com
API_BASE_URL=https://api-staging.natterbox.com/wallboards/v1
WEBSOCKET_URL=wss://ws-staging.natterbox.com/wallboards

# Token Management
TOKEN_EXPIRY_BUFFER=300
ACCESS_TOKEN_LIFETIME=7200
REFRESH_TOKEN_LIFETIME=604800
SESSION_COOKIE_SECRET=${STAGING_SESSION_SECRET}
SESSION_COOKIE_NAME=natterbox_stg_session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
SESSION_ABSOLUTE_DURATION=86400
SESSION_ROLLING_DURATION=3600

# Security
ENABLE_PKCE=true
ENABLE_STATE_PARAM=true
ALLOWED_ORIGINS=https://wallboards-staging.natterbox.com
CSP_FRAME_ANCESTORS='none'
RATE_LIMIT_AUTH_REQUESTS=20
ENABLE_MFA=false

# Logging
AUTH_LOG_LEVEL=info
LOG_TOKEN_EVENTS=true
LOG_AUTH_FAILURES=true
ENABLE_AUTH_DEBUG=false
```

### Production Environment

```env
# .env.production

# Auth0 Configuration
AUTH0_DOMAIN=natterbox.eu.auth0.com
AUTH0_CLIENT_ID=${PROD_AUTH0_CLIENT_ID}
AUTH0_CLIENT_SECRET=${PROD_AUTH0_CLIENT_SECRET}
AUTH0_AUDIENCE=https://api.natterbox.com/wallboards
AUTH0_ISSUER_BASE_URL=https://natterbox.eu.auth0.com

# URL Configuration
APP_BASE_URL=https://wallboards.natterbox.com
AUTH0_CALLBACK_URL=https://wallboards.natterbox.com/callback
AUTH0_LOGOUT_URL=https://wallboards.natterbox.com
API_BASE_URL=https://api.natterbox.com/wallboards/v1
WEBSOCKET_URL=wss://ws.natterbox.com/wallboards

# Token Management
TOKEN_EXPIRY_BUFFER=300
ACCESS_TOKEN_LIFETIME=7200
REFRESH_TOKEN_LIFETIME=2592000
SESSION_COOKIE_SECRET=${PROD_SESSION_SECRET}
SESSION_COOKIE_NAME=__Host-natterbox_session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
SESSION_ABSOLUTE_DURATION=86400
SESSION_ROLLING_DURATION=3600

# Security (Strict for Production)
ENABLE_PKCE=true
ENABLE_STATE_PARAM=true
ALLOWED_ORIGINS=https://wallboards.natterbox.com
CSP_FRAME_ANCESTORS='none'
RATE_LIMIT_AUTH_REQUESTS=10
ENABLE_MFA=true
MFA_REMEMBER_DEVICE_DAYS=7

# Logging (Minimal for Production)
AUTH_LOG_LEVEL=warn
LOG_TOKEN_EVENTS=false
LOG_AUTH_FAILURES=true
ENABLE_AUTH_DEBUG=false
```

---

## Security Considerations

### Sensitive Values Protection

| Variable | Sensitivity | Storage Recommendation |
|----------|-------------|----------------------|
| `AUTH0_CLIENT_SECRET` | **Critical** | Secrets manager (Vault, AWS Secrets Manager) |
| `SESSION_COOKIE_SECRET` | **Critical** | Secrets manager with rotation |
| `AUTH0_CLIENT_ID` | Medium | Environment variable |
| `AUTH0_DOMAIN` | Low | Environment variable or config file |

### Secret Generation

Generate secure secrets using cryptographically secure methods:

```bash
# Generate 64-character session secret
openssl rand -base64 48

# Generate using Node.js
node -e "console.log(require('crypto').randomBytes(48).toString('base64'))"
```

### Security Checklist

- [ ] All secrets stored in secure secrets manager
- [ ] `SESSION_COOKIE_SECURE=true` in production
- [ ] `SESSION_COOKIE_HTTPONLY=true` always enabled
- [ ] `SESSION_COOKIE_SAMESITE=Strict` in production
- [ ] PKCE enabled for all environments
- [ ] Rate limiting configured
- [ ] MFA enabled for production
- [ ] CORS origins explicitly defined
- [ ] CSP headers configured
- [ ] Token lifetimes minimized
- [ ] Refresh token rotation enabled in Auth0
- [ ] Debug logging disabled in production

### Cookie Security Configuration

For production, use the `__Host-` cookie prefix:

```javascript
// Ensures cookie is:
// - Secure (HTTPS only)
// - From the host (no domain attribute)
// - Path is '/'
SESSION_COOKIE_NAME=__Host-natterbox_session
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Invalid State" Error During Login

**Symptoms**: User redirected to error page after Auth0 login with "invalid state" message.

**Causes and Solutions**:

| Cause | Solution |
|-------|----------|
| Session cookie not persisting | Verify `SESSION_COOKIE_SECURE` matches protocol |
| Multiple browser tabs | Implement single-tab login flow |
| Clock skew | Ensure server time is synchronized |
| Cookie blocked | Check third-party cookie settings |

```bash
# Verify server time
date
timedatectl status
```

#### Issue: Token Refresh Failing Silently

**Symptoms**: Users logged out unexpectedly after token expiry.

**Diagnosis**:

```javascript
// Enable token event logging temporarily
LOG_TOKEN_EVENTS=true
AUTH_LOG_LEVEL=debug
```

**Common causes**:

1. Refresh token expired or revoked
2. Network issues during refresh
3. `TOKEN_EXPIRY_BUFFER` too small

#### Issue: CORS Errors on Authentication Requests

**Symptoms**: Browser console shows CORS policy errors.

**Solutions**:

```env
# Ensure all application origins are listed
ALLOWED_ORIGINS=https://wallboards.natterbox.com,https://www.wallboards.natterbox.com
```

Verify Auth0 application settings include all callback URLs.

#### Issue: "Unauthorized" on WebSocket Connection

**Symptoms**: Real-time data not loading, WebSocket connection rejected.

**Solutions**:

1. Verify `WEBSOCKET_URL` is correct
2. Ensure access token is included in connection handshake
3. Check token audience matches WebSocket server expectations

```javascript
// Correct WebSocket connection with auth
const ws = new WebSocket(`${WEBSOCKET_URL}?token=${accessToken}`);
```

#### Issue: Session Lost After Deployment

**Symptoms**: All users logged out after application deployment.

**Cause**: `SESSION_COOKIE_SECRET` changed between deployments.

**Solution**: 
- Use persistent secret from secrets manager
- Implement secret rotation with grace period

### Diagnostic Commands

```bash
# Test Auth0 connectivity
curl -I https://${AUTH0_DOMAIN}/.well-known/openid-configuration

# Verify JWKS endpoint
curl https://${AUTH0_DOMAIN}/.well-known/jwks.json | jq .

# Test API connectivity
curl -H "Authorization: Bearer ${ACCESS_TOKEN}" ${API_BASE_URL}/health

# Decode JWT token (for debugging)
echo "${ACCESS_TOKEN}" | cut -d'.' -f2 | base64 -d | jq .
```

### Logging Analysis

Enable comprehensive logging for troubleshooting:

```env
AUTH_LOG_LEVEL=debug
LOG_TOKEN_EVENTS=true
LOG_AUTH_FAILURES=true
ENABLE_AUTH_DEBUG=true
```

Log patterns to search for:

| Pattern | Meaning |
|---------|---------|
| `auth:token:refresh:success` | Token refreshed successfully |
| `auth:token:refresh:failed` | Token refresh failed |
| `auth:login:success` | User authenticated |
| `auth:login:failed` | Authentication failure |
| `auth:session:expired` | Session timed out |
| `auth:callback:error` | OAuth callback error |

---

## Example Complete .env File

```env
# =============================================================================
# NATTERBOX WALLBOARDS - AUTHENTICATION CONFIGURATION
# =============================================================================
# Environment: Production
# Last Updated: 2024-01-15
# =============================================================================

# -----------------------------------------------------------------------------
# AUTH0 CONFIGURATION
# -----------------------------------------------------------------------------
AUTH0_DOMAIN=natterbox.eu.auth0.com
AUTH0_CLIENT_ID=${PROD_AUTH0_CLIENT_ID}
AUTH0_CLIENT_SECRET=${PROD_AUTH0_CLIENT_SECRET}
AUTH0_AUDIENCE=https://api.natterbox.com/wallboards
AUTH0_ISSUER_BASE_URL=https://natterbox.eu.auth0.com
AUTH0_ALGORITHM=RS256

# -----------------------------------------------------------------------------
# URL CONFIGURATION
# -----------------------------------------------------------------------------
APP_BASE_URL=https://wallboards.natterbox.com
AUTH0_CALLBACK_URL=https://wallboards.natterbox.com/callback
AUTH0_LOGOUT_URL=https://wallboards.natterbox.com
API_BASE_URL=https://api.natterbox.com/wallboards/v1
WEBSOCKET_URL=wss://ws.natterbox.com/wallboards

# -----------------------------------------------------------------------------
# TOKEN MANAGEMENT
# -----------------------------------------------------------------------------
TOKEN_EXPIRY_BUFFER=300
ACCESS_TOKEN_LIFETIME=7200
REFRESH_TOKEN_LIFETIME=2592000

# -----------------------------------------------------------------------------
# SESSION CONFIGURATION
# -----------------------------------------------------------------------------
SESSION_COOKIE_SECRET=${PROD_SESSION_SECRET}
SESSION_COOKIE_NAME=__Host-natterbox_session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
SESSION_ABSOLUTE_DURATION=86400
SESSION_ROLLING_DURATION=3600

# -----------------------------------------------------------------------------
# SECURITY CONFIGURATION
# -----------------------------------------------------------------------------
ENABLE_PKCE=true
ENABLE_STATE_PARAM=true
ALLOWED_ORIGINS=https://wallboards.natterbox.com
CSP_FRAME_ANCESTORS='none'
RATE_LIMIT_AUTH_REQUESTS=10
ENABLE_MFA=true
MFA_REMEMBER_DEVICE_DAYS=7

# -----------------------------------------------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------------------------------------------
AUTH_LOG_LEVEL=warn
LOG_TOKEN_EVENTS=false
LOG_AUTH_FAILURES=true
ENABLE_AUTH_DEBUG=false
```

---

## Additional Resources

- [Auth0 Documentation](https://auth0.com/docs)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)