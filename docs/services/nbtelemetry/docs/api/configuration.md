# Configuration API

This document covers endpoints for managing dial plans, SIP devices, and availability profiles within an organisation.

## Overview

The Configuration API provides access to:
- **Dial Plan Policies**: Rules governing call routing and dialing behavior
- **SIP Devices**: Voice over IP device management and configuration
- **Availability Profiles**: User presence states and availability settings

---

## Endpoints

### Get Dial Plan Policies

Retrieve dial plan policies configured for an organisation. Dial plans define rules for call routing, number formatting, and dialing restrictions.

```
GET /v1/organisation/{orgid}/dial-plan/policy
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-123456/dial-plan/policy" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "id": "policy-001",
        "name": "Default Outbound Policy",
        "description": "Standard outbound dialing rules for UK numbers",
        "enabled": true,
        "priority": 1,
        "rules": [
          {
            "pattern": "^0[1-9][0-9]{9}$",
            "action": "allow",
            "transform": "+44{number:1}"
          },
          {
            "pattern": "^00[0-9]+$",
            "action": "allow",
            "description": "International calls"
          }
        ],
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-02-20T14:45:00Z"
      },
      {
        "id": "policy-002",
        "name": "Emergency Services",
        "description": "Emergency number routing",
        "enabled": true,
        "priority": 0,
        "rules": [
          {
            "pattern": "^999$|^112$",
            "action": "allow",
            "route": "emergency"
          }
        ],
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z"
      }
    ],
    "totalCount": 2
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `401` | `Unauthorized` | Invalid or expired access token |
| `403` | `Forbidden` | User lacks permission to view dial plan policies |
| `404` | `NotFound` | Organisation not found |
| `500` | `InternalServerError` | Server error while retrieving policies |

---

### Get SIP Devices

Retrieve all SIP devices registered to an organisation. SIP devices include desk phones, softphones, and other VoIP endpoints.

```
GET /v1/organisation/{orgid}/sip-device
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-123456/sip-device" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "id": "sip-dev-001",
        "name": "Reception Desk Phone",
        "type": "hardware",
        "manufacturer": "Polycom",
        "model": "VVX 450",
        "macAddress": "00:04:f2:12:34:56",
        "sipUsername": "reception@org-123456.sip.natterbox.com",
        "extension": "1001",
        "status": "registered",
        "ipAddress": "192.168.1.101",
        "assignedUser": {
          "id": "user-789",
          "name": "Jane Smith"
        },
        "lastRegistration": "2024-03-15T09:23:45Z",
        "createdAt": "2024-01-10T08:00:00Z"
      },
      {
        "id": "sip-dev-002",
        "name": "Sales Softphone",
        "type": "softphone",
        "manufacturer": "Natterbox",
        "model": "WebRTC Client",
        "sipUsername": "sales-01@org-123456.sip.natterbox.com",
        "extension": "1002",
        "status": "unregistered",
        "assignedUser": {
          "id": "user-456",
          "name": "John Doe"
        },
        "lastRegistration": "2024-03-14T17:30:00Z",
        "createdAt": "2024-02-01T12:00:00Z"
      }
    ],
    "totalCount": 2
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `401` | `Unauthorized` | Invalid or expired access token |
| `403` | `Forbidden` | User lacks permission to view SIP devices |
| `404` | `NotFound` | Organisation not found |
| `500` | `InternalServerError` | Server error while retrieving devices |

---

### Get Availability Profiles

Retrieve all availability profiles defined for an organisation. Availability profiles define the possible presence states users can set (e.g., Available, Busy, Away).

```
GET /v1/organisation/{orgid}/availability/profile
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-123456/availability/profile" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "profiles": [
      {
        "id": "profile-001",
        "name": "Standard Agent Profile",
        "description": "Default availability profile for call center agents",
        "isDefault": true,
        "states": [
          {
            "id": "state-001",
            "name": "Available",
            "category": "available",
            "color": "#22c55e",
            "allowInboundCalls": true,
            "allowOutboundCalls": true
          },
          {
            "id": "state-002",
            "name": "On a Call",
            "category": "busy",
            "color": "#ef4444",
            "allowInboundCalls": false,
            "allowOutboundCalls": false,
            "systemManaged": true
          },
          {
            "id": "state-003",
            "name": "Break",
            "category": "away",
            "color": "#f59e0b",
            "allowInboundCalls": false,
            "allowOutboundCalls": true,
            "maxDuration": 900
          }
        ],
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-02-15T11:20:00Z"
      },
      {
        "id": "profile-002",
        "name": "Manager Profile",
        "description": "Availability profile for team managers",
        "isDefault": false,
        "states": [
          {
            "id": "state-010",
            "name": "Available",
            "category": "available",
            "color": "#22c55e",
            "allowInboundCalls": true,
            "allowOutboundCalls": true
          },
          {
            "id": "state-011",
            "name": "In Meeting",
            "category": "busy",
            "color": "#8b5cf6",
            "allowInboundCalls": false,
            "allowOutboundCalls": false
          }
        ],
        "createdAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-15T10:00:00Z"
      }
    ],
    "totalCount": 2
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `401` | `Unauthorized` | Invalid or expired access token |
| `403` | `Forbidden` | User lacks permission to view availability profiles |
| `404` | `NotFound` | Organisation not found |
| `500` | `InternalServerError` | Server error while retrieving profiles |

---

### Get Availability Profile States

Retrieve the detailed states for a specific availability profile.

```
GET /v1/organisation/{orgid}/availability/profile/{profileId}/state
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `profileId` | string | path | Yes | The unique identifier of the availability profile |

#### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-123456/availability/profile/profile-001/state" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "profileId": "profile-001",
    "profileName": "Standard Agent Profile",
    "states": [
      {
        "id": "state-001",
        "name": "Available",
        "description": "Ready to receive calls",
        "category": "available",
        "color": "#22c55e",
        "icon": "phone",
        "allowInboundCalls": true,
        "allowOutboundCalls": true,
        "autoTransition": null,
        "order": 1
      },
      {
        "id": "state-002",
        "name": "On a Call",
        "description": "Currently handling a call",
        "category": "busy",
        "color": "#ef4444",
        "icon": "phone-call",
        "allowInboundCalls": false,
        "allowOutboundCalls": false,
        "systemManaged": true,
        "order": 2
      },
      {
        "id": "state-003",
        "name": "Break",
        "description": "On scheduled break",
        "category": "away",
        "color": "#f59e0b",
        "icon": "coffee",
        "allowInboundCalls": false,
        "allowOutboundCalls": true,
        "maxDuration": 900,
        "autoTransition": {
          "targetStateId": "state-001",
          "afterSeconds": 900
        },
        "order": 3
      },
      {
        "id": "state-004",
        "name": "Wrap-up",
        "description": "Post-call processing",
        "category": "busy",
        "color": "#3b82f6",
        "icon": "edit",
        "allowInboundCalls": false,
        "allowOutboundCalls": false,
        "maxDuration": 300,
        "autoTransition": {
          "targetStateId": "state-001",
          "afterSeconds": 300
        },
        "order": 4
      },
      {
        "id": "state-005",
        "name": "Training",
        "description": "In training session",
        "category": "away",
        "color": "#8b5cf6",
        "icon": "book-open",
        "allowInboundCalls": false,
        "allowOutboundCalls": false,
        "requiresReason": true,
        "order": 5
      }
    ],
    "totalCount": 5
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| `401` | `Unauthorized` | Invalid or expired access token |
| `403` | `Forbidden` | User lacks permission to view profile states |
| `404` | `NotFound` | Organisation or profile not found |
| `500` | `InternalServerError` | Server error while retrieving states |

---

## Related Documentation

- [Users and Organisations API](users-and-organizations.md) - Managing users, including updating user availability states
- [Authentication API](authentication.md) - Obtaining access tokens for API requests
- [API Overview](README.md) - General API information and conventions