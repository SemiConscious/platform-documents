# Microsoft Dynamics API Endpoints

Complete reference for Microsoft Dynamics CRM operations through the Service Gateway.

## Overview

The Microsoft Dynamics API endpoints provide integration with Microsoft Dynamics 365 CRM, allowing you to query, create, and update records across all Dynamics entities. These endpoints support flexible querying with conditions, field selection, ordering, and pagination.

## Base URL

All Microsoft Dynamics endpoints are prefixed with `/msdynamics`.

## Authentication

All endpoints require authentication via the Service Gateway authentication system. Include your authentication token in the request headers or as configured for your integration.

---

## Endpoints

### Query Dynamics Data

Retrieve records from Microsoft Dynamics CRM with optional filtering, field selection, ordering, and pagination.

```
GET /msdynamics/query
```

#### Description

Query Microsoft Dynamics CRM data with flexible options for filtering by conditions, selecting specific fields, ordering results, and limiting the number of records returned. Supports all standard Dynamics entities including accounts, contacts, opportunities, leads, and custom entities.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | query | Yes | The Dynamics entity to query (e.g., `account`, `contact`, `opportunity`, `lead`) |
| `conditions` | string | query | No | Filter conditions in JSON format or query string format |
| `fields` | string | query | No | Comma-separated list of fields to return. If omitted, returns all fields |
| `orderby` | string | query | No | Field name to sort results by |
| `order` | string | query | No | Sort direction: `asc` or `desc` (default: `asc`) |
| `limit` | integer | query | No | Maximum number of records to return |
| `offset` | integer | query | No | Number of records to skip (for pagination) |

#### Request Example

```bash
# Query all active accounts
curl -X GET "https://api.example.com/msdynamics/query?object=account&conditions={\"statecode\":0}&fields=accountid,name,telephone1,emailaddress1&orderby=name&order=asc&limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Query contacts by account
curl -X GET "https://api.example.com/msdynamics/query?object=contact&conditions={\"parentcustomerid\":\"00000000-0000-0000-0000-000000000001\"}&fields=contactid,fullname,emailaddress1,telephone1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Query opportunities with multiple conditions
curl -X GET "https://api.example.com/msdynamics/query?object=opportunity&conditions={\"statecode\":0,\"estimatedvalue_gt\":10000}&orderby=estimatedclosedate&limit=100" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "count": 3,
  "data": [
    {
      "accountid": "00000000-0000-0000-0000-000000000001",
      "name": "Contoso Ltd",
      "telephone1": "+1-555-0100",
      "emailaddress1": "info@contoso.com",
      "statecode": 0,
      "createdon": "2024-01-15T10:30:00Z",
      "modifiedon": "2024-06-20T14:45:00Z"
    },
    {
      "accountid": "00000000-0000-0000-0000-000000000002",
      "name": "Fabrikam Inc",
      "telephone1": "+1-555-0200",
      "emailaddress1": "contact@fabrikam.com",
      "statecode": 0,
      "createdon": "2024-02-10T09:15:00Z",
      "modifiedon": "2024-06-18T11:20:00Z"
    },
    {
      "accountid": "00000000-0000-0000-0000-000000000003",
      "name": "Northwind Traders",
      "telephone1": "+1-555-0300",
      "emailaddress1": "sales@northwind.com",
      "statecode": 0,
      "createdon": "2024-03-05T16:00:00Z",
      "modifiedon": "2024-06-22T08:30:00Z"
    }
  ],
  "metadata": {
    "object": "account",
    "total_count": 3,
    "limit": 50,
    "offset": 0
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified entity/object type is invalid |
| 400 | `INVALID_CONDITIONS` | The conditions parameter is malformed |
| 400 | `INVALID_FIELD` | One or more specified fields do not exist |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 403 | `FORBIDDEN` | User lacks permission to query this entity |
| 404 | `ENTITY_NOT_FOUND` | The specified entity type does not exist in Dynamics |
| 500 | `DYNAMICS_ERROR` | Microsoft Dynamics returned an error |
| 503 | `SERVICE_UNAVAILABLE` | Unable to connect to Microsoft Dynamics |

---

### Get Metadata

Retrieve metadata about available Dynamics entities, fields, supported methods, and operators.

```
GET /msdynamics/meta
```

#### Description

Returns metadata information about the Microsoft Dynamics integration including available query methods, supported operators for conditions, list of accessible Dynamics entities, and field definitions in DTD/XML format. Useful for discovering available objects and building dynamic queries.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `type` | string | query | No | Type of metadata to return: `methods`, `operators`, `objects`, `fields`, or `all` (default: `all`) |
| `object` | string | query | No | When `type=fields`, specifies which entity to get field metadata for |
| `format` | string | query | No | Response format: `json`, `xml`, or `dtd` (default: `json`) |

#### Request Example

```bash
# Get all metadata
curl -X GET "https://api.example.com/msdynamics/meta" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Get list of available objects/entities
curl -X GET "https://api.example.com/msdynamics/meta?type=objects" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Get field definitions for Account entity
curl -X GET "https://api.example.com/msdynamics/meta?type=fields&object=account" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

```bash
# Get supported operators
curl -X GET "https://api.example.com/msdynamics/meta?type=operators" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "data": {
    "methods": [
      "query",
      "add",
      "update",
      "meta"
    ],
    "operators": [
      {
        "operator": "eq",
        "description": "Equal to",
        "example": "{\"field_eq\": \"value\"}"
      },
      {
        "operator": "ne",
        "description": "Not equal to",
        "example": "{\"field_ne\": \"value\"}"
      },
      {
        "operator": "gt",
        "description": "Greater than",
        "example": "{\"field_gt\": 100}"
      },
      {
        "operator": "lt",
        "description": "Less than",
        "example": "{\"field_lt\": 100}"
      },
      {
        "operator": "gte",
        "description": "Greater than or equal to",
        "example": "{\"field_gte\": 100}"
      },
      {
        "operator": "lte",
        "description": "Less than or equal to",
        "example": "{\"field_lte\": 100}"
      },
      {
        "operator": "like",
        "description": "Contains substring",
        "example": "{\"field_like\": \"%value%\"}"
      },
      {
        "operator": "in",
        "description": "In list of values",
        "example": "{\"field_in\": [\"val1\", \"val2\"]}"
      }
    ],
    "objects": [
      {
        "name": "account",
        "display_name": "Account",
        "description": "Business accounts and companies"
      },
      {
        "name": "contact",
        "display_name": "Contact",
        "description": "Individual contacts and people"
      },
      {
        "name": "opportunity",
        "display_name": "Opportunity",
        "description": "Sales opportunities"
      },
      {
        "name": "lead",
        "display_name": "Lead",
        "description": "Sales leads"
      },
      {
        "name": "incident",
        "display_name": "Case",
        "description": "Customer service cases"
      },
      {
        "name": "task",
        "display_name": "Task",
        "description": "Activity tasks"
      },
      {
        "name": "appointment",
        "display_name": "Appointment",
        "description": "Scheduled appointments"
      }
    ],
    "fieldlist": {
      "account": [
        {
          "name": "accountid",
          "type": "uniqueidentifier",
          "display_name": "Account ID",
          "required": false,
          "readonly": true
        },
        {
          "name": "name",
          "type": "string",
          "display_name": "Account Name",
          "required": true,
          "readonly": false,
          "max_length": 160
        },
        {
          "name": "emailaddress1",
          "type": "string",
          "display_name": "Email",
          "required": false,
          "readonly": false,
          "max_length": 100
        },
        {
          "name": "telephone1",
          "type": "string",
          "display_name": "Main Phone",
          "required": false,
          "readonly": false,
          "max_length": 50
        },
        {
          "name": "statecode",
          "type": "integer",
          "display_name": "Status",
          "required": false,
          "readonly": false,
          "options": [
            {"value": 0, "label": "Active"},
            {"value": 1, "label": "Inactive"}
          ]
        }
      ]
    }
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_TYPE` | The specified metadata type is invalid |
| 400 | `OBJECT_REQUIRED` | Object parameter required when type=fields |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 404 | `OBJECT_NOT_FOUND` | The specified object does not exist |
| 500 | `DYNAMICS_ERROR` | Microsoft Dynamics returned an error |
| 503 | `SERVICE_UNAVAILABLE` | Unable to connect to Microsoft Dynamics |

---

### Add Object

Create a new record in Microsoft Dynamics CRM.

```
POST /msdynamics/add
```

#### Description

Add a new object/record to Microsoft Dynamics CRM. Supports creation of any standard or custom entity including accounts, contacts, opportunities, leads, cases, and more. Returns the created record with its unique identifier.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | body | Yes | The Dynamics entity type to create (e.g., `account`, `contact`) |
| `data` | object | body | Yes | Field values for the new record |

#### Request Example

```bash
# Create a new account
curl -X POST "https://api.example.com/msdynamics/add" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "account",
    "data": {
      "name": "Acme Corporation",
      "telephone1": "+1-555-0123",
      "emailaddress1": "info@acme.com",
      "websiteurl": "https://www.acme.com",
      "address1_line1": "123 Business Ave",
      "address1_city": "Seattle",
      "address1_stateorprovince": "WA",
      "address1_postalcode": "98101",
      "address1_country": "USA",
      "industrycode": 6,
      "numberofemployees": 500
    }
  }'
```

```bash
# Create a new contact linked to an account
curl -X POST "https://api.example.com/msdynamics/add" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "contact",
    "data": {
      "firstname": "John",
      "lastname": "Smith",
      "emailaddress1": "john.smith@acme.com",
      "telephone1": "+1-555-0124",
      "jobtitle": "Sales Director",
      "parentcustomerid": "00000000-0000-0000-0000-000000000001"
    }
  }'
```

```bash
# Create a new opportunity
curl -X POST "https://api.example.com/msdynamics/add" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "opportunity",
    "data": {
      "name": "Enterprise Software License",
      "customerid": "00000000-0000-0000-0000-000000000001",
      "estimatedvalue": 75000.00,
      "estimatedclosedate": "2024-09-30",
      "description": "Annual enterprise license renewal",
      "opportunityratingcode": 1
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Record created successfully",
  "data": {
    "id": "00000000-0000-0000-0000-000000000099",
    "object": "account",
    "record": {
      "accountid": "00000000-0000-0000-0000-000000000099",
      "name": "Acme Corporation",
      "telephone1": "+1-555-0123",
      "emailaddress1": "info@acme.com",
      "websiteurl": "https://www.acme.com",
      "address1_line1": "123 Business Ave",
      "address1_city": "Seattle",
      "address1_stateorprovince": "WA",
      "address1_postalcode": "98101",
      "address1_country": "USA",
      "industrycode": 6,
      "numberofemployees": 500,
      "statecode": 0,
      "statuscode": 1,
      "createdon": "2024-06-25T10:30:00Z",
      "modifiedon": "2024-06-25T10:30:00Z"
    }
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified entity/object type is invalid |
| 400 | `MISSING_REQUIRED_FIELD` | A required field is missing from the data |
| 400 | `INVALID_FIELD_VALUE` | A field value is invalid or malformed |
| 400 | `INVALID_REFERENCE` | A lookup/reference field points to non-existent record |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 403 | `FORBIDDEN` | User lacks permission to create this entity |
| 409 | `DUPLICATE_RECORD` | A duplicate record already exists |
| 500 | `DYNAMICS_ERROR` | Microsoft Dynamics returned an error |
| 503 | `SERVICE_UNAVAILABLE` | Unable to connect to Microsoft Dynamics |

---

### Update Object

Update an existing record in Microsoft Dynamics CRM.

```
PUT /msdynamics/update
```

#### Description

Update an existing object/record in Microsoft Dynamics CRM. Specify the entity type, record ID, and the fields to update. Only provided fields will be modified; other fields remain unchanged.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `object` | string | body | Yes | The Dynamics entity type (e.g., `account`, `contact`) |
| `id` | string | body | Yes | The unique identifier (GUID) of the record to update |
| `data` | object | body | Yes | Field values to update |

#### Request Example

```bash
# Update an account
curl -X PUT "https://api.example.com/msdynamics/update" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "account",
    "id": "00000000-0000-0000-0000-000000000001",
    "data": {
      "telephone1": "+1-555-9999",
      "emailaddress1": "newemail@acme.com",
      "numberofemployees": 750,
      "revenue": 50000000.00
    }
  }'
```

```bash
# Update a contact
curl -X PUT "https://api.example.com/msdynamics/update" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "contact",
    "id": "00000000-0000-0000-0000-000000000002",
    "data": {
      "jobtitle": "VP of Sales",
      "telephone1": "+1-555-8888",
      "address1_line1": "456 Executive Blvd"
    }
  }'
```

```bash
# Update an opportunity status
curl -X PUT "https://api.example.com/msdynamics/update" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "opportunity",
    "id": "00000000-0000-0000-0000-000000000003",
    "data": {
      "estimatedvalue": 100000.00,
      "opportunityratingcode": 3,
      "description": "Updated scope to include additional modules"
    }
  }'
```

#### Response Example

```json
{
  "status": "success",
  "message": "Record updated successfully",
  "data": {
    "id": "00000000-0000-0000-0000-000000000001",
    "object": "account",
    "record": {
      "accountid": "00000000-0000-0000-0000-000000000001",
      "name": "Acme Corporation",
      "telephone1": "+1-555-9999",
      "emailaddress1": "newemail@acme.com",
      "numberofemployees": 750,
      "revenue": 50000000.00,
      "statecode": 0,
      "statuscode": 1,
      "createdon": "2024-01-15T10:30:00Z",
      "modifiedon": "2024-06-25T14:22:00Z"
    },
    "fields_updated": [
      "telephone1",
      "emailaddress1",
      "numberofemployees",
      "revenue"
    ]
  }
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_OBJECT` | The specified entity/object type is invalid |
| 400 | `MISSING_ID` | The record ID is missing |
| 400 | `INVALID_ID` | The record ID format is invalid |
| 400 | `INVALID_FIELD_VALUE` | A field value is invalid or malformed |
| 400 | `READONLY_FIELD` | Attempted to update a read-only field |
| 401 | `UNAUTHORIZED` | Authentication token is missing or invalid |
| 403 | `FORBIDDEN` | User lacks permission to update this record |
| 404 | `RECORD_NOT_FOUND` | No record found with the specified ID |
| 409 | `CONCURRENT_MODIFICATION` | Record was modified by another user |
| 500 | `DYNAMICS_ERROR` | Microsoft Dynamics returned an error |
| 503 | `SERVICE_UNAVAILABLE` | Unable to connect to Microsoft Dynamics |

---

## Common Dynamics Entities

| Entity Name | Display Name | Description |
|-------------|--------------|-------------|
| `account` | Account | Companies and organizations |
| `contact` | Contact | Individual people |
| `opportunity` | Opportunity | Potential sales |
| `lead` | Lead | Prospective customers |
| `incident` | Case | Customer service requests |
| `task` | Task | To-do items |
| `appointment` | Appointment | Scheduled meetings |
| `phonecall` | Phone Call | Phone call activities |
| `email` | Email | Email activities |
| `quote` | Quote | Sales quotes |
| `salesorder` | Order | Sales orders |
| `invoice` | Invoice | Customer invoices |
| `product` | Product | Product catalog items |

---

## Query Operators

Use these operators in condition strings to filter query results:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` (default) | Equal to | `{"statecode": 0}` or `{"statecode_eq": 0}` |
| `ne` | Not equal to | `{"statecode_ne": 1}` |
| `gt` | Greater than | `{"revenue_gt": 100000}` |
| `lt` | Less than | `{"revenue_lt": 50000}` |
| `gte` | Greater than or equal | `{"createdon_gte": "2024-01-01"}` |
| `lte` | Less than or equal | `{"modifiedon_lte": "2024-06-30"}` |
| `like` | Contains (wildcard) | `{"name_like": "%Corp%"}` |
| `in` | In list | `{"industrycode_in": [1, 2, 3]}` |
| `null` | Is null | `{"emailaddress1_null": true}` |
| `notnull` | Is not null | `{"telephone1_notnull": true}` |

---

## Related Documentation

- [Generic API Endpoints](generic-endpoints.md) - Token-based queries via `/sgapi/` routes
- [API Response Models](../models/api-response-models.md) - Standard response formats
- [API Overview](README.md) - General API information