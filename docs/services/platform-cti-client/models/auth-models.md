# Authentication Models

This document covers JWT tokens, authentication state, and user identity models used in the platform-cti-client application. These models manage user authentication, session management, and identity information across the CTI system.

## Overview

The authentication system in platform-cti-client relies on several interconnected models:

- **JWT-based authentication** for API access
- **Salesforce session integration** for CRM connectivity
- **Natterbox identity** for telephony services
- **Redux state management** for authentication persistence

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐     │
│   │  CTIConfig   │───▶│ LocalDetails │───▶│    AuthState     │     │
│   │  (Initial)   │    │  (Storage)   │    │    (Redux)       │     │
│   └──────────────┘    └──────────────┘    └──────────────────┘     │
│         │                    │                     │                │
│         ▼                    ▼                     ▼                │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐     │
│   │ Salesforce   │    │ JWT Token    │    │  JWTExtracted    │     │
│   │ Session ID   │    │ accessToken  │    │  (Decoded)       │     │
│   └──────────────┘    └──────────────┘    └──────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## CTIConfig

Global CTI configuration object available on `window.cticonfig`. This model provides the initial configuration values passed from the Salesforce environment to the CTI client.

### Purpose

- Provides initial configuration from the hosting environment
- Contains Salesforce session credentials for authentication
- Configures UI theming and feature licensing
- Available globally via `window.cticonfig`

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `viewType` | string | No | View type for Freedom rendering (e.g., "FULL_VIEW", "LIMITED_VIEW") |
| `salesforce_sid` | string | Yes | Salesforce session ID for API authentication |
| `salesforce_url` | string | Yes | Salesforce host URL for SF origin calculation |
| `namespacePrefix` | string | No | Namespace prefix for Salesforce queries (managed package support) |
| `uiTheme` | string | No | UI theme configuration for styling |
| `smsLicensed` | string | No | SMS license status ('true'/'false' as string) |
| `forceRemoteAction` | boolean | No | Flag to force remote action usage over REST API |

### Validation Rules

- `salesforce_sid` must be a valid Salesforce session identifier
- `salesforce_url` must be a valid HTTPS URL
- `smsLicensed` uses string booleans ('true'/'false') rather than actual booleans

### Example

```json
{
  "viewType": "FULL_VIEW",
  "salesforce_sid": "00D5g00000ABC123!AQEAQI.xYz789AbCdEfGhIjKlMnOpQrStUvWxYz",
  "salesforce_url": "https://mycompany.lightning.force.com",
  "namespacePrefix": "natterbox__",
  "uiTheme": "Theme4d",
  "smsLicensed": "true",
  "forceRemoteAction": false
}
```

### Relationships

- Provides initial values for **LocalDetails**
- `salesforce_sid` is used to establish Salesforce API connections
- `viewType` influences **MainState** and feature availability
- `salesforce_url` used for cross-origin communication calculations

### Common Use Cases

1. **Initial Application Bootstrap**: Reading configuration when CTI client loads
2. **Salesforce Integration**: Using session ID for Salesforce API calls
3. **Feature Flags**: Checking SMS licensing before enabling SMS features

---

## AuthState

Authentication state stored in the Redux store. This model maintains the current authentication credentials and user identity throughout the application lifecycle.

### Purpose

- Stores the active JWT authentication token
- Maintains Natterbox organization and user identifiers
- Provides centralized authentication state for all components
- Persisted across page refreshes (in FreedomWeb)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `authToken` | string | Yes | JWT authentication token for API requests |
| `natterbox.orgId` | string | Yes | Natterbox organization ID extracted from JWT |
| `natterbox.userId` | string | Yes | Natterbox user ID extracted from JWT |

### Validation Rules

- `authToken` must be a valid JWT token (three Base64-encoded segments separated by dots)
- `natterbox.orgId` must be a non-empty string representing the organization
- `natterbox.userId` must be a non-empty string representing the authenticated user

### Example

```json
{
  "authToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYXR0ZXJib3hPcmdJZCI6IjEyMzQ1IiwibmF0dGVyYm94VXNlcklkIjoiNjc4OTAiLCJpYXQiOjE2OTg3NjU0MzIsImV4cCI6MTY5ODg1MTgzMn0.signature",
  "natterbox": {
    "orgId": "12345",
    "userId": "67890"
  }
}
```

### Relationships

- Populated from **JWTExtracted** after token decoding
- Token originates from **LocalDetails** storage
- Used by **WebsocketStartMessage** for connection authentication
- Referenced by **WebsocketGroupMessage** and **WebsocketUserSubscribeMessage**
- Part of **ReduxState** (`state.auth`)
- Equivalent structure in **FreedomWebAuthState**

### Common Use Cases

1. **API Authentication**: Attaching token to REST API requests
2. **WebSocket Authentication**: Authenticating WebSocket connections
3. **User Context**: Determining current user for personalized features
4. **Organization Scope**: Filtering data by organization

---

## LocalDetails

Local storage details retrieved by the `getLocalDetails` function. This model represents the authentication credentials stored in the browser's local storage.

### Purpose

- Persists authentication credentials across browser sessions
- Provides credentials during application initialization
- Enables session restoration without re-authentication
- Bridges initial configuration to runtime authentication

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sfSessionId` | string | Yes | Salesforce session ID for CRM API access |
| `accessToken` | string | Yes | JWT access token for Natterbox API access |

### Validation Rules

- `sfSessionId` must be a valid Salesforce session format
- `accessToken` must be a valid JWT token
- Both values should be checked for expiration before use

### Example

```json
{
  "sfSessionId": "00D5g00000ABC123!AQEAQI.xYz789AbCdEfGhIjKlMnOpQrStUvWxYz",
  "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYXR0ZXJib3hPcmdJZCI6IjEyMzQ1IiwibmF0dGVyYm94VXNlcklkIjoiNjc4OTAiLCJpYXQiOjE2OTg3NjU0MzIsImV4cCI6MTY5ODg1MTgzMn0.signature"
}
```

### Relationships

- Initialized from **CTIConfig** values
- `accessToken` is decoded into **JWTExtracted**
- Populates **AuthState** during application startup
- Used in **CallLogRefreshMessage** for worker authentication

### Common Use Cases

1. **Session Restoration**: Loading saved credentials on page load
2. **Token Refresh**: Storing new tokens after refresh operations
3. **Dual Authentication**: Maintaining both Salesforce and Natterbox sessions

---

## JWTExtracted

Extracted JWT token fields after decoding the authentication token. This model represents the decoded payload of the JWT token.

### Purpose

- Provides decoded identity information from JWT
- Extracts Natterbox organization and user IDs
- Enables identity verification without API calls
- Populates AuthState with user context

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `natterboxOrgId` | string | Yes | Natterbox organization ID from token payload |
| `natterboxUserId` | string | Yes | Natterbox user ID from token payload |

### Validation Rules

- Both fields must be present in a valid JWT payload
- Values must match expected format for Natterbox identifiers
- Token expiration should be validated before trusting extracted values

### Example

```json
{
  "natterboxOrgId": "12345",
  "natterboxUserId": "67890"
}
```

### JWT Token Structure

The JWT token that produces this model has the following structure:

```
Header.Payload.Signature

Header: {
  "alg": "RS256",
  "typ": "JWT"
}

Payload: {
  "natterboxOrgId": "12345",
  "natterboxUserId": "67890",
  "iat": 1698765432,
  "exp": 1698851832
}
```

### Relationships

- Extracted from `accessToken` in **LocalDetails**
- Populates `natterbox.orgId` and `natterbox.userId` in **AuthState**
- Used for subscription paths in **WebsocketGroupMessage**

### Common Use Cases

1. **Token Decoding**: Extracting identity from JWT during login
2. **State Initialization**: Populating Redux auth state
3. **Identity Verification**: Confirming user identity for operations

---

## FreedomWebAuthState

FreedomWeb authentication Redux state structure. This model represents the authentication-related portion of the Redux state specific to FreedomWeb mode.

### Purpose

- Organizes authentication state for FreedomWeb application
- Separates concerns between auth, Salesforce, and licensing
- Enables selective persistence of state slices
- Provides type structure for Redux selectors

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `main` | object | Yes | Main globals state (application-wide settings) |
| `auth` | object | Yes | Auth state - persisted across sessions |
| `sf` | object | Yes | Salesforce state - persisted for SF integration |
| `licences` | object | Yes | Licences state for feature gating |

### Validation Rules

- `auth` object must conform to **AuthState** structure
- Persistence configuration must be properly set for `auth` and `sf`
- `licences` must be validated against **NatterboxLicenses** and **SalesforceLicenses**

### Example

```json
{
  "main": {
    "isFreedomWeb": true,
    "viewType": "FULL_VIEW",
    "masterUUID": "550e8400-e29b-41d4-a716-446655440000"
  },
  "auth": {
    "authToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "natterbox": {
      "orgId": "12345",
      "userId": "67890"
    }
  },
  "sf": {
    "sessionId": "00D5g00000ABC123!AQEAQI...",
    "instanceUrl": "https://mycompany.lightning.force.com"
  },
  "licences": {
    "natterbox": "FREEDOM_LICENSE",
    "salesforce": "STANDARD_LICENSE"
  }
}
```

### Relationships

- Contains **AuthState** as `auth` property
- Part of overall **ReduxState** in FreedomWeb mode
- `licences` relates to **NatterboxLicenses** and **SalesforceLicenses** constants
- `main` relates to **MainState** model

### Common Use Cases

1. **State Hydration**: Restoring persisted auth state on load
2. **License Checking**: Determining available features
3. **Session Management**: Managing multiple authentication contexts

---

## NatterboxLicenses

Natterbox license type constants for licensing decisions.

### Purpose

- Defines Natterbox product license types
- Used for feature gating based on subscription
- Determines view access levels

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `FREEDOM_LICENSE` | string (constant) | - | Freedom license type - full CTI features |
| `PBX_LICENSE` | string (constant) | - | PBX license type - basic telephony features |

### Example

```javascript
const NatterboxLicenses = {
  FREEDOM_LICENSE: "FREEDOM_LICENSE",
  PBX_LICENSE: "PBX_LICENSE"
};
```

### Relationships

- Used in **FreedomWebAuthState** licences
- Combined with **SalesforceLicenses** to determine **ViewTypes**
- Influences available features throughout application

---

## SalesforceLicenses

Salesforce license type constants for CRM integration decisions.

### Purpose

- Defines Salesforce license types
- Determines CRM integration capabilities
- Affects data access and storage options

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `STANDARD_LICENSE` | string (constant) | - | Standard Salesforce license with full CRM access |
| `CHATTER_LICENSE` | string (constant) | - | Chatter-only license with limited CRM access |

### Example

```javascript
const SalesforceLicenses = {
  STANDARD_LICENSE: "STANDARD_LICENSE",
  CHATTER_LICENSE: "CHATTER_LICENSE"
};
```

### Relationships

- Used in **FreedomWebAuthState** licences
- Combined with **NatterboxLicenses** for view determination
- Affects Salesforce query capabilities

---

## ViewTypes

View access level constants determined by license combinations.

### Purpose

- Defines UI access levels based on licensing
- Controls feature visibility and availability
- Provides consistent access control constants

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `FULL_VIEW` | string (constant) | - | Full view access - all features available (Freedom + Standard) |
| `LIMITED_VIEW` | string (constant) | - | Limited view access - restricted feature set |
| `DENIED_VIEW` | string (constant) | - | Denied view access - invalid or missing license |

### License to View Mapping

| Natterbox License | Salesforce License | View Type |
|-------------------|-------------------|-----------|
| FREEDOM_LICENSE | STANDARD_LICENSE | FULL_VIEW |
| FREEDOM_LICENSE | CHATTER_LICENSE | LIMITED_VIEW |
| PBX_LICENSE | STANDARD_LICENSE | LIMITED_VIEW |
| PBX_LICENSE | CHATTER_LICENSE | DENIED_VIEW |
| (none) | (any) | DENIED_VIEW |

### Example

```javascript
const ViewTypes = {
  FULL_VIEW: "FULL_VIEW",
  LIMITED_VIEW: "LIMITED_VIEW",
  DENIED_VIEW: "DENIED_VIEW"
};
```

### Relationships

- Stored in **CTIConfig** `viewType` field
- Referenced in **MainState** `viewType` field
- Determines navigation and feature availability

---

## LicenseType

Combined license type constants (alias model for convenience).

### Purpose

- Provides unified access to all license constants
- Simplifies imports for license checking code

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `FREEDOM_LICENSE` | constant | - | Freedom license type (from NatterboxLicenses) |
| `PBX_LICENSE` | constant | - | PBX license type (from NatterboxLicenses) |
| `STANDARD_LICENSE` | constant | - | Standard Salesforce license (from SalesforceLicenses) |

### Example

```javascript
import { FREEDOM_LICENSE, PBX_LICENSE, STANDARD_LICENSE } from './constants';

function hasFullAccess(natterboxLicense, sfLicense) {
  return natterboxLicense === FREEDOM_LICENSE && 
         sfLicense === STANDARD_LICENSE;
}
```

---

## Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Authentication Lifecycle                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. INITIALIZATION                                                           │
│     ┌────────────┐                                                          │
│     │ Page Load  │                                                          │
│     └─────┬──────┘                                                          │
│           │                                                                  │
│           ▼                                                                  │
│     ┌────────────────┐      ┌────────────────┐                              │
│     │   CTIConfig    │─────▶│  LocalDetails  │                              │
│     │ (window.cti)   │      │  (Storage)     │                              │
│     └────────────────┘      └───────┬────────┘                              │
│                                     │                                        │
│  2. TOKEN PROCESSING                │                                        │
│           ┌─────────────────────────┘                                        │
│           │                                                                  │
│           ▼                                                                  │
│     ┌────────────────┐      ┌────────────────┐                              │
│     │ JWT Decoding   │─────▶│  JWTExtracted  │                              │
│     └────────────────┘      └───────┬────────┘                              │
│                                     │                                        │
│  3. STATE POPULATION                │                                        │
│           ┌─────────────────────────┘                                        │
│           │                                                                  │
│           ▼                                                                  │
│     ┌────────────────┐      ┌────────────────┐                              │
│     │   AuthState    │◀────▶│   ReduxStore   │                              │
│     │   (Redux)      │      │  (Persisted)   │                              │
│     └───────┬────────┘      └────────────────┘                              │
│             │                                                                │
│  4. AUTHENTICATION USE              │                                        │
│           ┌─────────────────────────┘                                        │
│           │                                                                  │
│           ├──────────────────┬──────────────────┐                           │
│           ▼                  ▼                  ▼                           │
│     ┌──────────┐      ┌──────────┐      ┌──────────────┐                   │
│     │ REST API │      │WebSocket │      │  Salesforce  │                   │
│     │  Calls   │      │  Auth    │      │     API      │                   │
│     └──────────┘      └──────────┘      └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Accessing Authentication State

```javascript
// Using Redux selector
import { useSelector } from 'react-redux';

function MyComponent() {
  const authToken = useSelector(state => state.auth.authToken);
  const orgId = useSelector(state => state.auth.natterbox.orgId);
  const userId = useSelector(state => state.auth.natterbox.userId);
  
  // Use for API calls
  const headers = {
    'Authorization': `Bearer ${authToken}`
  };
}
```

### Checking License Access

```javascript
import { FULL_VIEW, LIMITED_VIEW, DENIED_VIEW } from './constants';

function checkAccess(viewType) {
  switch (viewType) {
    case FULL_VIEW:
      return { canMakeCalls: true, canAccessReports: true, canManageSettings: true };
    case LIMITED_VIEW:
      return { canMakeCalls: true, canAccessReports: false, canManageSettings: false };
    case DENIED_VIEW:
    default:
      return { canMakeCalls: false, canAccessReports: false, canManageSettings: false };
  }
}
```

### Initializing Authentication from Config

```javascript
function initializeAuth() {
  // Read from global config
  const config = window.cticonfig;
  
  // Get stored details
  const localDetails = getLocalDetails();
  
  // Extract JWT claims
  const jwtExtracted = decodeJWT(localDetails.accessToken);
  
  // Dispatch to Redux store
  dispatch({
    type: 'SET_AUTH_STATE',
    payload: {
      authToken: localDetails.accessToken,
      natterbox: {
        orgId: jwtExtracted.natterboxOrgId,
        userId: jwtExtracted.natterboxUserId
      }
    }
  });
}
```

---

## Related Documentation

- [State Models](./state-models.md) - Redux state structures including MainState and ReduxState
- [WebSocket Models](./websocket-models.md) - WebSocket authentication messages
- [Salesforce Models](./salesforce-models.md) - Salesforce integration and session management