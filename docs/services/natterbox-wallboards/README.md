# Natterbox Wallboards Documentation

[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![Auth0](https://img.shields.io/badge/Auth0-Integrated-EB5424?style=flat-square&logo=auth0)](https://auth0.com/)
[![Salesforce](https://img.shields.io/badge/Salesforce-Visualforce-00A1E0?style=flat-square&logo=salesforce)](https://salesforce.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue?style=flat-square)]()
[![Documentation](https://img.shields.io/badge/Docs-Complete-green?style=flat-square)]()

---

## Introduction

**Natterbox Wallboards** is a sophisticated ReactJS-based dashboard application purpose-built for displaying real-time call center metrics, agent statuses, and queue information. Designed specifically for seamless integration within Salesforce Visualforce iframes, this application empowers call center managers and supervisors with instant visibility into their operations.

### What Does Natterbox Wallboards Do?

At its core, Natterbox Wallboards serves as the visual command center for call center operations. It transforms raw telephony data into actionable, real-time visualizations that help teams:

- **Monitor Agent Performance** — Track agent availability, call handling times, and status transitions in real-time
- **Manage Queue Health** — Visualize call queues, wait times, and service levels at a glance
- **Optimize Resources** — Make informed staffing decisions based on live metrics
- **Enhance Customer Experience** — Identify bottlenecks and respond proactively to service issues

### Key Features

| Feature | Description |
|---------|-------------|
| 🔴 **Real-time Agent Monitoring** | Live status tracking for all agents with instant updates |
| 📊 **Queue Visualization** | Dynamic queue displays with call counts, wait times, and SLA indicators |
| ⚙️ **Configurable Layouts** | Drag-and-drop wallboard customization to match your operational needs |
| 👥 **Agent Group Management** | Organize and filter agents by teams, skills, or custom groupings |
| 🔐 **Auth0 Authentication** | Enterprise-grade security with SSO support |
| 🔗 **Salesforce Integration** | Native Visualforce iframe embedding for unified CRM experience |
| 📦 **Single-Bundle Deployment** | Simplified deployment with Base64 embedded resources |

### Target Audience

This documentation is intended for **developers** who are:

- Integrating Natterbox Wallboards into existing Salesforce environments
- Extending or customizing wallboard functionality
- Deploying and maintaining wallboard instances
- Troubleshooting integration or performance issues

---

## Quick Start

Get Natterbox Wallboards running in your development environment in minutes.

### Prerequisites

Before you begin, ensure you have the following installed and configured:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 18.x or higher | JavaScript runtime |
| Yarn / npm | Latest | Package management |
| Git | 2.x+ | Version control |
| Auth0 Account | — | Authentication provider |
| Salesforce Org | — | Target deployment environment |

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd natterbox-wallboards

# Verify you're on the correct branch
git branch --show-current
```

### Step 2: Install Dependencies

```bash
# Using Yarn (recommended)
yarn install

# Or using npm
npm install
```

### Step 3: Configure Environment

Create your local environment configuration:

```bash
# Copy the environment template
cp .env.example .env.local
```

Edit `.env.local` with your specific configuration:

```env
# Auth0 Configuration
REACT_APP_AUTH0_DOMAIN=your-tenant.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your_client_id
REACT_APP_AUTH0_AUDIENCE=https://api.natterbox.com

# API Configuration
REACT_APP_API_BASE_URL=https://api.natterbox.com/v1
REACT_APP_WEBSOCKET_URL=wss://realtime.natterbox.com

# Feature Flags
REACT_APP_ENABLE_DEBUG_MODE=true
REACT_APP_ENABLE_MOCK_DATA=false
```

### Step 4: Start Development Server

```bash
# Start the development server
yarn start

# Or with npm
npm start
```

The application will be available at `http://localhost:3000`.

### Step 5: Verify Installation

Open your browser and navigate to `http://localhost:3000`. You should see the Auth0 login prompt. After authentication, the main wallboard dashboard will load.

```bash
# Run the test suite to verify everything is working
yarn test

# Run linting to check code quality
yarn lint
```

---

## Architecture Overview

Natterbox Wallboards follows a modern, component-based architecture optimized for real-time data visualization and Salesforce integration.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Salesforce Visualforce                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Visualforce iframe                       │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │            Natterbox Wallboards (React)              │  │  │
│  │  │                                                      │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │  │
│  │  │  │  Auth0   │  │  State   │  │  Real-time       │   │  │  │
│  │  │  │  Module  │  │  Manager │  │  WebSocket       │   │  │  │
│  │  │  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │  │  │
│  │  │       │             │                 │              │  │  │
│  │  │  ┌────┴─────────────┴─────────────────┴──────────┐  │  │  │
│  │  │  │              Component Layer                   │  │  │  │
│  │  │  │  ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │  │  │  │
│  │  │  │  │ Agent   │ │ Queue   │ │ Wallboard       │  │  │  │  │
│  │  │  │  │ Status  │ │ Metrics │ │ Layout Manager  │  │  │  │  │
│  │  │  │  └─────────┘ └─────────┘ └─────────────────┘  │  │  │  │
│  │  │  └────────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Natterbox Backend APIs                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────────┐ │
│  │  REST API  │  │  WebSocket │  │  Telephony Integration     │ │
│  │  (6 endpoints)  │  Server   │  │  Services                  │ │
│  └────────────┘  └────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Core Architectural Principles

1. **Single-Bundle Deployment** — All assets (JavaScript, CSS, images) are compiled into a single bundle with Base64-encoded resources, eliminating external dependencies during runtime.

2. **Real-time First** — WebSocket connections provide instant updates for agent status changes, queue metrics, and system events.

3. **Iframe Isolation** — The application is designed to run within Salesforce Visualforce iframes, with proper cross-origin communication handling.

4. **Modular Components** — Each wallboard widget is a self-contained React component that can be independently configured and positioned.

### Data Flow

```
User Action → React Component → State Manager → API/WebSocket → Backend
                    ↑                                    │
                    └────────────── State Update ←───────┘
```

### API Endpoints Overview

The application interacts with **6 primary API endpoints**:

| Endpoint Category | Purpose |
|-------------------|---------|
| Agent Status | Retrieve and update agent availability states |
| Queue Metrics | Fetch real-time queue statistics |
| Wallboard Config | Load/save wallboard layout configurations |
| Group Management | Manage agent groupings and filters |
| Authentication | Auth0 token validation and refresh |
| WebSocket | Real-time event subscription |

---

## Tech Stack

### Frontend Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI Framework | 18.x |
| **TypeScript** | Type Safety | 5.x |
| **Redux Toolkit** | State Management | Latest |
| **React Query** | Server State | v4+ |
| **Styled Components** | CSS-in-JS | 6.x |
| **Socket.io Client** | WebSocket Communication | 4.x |

### Authentication & Security

| Technology | Purpose |
|------------|---------|
| **Auth0** | Identity Provider & SSO |
| **JWT** | Token-based Authentication |
| **PKCE** | OAuth 2.0 Flow for SPAs |

### Build & Development

| Tool | Purpose |
|------|---------|
| **Webpack** | Module Bundling |
| **Babel** | JavaScript Transpilation |
| **ESLint** | Code Linting |
| **Prettier** | Code Formatting |
| **Jest** | Unit Testing |
| **React Testing Library** | Component Testing |

### Integration Technologies

| Technology | Purpose |
|------------|---------|
| **Salesforce Visualforce** | Hosting Environment |
| **PostMessage API** | Cross-frame Communication |
| **Base64 Encoding** | Resource Embedding |

---

## Documentation Index

Navigate to detailed documentation for specific topics:

### Setup & Configuration

| Document | Description |
|----------|-------------|
| 📘 [Setup & Development Guide](docs/setup/README.md) | Complete development environment setup, build processes, and local development workflow |
| ⚙️ [Configuration Guide](docs/configuration/README.md) | Environment variables, feature flags, and runtime configuration options |

### Architecture & Design

| Document | Description |
|----------|-------------|
| 🏗️ [Application Architecture](docs/architecture/README.md) | Detailed architectural decisions, component hierarchy, and design patterns |
| 🗺️ [Application Routes](docs/routes/README.md) | Route definitions, navigation patterns, and deep-linking support |

### Data & Models

| Document | Description |
|----------|-------------|
| 📊 [Data Models Overview](docs/models/README.md) | Complete reference for all 74 data models, TypeScript interfaces, and API contracts |

---

## Deployment Overview

Natterbox Wallboards uses a single-bundle deployment strategy optimized for Salesforce Visualforce integration.

### Build Process

```bash
# Create production build
yarn build

# The output will be in the /build directory
ls -la build/
```

### Deployment Artifacts

```
build/
├── index.html          # Entry point (self-contained)
├── static/
│   └── js/
│       └── main.[hash].js   # Single bundled JavaScript file
└── asset-manifest.json      # Build metadata
```

### Salesforce Deployment Steps

1. **Build the Application**
   ```bash
   yarn build:production
   ```

2. **Upload to Salesforce Static Resources**
   ```bash
   # Use Salesforce CLI or deploy via Setup
   sfdx force:source:deploy -p force-app/main/default/staticresources
   ```

3. **Configure Visualforce Page**
   ```html
   <apex:page>
       <apex:iframe src="{!$Resource.NatterboxWallboards}/index.html" 
                    width="100%" 
                    height="100%" 
                    frameBorder="0"/>
   </apex:page>
   ```

4. **Verify Deployment**
   - Navigate to the Visualforce page in your Salesforce org
   - Verify Auth0 authentication flows correctly
   - Confirm real-time data is streaming

### Environment-Specific Builds

```bash
# Development build
yarn build:dev

# Staging build
yarn build:staging

# Production build
yarn build:production
```

### Troubleshooting Deployment

| Issue | Solution |
|-------|----------|
| Auth0 redirect fails | Verify callback URLs include Visualforce page URL |
| WebSocket connection drops | Check CSP headers in Salesforce org |
| Styles not loading | Ensure Base64 encoding is enabled in build config |
| CORS errors | Verify API endpoints are whitelisted for Salesforce domain |

---

## Support & Contributing

### Getting Help

- Review the [Setup & Development Guide](docs/setup/README.md) for common issues
- Check the [Configuration Guide](docs/configuration/README.md) for environment-specific settings
- Consult the [Architecture Documentation](docs/architecture/README.md) for design decisions

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is proprietary software owned by Natterbox Ltd. Unauthorized copying, distribution, or modification is prohibited.

---

<div align="center">

**Natterbox Wallboards** — Real-time Call Center Intelligence

[Documentation](docs/) · [Report Bug](issues/) · [Request Feature](issues/)

</div>