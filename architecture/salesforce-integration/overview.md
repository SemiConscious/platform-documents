# Salesforce Integration Architecture

> **Last Updated:** 2026-01-19  
> **Source:** Repository analysis, Document360, SCV Connector docs  
> **Status:** ✅ Complete

---

## Overview

Natterbox integrates deeply with Salesforce to provide enterprise telephony within the CRM. The integration is delivered through multiple components:

1. **AVS Package** - Managed Salesforce package providing CTI, routing policies, and call management
2. **SCV BYOT Connector** - Service Cloud Voice "Bring Your Own Telephony" integration
3. **Data Connectors** - Real-time Salesforce data access during call routing
4. **SF PBX Proxy** - Backend proxy for Salesforce API interactions

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SALESFORCE ORG                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                    AVS Package (Managed)                                 │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │    CTI      │  │  Routing    │  │   Custom    │  │  Lightning  │    │  │
│   │  │  Adapter    │  │  Policies   │  │  Objects    │  │ Components  │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                    SCV BYOT Connector                                    │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │  │
│   │  │  Omni-      │  │   Voice     │  │   Agent     │                     │  │
│   │  │  Channel    │  │   Call      │  │   State     │                     │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘                     │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       │ REST/WebSocket
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────────┐
│                         NATTERBOX PLATFORM                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                       Integration Layer                                  │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │  SF PBX     │  │   Service   │  │   Core      │  │   Data      │    │  │
│   │  │   Proxy     │  │   Gateway   │  │   API       │  │ Connectors  │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                      Voice Routing                                       │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │  │
│   │  │  FreeSWITCH │  │  fsxinetd   │  │  Lua        │                     │  │
│   │  │    PBX      │  │             │  │  Scripts    │                     │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘                     │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. AVS Package (Natterbox Advanced Voice Services)

**Repository:** `redmatter/natterbox-avs-sfdx`

The AVS package is a managed Salesforce package distributed via AppExchange that provides:

| Component | Description |
|-----------|-------------|
| **CTI Adapter** | Computer Telephony Integration for click-to-dial, screen pop |
| **Routing Policies** | Visual flow builder for call routing logic |
| **Custom Objects** | Call history, configuration, user settings |
| **Lightning Components** | UI components for call control, dialpad, etc. |
| **Apex Classes** | Backend logic for Salesforce operations |
| **Connected Apps** | OAuth configuration for platform authentication |

#### Package Contents

```
force-app/main/default/
├── applications/          # Salesforce apps
├── aura/                  # Aura components (legacy)
├── lwc/                   # Lightning Web Components
├── classes/               # Apex classes
├── triggers/              # Apex triggers
├── objects/               # Custom objects and fields
├── flows/                 # Flow definitions
├── callCenters/           # Call center configurations
├── permissionsets/        # Permission sets
├── layouts/               # Page layouts
├── flexipages/            # Lightning pages
└── staticresources/       # JS/CSS resources
```

#### Deployment

- Package is deployed via SFDX
- Versioned releases (currently v1.169+)
- CI/CD via GitHub Actions with `github-action-apex-build`

---

### 2. SCV BYOT Connector

**Repository:** `redmatter/platform-scv-byot-connector`

Service Cloud Voice "Bring Your Own Telephony" connector enables Natterbox telephony within Salesforce's native Service Cloud Voice experience.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Salesforce Service Console                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Omni-Channel Widget                            ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │           SCV BYOT Connector (JavaScript)               │││
│  │  │  • Telephony state management                           │││
│  │  │  • Voice Call object integration                        │││
│  │  │  • Agent presence                                       │││
│  │  │  • Call controls (answer, hold, transfer, etc.)         │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────┬──────────────────────────────────┘
                               │ WebSocket/REST
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Natterbox Platform                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Voice Routing (FreeSWITCH)                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### Key Features

| Feature | Description |
|---------|-------------|
| **Omni-Channel Integration** | Unified agent interface for all channels |
| **Voice Call Object** | Native Salesforce call tracking |
| **Telephony Controls** | Answer, hold, mute, transfer, conference |
| **Screen Pop** | Automatic record matching on inbound calls |
| **Call Recording** | Integrated with Salesforce storage |
| **Real-time Transcription** | Live transcription display |

#### Development Setup

```bash
# Clone repository
git clone git@github.com:redmatter/platform-scv-byot-connector.git

# Install dependencies
cd connector
npm install --unsafe-perm

# Start development server
npm start

# Add to hosts file
echo "127.0.0.1 cti.io.tools" >> /etc/hosts

# Access at https://cti.io.tools:3002/
```

#### Configuration

In Salesforce Custom Settings → Natterbox Call Center:
- **CTI File Host**: URL of connector bundle
- Update to local dev server for testing

---

### 3. Data Connectors

Data Connectors enable real-time Salesforce data access during call routing.

#### Modern Path (Direct REST)

```
fsxinetd → Salesforce REST API → Salesforce Objects
```

Used by modern orgs with direct API access configured.

#### Legacy Path (Service Gateway)

```
fsxinetd → service-gateway → Salesforce SOAP API → Salesforce Objects
```

Used by legacy orgs with SOAP-based data connector configuration.

#### Use Cases

- Look up caller information during inbound calls
- Screen pop with relevant records
- Update Salesforce records during/after calls
- Access custom objects for routing decisions
- Retrieve queue configurations

---

### 4. SF PBX Proxy

**Repository:** `redmatter/sfpbxproxy`

Backend proxy service handling Salesforce API interactions from the platform.

| Function | Description |
|----------|-------------|
| **Authentication** | OAuth token management |
| **API Proxying** | REST/SOAP request forwarding |
| **Rate Limiting** | Salesforce API governance compliance |
| **Caching** | Reduce API calls for frequently accessed data |

---

## Integration Patterns

### CTI Integration Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Salesforce │     │   CTI       │     │  Natterbox  │
│   Console   │     │  Adapter    │     │  Platform   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │ Click to Dial     │                   │
       │──────────────────►│                   │
       │                   │ Dial Request      │
       │                   │──────────────────►│
       │                   │                   │ Place Call
       │                   │   Call Connected  │
       │                   │◄──────────────────│
       │ Update UI         │                   │
       │◄──────────────────│                   │
       │                   │                   │
```

### Inbound Call with Screen Pop

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Carrier   │     │  Natterbox  │     │ Salesforce  │     │  SF Agent   │
│             │     │  Platform   │     │    Org      │     │  Console    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ Inbound Call      │                   │                   │
       │──────────────────►│                   │                   │
       │                   │ Query Contact     │                   │
       │                   │──────────────────►│                   │
       │                   │ Contact Data      │                   │
       │                   │◄──────────────────│                   │
       │                   │ Route Call + Data │                   │
       │                   │──────────────────────────────────────►│
       │                   │                   │  Screen Pop       │
       │                   │                   │  Show Contact     │
       │                   │                   │                   │
```

---

## Key Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| `natterbox-avs-sfdx` | AVS managed package (SFDX) | Apex/LWC |
| `platform-scv-byot-connector` | SCV BYOT connector | JavaScript |
| `natterbox-scv-package` | SCV package components | Apex |
| `sfpbxproxy` | SF PBX proxy service | PHP |
| `natterbox-nbcc` | Natterbox Call Centre package | Apex |
| `sf-internal-delta-connector` | Delta API 2GP package | Apex |
| `natterbox-avsapp-scripts` | AVS Lua routing scripts | Lua |

---

## Terraform Modules

| Module | Description |
|--------|-------------|
| `aws-terraform-nexus-sfpbxproxy` | SF PBX Proxy infrastructure |
| `terraform-terraform-scv-app` | SCV app deployment |

---

## Authentication & Security

### OAuth Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Natterbox  │     │  Salesforce │     │    User     │
│  Platform   │     │    OAuth    │     │  Browser    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │ Auth Request      │                   │
       │──────────────────►│                   │
       │                   │ Login Page        │
       │                   │──────────────────►│
       │                   │                   │ Credentials
       │                   │◄──────────────────│
       │                   │ Auth Code         │
       │◄──────────────────│                   │
       │ Token Exchange    │                   │
       │──────────────────►│                   │
       │ Access Token      │                   │
       │◄──────────────────│                   │
       │                   │                   │
```

### Connected Apps

The AVS package includes Connected Apps for:
- Platform authentication
- API access
- Single Sign-On

---

## Voice Call Object (SCV)

When using Service Cloud Voice, calls are tracked in the standard Voice Call object:

| Field | Description |
|-------|-------------|
| `CallType` | Inbound, Outbound, Internal |
| `CallDuration` | Length of call in seconds |
| `FromPhoneNumber` | Caller phone number |
| `ToPhoneNumber` | Called phone number |
| `RelatedRecordId` | Associated Contact/Lead/Account |
| `OwnerId` | Agent who handled the call |
| `CallStartDateTime` | When call started |
| `CallEndDateTime` | When call ended |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CTI not loading | Connector bundle URL incorrect | Check CTI File Host setting |
| Screen pop not working | Contact not found | Verify phone number format |
| Call recording missing | Storage permissions | Check Salesforce storage config |
| Data connector timeout | Salesforce API limits | Implement caching, check limits |

### Debug Logs

- Salesforce: Setup → Debug Logs
- Connector: Browser DevTools Console
- Platform: CloudWatch logs for sfpbxproxy

---

## Related Documentation

- [Voice Routing Overview](../voice-routing/overview.md)
- [fsxinetd Service](../voice-routing/fsxinetd.md)
- [Document360: SCV Introduction](https://docs.natterbox.com/docs/en/service-cloud-voice-intro)
- [Document360: Installation Guide](https://docs.natterbox.com/docs/en/natterbox-installation-guide)

---

*Documentation compiled from repository analysis and Document360*
