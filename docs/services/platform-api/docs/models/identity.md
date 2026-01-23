# Identity Models

This document covers the identity and access management models in the Platform API, including users, groups, organizations, permissions, and authentication-related entities.

## Overview

The identity system in Platform API follows a hierarchical structure:

```
Organization (Org)
├── Users
│   ├── Sessions
│   ├── UserSecurity (passwords)
│   ├── Permissions
│   └── KeyValueStorage
├── Groups
│   └── GroupMaps (membership)
├── Domains
└── Child Organizations
```

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Orgs     │◄──────│   Users     │───────►│  Sessions   │
│             │  1:N  │             │  1:N   │  (SessionsX)│
└──────┬──────┘       └──────┬──────┘       └─────────────┘
       │                     │
       │ 1:N                 │ 1:1
       ▼                     ▼
┌─────────────┐       ┌─────────────┐
│   Domains   │       │UserSecurity │
└─────────────┘       └─────────────┘
       │
       │ 1:N          ┌─────────────┐
       │              │   Groups    │
┌──────┴──────┐       └──────┬──────┘
│  Child Orgs │              │
└─────────────┘              │ N:M
                             ▼
                      ┌─────────────┐
                      │  GroupMaps  │
                      └─────────────┘
```

---

## Core Identity Models

### Users

Primary user account model with authentication and security settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key UserID |
| UserName | string | Yes | Username for login, stored lowercase |
| FirstName | string | Yes | User's first name |
| LastName | string | Yes | User's last name |
| PrimaryMobile | string | No | Primary mobile number |
| Status | enum | Yes | Account status (Active, Suspended, etc.) |
| TwoFactorAuth | enum | No | Two-factor authentication enabled (YES/NO) |
| PermissionLevel | string | No | User permission level |
| UserType | enum | Yes | Type of user (User, System) |
| FailCount | int | No | Failed login attempt counter |
| FirstFailTime | datetime | No | Timestamp of first failed login |
| LastLogin | datetime | No | Last successful login timestamp |
| PasswordSetDate | datetime | No | When password was last set |
| TwoFactorSecret | string | No | Secret for 2FA TOTP generation |
| TwoFactorReUse | string | No | 2FA reuse setting |

**Validation Rules:**
- `UserName` must be unique within the organization and is stored lowercase
- `Status` must be one of: Active, Suspended, Deleted
- `UserType` must be one of: User, System
- `TwoFactorAuth` must be YES or NO

**Example JSON:**
```json
{
  "ID": 12345,
  "UserName": "john.smith",
  "FirstName": "John",
  "LastName": "Smith",
  "PrimaryMobile": "+447700900123",
  "Status": "Active",
  "TwoFactorAuth": "YES",
  "PermissionLevel": "Admin",
  "UserType": "User",
  "FailCount": 0,
  "FirstFailTime": null,
  "LastLogin": "2024-01-15 09:30:00",
  "PasswordSetDate": "2024-01-01 00:00:00",
  "TwoFactorSecret": "JBSWY3DPEHPK3PXP",
  "TwoFactorReUse": "NO"
}
```

**Relationships:**
- Belongs to an `Org` via OrgID (implicit)
- Has one `UserSecurity` record for password storage
- Has many `SessionsX` records for active sessions
- Has many `GroupMap` entries for group membership
- Has many `Permission` entries
- Has many `KeyValueStorage` entries

---

### User

Simplified user model used in entity descriptions and lookups.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key |
| FirstName | string | Yes | User's first name |
| LastName | string | Yes | User's last name |
| PIN | string | No | User PIN code for voicemail/access |
| UserType | string | Yes | Type of user (e.g., System) |
| Status | string | Yes | User status (e.g., Active) |
| UserName | string | Yes | Username for authentication |

**Example JSON:**
```json
{
  "ID": 12345,
  "FirstName": "John",
  "LastName": "Smith",
  "PIN": "1234",
  "UserType": "User",
  "Status": "Active",
  "UserName": "john.smith"
}
```

---

### UserSecurity

Stores password hashes and security information for users.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| USID | int | Yes | Primary key security record ID |
| ID | int | Yes | User ID reference (foreign key to Users) |
| HashAlgIter | string | Yes | Hash algorithm and iterations (e.g., "sha256:10000") |
| Salt | string | Yes | Password salt (base64 encoded) |
| EncPwd | string | Yes | Encrypted password hash (base64 encoded) |
| Time | datetime | Yes | Password set timestamp |
| ThisIsAReset | boolean | No | True if this password was set via reset flow |

**Validation Rules:**
- `ID` must reference a valid user
- `HashAlgIter` format: `algorithm:iterations`
- Password history may be maintained for rotation policies

**Example JSON:**
```json
{
  "USID": 98765,
  "ID": 12345,
  "HashAlgIter": "sha256:10000",
  "Salt": "Tm9uY2VTYWx0MTIzNA==",
  "EncPwd": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=",
  "Time": "2024-01-01 00:00:00",
  "ThisIsAReset": false
}
```

**Relationships:**
- Belongs to `Users` via ID field

---

### UserForeignIdType

Defines types of external/foreign IDs that can be associated with users for integration purposes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| TypeID | int | Yes | Primary key identifier for the type |
| ID | string | Yes | Token identifier (alias for Token field) |
| Name | string | Yes | Human-readable name of the foreign ID type |
| ValidationRegex | string | No | Regular expression pattern for validating foreign IDs |

**Example JSON:**
```json
{
  "TypeID": 1,
  "ID": "SALESFORCE_ID",
  "Name": "Salesforce User ID",
  "ValidationRegex": "^[a-zA-Z0-9]{15,18}$"
}
```

**Use Cases:**
- Mapping users to Salesforce contact IDs
- Linking to external HR systems
- CRM integration user mapping

---

## Organization Models

### Orgs

Primary organization/company model representing a tenant in the system.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Primary key organization ID |
| Name | string | Yes | Organization name |
| Status | enum | Yes | Organization status (Active, Suspended, etc.) |
| PasswordRotationD | int | No | Password rotation period in days (0 = disabled) |
| Type | string | Yes | Organization type (Reseller, Customer, etc.) |
| CallCostLimit | decimal | No | Call cost limit for fraud prevention |
| BillingOrgID | int | No | Billing organization reference |
| JBillingID | string | No | JBilling system ID for invoicing |
| Payment | string | No | Payment method/status |
| ParentID | int | No | Parent organization ID for hierarchy |
| EnableMediation | boolean | No | CDR mediation enabled flag |
| MarginLevel | string | No | Margin level (Custom or predefined tier) |
| OrgBillsChild | boolean | No | Whether org bills child organizations |
| Balance | decimal | No | Current account balance |
| CreditLimit | decimal | No | Credit limit for the organization |

**Validation Rules:**
- `Name` must be unique
- `Status` must be one of: Active, Suspended, Deleted
- `ParentID` must reference a valid organization or be null for root orgs
- `PasswordRotationD` must be 0 or a positive integer

**Example JSON:**
```json
{
  "OrgID": 1001,
  "Name": "Acme Corporation",
  "Status": "Active",
  "PasswordRotationD": 90,
  "Type": "Customer",
  "CallCostLimit": 1000.00,
  "BillingOrgID": 1,
  "JBillingID": "ACME-001",
  "Payment": "DirectDebit",
  "ParentID": 1,
  "EnableMediation": true,
  "MarginLevel": "Standard",
  "OrgBillsChild": false,
  "Balance": 5432.10,
  "CreditLimit": 10000.00
}
```

**Relationships:**
- Has many `Users`
- Has many `Groups`
- Has many `Domains`
- Has many child `Orgs` (via ParentID)
- Optionally belongs to a parent `Org`

---

### Org

Simplified organization model for XML input validation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | UINT | No | Organization ID (for updates) |
| ParentID | UINT | No | Parent organization ID |
| Name | STRING | Yes | Organization name |
| Alias | STRING/BLANK | No | Organization alias |
| Status | STRING | Yes | Organization status |
| Type | STRING | Yes | Organization type |
| AdminUserID | UINT | No | Admin user ID |
| TechUserID | UINT | No | Technical contact user ID |
| FinanceUserID | UINT | No | Finance contact user ID |
| CanProvision | YES\|NO | No | Whether org can provision devices |
| CreatorUserID | UINT | No | Creator user ID |
| AutoNumberFrom | UINT | No | Auto number starting point |
| MaxUsers | UINT | No | Maximum users allowed |
| MaxDevices | UINT | No | Maximum devices allowed |
| MaxConnectors | UINT | No | Maximum connectors allowed |

**Example JSON:**
```json
{
  "OrgID": 1001,
  "ParentID": 1,
  "Name": "Acme Corporation",
  "Alias": "acme",
  "Status": "Active",
  "Type": "Customer",
  "AdminUserID": 12345,
  "TechUserID": 12346,
  "FinanceUserID": 12347,
  "CanProvision": "YES",
  "CreatorUserID": 1,
  "AutoNumberFrom": 100,
  "MaxUsers": 500,
  "MaxDevices": 1000,
  "MaxConnectors": 10
}
```

---

### OrgAddress

Postal address information for an organization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SiteLabel | STRING/BLANK | No | Site label (e.g., "HQ", "Branch 1") |
| Address1 | STRING/BLANK | No | Address line 1 |
| Address2 | STRING/BLANK | No | Address line 2 |
| Address3 | STRING/BLANK | No | Address line 3 |
| City | STRING/BLANK | No | City |
| CountyState | STRING/BLANK | No | County or state |
| PostalCode | STRING/BLANK | No | Postal code |
| Country | STRING/BLANK | No | Country |
| Telephone | STRING/BLANK | No | Contact telephone number |

**Example JSON:**
```json
{
  "SiteLabel": "Headquarters",
  "Address1": "123 Business Park",
  "Address2": "Building A",
  "Address3": "",
  "City": "London",
  "CountyState": "Greater London",
  "PostalCode": "EC1A 1BB",
  "Country": "United Kingdom",
  "Telephone": "+442071234567"
}
```

---

## Group Models

### Group

Organizational group for managing collections of users, devices, and SIP URIs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| GroupID | int | Yes | Primary key |
| Name | string | Yes | Group name |
| Category | string | Yes | Group category (e.g., CallCenter, Department) |

**Validation Rules:**
- `Name` must be unique within the organization
- `Category` defines the group's purpose and behavior

**Example JSON:**
```json
{
  "GroupID": 5001,
  "Name": "Sales Team",
  "Category": "Department"
}
```

**Relationships:**
- Belongs to an `Org`
- Has many members via `GroupMaps`

---

### Group (XML Input)

Group entity for XML input validation when creating/updating groups.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | STRING | Yes | Group name |
| Category | STRING | Yes | Group category |
| AdminGroupID | UINT | No | Admin group ID for permissions |

**Example JSON:**
```json
{
  "Name": "Support Queue",
  "Category": "CallCenter",
  "AdminGroupID": 5000
}
```

---

### GroupMaps

Mapping table for group membership, supporting users, devices, SIP URIs, and nested groups.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| HoldingGroupID | int | Yes | Group ID (the container group) |
| UserID | int | Conditional | User ID if member is a user |
| DevID | int | Conditional | Device ID if member is a device |
| SIPID | int | Conditional | SIP URI ID if member is a SIP URI |
| GroupID | int | Conditional | Nested group ID |
| Primary | string | No | YES if this is the member's primary group |
| IgnoreCalls | string | No | YES if member is logged out/ignoring calls |

**Validation Rules:**
- Exactly one of `UserID`, `DevID`, `SIPID`, or `GroupID` must be set
- `Primary` and `IgnoreCalls` must be YES or NO

**Example JSON (User Member):**
```json
{
  "HoldingGroupID": 5001,
  "UserID": 12345,
  "DevID": null,
  "SIPID": null,
  "GroupID": null,
  "Primary": "YES",
  "IgnoreCalls": "NO"
}
```

**Example JSON (Nested Group):**
```json
{
  "HoldingGroupID": 5001,
  "UserID": null,
  "DevID": null,
  "SIPID": null,
  "GroupID": 5002,
  "Primary": "NO",
  "IgnoreCalls": "NO"
}
```

---

### GroupMap

Simplified user-to-group membership mapping.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UserID | int | Yes | Foreign key to Users |
| HoldingGroupID | int | Yes | Foreign key to Groups |
| Primary | boolean | No | Whether this is the user's primary group |

**Example JSON:**
```json
{
  "UserID": 12345,
  "HoldingGroupID": 5001,
  "Primary": true
}
```

---

### GroupMapsLog

Audit log for group membership changes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Time | datetime | Yes | Timestamp of change |
| GroupID | int | Yes | Group ID |
| UserID | int | Yes | User ID |
| State | string | Yes | IN or OUT |
| Reason | string | No | Reason for the change |

**Example JSON:**
```json
{
  "Time": "2024-01-15 09:30:00",
  "GroupID": 5001,
  "UserID": 12345,
  "State": "IN",
  "Reason": "Agent logged in for shift"
}
```

---

### GroupMember_User

User member input model for group operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | UINT | Yes | User ID |
| Primary | YES | No | Whether this is the primary group |
| IgnoreCalls | YES | No | Whether to ignore calls (logged out) |
| Reason | STRING | No | Reason for membership/status |

**Example JSON:**
```json
{
  "ID": 12345,
  "Primary": "YES",
  "IgnoreCalls": "NO",
  "Reason": "Primary sales agent"
}
```

---

### GroupMember_Device

Device member input model for group operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | UINT | Yes | Device ID |
| Primary | YES | No | Whether this is the primary group |
| IgnoreCalls | YES | No | Whether to ignore calls |

**Example JSON:**
```json
{
  "ID": 8001,
  "Primary": "NO",
  "IgnoreCalls": "NO"
}
```

---

### GroupMember_SIPURI

SIP URI member input model for group operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | UINT | Yes | SIP URI ID |
| Primary | YES | No | Whether this is the primary group |

**Example JSON:**
```json
{
  "ID": 3001,
  "Primary": "YES"
}
```

---

### GroupMember_Group

Nested group member input model for group operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | UINT | Yes | Group ID |
| Primary | YES | No | Whether this is the primary group |

**Example JSON:**
```json
{
  "ID": 5002,
  "Primary": "NO"
}
```

---

## Session & Authentication Models

### SessionsX

API session tokens for xAuth authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SessID | int | Yes | Primary key, auto-increment session ID |
| Token | binary | Yes | Session token stored as unhex binary |
| UserID | int | Yes | Foreign key to Users table |
| IPAddress | int | Yes | IP address stored as long integer via ip2long() |

**Validation Rules:**
- `Token` must be unique
- `UserID` must reference a valid user
- Sessions may have TTL enforcement

**Example JSON:**
```json
{
  "SessID": 999001,
  "Token": "a1b2c3d4e5f6...",
  "UserID": 12345,
  "IPAddress": 167772161
}
```

**Relationships:**
- Belongs to `Users` via UserID

---

### Session

Extended session data model with additional tracking fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | UINT | Yes | User ID |
| Token | string | Yes | Session token |
| IPAddress | string | Yes | Client IP address |
| URL | string | No | Server URL |
| SudoedToUserID | UINT | No | Sudoed user ID if impersonating |
| SSO | string | No | SSO flag (YES/NO) |
| LastCheck | datetime | No | Last activity timestamp |
| Notes | string | No | Session notes |
| APICalls | int | No | API calls count in session |
| UIVersion | string | No | UI version string |
| TZOffset | int | No | Timezone offset in minutes |

**Example JSON:**
```json
{
  "ID": 12345,
  "Token": "abc123def456...",
  "IPAddress": "192.168.1.100",
  "URL": "https://api.platform.com",
  "SudoedToUserID": null,
  "SSO": "NO",
  "LastCheck": "2024-01-15 10:30:00",
  "Notes": "",
  "APICalls": 42,
  "UIVersion": "3.2.1",
  "TZOffset": 0
}
```

---

### SSO_Request

SSO authentication request payload for single sign-on flows.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | ANY | Yes | Session ID |
| Server | ANY | Yes | Server URL for callback |
| UseSFRESTAPI | ANY | No | Flag to use Salesforce REST API |

**Example JSON:**
```json
{
  "SID": "session_abc123",
  "Server": "https://login.salesforce.com",
  "UseSFRESTAPI": "YES"
}
```

---

### TempAuth_Request

Temporary token authentication request based on CAPTCHA verification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Ref | STRING | Yes | CAPTCHA reference ID |
| Response | STRING | Yes | User's CAPTCHA response |

**Example JSON:**
```json
{
  "Ref": "captcha_ref_12345",
  "Response": "xK9mN2"
}
```

---

## Permission Models

### Permission

User permission configuration for fine-grained access control.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OwnerID | int | Yes | User ID who owns this permission (0 for global) |
| TargetType | string | Yes | Type of target (Orgs, Users) |
| TargetID | int | Yes | Target ID with special values: -4=all sub orgs+own, -3=all sub orgs, -2=local, -1=global, 0=own, >0=specific ID |
| Polarity | string | Yes | Allow or Deny |
| PCreate | int | No | Create permission bitmask |
| PRead | int | No | Read permission bitmask |
| PUpdate | int | No | Update permission bitmask |
| PDelete | int | No | Delete permission bitmask |

**Validation Rules:**
- `Polarity` must be "Allow" or "Deny"
- `TargetType` must be a valid entity type
- Permission bitmasks are evaluated using `BasePermission` bit definitions

**Example JSON:**
```json
{
  "OwnerID": 12345,
  "TargetType": "Users",
  "TargetID": -2,
  "Polarity": "Allow",
  "PCreate": 1,
  "PRead": 1,
  "PUpdate": 1,
  "PDelete": 0
}
```

**Special TargetID Values:**
| Value | Meaning |
|-------|---------|
| -4 | All sub-organizations plus own organization |
| -3 | All sub-organizations only |
| -2 | Local organization only |
| -1 | Global (all organizations) |
| 0 | Own record only |
| >0 | Specific entity ID |

---

### BasePermission

Base permission definition that maps object types to bit positions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Object | string | Yes | Object type the permission applies to |
| Bit | int | Yes | Bit position for this permission in bitmasks |

**Example JSON:**
```json
{
  "Object": "Users",
  "Bit": 1
}
```

**Usage:**
Permission bitmasks in the `Permission` model use these bit positions to encode multiple object permissions in a single integer.

---

## Availability & State Models

### AvailabilityProfile

Availability profile containing a set of states for user presence management.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AvailabilityProfileID | int | Yes | Profile ID |
| Name | string | Yes | Profile name |

**Example JSON:**
```json
{
  "AvailabilityProfileID": 1,
  "Name": "Standard Agent Profile"
}
```

**Relationships:**
- Has many `AvailabilityState` entries

---

### AvailabilityState

Individual availability state within a profile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AvailabilityStateID | int | Yes | Availability state ID |
| AvailabilityProfileID | int | Yes | Availability profile ID |
| Name | string | Yes | State name (internal) |
| DisplayName | string | Yes | Display name (user-facing) |
| GroupMembershipStrategy | string | No | Strategy for group membership (e.g., AUTOADD) |

**Example JSON:**
```json
{
  "AvailabilityStateID": 101,
  "AvailabilityProfileID": 1,
  "Name": "available",
  "DisplayName": "Available",
  "GroupMembershipStrategy": "AUTOADD"
}
```

**Relationships:**
- Belongs to `AvailabilityProfile`

---

### AvailabilityLog

Audit log for availability state changes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| UserID | int | Yes | User ID |
| UserName | string | Yes | User name |
| AvailabilityProfileID | int | Yes | Profile ID |
| AvailabilityProfileName | string | Yes | Profile name |
| AvailabilityStateID | int | Yes | State ID |
| AvailabilityStateName | string | Yes | State name |
| AvailabilityStateDisplayName | string | Yes | State display name |

**Example JSON:**
```json
{
  "OrgID": 1001,
  "UserID": 12345,
  "UserName": "john.smith",
  "AvailabilityProfileID": 1,
  "AvailabilityProfileName": "Standard Agent Profile",
  "AvailabilityStateID": 101,
  "AvailabilityStateName": "available",
  "AvailabilityStateDisplayName": "Available"
}
```

---

### UserCTIHeartbeat

CTI (Computer Telephony Integration) availability heartbeat tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| UserID | int | Yes | User ID |
| AppContext | string | Yes | App context and type identifier |
| OfflineAvailabilityStateID | int | No | Target offline availability state ID |
| OfflineAvailabilityTime | time | No | Time of day to go offline automatically |
| LastHeartbeat | datetime | Yes | Last heartbeat timestamp |

**Example JSON:**
```json
{
  "OrgID": 1001,
  "UserID": 12345,
  "AppContext": "CTI:Desktop",
  "OfflineAvailabilityStateID": 102,
  "OfflineAvailabilityTime": "18:00:00",
  "LastHeartbeat": "2024-01-15 10:30:00"
}
```

**Use Cases:**
- Detecting when CTI client disconnects
- Automatically changing availability state when client goes offline
- Scheduled availability changes (e.g., end of shift)

---

### CallCenterLoginHistory

Audit log for call center agent login/logout events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| GroupID | int | Yes | Call center group ID |
| UserID | int | Yes | User/agent ID |
| Time | datetime | Yes | Event timestamp |
| State | enum | Yes | Login state (IN/OUT) |
| Reason | string | No | Logout reason |

**Example JSON:**
```json
{
  "GroupID": 5001,
  "UserID": 12345,
  "Time": "2024-01-15 09:00:00",
  "State": "IN",
  "Reason": null
}
```

```json
{
  "GroupID": 5001,
  "UserID": 12345,
  "Time": "2024-01-15 17:30:00",
  "State": "OUT",
  "Reason": "End of shift"
}
```

---

## Storage & Notification Models

### KeyValueStorage

Generic key-value storage for user-specific data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| KID | int | Yes | Primary key |
| UserID | int | Yes | Foreign key to Users table |
| Context | string | Yes | Context/namespace for the key |
| Key | string | Yes | Key name within context |
| Data | string | Yes | Stored value data |
| Hash | string | Yes | SHA1 hash of the data value |
| Expires | datetime | No | Expiration timestamp (YYYYMMDDHHMMSS format) |

**Validation Rules:**
- Combination of `UserID`, `Context`, and `Key` must be unique
- `Hash` is automatically computed from `Data`
- Expired entries may be automatically purged

**Example JSON:**
```json
{
  "KID": 50001,
  "UserID": 12345,
  "Context": "preferences",
  "Key": "dashboard_layout",
  "Data": "{\"columns\":3,\"widgets\":[\"calls\",\"messages\",\"contacts\"]}",
  "Hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
  "Expires": "20241231235959"
}
```

**Use Cases:**
- User preferences storage
- Temporary data caching
- Application state persistence

---

### NotificationMap

Maps notifications to users with delivery preferences.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| NID | int | Yes | Notification ID |
| UserID | int | Yes | User ID |
| VisualResponse | enum | No | Visual response type (None, etc.) |
| Mode | string | No | Notification mode |

**Example JSON:**
```json
{
  "NID": 7001,
  "UserID": 12345,
  "VisualResponse": "None",
  "Mode": "email"
}
```

---

### Notifications

System notification records.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| NID | int | Yes | Primary key notification ID |
| StartTime | datetime | Yes | Notification start/active time |
| Expires | datetime | No | Notification expiration |

**Example JSON:**
```json
{
  "NID": 7001,
  "StartTime": "2024-01-15 00:00:00",
  "Expires": "2024-01-31 23:59:59"
}
```

**Relationships:**
- Has many `NotificationMap` entries for user targeting

---

## Data Connector Models

### DataConnectorCredentials

Credentials and configuration for external data connectors.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DCCID | int | Yes | Primary key data connector config ID |
| Name | string | Yes | Connector name |
| OrgID | int | No | Organization ID |
| Type | string | No | Connector type (e.g., SalesForce) |
| ResourceID | string | No | External resource ID |

**Example JSON:**
```json
{
  "DCCID": 2001,
  "Name": "Salesforce Production",
  "OrgID": 1001,
  "Type": "SalesForce",
  "ResourceID": "00D5g00000ABC123"
}
```

---

### DataConnectorForeignIdMap

Maps data connectors to foreign/external IDs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| DCCID | int | Yes | Data connector config ID |
| ConnectedApp | string | Yes | Connected application name |
| ForeignID | string | Yes | External system foreign ID |

**Example JSON:**
```json
{
  "OrgID": 1001,
  "DCCID": 2001,
  "ConnectedApp": "SalesforceService",
  "ForeignID": "0015g00000XYZ789"
}
```

---

### DataConnectorDependencies

Tracks items associated with data connectors for synchronization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| DCCID | int | Yes | Data connector config ID |
| ConnectedApp | string | Yes | Connected application name |
| LandLine_CountryCode | string | No | Landline country code |
| LandLine_Number | string | No | Landline number |
| SIMID | int | No | SIM ID reference |
| VSIMID | int | No | Virtual SIM ID reference |
| TrunkID | int | No | SIP Trunk ID reference |
| UserID | int | No | User ID reference |
| SyncStatus | enum | No | Sync status (Changed, Delete, etc.) |

**Example JSON:**
```json
{
  "OrgID": 1001,
  "DCCID": 2001,
  "ConnectedApp": "SalesforceService",
  "LandLine_CountryCode": null,
  "LandLine_Number": null,
  "SIMID": null,
  "VSIMID": null,
  "TrunkID": null,
  "UserID": 12345,
  "SyncStatus": "Changed"
}
```

---

## Client Directory Models

### ClientDirectory

Client directory entry for contact matching.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Number | E.164 | Yes | Phone number in E.164 format |
| OrgID | int | Conditional | Organization ID (null for user-level) |
| UserID | int | Conditional | User ID (null for org-level) |
| Sensitivity | string | Yes | Business or Private |
| Description | string | No | Description of the contact |

**Validation Rules:**
- `Number` must be in E.164 format
- Either `OrgID` or `UserID` must be set (determines scope)
- `Sensitivity` must be "Business" or "Private"

**Example JSON:**
```json
{
  "Number": "+447700900123",
  "OrgID": 1001,
  "UserID": null,
  "Sensitivity": "Business",
  "Description": "Main Reception"
}
```

---

### DirectoryEntry

Directory entry input for XML operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Scope | string | Yes | Org or User scope |
| ID | UINT | Yes | Scope ID (OrgID or UserID) |
| Delete | string | No | Delete flag |

**Example JSON:**
```json
{
  "Scope": "Org",
  "ID": 1001,
  "Delete": null
}
```

---

### DirectoryNumber

Phone number entry within a directory.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Val | E.164 | Yes | Phone number |
| Sens | string | Yes | Sensitivity (Business/Private) |
| Desc | string | No | Description |
| Delete | string | No | Delete flag |

**Example JSON:**
```json
{
  "Val": "+447700900123",
  "Sens": "Business",
  "Desc": "Sales Hotline",
  "Delete": null
}
```

---

## Client Access Models

### ClientAccess

IP-based access control for specific client products.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | UINT | Yes | Organization ID |
| Product | ANY | Yes | Product name (Flex Portal, QueueMon, CTI) |
| Mode | ANY | Yes | Access mode |
| IPs | ANY | No | Comma-separated list of allowed IP addresses |

**Example JSON:**
```json
{
  "OrgID": 1001,
  "Product": "CTI",
  "Mode": "Whitelist",
  "IPs": "192.168.1.0/24,10.0.0.1,10.0.0.2"
}
```

**Use Cases:**
- Restricting CTI client access to office IP ranges
- Limiting admin portal access to VPN addresses
- Per-product access control

---

## Domain Models

### Domain / Domains

SIP domain configuration for organizations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DMID | int | Yes | Primary key domain ID |
| OrgID | int | Yes | Organization ID |
| Domain | string | Yes | Domain name |
| Default | enum | Yes | Whether this is the default domain (YES/NO) |

**Validation Rules:**
- `Domain` must be unique globally
- Only one domain per org can have `Default` = YES

**Example JSON:**
```json
{
  "DMID": 3001,
  "OrgID": 1001,
  "Domain": "acme.sip.platform.com",
  "Default": "YES"
}
```

**Relationships:**
- Belongs to `Orgs`
- Referenced by `Devices` and `SIPURI`

---

## Common Patterns

### User Authentication Flow

1. Client submits credentials
2. System looks up `Users` by `UserName`
3. `UserSecurity` record retrieved for password verification
4. Password hash compared using `HashAlgIter`, `Salt`, and `EncPwd`
5. On success, `SessionsX` record created with token
6. `FailCount` incremented on failure, reset on success

### Permission Evaluation

1. Load all `Permission` records for user's `OwnerID`
2. Resolve `TargetID` special values based on org hierarchy
3. Load `BasePermission` bit definitions
4. Apply bitmask operations for CRUD permissions
5. Evaluate `Polarity` (Allow/Deny) with deny taking precedence

### Group Membership

1. `GroupMaps` links entities to groups
2. `Primary` flag indicates user's main group
3. `IgnoreCalls` controls call routing inclusion
4. Changes logged to `GroupMapsLog` for audit
5. Nested groups supported via `GroupID` field