# Configuration Guide: natterbox-routing-policies

## Overview

The `natterbox-routing-policies` service is a modern React-based application designed for managing telephony routing policies within the Natterbox communication platform. This service handles the configuration and management of call routing rules, policies, and associated logic that determines how incoming and outgoing calls are processed and directed.

This configuration guide provides comprehensive documentation for all environment variables, webpack configurations, development server settings, and production build optimizations. The application follows Create React App (CRA) conventions with additional customizations for enterprise deployment scenarios.

### Configuration Philosophy

The service adopts a twelve-factor app methodology where configuration is strictly separated from code. All environment-specific settings are managed through environment variables, allowing the same codebase to be deployed across development, staging, and production environments without modification.

---

## Environment Variables

### Core Environment Variables

The following table documents all environment variables supported by the `natterbox-routing-policies` service:

| Variable Name | Description | Type | Default Value | Required | Example Values |
|---------------|-------------|------|---------------|----------|----------------|
| `HTTPS` | Enable HTTPS for localhost development server. When set to `true`, the development server will use a self-signed SSL certificate to serve content over HTTPS. This is essential for testing features that require secure contexts such as service workers, geolocation APIs, or secure cookie handling. | Boolean | `false` | No | `true`, `false` |
| `NODE_ENV` | Specifies the current environment mode. Automatically set by build scripts but can be overridden for testing purposes. | String | `development` | Yes (auto-set) | `development`, `production`, `test` |
| `PORT` | The port number on which the development server listens. | Number | `3000` | No | `3000`, `3001`, `8080` |
| `HOST` | The hostname for the development server to bind to. | String | `localhost` | No | `localhost`, `0.0.0.0`, `127.0.0.1` |
| `PUBLIC_URL` | The base URL path where the application will be served from. Used for generating correct asset paths in production builds. | String | `/` | No | `/`, `/routing-policies`, `https://cdn.example.com` |
| `BUILD_PATH` | Custom output directory for production builds. | String | `build` | No | `build`, `dist`, `output` |
| `CI` | Indicates if running in a Continuous Integration environment. Affects test behavior and build warnings. | Boolean | `false` | No | `true`, `false` |
| `GENERATE_SOURCEMAP` | Controls whether source maps are generated during production builds. Disable for security-sensitive deployments. | Boolean | `true` | No | `true`, `false` |
| `INLINE_RUNTIME_CHUNK` | Whether to inline the webpack runtime chunk. Helps with caching strategies. | Boolean | `true` | No | `true`, `false` |
| `IMAGE_INLINE_SIZE_LIMIT` | Maximum size in bytes for images to be inlined as base64 data URIs. | Number | `10000` | No | `10000`, `5000`, `0` |
| `FAST_REFRESH` | Enable React Fast Refresh for hot module replacement during development. | Boolean | `true` | No | `true`, `false` |
| `TSC_COMPILE_ON_ERROR` | Allow builds to complete even when TypeScript type errors are present. | Boolean | `false` | No | `true`, `false` |
| `ESLINT_NO_DEV_ERRORS` | Prevent ESLint errors from appearing as overlay in development. | Boolean | `false` | No | `true`, `false` |
| `DISABLE_ESLINT_PLUGIN` | Completely disable ESLint checking during builds. | Boolean | `false` | No | `true`, `false` |

### Application-Specific Variables

| Variable Name | Description | Type | Default Value | Required | Example Values |
|---------------|-------------|------|---------------|----------|----------------|
| `REACT_APP_API_BASE_URL` | Base URL for the Natterbox routing policies API backend. | String | None | Yes | `https://api.natterbox.com/v1`, `http://localhost:4000/api` |
| `REACT_APP_AUTH_DOMAIN` | Authentication provider domain for OAuth/OIDC flows. | String | None | Yes | `auth.natterbox.com`, `login.microsoftonline.com` |
| `REACT_APP_CLIENT_ID` | OAuth client identifier for authentication. | String | None | Yes | `abc123-def456-ghi789` |
| `REACT_APP_TENANT_ID` | Multi-tenant identifier for organization isolation. | String | None | Conditional | `tenant-uuid-here` |
| `REACT_APP_FEATURE_FLAGS_URL` | Endpoint for fetching feature flag configurations. | String | None | No | `https://flags.natterbox.com/api/flags` |
| `REACT_APP_ANALYTICS_ID` | Analytics tracking identifier (Google Analytics, Mixpanel, etc.). | String | None | No | `UA-XXXXX-Y`, `G-XXXXXXXXXX` |
| `REACT_APP_SENTRY_DSN` | Sentry error tracking Data Source Name for error monitoring. | String | None | No | `https://key@sentry.io/project` |
| `REACT_APP_VERSION` | Application version string, typically injected during CI/CD. | String | `0.0.0` | No | `1.2.3`, `2.0.0-beta.1` |
| `REACT_APP_ENVIRONMENT` | Human-readable environment label for UI display. | String | `development` | No | `development`, `staging`, `production` |
| `REACT_APP_LOG_LEVEL` | Minimum log level for client-side logging. | String | `warn` | No | `debug`, `info`, `warn`, `error` |

---

## Webpack Configuration

### Default Webpack Settings

The `natterbox-routing-policies` service uses Create React App's webpack configuration with the following notable defaults:

```javascript
// webpack.config.js (abstracted representation)
module.exports = {
  mode: process.env.NODE_ENV,
  devtool: process.env.NODE_ENV === 'production' 
    ? (process.env.GENERATE_SOURCEMAP === 'true' ? 'source-map' : false)
    : 'cheap-module-source-map',
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, process.env.BUILD_PATH || 'build'),
    filename: 'static/js/[name].[contenthash:8].js',
    chunkFilename: 'static/js/[name].[contenthash:8].chunk.js',
    publicPath: process.env.PUBLIC_URL || '/',
  },
  optimization: {
    minimize: process.env.NODE_ENV === 'production',
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
    runtimeChunk: process.env.INLINE_RUNTIME_CHUNK === 'false' ? 'single' : false,
  },
};
```

### Custom Webpack Extensions

For advanced customization without ejecting, use `react-app-rewired` or `craco`. Example `craco.config.js`:

```javascript
// craco.config.js
const path = require('path');

module.exports = {
  webpack: {
    alias: {
      '@components': path.resolve(__dirname, 'src/components'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@services': path.resolve(__dirname, 'src/services'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@types': path.resolve(__dirname, 'src/types'),
      '@store': path.resolve(__dirname, 'src/store'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@assets': path.resolve(__dirname, 'src/assets'),
    },
    configure: (webpackConfig) => {
      // Add any additional webpack configuration here
      return webpackConfig;
    },
  },
  eslint: {
    enable: process.env.DISABLE_ESLINT_PLUGIN !== 'true',
  },
};
```

---

## Development Server Setup

### Basic Development Server Configuration

The development server is powered by webpack-dev-server with the following configuration options:

```javascript
// Development server configuration
const devServerConfig = {
  host: process.env.HOST || 'localhost',
  port: parseInt(process.env.PORT, 10) || 3000,
  https: process.env.HTTPS === 'true',
  hot: process.env.FAST_REFRESH !== 'false',
  historyApiFallback: true,
  compress: true,
  client: {
    overlay: {
      errors: true,
      warnings: process.env.ESLINT_NO_DEV_ERRORS !== 'true',
    },
    progress: true,
  },
  proxy: {
    '/api': {
      target: process.env.REACT_APP_API_BASE_URL,
      changeOrigin: true,
      secure: false,
    },
  },
};
```

### Starting the Development Server

```bash
# Standard development start
npm start

# With HTTPS enabled
HTTPS=true npm start

# With custom port
PORT=3001 npm start

# With all custom options
HTTPS=true PORT=3001 HOST=0.0.0.0 npm start
```

---

## HTTPS Configuration

### Enabling HTTPS for Local Development

The `HTTPS` environment variable is the primary mechanism for enabling secure connections during local development. This is particularly important for:

1. **Service Worker Testing**: Service workers require a secure context (HTTPS or localhost)
2. **OAuth Redirect Testing**: Many OAuth providers require HTTPS redirect URIs
3. **Secure Cookie Testing**: Cookies with `Secure` flag only work over HTTPS
4. **Mixed Content Debugging**: Identifying mixed content issues before production

### Configuration Methods

#### Method 1: Environment Variable (Recommended)

```bash
# .env.local
HTTPS=true
```

#### Method 2: Command Line

```bash
# Unix/macOS/Linux
HTTPS=true npm start

# Windows (cmd)
set HTTPS=true && npm start

# Windows (PowerShell)
$env:HTTPS="true"; npm start
```

#### Method 3: Custom SSL Certificate

For using your own SSL certificate instead of the auto-generated self-signed certificate:

```bash
# .env.local
HTTPS=true
SSL_CRT_FILE=./certificates/localhost.crt
SSL_KEY_FILE=./certificates/localhost.key
```

### Generating Custom Certificates

```bash
# Using mkcert (recommended)
brew install mkcert  # macOS
mkcert -install
mkcert localhost 127.0.0.1 ::1

# Using OpenSSL
openssl req -x509 -newkey rsa:4096 -keyout localhost.key -out localhost.crt -days 365 -nodes -subj "/CN=localhost"
```

### Browser Trust Configuration

When using self-signed certificates, browsers will display security warnings. To bypass:

1. **Chrome**: Click "Advanced" → "Proceed to localhost (unsafe)"
2. **Firefox**: Click "Advanced" → "Accept the Risk and Continue"
3. **Safari**: Click "Show Details" → "visit this website"

For permanent trust, install the certificate in your system's trust store.

---

## Path Aliases

### TypeScript Path Aliases Configuration

Path aliases simplify imports and improve code maintainability. Configure in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@components/*": ["components/*"],
      "@hooks/*": ["hooks/*"],
      "@services/*": ["services/*"],
      "@utils/*": ["utils/*"],
      "@types/*": ["types/*"],
      "@store/*": ["store/*"],
      "@pages/*": ["pages/*"],
      "@assets/*": ["assets/*"],
      "@constants/*": ["constants/*"],
      "@context/*": ["context/*"],
      "@routing/*": ["routing/*"]
    }
  }
}
```

### Usage Examples

```typescript
// Before (relative imports)
import { Button } from '../../../components/common/Button';
import { useAuth } from '../../../hooks/useAuth';
import { RoutingPolicy } from '../../../types/routing';

// After (path aliases)
import { Button } from '@components/common/Button';
import { useAuth } from '@hooks/useAuth';
import { RoutingPolicy } from '@types/routing';
```

### Jest Path Alias Configuration

Ensure Jest recognizes path aliases in `jest.config.js` or `package.json`:

```json
{
  "jest": {
    "moduleNameMapper": {
      "^@components/(.*)$": "<rootDir>/src/components/$1",
      "^@hooks/(.*)$": "<rootDir>/src/hooks/$1",
      "^@services/(.*)$": "<rootDir>/src/services/$1",
      "^@utils/(.*)$": "<rootDir>/src/utils/$1",
      "^@types/(.*)$": "<rootDir>/src/types/$1",
      "^@store/(.*)$": "<rootDir>/src/store/$1",
      "^@pages/(.*)$": "<rootDir>/src/pages/$1",
      "^@assets/(.*)$": "<rootDir>/src/assets/$1"
    }
  }
}
```

---

## Jest Testing Configuration

### Complete Jest Configuration

```javascript
// jest.config.js
module.exports = {
  roots: ['<rootDir>/src'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/serviceWorker.ts',
    '!src/reportWebVitals.ts',
  ],
  setupFiles: ['react-app-polyfill/jsdom'],
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{spec,test}.{js,jsx,ts,tsx}',
  ],
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(js|jsx|mjs|cjs|ts|tsx)$': '<rootDir>/config/jest/babelTransform.js',
    '^.+\\.css$': '<rootDir>/config/jest/cssTransform.js',
    '^(?!.*\\.(js|jsx|mjs|cjs|ts|tsx|css|json)$)': '<rootDir>/config/jest/fileTransform.js',
  },
  transformIgnorePatterns: [
    '[/\\\\]node_modules[/\\\\].+\\.(js|jsx|mjs|cjs|ts|tsx)$',
    '^.+\\.module\\.(css|sass|scss)$',
  ],
  moduleNameMapper: {
    '^react-native$': 'react-native-web',
    '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
  },
  moduleFileExtensions: ['web.js', 'js', 'web.ts', 'ts', 'web.tsx', 'tsx', 'json', 'web.jsx', 'jsx', 'node'],
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname',
  ],
  resetMocks: true,
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

### Test Environment Variables

```bash
# .env.test
REACT_APP_API_BASE_URL=http://localhost:4000/api
REACT_APP_AUTH_DOMAIN=test.auth.local
REACT_APP_CLIENT_ID=test-client-id
REACT_APP_ENVIRONMENT=test
REACT_APP_LOG_LEVEL=error
```

### Running Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- --testPathPattern="RoutingPolicy"

# Run in CI mode
CI=true npm test

# Run with verbose output
npm test -- --verbose
```

---

## Production Build Settings

### Build Optimization Configuration

```bash
# .env.production
NODE_ENV=production
GENERATE_SOURCEMAP=false
INLINE_RUNTIME_CHUNK=true
IMAGE_INLINE_SIZE_LIMIT=10000

REACT_APP_API_BASE_URL=https://api.natterbox.com/v1
REACT_APP_AUTH_DOMAIN=auth.natterbox.com
REACT_APP_CLIENT_ID=production-client-id
REACT_APP_ENVIRONMENT=production
REACT_APP_LOG_LEVEL=error
REACT_APP_SENTRY_DSN=https://key@sentry.io/project
REACT_APP_ANALYTICS_ID=G-XXXXXXXXXX
```

### Build Commands

```bash
# Standard production build
npm run build

# Build with source maps (for debugging)
GENERATE_SOURCEMAP=true npm run build

# Build with custom output directory
BUILD_PATH=dist npm run build

# Analyze bundle size
npm run build
npx source-map-explorer 'build/static/js/*.js'
```

### Production Build Output Structure

```
build/
├── static/
│   ├── css/
│   │   ├── main.[hash].css
│   │   └── main.[hash].css.map
│   ├── js/
│   │   ├── main.[hash].js
│   │   ├── main.[hash].js.map
│   │   ├── vendors.[hash].js
│   │   └── runtime-main.[hash].js
│   └── media/
│       └── [asset files]
├── index.html
├── manifest.json
├── robots.txt
└── asset-manifest.json
```

---

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
NODE_ENV=development
HTTPS=false
PORT=3000
FAST_REFRESH=true

REACT_APP_API_BASE_URL=http://localhost:4000/api
REACT_APP_AUTH_DOMAIN=dev.auth.natterbox.local
REACT_APP_CLIENT_ID=dev-client-id-12345
REACT_APP_TENANT_ID=dev-tenant
REACT_APP_ENVIRONMENT=development
REACT_APP_LOG_LEVEL=debug
REACT_APP_FEATURE_FLAGS_URL=http://localhost:4001/flags
```

### Staging Environment

```bash
# .env.staging
NODE_ENV=production
GENERATE_SOURCEMAP=true

REACT_APP_API_BASE_URL=https://api-staging.natterbox.com/v1
REACT_APP_AUTH_DOMAIN=auth-staging.natterbox.com
REACT_APP_CLIENT_ID=staging-client-id-67890
REACT_APP_TENANT_ID=staging-tenant
REACT_APP_ENVIRONMENT=staging
REACT_APP_LOG_LEVEL=info
REACT_APP_SENTRY_DSN=https://staging-key@sentry.io/project
REACT_APP_FEATURE_FLAGS_URL=https://flags-staging.natterbox.com/api/flags
```

### Production Environment

```bash
# .env.production
NODE_ENV=production
GENERATE_SOURCEMAP=false

REACT_APP_API_BASE_URL=https://api.natterbox.com/v1
REACT_APP_AUTH_DOMAIN=auth.natterbox.com
REACT_APP_CLIENT_ID=prod-client-id-secure
REACT_APP_ENVIRONMENT=production
REACT_APP_LOG_LEVEL=error
REACT_APP_SENTRY_DSN=https://production-key@sentry.io/project
REACT_APP_ANALYTICS_ID=G-PROD-ANALYTICS
REACT_APP_FEATURE_FLAGS_URL=https://flags.natterbox.com/api/flags
```

---

## Security Considerations

### Sensitive Value Handling

⚠️ **Critical Security Guidelines**:

1. **Never commit `.env` files** containing sensitive values to version control
2. **Use `.env.example`** as a template with placeholder values
3. **Prefix client-side variables** with `REACT_APP_` only if they should be exposed to the browser
4. **Rotate secrets regularly**, especially OAuth client secrets

### Environment File Security

```bash
# .gitignore
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Only commit the example file
!.env.example
```

### Secret Management Best Practices

| Secret Type | Storage Recommendation | Rotation Frequency |
|-------------|----------------------|-------------------|
| OAuth Client ID | Environment variable | On compromise |
| OAuth Client Secret | Never in frontend | Monthly |
| API Keys | Secret manager | Quarterly |
| Sentry DSN | Environment variable | On compromise |
| Analytics ID | Environment variable | Rarely |

### Client-Side Security Notes

```typescript
// ❌ NEVER do this - secrets exposed to browser
const apiKey = process.env.REACT_APP_SECRET_API_KEY;

// ✅ Safe - public identifiers only
const clientId = process.env.REACT_APP_CLIENT_ID;
const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;
```

---

## Complete Example .env File

### .env.example (Commit this to repository)

```bash
# ===========================================
# Natterbox Routing Policies Configuration
# ===========================================
# Copy this file to .env.local and fill in values
# NEVER commit .env.local to version control
# ===========================================

# ------------------------------------
# Development Server Configuration
# ------------------------------------
# Enable HTTPS for local development (true/false)
HTTPS=false

# Development server port
PORT=3000

# Development server host
HOST=localhost

# Enable React Fast Refresh
FAST_REFRESH=true

# ------------------------------------
# Build Configuration
# ------------------------------------
# Generate source maps in production (true/false)
# Set to false for production deployments
GENERATE_SOURCEMAP=true

# Custom build output directory
BUILD_PATH=build

# Inline webpack runtime chunk
INLINE_RUNTIME_CHUNK=true

# Maximum image size for base64 inlining (bytes)
IMAGE_INLINE_SIZE_LIMIT=10000

# ------------------------------------
# ESLint Configuration
# ------------------------------------
# Disable ESLint errors in development overlay
ESLINT_NO_DEV_ERRORS=false

# Completely disable ESLint plugin
DISABLE_ESLINT_PLUGIN=false

# Allow builds with TypeScript errors
TSC_COMPILE_ON_ERROR=false

# ------------------------------------
# Application Configuration
# ------------------------------------
# API base URL (required)
REACT_APP_API_BASE_URL=http://localhost:4000/api

# Authentication domain (required)
REACT_APP_AUTH_DOMAIN=auth.example.com

# OAuth client ID (required)
REACT_APP_CLIENT_ID=your-client-id-here

# Tenant ID for multi-tenant setups
REACT_APP_TENANT_ID=your-tenant-id

# Environment label for UI
REACT_APP_ENVIRONMENT=development

# ------------------------------------
# Monitoring & Analytics
# ------------------------------------
# Sentry DSN for error tracking
REACT_APP_SENTRY_DSN=

# Analytics tracking ID
REACT_APP_ANALYTICS_ID=

# Feature flags endpoint
REACT_APP_FEATURE_FLAGS_URL=

# ------------------------------------
# Logging
# ------------------------------------
# Log level: debug, info, warn, error
REACT_APP_LOG_LEVEL=debug

# ------------------------------------
# Version Information
# ------------------------------------
# Application version (usually set by CI/CD)
REACT_APP_VERSION=0.0.0-development
```

---

## Docker Configuration

### Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

ARG REACT_APP_API_BASE_URL
ARG REACT_APP_AUTH_DOMAIN
ARG REACT_APP_CLIENT_ID
ARG REACT_APP_ENVIRONMENT
ARG REACT_APP_VERSION

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  natterbox-routing-policies:
    build:
      context: .
      args:
        - REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL}
        - REACT_APP_AUTH_DOMAIN=${REACT_APP_AUTH_DOMAIN}
        - REACT_APP_CLIENT_ID=${REACT_APP_CLIENT_ID}
        - REACT_APP_ENVIRONMENT=${REACT_APP_ENVIRONMENT}
        - REACT_APP_VERSION=${REACT_APP_VERSION}
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
```

---

## Kubernetes Configuration

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: natterbox-routing-policies-config
  namespace: natterbox
data:
  REACT_APP_API_BASE_URL: "https://api.natterbox.com/v1"
  REACT_APP_AUTH_DOMAIN: "auth.natterbox.com"
  REACT_APP_ENVIRONMENT: "production"
  REACT_APP_LOG_LEVEL: "error"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: natterbox-routing-policies
  namespace: natterbox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: natterbox-routing-policies
  template:
    metadata:
      labels:
        app: natterbox-routing-policies
    spec:
      containers:
        - name: web
          image: natterbox/routing-policies:latest
          ports:
            - containerPort: 80
          envFrom:
            - configMapRef:
                name: natterbox-routing-policies-config
            - secretRef:
                name: natterbox-routing-policies-secrets
```

---

## Troubleshooting

### Common Configuration Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Environment variables undefined | Missing `REACT_APP_` prefix | Add prefix to variable name |
| HTTPS certificate errors | Self-signed certificate | Install certificate in system trust store |
| Build fails with memory error | Node heap overflow | Set `NODE_OPTIONS=--max_old_space_size=4096` |
| Hot reload not working | Fast Refresh disabled | Set `FAST_REFRESH=true` |
| Path aliases not resolved | Missing Jest configuration | Add `moduleNameMapper` to Jest config |
| Production build too large | Source maps enabled | Set `GENERATE_SOURCEMAP=false` |

### Debugging Configuration

```bash
# Print all environment variables (development only)
npm start 2>&1 | head -50

# Verify environment variable is set
echo $REACT_APP_API_BASE_URL

# Check Node environment
node -e "console.log(process.env.NODE_ENV)"
```

---

## Additional Resources

- [Create React App Documentation](https://create-react-app.dev/)
- [Webpack Configuration Guide](https://webpack.js.org/configuration/)
- [Jest Configuration Reference](https://jestjs.io/docs/configuration)
- [Natterbox API Documentation](https://docs.natterbox.com/api)