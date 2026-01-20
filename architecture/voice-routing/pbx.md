# PBX Component Architecture

> **Last Updated**: 2025-01-20
> **Status**: Complete
> **Owner**: Platform Team

## Overview

The Natterbox PBX layer consists of two primary components that work together to handle voice communications:

1. **OpenSIPS** - Open-source SIP proxy that routes SIP signaling
2. **FreeSWITCH** - Open-source PBX that processes calls and executes routing policies

Together, these components form the core of the voice routing infrastructure, handling all inbound and outbound calls for carriers, SIP trunks, MNOs, and endpoint devices (webphones, softphones, Yealink phones).

## Architecture Diagram

```
                                    ┌─────────────────────────────────────────┐
                                    │           External Sources              │
                                    │  (Carriers, SIP Trunks, MNOs, Devices)  │
                                    └───────────────────┬─────────────────────┘
                                                        │
                                                        ▼
                              ┌──────────────────────────────────────────────────┐
                              │                   OpenSIPS                        │
                              │               (SIP Proxy Layer)                   │
                              │                                                   │
                              │  • Device registration                            │
                              │  • SIP message routing                            │
                              │  • Load balancing to PBX nodes                    │
                              │  • dstcheck API lookups                           │
                              │  • PCI Pal tromboning                             │
                              └───────────────────────┬───────────────────────────┘
                                                      │
                                       ┌──────────────┼──────────────┐
                                       ▼              ▼              ▼
                              ┌────────────┐  ┌────────────┐  ┌────────────┐
                              │ FreeSWITCH │  │ FreeSWITCH │  │ FreeSWITCH │
                              │   PBX 01   │  │   PBX 02   │  │   PBX N    │
                              └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                                    │               │               │
                                    └───────────────┼───────────────┘
                                                    │
                              ┌─────────────────────┼─────────────────────┐
                              │                     │                     │
                              ▼                     ▼                     ▼
                     ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
                     │   CoreAPI   │       │   Dialplan  │       │     CDR     │
                     │   (REST)    │       │  Processor  │       │  Processor  │
                     └─────────────┘       └─────────────┘       └─────────────┘
```

## OpenSIPS (SIP Proxy)

### Purpose

OpenSIPS is an open-source SIP proxy that acts as the front door for all SIP traffic. It forwards calls to and from the FreeSWITCH PBX nodes.

### Key Responsibilities

| Function | Description |
|----------|-------------|
| SIP Routing | Routes SIP messages between carriers, devices, and PBX nodes |
| Load Balancing | Distributes calls across multiple FreeSWITCH instances |
| Device Registration | Stores device registration details (softphones, webphones, Yealink) |
| dstcheck Lookups | Calls CoreAPI to determine call routing based on destination |
| PCI Pal Integration | Trombones calls through PCI Pal for PCI compliance |
| Dialog Management | Tracks active SIP sessions |

### Network Configuration

| Port | Protocol | Profile | Primary Use |
|------|----------|---------|-------------|
| 5050 | UDP/TCP | Trusted | SIP trunks |
| 5060 | UDP/TCP | Internal | Devices (webphone, softphone, Yealink) |
| 5080 | UDP/TCP | External | Carriers |
| 5090 | UDP/TCP | Billing | Billing purposes |

### Database Tables

OpenSIPS uses a local MySQL database for:

| Table | Purpose |
|-------|---------|
| `dialog` | Tracks active calls (each record = one call) |
| `load_balancer` | PBX nodes available for load balancing |
| `location` | Device registration locations |
| `usr_preferences` | AVP variables (legacy) |
| `version` | Module version tracking |

### Redmatter Module

OpenSIPS includes a custom Redmatter module that provides platform-specific functionality:

```cfg
# Configuration parameters
modparam("redmatter", "fs_path", "172.30.98.22")
modparam("redmatter", "api_local_url", "http://api-local.redmatter.com/opensips")
modparam("redmatter", "api_timeout", 5)
```

#### Exported Functions

| Function | Description |
|----------|-------------|
| `redmatter_register()` | Handles REGISTER requests |
| `redmatter_subscribe()` | Handles SUBSCRIBE requests |
| `redmatter_handle_refer()` | Handles inbound REFER requests |
| `redmatter_dstcheck()` | Processes INVITE to add/amend headers based on R-URI |
| `redmatter_is_sender_us()` | Checks if message originated from our PBX |
| `redmatter_is_ip_us()` | Checks if IP belongs to a PBX |
| `redmatter_check_shutdown()` | Checks if shutdown mode is enabled |
| `redmatter_get_shutdown_response()` | Gets response code for shutdown mode |

### dstcheck API

When calls arrive at OpenSIPS, the `dstcheck` API is called to determine routing:

```xml
<!-- Request -->
POST /opensips/dstcheck HTTP/1.1
<?xml version="1.0" encoding="UTF-8"?>
<DSTCheck
 RURI="sip:541021447745113878@sip.redmatter.com:5050;user=phone"
 P-Asserted="+447410152010"
 From="+447410152010"
 To="541021447745113878"
 Profile="internal"
 TLS="notls"
 SourceIP="2887672342"
 MediaIP="2887672342"
 SIPProblems="13"
/>

<!-- Response -->
<?xml version="1.0" encoding="UTF-8"?>
<Destination 
  OrgID="2" 
  RURI="sip:447745113878@sip.redmatter.com:5050" 
  Profile="trusted" 
  To="447745113878" 
  Copy="RURI,From,To,P-Asserted-Identity,Allow" 
  X-RMInfo="D=ee.com;C=EEEE;L=;O=2;N=447410152010;H=;M=;P=541021;F=1101;T=14;G=;Z=;X=MNO;"
  Region="GB" 
  CallRoutingEnvironment="RT"
/>
```

### MNO Prefix Handling

Certain carriers (EE, Netcom) add prefixes to indicate call type:

| Customer | Prefix | Type |
|----------|--------|------|
| EE | 541020 | MT (Mobile Terminating) |
| EE | 541021 | MO (Mobile Originating) |
| Netcom | 19500 | MO |
| Netcom | 19502 | MT |

OpenSIPS strips these prefixes before forwarding to FreeSWITCH and adds them back on the B-leg via `X-RMInfo` header.

### Monitoring Commands

```bash
# Show uptime
opensipsctl fifo uptime

# List load balancer entries
opensipsctl fifo lb_list

# Show all active dialogs (calls)
opensipsctl fifo dlg_list

# Show shared memory stats
opensipsctl fifo get_statistics shmem:

# Show registered device
opensipsctl ul show 12031@fnga-003790.sip.nbox.com

# Control load balancer entry
opensipsctl fifo lb_status 11 0    # Disable entry 11
opensipsctl fifo lb_status 11 1    # Enable entry 11

# Enable/disable shutdown mode
opensipsctl fifo shutdown 0        # Disable (accept INVITEs)
opensipsctl fifo shutdown 1        # Enable (reject new INVITEs)
```

### File Locations

| Type | Path |
|------|------|
| Config files | `/etc/opensips/defines.m4`, `/etc/opensips/opensips.cfg.m4` |
| Application | `/usr/sbin/opensips` |
| Log files | `/var/log/app/opensips-prod-<region>-rt-sip01a.log` |

### Service Management

```bash
# Restart service
systemctl restart opensips

# Check if running
ps ax | grep opensips
opensipsctl fifo uptime
```

---

## FreeSWITCH (PBX)

### Purpose

FreeSWITCH is an open-source PBX that handles call processing, including executing routing policies and dialplan logic for inbound and outbound calls.

### Key Responsibilities

| Function | Description |
|----------|-------------|
| Call Processing | Executes dialplan and routing policy logic |
| Media Handling | Processes RTP audio streams |
| Voicemail | Records and plays voicemail messages |
| Call Recording | Captures call audio for compliance |
| IVR | Interactive voice response menus |
| Call Queuing | Agent queue management |
| Conference | Multi-party calling |

### Network Configuration

| Port | Protocol | Profile | Primary Use |
|------|----------|---------|-------------|
| 5050 | UDP | Trusted | SIP trunks |
| 5060 | UDP | Internal | Devices |
| 5070 | UDP | Private | Inter-switch communication |
| 5080 | UDP | External | Carriers |
| 5090 | UDP | Billing | Billing purposes |
| 8021 | TCP | ESL | Event Socket Library |
| 16384-32767 | UDP | RTP | Audio and DTMF |

### Custom Modules

#### mod_rmAPI

Core module for API calls and platform integration:

| Feature | Description |
|---------|-------------|
| API Calls | HTTP requests to CoreAPI |
| rmdb | Database access via API (replaces direct DB) |
| rmgroup | Group management via API |
| mod_limit replacement | Resource limiting via API |
| DTMF Detection | Detects and removes DTMF for CTI |
| rm_transcribed | Creates media bugs for transcription |

Configuration (`/etc/freeswitch/vars/common.xml`):
```xml
<X-PRE-PROCESS cmd="set" data="rmpAPIURL=http://api.redmatter.com"/>
<X-PRE-PROCESS cmd="set" data="rmpAPIMagicNumber=xxxx"/>
<X-PRE-PROCESS cmd="set" data="rmpDGAPIURL=http://dgapi.redmatter.com"/>
<X-PRE-PROCESS cmd="set" data="rmpDGAPIMagicNumber=xxxx"/>
```

#### mod_rmvoicemail

Custom voicemail module based on mod_voicemail:

- Uses CoreAPI for database queries (not local DB)
- Uses libs3 for storage gateway access (S3-compatible)
- Supports email notifications with attachments
- PIN management via `*101`

#### mod_rmremoterec

Remote recording module for:
- Etrali OpenTrade turrets
- Cisco CUCM phones
- VAD-based silence detection
- Audio chunking and archiving

### Monitoring Commands

```bash
# Show uptime and status
fs_cli -x "status"

# Show active channels (call legs)
fs_cli -x "show channels"

# Show Sofia SIP stack status
fs_cli -x "sofia status"

# Show specific profile
fs_cli -x "sofia status profile internal"
```

### File Locations

| Type | Path |
|------|------|
| Config files | `/etc/freeswitch/` |
| Application | `/usr/share/freeswitch` |
| Log files | `/var/log/app/freeswitch-prod-<region>-rt-pbx01<host>.log` |

### Service Management

```bash
# Restart service
systemctl restart freeswitch

# Check if running
ps ax | grep freeswitch
fs_cli -x "status"
```

---

## High Availability

### OpenSIPS HA

- **Two OpenSIPS hosts per region** with load balancing
- Calls distributed across both proxies
- If one fails, traffic routes to the other
- Device registrations stored in local MySQL (replicated)

### FreeSWITCH HA

- **Multiple FreeSWITCH hosts per region**
- OpenSIPS load balances across all PBX nodes
- If one PBX fails, new calls route to others
- Active calls on failed node are lost

### Failover Scenarios

| Scenario | Impact | Recovery |
|----------|--------|----------|
| Single OpenSIPS failure | Minimal - traffic shifts to partner | Automatic |
| Single FreeSWITCH failure | Active calls lost, new calls unaffected | Automatic |
| All OpenSIPS in region | Region offline | DNS/SRV failover to secondary region |
| All FreeSWITCH in region | Region offline | Requires OpenSIPS reconfiguration |

---

## PCI Pal Integration

For organizations requiring PCI DSS compliance, calls can be routed through PCI Pal to descope cardholder data.

### How It Works

1. OpenSIPS identifies PCI-enabled calls via dstcheck API response
2. Calls are "tromboned" through PCI Pal's platform
3. RTP (including DTMF) passes through PCI Pal, not Natterbox
4. Customer enters card details via DTMF, which PCI Pal intercepts
5. Natterbox never sees sensitive card data

### Inbound PCI Call Flow

```
Customer → Carrier → OpenSIPS → PCI Pal → OpenSIPS → FreeSWITCH → Agent
                                    ↑
                              Card data never
                              reaches Natterbox
```

### PCI Headers

| Header | Purpose |
|--------|---------|
| `X-PCI` | Contains PCI routing info: `dir=inbound;routed=yes;org=007820` |
| `X-pcipal-route` | PCI Pal route identifier: `Production-Inbound-Natterbox-007820` |

### Secure Mode

When agent enters PIN to enable secure mode:
1. FreeSWITCH sends PIN via SIP INFO to PCI Pal
2. PCI Pal sends re-INVITE to redirect customer's RTP
3. Customer's DTMF goes to PCI Pal only
4. After payment, PCI Pal sends re-INVITE to restore normal audio

---

## Integration Points

### CoreAPI Integration

Both OpenSIPS and FreeSWITCH communicate with CoreAPI:

| Component | API Endpoint | Purpose |
|-----------|--------------|---------|
| OpenSIPS | `/opensips/dstcheck` | Routing decisions |
| FreeSWITCH | `/freeswitch/*` | Directory, LCR, CDR |

### Database Dependencies

| Component | Database | Purpose |
|-----------|----------|---------|
| OpenSIPS | Local MySQL | Registrations, dialogs, load balancer |
| FreeSWITCH | Via API only | No direct DB access |

---

## Troubleshooting

### Common Issues

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| No calls completing | All calls fail | Check OpenSIPS lb_list for active PBX nodes |
| Registration failures | Devices can't register | Check OpenSIPS location table, verify DNS |
| One-way audio | Caller/callee can't hear | Check RTP port range, NAT configuration |
| PCI routing failure | X-PCI shows `routed=no` | Check PCI Pal connectivity, zone configuration |

### Log Analysis

```bash
# OpenSIPS - Check for call setup issues
grep "INVITE" /var/log/app/opensips-*.log | tail -100

# FreeSWITCH - Check for call errors
fs_cli -x "console loglevel debug"
grep "ERR" /var/log/app/freeswitch-*.log | tail -100

# Check specific call by Call-ID
grep "67379138_133669561@84.14.246.203" /var/log/app/opensips-*.log
```

---

## Source References

- [Confluence: FreeSWITCH Service Overview](https://natterbox.atlassian.net/wiki/spaces/A/pages/1717141540)
- [Confluence: OpenSIPS Service Overview](https://natterbox.atlassian.net/wiki/spaces/A/pages/1717141556)
- [GitHub: platform-opensips](https://github.com/redmatter/platform-opensips)
- [GitHub: platform-freeswitch](https://github.com/redmatter/platform-freeswitch)

---

## Related Documentation

- [Voice Routing Overview](./overview.md)
- [Dialplan Processing](./dialplan.md)
- [CDR Processing](./cdr-processing.md)
- [TTS Gateway](./tts-gateway.md)
