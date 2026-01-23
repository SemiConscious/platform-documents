# Data Models Overview

## Introduction

The platform-dgapi service implements a sophisticated data architecture for processing Call Detail Records (CDR) and managing asynchronous task execution. The data model is designed around two core concepts:

1. **Normalized CDR Storage**: Standardized XML-based call record storage with date-partitioned tables
2. **Task Processing System**: A flexible, priority-based task queue supporting multiple task types

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CDR Input Layer                              │
│                    (cdr-normalized XML Schema)                      │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage Layer                                  │
│  ┌─────────────────────┐    ┌──────────────────┐                   │
│  │   normalized_cdrs   │◄───│   tasks_data     │                   │
│  │   (CDR Storage)     │    │ (Extended Data)  │                   │
│  └─────────┬───────────┘    └──────────────────┘                   │
│            │                         ▲                              │
│            │                         │                              │
│            ▼                         │                              │
│  ┌─────────────────────┐    ┌───────┴──────────┐                   │
│  │    Task_Model       │───►│   tasks_error    │                   │
│  │   (Base Tasks)      │    │ (Error Tracking) │                   │
│  └─────────────────────┘    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Specialized Task Models                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │  Email   │ │   SMS    │ │  Voicemail   │ │   CDRToSGAPI     │   │
│  │  Model   │ │  Model   │ │    Model     │ │     Model        │   │
│  └──────────┘ └──────────┘ └──────────────┘ └──────────────────┘   │
│  ┌──────────────────┐ ┌────────────────────────────────────────┐   │
│  │  CBFinish_Model  │ │          Generic_Model                 │   │
│  └──────────────────┘ └────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Response Layer                                │
│                   (TaskStatusResponse)                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Model Categories

### Task Models

The task processing system provides a hierarchical model structure for managing asynchronous operations.

| Model | Purpose |
|-------|---------|
| `Task_Model` | Base model defining common task properties including scheduling, retry logic, and status tracking |
| `tasks_error` | Error tracking and logging for failed task attempts |
| `tasks_data` | Extended XML data storage for tasks requiring additional payload |
| `Generic_Model` | Flexible task type for custom operations |
| `CBFinish_Model` | Call buffering completion tasks |

**Detailed Documentation**: [Task Models](task-models.md)

### Messaging Models

Models supporting notification delivery through various channels.

| Model | Purpose |
|-------|---------|
| `Email_Model` | Email delivery task extending base task model |
| `Sms_Model` | SMS delivery task extending base task model |
| `Voicemail_Model` | Voicemail notifications supporting both email and SMS channels |

**Detailed Documentation**: [Messaging Models](messaging-models.md)

### CDR Models

Core models for Call Detail Record processing and storage.

| Model | Purpose |
|-------|---------|
| `normalized_cdrs` | Primary storage table for normalized CDR data |
| `cdr-normalized` | XML schema defining CDR input structure |
| `CDRToSGAPI_Model` | Task model for CDR processing and SGAPI integration |
| `TaskStatusResponse` | API response schema for task status queries |

**Detailed Documentation**: [CDR Models](cdr-models.md)

## Model Relationships

### Primary Relationships

```
normalized_cdrs (1) ◄──────────── (N) Task_Model
       │                                  │
       │                                  ├──────► (1) tasks_error
       │                                  │
       │                                  └──────► (1) tasks_data
       │
       └── Contains embedded task definitions from cdr-normalized XML
```

### Inheritance Hierarchy

The task system uses an inheritance pattern where specialized models extend `Task_Model`:

```
Task_Model (Base)
    ├── Email_Model
    ├── Sms_Model
    ├── Voicemail_Model
    ├── CDRToSGAPI_Model
    ├── CBFinish_Model
    └── Generic_Model
```

### Key Foreign Key Relationships

| Source Table | Target Table | Relationship |
|--------------|--------------|--------------|
| `Task_Model.id_normalized_cdrs` | `normalized_cdrs.id` | Many-to-One |
| `tasks_error.id_tasks` | `Task_Model.id` | One-to-One |
| `tasks_data.id_tasks` | `Task_Model.id` | One-to-One |

## Data Flow

1. **CDR Ingestion**: Raw CDR data arrives as XML conforming to the `cdr-normalized` schema
2. **Normalization**: CDR is parsed and stored in date-partitioned `normalized_cdrs` tables
3. **Task Creation**: Tasks embedded in the CDR XML are extracted and created as `Task_Model` records
4. **Task Execution**: Specialized task models process according to their type and priority
5. **Error Handling**: Failed tasks are tracked in `tasks_error` with retry scheduling
6. **Status Reporting**: `TaskStatusResponse` provides polling-based status updates

## Table Partitioning Strategy

The `normalized_cdrs` table uses date-based partitioning through the `TableSuffix` field:

- Format: `YYYYMMDD`
- Tables are named: `normalized_cdrs_YYYYMMDD`
- Enables efficient data lifecycle management and query performance

## Common Identifiers

Several identifiers are used consistently across models:

| Identifier | Description | Format |
|------------|-------------|--------|
| `rmOrgID` | Organization identifier | Integer |
| `rmUserID` | User identifier | String |
| `uuid` | CDR unique identifier | UUID (stored as binary in DB) |
| `LegUUID` | Call leg identifier | String |

## Detailed Documentation

For complete field specifications, validation rules, and usage examples, refer to:

- **[Task Models](task-models.md)** - Base task model, error tracking, and specialized task types
- **[Messaging Models](messaging-models.md)** - Email, SMS, and Voicemail notification models
- **[CDR Models](cdr-models.md)** - CDR storage, XML schemas, and API response structures