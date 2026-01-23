# Development Guide

## Overview

This comprehensive guide is designed for developers working on the **natterbox-routing-policies** frontend application. Whether you're a new team member getting started or an experienced contributor implementing new features, this guide covers everything you need to know about local development, testing, code standards, and debugging.

The natterbox-routing-policies service is a React-based application that manages Natterbox routing policies for telephony and communication systems. It includes AI-powered routing configurations, call flow management, variable-based routing rules, and policy snapshots with versioning capabilities.

---

## Local Development Setup

### Prerequisites

Before you begin, ensure you have the following installed on your development machine:

- **Node.js**: Version 18.x or higher (LTS recommended)
- **npm**: Version 9.x or higher (comes with Node.js)
- **Git**: Latest stable version
- **IDE**: VS Code recommended with ESLint and Prettier extensions

### Initial Setup

1. **Clone the Repository**

```bash
git clone https://github.com/natterbox/natterbox-routing-policies.git
cd natterbox-routing-policies
```

2. **Install Dependencies**

```bash
npm install
```

3. **Configure Environment Variables**

Create a `.env.local` file in the project root:

```bash
cp .env.example .env.local
```

Configure the required environment variables:

```env
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:3001/api
REACT_APP_AUTH_DOMAIN=your-auth-domain.com
REACT_APP_CLIENT_ID=your-client-id

# Feature Flags
REACT_APP_FEATURE_AI_ROUTING=true
REACT_APP_FEATURE_POLICY_SNAPSHOTS=true

# Development Settings
REACT_APP_DEBUG_MODE=true
REACT_APP_LOG_LEVEL=debug
```

4. **Start the Development Server**

```bash
npm start
```

The application will be available at `http://localhost:3000`.

### Development Environment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Development                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   React     │───▶│   API Mock  │───▶│   Mock Data    │  │
│  │   App       │    │   Server    │    │   Store        │  │
│  │  :3000      │    │   :3001     │    │                 │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Mock Server Setup (Optional)

For offline development or API independence:

```bash
npm run mock-server
```

This starts a JSON Server instance with mock routing policy data.

---

## Running Tests

### Test Framework Overview

The project uses Jest as the test runner with React Testing Library for component testing. The test suite is organized into three categories:

- **Unit Tests**: Individual functions and utilities
- **Component Tests**: React components in isolation
- **Integration Tests**: Feature workflows and API interactions

### Running All Tests

```bash
# Run all tests
npm test

# Run tests with coverage report
npm test -- --coverage

# Run tests in watch mode (recommended during development)
npm test -- --watch
```

### Running Specific Test Categories

```bash
# Run only unit tests
npm test -- --testPathPattern="unit"

# Run only component tests
npm test -- --testPathPattern="components"

# Run only integration tests
npm test -- --testPathPattern="integration"

# Run tests for a specific file
npm test -- RoutingPolicy.test.tsx
```

### Writing Tests

#### Component Test Example

```typescript
// src/components/RoutingPolicy/__tests__/RoutingPolicyEditor.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RoutingPolicyEditor } from '../RoutingPolicyEditor';
import { mockRoutingPolicy } from '../../../test/mocks/routingPolicies';

describe('RoutingPolicyEditor', () => {
  it('should render policy name input', () => {
    render(<RoutingPolicyEditor policy={mockRoutingPolicy} />);
    
    expect(screen.getByLabelText(/policy name/i)).toBeInTheDocument();
  });

  it('should validate required fields before submission', async () => {
    render(<RoutingPolicyEditor policy={mockRoutingPolicy} />);
    
    const nameInput = screen.getByLabelText(/policy name/i);
    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/policy name is required/i)).toBeInTheDocument();
    });
  });

  it('should handle AI routing configuration', async () => {
    render(<RoutingPolicyEditor policy={mockRoutingPolicy} enableAIRouting />);
    
    const aiToggle = screen.getByRole('switch', { name: /enable ai routing/i });
    fireEvent.click(aiToggle);
    
    await waitFor(() => {
      expect(screen.getByText(/ai agent configuration/i)).toBeInTheDocument();
    });
  });
});
```

#### Unit Test Example

```typescript
// src/utils/__tests__/routingRules.test.ts
import { evaluateRoutingRule, validatePhoneNumber } from '../routingRules';

describe('evaluateRoutingRule', () => {
  describe('date variable type', () => {
    it('should match date within range', () => {
      const rule = {
        type: 'date',
        operator: 'between',
        value: ['2024-01-01', '2024-12-31']
      };
      
      expect(evaluateRoutingRule(rule, '2024-06-15')).toBe(true);
    });
  });

  describe('string variable type', () => {
    it('should match exact string values', () => {
      const rule = {
        type: 'string',
        operator: 'equals',
        value: 'priority'
      };
      
      expect(evaluateRoutingRule(rule, 'priority')).toBe(true);
      expect(evaluateRoutingRule(rule, 'standard')).toBe(false);
    });
  });
});

describe('validatePhoneNumber', () => {
  it('should validate international phone numbers', () => {
    expect(validatePhoneNumber('+44 20 7123 4567')).toBe(true);
    expect(validatePhoneNumber('+1-555-123-4567')).toBe(true);
    expect(validatePhoneNumber('invalid')).toBe(false);
  });
});
```

### Test Coverage Requirements

Maintain minimum test coverage thresholds:

| Category    | Minimum Coverage |
|-------------|------------------|
| Statements  | 80%              |
| Branches    | 75%              |
| Functions   | 80%              |
| Lines       | 80%              |

---

## Code Style Guidelines

### TypeScript Standards

All code must be written in TypeScript with strict mode enabled. Follow these conventions:

#### Type Definitions

```typescript
// ✅ Good: Explicit interface definitions
interface RoutingPolicy {
  id: string;
  name: string;
  description?: string;
  rules: RoutingRule[];
  aiConfig?: AIRoutingConfig;
  createdAt: Date;
  updatedAt: Date;
}

// ✅ Good: Use type for unions and intersections
type VariableType = 'date' | 'string' | 'number' | 'boolean' | 'selection';

type RoutingRuleWithMetadata = RoutingRule & {
  metadata: RuleMetadata;
};

// ❌ Bad: Using 'any' type
const processPolicy = (policy: any) => { ... };

// ✅ Good: Use generics for reusable components
function useAsyncData<T>(fetcher: () => Promise<T>): AsyncState<T> {
  // implementation
}
```

#### Component Structure

```typescript
// src/components/RoutingPolicy/RoutingPolicyCard.tsx
import React, { FC, memo, useCallback } from 'react';
import { RoutingPolicy } from '../../types/routing';
import { useFeatureFlag } from '../../hooks/useFeatureFlag';
import styles from './RoutingPolicyCard.module.scss';

interface RoutingPolicyCardProps {
  policy: RoutingPolicy;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  isReadOnly?: boolean;
}

export const RoutingPolicyCard: FC<RoutingPolicyCardProps> = memo(({
  policy,
  onEdit,
  onDelete,
  isReadOnly = false
}) => {
  const isAIRoutingEnabled = useFeatureFlag('AI_ROUTING');

  const handleEdit = useCallback(() => {
    onEdit(policy.id);
  }, [onEdit, policy.id]);

  const handleDelete = useCallback(() => {
    if (window.confirm('Are you sure you want to delete this policy?')) {
      onDelete(policy.id);
    }
  }, [onDelete, policy.id]);

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>{policy.name}</h3>
      {policy.description && (
        <p className={styles.description}>{policy.description}</p>
      )}
      {isAIRoutingEnabled && policy.aiConfig && (
        <AIRoutingBadge config={policy.aiConfig} />
      )}
      {!isReadOnly && (
        <div className={styles.actions}>
          <button onClick={handleEdit}>Edit</button>
          <button onClick={handleDelete}>Delete</button>
        </div>
      )}
    </div>
  );
});

RoutingPolicyCard.displayName = 'RoutingPolicyCard';
```

### File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `RoutingPolicyEditor.tsx` |
| Hooks | camelCase with 'use' prefix | `useRoutingPolicy.ts` |
| Utilities | camelCase | `routingRules.ts` |
| Types | PascalCase | `RoutingTypes.ts` |
| Tests | Same as source with `.test` | `RoutingPolicy.test.tsx` |
| Styles | Same as component with `.module` | `RoutingPolicy.module.scss` |

### ESLint and Prettier

The project uses ESLint and Prettier for code formatting. Configuration is in `.eslintrc.js` and `.prettierrc`:

```bash
# Run linting
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Format code with Prettier
npm run format
```

---

## Adding New Features

### Feature Development Workflow

1. **Create a Feature Branch**

```bash
git checkout -b feature/TICKET-123-new-routing-variable
```

2. **Plan the Feature Structure**

For a new variable type (e.g., "time-range"), create the following:

```
src/
├── components/
│   └── VariableRules/
│       └── TimeRangeRule/
│           ├── TimeRangeRule.tsx
│           ├── TimeRangeRule.module.scss
│           ├── TimeRangeRule.test.tsx
│           └── index.ts
├── hooks/
│   └── useTimeRangeValidation.ts
├── types/
│   └── timeRange.ts
└── utils/
    └── timeRangeUtils.ts
```

3. **Implement the Type Definitions**

```typescript
// src/types/timeRange.ts
export interface TimeRange {
  start: string; // HH:mm format
  end: string;
  timezone: string;
  daysOfWeek?: DayOfWeek[];
}

export interface TimeRangeRule extends BaseRoutingRule {
  type: 'time-range';
  config: TimeRange;
}

export type DayOfWeek = 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun';
```

4. **Create the Component**

```typescript
// src/components/VariableRules/TimeRangeRule/TimeRangeRule.tsx
import React, { FC, useState, useCallback } from 'react';
import { TimeRangeRule as TimeRangeRuleType } from '../../../types/timeRange';
import { useTimeRangeValidation } from '../../../hooks/useTimeRangeValidation';
import styles from './TimeRangeRule.module.scss';

interface TimeRangeRuleProps {
  rule: TimeRangeRuleType;
  onChange: (rule: TimeRangeRuleType) => void;
  onValidationChange: (isValid: boolean) => void;
}

export const TimeRangeRule: FC<TimeRangeRuleProps> = ({
  rule,
  onChange,
  onValidationChange
}) => {
  const { validate, errors } = useTimeRangeValidation();

  const handleStartTimeChange = useCallback((start: string) => {
    const updatedRule = {
      ...rule,
      config: { ...rule.config, start }
    };
    onChange(updatedRule);
    onValidationChange(validate(updatedRule.config));
  }, [rule, onChange, onValidationChange, validate]);

  return (
    <div className={styles.timeRangeRule}>
      <label>
        Start Time
        <input
          type="time"
          value={rule.config.start}
          onChange={(e) => handleStartTimeChange(e.target.value)}
        />
      </label>
      {errors.start && <span className={styles.error}>{errors.start}</span>}
      {/* Additional fields... */}
    </div>
  );
};
```

5. **Register with Feature Flag (if applicable)**

```typescript
// src/features/variableRules/index.ts
import { registerVariableType } from '../registry';
import { TimeRangeRule } from '../../components/VariableRules/TimeRangeRule';

registerVariableType({
  type: 'time-range',
  component: TimeRangeRule,
  featureFlag: 'TIME_RANGE_ROUTING',
  validator: validateTimeRange
});
```

---

## Feature Flags Usage

### Overview

Feature flags allow controlled rollout of new functionality. The system supports runtime configuration through environment variables and remote configuration.

### Available Feature Flags

| Flag Name | Description | Default |
|-----------|-------------|---------|
| `AI_ROUTING` | Enable AI-powered routing features | `false` |
| `POLICY_SNAPSHOTS` | Enable policy versioning and snapshots | `true` |
| `ADVANCED_VARIABLES` | Enable complex variable types | `false` |
| `BULK_OPERATIONS` | Enable bulk policy operations | `false` |

### Using Feature Flags in Components

```typescript
import { useFeatureFlag } from '../hooks/useFeatureFlag';

export const RoutingPolicyEditor: FC<Props> = ({ policy }) => {
  const isAIRoutingEnabled = useFeatureFlag('AI_ROUTING');
  const isPolicySnapshotsEnabled = useFeatureFlag('POLICY_SNAPSHOTS');

  return (
    <div>
      <BasicPolicyForm policy={policy} />
      
      {isAIRoutingEnabled && (
        <AIRoutingSection policy={policy} />
      )}
      
      {isPolicySnapshotsEnabled && (
        <SnapshotControls policyId={policy.id} />
      )}
    </div>
  );
};
```

### Creating New Feature Flags

1. **Add to Feature Flag Configuration**

```typescript
// src/config/featureFlags.ts
export const FEATURE_FLAGS = {
  AI_ROUTING: {
    key: 'AI_ROUTING',
    defaultValue: false,
    description: 'Enable AI-powered routing features'
  },
  // Add your new flag
  NEW_FEATURE: {
    key: 'NEW_FEATURE',
    defaultValue: false,
    description: 'Description of the new feature'
  }
} as const;
```

2. **Add Environment Variable**

```env
REACT_APP_FEATURE_NEW_FEATURE=true
```

---

## Debugging Tips

### Browser DevTools

#### React Developer Tools

Install the React DevTools browser extension for component inspection:

```typescript
// Add debug information to components in development
if (process.env.NODE_ENV === 'development') {
  RoutingPolicyEditor.whyDidYouRender = true;
}
```

#### Network Debugging

Monitor API calls in the Network tab. Common endpoints to watch:

- `GET /api/routing-policies` - Fetch all policies
- `POST /api/routing-policies` - Create new policy
- `PUT /api/routing-policies/:id` - Update policy
- `POST /api/routing-policies/:id/snapshot` - Create snapshot

### Logging

Use the built-in logger for consistent debugging:

```typescript
import { logger } from '../utils/logger';

// Different log levels
logger.debug('Policy data:', policy);
logger.info('Policy created successfully', { policyId: policy.id });
logger.warn('Deprecated variable type used', { type: rule.type });
logger.error('Failed to save policy', error);
```

### State Debugging

For Redux/Context state debugging:

```typescript
// Add to src/store/index.ts for Redux DevTools
const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV === 'development'
});
```

### Performance Profiling

```typescript
// Use React Profiler for performance analysis
import { Profiler } from 'react';

const onRenderCallback = (
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number
) => {
  console.log(`${id} ${phase}: ${actualDuration}ms`);
};

<Profiler id="RoutingPolicyList" onRender={onRenderCallback}>
  <RoutingPolicyList policies={policies} />
</Profiler>
```

---

## Common Issues

### Issue: "Module not found" Errors

**Symptom**: Import statements fail with module resolution errors.

**Solution**:

```bash
# Clear node_modules and reinstall
rm -rf node_modules
rm package-lock.json
npm install

# If using path aliases, verify tsconfig.json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@components/*": ["components/*"],
      "@hooks/*": ["hooks/*"]
    }
  }
}
```

### Issue: API Connection Failures

**Symptom**: Network requests fail or timeout in development.

**Solution**:

1. Verify environment variables are set correctly
2. Check if the API server is running
3. Verify CORS configuration for local development

```typescript
// src/api/client.ts - Add request interceptor for debugging
apiClient.interceptors.request.use((config) => {
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  return config;
});
```

### Issue: Feature Flag Not Working

**Symptom**: Feature flag returns unexpected value.

**Solution**:

```typescript
// Debug feature flag resolution
import { getFeatureFlagValue, getFeatureFlagSource } from '../utils/featureFlags';

console.log('Flag value:', getFeatureFlagValue('AI_ROUTING'));
console.log('Flag source:', getFeatureFlagSource('AI_ROUTING')); // 'env' | 'remote' | 'default'
```

### Issue: Test Failures After Dependency Update

**Symptom**: Tests fail after running `npm update`.

**Solution**:

```bash
# Clear Jest cache
npm test -- --clearCache

# Update snapshots if intentional changes
npm test -- --updateSnapshot

# Check for breaking changes in updated packages
npm outdated
```

### Issue: Slow Development Server

**Symptom**: Hot reload takes too long or dev server is sluggish.

**Solution**:

```javascript
// craco.config.js or webpack.config.js
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Exclude large directories from watching
      webpackConfig.watchOptions = {
        ignored: /node_modules/,
        aggregateTimeout: 300,
        poll: 1000
      };
      return webpackConfig;
    }
  }
};
```

---

## Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Testing Library Docs](https://testing-library.com/docs/)
- [Internal API Documentation](./api-reference.md)
- [Data Models Reference](./data-models.md)

---

## Getting Help

If you encounter issues not covered in this guide:

1. Search existing GitHub issues
2. Check the `#natterbox-routing` Slack channel
3. Create a new GitHub issue with reproduction steps
4. Contact the platform team for infrastructure issues