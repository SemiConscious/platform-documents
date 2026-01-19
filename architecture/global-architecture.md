# Natterbox Global Platform Architecture

> **Last Updated:** 2026-01-19  
> **Source:** Confluence Architecture Space + Platform Analysis  
> **Status:** ✅ Complete

---

## Overview

The Natterbox platform is a globally distributed, multi-tenant telephony and communications platform built on three key clouds:

1. **Amazon AWS** - Primary infrastructure (target architecture)
2. **Natterbox Global Private Cloud** - Legacy on-premise data centres (being migrated)
3. **Salesforce** - Service administration and end-user CRM integration

The platform has been designed from the ground up as a true **multi-tenant environment**, with all customers sharing infrastructure while data and operations are logically segregated.

---

## Global Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          GLOBAL ARCHITECTURE                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐     │
│   │   SALESFORCE     │      │    AWS NEXUS     │      │   AWS PLATFORM   │     │
│   │   (Admin/CRM)    │◄────►│   (Global Svcs)  │◄────►│   VPC Services   │     │
│   └──────────────────┘      └──────────────────┘      └──────────────────┘     │
│            │                         │                         │                │
│            │                         │                         │                │
│            ▼                         ▼                         ▼                │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        GLOBAL VOICE NETWORK                              │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │  │
│   │  │ RT US-W │  │ RT US-E │  │ RT LON  │  │ RT FRA  │  │ RT SIN  │       │  │
│   │  │ Oregon  │  │Virginia │  │ London  │  │Frankfurt│  │Singapore│       │  │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │  │
│   │       │            │            │            │            │              │  │
│   │       └────────────┴─────┬──────┴────────────┴────────────┘              │  │
│   │                          │                                                │  │
│   │                   Global Mesh Network                                     │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                    LEGACY (Being Migrated)                               │  │
│   │       ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│   │       │  SDC 1  │  │  SDC 2  │  │  GDC    │  │ Hybrid  │               │  │
│   │       │ London  │  │ London  │  │ Various │  │  VPCs   │               │  │
│   │       └─────────┘  └─────────┘  └─────────┘  └─────────┘               │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Environment Types

### RT Platform (Real-Time) - Target Architecture

The RT environments are hosted in **AWS** and represent the target architecture for voice routing services and latency-sensitive services.

| Region | AWS Region | Status |
|--------|------------|--------|
| US West | us-west-2 (Oregon) | ✅ Active |
| US East | us-east-1 (N. Virginia) | ✅ Active |
| London | eu-west-2 | ✅ Active |
| Frankfurt | eu-central-1 | ✅ Active |
| Singapore | ap-southeast-1 | ✅ Active |
| Sydney | ap-southeast-2 | ✅ Active |

**Key Characteristics:**
- Auto-scaling capabilities
- Modern CI/CD deployment pipelines
- Containerised services (ECS)
- 3 Availability Zones per region
- 99.99% uptime target

### SDC (Super Data Centre) - Legacy

Two on-premise data centres located in **London**, providing:

- Command and control functions for the entire global network
- Back-office functions
- Voice routing for Europe (being migrated to RT)
- Real-time data replication between SDC1 and SDC2

### GDC (Global Data Centre) - Legacy

Multiple on-premise data centres in global regions:

- Voice routing with reduced latency for regional calls
- Controlled via SDC command and control
- Being migrated to AWS RT

### Hybrid Cloud

AWS VPCs extending on-premise SDC/GDC capabilities:

- FreeSWITCH instances in AWS
- Transitory architecture for capacity management
- Will be deprecated as RT migration completes

---

## Technology Stack

### Delivery Platforms

| Platform | Usage |
|----------|-------|
| **CentOS/Linux** | OS for bare metal/VM services (decreasing) |
| **Docker/ECS** | Containerised services (increasing) |
| **AWS Lambda** | Serverless functions |
| **Salesforce** | App delivery via AppExchange |
| **iOS/Android** | Native mobile apps (React Native) |

### Core Technologies

| Category | Technologies |
|----------|--------------|
| **Voice Switching** | FreeSWITCH, OpenSIPS (Carrier Grade) |
| **Databases** | MariaDB/MySQL, DynamoDB, Redis, Elasticsearch |
| **Message Queue** | RabbitMQ, Amazon MQ |
| **Web Servers** | Apache, NGINX |
| **IaC** | Terraform, Salt Stack |

### Development Languages

| Language | Usage |
|----------|-------|
| **PHP** | Core platform (Kohana framework) |
| **TypeScript/Node.js** | Modern services |
| **Go** | High-performance services, Lambda |
| **C/C++** | FreeSWITCH modules, CDR processing |
| **Lua** | Routing policies, dialplan scripts |
| **Apex** | Salesforce packages |
| **Swift/Kotlin** | Native mobile apps |

### Third-Party Services

| Service | Provider(s) |
|---------|-------------|
| **Transcription** | AWS Transcribe, Deepgram, Voicebase |
| **Text-to-Speech** | AWS Polly, Google TTS |
| **AI/LLM** | AWS Bedrock, Google Vertex AI |
| **PCI Compliance** | PCIPal |

---

## AWS Infrastructure Layout

### Account Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Organization                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   Nexus     │  │  Platform   │  │    Build    │        │
│   │  (Global)   │  │   (Prod)    │  │   (CI/CD)   │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │  RT Prod    │  │  RT Stage   │  │   RT Dev    │        │
│   │  (Regions)  │  │  (Regions)  │  │  (Regions)  │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │  Security   │  │   Shared    │  │  Internal   │        │
│   │  (Tools)    │  │  Services   │  │  (NBX)      │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Regional VPC Layout (RT Region)

Each RT region contains:

```
┌─────────────────────────────────────────────────────────────┐
│                    RT Region VPC                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                  Public Subnets                       │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │  │
│   │  │  ALB    │  │   NAT   │  │ Global  │              │  │
│   │  │         │  │ Gateway │  │ Accel   │              │  │
│   │  └─────────┘  └─────────┘  └─────────┘              │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                 Private Subnets                       │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │  │
│   │  │   ECS   │  │   EC2   │  │ Lambda  │              │  │
│   │  │ Cluster │  │  (FSX)  │  │         │              │  │
│   │  └─────────┘  └─────────┘  └─────────┘              │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                 Data Subnets                          │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │  │
│   │  │   RDS   │  │  Redis  │  │ Elastic │              │  │
│   │  │ Aurora  │  │ Cluster │  │ search  │              │  │
│   │  └─────────┘  └─────────┘  └─────────┘              │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Service Categories

### 1. Voice Routing Services
- SIP Proxy (OpenSIPS)
- PBX (FreeSWITCH)
- CDR Processing
- Recording & Archiving

**See:** [Voice Routing Subsystem](./voice-routing/overview.md)

### 2. Platform Core Services
- Core API (platform-api)
- Service Gateway
- Workflow Engine
- Dialplan & Scripting

### 3. Omnichannel Services
- OmniService (SMS, Chat, Email)
- Chat Widget
- Message Templates

**See:** [Omnichannel Architecture](./omnichannel/overview.md)

### 4. Salesforce Integration
- AVS Package
- SCV Connector
- SF PBX Proxy

**See:** [Salesforce Integration](./salesforce-integration/overview.md)

### 5. AI/CAI Services
- Conversational AI Service
- AI Prompt Pipeline
- Knowledge Base Integration

**See:** [AI/CAI Architecture](./ai-cai/overview.md)

### 6. Observability (Lumina)
- Real-time metrics
- Call analytics
- System health monitoring

### 7. Authentication & Authorization
- NAPS (Permissions Service)
- Gatekeeper (JWT Authorizer)
- Auth Scopes

---

## Data Flow Overview

### Inbound Call Flow

```
                                    ┌──────────────┐
                                    │   Carrier    │
                                    │   (PSTN)     │
                                    └──────┬───────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         RT Region                                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │   SIP    │───►│   PBX    │───►│ fsxinetd │───►│ Core API │     │
│  │  Proxy   │    │ FreeSW   │    │  (Lua)   │    │          │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│       │               │                               │             │
│       │               │                               ▼             │
│       │               │                        ┌──────────┐        │
│       │               └───────────────────────►│   CDR    │        │
│       │                                        │  Munch   │        │
│       │                                        └──────────┘        │
│       │                                              │              │
│       │                                              ▼              │
│       │                                        ┌──────────┐        │
│       │                                        │ Archiving│        │
│       │                                        └──────────┘        │
└───────┼─────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────┐         ┌──────────────┐
│   Handset    │         │  Salesforce  │
│   WebRTC     │         │  (CTI/AVS)   │
└──────────────┘         └──────────────┘
```

### Data Replication

- **Real-time**: Database replication across SDC1/SDC2
- **Cross-region**: DynamoDB global tables for routing state
- **CDR/Recordings**: S3 replication with archiving policies

---

## Deployment & CI/CD

### Pipeline Overview

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Git    │───►│ GitHub  │───►│CodeBuild│───►│ Deploy  │───►│  Prod   │
│  Push   │    │ Actions │    │         │    │ Stage   │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### Deployment Methods

| Service Type | Method |
|--------------|--------|
| ECS Services | CodePipeline → ECS Blue/Green |
| Lambda | SAM/CloudFormation |
| EC2 (Salt) | Guardian + Salt Stack |
| Terraform | tf wrapper + CodeBuild |
| Salesforce | SFDX + GitHub Actions |

---

## Security Architecture

### Network Security
- VPC isolation per environment
- Security groups with least privilege
- WAF protection on public endpoints
- Private subnets for data tier

### Authentication
- Auth0 for identity management
- JWT tokens for API authentication
- Gatekeeper Lambda authorizers
- Salesforce OAuth for SF integration

### Data Security
- Encryption at rest (KMS)
- Encryption in transit (TLS 1.2+)
- PCI DSS compliance for payments
- GDPR-compliant data handling

---

## Diagrams Reference

These diagrams are maintained in Google Drive (draw.io):

| Diagram | Link |
|---------|------|
| Technology Stack Overview | [View](https://app.diagrams.net/#G1_IwiTdsl51VoPQpqlhzxkdZF7cGYcUeg) |
| Global Architecture Block Diagram | [View](https://app.diagrams.net/#G1DCanRWtvPIaOKtYly74I5piHdp_ylGbU) |
| Voice Subsystem Functional View | [View](https://app.diagrams.net/#G1RoRjZ47B-2tjcBAXY9K8AXY6zgyFmEz4) |
| Voice Subsystem Redundancy | [View](https://app.diagrams.net/#G18LwIQTTxmBBMz5RGpL3oaU30LTpAVDB_) |
| PBX Component View | [View](https://app.diagrams.net/#G1r_JvNV2sFQ7PBzUFp6Bco5sXWXYCRzOS) |
| fsxinetd Component View | [View](https://app.diagrams.net/#G1RoDSOuOpX-nB5EIPdlNJ1Kj1HtRh-W-a) |

---

## Related Documentation

- [Voice Routing Subsystem](./voice-routing/overview.md)
- [Repository Inventory](../services/repository-inventory.md)
- [Terraform Module Catalog](../terraform-modules/catalog.md)

---

*Migrated from Confluence Architecture Space (Space: A)*
