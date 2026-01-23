# VoIP & Telecommunications Models

This document provides detailed documentation for voicemail, dial plan, and telephony-related data models in the schema-api service.

## Overview

The VoIP and telecommunications models handle core telephony functionality including:

- **Voicemail Management** - Message storage, preferences, and access control
- **Dial Plan Configuration** - Call routing rules and policies
- **Device Management** - SIP devices, trunks, and provisioning
- **Phone Number Association** - Linking numbers to users and organizations

## Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────┐
│  voicemail_msgs │       │  voicemail_prefs │
│  (messages)     │       │  (settings)      │
└────────┬────────┘       └────────┬─────────┘
         │                         │
         └────────┬────────────────┘
                  │ username/domain
                  ▼
         ┌────────────────┐
         │  AssocNumbers  │◄──────┐
         │  (phone nums)  │       │
         └───────┬────────┘       │
                 │                │
    OrgID/UserID │                │
                 ▼                │
         ┌────────────────┐       │
         │    Devices     │───────┤
         │  (SIP devices) │       │
         └───────┬────────┘       │
                 │                │
            DevID│                │
                 ▼                │
         ┌────────────────┐       │
         │  DevicesVars   │       │
         │  (config vars) │       │
         └────────────────┘       │
                                  │
         ┌────────────────┐       │
         │   DeviceMap    │───────┘
         │ (SIP URI→Dev)  │
         └────────────────┘

         ┌────────────────┐
         │DialPlanPolicies│
         │   (policies)   │
         └───────┬────────┘
                 │ DPPID
                 ▼
         ┌────────────────┐
         │  DialPlanItem  │◄──┐
         │    (rules)     │───┘ ParentDPIID
         └────────────────┘     (self-reference)
```

---

## Voicemail Models

### voicemail_msgs

Stores individual voicemail messages with metadata, file references, and read status.

#### Purpose and Usage

This model stores all voicemail messages in the system. Each record represents a single voicemail with caller information, timestamps, file location, and processing flags. Use this model to:

- Retrieve voicemail messages for a user
- Track read/unread status
- Manage voicemail folders
- Handle message forwarding
- Support voicemail-to-email functionality

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `created_epoch` | int(11) | Yes | Unix epoch timestamp when the voicemail was recorded |
| `read_epoch` | int(11) | No | Unix epoch timestamp when message was first listened to (null if unread) |
| `username` | varchar(255) | Yes | Username of the voicemail box owner |
| `domain` | varchar(255) | Yes | Domain associated with the voicemail owner |
| `uuid` | varchar(255) | Yes | Unique identifier for the voicemail message (UUID format) |
| `cid_name` | varchar(255) | No | Caller ID name of the person who left the message |
| `cid_number` | varchar(255) | No | Caller ID phone number of the caller |
| `in_folder` | varchar(255) | Yes | Current folder containing the message (e.g., "inbox", "saved", "trash") |
| `file_path` | varchar(255) | Yes | Full filesystem path to the audio file |
| `message_len` | int(11) | Yes | Duration of the voicemail in seconds |
| `flags` | varchar(255) | No | Comma-separated message flags (e.g., "urgent", "private") |
| `read_flags` | varchar(255) | No | Flags indicating read status across different access methods |
| `forwarded_by` | varchar(255) | No | Username of user who forwarded this message (if applicable) |
| `email` | varchar(255) | No | Email address for voicemail-to-email notifications |
| `transcription_flag` | int(11) | No | Transcription status: 0=none, 1=pending, 2=completed, 3=failed |

#### Validation Rules

- `username` and `domain` combination must correspond to a valid voicemail box
- `uuid` must be unique across all messages
- `created_epoch` must be a valid Unix timestamp
- `in_folder` must be one of the configured folder names
- `file_path` must point to a valid audio file location
- `message_len` must be a positive integer

#### Example JSON

```json
{
  "created_epoch": 1699876543,
  "read_epoch": 1699880000,
  "username": "jsmith",
  "domain": "acme-corp.voip.example.com",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "cid_name": "John Doe",
  "cid_number": "+14155551234",
  "in_folder": "inbox",
  "file_path": "/var/voicemail/acme-corp/jsmith/inbox/msg_1699876543.wav",
  "message_len": 45,
  "flags": "urgent",
  "read_flags": "phone",
  "forwarded_by": null,
  "email": "jsmith@acme-corp.com",
  "transcription_flag": 2
}
```

#### Relationships

- **voicemail_prefs**: Linked by `username` and `domain` to get user preferences
- **AssocNumbers**: Caller's number may be associated with a known user/organization

---

### voicemail_prefs

Stores user voicemail preferences including custom greetings and security settings.

#### Purpose and Usage

This model contains per-user voicemail configuration including recorded name, greeting file, and PIN. Use this model to:

- Configure voicemail greetings
- Manage voicemail passwords/PINs
- Store custom name recordings
- Personalize voicemail experience

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | varchar(255) | Yes | Username of the voicemail box owner (primary key part) |
| `domain` | varchar(255) | Yes | Domain associated with the voicemail owner (primary key part) |
| `name_path` | varchar(255) | No | Filesystem path to the recorded name audio file |
| `greeting_path` | varchar(255) | No | Filesystem path to the custom greeting audio file |
| `password` | varchar(255) | Yes | Voicemail PIN/password (stored hashed) |

#### Validation Rules

- `username` and `domain` combination must be unique (composite primary key)
- `password` must meet minimum complexity requirements (typically 4-10 digits)
- `name_path` and `greeting_path` must be valid file paths when provided
- Audio files must be in supported format (WAV, MP3)

#### Example JSON

```json
{
  "username": "jsmith",
  "domain": "acme-corp.voip.example.com",
  "name_path": "/var/voicemail/acme-corp/jsmith/name.wav",
  "greeting_path": "/var/voicemail/acme-corp/jsmith/greeting.wav",
  "password": "5a2d8f..."
}
```

#### Relationships

- **voicemail_msgs**: Messages are linked by `username` and `domain`

---

## Phone Number Management

### AssocNumbers

Associates phone numbers with organizations and users, controlling access and ownership.

#### Purpose and Usage

This model links phone numbers to users and organizations with configurable access policies. Use this model to:

- Register mobile, home, and work numbers for users
- Control voicemail access from different numbers
- Prioritize numbers for callback/caller ID
- Enable/disable number associations

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Val` | varchar(32) | Yes | Phone number in E.164 format (primary key) |
| `OrgID` | int(10) unsigned | Yes | Organization ID the number is associated with |
| `UserID` | int(11) | No | User ID the number belongs to (null for org-level numbers) |
| `Type` | enum | Yes | Number type: `Mobile`, `Home`, `Work`, `Other`, `Unknown` |
| `Rank` | tinyint(3) unsigned | Yes | Priority rank (1=highest) for number selection |
| `AccessVM` | enum | Yes | Voicemail access policy: `Allow`, `RequirePIN`, `Block` |
| `Ownership` | enum | Yes | Ownership type: `Active` (user owns), `Passive` (associated only) |
| `Status` | enum | Yes | Current status: `Enabled`, `Suspended` |

#### Validation Rules

- `Val` must be a valid phone number, preferably E.164 format
- `OrgID` must reference a valid organization
- `UserID` must reference a valid user when provided
- `Rank` values should be unique per user for prioritization
- Default `AccessVM` should be `RequirePIN` for security

#### Example JSON

```json
{
  "Val": "+14155551234",
  "OrgID": 1001,
  "UserID": 5432,
  "Type": "Mobile",
  "Rank": 1,
  "AccessVM": "Allow",
  "Ownership": "Active",
  "Status": "Enabled"
}
```

#### Relationships

- **Devices**: Numbers may be assigned to SIP devices
- **voicemail_msgs**: Caller numbers in messages can be matched to associated numbers

#### Common Use Cases

1. **Trusted Mobile Access**: Allow direct voicemail access without PIN from user's mobile
2. **Multi-Number Users**: Associate multiple numbers with priority ranking
3. **Shared Numbers**: Org-level numbers without specific user assignment

---

## Device Management

### Devices

SIP devices and trunks registered in the system.

#### Purpose and Usage

This model represents SIP endpoints including desk phones, softphones, and SIP trunks. Use this model to:

- Register and provision SIP devices
- Manage device credentials
- Assign extensions
- Control roaming permissions

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `DevID` | int(10) unsigned | Auto | Device ID (primary key, auto-increment) |
| `OrgID` | int(10) unsigned | Yes | Organization ID owning the device |
| `DMID` | int(10) unsigned | Yes | Domain ID for SIP registration |
| `Extension` | mediumint(8) unsigned | No | Extension number assigned to device |
| `DeviceType` | enum | Yes | Device type: `Device`, `SIPTrunk` |
| `Desc` | varchar(32) | No | Human-readable description |
| `Password` | varchar(32) | Yes | SIP authentication password |
| `Location` | varchar(32) | No | Physical location description |
| `AllowRoaming` | enum | Yes | Allow registration from different IPs: `YES`, `NO` |
| `MAC` | bigint(20) unsigned | No | MAC address for auto-provisioning (unique) |
| `Provisioned` | enum | Yes | Provisioning status: `YES`, `NO` |
| `Status` | enum | Yes | Device status: `Enabled`, `Suspended` |

#### Validation Rules

- `OrgID` and `DMID` must reference valid records
- `Extension` must be unique within the organization
- `MAC` must be unique system-wide when provided
- `Password` should meet complexity requirements
- `DeviceType` determines available features and routing

#### Example JSON

```json
{
  "DevID": 78901,
  "OrgID": 1001,
  "DMID": 50,
  "Extension": 2001,
  "DeviceType": "Device",
  "Desc": "Reception Desk Phone",
  "Password": "sip_secure_pass_123",
  "Location": "Main Lobby",
  "AllowRoaming": "NO",
  "MAC": 112233445566,
  "Provisioned": "YES",
  "Status": "Enabled"
}
```

#### Relationships

- **DevicesVars**: Configuration variables for the device
- **DeviceMap**: Maps SIP URIs to devices
- **DeviceMonitoring**: Usage statistics for the device
- **AssocNumbers**: Phone numbers assigned to the device

---

### DevicesVars

Device-specific configuration variables and overrides.

#### Purpose and Usage

This model stores configuration key-value pairs for individual devices, allowing per-device customization. Use this model to:

- Override default device settings
- Configure device-specific features
- Store provisioning parameters
- Manage codec preferences

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `DevID` | int(11) unsigned | Yes | Device ID (foreign key to Devices) |
| `Section` | varchar(16) | Yes | Configuration section name |
| `Field` | varchar(32) | Yes | Configuration field/parameter name |
| `Val_Device` | text | No | Value for the configuration parameter |

#### Validation Rules

- `DevID` must reference a valid device
- `Section` and `Field` combination should follow device vendor specifications
- Composite key: `DevID` + `Section` + `Field`

#### Example JSON

```json
{
  "DevID": 78901,
  "Section": "audio",
  "Field": "preferred_codec",
  "Val_Device": "G.722"
}
```

```json
{
  "DevID": 78901,
  "Section": "network",
  "Field": "vlan_id",
  "Val_Device": "100"
}
```

#### Relationships

- **Devices**: Parent device record

#### Common Configuration Sections

| Section | Common Fields |
|---------|--------------|
| `audio` | `preferred_codec`, `echo_cancel`, `noise_reduction` |
| `network` | `vlan_id`, `qos_dscp`, `ntp_server` |
| `display` | `language`, `timezone`, `backlight` |
| `features` | `call_waiting`, `dnd_enabled`, `auto_answer` |

---

### DeviceMap

Runtime mapping between SIP URIs and physical devices.

#### Purpose and Usage

This model tracks the current registration state of SIP endpoints, mapping SIP URIs to device records. Use this model to:

- Track device registrations
- Resolve SIP URIs to devices
- Monitor online/offline status
- Support multiple registrations per device

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `SIPID` | int(10) unsigned | Yes | SIP URI ID (primary key part) |
| `DevID` | int(10) unsigned | Yes | Device ID (primary key part) |
| `Started` | timestamp | Yes | When the mapping/registration started |

#### Validation Rules

- `SIPID` and `DevID` combination must be unique
- `Started` is automatically set on insert
- Stale mappings should be cleaned up based on registration expiry

#### Example JSON

```json
{
  "SIPID": 34567,
  "DevID": 78901,
  "Started": "2024-01-15T09:30:00Z"
}
```

#### Relationships

- **Devices**: The physical device record
- Used for call routing and presence

---

### DeviceMonitoring

Aggregated device usage statistics by hour.

#### Purpose and Usage

This model stores hourly call statistics per device for reporting and billing. Use this model to:

- Generate usage reports
- Track call volumes
- Calculate costs
- Identify usage patterns

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Hour` | mediumint(8) unsigned | Yes | Hour timestamp as integer (primary key part) |
| `DevID` | int(10) unsigned | Yes | Device ID (primary key part) |
| `Duration` | mediumint(8) unsigned | Yes | Total call duration in seconds for the hour |
| `WCost` | int(10) unsigned | Yes | Wholesale cost in minor currency units |
| `RCost` | int(10) unsigned | Yes | Retail cost in minor currency units |
| `Calls` | tinyint(3) unsigned | Yes | Number of calls in the hour |

#### Validation Rules

- `Hour` and `DevID` form composite primary key
- All numeric values must be non-negative
- Records are aggregated, not individual call records

#### Example JSON

```json
{
  "Hour": 20240115,
  "DevID": 78901,
  "Duration": 3600,
  "WCost": 1500,
  "RCost": 2500,
  "Calls": 25
}
```

#### Relationships

- **Devices**: Parent device being monitored

---

## Dial Plan Configuration

### DialPlanPolicies

Dial plan policy definitions controlling call routing behavior.

#### Purpose and Usage

This model defines dial plan policies that contain routing rules. Policies can be organization-specific or system-wide. Use this model to:

- Create custom dial plans
- Manage call routing rules
- Version control dial plan changes
- Lock policies during editing

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `DPPID` | int(10) unsigned | Auto | Dial plan policy ID (primary key, auto-increment) |
| `Name` | varchar(64) | Yes | Policy name for identification |
| `Status` | enum | Yes | Policy status: `Enabled`, `Suspended`, `Draft` |
| `Type` | enum | Yes | Policy type: `Call`, `NonCall`, `System` |
| `CurrentVersion` | smallint(5) unsigned | Yes | Current active version number |
| `OrgID` | int(10) unsigned | No | Organization ID (null for system policies) |
| `UserID` | int(11) | No | User ID who created/owns the policy |
| `LockedBySessID` | int(10) unsigned | No | Session ID holding edit lock |
| `Created` | datetime | Yes | Creation timestamp |

#### Validation Rules

- `Name` must be unique within organization scope
- Only `Draft` status policies can be edited
- `LockedBySessID` prevents concurrent edits
- `System` type policies require admin privileges

#### Example JSON

```json
{
  "DPPID": 1001,
  "Name": "Main Office Outbound",
  "Status": "Enabled",
  "Type": "Call",
  "CurrentVersion": 3,
  "OrgID": 1001,
  "UserID": 5432,
  "LockedBySessID": null,
  "Created": "2024-01-10T14:30:00Z"
}
```

#### Relationships

- **DialPlanItem**: Contains the actual routing rules for this policy

#### Policy Types

| Type | Description |
|------|-------------|
| `Call` | Standard voice call routing |
| `NonCall` | SMS, fax, and other non-voice routing |
| `System` | System-level routing (e.g., emergency services) |

---

### DialPlanItem

Individual dial plan routing rules within a policy.

#### Purpose and Usage

This model stores individual routing rules that make up a dial plan. Items can be hierarchical and support complex routing logic. Use this model to:

- Define number matching patterns
- Configure call actions (transfer, voicemail, IVR)
- Build hierarchical routing trees
- Set up time-based routing

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `DPIID` | int(10) unsigned | Yes | Dial plan item ID (primary key) |
| `TemplateID` | int(10) unsigned | No | Template ID this item is based on |
| `ParentDPIID` | int(10) unsigned | No | Parent item ID for hierarchical rules |
| `SortOrder` | int(10) unsigned | Yes | Order of evaluation within parent |
| `Name` | varchar(48) | Yes | Human-readable rule name |
| `IsRegExp` | enum | Yes | Whether DestinationNumber is regex: `YES`, `NO` |
| `DestinationNumber` | varchar(32) | No | Number pattern or transfer destination |
| `Context` | varchar(16) | No | Dial plan context (e.g., "internal", "external") |
| `DependentDPPID` | int(10) unsigned | No | ID of dependent policy |
| `DefaultStart` | enum | No | Is this the default entry point: `YES` or null |
| `Variables` | varchar(4096) | No | XML-formatted variables |
| `LinkItems` | varchar(4096) | No | XML-formatted link configuration |
| `UIInventory` | varchar(4096) | No | XML-formatted UI display metadata |
| `DPPID` | int(10) unsigned | Yes | Parent policy ID |

#### Validation Rules

- `DPIID` must be unique
- `DPPID` must reference a valid policy
- `ParentDPIID` must reference a valid item or be null for root items
- Only one item per policy can have `DefaultStart = 'YES'`
- `SortOrder` determines evaluation order among siblings

#### Example JSON

```json
{
  "DPIID": 50001,
  "TemplateID": null,
  "ParentDPIID": null,
  "SortOrder": 1,
  "Name": "US Toll-Free Numbers",
  "IsRegExp": "YES",
  "DestinationNumber": "^1(800|888|877|866|855)[0-9]{7}$",
  "Context": "external",
  "DependentDPPID": null,
  "DefaultStart": "YES",
  "Variables": "<vars><var name=\"rate_class\">toll_free</var></vars>",
  "LinkItems": null,
  "UIInventory": "<ui><icon>phone-outbound</icon><color>#00AA00</color></ui>",
  "DPPID": 1001
}
```

#### Relationships

- **DialPlanPolicies**: Parent policy containing this item
- **DialPlanItem** (self): Hierarchical parent-child relationship

#### Common Patterns

```json
// Internal Extension Routing
{
  "Name": "Internal Extensions",
  "IsRegExp": "YES",
  "DestinationNumber": "^[2-4][0-9]{3}$",
  "Context": "internal"
}

// Emergency Services
{
  "Name": "Emergency 911",
  "IsRegExp": "NO",
  "DestinationNumber": "911",
  "Context": "emergency"
}

// International Calls
{
  "Name": "International",
  "IsRegExp": "YES",
  "DestinationNumber": "^011[0-9]+$",
  "Context": "international"
}
```

---

## Common Use Cases

### Setting Up a New User's Voicemail

1. Create `voicemail_prefs` record with username, domain, and default PIN
2. Associate phone numbers in `AssocNumbers` with appropriate `AccessVM` settings
3. Voicemail messages will automatically populate `voicemail_msgs`

### Provisioning a New SIP Device

1. Create `Devices` record with organization, extension, and credentials
2. Add configuration overrides in `DevicesVars`
3. Device registration creates `DeviceMap` entry
4. Usage tracking populates `DeviceMonitoring`

### Creating a Custom Dial Plan

1. Create `DialPlanPolicies` record in `Draft` status
2. Add `DialPlanItem` records with routing rules
3. Set one item as `DefaultStart`
4. Change policy status to `Enabled` when ready

---

## Related Documentation

- [Device Models](device-models.md) - Additional device configuration details
- [Billing & Audit Models](billing-audit-models.md) - Cost tracking and audit logging
- [Permissions Models](permissions-models.md) - Access control for VoIP features
- [Models Overview](README.md) - Complete model index