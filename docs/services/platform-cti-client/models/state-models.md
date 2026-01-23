# Application State Models

This document covers the Redux state structures used throughout the platform-cti-client application, including authentication state, main application state, feature-specific states, and UI state management.

## Overview

The platform-cti-client uses Redux for state management with a modular architecture. State is divided into logical slices that manage different aspects of the application:

- **Authentication**: User credentials and tokens
- **Main State**: Core application configuration and runtime settings
- **Feature States**: Groups, call logs, voicemail, and audio player
- **UI States**: Modal, footer, and notification management

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ReduxState (Root)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐                  │
│  │  AuthState   │    │  MainState   │    │  GroupsState  │                  │
│  ├──────────────┤    ├──────────────┤    ├───────────────┤                  │
│  │ authToken    │    │ isFreedomWeb │    │ groupSelected │                  │
│  │ natterbox{}  │    │ masterUUID   │    └───────────────┘                  │
│  └──────────────┘    │ viewType     │                                       │
│         │            │ sfQuery...   │    ┌────────────────┐                 │
│         │            └──────────────┘    │ CallLogsState  │                 │
│         │                   │            ├────────────────┤                 │
│         │                   │            │ callLogsFilter │                 │
│         ▼                   ▼            │ callLogsSearch │                 │
│  ┌─────────────────────────────────┐     └────────────────┘                 │
│  │         JWTExtracted            │                                        │
│  ├─────────────────────────────────┤     ┌─────────────────┐                │
│  │ natterboxOrgId                  │     │ VoicemailState  │                │
│  │ natterboxUserId                 │     ├─────────────────┤                │
│  └─────────────────────────────────┘     │ voicemailFilter │                │
│                                          └─────────────────┘                │
│  ┌──────────────────┐    ┌────────────────────┐                             │
│  │ AudioPlayerState │    │ FreedomWebAuthState│                             │
│  ├──────────────────┤    ├────────────────────┤                             │
│  │ audio.uuid      │    │ main: MainGlobals  │                             │
│  └──────────────────┘    │ auth: AuthState   │                             │
│                          │ sf: SFState       │                             │
│                          │ licences          │                             │
│                          └────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Root State Models

### ReduxState

The root Redux state structure containing all application state slices.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| router | object | Yes | Connected router state for navigation |
| main | MainState | Yes | Main reducer state with core configuration |
| voicemail | VoicemailState | Yes | Voicemail feature state |
| voicemailDrop | object | Yes | Voicemail drop feature state |
| notification | object | Yes | Notification management state |
| activites | object | Yes | Activities/tasks state |
| modal | object | Yes | Modal dialog state |
| footer | object | Yes | Footer UI state |
| dialList | object | Yes | Dial list feature state |
| groups | GroupsState | Yes | Groups feature state |
| callLogs | CallLogsState | Yes | Call logs feature state |
| settings | object | Yes | User settings state |
| wrapups | object | Yes | Wrapup feature state |
| auth | AuthState | Yes | Authentication state |
| audioPlayer | AudioPlayerState | Yes | Audio player state |

#### Example

```json
{
  "router": {
    "location": {
      "pathname": "/calls",
      "search": "",
      "hash": ""
    }
  },
  "main": {
    "isFreedomWeb": false,
    "masterUUID": "550e8400-e29b-41d4-a716-446655440000",
    "viewType": "FULL_VIEW"
  },
  "auth": {
    "authToken": "eyJhbGciOiJIUzI1NiIs...",
    "natterbox": {
      "orgId": "12345",
      "userId": "67890"
    }
  },
  "groups": {
    "groupSelected": 101
  },
  "callLogs": {
    "callLogsFilter": { "value": "All" },
    "callLogsSearch": ""
  },
  "voicemail": {
    "voicemailFilterSet": []
  },
  "audioPlayer": {
    "audio": {
      "uuid": null
    }
  },
  "modal": {},
  "footer": {},
  "dialList": {},
  "settings": {},
  "wrapups": {},
  "notification": {},
  "activites": {},
  "voicemailDrop": {}
}
```

---

### FreedomWebAuthState

FreedomWeb-specific authentication Redux state structure with persistence support.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| main | object | Yes | Main globals state for FreedomWeb |
| auth | AuthState | Yes | Auth state (persisted to storage) |
| sf | object | Yes | Salesforce state (persisted to storage) |
| licences | object | Yes | User licence information |

#### Validation Rules

- The `auth` and `sf` slices are configured for persistence
- State is rehydrated on application startup

#### Example

```json
{
  "main": {
    "initialized": true,
    "loading": false
  },
  "auth": {
    "authToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "natterbox": {
      "orgId": "org_12345",
      "userId": "user_67890"
    }
  },
  "sf": {
    "sessionId": "00D5g000004HqLK!AR4AQ...",
    "instanceUrl": "https://na1.salesforce.com"
  },
  "licences": {
    "natterbox": "FREEDOM_LICENSE",
    "salesforce": "STANDARD_LICENSE"
  }
}
```

---

## Authentication State Models

### AuthState

Authentication state stored in the Redux store, containing JWT tokens and Natterbox identity information.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| authToken | string | Yes | JWT authentication token for API requests |
| natterbox.orgId | string | Yes | Natterbox organization identifier |
| natterbox.userId | string | Yes | Natterbox user identifier |

#### Validation Rules

- `authToken` must be a valid JWT token
- `natterbox.orgId` and `natterbox.userId` are extracted from the JWT payload
- Token expiration is validated on API requests

#### Example

```json
{
  "authToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYXR0ZXJib3hPcmdJZCI6IjEyMzQ1IiwibmF0dGVyYm94VXNlcklkIjoiNjc4OTAiLCJleHAiOjE3MDQwNjcyMDB9.signature",
  "natterbox": {
    "orgId": "12345",
    "userId": "67890"
  }
}
```

#### Relationships

- Extracted from JWT using `JWTExtracted` model
- Used by WebSocket connections for authentication
- Referenced by API service calls

---

### JWTExtracted

Extracted fields from a decoded JWT token containing Natterbox identity information.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| natterboxOrgId | string | Yes | Natterbox organization ID from JWT claims |
| natterboxUserId | string | Yes | Natterbox user ID from JWT claims |

#### Validation Rules

- Values are extracted from JWT payload during token decoding
- Both fields must be present for valid authentication

#### Example

```json
{
  "natterboxOrgId": "org_98765",
  "natterboxUserId": "user_12345"
}
```

#### Usage

```typescript
// JWT decoding extracts these fields
const token = "eyJhbGciOiJIUzI1NiIs...";
const decoded = jwtDecode(token);
const extracted: JWTExtracted = {
  natterboxOrgId: decoded.natterboxOrgId,
  natterboxUserId: decoded.natterboxUserId
};
```

---

### LocalDetails

Local storage details retrieved by the `getLocalDetails` utility function.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sfSessionId | string | Yes | Salesforce session ID from local storage |
| accessToken | string | Yes | Access token for API authentication |

#### Example

```json
{
  "sfSessionId": "00D5g000004HqLK!AR4AQPkKBpH...",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Main Application State Models

### MainState

Main application state containing core configuration and runtime settings.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isFreedomWeb | boolean | Yes | Whether running in Freedom Web mode vs CTI mode |
| masterUUID | string | Yes | UUID of the master tab (for multi-tab coordination) |
| masterLastWrite | any | No | Timestamp of last master write for sync |
| viewType | string | Yes | Current view type (FULL_VIEW, LIMITED_VIEW, DENIED_VIEW) |
| sfQueryNamespace.prefix | string | Yes | Salesforce query namespace prefix |
| sfQueryNamespace.path | string | Yes | Salesforce query namespace path |

#### Validation Rules

- `viewType` must be one of: `FULL_VIEW`, `LIMITED_VIEW`, `DENIED_VIEW`
- `masterUUID` should be a valid UUID v4 format
- `sfQueryNamespace.path` is derived from prefix by replacing `__` with `/`

#### Example

```json
{
  "isFreedomWeb": false,
  "masterUUID": "550e8400-e29b-41d4-a716-446655440000",
  "masterLastWrite": 1704067200000,
  "viewType": "FULL_VIEW",
  "sfQueryNamespace": {
    "prefix": "nbavs__",
    "path": "nbavs/"
  }
}
```

#### Relationships

- Used by components to determine rendering mode
- Controls feature availability based on `viewType`
- Coordinates multi-tab behavior via `masterUUID`

---

### SalesforceQueryNamespaceAction

Redux action for setting the Salesforce query namespace configuration.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Action type: `SALESFORCE_QUERY_NAME_SPACE` |
| data.prefix | string | Yes | Namespace prefix (e.g., `nbavs__`) |
| data.path | string | Yes | Namespace path with `__` replaced by `/` |

#### Example

```json
{
  "type": "SALESFORCE_QUERY_NAME_SPACE",
  "data": {
    "prefix": "nbavs__",
    "path": "nbavs/"
  }
}
```

---

### CTIConfig

Global CTI configuration object available on `window.cticonfig`, providing environment and session information.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| viewType | string | No | View type for Freedom rendering |
| salesforce_sid | string | Yes | Salesforce session ID |
| salesforce_url | string | Yes | Salesforce host URL |
| namespacePrefix | string | Yes | Namespace prefix for Salesforce queries |
| uiTheme | string | No | UI theme configuration |
| smsLicensed | string | No | SMS license status ('true'/'false') |
| forceRemoteAction | boolean | No | Flag to force remote action usage |

#### Validation Rules

- `salesforce_sid` must be a valid Salesforce session ID
- `salesforce_url` must be a valid URL
- `smsLicensed` is a string representation of boolean

#### Example

```json
{
  "viewType": "FULL_VIEW",
  "salesforce_sid": "00D5g000004HqLK!AR4AQPkKBpH...",
  "salesforce_url": "https://na1.salesforce.com",
  "namespacePrefix": "nbavs__",
  "uiTheme": "Theme4d",
  "smsLicensed": "true",
  "forceRemoteAction": false
}
```

#### Usage

```typescript
// Accessing global config
const config = window.cticonfig;
const sfUrl = config.salesforce_url;
const sessionId = config.salesforce_sid;
```

---

## Feature State Models

### GroupsState

Redux state for managing group selection and group-related features.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| groupSelected | number | No | Currently selected group ID |

#### Validation Rules

- `groupSelected` must be a valid group ID or null/undefined when no group is selected

#### Example

```json
{
  "groupSelected": 101
}
```

#### Relationships

- Used by group subscription WebSocket messages
- Controls which group's data is displayed in the UI

---

### CallLogsState

Redux state for call logs filtering and search functionality.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| callLogsFilter | any | No | Current filter applied to call logs |
| callLogsSearch | string | No | Current search term for call logs |

#### Validation Rules

- `callLogsFilter` typically contains a `value` property with filter type
- `callLogsSearch` is used for text-based filtering

#### Example

```json
{
  "callLogsFilter": {
    "label": "Missed",
    "value": "Missed"
  },
  "callLogsSearch": "John Smith"
}
```

#### Related Models

- Works with `CallsFilterOption` for filter values
- Passed to `CallLogRefreshMessage` for worker updates

---

### VoicemailState

Redux state for voicemail filtering and display.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| voicemailFilterSet | array | Yes | Filtered voicemail list for display |

#### Example

```json
{
  "voicemailFilterSet": [
    {
      "id": "vm_001",
      "callerName": "John Smith",
      "callerNumber": "+14155551234",
      "duration": 45,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "vm_002",
      "callerName": "Jane Doe",
      "callerNumber": "+14155555678",
      "duration": 120,
      "timestamp": "2024-01-15T09:15:00Z"
    }
  ]
}
```

#### Relationships

- Updated by `VoicemailWorkerFilterMessage` processing
- Contains `VoicemailItem` objects

---

### AudioPlayerState

Redux state for managing audio playback across tabs.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| audio.uuid | string | No | UUID of the tab currently playing audio |

#### Validation Rules

- `audio.uuid` is null when no audio is playing
- Only one tab should play audio at a time

#### Example

```json
{
  "audio": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Usage

```typescript
// Check if this tab is playing audio
const isPlayingHere = audioPlayerState.audio.uuid === currentTabUUID;
```

---

## UI State Enumerations

### FooterTypes

Enumeration of footer type constants for call UI states.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| HANG_UP | string | Yes | Hang up footer type |
| CONSULT | string | Yes | Consult footer type |
| CONFERENCE | string | Yes | Conference footer type |
| ACTIVE_CALL | string | Yes | Active call footer type |
| LISTENING_IN_CALL | string | Yes | Listening in call footer type |

#### Example

```json
{
  "HANG_UP": "HANG_UP",
  "CONSULT": "CONSULT",
  "CONFERENCE": "CONFERENCE",
  "ACTIVE_CALL": "ACTIVE_CALL",
  "LISTENING_IN_CALL": "LISTENING_IN_CALL"
}
```

---

### ModalTypes

Enumeration of modal type constants for various dialog types.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DIALLING | string | Yes | Dialling modal type |
| LISTENING_IN | string | Yes | Listening in modal type |
| WRAP_UP | string | Yes | Wrap up modal type |
| TRANSFER | string | Yes | Transfer modal type |
| TRANSFERING | string | Yes | Transferring modal type |
| VOICEMAIL | string | Yes | Voicemail modal type |
| VOICEMAIL_DROP | string | Yes | Voicemail drop modal type |
| NEW_CALL | string | Yes | New call modal type |
| WRAP_UP_NOTES | string | Yes | Wrap up notes modal type |
| SECURE_PAYMENT | string | Yes | Secure payment modal type |

#### Example

```json
{
  "DIALLING": "DIALLING",
  "LISTENING_IN": "LISTENING_IN",
  "WRAP_UP": "WRAP_UP",
  "TRANSFER": "TRANSFER",
  "TRANSFERING": "TRANSFERING",
  "VOICEMAIL": "VOICEMAIL",
  "VOICEMAIL_DROP": "VOICEMAIL_DROP",
  "NEW_CALL": "NEW_CALL",
  "WRAP_UP_NOTES": "WRAP_UP_NOTES",
  "SECURE_PAYMENT": "SECURE_PAYMENT"
}
```

---

### ModalActions

Redux action types for modal state management.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SET_MODAL_DETAILS | string | Yes | Action to set modal details |
| SET_MODAL_DETAILS_BEFORE_TRANSFER | string | Yes | Action to set modal details before transfer |
| CLOSE_MODAL | string | Yes | Action to close modal |
| COMPLETE_WRAPUP | string | Yes | Action to complete wrapup |
| COMPLETE_WRAPUP_NEXT_ACTION | string | Yes | Action for next step after wrapup completion |
| DISREGARD_WRAPUP | string | Yes | Action to disregard wrapup |
| SAVE_FOR_LATER_WRAPUP | string | Yes | Action to save wrapup for later |
| EXTEND_CALL_QUEUE_WRAP_UP | string | Yes | Action to extend call queue wrap up time |
| OPEN_WRAPUP_MODAL | string | Yes | Action to open wrapup modal |

#### Example

```typescript
// Dispatching modal actions
dispatch({ type: ModalActions.SET_MODAL_DETAILS, payload: modalData });
dispatch({ type: ModalActions.CLOSE_MODAL });
dispatch({ type: ModalActions.COMPLETE_WRAPUP, payload: wrapupData });
```

---

### ZIndexConstants

Z-index layering constants for UI component stacking.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DEFAULT_Z_INDEX | number | Yes | Default z-index value for standard elements |
| ABOVE_MODAL_Z_INDEX | number | Yes | Z-index for elements above modals |

#### Example

```json
{
  "DEFAULT_Z_INDEX": 1,
  "ABOVE_MODAL_Z_INDEX": 1000
}
```

---

## License and View Type Enumerations

### ViewTypes

View access level constants determined by license combination.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FULL_VIEW | string | Yes | Full view access |
| LIMITED_VIEW | string | Yes | Limited view access |
| DENIED_VIEW | string | Yes | Denied view access |

#### Example

```json
{
  "FULL_VIEW": "FULL_VIEW",
  "LIMITED_VIEW": "LIMITED_VIEW",
  "DENIED_VIEW": "DENIED_VIEW"
}
```

#### Usage

```typescript
// Determining view type based on licenses
if (hasNatterboxLicense && hasSalesforceLicense) {
  return ViewTypes.FULL_VIEW;
} else if (hasNatterboxLicense) {
  return ViewTypes.LIMITED_VIEW;
} else {
  return ViewTypes.DENIED_VIEW;
}
```

---

### NatterboxLicenses

Natterbox license type constants.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FREEDOM_LICENSE | string | Yes | Freedom license type |
| PBX_LICENSE | string | Yes | PBX license type |

#### Example

```json
{
  "FREEDOM_LICENSE": "FREEDOM_LICENSE",
  "PBX_LICENSE": "PBX_LICENSE"
}
```

---

### SalesforceLicenses

Salesforce license type constants.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| STANDARD_LICENSE | string | Yes | Standard Salesforce license |
| CHATTER_LICENSE | string | Yes | Chatter-only Salesforce license |

#### Example

```json
{
  "STANDARD_LICENSE": "STANDARD_LICENSE",
  "CHATTER_LICENSE": "CHATTER_LICENSE"
}
```

---

## User and Group Category Models

### UserGroupCategories

Constants for categorizing user groups in the UI.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MY_GROUP | string | Yes | Primary group category label |
| MY_OTHER_GROUPS | string | Yes | Secondary groups category label |
| ALL_OTHER_GROUPS | string | Yes | All other groups category label |
| NO_PRIMARY_GROUP_TEXT | string | Yes | Message when user has no primary group |

#### Example

```json
{
  "MY_GROUP": "My Group",
  "MY_OTHER_GROUPS": "My Other Groups",
  "ALL_OTHER_GROUPS": "All Other Groups",
  "NO_PRIMARY_GROUP_TEXT": "You have no primary group assigned"
}
```

---

### UserGroup

Represents a user group with grouping classification for display.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string \| number | Yes | Unique identifier for the group |
| name | string | Yes | Display name of the group |
| group | string | Yes | Grouping category (MY_GROUP, MY_OTHER_GROUPS, ALL_OTHER_GROUPS) |
| isDisabled | boolean | No | Whether the group option is disabled |

#### Example

```json
{
  "id": 101,
  "name": "Sales Team",
  "group": "MY_GROUP",
  "isDisabled": false
}
```

---

### UserTypeEnum

Enumeration of user types for address book categorization.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PBX_USERS | string | Yes | PBX users category |
| GROUP_USERS | string | Yes | Group users category |
| CONTACT_USERS | string | Yes | Contact users category |
| ACCOUNT_USERS | string | Yes | Account users category |

#### Example

```json
{
  "PBX_USERS": "PBX_USERS",
  "GROUP_USERS": "GROUP_USERS",
  "CONTACT_USERS": "CONTACT_USERS",
  "ACCOUNT_USERS": "ACCOUNT_USERS"
}
```

---

## UI Component State Models

### IconState

Represents the state configuration for button/icon display.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isIconDisabled | boolean | Yes | Whether the icon is disabled |
| isIconActive | boolean | Yes | Whether the icon is active |

#### Example

```json
{
  "isIconDisabled": false,
  "isIconActive": true
}
```

---

### IconObject

Output object from `disableBtns` function with cursor and icon classes.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cursor | string | Yes | CSS cursor class - 'cursor-non-active' or 'on-active' |
| icon | string | Yes | CSS icon class, may include 'greyed-out-non-active' |

#### Example

```json
{
  "cursor": "cursor-non-active",
  "icon": "phone-icon greyed-out-non-active"
}
```

---

### HistoryLocation

React Router history location object for navigation state.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pathname | string | Yes | Current pathname |
| state | object | No | Location state object |

#### Example

```json
{
  "pathname": "/calls",
  "state": {
    "from": "/groups",
    "callId": "call_12345"
  }
}
```

---

### NavLink

Navigation link model for menu/navigation filtering.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| to | string | Yes | Path/route for the navigation link |

#### Example

```json
{
  "to": "/call-logs"
}
```

---

## Common Patterns

### State Selection

```typescript
// Selecting state in components
const authToken = useSelector((state: ReduxState) => state.auth.authToken);
const viewType = useSelector((state: ReduxState) => state.main.viewType);
const selectedGroup = useSelector((state: ReduxState) => state.groups.groupSelected);
```

### State Updates

```typescript
// Dispatching state updates
dispatch({ type: 'SALESFORCE_QUERY_NAME_SPACE', data: { prefix: 'nbavs__', path: 'nbavs/' } });
dispatch({ type: 'SET_GROUP_SELECTED', payload: 101 });
dispatch({ type: 'SET_CALL_LOGS_FILTER', payload: { value: 'Missed' } });
```

### View Type Checking

```typescript
// Conditional rendering based on view type
if (mainState.viewType === ViewTypes.FULL_VIEW) {
  // Show full feature set
} else if (mainState.viewType === ViewTypes.LIMITED_VIEW) {
  // Show limited features
} else {
  // Show access denied message
}
```