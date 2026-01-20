# Routing Policies

> **Last Updated:** 2026-01-20  
> **Sources:** Confluence (Routing Policy Microservice, Digital Channel Routing Policies, FreeSWITCH Routing Explained), GitHub (natterbox-routing-policies)  
> **Status:** ✅ Complete

---

## Overview

Routing policies are the cornerstone of call handling in the Natterbox platform. They define how inbound and outbound calls, digital messages, and data analytics events are processed through a visual flow-based configuration system.

Administrators create routing policies using a drag-and-drop visual editor (React application) that generates JSON policy definitions. These policies are executed at runtime by the fsxinetd service via Lua scripts on FreeSWITCH.

---

## Policy Types

The platform supports multiple policy types, each designed for specific use cases:

| Policy Type | Description | Entry Points |
|-------------|-------------|--------------|
| **Voice (Call)** | Traditional voice call routing | Inbound Numbers, Extensions, SIP Trunk, Invokable Destinations |
| **Data Analytics** | Event-driven automation | Inbound Messages, Events |
| **Digital** | Omnichannel messaging (SMS, WhatsApp, Chat) | Inbound Digital Address |
| **AI Workforce Call** | AI-powered voice interactions | AI Test Node |
| **AI Workforce Digital** | AI-powered digital interactions | AI Test Node, AI Chat |

### Policy Type Entry Points

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         POLICY ENTRY POINTS                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   VOICE POLICY                     DATA ANALYTICS POLICY                 │
│   ┌─────────────────┐              ┌─────────────────┐                  │
│   │ Inbound Number  │──┐           │ Inbound Message │──┐               │
│   └─────────────────┘  │           └─────────────────┘  │               │
│   ┌─────────────────┐  │           ┌─────────────────┐  │               │
│   │   Extension     │──┼──► Voice  │     Event       │──┼──► DA Policy  │
│   └─────────────────┘  │   Policy  └─────────────────┘  │               │
│   ┌─────────────────┐  │                                │               │
│   │  SIP Trunk      │──┤                                │               │
│   └─────────────────┘  │                                                │
│   ┌─────────────────┐  │           DIGITAL POLICY                       │
│   │   Invokable     │──┘           ┌─────────────────┐                  │
│   │   Destination   │              │ Inbound Digital │──► Digital       │
│   └─────────────────┘              │    Address      │   Policy         │
│                                    └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Policy Components (Nodes)

Routing policies are composed of interconnected nodes that perform specific actions. Each node type has a unique template ID.

### Core Voice Nodes

| Node | ID | Description |
|------|-----|-------------|
| **Inbound Number** | 3 | Entry point for DDI/DID numbers |
| **Extension Number** | 31 | Internal extension entry point (requires AVS license) |
| **Invokable Destination** | 3100000 | Salesforce-invokable entry (requires Contact Centre license) |
| **From SIP Trunk** | 81 | BYOC SIP trunk entry point |
| **Speak** | 5 | Play TTS or audio file to caller |
| **Record Call** | 6 | Start/stop call recording |
| **Action** | 4 | Execute Salesforce action/data lookup |
| **Switchboard** | 9 | Multi-option routing (switch case) |
| **Call Queue** | 49 | Route to queue for agent distribution |
| **Get Info** | 34 | Collect DTMF input from caller |
| **Screen Caller** | 125 | Caller identification/screening |
| **Voice Mail** | 24 | Send to voicemail |
| **To Policy** | 66 | Transfer to another routing policy |
| **Finish** | 23 | End the call |
| **Catch All** | 16 | Default routing for unmatched conditions |

### Digital Channel Nodes

| Node | ID | Description |
|------|-----|-------------|
| **Digital Inbound Address** | 140 | Entry point for digital channels |
| **Digital Connect** | 140 | Connect digital interaction |
| **Digital Action** | 142 | Execute action on digital channel |
| **Assign Records** | 143 | Assign Salesforce records |
| **Digital Finish** | 144 | End digital interaction |

### Data Analytics Nodes

| Node | ID | Description |
|------|-----|-------------|
| **Inbound Message** | 93 | Entry point for data analytics |
| **DA Event** | 93 | Event trigger |
| **DA Action** | 94 | Execute data analytics action |
| **DA Notify** | 98 | Send notification |
| **DA Notify SMS** | 99 | Send SMS notification |
| **DA Finish** | 58 | End data analytics flow |
| **DA Apps** | 121 | Execute custom application |

### AI & Advanced Nodes

| Node | ID | Description |
|------|-----|-------------|
| **AI Test Node** | 111 | AI testing interface |
| **AI Support Chat** | 112 | AI-powered chat assistant |
| **Natterbox AI** | 145 | Natterbox AI integration |
| **Call Natterbox AI** | 146 | Voice AI assistant |
| **Analytics Natterbox AI** | 147 | AI analytics |
| **Omni Channel Flow** | 117 | Salesforce Omni-Channel routing |

### Utility Nodes

| Node | ID | Description |
|------|-----|-------------|
| **Notify** | 47 | Send email/notification |
| **Notify SMS** | 28 | Send SMS |
| **Debug** | 95 | Debug/logging node |
| **Apps** | 118 | Custom application execution |

---

## Policy Architecture

### Visual Editor (Routing Policies UI)

**Repository:** `redmatter/natterbox-routing-policies`

The routing policy editor is a React application embedded in the Natterbox Admin Portal:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ROUTING POLICY VISUAL EDITOR                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐    ┌─────────────────────────────────────────────┐    │
│   │   Toolbox   │    │              Canvas                         │    │
│   │             │    │                                             │    │
│   │ ┌─────────┐ │    │    ┌─────────┐     ┌─────────┐             │    │
│   │ │ Speak   │ │    │    │ Inbound │────►│  Speak  │─────┐       │    │
│   │ └─────────┘ │    │    │ Number  │     │         │     │       │    │
│   │ ┌─────────┐ │    │    └─────────┘     └─────────┘     │       │    │
│   │ │  Queue  │ │    │                                    │       │    │
│   │ └─────────┘ │    │                         ┌──────────▼──────┐│    │
│   │ ┌─────────┐ │    │                         │  Switch Board   ││    │
│   │ │ Action  │ │    │                         │  (Time/Day)     ││    │
│   │ └─────────┘ │    │                         └────┬────────┬───┘│    │
│   │    ...      │    │                              │        │    │    │
│   └─────────────┘    │              ┌───────────────┘        │    │    │
│                      │              ▼                        ▼    │    │
│                      │    ┌─────────────┐          ┌────────────┐ │    │
│                      │    │ Call Queue  │          │  Voicemail │ │    │
│                      │    │ (Sales)     │          │            │ │    │
│                      │    └─────────────┘          └────────────┘ │    │
│                      └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Drag-and-drop node placement
- Visual connection of nodes
- Real-time validation
- Policy versioning
- Import/export functionality
- AI test assistant (feature-flagged)

### Policy Storage & Execution

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Visual Editor  │────►│   Core API      │────►│   PostgreSQL    │
│  (React App)    │     │   (REST)        │     │   (Policy DB)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         │ Policy Lookup
                                                         │
┌─────────────────┐     ┌─────────────────┐     ┌────────▼────────┐
│   FreeSWITCH    │◄───►│    fsxinetd     │────►│   Core API      │
│   (Dialplan)    │ ESL │  (Lua Engine)   │     │   (Runtime)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Flow:**
1. Administrator creates/edits policy in visual editor
2. Policy saved as JSON via Core API to PostgreSQL
3. Inbound call arrives at FreeSWITCH
4. Dialplan triggers fsxinetd via ESL
5. fsxinetd retrieves policy from Core API
6. Lua engine executes policy nodes sequentially
7. Each node action (play audio, route call, etc.) executed on FreeSWITCH

---

## Carrier Routing & LCR

### Least Cost Routing (LCR)

The platform implements carrier failover using a "Ghost Channel" mechanism to work around FreeSWITCH CDR limitations with Enterprise Originate syntax.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LCR CARRIER FAILOVER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Caller                FreeSWITCH          Ghost FS         Carriers   │
│     │                       │                   │                │      │
│     │──INVITE: +441111─────►│                   │                │      │
│     │                       │                   │                │      │
│     │          Policy: Follow Me to +446666, +447777             │      │
│     │                       │                   │                │      │
│     │                       │──siplcr_+446666──►│                │      │
│     │                       │                   │──+446666@bt───►│      │
│     │                       │                   │◄──503 Unavail──│      │
│     │                       │                   │──+446666@ibasis►│     │
│     │                       │                   │◄──200 OK───────│      │
│     │                       │◄──200 OK──────────│                │      │
│     │◄──Connected───────────│                   │                │      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Concepts:**

| Concept | Description |
|---------|-------------|
| **siplcr_ Dialplan** | Private dialplan on port 5070 for carrier routing |
| **Ghost Channel** | Internal channel that handles carrier failover |
| **B Leg** | Original outbound leg from the caller's perspective |
| **C Leg** | Ghost channel to siplcr_ |
| **D Leg** | Actual carrier connection |

### Channel Variables for Tracking

Ghost channel calls set tracking variables for debugging:

| Variable | Description |
|----------|-------------|
| `rmGhostLegConnectedUUID` | UUID of the ghost leg channel connected to carrier |
| `rmOtherLegUUID_<uuid>` | Set on B leg for each C leg launched |
| `rmOtherLegUUID` | Set on C leg pointing to B leg UUID |

---

## Digital Routing Policies

Digital routing policies handle omnichannel interactions (SMS, WhatsApp, Web Chat):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIGITAL ROUTING POLICY FLOW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐                                                      │
│   │   Inbound    │                                                      │
│   │   Digital    │────┬──────────────────────────────────────┐          │
│   │   Address    │    │                                      │          │
│   └──────────────┘    │                                      │          │
│         │             │                                      │          │
│         ▼             │                                      │          │
│   ┌──────────────┐    │    ┌──────────────┐    ┌──────────────┐        │
│   │   Digital    │    │    │   Assign     │    │    Omni      │        │
│   │   Action     │────┼───►│   Records    │───►│   Channel    │        │
│   │              │    │    │              │    │    Flow      │        │
│   └──────────────┘    │    └──────────────┘    └──────────────┘        │
│         │             │                                                 │
│         │             │    ┌──────────────┐                            │
│         │             └───►│   AI Chat    │                            │
│         │                  │   (Bot)      │                            │
│         │                  └──────────────┘                            │
│         ▼                                                               │
│   ┌──────────────┐                                                     │
│   │   Digital    │                                                     │
│   │   Finish     │                                                     │
│   └──────────────┘                                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Digital Policy Capabilities:**
- Route incoming messages to appropriate handlers
- Integrate with Salesforce Omni-Channel for agent assignment
- AI-powered chatbot responses
- Record assignment for case/lead creation
- Channel-specific routing logic

---

## Policy Configuration Best Practices

### Inbound Policy Structure

1. **Entry Point** - Define how calls enter (DDI, Extension, SIP Trunk)
2. **Initial Processing** - Play greeting, collect caller info
3. **Routing Logic** - Time-based, caller ID, IVR selection
4. **Queue/Connect** - Route to queue, user, or external number
5. **Fallback** - Voicemail, callback, or overflow handling

### Example: Business Hours Policy

```
Inbound Number (+44 20 1234 5678)
    │
    ▼
Speak ("Welcome to Acme Corp")
    │
    ▼
Switchboard (Time of Day)
    ├─── Mon-Fri 9-17 ──► Call Queue (Sales)
    │                         │
    │                         ├─── Agent Available ──► Connect
    │                         └─── No Agent ──► Voicemail
    │
    └─── Outside Hours ──► Speak (After hours message)
                               │
                               ▼
                          Voicemail
```

### Non-Call Policies

Every voice policy can optionally chain to a "Non-Call Policy" (Data Analytics type) that executes when the call completes. This enables:
- Post-call surveys
- CRM updates
- Notification workflows
- Analytics events

---

## Microservice Integration

### Routing Policy Microservice

The Routing Policy Microservice provides runtime policy execution services:

**Key Endpoints:**
- Policy retrieval by ID
- Policy validation
- Runtime variable resolution
- Node execution APIs

**Integration Points:**
- Core API (policy storage)
- fsxinetd (runtime execution)
- Salesforce (data actions)
- Omniservice (digital channels)

---

## Key Repositories

| Repository | Description |
|------------|-------------|
| `natterbox-routing-policies` | React visual editor application |
| `platform-fsxinetdsocket` | Policy execution engine |
| `natterbox-avsapp-scripts` | Lua scripts for policy nodes |
| `platform-fscore` | Core FreeSWITCH scripts |

---

## Feature Flags

Some policy features are controlled by feature flags:

| Flag | Feature |
|------|---------|
| `conversationalAlPolicyTestAssistantEnabled` | AI Test Node in policy editor |
| `conversationalAiChatAssistantEnabled` | AI Chat node for digital policies |

---

## Related Documentation

- [Voice Routing Overview](./overview.md)
- [fsxinetd Service Details](./fsxinetd.md)
- [PBX Component View](./pbx.md)
- [Digital Channels](../omnichannel/overview.md)

---

## Confluence References

- [Routing Policy Microservice](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/1603895353)
- [Digital Channel Routing Policies](https://natterbox.atlassian.net/wiki/spaces/PROD/pages/1570471940)
- [FreeSWITCH Routing Explained](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/703923805)
- [Item: Start (Policy Entry Points)](https://natterbox.atlassian.net/wiki/spaces/NKB/pages/406323450)

---

*Documentation created from Confluence Engineering Space and GitHub repository analysis*
