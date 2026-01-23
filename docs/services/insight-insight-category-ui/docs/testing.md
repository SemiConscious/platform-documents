# Testing Guide

## Overview

This comprehensive testing guide provides strategies, configurations, and best practices for testing the insight-insight-category-ui service. As a React/TypeScript frontend application with Redux state management and Feature-Sliced Design architecture, effective testing is crucial to ensure reliability across the 82 data models, 9 API endpoints, and various integrations with external systems like Salesforce and Sapien.

Testing in this service spans multiple layers: unit tests for individual components and functions, integration tests for Redux slices and API interactions, and visual regression testing to catch UI inconsistencies. This guide will equip you with the knowledge to write maintainable, comprehensive tests that provide confidence in your code changes.

---

## Testing Philosophy

### Core Principles

The insight-insight-category-ui service follows a testing philosophy centered on several key principles:

#### 1. Test Behavior, Not Implementation

Focus on what the component does from a user's perspective, not how it internally accomplishes the task. This approach makes tests more resilient to refactoring and provides better documentation of expected behavior.

```typescript
// ❌ Bad: Testing implementation details
it('should set isLoading state to true', () => {
  const { result } = renderHook(() => useCategoryLoader());
  expect(result.current.state.isLoading).toBe(true);
});

// ✅ Good: Testing behavior
it('should display a loading spinner while categories are being fetched', () => {
  render(<CategoryList />);
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});
```

#### 2. Testing Pyramid Strategy

We follow the testing pyramid approach:

| Test Type | Coverage Target | Execution Speed | Maintenance Cost |
|-----------|----------------|-----------------|------------------|
| Unit Tests | 80%+ | Fast | Low |
| Integration Tests | 60%+ | Medium | Medium |
| E2E Tests | Critical paths | Slow | High |
| Visual Regression | UI components | Medium | Medium |

#### 3. Feature-Sliced Design Testing

Given our FSD architecture, tests should be organized to mirror the feature structure:

```
src/
├── features/
│   └── category-management/
│       ├── ui/
│       │   └── __tests__/
│       │       └── CategoryEditor.test.tsx
│       ├── model/
│       │   └── __tests__/
│       │       └── categorySlice.test.ts
│       └── api/
│           └── __tests__/
│               └── categoryApi.test.ts
```

#### 4. Test Isolation

Each test should be independent and not rely on the state from other tests. This ensures reliable test execution and easier debugging.

---

## Jest Configuration

### Base Configuration

Create or update `jest.config.js` in the project root:

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  modulePaths: ['<rootDir>/src'],
  moduleNameMapper: {
    // Handle CSS imports
    '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',
    '^.+\\.(css|sass|scss)$': '<rootDir>/__mocks__/styleMock.js',
    
    // Handle image imports
    '^.+\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/__mocks__/fileMock.js',
    
    // Handle path aliases (matching tsconfig paths)
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@features/(.*)$': '<rootDir>/src/features/$1',
    '^@shared/(.*)$': '<rootDir>/src/shared/$1',
    '^@entities/(.*)$': '<rootDir>/src/entities/$1',
    '^@widgets/(.*)$': '<rootDir>/src/widgets/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  testMatch: [
    '**/__tests__/**/*.+(ts|tsx|js)',
    '**/?(*.)+(spec|test).+(ts|tsx|js)',
  ],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
    }],
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
    '!src/**/*.stories.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80,
    },
  },
  coverageReporters: ['text', 'lcov', 'html'],
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname',
  ],
};
```

### Setup File

Create `src/setupTests.ts`:

```typescript
// src/setupTests.ts
import '@testing-library/jest-dom';
import { server } from './__mocks__/server';

// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Reset any request handlers that are declared in tests
afterEach(() => {
  server.resetHandlers();
  jest.clearAllMocks();
});

// Clean up after all tests are done
afterAll(() => server.close());

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
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
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback: IntersectionObserverCallback) {}
  observe() { return null; }
  disconnect() { return null; }
  unobserve() { return null; }
} as unknown as typeof IntersectionObserver;

// Suppress console errors in tests (optional)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
```

### Mock Files

```javascript
// __mocks__/styleMock.js
module.exports = {};
```

```javascript
// __mocks__/fileMock.js
module.exports = 'test-file-stub';
```

### NPM Scripts

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2",
    "test:debug": "node --inspect-brk node_modules/.bin/jest --runInBand"
  }
}
```

---

## Unit Testing Components

### Component Testing Patterns

#### Basic Component Test

```typescript
// src/features/category-management/ui/__tests__/CategoryCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CategoryCard } from '../CategoryCard';
import { mockCategory } from '@/__mocks__/data/categories';

describe('CategoryCard', () => {
  const defaultProps = {
    category: mockCategory,
    onEdit: jest.fn(),
    onDelete: jest.fn(),
    onApplyToUsers: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders category information correctly', () => {
    render(<CategoryCard {...defaultProps} />);

    expect(screen.getByText(mockCategory.name)).toBeInTheDocument();
    expect(screen.getByText(mockCategory.description)).toBeInTheDocument();
    expect(screen.getByText(`Query: ${mockCategory.querySyntax}`)).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<CategoryCard {...defaultProps} />);

    const editButton = screen.getByRole('button', { name: /edit/i });
    await user.click(editButton);

    expect(defaultProps.onEdit).toHaveBeenCalledWith(mockCategory.id);
    expect(defaultProps.onEdit).toHaveBeenCalledTimes(1);
  });

  it('shows confirmation dialog before deletion', async () => {
    const user = userEvent.setup();
    render(<CategoryCard {...defaultProps} />);

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await user.click(deleteButton);

    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    expect(defaultProps.onDelete).not.toHaveBeenCalled();

    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);

    expect(defaultProps.onDelete).toHaveBeenCalledWith(mockCategory.id);
  });

  it('renders disabled state correctly', () => {
    render(<CategoryCard {...defaultProps} disabled />);

    expect(screen.getByRole('button', { name: /edit/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled();
  });
});
```

#### Testing Complex Query Syntax Components

Given the category creation features with complex query syntax, testing these components thoroughly is essential:

```typescript
// src/features/category-management/ui/__tests__/QueryBuilder.test.tsx
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryBuilder } from '../QueryBuilder';

describe('QueryBuilder', () => {
  const mockOnQueryChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('query syntax validation', () => {
    it('validates AND operator syntax', async () => {
      const user = userEvent.setup();
      render(<QueryBuilder onQueryChange={mockOnQueryChange} />);

      const input = screen.getByRole('textbox', { name: /query/i });
      await user.type(input, 'term1 AND term2');

      expect(screen.queryByText(/invalid syntax/i)).not.toBeInTheDocument();
      expect(mockOnQueryChange).toHaveBeenCalledWith({
        query: 'term1 AND term2',
        isValid: true,
      });
    });

    it('validates OR operator syntax', async () => {
      const user = userEvent.setup();
      render(<QueryBuilder onQueryChange={mockOnQueryChange} />);

      const input = screen.getByRole('textbox', { name: /query/i });
      await user.type(input, 'term1 OR term2');

      expect(mockOnQueryChange).toHaveBeenCalledWith({
        query: 'term1 OR term2',
        isValid: true,
      });
    });

    it('shows error for invalid nested parentheses', async () => {
      const user = userEvent.setup();
      render(<QueryBuilder onQueryChange={mockOnQueryChange} />);

      const input = screen.getByRole('textbox', { name: /query/i });
      await user.type(input, '((term1 AND term2)');

      expect(screen.getByText(/unmatched parentheses/i)).toBeInTheDocument();
      expect(mockOnQueryChange).toHaveBeenCalledWith(
        expect.objectContaining({ isValid: false })
      );
    });

    it('handles proximity operators', async () => {
      const user = userEvent.setup();
      render(<QueryBuilder onQueryChange={mockOnQueryChange} />);

      const input = screen.getByRole('textbox', { name: /query/i });
      await user.type(input, '"customer service" NEAR/5 "complaint"');

      expect(mockOnQueryChange).toHaveBeenCalledWith({
        query: '"customer service" NEAR/5 "complaint"',
        isValid: true,
      });
    });
  });

  describe('visual query builder', () => {
    it('adds conditions through UI controls', async () => {
      const user = userEvent.setup();
      render(<QueryBuilder onQueryChange={mockOnQueryChange} mode="visual" />);

      const addConditionButton = screen.getByRole('button', { name: /add condition/i });
      await user.click(addConditionButton);

      const conditionGroup = screen.getByTestId('condition-group-0');
      const termInput = within(conditionGroup).getByRole('textbox');
      await user.type(termInput, 'satisfaction');

      const operatorSelect = within(conditionGroup).getByRole('combobox');
      await user.selectOptions(operatorSelect, 'AND');

      expect(mockOnQueryChange).toHaveBeenCalled();
    });
  });
});
```

#### Testing Components with Provider Context

```typescript
// src/features/category-management/ui/__tests__/CategoryList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { CategoryList } from '../CategoryList';
import { categorySlice } from '../../model/categorySlice';
import { mockCategories } from '@/__mocks__/data/categories';

const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: {
      categories: categorySlice.reducer,
    },
    preloadedState,
  });
};

const renderWithProviders = (
  component: React.ReactElement,
  { preloadedState = {}, store = createTestStore(preloadedState) } = {}
) => {
  return {
    store,
    ...render(<Provider store={store}>{component}</Provider>),
  };
};

describe('CategoryList', () => {
  it('displays loading state initially', () => {
    renderWithProviders(<CategoryList />, {
      preloadedState: {
        categories: {
          items: [],
          status: 'loading',
          error: null,
        },
      },
    });

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders list of categories', () => {
    renderWithProviders(<CategoryList />, {
      preloadedState: {
        categories: {
          items: mockCategories,
          status: 'succeeded',
          error: null,
        },
      },
    });

    mockCategories.forEach((category) => {
      expect(screen.getByText(category.name)).toBeInTheDocument();
    });
  });

  it('displays error message when fetch fails', () => {
    renderWithProviders(<CategoryList />, {
      preloadedState: {
        categories: {
          items: [],
          status: 'failed',
          error: 'Failed to fetch categories',
        },
      },
    });

    expect(screen.getByText(/failed to fetch categories/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('displays empty state when no categories exist', () => {
    renderWithProviders(<CategoryList />, {
      preloadedState: {
        categories: {
          items: [],
          status: 'succeeded',
          error: null,
        },
      },
    });

    expect(screen.getByText(/no categories found/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create category/i })).toBeInTheDocument();
  });
});
```

---

## Testing Redux Slices

### Slice Testing Patterns

```typescript
// src/features/category-management/model/__tests__/categorySlice.test.ts
import { configureStore } from '@reduxjs/toolkit';
import categoryReducer, {
  categorySlice,
  fetchCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  selectAllCategories,
  selectCategoryById,
  selectCategoriesStatus,
} from '../categorySlice';
import { server } from '@/__mocks__/server';
import { rest } from 'msw';

describe('categorySlice', () => {
  describe('reducers', () => {
    const initialState = {
      items: [],
      status: 'idle' as const,
      error: null,
      selectedId: null,
    };

    it('should return initial state', () => {
      expect(categoryReducer(undefined, { type: 'unknown' })).toEqual(initialState);
    });

    it('should handle setSelectedCategory', () => {
      const actual = categoryReducer(
        initialState,
        categorySlice.actions.setSelectedCategory('cat-123')
      );
      expect(actual.selectedId).toBe('cat-123');
    });

    it('should handle clearError', () => {
      const stateWithError = { ...initialState, error: 'Some error' };
      const actual = categoryReducer(
        stateWithError,
        categorySlice.actions.clearError()
      );
      expect(actual.error).toBeNull();
    });
  });

  describe('async thunks', () => {
    let store: ReturnType<typeof configureStore>;

    beforeEach(() => {
      store = configureStore({
        reducer: { categories: categoryReducer },
      });
    });

    describe('fetchCategories', () => {
      it('should fetch categories successfully', async () => {
        const mockCategories = [
          { id: '1', name: 'Category 1', querySyntax: 'term1' },
          { id: '2', name: 'Category 2', querySyntax: 'term2' },
        ];

        server.use(
          rest.get('/api/categories', (req, res, ctx) => {
            return res(ctx.json(mockCategories));
          })
        );

        await store.dispatch(fetchCategories());

        const state = store.getState().categories;
        expect(state.status).toBe('succeeded');
        expect(state.items).toEqual(mockCategories);
        expect(state.error).toBeNull();
      });

      it('should handle fetch failure', async () => {
        server.use(
          rest.get('/api/categories', (req, res, ctx) => {
            return res(ctx.status(500), ctx.json({ message: 'Server error' }));
          })
        );

        await store.dispatch(fetchCategories());

        const state = store.getState().categories;
        expect(state.status).toBe('failed');
        expect(state.error).toBeTruthy();
      });

      it('should set loading state during fetch', () => {
        store.dispatch(fetchCategories());

        const state = store.getState().categories;
        expect(state.status).toBe('loading');
      });
    });

    describe('createCategory', () => {
      const newCategory = {
        name: 'New Category',
        description: 'Test description',
        querySyntax: 'customer AND satisfaction',
      };

      it('should create category successfully', async () => {
        const createdCategory = { id: 'new-123', ...newCategory };

        server.use(
          rest.post('/api/categories', (req, res, ctx) => {
            return res(ctx.json(createdCategory));
          })
        );

        const result = await store.dispatch(createCategory(newCategory));

        expect(result.type).toBe('categories/createCategory/fulfilled');
        const state = store.getState().categories;
        expect(state.items).toContainEqual(createdCategory);
      });

      it('should handle validation errors', async () => {
        server.use(
          rest.post('/api/categories', (req, res, ctx) => {
            return res(
              ctx.status(400),
              ctx.json({
                errors: [{ field: 'name', message: 'Name is required' }],
              })
            );
          })
        );

        const result = await store.dispatch(createCategory({ ...newCategory, name: '' }));

        expect(result.type).toBe('categories/createCategory/rejected');
      });
    });

    describe('updateCategory', () => {
      it('should update existing category', async () => {
        const existingCategory = { id: '1', name: 'Original', querySyntax: 'term' };
        const updatedData = { name: 'Updated Name' };

        // Pre-populate store
        store = configureStore({
          reducer: { categories: categoryReducer },
          preloadedState: {
            categories: {
              items: [existingCategory],
              status: 'succeeded',
              error: null,
              selectedId: null,
            },
          },
        });

        server.use(
          rest.put('/api/categories/:id', (req, res, ctx) => {
            return res(ctx.json({ ...existingCategory, ...updatedData }));
          })
        );

        await store.dispatch(updateCategory({ id: '1', updates: updatedData }));

        const state = store.getState().categories;
        expect(state.items[0].name).toBe('Updated Name');
      });
    });
  });

  describe('selectors', () => {
    const stateWithCategories = {
      categories: {
        items: [
          { id: '1', name: 'Category A', querySyntax: 'term1' },
          { id: '2', name: 'Category B', querySyntax: 'term2' },
        ],
        status: 'succeeded' as const,
        error: null,
        selectedId: '1',
      },
    };

    it('selectAllCategories returns all categories', () => {
      const result = selectAllCategories(stateWithCategories);
      expect(result).toHaveLength(2);
    });

    it('selectCategoryById returns specific category', () => {
      const result = selectCategoryById(stateWithCategories, '1');
      expect(result?.name).toBe('Category A');
    });

    it('selectCategoryById returns undefined for non-existent id', () => {
      const result = selectCategoryById(stateWithCategories, 'non-existent');
      expect(result).toBeUndefined();
    });

    it('selectCategoriesStatus returns current status', () => {
      const result = selectCategoriesStatus(stateWithCategories);
      expect(result).toBe('succeeded');
    });
  });
});
```

### Testing API Integration with RTK Query

```typescript
// src/features/category-management/api/__tests__/categoryApi.test.ts
import { setupApiStore } from '@/__mocks__/testUtils';
import { categoryApi } from '../categoryApi';
import { server } from '@/__mocks__/server';
import { rest } from 'msw';

describe('categoryApi', () => {
  const storeRef = setupApiStore(categoryApi);

  describe('getCategories', () => {
    it('successful query', async () => {
      const mockData = [{ id: '1', name: 'Test Category' }];

      server.use(
        rest.get('/api/categories', (req, res, ctx) => {
          return res(ctx.json(mockData));
        })
      );

      const result = await storeRef.store.dispatch(
        categoryApi.endpoints.getCategories.initiate()
      );

      expect(result.data).toEqual(mockData);
      expect(result.isSuccess).toBe(true);
    });

    it('handles network error', async () => {
      server.use(
        rest.get('/api/categories', (req, res) => {
          return res.networkError('Network error');
        })
      );

      const result = await storeRef.store.dispatch(
        categoryApi.endpoints.getCategories.initiate()
      );

      expect(result.isError).toBe(true);
    });
  });

  describe('cache invalidation', () => {
    it('invalidates cache after mutation', async () => {
      // Initial fetch
      await storeRef.store.dispatch(
        categoryApi.endpoints.getCategories.initiate()
      );

      // Mutation
      await storeRef.store.dispatch(
        categoryApi.endpoints.createCategory.initiate({
          name: 'New',
          querySyntax: 'test',
        })
      );

      // Check that cache was invalidated
      const state = storeRef.store.getState();
      const cachedData = categoryApi.endpoints.getCategories.select()(state);
      expect(cachedData.status).toBe('pending'); // Re-fetching
    });
  });
});
```

---

## Visual Regression Testing

### Setup with Storybook and Chromatic

```typescript
// .storybook/main.ts
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@chromatic-com/storybook',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
};

export default config;
```

### Writing Stories for Visual Testing

```typescript
// src/features/category-management/ui/CategoryCard.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { within, userEvent } from '@storybook/testing-library';
import { expect } from '@storybook/jest';
import { CategoryCard } from './CategoryCard';

const meta: Meta<typeof CategoryCard> = {
  title: 'Features/CategoryManagement/CategoryCard',
  component: CategoryCard,
  parameters: {
    layout: 'centered',
    chromatic: { viewports: [320, 768, 1200] },
  },
  tags: ['autodocs'],
  argTypes: {
    onEdit: { action: 'edit clicked' },
    onDelete: { action: 'delete clicked' },
  },
};

export default meta;
type Story = StoryObj<typeof CategoryCard>;

export const Default: Story = {
  args: {
    category: {
      id: '1',
      name: 'Customer Satisfaction',
      description: 'Tracks mentions of customer satisfaction',
      querySyntax: 'satisfied OR happy OR "great service"',
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-15T10:00:00Z',
    },
  },
};

export const LongContent: Story = {
  args: {
    category: {
      id: '2',
      name: 'Very Long Category Name That Might Cause Layout Issues',
      description: 'This is a very long description that tests how the card handles overflow content. It should truncate or wrap appropriately without breaking the layout.',
      querySyntax: '(term1 AND term2) OR (term3 AND term4) OR (term5 NEAR/5 term6)',
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-15T10:00:00Z',
    },
  },
};

export const Disabled: Story = {
  args: {
    ...Default.args,
    disabled: true,
  },
};

export const WithInteraction: Story = {
  args: Default.args,
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const editButton = canvas.getByRole('button', { name: /edit/i });
    await userEvent.click(editButton);
    
    // Verify hover states and interactions
    await expect(editButton).toHaveBeenCalled;
  },
};

export const HoverState: Story = {
  args: Default.args,
  parameters: {
    pseudo: { hover: true },
  },
};

export const FocusState: Story = {
  args: Default.args,
  parameters: {
    pseudo: { focus: true },
  },
};
```

### Jest Image Snapshot Testing

```typescript
// src/features/category-management/ui/__tests__/CategoryCard.visual.test.tsx
import { render } from '@testing-library/react';
import { generateImage } from 'jsdom-screenshot';
import { CategoryCard } from '../CategoryCard';

describe('CategoryCard Visual Tests', () => {
  it('matches snapshot in default state', async () => {
    render(
      <CategoryCard
        category={{
          id: '1',
          name: 'Test Category',
          description: 'Test description',
          querySyntax: 'test',
        }}
        onEdit={jest.fn()}
        onDelete={jest.fn()}
      />
    );

    const screenshot = await generateImage();
    expect(screenshot).toMatchImageSnapshot();
  });

  it('matches snapshot in disabled state', async () => {
    render(
      <CategoryCard
        category={{
          id: '1',
          name: 'Test Category',
          description: 'Test description',
          querySyntax: 'test',
        }}
        onEdit={jest.fn()}
        onDelete={jest.fn()}
        disabled
      />
    );

    const screenshot = await generateImage();
    expect(screenshot).toMatchImageSnapshot({
      customSnapshotIdentifier: 'category-card-disabled',
    });
  });
});
```

---

## Test Utilities and Mocks

### Custom Test Utilities

```typescript
// src/__mocks__/testUtils.tsx
import React, { PropsWithChildren } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore, PreloadedState } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { rootReducer, RootState } from '@/app/store';
import { theme } from '@/shared/theme';

interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: PreloadedState<RootState>;
  store?: ReturnType<typeof configureStore>;
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState = {},
    store = configureStore({
      reducer: rootReducer,
      preloadedState,
    }),
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: PropsWithChildren<{}>): JSX.Element {
    return (
      <Provider store={store}>
        <BrowserRouter>
          <ThemeProvider theme={theme}>{children}</ThemeProvider>
        </BrowserRouter>
      </Provider>
    );
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

// Re-export everything
export * from '@testing-library/react';
export { renderWithProviders as render };
```

### API Mocking with MSW

```typescript
// src/__mocks__/handlers.ts
import { rest } from 'msw';
import { mockCategories, mockTemplates } from './data';

const API_BASE = process.env.REACT_APP_API_URL || '';

export const handlers = [
  // Categories
  rest.get(`${API_BASE}/api/categories`, (req, res, ctx) => {
    return res(ctx.json(mockCategories));
  }),

  rest.get(`${API_BASE}/api/categories/:id`, (req, res, ctx) => {
    const { id } = req.params;
    const category = mockCategories.find((c) => c.id === id);
    
    if (!category) {
      return res(ctx.status(404), ctx.json({ message: 'Category not found' }));
    }
    
    return res(ctx.json(category));
  }),

  rest.post(`${API_BASE}/api/categories`, async (req, res, ctx) => {
    const body = await req.json();
    const newCategory = {
      id: `cat-${Date.now()}`,
      ...body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return res(ctx.status(201), ctx.json(newCategory));
  }),

  rest.put(`${API_BASE}/api/categories/:id`, async (req, res, ctx) => {
    const { id } = req.params;
    const body = await req.json();
    const category = mockCategories.find((c) => c.id === id);
    
    if (!category) {
      return res(ctx.status(404), ctx.json({ message: 'Category not found' }));
    }
    
    return res(ctx.json({ ...category, ...body }));
  }),

  rest.delete(`${API_BASE}/api/categories/:id`, (req, res, ctx) => {
    return res(ctx.status(204));
  }),

  // Templates
  rest.get(`${API_BASE}/api/templates`, (req, res, ctx) => {
    return res(ctx.json(mockTemplates));
  }),

  // User/Group assignments (Salesforce/Sapien integration)
  rest.get(`${API_BASE}/api/users`, (req, res, ctx) => {
    const source = req.url.searchParams.get('source');
    return res(
      ctx.json({
        users: source === 'salesforce' ? mockSalesforceUsers : mockSapienUsers,
        source,
      })
    );
  }),

  rest.post(`${API_BASE}/api/categories/:id/assign`, async (req, res, ctx) => {
    const { id } = req.params;
    const { userIds, groupIds } = await req.json();
    
    return res(
      ctx.json({
        categoryId: id,
        assignedUsers: userIds,
        assignedGroups: groupIds,
      })
    );
  }),
];
```

```typescript
// src/__mocks__/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

### Mock Data Factories

```typescript
// src/__mocks__/data/factories.ts
import { faker } from '@faker-js/faker';
import type { Category, Template, User, Group } from '@/shared/types';

export const createMockCategory = (overrides: Partial<Category> = {}): Category => ({
  id: faker.string.uuid(),
  name: faker.commerce.department(),
  description: faker.lorem.sentence(),
  querySyntax: `${faker.word.noun()} AND ${faker.word.noun()}`,
  isActive: true,
  createdAt: faker.date.past().toISOString(),
  updatedAt: faker.date.recent().toISOString(),
  createdBy: faker.string.uuid(),
  ...overrides,
});

export const createMockTemplate = (overrides: Partial<Template> = {}): Template => ({
  id: faker.string.uuid(),
  name: faker.commerce.productName(),
  description: faker.lorem.paragraph(),
  categories: [createMockCategory(), createMockCategory()],
  isDefault: false,
  createdAt: faker.date.past().toISOString(),
  ...overrides,
});

export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  firstName: faker.person.firstName(),
  lastName: faker.person.lastName(),
  source: faker.helpers.arrayElement(['salesforce', 'sapien']),
  ...overrides,
});

export const createMockCategories = (count: number): Category[] =>
  Array.from({ length: count }, () => createMockCategory());
```

```typescript
// src/__mocks__/data/index.ts
import { createMockCategories, createMockTemplate, createMockUser } from './factories';

export const mockCategories = createMockCategories(5);

export const mockTemplates = [
  createMockTemplate({ name: 'Customer Service Template', isDefault: true }),
  createMockTemplate({ name: 'Sales Analysis Template' }),
  createMockTemplate({ name: 'Compliance Monitoring Template' }),
];

export const mockSalesforceUsers = Array.from({ length: 10 }, () =>
  createMockUser({ source: 'salesforce' })
);

export const mockSapienUsers = Array.from({ length: 10 }, () =>
  createMockUser({ source: 'sapien' })
);

export const mockCategory = mockCategories[0];
```

### Custom Jest Matchers

```typescript
// src/__mocks__/customMatchers.ts
import { expect } from '@jest/globals';

expect.extend({
  toBeValidQuerySyntax(received: string) {
    const validOperators = ['AND', 'OR', 'NOT', 'NEAR'];
    const hasValidStructure = /^[\w\s"()\/]+$/.test(received);
    const hasBalancedParentheses =
      (received.match(/\(/g) || []).length ===
      (received.match(/\)/g) || []).length;

    const pass = hasValidStructure && hasBalancedParentheses;

    return {
      message: () =>
        pass
          ? `expected "${received}" not to be valid query syntax`
          : `expected "${received}" to be valid query syntax`,
      pass,
    };
  },

  toHaveBeenCalledWithCategory(received: jest.Mock, expectedCategory: { id: string }) {
    const calls = received.mock.calls;
    const pass = calls.some(
      (call) => call[0]?.id === expectedCategory.id
    );

    return {
      message: () =>
        pass
          ? `expected mock not to have been called with category id "${expectedCategory.id}"`
          : `expected mock to have been called with category id "${expectedCategory.id}"`,
      pass,
    };
  },
});

// Type declarations
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidQuerySyntax(): R;
      toHaveBeenCalledWithCategory(category: { id: string }): R;
    }
  }
}
```

---

## Best Practices and Common Pitfalls

### Do's

1. **Use meaningful test descriptions** that describe behavior, not implementation
2. **Follow the Arrange-Act-Assert pattern** for clear test structure
3. **Use `userEvent` over `fireEvent`** for more realistic user interactions
4. **Test error states and edge cases** not just happy paths
5. **Keep tests focused** - one behavior per test
6. **Use data-testid sparingly** - prefer accessible queries

### Don'ts

1. **Don't test implementation details** - test what users see and do
2. **Don't use arbitrary timeouts** - use `waitFor` and proper async patterns
3. **Don't couple tests** - each test should be independent
4. **Don't ignore TypeScript errors** in tests
5. **Don't test third-party libraries** - trust they work as documented

### Performance Tips

```typescript
// Use beforeAll for expensive setup
beforeAll(async () => {
  // Database seeding, heavy computations
});

// Use test.concurrent for independent tests
describe('CategoryOperations', () => {
  test.concurrent('create category', async () => { /* ... */ });
  test.concurrent('update category', async () => { /* ... */ });
  test.concurrent('delete category', async () => { /* ... */ });
});
```

---

## Conclusion

This testing guide provides a comprehensive framework for testing the insight-insight-category-ui service. By following these patterns and practices, you'll create a robust test suite that catches bugs early, documents expected behavior, and provides confidence when shipping new features.

Remember that good tests are an investment in code quality and team velocity. Take the time to write thoughtful tests, and they will pay dividends throughout the life of the project.