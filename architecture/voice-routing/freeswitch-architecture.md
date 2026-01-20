# FreeSWITCH Architecture and Configuration

> **Last Updated**: 2026-01-20
> **Status**: Comprehensive Documentation
> **Owner**: Platform Team
> **Repository**: [platform-freeswitch](https://github.com/redmatter/platform-freeswitch), [platform-fscore](https://github.com/redmatter/platform-fscore), [platform-fsxinetdsocket](https://github.com/redmatter/platform-fsxinetdsocket)

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Loaded Modules](#loaded-modules)
4. [Configuration File Structure](#configuration-file-structure)
5. [SIP Profile Configurations](#sip-profile-configurations)
6. [Event Socket Library (ESL)](#event-socket-library-esl)
7. [XML CURL Integration](#xml-curl-integration)
8. [Least Cost Routing (LCR)](#least-cost-routing-lcr)
9. [Conference System](#conference-system)
10. [Custom Red Matter Modules](#custom-red-matter-modules)
11. [Environment Variables](#environment-variables)
12. [Systemd Service Configuration](#systemd-service-configuration)
13. [Health Check Endpoints](#health-check-endpoints)
14. [Integration Points](#integration-points)
15. [Troubleshooting](#troubleshooting)

---

## Overview

FreeSWITCH is the core telephony engine in the Red Matter platform, handling all voice call routing, SIP signaling, media processing, and integration with external services. It is deployed as a containerized service with custom-built Red Matter modules for voicemail, activity logging, remote recording, and API integration.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **SIP Signaling** | Full SIP support via mod_sofia with multiple profiles |
| **Media Processing** | Audio transcoding, recording, conferencing |
| **Call Routing** | XML dialplan with dynamic configuration via XML CURL |
| **Least Cost Routing** | Intelligent carrier selection via mod_lcr |
| **Voicemail** | Custom Red Matter voicemail system (mod_rmvoicemail) |
| **Activity Logging** | Real-time call activity logging (mod_rmlogactivity) |
| **API Integration** | Platform API integration (mod_rmapi) |
| **Speech Recognition** | UniMRCP integration for ASR/TTS |
| **Conferencing** | Multi-party audio conferencing |

### Core Configuration Parameters

```xml
<!-- switch.conf.xml - Core Settings -->
<param name="max-sessions" value="1500"/>
<param name="sessions-per-second" value="128"/>
<param name="loglevel" value="debug"/>
<param name="dump-cores" value="yes"/>
<param name="rtp-enable-zrtp" value="true"/>
<param name="mailer-app" value="/usr/sbin/sendmail"/>
<param name="mailer-app-args" value="-t -fnoreply@redmatter.com"/>
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FreeSWITCH Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │  PSTN Carriers  │     │   SIP Trunks    │     │   WebRTC/SIP    │       │
│  │  (via Gateways) │     │   (External)    │     │    Clients      │       │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘       │
│           │                       │                       │                 │
│           │      SIP/RTP          │      SIP/RTP          │   SIP/SRTP     │
│           ▼                       ▼                       ▼                 │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                         mod_sofia (SIP Stack)                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  external1   │  │  internal1   │  │  internal2   │  ...        │    │
│  │  │  Profile     │  │  Profile     │  │  Profile     │             │    │
│  │  │  Port: 5060  │  │  Port: 5061  │  │  Port: 5062  │             │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    FreeSWITCH Core Engine                           │    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ mod_dialplan │  │  mod_lcr     │  │mod_conference│              │    │
│  │  │    _xml      │  │(Least Cost)  │  │              │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ mod_rmapi    │  │mod_rmvoice   │  │mod_rmlog     │              │    │
│  │  │              │  │   mail       │  │  activity    │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ mod_lua      │  │mod_spandsp   │  │ mod_unimrcp  │              │    │
│  │  │              │  │              │  │              │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                    │                          │                             │
│       ESL (8021)   │                          │   HTTP                      │
│                    ▼                          ▼                             │
│  ┌────────────────────────┐    ┌────────────────────────┐                  │
│  │    FSXInetDSocket      │    │      XML CURL          │                  │
│  │    (Port: 60321)       │    │   (mod_xml_curl)       │                  │
│  │                        │    │                        │                  │
│  │  - Lua Script Engine   │    │  - Dynamic Dialplan    │                  │
│  │  - CRM Integration     │    │  - Directory Lookup    │                  │
│  │  - Custom Dialplan     │    │  - Configuration       │                  │
│  └───────────┬────────────┘    └───────────┬────────────┘                  │
│              │                              │                               │
└──────────────┼──────────────────────────────┼───────────────────────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           External Services                                   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Core API   │  │   DG API     │  │  Service     │  │   MRCP       │    │
│  │              │  │              │  │  Gateway     │  │   Server     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Loaded Modules

FreeSWITCH loads modules at startup based on the `modules.conf.xml` configuration. The following modules are actively loaded in the Red Matter deployment:

### Logging Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_console` | Console output and logging | `console.conf.xml` |
| `mod_syslog` | System logging integration | `syslog.conf.xml` |

### XML Interface Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_xml_curl` | HTTP-based dynamic XML configuration | `xml_curl.conf.xml` |
| `mod_xml_cdr` | Call Detail Record generation in XML | `xml_cdr.conf.xml` |

### Event Handler Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_event_socket` | Event Socket Library (ESL) for external control | `event_socket.conf.xml` |

### Endpoint Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_sofia` | SIP User Agent (primary VoIP endpoint) | `sofia.conf.xml` |
| `mod_loopback` | Loopback endpoint for internal call routing | N/A |

### Application Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_commands` | CLI and API commands | N/A |
| `mod_conference` | Multi-party audio/video conferencing | `conference.conf.xml` |
| `mod_dptools` | Dialplan tools and utilities | N/A |
| `mod_expr` | Expression evaluation | N/A |
| `mod_fifo` | First In First Out call queuing | `fifo.conf.xml` |
| `mod_hash` | Hash-based data storage | N/A |
| `mod_spandsp` | T.38 fax, DTMF detection, tone generation | `spandsp.conf.xml` |
| `mod_soundtouch` | Audio manipulation (pitch, tempo) | N/A |
| `mod_valet_parking` | Call parking functionality | N/A |
| `mod_distributor` | Load distribution across resources | `distributor.conf.xml` |

### Dialplan Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_dialplan_xml` | XML-based dialplan processing | N/A (uses XML configs) |

### Codec Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_opencore_amr` | AMR-NB and AMR-WB codec support | N/A |

### File Format Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_sndfile` | Sound file playback/recording (WAV, etc.) | N/A |
| `mod_native_file` | Native audio format support | N/A |
| `mod_shout` | MP3/Icecast streaming support | `shout.conf.xml` |
| `mod_local_stream` | Local audio stream playback | `local_stream.conf.xml` |
| `mod_tone_stream` | DTMF tone generation | N/A |

### Scripting Language Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_spidermonkey` | JavaScript scripting support | `spidermonkey.conf.xml` |
| `mod_lua` | Lua scripting support | `lua.conf.xml` |

### ASR/TTS Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_unimrcp` | UniMRCP integration for speech services | `unimrcp.conf.xml` |

### Language/Say Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_say_en` | English language say module | N/A |

### Custom Red Matter Modules

| Module | Purpose | Configuration File |
|--------|---------|-------------------|
| `mod_rmapi` | Red Matter Platform API integration | `rmapi.conf.xml` |
| `mod_rmlogactivity` | Call activity logging to platform | `rmlogactivity.conf.xml` |
| `mod_rmvoicemail` | Custom voicemail system | `rmvoicemail.conf.xml` |
| `mod_rmremoterec` | Remote recording functionality (optional) | `rmremoterec.conf.xml` |

---

## Configuration File Structure

FreeSWITCH configuration files are located in `/etc/freeswitch/` with the following directory structure:

```
/etc/freeswitch/
├── freeswitch.xml              # Main configuration entry point
├── vars.xml                    # Global variables and environment settings
├── autoload_configs/           # Module-specific configurations
│   ├── modules.conf.xml        # Modules to load at startup
│   ├── sofia.conf.xml          # SIP stack configuration
│   ├── event_socket.conf.xml   # ESL configuration
│   ├── xml_curl.conf.xml       # Dynamic XML configuration
│   ├── lcr.conf.xml            # Least Cost Routing
│   ├── conference.conf.xml     # Conferencing profiles
│   ├── switch.conf.xml         # Core FreeSWITCH settings
│   ├── rmapi.conf.xml          # Red Matter API module config
│   ├── rmlogactivity.conf.xml  # Activity logging config
│   ├── rmvoicemail.conf.xml    # Voicemail system config
│   ├── unimrcp.conf.xml        # MRCP client config
│   └── ... (other module configs)
├── sip_profiles/               # SIP profile definitions
│   ├── internal1.xml           # Internal SIP profile (softphones)
│   ├── external1.xml           # External SIP profile (carriers)
│   └── ... (additional profiles)
├── dialplan/                   # Dialplan contexts
│   ├── default.xml             # Default dialplan context
│   ├── public.xml              # Public inbound context
│   └── ... (custom contexts)
├── directory/                  # User/extension directory
│   └── default/                # Default domain directory
└── mrcp_profiles/              # MRCP server profiles
    └── speechserver.xml        # Speech server configuration
```

### Global Variables (vars.xml)

The `vars.xml` file defines global variables used throughout FreeSWITCH configuration:

```xml
<include>
  <!-- Core Settings -->
  <X-PRE-PROCESS cmd="set" data="default_password=1234"/>
  <X-PRE-PROCESS cmd="set" data="sound_prefix=$${sounds_dir}/en/us/callie"/>
  
  <!-- Network Settings -->
  <X-PRE-PROCESS cmd="exec-set" data="local_ip_v4=hostname -I | cut -d' ' -f1"/>
  <X-PRE-PROCESS cmd="set" data="external_rtp_ip=$${local_ip_v4}"/>
  <X-PRE-PROCESS cmd="set" data="external_sip_ip=$${local_ip_v4}"/>
  
  <!-- Domain Settings -->
  <X-PRE-PROCESS cmd="set" data="domain=$${local_ip_v4}"/>
  <X-PRE-PROCESS cmd="set" data="domain_name=$${domain}"/>
  
  <!-- Codec Preferences -->
  <X-PRE-PROCESS cmd="set" data="global_codec_prefs=PCMA,PCMU,GSM"/>
  <X-PRE-PROCESS cmd="set" data="outbound_codec_prefs=PCMA,PCMU"/>
  
  <!-- Recording Settings -->
  <X-PRE-PROCESS cmd="set" data="recordings_dir=/var/lib/freeswitch/recordings"/>
  <X-PRE-PROCESS cmd="set" data="base_dir=/var/lib/freeswitch"/>
  
  <!-- Platform Integration -->
  <X-PRE-PROCESS cmd="set" data="rmpCoreApiUrl=${CORE_API_URL}"/>
  <X-PRE-PROCESS cmd="set" data="rmpDgApiUrl=${DG_API_URL}"/>
  <X-PRE-PROCESS cmd="set" data="rmpFSXInetdSocket=${FSX_SOCKET_HOST}:60321"/>
  
  <!-- Environment-specific overrides -->
  <X-PRE-PROCESS cmd="include" data="vars_local.xml"/>
</include>
```

---

## SIP Profile Configurations

### Internal Profile (internal1.xml)

The internal profile handles SIP traffic from registered endpoints (softphones, IP phones, WebRTC clients):

```xml
<profile name="internal1">
  <domains>
    <domain name="all" alias="true" parse="true"/>
  </domains>
  <settings>
    <!-- Network Bindings -->
    <param name="sip-ip" value="$${local_ip_v4}"/>
    <param name="sip-port" value="5061"/>
    <param name="rtp-ip" value="$${local_ip_v4}"/>
    <param name="ext-rtp-ip" value="$${external_rtp_ip}"/>
    <param name="ext-sip-ip" value="$${external_sip_ip}"/>
    
    <!-- Call Processing -->
    <param name="context" value="default"/>
    <param name="dialplan" value="XML"/>
    <param name="dtmf-duration" value="2000"/>
    <param name="inbound-codec-prefs" value="$${global_codec_prefs}"/>
    <param name="outbound-codec-prefs" value="$${outbound_codec_prefs}"/>
    
    <!-- NAT Handling -->
    <param name="apply-nat-acl" value="nat.auto"/>
    <param name="aggressive-nat-detection" value="true"/>
    <param name="local-network-acl" value="localnet.auto"/>
    <param name="NDLB-received-in-nat-reg-contact" value="true"/>
    
    <!-- Security -->
    <param name="apply-inbound-acl" value="domains"/>
    <param name="auth-calls" value="true"/>
    <param name="challenge-realm" value="auto_from"/>
    
    <!-- TLS Configuration -->
    <param name="tls" value="$${internal_ssl_enable}"/>
    <param name="tls-bind-params" value="transport=tls"/>
    <param name="tls-sip-port" value="5071"/>
    <param name="tls-cert-dir" value="$${internal_ssl_dir}"/>
    <param name="tls-version" value="$${sip_tls_version}"/>
    
    <!-- RTP/Media -->
    <param name="rtp-timeout-sec" value="300"/>
    <param name="rtp-hold-timeout-sec" value="1800"/>
    <param name="enable-timer" value="false"/>
    <param name="session-timeout" value="1800"/>
    
    <!-- Recording -->
    <param name="record-path" value="$${recordings_dir}"/>
    <param name="record-template" value="${caller_id_number}.${target_domain}.${strftime(%Y-%m-%d-%H-%M-%S)}.wav"/>
    
    <!-- WebRTC Support -->
    <param name="apply-candidate-acl" value="rfc1918.auto"/>
    <param name="enable-3pcc" value="proxy"/>
  </settings>
  
  <gateways>
    <!-- Gateways loaded dynamically via XML CURL -->
  </gateways>
</profile>
```

### External Profile (external1.xml)

The external profile handles SIP traffic to/from carriers and external systems:

```xml
<profile name="external1">
  <settings>
    <!-- Network Bindings -->
    <param name="sip-ip" value="$${local_ip_v4}"/>
    <param name="sip-port" value="5060"/>
    <param name="rtp-ip" value="$${local_ip_v4}"/>
    <param name="ext-rtp-ip" value="$${external_rtp_ip}"/>
    <param name="ext-sip-ip" value="$${external_sip_ip}"/>
    
    <!-- Call Processing -->
    <param name="context" value="public"/>
    <param name="dialplan" value="XML"/>
    <param name="inbound-codec-prefs" value="$${global_codec_prefs}"/>
    <param name="outbound-codec-prefs" value="$${outbound_codec_prefs}"/>
    
    <!-- Security - No authentication required for carrier traffic -->
    <param name="auth-calls" value="false"/>
    <param name="apply-inbound-acl" value="carriers"/>
    
    <!-- NAT Handling -->
    <param name="aggressive-nat-detection" value="true"/>
    <param name="NDLB-force-rport" value="true"/>
    
    <!-- RTP/Media -->
    <param name="rtp-timeout-sec" value="300"/>
    <param name="rtp-hold-timeout-sec" value="1800"/>
    
    <!-- Caller ID Handling -->
    <param name="caller-id-in-from" value="true"/>
    <param name="inbound-late-negotiation" value="true"/>
    
    <!-- OPTIONS/Keepalive -->
    <param name="disable-register" value="true"/>
    <param name="manage-presence" value="false"/>
  </settings>
  
  <gateways>
    <!-- Carrier gateways loaded dynamically via XML CURL -->
    <X-PRE-PROCESS cmd="include" data="external/*.xml"/>
  </gateways>
</profile>
```

### Profile Port Matrix

| Profile | SIP Port | SIPS (TLS) Port | Purpose |
|---------|----------|-----------------|---------|
| external1 | 5060 | - | Carrier/external traffic |
| internal1 | 5061 | 5071 | Internal/registered endpoints |
| internal2 | 5062 | 5072 | Secondary internal (if needed) |

---

## Event Socket Library (ESL)

The Event Socket Library provides external applications with the ability to control FreeSWITCH and receive events.

### ESL Configuration (event_socket.conf.xml)

```xml
<configuration name="event_socket.conf" description="Socket Client">
  <settings>
    <param name="nat-map" value="false"/>
    <param name="listen-ip" value="0.0.0.0"/>
    <param name="listen-port" value="8021"/>
    <param name="password" value="ClueCon"/>
    <param name="apply-inbound-acl" value="socketacl"/>
  </settings>
</configuration>
```

### ESL Connection Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `listen-ip` | `0.0.0.0` | Listen on all interfaces |
| `listen-port` | `8021` | Default ESL port |
| `password` | `ClueCon` | Authentication password (configure per environment) |
| `apply-inbound-acl` | `socketacl` | ACL for allowed connections |

### ESL Connection Modes

#### Inbound Mode
External applications connect to FreeSWITCH ESL port:

```php
// PHP Example
$esl = new ESLconnection("freeswitch-host", "8021", "ClueCon");
$esl->events("plain", "ALL");
while ($e = $esl->recvEvent()) {
    // Process events
}
```

#### Outbound Mode (FSXInetDSocket)
FreeSWITCH connects out to an external socket server during dialplan processing.

---

## FSXInetDSocket

The FSXInetDSocket package enables FreeSWITCH to offload processing of dialplan-oriented tasks via outbound ESL connections.

### Architecture

```
FreeSWITCH                           FSXInetDSocket Server
    │                                        │
    │  1. Set rmSocketTask variable          │
    │  2. socket application                 │
    │                                        │
    ├───────── TCP Connection ───────────────►
    │       (Port 60321)                     │
    │                                        │
    │  3. ESL Event Data                     │
    │◄───────────────────────────────────────┤
    │                                        │
    │  4. Process Task                       │
    │     (Lua, CRM, etc.)                   │
    │                                        │
    │  5. ESL Commands                       │
    │◄───────────────────────────────────────┤
    │                                        │
```

### XINETD Configuration

```
service fssocket
{
    type            = UNLISTED
    socket_type     = stream
    protocol        = tcp
    wait            = no
    user            = root
    server          = /usr/bin/php
    server_args     = /usr/bin/fsxinetdsocket
    log_on_success  += DURATION
    nice            = 10
    disable         = no
    port            = 60321
    per_source      = 100
    instances       = 100
    cps             = 100 10
}
```

### Dialplan Integration

```xml
<!-- Set the socket task before invoking -->
<action application="set" data="rmSocketTask=SF_DataConnector::querySource"/>
<action application="socket" data="${rmpFSXInetdSocket} sync full"/>
```

### Available Socket Tasks

| Task Class | Method | Purpose |
|------------|--------|---------|
| `SF_DataConnector` | `querySource` | CRM data lookup |
| `LuaScriptEngine` | `execute` | Run Lua scripts |
| `CallManagement` | `route` | Custom call routing |
| `Available` | `test` | Health check |

### FSXInetDSocket Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORE_API_HOST` | `api-local` | Core API hostname |
| `DG_API_HOST` | `dgapi` | DG API hostname |
| `SERVICE_GATEWAY_HOST` | `servicegateway` | Service Gateway hostname |
| `ESL_HOST` | `esl` | ESL host for callbacks |

---

## XML CURL Integration

The `mod_xml_curl` module enables dynamic configuration retrieval from HTTP endpoints.

### Configuration (xml_curl.conf.xml)

```xml
<configuration name="xml_curl.conf" description="cURL XML Gateway">
  <bindings>
    <!-- Configuration binding -->
    <binding name="configuration">
      <param name="gateway-url" 
             value="http://${CORE_API_HOST}:8080/freeswitch/configuration.xml" 
             bindings="configuration"/>
      <param name="method" value="POST"/>
      <param name="timeout" value="10"/>
      <param name="connect-timeout" value="5"/>
    </binding>
    
    <!-- Dialplan binding -->
    <binding name="dialplan">
      <param name="gateway-url" 
             value="http://${CORE_API_HOST}:8080/freeswitch/dialplan.xml" 
             bindings="dialplan"/>
      <param name="method" value="POST"/>
      <param name="timeout" value="10"/>
    </binding>
    
    <!-- Directory binding (user authentication) -->
    <binding name="directory">
      <param name="gateway-url" 
             value="http://${CORE_API_HOST}:8080/freeswitch/directory.xml" 
             bindings="directory"/>
      <param name="method" value="POST"/>
      <param name="timeout" value="10"/>
    </binding>
  </bindings>
</configuration>
```

### XML CURL Request Parameters

When FreeSWITCH makes XML CURL requests, it POSTs the following data:

#### Configuration Request
```
section=configuration
tag_name=configuration
key_name=name
key_value=<module_name>
hostname=<freeswitch_hostname>
```

#### Dialplan Request
```
section=dialplan
hostname=<freeswitch_hostname>
Caller-Context=<context>
Caller-Destination-Number=<destination>
Caller-ANI=<caller_id>
variable_sip_from_user=<sip_user>
... (all channel variables)
```

#### Directory Request
```
section=directory
tag_name=domain
key_name=name
key_value=<domain>
user=<username>
domain=<domain>
action=<sip-auth|user_call>
hostname=<freeswitch_hostname>
```

### Expected Response Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<document type="freeswitch/xml">
  <section name="dialplan">
    <context name="default">
      <extension name="dynamic_route">
        <condition>
          <action application="bridge" data="sofia/gateway/carrier1/$1"/>
        </condition>
      </extension>
    </context>
  </section>
</document>
```

---

## Least Cost Routing (LCR)

The `mod_lcr` module provides intelligent carrier selection based on cost and routing rules.

### LCR Configuration (lcr.conf.xml)

```xml
<configuration name="lcr.conf" description="LCR Configuration">
  <settings>
    <param name="odbc-dsn" value="freeswitch-lcr"/>
    <param name="reorder-by-rate" value="false"/>
    <param name="quote-in-list" value="false"/>
  </settings>
  
  <profiles>
    <profile name="default">
      <param name="id" value="1"/>
      <param name="order_by" value="rate,quality,reliability"/>
    </profile>
    
    <profile name="premium">
      <param name="id" value="2"/>
      <param name="order_by" value="quality,reliability,rate"/>
    </profile>
  </profiles>
</configuration>
```

### LCR Database Schema

```sql
-- lcr table
CREATE TABLE lcr (
    id SERIAL PRIMARY KEY,
    digits VARCHAR(20) NOT NULL,
    rate DECIMAL(10,6),
    carrier_id INTEGER REFERENCES carriers(id),
    lead_strip INTEGER DEFAULT 0,
    trail_strip INTEGER DEFAULT 0,
    prefix VARCHAR(20),
    suffix VARCHAR(20),
    lcr_profile INTEGER DEFAULT 1,
    date_start TIMESTAMP,
    date_end TIMESTAMP,
    quality DECIMAL(5,2),
    reliability DECIMAL(5,2),
    cid VARCHAR(32),
    enabled BOOLEAN DEFAULT true,
    UNIQUE (digits, carrier_id)
);

-- carriers table
CREATE TABLE carriers (
    id SERIAL PRIMARY KEY,
    carrier_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true
);

-- gateways table
CREATE TABLE lcr_gateways (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER REFERENCES carriers(id),
    gateway_name VARCHAR(255) NOT NULL,
    codec_string VARCHAR(255),
    enabled BOOLEAN DEFAULT true
);
```

### LCR Dialplan Usage

```xml
<extension name="outbound_lcr">
  <condition field="destination_number" expression="^(\d{10,})$">
    <action application="lcr" data="$1"/>
    <action application="bridge" data="${lcr_auto_route}"/>
  </condition>
</extension>
```

### LCR API Commands

| Command | Description |
|---------|-------------|
| `lcr <number> [profile]` | Get LCR route for number |
| `lcr_admin show profiles` | List LCR profiles |
| `lcr_admin show gateways` | List gateways |
| `reload mod_lcr` | Reload LCR configuration |

---

## Conference System

The `mod_conference` module provides multi-party audio conferencing.

### Conference Configuration (conference.conf.xml)

```xml
<configuration name="conference.conf" description="Audio Conference">
  <advertise>
    <room name="3001@$${domain}" status="FreeSWITCH"/>
  </advertise>
  
  <caller-controls>
    <group name="default">
      <control action="mute" digits="0"/>
      <control action="deaf mute" digits="*"/>
      <control action="energy up" digits="9"/>
      <control action="energy equ" digits="8"/>
      <control action="energy dn" digits="7"/>
      <control action="vol talk up" digits="3"/>
      <control action="vol talk zero" digits="2"/>
      <control action="vol talk dn" digits="1"/>
      <control action="vol listen up" digits="6"/>
      <control action="vol listen zero" digits="5"/>
      <control action="vol listen dn" digits="4"/>
      <control action="hangup" digits="#"/>
    </group>
    
    <group name="moderator">
      <control action="mute" digits="0"/>
      <control action="lock" digits="*1"/>
      <control action="event" digits="*2"/>
      <control action="energy up" digits="9"/>
      <control action="energy equ" digits="8"/>
      <control action="energy dn" digits="7"/>
      <control action="vol talk up" digits="3"/>
      <control action="vol talk zero" digits="2"/>
      <control action="vol talk dn" digits="1"/>
      <control action="vol listen up" digits="6"/>
      <control action="vol listen zero" digits="5"/>
      <control action="vol listen dn" digits="4"/>
      <control action="hangup" digits="#"/>
    </group>
  </caller-controls>
  
  <profiles>
    <profile name="default">
      <param name="domain" value="$${domain}"/>
      <param name="rate" value="8000"/>
      <param name="interval" value="20"/>
      <param name="energy-level" value="300"/>
      <param name="sound-prefix" value="$${sounds_dir}/en/us/callie"/>
      
      <!-- Entry/Exit Sounds -->
      <param name="enter-sound" value="tone_stream://%(200,0,500,600,700)"/>
      <param name="exit-sound" value="tone_stream://%(500,0,300,200,100,50,25)"/>
      <param name="muted-sound" value="conference/conf-muted.wav"/>
      <param name="unmuted-sound" value="conference/conf-unmuted.wav"/>
      <param name="alone-sound" value="conference/conf-alone.wav"/>
      <param name="locked-sound" value="conference/conf-locked.wav"/>
      <param name="max-members-sound" value="conference/conf-full.wav"/>
      <param name="kicked-sound" value="conference/conf-kicked.wav"/>
      
      <!-- Recording -->
      <param name="auto-record" value="$${recordings_dir}/${conference_name}_${strftime(%Y-%m-%d-%H-%M-%S)}.wav"/>
      
      <!-- Limits -->
      <param name="max-members" value="100"/>
      <param name="comfort-noise" value="true"/>
      
      <!-- Controls -->
      <param name="caller-controls" value="default"/>
      <param name="moderator-controls" value="moderator"/>
    </profile>
    
    <profile name="wideband">
      <param name="rate" value="16000"/>
      <param name="interval" value="20"/>
      <param name="energy-level" value="300"/>
      <!-- ... other params similar to default ... -->
    </profile>
  </profiles>
</configuration>
```

### Conference API Commands

| Command | Description |
|---------|-------------|
| `conference list` | List active conferences |
| `conference <name> list` | List members in conference |
| `conference <name> kick <member>` | Kick a member |
| `conference <name> mute <member>` | Mute a member |
| `conference <name> unmute <member>` | Unmute a member |
| `conference <name> lock` | Lock conference |
| `conference <name> unlock` | Unlock conference |
| `conference <name> record <file>` | Start recording |
| `conference <name> norecord` | Stop recording |

---

## Custom Red Matter Modules

### mod_rmapi

Provides integration with the Red Matter Platform API for authentication, configuration, and call data.

**Configuration (rmapi.conf.xml)**:
```xml
<configuration name="rmapi.conf" description="Red Matter API">
  <settings>
    <param name="api-url" value="${CORE_API_URL}"/>
    <param name="api-key" value="${RMAPI_KEY}"/>
    <param name="timeout" value="5000"/>
    <param name="retry-count" value="3"/>
  </settings>
</configuration>
```

**Features**:
- User/extension authentication
- Call routing decisions
- Feature authorization checks
- Real-time call data sync

### mod_rmlogactivity

Logs call activity to the platform for reporting and analytics.

**Configuration (rmlogactivity.conf.xml)**:
```xml
<configuration name="rmlogactivity.conf" description="Activity Logging">
  <settings>
    <param name="log-url" value="${ACTIVITY_LOG_URL}"/>
    <param name="batch-size" value="100"/>
    <param name="flush-interval" value="5000"/>
    <param name="enable-async" value="true"/>
  </settings>
</configuration>
```

**Events Logged**:
- Call start/answer/end
- DTMF events
- Transfer events
- Conference events
- Voicemail events

### mod_rmvoicemail

Custom voicemail system integrated with the platform.

**Configuration (rmvoicemail.conf.xml)**:
```xml
<configuration name="rmvoicemail.conf" description="RM Voicemail">
  <settings>
    <param name="storage-type" value="file"/>
    <param name="storage-path" value="/var/lib/freeswitch/voicemail"/>
    <param name="api-url" value="${VOICEMAIL_API_URL}"/>
    <param name="notify-url" value="${VOICEMAIL_NOTIFY_URL}"/>
    <param name="max-message-length" value="300"/>
    <param name="min-message-length" value="3"/>
    <param name="default-greeting" value="voicemail/greeting.wav"/>
    <param name="record-format" value="wav"/>
  </settings>
  
  <profiles>
    <profile name="default">
      <param name="max-messages" value="100"/>
      <param name="greeting-max-length" value="60"/>
      <param name="notify-email" value="true"/>
      <param name="attach-audio" value="true"/>
    </profile>
  </profiles>
</configuration>
```

**Features**:
- Message recording and storage
- Email notification with audio attachment
- API integration for message management
- Custom greetings per user

### mod_rmremoterec (Optional)

Enables remote call recording control and storage.

**Features**:
- On-demand recording start/stop
- Remote storage upload
- Recording metadata management

---

## Environment Variables

FreeSWITCH and associated services use the following environment variables:

### Core FreeSWITCH Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FREESWITCH_PARAMS` | (empty) | Additional startup parameters |
| `FS_LOG_LEVEL` | `debug` | Logging verbosity |
| `FS_MAX_SESSIONS` | `1500` | Maximum concurrent calls |
| `FS_SPS` | `128` | Sessions per second limit |

### Network Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_IP_V4` | (auto-detected) | Primary IP address |
| `EXTERNAL_RTP_IP` | (same as local) | External RTP IP for NAT |
| `EXTERNAL_SIP_IP` | (same as local) | External SIP IP for NAT |

### Platform Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORE_API_URL` | `http://api-local:8080` | Core API base URL |
| `CORE_API_HOST` | `api-local` | Core API hostname |
| `DG_API_HOST` | `dgapi` | DG API hostname |
| `SERVICE_GATEWAY_HOST` | `servicegateway` | Service Gateway hostname |
| `ESL_HOST` | `localhost` | ESL connection host |
| `ESL_PORT` | `8021` | ESL connection port |
| `ESL_PASSWORD` | `ClueCon` | ESL authentication password |

### FSXInetDSocket Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FSX_SOCKET_HOST` | `localhost` | FSX socket server host |
| `FSX_SOCKET_PORT` | `60321` | FSX socket server port |

### Voicemail Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICEMAIL_API_URL` | (from CORE_API_URL) | Voicemail API endpoint |
| `VOICEMAIL_NOTIFY_URL` | (from CORE_API_URL) | Voicemail notification endpoint |
| `VOICEMAIL_STORAGE_PATH` | `/var/lib/freeswitch/voicemail` | Local voicemail storage |

---

## Systemd Service Configuration

FreeSWITCH runs as a systemd service with the following configuration:

### Service File (/usr/lib/systemd/system/freeswitch.service)

```ini
[Unit]
Description=FreeSWITCH
After=syslog.target network.target var-lib-freeswitch-db.mount
Requires=var-lib-freeswitch-db.mount
OnFailure=crash-monitor@%n.service

[Service]
Type=forking
EnvironmentFile=-/etc/sysconfig/freeswitch
RuntimeDirectory=freeswitch
RuntimeDirectoryMode=0777
PIDFile=/run/freeswitch/freeswitch.pid
WorkingDirectory=/run/freeswitch
Nice=-10
LimitDATA=infinity
LimitFSIZE=infinity
LimitSIGPENDING=infinity
LimitNOFILE=999999
LimitMSGQUEUE=infinity
LimitNPROC=infinity
LimitAS=infinity
LimitLOCKS=infinity
LimitSTACK=16777216
LimitMEMLOCK=infinity
IOSchedulingClass=realtime
IOSchedulingPriority=2
CPUSchedulingPolicy=rr
CPUSchedulingPriority=89
Restart=always
RestartSec=15s
StartLimitInterval=0
TimeoutSec=45s
ExecStartPre=/bin/find /var/lib/freeswitch/db -type f -delete
ExecStart=/usr/bin/freeswitch -u freeswitch -nc -rp -core $FREESWITCH_PARAMS
ExecReload=/usr/bin/kill -HUP $MAINPID

[Install]
WantedBy=multi-user.target
```

### Key Service Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `Nice=-10` | Higher CPU priority | Real-time audio processing |
| `LimitNOFILE=999999` | High file descriptor limit | Many concurrent connections |
| `IOSchedulingClass=realtime` | Real-time I/O scheduling | Audio quality |
| `CPUSchedulingPolicy=rr` | Round-robin scheduling | Predictable latency |
| `CPUSchedulingPriority=89` | High CPU priority | Real-time performance |
| `Restart=always` | Auto-restart on failure | High availability |
| `RestartSec=15s` | 15-second restart delay | Graceful recovery |

### Environment File (/etc/sysconfig/freeswitch)

```bash
# FreeSWITCH startup parameters
FREESWITCH_PARAMS="-nonat"

# Override log level for production
# FS_LOG_LEVEL=warning
```

### Service Management Commands

```bash
# Start FreeSWITCH
sudo systemctl start freeswitch

# Stop FreeSWITCH
sudo systemctl stop freeswitch

# Restart FreeSWITCH
sudo systemctl restart freeswitch

# Reload configuration (SIGHUP)
sudo systemctl reload freeswitch

# Check status
sudo systemctl status freeswitch

# View logs
sudo journalctl -u freeswitch -f
```

---

## Health Check Endpoints

### ESL Status Check

```bash
#!/bin/bash
# ESL health check
echo "api status" | timeout 2 nc localhost 8021
```

### FSXInetDSocket Health Check

The FSX Docker container implements a Docker HEALTHCHECK that:
1. Establishes TCP connection to localhost:60321
2. Requests the `Available` test app to be executed
3. Expects valid ESL response within 2 seconds
4. Runs every 10 seconds, 2 consecutive failures = unhealthy

```dockerfile
HEALTHCHECK --interval=10s --timeout=2s --retries=2 \
    CMD /usr/local/bin/fsx-healthcheck.sh
```

### Sofia Status Check

```bash
# Check SIP profile status
fs_cli -x "sofia status"

# Check specific profile
fs_cli -x "sofia status profile internal1"
```

### API Health Check Endpoint

The platform provides HTTP health endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/freeswitch/health` | GET | Overall FreeSWITCH health |
| `/freeswitch/sofia/status` | GET | SIP stack status |
| `/freeswitch/channels/count` | GET | Active channel count |

### Monitoring Metrics

Key metrics to monitor:

| Metric | Command | Normal Range |
|--------|---------|--------------|
| Active channels | `show channels count` | < 80% of max-sessions |
| Sessions per second | `show status` | < configured SPS limit |
| Sofia profile status | `sofia status` | All profiles RUNNING |
| Memory usage | `show status` | Stable, not growing |
| CPU usage | System monitor | < 70% per core |

---

## Integration Points

### Core API Integration

FreeSWITCH integrates with the Core API for:

| Integration | Protocol | Purpose |
|-------------|----------|---------|
| XML CURL Configuration | HTTP POST | Dynamic dialplan, directory |
| Call Events | HTTP POST | Real-time call state updates |
| Authentication | HTTP GET | User/extension validation |
| CDR Submission | HTTP POST | Call detail records |

### Service Gateway Integration

```
FreeSWITCH → Service Gateway → External Services
           └→ Salesforce CRM
           └→ Google Calendar
           └→ Custom Webhooks
```

### MRCP Server Integration

FreeSWITCH connects to MRCP servers for:
- Automatic Speech Recognition (ASR)
- Text-to-Speech (TTS)
- DTMF recognition

**UniMRCP Configuration (unimrcp.conf.xml)**:
```xml
<configuration name="unimrcp.conf" description="UniMRCP Client">
  <settings>
    <param name="default-synth-profile" value="speechserver"/>
    <param name="default-recog-profile" value="speechserver"/>
  </settings>
  
  <profiles>
    <profile name="speechserver">
      <param name="server-ip" value="${MRCP_SERVER_IP}"/>
      <param name="server-port" value="5060"/>
      <param name="rtp-ip" value="$${local_ip_v4}"/>
      <param name="rtp-port-min" value="4000"/>
      <param name="rtp-port-max" value="5000"/>
    </profile>
  </profiles>
</configuration>
```

### Database Integration

FreeSWITCH uses ODBC for database connectivity:

```xml
<!-- /etc/odbc.ini -->
[freeswitch-lcr]
Driver = PostgreSQL
Servername = db-host
Database = freeswitch_lcr
Username = freeswitch
Password = ****
Port = 5432
```

---

## Troubleshooting

### Common Issues

#### Sofia Profile Not Starting

**Symptoms**: Profile shows as "DOWN" in `sofia status`

**Causes**:
1. Port already in use
2. IP address binding issue
3. TLS certificate problems

**Solution**:
```bash
# Check port usage
netstat -tlnp | grep 5060

# Check FreeSWITCH logs
fs_cli -x "console loglevel debug"

# Restart profile
fs_cli -x "sofia profile internal1 restart"
```

#### ESL Connection Refused

**Symptoms**: Cannot connect to port 8021

**Causes**:
1. mod_event_socket not loaded
2. Firewall blocking port
3. ACL rejecting connection

**Solution**:
```bash
# Check module is loaded
fs_cli -x "module_exists mod_event_socket"

# Reload if needed
fs_cli -x "load mod_event_socket"

# Check ACLs
fs_cli -x "acl reloadxml"
```

#### XML CURL Timeout

**Symptoms**: Calls fail with "no route found"

**Causes**:
1. Core API unreachable
2. Network issues
3. API timeout

**Solution**:
```bash
# Test API connectivity
curl -X POST http://api-host:8080/freeswitch/dialplan.xml

# Check FreeSWITCH XML CURL errors
fs_cli -x "xml_curl debug on"

# Increase timeout if needed (in xml_curl.conf.xml)
<param name="timeout" value="30"/>
```

#### High Memory Usage

**Symptoms**: FreeSWITCH memory growing over time

**Causes**:
1. Memory leak in module
2. Too many cached objects
3. Recording files not cleaned

**Solution**:
```bash
# Check memory status
fs_cli -x "show status"

# Clear caches
fs_cli -x "sofia profile internal1 flush_inbound_reg"

# Check for stuck channels
fs_cli -x "show channels"
```

### Debug Commands

```bash
# Enable SIP tracing
fs_cli -x "sofia profile internal1 siptrace on"

# View active calls
fs_cli -x "show calls"

# View channel details
fs_cli -x "uuid_dump <uuid>"

# View dialplan processing
fs_cli -x "console loglevel debug"

# Test dialplan
fs_cli -x "eval ${expand(api originate {export_vars=DIALPLAN}user/1001 &park())}"
```

### Log Locations

| Log | Location | Purpose |
|-----|----------|---------|
| FreeSWITCH | `/var/log/freeswitch/freeswitch.log` | Main application log |
| Syslog | `/var/log/messages` | System-level events |
| CDR | `/var/log/freeswitch/cdr-csv/` | Call detail records |
| FSXInetDSocket | Via syslog to `/var/log/messages` | ESL socket processing |

---

## Related Documentation

- [Voice Telephony Service Inventory](../../services/inventory/voice-telephony.md)
- [SIP Trunk Configuration Guide](./sip-trunk-configuration.md)
- [Call Routing Rules](./call-routing-rules.md)
- [LCR Administration Guide](./lcr-administration.md)
- [Voicemail System Guide](./voicemail-system.md)

---

## Appendix: Complete Module List

### Modules Loaded (modules.conf.xml)

```xml
<!-- Loggers -->
<load module="mod_console"/>
<load module="mod_syslog"/>

<!-- XML Interfaces -->
<load module="mod_xml_curl"/>
<load module="mod_xml_cdr"/>

<!-- Event Handlers -->
<load module="mod_event_socket"/>

<!-- Endpoints -->
<load module="mod_sofia"/>
<load module="mod_loopback"/>

<!-- Applications -->
<load module="mod_commands"/>
<load module="mod_conference"/>
<load module="mod_dptools"/>
<load module="mod_expr"/>
<load module="mod_fifo"/>
<load module="mod_hash"/>
<load module="mod_spandsp"/>
<load module="mod_soundtouch"/>
<load module="mod_valet_parking"/>
<load module="mod_distributor"/>

<!-- Dialplan -->
<load module="mod_dialplan_xml"/>

<!-- Codecs -->
<load module="mod_opencore_amr"/>

<!-- File Formats -->
<load module="mod_sndfile"/>
<load module="mod_native_file"/>
<load module="mod_shout"/>
<load module="mod_local_stream"/>
<load module="mod_tone_stream"/>

<!-- Languages -->
<load module="mod_spidermonkey"/>
<load module="mod_lua"/>

<!-- ASR/TTS -->
<load module="mod_unimrcp"/>

<!-- Say -->
<load module="mod_say_en"/>

<!-- Red Matter Custom -->
<load module="mod_rmapi"/>
<load module="mod_rmlogactivity"/>
<load module="mod_rmvoicemail"/>
<!-- <load module="mod_rmremoterec"/> -->  <!-- Optional -->
```

### Modules Available But Not Loaded

```xml
<!-- Commented out in modules.conf.xml -->
<!--<load module="mod_logfile"/>-->
<!--<load module="mod_enum"/>-->
<!--<load module="mod_xml_rpc"/>-->
<!--<load module="mod_cdr_csv"/>-->
<!--<load module="mod_event_multicast"/>-->
<!--<load module="mod_zeroconf"/>-->
<!--<load module="mod_snmp"/>-->
<!--<load module="mod_ldap"/>-->
<!--<load module="mod_dingaling"/>-->
<!--<load module="mod_iax"/>-->
<!--<load module="mod_portaudio"/>-->
<!--<load module="mod_voicemail"/>-->   <!-- Using mod_rmvoicemail instead -->
<!--<load module="mod_fax"/>-->
<!--<load module="mod_lcr"/>-->         <!-- Can be enabled for LCR -->
<!--<load module="mod_callcenter"/>-->  <!-- Can be enabled for call center -->
<!--<load module="mod_db"/>-->
<!--<load module="mod_limit"/>-->
<!--<load module="mod_curl"/>-->
<!--<load module="mod_nibblebill"/>-->
<!--<load module="mod_voipcodecs"/>-->
<!--<load module="mod_g723_1"/>-->
<!--<load module="mod_g729"/>-->
<!--<load module="mod_amr"/>-->
<!--<load module="mod_ilbc"/>-->
<!--<load module="mod_speex"/>-->
<!--<load module="mod_h26x"/>-->
<!--<load module="mod_flite"/>-->
<!--<load module="mod_pocketsphinx"/>-->
<!--<load module="mod_cepstral"/>-->
<!--<load module="mod_perl"/>-->
<!--<load module="mod_python"/>-->
<!--<load module="mod_java"/>-->
```
