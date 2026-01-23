# Natterbox Wallboards - Setup & Development Guide

[![React](https://img.shields.io/badge/React-18.x-61DAFB?logo=react)](https://reactjs.org/)
[![Auth0](https://img.shields.io/badge/Auth0-Integrated-EB5424?logo=auth0)](https://auth0.com/)
[![Salesforce](https://img.shields.io/badge/Salesforce-VF%20Compatible-00A1E0?logo=salesforce)](https://salesforce.com/)
[![Webpack](https://img.shields.io/badge/Webpack-5.x-8DD6F9?logo=webpack)](https://webpack.js.org/)
[![Jest](https://img.shields.io/badge/Jest-Testing-C21325?logo=jest)](https://jestjs.io/)

> A ReactJS-based dashboard application for displaying real-time call center metrics, agent statuses, and queue information. Designed for seamless integration within Salesforce Visualforce iframes.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Locally](#running-locally)
- [Environment Configuration](#environment-configuration)
- [Build Process](#build-process)
- [Testing with Jest](#testing-with-jest)
- [Webpack Configuration](#webpack-configuration)
- [API Reference](#api-reference)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Natterbox Wallboards** is a sophisticated real-time dashboard solution built for call center operations. It provides operations managers and team leaders with instant visibility into agent performance, queue statistics, and overall call center health. The application is specifically architected to run within Salesforce Visualforce iframes, making it a natural extension of existing Salesforce CRM workflows.

The service utilizes a **single-bundle deployment strategy** with Base64 embedded resources, ensuring minimal external dependencies and simplified deployment within enterprise environments.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Agent Monitoring** | Live status updates for all agents including availability, call duration, and performance metrics |
| **Queue Visualization** | Visual representation of call queues with wait times, caller information, and queue depth |
| **Configurable Layouts** | Drag-and-drop wallboard customization to display relevant metrics |
| **Agent Group Management** | Organize agents into logical groups for targeted monitoring |
| **Auth0 Integration** | Enterprise-grade authentication and authorization |
| **Salesforce VF Integration** | Native iframe embedding within Visualforce pages |
| **Single-Bundle Deploy** | Self-contained build with embedded assets for simplified deployment |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Salesforce Environment                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Visualforce Page (iframe host)                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │           Natterbox Wallboards (React)              │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │  │
│  │  │  │   Agent     │  │   Queue     │  │  Layout    │  │  │  │
│  │  │  │  Monitor    │  │   Display   │  │  Manager   │  │  │  │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │  │  │
│  │  │         └────────────────┼────────────────┘        │  │  │
│  │  │                    ┌─────┴─────┐                    │  │  │
│  │  │                    │  State    │                    │  │  │
│  │  │                    │  Manager  │                    │  │  │
│  │  │                    └─────┬─────┘                    │  │  │
│  │  └──────────────────────────┼──────────────────────────┘  │  │
│  └─────────────────────────────┼─────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────┴─────┐           ┌───────┴───────┐
              │  Auth0    │           │  Natterbox    │
              │  Service  │           │  API Gateway  │
              └───────────┘           └───────────────┘
```

### Data Models

The application works with **74 distinct data models** covering:
- Agent profiles and status information
- Queue configurations and metrics
- Wallboard layout definitions
- Real-time call data structures
- Authentication and authorization tokens

---

## Prerequisites

Before setting up the development environment, ensure you have the following installed:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 18.x or higher | JavaScript runtime |
| Yarn | 1.22.x or higher | Package management |
| Git | 2.x+ | Version control |
| Auth0 Account | - | Authentication testing |

### System Requirements

- **OS**: macOS, Linux, or Windows 10/11
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: At least 2GB free space

### Recommended IDE Extensions

For VS Code users:
- ESLint
- Prettier
- React Developer Tools
- Jest Runner

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/natterbox/natterbox-wallboards.git
cd natterbox-wallboards
```

### Step 2: Install Dependencies

```bash
# Using Yarn (recommended)
yarn install

# Alternative: Using npm
npm install
```

### Step 3: Verify Installation

```bash
# Check that all dependencies are correctly installed
yarn check --integrity

# Run initial build verification
yarn build:check
```

### Step 4: Set Up Environment Files

```bash
# Copy the example environment file
cp .env.example .env.local

# Edit with your local configuration
nano .env.local
```

---

## Running Locally

### Development Server

Start the development server with hot-reload enabled:

```bash
# Start development server
yarn start

# Or with specific environment
yarn start:dev
```

The application will be available at `http://localhost:3000`.

### Running in Salesforce Simulation Mode

For testing Visualforce iframe integration locally:

```bash
# Start with VF simulation wrapper
yarn start:vf-sim
```

This launches the app within a simulated Visualforce container at `http://localhost:3000/vf-preview`.

### Development Server Options

```bash
# Start with verbose logging
DEBUG=wallboards:* yarn start

# Start on a different port
PORT=8080 yarn start

# Start with HTTPS (for Auth0 callbacks)
HTTPS=true yarn start
```

---

## Environment Configuration

### Required Environment Variables

Create a `.env.local` file with the following configuration:

```ini
# ===========================================
# Auth0 Configuration
# ===========================================
REACT_APP_AUTH0_DOMAIN=your-tenant.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.natterbox.com
REACT_APP_AUTH0_REDIRECT_URI=http://localhost:3000/callback

# ===========================================
# API Configuration
# ===========================================
REACT_APP_API_BASE_URL=https://api.natterbox.com/v1
REACT_APP_WEBSOCKET_URL=wss://realtime.natterbox.com

# ===========================================
# Feature Flags
# ===========================================
REACT_APP_ENABLE_QUEUE_MANAGEMENT=true
REACT_APP_ENABLE_AGENT_GROUPS=true
REACT_APP_ENABLE_CUSTOM_LAYOUTS=true

# ===========================================
# Salesforce Integration
# ===========================================
REACT_APP_SF_ORG_ID=00D000000000000
REACT_APP_VF_IFRAME_MODE=false

# ===========================================
# Development Settings
# ===========================================
REACT_APP_DEBUG_MODE=true
REACT_APP_MOCK_API=false
```

### Environment-Specific Files

| File | Purpose |
|------|---------|
| `.env` | Default values (committed) |
| `.env.local` | Local overrides (not committed) |
| `.env.development` | Development-specific settings |
| `.env.production` | Production build settings |
| `.env.test` | Test environment settings |

---

## Build Process

### Development Build

```bash
# Create development build
yarn build:dev
```

### Production Build

The production build creates a single-bundle deployment with Base64 embedded resources:

```bash
# Create optimized production build
yarn build:prod

# Build output location
ls -la dist/
```

### Build Output Structure

```
dist/
├── index.html              # Entry point with inline bundle reference
├── wallboards.bundle.js    # Single bundled application
├── wallboards.bundle.js.map # Source maps (optional)
└── assets/
    └── manifest.json       # Build manifest
```

### Bundle Analysis

```bash
# Analyze bundle size and composition
yarn build:analyze

# Generate detailed report
yarn build:report
```

### Build Configuration Flags

```bash
# Build without source maps
GENERATE_SOURCEMAP=false yarn build:prod

# Build with bundle analysis
ANALYZE=true yarn build:prod

# Build for specific environment
BUILD_ENV=staging yarn build
```

---

## Testing with Jest

### Running Tests

```bash
# Run all tests
yarn test

# Run tests in watch mode
yarn test:watch

# Run tests with coverage
yarn test:coverage
```

### Test File Structure

```
src/
├── components/
│   ├── AgentMonitor/
│   │   ├── AgentMonitor.tsx
│   │   ├── AgentMonitor.test.tsx    # Component tests
│   │   └── __snapshots__/
│   └── QueueDisplay/
│       ├── QueueDisplay.tsx
│       └── QueueDisplay.test.tsx
├── hooks/
│   ├── useAgentStatus.ts
│   └── useAgentStatus.test.ts       # Hook tests
└── utils/
    ├── formatters.ts
    └── formatters.test.ts           # Utility tests
```

### Example Test

```typescript
// src/components/AgentMonitor/AgentMonitor.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { AgentMonitor } from './AgentMonitor';
import { mockAgentData } from '../../__mocks__/agentData';

describe('AgentMonitor', () => {
  it('renders agent status correctly', async () => {
    render(<AgentMonitor agents={mockAgentData} />);
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByTestId('agent-status-available')).toBeInTheDocument();
    });
  });

  it('updates in real-time when agent status changes', async () => {
    const { rerender } = render(<AgentMonitor agents={mockAgentData} />);
    
    const updatedAgents = [...mockAgentData];
    updatedAgents[0].status = 'on-call';
    
    rerender(<AgentMonitor agents={updatedAgents} />);
    
    await waitFor(() => {
      expect(screen.getByTestId('agent-status-on-call')).toBeInTheDocument();
    });
  });
});
```

### Test Configuration

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

---

## Webpack Configuration

### Base Configuration

```javascript
// webpack.config.js
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'wallboards.bundle.js',
    clean: true,
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@utils': path.resolve(__dirname, 'src/utils'),
    },
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader'],
      },
      {
        test: /\.(png|jpg|gif|svg)$/,
        type: 'asset/inline', // Base64 embed all images
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/,
        type: 'asset/inline', // Base64 embed all fonts
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
      inject: 'body',
    }),
    new MiniCssExtractPlugin({
      filename: 'styles.css',
    }),
  ],
};
```

### Production Optimizations

```javascript
// webpack.prod.js
const { merge } = require('webpack-merge');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const baseConfig = require('./webpack.config');

module.exports = merge(baseConfig, {
  mode: 'production',
  devtool: 'source-map',
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
          },
        },
      }),
      new CssMinimizerPlugin(),
    ],
  },
  performance: {
    hints: 'warning',
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  },
});
```

---

## API Reference

The Natterbox Wallboards service interfaces with **6 API endpoints**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | Retrieve all agent statuses |
| `/agents/{id}` | GET | Get specific agent details |
| `/queues` | GET | Fetch queue metrics |
| `/queues/{id}/calls` | GET | Get calls in specific queue |
| `/layouts` | GET/POST | Manage wallboard layouts |
| `/groups` | GET | Retrieve agent groups |

---

## Documentation

For comprehensive documentation on all aspects of the Natterbox Wallboards service, please refer to the following resources:

| Document | Description |
|----------|-------------|
| [Configuration Guide](docs/configuration/README.md) | Detailed configuration options and environment setup |

---

## Troubleshooting

### Common Issues

#### Auth0 Callback Errors

```bash
# Ensure HTTPS is enabled for Auth0 callbacks
HTTPS=true yarn start

# Verify redirect URI matches Auth0 configuration
echo $REACT_APP_AUTH0_REDIRECT_URI
```

#### Build Size Exceeds Limit

```bash
# Analyze bundle to identify large dependencies
yarn build:analyze

# Consider lazy loading for non-critical components
```

#### WebSocket Connection Failures

1. Verify `REACT_APP_WEBSOCKET_URL` is correct
2. Check network firewall rules
3. Ensure Auth0 token is valid

#### Salesforce iframe Issues

```javascript
// Add to parent VF page for proper iframe communication
<script>
  document.domain = 'salesforce.com';
</script>
```

---

## Support

For issues and feature requests, please use the project's issue tracker or contact the Natterbox development team.

---

*Last updated: 2024*