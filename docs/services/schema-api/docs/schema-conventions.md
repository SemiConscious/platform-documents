# Schema Conventions

This document describes the coding standards and conventions used in schema definitions across the schema-api service. Understanding these conventions is essential for maintaining consistency and predictability when working with the data models.

## Overview

The schema-api follows a set of established naming conventions, data type patterns, and structural standards that ensure consistency across all models. These conventions apply to table naming, field naming, enumeration values, and relationship definitions.

## Table Naming Conventions

### General Patterns

| Pattern | Description | Examples |
|---------|-------------|----------|
| PascalCase | Primary entity tables use PascalCase | `Devices`, `BrandManagement`, `DialPlanPolicies` |
| UPPERCASE | Legacy or external system tables | `ADDAC`, `ARUDD` |
| snake_case | Specific subsystem tables (VoIP) | `voicemail_msgs`, `voicemail_prefs` |
| Plural Form | Collection tables use plural names | `Devices`, `BillingProcesses` |
| Compound Names | Related entities joined without separator | `DeviceMap`, `DeviceMonitoring`, `DevicesVars` |

### Table Name Suffixes

| Suffix | Purpose | Examples |
|--------|---------|----------|
| `Audit` | Logging and audit trail tables | `APIAudit` |
| `Log` | Error and event logging | `APIErrorLog` |
| `Map` | Mapping/junction tables | `DeviceMap` |
| `Monitoring` | Metrics and statistics | `DeviceMonitoring` |
| `Vars` | Configuration variables | `DevicesVars` |
| `Prefs` | User/entity preferences | `voicemail_prefs` |
| `Policies` | Rule and policy definitions | `DialPlanPolicies` |
| `Permissions` | Access control definitions | `BasePermissions` |
| `Credentials` | Authentication storage | `DataConnectorCredentials` |

## Primary Key Conventions

### Standard ID Fields

| Convention | Pattern | Examples |
|------------|---------|----------|
| Entity-specific ID | `{Entity}ID` | `DevID`, `DPPID`, `BrandID`, `DCCID` |
| Organization reference | `OrgID` | Used in nearly all tables |
| User reference | `UserID` | User ownership/association |
| Session reference | `SessID` | Session tracking |

### Composite Primary Keys

Many tables use composite primary keys for uniqueness:

```sql
-- Example: ADDAC table
PRIMARY KEY (ADDACFileID, reference)

-- Example: DeviceMonitoring table  
PRIMARY KEY (Hour, DevID)

-- Example: BasePermissions table
PRIMARY KEY (Object, Action, Bit)
```

### ID Abbreviation Patterns

| Abbreviation | Full Name | Context |
|--------------|-----------|---------|
| `ID` | Identifier | Generic identifier suffix |
| `DPIID` | Dial Plan Item ID | Dial plan items |
| `DPPID` | Dial Plan Policy ID | Dial plan policies |
| `DMID` | Domain ID | Domain references |
| `DCCID` | Data Connector Credential ID | CRM integrations |
| `BPID` | Billing Process ID | Billing operations |
| `EID` | Error ID | Error logging |

## Data Type Conventions

### Integer Types

| Type | Use Case | Range | Examples |
|------|----------|-------|----------|
| `tinyint(3) unsigned` | Small counters, flags | 0-255 | `BrandID`, `Rank`, `Calls` |
| `smallint(5) unsigned` | Version numbers, codes | 0-65535 | `CurrentVersion`, `ResponseCode` |
| `mediumint(8) unsigned` | Extensions, hours | 0-16M | `Extension`, `Hour`, `Duration` |
| `int(10) unsigned` | Standard IDs, costs | 0-4B | `OrgID`, `DevID`, `WCost` |
| `int(11)` | Signed integers, counts | ±2B | `UserID`, `Count`, `message_len` |
| `bigint(20) unsigned` | MAC addresses, large IDs | 0-18E | `MAC` |

### String Types

| Type | Use Case | Max Length | Examples |
|------|----------|------------|----------|
| `char(3)` | Fixed-length codes | 3 | `currency` |
| `varchar(10)` | Short codes | 10 | `reason-code`, `returnCode` |
| `varchar(15)` | IP addresses | 15 | `IPAddress` |
| `varchar(16)` | Short identifiers | 16 | `Section`, `AuthType`, `Context` |
| `varchar(32)` | Names, passwords | 32 | `Password`, `Val`, `Location`, `Action` |
| `varchar(64)` | Longer names | 64 | `BrandName`, `Name`, `Username` |
| `varchar(128)` | URLs, domains | 128 | `Domain`, `PortalURI`, `Command`, `Token` |
| `varchar(255)` | General text | 255 | VoIP fields (`username`, `domain`, `file_path`) |
| `varchar(256)` | Long URLs | 256 | `Server` |
| `varchar(4096)` | XML/JSON data | 4096 | `Variables`, `LinkItems`, `UIInventory` |
| `text` | Large text | 64KB | `Parameters`, `Fields`, `Val_Device` |
| `mediumtext` | XML configuration | 16MB | `XML` |

### Temporal Types

| Type | Use Case | Format | Examples |
|------|----------|--------|----------|
| `timestamp` | Auto-updated times | `YYYY-MM-DD HH:MM:SS` | `Time`, `Started` |
| `datetime` | Manual timestamps | `YYYY-MM-DD HH:MM:SS` | `Created`, `LastRun` |
| `date` | Date only | `YYYY-MM-DD` | `effective-date`, `originalProcessingDate` |
| `int(11)` (epoch) | Unix timestamps | Seconds since 1970 | `created_epoch`, `read_epoch` |

### Enumeration Patterns

Standard enum values follow consistent patterns:

#### Status Enumerations
```sql
-- Binary status
Status: enum('Enabled','Suspended')

-- Process status
Status: enum('Running','Not Running')

-- Policy status with draft
Status: enum('Enabled','Suspended','Draft')
```

#### Yes/No Enumerations
```sql
-- Uppercase pattern
AllowRoaming: enum('YES','NO')
Provisioned: enum('YES','NO')
IsRegExp: enum('YES','NO')

-- Capitalized pattern
LastRunSuccessful: enum('Yes','No')
Restricted: enum('Yes','No')
```

#### Type Enumerations
```sql
-- Device types
DeviceType: enum('Device','SIPTrunk')

-- Permission types
PType: enum('Action','List')

-- Policy types
Type: enum('Call','NonCall','System')

-- Phone number types
Type: enum('Mobile','Home','Work','Other','Unknown')
```

#### Access Level Enumerations
```sql
-- Permission levels
PermissionLevel: enum('DENY','LOW','MEDIUM','FULL')

-- Voicemail access
AccessVM: enum('Allow','RequirePIN','Block')

-- Ownership
Ownership: enum('Active','Passive')
```

#### HTTP Methods
```sql
Method: enum('GET','POST','PUT','DELETE')
```

## Field Naming Conventions

### Common Field Names

| Field Name | Purpose | Type | Used In |
|------------|---------|------|---------|
| `OrgID` | Organization ownership | `int(10) unsigned` | Most tables |
| `UserID` | User ownership | `int(11)` | User-related tables |
| `Status` | Entity status | `enum(...)` | Entity tables |
| `Created` | Creation timestamp | `datetime` | Tracked entities |
| `Name` | Display name | `varchar(64)` | Named entities |
| `Desc` | Description | `varchar(32)` | Descriptive entities |
| `Type` | Entity type | `enum(...)` | Typed entities |

### Camel Case vs Snake Case

| Convention | Context | Examples |
|------------|---------|----------|
| PascalCase | Primary fields | `OrgID`, `DevID`, `BrandName`, `PortalURI` |
| camelCase | External system fields | `payerReference`, `transCode`, `returnCode` |
| snake_case | VoIP subsystem | `created_epoch`, `cid_name`, `file_path` |
| kebab-case | Legacy imports | `reason-code`, `effective-date`, `payer-name` |

### Reference Field Patterns

```sql
-- Direct foreign keys
OrgID: int(10) unsigned      -- Organization reference
UserID: int(11)              -- User reference
DevID: int(10) unsigned      -- Device reference
DPPID: int(10) unsigned      -- Policy reference

-- Self-referential keys
ParentDPIID: int(10) unsigned    -- Parent item reference
DependentDPPID: int(10) unsigned -- Dependent policy

-- Mapping references
SIPID: int(10) unsigned      -- SIP URI reference (in DeviceMap)
```

## Constraint Conventions

### Unique Constraints

```sql
-- Single field unique
MAC: bigint(20) unsigned UNIQUE        -- Device MAC address
HomeOrgID: int(10) unsigned UNIQUE     -- Brand home organization

-- Composite primary keys serve as unique constraints
PRIMARY KEY (ADDACFileID, reference)
```

### Index Naming (Implied)

Standard indices are implied through:
- Primary key definitions
- Foreign key references
- Unique constraints
- Commonly queried fields

## JSON Field Conventions

### Standard JSON Structure

Fields containing structured data follow XML or JSON patterns:

```sql
-- XML configuration storage
Variables: varchar(4096)     -- Dial plan variables
LinkItems: varchar(4096)     -- Link configuration
UIInventory: varchar(4096)   -- UI display metadata
XML: mediumtext              -- Full XML configuration
```

### Example JSON/XML Patterns

```json
{
  "Variables": "<variables><var name='timeout' value='30'/></variables>",
  "LinkItems": "<links><link target='voicemail'/></links>",
  "UIInventory": "<ui><position x='100' y='200'/></ui>"
}
```

## Relationship Conventions

### One-to-Many Patterns

```
Organization (OrgID) -> Devices (many)
Organization (OrgID) -> DataConnectorCredentials (many)
Organization (OrgID) -> DialPlanPolicies (many)
Device (DevID) -> DevicesVars (many)
Device (DevID) -> DeviceMonitoring (many)
```

### Self-Referential Patterns

```
DialPlanItem.ParentDPIID -> DialPlanItem.DPIID (tree structure)
DialPlanItem.DependentDPPID -> DialPlanPolicies.DPPID (dependency)
```

### Junction Table Patterns

```
DeviceMap: SIPID <-> DevID (with timestamp)
AssocNumbers: Val <-> OrgID/UserID (with metadata)
```

## Versioning Conventions

### Version Tracking

```sql
-- Simple version counter
CurrentVersion: smallint(5) unsigned

-- Draft/Published workflow
Status: enum('Enabled','Suspended','Draft')
```

## Audit Conventions

### Timestamp Fields

| Field | Type | Purpose |
|-------|------|---------|
| `Time` | `timestamp` | Event timestamp |
| `Created` | `datetime` | Creation time |
| `Started` | `timestamp` | Process start |
| `LastRun` | `datetime` | Last execution |

### Audit Trail Fields

```sql
-- User tracking
UserID: int(11)              -- Who performed action
SessID: int(10) unsigned     -- Session context
IPAddress: varchar(15)       -- Client IP

-- Operation tracking
Command: varchar(128)        -- Action performed
Method: enum(...)            -- HTTP method
Parameters: text             -- Request details
ResponseCode: smallint(5)    -- Result code
```

## Cost and Currency Conventions

### Monetary Values

```sql
-- Integer representation (in minor units)
WCost: int(10) unsigned      -- Wholesale cost (pennies/cents)
RCost: int(10) unsigned      -- Retail cost (pennies/cents)

-- Float for external values
valueOf: float               -- Transaction value

-- Currency codes
currency: char(3)            -- ISO 4217 code (GBP, USD, EUR)
```

## Summary of Key Conventions

| Category | Convention | Example |
|----------|------------|---------|
| Table names | PascalCase, plural | `Devices`, `DialPlanPolicies` |
| Primary keys | `{Entity}ID` | `DevID`, `DPPID` |
| Foreign keys | Match source table | `OrgID`, `DevID` |
| Status fields | Title case enum | `enum('Enabled','Suspended')` |
| Boolean fields | YES/NO or Yes/No | `enum('YES','NO')` |
| Timestamps | `datetime` or `timestamp` | `Created`, `Time` |
| IP addresses | `varchar(15)` | `IPAddress` |
| MAC addresses | `bigint(20) unsigned` | `MAC` |
| Currency | `char(3)` | `currency` |
| URLs | `varchar(128-256)` | `Server`, `PortalURI` |

---

## Related Documentation

- [Data Models Overview](models/README.md) - Complete model reference
- [VoIP Models](models/voip-models.md) - Voice and messaging models
- [Device Models](models/device-models.md) - Device configuration models
- [Billing & Audit Models](models/billing-audit-models.md) - Financial and logging models
- [Permissions Models](models/permissions-models.md) - Access control models