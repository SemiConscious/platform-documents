# Migration Guide

## Overview

This guide provides comprehensive documentation for creating, running, and managing database migrations within the schema-api service. The schema-api service is the backbone of your telecommunications/VoIP platform's data layer, containing migration files that define and evolve the database schema for billing, device management, voicemail capabilities, and more.

Database migrations are essential for maintaining data integrity while evolving your schema over time. This repository contains migrations spanning from 2010 to 2022, representing over a decade of schema evolution for a complex telecommunications platform. Understanding how to work with these migrations effectively is crucial for any developer contributing to this service.

## Migration File Naming Convention

### Standard Naming Pattern

All migration files in the schema-api service follow a strict naming convention that ensures proper ordering and identification:

```
{YYYYMMDDHHMMSS}_{descriptive_name}.{direction}.sql
```

**Components breakdown:**

| Component | Description | Example |
|-----------|-------------|---------|
| `YYYYMMDDHHMMSS` | Timestamp of migration creation | `20220315143022` |
| `descriptive_name` | Snake_case description of changes | `add_voicemail_transcription` |
| `direction` | Migration direction (`up` or `down`) | `up`, `down` |
| `extension` | File extension | `.sql` |

### Example File Names

```
20220315143022_add_voicemail_transcription.up.sql
20220315143022_add_voicemail_transcription.down.sql
20220118092145_create_device_monitoring_table.up.sql
20220118092145_create_device_monitoring_table.down.sql
20211205110030_add_billing_audit_columns.up.sql
20211205110030_add_billing_audit_columns.down.sql
```

### Naming Best Practices

1. **Use descriptive names**: The name should clearly indicate what the migration does
2. **Use action verbs**: Start with `create_`, `add_`, `remove_`, `modify_`, `drop_`
3. **Reference the affected entity**: Include table or feature names
4. **Keep it concise**: Aim for 3-5 words maximum
5. **Use snake_case**: All lowercase with underscores

```
✅ Good names:
   - create_dial_plans_table
   - add_user_permissions_column
   - remove_legacy_billing_fields
   - modify_device_status_enum

❌ Bad names:
   - migration1
   - changes
   - update
   - fix_stuff
```

## Creating New Migrations

### Step 1: Generate Migration Files

Create both `up` and `down` migration files with matching timestamps. You can generate the timestamp automatically:

```bash
# Generate timestamp
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Create migration files
touch migrations/${TIMESTAMP}_your_migration_name.up.sql
touch migrations/${TIMESTAMP}_your_migration_name.down.sql
```

Alternatively, use the provided helper script if available:

```bash
./scripts/create-migration.sh "add_voicemail_settings"
```

### Step 2: Write the Up Migration

The `up` migration contains the SQL statements to apply the schema change. Here's a comprehensive example for the telecommunications domain:

```sql
-- migrations/20220315143022_add_voicemail_transcription.up.sql

-- Add transcription support to voicemail messages
ALTER TABLE voicemail_messages
    ADD COLUMN transcription_text TEXT,
    ADD COLUMN transcription_status VARCHAR(50) DEFAULT 'pending',
    ADD COLUMN transcription_confidence DECIMAL(5,4),
    ADD COLUMN transcription_engine VARCHAR(100),
    ADD COLUMN transcription_completed_at TIMESTAMP;

-- Create index for efficient transcription status queries
CREATE INDEX idx_voicemail_messages_transcription_status 
    ON voicemail_messages(transcription_status);

-- Create transcription audit table
CREATE TABLE voicemail_transcription_audit (
    id SERIAL PRIMARY KEY,
    voicemail_message_id INTEGER NOT NULL REFERENCES voicemail_messages(id),
    engine_used VARCHAR(100) NOT NULL,
    processing_time_ms INTEGER,
    character_count INTEGER,
    cost_units DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comment for documentation
COMMENT ON TABLE voicemail_transcription_audit IS 
    'Tracks transcription processing metrics for billing and optimization';
```

### Step 3: Write the Down Migration

The `down` migration must reverse all changes made by the `up` migration:

```sql
-- migrations/20220315143022_add_voicemail_transcription.down.sql

-- Drop transcription audit table first (foreign key dependency)
DROP TABLE IF EXISTS voicemail_transcription_audit;

-- Remove transcription index
DROP INDEX IF EXISTS idx_voicemail_messages_transcription_status;

-- Remove transcription columns from voicemail_messages
ALTER TABLE voicemail_messages
    DROP COLUMN IF EXISTS transcription_text,
    DROP COLUMN IF EXISTS transcription_status,
    DROP COLUMN IF EXISTS transcription_confidence,
    DROP COLUMN IF EXISTS transcription_engine,
    DROP COLUMN IF EXISTS transcription_completed_at;
```

### Step 4: Validate Your Migration

Before committing, validate your migration:

```bash
# Syntax check (PostgreSQL example)
psql -d your_test_db -f migrations/20220315143022_add_voicemail_transcription.up.sql --set ON_ERROR_STOP=1

# Verify rollback works
psql -d your_test_db -f migrations/20220315143022_add_voicemail_transcription.down.sql --set ON_ERROR_STOP=1

# Re-apply to confirm idempotency
psql -d your_test_db -f migrations/20220315143022_add_voicemail_transcription.up.sql --set ON_ERROR_STOP=1
```

### Complex Migration Example: Device Management

```sql
-- migrations/20220201100000_create_device_provisioning_system.up.sql

-- Device provisioning templates
CREATE TABLE device_templates (
    id SERIAL PRIMARY KEY,
    manufacturer VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    firmware_version VARCHAR(50),
    config_template JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manufacturer, model, firmware_version)
);

-- Device provisioning status tracking
CREATE TYPE device_provision_status AS ENUM (
    'pending',
    'in_progress', 
    'completed',
    'failed',
    'cancelled'
);

CREATE TABLE device_provisioning_jobs (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    template_id INTEGER NOT NULL REFERENCES device_templates(id),
    status device_provision_status DEFAULT 'pending',
    config_payload JSONB,
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_provisioning_jobs_status ON device_provisioning_jobs(status);
CREATE INDEX idx_provisioning_jobs_device ON device_provisioning_jobs(device_id);
CREATE INDEX idx_provisioning_jobs_scheduled ON device_provisioning_jobs(scheduled_at) 
    WHERE status = 'pending';

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_device_templates_modtime
    BEFORE UPDATE ON device_templates
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
```

## Running Migrations

### Prerequisites

Ensure your database connection is properly configured:

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/schema_api"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export DATABASE_NAME="schema_api"
export DATABASE_USER="your_user"
export DATABASE_PASSWORD="your_password"
```

### Running All Pending Migrations

```bash
# Using the migration tool
migrate -path ./migrations -database $DATABASE_URL up

# Or using the provided script
./scripts/run-migrations.sh up
```

### Running Specific Number of Migrations

```bash
# Apply next 2 migrations only
migrate -path ./migrations -database $DATABASE_URL up 2

# Apply migrations up to a specific version
migrate -path ./migrations -database $DATABASE_URL goto 20220315143022
```

### Checking Migration Status

```bash
# View current migration version
migrate -path ./migrations -database $DATABASE_URL version

# List all migrations and their status
./scripts/migration-status.sh
```

### Running Migrations in Different Environments

```bash
# Development
DATABASE_URL=$DEV_DATABASE_URL migrate -path ./migrations -database $DATABASE_URL up

# Staging
DATABASE_URL=$STAGING_DATABASE_URL migrate -path ./migrations -database $DATABASE_URL up

# Production (with confirmation)
./scripts/run-migrations.sh up --env production --confirm
```

### Migration Execution Order

Migrations are executed in chronological order based on the timestamp prefix:

```
1. 20100115000000_initial_schema.up.sql
2. 20100215120000_add_users_table.up.sql
3. 20100301090000_create_billing_tables.up.sql
...
n. 20220315143022_add_voicemail_transcription.up.sql
```

## Rolling Back Migrations

### Rolling Back the Last Migration

```bash
# Rollback most recent migration
migrate -path ./migrations -database $DATABASE_URL down 1
```

### Rolling Back Multiple Migrations

```bash
# Rollback last 3 migrations
migrate -path ./migrations -database $DATABASE_URL down 3
```

### Rolling Back to a Specific Version

```bash
# Rollback to version 20220101000000
migrate -path ./migrations -database $DATABASE_URL goto 20220101000000
```

### Rolling Back All Migrations (DANGER)

```bash
# Rollback ALL migrations - use with extreme caution
migrate -path ./migrations -database $DATABASE_URL down

# Force rollback (bypasses dirty state)
migrate -path ./migrations -database $DATABASE_URL force 20220101000000
```

### Safe Rollback Procedure for Production

```bash
#!/bin/bash
# scripts/safe-rollback.sh

set -e

VERSION=$1
ENV=${2:-staging}

if [ -z "$VERSION" ]; then
    echo "Usage: ./safe-rollback.sh <version> [environment]"
    exit 1
fi

# Backup database first
./scripts/backup-database.sh $ENV

# Show what will be rolled back
echo "Migrations to be rolled back:"
migrate -path ./migrations -database $DATABASE_URL version
echo "Target version: $VERSION"

# Confirm
read -p "Proceed with rollback? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Execute rollback
migrate -path ./migrations -database $DATABASE_URL goto $VERSION

echo "Rollback completed successfully"
```

## Migration Best Practices

### 1. Always Write Reversible Migrations

Every `up` migration must have a corresponding `down` migration that completely reverses the changes:

```sql
-- ✅ Good: Reversible migration
-- UP
ALTER TABLE billing_records ADD COLUMN tax_rate DECIMAL(5,2);

-- DOWN  
ALTER TABLE billing_records DROP COLUMN tax_rate;

-- ❌ Bad: Irreversible data migration
-- UP
DELETE FROM legacy_data WHERE created_at < '2010-01-01';
-- DOWN
-- Cannot restore deleted data!
```

### 2. Make Migrations Idempotent When Possible

```sql
-- Use IF EXISTS / IF NOT EXISTS
CREATE TABLE IF NOT EXISTS api_audit_logs (...);
DROP TABLE IF EXISTS api_audit_logs;

-- Use conditional column additions
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'devices' AND column_name = 'firmware_version'
    ) THEN
        ALTER TABLE devices ADD COLUMN firmware_version VARCHAR(50);
    END IF;
END $$;
```

### 3. Keep Migrations Small and Focused

```sql
-- ✅ Good: Single responsibility
-- Migration 1: Create table
CREATE TABLE dial_plans (...);

-- Migration 2: Add indexes (separate migration)
CREATE INDEX idx_dial_plans_name ON dial_plans(name);

-- ❌ Bad: Too many changes in one migration
CREATE TABLE dial_plans (...);
CREATE TABLE dial_plan_rules (...);
CREATE TABLE dial_plan_permissions (...);
ALTER TABLE users ADD COLUMN default_dial_plan_id INTEGER;
-- Plus 20 more changes...
```

### 4. Handle Large Data Migrations Carefully

```sql
-- For large tables, migrate data in batches
DO $$
DECLARE
    batch_size INTEGER := 10000;
    total_rows INTEGER;
    offset_val INTEGER := 0;
BEGIN
    SELECT COUNT(*) INTO total_rows FROM billing_records WHERE new_column IS NULL;
    
    WHILE offset_val < total_rows LOOP
        UPDATE billing_records 
        SET new_column = calculate_value(old_column)
        WHERE id IN (
            SELECT id FROM billing_records 
            WHERE new_column IS NULL 
            LIMIT batch_size
        );
        
        offset_val := offset_val + batch_size;
        RAISE NOTICE 'Processed % of % rows', offset_val, total_rows;
    END LOOP;
END $$;
```

### 5. Add Appropriate Indexes

```sql
-- Index naming convention: idx_{table}_{column(s)}
CREATE INDEX idx_voicemail_messages_user_id ON voicemail_messages(user_id);
CREATE INDEX idx_voicemail_messages_created_at ON voicemail_messages(created_at DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_devices_account_status ON devices(account_id, status);

-- Partial indexes for specific conditions
CREATE INDEX idx_provisioning_jobs_pending ON device_provisioning_jobs(scheduled_at) 
    WHERE status = 'pending';
```

### 6. Document Complex Migrations

```sql
-- Migration: 20220315143022_add_voicemail_transcription
-- Author: team-voicemail
-- Ticket: VOIP-1234
-- 
-- Purpose: Add transcription support for voicemail messages to enable
-- text-based search and accessibility features.
--
-- Dependencies: Requires voicemail_messages table from migration 20200115000000
--
-- Performance Impact: 
--   - Adds 5 nullable columns (~100 bytes per row)
--   - New index on transcription_status
--   - Expected migration time: < 1 minute for tables under 1M rows
--
-- Rollback Risk: LOW - Only additive changes
```

### 7. Use Transactions Appropriately

```sql
-- Wrap related changes in transactions
BEGIN;

ALTER TABLE call_records ADD COLUMN duration_seconds INTEGER;
ALTER TABLE call_records ADD COLUMN billing_duration_seconds INTEGER;
UPDATE call_records SET duration_seconds = EXTRACT(EPOCH FROM (end_time - start_time));
UPDATE call_records SET billing_duration_seconds = CEIL(duration_seconds / 6.0) * 6;

COMMIT;
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Migration Stuck in "Dirty" State

**Symptom:** `Dirty database version X. Fix and force version.`

**Cause:** A previous migration failed partway through, leaving the database in an inconsistent state.

**Solution:**

```bash
# Check current state
migrate -path ./migrations -database $DATABASE_URL version

# Review what went wrong
psql $DATABASE_URL -c "SELECT * FROM schema_migrations;"

# Manually fix the issue, then force the version
migrate -path ./migrations -database $DATABASE_URL force <last_successful_version>
```

#### 2. Migration File Not Found

**Symptom:** `no migration found for version X`

**Cause:** Migration files were renamed, deleted, or have incorrect naming format.

**Solution:**

```bash
# List all migration files
ls -la migrations/

# Verify naming convention
# Should be: YYYYMMDDHHMMSS_name.up.sql and YYYYMMDDHHMMSS_name.down.sql

# Check for missing pairs
./scripts/check-migration-pairs.sh
```

#### 3. Foreign Key Constraint Violations

**Symptom:** `cannot drop table X because other objects depend on it`

**Solution:**

```sql
-- Drop dependent objects first
ALTER TABLE child_table DROP CONSTRAINT fk_parent_id;
DROP TABLE parent_table;

-- Or use CASCADE (with caution)
DROP TABLE parent_table CASCADE;
```

#### 4. Timeout During Large Migrations

**Symptom:** Migration hangs or times out on large tables.

**Solution:**

```bash
# Increase statement timeout
psql $DATABASE_URL -c "SET statement_timeout = '3600s';"

# Or run migration with extended timeout
PGOPTIONS='-c statement_timeout=3600000' migrate -path ./migrations -database $DATABASE_URL up
```

#### 5. Lock Contention Issues

**Symptom:** `deadlock detected` or migration blocks other operations.

**Solution:**

```sql
-- Use non-blocking index creation
CREATE INDEX CONCURRENTLY idx_large_table_column ON large_table(column);

-- Add columns without default values
ALTER TABLE large_table ADD COLUMN new_col INTEGER;
-- Then backfill in batches
```

#### 6. Inconsistent Environments

**Symptom:** Migration works in development but fails in production.

**Solution:**

```bash
# Compare schema versions across environments
./scripts/compare-schemas.sh dev staging production

# Export current schema for comparison
pg_dump --schema-only $DATABASE_URL > current_schema.sql

# Check for environment-specific configurations
diff <(psql $DEV_DB -c "SHOW ALL") <(psql $PROD_DB -c "SHOW ALL")
```

### Debugging Commands

```bash
# View migration history
psql $DATABASE_URL -c "SELECT * FROM schema_migrations ORDER BY version;"

# Check table existence
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"

# View table structure
psql $DATABASE_URL -c "\d+ table_name"

# Check for locks
psql $DATABASE_URL -c "SELECT * FROM pg_locks WHERE NOT granted;"

# View active queries
psql $DATABASE_URL -c "SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle';"
```

### Getting Help

If you encounter issues not covered in this guide:

1. Check the migration logs in `/var/log/schema-api/migrations.log`
2. Review the specific migration file for comments and documentation
3. Consult the schema-api team via your organization's communication channels
4. Search existing tickets for similar issues
5. Create a new ticket with:
   - Migration version and filename
   - Full error message
   - Database version and environment
   - Steps to reproduce

---

## Summary

Effective database migration management is crucial for maintaining the schema-api service. Remember these key points:

- **Always create both up and down migrations**
- **Follow the naming convention strictly**
- **Test migrations in development before applying to production**
- **Keep migrations small and focused**
- **Document complex changes**
- **Back up before rolling back in production**

For questions or improvements to this guide, please submit a pull request or contact the schema-api maintainers.