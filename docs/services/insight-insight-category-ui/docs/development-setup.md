# Development Setup Guide

## Overview

This comprehensive guide provides step-by-step instructions for setting up the development environment for the **insight-insight-category-ui** service. This React/TypeScript frontend application powers the Insight voice analytics categorization system, enabling customers to create and manage categories and dictionaries for call analysis.

The application is built using modern frontend technologies including Redux for state management and Feature-Sliced Design (FSD) architecture, ensuring scalability and maintainability. This guide covers everything from initial setup through production builds.

## Prerequisites

### System Requirements

Before beginning the setup process, ensure your development machine meets the following requirements:

| Requirement | Minimum Version | Recommended Version |
|-------------|-----------------|---------------------|
| Node.js | 18.x LTS | 20.x LTS |
| npm | 9.x | 10.x |
| Git | 2.30+ | Latest |
| RAM | 8 GB | 16 GB |
| Disk Space | 2 GB | 5 GB |

### Required Software

#### Node.js and npm

Install Node.js using a version manager for flexibility across projects:

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal, then install Node.js
nvm install 20
nvm use 20
nvm alias default 20

# Verify installation
node --version  # Should output v20.x.x
npm --version   # Should output 10.x.x
```

#### Git Configuration

Configure Git with your credentials:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# For Windows users, configure line endings
git config --global core.autocrlf true

# For Mac/Linux users
git config --global core.autocrlf input
```

### IDE Setup (Recommended)

We recommend Visual Studio Code with the following extensions:

- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **TypeScript Importer** - Auto-import TypeScript modules
- **Redux DevTools** - Redux state debugging
- **GitLens** - Enhanced Git integration

Create a `.vscode/settings.json` file for consistent editor configuration:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "files.associations": {
    "*.css": "postcss"
  }
}
```

## Installation

### Cloning the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/insight-insight-category-ui.git

# Navigate to the project directory
cd insight-insight-category-ui

# Checkout the development branch
git checkout develop
```

### Installing Dependencies

Install all project dependencies using npm:

```bash
# Install dependencies
npm install

# If you encounter peer dependency issues, use:
npm install --legacy-peer-deps

# Verify installation by checking node_modules
ls -la node_modules | head -20
```

### Post-Installation Setup

After installing dependencies, run the setup scripts:

```bash
# Install Git hooks for pre-commit linting
npm run prepare

# Generate TypeScript types from API schemas
npm run generate:types

# Initialize local configuration
npm run setup:local
```

## Environment Configuration

### Environment Files

The application uses environment-specific configuration files. Create the necessary files based on your environment:

```bash
# Copy the example environment file
cp .env.example .env.local
```

### Configuration Variables

Configure the following environment variables in your `.env.local` file:

```bash
# API Configuration
REACT_APP_API_BASE_URL=https://api.dev.insight.company.com
REACT_APP_API_VERSION=v1

# Authentication
REACT_APP_AUTH_DOMAIN=auth.company.com
REACT_APP_AUTH_CLIENT_ID=your-client-id-here
REACT_APP_AUTH_AUDIENCE=https://api.insight.company.com

# Feature Flags
REACT_APP_ENABLE_SALESFORCE_INTEGRATION=true
REACT_APP_ENABLE_SAPIEN_INTEGRATION=true
REACT_APP_ENABLE_DEBUG_MODE=true

# Transcription Partner Configuration
REACT_APP_DEFAULT_TRANSCRIPTION_PARTNER=primary
REACT_APP_SUPPORTED_PARTNERS=primary,secondary,tertiary

# Analytics and Monitoring
REACT_APP_ANALYTICS_KEY=your-analytics-key
REACT_APP_SENTRY_DSN=https://your-sentry-dsn

# Development Settings
REACT_APP_MOCK_API=false
REACT_APP_LOG_LEVEL=debug
```

### Environment-Specific Configurations

| Variable | Development | Staging | Production |
|----------|------------|---------|------------|
| `REACT_APP_API_BASE_URL` | `localhost:3001` | `api.staging.insight.com` | `api.insight.com` |
| `REACT_APP_ENABLE_DEBUG_MODE` | `true` | `true` | `false` |
| `REACT_APP_LOG_LEVEL` | `debug` | `info` | `error` |

### Validating Configuration

Run the configuration validation script to ensure all required variables are set:

```bash
npm run validate:env

# Expected output:
# ✓ REACT_APP_API_BASE_URL is set
# ✓ REACT_APP_AUTH_DOMAIN is set
# ✓ All required environment variables are configured
```

## Running Locally

### Starting the Development Server

Launch the application in development mode:

```bash
# Start the development server
npm run start

# Or with specific environment
npm run start:dev
npm run start:staging
```

The application will be available at `http://localhost:3000` with hot module replacement enabled.

### Development Server Options

```bash
# Start with custom port
PORT=3001 npm run start

# Start with HTTPS enabled
HTTPS=true npm run start

# Start with specific API mock server
npm run start:mock

# Start with debug logging
DEBUG=true npm run start
```

### Connecting to Backend Services

The application integrates with multiple backend services. Configure proxy settings in `setupProxy.js`:

```javascript
// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Category API proxy
  app.use(
    '/api/categories',
    createProxyMiddleware({
      target: process.env.REACT_APP_API_BASE_URL,
      changeOrigin: true,
      pathRewrite: {
        '^/api/categories': '/v1/categories'
      }
    })
  );

  // Salesforce integration proxy
  app.use(
    '/api/salesforce',
    createProxyMiddleware({
      target: process.env.SALESFORCE_API_URL,
      changeOrigin: true
    })
  );

  // Sapien user system proxy
  app.use(
    '/api/sapien',
    createProxyMiddleware({
      target: process.env.SAPIEN_API_URL,
      changeOrigin: true
    })
  );
};
```

### Mock API Server

For offline development or testing without backend dependencies:

```bash
# Start the mock API server
npm run mock:server

# In a separate terminal, start the app with mocks
REACT_APP_MOCK_API=true npm run start
```

## Webpack Configuration

### Configuration Overview

The application uses a customized Webpack configuration through Create React App with CRACO (Create React App Configuration Override):

```javascript
// craco.config.js
const path = require('path');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  webpack: {
    alias: {
      '@app': path.resolve(__dirname, 'src/app'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@widgets': path.resolve(__dirname, 'src/widgets'),
      '@features': path.resolve(__dirname, 'src/features'),
      '@entities': path.resolve(__dirname, 'src/entities'),
      '@shared': path.resolve(__dirname, 'src/shared')
    },
    plugins: {
      add: process.env.ANALYZE === 'true' 
        ? [new BundleAnalyzerPlugin()] 
        : []
    },
    configure: (webpackConfig) => {
      // Feature-Sliced Design path resolution
      webpackConfig.resolve.modules = [
        path.resolve(__dirname, 'src'),
        'node_modules'
      ];

      // Source map configuration for development
      if (process.env.NODE_ENV === 'development') {
        webpackConfig.devtool = 'eval-source-map';
      }

      return webpackConfig;
    }
  },
  style: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer')
      ]
    }
  }
};
```

### Code Splitting Configuration

Optimize bundle size with route-based code splitting:

```typescript
// src/app/routes/index.tsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { LoadingSpinner } from '@shared/ui';

// Lazy-loaded route components
const CategoryManagement = lazy(() => 
  import('@pages/category-management')
);
const TemplateSystem = lazy(() => 
  import('@pages/template-system')
);
const UserAssignment = lazy(() => 
  import('@pages/user-assignment')
);
const PromptManagement = lazy(() => 
  import('@pages/prompt-management')
);

export const AppRoutes = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <Routes>
      <Route path="/categories/*" element={<CategoryManagement />} />
      <Route path="/templates/*" element={<TemplateSystem />} />
      <Route path="/assignments/*" element={<UserAssignment />} />
      <Route path="/prompts/*" element={<PromptManagement />} />
    </Routes>
  </Suspense>
);
```

### Bundle Analysis

Analyze the production bundle to identify optimization opportunities:

```bash
# Generate bundle analysis report
npm run build:analyze

# View the report (opens in browser)
# Report shows:
# - Bundle size breakdown
# - Duplicate dependencies
# - Unused exports
```

## Testing with Jest

### Test Configuration

The project uses Jest with React Testing Library. Configuration is defined in `jest.config.js`:

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  moduleNameMapper: {
    '^@app/(.*)$': '<rootDir>/src/app/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@widgets/(.*)$': '<rootDir>/src/widgets/$1',
    '^@features/(.*)$': '<rootDir>/src/features/$1',
    '^@entities/(.*)$': '<rootDir>/src/entities/$1',
    '^@shared/(.*)$': '<rootDir>/src/shared/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/index.tsx'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  testMatch: [
    '**/__tests__/**/*.{ts,tsx}',
    '**/*.{spec,test}.{ts,tsx}'
  ]
};
```

### Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run specific test file
npm run test -- --testPathPattern="CategoryForm"

# Run tests matching a pattern
npm run test -- --testNamePattern="should validate query syntax"
```

### Writing Tests

Example test for the category creation feature:

```typescript
// src/features/category-creation/__tests__/CategoryForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { CategoryForm } from '../ui/CategoryForm';
import { categorySlice } from '../model/categorySlice';

const createTestStore = (preloadedState = {}) => 
  configureStore({
    reducer: {
      category: categorySlice.reducer
    },
    preloadedState
  });

describe('CategoryForm', () => {
  const user = userEvent.setup();

  it('should render category creation form', () => {
    render(
      <Provider store={createTestStore()}>
        <CategoryForm />
      </Provider>
    );

    expect(screen.getByLabelText(/category name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/query syntax/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
  });

  it('should validate complex query syntax', async () => {
    render(
      <Provider store={createTestStore()}>
        <CategoryForm />
      </Provider>
    );

    const queryInput = screen.getByLabelText(/query syntax/i);
    
    // Test invalid syntax
    await user.type(queryInput, 'AND OR invalid');
    await user.click(screen.getByRole('button', { name: /validate/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid query syntax/i)).toBeInTheDocument();
    });
  });

  it('should submit form with valid data', async () => {
    const onSubmit = jest.fn();
    
    render(
      <Provider store={createTestStore()}>
        <CategoryForm onSubmit={onSubmit} />
      </Provider>
    );

    await user.type(screen.getByLabelText(/category name/i), 'Test Category');
    await user.type(screen.getByLabelText(/query syntax/i), '"refund" AND "cancel"');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'Test Category',
        query: '"refund" AND "cancel"'
      });
    });
  });
});
```

### Testing Redux State

```typescript
// src/features/category-creation/__tests__/categorySlice.test.ts
import { categorySlice, createCategory, fetchCategories } from '../model/categorySlice';

describe('categorySlice', () => {
  const initialState = {
    categories: [],
    loading: false,
    error: null
  };

  it('should handle initial state', () => {
    expect(categorySlice.reducer(undefined, { type: 'unknown' }))
      .toEqual(initialState);
  });

  it('should handle createCategory.pending', () => {
    const action = { type: createCategory.pending.type };
    const state = categorySlice.reducer(initialState, action);
    
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('should handle createCategory.fulfilled', () => {
    const newCategory = { id: '1', name: 'Test', query: '"test"' };
    const action = { 
      type: createCategory.fulfilled.type,
      payload: newCategory 
    };
    const state = categorySlice.reducer(initialState, action);
    
    expect(state.loading).toBe(false);
    expect(state.categories).toContainEqual(newCategory);
  });
});
```

## Storybook Setup

### Configuration

Storybook is configured for component development and documentation:

```javascript
// .storybook/main.js
module.exports = {
  stories: [
    '../src/**/*.stories.mdx',
    '../src/**/*.stories.@(js|jsx|ts|tsx)'
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
    'storybook-addon-designs'
  ],
  framework: '@storybook/react',
  core: {
    builder: '@storybook/builder-webpack5'
  },
  webpackFinal: async (config) => {
    // Add path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@app': path.resolve(__dirname, '../src/app'),
      '@shared': path.resolve(__dirname, '../src/shared'),
      '@features': path.resolve(__dirname, '../src/features'),
      '@entities': path.resolve(__dirname, '../src/entities')
    };
    return config;
  }
};
```

### Running Storybook

```bash
# Start Storybook development server
npm run storybook

# Build static Storybook for deployment
npm run build-storybook

# Run Storybook tests
npm run test-storybook
```

Storybook will be available at `http://localhost:6006`.

### Writing Stories

Example component story:

```typescript
// src/shared/ui/QueryEditor/QueryEditor.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { QueryEditor } from './QueryEditor';

const meta: Meta<typeof QueryEditor> = {
  title: 'Shared/QueryEditor',
  component: QueryEditor,
  tags: ['autodocs'],
  argTypes: {
    value: {
      description: 'Current query string',
      control: 'text'
    },
    onChange: {
      description: 'Callback when query changes',
      action: 'changed'
    },
    onValidate: {
      description: 'Callback when validation is triggered',
      action: 'validated'
    }
  }
};

export default meta;
type Story = StoryObj<typeof QueryEditor>;

export const Default: Story = {
  args: {
    value: '',
    placeholder: 'Enter query syntax...'
  }
};

export const WithQuery: Story = {
  args: {
    value: '"customer service" AND ("refund" OR "return")',
    placeholder: 'Enter query syntax...'
  }
};

export const WithValidationError: Story = {
  args: {
    value: 'AND OR invalid syntax',
    error: 'Invalid query: unexpected operator'
  }
};

export const ComplexQuery: Story = {
  args: {
    value: `("cancellation" OR "cancel") AND NOT "renewal" 
    NEAR/5 ("policy" OR "subscription")`,
    showLineNumbers: true
  }
};
```

## Building for Production

### Production Build Process

```bash
# Create optimized production build
npm run build

# Build with source maps for debugging
npm run build:sourcemap

# Build with bundle analysis
npm run build:analyze
```

### Build Configuration

Production builds are optimized with the following settings:

```javascript
// Production optimizations in craco.config.js
module.exports = {
  webpack: {
    configure: (webpackConfig, { env }) => {
      if (env === 'production') {
        // Enable tree shaking
        webpackConfig.optimization.usedExports = true;
        
        // Configure chunk splitting
        webpackConfig.optimization.splitChunks = {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all'
            },
            redux: {
              test: /[\\/]node_modules[\\/](@reduxjs|redux|react-redux)[\\/]/,
              name: 'redux',
              chunks: 'all'
            }
          }
        };
        
        // Minimize bundle size
        webpackConfig.optimization.minimize = true;
      }
      return webpackConfig;
    }
  }
};
```

### Build Output

After building, the `build/` directory contains:

```
build/
├── static/
│   ├── css/
│   │   ├── main.[hash].css
│   │   └── main.[hash].css.map
│   ├── js/
│   │   ├── main.[hash].js
│   │   ├── vendors.[hash].js
│   │   ├── redux.[hash].js
│   │   └── [chunk].[hash].js
│   └── media/
│       └── [assets]
├── index.html
├── asset-manifest.json
└── robots.txt
```

### Deployment Verification

```bash
# Serve production build locally
npm install -g serve
serve -s build

# Run Lighthouse audit
npm run lighthouse

# Verify build integrity
npm run verify:build
```

### Build Troubleshooting

Common build issues and solutions:

| Issue | Solution |
|-------|----------|
| Out of memory | Increase Node memory: `NODE_OPTIONS=--max_old_space_size=4096 npm run build` |
| TypeScript errors | Run `npm run type-check` before building |
| Missing environment variables | Ensure `.env.production` is configured |
| Large bundle size | Run `npm run build:analyze` and optimize imports |

## Additional Resources

- [Feature-Sliced Design Documentation](https://feature-sliced.design/)
- [Redux Toolkit Best Practices](https://redux-toolkit.js.org/usage/usage-guide)
- [React Testing Library Guides](https://testing-library.com/docs/react-testing-library/intro/)
- [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)

## Getting Help

If you encounter issues during setup:

1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Search existing issues in the repository
3. Contact the development team on Slack: `#insight-category-ui-support`
4. Create a new issue with the `setup-help` label