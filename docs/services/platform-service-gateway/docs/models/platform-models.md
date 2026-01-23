# Platform Integration Models

This document covers data models specific to CRM platform integrations in the Platform Service Gateway. These models define the structures used for connecting to and interacting with various third-party platforms including Salesforce, SugarCRM, Microsoft Dynamics, Zendesk, Oracle Fusion, GoodData, Workbooks, and MPP Global.

> **Related Documentation:**
> - [Session Models](session-models.md) - Authentication session storage models
> - [Feed Models](feed-models.md) - Feed configuration and message models
> - [API Response Models](api-response-models.md) - Standard API response structures

---

## Table of Contents

- [Overview](#overview)
- [Salesforce Integration](#salesforce-integration)
- [SugarCRM Integration](#sugarcrm-integration)
- [Microsoft Dynamics Integration](#microsoft-dynamics-integration)
- [Zendesk Integration](#zendesk-integration)
- [Oracle Fusion Integration](#oracle-fusion-integration)
- [GoodData Integration](#gooddata-integration)
- [Workbooks Integration](#workbooks-integration)
- [MPP Global Integration](#mpp-global-integration)
- [LDAP Integration](#ldap-integration)
- [Entity Relationships](#entity-relationships)

---

## Overview

Platform integration models facilitate authentication, data exchange, and session management with external CRM and business platforms. Each integration typically includes:

1. **Feed Payload Model** - XML structure for initial authentication
2. **Session Model** - Database storage for active sessions
3. **API Class Model** - Runtime configuration for API operations
4. **Resource Models** - Platform-specific data structures

---

## Salesforce Integration

### Sgapi_Salesforce

General class that supports the Salesforce API for message gateway operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SforceConnection | object | Yes | Salesforce connection object instance |
| accounttype | string | Yes | Account type: `partner` or `enterprise` |
| response_timeout | integer | Yes | Time limit in seconds for API responses |
| aDbRow | array | Yes | Database row with connection configuration |
| oDB | Database | Yes | Database connection object |
| aTypeFieldQueryError | array | No | Array of type/field query error codes |
| token | string | Yes | Authentication token |
| feedId | string | Yes | Feed identifier |

**Validation Rules:**
- `accounttype` must be either `partner` or `enterprise`
- `response_timeout` must be a positive integer
- `token` must be a valid 40-character SHA1 hash

**Example:**
```json
{
  "SforceConnection": {},
  "accounttype": "partner",
  "response_timeout": 30,
  "aDbRow": {
    "SFToken": "00D5g00000XXXX!AQQXX...",
    "Location": "https://na1.salesforce.com/services/Soap/u/52.0"
  },
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "feedId": "12345"
}
```

---

### Auth_Salesforce

Authorization class that supports the Salesforce API authentication flow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SforceConnection | object | Yes | Salesforce connection object |
| dbConn | Database | Yes | Database connection object |
| response_timeout | integer | Yes | Response timeout value in seconds |
| sApexWsdlFile | string | No | Path to Apex WSDL file |
| sApexWsdlURI | string | No | Apex WSDL URI |

**Example:**
```json
{
  "SforceConnection": {},
  "dbConn": {},
  "response_timeout": 30,
  "sApexWsdlFile": "/var/wsdl/apex.wsdl.xml",
  "sApexWsdlURI": "https://na1.salesforce.com/services/wsdl/apex"
}
```

---

### Sessions_Salesforce

Database table for storing Salesforce session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID (foreign key to Sessions table) |
| AuthType | string | No | Authentication type (e.g., `oauth`) |
| SFToken | string | Yes | Salesforce session token |
| Location | string | Yes | Salesforce API location URL |
| WSDL | string | Yes | WSDL type: `partner` or `enterprise` |
| ApexWsdlURI | string | No | Apex WSDL URI |
| ApexWsdlPath | string | No | Apex WSDL file path |
| Timeout | integer | Yes | Session timeout in minutes |

**Validation Rules:**
- `SID` must reference a valid session in the Sessions table
- `WSDL` must be either `partner` or `enterprise`
- `Timeout` must be a positive integer

**Example:**
```json
{
  "SID": 1001,
  "AuthType": "oauth",
  "SFToken": "00D5g00000XXXX!AQQXX.9kLM8nPqRsTuVwXyZ",
  "Location": "https://na1.salesforce.com/services/Soap/u/52.0/00D5g00000XXXX",
  "WSDL": "partner",
  "ApexWsdlURI": "https://na1.salesforce.com/services/wsdl/apex",
  "ApexWsdlPath": "/var/cache/wsdl/apex_00D5g.wsdl",
  "Timeout": 120
}
```

---

### tokentosfsession

Database table mapping tokens to Salesforce sessions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Token | string | Yes | Authentication token |
| FeedId | integer | Yes | Feed identifier |
| Location | string | Yes | Salesforce endpoint location |
| SessionId | string | Yes | Salesforce session ID |
| wsdl | string | Yes | WSDL file path (partner or enterprise) |

**Example:**
```json
{
  "Token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "FeedId": 12345,
  "Location": "https://na1.salesforce.com/services/Soap/u/52.0",
  "SessionId": "00D5g00000XXXX!AQQXX.9kLM8nPqRsTuVwXyZ",
  "wsdl": "partner.wsdl.xml"
}
```

---

### Contact_Salesforce

Contact class that supports the Salesforce API for contact queries and activities.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SforceConnection | object | Yes | Salesforce connection object |
| accounttype | string | Yes | Salesforce account type: `partner` or `enterprise` |
| dbConn | object | Yes | Database connection object |
| token | string | Yes | Session token |

**Example:**
```json
{
  "SforceConnection": {},
  "accounttype": "enterprise",
  "dbConn": {},
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

---

### Task_Salesforce

Salesforce task/activity class for adding tasks to Salesforce accounts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SforceConnection | object | Yes | Salesforce connection object |
| accounttype | string | Yes | Type of account: `partner` or `enterprise` |
| dbConn | object | Yes | Database connection object |
| token | string | Yes | Session token |

**Example:**
```json
{
  "SforceConnection": {},
  "accounttype": "partner",
  "dbConn": {},
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

---

### Task_Salesforce_Payload

XML payload structure for Salesforce task/activity addition.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subject | string | Yes | Task subject |
| comment | string | No | Comment for task (maps to Description) |
| feedid | integer | Yes | Feed identifier |
| username | string | No | Salesforce username to assign task ownership |

**Example:**
```json
{
  "subject": "Follow up on sales inquiry",
  "comment": "Customer requested pricing information for enterprise plan",
  "feedid": 12345,
  "username": "john.doe@company.com"
}
```

---

### Salesforce_Task_Fields

Internal Salesforce Task object fields used when creating tasks.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Subject | string | Yes | Task subject |
| Description | string | No | Task description/comment |
| Status | string | Yes | Task status |
| Priority | string | Yes | Task priority |
| OwnerId | string | No | Salesforce user ID for task owner |

**Validation Rules:**
- `Status` typically: `Not Started`, `In Progress`, `Completed`, `Waiting on someone else`, `Deferred`
- `Priority` typically: `High`, `Normal`, `Low`

**Example:**
```json
{
  "Subject": "Schedule product demo",
  "Description": "Arrange a demo session for the new CRM features",
  "Status": "Not Started",
  "Priority": "High",
  "OwnerId": "005xx000001SvmDAAS"
}
```

---

### SalesforceActivityPayload

XML payload structure for adding Salesforce activity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| contactid | string | Yes | Salesforce contact ID |
| subject | string | Yes | Activity subject |
| comment | string | No | Activity comment/description |
| feedid | integer | Yes | Feed identifier |
| username | string | No | Username to assign activity owner |

**Example:**
```json
{
  "contactid": "003xx000004TmXDAA0",
  "subject": "Initial consultation call",
  "comment": "Discussed requirements and timeline for implementation",
  "feedid": 12345,
  "username": "sales.rep@company.com"
}
```

---

### SalesforceContact

Contact data structure returned from Salesforce queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | string | Yes | Salesforce contact ID |
| Name | string | No | Full name |
| FirstName | string | No | First name |
| LastName | string | Yes | Last name |
| Email | string | No | Email address |
| Phone | string | No | Phone number |
| MobilePhone | string | No | Mobile phone number |
| OtherPhone | string | No | Other phone number |
| AccountId | string | No | Associated account ID |
| OwnerId | string | No | Owner user ID |

**Example:**
```json
{
  "Id": "003xx000004TmXDAA0",
  "Name": "Jane Smith",
  "FirstName": "Jane",
  "LastName": "Smith",
  "Email": "jane.smith@example.com",
  "Phone": "+1-555-123-4567",
  "MobilePhone": "+1-555-987-6543",
  "OtherPhone": null,
  "AccountId": "001xx000003GHuIAAW",
  "OwnerId": "005xx000001SvmDAAS"
}
```

---

### SalesforceTask

Task/Activity data structure for Salesforce.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Subject | string | Yes | Task subject |
| Description | string | No | Task description |
| WhoId | string | No | Related contact ID |
| Status | string | Yes | Task status |
| Priority | string | Yes | Task priority |
| OwnerId | string | No | Task owner user ID |

**Example:**
```json
{
  "Subject": "Quarterly review meeting",
  "Description": "Review Q3 performance and discuss Q4 goals",
  "WhoId": "003xx000004TmXDAA0",
  "Status": "Not Started",
  "Priority": "Normal",
  "OwnerId": "005xx000001SvmDAAS"
}
```

---

### Feed_Salesforce

Feed class that supports the Salesforce API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| feedid | integer | Yes | Feed identifier |
| salesforce | object | Yes | Salesforce connection object |
| exch | object | No | Exchange connection object |

**Example:**
```json
{
  "feedid": 12345,
  "salesforce": {},
  "exch": null
}
```

---

## SugarCRM Integration

### Sgapi_Sugarcrm

General class that supports the SugarCRM API for message gateway.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SugarConnection | object | Yes | SugarCRM connection object |
| token | string | Yes | Authentication token |
| wsdl | string | Yes | Path to WSDL file |
| sessionId | string | Yes | Session identifier |
| cache_dir | string | Yes | Cache directory path |
| response_timeout | integer | Yes | Time limit for response in seconds |
| aDbRow | object | Yes | Database row object with connection details |

**Example:**
```json
{
  "SugarConnection": {},
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "wsdl": "/var/wsdl/sugarcrm/soap.wsdl",
  "sessionId": "qrs7tuv8wxy9z0a1b2c3d4e5f6g7h8i9",
  "cache_dir": "/var/cache/sugarcrm",
  "response_timeout": 30,
  "aDbRow": {
    "SugarToken": "abc123...",
    "EndPoint": "https://crm.company.com/soap.php"
  }
}
```

---

### SugarCRM_Feed_XML

XML payload structure for SugarCRM feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be `sugarcrm`) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | SugarCRM server URL |
| nicename | string | Yes | Nice display name |
| username | string | Yes | SugarCRM username |
| password | string | Yes | SugarCRM password |

**Validation Rules:**
- `type` must be exactly `sugarcrm`
- `server` must be a valid URL
- `username` and `password` are required for authentication

**Example:**
```json
{
  "type": "sugarcrm",
  "feedid": "5001",
  "server": "https://crm.company.com",
  "nicename": "Company CRM",
  "username": "api_user",
  "password": "secure_password_123"
}
```

---

### Sessions_Sugarcrm

Database table for SugarCRM connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID (foreign key to Sessions) |
| SugarToken | string | Yes | SugarCRM authentication token |
| PhpSessionId | string | Yes | PHP session identifier |
| EndPoint | string | Yes | SOAP endpoint URL |
| Timeout | int | Yes | Session timeout in minutes |

**Validation Rules:**
- `SID` must reference a valid session in the Sessions table
- `EndPoint` must be a valid SOAP endpoint URL
- `Timeout` must be a positive integer

**Example:**
```json
{
  "SID": 2001,
  "SugarToken": "qrs7tuv8wxy9z0a1b2c3d4e5f6g7h8i9",
  "PhpSessionId": "php_sess_abc123def456",
  "EndPoint": "https://crm.company.com/soap.php",
  "Timeout": 60
}
```

---

## Microsoft Dynamics Integration

### Msdynamics

Microsoft Dynamics CRM wrapper class for message gateway API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sHeaderSecurity | string | Yes | Security header with encrypted authentication |
| response_timeout | int | Yes | Time limit in seconds for responses |
| server | string | Yes | Server name or IP address with port |
| aStatsParam | array | No | Statistics parameters |
| cache_dir | string | No | Cache directory path |
| namespace | string | No | XML namespace |
| url_discovery | string | No | Discovery service URL |
| url_crm | string | No | CRM service URL |
| url_metadata | string | No | Metadata service URL |
| endpoint_crm | string | No | CRM endpoint |
| endpoint_metadata | string | No | Metadata endpoint |
| wsdl_status_crm | boolean | No | CRM WSDL status |
| wsdl_status_meta | boolean | No | Metadata WSDL status |
| ticket | string | No | Authentication ticket |
| wsdl_type | string | No | WSDL type: `metadata` or `crm` |
| authtype | string | Yes | Auth type: `ad`, `spla`, or `passport` |
| client | object | No | SOAP client object |
| endpoint | string | No | Service endpoint |

**Validation Rules:**
- `authtype` must be one of: `ad`, `spla`, `passport`
- `server` must include protocol and port

**Example:**
```json
{
  "sHeaderSecurity": "<Security>...</Security>",
  "response_timeout": 45,
  "server": "https://crm.dynamics.com:443",
  "authtype": "spla",
  "cache_dir": "/var/cache/dynamics",
  "namespace": "http://schemas.microsoft.com/xrm/2011/Contracts",
  "url_crm": "https://crm.dynamics.com/XRMServices/2011/Organization.svc",
  "url_metadata": "https://crm.dynamics.com/XRMServices/2011/Metadata.svc",
  "ticket": "CrmTicket_ABC123...",
  "wsdl_type": "crm"
}
```

---

### Auth_Msdynamics

Microsoft Dynamics CRM authentication class.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MSDConnection | object | Yes | Microsoft Dynamics connection object |
| dbConn | object | Yes | Database connection object |
| response_timeout | integer | Yes | Response timeout in seconds |
| aMsdInfo | array | Yes | MS Dynamics auth info including HeaderSecurity and OrgServiceURI |

**Example:**
```json
{
  "MSDConnection": {},
  "dbConn": {},
  "response_timeout": 30,
  "aMsdInfo": {
    "HeaderSecurity": "<Security>...</Security>",
    "OrgServiceURI": "https://org.crm.dynamics.com/XRMServices/2011/Organization.svc"
  }
}
```

---

### Sessions_Msdynamics

Database table for Microsoft Dynamics session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID (foreign key to Sessions) |
| User | string | Yes | Username |
| Pword | string | Yes | Encrypted password |
| Organization | string | Yes | Organization name |
| Server | string | Yes | Server URL |
| AuthType | string | Yes | Authentication type |
| CrmTicket | string | Yes | CRM security header/ticket |
| CrmServiceUrl | string | Yes | CRM organization service URL |
| Timeout | integer | Yes | Session timeout in minutes |

**Validation Rules:**
- `AuthType` must be one of: `ad`, `spla`, `passport`
- `CrmTicket` contains the security token for API calls

**Example:**
```json
{
  "SID": 3001,
  "User": "dynamics_user@company.com",
  "Pword": "encrypted_pwd_hash_xyz",
  "Organization": "CompanyOrg",
  "Server": "https://company.crm.dynamics.com",
  "AuthType": "spla",
  "CrmTicket": "<s:Envelope>...</s:Envelope>",
  "CrmServiceUrl": "https://company.crm.dynamics.com/XRMServices/2011/Organization.svc",
  "Timeout": 120
}
```

---

### Msdynamics_Feed_Payload

XML payload structure for Microsoft Dynamics authentication feed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be `msdynamics`) |
| feedid | integer | Yes | Feed identifier |
| nicename | string | Yes | Nice/display name for the feed |
| authtype | string | Yes | Authentication type (e.g., `spla`) |
| server | string | Yes | CRM server URL |
| organization | string | Yes | Organization name |
| username | string | Yes | Username for authentication |
| password | string | Yes | Password for authentication |

**Example:**
```json
{
  "type": "msdynamics",
  "feedid": 6001,
  "nicename": "Company Dynamics CRM",
  "authtype": "spla",
  "server": "https://company.crm.dynamics.com",
  "organization": "CompanyOrg",
  "username": "crm_api_user@company.com",
  "password": "secure_password"
}
```

---

### MSDynamics_FieldList_Item

Field metadata structure returned by MS Dynamics fieldlist query.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | string | Yes | Logical field name |
| Type | string | Yes | Field attribute type |
| Length | int | No | Maximum field length |
| Required | string | Yes | Required status: `Yes`, `No`, or `Internal` |
| PicklistValueN | string | No | Picklist option values (indexed 1, 2, 3...) |

**Example:**
```json
{
  "Name": "accountname",
  "Type": "String",
  "Length": 160,
  "Required": "Yes",
  "PicklistValue1": null,
  "PicklistValue2": null
}
```

---

### SecurityData

Microsoft Dynamics security data object returned from Live ID authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| keyIdentifier | string | Yes | Key identifier for security token |
| securityToken0 | string | Yes | First encrypted security token (CipherValue) |
| securityToken1 | string | Yes | Second encrypted security token (CipherValue) |

**Example:**
```json
{
  "keyIdentifier": "WTY3ZjQ1NmUtNDEyMC00YjM5",
  "securityToken0": "MIIE7DCCA9SgAwIBAgIKYQ...",
  "securityToken1": "PHNhbWw6QXNzZXJ0aW9uIE..."
}
```

---

## Zendesk Integration

### Sgapi_Zendesk

Zendesk API integration class for message gateway.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ZendeskConnection | object | Yes | Zendesk connection object |
| dbConn | object | Yes | Database connection object |
| response_timeout | integer | Yes | Response timeout in seconds |
| arrObjectList | array | Yes | List of supported Zendesk objects |
| arrTableToPath | array | Yes | Mapping of table names to API paths |
| arrFieldTrans | array | Yes | Field name translations |
| arrValidOrderby | array | Yes | Valid order by fields |
| aDbRow | array | Yes | Database row with connection details |
| sEndPtExt | string | Yes | API endpoint file extension |

**Example:**
```json
{
  "ZendeskConnection": {},
  "dbConn": {},
  "response_timeout": 30,
  "arrObjectList": ["organizations", "tickets", "users"],
  "arrTableToPath": {
    "organizations": "/api/v2/organizations",
    "tickets": "/api/v2/tickets"
  },
  "arrFieldTrans": {
    "type": "ticket_type",
    "created_at": "created"
  },
  "arrValidOrderby": ["created_at", "updated_at", "priority"],
  "aDbRow": {
    "User": "admin@company.zendesk.com",
    "Server": "https://company.zendesk.com"
  },
  "sEndPtExt": ".json"
}
```

---

### Sessions_Zendesk

Database table for Zendesk connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID (foreign key to Sessions) |
| User | string | Yes | Zendesk username (may include `/token` suffix) |
| Pword | string | Yes | Encrypted password or API token |
| Server | string | Yes | Zendesk server URL |
| Timeout | int | Yes | Session timeout in minutes |

**Validation Rules:**
- `User` may end with `/token` for API token authentication
- `Server` must be a valid Zendesk subdomain URL

**Example:**
```json
{
  "SID": 4001,
  "User": "api_user@company.com/token",
  "Pword": "encrypted_api_token_xyz",
  "Server": "https://company.zendesk.com",
  "Timeout": 120
}
```

---

### Zendesk_Feed_XML

XML payload structure for Zendesk feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be `zendesk`) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | Zendesk server URL |
| username | string | Yes | Zendesk username/email |
| password | string | Conditional | Zendesk password (alternative to token) |
| token | string | Conditional | Zendesk API token (alternative to password) |

**Validation Rules:**
- Either `password` or `token` must be provided, not both
- `server` should be the Zendesk subdomain URL

**Example:**
```json
{
  "type": "zendesk",
  "feedid": "4501",
  "server": "https://company.zendesk.com",
  "username": "support@company.com",
  "token": "aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV"
}
```

---

### Zendesk_DbRow

Database row structure containing Zendesk connection details.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| User | string | Yes | Zendesk username |
| Pword | string | Yes | Zendesk password |
| Server | string | Yes | Zendesk server URL |

**Example:**
```json
{
  "User": "api_user@company.zendesk.com/token",
  "Pword": "encrypted_token",
  "Server": "https://company.zendesk.com"
}
```

---

### Zendesk_ObjectList

Supported Zendesk objects/tables for API operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| organizations | string | Yes | Organizations endpoint |
| groups | string | Yes | Groups endpoint |
| tickets | string | Yes | Tickets endpoint |
| ticket_metrics | string | Yes | Ticket metrics endpoint |
| ticket_comments | string | Yes | Ticket comments endpoint |
| requests | string | Yes | Requests endpoint |
| uploads | string | Yes | Uploads/attachments endpoint |
| users | string | Yes | Users endpoint |
| group_memberships | string | Yes | Group memberships endpoint |
| forums | string | Yes | Forums endpoint |
| forum_subscriptions | string | Yes | Forum subscriptions endpoint |
| categories | string | Yes | Categories endpoint |
| topics | string | Yes | Topics endpoint |
| topic_subscriptions | string | Yes | Topic subscriptions endpoint |
| topic_comments | string | Yes | Topic comments endpoint |

**Example:**
```json
{
  "organizations": "/api/v2/organizations",
  "groups": "/api/v2/groups",
  "tickets": "/api/v2/tickets",
  "ticket_metrics": "/api/v2/ticket_metrics",
  "ticket_comments": "/api/v2/tickets/{id}/comments",
  "requests": "/api/v2/requests",
  "uploads": "/api/v2/uploads",
  "users": "/api/v2/users",
  "group_memberships": "/api/v2/group_memberships",
  "forums": "/api/v2/community/forums",
  "categories": "/api/v2/community/categories",
  "topics": "/api/v2/community/topics"
}
```

---

### Zendesk_FieldTranslations

Field name translations between internal and Zendesk API field names.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Maps to `ticket_type` |
| due_at | string | Yes | Maps to `due_date` |
| created_at | string | Yes | Maps to `created` |
| requester_id | string | Yes | Maps to `requester` |
| submitter_id | string | Yes | Maps to `submitter` |
| updated_at | string | Yes | Maps to `updated` |
| Custom | string | Yes | Maps to `fieldvalue` |
| roles | string | Yes | Maps to `role` |

**Example:**
```json
{
  "type": "ticket_type",
  "due_at": "due_date",
  "created_at": "created",
  "requester_id": "requester",
  "submitter_id": "submitter",
  "updated_at": "updated",
  "Custom": "fieldvalue",
  "roles": "role"
}
```

---

### ZendeskOrganization

Zendesk organizations resource model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | No | Organization ID (internal) |
| url | string | No | API URL (internal) |
| external_id | string | No | External identifier |
| name | string | Yes | Organization name |
| created_at | date | No | Creation timestamp (internal) |
| updated_at | date | No | Last update timestamp (internal) |
| domain_names | array | No | Associated domain names |
| details | string | No | Organization details |
| notes | string | No | Notes |
| group_id | integer | No | Associated group ID |
| shared_tickets | boolean | No | Shared tickets flag |
| shared_comments | boolean | No | Shared comments flag |
| tags | array | No | Organization tags |

**Example:**
```json
{
  "id": 12345678,
  "url": "https://company.zendesk.com/api/v2/organizations/12345678.json",
  "external_id": "EXT-ORG-001",
  "name": "Acme Corporation",
  "created_at": "2023-01-15T10:30:00Z",
  "updated_at": "2024-06-20T14:45:00Z",
  "domain_names": ["acme.com", "acme.io"],
  "details": "Enterprise customer since 2020",
  "notes": "VIP support tier",
  "group_id": 987654,
  "shared_tickets": true,
  "shared_comments": true,
  "tags": ["enterprise", "vip", "priority"]
}
```

---

### ZendeskGroup

Zendesk groups resource model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | No | Group ID (internal) |
| url | string | No | API URL (internal) |
| name | string | Yes | Group name |
| deleted | boolean | No | Deletion flag |
| created_at | date | No | Creation timestamp (internal) |
| updated_at | date | No | Last update timestamp (internal) |

**Example:**
```json
{
  "id": 987654,
  "url": "https://company.zendesk.com/api/v2/groups/987654.json",
  "name": "Technical Support",
  "deleted": false,
  "created_at": "2022-06-01T09:00:00Z",
  "updated_at": "2024-03-15T11:30:00Z"
}
```

---

### ZendeskTicket

Zendesk tickets resource model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | No | Ticket ID (internal) |
| url | string | No | API URL (internal) |
| external_id | string | No | External identifier |
| type | picklist | No | Ticket type |
| subject | string | Yes | Ticket subject |
| raw_subject | string | No | Raw subject line |
| description | string | Yes | Ticket description |
| priority | picklist | No | Priority level: `low`, `normal`, `high`, `urgent` |
| status | picklist | Yes | Ticket status: `new`, `open`, `pending`, `hold`, `solved`, `closed` |
| recipient | string | No | Ticket recipient |
| requester_id | integer | Yes | Requester user ID |
| submitter_id | integer | No | Submitter user ID |
| assignee_id | integer | No | Assignee user ID |
| organization_id | integer | No | Organization ID (internal) |
| group_id | integer | No | Group ID |

**Example:**
```json
{
  "id": 456789,
  "url": "https://company.zendesk.com/api/v2/tickets/456789.json",
  "external_id": "EXT-TKT-12345",
  "type": "incident",
  "subject": "Login issues after password reset",
  "raw_subject": "RE: Login issues after password reset",
  "description": "Customer unable to access account after resetting password",
  "priority": "high",
  "status": "open",
  "recipient": "support@company.com",
  "requester_id": 111222333,
  "submitter_id": 111222333,
  "assignee_id": 444555666,
  "organization_id": 12345678,
  "group_id": 987654
}
```

---

### ZendeskTicketMetrics

Zendesk ticket metrics resource model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | No | Metric ID (internal) |
| ticket_id | integer | Yes | Associated ticket ID (internal) |
| url | string | No | API URL (internal) |
| group_stations | integer | No | Number of group stations |
| assignee_stations | integer | No | Number of assignee stations |
| reopens | integer | No | Number of reopens |
| replies | integer | No | Number of replies |
| assignee_updated_at | date | No | Last assignee update |
| requester_updated_at | date | No | Last requester update |
| status_updated_at | date | No | Last status update |
| initially_assigned_at | date | No | Initial assignment timestamp |
| assigned_at | date | No | Current assignment timestamp |
| solved_at | date | No | Solved timestamp |
| latest_comment_added_at | date | No | Latest comment timestamp |
| first_resolution_time_in_minutes | object | No | First resolution time (internal) |

**Example:**
```json
{
  "id": 789012345,
  "ticket_id": 456789,
  "url": "https://company.zendesk.com/api/v2/ticket_metrics/789012345.json",
  "group_stations": 2,
  "assignee_stations": 3,
  "reopens": 1,
  "replies": 5,
  "assignee_updated_at": "2024-06-20T10:15:00Z",
  "requester_updated_at": "2024-06-20T09:30:00Z",
  "status_updated_at": "2024-06-20T10:15:00Z",
  "initially_assigned_at": "2024-06-18T14:00:00Z",
  "assigned_at": "2024-06-19T09:00:00Z",
  "solved_at": null,
  "latest_comment_added_at": "2024-06-20T10:15:00Z",
  "first_resolution_time_in_minutes": {
    "calendar": 120,
    "business": 90
  }
}
```

---

## Oracle Fusion Integration

### Sgapi_Oraclefusion

Oracle Fusion CRM API integration class for message gateway.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| oOraclefusionClient | SoapClient | Yes | Oracle Fusion SOAP client object |
| dbConn | object | Yes | Database connection object |
| aObjects | array | Yes | Supported Oracle Fusion objects with paths |
| aDbRow | array | Yes | Database row with connection details |
| aKeyField | array | No | Key field information for queries |

**Example:**
```json
{
  "oOraclefusionClient": {},
  "dbConn": {},
  "aObjects": {
    "Person": {
      "path": "/foundationParties/PersonService",
      "method": "findPerson"
    },
    "Opportunity": {
      "path": "/opptyMgmtOpportunities/OpportunityService",
      "method": "findOpportunity"
    }
  },
  "aDbRow": {
    "Usr": "fusion_user",
    "Server": "https://company.fs.us2.oraclecloud.com"
  },
  "aKeyField": {
    "Person": "PartyId",
    "Opportunity": "OptyId"
  }
}
```

---

### Auth_Oraclefusion

Authorisation class that supports the Oracle Fusion API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| response_timeout | string | Yes | Time limit to get response |
| aOracleFusionInfo | array | Yes | Oracle Fusion connection info |

**Example:**
```json
{
  "dbConn": {},
  "response_timeout": "45",
  "aOracleFusionInfo": {
    "server": "https://company.fs.us2.oraclecloud.com",
    "username": "fusion_api_user",
    "authenticated": true
  }
}
```

---

### Sessions_Oraclefusion

Database table for storing Oracle Fusion session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID from Sessions table |
| Usr | string | Yes | Oracle Fusion username |
| Pword | string | Yes | Encrypted password |
| Server | string | Yes | Oracle Fusion server URL |
| Timeout | integer | Yes | Auth token lifetime in minutes |

**Example:**
```json
{
  "SID": 5001,
  "Usr": "fusion.api@company.com",
  "Pword": "encrypted_password_hash",
  "Server": "https://company.fs.us2.oraclecloud.com",
  "Timeout": 120
}
```

---

### OracleFusionFeedPayload

XML payload structure for Oracle Fusion authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be `oraclefusion`) |
| feedid | integer | Yes | Feed identifier |
| server | string | Yes | Oracle Fusion server URL |
| nicename | string | Yes | Human-readable feed name |
| username | string | Yes | Oracle Fusion username |
| password | string | Yes | Oracle Fusion password |

**Example:**
```json
{
  "type": "oraclefusion",
  "feedid": 5501,
  "server": "https://company.fs.us2.oraclecloud.com",
  "nicename": "Oracle Fusion Sales Cloud",
  "username": "sales_integration@company.com",
  "password": "secure_password_456"
}
```

---

### Oraclefusion_Objects

Oracle Fusion CRM supported objects configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Person | object | Yes | Person/Party object - path: `/foundationParties/PersonService` |
| Opportunity | object | Yes | Opportunity object - path: `/opptyMgmtOpportunities/OpportunityService` |
| Interaction | object | Yes | Interaction object - path: `/appCmmnCompInteractions/InteractionService` |
| ServiceLead | object | Yes | Service Lead object - path: `/mklLeads/LeadPublicService` |
| MklLead | object | Yes | Marketing Lead object - path: `/mklLeads/SalesLeadService` |
| SalesParty | object | Yes | Sales Party/Account object - path: `/crmCommonSalesParties/SalesPartyService` |
| Location | object | Yes | Location object - path: `/foundationParties/LocationService` |
| SalesCustom | object | Yes | Sales Custom object - path: `/opptyMgmtExtensibility/SalesCustomObjectService` |
| CustomerCenterCustom | object | Yes | Customer Center Custom object - path: `/crmCommonCustExtn/CustomerCenterCustomObjectService` |
| MarketingCustom | object | Yes | Marketing Custom object - path: `/mktExtensibility/MarketingCustomObjectService` |

**Example:**
```json
{
  "Person": {
    "path": "/foundationParties/PersonService",
    "methods": ["findPerson", "createPerson", "updatePerson"]
  },
  "Opportunity": {
    "path": "/opptyMgmtOpportunities/OpportunityService",
    "methods": ["findOpportunity", "createOpportunity", "updateOpportunity"]
  },
  "SalesParty": {
    "path": "/crmCommonSalesParties/SalesPartyService",
    "methods": ["findSalesParty", "createSalesParty"]
  },
  "Location": {
    "path": "/foundationParties/LocationService",
    "methods": ["findLocation", "createLocation"]
  }
}
```

---

### Oraclefusion_Field

Oracle Fusion field metadata structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | string | Yes | Field name |
| Type | string | Yes | Field data type |
| Length | integer | No | Field length |
| Required | string | Yes | Required status: `Yes`, `No`, or `Internal` |

**Example:**
```json
{
  "Name": "PartyName",
  "Type": "String",
  "Length": 360,
  "Required": "Yes"
}
```

---

### Oraclefusion_DbRow

Database row structure containing Oracle Fusion connection details.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Usr | string | Yes | Oracle Fusion username |
| Pword | string | Yes | Oracle Fusion password |
| Timeout | integer | Yes | Connection timeout |
| Server | string | Yes | Oracle Fusion server URL |

**Example:**
```json
{
  "Usr": "fusion_service_account",
  "Pword": "encrypted_pwd",
  "Timeout": 120,
  "Server": "https://company.fs.us2.oraclecloud.com"
}
```

---

## GoodData Integration

### Sgapi_Gooddata

General class that supports the GoodData API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | Database | Yes | Database connection object |
| response_timeout | integer | Yes | Response timeout value |
| arrObjectList | array | Yes | List of available objects |
| arrTableToPath | array | Yes | Mapping of tables to paths |
| arrIdToText | array | No | ID to text mapping |
| arrTextToId | array | No | Text to ID mapping |
| server | string | Yes | GoodData server URL |
| strEndPointOnURL | string | Yes | Project endpoint path |
| strGDCAuthTT | string | Yes | GoodData temporary auth token |
| strGDCAuthSST | string | Yes | GoodData secure auth token |
| CLIpath | string | No | Path to GoodData CLI |
| aDbRow | array | Yes | Database row with session info |
| token | string | Yes | Authentication token |

**Example:**
```json
{
  "dbConn": {},
  "response_timeout": 60,
  "arrObjectList": ["datasets", "reports", "dashboards"],
  "arrTableToPath": {
    "datasets": "/gdc/md/{project}/datasets",
    "reports": "/gdc/md/{project}/reports"
  },
  "server": "https://secure.gooddata.com",
  "strEndPointOnURL": "/gdc/projects/abc123xyz",
  "strGDCAuthTT": "temp_token_abc123",
  "strGDCAuthSST": "secure_token_xyz789",
  "CLIpath": "/usr/local/bin/gooddata",
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

---

### Sessions_Gooddata

Database table for GoodData connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID (foreign key to Sessions) |
| User | string | Yes | GoodData username |
| Pword | string | Yes | Encrypted password |
| Server | string | Yes | GoodData server URL |
| GDCAuthTT | string | Yes | GoodData temporary authentication token |
| GDCAuthSST | string | Yes | GoodData super secure token |
| ProjectEndpoint | string | Yes | GoodData project metadata endpoint |
| Timeout | int | Yes | Session timeout in minutes |

**Example:**
```json
{
  "SID": 6001,
  "User": "analytics@company.com",
  "Pword": "encrypted_password_hash",
  "Server": "https://secure.gooddata.com",
  "GDCAuthTT": "gdcTT_temp123456789",
  "GDCAuthSST": "gdcSST_secure987654321",
  "ProjectEndpoint": "/gdc/projects/abc123def456",
  "Timeout": 180
}
```

---

### GoodData_Feed_XML

XML payload structure for GoodData feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be `gooddata`) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | GoodData server URL |
| username | string | Yes | GoodData username/email |
| password | string | Yes | GoodData password |
| project_title | string | Yes | GoodData project title to connect to |

**Example:**
```json
{
  "type": "gooddata",
  "feedid": "6501",
  "server": "https://secure.gooddata.com",
  "username": "bi_analyst@company.com",
  "password": "secure_analytics_pwd",
  "project_title": "Sales Analytics Dashboard"
}
```

---

## Workbooks Integration

### WorkbooksApi

PHP wrapper for the Workbooks API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| curl_handle | resource | No | CURL handle for HTTP requests |
| curl_options | array | No | CURL configuration options |
| logger_callback | array | No | Callback function for logging |
| session_id | string | Yes | Session ID from Workbooks |
| authenticity_token | string | Yes | Authenticity token unique to each session |
| login_state | boolean | Yes | Whether user is logged in |
| application_name | string | Yes | Human-readable name for the client application |
| user_agent | string | Yes | Technical name with version for HTTP User-Agent |
| connect_timeout | integer | Yes | Connection timeout in seconds |
| request_timeout | integer | Yes | Request timeout in seconds |
| verify_peer | boolean | Yes | Whether to verify peer SSL certificate |
| service | string | Yes | FQDN of the Workbooks service |
| last_request_duration | float | No | Duration of the last request in seconds |

**Example:**
```json
{
  "curl_handle": null,
  "curl_options": {
    "CURLOPT_SSL_VERIFYPEER": true,
    "CURLOPT_TIMEOUT": 30
  },
  "session_id": "wb_sess_abc123def456",
  "authenticity_token": "auth_token_xyz789",
  "login_state": true,
  "application_name": "Platform Service Gateway",
  "user_agent": "PSG/2.1.0",
  "connect_timeout": 10,
  "request_timeout": 30,
  "verify_peer": true,
  "service": "secure.workbooks.com",
  "last_request_duration": 0.245
}
```

---

### Auth_Workbooks

Authorisation class that supports the Workbooks API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| response_timeout | string | Yes | Time limit to get response |
| aWbInfo | array | Yes | Workbooks info containing AuthenticityToken and SessionId |

**Example:**
```json
{
  "dbConn": {},
  "response_timeout": "30",
  "aWbInfo": {
    "AuthenticityToken": "wb_auth_abc123",
    "SessionId": "wb_session_xyz789"
  }
}
```

---

### Sgapi_Workbooks

General class that supports the Workbooks CRM API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| WorkbookConnection | WorkbooksApi | Yes | Workbooks API connection object |
| dbConn | Database | Yes | Database connection object |
| token | string | Yes | Authentication token |
| metadata_path | string | No | Path to metadata cache file |
| objArr | array | Yes | Array mapping class names to controller paths |
| resultdata | array | No | Metadata result data |
| response_timeout | integer | Yes | Response timeout value |
| aDbRow | array | Yes | Database row with session info |

**Example:**
```json
{
  "WorkbookConnection": {},
  "dbConn": {},
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "metadata_path": "/var/cache/workbooks/metadata.json",
  "objArr": {
    "Person": "/crm/people",
    "Organisation": "/crm/organisations",
    "Opportunity": "/crm/opportunities"
  },
  "response_timeout": 30,
  "aDbRow": {
    "AuthenticityToken": "wb_auth_token",
    "SessionId": "wb_session_id",
    "User": "workbooks_user"
  }
}
```

---

### Sessions_Workbooks

Database table for storing Workbooks session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID from Sessions table |
| User | string | Yes | Workbooks username |
| AuthenticityToken | string | Yes | Workbooks authenticity token |
| SessionId | string | Yes | Workbooks session ID |
| Timeout | integer | Yes | Auth token lifetime in minutes |

**Example:**
```json
{
  "SID": 7001,
  "User": "api_user@company.com",
  "AuthenticityToken": "wb_authenticity_abc123xyz",
  "SessionId": "wb_session_def456uvw",
  "Timeout": 60
}
```

---

### WorkbooksFeedPayload

XML payload structure for Workbooks authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be `workbooks`) |
| feedid | integer | Yes | Feed identifier |
| server | string | Yes | Workbooks server URL |
| nicename | string | Yes | Human-readable feed name |
| username | string | Yes | Workbooks username |
| password | string | Yes | Workbooks password |
| dbname | string | No | Optional database name for multi-database accounts |

**Example:**
```json
{
  "type": "workbooks",
  "feedid": 7501,
  "server": "https://secure.workbooks.com",
  "nicename": "Company Workbooks CRM",
  "username": "integration@company.com",
  "password": "secure_wb_password",
  "dbname": "production"
}
```

---

## MPP Global Integration

### Auth_Mpp

Authorization class for MPP payment gateway connector.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nFeedid | integer | Yes | Feed identifier |
| oDbConn | Database | Yes | Database connection object |
| nResponse_timeout | integer | Yes | Response timeout value |
| sServer | string | Yes | Server URL |
| aMppInfo | array | Yes | MPP information including GUID |

**Example:**
```json
{
  "nFeedid": 8001,
  "oDbConn": {},
  "nResponse_timeout": 30,
  "sServer": "https://payments.mppglobal.com",
  "aMppInfo": {
    "GUID": "mpp-guid-abc123-def456-ghi789"
  }
}
```

---

### Sgapi_Mpp

API class for MPP Global payment gateway integration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| oDbConn | object | Yes | Database connection object |
| nResponse_timeout | integer | Yes | Response timeout in seconds |
| sServer | string | Yes | API endpoint server URL |
| sClientId | string | Yes | MPP client ID |
| sPassword | string | Yes | MPP password |
| aDbRow | array | Yes | Database row with connection details |

**Example:**
```json
{
  "oDbConn": {},
  "nResponse_timeout": 45,
  "sServer": "https://api.mppglobal.com/v2",
  "sClientId": "client_abc123",
  "sPassword": "encrypted_password",
  "aDbRow": {
    "ClientId": "client_abc123",
    "Guid": "mpp-guid-xyz789",
    "Server": "https://api.mppglobal.com/v2"
  }
}
```

---

### Sessions_Mpp

Database table for storing MPP session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID (foreign key to Sessions) |
| ClientId | string | Yes | MPP client identifier |
| Pword | string | Yes | Encrypted password |
| Guid | string | Yes | MPP GUID token |
| Server | string | Yes | Server URL |
| Timeout | integer | Yes | Session timeout |

**Example:**
```json
{
  "SID": 8001,
  "ClientId": "mpp_client_12345",
  "Pword": "encrypted_password_hash",
  "Guid": "550e8400-e29b-41d4-a716-446655440000",
  "Server": "https://payments.mppglobal.com",
  "Timeout": 60
}
```

---

### MppUserAccount

User account field definitions for MPP Global payment system.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| emailaddress | String | Yes | User email address |
| userpassword | String | Yes | User password |
| clientuserid | String | Yes | Client user identifier |
| title | String | No | User title |
| firstname | String | Yes | First name |
| surname | String | Yes | Surname |
| dateofbirth | String | No | Date of birth |
| nomarketinginformation | Boolean | No | Marketing opt-out flag |
| maidenname | String | No | Maiden name |
| memorableplace | String | No | Security question - memorable place |
| gender | Picklist | No | Gender |
| mobilephonenumber | String | No | Mobile phone number |
| homephonenumber | String | No | Home phone number |
| homehousename | String | No | House name |
| homehouseflatname | String | No | Flat name |

**Example:**
```json
{
  "emailaddress": "customer@example.com",
  "userpassword": "secure_password",
  "clientuserid": "USR-12345",
  "title": "Mr",
  "firstname": "John",
  "surname": "Smith",
  "dateofbirth": "1985-03-15",
  "nomarketinginformation": false,
  "maidenname": null,
  "memorableplace": "London",
  "gender": "Male",
  "mobilephonenumber": "+44-7700-900123",
  "homephonenumber": "+44-20-7946-0958",
  "homehousename": "Oak House",
  "homehouseflatname": "Flat 2B"
}
```

---

### MppApiResponse

Response structure from MPP API requests.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Httpcode | integer | Yes | HTTP response code |
| CurlErrMsg | string | No | cURL error message |
| CurlErrNo | integer | No | cURL error number |
| ErrorNumber | integer | No | MPP error number |
| ErrorMessage | string | No | MPP error message |
| Guid | string | No | Response GUID |
| OrderId | string | No | Order identifier |
| SgapiPmtError | array | No | Mapped payment error |
| faultcode | string | No | SOAP fault code |

**Example:**
```json
{
  "Httpcode": 200,
  "CurlErrMsg": null,
  "CurlErrNo": 0,
  "ErrorNumber": 0,
  "ErrorMessage": null,
  "Guid": "550e8400-e29b-41d4-a716-446655440000",
  "OrderId": "ORD-2024-001234",
  "SgapiPmtError": null,
  "faultcode": null
}
```

---

## LDAP Integration

### Sgapi_Ldap

Class for connecting and querying LDAP servers.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| LdapConnection | resource | Yes | LDAP connection resource |
| dbConn | object | Yes | Database connection |
| response_timeout | integer | Yes | Response timeout in seconds |
| server | string | Yes | LDAP server URL |
| userdn | string | Yes | User distinguished name |
| userParentDN | string | Yes | Parent DN for user |
| strLDAPTLS_CERT | string | No | TLS certificate file path |
| strLDAPTLS_KEY | string | No | TLS key file path |
| arrAttribValueConversion | array | No | Attribute value conversion mapping |
| strService | string | Yes | Service identifier (e.g., `MSAD`) |
| aDbRow | array | Yes | Database row with configuration |
| sLockFilePath | string | No | Lock file path for client cert |
| bSetClientCert | boolean | No | Flag indicating if client cert was set |

**Example:**
```json
{
  "LdapConnection": {},
  "dbConn": {},
  "response_timeout": 30,
  "server": "ldaps://ldap.company.com:636",
  "userdn": "cn=service_account,ou=Service Accounts,dc=company,dc=com",
  "userParentDN": "ou=Users,dc=company,dc=com",
  "strLDAPTLS_CERT": "/etc/ssl/certs/ldap-client.crt",
  "strLDAPTLS_KEY": "/etc/ssl/private/ldap-client.key",
  "arrAttribValueConversion": {
    "objectGUID": "binary_to_guid",
    "objectSid": "binary_to_sid"
  },
  "strService": "MSAD",
  "aDbRow": {
    "Server": "ldaps://ldap.company.com:636",
    "ParentDn": "ou=Users,dc=company,dc=com"
  },
  "bSetClientCert": true
}
```

---

### Sessions_Ldap

Database table for LDAP connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID (foreign key to Sessions) |
| UserRDn | string | Yes | User relative distinguished name |
| ParentDn | string | Yes | Parent distinguished name |
| Pword | string | Yes | Encrypted password |
| Service | string | Yes | LDAP service type (e.g., `MSAD`) |
| TlsCertfile | string | No | TLS certificate file content |
| TlsKeyfile | string | No | TLS key file content |
| Server | string | Yes | LDAP server URL |
| Timeout | int | Yes | Session timeout in minutes |

**Example:**
```json
{
  "SID": 9001,
  "UserRDn": "cn=ldap_service",
  "ParentDn": "ou=Service Accounts,dc=company,dc=com",
  "Pword": "encrypted_ldap_password",
  "Service": "MSAD",
  "TlsCertfile": "-----BEGIN CERTIFICATE-----\n...",
  "TlsKeyfile": "-----BEGIN PRIVATE KEY-----\n...",
  "Server": "ldaps://dc1.company.com:636",
  "Timeout": 120
}
```

---

### LDAP_Feed_XML

XML payload structure for LDAP feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be `ldap`) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | LDAP server URL |
| service | string | Yes | LDAP service type (e.g., `MSAD`) |
| parentdn | string | Yes | Parent distinguished name |
| userrdn | string | Yes | User relative distinguished name |
| password | string | Yes | LDAP password |
| tlscertfile | string | No | TLS certificate filename |
| tlskeyfile | string | No | TLS key filename |

**Example:**
```json
{
  "type": "ldap",
  "feedid": "9501",
  "server": "ldaps://ldap.company.com:636",
  "service": "MSAD",
  "parentdn": "ou=Users,dc=company,dc=com",
  "userrdn": "cn=integration_service",
  "password": "secure_ldap_password",
  "tlscertfile": "ldap-client.crt",
  "tlskeyfile": "ldap-client.key"
}
```

---

### LdapConnectionConfig

Configuration for LDAP connection from database row.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Server | string | Yes | LDAP server URL |
| TlsCertfile | string | No | TLS certificate filename |
| TlsKeyfile | string | No | TLS key filename |
| ParentDn | string | Yes | Parent distinguished name |
| UserRDn | string | Yes | User relative distinguished name |
| Pword | string | Yes | Password |
| Service | string | Yes | Service identifier |

**Example:**
```json
{
  "Server": "ldaps://dc.company.com:636",
  "TlsCertfile": "/etc/ssl/certs/ldap.crt",
  "TlsKeyfile": "/etc/ssl/private/ldap.key",
  "ParentDn": "ou=Corporate,dc=company,dc=com",
  "UserRDn": "cn=api_service",
  "Pword": "service_password",
  "Service": "MSAD"
}
```

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Platform Integration Model Relationships             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Sessions   │
                              │   (Master)   │
                              └──────┬───────┘
                                     │
         ┌───────────────┬───────────┼───────────┬───────────────┐
         │               │           │           │               │
         ▼               ▼           ▼           ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Sessions_        │ │Sessions_    │ │Sessions_    │ │Sessions_    │ │Sessions_    │
│Salesforce       │ │Sugarcrm     │ │Msdynamics   │ │Zendesk      │ │Workbooks    │
└────────┬────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
         │
         │  1:1
         ▼
┌─────────────────┐
│tokentosfsession │
└────────┬────────┘
         │
         │  N:1
         ▼
┌─────────────────┐
│  Sgapi_         │
│  Salesforce     │───────────────────┐
└────────┬────────┘                   │
         │                            │
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌─────────────────┐
│Contact_         │          │Task_            │
│Salesforce       │          │Salesforce       │
└─────────────────┘          └─────────────────┘
         │                            │
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌─────────────────┐
│Salesforce       │          │Salesforce_      │
│Contact          │          │Task_Fields      │
└─────────────────┘          └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                        Feed Payload to Session Flow                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     Auth      ┌──────────────────┐     Store     ┌──────────────────┐
│  Feed XML        │─────────────► │  Auth_*          │─────────────► │  Sessions_*      │
│  Payload         │               │  Class           │               │  Table           │
└──────────────────┘               └──────────────────┘               └──────────────────┘
        │                                   │                                  │
        │                                   │                                  │
        ▼                                   ▼                                  ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
│• SugarCRM_       │               │• Auth_Salesforce │               │• Sessions_       │
│  Feed_XML        │               │• Auth_Msdynamics │               │  Salesforce      │
│• Zendesk_        │               │• Auth_Workbooks  │               │• Sessions_       │
│  Feed_XML        │               │• Auth_Oraclefusion│              │  Msdynamics      │
│• GoodData_       │               │• Auth_Mpp        │               │• Sessions_       │
│  Feed_XML        │               │• Auth_Custom     │               │  Zendesk         │
│• LDAP_Feed_XML   │               └──────────────────┘               │• Sessions_       │
│• Msdynamics_     │                                                  │  Workbooks       │
│  Feed_Payload    │                                                  └──────────────────┘
│• Workbooks       │
│  FeedPayload     │
│• Oraclefusion    │
│  FeedPayload     │
└──────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                        Zendesk Object Hierarchy                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│Zendesk           │
│Organization      │◄────────────────────────────┐
└────────┬─────────┘                             │
         │ 1:N                                   │
         │                                       │
         ▼                                       │
┌──────────────────┐         ┌──────────────────┐│
│ZendeskTicket     │────────►│ZendeskGroup      ││
└────────┬─────────┘  N:1    └──────────────────┘│
         │                                       │
         │ 1:1                                   │
         │                                       │
         ▼                                       │
┌──────────────────┐                             │
│ZendeskTicket     │                             │
│Metrics           │                             │
└──────────────────┘                             │
                                                 │
┌──────────────────┐                             │
│Sgapi_Zendesk     │─────────────────────────────┘
│                  │ Uses Zendesk_ObjectList
│                  │ Uses Zendesk_FieldTranslations
└──────────────────┘
```

---

## Common Use Cases

### 1. Salesforce Integration Setup

```php
// 1. Parse feed XML payload
$feedPayload = [
    'type' => 'salesforce',
    'feedid' => '12345',
    'server' => 'https://login.salesforce.com',
    'username' => 'api_user@company.com',
    'password' => 'password123',
    'token' => 'security_token_xyz'
];

// 2. Authenticate and create session
$auth = new Auth_Salesforce();
$session = $auth->authenticate($feedPayload);

// 3. Store session data
// Sessions_Salesforce record created with:
// - SFToken: session token from Salesforce
// - Location: API endpoint URL
// - WSDL: 'partner' or 'enterprise'

// 4. Create API instance for queries
$api = new Sgapi_Salesforce($session);
```

### 2. Zendesk Ticket Query

```php
// Query tickets using Sgapi_Zendesk
$zendesk = new Sgapi_Zendesk($session);

// Field translations applied automatically
$tickets = $zendesk->query('tickets', [
    'status' => 'open',
    'priority' => 'high'
]);

// Returns array of ZendeskTicket objects
```

### 3. Microsoft Dynamics Contact Creation

```php
// Use Msdynamics class for CRM operations
$dynamics = new Msdynamics($session);

// Create contact record
$contact = [
    'firstname' => 'Jane',
    'lastname' => 'Smith',
    'emailaddress1' => 'jane.smith@example.com'
];

$result = $dynamics->create('contact', $contact);
```

---

## See Also

- [Session Models](session-models.md) - Core session management tables
- [Feed Models](feed-models.md) - Feed configuration and authentication
- [API Response Models](api-response-models.md) - Standard response structures