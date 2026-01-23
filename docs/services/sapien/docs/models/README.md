# Data Models Overview

This document provides a high-level overview of the data architecture in the Sapien service, organizing all 44 data models by domain and providing navigation to detailed documentation.

## Architecture Overview

The Sapien service implements a multi-layered data architecture supporting:

- **Real-time WebSocket Communication** - ESL (Event Socket Library) listener for telephony events
- **OAuth 2.0 Authentication** - Complete token-based authentication and authorization
- **Multi-tenant Organization Management** - Rate limiting and resource isolation
- **Comprehensive Audit Logging** - Event tracking and compliance support
- **Archiving and Retention** - Recording storage, legal hold, and deletion workflows

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Applications                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  WebSocket   │ │  REST API    │ │  OAuth 2.0   │
            │  Server      │ │  Endpoints   │ │  Endpoints   │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                    Core Domain Models                        │
            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
            │  │   Person    │  │   User      │  │   Organisation      │  │
            │  └─────────────┘  └─────────────┘  └─────────────────────┘  │
            └─────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  Event Log   │ │  Retention   │ │  Rate Limit  │
            │  System      │ │  System      │ │  System      │
            └──────────────┘ └──────────────┘ └──────────────┘
```

## Model Categories

### 1. Core Domain Models
**Count:** 2 models

Foundation entities representing people and business objects within the system.

| Model | Purpose |
|-------|---------|
| `Person` | Contact information and personal data |
| `EndOfWorldErrorException` | Custom REST exception handling |

→ [Detailed Documentation: Core Models](./core-models.md)

---

### 2. Authentication & Authorization Models
**Count:** 11 models

Complete OAuth 2.0 implementation with session management and multi-factor authentication support.

| Model | Purpose |
|-------|---------|
| `AccessToken` | OAuth access token storage and validation |
| `RefreshToken` | OAuth refresh token for token renewal |
| `AuthCode` | OAuth authorization code grant flow |
| `Client` | OAuth client application registration |
| `CoreApiSession` | API session tracking and management |
| `RedmatterUserInterface` | User interface with SSO/MFA capabilities |
| `AbstractVoter` | Security voter base class for authorization |
| `AccessTokenRepositoryInterface` | Token repository operations |

→ [Detailed Documentation: Authentication Models](./authentication-models.md)

---

### 3. Infrastructure & Configuration Models
**Count:** 31 models

System infrastructure including WebSocket servers, Symfony bundles, Doctrine types, and database abstractions.

#### WebSocket/ESL Subsystem
| Model | Purpose |
|-------|---------|
| `Server` | WebSocket server for ESL listener |
| `Handler` | Connection and message processing |
| `Responses` | ESL event response generation |
| `RecordedTrafficEntry` | Traffic recording data structure |
| `CommandMessage` | WebSocket command protocol |
| `StartCapturingTrafficValue` | Traffic capture configuration |

#### Symfony Bundles
| Model | Purpose |
|-------|---------|
| `AppKernel` | Application kernel configuration |
| `RedmatterSapienBundle` | Main Sapien bundle |
| `RedmatterUserBundle` | User functionality bundle |
| `RedmatterBlobStorageBundle` | Blob storage bundle |
| `RedmatterHelloBundle` | Development/test bundle |

#### Doctrine Types
| Model | Purpose |
|-------|---------|
| `PrimaryKeyDateTimeType` | Custom datetime primary key type |
| `UuidType` | UUID column type |

#### Rate Limiting
| Model | Purpose |
|-------|---------|
| `OrganisationApiRateLimit` | Rate limit configuration entity |
| `OrgAPIRateLimit` | Rate limit state table |
| `Orgs` | Organization rate limit settings |

#### Event Logging & Audit
| Model | Purpose |
|-------|---------|
| `EventLog` | System event logging entity |
| `EventLogRepositoryInterface` | Event logging operations |
| `Audit` | File access audit trail |

#### Archiving & Retention
| Model | Purpose |
|-------|---------|
| `Retention` | Archiving retention configuration |
| `DeleteRequest` | Deletion request tracking |
| `DeleteRequestItems` | Individual deletion items |

#### Database Abstractions
| Model | Purpose |
|-------|---------|
| `DbalEntityFieldsCollection` | Field mapping utilities |
| `DbalRepositoryConnectionInterface` | Connection configuration |
| `DbalEntityInterface` | Entity interface contract |
| `SwitchableDatabaseConnectionInterface` | Runtime database switching |

→ [Detailed Documentation: Infrastructure Models](./infrastructure-models.md)

---

## Cross-Domain Relationships

### Authentication Flow
```
Client ──creates──▶ AccessToken ──belongs to──▶ User
                         │
                         ▼
                  CoreApiSession ──tracks──▶ User Activity
                         │
                         ▼
                    EventLog ──records──▶ Auth Events
```

### Rate Limiting Flow
```
Organisation ──configures──▶ OrganisationApiRateLimit
                                    │
                                    ▼
              API Request ──checks──▶ OrgAPIRateLimit (state)
                                    │
                                    ▼
                            Allow/Deny Request
```

### Audit & Compliance Flow
```
User Action ──triggers──▶ EventLog
      │
      ├──▶ Retention Access ──records──▶ Audit
      │
      └──▶ Delete Request ──creates──▶ DeleteRequestItems
                                │
                                ▼
                          EventLog (audit trail)
```

### WebSocket Communication Flow
```
Client Connection ──▶ Server ──delegates──▶ Handler
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
          RecordedTrafficEntry         CommandMessage              Responses
                                              │
                                              ▼
                                StartCapturingTrafficValue
```

## Database Architecture

The system uses multiple database schemas for multi-tenancy:

| Schema | Purpose | Key Tables |
|--------|---------|------------|
| `Org` | Organization data | `Orgs`, `OrgAPIRateLimit` |
| `ArchivingRetention` | Recording lifecycle | `Audit_X`, `DeleteRequest_X`, `DeleteRequestItems_X` |

*Note: `_X` suffix indicates sharded tables by organization*

## Detailed Documentation Index

| Document | Models Covered | Description |
|----------|---------------|-------------|
| [Core Models](./core-models.md) | 2 | Person entity and exception handling |
| [Authentication Models](./authentication-models.md) | 11 | OAuth 2.0 tokens, sessions, and authorization |
| [Infrastructure Models](./infrastructure-models.md) | 31 | WebSocket, bundles, types, and database layers |

---

## Quick Reference

### Entity-to-Table Mapping

| Entity | Database Table |
|--------|---------------|
| `OrganisationApiRateLimit` | `Org.OrgAPIRateLimit` |
| `EventLog` | `EventLog` (auto-generated ID) |
| `Audit` | `ArchivingRetention.Audit_X` |
| `DeleteRequest` | `ArchivingRetention.DeleteRequest_X` |
| `DeleteRequestItems` | `ArchivingRetention.DeleteRequestItems_X` |

### Custom Doctrine Types

| Type Name | Class | Usage |
|-----------|-------|-------|
| `pkdatetime` | `PrimaryKeyDateTimeType` | DateTime as primary key |
| `uuid` | `UuidType` | UUID column storage |