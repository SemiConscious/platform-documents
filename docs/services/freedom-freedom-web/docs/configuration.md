# Configuration Guide for Freedom-Freedom-Web

## Overview

Freedom-Freedom-Web is a modern web application built with contemporary frontend technologies. This comprehensive configuration guide covers all aspects of setting up and configuring the application across different environments, from local development to production deployment.

The configuration system follows a layered approach:
1. **Environment Variables** - Runtime configuration via `.env` files
2. **Webpack Configuration** - Build-time bundling and optimization
3. **ESLint Configuration** - Code quality and style enforcement
4. **PostCSS Configuration** - CSS processing and transformations
5. **Jest Configuration** - Testing framework setup

This guide provides detailed explanations for each configuration layer, ensuring your development team can maintain consistent environments and troubleshoot issues effectively.

---

## Environment Variables

Environment variables are the primary mechanism for configuring Freedom-Freedom-Web across different deployment environments. These variables control API endpoints, feature flags, authentication settings, and third-party service integrations.

### Core Application Variables

| Variable Name | Type | Default | Required | Description |
|--------------|------|---------|----------|-------------|
| `NODE_ENV` | string | `development` | Yes | Application environment mode. Controls build optimizations, logging levels, and feature availability. |
| `PORT` | number | `3000` | No | Port number for the development server. Production deployments typically use reverse proxy configuration. |
| `HOST` | string | `localhost` | No | Hostname for the development server binding. Use `0.0.0.0` for external access. |
| `PUBLIC_URL` | string | `/` | No | Base URL path for the application. Used when deploying to a subdirectory. |
| `GENERATE_SOURCEMAP` | boolean | `true` | No | Whether to generate source maps in production builds. Disable for enhanced security. |
| `BUILD_PATH` | string | `build` | No | Output directory for production build artifacts. |

### API Configuration Variables

| Variable Name | Type | Default | Required | Description |
|--------------|------|---------|----------|-------------|
| `REACT_APP_API_URL` | string | - | Yes | Base URL for the backend API server. Must include protocol (http/https). |
| `REACT_APP_API_VERSION` | string | `v1` | No | API version prefix for endpoint construction. |
| `REACT_APP_API_TIMEOUT` | number | `30000` | No | Request timeout in milliseconds for API calls. |
| `REACT_APP_WEBSOCKET_URL` | string | - | No | WebSocket server URL for real-time features. |
| `REACT_APP_GRAPHQL_ENDPOINT` | string | - | No | GraphQL endpoint URL if using GraphQL API. |

### Authentication Variables

| Variable Name | Type | Default | Required | Description |
|--------------|------|---------|----------|-------------|
| `REACT_APP_AUTH_DOMAIN` | string | - | Yes | Authentication provider domain (e.g., Auth0, Okta). |
| `REACT_APP_AUTH_CLIENT_ID` | string | - | Yes | OAuth client identifier for the application. |
| `REACT_APP_AUTH_AUDIENCE` | string | - | No | API audience identifier for access token scope. |
| `REACT_APP_AUTH_REDIRECT_URI` | string | - | Yes | OAuth callback URL after successful authentication. |
| `REACT_APP_AUTH_LOGOUT_URI` | string | - | No | Redirect URL after logout. Defaults to application root. |
| `REACT_APP_SESSION_TIMEOUT` | number | `3600000` | No | Session timeout in milliseconds (default: 1 hour). |

### Feature Flags

| Variable Name | Type | Default | Required | Description |
|--------------|------|---------|----------|-------------|
| `REACT_APP_FEATURE_ANALYTICS` | boolean | `false` | No | Enable/disable analytics tracking functionality. |
| `REACT_APP_FEATURE_DARK_MODE` | boolean | `true` | No | Enable/disable dark mode theme toggle. |
| `REACT_APP_FEATURE_PWA` | boolean | `false` | No | Enable Progressive Web App functionality. |
| `REACT_APP_FEATURE_NOTIFICATIONS` | boolean | `true` | No | Enable browser push notifications. |
| `REACT_APP_FEATURE_EXPERIMENTAL` | boolean | `false` | No | Enable experimental features for beta testing. |

### Third-Party Service Integration

| Variable Name | Type | Default | Required | Description |
|--------------|------|---------|----------|-------------|
| `REACT_APP_GOOGLE_ANALYTICS_ID` | string | - | No | Google Analytics tracking ID (GA4 format: G-XXXXXXXXXX). |
| `REACT_APP_SENTRY_DSN` | string | - | No | Sentry error tracking Data Source Name. |
| `REACT_APP_HOTJAR_ID` | string | - | No | Hotjar site ID for behavior analytics. |
| `REACT_APP_STRIPE_PUBLIC_KEY` | string | - | No | Stripe publishable key for payment processing. |
| `REACT_APP_MAPBOX_TOKEN` | string | - | No | Mapbox access token for map components. |
| `REACT_APP_CLOUDINARY_CLOUD_NAME` | string | - | No | Cloudinary cloud name for image management. |

---

## Webpack Configuration

Freedom-Freedom-Web uses Webpack 5 for module bundling with optimized configurations for development and production environments.

### Base Configuration (`webpack.config.js`)

```javascript
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const Dotenv = require('dotenv-webpack');

const isProduction = process.env.NODE_ENV === 'production';
const shouldAnalyze = process.env.ANALYZE === 'true';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  
  entry: {
    main: './src/index.js',
    // Additional entry points for code splitting
    vendor: ['react', 'react-dom', 'react-router-dom'],
  },
  
  output: {
    path: path.resolve(__dirname, process.env.BUILD_PATH || 'build'),
    filename: isProduction 
      ? 'static/js/[name].[contenthash:8].js' 
      : 'static/js/[name].bundle.js',
    chunkFilename: isProduction
      ? 'static/js/[name].[contenthash:8].chunk.js'
      : 'static/js/[name].chunk.js',
    publicPath: process.env.PUBLIC_URL || '/',
    clean: true,
  },
  
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@services': path.resolve(__dirname, 'src/services'),
      '@assets': path.resolve(__dirname, 'src/assets'),
      '@styles': path.resolve(__dirname, 'src/styles'),
    },
  },
  
  module: {
    rules: [
      // JavaScript/TypeScript processing
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', { targets: 'defaults' }],
              ['@babel/preset-react', { runtime: 'automatic' }],
              '@babel/preset-typescript',
            ],
            plugins: [
              '@babel/plugin-transform-runtime',
              isProduction && 'transform-remove-console',
            ].filter(Boolean),
            cacheDirectory: true,
          },
        },
      },
      
      // CSS/SCSS processing
      {
        test: /\.(css|scss|sass)$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          {
            loader: 'css-loader',
            options: {
              modules: {
                auto: /\.module\.\w+$/,
                localIdentName: isProduction 
                  ? '[hash:base64:8]' 
                  : '[name]__[local]--[hash:base64:5]',
              },
              importLoaders: 2,
            },
          },
          'postcss-loader',
          'sass-loader',
        ],
      },
      
      // Asset handling
      {
        test: /\.(png|jpg|jpeg|gif|webp)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 10 * 1024, // 10KB
          },
        },
        generator: {
          filename: 'static/images/[name].[hash:8][ext]',
        },
      },
      
      // SVG handling with SVGR
      {
        test: /\.svg$/,
        use: ['@svgr/webpack', 'url-loader'],
      },
      
      // Font handling
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/fonts/[name].[hash:8][ext]',
        },
      },
    ],
  },
  
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
      favicon: './public/favicon.ico',
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true,
      } : false,
    }),
    
    new Dotenv({
      systemvars: true,
      safe: true,
      defaults: true,
    }),
    
    isProduction && new MiniCssExtractPlugin({
      filename: 'static/css/[name].[contenthash:8].css',
      chunkFilename: 'static/css/[name].[contenthash:8].chunk.css',
    }),
    
    shouldAnalyze && new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      reportFilename: 'bundle-report.html',
    }),
  ].filter(Boolean),
  
  optimization: {
    minimize: isProduction,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
          },
          output: {
            comments: false,
          },
        },
        extractComments: false,
      }),
      new CssMinimizerPlugin(),
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 20,
        },
        common: {
          minChunks: 2,
          priority: 10,
          reuseExistingChunk: true,
        },
      },
    },
    runtimeChunk: 'single',
  },
  
  devServer: {
    port: process.env.PORT || 3000,
    host: process.env.HOST || 'localhost',
    hot: true,
    open: true,
    historyApiFallback: true,
    compress: true,
    proxy: {
      '/api': {
        target: process.env.REACT_APP_API_URL,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  
  devtool: isProduction 
    ? (process.env.GENERATE_SOURCEMAP === 'true' ? 'source-map' : false)
    : 'eval-cheap-module-source-map',
    
  performance: {
    hints: isProduction ? 'warning' : false,
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  },
};
```

### Webpack Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ANALYZE` | boolean | `false` | Enable webpack-bundle-analyzer output |
| `WEBPACK_DEV_SERVER_PORT` | number | `3000` | Development server port override |
| `INLINE_RUNTIME_CHUNK` | boolean | `true` | Inline webpack runtime in HTML |
| `IMAGE_INLINE_SIZE_LIMIT` | number | `10000` | Max size (bytes) for base64 inlining |

---

## Development vs Production Configuration

### Development Environment

Development configuration prioritizes fast rebuilds, debugging capabilities, and developer experience.

```env
# .env.development
NODE_ENV=development
PORT=3000
HOST=localhost

# API Configuration
REACT_APP_API_URL=http://localhost:8080
REACT_APP_API_VERSION=v1
REACT_APP_API_TIMEOUT=60000
REACT_APP_WEBSOCKET_URL=ws://localhost:8080/ws

# Authentication (Development)
REACT_APP_AUTH_DOMAIN=dev-freedom.auth0.com
REACT_APP_AUTH_CLIENT_ID=dev_client_id_here
REACT_APP_AUTH_REDIRECT_URI=http://localhost:3000/callback
REACT_APP_AUTH_LOGOUT_URI=http://localhost:3000

# Features
REACT_APP_FEATURE_ANALYTICS=false
REACT_APP_FEATURE_DARK_MODE=true
REACT_APP_FEATURE_PWA=false
REACT_APP_FEATURE_NOTIFICATIONS=true
REACT_APP_FEATURE_EXPERIMENTAL=true

# Development Tools
GENERATE_SOURCEMAP=true
REACT_APP_DEBUG_MODE=true
REACT_APP_LOG_LEVEL=debug

# Mock Services (Development Only)
REACT_APP_USE_MOCKS=true
REACT_APP_MOCK_DELAY=500
```

### Staging Environment

Staging mirrors production configuration with additional debugging capabilities.

```env
# .env.staging
NODE_ENV=production
PUBLIC_URL=https://staging.freedom-web.example.com

# API Configuration
REACT_APP_API_URL=https://api-staging.freedom-web.example.com
REACT_APP_API_VERSION=v1
REACT_APP_API_TIMEOUT=30000
REACT_APP_WEBSOCKET_URL=wss://api-staging.freedom-web.example.com/ws

# Authentication (Staging)
REACT_APP_AUTH_DOMAIN=staging-freedom.auth0.com
REACT_APP_AUTH_CLIENT_ID=staging_client_id_here
REACT_APP_AUTH_AUDIENCE=https://api-staging.freedom-web.example.com
REACT_APP_AUTH_REDIRECT_URI=https://staging.freedom-web.example.com/callback
REACT_APP_AUTH_LOGOUT_URI=https://staging.freedom-web.example.com

# Features
REACT_APP_FEATURE_ANALYTICS=true
REACT_APP_FEATURE_DARK_MODE=true
REACT_APP_FEATURE_PWA=true
REACT_APP_FEATURE_NOTIFICATIONS=true
REACT_APP_FEATURE_EXPERIMENTAL=true

# Third-Party Services (Staging)
REACT_APP_GOOGLE_ANALYTICS_ID=G-STAGING1234
REACT_APP_SENTRY_DSN=https://staging@sentry.io/staging-project

# Build Configuration
GENERATE_SOURCEMAP=true
REACT_APP_DEBUG_MODE=false
REACT_APP_LOG_LEVEL=warn
```

### Production Environment

Production configuration emphasizes security, performance, and stability.

```env
# .env.production
NODE_ENV=production
PUBLIC_URL=https://freedom-web.example.com

# API Configuration
REACT_APP_API_URL=https://api.freedom-web.example.com
REACT_APP_API_VERSION=v1
REACT_APP_API_TIMEOUT=30000
REACT_APP_WEBSOCKET_URL=wss://api.freedom-web.example.com/ws

# Authentication (Production)
REACT_APP_AUTH_DOMAIN=freedom.auth0.com
REACT_APP_AUTH_CLIENT_ID=prod_client_id_here
REACT_APP_AUTH_AUDIENCE=https://api.freedom-web.example.com
REACT_APP_AUTH_REDIRECT_URI=https://freedom-web.example.com/callback
REACT_APP_AUTH_LOGOUT_URI=https://freedom-web.example.com

# Features
REACT_APP_FEATURE_ANALYTICS=true
REACT_APP_FEATURE_DARK_MODE=true
REACT_APP_FEATURE_PWA=true
REACT_APP_FEATURE_NOTIFICATIONS=true
REACT_APP_FEATURE_EXPERIMENTAL=false

# Third-Party Services (Production)
REACT_APP_GOOGLE_ANALYTICS_ID=G-PRODUCTION12
REACT_APP_SENTRY_DSN=https://prod@sentry.io/prod-project
REACT_APP_HOTJAR_ID=1234567
REACT_APP_STRIPE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx

# Build Configuration
GENERATE_SOURCEMAP=false
REACT_APP_DEBUG_MODE=false
REACT_APP_LOG_LEVEL=error
```

---

## ESLint Configuration

The ESLint configuration ensures consistent code quality and catches potential errors during development.

### ESLint Configuration File (`.eslintrc.js`)

```javascript
module.exports = {
  root: true,
  
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true,
  },
  
  parser: '@typescript-eslint/parser',
  
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
    project: './tsconfig.json',
  },
  
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier',
  ],
  
  plugins: [
    'react',
    'react-hooks',
    '@typescript-eslint',
    'jsx-a11y',
    'import',
  ],
  
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json',
      },
      alias: {
        map: [
          ['@', './src'],
          ['@components', './src/components'],
          ['@hooks', './src/hooks'],
          ['@utils', './src/utils'],
          ['@services', './src/services'],
        ],
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },
  
  rules: {
    // React Rules
    'react/prop-types': 'off',
    'react/react-in-jsx-scope': 'off',
    'react/jsx-uses-react': 'off',
    'react/jsx-props-no-spreading': 'warn',
    'react/jsx-filename-extension': ['error', { 
      extensions: ['.jsx', '.tsx'] 
    }],
    'react/function-component-definition': ['error', {
      namedComponents: 'arrow-function',
      unnamedComponents: 'arrow-function',
    }],
    
    // React Hooks Rules
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // TypeScript Rules
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { 
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    }],
    '@typescript-eslint/consistent-type-imports': ['error', {
      prefer: 'type-imports',
    }],
    
    // Import Rules
    'import/order': ['error', {
      groups: [
        'builtin',
        'external',
        'internal',
        'parent',
        'sibling',
        'index',
        'type',
      ],
      'newlines-between': 'always',
      alphabetize: {
        order: 'asc',
        caseInsensitive: true,
      },
    }],
    'import/no-duplicates': 'error',
    'import/no-unresolved': 'error',
    
    // Accessibility Rules
    'jsx-a11y/anchor-is-valid': ['error', {
      components: ['Link'],
      specialLink: ['to'],
    }],
    
    // General Rules
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
  },
  
  overrides: [
    {
      files: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx'],
      env: {
        jest: true,
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        '@typescript-eslint/no-non-null-assertion': 'off',
      },
    },
  ],
  
  ignorePatterns: [
    'build/',
    'dist/',
    'coverage/',
    'node_modules/',
    '*.config.js',
    'public/',
  ],
};
```

---

## PostCSS Configuration

PostCSS configuration handles CSS transformations, autoprefixing, and modern CSS features.

### PostCSS Configuration File (`postcss.config.js`)

```javascript
const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  plugins: [
    // Import CSS files
    require('postcss-import')({
      path: ['src/styles'],
    }),
    
    // Enable nesting syntax
    require('postcss-nested'),
    
    // Custom media queries
    require('postcss-custom-media')({
      importFrom: 'src/styles/media-queries.css',
    }),
    
    // CSS Custom Properties fallbacks
    require('postcss-custom-properties')({
      preserve: true,
      importFrom: 'src/styles/variables.css',
    }),
    
    // Modern CSS features
    require('postcss-preset-env')({
      stage: 2,
      features: {
        'nesting-rules': true,
        'custom-properties': true,
        'custom-media-queries': true,
        'gap-properties': true,
        'logical-properties-and-values': true,
      },
      autoprefixer: {
        flexbox: 'no-2009',
        grid: 'autoplace',
      },
      browsers: [
        '>0.2%',
        'not dead',
        'not op_mini all',
      ],
    }),
    
    // PurgeCSS for production
    isProduction && require('@fullhuman/postcss-purgecss')({
      content: [
        './src/**/*.{js,jsx,ts,tsx}',
        './public/index.html',
      ],
      defaultExtractor: (content) => content.match(/[\w-/:]+(?<!:)/g) || [],
      safelist: {
        standard: [/^html/, /^body/],
        deep: [/modal/, /tooltip/, /dropdown/],
        greedy: [/^animate-/],
      },
    }),
    
    // CSS Minification
    isProduction && require('cssnano')({
      preset: ['default', {
        discardComments: { removeAll: true },
        normalizeWhitespace: true,
        colormin: true,
        reduceIdents: false,
      }],
    }),
  ].filter(Boolean),
};
```

### CSS Variables File (`src/styles/variables.css`)

```css
:root {
  /* Colors - Primary */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  
  /* Colors - Neutral */
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-500: #6b7280;
  --color-gray-900: #111827;
  
  /* Typography */
  --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-family-mono: 'Fira Code', Consolas, monospace;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Borders */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.5rem;
  --border-radius-lg: 1rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
  --transition-slow: 500ms ease;
}
```

---

## Jest Testing Setup

Jest configuration provides comprehensive testing capabilities for unit, integration, and snapshot testing.

### Jest Configuration File (`jest.config.js`)

```javascript
module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.ts',
  ],
  
  // Module resolution
  moduleNameMapper: {
    // Path aliases
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@assets/(.*)$': '<rootDir>/src/assets/$1',
    
    // Static assets
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/src/__mocks__/fileMock.js',
  },
  
  // Transform configuration
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }],
        '@babel/preset-typescript',
      ],
    }],
  },
  
  // File extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // Test patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}',
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/__mocks__/**',
  ],
  
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  
  coverageReporters: ['text', 'lcov', 'html'],
  
  // Performance
  maxWorkers: '50%',
  
  // Globals
  globals: {
    'ts-jest': {
      isolatedModules: true,
    },
  },
  
  // Timeouts
  testTimeout: 10000,
  
  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname',
  ],
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Verbose output
  verbose: true,
};
```

### Test Setup File (`src/setupTests.ts`)

```typescript
import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { server } from './__mocks__/server';

// Configure Testing Library
configure({
  testIdAttribute: 'data-testid',
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = jest.fn();
  disconnect = jest.fn();
  unobserve = jest.fn();
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: MockIntersectionObserver,
});

// Mock ResizeObserver
class MockResizeObserver {
  observe = jest.fn();
  disconnect = jest.fn();
  unobserve = jest.fn();
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: MockResizeObserver,
});

// Setup MSW
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Global test utilities
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
};
```

---

## Security Considerations

### Sensitive Values Protection

1. **Never commit sensitive values** - All `.env` files containing real credentials must be in `.gitignore`
2. **Use environment-specific files** - Separate configurations prevent accidental credential exposure
3. **Rotate credentials regularly** - Especially after team member departures
4. **Audit environment variable access** - Log when sensitive variables are accessed

### Security Best Practices

| Practice | Implementation |
|----------|----------------|
| API Keys | Store in environment variables, never in code |
| Authentication Secrets | Use secure secret management (Vault, AWS Secrets Manager) |
| Source Maps | Disable in production (`GENERATE_SOURCEMAP=false`) |
| Console Logging | Remove in production builds |
| HTTPS | Enforce HTTPS for all production URLs |
| CSP Headers | Configure Content Security Policy at server level |

### Example `.gitignore` for Environment Files

```gitignore
# Environment files
.env
.env.local
.env.*.local
.env.development.local
.env.staging.local
.env.production.local

# Keep example files
!.env.example
!.env.development.example
```

---

## Troubleshooting Common Configuration Issues

### Issue: Environment Variables Not Loading

**Symptoms:** `process.env.REACT_APP_*` returns `undefined`

**Solutions:**
1. Ensure variable name starts with `REACT_APP_`
2. Restart development server after changes
3. Verify `.env` file is in project root
4. Check for syntax errors in `.env` file

### Issue: Webpack Build Fails

**Symptoms:** Build errors related to module resolution

**Solutions:**
1. Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Clear webpack cache: `rm -rf .cache`
3. Verify all path aliases match between `webpack.config.js` and `tsconfig.json`

### Issue: ESLint Not Working

**Symptoms:** Linting errors not appearing in IDE

**Solutions:**
1. Ensure ESLint extension is installed
2. Verify `.eslintrc.js` syntax
3. Check that `eslint` and plugins are installed
4. Restart IDE/editor

### Issue: Tests Failing After Configuration Change

**Symptoms:** Jest tests fail with module resolution errors

**Solutions:**
1. Clear Jest cache: `npm test -- --clearCache`
2. Verify `moduleNameMapper` matches webpack aliases
3. Check `transform` configuration for file types

---

## Complete Example `.env` File

```env
# ===========================================
# Freedom-Freedom-Web Configuration
# ===========================================
# Copy this file to .env.local and fill in values
# DO NOT commit .env.local to version control

# Application
NODE_ENV=development
PORT=3000
HOST=localhost
PUBLIC_URL=/
BUILD_PATH=build
GENERATE_SOURCEMAP=true

# API Configuration
REACT_APP_API_URL=http://localhost:8080
REACT_APP_API_VERSION=v1
REACT_APP_API_TIMEOUT=30000
REACT_APP_WEBSOCKET_URL=ws://localhost:8080/ws

# Authentication
REACT_APP_AUTH_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH_CLIENT_ID=your_client_id
REACT_APP_AUTH_AUDIENCE=https://your-api.example.com
REACT_APP_AUTH_REDIRECT_URI=http://localhost:3000/callback
REACT_APP_AUTH_LOGOUT_URI=http://localhost:3000
REACT_APP_SESSION_TIMEOUT=3600000

# Feature Flags
REACT_APP_FEATURE_ANALYTICS=false
REACT_APP_FEATURE_DARK_MODE=true
REACT_APP_FEATURE_PWA=false
REACT_APP_FEATURE_NOTIFICATIONS=true
REACT_APP_FEATURE_EXPERIMENTAL=false

# Third-Party Services
REACT_APP_GOOGLE_ANALYTICS_ID=
REACT_APP_SENTRY_DSN=
REACT_APP_HOTJAR_ID=
REACT_APP_STRIPE_PUBLIC_KEY=
REACT_APP_MAPBOX_TOKEN=
REACT_APP_CLOUDINARY_CLOUD_NAME=

# Development Settings
REACT_APP_DEBUG_MODE=true
REACT_APP_LOG_LEVEL=debug
REACT_APP_USE_MOCKS=false
```

---

This configuration guide provides a comprehensive foundation for configuring Freedom-Freedom-Web across all environments. For additional assistance or advanced configuration scenarios, consult the development team or refer to the individual tool documentation.