# Data Models Overview

## Introduction

The Platform Service Gateway (PSG) implements a comprehensive data model architecture supporting multi-platform CRM and service integrations. The gateway acts as a unified interface to various external systems including Salesforce, Microsoft Dynamics, Zendesk, Oracle Fusion, SugarCRM, Workbooks, GoodData, LDAP directories, and custom HTTP endpoints.

This document provides a high-level overview of the data architecture and serves as an index to detailed model documentation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API Response Layer                                │
│                    (Standardized response formats)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Session Management                                  │
│           (Authentication tokens, connector sessions, timeouts)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │    Feed      │  │   Platform   │  │   Message    │
         │   Configs    │  │   Connectors │  │   Storage    │
         └──────────────┘  └──────────────┘  └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        External Systems                                      │
│  Salesforce │ Dynamics │ Zendesk │ Oracle │ SugarCRM │ LDAP │ Custom │ etc │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Model Categories

The PSG data models are organized into four primary categories:

### 1. Session Models
**Purpose:** Manage authentication state and connector-specific session data across all integrated platforms.

**Scope:** 15+ session table models covering base sessions and platform-specific extensions.

**Key Responsibilities:**
- Authentication token management
- Session timeout handling
- Platform-specific credential storage
- Connection state persistence

[**→ Detailed Session Models Documentation**](docs/models/session-models.md)

---

### 2. Feed Models
**Purpose:** Define configuration and authentication payloads for data feed connections.

**Scope:** 12+ feed configuration models spanning all supported platforms.

**Key Responsibilities:**
- Feed authentication parameters
- Connection endpoint configuration
- Protocol-specific settings (SSL/TLS, ports, etc.)
- Feed context and state management

[**→ Detailed Feed Models Documentation**](docs/models/feed-models.md)

---

### 3. Platform Models
**Purpose:** Define platform-specific data structures, field mappings, and object schemas.

**Scope:** 40+ models covering CRM entities, field definitions, and platform-specific structures.

**Key Responsibilities:**
- CRM object definitions (Contacts, Tasks, Accounts, etc.)
- Field metadata and validation rules
- Platform API response parsing
- Object relationship mapping

[**→ Detailed Platform Models Documentation**](docs/models/platform-models.md)

---

### 4. API Response Models
**Purpose:** Standardize response formats across all gateway operations.

**Scope:** 10+ response models for various operation types.

**Key Responsibilities:**
- Unified error code system
- Result data formatting
- Field list responses
- Operation status reporting

[**→ Detailed API Response Models Documentation**](docs/models/api-response-models.md)

---

## Model Index by Category

### Session Models

| Model | Description |
|-------|-------------|
| `Sessions` | Base session table with common fields |
| `Sessions_Salesforce` | Salesforce OAuth and session tokens |
| `Sessions_Msdynamics` | Microsoft Dynamics CRM tickets |
| `Sessions_Zendesk` | Zendesk API credentials |
| `Sessions_Sugarcrm` | SugarCRM session data |
| `Sessions_Gooddata` | GoodData authentication tokens |
| `Sessions_Ldap` | LDAP connection parameters |
| `Sessions_Workbooks` | Workbooks CRM session |
| `Sessions_Oraclefusion` | Oracle Fusion credentials |
| `Sessions_Mpp` | MPP payment gateway session |
| `Sessions_Mysqlcon` | MySQL direct connection |
| `Sessions_Custom` | Custom connector sessions |
| `Auth_Token_Parsed` | Parsed authentication token structure |
| `tokentofeed` | Token to feed mapping table |
| `tokentosfsession` | Salesforce session token mapping |

### Feed Models

| Model | Description |
|-------|-------------|
| `SugarCRM_Feed_XML` | SugarCRM feed authentication payload |
| `Zendesk_Feed_XML` | Zendesk feed configuration |
| `GoodData_Feed_XML` | GoodData project connection |
| `LDAP_Feed_XML` | LDAP directory feed settings |
| `Msdynamics_Feed_Payload` | MS Dynamics authentication |
| `Http_Feed_Payload` | Generic HTTP endpoint feed |
| `Imap_Feed_Payload` | IMAP email feed configuration |
| `WorkbooksFeedPayload` | Workbooks CRM feed |
| `CustomFeedPayload` | Custom connector feed |
| `OracleFusionFeedPayload` | Oracle Fusion feed |
| `ExchangeFeedConfig` | Exchange server WebDAV feed |
| `MysqlconFeedConfig` | MySQL direct connection feed |
| `FeedModelContext` | Feed state context container |

### Platform Models

#### Salesforce
| Model | Description |
|-------|-------------|
| `SalesforceContact` | Contact record structure |
| `SalesforceTask` | Task/Activity structure |
| `Task_Salesforce_Payload` | Task creation payload |
| `Salesforce_Task_Fields` | Internal task field mapping |
| `SalesforceActivityPayload` | Activity addition payload |

#### Microsoft Dynamics
| Model | Description |
|-------|-------------|
| `Msdynamics` | Dynamics connection wrapper |
| `MSDynamics_FieldList_Item` | Field metadata structure |
| `SecurityData` | Live ID authentication data |

#### Zendesk
| Model | Description |
|-------|-------------|
| `Zendesk_ObjectList` | Supported Zendesk objects |
| `Zendesk_FieldTranslations` | Field name mappings |
| `ZendeskOrganization` | Organization resource |
| `ZendeskGroup` | Group resource |
| `ZendeskTicket` | Ticket resource |
| `ZendeskTicketMetrics` | Ticket metrics resource |

#### Oracle Fusion
| Model | Description |
|-------|-------------|
| `Oraclefusion_Objects` | Supported Oracle objects |
| `Oraclefusion_Field` | Field metadata |

#### Workbooks
| Model | Description |
|-------|-------------|
| `WorkbooksApi` | Workbooks API wrapper |

#### MPP Payment Gateway
| Model | Description |
|-------|-------------|
| `MppUserAccount` | User account fields |
| `MppApiResponse` | API response structure |

#### LDAP
| Model | Description |
|-------|-------------|
| `LdapConnectionConfig` | LDAP connection parameters |

#### Generic/Utility
| Model | Description |
|-------|-------------|
| `Expression` | Query filter expression |
| `Xml` | XML parser class |
| `Xml_Element` | Parsed XML element |
| `MessageObject` | Feed message container |
| `ExchangeMessage` | Exchange email message |
| `ExchangeUser` | Exchange WebDAV user |

### Message & Storage Models

| Model | Description |
|-------|-------------|
| `inbox` | Message inbox storage |
| `content` | Message content storage |
| `recordsbuffer` | Metadata cache storage |
| `Imap_Message_Result` | IMAP message parse result |

### API Response Models

| Model | Description |
|-------|-------------|
| `API_Response` | Standard response envelope |
| `HttpResponse` | HTTP connector response |
| `MppApiResponse` | MPP payment response |

---

## Cross-Category Relationships

### Session → Feed Relationships

```
Sessions (base)
    │
    ├── Sessions_Salesforce ←→ tokentosfsession ←→ Feed_Salesforce
    │
    ├── Sessions_Zendesk ←→ Zendesk_Feed_XML
    │
    ├── Sessions_Msdynamics ←→ Msdynamics_Feed_Payload
    │
    ├── Sessions_Workbooks ←→ WorkbooksFeedPayload
    │
    └── [other connectors follow same pattern]
```

### Token Flow

```
Authentication Request
        │
        ▼
    Feed XML Payload ──→ Platform Auth Class
        │                       │
        ▼                       ▼
    Sessions (base) ◄─── Sessions_[Platform]
        │
        ▼
    tokentofeed ──→ FeedModelContext
        │
        ▼
    API Operations
```

### Data Query Flow

```
API Request + Token
        │
        ▼
    Session Lookup (Sessions + Sessions_[Platform])
        │
        ▼
    Platform Connector (Sgapi_[Platform])
        │
        ▼
    Platform Models (Objects, Fields, etc.)
        │
        ▼
    API_Response (standardized)
```

---

## Supported Platforms Summary

| Platform | Auth Model | Feed Model | API Class |
|----------|------------|------------|-----------|
| Salesforce | `Auth_Salesforce` | `Feed_Salesforce` | `Sgapi_Salesforce` |
| Microsoft Dynamics | `Auth_Msdynamics` | `Msdynamics_Feed_Payload` | `Msdynamics` |
| Zendesk | (inline) | `Zendesk_Feed_XML` | `Sgapi_Zendesk` |
| Oracle Fusion | `Auth_Oraclefusion` | `OracleFusionFeedPayload` | `Sgapi_Oraclefusion` |
| SugarCRM | (inline) | `SugarCRM_Feed_XML` | `Sgapi_Sugarcrm` |
| Workbooks | `Auth_Workbooks` | `WorkbooksFeedPayload` | `Sgapi_Workbooks` |
| GoodData | (inline) | `GoodData_Feed_XML` | `Sgapi_Gooddata` |
| LDAP | (inline) | `LDAP_Feed_XML` | `Sgapi_Ldap` |
| MPP Payment | `Auth_Mpp` | (custom) | `Sgapi_Mpp` |
| MySQL | `Auth_Mysqlcon` | `MysqlconFeedConfig` | `Sgapi_Mysqlcon` |
| HTTP | `Auth_Http` | `Http_Feed_Payload` | `Sgapi_Http` |
| Exchange | (inline) | `ExchangeFeedConfig` | `Feed_Exchange` |
| IMAP | (inline) | `Imap_Feed_Payload` | `Feed_Imap` |
| Custom | `Auth_Custom` | `CustomFeedPayload` | (custom) |

---

## Error Code Reference

All models returning `API_Response` use the `MGWERR_*` error code system:

| Code | Constant | Description |
|------|----------|-------------|
| 0 | `MGWERR_SUCCESS` | Operation successful |
| 1xx | `MGWERR_AUTH_*` | Authentication errors |
| 2xx | `MGWERR_QUERY_*` | Query/operation errors |
| 3xx | `MGWERR_CONN_*` | Connection errors |
| 4xx | `MGWERR_DATA_*` | Data validation errors |

---

## Navigation

- **[Session Models](docs/models/session-models.md)** - Authentication and session management
- **[Feed Models](docs/models/feed-models.md)** - Feed configuration and authentication
- **[Platform Models](docs/models/platform-models.md)** - Platform-specific data structures
- **[API Response Models](docs/models/api-response-models.md)** - Response format specifications