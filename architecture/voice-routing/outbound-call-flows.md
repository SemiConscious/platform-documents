# Outbound Call Flow Documentation

## Overview

This document provides comprehensive technical documentation for outbound call flows in the Natterbox voice platform. It covers all aspects from call initiation through various methods (Click-to-dial, API, Salesforce CTI, WebRTC) to PSTN egress via carrier trunks, including routing decisions, caller ID manipulation, recording policies, and CDR generation.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Call Initiation Methods](#call-initiation-methods)
3. [Originate Command](#originate-command)
4. [LCR (Least Cost Routing)](#lcr-least-cost-routing)
5. [Carrier Gateway Selection](#carrier-gateway-selection)
6. [Outbound Caller ID Manipulation](#outbound-caller-id-manipulation)
7. [PSTN Egress](#pstn-egress)
8. [Call Progress Detection](#call-progress-detection)
9. [Recording Policies](#recording-policies)
10. [CDR Generation and Billing](#cdr-generation-and-billing)
11. [Error Handling](#error-handling)
12. [Sequence Diagrams](#sequence-diagrams)

---

## Architecture Overview

### High-Level Outbound Call Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTBOUND CALL FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Initiation │───▶│  FreeSWITCH  │───▶│  LCR Service │───▶│  Carrier  │ │
│  │  (CTI/API/   │    │   (Originate │    │  (Route      │    │  Gateway  │ │
│  │   WebRTC)    │    │    Command)  │    │   Selection) │    │           │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └─────┬─────┘ │
│                             │                    │                  │       │
│                             ▼                    ▼                  ▼       │
│                      ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│                      │  Caller ID   │    │   Carrier    │    │   PSTN    │ │
│                      │ Manipulation │    │   Failover   │    │  Network  │ │
│                      └──────────────┘    └──────────────┘    └───────────┘ │
│                             │                    │                          │
│                             ▼                    ▼                          │
│                      ┌──────────────┐    ┌──────────────┐                   │
│                      │  Recording   │    │     CDR      │                   │
│                      │   Policy     │    │  Generation  │                   │
│                      └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **Initiation Layer** | Click-to-dial, API calls, WebRTC origination |
| **FreeSWITCH Core** | Call control, originate commands, bridging |
| **LCR Service** | Route selection, cost optimization, carrier prioritization |
| **Carrier Gateway** | SIP trunk management, PSTN interconnection |
| **Recording Service** | Call recording based on policy configuration |
| **CDR Service** | Call detail record generation, billing integration |

---

## Call Initiation Methods

### 1. Click-to-Dial via Salesforce CTI

Click-to-dial is implemented through the Salesforce Open CTI framework, allowing users to initiate calls directly from Salesforce records.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SALESFORCE CTI CLICK-TO-DIAL                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌─────────┐ │
│  │ Salesforce │───▶│  CTI       │───▶│ Middleware │───▶│ Natterbox│ │
│  │    UI      │    │ Softphone  │    │   (AWS)    │    │   API   │ │
│  └────────────┘    └────────────┘    └────────────┘    └────┬────┘ │
│        │                 │                 │                 │      │
│        │                 │                 │                 ▼      │
│        │                 │                 │           ┌─────────┐  │
│        │                 │                 └──────────▶│FreeSWITCH│ │
│        │                 │                             └─────────┘  │
│        │                 ▼                                          │
│        │           ┌────────────┐                                   │
│        └──────────▶│  WebPhone  │                                   │
│                    │  (WebRTC)  │                                   │
│                    └────────────┘                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Salesforce CTI Integration Objects

**API__c Custom Settings Object**

| Field | API Name | Type | Description |
|-------|----------|------|-------------|
| Host | `Host__c` | Text(255) | Production API host URL |
| Host Sandbox | `HostSandbox__c` | Text(255) | Sandbox API host URL |
| Client ID | `ClientId__c` | Text(255) | OAuth2 client ID for production |
| Client Secret | `ClientSecret__c` | Text(255) | OAuth2 client secret for production |
| Organization ID | `OrganizationId__c` | Number(18,0) | Natterbox organization identifier |
| SIP Domain | `SipDomain__c` | Text(255) | Organization SIP domain URL |

**Click-to-Dial Request Flow**

```javascript
// Salesforce CTI Click-to-Dial Implementation
sforce.opencti.onClickToDial({
    callback: function(result) {
        if (result.success) {
            var phoneNumber = result.number;
            var recordId = result.recordId;
            var objectType = result.objectType;
            
            // Initiate outbound call via Natterbox API
            initiateOutboundCall({
                destination: phoneNumber,
                callerId: getUserCallerId(),
                recordId: recordId,
                objectType: objectType
            });
        }
    }
});
```

#### Click-to-Dial API Request

**Endpoint:** `POST /v1/calls/originate`

**Request Body:**
```json
{
    "destination": "+441onal234567",
    "callerId": "+442012345678",
    "userId": 12345,
    "deviceId": 67890,
    "salesforceRecordId": "0012400000abcDEF",
    "salesforceObjectType": "Contact",
    "options": {
        "recordCall": true,
        "maxDuration": 3600,
        "callbackUrl": "https://callback.example.com/call-events"
    }
}
```

**Response:**
```json
{
    "success": true,
    "callId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "callUuid": "550e8400-e29b-41d4-a716-446655440000",
    "status": "initiated",
    "timestamp": "2026-01-20T10:30:00Z"
}
```

### 2. WebRTC Origination

WebRTC calls are initiated through the browser-based softphone using WebSocket signaling.

#### WebRTC Call Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEBRTC OUTBOUND CALL FLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐     ┌────────────┐     ┌───────────┐     ┌─────────────┐ │
│  │ Browser  │────▶│  WebSocket │────▶│  WebRTC   │────▶│ FreeSWITCH  │ │
│  │ WebPhone │     │    WSS     │     │  Gateway  │     │   Core      │ │
│  └──────────┘     └────────────┘     └───────────┘     └──────┬──────┘ │
│       │                │                   │                   │        │
│       │           SIP over WSS        SIP/RTP              SIP/RTP     │
│       │                │                   │                   │        │
│       ▼                ▼                   ▼                   ▼        │
│  ┌──────────┐     ┌────────────┐     ┌───────────┐     ┌─────────────┐ │
│  │ getUserMedia()│ │SIP REGISTER│    │  SRTP     │     │   LCR       │ │
│  │ Audio    │     │SIP INVITE  │     │  Media    │     │   Routing   │ │
│  └──────────┘     └────────────┘     └───────────┘     └─────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### WebRTC Device Registration

```javascript
// WebPhone Registration Flow
class WebPhoneClient {
    constructor(deviceId, password, domain) {
        this.deviceId = deviceId;
        this.password = password;
        this.domain = domain;
        this.wsUrl = `wss://webrtc.${domain}/ws`;
    }
    
    async register() {
        // Establish WSS connection
        this.websocket = new WebSocket(this.wsUrl);
        
        // Send SIP REGISTER
        const registerMessage = {
            method: 'REGISTER',
            headers: {
                'From': `sip:${this.deviceId}@${this.domain}`,
                'To': `sip:${this.deviceId}@${this.domain}`,
                'Contact': `<sip:${this.deviceId}@${this.domain};transport=ws>`,
                'Expires': 3600
            },
            auth: {
                username: this.deviceId,
                password: this.password
            }
        };
        
        return this.sendSipMessage(registerMessage);
    }
    
    async makeCall(destination) {
        const inviteMessage = {
            method: 'INVITE',
            requestUri: `sip:${destination}@${this.domain}`,
            headers: {
                'From': `sip:${this.deviceId}@${this.domain}`,
                'To': `sip:${destination}@${this.domain}`,
                'Contact': `<sip:${this.deviceId}@${this.domain};transport=ws>`
            },
            sdp: await this.createOffer()
        };
        
        return this.sendSipMessage(inviteMessage);
    }
}
```

### 3. Direct API Origination

External systems can initiate calls through the Natterbox REST API.

**Endpoint:** `POST /v1/originate`

**Authentication:** OAuth2 Bearer Token

**Request Headers:**
```http
POST /v1/originate HTTP/1.1
Host: api.natterbox.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json
X-Organization-Id: 12345
```

**Request Body Schema:**

```typescript
interface OriginateRequest {
    // Required fields
    destination: string;       // E.164 format destination number
    userId: number;            // Natterbox user ID initiating the call
    
    // Optional fields
    deviceId?: number;         // Specific device to use (defaults to user's primary)
    callerId?: string;         // Override caller ID (must be validated)
    displayName?: string;      // Caller name for presentation
    
    // Call options
    options?: {
        maxDuration?: number;      // Maximum call duration in seconds
        recordCall?: boolean;      // Enable call recording
        recordingPolicyId?: number; // Specific recording policy to apply
        timeout?: number;          // Ring timeout in seconds (default: 60)
        
        // Callback configuration
        callbackUrl?: string;      // URL for call event webhooks
        callbackEvents?: string[]; // Events to notify: ['answered', 'completed', 'failed']
        
        // Advanced options
        earlyMedia?: boolean;      // Enable early media detection
        answerConfirm?: boolean;   // Require answer confirmation (AMD)
        customHeaders?: Record<string, string>; // Custom SIP headers
    };
    
    // CRM integration
    salesforce?: {
        recordId?: string;         // Salesforce record ID for screen pop
        objectType?: string;       // Object type (Contact, Lead, Account)
        createTask?: boolean;      // Auto-create activity task
    };
}
```

**Response Schema:**

```typescript
interface OriginateResponse {
    success: boolean;
    callId: string;           // Internal call identifier
    callUuid: string;         // UUID for call tracking
    status: 'initiated' | 'ringing' | 'answered' | 'failed';
    timestamp: string;        // ISO 8601 timestamp
    
    // Error information (if failed)
    error?: {
        code: string;
        message: string;
        details?: Record<string, any>;
    };
}
```

**Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_DESTINATION` | 400 | Destination number format invalid |
| `USER_NOT_FOUND` | 404 | Specified user ID does not exist |
| `DEVICE_UNAVAILABLE` | 409 | User's device is not registered |
| `CALLER_ID_NOT_ALLOWED` | 403 | Requested caller ID not permitted |
| `QUOTA_EXCEEDED` | 429 | Call rate limit exceeded |
| `CARRIER_UNAVAILABLE` | 503 | No available carriers for route |

---

## Originate Command

### FreeSWITCH Originate Command Structure

The originate command is the core mechanism for initiating outbound calls in FreeSWITCH.

#### Basic Originate Syntax

```
originate <call_url> <exten>|&<application_name>(<app_args>) [<dialplan>] [<context>] [<cid_name>] [<cid_num>] [<timeout_sec>]
```

#### Natterbox Originate Implementation

```lua
-- Lua script for outbound call origination
function originate_outbound_call(params)
    -- Build dial string with channel variables
    local dial_string = string.format(
        "{origination_uuid=%s,origination_caller_id_number=%s,origination_caller_id_name=%s," ..
        "effective_caller_id_number=%s,effective_caller_id_name=%s," ..
        "sip_h_X-Natterbox-OrgId=%s,sip_h_X-Natterbox-UserId=%s," ..
        "sip_h_X-Natterbox-CallId=%s,ignore_early_media=%s," ..
        "call_timeout=%d,originate_timeout=%d}",
        params.call_uuid,
        params.caller_id_number,
        params.caller_id_name,
        params.effective_caller_id_number,
        params.effective_caller_id_name,
        params.org_id,
        params.user_id,
        params.call_id,
        params.ignore_early_media and "true" or "false",
        params.call_timeout or 60,
        params.originate_timeout or 120
    )
    
    -- Get LCR routes for destination
    local lcr_routes = get_lcr_routes(params.destination, params.org_id)
    
    -- Build gateway dial string with failover
    local gateway_string = build_gateway_string(lcr_routes, params.destination)
    
    -- Execute originate
    local full_dial_string = dial_string .. gateway_string
    
    return api:executeString("originate " .. full_dial_string .. " &bridge()")
end
```

#### Channel Variables for Outbound Calls

| Variable | Description | Example |
|----------|-------------|---------|
| `origination_uuid` | Pre-set UUID for the call | `550e8400-e29b-41d4-a716-446655440000` |
| `origination_caller_id_number` | A-leg caller ID number | `+442012345678` |
| `origination_caller_id_name` | A-leg caller ID name | `John Smith` |
| `effective_caller_id_number` | B-leg caller ID number | `+442012345678` |
| `effective_caller_id_name` | B-leg caller ID name | `Natterbox` |
| `sip_h_X-Natterbox-OrgId` | Organization ID header | `12345` |
| `sip_h_X-Natterbox-UserId` | User ID header | `67890` |
| `sip_h_X-Natterbox-CallId` | Call tracking ID | `abc123` |
| `call_timeout` | Ring timeout (seconds) | `60` |
| `originate_timeout` | Overall timeout (seconds) | `120` |
| `ignore_early_media` | Handle early media | `true` |
| `hangup_after_bridge` | Hangup on bridge end | `true` |
| `continue_on_fail` | Try next route on failure | `true` |
| `failure_causes` | Causes to trigger failover | `NORMAL_TEMPORARY_FAILURE,NO_ROUTE_DESTINATION` |

#### Bridge Application for Outbound Calls

```xml
<!-- FreeSWITCH dialplan for outbound calls -->
<extension name="outbound_call">
    <condition field="destination_number" expression="^(\d{10,15})$">
        <!-- Set call variables -->
        <action application="set" data="hangup_after_bridge=true"/>
        <action application="set" data="continue_on_fail=true"/>
        <action application="set" data="bypass_media=false"/>
        
        <!-- Apply caller ID rules -->
        <action application="lua" data="apply_caller_id_rules.lua"/>
        
        <!-- Get LCR route -->
        <action application="lcr" data="${destination_number}"/>
        
        <!-- Apply recording policy -->
        <action application="lua" data="apply_recording_policy.lua"/>
        
        <!-- Bridge to destination -->
        <action application="bridge" data="${lcr_auto_route}"/>
    </condition>
</extension>
```

---

## LCR (Least Cost Routing)

### LCR Service Architecture

The LCR service determines the optimal carrier route for outbound calls based on cost, quality, and availability.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LCR SERVICE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌────────────────┐    ┌─────────────────────────┐ │
│  │  FreeSWITCH  │───▶│   LCR Service  │───▶│      LCR Database       │ │
│  │   mod_lcr    │    │   (TypeScript) │    │   (PostgreSQL/MySQL)    │ │
│  └──────────────┘    └────────────────┘    └─────────────────────────┘ │
│         │                    │                         │                │
│         │                    ▼                         │                │
│         │           ┌────────────────┐                 │                │
│         │           │  Route Cache   │                 │                │
│         │           │    (Redis)     │                 │                │
│         │           └────────────────┘                 │                │
│         │                    │                         │                │
│         ▼                    ▼                         ▼                │
│  ┌──────────────┐    ┌────────────────┐    ┌─────────────────────────┐ │
│  │   Carrier    │    │   Rate Tables  │    │    Carrier Config       │ │
│  │   Gateway    │    │   & Prefixes   │    │    & Priorities         │ │
│  └──────────────┘    └────────────────┘    └─────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### LCR Service API

**Endpoint:** `POST /lcr/route`

**Request:**
```typescript
interface LcrRouteRequest {
    destination: string;           // E.164 destination number
    organizationId: number;        // Organization making the call
    userId?: number;               // Optional user ID for user-specific routing
    callType?: 'voice' | 'fax';    // Type of call
    options?: {
        maxRoutes?: number;        // Maximum routes to return (default: 5)
        includeRates?: boolean;    // Include rate information
        preferredCarriers?: string[]; // Prioritize specific carriers
        excludeCarriers?: string[];   // Exclude specific carriers
    };
}
```

**Response:**
```typescript
interface LcrRouteResponse {
    success: boolean;
    destination: string;
    normalizedDestination: string;
    countryCode: string;
    routes: LcrRoute[];
    cacheHit: boolean;
    lookupTimeMs: number;
}

interface LcrRoute {
    rank: number;                  // Route priority (1 = highest)
    carrierId: number;
    carrierName: string;
    gatewayId: number;
    gatewayName: string;
    dialString: string;            // FreeSWITCH dial string
    prefix: string;                // Matched prefix
    rate?: {
        perMinute: number;         // Cost per minute
        connectionFee: number;      // Connection fee
        currency: string;          // Currency code
        billingIncrement: number;   // Billing increment in seconds
    };
    quality?: {
        asr: number;               // Answer Seizure Ratio (%)
        acd: number;               // Average Call Duration (seconds)
        pdd: number;               // Post Dial Delay (ms)
    };
    constraints?: {
        maxCallDuration?: number;  // Maximum call duration
        timeRestrictions?: string[]; // Time-based restrictions
    };
}
```

### LCR Database Schema

#### lcr_profiles Table

```sql
CREATE TABLE lcr_profiles (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    organization_id INT NOT NULL,
    priority        INT DEFAULT 0,
    enabled         BOOLEAN DEFAULT true,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_organization 
        FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE INDEX idx_lcr_profiles_org ON lcr_profiles(organization_id);
CREATE INDEX idx_lcr_profiles_enabled ON lcr_profiles(enabled);
```

#### lcr_routes Table

```sql
CREATE TABLE lcr_routes (
    id              SERIAL PRIMARY KEY,
    profile_id      INT NOT NULL,
    carrier_id      INT NOT NULL,
    gateway_id      INT NOT NULL,
    prefix          VARCHAR(20) NOT NULL,
    priority        INT DEFAULT 0,
    weight          INT DEFAULT 1,
    enabled         BOOLEAN DEFAULT true,
    rate_per_minute DECIMAL(10, 6),
    connection_fee  DECIMAL(10, 6),
    currency        VARCHAR(3) DEFAULT 'GBP',
    billing_increment INT DEFAULT 60,
    
    -- Quality metrics
    asr             DECIMAL(5, 2),
    acd             INT,
    pdd             INT,
    
    -- Constraints
    max_channels    INT,
    max_call_duration INT,
    time_restrictions JSONB,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_profile 
        FOREIGN KEY (profile_id) 
        REFERENCES lcr_profiles(id) ON DELETE CASCADE,
    CONSTRAINT fk_carrier 
        FOREIGN KEY (carrier_id) 
        REFERENCES carriers(id),
    CONSTRAINT fk_gateway 
        FOREIGN KEY (gateway_id) 
        REFERENCES gateways(id)
);

CREATE INDEX idx_lcr_routes_profile ON lcr_routes(profile_id);
CREATE INDEX idx_lcr_routes_prefix ON lcr_routes(prefix);
CREATE INDEX idx_lcr_routes_carrier ON lcr_routes(carrier_id);
CREATE INDEX idx_lcr_routes_enabled ON lcr_routes(enabled);
CREATE INDEX idx_lcr_routes_priority ON lcr_routes(priority);
```

#### carriers Table

```sql
CREATE TABLE carriers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(50) UNIQUE NOT NULL,
    enabled         BOOLEAN DEFAULT true,
    max_channels    INT,
    current_channels INT DEFAULT 0,
    
    -- Carrier capabilities
    supports_cli_override BOOLEAN DEFAULT true,
    supports_fax    BOOLEAN DEFAULT false,
    supports_sms    BOOLEAN DEFAULT false,
    
    -- Failover settings
    failover_enabled BOOLEAN DEFAULT true,
    failover_threshold INT DEFAULT 3,
    failover_window INT DEFAULT 300,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### gateways Table

```sql
CREATE TABLE gateways (
    id              SERIAL PRIMARY KEY,
    carrier_id      INT NOT NULL,
    name            VARCHAR(255) NOT NULL,
    hostname        VARCHAR(255) NOT NULL,
    port            INT DEFAULT 5060,
    transport       VARCHAR(10) DEFAULT 'udp',
    
    -- Authentication
    auth_type       VARCHAR(20) DEFAULT 'none',
    username        VARCHAR(255),
    password        VARCHAR(255),
    realm           VARCHAR(255),
    
    -- Codec preferences
    codecs          VARCHAR(255) DEFAULT 'PCMA,PCMU,G729',
    
    -- Channel limits
    max_channels    INT,
    current_channels INT DEFAULT 0,
    
    -- Status
    enabled         BOOLEAN DEFAULT true,
    status          VARCHAR(20) DEFAULT 'active',
    last_health_check TIMESTAMP,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_carrier 
        FOREIGN KEY (carrier_id) 
        REFERENCES carriers(id) ON DELETE CASCADE
);

CREATE INDEX idx_gateways_carrier ON gateways(carrier_id);
CREATE INDEX idx_gateways_enabled ON gateways(enabled);
```

### LCR Route Selection Algorithm

```typescript
// LCR Service - Route Selection Logic
class LcrService {
    async getRoutes(request: LcrRouteRequest): Promise<LcrRouteResponse> {
        const startTime = Date.now();
        
        // 1. Normalize destination number
        const normalizedDest = this.normalizeNumber(request.destination);
        const countryCode = this.extractCountryCode(normalizedDest);
        
        // 2. Check cache first
        const cacheKey = `lcr:${request.organizationId}:${normalizedDest}`;
        const cachedRoutes = await this.cache.get(cacheKey);
        if (cachedRoutes) {
            return {
                success: true,
                destination: request.destination,
                normalizedDestination: normalizedDest,
                countryCode,
                routes: cachedRoutes,
                cacheHit: true,
                lookupTimeMs: Date.now() - startTime
            };
        }
        
        // 3. Get organization's LCR profile
        const profile = await this.getOrganizationProfile(request.organizationId);
        
        // 4. Find matching routes by prefix (longest prefix match)
        const routes = await this.findMatchingRoutes(
            profile.id,
            normalizedDest,
            request.options
        );
        
        // 5. Sort routes by priority, cost, and quality
        const sortedRoutes = this.sortRoutes(routes, profile.routingStrategy);
        
        // 6. Apply carrier exclusions and preferences
        const filteredRoutes = this.applyCarrierFilters(
            sortedRoutes,
            request.options?.preferredCarriers,
            request.options?.excludeCarriers
        );
        
        // 7. Check channel availability
        const availableRoutes = await this.filterByChannelAvailability(filteredRoutes);
        
        // 8. Limit results
        const maxRoutes = request.options?.maxRoutes || 5;
        const finalRoutes = availableRoutes.slice(0, maxRoutes);
        
        // 9. Build dial strings
        const routesWithDialStrings = finalRoutes.map((route, index) => ({
            ...route,
            rank: index + 1,
            dialString: this.buildDialString(route, normalizedDest)
        }));
        
        // 10. Cache results
        await this.cache.set(cacheKey, routesWithDialStrings, 300); // 5 minute TTL
        
        return {
            success: true,
            destination: request.destination,
            normalizedDestination: normalizedDest,
            countryCode,
            routes: routesWithDialStrings,
            cacheHit: false,
            lookupTimeMs: Date.now() - startTime
        };
    }
    
    private sortRoutes(routes: LcrRoute[], strategy: RoutingStrategy): LcrRoute[] {
        switch (strategy) {
            case 'LOWEST_COST':
                return routes.sort((a, b) => {
                    // Primary: cost per minute
                    const costDiff = (a.rate?.perMinute || 0) - (b.rate?.perMinute || 0);
                    if (costDiff !== 0) return costDiff;
                    // Secondary: priority
                    return a.priority - b.priority;
                });
                
            case 'HIGHEST_QUALITY':
                return routes.sort((a, b) => {
                    // Primary: ASR (higher is better)
                    const asrDiff = (b.quality?.asr || 0) - (a.quality?.asr || 0);
                    if (Math.abs(asrDiff) > 5) return asrDiff > 0 ? 1 : -1;
                    // Secondary: PDD (lower is better)
                    return (a.quality?.pdd || 999) - (b.quality?.pdd || 999);
                });
                
            case 'PRIORITY':
            default:
                return routes.sort((a, b) => a.priority - b.priority);
        }
    }
    
    private buildDialString(route: LcrRoute, destination: string): string {
        const gateway = route.gateway;
        
        // Build Sofia dial string for FreeSWITCH
        return `sofia/gateway/${gateway.name}/${destination}`;
    }
}
```

### mod_lcr Configuration

**FreeSWITCH mod_lcr Configuration:**

```xml
<!-- conf/autoload_configs/lcr.conf.xml -->
<configuration name="lcr.conf" description="LCR Configuration">
    <settings>
        <!-- Database connection -->
        <param name="odbc-dsn" value="natterbox:natterbox:password"/>
        
        <!-- LCR behavior settings -->
        <param name="lcr_default_profile" value="default"/>
        <param name="lcr_cache_expire" value="300"/>
        
        <!-- Custom SQL queries -->
        <param name="lcr_sql" value="
            SELECT 
                l.prefix,
                c.name AS carrier_name,
                g.name AS gateway_name,
                l.priority,
                l.weight,
                l.rate_per_minute,
                CONCAT('sofia/gateway/', g.name, '/', '${lcr_digits}') AS dial_string
            FROM lcr_routes l
            JOIN carriers c ON l.carrier_id = c.id
            JOIN gateways g ON l.gateway_id = g.id
            WHERE l.enabled = true
              AND c.enabled = true
              AND g.enabled = true
              AND '${lcr_digits}' LIKE CONCAT(l.prefix, '%')
            ORDER BY 
                LENGTH(l.prefix) DESC,
                l.priority ASC,
                l.weight DESC
        "/>
    </settings>
    
    <profiles>
        <profile name="default">
            <param name="order_by" value="priority, rate"/>
            <param name="reorder_by_rate" value="true"/>
            <param name="quote_in_list" value="false"/>
        </profile>
    </profiles>
</configuration>
```

---

## Carrier Gateway Selection

### Gateway Selection Logic

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GATEWAY SELECTION DECISION FLOW                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐                                                         │
│  │ LCR Routes  │                                                         │
│  │  Returned   │                                                         │
│  └──────┬──────┘                                                         │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────────┐    YES    ┌─────────────────┐                      │
│  │ Gateway Health  │──────────▶│   Use Gateway   │                      │
│  │    OK?          │           │                 │                      │
│  └────────┬────────┘           └─────────────────┘                      │
│           │ NO                                                           │
│           ▼                                                              │
│  ┌─────────────────┐    YES    ┌─────────────────┐                      │
│  │ Channels        │──────────▶│   Use Gateway   │                      │
│  │ Available?      │           │                 │                      │
│  └────────┬────────┘           └─────────────────┘                      │
│           │ NO                                                           │
│           ▼                                                              │
│  ┌─────────────────┐    YES    ┌─────────────────┐                      │
│  │ More Routes?    │──────────▶│   Try Next      │                      │
│  │                 │           │   Route         │                      │
│  └────────┬────────┘           └────────┬────────┘                      │
│           │ NO                          │                                │
│           ▼                             │                                │
│  ┌─────────────────┐                    │                                │
│  │ Return Error:   │◀───────────────────┘                                │
│  │ NO_ROUTE_       │                                                     │
│  │ DESTINATION     │                                                     │
│  └─────────────────┘                                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Gateway Health Monitoring

```typescript
// Gateway Health Check Service
class GatewayHealthService {
    private healthStatus: Map<number, GatewayHealth> = new Map();
    
    async checkGatewayHealth(gatewayId: number): Promise<GatewayHealth> {
        const gateway = await this.gatewayRepo.findById(gatewayId);
        
        // 1. Check SIP OPTIONS response
        const sipOptionsResult = await this.sendSipOptions(gateway);
        
        // 2. Check recent call statistics
        const recentStats = await this.getRecentCallStats(gatewayId, 300); // Last 5 minutes
        
        // 3. Calculate health score
        const healthScore = this.calculateHealthScore({
            sipResponseTime: sipOptionsResult.responseTime,
            sipResponseCode: sipOptionsResult.code,
            asr: recentStats.asr,
            failureRate: recentStats.failureRate,
            activeChannels: gateway.currentChannels,
            maxChannels: gateway.maxChannels
        });
        
        const health: GatewayHealth = {
            gatewayId,
            status: healthScore >= 70 ? 'healthy' : healthScore >= 40 ? 'degraded' : 'unhealthy',
            score: healthScore,
            lastCheck: new Date(),
            metrics: {
                sipResponseTime: sipOptionsResult.responseTime,
                asr: recentStats.asr,
                activeChannels: gateway.currentChannels,
                availableChannels: gateway.maxChannels - gateway.currentChannels
            }
        };
        
        this.healthStatus.set(gatewayId, health);
        return health;
    }
    
    private calculateHealthScore(metrics: HealthMetrics): number {
        let score = 100;
        
        // SIP OPTIONS response time penalty
        if (metrics.sipResponseTime > 500) score -= 20;
        else if (metrics.sipResponseTime > 200) score -= 10;
        
        // ASR penalty (Answer Seizure Ratio)
        if (metrics.asr < 50) score -= 30;
        else if (metrics.asr < 70) score -= 15;
        
        // Failure rate penalty
        if (metrics.failureRate > 20) score -= 25;
        else if (metrics.failureRate > 10) score -= 10;
        
        // Channel utilization penalty
        const channelUtilization = metrics.activeChannels / metrics.maxChannels;
        if (channelUtilization > 0.95) score -= 20;
        else if (channelUtilization > 0.85) score -= 10;
        
        return Math.max(0, score);
    }
}
```

### Failover Configuration

```typescript
interface FailoverConfig {
    enabled: boolean;
    strategy: 'sequential' | 'round_robin' | 'weighted';
    
    // Failure detection
    failureThreshold: number;        // Consecutive failures before failover
    failureWindow: number;           // Time window for failure counting (seconds)
    
    // Recovery
    recoveryStrategy: 'automatic' | 'manual';
    recoveryCheckInterval: number;   // Seconds between recovery checks
    recoveryThreshold: number;       // Successful checks before recovery
    
    // Causes that trigger failover
    failoverCauses: string[];        // SIP response codes or Q.850 causes
}

// Default failover configuration
const defaultFailoverConfig: FailoverConfig = {
    enabled: true,
    strategy: 'sequential',
    failureThreshold: 3,
    failureWindow: 300,
    recoveryStrategy: 'automatic',
    recoveryCheckInterval: 60,
    recoveryThreshold: 5,
    failoverCauses: [
        'NORMAL_TEMPORARY_FAILURE',
        'NO_ROUTE_DESTINATION',
        'NETWORK_OUT_OF_ORDER',
        'SERVICE_UNAVAILABLE',
        'SWITCH_CONGESTION',
        'USER_BUSY'  // Only for carrier-level congestion
    ]
};
```

---

## Outbound Caller ID Manipulation

### Caller ID Rule Types

The platform supports multiple levels of caller ID manipulation:

1. **Organization-level defaults**
2. **User-level settings**
3. **Number-level overrides**
4. **Call-specific parameters**

### Caller ID Manipulation Logic

```php
<?php
// SE_Modify_Channel_Props.php - Caller ID Manipulation

class SE_Modify_Channel_Props {
    
    /**
     * Apply caller ID rules for outbound calls
     */
    public function applyCallerIdRules(array $params): array {
        $orgId = $params['org_id'];
        $userId = $params['user_id'];
        $destination = $params['destination'];
        $requestedCallerId = $params['requested_caller_id'] ?? null;
        
        // 1. Get organization default settings
        $orgSettings = $this->getOrganizationSettings($orgId);
        
        // 2. Get user settings (may override org defaults)
        $userSettings = $this->getUserSettings($userId);
        
        // 3. Determine base caller ID
        $callerId = $this->determineCallerId(
            $orgSettings,
            $userSettings,
            $requestedCallerId
        );
        
        // 4. Apply destination-specific rules
        $callerId = $this->applyDestinationRules($callerId, $destination, $orgId);
        
        // 5. Validate caller ID is allowed
        if (!$this->validateCallerId($callerId, $orgId, $userId)) {
            // Fall back to organization default
            $callerId = $orgSettings['default_caller_id'];
        }
        
        // 6. Apply CLIR (Calling Line Identification Restriction) if needed
        $presentation = $this->getCallerIdPresentation($userSettings);
        
        return [
            'caller_id_number' => $callerId,
            'caller_id_name' => $this->getCallerIdName($userSettings, $orgSettings),
            'presentation' => $presentation,
            'privacy' => $presentation === 'withheld' ? 'id' : 'none'
        ];
    }
    
    /**
     * Determine the caller ID based on hierarchy
     */
    private function determineCallerId(
        array $orgSettings,
        array $userSettings,
        ?string $requestedCallerId
    ): string {
        // Priority: Requested > User > Organization
        
        if ($requestedCallerId && $this->isValidE164($requestedCallerId)) {
            return $requestedCallerId;
        }
        
        if (!empty($userSettings['external_caller_id_number'])) {
            return $userSettings['external_caller_id_number'];
        }
        
        if (!empty($userSettings['ddi_number'])) {
            return $userSettings['ddi_number'];
        }
        
        return $orgSettings['default_caller_id'] ?? $orgSettings['main_number'];
    }
    
    /**
     * Apply destination-specific caller ID rules
     */
    private function applyDestinationRules(
        string $callerId,
        string $destination,
        int $orgId
    ): string {
        // Get destination country
        $destCountry = $this->getCountryFromNumber($destination);
        $callerCountry = $this->getCountryFromNumber($callerId);
        
        // Check if we need a local presence number
        $localPresenceRules = $this->getLocalPresenceRules($orgId, $destCountry);
        
        if ($localPresenceRules && $destCountry !== $callerCountry) {
            // Use local presence number for this destination country
            $localNumber = $this->getLocalPresenceNumber($orgId, $destCountry);
            if ($localNumber) {
                return $localNumber;
            }
        }
        
        return $callerId;
    }
    
    /**
     * Validate caller ID is allowed for organization/user
     */
    private function validateCallerId(
        string $callerId,
        int $orgId,
        int $userId
    ): bool {
        // Check if number belongs to organization
        $orgNumbers = $this->getOrganizationNumbers($orgId);
        if (in_array($callerId, $orgNumbers)) {
            return true;
        }
        
        // Check if user has permission for this number
        $userNumbers = $this->getUserAllowedNumbers($userId);
        if (in_array($callerId, $userNumbers)) {
            return true;
        }
        
        // Check carrier allowlist
        $carrierAllowed = $this->isCarrierAllowedCli($callerId, $orgId);
        
        return $carrierAllowed;
    }
}
```

### Channel Variable Configuration for Caller ID

```xml
<!-- FreeSWITCH Dialplan - Caller ID Configuration -->
<extension name="set_outbound_caller_id">
    <condition field="direction" expression="outbound">
        <!-- Set effective caller ID -->
        <action application="set" 
                data="effective_caller_id_number=${caller_id_number}"/>
        <action application="set" 
                data="effective_caller_id_name=${caller_id_name}"/>
        
        <!-- Set SIP From header -->
        <action application="set" 
                data="sip_from_display=${caller_id_name}"/>
        <action application="set" 
                data="sip_from_user=${caller_id_number}"/>
        
        <!-- Set P-Asserted-Identity header -->
        <action application="set" 
                data="sip_h_P-Asserted-Identity=<sip:${caller_id_number}@${domain}>"/>
        
        <!-- Handle CLIR/Privacy -->
        <action application="set" 
                data="sip_h_Privacy=${privacy_header}"/>
        <action application="set" 
                data="privacy=${privacy_setting}"/>
        
        <!-- Remote Party ID header (some carriers) -->
        <action application="set" 
                data="sip_h_Remote-Party-ID=<sip:${caller_id_number}@${domain}>;party=calling;privacy=${privacy_rpid};screen=yes"/>
    </condition>
</extension>
```

### Caller ID Validation API

**Endpoint:** `POST /v1/caller-id/validate`

**Request:**
```json
{
    "number": "+442012345678",
    "organizationId": 12345,
    "userId": 67890,
    "purpose": "outbound_call"
}
```

**Response:**
```json
{
    "valid": true,
    "number": "+442012345678",
    "normalized": "+442012345678",
    "ownership": {
        "type": "organization",
        "verified": true,
        "verificationDate": "2025-06-15T10:00:00Z"
    },
    "restrictions": [],
    "carrierSupport": {
        "bt_wholesale": true,
        "vonage": true,
        "twilio": true
    }
}
```

---

## PSTN Egress

### SIP Trunk Configuration

```xml
<!-- FreeSWITCH Sofia Gateway Configuration -->
<!-- conf/sip_profiles/external/carrier_gateway.xml -->

<include>
    <gateway name="carrier_primary">
        <param name="realm" value="sip.carrier.example.com"/>
        <param name="proxy" value="sip.carrier.example.com:5060"/>
        <param name="transport" value="tcp"/>
        
        <!-- Authentication -->
        <param name="username" value="natterbox_trunk"/>
        <param name="password" value="secure_password"/>
        <param name="register" value="false"/>
        <param name="auth-username" value="natterbox_trunk"/>
        
        <!-- Caller ID handling -->
        <param name="caller-id-in-from" value="true"/>
        
        <!-- Codec preferences -->
        <param name="codec-prefs" value="PCMA,PCMU,G729"/>
        
        <!-- Channel limits -->
        <param name="max-calls" value="100"/>
        
        <!-- Timers -->
        <param name="retry-seconds" value="30"/>
        <param name="ping" value="25"/>
        
        <!-- Headers -->
        <param name="contact-params" value="tport=tcp"/>
    </gateway>
    
    <gateway name="carrier_secondary">
        <param name="realm" value="sip2.carrier.example.com"/>
        <param name="proxy" value="sip2.carrier.example.com:5060"/>
        <param name="transport" value="udp"/>
        <param name="username" value="natterbox_backup"/>
        <param name="password" value="backup_password"/>
        <param name="register" value="false"/>
        <param name="codec-prefs" value="PCMA,PCMU"/>
        <param name="max-calls" value="50"/>
    </gateway>
</include>
```

### PSTN Egress Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PSTN EGRESS FLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  FreeSWITCH                  Carrier Gateway              PSTN           │
│      │                            │                        │             │
│      │  SIP INVITE               │                        │             │
│      │  To: +442012345678        │                        │             │
│      │  From: +441onal234567     │                        │             │
│      │──────────────────────────▶│                        │             │
│      │                            │                        │             │
│      │  100 Trying               │                        │             │
│      │◀──────────────────────────│                        │             │
│      │                            │  ISUP IAM             │             │
│      │                            │──────────────────────▶│             │
│      │                            │                        │             │
│      │                            │  ISUP ACM             │             │
│      │  183 Session Progress     │◀──────────────────────│             │
│      │◀──────────────────────────│                        │             │
│      │                            │                        │             │
│      │  (Early Media/Ringback)   │                        │             │
│      │◀ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ │                        │             │
│      │                            │  ISUP ANM             │             │
│      │  200 OK                   │◀──────────────────────│             │
│      │◀──────────────────────────│                        │             │
│      │                            │                        │             │
│      │  ACK                      │                        │             │
│      │──────────────────────────▶│                        │             │
│      │                            │                        │             │
│      │  ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ RTP MEDIA ═ ═ ═ ═ ═ ═│             │
│      │                            │                        │             │
│      │  BYE                      │                        │             │
│      │──────────────────────────▶│  ISUP REL             │             │
│      │                            │──────────────────────▶│             │
│      │  200 OK                   │  ISUP RLC             │             │
│      │◀──────────────────────────│◀──────────────────────│             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Multi-Gateway Dial String for Failover

```lua
-- Build failover dial string
function build_failover_dial_string(routes, destination)
    local dial_strings = {}
    
    for i, route in ipairs(routes) do
        local gateway = route.gateway_name
        local dial_string = string.format(
            "[leg_%d=true,failure_causes='%s']sofia/gateway/%s/%s",
            i,
            get_failover_causes(),
            gateway,
            destination
        )
        table.insert(dial_strings, dial_string)
    end
    
    -- Join with pipe for sequential failover
    return table.concat(dial_strings, "|")
end

-- Example output:
-- [leg_1=true,failure_causes='NORMAL_TEMPORARY_FAILURE']sofia/gateway/carrier_primary/+442012345678|
-- [leg_2=true,failure_causes='NORMAL_TEMPORARY_FAILURE']sofia/gateway/carrier_secondary/+442012345678|
-- [leg_3=true,failure_causes='NORMAL_TEMPORARY_FAILURE']sofia/gateway/carrier_tertiary/+442012345678
```

---

## Call Progress Detection

### Answer Machine Detection (AMD)

```xml
<!-- FreeSWITCH AMD Configuration -->
<extension name="outbound_with_amd">
    <condition field="destination_number" expression="^(\d+)$">
        <!-- Enable AMD -->
        <action application="set" data="execute_on_answer=detect_speech"/>
        <action application="set" data="amd_enabled=true"/>
        
        <!-- AMD parameters -->
        <action application="set" data="amd_maximum_word_length=5000"/>
        <action application="set" data="amd_maximum_number_of_words=3"/>
        <action application="set" data="amd_silence_threshold=256"/>
        <action application="set" data="amd_between_words_silence=50"/>
        <action application="set" data="amd_min_word_length=100"/>
        <action application="set" data="amd_total_analysis_time=5000"/>
        
        <!-- Bridge with AMD -->
        <action application="bridge" data="${lcr_auto_route}"/>
        
        <!-- Handle AMD result -->
        <action application="lua" data="handle_amd_result.lua"/>
    </condition>
</extension>
```

### Call Progress Tones

```lua
-- Call progress tone detection
local progress_tones = {
    -- UK tones
    uk_dial = "%(350)425",
    uk_ringback = "%(400,200,400,2000)400+450",
    uk_busy = "%(375,375)400",
    uk_congestion = "%(400,350,225,525)400",
    
    -- US tones
    us_dial = "%(1000)350+440",
    us_ringback = "%(2000,4000)440+480",
    us_busy = "%(500,500)480+620",
    
    -- European tones
    eu_ringback = "%(1000,4000)425"
}

function detect_call_progress(session)
    -- Start tone detection
    session:execute("start_tone_detect", "ring_back")
    
    -- Wait for progress indication
    local timeout = 30000  -- 30 seconds
    local start_time = os.time()
    
    while (os.time() - start_time) < timeout do
        local tone = session:getVariable("detected_tone")
        
        if tone == "ANSWER" then
            return "answered"
        elseif tone == "BUSY" then
            return "busy"
        elseif tone == "CONGESTION" then
            return "congestion"
        end
        
        session:sleep(100)
    end
    
    return "no_answer"
end
```

---

## Recording Policies

### Recording Policy Configuration

```typescript
interface RecordingPolicy {
    id: number;
    organizationId: number;
    name: string;
    enabled: boolean;
    
    // Recording scope
    scope: {
        type: 'all' | 'inbound' | 'outbound' | 'specific';
        users?: number[];
        groups?: number[];
        numbers?: string[];
    };
    
    // Recording settings
    settings: {
        format: 'wav' | 'mp3' | 'ogg';
        channels: 'mono' | 'stereo' | 'split';  // split = separate A/B legs
        sampleRate: 8000 | 16000 | 44100;
        
        // Start recording
        startOn: 'answer' | 'ring' | 'immediate';
        
        // Announcement
        announcement?: {
            enabled: boolean;
            audioFileId?: number;
            playTo: 'all' | 'external_only' | 'internal_only';
        };
        
        // Pause/resume
        pauseOnHold: boolean;
        pauseDigits?: string;  // DTMF digits to pause recording
        resumeDigits?: string; // DTMF digits to resume recording
    };
    
    // Storage settings
    storage: {
        retention: number;      // Days to retain recordings
        archivePolicy?: number; // Archive policy ID
        encryptAtRest: boolean;
    };
    
    // Compliance
    compliance: {
        pciEnabled: boolean;    // Pause during PCI transactions
        gdprEnabled: boolean;   // GDPR consent handling
        consentRequired: boolean;
    };
}
```

### Recording Implementation in Dialplan

```xml
<!-- FreeSWITCH Recording Dialplan -->
<extension name="apply_recording_policy">
    <condition field="${recording_enabled}" expression="^true$">
        <!-- Set recording variables -->
        <action application="set" 
                data="RECORD_TITLE=${uuid}"/>
        <action application="set" 
                data="RECORD_ARTIST=${caller_id_number}"/>
        <action application="set" 
                data="RECORD_DATE=${strftime(%Y-%m-%d)}"/>
        
        <!-- Recording path -->
        <action application="set" 
                data="record_path=/recordings/${org_id}/${strftime(%Y/%m/%d)}"/>
        <action application="set" 
                data="record_file=${record_path}/${uuid}.wav"/>
        
        <!-- Start recording -->
        <action application="record_session" 
                data="${record_file}"/>
        
        <!-- Play announcement if configured -->
        <action application="lua" 
                data="play_recording_announcement.lua" 
                condition="${recording_announcement}" 
                expression="^true$"/>
    </condition>
</extension>
```

### Recording Storage Integration

```typescript
// Recording upload to storage
class RecordingStorageService {
    async uploadRecording(recording: RecordingFile): Promise<StorageResult> {
        // 1. Generate unique storage key
        const storageKey = `${recording.orgId}/${recording.date}/${recording.uuid}.${recording.format}`;
        
        // 2. Encrypt if required
        let content = recording.content;
        if (recording.encryptAtRest) {
            content = await this.encryptionService.encrypt(content, recording.orgId);
        }
        
        // 3. Upload to S3
        const result = await this.s3Client.upload({
            Bucket: this.config.recordingBucket,
            Key: storageKey,
            Body: content,
            ContentType: this.getContentType(recording.format),
            Metadata: {
                'x-nb-org-id': String(recording.orgId),
                'x-nb-call-uuid': recording.uuid,
                'x-nb-caller': recording.callerNumber,
                'x-nb-callee': recording.calleeNumber,
                'x-nb-duration': String(recording.duration),
                'x-nb-encrypted': String(recording.encryptAtRest)
            },
            ServerSideEncryption: 'AES256'
        });
        
        // 4. Create database record
        await this.recordingRepo.create({
            uuid: recording.uuid,
            orgId: recording.orgId,
            callUuid: recording.callUuid,
            storageKey,
            duration: recording.duration,
            format: recording.format,
            size: recording.content.length,
            createdAt: new Date()
        });
        
        return {
            success: true,
            storageKey,
            url: result.Location
        };
    }
}
```

---

## CDR Generation and Billing

### CDR (Call Detail Record) Schema

```sql
-- CDR Table Schema
CREATE TABLE call_detail_records (
    id                  BIGSERIAL PRIMARY KEY,
    uuid                UUID NOT NULL UNIQUE,
    organization_id     INT NOT NULL,
    
    -- Call identification
    call_id             VARCHAR(64),
    parent_uuid         UUID,  -- For transfers/conferences
    
    -- Timestamps
    start_time          TIMESTAMP NOT NULL,
    answer_time         TIMESTAMP,
    end_time            TIMESTAMP NOT NULL,
    progress_time       TIMESTAMP,
    
    -- Duration
    duration_seconds    INT NOT NULL DEFAULT 0,
    billable_seconds    INT NOT NULL DEFAULT 0,
    ring_duration       INT DEFAULT 0,
    
    -- Direction
    direction           VARCHAR(20) NOT NULL,  -- 'inbound', 'outbound', 'internal'
    
    -- Parties
    caller_number       VARCHAR(32),
    caller_name         VARCHAR(128),
    caller_user_id      INT,
    callee_number       VARCHAR(32),
    callee_name         VARCHAR(128),
    callee_user_id      INT,
    dialed_number       VARCHAR(32),
    
    -- Routing
    gateway_id          INT,
    gateway_name        VARCHAR(128),
    carrier_id          INT,
    carrier_name        VARCHAR(128),
    lcr_profile_id      INT,
    
    -- Call result
    hangup_cause        VARCHAR(64),
    hangup_cause_q850   INT,
    sip_term_status     VARCHAR(10),
    disposition         VARCHAR(32),  -- 'ANSWERED', 'NO_ANSWER', 'BUSY', 'FAILED'
    
    -- Recording
    recording_uuid      UUID,
    recording_duration  INT,
    recording_path      VARCHAR(512),
    
    -- Billing
    rate_per_minute     DECIMAL(10, 6),
    connection_fee      DECIMAL(10, 6),
    total_cost          DECIMAL(10, 6),
    currency            VARCHAR(3) DEFAULT 'GBP',
    billing_increment   INT DEFAULT 60,
    
    -- Quality metrics
    mos_score           DECIMAL(3, 2),
    jitter_avg          INT,
    packet_loss_pct     DECIMAL(5, 2),
    
    -- Custom data
    custom_data         JSONB,
    salesforce_task_id  VARCHAR(20),
    
    -- Metadata
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed           BOOLEAN DEFAULT FALSE,
    processed_at        TIMESTAMP,
    
    CONSTRAINT fk_organization 
        FOREIGN KEY (organization_id) 
        REFERENCES organizations(id),
    CONSTRAINT fk_gateway 
        FOREIGN KEY (gateway_id) 
        REFERENCES gateways(id),
    CONSTRAINT fk_carrier 
        FOREIGN KEY (carrier_id) 
        REFERENCES carriers(id)
);

-- Indexes
CREATE INDEX idx_cdr_org_time ON call_detail_records(organization_id, start_time);
CREATE INDEX idx_cdr_uuid ON call_detail_records(uuid);
CREATE INDEX idx_cdr_caller ON call_detail_records(caller_number);
CREATE INDEX idx_cdr_callee ON call_detail_records(callee_number);
CREATE INDEX idx_cdr_user ON call_detail_records(caller_user_id);
CREATE INDEX idx_cdr_gateway ON call_detail_records(gateway_id);
CREATE INDEX idx_cdr_disposition ON call_detail_records(disposition);
CREATE INDEX idx_cdr_processed ON call_detail_records(processed);
```

### Salesforce Call Reporting Object

**CallReporting__c Object Fields:**

| Field Name | API Name | Type | Description |
|------------|----------|------|-------------|
| Call Direction | `Call_Direction__c` | Picklist | Inbound, Outbound, External, Service |
| From Number | `From_Number__c` | Text(32) | Normalized caller number |
| To Number | `To_Number__c` | Text(32) | Normalized destination number |
| From UUID | `From_UUID__c` | Text(64) | A-leg channel UUID |
| To UUID | `To_UUID__c` | Text(64) | B-leg channel UUID |
| From Start Time | `From_Start_Time__c` | DateTime | Call initiation time |
| From Answer Time | `From_Answer_Time__c` | DateTime | Call answer time |
| From End Time | `From_End_Time__c` | DateTime | Call end time |
| From Time Talking | `From_Time_Talking__c` | Number | Talk duration in seconds |
| From Time Ringing | `From_Time_Ringing__c` | Number | Ring duration in seconds |
| From Hangup Cause | `From_Hangup_Cause__c` | Text(32) | Hangup cause code |
| From AVS User | `From_AVS_User__c` | Lookup(User__c) | Originating Natterbox user |
| To AVS User | `To_AVS_User__c` | Lookup(User__c) | Receiving Natterbox user |
| From Flag Record | `From_Flag_Record__c` | Checkbox | Recording exists flag |
| Recording URL | `RecordingURL1__c` | URL | A-leg recording URL |
| Account | `Account__c` | Lookup(Account) | Related Salesforce Account |
| Contact | `Contact__c` | Lookup(Contact) | Related Salesforce Contact |
| Lead | `Lead__c` | Lookup(Lead) | Related Salesforce Lead |

### CDR Processing Pipeline

```typescript
// CDR Processing Service
class CdrProcessingService {
    async processCallEnd(event: CallEndEvent): Promise<void> {
        // 1. Build CDR from call event
        const cdr = this.buildCdr(event);
        
        // 2. Calculate billing
        cdr.billing = await this.calculateBilling(cdr);
        
        // 3. Store CDR
        await this.cdrRepository.create(cdr);
        
        // 4. Update Salesforce Call Reporting
        await this.updateSalesforceCallReporting(cdr);
        
        // 5. Update billing/usage metrics
        await this.updateUsageMetrics(cdr);
        
        // 6. Send to billing system
        if (cdr.billing.totalCost > 0) {
            await this.billingQueue.enqueue(cdr);
        }
        
        // 7. Send webhook if configured
        await this.sendCallEndWebhook(cdr);
    }
    
    private async calculateBilling(cdr: Cdr): Promise<BillingInfo> {
        // Get rate for this route
        const rate = await this.rateService.getRate(
            cdr.organizationId,
            cdr.destination,
            cdr.gatewayId
        );
        
        // Calculate billable duration
        const billableSeconds = this.calculateBillableSeconds(
            cdr.durationSeconds,
            rate.billingIncrement
        );
        
        // Calculate cost
        const minuteCost = (billableSeconds / 60) * rate.perMinute;
        const totalCost = minuteCost + rate.connectionFee;
        
        return {
            ratePerMinute: rate.perMinute,
            connectionFee: rate.connectionFee,
            billableSeconds,
            totalCost,
            currency: rate.currency,
            billingIncrement: rate.billingIncrement
        };
    }
    
    private calculateBillableSeconds(duration: number, increment: number): number {
        if (duration === 0) return 0;
        return Math.ceil(duration / increment) * increment;
    }
}
```

### Hourly Call Reporting Aggregation

```sql
-- Hourly aggregation for reporting
INSERT INTO hourly_call_reporting (
    time_bucket,
    organization_id,
    user_id,
    inbound_calls,
    outbound_calls,
    internal_calls,
    inbound_talk_seconds,
    outbound_talk_seconds,
    inbound_connected_primary,
    outbound_connected_primary,
    total_cost
)
SELECT 
    date_trunc('hour', start_time) AS time_bucket,
    organization_id,
    caller_user_id AS user_id,
    COUNT(*) FILTER (WHERE direction = 'inbound') AS inbound_calls,
    COUNT(*) FILTER (WHERE direction = 'outbound') AS outbound_calls,
    COUNT(*) FILTER (WHERE direction = 'internal') AS internal_calls,
    SUM(duration_seconds) FILTER (WHERE direction = 'inbound') AS inbound_talk_seconds,
    SUM(duration_seconds) FILTER (WHERE direction = 'outbound') AS outbound_talk_seconds,
    COUNT(*) FILTER (WHERE direction = 'inbound' AND disposition = 'ANSWERED') AS inbound_connected_primary,
    COUNT(*) FILTER (WHERE direction = 'outbound' AND disposition = 'ANSWERED') AS outbound_connected_primary,
    SUM(total_cost) AS total_cost
FROM call_detail_records
WHERE start_time >= NOW() - INTERVAL '1 hour'
  AND NOT processed
GROUP BY 
    date_trunc('hour', start_time),
    organization_id,
    caller_user_id;
```

---

## Error Handling

### Error Codes and Handling

| Error Code | SIP Code | Q.850 Cause | Description | Action |
|------------|----------|-------------|-------------|--------|
| `NO_ROUTE_DESTINATION` | 404 | 3 | No route to destination | Return error to caller |
| `USER_BUSY` | 486 | 17 | Destination busy | Retry or failover |
| `NO_ANSWER` | 480 | 18 | No answer within timeout | Return no answer |
| `CALL_REJECTED` | 603 | 21 | Call rejected by destination | Return error |
| `NORMAL_TEMPORARY_FAILURE` | 503 | 41 | Temporary carrier failure | Failover to next route |
| `NETWORK_OUT_OF_ORDER` | 503 | 38 | Network issue | Failover to next route |
| `RECOVERY_ON_TIMER_EXPIRE` | 408 | 102 | Request timeout | Failover to next route |
| `GATEWAY_DOWN` | 503 | 27 | Gateway unavailable | Failover to next route |
| `INVALID_NUMBER_FORMAT` | 400 | 28 | Invalid destination format | Return error |
| `CALLER_ID_NOT_ALLOWED` | 403 | - | CLI validation failed | Use default CLI |
| `QUOTA_EXCEEDED` | 429 | - | Rate limit exceeded | Return error |
| `CHANNEL_UNAVAILABLE` | 503 | 34 | No available channels | Failover or queue |

### Error Handling Implementation

```lua
-- Error handling in FreeSWITCH
function handle_bridge_failure(session)
    local hangup_cause = session:getVariable("last_bridge_hangup_cause")
    local sip_status = session:getVariable("sip_term_status")
    
    -- Log the failure
    freeswitch.consoleLog("WARNING", 
        "Bridge failed: cause=" .. (hangup_cause or "unknown") .. 
        " sip_status=" .. (sip_status or "unknown"))
    
    -- Determine if we should failover
    local failover_causes = {
        "NORMAL_TEMPORARY_FAILURE",
        "NO_ROUTE_DESTINATION",
        "NETWORK_OUT_OF_ORDER",
        "RECOVERY_ON_TIMER_EXPIRE",
        "GATEWAY_DOWN",
        "SWITCH_CONGESTION"
    }
    
    for _, cause in ipairs(failover_causes) do
        if hangup_cause == cause then
            -- Try next route
            local next_route = session:getVariable("next_lcr_route")
            if next_route then
                freeswitch.consoleLog("INFO", "Failing over to: " .. next_route)
                session:execute("bridge", next_route)
                return
            end
        end
    end
    
    -- No failover, return error
    session:setVariable("call_status", "failed")
    session:setVariable("failure_reason", hangup_cause)
    session:hangup(hangup_cause)
end
```

### Error Response to API Clients

```typescript
// API error response handler
class CallErrorHandler {
    handleCallFailure(error: CallError): ApiResponse {
        const errorMapping: Record<string, ApiErrorResponse> = {
            'NO_ROUTE_DESTINATION': {
                httpStatus: 404,
                code: 'ROUTE_NOT_FOUND',
                message: 'No route available for the destination number',
                userMessage: 'Unable to connect to this number. Please check the number and try again.'
            },
            'USER_BUSY': {
                httpStatus: 486,
                code: 'DESTINATION_BUSY',
                message: 'The destination number is busy',
                userMessage: 'The number you called is busy. Please try again later.'
            },
            'NO_ANSWER': {
                httpStatus: 480,
                code: 'NO_ANSWER',
                message: 'The destination did not answer',
                userMessage: 'There was no answer. Please try again later.'
            },
            'INVALID_NUMBER_FORMAT': {
                httpStatus: 400,
                code: 'INVALID_NUMBER',
                message: 'The destination number format is invalid',
                userMessage: 'Please enter a valid phone number.'
            },
            'CALLER_ID_NOT_ALLOWED': {
                httpStatus: 403,
                code: 'CLI_NOT_PERMITTED',
                message: 'The requested caller ID is not allowed',
                userMessage: 'Unable to use the requested caller ID.'
            },
            'QUOTA_EXCEEDED': {
                httpStatus: 429,
                code: 'RATE_LIMIT_EXCEEDED',
                message: 'Call rate limit has been exceeded',
                userMessage: 'Too many calls. Please wait before trying again.',
                retryAfter: 60
            }
        };
        
        const mapping = errorMapping[error.cause] || {
            httpStatus: 500,
            code: 'CALL_FAILED',
            message: `Call failed: ${error.cause}`,
            userMessage: 'The call could not be completed. Please try again.'
        };
        
        return {
            success: false,
            error: {
                ...mapping,
                callId: error.callId,
                timestamp: new Date().toISOString()
            }
        };
    }
}
```

---

## Sequence Diagrams

### Complete Outbound Call Flow

```
┌─────────┐     ┌──────────┐     ┌───────────┐     ┌─────────┐     ┌─────────┐     ┌──────┐
│Salesforce│     │Middleware│     │FreeSWITCH │     │LCR Svc  │     │Carrier  │     │ PSTN │
│   CTI   │     │  (AWS)   │     │           │     │         │     │Gateway  │     │      │
└────┬────┘     └────┬─────┘     └─────┬─────┘     └────┬────┘     └────┬────┘     └──┬───┘
     │               │                 │                │               │             │
     │ Click-to-Dial │                 │                │               │             │
     │──────────────▶│                 │                │               │             │
     │               │                 │                │               │             │
     │               │ POST /originate │                │               │             │
     │               │────────────────▶│                │               │             │
     │               │                 │                │               │             │
     │               │                 │ Get LCR Routes │               │             │
     │               │                 │───────────────▶│               │             │
     │               │                 │                │               │             │
     │               │                 │  Routes[]      │               │             │
     │               │                 │◀───────────────│               │             │
     │               │                 │                │               │             │
     │               │                 │ Apply CLI Rules│               │             │
     │               │                 │───────┐        │               │             │
     │               │                 │       │        │               │             │
     │               │                 │◀──────┘        │               │             │
     │               │                 │                │               │             │
     │               │                 │  SIP INVITE    │               │             │
     │               │                 │───────────────────────────────▶│             │
     │               │                 │                │               │             │
     │               │                 │  100 Trying    │               │             │
     │               │                 │◀───────────────────────────────│             │
     │               │                 │                │               │             │
     │               │                 │                │               │ ISUP IAM    │
     │               │                 │                │               │────────────▶│
     │               │                 │                │               │             │
     │               │                 │                │               │ ISUP ACM    │
     │               │                 │  183 Progress  │               │◀────────────│
     │               │                 │◀───────────────────────────────│             │
     │               │                 │                │               │             │
     │               │  Call Ringing   │                │               │             │
     │               │◀────────────────│                │               │             │
     │               │                 │                │               │             │
     │  Call Ringing │                 │                │               │             │
     │◀──────────────│                 │                │               │             │
     │               │                 │                │               │             │
     │               │                 │                │               │ ISUP ANM    │
     │               │                 │  200 OK        │               │◀────────────│
     │               │                 │◀───────────────────────────────│             │
     │               │                 │                │               │             │
     │               │                 │  ACK           │               │             │
     │               │                 │───────────────────────────────▶│             │
     │               │                 │                │               │             │
     │               │                 │ Start Recording│               │             │
     │               │                 │───────┐        │               │             │
     │               │                 │       │        │               │             │
     │               │                 │◀──────┘        │               │             │
     │               │                 │                │               │             │
     │               │  Call Answered  │                │               │             │
     │               │◀────────────────│                │               │             │
     │               │                 │                │               │             │
     │ Call Answered │                 │                │               │             │
     │◀──────────────│                 │                │               │             │
     │               │                 │                │               │             │
     │               │                 │ ═══RTP MEDIA══════════════════▶│             │
     │               │                 │                │               │             │
     │               │                 │                │               │             │
     │ [User hangs up]                 │                │               │             │
     │               │                 │                │               │             │
     │               │                 │  BYE           │               │             │
     │               │                 │───────────────────────────────▶│             │
     │               │                 │                │               │             │
     │               │                 │                │               │ ISUP REL    │
     │               │                 │                │               │────────────▶│
     │               │                 │                │               │             │
     │               │                 │  200 OK        │               │ ISUP RLC    │
     │               │                 │◀───────────────────────────────│◀────────────│
     │               │                 │                │               │             │
     │               │                 │ Generate CDR   │               │             │
     │               │                 │───────┐        │               │             │
     │               │                 │       │        │               │             │
     │               │                 │◀──────┘        │               │             │
     │               │                 │                │               │             │
     │               │  Call Ended     │                │               │             │
     │               │◀────────────────│                │               │             │
     │               │                 │                │               │             │
     │ Call Ended    │                 │                │               │             │
     │◀──────────────│                 │                │               │             │
     │               │                 │                │               │             │
     ▼               ▼                 ▼                ▼               ▼             ▼
```

### Gateway Failover Sequence

```
┌───────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│FreeSWITCH │     │Gateway A    │     │Gateway B    │     │Gateway C    │
│           │     │(Primary)    │     │(Secondary)  │     │(Tertiary)   │
└─────┬─────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
      │                  │                   │                   │
      │ SIP INVITE       │                   │                   │
      │─────────────────▶│                   │                   │
      │                  │                   │                   │
      │ 503 Unavailable  │                   │                   │
      │◀─────────────────│                   │                   │
      │                  │                   │                   │
      │ [Failover]       │                   │                   │
      │                  │                   │                   │
      │ SIP INVITE       │                   │                   │
      │─────────────────────────────────────▶│                   │
      │                  │                   │                   │
      │ 100 Trying       │                   │                   │
      │◀─────────────────────────────────────│                   │
      │                  │                   │                   │
      │ 408 Timeout      │                   │                   │
      │◀─────────────────────────────────────│                   │
      │                  │                   │                   │
      │ [Failover]       │                   │                   │
      │                  │                   │                   │
      │ SIP INVITE       │                   │                   │
      │────────────────────────────────────────────────────────▶│
      │                  │                   │                   │
      │ 100 Trying       │                   │                   │
      │◀────────────────────────────────────────────────────────│
      │                  │                   │                   │
      │ 183 Progress     │                   │                   │
      │◀────────────────────────────────────────────────────────│
      │                  │                   │                   │
      │ 200 OK           │                   │                   │
      │◀────────────────────────────────────────────────────────│
      │                  │                   │                   │
      │ ACK              │                   │                   │
      │────────────────────────────────────────────────────────▶│
      │                  │                   │                   │
      │ ════════════════RTP══════════════════════════════════▶│
      │                  │                   │                   │
      ▼                  ▼                   ▼                   ▼
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LCR_SERVICE_URL` | LCR service endpoint | `http://lcr-service:8080` |
| `LCR_CACHE_TTL` | Route cache TTL (seconds) | `300` |
| `LCR_MAX_ROUTES` | Maximum routes returned | `5` |
| `RECORDING_BUCKET` | S3 bucket for recordings | `natterbox-recordings` |
| `CDR_RETENTION_DAYS` | CDR retention period | `365` |
| `FAILOVER_THRESHOLD` | Failures before failover | `3` |
| `FAILOVER_WINDOW` | Failover window (seconds) | `300` |
| `AMD_ENABLED` | Enable answer machine detection | `false` |
| `MAX_CALL_DURATION` | Maximum call duration (seconds) | `7200` |

### FreeSWITCH Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `lcr_auto_route` | Auto-generated LCR dial string | `sofia/gateway/carrier/+44...` |
| `lcr_profile` | LCR profile to use | `default` |
| `recording_enabled` | Enable call recording | `true` |
| `recording_policy_id` | Recording policy ID | `123` |
| `max_forwards` | SIP Max-Forwards header | `70` |
| `call_timeout` | Ring timeout (seconds) | `60` |
| `originate_timeout` | Overall timeout (seconds) | `120` |

---

## Related Documentation

- [Inbound Call Flows](./inbound-call-flows.md)
- [LCR Service API Reference](./lcr-service-api.md)
- [Recording Service Documentation](../recording/recording-service.md)
- [CDR Processing Pipeline](../billing/cdr-processing.md)
- [Carrier Integration Guide](../carriers/integration-guide.md)
- [FreeSWITCH Configuration](../freeswitch/configuration.md)

---

## Changelog

| Date | Version | Description |
|------|---------|-------------|
| 2026-01-20 | 1.0.0 | Initial documentation |
