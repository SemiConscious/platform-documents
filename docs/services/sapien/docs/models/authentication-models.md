# Authentication Models

This document provides detailed documentation for authentication and authorization related models in the Sapien service. These models handle OAuth tokens, API sessions, rate limiting, and security voting.

## Overview

The authentication system in Sapien is built around OAuth 2.0 with additional support for Core API sessions. The architecture supports:

- **OAuth 2.0 Authentication**: Access tokens, refresh tokens, authorization codes, and clients
- **Session Management**: Core API sessions for tracking authenticated user activity
- **Rate Limiting**: Organisation-level API rate limiting
- **Security Voting**: Role-based access control via abstract voters

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Client      │       │      User       │       │  Organisation   │
│                 │       │                 │       │                 │
│  - id           │       │  - id           │       │  - id           │
│  - name         │       │  - isSingleSign │       │  - APIRequest   │
│  - description  │       │  - isMfa        │       │    Limit        │
│  - company      │       │                 │       │  - APIReset     │
└────────┬────────┘       └────────┬────────┘       │    Seconds      │
         │                         │                └────────┬────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   AccessToken   │◄──────│ CoreApiSession  │       │ Organisation    │
│                 │       │                 │       │ ApiRateLimit    │
│  - token        │       │  - token        │       │                 │
│  - client_id    │       │  - user_id      │       │  - org_id       │
│  - user_id      │       │  - ip_address   │       │  - next_reset   │
│  - expires_at   │       │  - ui_version   │       │  - requests     │
└─────────────────┘       │  - last_check   │       └─────────────────┘
         ▲                └─────────────────┘
         │
┌────────┴────────┐       ┌─────────────────┐
│  RefreshToken   │       │    AuthCode     │
│                 │       │                 │
│  - client_id    │       │  - client_id    │
│  - user_id      │       │  - user_id      │
└─────────────────┘       └─────────────────┘
```

---

## OAuth Models

### AccessToken

OAuth access token entity extending FOS OAuthServerBundle BaseAccessToken. This is the primary authentication credential for API requests.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | Yes | The access token string used for authentication |
| `client_id` | int | Yes | Foreign key to the OAuth client that issued the token |
| `user_id` | int | Yes | Foreign key to the user who owns the token |
| `client` | object | Yes | OAuth client entity reference |
| `user` | object | Yes | User entity reference |
| `core_api_session` | CoreApiSession\|null | No | Associated Core API session for session tracking |

#### Validation Rules

- Token must be unique across all access tokens
- Client must be a valid, registered OAuth client
- User must exist and be active
- Token expiration is managed by the OAuth server bundle

#### Relationships

- **Belongs to** `Client` - The OAuth client that issued the token
- **Belongs to** `User` - The user who authorized the token
- **Has one** `CoreApiSession` - Optional session tracking record

#### Example JSON

```json
{
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "client_id": 1,
  "user_id": 12345,
  "client": {
    "id": 1,
    "name": "Sapien Web Application",
    "company": "Redmatter"
  },
  "user": {
    "id": 12345,
    "username": "john.doe@example.com"
  },
  "core_api_session": {
    "id": 98765,
    "ip_address": "192.168.1.100"
  }
}
```

---

### RefreshToken

OAuth refresh token entity extending FOS OAuthServerBundle BaseRefreshToken. Used to obtain new access tokens without requiring user re-authentication.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | int | Yes | Foreign key to the OAuth client |
| `user_id` | int | Yes | Foreign key to the user |

#### Validation Rules

- Must be associated with a valid client
- Must be associated with a valid user
- Token string must be unique
- Expiration managed by OAuth server configuration

#### Relationships

- **Belongs to** `Client` - The OAuth client that issued the token
- **Belongs to** `User` - The user who authorized the token

#### Example JSON

```json
{
  "id": 5678,
  "token": "refresh_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",
  "client_id": 1,
  "user_id": 12345,
  "expires_at": 1735689600
}
```

---

### AuthCode

OAuth authorization code entity extending FOS OAuthServerBundle BaseAuthCode. Used in the authorization code grant flow.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_id` | int | Yes | Foreign key to the OAuth client requesting authorization |
| `user_id` | int | Yes | Foreign key to the user granting authorization |

#### Validation Rules

- Code must be unique
- Code expires after a short period (typically 30 seconds to 10 minutes)
- Can only be used once to exchange for an access token

#### Relationships

- **Belongs to** `Client` - The OAuth client requesting authorization
- **Belongs to** `User` - The user granting authorization

#### Example JSON

```json
{
  "code": "auth_x1y2z3a4b5c6d7e8f9g0",
  "client_id": 2,
  "user_id": 12345,
  "redirect_uri": "https://app.example.com/callback",
  "expires_at": 1704067500,
  "scope": "read write"
}
```

---

### Client

OAuth client entity extending FOS OAuthServerBundle BaseClient. Represents an application that can request authentication on behalf of users.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string\|null | No | Human-readable client application name |
| `description` | string | Yes | Detailed description of the client application |
| `company` | string | Yes | Company or organization that owns the client |

#### Validation Rules

- Client ID and secret are auto-generated
- Redirect URIs must be valid URLs
- Grant types must be explicitly configured

#### Relationships

- **Has many** `AccessToken` - Tokens issued to this client
- **Has many** `RefreshToken` - Refresh tokens issued to this client
- **Has many** `AuthCode` - Authorization codes issued to this client

#### Example JSON

```json
{
  "id": 1,
  "name": "Sapien Web Application",
  "description": "Primary web interface for the Sapien platform",
  "company": "Redmatter",
  "client_id": "1_abc123def456",
  "client_secret": "secret_xyz789",
  "redirect_uris": [
    "https://app.sapien.example.com/oauth/callback"
  ],
  "allowed_grant_types": [
    "authorization_code",
    "refresh_token",
    "password"
  ]
}
```

---

## Session Models

### CoreApiSession

Core API session tracking entity for authenticated users. Provides detailed session state management beyond OAuth tokens.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | int | Yes | Primary key identifier |
| `token` | string | Yes | SHA1 hash of the authentication token (40 characters) |
| `user` | User | Yes | User entity who owns the session |
| `ip_address` | string | Yes | Client IP address that initiated the session |
| `url` | string | No | Request URL associated with the session |
| `ui_version` | string | No | Version string of the UI client |
| `timezone_offset` | int | No | Client's timezone offset from UTC in minutes |
| `sudoed_to_user` | User | No | User being impersonated via sudo functionality |
| `last_check` | DateTime | Yes | Timestamp of last session validation check |
| `access_token` | AccessToken | No | Associated OAuth access token (for non-JWT auth) |

#### Validation Rules

- Token must be exactly 40 characters (SHA1 hash)
- IP address must be a valid IPv4 or IPv6 address
- Last check timestamp is automatically updated on each request
- Session may be invalidated if IP address changes (depending on configuration)

#### Relationships

- **Belongs to** `User` - The authenticated user
- **Has one** `AccessToken` - Associated OAuth access token
- **May reference** `User` (sudoed_to_user) - For impersonation scenarios

#### Example JSON

```json
{
  "id": 98765,
  "token": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
  "user": {
    "id": 12345,
    "username": "john.doe@example.com"
  },
  "ip_address": "192.168.1.100",
  "url": "/api/v1/recordings",
  "ui_version": "2.5.3",
  "timezone_offset": -300,
  "sudoed_to_user": null,
  "last_check": "2024-01-15T14:30:00Z",
  "access_token": {
    "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
  }
}
```

---

## Rate Limiting Models

### OrganisationApiRateLimit

Rate limiting configuration and state for organisation API access. Tracks request counts and reset windows per organisation.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `organisation_id` | int | Yes | Foreign key to organisation (primary key) |
| `request_limit` | int | No | Maximum number of requests allowed per window; null or 0 for unlimited |
| `reset_seconds` | int | Yes | Duration of the rate limit window in seconds |
| `next_reset` | DateTime\|null | No | DateTime when the current rate limit window resets |
| `requests` | int | Yes | Current number of requests made in the window |

#### Validation Rules

- Organisation ID must reference a valid organisation
- Request limit of 0 or null indicates unlimited requests
- Reset seconds must be a positive integer
- Requests counter resets when `next_reset` time is reached

#### Relationships

- **Belongs to** `Organisation` - The organisation being rate limited

#### Database Table Structure

The `Org.OrgAPIRateLimit` table stores the runtime state:

| Column | Type | Description |
|--------|------|-------------|
| `OrgID` | int | Organisation ID (primary key) |
| `NextReset` | datetime | Next rate limit reset time |
| `Requests` | int | Current request count |

The `Org.Orgs` table stores the configuration:

| Column | Type | Description |
|--------|------|-------------|
| `OrgID` | int | Organisation ID (primary key) |
| `APIRequestLimit` | int | API request limit |
| `APIResetSeconds` | int | Rate limit reset interval |

#### Example JSON

```json
{
  "organisation_id": 100,
  "request_limit": 1000,
  "reset_seconds": 3600,
  "next_reset": "2024-01-15T15:00:00Z",
  "requests": 423
}
```

#### Common Use Cases

1. **Checking Rate Limit Status**
```json
{
  "organisation_id": 100,
  "request_limit": 1000,
  "requests": 423,
  "remaining": 577,
  "reset_seconds": 3600,
  "seconds_until_reset": 1847
}
```

2. **Unlimited API Access**
```json
{
  "organisation_id": 200,
  "request_limit": 0,
  "reset_seconds": 3600,
  "next_reset": null,
  "requests": 0
}
```

---

## Security Interfaces and Abstract Classes

### RedmatterUserInterface

User interface defining SSO and MFA capability properties.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isSingleSignOn` | bool | Yes | Whether the user authenticates via single sign-on |
| `isMfa` | bool | Yes | Whether the user has multi-factor authentication enabled |

#### Example JSON

```json
{
  "id": 12345,
  "username": "john.doe@example.com",
  "isSingleSignOn": false,
  "isMfa": true
}
```

---

### AbstractVoter

Abstract base class for Symfony security voters implementing role-based access control.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allowed_roles` | array | Yes | List of roles allowed by this voter |
| `supported_attributes` | array | Yes | List of security attributes this voter supports |
| `supported_classes` | array | Yes | List of entity classes this voter can make decisions about |
| `logger` | LoggerInterface | No | PSR logger instance for debugging |

#### Common Use Cases

Extending the AbstractVoter for custom authorization:

```php
class RecordingAccessVoter extends AbstractVoter
{
    protected $allowed_roles = ['ROLE_ADMIN', 'ROLE_SUPERVISOR'];
    protected $supported_attributes = ['VIEW', 'DOWNLOAD', 'DELETE'];
    protected $supported_classes = [Recording::class];
}
```

---

## Repository Interfaces

### AccessTokenRepositoryInterface

Interface defining operations for access token management.

#### Methods and Parameters

| Method | Parameters | Description |
|--------|------------|-------------|
| `findByToken` | `token: string` | Find access token by token string |
| `findByUserIds` | `user_ids: array` | Find tokens for multiple users |
| `findByClientAndUser` | `client_id: int, user_id: int` | Find token for specific client/user pair |

---

### EventLogRepositoryInterface

Interface defining event logging operations for authentication audit trail.

#### Authentication Event Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `organisation_id` | int | Organisation identifier for the event |
| `user_id` | int | User identifier who triggered the event |
| `two_factor_authentication_used` | string | Whether 2FA was used for login |
| `successful` | bool | Whether login was successful |
| `action` | string | Event action type (e.g., 'Auth:Login', 'Auth:Logout') |
| `message` | string | Descriptive message for the event |

#### Example Login Event

```json
{
  "organisation_id": 100,
  "user_id": 12345,
  "action": "Auth:Login",
  "message": "User logged in successfully",
  "two_factor_authentication_used": "true",
  "successful": true,
  "context": "Security",
  "level": "Message",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

---

## Authentication Flow Patterns

### OAuth 2.0 Authorization Code Flow

1. **Authorization Request**: Client redirects user to authorization endpoint
2. **User Authentication**: User authenticates and grants permissions
3. **Authorization Code**: Server issues `AuthCode` and redirects to client
4. **Token Exchange**: Client exchanges `AuthCode` for `AccessToken` and `RefreshToken`
5. **API Access**: Client uses `AccessToken` for API requests
6. **Token Refresh**: Client uses `RefreshToken` to obtain new `AccessToken`

### Core API Session Flow

1. **Authentication**: User authenticates via OAuth or direct login
2. **Session Creation**: `CoreApiSession` created with user details
3. **Request Processing**: Each request updates `last_check` timestamp
4. **Rate Limit Check**: `OrganisationApiRateLimit` validated per request
5. **Event Logging**: Authentication events logged via `EventLogRepositoryInterface`