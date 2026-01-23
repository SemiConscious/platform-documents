# Session and Authentication Models

This document covers the session management and authentication models used across the Platform Service Gateway for managing user sessions, authentication tokens, and connector-specific session data.

## Overview

The authentication system uses a hierarchical session model where:
1. A master `Sessions` table stores core session metadata
2. Connector-specific session tables extend the base session with platform-specific credentials
3. Token-to-feed mappings enable multi-feed authentication with a single token
4. Feed XML payloads define the authentication parameters for each platform

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Token Authentication                         │
├─────────────────────────────────────────────────────────────────────┤
│  tokentofeed ───────────────────────────────────────────────────────│
│       │                                                              │
│       ▼                                                              │
│  ┌─────────┐                                                        │
│  │ Sessions │◄──────────────────────────────────────────────────────│
│  └────┬────┘                                                        │
│       │                                                              │
│       ├──► Sessions_Salesforce                                      │
│       ├──► Sessions_Sugarcrm                                        │
│       ├──► Sessions_Zendesk                                         │
│       ├──► Sessions_Gooddata                                        │
│       ├──► Sessions_Ldap                                            │
│       ├──► Sessions_Msdynamics                                      │
│       ├──► Sessions_Workbooks                                       │
│       ├──► Sessions_Oraclefusion                                    │
│       ├──► Sessions_Mpp                                             │
│       ├──► Sessions_Custom                                          │
│       └──► Sessions_Mysqlcon (inferred)                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Session Models

### Sessions

The master database table storing authentication sessions for all connectors.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID - Primary key, auto-incremented |
| OrgID | int | Yes | Organization ID for multi-tenant isolation |
| DataConnectorID | int | Yes | Identifier for the data connector type |
| FeedID | int | Yes | Feed identifier linking to specific data source |
| NiceName | string | Yes | Human-readable name for the connector (max 27 characters) |
| Token20 | binary | Yes | Authentication token stored as hex (20 bytes) |
| UIVersion | string | No | Client UI version for compatibility tracking |
| IP | int | Yes | Client IP address stored as integer |
| LastAccess | datetime | Yes | Timestamp of last session access |

**Validation Rules:**
- `NiceName` must not exceed 27 characters
- `Token20` is stored as binary hex data (40 character hex string = 20 bytes)
- `IP` is converted from dotted notation using `ip2long()`
- `LastAccess` is updated on each session access

**Example JSON:**
```json
{
  "SID": 12345,
  "OrgID": 100,
  "DataConnectorID": 5,
  "FeedID": 789,
  "NiceName": "Salesforce Production",
  "Token20": "a1b2c3d4e5f6789012345678901234567890abcd",
  "UIVersion": "2.5.1",
  "IP": 3232235777,
  "LastAccess": "2024-01-15T10:30:00Z"
}
```

**Relationships:**
- One-to-one with connector-specific session tables (via `SID`)
- One-to-many with `tokentofeed` (via token)

---

### Auth_Token_Parsed

Parsed authentication token structure used after validating and decoding a session token.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID extracted from token |
| ConnectorName | string | Yes | Connector name resolved from DataConnectorID |
| Token | string | Yes | 40-character SHA1 token hash |
| OrgID | int | Yes | Organization ID from session |
| DataConnectorID | int | Yes | Data connector ID from session |
| NiceName | string | Yes | Nice name from session |

**Validation Rules:**
- `Token` must be exactly 40 hexadecimal characters
- `SID` must exist in Sessions table
- Token must match stored `Token20` value

**Example JSON:**
```json
{
  "SID": 12345,
  "ConnectorName": "salesforce",
  "Token": "a1b2c3d4e5f6789012345678901234567890abcd",
  "OrgID": 100,
  "DataConnectorID": 5,
  "NiceName": "Salesforce Production"
}
```

---

### tokentofeed

Database table mapping authentication tokens to feeds for multi-feed session support.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Token | string | Yes | Authentication token (primary key) |
| Feeds | string | Yes | Comma-separated feed IDs or serialized feed data |
| Context | text | No | Serialized FeedModelContext object |

**Validation Rules:**
- `Token` must be unique
- `Feeds` contains valid feed identifiers
- `Context` must be valid serialized PHP object when present

**Example JSON:**
```json
{
  "Token": "a1b2c3d4e5f6789012345678901234567890abcd",
  "Feeds": "101,102,103",
  "Context": "O:16:\"FeedModelContext\":7:{s:14:\"CurrentMessage\";i:0;...}"
}
```

**Relationships:**
- Links tokens to multiple feeds
- Contains serialized `FeedModelContext`

---

### tokentosfsession

Database table specifically for mapping tokens to Salesforce sessions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Token | string | Yes | Authentication token |
| FeedId | integer | Yes | Feed identifier |
| Location | string | Yes | Salesforce endpoint location URL |
| SessionId | string | Yes | Salesforce session ID |
| wsdl | string | Yes | WSDL file path (enterprise.wsdl.xml or partner.wsdl.xml) |

**Validation Rules:**
- `wsdl` must be either `enterprise.wsdl.xml` or `partner.wsdl.xml`
- `Location` must be a valid Salesforce API endpoint URL

**Example JSON:**
```json
{
  "Token": "a1b2c3d4e5f6789012345678901234567890abcd",
  "FeedId": 456,
  "Location": "https://na1.salesforce.com/services/Soap/u/52.0/00D000000000001",
  "SessionId": "00D000000000001!AQcAQH8...",
  "wsdl": "partner.wsdl.xml"
}
```

---

### FeedModelContext

Context data maintained between calls to the MessageGateway API for stateful operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| CurrentMessage | mixed | No | Current message index in navigation |
| UnreadMessages | array | No | Array of unread message identifiers |
| ReadMessages | array | No | Array of read message identifiers |
| UnreadFlag | boolean | No | Flag indicating if there are unread messages |
| NoMoreMessages | boolean | No | Flag indicating no more messages available |
| SwitchBackToUnread | mixed | No | Switch back to unread navigation flag |
| SwitchBackToUnreadID | mixed | No | ID for switching back to unread context |
| feedxml | string | No | XML feed data for serialization |

**Example JSON:**
```json
{
  "CurrentMessage": 5,
  "UnreadMessages": [1, 3, 7, 12],
  "ReadMessages": [2, 4, 5, 6],
  "UnreadFlag": true,
  "NoMoreMessages": false,
  "SwitchBackToUnread": false,
  "SwitchBackToUnreadID": null,
  "feedxml": "<feed><type>salesforce</type>...</feed>"
}
```

---

## Platform-Specific Session Models

### Sessions_Salesforce

Database table for storing Salesforce-specific session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID (foreign key to Sessions table) |
| AuthType | string | Yes | Authentication type (e.g., oauth, password) |
| SFToken | string | Yes | Salesforce session token |
| Location | string | Yes | Salesforce API location URL |
| WSDL | string | Yes | WSDL type (partner or enterprise) |
| ApexWsdlURI | string | No | Apex WSDL URI for custom Apex calls |
| ApexWsdlPath | string | No | Local Apex WSDL file path |
| Timeout | integer | Yes | Session timeout in minutes |

**Validation Rules:**
- `SID` must reference existing Sessions record
- `WSDL` must be either "partner" or "enterprise"
- `Timeout` typically defaults to 120 minutes

**Example JSON:**
```json
{
  "SID": 12345,
  "AuthType": "oauth",
  "SFToken": "00D000000000001!AQcAQH8xyzabc...",
  "Location": "https://na1.salesforce.com/services/Soap/u/52.0/00D000000000001",
  "WSDL": "partner",
  "ApexWsdlURI": "https://na1.salesforce.com/services/wsdl/apex",
  "ApexWsdlPath": "/var/cache/apex_wsdl_12345.xml",
  "Timeout": 120
}
```

---

### Sessions_Sugarcrm

Database table for SugarCRM connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID - Foreign key to Sessions |
| SugarToken | string | Yes | SugarCRM authentication token |
| PhpSessionId | string | Yes | PHP session identifier from SugarCRM |
| EndPoint | string | Yes | SOAP endpoint URL |
| Timeout | int | Yes | Session timeout in minutes |

**Example JSON:**
```json
{
  "SID": 12346,
  "SugarToken": "sugar_session_abc123def456",
  "PhpSessionId": "php_sess_789xyz",
  "EndPoint": "https://crm.example.com/soap.php",
  "Timeout": 60
}
```

---

### Sessions_Zendesk

Database table for Zendesk connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID - Foreign key to Sessions |
| User | string | Yes | Zendesk username (may include /token suffix for API token auth) |
| Pword | string | Yes | Encrypted password or API token |
| Server | string | Yes | Zendesk server URL |
| Timeout | int | Yes | Session timeout in minutes |

**Validation Rules:**
- `User` with `/token` suffix indicates API token authentication
- `Server` must be valid Zendesk subdomain URL

**Example JSON:**
```json
{
  "SID": 12347,
  "User": "agent@company.com/token",
  "Pword": "encrypted_api_token_value",
  "Server": "https://company.zendesk.com",
  "Timeout": 480
}
```

---

### Sessions_Gooddata

Database table for GoodData connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID - Foreign key to Sessions |
| User | string | Yes | GoodData username |
| Pword | string | Yes | Encrypted password |
| Server | string | Yes | GoodData server URL |
| GDCAuthTT | string | Yes | GoodData temporary authentication token |
| GDCAuthSST | string | Yes | GoodData super secure token |
| ProjectEndpoint | string | Yes | GoodData project metadata endpoint |
| Timeout | int | Yes | Session timeout in minutes |

**Validation Rules:**
- Both `GDCAuthTT` and `GDCAuthSST` required for authenticated requests
- `ProjectEndpoint` must be valid GoodData project path

**Example JSON:**
```json
{
  "SID": 12348,
  "User": "analyst@company.com",
  "Pword": "encrypted_password",
  "Server": "https://secure.gooddata.com",
  "GDCAuthTT": "tt_temporary_token_abc123",
  "GDCAuthSST": "sst_super_secure_token_xyz789",
  "ProjectEndpoint": "/gdc/projects/abc123project",
  "Timeout": 30
}
```

---

### Sessions_Ldap

Database table for LDAP connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Session ID - Foreign key to Sessions |
| UserRDn | string | Yes | User relative distinguished name |
| ParentDn | string | Yes | Parent distinguished name |
| Pword | string | Yes | Encrypted password |
| Service | string | Yes | LDAP service type (e.g., MSAD for Microsoft AD) |
| TlsCertfile | string | No | TLS certificate file content |
| TlsKeyfile | string | No | TLS key file content |
| Server | string | Yes | LDAP server URL |
| Timeout | int | Yes | Session timeout in minutes |

**Validation Rules:**
- `Service` determines attribute mapping (MSAD for Microsoft Active Directory)
- TLS files required for secure LDAP connections

**Example JSON:**
```json
{
  "SID": 12349,
  "UserRDn": "cn=ServiceAccount",
  "ParentDn": "ou=ServiceAccounts,dc=company,dc=com",
  "Pword": "encrypted_ldap_password",
  "Service": "MSAD",
  "TlsCertfile": "-----BEGIN CERTIFICATE-----\nMIID...",
  "TlsKeyfile": "-----BEGIN PRIVATE KEY-----\nMIIE...",
  "Server": "ldaps://ldap.company.com:636",
  "Timeout": 60
}
```

---

### Sessions_Msdynamics

Database table for Microsoft Dynamics CRM connector session data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID (foreign key to Sessions table) |
| User | string | Yes | Username |
| Pword | string | Yes | Encrypted password |
| Organization | string | Yes | Organization name |
| Server | string | Yes | Server URL |
| AuthType | string | Yes | Authentication type (ad, spla, passport) |
| CrmTicket | string | Yes | CRM security header/ticket |
| CrmServiceUrl | string | Yes | CRM organization service URL |
| Timeout | integer | Yes | Session timeout in minutes |

**Validation Rules:**
- `AuthType` must be one of: `ad`, `spla`, `passport`
- `CrmTicket` contains encrypted security header for SOAP requests

**Example JSON:**
```json
{
  "SID": 12350,
  "User": "crm_user@company.onmicrosoft.com",
  "Pword": "encrypted_dynamics_password",
  "Organization": "companycrm",
  "Server": "https://company.crm.dynamics.com",
  "AuthType": "spla",
  "CrmTicket": "<SecurityHeader>encrypted_ticket_data</SecurityHeader>",
  "CrmServiceUrl": "https://company.api.crm.dynamics.com/XRMServices/2011/Organization.svc",
  "Timeout": 120
}
```

---

### Sessions_Workbooks

Database table for storing Workbooks CRM session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID from Sessions table |
| User | string | Yes | Workbooks username |
| AuthenticityToken | string | Yes | Workbooks authenticity token (CSRF protection) |
| SessionId | string | Yes | Workbooks session ID |
| Timeout | integer | Yes | Auth token lifetime in minutes |

**Example JSON:**
```json
{
  "SID": 12351,
  "User": "user@company.com",
  "AuthenticityToken": "authenticity_abc123xyz789",
  "SessionId": "workbooks_session_def456",
  "Timeout": 60
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

**Example JSON:**
```json
{
  "SID": 12352,
  "Usr": "oracle_user",
  "Pword": "encrypted_oracle_password",
  "Server": "https://company.oraclecloud.com",
  "Timeout": 60
}
```

---

### Sessions_Mpp

Database table for storing MPP payment gateway session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID (foreign key to Sessions table) |
| ClientId | string | Yes | MPP client identifier |
| Pword | string | Yes | Encrypted password |
| Guid | string | Yes | MPP GUID token for authenticated requests |
| Server | string | Yes | Server URL |
| Timeout | integer | Yes | Session timeout |

**Example JSON:**
```json
{
  "SID": 12353,
  "ClientId": "mpp_client_12345",
  "Pword": "encrypted_mpp_password",
  "Guid": "550e8400-e29b-41d4-a716-446655440000",
  "Server": "https://api.mppglobal.com",
  "Timeout": 30
}
```

---

### Sessions_Custom

Database table for storing Custom connector session information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | integer | Yes | Session ID from Sessions table |
| Server | string | Yes | Custom server URL |
| Timeout | integer | Yes | Auth token lifetime in minutes |

**Example JSON:**
```json
{
  "SID": 12354,
  "Server": "https://custom-api.company.com",
  "Timeout": 120
}
```

---

## Authentication Payload Models

These models define the XML payload structures used when authenticating to various platforms.

### SugarCRM_Feed_XML

XML payload structure for SugarCRM feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be "sugarcrm") |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | SugarCRM server URL |
| nicename | string | Yes | Display name for the feed |
| username | string | Yes | SugarCRM username |
| password | string | Yes | SugarCRM password |

**Example JSON:**
```json
{
  "type": "sugarcrm",
  "feedid": "101",
  "server": "https://crm.company.com",
  "nicename": "Production CRM",
  "username": "api_user",
  "password": "secure_password"
}
```

---

### Zendesk_Feed_XML

XML payload structure for Zendesk feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be "zendesk") |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | Zendesk server URL |
| username | string | Yes | Zendesk username/email |
| password | string | Conditional | Zendesk password (alternative to token) |
| token | string | Conditional | Zendesk API token (alternative to password) |

**Validation Rules:**
- Either `password` or `token` must be provided, not both
- When using `token`, append `/token` to username

**Example JSON:**
```json
{
  "type": "zendesk",
  "feedid": "102",
  "server": "https://company.zendesk.com",
  "username": "agent@company.com",
  "token": "api_token_xyz789"
}
```

---

### GoodData_Feed_XML

XML payload structure for GoodData feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be "gooddata") |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | GoodData server URL |
| username | string | Yes | GoodData username/email |
| password | string | Yes | GoodData password |
| project_title | string | Yes | GoodData project title to connect to |

**Example JSON:**
```json
{
  "type": "gooddata",
  "feedid": "103",
  "server": "https://secure.gooddata.com",
  "username": "analyst@company.com",
  "password": "gooddata_password",
  "project_title": "Sales Analytics Dashboard"
}
```

---

### LDAP_Feed_XML

XML payload structure for LDAP feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (must be "ldap") |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | LDAP server URL |
| service | string | Yes | LDAP service type (e.g., MSAD) |
| parentdn | string | Yes | Parent distinguished name |
| userrdn | string | Yes | User relative distinguished name |
| password | string | Yes | LDAP password |
| tlscertfile | string | No | TLS certificate filename |
| tlskeyfile | string | No | TLS key filename |

**Example JSON:**
```json
{
  "type": "ldap",
  "feedid": "104",
  "server": "ldaps://ldap.company.com:636",
  "service": "MSAD",
  "parentdn": "ou=Users,dc=company,dc=com",
  "userrdn": "cn=ServiceAccount",
  "password": "ldap_password",
  "tlscertfile": "ldap_client.crt",
  "tlskeyfile": "ldap_client.key"
}
```

---

### Msdynamics_Feed_Payload

XML payload structure for Microsoft Dynamics authentication feed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be "msdynamics") |
| feedid | integer | Yes | Feed identifier |
| nicename | string | Yes | Display name for the feed |
| authtype | string | Yes | Authentication type (ad, spla, passport) |
| server | string | Yes | CRM server URL |
| organization | string | Yes | Organization name |
| username | string | Yes | Username for authentication |
| password | string | Yes | Password for authentication |

**Validation Rules:**
- `authtype` must be one of: `ad`, `spla`, `passport`

**Example JSON:**
```json
{
  "type": "msdynamics",
  "feedid": 105,
  "nicename": "Dynamics CRM Production",
  "authtype": "spla",
  "server": "https://company.crm.dynamics.com",
  "organization": "companycrm",
  "username": "crm_user@company.onmicrosoft.com",
  "password": "dynamics_password"
}
```

---

### WorkbooksFeedPayload

XML payload structure for Workbooks authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be "workbooks") |
| feedid | integer | Yes | Feed identifier |
| server | string | Yes | Workbooks server URL |
| nicename | string | Yes | Human-readable feed name |
| username | string | Yes | Workbooks username |
| password | string | Yes | Workbooks password |
| dbname | string | No | Database name for multi-database accounts |

**Example JSON:**
```json
{
  "type": "workbooks",
  "feedid": 106,
  "server": "https://secure.workbooks.com",
  "nicename": "Workbooks CRM",
  "username": "user@company.com",
  "password": "workbooks_password",
  "dbname": "production_db"
}
```

---

### OracleFusionFeedPayload

XML payload structure for Oracle Fusion authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be "oraclefusion") |
| feedid | integer | Yes | Feed identifier |
| server | string | Yes | Oracle Fusion server URL |
| nicename | string | Yes | Human-readable feed name |
| username | string | Yes | Oracle Fusion username |
| password | string | Yes | Oracle Fusion password |

**Example JSON:**
```json
{
  "type": "oraclefusion",
  "feedid": 107,
  "server": "https://company.oraclecloud.com",
  "nicename": "Oracle Fusion CRM",
  "username": "oracle_user",
  "password": "oracle_password"
}
```

---

### CustomFeedPayload

XML payload structure for Custom connector authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be "custom") |
| feedid | integer | Yes | Feed identifier |
| authtype | string | Yes | Authentication type (e.g., basic) |
| nicename | string | Yes | Human-readable feed name |
| server | string | Yes | Custom server URL |
| username | string | Yes | Username |
| password | string | Yes | Password |
| clientkey | string | No | Optional client key |
| applicationkey | string | Yes | Server/application key for validation |

**Example JSON:**
```json
{
  "type": "custom",
  "feedid": 108,
  "authtype": "basic",
  "nicename": "Custom API Integration",
  "server": "https://api.custom-service.com",
  "username": "api_user",
  "password": "api_password",
  "clientkey": "client_key_abc123",
  "applicationkey": "app_key_xyz789"
}
```

---

### Http_Feed_Payload

XML payload structure for HTTP authentication feed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (must be "http") |
| feedid | integer | Yes | Feed identifier |
| accounttype | string | Yes | Account type |
| location | string | Yes | URL location |
| nicename | string | Yes | Display name for the feed |

**Example JSON:**
```json
{
  "type": "http",
  "feedid": 109,
  "accounttype": "rest",
  "location": "https://api.external-service.com",
  "nicename": "External REST API"
}
```

---

### MysqlconFeedConfig

MySQL connector feed configuration parameters.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | MySQL username |
| password | string | Yes | MySQL password |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | MySQL server address with optional port |
| dbname | string | Yes | Database name |
| ssl_ca | string | No | SSL CA certificate path |

**Example JSON:**
```json
{
  "username": "db_user",
  "password": "db_password",
  "feedid": "110",
  "server": "mysql.company.com:3306",
  "dbname": "analytics_db",
  "ssl_ca": "/path/to/ca-cert.pem"
}
```

---

## Security Models

### SecurityData

Microsoft Dynamics security data object returned from Live ID authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| keyIdentifier | string | Yes | Key identifier for security token |
| securityToken0 | string | Yes | First encrypted security token (CipherValue) |
| securityToken1 | string | Yes | Second encrypted security token (CipherValue) |

**Example JSON:**
```json
{
  "keyIdentifier": "key_id_abc123",
  "securityToken0": "encrypted_cipher_value_token_0",
  "securityToken1": "encrypted_cipher_value_token_1"
}
```

---

## Authentication Handler Classes

### Auth_Salesforce

Authorization class that supports the Salesforce API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SforceConnection | object | Yes | Salesforce connection object |
| dbConn | Database | Yes | Database connection object |
| response_timeout | integer | Yes | Response timeout value |
| sApexWsdlFile | string | No | Apex WSDL file path |
| sApexWsdlURI | string | No | Apex WSDL URI |

---

### Auth_Msdynamics

Microsoft Dynamics CRM authentication class for message gateway API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MSDConnection | object | Yes | Microsoft Dynamics connection object |
| dbConn | object | Yes | Database connection object |
| response_timeout | integer | Yes | Response timeout in seconds |
| aMsdInfo | array | Yes | MS Dynamics auth info including HeaderSecurity and OrgServiceURI |

---

### Auth_Workbooks

Authorisation class that supports the Workbooks API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| response_timeout | string | Yes | Time limit to get response |
| aWbInfo | array | Yes | Workbooks info containing AuthenticityToken and SessionId |

---

### Auth_Oraclefusion

Authorisation class that supports the Oracle Fusion API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| response_timeout | string | Yes | Time limit to get response |
| aOracleFusionInfo | array | Yes | Oracle Fusion connection info |

---

### Auth_Mpp

Authorization class for MPP payment gateway connector.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nFeedid | integer | Yes | Feed identifier |
| oDbConn | Database | Yes | Database connection object |
| nResponse_timeout | integer | Yes | Response timeout value |
| sServer | string | Yes | Server URL |
| aMppInfo | array | Yes | MPP information including GUID |

---

### Auth_Custom

Authorisation class that supports the Generic Developer Interface.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| response_timeout | integer | Yes | Time limit to get response |

---

### Auth_Http

HTTP API authentication class for message gateway (stub implementation).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| feedid | integer | Yes | Feed identifier |
| dbConn | object | Yes | Database connection object |

---

### Auth_Mysqlcon

MySQL connector authentication class.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| php_sessionid | string | No | PHP session ID |
| response_timeout | integer | Yes | Response timeout |

---

## Common Use Cases

### 1. Creating a New Session

```php
// 1. Parse feed XML payload
$feedPayload = new Salesforce_Feed_XML($xmlData);

// 2. Authenticate with platform
$auth = new Auth_Salesforce($dbConn);
$sessionData = $auth->authenticate($feedPayload);

// 3. Create master session record
$session = new Sessions();
$session->OrgID = $orgId;
$session->DataConnectorID = CONNECTOR_SALESFORCE;
$session->FeedID = $feedPayload->feedid;
$session->NiceName = $feedPayload->nicename;
$session->Token20 = generateToken();
$session->save();

// 4. Create platform-specific session
$sfSession = new Sessions_Salesforce();
$sfSession->SID = $session->SID;
$sfSession->SFToken = $sessionData['token'];
$sfSession->Location = $sessionData['location'];
$sfSession->save();
```

### 2. Validating and Parsing Tokens

```php
// Parse incoming token
$parsedToken = parseToken($rawToken);

// Validate session exists and is active
$session = Sessions::findBySID($parsedToken->SID);
if ($session->Token20 !== $parsedToken->Token) {
    throw new AuthenticationException('Invalid token');
}

// Check session timeout
$connectorSession = getConnectorSession($session->DataConnectorID, $session->SID);
if (isExpired($session->LastAccess, $connectorSession->Timeout)) {
    throw new SessionExpiredException('Session expired');
}
```

### 3. Multi-Feed Token Mapping

```php
// Map token to multiple feeds
$tokenMap = new tokentofeed();
$tokenMap->Token = $authToken;
$tokenMap->Feeds = implode(',', [$feed1Id, $feed2Id, $feed3Id]);
$tokenMap->Context = serialize(new FeedModelContext());
$tokenMap->save();
```

---

## Related Documentation

- [Feed Models](feed-models.md) - Feed configuration and message handling
- [API Response Models](api-response-models.md) - Response structures for authentication endpoints
- [Platform Models](platform-models.md) - Platform-specific integration models