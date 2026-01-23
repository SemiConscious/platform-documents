# Data Models Overview

This document provides a comprehensive index of all data models used in the CDC (Change Data Capture) pipeline service. The pipeline processes database change events from Kinesis streams, enriches them with organizational context, and publishes normalized events to EventBridge.

## Data Architecture Overview

The CDC pipeline follows a layered data architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Kinesis Stream                                  │
│                         (Raw CDC Events)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Decoding Layer                                     │
│              KinesisDecodedData, KinesisRecordMetadata                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Enrichment Layer                                    │
│         Adds orgId/userId context via database lookups                       │
│              ExtendedKinesisDecodedData, Enrichment                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Domain Record Layer                                   │
│     UsersRecord, CallStatusRecord, PoolRecord, ProfilesRecord, etc.          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Normalization Layer                                   │
│                    NormalizedRecord, RecordMetadata                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             EventBridge                                      │
│                       (Published CDC Events)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Model Categories

The 75 data models in this service are organized into the following categories:

| Category | Model Count | Description |
|----------|-------------|-------------|
| [Domain Records](#domain-records) | 12 | Business entity representations for CDC events |
| [Kinesis/Stream Models](#kinesisstream-models) | 8 | Raw and decoded stream data structures |
| [Enrichment Models](#enrichment-models) | 10 | Data enrichment processors and context models |
| [Event Models](#event-models) | 6 | EventBridge event structures and metadata |
| [Configuration Models](#configuration-models) | 12 | Environment, credentials, and service configuration |
| [Infrastructure Models](#infrastructure-models) | 8 | AWS service integration models (SSM, DynamoDB) |
| [Utility Models](#utility-models) | 10 | Logging, redaction, and HTTP utilities |
| [Enumerations](#enumerations) | 9 | Type-safe constants and status values |

---

## Domain Records

Domain records represent the core business entities tracked by the CDC pipeline. Each record type corresponds to a database table and captures create, update, and delete operations.

| Model | Domain | Description |
|-------|--------|-------------|
| `UsersRecord` | Identity | User accounts with authentication and profile data |
| `OrgsRecord` | Identity | Organization/tenant configurations |
| `GroupsRecord` | Identity | User group definitions |
| `UserScopesRecord` | Identity | User permission scopes |
| `ProfilesRecord` | Configuration | Scoped configuration profiles |
| `ChannelsRecord` | Communication | Communication channel configurations |
| `PoolRecord` | Telephony | Phone number pool entries with billing info |
| `CallStatusRecord` | Telephony | Active call status with SIP details |
| `CallCenterAgentRecord` | Call Center | Call center agent records |
| `CallCenterQueueRecord` | Call Center | Queue entries with callback settings |
| `AvailabilityLogRecord` | Call Center | Agent availability tracking |
| `GroupMapsLogRecord` | Call Center | Group mapping audit logs |

**Detailed documentation:** [docs/models/records.md](./records.md)

---

## Kinesis/Stream Models

These models handle the ingestion and decoding of raw Kinesis stream records from AWS DMS (Database Migration Service).

| Model | Purpose |
|-------|---------|
| `KinesisDecodedData` | Decoded payload with data and metadata |
| `KinesisDecodedMetadata` | Stream record metadata (table, schema, operation) |
| `KinesisRecordMetadata` | Kinesis-specific metadata (partition key, sequence) |
| `KinesisRecordAttributes` | Combined record attributes container |
| `ExtendedKinesisStreamRecord` | AWS record extended with correlation ID |
| `ExtendedKinesisDecodedData` | Decoded data with enrichment |
| `ExtendedKinesisRecordAttributes` | Full record with all extensions |
| `RecordData` | Before/after state diff container |

**Detailed documentation:** [docs/models/events.md](./events.md)

---

## Enrichment Models

Enrichment models add organizational context (orgId, userId) to CDC records through database lookups or data extraction.

| Model | Strategy | Description |
|-------|----------|-------------|
| `Enrichment` | — | Base enrichment data structure |
| `RecordsEnrichment` | Abstract | Base class for enrichment implementations |
| `UsersEnrichment` | Direct Mapping | Maps HomeOrgID → orgId, ID → userId |
| `UserScopesEnrichment` | Direct Extract | Extracts IDs from record data |
| `GroupMapsLogEnrichment` | Database Lookup | Queries repository for orgId by groupId |
| `CallCenterAgentEnrichment` | Conditional | Assigns userId based on agent type |
| `CallCenterQueueEnrichment` | Partial | Extracts orgId only (userId always null) |
| `CallStatusEnrichment` | Direct Extract | Extracts both IDs from record |
| `AvailabilityLogEnrichment` | Direct Extract | Extracts both IDs from record |
| `PoolEnrichment` | Direct Extract | Extracts both IDs from record |

**Detailed documentation:** [docs/models/records.md](./records.md)

---

## Event Models

Event models define the structure of normalized events published to EventBridge.

| Model | Purpose |
|-------|---------|
| `NormalizedRecord` | EventBridge event envelope |
| `RecordMetadata` | Event metadata (service, timestamp, correlation) |
| `RecordType` | Abstract base for record type processing |
| `EventBridgeEventFailure` | Batch item failure response |
| `LambdaResponse` | Lambda response with batch failures |
| `EventBridgeHC` | Health check status enum |

**Detailed documentation:** [docs/models/events.md](./events.md)

---

## Configuration Models

Configuration models manage environment settings, credentials, and service parameters.

| Model | Purpose |
|-------|---------|
| `Environment` | Deployment environment enum (LOCAL, DEV, QA, PRD) |
| `EnvVariables` | Runtime environment configuration |
| `DatabaseCredentials` | Database connection parameters |
| `SSMConfigParams` | AWS SSM client configuration |
| `SSMDBParametersName` | SSM parameter path mappings |
| `ParameterResponse` | SSM parameter retrieval response |
| `ParameterHandlerProps` | SSM parameter handler properties |
| `ParameterOptions` | Optional SSM retrieval parameters |
| `RedactionConfig` | Redaction service configuration |
| `ObjectRedaction` | Runtime redaction settings |
| `LoggerConfigOptions` | Logger service configuration |
| `LoggerRedaction` | Logger redaction subset |

**Detailed documentation:** [docs/models/configuration.md](./configuration.md)

---

## Infrastructure Models

Infrastructure models support AWS service integrations and database operations.

| Model | Service | Purpose |
|-------|---------|---------|
| `DynamoDBActionParams` | DynamoDB | Operation parameters for queries |
| `PreparedQuery` | PostgreSQL | Prepared SQL query definition |
| `DatabaseInstanceStatus` | RDS | Database availability status |
| `ProfilesGetOrgResponse` | Database | Profiles org lookup response |
| `GroupsMapLogGetOrgResponse` | Database | Group maps org lookup response |
| `ChannelsGetOrgAndUserResponse` | Database | Channels org/user lookup response |
| `IRequester` | HTTP | HTTP client interface |
| `HeaderItem` | HTTP | HTTP header key-value pair |

**Detailed documentation:** [docs/models/configuration.md](./configuration.md)

---

## Utility Models

Utility models support cross-cutting concerns like logging, redaction, and testing.

| Model | Category | Purpose |
|-------|----------|---------|
| `IRedactor` | Security | Generic redaction interface |
| `RegexRedaction` | Security | Regex-based redaction config |
| `MockedRecordType` | Testing | Test mock for RecordType |

**Detailed documentation:** [docs/models/configuration.md](./configuration.md)

---

## Enumerations

Type-safe enumerations used throughout the pipeline.

| Enum | Values | Purpose |
|------|--------|---------|
| `DatabaseActionEnum` | CREATE, UPDATE, DELETE, UNKNOWN | CRUD operation types |
| `RecordTypeEnum` | 12 record types | Supported CDC record types |
| `Environment` | LOCAL, DEV, QA, PRD | Deployment environments |
| `EventBridgeHC` | OK, IN_ALARM, UNKNOWN | Health check status |
| `DatabaseInstanceStatus` | AVAILABLE, UNAVAILABLE | Database availability |

---

## Model Relationships

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           RELATIONSHIP DIAGRAM                                │
└──────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │  RecordTypeEnum     │
                    │  (12 record types)  │
                    └──────────┬──────────┘
                               │ identifies
                               ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ KinesisDecoded  │───▶│  RecordType     │───▶│ NormalizedRecord│
│     Data        │    │   (abstract)    │    │                 │
└────────┬────────┘    └────────┬────────┘    └─────────────────┘
         │                      │
         │ extends              │ extends
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ ExtendedKinesis │    │  Domain Records │
│   DecodedData   │    │ (UsersRecord,   │
└────────┬────────┘    │  PoolRecord,    │
         │             │  etc.)          │
         │ contains    └─────────────────┘
         ▼
┌─────────────────┐
│   Enrichment    │◀───────────────────────┐
│  (orgId,userId) │                        │
└─────────────────┘                        │
         ▲                                 │
         │ produced by                     │
         │                                 │
┌─────────────────┐    ┌─────────────────┐ │
│ RecordsEnrich-  │───▶│ Database        │─┘
│   ment          │    │ Repositories    │
│ (10 impl.)      │    │                 │
└─────────────────┘    └─────────────────┘
```

### Key Relationships

1. **KinesisDecodedData → ExtendedKinesisDecodedData**: Raw stream data is extended with enrichment context
2. **RecordTypeEnum → Domain Records**: Each enum value maps to a specific record class
3. **RecordsEnrichment → Enrichment**: Enrichment processors produce Enrichment objects
4. **RecordType → NormalizedRecord**: Record types transform to normalized EventBridge events
5. **DatabaseCredentials → Repositories**: Credentials configure database access for enrichment lookups

---

## Quick Reference: Model by Use Case

| Use Case | Primary Models |
|----------|----------------|
| Processing incoming CDC events | `KinesisDecodedData`, `KinesisRecordMetadata` |
| Adding org/user context | `Enrichment`, `*Enrichment` classes |
| Publishing to EventBridge | `NormalizedRecord`, `RecordMetadata` |
| Handling failures | `EventBridgeEventFailure`, `LambdaResponse` |
| Database queries | `DatabaseCredentials`, `PreparedQuery` |
| Configuration management | `EnvVariables`, `SSMConfigParams` |
| Security/compliance | `RedactionConfig`, `IRedactor` |

---

## Detailed Documentation

For complete field definitions, validation rules, and examples, see:

- **[Domain Records & Enrichment](./records.md)** - All 12 domain record types and enrichment processors
- **[Events & Streaming](./events.md)** - Kinesis, EventBridge, and event processing models
- **[Configuration & Infrastructure](./configuration.md)** - Environment, credentials, AWS integrations