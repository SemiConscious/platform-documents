# Dialplan and PBX Deep-Dive

> **Last Updated:** 2026-01-20  
> **Source:** platform-dialplan, platform-freeswitch, platform-opensips repositories, Confluence  
> **Status:** ✅ Complete

---

## Overview

This document provides a deep technical dive into the dialplan structure, PBX architecture, TTS gateway service, and routing policy implementation within the Natterbox voice platform. It complements the [Voice Routing Overview](./overview.md) with detailed implementation specifics.

The voice routing system uses a layered architecture:
1. **OpenSIPS** - SIP proxy for registration, load balancing, and initial routing
2. **FreeSWITCH** - PBX for call control, media handling, and dialplan execution
3. **fsxinetd** - Lua scripting engine for business logic and integrations

---

## Dialplan Architecture

### Dialplan Contexts Overview

The FreeSWITCH dialplan is organized into multiple XML context files, each handling specific call flow scenarios:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIALPLAN CONTEXT HIERARCHY                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   dpPreRouting.xml          ──►  Initial call processing & number lookup    │
│         │                                                                   │
│         ▼                                                                   │
│   dpTrustedIn.xml           ──►  Inbound calls from trusted sources         │
│         │                                                                   │
│         ▼                                                                   │
│   dpOutbound.xml            ──►  Outbound call routing to carriers          │
│         │                                                                   │
│         ▼                                                                   │
│   dpSupport.xml             ──►  Support extensions (voicemail, IVR, etc.)  │
│         │                                                                   │
│         ▼                                                                   │
│   dialPlanFeatures.xml      ──►  Feature processing (transfers, holds)      │
│         │                                                                   │
│         ▼                                                                   │
│   dpPrivate.xml             ──►  Internal extension routing                 │
│         │                                                                   │
│         ▼                                                                   │
│   dpRedirect.xml            ──►  Call redirection and forwarding            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Dialplan Files

| File | Purpose | Size | Key Extensions |
|------|---------|------|----------------|
| `dpPreRouting.xml` | Pre-routing number normalization, caller ID lookup | ~40KB | Number format normalization, geographic routing |
| `dpTrustedIn.xml` | Inbound call handling from SIP trunks | ~23KB | DID routing, IVR entry points |
| `dpOutbound.xml` | Outbound routing to carriers | ~28KB | Carrier selection, CLI manipulation |
| `dpSupport.xml` | Voicemail, conferencing, IVR | ~71KB | Voicemail access, queue management |
| `dialPlanFeatures.xml` | Call features and controls | ~44KB | Transfer, hold, park, pickup |
| `dpPrivate.xml` | Internal extension dialing | ~20KB | Extension-to-extension routing |
| `dpRedirect.xml` | Forwarding logic | ~3KB | Redirect handling |

---

## Pre-Routing (dpPreRouting.xml)

### Purpose

The pre-routing context is the first point of entry for all calls. It handles:

- Number normalization (converting local formats to E.164)
- Geographic routing decisions
- Account identification
- Initial call setup variables

### Key Extensions

```xml
<!-- Number normalization extension -->
<extension name="normalize_number">
  <condition field="${destination_number}" expression="^0([1-9]\d+)$">
    <action application="set" data="destination_number=+44$1"/>
    <action application="transfer" data="${destination_number} XML dpTrustedIn"/>
  </condition>
</extension>

<!-- Account lookup extension -->
<extension name="account_lookup">
  <condition field="${sip_to_user}" expression="^(\d+)$">
    <action application="lua" data="account_lookup.lua"/>
    <action application="set" data="account_id=${lua_account_id}"/>
  </condition>
</extension>
```

### Number Normalization Rules

The system applies country-specific normalization rules:

| Country | Input Format | Normalized Format |
|---------|-------------|-------------------|
| UK | 020 1234 5678 | +442012345678 |
| UK | 07700 900123 | +447700900123 |
| US | (555) 123-4567 | +15551234567 |
| Australia | 02 1234 5678 | +61212345678 |

Configuration is loaded from `files/conf/redmatter/NormaliseRules.xml`:

```xml
<normalisation>
  <rule country="GB" pattern="^0(\d{10})$" replacement="+44$1"/>
  <rule country="US" pattern="^1?(\d{10})$" replacement="+1$1"/>
  <rule country="AU" pattern="^0(\d{9})$" replacement="+61$1"/>
</normalisation>
```

---

## Trusted Inbound Routing (dpTrustedIn.xml)

### Purpose

Handles inbound calls from trusted SIP sources (carriers, SIP trunks). This context:

- Validates the called number (DID)
- Looks up the routing policy for the DID
- Routes to the appropriate destination (user, queue, IVR)

### Call Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRUSTED INBOUND CALL FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Carrier SIP INVITE                                                        │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────┐                                                       │
│   │ DID Validation  │──► Invalid DID ──► Play "Number not in service"       │
│   └────────┬────────┘                                                       │
│            │ Valid                                                          │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ Account Lookup  │──► No account ──► Play "Account suspended"            │
│   └────────┬────────┘                                                       │
│            │ Found                                                          │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ Routing Policy  │──► Get routing rules for this DID                     │
│   │     Lookup      │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                │
│     ┌──────┴──────┬────────────┬───────────────┐                           │
│     ▼             ▼            ▼               ▼                           │
│  ┌──────┐    ┌────────┐   ┌────────┐    ┌───────────┐                      │
│  │ User │    │ Queue  │   │  IVR   │    │ Voicemail │                      │
│  └──────┘    └────────┘   └────────┘    └───────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Extension Patterns

```xml
<!-- Main DID routing extension -->
<extension name="inbound_did">
  <condition field="${destination_number}" expression="^(\+?\d{10,15})$">
    <!-- Log the inbound call -->
    <action application="log" data="INFO Inbound call to DID: ${destination_number}"/>
    
    <!-- Lookup routing policy via Lua -->
    <action application="lua" data="inbound_routing.lua"/>
    
    <!-- Route based on policy result -->
    <action application="transfer" data="${routing_destination} XML ${routing_context}"/>
  </condition>
</extension>

<!-- Fallback for unmatched DIDs -->
<extension name="unmatched_did">
  <condition field="${destination_number}" expression=".*">
    <action application="answer"/>
    <action application="playback" data="ivr/ivr-invalid_number.wav"/>
    <action application="hangup" data="UNALLOCATED_NUMBER"/>
  </condition>
</extension>
```

---

## Outbound Routing (dpOutbound.xml)

### Purpose

Handles all outbound call routing to external destinations. Key responsibilities:

- Carrier selection based on routing policies
- CLI (Caller ID) manipulation
- Cost optimization and least-cost routing
- Failover to backup carriers

### Carrier Selection Logic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTBOUND CARRIER SELECTION                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Outbound Call Request                                                     │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────┐                                                       │
│   │  Account Check  │──► No outbound permissions ──► Reject call            │
│   └────────┬────────┘                                                       │
│            │ Permitted                                                      │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ CLI Validation  │──► Invalid CLI ──► Use default CLI                    │
│   └────────┬────────┘                                                       │
│            │                                                                │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ Routing Policy  │──► Get carrier preference list                        │
│   └────────┬────────┘                                                       │
│            │                                                                │
│     ┌──────┴────────────────────┐                                          │
│     ▼                           ▼                                          │
│  ┌────────────────┐      ┌────────────────┐                                │
│  │Primary Carrier │──X──►│ Backup Carrier │                                │
│  │   (Cost: $)    │      │   (Cost: $$)   │                                │
│  └───────┬────────┘      └───────┬────────┘                                │
│          │                       │                                          │
│          ▼                       ▼                                          │
│   SIP INVITE to carrier gateway                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CLI Manipulation

The system supports various CLI presentation rules:

```xml
<!-- CLI manipulation for outbound calls -->
<extension name="set_outbound_cli">
  <condition field="${caller_id_number}" expression="^(\+?1?\d{10})$">
    <!-- Format CLI for US/Canada -->
    <action application="set" data="effective_caller_id_number=+1${1}"/>
  </condition>
  <condition field="${caller_id_number}" expression="^(\+?44\d{10})$">
    <!-- Format CLI for UK -->
    <action application="set" data="effective_caller_id_number=${1}"/>
  </condition>
</extension>

<!-- Carrier gateway selection -->
<extension name="carrier_gateway_primary">
  <condition field="${sip_network_ip}" expression=".*">
    <action application="set" data="sip_h_X-Carrier-Id=${carrier_id}"/>
    <action application="bridge" data="sofia/gateway/${primary_gateway}/${destination_number}"/>
  </condition>
</extension>
```

### Dialling Rules

Configured in `files/conf/redmatter/DiallingRules.xml`:

```xml
<diallingRules>
  <!-- International dialling -->
  <rule name="international" pattern="^00(\d+)$" 
        action="normalize" replacement="+$1"/>
  
  <!-- National (UK) dialling -->
  <rule name="uk_national" pattern="^0([1-9]\d{9,10})$" 
        action="normalize" replacement="+44$1"/>
  
  <!-- Emergency services -->
  <rule name="emergency" pattern="^(999|112|911)$" 
        action="route" carrier="emergency_gateway"/>
  
  <!-- Premium rate blocking -->
  <rule name="premium_block" pattern="^(\+44(9|8[47]))\d+$" 
        action="block" reason="Premium rate blocked"/>
</diallingRules>
```

---

## Support Extensions (dpSupport.xml)

### Purpose

The largest dialplan file, handling all support features including:

- Voicemail access and management
- Conference calling
- Call queues
- Interactive Voice Response (IVR)
- Call recording controls
- Feature codes (e.g., *67 for privacy)

### Key Feature Extensions

#### Voicemail Access

```xml
<!-- Voicemail access extension -->
<extension name="voicemail_access">
  <condition field="${destination_number}" expression="^\*98$">
    <action application="answer"/>
    <action application="sleep" data="500"/>
    <action application="set" data="vm_extension=${caller_id_number}"/>
    <action application="lua" data="voicemail_access.lua"/>
  </condition>
</extension>

<!-- Direct voicemail deposit -->
<extension name="voicemail_deposit">
  <condition field="${destination_number}" expression="^\*99(\d+)$">
    <action application="set" data="target_extension=$1"/>
    <action application="answer"/>
    <action application="lua" data="voicemail_deposit.lua"/>
  </condition>
</extension>
```

#### Conference Bridge

```xml
<!-- Conference room entry -->
<extension name="conference_entry">
  <condition field="${destination_number}" expression="^conf(\d{4,8})$">
    <action application="answer"/>
    <action application="set" data="conference_id=$1"/>
    <action application="lua" data="conference_auth.lua"/>
    <action application="conference" data="${conference_id}@default"/>
  </condition>
</extension>
```

#### Call Queue

```xml
<!-- Call queue entry -->
<extension name="queue_entry">
  <condition field="${destination_number}" expression="^queue(\d+)$">
    <action application="set" data="queue_id=$1"/>
    <action application="answer"/>
    <!-- Play hold music while waiting -->
    <action application="set" data="hold_music=local_stream://moh"/>
    <!-- Enter queue via fsxinetd -->
    <action application="lua" data="queue_entry.lua"/>
  </condition>
</extension>
```

### Feature Codes

| Code | Function | Description |
|------|----------|-------------|
| `*67` | Privacy | Block CLI for next call |
| `*72` | Forward All | Enable call forwarding |
| `*73` | Cancel Forward | Disable call forwarding |
| `*78` | Do Not Disturb | Enable DND |
| `*79` | Cancel DND | Disable DND |
| `*98` | Voicemail | Access voicemail |
| `*99xxx` | Deposit VM | Leave voicemail for extension |
| `*70` | Call Waiting | Toggle call waiting |

---

## Dialplan Features (dialPlanFeatures.xml)

### Purpose

Handles mid-call features and call control operations:

- Call transfer (blind and attended)
- Call hold/retrieve
- Call park/pickup
- Three-way calling
- Call recording controls

### Transfer Handling

```xml
<!-- Blind transfer -->
<extension name="blind_transfer">
  <condition field="${destination_number}" expression="^\*2(\d+)$">
    <action application="set" data="transfer_destination=$1"/>
    <action application="transfer" data="${transfer_destination} XML dpPrivate"/>
  </condition>
</extension>

<!-- Attended transfer -->
<extension name="attended_transfer">
  <condition field="${destination_number}" expression="^\*4(\d+)$">
    <action application="set" data="transfer_destination=$1"/>
    <action application="set" data="transfer_type=attended"/>
    <action application="lua" data="attended_transfer.lua"/>
  </condition>
</extension>
```

### Call Park System

```xml
<!-- Park call -->
<extension name="park_call">
  <condition field="${destination_number}" expression="^700$">
    <action application="answer"/>
    <action application="valet_park" data="valet_lot auto in 1 10"/>
  </condition>
</extension>

<!-- Retrieve parked call -->
<extension name="retrieve_parked">
  <condition field="${destination_number}" expression="^70([1-9])$">
    <action application="answer"/>
    <action application="valet_park" data="valet_lot $1 out"/>
  </condition>
</extension>
```

---

## PBX Component Architecture

### FreeSWITCH Configuration Structure

The FreeSWITCH PBX component is configured via the `platform-freeswitch` repository:

```
platform-freeswitch/
├── files/
│   ├── conf/
│   │   ├── autoload_configs/         # Module configurations
│   │   │   ├── switch.conf.xml       # Core switch settings
│   │   │   ├── modules.conf.xml      # Module loading
│   │   │   ├── sofia.conf.xml        # SIP stack config
│   │   │   └── lua.conf.xml          # Lua scripting config
│   │   ├── sip_profiles/             # SIP endpoint profiles
│   │   │   ├── internal.xml          # Internal profile (users)
│   │   │   └── external.xml          # External profile (carriers)
│   │   └── vars.xml                  # Global variables
│   └── scripts/
│       └── lua/                      # Lua scripts
├── config/                           # Environment configuration
└── README.md
```

### Core Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FREESWITCH PBX COMPONENTS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                       FreeSWITCH Core                              │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │     │
│   │  │   Switch    │  │    Event    │  │   Channel   │  │  Session  │ │     │
│   │  │   Core      │  │   System    │  │   Manager   │  │  Manager  │ │     │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                         Module Layer                               │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │     │
│   │  │mod_sofia    │  │mod_lua      │  │mod_dptools  │  │mod_event_ │ │     │
│   │  │(SIP Stack)  │  │(Scripting)  │  │(Dialplan)   │  │socket     │ │     │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │     │
│   │                                                                    │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │     │
│   │  │mod_record   │  │mod_conferen │  │mod_voicemai │  │mod_db     │ │     │
│   │  │(Recording)  │  │ce (Meet)    │  │l (VM)       │  │(Database) │ │     │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                       Media Processing                             │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │     │
│   │  │ RTP Engine  │  │  Codec      │  │   DTMF      │  │   Media   │ │     │
│   │  │             │  │  Handling   │  │  Detection  │  │   Files   │ │     │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sofia SIP Profiles

FreeSWITCH uses the Sofia SIP stack with multiple profiles:

#### Internal Profile (Users)

```xml
<profile name="internal">
  <settings>
    <param name="sip-ip" value="$${local_ip_v4}"/>
    <param name="sip-port" value="5060"/>
    <param name="rtp-ip" value="$${local_ip_v4}"/>
    <param name="context" value="dpPreRouting"/>
    <param name="codec-prefs" value="OPUS,PCMU,PCMA,G729"/>
    <param name="apply-nat-acl" value="rfc1918"/>
    <param name="auth-calls" value="true"/>
    <param name="inbound-reg-force-matching-username" value="true"/>
  </settings>
</profile>
```

#### External Profile (Carriers)

```xml
<profile name="external">
  <settings>
    <param name="sip-ip" value="$${external_ip_v4}"/>
    <param name="sip-port" value="5080"/>
    <param name="rtp-ip" value="$${external_ip_v4}"/>
    <param name="context" value="dpTrustedIn"/>
    <param name="auth-calls" value="false"/>
    <param name="inbound-codec-negotiation" value="generous"/>
  </settings>
  <gateways>
    <X-PRE-PROCESS cmd="include" data="gateways/*.xml"/>
  </gateways>
</profile>
```

---

## OpenSIPS SIP Proxy

### Architecture Role

OpenSIPS serves as the front-end SIP proxy, handling:

- SIP registration for all endpoints
- Authentication via database lookup
- Load balancing across PBX servers
- NAT traversal via RTP proxy
- Cross-region routing

### Configuration Overview

From `platform-opensips` repository:

```
platform-opensips/
├── files/
│   ├── opensips.cfg              # Main configuration
│   ├── opensips.m4               # M4 macro templates
│   └── scripts/
│       ├── routing.cfg           # Routing logic
│       ├── auth.cfg              # Authentication
│       └── lb.cfg                # Load balancing
├── config/
│   └── env.conf                  # Environment variables
└── README.md
```

### Load Balancing Logic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OPENSIPS LOAD BALANCING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Incoming SIP Request                                                      │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────┐                                                       │
│   │ Authentication  │──► Failed ──► 401 Unauthorized                        │
│   └────────┬────────┘                                                       │
│            │ Success                                                        │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ Registration    │──► REGISTER ──► Store in usrloc                       │
│   │     Check       │                                                       │
│   └────────┬────────┘                                                       │
│            │ INVITE                                                         │
│            ▼                                                                │
│   ┌─────────────────┐     ┌────────────────────────────────────┐           │
│   │  Load Balancer  │────►│  PBX Pool                          │           │
│   │  (Round Robin   │     │  ┌──────────┐  ┌──────────┐       │           │
│   │   with Health)  │     │  │  PBX-01  │  │  PBX-02  │  ...  │           │
│   └─────────────────┘     │  └──────────┘  └──────────┘       │           │
│                           └────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key OpenSIPS Functions

```
# Load balancing configuration (pseudo-code from opensips.cfg)

# Define PBX destinations
modparam("dispatcher", "list_file", "/etc/opensips/dispatcher.list")
modparam("dispatcher", "ds_ping_method", "OPTIONS")
modparam("dispatcher", "ds_ping_interval", 30)

# Routing logic
route {
    if (is_method("REGISTER")) {
        # Handle registration
        if (!www_authorize("natterbox.com", "subscriber")) {
            www_challenge("natterbox.com", "0");
            exit;
        }
        save("location");
        exit;
    }
    
    if (is_method("INVITE")) {
        # Load balance to PBX
        if (!ds_select_dst("1", "4")) {  # Round-robin with probing
            send_reply("503", "Service Unavailable");
            exit;
        }
        
        # Set failure handling
        t_on_failure("PBX_FAILOVER");
        t_relay();
    }
}

failure_route[PBX_FAILOVER] {
    # Try next PBX if first fails
    if (ds_next_dst()) {
        t_relay();
        exit;
    }
    send_reply("503", "All PBX servers unavailable");
}
```

---

## TTS Gateway Service

### Overview

The TTS (Text-to-Speech) Gateway provides voice synthesis capabilities using multiple backend providers:

- Google Cloud Text-to-Speech
- AWS Polly
- Microsoft Azure Speech
- ElevenLabs (for advanced voices)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TTS GATEWAY ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FreeSWITCH                                                                │
│   ┌─────────────────┐                                                       │
│   │  Lua Script     │                                                       │
│   │  tts_speak()    │                                                       │
│   └────────┬────────┘                                                       │
│            │ HTTP Request                                                   │
│            ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      TTS Gateway Service                             │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │   │
│   │  │   REST API  │  │   Cache     │  │    Provider Selection      │  │   │
│   │  │  Endpoint   │  │  Manager    │  │    (Voice → Provider)      │  │   │
│   │  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────────┘  │   │
│   │         │                │                        │                  │   │
│   │         ▼                ▼                        ▼                  │   │
│   │  ┌─────────────────────────────────────────────────────────────────┐│   │
│   │  │                      Audio Cache (Redis/S3)                     ││   │
│   │  │  Key: hash(text + voice + options) → WAV file path             ││   │
│   │  └─────────────────────────────────────────────────────────────────┘│   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│            │ Cache miss                                                     │
│            ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     TTS Provider Backends                            │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│   │  │   Google    │  │    AWS      │  │  Microsoft  │  │ ElevenLabs│  │   │
│   │  │   TTS API   │  │   Polly     │  │   Azure     │  │           │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Voice Configuration

Voices are mapped to providers in configuration:

| Voice ID | Provider | Language | Gender | Quality |
|----------|----------|----------|--------|---------|
| `en-GB-Standard-A` | Google | en-GB | Female | Standard |
| `en-GB-Wavenet-B` | Google | en-GB | Male | Premium |
| `Amy` | AWS Polly | en-GB | Female | Standard |
| `Brian` | AWS Polly | en-GB | Male | Standard |
| `en-GB-SoniaNeural` | Azure | en-GB | Female | Neural |
| `rachel` | ElevenLabs | en-US | Female | Ultra |

### TTS API Interface

```lua
-- Lua TTS integration in FreeSWITCH
local tts = require("tts_gateway")

-- Simple TTS playback
tts.speak(session, "Hello, welcome to Natterbox", {
    voice = "en-GB-Wavenet-B",
    rate = 1.0,
    pitch = 0
})

-- With SSML support
tts.speak_ssml(session, [[
<speak>
  <prosody rate="medium" pitch="+2st">
    Your call is important to us.
  </prosody>
  <break time="500ms"/>
  Please hold while we connect you.
</speak>
]], {voice = "en-GB-Standard-A"})
```

### Caching Strategy

The TTS Gateway implements a multi-level cache:

1. **Memory Cache** - LRU cache for frequently used phrases
2. **Redis Cache** - Distributed cache for cluster-wide sharing
3. **S3 Storage** - Long-term storage for generated audio files

```
Cache Key Generation:
  key = SHA256(text + voice_id + rate + pitch + format)
  path = "tts-cache/{voice_id}/{key[0:2]}/{key}.wav"
```

---

## Routing Policy Implementation

### Overview

Routing policies are defined in Salesforce and executed by the voice platform. The `natterbox-routing-policies` repository provides the UI for creating and managing these policies.

### Policy Types

| Policy Type | Purpose | Example |
|-------------|---------|---------|
| Inbound | Route incoming calls | DID → Queue/User/IVR |
| Outbound | Route outgoing calls | User → Carrier selection |
| Time-based | Schedule routing | Business hours → Queue, After hours → VM |
| Geographic | Route by caller location | UK callers → UK queue |
| Skills-based | Route to appropriate agents | Technical → Tech support queue |

### Policy Structure

```json
{
  "policyId": "RP-001",
  "name": "Main Sales Line",
  "type": "inbound",
  "did": "+442012345678",
  "rules": [
    {
      "order": 1,
      "condition": {
        "type": "time",
        "schedule": "business_hours",
        "timezone": "Europe/London"
      },
      "action": {
        "type": "queue",
        "queueId": "Q-SALES-001",
        "timeout": 120
      }
    },
    {
      "order": 2,
      "condition": {
        "type": "fallback"
      },
      "action": {
        "type": "voicemail",
        "box": "sales-general",
        "greeting": "after-hours"
      }
    }
  ]
}
```

### Policy Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ROUTING POLICY EVALUATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Incoming Call                                                             │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────┐                                                       │
│   │ Load Policy for │                                                       │
│   │ Called Number   │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │  For each rule  │◄─────────────────────────────┐                       │
│   │  (in order)     │                              │                       │
│   └────────┬────────┘                              │                       │
│            │                                        │                       │
│            ▼                                        │                       │
│   ┌─────────────────┐                              │                       │
│   │ Evaluate        │──► Condition NOT met ────────┘                       │
│   │ Condition       │                                                       │
│   └────────┬────────┘                                                       │
│            │ Condition MET                                                  │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ Execute Action  │                                                       │
│   │ (Queue/User/VM) │                                                       │
│   └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Time Condition Evaluation

```lua
-- Time condition evaluation in Lua
function evaluate_time_condition(condition, call_time)
    local schedule = schedules[condition.schedule]
    local tz = condition.timezone or "UTC"
    
    -- Convert call time to target timezone
    local local_time = convert_timezone(call_time, tz)
    
    -- Check if within schedule
    for _, period in ipairs(schedule.periods) do
        if is_within_period(local_time, period) then
            return true
        end
    end
    
    return false
end

-- Schedule definition
schedules = {
    business_hours = {
        periods = {
            {days = {1,2,3,4,5}, start = "09:00", finish = "17:30"},
        }
    },
    extended_hours = {
        periods = {
            {days = {1,2,3,4,5}, start = "08:00", finish = "20:00"},
            {days = {6}, start = "09:00", finish = "13:00"},
        }
    }
}
```

---

## Language and Sound Files

### Directory Structure

```
files/conf/lang/en/redmatter/
├── common.xml                    # Common phrases
├── conference.xml                # Conference prompts
├── dialplan_management.xml       # Admin prompts
├── dialplan_sounds.xml           # Call flow sounds
├── redmatter_vm.xml              # Voicemail prompts
└── sounds.xml                    # General sounds

files/conf/redmatter/
├── DiallingRules.xml             # Number format rules
├── NormaliseRules.xml            # Normalization patterns
└── Phrases.xml                   # Dynamic phrase definitions
```

### Phrase Macros

Custom phrase macros enable dynamic audio generation:

```xml
<macro name="say_account_balance">
  <input pattern="(\d+)\.(\d{2})">
    <match>
      <action function="play-file" data="currency/your_balance_is.wav"/>
      <action function="say" data="$1" method="currency"/>
      <action function="play-file" data="currency/pounds.wav"/>
      <action function="say" data="$2" method="digits"/>
      <action function="play-file" data="currency/pence.wav"/>
    </match>
  </input>
</macro>
```

---

## Performance Considerations

### Dialplan Optimization

1. **Extension Order** - Most frequently matched extensions should be first
2. **Condition Caching** - Use `continue="true"` to avoid re-evaluation
3. **Lua Caching** - Pre-load Lua scripts at startup
4. **Database Queries** - Cache routing policies in memory

### Recommended Settings

```xml
<!-- Dialplan caching -->
<param name="dialplan-cache-capacity" value="1000"/>
<param name="dialplan-cache-ttl" value="300"/>

<!-- Lua optimization -->
<param name="lua-startup-file" value="/scripts/startup.lua"/>
<param name="lua-reload-files" value="false"/>
```

### Monitoring Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Dialplan evaluation time | < 10ms | > 50ms |
| TTS cache hit ratio | > 90% | < 70% |
| Policy lookup time | < 5ms | > 20ms |
| Active calls per PBX | < 500 | > 400 |

---

## Related Documentation

- [Voice Routing Overview](./overview.md) - High-level architecture
- [fsxinetd Service](./fsxinetd.md) - Lua scripting engine details
- [Call Recording](../recording/README.md) - Recording subsystem
- [Transcription Service](../transcription/README.md) - Speech-to-text processing

---

## Repository References

| Repository | Purpose |
|------------|---------|
| `platform-dialplan` | FreeSWITCH dialplan XML configuration |
| `platform-freeswitch` | FreeSWITCH core configuration and scripts |
| `platform-opensips` | OpenSIPS SIP proxy configuration |
| `natterbox-routing-policies` | Routing policy UI application |

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-20 | Documentation Team | Initial comprehensive documentation |
