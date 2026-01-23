# Salesforce Integration Models

This document covers data models used for Salesforce API interactions, namespace handling, and Salesforce-specific data structures in the platform-cti-client.

## Overview

The Salesforce integration models handle:
- Global CTI configuration from Salesforce
- Namespace prefix management for custom objects
- Salesforce-specific call reporting and phone event records
- License type detection and view access control
- Session management and authentication

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Salesforce Integration Layer                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐     provides config     ┌──────────────────────┐  │
│  │  CTIConfig  │ ───────────────────────►│ SalesforceQuery      │  │
│  │  (window)   │                         │ NamespaceAction      │  │
│  └─────────────┘                         └──────────────────────┘  │
│        │                                           │                │
│        │ contains                                  │ updates        │
│        ▼                                           ▼                │
│  ┌─────────────┐                         ┌──────────────────────┐  │
│  │LocalDetails │                         │ MainState            │  │
│  │             │                         │ (sfQueryNamespace)   │  │
│  └─────────────┘                         └──────────────────────┘  │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                    Salesforce Data Objects                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │SalesforceCallReport │◄────────│ SalesforcePhoneEvent│           │
│  │ (CallReporting__c)  │  refs   │  (Phone_Event__c)   │           │
│  └─────────────────────┘         └─────────────────────┘           │
│           │                                                         │
│           │ transforms to                                           │
│           ▼                                                         │
│  ┌─────────────────────┐                                           │
│  │     CallLog         │ (see call-models.md)                      │
│  └─────────────────────┘                                           │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                    License & View Management                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │SalesforceLicenses│    │NatterboxLicenses│    │   ViewTypes    │  │
│  │ • STANDARD      │    │ • FREEDOM       │───►│ • FULL_VIEW    │  │
│  │ • CHATTER       │    │ • PBX           │    │ • LIMITED_VIEW │  │
│  └─────────────────┘    └─────────────────┘    │ • DENIED_VIEW  │  │
│                                                 └────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Models

### CTIConfig

Global CTI configuration object available on `window.cticonfig`. This is the primary configuration source injected by Salesforce into the CTI client.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| viewType | string | No | View type for Freedom rendering |
| salesforce_sid | string | Yes | Salesforce session ID for API authentication |
| salesforce_url | string | Yes | Salesforce host URL for SF origin calculation |
| namespacePrefix | string | No | Namespace prefix for Salesforce queries (managed package) |
| uiTheme | string | No | UI theme configuration |
| smsLicensed | string | No | SMS license status ('true'/'false' as string) |
| forceRemoteAction | boolean | No | Flag to force remote action usage over REST API |

**Validation Rules:**
- `salesforce_sid` must be a valid Salesforce session ID
- `salesforce_url` must be a valid HTTPS URL
- `smsLicensed` is a string boolean, not actual boolean

**Example:**
```json
{
  "viewType": "FULL_VIEW",
  "salesforce_sid": "00D5g00000ABC123!ARcAQD...",
  "salesforce_url": "https://mycompany.my.salesforce.com",
  "namespacePrefix": "natterbox",
  "uiTheme": "Theme4d",
  "smsLicensed": "true",
  "forceRemoteAction": false
}
```

**Usage:**
```typescript
// Accessing global config
const config = window.cticonfig;
const sfHost = config.salesforce_url;
const sessionId = config.salesforce_sid;
```

---

### LocalDetails

Local storage details retrieved by the `getLocalDetails` function for maintaining session state.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sfSessionId | string | Yes | Salesforce session ID |
| accessToken | string | Yes | JWT access token for Natterbox API |

**Validation Rules:**
- Both fields must be non-empty strings
- `sfSessionId` must match the current Salesforce session

**Example:**
```json
{
  "sfSessionId": "00D5g00000ABC123!ARcAQD...",
  "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Relationships:**
- Used in conjunction with `CTIConfig` for API authentication
- Stored in browser local storage for session persistence

---

## Namespace Models

### SalesforceQueryNamespaceAction

Redux action for setting the Salesforce query namespace. Used when the application needs to query custom objects from a managed package.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Action type: `SALESFORCE_QUERY_NAME_SPACE` |
| data.prefix | string | Yes | Namespace prefix (e.g., `natterbox__`) |
| data.path | string | Yes | Namespace path with `__` replaced by `/` |

**Validation Rules:**
- `type` must be exactly `SALESFORCE_QUERY_NAME_SPACE`
- `data.prefix` typically ends with `__` for managed packages
- `data.path` is derived from prefix by replacing `__` with `/`

**Example:**
```json
{
  "type": "SALESFORCE_QUERY_NAME_SPACE",
  "data": {
    "prefix": "natterbox__",
    "path": "natterbox/"
  }
}
```

**Usage:**
```typescript
// Dispatching namespace action
dispatch({
  type: 'SALESFORCE_QUERY_NAME_SPACE',
  data: {
    prefix: 'natterbox__',
    path: 'natterbox/'
  }
});

// Using in queries
const query = `SELECT Id, ${nsPrefix}From_Number__c FROM ${nsPrefix}CallReporting__c`;
```

---

## Salesforce Data Objects

### SalesforceCallReporting

Represents the Salesforce `CallReporting__c` custom object fields. This is the primary object for storing call history in Salesforce.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | string | Yes | Salesforce record ID (18 characters) |
| From_Start_Time__c | datetime | Yes | Call start time |
| Call_Direction__c | string | Yes | Call direction: Inbound, Outbound, Internal, Service |
| From_UUID__c | string | Yes | From channel UUID |
| From_Dialled_Number__c | string | No | Dialled number from originator |
| From_Number__c | string | Yes | From phone number |
| From_AVS_User_Id__c | number | No | Natterbox user ID (from side) |
| From_AVS_User__r.Name | string | No | From user name (relationship field) |
| From_Time_Talking__c | number | No | Time spent talking in seconds |
| From_Flag_Record__c | boolean | No | Recording flag (from side) |
| From_Flag_Voicemail_Record__c | boolean | No | Voicemail recording flag (from side) |
| To_Channel_Start_Time__c | datetime | No | To channel start time |
| To_UUID__c | string | No | To channel UUID |
| To_Number__c | string | No | To phone number |
| To_AVS_User_Id__c | number | No | Natterbox user ID (to side) |

**Validation Rules:**
- `Id` must be a valid 18-character Salesforce ID
- `Call_Direction__c` must be one of: Inbound, Outbound, Internal, Service
- `From_Start_Time__c` must be a valid ISO datetime

**Example:**
```json
{
  "Id": "a005g00000AbCdEfGH",
  "From_Start_Time__c": "2024-01-15T10:30:00.000Z",
  "Call_Direction__c": "Inbound",
  "From_UUID__c": "550e8400-e29b-41d4-a716-446655440000",
  "From_Dialled_Number__c": "+14155551234",
  "From_Number__c": "+442071234567",
  "From_AVS_User_Id__c": 12345,
  "From_AVS_User__r": {
    "Name": "John Smith"
  },
  "From_Time_Talking__c": 245,
  "From_Flag_Record__c": true,
  "From_Flag_Voicemail_Record__c": false,
  "To_Channel_Start_Time__c": "2024-01-15T10:30:05.000Z",
  "To_UUID__c": "550e8400-e29b-41d4-a716-446655440001",
  "To_Number__c": "+14155559876",
  "To_AVS_User_Id__c": 67890
}
```

**Relationships:**
- Referenced by `SalesforcePhoneEvent` via `To_Call_Reporting__c`
- Transforms to `CallLog` model for UI display
- Linked to Natterbox users via `From_AVS_User_Id__c` and `To_AVS_User_Id__c`

---

### SalesforcePhoneEvent

Represents the Salesforce `Phone_Event__c` custom object for missed calls and other phone events.

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
| To_Call_Reporting__r | object | No | Related CallReporting record (lookup) |

**Validation Rules:**
- `Event_Type__c` typically contains 'Missed Call'
- `Time__c` must be a valid ISO datetime
- `User_Id__c` must reference a valid Natterbox user

**Example:**
```json
{
  "Id": "a015g00000XyZaBcDE",
  "Time__c": "2024-01-15T14:22:30.000Z",
  "Originating_UUID__c": "660f9511-f30c-52e5-b827-557766551111",
  "Caller_ID_Number__c": "+442079876543",
  "Originating_User_Id__c": null,
  "Caller_ID_Name__c": "External Caller",
  "User_Id__c": 12345,
  "Event_Type__c": "Missed Call",
  "To_Call_Reporting__c": "a005g00000AbCdEfGH",
  "To_Call_Reporting__r": {
    "Id": "a005g00000AbCdEfGH",
    "Call_Direction__c": "Inbound"
  }
}
```

**Relationships:**
- References `SalesforceCallReporting` via `To_Call_Reporting__c` lookup
- Used to populate missed call logs in the UI

---

### ChatterCallLog

Call log data retrieved from the Chatter/Sapien API as an alternative to direct Salesforce queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| aFlags | array | No | A-leg flags (e.g., ['RECORDED']) |
| bFlags | array | No | B-leg flags |
| timeStart | datetime | Yes | Call start time |
| timeTalking | number | No | Time spent talking in seconds |
| fromNumber | string | Yes | From phone number |
| fromUserId | number | No | From user ID |
| toNumberDialled | string | No | Dialled number |
| aUuid | string | Yes | A-leg UUID |
| bUuid | string | No | B-leg UUID |

**Validation Rules:**
- `aFlags` and `bFlags` are arrays of string constants
- `timeTalking` is in seconds, can be 0 for unanswered calls

**Example:**
```json
{
  "aFlags": ["RECORDED"],
  "bFlags": [],
  "timeStart": "2024-01-15T09:15:00.000Z",
  "timeTalking": 180,
  "fromNumber": "+442071234567",
  "fromUserId": 12345,
  "toNumberDialled": "+14155551234",
  "aUuid": "770g0622-g41d-63f6-c938-668877662222",
  "bUuid": "770g0622-g41d-63f6-c938-668877663333"
}
```

**Relationships:**
- Transforms to `CallLog` model for UI display
- Alternative data source to `SalesforceCallReporting`

---

## License Models

### SalesforceLicenses

Constants defining Salesforce license types that affect feature availability.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| STANDARD_LICENSE | string | N/A | Standard Salesforce license (`"Standard"`) |
| CHATTER_LICENSE | string | N/A | Chatter-only Salesforce license (`"Chatter"`) |

**Example:**
```typescript
// License type constants
const SalesforceLicenses = {
  STANDARD_LICENSE: "Standard",
  CHATTER_LICENSE: "Chatter"
};

// Usage in license checking
if (userLicense === SalesforceLicenses.CHATTER_LICENSE) {
  // Limit functionality for Chatter-only users
}
```

**Relationships:**
- Combined with `NatterboxLicenses` to determine `ViewTypes`

---

### NatterboxLicenses

Constants defining Natterbox license types.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FREEDOM_LICENSE | string | N/A | Freedom license type (`"Freedom"`) |
| PBX_LICENSE | string | N/A | PBX license type (`"PBX"`) |

**Example:**
```typescript
// License type constants
const NatterboxLicenses = {
  FREEDOM_LICENSE: "Freedom",
  PBX_LICENSE: "PBX"
};

// Checking for Freedom features
if (natterboxLicense === NatterboxLicenses.FREEDOM_LICENSE) {
  enableAdvancedFeatures();
}
```

**Relationships:**
- Combined with `SalesforceLicenses` to determine `ViewTypes`

---

### ViewTypes

Constants defining view access levels based on license combinations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FULL_VIEW | string | N/A | Full view access (`"FULL_VIEW"`) |
| LIMITED_VIEW | string | N/A | Limited view access (`"LIMITED_VIEW"`) |
| DENIED_VIEW | string | N/A | Denied view access (`"DENIED_VIEW"`) |

**View Type Determination Logic:**

| Salesforce License | Natterbox License | View Type |
|-------------------|-------------------|-----------|
| Standard | Freedom | FULL_VIEW |
| Standard | PBX | LIMITED_VIEW |
| Chatter | Freedom | LIMITED_VIEW |
| Chatter | PBX | LIMITED_VIEW |
| None/Invalid | Any | DENIED_VIEW |

**Example:**
```typescript
// View type constants
const ViewTypes = {
  FULL_VIEW: "FULL_VIEW",
  LIMITED_VIEW: "LIMITED_VIEW",
  DENIED_VIEW: "DENIED_VIEW"
};

// Determining view type
function getViewType(sfLicense: string, nbLicense: string): string {
  if (sfLicense === SalesforceLicenses.STANDARD_LICENSE && 
      nbLicense === NatterboxLicenses.FREEDOM_LICENSE) {
    return ViewTypes.FULL_VIEW;
  }
  if (!sfLicense || !nbLicense) {
    return ViewTypes.DENIED_VIEW;
  }
  return ViewTypes.LIMITED_VIEW;
}
```

**Usage:**
```typescript
// Conditional feature rendering
if (viewType === ViewTypes.FULL_VIEW) {
  renderFullFeatureSet();
} else if (viewType === ViewTypes.LIMITED_VIEW) {
  renderBasicFeatureSet();
} else {
  renderAccessDenied();
}
```

---

### LicenseType

Consolidated license type constants for both NatterBox and Salesforce licensing (used in utility functions).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FREEDOM_LICENSE | constant | N/A | Freedom license type |
| PBX_LICENSE | constant | N/A | PBX license type |
| STANDARD_LICENSE | constant | N/A | Standard Salesforce license type |

**Example:**
```typescript
import { FREEDOM_LICENSE, PBX_LICENSE, STANDARD_LICENSE } from './constants';

function hasFullAccess(nbLicense: string, sfLicense: string): boolean {
  return nbLicense === FREEDOM_LICENSE && sfLicense === STANDARD_LICENSE;
}
```

---

## Avatar & UI Models

### AvatarTypes

Salesforce object types used for avatar display in the contact card and search results.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| USER | string | N/A | User object type (`"User"`) |
| ACCOUNT | string | N/A | Account object type (`"Account"`) |
| CONTACT | string | N/A | Contact object type (`"Contact"`) |
| LEAD | string | N/A | Lead object type (`"Lead"`) |
| CASE | string | N/A | Case object type (`"Case"`) |
| OPPORTUNITY | string | N/A | Opportunity object type (`"Opportunity"`) |
| CAMPAIGN | string | N/A | Campaign object type (`"Campaign"`) |
| GROUP | string | N/A | Group object type (`"Group"`) |

**Example:**
```typescript
const AvatarTypes = {
  USER: "User",
  ACCOUNT: "Account",
  CONTACT: "Contact",
  LEAD: "Lead",
  CASE: "Case",
  OPPORTUNITY: "Opportunity",
  CAMPAIGN: "Campaign",
  GROUP: "Group"
};

// Rendering appropriate avatar based on object type
function getAvatarIcon(objectType: string): string {
  switch (objectType) {
    case AvatarTypes.USER:
      return 'standard:user';
    case AvatarTypes.ACCOUNT:
      return 'standard:account';
    case AvatarTypes.CONTACT:
      return 'standard:contact';
    default:
      return 'standard:default';
  }
}
```

**Usage:**
- Determines icon style for search results
- Used in contact card rendering
- Maps to Salesforce Lightning Design System icons

---

## Common Patterns

### Namespace-Aware Queries

```typescript
// Building namespace-aware SOQL queries
const buildQuery = (nsPrefix: string) => {
  return `
    SELECT 
      Id, 
      ${nsPrefix}From_Number__c,
      ${nsPrefix}Call_Direction__c,
      ${nsPrefix}From_Start_Time__c
    FROM ${nsPrefix}CallReporting__c
    WHERE ${nsPrefix}From_AVS_User_Id__c = :userId
    ORDER BY ${nsPrefix}From_Start_Time__c DESC
    LIMIT 100
  `;
};
```

### Session Validation

```typescript
// Validating Salesforce session
function isSessionValid(config: CTIConfig, localDetails: LocalDetails): boolean {
  return (
    config.salesforce_sid === localDetails.sfSessionId &&
    localDetails.accessToken !== null
  );
}
```

### License-Based Feature Gating

```typescript
// Feature availability based on licenses
function getAvailableFeatures(viewType: string): string[] {
  const baseFeatures = ['dial', 'call_logs'];
  
  if (viewType === ViewTypes.FULL_VIEW) {
    return [...baseFeatures, 'voicemail', 'groups', 'settings', 'sms'];
  }
  
  if (viewType === ViewTypes.LIMITED_VIEW) {
    return baseFeatures;
  }
  
  return [];
}
```

---

## Related Documentation

- [State Models](./state-models.md) - Redux state including `MainState.sfQueryNamespace`
- [Call Models](./call-models.md) - `CallLog` model that transforms from Salesforce data
- [Auth Models](./auth-models.md) - JWT and authentication token handling