# WebSocket Communication Guide

## Overview

This comprehensive guide documents the WebSocket communication architecture, message types, and connection management patterns used in the FreedomCTI platform-cti-client service. WebSocket communication is the backbone of real-time call management, enabling instant call event notifications, presence updates, and bidirectional communication between the Salesforce-embedded CTI client and the backend telephony systems.

Understanding the WebSocket implementation is critical for developers working on real-time features, debugging connection issues, and extending the platform's capabilities.

## WebSocket Architecture

### Architectural Overview

The FreedomCTI WebSocket architecture follows a layered design pattern that separates concerns between connection management, message handling, state synchronization, and UI updates.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Salesforce Lightning                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FreedomCTI iframe                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │   React UI   │  │Redux Store  │  │ WebSocket Layer │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │  │
│  │         │                │                   │             │  │
│  │         └────────────────┴───────────────────┘             │  │
│  └───────────────────────────┬───────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────────┘
                               │ WSS Connection
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Minerva WebSocket Server                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Connection  │  │  Message    │  │   Subscription          │ │
│  │  Manager    │  │  Router     │  │   Manager               │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### WebSocket Service Layer

```javascript
// src/services/websocket/WebSocketService.js
class WebSocketService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.subscriptions = new Map();
    this.messageHandlers = new Map();
    this.connectionState = 'disconnected';
  }

  /**
   * Initialize WebSocket connection with authentication
   * @param {string} endpoint - WebSocket server endpoint
   * @param {Object} authConfig - Authentication configuration
   */
  async connect(endpoint, authConfig) {
    const wsUrl = this.buildConnectionUrl(endpoint, authConfig);
    
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = (event) => {
        this.connectionState = 'connected';
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        resolve(event);
      };
      
      this.socket.onclose = (event) => {
        this.handleDisconnection(event);
      };
      
      this.socket.onerror = (error) => {
        this.connectionState = 'error';
        reject(error);
      };
      
      this.socket.onmessage = (event) => {
        this.handleMessage(event);
      };
    });
  }

  buildConnectionUrl(endpoint, authConfig) {
    const params = new URLSearchParams({
      token: authConfig.accessToken,
      userId: authConfig.userId,
      orgId: authConfig.salesforceOrgId,
      timestamp: Date.now()
    });
    return `${endpoint}?${params.toString()}`;
  }
}
```

#### Redux Middleware Integration

The WebSocket layer integrates with Redux through custom middleware, ensuring all WebSocket events properly update application state:

```javascript
// src/middleware/websocketMiddleware.js
const websocketMiddleware = (wsService) => (store) => (next) => (action) => {
  switch (action.type) {
    case 'WEBSOCKET_CONNECT':
      wsService.connect(action.payload.endpoint, action.payload.auth)
        .then(() => {
          store.dispatch({ type: 'WEBSOCKET_CONNECTED' });
          // Restore subscriptions after reconnection
          wsService.restoreSubscriptions();
        })
        .catch((error) => {
          store.dispatch({ 
            type: 'WEBSOCKET_ERROR', 
            payload: { error: error.message } 
          });
        });
      break;
      
    case 'WEBSOCKET_SEND':
      wsService.send(action.payload);
      break;
      
    case 'WEBSOCKET_SUBSCRIBE_USER':
      wsService.subscribeUser(action.payload.userId);
      break;
      
    case 'WEBSOCKET_SUBSCRIBE_GROUP':
      wsService.subscribeGroup(action.payload.groupId);
      break;
      
    case 'WEBSOCKET_DISCONNECT':
      wsService.disconnect();
      break;
      
    default:
      break;
  }
  
  return next(action);
};

export default websocketMiddleware;
```

## Connection Lifecycle

### Connection States

The WebSocket connection transitions through several states during its lifecycle:

| State | Description | Triggers |
|-------|-------------|----------|
| `disconnected` | No active connection | Initial state, manual disconnect, server close |
| `connecting` | Connection attempt in progress | `connect()` called |
| `connected` | Active, healthy connection | Successful handshake |
| `reconnecting` | Automatic reconnection in progress | Connection lost unexpectedly |
| `error` | Connection failed | Network error, authentication failure |
| `suspended` | Temporarily paused | Browser tab hidden, network offline |

### Connection Initialization Flow

```javascript
// src/hooks/useWebSocketConnection.js
import { useEffect, useCallback, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';

export const useWebSocketConnection = () => {
  const dispatch = useDispatch();
  const connectionState = useSelector(state => state.websocket.connectionState);
  const authToken = useSelector(state => state.auth.accessToken);
  const userId = useSelector(state => state.user.id);
  const heartbeatRef = useRef(null);

  const initializeConnection = useCallback(async () => {
    const endpoint = getWebSocketEndpoint(process.env.REACT_APP_ENV);
    
    dispatch({
      type: 'WEBSOCKET_CONNECT',
      payload: {
        endpoint,
        auth: {
          accessToken: authToken,
          userId,
          salesforceOrgId: window.SF_ORG_ID
        }
      }
    });
  }, [dispatch, authToken, userId]);

  const handleVisibilityChange = useCallback(() => {
    if (document.hidden) {
      dispatch({ type: 'WEBSOCKET_SUSPEND' });
    } else {
      dispatch({ type: 'WEBSOCKET_RESUME' });
    }
  }, [dispatch]);

  useEffect(() => {
    if (authToken && userId) {
      initializeConnection();
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('online', initializeConnection);
    window.addEventListener('offline', () => {
      dispatch({ type: 'WEBSOCKET_SUSPEND' });
    });

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('online', initializeConnection);
      dispatch({ type: 'WEBSOCKET_DISCONNECT' });
    };
  }, [authToken, userId, initializeConnection, handleVisibilityChange, dispatch]);

  return { connectionState, reconnect: initializeConnection };
};
```

### Heartbeat Mechanism

Maintaining connection health requires regular heartbeat messages:

```javascript
// src/services/websocket/heartbeat.js
class HeartbeatManager {
  constructor(wsService, options = {}) {
    this.wsService = wsService;
    this.interval = options.interval || 30000; // 30 seconds
    this.timeout = options.timeout || 10000;   // 10 seconds
    this.heartbeatTimer = null;
    this.timeoutTimer = null;
    this.missedHeartbeats = 0;
    this.maxMissedHeartbeats = 3;
  }

  start() {
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.interval);
  }

  sendHeartbeat() {
    const heartbeatMessage = {
      type: 'HEARTBEAT',
      timestamp: Date.now(),
      clientId: this.wsService.clientId
    };

    this.wsService.send(heartbeatMessage);

    // Start timeout for response
    this.timeoutTimer = setTimeout(() => {
      this.handleMissedHeartbeat();
    }, this.timeout);
  }

  handleHeartbeatResponse(response) {
    clearTimeout(this.timeoutTimer);
    this.missedHeartbeats = 0;
    
    // Calculate latency for monitoring
    const latency = Date.now() - response.originalTimestamp;
    this.wsService.emit('latency', latency);
  }

  handleMissedHeartbeat() {
    this.missedHeartbeats++;
    
    if (this.missedHeartbeats >= this.maxMissedHeartbeats) {
      console.warn('WebSocket: Max missed heartbeats reached, reconnecting...');
      this.wsService.reconnect();
    }
  }

  stop() {
    clearInterval(this.heartbeatTimer);
    clearTimeout(this.timeoutTimer);
  }
}
```

## Message Types

### Message Structure

All WebSocket messages follow a standardized structure for consistency:

```typescript
// src/types/websocket.d.ts
interface WebSocketMessage {
  type: MessageType;
  id: string;           // Unique message identifier
  timestamp: number;    // Unix timestamp
  payload: any;         // Message-specific data
  meta?: {
    correlationId?: string;  // For request-response patterns
    priority?: 'high' | 'normal' | 'low';
    ttl?: number;            // Time to live in milliseconds
  };
}

type MessageType = 
  | 'CALL_INCOMING'
  | 'CALL_CONNECTED'
  | 'CALL_ENDED'
  | 'CALL_HELD'
  | 'CALL_TRANSFERRED'
  | 'VOICEMAIL_NEW'
  | 'VOICEMAIL_UPDATED'
  | 'PRESENCE_UPDATE'
  | 'AGENT_STATUS_CHANGE'
  | 'QUEUE_UPDATE'
  | 'HEARTBEAT'
  | 'HEARTBEAT_ACK'
  | 'SUBSCRIBE'
  | 'UNSUBSCRIBE'
  | 'SUBSCRIPTION_CONFIRMED'
  | 'ERROR';
```

### Call Event Messages

```javascript
// src/handlers/callEventHandlers.js

/**
 * Incoming Call Message
 * Triggered when a new call is routed to the agent
 */
const incomingCallMessage = {
  type: 'CALL_INCOMING',
  id: 'msg-uuid-123',
  timestamp: 1699234567890,
  payload: {
    callId: 'call-uuid-456',
    callSid: 'CA1234567890abcdef',
    direction: 'inbound',
    from: '+15551234567',
    to: '+15559876543',
    queueId: 'queue-uuid-789',
    queueName: 'Sales Queue',
    callerInfo: {
      name: 'John Doe',
      accountId: '001ABC123',
      contactId: '003DEF456',
      caseId: null
    },
    ani: '+15551234567',
    dnis: '+15559876543',
    waitTime: 45  // seconds in queue
  }
};

/**
 * Handler for incoming call events
 */
export const handleIncomingCall = (store) => (message) => {
  const { payload } = message;
  
  // Update call state
  store.dispatch({
    type: 'CALL_RECEIVED',
    payload: {
      call: payload,
      receivedAt: message.timestamp
    }
  });
  
  // Trigger screen pop in Salesforce
  const screenPopData = {
    type: 'SCREEN_POP',
    searchParams: payload.from,
    callInfo: payload
  };
  window.parent.postMessage(screenPopData, '*');
  
  // Play notification sound
  playNotificationSound('incoming_call');
};

/**
 * Call Connected Message
 */
const callConnectedMessage = {
  type: 'CALL_CONNECTED',
  id: 'msg-uuid-124',
  timestamp: 1699234570000,
  payload: {
    callId: 'call-uuid-456',
    connectedAt: 1699234570000,
    participants: [
      { id: 'agent-uuid-001', role: 'agent', name: 'Jane Smith' },
      { id: 'caller-uuid-002', role: 'caller', number: '+15551234567' }
    ],
    recordingEnabled: true,
    recordingId: 'rec-uuid-789'
  }
};

/**
 * Call Ended Message
 */
const callEndedMessage = {
  type: 'CALL_ENDED',
  id: 'msg-uuid-125',
  timestamp: 1699234800000,
  payload: {
    callId: 'call-uuid-456',
    endedAt: 1699234800000,
    duration: 230,  // seconds
    disposition: 'completed',
    endedBy: 'caller',
    wrapUpRequired: true,
    wrapUpTimeout: 120  // seconds
  }
};
```

### Voicemail Messages

```javascript
// src/handlers/voicemailHandlers.js

/**
 * New Voicemail Message
 */
const newVoicemailMessage = {
  type: 'VOICEMAIL_NEW',
  id: 'msg-uuid-200',
  timestamp: 1699235000000,
  payload: {
    voicemailId: 'vm-uuid-001',
    from: '+15551234567',
    to: '+15559876543',
    duration: 45,
    transcription: 'Hi, this is John calling about my order...',
    transcriptionConfidence: 0.92,
    recordingUrl: '/api/voicemail/vm-uuid-001/audio',
    callerInfo: {
      name: 'John Doe',
      contactId: '003DEF456'
    },
    priority: 'normal',
    createdAt: 1699235000000
  }
};

export const handleNewVoicemail = (store) => (message) => {
  const { payload } = message;
  
  store.dispatch({
    type: 'VOICEMAIL_ADDED',
    payload: {
      voicemail: payload,
      unreadCount: store.getState().voicemail.unreadCount + 1
    }
  });
  
  // Show notification
  showNotification({
    title: 'New Voicemail',
    body: `From: ${payload.callerInfo?.name || payload.from}`,
    icon: '/icons/voicemail.png'
  });
};
```

### Presence and Status Messages

```javascript
// src/handlers/presenceHandlers.js

/**
 * Presence Update Message
 */
const presenceUpdateMessage = {
  type: 'PRESENCE_UPDATE',
  id: 'msg-uuid-300',
  timestamp: 1699235100000,
  payload: {
    userId: 'user-uuid-001',
    status: 'available',
    previousStatus: 'away',
    statusMessage: 'Back from lunch',
    availableChannels: ['voice', 'chat'],
    skills: ['sales', 'support'],
    capacity: {
      voice: { current: 0, max: 1 },
      chat: { current: 2, max: 3 }
    },
    updatedAt: 1699235100000
  }
};

/**
 * Agent Status Change Message
 */
const agentStatusMessage = {
  type: 'AGENT_STATUS_CHANGE',
  id: 'msg-uuid-301',
  timestamp: 1699235200000,
  payload: {
    agentId: 'agent-uuid-001',
    newStatus: 'on_call',
    statusReason: 'Inbound call accepted',
    callId: 'call-uuid-456',
    queueIds: ['queue-001', 'queue-002'],
    timestamp: 1699235200000
  }
};
```

## User Subscriptions

### Subscribing to User Events

User subscriptions enable real-time updates for individual agent activities:

```javascript
// src/services/websocket/subscriptions/userSubscription.js

class UserSubscriptionManager {
  constructor(wsService) {
    this.wsService = wsService;
    this.activeSubscriptions = new Set();
  }

  /**
   * Subscribe to user-specific events
   * @param {string} userId - The user ID to subscribe to
   * @param {Object} options - Subscription options
   */
  async subscribe(userId, options = {}) {
    const subscriptionMessage = {
      type: 'SUBSCRIBE',
      id: generateMessageId(),
      timestamp: Date.now(),
      payload: {
        channel: 'user',
        userId,
        events: options.events || [
          'CALL_INCOMING',
          'CALL_CONNECTED',
          'CALL_ENDED',
          'CALL_HELD',
          'CALL_TRANSFERRED',
          'VOICEMAIL_NEW',
          'VOICEMAIL_UPDATED',
          'PRESENCE_UPDATE'
        ],
        options: {
          includeHistory: options.includeHistory || false,
          historyLimit: options.historyLimit || 10
        }
      }
    };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Subscription timeout'));
      }, 10000);

      const handleConfirmation = (message) => {
        if (message.type === 'SUBSCRIPTION_CONFIRMED' && 
            message.payload.channel === 'user' &&
            message.payload.userId === userId) {
          clearTimeout(timeout);
          this.wsService.off('message', handleConfirmation);
          this.activeSubscriptions.add(userId);
          resolve(message.payload);
        }
      };

      this.wsService.on('message', handleConfirmation);
      this.wsService.send(subscriptionMessage);
    });
  }

  /**
   * Unsubscribe from user events
   * @param {string} userId - The user ID to unsubscribe from
   */
  unsubscribe(userId) {
    const unsubscribeMessage = {
      type: 'UNSUBSCRIBE',
      id: generateMessageId(),
      timestamp: Date.now(),
      payload: {
        channel: 'user',
        userId
      }
    };

    this.wsService.send(unsubscribeMessage);
    this.activeSubscriptions.delete(userId);
  }

  /**
   * Get all active user subscriptions
   */
  getActiveSubscriptions() {
    return Array.from(this.activeSubscriptions);
  }
}

export default UserSubscriptionManager;
```

### User Subscription Events

```javascript
// src/hooks/useUserSubscription.js
import { useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';

export const useUserSubscription = (userId) => {
  const dispatch = useDispatch();
  const subscriptionStatus = useSelector(
    state => state.websocket.subscriptions.user[userId]
  );

  const handleUserEvent = useCallback((message) => {
    switch (message.type) {
      case 'CALL_INCOMING':
        dispatch({ type: 'HANDLE_INCOMING_CALL', payload: message.payload });
        break;
      case 'CALL_CONNECTED':
        dispatch({ type: 'HANDLE_CALL_CONNECTED', payload: message.payload });
        break;
      case 'CALL_ENDED':
        dispatch({ type: 'HANDLE_CALL_ENDED', payload: message.payload });
        break;
      case 'VOICEMAIL_NEW':
        dispatch({ type: 'HANDLE_NEW_VOICEMAIL', payload: message.payload });
        break;
      default:
        console.log('Unhandled user event:', message.type);
    }
  }, [dispatch]);

  useEffect(() => {
    if (userId) {
      dispatch({
        type: 'WEBSOCKET_SUBSCRIBE_USER',
        payload: { userId, handler: handleUserEvent }
      });
    }

    return () => {
      if (userId) {
        dispatch({
          type: 'WEBSOCKET_UNSUBSCRIBE_USER',
          payload: { userId }
        });
      }
    };
  }, [userId, handleUserEvent, dispatch]);

  return { subscriptionStatus };
};
```

## Group Subscriptions

### Queue and Team Subscriptions

Group subscriptions allow monitoring of queues, teams, and shared resources:

```javascript
// src/services/websocket/subscriptions/groupSubscription.js

class GroupSubscriptionManager {
  constructor(wsService) {
    this.wsService = wsService;
    this.groupSubscriptions = new Map();
  }

  /**
   * Subscribe to queue events
   * @param {string} queueId - Queue identifier
   * @param {Object} options - Subscription options
   */
  async subscribeToQueue(queueId, options = {}) {
    return this.subscribeToGroup('queue', queueId, {
      events: [
        'QUEUE_UPDATE',
        'CALL_QUEUED',
        'CALL_DEQUEUED',
        'QUEUE_STATS_UPDATE',
        'SLA_WARNING',
        'SLA_BREACH'
      ],
      ...options
    });
  }

  /**
   * Subscribe to team events
   * @param {string} teamId - Team identifier
   * @param {Object} options - Subscription options
   */
  async subscribeToTeam(teamId, options = {}) {
    return this.subscribeToGroup('team', teamId, {
      events: [
        'AGENT_STATUS_CHANGE',
        'TEAM_STATS_UPDATE',
        'MEMBER_ADDED',
        'MEMBER_REMOVED'
      ],
      ...options
    });
  }

  /**
   * Generic group subscription
   */
  async subscribeToGroup(groupType, groupId, options) {
    const subscriptionKey = `${groupType}:${groupId}`;
    
    const subscriptionMessage = {
      type: 'SUBSCRIBE',
      id: generateMessageId(),
      timestamp: Date.now(),
      payload: {
        channel: 'group',
        groupType,
        groupId,
        events: options.events,
        options: {
          includeStats: options.includeStats || true,
          statsInterval: options.statsInterval || 5000
        }
      }
    };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Group subscription timeout: ${subscriptionKey}`));
      }, 10000);

      const handleConfirmation = (message) => {
        if (message.type === 'SUBSCRIPTION_CONFIRMED' &&
            message.payload.groupType === groupType &&
            message.payload.groupId === groupId) {
          clearTimeout(timeout);
          this.wsService.off('message', handleConfirmation);
          
          this.groupSubscriptions.set(subscriptionKey, {
            groupType,
            groupId,
            subscribedAt: Date.now(),
            events: options.events
          });
          
          resolve(message.payload);
        }
      };

      this.wsService.on('message', handleConfirmation);
      this.wsService.send(subscriptionMessage);
    });
  }

  /**
   * Unsubscribe from a group
   */
  unsubscribeFromGroup(groupType, groupId) {
    const subscriptionKey = `${groupType}:${groupId}`;
    
    const unsubscribeMessage = {
      type: 'UNSUBSCRIBE',
      id: generateMessageId(),
      timestamp: Date.now(),
      payload: {
        channel: 'group',
        groupType,
        groupId
      }
    };

    this.wsService.send(unsubscribeMessage);
    this.groupSubscriptions.delete(subscriptionKey);
  }
}
```

### Queue Statistics Updates

```javascript
// src/handlers/queueHandlers.js

/**
 * Queue Update Message Structure
 */
const queueUpdateMessage = {
  type: 'QUEUE_UPDATE',
  id: 'msg-uuid-400',
  timestamp: 1699236000000,
  payload: {
    queueId: 'queue-uuid-001',
    queueName: 'Sales Queue',
    stats: {
      callsInQueue: 5,
      longestWaitTime: 120,  // seconds
      averageWaitTime: 45,   // seconds
      availableAgents: 3,
      totalAgents: 8,
      busyAgents: 4,
      awayAgents: 1,
      serviceLevelTarget: 80,  // percentage
      currentServiceLevel: 75,  // percentage
      callsAnsweredToday: 150,
      callsAbandonedToday: 12,
      averageHandleTime: 280   // seconds
    },
    slaStatus: 'warning',  // 'healthy', 'warning', 'critical'
    updatedAt: 1699236000000
  }
};

export const handleQueueUpdate = (store) => (message) => {
  const { payload } = message;
  
  store.dispatch({
    type: 'QUEUE_STATS_UPDATED',
    payload: {
      queueId: payload.queueId,
      stats: payload.stats,
      slaStatus: payload.slaStatus
    }
  });
  
  // Check for SLA warnings
  if (payload.slaStatus === 'warning' || payload.slaStatus === 'critical') {
    store.dispatch({
      type: 'SLA_ALERT',
      payload: {
        queueId: payload.queueId,
        queueName: payload.queueName,
        status: payload.slaStatus,
        currentLevel: payload.stats.currentServiceLevel,
        targetLevel: payload.stats.serviceLevelTarget
      }
    });
  }
};
```

## Error Handling and Reconnection

### Error Types and Handling

```javascript
// src/services/websocket/errorHandler.js

const WebSocketErrorCodes = {
  NORMAL_CLOSURE: 1000,
  GOING_AWAY: 1001,
  PROTOCOL_ERROR: 1002,
  UNSUPPORTED_DATA: 1003,
  NO_STATUS_RECEIVED: 1005,
  ABNORMAL_CLOSURE: 1006,
  INVALID_PAYLOAD: 1007,
  POLICY_VIOLATION: 1008,
  MESSAGE_TOO_BIG: 1009,
  INTERNAL_ERROR: 1011,
  SERVICE_RESTART: 1012,
  TRY_AGAIN_LATER: 1013,
  TLS_HANDSHAKE_FAILED: 1015
};

class WebSocketErrorHandler {
  constructor(wsService, store) {
    this.wsService = wsService;
    this.store = store;
  }

  handleError(error, closeEvent = null) {
    const errorInfo = this.classifyError(error, closeEvent);
    
    // Log error for debugging
    console.error('WebSocket Error:', errorInfo);
    
    // Dispatch error to store
    this.store.dispatch({
      type: 'WEBSOCKET_ERROR',
      payload: errorInfo
    });
    
    // Determine recovery action
    this.determineRecoveryAction(errorInfo);
  }

  classifyError(error, closeEvent) {
    if (closeEvent) {
      return {
        type: 'close',
        code: closeEvent.code,
        reason: closeEvent.reason || this.getReasonFromCode(closeEvent.code),
        wasClean: closeEvent.wasClean,
        recoverable: this.isRecoverable(closeEvent.code),
        timestamp: Date.now()
      };
    }
    
    return {
      type: 'error',
      message: error.message,
      recoverable: true,
      timestamp: Date.now()
    };
  }

  getReasonFromCode(code) {
    const reasons = {
      [WebSocketErrorCodes.NORMAL_CLOSURE]: 'Normal closure',
      [WebSocketErrorCodes.GOING_AWAY]: 'Server going away',
      [WebSocketErrorCodes.PROTOCOL_ERROR]: 'Protocol error',
      [WebSocketErrorCodes.ABNORMAL_CLOSURE]: 'Abnormal closure',
      [WebSocketErrorCodes.INTERNAL_ERROR]: 'Internal server error',
      [WebSocketErrorCodes.SERVICE_RESTART]: 'Service restart'
    };
    return reasons[code] || 'Unknown error';
  }

  isRecoverable(code) {
    const nonRecoverableCodes = [
      WebSocketErrorCodes.PROTOCOL_ERROR,
      WebSocketErrorCodes.UNSUPPORTED_DATA,
      WebSocketErrorCodes.POLICY_VIOLATION,
      WebSocketErrorCodes.TLS_HANDSHAKE_FAILED
    ];
    return !nonRecoverableCodes.includes(code);
  }

  determineRecoveryAction(errorInfo) {
    if (!errorInfo.recoverable) {
      this.store.dispatch({
        type: 'WEBSOCKET_FATAL_ERROR',
        payload: {
          message: 'WebSocket connection cannot be recovered',
          error: errorInfo
        }
      });
      return;
    }
    
    // Trigger reconnection
    this.wsService.scheduleReconnect();
  }
}
```

### Reconnection Strategy

```javascript
// src/services/websocket/reconnectionManager.js

class ReconnectionManager {
  constructor(wsService, options = {}) {
    this.wsService = wsService;
    this.maxAttempts = options.maxAttempts || 10;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 30000;
    this.attempts = 0;
    this.reconnectTimer = null;
    this.backoffMultiplier = options.backoffMultiplier || 2;
  }

  /**
   * Calculate delay with exponential backoff and jitter
   */
  calculateDelay() {
    const exponentialDelay = this.baseDelay * Math.pow(this.backoffMultiplier, this.attempts);
    const cappedDelay = Math.min(exponentialDelay, this.maxDelay);
    
    // Add jitter (±20%)
    const jitter = cappedDelay * 0.2 * (Math.random() * 2 - 1);
    return Math.floor(cappedDelay + jitter);
  }

  /**
   * Schedule a reconnection attempt
   */
  scheduleReconnect() {
    if (this.attempts >= this.maxAttempts) {
      console.error('Max reconnection attempts reached');
      this.wsService.emit('reconnect_failed', {
        attempts: this.attempts,
        message: 'Maximum reconnection attempts exceeded'
      });
      return;
    }

    const delay = this.calculateDelay();
    this.attempts++;

    console.log(`Scheduling reconnection attempt ${this.attempts}/${this.maxAttempts} in ${delay}ms`);

    this.wsService.emit('reconnecting', {
      attempt: this.attempts,
      maxAttempts: this.maxAttempts,
      delay
    });

    this.reconnectTimer = setTimeout(async () => {
      try {
        await this.wsService.connect();
        this.reset();
        this.wsService.emit('reconnected', { attempts: this.attempts });
      } catch (error) {
        console.error('Reconnection attempt failed:', error);
        this.scheduleReconnect();
      }
    }, delay);
  }

  /**
   * Reset reconnection state
   */
  reset() {
    this.attempts = 0;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Cancel pending reconnection
   */
  cancel() {
    this.reset();
    this.wsService.emit('reconnect_cancelled');
  }
}
```

### Connection State UI Component

```jsx
// src/components/ConnectionStatus/ConnectionStatus.jsx
import React from 'react';
import { useSelector } from 'react-redux';
import './ConnectionStatus.css';

const ConnectionStatus = () => {
  const connectionState = useSelector(state => state.websocket.connectionState);
  const reconnectInfo = useSelector(state => state.websocket.reconnectInfo);

  const getStatusConfig = () => {
    switch (connectionState) {
      case 'connected':
        return { 
          label: 'Connected', 
          className: 'status-connected',
          icon: '🟢' 
        };
      case 'connecting':
        return { 
          label: 'Connecting...', 
          className: 'status-connecting',
          icon: '🟡' 
        };
      case 'reconnecting':
        return { 
          label: `Reconnecting (${reconnectInfo?.attempt}/${reconnectInfo?.maxAttempts})...`, 
          className: 'status-reconnecting',
          icon: '🟠' 
        };
      case 'disconnected':
        return { 
          label: 'Disconnected', 
          className: 'status-disconnected',
          icon: '🔴' 
        };
      case 'error':
        return { 
          label: 'Connection Error', 
          className: 'status-error',
          icon: '❌' 
        };
      default:
        return { 
          label: 'Unknown', 
          className: 'status-unknown',
          icon: '⚪' 
        };
    }
  };

  const status = getStatusConfig();

  return (
    <div className={`connection-status ${status.className}`}>
      <span className="status-icon">{status.icon}</span>
      <span className="status-label">{status.label}</span>
    </div>
  );
};

export default ConnectionStatus;
```

## Minerva WebSocket Integration

### Overview

Minerva is the backend WebSocket server that powers real-time communication for FreedomCTI. It handles connection management, message routing, subscription management, and integration with telephony systems.

### Connection Configuration

```javascript
// src/config/minervaConfig.js

const MINERVA_ENDPOINTS = {
  development: 'wss://minerva-dev.freedomcti.local/ws',
  qa: 'wss://minerva-qa.freedomcti.com/ws',
  staging: 'wss://minerva-stage.freedomcti.com/ws',
  production: 'wss://minerva.freedomcti.com/ws'
};

export const getMinervaConfig = (environment) => {
  return {
    endpoint: MINERVA_ENDPOINTS[environment] || MINERVA_ENDPOINTS.development,
    options: {
      reconnectAttempts: environment === 'production' ? 15 : 5,
      heartbeatInterval: 30000,
      heartbeatTimeout: 10000,
      messageTimeout: 5000,
      compression: true,
      protocols: ['minerva-v2']
    },
    auth: {
      tokenRefreshThreshold: 300000,  // 5 minutes before expiry
      authEndpoint: '/api/auth/ws-token'
    }
  };
};
```

### Minerva Protocol Implementation

```javascript
// src/services/websocket/minervaProtocol.js

class MinervaProtocol {
  static VERSION = '2.0';
  
  /**
   * Create authentication handshake message
   */
  static createAuthMessage(credentials) {
    return {
      protocol: 'minerva',
      version: this.VERSION,
      type: 'AUTH',
      timestamp: Date.now(),
      payload: {
        token: credentials.accessToken,
        userId: credentials.userId,
        orgId: credentials.orgId,
        clientInfo: {
          platform: 'web',
          userAgent: navigator.userAgent,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }
      }
    };
  }

  /**
   * Parse incoming Minerva message
   */
  static parseMessage(rawMessage) {
    try {
      const message = JSON.parse(rawMessage);
      
      // Validate message structure
      if (!message.type || !message.timestamp) {
        throw new Error('Invalid message structure');
      }
      
      return {
        success: true,
        message
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        rawMessage
      };
    }
  }

  /**
   * Serialize outgoing message
   */
  static serializeMessage(message) {
    return JSON.stringify({
      ...message,
      protocol: 'minerva',
      version: this.VERSION
    });
  }
}
```

### Minerva Event Types

```javascript
// src/services/websocket/minervaEvents.js

/**
 * Minerva-specific event handlers
 */
export const MinervaEventHandlers = {
  /**
   * Handle Minerva system events
   */
  SYSTEM_MAINTENANCE: (store, message) => {
    store.dispatch({
      type: 'SYSTEM_MAINTENANCE_NOTICE',
      payload: {
        startTime: message.payload.startTime,
        endTime: message.payload.endTime,
        message: message.payload.message,
        severity: message.payload.severity
      }
    });
  },

  /**
   * Handle Minerva rate limiting
   */
  RATE_LIMITED: (store, message) => {
    console.warn('Rate limited by Minerva:', message.payload);
    store.dispatch({
      type: 'WEBSOCKET_RATE_LIMITED',
      payload: {
        retryAfter: message.payload.retryAfter,
        limit: message.payload.limit,
        current: message.payload.current
      }
    });
  },

  /**
   * Handle Minerva session events
   */
  SESSION_EXPIRED: (store, message) => {
    store.dispatch({ type: 'SESSION_EXPIRED' });
    // Trigger re-authentication
    store.dispatch({ type: 'AUTH_REFRESH_REQUIRED' });
  },

  /**
   * Handle Minerva subscription events
   */
  SUBSCRIPTION_ERROR: (store, message) => {
    store.dispatch({
      type: 'SUBSCRIPTION_FAILED',
      payload: {
        channel: message.payload.channel,
        reason: message.payload.reason,
        code: message.payload.code
      }
    });
  }
};
```

### Complete Integration Example

```javascript
// src/services/websocket/MinervaWebSocketClient.js

import { EventEmitter } from 'events';
import { getMinervaConfig } from '../../config/minervaConfig';
import { MinervaProtocol } from './minervaProtocol';
import { ReconnectionManager } from './reconnectionManager';
import { HeartbeatManager } from './heartbeat';
import { UserSubscriptionManager } from './subscriptions/userSubscription';
import { GroupSubscriptionManager } from './subscriptions/groupSubscription';

class MinervaWebSocketClient extends EventEmitter {
  constructor(environment, store) {
    super();
    this.config = getMinervaConfig(environment);
    this.store = store;
    this.socket = null;
    this.authenticated = false;
    
    this.reconnectionManager = new ReconnectionManager(this, this.config.options);
    this.heartbeatManager = new HeartbeatManager(this, {
      interval: this.config.options.heartbeatInterval,
      timeout: this.config.options.heartbeatTimeout
    });
    this.userSubscriptions = new UserSubscriptionManager(this);
    this.groupSubscriptions = new GroupSubscriptionManager(this);
  }

  async connect(credentials) {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(
        this.config.endpoint, 
        this.config.options.protocols
      );

      this.socket.onopen = async () => {
        try {
          await this.authenticate(credentials);
          this.heartbeatManager.start();
          this.emit('connected');
          resolve();
        } catch (authError) {
          reject(authError);
        }
      };

      this.socket.onclose = (event) => {
        this.heartbeatManager.stop();
        this.emit('disconnected', event);
        
        if (!event.wasClean) {
          this.reconnectionManager.scheduleReconnect();
        }
      };

      this.socket.onerror = (error) => {
        this.emit('error', error);
        reject(error);
      };

      this.socket.onmessage = (event) => {
        this.handleMessage(event.data);
      };
    });
  }

  async authenticate(credentials) {
    const authMessage = MinervaProtocol.createAuthMessage(credentials);
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Authentication timeout'));
      }, 10000);

      const handleAuthResponse = (response) => {
        if (response.type === 'AUTH_SUCCESS') {
          clearTimeout(timeout);
          this.authenticated = true;
          this.clientId = response.payload.clientId;
          resolve(response);
        } else if (response.type === 'AUTH_FAILURE') {
          clearTimeout(timeout);
          reject(new Error(response.payload.message));
        }
      };

      this.once('auth_response', handleAuthResponse);
      this.send(authMessage);
    });
  }

  handleMessage(rawMessage) {
    const { success, message, error } = MinervaProtocol.parseMessage(rawMessage);
    
    if (!success) {
      console.error('Failed to parse message:', error);
      return;
    }

    // Handle authentication responses
    if (message.type === 'AUTH_SUCCESS' || message.type === 'AUTH_FAILURE') {
      this.emit('auth_response', message);
      return;
    }

    // Handle heartbeat responses
    if (message.type === 'HEARTBEAT_ACK') {
      this.heartbeatManager.handleHeartbeatResponse(message.payload);
      return;
    }

    // Emit message for handlers
    this.emit('message', message);
    this.emit(message.type, message);
  }

  send(message) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      const serialized = MinervaProtocol.serializeMessage(message);
      this.socket.send(serialized);
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }

  disconnect() {
    this.reconnectionManager.cancel();
    this.heartbeatManager.stop();
    
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    
    this.authenticated = false;
    this.emit('disconnected', { wasClean: true });
  }
}

export default MinervaWebSocketClient;
```

## Best Practices

### 1. Message Handling

- Always validate incoming message structure before processing
- Use message correlation IDs for request-response patterns
- Implement message deduplication for critical events
- Handle out-of-order messages gracefully

### 2. Connection Management

- Implement proper cleanup in component unmount
- Use visibility API to pause/resume connections
- Monitor connection health with heartbeats
- Implement graceful degradation when disconnected

### 3. State Synchronization

- Queue actions during disconnection for replay
- Implement optimistic updates with rollback
- Use sequence numbers to detect missed messages
- Periodically reconcile client state with server

### 4. Performance

- Batch non-critical messages when possible
- Implement message compression for large payloads
- Use binary protocols for high-frequency data
- Throttle UI updates for rapidly changing data

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Frequent disconnections | Network instability | Increase heartbeat timeout, implement connection quality monitoring |
| Messages not received | Subscription not confirmed | Wait for subscription confirmation before expecting events |
| High latency | Server overload | Implement message prioritization, reduce subscription scope |
| Authentication failures | Token expired | Implement proactive token refresh |
| Memory leaks | Uncleared event handlers | Always remove listeners on cleanup |

### Debug Mode

```javascript
// Enable WebSocket debugging
localStorage.setItem('WS_DEBUG', 'true');

// Debug utility
const wsDebug = {
  logMessage: (direction, message) => {
    if (localStorage.getItem('WS_DEBUG') === 'true') {
      console.log(`[WS ${direction}]`, new Date().toISOString(), message);
    }
  }
};
```

---

*Last Updated: 2024*
*Version: 2.0*
*Maintainer: FreedomCTI Platform Team*