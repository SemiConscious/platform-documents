# Data Models Overview

## Introduction

The schema-api service provides a comprehensive data model supporting VoIP telephony operations, device management, billing processes, and API access control. This document serves as an index to all 18 data models organized by functional domain.

## Data Architecture Overview

The schema-api data layer is organized into four primary domains:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        schema-api Data Layer                        │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│   VoIP Domain   │ Device Domain   │ Billing/Audit   │  Permissions  │
├─────────────────┼─────────────────┼─────────────────┼───────────────┤
│ • Voicemail     │ • Devices       │ • API Audit     │ • API Policy  │
│ • Dial Plans    │ • Device Config │ • ADDAC/ARUDD   │ • Base Perms  │
│ • Phone Numbers │ • Device Maps   │ • Billing Procs │               │
│                 │ • Monitoring    │ • Error Logs    │               │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
```

## Model Categories

### VoIP & Telephony Models
**6 models** | [Detailed Documentation →](models/voip-models.md)

Core telephony functionality including voicemail management, dial plan configuration, and phone number associations.

| Model | Purpose |
|-------|---------|
| `voicemail_msgs` | Voicemail message storage and metadata |
| `voicemail_prefs` | User voicemail preferences and greetings |
| `DialPlanPolicies` | Call routing policy definitions |
| `DialPlanItem` | Individual dial plan routing rules |
| `AssocNumbers` | Phone number assignments to users/orgs |
| `DataConnectorCredentials` | CRM integration credentials (Salesforce, Dynamics, Sugar) |

---

### Device Management Models
**5 models** | [Detailed Documentation →](models/device-models.md)

Physical and virtual SIP device configuration, provisioning, and monitoring.

| Model | Purpose |
|-------|---------|
| `Devices` | SIP devices and trunk definitions |
| `DevicesVars` | Device-specific configuration variables |
| `DeviceMap` | SIP URI to device mappings |
| `DeviceMonitoring` | Device usage statistics and call metrics |
| `BrandManagement` | Multi-tenant brand configuration |

---

### Billing & Audit Models
**5 models** | [Detailed Documentation →](models/billing-audit-models.md)

Financial transaction processing, direct debit management, and audit logging.

| Model | Purpose |
|-------|---------|
| `APIAudit` | API request logging and tracking |
| `APIErrorLog` | API error capture and diagnostics |
| `ADDAC` | Direct debit amendments and cancellations |
| `ARUDD` | Unpaid direct debit returns |
| `BillingProcesses` | Billing job scheduling and status |

---

### Permissions & Access Control Models
**2 models** | [Detailed Documentation →](models/permissions-models.md)

API access control and permission management.

| Model | Purpose |
|-------|---------|
| `APIPolicy` | IP-based API access policies per organization |
| `BasePermissions` | Core permission definitions and bit flags |

---

## Cross-Domain Relationships

### Organization-Centric Design

Most models reference `OrgID` as a foreign key, establishing organization as the primary tenant boundary:

```
                    ┌──────────────┐
                    │ Organization │
                    │   (OrgID)    │
                    └──────┬───────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Devices    │   │ AssocNumbers │   │  APIPolicy   │
│   ADDAC      │   │ DialPlan*    │   │ DataConnector│
│   ARUDD      │   │ Voicemail*   │   │ BrandMgmt    │
└──────────────┘   └──────────────┘   └──────────────┘
```

### Key Relationship Chains

1. **Device → SIP → Voicemail**: Devices connect via DeviceMap to SIP URIs, which receive voicemail stored in voicemail_msgs

2. **User → Numbers → Access**: Users own AssocNumbers which define voicemail access policies

3. **DialPlan Hierarchy**: DialPlanPolicies contain DialPlanItems in a parent-child tree structure via `ParentDPIID`

4. **Billing Flow**: ADDAC and ARUDD records track direct debit lifecycle, monitored by BillingProcesses

## Model Count by Domain

| Domain | Model Count | Primary Key Types |
|--------|-------------|-------------------|
| VoIP & Telephony | 6 | Composite, Auto-increment |
| Device Management | 5 | Auto-increment, Composite |
| Billing & Audit | 5 | Auto-increment, Composite |
| Permissions | 2 | Composite |
| **Total** | **18** | |

## Quick Reference: All Models

| Model | Domain | Primary Key |
|-------|--------|-------------|
| `ADDAC` | Billing | `(ADDACFileID, reference)` |
| `APIAudit` | Audit | None (log table) |
| `APIErrorLog` | Audit | `EID` |
| `APIPolicy` | Permissions | `(IPAddress, OrgID)` |
| `ARUDD` | Billing | `(ARUDDFileID, ref)` |
| `AssocNumbers` | VoIP | `Val` |
| `BasePermissions` | Permissions | `(Object, Action, Bit)` |
| `BillingProcesses` | Billing | `BPID` |
| `BrandManagement` | Device | `BrandID` |
| `DataConnectorCredentials` | VoIP | `DCCID` |
| `DeviceMap` | Device | `(SIPID, DevID)` |
| `DeviceMonitoring` | Device | `(Hour, DevID)` |
| `Devices` | Device | `DevID` |
| `DevicesVars` | Device | `(DevID, Section, Field)` |
| `DialPlanItem` | VoIP | `DPIID` |
| `DialPlanPolicies` | VoIP | `DPPID` |
| `voicemail_msgs` | VoIP | `uuid` |
| `voicemail_prefs` | VoIP | `(username, domain)` |

## Next Steps

For detailed model specifications including field definitions, validation rules, and JSON examples, refer to the domain-specific documentation:

- [VoIP Models Documentation](models/voip-models.md) - Voicemail, dial plans, phone numbers
- [Device Models Documentation](models/device-models.md) - SIP devices, configuration, monitoring
- [Billing & Audit Models Documentation](models/billing-audit-models.md) - Financial transactions, logging
- [Permissions Models Documentation](models/permissions-models.md) - Access control, policies