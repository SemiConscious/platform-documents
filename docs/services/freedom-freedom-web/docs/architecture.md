# Application Architecture

## Overview

This document provides comprehensive technical architecture documentation for the Freedom Web application, a sophisticated standalone web application designed for call center and telephony operations. Freedom Web leverages modern frontend technologies to deliver a robust, scalable, and maintainable solution for managing active calls, voicemails, address books, team collaboration, and call logging with CTI (Computer Telephony Integration) bridge capabilities.

The architecture follows industry best practices for React/Redux applications, emphasizing component reusability, predictable state management, and clean separation of concerns. This documentation is intended for developers who need to understand, maintain, or extend the Freedom Web application.

---

## Technology Stack

### Core Technologies

Freedom Web is built on a modern JavaScript/TypeScript technology stack that prioritizes developer productivity, application performance, and long-term maintainability.

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI component library and rendering engine |
| Redux Toolkit | 1.9.x | Centralized state management |
| TypeScript | 5.x | Type-safe JavaScript development |
| React Router | 6.x | Client-side routing and navigation |
| Axios | 1.x | HTTP client for API communication |
| WebSocket | Native | Real-time CTI bridge communication |
| Tailwind CSS | 3.x | Utility-first CSS framework |
| Vite | 4.x | Build tool and development server |

### Supporting Libraries

```json
{
  "dependencies": {
    "@reduxjs/toolkit": "^1.9.5",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-redux": "^8.1.1",
    "react-router-dom": "^6.14.0",
    "axios": "^1.4.0",
    "date-fns": "^2.30.0",
    "react-hook-form": "^7.45.0",
    "zod": "^3.21.4",
    "socket.io-client": "^4.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.1.0",
    "vite": "^4.4.0",
    "vitest": "^0.33.0",
    "@testing-library/react": "^14.0.0"
  }
}
```

### Authentication Stack

Freedom Web implements JWT-based authentication with the following components:

- **Access Tokens**: Short-lived tokens (15 minutes) for API authorization
- **Refresh Tokens**: Long-lived tokens (7 days) for session persistence
- **Token Storage**: Secure browser storage with automatic refresh handling

---

## Project Structure

The Freedom Web application follows a feature-based organization pattern, grouping related components, hooks, and services together for improved discoverability and maintainability.

```
freedom-freedom-web/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       └── images/
├── src/
│   ├── app/
│   │   ├── store.ts              # Redux store configuration
│   │   ├── hooks.ts              # Typed Redux hooks
│   │   └── rootReducer.ts        # Combined reducers
│   ├── components/
│   │   ├── common/               # Shared/reusable components
│   │   │   ├── Button/
│   │   │   ├── Modal/
│   │   │   ├── Table/
│   │   │   └── Form/
│   │   ├── layout/               # Layout components
│   │   │   ├── Header/
│   │   │   ├── Sidebar/
│   │   │   └── MainLayout/
│   │   └── ui/                   # UI primitives
│   │       ├── Input/
│   │       ├── Select/
│   │       └── Card/
│   ├── features/
│   │   ├── auth/                 # Authentication feature
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── authSlice.ts
│   │   │   └── index.ts
│   │   ├── activeCalls/          # Active calls management
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── activeCallsSlice.ts
│   │   │   └── index.ts
│   │   ├── voicemail/            # Voicemail handling
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── voicemailSlice.ts
│   │   │   └── index.ts
│   │   ├── addressBook/          # Address book management
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── addressBookSlice.ts
│   │   │   └── index.ts
│   │   ├── team/                 # Team collaboration
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── teamSlice.ts
│   │   │   └── index.ts
│   │   ├── callLog/              # Call logging and wrap-ups
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── callLogSlice.ts
│   │   │   └── index.ts
│   │   └── cti/                  # CTI bridge integration
│   │       ├── components/
│   │       ├── hooks/
│   │       ├── services/
│   │       ├── ctiSlice.ts
│   │       └── index.ts
│   ├── hooks/                    # Global custom hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   └── useNotification.ts
│   ├── services/                 # Global services
│   │   ├── api/
│   │   │   ├── client.ts         # Axios instance configuration
│   │   │   ├── interceptors.ts   # Request/response interceptors
│   │   │   └── endpoints.ts      # API endpoint constants
│   │   └── websocket/
│   │       ├── ctiSocket.ts      # CTI WebSocket handler
│   │       └── eventHandlers.ts
│   ├── utils/                    # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── types/                    # TypeScript type definitions
│   │   ├── api.types.ts
│   │   ├── call.types.ts
│   │   └── user.types.ts
│   ├── styles/                   # Global styles
│   │   └── globals.css
│   ├── App.tsx                   # Root application component
│   ├── main.tsx                  # Application entry point
│   └── vite-env.d.ts
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .eslintrc.js
├── .prettierrc
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### Directory Purpose Summary

| Directory | Purpose |
|-----------|---------|
| `src/app/` | Redux store configuration and typed hooks |
| `src/components/` | Shared, reusable UI components |
| `src/features/` | Feature modules with isolated state and logic |
| `src/hooks/` | Global custom React hooks |
| `src/services/` | API clients and external service integrations |
| `src/utils/` | Pure utility functions and constants |
| `src/types/` | Centralized TypeScript type definitions |

---

## Component Architecture

### Component Hierarchy

Freedom Web follows a hierarchical component structure that promotes reusability and maintainability:

```
App
├── AuthProvider
│   └── Router
│       ├── PublicRoutes
│       │   └── LoginPage
│       └── ProtectedRoutes
│           └── MainLayout
│               ├── Header
│               │   ├── UserMenu
│               │   ├── NotificationBell
│               │   └── CTIStatus
│               ├── Sidebar
│               │   └── NavigationMenu
│               └── MainContent
│                   ├── ActiveCallsPage
│                   │   ├── CallList
│                   │   ├── CallDetails
│                   │   └── CallControls
│                   ├── VoicemailPage
│                   │   ├── VoicemailList
│                   │   ├── VoicemailPlayer
│                   │   └── VoicemailDropPanel
│                   ├── AddressBookPage
│                   │   ├── ContactList
│                   │   ├── ContactForm
│                   │   └── ContactDetails
│                   ├── TeamPage
│                   │   ├── TeamMembers
│                   │   └── PresenceIndicator
│                   └── CallLogPage
│                       ├── CallHistory
│                       └── WrapUpForm
```

### Component Types and Patterns

#### 1. Container Components (Smart Components)

Container components handle data fetching, state management, and business logic:

```typescript
// src/features/activeCalls/components/ActiveCallsContainer.tsx
import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../../app/hooks';
import { fetchActiveCalls, selectActiveCalls, selectCallsLoading } from '../activeCallsSlice';
import { ActiveCallsList } from './ActiveCallsList';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';

export const ActiveCallsContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const calls = useAppSelector(selectActiveCalls);
  const isLoading = useAppSelector(selectCallsLoading);

  useEffect(() => {
    dispatch(fetchActiveCalls());
  }, [dispatch]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <ActiveCallsList 
      calls={calls}
      onCallSelect={handleCallSelect}
      onCallAction={handleCallAction}
    />
  );
};
```

#### 2. Presentational Components (Dumb Components)

Presentational components focus purely on rendering UI based on props:

```typescript
// src/features/activeCalls/components/CallCard.tsx
import React from 'react';
import { Call } from '../../../types/call.types';
import { formatDuration, formatPhoneNumber } from '../../../utils/formatters';

interface CallCardProps {
  call: Call;
  onHold: () => void;
  onTransfer: () => void;
  onEnd: () => void;
}

export const CallCard: React.FC<CallCardProps> = ({
  call,
  onHold,
  onTransfer,
  onEnd
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-blue-500">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold">{call.callerName || 'Unknown'}</h3>
          <p className="text-gray-600">{formatPhoneNumber(call.phoneNumber)}</p>
          <span className="text-sm text-gray-500">
            Duration: {formatDuration(call.duration)}
          </span>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={onHold}
            className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
          >
            Hold
          </button>
          <button 
            onClick={onTransfer}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Transfer
          </button>
          <button 
            onClick={onEnd}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
          >
            End
          </button>
        </div>
      </div>
    </div>
  );
};
```

#### 3. Higher-Order Components (HOCs)

HOCs are used for cross-cutting concerns like authentication:

```typescript
// src/components/common/withAuth.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }

    return <WrappedComponent {...props} />;
  };
}
```

#### 4. Custom Hooks

Custom hooks encapsulate reusable stateful logic:

```typescript
// src/features/activeCalls/hooks/useCallControls.ts
import { useCallback } from 'react';
import { useAppDispatch } from '../../../app/hooks';
import { holdCall, transferCall, endCall } from '../activeCallsSlice';

export const useCallControls = (callId: string) => {
  const dispatch = useAppDispatch();

  const handleHold = useCallback(() => {
    dispatch(holdCall(callId));
  }, [dispatch, callId]);

  const handleTransfer = useCallback((targetExtension: string) => {
    dispatch(transferCall({ callId, targetExtension }));
  }, [dispatch, callId]);

  const handleEnd = useCallback(() => {
    dispatch(endCall(callId));
  }, [dispatch, callId]);

  return {
    handleHold,
    handleTransfer,
    handleEnd
  };
};
```

---

## State Management Overview

### Redux Architecture

Freedom Web uses Redux Toolkit for state management, following the "ducks" pattern with feature-based slices.

#### Store Configuration

```typescript
// src/app/store.ts
import { configureStore } from '@reduxjs/toolkit';
import { rootReducer } from './rootReducer';
import { apiMiddleware } from '../services/api/middleware';
import { ctiMiddleware } from '../features/cti/ctiMiddleware';

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['cti/connectionEstablished'],
        ignoredPaths: ['cti.socket']
      }
    }).concat(apiMiddleware, ctiMiddleware),
  devTools: process.env.NODE_ENV !== 'production'
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

#### Root Reducer

```typescript
// src/app/rootReducer.ts
import { combineReducers } from '@reduxjs/toolkit';
import authReducer from '../features/auth/authSlice';
import activeCallsReducer from '../features/activeCalls/activeCallsSlice';
import voicemailReducer from '../features/voicemail/voicemailSlice';
import addressBookReducer from '../features/addressBook/addressBookSlice';
import teamReducer from '../features/team/teamSlice';
import callLogReducer from '../features/callLog/callLogSlice';
import ctiReducer from '../features/cti/ctiSlice';

export const rootReducer = combineReducers({
  auth: authReducer,
  activeCalls: activeCallsReducer,
  voicemail: voicemailReducer,
  addressBook: addressBookReducer,
  team: teamReducer,
  callLog: callLogReducer,
  cti: ctiReducer
});
```

### State Shape

```typescript
interface RootState {
  auth: {
    user: User | null;
    token: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
  };
  activeCalls: {
    calls: Call[];
    selectedCallId: string | null;
    loading: boolean;
    error: string | null;
  };
  voicemail: {
    messages: VoicemailMessage[];
    dropTemplates: VoicemailDrop[];
    loading: boolean;
    error: string | null;
  };
  addressBook: {
    contacts: Contact[];
    selectedContactId: string | null;
    searchQuery: string;
    loading: boolean;
    error: string | null;
  };
  team: {
    members: TeamMember[];
    presence: Record<string, PresenceStatus>;
    loading: boolean;
    error: string | null;
  };
  callLog: {
    entries: CallLogEntry[];
    filters: CallLogFilters;
    pagination: PaginationState;
    loading: boolean;
    error: string | null;
  };
  cti: {
    connected: boolean;
    agentStatus: AgentStatus;
    events: CTIEvent[];
    error: string | null;
  };
}
```

### Feature Slice Example

```typescript
// src/features/activeCalls/activeCallsSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { callsService } from './services/callsService';
import { Call, CallAction } from '../../types/call.types';

interface ActiveCallsState {
  calls: Call[];
  selectedCallId: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: ActiveCallsState = {
  calls: [],
  selectedCallId: null,
  loading: false,
  error: null
};

// Async thunks
export const fetchActiveCalls = createAsyncThunk(
  'activeCalls/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await callsService.getActiveCalls();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const holdCall = createAsyncThunk(
  'activeCalls/hold',
  async (callId: string, { rejectWithValue }) => {
    try {
      const response = await callsService.holdCall(callId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const transferCall = createAsyncThunk(
  'activeCalls/transfer',
  async ({ callId, targetExtension }: { callId: string; targetExtension: string }, { rejectWithValue }) => {
    try {
      const response = await callsService.transferCall(callId, targetExtension);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Slice
const activeCallsSlice = createSlice({
  name: 'activeCalls',
  initialState,
  reducers: {
    selectCall: (state, action: PayloadAction<string>) => {
      state.selectedCallId = action.payload;
    },
    callReceived: (state, action: PayloadAction<Call>) => {
      state.calls.push(action.payload);
    },
    callUpdated: (state, action: PayloadAction<Call>) => {
      const index = state.calls.findIndex(c => c.id === action.payload.id);
      if (index !== -1) {
        state.calls[index] = action.payload;
      }
    },
    callEnded: (state, action: PayloadAction<string>) => {
      state.calls = state.calls.filter(c => c.id !== action.payload);
      if (state.selectedCallId === action.payload) {
        state.selectedCallId = null;
      }
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchActiveCalls.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchActiveCalls.fulfilled, (state, action) => {
        state.loading = false;
        state.calls = action.payload;
      })
      .addCase(fetchActiveCalls.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

// Selectors
export const selectActiveCalls = (state: RootState) => state.activeCalls.calls;
export const selectCallsLoading = (state: RootState) => state.activeCalls.loading;
export const selectSelectedCall = (state: RootState) => 
  state.activeCalls.calls.find(c => c.id === state.activeCalls.selectedCallId);

export const { selectCall, callReceived, callUpdated, callEnded, clearError } = activeCallsSlice.actions;
export default activeCallsSlice.reducer;
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    React Components                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ Call List  │  │ Call Card  │  │  Control Buttons   │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Custom Hooks Layer                         │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐    │
│  │ useCallList  │  │ useCallCtrl   │  │   useWebSocket    │    │
│  └──────────────┘  └───────────────┘  └───────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Redux Store                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Action Dispatch                        │  │
│  │  fetchCalls() ─────────────────────────▶ Thunk Middleware │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                       Reducers                            │  │
│  │  activeCallsSlice ◀────── Action ────▶ State Update       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      Selectors                            │  │
│  │  selectActiveCalls ─────────────────────▶ Derived State   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐    │
│  │ API Client   │  │ WebSocket     │  │   CTI Bridge      │    │
│  │ (Axios)      │  │ Handler       │  │   Handler         │    │
│  └──────────────┘  └───────────────┘  └───────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐    │
│  │  REST API    │  │  WebSocket    │  │   CTI Server      │    │
│  │  Server      │  │  Server       │  │                   │    │
│  └──────────────┘  └───────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Layer

### API Client Configuration

```typescript
// src/services/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { store } from '../../app/store';
import { refreshToken, logout } from '../../features/auth/authSlice';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const state = store.getState();
    const token = state.auth.token;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        await store.dispatch(refreshToken());
        const state = store.getState();
        originalRequest.headers.Authorization = `Bearer ${state.auth.token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        store.dispatch(logout());
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

### Feature Services

```typescript
// src/features/activeCalls/services/callsService.ts
import { apiClient } from '../../../services/api/client';
import { Call, CallTransferRequest, CallWrapUpRequest } from '../../../types/call.types';

export const callsService = {
  getActiveCalls: () => 
    apiClient.get<Call[]>('/api/v1/calls/active'),
  
  getCallDetails: (callId: string) => 
    apiClient.get<Call>(`/api/v1/calls/${callId}`),
  
  holdCall: (callId: string) => 
    apiClient.post<Call>(`/api/v1/calls/${callId}/hold`),
  
  resumeCall: (callId: string) => 
    apiClient.post<Call>(`/api/v1/calls/${callId}/resume`),
  
  transferCall: (callId: string, target: string) => 
    apiClient.post<Call>(`/api/v1/calls/${callId}/transfer`, { target }),
  
  endCall: (callId: string) => 
    apiClient.post<void>(`/api/v1/calls/${callId}/end`),
  
  wrapUpCall: (callId: string, data: CallWrapUpRequest) => 
    apiClient.post<void>(`/api/v1/calls/${callId}/wrapup`, data)
};
```

### CTI WebSocket Service

```typescript
// src/services/websocket/ctiSocket.ts
import { io, Socket } from 'socket.io-client';
import { store } from '../../app/store';
import { 
  connectionEstablished, 
  connectionLost, 
  agentStatusChanged 
} from '../../features/cti/ctiSlice';
import { 
  callReceived, 
  callUpdated, 
  callEnded 
} from '../../features/activeCalls/activeCallsSlice';

class CTISocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token: string): void {
    const CTI_SOCKET_URL = import.meta.env.VITE_CTI_SOCKET_URL;
    
    this.socket = io(CTI_SOCKET_URL, {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('CTI Socket connected');
      this.reconnectAttempts = 0;
      store.dispatch(connectionEstablished());
    });

    this.socket.on('disconnect', (reason) => {
      console.log('CTI Socket disconnected:', reason);
      store.dispatch(connectionLost());
    });

    this.socket.on('call:incoming', (call) => {
      store.dispatch(callReceived(call));
    });

    this.socket.on('call:updated', (call) => {
      store.dispatch(callUpdated(call));
    });

    this.socket.on('call:ended', (callId) => {
      store.dispatch(callEnded(callId));
    });

    this.socket.on('agent:status', (status) => {
      store.dispatch(agentStatusChanged(status));
    });

    this.socket.on('error', (error) => {
      console.error('CTI Socket error:', error);
    });
  }

  setAgentStatus(status: string): void {
    this.socket?.emit('agent:setStatus', { status });
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }
}

export const ctiSocketService = new CTISocketService();
```

---

## Build Configuration

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@features': path.resolve(__dirname, './src/features'),
        '@hooks': path.resolve(__dirname, './src/hooks'),
        '@services': path.resolve(__dirname, './src/services'),
        '@utils': path.resolve(__dirname, './src/utils'),
        '@types': path.resolve(__dirname, './src/types')
      }
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
          secure: false
        },
        '/socket.io': {
          target: env.VITE_CTI_SOCKET_URL,
          ws: true,
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            redux: ['@reduxjs/toolkit', 'react-redux'],
            ui: ['tailwindcss']
          }
        }
      }
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './tests/setup.ts',
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html']
      }
    }
  };
});
```

### Environment Configuration

```bash
# .env.example
VITE_API_BASE_URL=http://localhost:8080
VITE_CTI_SOCKET_URL=ws://localhost:8081
VITE_APP_TITLE=Freedom Web
VITE_AUTH_STORAGE_KEY=freedom_auth
VITE_ENABLE_DEBUG=false
```

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@features/*": ["src/features/*"],
      "@hooks/*": ["src/hooks/*"],
      "@services/*": ["src/services/*"],
      "@utils/*": ["src/utils/*"],
      "@types/*": ["src/types/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### NPM Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint src --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,json}\"",
    "type-check": "tsc --noEmit",
    "prepare": "husky install"
  }
}
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [API Reference](./api-reference.md) | Complete API endpoint documentation |
| [Component Library](./component-library.md) | Detailed component documentation and usage examples |
| [State Management Guide](./state-management.md) | In-depth Redux patterns and best practices |
| [CTI Integration Guide](./cti-integration.md) | CTI bridge setup and event handling |
| [Authentication Flow](./authentication.md) | JWT authentication implementation details |
| [Testing Guide](./testing.md) | Unit, integration, and E2E testing strategies |
| [Deployment Guide](./deployment.md) | Build and deployment procedures |
| [Contributing Guidelines](./CONTRIBUTING.md) | Code standards and contribution workflow |

---

## Best Practices and Guidelines

### Code Organization

1. **Feature Isolation**: Keep feature-specific code within feature directories
2. **Shared Components**: Extract reusable components to `src/components`
3. **Type Safety**: Use TypeScript interfaces for all data structures
4. **Consistent Naming**: Follow naming conventions (PascalCase for components, camelCase for functions)

### Performance Optimization

1. **Memoization**: Use `React.memo`, `useMemo`, and `useCallback` appropriately
2. **Code Splitting**: Implement lazy loading for route-based code splitting
3. **Selector Optimization**: Use Reselect for derived state calculations
4. **Bundle Analysis**: Regularly analyze bundle size with `vite-bundle-visualizer`

### Testing Strategy

1. **Unit Tests**: Test individual components and functions in isolation
2. **Integration Tests**: Test feature workflows and Redux integration
3. **E2E Tests**: Test critical user journeys with Playwright or Cypress
4. **Minimum Coverage**: Maintain 80% code coverage for critical paths

---

*Last Updated: 2024*
*Version: 1.0.0*