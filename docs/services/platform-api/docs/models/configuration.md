# Configuration Models

This document covers configuration-related data models in the platform-api, including key-value storage, scheduling, archiving policies, and system configuration entities.

## Overview

Configuration models provide the foundation for storing and managing system settings, user preferences, scheduled tasks, and organizational policies. These models enable flexible configuration management across the platform.

**Related Documentation:**
- [Identity Models](identity.md) - User and organization models that reference configurations
- [Telephony Models](telephony.md) - Device configurations and call settings
- [Billing Models](billing.md) - Rate and service configurations

---

## KeyValueStorage

Flexible key-value storage for user-specific or application-specific data, organized by context namespaces.

### Purpose

KeyValueStorage provides a schema-less storage mechanism for:
- User preferences and settings
- Application state persistence
- Cached data with expiration
- Custom metadata storage

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| KID | int | Yes | Primary key identifier |
| UserID | int | Yes | Foreign key to Users table - owner of the data |
| Context | string | Yes | Namespace/context for organizing keys (e.g., "ui_preferences", "app_state") |
| Key | string | Yes | Key name within the context |
| Data | string | Yes | Stored value data (can be JSON, plain text, or serialized data) |
| Hash | string | No | SHA1 hash of the data value for integrity verification |
| Expires | datetime | No | Expiration timestamp in YYYYMMDDHHMMSS format |

### Validation Rules

- **UserID**: Must reference a valid user in the Users table
- **Context**: Should follow a consistent naming convention (lowercase, underscores)
- **Key**: Unique within the combination of UserID and Context
- **Expires**: Optional; when set, data should be considered invalid after this timestamp
- **Hash**: Auto-generated SHA1 hash of the Data field

### Example

```json
{
  "KID": 12345,
  "UserID": 1001,
  "Context": "ui_preferences",
  "Key": "dashboard_layout",
  "Data": "{\"columns\":3,\"widgets\":[\"call_stats\",\"voicemail\",\"contacts\"],\"theme\":\"dark\"}",
  "Hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
  "Expires": "20251231235959"
}
```

### Relationships

```
KeyValueStorage.UserID → Users.ID
```

### Common Use Cases

1. **UI Preferences**: Store dashboard layouts, theme settings, column widths
2. **Application State**: Persist filter selections, last viewed items
3. **Temporary Tokens**: Store short-lived verification codes with expiration
4. **Feature Flags**: User-specific feature toggles

---

## Schedule

Defines recurring or one-time scheduled events with flexible timing options.

### Purpose

Schedule manages automated task execution with support for:
- Complex recurring patterns (daily, weekly, monthly)
- Time-based frequency within date ranges
- Policy-triggered executions
- Late execution handling

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SchID | int | Yes | Primary key - Schedule identifier |
| OrgID | int | Yes | Organization ID owning this schedule |
| Name | string | Yes | Human-readable schedule name |
| Status | string | Yes | Schedule status: "Active" or "Suspended" |
| FireIfLate | string | Yes | "YES" or "NO" - whether to execute if schedule time was missed |
| PolicyStart | string | No | Policy identifier that triggers this schedule |
| DayNumbers | string | No | Comma-separated day numbers (1-31) or "L" for last day of month |
| DayNames | string | No | Comma-separated day names (MON, TUE, WED, THU, FRI, SAT, SUN) |
| Freq_SpacingM | int | No | Frequency spacing in minutes between executions |
| Freq_StartTime | time | No | Daily start time for frequency-based execution (HH:MM:SS) |
| Freq_EndTime | time | No | Daily end time for frequency-based execution (HH:MM:SS) |
| RepeatTimes | int | No | Maximum number of times to repeat execution |
| RepeatCount | int | No | Current count of completed executions |
| Start | datetime | No | Schedule validity start datetime |
| End | datetime | No | Schedule validity end datetime |

### Validation Rules

- **Status**: Must be "Active" or "Suspended"
- **FireIfLate**: Must be "YES" or "NO"
- **DayNumbers**: Valid values are 1-31 or "L" (last day), comma-separated
- **DayNames**: Valid values are MON, TUE, WED, THU, FRI, SAT, SUN
- **Freq_SpacingM**: Positive integer when using frequency-based scheduling
- **Start/End**: End must be after Start when both are specified

### Example

```json
{
  "SchID": 500,
  "OrgID": 100,
  "Name": "Daily Report Generation",
  "Status": "Active",
  "FireIfLate": "YES",
  "PolicyStart": "REPORT_GEN_V1",
  "DayNumbers": null,
  "DayNames": "MON,TUE,WED,THU,FRI",
  "Freq_SpacingM": 0,
  "Freq_StartTime": "08:00:00",
  "Freq_EndTime": "08:00:00",
  "RepeatTimes": 0,
  "RepeatCount": 0,
  "Start": "2024-01-01 00:00:00",
  "End": "2025-12-31 23:59:59"
}
```

### Relationships

```
Schedule.OrgID → Orgs.OrgID
Schedule.SchID → ScheduledEvent.SchID
```

### Common Use Cases

1. **Report Generation**: Daily/weekly automated reports
2. **Data Cleanup**: Scheduled archiving or deletion tasks
3. **Notifications**: Recurring reminder systems
4. **Billing Cycles**: Monthly billing job triggers

---

## ScheduledEvent

Individual event instances generated from Schedule definitions.

### Purpose

ScheduledEvent tracks specific execution instances of schedules, enabling:
- Event queue management
- Execution status tracking
- Late event handling
- Audit trail for scheduled jobs

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SchID | int | Yes | Foreign key to Schedule table |
| FireTime | datetime | Yes | Scheduled execution timestamp |
| FireStatus | string | Yes | Event status: "Pending", "Completed", "Failed", or "Late" |

### Validation Rules

- **SchID**: Must reference a valid Schedule
- **FireStatus**: Must be one of "Pending", "Completed", "Failed", "Late"
- **FireTime**: Must be a valid datetime

### Example

```json
{
  "SchID": 500,
  "FireTime": "2024-06-15 08:00:00",
  "FireStatus": "Completed"
}
```

```json
{
  "SchID": 500,
  "FireTime": "2024-06-16 08:00:00",
  "FireStatus": "Pending"
}
```

### Relationships

```
ScheduledEvent.SchID → Schedule.SchID
```

### Status Lifecycle

```
Pending → Completed (successful execution)
        → Failed (execution error)
        → Late (missed execution window, processed if FireIfLate=YES)
```

---

## ArchivingPolicyTypes

Defines types of archiving policies for data retention management.

### Purpose

ArchivingPolicyTypes categorizes archiving policies for:
- Compliance requirements
- Data retention rules
- Storage optimization
- Internal vs. customer-facing policies

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | int | Yes | Primary key - Policy type identifier |
| isInternal | boolean | Yes | Whether the policy type is internal (derived from "yes"/"no" database field) |

### Validation Rules

- **id**: Unique positive integer
- **isInternal**: Boolean derived from Internal field ("yes" → true, "no" → false)

### Example

```json
{
  "id": 1,
  "isInternal": false
}
```

```json
{
  "id": 2,
  "isInternal": true
}
```

### Common Use Cases

1. **Compliance Archiving**: External policy types for regulatory compliance (GDPR, HIPAA)
2. **Internal Cleanup**: Internal policy types for system maintenance
3. **Customer Retention**: External policies customers can configure

---

## Domain

Domain configuration mapping organizations to their SIP domains.

### Purpose

Domain manages the relationship between organizations and their SIP domain names:
- Multi-domain support per organization
- Default domain designation
- SIP URI routing

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DMID | int | Yes | Primary key - Domain mapping identifier |
| OrgID | int | Yes | Foreign key to Organizations table |
| Domain | string | Yes | Domain name (e.g., "company.sip.example.com") |
| Default | string | Yes | "YES" or "NO" - whether this is the default domain for the org |

### Validation Rules

- **Domain**: Valid domain name format, unique across the system
- **Default**: Only one domain per OrgID can have Default="YES"
- **OrgID**: Must reference a valid organization

### Example

```json
{
  "DMID": 1001,
  "OrgID": 100,
  "Domain": "acme-corp.sip.platform.com",
  "Default": "YES"
}
```

```json
{
  "DMID": 1002,
  "OrgID": 100,
  "Domain": "acme-sales.sip.platform.com",
  "Default": "NO"
}
```

### Relationships

```
Domain.OrgID → Orgs.OrgID
Domain.DMID → Devices.DMID
Domain.DMID → SIPURI.DMID
```

---

## OrgService

Service subscription configuration for organizations.

### Purpose

OrgService tracks which services are enabled for each organization:
- Service activation/deactivation
- Date-bound service availability
- Service-level configuration

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OSID | int | Yes | Primary key - Org Service identifier |
| OrgID | int | Yes | Foreign key to Organizations table |
| ServiceID | int | Yes | Foreign key to Services table |
| Status | string | Yes | Service status: "Active" or "Inactive" |
| StartDate | date | Yes | Service activation date |
| EndDate | date | No | Service termination date (0000-00-00 for indefinite) |

### Validation Rules

- **Status**: Must be "Active" or "Inactive"
- **StartDate**: Valid date, typically not in the future
- **EndDate**: Must be after StartDate if specified; "0000-00-00" means indefinite

### Example

```json
{
  "OSID": 5001,
  "OrgID": 100,
  "ServiceID": 10,
  "Status": "Active",
  "StartDate": "2024-01-01",
  "EndDate": "0000-00-00"
}
```

### Relationships

```
OrgService.OrgID → Orgs.OrgID
OrgService.ServiceID → Services.SID
OrgService.OSID → OrgServiceRate.OSID
```

---

## BillingPrefs

Organization billing preferences and configuration.

### Purpose

BillingPrefs stores billing-related settings:
- Billing cycle timing
- Tax information
- Currency preferences

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Primary key - Organization identifier |
| BillingDay | int | Yes | Day of month for billing (1-28 recommended) |
| BillingCycle | string | Yes | Billing cycle period (e.g., "Monthly", "Quarterly") |
| VAT | string | No | VAT registration number or rate |
| Currency | string | Yes | ISO 4217 currency code (e.g., "GBP", "USD", "EUR") |

### Validation Rules

- **BillingDay**: Integer 1-31 (28 recommended for consistent monthly billing)
- **BillingCycle**: Valid cycle identifier
- **Currency**: Valid ISO 4217 currency code

### Example

```json
{
  "OrgID": 100,
  "BillingDay": 1,
  "BillingCycle": "Monthly",
  "VAT": "GB123456789",
  "Currency": "GBP"
}
```

### Relationships

```
BillingPrefs.OrgID → Orgs.OrgID
```

---

## Permission

User permission configuration for access control.

### Purpose

Permission defines granular access control rules:
- CRUD operation permissions
- Target-based scoping
- Allow/Deny policies

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OwnerID | int | Yes | User ID who owns this permission (0 for global) |
| TargetType | string | Yes | Type of target: "Orgs" or "Users" |
| TargetID | int | Yes | Target scope: -4=all sub orgs+own, -3=all sub orgs, -2=local, -1=global, 0=own, >0=specific ID |
| Polarity | string | Yes | "Allow" or "Deny" |
| PCreate | int | Yes | Create permission bitmask |
| PRead | int | Yes | Read permission bitmask |
| PUpdate | int | Yes | Update permission bitmask |
| PDelete | int | Yes | Delete permission bitmask |

### Validation Rules

- **TargetType**: Must be "Orgs" or "Users"
- **Polarity**: Must be "Allow" or "Deny"
- **TargetID Special Values**:
  - `-4`: All sub-organizations plus own organization
  - `-3`: All sub-organizations only
  - `-2`: Local scope
  - `-1`: Global scope
  - `0`: Own record only
  - `>0`: Specific entity ID

### Example

```json
{
  "OwnerID": 1001,
  "TargetType": "Users",
  "TargetID": -2,
  "Polarity": "Allow",
  "PCreate": 1,
  "PRead": 1,
  "PUpdate": 1,
  "PDelete": 0
}
```

### Relationships

```
Permission.OwnerID → Users.ID
```

---

## BasePermission

Base permission definitions for object-level access control.

### Purpose

BasePermission defines the available permissions for each object type, used in conjunction with Permission bitmasks.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Object | string | Yes | Object type the permission applies to (e.g., "Users", "Devices", "Groups") |
| Bit | int | Yes | Bit position for this permission in the bitmask |

### Validation Rules

- **Object**: Must be a valid system object type
- **Bit**: Unique within each Object type, typically 0-31 for 32-bit bitmask

### Example

```json
{
  "Object": "Users",
  "Bit": 0
}
```

```json
{
  "Object": "Users",
  "Bit": 1
}
```

### Usage with Permission Bitmasks

```
Permission.PRead = 5 (binary: 101)
  → BasePermission.Bit=0 granted (basic read)
  → BasePermission.Bit=2 granted (extended read)
  → BasePermission.Bit=1 denied
```

---

## ClientAccess

IP-based access control configuration for client products.

### Purpose

ClientAccess manages network-level security for platform products:
- Flex Portal access restrictions
- QueueMon access control
- CTI application security

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID (from UINT validation) |
| Product | string | Yes | Product name (e.g., "FlexPortal", "QueueMon", "CTI") |
| Mode | string | Yes | Access mode configuration |
| IPs | string | No | Comma-separated list of allowed IP addresses |

### Validation Rules

- **OrgID**: Must reference a valid organization
- **Product**: Must be a recognized product identifier
- **IPs**: Valid IPv4/IPv6 addresses, comma-separated

### Example

```json
{
  "OrgID": 100,
  "Product": "CTI",
  "Mode": "Whitelist",
  "IPs": "192.168.1.100,192.168.1.101,10.0.0.50"
}
```

### Relationships

```
ClientAccess.OrgID → Orgs.OrgID
```

---

## NotificationMap

User notification preference mapping.

### Purpose

NotificationMap configures how users receive and respond to system notifications:
- Notification delivery preferences
- Visual response settings
- Mode-based filtering

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| NID | int | Yes | Foreign key to Notifications table |
| UserID | int | Yes | Foreign key to Users table |
| VisualResponse | string | Yes | Visual response type (e.g., "None", "Popup", "Badge") |
| Mode | string | Yes | Notification mode/channel |

### Validation Rules

- **NID**: Must reference a valid notification
- **UserID**: Must reference a valid user
- **VisualResponse**: Must be a recognized response type

### Example

```json
{
  "NID": 2001,
  "UserID": 1001,
  "VisualResponse": "Popup",
  "Mode": "UI"
}
```

### Relationships

```
NotificationMap.NID → Notifications.NID
NotificationMap.UserID → Users.ID
```

---

## Notifications

System notification definitions.

### Purpose

Notifications stores platform-wide announcements and alerts:
- System maintenance notices
- Feature announcements
- Security alerts

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| NID | int | Yes | Primary key - Notification identifier |
| StartTime | datetime | Yes | When the notification becomes active |
| Expires | datetime | Yes | When the notification expires |

### Validation Rules

- **StartTime**: Valid datetime
- **Expires**: Must be after StartTime

### Example

```json
{
  "NID": 2001,
  "StartTime": "2024-06-01 00:00:00",
  "Expires": "2024-06-30 23:59:59"
}
```

### Relationships

```
Notifications.NID → NotificationMap.NID
```

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION MODELS                              │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│      Users       │         │      Orgs        │
│──────────────────│         │──────────────────│
│  ID (PK)         │         │  OrgID (PK)      │
│  UserName        │         │  Name            │
│  ...             │         │  ...             │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         │ 1:N                        │ 1:N
         ▼                            ▼
┌──────────────────┐         ┌──────────────────┐
│  KeyValueStorage │         │     Domain       │
│──────────────────│         │──────────────────│
│  KID (PK)        │         │  DMID (PK)       │
│  UserID (FK)     │─────────│  OrgID (FK)      │
│  Context         │         │  Domain          │
│  Key             │         │  Default         │
│  Data            │         └──────────────────┘
│  Hash            │
│  Expires         │         ┌──────────────────┐
└──────────────────┘         │    Schedule      │
                             │──────────────────│
         ┌───────────────────│  SchID (PK)      │
         │                   │  OrgID (FK)      │───────┐
         │ 1:N               │  Name            │       │
         ▼                   │  Status          │       │
┌──────────────────┐         │  DayNames        │       │
│  ScheduledEvent  │         │  Freq_SpacingM   │       │
│──────────────────│         │  ...             │       │
│  SchID (FK)      │         └──────────────────┘       │
│  FireTime        │                                    │
│  FireStatus      │                                    │
└──────────────────┘                                    │
                             ┌──────────────────┐       │
                             │   OrgService     │       │
                             │──────────────────│       │
                             │  OSID (PK)       │       │
                             │  OrgID (FK)      │◄──────┘
                             │  ServiceID (FK)  │
                             │  Status          │
                             │  StartDate       │
                             │  EndDate         │
                             └────────┬─────────┘
                                      │
         ┌──────────────────┐         │ 1:N
         │    Permission    │         ▼
         │──────────────────│  ┌──────────────────┐
         │  OwnerID (FK)    │  │  OrgServiceRate  │
         │  TargetType      │  │──────────────────│
         │  TargetID        │  │  OSRID (PK)      │
         │  Polarity        │  │  OSID (FK)       │
         │  PCreate         │  │  RID (FK)        │
         │  PRead           │  │  ...             │
         │  PUpdate         │  └──────────────────┘
         │  PDelete         │
         └──────────────────┘
                  │
                  │ Uses
                  ▼
         ┌──────────────────┐
         │  BasePermission  │
         │──────────────────│
         │  Object          │
         │  Bit             │
         └──────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  Notifications   │ 1:N     │  NotificationMap │
│──────────────────│────────▶│──────────────────│
│  NID (PK)        │         │  NID (FK)        │
│  StartTime       │         │  UserID (FK)     │
│  Expires         │         │  VisualResponse  │
└──────────────────┘         │  Mode            │
                             └──────────────────┘

┌──────────────────┐         ┌──────────────────┐
│   BillingPrefs   │         │   ClientAccess   │
│──────────────────│         │──────────────────│
│  OrgID (PK/FK)   │         │  OrgID (FK)      │
│  BillingDay      │         │  Product         │
│  BillingCycle    │         │  Mode            │
│  VAT             │         │  IPs             │
│  Currency        │         └──────────────────┘
└──────────────────┘

┌──────────────────────┐
│ ArchivingPolicyTypes │
│──────────────────────│
│  id (PK)             │
│  isInternal          │
└──────────────────────┘
```

---

## Common Patterns

### Key-Value Storage Patterns

```php
// Storing user preferences
$storage = [
    'UserID' => 1001,
    'Context' => 'dashboard',
    'Key' => 'layout',
    'Data' => json_encode(['columns' => 3, 'widgets' => ['stats', 'calls']]),
    'Expires' => null  // No expiration for preferences
];

// Storing temporary verification code
$storage = [
    'UserID' => 1001,
    'Context' => 'verification',
    'Key' => 'email_code',
    'Data' => '123456',
    'Expires' => date('YmdHis', strtotime('+15 minutes'))
];
```

### Schedule Configuration Patterns

```php
// Weekday-only schedule at 9 AM
$schedule = [
    'Name' => 'Morning Report',
    'Status' => 'Active',
    'DayNames' => 'MON,TUE,WED,THU,FRI',
    'Freq_StartTime' => '09:00:00',
    'Freq_EndTime' => '09:00:00'
];

// Monthly schedule on last day
$schedule = [
    'Name' => 'Month-End Processing',
    'Status' => 'Active',
    'DayNumbers' => 'L',
    'Freq_StartTime' => '23:00:00'
];

// Hourly during business hours
$schedule = [
    'Name' => 'Hourly Sync',
    'Status' => 'Active',
    'DayNames' => 'MON,TUE,WED,THU,FRI',
    'Freq_SpacingM' => 60,
    'Freq_StartTime' => '08:00:00',
    'Freq_EndTime' => '18:00:00'
];
```

### Permission Bitmask Examples

```php
// Full CRUD access
$permission = [
    'PCreate' => 1,
    'PRead' => 1,
    'PUpdate' => 1,
    'PDelete' => 1
];

// Read-only access
$permission = [
    'PCreate' => 0,
    'PRead' => 1,
    'PUpdate' => 0,
    'PDelete' => 0
];

// Create and read (no modify/delete)
$permission = [
    'PCreate' => 1,
    'PRead' => 1,
    'PUpdate' => 0,
    'PDelete' => 0
];
```