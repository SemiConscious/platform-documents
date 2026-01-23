# Application Architecture

## Overview

The insight-insight-category-ui service implements a sophisticated frontend architecture built on **Feature-Sliced Design (FSD)** principles, combined with **Redux** for state management. This architecture enables scalable development of the Insight voice analytics categorization system while maintaining clear separation of concerns, predictable data flow, and high code reusability.

This document provides a comprehensive guide to understanding the architectural decisions, directory organization, state management patterns, and data flow within the application. Whether you're onboarding to the team or implementing new features, this guide will help you navigate and contribute to the codebase effectively.

---

## Feature-Sliced Design Overview

### What is Feature-Sliced Design?

Feature-Sliced Design (FSD) is an architectural methodology for frontend applications that organizes code by business domains rather than technical layers. It provides a standardized way to structure projects that scales well with team size and application complexity.

### Core Principles

FSD is built on three fundamental principles:

1. **Standardized Structure**: Every project follows the same layer hierarchy, making it easier for developers to navigate unfamiliar codebases.

2. **Business-Oriented Decomposition**: Code is organized around business features and entities rather than technical concerns (components, hooks, utils).

3. **Explicit Public APIs**: Each module exposes only what's necessary through a public API, hiding implementation details.

### Layer Hierarchy

The insight-insight-category-ui application follows the standard FSD layer hierarchy, ordered from most abstract to most specific:

```
┌─────────────────────────────────────────┐
│                  app                     │  ← Application initialization
├─────────────────────────────────────────┤
│               processes                  │  ← Complex multi-page flows
├─────────────────────────────────────────┤
│                 pages                    │  ← Full page components
├─────────────────────────────────────────┤
│               widgets                    │  ← Large composite blocks
├─────────────────────────────────────────┤
│               features                   │  ← User interactions
├─────────────────────────────────────────┤
│               entities                   │  ← Business entities
├─────────────────────────────────────────┤
│                shared                    │  ← Reusable infrastructure
└─────────────────────────────────────────┘
```

### Layer Responsibilities in Our Context

| Layer | Purpose | Examples in Our App |
|-------|---------|---------------------|
| **app** | Application bootstrap, providers, global styles | Redux store setup, Router configuration, Theme provider |
| **pages** | Route-level components, page composition | CategoryManagementPage, TemplateEditorPage, UserAssignmentPage |
| **widgets** | Self-contained UI blocks with business logic | CategoryTreeWidget, QueryBuilderWidget, AssignmentMatrixWidget |
| **features** | Interactive functionality units | CreateCategory, ApplyTemplate, AssignToGroup |
| **entities** | Core business data and operations | Category, Template, User, Group, Prompt |
| **shared** | Reusable utilities without business logic | UI Kit, API client, validation utilities |

### Import Rules

FSD enforces strict import rules to maintain architectural integrity:

```typescript
// ✅ ALLOWED: Lower layers can be imported by higher layers
// pages can import from widgets, features, entities, shared

// pages/CategoryManagement/ui/CategoryManagementPage.tsx
import { CategoryTreeWidget } from '@/widgets/CategoryTree';
import { CreateCategoryFeature } from '@/features/CreateCategory';
import { Category } from '@/entities/Category';
import { Button } from '@/shared/ui';

// ❌ FORBIDDEN: Higher layers cannot be imported by lower layers
// entities/Category/model/categorySlice.ts
import { CategoryTreeWidget } from '@/widgets/CategoryTree'; // ERROR!

// ❌ FORBIDDEN: Cross-imports within the same layer (with exceptions)
// features/CreateCategory/ui/CreateCategoryForm.tsx
import { ApplyTemplate } from '@/features/ApplyTemplate'; // ERROR!
```

---

## Directory Structure

### Root Structure

```
insight-insight-category-ui/
├── src/
│   ├── app/                          # Application layer
│   │   ├── providers/                # Context providers
│   │   │   ├── StoreProvider.tsx
│   │   │   ├── ThemeProvider.tsx
│   │   │   └── RouterProvider.tsx
│   │   ├── styles/                   # Global styles
│   │   │   ├── index.scss
│   │   │   ├── variables.scss
│   │   │   └── reset.scss
│   │   ├── store/                    # Redux store configuration
│   │   │   ├── index.ts
│   │   │   ├── rootReducer.ts
│   │   │   └── middleware.ts
│   │   └── index.tsx                 # Application entry point
│   │
│   ├── pages/                        # Page layer
│   │   ├── CategoryManagement/
│   │   ├── TemplateEditor/
│   │   ├── UserAssignment/
│   │   ├── PromptManagement/
│   │   └── index.ts                  # Public API
│   │
│   ├── widgets/                      # Widget layer
│   │   ├── CategoryTree/
│   │   ├── QueryBuilder/
│   │   ├── AssignmentMatrix/
│   │   ├── PromptEditor/
│   │   └── index.ts
│   │
│   ├── features/                     # Feature layer
│   │   ├── CreateCategory/
│   │   ├── EditCategory/
│   │   ├── DeleteCategory/
│   │   ├── ApplyTemplate/
│   │   ├── ManagePrompts/
│   │   ├── AssignToUser/
│   │   ├── AssignToGroup/
│   │   └── index.ts
│   │
│   ├── entities/                     # Entity layer
│   │   ├── Category/
│   │   ├── Template/
│   │   ├── User/
│   │   ├── Group/
│   │   ├── Prompt/
│   │   ├── Dictionary/
│   │   └── index.ts
│   │
│   └── shared/                       # Shared layer
│       ├── api/                      # API client and utilities
│       ├── ui/                       # UI component library
│       ├── lib/                      # Utility libraries
│       ├── config/                   # Configuration constants
│       ├── types/                    # Shared TypeScript types
│       └── index.ts
│
├── public/                           # Static assets
├── tests/                            # Test utilities and setup
├── .env                              # Environment variables
├── package.json
├── tsconfig.json
├── webpack.config.js
└── README.md
```

### Slice Structure (Standard Pattern)

Each slice (feature, entity, widget) follows a consistent internal structure:

```
entities/Category/
├── api/                              # API calls for this entity
│   ├── categoryApi.ts
│   └── index.ts
├── model/                            # Business logic and state
│   ├── types.ts                      # TypeScript interfaces
│   ├── categorySlice.ts              # Redux slice
│   ├── selectors.ts                  # Memoized selectors
│   ├── thunks.ts                     # Async actions
│   └── index.ts
├── ui/                               # UI components
│   ├── CategoryCard/
│   │   ├── CategoryCard.tsx
│   │   ├── CategoryCard.module.scss
│   │   └── index.ts
│   ├── CategoryBadge/
│   │   ├── CategoryBadge.tsx
│   │   └── index.ts
│   └── index.ts
├── lib/                              # Entity-specific utilities
│   ├── categoryHelpers.ts
│   ├── queryParser.ts
│   └── index.ts
└── index.ts                          # Public API (slice barrel)
```

### Public API Pattern

Each slice exposes a carefully curated public API through its `index.ts`:

```typescript
// entities/Category/index.ts

// Types
export type { Category, CategoryQuery, CategoryStatus } from './model/types';

// State management
export { categoryReducer } from './model/categorySlice';
export { 
  selectAllCategories, 
  selectCategoryById,
  selectCategoriesByStatus 
} from './model/selectors';
export { 
  fetchCategories, 
  createCategory, 
  updateCategory 
} from './model/thunks';

// UI Components
export { CategoryCard } from './ui/CategoryCard';
export { CategoryBadge } from './ui/CategoryBadge';

// Utilities
export { parseQuerySyntax, validateCategoryQuery } from './lib';
```

---

## Entity Layer Organization

The entity layer forms the foundation of our business logic. Each entity represents a core domain concept in the Insight categorization system.

### Category Entity

The Category entity is the central domain object, representing a classification rule for call analysis.

```typescript
// entities/Category/model/types.ts

export interface Category {
  id: string;
  name: string;
  description: string;
  query: CategoryQuery;
  status: CategoryStatus;
  parentId: string | null;
  children: string[];  // Child category IDs
  metadata: CategoryMetadata;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface CategoryQuery {
  raw: string;                        // Raw query string with syntax
  parsed: ParsedQueryNode;            // AST representation
  validationStatus: ValidationStatus;
  transcriptionPartner: TranscriptionPartner;
}

export type CategoryStatus = 'draft' | 'active' | 'archived' | 'error';

export interface CategoryMetadata {
  templateId?: string;
  tags: string[];
  assignedUsers: string[];
  assignedGroups: string[];
  integrations: IntegrationConfig[];
}

export type TranscriptionPartner = 
  | 'default' 
  | 'partner_a' 
  | 'partner_b' 
  | 'custom';
```

### Template Entity

Templates provide reusable category configurations:

```typescript
// entities/Template/model/types.ts

export interface Template {
  id: string;
  name: string;
  description: string;
  version: number;
  categories: TemplateCategory[];
  variables: TemplateVariable[];
  isPublic: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface TemplateCategory {
  localId: string;                    // ID within template
  name: string;
  queryTemplate: string;              // Query with variable placeholders
  parentLocalId: string | null;
}

export interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'dictionary';
  defaultValue: unknown;
  required: boolean;
  description: string;
}
```

### User and Group Entities

Support both Salesforce and Sapien user systems:

```typescript
// entities/User/model/types.ts

export interface User {
  id: string;
  externalId: string;
  source: UserSource;
  email: string;
  displayName: string;
  role: UserRole;
  groupIds: string[];
  preferences: UserPreferences;
}

export type UserSource = 'salesforce' | 'sapien' | 'internal';

export interface Group {
  id: string;
  name: string;
  description: string;
  source: UserSource;
  memberIds: string[];
  parentGroupId: string | null;
  permissions: GroupPermissions;
}
```

### Entity Relationships Diagram

```
┌─────────────┐     contains      ┌─────────────┐
│   Template  │──────────────────▶│   Category  │
└─────────────┘                   └─────────────┘
                                        │
                                        │ assigned to
                                        ▼
                                  ┌─────────────┐
                                  │    User     │
                                  └─────────────┘
                                        │
                                        │ belongs to
                                        ▼
                                  ┌─────────────┐
                                  │    Group    │
                                  └─────────────┘
                                        │
┌─────────────┐                         │
│   Prompt    │─────────────────────────┘
└─────────────┘     associated with
```

---

## State Management with Redux

### Store Configuration

The Redux store is configured with Redux Toolkit, providing a balance of power and simplicity:

```typescript
// app/store/index.ts

import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { rootReducer } from './rootReducer';
import { apiMiddleware } from './middleware';

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore certain action types for serialization
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['category.query.parsed'],
      },
      thunk: {
        extraArgument: {
          apiClient: createApiClient(),
        },
      },
    }).concat(apiMiddleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Enable refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### Root Reducer Composition

```typescript
// app/store/rootReducer.ts

import { combineReducers } from '@reduxjs/toolkit';
import { categoryReducer } from '@/entities/Category';
import { templateReducer } from '@/entities/Template';
import { userReducer } from '@/entities/User';
import { groupReducer } from '@/entities/Group';
import { promptReducer } from '@/entities/Prompt';
import { uiReducer } from '@/shared/ui/model';

export const rootReducer = combineReducers({
  categories: categoryReducer,
  templates: templateReducer,
  users: userReducer,
  groups: groupReducer,
  prompts: promptReducer,
  ui: uiReducer,
});

export type RootState = ReturnType<typeof rootReducer>;
```

### Entity Slice Pattern

Each entity follows a standardized slice pattern:

```typescript
// entities/Category/model/categorySlice.ts

import { 
  createSlice, 
  createEntityAdapter,
  PayloadAction 
} from '@reduxjs/toolkit';
import { Category, CategoryStatus } from './types';
import { 
  fetchCategories, 
  createCategory, 
  updateCategory, 
  deleteCategory 
} from './thunks';

// Entity adapter for normalized state
const categoryAdapter = createEntityAdapter<Category>({
  selectId: (category) => category.id,
  sortComparer: (a, b) => a.name.localeCompare(b.name),
});

interface CategoryState {
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  selectedId: string | null;
  filters: CategoryFilters;
  expandedIds: string[];
}

const initialState = categoryAdapter.getInitialState<CategoryState>({
  status: 'idle',
  error: null,
  selectedId: null,
  filters: {
    status: null,
    search: '',
    tags: [],
  },
  expandedIds: [],
});

const categorySlice = createSlice({
  name: 'categories',
  initialState,
  reducers: {
    categorySelected(state, action: PayloadAction<string | null>) {
      state.selectedId = action.payload;
    },
    filtersUpdated(state, action: PayloadAction<Partial<CategoryFilters>>) {
      state.filters = { ...state.filters, ...action.payload };
    },
    categoryExpanded(state, action: PayloadAction<string>) {
      if (!state.expandedIds.includes(action.payload)) {
        state.expandedIds.push(action.payload);
      }
    },
    categoryCollapsed(state, action: PayloadAction<string>) {
      state.expandedIds = state.expandedIds.filter(id => id !== action.payload);
    },
    resetCategoryState(state) {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch categories
      .addCase(fetchCategories.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.status = 'succeeded';
        categoryAdapter.setAll(state, action.payload);
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      })
      // Create category
      .addCase(createCategory.fulfilled, (state, action) => {
        categoryAdapter.addOne(state, action.payload);
      })
      // Update category
      .addCase(updateCategory.fulfilled, (state, action) => {
        categoryAdapter.upsertOne(state, action.payload);
      })
      // Delete category
      .addCase(deleteCategory.fulfilled, (state, action) => {
        categoryAdapter.removeOne(state, action.payload);
        if (state.selectedId === action.payload) {
          state.selectedId = null;
        }
      });
  },
});

export const { 
  categorySelected, 
  filtersUpdated, 
  categoryExpanded,
  categoryCollapsed,
  resetCategoryState 
} = categorySlice.actions;

export const categoryReducer = categorySlice.reducer;

// Export adapter selectors
export const {
  selectAll: selectAllCategoriesRaw,
  selectById: selectCategoryByIdRaw,
  selectIds: selectCategoryIds,
} = categoryAdapter.getSelectors();
```

### Async Thunks Pattern

```typescript
// entities/Category/model/thunks.ts

import { createAsyncThunk } from '@reduxjs/toolkit';
import { Category, CreateCategoryDTO, UpdateCategoryDTO } from './types';
import { categoryApi } from '../api';

export const fetchCategories = createAsyncThunk<
  Category[],
  void,
  { rejectValue: string }
>(
  'categories/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await categoryApi.getAll();
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const createCategory = createAsyncThunk<
  Category,
  CreateCategoryDTO,
  { rejectValue: string }
>(
  'categories/create',
  async (dto, { rejectWithValue, dispatch }) => {
    try {
      const response = await categoryApi.create(dto);
      
      // Side effect: Show success notification
      dispatch(showNotification({
        type: 'success',
        message: `Category "${dto.name}" created successfully`,
      }));
      
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const updateCategory = createAsyncThunk<
  Category,
  { id: string; updates: UpdateCategoryDTO },
  { rejectValue: string }
>(
  'categories/update',
  async ({ id, updates }, { rejectWithValue }) => {
    try {
      const response = await categoryApi.update(id, updates);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);
```

### Memoized Selectors

```typescript
// entities/Category/model/selectors.ts

import { createSelector } from '@reduxjs/toolkit';
import { RootState } from '@/app/store';
import { selectAllCategoriesRaw, selectCategoryByIdRaw } from './categorySlice';

const selectCategoryState = (state: RootState) => state.categories;

export const selectAllCategories = createSelector(
  [selectCategoryState],
  (state) => selectAllCategoriesRaw(state)
);

export const selectCategoryById = (id: string) =>
  createSelector(
    [selectCategoryState],
    (state) => selectCategoryByIdRaw(state, id)
  );

export const selectCategoriesLoading = createSelector(
  [selectCategoryState],
  (state) => state.status === 'loading'
);

export const selectCategoriesError = createSelector(
  [selectCategoryState],
  (state) => state.error
);

export const selectSelectedCategory = createSelector(
  [selectCategoryState],
  (state) => state.selectedId 
    ? selectCategoryByIdRaw(state, state.selectedId) 
    : null
);

export const selectFilteredCategories = createSelector(
  [selectAllCategories, selectCategoryState],
  (categories, state) => {
    const { status, search, tags } = state.filters;
    
    return categories.filter((category) => {
      if (status && category.status !== status) return false;
      if (search && !category.name.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      if (tags.length > 0 && !tags.some(tag => category.metadata.tags.includes(tag))) {
        return false;
      }
      return true;
    });
  }
);

// Hierarchical tree selector for CategoryTree widget
export const selectCategoryTree = createSelector(
  [selectAllCategories],
  (categories) => {
    const rootCategories = categories.filter(c => c.parentId === null);
    
    const buildTree = (category: Category): CategoryTreeNode => ({
      ...category,
      children: categories
        .filter(c => c.parentId === category.id)
        .map(buildTree),
    });
    
    return rootCategories.map(buildTree);
  }
);
```

---

## Data Flow Patterns

### Unidirectional Data Flow

The application follows a strict unidirectional data flow:

```
┌─────────────────────────────────────────────────────────────┐
│                         User Action                          │
│                    (Click, Input, Submit)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Action Dispatch                         │
│              (Sync action or Async thunk)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reducer Processing                        │
│              (State transformation logic)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        New State                             │
│                  (Immutable state tree)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Selector Layer                          │
│               (Memoized derived state)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Component Re-render                       │
│                (React reconciliation)                        │
└─────────────────────────────────────────────────────────────┘
```

### Feature-to-Entity Communication

Features communicate with entities through well-defined patterns:

```typescript
// features/CreateCategory/ui/CreateCategoryForm.tsx

import { useAppDispatch, useAppSelector } from '@/shared/lib/hooks';
import { 
  createCategory, 
  selectCategoriesLoading,
  Category 
} from '@/entities/Category';
import { selectAllTemplates, Template } from '@/entities/Template';

export const CreateCategoryForm: React.FC = () => {
  const dispatch = useAppDispatch();
  const isLoading = useAppSelector(selectCategoriesLoading);
  const templates = useAppSelector(selectAllTemplates);
  
  const [formData, setFormData] = useState<CreateCategoryDTO>({
    name: '',
    description: '',
    query: '',
    parentId: null,
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await dispatch(createCategory(formData)).unwrap();
      // Success handling
      onSuccess?.();
    } catch (error) {
      // Error handling
      console.error('Failed to create category:', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
};
```

### Cross-Entity Operations

For operations spanning multiple entities:

```typescript
// features/ApplyTemplate/model/thunks.ts

import { createAsyncThunk } from '@reduxjs/toolkit';
import { createCategory } from '@/entities/Category';
import { selectTemplateById } from '@/entities/Template';
import { RootState } from '@/app/store';

export const applyTemplate = createAsyncThunk<
  void,
  { templateId: string; variables: Record<string, unknown> },
  { state: RootState; rejectValue: string }
>(
  'features/applyTemplate',
  async ({ templateId, variables }, { getState, dispatch, rejectWithValue }) => {
    const state = getState();
    const template = selectTemplateById(templateId)(state);
    
    if (!template) {
      return rejectWithValue('Template not found');
    }
    
    try {
      // Apply template by creating categories
      const categoryIdMap = new Map<string, string>();
      
      for (const templateCategory of template.categories) {
        const resolvedQuery = resolveVariables(
          templateCategory.queryTemplate, 
          variables
        );
        
        const parentId = templateCategory.parentLocalId
          ? categoryIdMap.get(templateCategory.parentLocalId)
          : null;
        
        const result = await dispatch(createCategory({
          name: templateCategory.name,
          query: resolvedQuery,
          parentId,
          metadata: { templateId },
        })).unwrap();
        
        categoryIdMap.set(templateCategory.localId, result.id);
      }
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);
```

### API Integration Pattern

```typescript
// shared/api/apiClient.ts

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

class ApiClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        const token = getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          store.dispatch(logout());
        }
        return Promise.reject(error);
      }
    );
  }
  
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }
  
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }
  
  // ... other methods
}

export const apiClient = new ApiClient();
```

### Entity API Layer

```typescript
// entities/Category/api/categoryApi.ts

import { apiClient } from '@/shared/api';
import { Category, CreateCategoryDTO, UpdateCategoryDTO } from '../model/types';

export const categoryApi = {
  getAll: () => 
    apiClient.get<Category[]>('/api/categories'),
  
  getById: (id: string) => 
    apiClient.get<Category>(`/api/categories/${id}`),
  
  create: (dto: CreateCategoryDTO) => 
    apiClient.post<Category>('/api/categories', dto),
  
  update: (id: string, dto: UpdateCategoryDTO) => 
    apiClient.put<Category>(`/api/categories/${id}`, dto),
  
  delete: (id: string) => 
    apiClient.delete<void>(`/api/categories/${id}`),
  
  validateQuery: (query: string) => 
    apiClient.post<ValidationResult>('/api/categories/validate-query', { query }),
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
const { DefinePlugin } = require('webpack');

const isDevelopment = process.env.NODE_ENV !== 'production';

module.exports = {
  mode: isDevelopment ? 'development' : 'production',
  
  entry: './src/app/index.tsx',
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isDevelopment 
      ? '[name].js' 
      : '[name].[contenthash].js',
    publicPath: '/',
    clean: true,
  },
  
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@app': path.resolve(__dirname, 'src/app'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@widgets': path.resolve(__dirname, 'src/widgets'),
      '@features': path.resolve(__dirname, 'src/features'),
      '@entities': path.resolve(__dirname, 'src/entities'),
      '@shared': path.resolve(__dirname, 'src/shared'),
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
        test: /\.module\.scss$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              modules: {
                localIdentName: isDevelopment
                  ? '[name]__[local]--[hash:base64:5]'
                  : '[hash:base64]',
              },
            },
          },
          'sass-loader',
        ],
      },
      {
        test: /\.scss$/,
        exclude: /\.module\.scss$/,
        use: [
          isDevelopment ? 'style-loader' : MiniCssExtractPlugin.loader,
          'css-loader',
          'sass-loader',
        ],
      },
    ],
  },
  
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
    }),
    new MiniCssExtractPlugin({
      filename: isDevelopment ? '[name].css' : '[name].[contenthash].css',
    }),
    new DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
      'process.env.REACT_APP_API_BASE_URL': JSON.stringify(
        process.env.REACT_APP_API_BASE_URL
      ),
    }),
  ],
  
  devServer: {
    port: 3000,
    hot: true,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        entities: {
          test: /[\\/]src[\\/]entities[\\/]/,
          name: 'entities',
          chunks: 'all',
          minSize: 0,
        },
      },
    },
  },
};
```

### TypeScript Configuration

```json
// tsconfig.json

{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@app/*": ["src/app/*"],
      "@pages/*": ["src/pages/*"],
      "@widgets/*": ["src/widgets/*"],
      "@features/*": ["src/features/*"],
      "@entities/*": ["src/entities/*"],
      "@shared/*": ["src/shared/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### ESLint Configuration for FSD

```javascript
// .eslintrc.js

module.exports = {
  extends: [
    'react-app',
    'react-app/jest',
    '@feature-sliced/eslint-config',
  ],
  rules: {
    // Enforce FSD import rules
    'import/order': [
      'error',
      {
        groups: [
          'builtin',
          'external',
          'internal',
          ['parent', 'sibling', 'index'],
        ],
        pathGroups: [
          { pattern: '@app/**', group: 'internal', position: 'before' },
          { pattern: '@pages/**', group: 'internal', position: 'before' },
          { pattern: '@widgets/**', group: 'internal', position: 'before' },
          { pattern: '@features/**', group: 'internal', position: 'before' },
          { pattern: '@entities/**', group: 'internal', position: 'before' },
          { pattern: '@shared/**', group: 'internal', position: 'before' },
        ],
        pathGroupsExcludedImportTypes: ['builtin'],
        'newlines-between': 'always',
        alphabetize: { order: 'asc', caseInsensitive: true },
      },
    ],
    // Prevent cross-slice imports
    'boundaries/element-types': [
      'error',
      {
        default: 'disallow',
        rules: [
          { from: 'app', allow: ['pages', 'widgets', 'features', 'entities', 'shared'] },
          { from: 'pages', allow: ['widgets', 'features', 'entities', 'shared'] },
          { from: 'widgets', allow: ['features', 'entities', 'shared'] },
          { from: 'features', allow: ['entities', 'shared'] },
          { from: 'entities', allow: ['shared'] },
          { from: 'shared', allow: ['shared'] },
        ],
      },
    ],
  },
};
```

---

## Best Practices and Guidelines

### Do's

1. **Keep slices focused**: Each slice should represent a single business concept
2. **Use public APIs**: Always import from slice index files, not internal modules
3. **Leverage selectors**: Use memoized selectors for derived state
4. **Normalize data**: Use entity adapters for collection management
5. **Type everything**: Leverage TypeScript for full type safety

### Don'ts

1. **Don't skip layers**: Follow the layer hierarchy strictly
2. **Don't create circular dependencies**: Use proper slice composition
3. **Don't store derived state**: Compute it with selectors
4. **Don't mutate state directly**: Use Redux Toolkit's Immer integration
5. **Don't mix business logic with UI**: Keep components presentational when possible

### Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Importing from internal paths | Use public API (index.ts) only |
| Feature-to-feature imports | Extract shared logic to entities/shared |
| Large slice files | Split into model/, api/, ui/ subdirectories |
| Over-fetching data | Implement proper caching with RTK Query |
| Prop drilling | Use selectors at appropriate component level |

---

## Conclusion

The Feature-Sliced Design architecture combined with Redux provides a robust foundation for the insight-insight-category-ui service. By following the patterns and practices outlined in this document, developers can maintain a consistent, scalable, and maintainable codebase as the application grows in complexity.

For questions or clarifications about the architecture, consult the team lead or refer to the official [Feature-Sliced Design documentation](https://feature-sliced.design/).