# Natterbox Wallboards - Deployment Guide

[![Frontend](https://img.shields.io/badge/type-frontend-blue.svg)](.)
[![ReactJS](https://img.shields.io/badge/framework-ReactJS-61DAFB.svg)](https://reactjs.org/)
[![Auth0](https://img.shields.io/badge/auth-Auth0-EB5424.svg)](https://auth0.com/)
[![Salesforce](https://img.shields.io/badge/integration-Salesforce-00A1E0.svg)](https://www.salesforce.com/)

A comprehensive guide for deploying the Natterbox Wallboards application to production environments and integrating with Salesforce Visualforce pages.

---

## Table of Contents

- [Overview](#overview)
- [Documentation](#documentation)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Build Process](#build-process)
- [Production Bundle](#production-bundle)
- [Salesforce Visualforce Integration](#salesforce-visualforce-integration)
- [Static Resource Handling](#static-resource-handling)
- [API Endpoints](#api-endpoints)
- [Troubleshooting Deployment](#troubleshooting-deployment)
- [Quick Reference](#quick-reference)

---

## Overview

Natterbox Wallboards is a ReactJS-based dashboard application designed for displaying real-time call center metrics, agent statuses, and queue information. The application is specifically architected for seamless integration within Salesforce Visualforce iframes, featuring a single-bundle deployment strategy with Base64 embedded resources.

### Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Agent Status Monitoring** | Live tracking of agent availability, call states, and performance metrics |
| **Queue Call Visualization** | Interactive displays for managing and monitoring call queues |
| **Configurable Layouts** | Customizable wallboard configurations for different team needs |
| **Agent Group Management** | Organize and monitor agents by team, skill group, or custom criteria |
| **Auth0 Integration** | Secure authentication via Auth0 identity platform |
| **Salesforce Integration** | Native support for Visualforce iframe embedding |
| **Single-Bundle Deployment** | Simplified deployment with all resources embedded as Base64 |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Setup & Development Guide](docs/setup/README.md) | Complete guide for local development setup, configuration, and development workflows |

---

## Prerequisites

Before deploying the Natterbox Wallboards application, ensure you have the following:

### Development Environment

- Node.js 18.x or higher
- Yarn or npm package manager
- Git for version control
- Access to the Natterbox Wallboards repository

### Salesforce Environment

- Salesforce org with Visualforce enabled
- System Administrator or Developer permissions
- Static Resource deployment capabilities
- Connected App configuration for Auth0

### Auth0 Configuration

- Auth0 tenant with appropriate application configured
- Client ID and domain configured for production
- Allowed callback URLs configured for Salesforce domain

### Required Access

```plaintext
✓ Natterbox API credentials
✓ Salesforce deployment permissions
✓ Auth0 management dashboard access
✓ CDN or static hosting access (optional)
```

---

## Architecture Overview

The Natterbox Wallboards application follows a specific architecture designed for Salesforce embedding:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Salesforce Visualforce Page                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     <apex:iframe>                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │           Natterbox Wallboards (ReactJS)            │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │  │
│  │  │  │ Auth0 SDK   │  │ Wallboard   │  │ WebSocket  │  │  │  │
│  │  │  │ Integration │  │ Components  │  │ Connection │  │  │  │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │  │  │
│  │  │         │                │                │         │  │  │
│  │  └─────────┼────────────────┼────────────────┼─────────┘  │  │
│  └────────────┼────────────────┼────────────────┼────────────┘  │
└───────────────┼────────────────┼────────────────┼───────────────┘
                │                │                │
         ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
         │   Auth0     │  │  Natterbox  │  │  Real-time  │
         │   Tenant    │  │    API      │  │   Events    │
         └─────────────┘  └─────────────┘  └─────────────┘
```

### Data Flow

1. **Authentication**: User authenticates via Auth0 within Salesforce context
2. **Configuration Load**: Wallboard configuration fetched from Natterbox API
3. **Real-time Updates**: WebSocket connection established for live metrics
4. **Rendering**: React components render dashboard with real-time data

---

## Build Process

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd natterbox-wallboards

# Install dependencies
yarn install
# or
npm install
```

### Step 2: Environment Configuration

Create environment-specific configuration files:

```bash
# Production environment
cp .env.example .env.production
```

Edit `.env.production` with your production values:

```env
# Auth0 Configuration
REACT_APP_AUTH0_DOMAIN=your-tenant.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.natterbox.com

# API Configuration
REACT_APP_API_BASE_URL=https://api.natterbox.com/v1
REACT_APP_WEBSOCKET_URL=wss://realtime.natterbox.com

# Salesforce Configuration
REACT_APP_SF_ORIGIN=https://your-org.lightning.force.com
REACT_APP_EMBED_MODE=visualforce

# Build Configuration
REACT_APP_INLINE_RUNTIME_CHUNK=true
GENERATE_SOURCEMAP=false
```

### Step 3: Build for Production

```bash
# Run production build
yarn build:production
# or
npm run build:production
```

This generates optimized production assets in the `build/` directory:

```
build/
├── static/
│   ├── js/
│   │   └── main.[hash].js       # Single bundled JavaScript
│   └── css/
│       └── main.[hash].css      # Single bundled CSS
├── index.html                    # Entry point
└── asset-manifest.json          # Build manifest
```

### Step 4: Generate Single-Bundle Package

For Salesforce deployment, generate a self-contained HTML file with embedded resources:

```bash
# Run the bundle packaging script
yarn build:salesforce
# or
npm run build:salesforce
```

This creates a single HTML file with all resources inlined:

```bash
dist/
└── wallboards-bundle.html       # Self-contained deployment package
```

---

## Production Bundle

### Bundle Structure

The production bundle is a single HTML file optimized for Visualforce embedding:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Natterbox Wallboards</title>
    <!-- Inlined CSS -->
    <style>
        /* All CSS bundled and minified inline */
    </style>
</head>
<body>
    <div id="root"></div>
    <!-- Inlined JavaScript -->
    <script>
        /* All JavaScript bundled and minified inline */
    </script>
</body>
</html>
```

### Bundle Size Optimization

Monitor and optimize bundle size with these commands:

```bash
# Analyze bundle composition
yarn analyze
# or
npm run analyze

# View bundle size report
yarn size
# or
npm run size
```

**Target bundle sizes:**

| Asset Type | Target Size | Max Size |
|------------|-------------|----------|
| JavaScript | < 500 KB | 750 KB |
| CSS | < 50 KB | 100 KB |
| Total Bundle | < 600 KB | 1 MB |

### Versioning the Bundle

Each production bundle should include version metadata:

```javascript
// Embedded in bundle header
window.NATTERBOX_WALLBOARDS = {
    version: '2.5.0',
    buildDate: '2024-01-15T10:30:00Z',
    commitHash: 'abc123f',
    environment: 'production'
};
```

---

## Salesforce Visualforce Integration

### Step 1: Create Static Resource

1. Navigate to **Setup → Static Resources** in Salesforce
2. Click **New Static Resource**
3. Configure the resource:

| Field | Value |
|-------|-------|
| Name | `NatterboxWallboards` |
| Description | `Natterbox Wallboards Application Bundle v2.5.0` |
| File | Upload `wallboards-bundle.html` |
| Cache Control | `Public` |

### Step 2: Create Visualforce Page

Create a new Visualforce page to host the wallboard:

```xml
<apex:page showHeader="false" 
           sidebar="false" 
           standardStylesheets="false"
           applyHtmlTag="false"
           applyBodyTag="false"
           docType="html-5.0"
           controller="NatterboxWallboardController">
    
    <html>
    <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Natterbox Wallboards</title>
        
        <!-- Security Headers -->
        <meta http-equiv="Content-Security-Policy" 
              content="default-src 'self' https://*.natterbox.com https://*.auth0.com; 
                       script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
                       style-src 'self' 'unsafe-inline';
                       connect-src 'self' https://*.natterbox.com wss://*.natterbox.com https://*.auth0.com;
                       frame-ancestors 'self' https://*.force.com https://*.salesforce.com;"/>
    </head>
    <body>
        <!-- Configuration injection from Salesforce -->
        <script>
            window.SALESFORCE_CONFIG = {
                userId: '{!$User.Id}',
                orgId: '{!$Organization.Id}',
                sessionId: '{!$Api.Session_ID}',
                baseUrl: '{!$Site.BaseUrl}'
            };
        </script>
        
        <!-- Load wallboard bundle -->
        <apex:outputText value="{!wallboardBundle}" escape="false"/>
    </body>
    </html>
</apex:page>
```

### Step 3: Create Apex Controller

```java
public class NatterboxWallboardController {
    
    public String wallboardBundle { get; private set; }
    
    public NatterboxWallboardController() {
        // Load the static resource content
        StaticResource sr = [
            SELECT Body 
            FROM StaticResource 
            WHERE Name = 'NatterboxWallboards' 
            LIMIT 1
        ];
        
        wallboardBundle = sr.Body.toString();
    }
    
    // Optional: Provide user context
    @AuraEnabled(cacheable=true)
    public static Map<String, Object> getUserContext() {
        return new Map<String, Object>{
            'userId' => UserInfo.getUserId(),
            'userName' => UserInfo.getName(),
            'userEmail' => UserInfo.getUserEmail(),
            'orgId' => UserInfo.getOrganizationId(),
            'timezone' => UserInfo.getTimeZone().toString()
        };
    }
}
```

### Step 4: Configure Security Settings

Add the following to your Salesforce org's security settings:

**Remote Site Settings:**

| Remote Site Name | URL |
|------------------|-----|
| NatterboxAPI | `https://api.natterbox.com` |
| NatterboxRealtime | `https://realtime.natterbox.com` |
| Auth0 | `https://your-tenant.auth0.com` |

**CSP Trusted Sites:**

```plaintext
https://*.natterbox.com
wss://*.natterbox.com
https://*.auth0.com
```

### Step 5: Embed in Lightning Experience

Create a Lightning component wrapper for the Visualforce page:

```html
<!-- natterboxWallboardWrapper.html -->
<template>
    <div class="wallboard-container">
        <iframe 
            src={visualforceUrl}
            frameborder="0"
            width="100%"
            height="100%"
            allow="fullscreen">
        </iframe>
    </div>
</template>
```

```javascript
// natterboxWallboardWrapper.js
import { LightningElement, api } from 'lwc';

export default class NatterboxWallboardWrapper extends LightningElement {
    @api wallboardId;
    
    get visualforceUrl() {
        return `/apex/NatterboxWallboard?wallboardId=${this.wallboardId}`;
    }
}
```

---

## Static Resource Handling

### Base64 Resource Embedding

All static assets (images, fonts, icons) are embedded as Base64 data URIs in the production bundle:

```javascript
// webpack.config.js - Asset embedding configuration
module.exports = {
    module: {
        rules: [
            {
                test: /\.(png|jpg|gif|svg)$/i,
                type: 'asset/inline', // Forces Base64 embedding
            },
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/i,
                type: 'asset/inline',
            },
        ],
    },
};
```

### Asset Size Limits

Configure asset inline limits in your build configuration:

```javascript
// Asset inline threshold (bytes)
const INLINE_LIMIT = 100000; // 100KB

module.exports = {
    module: {
        rules: [
            {
                test: /\.(png|jpg|gif)$/i,
                type: 'asset',
                parser: {
                    dataUrlCondition: {
                        maxSize: INLINE_LIMIT,
                    },
                },
            },
        ],
    },
};
```

### Handling External Resources

For resources that cannot be embedded, use Salesforce Static Resources:

```javascript
// Dynamic resource loading within Salesforce context
const loadExternalResource = (resourceName) => {
    const baseUrl = window.SALESFORCE_CONFIG?.baseUrl || '';
    return `${baseUrl}/resource/${resourceName}`;
};

// Usage
const logoUrl = loadExternalResource('NatterboxLogo');
```

---

## API Endpoints

The Natterbox Wallboards application communicates with the following 6 primary endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wallboards` | GET | Retrieve wallboard configurations |
| `/api/v1/wallboards/{id}` | GET | Get specific wallboard details |
| `/api/v1/agents/status` | GET | Fetch current agent statuses |
| `/api/v1/queues` | GET | List available call queues |
| `/api/v1/queues/{id}/metrics` | GET | Get queue-specific metrics |
| `/api/v1/groups` | GET | Retrieve agent group configurations |

### WebSocket Connections

Real-time data is delivered via WebSocket:

```javascript
// WebSocket connection for real-time updates
const ws = new WebSocket('wss://realtime.natterbox.com/wallboards');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle real-time updates
    switch(data.type) {
        case 'AGENT_STATUS_CHANGE':
            // Update agent status display
            break;
        case 'QUEUE_METRICS_UPDATE':
            // Update queue metrics
            break;
        case 'CALL_EVENT':
            // Handle call events
            break;
    }
};
```

---

## Troubleshooting Deployment

### Common Issues and Solutions

#### Issue 1: Bundle Not Loading in Visualforce

**Symptoms:** Blank page or JavaScript errors in console

**Solutions:**

```bash
# Verify bundle integrity
sha256sum dist/wallboards-bundle.html

# Check for special characters
file dist/wallboards-bundle.html
# Expected: HTML document, UTF-8 Unicode text
```

Ensure the Static Resource is uploaded correctly:
- Maximum file size: 5 MB
- Content type: `text/html`
- Cache Control: `Public`

#### Issue 2: Auth0 Authentication Failures

**Symptoms:** Login redirects fail or tokens not received

**Checklist:**

| Check | Expected Value |
|-------|----------------|
| Allowed Callback URLs | `https://your-org.lightning.force.com/apex/NatterboxWallboard` |
| Allowed Web Origins | `https://your-org.lightning.force.com` |
| Allowed Logout URLs | `https://your-org.lightning.force.com` |

**Debug Authentication:**

```javascript
// Enable Auth0 debug mode in development
auth0Client.checkSession({
    debug: true
}).then(console.log).catch(console.error);
```

#### Issue 3: WebSocket Connection Failures

**Symptoms:** Real-time updates not appearing

**Diagnostic Steps:**

```javascript
// Test WebSocket connectivity
const testConnection = () => {
    const ws = new WebSocket('wss://realtime.natterbox.com/health');
    
    ws.onopen = () => console.log('✓ WebSocket connection successful');
    ws.onerror = (e) => console.error('✗ WebSocket error:', e);
    ws.onclose = (e) => console.log('WebSocket closed:', e.code, e.reason);
    
    setTimeout(() => ws.close(), 5000);
};
```

**Firewall Requirements:**

```plaintext
Outbound connections required:
- TCP 443 → realtime.natterbox.com (WSS)
- TCP 443 → api.natterbox.com (HTTPS)
- TCP 443 → your-tenant.auth0.com (HTTPS)
```

#### Issue 4: Content Security Policy Errors

**Symptoms:** Resources blocked, script errors

**Solution:** Update the Visualforce page CSP meta tag:

```html
<meta http-equiv="Content-Security-Policy" 
      content="
        default-src 'self' https://*.natterbox.com https://*.auth0.com;
        script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.auth0.com;
        style-src 'self' 'unsafe-inline';
        img-src 'self' data: https://*.natterbox.com;
        font-src 'self' data:;
        connect-src 'self' 
            https://*.natterbox.com 
            wss://*.natterbox.com 
            https://*.auth0.com;
        frame-ancestors 'self' 
            https://*.force.com 
            https://*.salesforce.com 
            https://*.lightning.force.com;
      "/>
```

#### Issue 5: Iframe Cross-Origin Issues

**Symptoms:** `postMessage` failures, storage access denied

**Solution:** Configure proper frame communication:

```javascript
// Parent frame (Salesforce) to iframe communication
window.addEventListener('message', (event) => {
    // Validate origin
    const allowedOrigins = [
        'https://your-org.lightning.force.com',
        'https://your-org.my.salesforce.com'
    ];
    
    if (!allowedOrigins.includes(event.origin)) {
        console.warn('Message from unauthorized origin:', event.origin);
        return;
    }
    
    // Handle message
    const { type, payload } = event.data;
    // Process message...
});
```

### Deployment Verification Checklist

```markdown
## Pre-Deployment
- [ ] Production build completed successfully
- [ ] Bundle size within limits (< 1 MB)
- [ ] Environment variables configured
- [ ] Auth0 application settings verified

## Salesforce Configuration
- [ ] Static Resource uploaded
- [ ] Visualforce page created
- [ ] Apex controller deployed
- [ ] Remote Site Settings configured
- [ ] CSP Trusted Sites added

## Post-Deployment
- [ ] Visualforce page loads correctly
- [ ] Authentication flow works
- [ ] Real-time data updates appear
- [ ] All wallboard features functional
- [ ] Mobile responsiveness verified
```

---

## Quick Reference

### Build Commands

| Command | Description |
|---------|-------------|
| `yarn build` | Standard production build |
| `yarn build:salesforce` | Single-bundle for Salesforce |
| `yarn analyze` | Bundle size analysis |
| `yarn test` | Run test suite |

### Key Files

| File | Purpose |
|------|---------|
| `dist/wallboards-bundle.html` | Production deployment package |
| `.env.production` | Production environment config |
| `build/asset-manifest.json` | Build artifact manifest |

### Support Resources

| Resource | Location |
|----------|----------|
| API Documentation | `https://docs.natterbox.com/api` |
| Auth0 Dashboard | `https://manage.auth0.com` |
| Salesforce Setup | `Setup → Visualforce Pages` |

---

## Contributing

For development setup and contribution guidelines, see the [Setup & Development Guide](docs/setup/README.md).

---

*Last updated: 2024*