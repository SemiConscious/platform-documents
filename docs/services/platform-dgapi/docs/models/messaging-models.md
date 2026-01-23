# Messaging Data Models

This document covers the data models used for messaging functionality in the platform-dgapi service, including SMS, Email, and Voicemail notifications along with their XML DOM representations.

## Overview

The messaging subsystem handles asynchronous delivery of notifications through multiple channels:
- **Email**: Direct email notifications for CDR events
- **SMS**: Text message notifications
- **Voicemail**: Hybrid notifications that can use both email and SMS channels

All messaging models extend the base `Task_Model` and are processed through the CDR task queue system.

> **Related Documentation**:
> - [Task Models](task-models.md) - Base task model and task management
> - [CDR Models](cdr-models.md) - CDR data structures that trigger messaging

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        Task_Model (Base)                        │
│                    (See task-models.md)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ extends
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
        │ Email_Model │ │  Sms_Model  │ │ Voicemail_Model │
        └─────────────┘ └─────────────┘ └─────────────────┘
                │               │               │
                │               │               │
                └───────────────┼───────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   normalized_cdrs   │
                    │  (via LegUUID ref)  │
                    │ (See cdr-models.md) │
                    └─────────────────────┘
```

---

## Email_Model

### Purpose

The `Email_Model` handles email notification tasks triggered by CDR events. It extends the base `Task_Model` to include organization, user, and CDR leg context necessary for email delivery.

### When to Use

- Sending CDR event notifications to users via email
- Delivering call completion summaries
- Notifying administrators of system events

### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `rmOrgID` | int | Yes | Organization ID that owns this email task |
| `rmUserID` | string | Yes | User ID of the notification recipient |
| `LegUUID` | string | Yes | Reference to the CDR leg that triggered this notification |

> **Note**: This model inherits all fields from `Task_Model` including `id`, `task_type`, `create_time`, `next_attempt`, `done`, `retry`, and `priority`. See [Task Models](task-models.md) for inherited field details.

### Validation Rules

| Rule | Description |
|------|-------------|
| `rmOrgID` | Must be a positive integer; must reference a valid organization |
| `rmUserID` | Must be a non-empty string; typically numeric or alphanumeric identifier |
| `LegUUID` | Must be a valid UUID format (36 characters with hyphens) |
| `task_type` | Must be set to `"SendEmail"` for email tasks |

### XML DOM Representation

The Email_Model is represented in the normalized CDR XML structure:

```xml
<task>
  <type>SendEmail</type>
  <rmOrgID>12345</rmOrgID>
  <rmUserID>user_789</rmUserID>
  <LegUUID>550e8400-e29b-41d4-a716-446655440000</LegUUID>
</task>
```

### Example JSON

```json
{
  "id": 1001,
  "id_normalized_cdrs": 5000,
  "task_type": "SendEmail",
  "create_time": "2024-01-15T10:30:00Z",
  "next_attempt": "2024-01-15T10:30:00Z",
  "done": "n",
  "node_index": 0,
  "retry": 0,
  "priority": "medium",
  "rmOrgID": 12345,
  "rmUserID": "user_789",
  "LegUUID": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common Use Cases

1. **Call Completion Notification**: Send email when a recorded call completes
2. **Voicemail Transcript Delivery**: Email voicemail transcripts to users
3. **CDR Summary Reports**: Deliver periodic call detail summaries

---

## Sms_Model

### Purpose

The `Sms_Model` handles SMS notification tasks for mobile delivery of CDR event alerts. It provides a lightweight notification mechanism for time-sensitive events.

### When to Use

- Immediate notification of missed calls
- Urgent voicemail alerts
- Real-time call status updates to mobile devices

### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `rmOrgID` | int | Yes | Organization ID that owns this SMS task |
| `rmUserID` | string | Yes | User ID of the SMS recipient |
| `LegUUID` | string | Yes | Reference to the CDR leg that triggered this notification |

> **Note**: This model inherits all fields from `Task_Model`. See [Task Models](task-models.md) for inherited field details.

### Validation Rules

| Rule | Description |
|------|-------------|
| `rmOrgID` | Must be a positive integer; must reference a valid organization |
| `rmUserID` | Must be a non-empty string; user must have a valid mobile number configured |
| `LegUUID` | Must be a valid UUID format (36 characters with hyphens) |
| `task_type` | Must be set to `"SendSMS"` for SMS tasks |

### XML DOM Representation

```xml
<task>
  <type>SendSMS</type>
  <rmOrgID>12345</rmOrgID>
  <rmUserID>user_456</rmUserID>
  <LegUUID>660e8400-e29b-41d4-a716-446655440001</LegUUID>
</task>
```

### Example JSON

```json
{
  "id": 1002,
  "id_normalized_cdrs": 5001,
  "task_type": "SendSMS",
  "create_time": "2024-01-15T11:45:00Z",
  "next_attempt": "2024-01-15T11:45:00Z",
  "done": "n",
  "node_index": 0,
  "retry": 0,
  "priority": "high",
  "rmOrgID": 12345,
  "rmUserID": "user_456",
  "LegUUID": "660e8400-e29b-41d4-a716-446655440001"
}
```

### Common Use Cases

1. **Missed Call Alert**: Immediate SMS when a call goes unanswered
2. **Voicemail Notification**: Alert user of new voicemail via SMS
3. **Urgent Contact Notification**: Priority alerts for VIP callers

---

## Voicemail_Model

### Purpose

The `Voicemail_Model` handles voicemail notification tasks that can deliver alerts through both email and SMS channels simultaneously. It provides flexible multi-channel notification capabilities with granular control over each delivery method.

### When to Use

- Notifying users of new voicemail messages
- Multi-channel delivery where both email and SMS are required
- Configurable notification preferences per user

### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `rmOrgID` | int | Yes | Organization ID that owns this voicemail notification |
| `rmUserID` | string | Yes | User ID of the voicemail owner |
| `LegUUID` | string | Yes | Reference to the CDR leg containing the voicemail |
| `Notification/Email` | xml_node | No | Email notification configuration node |
| `Notification/SMS` | xml_node | No | SMS notification configuration node |

> **Note**: This model inherits all fields from `Task_Model`. See [Task Models](task-models.md) for inherited field details.

### Notification Sub-Elements

#### Email Notification Node

| Attribute/Element | Type | Required | Description |
|-------------------|------|----------|-------------|
| `enabled` | boolean | Yes | Whether email notification is active |
| `recipient` | string | Conditional | Email address (required if enabled) |
| `include_attachment` | boolean | No | Include voicemail audio as attachment |
| `include_transcript` | boolean | No | Include voicemail transcript in body |

#### SMS Notification Node

| Attribute/Element | Type | Required | Description |
|-------------------|------|----------|-------------|
| `enabled` | boolean | Yes | Whether SMS notification is active |
| `phone_number` | string | Conditional | Mobile number (required if enabled) |
| `include_caller_id` | boolean | No | Include caller information in SMS |

### Validation Rules

| Rule | Description |
|------|-------------|
| `rmOrgID` | Must be a positive integer; must reference a valid organization |
| `rmUserID` | Must be a non-empty string |
| `LegUUID` | Must be a valid UUID format |
| `Notification/Email` | If `enabled=true`, `recipient` must be a valid email address |
| `Notification/SMS` | If `enabled=true`, `phone_number` must be a valid E.164 format |
| At least one notification | Either Email or SMS notification must be enabled |

### XML DOM Representation

```xml
<task>
  <type>Voicemail</type>
  <rmOrgID>12345</rmOrgID>
  <rmUserID>user_321</rmUserID>
  <LegUUID>770e8400-e29b-41d4-a716-446655440002</LegUUID>
  <Notification>
    <Email enabled="true">
      <recipient>user@example.com</recipient>
      <include_attachment>true</include_attachment>
      <include_transcript>true</include_transcript>
    </Email>
    <SMS enabled="true">
      <phone_number>+15551234567</phone_number>
      <include_caller_id>true</include_caller_id>
    </SMS>
  </Notification>
</task>
```

### Example JSON

```json
{
  "id": 1003,
  "id_normalized_cdrs": 5002,
  "task_type": "Voicemail",
  "create_time": "2024-01-15T14:20:00Z",
  "next_attempt": "2024-01-15T14:20:00Z",
  "done": "n",
  "node_index": 0,
  "retry": 0,
  "priority": "high",
  "rmOrgID": 12345,
  "rmUserID": "user_321",
  "LegUUID": "770e8400-e29b-41d4-a716-446655440002",
  "Notification": {
    "Email": {
      "enabled": true,
      "recipient": "user@example.com",
      "include_attachment": true,
      "include_transcript": true
    },
    "SMS": {
      "enabled": true,
      "phone_number": "+15551234567",
      "include_caller_id": true
    }
  }
}
```

### Common Use Cases

1. **Full Notification**: Both email with attachment and SMS alert
2. **Email-Only Notification**: Detailed voicemail delivery with transcript
3. **SMS-Only Alert**: Quick notification for mobile-first users
4. **Transcript Delivery**: Email with speech-to-text transcription

---

## Integration with CDR Normalized XML

Messaging models are embedded within the `cdr-normalized` XML structure as task nodes. The relationship between messaging tasks and the parent CDR is established through the `LegUUID` reference.

### Example: Complete CDR with Messaging Tasks

```xml
<?xml version="1.0" encoding="UTF-8"?>
<cdr>
  <data>
    <uuid>880e8400-e29b-41d4-a716-446655440003</uuid>
    <TimeZoneOffset>-28800</TimeZoneOffset>
    <StartEpoch>1705322400</StartEpoch>
    <TableSuffix>20240115</TableSuffix>
    <LegUUID>770e8400-e29b-41d4-a716-446655440002</LegUUID>
    <rmOrgID>12345</rmOrgID>
    <rmUserID>user_321</rmUserID>
    <variables>
      <caller_id_number>+15559876543</caller_id_number>
      <caller_id_name>John Doe</caller_id_name>
      <duration>45</duration>
    </variables>
  </data>
  <tasks>
    <!-- Email notification task -->
    <task>
      <type>SendEmail</type>
      <rmOrgID>12345</rmOrgID>
      <rmUserID>user_321</rmUserID>
      <LegUUID>770e8400-e29b-41d4-a716-446655440002</LegUUID>
    </task>
    <!-- SMS notification task -->
    <task>
      <type>SendSMS</type>
      <rmOrgID>12345</rmOrgID>
      <rmUserID>user_321</rmUserID>
      <LegUUID>770e8400-e29b-41d4-a716-446655440002</LegUUID>
    </task>
    <!-- Combined voicemail notification -->
    <task>
      <type>Voicemail</type>
      <rmOrgID>12345</rmOrgID>
      <rmUserID>user_321</rmUserID>
      <LegUUID>770e8400-e29b-41d4-a716-446655440002</LegUUID>
      <Notification>
        <Email enabled="true">
          <recipient>user@example.com</recipient>
          <include_attachment>true</include_attachment>
        </Email>
        <SMS enabled="false"/>
      </Notification>
    </task>
  </tasks>
</cdr>
```

---

## Processing Flow

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   CDR Event  │────▶│ Task Extraction │────▶│ Message Dispatch │
└──────────────┘     └─────────────────┘     └──────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌─────────────────┐     ┌──────────────────┐
                     │  Email_Model    │────▶│   SMTP Server    │
                     │  Sms_Model      │────▶│   SMS Gateway    │
                     │  Voicemail_Model│────▶│   Both Channels  │
                     └─────────────────┘     └──────────────────┘
```

---

## Error Handling

When messaging tasks fail, errors are recorded in the `tasks_error` table (documented in [Task Models](task-models.md)). Common messaging-specific errors include:

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `EMAIL_DELIVERY_FAILED` | SMTP server rejected the message | Verify recipient address; check SMTP configuration |
| `SMS_DELIVERY_FAILED` | SMS gateway returned error | Verify phone number format; check carrier restrictions |
| `INVALID_RECIPIENT` | No valid contact information for user | Update user profile with valid email/phone |
| `TEMPLATE_ERROR` | Message template rendering failed | Check template syntax and variable availability |

---

## See Also

- [Task Models](task-models.md) - Base task model and error handling
- [CDR Models](cdr-models.md) - CDR data structures
- [API Overview](../README.md) - Service architecture overview