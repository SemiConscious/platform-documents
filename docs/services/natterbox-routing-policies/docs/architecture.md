# Application Architecture

## Overview

The **natterbox-routing-policies** service is a React-based frontend application designed for managing Natterbox routing policies in telephony and communication systems. This document provides a comprehensive overview of the application architecture, including project structure, component organization, state management patterns, routing configuration, build processes, and testing strategies.

This architecture documentation serves as the definitive guide for developers working on or integrating with the routing policies management interface. Understanding these patterns is essential for maintaining consistency, scalability, and code quality across the application.

---

## Project Structure

The application follows a feature-based modular architecture that promotes separation of concerns and maintainability. Below is the comprehensive directory structure:

```
natterbox-routing-policies/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── routing-policies.ts
│   │   │   ├── ai-routing.ts
│   │   │   ├── snapshots.ts
│   │   │   └── feature-flags.ts
│   │   ├── client.ts
│   │   └── index.ts
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   ├── Table/
│   │   │   └── PhoneNumberInput/
│   │   ├── routing/
│   │   │   ├── PolicyEditor/
│   │   │   ├── RuleBuilder/
│   │   │   ├── CallFlowDiagram/
│   │   │   └── VariableSelector/
│   │   ├── ai/
│   │   │   ├── AgentConfiguration/
│   │   │   ├── AIRoutingPanel/
│   │   │   └── ModelSelector/
│   │   └── snapshots/
│   │       ├── SnapshotList/
│   │       ├── SnapshotComparison/
│   │       └── VersionHistory/
│   ├── features/
│   │   ├── policies/
│   │   ├── ai-routing/
│   │   ├── variables/
│   │   └── snapshots/
│   ├── hooks/
│   │   ├── usePolicy.ts
│   │   ├── useFeatureFlags.ts
│   │   ├── useCountryCodes.ts
│   │   └── useSnapshot.ts
│   ├── store/
│   │   ├── slices/
│   │   ├── middleware/
│   │   └── index.ts
│   ├── types/
│   │   ├── models/
│   │   ├── api/
│   │   └── index.ts
│   ├── utils/
│   │   ├── validation/
│   │   ├── formatting/
│   │   └── phone-utils/
│   ├── styles/
│   ├── App.tsx
│   └── index.tsx
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── package.json
├── tsconfig.json
├── webpack.config.js
└── jest.config.js
```

### Directory Responsibilities

| Directory | Purpose |
|-----------|---------|
| `src/api/` | API client configuration and endpoint definitions |
| `src/components/` | Reusable UI components organized by domain |
| `src/features/` | Feature-specific modules containing logic and views |
| `src/hooks/` | Custom React hooks for shared functionality |
| `src/store/` | Redux store configuration and state slices |
| `src/types/` | TypeScript type definitions and interfaces |
| `src/utils/` | Utility functions and helpers |

---

## Component Hierarchy

The application follows a hierarchical component structure that separates concerns between presentational and container components.

### Component Architecture Diagram

```
App
├── AppProvider (Context Providers)
│   ├── ThemeProvider
│   ├── AuthProvider
│   └── FeatureFlagProvider
├── Layout
│   ├── Header
│   │   ├── Navigation
│   │   └── UserMenu
│   ├── Sidebar
│   │   └── PolicyNavigation
│   └── MainContent
│       └── Routes
│           ├── PolicyListPage
│           │   ├── PolicyTable
│           │   ├── PolicyFilters
│           │   └── PolicyActions
│           ├── PolicyEditorPage
│           │   ├── PolicyEditor
│           │   │   ├── RuleBuilder
│           │   │   │   ├── VariableSelector
│           │   │   │   ├── ConditionBuilder
│           │   │   │   └── ActionConfigurator
│           │   │   └── CallFlowDiagram
│           │   └── PolicyMetadata
│           ├── AIRoutingPage
│           │   ├── AgentConfiguration
│           │   └── AIRoutingPanel
│           └── SnapshotsPage
│               ├── SnapshotList
│               └── SnapshotComparison
└── GlobalModals
    ├── ConfirmationModal
    └── ErrorBoundary
```

### Core Component Patterns

#### Container Components

Container components handle business logic, state management, and data fetching:

```typescript
// src/features/policies/PolicyListContainer.tsx
import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchPolicies, selectPolicies, selectLoadingState } from '../../store/slices/policiesSlice';
import { PolicyTable } from '../../components/routing/PolicyTable';
import { useFeatureFlags } from '../../hooks/useFeatureFlags';

interface PolicyListContainerProps {
  organizationId: string;
}

export const PolicyListContainer: React.FC<PolicyListContainerProps> = ({ 
  organizationId 
}) => {
  const dispatch = useDispatch();
  const policies = useSelector(selectPolicies);
  const { isLoading, error } = useSelector(selectLoadingState);
  const { isEnabled } = useFeatureFlags();

  useEffect(() => {
    dispatch(fetchPolicies({ organizationId }));
  }, [dispatch, organizationId]);

  const handlePolicySelect = (policyId: string) => {
    // Navigation logic
  };

  const handlePolicyDelete = async (policyId: string) => {
    // Delete logic with confirmation
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <PolicyTable
      policies={policies}
      onSelect={handlePolicySelect}
      onDelete={handlePolicyDelete}
      showAIFeatures={isEnabled('ai-routing')}
    />
  );
};
```

#### Presentational Components

Presentational components focus on UI rendering and receive data via props:

```typescript
// src/components/routing/PolicyTable/PolicyTable.tsx
import React from 'react';
import { Policy } from '../../../types/models';
import { Table, TableRow, TableCell } from '../../common/Table';
import { Button } from '../../common/Button';

interface PolicyTableProps {
  policies: Policy[];
  onSelect: (policyId: string) => void;
  onDelete: (policyId: string) => void;
  showAIFeatures?: boolean;
}

export const PolicyTable: React.FC<PolicyTableProps> = ({
  policies,
  onSelect,
  onDelete,
  showAIFeatures = false,
}) => {
  return (
    <Table>
      <thead>
        <TableRow>
          <TableCell header>Name</TableCell>
          <TableCell header>Status</TableCell>
          <TableCell header>Last Modified</TableCell>
          {showAIFeatures && <TableCell header>AI Enabled</TableCell>}
          <TableCell header>Actions</TableCell>
        </TableRow>
      </thead>
      <tbody>
        {policies.map((policy) => (
          <TableRow key={policy.id} onClick={() => onSelect(policy.id)}>
            <TableCell>{policy.name}</TableCell>
            <TableCell>
              <StatusBadge status={policy.status} />
            </TableCell>
            <TableCell>{formatDate(policy.updatedAt)}</TableCell>
            {showAIFeatures && (
              <TableCell>
                {policy.aiRoutingEnabled ? 'Yes' : 'No'}
              </TableCell>
            )}
            <TableCell>
              <Button variant="danger" onClick={() => onDelete(policy.id)}>
                Delete
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </tbody>
    </Table>
  );
};
```

### Variable-Based Routing Components

The application supports multiple variable types for routing rules:

```typescript
// src/components/routing/VariableSelector/VariableSelector.tsx
import React from 'react';
import { VariableType, Variable } from '../../../types/models';

interface VariableSelectorProps {
  onVariableSelect: (variable: Variable) => void;
  allowedTypes?: VariableType[];
}

export const VariableSelector: React.FC<VariableSelectorProps> = ({
  onVariableSelect,
  allowedTypes = ['date', 'string', 'number', 'boolean', 'selection'],
}) => {
  const renderVariableInput = (type: VariableType) => {
    switch (type) {
      case 'date':
        return <DateVariableInput />;
      case 'string':
        return <StringVariableInput />;
      case 'number':
        return <NumberVariableInput />;
      case 'boolean':
        return <BooleanVariableInput />;
      case 'selection':
        return <SelectionVariableInput />;
      default:
        return null;
    }
  };

  return (
    <div className="variable-selector">
      {allowedTypes.map((type) => (
        <VariableTypeOption key={type} type={type}>
          {renderVariableInput(type)}
        </VariableTypeOption>
      ))}
    </div>
  );
};
```

---

## State Management

The application uses Redux Toolkit for centralized state management, providing predictable state updates and powerful debugging capabilities.

### Store Configuration

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import policiesReducer from './slices/policiesSlice';
import aiRoutingReducer from './slices/aiRoutingSlice';
import snapshotsReducer from './slices/snapshotsSlice';
import variablesReducer from './slices/variablesSlice';
import featureFlagsReducer from './slices/featureFlagsSlice';
import { apiMiddleware } from './middleware/apiMiddleware';
import { loggingMiddleware } from './middleware/loggingMiddleware';

export const store = configureStore({
  reducer: {
    policies: policiesReducer,
    aiRouting: aiRoutingReducer,
    snapshots: snapshotsReducer,
    variables: variablesReducer,
    featureFlags: featureFlagsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['policies/setDateVariable'],
      },
    }).concat(apiMiddleware, loggingMiddleware),
  devTools: process.env.NODE_ENV !== 'production',
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### State Slices

#### Policies Slice

```typescript
// src/store/slices/policiesSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Policy, PolicyRule, RoutingVariable } from '../../types/models';
import { policiesApi } from '../../api/endpoints/routing-policies';

interface PoliciesState {
  items: Policy[];
  currentPolicy: Policy | null;
  isLoading: boolean;
  error: string | null;
  filters: PolicyFilters;
}

const initialState: PoliciesState = {
  items: [],
  currentPolicy: null,
  isLoading: false,
  error: null,
  filters: {
    status: 'all',
    search: '',
  },
};

export const fetchPolicies = createAsyncThunk(
  'policies/fetchPolicies',
  async ({ organizationId }: { organizationId: string }, { rejectWithValue }) => {
    try {
      const response = await policiesApi.getAll(organizationId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const createPolicy = createAsyncThunk(
  'policies/createPolicy',
  async (policy: Partial<Policy>, { rejectWithValue }) => {
    try {
      const response = await policiesApi.create(policy);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updatePolicyRule = createAsyncThunk(
  'policies/updateRule',
  async ({ 
    policyId, 
    ruleId, 
    updates 
  }: { 
    policyId: string; 
    ruleId: string; 
    updates: Partial<PolicyRule> 
  }, { rejectWithValue }) => {
    try {
      const response = await policiesApi.updateRule(policyId, ruleId, updates);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const policiesSlice = createSlice({
  name: 'policies',
  initialState,
  reducers: {
    setCurrentPolicy: (state, action: PayloadAction<Policy>) => {
      state.currentPolicy = action.payload;
    },
    addRuleToPolicy: (state, action: PayloadAction<PolicyRule>) => {
      if (state.currentPolicy) {
        state.currentPolicy.rules.push(action.payload);
      }
    },
    updateVariable: (state, action: PayloadAction<{
      ruleId: string;
      variable: RoutingVariable;
    }>) => {
      if (state.currentPolicy) {
        const rule = state.currentPolicy.rules.find(
          r => r.id === action.payload.ruleId
        );
        if (rule) {
          rule.variable = action.payload.variable;
        }
      }
    },
    setFilters: (state, action: PayloadAction<Partial<PolicyFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPolicies.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPolicies.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload;
      })
      .addCase(fetchPolicies.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(createPolicy.fulfilled, (state, action) => {
        state.items.push(action.payload);
      });
  },
});

export const { 
  setCurrentPolicy, 
  addRuleToPolicy, 
  updateVariable,
  setFilters,
  clearError 
} = policiesSlice.actions;

// Selectors
export const selectPolicies = (state: RootState) => state.policies.items;
export const selectCurrentPolicy = (state: RootState) => state.policies.currentPolicy;
export const selectLoadingState = (state: RootState) => ({
  isLoading: state.policies.isLoading,
  error: state.policies.error,
});

export default policiesSlice.reducer;
```

### Custom Hooks for State Access

```typescript
// src/hooks/usePolicy.ts
import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  selectCurrentPolicy,
  selectLoadingState,
  addRuleToPolicy,
  updateVariable,
  createPolicy,
  updatePolicyRule,
} from '../store/slices/policiesSlice';
import { PolicyRule, RoutingVariable, VariableType } from '../types/models';
import { AppDispatch } from '../store';

export const usePolicy = () => {
  const dispatch = useDispatch<AppDispatch>();
  const currentPolicy = useSelector(selectCurrentPolicy);
  const { isLoading, error } = useSelector(selectLoadingState);

  const addRule = useCallback((rule: PolicyRule) => {
    dispatch(addRuleToPolicy(rule));
  }, [dispatch]);

  const setVariable = useCallback((
    ruleId: string, 
    variableType: VariableType, 
    value: any
  ) => {
    const variable: RoutingVariable = {
      type: variableType,
      value,
      validators: getValidatorsForType(variableType),
    };
    dispatch(updateVariable({ ruleId, variable }));
  }, [dispatch]);

  const savePolicy = useCallback(async () => {
    if (!currentPolicy) return;
    
    try {
      await dispatch(createPolicy(currentPolicy)).unwrap();
      return { success: true };
    } catch (error) {
      return { success: false, error };
    }
  }, [dispatch, currentPolicy]);

  return {
    policy: currentPolicy,
    isLoading,
    error,
    addRule,
    setVariable,
    savePolicy,
  };
};
```

---

## Routing Structure

The application uses React Router v6 for client-side routing with nested route configurations.

### Route Configuration

```typescript
// src/routes/index.tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { ProtectedRoute } from './ProtectedRoute';
import { FeatureRoute } from './FeatureRoute';
import { LoadingFallback } from '../components/common/LoadingFallback';

// Lazy-loaded route components
const PolicyListPage = lazy(() => import('../features/policies/PolicyListPage'));
const PolicyEditorPage = lazy(() => import('../features/policies/PolicyEditorPage'));
const AIRoutingPage = lazy(() => import('../features/ai-routing/AIRoutingPage'));
const SnapshotsPage = lazy(() => import('../features/snapshots/SnapshotsPage'));
const SnapshotDetailPage = lazy(() => import('../features/snapshots/SnapshotDetailPage'));
const SettingsPage = lazy(() => import('../features/settings/SettingsPage'));

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Default redirect */}
          <Route index element={<Navigate to="/policies" replace />} />
          
          {/* Policy Management Routes */}
          <Route path="policies">
            <Route index element={
              <ProtectedRoute permission="policies:read">
                <PolicyListPage />
              </ProtectedRoute>
            } />
            <Route path="new" element={
              <ProtectedRoute permission="policies:create">
                <PolicyEditorPage mode="create" />
              </ProtectedRoute>
            } />
            <Route path=":policyId" element={
              <ProtectedRoute permission="policies:read">
                <PolicyEditorPage mode="view" />
              </ProtectedRoute>
            } />
            <Route path=":policyId/edit" element={
              <ProtectedRoute permission="policies:update">
                <PolicyEditorPage mode="edit" />
              </ProtectedRoute>
            } />
          </Route>

          {/* AI Routing Routes (Feature Flag Protected) */}
          <Route path="ai-routing" element={
            <FeatureRoute flag="ai-routing">
              <ProtectedRoute permission="ai-routing:read">
                <AIRoutingPage />
              </ProtectedRoute>
            </FeatureRoute>
          } />

          {/* Snapshots & Versioning */}
          <Route path="snapshots">
            <Route index element={
              <ProtectedRoute permission="snapshots:read">
                <SnapshotsPage />
              </ProtectedRoute>
            } />
            <Route path=":snapshotId" element={
              <ProtectedRoute permission="snapshots:read">
                <SnapshotDetailPage />
              </ProtectedRoute>
            } />
            <Route path="compare/:snapshotA/:snapshotB" element={
              <ProtectedRoute permission="snapshots:read">
                <SnapshotComparisonPage />
              </ProtectedRoute>
            } />
          </Route>

          {/* Settings */}
          <Route path="settings" element={
            <ProtectedRoute permission="settings:read">
              <SettingsPage />
            </ProtectedRoute>
          } />

          {/* 404 Handler */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
};
```

### Route Guards

```typescript
// src/routes/FeatureRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useFeatureFlags } from '../hooks/useFeatureFlags';

interface FeatureRouteProps {
  flag: string;
  children: React.ReactNode;
  fallbackPath?: string;
}

export const FeatureRoute: React.FC<FeatureRouteProps> = ({
  flag,
  children,
  fallbackPath = '/policies',
}) => {
  const { isEnabled, isLoading } = useFeatureFlags();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isEnabled(flag)) {
    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
};
```

---

## Build Configuration

### Webpack Configuration

```javascript
// webpack.config.js
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const TerserPlugin = require('terser-webpack-plugin');

const isDevelopment = process.env.NODE_ENV !== 'production';

module.exports = {
  mode: isDevelopment ? 'development' : 'production',
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isDevelopment 
      ? '[name].js' 
      : '[name].[contenthash].js',
    chunkFilename: isDevelopment 
      ? '[name].chunk.js' 
      : '[name].[contenthash].chunk.js',
    publicPath: '/',
    clean: true,
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@features': path.resolve(__dirname, 'src/features'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@store': path.resolve(__dirname, 'src/store'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@types': path.resolve(__dirname, 'src/types'),
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
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          'css-loader',
          'postcss-loader',
        ],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
      },
    ],
  },
  optimization: {
    minimize: !isDevelopment,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
          },
        },
      }),
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          priority: -10,
          reuseExistingChunk: true,
        },
      },
    },
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
      favicon: './public/favicon.ico',
    }),
    !isDevelopment && new MiniCssExtractPlugin({
      filename: '[name].[contenthash].css',
    }),
    process.env.ANALYZE && new BundleAnalyzerPlugin(),
  ].filter(Boolean),
  devServer: {
    port: 3000,
    historyApiFallback: true,
    hot: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  devtool: isDevelopment ? 'eval-source-map' : 'source-map',
};
```

### Environment Configuration

```typescript
// src/config/environment.ts
interface EnvironmentConfig {
  apiBaseUrl: string;
  featureFlagsEndpoint: string;
  enableDevTools: boolean;
  sentryDsn?: string;
  analyticsId?: string;
}

const config: Record<string, EnvironmentConfig> = {
  development: {
    apiBaseUrl: 'http://localhost:8080/api',
    featureFlagsEndpoint: 'http://localhost:8080/api/feature-flags',
    enableDevTools: true,
  },
  staging: {
    apiBaseUrl: 'https://staging-api.natterbox.com/api',
    featureFlagsEndpoint: 'https://staging-api.natterbox.com/api/feature-flags',
    enableDevTools: true,
    sentryDsn: process.env.REACT_APP_SENTRY_DSN,
  },
  production: {
    apiBaseUrl: 'https://api.natterbox.com/api',
    featureFlagsEndpoint: 'https://api.natterbox.com/api/feature-flags',
    enableDevTools: false,
    sentryDsn: process.env.REACT_APP_SENTRY_DSN,
    analyticsId: process.env.REACT_APP_ANALYTICS_ID,
  },
};

export const getConfig = (): EnvironmentConfig => {
  const env = process.env.NODE_ENV || 'development';
  return config[env] || config.development;
};
```

---

## Testing Strategy

The application employs a comprehensive testing strategy covering unit tests, integration tests, and end-to-end tests.

### Unit Testing with Jest and React Testing Library

```typescript
// tests/unit/components/PolicyTable.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PolicyTable } from '@components/routing/PolicyTable';
import { mockPolicies } from '../../fixtures/policies';

describe('PolicyTable', () => {
  const defaultProps = {
    policies: mockPolicies,
    onSelect: jest.fn(),
    onDelete: jest.fn(),
    showAIFeatures: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all policies in the table', () => {
    render(<PolicyTable {...defaultProps} />);
    
    mockPolicies.forEach((policy) => {
      expect(screen.getByText(policy.name)).toBeInTheDocument();
    });
  });

  it('calls onSelect when a row is clicked', () => {
    render(<PolicyTable {...defaultProps} />);
    
    const firstRow = screen.getByText(mockPolicies[0].name).closest('tr');
    fireEvent.click(firstRow!);
    
    expect(defaultProps.onSelect).toHaveBeenCalledWith(mockPolicies[0].id);
  });

  it('shows AI column when showAIFeatures is true', () => {
    render(<PolicyTable {...defaultProps} showAIFeatures={true} />);
    
    expect(screen.getByText('AI Enabled')).toBeInTheDocument();
  });

  it('hides AI column when showAIFeatures is false', () => {
    render(<PolicyTable {...defaultProps} showAIFeatures={false} />);
    
    expect(screen.queryByText('AI Enabled')).not.toBeInTheDocument();
  });

  it('calls onDelete with correct policy ID', async () => {
    render(<PolicyTable {...defaultProps} />);
    
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);
    
    expect(defaultProps.onDelete).toHaveBeenCalledWith(mockPolicies[0].id);
  });
});
```

### Integration Testing with Redux

```typescript
// tests/integration/features/policies.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import policiesReducer from '@store/slices/policiesSlice';
import { PolicyListContainer } from '@features/policies/PolicyListContainer';
import { server } from '../../mocks/server';
import { rest } from 'msw';

const renderWithProviders = (
  ui: React.ReactElement,
  {
    preloadedState = {},
    store = configureStore({
      reducer: { policies: policiesReducer },
      preloadedState,
    }),
    ...renderOptions
  } = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>
      <MemoryRouter>{children}</MemoryRouter>
    </Provider>
  );

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
};

describe('PolicyListContainer Integration', () => {
  it('fetches and displays policies on mount', async () => {
    renderWithProviders(<PolicyListContainer organizationId="org-123" />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Test Policy 1')).toBeInTheDocument();
      expect(screen.getByText('Test Policy 2')).toBeInTheDocument();
    });
  });

  it('displays error message when fetch fails', async () => {
    server.use(
      rest.get('/api/policies', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );

    renderWithProviders(<PolicyListContainer organizationId="org-123" />);

    await waitFor(() => {
      expect(screen.getByText(/error loading policies/i)).toBeInTheDocument();
    });
  });
});
```

### End-to-End Testing with Cypress

```typescript
// tests/e2e/policies.cy.ts
describe('Policy Management', () => {
  beforeEach(() => {
    cy.login('admin@test.com', 'password');
    cy.visit('/policies');
  });

  it('creates a new routing policy', () => {
    cy.get('[data-testid="create-policy-btn"]').click();
    
    // Fill in policy details
    cy.get('[data-testid="policy-name-input"]').type('E2E Test Policy');
    cy.get('[data-testid="policy-description-input"]')
      .type('Created by E2E test');
    
    // Add a routing rule
    cy.get('[data-testid="add-rule-btn"]').click();
    cy.get('[data-testid="variable-type-select"]').select('string');
    cy.get('[data-testid="variable-name-input"]').type('caller_region');
    cy.get('[data-testid="condition-select"]').select('equals');
    cy.get('[data-testid="condition-value-input"]').type('US');
    
    // Save policy
    cy.get('[data-testid="save-policy-btn"]').click();
    
    // Verify success
    cy.get('[data-testid="success-toast"]')
      .should('contain', 'Policy created successfully');
    cy.url().should('match', /\/policies\/[\w-]+$/);
  });

  it('creates a snapshot of existing policy', () => {
    cy.get('[data-testid="policy-row"]').first().click();
    cy.get('[data-testid="create-snapshot-btn"]').click();
    
    cy.get('[data-testid="snapshot-name-input"]')
      .type('Pre-release snapshot');
    cy.get('[data-testid="confirm-snapshot-btn"]').click();
    
    cy.get('[data-testid="success-toast"]')
      .should('contain', 'Snapshot created');
    
    // Verify in snapshots list
    cy.visit('/snapshots');
    cy.get('[data-testid="snapshot-list"]')
      .should('contain', 'Pre-release snapshot');
  });

  it('handles phone number country code selection', () => {
    cy.get('[data-testid="create-policy-btn"]').click();
    cy.get('[data-testid="add-rule-btn"]').click();
    
    cy.get('[data-testid="variable-type-select"]').select('phone');
    cy.get('[data-testid="country-code-select"]').click();
    cy.get('[data-testid="country-option-US"]').click();
    
    cy.get('[data-testid="phone-number-input"]').type('5551234567');
    cy.get('[data-testid="phone-preview"]')
      .should('contain', '+1 555 123 4567');
  });
});
```

### Test Coverage Configuration

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@features/(.*)$': '<rootDir>/src/features/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@store/(.*)$': '<rootDir>/src/store/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/types/**/*',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testMatch: [
    '<rootDir>/tests/**/*.test.{ts,tsx}',
  ],
};
```

---

## Best Practices and Guidelines

### Code Organization

1. **Feature-based structure**: Group related components, hooks, and utilities by feature domain
2. **Barrel exports**: Use index files to simplify imports
3. **Type safety**: Leverage TypeScript for all components and utilities
4. **Consistent naming**: Follow established naming conventions for files and components

### Performance Considerations

- Use React.memo for expensive presentational components
- Implement code splitting with React.lazy for route-level components
- Optimize Redux selectors with createSelector for derived state
- Leverage useMemo and useCallback appropriately

### Common Pitfalls to Avoid

1. **Over-fetching**: Use proper caching strategies and avoid redundant API calls
2. **Prop drilling**: Utilize context or Redux for deeply nested state requirements
3. **Memory leaks**: Clean up subscriptions and async operations in useEffect
4. **Bundle size**: Monitor and optimize chunk sizes regularly

---

## Related Documentation

- [Data Models Reference](./data-models.md) - 34 documented data models
- [Configuration Guide](./configuration.md) - Environment and feature flag configuration
- [API Integration](./api-integration.md) - External API dependencies and side effects
- [Deployment Guide](./deployment.md) - Build and deployment procedures