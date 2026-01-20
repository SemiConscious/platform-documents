# Voice Routing Subsystem

> **Last Updated:** 2026-01-19  
> **Source:** Confluence Architecture Space  
> **Status:** ✅ Complete

---

## Overview

Voice routing is central to the operation of the Natterbox platform. This subsystem handles all aspects of voice call routing, including inbound/outbound calls, SIP registration, call queues, recording, and transcription.

The architecture is standardised across all environment types (SDC, GDC, Hybrid, RT), though the underlying networking and container management may differ.

---

## Functional Component View

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        VOICE ROUTING SUBSYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   EXTERNAL                                                                       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                        │
│   │   Carrier   │    │  SIP Phone  │    │   WebRTC    │                        │
│   │   (PSTN)    │    │  (Handset)  │    │  (Browser)  │                        │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                        │
│          │                  │                  │                                │
│          └──────────────────┼──────────────────┘                                │
│                             │                                                    │
│                             ▼                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        SIP PROXY (OpenSIPS)                              │  │
│   │  • SIP Registration & Authentication                                     │  │
│   │  • Load balancing to PBX servers                                         │  │
│   │  • NAT traversal (floating IP)                                           │  │
│   │  • Cross-region routing                                                  │  │
│   └───────────────────────────────┬─────────────────────────────────────────┘  │
│                                   │                                             │
│                                   ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         PBX (FreeSWITCH)                                 │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │  Dialplan   │  │   Media     │  │  Recording  │  │    TTS      │    │  │
│   │  │  (XML/Lua)  │  │  Handling   │  │             │  │  Gateway    │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └───────────────────────────────┬─────────────────────────────────────────┘  │
│                                   │                                             │
│                                   ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         fsxinetd Service                                 │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │ Lua Script  │  │    Data     │  │    Call     │  │   Mobile    │    │  │
│   │  │   Engine    │  │ Connectors  │  │   Queues    │  │Push Notif.  │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └───────────────────────────────┬─────────────────────────────────────────┘  │
│                                   │                                             │
│                                   ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                       Supporting Services                                │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │  Core API   │  │   Service   │  │    CDR      │  │  Archiving  │    │  │
│   │  │             │  │   Gateway   │  │   Munch     │  │             │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. SIP Proxy (OpenSIPS)

**Repository:** `redmatter/platform-opensips`

The SIP Proxy is the entry point for all SIP traffic. It handles:

| Function | Description |
|----------|-------------|
| SIP Registration | Authenticates and registers SIP devices |
| Load Balancing | Distributes calls across PBX servers based on current load |
| NAT Traversal | Maintains floating IP for outbound calls to registered devices |
| Cross-Region Routing | Routes calls to specific PBX in any region |
| Failover | Automatic failover via floating IP cluster |

**Key Characteristics:**
- Deployed as HA pair with floating IP
- Shares state between cluster members
- Seamless call handover on failure

### 2. PBX (FreeSWITCH)

**Repositories:**
- `redmatter/platform-freeswitch` - Core FreeSWITCH with RM modules
- `redmatter/platform-dialplan` - XML dialplan configuration
- `redmatter/platform-dialplanscripts` - JavaScript dialplan scripts
- `redmatter/platform-fscore` - JS, PHP, Lua scripts and XML config

The PBX handles all call processing:

| Function | Description |
|----------|-------------|
| Dialplan Execution | Processes calls according to routing policies |
| Media Handling | RTP media, transcoding, conferencing |
| Recording | Call recording with various storage options |
| TTS Integration | Text-to-speech via tts-gateway |
| Event Generation | Produces events for CDR, analytics, CTI |

**Deployment:**
- Multiple PBX instances per region
- EC2 instances (not containerised due to real-time requirements)
- Auto-scaling based on call volume

### 3. fsxinetd Service

**Repositories:**
- `redmatter/platform-fsxinetdsocket` - Main service
- `redmatter/platform-fsxinetdsocket-php8` - PHP 8 version

fsxinetd extends FreeSWITCH call processing via the ESL (Event Socket Library) interface.

**Key Responsibilities:**

| Function | Description |
|----------|-------------|
| Lua Script Engine | Executes routing policy scripts |
| Data Connectors | Accesses Salesforce data during call routing |
| Call Queues | Manages queue membership and distribution |
| Freedom Mobile | Push notifications to mobile app |

**Integrations:**

```
┌─────────────┐         ┌─────────────┐
│  FreeSWITCH │◄──ESL──►│  fsxinetd   │
└─────────────┘         └──────┬──────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Core API   │       │  Salesforce │       │   Service   │
│  (REST)     │       │  (REST/SOAP)│       │   Gateway   │
└─────────────┘       └─────────────┘       └─────────────┘
```

### 4. TTS Gateway

**Repository:** `redmatter/platform-tts-gateway`

Provides text-to-speech capabilities:
- Replaced legacy Java-based Ivona server
- Integrates with AWS Polly and Google TTS
- Caches generated audio for performance

### 5. CDR Processing

**Repositories:**
- `redmatter/platform-cdrmunch` - CDR processing
- `redmatter/platform-cdr2sgapi` - CDR to Service Gateway API
- `redmatter/go-cdr-import` - CDR import utility

Processes Call Detail Records for:
- Billing
- Analytics
- Compliance
- Reporting

### 6. Archiving

**Repositories:**
- `redmatter/platform-archiving` - Policy-based archiving
- `redmatter/archiving-purge` - Purge and monitoring

Handles long-term storage of:
- CDR data
- Recordings
- PCAP captures
- SMS/MMS

---

## Redundancy Architecture

### Regional Redundancy

Each region deploys components for high availability:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REGION                                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌───────────────────────────────────────────────────────────────────────┐    │
│   │                        SIP CLUSTER                                     │    │
│   │                                                                        │    │
│   │   ┌─────────┐           ┌─────────┐                                   │    │
│   │   │  SIP 1  │◄─────────►│  SIP 2  │                                   │    │
│   │   │         │   State   │         │                                   │    │
│   │   └────┬────┘   Sync    └────┬────┘                                   │    │
│   │        │                     │                                        │    │
│   │        └──────────┬──────────┘                                        │    │
│   │                   │                                                   │    │
│   │            ┌──────┴──────┐                                            │    │
│   │            │ Floating IP │  ◄── Always assigned to one SIP server    │    │
│   │            └─────────────┘                                            │    │
│   └───────────────────────────────────────────────────────────────────────┘    │
│                           │                                                     │
│                           ▼                                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐    │
│   │                       PBX POOL                                         │    │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │    │
│   │   │  PBX 1  │  │  PBX 2  │  │  PBX 3  │  │  PBX n  │                 │    │
│   │   └─────────┘  └─────────┘  └─────────┘  └─────────┘                 │    │
│   │        Load balanced by SIP proxy based on session count              │    │
│   └───────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Floating IP Importance

The floating IP is critical for outbound calling to SIP devices behind NAT:

1. Device registers with SIP proxy using floating IP
2. Floating IP is always assigned to exactly one SIP server
3. On failover, alternate server takes over floating IP
4. Outbound calls always originate from same IP the device registered against
5. Ensures calls can traverse customer firewalls/routers

### Cross-Region Routing

The global network supports routing from any SIP server to any PBX:

```
┌──────────────────┐         ┌──────────────────┐
│    Region A      │         │    Region B      │
│  ┌──────────┐   │         │   ┌──────────┐   │
│  │   SIP    │───┼─────────┼──►│   PBX    │   │
│  └──────────┘   │         │   └──────────┘   │
│  ┌──────────┐   │         │   ┌──────────┐   │
│  │   PBX    │◄──┼─────────┼───│   SIP    │   │
│  └──────────┘   │         │   └──────────┘   │
└──────────────────┘         └──────────────────┘
```

**Use Cases:**
- Listen-in service (must route to specific PBX hosting the call)
- Regional failover
- Follow-the-sun routing
- User registration in different region than call origin

---

## Call Flow Examples

### Inbound Call (Carrier to User)

```
1. Carrier → SIP Proxy (receive INVITE)
2. SIP Proxy → Core API (lookup routing)
3. Core API → SIP Proxy (return PBX target)
4. SIP Proxy → PBX (forward INVITE)
5. PBX → fsxinetd (execute routing policy)
6. fsxinetd → Salesforce (data lookup if needed)
7. PBX → Target device (ring user)
8. PBX → CDR Munch (generate CDR on completion)
```

### Outbound Call (User to PSTN)

```
1. Device → SIP Proxy (send INVITE)
2. SIP Proxy → PBX (route to available PBX)
3. PBX → fsxinetd (execute outbound policy)
4. fsxinetd → Core API (validate, get carrier)
5. PBX → Carrier (place call)
6. PBX → CDR Munch (generate CDR on completion)
```

---

## Key Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| `platform-freeswitch` | FreeSWITCH with RM modules | C |
| `platform-opensips` | OpenSIPS 3.3.4 with custom module | C |
| `platform-dialplan` | Dialplan XML configuration | XML |
| `platform-dialplanscripts` | Dialplan JS scripts | JavaScript |
| `platform-fscore` | FS scripts and config | Lua/PHP/JS |
| `platform-fsxinetdsocket` | ESL task offloading | PHP |
| `natterbox-avsapp-scripts` | AVS Lua scripts | Lua |
| `platform-tts-gateway` | TTS gateway | C |
| `platform-cdrmunch` | CDR processing | C++ |
| `platform-archiving` | Recording archiving | C++ |

---

## Terraform Modules

| Module | Description |
|--------|-------------|
| `aws-terraform-rt-sip` | RT SIP proxy infrastructure |
| `aws-terraform-rt-pbx` | RT PBX infrastructure |
| `aws-terraform-fsx` | FreeSWITCH infrastructure |
| `aws-terraform-fsx8` | FreeSWITCH PHP 8 version |
| `aws-terraform-rt-tts` | RT TTS gateway |
| `aws-terraform-rt-transcribed` | RT transcription service |

---

## Monitoring & Observability

### Key Metrics
- Call volume (inbound/outbound)
- Call success rate
- Average call duration
- SIP registration count
- PBX session count
- Queue wait times
- Recording success rate

### Alerting
- SIP proxy failover
- PBX capacity thresholds
- Failed calls spike
- Recording failures
- Transcription delays

---

## Related Documentation

- [Global Architecture](../global-architecture.md)
- [fsxinetd Service Details](./fsxinetd.md)
- [TTS Gateway Service](./tts-gateway.md)
- [PBX Component View](./pbx.md)
- [CDR Processing](./cdr-processing.md)

---

*Migrated from Confluence Architecture Space - Voice Routing Subsystem*
