# Billing & Audit Models

This document covers the data models used for billing processes, API auditing, error logging, and policy schemas in the schema-api service.

## Overview

The billing and audit models provide comprehensive tracking and management for:
- **Direct Debit Processing**: ADDAC and ARUDD records for UK Direct Debit scheme compliance
- **API Auditing**: Request logging, error tracking, and access policies
- **Billing Operations**: Process scheduling and status monitoring
- **Brand Management**: Multi-tenant brand configuration

## Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│   APIPolicy     │         │    APIAudit     │
│  (IP/Org ACL)   │────────▶│ (Request Logs)  │
└─────────────────┘         └─────────────────┘
                                    │
                                    ▼
                            ┌─────────────────┐
                            │  APIErrorLog    │
                            │ (Error Details) │
                            └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│     ADDAC       │         │     ARUDD       │
│ (DD Amendments) │         │ (Unpaid DD)     │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
            ┌─────────────────┐
            │ BillingProcesses│
            │  (Scheduling)   │
            └─────────────────┘

┌─────────────────┐
│ BrandManagement │──────▶ Organization Configuration
└─────────────────┘
```

---

## API Audit Models

### APIAudit

Comprehensive audit log for tracking all API requests made to the system. Essential for security monitoring, debugging, and compliance reporting.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Time` | timestamp | Yes | Timestamp when the API call was made |
| `SessID` | int(10) unsigned | Yes | Session ID associated with the request |
| `UserID` | int(11) | Yes | User ID who initiated the API call |
| `IPAddress` | varchar(15) | Yes | IPv4 address of the requester |
| `Command` | varchar(128) | Yes | API command/endpoint that was executed |
| `Method` | enum | Yes | HTTP method: `GET`, `POST`, `PUT`, `DELETE` |
| `Parameters` | text | No | Request parameters (query string or body) |
| `ResponseCode` | smallint(5) unsigned | Yes | HTTP response code returned |

#### Validation Rules

- `IPAddress` must be a valid IPv4 address format
- `Method` must be one of the four allowed HTTP methods
- `ResponseCode` should be a valid HTTP status code (100-599)
- `Time` defaults to current timestamp if not provided

#### Example JSON

```json
{
  "Time": "2024-01-15T14:32:45Z",
  "SessID": 8847291,
  "UserID": 12345,
  "IPAddress": "192.168.1.100",
  "Command": "/api/v2/organizations/5001/users",
  "Method": "GET",
  "Parameters": "{\"limit\":50,\"offset\":0,\"status\":\"active\"}",
  "ResponseCode": 200
}
```

#### Relationships

- **SessID** → Links to active session management
- **UserID** → References the Users table (documented in [permissions-models.md](permissions-models.md))
- **OrgID** → Implicitly linked via UserID for organization-level reporting

#### Common Use Cases

1. **Security Auditing**: Track who accessed what data and when
2. **API Usage Analytics**: Monitor endpoint popularity and performance
3. **Debugging**: Trace failed requests and identify error patterns
4. **Compliance Reporting**: Generate access logs for regulatory requirements

---

### APIErrorLog

Dedicated table for logging API errors. Provides detailed error tracking separate from the main audit log.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `EID` | int(10) unsigned | Yes | Error ID (primary key, auto-increment) |

#### Validation Rules

- `EID` is auto-generated and cannot be manually set
- Additional error detail fields may be stored in related tables or as JSON

#### Example JSON

```json
{
  "EID": 1542789
}
```

#### Relationships

- **EID** → May link to extended error detail tables
- Typically correlated with **APIAudit** records via timestamp or session ID

#### Common Use Cases

1. **Error Tracking**: Central registry for all API errors
2. **Alerting Integration**: Trigger notifications on new error entries
3. **Error Rate Monitoring**: Track error frequency over time

---

### APIPolicy

Defines access control policies based on IP address and organization combinations. Controls API permission levels for external integrations.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `IPAddress` | varchar(15) | Yes | IPv4 address to apply policy to (primary key part) |
| `OrgID` | int(10) unsigned | Yes | Organization ID (primary key part) |
| `PermissionLevel` | enum | Yes | Access level: `DENY`, `LOW`, `MEDIUM`, `FULL` |

#### Validation Rules

- Composite primary key: `IPAddress` + `OrgID` must be unique
- `IPAddress` must be valid IPv4 format
- `OrgID` must reference a valid organization
- `PermissionLevel` determines API access scope:
  - `DENY`: Block all API access
  - `LOW`: Read-only access to basic endpoints
  - `MEDIUM`: Read/write access to non-sensitive data
  - `FULL`: Complete API access including admin functions

#### Example JSON

```json
{
  "IPAddress": "203.45.67.89",
  "OrgID": 5001,
  "PermissionLevel": "MEDIUM"
}
```

#### Relationships

- **OrgID** → References organization configuration
- Used by **APIAudit** to validate incoming requests

#### Common Use Cases

1. **IP Whitelisting**: Allow specific IPs full access for trusted integrations
2. **Partner Access Control**: Grant limited access to third-party systems
3. **Security Lockdown**: Deny access from suspicious IP addresses
4. **Multi-tenant Isolation**: Different policies per organization

---

### BasePermissions

Defines the foundational permission structure for API access control. Maps actions to bit positions for efficient permission checking.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Object` | varchar(30) | Yes | Object/resource name (primary key part) |
| `PType` | enum | Yes | Permission type: `Action` or `List` |
| `Action` | varchar(32) | Yes | Specific action name (primary key part) |
| `Bit` | int(10) unsigned | Yes | Bit position for permission flag (primary key part) |
| `Fields` | text | No | Associated fields this permission affects |

#### Validation Rules

- Composite primary key: `Object` + `Action` + `Bit`
- `Bit` positions must be unique within an Object for efficient bitwise operations
- `PType` determines how the permission is evaluated:
  - `Action`: Single operation permission
  - `List`: Permission to view collections

#### Example JSON

```json
{
  "Object": "Organization",
  "PType": "Action",
  "Action": "Create",
  "Bit": 1,
  "Fields": "Name,Status,BillingContact,Address"
}
```

```json
{
  "Object": "Users",
  "PType": "List",
  "Action": "ViewAll",
  "Bit": 4,
  "Fields": "UserID,Email,FirstName,LastName,Status"
}
```

#### Relationships

- Referenced by role and user permission assignments
- Links to **APIPolicy** for comprehensive access control

#### Common Use Cases

1. **Role Definition**: Build roles from combinations of base permissions
2. **Fine-grained Access**: Control access at field level
3. **Permission Inheritance**: Base permissions cascade through role hierarchy

---

## Billing Process Models

### BillingProcesses

Tracks the status and scheduling of automated billing processes. Provides operational visibility into billing system health.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `BPID` | int(11) | Yes | Billing process ID (primary key, auto-increment) |
| `BillingProcess` | varchar(20) | Yes | Name/identifier of the billing process |
| `Status` | enum | Yes | Current status: `Running` or `Not Running` |
| `FrequencySecs` | int(11) | Yes | How often the process runs (in seconds) |
| `LastRun` | datetime | No | Timestamp of the most recent execution |
| `LastRunSuccessful` | enum | No | Whether last run completed successfully: `Yes` or `No` |
| `LastRunRunTime` | int(11) | No | Duration of last run in seconds |
| `RunTimes` | int(11) | No | Total number of times process has run |
| `AverageRunTime` | double | No | Average execution time across all runs |

#### Validation Rules

- `BPID` is auto-generated
- `FrequencySecs` must be positive; typical values: 3600 (hourly), 86400 (daily)
- `AverageRunTime` is calculated: `TotalRunTime / RunTimes`

#### Example JSON

```json
{
  "BPID": 1,
  "BillingProcess": "InvoiceGeneration",
  "Status": "Not Running",
  "FrequencySecs": 86400,
  "LastRun": "2024-01-15T02:00:00Z",
  "LastRunSuccessful": "Yes",
  "LastRunRunTime": 1847,
  "RunTimes": 365,
  "AverageRunTime": 1623.45
}
```

```json
{
  "BPID": 2,
  "BillingProcess": "DDCollection",
  "Status": "Running",
  "FrequencySecs": 3600,
  "LastRun": "2024-01-15T14:00:00Z",
  "LastRunSuccessful": "Yes",
  "LastRunRunTime": 234,
  "RunTimes": 8760,
  "AverageRunTime": 198.7
}
```

#### Relationships

- Processes **ADDAC** and **ARUDD** records
- May trigger updates to organization billing status

#### Common Use Cases

1. **Operations Dashboard**: Monitor billing system health
2. **Alerting**: Detect failed or stuck processes
3. **Capacity Planning**: Analyze run times for scaling decisions
4. **Audit Trail**: Track when billing operations occur

---

## Direct Debit Models

### ADDAC

Stores ADDAC (Automated Direct Debit Amendment and Cancellation) records. Part of the UK Bacs Direct Debit scheme for handling instruction changes.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `OrgID` | int(10) unsigned | Yes | Organization ID owning this record |
| `ADDACFileID` | int(11) | Yes | ADDAC file identifier (primary key part) |
| `reference` | int(11) | Yes | Internal reference number (primary key part) |
| `reason-code` | varchar(10) | Yes | Bacs reason code for the change |
| `payer-reference` | varchar(40) | Yes | Customer/payer reference |
| `aosn` | int(11) | No | Originator's Service Number |
| `payer-name` | varchar(200) | Yes | Name of the payer |
| `payer-account-number` | int(11) | Yes | Payer's bank account number |
| `payer-sort-code` | int(11) | Yes | Payer's bank sort code |
| `effective-date` | date | Yes | Date the change takes effect |
| `Count` | int(11) | No | Record count within file |

#### Validation Rules

- Composite primary key: `ADDACFileID` + `reference`
- `reason-code` must be valid Bacs ADDAC code (0, C, N, R, etc.)
- `payer-sort-code` must be 6 digits
- `payer-account-number` must be 8 digits
- `effective-date` cannot be in the past

#### Common Reason Codes

| Code | Description |
|------|-------------|
| `0` | Instruction cancelled by payer |
| `C` | Account transferred to new bank |
| `N` | Payer deceased |
| `R` | Instruction amended |

#### Example JSON

```json
{
  "OrgID": 5001,
  "ADDACFileID": 20240115,
  "reference": 1001,
  "reason-code": "C",
  "payer-reference": "CUST-78432",
  "aosn": 123456,
  "payer-name": "John Smith",
  "payer-account-number": 12345678,
  "payer-sort-code": 204532,
  "effective-date": "2024-02-01",
  "Count": 1
}
```

#### Relationships

- **OrgID** → Organization owning the Direct Debit mandate
- Processed by **BillingProcesses** (DDCollection process)

#### Common Use Cases

1. **Mandate Updates**: Process bank account changes
2. **Cancellation Handling**: Disable billing when mandates are cancelled
3. **Compliance**: Maintain audit trail for Direct Debit scheme
4. **Customer Communication**: Trigger notifications for payment changes

---

### ARUDD

Stores ARUDD (Automated Return of Unpaid Direct Debit) records. Tracks failed Direct Debit collections that were returned unpaid.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `OrgID` | int(10) unsigned | Yes | Organization ID owning this record |
| `ARUDDFileID` | int(11) | Yes | ARUDD file identifier (primary key part) |
| `ref` | int(11) | Yes | Internal reference number (primary key part) |
| `returnDescription` | varchar(40) | Yes | Human-readable return reason |
| `originalProcessingDate` | date | Yes | Date the DD was originally processed |
| `payerReference` | varchar(40) | Yes | Customer/payer reference |
| `valueOf` | float | Yes | Amount of the failed transaction |
| `currency` | char(3) | Yes | Currency code (ISO 4217) |
| `transCode` | int(11) | Yes | Bacs transaction code |
| `returnCode` | varchar(10) | Yes | Bacs return reason code |
| `Count` | int(11) | No | Record count within file |

#### Validation Rules

- Composite primary key: `ARUDDFileID` + `ref`
- `currency` must be valid ISO 4217 code (typically `GBP`)
- `valueOf` must be positive
- `returnCode` must be valid Bacs ARUDD code

#### Common Return Codes

| Code | Description |
|------|-------------|
| `1` | Instruction cancelled |
| `2` | Payer deceased |
| `3` | Account transferred |
| `5` | No account |
| `6` | No instruction |
| `B` | Account closed |

#### Example JSON

```json
{
  "OrgID": 5001,
  "ARUDDFileID": 20240116,
  "ref": 5523,
  "returnDescription": "REFER TO PAYER",
  "originalProcessingDate": "2024-01-15",
  "payerReference": "CUST-78432",
  "valueOf": 149.99,
  "currency": "GBP",
  "transCode": 17,
  "returnCode": "6",
  "Count": 1
}
```

#### Relationships

- **OrgID** → Organization whose collection failed
- **payerReference** → Links to customer/subscription records
- Processed by **BillingProcesses** (ARUDDProcessing)

#### Common Use Cases

1. **Failed Payment Handling**: Update customer billing status
2. **Retry Logic**: Schedule re-collection attempts
3. **Customer Communication**: Send payment failure notifications
4. **Revenue Reporting**: Track unpaid amounts and recovery rates
5. **Risk Assessment**: Identify customers with repeated failures

---

## Brand Management

### BrandManagement

Configures brand-specific settings for multi-tenant white-label deployments. Each brand can have custom domain, portal, and configuration.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `BrandID` | tinyint(3) unsigned | Yes | Brand ID (primary key) |
| `HomeOrgID` | int(10) unsigned | Yes | Home organization ID (unique) |
| `BrandName` | varchar(64) | Yes | Display name of the brand |
| `Domain` | varchar(128) | Yes | Primary domain for the brand |
| `PortalURI` | varchar(128) | Yes | URI path for the brand's portal |
| `XML` | mediumtext | No | Extended XML configuration data |

#### Validation Rules

- `BrandID` must be unique (max 255 brands due to tinyint)
- `HomeOrgID` must be unique - one brand per home organization
- `Domain` must be valid domain format
- `PortalURI` must be valid URI path
- `XML` must be well-formed XML if provided

#### Example JSON

```json
{
  "BrandID": 1,
  "HomeOrgID": 1000,
  "BrandName": "TelecomPro",
  "Domain": "telecompro.com",
  "PortalURI": "/portal/telecompro",
  "XML": "<?xml version=\"1.0\"?><config><theme>blue</theme><logo>/assets/telecompro-logo.png</logo><supportEmail>support@telecompro.com</supportEmail><features><voicemail>true</voicemail><conferencing>true</conferencing></features></config>"
}
```

```json
{
  "BrandID": 2,
  "HomeOrgID": 2000,
  "BrandName": "CloudVoice",
  "Domain": "cloudvoice.io",
  "PortalURI": "/portal/cloudvoice",
  "XML": "<?xml version=\"1.0\"?><config><theme>green</theme><logo>/assets/cv-logo.svg</logo><supportEmail>help@cloudvoice.io</supportEmail></config>"
}
```

#### Relationships

- **HomeOrgID** → Root organization for this brand
- All sub-organizations inherit brand settings
- Affects portal theming and domain routing

#### Common Use Cases

1. **White-Label Deployments**: Resellers can have their own branded portals
2. **Domain Routing**: Route requests based on domain to correct brand
3. **Custom Theming**: Apply brand-specific UI configurations
4. **Feature Toggles**: Enable/disable features per brand via XML config

---

## Related Documentation

- [VoIP Models](voip-models.md) - Call data and voicemail records
- [Device Models](device-models.md) - Device configuration and monitoring
- [Permissions Models](permissions-models.md) - User and role permissions
- [Overview](README.md) - Complete model index