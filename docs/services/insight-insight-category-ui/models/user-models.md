# User Data Models

This document covers user-related data models in the insight-insight-category-ui service, including integrations with Salesforce and Sapien systems for user management and authentication.

## Overview

The user data models handle user identity, authentication state, and integration with external systems. The service retrieves user information from two primary sources:
- **Salesforce**: Primary user management system with CRM integration
- **Sapien**: Internal system providing availability and SIP device information

## Entity Relationship Diagram

```
┌─────────────────────────────────┐
│       UserSliceState            │
│   (Redux State Container)       │
├─────────────────────────────────┤
│ allUsersFromSalesforce[]────────┼──────┐
│ authUser ───────────────────────┼──┐   │
└─────────────────────────────────┘  │   │
                                     │   │
                    ┌────────────────┘   │
                    ▼                    ▼
         ┌─────────────────────┐  ┌─────────────────────┐
         │  UserFromSalesforce │  │  UserFromSalesforce │
         │  (Authenticated)    │  │  (List of Users)    │
         └─────────┬───────────┘  └─────────────────────┘
                   │
                   │ Transformed from
                   ▼
         ┌─────────────────────────────┐
         │ UserFromSalesforceRequest   │
         │ (Raw API Response)          │
         └─────────────────────────────┘

┌─────────────────────────────────┐
│       UserFromSapien            │
│   (Alternative User Source)     │
├─────────────────────────────────┤
│ availabilityProfile ────────────┼─────► AvailabilityProfile
│ availabilityState ──────────────┼─────► AvailabilityState
└─────────────────────────────────┘
```

---

## Redux State Models

### UserSliceState

Redux slice state for managing user data throughout the application.

#### Purpose
Maintains the global user state including the list of all users retrieved from Salesforce and the currently authenticated user. This state is used for user selection in category/prompt assignment and for tracking the current session.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allUsersFromSalesforce` | `UserFromSalesforce[]` | Yes | Array of all users retrieved from Salesforce API |
| `authUser` | `UserFromSalesforce \| null` | Yes | Currently authenticated user, null if not authenticated |

#### Example

```json
{
  "allUsersFromSalesforce": [
    {
      "enabled": true,
      "firstName": "John",
      "lastName": "Smith",
      "idFromSalesforce": "005xx000001SvSAAA0",
      "idFromApi": 12345,
      "mobilePhone": "+1-555-123-4567",
      "sipDevice": 1001,
      "username": "john.smith@company.com"
    },
    {
      "enabled": true,
      "firstName": "Jane",
      "lastName": "Doe",
      "idFromSalesforce": "005xx000001SvSBBB0",
      "idFromApi": 12346,
      "mobilePhone": "+1-555-987-6543",
      "sipDevice": 1002,
      "username": "jane.doe@company.com"
    }
  ],
  "authUser": {
    "enabled": true,
    "firstName": "John",
    "lastName": "Smith",
    "idFromSalesforce": "005xx000001SvSAAA0",
    "idFromApi": 12345,
    "mobilePhone": "+1-555-123-4567",
    "sipDevice": 1001,
    "username": "john.smith@company.com"
  }
}
```

#### Usage Patterns
- **User Assignment**: When creating categories or prompts, users are selected from `allUsersFromSalesforce`
- **Audit Tracking**: The `authUser.idFromApi` is used for `createdBy` fields on new entities
- **Permission Checking**: The `authUser` can be used to verify user permissions

---

## Salesforce User Models

### UserFromSalesforceRequest

Raw user model as received directly from the Salesforce API. Contains fields with both standard and namespaced variations to support different Salesforce org configurations.

#### Purpose
Represents the raw API response from Salesforce before normalization. The dual-field pattern (e.g., both `Enabled__c` and `nbavs__Enabled__c`) allows the application to work with different Salesforce package configurations.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Enabled__c` | `boolean` | No | Whether user is enabled (standard namespace) |
| `nbavs__Enabled__c` | `boolean` | No | Whether user is enabled (nbavs namespace) |
| `FirstName__c` | `string` | No | User's first name (standard namespace) |
| `nbavs__FirstName__c` | `string` | No | User's first name (nbavs namespace) |
| `Id` | `string` | Yes | Salesforce record ID |
| `nbavs__Id` | `string` | No | Salesforce record ID (nbavs namespace) |
| `Id__c` | `number` | No | API identifier (standard namespace) |
| `nbavs__Id__c` | `number` | No | API identifier (nbavs namespace) |
| `LastName__c` | `string` | No | User's last name (standard namespace) |
| `nbavs__LastName__c` | `string` | No | User's last name (nbavs namespace) |
| `MobilePhone__c` | `string` | No | Mobile phone number (standard namespace) |
| `nbavs__MobilePhone__c` | `string` | No | Mobile phone number (nbavs namespace) |
| `SipDevice__c` | `number` | No | SIP device identifier (standard namespace) |
| `nbavs__SipDevice__c` | `number` | No | SIP device identifier (nbavs namespace) |
| `User__c` | `string` | No | Reference to Salesforce User record |

#### Validation Rules
- At least one of `Id` or `nbavs__Id` must be present
- Namespace fields take precedence over standard fields when both are present

#### Example

```json
{
  "Id": "005xx000001SvSAAA0",
  "Enabled__c": true,
  "nbavs__Enabled__c": true,
  "FirstName__c": "John",
  "nbavs__FirstName__c": "John",
  "Id__c": 12345,
  "nbavs__Id__c": 12345,
  "LastName__c": "Smith",
  "nbavs__LastName__c": "Smith",
  "MobilePhone__c": "+1-555-123-4567",
  "nbavs__MobilePhone__c": "+1-555-123-4567",
  "SipDevice__c": 1001,
  "nbavs__SipDevice__c": 1001,
  "User__c": "005xx000001SvSAAA0"
}
```

---

### UserFromSalesforce

Normalized user model from Salesforce, transformed from `UserFromSalesforceRequest` for consistent application use.

#### Purpose
Provides a clean, consistent interface for user data regardless of the Salesforce namespace configuration. This is the primary user model used throughout the application after data transformation.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | `boolean` | Yes | Whether the user account is enabled and active |
| `firstName` | `string` | Yes | User's first name |
| `lastName` | `string` | Yes | User's last name |
| `idFromSalesforce` | `string` | Yes | Unique Salesforce record ID (18-character format) |
| `idFromApi` | `number` | Yes | Numeric API identifier used for internal references |
| `mobilePhone` | `string` | No | User's mobile phone number |
| `sipDevice` | `number` | No | SIP device identifier for telephony integration |
| `username` | `string` | Yes | User's login username (typically email) |

#### Validation Rules
- `idFromSalesforce` must be a valid 18-character Salesforce ID
- `idFromApi` must be a positive integer
- `firstName` and `lastName` cannot be empty strings
- `enabled` determines if user appears in selection lists

#### Example

```json
{
  "enabled": true,
  "firstName": "John",
  "lastName": "Smith",
  "idFromSalesforce": "005xx000001SvSAAA0",
  "idFromApi": 12345,
  "mobilePhone": "+1-555-123-4567",
  "sipDevice": 1001,
  "username": "john.smith@company.com"
}
```

#### Relationships
- Referenced by `CategorySliceState.createdBy` via `idFromApi`
- Referenced by `PromptSliceState.createdBy` via `idFromApi`
- Used in `CreateCategoryBody.onlyAppliesTo.users` array
- Used in `EditCategoryBody.onlyAppliesTo.users` array

#### Common Use Cases

**Display User Name:**
```typescript
const displayName = `${user.firstName} ${user.lastName}`;
```

**Filter Active Users:**
```typescript
const activeUsers = allUsers.filter(user => user.enabled);
```

**Find Category Creator:**
```typescript
const creator = allUsers.find(user => user.idFromApi === category.createdBy);
```

---

## Sapien User Models

### UserFromSapien

User model from the Sapien system, providing real-time availability and SIP extension information.

#### Purpose
Represents user data from the Sapien telephony system. Used for real-time agent availability tracking and SIP-based communication routing.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `number` | Yes | Unique Sapien user identifier |
| `userName` | `string` | Yes | User's login name in Sapien |
| `firstName` | `string` | Yes | User's first name |
| `lastName` | `string` | Yes | User's last name |
| `sipExtension` | `string` | Yes | SIP extension number for telephony |
| `availabilityProfile` | `AvailabilityProfile` | Yes | User's configured availability profile |
| `availabilityState` | `AvailabilityState` | Yes | Current real-time availability state |

#### Example

```json
{
  "id": 5001,
  "userName": "jsmith",
  "firstName": "John",
  "lastName": "Smith",
  "sipExtension": "1001",
  "availabilityProfile": {
    "id": 1,
    "name": "Standard Agent"
  },
  "availabilityState": {
    "id": 2,
    "name": "AVAILABLE",
    "displayName": "Available"
  }
}
```

#### Relationships
- Contains `AvailabilityProfile` as nested object
- Contains `AvailabilityState` as nested object
- May correlate with `UserFromSalesforce` via SIP device/extension matching

---

### AvailabilityProfile

Defines a user's availability configuration profile in the Sapien system.

#### Purpose
Represents the configured availability settings for a user, determining how their availability states and routing rules are managed.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `number` | Yes | Unique profile identifier |
| `name` | `string` | Yes | Human-readable profile name |

#### Example

```json
{
  "id": 1,
  "name": "Standard Agent"
}
```

```json
{
  "id": 2,
  "name": "Supervisor"
}
```

```json
{
  "id": 3,
  "name": "Premium Support"
}
```

---

### AvailabilityState

Represents a user's current real-time availability status.

#### Purpose
Tracks the current availability state of a user for routing and display purposes. The `displayName` provides a user-friendly version suitable for UI presentation.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `number` | Yes | Unique state identifier |
| `name` | `string` | Yes | System name for the state (typically uppercase) |
| `displayName` | `string` | Yes | User-friendly display name for UI |

#### Common State Values

| ID | Name | Display Name |
|----|------|--------------|
| 1 | `OFFLINE` | Offline |
| 2 | `AVAILABLE` | Available |
| 3 | `BUSY` | Busy |
| 4 | `AWAY` | Away |
| 5 | `ON_CALL` | On Call |
| 6 | `WRAP_UP` | Wrap Up |

#### Example

```json
{
  "id": 2,
  "name": "AVAILABLE",
  "displayName": "Available"
}
```

```json
{
  "id": 5,
  "name": "ON_CALL",
  "displayName": "On Call"
}
```

---

## Data Transformation

### Salesforce to Normalized User

The transformation from `UserFromSalesforceRequest` to `UserFromSalesforce` handles namespace variations:

```typescript
function transformSalesforceUser(raw: UserFromSalesforceRequest): UserFromSalesforce {
  return {
    enabled: raw.nbavs__Enabled__c ?? raw.Enabled__c ?? false,
    firstName: raw.nbavs__FirstName__c ?? raw.FirstName__c ?? '',
    lastName: raw.nbavs__LastName__c ?? raw.LastName__c ?? '',
    idFromSalesforce: raw.nbavs__Id ?? raw.Id,
    idFromApi: raw.nbavs__Id__c ?? raw.Id__c ?? 0,
    mobilePhone: raw.nbavs__MobilePhone__c ?? raw.MobilePhone__c ?? '',
    sipDevice: raw.nbavs__SipDevice__c ?? raw.SipDevice__c ?? 0,
    username: raw.User__c ?? ''
  };
}
```

---

## Integration Points

### Category Assignment
Users from `UserSliceState.allUsersFromSalesforce` are used when configuring category scope:

```typescript
// In CreateCategoryBody
{
  "onlyAppliesTo": {
    "groups": ["group-1", "group-2"],
    "users": ["005xx000001SvSAAA0", "005xx000001SvSBBB0"]
  }
}
```

### Audit Trail
The `authUser.idFromApi` is captured when creating entities:

```typescript
// Category or Prompt creation
{
  "createdBy": 12345  // authUser.idFromApi
}
```

### User Display
User names are resolved for display in tables and forms:

```typescript
// Find user by API ID for display
const getUserDisplayName = (userId: number): string => {
  const user = allUsersFromSalesforce.find(u => u.idFromApi === userId);
  return user ? `${user.firstName} ${user.lastName}` : 'Unknown User';
};
```