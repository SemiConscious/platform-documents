# Components Guide

## Overview

This comprehensive guide documents the React component architecture for the Freedom Web application, a sophisticated call center and telephony operations platform. Understanding the component structure, patterns, and styling conventions is essential for developers working on extending or maintaining this frontend application.

Freedom Web utilizes a modular component-based architecture that promotes reusability, maintainability, and consistent user experience across features like active calls management, voicemail handling, address book operations, and team collaboration.

## Component Structure

### Directory Organization

The Freedom Web application follows a well-organized component structure that separates concerns and promotes code reusability:

```
src/
├── components/
│   ├── Home/
│   │   ├── Home.tsx
│   │   ├── Home.module.css
│   │   ├── HomeHeader.tsx
│   │   ├── HomeSidebar.tsx
│   │   └── index.ts
│   ├── shared/
│   │   ├── Button/
│   │   ├── Modal/
│   │   ├── Input/
│   │   ├── Card/
│   │   ├── Table/
│   │   └── index.ts
│   ├── calls/
│   │   ├── ActiveCallsPanel.tsx
│   │   ├── CallLogEntry.tsx
│   │   ├── CallControls.tsx
│   │   └── index.ts
│   ├── voicemail/
│   │   ├── VoicemailList.tsx
│   │   ├── VoicemailPlayer.tsx
│   │   ├── VoicemailDropModal.tsx
│   │   └── index.ts
│   ├── addressbook/
│   │   ├── ContactList.tsx
│   │   ├── ContactCard.tsx
│   │   ├── ContactForm.tsx
│   │   └── index.ts
│   └── team/
│       ├── TeamPanel.tsx
│       ├── TeamMemberCard.tsx
│       ├── ActivityFeed.tsx
│       └── index.ts
├── hooks/
│   ├── useCall.ts
│   ├── useAuth.ts
│   ├── useVoicemail.ts
│   └── useCTI.ts
├── contexts/
│   ├── AuthContext.tsx
│   ├── CallContext.tsx
│   └── CTIContext.tsx
└── styles/
    ├── variables.css
    ├── global.css
    └── mixins.css
```

### Component Naming Conventions

Follow these naming conventions to maintain consistency across the codebase:

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `ActiveCallsPanel.tsx` |
| Hooks | camelCase with `use` prefix | `useCallState.ts` |
| Contexts | PascalCase with `Context` suffix | `AuthContext.tsx` |
| Styles | Component name with `.module.css` | `Button.module.css` |
| Utilities | camelCase | `formatPhoneNumber.ts` |

## Home Component

The Home component serves as the main dashboard and entry point for authenticated users. It orchestrates the primary call center interface, integrating multiple feature panels.

### Home Component Implementation

```typescript
// src/components/Home/Home.tsx
import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useCTI } from '../../hooks/useCTI';
import { HomeHeader } from './HomeHeader';
import { HomeSidebar } from './HomeSidebar';
import { ActiveCallsPanel } from '../calls/ActiveCallsPanel';
import { VoicemailList } from '../voicemail/VoicemailList';
import { TeamPanel } from '../team/TeamPanel';
import { ActivityFeed } from '../team/ActivityFeed';
import styles from './Home.module.css';

interface HomeProps {
  defaultPanel?: 'calls' | 'voicemail' | 'team' | 'contacts';
}

export const Home: React.FC<HomeProps> = ({ defaultPanel = 'calls' }) => {
  const { user, isAuthenticated } = useAuth();
  const { connectionStatus, initializeCTI } = useCTI();
  const [activePanel, setActivePanel] = useState(defaultPanel);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    if (isAuthenticated && connectionStatus === 'disconnected') {
      initializeCTI();
    }
  }, [isAuthenticated, connectionStatus, initializeCTI]);

  const renderActivePanel = () => {
    switch (activePanel) {
      case 'calls':
        return <ActiveCallsPanel />;
      case 'voicemail':
        return <VoicemailList />;
      case 'team':
        return <TeamPanel />;
      case 'contacts':
        return <ContactList />;
      default:
        return <ActiveCallsPanel />;
    }
  };

  return (
    <div className={styles.homeContainer}>
      <HomeHeader 
        user={user}
        connectionStatus={connectionStatus}
        onMenuToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      
      <div className={styles.mainContent}>
        <HomeSidebar
          activePanel={activePanel}
          onPanelChange={setActivePanel}
          collapsed={sidebarCollapsed}
        />
        
        <main className={styles.contentArea}>
          {renderActivePanel()}
        </main>
        
        <aside className={styles.activitySidebar}>
          <ActivityFeed userId={user?.id} />
        </aside>
      </div>
    </div>
  );
};

export default Home;
```

### Home Header Component

```typescript
// src/components/Home/HomeHeader.tsx
import React from 'react';
import { User } from '../../types/user';
import { ConnectionStatus } from '../../types/cti';
import { Button } from '../shared/Button';
import { StatusIndicator } from '../shared/StatusIndicator';
import styles from './HomeHeader.module.css';

interface HomeHeaderProps {
  user: User | null;
  connectionStatus: ConnectionStatus;
  onMenuToggle: () => void;
}

export const HomeHeader: React.FC<HomeHeaderProps> = ({
  user,
  connectionStatus,
  onMenuToggle,
}) => {
  const getStatusColor = (status: ConnectionStatus): string => {
    const statusColors: Record<ConnectionStatus, string> = {
      connected: 'green',
      connecting: 'yellow',
      disconnected: 'red',
      error: 'red',
    };
    return statusColors[status];
  };

  return (
    <header className={styles.header}>
      <div className={styles.leftSection}>
        <Button
          variant="ghost"
          icon="menu"
          onClick={onMenuToggle}
          aria-label="Toggle sidebar"
        />
        <h1 className={styles.logo}>Freedom Web</h1>
      </div>

      <div className={styles.centerSection}>
        <StatusIndicator
          status={connectionStatus}
          color={getStatusColor(connectionStatus)}
          label={`CTI: ${connectionStatus}`}
        />
      </div>

      <div className={styles.rightSection}>
        {user && (
          <div className={styles.userInfo}>
            <span className={styles.userName}>{user.displayName}</span>
            <span className={styles.userExtension}>Ext: {user.extension}</span>
          </div>
        )}
        <Button variant="secondary" icon="settings" aria-label="Settings" />
        <Button variant="secondary" icon="logout" aria-label="Logout" />
      </div>
    </header>
  );
};
```

### Home Sidebar Component

```typescript
// src/components/Home/HomeSidebar.tsx
import React from 'react';
import { NavButton } from '../shared/NavButton';
import styles from './HomeSidebar.module.css';

type PanelType = 'calls' | 'voicemail' | 'team' | 'contacts';

interface HomeSidebarProps {
  activePanel: PanelType;
  onPanelChange: (panel: PanelType) => void;
  collapsed: boolean;
}

interface NavItem {
  id: PanelType;
  icon: string;
  label: string;
  badge?: number;
}

export const HomeSidebar: React.FC<HomeSidebarProps> = ({
  activePanel,
  onPanelChange,
  collapsed,
}) => {
  const navItems: NavItem[] = [
    { id: 'calls', icon: 'phone', label: 'Active Calls', badge: 3 },
    { id: 'voicemail', icon: 'voicemail', label: 'Voicemail', badge: 5 },
    { id: 'team', icon: 'users', label: 'Team' },
    { id: 'contacts', icon: 'address-book', label: 'Contacts' },
  ];

  return (
    <nav className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      <ul className={styles.navList}>
        {navItems.map((item) => (
          <li key={item.id}>
            <NavButton
              icon={item.icon}
              label={item.label}
              isActive={activePanel === item.id}
              onClick={() => onPanelChange(item.id)}
              badge={item.badge}
              showLabel={!collapsed}
            />
          </li>
        ))}
      </ul>
    </nav>
  );
};
```

## Shared Components

Shared components form the foundation of the UI library, ensuring consistency and reducing code duplication across the application.

### Button Component

```typescript
// src/components/shared/Button/Button.tsx
import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import { Icon } from '../Icon';
import styles from './Button.module.css';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
type ButtonSize = 'small' | 'medium' | 'large';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: string;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  fullWidth?: boolean;
  children?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'medium',
      icon,
      iconPosition = 'left',
      loading = false,
      fullWidth = false,
      children,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const classNames = [
      styles.button,
      styles[variant],
      styles[size],
      fullWidth && styles.fullWidth,
      loading && styles.loading,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        className={classNames}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <span className={styles.spinner} />}
        {icon && iconPosition === 'left' && !loading && (
          <Icon name={icon} className={styles.iconLeft} />
        )}
        {children && <span className={styles.label}>{children}</span>}
        {icon && iconPosition === 'right' && !loading && (
          <Icon name={icon} className={styles.iconRight} />
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### Modal Component

```typescript
// src/components/shared/Modal/Modal.tsx
import React, { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Button } from '../Button';
import { Icon } from '../Icon';
import styles from './Modal.module.css';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  footer?: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'medium',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  footer,
}) => {
  const handleEscape = useCallback(
    (event: KeyboardEvent) => {
      if (closeOnEscape && event.key === 'Escape') {
        onClose();
      }
    },
    [closeOnEscape, onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, handleEscape]);

  if (!isOpen) return null;

  const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOverlayClick && event.target === event.currentTarget) {
      onClose();
    }
  };

  return createPortal(
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div
        className={`${styles.modal} ${styles[size]}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <header className={styles.header}>
          <h2 id="modal-title" className={styles.title}>
            {title}
          </h2>
          {showCloseButton && (
            <Button
              variant="ghost"
              size="small"
              onClick={onClose}
              aria-label="Close modal"
            >
              <Icon name="close" />
            </Button>
          )}
        </header>

        <div className={styles.content}>{children}</div>

        {footer && <footer className={styles.footer}>{footer}</footer>}
      </div>
    </div>,
    document.body
  );
};
```

### Card Component

```typescript
// src/components/shared/Card/Card.tsx
import React from 'react';
import styles from './Card.module.css';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: 'none' | 'small' | 'medium' | 'large';
  className?: string;
  onClick?: () => void;
  interactive?: boolean;
}

interface CardHeaderProps {
  children: React.ReactNode;
  action?: React.ReactNode;
}

interface CardContentProps {
  children: React.ReactNode;
}

interface CardFooterProps {
  children: React.ReactNode;
  alignment?: 'left' | 'center' | 'right' | 'space-between';
}

export const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>;
  Content: React.FC<CardContentProps>;
  Footer: React.FC<CardFooterProps>;
} = ({
  children,
  variant = 'default',
  padding = 'medium',
  className,
  onClick,
  interactive = false,
}) => {
  const classNames = [
    styles.card,
    styles[variant],
    styles[`padding-${padding}`],
    interactive && styles.interactive,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classNames} onClick={onClick}>
      {children}
    </div>
  );
};

Card.Header = ({ children, action }) => (
  <div className={styles.header}>
    <div className={styles.headerContent}>{children}</div>
    {action && <div className={styles.headerAction}>{action}</div>}
  </div>
);

Card.Content = ({ children }) => (
  <div className={styles.content}>{children}</div>
);

Card.Footer = ({ children, alignment = 'right' }) => (
  <div className={`${styles.footer} ${styles[`align-${alignment}`]}`}>
    {children}
  </div>
);
```

### Table Component

```typescript
// src/components/shared/Table/Table.tsx
import React from 'react';
import styles from './Table.module.css';

interface Column<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  render?: (item: T, index: number) => React.ReactNode;
  sortable?: boolean;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string | number;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
  loading?: boolean;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: string) => void;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyMessage = 'No data available',
  loading = false,
  sortColumn,
  sortDirection,
  onSort,
}: TableProps<T>) {
  const getCellValue = (item: T, column: Column<T>): React.ReactNode => {
    if (column.render) {
      return column.render(item, data.indexOf(item));
    }
    return item[column.key as keyof T] as React.ReactNode;
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <span>Loading...</span>
      </div>
    );
  }

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key as string}
                style={{ width: column.width }}
                className={column.sortable ? styles.sortable : ''}
                onClick={() => column.sortable && onSort?.(column.key as string)}
              >
                <span>{column.header}</span>
                {column.sortable && sortColumn === column.key && (
                  <span className={styles.sortIcon}>
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={styles.emptyRow}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={keyExtractor(item)}
                onClick={() => onRowClick?.(item)}
                className={onRowClick ? styles.clickableRow : ''}
              >
                {columns.map((column) => (
                  <td key={column.key as string}>{getCellValue(item, column)}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
```

## Component Patterns

### Container/Presentational Pattern

Freedom Web uses the Container/Presentational pattern to separate data fetching logic from UI rendering:

```typescript
// Container Component - handles data and state
// src/components/calls/ActiveCallsPanelContainer.tsx
import React from 'react';
import { useActiveCalls } from '../../hooks/useActiveCalls';
import { useCTI } from '../../hooks/useCTI';
import { ActiveCallsPanel } from './ActiveCallsPanel';

export const ActiveCallsPanelContainer: React.FC = () => {
  const { calls, loading, error, refreshCalls } = useActiveCalls();
  const { holdCall, transferCall, endCall } = useCTI();

  const handleHold = async (callId: string) => {
    await holdCall(callId);
    refreshCalls();
  };

  const handleTransfer = async (callId: string, destination: string) => {
    await transferCall(callId, destination);
    refreshCalls();
  };

  const handleEnd = async (callId: string) => {
    await endCall(callId);
    refreshCalls();
  };

  return (
    <ActiveCallsPanel
      calls={calls}
      loading={loading}
      error={error}
      onHold={handleHold}
      onTransfer={handleTransfer}
      onEnd={handleEnd}
      onRefresh={refreshCalls}
    />
  );
};

// Presentational Component - handles UI rendering
// src/components/calls/ActiveCallsPanel.tsx
import React from 'react';
import { Call } from '../../types/call';
import { Card } from '../shared/Card';
import { Button } from '../shared/Button';
import { CallCard } from './CallCard';
import styles from './ActiveCallsPanel.module.css';

interface ActiveCallsPanelProps {
  calls: Call[];
  loading: boolean;
  error: string | null;
  onHold: (callId: string) => void;
  onTransfer: (callId: string, destination: string) => void;
  onEnd: (callId: string) => void;
  onRefresh: () => void;
}

export const ActiveCallsPanel: React.FC<ActiveCallsPanelProps> = ({
  calls,
  loading,
  error,
  onHold,
  onTransfer,
  onEnd,
  onRefresh,
}) => {
  if (error) {
    return (
      <Card variant="outlined">
        <Card.Content>
          <div className={styles.error}>
            <p>Error loading calls: {error}</p>
            <Button onClick={onRefresh}>Retry</Button>
          </div>
        </Card.Content>
      </Card>
    );
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2>Active Calls ({calls.length})</h2>
        <Button variant="ghost" icon="refresh" onClick={onRefresh} />
      </div>

      <div className={styles.callsList}>
        {loading ? (
          <div className={styles.loading}>Loading calls...</div>
        ) : calls.length === 0 ? (
          <div className={styles.empty}>No active calls</div>
        ) : (
          calls.map((call) => (
            <CallCard
              key={call.id}
              call={call}
              onHold={() => onHold(call.id)}
              onTransfer={(dest) => onTransfer(call.id, dest)}
              onEnd={() => onEnd(call.id)}
            />
          ))
        )}
      </div>
    </div>
  );
};
```

### Compound Components Pattern

Used for complex components with related sub-components:

```typescript
// src/components/shared/Tabs/Tabs.tsx
import React, { createContext, useContext, useState } from 'react';
import styles from './Tabs.module.css';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

const useTabsContext = () => {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tab components must be used within a Tabs component');
  }
  return context;
};

interface TabsProps {
  defaultTab: string;
  children: React.ReactNode;
  onChange?: (tab: string) => void;
}

interface TabListProps {
  children: React.ReactNode;
}

interface TabProps {
  id: string;
  children: React.ReactNode;
  disabled?: boolean;
}

interface TabPanelProps {
  id: string;
  children: React.ReactNode;
}

export const Tabs: React.FC<TabsProps> & {
  List: React.FC<TabListProps>;
  Tab: React.FC<TabProps>;
  Panel: React.FC<TabPanelProps>;
} = ({ defaultTab, children, onChange }) => {
  const [activeTab, setActiveTab] = useState(defaultTab);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    onChange?.(tab);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={styles.tabs}>{children}</div>
    </TabsContext.Provider>
  );
};

Tabs.List = ({ children }) => (
  <div className={styles.tabList} role="tablist">
    {children}
  </div>
);

Tabs.Tab = ({ id, children, disabled }) => {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === id;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${id}`}
      className={`${styles.tab} ${isActive ? styles.active : ''}`}
      onClick={() => !disabled && setActiveTab(id)}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

Tabs.Panel = ({ id, children }) => {
  const { activeTab } = useTabsContext();

  if (activeTab !== id) return null;

  return (
    <div
      role="tabpanel"
      id={`panel-${id}`}
      className={styles.tabPanel}
    >
      {children}
    </div>
  );
};

// Usage Example
const CallDetailsView: React.FC = () => (
  <Tabs defaultTab="details">
    <Tabs.List>
      <Tabs.Tab id="details">Details</Tabs.Tab>
      <Tabs.Tab id="notes">Notes</Tabs.Tab>
      <Tabs.Tab id="history">History</Tabs.Tab>
    </Tabs.List>
    <Tabs.Panel id="details">
      <CallDetailsPanel />
    </Tabs.Panel>
    <Tabs.Panel id="notes">
      <CallNotesPanel />
    </Tabs.Panel>
    <Tabs.Panel id="history">
      <CallHistoryPanel />
    </Tabs.Panel>
  </Tabs>
);
```

### Render Props Pattern

Used for flexible component composition:

```typescript
// src/components/shared/DataFetcher/DataFetcher.tsx
import React, { useState, useEffect } from 'react';

interface DataFetcherProps<T> {
  url: string;
  children: (state: {
    data: T | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
  }) => React.ReactNode;
}

export function DataFetcher<T>({ url, children }: DataFetcherProps<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [url]);

  return <>{children({ data, loading, error, refetch: fetchData })}</>;
}

// Usage Example
const VoicemailSection: React.FC = () => (
  <DataFetcher<Voicemail[]> url="/api/v1/voicemails">
    {({ data, loading, error, refetch }) => (
      <VoicemailList
        voicemails={data || []}
        loading={loading}
        error={error}
        onRefresh={refetch}
      />
    )}
  </DataFetcher>
);
```

## Styling with PostCSS

Freedom Web uses PostCSS with CSS Modules for component styling, providing scoped styles and advanced CSS features.

### PostCSS Configuration

```javascript
// postcss.config.js
module.exports = {
  plugins: {
    'postcss-import': {},
    'postcss-nested': {},
    'postcss-custom-properties': {
      preserve: true,
    },
    'postcss-calc': {},
    'postcss-color-function': {},
    autoprefixer: {},
    cssnano: process.env.NODE_ENV === 'production' ? {} : false,
  },
};
```

### CSS Variables and Theming

```css
/* src/styles/variables.css */
:root {
  /* Colors */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-light: #dbeafe;
  
  --color-secondary: #64748b;
  --color-secondary-hover: #475569;
  
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  
  --color-background: #ffffff;
  --color-surface: #f8fafc;
  --color-border: #e2e8f0;
  
  --color-text-primary: #1e293b;
  --color-text-secondary: #64748b;
  --color-text-muted: #94a3b8;
  
  /* CTI Status Colors */
  --color-call-active: #10b981;
  --color-call-hold: #f59e0b;
  --color-call-ringing: #3b82f6;
  --color-call-ended: #6b7280;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  
  /* Typography */
  --font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-family-mono: 'JetBrains Mono', monospace;
  
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
  
  /* Z-index layers */
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal: 300;
  --z-tooltip: 400;
  --z-toast: 500;
}

/* Dark Theme */
[data-theme='dark'] {
  --color-background: #0f172a;
  --color-surface: #1e293b;
  --color-border: #334155;
  
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;
}
```

### CSS Mixins

```css
/* src/styles/mixins.css */

/* Flexbox utilities */
.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Focus styles */
.focus-ring {
  &:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

/* Truncate text */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Screen reader only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
```

### Component-Specific Styles

```css
/* src/components/shared/Button/Button.module.css */
@import '../../../styles/variables.css';

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  font-family: var(--font-family-base);
  font-weight: var(--font-weight-medium);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

/* Variants */
.primary {
  background-color: var(--color-primary);
  color: white;
  
  &:hover:not(:disabled) {
    background-color: var(--color-primary-hover);
  }
}

.secondary {
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  
  &:hover:not(:disabled) {
    background-color: var(--color-border);
  }
}

.ghost {
  background-color: transparent;
  color: var(--color-text-secondary);
  
  &:hover:not(:disabled) {
    background-color: var(--color-surface);
  }
}

.danger {
  background-color: var(--color-danger);
  color: white;
  
  &:hover:not(:disabled) {
    background-color: color-mod(var(--color-danger) shade(10%));
  }
}

.success {
  background-color: var(--color-success);
  color: white;
  
  &:hover:not(:disabled) {
    background-color: color-mod(var(--color-success) shade(10%));
  }
}

/* Sizes */
.small {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.medium {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
}

.large {
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: var(--font-size-lg);
}

/* Modifiers */
.fullWidth {
  width: 100%;
}

.loading {
  position: relative;
  color: transparent;
  
  .spinner {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
}

.spinner {
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: var(--radius-full);
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.iconLeft {
  margin-right: var(--spacing-xs);
}

.iconRight {
  margin-left: var(--spacing-xs);
}
```

### Responsive Design

```css
/* src/styles/breakpoints.css */
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}

/* src/components/Home/Home.module.css */
.homeContainer {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.mainContent {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.contentArea {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.activitySidebar {
  width: 320px;
  border-left: 1px solid var(--color-border);
  overflow-y: auto;
  
  @media (max-width: 1024px) {
    display: none;
  }
}

/* Mobile-first responsive patterns */
@media (max-width: 768px) {
  .mainContent {
    flex-direction: column;
  }
  
  .contentArea {
    padding: var(--spacing-md);
  }
}
```

## Best Practices

### Component Development Checklist

1. **Accessibility**: Always include proper ARIA attributes, keyboard navigation, and focus management
2. **TypeScript**: Define comprehensive interfaces for all props
3. **Error Handling**: Implement error boundaries and loading states
4. **Performance**: Use `React.memo`, `useMemo`, and `useCallback` appropriately
5. **Testing**: Write unit tests for component logic and integration tests for user flows
6. **Documentation**: Include JSDoc comments and usage examples

### Common Pitfalls to Avoid

- **Over-rendering**: Always check for unnecessary re-renders using React DevTools
- **Prop Drilling**: Use Context API or state management for deeply nested data
- **Missing Keys**: Always provide stable keys for list items
- **Inline Styles**: Prefer CSS Modules over inline styles for better performance
- **Memory Leaks**: Clean up subscriptions and event listeners in useEffect cleanup functions

---

This component guide provides the foundation for building consistent, maintainable, and performant React components within the Freedom Web application. For additional information, refer to the API documentation and CTI integration guides.