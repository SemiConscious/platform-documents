# State Management

## Overview

This document provides comprehensive documentation for the Redux state management implementation in the Freedom Web application. The state management layer serves as the single source of truth for all application data, handling everything from authentication state to active call management, voicemail operations, and Salesforce (SF) integration.

Freedom Web utilizes Redux for predictable state management, enabling efficient data flow throughout the CTI (Computer Telephony Integration) bridge application. Understanding this architecture is essential for developers working on feature development, debugging, or performance optimization.

## Store Configuration

The Redux store in Freedom Web is configured with middleware support, development tools integration, and proper reducer composition. The store setup follows Redux best practices for enterprise-grade applications.

### Basic Store Setup

```javascript
// store/index.js
import { createStore, applyMiddleware, compose } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from './reducers';

// Enable Redux DevTools Extension in development
const composeEnhancers = 
  (process.env.NODE_ENV === 'development' && 
   window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) || 
  compose;

// Middleware configuration
const middleware = [thunk];

// Add logging middleware in development
if (process.env.NODE_ENV === 'development') {
  const { createLogger } = require('redux-logger');
  middleware.push(createLogger({
    collapsed: true,
    diff: true
  }));
}

// Create the store with middleware
const store = createStore(
  rootReducer,
  composeEnhancers(applyMiddleware(...middleware))
);

export default store;
```

### Root Reducer Composition

```javascript
// store/reducers/index.js
import { combineReducers } from 'redux';
import authReducer from './authReducer';
import mainReducer from './mainReducer';
import sfReducer from './sfReducer';

const rootReducer = combineReducers({
  auth: authReducer,
  main: mainReducer,
  sf: sfReducer
});

export default rootReducer;
```

### Provider Configuration

```javascript
// index.js or App.js
import React from 'react';
import { Provider } from 'react-redux';
import store from './store';
import App from './App';

const Root = () => (
  <Provider store={store}>
    <App />
  </Provider>
);

export default Root;
```

## Initial State

The initial state structure defines the shape of the entire application state tree. Understanding this structure is critical for proper state access and manipulation.

### Complete Initial State Structure

```javascript
// store/initialState.js
export const initialState = {
  auth: {
    isAuthenticated: false,
    isLoading: false,
    user: null,
    token: null,
    refreshToken: null,
    tokenExpiry: null,
    error: null,
    permissions: [],
    loginAttempts: 0
  },
  
  main: {
    // Active Calls Management
    activeCalls: [],
    currentCall: null,
    callHistory: [],
    isOnCall: false,
    callStatus: 'idle', // 'idle' | 'ringing' | 'connected' | 'on-hold' | 'wrapping-up'
    
    // Voicemail Management
    voicemails: [],
    voicemailDrops: [],
    selectedVoicemail: null,
    voicemailLoading: false,
    unreadVoicemailCount: 0,
    
    // Address Book
    contacts: [],
    contactsLoading: false,
    selectedContact: null,
    contactSearchQuery: '',
    contactFilters: {
      type: 'all',
      favorite: false
    },
    
    // Team Collaboration
    teamMembers: [],
    teamStatus: {},
    teamPresence: {},
    
    // Call Logging & Wrap-ups
    callLogs: [],
    wrapUpCodes: [],
    currentWrapUp: null,
    wrapUpTimer: null,
    
    // Activity Tracking
    activities: [],
    activityStats: {
      totalCalls: 0,
      answeredCalls: 0,
      missedCalls: 0,
      averageHandleTime: 0,
      averageWrapUpTime: 0
    },
    
    // CTI Bridge
    ctiConnected: false,
    ctiStatus: 'disconnected',
    ctiError: null,
    agentState: 'logged-out', // 'logged-out' | 'available' | 'unavailable' | 'break' | 'after-call-work'
    
    // UI State
    isLoading: false,
    error: null,
    notifications: [],
    sidebarCollapsed: false,
    activeTab: 'calls'
  },
  
  sf: {
    // Salesforce Integration State
    isConnected: false,
    connectionStatus: 'disconnected',
    sessionId: null,
    instanceUrl: null,
    
    // Salesforce Records
    currentRecord: null,
    searchResults: [],
    recentRecords: [],
    
    // Screen Pop Configuration
    screenPopEnabled: true,
    screenPopBehavior: 'new-tab', // 'new-tab' | 'same-tab' | 'popup'
    
    // Click-to-Dial
    clickToDialEnabled: true,
    
    // Sync State
    syncStatus: 'idle',
    lastSyncTime: null,
    pendingSyncItems: [],
    
    // Error Handling
    error: null,
    isLoading: false
  }
};
```

## Reducers Overview

Freedom Web implements a modular reducer architecture with three primary reducers, each responsible for a specific domain of the application.

| Reducer | Domain | Responsibilities |
|---------|--------|------------------|
| `authReducer` | Authentication | User authentication, JWT token management, session handling |
| `mainReducer` | Core Operations | Calls, voicemail, contacts, team, activities, CTI bridge |
| `sfReducer` | Salesforce Integration | SF connection, records, screen pop, click-to-dial |

## Auth Reducer

The authentication reducer manages all user authentication state, including JWT token lifecycle, user permissions, and session management.

```javascript
// store/reducers/authReducer.js
import { initialState } from '../initialState';
import {
  LOGIN_REQUEST,
  LOGIN_SUCCESS,
  LOGIN_FAILURE,
  LOGOUT,
  REFRESH_TOKEN_REQUEST,
  REFRESH_TOKEN_SUCCESS,
  REFRESH_TOKEN_FAILURE,
  SET_USER_PERMISSIONS,
  CLEAR_AUTH_ERROR,
  UPDATE_USER_PROFILE
} from '../constants/authConstants';

const authReducer = (state = initialState.auth, action) => {
  switch (action.type) {
    case LOGIN_REQUEST:
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case LOGIN_SUCCESS:
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        tokenExpiry: action.payload.tokenExpiry,
        permissions: action.payload.permissions || [],
        error: null,
        loginAttempts: 0
      };

    case LOGIN_FAILURE:
      return {
        ...state,
        isAuthenticated: false,
        isLoading: false,
        user: null,
        token: null,
        error: action.payload.error,
        loginAttempts: state.loginAttempts + 1
      };

    case LOGOUT:
      return {
        ...initialState.auth
      };

    case REFRESH_TOKEN_REQUEST:
      return {
        ...state,
        isLoading: true
      };

    case REFRESH_TOKEN_SUCCESS:
      return {
        ...state,
        isLoading: false,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        tokenExpiry: action.payload.tokenExpiry,
        error: null
      };

    case REFRESH_TOKEN_FAILURE:
      return {
        ...initialState.auth,
        error: action.payload.error
      };

    case SET_USER_PERMISSIONS:
      return {
        ...state,
        permissions: action.payload
      };

    case CLEAR_AUTH_ERROR:
      return {
        ...state,
        error: null
      };

    case UPDATE_USER_PROFILE:
      return {
        ...state,
        user: {
          ...state.user,
          ...action.payload
        }
      };

    default:
      return state;
  }
};

export default authReducer;
```

### Auth Reducer Usage Examples

```javascript
// Selecting auth state in components
import { useSelector } from 'react-redux';

const AuthenticatedComponent = () => {
  const { isAuthenticated, user, permissions } = useSelector(state => state.auth);
  
  if (!isAuthenticated) {
    return <LoginRedirect />;
  }
  
  const canManageCalls = permissions.includes('calls:manage');
  
  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      {canManageCalls && <CallManagementPanel />}
    </div>
  );
};
```

## Main Reducer

The main reducer handles the core telephony operations including active calls, voicemail, contacts, team collaboration, and CTI bridge state.

```javascript
// store/reducers/mainReducer.js
import { initialState } from '../initialState';
import {
  // Call Management
  SET_ACTIVE_CALLS,
  ADD_ACTIVE_CALL,
  REMOVE_ACTIVE_CALL,
  UPDATE_CALL_STATUS,
  SET_CURRENT_CALL,
  SET_CALL_HISTORY,
  
  // Voicemail
  SET_VOICEMAILS,
  ADD_VOICEMAIL,
  DELETE_VOICEMAIL,
  SET_VOICEMAIL_DROPS,
  MARK_VOICEMAIL_READ,
  SET_SELECTED_VOICEMAIL,
  
  // Contacts
  SET_CONTACTS,
  ADD_CONTACT,
  UPDATE_CONTACT,
  DELETE_CONTACT,
  SET_SELECTED_CONTACT,
  SET_CONTACT_SEARCH_QUERY,
  SET_CONTACT_FILTERS,
  
  // Team
  SET_TEAM_MEMBERS,
  UPDATE_TEAM_STATUS,
  UPDATE_TEAM_PRESENCE,
  
  // Call Logging
  SET_CALL_LOGS,
  ADD_CALL_LOG,
  SET_WRAP_UP_CODES,
  SET_CURRENT_WRAP_UP,
  
  // CTI Bridge
  SET_CTI_CONNECTED,
  SET_CTI_STATUS,
  SET_CTI_ERROR,
  SET_AGENT_STATE,
  
  // UI State
  SET_LOADING,
  SET_ERROR,
  ADD_NOTIFICATION,
  REMOVE_NOTIFICATION,
  SET_SIDEBAR_COLLAPSED,
  SET_ACTIVE_TAB
} from '../constants/mainConstants';

const mainReducer = (state = initialState.main, action) => {
  switch (action.type) {
    // ==========================================
    // CALL MANAGEMENT
    // ==========================================
    case SET_ACTIVE_CALLS:
      return {
        ...state,
        activeCalls: action.payload,
        isOnCall: action.payload.length > 0
      };

    case ADD_ACTIVE_CALL:
      return {
        ...state,
        activeCalls: [...state.activeCalls, action.payload],
        isOnCall: true,
        callStatus: 'ringing'
      };

    case REMOVE_ACTIVE_CALL:
      const filteredCalls = state.activeCalls.filter(
        call => call.id !== action.payload
      );
      return {
        ...state,
        activeCalls: filteredCalls,
        isOnCall: filteredCalls.length > 0,
        currentCall: state.currentCall?.id === action.payload 
          ? null 
          : state.currentCall,
        callStatus: filteredCalls.length > 0 ? state.callStatus : 'idle'
      };

    case UPDATE_CALL_STATUS:
      return {
        ...state,
        callStatus: action.payload.status,
        activeCalls: state.activeCalls.map(call =>
          call.id === action.payload.callId
            ? { ...call, status: action.payload.status }
            : call
        )
      };

    case SET_CURRENT_CALL:
      return {
        ...state,
        currentCall: action.payload
      };

    case SET_CALL_HISTORY:
      return {
        ...state,
        callHistory: action.payload
      };

    // ==========================================
    // VOICEMAIL MANAGEMENT
    // ==========================================
    case SET_VOICEMAILS:
      return {
        ...state,
        voicemails: action.payload,
        unreadVoicemailCount: action.payload.filter(vm => !vm.isRead).length,
        voicemailLoading: false
      };

    case ADD_VOICEMAIL:
      return {
        ...state,
        voicemails: [action.payload, ...state.voicemails],
        unreadVoicemailCount: state.unreadVoicemailCount + 1
      };

    case DELETE_VOICEMAIL:
      const updatedVoicemails = state.voicemails.filter(
        vm => vm.id !== action.payload
      );
      return {
        ...state,
        voicemails: updatedVoicemails,
        unreadVoicemailCount: updatedVoicemails.filter(vm => !vm.isRead).length,
        selectedVoicemail: state.selectedVoicemail?.id === action.payload 
          ? null 
          : state.selectedVoicemail
      };

    case SET_VOICEMAIL_DROPS:
      return {
        ...state,
        voicemailDrops: action.payload
      };

    case MARK_VOICEMAIL_READ:
      return {
        ...state,
        voicemails: state.voicemails.map(vm =>
          vm.id === action.payload ? { ...vm, isRead: true } : vm
        ),
        unreadVoicemailCount: Math.max(0, state.unreadVoicemailCount - 1)
      };

    case SET_SELECTED_VOICEMAIL:
      return {
        ...state,
        selectedVoicemail: action.payload
      };

    // ==========================================
    // CONTACTS / ADDRESS BOOK
    // ==========================================
    case SET_CONTACTS:
      return {
        ...state,
        contacts: action.payload,
        contactsLoading: false
      };

    case ADD_CONTACT:
      return {
        ...state,
        contacts: [...state.contacts, action.payload]
      };

    case UPDATE_CONTACT:
      return {
        ...state,
        contacts: state.contacts.map(contact =>
          contact.id === action.payload.id
            ? { ...contact, ...action.payload }
            : contact
        ),
        selectedContact: state.selectedContact?.id === action.payload.id
          ? { ...state.selectedContact, ...action.payload }
          : state.selectedContact
      };

    case DELETE_CONTACT:
      return {
        ...state,
        contacts: state.contacts.filter(c => c.id !== action.payload),
        selectedContact: state.selectedContact?.id === action.payload 
          ? null 
          : state.selectedContact
      };

    case SET_SELECTED_CONTACT:
      return {
        ...state,
        selectedContact: action.payload
      };

    case SET_CONTACT_SEARCH_QUERY:
      return {
        ...state,
        contactSearchQuery: action.payload
      };

    case SET_CONTACT_FILTERS:
      return {
        ...state,
        contactFilters: {
          ...state.contactFilters,
          ...action.payload
        }
      };

    // ==========================================
    // TEAM COLLABORATION
    // ==========================================
    case SET_TEAM_MEMBERS:
      return {
        ...state,
        teamMembers: action.payload
      };

    case UPDATE_TEAM_STATUS:
      return {
        ...state,
        teamStatus: {
          ...state.teamStatus,
          [action.payload.userId]: action.payload.status
        }
      };

    case UPDATE_TEAM_PRESENCE:
      return {
        ...state,
        teamPresence: {
          ...state.teamPresence,
          [action.payload.userId]: action.payload.presence
        }
      };

    // ==========================================
    // CTI BRIDGE
    // ==========================================
    case SET_CTI_CONNECTED:
      return {
        ...state,
        ctiConnected: action.payload,
        ctiStatus: action.payload ? 'connected' : 'disconnected'
      };

    case SET_CTI_STATUS:
      return {
        ...state,
        ctiStatus: action.payload
      };

    case SET_CTI_ERROR:
      return {
        ...state,
        ctiError: action.payload,
        ctiStatus: 'error'
      };

    case SET_AGENT_STATE:
      return {
        ...state,
        agentState: action.payload
      };

    // ==========================================
    // UI STATE
    // ==========================================
    case SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      };

    case SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, {
          id: Date.now(),
          ...action.payload
        }]
      };

    case REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload)
      };

    case SET_SIDEBAR_COLLAPSED:
      return {
        ...state,
        sidebarCollapsed: action.payload
      };

    case SET_ACTIVE_TAB:
      return {
        ...state,
        activeTab: action.payload
      };

    default:
      return state;
  }
};

export default mainReducer;
```

## SF Reducer

The Salesforce (SF) reducer manages all Salesforce integration state, including connection status, record management, screen pop functionality, and click-to-dial features.

```javascript
// store/reducers/sfReducer.js
import { initialState } from '../initialState';
import {
  SF_CONNECT_REQUEST,
  SF_CONNECT_SUCCESS,
  SF_CONNECT_FAILURE,
  SF_DISCONNECT,
  SF_SET_CURRENT_RECORD,
  SF_SET_SEARCH_RESULTS,
  SF_CLEAR_SEARCH_RESULTS,
  SF_ADD_RECENT_RECORD,
  SF_SET_SCREEN_POP_ENABLED,
  SF_SET_SCREEN_POP_BEHAVIOR,
  SF_SET_CLICK_TO_DIAL_ENABLED,
  SF_SYNC_START,
  SF_SYNC_SUCCESS,
  SF_SYNC_FAILURE,
  SF_ADD_PENDING_SYNC_ITEM,
  SF_REMOVE_PENDING_SYNC_ITEM,
  SF_SET_ERROR,
  SF_CLEAR_ERROR
} from '../constants/sfConstants';

const sfReducer = (state = initialState.sf, action) => {
  switch (action.type) {
    // ==========================================
    // CONNECTION MANAGEMENT
    // ==========================================
    case SF_CONNECT_REQUEST:
      return {
        ...state,
        isLoading: true,
        connectionStatus: 'connecting',
        error: null
      };

    case SF_CONNECT_SUCCESS:
      return {
        ...state,
        isConnected: true,
        connectionStatus: 'connected',
        sessionId: action.payload.sessionId,
        instanceUrl: action.payload.instanceUrl,
        isLoading: false,
        error: null
      };

    case SF_CONNECT_FAILURE:
      return {
        ...state,
        isConnected: false,
        connectionStatus: 'failed',
        sessionId: null,
        instanceUrl: null,
        isLoading: false,
        error: action.payload.error
      };

    case SF_DISCONNECT:
      return {
        ...initialState.sf
      };

    // ==========================================
    // RECORD MANAGEMENT
    // ==========================================
    case SF_SET_CURRENT_RECORD:
      return {
        ...state,
        currentRecord: action.payload
      };

    case SF_SET_SEARCH_RESULTS:
      return {
        ...state,
        searchResults: action.payload,
        isLoading: false
      };

    case SF_CLEAR_SEARCH_RESULTS:
      return {
        ...state,
        searchResults: []
      };

    case SF_ADD_RECENT_RECORD:
      // Keep only last 10 recent records, avoid duplicates
      const filteredRecent = state.recentRecords.filter(
        r => r.id !== action.payload.id
      );
      return {
        ...state,
        recentRecords: [action.payload, ...filteredRecent].slice(0, 10)
      };

    // ==========================================
    // SCREEN POP & CLICK-TO-DIAL
    // ==========================================
    case SF_SET_SCREEN_POP_ENABLED:
      return {
        ...state,
        screenPopEnabled: action.payload
      };

    case SF_SET_SCREEN_POP_BEHAVIOR:
      return {
        ...state,
        screenPopBehavior: action.payload
      };

    case SF_SET_CLICK_TO_DIAL_ENABLED:
      return {
        ...state,
        clickToDialEnabled: action.payload
      };

    // ==========================================
    // SYNC STATE
    // ==========================================
    case SF_SYNC_START:
      return {
        ...state,
        syncStatus: 'syncing'
      };

    case SF_SYNC_SUCCESS:
      return {
        ...state,
        syncStatus: 'idle',
        lastSyncTime: new Date().toISOString(),
        pendingSyncItems: []
      };

    case SF_SYNC_FAILURE:
      return {
        ...state,
        syncStatus: 'error',
        error: action.payload.error
      };

    case SF_ADD_PENDING_SYNC_ITEM:
      return {
        ...state,
        pendingSyncItems: [...state.pendingSyncItems, action.payload]
      };

    case SF_REMOVE_PENDING_SYNC_ITEM:
      return {
        ...state,
        pendingSyncItems: state.pendingSyncItems.filter(
          item => item.id !== action.payload
        )
      };

    // ==========================================
    // ERROR HANDLING
    // ==========================================
    case SF_SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case SF_CLEAR_ERROR:
      return {
        ...state,
        error: null
      };

    default:
      return state;
  }
};

export default sfReducer;
```

## Actions

Actions are organized by domain and follow a consistent pattern with action creators for both synchronous and asynchronous operations.

### Auth Actions

```javascript
// store/actions/authActions.js
import {
  LOGIN_REQUEST,
  LOGIN_SUCCESS,
  LOGIN_FAILURE,
  LOGOUT,
  REFRESH_TOKEN_REQUEST,
  REFRESH_TOKEN_SUCCESS,
  REFRESH_TOKEN_FAILURE
} from '../constants/authConstants';
import { authService } from '../../services/authService';

// Synchronous Action Creators
export const loginRequest = () => ({
  type: LOGIN_REQUEST
});

export const loginSuccess = (payload) => ({
  type: LOGIN_SUCCESS,
  payload
});

export const loginFailure = (error) => ({
  type: LOGIN_FAILURE,
  payload: { error }
});

export const logout = () => ({
  type: LOGOUT
});

// Async Thunk Actions
export const login = (credentials) => async (dispatch) => {
  dispatch(loginRequest());
  
  try {
    const response = await authService.login(credentials);
    
    // Store tokens in secure storage
    localStorage.setItem('accessToken', response.token);
    localStorage.setItem('refreshToken', response.refreshToken);
    
    dispatch(loginSuccess({
      user: response.user,
      token: response.token,
      refreshToken: response.refreshToken,
      tokenExpiry: response.tokenExpiry,
      permissions: response.permissions
    }));
    
    return { success: true };
  } catch (error) {
    dispatch(loginFailure(error.message || 'Login failed'));
    return { success: false, error: error.message };
  }
};

export const refreshToken = () => async (dispatch, getState) => {
  dispatch({ type: REFRESH_TOKEN_REQUEST });
  
  const { auth } = getState();
  
  try {
    const response = await authService.refreshToken(auth.refreshToken);
    
    localStorage.setItem('accessToken', response.token);
    localStorage.setItem('refreshToken', response.refreshToken);
    
    dispatch({
      type: REFRESH_TOKEN_SUCCESS,
      payload: {
        token: response.token,
        refreshToken: response.refreshToken,
        tokenExpiry: response.tokenExpiry
      }
    });
    
    return { success: true };
  } catch (error) {
    dispatch({
      type: REFRESH_TOKEN_FAILURE,
      payload: { error: error.message }
    });
    
    // Force logout on refresh failure
    dispatch(performLogout());
    return { success: false };
  }
};

export const performLogout = () => (dispatch) => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  dispatch(logout());
};
```

### Main Actions

```javascript
// store/actions/mainActions.js
import {
  SET_ACTIVE_CALLS,
  ADD_ACTIVE_CALL,
  REMOVE_ACTIVE_CALL,
  UPDATE_CALL_STATUS,
  SET_VOICEMAILS,
  SET_CONTACTS,
  SET_CTI_CONNECTED,
  SET_AGENT_STATE,
  ADD_NOTIFICATION
} from '../constants/mainConstants';
import { callService } from '../../services/callService';
import { voicemailService } from '../../services/voicemailService';
import { contactService } from '../../services/contactService';

// ==========================================
// CALL ACTIONS
// ==========================================
export const fetchActiveCalls = () => async (dispatch) => {
  try {
    const calls = await callService.getActiveCalls();
    dispatch({
      type: SET_ACTIVE_CALLS,
      payload: calls
    });
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to fetch active calls',
      duration: 5000
    }));
  }
};

export const handleIncomingCall = (callData) => (dispatch) => {
  dispatch({
    type: ADD_ACTIVE_CALL,
    payload: {
      id: callData.callId,
      callerNumber: callData.callerNumber,
      callerName: callData.callerName,
      direction: 'inbound',
      status: 'ringing',
      startTime: new Date().toISOString(),
      ...callData
    }
  });
  
  dispatch(addNotification({
    type: 'info',
    message: `Incoming call from ${callData.callerName || callData.callerNumber}`,
    duration: 0 // Persistent until answered
  }));
};

export const answerCall = (callId) => async (dispatch) => {
  try {
    await callService.answerCall(callId);
    dispatch({
      type: UPDATE_CALL_STATUS,
      payload: { callId, status: 'connected' }
    });
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to answer call',
      duration: 5000
    }));
  }
};

export const endCall = (callId) => async (dispatch) => {
  try {
    await callService.endCall(callId);
    dispatch({
      type: REMOVE_ACTIVE_CALL,
      payload: callId
    });
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to end call',
      duration: 5000
    }));
  }
};

export const holdCall = (callId) => async (dispatch) => {
  try {
    await callService.holdCall(callId);
    dispatch({
      type: UPDATE_CALL_STATUS,
      payload: { callId, status: 'on-hold' }
    });
  } catch (error) {
    throw error;
  }
};

// ==========================================
// VOICEMAIL ACTIONS
// ==========================================
export const fetchVoicemails = () => async (dispatch) => {
  try {
    const voicemails = await voicemailService.getVoicemails();
    dispatch({
      type: SET_VOICEMAILS,
      payload: voicemails
    });
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to fetch voicemails',
      duration: 5000
    }));
  }
};

export const dropVoicemail = (callId, voicemailDropId) => async (dispatch) => {
  try {
    await voicemailService.dropVoicemail(callId, voicemailDropId);
    dispatch(addNotification({
      type: 'success',
      message: 'Voicemail dropped successfully',
      duration: 3000
    }));
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to drop voicemail',
      duration: 5000
    }));
    throw error;
  }
};

// ==========================================
// CONTACT ACTIONS
// ==========================================
export const fetchContacts = () => async (dispatch) => {
  try {
    const contacts = await contactService.getContacts();
    dispatch({
      type: SET_CONTACTS,
      payload: contacts
    });
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to fetch contacts',
      duration: 5000
    }));
  }
};

// ==========================================
// CTI BRIDGE ACTIONS
// ==========================================
export const initializeCTI = () => async (dispatch) => {
  try {
    await callService.initializeCTIBridge();
    dispatch({
      type: SET_CTI_CONNECTED,
      payload: true
    });
    dispatch({
      type: SET_AGENT_STATE,
      payload: 'available'
    });
  } catch (error) {
    dispatch({
      type: SET_CTI_CONNECTED,
      payload: false
    });
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to connect to CTI bridge',
      duration: 0
    }));
  }
};

export const setAgentState = (state) => async (dispatch) => {
  try {
    await callService.setAgentState(state);
    dispatch({
      type: SET_AGENT_STATE,
      payload: state
    });
  } catch (error) {
    dispatch(addNotification({
      type: 'error',
      message: 'Failed to update agent state',
      duration: 5000
    }));
  }
};

// ==========================================
// NOTIFICATION ACTIONS
// ==========================================
export const addNotification = (notification) => ({
  type: ADD_NOTIFICATION,
  payload: notification
});
```

### SF Actions

```javascript
// store/actions/sfActions.js
import {
  SF_CONNECT_REQUEST,
  SF_CONNECT_SUCCESS,
  SF_CONNECT_FAILURE,
  SF_DISCONNECT,
  SF_SET_CURRENT_RECORD,
  SF_SET_SEARCH_RESULTS,
  SF_SET_SCREEN_POP_ENABLED
} from '../constants/sfConstants';
import { sfService } from '../../services/sfService';

export const connectToSalesforce = () => async (dispatch) => {
  dispatch({ type: SF_CONNECT_REQUEST });
  
  try {
    const response = await sfService.connect();
    dispatch({
      type: SF_CONNECT_SUCCESS,
      payload: {
        sessionId: response.sessionId,
        instanceUrl: response.instanceUrl
      }
    });
    return { success: true };
  } catch (error) {
    dispatch({
      type: SF_CONNECT_FAILURE,
      payload: { error: error.message }
    });
    return { success: false, error: error.message };
  }
};

export const searchRecords = (query) => async (dispatch) => {
  try {
    const results = await sfService.searchRecords(query);
    dispatch({
      type: SF_SET_SEARCH_RESULTS,
      payload: results
    });
  } catch (error) {
    console.error('SF search failed:', error);
  }
};

export const triggerScreenPop = (phoneNumber) => async (dispatch, getState) => {
  const { sf } = getState();
  
  if (!sf.screenPopEnabled || !sf.isConnected) {
    return;
  }
  
  try {
    const record = await sfService.findRecordByPhone(phoneNumber);
    
    if (record) {
      dispatch({
        type: SF_SET_CURRENT_RECORD,
        payload: record
      });
      
      // Trigger screen pop based on behavior setting
      sfService.openRecord(record.id, sf.screenPopBehavior);
    }
  } catch (error) {
    console.error('Screen pop failed:', error);
  }
};

export const disconnectSalesforce = () => (dispatch) => {
  dispatch({ type: SF_DISCONNECT });
};

export const setScreenPopEnabled = (enabled) => ({
  type: SF_SET_SCREEN_POP_ENABLED,
  payload: enabled
});
```

## Action Constants

All action type constants are centralized in dedicated constant files to prevent typos and enable easy refactoring.

```javascript
// store/constants/authConstants.js
export const LOGIN_REQUEST = 'auth/LOGIN_REQUEST';
export const LOGIN_SUCCESS = 'auth/LOGIN_SUCCESS';
export const LOGIN_FAILURE = 'auth/LOGIN_FAILURE';
export const LOGOUT = 'auth/LOGOUT';
export const REFRESH_TOKEN_REQUEST = 'auth/REFRESH_TOKEN_REQUEST';
export const REFRESH_TOKEN_SUCCESS = 'auth/REFRESH_TOKEN_SUCCESS';
export const REFRESH_TOKEN_FAILURE = 'auth/REFRESH_TOKEN_FAILURE';
export const SET_USER_PERMISSIONS = 'auth/SET_USER_PERMISSIONS';
export const CLEAR_AUTH_ERROR = 'auth/CLEAR_AUTH_ERROR';
export const UPDATE_USER_PROFILE = 'auth/UPDATE_USER_PROFILE';

// store/constants/mainConstants.js
// Call Management
export const SET_ACTIVE_CALLS = 'main/SET_ACTIVE_CALLS';
export const ADD_ACTIVE_CALL = 'main/ADD_ACTIVE_CALL';
export const REMOVE_ACTIVE_CALL = 'main/REMOVE_ACTIVE_CALL';
export const UPDATE_CALL_STATUS = 'main/UPDATE_CALL_STATUS';
export const SET_CURRENT_CALL = 'main/SET_CURRENT_CALL';
export const SET_CALL_HISTORY = 'main/SET_CALL_HISTORY';

// Voicemail
export const SET_VOICEMAILS = 'main/SET_VOICEMAILS';
export const ADD_VOICEMAIL = 'main/ADD_VOICEMAIL';
export const DELETE_VOICEMAIL = 'main/DELETE_VOICEMAIL';
export const SET_VOICEMAIL_DROPS = 'main/SET_VOICEMAIL_DROPS';
export const MARK_VOICEMAIL_READ = 'main/MARK_VOICEMAIL_READ';
export const SET_SELECTED_VOICEMAIL = 'main/SET_SELECTED_VOICEMAIL';

// Contacts
export const SET_CONTACTS = 'main/SET_CONTACTS';
export const ADD_CONTACT = 'main/ADD_CONTACT';
export const UPDATE_CONTACT = 'main/UPDATE_CONTACT';
export const DELETE_CONTACT = 'main/DELETE_CONTACT';
export const SET_SELECTED_CONTACT = 'main/SET_SELECTED_CONTACT';
export const SET_CONTACT_SEARCH_QUERY = 'main/SET_CONTACT_SEARCH_QUERY';
export const SET_CONTACT_FILTERS = 'main/SET_CONTACT_FILTERS';

// Team
export const SET_TEAM_MEMBERS = 'main/SET_TEAM_MEMBERS';
export const UPDATE_TEAM_STATUS = 'main/UPDATE_TEAM_STATUS';
export const UPDATE_TEAM_PRESENCE = 'main/UPDATE_TEAM_PRESENCE';

// Call Logging
export const SET_CALL_LOGS = 'main/SET_CALL_LOGS';
export const ADD_CALL_LOG = 'main/ADD_CALL_LOG';
export const SET_WRAP_UP_CODES = 'main/SET_WRAP_UP_CODES';
export const SET_CURRENT_WRAP_UP = 'main/SET_CURRENT_WRAP_UP';

// CTI Bridge
export const SET_CTI_CONNECTED = 'main/SET_CTI_CONNECTED';
export const SET_CTI_STATUS = 'main/SET_CTI_STATUS';
export const SET_CTI_ERROR = 'main/SET_CTI_ERROR';
export const SET_AGENT_STATE = 'main/SET_AGENT_STATE';

// UI State
export const SET_LOADING = 'main/SET_LOADING';
export const SET_ERROR = 'main/SET_ERROR';
export const ADD_NOTIFICATION = 'main/ADD_NOTIFICATION';
export const REMOVE_NOTIFICATION = 'main/REMOVE_NOTIFICATION';
export const SET_SIDEBAR_COLLAPSED = 'main/SET_SIDEBAR_COLLAPSED';
export const SET_ACTIVE_TAB = 'main/SET_ACTIVE_TAB';

// store/constants/sfConstants.js
export const SF_CONNECT_REQUEST = 'sf/CONNECT_REQUEST';
export const SF_CONNECT_SUCCESS = 'sf/CONNECT_SUCCESS';
export const SF_CONNECT_FAILURE = 'sf/CONNECT_FAILURE';
export const SF_DISCONNECT = 'sf/DISCONNECT';
export const SF_SET_CURRENT_RECORD = 'sf/SET_CURRENT_RECORD';
export const SF_SET_SEARCH_RESULTS = 'sf/SET_SEARCH_RESULTS';
export const SF_CLEAR_SEARCH_RESULTS = 'sf/CLEAR_SEARCH_RESULTS';
export const SF_ADD_RECENT_RECORD = 'sf/ADD_RECENT_RECORD';
export const SF_SET_SCREEN_POP_ENABLED = 'sf/SET_SCREEN_POP_ENABLED';
export const SF_SET_SCREEN_POP_BEHAVIOR = 'sf/SET_SCREEN_POP_BEHAVIOR';
export const SF_SET_CLICK_TO_DIAL_ENABLED = 'sf/SET_CLICK_TO_DIAL_ENABLED';
export const SF_SYNC_START = 'sf/SYNC_START';
export const SF_SYNC_SUCCESS = 'sf/SYNC_SUCCESS';
export const SF_SYNC_FAILURE = 'sf/SYNC_FAILURE';
export const SF_ADD_PENDING_SYNC_ITEM = 'sf/ADD_PENDING_SYNC_ITEM';
export const SF_REMOVE_PENDING_SYNC_ITEM = 'sf/REMOVE_PENDING_SYNC_ITEM';
export const SF_SET_ERROR = 'sf/SET_ERROR';
export const SF_CLEAR_ERROR = 'sf/CLEAR_ERROR';
```

## Best Practices

### 1. Selector Functions

Create memoized selectors for derived data to prevent unnecessary re-renders:

```javascript
// store/selectors/mainSelectors.js
import { createSelector } from 'reselect';

// Base selectors
const selectMainState = (state) => state.main;
const selectContacts = (state) => state.main.contacts;
const selectContactFilters = (state) => state.main.contactFilters;
const selectContactSearchQuery = (state) => state.main.contactSearchQuery;

// Memoized filtered contacts selector
export const selectFilteredContacts = createSelector(
  [selectContacts, selectContactFilters, selectContactSearchQuery],
  (contacts, filters, searchQuery) => {
    let filtered = contacts;
    
    // Apply type filter
    if (filters.type !== 'all') {
      filtered = filtered.filter(c => c.type === filters.type);
    }
    
    // Apply favorite filter
    if (filters.favorite) {
      filtered = filtered.filter(c => c.isFavorite);
    }
    
    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(c =>
        c.name.toLowerCase().includes(query) ||
        c.phone.includes(query) ||
        c.email?.toLowerCase().includes(query)
      );
    }
    
    return filtered;
  }
);

// Select active call count
export const selectActiveCallCount = createSelector(
  [selectMainState],
  (main) => main.activeCalls.length
);

// Select unread voicemail count
export const selectUnreadVoicemailCount = createSelector(
  [selectMainState],
  (main) => main.unreadVoicemailCount
);
```

### 2. Action Batching

Batch multiple related actions to minimize re-renders:

```javascript
// Use batch from react-redux for multiple dispatches
import { batch } from 'react-redux';

export const initializeWorkspace = () => async (dispatch) => {
  const [calls, voicemails, contacts, team] = await Promise.all([
    callService.getActiveCalls(),
    voicemailService.getVoicemails(),
    contactService.getContacts(),
    teamService.getTeamMembers()
  ]);
  
  batch(() => {
    dispatch({ type: SET_ACTIVE_CALLS, payload: calls });
    dispatch({ type: SET_VOICEMAILS, payload: voicemails });
    dispatch({ type: SET_CONTACTS, payload: contacts });
    dispatch({ type: SET_TEAM_MEMBERS, payload: team });
  });
};
```

### 3. State Normalization

Normalize complex nested data structures for efficient updates:

```javascript
// Normalized state structure for calls
const normalizedCallsState = {
  byId: {
    'call-1': { id: 'call-1', callerNumber: '+15551234567', status: 'connected' },
    'call-2': { id: 'call-2', callerNumber: '+15559876543', status: 'on-hold' }
  },
  allIds: ['call-1', 'call-2']
};

// Update reducer for normalized state
case UPDATE_CALL_STATUS:
  return {
    ...state,
    byId: {
      ...state.byId,
      [action.payload.callId]: {
        ...state.byId[action.payload.callId],
        status: action.payload.status
      }
    }
  };
```

### 4. Error Handling Pattern

Implement consistent error handling across all async actions:

```javascript
// Utility for async action error handling
export const createAsyncAction = (actionTypes, asyncFn) => {
  return (...args) => async (dispatch, getState) => {
    dispatch({ type: actionTypes.request });
    
    try {
      const result = await asyncFn(...args, { dispatch, getState });
      dispatch({ 
        type: actionTypes.success, 
        payload: result 
      });
      return { success: true, data: result };
    } catch (error) {
      dispatch({ 
        type: actionTypes.failure, 
        payload: { 
          error: error.message,
          code: error.code 
        } 
      });
      return { success: false, error: error.message };
    }
  };
};
```

### 5. Testing Reducers

Write comprehensive tests for reducers:

```javascript
// store/reducers/__tests__/authReducer.test.js
import authReducer from '../authReducer';
import { LOGIN_SUCCESS, LOGOUT } from '../../constants/authConstants';
import { initialState } from '../../initialState';

describe('authReducer', () => {
  it('should return initial state', () => {
    expect(authReducer(undefined, {})).toEqual(initialState.auth);
  });
  
  it('should handle LOGIN_SUCCESS', () => {
    const payload = {
      user: { id: '1', name: 'Test User' },
      token: 'test-token',
      refreshToken: 'test-refresh',
      tokenExpiry: '2024-01-01T00:00:00Z',
      permissions: ['calls:manage']
    };
    
    const result = authReducer(initialState.auth, {
      type: LOGIN_SUCCESS,
      payload
    });
    
    expect(result.isAuthenticated).toBe(true);
    expect(result.user).toEqual(payload.user);
    expect(result.token).toBe(payload.token);
    expect(result.permissions).toEqual(payload.permissions);
  });
  
  it('should handle LOGOUT', () => {
    const loggedInState = {
      ...initialState.auth,
      isAuthenticated: true,
      user: { id: '1' },
      token: 'test-token'
    };
    
    const result = authReducer(loggedInState, { type: LOGOUT });
    
    expect(result).toEqual(initialState.auth);
  });
});
```

### 6. Performance Optimization

```javascript
// Use React.memo with selector hooks
import React, { memo } from 'react';
import { useSelector, shallowEqual } from 'react-redux';

const CallList = memo(() => {
  // Use shallowEqual for object/array comparisons
  const activeCalls = useSelector(
    state => state.main.activeCalls,
    shallowEqual
  );
  
  return (
    <ul>
      {activeCalls.map(call => (
        <CallItem key={call.id} call={call} />
      ))}
    </ul>
  );
});
```

---

## Summary

The Freedom Web state management implementation provides a robust, scalable foundation for managing complex telephony application state. By following the patterns and best practices outlined in this document, developers can effectively work with the Redux store while maintaining code quality and application performance.

Key takeaways:
- **Three-domain architecture**: Auth, Main, and SF reducers handle distinct concerns
- **Centralized constants**: All action types are defined in constant files
- **Async with thunks**: Complex async operations use Redux Thunk middleware
- **Memoized selectors**: Use Reselect for derived data calculations
- **Comprehensive testing**: All reducers should have unit test coverage