# Messaging and Contact Models

This document covers data models related to messaging, contacts, and identity management in the Natterbox Routing Policies service. These models handle outbound messaging operations, contact information, and template-based communications.

## Overview

The messaging models support various communication channels and provide structured ways to send messages, manage contacts, and work with message templates. These models are essential for any routing policy that needs to send notifications or communicate with external parties.

## Entity Relationships

```
┌─────────────────────────┐
│    SendMessageSchema    │
│    SendTemplateSchema   │
└───────────┬─────────────┘
            │ contains
            ▼
┌─────────────────────────┐
│        Contact          │
└───────────┬─────────────┘
            │ contains
            ▼
┌─────────────────────────┐
│        Identity         │
└─────────────────────────┘

┌─────────────────────────┐
│   SendTemplateSchema    │
└───────────┬─────────────┘
            │ contains array of
            ▼
┌─────────────────────────┐
│      Placeholder        │
└─────────────────────────┘
```

---

## SendMessageSchema

Schema for sending a free text or template-based message to contacts.

### Purpose

This model defines the structure for sending outbound messages. It supports multiple target types and communication channels, allowing routing policies to send notifications, alerts, or follow-up messages.

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target` | enum | Yes | Message target type (e.g., specific recipient, group) |
| `targetType` | enum | Yes | Target content type classification |
| `textMessage` | string | No | The text message content for free-text messages |
| `fromNumber` | string | Yes | Sender phone number for the outbound message |
| `contact` | Contact | Yes | Contact information object containing recipient details |
| `location` | string | No | Location information associated with the message |
| `templateId` | string | No | Template identifier when sending template-based messages |

### Validation Rules

- `fromNumber` must be a valid phone number format
- Either `textMessage` or `templateId` should be provided
- `contact` object must contain valid identity information

### Example JSON

```json
{
  "target": "INDIVIDUAL",
  "targetType": "PHONE",
  "textMessage": "Your appointment is confirmed for tomorrow at 2:00 PM. Reply CONFIRM to acknowledge.",
  "fromNumber": "+14155551234",
  "contact": {
    "identity": {
      "address": "+14155559876",
      "channelType": "SMS",
      "countryCodePrefix": "+1",
      "externalId": "contact-12345",
      "displayName": "John Smith"
    }
  },
  "location": "San Francisco Office"
}
```

### Common Use Cases

- Sending appointment reminders
- Delivering notification alerts
- Follow-up messages after call completion
- Status updates to customers

---

## SendTemplateSchema

Schema for sending a template message with dynamic placeholder values.

### Purpose

This model extends messaging capabilities by supporting pre-defined message templates with customizable placeholders. It enables consistent, personalized messaging while maintaining compliance with approved message formats.

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target` | enum | Yes | Message target type |
| `targetType` | enum | Yes | Target content type classification |
| `textMessage` | string | No | Optional text message content |
| `fromNumber` | string | Yes | Sender phone number |
| `contact` | Contact | Yes | Contact information object |
| `location` | string | No | Location information |
| `templateId` | string | Yes | Template identifier for the message template to use |
| `placeholders` | Placeholder[] | Yes | Array of placeholder values to substitute in the template |

### Validation Rules

- `templateId` must reference an existing, valid template
- `placeholders` array must contain all required placeholders for the selected template
- Placeholder macro names must match those defined in the template

### Relationships

- Contains a `Contact` object for recipient information
- Contains an array of `Placeholder` objects for dynamic content

### Example JSON

```json
{
  "target": "INDIVIDUAL",
  "targetType": "PHONE",
  "fromNumber": "+14155551234",
  "contact": {
    "identity": {
      "address": "+14155559876",
      "channelType": "SMS",
      "countryCodePrefix": "+1",
      "externalId": "contact-67890",
      "displayName": "Jane Doe"
    }
  },
  "location": "New York Office",
  "templateId": "appointment-reminder-v2",
  "placeholders": [
    {
      "macro": "CUSTOMER_NAME",
      "value": "Jane"
    },
    {
      "macro": "APPOINTMENT_DATE",
      "value": "December 15, 2024"
    },
    {
      "macro": "APPOINTMENT_TIME",
      "value": "3:30 PM"
    },
    {
      "macro": "LOCATION",
      "value": "123 Main Street, Suite 400"
    }
  ]
}
```

### Common Use Cases

- Sending standardized appointment confirmations
- Compliance-approved marketing messages
- Multi-language message support with localized templates
- Transactional notifications with dynamic data

---

## Contact

Wrapper object containing contact identity information.

### Purpose

The Contact model serves as a container for identity information, providing a structured way to reference message recipients. It acts as an intermediary layer that can be extended for additional contact metadata.

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `identity` | Identity | Yes | Contact identity information containing address and channel details |

### Relationships

- Contains an `Identity` object with detailed contact information
- Used by `SendMessageSchema` and `SendTemplateSchema`

### Example JSON

```json
{
  "identity": {
    "address": "+442071234567",
    "channelType": "VOICE",
    "countryCodePrefix": "+44",
    "externalId": "sf-contact-abc123",
    "displayName": "David Wilson"
  }
}
```

### Common Use Cases

- Encapsulating recipient information for messaging operations
- Passing contact details between routing policy nodes
- Referencing CRM contacts in communication workflows

---

## Identity

Detailed contact identity information including address and communication channel.

### Purpose

The Identity model contains the core identification details for a contact, including their communication address, preferred channel, and external system references. This enables proper routing and tracking of communications.

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | string | Yes | Contact address (phone number, email, or channel-specific identifier) |
| `channelType` | enum | Yes | Communication channel type (SMS, VOICE, WHATSAPP, etc.) |
| `countryCodePrefix` | string | No | Country code prefix for phone numbers (e.g., "+1", "+44") |
| `externalId` | string | No | External identifier linking to CRM or other systems |
| `displayName` | string | No | Human-readable display name for the contact |

### Validation Rules

- `address` format depends on `channelType`:
  - For SMS/VOICE: Must be a valid phone number
  - For email channels: Must be a valid email format
- `channelType` must be a valid enum value from supported channels
- `countryCodePrefix` should start with "+" followed by country code digits

### Example JSON

```json
{
  "address": "+14155551234",
  "channelType": "SMS",
  "countryCodePrefix": "+1",
  "externalId": "salesforce-003Dn00000ABC123",
  "displayName": "Sarah Johnson"
}
```

### Channel Types

| Channel Type | Description | Address Format |
|--------------|-------------|----------------|
| `SMS` | Short Message Service | Phone number |
| `VOICE` | Voice call | Phone number |
| `WHATSAPP` | WhatsApp messaging | Phone number |
| `EMAIL` | Email communication | Email address |

### Common Use Cases

- Identifying message recipients across multiple channels
- Linking communications to CRM records via `externalId`
- Supporting multi-channel contact strategies
- Personalizing communications with `displayName`

---

## Placeholder

Template placeholder containing a macro name and substitution value.

### Purpose

The Placeholder model defines key-value pairs used to substitute dynamic content into message templates. Each placeholder maps a macro identifier to the specific value that should replace it in the template.

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `macro` | string | Yes | Macro name that matches a placeholder in the template |
| `value` | string | Yes | Value to substitute for the macro in the message |

### Validation Rules

- `macro` must match a defined placeholder in the associated template
- `macro` names are typically uppercase with underscores (e.g., `CUSTOMER_NAME`)
- `value` may be empty string but the field is required

### Example JSON

```json
{
  "macro": "ORDER_NUMBER",
  "value": "ORD-2024-78432"
}
```

### Example: Multiple Placeholders

```json
[
  {
    "macro": "CUSTOMER_FIRST_NAME",
    "value": "Michael"
  },
  {
    "macro": "ACCOUNT_BALANCE",
    "value": "$1,234.56"
  },
  {
    "macro": "DUE_DATE",
    "value": "January 15, 2025"
  },
  {
    "macro": "SUPPORT_PHONE",
    "value": "1-800-555-0199"
  }
]
```

### Common Use Cases

- Personalizing customer names in messages
- Inserting dynamic dates and times
- Including order/reference numbers
- Adding calculated values or amounts
- Inserting location-specific information

---

## Integration Patterns

### Sending a Simple Text Message

```json
{
  "target": "INDIVIDUAL",
  "targetType": "PHONE",
  "textMessage": "Thank you for calling. Your reference number is REF-12345.",
  "fromNumber": "+14155550100",
  "contact": {
    "identity": {
      "address": "+14155550199",
      "channelType": "SMS",
      "displayName": "Customer"
    }
  }
}
```

### Sending a Template Message with CRM Integration

```json
{
  "target": "INDIVIDUAL",
  "targetType": "PHONE",
  "fromNumber": "+14155550100",
  "contact": {
    "identity": {
      "address": "+14155550199",
      "channelType": "SMS",
      "countryCodePrefix": "+1",
      "externalId": "003Dn00000XYZ789",
      "displayName": "Premium Customer"
    }
  },
  "templateId": "premium-follow-up",
  "placeholders": [
    {
      "macro": "AGENT_NAME",
      "value": "Sarah"
    },
    {
      "macro": "CASE_NUMBER",
      "value": "CS-2024-45678"
    }
  ]
}
```

---

## Related Documentation

- [AI Routing Models](./ai-routing.md) - For AI-powered routing decisions that may trigger messaging
- [Policy Records](./policy-records.md) - For understanding how messaging integrates with routing policies
- [Routing Variables](./routing-variables.md) - For using variables in message content