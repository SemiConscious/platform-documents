# Zendesk API Endpoints

This document covers the Zendesk helpdesk integration endpoints provided by the Service Gateway. These endpoints allow you to query, create, and update objects in Zendesk including tickets, users, organizations, and more.

## Overview

The Zendesk integration provides a simplified REST interface to interact with Zendesk's API. All endpoints require proper authentication and support standard CRUD operations on Zendesk objects.

**Base URL:** `/zendesk`

**Related Documentation:**
- [API Overview](README.md)
- [Generic Query Endpoints](generic-endpoints.md)
- [API Response Models](../models/api-response-models.md)

---

## Endpoints

### Query Zendesk Data

Retrieve data from Zendesk including tickets, users, organizations, groups, and other Zendesk objects.

```
GET /zendesk/query
```

#### Description

Query Zendesk data with support for filtering, field selection, and pagination. This endpoint translates Service Gateway query parameters into Zendesk API calls and returns normalized results.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | query | Yes | Zendesk object type to query (e.g., `tickets`, `users`, `organizations`, `groups`) |
| `conditions` | string | query | No | Filter conditions in JSON format |
| `fields` | string | query | No | Comma-separated list of fields to return |
| `limit` | integer | query | No | Maximum number of records to return (default: 100) |
| `offset` | integer | query | No | Number of records to skip for pagination |
| `orderby` | string | query | No | Field name to sort results by |
| `order` | string | query | No | Sort direction: `asc` or `desc` (default: `asc`) |

#### Supported Objects

| Object | Description |
|--------|-------------|
| `tickets` | Support tickets |
| `users` | End users and agents |
| `organizations` | Customer organizations |
| `groups` | Agent groups |
| `ticket_fields` | Custom ticket fields |
| `user_fields` | Custom user fields |
| `organization_fields` | Custom organization fields |
| `brands` | Zendesk brands |
| `ticket_forms` | Ticket form configurations |

#### Request Example

```bash
# Query all open tickets
curl -X GET "https://api.example.com/zendesk/query?object=tickets&conditions={\"status\":\"open\"}&limit=50" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Query users in a specific organization
curl -X GET "https://api.example.com/zendesk/query?object=users&conditions={\"organization_id\":12345}&fields=id,name,email" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Query organizations with pagination
curl -X GET "https://api.example.com/zendesk/query?object=organizations&limit=25&offset=50&orderby=name&order=asc" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

**Success Response (200 OK):**

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": 123456,
      "subject": "Cannot login to account",
      "description": "User reports login issues since yesterday",
      "status": "open",
      "priority": "high",
      "requester_id": 789012,
      "assignee_id": 345678,
      "organization_id": 901234,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:22:00Z",
      "tags": ["login", "urgent"]
    },
    {
      "id": 123457,
      "subject": "Feature request: Dark mode",
      "description": "Customer requesting dark mode option",
      "status": "open",
      "priority": "low",
      "requester_id": 789013,
      "assignee_id": null,
      "organization_id": 901234,
      "created_at": "2024-01-15T11:45:00Z",
      "updated_at": "2024-01-15T11:45:00Z",
      "tags": ["feature-request"]
    }
  ],
  "metadata": {
    "object": "tickets",
    "total_count": 156,
    "has_more": true
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_OBJECT` | The specified object type is not supported |
| 400 | `INVALID_CONDITIONS` | The conditions parameter contains invalid JSON |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 403 | `FORBIDDEN` | Insufficient permissions to access the resource |
| 429 | `RATE_LIMITED` | Zendesk API rate limit exceeded |
| 500 | `ZENDESK_ERROR` | Error returned from Zendesk API |

---

### Create Zendesk Object

Create a new object in Zendesk such as a ticket, user, or organization.

```
POST /zendesk/add
```

#### Description

Create new records in Zendesk. The request body should contain the object type and the data fields required for that object type. Required fields vary by object type.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | body | Yes | Zendesk object type to create |
| `data` | object | body | Yes | Object data fields |

#### Required Fields by Object Type

| Object | Required Fields |
|--------|-----------------|
| `tickets` | `subject`, `comment.body` |
| `users` | `name`, `email` |
| `organizations` | `name` |
| `groups` | `name` |

#### Request Example

```bash
# Create a new ticket
curl -X POST "https://api.example.com/zendesk/add" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "tickets",
    "data": {
      "subject": "New support request",
      "comment": {
        "body": "Customer needs help with billing inquiry"
      },
      "priority": "normal",
      "requester_id": 789012,
      "tags": ["billing", "inquiry"]
    }
  }'
```

```bash
# Create a new user
curl -X POST "https://api.example.com/zendesk/add" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "users",
    "data": {
      "name": "John Smith",
      "email": "john.smith@example.com",
      "phone": "+1-555-123-4567",
      "organization_id": 901234,
      "role": "end-user",
      "user_fields": {
        "customer_tier": "premium"
      }
    }
  }'
```

```bash
# Create a new organization
curl -X POST "https://api.example.com/zendesk/add" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "organizations",
    "data": {
      "name": "Acme Corporation",
      "domain_names": ["acme.com", "acmecorp.com"],
      "details": "Enterprise customer since 2020",
      "notes": "Primary contact: Jane Doe",
      "organization_fields": {
        "contract_type": "enterprise",
        "account_manager": "Mike Johnson"
      }
    }
  }'
```

#### Response Example

**Success Response (201 Created):**

```json
{
  "status": "success",
  "message": "Object created successfully",
  "data": {
    "id": 123458,
    "subject": "New support request",
    "description": "Customer needs help with billing inquiry",
    "status": "new",
    "priority": "normal",
    "requester_id": 789012,
    "submitter_id": 345678,
    "assignee_id": null,
    "organization_id": null,
    "created_at": "2024-01-15T16:00:00Z",
    "updated_at": "2024-01-15T16:00:00Z",
    "tags": ["billing", "inquiry"],
    "url": "https://yoursubdomain.zendesk.com/api/v2/tickets/123458.json"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `MISSING_REQUIRED_FIELD` | A required field is missing from the request |
| 400 | `INVALID_FIELD_VALUE` | A field contains an invalid value |
| 400 | `INVALID_OBJECT` | The specified object type is not supported |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 403 | `FORBIDDEN` | Insufficient permissions to create the object |
| 409 | `DUPLICATE_RECORD` | A record with the same unique identifier already exists |
| 422 | `VALIDATION_ERROR` | The request data failed Zendesk validation |
| 429 | `RATE_LIMITED` | Zendesk API rate limit exceeded |
| 500 | `ZENDESK_ERROR` | Error returned from Zendesk API |

---

### Update Zendesk Object

Update an existing object in Zendesk.

```
PUT /zendesk/update
```

#### Description

Update existing records in Zendesk. You must provide the object type, the record ID, and the fields to update. Only provided fields will be modified; other fields remain unchanged.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | body | Yes | Zendesk object type to update |
| `id` | integer | body | Yes | ID of the record to update |
| `data` | object | body | Yes | Fields to update |

#### Request Example

```bash
# Update ticket status and add a comment
curl -X PUT "https://api.example.com/zendesk/update" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "tickets",
    "id": 123456,
    "data": {
      "status": "pending",
      "priority": "high",
      "assignee_id": 345678,
      "comment": {
        "body": "Escalating to senior support team",
        "public": false
      },
      "tags": ["escalated", "billing", "urgent"]
    }
  }'
```

```bash
# Update user information
curl -X PUT "https://api.example.com/zendesk/update" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "users",
    "id": 789012,
    "data": {
      "phone": "+1-555-987-6543",
      "organization_id": 901235,
      "user_fields": {
        "customer_tier": "enterprise"
      }
    }
  }'
```

```bash
# Update organization details
curl -X PUT "https://api.example.com/zendesk/update" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "organizations",
    "id": 901234,
    "data": {
      "notes": "Contract renewed through 2025",
      "organization_fields": {
        "contract_type": "enterprise-plus",
        "renewal_date": "2025-12-31"
      }
    }
  }'
```

#### Response Example

**Success Response (200 OK):**

```json
{
  "status": "success",
  "message": "Object updated successfully",
  "data": {
    "id": 123456,
    "subject": "Cannot login to account",
    "description": "User reports login issues since yesterday",
    "status": "pending",
    "priority": "high",
    "requester_id": 789012,
    "assignee_id": 345678,
    "organization_id": 901234,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T16:30:00Z",
    "tags": ["escalated", "billing", "urgent"]
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `MISSING_ID` | The record ID was not provided |
| 400 | `INVALID_FIELD_VALUE` | A field contains an invalid value |
| 400 | `INVALID_OBJECT` | The specified object type is not supported |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 403 | `FORBIDDEN` | Insufficient permissions to update the object |
| 404 | `NOT_FOUND` | The specified record does not exist |
| 422 | `VALIDATION_ERROR` | The request data failed Zendesk validation |
| 429 | `RATE_LIMITED` | Zendesk API rate limit exceeded |
| 500 | `ZENDESK_ERROR` | Error returned from Zendesk API |

---

## Ticket Status Values

| Status | Description |
|--------|-------------|
| `new` | Ticket has not been assigned |
| `open` | Ticket is assigned and being worked on |
| `pending` | Awaiting response from requester |
| `hold` | Ticket is on hold |
| `solved` | Issue has been resolved |
| `closed` | Ticket is permanently closed |

## Priority Values

| Priority | Description |
|----------|-------------|
| `urgent` | Highest priority - immediate attention required |
| `high` | High priority |
| `normal` | Standard priority (default) |
| `low` | Low priority |

---

## Rate Limiting

Zendesk enforces API rate limits which are passed through by the Service Gateway. Default limits vary by Zendesk plan:

| Plan | Rate Limit |
|------|------------|
| Essential | 10 requests per minute |
| Team | 200 requests per minute |
| Professional | 400 requests per minute |
| Enterprise | 700 requests per minute |

When rate limited, the API returns a `429` status code with a `Retry-After` header indicating when to retry.

---

## See Also

- [Generic Query Endpoints](generic-endpoints.md) - Unified query interface for all data sources
- [API Response Models](../models/api-response-models.md) - Standard response formats
- [Salesforce Endpoints](salesforce-endpoints.md) - Similar CRM integration patterns
- [Feed Endpoints](feed-endpoints.md) - Message feed operations