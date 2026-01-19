# fsxinetd Service

> **Last Updated:** 2026-01-19  
> **Source:** Confluence Architecture Space  
> **SMEs:** Neil Burgess, James Bravo, Greg Inglis  
> **Status:** ✅ Published

---

## Overview

fsxinetd is invoked by FreeSWITCH via the ESL (Event Socket Library) interface to extend call processing functionality. It operates the public Lua scripting engine heavily utilised by AVS Routing Policies.

**Key Point:** Pretty much most of the AVS Routing Policy components you see in the AVS UI use this service.

---

## Component View

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              fsxinetd Service                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         ESL Interface                                    │  │
│   │   Receives commands from FreeSWITCH via Event Socket Library            │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                       Lua Script Engine                                  │  │
│   │   • Executes routing policy scripts                                     │  │
│   │   • Handles AVS flow logic                                              │  │
│   │   • Customer-specific routing rules                                     │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                            │
│          ┌─────────────────────────┼─────────────────────────┐                 │
│          │                         │                         │                 │
│          ▼                         ▼                         ▼                 │
│   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐           │
│   │    Data     │          │    Call     │          │   Freedom   │           │
│   │ Connectors  │          │   Queues    │          │   Mobile    │           │
│   │             │          │             │          │    Push     │           │
│   └─────────────┘          └─────────────┘          └─────────────┘           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Functions

| Function | Description |
|----------|-------------|
| **Lua Script Engine** | Executes customer routing policies defined in AVS |
| **Data Connectors** | Queries Salesforce for call routing decisions |
| **Call Queues** | Manages queue membership, agent status, distribution |
| **Call Connectivity** | Handles complex call scenarios (transfer, conference) |
| **Freedom Mobile Push** | Sends push notifications to mobile app users |

---

## Service Inputs

| Input | Protocol | Description |
|-------|----------|-------------|
| FreeSWITCH | ESL | Invoked when a call requires Lua script execution, Data Connector access, or Freedom Mobile push notifications |

---

## Service Outputs & Integrations

| Target | Protocol | Description |
|--------|----------|-------------|
| **core-api-fast** | REST | Lookups for Lua scripts from dialplan policies; retrieves group data, data connector credentials |
| **service-gateway** | REST | Accesses Salesforce objects for legacy orgs using SOAP-based data connectors |
| **Salesforce** | REST | Direct REST API access for modern orgs requiring Salesforce object access |
| **FreeSWITCH** | ESL | On-demand connections to other FreeSWITCH instances in the network |

---

## Integration Flow

```
                         ┌──────────────────┐
                         │    FreeSWITCH    │
                         │  (Call in prog)  │
                         └────────┬─────────┘
                                  │ ESL
                                  ▼
                         ┌──────────────────┐
                         │     fsxinetd     │
                         └────────┬─────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│    core-api      │    │   Salesforce     │    │   Other FS       │
│   (REST API)     │    │  (REST/SOAP)     │    │   Instances      │
│                  │    │                  │    │    (ESL)         │
│ • Load scripts   │    │ • Query objects  │    │ • Listen-in      │
│ • Get config     │    │ • Update records │    │ • Transfer       │
│ • Group data     │    │ • Screen pop     │    │ • Conference     │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                        │
         │                        ▼
         │              ┌──────────────────┐
         └─────────────►│  service-gateway │
                        │  (Legacy SOAP)   │
                        └──────────────────┘
```

---

## Data Connector Paths

### Modern Orgs (Direct REST)
```
fsxinetd → Salesforce REST API → Salesforce Objects
```

### Legacy Orgs (Service Gateway)
```
fsxinetd → service-gateway → Salesforce SOAP API → Salesforce Objects
```

---

## Repositories

| Repository | Description |
|------------|-------------|
| `redmatter/platform-fsxinetdsocket` | Main fsxinetd service |
| `redmatter/platform-fsxinetdsocket-php8` | PHP 8 version |
| `redmatter/natterbox-avsapp-scripts` | AVS Lua scripts |
| `redmatter/libraries-fscallmanagement` | Call management PHP classes |

---

## Configuration

fsxinetd is configured via:
- Environment variables
- Salt pillar data
- Core API configuration endpoints

Key configuration items:
- ESL connection settings
- Salesforce API credentials (via data connectors)
- Core API endpoints
- Logging levels

---

## Monitoring

### Key Metrics
- Script execution time
- Data connector query latency
- Queue operations per second
- ESL connection health

### Alerts
- Script execution failures
- Data connector timeouts
- High latency warnings
- Connection pool exhaustion

---

## Runbooks

*Links to operational runbooks:*
- TBD: fsxinetd service restart
- TBD: Data connector troubleshooting
- TBD: Lua script debugging

---

## Support

| Level | Team |
|-------|------|
| First Line | Platform Support |
| Second Line | Platform Engineering |
| Third Line | Core Platform Team (SMEs) |

### Third-Party Dependencies
- Salesforce (for data connector operations)

---

## Related Documentation

- [Voice Routing Overview](./overview.md)
- [PBX Component View](./pbx.md)
- [Core API Documentation](../core-api.md)

---

*Migrated from Confluence Architecture Space - fsxinetd Service Overview*
