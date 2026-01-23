# WebSocket Endpoints

This document covers the WebSocket connection endpoints for real-time communication in FreedomCTI. These endpoints enable live presence updates for users and user groups within an organization.

## Overview

FreedomCTI uses WebSocket connections to provide real-time updates for:
- **User Presence**: Track individual user availability and status changes
- **Group Presence**: Monitor presence status across user groups

WebSocket connections are maintained through subscription/unsubscription patterns, allowing the CTI client to receive push notifications without polling.

---

## Endpoints

### Subscribe to User Presence

Subscribe to real-time presence updates for a specific user.

```
WEBSOCKET /organisation/{orgId}/user/{userId}
```

**Description**: Establishes a WebSocket subscription to receive real-time presence updates for a specific user within an organization. Use this to track when a user becomes available, busy, on a call, or offline.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orgId` | string | Yes | The unique identifier of the organization |
| `userId` | string | Yes | The unique identifier of the user to subscribe to |

#### Connection Example (JavaScript)

```javascript
// Establish WebSocket connection
const socket = new WebSocket('wss://cti.example.com/organisation/org-12345/user/user-67890');

// Handle connection open
socket.onopen = function(event) {
    console.log('Connected to user presence stream');
    
    // Send subscription message
    socket.send(JSON.stringify({
        action: 'subscribe',
        orgId: 'org-12345',
        userId: 'user-67890'
    }));
};

// Handle incoming messages
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Presence update:', data);
};

// Handle connection close
socket.onclose = function(event) {
    console.log('Disconnected from presence stream');
};

// Handle errors
socket.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

#### Subscription Message Format

```json
{
    "action": "subscribe",
    "orgId": "org-12345",
    "userId": "user-67890"
}
```

#### Presence Update Response

```json
{
    "type": "presence_update",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "data": {
        "userId": "user-67890",
        "orgId": "org-12345",
        "status": "available",
        "previousStatus": "offline",
        "statusMessage": "Ready to take calls",
        "lastActivity": "2024-01-15T10:29:55.000Z",
        "activeCall": null,
        "extension": "1001",
        "capabilities": {
            "canReceiveCalls": true,
            "canMakeOutbound": true,
            "canTransfer": true
        }
    }
}
```

#### Unsubscription Message Format

```json
{
    "action": "unsubscribe",
    "orgId": "org-12345",
    "userId": "user-67890"
}
```

#### Presence Status Values

| Status | Description |
|--------|-------------|
| `available` | User is online and ready to receive calls |
| `busy` | User is occupied but not on a call |
| `on_call` | User is currently on an active call |
| `away` | User is temporarily away |
| `dnd` | User has enabled Do Not Disturb |
| `offline` | User is not connected |

#### Error Messages

| Error Code | Message | Description |
|------------|---------|-------------|
| `4001` | `INVALID_ORG_ID` | The specified organization ID is invalid or not found |
| `4002` | `INVALID_USER_ID` | The specified user ID is invalid or not found |
| `4003` | `UNAUTHORIZED` | Authentication failed or insufficient permissions |
| `4004` | `SUBSCRIPTION_FAILED` | Failed to establish subscription |
| `4008` | `CONNECTION_LIMIT_EXCEEDED` | Maximum concurrent connections exceeded |
| `1011` | `SERVER_ERROR` | Internal server error occurred |

---

### Subscribe to User Group Presence

Subscribe to real-time presence updates for all users in a specific group.

```
WEBSOCKET /organisation/{orgId}/user-group/{groupId}
```

**Description**: Establishes a WebSocket subscription to receive aggregated real-time presence updates for all users within a specific group. Useful for supervisor dashboards and queue management.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orgId` | string | Yes | The unique identifier of the organization |
| `groupId` | string | Yes | The unique identifier of the user group to subscribe to |

#### Connection Example (JavaScript)

```javascript
// Establish WebSocket connection for group
const socket = new WebSocket('wss://cti.example.com/organisation/org-12345/user-group/group-sales-team');

// Handle connection open
socket.onopen = function(event) {
    console.log('Connected to group presence stream');
    
    // Send subscription message
    socket.send(JSON.stringify({
        action: 'subscribe',
        orgId: 'org-12345',
        groupId: 'group-sales-team'
    }));
};

// Handle incoming messages
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'group_presence_update') {
        updateGroupDashboard(data.data);
    } else if (data.type === 'member_presence_update') {
        updateMemberStatus(data.data);
    }
};

// Unsubscribe before closing
function disconnect() {
    socket.send(JSON.stringify({
        action: 'unsubscribe',
        orgId: 'org-12345',
        groupId: 'group-sales-team'
    }));
    socket.close();
}
```

#### Subscription Message Format

```json
{
    "action": "subscribe",
    "orgId": "org-12345",
    "groupId": "group-sales-team"
}
```

#### Group Presence Update Response

```json
{
    "type": "group_presence_update",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "data": {
        "groupId": "group-sales-team",
        "groupName": "Sales Team",
        "orgId": "org-12345",
        "summary": {
            "totalMembers": 12,
            "available": 5,
            "busy": 2,
            "onCall": 3,
            "away": 1,
            "offline": 1
        },
        "members": [
            {
                "userId": "user-001",
                "displayName": "John Smith",
                "status": "available",
                "extension": "1001"
            },
            {
                "userId": "user-002",
                "displayName": "Jane Doe",
                "status": "on_call",
                "extension": "1002",
                "callDuration": 145
            }
        ],
        "queueMetrics": {
            "callsWaiting": 3,
            "averageWaitTime": 45,
            "longestWaitTime": 120
        }
    }
}
```

#### Individual Member Update Response

When a single member's status changes, you receive a targeted update:

```json
{
    "type": "member_presence_update",
    "timestamp": "2024-01-15T10:31:15.000Z",
    "data": {
        "groupId": "group-sales-team",
        "userId": "user-002",
        "displayName": "Jane Doe",
        "status": "available",
        "previousStatus": "on_call",
        "extension": "1002",
        "updatedSummary": {
            "totalMembers": 12,
            "available": 6,
            "busy": 2,
            "onCall": 2,
            "away": 1,
            "offline": 1
        }
    }
}
```

#### Unsubscription Message Format

```json
{
    "action": "unsubscribe",
    "orgId": "org-12345",
    "groupId": "group-sales-team"
}
```

#### Error Messages

| Error Code | Message | Description |
|------------|---------|-------------|
| `4001` | `INVALID_ORG_ID` | The specified organization ID is invalid or not found |
| `4005` | `INVALID_GROUP_ID` | The specified group ID is invalid or not found |
| `4003` | `UNAUTHORIZED` | Authentication failed or insufficient permissions |
| `4006` | `GROUP_ACCESS_DENIED` | User does not have permission to view this group |
| `4004` | `SUBSCRIPTION_FAILED` | Failed to establish subscription |
| `4008` | `CONNECTION_LIMIT_EXCEEDED` | Maximum concurrent connections exceeded |
| `1011` | `SERVER_ERROR` | Internal server error occurred |

---

## Connection Management

### Heartbeat/Keep-Alive

To maintain the WebSocket connection, implement a heartbeat mechanism:

```javascript
// Send ping every 30 seconds
const heartbeatInterval = setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);

// Handle pong response
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'pong') {
        console.log('Heartbeat acknowledged');
        return;
    }
    // Handle other messages...
};
```

### Reconnection Strategy

Implement exponential backoff for reconnection attempts:

```javascript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connect() {
    const socket = new WebSocket('wss://cti.example.com/organisation/org-12345/user/user-67890');
    
    socket.onclose = function(event) {
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            reconnectAttempts++;
            console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
            setTimeout(connect, delay);
        }
    };
    
    socket.onopen = function(event) {
        reconnectAttempts = 0; // Reset on successful connection
    };
}
```

---

## Related Documentation

- [Call Logs API](call-logs-api.md) - REST endpoints for retrieving call history
- [Salesforce API](salesforce-api.md) - Salesforce query endpoints for call reporting
- [API Overview](README.md) - General API information and authentication