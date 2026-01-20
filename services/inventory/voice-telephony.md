# Voice and Telephony Repository Inventory

## Overview

This document provides a comprehensive inventory of all repositories related to voice and telephony services in the Red Matter/Natterbox platform. The voice infrastructure is built around FreeSWITCH as the core media server, OpenSIPS as the SIP proxy, and various supporting services for routing, monitoring, and media processing.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              VOICE PLATFORM ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐     │
│   │   PSTN/Carriers │        │   SIP Clients   │        │   WebRTC/WebRTC │     │
│   │   (MNO/Trunks)  │        │   (Devices)     │        │   Clients       │     │
│   └────────┬────────┘        └────────┬────────┘        └────────┬────────┘     │
│            │                          │                          │              │
│            └──────────────────────────┼──────────────────────────┘              │
│                                       │                                          │
│                                       ▼                                          │
│                       ┌───────────────────────────────┐                          │
│                       │         OpenSIPS              │                          │
│                       │    (SIP Proxy/Router)         │                          │
│                       │   platform-opensips           │                          │
│                       └───────────────┬───────────────┘                          │
│                                       │                                          │
│            ┌──────────────────────────┼──────────────────────────┐              │
│            │                          │                          │              │
│            ▼                          ▼                          ▼              │
│   ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐     │
│   │   FreeSWITCH    │        │   FreeSWITCH    │        │   FreeSWITCH    │     │
│   │   (PBX Node 1)  │        │   (PBX Node 2)  │        │   (PBX Node N)  │     │
│   │  platform-      │        │  platform-      │        │  platform-      │     │
│   │  freeswitch     │        │  freeswitch     │        │  freeswitch     │     │
│   └────────┬────────┘        └────────┬────────┘        └────────┬────────┘     │
│            │                          │                          │              │
│            └──────────────────────────┼──────────────────────────┘              │
│                                       │                                          │
│            ┌──────────────────────────┼──────────────────────────┐              │
│            │                          │                          │              │
│            ▼                          ▼                          ▼              │
│   ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐     │
│   │  fsxinetdsocket │        │   TTS Gateway   │        │  Dialplan/LCR   │     │
│   │  (Event Socket) │        │ platform-tts-   │        │  platform-      │     │
│   │                 │        │    gateway      │        │  dialplanscripts│     │
│   └─────────────────┘        └─────────────────┘        └─────────────────┘     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Voice Platform Repositories

### 1. platform-freeswitch

**Repository:** `redmatter/platform-freeswitch`

**Purpose:** Custom FreeSWITCH build package with Red Matter-specific patches and modules. This is the core media server handling all call processing, audio streaming, and telephony applications.

**Key Technologies:**
- FreeSWITCH 1.2.0 (patched)
- C/C++
- Lua (scripting)
- SpiderMonkey (JavaScript)
- MRCP (Media Resource Control Protocol)
- SIP/RTP/RTCP

**Primary Language:** C (with Lua/JavaScript scripting)

**Key Red Matter Modules:**
- `mod_rmapi` - Red Matter custom API module
- `mod_rmvoicemail` - Custom voicemail module
- `mod_rmlogactivity` - Activity logging module
- `mod_rmremoterec` - Remote recording module
- `mod_opencore_amr` - AMR codec support

**Patches Applied:**
| Patch | Purpose |
|-------|---------|
| `mod_lcr.patch` | Least Cost Routing enhancements |
| `mod_xml_curl.patch` | XML CURL configuration |
| `mod_unimrcp.patch` | MRCP integration fixes |
| `mod_sofia_*.patch` | SIP stack customizations |
| `esl_*.patch` | Event Socket Library fixes |
| `rtcp.patch` | RTCP improvements |
| `media_bug.patch` | Media bug fixes |

**Configuration Files:**
- `/etc/freeswitch/` - Main configuration directory
- `/etc/freeswitch/autoload_configs/` - Module autoload configurations
- `/etc/freeswitch/dialplan/` - Dialplan definitions
- `/etc/freeswitch/sip_profiles/` - SIP profile configurations

**Deployment:**
- **AWS Regions:** All production regions (EU-West-1, US-East-1)
- **Services:** EC2 instances, ECS containers
- **Package:** RPM (`freeswitch-*.rpm`)

**Dependencies:**
- openssl-devel
- unixODBC-devel
- opencore-amr-devel
- libedit-devel
- curl-devel >= 7.21.2

**Status:** ✅ Active - Core production component

---

### 2. platform-opensips

**Repository:** `redmatter/platform-opensips`

**Purpose:** OpenSIPS SIP proxy with custom Red Matter module for SIP routing, registration handling, and load balancing across FreeSWITCH instances.

**Key Technologies:**
- OpenSIPS 1.7.0-tls (patched)
- C
- SIP/UDP/TCP/TLS/SCTP
- ISUP/SIP-I

**Primary Language:** C

**Red Matter Module Functions:**
- `redmatter_register()` - Handle REGISTER requests
- `redmatter_subscribe()` - Handle SUBSCRIBE requests
- `redmatter_handle_refer()` - Handle inbound REFER requests
- `redmatter_dstcheck()` - Destination check and header manipulation
- `redmatter_is_sender_us()` - Check if message from our PBX
- `redmatter_is_ip_us()` - Check if IP belongs to a PBX
- `redmatter_check_shutdown()` - Graceful shutdown check

**Configuration Parameters:**
```c
# IP where OpenSIPS is running. Mandatory
modparam("redmatter", "fs_path", "172.30.98.22")

# API URL. Optional, default value shown below
modparam("redmatter", "api_local_url", "http://api-local.redmatter.com/opensips")

# API request timeout. Optional, defaults to no timeout
modparam("redmatter", "api_timeout", 5)
```

**API Calls:**
- `opensips/dstcheck` - Amend SIP headers (R-URI, destination URI, To) based on routing rules

**SIP-I Support:**
- RFC 3204 compliant
- ITU Q.1912.5, Q.763 integration
- ISUP content handling for trombone calls

**Load Balancer Features:**
- Traffic routing based on load
- Session affinity for device calls (OpenTrade turrets, Cisco CUCM)
- Per-datacenter health status

**Carrier Prefixes:**
| Customer | Prefix | Type |
|----------|--------|------|
| EE | 541020 | MT (Mobile Terminating) |
| EE | 541021 | MO (Mobile Originating) |
| Netcom | 19500 | MO |
| Netcom | 19502 | MT |

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances
- **Ports:** 5060 (UDP/TCP), 5061 (TLS), 5080, 5050

**Dependencies:**
- platform-freeswitch
- Core API

**Status:** ✅ Active - Core production component

---

### 3. platform-fsxinetdsocket

**Repository:** `redmatter/platform-fsxinetdsocket`

**Purpose:** FreeSWITCH Event Socket Interface daemon. Provides inetd-style socket connection handling for FreeSWITCH Event Socket Library (ESL) connections.

**Key Technologies:**
- C
- Event Socket Library (ESL)
- TCP sockets
- inetd-style connection handling

**Primary Language:** C

**Features:**
- Persistent ESL connections
- Connection pooling
- Event filtering and routing
- Heartbeat monitoring

**Configuration:**
- Connection timeout settings
- Reconnection logic
- Event subscriptions

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** Runs alongside FreeSWITCH instances
- **Port:** Configurable (default: local socket)

**Dependencies:**
- platform-freeswitch
- libesl

**Status:** ✅ Active - Core production component

---

### 4. platform-tts-gateway

**Repository:** `redmatter/platform-tts-gateway`

**Purpose:** Text-to-Speech gateway service providing MRCP (Media Resource Control Protocol) server interface for TTS synthesis. Interfaces with multiple TTS providers including Amazon Polly and Ivona.

**Key Technologies:**
- C
- MRCP v2
- HTTP/HTTPS
- AWS SDK (Polly integration)
- SIP/RTP
- MP3 decoding
- G.711, G.722 codec support

**Primary Language:** C

**Source Files:**
| File | Purpose |
|------|---------|
| `src/app.c` | Main application entry point |
| `src/mrcpsercom.c` | MRCP server implementation (41KB) |
| `src/httpser.c` | HTTP server for management |
| `src/ivonacli.c` | Ivona TTS client |
| `src/ttscli.c` | Generic TTS client interface |
| `src/db.c` | Database operations |
| `src/oaudio.c` | Audio processing (40KB) |

**MRCP Functions:**
- `SPEAK` - Text-to-speech synthesis
- `STOP` - Stop current synthesis
- `PAUSE` - Pause synthesis
- `RESUME` - Resume synthesis

**Audio Codecs Supported:**
- G.711 (µ-law, A-law)
- G.722
- MP3 (decode only)

**Configuration:**
```xml
<!-- /conf/tts-gateway.xml - 35KB configuration file -->
<tts-gateway>
  <mrcp-server port="5060"/>
  <http-server port="8080"/>
  <providers>
    <provider name="polly" type="aws"/>
    <provider name="ivona" type="ivona"/>
  </providers>
</tts-gateway>
```

**Docker Support:**
- `Dockerfile` included
- `docker-compose.yml` for local development
- `entrypoint.sh` for container initialization

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** ECS containers, EC2
- **Ports:** 5060 (MRCP), 8080 (HTTP management)

**Dependencies:**
- AWS SDK (for Polly)
- libcurl
- libssl

**Status:** ✅ Active - Core production component

---

### 5. platform-dialplanscripts

**Repository:** `redmatter/platform-dialplanscripts`

**Purpose:** Lua-based dialplan scripts for FreeSWITCH call routing and processing.

**Key Technologies:**
- Lua
- FreeSWITCH mod_lua
- XML dialplans

**Primary Language:** Lua

**Script Categories:**
- Inbound call routing
- Outbound call routing
- IVR flows
- Feature codes (star codes)
- Call recording logic
- Conference handling

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** Deployed with FreeSWITCH
- **Location:** `/usr/share/freeswitch/scripts/`

**Dependencies:**
- platform-freeswitch
- platform-dialplan (XML configurations)

**Status:** ✅ Active - Core production component

---

## Monitoring and Management Repositories

### 6. platform-fseventmonitor

**Repository:** `redmatter/platform-fseventmonitor`

**Purpose:** FreeSWITCH event monitoring service that subscribes to ESL events and processes them for monitoring, alerting, and metrics collection.

**Key Technologies:**
- PHP/C
- Event Socket Library
- Redis (for state management)

**Primary Language:** PHP

**Monitored Events:**
- Channel create/destroy
- Call state changes
- Conference events
- Registration events
- Error conditions

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances

**Dependencies:**
- platform-freeswitch
- platform-fsxinetdsocket
- Redis

**Status:** ✅ Active

---

### 7. platform-fscallcentermonitor

**Repository:** `redmatter/platform-fscallcentermonitor`

**Purpose:** Call center specific monitoring for mod_callcenter queues, agent states, and queue statistics.

**Key Technologies:**
- PHP
- Event Socket Library
- mod_callcenter events

**Primary Language:** PHP

**Monitored Metrics:**
- Queue lengths
- Agent availability
- Wait times
- Abandon rates
- Service level metrics

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances

**Dependencies:**
- platform-freeswitch (mod_callcenter)
- platform-fsxinetdsocket

**Status:** ✅ Active

---

### 8. platform-sipgwping

**Repository:** `redmatter/platform-sipgwping`

**Purpose:** SIP Gateway OPTIONS pinger (rmsipgwping) - Replacement for transaping service. Monitors SIP gateway health via OPTIONS pings.

**Key Technologies:**
- C/PHP
- SIP OPTIONS
- Async I/O

**Primary Language:** C

**Key Features:**
- Internally asynchronous and event-driven
- Proxies all SIP OPTIONS pings via OpenSIPS
- Runs on all DCs (GDCs and NDCs)
- DC-specific health status for LCR gateways
- Queries/updates via CoreAPI

**Database Tables:**
- `LCR.CarrierGateway` - LCR gateway configurations
- `LCR.CarrierGatewayHealth` - Per-DC health status
- `Numbers.Gateway` - Number gateway configurations

**Configuration Fields:**
| Field | Values | Purpose |
|-------|--------|---------|
| PingGateway | YES/NO/TEST | Enable/disable pinging |
| PingAlert | SILENT/WARNING/CRITICAL | Alert level |
| PingMaxFwd | NULL/integer | Max-Forwards header value |
| PingUser | NULL/string | User part of From URI |
| PingAcceptErrors | NULL/comma-separated codes | Additional accepted response codes |

**Timeout Behavior:**
- Unresponsive gateways: 30-50 second retry sequence
- LastUpdate field updated after timeout sequence

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** Runs on RMS boxes in all DCs
- **Port:** 5060 (via OpenSIPS proxy)

**Dependencies:**
- platform-opensips
- Core API
- LCR database

**Status:** ✅ Active

---

### 9. platform-fseventfilemonitor

**Repository:** `redmatter/platform-fseventfilemonitor`

**Purpose:** File-based event monitoring for FreeSWITCH, monitoring log files and CDR files for processing.

**Key Technologies:**
- PHP
- inotify (file watching)
- Log parsing

**Primary Language:** PHP

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances

**Dependencies:**
- platform-freeswitch

**Status:** ✅ Active

---

## CDR and Recording Repositories

### 10. platform-cdrmunch

**Repository:** `redmatter/platform-cdrmunch`

**Purpose:** CDR (Call Detail Record) processing service. Munches CDR files generated by FreeSWITCH and processes them for billing, analytics, and storage.

**Key Technologies:**
- PHP
- XML parsing
- Database operations

**Primary Language:** PHP

**Features:**
- CDR file parsing
- Data normalization
- Database insertion
- S3 archival
- Error handling and retry

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances, Lambda

**Dependencies:**
- platform-freeswitch (CDR files)
- Core API
- S3

**Status:** ✅ Active

---

### 11. platform-transcribed

**Repository:** `redmatter/platform-transcribed`

**Purpose:** Transcription daemon for processing call recordings and generating transcripts using ASR (Automatic Speech Recognition) services.

**Key Technologies:**
- PHP/Python
- AWS Transcribe
- Audio processing
- S3 integration

**Primary Language:** PHP

**Features:**
- Automatic transcription of recordings
- Multiple language support
- Confidence scoring
- Searchable transcript storage

**Deployment:**
- **AWS Regions:** US-East-1, EU-West-1
- **Services:** ECS containers

**Dependencies:**
- AWS Transcribe
- S3 (recording storage)
- Core API

**Status:** ✅ Active

---

### 12. platform-archiving

**Repository:** `redmatter/platform-archiving`

**Purpose:** Recording archival service for long-term storage and compliance retention of call recordings.

**Key Technologies:**
- PHP
- S3 lifecycle policies
- Glacier integration

**Primary Language:** PHP

**Features:**
- Configurable retention policies
- Compliance archival
- Glacier cold storage
- Retrieval workflows

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances, Lambda

**Dependencies:**
- S3
- Glacier
- Core API

**Status:** ✅ Active

---

## Supporting Libraries

### 13. libraries-fscallmanagement-php8

**Repository:** `redmatter/libraries-fscallmanagement-php8`

**Purpose:** PHP 8 library for FreeSWITCH call management operations. Provides high-level abstractions for ESL operations and call control.

**Key Technologies:**
- PHP 8
- Event Socket Library
- Object-oriented design

**Primary Language:** PHP

**Key Classes:**
- Call management
- Channel operations
- Conference control
- User presence
- Registration management

**API Methods:**
```php
// Example usage
$call = new FSCall($eslConnection);
$call->originate($destination, $callerIdNum, $callerIdName);
$call->bridge($otherLeg);
$call->record($filepath);
$call->hangup();
```

**Dependencies:**
- platform-freeswitch
- php-esl extension

**Status:** ✅ Active

---

### 14. platform-fscore

**Repository:** `redmatter/platform-fscore`

**Purpose:** Core FreeSWITCH utilities and shared libraries used across multiple voice services.

**Key Technologies:**
- C
- PHP
- Shared libraries

**Primary Language:** C/PHP

**Features:**
- Common ESL utilities
- Configuration helpers
- Logging utilities

**Dependencies:**
- platform-freeswitch

**Status:** ✅ Active

---

## WebRTC and Browser-Based Telephony

### 15. platform-webphoned

**Repository:** `redmatter/platform-webphoned`

**Purpose:** WebRTC-based softphone daemon providing browser-to-SIP gateway functionality.

**Key Technologies:**
- WebRTC
- SIP.js / SRTP
- WebSocket signaling
- TURN/STUN integration
- PHP/JavaScript

**Primary Language:** PHP/JavaScript

**Features:**
- Browser-based calling
- WebSocket to SIP translation
- Media transcoding
- SRTP encryption
- ICE/STUN/TURN handling

**WebRTC to SIP Flow:**
```
Browser WebRTC <--WebSocket--> webphoned <--SIP--> OpenSIPS <--SIP--> FreeSWITCH
```

**Deployment:**
- **AWS Regions:** All production regions
- **Services:** EC2 instances with WebSocket support
- **Ports:** 443 (WSS), internal SIP ports

**Dependencies:**
- platform-opensips
- TURN/STUN servers
- SSL certificates

**Status:** ✅ Active

---

## Additional Voice Repositories

### 16. platform-workflow-engine

**Repository:** `redmatter/platform-workflow-engine`

**Purpose:** Call flow workflow engine for visual IVR builder and advanced call routing logic.

**Key Technologies:**
- PHP
- JSON workflow definitions
- State machine

**Primary Language:** PHP

**Status:** ✅ Active

---

### 17. natterbox-avsapp-scripts

**Repository:** `redmatter/natterbox-avsapp-scripts`

**Purpose:** Application Voice Services (AVS) scripts for custom application integrations.

**Key Technologies:**
- Lua
- PHP
- FreeSWITCH scripting

**Primary Language:** Lua/PHP

**Status:** ✅ Active

---

## External Integrations

### Carrier/PSTN Integrations

| Integration | Protocol | Configuration |
|-------------|----------|---------------|
| EE | SIP/SIP-I | Prefix: 541020/541021 |
| Netcom | SIP/SCTP | Prefix: 19500/19502 |
| Twilio | SIP | SIP Trunk profiles |
| Generic SIP Trunks | SIP | LCR gateway configuration |

### MRCP/ASR/TTS Providers

| Provider | Type | Integration |
|----------|------|-------------|
| Amazon Polly | TTS | Via platform-tts-gateway |
| Amazon Transcribe | ASR | Via platform-transcribed |
| Ivona | TTS | Via platform-tts-gateway (legacy) |
| UniMRCP | MRCP | mod_unimrcp |

### Recording Storage

| Storage | Purpose | Integration |
|---------|---------|-------------|
| S3 | Primary recording storage | Direct from FreeSWITCH |
| Glacier | Long-term archival | Via platform-archiving |
| EFS | Temporary recording buffer | FreeSWITCH local |

---

## Configuration Requirements

### FreeSWITCH Essential Configuration

```xml
<!-- /etc/freeswitch/autoload_configs/modules.conf.xml -->
<configuration name="modules.conf" description="Modules">
  <modules>
    <load module="mod_console"/>
    <load module="mod_sofia"/>
    <load module="mod_commands"/>
    <load module="mod_dptools"/>
    <load module="mod_dialplan_xml"/>
    <load module="mod_lua"/>
    <load module="mod_spidermonkey"/>
    <load module="mod_event_socket"/>
    <load module="mod_local_stream"/>
    <load module="mod_native_file"/>
    <load module="mod_sndfile"/>
    <load module="mod_tone_stream"/>
    <load module="mod_shout"/>
    <load module="mod_say_en"/>
    <load module="mod_xml_curl"/>
    <load module="mod_xml_cdr"/>
    <load module="mod_lcr"/>
    <load module="mod_conference"/>
    <load module="mod_db"/>
    <load module="mod_hash"/>
    <load module="mod_fifo"/>
    <load module="mod_valet_parking"/>
    <load module="mod_unimrcp"/>
    <load module="mod_soundtouch"/>
    <load module="mod_spandsp"/>
    <load module="mod_distributor"/>
    <!-- Red Matter modules -->
    <load module="mod_rmapi"/>
    <load module="mod_rmvoicemail"/>
    <load module="mod_rmlogactivity"/>
    <load module="mod_rmremoterec"/>
  </modules>
</configuration>
```

### OpenSIPS Essential Configuration

```
# /etc/opensips/opensips.cfg (key sections)
loadmodule "redmatter.so"

modparam("redmatter", "fs_path", "172.30.98.22")
modparam("redmatter", "api_local_url", "http://api-local.redmatter.com/opensips")
modparam("redmatter", "api_timeout", 5)

route {
    if (is_method("REGISTER")) {
        redmatter_register("");
        switch($retcode) {
            case -18:
                sl_send_reply("401", "Unauthorized");
                break;
            case -4:
                www_challenge("", "1");
                break;
            case 1:
                save("location", "c1f");
                break;
            default:
                sl_send_reply("500", "Server Internal Error");
        }
    }
    
    if (is_method("INVITE")) {
        redmatter_dstcheck();
        # ... routing logic
    }
}
```

### Environment Variables

```bash
# Common environment variables for voice services
FS_ESL_HOST=localhost
FS_ESL_PORT=8021
FS_ESL_PASSWORD=ClueCon
OPENSIPS_HOST=sip-local.redmatter.com
OPENSIPS_PORT=5060
TTS_GATEWAY_HOST=tts-gateway.redmatter.com
TTS_GATEWAY_PORT=5060
REDIS_HOST=redis.redmatter.com
REDIS_PORT=6379
DB_HOST=db.redmatter.com
```

---

## Deployment Summary

### AWS Services Used

| Service | Purpose |
|---------|---------|
| EC2 | FreeSWITCH PBX nodes, OpenSIPS proxies |
| ECS | TTS Gateway, monitoring services |
| S3 | Recording storage, CDR archival |
| Glacier | Long-term recording retention |
| EFS | Shared storage for recordings |
| Route53 | SIP DNS routing |
| ALB | WebSocket load balancing |
| CloudWatch | Metrics and alerting |

### Region Deployment

| Region | Services |
|--------|----------|
| EU-West-1 (Ireland) | Full voice stack |
| US-East-1 (N. Virginia) | Full voice stack |
| EU-West-2 (London) | Secondary/DR |

---

## Repository Status Summary

| Repository | Status | Criticality | Last Updated |
|------------|--------|-------------|--------------|
| platform-freeswitch | ✅ Active | Critical | Ongoing |
| platform-opensips | ✅ Active | Critical | Ongoing |
| platform-fsxinetdsocket | ✅ Active | Critical | Ongoing |
| platform-tts-gateway | ✅ Active | High | Ongoing |
| platform-dialplanscripts | ✅ Active | High | Ongoing |
| platform-fseventmonitor | ✅ Active | Medium | Ongoing |
| platform-fscallcentermonitor | ✅ Active | Medium | Ongoing |
| platform-sipgwping | ✅ Active | Medium | Ongoing |
| platform-fseventfilemonitor | ✅ Active | Medium | Ongoing |
| platform-cdrmunch | ✅ Active | High | Ongoing |
| platform-transcribed | ✅ Active | Medium | Ongoing |
| platform-archiving | ✅ Active | Medium | Ongoing |
| libraries-fscallmanagement-php8 | ✅ Active | High | Ongoing |
| platform-fscore | ✅ Active | High | Ongoing |
| platform-webphoned | ✅ Active | High | Ongoing |
| platform-workflow-engine | ✅ Active | Medium | Ongoing |
| natterbox-avsapp-scripts | ✅ Active | Medium | Ongoing |

---

## Related Documentation

- [OpenSIPS Module Documentation](../opensips/redmatter-module.md)
- [FreeSWITCH Configuration Guide](../freeswitch/configuration.md)
- [TTS Gateway API Reference](../tts-gateway/api-reference.md)
- [Call Flow Architecture](../architecture/call-flows.md)
- [Recording Infrastructure](../recordings/infrastructure.md)

---

*Last Updated: 2026-01-20*
*Document Owner: Platform Engineering Team*
