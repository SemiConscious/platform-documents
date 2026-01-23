# Natterbox Routing Policies - Overview

[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![npm](https://img.shields.io/badge/npm-10.x-CB3837?style=flat-square&logo=npm)](https://www.npmjs.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue?style=flat-square)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

A powerful React-based frontend application for managing Natterbox routing policies. This service provides an intuitive interface for configuring AI-powered routing, managing call flows, and maintaining policy snapshots for enterprise telephony and communication systems.

---

## Table of Contents

- [Introduction](#introduction)
- [Features Overview](#features-overview)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Available Scripts](#available-scripts)
- [Project Architecture](#project-architecture)
- [Documentation Index](#documentation-index)
- [Contributing](#contributing)

---

## Introduction

The **natterbox-routing-policies** service is a sophisticated frontend application designed to empower administrators and developers with complete control over telephony routing configurations. Built with modern React practices, this application serves as the primary interface for:

- **Call Flow Management**: Design and manage complex call routing workflows with an intuitive visual interface
- **AI-Powered Routing**: Configure intelligent routing rules that leverage machine learning for optimal call distribution
- **Policy Versioning**: Maintain snapshots of routing configurations for auditing, rollback, and compliance purposes
- **Variable-Based Rules**: Create dynamic routing logic using various data types including dates, strings, numbers, and selection lists

This application integrates seamlessly with the Natterbox telephony infrastructure, providing real-time configuration capabilities for enterprise communication systems.

### Who Should Use This?

- **Telephony Administrators** managing call routing for organizations
- **Developers** building integrations with Natterbox services
- **DevOps Engineers** maintaining routing infrastructure
- **Support Teams** troubleshooting call flow issues

---

## Features Overview

### 🔀 Routing Policy Management

Create, edit, and manage routing policies with a comprehensive configuration interface:

| Feature | Description |
|---------|-------------|
| Policy CRUD Operations | Full create, read, update, delete capabilities for routing policies |
| Bulk Operations | Apply changes to multiple policies simultaneously |
| Import/Export | JSON-based policy import and export for migration |
| Validation | Real-time validation of policy configurations |

### 🤖 AI-Powered Routing

Configure intelligent routing with agent-based configurations:

- **Agent Assignment**: Define AI agents for specific routing scenarios
- **Skills-Based Routing**: Route calls based on agent capabilities
- **Load Balancing**: Distribute calls intelligently across available agents
- **Priority Queuing**: Set up priority-based call handling

### 📊 Variable-Based Routing Rules

Build dynamic routing logic with multiple variable types:

```typescript
// Example variable types supported
type RoutingVariable = 
  | { type: 'date'; value: Date; operator: 'before' | 'after' | 'between' }
  | { type: 'string'; value: string; operator: 'equals' | 'contains' | 'regex' }
  | { type: 'number'; value: number; operator: 'gt' | 'lt' | 'eq' | 'between' }
  | { type: 'boolean'; value: boolean }
  | { type: 'selection'; value: string[]; operator: 'in' | 'notIn' };
```

### 📸 Policy Snapshots & Versioning

- **Automatic Snapshots**: Capture policy states before changes
- **Manual Snapshots**: Create named snapshots for important configurations
- **Rollback Capability**: Restore previous policy versions instantly
- **Diff Viewer**: Compare policy versions side-by-side

### 🎛️ Feature Flags Support

Toggle features dynamically without deployments using integrated feature flag management.

### 🌍 International Support

Comprehensive country code and phone number handling for global telephony operations.

---

## Quick Start

Get the application running in under 5 minutes:

```bash
# Clone the repository
git clone <repository-url>
cd natterbox-routing-policies

# Install dependencies
npm install

# Set up environment configuration
cp .env.example .env.local

# Start the development server
npm start
```

The application will be available at `http://localhost:3000`.

### Environment Configuration

Create a `.env.local` file with the required configuration:

```env
# API Configuration
REACT_APP_NB_URL=https://api.natterbox.com

# Feature Flags
REACT_APP_ENABLE_AI_ROUTING=true
REACT_APP_ENABLE_SNAPSHOTS=true

# Authentication
REACT_APP_AUTH_DOMAIN=auth.natterbox.com
REACT_APP_CLIENT_ID=your-client-id
```

| Variable | Required | Description |
|----------|----------|-------------|
| `REACT_APP_NB_URL` | ✅ Yes | Base URL for Natterbox API endpoints |
| `REACT_APP_ENABLE_AI_ROUTING` | No | Enable AI routing features (default: false) |
| `REACT_APP_ENABLE_SNAPSHOTS` | No | Enable snapshot functionality (default: true) |

---

## Development Setup

### Prerequisites

Ensure you have the following installed:

| Tool | Version | Verification Command |
|------|---------|---------------------|
| Node.js | 18.x or higher | `node --version` |
| npm | 10.x or higher | `npm --version` |
| Git | 2.x or higher | `git --version` |

### Installation Steps

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd natterbox-routing-policies
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env.local
   
   # Edit with your configuration
   nano .env.local
   ```

4. **Verify Installation**
   ```bash
   npm run lint
   npm test -- --watchAll=false
   ```

5. **Start Development Server**
   ```bash
   npm start
   ```

### IDE Setup (Recommended)

For the best development experience with VS Code:

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

---

## Available Scripts

| Script | Command | Description |
|--------|---------|-------------|
| **Start** | `npm start` | Launches development server with hot reload |
| **Build** | `npm run build` | Creates production-optimized build in `/build` |
| **Test** | `npm test` | Runs test suite in interactive watch mode |
| **Test Coverage** | `npm run test:coverage` | Generates test coverage report |
| **Lint** | `npm run lint` | Checks code for style and syntax issues |
| **Lint Fix** | `npm run lint:fix` | Automatically fixes linting issues |
| **Type Check** | `npm run typecheck` | Validates TypeScript types |
| **Analyze** | `npm run analyze` | Analyzes bundle size |

### Common Development Workflows

```bash
# Run tests for a specific file
npm test -- PolicyEditor.test.tsx

# Build and analyze bundle
npm run build && npm run analyze

# Full validation before commit
npm run lint && npm run typecheck && npm test -- --watchAll=false
```

---

## Project Architecture

```
natterbox-routing-policies/
├── public/                    # Static assets and index.html
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── PolicyEditor/     # Policy editing interface
│   │   ├── RoutingBuilder/   # Visual routing flow builder
│   │   ├── SnapshotManager/  # Policy versioning UI
│   │   └── common/           # Shared components
│   ├── hooks/                # Custom React hooks
│   ├── models/               # TypeScript interfaces (34 models)
│   ├── services/             # API integration layer
│   ├── store/                # State management
│   ├── utils/                # Utility functions
│   ├── App.tsx               # Root application component
│   └── index.tsx             # Application entry point
├── docs/                     # Documentation files
├── .env.example              # Environment template
├── package.json              # Dependencies and scripts
└── tsconfig.json             # TypeScript configuration
```

### Key Architectural Decisions

- **Component-Based Architecture**: Modular, reusable components following React best practices
- **TypeScript First**: Full type coverage with 34 data models ensuring type safety
- **Service Layer Pattern**: Abstracted API calls for maintainability and testing
- **Feature-Based Organization**: Related functionality grouped together

---

## Documentation Index

Explore our comprehensive documentation for detailed information:

| Document | Description |
|----------|-------------|
| 📐 [Application Architecture](docs/architecture.md) | Detailed system design, component hierarchy, and architectural decisions |
| 📊 [Data Models Overview](docs/models/README.md) | Complete reference for all 34 TypeScript models and interfaces |
| 🔧 [Utility Functions Reference](docs/utilities.md) | Helper functions, formatters, and shared utilities |
| ⚙️ [Configuration Guide](docs/configuration.md) | Environment variables, feature flags, and deployment settings |

### Additional Resources

- **API Integration**: See the services directory for API client implementations
- **Component Storybook**: Run `npm run storybook` for interactive component documentation
- **Type Definitions**: Explore `src/models/` for complete TypeScript interfaces

---

## Contributing

We welcome contributions from the development team! Please follow these guidelines:

### Development Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow existing code patterns and conventions
   - Add tests for new functionality
   - Update documentation as needed

3. **Validate Your Changes**
   ```bash
   npm run lint
   npm run typecheck
   npm test -- --watchAll=false
   ```

4. **Submit a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

### Code Standards

- **TypeScript**: Use strict typing; avoid `any` types
- **Components**: Prefer functional components with hooks
- **Testing**: Maintain minimum 80% code coverage
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/) format

### Troubleshooting Common Issues

| Issue | Solution |
|-------|----------|
| `Module not found` errors | Run `npm install` and restart dev server |
| TypeScript compilation errors | Run `npm run typecheck` for detailed errors |
| Test failures | Check for environment variables in `.env.test` |
| Build failures | Clear cache with `npm cache clean --force` |

---

## Support

For questions, issues, or feature requests:

- **Internal Teams**: Reach out via Slack `#natterbox-routing-dev`
- **Bug Reports**: Create an issue in the repository
- **Documentation Issues**: Submit a PR with corrections

---

<div align="center">

**Built with ❤️ by the Natterbox Development Team**

</div>