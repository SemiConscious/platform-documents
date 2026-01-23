# WebSocket Message Models

This document details the message structures used for WebSocket communication in the platform-cti-client. These models define the payloads for establishing connections, managing subscriptions, and handling real-time events for presence, availability, and messaging.

## Overview

The WebSocket messaging system supports:
- **Connection Management**: Authentication and connection lifecycle
- **Subscriptions**: User and group subscription management
- **Real-time Updates**: Presence, availability, and message notifications
- **Client Identification**: Version and client type tracking

## Entity Relationship Diagram

```
┌─────────────────────────┐
│    WebSocketMessage     │
│    (Base Structure)     │
└───────────┬─────────────┘
            │
            │ extends/specializes
            │
    ┌───────┴───────┬───────────────┬────────────────┐
    │               │               │                │
    ▼               ▼               ▼                ▼
┌─────────┐  ┌───────────┐  ┌────────────┐  ┌─────────────────┐
│Websocket│  │Websocket  │  │Websocket   │  │WebsocketResponse│
│Start    │  │Group      │  │User        │  │Message          │
│Message  │  │Message    │  │Subscribe   │  │                 │
└────┬────┘  └─────┬─────┘  │Message     │  └────────┬────────┘
     │             │        └─────┬──────┘           │
     │             │              │                  │
     │             ▼              │                  │
     │      ┌───────────┐        │                  │
     │      │Websocket  │        │                  │
     │      │Subscribe  │◄───────┘                  │
     │      │Payload    │                           │
     │      └───────────┘                           │
     │                                              │
     ▼                                              ▼
┌─────────────────┐                    ┌─────────────────────┐
│WebSocketClient  │                    │UserPresenceData     │
│Info             │                    │(event payload)      │
└─────────────────┘                    └─────────────────────┘
```

---

## Core WebSocket Message Structure

### WebSocketMessage

Base WebSocket message structure used for all WebSocket communication.

#### Purpose
Defines the common structure for WebSocket messages including authentication, subscriptions, and responses. All WebSocket communication follows this base format.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type identifier (`auth`, `subscribe`, `unsubscribe`, `tick`, `error`, `response`) |
| `accessToken` | string | Conditional | JWT authentication token (required for `auth` messages) |
| `client` | WebSocketClientInfo | Conditional | Client identification information (required for `auth` messages) |
| `path` | string | Conditional | Subscription path (required for `subscribe`/`unsubscribe` messages) |
| `message` | string | No | Message content (e.g., `'welcome'` for tick messages) |
| `data` | array | No | Response data array for `response` type messages |

#### Validation Rules
- `type` must be one of the defined message types
- `auth` messages must include `accessToken` and `client`
- `subscribe`/`unsubscribe` messages must include `path`

#### Example JSON

**Authentication Message:**
```json
{
  "type": "auth",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYXR0ZXJib3hPcmdJZCI6IjEyMzQ1IiwibmF0dGVyYm94VXNlcklkIjoiNjc4OTAifQ.signature",
  "client": {
    "name": "CTI 2.0",
    "version": "2.5.1"
  }
}
```

**Subscribe Message:**
```json
{
  "type": "subscribe",
  "path": "/org/12345/user/67890/presence"
}
```

**Tick/Heartbeat Message:**
```json
{
  "type": "tick",
  "message": "welcome"
}
```

**Response Message:**
```json
{
  "type": "response",
  "data": [
    {
      "userId": 67890,
      "presence": "ANSWERED",
      "availability": "Available"
    }
  ]
}
```

---

### WebSocketClientInfo

Client information sent during WebSocket authentication to identify the connecting application.

#### Purpose
Provides server-side visibility into which client application and version is connecting, enabling version-specific handling and analytics.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Client application name (`FreedomWeb`, `CTI 2.0`, `FreedomCTI`) |
| `version` | string | Yes | Client version from `CTI_CLIENT_VERSION` constant |

#### Validation Rules
- `name` must be a recognized client identifier
- `version` should follow semantic versioning format

#### Example JSON

```json
{
  "name": "CTI 2.0",
  "version": "2.5.1"
}
```

```json
{
  "name": "FreedomWeb",
  "version": "3.0.0"
}
```

#### Relationships
- Embedded within `WebSocketMessage` for authentication
- Used by server for client identification and feature flagging

---

## Connection Management Messages

### WebsocketStartMessage

Message payload for initiating a WebSocket connection from the application.

#### Purpose
Contains all necessary information to establish and authenticate a WebSocket connection, including endpoint configuration and user context.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type, always `WEBSOCKET_START` |
| `endpoint` | string | Yes | WebSocket server endpoint URL |
| `accessToken` | string | Yes | JWT access token for authentication |
| `uiTheme` | string | No | UI theme setting for client configuration |
| `isFreedomWeb` | boolean | Yes | Flag indicating if running in Freedom Web mode |
| `clientRequestId` | string | Conditional | UUID for client request (required for messages WebSocket) |
| `users` | string | Conditional | User string for subscription (required for messages WebSocket) |

#### Validation Rules
- `type` must be exactly `WEBSOCKET_START`
- `endpoint` must be a valid WebSocket URL (wss:// or ws://)
- `accessToken` must be a valid JWT token
- `clientRequestId` must be a valid UUID when provided

#### Example JSON

**Standard Connection:**
```json
{
  "type": "WEBSOCKET_START",
  "endpoint": "wss://realtime.natterbox.com/v1/events",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "uiTheme": "Theme4d",
  "isFreedomWeb": false
}
```

**Messages WebSocket Connection:**
```json
{
  "type": "WEBSOCKET_START",
  "endpoint": "wss://messages.natterbox.com/v1/subscribe",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "uiTheme": "Theme4d",
  "isFreedomWeb": true,
  "clientRequestId": "550e8400-e29b-41d4-a716-446655440000",
  "users": "org:12345:user:67890"
}
```

#### Common Use Cases
- Application initialization
- Reconnection after network interruption
- Switching between WebSocket endpoints

---

## Subscription Messages

### WebsocketGroupMessage

Message payload for subscribing to or unsubscribing from group presence updates.

#### Purpose
Manages group-level subscriptions to receive real-time updates about group members' presence and availability status.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type: `WEBSOCKET_GROUP_SUBSCRIBE` or `WEBSOCKET_GROUP_UNSUBSCRIBE` |
| `orgId` | string | Yes | Natterbox organization identifier |
| `groupId` | number | Yes | Group identifier to subscribe/unsubscribe |

#### Validation Rules
- `type` must be exactly `WEBSOCKET_GROUP_SUBSCRIBE` or `WEBSOCKET_GROUP_UNSUBSCRIBE`
- `orgId` must be a valid organization identifier
- `groupId` must be a positive integer

#### Example JSON

**Subscribe to Group:**
```json
{
  "type": "WEBSOCKET_GROUP_SUBSCRIBE",
  "orgId": "12345",
  "groupId": 100
}
```

**Unsubscribe from Group:**
```json
{
  "type": "WEBSOCKET_GROUP_UNSUBSCRIBE",
  "orgId": "12345",
  "groupId": 100
}
```

#### Common Use Cases
- User navigates to Teams/Groups view
- User changes selected group in dropdown
- User leaves Teams/Groups view (cleanup)

#### Relationships
- Triggers `UserPresenceData` events for group members
- Related to `GroupsState.groupSelected` in Redux store

---

### WebsocketUserSubscribeMessage

Message payload for subscribing to individual user presence updates.

#### Purpose
Establishes a subscription for real-time presence and availability updates for a specific user, typically the logged-in user.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type, always `WEBSOCKET_USER_SUBSCRIBE` |
| `orgId` | string | Yes | Natterbox organization identifier |
| `userId` | number | Yes | Natterbox user ID to subscribe to |

#### Validation Rules
- `type` must be exactly `WEBSOCKET_USER_SUBSCRIBE`
- `orgId` must be a valid organization identifier
- `userId` must be a positive integer

#### Example JSON

```json
{
  "type": "WEBSOCKET_USER_SUBSCRIBE",
  "orgId": "12345",
  "userId": 67890
}
```

#### Common Use Cases
- Application startup (subscribe to own presence)
- Monitoring specific user's status
- Call center supervisor functionality

#### Relationships
- Triggers `UserPresenceData` events
- Related to `AuthState.natterbox.userId`

---

### WebsocketSubscribePayload

Payload structure for subscribing to the messages WebSocket service.

#### Purpose
Defines the subscription request format for the messages WebSocket, enabling receipt of unread message count updates.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request` | string | Yes | Request type identifier |
| `clientRequestId` | string | Yes | UUID for correlating request/response |
| `data.users` | array | Yes | Array of user identifier strings to subscribe |

#### Validation Rules
- `clientRequestId` must be a valid UUID
- `data.users` must be a non-empty array
- Each user string should follow the format `org:{orgId}:user:{userId}`

#### Example JSON

```json
{
  "request": "subscribe",
  "clientRequestId": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "users": [
      "org:12345:user:67890",
      "org:12345:user:67891"
    ]
  }
}
```

#### Common Use Cases
- Initial subscription to message notifications
- Multi-user monitoring scenarios
- Team inbox functionality

#### Relationships
- Referenced in `WebsocketStartMessage.clientRequestId`
- Generates `WebsocketResponseMessage` events

---

## Response and Event Messages

### WebsocketResponseMessage

Response message received from the messages WebSocket service.

#### Purpose
Delivers real-time updates about user message statistics, particularly unread message counts.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation` | string | Yes | Operation type (e.g., `'MODIFY'`, `'INSERT'`) |
| `data.userStatistics.unreadMessages` | number | No | Count of unread messages for the user |

#### Validation Rules
- `operation` indicates the type of change that triggered the message
- `unreadMessages` is a non-negative integer

#### Example JSON

```json
{
  "operation": "MODIFY",
  "data": {
    "userStatistics": {
      "unreadMessages": 5
    }
  }
}
```

```json
{
  "operation": "INSERT",
  "data": {
    "userStatistics": {
      "unreadMessages": 1
    }
  }
}
```

#### Common Use Cases
- Updating unread message badge in UI
- Triggering notification sounds
- Updating message list views

---

### UserPresenceData

User presence and availability data received from WebSocket events.

#### Purpose
Provides real-time updates about a user's call state (presence) and availability status, enabling live status displays in the application.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | number | Yes | Natterbox user identifier |
| `presence` | string | No | User presence status (`ANSWERED`, `BRIDGED`, `RINGING`, or empty) |
| `logicalDirection` | string | No | Call direction (`Inbound`, `Outbound`) |
| `callChannelUUID` | string | No | UUID of the active call channel |
| `availability` | string | No | Availability state name (e.g., `Available`, `Busy`, `Away`) |
| `availabilityStateId` | number | No | Numeric ID of the availability state |
| `availabilityProfileId` | number | No | ID of the availability profile containing the state |

#### Validation Rules
- `userId` must be a positive integer
- `presence` must be one of the defined `UserPresenceEnum` values when set
- `logicalDirection` must be `Inbound` or `Outbound` when present

#### Example JSON

**User on Active Call:**
```json
{
  "userId": 67890,
  "presence": "ANSWERED",
  "logicalDirection": "Inbound",
  "callChannelUUID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "availability": "On Call",
  "availabilityStateId": 3,
  "availabilityProfileId": 1
}
```

**User Available:**
```json
{
  "userId": 67890,
  "presence": "",
  "logicalDirection": "",
  "callChannelUUID": "",
  "availability": "Available",
  "availabilityStateId": 1,
  "availabilityProfileId": 1
}
```

**User Ringing:**
```json
{
  "userId": 67890,
  "presence": "RINGING",
  "logicalDirection": "Outbound",
  "callChannelUUID": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "availability": "Available",
  "availabilityStateId": 1,
  "availabilityProfileId": 1
}
```

#### Common Use Cases
- Updating user status indicators in team views
- Showing call state in contact cards
- Enabling/disabling call controls based on user state
- Listen-in functionality (using `callChannelUUID`)

#### Relationships
- Mapped to `UserDisplayItem` for UI rendering
- Mapped to `PBXResultItem` for address book display
- References `AvailabilityState` via `availabilityStateId`
- References `AvailabilityProfile` via `availabilityProfileId`

---

## Related Display Models

### UserDisplayItem

User display information formatted for teams/groups views.

#### Purpose
Transforms `UserPresenceData` into a format suitable for rendering user status in team and group lists.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | number | Yes | User ID |
| `presence` | string | No | User presence status |
| `logicalDirection` | string | No | Call direction |
| `callChannelUUID` | string | No | UUID of the call channel (for listen-in) |
| `availability` | string | No | Availability state name |

#### Example JSON

```json
{
  "id": 67890,
  "presence": "BRIDGED",
  "logicalDirection": "Inbound",
  "callChannelUUID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "availability": "On Call"
}
```

#### Relationships
- Derived from `UserPresenceData`
- Used in team/group member lists

---

### PBXResultItem

PBX/Address book search result item with presence information.

#### Purpose
Enriches PBX search results with real-time presence data from WebSocket updates.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `natterboxId` | number | Yes | Natterbox user ID |
| `presence` | string | No | User presence status |
| `logicalDirection` | string | No | Call direction |
| `callChannelUUID` | string | No | UUID of the call channel |
| `availability` | string | No | Availability state name |

#### Example JSON

```json
{
  "natterboxId": 67890,
  "presence": "ANSWERED",
  "logicalDirection": "Outbound",
  "callChannelUUID": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "availability": "Busy"
}
```

#### Relationships
- Extends `PBXListItem` with presence data
- Updated via `UserPresenceData` events

---

## Presence State Constants

### UserPresenceEnum

Enumeration of user presence states received via WebSocket.

| Constant | Value | Description |
|----------|-------|-------------|
| `USER_PRESENCE_ANSWERED` | `"ANSWERED"` | User has answered a call |
| `USER_PRESENCE_BRIDGED` | `"BRIDGED"` | User's call is bridged/connected |
| `USER_PRESENCE_RINGING` | `"RINGING"` | User's phone is ringing |

#### Usage Example

```javascript
import { UserPresenceEnum } from './constants';

function getPresenceIcon(presence) {
  switch (presence) {
    case UserPresenceEnum.USER_PRESENCE_ANSWERED:
    case UserPresenceEnum.USER_PRESENCE_BRIDGED:
      return 'phone-active';
    case UserPresenceEnum.USER_PRESENCE_RINGING:
      return 'phone-ringing';
    default:
      return 'phone-idle';
  }
}
```

---

## Message Flow Diagrams

### Connection Establishment Flow

```
Client                          WebSocket Server
   │                                   │
   │  WebsocketStartMessage            │
   │  (type: WEBSOCKET_START)          │
   │──────────────────────────────────>│
   │                                   │
   │  WebSocketMessage (type: auth)    │
   │  + WebSocketClientInfo            │
   │──────────────────────────────────>│
   │                                   │
   │  WebSocketMessage (type: tick)    │
   │  message: "welcome"               │
   │<──────────────────────────────────│
   │                                   │
```

### Subscription Flow

```
Client                          WebSocket Server
   │                                   │
   │  WebsocketUserSubscribeMessage    │
   │──────────────────────────────────>│
   │                                   │
   │  WebSocketMessage (type: response)│
   │  + UserPresenceData               │
   │<──────────────────────────────────│
   │                                   │
   │  WebsocketGroupMessage            │
   │  (WEBSOCKET_GROUP_SUBSCRIBE)      │
   │──────────────────────────────────>│
   │                                   │
   │  [Multiple UserPresenceData]      │
   │<──────────────────────────────────│
   │                                   │
```

---

## Common Integration Patterns

### Subscribing to User Presence

```javascript
// Subscribe to own presence on login
function subscribeToOwnPresence(orgId, userId) {
  const message = {
    type: 'WEBSOCKET_USER_SUBSCRIBE',
    orgId: orgId,
    userId: userId
  };
  websocket.send(JSON.stringify(message));
}
```

### Handling Presence Updates

```javascript
function handlePresenceUpdate(data: UserPresenceData) {
  const userDisplay: UserDisplayItem = {
    id: data.userId,
    presence: data.presence,
    logicalDirection: data.logicalDirection,
    callChannelUUID: data.callChannelUUID,
    availability: data.availability
  };
  
  dispatch(updateUserPresence(userDisplay));
}
```

### Managing Group Subscriptions

```javascript
function onGroupChange(newGroupId, oldGroupId, orgId) {
  // Unsubscribe from old group
  if (oldGroupId) {
    websocket.send(JSON.stringify({
      type: 'WEBSOCKET_GROUP_UNSUBSCRIBE',
      orgId: orgId,
      groupId: oldGroupId
    }));
  }
  
  // Subscribe to new group
  websocket.send(JSON.stringify({
    type: 'WEBSOCKET_GROUP_SUBSCRIBE',
    orgId: orgId,
    groupId: newGroupId
  }));
}
```

---

## Related Documentation

- [State Models](./state-models.md) - Redux state structures including WebSocket-related state
- [Auth Models](./auth-models.md) - Authentication models including JWT extraction
- [Call Models](./call-models.md) - Call-related models that interact with presence data