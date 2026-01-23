# Billing Models

This document covers all billing-related models in the Platform API, including rates, tariffs, subscriptions, invoices, payments, and organizational billing configuration.

## Overview

The billing system in Platform API supports complex pricing scenarios including:
- **Rate Management**: Global and local rate configurations for various services
- **Subscription Management**: Service subscriptions with quantity and margin tracking
- **Invoice & Payment Processing**: Invoice generation and payment tracking
- **Margin Configuration**: Tiered margin/discount structures for resellers
- **LCR (Least Cost Routing)**: Carrier rate management for call routing

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Services     │       │     Rates       │       │   OrgMargins    │
│                 │       │                 │       │                 │
│  SID (PK)       │◄──────│  RID (PK)       │       │  OrgID (FK)     │
│  ServiceName    │       │  SID (FK)       │       │  Type           │
└─────────────────┘       │  RateName       │       │  Service        │
                          │  BillingType    │       │  Hardware       │
                          └────────┬────────┘       └─────────────────┘
                                   │
                                   ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│      Orgs       │◄──────│  OrgServices    │       │ OrgServicesRates│
│                 │       │                 │       │                 │
│  OrgID (PK)     │       │  OSID (PK)      │◄──────│  OSID (FK)      │
│  BillingOrgID   │       │  OrgID (FK)     │       │  RID (FK)       │
│  Balance        │       │                 │       │  Quantity       │
│  CreditLimit    │       └─────────────────┘       │  Margin         │
└────────┬────────┘                                 └─────────────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│    Invoices     │ │    Payments     │
│                 │ │                 │
│  OrgID (FK)     │ │  OrgID (FK)     │
│  Total          │ │  Amount         │
│  CreatedDate    │ │  Type           │
└─────────────────┘ └─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    LCR Billing Models                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│  LCR_Carriers   │   LCR_Bands     │      LCR_LCRRates       │
│                 │                 │                         │
│  ID (PK)        │◄──ID (PK)       │◄──ID (PK)               │
│  CarrierName    │  CarrierID (FK) │  BandID (FK)            │
│  Type           │  BandName       │  Rate                   │
└─────────────────┴─────────────────┴─────────────────────────┘
```

---

## Core Billing Models

### Rate

Pricing rate configuration for services and SIM operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| RID | int | Yes | Primary key - Rate ID |
| Scope | string | Yes | `Global` or `Local` scope indicator |
| UnitType | string | Yes | Type of unit: `SIM_SMS`, `SIM_MMS`, `SIM_Call`, `SIM_Package` |
| RateName | string | Yes | Name of the rate (aliased as Item) |
| Description | string | No | Rate description |
| StartDate | date | No | Rate validity start date |
| EndDate | date | No | Rate validity end date |
| InRange | string | No | `YES`/`NO` indicator if current date is within rate validity range |
| OrgID | int | Yes | Organization ID (0 for global rates) |

**Validation Rules:**
- `UnitType` must be one of the predefined SIM operation types
- `Scope` must be either `Global` or `Local`
- `StartDate` must be before `EndDate` when both are specified
- `OrgID` of 0 indicates a global rate applicable to all organizations

**Example JSON:**
```json
{
  "RID": 1542,
  "Scope": "Global",
  "UnitType": "SIM_Call",
  "RateName": "UK Mobile Standard",
  "Description": "Standard rate for UK mobile calls",
  "StartDate": "2024-01-01",
  "EndDate": "2024-12-31",
  "InRange": "YES",
  "OrgID": 0
}
```

**Relationships:**
- Referenced by `Rates` for service-specific rate definitions
- Used by `OrgServicesRates` to assign rates to organization services

---

### Rates

Service rate definitions linking rates to services.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| RID | int | Yes | Primary key - Rate ID |
| SID | int | Yes | Foreign key to Services table |
| RateName | string | Yes | Human-readable rate name |
| BillingType | enum | Yes | Billing type: `Recurring`, `Both`, `OneTime` |

**Validation Rules:**
- `SID` must reference a valid service
- `BillingType` determines how charges are applied

**Example JSON:**
```json
{
  "RID": 2001,
  "SID": 15,
  "RateName": "Enterprise SIP Trunk - Monthly",
  "BillingType": "Recurring"
}
```

**Relationships:**
- Foreign key to `Services` via `SID`
- Referenced by `OrgServicesRates` via `RID`
- Referenced by `OrgServiceRate` via `RID`

---

### Services

Service definitions for billable products.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SID | int | Yes | Primary key - Service ID |
| ServiceName | string | Yes | Name of the service |

**Validation Rules:**
- `ServiceName` must be unique within the system

**Example JSON:**
```json
{
  "SID": 15,
  "ServiceName": "SIP Trunk Service"
}
```

**Relationships:**
- Referenced by `Rates` via `SID`
- Referenced by `OrgService` via `ServiceID`

---

## Organization Billing Models

### OrgServices

Organization service subscriptions linking orgs to services.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OSID | int | Yes | Primary key - Org Service ID |
| OrgID | int | Yes | Foreign key to organization |

**Example JSON:**
```json
{
  "OSID": 5001,
  "OrgID": 1234
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`
- Referenced by `OrgServicesRates` via `OSID`

---

### OrgServicesRates

Organization service rate assignments with pricing details.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OSID | int | Yes | Foreign key to OrgServices |
| RID | int | Yes | Foreign key to Rates |
| Quantity | int | Yes | Service quantity subscribed |
| Margin | decimal | No | Applied margin percentage |
| Discount | decimal | No | Applied discount percentage |
| RecurringPrice | decimal | No | Recurring price override |
| ActivationDiscount | decimal | No | Discount on activation fee |
| ActivationPrice | decimal | No | Activation price override |
| Start | date | No | Rate start date |
| End | date | No | Rate end date |

**Validation Rules:**
- `Quantity` must be a positive integer
- `Margin` and `Discount` are percentage values (0-100)
- `Start` must be before `End` when both specified

**Example JSON:**
```json
{
  "OSID": 5001,
  "RID": 2001,
  "Quantity": 10,
  "Margin": 15.00,
  "Discount": 5.00,
  "RecurringPrice": 45.00,
  "ActivationDiscount": 0.00,
  "ActivationPrice": 50.00,
  "Start": "2024-01-01",
  "End": "2024-12-31"
}
```

**Relationships:**
- Foreign key to `OrgServices` via `OSID`
- Foreign key to `Rates` via `RID`

---

### OrgService

Service configuration for an organization with status tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OSID | int | Yes | Primary key - Org Service ID |
| OrgID | int | Yes | Foreign key to organization |
| ServiceID | int | Yes | Foreign key to service |
| Status | string | Yes | Service status: `Active`, `Inactive` |
| StartDate | date | Yes | Service activation date |
| EndDate | date | No | Service termination date (`0000-00-00` for indefinite) |

**Validation Rules:**
- `Status` must be `Active` or `Inactive`
- `EndDate` of `0000-00-00` indicates an ongoing subscription

**Example JSON:**
```json
{
  "OSID": 5002,
  "OrgID": 1234,
  "ServiceID": 15,
  "Status": "Active",
  "StartDate": "2024-01-15",
  "EndDate": "0000-00-00"
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`
- Foreign key to `Services` via `ServiceID`
- Referenced by `OrgServiceRate` via `OSID`

---

### OrgServiceRate

Detailed rate configuration for organization services with discount management.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OSRID | int | Yes | Primary key - Org Service Rate ID |
| RID | int | Yes | Foreign key to Rate |
| OSID | int | Yes | Foreign key to OrgService |
| OrgID | int | Yes | Organization ID |
| Quantity | int | Yes | Quantity of units |
| Discount | float | No | Discount percentage |
| DiscountUntil | date | No | Discount validity end date |
| DiscountActivation | float | No | Activation discount percentage |
| Price | decimal | No | Custom price override |
| PriceActivation | decimal | No | Custom activation price |
| Margin | decimal | No | Margin percentage |
| Notes | string | No | Additional notes |
| PORef | string | No | Purchase order reference |
| BillingType | string | No | Type of billing |
| EndDate | date | No | Rate end date |

**Validation Rules:**
- `Discount` and `DiscountActivation` are percentages (0-100)
- `DiscountUntil` should be in the future when setting a new discount
- `PORef` is typically used for enterprise customers with PO requirements

**Example JSON:**
```json
{
  "OSRID": 8001,
  "RID": 2001,
  "OSID": 5002,
  "OrgID": 1234,
  "Quantity": 25,
  "Discount": 10.0,
  "DiscountUntil": "2024-06-30",
  "DiscountActivation": 50.0,
  "Price": 42.50,
  "PriceActivation": 25.00,
  "Margin": 20.0,
  "Notes": "Enterprise agreement - 2 year term",
  "PORef": "PO-2024-00456",
  "BillingType": "Recurring",
  "EndDate": "2026-01-15"
}
```

**Relationships:**
- Foreign key to `Rates` via `RID`
- Foreign key to `OrgService` via `OSID`
- Foreign key to `Orgs` via `OrgID`

---

### BillingPrefs

Organization billing preferences configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Primary key - Organization ID |
| BillingDay | int | Yes | Day of month for billing (1-28) |
| BillingCycle | string | Yes | Billing cycle period |
| VAT | string | No | VAT number or rate |
| Currency | string | Yes | Billing currency code (ISO 4217) |

**Validation Rules:**
- `BillingDay` must be between 1 and 28 to accommodate all months
- `Currency` should be a valid ISO 4217 currency code
- `VAT` can be a registration number or percentage rate

**Example JSON:**
```json
{
  "OrgID": 1234,
  "BillingDay": 15,
  "BillingCycle": "Monthly",
  "VAT": "GB123456789",
  "Currency": "GBP"
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`

---

### OrgMargins

Organization margin/discount levels for reseller pricing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | No | Organization ID (null for default levels) |
| Type | string | Yes | Margin level type identifier |
| Service | decimal | Yes | Service margin percentage |
| ServiceOption | decimal | Yes | Service option margin percentage |
| RatePlan | decimal | Yes | Rate plan margin percentage |
| Support | decimal | Yes | Support margin percentage |
| Additional | decimal | Yes | Additional services margin percentage |
| Hardware | decimal | Yes | Hardware margin percentage |

**Validation Rules:**
- All margin values are percentages (typically 0-100)
- `OrgID` of null or 0 indicates a default margin level
- Custom margins override default levels when `OrgID` is specified

**Example JSON:**
```json
{
  "OrgID": 1234,
  "Type": "Gold Partner",
  "Service": 25.00,
  "ServiceOption": 20.00,
  "RatePlan": 15.00,
  "Support": 30.00,
  "Additional": 18.00,
  "Hardware": 12.00
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`
- Used by `Orgs.MarginLevel` to reference margin type

---

## Invoice & Payment Models

### Invoices

Invoice records for organization billing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Foreign key to organization |
| CreatedDate | date | Yes | Invoice creation date |
| Total | decimal | Yes | Invoice total amount |
| FileID | string | No | Reference to invoice file/document |

**Validation Rules:**
- `Total` must be a positive decimal value
- `CreatedDate` is system-generated at invoice creation

**Example JSON:**
```json
{
  "OrgID": 1234,
  "CreatedDate": "2024-02-01",
  "Total": 1542.75,
  "FileID": "INV-2024-001234-FEB"
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`

---

### Payments

Payment records tracking financial transactions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Foreign key to organization |
| Date | date | Yes | Payment date |
| Amount | decimal | Yes | Payment amount |
| Type | enum | Yes | Payment type: `DD` (Direct Debit), `Card`, `BACS`, etc. |
| Status | enum | Yes | Payment status: `DDPending`, `Completed`, `Failed`, etc. |
| DDOnDate | date | No | Direct debit scheduled date |

**Validation Rules:**
- `Amount` must be a positive decimal
- `DDOnDate` required when `Type` is `DD`
- `Status` transitions follow payment processing workflow

**Example JSON:**
```json
{
  "OrgID": 1234,
  "Date": "2024-02-15",
  "Amount": 1542.75,
  "Type": "DD",
  "Status": "DDPending",
  "DDOnDate": "2024-02-20"
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`

---

## LCR (Least Cost Routing) Billing Models

### LCR_Carriers

LCR carriers/providers for call routing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key - Carrier ID |
| CarrierName | string | Yes | Carrier name |
| Enabled | boolean | Yes | Whether carrier is enabled |
| Type | enum | Yes | Carrier type: `retail`, `route` |
| ClosedLoopCarrier | boolean | No | Closed loop carrier flag |
| PrivateServicesCarrier | boolean | No | Private services carrier flag |

**Validation Rules:**
- `CarrierName` must be unique
- `Type` determines routing behavior

**Example JSON:**
```json
{
  "ID": 101,
  "CarrierName": "Premium Routes UK",
  "Enabled": true,
  "Type": "route",
  "ClosedLoopCarrier": false,
  "PrivateServicesCarrier": false
}
```

**Relationships:**
- Referenced by `LCR_Bands` via `CarrierID`
- Referenced by `LCR_CarrierGateway` via `CarrierID`

---

### LCR_Bands

LCR rate bands/destinations for carrier pricing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key - Band ID |
| BandName | string | Yes | Band/destination name |
| CarrierID | int | Yes | Foreign key to Carriers |
| Type | string | Yes | Primary band type |
| CountryCode | string | No | Country code |
| Enabled | enum | Yes | Band enabled: `Yes`/`No` |

**Validation Rules:**
- `BandName` should describe the destination (e.g., "UK Mobile", "US Landline")
- `CountryCode` should be ISO 3166-1 alpha-2

**Example JSON:**
```json
{
  "ID": 501,
  "BandName": "UK Mobile - All Networks",
  "CarrierID": 101,
  "Type": "Mobile",
  "CountryCode": "GB",
  "Enabled": "Yes"
}
```

**Relationships:**
- Foreign key to `LCR_Carriers` via `CarrierID`
- Referenced by `LCR_Numbers` via `BandID`
- Referenced by `LCR_LCRRates` via `BandID`

---

### LCR_Numbers

LCR number prefix lookup table for routing decisions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key - Number ID |
| Number | string | Yes | Number prefix pattern |
| BandID | int | Yes | Foreign key to Bands |
| Enabled | enum | Yes | Number enabled: `Yes`/`No` |
| OrgID | int | No | Organization ID for private numbers |

**Validation Rules:**
- `Number` is a prefix pattern for matching dialed numbers
- `OrgID` of 0 or null indicates a global number pattern
- Longer prefixes take precedence in routing

**Example JSON:**
```json
{
  "ID": 10001,
  "Number": "447",
  "BandID": 501,
  "Enabled": "Yes",
  "OrgID": 0
}
```

**Relationships:**
- Foreign key to `LCR_Bands` via `BandID`
- Optional foreign key to `Orgs` via `OrgID`

---

### LCR_LCRRates

LCR rate definitions with pricing details.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key - Rate ID |
| BandID | int | Yes | Foreign key to Bands |
| Rate | decimal | Yes | Per minute rate |
| Setup | decimal | No | Setup/connection charge |
| Currency | string | Yes | Currency code |
| Period | string | No | Rate period type |
| Start | datetime | Yes | Rate effective start date |
| Enabled | enum | Yes | Rate enabled: `Yes`/`No` |
| FormatNumber | string | No | Number format rule |
| FormatCLI | string | No | CLI format rule |
| ABandID | int | No | A-number band ID for CLI-based rating |

**Validation Rules:**
- `Rate` must be a non-negative decimal
- `Currency` should be a valid ISO 4217 currency code
- `Start` determines when the rate becomes effective

**Example JSON:**
```json
{
  "ID": 20001,
  "BandID": 501,
  "Rate": 0.0125,
  "Setup": 0.005,
  "Currency": "GBP",
  "Period": "Peak",
  "Start": "2024-01-01 00:00:00",
  "Enabled": "Yes",
  "FormatNumber": "E164",
  "FormatCLI": "E164",
  "ABandID": null
}
```

**Relationships:**
- Foreign key to `LCR_Bands` via `BandID`
- Optional foreign key to `LCR_Bands` via `ABandID` for CLI-based rating

---

### LCR_CarrierGateway

LCR carrier gateway configurations for routing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Primary key - Gateway ID |
| CarrierID | int | Yes | Foreign key to Carriers |
| Enabled | boolean | Yes | Gateway enabled |
| Prefix | string | No | Dial prefix to add |
| Suffix | string | No | Dial suffix to add |
| ChannelVars | string | No | FreeSWITCH channel variables |
| PrivacyClass | string | No | Privacy classification level |
| PCIZone | string | No | PCI compliance zone |
| ConcCalls | int | No | Concurrent call limit |
| Reliability | int | No | Reliability weighting (higher = more reliable) |
| PingGateway | enum | No | Ping gateway for health check: `YES`/`NO` |
| DataCentre | string | No | Data center locations (CSV) |
| CarrierGroup | string | No | Carrier groups (CSV) |

**Validation Rules:**
- `ConcCalls` must be a positive integer
- `Reliability` typically ranges from 0-100
- `DataCentre` and `CarrierGroup` are comma-separated lists

**Example JSON:**
```json
{
  "ID": 3001,
  "CarrierID": 101,
  "Enabled": true,
  "Prefix": "00",
  "Suffix": "",
  "ChannelVars": "absolute_codec_string=PCMA,PCMU",
  "PrivacyClass": "Standard",
  "PCIZone": "UK",
  "ConcCalls": 100,
  "Reliability": 95,
  "PingGateway": "YES",
  "DataCentre": "LON1,LON2",
  "CarrierGroup": "Primary,Failover"
}
```

**Relationships:**
- Foreign key to `LCR_Carriers` via `CarrierID`
- Referenced by `LCR_CarrierGatewayHealth` via `ID`

---

### LCR_CarrierGatewayHealth

LCR gateway health monitoring records.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ID | int | Yes | Foreign key to CarrierGateway |
| DataCentre | string | Yes | Data center location |
| Healthy | enum | Yes | Health status: `YES`/`NO` |
| LastUpdate | datetime | Yes | Last health check timestamp |

**Validation Rules:**
- Composite key of `ID` and `DataCentre`
- `LastUpdate` is system-managed

**Example JSON:**
```json
{
  "ID": 3001,
  "DataCentre": "LON1",
  "Healthy": "YES",
  "LastUpdate": "2024-02-15 14:32:45"
}
```

**Relationships:**
- Foreign key to `LCR_CarrierGateway` via `ID`

---

### WholesaleCallCostCache

Cached wholesale call costs used for fraud detection and real-time cost monitoring.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrgID | int | Yes | Organization ID |
| Cost | decimal | Yes | Accumulated cost amount |
| Time | datetime | Yes | Cost timestamp |

**Validation Rules:**
- `Cost` is aggregated over a time window
- Used for real-time fraud detection and alerting

**Example JSON:**
```json
{
  "OrgID": 1234,
  "Cost": 542.75,
  "Time": "2024-02-15 14:00:00"
}
```

**Relationships:**
- Foreign key to `Orgs` via `OrgID`

---

## Subscription Models

### Subscription

Subscription entity for monitoring SIP URIs and managing event subscriptions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| FromDevID | int | Yes | Subscriber device ID |
| FromTag | string | Yes | SIP From tag |
| CallID | string | Yes | SIP Call-ID |
| Expires | int | Yes | Seconds until subscription expiry |
| Event | string | Yes | Event type: `dialog`, `message-summary` |
| RegFSPath | string | No | Registration FreeSWITCH path |
| RegExpires | int | No | Registration expiry in seconds |
| SubscriberURI | string | Yes | Subscriber SIP URI |
| TargetURI | string | Yes | Target SIP URI being monitored |
| ToDevID | int | No | Target device ID |
| ToSIPID | int | No | Target SIP URI ID |

**Validation Rules:**
- `Event` must be a valid SIP event type
- `Expires` must be a positive integer
- `CallID` must be unique per active subscription

**Example JSON:**
```json
{
  "FromDevID": 5001,
  "FromTag": "as73h4k2j",
  "CallID": "a84b4c76e66710@192.168.1.100",
  "Expires": 3600,
  "Event": "dialog",
  "RegFSPath": "192.168.10.50",
  "RegExpires": 300,
  "SubscriberURI": "sip:1001@example.com",
  "TargetURI": "sip:1002@example.com",
  "ToDevID": 5002,
  "ToSIPID": 2002
}
```

**Relationships:**
- Foreign key to `Devices` via `FromDevID` and `ToDevID`
- Foreign key to `SIPURI` via `ToSIPID`

---

### SubscriptionService_Model

Service model for managing subscriptions programmatically.

This is a service class that provides methods for subscription management operations. It does not have persistent fields but operates on `Subscription` entities.

**Common Use Cases:**
- Creating new event subscriptions
- Renewing existing subscriptions
- Terminating subscriptions
- Querying active subscriptions for a device or URI

---

## Organization Billing Fields (from Orgs model)

The `Orgs` model contains several billing-relevant fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| CallCostLimit | decimal | No | Maximum call cost limit for fraud protection |
| BillingOrgID | int | No | ID of organization responsible for billing |
| JBillingID | string | No | External JBilling system ID |
| Payment | string | No | Payment method/status |
| Balance | decimal | No | Current account balance |
| CreditLimit | decimal | No | Credit limit for the organization |
| MarginLevel | string | No | Margin level: `Custom` or predefined level |
| OrgBillsChild | boolean | No | Whether this org bills child organizations |

**Example JSON (billing fields):**
```json
{
  "OrgID": 1234,
  "CallCostLimit": 5000.00,
  "BillingOrgID": 100,
  "JBillingID": "JB-12345",
  "Payment": "DirectDebit",
  "Balance": 1250.50,
  "CreditLimit": 10000.00,
  "MarginLevel": "Gold Partner",
  "OrgBillsChild": true
}
```

---

## Common Use Cases

### 1. Setting Up a New Service Subscription

```json
// 1. Create OrgService
{
  "OrgID": 1234,
  "ServiceID": 15,
  "Status": "Active",
  "StartDate": "2024-02-01",
  "EndDate": "0000-00-00"
}

// 2. Assign Rate to Service
{
  "OSID": 5002,
  "RID": 2001,
  "Quantity": 10,
  "Margin": 15.00,
  "Discount": 0.00
}
```

### 2. Configuring Reseller Margins

```json
{
  "OrgID": 5678,
  "Type": "Silver Partner",
  "Service": 20.00,
  "ServiceOption": 15.00,
  "RatePlan": 10.00,
  "Support": 25.00,
  "Additional": 12.00,
  "Hardware": 8.00
}
```

### 3. LCR Rate Configuration

```json
// Create Band
{
  "BandName": "France Mobile",
  "CarrierID": 101,
  "Type": "Mobile",
  "CountryCode": "FR",
  "Enabled": "Yes"
}

// Add Number Prefixes
{
  "Number": "336",
  "BandID": 502,
  "Enabled": "Yes"
}

// Configure Rate
{
  "BandID": 502,
  "Rate": 0.0285,
  "Setup": 0.01,
  "Currency": "EUR",
  "Start": "2024-02-01 00:00:00",
  "Enabled": "Yes"
}
```

---

## Related Documentation

- [Identity Models](identity.md) - User and organization authentication
- [Telephony Models](telephony.md) - SIP trunks and call routing
- [Configuration Models](configuration.md) - System configuration
- [Models Overview](README.md) - Complete model reference