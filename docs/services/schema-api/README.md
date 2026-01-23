# Schema API Overview

[![Database](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Migrations](https://img.shields.io/badge/Migrations-2010--2022-blue)](docs/migration-guide.md)
[![Models](https://img.shields.io/badge/Data%20Models-18-green)](models/README.md)
[![Platform](https://img.shields.io/badge/Platform-VoIP%2FTelecom-orange)]()

> **API Schema definitions service** — The foundational database migration repository that defines all data models and schema structures for a comprehensive telecommunications/VoIP platform with billing, device management, and voicemail capabilities.

---

## Table of Contents

- [Introduction](#introduction)
- [Purpose and Scope](#purpose-and-scope)
- [Architecture Overview](#architecture-overview)
- [Data Models at a Glance](#data-models-at-a-glance)
- [Migration Naming Convention](#migration-naming-convention)
- [How to Use These Schemas](#how-to-use-these-schemas)
- [Getting Started](#getting-started)
- [Documentation Index](#documentation-index)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Introduction

The **schema-api** service serves as the single source of truth for all database schema definitions across our telecommunications platform. This repository contains over a decade of carefully crafted database migrations (2010-2022) that collectively define the data architecture powering VoIP communications, billing operations, device management, and voicemail services.

Unlike traditional application services, `schema-api` is a **schema-only repository** — it doesn't run as a standalone service but instead provides the foundational data structures that all other platform services depend upon. Think of it as the architectural blueprint for your entire data layer.

### Who Should Use This Repository?

- **Backend Developers** building features that require database changes
- **Database Administrators** managing schema deployments and optimizations
- **DevOps Engineers** orchestrating database migrations across environments
- **New Team Members** seeking to understand the platform's data architecture

---

## Purpose and Scope

### What This Repository Provides

| Capability | Description |
|------------|-------------|
| **Database Migrations** | Sequential SQL migration files defining schema evolution |
| **Data Model Definitions** | 18 comprehensive models covering all platform domains |
| **Schema Documentation** | Detailed documentation of tables, relationships, and constraints |
| **Dial Plan Structures** | Complex routing and permissions management schemas |
| **Billing Infrastructure** | Tables supporting usage tracking, invoicing, and API auditing |
| **Device Management** | Schemas for device provisioning, monitoring, and configuration |
| **Voicemail System** | Complete voicemail storage and retrieval data structures |

### Domain Coverage

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCHEMA-API DOMAINS                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   VoIP/Telecom  │     Billing     │      Device Management      │
│                 │                 │                             │
│  • Call routing │  • Usage meters │  • Device registry          │
│  • Dial plans   │  • Invoices     │  • Provisioning configs     │
│  • Permissions  │  • API audits   │  • Health monitoring        │
│  • Extensions   │  • Rate tables  │  • Firmware tracking        │
├─────────────────┴─────────────────┴─────────────────────────────┤
│                      Voicemail Services                         │
│                                                                 │
│    • Message storage  • Transcriptions  • Notification prefs    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

The schema-api repository follows a migration-based architecture where each schema change is captured as an immutable, versioned migration file.

```
schema-api/
├── migrations/
│   ├── 2010/
│   │   ├── 20100115_001_initial_schema.sql
│   │   ├── 20100203_002_add_users_table.sql
│   │   └── ...
│   ├── 2011/
│   ├── ...
│   └── 2022/
│       ├── 20220801_156_billing_audit_tables.sql
│       └── 20220915_157_device_monitoring_indexes.sql
├── models/
│   ├── README.md
│   ├── billing/
│   ├── devices/
│   ├── voicemail/
│   └── telecom/
├── docs/
│   ├── migration-guide.md
│   ├── schema-conventions.md
│   └── diagrams/
├── scripts/
│   ├── migrate.sh
│   ├── rollback.sh
│   └── validate-schema.sh
└── README.md
```

### Key Architectural Principles

1. **Immutability**: Once applied, migrations are never modified — only new migrations are added
2. **Sequential Ordering**: Migrations execute in strict chronological order
3. **Idempotency**: Migration scripts can be safely re-run without side effects
4. **Reversibility**: Each migration includes rollback procedures where possible

---

## Data Models at a Glance

The repository defines **18 data models** organized across functional domains:

| Model Category | Models | Description |
|----------------|--------|-------------|
| **Core Telecom** | 5 | Call records, extensions, dial plans, routing rules, SIP configurations |
| **Billing** | 4 | Accounts, invoices, usage records, rate tables |
| **Devices** | 4 | Device registry, configurations, firmware versions, health metrics |
| **Voicemail** | 3 | Messages, transcriptions, user preferences |
| **Security** | 2 | API audit logs, permission matrices |

For detailed model documentation, see the [Data Models Overview](models/README.md).

---

## Migration Naming Convention

All migrations follow a strict naming convention to ensure proper ordering and traceability:

```
YYYYMMDD_NNN_descriptive_name.sql
│        │   │
│        │   └── Snake_case description of the change
│        └────── Sequential number within the day (001-999)
└─────────────── Date in ISO format
```

### Examples

```
20220801_001_create_billing_audit_table.sql
20220801_002_add_billing_audit_indexes.sql
20220915_001_add_device_health_metrics.sql
```

### Migration File Structure

Each migration file follows this standard template:

```sql
-- Migration: 20220801_001_create_billing_audit_table
-- Author: engineering-team
-- Date: 2022-08-01
-- Description: Creates the billing_audit table for tracking all billing-related API calls

-- ============================================
-- UP MIGRATION
-- ============================================

BEGIN;

CREATE TABLE IF NOT EXISTS billing_audit (
    id              BIGSERIAL PRIMARY KEY,
    account_id      UUID NOT NULL REFERENCES accounts(id),
    action_type     VARCHAR(50) NOT NULL,
    request_payload JSONB,
    response_code   INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address      INET
);

CREATE INDEX idx_billing_audit_account_id ON billing_audit(account_id);
CREATE INDEX idx_billing_audit_created_at ON billing_audit(created_at);

COMMIT;

-- ============================================
-- DOWN MIGRATION (Rollback)
-- ============================================

-- BEGIN;
-- DROP TABLE IF EXISTS billing_audit CASCADE;
-- COMMIT;
```

---

## How to Use These Schemas

### For New Service Development

When building a new service that needs database access:

1. **Review existing models** in the [models/](models/README.md) directory
2. **Identify required tables** for your feature
3. **Create new migrations** if schema changes are needed
4. **Follow conventions** outlined in [Schema Conventions](docs/schema-conventions.md)

### For Database Migrations

#### Using the Migration Scripts

```bash
# Run all pending migrations
./scripts/migrate.sh --env production

# Run migrations up to a specific version
./scripts/migrate.sh --env staging --target 20220801_001

# Validate migration files without executing
./scripts/validate-schema.sh

# Rollback the last migration
./scripts/rollback.sh --env development --steps 1
```

#### Manual Migration Execution

For direct database access, execute migrations in order:

```bash
# Connect to your PostgreSQL database
psql -h localhost -U dbuser -d telecom_platform

# Execute a specific migration
\i migrations/2022/20220801_001_create_billing_audit_table.sql

# Verify the migration was applied
\dt billing_audit
```

### Environment Configuration

Set up your database connection via environment variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=telecom_platform
export DB_USER=schema_admin
export DB_PASSWORD=secure_password
export DB_SSL_MODE=require
```

---

## Getting Started

### Prerequisites

Before working with schema-api, ensure you have:

- [ ] **PostgreSQL 12+** installed locally or accessible remotely
- [ ] **Database credentials** with schema modification privileges
- [ ] **Git** for version control
- [ ] Basic understanding of SQL and database migrations

### Quick Start Guide

#### Step 1: Clone the Repository

```bash
git clone <repository-url>/schema-api.git
cd schema-api
```

#### Step 2: Review the Current Schema State

```bash
# List all migrations by year
ls -la migrations/

# Count total migrations
find migrations/ -name "*.sql" | wc -l

# View the latest migration
ls -t migrations/2022/*.sql | head -1 | xargs cat
```

#### Step 3: Set Up a Local Development Database

```bash
# Create a new PostgreSQL database
createdb telecom_dev

# Run all migrations against the development database
DB_NAME=telecom_dev ./scripts/migrate.sh --env development
```

#### Step 4: Verify Schema Installation

```sql
-- Connect and list all tables
psql -d telecom_dev -c "\dt"

-- Check migration history (if using a migrations tracking table)
SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 10;
```

### Creating Your First Migration

```bash
# Generate a new migration file
./scripts/new-migration.sh "add_customer_preferences_table"

# This creates: migrations/2024/20240115_001_add_customer_preferences_table.sql
```

Edit the generated file with your schema changes, then apply:

```bash
./scripts/migrate.sh --env development
```

---

## Documentation Index

| Document | Description |
|----------|-------------|
| 📘 [Data Models Overview](models/README.md) | Comprehensive documentation of all 18 data models, their relationships, and field definitions |
| 📗 [Migration Guide](docs/migration-guide.md) | Step-by-step guide for creating, testing, and deploying database migrations |
| 📙 [Schema Conventions](docs/schema-conventions.md) | Coding standards, naming conventions, and best practices for schema design |

### Additional Resources

- `models/billing/` — Billing-specific model documentation
- `models/devices/` — Device management schema details
- `models/voicemail/` — Voicemail system data structures
- `models/telecom/` — Core VoIP/telecommunications models
- `docs/diagrams/` — Entity-relationship diagrams and visual documentation

---

## Troubleshooting

### Common Issues

#### Migration Fails with "Relation Already Exists"

```sql
-- Check if the table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'your_table_name'
);

-- Use IF NOT EXISTS in your migration
CREATE TABLE IF NOT EXISTS your_table_name (...);
```

#### Foreign Key Constraint Violations

Ensure migrations are run in order. Check the migration tracking table:

```sql
SELECT * FROM schema_migrations 
WHERE NOT applied 
ORDER BY version;
```

#### Permission Denied Errors

Verify your database user has sufficient privileges:

```sql
GRANT ALL PRIVILEGES ON DATABASE telecom_platform TO schema_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO schema_admin;
```

### Getting Help

- Review existing migrations for patterns and examples
- Check the [Migration Guide](docs/migration-guide.md) for detailed procedures
- Consult the [Schema Conventions](docs/schema-conventions.md) for best practices

---

## Contributing

When contributing to schema-api:

1. **Never modify existing migrations** that have been applied to production
2. **Always include rollback procedures** in new migrations
3. **Test migrations** against a copy of production data when possible
4. **Document complex changes** with inline comments
5. **Follow naming conventions** strictly for consistency

See the [Migration Guide](docs/migration-guide.md) for detailed contribution procedures.

---

<div align="center">

**[Data Models](models/README.md)** · **[Migration Guide](docs/migration-guide.md)** · **[Schema Conventions](docs/schema-conventions.md)**

*Maintaining the foundation of telecommunications infrastructure since 2010*

</div>