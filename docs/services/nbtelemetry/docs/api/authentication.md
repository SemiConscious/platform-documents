# Authentication Endpoints

This document covers the authentication and token management endpoints for the nbtelemetry API. These endpoints handle user authentication using OAuth2 password grant flow and session management.

## Overview

The nbtelemetry API uses token-based authentication. Clients must first obtain an access token via the authentication endpoint, then include this token in subsequent API requests. Tokens can be revoked when ending a session.

## Base URL

All authentication endpoints are relative to the API base URL:

```
https://api.natterbox.com
```

---

## Endpoints

### Obtain Access Token

Authenticate a user and obtain an access token using OAuth2 password grant.

```
POST /auth/token
```

#### Description

This endpoint authenticates a user with their credentials and returns an access token. The token must be included in the `Authorization` header for all subsequent API requests.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `grant_type` | body | string | Yes | Must be `password` for password grant flow |
| `username` | body | string | Yes | User's email address or username |
| `password` | body | string | Yes | User's password |
| `client_id` | body | string | No | OAuth2 client identifier |
| `client_secret` | body | string | No | OAuth2 client secret (if required) |

#### Request Example

```bash
curl -X POST "https://api.natterbox.com/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "username=user@example.com" \
  -d "password=your_password"
```

#### Response Example

**Success (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "scope": "read write"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | The token to use for authenticated requests |
| `token_type` | string | Token type, typically `Bearer` |
| `expires_in` | integer | Token validity duration in seconds |
| `refresh_token` | string | Token used to obtain a new access token |
| `scope` | string | Permissions granted to the token |

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `invalid_request` | Missing or invalid parameters |
| 401 | `invalid_grant` | Invalid username or password |
| 401 | `invalid_client` | Invalid client credentials |
| 429 | `too_many_requests` | Rate limit exceeded |
| 500 | `server_error` | Internal server error |

---

### Revoke Access Token

End the current authentication session and revoke the access token.

```
DELETE /auth/token
```

#### Description

This endpoint invalidates the current access token, effectively logging out the user. After calling this endpoint, the token can no longer be used for authenticated requests.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `Authorization` | header | string | Yes | Bearer token to revoke |

#### Request Example

```bash
curl -X DELETE "https://api.natterbox.com/auth/token" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response Example

**Success (204 No Content)**

No response body is returned on successful token revocation.

**Success (200 OK)** - Alternative response

```json
{
  "message": "Token successfully revoked",
  "revoked_at": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `invalid_request` | Malformed request |
| 401 | `invalid_token` | Token is already invalid or expired |
| 500 | `server_error` | Internal server error |

---

## Using Authentication Tokens

Once you have obtained an access token, include it in the `Authorization` header of all API requests:

```bash
curl -X GET "https://api.natterbox.com/v1/user/me" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Token Lifecycle

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  POST /auth/    │     │   Use Token in  │     │ DELETE /auth/   │
│     token       │────▶│   API Requests  │────▶│     token       │
│  (Authenticate) │     │                 │     │    (Logout)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Best Practices

1. **Secure Storage**: Store tokens securely and never expose them in client-side code or logs
2. **Token Expiration**: Monitor `expires_in` and refresh tokens before expiration
3. **Logout**: Always revoke tokens when users log out to prevent unauthorized access
4. **HTTPS Only**: All authentication requests must be made over HTTPS

---

## Related Documentation

- [Users and Organizations](users-and-organizations.md) - User management endpoints including `GET /v1/user/me`
- [API Overview](README.md) - General API information and conventions