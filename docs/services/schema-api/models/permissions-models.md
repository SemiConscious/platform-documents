# Permissions & Configuration Models

This document covers the data models for access control, brand management, and data connector integrations in the schema-api service.

## Overview

These models manage:
- **API Access Control**: Permission policies, audit logging, and base permission definitions
- **Brand Management**: Multi-tenant branding and configuration
- **Data Connectors**: CRM integration credentials for external systems
- **Dial Plan Configuration**: Call routing policies and configurations

## Entity Relationships

```
BrandManagement (1) -----> (1) Organization (HomeOrgID)

APIPolicy (N) -----> (1) Organization (OrgID)
APIAudit (N) -----> (1) Session (SessID)
APIAudit (N) -----> (1) User (UserID)

DataConnectorCredentials (N) -----> (1) Organization (OrgID)

BasePermissions <-----> API Objects/Actions

DialPlanPolicies (N) -----> (1) Organization (OrgID)
DialPlanPolicies (N) -----> (1) User (UserID)
DialPlanItem (N) -----> (1) DialPlanPolicies (DPPID)
DialPlanItem (N) -----> (1) DialPlanItem (ParentDPIID) [self-referential]
```

---

## API Access Control Models

### APIPolicy

Defines API access permissions based on IP address and organization combinations. This model implements IP-based access control lists (ACLs) for API security.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| IPAddress | varchar(15) | Yes (PK) | IPv4 address to apply policy to |
| OrgID | int(10) unsigned | Yes (PK) | Organization ID for the policy scope |
| PermissionLevel | enum | Yes | Access level: `DENY`, `LOW`, `MEDIUM`, `FULL` |

#### Validation Rules
- `IPAddress` must be a valid IPv4 address format
- `OrgID` must reference a valid organization
- Composite primary key on (`IPAddress`, `OrgID`)
- Permission levels are hierarchical: DENY < LOW < MEDIUM < FULL

#### Example JSON

```json
{
  "IPAddress": "192.168.1.100",
  "OrgID": 1001,
  "PermissionLevel": "FULL"
}
```

#### Common Use Cases
- Whitelisting trusted office IP addresses for full API access
- Restricting third-party integrations to limited permissions
- Blocking suspicious IP addresses at the API level

---

### APIAudit

Comprehensive audit log tracking all API requests for security monitoring, debugging, and compliance purposes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Time | timestamp | Yes | Timestamp when the API call was made |
| SessID | int(10) unsigned | No | Session ID associated with the request |
| UserID | int(11) | No | User ID who initiated the API call |
| IPAddress | varchar(15) | No | Source IP address of the request |
| Command | varchar(128) | No | API endpoint/command that was executed |
| Method | enum | No | HTTP method: `GET`, `POST`, `PUT`, `DELETE` |
| Parameters | text | No | Request parameters (may be JSON or query string) |
| ResponseCode | smallint(5) unsigned | No | HTTP response status code returned |

#### Validation Rules
- `Time` defaults to current timestamp on insert
- `Method` must be one of the allowed HTTP verbs
- `ResponseCode` should be a valid HTTP status code (100-599)

#### Example JSON

```json
{
  "Time": "2024-01-15T14:32:45Z",
  "SessID": 89234,
  "UserID": 5421,
  "IPAddress": "10.0.0.55",
  "Command": "/api/v1/users/list",
  "Method": "GET",
  "Parameters": "{\"page\": 1, \"limit\": 50, \"status\": \"active\"}",
  "ResponseCode": 200
}
```

#### Common Use Cases
- Security incident investigation
- API usage analytics and reporting
- Compliance auditing and regulatory requirements
- Performance monitoring by tracking response patterns

---

### APIErrorLog

Stores API error events for debugging and monitoring purposes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| EID | int(10) unsigned | Yes (PK) | Auto-incrementing error ID |

#### Validation Rules
- `EID` is auto-generated on insert
- Additional error detail fields may exist (schema appears truncated)

#### Example JSON

```json
{
  "EID": 45892
}
```

> **Note**: This model appears to have additional fields not captured in the schema. Consult the database directly for complete field definitions.

---

### BasePermissions

Defines the foundational permission structure for API access control. This model maps objects and actions to specific bit positions for efficient permission checking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Object | varchar(30) | Yes (PK) | API object/resource name |
| PType | enum | Yes | Permission type: `Action` (single operation) or `List` (collection) |
| Action | varchar(32) | Yes (PK) | Specific action name (e.g., read, write, delete) |
| Bit | int(10) unsigned | Yes (PK) | Bit position for bitmask permission calculations |
| Fields | text | No | Associated field names this permission applies to |

#### Validation Rules
- Composite primary key on (`Object`, `Action`, `Bit`)
- `Bit` values must be unique within an object for proper bitmask operations
- `PType` determines how the permission is evaluated

#### Example JSON

```json
{
  "Object": "Users",
  "PType": "Action",
  "Action": "create",
  "Bit": 1,
  "Fields": "username,email,password,role"
}
```

```json
{
  "Object": "Reports",
  "PType": "List",
  "Action": "read",
  "Bit": 4,
  "Fields": "call_records,billing_summary,usage_stats"
}
```

#### Common Use Cases
- Defining granular API permissions for role-based access control
- Building permission bitmasks for efficient authorization checks
- Mapping permissions to specific data fields for field-level security

---

## Brand Management Models

### BrandManagement

Manages multi-tenant branding configuration, allowing different organizations to have customized portal appearances and settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| BrandID | tinyint(3) unsigned | Yes (PK) | Unique brand identifier |
| HomeOrgID | int(10) unsigned | Yes (Unique) | Home organization ID that owns this brand |
| BrandName | varchar(64) | No | Display name for the brand |
| Domain | varchar(128) | No | Primary domain associated with the brand |
| PortalURI | varchar(128) | No | URI path for the branded portal |
| XML | mediumtext | No | Full XML configuration for brand customization |

#### Validation Rules
- `BrandID` is the primary key (max 255 brands supported)
- `HomeOrgID` must be unique (one brand per organization)
- `Domain` should be a valid domain name format
- `XML` should contain valid XML configuration data

#### Example JSON

```json
{
  "BrandID": 5,
  "HomeOrgID": 2001,
  "BrandName": "Acme Communications",
  "Domain": "portal.acmecomm.com",
  "PortalURI": "/acme/portal",
  "XML": "<?xml version=\"1.0\"?><brand><logo>https://cdn.acmecomm.com/logo.png</logo><primaryColor>#003366</primaryColor><supportEmail>support@acmecomm.com</supportEmail><features><voicemail>enabled</voicemail><conferencing>enabled</conferencing></features></brand>"
}
```

#### Common Use Cases
- White-label portal deployments for resellers
- Customizing appearance per customer organization
- Managing feature flags and configurations per brand

---

## Data Connector Models

### DataConnectorCredentials

Stores credentials and configuration for external CRM integrations, enabling synchronization between the telephony platform and third-party systems.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DCCID | int(10) unsigned | Yes (PK) | Auto-incrementing credential ID |
| OrgID | int(10) unsigned | No | Organization ID that owns these credentials |
| Name | varchar(64) | No | Friendly name for the connector |
| Type | enum | No | CRM type: `SalesForce`, `MicrosoftDynamics`, `Sugar` |
| Server | varchar(256) | No | CRM server URL or endpoint |
| Username | varchar(64) | No | Authentication username |
| Password | varchar(64) | No | Authentication password (should be encrypted) |
| Restricted | enum | No | Access restriction flag: `Yes` or `No` |
| AccountType | varchar(32) | No | CRM account type (e.g., Enterprise, Professional) |
| Organization | varchar(64) | No | CRM organization/tenant name |
| AuthType | varchar(16) | No | Authentication method (e.g., OAuth, Basic) |
| Token | varchar(128) | No | OAuth or API token for authentication |

#### Validation Rules
- `DCCID` is auto-generated
- `Type` must match one of the supported CRM platforms
- `Server` should be a valid URL format
- Credentials should be stored encrypted (implementation detail)

#### Example JSON

```json
{
  "DCCID": 142,
  "OrgID": 3005,
  "Name": "Salesforce Production",
  "Type": "SalesForce",
  "Server": "https://na45.salesforce.com",
  "Username": "integration@company.com",
  "Password": "********",
  "Restricted": "No",
  "AccountType": "Enterprise",
  "Organization": "Company Corp",
  "AuthType": "OAuth",
  "Token": "00D5f000000XXXXX!AQEAQ..."
}
```

```json
{
  "DCCID": 143,
  "OrgID": 3005,
  "Name": "Dynamics CRM",
  "Type": "MicrosoftDynamics",
  "Server": "https://company.crm.dynamics.com",
  "Username": "crm-service@company.onmicrosoft.com",
  "Password": "********",
  "Restricted": "Yes",
  "AccountType": "Online",
  "Organization": "CompanyCRM",
  "AuthType": "OAuth",
  "Token": "eyJ0eXAiOiJKV1QiLC..."
}
```

#### Common Use Cases
- Click-to-dial integration with CRM systems
- Automatic call logging to customer records
- Screen pop with caller information from CRM
- Synchronizing contact data between systems

---

## Dial Plan Configuration Models

### DialPlanPolicies

Defines dial plan policies that control call routing behavior. Policies can be applied at organization or user levels.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DPPID | int(10) unsigned | Yes (PK) | Auto-incrementing policy ID |
| Name | varchar(64) | No | Policy name for identification |
| Status | enum | No | Policy status: `Enabled`, `Suspended`, `Draft` |
| Type | enum | No | Policy type: `Call`, `NonCall`, `System` |
| CurrentVersion | smallint(5) unsigned | No | Version number for change tracking |
| OrgID | int(10) unsigned | No | Organization this policy belongs to |
| UserID | int(11) | No | User who created/owns the policy |
| LockedBySessID | int(10) unsigned | No | Session ID holding edit lock |
| Created | datetime | No | Creation timestamp |

#### Validation Rules
- `DPPID` is auto-generated
- Only `Enabled` policies are active in call routing
- `LockedBySessID` prevents concurrent editing conflicts
- `Type` determines when the policy is evaluated:
  - `Call`: Applied during call processing
  - `NonCall`: Applied for non-call events
  - `System`: Global system-level policies

#### Example JSON

```json
{
  "DPPID": 501,
  "Name": "Business Hours Routing",
  "Status": "Enabled",
  "Type": "Call",
  "CurrentVersion": 3,
  "OrgID": 2001,
  "UserID": 1542,
  "LockedBySessID": null,
  "Created": "2023-06-15T09:30:00Z"
}
```

#### Common Use Cases
- Time-based call routing (business hours vs. after hours)
- Geographic routing based on caller location
- Feature code handling (e.g., *72 for call forwarding)
- Emergency service routing

---

### DialPlanItem

Individual items within a dial plan policy, forming a tree structure for complex routing logic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DPIID | int(10) unsigned | Yes (PK) | Dial plan item ID |
| TemplateID | int(10) unsigned | No | Reference to template this item uses |
| ParentDPIID | int(10) unsigned | No | Parent item ID for tree structure |
| SortOrder | int(10) unsigned | No | Order for processing multiple items |
| Name | varchar(48) | No | Item name/description |
| IsRegExp | enum | No | Whether destination is regex: `YES` or `NO` |
| DestinationNumber | varchar(32) | No | Target number for transfers/routing |
| Context | varchar(16) | No | Dial plan context (e.g., default, internal) |
| DependentDPPID | int(10) unsigned | No | Dependent policy that must be met |
| DefaultStart | enum | No | Marks this as default entry point: `YES` or null |
| Variables | varchar(4096) | No | XML configuration variables |
| LinkItems | varchar(4096) | No | XML defining linked items |
| UIInventory | varchar(4096) | No | XML for UI display properties |
| DPPID | int(10) unsigned | No | Parent policy ID |

#### Validation Rules
- `DPIID` is the primary key
- `ParentDPIID` creates hierarchical structure (null for root items)
- `SortOrder` determines evaluation sequence among siblings
- Only one item per policy should have `DefaultStart = 'YES'`

#### Example JSON

```json
{
  "DPIID": 10001,
  "TemplateID": 50,
  "ParentDPIID": null,
  "SortOrder": 1,
  "Name": "Check Business Hours",
  "IsRegExp": "NO",
  "DestinationNumber": null,
  "Context": "default",
  "DependentDPPID": null,
  "DefaultStart": "YES",
  "Variables": "<variables><var name=\"timezone\">America/New_York</var></variables>",
  "LinkItems": "<links><onSuccess>10002</onSuccess><onFailure>10003</onFailure></links>",
  "UIInventory": "<ui><x>100</x><y>50</y><icon>clock</icon></ui>",
  "DPPID": 501
}
```

```json
{
  "DPIID": 10002,
  "TemplateID": 75,
  "ParentDPIID": 10001,
  "SortOrder": 1,
  "Name": "Route to Sales Queue",
  "IsRegExp": "NO",
  "DestinationNumber": "8001",
  "Context": "queues",
  "DependentDPPID": null,
  "DefaultStart": null,
  "Variables": "<variables><var name=\"queue_timeout\">300</var></variables>",
  "LinkItems": null,
  "UIInventory": "<ui><x>200</x><y>100</y><icon>queue</icon></ui>",
  "DPPID": 501
}
```

#### Common Use Cases
- Building visual dial plan flows
- Conditional routing based on time, caller ID, or other criteria
- IVR menu construction
- Call queue and hunt group configuration

---

## Security Considerations

### Credential Storage
- `DataConnectorCredentials.Password` and `Token` fields should be encrypted at rest
- Consider using a secrets manager for production deployments
- Rotate credentials periodically

### Audit Compliance
- `APIAudit` records should be retained per compliance requirements
- Consider archiving old audit records to separate storage
- Implement log tamper detection mechanisms

### Permission Management
- Use `BasePermissions` with role-based access control
- Apply principle of least privilege when setting `APIPolicy` levels
- Regularly review and audit permission assignments

---

## Related Documentation

- [VoIP Models](voip-models.md) - Call handling and voicemail
- [Device Models](device-models.md) - SIP devices and provisioning
- [Billing & Audit Models](billing-audit-models.md) - Financial and process tracking
- [Overview](README.md) - Complete schema overview