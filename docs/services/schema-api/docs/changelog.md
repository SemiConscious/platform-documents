# Schema Changelog

> **Historical record of significant schema changes organized by date**

## Overview

This document provides a comprehensive historical record of all significant schema changes made to the schema-api service database. The schema-api service forms the backbone of a telecommunications/VoIP platform, managing database migrations that define data models for billing, device management, voicemail capabilities, dial plan management, and permissions systems.

Understanding the evolution of these schemas is crucial for:
- **Migration planning**: When upgrading from older versions
- **Debugging**: Understanding why certain data structures exist
- **Feature development**: Knowing what capabilities are available at different schema versions
- **Compliance**: Maintaining audit trails for regulatory requirements

The changelog is organized chronologically in reverse order (newest first) with special attention to breaking changes that may require data migration or application updates.

---

## 2022 Changes

### Q4 2022

#### November 2022 - API Audit Infrastructure Enhancement

**Migration ID**: `2022110801`

Added comprehensive API audit logging capabilities to track all API interactions for compliance and debugging purposes.

```sql
-- Example structure added for API audit logging
CREATE TABLE api_audit_log (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    account_id VARCHAR(32) REFERENCES accounts(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_payload JSONB,
    response_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_audit_account_id ON api_audit_log(account_id);
CREATE INDEX idx_api_audit_created_at ON api_audit_log(created_at);
CREATE INDEX idx_api_audit_endpoint ON api_audit_log(endpoint);
```

**Key Changes**:
- Added `api_audit_log` table for comprehensive request tracking
- Implemented JSONB storage for flexible payload logging
- Added performance indexes for common query patterns
- Introduced request timing metrics for SLA monitoring

**Impact**: Low - Additive change only, no existing data affected

---

#### October 2022 - Device Status Model Expansion

**Migration ID**: `2022100501`

Enhanced the device status tracking system to support more granular device states and diagnostic information.

**Schema Changes**:
- Added `last_diagnostic_run` timestamp to `device_status` table
- Introduced `firmware_version` tracking column
- Created new `device_diagnostics` table for historical diagnostic data
- Added `device_health_score` computed column

```sql
-- Device diagnostics historical tracking
ALTER TABLE device_status 
ADD COLUMN last_diagnostic_run TIMESTAMP WITH TIME ZONE,
ADD COLUMN firmware_version VARCHAR(50),
ADD COLUMN health_score DECIMAL(3,2) DEFAULT 1.00;

CREATE TABLE device_diagnostics (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(32) NOT NULL REFERENCES devices(id),
    diagnostic_type VARCHAR(50) NOT NULL,
    result_code INTEGER NOT NULL,
    result_data JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Impact**: Low - Backward compatible additions

---

### Q3 2022

#### September 2022 - Voicemail Transcription Support

**Migration ID**: `2022090101`

Added infrastructure to support voicemail-to-text transcription services.

**Key Additions**:
- `transcription_text` column in voicemail messages table
- `transcription_status` enum for tracking transcription state
- `transcription_confidence` score field
- Integration fields for external transcription services

```sql
-- Voicemail transcription support
CREATE TYPE transcription_status AS ENUM (
    'pending', 
    'processing', 
    'completed', 
    'failed', 
    'not_requested'
);

ALTER TABLE voicemail_messages
ADD COLUMN transcription_text TEXT,
ADD COLUMN transcription_status transcription_status DEFAULT 'not_requested',
ADD COLUMN transcription_confidence DECIMAL(4,3),
ADD COLUMN transcription_service VARCHAR(50),
ADD COLUMN transcription_completed_at TIMESTAMP WITH TIME ZONE;
```

**Impact**: Low - Additive change, existing voicemails remain unaffected

---

#### July 2022 - Billing System Modernization

**Migration ID**: `2022070101`

Major restructuring of the billing infrastructure to support subscription-based pricing models alongside usage-based billing.

**⚠️ BREAKING CHANGE**

**Schema Changes**:
- Renamed `billing_transactions` to `billing_transactions_legacy`
- Created new `billing_events` table with expanded schema
- Added `subscription_plans` table
- Created `account_subscriptions` junction table
- Introduced `billing_periods` for subscription management

```sql
-- New subscription-aware billing structure
CREATE TABLE subscription_plans (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    billing_cycle_days INTEGER NOT NULL DEFAULT 30,
    base_price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    features JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE account_subscriptions (
    id VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES accounts(id),
    plan_id VARCHAR(32) NOT NULL REFERENCES subscription_plans(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing_events (
    id BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL REFERENCES accounts(id),
    subscription_id VARCHAR(32) REFERENCES account_subscriptions(id),
    event_type VARCHAR(50) NOT NULL,
    amount DECIMAL(12,4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    quantity DECIMAL(12,4) DEFAULT 1,
    unit_type VARCHAR(20),
    description TEXT,
    metadata JSONB,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    invoice_id VARCHAR(32)
);
```

**Migration Steps Required**:
1. Run data migration script to copy existing transactions
2. Update application billing modules to use new tables
3. Verify data integrity post-migration
4. Archive legacy table after 90-day validation period

**Impact**: HIGH - Requires coordinated deployment with application changes

---

### Q1-Q2 2022

#### April 2022 - Dial Plan Versioning

**Migration ID**: `2022040101`

Implemented version control for dial plans to support rollback capabilities.

```sql
CREATE TABLE dial_plan_versions (
    id BIGSERIAL PRIMARY KEY,
    dial_plan_id VARCHAR(32) NOT NULL REFERENCES dial_plans(id),
    version_number INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_by VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(dial_plan_id, version_number)
);
```

**Impact**: Low - Additive change

#### February 2022 - Enhanced Device Metadata

**Migration ID**: `2022020101`

Expanded device metadata storage for improved device management.

**Changes**:
- Added `custom_metadata` JSONB column to devices table
- Created `device_tags` table for flexible categorization
- Added MAC address validation trigger

**Impact**: Low - Additive change

---

## 2021 Changes

### Q4 2021

#### December 2021 - Multi-Tenant Isolation Enhancement

**Migration ID**: `2021120101`

**⚠️ BREAKING CHANGE**

Strengthened multi-tenant data isolation by adding account_id foreign keys to tables that previously relied on implicit relationships.

**Affected Tables**:
- `voicemail_boxes` - Added required `account_id` column
- `call_recordings` - Added required `account_id` column  
- `fax_documents` - Added required `account_id` column

```sql
-- Example migration for voicemail_boxes
ALTER TABLE voicemail_boxes
ADD COLUMN account_id VARCHAR(32);

-- Backfill from related data
UPDATE voicemail_boxes vb
SET account_id = u.account_id
FROM users u
WHERE vb.owner_id = u.id;

-- Make column required after backfill
ALTER TABLE voicemail_boxes
ALTER COLUMN account_id SET NOT NULL,
ADD CONSTRAINT fk_voicemail_account 
    FOREIGN KEY (account_id) REFERENCES accounts(id);

-- Add row-level security policy
CREATE POLICY voicemail_tenant_isolation ON voicemail_boxes
    USING (account_id = current_setting('app.current_account_id'));
```

**Impact**: HIGH - Required data backfill and application updates

---

#### November 2021 - Call Detail Record Optimization

**Migration ID**: `2021110101`

Partitioned the CDR table by month for improved query performance on historical data.

```sql
-- Convert to partitioned table
CREATE TABLE call_detail_records_partitioned (
    id BIGSERIAL,
    call_id VARCHAR(64) NOT NULL,
    account_id VARCHAR(32) NOT NULL,
    caller_number VARCHAR(20),
    callee_number VARCHAR(20),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    disposition VARCHAR(20),
    -- Additional CDR fields
    PRIMARY KEY (id, start_time)
) PARTITION BY RANGE (start_time);

-- Create monthly partitions
CREATE TABLE cdr_2021_11 PARTITION OF call_detail_records_partitioned
    FOR VALUES FROM ('2021-11-01') TO ('2021-12-01');
```

**Impact**: Medium - Improved query performance, required maintenance procedures update

---

### Q2-Q3 2021

#### August 2021 - Permission System Overhaul

**Migration ID**: `2021080101`

Replaced simple role-based permissions with granular resource-based access control.

**New Tables**:
- `permissions` - Individual permission definitions
- `role_permissions` - Role to permission mappings
- `user_permissions` - Direct user permission grants
- `permission_groups` - Logical groupings of permissions

**Impact**: HIGH - Required application permission checks update

#### May 2021 - Voicemail Greeting Management

**Migration ID**: `2021050101`

Added support for multiple custom greetings per voicemail box.

```sql
CREATE TABLE voicemail_greetings (
    id VARCHAR(32) PRIMARY KEY,
    mailbox_id VARCHAR(32) NOT NULL REFERENCES vmboxes(id),
    greeting_type VARCHAR(20) NOT NULL DEFAULT 'unavailable',
    media_id VARCHAR(32),
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Impact**: Low - Additive change

---

## 2020 Changes

### Q4 2020

#### November 2020 - Device Monitoring Foundation

**Migration ID**: `2020110101`

Established the device monitoring infrastructure that would later support real-time device status tracking.

**Schema Additions**:
- `device_status` table for current state tracking
- `device_events` table for historical event logging
- `device_alerts` table for threshold-based alerting

```sql
CREATE TABLE device_status (
    device_id VARCHAR(32) PRIMARY KEY REFERENCES devices(id),
    status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    last_seen TIMESTAMP WITH TIME ZONE,
    last_ip_address INET,
    registration_status VARCHAR(20),
    uptime_seconds BIGINT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE device_events (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_device_events_device_time 
    ON device_events(device_id, occurred_at DESC);
```

**Impact**: Low - New feature tables

---

#### September 2020 - Billing API Foundation

**Migration ID**: `2020090101`

Initial billing system schema supporting usage-based billing.

**Core Tables Created**:
- `billing_accounts` - Billing profile for accounts
- `billing_transactions` - Transaction records
- `billing_rates` - Rate definitions
- `payment_methods` - Stored payment information

**Impact**: Low - Initial implementation

---

### Q1-Q2 2020

#### June 2020 - Fax Document Management

**Migration ID**: `2020060101`

Added fax transmission and storage capabilities.

**Tables**: `fax_documents`, `fax_transmissions`, `fax_queues`

**Impact**: Low - New feature

#### March 2020 - User Authentication Enhancement

**Migration ID**: `2020030101`

Added MFA support and session management.

**Changes**:
- Added `mfa_enabled`, `mfa_secret` to users table
- Created `user_sessions` table
- Added `password_reset_tokens` table

**Impact**: Low - Backward compatible

---

## Earlier Changes Summary

### 2019 and Earlier

The schema-api service has migrations dating back to 2010. Below is a summary of the foundational schemas established during this period:

| Year | Major Feature | Key Tables |
|------|---------------|------------|
| 2019 | Conference Bridge Support | `conferences`, `conference_participants` |
| 2018 | Call Recording | `recordings`, `recording_storage` |
| 2017 | Ring Group Management | `ring_groups`, `ring_group_members` |
| 2016 | Time-based Routing | `temporal_rules`, `time_conditions` |
| 2015 | IVR/Auto Attendant | `menus`, `menu_entries` |
| 2014 | Call Queue System | `queues`, `queue_agents` |
| 2013 | Voicemail Core | `vmboxes`, `voicemail_messages` |
| 2012 | Device Management | `devices`, `device_assignments` |
| 2011 | User/Account Core | `accounts`, `users`, `users_to_accounts` |
| 2010 | Foundation | Initial database schema, phone numbers |

For detailed information about migrations prior to 2020, consult the individual migration files in the `/migrations` directory or contact the database administration team.

---

## Breaking Changes

This section provides a quick reference for all breaking changes requiring special migration attention.

### Breaking Changes Summary Table

| Migration ID | Date | Description | Impact Level | Rollback Possible |
|--------------|------|-------------|--------------|-------------------|
| 2022070101 | July 2022 | Billing System Modernization | HIGH | With data loss |
| 2021120101 | Dec 2021 | Multi-Tenant Isolation | HIGH | No |
| 2021080101 | Aug 2021 | Permission System Overhaul | HIGH | No |

### Pre-Migration Checklist for Breaking Changes

Before applying any breaking change migration:

1. **Backup**: Create a full database backup
2. **Test**: Apply migration to staging environment first
3. **Validate**: Run data integrity checks post-migration
4. **Coordinate**: Ensure application deployments are synchronized
5. **Monitor**: Watch for errors during and after migration
6. **Document**: Record any issues encountered

### Rollback Procedures

For migrations marked "Rollback Possible":
- Rollback scripts are available in `/migrations/rollback/`
- Test rollback in staging before production
- Data loss may occur - review rollback script comments

For migrations marked "No Rollback":
- Restore from backup is the only recovery option
- Plan additional testing time before production deployment

---

## Best Practices

### Working with Schema Changes

1. **Always review migration scripts** before applying to production
2. **Test migrations** on a copy of production data when possible
3. **Schedule breaking changes** during maintenance windows
4. **Monitor application logs** after schema changes
5. **Update documentation** when adding new tables or columns

### Version Compatibility

When developing against the schema-api:
- Check the `schema_version` table for current version
- Ensure application code supports the target schema version
- Use feature flags for gradual rollout of schema-dependent features

---

## Contact and Support

For questions about schema changes or migration assistance:
- **Database Team**: database-team@company.com
- **Schema Change Requests**: Submit via internal ticketing system
- **Emergency Support**: Follow on-call procedures in runbook