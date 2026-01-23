# Messaging Endpoints (SMS & Email)

This document covers the SMS and Email notification endpoints in the Disposition Gateway API. These endpoints enable sending SMS messages and template-based emails as part of task disposition workflows.

## Overview

The messaging endpoints provide:
- **SMS**: Send SMS messages with delivery tracking
- **Email**: Create and send template-based emails with status tracking

Both endpoint types follow the standard DGAPI task pattern, creating tasks that are processed asynchronously.

---

## SMS Endpoints

### Send SMS Message

Creates a new SMS task to send an SMS message.

```
PUT /sms/{entity}
```

or

```
POST /sms/{entity}
```

#### Description

Creates an SMS task that queues an SMS message for delivery. The task is processed asynchronously, and the message is sent to the specified recipient phone number.

#### Path Parameters

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| `entity`  | string | Yes      | Task entity identifier (e.g., campaign ID, task reference) |

#### Request Body Parameters

| Parameter       | Type   | Required | Description                                           |
|-----------------|--------|----------|-------------------------------------------------------|
| `to`            | string | Yes      | Recipient phone number (E.164 format recommended)     |
| `from`          | string | No       | Sender phone number or sender ID                      |
| `message`       | string | Yes      | SMS message content (max 1600 characters)             |
| `callback_url`  | string | No       | URL for delivery status callbacks                     |
| `metadata`      | object | No       | Additional metadata to attach to the task             |
| `priority`      | integer| No       | Task priority (higher = more urgent)                  |

#### Request Example

```bash
curl -X PUT "https://api.example.com/sms/campaign_12345" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "to": "+15551234567",
    "from": "+15559876543",
    "message": "Your appointment is confirmed for tomorrow at 2:00 PM. Reply CONFIRM to acknowledge.",
    "callback_url": "https://your-server.com/webhooks/sms-status",
    "metadata": {
      "appointment_id": "apt_789",
      "customer_id": "cust_456"
    },
    "priority": 5
  }'
```

#### Response Example

**Success (201 Created)**

```json
{
  "status": "success",
  "data": {
    "task_id": "sms_task_abc123def456",
    "entity": "campaign_12345",
    "type": "sms",
    "state": "queued",
    "to": "+15551234567",
    "from": "+15559876543",
    "message_length": 89,
    "segments": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "metadata": {
      "appointment_id": "apt_789",
      "customer_id": "cust_456"
    }
  }
}
```

#### Error Codes

| HTTP Status | Error Code        | Description                                      |
|-------------|-------------------|--------------------------------------------------|
| 400         | `invalid_phone`   | Invalid phone number format                      |
| 400         | `message_empty`   | Message content is required                      |
| 400         | `message_too_long`| Message exceeds maximum length                   |
| 401         | `unauthorized`    | Invalid or missing authentication                |
| 422         | `invalid_entity`  | Entity identifier is invalid                     |
| 429         | `rate_limited`    | Too many requests, try again later               |
| 500         | `internal_error`  | Server error processing request                  |

---

### Get SMS Task Status

Retrieves the status and details of an SMS task.

```
GET /sms/{entity}
```

#### Description

Returns the current status of an SMS task, including delivery status if the message has been sent.

#### Path Parameters

| Parameter | Type   | Required | Description                           |
|-----------|--------|----------|---------------------------------------|
| `entity`  | string | Yes      | Task entity identifier or task ID     |

#### Query Parameters

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| `include` | string | No       | Additional data to include (e.g., `delivery_log`)|

#### Request Example

```bash
curl -X GET "https://api.example.com/sms/sms_task_abc123def456?include=delivery_log" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

**Success (200 OK)**

```json
{
  "status": "success",
  "data": {
    "task_id": "sms_task_abc123def456",
    "entity": "campaign_12345",
    "type": "sms",
    "state": "completed",
    "to": "+15551234567",
    "from": "+15559876543",
    "message": "Your appointment is confirmed for tomorrow at 2:00 PM. Reply CONFIRM to acknowledge.",
    "segments": 1,
    "delivery_status": "delivered",
    "created_at": "2024-01-15T10:30:00Z",
    "sent_at": "2024-01-15T10:30:05Z",
    "delivered_at": "2024-01-15T10:30:08Z",
    "delivery_log": [
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "status": "queued",
        "message": "Task created and queued"
      },
      {
        "timestamp": "2024-01-15T10:30:05Z",
        "status": "sent",
        "message": "Message sent to carrier"
      },
      {
        "timestamp": "2024-01-15T10:30:08Z",
        "status": "delivered",
        "message": "Delivery confirmed"
      }
    ],
    "metadata": {
      "appointment_id": "apt_789",
      "customer_id": "cust_456"
    }
  }
}
```

#### SMS Delivery States

| State       | Description                                      |
|-------------|--------------------------------------------------|
| `queued`    | Task created, waiting to be processed            |
| `sending`   | Message is being sent                            |
| `sent`      | Message sent to carrier                          |
| `delivered` | Delivery confirmed by carrier                    |
| `failed`    | Delivery failed                                  |
| `undelivered` | Message could not be delivered                 |

#### Error Codes

| HTTP Status | Error Code      | Description                           |
|-------------|-----------------|---------------------------------------|
| 404         | `not_found`     | SMS task not found                    |
| 401         | `unauthorized`  | Invalid or missing authentication     |
| 500         | `internal_error`| Server error processing request       |

---

## Email Endpoints

### Send Template Email

Creates and sends a template-based email.

```
PUT /email
```

#### Description

Creates an email task that renders a template with provided data and sends the email to specified recipients. Supports multiple recipients, CC, BCC, and attachments.

#### Request Body Parameters

| Parameter     | Type     | Required | Description                                           |
|---------------|----------|----------|-------------------------------------------------------|
| `to`          | string[] | Yes      | Array of recipient email addresses                    |
| `cc`          | string[] | No       | Array of CC email addresses                           |
| `bcc`         | string[] | No       | Array of BCC email addresses                          |
| `from`        | string   | No       | Sender email address (uses default if not specified)  |
| `from_name`   | string   | No       | Sender display name                                   |
| `reply_to`    | string   | No       | Reply-to email address                                |
| `subject`     | string   | Yes      | Email subject line (supports template variables)      |
| `template`    | string   | Yes      | Template identifier or name                           |
| `template_data` | object | No       | Data to populate template variables                   |
| `attachments` | array    | No       | Array of attachment objects                           |
| `headers`     | object   | No       | Custom email headers                                  |
| `metadata`    | object   | No       | Additional metadata to attach to the task             |
| `priority`    | integer  | No       | Task priority (higher = more urgent)                  |

#### Attachment Object

| Field         | Type   | Required | Description                                |
|---------------|--------|----------|--------------------------------------------|
| `filename`    | string | Yes      | Attachment filename                        |
| `content`     | string | Yes      | Base64-encoded file content                |
| `content_type`| string | Yes      | MIME type (e.g., `application/pdf`)        |

#### Request Example

```bash
curl -X PUT "https://api.example.com/email" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "to": ["customer@example.com"],
    "cc": ["manager@company.com"],
    "from": "notifications@company.com",
    "from_name": "Company Notifications",
    "reply_to": "support@company.com",
    "subject": "Your Order #{{order_id}} Has Shipped",
    "template": "order_shipped",
    "template_data": {
      "order_id": "ORD-12345",
      "customer_name": "John Doe",
      "tracking_number": "1Z999AA10123456784",
      "carrier": "UPS",
      "estimated_delivery": "January 18, 2024",
      "items": [
        {
          "name": "Widget Pro",
          "quantity": 2,
          "price": "$29.99"
        }
      ]
    },
    "attachments": [
      {
        "filename": "shipping_label.pdf",
        "content": "JVBERi0xLjQKJeLjz9MKMyAwIG9...",
        "content_type": "application/pdf"
      }
    ],
    "metadata": {
      "order_id": "ORD-12345",
      "customer_id": "cust_789"
    }
  }'
```

#### Response Example

**Success (201 Created)**

```json
{
  "status": "success",
  "data": {
    "task_id": "email_task_xyz789ghi012",
    "type": "email",
    "state": "queued",
    "to": ["customer@example.com"],
    "cc": ["manager@company.com"],
    "from": "notifications@company.com",
    "subject": "Your Order #ORD-12345 Has Shipped",
    "template": "order_shipped",
    "attachments_count": 1,
    "created_at": "2024-01-15T11:00:00Z",
    "metadata": {
      "order_id": "ORD-12345",
      "customer_id": "cust_789"
    }
  }
}
```

#### Error Codes

| HTTP Status | Error Code           | Description                                      |
|-------------|----------------------|--------------------------------------------------|
| 400         | `invalid_email`      | One or more email addresses are invalid          |
| 400         | `missing_recipients` | At least one recipient is required               |
| 400         | `missing_subject`    | Subject is required                              |
| 400         | `missing_template`   | Template identifier is required                  |
| 400         | `template_not_found` | Specified template does not exist                |
| 400         | `template_error`     | Error rendering template with provided data      |
| 400         | `attachment_too_large` | Attachment exceeds maximum size                |
| 401         | `unauthorized`       | Invalid or missing authentication                |
| 422         | `invalid_attachment` | Invalid attachment format                        |
| 429         | `rate_limited`       | Too many requests, try again later               |
| 500         | `internal_error`     | Server error processing request                  |

---

### Get Email Status

Retrieves the status and details of an email task.

```
GET /email/{entity}
```

#### Description

Returns the current status of an email task, including delivery status and any bounce/complaint information.

#### Path Parameters

| Parameter | Type   | Required | Description                           |
|-----------|--------|----------|---------------------------------------|
| `entity`  | string | Yes      | Email task ID or entity identifier    |

#### Query Parameters

| Parameter | Type   | Required | Description                                           |
|-----------|--------|----------|-------------------------------------------------------|
| `include` | string | No       | Additional data to include (e.g., `events,content`)   |

#### Request Example

```bash
curl -X GET "https://api.example.com/email/email_task_xyz789ghi012?include=events" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

#### Response Example

**Success (200 OK)**

```json
{
  "status": "success",
  "data": {
    "task_id": "email_task_xyz789ghi012",
    "type": "email",
    "state": "completed",
    "to": ["customer@example.com"],
    "cc": ["manager@company.com"],
    "from": "notifications@company.com",
    "subject": "Your Order #ORD-12345 Has Shipped",
    "template": "order_shipped",
    "delivery_status": "delivered",
    "created_at": "2024-01-15T11:00:00Z",
    "sent_at": "2024-01-15T11:00:03Z",
    "delivered_at": "2024-01-15T11:00:05Z",
    "events": [
      {
        "timestamp": "2024-01-15T11:00:00Z",
        "event": "queued",
        "recipient": null,
        "message": "Email task created"
      },
      {
        "timestamp": "2024-01-15T11:00:03Z",
        "event": "sent",
        "recipient": "customer@example.com",
        "message": "Email sent"
      },
      {
        "timestamp": "2024-01-15T11:00:05Z",
        "event": "delivered",
        "recipient": "customer@example.com",
        "message": "Email delivered"
      },
      {
        "timestamp": "2024-01-15T11:00:03Z",
        "event": "sent",
        "recipient": "manager@company.com",
        "message": "Email sent"
      },
      {
        "timestamp": "2024-01-15T11:00:06Z",
        "event": "delivered",
        "recipient": "manager@company.com",
        "message": "Email delivered"
      }
    ],
    "opens": 1,
    "clicks": 0,
    "metadata": {
      "order_id": "ORD-12345",
      "customer_id": "cust_789"
    }
  }
}
```

#### Email Delivery States

| State       | Description                                      |
|-------------|--------------------------------------------------|
| `queued`    | Task created, waiting to be processed            |
| `rendering` | Template is being rendered                       |
| `sending`   | Email is being sent                              |
| `sent`      | Email sent to mail server                        |
| `delivered` | Delivery confirmed                               |
| `bounced`   | Email bounced (hard or soft)                     |
| `complained`| Recipient marked as spam                         |
| `failed`    | Sending failed                                   |

#### Email Event Types

| Event       | Description                                      |
|-------------|--------------------------------------------------|
| `queued`    | Email task was created                           |
| `rendered`  | Template was successfully rendered               |
| `sent`      | Email was sent to the mail server                |
| `delivered` | Email was delivered to recipient                 |
| `opened`    | Recipient opened the email                       |
| `clicked`   | Recipient clicked a link in the email            |
| `bounced`   | Email bounced                                    |
| `complained`| Recipient marked email as spam                   |
| `unsubscribed` | Recipient unsubscribed                        |

#### Error Codes

| HTTP Status | Error Code      | Description                           |
|-------------|-----------------|---------------------------------------|
| 404         | `not_found`     | Email task not found                  |
| 401         | `unauthorized`  | Invalid or missing authentication     |
| 500         | `internal_error`| Server error processing request       |

---

## Related Documentation

- [Task Endpoints](task-endpoints.md) - General task management and status
- [API Overview](README.md) - Authentication and general API information
- [CDR Endpoints](cdr-endpoints.md) - Call detail record processing