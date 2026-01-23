# Insight Categorisation UI - Overview

[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![Redux](https://img.shields.io/badge/Redux-Toolkit-764ABC?logo=redux&logoColor=white)](https://redux-toolkit.js.org/)
[![Feature-Sliced Design](https://img.shields.io/badge/Architecture-Feature--Sliced-blueviolet)](https://feature-sliced.design/)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

> A powerful React/TypeScript frontend application for Insight voice analytics categorization, enabling customers to create, manage, and apply sophisticated call analysis categories across their organization.

---

## 📋 Table of Contents

- [Introduction](#introduction)
- [Business Context](#business-context)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Key Features](#key-features)
- [Documentation Index](#documentation-index)
- [Development Workflow](#development-workflow)
- [Configuration](#configuration)
- [Contributing](#contributing)

---

## Introduction

The **insight-insight-category-ui** service is a comprehensive frontend application designed for the Insight voice analytics platform. It provides an intuitive interface for creating and managing categorization rules that analyze call transcriptions, enabling businesses to extract valuable insights from their customer interactions.

This application serves as the primary user interface for:
- Building complex query-based categories for call analysis
- Managing reusable category templates
- Assigning categories to specific users and groups
- Configuring prompts for AI-driven analysis
- Integrating with external systems like Salesforce and Sapien

The categorization engine is **transcription-partner agnostic**, meaning it can process call data from multiple speech-to-text providers without requiring source-specific configurations.

---

## Business Context

### Why Call Categorization Matters

In modern contact centers and sales organizations, thousands of calls occur daily. Manually reviewing these calls is impractical, yet the insights they contain are invaluable. The Insight Categorisation UI addresses this challenge by:

| Business Challenge | Solution Provided |
|-------------------|-------------------|
| High volume of calls to analyze | Automated categorization with complex query rules |
| Inconsistent call quality assessment | Standardized category templates and scoring |
| Siloed insights across teams | User/group-based category assignments |
| Multiple transcription providers | Agnostic engine supporting various partners |
| Integration with existing CRM | Salesforce and Sapien system connectivity |

### Target Users

- **Quality Assurance Teams**: Define compliance and quality categories
- **Sales Managers**: Track sales methodology adherence
- **Operations Leaders**: Monitor customer sentiment and issue escalation
- **Developers**: Integrate categorization into broader analytics pipelines

---

## Quick Start

Get up and running with the Insight Categorisation UI in under 5 minutes.

### Prerequisites

Ensure you have the following installed:

```bash
# Check Node.js version (18.x or higher recommended)
node --version

# Check npm version (9.x or higher)
npm --version
```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd insight-insight-category-ui

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.local
```

### Environment Setup

Edit `.env.local` with your configuration:

```env
# API Configuration
REACT_APP_API_BASE_URL=https://api.insight.example.com
REACT_APP_AUTH_DOMAIN=auth.insight.example.com

# Feature Flags
REACT_APP_ENABLE_SALESFORCE=true
REACT_APP_ENABLE_SAPIEN=true
```

### Running the Application

```bash
# Start development server
npm run dev

# Application will be available at http://localhost:3000
```

### Verify Installation

Once running, you should see the login screen. Use your organization credentials or development test accounts to access the categorization dashboard.

---

## Architecture Overview

The application follows **Feature-Sliced Design (FSD)** architecture, providing a scalable and maintainable codebase structure.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Insight Category UI                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  App    │  │ Pages   │  │ Widgets │  │Features │            │
│  │ Layer   │  │ Layer   │  │ Layer   │  │ Layer   │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                   │
│  ┌────┴────────────┴────────────┴────────────┴────┐            │
│  │              Entities Layer                      │            │
│  │   (Categories, Templates, Users, Groups, etc.)  │            │
│  └────────────────────┬─────────────────────────────┘            │
│                       │                                          │
│  ┌────────────────────┴─────────────────────────────┐            │
│  │                 Shared Layer                      │            │
│  │    (UI Kit, API Client, Utils, Constants)        │            │
│  └───────────────────────────────────────────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                    Redux Store (State Management)                │
├─────────────────────────────────────────────────────────────────┤
│           External APIs (Insight API, Salesforce, Sapien)       │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── app/                    # Application initialization, providers, global styles
│   ├── providers/          # React context providers
│   ├── store/              # Redux store configuration
│   └── styles/             # Global CSS/SCSS
├── pages/                  # Route-level components
│   ├── categories/         # Category management pages
│   ├── templates/          # Template management pages
│   └── settings/           # User/group settings pages
├── widgets/                # Complex UI blocks combining features
│   ├── CategoryBuilder/    # Query builder widget
│   └── AssignmentPanel/    # User/group assignment widget
├── features/               # User interactions and business logic
│   ├── create-category/    # Category creation feature
│   ├── manage-templates/   # Template management feature
│   └── prompt-editor/      # Prompt configuration feature
├── entities/               # Business entities with their logic
│   ├── category/           # Category entity
│   ├── template/           # Template entity
│   ├── user/               # User entity
│   └── group/              # Group entity
└── shared/                 # Reusable code across all layers
    ├── api/                # API client and endpoints
    ├── ui/                 # UI component library
    ├── lib/                # Utility libraries
    └── config/             # Configuration constants
```

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Language** | TypeScript | 5.0+ | Type-safe development |
| **UI Framework** | React | 18.x | Component-based UI |
| **State Management** | Redux Toolkit | 2.x | Global state management |
| **Routing** | React Router | 6.x | Client-side routing |
| **Styling** | Styled Components / CSS Modules | - | Component styling |
| **API Communication** | RTK Query | 2.x | Data fetching & caching |
| **Testing** | Jest + React Testing Library | - | Unit & integration tests |
| **Build Tool** | Vite | 5.x | Fast development builds |
| **Linting** | ESLint + Prettier | - | Code quality |

### API Integration Points

The application interfaces with **9 API endpoints** across multiple services:

- **Category Service**: CRUD operations for categories
- **Template Service**: Template management and sharing
- **Assignment Service**: User/group category assignments
- **Prompt Service**: AI prompt configuration
- **Integration Service**: Salesforce/Sapien connectivity

---

## Key Features

### 1. Category Creation with Complex Query Syntax

Build sophisticated categorization rules using an intuitive query builder:

```typescript
// Example category query structure
const categoryQuery = {
  operator: 'AND',
  conditions: [
    {
      field: 'transcript.content',
      operator: 'CONTAINS',
      value: 'refund request',
      caseSensitive: false
    },
    {
      field: 'speaker.role',
      operator: 'EQUALS',
      value: 'CUSTOMER'
    },
    {
      operator: 'OR',
      conditions: [
        { field: 'sentiment.score', operator: 'LESS_THAN', value: -0.5 },
        { field: 'keywords', operator: 'INCLUDES', value: ['frustrated', 'angry'] }
      ]
    }
  ]
};
```

### 2. Template System

Create reusable category configurations for consistent analysis across teams:

```typescript
// Template usage example
import { useTemplate } from '@/features/manage-templates';

const SalesComplianceTemplate = () => {
  const { applyTemplate, templates } = useTemplate();
  
  return (
    <TemplateSelector
      templates={templates}
      onSelect={(template) => applyTemplate(template.id)}
    />
  );
};
```

### 3. User and Group Assignment

Assign categories to specific users or entire groups for targeted analysis:

```typescript
// Assignment configuration
interface CategoryAssignment {
  categoryId: string;
  assignees: {
    users: string[];
    groups: string[];
  };
  effectiveFrom: Date;
  effectiveTo?: Date;
}
```

### 4. Multi-System Integration

Seamlessly connect with Salesforce and Sapien for unified user management:

| Integration | Capabilities |
|-------------|--------------|
| **Salesforce** | User sync, CRM data enrichment, activity logging |
| **Sapien** | Advanced user authentication, group hierarchy |

---

## Documentation Index

Explore detailed documentation for specific aspects of the application:

| Document | Description |
|----------|-------------|
| [Application Architecture](docs/architecture.md) | Deep dive into FSD architecture, layer responsibilities, and design decisions |
| [Development Setup Guide](docs/development-setup.md) | Comprehensive local development environment configuration |
| [API Integration Overview](api/README.md) | API client setup, endpoint documentation, and authentication |
| [Data Models Overview](models/README.md) | Complete reference for all 82 data models used in the application |

### Additional Resources

- `docs/testing.md` - Testing strategies and guidelines
- `docs/deployment.md` - Build and deployment procedures
- `docs/contributing.md` - Contribution guidelines and code standards

---

## Development Workflow

### Available Scripts

```bash
# Development
npm run dev              # Start development server with HMR
npm run dev:mock         # Start with mock API responses

# Building
npm run build            # Production build
npm run build:analyze    # Build with bundle analysis
npm run preview          # Preview production build locally

# Testing
npm run test             # Run unit tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Generate coverage report
npm run test:e2e         # Run end-to-end tests

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Fix auto-fixable lint issues
npm run format           # Format code with Prettier
npm run type-check       # Run TypeScript compiler checks

# Documentation
npm run docs:generate    # Generate API documentation
npm run storybook        # Launch Storybook component explorer
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/INSIGHT-123-category-builder-enhancement

# Make changes and commit
git add .
git commit -m "feat(categories): add nested condition support in query builder"

# Push and create PR
git push origin feature/INSIGHT-123-category-builder-enhancement
```

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `refactor:` - Code refactoring
- `test:` - Test additions/modifications
- `chore:` - Maintenance tasks

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REACT_APP_API_BASE_URL` | Yes | - | Base URL for Insight API |
| `REACT_APP_AUTH_DOMAIN` | Yes | - | Authentication service domain |

### Feature Flags

Control feature availability through configuration:

```typescript
// src/shared/config/features.ts
export const featureFlags = {
  enableSalesforce: process.env.REACT_APP_ENABLE_SALESFORCE === 'true',
  enableSapien: process.env.REACT_APP_ENABLE_SAPIEN === 'true',
  enableAdvancedQueries: process.env.REACT_APP_ENABLE_ADVANCED_QUERIES === 'true',
};
```

---

## Contributing

We welcome contributions! Please review our development guidelines:

1. **Fork** the repository and create your branch from `main`
2. **Follow** the Feature-Sliced Design architecture
3. **Write** tests for new functionality
4. **Ensure** all tests pass and linting rules are satisfied
5. **Submit** a pull request with a clear description

For detailed guidelines, see [docs/contributing.md](docs/contributing.md).

---

## Support

- **Issues**: Report bugs via GitHub Issues
- **Questions**: Reach out to the development team on Slack (#insight-category-ui)
- **Documentation**: Check the [Documentation Index](#documentation-index) for detailed guides

---

<p align="center">
  <strong>Built with ❤️ by the Insight Platform Team</strong>
</p>