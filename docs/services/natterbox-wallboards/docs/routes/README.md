# Natterbox Wallboards

[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Auth0](https://img.shields.io/badge/Auth0-Integrated-EB5424?style=flat-square&logo=auth0)](https://auth0.com/)
[![Salesforce](https://img.shields.io/badge/Salesforce-Visualforce-00A1E0?style=flat-square&logo=salesforce)](https://salesforce.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)]()

A ReactJS-based dashboard application for displaying real-time call center metrics, agent statuses, and queue information. Designed specifically for seamless integration within Salesforce Visualforce iframes, Natterbox Wallboards provides call center managers with instant visibility into team performance and queue health.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Application Routes](#application-routes)
  - [Route Overview](#route-overview)
  - [Home Route](#home-route)
  - [Wallboard Routes](#wallboard-routes)
  - [Group Routes](#group-routes)
  - [Utility Routes](#utility-routes)
  - [Route Parameters](#route-parameters)
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## Overview

Natterbox Wallboards transforms complex call center data into intuitive, real-time visual dashboards. Built with React and optimized for Salesforce Visualforce iframe embedding, this application enables call center supervisors and managers to monitor agent availability, track queue metrics, and respond quickly to changing conditions.

The application uses a **single-bundle deployment model** with Base64 embedded resources, making it ideal for environments where external resource loading is restricted or impractical.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Agent Monitoring** | Live status updates for all agents including availability, call state, and activity duration |
| **Queue Visualization** | Visual representation of queue depth, wait times, and call distribution |
| **Configurable Layouts** | Drag-and-drop wallboard configuration to display metrics that matter most |
| **Agent Group Management** | Organize agents into logical groups for targeted monitoring |
| **Auth0 Authentication** | Enterprise-grade authentication with SSO support |
| **Salesforce Integration** | Native Visualforce iframe compatibility for seamless CRM embedding |
| **Single-Bundle Deploy** | Self-contained deployment with no external dependencies |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Salesforce Visualforce                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Wallboards iframe                       │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              React Application                       │  │  │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │  │  │
│  │  │  │  Router   │──│  Context  │──│  Components   │   │  │  │
│  │  │  └───────────┘  └───────────┘  └───────────────┘   │  │  │
│  │  │        │              │               │            │  │  │
│  │  │        ▼              ▼               ▼            │  │  │
│  │  │  ┌─────────────────────────────────────────────┐   │  │  │
│  │  │  │           State Management                   │   │  │  │
│  │  │  └─────────────────────────────────────────────┘   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Auth0 Identity                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Natterbox API Services                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Agent Status │  │ Queue Metrics │  │ Wallboard Config    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Application Routes

### Route Overview

The Natterbox Wallboards application implements a hierarchical routing structure designed to support multiple wallboard configurations, agent group management, and utility functions. All routes are protected by Auth0 authentication unless otherwise specified.

| Route Pattern | Component | Auth Required | Description |
|---------------|-----------|---------------|-------------|
| `/` | `Home` | Yes | Main dashboard entry point |
| `/wallboard` | `WallboardList` | Yes | List all available wallboards |
| `/wallboard/:id` | `WallboardView` | Yes | Display specific wallboard |
| `/wallboard/:id/edit` | `WallboardEditor` | Yes | Configure wallboard layout |
| `/groups` | `GroupList` | Yes | Manage agent groups |
| `/groups/:groupId` | `GroupDetail` | Yes | View/edit specific group |
| `/callback` | `AuthCallback` | No | Auth0 callback handler |
| `/logout` | `LogoutHandler` | No | Session termination |

### Home Route

The home route (`/`) serves as the primary entry point and dashboard hub for authenticated users.

```tsx
// Route: /
// Component: Home

interface HomeRouteProps {
  defaultWallboardId?: string;
  showQuickStats: boolean;
}

// The Home component displays:
// - Quick statistics overview (total agents, active calls, queue depth)
// - Recent wallboards accessed by the user
// - Quick navigation to frequently used groups
// - System health indicators
```

**Behavior:**
- Redirects unauthenticated users to Auth0 login
- Loads user preferences from local storage
- Fetches real-time summary statistics on mount
- Auto-refreshes statistics every 30 seconds

### Wallboard Routes

Wallboard routes handle the core functionality of creating, viewing, and configuring wallboards.

#### List View (`/wallboard`)

```tsx
// Route: /wallboard
// Component: WallboardList

// Displays a grid of available wallboards with:
// - Thumbnail previews
// - Last modified timestamps
// - Quick actions (view, edit, duplicate, delete)
// - Search and filter capabilities
```

#### Detail View (`/wallboard/:id`)

```tsx
// Route: /wallboard/:id
// Component: WallboardView

interface WallboardViewParams {
  id: string;  // UUID of the wallboard configuration
}

// Features:
// - Full-screen wallboard display
// - Real-time data updates via WebSocket
// - Presentation mode toggle
// - Export to PDF functionality
```

**Example URL:** `/wallboard/550e8400-e29b-41d4-a716-446655440000`

#### Editor (`/wallboard/:id/edit`)

```tsx
// Route: /wallboard/:id/edit
// Component: WallboardEditor

// Provides drag-and-drop interface for:
// - Adding/removing widgets
// - Configuring widget data sources
// - Setting refresh intervals
// - Customizing visual themes
// - Defining alert thresholds
```

### Group Routes

Group routes manage agent groupings for organized monitoring.

#### Group List (`/groups`)

```tsx
// Route: /groups
// Component: GroupList

// Capabilities:
// - View all agent groups
// - Create new groups
// - Bulk agent assignment
// - Group hierarchy visualization
```

#### Group Detail (`/groups/:groupId`)

```tsx
// Route: /groups/:groupId
// Component: GroupDetail

interface GroupDetailParams {
  groupId: string;  // Unique identifier for the agent group
}

// Features:
// - List all agents in the group
// - Add/remove agents
// - Set group-level permissions
// - Configure group-specific alerts
```

**Example URL:** `/groups/support-tier-1`

### Utility Routes

#### Authentication Callback (`/callback`)

```tsx
// Route: /callback
// Component: AuthCallback

// Handles Auth0 redirect after successful authentication
// - Extracts authorization code from URL
// - Exchanges code for tokens
// - Stores tokens securely
// - Redirects to originally requested route or home
```

#### Logout (`/logout`)

```tsx
// Route: /logout
// Component: LogoutHandler

// Performs clean session termination:
// - Clears local storage tokens
// - Invalidates Auth0 session
// - Redirects to Auth0 logout endpoint
// - Returns user to login page
```

### Route Parameters

#### URL Parameters

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| `id` | `string (UUID)` | Path | Wallboard configuration identifier |
| `groupId` | `string` | Path | Agent group identifier |

#### Query Parameters

| Parameter | Type | Routes | Description |
|-----------|------|--------|-------------|
| `presentation` | `boolean` | `/wallboard/:id` | Enable presentation mode |
| `refresh` | `number` | `/wallboard/:id` | Override default refresh interval (seconds) |
| `theme` | `string` | All | Force specific visual theme (`light`, `dark`, `auto`) |
| `returnTo` | `string` | `/callback`, `/logout` | URL to redirect after operation |

**Example with Query Parameters:**
```
/wallboard/550e8400-e29b-41d4-a716-446655440000?presentation=true&refresh=15&theme=dark
```

---

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or yarn 1.22+
- Auth0 tenant configured
- Access to Natterbox API endpoints

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd natterbox-wallboards

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.local

# Configure environment variables (see Authentication section)
```

### Development

```bash
# Start development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint

# Run tests
npm run test
```

### Building for Production

```bash
# Create production build with embedded resources
npm run build

# The output will be a single HTML file with Base64 embedded assets
# Located at: dist/index.html
```

---

## Authentication

The application uses Auth0 for authentication. Configure the following environment variables:

```bash
# .env.local
REACT_APP_AUTH0_DOMAIN=your-tenant.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.natterbox.com
REACT_APP_AUTH0_REDIRECT_URI=https://your-domain.com/callback
```

---

## Deployment

### Salesforce Visualforce Integration

1. Build the production bundle
2. Upload the single HTML file to Salesforce Static Resources
3. Create a Visualforce page referencing the static resource
4. Configure iframe dimensions and permissions

```html
<!-- Example Visualforce Page -->
<apex:page showHeader="false" sidebar="false">
  <apex:iframe src="{!URLFOR($Resource.NatterboxWallboards)}" 
               height="100%" 
               width="100%" 
               scrolling="true"/>
</apex:page>
```

---

## Documentation

For detailed information about data models and configurations, refer to:

- **[Wallboard Configuration Models](docs/models/wallboard-models.md)** - Comprehensive documentation of wallboard configuration schemas, widget definitions, and layout options
- **[Agent & Queue Models](docs/models/agent-models.md)** - Data models for agent status, queue metrics, and real-time event structures

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Blank screen after login | Auth0 callback misconfiguration | Verify `REACT_APP_AUTH0_REDIRECT_URI` matches Auth0 allowed callbacks |
| Real-time updates not working | WebSocket connection blocked | Check firewall rules and CSP headers |
| Styles not loading in Salesforce | CSP restrictions | Ensure single-bundle build is used with embedded resources |
| Route not found errors | Base path mismatch | Configure `PUBLIC_URL` environment variable |

### Debug Mode

Enable debug logging by setting:

```bash
localStorage.setItem('natterbox_debug', 'true');
```

---

## Support

For technical support or feature requests, contact the Natterbox development team or submit an issue through the internal ticketing system.