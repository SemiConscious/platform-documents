# Call and Telephony Models

This document covers the data models used for call management, call logs, telephony operations, and PBX-related structures in the platform-cti-client.

## Overview

The call and telephony models support:
- **Call State Management**: Tracking active calls and their status
- **Call Logging**: Recording and retrieving call history
- **Telephony Operations**: Transfers, conferencing, and call control
- **PBX Integration**: User presence and extension management

## Entity Relationships

```
┌─────────────────┐         ┌──────────────────┐
│   ActiveCall    │────────>│   CallDetails    │
│                 │         │                  │
│  - status       │         │ - other_name     │
│  - call_uuid    │         │ - lookup_results │
└────────┬────────┘         └──────────────────┘
         │
         │ references
         v
┌─────────────────┐         ┌──────────────────┐
│    CallLog      │<────────│SalesforceCall    │
│                 │         │   Reporting      │
│  - id (UUID)    │         │                  │
│  - direction    │         │ - From_UUID__c   │
│  - answered     │         │ - To_UUID__c     │
└─────────────────┘         └──────────────────┘
         │
         │ filtered by
         v
┌─────────────────┐         ┌──────────────────┐
│CallsFilterOption│         │  ChatterCallLog  │
│                 │         │                  │
│  - label        │         │  - aUuid         │
│  - value        │         │  - bUuid         │
└─────────────────┘         └──────────────────┘
```

---

## Active Call Models

### ActiveCall

Represents the current active call state stored in the Redux store. This is the primary model for tracking ongoing calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | number | Yes | Call status code (1-15, see CallStatusEnum) |
| auto_answering_call | string | No | Auto answering call identifier |
| call_direction | number | Yes | Call direction (1=Inbound, 2=Outbound) |
| other_number | string | No | Phone number of the other party |
| other_name | string | No | Name of the other party |
| display_text | string | No | Text to display in the UI |
| selected_person_result_id | string | No | ID of the selected person from lookup |
| selected_relatedto_result_id | string | No | ID of the selected related-to record |
| selected_result_id | string | No | Generic selected result ID |
| number_lookup_results | array | No | Results from number lookup operation |
| pop_record_lookup_results | array | No | Results from pop record lookup |
| call_uuid | string | Yes | Unique identifier for the call |

**Validation Rules:**
- `status` must be a valid value from CallStatusEnum (1-15)
- `call_direction` must be 1 (Inbound) or 2 (Outbound)
- `call_uuid` must be a valid UUID string

**Example:**
```json
{
  "status": 4,
  "auto_answering_call": null,
  "call_direction": 1,
  "other_number": "+14155551234",
  "other_name": "John Smith",
  "display_text": "Talking with John Smith",
  "selected_person_result_id": "003xx000004TmEQAA0",
  "selected_relatedto_result_id": "001xx000003DGbYAAW",
  "selected_result_id": "003xx000004TmEQAA0",
  "number_lookup_results": [
    {
      "object_id": "003xx000004TmEQAA0",
      "object_type": "Contact",
      "value": "John Smith"
    }
  ],
  "pop_record_lookup_results": [],
  "call_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Relationships:**
- References `CallDetails` for extended call information
- Uses `CallStatusEnum` for status values
- Uses `CallDirectionEnum` for direction values

---

### Call

Simplified call object model used for call state checks, such as determining incoming ringing calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| call_direction | string | Yes | Direction of the call (INBOUND_CALL or outbound) |
| status | string | Yes | Current call status (RINGING, CREATED_CALL_SESSION, etc.) |

**Validation Rules:**
- `call_direction` must match CallDirectionEnum values
- `status` must match CallStatusEnum string representations

**Example:**
```json
{
  "call_direction": "INBOUND_CALL",
  "status": "RINGING"
}
```

**Common Use Cases:**
- Checking if an incoming call is ringing
- Determining call state for UI updates

---

### CallDetails

Extended call information model containing lookup results for contacts and related entities.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| other_name | string | No | Name of the other party (internal number) |
| other_leg_uuid | string | No | UUID of the other leg of the call |
| number_lookup_results | LookupResult[] | No | Array of number lookup results |
| pop_record_lookup_results | LookupResult[] | No | Array of pop record lookup results |
| person_number_lookup_results | LookupResult[] | No | Array of person number lookup results |
| person_pop_record_lookup_results | LookupResult[] | No | Array of person pop record lookup results |
| relatedto_number_lookup_results | LookupResult[] | No | Array of related-to number lookup results |
| relatedto_pop_record_lookup_results | LookupResult[] | No | Array of related-to pop record lookup results |

**Example:**
```json
{
  "other_name": "Extension 1234",
  "other_leg_uuid": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "number_lookup_results": [
    {
      "object_id": "003xx000004TmEQAA0",
      "object_type": "Contact",
      "value": "Jane Doe"
    }
  ],
  "pop_record_lookup_results": [],
  "person_number_lookup_results": [
    {
      "object_id": "003xx000004TmEQAA0",
      "object_type": "Contact",
      "value": "Jane Doe"
    }
  ],
  "person_pop_record_lookup_results": [],
  "relatedto_number_lookup_results": [
    {
      "object_id": "001xx000003DGbYAAW",
      "object_type": "Account",
      "value": "Acme Corporation"
    }
  ],
  "relatedto_pop_record_lookup_results": []
}
```

**Relationships:**
- Contains arrays of `LookupResult` objects
- Linked to `ActiveCall` via UUID

---

### LookupResult

Represents a single lookup result for contact matching during calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| object_id | string | Yes | Unique Salesforce identifier for the lookup object |
| object_type | string | Yes | Type of the object (User, Contact, Account, Lead, etc.) |
| value | string | Yes | Display value or name |

**Example:**
```json
{
  "object_id": "003xx000004TmEQAA0",
  "object_type": "Contact",
  "value": "John Smith"
}
```

---

### LookupResultsOutput

Structured output from the `getLookupResults` function combining person and related-to arrays.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| person | LookupResult[] | Yes | Combined array of person number and pop record lookup results |
| relatedTo | LookupResult[] | Yes | Combined array of related-to number and pop record lookup results |

**Example:**
```json
{
  "person": [
    {
      "object_id": "003xx000004TmEQAA0",
      "object_type": "Contact",
      "value": "John Smith"
    }
  ],
  "relatedTo": [
    {
      "object_id": "001xx000003DGbYAAW",
      "object_type": "Account",
      "value": "Acme Corporation"
    },
    {
      "object_id": "006xx000001ABCDEF",
      "object_type": "Opportunity",
      "value": "Q4 Deal"
    }
  ]
}
```

---

## Call Log Models

### CallLog

Processed call log entry for display in the UI.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (UUID) |
| direction | string | Yes | Call direction (Inbound, Outbound) |
| answered | boolean | Yes | Whether the call was answered |
| time | string | Yes | Formatted call start time |
| duration | string | Yes | Formatted call duration |
| number | string | Yes | Phone number |
| name | string | No | Contact/user name |
| search | string | Yes | Lowercase search string for filtering |
| unixTimeStamp | number | Yes | Unix timestamp for sorting |
| recorded | boolean | Yes | Whether call was recorded |
| fromFlagRecord | array | No | Recording flags array |

**Validation Rules:**
- `direction` must be "Inbound" or "Outbound"
- `unixTimeStamp` must be a valid Unix timestamp
- `id` must be a valid UUID

**Example:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "direction": "Inbound",
  "answered": true,
  "time": "2024-01-15 14:30:25",
  "duration": "5:32",
  "number": "+14155551234",
  "name": "John Smith",
  "search": "john smith +14155551234 inbound",
  "unixTimeStamp": 1705329025,
  "recorded": true,
  "fromFlagRecord": ["RECORDED"]
}
```

**Common Use Cases:**
- Displaying call history in the UI
- Filtering and searching call records
- Playing back recorded calls

---

### CallLogsState

Redux state for managing call logs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| callLogsFilter | any | No | Current filter applied to call logs |
| callLogsSearch | string | No | Current search term for call logs |

**Example:**
```json
{
  "callLogsFilter": {
    "label": "Missed",
    "value": "Missed"
  },
  "callLogsSearch": "john"
}
```

---

### CallsFilterOption

Filter option for call logs dropdown.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| label | string | Yes | Display label for the filter |
| value | string | Yes | Filter value (All, Outbound, Inbound, Missed) |

**Validation Rules:**
- `value` must be one of: "All", "Outbound", "Inbound", "Missed"

**Example:**
```json
{
  "label": "Missed Calls",
  "value": "Missed"
}
```

---

### CallLogRefreshMessage

Message payload for refreshing call logs in the web worker.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Message type (CALL_LOGS_REFRESH) |
| urlRoot | string | Yes | Window location host |
| ns | string | No | Salesforce namespace prefix |
| sfToken | string | Yes | Salesforce session token |
| token | string | Yes | Access token |
| orgId | string | Yes | Organization ID |
| viewType | string | Yes | Current view type |
| userId | number | Yes | Natterbox user ID |
| searchTerm | string | No | Search term for filtering |
| filter | any | No | Call logs filter |
| isFreedomWeb | boolean | Yes | Freedom Web mode flag |
| salesforceHost | string | Yes | Salesforce host URL |
| sapienUrl | string | Yes | Sapien API URL |
| callLogsFromRemoteAction | any | No | Call logs from remote action |
| missedCallLogsFromRemoteAction | any | No | Missed call logs from remote action |

**Example:**
```json
{
  "type": "CALL_LOGS_REFRESH",
  "urlRoot": "na1.salesforce.com",
  "ns": "natterbox__",
  "sfToken": "00Dxx0000001gER!AR8AQJXg...",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "orgId": "12345",
  "viewType": "FULL_VIEW",
  "userId": 67890,
  "searchTerm": "",
  "filter": { "value": "All" },
  "isFreedomWeb": false,
  "salesforceHost": "https://na1.salesforce.com",
  "sapienUrl": "https://api.natterbox.com",
  "callLogsFromRemoteAction": null,
  "missedCallLogsFromRemoteAction": null
}
```

---

### ChatterCallLog

Call log entry from Chatter/Sapien API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| aFlags | array | No | A-leg flags (e.g., RECORDED) |
| bFlags | array | No | B-leg flags |
| timeStart | datetime | Yes | Call start time |
| timeTalking | number | No | Time spent talking in seconds |
| fromNumber | string | No | From phone number |
| fromUserId | number | No | From user ID |
| toNumberDialled | string | No | Dialled number |
| aUuid | string | Yes | A-leg UUID |
| bUuid | string | No | B-leg UUID |

**Example:**
```json
{
  "aFlags": ["RECORDED"],
  "bFlags": [],
  "timeStart": "2024-01-15T14:30:25Z",
  "timeTalking": 332,
  "fromNumber": "+14155551234",
  "fromUserId": 12345,
  "toNumberDialled": "+14155559876",
  "aUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "bUuid": "f1e2d3c4-b5a6-7890-1234-567890abcdef"
}
```

---

### SalesforceCallReporting

Salesforce CallReporting__c custom object fields for call data storage.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | string | Yes | Salesforce record ID |
| From_Start_Time__c | datetime | Yes | Call start time |
| Call_Direction__c | string | Yes | Call direction (Inbound, Outbound, Internal, Service) |
| From_UUID__c | string | Yes | From channel UUID |
| From_Dialled_Number__c | string | No | Dialled number from originator |
| From_Number__c | string | No | From phone number |
| From_AVS_User_Id__c | number | No | Natterbox user ID (from) |
| From_AVS_User__r.Name | string | No | From user name (relationship) |
| From_Time_Talking__c | number | No | Time spent talking |
| From_Flag_Record__c | boolean | No | Recording flag (from) |
| From_Flag_Voicemail_Record__c | boolean | No | Voicemail recording flag (from) |
| To_Channel_Start_Time__c | datetime | No | To channel start time |
| To_UUID__c | string | No | To channel UUID |
| To_Number__c | string | No | To phone number |
| To_AVS_User_Id__c | number | No | Natterbox user ID (to) |

**Example:**
```json
{
  "Id": "a0Axx000000ABCDEFG",
  "From_Start_Time__c": "2024-01-15T14:30:25.000Z",
  "Call_Direction__c": "Inbound",
  "From_UUID__c": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "From_Dialled_Number__c": "+14155559876",
  "From_Number__c": "+14155551234",
  "From_AVS_User_Id__c": 12345,
  "From_AVS_User__r": {
    "Name": "Jane Agent"
  },
  "From_Time_Talking__c": 332,
  "From_Flag_Record__c": true,
  "From_Flag_Voicemail_Record__c": false,
  "To_Channel_Start_Time__c": "2024-01-15T14:30:28.000Z",
  "To_UUID__c": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "To_Number__c": "+14155558888",
  "To_AVS_User_Id__c": 67890
}
```

---

### SalesforcePhoneEvent

Salesforce Phone_Event__c object for missed calls and other phone events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | string | Yes | Salesforce record ID |
| Time__c | datetime | Yes | Event time |
| Originating_UUID__c | string | Yes | Originating call UUID |
| Caller_ID_Number__c | string | No | Caller ID number |
| Originating_User_Id__c | number | No | Originating user ID |
| Caller_ID_Name__c | string | No | Caller ID name |
| User_Id__c | number | Yes | Target user ID |
| Event_Type__c | string | Yes | Event type (e.g., 'Missed Call') |
| To_Call_Reporting__c | string | No | Related CallReporting ID |
| To_Call_Reporting__r | object | No | Related CallReporting record |

**Example:**
```json
{
  "Id": "a0Bxx000000HIJKLMN",
  "Time__c": "2024-01-15T14:30:25.000Z",
  "Originating_UUID__c": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "Caller_ID_Number__c": "+14155551234",
  "Originating_User_Id__c": null,
  "Caller_ID_Name__c": "John Smith",
  "User_Id__c": 67890,
  "Event_Type__c": "Missed Call",
  "To_Call_Reporting__c": "a0Axx000000ABCDEFG",
  "To_Call_Reporting__r": {
    "Id": "a0Axx000000ABCDEFG",
    "Call_Direction__c": "Inbound"
  }
}
```

---

## PBX Models

### PBXListItem

PBX user list item for directory lookups.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| natterboxId | number | Yes | Natterbox user ID |

**Example:**
```json
{
  "natterboxId": 12345
}
```

---

### PBXResultItem

PBX/Address book search result item with presence information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| natterboxId | number | Yes | Natterbox user ID |
| presence | string | No | User presence status |
| logicalDirection | string | No | Call direction |
| callChannelUUID | string | No | UUID of the call channel |
| availability | string | No | Availability state name |

**Example:**
```json
{
  "natterboxId": 12345,
  "presence": "ANSWERED",
  "logicalDirection": "Outbound",
  "callChannelUUID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "availability": "Available"
}
```

**Relationships:**
- Uses `UserPresenceEnum` for presence values
- Contains availability state from `AvailabilityState`

---

## Enumerations

### CallStatusEnum

Enumeration of all possible call status codes.

| Field | Value | Description |
|-------|-------|-------------|
| CREATED_CALL_SESSION | 1 | Call session created |
| DIALING | 2 | Dialing state |
| RINGING | 3 | Ringing state |
| TALKING | 4 | Talking state |
| HOLDING | 5 | Call on hold |
| BLIND_TRANSFER | 6 | Blind transfer in progress |
| ATTENDED_TRANSFER_DIAL | 7 | Attended transfer dialing |
| ATTENDED_TRANSFER_RINGING | 8 | Attended transfer ringing |
| ATTENDED_TRANSFER_CONSULT | 9 | Attended transfer consulting |
| ATTENDED_TRANSFER_CONFERENCE | 10 | Attended transfer conference |
| WRAPUP_MODE | 11 | Wrapup mode |
| PARK_BEFORE_TRANSFER | 12 | Park before transfer |

**Example Usage:**
```javascript
if (call.status === CallStatusEnum.TALKING) {
  // Handle talking state
}
```

---

### CallDirectionEnum

Enumeration of call directions.

| Field | Value | Description |
|-------|-------|-------------|
| INBOUND_CALL | 1 | Inbound call |
| OUTBOUND_CALL | 2 | Outbound call |

**Example Usage:**
```javascript
const isInbound = call.call_direction === CallDirectionEnum.INBOUND_CALL;
```

---

### UserPresenceEnum

Enumeration of user presence states for PBX users.

| Field | Value | Description |
|-------|-------|-------------|
| USER_PRESENCE_ANSWERED | "ANSWERED" | User answered a call |
| USER_PRESENCE_BRIDGED | "BRIDGED" | User call is bridged |
| USER_PRESENCE_RINGING | "RINGING" | User phone is ringing |

---

### ListenModeEnum

Enumeration of listen-in talk modes for supervisor features.

| Field | Value | Description |
|-------|-------|-------------|
| LISTEN_MODE | "listen" | Listen only mode (silent monitoring) |
| WHISPER_MODE | "whisper" | Whisper to target mode (agent only hears) |
| BARGE_MODE | "barge" | Barge in mode (speak to both parties) |

---

### FooterTypes

Enumeration of footer type constants for call UI states.

| Field | Value | Description |
|-------|-------|-------------|
| HANG_UP | "hangUp" | Hang up footer type |
| CONSULT | "consult" | Consult footer type |
| CONFERENCE | "conference" | Conference footer type |
| ACTIVE_CALL | "activeCall" | Active call footer type |
| LISTENING_IN_CALL | "listeningInCall" | Listening in call footer type |

---

### TransferTypes

Enumeration of call transfer type constants.

| Field | Value | Description |
|-------|-------|-------------|
| ATTENDED_TRANSFER | "attended" | Attended/warm transfer type |
| BLIND_TRANSFER | "blind" | Blind/cold transfer type |

---

## Configuration Models

### CallCenterConfig

Configuration settings for call center behavior.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| updateLog | boolean | No | Whether to update the call log |
| offerSkipWrapupConditions | string \| string[] | No | Conditions for offering skip wrapup |

**Validation Rules:**
- `offerSkipWrapupConditions` can be "always" or an array containing "nocontact", "noanswer"

**Example:**
```json
{
  "updateLog": true,
  "offerSkipWrapupConditions": ["nocontact", "noanswer"]
}
```

---

### InternalCallConfig

Configuration for internal call detection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| noWrapupNumberLenEnd | number | Yes | Maximum number length for internal calls |
| noWrapupNumberLenStart | number | Yes | Minimum number length for internal calls |

**Example:**
```json
{
  "noWrapupNumberLenEnd": 6,
  "noWrapupNumberLenStart": 3
}
```

**Use Case:**
Calls to numbers with length between `noWrapupNumberLenStart` and `noWrapupNumberLenEnd` are considered internal and may skip wrapup.

---

## UI Helper Models

### IconState

State configuration for button/icon display during calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isIconDisabled | boolean | Yes | Whether the icon is disabled |
| isIconActive | boolean | Yes | Whether the icon is active |

**Example:**
```json
{
  "isIconDisabled": false,
  "isIconActive": true
}
```

---

### IconObject

Output object for button styling during calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cursor | string | Yes | CSS cursor class |
| icon | string | Yes | CSS icon class |

**Example:**
```json
{
  "cursor": "on-active",
  "icon": "call-button"
}
```

---

## Common Patterns

### Call Lifecycle

1. **Call Created**: `status = CREATED_CALL_SESSION`
2. **Dialing**: `status = DIALING`
3. **Ringing**: `status = RINGING`
4. **Connected**: `status = TALKING`
5. **On Hold**: `status = HOLDING`
6. **Transfer/Conference**: Various transfer statuses
7. **Wrapup**: `status = WRAPUP_MODE`
8. **Complete**: Call removed from active state

### Filtering Call Logs

```javascript
// Filter by direction
const inboundCalls = callLogs.filter(log => log.direction === 'Inbound');

// Filter by answered status
const missedCalls = callLogs.filter(log => !log.answered);

// Search by text
const searchResults = callLogs.filter(log => 
  log.search.includes(searchTerm.toLowerCase())
);
```