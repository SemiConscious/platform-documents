# Salesforce REST API Integration

This document covers the Salesforce REST API endpoints used by the FreedomCTI client for querying call data directly from Salesforce objects. These endpoints use Salesforce's standard SOQL query interface to retrieve call reporting and missed call records.

## Overview

The CTI client integrates with Salesforce's REST API to fetch call-related data stored in Salesforce custom objects. These queries are executed against the authenticated user's Salesforce org and respect all Salesforce security and sharing settings.

### Base URL

```
https://{instance}.salesforce.com/services/data/{REST_API_VERSION}/query
```

Where:
- `{instance}` is your Salesforce instance (e.g., `na1`, `eu5`, `ap2`)
- `{REST_API_VERSION}` is the Salesforce API version (e.g., `v58.0`, `v59.0`)

### Authentication

All Salesforce REST API calls require OAuth 2.0 authentication. Include the access token in the Authorization header:

```
Authorization: Bearer {access_token}
```

---

## Endpoints

### Fetch Call Reporting Records

Retrieves call reporting records from Salesforce for a specific user. This endpoint queries the custom call reporting object to return detailed call history data.

```
GET /services/data/{REST_API_VERSION}/query
```

#### Description

Fetches call logs stored in Salesforce's call reporting custom object. The query filters results by the specified user ID and returns comprehensive call details including duration, direction, timestamps, and associated records.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `REST_API_VERSION` | string | path | Yes | Salesforce REST API version (e.g., `v58.0`) |
| `q` | string | query | Yes | URL-encoded SOQL query string |

#### SOQL Query Structure

The `q` parameter contains a SOQL query targeting the call reporting object:

```sql
SELECT Id, Name, freedomcti__Call_Direction__c, freedomcti__Call_Duration__c,
       freedomcti__Call_Start_Time__c, freedomcti__Call_End_Time__c,
       freedomcti__Phone_Number__c, freedomcti__Contact__c, freedomcti__Lead__c,
       freedomcti__Account__c, freedomcti__User__c, freedomcti__Call_Recording_URL__c,
       freedomcti__Call_Notes__c, freedomcti__Call_Outcome__c, CreatedDate
FROM freedomcti__Call_Report__c
WHERE freedomcti__User__c = '{userId}'
ORDER BY freedomcti__Call_Start_Time__c DESC
LIMIT 100
```

#### Request Example

```bash
curl -X GET \
  "https://na1.salesforce.com/services/data/v58.0/query?q=SELECT+Id,Name,freedomcti__Call_Direction__c,freedomcti__Call_Duration__c,freedomcti__Call_Start_Time__c,freedomcti__Call_End_Time__c,freedomcti__Phone_Number__c,freedomcti__Contact__c,freedomcti__Lead__c,freedomcti__Account__c,freedomcti__User__c,freedomcti__Call_Recording_URL__c,freedomcti__Call_Notes__c,freedomcti__Call_Outcome__c,CreatedDate+FROM+freedomcti__Call_Report__c+WHERE+freedomcti__User__c='005xx000001Sv6AAAS'+ORDER+BY+freedomcti__Call_Start_Time__c+DESC+LIMIT+100" \
  -H "Authorization: Bearer 00Dxx0000001gPL!AR8AQJXg..." \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "totalSize": 3,
  "done": true,
  "records": [
    {
      "attributes": {
        "type": "freedomcti__Call_Report__c",
        "url": "/services/data/v58.0/sobjects/freedomcti__Call_Report__c/a0Bxx0000001234AAA"
      },
      "Id": "a0Bxx0000001234AAA",
      "Name": "CR-00001234",
      "freedomcti__Call_Direction__c": "Outbound",
      "freedomcti__Call_Duration__c": 245,
      "freedomcti__Call_Start_Time__c": "2024-01-15T14:30:00.000+0000",
      "freedomcti__Call_End_Time__c": "2024-01-15T14:34:05.000+0000",
      "freedomcti__Phone_Number__c": "+1-555-123-4567",
      "freedomcti__Contact__c": "003xx000001a2b3AAA",
      "freedomcti__Lead__c": null,
      "freedomcti__Account__c": "001xx000001x2y3AAA",
      "freedomcti__User__c": "005xx000001Sv6AAAS",
      "freedomcti__Call_Recording_URL__c": "https://recordings.freedomcti.com/rec/abc123",
      "freedomcti__Call_Notes__c": "Discussed product demo scheduling",
      "freedomcti__Call_Outcome__c": "Successful",
      "CreatedDate": "2024-01-15T14:34:10.000+0000"
    },
    {
      "attributes": {
        "type": "freedomcti__Call_Report__c",
        "url": "/services/data/v58.0/sobjects/freedomcti__Call_Report__c/a0Bxx0000001235AAA"
      },
      "Id": "a0Bxx0000001235AAA",
      "Name": "CR-00001235",
      "freedomcti__Call_Direction__c": "Inbound",
      "freedomcti__Call_Duration__c": 180,
      "freedomcti__Call_Start_Time__c": "2024-01-15T10:15:00.000+0000",
      "freedomcti__Call_End_Time__c": "2024-01-15T10:18:00.000+0000",
      "freedomcti__Phone_Number__c": "+1-555-987-6543",
      "freedomcti__Contact__c": "003xx000001c4d5AAA",
      "freedomcti__Lead__c": null,
      "freedomcti__Account__c": "001xx000001y3z4AAA",
      "freedomcti__User__c": "005xx000001Sv6AAAS",
      "freedomcti__Call_Recording_URL__c": "https://recordings.freedomcti.com/rec/def456",
      "freedomcti__Call_Notes__c": "Support inquiry - resolved",
      "freedomcti__Call_Outcome__c": "Successful",
      "CreatedDate": "2024-01-15T10:18:05.000+0000"
    },
    {
      "attributes": {
        "type": "freedomcti__Call_Report__c",
        "url": "/services/data/v58.0/sobjects/freedomcti__Call_Report__c/a0Bxx0000001236AAA"
      },
      "Id": "a0Bxx0000001236AAA",
      "Name": "CR-00001236",
      "freedomcti__Call_Direction__c": "Outbound",
      "freedomcti__Call_Duration__c": 0,
      "freedomcti__Call_Start_Time__c": "2024-01-14T16:45:00.000+0000",
      "freedomcti__Call_End_Time__c": "2024-01-14T16:45:30.000+0000",
      "freedomcti__Phone_Number__c": "+1-555-222-3333",
      "freedomcti__Contact__c": null,
      "freedomcti__Lead__c": "00Qxx000001e5f6AAA",
      "freedomcti__Account__c": null,
      "freedomcti__User__c": "005xx000001Sv6AAAS",
      "freedomcti__Call_Recording_URL__c": null,
      "freedomcti__Call_Notes__c": null,
      "freedomcti__Call_Outcome__c": "No Answer",
      "CreatedDate": "2024-01-14T16:45:35.000+0000"
    }
  ]
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `MALFORMED_QUERY` | The SOQL query syntax is invalid |
| `401` | `INVALID_SESSION_ID` | The access token is invalid or expired |
| `403` | `INSUFFICIENT_ACCESS` | User lacks permission to query this object |
| `404` | `NOT_FOUND` | The requested API version or object doesn't exist |
| `500` | `INTERNAL_ERROR` | Salesforce server error |

---

### Fetch Missed Call Phone Events

Retrieves missed call events from Salesforce for a specific user. This endpoint queries phone event records to return calls that were not answered.

```
GET /services/data/{REST_API_VERSION}/query
```

#### Description

Fetches missed call records from Salesforce's phone event object. These records represent inbound calls that were not answered by the user, providing visibility into potentially missed opportunities.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `REST_API_VERSION` | string | path | Yes | Salesforce REST API version (e.g., `v58.0`) |
| `q` | string | query | Yes | URL-encoded SOQL query string |

#### SOQL Query Structure

The `q` parameter contains a SOQL query targeting the phone event object:

```sql
SELECT Id, Name, freedomcti__Event_Type__c, freedomcti__Event_Time__c,
       freedomcti__Phone_Number__c, freedomcti__Caller_Name__c,
       freedomcti__Contact__c, freedomcti__Lead__c, freedomcti__Account__c,
       freedomcti__User__c, freedomcti__Queue_Name__c, freedomcti__Ring_Duration__c,
       freedomcti__Callback_Completed__c, CreatedDate
FROM freedomcti__Phone_Event__c
WHERE freedomcti__User__c = '{userId}'
  AND freedomcti__Event_Type__c = 'Missed Call'
ORDER BY freedomcti__Event_Time__c DESC
LIMIT 50
```

#### Request Example

```bash
curl -X GET \
  "https://na1.salesforce.com/services/data/v58.0/query?q=SELECT+Id,Name,freedomcti__Event_Type__c,freedomcti__Event_Time__c,freedomcti__Phone_Number__c,freedomcti__Caller_Name__c,freedomcti__Contact__c,freedomcti__Lead__c,freedomcti__Account__c,freedomcti__User__c,freedomcti__Queue_Name__c,freedomcti__Ring_Duration__c,freedomcti__Callback_Completed__c,CreatedDate+FROM+freedomcti__Phone_Event__c+WHERE+freedomcti__User__c='005xx000001Sv6AAAS'+AND+freedomcti__Event_Type__c='Missed+Call'+ORDER+BY+freedomcti__Event_Time__c+DESC+LIMIT+50" \
  -H "Authorization: Bearer 00Dxx0000001gPL!AR8AQJXg..." \
  -H "Content-Type: application/json"
```

#### Response Example

```json
{
  "totalSize": 2,
  "done": true,
  "records": [
    {
      "attributes": {
        "type": "freedomcti__Phone_Event__c",
        "url": "/services/data/v58.0/sobjects/freedomcti__Phone_Event__c/a0Cxx0000002345AAA"
      },
      "Id": "a0Cxx0000002345AAA",
      "Name": "PE-00002345",
      "freedomcti__Event_Type__c": "Missed Call",
      "freedomcti__Event_Time__c": "2024-01-15T11:22:00.000+0000",
      "freedomcti__Phone_Number__c": "+1-555-444-5555",
      "freedomcti__Caller_Name__c": "John Smith",
      "freedomcti__Contact__c": "003xx000001f6g7AAA",
      "freedomcti__Lead__c": null,
      "freedomcti__Account__c": "001xx000001z4a5AAA",
      "freedomcti__User__c": "005xx000001Sv6AAAS",
      "freedomcti__Queue_Name__c": "Sales Queue",
      "freedomcti__Ring_Duration__c": 25,
      "freedomcti__Callback_Completed__c": false,
      "CreatedDate": "2024-01-15T11:22:30.000+0000"
    },
    {
      "attributes": {
        "type": "freedomcti__Phone_Event__c",
        "url": "/services/data/v58.0/sobjects/freedomcti__Phone_Event__c/a0Cxx0000002346AAA"
      },
      "Id": "a0Cxx0000002346AAA",
      "Name": "PE-00002346",
      "freedomcti__Event_Type__c": "Missed Call",
      "freedomcti__Event_Time__c": "2024-01-14T09:05:00.000+0000",
      "freedomcti__Phone_Number__c": "+1-555-666-7777",
      "freedomcti__Caller_Name__c": null,
      "freedomcti__Contact__c": null,
      "freedomcti__Lead__c": null,
      "freedomcti__Account__c": null,
      "freedomcti__User__c": "005xx000001Sv6AAAS",
      "freedomcti__Queue_Name__c": "Support Queue",
      "freedomcti__Ring_Duration__c": 30,
      "freedomcti__Callback_Completed__c": true,
      "CreatedDate": "2024-01-14T09:05:35.000+0000"
    }
  ]
}
```

#### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `MALFORMED_QUERY` | The SOQL query syntax is invalid |
| `401` | `INVALID_SESSION_ID` | The access token is invalid or expired |
| `403` | `INSUFFICIENT_ACCESS` | User lacks permission to query this object |
| `404` | `NOT_FOUND` | The requested API version or object doesn't exist |
| `429` | `REQUEST_LIMIT_EXCEEDED` | API request limits have been exceeded |
| `500` | `INTERNAL_ERROR` | Salesforce server error |

---

## Field Reference

### Call Report Fields

| Field | Type | Description |
|-------|------|-------------|
| `Id` | ID | Unique Salesforce record identifier |
| `Name` | string | Auto-generated record name |
| `freedomcti__Call_Direction__c` | picklist | `Inbound` or `Outbound` |
| `freedomcti__Call_Duration__c` | number | Call duration in seconds |
| `freedomcti__Call_Start_Time__c` | datetime | Timestamp when call started |
| `freedomcti__Call_End_Time__c` | datetime | Timestamp when call ended |
| `freedomcti__Phone_Number__c` | phone | External phone number |
| `freedomcti__Contact__c` | reference | Related Contact record ID |
| `freedomcti__Lead__c` | reference | Related Lead record ID |
| `freedomcti__Account__c` | reference | Related Account record ID |
| `freedomcti__User__c` | reference | User who handled the call |
| `freedomcti__Call_Recording_URL__c` | url | Link to call recording |
| `freedomcti__Call_Notes__c` | textarea | Agent notes about the call |
| `freedomcti__Call_Outcome__c` | picklist | Call outcome status |

### Phone Event Fields

| Field | Type | Description |
|-------|------|-------------|
| `Id` | ID | Unique Salesforce record identifier |
| `Name` | string | Auto-generated record name |
| `freedomcti__Event_Type__c` | picklist | Type of phone event |
| `freedomcti__Event_Time__c` | datetime | When the event occurred |
| `freedomcti__Phone_Number__c` | phone | Caller's phone number |
| `freedomcti__Caller_Name__c` | string | Caller name (if identified) |
| `freedomcti__Contact__c` | reference | Matched Contact record ID |
| `freedomcti__Lead__c` | reference | Matched Lead record ID |
| `freedomcti__Account__c` | reference | Matched Account record ID |
| `freedomcti__User__c` | reference | User assigned to the call |
| `freedomcti__Queue_Name__c` | string | Call queue name |
| `freedomcti__Ring_Duration__c` | number | How long the call rang (seconds) |
| `freedomcti__Callback_Completed__c` | boolean | Whether callback was made |

---

## Related Documentation

- [Call Logs API](call-logs-api.md) - FreedomCTI backend call log endpoints
- [WebSocket Endpoints](websocket-endpoints.md) - Real-time presence updates
- [API Overview](README.md) - General API information