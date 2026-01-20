# Natterbox Database Architecture

> **Last Updated**: 2026-01-20  
> **Status**: Active  
> **Owner**: Platform Engineering Team

## Overview

Natterbox employs a multi-tier database architecture designed for high availability, geographic distribution, and scalable data management. The architecture spans on-premise data centers (SDCs) and AWS cloud infrastructure, supporting the core telephony platform, customer data storage, analytics, and real-time event processing.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        NATTERBOX DATABASE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────┐         ┌─────────────────────────┐               │
│  │      SDC S01 (UK)       │◄───────►│      SDC S02 (UK)       │               │
│  │                         │ Master  │                         │               │
│  │  ┌─────────────────┐    │ Master  │    ┌─────────────────┐  │               │
│  │  │   Core DB       │    │ Repl    │    │   Core DB       │  │               │
│  │  │   (MariaDB)     │◄───┼─────────┼───►│   (MariaDB)     │  │               │
│  │  └─────────────────┘    │         │    └─────────────────┘  │               │
│  │                         │         │                         │               │
│  │  ┌─────────────────┐    │         │    ┌─────────────────┐  │               │
│  │  │   Big DB        │    │         │    │   Big DB        │  │               │
│  │  │   (MariaDB)     │────┼─────────┼───►│   (ProxySQL)    │  │               │
│  │  └────────┬────────┘    │         │    └─────────────────┘  │               │
│  └───────────┼─────────────┘         └─────────────────────────┘               │
│              │                                                                  │
│              │ AWS DMS                                                          │
│              │ Replication                                                      │
│              ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           AWS CLOUD                                      │   │
│  │                                                                          │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐   │   │
│  │  │ Aurora MySQL │    │    RDS       │    │      DynamoDB            │   │   │
│  │  │  (BigDB)     │    │  (Various)   │    │ (Session, Analytics)     │   │   │
│  │  └──────────────┘    └──────────────┘    └──────────────────────────┘   │   │
│  │                                                                          │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│  │  │                    CDC Pipeline (Kinesis)                         │   │   │
│  │  │  DMS → Kinesis Data Streams → Lambda → EventBridge → Consumers   │   │   │
│  │  └──────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Database Tiers

### Tier 1: Core Database (CoreDB)

The Core Database is the primary operational datastore for the Natterbox platform, containing all critical business data including organizations, users, configurations, and real-time state.

#### Infrastructure

| Property | SDC S01 | SDC S02 |
|----------|---------|---------|
| **Engine** | MariaDB 10.6+ | MariaDB 10.6+ |
| **Role** | Master | Master |
| **Replication** | Master-Master | Master-Master |
| **Host** | `core-db-01.s01.natterbox.net` | `core-db-01.s02.natterbox.net` |
| **Port** | 3306 | 3306 |

#### Replication Architecture

```
┌──────────────────────────┐           ┌──────────────────────────┐
│       SDC S01            │           │       SDC S02            │
│                          │           │                          │
│   ┌────────────────┐     │           │     ┌────────────────┐   │
│   │   Core DB      │     │           │     │   Core DB      │   │
│   │   (Master)     │◄────┼───────────┼────►│   (Master)     │   │
│   └───────┬────────┘     │  Binary   │     └───────┬────────┘   │
│           │              │   Log     │             │            │
│           ▼              │  Repl     │             ▼            │
│   ┌────────────────┐     │           │     ┌────────────────┐   │
│   │ Platform-API   │     │           │     │ Platform-API   │   │
│   │ Platform-Sapien│     │           │     │ Platform-Sapien│   │
│   └────────────────┘     │           │     └────────────────┘   │
│                          │           │                          │
└──────────────────────────┘           └──────────────────────────┘
```

**Key Characteristics:**
- **Auto-increment Offset**: S01 uses odd IDs (1,3,5...), S02 uses even IDs (2,4,6...)
- **Conflict Handling**: Application-level conflict detection for simultaneous writes
- **Failover**: Automatic DNS-based failover between data centers

#### Database Schemas (from schema-api repository)

The CoreDB contains multiple logical schemas managed by the `schema-api` repository:

| Schema | Purpose | Key Tables |
|--------|---------|------------|
| **Org** | Organization and user data | `orgs`, `users`, `groups`, `devices`, `permissions` |
| **Voicemail** | Voicemail storage | `voicemail_msgs`, `voicemail_prefs` |
| **Contacts** | Contact management | `contacts`, `contact_directories` |
| **Numbers** | Phone number pool | `numbers`, `number_assignments` |
| **Reports** | Analytics aggregates | `report_data`, `report_schedules` |
| **Archiving** | Recording policies | `archive_policies`, `archive_jobs` |

#### Key Tables in Org Schema

```sql
-- Core organizational tables (from schema-api)
CREATE TABLE orgs (
    orgId INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status ENUM('active', 'suspended', 'deleted'),
    created DATETIME,
    modified DATETIME,
    INDEX idx_status (status)
);

CREATE TABLE users (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    orgId INT NOT NULL,
    email VARCHAR(255) NOT NULL,
    firstName VARCHAR(100),
    lastName VARCHAR(100),
    status ENUM('active', 'inactive', 'deleted'),
    created DATETIME,
    modified DATETIME,
    FOREIGN KEY (orgId) REFERENCES orgs(orgId),
    UNIQUE INDEX idx_email (email),
    INDEX idx_org_status (orgId, status)
);

CREATE TABLE devices (
    deviceId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT,
    orgId INT NOT NULL,
    deviceType ENUM('softphone', 'deskphone', 'mobile'),
    macAddress VARCHAR(17),
    sipUsername VARCHAR(64),
    status ENUM('registered', 'unregistered', 'disabled'),
    FOREIGN KEY (userId) REFERENCES users(userId),
    FOREIGN KEY (orgId) REFERENCES orgs(orgId)
);

CREATE TABLE groups (
    groupId INT AUTO_INCREMENT PRIMARY KEY,
    orgId INT NOT NULL,
    name VARCHAR(255),
    type ENUM('hunt', 'queue', 'broadcast'),
    FOREIGN KEY (orgId) REFERENCES orgs(orgId)
);
```

### Tier 2: Big Database (BigDB)

BigDB stores high-volume customer-specific data including Call Detail Records (CDRs), call recordings metadata, and historical analytics data. This tier is undergoing migration from on-premise to AWS Aurora.

#### Current Architecture (Hybrid)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         BigDB Hybrid Architecture                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────┐   │
│  │         SDC (On-Premise)         │    │         AWS Cloud           │   │
│  │                                  │    │                             │   │
│  │  ┌──────────────────────────┐   │    │  ┌───────────────────────┐  │   │
│  │  │     ProxySQL Layer       │   │    │  │    Aurora MySQL       │  │   │
│  │  │  (Query Routing)         │   │    │  │    (Primary)          │  │   │
│  │  └────────────┬─────────────┘   │    │  └───────────────────────┘  │   │
│  │               │                  │    │              ▲              │   │
│  │    ┌──────────┴──────────┐      │    │              │              │   │
│  │    │                     │      │    │     AWS DMS  │              │   │
│  │    ▼                     ▼      │    │  (CDC Repl)  │              │   │
│  │  ┌─────────┐      ┌─────────┐   │    │              │              │   │
│  │  │ BigDB   │──────│ BigDB   │───┼────┼──────────────┘              │   │
│  │  │ Master  │ Repl │ Replica │   │    │                             │   │
│  │  └─────────┘      └─────────┘   │    │                             │   │
│  │                                  │    │                             │   │
│  └──────────────────────────────────┘    └─────────────────────────────┘   │
│                                                                            │
│  Query Routing Rules (ProxySQL):                                          │
│  - WRITE queries → SDC Master                                              │
│  - READ queries → Aurora (preferred) or SDC Replica                        │
│  - Historical queries (>90 days) → Aurora only                            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

#### BigDB Tables

| Table | Purpose | Typical Size |
|-------|---------|--------------|
| `call_records` | CDR storage | 500M+ rows |
| `call_recordings` | Recording metadata | 100M+ rows |
| `call_events` | Real-time call events | 1B+ rows |
| `analytics_hourly` | Hourly aggregates | 50M+ rows |
| `analytics_daily` | Daily aggregates | 5M+ rows |

#### ProxySQL Configuration

ProxySQL provides intelligent query routing between on-premise and AWS databases:

```sql
-- ProxySQL query rules (simplified)
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, destination_hostgroup, apply)
VALUES
  -- Route writes to on-prem master
  (1, 1, '^INSERT|^UPDATE|^DELETE', 10, 1),
  -- Route historical reads to Aurora
  (2, 1, 'WHERE.*date.*<.*DATE_SUB', 20, 1),
  -- Route all other reads to Aurora
  (3, 1, '^SELECT', 20, 1);

-- Host groups
-- 10 = On-premise BigDB master
-- 20 = Aurora MySQL cluster
```

### Tier 3: AWS Managed Databases

#### Amazon Aurora MySQL

Primary cloud database for BigDB migration and new workloads.

| Property | Value |
|----------|-------|
| **Engine** | Aurora MySQL 8.0 |
| **Instance Class** | db.r6g.2xlarge (primary) |
| **Multi-AZ** | Yes (3 read replicas) |
| **Storage** | Aurora Standard (auto-scaling) |
| **Encryption** | AWS KMS (customer managed key) |
| **Backup** | Continuous (35-day retention) |

#### Amazon DynamoDB

Used for session management, real-time analytics, and high-throughput operational data.

| Table | Partition Key | Sort Key | Purpose |
|-------|---------------|----------|---------|
| `sessions` | `sessionId` | - | User session state |
| `call_state` | `callId` | `timestamp` | Real-time call tracking |
| `analytics_realtime` | `orgId` | `timestamp` | Live dashboard data |
| `feature_flags` | `orgId` | `featureKey` | Feature toggles |

#### Amazon RDS (Legacy/Specialized)

Several specialized RDS instances for specific workloads:

| Instance | Engine | Purpose |
|----------|--------|---------|
| `billing-prod` | MySQL 8.0 | Billing and subscription data |
| `analytics-prod` | PostgreSQL 14 | Advanced analytics queries |
| `freeswitch-prod` | MySQL 5.7 | FreeSWITCH CDR capture |

---

## Change Data Capture (CDC) Architecture

The CDC pipeline enables real-time streaming of database changes from on-premise MariaDB to AWS services for analytics, integrations, and event-driven workflows.

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            CDC Pipeline Architecture                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   MariaDB    │    │   AWS DMS    │    │   Kinesis    │    │   Lambda     │   │
│  │   (Source)   │───►│  (CDC Task)  │───►│   Stream     │───►│  (Transform) │   │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘   │
│                                                                      │           │
│                                                                      ▼           │
│                                                           ┌──────────────────┐   │
│                                                           │   EventBridge    │   │
│                                                           │   (Event Bus)    │   │
│                                                           └────────┬─────────┘   │
│                                                                    │             │
│                         ┌──────────────────────────────────────────┤             │
│                         │                    │                     │             │
│                         ▼                    ▼                     ▼             │
│              ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│              │   Salesforce     │  │   Analytics      │  │   Webhooks       │   │
│              │   Integration    │  │   Pipeline       │  │   (Customer)     │   │
│              └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### AWS DMS (Database Migration Service)

Captures binary log changes from MariaDB and streams to Kinesis.

**Configuration:**
```json
{
  "ReplicationInstanceArn": "arn:aws:dms:eu-west-2:...:rep:cdc-prod",
  "SourceEndpoint": {
    "Engine": "mariadb",
    "ServerName": "core-db-01.s01.natterbox.net",
    "Port": 3306,
    "DatabaseName": "org"
  },
  "TargetEndpoint": {
    "Engine": "kinesis",
    "ServiceAccessRoleArn": "arn:aws:iam::...:role/dms-kinesis-role",
    "StreamArn": "arn:aws:kinesis:eu-west-2:...:stream/cdc-events"
  },
  "ReplicationTaskSettings": {
    "TargetMetadata": {
      "BatchApplyEnabled": true,
      "FullLobMode": false
    },
    "ChangeProcessingTuning": {
      "BatchApplyTimeoutMin": 1,
      "BatchApplyTimeoutMax": 30,
      "CommitTimeout": 1
    }
  }
}
```

#### Kinesis Data Streams

**Stream Configuration:**

| Property | Value |
|----------|-------|
| **Stream Name** | `cdc-events-prod` |
| **Shard Count** | 8 (auto-scaling enabled) |
| **Retention** | 7 days |
| **Encryption** | AWS KMS |

**Event Format:**
```json
{
  "metadata": {
    "timestamp": "2026-01-20T10:30:00.123Z",
    "table-name": "users",
    "operation": "update",
    "schema-name": "org",
    "transaction-id": "12345678"
  },
  "data": {
    "userId": 12345,
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "status": "active"
  },
  "before-image": {
    "status": "inactive"
  }
}
```

#### Lambda Transformer

Transforms raw DMS events into domain events for downstream consumers.

**Function Configuration:**
```yaml
FunctionName: cdc-transformer-prod
Runtime: python3.11
MemorySize: 1024
Timeout: 60
ReservedConcurrentExecutions: 100
Environment:
  EVENT_BUS_NAME: natterbox-events-prod
  LOG_LEVEL: INFO
```

**Transformation Logic:**
```python
# Simplified transformation logic
def transform_cdc_event(raw_event):
    """Transform raw CDC event to domain event."""
    table = raw_event['metadata']['table-name']
    operation = raw_event['metadata']['operation']
    
    event_type = f"natterbox.{table}.{operation}"
    
    return {
        'Source': 'natterbox.cdc',
        'DetailType': event_type,
        'Detail': json.dumps({
            'entityId': raw_event['data'].get('id') or raw_event['data'].get(f'{table}Id'),
            'timestamp': raw_event['metadata']['timestamp'],
            'operation': operation,
            'data': raw_event['data'],
            'previousData': raw_event.get('before-image', {})
        }),
        'EventBusName': os.environ['EVENT_BUS_NAME']
    }
```

#### EventBridge Rules

Events are routed to consumers based on rules:

```json
{
  "Name": "salesforce-sync-rule",
  "EventPattern": {
    "source": ["natterbox.cdc"],
    "detail-type": [
      "natterbox.users.insert",
      "natterbox.users.update",
      "natterbox.orgs.update"
    ]
  },
  "Targets": [{
    "Arn": "arn:aws:sqs:eu-west-2:...:salesforce-sync-queue",
    "Id": "salesforce-sync"
  }]
}
```

### CDC Performance Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **End-to-end Latency** | < 5 seconds | > 30 seconds |
| **DMS Replication Lag** | < 1 second | > 10 seconds |
| **Lambda Processing Time** | < 500ms | > 2 seconds |
| **EventBridge Delivery** | 99.9% | < 99% |
| **Kinesis Iterator Age** | < 1000ms | > 60000ms |

---

## hAPI Database (Network Management)

The hAPI (Host API) database manages network infrastructure including hosts, services, pools, and DNS records.

### Schema Overview

```sql
-- Core hAPI tables (from infrastructure-hcore/test/hAPI.sql)

CREATE TABLE Hosts (
    hostId INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    ipAddress VARCHAR(45),
    sdcId INT,
    status ENUM('active', 'maintenance', 'offline'),
    hostType ENUM('sbc', 'media', 'app', 'db'),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sdc_status (sdcId, status),
    INDEX idx_type (hostType)
);

CREATE TABLE Services (
    serviceId INT AUTO_INCREMENT PRIMARY KEY,
    hostId INT NOT NULL,
    serviceName VARCHAR(100) NOT NULL,
    serviceType ENUM('freeswitch', 'kamailio', 'nginx', 'mysql'),
    port INT,
    status ENUM('running', 'stopped', 'failed'),
    FOREIGN KEY (hostId) REFERENCES Hosts(hostId),
    UNIQUE KEY uk_host_service (hostId, serviceName)
);

CREATE TABLE Pools (
    poolId INT AUTO_INCREMENT PRIMARY KEY,
    poolName VARCHAR(100) NOT NULL UNIQUE,
    poolType ENUM('sbc', 'media', 'app'),
    loadBalanceMethod ENUM('round_robin', 'least_conn', 'ip_hash'),
    healthCheckUrl VARCHAR(255),
    healthCheckInterval INT DEFAULT 30
);

CREATE TABLE PoolMembers (
    poolMemberId INT AUTO_INCREMENT PRIMARY KEY,
    poolId INT NOT NULL,
    hostId INT NOT NULL,
    weight INT DEFAULT 1,
    status ENUM('active', 'draining', 'disabled'),
    FOREIGN KEY (poolId) REFERENCES Pools(poolId),
    FOREIGN KEY (hostId) REFERENCES Hosts(hostId),
    UNIQUE KEY uk_pool_host (poolId, hostId)
);

CREATE TABLE Domains (
    domainId INT AUTO_INCREMENT PRIMARY KEY,
    domainName VARCHAR(255) NOT NULL UNIQUE,
    orgId INT,
    certificateId INT,
    status ENUM('active', 'pending', 'expired'),
    sslEnabled BOOLEAN DEFAULT TRUE,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### hAPI Relationships

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        hAPI Entity Relationships                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐                                                             │
│  │  SDCs   │◄──────────────┐                                            │
│  └─────────┘               │                                            │
│       │                    │                                            │
│       │ 1:N                │                                            │
│       ▼                    │                                            │
│  ┌─────────┐          ┌─────────┐          ┌─────────────────┐          │
│  │  Hosts  │◄─────────│  Pool   │          │    Services     │          │
│  └─────────┘    N:M   │ Members │          └─────────────────┘          │
│       │               └─────────┘                  ▲                    │
│       │                    │                       │                    │
│       │ 1:N                │ N:1                   │ 1:N                │
│       │                    ▼                       │                    │
│       │               ┌─────────┐                  │                    │
│       └──────────────►│  Pools  │◄─────────────────┘                    │
│                       └─────────┘                                       │
│                            │                                            │
│                            │ 1:N                                        │
│                            ▼                                            │
│                       ┌─────────┐                                       │
│                       │ Domains │                                       │
│                       └─────────┘                                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Database Connections (Platform-API)

The Platform-API application maintains connections to multiple databases. Configuration is defined in `application/config/database.php`:

### Connection Definitions

```php
// From platform-api/application/config/database.php

$db['aux'] = array(
    'dsn'      => '',
    'hostname' => getenv('AUX_DB_HOST') ?: 'aux-db.natterbox.net',
    'database' => 'aux',
    'username' => getenv('AUX_DB_USER'),
    'password' => getenv('AUX_DB_PASS'),
    'dbdriver' => 'mysqli',
    'pconnect' => FALSE,
    'db_debug' => FALSE,
    'cache_on' => FALSE,
    'char_set' => 'utf8mb4',
    'dbcollat' => 'utf8mb4_unicode_ci',
);

$db['billing'] = array(
    'hostname' => getenv('BILLING_DB_HOST') ?: 'billing-db.natterbox.net',
    'database' => 'billing',
    // ... connection settings
);

$db['org'] = array(
    'hostname' => getenv('ORG_DB_HOST') ?: 'core-db.natterbox.net',
    'database' => 'org',
    // Primary organization database
);

$db['cdr'] = array(
    'hostname' => getenv('CDR_DB_HOST') ?: 'bigdb.natterbox.net',
    'database' => 'cdr',
    // Call Detail Records
);

$db['freeswitch'] = array(
    'hostname' => getenv('FS_DB_HOST') ?: 'fs-db.natterbox.net',
    'database' => 'freeswitch',
    // FreeSWITCH CDR capture
);

$db['archiving'] = array(
    'hostname' => getenv('ARCHIVE_DB_HOST'),
    'database' => 'archiving_retention',
    // Recording archive policies
);
```

### Database Purpose Summary

| Connection | Database | Purpose | Location |
|------------|----------|---------|----------|
| `org` | CoreDB | Organizations, users, config | SDC (Master-Master) |
| `cdr` | BigDB | Call records | SDC → AWS (migrating) |
| `billing` | Billing | Subscription, invoicing | AWS RDS |
| `freeswitch` | FS CDR | Raw FreeSWITCH events | SDC |
| `aux` | Auxiliary | Temporary/operational data | SDC |
| `archiving` | Archive | Recording retention rules | AWS RDS |
| `eventLogs` | Logs | Audit and event logs | SDC |
| `lcr` | LCR | Least Cost Routing tables | SDC |

---

## Data Archiving and Retention

### Archive Purge v2 Architecture

The Archive Purge system manages retention policies for call recordings stored in S3.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Archive Purge v2 Architecture                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐  │
│  │   RDS        │     │  Lambda      │     │  S3 Batch    │     │    S3      │  │
│  │  (Policies)  │────►│  (Scanner)   │────►│   Jobs       │────►│ (Deletion) │  │
│  └──────────────┘     └──────────────┘     └──────────────┘     └────────────┘  │
│                                                                                  │
│  Flow:                                                                          │
│  1. Lambda queries RDS for recordings past retention date                       │
│  2. Creates S3 Batch Operations manifest                                        │
│  3. S3 Batch Job performs bulk deletion                                         │
│  4. Updates RDS with deletion confirmations                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Retention Policies

| Data Type | Default Retention | Configurable | Storage |
|-----------|-------------------|--------------|---------|
| Call Recordings | 90 days | Yes (org level) | S3 |
| CDR Records | 7 years | No (compliance) | BigDB/Aurora |
| Voicemail | 30 days | Yes | S3 |
| Analytics | 2 years | No | Aurora |
| Audit Logs | 7 years | No | CloudWatch/S3 |

---

## Backup and Recovery

### Core DB Backup Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Backup Architecture                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  On-Premise (SDC):                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  • Daily full backups via mariabackup                                    │   │
│  │  • Continuous binary log shipping                                        │   │
│  │  • Retention: 30 days local, 90 days S3                                  │   │
│  │  • Cross-SDC replication provides live redundancy                        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  AWS (RDS/Aurora):                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  • Automated snapshots: Daily (35-day retention)                         │   │
│  │  • Point-in-time recovery: Up to 35 days                                 │   │
│  │  • Cross-region replication: eu-west-2 → eu-west-1                       │   │
│  │  • Manual snapshots: Before major changes                                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### RDS Restore Procedure

```bash
# Restore RDS from snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier restored-db \
    --db-snapshot-identifier rds:production-2026-01-20-00-00 \
    --db-instance-class db.r6g.large \
    --vpc-security-group-ids sg-xxxxxxxx \
    --db-subnet-group-name prod-db-subnet-group

# Point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
    --source-db-instance-identifier production-db \
    --target-db-instance-identifier restored-db-pit \
    --restore-time 2026-01-20T10:30:00Z
```

---

## Monitoring and Alerting

### Key Database Metrics

| Metric | Warning | Critical | Source |
|--------|---------|----------|--------|
| **Replication Lag (Core)** | > 30s | > 60s | MariaDB |
| **DMS CDC Latency** | > 10s | > 60s | CloudWatch |
| **Aurora CPU** | > 70% | > 90% | CloudWatch |
| **Connection Count** | > 80% max | > 95% max | CloudWatch |
| **Storage Space** | < 20% free | < 10% free | CloudWatch |
| **Query Duration (P99)** | > 1s | > 5s | Slow Query Log |

### CloudWatch Dashboard

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Database Connections",
        "metrics": [
          ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "aurora-prod"]
        ],
        "period": 60
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Replication Lag",
        "metrics": [
          ["AWS/DMS", "CDCLatencySource", "ReplicationTaskIdentifier", "cdc-task-prod"]
        ],
        "period": 60
      }
    }
  ]
}
```

---

## Security

### Access Control

| Database | Authentication | Network | Encryption |
|----------|---------------|---------|------------|
| Core DB (SDC) | MySQL native auth | VPN required | TLS 1.2+ |
| Aurora | IAM + password | VPC private subnets | KMS at-rest, TLS in-transit |
| DynamoDB | IAM roles | VPC endpoints | KMS at-rest, TLS in-transit |
| RDS | IAM + password | VPC private subnets | KMS at-rest |

### Data Classification

| Classification | Examples | Handling |
|---------------|----------|----------|
| **PII** | User emails, phone numbers | Encrypted, access logged |
| **Financial** | Billing data, invoices | Encrypted, SOC2 controls |
| **Operational** | CDRs, call events | Standard encryption |
| **System** | Config, metadata | Standard controls |

---

## Troubleshooting

### Common Issues

#### 1. Master-Master Replication Conflict

**Symptoms:** Duplicate key errors, data inconsistency between SDCs

**Resolution:**
```sql
-- Check replication status
SHOW SLAVE STATUS\G

-- Identify conflicting rows
SELECT * FROM table WHERE id = <conflicting_id>;

-- Skip problematic transaction (use with caution)
STOP SLAVE;
SET GLOBAL SQL_SLAVE_SKIP_COUNTER = 1;
START SLAVE;
```

#### 2. CDC Pipeline Delay

**Symptoms:** Events not appearing in EventBridge, Kinesis iterator age increasing

**Diagnostic Steps:**
```bash
# Check DMS task status
aws dms describe-replication-tasks \
    --filters Name=replication-task-id,Values=cdc-task-prod

# Check Kinesis stream metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/Kinesis \
    --metric-name GetRecords.IteratorAgeMilliseconds \
    --dimensions Name=StreamName,Value=cdc-events-prod \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 300 \
    --statistics Maximum

# Check Lambda errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/cdc-transformer-prod \
    --filter-pattern "ERROR"
```

#### 3. Aurora Performance Degradation

**Symptoms:** Slow queries, high CPU, connection timeouts

**Resolution:**
```sql
-- Identify long-running queries
SELECT * FROM information_schema.processlist 
WHERE time > 30 ORDER BY time DESC;

-- Check for blocking
SELECT * FROM information_schema.innodb_lock_waits;

-- Review query plans
EXPLAIN ANALYZE SELECT ... ;
```

---

## Related Documentation

- [Platform-API Service Documentation](../services/platform-api.md)
- [Platform-Sapien Service Documentation](../services/platform-sapien.md)
- [CDR Processing Pipeline](./cdr-processing.md) (Coming Soon)
- [Infrastructure Overview](./infrastructure/overview.md)
- [Terraform RDS Modules](../terraform-modules/README.md)

---

## Source References

- **Schema Repository**: [redmatter/schema-api](https://github.com/redmatter/schema-api)
- **hAPI Schema**: [redmatter/infrastructure-hcore/test/hAPI.sql](https://github.com/redmatter/infrastructure-hcore/tree/main/test)
- **Platform-API DB Config**: [platform-api/application/config/database.php](https://github.com/redmatter/platform-api)
- **Confluence**: 
  - [CDC Architecture](https://natterbox.atlassian.net/wiki/spaces/EN/pages/1673789458)
  - [BigDB Migration](https://natterbox.atlassian.net/wiki/spaces/EN/pages/1859289090)
  - [CoreDB Schema](https://natterbox.atlassian.net/wiki/spaces/EN/pages/1551073301)
