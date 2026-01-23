# Authentication Models

This document covers data models related to authentication, user sessions, permissions, and login state management in the Natterbox Wallboards application.

## Overview

The authentication system in Natterbox Wallboards uses Auth0 for OAuth2-based authentication. These models handle:

- Auth0 configuration and URLs
- User information and permissions
- Login state management
- Listen-in permissions for call monitoring
- Session and access control

## Entity Relationship Diagram

```
┌─────────────────────┐
│     AuthConfig      │
│  (OAuth Settings)   │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐         ┌─────────────────────┐
│     Auth0Urls       │────────▶│     LoginState      │
│  (Auth0 Settings)   │         │  (Redux Slice)      │
└─────────────────────┘         └─────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
          ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
          │    UserInfo     │  │    LoginData    │  │ListenInPermissions  │
          │ (User Details)  │  │  (API Utility)  │  │  (Call Monitoring)  │
          └─────────────────┘  └─────────────────┘  └─────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │   UserAvatar    │
          │ (Profile Image) │
          └─────────────────┘
```

---

## AuthConfig

Auth0 authentication configuration object used to initialize the Auth0 client.

### Purpose

Configures the OAuth2 authentication flow with Auth0, including redirect URIs, scopes, and token caching strategy. This model is used during application initialization to set up the authentication provider.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `redirectUri` | `string` | Yes | OAuth redirect URI, dynamically set based on environment (localhost vs production) |
| `scope` | `string` | Yes | OAuth scopes requested (e.g., "openid profile email") |
| `responseType` | `string` | Yes | OAuth response type (typically "token" or "code") |
| `cacheLocation` | `string` | Yes | Where to cache auth tokens ("localstorage" or "memory") |
| `envHost` | `string` | Yes | Environment host URL for production deployments |
| `localHost` | `string` | Yes | Local development host URL |

### Validation Rules

- `redirectUri` must be a valid URL matching configured Auth0 callback URLs
- `scope` must include at minimum "openid" for OIDC compliance
- `cacheLocation` must be either "localstorage" or "memory"
- `responseType` must be a valid OAuth2 response type

### Example

```json
{
  "redirectUri": "https://wallboards.natterbox.com/callback",
  "scope": "openid profile email read:wallboards write:wallboards",
  "responseType": "token",
  "cacheLocation": "localstorage",
  "envHost": "https://wallboards.natterbox.com",
  "localHost": "http://localhost:3000"
}
```

### Relationships

- Used to configure the Auth0Provider component
- Determines the `Auth0Urls` endpoint configuration

---

## Auth0Urls

Auth0 URL configuration stored in Redux for runtime access to authentication endpoints.

### Purpose

Stores the Auth0 tenant-specific configuration retrieved from the backend, enabling the application to authenticate against the correct Auth0 domain and audience.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `string` | Yes | Auth0 domain URL (e.g., "natterbox.eu.auth0.com") |
| `clientId` | `string` | Yes | Auth0 application client ID |
| `audience` | `string` | Yes | Auth0 API audience identifier |
| `connection_name` | `string` | No | Auth0 connection name for specific identity providers |

### Validation Rules

- `url` must be a valid Auth0 domain URL
- `clientId` must be a valid Auth0 client identifier (32 characters)
- `audience` must match a registered API in Auth0

### Example

```json
{
  "url": "natterbox.eu.auth0.com",
  "clientId": "abc123def456ghi789jkl012mno345pq",
  "audience": "https://api.natterbox.com",
  "connection_name": "natterbox-saml"
}
```

### Relationships

- Contained within `LoginState.auth0Urls`
- Used by `AuthConfig` for authentication initialization
- Retrieved from backend API during application bootstrap

---

## UserInfo

User information object containing the authenticated user's details and permissions.

### Purpose

Stores the current user's identity information, organization membership, and permission scopes. This model is central to authorization decisions throughout the application.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | User unique identifier |
| `firstName` | `string` | No | User's first name |
| `lastName` | `string` | No | User's last name |
| `organisationId` | `number` | Yes | User's organization ID |
| `scopes` | `array` | Yes | Array of user permission scopes |
| `isAdmin` | `boolean` | Yes | Whether user has admin permissions |
| `isTeamLeader` | `boolean` | Yes | Whether user has team leader permissions |

### Validation Rules

- `id` must be a non-empty string
- `organisationId` must be a positive integer
- `scopes` must be an array (can be empty)
- `isAdmin` and `isTeamLeader` default to `false` if not provided

### Example

```json
{
  "id": "user-12345-abcde",
  "firstName": "John",
  "lastName": "Smith",
  "organisationId": 5001,
  "scopes": [
    "read:wallboards",
    "write:wallboards",
    "read:agents",
    "manage:calls"
  ],
  "isAdmin": false,
  "isTeamLeader": true
}
```

### Relationships

- Contained within `LoginState.userInfo`
- Determines available actions in UI components
- Referenced by `ListenInPermissions` for call monitoring authorization

---

## LoginState

Redux login state slice managing all authentication-related state.

### Purpose

Central Redux state slice that holds all authentication information, user data, and error states. This is the primary source of truth for authentication status throughout the application.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userInfo` | `UserInfo` | No | Current user information (null when not authenticated) |
| `isAccessEnabled` | `boolean \| null` | No | Whether user access is enabled; null indicates unknown state |
| `auth0Urls` | `Auth0Urls` | No | Auth0 configuration URLs |
| `gatekeeperErrorMessage` | `string` | No | Error message from gatekeeper authentication service |
| `usersAvatars` | `object` | No | Map of user IDs to avatar objects |
| `listenInPermissions` | `ListenInPermissions` | No | Permissions for call monitoring functionality |

### Validation Rules

- `isAccessEnabled` transitions: `null` → `true`/`false` after authentication check
- `gatekeeperErrorMessage` should only be set when `isAccessEnabled` is `false`
- `userInfo` must be valid `UserInfo` object when user is authenticated

### Example

```json
{
  "userInfo": {
    "id": "user-12345-abcde",
    "firstName": "John",
    "lastName": "Smith",
    "organisationId": 5001,
    "scopes": ["read:wallboards", "write:wallboards"],
    "isAdmin": false,
    "isTeamLeader": true
  },
  "isAccessEnabled": true,
  "auth0Urls": {
    "url": "natterbox.eu.auth0.com",
    "clientId": "abc123def456ghi789jkl012mno345pq",
    "audience": "https://api.natterbox.com",
    "connection_name": "natterbox-saml"
  },
  "gatekeeperErrorMessage": "",
  "usersAvatars": {
    "user-12345-abcde": {
      "smallPhoto": "https://cdn.natterbox.com/avatars/user-12345.jpg"
    }
  },
  "listenInPermissions": {
    "availableListenInAgentIds": {
      "agent-001": true,
      "agent-002": true,
      "agent-003": false
    }
  }
}
```

### Relationships

- Root state slice accessed via `state.login`
- Contains `UserInfo`, `Auth0Urls`, and `ListenInPermissions`
- Used by authentication hooks and selectors
- Updated by login/logout actions

---

## LoginData

Login data utility object for making authenticated API calls.

### Purpose

Provides access to the Auth0 `getAccessTokenSilently` function for obtaining fresh access tokens when making API requests. Used by API utilities to ensure requests are properly authenticated.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `getAccessTokenSilently` | `function` | Yes | Auth0 function to get access token silently without user interaction |

### Validation Rules

- `getAccessTokenSilently` must be a valid async function
- Function should return a valid JWT access token
- Should handle token refresh automatically

### Example

```javascript
// Usage in API calls
const loginData = {
  getAccessTokenSilently: async () => {
    // Returns fresh JWT token
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...";
  }
};

// Making authenticated request
const token = await loginData.getAccessTokenSilently();
const response = await fetch('/api/wallboards', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Relationships

- Passed to API utility functions
- Obtained from Auth0's `useAuth0` hook
- Used in conjunction with `RequestOptions`

---

## RequestOptions

API request options object for configuring API calls.

### Purpose

Configures API request behavior, particularly for handling differences between standalone and Salesforce-embedded deployments.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isPackaged` | `boolean` | No | Whether the app is packaged (Salesforce managed package); affects API endpoints |

### Validation Rules

- `isPackaged` defaults to `false` if not provided
- When `true`, API calls route through Salesforce proxy endpoints

### Example

```json
{
  "isPackaged": false
}
```

```json
{
  "isPackaged": true
}
```

### Relationships

- Used alongside `LoginData` in API calls
- Determines API base URL routing

---

## ListenInPermissions

Permissions for call monitoring (listen-in) functionality.

### Purpose

Defines which agents the current user has permission to monitor (listen-in) during live calls. This is a critical security feature for call center supervision.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `availableListenInAgentIds` | `object` | Yes | Object mapping agent IDs to boolean permission status |

### Validation Rules

- `availableListenInAgentIds` must be an object
- Keys must be valid agent ID strings
- Values must be boolean (`true` = can listen, `false` = cannot listen)

### Example

```json
{
  "availableListenInAgentIds": {
    "agent-001": true,
    "agent-002": true,
    "agent-003": false,
    "agent-004": true,
    "agent-005": false
  }
}
```

### Relationships

- Contained within `LoginState.listenInPermissions`
- Used by Agent List and Agent Card components
- Determines visibility of "Listen In" action buttons

---

## UserAvatar

User avatar/profile image data.

### Purpose

Stores avatar image URLs for users, enabling display of profile pictures in the UI.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `smallPhoto` | `string` | No | URL to small photo/avatar image |

### Validation Rules

- `smallPhoto` must be a valid URL if provided
- URL should point to an accessible image resource
- Empty string indicates no avatar available

### Example

```json
{
  "smallPhoto": "https://cdn.natterbox.com/avatars/user-12345-small.jpg"
}
```

### Relationships

- Stored in `LoginState.usersAvatars` mapped by user ID
- Used by agent cards and user profile displays

---

## Common Use Cases

### 1. Checking User Permissions

```javascript
// Check if user can edit wallboards
const canEdit = userInfo.isAdmin || userInfo.isTeamLeader;

// Check specific scope
const hasScope = (scope) => userInfo.scopes.includes(scope);
const canManageCalls = hasScope('manage:calls');
```

### 2. Determining Listen-In Access

```javascript
// Check if current user can listen to specific agent
const canListenToAgent = (agentId) => {
  return listenInPermissions.availableListenInAgentIds[agentId] === true;
};
```

### 3. Making Authenticated API Calls

```javascript
const fetchWallboards = async (loginData, requestOptions) => {
  const token = await loginData.getAccessTokenSilently();
  const baseUrl = requestOptions.isPackaged 
    ? '/services/apexrest/wallboards'
    : '/api/wallboards';
    
  return fetch(baseUrl, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
};
```

### 4. Handling Authentication State

```javascript
// In React component
const { isAccessEnabled, gatekeeperErrorMessage, userInfo } = loginState;

if (isAccessEnabled === null) {
  return <LoadingSpinner />;
}

if (!isAccessEnabled) {
  return <ErrorPage message={gatekeeperErrorMessage} />;
}

return <AuthenticatedApp user={userInfo} />;
```

---

## Related Documentation

- [Wallboard Models](./wallboard-models.md) - For wallboard permission settings
- [Agent Models](./agent-models.md) - For agent availability states
- [Widget Models](./widget-models.md) - For widget-level permissions
- [UI Models](./ui-models.md) - For modal and error state handling