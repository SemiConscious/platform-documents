# Contact & Identity Data Models

This document covers the data models used for managing contacts, identities, and external system integrations in the omnichannel-omniservice. These models form the foundation for tracking and identifying users across multiple communication channels.

## Overview

The contact and identity system provides a hierarchical structure where:
- A **Contact** represents a unique person in the system
- A **ContactIdentity** links a contact to a specific channel address (phone number, etc.)
- An **Identity** provides lightweight identity information for message processing
- **ExternalId** records link contacts/identities to external systems (e.g., Salesforce)

```
┌─────────────────────────────────────────────────────────────────┐
│                          Contact                                 │
│  (represents a unique person across all channels)               │
├─────────────────────────────────────────────────────────────────┤
│  contactId: "cnt_abc123"                                        │
│  displayName: "John Smith"                                      │
│  referencedIdentityId: "idt_xyz789"                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │  ContactIdentity    │  │  ContactIdentity    │              │
│  │  (SMS Channel)      │  │  (WhatsApp Channel) │              │
│  │  +14155551234       │  │  +14155551234       │              │
│  └─────────────────────┘  └─────────────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │  ExternalId         │  │  ExternalId         │              │
│  │  Salesforce Lead    │  │  HubSpot Contact    │              │
│  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Contact

The primary entity representing a person communicating through the system. A contact aggregates multiple identities across different channels.

### Purpose and Usage

- Represents a unique individual across all communication channels
- Aggregates multiple channel-specific identities
- Links to external CRM/system records via ExternalIds
- Serves as the primary entity for contact management and history

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contactId` | string | Yes | Unique identifier for the contact (UUID format) |
| `displayName` | string | Yes | Human-readable display name of the contact |
| `identities` | ContactIdentity[] | Yes | List of contact identities across different channels |
| `createdDate` | string (ISO 8601) | Yes | Timestamp when the contact was created |
| `modifiedDate` | string (ISO 8601) | Yes | Timestamp of last modification |
| `externalIds` | ExternalId[] | No | List of external system identifiers (e.g., Salesforce IDs) |
| `referencedIdentityId` | string | No | Primary identity reference for default channel selection |

### Validation Rules

- `contactId` must be a valid UUID
- `displayName` must be non-empty and no longer than 255 characters
- `identities` array must contain at least one identity
- `createdDate` and `modifiedDate` must be valid ISO 8601 timestamps
- `referencedIdentityId` must reference an identity within the `identities` array

### Example JSON

```json
{
  "contactId": "cnt_8f14e45f-ceea-467f-a123-456789abcdef",
  "displayName": "John Smith",
  "identities": [
    {
      "identityId": "idt_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "displayName": "John Smith (Mobile)",
      "channelType": "SMS",
      "address": "+14155551234",
      "contactId": "cnt_8f14e45f-ceea-467f-a123-456789abcdef",
      "countryCodePrefix": "1",
      "countryCodeIso": "US",
      "createdDate": "2024-01-15T10:30:00.000Z",
      "modifiedDate": "2024-01-15T10:30:00.000Z",
      "externalIds": []
    },
    {
      "identityId": "idt_b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "displayName": "John Smith (WhatsApp)",
      "channelType": "WhatsApp",
      "address": "+14155551234",
      "contactId": "cnt_8f14e45f-ceea-467f-a123-456789abcdef",
      "countryCodePrefix": "1",
      "countryCodeIso": "US",
      "createdDate": "2024-01-16T14:22:00.000Z",
      "modifiedDate": "2024-01-16T14:22:00.000Z",
      "externalIds": []
    }
  ],
  "createdDate": "2024-01-15T10:30:00.000Z",
  "modifiedDate": "2024-01-16T14:22:00.000Z",
  "externalIds": [
    {
      "externalId": "003xx000004TmiKAAS",
      "confirmed": true,
      "displayName": "John Smith - Salesforce",
      "primary": true
    }
  ],
  "referencedIdentityId": "idt_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| ContactIdentity | One-to-Many | A contact has multiple identities across channels |
| ExternalId | One-to-Many | A contact can be linked to multiple external systems |
| Interaction | One-to-Many | A contact can have multiple interactions |
| ServiceMessage | Many-to-One | Messages reference a contact |

---

## ContactIdentity

Links a contact to a specific channel address, enabling communication across different channels.

### Purpose and Usage

- Associates a specific phone number or address with a contact
- Enables channel-specific routing and communication
- Stores channel-specific metadata (country code, carrier info)
- Supports identity lookup during message processing

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identityId` | string | Yes | Unique identifier for this identity |
| `displayName` | string | Yes | Display name for this specific identity |
| `channelType` | ChannelType | Yes | Channel type (SMS, MMS, WhatsApp, PubNub, LiveChat) |
| `address` | string | Yes | Address/phone number for this identity |
| `contactId` | string | Yes | Parent contact identifier |
| `countryCodePrefix` | string | No | Country code prefix (e.g., "1" for US) |
| `countryCodeIso` | string | No | ISO country code (e.g., "US", "GB") |
| `createdDate` | string (ISO 8601) | Yes | Creation timestamp |
| `modifiedDate` | string (ISO 8601) | Yes | Last modification timestamp |
| `externalIds` | ExternalId[] | No | Channel-specific external identifiers |

### Validation Rules

- `identityId` must be a valid UUID
- `channelType` must be a valid enum value: `SMS`, `MMS`, `WhatsApp`, `PubNub`, `LiveChat`
- `address` format depends on channel type:
  - SMS/MMS/WhatsApp: E.164 phone number format
  - LiveChat/PubNub: Platform-specific identifier
- `countryCodePrefix` must be numeric when provided
- `countryCodeIso` must be valid ISO 3166-1 alpha-2 code when provided

### Example JSON

```json
{
  "identityId": "idt_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "displayName": "John Smith (Mobile)",
  "channelType": "SMS",
  "address": "+14155551234",
  "contactId": "cnt_8f14e45f-ceea-467f-a123-456789abcdef",
  "countryCodePrefix": "1",
  "countryCodeIso": "US",
  "createdDate": "2024-01-15T10:30:00.000Z",
  "modifiedDate": "2024-01-15T10:30:00.000Z",
  "externalIds": [
    {
      "externalId": "mobile_003xx000004TmiKAAS",
      "confirmed": true,
      "displayName": "Salesforce Mobile Number",
      "primary": true
    }
  ]
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| Contact | Many-to-One | Each identity belongs to one contact |
| ExternalId | One-to-Many | Identity can have multiple external IDs |
| Interaction | One-to-Many | Identity can participate in multiple interactions |
| PublishIdentity | Transform | Used to create PublishIdentity for outbound messages |

---

## Identity

Lightweight identity information used during message processing. This is a simplified view used in ServiceMessage context.

### Purpose and Usage

- Provides minimal identity info for message routing
- Used within ServiceMessage for sender/recipient identification
- Supports quick identity resolution during message processing
- Serves as a simplified DTO for identity information

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channelType` | ChannelType | Yes | Channel type for this identity |
| `address` | string | Yes | Address/phone number |
| `displayName` | string | No | Display name for the identity |

### Validation Rules

- `channelType` must be a valid ChannelType enum value
- `address` must be non-empty and follow channel-specific format rules
- `displayName` is optional but recommended for user-facing contexts

### Example JSON

```json
{
  "channelType": "WhatsApp",
  "address": "+14155551234",
  "displayName": "John Smith"
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| ServiceMessage | Component | Embedded within ServiceMessage |
| ContactIdentity | Simplified View | Represents a simplified version of ContactIdentity |

---

## ExternalId

Links contacts or identities to external system records (CRM, ticketing systems, etc.).

### Purpose and Usage

- Enables integration with external systems like Salesforce, HubSpot
- Supports bi-directional sync of contact information
- Allows confirmation workflow for verified external links
- Designates primary external reference for default lookups

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `externalId` | string | Yes | External system identifier (e.g., Salesforce record ID) |
| `confirmed` | boolean | Yes | Whether the external ID link has been confirmed/verified |
| `displayName` | string | No | Display name from the external system |
| `primary` | boolean | No | Whether this is the primary external ID for the contact |

### Validation Rules

- `externalId` must be non-empty
- `externalId` format may vary by external system (Salesforce IDs are 15 or 18 characters)
- Only one ExternalId per contact should have `primary: true`
- `confirmed` defaults to `false` until verification is complete

### Example JSON

```json
{
  "externalId": "003xx000004TmiKAAS",
  "confirmed": true,
  "displayName": "John Smith - Salesforce Lead",
  "primary": true
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| Contact | Many-to-One | External IDs belong to a contact |
| ContactIdentity | Many-to-One | External IDs can also be channel-specific |
| ExternalIdLookupResponse | Related | Used in external ID lookup operations |

---

## PublishIdentity

Extended identity information used when publishing outbound messages.

### Purpose and Usage

- Provides complete identity context for outbound message publishing
- Used in PublishChannel for routing decisions
- Contains full metadata needed for carrier-specific formatting
- Supports external ID propagation for CRM integration

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | string | Yes | Target phone number or address |
| `channelType` | ChannelType | Yes | Channel type for publishing |
| `contactId` | string | Yes | Associated contact identifier |
| `displayName` | string | Yes | Display name for the recipient |
| `identityId` | string | Yes | Identity identifier |
| `countryCodeIso` | string | No | ISO country code |
| `countryCodePrefix` | string | No | Country code prefix |
| `createdDate` | string (ISO 8601) | No | Creation timestamp |
| `modifiedDate` | string (ISO 8601) | No | Modification timestamp |
| `externalIds` | ExternalId[] | No | Associated external identifiers |

### Validation Rules

- `address` must follow channel-specific format (E.164 for telephony channels)
- `channelType` must match the target publish channel type
- `contactId` and `identityId` must be valid UUIDs
- Country code fields must be consistent (if one is provided, both should be)

### Example JSON

```json
{
  "address": "+14155551234",
  "channelType": "WhatsApp",
  "contactId": "cnt_8f14e45f-ceea-467f-a123-456789abcdef",
  "displayName": "John Smith",
  "identityId": "idt_b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "countryCodeIso": "US",
  "countryCodePrefix": "1",
  "createdDate": "2024-01-16T14:22:00.000Z",
  "modifiedDate": "2024-01-16T14:22:00.000Z",
  "externalIds": [
    {
      "externalId": "003xx000004TmiKAAS",
      "confirmed": true,
      "displayName": "Salesforce Contact",
      "primary": true
    }
  ]
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| PublishChannel | Component | Embedded within PublishChannel |
| ContactIdentity | Derived From | Created from ContactIdentity with additional context |
| Contact | Reference | References the parent contact |

---

## ExternalIdLookupResponse

Response model for external identity lookup operations.

### Purpose and Usage

- Returns results from external system identity lookups
- Used during inbound message processing to resolve contacts
- Supports CRM integration workflows
- Provides display information from external systems

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recordId` | string | Yes | Combined namespace:id record identifier |
| `displayName` | string | No | Display name from the external system |

### Validation Rules

- `recordId` format is `namespace:identifier` (e.g., `salesforce:003xx000004TmiKAAS`)
- Namespace must be a known integration type
- `displayName` should be human-readable

### Example JSON

```json
{
  "recordId": "salesforce:003xx000004TmiKAAS",
  "displayName": "John Smith - Acme Corp"
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| ServiceMessage | Component | Stored in `externalIdLookupResponse` array |
| ExternalId | Creates | Used to create/update ExternalId records |
| Contact | Resolves | Used to resolve or create contacts |

---

## Tenant

Organization and user context for multi-tenant operations.

### Purpose and Usage

- Provides organization context for all operations
- Enables multi-tenant data isolation
- Associates actions with specific users
- Used throughout the system for authorization and routing

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | number | Yes | Organization identifier |
| `userId` | number | No | User identifier within the organization |

### Validation Rules

- `orgId` must be a positive integer
- `userId` must be a positive integer when provided
- `orgId` is required for all operations

### Example JSON

```json
{
  "orgId": 12345,
  "userId": 67890
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| ServiceMessage | Component | Embedded in every service message |
| Contact | Scoped By | All contacts are scoped to an organization |
| DigitalChannelGroup | Scoped By | Channel groups belong to organizations |

---

## WhatsAppContact

Contact information from WhatsApp message webhooks.

### Purpose and Usage

- Captures contact info from inbound WhatsApp messages
- Contains WhatsApp-specific profile data
- Used during identity resolution for WhatsApp channel
- Maps WhatsApp user ID to system identity

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile` | WhatsAppProfile | Yes | WhatsApp user profile information |
| `wa_id` | string | Yes | WhatsApp user identifier (phone number) |

### Validation Rules

- `wa_id` must be a valid phone number in WhatsApp format
- `profile` must contain valid WhatsAppProfile object

### Example JSON

```json
{
  "profile": {
    "name": "John Smith"
  },
  "wa_id": "14155551234"
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| WhatsAppProfile | Component | Contains the profile object |
| WhatsAppMessage | Related | Associated with WhatsApp messages |
| ContactIdentity | Maps To | Used to find/create ContactIdentity |

---

## WhatsAppProfile

WhatsApp user profile information from webhooks.

### Purpose and Usage

- Contains user's WhatsApp display name
- Used to populate Contact/Identity display names
- Extracted from WhatsApp webhook payloads

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | User's WhatsApp display name |

### Validation Rules

- `name` must be non-empty
- `name` maximum length follows WhatsApp's limits (typically 25 characters)

### Example JSON

```json
{
  "name": "John Smith"
}
```

### Relationships

| Related Model | Relationship | Description |
|---------------|--------------|-------------|
| WhatsAppContact | Component | Embedded in WhatsAppContact |
| Contact | Populates | Name used for Contact displayName |

---

## Common Patterns

### Identity Resolution Flow

```
Inbound Message
      │
      ▼
┌─────────────────┐
│ Extract Address │
│ & Channel Type  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Not Found    ┌─────────────────┐
│ Lookup Identity │ ───────────────► │ Create Contact  │
│ by Address      │                  │ & Identity      │
└────────┬────────┘                  └────────┬────────┘
         │ Found                              │
         ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│ Return Existing │                 │ Return New      │
│ Contact         │                 │ Contact         │
└─────────────────┘                 └─────────────────┘
```

### External ID Lookup Pattern

```typescript
// Service message includes external ID lookup results
{
  "externalIdLookupResponse": [
    {
      "recordId": "salesforce:003xx000004TmiKAAS",
      "displayName": "John Smith"
    },
    {
      "recordId": "hubspot:12345678",
      "displayName": "John Smith - HubSpot"
    }
  ]
}
```

### Contact with Multiple Channel Identities

```json
{
  "contactId": "cnt_example123",
  "displayName": "Jane Doe",
  "identities": [
    {
      "identityId": "idt_sms_001",
      "channelType": "SMS",
      "address": "+14155559999"
    },
    {
      "identityId": "idt_wa_001", 
      "channelType": "WhatsApp",
      "address": "+14155559999"
    },
    {
      "identityId": "idt_livechat_001",
      "channelType": "LiveChat",
      "address": "user_abc123"
    }
  ],
  "referencedIdentityId": "idt_wa_001"
}
```

---

## Related Documentation

- [Message Models](./message-models.md) - ServiceMessage and payload structures
- [Channel Models](./channel-models.md) - DigitalChannel and channel group configurations
- [WhatsApp Models](./whatsapp-models.md) - WhatsApp-specific webhook and message models
- [Workflow Models](./workflow-models.md) - Workflow step tracking and results