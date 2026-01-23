# Generic API Endpoints

This document covers platform-agnostic and utility endpoints in the Service Gateway API. These endpoints provide cross-platform data access, error handling, statistics, and general-purpose query capabilities.

## Overview

The generic API endpoints abstract away platform-specific implementations, allowing unified access to data sources through token-based authentication and feed identifiers. This enables client applications to interact with multiple backend systems using a consistent interface.

## Base URL

All endpoints are relative to your Service Gateway installation:

```
https://{your-gateway-host}/
```

## Related Documentation

- [Feed Management Endpoints](feed-endpoints.md) - Email/message feed operations
- [Microsoft Dynamics Endpoints](msdynamics-endpoints.md) - Dynamics CRM integration
- [Salesforce Endpoints](salesforce-endpoints.md) - Salesforce integration
- [Zendesk Endpoints](zendesk-endpoints.md) - Zendesk integration
- [Custom Server Endpoints](custom-endpoints.md) - Custom application server integration
- [API Response Models](../models/api-response-models.md) - Response format specifications

---

## Error Handling

### GET /e404

Default route handler for 404 errors. Returns standardized error response for unknown API calls.

**Handler:** `E404_Controller::index`

#### Request

```bash
curl -X GET "https://{gateway-host}/e404" \
  -H "Accept: application/json"
```

#### Response

**Status:** `404 Not Found`

```json
{
  "status": "error",
  "error_code": 404,
  "message": "Unknown API call",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `404` | The requested endpoint does not exist |

---

### GET /e404/index

Explicit handler for 404 errors - returns unknown API call error.

**Handler:** `E404_Controller::index`

#### Request

```bash
curl -X GET "https://{gateway-host}/e404/index" \
  -H "Accept: application/json"
```

#### Response

**Status:** `404 Not Found`

```json
{
  "status": "error",
  "error_code": 404,
  "message": "Unknown API call",
  "path": "/nonexistent/endpoint",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Unified API Endpoints

These endpoints provide platform-agnostic data access based on authenticated tokens and feed configurations.

### GET /api/query

Query data source based on authenticated token and feed ID. The underlying platform is determined by the feed configuration.

**Handler:** `Sgapi_Model::QuerySource`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | query | Yes | Authentication token |
| `feedid` | string | query | Yes | Feed identifier determining data source |
| `object` | string | query | Yes | Object/entity type to query |
| `conditions` | string | query | No | Query conditions (JSON encoded) |
| `fields` | string | query | No | Comma-separated list of fields to return |
| `orderby` | string | query | No | Field to order results by |
| `order` | string | query | No | Sort direction: `asc` or `desc` |
| `limit` | integer | query | No | Maximum records to return |
| `offset` | integer | query | No | Number of records to skip |

#### Request

```bash
curl -X GET "https://{gateway-host}/api/query" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -G \
  --data-urlencode "token=abc123token" \
  --data-urlencode "feedid=feed_001" \
  --data-urlencode "object=Contact" \
  --data-urlencode "fields=Id,FirstName,LastName,Email" \
  --data-urlencode "conditions={\"Email\":{\"like\":\"%@example.com\"}}" \
  --data-urlencode "limit=50"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "Id": "003xx000004TmiA",
        "FirstName": "John",
        "LastName": "Smith",
        "Email": "john.smith@example.com"
      },
      {
        "Id": "003xx000004TmiB",
        "FirstName": "Jane",
        "LastName": "Doe",
        "Email": "jane.doe@example.com"
      }
    ],
    "total_count": 2,
    "has_more": false
  },
  "source_type": "salesforce",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid query parameters or malformed conditions |
| `401` | Invalid or expired authentication token |
| `403` | Access denied to specified feed |
| `404` | Feed not found |
| `500` | Internal server error or data source unavailable |

---

### GET /api/queryraw

Execute raw query against data source. Query syntax depends on the underlying platform (SOQL for Salesforce, FetchXML for Dynamics, SQL for databases).

**Handler:** `Sgapi_Model::QueryRaw`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | query | Yes | Authentication token |
| `feedid` | string | query | Yes | Feed identifier determining data source |
| `query` | string | query | Yes | Raw query string in platform-native syntax |

#### Request

```bash
curl -X GET "https://{gateway-host}/api/queryraw" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "token=abc123token" \
  --data-urlencode "feedid=feed_001" \
  --data-urlencode "query=SELECT Id, Name, Email FROM Contact WHERE CreatedDate = LAST_MONTH"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "Id": "003xx000004TmiA",
        "Name": "John Smith",
        "Email": "john.smith@example.com"
      }
    ],
    "total_count": 1,
    "query_executed": "SELECT Id, Name, Email FROM Contact WHERE CreatedDate = LAST_MONTH"
  },
  "source_type": "salesforce",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid or malformed query syntax |
| `401` | Invalid or expired authentication token |
| `403` | Access denied to specified feed or query not permitted |
| `404` | Feed not found |
| `500` | Query execution failed or data source unavailable |

---

### POST /api/add

Add new data object to the data source. The target platform is determined by the feed configuration.

**Handler:** `Sgapi_Model::AddData`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | body | Yes | Authentication token |
| `feedid` | string | body | Yes | Feed identifier determining data source |
| `object` | string | body | Yes | Object/entity type to create |
| `data` | object | body | Yes | Field values for the new record |

#### Request

```bash
curl -X POST "https://{gateway-host}/api/add" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123token",
    "feedid": "feed_001",
    "object": "Contact",
    "data": {
      "FirstName": "Alice",
      "LastName": "Johnson",
      "Email": "alice.johnson@example.com",
      "Phone": "+1-555-0123"
    }
  }'
```

#### Response

**Status:** `201 Created`

```json
{
  "status": "success",
  "data": {
    "id": "003xx000004TmiC",
    "object": "Contact",
    "created": true
  },
  "source_type": "salesforce",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body or missing required fields |
| `401` | Invalid or expired authentication token |
| `403` | Access denied to specified feed or create operation not permitted |
| `404` | Feed not found |
| `409` | Duplicate record or constraint violation |
| `422` | Validation failed for provided data |
| `500` | Internal server error or data source unavailable |

---

## Statistics

### GET /stats/{entity}

Get cached statistical data for the service gateway. Provides performance metrics and usage statistics.

**Handler:** `Stats_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Statistics entity type: `requests`, `feeds`, `errors`, `performance`, `all` |
| `from` | string | query | No | Start date for statistics range (ISO 8601 format) |
| `to` | string | query | No | End date for statistics range (ISO 8601 format) |
| `format` | string | query | No | Output format: `json` (default), `xml` |

#### Request

```bash
curl -X GET "https://{gateway-host}/stats/performance" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "from=2024-01-01T00:00:00Z" \
  --data-urlencode "to=2024-01-15T23:59:59Z"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "entity": "performance",
  "data": {
    "period": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-01-15T23:59:59Z"
    },
    "metrics": {
      "total_requests": 125430,
      "successful_requests": 123250,
      "failed_requests": 2180,
      "average_response_time_ms": 245,
      "p95_response_time_ms": 580,
      "p99_response_time_ms": 1250
    },
    "by_platform": {
      "salesforce": {
        "requests": 65000,
        "avg_response_ms": 210
      },
      "msdynamics": {
        "requests": 35000,
        "avg_response_ms": 285
      },
      "zendesk": {
        "requests": 25430,
        "avg_response_ms": 265
      }
    }
  },
  "cached_at": "2024-01-15T10:25:00Z",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Available Entity Types

| Entity | Description |
|--------|-------------|
| `requests` | Request count and breakdown by endpoint |
| `feeds` | Active feeds and their usage statistics |
| `errors` | Error rates and common error types |
| `performance` | Response times and throughput metrics |
| `all` | Combined statistics from all entities |

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid date range or entity type |
| `401` | Authentication required for statistics access |
| `403` | Access denied to statistics |
| `404` | Unknown statistics entity |
| `500` | Statistics service unavailable |

---

## SGAPI Controller Endpoints

Token-based endpoints for unified platform access through the SGAPI controller.

### GET /sgapi/query/{token}/{feedid}

Query the source for data with given type of query and parameters.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `object` | string | query | Yes | Object/entity type to query |
| `querytype` | string | query | No | Type of query: `all`, `byId`, `byCondition` |
| `conditions` | string | query | No | Query conditions (JSON encoded) |
| `fields` | string | query | No | Comma-separated fields to return |
| `limit` | integer | query | No | Maximum records to return |

#### Request

```bash
curl -X GET "https://{gateway-host}/sgapi/query/abc123token/feed_001" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "object=Account" \
  --data-urlencode "querytype=byCondition" \
  --data-urlencode "conditions={\"Industry\":\"Technology\"}" \
  --data-urlencode "fields=Id,Name,Industry,Website" \
  --data-urlencode "limit=100"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "Id": "001xx000003DGbY",
        "Name": "Acme Technology",
        "Industry": "Technology",
        "Website": "https://acme.tech"
      }
    ],
    "total_count": 1
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid query parameters |
| `401` | Invalid or expired token |
| `404` | Feed not found |
| `500` | Query execution failed |

---

### POST /sgapi/add/{token}/{feedid}

Add new data to the source.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `object` | string | body | Yes | Object/entity type to create |
| `data` | object | body | Yes | Field values for new record |

#### Request

```bash
curl -X POST "https://{gateway-host}/sgapi/add/abc123token/feed_001" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "Lead",
    "data": {
      "FirstName": "Bob",
      "LastName": "Wilson",
      "Company": "Wilson Enterprises",
      "Email": "bob@wilson.com",
      "Status": "New"
    }
  }'
```

#### Response

**Status:** `201 Created`

```json
{
  "status": "success",
  "data": {
    "id": "00Qxx000001abc123",
    "object": "Lead",
    "created": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body |
| `401` | Invalid or expired token |
| `404` | Feed not found |
| `422` | Validation failed |
| `500` | Create operation failed |

---

### PUT /sgapi/add/{token}/{feedid}

Update existing data in the source.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `object` | string | body | Yes | Object/entity type to update |
| `id` | string | body | Yes | Record identifier to update |
| `data` | object | body | Yes | Field values to update |

#### Request

```bash
curl -X PUT "https://{gateway-host}/sgapi/add/abc123token/feed_001" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "Lead",
    "id": "00Qxx000001abc123",
    "data": {
      "Status": "Qualified",
      "Rating": "Hot"
    }
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "id": "00Qxx000001abc123",
    "object": "Lead",
    "updated": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request body |
| `401` | Invalid or expired token |
| `404` | Feed or record not found |
| `422` | Validation failed |
| `500` | Update operation failed |

---

### DELETE /sgapi/deleterecord/{token}/{feedid}

Delete a record from the source.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `object` | string | query | Yes | Object/entity type |
| `id` | string | query | Yes | Record identifier to delete |

#### Request

```bash
curl -X DELETE "https://{gateway-host}/sgapi/deleterecord/abc123token/feed_001" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "object=Lead" \
  --data-urlencode "id=00Qxx000001abc123"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "id": "00Qxx000001abc123",
    "object": "Lead",
    "deleted": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid parameters |
| `401` | Invalid or expired token |
| `403` | Delete operation not permitted |
| `404` | Feed or record not found |
| `500` | Delete operation failed |

---

### GET /sgapi/queryraw/{token}/{feedid}

Execute raw query in platform-native syntax (SOQL/SOSL for Salesforce, FetchXML for Dynamics, etc.).

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `query` | string | query | Yes | Raw query string in platform-native syntax |

#### Request

```bash
curl -X GET "https://{gateway-host}/sgapi/queryraw/abc123token/feed_001" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "query=SELECT Id, Name FROM Account WHERE Type = 'Customer' LIMIT 10"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "Id": "001xx000003DGbY",
        "Name": "Acme Corp"
      }
    ],
    "total_count": 1
  },
  "query_type": "SOQL",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid or malformed query |
| `401` | Invalid or expired token |
| `403` | Query not permitted |
| `404` | Feed not found |
| `500` | Query execution failed |

---

### GET /sgapi/metaquery/{token}/{feedid}

Get metadata including available methods, operators, objects, and fields.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `type` | string | query | Yes | Metadata type: `methodlist`, `operatorlist`, `objectlist`, `fieldlist` |
| `object` | string | query | No | Object name (required when type=`fieldlist`) |

#### Request

```bash
curl -X GET "https://{gateway-host}/sgapi/metaquery/abc123token/feed_001" \
  -H "Accept: application/json" \
  -G \
  --data-urlencode "type=objectlist"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "type": "objectlist",
    "objects": [
      {
        "name": "Account",
        "label": "Account",
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deletable": true
      },
      {
        "name": "Contact",
        "label": "Contact",
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deletable": true
      },
      {
        "name": "Lead",
        "label": "Lead",
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deletable": true
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid metadata type |
| `401` | Invalid or expired token |
| `404` | Feed not found |
| `500` | Metadata retrieval failed |

---

### GET /sgapi/updatemetadata/{token}/{feedid}

Update metadata file from server. Refreshes cached metadata for the specified feed.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |

#### Request

```bash
curl -X GET "https://{gateway-host}/sgapi/updatemetadata/abc123token/feed_001" \
  -H "Accept: application/json"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "metadata_updated": true,
    "objects_count": 45,
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |
| `404` | Feed not found |
| `500` | Metadata update failed |

---

### POST /sgapi/create_dataset/{token}/{feedid}

Create a new dataset in the data source.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `name` | string | body | Yes | Dataset name |
| `schema` | object | body | Yes | Dataset schema definition |

#### Request

```bash
curl -X POST "https://{gateway-host}/sgapi/create_dataset/abc123token/feed_001" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CustomMetrics",
    "schema": {
      "fields": [
        {"name": "date", "type": "DATE"},
        {"name": "metric_name", "type": "VARCHAR(100)"},
        {"name": "value", "type": "DECIMAL(10,2)"}
      ],
      "primary_key": ["date", "metric_name"]
    }
  }'
```

#### Response

**Status:** `201 Created`

```json
{
  "status": "success",
  "data": {
    "dataset_id": "ds_001abc",
    "name": "CustomMetrics",
    "created": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid schema definition |
| `401` | Invalid or expired token |
| `404` | Feed not found |
| `409` | Dataset already exists |
| `500` | Dataset creation failed |

---

### POST /sgapi/flush_records/{token}/{feedid}

Flush records from buffer to the data source.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `dataset` | string | body | No | Specific dataset to flush (optional, flushes all if not specified) |

#### Request

```bash
curl -X POST "https://{gateway-host}/sgapi/flush_records/abc123token/feed_001" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "CustomMetrics"
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "records_flushed": 250,
    "dataset": "CustomMetrics",
    "flush_time_ms": 1250
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid request |
| `401` | Invalid or expired token |
| `404` | Feed or dataset not found |
| `500` | Flush operation failed |

---

### POST /sgapi/custom_call/{token}/{feedid}

Execute a custom API call against the data source. Allows for platform-specific operations not covered by standard endpoints.

**Handler:** `Sgapi_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `method` | string | body | Yes | Custom method name to execute |
| `params` | object | body | No | Parameters for the custom method |

#### Request

```bash
curl -X POST "https://{gateway-host}/sgapi/custom_call/abc123token/feed_001" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "convertLead",
    "params": {
      "leadId": "00Qxx000001abc123",
      "convertedStatus": "Qualified",
      "createOpportunity": true,
      "opportunityName": "New Opportunity from Lead"
    }
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "method": "convertLead",
    "result": {
      "accountId": "001xx000003NEW01",
      "contactId": "003xx000004NEW01",
      "opportunityId": "006xx000005NEW01",
      "success": true
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid method or parameters |
| `401` | Invalid or expired token |
| `403` | Custom method not permitted |
| `404` | Feed not found or method not found |
| `500` | Custom call execution failed |

---

## Authentication Endpoints

### PUT /sgapi_auth/auth

Create feed context and load initial configuration. Authenticates against the target platform and establishes a session.

**Handler:** `Sgapi_Auth_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `feedid` | string | body | Yes | Feed identifier |
| `credentials` | object | body | Yes | Platform-specific credentials |
| `norefresh` | boolean | body | No | If true, skip initial data refresh |

#### Request

```bash
curl -X PUT "https://{gateway-host}/sgapi_auth/auth" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "feedid": "feed_001",
    "credentials": {
      "username": "user@example.com",
      "password": "securepassword",
      "security_token": "optional_token"
    },
    "norefresh": false
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "token": "abc123xyz789token",
    "expires_at": "2024-01-15T12:30:00Z",
    "feed_type": "salesforce",
    "permissions": ["query", "create", "update", "delete"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid credentials format |
| `401` | Authentication failed |
| `404` | Feed configuration not found |
| `500` | Authentication service error |

---

### DELETE /sgapi_auth/auth/{token}

Destroy feed context and invalidate authentication token.

**Handler:** `Sgapi_Auth_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token to invalidate |

#### Request

```bash
curl -X DELETE "https://{gateway-host}/sgapi_auth/auth/abc123xyz789token" \
  -H "Accept: application/json"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "token": "abc123xyz789token",
    "destroyed": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `404` | Token not found or already expired |
| `500` | Logout operation failed |

---

### POST /sgapi_auth/auth/{token}

Modify an existing context. Can be used to refresh token or update session parameters.

**Handler:** `Sgapi_Auth_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `action` | string | body | Yes | Action to perform: `refresh`, `extend`, `update_permissions` |
| `params` | object | body | No | Additional parameters for the action |

#### Request

```bash
curl -X POST "https://{gateway-host}/sgapi_auth/auth/abc123xyz789token" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "refresh",
    "params": {
      "extend_by_hours": 2
    }
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "token": "abc123xyz789token",
    "action": "refresh",
    "new_expires_at": "2024-01-15T14:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid action or parameters |
| `401` | Token invalid or expired |
| `403` | Action not permitted |
| `500` | Context modification failed |

---

## Contact Query Endpoints

### GET /sgapi_contact/query/{token}/{feedid}/{queryType}/{param1}/{param2}

Query the source for contacts with given type of query and parameters.

**Handler:** `Sgapi_Contact_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `feedid` | string | path | Yes | Feed identifier |
| `queryType` | string | path | Yes | Query type: `byEmail`, `byPhone`, `byName`, `byId`, `byCustom` |
| `param1` | string | path | Yes | Primary query parameter |
| `param2` | string | path | No | Secondary query parameter (optional) |

#### Request

```bash
curl -X GET "https://{gateway-host}/sgapi_contact/query/abc123token/feed_001/byEmail/john@example.com/_" \
  -H "Accept: application/json"
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "contacts": [
      {
        "id": "003xx000004TmiA",
        "firstName": "John",
        "lastName": "Smith",
        "email": "john@example.com",
        "phone": "+1-555-0123",
        "company": "Acme Corp",
        "title": "Sales Manager"
      }
    ],
    "total_count": 1,
    "query_type": "byEmail"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Query Types

| Query Type | Description | param1 | param2 |
|------------|-------------|--------|--------|
| `byEmail` | Search by email address | Email address | - |
| `byPhone` | Search by phone number | Phone number | - |
| `byName` | Search by name | First name | Last name |
| `byId` | Retrieve by record ID | Record ID | - |
| `byCustom` | Custom field search | Field name | Field value |

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid query type or parameters |
| `401` | Invalid or expired token |
| `404` | Feed not found or no contacts found |
| `500` | Query execution failed |

---

### PUT /sgapi_contact/activity/{token}

Add activity record to refresh virtual inbox using original credentials.

**Handler:** `Sgapi_Contact_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `contactId` | string | body | Yes | Contact ID to add activity for |
| `activityType` | string | body | Yes | Type of activity: `call`, `email`, `meeting`, `task` |
| `subject` | string | body | Yes | Activity subject |
| `description` | string | body | No | Activity description |
| `timestamp` | string | body | No | Activity timestamp (ISO 8601) |

#### Request

```bash
curl -X PUT "https://{gateway-host}/sgapi_contact/activity/abc123token" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contactId": "003xx000004TmiA",
    "activityType": "call",
    "subject": "Follow-up call",
    "description": "Discussed product features and pricing",
    "timestamp": "2024-01-15T10:00:00Z"
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "activityId": "00Txx000001xyz",
    "contactId": "003xx000004TmiA",
    "activityType": "call",
    "created": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid activity data |
| `401` | Invalid or expired token |
| `404` | Contact not found |
| `500` | Activity creation failed |

---

## Task Management

### PUT /sgapi_tasks/task/{token}

Add activity to a task - refresh virtual inbox using original credentials.

**Handler:** `Sgapi_Tasks_Controller::__call`

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `token` | string | path | Yes | Authentication token |
| `taskId` | string | body | No | Existing task ID (if updating) |
| `subject` | string | body | Yes | Task subject |
| `description` | string | body | No | Task description |
| `dueDate` | string | body | No | Due date (ISO 8601) |
| `priority` | string | body | No | Priority: `low`, `normal`, `high` |
| `status` | string | body | No | Status: `not_started`, `in_progress`, `completed` |
| `relatedTo` | object | body | No | Related record reference |

#### Request

```bash
curl -X PUT "https://{gateway-host}/sgapi_tasks/task/abc123token" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Follow up with customer",
    "description": "Send product information and schedule demo",
    "dueDate": "2024-01-20T17:00:00Z",
    "priority": "high",
    "status": "not_started",
    "relatedTo": {
      "type": "Contact",
      "id": "003xx000004TmiA"
    }
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "status": "success",
  "data": {
    "taskId": "00Txx000002abc",
    "subject": "Follow up with customer",
    "created": true,
    "dueDate": "2024-01-20T17:00:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid task data |
| `401` | Invalid or expired token |
| `404` | Related record not found |
| `500` | Task operation failed |

---

## Common Response Formats

### Success Response

All successful responses follow this format:

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response

All error responses follow this format:

```json
{
  "status": "error",
  "error_code": 400,
  "message": "Description of the error",
  "details": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Rate Limiting

The generic API endpoints may be subject to rate limiting based on the underlying platform limits:

| Platform | Rate Limit |
|----------|------------|
| Salesforce | Based on org edition (typically 15,000-100,000 API calls/day) |
| Dynamics | Based on license (typically 20,000/user/24h) |
| Zendesk | 200-700 requests/minute based on plan |
| Custom | Configurable per integration |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705315800
```