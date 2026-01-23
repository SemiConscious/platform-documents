# Salesforce API Endpoints

This document covers the Salesforce integration endpoints available through the Platform Service Gateway. These endpoints enable querying Salesforce data using SOQL/SOSL, managing records, and handling Salesforce-specific operations.

## Overview

The Service Gateway provides Salesforce integration through the SGAPI controller system. Salesforce operations are accessed using authentication tokens and feed IDs that identify the Salesforce connection configuration.

### Base URL Pattern

All Salesforce-specific operations use the SGAPI controller endpoints with Salesforce-configured feeds:

```
/sgapi/{operation}/{token}/{feedid}
```

### Authentication

Salesforce endpoints require:
1. A valid authentication token obtained via `/sgapi_auth/auth`
2. A feed ID configured for Salesforce integration

## Endpoints

### Query Salesforce Data

Query Salesforce objects with structured parameters.

```
GET /sgapi/query/{token}/{feedid}
```

#### Description

Queries Salesforce objects (Accounts, Contacts, Leads, Opportunities, etc.) using structured query parameters. Supports field selection, conditions, ordering, and pagination.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object` | string | Yes | Salesforce object name (e.g., `Account`, `Contact`, `Lead`) |
| `fields` | string | No | Comma-separated list of fields to return |
| `conditions` | string | No | JSON-encoded filter conditions |
| `orderby` | string | No | Field name to sort by |
| `order` | string | No | Sort direction: `ASC` or `DESC` |
| `limit` | integer | No | Maximum number of records to return |
| `offset` | integer | No | Number of records to skip |

#### Request Example

```bash
# Query Salesforce Contacts with specific fields and conditions
curl -X GET "https://gateway.example.com/sgapi/query/abc123token/salesforce_feed?object=Contact&fields=Id,FirstName,LastName,Email,Phone&conditions=%7B%22Email%22:%7B%22operator%22:%22!%3D%22,%22value%22:%22null%22%7D%7D&orderby=LastName&order=ASC&limit=50" \
  -H "Accept: application/json"
```

```bash
# Query Salesforce Opportunities
curl -X GET "https://gateway.example.com/sgapi/query/abc123token/salesforce_feed?object=Opportunity&fields=Id,Name,Amount,StageName,CloseDate&conditions=%7B%22StageName%22:%7B%22operator%22:%22%3D%22,%22value%22:%22Prospecting%22%7D%7D&limit=100" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "totalSize": 2,
    "done": true,
    "records": [
      {
        "Id": "003xx000004TmiAAAS",
        "FirstName": "John",
        "LastName": "Anderson",
        "Email": "john.anderson@example.com",
        "Phone": "+1-555-0101"
      },
      {
        "Id": "003xx000004TmiBBBS",
        "FirstName": "Sarah",
        "LastName": "Baker",
        "Email": "sarah.baker@example.com",
        "Phone": "+1-555-0102"
      }
    ]
  },
  "metadata": {
    "object": "Contact",
    "queryTime": "0.234s"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid query parameters or malformed conditions |
| `401` | Invalid or expired token |
| `403` | Insufficient permissions for the requested object |
| `404` | Feed ID not found or not configured for Salesforce |
| `500` | Salesforce API error or connection failure |

---

### Execute Raw SOQL/SOSL Query

Execute raw Salesforce queries using SOQL or SOSL syntax.

```
GET /sgapi/queryraw/{token}/{feedid}
```

#### Description

Executes raw SOQL (Salesforce Object Query Language) or SOSL (Salesforce Object Search Language) queries directly against Salesforce. This provides full flexibility for complex queries, relationships, and aggregate functions.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | URL-encoded SOQL or SOSL query string |
| `type` | string | No | Query type: `soql` (default) or `sosl` |

#### Request Example

```bash
# Execute SOQL query with relationship
curl -X GET "https://gateway.example.com/sgapi/queryraw/abc123token/salesforce_feed?query=SELECT%20Id%2C%20Name%2C%20Account.Name%2C%20Email%20FROM%20Contact%20WHERE%20Account.Industry%20%3D%20%27Technology%27%20LIMIT%2050" \
  -H "Accept: application/json"
```

```bash
# Execute SOSL search query
curl -X GET "https://gateway.example.com/sgapi/queryraw/abc123token/salesforce_feed?query=FIND%20%7BJohn%2A%7D%20IN%20ALL%20FIELDS%20RETURNING%20Contact(Id%2C%20Name%2C%20Email)&type=sosl" \
  -H "Accept: application/json"
```

```bash
# Execute aggregate SOQL query
curl -X GET "https://gateway.example.com/sgapi/queryraw/abc123token/salesforce_feed?query=SELECT%20StageName%2C%20COUNT(Id)%20FROM%20Opportunity%20GROUP%20BY%20StageName" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "totalSize": 3,
    "done": true,
    "records": [
      {
        "Id": "003xx000004TmiAAAS",
        "Name": "John Smith",
        "Account": {
          "Name": "Acme Technology Inc"
        },
        "Email": "john.smith@acme.com"
      },
      {
        "Id": "003xx000004TmiBBBS",
        "Name": "Jane Doe",
        "Account": {
          "Name": "Tech Solutions Ltd"
        },
        "Email": "jane.doe@techsolutions.com"
      },
      {
        "Id": "003xx000004TmiCCCS",
        "Name": "Bob Wilson",
        "Account": {
          "Name": "Digital Innovations Corp"
        },
        "Email": "bob.wilson@digitalinnovations.com"
      }
    ]
  },
  "metadata": {
    "queryType": "soql",
    "queryTime": "0.312s"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid SOQL/SOSL syntax or malformed query |
| `401` | Invalid or expired token |
| `403` | Query references objects or fields without access |
| `404` | Feed ID not found |
| `500` | Salesforce API error |

---

### Add Salesforce Record

Create a new record in Salesforce.

```
POST /sgapi/add/{token}/{feedid}
```

#### Description

Creates a new record in a specified Salesforce object. Supports all standard and custom Salesforce objects that the authenticated user has create access to.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object` | string | Yes | Salesforce object API name |
| `data` | object | Yes | Field-value pairs for the new record |

#### Request Example

```bash
# Create a new Contact
curl -X POST "https://gateway.example.com/sgapi/add/abc123token/salesforce_feed" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "object": "Contact",
    "data": {
      "FirstName": "Michael",
      "LastName": "Johnson",
      "Email": "michael.johnson@example.com",
      "Phone": "+1-555-0150",
      "AccountId": "001xx000003DGbYAAW",
      "Title": "Senior Developer",
      "Department": "Engineering"
    }
  }'
```

```bash
# Create a new Opportunity
curl -X POST "https://gateway.example.com/sgapi/add/abc123token/salesforce_feed" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "object": "Opportunity",
    "data": {
      "Name": "Enterprise License Deal",
      "AccountId": "001xx000003DGbYAAW",
      "Amount": 50000,
      "StageName": "Prospecting",
      "CloseDate": "2024-06-30",
      "Type": "New Business"
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "003xx000004TmiDDDS",
    "success": true,
    "errors": []
  },
  "message": "Record created successfully",
  "metadata": {
    "object": "Contact",
    "operation": "insert"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Missing required fields or invalid field values |
| `401` | Invalid or expired token |
| `403` | Insufficient permissions to create records |
| `404` | Feed ID not found or invalid object name |
| `409` | Duplicate record violation |
| `500` | Salesforce API error |

---

### Update Salesforce Record

Update an existing record in Salesforce.

```
PUT /sgapi/add/{token}/{feedid}
```

#### Description

Updates an existing record in Salesforce. The record ID must be provided along with the fields to update. Only the specified fields will be modified.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object` | string | Yes | Salesforce object API name |
| `id` | string | Yes | Salesforce record ID to update |
| `data` | object | Yes | Field-value pairs to update |

#### Request Example

```bash
# Update a Contact record
curl -X PUT "https://gateway.example.com/sgapi/add/abc123token/salesforce_feed" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "object": "Contact",
    "id": "003xx000004TmiDDDS",
    "data": {
      "Phone": "+1-555-0199",
      "Title": "Lead Developer",
      "Department": "Product Engineering"
    }
  }'
```

```bash
# Update Opportunity stage
curl -X PUT "https://gateway.example.com/sgapi/add/abc123token/salesforce_feed" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "object": "Opportunity",
    "id": "006xx000004TmiEEES",
    "data": {
      "StageName": "Qualification",
      "Amount": 75000,
      "NextStep": "Schedule demo with technical team"
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "003xx000004TmiDDDS",
    "success": true,
    "errors": []
  },
  "message": "Record updated successfully",
  "metadata": {
    "object": "Contact",
    "operation": "update"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid field values or malformed request |
| `401` | Invalid or expired token |
| `403` | Insufficient permissions to update record |
| `404` | Record ID not found or feed not configured |
| `409` | Concurrent modification conflict |
| `500` | Salesforce API error |

---

### Delete Salesforce Record

Delete a record from Salesforce.

```
DELETE /sgapi/deleterecord/{token}/{feedid}
```

#### Description

Permanently deletes a record from Salesforce. This operation cannot be undone through the API (records go to Salesforce Recycle Bin based on org settings).

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object` | string | Yes | Salesforce object API name |
| `id` | string | Yes | Salesforce record ID to delete |

#### Request Example

```bash
# Delete a Contact record
curl -X DELETE "https://gateway.example.com/sgapi/deleterecord/abc123token/salesforce_feed?object=Contact&id=003xx000004TmiDDDS" \
  -H "Accept: application/json"
```

```bash
# Delete a Task record
curl -X DELETE "https://gateway.example.com/sgapi/deleterecord/abc123token/salesforce_feed?object=Task&id=00Txx000003ABCD" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "003xx000004TmiDDDS",
    "deleted": true
  },
  "message": "Record deleted successfully",
  "metadata": {
    "object": "Contact",
    "operation": "delete"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Missing required parameters |
| `401` | Invalid or expired token |
| `403` | Insufficient permissions to delete record |
| `404` | Record ID not found |
| `409` | Record cannot be deleted due to dependencies |
| `500` | Salesforce API error |

---

### Get Salesforce Metadata

Retrieve metadata about available Salesforce objects and fields.

```
GET /sgapi/metaquery/{token}/{feedid}
```

#### Description

Returns metadata information about the Salesforce organization including available objects, fields, operators, and API methods. Useful for building dynamic queries and forms.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | Yes | Metadata type: `methodlist`, `operatorlist`, `objectlist`, or `fieldlist` |
| `object` | string | Conditional | Required when `type=fieldlist` - the object to get fields for |

#### Request Example

```bash
# Get list of available Salesforce objects
curl -X GET "https://gateway.example.com/sgapi/metaquery/abc123token/salesforce_feed?type=objectlist" \
  -H "Accept: application/json"
```

```bash
# Get fields for Contact object
curl -X GET "https://gateway.example.com/sgapi/metaquery/abc123token/salesforce_feed?type=fieldlist&object=Contact" \
  -H "Accept: application/json"
```

```bash
# Get available operators for queries
curl -X GET "https://gateway.example.com/sgapi/metaquery/abc123token/salesforce_feed?type=operatorlist" \
  -H "Accept: application/json"
```

#### Response Example (Object List)

```json
{
  "success": true,
  "data": {
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
        "name": "Opportunity",
        "label": "Opportunity",
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
      },
      {
        "name": "Task",
        "label": "Task",
        "queryable": true,
        "createable": true,
        "updateable": true,
        "deletable": true
      }
    ]
  },
  "metadata": {
    "type": "objectlist",
    "count": 5
  }
}
```

#### Response Example (Field List)

```json
{
  "success": true,
  "data": {
    "object": "Contact",
    "fields": [
      {
        "name": "Id",
        "label": "Contact ID",
        "type": "id",
        "required": false,
        "createable": false,
        "updateable": false
      },
      {
        "name": "FirstName",
        "label": "First Name",
        "type": "string",
        "required": false,
        "createable": true,
        "updateable": true,
        "length": 40
      },
      {
        "name": "LastName",
        "label": "Last Name",
        "type": "string",
        "required": true,
        "createable": true,
        "updateable": true,
        "length": 80
      },
      {
        "name": "Email",
        "label": "Email",
        "type": "email",
        "required": false,
        "createable": true,
        "updateable": true
      },
      {
        "name": "AccountId",
        "label": "Account ID",
        "type": "reference",
        "required": false,
        "createable": true,
        "updateable": true,
        "referenceTo": ["Account"]
      }
    ]
  },
  "metadata": {
    "type": "fieldlist",
    "object": "Contact",
    "fieldCount": 5
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid metadata type or missing object parameter |
| `401` | Invalid or expired token |
| `404` | Feed ID not found or object not found |
| `500` | Salesforce API error |

---

### Update Metadata Cache

Refresh the locally cached Salesforce metadata.

```
GET /sgapi/updatemetadata/{token}/{feedid}
```

#### Description

Forces a refresh of the cached Salesforce metadata. Use this when Salesforce schema changes (new custom fields, objects) need to be reflected in the gateway.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Request Example

```bash
curl -X GET "https://gateway.example.com/sgapi/updatemetadata/abc123token/salesforce_feed" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "message": "Metadata updated successfully",
  "data": {
    "objectsUpdated": 47,
    "lastUpdated": "2024-01-15T14:32:00Z"
  },
  "metadata": {
    "cacheRefreshed": true
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `401` | Invalid or expired token |
| `404` | Feed ID not found |
| `500` | Failed to retrieve metadata from Salesforce |

---

### Execute Custom Salesforce API Call

Execute custom Salesforce REST API calls.

```
POST /sgapi/custom_call/{token}/{feedid}
```

#### Description

Executes custom Salesforce REST API calls for operations not covered by standard endpoints. Supports any valid Salesforce REST API endpoint.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |
| `feedid` | string | Yes | Feed ID configured for Salesforce |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `endpoint` | string | Yes | Salesforce REST API endpoint path |
| `method` | string | Yes | HTTP method: `GET`, `POST`, `PATCH`, `DELETE` |
| `body` | object | No | Request body for POST/PATCH requests |
| `headers` | object | No | Additional headers to include |

#### Request Example

```bash
# Get current user info
curl -X POST "https://gateway.example.com/sgapi/custom_call/abc123token/salesforce_feed" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "endpoint": "/services/data/v58.0/chatter/users/me",
    "method": "GET"
  }'
```

```bash
# Create a composite request
curl -X POST "https://gateway.example.com/sgapi/custom_call/abc123token/salesforce_feed" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "endpoint": "/services/data/v58.0/composite",
    "method": "POST",
    "body": {
      "allOrNone": true,
      "compositeRequest": [
        {
          "method": "POST",
          "url": "/services/data/v58.0/sobjects/Account",
          "referenceId": "newAccount",
          "body": {
            "Name": "New Account from Composite"
          }
        },
        {
          "method": "POST",
          "url": "/services/data/v58.0/sobjects/Contact",
          "referenceId": "newContact",
          "body": {
            "LastName": "Smith",
            "AccountId": "@{newAccount.id}"
          }
        }
      ]
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "compositeResponse": [
      {
        "body": {
          "id": "001xx000003NEWFFF",
          "success": true,
          "errors": []
        },
        "httpHeaders": {},
        "httpStatusCode": 201,
        "referenceId": "newAccount"
      },
      {
        "body": {
          "id": "003xx000004NEWGGG",
          "success": true,
          "errors": []
        },
        "httpHeaders": {},
        "httpStatusCode": 201,
        "referenceId": "newContact"
      }
    ]
  },
  "metadata": {
    "endpoint": "/services/data/v58.0/composite",
    "method": "POST"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Invalid endpoint or malformed request body |
| `401` | Invalid or expired token |
| `403` | Insufficient permissions for the API endpoint |
| `404` | Feed ID not found or Salesforce endpoint not found |
| `500` | Salesforce API error |

---

### Add Task Activity

Add an activity to a Salesforce task.

```
PUT /sgapi_tasks/task/{token}
```

#### Description

Adds activity information to a Salesforce Task record. This endpoint is specifically designed for task management and activity tracking workflows.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Authentication token from sgapi_auth |

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `feedid` | string | Yes | Feed ID configured for Salesforce |
| `taskId` | string | Yes | Salesforce Task record ID |
| `activity` | object | Yes | Activity details to add |
| `activity.type` | string | Yes | Activity type (e.g., `Call`, `Email`, `Meeting`) |
| `activity.subject` | string | Yes | Activity subject line |
| `activity.description` | string | No | Detailed description of the activity |
| `activity.status` | string | No | Task status update |
| `activity.priority` | string | No | Task priority: `High`, `Normal`, `Low` |

#### Request Example

```bash
curl -X PUT "https://gateway.example.com/sgapi_tasks/task/abc123token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "feedid": "salesforce_feed",
    "taskId": "00Txx000003ABCDEF",
    "activity": {
      "type": "Call",
      "subject": "Follow-up call completed",
      "description": "Discussed product requirements and pricing. Customer requested proposal by Friday.",
      "status": "In Progress",
      "priority": "High"
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "taskId": "00Txx000003ABCDEF",
    "activityAdded": true,
    "updatedFields": ["Description", "Status", "Priority"]
  },
  "message": "Task activity added successfully",
  "metadata": {
    "activityType": "Call",
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| `400` | Missing required fields or invalid activity data |
| `401` | Invalid or expired token |
| `403` | Insufficient permissions to update task |
| `404` | Task ID not found |
| `500` | Salesforce API error |

---

## Common Salesforce Objects

The following standard Salesforce objects are commonly accessed through these endpoints:

| Object | Description |
|--------|-------------|
| `Account` | Business accounts and organizations |
| `Contact` | Individual people associated with accounts |
| `Lead` | Potential customers not yet qualified |
| `Opportunity` | Sales deals and revenue tracking |
| `Task` | To-do items and activities |
| `Event` | Calendar events and meetings |
| `Case` | Customer support cases |
| `Campaign` | Marketing campaigns |
| `User` | Salesforce users |

## SOQL Query Examples

### Basic Query
```sql
SELECT Id, Name, Email FROM Contact WHERE AccountId = '001xx000003DGbY'
```

### Query with Relationship
```sql
SELECT Id, Name, Account.Name, Account.Industry 
FROM Contact 
WHERE Account.Industry = 'Technology'
```

### Aggregate Query
```sql
SELECT StageName, COUNT(Id), SUM(Amount) 
FROM Opportunity 
GROUP BY StageName
```

### Date Filter
```sql
SELECT Id, Name, CreatedDate 
FROM Lead 
WHERE CreatedDate = LAST_N_DAYS:30
```

## Related Documentation

- [Authentication Endpoints](./generic-endpoints.md) - Token management
- [Feed Management](./feed-endpoints.md) - Feed configuration
- [API Response Models](../models/api-response-models.md) - Response structures