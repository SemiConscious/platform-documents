# Services & Integrations

## Overview

Freedom Web's service layer provides a robust architecture for handling HTTP communications, telephony integrations, and real-time data synchronization. This documentation covers the core service infrastructure, including the Axios HTTP client configuration, API client patterns, and the CTI (Computer Telephony Integration) bridge that enables seamless telephony operations within the web application.

The service layer is designed with the following principles:
- **Modularity**: Each service handles a specific domain (calls, voicemail, contacts, etc.)
- **Consistency**: Unified error handling and response patterns across all services
- **Reliability**: Automatic retry mechanisms and graceful degradation
- **Security**: JWT-based authentication with automatic token refresh

---

## Services Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Freedom Web Frontend                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Call Service │  │Voicemail Svc │  │Contact Svc   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│                    ┌──────▼───────┐                             │
│                    │ Axios Client │                             │
│                    │  (HTTP Layer)│                             │
│                    └──────┬───────┘                             │
│                           │                                     │
│  ┌────────────────────────┼────────────────────────┐           │
│  │                 CTI Bridge                       │           │
│  │  ┌─────────────┐  ┌─────────────┐              │           │
│  │  │ WebSocket   │  │ Event       │              │           │
│  │  │ Handler     │  │ Dispatcher  │              │           │
│  │  └─────────────┘  └─────────────┘              │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  REST API    │  │  Telephony   │  │  Database    │          │
│  │  Gateway     │  │  Server      │  │  Services    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Core Services

| Service | Purpose | Primary Endpoints |
|---------|---------|-------------------|
| `callService` | Active call management | `/calls`, `/wrap-ups` |
| `voicemailService` | Voicemail operations | `/voicemail` |
| `contactService` | Address book management | `/addressbook`, `/contacts` |
| `teamService` | Team collaboration | `/teams` |
| `activityService` | Activity tracking | `/activities` |
| `authService` | Authentication & tokens | `/auth` |

---

## Axios Configuration

### Base Configuration

The Axios client is configured with sensible defaults that ensure consistent behavior across all API calls.

```typescript
// src/services/api/axiosConfig.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

interface ApiConfig {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
}

const defaultConfig: ApiConfig = {
  baseURL: process.env.REACT_APP_API_BASE_URL || 'https://api.freedom.com/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Version': process.env.REACT_APP_VERSION || '1.0.0',
  },
};

export const createApiClient = (config: Partial<ApiConfig> = {}): AxiosInstance => {
  const instance = axios.create({
    ...defaultConfig,
    ...config,
  });

  // Request interceptor for authentication
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      // Add request timestamp for debugging
      config.metadata = { startTime: new Date() };
      
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  instance.interceptors.response.use(
    (response) => {
      // Log response time in development
      if (process.env.NODE_ENV === 'development') {
        const duration = new Date().getTime() - response.config.metadata?.startTime?.getTime();
        console.debug(`[API] ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`);
      }
      return response;
    },
    async (error: AxiosError) => {
      return handleApiError(error);
    }
  );

  return instance;
};

export const apiClient = createApiClient();
```

### Token Refresh Mechanism

```typescript
// src/services/api/tokenRefresh.ts
import { apiClient } from './axiosConfig';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token!);
    }
  });
  failedQueue = [];
};

export const refreshToken = async (): Promise<string> => {
  const refresh_token = localStorage.getItem('refresh_token');
  
  if (!refresh_token) {
    throw new Error('No refresh token available');
  }

  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token,
  });

  const { access_token, refresh_token: new_refresh_token } = response.data;
  
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', new_refresh_token);
  
  return access_token;
};

export const handleTokenExpiration = async (originalRequest: any): Promise<any> => {
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    }).then((token) => {
      originalRequest.headers.Authorization = `Bearer ${token}`;
      return apiClient(originalRequest);
    });
  }

  isRefreshing = true;

  try {
    const newToken = await refreshToken();
    processQueue(null, newToken);
    originalRequest.headers.Authorization = `Bearer ${newToken}`;
    return apiClient(originalRequest);
  } catch (error) {
    processQueue(error as Error, null);
    // Redirect to login on refresh failure
    window.location.href = '/login';
    throw error;
  } finally {
    isRefreshing = false;
  }
};
```

### Request/Response Interceptors

```typescript
// src/services/api/interceptors.ts
import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { handleTokenExpiration } from './tokenRefresh';

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export const requestInterceptor = (config: InternalAxiosRequestConfig) => {
  // Add correlation ID for request tracing
  config.headers['X-Correlation-ID'] = generateCorrelationId();
  
  // Add timezone for proper datetime handling
  config.headers['X-Timezone'] = Intl.DateTimeFormat().resolvedOptions().timeZone;
  
  return config;
};

export const responseInterceptor = (response: AxiosResponse) => {
  // Transform response data if needed
  if (response.data && response.data.data) {
    // Unwrap nested data structure
    return {
      ...response,
      data: response.data.data,
      meta: response.data.meta,
    };
  }
  return response;
};

export const errorInterceptor = async (error: AxiosError<ApiError>) => {
  const originalRequest = error.config;

  // Handle 401 - Unauthorized
  if (error.response?.status === 401 && originalRequest) {
    return handleTokenExpiration(originalRequest);
  }

  // Handle 429 - Rate Limiting
  if (error.response?.status === 429) {
    const retryAfter = error.response.headers['retry-after'] || 60;
    console.warn(`Rate limited. Retry after ${retryAfter} seconds`);
    
    // Optionally implement automatic retry
    await sleep(parseInt(retryAfter) * 1000);
    return apiClient(originalRequest!);
  }

  // Transform error for consistent handling
  const apiError: ApiError = {
    code: error.response?.data?.code || 'UNKNOWN_ERROR',
    message: error.response?.data?.message || error.message,
    details: error.response?.data?.details,
    timestamp: new Date().toISOString(),
  };

  return Promise.reject(apiError);
};

const generateCorrelationId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
```

---

## API Client Usage

### Creating Domain-Specific Services

```typescript
// src/services/callService.ts
import { apiClient } from './api/axiosConfig';

export interface Call {
  id: string;
  phoneNumber: string;
  direction: 'inbound' | 'outbound';
  status: 'ringing' | 'active' | 'on-hold' | 'completed';
  startTime: string;
  duration?: number;
  agentId: string;
  queueId?: string;
  metadata?: Record<string, any>;
}

export interface CreateCallRequest {
  phoneNumber: string;
  queueId?: string;
  metadata?: Record<string, any>;
}

export interface WrapUpRequest {
  callId: string;
  dispositionCode: string;
  notes?: string;
  followUpRequired?: boolean;
  followUpDate?: string;
}

class CallService {
  private readonly basePath = '/calls';

  async getActiveCalls(): Promise<Call[]> {
    const response = await apiClient.get<Call[]>(`${this.basePath}/active`);
    return response.data;
  }

  async getCallById(callId: string): Promise<Call> {
    const response = await apiClient.get<Call>(`${this.basePath}/${callId}`);
    return response.data;
  }

  async initiateCall(request: CreateCallRequest): Promise<Call> {
    const response = await apiClient.post<Call>(this.basePath, request);
    return response.data;
  }

  async holdCall(callId: string): Promise<Call> {
    const response = await apiClient.post<Call>(`${this.basePath}/${callId}/hold`);
    return response.data;
  }

  async resumeCall(callId: string): Promise<Call> {
    const response = await apiClient.post<Call>(`${this.basePath}/${callId}/resume`);
    return response.data;
  }

  async transferCall(callId: string, targetNumber: string): Promise<Call> {
    const response = await apiClient.post<Call>(`${this.basePath}/${callId}/transfer`, {
      targetNumber,
    });
    return response.data;
  }

  async endCall(callId: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${callId}`);
  }

  async submitWrapUp(request: WrapUpRequest): Promise<void> {
    await apiClient.post(`${this.basePath}/${request.callId}/wrap-up`, request);
  }

  async getCallHistory(params: {
    startDate?: string;
    endDate?: string;
    direction?: 'inbound' | 'outbound';
    page?: number;
    limit?: number;
  }): Promise<{ calls: Call[]; total: number; page: number }> {
    const response = await apiClient.get(`${this.basePath}/history`, { params });
    return response.data;
  }
}

export const callService = new CallService();
```

### Voicemail Service Implementation

```typescript
// src/services/voicemailService.ts
import { apiClient } from './api/axiosConfig';

export interface Voicemail {
  id: string;
  callerId: string;
  callerName?: string;
  duration: number;
  timestamp: string;
  transcription?: string;
  isNew: boolean;
  audioUrl: string;
  queueId?: string;
}

export interface VoicemailDrop {
  id: string;
  name: string;
  description?: string;
  audioUrl: string;
  duration: number;
  createdAt: string;
}

class VoicemailService {
  private readonly basePath = '/voicemail';

  async getVoicemails(params?: {
    isNew?: boolean;
    queueId?: string;
    page?: number;
    limit?: number;
  }): Promise<{ voicemails: Voicemail[]; total: number }> {
    const response = await apiClient.get(this.basePath, { params });
    return response.data;
  }

  async getVoicemailById(id: string): Promise<Voicemail> {
    const response = await apiClient.get<Voicemail>(`${this.basePath}/${id}`);
    return response.data;
  }

  async markAsRead(id: string): Promise<Voicemail> {
    const response = await apiClient.patch<Voicemail>(`${this.basePath}/${id}`, {
      isNew: false,
    });
    return response.data;
  }

  async deleteVoicemail(id: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${id}`);
  }

  async getVoicemailDrops(): Promise<VoicemailDrop[]> {
    const response = await apiClient.get<VoicemailDrop[]>(`${this.basePath}/drops`);
    return response.data;
  }

  async playVoicemailDrop(dropId: string, callId: string): Promise<void> {
    await apiClient.post(`${this.basePath}/drops/${dropId}/play`, { callId });
  }

  async uploadVoicemailDrop(formData: FormData): Promise<VoicemailDrop> {
    const response = await apiClient.post<VoicemailDrop>(
      `${this.basePath}/drops`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }
}

export const voicemailService = new VoicemailService();
```

### React Hooks for Service Integration

```typescript
// src/hooks/useCallService.ts
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { callService, Call, CreateCallRequest, WrapUpRequest } from '../services/callService';

export const useActiveCalls = () => {
  return useQuery({
    queryKey: ['calls', 'active'],
    queryFn: () => callService.getActiveCalls(),
    refetchInterval: 5000, // Poll every 5 seconds
    staleTime: 2000,
  });
};

export const useInitiateCall = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateCallRequest) => callService.initiateCall(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] });
    },
  });
};

export const useCallActions = (callId: string) => {
  const queryClient = useQueryClient();

  const holdMutation = useMutation({
    mutationFn: () => callService.holdCall(callId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: () => callService.resumeCall(callId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] });
    },
  });

  const endMutation = useMutation({
    mutationFn: () => callService.endCall(callId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calls', 'active'] });
    },
  });

  const wrapUpMutation = useMutation({
    mutationFn: (request: WrapUpRequest) => callService.submitWrapUp(request),
  });

  return {
    hold: holdMutation.mutate,
    resume: resumeMutation.mutate,
    end: endMutation.mutate,
    wrapUp: wrapUpMutation.mutate,
    isLoading: holdMutation.isPending || resumeMutation.isPending || endMutation.isPending,
  };
};
```

---

## CTI Bridge Integration

### Overview

The CTI (Computer Telephony Integration) Bridge provides real-time communication between the Freedom Web application and the telephony infrastructure. It handles:

- Real-time call state updates
- Screen pop functionality
- Softphone controls
- Agent status management
- Call event streaming

### CTI Bridge Architecture

```typescript
// src/services/cti/CTIBridge.ts
import { EventEmitter } from 'events';

export type CallEvent = 
  | 'call:ringing'
  | 'call:connected'
  | 'call:hold'
  | 'call:resume'
  | 'call:transfer'
  | 'call:ended'
  | 'call:error';

export type AgentEvent =
  | 'agent:available'
  | 'agent:busy'
  | 'agent:away'
  | 'agent:offline';

export interface CTIEvent {
  type: CallEvent | AgentEvent;
  timestamp: string;
  payload: Record<string, any>;
  correlationId?: string;
}

export interface CTIConfig {
  wsUrl: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  debug?: boolean;
}

class CTIBridge extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: CTIConfig;
  private reconnectAttempts = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnected = false;
  private messageQueue: CTIEvent[] = [];

  constructor(config: CTIConfig) {
    super();
    this.config = config;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const token = localStorage.getItem('access_token');
        const wsUrl = `${this.config.wsUrl}?token=${token}`;
        
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.flushMessageQueue();
          this.emit('connected');
          this.log('CTI Bridge connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          this.log('WebSocket error:', error);
          this.emit('error', error);
        };

        this.ws.onclose = (event) => {
          this.isConnected = false;
          this.stopHeartbeat();
          this.emit('disconnected', event);
          this.log('CTI Bridge disconnected', event.code, event.reason);
          
          if (!event.wasClean) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    this.isConnected = false;
  }

  sendCommand(command: string, payload: Record<string, any>): void {
    const message: CTIEvent = {
      type: command as CallEvent,
      timestamp: new Date().toISOString(),
      payload,
      correlationId: this.generateCorrelationId(),
    };

    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      this.log('Sent command:', message);
    } else {
      this.messageQueue.push(message);
      this.log('Queued command:', message);
    }
  }

  private handleMessage(data: string): void {
    try {
      const event: CTIEvent = JSON.parse(data);
      this.log('Received event:', event);

      // Emit specific event type
      this.emit(event.type, event);

      // Emit generic event for logging/debugging
      this.emit('message', event);
    } catch (error) {
      this.log('Failed to parse message:', data, error);
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.emit('reconnect_failed');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        this.log('Reconnection failed:', error);
      });
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.sendCommand('heartbeat', { timestamp: Date.now() });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message && this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  private generateCorrelationId(): string {
    return `cti-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[CTI Bridge]', ...args);
    }
  }
}

export const createCTIBridge = (config: Partial<CTIConfig> = {}): CTIBridge => {
  const defaultConfig: CTIConfig = {
    wsUrl: process.env.REACT_APP_CTI_WS_URL || 'wss://cti.freedom.com/ws',
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000,
    debug: process.env.NODE_ENV === 'development',
  };

  return new CTIBridge({ ...defaultConfig, ...config });
};
```

### CTI React Context Provider

```typescript
// src/contexts/CTIContext.tsx
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { CTIBridge, createCTIBridge, CTIEvent, CallEvent } from '../services/cti/CTIBridge';

interface CTIContextValue {
  isConnected: boolean;
  currentCall: any | null;
  agentStatus: string;
  makeCall: (phoneNumber: string) => void;
  answerCall: (callId: string) => void;
  holdCall: (callId: string) => void;
  resumeCall: (callId: string) => void;
  transferCall: (callId: string, target: string) => void;
  endCall: (callId: string) => void;
  setAgentStatus: (status: string) => void;
}

const CTIContext = createContext<CTIContextValue | null>(null);

export const CTIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [bridge] = useState(() => createCTIBridge());
  const [isConnected, setIsConnected] = useState(false);
  const [currentCall, setCurrentCall] = useState<any | null>(null);
  const [agentStatus, setAgentStatusState] = useState('offline');

  useEffect(() => {
    bridge.connect();

    bridge.on('connected', () => setIsConnected(true));
    bridge.on('disconnected', () => setIsConnected(false));

    bridge.on('call:ringing', (event: CTIEvent) => {
      setCurrentCall(event.payload);
      // Trigger screen pop
      notifyIncomingCall(event.payload);
    });

    bridge.on('call:connected', (event: CTIEvent) => {
      setCurrentCall((prev: any) => ({ ...prev, status: 'active' }));
    });

    bridge.on('call:ended', () => {
      setCurrentCall(null);
    });

    return () => {
      bridge.disconnect();
    };
  }, [bridge]);

  const makeCall = useCallback((phoneNumber: string) => {
    bridge.sendCommand('call:initiate', { phoneNumber });
  }, [bridge]);

  const answerCall = useCallback((callId: string) => {
    bridge.sendCommand('call:answer', { callId });
  }, [bridge]);

  const holdCall = useCallback((callId: string) => {
    bridge.sendCommand('call:hold', { callId });
  }, [bridge]);

  const resumeCall = useCallback((callId: string) => {
    bridge.sendCommand('call:resume', { callId });
  }, [bridge]);

  const transferCall = useCallback((callId: string, target: string) => {
    bridge.sendCommand('call:transfer', { callId, target });
  }, [bridge]);

  const endCall = useCallback((callId: string) => {
    bridge.sendCommand('call:end', { callId });
  }, [bridge]);

  const setAgentStatus = useCallback((status: string) => {
    bridge.sendCommand('agent:status', { status });
    setAgentStatusState(status);
  }, [bridge]);

  const value: CTIContextValue = {
    isConnected,
    currentCall,
    agentStatus,
    makeCall,
    answerCall,
    holdCall,
    resumeCall,
    transferCall,
    endCall,
    setAgentStatus,
  };

  return <CTIContext.Provider value={value}>{children}</CTIContext.Provider>;
};

export const useCTI = (): CTIContextValue => {
  const context = useContext(CTIContext);
  if (!context) {
    throw new Error('useCTI must be used within a CTIProvider');
  }
  return context;
};

const notifyIncomingCall = (callData: any) => {
  if (Notification.permission === 'granted') {
    new Notification('Incoming Call', {
      body: `Call from ${callData.callerName || callData.callerId}`,
      icon: '/phone-icon.png',
      requireInteraction: true,
    });
  }
};
```

---

## Telephony Features

### Softphone Integration

```typescript
// src/components/Softphone/Softphone.tsx
import React, { useState, useEffect } from 'react';
import { useCTI } from '../../contexts/CTIContext';

export const Softphone: React.FC = () => {
  const {
    isConnected,
    currentCall,
    agentStatus,
    makeCall,
    answerCall,
    holdCall,
    resumeCall,
    endCall,
    setAgentStatus,
  } = useCTI();

  const [dialNumber, setDialNumber] = useState('');
  const [callDuration, setCallDuration] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (currentCall?.status === 'active') {
      timer = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      clearInterval(timer);
      setCallDuration(0);
    };
  }, [currentCall?.status]);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleDial = () => {
    if (dialNumber.length >= 10) {
      makeCall(dialNumber);
      setDialNumber('');
    }
  };

  const handleKeyPress = (key: string) => {
    if (currentCall?.status === 'active') {
      // Send DTMF tone
      // dtmfService.sendTone(currentCall.id, key);
    } else {
      setDialNumber((prev) => prev + key);
    }
  };

  return (
    <div className="softphone">
      <div className="softphone-status">
        <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>

      <select
        value={agentStatus}
        onChange={(e) => setAgentStatus(e.target.value)}
        className="agent-status-select"
      >
        <option value="available">Available</option>
        <option value="busy">Busy</option>
        <option value="away">Away</option>
        <option value="offline">Offline</option>
      </select>

      {currentCall ? (
        <div className="active-call">
          <div className="call-info">
            <span className="caller-name">{currentCall.callerName || 'Unknown'}</span>
            <span className="caller-number">{currentCall.callerId}</span>
            <span className="call-duration">{formatDuration(callDuration)}</span>
          </div>

          <div className="call-controls">
            {currentCall.status === 'ringing' && (
              <button onClick={() => answerCall(currentCall.id)} className="btn-answer">
                Answer
              </button>
            )}
            
            {currentCall.status === 'active' && (
              <button onClick={() => holdCall(currentCall.id)} className="btn-hold">
                Hold
              </button>
            )}
            
            {currentCall.status === 'on-hold' && (
              <button onClick={() => resumeCall(currentCall.id)} className="btn-resume">
                Resume
              </button>
            )}
            
            <button onClick={() => endCall(currentCall.id)} className="btn-end">
              End
            </button>
          </div>
        </div>
      ) : (
        <div className="dialer">
          <input
            type="tel"
            value={dialNumber}
            onChange={(e) => setDialNumber(e.target.value)}
            placeholder="Enter number"
            className="dial-input"
          />
          
          <div className="keypad">
            {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((key) => (
              <button
                key={key}
                onClick={() => handleKeyPress(key)}
                className="keypad-btn"
              >
                {key}
              </button>
            ))}
          </div>
          
          <button
            onClick={handleDial}
            disabled={dialNumber.length < 10}
            className="btn-dial"
          >
            Dial
          </button>
        </div>
      )}
    </div>
  );
};
```

### Screen Pop Service

```typescript
// src/services/screenPopService.ts
import { callService } from './callService';
import { contactService } from './contactService';

export interface ScreenPopData {
  caller: {
    phoneNumber: string;
    name?: string;
    contactId?: string;
  };
  recentCalls: any[];
  contactHistory: any[];
  openCases: any[];
}

class ScreenPopService {
  async getScreenPopData(callerId: string): Promise<ScreenPopData> {
    // Parallel fetch of related data
    const [contact, recentCalls, openCases] = await Promise.allSettled([
      contactService.findByPhone(callerId),
      callService.getCallHistory({ phoneNumber: callerId, limit: 5 }),
      this.getOpenCases(callerId),
    ]);

    return {
      caller: {
        phoneNumber: callerId,
        name: contact.status === 'fulfilled' ? contact.value?.name : undefined,
        contactId: contact.status === 'fulfilled' ? contact.value?.id : undefined,
      },
      recentCalls: recentCalls.status === 'fulfilled' ? recentCalls.value.calls : [],
      contactHistory: [],
      openCases: openCases.status === 'fulfilled' ? openCases.value : [],
    };
  }

  private async getOpenCases(callerId: string): Promise<any[]> {
    // Integration with case management system
    return [];
  }
}

export const screenPopService = new ScreenPopService();
```

---

## Error Handling

### Error Types and Handling Strategies

```typescript
// src/services/api/errorHandler.ts
export enum ErrorCode {
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT = 'TIMEOUT',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  NOT_FOUND = 'NOT_FOUND',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  RATE_LIMIT = 'RATE_LIMIT',
  SERVER_ERROR = 'SERVER_ERROR',
  CTI_CONNECTION_ERROR = 'CTI_CONNECTION_ERROR',
  CTI_COMMAND_FAILED = 'CTI_COMMAND_FAILED',
  UNKNOWN = 'UNKNOWN',
}

export interface AppError {
  code: ErrorCode;
  message: string;
  details?: Record<string, any>;
  recoverable: boolean;
  retryable: boolean;
  userMessage: string;
}

const ERROR_MESSAGES: Record<ErrorCode, { message: string; recoverable: boolean; retryable: boolean }> = {
  [ErrorCode.NETWORK_ERROR]: {
    message: 'Network connection failed',
    recoverable: true,
    retryable: true,
  },
  [ErrorCode.TIMEOUT]: {
    message: 'Request timed out',
    recoverable: true,
    retryable: true,
  },
  [ErrorCode.UNAUTHORIZED]: {
    message: 'Authentication required',
    recoverable: true,
    retryable: false,
  },
  [ErrorCode.FORBIDDEN]: {
    message: 'Access denied',
    recoverable: false,
    retryable: false,
  },
  [ErrorCode.NOT_FOUND]: {
    message: 'Resource not found',
    recoverable: false,
    retryable: false,
  },
  [ErrorCode.VALIDATION_ERROR]: {
    message: 'Invalid input data',
    recoverable: true,
    retryable: false,
  },
  [ErrorCode.RATE_LIMIT]: {
    message: 'Too many requests',
    recoverable: true,
    retryable: true,
  },
  [ErrorCode.SERVER_ERROR]: {
    message: 'Server error occurred',
    recoverable: true,
    retryable: true,
  },
  [ErrorCode.CTI_CONNECTION_ERROR]: {
    message: 'Telephony connection failed',
    recoverable: true,
    retryable: true,
  },
  [ErrorCode.CTI_COMMAND_FAILED]: {
    message: 'Call operation failed',
    recoverable: true,
    retryable: true,
  },
  [ErrorCode.UNKNOWN]: {
    message: 'An unexpected error occurred',
    recoverable: false,
    retryable: false,
  },
};

export const createAppError = (
  code: ErrorCode,
  details?: Record<string, any>,
  customMessage?: string
): AppError => {
  const config = ERROR_MESSAGES[code];
  return {
    code,
    message: config.message,
    details,
    recoverable: config.recoverable,
    retryable: config.retryable,
    userMessage: customMessage || config.message,
  };
};

export const handleApiError = (error: any): AppError => {
  if (!error.response) {
    // Network error
    if (error.code === 'ECONNABORTED') {
      return createAppError(ErrorCode.TIMEOUT);
    }
    return createAppError(ErrorCode.NETWORK_ERROR);
  }

  const status = error.response.status;
  const data = error.response.data;

  switch (status) {
    case 401:
      return createAppError(ErrorCode.UNAUTHORIZED);
    case 403:
      return createAppError(ErrorCode.FORBIDDEN);
    case 404:
      return createAppError(ErrorCode.NOT_FOUND);
    case 422:
      return createAppError(ErrorCode.VALIDATION_ERROR, data.errors);
    case 429:
      return createAppError(ErrorCode.RATE_LIMIT);
    case 500:
    case 502:
    case 503:
    case 504:
      return createAppError(ErrorCode.SERVER_ERROR);
    default:
      return createAppError(ErrorCode.UNKNOWN, { status, data });
  }
};
```

### React Error Boundary Integration

```typescript
// src/components/ErrorBoundary/ApiErrorHandler.tsx
import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AppError, ErrorCode } from '../../services/api/errorHandler';

interface ApiErrorHandlerProps {
  error: AppError;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ApiErrorHandler: React.FC<ApiErrorHandlerProps> = ({
  error,
  onRetry,
  onDismiss,
}) => {
  const queryClient = useQueryClient();

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    } else {
      queryClient.invalidateQueries();
    }
  };

  return (
    <div className="api-error-handler" role="alert">
      <div className="error-icon">
        {error.code === ErrorCode.NETWORK_ERROR ? '📡' : '⚠️'}
      </div>
      
      <h3 className="error-title">
        {error.code === ErrorCode.NETWORK_ERROR
          ? 'Connection Issue'
          : 'Something Went Wrong'}
      </h3>
      
      <p className="error-message">{error.userMessage}</p>
      
      {error.details && (
        <details className="error-details">
          <summary>Technical Details</summary>
          <pre>{JSON.stringify(error.details, null, 2)}</pre>
        </details>
      )}
      
      <div className="error-actions">
        {error.retryable && (
          <button onClick={handleRetry} className="btn-retry">
            Try Again
          </button>
        )}
        
        {onDismiss && (
          <button onClick={onDismiss} className="btn-dismiss">
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
};
```

### Retry Mechanism

```typescript
// src/services/api/retryMechanism.ts
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  retryableErrors: ErrorCode[];
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  retryableErrors: [
    ErrorCode.NETWORK_ERROR,
    ErrorCode.TIMEOUT,
    ErrorCode.SERVER_ERROR,
    ErrorCode.RATE_LIMIT,
  ],
};

export const withRetry = async <T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> => {
  const finalConfig = { ...defaultRetryConfig, ...config };
  let lastError: AppError;
  
  for (let attempt = 0; attempt <= finalConfig.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as AppError;
      
      if (!finalConfig.retryableErrors.includes(lastError.code)) {
        throw error;
      }
      
      if (attempt === finalConfig.maxRetries) {
        throw error;
      }
      
      const delay = Math.min(
        finalConfig.baseDelay * Math.pow(2, attempt),
        finalConfig.maxDelay
      );
      
      console.warn(`Retry attempt ${attempt + 1} after ${delay}ms`, lastError);
      await sleep(delay);
    }
  }
  
  throw lastError!;
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
```

---

## Best Practices

### 1. Service Layer Organization

```
src/
├── services/
│   ├── api/
│   │   ├── axiosConfig.ts      # Base Axios configuration
│   │   ├── interceptors.ts      # Request/Response interceptors
│   │   ├── tokenRefresh.ts      # Token management
│   │   ├── errorHandler.ts      # Error handling utilities
│   │   └── retryMechanism.ts    # Retry logic
│   ├── cti/
│   │   ├── CTIBridge.ts         # WebSocket bridge
│   │   ├── events.ts            # Event type definitions
│   │   └── commands.ts          # CTI command builders
│   ├── callService.ts           # Call management
│   ├── voicemailService.ts      # Voicemail operations
│   ├── contactService.ts        # Address book
│   └── index.ts                 # Service exports
```

### 2. Environment-Specific Configuration

```typescript
// src/config/api.config.ts
interface ApiConfig {
  baseUrl: string;
  ctiWsUrl: string;
  timeout: number;
  retryAttempts: number;
}

const configs: Record<string, ApiConfig> = {
  development: {
    baseUrl: 'http://localhost:3001/api/v1',
    ctiWsUrl: 'ws://localhost:3002/cti',
    timeout: 30000,
    retryAttempts: 3,
  },
  staging: {
    baseUrl: 'https://staging-api.freedom.com/v1',
    ctiWsUrl: 'wss://staging-cti.freedom.com/ws',
    timeout: 30000,
    retryAttempts: 3,
  },
  production: {
    baseUrl: 'https://api.freedom.com/v1',
    ctiWsUrl: 'wss://cti.freedom.com/ws',
    timeout: 30000,
    retryAttempts: 5,
  },
};

export const apiConfig = configs[process.env.NODE_ENV || 'development'];
```

### 3. Testing Services

```typescript
// src/services/__tests__/callService.test.ts
import { callService } from '../callService';
import { apiClient } from '../api/axiosConfig';

jest.mock('../api/axiosConfig');

describe('CallService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getActiveCalls', () => {
    it('should return active calls', async () => {
      const mockCalls = [
        { id: '1', status: 'active' },
        { id: '2', status: 'ringing' },
      ];
      
      (apiClient.get as jest.Mock).mockResolvedValue({ data: mockCalls });

      const result = await callService.getActiveCalls();

      expect(apiClient.get).toHaveBeenCalledWith('/calls/active');
      expect(result).toEqual(mockCalls);
    });

    it('should handle errors gracefully', async () => {
      (apiClient.get as jest.Mock).mockRejectedValue(new Error('Network error'));

      await expect(callService.getActiveCalls()).rejects.toThrow('Network error');
    });
  });
});
```

---

## Summary

The Freedom Web service layer provides a robust foundation for telephony operations with:

- **Axios HTTP Client**: Configured with interceptors for authentication, error handling, and request/response transformation
- **CTI Bridge**: Real-time WebSocket integration for telephony events and commands
- **Domain Services**: Modular services for calls, voicemail, contacts, and team collaboration
- **Error Handling**: Comprehensive error classification with retry mechanisms
- **React Integration**: Custom hooks and context providers for seamless UI integration

For additional support or questions, contact the Freedom Web development team or refer to the API documentation.