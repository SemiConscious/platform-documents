# Database Architecture Overview

**Last Updated:** 2026-01-20  
**Status:** Production (Migration In Progress)  
**Technology:** MariaDB/MySQL (on-premises), Aurora MySQL (AWS)

---

## Executive Summary

The Natterbox platform uses a MySQL-based relational database architecture distributed across two primary database tiers: **Core DB** (CoreDB) and **Big DB** (BigDB). The platform is currently undergoing a strategic migration from on-premises MariaDB to AWS Aurora MySQL, with a longer-term vision to move certain workloads to DynamoDB.

### Key Databases

| Database | Purpose | Current Location | Future State |
|----------|---------|------------------|--------------|
| **Core DB** | Platform configuration (orgs, users, devices, numbers) | On-premises (SDC) + RT | DynamoDB-based microservices |
| **Big DB** | High-volume operational data (CDRs, call logs, tasks) | On-premises (SDC) | AWS Aurora MySQL + DynamoDB |
| **LCR DB** | Least Cost Routing data | On-premises | DynamoDB |
| **ArchivingRetention DB** | Archiving policies and retention metadata | AWS | AWS Aurora |
| **Queue DB** | Task queue management | On-premises (CDR hosts) | AWS Aurora Serverless |
| **Billing DB** | Billing and cost data | On-premises | TBD |

---

## Architecture Overview

### Current Database Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SDC (Service Data Centres)                         │
│                          (LON1 / LON2 - On-Premises)                        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    Core DB      │    │    Big DB       │    │    LCR DB       │         │
│  │   (MariaDB)     │    │   (MariaDB)     │    │   (MariaDB)     │         │
│  │                 │    │                 │    │                 │         │
│  │ • Config data   │    │ • CDR tasks     │    │ • Routing rates │         │
│  │ • User mgmt     │◄───│ • Call logs     │    │ • Carriers      │         │
│  │ • Org settings  │    │ • Recording meta│    │ • Gateways      │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                    Master-Master │Replication                               │
└────────────────────────────────────────────────────────────────────────────┘
                                   │
                            ┌──────┴──────┐
                            │  Geoshim    │
                            │  (Cache)    │
                            └──────┬──────┘
                                   │
┌──────────────────────────────────┼──────────────────────────────────────────┐
│                          RT (Real-Time) Regions                             │
│                               (AWS)                                         │
│  ┌─────────────────┐    ┌─────────────────┐                                │
│  │  Core DB        │    │  Queue DB       │                                │
│  │  Read Replica   │    │  (Aurora        │                                │
│  │  (Single AZ)    │    │  Serverless)    │                                │
│  └─────────────────┘    └─────────────────┘                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ArchivingRetention DB                            │   │
│  │                    (Aurora MySQL - eu-west-2)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Access Patterns

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                  │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Platform    │  │   Sapien     │  │  CDRMunch    │  │   Toolbox    │  │
│  │    API       │  │    API       │  │  Services    │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         XDatabase Layer                                  │
│              (Connection abstraction with named aliases)                 │
│                                                                          │
│   Aliases: LCR_RO, BigDB, CoreDB, ArchivingRetention, Billing, etc.    │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    hAPI (Environment Configuration)                     │
│               (Auto-configuration and DNS resolution)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Database (CoreDB)

### Purpose

The Core Database stores **platform configuration and transactional data**:

- Organization configuration and settings
- User accounts and profiles
- Device registrations and assignments
- Phone number inventory and assignments
- Routing policies and dialplans
- System settings and permissions
- Feature configurations

### Schema Management

Schema migrations are managed via the **schema-api** repository:

- ~238 migration files (2010 to present)
- Timestamped PHP migration scripts
- Master schema definition (`schema.php`)

**SQL File Conventions:**

| Prefix | Purpose |
|--------|---------|
| `20` | Database structure (tables, indexes) |
| `30` | Database grants (permissions) |
| `50` | Base/seed data (Org 0, etc.) |
| `90` | Health check grants |

### Replication

- **Master-Master replication** between SDC data centres
- **Auto-increment offsets** used to prevent ID collisions
- **Geoshim** provides caching for RT regions

### Current Limitations

1. **Single-AZ deployment** in RT regions (reliability risk)
2. **No maintenance windows** flexibility
3. **Geoshim dependency** for read scaling
4. **SDC dependency** for write operations from RT

---

## Big Database (BigDB)

### Purpose

The Big Database stores **high-volume operational data**:

- Call Detail Record (CDR) task processing queue
- Call logs and analytics data
- Recording metadata
- Application blobs
- Historical operational data

### Key Tables

| Table/Schema | Purpose |
|--------------|---------|
| `CDR tasks` | Task queue for post-call processing |
| `Call logs` | Historical call records |
| `ApplicationBlob` | Application-specific data storage |
| `WholesaleCallCostCache` | Call cost caching for fraud detection |
| `Toolbox` | Toolbox application data |

### Data Distribution

BigDB data is categorized by **Home Region (HR)**:

- Data owned by an OrgID stored in the selected cluster
- Tech data (Toolbox, operational data) stored separately
- Migration strategy maintains data residency requirements

### Challenges

1. **Data residency requirements** - stricter regional data laws
2. **Scalability constraints** - single host per SDC limitation
3. **Purge capacity** - retention processing lagging behind

---

## LCR Database

### Purpose

The LCR (Least Cost Routing) database stores **routing and carrier data**:

- Carrier information and rates
- Gateway configurations and health
- Number plan lookups
- Charge bands and rate periods
- Override rules

### Key Tables

| Table | Purpose |
|-------|---------|
| `LCR.Numbers` | Number prefix lookups |
| `LCR.Bands` | Charge band definitions |
| `LCR.LCRRates` | Rate information |
| `LCR.Carriers` | Carrier configurations |
| `LCR.CarrierGateway` | Gateway definitions |
| `LCR.CarrierGatewayHealth` | Gateway health status |
| `LCR.Overrides` | Routing override rules |
| `LCR.ClosedLoopCarriers` | Closed-loop carrier assignments |
| `LCR.Formats` | Number formatting rules |

### Access Pattern

- **Read-only** connections (`LCR_RO` alias) from Core API
- **Heavy caching** for performance
- Used during real-time call routing decisions

---

## Post-Call Processing Databases

### Queue Database

Used by ArchiveD for queue management:

```
┌─────────────────┐
│  ArchiveDQueue  │  - Task queue entries
│     (Table)     │  - Survives crashes/restarts
│                 │  - Auto-increment offset based
└─────────────────┘
```

### Retention Database

Stores archiving metadata:

```
┌─────────────────┐
│ArchivingRetention│  - Object metadata
│    Database      │  - Retention rules
│    (Aurora)      │  - Space usage statistics
└─────────────────┘
```

### CDR Tasks Database

Used by CDRMunch services:

```
┌─────────────────┐
│  CDR Tasks      │  - Post-call task queue
│    Table        │  - Task types and status
│   (BigDB)       │  - Processing state
└─────────────────┘
```

---

## Migration Strategy

### Phase 1: BigDB to AWS (In Progress)

**Goal:** Move BigDB to AWS Aurora MySQL using ProxySQL as a proxy layer.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Migration Architecture                          │
│                                                                         │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐     │
│  │  Existing    │        │   ProxySQL   │        │ AWS Aurora   │     │
│  │  MariaDB     │◄──────►│   (Proxy)    │◄──────►│   MySQL      │     │
│  │  (On-prem)   │   DMS  │              │        │   (Target)   │     │
│  └──────────────┘        └──────────────┘        └──────────────┘     │
│                                                                         │
│  Components:                                                            │
│  • ProxySQL on Nexus (both regions)                                    │
│  • ProxySQL on-prem (both SDCs) for local access                       │
│  • AWS DMS for continuous replication                                  │
│  • Per-OrgID migration strategy                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Requirements:**
- No downtime during migration
- Per-OrgID migration with Home Region (HR) awareness
- ProxySQL for query routing during transition
- DMS for data synchronization

### Phase 2: CoreDB Modernization

**Goal:** Replace CoreDB access with new TypeScript microservices using DynamoDB.

**Approach: Strangler Fig Pattern**
1. Create new TypeScript API service (initially connecting to MySQL)
2. Update client applications to use new API
3. Switch service to DynamoDB backend
4. Decommission legacy MySQL access

**Benefits:**
- Reduced tech debt
- Modern TypeScript architecture
- DynamoDB scalability (multi-AZ, global tables)
- No maintenance windows
- Encrypted data at rest and in transit

### Phase 3: LCR Service Migration

The LCR service is a primary candidate for modernization:

1. **Assess** existing PHP code and dependencies
2. **Convert** to TypeScript Lambda functions
3. **Migrate** data to DynamoDB
4. **Switch** clients to new API endpoints

---

## Geoshim (Database Cache Layer)

### Purpose

Geoshim provides **database caching and replication** for RT regions:

- Reduces latency for database reads
- Caches CoreDB data locally in RT regions
- Handles read/write splitting

### Future State

With ProxySQL deployment, Geoshim may be **retired**:

> "If ProxySQL were deployed effectively within the RT platform environment, it might enable the retirement of Geoshim. A CoreAPI instance running locally could direct all its database requests to a local ProxySQL instance, which could serve reads locally and intelligently route write operations to the central master database instance."

---

## Database Connection Management

### XDatabase Layer

Applications use the `XDatabase` abstraction layer:

```php
// Example: Get LCR read-only connection
$connection = XDatabase::GetConnection('LCR_RO');

// Execute query
$result = $connection->query($sql, $params);
```

### Connection Aliases

| Alias | Database | Access |
|-------|----------|--------|
| `LCR_RO` | LCR Database | Read-only |
| `BigDB` | Big Database | Read/Write |
| `CoreDB` | Core Database | Read/Write |
| `ArchivingRetention` | Retention DB | Read/Write |
| `Billing` | Billing Database | Read/Write |

### Configuration

Database connections configured via:
- `hAPI` for environment-based auto-configuration
- `application/config/database.php` in Platform API
- Environment variables for container deployments

---

## Monitoring & Operations

### Key Metrics

| Metric | Description |
|--------|-------------|
| Connection pool usage | Active/idle connections |
| Query latency | P50/P95/P99 query times |
| Replication lag | DMS or master-slave lag |
| Storage usage | Disk space consumption |
| IOPS | Input/output operations |

### Monitoring Tools

- **Nagios** - Traditional on-premises monitoring
- **CloudWatch** - AWS Aurora metrics
- **DMS metrics** - Migration replication status

### Backup Strategy

| Database | Backup Method | Frequency |
|----------|---------------|-----------|
| On-prem MariaDB | Traditional backup scripts | Daily |
| Aurora MySQL | Automated snapshots | Continuous |
| DynamoDB | Point-in-time recovery | Continuous |

---

## Data Residency

### Requirements

- Data stored in appropriate Home Region (HR)
- Compliance with regional data laws (GDPR, etc.)
- Customer-specific storage requirements

### Implementation

- Per-OrgID database clustering
- Home Region lookup for routing
- ProxySQL rules for region-aware routing

---

## Related Documentation

### Internal Resources

- **Repository**: [schema-api](https://github.com/redmatter/schema-api) - Database schema migrations
- **Platform API**: [platform-api](https://github.com/redmatter/platform-api) - Core API with database access
- **CDRMunch**: [platform-cdrmunch](https://github.com/redmatter/platform-cdrmunch) - CDR processing

### Confluence Documentation

- [BigDB Requirements](https://natterbox.atlassian.net/wiki/spaces/df/pages/1859289090/BigDB+requirements)
- [BigDB Architect Requirements](https://natterbox.atlassian.net/wiki/spaces/df/pages/1954938886/BigDB+architect+requirements)
- [SDC API Modernization](https://natterbox.atlassian.net/wiki/spaces/~897029173/pages/2318827569/SDC+API+modernization)
- [Post Call Processing Services](https://natterbox.atlassian.net/wiki/spaces/df/pages/1269465093/Post+Call+Processing+Services)
- [Current Architecture Overview](https://natterbox.atlassian.net/wiki/spaces/df/pages/1785757705/Current+Architecture+Overview)

### Related Platform Documentation

- [Platform API Documentation](/services/platform-core/platform-api.md)
- [Platform Sapien Documentation](/services/platform-core/platform-sapien.md)
- [CDR Processing Pipeline](/architecture/voice-routing/overview.md)

---

## Key Contacts

| Role | Team |
|------|------|
| Database Architecture | Architecture Team |
| Migration | Platform Engineering |
| Operations | Platform Operations |
| Development | VoIP Chapter |

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial documentation | Documentation Agent |

---

*This documentation is part of the Platform Documentation Project. For updates or corrections, please submit a PR to the platform-documents repository.*
