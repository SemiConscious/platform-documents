# FreedomCTI Client Overview

[![Platform](https://img.shields.io/badge/platform-Salesforce%20Lightning-00A1E0?style=flat-square&logo=salesforce)](https://www.salesforce.com/)
[![Integration](https://img.shields.io/badge/integration-CTI-green?style=flat-square)]()
[![WebSocket](https://img.shields.io/badge/realtime-WebSocket-blue?style=flat-square)]()
[![Testing](https://img.shields.io/badge/e2e-Cypress-17202C?style=flat-square&logo=cypress)]()

---

## Introduction

**platform-cti-client** is a browser-based Computer Telephony Integration (CTI) application designed to seamlessly integrate with Salesforce Lightning. This documentation serves as the central entry point for developers working with FreedomCTI, providing architecture guidance, setup instructions, and navigation to detailed technical documentation.

FreedomCTI empowers Salesforce users with real-time call management capabilities directly within their CRM workflow, eliminating context switching and improving agent productivity.

---

## What is FreedomCTI?

FreedomCTI is a sophisticated CTI client application that bridges telephony systems with Salesforce CRM. It operates as an embedded iframe within the Salesforce Lightning interface, providing agents with comprehensive call control and management features without leaving their primary workspace.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Real-time Call Management** | Handle incoming/outgoing calls, transfers, holds, and conferencing |
| **WebSocket Communication** | Live event streaming for instant call state updates |
| **Call Logging** | Automatic and manual call activity logging to Salesforce records |
| **Voicemail Management** | Listen, manage, and respond to voicemails directly in Salesforce |
| **Call History** | Comprehensive call records with search and filtering |
| **Multi-Environment Support** | Seamless deployment across dev, QA, stage, and production |

### Key Benefits

- **Zero Context Switching**: Agents stay within Salesforce for all telephony operations
- **Real-time Updates**: WebSocket-powered instant notifications and state changes
- **CRM Integration**: Automatic association of calls with Salesforce records
- **Scalable Architecture**: Redux-based state management for predictable behavior
- **Quality Assurance**: Comprehensive Cypress end-to-end testing suite

---

## Architecture Overview

FreedomCTI follows a modern frontend architecture optimized for real-time communication and Salesforce integration.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SALESFORCE LIGHTNING                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Lightning Container                     │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              FreedomCTI (iframe)                     │  │  │
│  │  │                                                      │  │  │
│  │  │  ┌──────────────┐    ┌──────────────────────────┐   │  │  │
│  │  │  │   UI Layer   │    │    Redux Store           │   │  │  │
│  │  │  │  Components  │◄──►│  - Call State            │   │  │  │
│  │  │  │  - Dialpad   │    │  - User Session          │   │  │  │
│  │  │  │  - Call Bar  │    │  - Voicemail Queue       │   │  │  │
│  │  │  │  - History   │    │  - Configuration         │   │  │  │
│  │  │  └──────────────┘    └───────────┬──────────────┘   │  │  │
│  │  │                                  │                   │  │  │
│  │  │                      ┌───────────▼──────────────┐   │  │  │
│  │  │                      │   Redux Middleware       │   │  │  │
│  │  │                      │   - WebSocket Handler    │   │  │  │
│  │  │                      │   - API Integration      │   │  │  │
│  │  │                      │   - Event Processing     │   │  │  │
│  │  │                      └───────────┬──────────────┘   │  │  │
│  │  └──────────────────────────────────┼──────────────────┘  │  │
│  └─────────────────────────────────────┼─────────────────────┘  │
└────────────────────────────────────────┼────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
           ┌────────▼────────┐                    ┌───────────▼───────────┐
           │  WebSocket API  │                    │      REST API         │
           │  (Real-time)    │                    │  (CRUD Operations)    │
           │                 │                    │                       │
           │  - Call Events  │                    │  - Call Logs          │
           │  - Status       │                    │  - Voicemail          │
           │  - Presence     │                    │  - Configuration      │
           └─────────────────┘                    └───────────────────────┘
```

### Component Breakdown

| Layer | Responsibility | Technologies |
|-------|---------------|--------------|
| **UI Layer** | User interface components and interactions | React Components, CSS |
| **State Management** | Centralized application state | Redux, Redux Middleware |
| **Communication** | Real-time and REST API communication | WebSocket, Fetch API |
| **Integration** | Salesforce Lightning container messaging | Lightning Message Service |

### Data Flow

1. **User Action** → UI Component triggers action
2. **Redux Dispatch** → Action processed by middleware
3. **API/WebSocket** → Communication with backend services
4. **State Update** → Redux store updated with response
5. **UI Re-render** → Components reflect new state

---

## Quick Start

Get FreedomCTI running in your development environment with these steps.

### Prerequisites

Before starting, ensure you have the following:

- [ ] Access to a Salesforce Developer or Sandbox org
- [ ] CTI backend services deployed and accessible
- [ ] Valid environment configuration credentials
- [ ] Modern web browser (Chrome, Firefox, Edge)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd platform-cti-client
```

### Step 2: Configure Environment

Create your environment configuration file based on your target environment:

```bash
# Copy the appropriate environment template
cp config/env.template.json config/env.local.json
```

Edit `config/env.local.json` with your environment-specific values:

```json
{
  "environment": "development",
  "apiBaseUrl": "https://api.dev.example.com",
  "websocketUrl": "wss://ws.dev.example.com",
  "salesforceOrgId": "YOUR_ORG_ID",
  "featureFlags": {
    "voicemailEnabled": true,
    "callRecordingEnabled": true
  }
}
```

### Step 3: Build the Application

Build commands vary by environment:

```bash
# Development build
make build-dev

# QA build
make build-qa

# Staging build
make build-stage

# Production build
make build-prod
```

### Step 4: Deploy to Salesforce

Upload the built assets to your Salesforce org's static resources:

```bash
# Package for Salesforce deployment
make package

# Deploy using Salesforce CLI (if configured)
sfdx force:source:deploy -p force-app/main/default/staticresources
```

### Step 5: Verify Installation

1. Navigate to Salesforce Lightning
2. Open the utility bar or designated CTI component area
3. Verify FreedomCTI loads within the iframe
4. Check browser console for connection status messages

---

## Environment Setup

FreedomCTI supports multiple deployment environments, each with specific configurations.

### Environment Matrix

| Environment | Purpose | WebSocket URL | API URL |
|-------------|---------|---------------|---------|
| **Development** | Local development and testing | `wss://ws.dev.cti.example.com` | `https://api.dev.cti.example.com` |
| **QA** | Quality assurance testing | `wss://ws.qa.cti.example.com` | `https://api.qa.cti.example.com` |
| **Stage** | Pre-production validation | `wss://ws.stage.cti.example.com` | `https://api.stage.cti.example.com` |
| **Production** | Live user environment | `wss://ws.cti.example.com` | `https://api.cti.example.com` |

### Configuration Variables

Key configuration parameters for each environment:

```javascript
// Example configuration structure
const config = {
  // API Configuration
  apiBaseUrl: 'https://api.example.com',
  apiTimeout: 30000,
  
  // WebSocket Configuration
  websocketUrl: 'wss://ws.example.com',
  websocketReconnectInterval: 5000,
  websocketMaxRetries: 10,
  
  // Salesforce Integration
  salesforceOrgId: '00Dxx0000000000',
  lightningContainerOrigin: 'https://your-org.lightning.force.com',
  
  // Feature Flags
  features: {
    voicemailEnabled: true,
    callRecordingEnabled: true,
    conferenceCallEnabled: false
  },
  
  // Logging
  logLevel: 'debug', // debug | info | warn | error
  sentryDsn: 'https://sentry.example.com/project'
};
```

### Running End-to-End Tests

FreedomCTI uses Cypress for comprehensive end-to-end testing:

```bash
# Open Cypress Test Runner (interactive mode)
npx cypress open

# Run all tests headlessly
npx cypress run

# Run specific test suite
npx cypress run --spec "cypress/e2e/call-management/*.cy.js"

# Run tests against specific environment
CYPRESS_BASE_URL=https://qa.example.com npx cypress run
```

---

## Documentation Index

Navigate to detailed documentation for specific topics:

### Architecture & Design

| Document | Description |
|----------|-------------|
| [Application Architecture](docs/architecture.md) | Detailed system design, component hierarchy, and data flow patterns |
| [WebSocket Communication Guide](docs/websocket-guide.md) | Real-time communication protocols, event handling, and reconnection strategies |

### Configuration & Setup

| Document | Description |
|----------|-------------|
| [Configuration Guide](docs/configuration.md) | Complete configuration reference for all environments |
| [Salesforce Integration Guide](docs/salesforce-integration.md) | Lightning container setup, messaging, and deployment |

### API & Data

| Document | Description |
|----------|-------------|
| [API Reference Overview](api/README.md) | REST API endpoints, authentication, and request/response formats |
| [Data Models Overview](models/README.md) | 71 data models with schemas and relationships |

### Quick Reference

```
docs/
├── architecture.md          # System architecture deep-dive
├── configuration.md         # Environment configuration
├── salesforce-integration.md # Salesforce-specific setup
└── websocket-guide.md       # Real-time communication

api/
└── README.md               # API endpoint documentation

models/
└── README.md               # Data model schemas (71 models)
```

---

## CTI 2.0 vs FreedomCTI

Understanding the evolution from CTI 2.0 to FreedomCTI helps teams plan migrations and understand feature differences.

### Feature Comparison

| Feature | CTI 2.0 (Legacy) | FreedomCTI |
|---------|------------------|------------|
| **Platform** | Desktop application | Browser-based (iframe) |
| **Salesforce Integration** | External popup | Embedded Lightning component |
| **Real-time Updates** | Polling-based | WebSocket-based |
| **State Management** | Local storage | Redux store |
| **Multi-tab Support** | Limited | Full support with sync |
| **Offline Capability** | Partial | Queue-based with sync |
| **Testing** | Manual | Cypress automation |
| **Deployment** | MSI installer | Static resource upload |

### Migration Considerations

When migrating from CTI 2.0 to FreedomCTI:

1. **User Training**: Interface differences require agent familiarization
2. **Configuration Migration**: Settings must be reconfigured in new format
3. **Integration Updates**: Custom integrations need API endpoint updates
4. **Browser Requirements**: Ensure compatible browsers are available
5. **Network Configuration**: WebSocket connections may require firewall updates

### Why FreedomCTI?

| Advantage | Impact |
|-----------|--------|
| **No Installation** | Zero deployment to agent workstations |
| **Instant Updates** | Changes deploy immediately via static resources |
| **Better UX** | Seamless Salesforce integration reduces friction |
| **Real-time** | WebSocket provides sub-second event delivery |
| **Maintainability** | Modern architecture simplifies development |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| **iframe not loading** | CSP restrictions | Verify Salesforce trusted URLs |
| **WebSocket disconnects** | Network instability | Check reconnection logs, verify firewall |
| **Call events delayed** | API throttling | Review rate limits, optimize polling |
| **State not persisting** | Redux middleware error | Check browser console for errors |

### Debug Mode

Enable verbose logging for troubleshooting:

```javascript
// In browser console
localStorage.setItem('freedomcti_debug', 'true');
location.reload();
```

### Getting Help

- Review the [Architecture Documentation](docs/architecture.md) for system understanding
- Check [WebSocket Guide](docs/websocket-guide.md) for connection issues
- Consult [Configuration Guide](docs/configuration.md) for environment setup

---

## Contributing

1. Review the [Application Architecture](docs/architecture.md)
2. Follow established patterns in the codebase
3. Include Cypress tests for new features
4. Update relevant documentation

---

*For detailed API documentation, see the [API Reference Overview](api/README.md). For data model schemas, refer to [Data Models Overview](models/README.md).*