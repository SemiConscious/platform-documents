# Development Guide

## Overview

This comprehensive guide provides everything you need to know to set up, develop, test, and contribute to the Freedom-Freedom-Web service. Whether you're a new team member getting started or an experienced developer looking for specific guidance, this document covers the complete development workflow for our call center/telephony web application.

Freedom-Freedom-Web is a sophisticated frontend application that powers call center operations, including active call management, voicemail handling, address book functionality, team collaboration, and CTI (Computer Telephony Integration) bridge capabilities. Understanding the development environment and best practices is crucial for maintaining code quality and ensuring smooth collaboration across the team.

---

## Development Environment Setup

### Prerequisites

Before setting up your development environment, ensure you have the following tools installed:

| Tool | Minimum Version | Recommended Version | Purpose |
|------|-----------------|---------------------|---------|
| Node.js | 16.x | 18.x LTS | JavaScript runtime |
| npm | 8.x | 9.x | Package management |
| Git | 2.30+ | Latest | Version control |
| VS Code | Latest | Latest | Recommended IDE |

### System Requirements

- **RAM**: Minimum 8GB, recommended 16GB for optimal performance
- **Storage**: At least 2GB free space for dependencies and build artifacts
- **OS**: macOS, Linux, or Windows 10/11 with WSL2

### Initial Setup

1. **Clone the Repository**

```bash
# Clone the repository
git clone https://github.com/your-org/freedom-freedom-web.git

# Navigate to the project directory
cd freedom-freedom-web
```

2. **Install Dependencies**

```bash
# Install all project dependencies
npm install

# If you encounter peer dependency issues, try:
npm install --legacy-peer-deps
```

3. **Environment Configuration**

Create a local environment file by copying the template:

```bash
# Copy the example environment file
cp .env.example .env.local
```

Configure the following essential variables in your `.env.local`:

```env
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:3001/api
REACT_APP_CTI_BRIDGE_URL=ws://localhost:8080

# Authentication
REACT_APP_JWT_SECRET=your-development-secret
REACT_APP_AUTH_DOMAIN=localhost

# Feature Flags
REACT_APP_ENABLE_VOICEMAIL_DROP=true
REACT_APP_ENABLE_TEAM_COLLABORATION=true
REACT_APP_ENABLE_ACTIVITY_TRACKING=true

# Development Settings
REACT_APP_DEBUG_MODE=true
REACT_APP_LOG_LEVEL=debug
```

4. **Install Recommended VS Code Extensions**

Create or update `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense"
  ]
}
```

5. **Configure VS Code Settings**

Add to `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

---

## Running Locally

### Development Server

Start the development server with hot reload:

```bash
# Start development server
npm run dev

# Or with specific port
PORT=3000 npm run dev
```

The application will be available at `http://localhost:3000` by default.

### Available npm Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Create production build |
| `npm run preview` | Preview production build locally |
| `npm run test` | Run test suite |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Fix auto-fixable linting issues |
| `npm run format` | Format code with Prettier |
| `npm run type-check` | Run TypeScript type checking |

### Running with Mock API

For frontend development without a backend connection:

```bash
# Start with mock service worker
npm run dev:mock

# Or start the mock API server separately
npm run mock-server
```

### CTI Bridge Development Mode

When developing CTI-related features:

```bash
# Start with CTI bridge simulator
npm run dev:cti

# This starts both the app and a WebSocket simulator
```

### Building for Production

```bash
# Create optimized production build
npm run build

# Analyze bundle size
npm run build:analyze

# Preview the production build
npm run preview
```

---

## Testing with Jest

### Test Structure

Our test suite is organized following Jest conventions:

```
src/
├── components/
│   ├── ActiveCalls/
│   │   ├── ActiveCalls.tsx
│   │   ├── ActiveCalls.test.tsx
│   │   └── __snapshots__/
│   │       └── ActiveCalls.test.tsx.snap
├── hooks/
│   ├── useVoicemail.ts
│   └── useVoicemail.test.ts
├── services/
│   ├── ctiService.ts
│   └── __tests__/
│       └── ctiService.test.ts
└── __mocks__/
    └── ctiService.ts
```

### Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm run test -- ActiveCalls.test.tsx

# Run tests matching a pattern
npm run test -- --testNamePattern="should handle call transfer"

# Run tests with coverage
npm run test:coverage

# Run tests for changed files only
npm run test -- --onlyChanged
```

### Writing Tests

#### Component Testing Example

```typescript
// src/components/ActiveCalls/ActiveCalls.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActiveCalls } from './ActiveCalls';
import { CTIProvider } from '../../contexts/CTIContext';
import { mockCalls } from '../../__mocks__/callData';

// Mock the CTI service
jest.mock('../../services/ctiService');

describe('ActiveCalls Component', () => {
  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <CTIProvider>
        {ui}
      </CTIProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render active calls list', () => {
    renderWithProvider(<ActiveCalls calls={mockCalls} />);
    
    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(mockCalls.length);
  });

  it('should handle call hold action', async () => {
    const onHold = jest.fn();
    renderWithProvider(<ActiveCalls calls={mockCalls} onHold={onHold} />);
    
    const holdButton = screen.getByRole('button', { name: /hold/i });
    await userEvent.click(holdButton);
    
    await waitFor(() => {
      expect(onHold).toHaveBeenCalledWith(mockCalls[0].id);
    });
  });

  it('should display call duration correctly', () => {
    const callWithDuration = { ...mockCalls[0], duration: 125 };
    renderWithProvider(<ActiveCalls calls={[callWithDuration]} />);
    
    expect(screen.getByText('2:05')).toBeInTheDocument();
  });
});
```

#### Hook Testing Example

```typescript
// src/hooks/useVoicemail.test.ts
import { renderHook, act } from '@testing-library/react';
import { useVoicemail } from './useVoicemail';
import { voicemailService } from '../services/voicemailService';

jest.mock('../services/voicemailService');

describe('useVoicemail Hook', () => {
  it('should fetch voicemails on mount', async () => {
    const mockVoicemails = [
      { id: '1', from: '+1234567890', duration: 30 },
      { id: '2', from: '+0987654321', duration: 45 }
    ];
    
    (voicemailService.getVoicemails as jest.Mock).mockResolvedValue(mockVoicemails);
    
    const { result } = renderHook(() => useVoicemail());
    
    expect(result.current.loading).toBe(true);
    
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(result.current.loading).toBe(false);
    expect(result.current.voicemails).toEqual(mockVoicemails);
  });

  it('should handle delete voicemail', async () => {
    (voicemailService.deleteVoicemail as jest.Mock).mockResolvedValue(true);
    
    const { result } = renderHook(() => useVoicemail());
    
    await act(async () => {
      await result.current.deleteVoicemail('1');
    });
    
    expect(voicemailService.deleteVoicemail).toHaveBeenCalledWith('1');
  });
});
```

#### API Service Testing Example

```typescript
// src/services/__tests__/ctiService.test.ts
import { ctiService } from '../ctiService';
import WS from 'jest-websocket-mock';

describe('CTI Service', () => {
  let server: WS;
  
  beforeEach(() => {
    server = new WS('ws://localhost:8080');
  });
  
  afterEach(() => {
    WS.clean();
  });

  it('should establish WebSocket connection', async () => {
    const connectionPromise = ctiService.connect();
    
    await server.connected;
    await connectionPromise;
    
    expect(ctiService.isConnected()).toBe(true);
  });

  it('should handle incoming call events', async () => {
    const callHandler = jest.fn();
    ctiService.on('incomingCall', callHandler);
    
    await ctiService.connect();
    await server.connected;
    
    server.send(JSON.stringify({
      type: 'INCOMING_CALL',
      data: { callId: '123', from: '+1234567890' }
    }));
    
    expect(callHandler).toHaveBeenCalledWith({
      callId: '123',
      from: '+1234567890'
    });
  });
});
```

### Coverage Requirements

Maintain minimum coverage thresholds:

```javascript
// jest.config.js
module.exports = {
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

---

## Code Style & Linting

### ESLint Configuration

Our ESLint setup enforces consistent code quality:

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'prettier'
  ],
  rules: {
    'react/react-in-jsx-scope': 'off',
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn'
  }
};
```

### Prettier Configuration

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "jsxSingleQuote": false,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `ActiveCallsList.tsx` |
| Hooks | camelCase with `use` prefix | `useVoicemail.ts` |
| Utilities | camelCase | `formatPhoneNumber.ts` |
| Constants | UPPER_SNAKE_CASE | `MAX_CALL_DURATION` |
| Types/Interfaces | PascalCase with `I` or `T` prefix | `ICallData`, `TCallStatus` |
| CSS Modules | camelCase | `styles.activeCall` |

### Code Organization

```typescript
// Component file structure example
// 1. Imports (external, then internal)
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../common/Button';
import { useVoicemail } from '../../hooks/useVoicemail';
import type { IVoicemail } from '../../types/voicemail';
import styles from './VoicemailList.module.css';

// 2. Type definitions
interface IVoicemailListProps {
  initialFilter?: string;
  onSelect: (voicemail: IVoicemail) => void;
}

// 3. Component definition
export const VoicemailList: React.FC<IVoicemailListProps> = ({
  initialFilter = '',
  onSelect
}) => {
  // 4. Hooks
  const { t } = useTranslation();
  const { voicemails, loading, error } = useVoicemail();
  
  // 5. State
  const [filter, setFilter] = useState(initialFilter);
  
  // 6. Effects
  useEffect(() => {
    // Effect logic
  }, [filter]);
  
  // 7. Handlers
  const handleFilterChange = (value: string): void => {
    setFilter(value);
  };
  
  // 8. Render helpers
  const renderVoicemailItem = (voicemail: IVoicemail): JSX.Element => (
    <li key={voicemail.id} className={styles.item}>
      {/* ... */}
    </li>
  );
  
  // 9. Main render
  return (
    <div className={styles.container}>
      {/* ... */}
    </div>
  );
};
```

---

## Debugging Tips

### Browser DevTools

#### React Developer Tools

1. Install the React DevTools browser extension
2. Use the Components tab to inspect component hierarchy
3. Use the Profiler tab to identify performance issues

```typescript
// Enable profiling in development
if (process.env.NODE_ENV === 'development') {
  const whyDidYouRender = require('@welldone-software/why-did-you-render');
  whyDidYouRender(React, {
    trackAllPureComponents: true
  });
}
```

#### Redux DevTools (if using Redux)

```typescript
// Configure store with DevTools
import { configureStore } from '@reduxjs/toolkit';

const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== 'production'
});
```

### Debugging CTI Bridge Connections

```typescript
// Enable WebSocket debugging
const debugCTI = (): void => {
  if (process.env.REACT_APP_DEBUG_MODE === 'true') {
    const originalSend = WebSocket.prototype.send;
    WebSocket.prototype.send = function(data) {
      console.log('[CTI OUT]:', data);
      return originalSend.call(this, data);
    };
  }
};
```

### Source Maps

Ensure source maps are enabled in development:

```javascript
// vite.config.ts or webpack.config.js
export default {
  build: {
    sourcemap: process.env.NODE_ENV !== 'production'
  }
};
```

### Logging Best Practices

```typescript
// src/utils/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
};

const currentLevel = LOG_LEVELS[process.env.REACT_APP_LOG_LEVEL as LogLevel] || 1;

export const logger = {
  debug: (...args: unknown[]): void => {
    if (LOG_LEVELS.debug >= currentLevel) {
      console.log('[DEBUG]', ...args);
    }
  },
  info: (...args: unknown[]): void => {
    if (LOG_LEVELS.info >= currentLevel) {
      console.info('[INFO]', ...args);
    }
  },
  warn: (...args: unknown[]): void => {
    if (LOG_LEVELS.warn >= currentLevel) {
      console.warn('[WARN]', ...args);
    }
  },
  error: (...args: unknown[]): void => {
    if (LOG_LEVELS.error >= currentLevel) {
      console.error('[ERROR]', ...args);
    }
  }
};
```

### Network Debugging

```typescript
// Intercept API calls for debugging
if (process.env.REACT_APP_DEBUG_MODE === 'true') {
  axios.interceptors.request.use(config => {
    console.log('[API Request]', config.method?.toUpperCase(), config.url);
    return config;
  });
  
  axios.interceptors.response.use(
    response => {
      console.log('[API Response]', response.status, response.config.url);
      return response;
    },
    error => {
      console.error('[API Error]', error.response?.status, error.config?.url);
      return Promise.reject(error);
    }
  );
}
```

---

## Common Issues

### Issue 1: WebSocket Connection Failures

**Symptoms**: CTI bridge fails to connect, call features unavailable

**Solution**:
```typescript
// Implement reconnection logic
const connectWithRetry = async (maxRetries = 5): Promise<void> => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await ctiService.connect();
      return;
    } catch (error) {
      logger.warn(`Connection attempt ${i + 1} failed, retrying...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
  throw new Error('Failed to connect after max retries');
};
```

### Issue 2: JWT Token Expiration

**Symptoms**: 401 errors, sudden logouts

**Solution**:
```typescript
// Implement token refresh interceptor
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const newToken = await authService.refreshToken();
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        authService.logout();
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

### Issue 3: Memory Leaks in Call Components

**Symptoms**: Increasing memory usage, slow performance

**Solution**:
```typescript
// Proper cleanup in useEffect
useEffect(() => {
  const subscription = callService.subscribe(handleCallUpdate);
  
  return () => {
    subscription.unsubscribe();
  };
}, []);

// Cancel pending requests on unmount
useEffect(() => {
  const controller = new AbortController();
  
  fetchData({ signal: controller.signal });
  
  return () => {
    controller.abort();
  };
}, []);
```

### Issue 4: Hot Reload Not Working

**Symptoms**: Changes don't reflect without full page reload

**Solution**:
```bash
# Clear cache and restart
rm -rf node_modules/.cache
npm run dev
```

### Issue 5: Type Errors After Dependency Update

**Symptoms**: TypeScript compilation errors after npm update

**Solution**:
```bash
# Regenerate type definitions
rm -rf node_modules/@types
npm install

# Clear TypeScript cache
rm -rf tsconfig.tsbuildinfo
```

---

## Contributing Guidelines

### Getting Started

1. **Fork the Repository**: Create your own fork of the project
2. **Create a Feature Branch**: Base it on `develop` branch
3. **Make Your Changes**: Follow the coding standards
4. **Submit a Pull Request**: Include a comprehensive description

### Branch Naming Convention

```
feature/TICKET-123-add-voicemail-drop
bugfix/TICKET-456-fix-call-transfer
hotfix/TICKET-789-security-patch
chore/update-dependencies
docs/update-readme
```

### Commit Message Format

Follow Conventional Commits:

```
type(scope): description

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, no code change
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(calls): add call transfer functionality

Implement drag-and-drop call transfer between agents.
Includes visual feedback and confirmation dialog.

Closes #123
```

### Pull Request Process

1. **Ensure Tests Pass**:
   ```bash
   npm run test
   npm run lint
   npm run type-check
   ```

2. **Update Documentation**: If your changes affect the API or user-facing features

3. **Request Review**: Assign at least two reviewers

4. **Address Feedback**: Make requested changes promptly

5. **Squash and Merge**: Keep a clean commit history

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests cover new functionality
- [ ] No console.log statements (except in development utilities)
- [ ] Types are properly defined
- [ ] Accessibility considerations addressed
- [ ] Performance implications considered
- [ ] Security best practices followed
- [ ] Documentation updated if needed

### Release Process

1. Merge feature branches to `develop`
2. Create release branch: `release/v1.2.0`
3. Run full test suite and QA
4. Merge to `main` and tag release
5. Deploy to production

---

## Additional Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Library](https://testing-library.com/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

For questions or support, reach out to the team on Slack in `#freedom-web-dev` or create an issue in the repository.