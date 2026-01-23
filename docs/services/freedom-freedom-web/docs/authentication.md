# Authentication Guide

## Overview

This document provides comprehensive documentation for the authentication system in Freedom Web, a standalone web application for call center and telephony operations. The authentication system is built on JWT (JSON Web Token) technology, providing secure, stateless authentication that integrates seamlessly with the CTI bridge and other telephony features.

Freedom Web's authentication architecture follows industry best practices for single-page applications (SPAs), implementing token-based authentication with automatic refresh capabilities, secure storage strategies, and a robust state management pattern using React Context and reducers.

## Authentication Overview

### Architecture Overview

The Freedom Web authentication system is designed around several core principles:

1. **Stateless Authentication**: JWT tokens contain all necessary user information, eliminating server-side session storage requirements
2. **Secure Token Storage**: Tokens are stored securely with appropriate safeguards against XSS and CSRF attacks
3. **Automatic Token Refresh**: Seamless token renewal ensures uninterrupted user sessions
4. **Role-Based Access Control**: User permissions are embedded in tokens for efficient authorization checks
5. **CTI Integration**: Authentication state is shared with the CTI bridge for telephony operations

### Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │     │  Frontend   │     │  Auth API   │     │  CTI Bridge │
│   Login     │────▶│  App        │────▶│  Server     │────▶│  Integration│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │                   │
                           │   JWT Token       │                   │
                           │◀──────────────────│                   │
                           │                   │                   │
                           │   Store Token     │                   │
                           │   in Context      │                   │
                           │                   │                   │
                           │   CTI Auth Sync   │                   │
                           │──────────────────────────────────────▶│
```

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `AuthContext` | Global authentication state provider | `src/context/AuthContext.tsx` |
| `AuthReducer` | State management for auth actions | `src/reducers/authReducer.ts` |
| `useAuth` | Custom hook for accessing auth state | `src/hooks/useAuth.ts` |
| `ProtectedRoute` | Route guard component | `src/components/ProtectedRoute.tsx` |
| `TokenService` | JWT handling utilities | `src/services/tokenService.ts` |

## JWT Token Handling

### Token Structure

Freedom Web uses JWT tokens with the following structure:

```javascript
// JWT Token Payload Structure
{
  // Standard Claims
  "sub": "user-uuid-12345",           // Subject (User ID)
  "iat": 1699900000,                   // Issued At timestamp
  "exp": 1699903600,                   // Expiration timestamp
  "iss": "freedom-auth-service",       // Issuer
  
  // Custom Claims
  "email": "agent@company.com",
  "name": "John Agent",
  "role": "call_center_agent",
  "permissions": [
    "calls:view",
    "calls:manage",
    "voicemail:access",
    "addressbook:read",
    "addressbook:write"
  ],
  "teamId": "team-uuid-67890",
  "extensionNumber": "1234",
  "ctiEnabled": true
}
```

### Token Service Implementation

```typescript
// src/services/tokenService.ts

interface TokenPayload {
  sub: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  teamId: string;
  extensionNumber: string;
  ctiEnabled: boolean;
  iat: number;
  exp: number;
}

interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

class TokenService {
  private readonly ACCESS_TOKEN_KEY = 'freedom_access_token';
  private readonly REFRESH_TOKEN_KEY = 'freedom_refresh_token';
  private readonly TOKEN_EXPIRY_BUFFER = 60; // seconds before expiry to trigger refresh

  /**
   * Store tokens securely
   * Access token in memory, refresh token in httpOnly cookie (when available)
   * Falls back to localStorage for development environments
   */
  storeTokens(tokens: TokenPair): void {
    // Store access token in memory for security
    this.accessToken = tokens.accessToken;
    
    // Store refresh token
    // In production, this should be an httpOnly cookie set by the server
    if (process.env.NODE_ENV === 'development') {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refreshToken);
    }
  }

  /**
   * Retrieve the current access token
   */
  getAccessToken(): string | null {
    return this.accessToken || null;
  }

  /**
   * Decode JWT token without verification
   * Note: Verification happens server-side; this is for client-side parsing only
   */
  decodeToken(token: string): TokenPayload | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Failed to decode token:', error);
      return null;
    }
  }

  /**
   * Check if the access token is expired or about to expire
   */
  isTokenExpired(token: string): boolean {
    const payload = this.decodeToken(token);
    if (!payload) return true;
    
    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp - currentTime <= this.TOKEN_EXPIRY_BUFFER;
  }

  /**
   * Clear all stored tokens
   */
  clearTokens(): void {
    this.accessToken = null;
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.clear();
  }

  private accessToken: string | null = null;
}

export const tokenService = new TokenService();
```

### Token Refresh Mechanism

```typescript
// src/services/authService.ts

import { tokenService } from './tokenService';
import { apiClient } from './apiClient';

interface RefreshResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

class AuthService {
  private refreshPromise: Promise<string> | null = null;

  /**
   * Refresh the access token using the refresh token
   * Implements request deduplication to prevent multiple simultaneous refresh calls
   */
  async refreshAccessToken(): Promise<string> {
    // Return existing promise if refresh is already in progress
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    try {
      const response = await apiClient.post<RefreshResponse>('/auth/refresh', {
        // Refresh token sent via httpOnly cookie or retrieved from storage
      });

      tokenService.storeTokens({
        accessToken: response.data.accessToken,
        refreshToken: response.data.refreshToken,
      });

      return response.data.accessToken;
    } catch (error) {
      tokenService.clearTokens();
      throw new Error('Session expired. Please log in again.');
    }
  }

  /**
   * Authenticate user with credentials
   */
  async login(email: string, password: string): Promise<TokenPayload> {
    const response = await apiClient.post('/auth/login', { email, password });
    
    tokenService.storeTokens({
      accessToken: response.data.accessToken,
      refreshToken: response.data.refreshToken,
    });

    return tokenService.decodeToken(response.data.accessToken)!;
  }

  /**
   * Log out user and invalidate tokens
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      tokenService.clearTokens();
    }
  }
}

export const authService = new AuthService();
```

## Token Validation

### Client-Side Validation

While full token verification occurs server-side, the client performs several validation checks:

```typescript
// src/utils/tokenValidation.ts

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  payload?: TokenPayload;
}

/**
 * Validate token structure and claims on the client side
 * This is NOT a security measure - server-side validation is authoritative
 */
export function validateToken(token: string): ValidationResult {
  const errors: string[] = [];

  // Check token structure
  const parts = token.split('.');
  if (parts.length !== 3) {
    return { isValid: false, errors: ['Invalid token structure'] };
  }

  // Decode and validate payload
  const payload = tokenService.decodeToken(token);
  if (!payload) {
    return { isValid: false, errors: ['Unable to decode token'] };
  }

  // Check expiration
  const currentTime = Math.floor(Date.now() / 1000);
  if (payload.exp <= currentTime) {
    errors.push('Token has expired');
  }

  // Check required claims
  const requiredClaims = ['sub', 'email', 'role', 'permissions'];
  for (const claim of requiredClaims) {
    if (!(claim in payload)) {
      errors.push(`Missing required claim: ${claim}`);
    }
  }

  // Validate permissions array
  if (!Array.isArray(payload.permissions)) {
    errors.push('Permissions must be an array');
  }

  return {
    isValid: errors.length === 0,
    errors,
    payload: errors.length === 0 ? payload : undefined,
  };
}

/**
 * Check if user has specific permission
 */
export function hasPermission(payload: TokenPayload, permission: string): boolean {
  return payload.permissions.includes(permission);
}

/**
 * Check if user has any of the specified permissions
 */
export function hasAnyPermission(payload: TokenPayload, permissions: string[]): boolean {
  return permissions.some((p) => payload.permissions.includes(p));
}

/**
 * Check if user has all of the specified permissions
 */
export function hasAllPermissions(payload: TokenPayload, permissions: string[]): boolean {
  return permissions.every((p) => payload.permissions.includes(p));
}
```

### API Request Interceptor

```typescript
// src/services/apiClient.ts

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { tokenService } from './tokenService';
import { authService } from './authService';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: Error) => void;
  }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor - attach access token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = tokenService.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Queue this request while refresh is in progress
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return this.client(originalRequest);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newToken = await authService.refreshAccessToken();
            
            // Process queued requests
            this.failedQueue.forEach(({ resolve }) => resolve(newToken));
            this.failedQueue = [];

            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Reject all queued requests
            this.failedQueue.forEach(({ reject }) => 
              reject(new Error('Session expired'))
            );
            this.failedQueue = [];
            
            // Redirect to login
            window.location.href = '/login';
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Expose axios methods
  get = this.client.get.bind(this.client);
  post = this.client.post.bind(this.client);
  put = this.client.put.bind(this.client);
  patch = this.client.patch.bind(this.client);
  delete = this.client.delete.bind(this.client);
}

export const apiClient = new ApiClient();
```

## Auth Context Usage

### Context Definition

```typescript
// src/context/AuthContext.tsx

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { authReducer, AuthState, AuthAction, initialAuthState } from '../reducers/authReducer';
import { tokenService } from '../services/tokenService';
import { authService } from '../services/authService';

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const [state, dispatch] = useReducer(authReducer, initialAuthState);

  // Initialize auth state from stored token on mount
  useEffect(() => {
    const initializeAuth = async () => {
      dispatch({ type: 'AUTH_LOADING' });
      
      try {
        const token = tokenService.getAccessToken();
        if (token && !tokenService.isTokenExpired(token)) {
          const payload = tokenService.decodeToken(token);
          if (payload) {
            dispatch({ type: 'AUTH_SUCCESS', payload: { user: payload } });
            return;
          }
        }
        
        // Attempt to refresh if we have a refresh token
        const newToken = await authService.refreshAccessToken();
        const payload = tokenService.decodeToken(newToken);
        if (payload) {
          dispatch({ type: 'AUTH_SUCCESS', payload: { user: payload } });
        } else {
          dispatch({ type: 'AUTH_LOGOUT' });
        }
      } catch (error) {
        dispatch({ type: 'AUTH_LOGOUT' });
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    dispatch({ type: 'AUTH_LOADING' });
    
    try {
      const user = await authService.login(email, password);
      dispatch({ type: 'AUTH_SUCCESS', payload: { user } });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'AUTH_ERROR', payload: { error: message } });
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } finally {
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const token = await authService.refreshAccessToken();
      const payload = tokenService.decodeToken(token);
      if (payload) {
        dispatch({ type: 'AUTH_SUCCESS', payload: { user: payload } });
      }
    } catch (error) {
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  const hasPermission = (permission: string): boolean => {
    return state.user?.permissions.includes(permission) ?? false;
  };

  const hasRole = (role: string): boolean => {
    return state.user?.role === role;
  };

  const value: AuthContextValue = {
    ...state,
    login,
    logout,
    refreshUser,
    hasPermission,
    hasRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Custom hook to access authentication context
 * Must be used within an AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Usage Examples

```typescript
// Example: Using auth context in a component

import React from 'react';
import { useAuth } from '../context/AuthContext';

function UserProfile(): JSX.Element {
  const { user, isAuthenticated, isLoading, logout, hasPermission } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="user-profile">
      <h2>Welcome, {user.name}</h2>
      <p>Extension: {user.extensionNumber}</p>
      <p>Role: {user.role}</p>
      
      {hasPermission('calls:manage') && (
        <button onClick={() => navigate('/calls')}>
          Manage Calls
        </button>
      )}
      
      {hasPermission('addressbook:write') && (
        <button onClick={() => navigate('/addressbook/new')}>
          Add Contact
        </button>
      )}
      
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}
```

## Auth Actions & Reducers

### Reducer Implementation

```typescript
// src/reducers/authReducer.ts

export interface AuthUser {
  sub: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  teamId: string;
  extensionNumber: string;
  ctiEnabled: boolean;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastActivity: number | null;
}

export type AuthAction =
  | { type: 'AUTH_LOADING' }
  | { type: 'AUTH_SUCCESS'; payload: { user: AuthUser } }
  | { type: 'AUTH_ERROR'; payload: { error: string } }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'AUTH_UPDATE_USER'; payload: { updates: Partial<AuthUser> } }
  | { type: 'AUTH_UPDATE_ACTIVITY' };

export const initialAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading to check stored tokens
  error: null,
  lastActivity: null,
};

export function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_LOADING':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        lastActivity: Date.now(),
      };

    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload.error,
      };

    case 'AUTH_LOGOUT':
      return {
        ...initialAuthState,
        isLoading: false,
      };

    case 'AUTH_UPDATE_USER':
      if (!state.user) return state;
      return {
        ...state,
        user: {
          ...state.user,
          ...action.payload.updates,
        },
      };

    case 'AUTH_UPDATE_ACTIVITY':
      return {
        ...state,
        lastActivity: Date.now(),
      };

    default:
      return state;
  }
}
```

### Action Creators

```typescript
// src/actions/authActions.ts

import { AuthAction, AuthUser } from '../reducers/authReducer';

export const authActions = {
  loading: (): AuthAction => ({ type: 'AUTH_LOADING' }),
  
  success: (user: AuthUser): AuthAction => ({
    type: 'AUTH_SUCCESS',
    payload: { user },
  }),
  
  error: (error: string): AuthAction => ({
    type: 'AUTH_ERROR',
    payload: { error },
  }),
  
  logout: (): AuthAction => ({ type: 'AUTH_LOGOUT' }),
  
  updateUser: (updates: Partial<AuthUser>): AuthAction => ({
    type: 'AUTH_UPDATE_USER',
    payload: { updates },
  }),
  
  updateActivity: (): AuthAction => ({ type: 'AUTH_UPDATE_ACTIVITY' }),
};
```

## Protected Routes

### Protected Route Component

```typescript
// src/components/ProtectedRoute.tsx

import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredPermissions?: string[];
  requiredRole?: string;
  requireAll?: boolean; // If true, user needs ALL permissions; if false, ANY permission
  fallbackPath?: string;
}

export function ProtectedRoute({
  children,
  requiredPermissions = [],
  requiredRole,
  requireAll = true,
  fallbackPath = '/login',
}: ProtectedRouteProps): JSX.Element {
  const { isAuthenticated, isLoading, user, hasPermission, hasRole } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="auth-loading">
        <LoadingSpinner />
        <p>Verifying authentication...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate 
        to={fallbackPath} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Check role requirement
  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <Navigate 
        to="/unauthorized" 
        state={{ reason: 'Insufficient role' }} 
        replace 
      />
    );
  }

  // Check permission requirements
  if (requiredPermissions.length > 0) {
    const hasRequiredPermissions = requireAll
      ? requiredPermissions.every((p) => hasPermission(p))
      : requiredPermissions.some((p) => hasPermission(p));

    if (!hasRequiredPermissions) {
      return (
        <Navigate 
          to="/unauthorized" 
          state={{ reason: 'Insufficient permissions' }} 
          replace 
        />
      );
    }
  }

  return <>{children}</>;
}
```

### Route Configuration

```typescript
// src/routes/AppRoutes.tsx

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';

// Page imports
import LoginPage from '../pages/LoginPage';
import DashboardPage from '../pages/DashboardPage';
import ActiveCallsPage from '../pages/ActiveCallsPage';
import VoicemailPage from '../pages/VoicemailPage';
import AddressBookPage from '../pages/AddressBookPage';
import TeamPage from '../pages/TeamPage';
import CallLogPage from '../pages/CallLogPage';
import UnauthorizedPage from '../pages/UnauthorizedPage';

export function AppRoutes(): JSX.Element {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

      {/* Protected Routes - Basic Authentication */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes - With Permissions */}
      <Route
        path="/calls"
        element={
          <ProtectedRoute requiredPermissions={['calls:view']}>
            <ActiveCallsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/voicemail"
        element={
          <ProtectedRoute requiredPermissions={['voicemail:access']}>
            <VoicemailPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/addressbook"
        element={
          <ProtectedRoute requiredPermissions={['addressbook:read']}>
            <AddressBookPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes - Role-Based */}
      <Route
        path="/team"
        element={
          <ProtectedRoute 
            requiredRole="team_lead"
            requiredPermissions={['team:manage']}
          >
            <TeamPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes - Multiple Permissions */}
      <Route
        path="/call-log"
        element={
          <ProtectedRoute
            requiredPermissions={['calls:view', 'calls:history']}
            requireAll={true}
          >
            <CallLogPage />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
```

## Session Management

### Session Timeout Handler

```typescript
// src/hooks/useSessionTimeout.ts

import { useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';

interface SessionTimeoutOptions {
  timeoutDuration?: number;      // Milliseconds until timeout (default: 30 minutes)
  warningDuration?: number;      // Milliseconds before timeout to show warning (default: 5 minutes)
  onWarning?: () => void;        // Callback when warning should be shown
  onTimeout?: () => void;        // Callback when session times out
  events?: string[];             // DOM events that reset the timer
}

const DEFAULT_TIMEOUT = 30 * 60 * 1000;    // 30 minutes
const DEFAULT_WARNING = 5 * 60 * 1000;     // 5 minutes
const DEFAULT_EVENTS = [
  'mousedown',
  'mousemove',
  'keypress',
  'scroll',
  'touchstart',
  'click',
];

export function useSessionTimeout(options: SessionTimeoutOptions = {}): void {
  const {
    timeoutDuration = DEFAULT_TIMEOUT,
    warningDuration = DEFAULT_WARNING,
    onWarning,
    onTimeout,
    events = DEFAULT_EVENTS,
  } = options;

  const { isAuthenticated, logout } = useAuth();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const warningRef = useRef<NodeJS.Timeout | null>(null);
  const isWarningShown = useRef(false);

  const clearTimers = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (warningRef.current) {
      clearTimeout(warningRef.current);
      warningRef.current = null;
    }
  }, []);

  const handleTimeout = useCallback(async () => {
    clearTimers();
    if (onTimeout) {
      onTimeout();
    }
    await logout();
  }, [clearTimers, logout, onTimeout]);

  const handleWarning = useCallback(() => {
    if (!isWarningShown.current && onWarning) {
      isWarningShown.current = true;
      onWarning();
    }
  }, [onWarning]);

  const resetTimers = useCallback(() => {
    clearTimers();
    isWarningShown.current = false;

    if (!isAuthenticated) return;

    // Set warning timer
    warningRef.current = setTimeout(handleWarning, timeoutDuration - warningDuration);

    // Set timeout timer
    timeoutRef.current = setTimeout(handleTimeout, timeoutDuration);
  }, [
    clearTimers,
    isAuthenticated,
    timeoutDuration,
    warningDuration,
    handleWarning,
    handleTimeout,
  ]);

  // Set up event listeners
  useEffect(() => {
    if (!isAuthenticated) {
      clearTimers();
      return;
    }

    // Initial timer setup
    resetTimers();

    // Add event listeners
    const handleActivity = () => resetTimers();
    events.forEach((event) => {
      document.addEventListener(event, handleActivity);
    });

    return () => {
      clearTimers();
      events.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
    };
  }, [isAuthenticated, events, resetTimers, clearTimers]);
}
```

### Session Timeout Component

```typescript
// src/components/SessionTimeoutModal.tsx

import React, { useState, useEffect } from 'react';
import { useSessionTimeout } from '../hooks/useSessionTimeout';
import { useAuth } from '../context/AuthContext';

export function SessionTimeoutManager(): JSX.Element | null {
  const [showWarning, setShowWarning] = useState(false);
  const [countdown, setCountdown] = useState(300); // 5 minutes in seconds
  const { isAuthenticated, refreshUser } = useAuth();

  useSessionTimeout({
    timeoutDuration: 30 * 60 * 1000, // 30 minutes
    warningDuration: 5 * 60 * 1000,  // 5 minutes warning
    onWarning: () => {
      setShowWarning(true);
      setCountdown(300);
    },
    onTimeout: () => {
      setShowWarning(false);
    },
  });

  // Countdown timer
  useEffect(() => {
    if (!showWarning) return;

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [showWarning]);

  const handleExtendSession = async () => {
    try {
      await refreshUser();
      setShowWarning(false);
    } catch (error) {
      console.error('Failed to extend session:', error);
    }
  };

  if (!isAuthenticated || !showWarning) {
    return null;
  }

  const minutes = Math.floor(countdown / 60);
  const seconds = countdown % 60;

  return (
    <div className="session-timeout-overlay">
      <div className="session-timeout-modal">
        <h2>Session Expiring</h2>
        <p>
          Your session will expire in{' '}
          <strong>
            {minutes}:{seconds.toString().padStart(2, '0')}
          </strong>
        </p>
        <p>Would you like to extend your session?</p>
        <div className="modal-actions">
          <button onClick={handleExtendSession} className="btn-primary">
            Extend Session
          </button>
          <button onClick={() => setShowWarning(false)} className="btn-secondary">
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
```

### CTI Bridge Authentication Sync

```typescript
// src/services/ctiBridgeAuth.ts

import { tokenService } from './tokenService';
import { EventEmitter } from 'events';

interface CTIAuthState {
  isAuthenticated: boolean;
  extensionNumber: string | null;
  agentId: string | null;
}

class CTIBridgeAuth extends EventEmitter {
  private authState: CTIAuthState = {
    isAuthenticated: false,
    extensionNumber: null,
    agentId: null,
  };

  /**
   * Synchronize authentication state with CTI bridge
   */
  async syncAuth(): Promise<void> {
    const token = tokenService.getAccessToken();
    if (!token) {
      await this.disconnect();
      return;
    }

    const payload = tokenService.decodeToken(token);
    if (!payload || !payload.ctiEnabled) {
      await this.disconnect();
      return;
    }

    try {
      // Send authentication to CTI bridge
      await this.sendToCTIBridge({
        type: 'AUTH_SYNC',
        payload: {
          token,
          extensionNumber: payload.extensionNumber,
          agentId: payload.sub,
        },
      });

      this.authState = {
        isAuthenticated: true,
        extensionNumber: payload.extensionNumber,
        agentId: payload.sub,
      };

      this.emit('auth:connected', this.authState);
    } catch (error) {
      console.error('CTI Bridge auth sync failed:', error);
      this.emit('auth:error', error);
    }
  }

  /**
   * Disconnect from CTI bridge
   */
  async disconnect(): Promise<void> {
    try {
      await this.sendToCTIBridge({ type: 'AUTH_DISCONNECT' });
    } finally {
      this.authState = {
        isAuthenticated: false,
        extensionNumber: null,
        agentId: null,
      };
      this.emit('auth:disconnected');
    }
  }

  /**
   * Get current CTI auth state
   */
  getAuthState(): CTIAuthState {
    return { ...this.authState };
  }

  private async sendToCTIBridge(message: object): Promise<void> {
    // Implementation depends on CTI bridge communication method
    // (WebSocket, postMessage, etc.)
    if (window.ctiBridge) {
      await window.ctiBridge.send(message);
    }
  }
}

export const ctiBridgeAuth = new CTIBridgeAuth();
```

## Best Practices

### Security Recommendations

1. **Never store sensitive tokens in localStorage** in production - use httpOnly cookies for refresh tokens
2. **Always validate tokens server-side** - client-side validation is for UX only
3. **Implement token refresh** before expiration to prevent session interruption
4. **Use short-lived access tokens** (15-30 minutes) with longer-lived refresh tokens
5. **Clear all tokens on logout** including any cached data

### Error Handling

```typescript
// Example: Comprehensive auth error handling

try {
  await login(email, password);
} catch (error) {
  if (error instanceof AuthenticationError) {
    switch (error.code) {
      case 'INVALID_CREDENTIALS':
        showError('Invalid email or password');
        break;
      case 'ACCOUNT_LOCKED':
        showError('Account locked. Please contact support.');
        break;
      case 'MFA_REQUIRED':
        navigate('/mfa-verification');
        break;
      default:
        showError('Authentication failed. Please try again.');
    }
  } else if (error instanceof NetworkError) {
    showError('Network error. Please check your connection.');
  } else {
    showError('An unexpected error occurred.');
    console.error('Login error:', error);
  }
}
```

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Token not persisting after refresh | Race condition in token storage | Implement request queuing during refresh |
| Infinite redirect loop | Missing loading state check | Ensure `isLoading` is checked before redirecting |
| CTI bridge auth out of sync | Token refreshed without CTI sync | Call `ctiBridgeAuth.syncAuth()` after token refresh |
| Session timing out too quickly | Activity events not resetting timer | Verify event listeners are attached correctly |

---

For additional support or questions about the authentication system, please contact the Freedom Web development team or refer to the API documentation.