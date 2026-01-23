# Telephony Resources API

This document covers the telephony resource management endpoints in the Platform API, including SIP trunks, gateways, devices, phones, routes, and VoIP resource management.

## Overview

The Telephony Resources API provides comprehensive management of VoIP infrastructure components:

- **SIP Trunks**: Configure and manage SIP trunk connections for voice traffic
- **SIP Trunk IPs**: Manage IP address configurations for SIP trunks
- **Devices**: Provision and control VoIP phones and endpoints
- **SIP Gateway Monitoring**: Monitor gateway health and connectivity
- **Domains**: Manage SIP domain mappings

## Base URL

All endpoints are relative to: `https://api.platform.example.com`

---

## SIP Trunks

SIP trunks are the primary connections for voice traffic between the platform and external carriers or PBX systems.

### Get SIP Trunk

Retrieves a SIP trunk configuration by ID.

```
GET /siptrunk/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | SIP trunk ID |
| `include` | string | query | No | Additional data to include (e.g., `ips`, `routes`) |
| `format` | string | query | No | Response format (`json`, `xml`) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/siptrunk/trunk_12345?include=ips" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "trunk_12345",
    "name": "Primary Carrier Trunk",
    "organization_id": "org_98765",
    "status": "active",
    "type": "carrier",
    "protocol": "sip",
    "transport": "udp",
    "host": "sip.carrier.example.com",
    "port": 5060,
    "username": "trunk_user",
    "realm": "carrier.example.com",
    "register": true,
    "max_channels": 100,
    "codecs": ["G.711", "G.729", "OPUS"],
    "dtmf_mode": "rfc2833",
    "nat_support": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:22:00Z",
    "ips": [
      {
        "id": "ip_001",
        "address": "203.0.113.10",
        "type": "signaling"
      },
      {
        "id": "ip_002",
        "address": "203.0.113.11",
        "type": "media"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid trunk ID format |
| 401 | Authentication required |
| 403 | Insufficient permissions to view trunk |
| 404 | SIP trunk not found |

---

### Create SIP Trunk

Creates a new SIP trunk or updates an existing one.

```
PUT /siptrunk/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity type or trunk identifier |
| `name` | string | body | Yes | Trunk display name |
| `organization_id` | string | body | Yes | Organization ID |
| `type` | string | body | Yes | Trunk type: `carrier`, `pbx`, `peer` |
| `host` | string | body | Yes | SIP server hostname or IP |
| `port` | integer | body | No | SIP port (default: 5060) |
| `transport` | string | body | No | Transport protocol: `udp`, `tcp`, `tls` |
| `username` | string | body | No | Authentication username |
| `password` | string | body | No | Authentication password |
| `realm` | string | body | No | Authentication realm |
| `register` | boolean | body | No | Whether to register with remote server |
| `max_channels` | integer | body | No | Maximum concurrent channels |
| `codecs` | array | body | No | Allowed audio codecs |
| `dtmf_mode` | string | body | No | DTMF mode: `rfc2833`, `inband`, `info` |
| `nat_support` | boolean | body | No | Enable NAT traversal support |
| `caller_id_name` | string | body | No | Default caller ID name |
| `caller_id_number` | string | body | No | Default caller ID number |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/siptrunk/new" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Secondary Carrier Trunk",
    "organization_id": "org_98765",
    "type": "carrier",
    "host": "sip2.carrier.example.com",
    "port": 5060,
    "transport": "udp",
    "username": "secondary_trunk",
    "password": "secure_password_123",
    "realm": "carrier.example.com",
    "register": true,
    "max_channels": 50,
    "codecs": ["G.711", "G.729"],
    "dtmf_mode": "rfc2833",
    "nat_support": true,
    "caller_id_name": "Company Name",
    "caller_id_number": "+15551234567"
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "trunk_12346",
    "name": "Secondary Carrier Trunk",
    "organization_id": "org_98765",
    "status": "pending",
    "type": "carrier",
    "host": "sip2.carrier.example.com",
    "port": 5060,
    "transport": "udp",
    "username": "secondary_trunk",
    "realm": "carrier.example.com",
    "register": true,
    "max_channels": 50,
    "codecs": ["G.711", "G.729"],
    "dtmf_mode": "rfc2833",
    "nat_support": true,
    "caller_id_name": "Company Name",
    "caller_id_number": "+15551234567",
    "created_at": "2024-01-22T09:15:00Z",
    "updated_at": "2024-01-22T09:15:00Z"
  },
  "message": "SIP trunk created successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions to create trunk |
| 409 | Trunk with same name already exists |
| 422 | Validation error (e.g., invalid host) |

---

### Update SIP Trunk

Updates an existing SIP trunk configuration.

```
POST /siptrunk/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | SIP trunk ID to update |
| `name` | string | body | No | Updated trunk name |
| `status` | string | body | No | Trunk status: `active`, `inactive`, `suspended` |
| `host` | string | body | No | Updated SIP host |
| `port` | integer | body | No | Updated SIP port |
| `transport` | string | body | No | Updated transport protocol |
| `username` | string | body | No | Updated authentication username |
| `password` | string | body | No | Updated authentication password |
| `max_channels` | integer | body | No | Updated channel limit |
| `codecs` | array | body | No | Updated codec list |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/siptrunk/trunk_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Primary Carrier Trunk - Updated",
    "max_channels": 150,
    "codecs": ["G.711", "G.729", "OPUS", "G.722"]
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "trunk_12345",
    "name": "Primary Carrier Trunk - Updated",
    "organization_id": "org_98765",
    "status": "active",
    "max_channels": 150,
    "codecs": ["G.711", "G.729", "OPUS", "G.722"],
    "updated_at": "2024-01-22T10:30:00Z"
  },
  "message": "SIP trunk updated successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions to update trunk |
| 404 | SIP trunk not found |
| 422 | Validation error |

---

### Delete SIP Trunk

Deletes a SIP trunk by ID.

```
DELETE /siptrunk/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | SIP trunk ID to delete |
| `force` | boolean | query | No | Force deletion even if active calls exist |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/siptrunk/trunk_12346?force=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "message": "SIP trunk deleted successfully",
  "data": {
    "id": "trunk_12346",
    "deleted_at": "2024-01-22T11:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid trunk ID |
| 401 | Authentication required |
| 403 | Insufficient permissions to delete trunk |
| 404 | SIP trunk not found |
| 409 | Trunk has active calls (use force=true to override) |

---

## SIP Trunk IPs

Manage IP addresses associated with SIP trunks for signaling and media traffic.

### Get SIP Trunk IPs

Retrieves IP addresses configured for a SIP trunk.

```
GET /siptrunkips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | SIP trunk ID or `all` for all IPs |
| `type` | string | query | No | Filter by IP type: `signaling`, `media`, `both` |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/siptrunkips/trunk_12345?type=signaling" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "trunk_id": "trunk_12345",
    "ips": [
      {
        "id": "ip_001",
        "address": "203.0.113.10",
        "type": "signaling",
        "port": 5060,
        "priority": 1,
        "active": true,
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": "ip_003",
        "address": "203.0.113.12",
        "type": "signaling",
        "port": 5060,
        "priority": 2,
        "active": true,
        "created_at": "2024-01-16T08:00:00Z"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid entity parameter |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | SIP trunk not found |

---

### Create/Update SIP Trunk IPs

Creates or updates IP addresses for a SIP trunk.

```
PUT /siptrunkips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | SIP trunk ID |
| `ips` | array | body | Yes | Array of IP configurations |
| `ips[].address` | string | body | Yes | IP address |
| `ips[].type` | string | body | Yes | IP type: `signaling`, `media`, `both` |
| `ips[].port` | integer | body | No | Port number (default varies by type) |
| `ips[].priority` | integer | body | No | Routing priority (lower = higher priority) |
| `ips[].active` | boolean | body | No | Whether IP is active (default: true) |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/siptrunkips/trunk_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ips": [
      {
        "address": "203.0.113.20",
        "type": "signaling",
        "port": 5060,
        "priority": 1,
        "active": true
      },
      {
        "address": "203.0.113.21",
        "type": "media",
        "port": 10000,
        "priority": 1,
        "active": true
      }
    ]
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "trunk_id": "trunk_12345",
    "ips": [
      {
        "id": "ip_004",
        "address": "203.0.113.20",
        "type": "signaling",
        "port": 5060,
        "priority": 1,
        "active": true,
        "created_at": "2024-01-22T12:00:00Z"
      },
      {
        "id": "ip_005",
        "address": "203.0.113.21",
        "type": "media",
        "port": 10000,
        "priority": 1,
        "active": true,
        "created_at": "2024-01-22T12:00:00Z"
      }
    ]
  },
  "message": "SIP trunk IPs configured successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid IP address format |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | SIP trunk not found |
| 409 | IP address already in use |
| 422 | Validation error |

---

### Update SIP Trunk IPs

Updates existing IP configurations for a SIP trunk.

```
POST /siptrunkips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | SIP trunk ID |
| `ip_id` | string | body | Yes | ID of IP to update |
| `address` | string | body | No | New IP address |
| `type` | string | body | No | Updated IP type |
| `port` | integer | body | No | Updated port |
| `priority` | integer | body | No | Updated priority |
| `active` | boolean | body | No | Enable/disable IP |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/siptrunkips/trunk_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ip_id": "ip_004",
    "priority": 2,
    "active": false
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "ip_004",
    "address": "203.0.113.20",
    "type": "signaling",
    "port": 5060,
    "priority": 2,
    "active": false,
    "updated_at": "2024-01-22T13:00:00Z"
  },
  "message": "SIP trunk IP updated successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | IP configuration not found |

---

### Delete SIP Trunk IPs

Removes IP addresses from a SIP trunk.

```
DELETE /siptrunkips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | SIP trunk ID |
| `ip_id` | string | query | Yes | ID of IP to delete |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/siptrunkips/trunk_12345?ip_id=ip_004" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "message": "SIP trunk IP deleted successfully",
  "data": {
    "id": "ip_004",
    "deleted_at": "2024-01-22T14:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Missing ip_id parameter |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | IP configuration not found |

---

## Devices

Manage VoIP phones, softphones, and other SIP endpoints.

### Get Device by ID

Retrieves device information by device ID.

```
GET /devices/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | Device ID |
| `include` | string | query | No | Additional data: `lines`, `settings`, `status` |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/devices/dev_12345?include=lines,status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dev_12345",
    "mac_address": "00:1A:2B:3C:4D:5E",
    "organization_id": "org_98765",
    "user_id": "user_54321",
    "name": "John's Desk Phone",
    "model": "Polycom VVX 450",
    "manufacturer": "Polycom",
    "firmware_version": "6.4.0.12345",
    "status": "online",
    "ip_address": "192.168.1.100",
    "provisioning_status": "provisioned",
    "last_seen": "2024-01-22T14:30:00Z",
    "created_at": "2024-01-10T08:00:00Z",
    "lines": [
      {
        "line_number": 1,
        "extension": "1001",
        "label": "John Doe",
        "type": "primary",
        "registered": true
      },
      {
        "line_number": 2,
        "extension": "1050",
        "label": "Sales Queue",
        "type": "shared",
        "registered": true
      }
    ],
    "status_details": {
      "registration_state": "registered",
      "last_registration": "2024-01-22T14:25:00Z",
      "network_quality": "excellent",
      "uptime_seconds": 432000
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid device ID format |
| 401 | Authentication required |
| 403 | Insufficient permissions to view device |
| 404 | Device not found |

---

### Get Device by MAC Address

Retrieves device information by MAC address.

```
GET /devices/mac/:macAddress
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `macAddress` | string | path | Yes | Device MAC address (formats: `001A2B3C4D5E` or `00:1A:2B:3C:4D:5E`) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/devices/mac/00:1A:2B:3C:4D:5E" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dev_12345",
    "mac_address": "00:1A:2B:3C:4D:5E",
    "organization_id": "org_98765",
    "user_id": "user_54321",
    "name": "John's Desk Phone",
    "model": "Polycom VVX 450",
    "manufacturer": "Polycom",
    "status": "online",
    "provisioning_status": "provisioned"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid MAC address format |
| 401 | Authentication required |
| 404 | Device not found |

---

### Create Device

Creates a new device in the system.

```
PUT /devices/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity type (e.g., `phone`, `softphone`, `ata`) |
| `mac_address` | string | body | Yes | Device MAC address |
| `organization_id` | string | body | Yes | Organization ID |
| `user_id` | string | body | No | User ID to assign device to |
| `name` | string | body | No | Device display name |
| `model` | string | body | No | Device model identifier |
| `manufacturer` | string | body | No | Device manufacturer |
| `template_id` | string | body | No | Provisioning template ID |
| `lines` | array | body | No | Line configuration array |
| `lines[].line_number` | integer | body | No | Line number (1-based) |
| `lines[].extension` | string | body | No | Extension number |
| `lines[].label` | string | body | No | Line label |
| `lines[].type` | string | body | No | Line type: `primary`, `shared`, `blf` |
| `settings` | object | body | No | Device-specific settings |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/devices/phone" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "00:1A:2B:3C:4D:5F",
    "organization_id": "org_98765",
    "user_id": "user_54322",
    "name": "Jane'\''s Desk Phone",
    "model": "yealink_t46u",
    "manufacturer": "Yealink",
    "template_id": "tmpl_standard",
    "lines": [
      {
        "line_number": 1,
        "extension": "1002",
        "label": "Jane Smith",
        "type": "primary"
      }
    ],
    "settings": {
      "timezone": "America/New_York",
      "language": "en",
      "ringtone": "default"
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dev_12346",
    "mac_address": "00:1A:2B:3C:4D:5F",
    "organization_id": "org_98765",
    "user_id": "user_54322",
    "name": "Jane's Desk Phone",
    "model": "yealink_t46u",
    "manufacturer": "Yealink",
    "status": "offline",
    "provisioning_status": "pending",
    "provisioning_url": "https://provision.example.com/dev_12346",
    "created_at": "2024-01-22T15:00:00Z",
    "lines": [
      {
        "line_number": 1,
        "extension": "1002",
        "label": "Jane Smith",
        "type": "primary",
        "registered": false
      }
    ]
  },
  "message": "Device created successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 409 | Device with MAC address already exists |
| 422 | Validation error (e.g., invalid MAC format) |

---

### Update Device

Updates an existing device configuration.

```
POST /devices/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Device ID to update |
| `name` | string | body | No | Updated device name |
| `user_id` | string | body | No | New user assignment |
| `template_id` | string | body | No | New provisioning template |
| `lines` | array | body | No | Updated line configurations |
| `settings` | object | body | No | Updated device settings |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/devices/dev_12346" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane'\''s Conference Phone",
    "lines": [
      {
        "line_number": 1,
        "extension": "1002",
        "label": "Jane Smith",
        "type": "primary"
      },
      {
        "line_number": 2,
        "extension": "1100",
        "label": "Conference",
        "type": "shared"
      }
    ]
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dev_12346",
    "name": "Jane's Conference Phone",
    "provisioning_status": "needs_update",
    "updated_at": "2024-01-22T16:00:00Z",
    "lines": [
      {
        "line_number": 1,
        "extension": "1002",
        "label": "Jane Smith",
        "type": "primary"
      },
      {
        "line_number": 2,
        "extension": "1100",
        "label": "Conference",
        "type": "shared"
      }
    ]
  },
  "message": "Device updated successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Device not found |
| 422 | Validation error |

---

### Delete Device

Removes a device from the system.

```
DELETE /devices/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Device ID to delete |
| `keep_config` | boolean | query | No | Preserve provisioning config (default: false) |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/devices/dev_12346" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "message": "Device deleted successfully",
  "data": {
    "id": "dev_12346",
    "deleted_at": "2024-01-22T17:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid device ID |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Device not found |

---

### Reboot Device

Remotely reboots a device.

```
PUT /devices/reboot/:deviceId
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `deviceId` | string | path | Yes | Device ID to reboot |
| `delay` | integer | body | No | Delay in seconds before reboot (default: 0) |
| `force` | boolean | body | No | Force reboot even during active call |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/devices/reboot/dev_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "delay": 60,
    "force": false
  }'
```

#### Response Example

```json
{
  "success": true,
  "message": "Reboot command sent successfully",
  "data": {
    "device_id": "dev_12345",
    "reboot_scheduled": true,
    "scheduled_time": "2024-01-22T17:01:00Z",
    "delay_seconds": 60
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid device ID |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Device not found |
| 409 | Device has active call (use force=true) |
| 503 | Device unreachable |

---

### Send SIP NOTIFY to Device

Sends a SIP NOTIFY message to a device for various purposes (check-sync, reboot, etc.).

```
POST /devices/sipnotify/:deviceId
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `deviceId` | string | path | Yes | Device ID |
| `event` | string | body | Yes | SIP event type: `check-sync`, `reboot`, `talk`, `hold` |
| `content_type` | string | body | No | Content-Type header value |
| `body` | string | body | No | NOTIFY body content |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/devices/sipnotify/dev_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "check-sync",
    "content_type": "application/simple-message-summary",
    "body": "Messages-Waiting: yes\r\nVoice-Message: 2/0 (0/0)"
  }'
```

#### Response Example

```json
{
  "success": true,
  "message": "SIP NOTIFY sent successfully",
  "data": {
    "device_id": "dev_12345",
    "event": "check-sync",
    "sent_at": "2024-01-22T17:30:00Z",
    "response_code": 200
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid event type or parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Device not found |
| 408 | SIP NOTIFY timed out |
| 503 | Device unreachable |

---

## SIP Gateway Monitoring

Monitor the health and connectivity of SIP gateways.

### Get SIP Gateway Ping Status

Retrieves the current ping/health status of SIP gateways.

```
GET /sipgwping/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Gateway ID or `all` for all gateways |
| `include_history` | boolean | query | No | Include historical ping data |
| `history_hours` | integer | query | No | Hours of history to include (default: 24) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/sipgwping/gw_12345?include_history=true&history_hours=12" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "gateway_id": "gw_12345",
    "name": "Primary SIP Gateway",
    "host": "sip.gateway.example.com",
    "status": "healthy",
    "last_ping": "2024-01-22T17:45:00Z",
    "response_time_ms": 45,
    "packet_loss_percent": 0.0,
    "uptime_percent_24h": 99.98,
    "history": [
      {
        "timestamp": "2024-01-22T17:00:00Z",
        "status": "healthy",
        "response_time_ms": 42
      },
      {
        "timestamp": "2024-01-22T16:00:00Z",
        "status": "healthy",
        "response_time_ms": 48
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid entity parameter |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Gateway not found |

---

### Update SIP Gateway Ping Status

Updates or records ping status for a SIP gateway.

```
POST /sipgwping/:entity/:param1/:param2
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Gateway ID |
| `param1` | string | path | Yes | Status or action type |
| `param2` | string | path | Yes | Additional parameter (e.g., timestamp) |
| `status` | string | body | No | Gateway status: `healthy`, `degraded`, `down` |
| `response_time_ms` | integer | body | No | Response time in milliseconds |
| `packet_loss_percent` | float | body | No | Packet loss percentage |
| `error_message` | string | body | No | Error message if gateway is down |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/sipgwping/gw_12345/status/update" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "degraded",
    "response_time_ms": 250,
    "packet_loss_percent": 5.2,
    "error_message": "High latency detected"
  }'
```

#### Response Example

```json
{
  "success": true,
  "message": "Gateway status updated",
  "data": {
    "gateway_id": "gw_12345",
    "status": "degraded",
    "updated_at": "2024-01-22T18:00:00Z",
    "alert_generated": true
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid status or parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Gateway not found |

---

## Domains

Manage SIP domain mappings for the platform.

### Get All Domains

Retrieves all domain mappings.

```
GET /domains
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `organization_id` | string | query | No | Filter by organization |
| `status` | string | query | No | Filter by status: `active`, `inactive`, `pending` |
| `page` | integer | query | No | Page number (default: 1) |
| `per_page` | integer | query | No | Results per page (default: 50) |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/domains?status=active&per_page=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "domains": [
      {
        "id": "dom_001",
        "domain": "sip.company1.example.com",
        "organization_id": "org_98765",
        "status": "active",
        "type": "primary",
        "ssl_enabled": true,
        "created_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": "dom_002",
        "domain": "pbx.company2.example.com",
        "organization_id": "org_98766",
        "status": "active",
        "type": "primary",
        "ssl_enabled": true,
        "created_at": "2024-01-05T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 45,
      "total_pages": 3
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Authentication required |
| 403 | Insufficient permissions |

---

### Get Domain by ID

Retrieves a specific domain mapping.

```
GET /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | Domain ID |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/domains/dom_001" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dom_001",
    "domain": "sip.company1.example.com",
    "organization_id": "org_98765",
    "status": "active",
    "type": "primary",
    "ssl_enabled": true,
    "ssl_certificate_expiry": "2025-01-01T00:00:00Z",
    "dns_records": {
      "a_record": "203.0.113.50",
      "srv_record": "_sip._udp.sip.company1.example.com"
    },
    "settings": {
      "default_transport": "tls",
      "nat_keepalive": true
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid domain ID |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Domain not found |

---

### Create/Update Domain

Creates a new domain mapping or updates an existing one.

```
PUT /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | Domain ID (use `new` for creation) |
| `domain` | string | body | Yes | Domain name |
| `organization_id` | string | body | Yes | Organization ID |
| `type` | string | body | No | Domain type: `primary`, `alias` |
| `ssl_enabled` | boolean | body | No | Enable SSL/TLS |
| `settings` | object | body | No | Domain-specific settings |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/domains/new" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "voice.newcompany.example.com",
    "organization_id": "org_98767",
    "type": "primary",
    "ssl_enabled": true,
    "settings": {
      "default_transport": "tls",
      "nat_keepalive": true
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dom_003",
    "domain": "voice.newcompany.example.com",
    "organization_id": "org_98767",
    "status": "pending",
    "type": "primary",
    "ssl_enabled": true,
    "dns_verification_record": "voiceplatform-verify=abc123xyz",
    "created_at": "2024-01-22T19:00:00Z"
  },
  "message": "Domain created successfully. Please add DNS verification record."
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid domain format |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 409 | Domain already exists |
| 422 | Validation error |

---

### Update Domain

Updates an existing domain mapping.

```
POST /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | Domain ID |
| `status` | string | body | No | Domain status |
| `ssl_enabled` | boolean | body | No | Enable/disable SSL |
| `settings` | object | body | No | Updated settings |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/domains/dom_003" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "settings": {
      "default_transport": "udp",
      "nat_keepalive": false
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dom_003",
    "domain": "voice.newcompany.example.com",
    "status": "active",
    "settings": {
      "default_transport": "udp",
      "nat_keepalive": false
    },
    "updated_at": "2024-01-22T20:00:00Z"
  },
  "message": "Domain updated successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Domain not found |

---

### Delete Domain

Removes a domain mapping.

```
DELETE /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | Domain ID to delete |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/domains/dom_003" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "message": "Domain deleted successfully",
  "data": {
    "id": "dom_003",
    "deleted_at": "2024-01-22T21:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid domain ID |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Domain not found |
| 409 | Domain has active resources (trunks, devices) |

---

## Organization IPs

Manage IP addresses associated with organizations for SIP traffic.

### Get All Organization IPs

Retrieves all IP addresses for organizations.

```
GET /orgips/index
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `organization_id` | string | query | No | Filter by organization |
| `type` | string | query | No | Filter by type: `whitelist`, `blacklist` |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/orgips/index?organization_id=org_98765" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "ips": [
      {
        "id": "orgip_001",
        "organization_id": "org_98765",
        "ip_address": "203.0.113.100",
        "cidr": 32,
        "type": "whitelist",
        "description": "Office main IP",
        "created_at": "2024-01-10T00:00:00Z"
      },
      {
        "id": "orgip_002",
        "organization_id": "org_98765",
        "ip_address": "203.0.113.0",
        "cidr": 24,
        "type": "whitelist",
        "description": "Office subnet",
        "created_at": "2024-01-11T00:00:00Z"
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Authentication required |
| 403 | Insufficient permissions |

---

### Get Organization IP

Retrieves a specific organization IP by ID.

```
GET /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Organization IP ID |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/orgips/orgip_001" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "orgip_001",
    "organization_id": "org_98765",
    "ip_address": "203.0.113.100",
    "cidr": 32,
    "type": "whitelist",
    "description": "Office main IP",
    "last_seen": "2024-01-22T15:00:00Z",
    "request_count_24h": 1523,
    "created_at": "2024-01-10T00:00:00Z",
    "updated_at": "2024-01-20T10:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid ID format |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Organization IP not found |

---

### Create Organization IP

Creates a new organization IP entry.

```
PUT /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity type or `new` |
| `organization_id` | string | body | Yes | Organization ID |
| `ip_address` | string | body | Yes | IP address |
| `cidr` | integer | body | No | CIDR notation (default: 32) |
| `type` | string | body | No | Type: `whitelist`, `blacklist` (default: whitelist) |
| `description` | string | body | No | Description of the IP |

#### Request Example

```bash
curl -X PUT "https://api.platform.example.com/orgips/new" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org_98765",
    "ip_address": "198.51.100.0",
    "cidr": 24,
    "type": "whitelist",
    "description": "Remote office subnet"
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "orgip_003",
    "organization_id": "org_98765",
    "ip_address": "198.51.100.0",
    "cidr": 24,
    "type": "whitelist",
    "description": "Remote office subnet",
    "created_at": "2024-01-22T22:00:00Z"
  },
  "message": "Organization IP created successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid IP address format |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 409 | IP address already exists for organization |
| 422 | Validation error |

---

### Update Organization IP

Updates an existing organization IP.

```
POST /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Organization IP ID |
| `type` | string | body | No | Updated type |
| `description` | string | body | No | Updated description |
| `cidr` | integer | body | No | Updated CIDR |

#### Request Example

```bash
curl -X POST "https://api.platform.example.com/orgips/orgip_003" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Remote office - Updated",
    "cidr": 28
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "orgip_003",
    "ip_address": "198.51.100.0",
    "cidr": 28,
    "description": "Remote office - Updated",
    "updated_at": "2024-01-22T23:00:00Z"
  },
  "message": "Organization IP updated successfully"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Organization IP not found |

---

### Delete Organization IP

Removes an organization IP entry.

```
DELETE /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Organization IP ID to delete |

#### Request Example

```bash
curl -X DELETE "https://api.platform.example.com/orgips/orgip_003" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "message": "Organization IP deleted successfully",
  "data": {
    "id": "orgip_003",
    "deleted_at": "2024-01-22T23:30:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid ID format |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 404 | Organization IP not found |

---

## Related Documentation

- [Authentication API](authentication.md) - Authentication and authorization
- [Dialplan API](dialplan.md) - Call routing and dial plan configuration
- [Organizations API](organizations.md) - Organization management
- [Numbers API](billing.md) - Phone number management (in Billing)