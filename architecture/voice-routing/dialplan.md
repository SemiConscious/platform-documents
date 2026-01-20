# FreeSWITCH Dialplan Structure

> **Last Updated:** 2026-01-20  
> **Source:** Confluence ENG Space, GitHub platform-dialplan  
> **Status:** ✅ Complete

---

## Overview

The FreeSWITCH dialplan is the core routing engine that determines how calls flow through the Natterbox platform. It uses XML-based configuration with extensions, contexts, and conditions to match and process calls. The dialplan integrates with JavaScript, Lua, and PHP scripts for complex routing logic.

**Repository:** `redmatter/platform-dialplan`

---

## Dialplan Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                           DIALPLAN PROCESSING FLOW                                  │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│   INBOUND CALL                                                                     │
│        │                                                                           │
│        ▼                                                                           │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │
│   │   public    │────▶│dpPreRouting │────▶│ dpOutbound  │────▶│   <OrgID>   │     │
│   │  (carrier)  │     │(pre-process)│     │(ext numbers)│     │  (customer) │     │
│   └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     │
│                                                                      │             │
│   INTERNAL/FEATURE CALLS                                             ▼             │
│        │                                                      ┌─────────────┐     │
│        ▼                                                      │  features   │     │
│   ┌─────────────┐                                             │(feature codes│    │
│   │  features   │                                             └─────────────┘     │
│   └─────────────┘                                                    │             │
│                                                                      ▼             │
│   PRIVATE/LCR CALLS                                          ┌─────────────┐     │
│        │                                                      │DialPlanDest │     │
│        ▼                                                      │ NotFound.js │     │
│   ┌─────────────┐                                             └─────────────┘     │
│   │   private   │◀──────────────────────────────────────────────────┘             │
│   │ (port 5070) │                                                                  │
│   └─────────────┘                                                                  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Dialplan Contexts

### 1. dpPreRouting (Pre-Routing Context)

**File:** `dpPreRouting.xml`

The pre-routing context performs initial call setup and routing decisions. It runs first for most calls and handles:

| Function | Description |
|----------|-------------|
| Call Initialisation | Sets channel variables, initialises CDR data |
| REFER Handling | Processes blind and attended transfers |
| Feature Code Detection | Routes to features context for star codes |
| Emergency Call Detection | Identifies and prioritises emergency numbers |
| Device Limits | Applies concurrent call limits per device |
| Insights Setup | Configures transcription and analysis |

**Key Extensions:**

```xml
<!-- Set the implied destination number -->
<extension name="setImpliedDestNumber" continue="true">
    <condition field="destination_number" expression="(.*)">
        <action inline="true" application="set" data="rmImpliedDest=$1"/>
    </condition>
</extension>

<!-- Handle REFERs for attended transfers across switches -->
<extension name="split_refer">
    <condition field="destination_number" expression="^_refer_(.*)$">
        <action application="set" data="rmReferHandled=true"/>
        <action application="transfer" data="${destination_number} XML ${user_context}"/>
    </condition>
</extension>
```

**Feature Code Routing:**

| Code | Feature | Destination |
|------|---------|-------------|
| `*100` | Voicemail Main | `featureVoiceMain XML features` |
| `*101` | Voicemail Prompted | `featureVoiceMailPrompted XML features` |
| `*111` | Login/Logout Service | `featureLoginLogoutSvce XML features` |
| `*150` | Manage Phrases | `featureManagePhrases XML features` |
| `*180` | Echo Test | `featureEcho XML features` |
| `*182` | Who Am I | `featureWhoAmI XML features` |

### 2. dpOutbound (Outbound Routing Context)

**File:** `dpOutbound.xml`

Handles outbound call routing with country-specific dialling plans. Normalises numbers and routes to external carriers.

**Country-Specific Processing:**

| Country | Code | Number Length | Notes |
|---------|------|---------------|-------|
| UK | 44 | 9+ digits | Default dialplan |
| Spain | 34 | 10+ digits | External dial code support |
| Italy | 39 | 7+ digits | Shorter number lengths |
| Portugal | 351 | 10+ digits | Standard EU |
| Denmark | 45 | 9+ digits | No area codes |
| Sweden | 46 | 9+ digits | Standard Scandinavian |
| Greece | 30 | 9+ digits | Standard EU |
| Ireland | 353 | 8+ digits | Shorter numbers |

**Routing Flow:**

```
1. Identify Home Country Code (rmHCDCode)
2. Normalise number to E.164 format
3. Check for emergency services
4. Route based on device type:
   - Mobile → OutboundMobile hook
   - SIP Trunk → OutboundSIPTrunk hook  
   - SIP Device → OutboundHook
```

### 3. dpPrivate (Private/Internal Context)

**File:** `dpPrivate.xml`  
**Port:** 5070 (internal only)

The private context handles internal routing that shouldn't be exposed externally:

| Extension | Purpose |
|-----------|---------|
| `siplcr_` | LCR (Least Cost Routing) carrier failover |
| `sipds_` | Directory service lookups |
| `transfer_` | Cross-switch attended transfers |
| `policy_` | Connect calls to routing policies |
| `listenin_` | Listen-in/supervisor monitoring |
| `conf_` | Conference bridging |
| `choice_` | Choice mobile MSRN lookups |

### 4. features (Feature Codes Context)

**File:** `dialPlanFeatures.xml`

Implements telephony features accessible via dial codes:

| Feature | Description |
|---------|-------------|
| Voicemail | Access and manage voicemail |
| Call Return | Dial last caller |
| Last Number Redial | Redial last dialled |
| Call Pickup | Pick up ringing calls |
| Group Login/Logout | Join/leave hunt groups |
| Valet Parking | Park and retrieve calls |
| Eavesdrop | Supervisor monitoring |

### 5. public (Carrier Ingress Context)

Entry point for calls from external carriers (PSTN). Performs initial validation and routes to appropriate org context.

### 6. Organisation Contexts (`<OrgID>`)

Each customer organisation has a dedicated context (named by OrgID) containing their specific routing policies configured via AVS (Advanced Voice Services).

---

## Key Channel Variables

### Call Identification

| Variable | Description |
|----------|-------------|
| `rmOrgID` | Organisation identifier |
| `rmUserID` | User identifier |
| `rmDevID` | Device identifier |
| `rmCallCategory` | Call type (SOC, MOC, COC, etc.) |
| `rmDeviceType` | Device type (sip, mobile, siptrunk) |
| `rmHCDCode` | Home Country Dialling code |

### Number Processing

| Variable | Description |
|----------|-------------|
| `rmDialledNumber` | Original dialled number |
| `rmDialledNumberStripped` | Normalised number without prefixes |
| `rmDialledNumberNormalised` | E.164 formatted number |
| `rmDialledNumberType` | Type: USER, EXTERNAL, FEATURE |
| `rmNumberNormalised` | Caller's normalised number |

### Routing Control

| Variable | Description |
|----------|-------------|
| `rmReferHandled` | REFER already processed flag |
| `rmDPPreRoutingDone` | Pre-routing completed flag |
| `rmForceExternal` | Force external routing |
| `rmWithholdCLI` | Suppress caller ID |
| `rmEmergencyNumber` | Emergency call flag |

### CDR and Recording

| Variable | Description |
|----------|-------------|
| `rmCDRDiscard` | Don't generate CDR |
| `rmCDRStoreOnly` | Store CDR but don't process |
| `rmDumpCalls` | RTP packet capture mode |

---

## Carrier Failover (siplcr_ Mechanism)

The `siplcr_` dialplan provides carrier failover without breaking CDR integrity, emulating FreeSWITCH Enterprise Originate syntax.

### Problem Solved

Standard Enterprise Originate syntax causes broken CDRs. The siplcr_ mechanism allows failover between carriers while preserving CDR validity.

### How It Works

```
┌─────────┐      ┌──────────┐      ┌──────────────────┐      ┌─────────┐
│ Caller  │─────▶│FreeSWITCH│─────▶│ Ghost FreeSWITCH │─────▶│ Carrier │
│         │      │ (Main)   │      │   (Port 5070)    │      │         │
└─────────┘      └──────────┘      └──────────────────┘      └─────────┘
                      │                     │
                      │   INVITE to         │
                      │   siplcr_+446666    │    503 from BT
                      │   ─────────────────▶│    ◀────────────
                      │                     │    Retry with iBasis
                      │                     │    ────────────▶
```

### Call Flow Example

1. Caller dials +441111 which routes to Follow Me
2. Follow Me needs to ring +446666 and +447777
3. Instead of direct carrier calls, FreeSWITCH sends INVITEs to:
   - `siplcr_+446666@gateway.redmatter.com:5070`
   - `siplcr_+447777@gateway.redmatter.com:5070`
4. Ghost channels on port 5070 perform LCR lookup
5. Each ghost channel tries carriers sequentially (BT → iBasis → etc.)
6. On 503 from one carrier, automatically tries next
7. Original CDR remains intact on main channel

### Channel Variables for Tracking

| Variable | Description |
|----------|-------------|
| `rmGhostLegConnectedUUID` | UUID of ghost leg connected to carrier |
| `rmOtherLegUUID_<uuid>` | Set for each ghost leg launched |
| `rmOtherLegUUID` | B leg UUID (set on C leg) |

---

## Transfer Handling

### Types of Transfers

| Type | Description |
|------|-------------|
| Blind Transfer | Immediate transfer without announcement |
| Attended Transfer | Consult with target before completing |
| Cross-Switch Transfer | Transfer when legs are on different PBXs |

### Cross-Switch Attended Transfer Challenge

When call legs exist on different FreeSWITCH instances, standard SIP REFER fails because the target switch doesn't know the original Call-ID.

```
┌───────────┐                    ┌───────────┐
│FreeSWITCH │    REFER with      │FreeSWITCH │
│     Y     │────Call-ID 1──────▶│     X     │
└───────────┘                    └───────────┘
      │                                │
      │ FreeSWITCH Y doesn't          │
      │ know Call-ID 1!               │
      │ Transfer FAILS                │
```

### Solution: API-Mediated Transfers

1. OpenSIPS intercepts REFER with `replaces` parameter
2. CoreAPI looks up `CallStatus` table for involved switches
3. If two switches involved:
   - **Internal B-Leg**: API returns correct Replaces header for Call-ID 3
   - **External B-Leg**: Bridges the two FreeSWITCHes via private port

**Internal Transfer Flow:**
```xml
<action application="set" data="sip_h_Replaces={New replaces line for Call-ID 3}"/>
<action application="set" data="rmReferDialString={Dialstring of B device}"/>
<action application="javascript" data="applications/DialPlanDestNotFound.js"/>
```

**External Transfer Flow:**
```
1. Store transfer details in Refers table
2. OpenSIPS modifies Refer-To to sip:refer_xxx@127.0.0.1
3. FreeSWITCH Y calls FreeSWITCH X via private profile (port 5070)
4. FreeSWITCH X answers, parks the specified leg, bridges calls
```

---

## Integration with fsxinetd

The dialplan frequently hands off to fsxinetd for complex operations via the socket application:

```xml
<action application="set" data="rmSocketTask=SomeTask::method"/>
<action application="socket" data="${rmpFSXInetdSocket} sync full"/>
```

### Common Socket Tasks

| Task | Purpose |
|------|---------|
| `ApplePushNotificationService::sendAndWaitForRegister` | Mobile push notifications |
| `CallCenter.js` | Call queue processing |
| `ListenIn.lua` | Supervisor monitoring |
| `DialPlanDestNotFound.js` | Dynamic routing lookup |

---

## Configuration Files

### Repository Structure

```
platform-dialplan/
├── files/conf/dialplan/
│   ├── dpPreRouting.xml      # Pre-routing context
│   ├── dpOutbound.xml        # Outbound routing
│   ├── dpPrivate.xml         # Private/internal routing
│   ├── dialPlanRouting.xml   # Main routing include
│   ├── dialPlanFeatures.xml  # Feature codes
│   ├── dpSupport.xml         # Support extensions
│   └── features/             # Feature-specific dialplans
└── config/                   # Salt deployment config
```

### Deployment via Salt

Dialplan files are deployed to FreeSWITCH servers via Salt Stack:

```
/usr/share/freeswitch/conf/dialplan/
├── dpPreRouting.xml
├── dpOutbound.xml
├── dpPrivate.xml
└── [other contexts]
```

---

## Debugging

### Useful fs_cli Commands

```bash
# Show dialplan for a destination
fs_cli -x "xml_locate dialplan default 1001"

# Trace dialplan execution
fs_cli -x "console loglevel debug"
fs_cli -x "sofia loglevel all 9"

# Subscribe to events
/events plain CUSTOM fifo::info

# Show channel variables
fs_cli -x "uuid_dump <uuid>"
```

### Key Log Patterns

```
# Dialplan extension match
EXECUTE sofia/internal/... destination_number=1001

# Context transfer  
TRANSFER XML dpPreRouting -> XML 37 (org context)

# Feature code execution
rmDialledNumberType=FEATURE -> featureVoiceMain XML features
```

---

## Related Documentation

- [Voice Routing Overview](./overview.md)
- [fsxinetd Service](./fsxinetd.md)
- [CDR Processing](./cdr-processing.md)
- [TTS Gateway](./tts-gateway.md)

---

## References

- [Confluence: FreeSWITCH Routing Explained](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/703923805)
- [Confluence: Transfers](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/941391990)
- [Confluence: Call Queue Operation](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/704905945)
- [GitHub: platform-dialplan](https://github.com/redmatter/platform-dialplan)

---

*Documentation created from Confluence ENG Space and GitHub platform-dialplan repository*
