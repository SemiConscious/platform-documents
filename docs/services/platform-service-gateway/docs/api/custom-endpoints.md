# Custom Data Source Endpoints

This document covers endpoints for custom data source integrations in the Service Gateway API. These endpoints allow you to connect to and interact with custom application servers and data sources that don't fit the standard CRM connectors.

## Overview

The custom data source endpoints provide a flexible interface for integrating with proprietary or custom-built application servers. This includes querying data, executing raw queries, managing objects, and retrieving schema information.

**Base URL:** `/custom`

**Related Documentation:**
- [API Overview](README.md)
- [Generic API Endpoints](generic-endpoints.md)
- [API Response Models](../models/api-response-models.md)

---

## Endpoints

### Query Custom Data Source

Query data from a custom application server with structured conditions.

```
GET /custom/query
```

#### Description

Retrieves data from a custom application server using structured query parameters. Supports filtering, field selection, ordering, and pagination.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | query | Yes | The object/entity type to query |
| `conditions` | string | query | No | JSON-encoded filter conditions |
| `fields` | string | query | No | Comma-separated list of fields to return |
| `orderby` | string | query | No | Field name to order results by |
| `order` | string | query | No | Sort direction: `ASC` or `DESC` |
| `limit` | integer | query | No | Maximum number of records to return |
| `offset` | integer | query | No | Number of records to skip |

#### Request Example

```bash
curl -X GET "https://api.example.com/custom/query?object=customers&conditions=%7B%22status%22%3A%22active%22%7D&fields=id,name,email&limit=50&orderby=created_at&order=DESC" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "records": [
      {
        "id": "cust_001",
        "name": "Acme Corporation",
        "email": "contact@acme.com"
      },
      {
        "id": "cust_002",
        "name": "Global Industries",
        "email": "info@globalind.com"
      }
    ],
    "total_count": 245,
    "returned_count": 2,
    "offset": 0
  },
  "metadata": {
    "query_time_ms": 45,
    "server": "custom-app-01"
  }
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified object type does not exist |
| 400 | `INVALID_CONDITIONS` | The conditions parameter is malformed JSON |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `FORBIDDEN` | Access to the requested object is denied |
| 500 | `SERVER_ERROR` | Custom application server error |

---

### Execute Raw Query

Execute a raw query against the custom application server.

```
GET /custom/queryraw
```

#### Description

Executes a raw, unstructured query directly against the custom application server. This endpoint provides maximum flexibility for complex queries that cannot be expressed through the standard query interface.

> **Warning:** Raw queries bypass standard validation. Ensure proper input sanitization to prevent injection attacks.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `query` | string | query | Yes | The raw query string to execute |
| `format` | string | query | No | Response format: `json` (default), `xml`, `csv` |
| `timeout` | integer | query | No | Query timeout in seconds (default: 30, max: 120) |

#### Request Example

```bash
curl -X GET "https://api.example.com/custom/queryraw?query=SELECT%20*%20FROM%20transactions%20WHERE%20amount%20%3E%201000&format=json&timeout=60" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "transaction_id": "txn_98765",
        "amount": 1500.00,
        "currency": "USD",
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "transaction_id": "txn_98766",
        "amount": 2300.50,
        "currency": "USD",
        "timestamp": "2024-01-15T11:45:00Z"
      }
    ],
    "row_count": 2
  },
  "metadata": {
    "query_time_ms": 128,
    "raw_query": "SELECT * FROM transactions WHERE amount > 1000"
  }
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_QUERY` | The query syntax is invalid |
| 400 | `QUERY_TOO_LONG` | Query exceeds maximum length limit |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 408 | `QUERY_TIMEOUT` | Query execution exceeded timeout limit |
| 500 | `EXECUTION_ERROR` | Error executing query on application server |

---

### Add Custom Object

Add a new object/record via the custom application server.

```
POST /custom/add
```

#### Description

Creates a new object or record in the custom application server. The object type and data structure depend on the configured custom server schema.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | body | Yes | The object/entity type to create |
| `data` | object | body | Yes | The field values for the new record |
| `validate` | boolean | body | No | Whether to validate data before insert (default: true) |
| `return_record` | boolean | body | No | Return the created record in response (default: false) |

#### Request Example

```bash
curl -X POST "https://api.example.com/custom/add" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "customers",
    "data": {
      "name": "New Tech Solutions",
      "email": "contact@newtech.com",
      "phone": "+1-555-0123",
      "industry": "Technology",
      "status": "active",
      "custom_field_1": "Enterprise",
      "custom_field_2": "Q1-2024"
    },
    "validate": true,
    "return_record": true
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "cust_003",
    "created": true,
    "record": {
      "id": "cust_003",
      "name": "New Tech Solutions",
      "email": "contact@newtech.com",
      "phone": "+1-555-0123",
      "industry": "Technology",
      "status": "active",
      "custom_field_1": "Enterprise",
      "custom_field_2": "Q1-2024",
      "created_at": "2024-01-15T14:22:00Z",
      "updated_at": "2024-01-15T14:22:00Z"
    }
  },
  "message": "Record created successfully"
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified object type does not exist |
| 400 | `VALIDATION_ERROR` | Data validation failed |
| 400 | `MISSING_REQUIRED_FIELD` | A required field is missing |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 409 | `DUPLICATE_RECORD` | A record with the same unique key already exists |
| 500 | `INSERT_ERROR` | Error inserting record on application server |

---

### Update Custom Object

Update an existing object/record via the custom application server.

```
PUT /custom/update
```

#### Description

Updates an existing object or record in the custom application server. Supports partial updates where only specified fields are modified.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | body | Yes | The object/entity type to update |
| `id` | string | body | Yes | The unique identifier of the record to update |
| `data` | object | body | Yes | The field values to update |
| `validate` | boolean | body | No | Whether to validate data before update (default: true) |
| `return_record` | boolean | body | No | Return the updated record in response (default: false) |

#### Request Example

```bash
curl -X PUT "https://api.example.com/custom/update" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "customers",
    "id": "cust_003",
    "data": {
      "phone": "+1-555-9999",
      "status": "premium",
      "custom_field_1": "Enterprise Plus"
    },
    "validate": true,
    "return_record": true
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "cust_003",
    "updated": true,
    "fields_modified": ["phone", "status", "custom_field_1"],
    "record": {
      "id": "cust_003",
      "name": "New Tech Solutions",
      "email": "contact@newtech.com",
      "phone": "+1-555-9999",
      "industry": "Technology",
      "status": "premium",
      "custom_field_1": "Enterprise Plus",
      "custom_field_2": "Q1-2024",
      "created_at": "2024-01-15T14:22:00Z",
      "updated_at": "2024-01-15T15:30:00Z"
    }
  },
  "message": "Record updated successfully"
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified object type does not exist |
| 400 | `VALIDATION_ERROR` | Data validation failed |
| 400 | `INVALID_FIELD` | One or more fields do not exist on the object |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 404 | `RECORD_NOT_FOUND` | No record found with the specified ID |
| 500 | `UPDATE_ERROR` | Error updating record on application server |

---

### Get Available Objects

Retrieve a list of available objects from the custom server.

```
GET /custom/objects
```

#### Description

Returns a list of all available object types (tables/entities) configured on the custom application server. This is useful for discovering the schema and available data structures.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `include_system` | boolean | query | No | Include system objects (default: false) |
| `category` | string | query | No | Filter objects by category |

#### Request Example

```bash
curl -X GET "https://api.example.com/custom/objects?include_system=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "objects": [
      {
        "name": "customers",
        "label": "Customers",
        "category": "core",
        "description": "Customer account records",
        "record_count": 15420,
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deleteable": true
      },
      {
        "name": "transactions",
        "label": "Transactions",
        "category": "financial",
        "description": "Financial transaction records",
        "record_count": 892340,
        "queryable": true,
        "createable": true,
        "updateable": false,
        "deleteable": false
      },
      {
        "name": "products",
        "label": "Products",
        "category": "inventory",
        "description": "Product catalog",
        "record_count": 3250,
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deleteable": true
      }
    ],
    "total_count": 3
  },
  "metadata": {
    "server_version": "2.4.1",
    "last_schema_update": "2024-01-10T00:00:00Z"
  }
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `FORBIDDEN` | Access to schema information is denied |
| 500 | `SERVER_ERROR` | Error retrieving object list from application server |

---

### Get Object Fields

Retrieve the list of fields for a specific table/object from the custom server.

```
GET /custom/fields
```

#### Description

Returns detailed field information for a specific object type, including field names, data types, constraints, and metadata. This is essential for understanding the data structure before querying or creating records.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | query | Yes | The object/entity type to get fields for |
| `include_readonly` | boolean | query | No | Include read-only/system fields (default: true) |
| `include_deprecated` | boolean | query | No | Include deprecated fields (default: false) |

#### Request Example

```bash
curl -X GET "https://api.example.com/custom/fields?object=customers&include_readonly=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "object": "customers",
    "fields": [
      {
        "name": "id",
        "label": "Customer ID",
        "type": "string",
        "length": 36,
        "required": true,
        "readonly": true,
        "primary_key": true,
        "description": "Unique customer identifier"
      },
      {
        "name": "name",
        "label": "Company Name",
        "type": "string",
        "length": 255,
        "required": true,
        "readonly": false,
        "primary_key": false,
        "description": "Customer company name"
      },
      {
        "name": "email",
        "label": "Email Address",
        "type": "email",
        "length": 255,
        "required": true,
        "readonly": false,
        "primary_key": false,
        "unique": true,
        "description": "Primary contact email"
      },
      {
        "name": "phone",
        "label": "Phone Number",
        "type": "phone",
        "length": 20,
        "required": false,
        "readonly": false,
        "primary_key": false,
        "description": "Primary contact phone"
      },
      {
        "name": "status",
        "label": "Account Status",
        "type": "picklist",
        "required": true,
        "readonly": false,
        "default_value": "active",
        "picklist_values": [
          {"value": "active", "label": "Active"},
          {"value": "inactive", "label": "Inactive"},
          {"value": "premium", "label": "Premium"},
          {"value": "suspended", "label": "Suspended"}
        ],
        "description": "Current account status"
      },
      {
        "name": "created_at",
        "label": "Created At",
        "type": "datetime",
        "required": false,
        "readonly": true,
        "description": "Record creation timestamp"
      },
      {
        "name": "updated_at",
        "label": "Updated At",
        "type": "datetime",
        "required": false,
        "readonly": true,
        "description": "Last update timestamp"
      }
    ],
    "field_count": 7
  },
  "metadata": {
    "object_label": "Customers",
    "last_modified": "2024-01-10T00:00:00Z"
  }
}
```

#### Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified object type does not exist |
| 401 | `UNAUTHORIZED` | Invalid or missing authentication token |
| 403 | `FORBIDDEN` | Access to schema information is denied |
| 500 | `SERVER_ERROR` | Error retrieving field list from application server |

---

## Field Types Reference

The custom data source supports the following field types:

| Type | Description | Example Value |
|------|-------------|---------------|
| `string` | Text string | `"Hello World"` |
| `integer` | Whole number | `42` |
| `decimal` | Decimal number | `99.95` |
| `boolean` | True/false | `true` |
| `date` | Date only | `"2024-01-15"` |
| `datetime` | Date and time | `"2024-01-15T14:30:00Z"` |
| `email` | Email address | `"user@example.com"` |
| `phone` | Phone number | `"+1-555-0123"` |
| `url` | Web URL | `"https://example.com"` |
| `picklist` | Enumerated values | `"active"` |
| `reference` | Foreign key reference | `"ref_12345"` |
| `blob` | Binary data | Base64 encoded string |

---

## Query Conditions Format

When using the `conditions` parameter in the query endpoint, use the following JSON format:

### Simple Equality

```json
{
  "status": "active"
}
```

### Operators

```json
{
  "field": "amount",
  "operator": "gt",
  "value": 1000
}
```

**Supported Operators:**

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal to | `{"field": "status", "operator": "eq", "value": "active"}` |
| `ne` | Not equal to | `{"field": "status", "operator": "ne", "value": "deleted"}` |
| `gt` | Greater than | `{"field": "amount", "operator": "gt", "value": 100}` |
| `gte` | Greater than or equal | `{"field": "amount", "operator": "gte", "value": 100}` |
| `lt` | Less than | `{"field": "amount", "operator": "lt", "value": 1000}` |
| `lte` | Less than or equal | `{"field": "amount", "operator": "lte", "value": 1000}` |
| `like` | Pattern match | `{"field": "name", "operator": "like", "value": "%Corp%"}` |
| `in` | In list | `{"field": "status", "operator": "in", "value": ["active", "premium"]}` |
| `between` | Between values | `{"field": "created_at", "operator": "between", "value": ["2024-01-01", "2024-12-31"]}` |

### Compound Conditions

```json
{
  "AND": [
    {"status": "active"},
    {"field": "amount", "operator": "gt", "value": 1000}
  ]
}
```

```json
{
  "OR": [
    {"status": "premium"},
    {"field": "amount", "operator": "gt", "value": 10000}
  ]
}
```