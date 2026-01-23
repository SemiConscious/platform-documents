# Platform API - Data Models Overview

## Introduction

The Platform API provides a comprehensive data model architecture supporting enterprise communication, billing, and identity management. This document serves as the central reference for understanding the data architecture and navigating to detailed model documentation.

## Data Architecture Overview

The Platform API data model is organized around several core domains that work together to provide a complete unified communications platform:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Platform API Data Model                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Identity   │───▶│  Telephony  │◀───│   Billing   │◀───│Configuration│  │
│  │   Models    │    │   Models    │    │   Models    │    │   Models    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                  │                  │                  │          │
│        ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Shared Infrastructure                            │   │
│  │  (Sessions, Permissions, Schedules, Notifications, Storage)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Model Categories

The 100 data models are organized into the following categories:

### 1. Identity & Access Management
**Models:** ~20 | **Documentation:** [docs/models/identity.md](docs/models/identity.md)

Core models for user authentication, authorization, and organizational structure:

| Category | Key Models | Purpose |
|----------|------------|---------|
| Users & Authentication | `Users`, `UserSecurity`, `SessionsX` | User accounts, passwords, sessions |
| Organizations | `Orgs`, `OrgAddress`, `Domain` | Multi-tenant organization hierarchy |
| Groups & Membership | `Group`, `GroupMap`, `GroupMember_*` | User grouping and team structure |
| Permissions | `Permission`, `BasePermission` | Role-based access control |
| External Identity | `UserForeignIdType`, `DataConnectorForeignIdMap` | SSO and external system integration |

### 2. Telephony & Communications
**Models:** ~35 | **Documentation:** [docs/models/telephony.md](docs/models/telephony.md)

Models supporting voice, SIP, and mobile communications:

| Category | Key Models | Purpose |
|----------|------------|---------|
| Devices | `Device`, `Phone`, `PhoneType`, `Phones` | Physical and virtual phone management |
| SIP Infrastructure | `SIPURI`, `SIPTrunk`, `Gateway`, `Route` | SIP routing and trunk configuration |
| Call Control | `CallStatus`, `CallControlService_Model` | Real-time call state management |
| Mobile/VSIM | `VSIMs`, `IMSIs`, `MobileNumbers` | Virtual SIM and mobile number management |
| Voicemail | `VoiceMail`, `VMDropFile` | Voicemail storage and management |
| Call Center | `Skill`, `CallCenterLoginHistory`, `AvailabilityState` | Agent management and routing |
| LCR/Routing | `LCR_Numbers`, `LCR_Bands`, `LCR_Carriers`, `LCR_LCRRates` | Least cost routing |

### 3. Billing & Commercial
**Models:** ~15 | **Documentation:** [docs/models/billing.md](docs/models/billing.md)

Financial and commercial management models:

| Category | Key Models | Purpose |
|----------|------------|---------|
| Rates & Pricing | `Rate`, `Rates`, `LCR_LCRRates` | Service and call pricing |
| Services | `Services`, `OrgServices`, `OrgServicesRates` | Service subscriptions |
| Invoicing | `Invoices`, `Payments` | Billing and payment tracking |
| Margins | `OrgMargins` | Wholesale/retail margin management |
| Billing Config | `BillingPrefs` | Organization billing settings |

### 4. Configuration & System
**Models:** ~30 | **Documentation:** [docs/models/configuration.md](docs/models/configuration.md)

System configuration and operational models:

| Category | Key Models | Purpose |
|----------|------------|---------|
| Storage | `KeyValueStorage` | Generic key-value data storage |
| Scheduling | `Schedule`, `ScheduledEvent` | Time-based automation |
| Notifications | `Notifications`, `NotificationMap` | User notification system |
| Directory | `ClientDirectory`, `DirectoryEntry`, `AssocNumbers` | Contact and number management |
| Data Connectors | `DataConnectorCredentials`, `DataConnectorDependencies` | External system integration |
| Security | `ArchivingPolicyTypes`, `ClientAccess` | Compliance and access control |
| Subscriptions | `Subscription` | SIP presence subscriptions |

## Model Relationships

### Organization Hierarchy

```
Orgs (Parent)
  │
  ├──▶ Orgs (Children)          [ParentID → OrgID]
  ├──▶ Users                    [OrgID]
  ├──▶ Devices                  [OrgID]
  ├──▶ Groups                   [OrgID]
  ├──▶ Domains                  [OrgID]
  ├──▶ OrgServices              [OrgID]
  └──▶ SIPTrunk                 [OrgID]
```

### User-Device-SIP Relationships

```
Users
  │
  ├──▶ Devices                  [Associated via extensions]
  │      │
  │      └──▶ SIPURI            [DevID linkage]
  │
  ├──▶ GroupMap                 [UserID → HoldingGroupID]
  ├──▶ AssocNumbers             [UserID]
  ├──▶ UserSecurity             [ID → UserID]
  └──▶ SessionsX                [UserID]
```

### Telephony Routing Chain

```
LCR_Numbers ──▶ LCR_Bands ──▶ LCR_Carriers ──▶ LCR_CarrierGateway
     │              │              │                   │
     └──────────────┴──────────────┴───────────────────┘
                          │
                    LCR_LCRRates (pricing per band)
```

### Billing Relationships

```
Services
  │
  └──▶ Rates                    [SID → ServiceID]
         │
         └──▶ OrgServicesRates  [RID]
                   │
                   └──▶ OrgServices [OSID → OrgID]
```

## Cross-Domain Dependencies

| Source Domain | Target Domain | Key Relationships |
|--------------|---------------|-------------------|
| Identity | Telephony | Users own Devices, SIPURIs; Groups route calls |
| Identity | Billing | Orgs have OrgServices, BillingPrefs |
| Telephony | Billing | Calls rated via LCR_LCRRates, WholesaleCallCostCache |
| Configuration | Identity | Permissions, Schedules scoped to Orgs/Users |
| Configuration | Telephony | DataConnectors sync with external systems |

## Detailed Documentation

Navigate to category-specific documentation for complete field definitions, validation rules, and examples:

| Document | Coverage | Link |
|----------|----------|------|
| **Identity Models** | Users, Organizations, Groups, Sessions, Permissions | [docs/models/identity.md](docs/models/identity.md) |
| **Telephony Models** | Devices, SIP, Call Control, Mobile, LCR, Voicemail | [docs/models/telephony.md](docs/models/telephony.md) |
| **Billing Models** | Rates, Services, Invoices, Payments, Margins | [docs/models/billing.md](docs/models/billing.md) |
| **Configuration Models** | Storage, Schedules, Notifications, Connectors | [docs/models/configuration.md](docs/models/configuration.md) |

## Common Patterns

### Multi-Tenant Isolation
All models support multi-tenancy through `OrgID` foreign keys. Data is strictly isolated between organizations unless explicitly shared via parent-child relationships.

### Soft Delete & Status Fields
Most entities use `Status` enum fields (`Active`, `Suspended`, etc.) rather than physical deletion, enabling audit trails and recovery.

### Temporal Data
- `Start`/`End` date fields for validity periods
- `Expires` timestamps for time-limited records
- `LastTime`/`LastUpdate` for tracking modifications

### Hierarchical Structures
- Organizations support unlimited nesting via `ParentID`
- Groups support nested membership via `GroupMember_Group`
- Permissions cascade through organizational hierarchy

## API Model Conventions

| Convention | Example | Description |
|------------|---------|-------------|
| Primary Keys | `OrgID`, `UserID`, `DevID` | Unsigned integers, auto-increment |
| Foreign Keys | `OrgID` in `Users` | Same name as referenced PK |
| Status Fields | `Status: enum` | Standardized status values |
| Timestamps | `YYYYMMDDHHMMSS` format | Consistent datetime formatting |
| Boolean Fields | `YES`/`NO` enum | String-based boolean flags |
| Phone Numbers | E.164 format | International number format |