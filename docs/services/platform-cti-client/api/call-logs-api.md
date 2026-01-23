# Call Logs API

This document covers the endpoints for retrieving and managing call history in FreedomCTI.

## Overview

The Call Logs API provides access to call history data, enabling applications to retrieve detailed call records for users. This includes standard call logs, call reporting records, and missed call tracking.

## Endpoints

### Get User Call Logs (Chatter/Limited View)

Retrieves call logs for a specific user within an organization. This endpoint provides a condensed view suitable for Chatter feeds and limited display contexts.

```
GET /v1/organisation/{orgId}/user/{userId}/log/call
```

#### Description

Fetches call log entries for a specific user, returning summary information about recent calls. This endpoint is optimized for displaying call activity in Salesforce Chatter feeds and other limited-view contexts.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgId` | string | path | Yes | The organization identifier |
| `userId` | string | path | Yes | The user identifier |
| `limit` | integer | query | No | Maximum number of records to return (default: 50, max: 200) |
| `offset` | integer | query | No | Number of records to skip for pagination (default: 0) |
| `startDate` | string | query | No | Filter logs from this date (ISO 8601 format) |
| `endDate` | string | query | No | Filter logs until this date (ISO 8601 format) |
| `direction` | string | query | No | Filter by call direction: `inbound`, `outbound`, or `all` (default: `all`) |

#### Request Example

```bash
curl -X GET "https://api.freedomcti.com/v1/organisation/org_12345/user/user_67890/log/call?limit=25&direction=inbound&startDate=2024-01-01T00:00:00Z" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "callLogs": [
      {
        "id": "call_abc123",
        "direction": "inbound",
        "status": "completed",
        "duration": 245,
        "startTime": "2024-01-15T14:32:00Z",
        "endTime": "2024-01-15T14:36:05Z",
        "fromNumber": "+14155551234",
        "toNumber": "+14155555678",
        "callerName": "John Smith",
        "recordingAvailable": true,
        "disposition": "Answered",
        "notes": "Customer inquiry about billing"
      },
      {
        "id": "call_def456",
        "direction": "inbound",
        "status": "completed",
        "duration": 120,
        "startTime": "2024-01-15T10:15:00Z",
        "endTime": "2024-01-15T10:17:00Z",
        "fromNumber": "+14155559999",
        "toNumber": "+14155555678",
        "callerName": "Jane Doe",
        "recordingAvailable": false,
        "disposition": "Answered",
        "notes": null
      }
    ],
    "pagination": {
      "total": 156,
      "limit": 25,
      "offset": 0,
      "hasMore": true
    }
  }
}
```

#### Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_PARAMETERS` | Invalid query parameters provided |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | User does not have permission to access these logs |
| 404 | `USER_NOT_FOUND` | The specified user or organization does not exist |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests, please retry later |
| 500 | `INTERNAL_ERROR` | Internal server error |

---

### Fetch Call Reporting Records

Retrieves detailed call reporting records directly from Salesforce for a specific user.

```
GET /services/data/{REST_API_VERSION}/query
```

#### Description

Executes a SOQL query against Salesforce to fetch comprehensive call reporting records. This endpoint provides full call detail records (CDRs) with all associated Salesforce metadata.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `REST_API_VERSION` | string | path | Yes | Salesforce REST API version (e.g., `v58.0`) |
| `q` | string | query | Yes | SOQL query string to fetch call records |

#### Request Example

```bash
curl -X GET "https://yourinstance.salesforce.com/services/data/v58.0/query?q=SELECT+Id,CallType,CallDurationInSeconds,CallDisposition,CreatedDate,Description,Subject,WhoId,WhatId,OwnerId+FROM+Task+WHERE+OwnerId='005xx000001234'+AND+TaskSubtype='Call'+AND+CreatedDate>=2024-01-01T00:00:00Z+ORDER+BY+CreatedDate+DESC+LIMIT+100" \
  -H "Authorization: Bearer <salesforce_access_token>" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "totalSize": 42,
  "done": true,
  "records": [
    {
      "attributes": {
        "type": "Task",
        "url": "/services/data/v58.0/sobjects/Task/00Txx0000012345"
      },
      "Id": "00Txx0000012345",
      "CallType": "Inbound",
      "CallDurationInSeconds": 312,
      "CallDisposition": "Completed",
      "CreatedDate": "2024-01-15T14:32:00.000+0000",
      "Description": "Customer called regarding account upgrade options",
      "Subject": "Call with John Smith",
      "WhoId": "003xx0000045678",
      "WhatId": "001xx0000098765",
      "OwnerId": "005xx000001234"
    },
    {
      "attributes": {
        "type": "Task",
        "url": "/services/data/v58.0/sobjects/Task/00Txx0000012346"
      },
      "Id": "00Txx0000012346",
      "CallType": "Outbound",
      "CallDurationInSeconds": 180,
      "CallDisposition": "Completed",
      "CreatedDate": "2024-01-15T11:00:00.000+0000",
      "Description": "Follow-up call to discuss proposal",
      "Subject": "Outbound call to Acme Corp",
      "WhoId": "003xx0000045679",
      "WhatId": "006xx0000011111",
      "OwnerId": "005xx000001234"
    }
  ]
}
```

#### Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `MALFORMED_QUERY` | The SOQL query syntax is invalid |
| 401 | `INVALID_SESSION_ID` | Session expired or invalid |
| 403 | `INSUFFICIENT_ACCESS` | User lacks permission to query these records |
| 404 | `NOT_FOUND` | Invalid API version or resource |
| 414 | `URI_TOO_LONG` | Query string exceeds maximum length |
| 500 | `INTERNAL_ERROR` | Salesforce internal error |

---

### Fetch Missed Call Logs

Retrieves missed call phone events from Salesforce for a specific user.

```
GET /services/data/{REST_API_VERSION}/query
```

#### Description

Executes a SOQL query to fetch missed call events, including unanswered inbound calls and abandoned calls. This is essential for callback lists and missed opportunity tracking.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `REST_API_VERSION` | string | path | Yes | Salesforce REST API version (e.g., `v58.0`) |
| `q` | string | query | Yes | SOQL query string to fetch missed call records |

#### Request Example

```bash
curl -X GET "https://yourinstance.salesforce.com/services/data/v58.0/query?q=SELECT+Id,CallType,CreatedDate,Description,Subject,WhoId,Phone,CallDisposition+FROM+Task+WHERE+OwnerId='005xx000001234'+AND+TaskSubtype='Call'+AND+CallDisposition='No+Answer'+AND+CreatedDate>=2024-01-01T00:00:00Z+ORDER+BY+CreatedDate+DESC" \
  -H "Authorization: Bearer <salesforce_access_token>" \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "totalSize": 8,
  "done": true,
  "records": [
    {
      "attributes": {
        "type": "Task",
        "url": "/services/data/v58.0/sobjects/Task/00Txx0000012350"
      },
      "Id": "00Txx0000012350",
      "CallType": "Inbound",
      "CreatedDate": "2024-01-15T16:45:00.000+0000",
      "Description": "Missed inbound call",
      "Subject": "Missed Call from +14155551111",
      "WhoId": "003xx0000045680",
      "Phone": "+14155551111",
      "CallDisposition": "No Answer"
    },
    {
      "attributes": {
        "type": "Task",
        "url": "/services/data/v58.0/sobjects/Task/00Txx0000012351"
      },
      "Id": "00Txx0000012351",
      "CallType": "Inbound",
      "CreatedDate": "2024-01-15T09:20:00.000+0000",
      "Description": "Caller abandoned before answer",
      "Subject": "Missed Call from +14155552222",
      "WhoId": null,
      "Phone": "+14155552222",
      "CallDisposition": "Abandoned"
    }
  ]
}
```

#### Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `MALFORMED_QUERY` | The SOQL query syntax is invalid |
| 401 | `INVALID_SESSION_ID` | Session expired or invalid |
| 403 | `INSUFFICIENT_ACCESS` | User lacks permission to query these records |
| 404 | `NOT_FOUND` | Invalid API version or resource |
| 500 | `INTERNAL_ERROR` | Salesforce internal error |

---

## Common SOQL Query Patterns

### Fetch All Call Logs for a User (Last 30 Days)

```sql
SELECT Id, CallType, CallDurationInSeconds, CallDisposition, 
       CreatedDate, Description, Subject, WhoId, WhatId, OwnerId
FROM Task 
WHERE OwnerId = '005xx000001234' 
  AND TaskSubtype = 'Call' 
  AND CreatedDate >= LAST_N_DAYS:30
ORDER BY CreatedDate DESC
```

### Fetch Only Inbound Calls

```sql
SELECT Id, CallType, CallDurationInSeconds, CallDisposition, CreatedDate
FROM Task 
WHERE OwnerId = '005xx000001234' 
  AND TaskSubtype = 'Call' 
  AND CallType = 'Inbound'
ORDER BY CreatedDate DESC
```

### Fetch Calls with Recordings

```sql
SELECT Id, CallType, CallDurationInSeconds, CreatedDate, 
       FreedomCTI__Recording_URL__c
FROM Task 
WHERE OwnerId = '005xx000001234' 
  AND TaskSubtype = 'Call' 
  AND FreedomCTI__Recording_URL__c != null
ORDER BY CreatedDate DESC
```

---

## Related Documentation

- [Salesforce API](salesforce-api.md) - General Salesforce integration endpoints
- [WebSocket Endpoints](websocket-endpoints.md) - Real-time presence and event subscriptions
- [API Overview](README.md) - General API information and authentication