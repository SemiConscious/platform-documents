# Billing and Subscriptions API

The Billing and Subscriptions API provides endpoints for managing billing profiles, subscriptions, and financial aspects of the telecommunications platform. This includes retrieving billing information for organizations and managing service subscriptions.

## Overview

The billing system in the platform manages:
- **Billing Profiles**: Organization-level billing configurations and payment settings
- **Subscriptions**: Service subscriptions for entities (users, devices, etc.)
- **Rate Management**: Call rates and tariff configurations (managed through billing profiles)

## Base URL

All endpoints are relative to:
```
https://api.platform.example.com
```

---

## Billing Profile Endpoints

### Get Billing Profile (Authenticated Organization)

Retrieves the billing profile for the currently authenticated organization.

```
GET /billingprofile
```

#### Description

Returns the billing profile associated with the organization of the authenticated user. This endpoint requires no parameters as it uses the authentication context to determine the organization.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| None | - | - | - | Uses authenticated organization context |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/billingprofile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "billingProfileId": "bp_12345",
    "organizationId": "org_67890",
    "billingName": "Acme Corporation",
    "billingAddress": {
      "street": "123 Business Ave",
      "city": "New York",
      "state": "NY",
      "postalCode": "10001",
      "country": "US"
    },
    "billingContact": {
      "name": "John Smith",
      "email": "billing@acme.com",
      "phone": "+1-555-123-4567"
    },
    "paymentMethod": "invoice",
    "currency": "USD",
    "billingCycle": "monthly",
    "taxId": "12-3456789",
    "taxExempt": false,
    "creditLimit": 10000.00,
    "currentBalance": 2500.00,
    "paymentTerms": "NET30",
    "rates": {
      "defaultCallRate": 0.015,
      "defaultSmsRate": 0.0075,
      "internationalCallRate": 0.045
    },
    "tariffPlan": "enterprise",
    "discounts": [
      {
        "type": "volume",
        "threshold": 10000,
        "percentage": 10
      }
    ],
    "createdAt": "2023-01-15T10:00:00Z",
    "updatedAt": "2024-01-10T14:30:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `unauthorized` | Missing or invalid authentication token |
| 403 | `forbidden` | User does not have permission to view billing profile |
| 404 | `not_found` | No billing profile exists for the organization |
| 500 | `internal_error` | Server error while retrieving billing profile |

---

### Get Billing Profile by Organization ID

Retrieves the billing profile for a specific organization by ID.

```
GET /billingprofile/:id
```

#### Description

Returns the billing profile for a specified organization. Requires appropriate permissions to view billing information for other organizations (typically admin or reseller access).

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | path | Yes | Organization ID to retrieve billing profile for |

#### Request Example

```bash
curl -X GET "https://api.platform.example.com/billingprofile/org_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "billingProfileId": "bp_12345",
    "organizationId": "org_67890",
    "billingName": "Acme Corporation",
    "billingAddress": {
      "street": "123 Business Ave",
      "city": "New York",
      "state": "NY",
      "postalCode": "10001",
      "country": "US"
    },
    "billingContact": {
      "name": "John Smith",
      "email": "billing@acme.com",
      "phone": "+1-555-123-4567"
    },
    "paymentMethod": "invoice",
    "currency": "USD",
    "billingCycle": "monthly",
    "taxId": "12-3456789",
    "taxExempt": false,
    "creditLimit": 10000.00,
    "currentBalance": 2500.00,
    "outstandingInvoices": 2,
    "paymentTerms": "NET30",
    "rates": {
      "defaultCallRate": 0.015,
      "defaultSmsRate": 0.0075,
      "internationalCallRate": 0.045,
      "tollFreeRate": 0.03
    },
    "tariffPlan": "enterprise",
    "tariffPlanDetails": {
      "name": "Enterprise Plan",
      "monthlyMinimum": 500.00,
      "includedMinutes": 50000,
      "includedSms": 10000
    },
    "discounts": [
      {
        "type": "volume",
        "threshold": 10000,
        "percentage": 10
      },
      {
        "type": "loyalty",
        "yearsActive": 2,
        "percentage": 5
      }
    ],
    "usageSummary": {
      "currentPeriodStart": "2024-01-01T00:00:00Z",
      "currentPeriodEnd": "2024-01-31T23:59:59Z",
      "minutesUsed": 35420,
      "smsUsed": 8750,
      "currentCharges": 1875.50
    },
    "createdAt": "2023-01-15T10:00:00Z",
    "updatedAt": "2024-01-10T14:30:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `invalid_id` | Invalid organization ID format |
| 401 | `unauthorized` | Missing or invalid authentication token |
| 403 | `forbidden` | User does not have permission to view this organization's billing profile |
| 404 | `not_found` | Organization or billing profile not found |
| 500 | `internal_error` | Server error while retrieving billing profile |

---

## Subscription Endpoints

### Get Subscription by Entity

Retrieves subscription information for a specific entity type and ID.

```
GET /subscriptions/:entity/:id
```

#### Description

Returns subscription details for an entity, commonly used for BLF (Busy Lamp Field) subscriptions and other service-related subscriptions. The entity type determines what kind of subscription data is returned.

#### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `entity` | string | path | Yes | Entity type (e.g., `blf`, `user`, `device`, `line`) |
| `id` | string | path | Yes | Entity ID to retrieve subscriptions for |

#### Request Example

```bash
# Get BLF subscriptions for a user
curl -X GET "https://api.platform.example.com/subscriptions/blf/user_12345" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

```bash
# Get device subscriptions
curl -X GET "https://api.platform.example.com/subscriptions/device/dev_67890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (BLF Subscription)

```json
{
  "success": true,
  "data": {
    "subscriptionId": "sub_abc123",
    "entityType": "blf",
    "entityId": "user_12345",
    "organizationId": "org_67890",
    "status": "active",
    "subscriptionType": "blf_monitoring",
    "targets": [
      {
        "targetId": "user_11111",
        "targetExtension": "1001",
        "displayName": "Alice Johnson",
        "buttonIndex": 1
      },
      {
        "targetId": "user_22222",
        "targetExtension": "1002",
        "displayName": "Bob Williams",
        "buttonIndex": 2
      },
      {
        "targetId": "user_33333",
        "targetExtension": "1003",
        "displayName": "Carol Davis",
        "buttonIndex": 3
      }
    ],
    "maxTargets": 50,
    "protocol": "SIP",
    "expiresAt": "2024-01-15T12:00:00Z",
    "autoRenew": true,
    "createdAt": "2024-01-01T10:00:00Z",
    "updatedAt": "2024-01-10T08:30:00Z"
  }
}
```

#### Response Example (Service Subscription)

```json
{
  "success": true,
  "data": {
    "subscriptionId": "sub_xyz789",
    "entityType": "user",
    "entityId": "user_12345",
    "organizationId": "org_67890",
    "status": "active",
    "subscriptions": [
      {
        "serviceType": "voicemail",
        "plan": "enhanced",
        "status": "active",
        "features": ["transcription", "email_notification", "mobile_access"],
        "startDate": "2023-06-01T00:00:00Z",
        "billingRate": 5.00,
        "billingCycle": "monthly"
      },
      {
        "serviceType": "call_recording",
        "plan": "compliance",
        "status": "active",
        "features": ["auto_record", "retention_7yr", "encryption"],
        "startDate": "2023-06-01T00:00:00Z",
        "storageUsedGB": 12.5,
        "storageIncludedGB": 50,
        "billingRate": 15.00,
        "billingCycle": "monthly"
      },
      {
        "serviceType": "video_conferencing",
        "plan": "business",
        "status": "active",
        "features": ["hd_video", "screen_share", "recording"],
        "maxParticipants": 100,
        "startDate": "2023-09-15T00:00:00Z",
        "billingRate": 25.00,
        "billingCycle": "monthly"
      }
    ],
    "totalMonthlyRate": 45.00,
    "currency": "USD",
    "nextBillingDate": "2024-02-01T00:00:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `invalid_entity_type` | Unrecognized entity type provided |
| 400 | `invalid_id` | Invalid entity ID format |
| 401 | `unauthorized` | Missing or invalid authentication token |
| 403 | `forbidden` | User does not have permission to view subscriptions for this entity |
| 404 | `not_found` | Entity or subscription not found |
| 500 | `internal_error` | Server error while retrieving subscription |

---

## Data Models

### Billing Profile Object

| Field | Type | Description |
|-------|------|-------------|
| `billingProfileId` | string | Unique identifier for the billing profile |
| `organizationId` | string | Associated organization ID |
| `billingName` | string | Name on billing statements |
| `billingAddress` | object | Billing address details |
| `billingContact` | object | Primary billing contact information |
| `paymentMethod` | string | Payment method (`invoice`, `credit_card`, `ach`, `wire`) |
| `currency` | string | ISO 4217 currency code |
| `billingCycle` | string | Billing frequency (`monthly`, `quarterly`, `annual`) |
| `taxId` | string | Tax identification number |
| `taxExempt` | boolean | Tax exemption status |
| `creditLimit` | number | Maximum credit limit |
| `currentBalance` | number | Current account balance |
| `paymentTerms` | string | Payment terms (e.g., `NET30`) |
| `rates` | object | Custom rate configuration |
| `tariffPlan` | string | Active tariff plan identifier |
| `discounts` | array | Applied discounts |
| `createdAt` | string | ISO 8601 creation timestamp |
| `updatedAt` | string | ISO 8601 last update timestamp |

### Subscription Object

| Field | Type | Description |
|-------|------|-------------|
| `subscriptionId` | string | Unique subscription identifier |
| `entityType` | string | Type of entity subscribed |
| `entityId` | string | Entity identifier |
| `organizationId` | string | Associated organization ID |
| `status` | string | Subscription status (`active`, `suspended`, `cancelled`, `pending`) |
| `subscriptionType` | string | Type of subscription |
| `startDate` | string | ISO 8601 subscription start date |
| `expiresAt` | string | ISO 8601 expiration timestamp |
| `autoRenew` | boolean | Auto-renewal status |
| `billingRate` | number | Subscription rate |
| `billingCycle` | string | Billing frequency |

---

## Related Documentation

- [Authentication](./authentication.md) - API authentication methods
- [Organizations](./organizations.md) - Organization management
- [Users and Groups](./users-and-groups.md) - User management
- [Telephony](./telephony.md) - Call and telephony services that generate billable events