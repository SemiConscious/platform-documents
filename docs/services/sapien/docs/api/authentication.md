# Authentication

This document provides a comprehensive guide to authentication in the Sapien API, covering access tokens, session management, and security best practices.

## Overview

The Sapien API currently operates without authentication requirements in its default configuration. This guide documents the authentication patterns and security considerations for production deployments.

> **Note:** The current implementation is designed for development and testing environments. Production deployments should implement appropriate authentication mechanisms as described below.

## Current Authentication Status

Based on the API implementation, the following authentication characteristics apply:

| Aspect | Status | Notes |
|--------|--------|-------|
| Authentication Required | No | All endpoints are publicly accessible |
| Session Management | None | Stateless REST architecture |
| Rate Limiting | Not Implemented | Consider adding for production |
| HTTPS Required | Recommended | Not enforced at API level |

## Recommended Authentication Implementation

For production deployments, we recommend implementing OAuth2 or API key-based authentication.

### API Key Authentication

The simplest approach for service-to-service communication:

```bash
# Example authenticated request with API key
curl -X GET "http://localhost:8080/person/1" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### OAuth2 Flow (Recommended)

For user-facing applications, implement the OAuth2 authorization code flow:

#### 1. Authorization Request

```bash
# Redirect user to authorization endpoint
GET /oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://your-app.com/callback&
  scope=read write&
  state=RANDOM_STATE_STRING
```

#### 2. Token Exchange

```bash
# Exchange authorization code for tokens
curl -X POST "http://localhost:8080/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://your-app.com/callback"
```

**Example Token Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "scope": "read write"
}
```

#### 3. Using Access Tokens

Include the access token in all API requests:

```bash
# Authenticated request example
curl -X GET "http://localhost:8080/person/1" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### 4. Refreshing Tokens

```bash
# Refresh an expired access token
curl -X POST "http://localhost:8080/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..." \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

## Session Management

The Sapien API follows RESTful principles with stateless request handling:

- **No server-side sessions**: Each request must be self-contained
- **Token-based identity**: Use bearer tokens to identify requests
- **Stateless architecture**: No session cookies or server-side session storage

### Token Lifecycle

| Token Type | Typical Lifetime | Storage Recommendation |
|------------|------------------|----------------------|
| Access Token | 1 hour | Memory only |
| Refresh Token | 30 days | Secure, encrypted storage |
| API Key | No expiration | Environment variables |

## Authentication Errors

When authentication is implemented, expect these error responses:

### 401 Unauthorized

Returned when no valid credentials are provided:

```json
{
  "error": "unauthorized",
  "error_description": "Missing or invalid authentication token",
  "status_code": 401
}
```

### 403 Forbidden

Returned when credentials are valid but insufficient permissions:

```json
{
  "error": "forbidden",
  "error_description": "Insufficient permissions for this resource",
  "status_code": 403
}
```

### Error Code Reference

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 401 | `unauthorized` | No valid credentials provided |
| 401 | `token_expired` | Access token has expired |
| 401 | `invalid_token` | Token format is invalid |
| 403 | `forbidden` | Valid credentials but insufficient scope |
| 403 | `scope_required` | Specific scope needed for endpoint |

## Security Best Practices

### Token Storage

- **Never** store tokens in localStorage for sensitive applications
- Use httpOnly cookies or secure session storage
- Implement token rotation for long-lived sessions

### Request Security

```bash
# Always use HTTPS in production
curl -X GET "https://api.example.com/person/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Development vs Production

| Consideration | Development | Production |
|---------------|-------------|------------|
| HTTPS | Optional | Required |
| Token Expiration | Longer (testing) | Shorter (1 hour) |
| Rate Limiting | Disabled | Enabled |
| Logging | Verbose | Security-focused |

## Testing Authentication

Use the constant endpoint to verify your authentication setup:

### `GET /constant`

Returns a predictable response useful for testing authentication configurations.

**Request:**

```bash
curl -X GET "http://localhost:8080/constant" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**

```json
{
  "message": "constant response"
}
```

This endpoint is ideal for:
- Verifying token validity
- Testing authentication middleware
- Acceptance testing authentication flows

## Related Documentation

- [Person Endpoints](./person-endpoints.md) - CRUD operations for person entities
- [Pet Endpoints](./pet-endpoints.md) - CRUD operations for pet entities
- [Toy Endpoints](./toy-endpoints.md) - CRUD operations for toy entities
- [Utility Endpoints](./utility-endpoints.md) - Testing and debugging endpoints