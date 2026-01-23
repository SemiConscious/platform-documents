# Salesforce Integration Guide

## Overview

This guide provides comprehensive documentation for integrating the FreedomCTI client with Salesforce Lightning. FreedomCTI is a browser-based Computer Telephony Integration (CTI) client that embeds within Salesforce as an iframe, enabling real-time call management, voicemail handling, and seamless telephony operations directly within the Salesforce user interface.

The integration leverages Salesforce's Open CTI API to provide a native-feeling telephony experience while maintaining the flexibility of a modern web application built with Redux state management and WebSocket-based real-time communication.

## Salesforce Lightning Integration

### Architecture Overview

FreedomCTI integrates with Salesforce Lightning through a multi-layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                 Salesforce Lightning Experience             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Lightning App                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │              Softphone Utility Bar               │  │  │
│  │  │  ┌─────────────────────────────────────────┐    │  │  │
│  │  │  │         FreedomCTI iframe               │    │  │  │
│  │  │  │  ┌───────────────────────────────────┐  │    │  │  │
│  │  │  │  │     React Application             │  │    │  │  │
│  │  │  │  │  • Redux State Management         │  │    │  │  │
│  │  │  │  │  • WebSocket Connection           │  │    │  │  │
│  │  │  │  │  • Open CTI API Bridge            │  │    │  │  │
│  │  │  │  └───────────────────────────────────┘  │    │  │  │
│  │  │  └─────────────────────────────────────────┘    │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Setting Up the Call Center Definition

Before embedding FreedomCTI, you must create a Call Center Definition file in Salesforce. This XML file defines the softphone configuration:

```xml
<!-- FreedomCTI_CallCenter.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<callCenter>
    <section sortOrder="0" name="reqGeneralInfo" label="General Information">
        <item sortOrder="0" name="reqInternalName" label="Internal Name">FreedomCTI</item>
        <item sortOrder="1" name="reqDisplayName" label="Display Name">Freedom CTI Client</item>
        <item sortOrder="2" name="reqAdapterUrl" label="CTI Adapter URL">/apex/FreedomCTIAdapter</item>
        <item sortOrder="3" name="reqUseApi" label="Use CTI API">true</item>
        <item sortOrder="4" name="reqSoftphoneHeight" label="Softphone Height">550</item>
        <item sortOrder="5" name="reqSoftphoneWidth" label="Softphone Width">350</item>
    </section>
    <section sortOrder="1" name="reqDialingOptions" label="Dialing Options">
        <item sortOrder="0" name="reqOutsidePrefix" label="Outside Prefix">9</item>
        <item sortOrder="1" name="reqLongDistPrefix" label="Long Distance Prefix">1</item>
        <item sortOrder="2" name="reqInternationalPrefix" label="International Prefix">011</item>
    </section>
    <section sortOrder="2" name="FreedomCTISettings" label="FreedomCTI Settings">
        <item sortOrder="0" name="Environment" label="Environment">production</item>
        <item sortOrder="1" name="WebSocketEndpoint" label="WebSocket Endpoint">wss://cti.freedomvoice.com/ws</item>
        <item sortOrder="2" name="EnableClickToDial" label="Enable Click-to-Dial">true</item>
        <item sortOrder="3" name="EnableScreenPop" label="Enable Screen Pop">true</item>
    </section>
</callCenter>
```

### Visualforce Adapter Page

Create a Visualforce page to host the FreedomCTI iframe:

```html
<!-- FreedomCTIAdapter.page -->
<apex:page showHeader="false" sidebar="false" standardStylesheets="false">
    <html>
        <head>
            <meta charset="UTF-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <style>
                html, body {
                    margin: 0;
                    padding: 0;
                    height: 100%;
                    overflow: hidden;
                }
                #cti-container {
                    width: 100%;
                    height: 100%;
                    border: none;
                }
            </style>
        </head>
        <body>
            <iframe 
                id="cti-container"
                src="{!$Setup.FreedomCTI_Settings__c.CTI_URL__c}"
                allow="microphone; camera"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            />
            <script src="/support/api/49.0/lightning/opencti_min.js"></script>
            <script>
                // Initialize message bridge between iframe and Salesforce
                window.addEventListener('message', function(event) {
                    if (event.data && event.data.type === 'FREEDOM_CTI_EVENT') {
                        handleCTIEvent(event.data);
                    }
                });
                
                function handleCTIEvent(data) {
                    var iframe = document.getElementById('cti-container');
                    // Forward Salesforce responses back to iframe
                    iframe.contentWindow.postMessage({
                        type: 'SALESFORCE_RESPONSE',
                        payload: data
                    }, '*');
                }
            </script>
        </body>
    </html>
</apex:page>
```

### Lightning App Configuration

Add the softphone utility to your Lightning App:

```javascript
// In Lightning App Builder or via Metadata API
{
    "flexiPageType": "AppPage",
    "utilityBar": {
        "utilityItems": [
            {
                "utilityItem": "SoftphoneUtility",
                "componentName": "lightning:openCTI",
                "label": "Phone",
                "icon": "standard:call",
                "width": 350,
                "height": 550,
                "contextParams": {
                    "customData": {
                        "environment": "production"
                    }
                }
            }
        ]
    }
}
```

## Iframe Communication

### Message Protocol

FreedomCTI uses a structured message protocol for bidirectional communication between the iframe and Salesforce:

```typescript
// types/IframeMessages.ts

// Base message interface
interface CTIMessage {
    type: string;
    timestamp: number;
    correlationId: string;
    payload: unknown;
}

// Outbound messages (CTI -> Salesforce)
interface ScreenPopRequest extends CTIMessage {
    type: 'SCREEN_POP_REQUEST';
    payload: {
        recordId?: string;
        phoneNumber?: string;
        searchType: 'exact' | 'contains' | 'starts_with';
        objectTypes?: string[];
    };
}

interface CallLogRequest extends CTIMessage {
    type: 'CALL_LOG_REQUEST';
    payload: {
        callId: string;
        subject: string;
        description: string;
        status: 'Completed' | 'No Answer' | 'Busy' | 'Left Voicemail';
        durationSeconds: number;
        direction: 'Inbound' | 'Outbound';
        relatedRecordId?: string;
    };
}

// Inbound messages (Salesforce -> CTI)
interface ClickToDialEvent extends CTIMessage {
    type: 'CLICK_TO_DIAL';
    payload: {
        number: string;
        recordId: string;
        objectType: string;
        recordName: string;
    };
}

interface SalesforceUserContext extends CTIMessage {
    type: 'USER_CONTEXT';
    payload: {
        userId: string;
        userName: string;
        userEmail: string;
        orgId: string;
        sessionId: string;
    };
}
```

### Message Handler Implementation

```javascript
// services/SalesforceMessageBridge.js

class SalesforceMessageBridge {
    constructor(store) {
        this.store = store;
        this.pendingRequests = new Map();
        this.messageQueue = [];
        this.isReady = false;
        
        this.initializeListener();
    }
    
    initializeListener() {
        window.addEventListener('message', this.handleMessage.bind(this));
        
        // Notify parent that CTI is ready
        this.postMessage({
            type: 'CTI_READY',
            payload: { version: '2.0.0' }
        });
    }
    
    handleMessage(event) {
        // Validate origin for security
        if (!this.isValidOrigin(event.origin)) {
            console.warn('Rejected message from invalid origin:', event.origin);
            return;
        }
        
        const message = event.data;
        
        if (!message || !message.type) {
            return;
        }
        
        switch (message.type) {
            case 'SALESFORCE_READY':
                this.isReady = true;
                this.flushMessageQueue();
                break;
                
            case 'CLICK_TO_DIAL':
                this.handleClickToDial(message.payload);
                break;
                
            case 'USER_CONTEXT':
                this.handleUserContext(message.payload);
                break;
                
            case 'SCREEN_POP_RESPONSE':
                this.resolveRequest(message.correlationId, message.payload);
                break;
                
            case 'NAVIGATION_CHANGE':
                this.handleNavigationChange(message.payload);
                break;
                
            default:
                console.log('Unhandled message type:', message.type);
        }
    }
    
    isValidOrigin(origin) {
        const allowedOrigins = [
            'https://*.salesforce.com',
            'https://*.force.com',
            'https://*.lightning.force.com',
            'https://*.my.salesforce.com'
        ];
        
        return allowedOrigins.some(pattern => {
            const regex = new RegExp(pattern.replace('*', '[a-zA-Z0-9-]+'));
            return regex.test(origin);
        });
    }
    
    postMessage(message) {
        const enrichedMessage = {
            ...message,
            timestamp: Date.now(),
            correlationId: message.correlationId || this.generateCorrelationId()
        };
        
        if (!this.isReady) {
            this.messageQueue.push(enrichedMessage);
            return enrichedMessage.correlationId;
        }
        
        window.parent.postMessage(enrichedMessage, '*');
        return enrichedMessage.correlationId;
    }
    
    async requestWithResponse(message, timeoutMs = 5000) {
        return new Promise((resolve, reject) => {
            const correlationId = this.postMessage(message);
            
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(correlationId);
                reject(new Error(`Request timeout: ${message.type}`));
            }, timeoutMs);
            
            this.pendingRequests.set(correlationId, {
                resolve: (data) => {
                    clearTimeout(timeout);
                    resolve(data);
                },
                reject
            });
        });
    }
    
    handleClickToDial(payload) {
        this.store.dispatch({
            type: 'INITIATE_OUTBOUND_CALL',
            payload: {
                phoneNumber: payload.number,
                recordId: payload.recordId,
                objectType: payload.objectType,
                recordName: payload.recordName
            }
        });
    }
    
    handleUserContext(payload) {
        this.store.dispatch({
            type: 'SET_SALESFORCE_CONTEXT',
            payload
        });
    }
    
    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            window.parent.postMessage(message, '*');
        }
    }
    
    generateCorrelationId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
}

export default SalesforceMessageBridge;
```

## Open CTI API Usage

### Initializing Open CTI

The Open CTI API must be initialized before any telephony operations:

```javascript
// services/OpenCTIService.js

class OpenCTIService {
    constructor() {
        this.isInitialized = false;
        this.sforce = null;
    }
    
    async initialize() {
        return new Promise((resolve, reject) => {
            // Check if running inside Salesforce iframe
            if (typeof sforce === 'undefined' || !sforce.opencti) {
                console.warn('Open CTI not available - running outside Salesforce');
                resolve(false);
                return;
            }
            
            this.sforce = sforce;
            
            // Get call center settings
            sforce.opencti.getCallCenterSettings({
                callback: (response) => {
                    if (response.success) {
                        this.callCenterSettings = response.returnValue;
                        this.isInitialized = true;
                        console.log('Open CTI initialized successfully');
                        resolve(true);
                    } else {
                        reject(new Error('Failed to get call center settings'));
                    }
                }
            });
        });
    }
    
    async setSoftphoneVisibility(visible) {
        if (!this.isInitialized) {
            throw new Error('Open CTI not initialized');
        }
        
        return new Promise((resolve, reject) => {
            sforce.opencti.setSoftphoneVisibility({
                visible: visible,
                callback: (response) => {
                    if (response.success) {
                        resolve(response);
                    } else {
                        reject(new Error(response.errors));
                    }
                }
            });
        });
    }
    
    async setSoftphoneItemLabel(label) {
        return new Promise((resolve, reject) => {
            sforce.opencti.setSoftphoneItemLabel({
                label: label,
                callback: (response) => {
                    response.success ? resolve(response) : reject(response.errors);
                }
            });
        });
    }
    
    async setSoftphoneItemIcon(icon, iconColor) {
        return new Promise((resolve, reject) => {
            sforce.opencti.setSoftphoneItemIcon({
                key: icon, // e.g., 'call', 'voicemail', 'end_call'
                iconColor: iconColor, // e.g., 'green', 'red', 'orange'
                callback: (response) => {
                    response.success ? resolve(response) : reject(response.errors);
                }
            });
        });
    }
    
    onNavigationChange(callback) {
        sforce.opencti.onNavigationChange({
            listener: callback
        });
    }
    
    enableClickToDial() {
        sforce.opencti.enableClickToDial({
            callback: (response) => {
                if (!response.success) {
                    console.error('Failed to enable click-to-dial:', response.errors);
                }
            }
        });
    }
    
    disableClickToDial() {
        sforce.opencti.disableClickToDial({
            callback: (response) => {
                if (!response.success) {
                    console.error('Failed to disable click-to-dial:', response.errors);
                }
            }
        });
    }
    
    onClickToDial(callback) {
        sforce.opencti.onClickToDial({
            listener: callback
        });
    }
}

export default new OpenCTIService();
```

### Softphone State Management

Manage the softphone panel state based on call activity:

```javascript
// redux/middleware/softphoneMiddleware.js

import OpenCTIService from '../services/OpenCTIService';

const softphoneMiddleware = store => next => action => {
    const result = next(action);
    const state = store.getState();
    
    switch (action.type) {
        case 'INCOMING_CALL':
            // Expand softphone and update icon
            OpenCTIService.setSoftphoneVisibility(true);
            OpenCTIService.setSoftphoneItemIcon('incoming_call', 'green');
            OpenCTIService.setSoftphoneItemLabel(`Incoming: ${action.payload.callerName || action.payload.phoneNumber}`);
            
            // Flash the utility bar item
            OpenCTIService.notifyUtilityItem({
                attention: true,
                label: 'Incoming Call'
            });
            break;
            
        case 'CALL_CONNECTED':
            OpenCTIService.setSoftphoneItemIcon('call', 'green');
            OpenCTIService.setSoftphoneItemLabel(`On Call: ${formatDuration(0)}`);
            
            // Start call duration timer
            store.dispatch({ type: 'START_CALL_TIMER' });
            break;
            
        case 'CALL_ENDED':
            OpenCTIService.setSoftphoneItemIcon('end_call', 'gray');
            OpenCTIService.setSoftphoneItemLabel('Phone');
            
            // Clear attention state
            OpenCTIService.notifyUtilityItem({
                attention: false
            });
            break;
            
        case 'VOICEMAIL_RECEIVED':
            const voicemailCount = state.voicemail.unreadCount + 1;
            OpenCTIService.setSoftphoneItemLabel(`Phone (${voicemailCount} VM)`);
            OpenCTIService.notifyUtilityItem({
                attention: true,
                label: 'New Voicemail'
            });
            break;
    }
    
    return result;
};

export default softphoneMiddleware;
```

## Screen Pop Configuration

### Implementing Screen Pop

Screen pop automatically navigates to relevant records when calls are received:

```javascript
// services/ScreenPopService.js

class ScreenPopService {
    constructor() {
        this.screenPopRules = [];
    }
    
    async searchAndPop(phoneNumber, callDirection) {
        if (!sforce || !sforce.opencti) {
            console.warn('Screen pop unavailable outside Salesforce');
            return null;
        }
        
        try {
            // First, search for matching records
            const searchResults = await this.searchByPhoneNumber(phoneNumber);
            
            if (searchResults.length === 0) {
                // No matches - offer to create new record
                return this.popNewRecordPage(phoneNumber, callDirection);
            } else if (searchResults.length === 1) {
                // Single match - navigate directly
                return this.popRecord(searchResults[0]);
            } else {
                // Multiple matches - show search results
                return this.popSearchResults(phoneNumber, searchResults);
            }
        } catch (error) {
            console.error('Screen pop failed:', error);
            throw error;
        }
    }
    
    async searchByPhoneNumber(phoneNumber) {
        return new Promise((resolve, reject) => {
            sforce.opencti.searchAndScreenPop({
                searchParams: phoneNumber,
                queryParams: '', // Optional SOQL filter
                defaultFieldValues: {}, // For new record creation
                callType: sforce.opencti.CALL_TYPE.INBOUND,
                deferred: true, // Don't auto-navigate
                callback: (response) => {
                    if (response.success) {
                        resolve(response.returnValue);
                    } else {
                        reject(new Error(response.errors));
                    }
                }
            });
        });
    }
    
    async popRecord(record) {
        return new Promise((resolve, reject) => {
            sforce.opencti.screenPop({
                type: sforce.opencti.SCREENPOP_TYPE.SOBJECT,
                params: {
                    recordId: record.Id
                },
                callback: (response) => {
                    if (response.success) {
                        resolve(record);
                    } else {
                        reject(new Error(response.errors));
                    }
                }
            });
        });
    }
    
    async popNewRecordPage(phoneNumber, callDirection) {
        const objectType = callDirection === 'Inbound' ? 'Case' : 'Task';
        const defaultValues = this.getDefaultFieldValues(phoneNumber, callDirection, objectType);
        
        return new Promise((resolve, reject) => {
            sforce.opencti.screenPop({
                type: sforce.opencti.SCREENPOP_TYPE.NEW_RECORD_MODAL,
                params: {
                    entityName: objectType,
                    defaultFieldValues: defaultValues
                },
                callback: (response) => {
                    response.success ? resolve(response) : reject(response.errors);
                }
            });
        });
    }
    
    async popSearchResults(phoneNumber, results) {
        return new Promise((resolve, reject) => {
            sforce.opencti.screenPop({
                type: sforce.opencti.SCREENPOP_TYPE.SEARCH,
                params: {
                    searchString: phoneNumber
                },
                callback: (response) => {
                    response.success ? resolve(results) : reject(response.errors);
                }
            });
        });
    }
    
    async popUrl(url) {
        return new Promise((resolve, reject) => {
            sforce.opencti.screenPop({
                type: sforce.opencti.SCREENPOP_TYPE.URL,
                params: {
                    url: url
                },
                callback: (response) => {
                    response.success ? resolve(response) : reject(response.errors);
                }
            });
        });
    }
    
    getDefaultFieldValues(phoneNumber, callDirection, objectType) {
        const baseValues = {
            Phone: phoneNumber,
            Origin: 'Phone'
        };
        
        if (objectType === 'Task') {
            return {
                ...baseValues,
                Subject: `${callDirection} Call - ${phoneNumber}`,
                Status: 'In Progress',
                Priority: 'Normal',
                CallType: callDirection
            };
        }
        
        if (objectType === 'Case') {
            return {
                ...baseValues,
                Subject: `Phone Inquiry - ${phoneNumber}`,
                Status: 'New',
                Priority: 'Medium'
            };
        }
        
        return baseValues;
    }
}

export default new ScreenPopService();
```

### Screen Pop Rules Configuration

```javascript
// config/screenPopRules.js

export const screenPopRules = [
    {
        name: 'VIP Customer',
        priority: 1,
        conditions: {
            objectType: 'Contact',
            fieldConditions: [
                { field: 'VIP_Status__c', operator: 'equals', value: 'true' }
            ]
        },
        action: {
            type: 'navigate',
            target: 'record'
        }
    },
    {
        name: 'Open Case',
        priority: 2,
        conditions: {
            objectType: 'Case',
            fieldConditions: [
                { field: 'Status', operator: 'not_equals', value: 'Closed' }
            ]
        },
        action: {
            type: 'navigate',
            target: 'record'
        }
    },
    {
        name: 'Recent Opportunity',
        priority: 3,
        conditions: {
            objectType: 'Opportunity',
            fieldConditions: [
                { field: 'StageName', operator: 'not_equals', value: 'Closed Won' },
                { field: 'StageName', operator: 'not_equals', value: 'Closed Lost' }
            ]
        },
        action: {
            type: 'navigate',
            target: 'record'
        }
    },
    {
        name: 'Default - Create Task',
        priority: 99,
        conditions: {
            noMatchFound: true
        },
        action: {
            type: 'create',
            target: 'Task',
            defaultFields: {
                Subject: 'Phone Call',
                Status: 'In Progress'
            }
        }
    }
];
```

## Click-to-Dial Setup

### Enabling Click-to-Dial

```javascript
// services/ClickToDialService.js

class ClickToDialService {
    constructor(dialHandler) {
        this.dialHandler = dialHandler;
        this.isEnabled = false;
    }
    
    enable() {
        if (!sforce || !sforce.opencti) {
            console.warn('Click-to-dial unavailable outside Salesforce');
            return;
        }
        
        // Enable click-to-dial links
        sforce.opencti.enableClickToDial({
            callback: (response) => {
                if (response.success) {
                    this.isEnabled = true;
                    console.log('Click-to-dial enabled');
                    
                    // Register click handler
                    this.registerClickHandler();
                } else {
                    console.error('Failed to enable click-to-dial:', response.errors);
                }
            }
        });
    }
    
    disable() {
        sforce.opencti.disableClickToDial({
            callback: (response) => {
                if (response.success) {
                    this.isEnabled = false;
                    console.log('Click-to-dial disabled');
                }
            }
        });
    }
    
    registerClickHandler() {
        sforce.opencti.onClickToDial({
            listener: (payload) => {
                this.handleClickToDial(payload);
            }
        });
    }
    
    handleClickToDial(payload) {
        console.log('Click-to-dial triggered:', payload);
        
        const dialInfo = {
            phoneNumber: this.normalizePhoneNumber(payload.number),
            recordId: payload.recordId,
            recordName: payload.recordName,
            objectType: payload.objectType,
            rawNumber: payload.number
        };
        
        // Validate phone number
        if (!this.isValidPhoneNumber(dialInfo.phoneNumber)) {
            this.showError('Invalid phone number format');
            return;
        }
        
        // Check if user is available to make calls
        if (!this.canMakeCall()) {
            this.showError('Unable to make call - check your phone status');
            return;
        }
        
        // Initiate the call
        this.dialHandler(dialInfo);
    }
    
    normalizePhoneNumber(number) {
        // Remove all non-numeric characters except +
        let normalized = number.replace(/[^\d+]/g, '');
        
        // Handle special prefixes from call center settings
        if (normalized.startsWith('9')) {
            normalized = normalized.substring(1); // Remove outside prefix
        }
        
        // Ensure proper format for US numbers
        if (normalized.length === 10) {
            normalized = '1' + normalized;
        }
        
        return normalized;
    }
    
    isValidPhoneNumber(number) {
        // US/Canada: 11 digits starting with 1
        // International: starts with + and has 10-15 digits
        const usPattern = /^1\d{10}$/;
        const internationalPattern = /^\+\d{10,15}$/;
        
        return usPattern.test(number) || internationalPattern.test(number);
    }
    
    canMakeCall() {
        // Check agent status, active calls, etc.
        const state = window.store?.getState();
        
        if (!state) return false;
        
        return (
            state.agent.status !== 'offline' &&
            state.calls.activeCalls.length === 0 &&
            state.phone.registered
        );
    }
    
    showError(message) {
        sforce.opencti.screenPop({
            type: sforce.opencti.SCREENPOP_TYPE.FLOW,
            params: {
                flowDevName: 'CTI_Error_Toast',
                flowArgs: [
                    { name: 'errorMessage', type: 'String', value: message }
                ]
            },
            callback: () => {}
        });
    }
}

export default ClickToDialService;
```

### Click-to-Dial Component Integration

```javascript
// components/DialPad/DialPad.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { initiateCall } from '../../redux/actions/callActions';
import ClickToDialService from '../../services/ClickToDialService';

const DialPad = () => {
    const dispatch = useDispatch();
    const [phoneNumber, setPhoneNumber] = useState('');
    const [clickToDialContext, setClickToDialContext] = useState(null);
    
    const agentStatus = useSelector(state => state.agent.status);
    const activeCalls = useSelector(state => state.calls.activeCalls);
    
    // Handle click-to-dial from Salesforce
    const handleClickToDial = useCallback((dialInfo) => {
        setPhoneNumber(dialInfo.phoneNumber);
        setClickToDialContext({
            recordId: dialInfo.recordId,
            recordName: dialInfo.recordName,
            objectType: dialInfo.objectType
        });
        
        // Auto-dial if configured
        if (window.appConfig?.autoDialClickToDial) {
            handleDial(dialInfo.phoneNumber, dialInfo);
        }
    }, []);
    
    useEffect(() => {
        const clickToDialService = new ClickToDialService(handleClickToDial);
        
        if (agentStatus === 'available') {
            clickToDialService.enable();
        } else {
            clickToDialService.disable();
        }
        
        return () => {
            clickToDialService.disable();
        };
    }, [agentStatus, handleClickToDial]);
    
    const handleDial = (number, context = null) => {
        if (!number || activeCalls.length > 0) {
            return;
        }
        
        dispatch(initiateCall({
            phoneNumber: number,
            salesforceContext: context || clickToDialContext
        }));
        
        // Clear after dialing
        setPhoneNumber('');
        setClickToDialContext(null);
    };
    
    return (
        <div className="dial-pad">
            {clickToDialContext && (
                <div className="click-to-dial-context">
                    <span className="record-info">
                        Calling: {clickToDialContext.recordName}
                    </span>
                    <span className="object-type">
                        ({clickToDialContext.objectType})
                    </span>
                </div>
            )}
            
            <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="Enter phone number"
                className="phone-input"
            />
            
            {/* Dial pad buttons */}
            <div className="dial-buttons">
                {/* ... number buttons ... */}
            </div>
            
            <button
                className="dial-button"
                onClick={() => handleDial(phoneNumber)}
                disabled={!phoneNumber || activeCalls.length > 0}
            >
                Call
            </button>
        </div>
    );
};

export default DialPad;
```

## Namespace Handling

### Managing Salesforce Namespaces

When working with managed packages or custom objects, proper namespace handling is critical:

```javascript
// utils/namespaceUtils.js

class NamespaceManager {
    constructor() {
        this.namespace = null;
        this.namespacePrefix = '';
    }
    
    async detectNamespace() {
        return new Promise((resolve) => {
            if (!sforce || !sforce.opencti) {
                resolve(null);
                return;
            }
            
            sforce.opencti.getCallCenterSettings({
                callback: (response) => {
                    if (response.success) {
                        // Extract namespace from settings if present
                        const settings = response.returnValue;
                        
                        // Check for namespace in internal name
                        const internalName = settings['/reqGeneralInfo/reqInternalName'];
                        const namespaceMatch = internalName?.match(/^(\w+)__/);
                        
                        if (namespaceMatch) {
                            this.namespace = namespaceMatch[1];
                            this.namespacePrefix = `${this.namespace}__`;
                        }
                        
                        resolve(this.namespace);
                    } else {
                        resolve(null);
                    }
                }
            });
        });
    }
    
    // Apply namespace to field API names
    applyNamespace(fieldName) {
        // Don't namespace standard fields
        if (this.isStandardField(fieldName)) {
            return fieldName;
        }
        
        // Don't double-namespace
        if (fieldName.includes('__')) {
            return fieldName;
        }
        
        return `${this.namespacePrefix}${fieldName}__c`;
    }
    
    // Apply namespace to object API names
    applyNamespaceToObject(objectName) {
        // Don't namespace standard objects
        if (this.isStandardObject(objectName)) {
            return objectName;
        }
        
        // Don't double-namespace
        if (objectName.includes('__')) {
            return objectName;
        }
        
        return `${this.namespacePrefix}${objectName}__c`;
    }
    
    // Strip namespace from API names
    stripNamespace(apiName) {
        if (!this.namespacePrefix) {
            return apiName;
        }
        
        return apiName.replace(this.namespacePrefix, '');
    }
    
    isStandardField(fieldName) {
        const standardFields = [
            'Id', 'Name', 'CreatedDate', 'LastModifiedDate', 'OwnerId',
            'Phone', 'Email', 'FirstName', 'LastName', 'AccountId',
            'ContactId', 'Subject', 'Description', 'Status', 'Priority'
        ];
        
        return standardFields.includes(fieldName);
    }
    
    isStandardObject(objectName) {
        const standardObjects = [
            'Account', 'Contact', 'Lead', 'Opportunity', 'Case',
            'Task', 'Event', 'User', 'Campaign', 'Contract'
        ];
        
        return standardObjects.includes(objectName);
    }
    
    // Build dynamic SOQL with proper namespacing
    buildQuery(objectName, fields, whereClause) {
        const namespacedObject = this.applyNamespaceToObject(objectName);
        const namespacedFields = fields.map(f => this.applyNamespace(f));
        
        let query = `SELECT ${namespacedFields.join(', ')} FROM ${namespacedObject}`;
        
        if (whereClause) {
            query += ` WHERE ${whereClause}`;
        }
        
        return query;
    }
}

export const namespaceManager = new NamespaceManager();
```

### Using Namespace Manager in Services

```javascript
// services/SalesforceDataService.js

import { namespaceManager } from '../utils/namespaceUtils';

class SalesforceDataService {
    async initialize() {
        await namespaceManager.detectNamespace();
        console.log('Detected namespace:', namespaceManager.namespace || 'none');
    }
    
    async createCallLog(callData) {
        const taskFields = {
            [namespaceManager.applyNamespace('Call_ID')]: callData.callId,
            [namespaceManager.applyNamespace('Call_Duration')]: callData.duration,
            [namespaceManager.applyNamespace('Call_Direction')]: callData.direction,
            [namespaceManager.applyNamespace('Recording_URL')]: callData.recordingUrl,
            Subject: `${callData.direction} Call - ${callData.phoneNumber}`,
            Description: callData.notes,
            Status: 'Completed',
            Priority: 'Normal',
            WhoId: callData.contactId,
            WhatId: callData.accountId
        };
        
        return this.createRecord('Task', taskFields);
    }
    
    async createRecord(objectType, fields) {
        // Implementation using Salesforce API
        // This would use REST API or Lightning Data Service
    }
}

export default new SalesforceDataService();
```

## Troubleshooting Salesforce Issues

### Common Issues and Solutions

#### 1. Open CTI Not Loading

**Symptoms:** Softphone doesn't appear, console shows "sforce is undefined"

**Diagnostic Steps:**

```javascript
// diagnostics/OpenCTIDiagnostics.js

export async function runOpenCTIDiagnostics() {
    const results = {
        timestamp: new Date().toISOString(),
        checks: []
    };
    
    // Check 1: sforce global object
    results.checks.push({
        name: 'sforce Global Object',
        passed: typeof sforce !== 'undefined',
        details: typeof sforce !== 'undefined' 
            ? 'sforce object is available'
            : 'sforce object not found - ensure Open CTI script is loaded'
    });
    
    // Check 2: opencti API
    results.checks.push({
        name: 'Open CTI API',
        passed: typeof sforce?.opencti !== 'undefined',
        details: sforce?.opencti 
            ? 'opencti API is available'
            : 'opencti API not found - check API version'
    });
    
    // Check 3: Call Center Settings
    if (sforce?.opencti) {
        try {
            const settings = await new Promise((resolve, reject) => {
                sforce.opencti.getCallCenterSettings({
                    callback: (response) => {
                        response.success ? resolve(response.returnValue) : reject(response.errors);
                    }
                });
            });
            
            results.checks.push({
                name: 'Call Center Settings',
                passed: true,
                details: settings
            });
        } catch (error) {
            results.checks.push({
                name: 'Call Center Settings',
                passed: false,
                details: `Error: ${error}`
            });
        }
    }
    
    // Check 4: User Assignment
    if (sforce?.opencti) {
        try {
            const softphoneInfo = await new Promise((resolve, reject) => {
                sforce.opencti.isSoftphonePanelVisible({
                    callback: (response) => {
                        response.success ? resolve(response) : reject(response.errors);
                    }
                });
            });
            
            results.checks.push({
                name: 'Softphone Panel',
                passed: true,
                details: `Panel visible: ${softphoneInfo.returnValue}`
            });
        } catch (error) {
            results.checks.push({
                name: 'Softphone Panel',
                passed: false,
                details: `User may not be assigned to Call Center: ${error}`
            });
        }
    }
    
    console.log('Open CTI Diagnostics:', results);
    return results;
}
```

**Solutions:**

```html
<!-- Ensure correct API version in Visualforce -->
<script src="/support/api/58.0/lightning/opencti_min.js"></script>

<!-- Or dynamically load correct version -->
<script>
    var apiVersion = '{!$Api.Session_ID}'.split('!')[0] === '00D' ? '58.0' : '57.0';
    var script = document.createElement('script');
    script.src = '/support/api/' + apiVersion + '/lightning/opencti_min.js';
    document.head.appendChild(script);
</script>
```

#### 2. Iframe Communication Failures

**Symptoms:** Actions in CTI don't reflect in Salesforce, screen pops don't work

**Diagnostic Script:**

```javascript
// diagnostics/IframeDiagnostics.js

export function diagnoseIframeCommunication() {
    const diagnostics = {
        isInIframe: window.self !== window.top,
        parentOrigin: null,
        messageChannelActive: false
    };
    
    // Test message channel
    const testMessage = {
        type: 'DIAGNOSTIC_PING',
        timestamp: Date.now()
    };
    
    // Set up response listener
    const responsePromise = new Promise((resolve) => {
        const handler = (event) => {
            if (event.data?.type === 'DIAGNOSTIC_PONG') {
                diagnostics.parentOrigin = event.origin;
                diagnostics.messageChannelActive = true;
                window.removeEventListener('message', handler);
                resolve(true);
            }
        };
        
        window.addEventListener('message', handler);
        
        // Timeout after 3 seconds
        setTimeout(() => {
            window.removeEventListener('message', handler);
            resolve(false);
        }, 3000);
    });
    
    // Send test message
    if (diagnostics.isInIframe) {
        window.parent.postMessage(testMessage, '*');
    }
    
    return responsePromise.then(() => {
        console.log('Iframe Diagnostics:', diagnostics);
        return diagnostics;
    });
}
```

#### 3. Click-to-Dial Not Working

**Troubleshooting Checklist:**

```javascript
// diagnostics/ClickToDialDiagnostics.js

export async function diagnoseClickToDial() {
    const results = [];
    
    // Check 1: Click-to-dial enabled
    if (sforce?.opencti) {
        const status = await new Promise((resolve) => {
            sforce.opencti.isClickToDialEnabled({
                callback: (response) => resolve(response)
            });
        });
        
        results.push({
            check: 'Click-to-Dial Enabled',
            status: status.success && status.returnValue,
            action: !status.returnValue ? 'Call enableClickToDial()' : null
        });
    }
    
    // Check 2: Listener registered
    results.push({
        check: 'Listener Registered',
        status: window._clickToDialListenerActive === true,
        action: !window._clickToDialListenerActive ? 'Register onClickToDial listener' : null
    });
    
    // Check 3: Phone fields on page layout
    results.push({
        check: 'Phone Fields on Layout',
        status: 'Manual check required',
        action: 'Verify phone fields are on the page layout and have click-to-dial enabled'
    });
    
    // Check 4: User permissions
    results.push({
        check: 'User Permissions',
        status: 'Manual check required',
        action: 'Verify user has "Make Calls" permission in Call Center'
    });
    
    console.table(results);
    return results;
}
```

#### 4. Screen Pop Issues

**Debug Mode for Screen Pop:**

```javascript
// services/ScreenPopService.js - Debug version

class ScreenPopServiceDebug extends ScreenPopService {
    async searchAndPop(phoneNumber, callDirection) {
        console.group('Screen Pop Debug');
        console.log('Input:', { phoneNumber, callDirection });
        
        try {
            // Log search query
            console.log('Searching for:', phoneNumber);
            
            const searchResults = await this.searchByPhoneNumber(phoneNumber);
            console.log('Search results:', searchResults);
            
            if (searchResults.length === 0) {
                console.log('No results - popping new record form');
                return await this.popNewRecordPage(phoneNumber, callDirection);
            }
            
            if (searchResults.length === 1) {
                console.log('Single result - navigating to:', searchResults[0]);
                return await this.popRecord(searchResults[0]);
            }
            
            console.log('Multiple results - showing search');
            return await this.popSearchResults(phoneNumber, searchResults);
            
        } catch (error) {
            console.error('Screen pop error:', error);
            throw error;
        } finally {
            console.groupEnd();
        }
    }
}
```

### Error Reference Table

| Error Code | Description | Solution |
|------------|-------------|----------|
| `OPENCTI_NOT_INITIALIZED` | Open CTI API not loaded | Verify API script URL and loading order |
| `USER_NOT_ASSIGNED` | User not in Call Center | Assign user to Call Center in Salesforce Setup |
| `SOFTPHONE_NOT_VISIBLE` | Utility bar item hidden | Check Lightning App configuration |
| `CLICK_TO_DIAL_DISABLED` | Feature not enabled | Call `enableClickToDial()` on initialization |
| `CROSS_ORIGIN_BLOCKED` | Message rejected | Verify iframe origin in CSP headers |
| `NAMESPACE_MISMATCH` | Wrong field/object names | Use NamespaceManager for API names |
| `SCREEN_POP_BLOCKED` | Browser popup blocker | Screen pop uses navigation, not popups |
| `API_VERSION_MISMATCH` | Incompatible API version | Update `opencti_min.js` version |

### Logging and Monitoring

```javascript
// utils/SalesforceLogger.js

class SalesforceLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 1000;
    }
    
    log(level, category, message, data = {}) {
        const entry = {
            timestamp: new Date().toISOString(),
            level,
            category,
            message,
            data,
            sessionId: this.getSessionId()
        };
        
        this.logs.push(entry);
        
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // Console output
        const consoleMethod = level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log';
        console[consoleMethod](`[${category}] ${message}`, data);
        
        // Send to backend if error
        if (level === 'error') {
            this.sendToBackend(entry);
        }
    }
    
    exportLogs() {
        return JSON.stringify(this.logs, null, 2);
    }
    
    async sendToBackend(entry) {
        try {
            await fetch('/api/logs/salesforce', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(entry)
            });
        } catch (error) {
            console.error('Failed to send log:', error);
        }
    }
    
    getSessionId() {
        return window.salesforceContext?.sessionId || 'unknown';
    }
}

export const logger = new SalesforceLogger();

// Usage examples:
// logger.log('info', 'ScreenPop', 'Searching for phone number', { phone: '555-1234' });
// logger.log('error', 'OpenCTI', 'Failed to enable click-to-dial', { error: response.errors });
```

---

## Related Documentation

- [WebSocket Events Documentation](./websocket-events.md)
- [Call Logging API Reference](./api/call-logging.md)
- [Redux State Management](./redux-architecture.md)
- [Environment Configuration](./environment-config.md)

## Support

For issues specific to Salesforce integration:
1. Check the browser console for Open CTI errors
2. Run diagnostic scripts documented above
3. Review Salesforce Setup → Call Centers → Debug Logs
4. Contact the platform team with exported logs