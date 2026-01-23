# Application Architecture

## Overview

FreedomCTI is a sophisticated browser-based Computer Telephony Integration (CTI) client designed to operate as an embedded iframe within Salesforce Lightning. This document provides a comprehensive exploration of the application's architecture, including the React component hierarchy, Redux state management patterns, middleware implementations, and the hybrid build system that supports both legacy and modern code paths.

Understanding this architecture is essential for developers working on feature development, debugging integration issues, or optimizing performance within the Salesforce iframe context.

---

## Project Structure

The FreedomCTI application follows a modular project structure that separates concerns across multiple directories while maintaining clear boundaries between legacy code and modern React/Redux implementations.

### Root Directory Layout

```
platform-cti-client/
├── src/
│   ├── components/           # React UI components
│   │   ├── common/          # Shared/reusable components
│   │   ├── call/            # Call management components
│   │   ├── voicemail/       # Voicemail handling components
│   │   └── layout/          # Layout and container components
│   ├── containers/          # Redux-connected containers
│   ├── store/               # Redux store configuration
│   │   ├── actions/         # Action creators
│   │   ├── reducers/        # State reducers
│   │   ├── middleware/      # Custom middleware
│   │   └── selectors/       # Memoized selectors
│   ├── services/            # API and WebSocket services
│   ├── utils/               # Utility functions and helpers
│   ├── legacy/              # Legacy non-React code
│   └── config/              # Environment configurations
├── cypress/                  # E2E test suites
│   ├── integration/         # Test specifications
│   ├── fixtures/            # Test data
│   └── support/             # Custom commands
├── grunt/                    # Grunt task configurations
├── webpack/                  # Webpack configurations
├── dist/                     # Build output
└── public/                   # Static assets
```

### Key Directory Responsibilities

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `src/components/` | Presentational React components | `CallPanel.jsx`, `VoicemailList.jsx` |
| `src/containers/` | Redux-connected smart components | `CallPanelContainer.jsx` |
| `src/store/` | State management infrastructure | `configureStore.js`, `rootReducer.js` |
| `src/services/` | External communication layer | `WebSocketService.js`, `SalesforceAPI.js` |
| `src/legacy/` | Pre-React code maintained for compatibility | `softphone.js`, `legacyHandlers.js` |

---

## React Application Layout

### Component Hierarchy

The application follows a hierarchical component structure designed to maximize reusability while maintaining clear data flow patterns.

```
<App>
├── <SalesforceProvider>
│   ├── <WebSocketProvider>
│   │   ├── <Layout>
│   │   │   ├── <Header>
│   │   │   │   ├── <AgentStatus />
│   │   │   │   ├── <ConnectionIndicator />
│   │   │   │   └── <SettingsMenu />
│   │   │   ├── <MainContent>
│   │   │   │   ├── <CallPanel>
│   │   │   │   │   ├── <ActiveCall />
│   │   │   │   │   ├── <Dialpad />
│   │   │   │   │   ├── <CallControls />
│   │   │   │   │   └── <CallTimer />
│   │   │   │   ├── <CallHistory />
│   │   │   │   └── <VoicemailPanel>
│   │   │   │       ├── <VoicemailList />
│   │   │   │       └── <VoicemailPlayer />
│   │   │   └── <Footer>
│   │   │       └── <QuickActions />
```

### Context Providers

The application utilizes React Context for cross-cutting concerns that need to be accessible throughout the component tree:

```javascript
// src/context/SalesforceContext.js
import React, { createContext, useContext, useEffect, useState } from 'react';

const SalesforceContext = createContext(null);

export const SalesforceProvider = ({ children }) => {
  const [sfApi, setSfApi] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionInfo, setSessionInfo] = useState(null);

  useEffect(() => {
    // Initialize Salesforce OpenCTI integration
    const initializeSalesforce = async () => {
      if (window.sforce && window.sforce.opencti) {
        try {
          const api = window.sforce.opencti;
          await api.enableClickToDial({ callback: handleClickToDial });
          
          const session = await new Promise((resolve) => {
            api.getCallCenterSettings({
              callback: (result) => resolve(result)
            });
          });
          
          setSfApi(api);
          setSessionInfo(session);
          setIsConnected(true);
        } catch (error) {
          console.error('Salesforce initialization failed:', error);
        }
      }
    };

    initializeSalesforce();
  }, []);

  return (
    <SalesforceContext.Provider value={{ sfApi, isConnected, sessionInfo }}>
      {children}
    </SalesforceContext.Provider>
  );
};

export const useSalesforce = () => useContext(SalesforceContext);
```

### Component Design Patterns

#### Presentational Components

Presentational components focus solely on rendering UI based on props:

```javascript
// src/components/call/CallControls.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonGroup } from '../common';

const CallControls = ({
  isOnCall,
  isMuted,
  isOnHold,
  onAnswer,
  onHangup,
  onMute,
  onHold,
  onTransfer,
  disabled
}) => {
  return (
    <div className="call-controls">
      <ButtonGroup>
        {!isOnCall && (
          <Button
            icon="phone"
            variant="success"
            onClick={onAnswer}
            disabled={disabled}
            aria-label="Answer call"
          />
        )}
        {isOnCall && (
          <>
            <Button
              icon={isMuted ? 'microphone-slash' : 'microphone'}
              variant={isMuted ? 'warning' : 'default'}
              onClick={onMute}
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            />
            <Button
              icon="pause"
              variant={isOnHold ? 'warning' : 'default'}
              onClick={onHold}
              aria-label={isOnHold ? 'Resume' : 'Hold'}
            />
            <Button
              icon="exchange"
              onClick={onTransfer}
              aria-label="Transfer call"
            />
            <Button
              icon="phone-slash"
              variant="danger"
              onClick={onHangup}
              aria-label="End call"
            />
          </>
        )}
      </ButtonGroup>
    </div>
  );
};

CallControls.propTypes = {
  isOnCall: PropTypes.bool.isRequired,
  isMuted: PropTypes.bool,
  isOnHold: PropTypes.bool,
  onAnswer: PropTypes.func.isRequired,
  onHangup: PropTypes.func.isRequired,
  onMute: PropTypes.func.isRequired,
  onHold: PropTypes.func.isRequired,
  onTransfer: PropTypes.func.isRequired,
  disabled: PropTypes.bool
};

export default CallControls;
```

#### Container Components

Containers connect presentational components to the Redux store:

```javascript
// src/containers/CallControlsContainer.jsx
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import CallControls from '../components/call/CallControls';
import {
  answerCall,
  hangupCall,
  toggleMute,
  toggleHold,
  initiateTransfer
} from '../store/actions/callActions';
import {
  selectIsOnCall,
  selectIsMuted,
  selectIsOnHold,
  selectCallControlsDisabled
} from '../store/selectors/callSelectors';

const mapStateToProps = (state) => ({
  isOnCall: selectIsOnCall(state),
  isMuted: selectIsMuted(state),
  isOnHold: selectIsOnHold(state),
  disabled: selectCallControlsDisabled(state)
});

const mapDispatchToProps = (dispatch) => ({
  onAnswer: bindActionCreators(answerCall, dispatch),
  onHangup: bindActionCreators(hangupCall, dispatch),
  onMute: bindActionCreators(toggleMute, dispatch),
  onHold: bindActionCreators(toggleHold, dispatch),
  onTransfer: bindActionCreators(initiateTransfer, dispatch)
});

export default connect(mapStateToProps, mapDispatchToProps)(CallControls);
```

---

## Redux Store Architecture

### Store Configuration

The Redux store is configured with middleware for handling asynchronous operations, WebSocket communication, and development debugging:

```javascript
// src/store/configureStore.js
import { createStore, applyMiddleware, compose } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from './reducers';
import { websocketMiddleware } from './middleware/websocketMiddleware';
import { salesforceMiddleware } from './middleware/salesforceMiddleware';
import { callLoggingMiddleware } from './middleware/callLoggingMiddleware';
import { analyticsMiddleware } from './middleware/analyticsMiddleware';

const configureStore = (preloadedState = {}) => {
  const middlewares = [
    thunk,
    websocketMiddleware,
    salesforceMiddleware,
    callLoggingMiddleware,
    analyticsMiddleware
  ];

  // Enable Redux DevTools in development
  const composeEnhancers =
    (process.env.NODE_ENV === 'development' &&
      window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) ||
    compose;

  const store = createStore(
    rootReducer,
    preloadedState,
    composeEnhancers(applyMiddleware(...middlewares))
  );

  // Hot module replacement for reducers
  if (process.env.NODE_ENV === 'development' && module.hot) {
    module.hot.accept('./reducers', () => {
      store.replaceReducer(rootReducer);
    });
  }

  return store;
};

export default configureStore;
```

### State Shape

The application state is organized into logical domains:

```javascript
// State shape visualization
{
  auth: {
    isAuthenticated: boolean,
    user: {
      id: string,
      name: string,
      extension: string,
      permissions: string[]
    },
    token: string,
    expiresAt: number
  },
  
  call: {
    activeCall: {
      id: string,
      direction: 'inbound' | 'outbound',
      state: 'ringing' | 'connected' | 'hold' | 'ended',
      phoneNumber: string,
      startTime: number,
      duration: number,
      isMuted: boolean,
      isOnHold: boolean,
      recordingEnabled: boolean
    },
    callHistory: [
      {
        id: string,
        direction: string,
        phoneNumber: string,
        duration: number,
        timestamp: number,
        disposition: string,
        salesforceRecordId: string
      }
    ],
    pendingCalls: []
  },
  
  voicemail: {
    messages: [],
    selectedMessage: null,
    isLoading: boolean,
    playbackState: {
      isPlaying: boolean,
      currentTime: number,
      duration: number
    }
  },
  
  connection: {
    websocket: {
      status: 'disconnected' | 'connecting' | 'connected' | 'error',
      lastHeartbeat: number,
      reconnectAttempts: number
    },
    salesforce: {
      status: 'disconnected' | 'connected' | 'error',
      callCenterSettings: object
    }
  },
  
  ui: {
    activeTab: 'dialpad' | 'history' | 'voicemail',
    notifications: [],
    modals: {
      transfer: { isOpen: boolean, data: object },
      settings: { isOpen: boolean }
    },
    isCompactMode: boolean
  }
}
```

### Reducers

Reducers are organized by domain and combined using `combineReducers`:

```javascript
// src/store/reducers/callReducer.js
import {
  CALL_INCOMING,
  CALL_ANSWERED,
  CALL_ENDED,
  CALL_MUTE_TOGGLED,
  CALL_HOLD_TOGGLED,
  CALL_HISTORY_LOADED,
  CALL_LOG_SAVED
} from '../actions/types';

const initialState = {
  activeCall: null,
  callHistory: [],
  pendingCalls: [],
  isLoading: false,
  error: null
};

const callReducer = (state = initialState, action) => {
  switch (action.type) {
    case CALL_INCOMING:
      return {
        ...state,
        activeCall: {
          id: action.payload.callId,
          direction: 'inbound',
          state: 'ringing',
          phoneNumber: action.payload.callerNumber,
          callerName: action.payload.callerName,
          startTime: Date.now(),
          duration: 0,
          isMuted: false,
          isOnHold: false
        }
      };

    case CALL_ANSWERED:
      return {
        ...state,
        activeCall: state.activeCall
          ? {
              ...state.activeCall,
              state: 'connected',
              answeredAt: Date.now()
            }
          : null
      };

    case CALL_ENDED:
      const endedCall = state.activeCall
        ? {
            ...state.activeCall,
            state: 'ended',
            endTime: Date.now(),
            duration: Date.now() - (state.activeCall.answeredAt || state.activeCall.startTime)
          }
        : null;

      return {
        ...state,
        activeCall: null,
        callHistory: endedCall
          ? [endedCall, ...state.callHistory.slice(0, 99)]
          : state.callHistory
      };

    case CALL_MUTE_TOGGLED:
      return {
        ...state,
        activeCall: state.activeCall
          ? { ...state.activeCall, isMuted: !state.activeCall.isMuted }
          : null
      };

    case CALL_HOLD_TOGGLED:
      return {
        ...state,
        activeCall: state.activeCall
          ? { 
              ...state.activeCall, 
              isOnHold: !state.activeCall.isOnHold,
              state: state.activeCall.isOnHold ? 'connected' : 'hold'
            }
          : null
      };

    case CALL_HISTORY_LOADED:
      return {
        ...state,
        callHistory: action.payload,
        isLoading: false
      };

    default:
      return state;
  }
};

export default callReducer;
```

### Selectors

Memoized selectors optimize re-rendering and encapsulate state access patterns:

```javascript
// src/store/selectors/callSelectors.js
import { createSelector } from 'reselect';

// Base selectors
const selectCallState = (state) => state.call;
const selectActiveCall = (state) => state.call.activeCall;

// Derived selectors
export const selectIsOnCall = createSelector(
  [selectActiveCall],
  (activeCall) => activeCall !== null && activeCall.state !== 'ended'
);

export const selectIsMuted = createSelector(
  [selectActiveCall],
  (activeCall) => activeCall?.isMuted ?? false
);

export const selectIsOnHold = createSelector(
  [selectActiveCall],
  (activeCall) => activeCall?.isOnHold ?? false
);

export const selectCallDuration = createSelector(
  [selectActiveCall],
  (activeCall) => {
    if (!activeCall || !activeCall.answeredAt) return 0;
    return Date.now() - activeCall.answeredAt;
  }
);

export const selectCallControlsDisabled = createSelector(
  [selectActiveCall, (state) => state.connection.websocket.status],
  (activeCall, wsStatus) => {
    return wsStatus !== 'connected' || 
           (activeCall && activeCall.state === 'ringing');
  }
);

export const selectRecentCalls = createSelector(
  [selectCallState],
  (callState) => callState.callHistory.slice(0, 10)
);

export const selectCallsByDirection = createSelector(
  [selectCallState, (_, direction) => direction],
  (callState, direction) => 
    callState.callHistory.filter(call => call.direction === direction)
);
```

---

## Middleware Overview

### WebSocket Middleware

The WebSocket middleware manages the real-time connection for call events, ensuring reliable message delivery and automatic reconnection:

```javascript
// src/store/middleware/websocketMiddleware.js
import {
  WS_CONNECT,
  WS_DISCONNECT,
  WS_SEND_MESSAGE,
  WS_CONNECTED,
  WS_DISCONNECTED,
  WS_ERROR,
  WS_MESSAGE_RECEIVED
} from '../actions/types';
import { getWebSocketUrl } from '../../config/environment';

const createWebSocketMiddleware = () => {
  let socket = null;
  let reconnectTimer = null;
  let heartbeatTimer = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY_BASE = 1000;
  const HEARTBEAT_INTERVAL = 30000;

  return (store) => (next) => (action) => {
    switch (action.type) {
      case WS_CONNECT:
        if (socket !== null) {
          socket.close();
        }

        const wsUrl = getWebSocketUrl(action.payload.environment);
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          reconnectAttempts = 0;
          store.dispatch({ type: WS_CONNECTED });
          
          // Authenticate on connection
          socket.send(JSON.stringify({
            type: 'authenticate',
            token: store.getState().auth.token
          }));

          // Start heartbeat
          heartbeatTimer = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ type: 'heartbeat' }));
            }
          }, HEARTBEAT_INTERVAL);
        };

        socket.onclose = (event) => {
          clearInterval(heartbeatTimer);
          store.dispatch({ 
            type: WS_DISCONNECTED, 
            payload: { code: event.code, reason: event.reason }
          });

          // Attempt reconnection
          if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && !event.wasClean) {
            const delay = RECONNECT_DELAY_BASE * Math.pow(2, reconnectAttempts);
            reconnectTimer = setTimeout(() => {
              reconnectAttempts++;
              store.dispatch({ type: WS_CONNECT, payload: action.payload });
            }, delay);
          }
        };

        socket.onerror = (error) => {
          store.dispatch({ 
            type: WS_ERROR, 
            payload: { message: 'WebSocket error occurred' }
          });
        };

        socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            store.dispatch({ 
              type: WS_MESSAGE_RECEIVED, 
              payload: message 
            });

            // Dispatch specific actions based on message type
            handleWebSocketMessage(store, message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        break;

      case WS_DISCONNECT:
        clearTimeout(reconnectTimer);
        clearInterval(heartbeatTimer);
        if (socket !== null) {
          socket.close(1000, 'Client disconnecting');
          socket = null;
        }
        break;

      case WS_SEND_MESSAGE:
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify(action.payload));
        } else {
          console.warn('WebSocket not connected, message not sent:', action.payload);
        }
        break;
    }

    return next(action);
  };
};

const handleWebSocketMessage = (store, message) => {
  const messageHandlers = {
    'call.incoming': () => store.dispatch({ 
      type: 'CALL_INCOMING', 
      payload: message.data 
    }),
    'call.answered': () => store.dispatch({ 
      type: 'CALL_ANSWERED', 
      payload: message.data 
    }),
    'call.ended': () => store.dispatch({ 
      type: 'CALL_ENDED', 
      payload: message.data 
    }),
    'agent.status_changed': () => store.dispatch({ 
      type: 'AGENT_STATUS_UPDATED', 
      payload: message.data 
    }),
    'voicemail.new': () => store.dispatch({ 
      type: 'VOICEMAIL_RECEIVED', 
      payload: message.data 
    })
  };

  const handler = messageHandlers[message.type];
  if (handler) {
    handler();
  }
};

export const websocketMiddleware = createWebSocketMiddleware();
```

### Salesforce Middleware

This middleware handles bidirectional communication with the Salesforce Lightning container:

```javascript
// src/store/middleware/salesforceMiddleware.js
import {
  SF_SCREEN_POP,
  SF_SAVE_LOG,
  SF_UPDATE_SOFTPHONE_PANEL,
  CALL_ENDED,
  CALL_LOG_SAVED
} from '../actions/types';

export const salesforceMiddleware = (store) => (next) => (action) => {
  const result = next(action);
  const sfApi = window.sforce?.opencti;

  if (!sfApi) {
    console.warn('Salesforce OpenCTI not available');
    return result;
  }

  switch (action.type) {
    case SF_SCREEN_POP:
      sfApi.screenPop({
        type: action.payload.type,
        params: action.payload.params,
        callback: (response) => {
          if (!response.success) {
            console.error('Screen pop failed:', response.errors);
          }
        }
      });
      break;

    case CALL_ENDED:
      // Automatically trigger call log creation
      const call = store.getState().call.callHistory[0];
      if (call && call.salesforceRecordId) {
        sfApi.saveLog({
          value: {
            Subject: `${call.direction} Call - ${call.phoneNumber}`,
            Description: `Duration: ${formatDuration(call.duration)}`,
            CallDurationInSeconds: Math.floor(call.duration / 1000),
            CallType: call.direction === 'inbound' ? 'Inbound' : 'Outbound',
            Status: 'Completed'
          },
          entityApiName: 'Task',
          callback: (response) => {
            if (response.success) {
              store.dispatch({
                type: CALL_LOG_SAVED,
                payload: { callId: call.id, taskId: response.returnValue.recordId }
              });
            }
          }
        });
      }
      break;

    case SF_UPDATE_SOFTPHONE_PANEL:
      sfApi.setSoftphonePanelVisibility({
        visible: action.payload.visible,
        callback: (response) => {
          if (!response.success) {
            console.error('Panel visibility update failed:', response.errors);
          }
        }
      });
      break;
  }

  return result;
};

const formatDuration = (ms) => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};
```

### Call Logging Middleware

Handles automatic call activity logging to the backend API:

```javascript
// src/store/middleware/callLoggingMiddleware.js
import { CALL_ENDED, CALL_LOG_SUBMITTED, CALL_LOG_FAILED } from '../actions/types';
import { apiClient } from '../../services/apiClient';

export const callLoggingMiddleware = (store) => (next) => async (action) => {
  const result = next(action);

  if (action.type === CALL_ENDED) {
    const state = store.getState();
    const completedCall = state.call.callHistory[0];

    if (completedCall) {
      try {
        const logData = {
          callId: completedCall.id,
          direction: completedCall.direction,
          phoneNumber: completedCall.phoneNumber,
          startTime: new Date(completedCall.startTime).toISOString(),
          endTime: new Date(completedCall.endTime).toISOString(),
          duration: completedCall.duration,
          agentId: state.auth.user.id,
          disposition: completedCall.disposition || 'completed'
        };

        await apiClient.post('/api/calls/log', logData);
        
        store.dispatch({
          type: CALL_LOG_SUBMITTED,
          payload: { callId: completedCall.id }
        });
      } catch (error) {
        store.dispatch({
          type: CALL_LOG_FAILED,
          payload: { 
            callId: completedCall.id, 
            error: error.message 
          }
        });
      }
    }
  }

  return result;
};
```

---

## Build System (Grunt/Webpack)

FreedomCTI uses a hybrid build system combining Grunt for task automation and Webpack for module bundling. This architecture supports both legacy code paths and modern React development.

### Webpack Configuration

```javascript
// webpack/webpack.config.js
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { DefinePlugin } = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  
  entry: {
    main: './src/index.js',
    legacy: './src/legacy/index.js'
  },
  
  output: {
    path: path.resolve(__dirname, '../dist'),
    filename: isProduction 
      ? '[name].[contenthash].js' 
      : '[name].bundle.js',
    publicPath: '/',
    clean: true
  },
  
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', { targets: { browsers: ['last 2 versions'] } }],
              '@babel/preset-react'
            ],
            plugins: [
              '@babel/plugin-proposal-class-properties',
              '@babel/plugin-transform-runtime'
            ]
          }
        }
      },
      {
        test: /\.css$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          'css-loader',
          'postcss-loader'
        ]
      },
      {
        test: /\.scss$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          'css-loader',
          'postcss-loader',
          'sass-loader'
        ]
      },
      {
        test: /\.(png|jpg|gif|svg)$/,
        type: 'asset/resource',
        generator: {
          filename: 'images/[name].[hash][ext]'
        }
      }
    ]
  },
  
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
      inject: true,
      chunks: ['main']
    }),
    new DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
      'process.env.API_BASE_URL': JSON.stringify(process.env.API_BASE_URL),
      'process.env.WS_URL': JSON.stringify(process.env.WS_URL)
    }),
    ...(isProduction ? [
      new MiniCssExtractPlugin({
        filename: '[name].[contenthash].css'
      })
    ] : [])
  ],
  
  optimization: {
    minimize: isProduction,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: isProduction
          }
        }
      })
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    }
  },
  
  devServer: {
    port: 3000,
    hot: true,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  },
  
  resolve: {
    extensions: ['.js', '.jsx', '.json'],
    alias: {
      '@components': path.resolve(__dirname, '../src/components'),
      '@containers': path.resolve(__dirname, '../src/containers'),
      '@store': path.resolve(__dirname, '../src/store'),
      '@services': path.resolve(__dirname, '../src/services'),
      '@utils': path.resolve(__dirname, '../src/utils')
    }
  },
  
  devtool: isProduction ? 'source-map' : 'eval-cheap-module-source-map'
};
```

### Grunt Configuration

```javascript
// Gruntfile.js
module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    
    // Clean build directories
    clean: {
      dist: ['dist/*'],
      temp: ['.tmp/*']
    },
    
    // Copy static assets
    copy: {
      static: {
        files: [{
          expand: true,
          cwd: 'public',
          src: ['**/*', '!index.html'],
          dest: 'dist/'
        }]
      },
      legacy: {
        files: [{
          expand: true,
          cwd: 'src/legacy/assets',
          src: ['**/*'],
          dest: 'dist/legacy/'
        }]
      }
    },
    
    // SASS compilation for legacy styles
    sass: {
      options: {
        implementation: require('sass')
      },
      legacy: {
        files: [{
          expand: true,
          cwd: 'src/legacy/styles',
          src: ['*.scss'],
          dest: '.tmp/css',
          ext: '.css'
        }]
      }
    },
    
    // CSS minification
    cssmin: {
      legacy: {
        files: [{
          expand: true,
          cwd: '.tmp/css',
          src: ['*.css'],
          dest: 'dist/css',
          ext: '.min.css'
        }]
      }
    },
    
    // JavaScript concatenation for legacy files
    concat: {
      legacy: {
        src: [
          'src/legacy/vendor/*.js',
          'src/legacy/lib/*.js',
          'src/legacy/modules/*.js'
        ],
        dest: '.tmp/js/legacy-bundle.js'
      }
    },
    
    // JavaScript minification
    uglify: {
      options: {
        mangle: true,
        compress: true
      },
      legacy: {
        files: {
          'dist/js/legacy-bundle.min.js': ['.tmp/js/legacy-bundle.js']
        }
      }
    },
    
    // Watch for changes
    watch: {
      legacy: {
        files: ['src/legacy/**/*'],
        tasks: ['build:legacy']
      }
    },
    
    // Environment configuration
    ngconstant: {
      options: {
        name: 'config',
        dest: 'src/config/generated.js'
      },
      dev: {
        constants: {
          ENV: {
            name: 'development',
            apiUrl: 'http://localhost:8080/api',
            wsUrl: 'ws://localhost:8080/ws'
          }
        }
      },
      qa: {
        constants: {
          ENV: {
            name: 'qa',
            apiUrl: 'https://qa-api.freedomcti.com/api',
            wsUrl: 'wss://qa-api.freedomcti.com/ws'
          }
        }
      },
      stage: {
        constants: {
          ENV: {
            name: 'stage',
            apiUrl: 'https://stage-api.freedomcti.com/api',
            wsUrl: 'wss://stage-api.freedomcti.com/ws'
          }
        }
      },
      prod: {
        constants: {
          ENV: {
            name: 'production',
            apiUrl: 'https://api.freedomcti.com/api',
            wsUrl: 'wss://api.freedomcti.com/ws'
          }
        }
      }
    }
  });

  // Load plugins
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-ng-constant');

  // Task definitions
  grunt.registerTask('build:legacy', [
    'sass:legacy',
    'cssmin:legacy',
    'concat:legacy',
    'uglify:legacy',
    'copy:legacy'
  ]);

  grunt.registerTask('build:dev', ['ngconstant:dev', 'clean', 'copy:static', 'build:legacy']);
  grunt.registerTask('build:qa', ['ngconstant:qa', 'clean', 'copy:static', 'build:legacy']);
  grunt.registerTask('build:stage', ['ngconstant:stage', 'clean', 'copy:static', 'build:legacy']);
  grunt.registerTask('build:prod', ['ngconstant:prod', 'clean', 'copy:static', 'build:legacy']);
  
  grunt.registerTask('default', ['build:dev']);
};
```

### Build Scripts

The `package.json` defines convenient npm scripts for different build scenarios:

```json
{
  "scripts": {
    "start": "webpack serve --config webpack/webpack.config.js",
    "build": "npm run build:prod",
    "build:dev": "grunt build:dev && webpack --config webpack/webpack.config.js --mode development",
    "build:qa": "grunt build:qa && webpack --config webpack/webpack.config.js --mode production",
    "build:stage": "grunt build:stage && webpack --config webpack/webpack.config.js --mode production",
    "build:prod": "grunt build:prod && webpack --config webpack/webpack.config.js --mode production",
    "test": "jest",
    "test:e2e": "cypress run",
    "test:e2e:open": "cypress open",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix"
  }
}
```

---

## Legacy vs Modern Components

### Architecture Comparison

FreedomCTI maintains both legacy and modern code paths to ensure backward compatibility while enabling progressive modernization.

| Aspect | Legacy Components | Modern Components |
|--------|------------------|-------------------|
| **Framework** | Vanilla JS / jQuery | React 17+ |
| **State Management** | Global objects / Events | Redux |
| **Styling** | SCSS with BEM naming | CSS Modules / Styled Components |
| **Data Fetching** | XMLHttpRequest / jQuery AJAX | Axios / Fetch API |
| **Build** | Grunt concatenation | Webpack bundling |
| **Testing** | Manual / Limited unit tests | Jest + React Testing Library |

### Legacy Code Structure

```javascript
// src/legacy/modules/softphone.js
(function(window, $) {
  'use strict';

  var Softphone = {
    config: null,
    currentCall: null,
    eventHandlers: {},

    init: function(options) {
      this.config = $.extend({}, this.defaults, options);
      this.bindEvents();
      this.initializeUI();
      return this;
    },

    defaults: {
      container: '#softphone-container',
      apiEndpoint: '/api/v1',
      debug: false
    },

    bindEvents: function() {
      var self = this;
      
      $(document).on('click', '.dial-button', function() {
        var number = $('#dial-input').val();
        self.dial(number);
      });

      $(document).on('click', '.hangup-button', function() {
        self.hangup();
      });

      // Listen for events from modern components
      window.addEventListener('cti:dial', function(event) {
        self.dial(event.detail.number);
      });
    },

    dial: function(number) {
      var self = this;
      
      $.ajax({
        url: this.config.apiEndpoint + '/calls/dial',
        method: 'POST',
        data: JSON.stringify({ number: number }),
        contentType: 'application/json',
        success: function(response) {
          self.currentCall = response.call;
          self.trigger('call:started', response.call);
        },
        error: function(xhr) {
          self.trigger('call:error', xhr.responseJSON);
        }
      });
    },

    hangup: function() {
      // Implementation
    },

    on: function(event, handler) {
      if (!this.eventHandlers[event]) {
        this.eventHandlers[event] = [];
      }
      this.eventHandlers[event].push(handler);
    },

    trigger: function(event, data) {
      var handlers = this.eventHandlers[event] || [];
      handlers.forEach(function(handler) {
        handler(data);
      });
      
      // Also dispatch DOM event for modern component interop
      window.dispatchEvent(new CustomEvent('cti:' + event.replace(':', '_'), {
        detail: data
      }));
    }
  };

  window.FreedomCTI = window.FreedomCTI || {};
  window.FreedomCTI.Softphone = Softphone;

})(window, jQuery);
```

### Bridge Layer

The bridge layer enables communication between legacy and modern components:

```javascript
// src/services/legacyBridge.js
import store from '../store';
import { legacyCallStarted, legacyCallEnded } from '../store/actions/legacyActions';

class LegacyBridge {
  constructor() {
    this.isInitialized = false;
  }

  initialize() {
    if (this.isInitialized) return;

    // Listen for legacy events
    window.addEventListener('cti:call_started', this.handleLegacyCallStarted.bind(this));
    window.addEventListener('cti:call_ended', this.handleLegacyCallEnded.bind(this));

    // Expose methods for legacy code to call
    window.FreedomCTI = window.FreedomCTI || {};
    window.FreedomCTI.modernAPI = {
      getState: () => store.getState(),
      dispatch: (action) => store.dispatch(action),
      subscribe: (listener) => store.subscribe(listener)
    };

    // Subscribe to Redux state changes for legacy updates
    store.subscribe(this.syncToLegacy.bind(this));

    this.isInitialized = true;
  }

  handleLegacyCallStarted(event) {
    store.dispatch(legacyCallStarted(event.detail));
  }

  handleLegacyCallEnded(event) {
    store.dispatch(legacyCallEnded(event.detail));
  }

  syncToLegacy() {
    const state = store.getState();
    
    // Update legacy UI components
    if (window.FreedomCTI?.Softphone?.updateFromState) {
      window.FreedomCTI.Softphone.updateFromState({
        isOnCall: state.call.activeCall !== null,
        callDuration: state.call.activeCall?.duration || 0
      });
    }
  }

  // Call from modern components to trigger legacy functionality
  triggerLegacy(event, data) {
    window.dispatchEvent(new CustomEvent(`cti:${event}`, { detail: data }));
  }
}

export const legacyBridge = new LegacyBridge();
export default legacyBridge;
```

### Migration Strategy

When migrating legacy components to modern React:

1. **Identify Dependencies**: Map all dependencies and event listeners
2. **Create React Wrapper**: Build a React component that wraps legacy functionality
3. **Implement Bridge Events**: Use the bridge layer for communication
4. **Gradual Replacement**: Replace DOM manipulation with React state
5. **Remove Legacy Code**: Once fully migrated, remove the legacy module

```javascript
// Example: Migrating legacy DialPad to React
// src/components/call/DialPad.jsx
import React, { useState, useCallback, useEffect } from 'react';
import { legacyBridge } from '../../services/legacyBridge';

const DialPad = ({ onDial, disabled }) => {
  const [number, setNumber] = useState('');

  // Support legacy dial events during migration
  useEffect(() => {
    const handleLegacyDial = (event) => {
      if (event.detail?.number) {
        setNumber(event.detail.number);
        onDial(event.detail.number);
      }
    };

    window.addEventListener('cti:legacy_dial', handleLegacyDial);
    return () => window.removeEventListener('cti:legacy_dial', handleLegacyDial);
  }, [onDial]);

  const handleKeyPress = useCallback((key) => {
    if (key === 'backspace') {
      setNumber(prev => prev.slice(0, -1));
    } else if (key === 'call') {
      onDial(number);
      // Notify legacy components
      legacyBridge.triggerLegacy('dial_initiated', { number });
    } else {
      setNumber(prev => prev + key);
    }
  }, [number, onDial]);

  const keys = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#']
  ];

  return (
    <div className="dial-pad">
      <input
        type="tel"
        value={number}
        onChange={(e) => setNumber(e.target.value)}
        placeholder="Enter phone number"
        disabled={disabled}
      />
      <div className="dial-pad__keys">
        {keys.map((row, i) => (
          <div key={i} className="dial-pad__row">
            {row.map(key => (
              <button
                key={key}
                className="dial-pad__key"
                onClick={() => handleKeyPress(key)}
                disabled={disabled}
              >
                {key}
              </button>
            ))}
          </div>
        ))}
      </div>
      <div className="dial-pad__actions">
        <button
          className="dial-pad__backspace"
          onClick={() => handleKeyPress('backspace')}
          disabled={disabled || !number}
        >
          ⌫
        </button>
        <button
          className="dial-pad__call"
          onClick={() => handleKeyPress('call')}
          disabled={disabled || !number}
        >
          📞 Call
        </button>
      </div>
    </div>
  );
};

export default DialPad;
```

---

## Best Practices and Guidelines

### Component Development

1. **Keep components focused**: Each component should have a single responsibility
2. **Use TypeScript for new components**: Gradually migrate to TypeScript for better type safety
3. **Implement error boundaries**: Wrap major sections in error boundaries
4. **Optimize renders**: Use `React.memo`, `useMemo`, and `useCallback` appropriately

### State Management

1. **Normalize state shape**: Keep state flat and use IDs for references
2. **Use selectors everywhere**: Never access state directly in components
3. **Keep actions simple**: Complex logic belongs in middleware or thunks
4. **Document state changes**: Use descriptive action types

### Performance Considerations

1. **Lazy load routes**: Use `React.lazy` for code splitting
2. **Virtualize long lists**: Use react-window for call history
3. **Debounce WebSocket updates**: Batch rapid state changes
4. **Monitor bundle size**: Regularly analyze with webpack-bundle-analyzer

---

## Related Documentation

- [API Reference](./api-reference.md) - Backend API endpoints
- [WebSocket Events](./websocket-events.md) - Real-time event documentation
- [Testing Guide](./testing.md) - Unit and E2E testing strategies
- [Deployment Guide](./deployment.md) - Environment-specific deployment procedures