# Device Management Models

This document covers the data models for device tracking, monitoring, and configuration in the schema-api service. These models handle SIP device registration, provisioning, monitoring statistics, and device-to-endpoint mappings.

## Overview

The device management system supports:
- SIP device and trunk registration
- Device provisioning and configuration
- Real-time device monitoring and statistics
- Device-to-SIP URI mapping
- Flexible device variable configuration

## Entity Relationships

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   Devices   │───────│  DeviceMap   │───────│   SIP URIs  │
│   (DevID)   │       │ (DevID,SIPID)│       │   (SIPID)   │
└──────┬──────┘       └──────────────┘       └─────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐
│  DevicesVars     │
│  (DevID, Field)  │
└──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────────┐
│ DeviceMonitoring │
│ (DevID, Hour)    │
└──────────────────┘
```

## Models

---

### Devices

Primary table for SIP devices and trunks. Stores device registration, authentication credentials, and provisioning status.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DevID | int(10) unsigned | Yes | Device ID (primary key, auto increment) |
| OrgID | int(10) unsigned | Yes | Organization ID (part of composite key) |
| DMID | int(10) unsigned | No | Domain ID for the device |
| Extension | mediumint(8) unsigned | No | Extension number assigned to device |
| DeviceType | enum('Device','SIPTrunk') | Yes | Type of device - endpoint or SIP trunk |
| Desc | varchar(32) | No | Human-readable description |
| Password | varchar(32) | No | Device authentication password |
| Location | varchar(32) | No | Physical location identifier |
| AllowRoaming | enum('YES','NO') | Yes | Whether device can register from different IPs |
| MAC | bigint(20) unsigned | No | MAC address (unique constraint) |
| Provisioned | enum('YES','NO') | Yes | Whether device has been provisioned |
| Status | enum('Enabled','Suspended') | Yes | Current device status |

#### Validation Rules

- `DevID` auto-increments and must be unique
- `MAC` address must be unique across all devices when provided
- `DeviceType` must be either 'Device' or 'SIPTrunk'
- `Status` controls whether device can register and make calls
- `OrgID` must reference a valid organization

#### Example JSON

```json
{
  "DevID": 10542,
  "OrgID": 1205,
  "DMID": 87,
  "Extension": 1001,
  "DeviceType": "Device",
  "Desc": "Conference Room A - Polycom",
  "Password": "Xk9$mP2nQ7wL",
  "Location": "Building A, Floor 2",
  "AllowRoaming": "NO",
  "MAC": 170568329876542,
  "Provisioned": "YES",
  "Status": "Enabled"
}
```

#### Relationships

- **Organization**: Belongs to an organization via `OrgID`
- **Domain**: Associated with a domain via `DMID`
- **DevicesVars**: Has many configuration variables
- **DeviceMap**: Can have multiple SIP URI mappings
- **DeviceMonitoring**: Has many monitoring records

#### Common Use Cases

1. **Device Registration**: Create new devices for SIP endpoints
2. **SIP Trunk Setup**: Configure carrier trunks with `DeviceType: 'SIPTrunk'`
3. **Provisioning Management**: Track auto-provisioning via MAC address
4. **Access Control**: Suspend/enable devices via `Status` field

---

### DevicesVars

Flexible key-value storage for device-specific configuration variables. Allows custom settings per device organized by section.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DevID | int(11) unsigned | Yes | Device ID (foreign key to Devices) |
| Section | varchar(16) | Yes | Configuration section grouping |
| Field | varchar(32) | Yes | Configuration field name |
| Val_Device | text | No | Configuration value for this device |

#### Validation Rules

- Composite primary key of `DevID`, `Section`, and `Field`
- `DevID` must reference an existing device
- `Section` provides logical grouping (e.g., 'sip', 'codec', 'network')
- `Field` names should follow consistent naming conventions

#### Example JSON

```json
{
  "DevID": 10542,
  "Section": "sip",
  "Field": "transport",
  "Val_Device": "tls"
}
```

```json
{
  "DevID": 10542,
  "Section": "codec",
  "Field": "preferred_list",
  "Val_Device": "PCMU,PCMA,G722,G729"
}
```

```json
{
  "DevID": 10542,
  "Section": "network",
  "Field": "vlan_id",
  "Val_Device": "100"
}
```

#### Relationships

- **Devices**: Belongs to a device via `DevID`

#### Common Use Cases

1. **SIP Configuration**: Transport settings, registration intervals
2. **Codec Preferences**: Audio/video codec priority lists
3. **Network Settings**: VLAN, QoS, and firewall configurations
4. **Provisioning Templates**: Device-specific overrides for auto-provisioning

---

### DeviceMap

Maps SIP URIs to physical devices, tracking when each mapping was established. Enables routing calls to the correct device.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SIPID | int(10) unsigned | Yes | SIP URI identifier |
| DevID | int(10) unsigned | Yes | Device identifier |
| Started | timestamp | Yes | When this mapping became active |

#### Validation Rules

- Composite primary key of `SIPID` and `DevID`
- `Started` defaults to current timestamp on insert
- A SIP URI may map to multiple devices (multi-device ring)
- A device may handle multiple SIP URIs

#### Example JSON

```json
{
  "SIPID": 50234,
  "DevID": 10542,
  "Started": "2024-01-15T09:30:00Z"
}
```

```json
{
  "SIPID": 50234,
  "DevID": 10543,
  "Started": "2024-01-15T09:30:00Z"
}
```

#### Relationships

- **Devices**: References device via `DevID`
- **SIP URIs**: References SIP URI via `SIPID` (external table)

#### Common Use Cases

1. **Single Device Mapping**: Standard 1:1 URI to device assignment
2. **Multi-Device Ring**: Map one URI to multiple devices for simultaneous ring
3. **Hot Desking**: Track which device is currently associated with a user's URI
4. **Audit Trail**: `Started` timestamp provides history of device assignments

---

### DeviceMonitoring

Aggregated hourly statistics for device usage, including call counts, duration, and costs. Used for reporting and capacity planning.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Hour | mediumint(8) unsigned | Yes | Hour timestamp - hours since epoch (primary key part) |
| DevID | int(10) unsigned | Yes | Device ID (primary key part) |
| Duration | mediumint(8) unsigned | No | Total call duration in seconds for the hour |
| WCost | int(10) unsigned | No | Wholesale cost in minor currency units |
| RCost | int(10) unsigned | No | Retail cost in minor currency units |
| Calls | tinyint(3) unsigned | No | Number of calls during the hour |

#### Validation Rules

- Composite primary key of `Hour` and `DevID`
- `Hour` is stored as hours since Unix epoch for efficient storage
- `Duration` accumulates total seconds of all calls
- `WCost` and `RCost` stored as integers (cents/pence) to avoid floating-point issues
- `Calls` limited to 255 per hour per device (tinyint)

#### Example JSON

```json
{
  "Hour": 473856,
  "DevID": 10542,
  "Duration": 3847,
  "WCost": 1250,
  "RCost": 2500,
  "Calls": 23
}
```

#### Relationships

- **Devices**: References device via `DevID`

#### Common Use Cases

1. **Usage Reports**: Generate hourly/daily/monthly usage statistics
2. **Billing Reconciliation**: Verify retail vs wholesale costs
3. **Capacity Planning**: Identify high-usage devices and peak hours
4. **Anomaly Detection**: Detect unusual call patterns or fraud

#### Querying Examples

**Calculate daily totals for a device:**
```sql
SELECT 
  DevID,
  SUM(Duration) as TotalDuration,
  SUM(Calls) as TotalCalls,
  SUM(RCost) as TotalRevenue
FROM DeviceMonitoring
WHERE DevID = 10542
  AND Hour BETWEEN 473832 AND 473856
GROUP BY DevID
```

**Find most active devices:**
```sql
SELECT 
  DevID,
  SUM(Calls) as TotalCalls
FROM DeviceMonitoring
WHERE Hour >= 473832
GROUP BY DevID
ORDER BY TotalCalls DESC
LIMIT 10
```

---

## Integration Patterns

### Device Provisioning Flow

```
1. Create Device record with MAC address
2. Set Provisioned = 'NO'
3. Device boots and requests config via MAC
4. System generates config from DevicesVars
5. Update Provisioned = 'YES'
6. Create DeviceMap entry for SIP URI
```

### Monitoring Data Collection

```
1. CDR generated at call completion
2. Aggregator groups by hour and DevID
3. Upsert into DeviceMonitoring
4. Increment Duration, Calls, WCost, RCost
```

### Device Status Management

| Status | Registration | Calls | Use Case |
|--------|--------------|-------|----------|
| Enabled | Allowed | Allowed | Normal operation |
| Suspended | Blocked | Blocked | Non-payment, lost device |

## See Also

- [VoIP Models](voip-models.md) - SIP URI and call handling schemas
- [Billing & Audit Models](billing-audit-models.md) - Cost tracking and audit logs
- [Permissions Models](permissions-models.md) - Access control for device management