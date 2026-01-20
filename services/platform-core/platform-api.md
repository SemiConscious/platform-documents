# Platform API (Core API)

**Last Updated:** 2026-01-20  
**Status:** Production  
**Repository:** [redmatter/platform-api](https://github.com/redmatter/platform-api)  
**Language:** PHP (Kohana Framework)

---

## Overview

The Platform API, historically known as **Core API** or **RM-API**, is the central REST API service for the Natterbox platform. It acts as the main hub for both machine and human interfacing, providing the primary interface for interacting with the platform's core databases.

### Key Responsibilities

- **Configuration Management**: User, organization, device, and number management
- **Call Control**: Real-time call control operations
- **Database Interface**: Central hub for all database operations (Core DB and Big DB)
- **FreeSWITCH Integration**: Supporting dialplan execution and call processing
- **Authentication & Authorization**: User authentication and session management
- **CDR Processing**: Call Detail Record management interface
- **Storage Gateway**: File and recording management

---

## Architecture

### System Position

```
┌─────────────────────────────────────────────────────────────────────┐
│                        External Consumers                            │
│   (AVS/Salesforce, CTI Adapter, Freedom Mobile, Wallboards, etc.)  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Platform Sapien                              │
│              (Public API with Auth0 Authentication)                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PLATFORM API                                 │
│                   (Internal Core API - PHP)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Controllers │  │   Models    │  │   Config    │  │  Libraries │ │
│  │  (79 files) │  │             │  │             │  │            │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐  ┌──────────┐  ┌──────────┐
             │ Core DB  │  │  Big DB  │  │ Memcache │
             │  (MySQL) │  │ (MySQL)  │  │ (Cache)  │
             └──────────┘  └──────────┘  └──────────┘
```

### Related Services

| Service | Relationship | Description |
|---------|-------------|-------------|
| **Platform Sapien** | Proxy Layer | Public-facing API that wraps Core API with Auth0 authentication |
| **fsxinetd** | Consumer | Uses Core API for dialplan execution and call data |
| **CDRMunch** | Consumer | Sends CDR data through Core API interfaces |
| **AVS (Salesforce)** | Consumer | Salesforce package that integrates via Sapien/Core API |
| **FreeSWITCH** | Integration | Receives configuration and dialplan data |
| **Delta API** | Successor | New microservice gradually replacing Core API functionality |

---

## Repository Structure

```
platform-api/
├── application/
│   ├── cache/              # Application cache directory
│   ├── config/             # Configuration files
│   │   ├── config.php      # Main application config
│   │   ├── coreapi.php     # Core API specific settings
│   │   ├── database.php    # Database connections
│   │   ├── oauth.php       # OAuth configuration
│   │   └── ...
│   ├── controllers/        # API endpoint controllers (79 files)
│   │   ├── archiving.php   # Archiving operations
│   │   ├── callcontrol.php # Real-time call control
│   │   ├── cdrmunch.php    # CDR processing interface
│   │   ├── dialplan.php    # Dialplan management
│   │   ├── freeswitch.php  # FreeSWITCH integration
│   │   ├── orgs.php        # Organization management
│   │   ├── users.php       # User management
│   │   ├── numbers.php     # Number management
│   │   └── ...
│   ├── helpers/            # Helper functions
│   ├── hooks/              # Application hooks
│   ├── libraries/          # Shared libraries
│   ├── models/             # Data models
│   ├── schemas/            # JSON schemas
│   └── views/              # View templates
├── sql/
│   ├── core/               # Core DB initialization
│   └── big/                # Big DB initialization
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container definition
├── composer.json           # PHP dependencies
└── README.md               # Repository documentation
```

---

## API Endpoint Categories

The Platform API exposes approximately **79 controllers** covering various domains:

### Core Configuration

| Endpoint | Controller | Description |
|----------|------------|-------------|
| `/orgs` | `orgs.php` | Organization management |
| `/users` | `users.php` | User management and profiles |
| `/devices` | `devices.php` | Device configuration |
| `/numbers` | `numbers.php` | Phone number management |
| `/groups` | `groups.php` | Group management |
| `/permissions` | `permissions.php` | Permission management |

### Telephony Operations

| Endpoint | Controller | Description |
|----------|------------|-------------|
| `/callcontrol` | `callcontrol.php` | Real-time call control operations |
| `/dialplan` | `dialplan.php` | Dialplan configuration |
| `/freeswitch` | `freeswitch.php` | FreeSWITCH integration |
| `/trunks` | `trunks.php` | SIP trunk management |
| `/siptrunk` | `siptrunk.php` | SIP trunk configuration |
| `/sipuris` | `sipuris.php` | SIP URI management |
| `/voicemail` | `voicemail.php` | Voicemail configuration |

### Data & Reporting

| Endpoint | Controller | Description |
|----------|------------|-------------|
| `/cdrmunch` | `cdrmunch.php` | CDR processing interface |
| `/logs` | `logs.php` | Call logs access |
| `/eventlog` | `eventlog.php` | Event logging |
| `/archiving` | `archiving.php` | Data archiving operations |

### Integration

| Endpoint | Controller | Description |
|----------|------------|-------------|
| `/auth` | `auth.php` | Authentication |
| `/oauthcallback` | `oauthcallback.php` | OAuth callbacks |
| `/dataconnector` | `dataconnector.php` | External data connectors |
| `/opensips` | `opensips.php` | OpenSIPS integration |

---

## Database Architecture

### Core Database

The Core DB stores configuration and transactional data:
- Organization and user configuration
- Device and number assignments
- Routing policies and dialplans
- System settings and permissions

### Big Database

The Big DB stores high-volume operational data:
- Call Detail Records (CDRs)
- Call logs and analytics
- Recording metadata
- Historical data

### Database Schema

Schema migrations are managed via the `schema-api` repository containing:
- ~238 migration files dating from 2010 to present
- Timestamped PHP migration scripts
- Master schema definition (`schema.php`)

SQL initialization files use prefix conventions:

| Prefix | Purpose |
|--------|---------|
| `20` | Database structure |
| `30` | Database grants |
| `50` | Base/seed data (Org 0, etc.) |
| `90` | Health check grants |

---

## Deployment

### Container Deployment

Platform API runs as a Docker container with Apache:

```bash
# Build the image
docker-compose build app

# Run in production mode
docker-compose up -d app

# Run in dev mode (with mounted volumes)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d app
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ALLOWED_HOSTS` | Comma-separated CIDR ranges for Apache Allow directive | `10.0.0.0/8,192.168.0.0/16` or `all` |
| Database credentials | Via config files | See `application/config/database.php` |

### Health Checks

The API exposes health check endpoints that are enabled after database initialization completes (via `90` prefix grants).

---

## Migration Strategy

### Current State

Core API is a **legacy monolithic service** that is being gradually decomposed using the **Strangler Fig Pattern**. New functionality should be built in microservices, while existing functionality is migrated incrementally.

### Delta API Migration

The [Delta API](https://github.com/redmatter/delta) is the modern successor, implementing:
- TypeScript/Node.js implementation
- AWS-native deployment (Lambda, API Gateway)
- GraphQL interface via AppSync

### Decision Framework

When determining whether to modify Core API or build new:

| Scenario | Recommendation |
|----------|----------------|
| Feature scheduled for replacement | Use Core API (temporary) |
| High complexity / transactional safety required | Use Core API |
| Simple, low-risk, isolated feature | Rebuild in Delta API |
| New feature with no legacy equivalent | Build in Delta API |

See Confluence: [Core API Migration Strategy & Guide](https://natterbox.atlassian.net/wiki/spaces/A/pages/2546466818/Core+API+Migration+Strategy+Guide)

---

## Integration Points

### With FreeSWITCH (via fsxinetd)

Core API provides configuration data to FreeSWITCH through the fsxinetd service:
- Dialplan XML generation
- User directory lookups
- Call routing decisions
- Real-time call control

### With Salesforce (via AVS)

The AVS Salesforce package interacts with Core API through Platform Sapien:
- User synchronization
- Click-to-dial operations
- Call logging
- Screen pop data

### With Platform Sapien

Sapien acts as the public-facing proxy layer:
- Auth0 JWT validation
- Request routing to Core API
- Response transformation
- Rate limiting

---

## Testing

### Codeception Tests

```bash
cd codeception
docker-compose run --rm composer-install
docker-compose build tests

# Run all tests
docker-compose run --rm tests

# Run specific test suite
docker-compose run --rm tests API HealthCest.php --debug
```

---

## Related Documentation

### Internal Resources

- **Repository**: [platform-api](https://github.com/redmatter/platform-api)
- **Schema**: [schema-api](https://github.com/redmatter/schema-api)
- **Sapien Proxy**: [platform-sapien](https://github.com/redmatter/platform-sapien)
- **Delta API**: [delta](https://github.com/redmatter/delta)

### Confluence Documentation

- [Sapien API Overview](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/939819009/Sapien)
- [Core API Migration Strategy](https://natterbox.atlassian.net/wiki/spaces/A/pages/2546466818/Core+API+Migration+Strategy+Guide)
- [Strategy and Architecture for APIs](https://natterbox.atlassian.net/wiki/spaces/A/pages/1539604500/Strategy+and+Architecture+for+APIs)
- [Requirements for Building APIs](https://natterbox.atlassian.net/wiki/spaces/A/pages/1521745929/Requirements+for+Building+APIs)

---

## Key Contacts

| Role | Team |
|------|------|
| Development | VoIP Chapter |
| Operations | Platform Operations |
| Architecture | Architecture Team |

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial documentation | Documentation Agent |

---

*This documentation is part of the Platform Documentation Project. For updates or corrections, please submit a PR to the platform-documents repository.*
