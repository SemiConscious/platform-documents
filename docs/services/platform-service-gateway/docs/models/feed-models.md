# Feed and Inbox Models

This document covers the data models used for feed subscriptions, inbox message management, and XML processing in the Platform Service Gateway. These models handle the storage and retrieval of messages from various external feed sources including IMAP, Exchange, and custom HTTP feeds.

## Overview

Feed and Inbox models provide the infrastructure for:
- Message inbox storage and retrieval
- Feed subscription management
- Feed context persistence between API calls
- XML payload parsing for feed configuration
- Protocol-specific feed implementations

## Entity Relationship Diagram

```
┌─────────────────────┐
│   tokentofeed       │
│  (Token Mapping)    │
├─────────────────────┤
│ Token               │──────────────────────────────────┐
│ Feeds               │                                  │
│ Context             │──────┐                           │
└─────────────────────┘      │                           │
                             ▼                           │
                    ┌─────────────────────┐              │
                    │  FeedModelContext   │              │
                    │  (Runtime Context)  │              │
                    ├─────────────────────┤              │
                    │ CurrentMessage      │              │
                    │ UnreadMessages      │              │
                    │ ReadMessages        │              │
                    │ feedxml             │              │
                    └─────────────────────┘              │
                                                         │
                    ┌─────────────────────┐              │
                    │       inbox         │◄─────────────┘
                    │  (Message Store)    │
                    ├─────────────────────┤
                    │ MessageID (PK)      │
                    │ Feed                │
                    │ FeedMsgID           │
                    │ Read                │
                    │ Arrived             │
                    └─────────────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │      content        │
                    │  (Message Bodies)   │
                    ├─────────────────────┤
                    │ Feed                │
                    │ FeedMsgID           │
                    │ Content             │
                    └─────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  Feed XML Payloads                       │
├─────────────────────┬─────────────────┬─────────────────┤
│  Imap_Feed_Payload  │ Http_Feed_Payload│ ExchangeFeed   │
│  SugarCRM_Feed_XML  │ Zendesk_Feed_XML │ GoodData_XML   │
│  LDAP_Feed_XML      │ MSDynamics_Feed  │ Oraclefusion   │
└─────────────────────┴─────────────────┴─────────────────┘
```

---

## Core Inbox Models

### inbox

Database table for storing messages retrieved from external feed sources.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MessageID | bigint | Yes | Auto-generated unique message identifier (Primary Key) |
| Feed | integer | Yes | Feed identifier linking to the feed source |
| FeedMsgID | string | Yes | Protocol-specific message ID from the source system |
| Arrived | datetime | Yes | Timestamp when message arrived in the inbox |
| ArrivedUNIX | integer | No | Arrival time as Unix timestamp (computed field) |
| Refreshed | datetime | No | Timestamp of last refresh/sync operation |
| Sender | string | No | Message sender identifier or email address |
| Subject | string | No | Message subject line |
| Attachments | string | No | Description of message attachments |
| Read | char(1) | Yes | Read status flag: 'y' for read, 'n' for unread |

**Validation Rules:**
- `MessageID` is auto-incremented
- `Read` must be either 'y' or 'n'
- `Feed` must reference a valid feed configuration
- `FeedMsgID` combined with `Feed` should be unique

**Example:**
```json
{
  "MessageID": 12345,
  "Feed": 42,
  "FeedMsgID": "<msg123@example.com>",
  "Arrived": "2024-01-15 10:30:00",
  "ArrivedUNIX": 1705314600,
  "Refreshed": "2024-01-15 10:35:00",
  "Sender": "john.doe@example.com",
  "Subject": "Quarterly Report Q4 2023",
  "Attachments": "report.pdf (2.5MB)",
  "Read": "n"
}
```

**Relationships:**
- Links to `content` table via `Feed` + `FeedMsgID`
- Links to feed configurations via `Feed` identifier

---

### content

Database table for storing the actual message body content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Feed | integer | Yes | Feed identifier matching the inbox record |
| FeedMsgID | string | Yes | Protocol-specific message ID (composite key with Feed) |
| Bytes | integer | No | Content size in bytes |
| Content | text | Yes | Full message content/body |

**Validation Rules:**
- Composite key: `Feed` + `FeedMsgID`
- `Content` may contain HTML or plain text depending on message source
- `Bytes` should accurately reflect `Content` length

**Example:**
```json
{
  "Feed": 42,
  "FeedMsgID": "<msg123@example.com>",
  "Bytes": 1524,
  "Content": "Dear Team,\n\nPlease find attached the quarterly report for Q4 2023.\n\nBest regards,\nJohn Doe"
}
```

**Relationships:**
- Links to `inbox` table via `Feed` + `FeedMsgID`

---

## Feed Context Models

### FeedModelContext

Context data that persists between calls to the MessageGateway API, enabling stateful message navigation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| CurrentMessage | mixed | No | Index of the currently selected message |
| UnreadMessages | array | No | Array of unread message identifiers |
| ReadMessages | array | No | Array of read message identifiers |
| UnreadFlag | boolean | No | Flag indicating if there are unread messages |
| NoMoreMessages | boolean | No | Flag indicating end of message list reached |
| SwitchBackToUnread | mixed | No | Flag for switching context back to unread messages |
| SwitchBackToUnreadID | mixed | No | Message ID to return to after viewing read messages |
| feedxml | string | No | Serialized XML feed data for session persistence |

**Validation Rules:**
- Context is serialized and stored in the `tokentofeed` table
- Arrays are JSON-encoded when stored
- `feedxml` must be valid XML when present

**Example:**
```json
{
  "CurrentMessage": 5,
  "UnreadMessages": [12345, 12346, 12347],
  "ReadMessages": [12340, 12341, 12342, 12343, 12344],
  "UnreadFlag": true,
  "NoMoreMessages": false,
  "SwitchBackToUnread": false,
  "SwitchBackToUnreadID": null,
  "feedxml": "<?xml version=\"1.0\"?><feed><type>imap</type><feedid>42</feedid></feed>"
}
```

**Relationships:**
- Stored within `tokentofeed.Context` field
- References messages in `inbox` table

---

### tokentofeed

Database table mapping authentication tokens to feed subscriptions (legacy table).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Token | string | Yes | Authentication token (Primary Key) |
| Feeds | string | Yes | Comma-separated list of feed IDs or feed data |
| Context | text | No | Serialized FeedModelContext data |

**Validation Rules:**
- `Token` must be a valid session token
- `Feeds` format depends on implementation (CSV or structured data)
- `Context` is PHP serialized or JSON encoded

**Example:**
```json
{
  "Token": "abc123def456ghi789jkl012mno345pqr678stu",
  "Feeds": "42,43,44",
  "Context": "O:16:\"FeedModelContext\":7:{s:14:\"CurrentMessage\";i:5;s:14:\"UnreadMessages\";a:3:{i:0;i:12345;i:1;i:12346;i:2;i:12347;}}"
}
```

**Relationships:**
- Links to `Sessions` table via `Token`
- Contains serialized `FeedModelContext`

---

### MessageObject

Convenience class for storing message information during feed refresh operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| msgid | string | Yes | Unique message ID from the feed source |
| feedid | string | Yes | Feed identifier passed from caller |
| messagedate | string | Yes | Date message received, or 'now' for current time |
| sender | string | No | Message sender information |
| subject | string | No | Message subject line |
| attachments | string | No | String describing attachments |
| read | string | Yes | Read flag: 'y' or 'n' |

**Validation Rules:**
- `msgid` must be unique within the feed
- `read` must be 'y' or 'n'
- `messagedate` must be valid date string or 'now'

**Example:**
```json
{
  "msgid": "<unique-msg-id-12345@mail.example.com>",
  "feedid": "42",
  "messagedate": "2024-01-15 10:30:00",
  "sender": "sender@example.com",
  "subject": "Important Update",
  "attachments": "document.pdf, image.png",
  "read": "n"
}
```

**Relationships:**
- Used to populate `inbox` table entries
- Created by feed protocol implementations

---

## Feed Base Classes

### Feed

Abstract base class for feed protocols from which protocol-specific classes are derived.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| handle | resource | No | Connection handle to feed source |
| error_message | string | No | Error message from last operation |
| DB | Database | Yes | Message gateway database connection object |
| OpenTimeout | integer | No | Connection open timeout in seconds |

**Validation Rules:**
- Abstract class - must be extended by protocol implementations
- `handle` is set during connection establishment
- `OpenTimeout` defaults to system configuration if not set

**Example:**
```json
{
  "handle": "<resource:connection>",
  "error_message": null,
  "DB": "<Database:instance>",
  "OpenTimeout": 30
}
```

**Relationships:**
- Parent class for `Feed_Imap`, `Feed_Exchange`, `Feed_Salesforce`
- Uses `inbox` and `content` tables for storage

---

## Protocol-Specific Feed Models

### Feed_Imap

IMAP feed class for email retrieval and parsing via IMAP protocol.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| mbox | resource | No | IMAP mailbox resource handle |
| conn | string | Yes | IMAP connection string |
| feedid | integer | Yes | Feed identifier |
| OpenTimeout | integer | No | Connection timeout (inherited from Feed) |

**Validation Rules:**
- `conn` must be valid IMAP connection string format
- `mbox` is established via `imap_open()` function

**Example:**
```json
{
  "mbox": "<resource:imap>",
  "conn": "{imap.example.com:993/imap/ssl}INBOX",
  "feedid": 42,
  "OpenTimeout": 30
}
```

**Relationships:**
- Extends `Feed` base class
- Configured by `Imap_Feed_Payload`
- Produces `Imap_Message_Result` objects

---

### Imap_Feed_Payload

XML payload structure for IMAP feed authentication configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | IMAP account username |
| password | string | Yes | IMAP account password |
| host | string | Yes | IMAP server hostname |
| feedid | integer | Yes | Feed identifier |
| nicename | string | No | Display name for the feed |
| port | integer | No | IMAP server port (default: 993) |
| ssl | string | No | Enable SSL connection (yes/no) |
| tls | string | No | Enable TLS connection (yes/no) |
| secure | string | No | Enable secure mode (yes/no) |
| protocol | string | No | Protocol type specification |

**Validation Rules:**
- `username` and `password` are required for authentication
- `host` must be valid hostname or IP
- `ssl` and `tls` values must be 'yes' or 'no'
- `port` defaults to 993 for SSL, 143 for non-SSL

**Example:**
```json
{
  "username": "user@example.com",
  "password": "securePassword123",
  "host": "imap.example.com",
  "feedid": 42,
  "nicename": "Work Email",
  "port": 993,
  "ssl": "yes",
  "tls": "no",
  "secure": "yes",
  "protocol": "imap"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>imap</type>
  <feedid>42</feedid>
  <nicename>Work Email</nicename>
  <host>imap.example.com</host>
  <port>993</port>
  <username>user@example.com</username>
  <password>securePassword123</password>
  <ssl>yes</ssl>
  <tls>no</tls>
  <secure>yes</secure>
</feed>
```

**Relationships:**
- Configures `Feed_Imap` instances

---

### Imap_Message_Result

Result structure from analyzing an IMAP message.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | Message body content (text or HTML) |
| attachments | array | No | Array of attachment filenames |

**Validation Rules:**
- `content` is extracted from message body parts
- `attachments` contains only filenames, not full attachment data

**Example:**
```json
{
  "content": "Hello,\n\nThis is the message body.\n\nRegards,\nSender",
  "attachments": [
    "document.pdf",
    "spreadsheet.xlsx",
    "image.png"
  ]
}
```

**Relationships:**
- Produced by `Feed_Imap` message analysis

---

### Feed_Exchange

Feed class supporting Microsoft Exchange server WebDAV protocol.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| feedid | mixed | Yes | ID of the associated feed |
| exch | ExchangeUser | Yes | ExchangeUser instance for authenticated connection |

**Validation Rules:**
- `exch` must be properly authenticated before use
- `feedid` must reference valid feed configuration

**Example:**
```json
{
  "feedid": 45,
  "exch": "<ExchangeUser:instance>"
}
```

**Relationships:**
- Uses `ExchangeUser` for WebDAV operations
- Configured by `ExchangeFeedConfig`
- Produces `ExchangeMessage` objects

---

### ExchangeUser

Exchange server WebDAV protocol class for basic message gateway functionality.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| exchange_server | string | Yes | Hostname of Exchange server |
| exchange_username | string | Yes | Username for Exchange login |
| exchange_password | string | Yes | Password for Exchange login |
| secstr | string | No | Security cookie string for WebDAV calls |

**Validation Rules:**
- `exchange_server` must be reachable hostname
- `secstr` is obtained during authentication

**Example:**
```json
{
  "exchange_server": "mail.company.com",
  "exchange_username": "DOMAIN\\username",
  "exchange_password": "password123",
  "secstr": "sessionid=abc123; path=/exchange/"
}
```

**Relationships:**
- Used by `Feed_Exchange` for WebDAV operations
- Produces `ExchangeMessage` objects

---

### ExchangeMessage

Email message structure returned from Exchange inbox iteration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Message href used as unique identifier |
| permurl | string | No | Permanent URL of message in flat address space |
| subject | string | No | Subject of the message |
| from | string | No | Display name or email address of sender |
| content | string | No | Message content (text version preferred) |
| date | string | Yes | Date message was received (ISO format) |
| read | string | Yes | Read flag: 'y' or 'n' |
| hasattachments | string | No | Attachment flag: 'y' or 'n' |

**Validation Rules:**
- `id` must be unique within the mailbox
- `read` and `hasattachments` must be 'y' or 'n'
- `date` should be ISO 8601 format

**Example:**
```json
{
  "id": "/exchange/user/Inbox/message123.EML",
  "permurl": "mapi://server/user/Inbox/message123",
  "subject": "Meeting Reminder",
  "from": "colleague@company.com",
  "content": "Don't forget about the meeting tomorrow at 10am.",
  "date": "2024-01-15T10:30:00Z",
  "read": "n",
  "hasattachments": "n"
}
```

**Relationships:**
- Produced by `ExchangeUser` inbox iteration
- Mapped to `inbox` table entries

---

### ExchangeFeedConfig

Configuration parameters required for Exchange feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Exchange username (may include domain) |
| password | string | Yes | Exchange password |
| host | string | Yes | Exchange server hostname |
| feedid | string | Yes | Feed identifier |
| nicename | string | No | Display name for the feed |

**Validation Rules:**
- `username` format may be `DOMAIN\user` or `user@domain.com`
- `host` must be valid hostname

**Example:**
```json
{
  "username": "CORP\\jsmith",
  "password": "securePass123",
  "host": "mail.corporation.com",
  "feedid": "45",
  "nicename": "Corporate Email"
}
```

**Relationships:**
- Configures `Feed_Exchange` and `ExchangeUser` instances

---

### Feed_Salesforce

Feed class supporting Salesforce API for message gateway operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| feedid | integer | Yes | Feed identifier |
| salesforce | object | No | Salesforce connection object |
| exch | object | No | Exchange connection object (for hybrid setups) |

**Validation Rules:**
- `feedid` must reference valid Salesforce feed configuration
- `salesforce` is established via SOAP authentication

**Example:**
```json
{
  "feedid": 50,
  "salesforce": "<SforcePartnerClient:instance>",
  "exch": null
}
```

**Relationships:**
- Uses Salesforce session from `Sessions_Salesforce`
- Configured via feed XML payload

---

## HTTP Feed Models

### Sgapi_Http

HTTP feed class for message gateway API supporting HTTP GET/POST requests to external services.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dbConn | object | Yes | Database connection object |
| token | string | Yes | Session authentication token |

**Validation Rules:**
- `token` must be valid session token
- Database connection must be established

**Example:**
```json
{
  "dbConn": "<Database:instance>",
  "token": "abc123def456ghi789jkl012mno345pqr678stu"
}
```

**Relationships:**
- Uses `HttpQueryParameters` for request configuration
- Returns `HttpResponse` structures

---

### Http_Feed_Payload

XML payload structure for HTTP feed authentication configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type identifier (http) |
| feedid | integer | Yes | Feed identifier |
| accounttype | string | No | Account type classification |
| location | string | Yes | Target URL location |
| nicename | string | No | Display name for the feed |

**Validation Rules:**
- `type` must be 'http'
- `location` must be valid URL

**Example:**
```json
{
  "type": "http",
  "feedid": 55,
  "accounttype": "rest",
  "location": "https://api.example.com/data",
  "nicename": "External API Feed"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>http</type>
  <feedid>55</feedid>
  <accounttype>rest</accounttype>
  <location>https://api.example.com/data</location>
  <nicename>External API Feed</nicename>
</feed>
```

**Relationships:**
- Configures `Sgapi_Http` instances

---

### HttpQueryParameters

Virtual model representing HTTP query parameters parsed from API input.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sgAPIHTTPHost | string | Yes | Target HTTP host URL |
| sgAPIMethod | string | Yes | HTTP method (GET or POST) |
| sgAPIHTTPUser | string | No | HTTP basic auth username |
| sgAPIHTTPPass | string | No | HTTP basic auth password |
| sgAPIHTTPTimeout | integer | No | Request timeout in seconds |

**Validation Rules:**
- `sgAPIMethod` must be 'GET' or 'POST'
- `sgAPIHTTPHost` must be valid URL
- If `sgAPIHTTPUser` is set, `sgAPIHTTPPass` should also be set

**Example:**
```json
{
  "sgAPIHTTPHost": "https://api.example.com/endpoint",
  "sgAPIMethod": "POST",
  "sgAPIHTTPUser": "apiuser",
  "sgAPIHTTPPass": "apikey123",
  "sgAPIHTTPTimeout": 30
}
```

**Relationships:**
- Parsed from query parameters by `Sgapi_Http`

---

### HttpResponse

Response structure returned by HTTP connector operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Format | string | Yes | Response format type (Ok, Records, Error) |
| Code | integer | Yes | Response code (MGWERR_SUCCESS on success) |
| resultdata | array | No | Array of result record arrays |
| Summary | string | No | Summary message |
| Message | string | No | Detailed message with record count |

**Validation Rules:**
- `Code` of 0 indicates success (MGWERR_SUCCESS)
- `Format` determines response structure interpretation

**Example:**
```json
{
  "Format": "Records",
  "Code": 0,
  "resultdata": [
    {"id": 1, "name": "Record 1"},
    {"id": 2, "name": "Record 2"}
  ],
  "Summary": "Query successful",
  "Message": "Retrieved 2 records"
}
```

**Relationships:**
- Returned by `Sgapi_Http` query operations

---

## XML Processing Models

### Xml

XML parser class for reading and validating XML content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| log | string | No | Log of parser operations |
| data | object | No | Parsed XML data as nested objects |
| parser | resource | No | XML parser resource handle |
| stack | array | No | Stack for tracking nested elements during parsing |
| index | integer | No | Current stack index during parsing |

**Validation Rules:**
- XML must be well-formed
- Parser uses expat-based PHP XML functions

**Example:**
```json
{
  "log": "Parsed 5 elements successfully",
  "data": {
    "feed": {
      "type": { "_text": "imap" },
      "feedid": { "_text": "42" },
      "host": { "_text": "imap.example.com" }
    }
  },
  "parser": "<resource:xml_parser>",
  "stack": [],
  "index": 0
}
```

**Relationships:**
- Used to parse all feed XML payloads
- Produces `Xml_Element` structures

---

### Xml_Element

Parsed XML element structure created during XML parsing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _text | string | No | Text content of the element |
| _attr | object | No | Object containing element attributes as properties |

**Validation Rules:**
- `_text` contains CDATA or text node content
- `_attr` properties match XML attribute names

**Example:**
```json
{
  "_text": "imap.example.com",
  "_attr": {
    "secure": "yes",
    "port": "993"
  }
}
```

**Relationships:**
- Nested within `Xml.data` structure
- Represents individual XML elements

---

## CRM-Specific Feed XML Payloads

### SugarCRM_Feed_XML

XML payload structure for SugarCRM feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (sugarcrm) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | SugarCRM server URL |
| nicename | string | No | Display name for the feed |
| username | string | Yes | SugarCRM username |
| password | string | Yes | SugarCRM password |

**Validation Rules:**
- `type` must be 'sugarcrm'
- `server` must be valid SugarCRM instance URL

**Example:**
```json
{
  "type": "sugarcrm",
  "feedid": "60",
  "server": "https://crm.company.com/sugarcrm",
  "nicename": "Company CRM",
  "username": "admin",
  "password": "admin123"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>sugarcrm</type>
  <feedid>60</feedid>
  <server>https://crm.company.com/sugarcrm</server>
  <nicename>Company CRM</nicename>
  <username>admin</username>
  <password>admin123</password>
</feed>
```

**Relationships:**
- Configures `Sgapi_Sugarcrm` instances
- Creates `Sessions_Sugarcrm` records

---

### Zendesk_Feed_XML

XML payload structure for Zendesk feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (zendesk) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | Zendesk subdomain URL |
| username | string | Yes | Zendesk username/email |
| password | string | Conditional | Zendesk password (alternative to token) |
| token | string | Conditional | Zendesk API token (alternative to password) |

**Validation Rules:**
- `type` must be 'zendesk'
- Either `password` or `token` must be provided
- `server` format: `https://subdomain.zendesk.com`

**Example:**
```json
{
  "type": "zendesk",
  "feedid": "65",
  "server": "https://company.zendesk.com",
  "username": "agent@company.com",
  "token": "API_TOKEN_abc123xyz789"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>zendesk</type>
  <feedid>65</feedid>
  <server>https://company.zendesk.com</server>
  <username>agent@company.com</username>
  <token>API_TOKEN_abc123xyz789</token>
</feed>
```

**Relationships:**
- Configures `Sgapi_Zendesk` instances
- Creates `Sessions_Zendesk` records

---

### GoodData_Feed_XML

XML payload structure for GoodData analytics feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (gooddata) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | GoodData server URL |
| username | string | Yes | GoodData username/email |
| password | string | Yes | GoodData password |
| project_title | string | Yes | GoodData project title to connect to |

**Validation Rules:**
- `type` must be 'gooddata'
- `project_title` must match existing project name

**Example:**
```json
{
  "type": "gooddata",
  "feedid": "70",
  "server": "https://secure.gooddata.com",
  "username": "analyst@company.com",
  "password": "securePass456",
  "project_title": "Sales Analytics 2024"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>gooddata</type>
  <feedid>70</feedid>
  <server>https://secure.gooddata.com</server>
  <username>analyst@company.com</username>
  <password>securePass456</password>
  <project_title>Sales Analytics 2024</project_title>
</feed>
```

**Relationships:**
- Configures `Sgapi_Gooddata` instances
- Creates `Sessions_Gooddata` records

---

### LDAP_Feed_XML

XML payload structure for LDAP directory feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type value (ldap) |
| feedid | string | Yes | Feed identifier |
| server | string | Yes | LDAP server URL (ldap:// or ldaps://) |
| service | string | No | LDAP service type (e.g., MSAD for Active Directory) |
| parentdn | string | Yes | Parent distinguished name for user base |
| userrdn | string | Yes | User relative distinguished name |
| password | string | Yes | LDAP bind password |
| tlscertfile | string | No | TLS client certificate filename |
| tlskeyfile | string | No | TLS client key filename |

**Validation Rules:**
- `type` must be 'ldap'
- `server` must start with 'ldap://' or 'ldaps://'
- `parentdn` and `userrdn` must form valid DN when combined

**Example:**
```json
{
  "type": "ldap",
  "feedid": "75",
  "server": "ldaps://ldap.company.com:636",
  "service": "MSAD",
  "parentdn": "OU=Users,DC=company,DC=com",
  "userrdn": "CN=svcaccount",
  "password": "ldapPass789",
  "tlscertfile": "client.crt",
  "tlskeyfile": "client.key"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>ldap</type>
  <feedid>75</feedid>
  <server>ldaps://ldap.company.com:636</server>
  <service>MSAD</service>
  <parentdn>OU=Users,DC=company,DC=com</parentdn>
  <userrdn>CN=svcaccount</userrdn>
  <password>ldapPass789</password>
  <tlscertfile>client.crt</tlscertfile>
  <tlskeyfile>client.key</tlskeyfile>
</feed>
```

**Relationships:**
- Configures `Sgapi_Ldap` instances
- Creates `Sessions_Ldap` records

---

### Msdynamics_Feed_Payload

XML payload structure for Microsoft Dynamics CRM feed authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (msdynamics) |
| feedid | integer | Yes | Feed identifier |
| nicename | string | No | Display name for the feed |
| authtype | string | Yes | Authentication type (ad, spla, passport) |
| server | string | Yes | CRM server URL |
| organization | string | Yes | CRM organization name |
| username | string | Yes | Username for authentication |
| password | string | Yes | Password for authentication |

**Validation Rules:**
- `type` must be 'msdynamics'
- `authtype` must be one of: 'ad', 'spla', 'passport'
- `organization` must match CRM organization name

**Example:**
```json
{
  "type": "msdynamics",
  "feedid": 80,
  "nicename": "Dynamics CRM",
  "authtype": "spla",
  "server": "https://crm.company.com",
  "organization": "CompanyOrg",
  "username": "crmuser@company.com",
  "password": "crmPass123"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>msdynamics</type>
  <feedid>80</feedid>
  <nicename>Dynamics CRM</nicename>
  <authtype>spla</authtype>
  <server>https://crm.company.com</server>
  <organization>CompanyOrg</organization>
  <username>crmuser@company.com</username>
  <password>crmPass123</password>
</feed>
```

**Relationships:**
- Configures `Msdynamics` and `Auth_Msdynamics` instances
- Creates `Sessions_Msdynamics` records

---

### OracleFusionFeedPayload

XML payload structure for Oracle Fusion CRM authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Feed type (oraclefusion) |
| feedid | integer | Yes | Feed identifier |
| server | string | Yes | Oracle Fusion server URL |
| nicename | string | No | Human-readable feed name |
| username | string | Yes | Oracle Fusion username |
| password | string | Yes | Oracle Fusion password |

**Validation Rules:**
- `type` must be 'oraclefusion'
- `server` must be valid Oracle Fusion Cloud URL

**Example:**
```json
{
  "type": "oraclefusion",
  "feedid": 85,
  "server": "https://company.crm.us2.oraclecloud.com",
  "nicename": "Oracle Sales Cloud",
  "username": "sales.user@company.com",
  "password": "oraclePass456"
}
```

**XML Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>oraclefusion</type>
  <feedid>85</feedid>
  <server>https://company.crm.us2.oraclecloud.com</server>
  <nicename>Oracle Sales Cloud</nicename>
  <username>sales.user@company.com</username>
  <password>oraclePass456</password>
</feed>
```

**Relationships:**
- Configures `Sgapi_Oraclefusion` and `Auth_Oraclefusion` instances
- Creates `Sessions_Oraclefusion` records

---

## Metadata Cache Model

### recordsbuffer

Database table for caching metadata and schemas from external services.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UsrID | string | Yes | User identifier (part of composite key) |
| ProjectID | string | Yes | Project identifier (part of composite key) |
| DataSet | string | Yes | Dataset/table name (part of composite key) |
| Type | integer | Yes | Record type indicator |
| Contents | text | Yes | Cached content (e.g., XML schema, metadata) |

**Validation Rules:**
- Composite key: `UsrID` + `ProjectID` + `DataSet` + `Type`
- `Contents` may contain XML or JSON metadata

**Example:**
```json
{
  "UsrID": "user123",
  "ProjectID": "project456",
  "DataSet": "Accounts",
  "Type": 1,
  "Contents": "<?xml version=\"1.0\"?><schema><field name=\"Id\" type=\"string\"/><field name=\"Name\" type=\"string\"/></schema>"
}
```

**Relationships:**
- Used by `Sgapi_Gooddata` for metadata caching
- Indexed by user/project for quick retrieval

---

## Common Use Cases

### 1. Retrieving Unread Messages

```php
// Load context from tokentofeed
$context = unserialize($tokentofeed['Context']);

// Get unread message IDs from context
$unreadIds = $context->UnreadMessages;

// Query inbox for unread messages
$messages = $db->query("SELECT * FROM inbox WHERE MessageID IN (...) AND Read = 'n'");
```

### 2. Configuring a New IMAP Feed

```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <type>imap</type>
  <feedid>100</feedid>
  <nicename>Support Mailbox</nicename>
  <host>imap.company.com</host>
  <port>993</port>
  <ssl>yes</ssl>
  <username>support@company.com</username>
  <password>mailboxPassword</password>
</feed>
```

### 3. Processing Feed Refresh Results

```php
// Create MessageObject for each new message
$msgObj = new MessageObject();
$msgObj->msgid = $message['id'];
$msgObj->feedid = $feedId;
$msgObj->messagedate = $message['date'];
$msgObj->sender = $message['from'];
$msgObj->subject = $message['subject'];
$msgObj->read = 'n';

// Insert into inbox table
$db->insert('inbox', $msgObj);
```

---

## Related Documentation

- [Session Models](session-models.md) - Authentication session management
- [API Response Models](api-response-models.md) - Standard API response formats
- [Platform Models](platform-models.md) - Core platform data structures