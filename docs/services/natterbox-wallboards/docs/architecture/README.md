# Natterbox Wallboards

[![Frontend](https://img.shields.io/badge/type-frontend-blue.svg)](https://github.com/)
[![ReactJS](https://img.shields.io/badge/framework-ReactJS-61DAFB.svg?logo=react)](https://reactjs.org/)
[![Auth0](https://img.shields.io/badge/auth-Auth0-EB5424.svg?logo=auth0)](https://auth0.com/)
[![Salesforce](https://img.shields.io/badge/platform-Salesforce-00A1E0.svg?logo=salesforce)](https://www.salesforce.com/)

A ReactJS-based dashboard application for displaying real-time call center metrics, agent statuses, and queue information. Designed specifically for seamless integration within Salesforce Visualforce iframes, Natterbox Wallboards provides call center managers and supervisors with powerful visualization tools to monitor and optimize contact center operations.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Application Architecture](#application-architecture)
  - [Application Structure](#application-structure)
  - [Component Hierarchy](#component-hierarchy)
  - [State Management (Redux Store)](#state-management-redux-store)
  - [Authentication Flow](#authentication-flow)
  - [Salesforce Integration](#salesforce-integration)
  - [Build Pipeline](#build-pipeline)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

Natterbox Wallboards transforms raw call center data into actionable visual intelligence. The application renders real-time metrics through configurable dashboard layouts, enabling supervisors to:

- Monitor agent availability and status in real-time
- Track queue depths and wait times
- Visualize call volume patterns and trends
- Manage agent group assignments dynamically

The application is architected as a **single-bundle deployment** with Base64 embedded resources, ensuring reliable delivery within the constraints of Salesforce Visualforce iframe environments.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Agent Monitoring** | Live status updates for all agents including availability, call state, and duration |
| **Queue Visualization** | Visual representation of queue depths, wait times, and service levels |
| **Configurable Layouts** | Drag-and-drop wallboard configuration with customizable widgets |
| **Agent Group Management** | Dynamic grouping and filtering of agents by skill, team, or custom criteria |
| **Auth0 Integration** | Secure authentication with enterprise SSO support |
| **Salesforce Native** | Purpose-built for Visualforce iframe embedding |
| **Single-Bundle Deploy** | Self-contained deployment with embedded assets |

---

## Application Architecture

### Application Structure

The Natterbox Wallboards application follows a modular architecture optimized for maintainability and performance within Salesforce environments:

```
natterbox-wallboards/
├── src/
│   ├── components/           # React UI components
│   │   ├── common/          # Shared/reusable components
│   │   ├── widgets/         # Wallboard widget components
│   │   ├── layouts/         # Layout container components
│   │   └── auth/            # Authentication components
│   ├── containers/          # Redux-connected containers
│   ├── store/               # Redux store configuration
│   │   ├── actions/         # Action creators
│   │   ├── reducers/        # State reducers
│   │   ├── selectors/       # Memoized selectors
│   │   └── middleware/      # Custom middleware
│   ├── services/            # API and external service integrations
│   │   ├── api/             # REST API clients
│   │   ├── websocket/       # Real-time data connections
│   │   └── salesforce/      # Salesforce-specific integrations
│   ├── utils/               # Utility functions and helpers
│   ├── hooks/               # Custom React hooks
│   ├── styles/              # Global styles and themes
│   └── config/              # Application configuration
├── public/                   # Static assets
├── build/                    # Production build output
└── scripts/                  # Build and deployment scripts
```

### Component Hierarchy

The application follows a hierarchical component structure designed for optimal rendering performance:

```
<App>
├── <AuthProvider>                    # Auth0 authentication context
│   ├── <SalesforceConnector>         # SF iframe communication layer
│   │   ├── <WallboardRouter>         # Route management
│   │   │   ├── <DashboardLayout>     # Main dashboard container
│   │   │   │   ├── <Header>          # Navigation and user info
│   │   │   │   ├── <WidgetGrid>      # Configurable widget layout
│   │   │   │   │   ├── <AgentStatusWidget>
│   │   │   │   │   ├── <QueueMetricsWidget>
│   │   │   │   │   ├── <CallVolumeWidget>
│   │   │   │   │   └── <ServiceLevelWidget>
│   │   │   │   └── <Sidebar>         # Configuration panel
│   │   │   └── <ConfigurationView>   # Wallboard setup screens
│   │   └── <NotificationLayer>       # Toast/alert overlays
│   └── <ErrorBoundary>               # Global error handling
└── <ReduxProvider>                   # State management wrapper
```

### State Management (Redux Store)

The Redux store is structured into distinct slices for optimal performance and maintainability:

```javascript
// Store Structure
{
  auth: {
    user: Object,              // Current authenticated user
    token: String,             // Auth0 JWT token
    isAuthenticated: Boolean,
    isLoading: Boolean,
    error: String | null
  },
  
  agents: {
    byId: Object,              // Normalized agent entities
    allIds: Array,             // Agent ID list
    statusFilter: String,      // Current filter state
    lastUpdated: Timestamp
  },
  
  queues: {
    byId: Object,              // Normalized queue entities
    allIds: Array,
    metrics: Object,           // Aggregated queue metrics
    realTimeData: Object       // WebSocket stream data
  },
  
  wallboard: {
    layout: Object,            // Current layout configuration
    widgets: Array,            // Active widget definitions
    theme: String,             // Visual theme selection
    refreshInterval: Number
  },
  
  ui: {
    sidebarOpen: Boolean,
    activeModal: String | null,
    notifications: Array,
    isFullscreen: Boolean
  }
}
```

**Selector Pattern Example:**

```javascript
// selectors/agentSelectors.js
import { createSelector } from 'reselect';

const getAgentsById = (state) => state.agents.byId;
const getAgentIds = (state) => state.agents.allIds;
const getStatusFilter = (state) => state.agents.statusFilter;

export const getFilteredAgents = createSelector(
  [getAgentsById, getAgentIds, getStatusFilter],
  (byId, allIds, filter) => {
    const agents = allIds.map(id => byId[id]);
    if (!filter || filter === 'all') return agents;
    return agents.filter(agent => agent.status === filter);
  }
);

export const getAgentStatusCounts = createSelector(
  [getAgentsById, getAgentIds],
  (byId, allIds) => {
    return allIds.reduce((counts, id) => {
      const status = byId[id].status;
      counts[status] = (counts[status] || 0) + 1;
      return counts;
    }, {});
  }
);
```

### Authentication Flow

The application implements Auth0 authentication with Salesforce session coordination:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐ │
│  │Salesforce│───▶│ Wallboard │───▶│  Auth0   │───▶│   API    │ │
│  │  User    │    │   App     │    │  Login   │    │  Server  │ │
│  └──────────┘    └───────────┘    └──────────┘    └──────────┘ │
│       │               │                │               │        │
│       │  1. Load in   │                │               │        │
│       │   iframe      │                │               │        │
│       │──────────────▶│                │               │        │
│       │               │ 2. Check       │               │        │
│       │               │   session      │               │        │
│       │               │───────────────▶│               │        │
│       │               │                │ 3. Silent     │        │
│       │               │                │   auth or     │        │
│       │               │                │   redirect    │        │
│       │               │◀───────────────│               │        │
│       │               │ 4. JWT Token   │               │        │
│       │               │────────────────────────────────▶│       │
│       │               │               5. Validate &    │        │
│       │               │◀────────────────────────────────│       │
│       │               │               return data      │        │
│       │◀──────────────│                                │        │
│       │  6. Render    │                                │        │
│       │   dashboard   │                                │        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Auth Configuration:**

```javascript
// config/auth.config.js
export const authConfig = {
  domain: process.env.REACT_APP_AUTH0_DOMAIN,
  clientId: process.env.REACT_APP_AUTH0_CLIENT_ID,
  audience: process.env.REACT_APP_AUTH0_AUDIENCE,
  redirectUri: window.location.origin,
  scope: 'openid profile email',
  
  // Salesforce iframe-specific settings
  useRefreshTokens: true,
  cacheLocation: 'localstorage',
  
  // Silent authentication for iframe contexts
  authorizationParams: {
    prompt: 'none'
  }
};
```

### Salesforce Integration

The application communicates with its Salesforce host through a dedicated message-passing interface:

```javascript
// services/salesforce/SalesforceConnector.js
class SalesforceConnector {
  constructor() {
    this.origin = null;
    this.messageHandlers = new Map();
    this.initializeListener();
  }

  initializeListener() {
    window.addEventListener('message', (event) => {
      // Validate origin for security
      if (!this.isValidOrigin(event.origin)) return;
      
      this.origin = event.origin;
      const { type, payload } = event.data;
      
      if (this.messageHandlers.has(type)) {
        this.messageHandlers.get(type)(payload);
      }
    });
  }

  postMessage(type, payload) {
    if (window.parent && this.origin) {
      window.parent.postMessage({ type, payload }, this.origin);
    }
  }

  onMessage(type, handler) {
    this.messageHandlers.set(type, handler);
  }

  // Request Salesforce session context
  requestSessionContext() {
    this.postMessage('REQUEST_SESSION_CONTEXT', {});
  }

  // Navigate to Salesforce record
  navigateToRecord(recordId) {
    this.postMessage('NAVIGATE_TO_RECORD', { recordId });
  }
}

export default new SalesforceConnector();
```

**Visualforce Page Template:**

```html
<apex:page showHeader="false" sidebar="false" standardStylesheets="false">
  <apex:includeScript value="{!$Resource.NatterboxWallboardBundle}"/>
  
  <div id="natterbox-wallboard-root"></div>
  
  <script>
    // Initialize wallboard with Salesforce context
    window.NatterboxWallboard.init({
      orgId: '{!$Organization.Id}',
      userId: '{!$User.Id}',
      sessionId: '{!$Api.Session_ID}'
    });
  </script>
</apex:page>
```

### Build Pipeline

The build process produces a single, self-contained bundle suitable for Salesforce Static Resource deployment:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Build Pipeline                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐              │
│  │   Source   │──▶│  Webpack   │──▶│   Bundle   │              │
│  │   Files    │   │   Build    │   │  Output    │              │
│  └────────────┘   └────────────┘   └────────────┘              │
│        │                │                │                      │
│        ▼                ▼                ▼                      │
│  • React JSX      • Transpile      • Single JS file            │
│  • SCSS/CSS       • Minify         • Embedded CSS              │
│  • Assets         • Tree-shake     • Base64 assets             │
│  • TypeScript     • Code-split     • Source maps               │
│                                                                 │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐              │
│  │  Bundle    │──▶│  Package   │──▶│  Deploy    │              │
│  │  Output    │   │  as ZIP    │   │  to SF     │              │
│  └────────────┘   └────────────┘   └────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Build Commands:**

```bash
# Development build with hot-reload
npm run start

# Production build with optimization
npm run build

# Create Salesforce-ready static resource
npm run build:salesforce

# Run test suite
npm run test

# Lint and format check
npm run lint
```

**Webpack Configuration Highlights:**

```javascript
// webpack.config.js (excerpt)
module.exports = {
  output: {
    filename: 'natterbox-wallboard.bundle.js',
    library: 'NatterboxWallboard',
    libraryTarget: 'umd'
  },
  
  module: {
    rules: [
      {
        test: /\.(png|jpg|gif|svg)$/,
        type: 'asset/inline'  // Base64 embed all images
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/,
        type: 'asset/inline'  // Base64 embed fonts
      }
    ]
  },
  
  optimization: {
    minimize: true,
    usedExports: true
  }
};
```

---

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm 8.x or yarn 1.22.x
- Salesforce org with Visualforce enabled
- Auth0 tenant configured for your organization

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/natterbox/natterbox-wallboards.git
   cd natterbox-wallboards
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your configuration:
   ```env
   REACT_APP_AUTH0_DOMAIN=your-tenant.auth0.com
   REACT_APP_AUTH0_CLIENT_ID=your-client-id
   REACT_APP_AUTH0_AUDIENCE=https://api.natterbox.com
   REACT_APP_API_BASE_URL=https://api.natterbox.com/v1
   ```

4. **Start development server:**
   ```bash
   npm run start
   ```

5. **Build for production:**
   ```bash
   npm run build:salesforce
   ```

---

## API Endpoints

The application interacts with 6 primary API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | Retrieve all agent statuses |
| `/agents/{id}` | GET | Get specific agent details |
| `/queues` | GET | List all queue metrics |
| `/queues/{id}/calls` | GET | Get calls in specific queue |
| `/wallboards` | GET/POST | Manage wallboard configurations |
| `/groups` | GET/POST | Agent group management |

---

## Data Models

The application utilizes **74 data models** covering agents, queues, calls, configurations, and metrics. For comprehensive model documentation, see the [Data Models Overview](docs/models/README.md).

---

## Documentation

| Document | Description |
|----------|-------------|
| [Data Models Overview](docs/models/README.md) | Complete reference for all 74 data models |
| [Authentication Configuration](docs/configuration/auth.md) | Auth0 setup and configuration guide |

---

## Troubleshooting

### Common Issues

**Issue: Blank screen in Salesforce iframe**
- Verify Auth0 callback URLs include Salesforce domain
- Check browser console for CSP violations
- Ensure Static Resource is deployed correctly

**Issue: Authentication loop**
- Clear localStorage and cookies
- Verify Auth0 tenant configuration
- Check for popup blockers interfering with silent auth

**Issue: Real-time updates not working**
- Verify WebSocket connection in Network tab
- Check firewall rules for WebSocket protocol
- Ensure JWT token hasn't expired

**Issue: Widgets not rendering**
- Check Redux DevTools for state errors
- Verify API responses in Network tab
- Review console for React errors

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Copyright © Natterbox Ltd. All rights reserved.