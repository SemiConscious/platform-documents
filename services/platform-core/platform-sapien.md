# Platform Sapien (Public API)

**Last Updated:** 2026-01-20  
**Status:** Production  
**Repository:** [redmatter/platform-sapien](https://github.com/redmatter/platform-sapien)  
**Language:** PHP (Symfony 3 Framework)

---

## Overview

Platform Sapien is the **public-facing REST API** for the Natterbox platform, providing secure access to platform data and functionality for 3rd party clients and internal consumers. It serves as an authenticated proxy layer over the internal Core API, adding OAuth/JWT authentication, caching, and modern API features.

### Key Responsibilities

- **Public API Access**: REST HTTP API serving JSON data to external integrations
- **Authentication & Authorization**: OAuth 2.0 token-based authentication with JWT support
- **Data Aggregation**: Transposes data from multiple backend services (Core API, ArchiveD, API Gateway)
- **Event Distribution**: AMQP message queue integration for real-time event fanout
- **Recording Access**: Retrieves recordings, transcriptions, AI analysis, and talk-time results
- **ESL Events**: Listens to and processes FreeSWITCH Event Socket Layer events
- **Rate Limiting**: Organization-level API rate limiting

---

## Architecture

### System Position

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          External Consumers                             │
│      (AVS/Salesforce, CTI Adapter, Wallboards, 3rd Party Apps)         │
└─────────────────────────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        AWS API Gateway                                  │
│              (sapien-proxy - Auth0 JWT validation)                     │
│                     + Caching + Rate Limiting                          │
└─────────────────────────────────────────┬───────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PLATFORM SAPIEN                                  │
│                   (PHP Symfony - SDC Deployment)                       │
│                                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐              │
│  │ SapienBundle  │  │ FreeSWitch    │  │ Archiving     │              │
│  │ (Core Logic)  │  │ Bundle        │  │ Bundle        │              │
│  └───────────────┘  └───────────────┘  └───────────────┘              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐              │
│  │ BlobStorage   │  │ UserBundle    │  │ OAuth Server  │              │
│  │ Bundle        │  │               │  │ Bundle        │              │
│  └───────────────┘  └───────────────┘  └───────────────┘              │
└─────────────────────────────────────────┬───────────────────────────────┘
                                          │
             ┌──────────────┬─────────────┼─────────────┬────────────────┐
             │              │             │             │                │
             ▼              ▼             ▼             ▼                ▼
      ┌──────────┐   ┌──────────┐  ┌───────────┐ ┌──────────┐    ┌─────────┐
      │ Core API │   │ Core DB  │  │  Big DB   │ │ ArchiveD │    │   MQ    │
      │ (Port 80)│   │  (MySQL) │  │  (MySQL)  │ │(Storage) │    │ (AMQP)  │
      └──────────┘   └──────────┘  └───────────┘ └──────────┘    └─────────┘
```

### Service Description

> REST HTTP monolithic API serving data from Core and Big DBs in JSON to 3rd party clients and internal clients (AVS, CTI and others involved in auth such as Gatekeeper). It also connects to and transposes data from CoreAPI to retrieve DialPlans, ArchiveD to retrieve recordings, transcriptions, AI analysis, and talk-time results and API gateway to fetch analysis result statuses. Runs in the SDCs only.

### Related Services

| Service | Relationship | Description |
|---------|-------------|-------------|
| **Platform API (Core API)** | Backend | Internal API that Sapien proxies and extends |
| **Sapien Proxy** | Frontend | AWS API Gateway layer for Auth0 JWT validation and caching |
| **Gatekeeper** | Consumer | Authorization service that validates Sapien tokens |
| **AVS (Salesforce)** | Consumer | Salesforce package integrating via Sapien |
| **CTI Adapter** | Consumer | Browser-based telephony controls |
| **ArchiveD** | Backend | Recording and archiving storage service |
| **ESL Listener** | Component | FreeSWITCH event processing service |

---

## Repository Structure

```
platform-sapien/
├── core/                           # Main Sapien API application
│   ├── build/                      # Build configuration
│   ├── project/
│   │   ├── app/                    # Symfony application config
│   │   │   └── config/             # Configuration files
│   │   ├── src/Redmatter/
│   │   │   ├── SapienBundle/       # Main API bundle
│   │   │   │   ├── Controller/     # API controllers
│   │   │   │   ├── Entity/         # Doctrine entities
│   │   │   │   ├── Manager/        # Business logic managers
│   │   │   │   ├── Repository/     # Data repositories
│   │   │   │   ├── Security/       # Security components
│   │   │   │   ├── Event/          # Event definitions
│   │   │   │   └── Resources/      # Bundle resources
│   │   │   ├── ArchivingBundle/    # Recording/archiving functionality
│   │   │   ├── BlobStorageBundle/  # File storage operations
│   │   │   ├── FreeswitchBundle/   # FreeSWITCH integration
│   │   │   ├── UserBundle/         # User management
│   │   │   ├── HelloBundle/        # Test/health check
│   │   │   └── TestBundle/         # Testing utilities
│   │   ├── tests/                  # Unit tests
│   │   ├── web/                    # Web root
│   │   └── composer.json           # PHP dependencies
│   └── Dockerfile                  # Container definition
├── esl-listener-server/            # ESL event listener service
│   ├── project/                    # Listener application
│   └── Dockerfile
├── front-end/                      # NGINX frontend proxy
├── mq/                             # Message queue components
│   ├── consumer/                   # MQ consumer service
│   ├── publisher/                  # MQ publisher service
│   └── server/                     # RabbitMQ server config
├── database/                       # Database setup/migrations
├── codeception/                    # Integration tests
├── mock-server/                    # Testing mock server
├── sandbox/                        # API sandbox/documentation
├── storage-gateway/                # MinIO for local dev
├── docker-compose.yml              # Docker orchestration
└── cli.bash                        # CLI development tools
```

---

## API Endpoints

### Authentication

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/token` | POST | No | OAuth token generation |
| `/v1/test/unsecure` | GET | No | Unsecured test endpoint |
| `/v1/test/secure` | GET | Yes | Secured test endpoint |

### User Operations

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/v1/user/me` | GET | Yes | Get current user details |
| `/v1/user` | GET | Yes | Get user by username |
| `/v1/organisation/{org_id}/user` | GET | Yes | List users in organization |
| `/v1/organisation/{org_id}/user/{user_id}/skill` | GET | Yes | Get user skills |
| `/v1/organisation/{org_id}/user/{user_id}/log/call` | GET | Yes | Get user call logs |

### Call Data

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/v1/organisation/{org_id}/log/call` | GET | Yes | Organization call logs |
| `/v1/organisation/{org_id}/call/statistic` | GET | Yes | Call statistics |
| `/v1/organisation/{org_id}/call-queue/{queue_id}/statistic` | GET | Yes | Queue statistics |

### Skills & Groups

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/v1/organisation/{org_id}/skill/{skill_id}/user` | GET | Yes | Users with skill |
| `/v1/organisation/{org_id}/user-group/event` | GET | Yes | User group events |

### Media Files

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/v1/organisation/{org_id}/user/{user_id}/voicemail/{voicemail_id}` | GET | Yes | Download voicemail (Lambda) |
| `/v1/organisation/{org_id}/voicemail-drop/{voicemail_drop_id}` | GET | Yes | Download voicemail drop (Lambda) |

---

## Authentication

### OAuth 2.0 Flow

Sapien implements OAuth 2.0 with the following entities:

| Entity | Description |
|--------|-------------|
| `Client` | OAuth client credentials (client_id, client_secret) |
| `AccessToken` | Short-lived access tokens |
| `RefreshToken` | Long-lived refresh tokens |
| `AuthCode` | Authorization codes for code flow |

### Token Request

```bash
curl -X POST https://api.natterbox.com/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

### JWT Authentication (via Sapien Proxy)

External requests go through the AWS API Gateway (sapien-proxy) which:
1. Validates Auth0 JWT tokens in the `Authorization` header
2. Caches authorization results for TTL period
3. Applies rate limiting based on usage plans
4. Forwards authenticated requests to Sapien

---

## Core Components

### SapienBundle

The main bundle containing:
- **Controllers**: OAuth, OAuthToken, and abstract controllers
- **Entities**: AccessToken, RefreshToken, Client, CoreApiSession, EventLog, OrganisationApiRateLimit
- **Managers**: Business logic for data operations
- **Repositories**: Database access layer
- **Security**: Authentication providers and voters

### FreeswitchBundle

Integration with FreeSWITCH telephony:
- ESL event processing
- Call state management
- User availability tracking

### ArchivingBundle

Recording and archiving functionality:
- Recording retrieval from ArchiveD
- Transcription access
- AI analysis results
- Talk-time statistics

### BlobStorageBundle

File storage operations:
- S3/MinIO integration
- Voicemail storage
- Sound file management

---

## ESL Listener Service

A separate PHP application that processes FreeSWITCH events:

### Events Published

| Event | Description |
|-------|-------------|
| `SapienEvent::UserAvailabilityUpdate` | User availability changes |
| `SapienEvent::AvailabilityProfileUpdate` | Availability profile updates |

### Architecture

```
FreeSWITCH ──ESL Port 8021──> ESL Listener ──AMQP──> RabbitMQ ──> Consumers
```

---

## Message Queue Integration

### RabbitMQ Exchanges

| Exchange | Type | Purpose |
|----------|------|---------|
| `events` | fanout | User and user group events |

### AMQP Publishing

Sapien publishes events to MQ for:
- Real-time user availability updates
- Call state changes
- System events

---

## Sapien Proxy (AWS API Gateway)

The `aws-terraform-sapien-proxy` module provides:

### Features

| Feature | Implementation |
|---------|----------------|
| JWT Validation | Custom Lambda authorizer with Auth0 |
| Caching | API Gateway caching on GET requests |
| Rate Limiting | Usage plans (planned) |
| CORS | Mock integration for OPTIONS |
| Binary Media | PDF, audio, and other binary types |

### Lambda Functions

| Function | Purpose |
|----------|---------|
| Lambda Authorizer | JWT validation against Auth0 |
| File Service | Voicemail/file retrieval (30s timeout) |

### Terraform Resources

```
aws-terraform-sapien-proxy/
├── api-gateway.tf        # API Gateway configuration
├── lambda-authoriser.tf  # JWT validation Lambda
├── lambda-file-service.tf # File retrieval Lambda
├── sapien.openapi30.yaml # OpenAPI specification
├── cors.yaml             # CORS configuration
├── dns.tf                # Route53 DNS setup
└── dashboard.tf          # CloudWatch dashboard
```

---

## Deployment

### Production (SDC)

Sapien runs in Docker containers within SDCs (Secure Data Centers):

| Component | Container | Port |
|-----------|-----------|------|
| Sapien Core | `sapien-core` | 80 (internal) |
| Frontend (NGINX) | `sapien-front-end` | 80, 443 |
| ESL Listener | `esl-listener` | 4444 |

### Configuration Files

| Path | Description |
|------|-------------|
| `/var/www/sapien/app/config` | Application configuration |
| `/var/www/sapien` | Application directory |

### Log Files

| Location | Description |
|----------|-------------|
| Log boxes `/var/log/app/sapien.log` | Application logs |

### Service Management

```bash
# Restart Sapien container
sudo docker restart <container_id>

# View container logs
sudo docker logs sapien-core
```

---

## Local Development

### Prerequisites

- Docker and Docker Compose v2
- PHP 7.4 environment (optional, for IDE support)
- Access to Docker registry (`docker-registry.redmatter.com`)

### Quick Start

```bash
# Clone repository
git clone git@github.com:redmatter/platform-sapien.git
cd platform-sapien

# Install dependencies
docker compose run composer-install

# Start services
docker compose up -d

# Access API
curl http://localhost/v1/test/unsecure
```

### Development Services

| Service | URL | Description |
|---------|-----|-------------|
| Sapien API | http://localhost/v1 | Main API endpoints |
| RabbitMQ UI | http://localhost:8080 | MQ management |
| Mock Server | Internal | Testing mocks |
| ESL Listener | :4444 | ESL events |

### CLI Commands

```bash
# Source CLI tools
source cli.bash

# Generate API documentation
d-sapien-core generate_docs

# Run unit tests
docker compose run sapien-unit-tests

# Run integration tests
docker compose run sapien-tests --env=dev --no-rebuild
```

---

## Testing

### Unit Tests

```bash
docker compose run sapien-unit-tests
```

Configuration: `/tests/phpunit.xml.dist`

### Integration Tests (Codeception)

```bash
docker compose run sapien-tests --env=dev
```

### Code Quality

```bash
# PHPStan static analysis
docker compose run phpstan

# PHP CodeSniffer (PSR-12)
docker compose run phpcs

# Security vulnerability check
docker compose run check-security
```

---

## Monitoring

### Health Checks

Sapien Service Availability runs in AWS and:
- Polls health check endpoint within Sapien
- Triggers CloudWatch alarms on failure
- Sapien tests cron for additional monitoring

### Runbooks

| Runbook | Purpose |
|---------|---------|
| [Codeception Sapien is Critical](https://natterbox.atlassian.net/wiki/spaces/RUN/pages/.../Codeception+Sapien+is+Critical+-+TBR) | Test failures |
| [Container Health is Critical](https://natterbox.atlassian.net/wiki/spaces/RUN/pages/.../Container+Health+is+Critical+-+TBR) | Container health issues |

### Failover

Standard SDC failover (all-or-nothing, not application specific).

**Known Issues**: All-or-nothing failover means Sapien cannot be failed over independently of other SDC services.

---

## Impact Analysis

### If Sapien Stops Working

**Severity: High**

If Sapien is not operating:
- Internal and 3rd party clients will fail to save or retrieve data
- **Authentication failures** - especially critical for Gatekeeper
- AVS/Salesforce integration will fail
- CTI adapter will lose functionality
- Wallboards will stop updating

---

## Integration Points

### Inbound (Consumers)

| Consumer | Protocol | Description |
|----------|----------|-------------|
| AVS (Salesforce) | HTTPS | Salesforce CTI integration |
| CTI Adapter | HTTPS | Browser-based call controls |
| Gatekeeper | HTTPS | Auth token validation |
| Wallboards | HTTPS | Real-time statistics |
| 3rd Party Apps | HTTPS | Custom integrations |

### Outbound (Dependencies)

| Service | Protocol | Port | Description |
|---------|----------|------|-------------|
| Core API | HTTP | 80 | Configuration and call data |
| Core DB | MySQL | 3306 | Direct database access |
| Big DB | MySQL | 3306 | CDR and analytics data |
| ArchiveD | HTTP | 80 | Recordings and transcriptions |
| FreeSWITCH ESL | TCP | 8021 | Event socket connection |
| RabbitMQ | AMQP | 5672 | Event publishing |

---

## Related Documentation

### Repositories

- **Sapien Core**: [platform-sapien](https://github.com/redmatter/platform-sapien)
- **Sapien Proxy**: [aws-terraform-sapien-proxy](https://github.com/redmatter/aws-terraform-sapien-proxy)
- **Core API**: [platform-api](https://github.com/redmatter/platform-api)
- **Gatekeeper**: [go-gatekeeper-authoriser](https://github.com/redmatter/go-gatekeeper-authoriser)

### Confluence Documentation

- [Sapien Engineering Docs](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/939819009/Sapien)
- [Sapien Service Overview](https://natterbox.atlassian.net/wiki/spaces/A/pages/1717141524/Sapien+Service+Overview)
- [Developer Commands](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/939753475/Developer+Commands)

---

## Key Contacts

| Role | Team |
|------|------|
| SME | VoIP Chapter |
| Development | VoIP Chapter |
| Operations | Platform Operations |

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial documentation | Documentation Agent |

---

*This documentation is part of the Platform Documentation Project. For updates or corrections, please submit a PR to the platform-documents repository.*
