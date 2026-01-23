# Data Models Overview

## Introduction

The platform-cti-client application uses a comprehensive data model architecture to manage CTI (Computer Telephony Integration) functionality, WebSocket communications, Salesforce integration, and user interface state. This document provides a high-level overview of all data structures and serves as an index to detailed model documentation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Application Layer                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Redux      │  │  WebSocket   │  │  Salesforce  │  │    Auth      │    │
│  │   State      │  │  Messages    │  │   Objects    │  │   Models     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         ▼                 ▼                 ▼                 ▼             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Call Management Layer                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Active Call │  │  Call Logs  │  │  Voicemail  │  │  Transfer   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        UI Components Layer                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Modals    │  │  Contacts   │  │   Groups    │  │  Settings   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Model Categories

The application's 71 data models are organized into five primary categories:

### 1. State Models (Redux Store)

**Count:** ~15 models

Redux state models manage application-wide state including authentication, UI configuration, call management, and feature-specific states.

| Model | Purpose |
|-------|---------|
| `ReduxState` | Root Redux state structure combining all reducers |
| `MainState` | Core application state (view type, master tab, namespaces) |
| `AuthState` | JWT tokens and Natterbox credentials |
| `GroupsState` | Selected group tracking |
| `CallLogsState` | Call log filtering and search |
| `VoicemailState` | Voicemail list management |
| `AudioPlayerState` | Audio playback coordination across tabs |
| `WebPhoneState` | WebPhone connection, registration, and device state |
| `FreedomWebAuthState` | FreedomWeb-specific authentication state |

**See:** [State Models Documentation](models/state-models.md)

---

### 2. Call Models

**Count:** ~20 models

Call models represent telephony data including active calls, call logs, transfers, and call-related enumerations.

| Model | Purpose |
|-------|---------|
| `ActiveCall` | Current call state with status, direction, and participant info |
| `CallLog` | Processed call history entry |
| `CallDetails` | Extended call information with lookup results |
| `Call` | Basic call object for status checking |
| `CallItem` | Call lookup by UUID |
| `CallStatusEnum` | Call lifecycle status codes (1-15) |
| `CallDirectionEnum` | Inbound/Outbound direction constants |
| `CallsFilterOption` | Filter options for call log display |
| `InternalCallConfig` | Configuration for internal call detection |
| `LookupResult` | Contact matching result |
| `LookupResultsOutput` | Structured person/relatedTo lookup arrays |

**See:** [Call Models Documentation](models/call-models.md)

---

### 3. WebSocket Models

**Count:** ~12 models

WebSocket models define message structures for real-time communication including presence updates, subscriptions, and event notifications.

| Model | Purpose |
|-------|---------|
| `WebSocketMessage` | Base WebSocket message structure |
| `WebSocketClientInfo` | Client identification during auth |
| `WebsocketStartMessage` | Connection initialization payload |
| `WebsocketGroupMessage` | Group subscription/unsubscription |
| `WebsocketUserSubscribeMessage` | User subscription management |
| `WebsocketResponseMessage` | Server response with unread counts |
| `WebsocketSubscribePayload` | Subscription request payload |
| `UserPresenceData` | Real-time user presence from WebSocket |
| `UserPresenceEnum` | Presence state constants |

**See:** [WebSocket Models Documentation](models/websocket-models.md)

---

### 4. Salesforce Models

**Count:** ~12 models

Salesforce models represent Salesforce objects, query configurations, and integration-specific data structures.

| Model | Purpose |
|-------|---------|
| `SalesforceCallReporting` | CallReporting__c custom object |
| `SalesforcePhoneEvent` | Phone_Event__c for missed calls |
| `ChatterCallLog` | Call logs from Sapien API |
| `SalesforceQueryNamespaceAction` | Namespace configuration action |
| `SalesforceLicenses` | License type constants |
| `CTIConfig` | Global window.cticonfig configuration |
| `CallCenterConfig` | Call center behavior settings |
| `AvatarTypes` | Salesforce object types for avatars |

**See:** [Salesforce Models Documentation](models/salesforce-models.md)

---

### 5. Auth Models

**Count:** ~12 models

Authentication models manage JWT tokens, license validation, view access, and user identity across Salesforce and Natterbox systems.

| Model | Purpose |
|-------|---------|
| `AuthState` | Authentication state in Redux |
| `LocalDetails` | Local storage auth details |
| `JWTExtracted` | Extracted JWT token fields |
| `LicenseType` | Natterbox license constants |
| `ViewType` | View access level constants |
| `NatterboxLicenses` | Natterbox license types |
| `ViewTypes` | View access enumeration |

**See:** [Auth Models Documentation](models/auth-models.md)

---

## Supporting Models

### UI Component Models

Models supporting user interface components and interactions:

| Model | Purpose |
|-------|---------|
| `ContactCardData` | Contact display information |
| `UserDisplayItem` | User info for teams/groups display |
| `UserGroup` | User group with classification |
| `NavLink` | Navigation link structure |
| `IconState` | Button/icon display state |
| `IconObject` | CSS classes for icon rendering |
| `HistoryLocation` | React Router location object |

### Configuration Constants

Enumeration and constant models:

| Model | Purpose |
|-------|---------|
| `FooterTypes` | Call UI footer state types |
| `ModalTypes` | Modal type enumeration |
| `ModalActions` | Modal Redux action types |
| `TransferTypes` | Call transfer type constants |
| `ListenModeEnum` | Listen-in mode options |
| `UserTypeEnum` | Address book user types |
| `UserGroupCategories` | Group categorization labels |
| `ZIndexConstants` | UI layering constants |

### Worker Communication Models

Models for Web Worker inter-thread communication:

| Model | Purpose |
|-------|---------|
| `CallLogRefreshMessage` | Call log refresh worker message |
| `VoicemailWorkerFilterMessage` | Voicemail filter worker message |

---

## Entity Relationships

### Core Relationships

```
┌─────────────────┐         ┌─────────────────┐
│    AuthState    │────────▶│    CTIConfig    │
│  (JWT tokens)   │         │ (SF credentials)│
└────────┬────────┘         └─────────────────┘
         │
         │ provides credentials
         ▼
┌─────────────────┐         ┌─────────────────┐
│  WebSocket      │◀───────▶│ UserPresenceData│
│  Messages       │ updates │                 │
└────────┬────────┘         └─────────────────┘
         │
         │ real-time events
         ▼
┌─────────────────┐         ┌─────────────────┐
│   ActiveCall    │────────▶│   CallDetails   │
│                 │ extends │  (lookup data)  │
└────────┬────────┘         └─────────────────┘
         │
         │ persists to
         ▼
┌─────────────────┐         ┌─────────────────┐
│   CallLog       │◀───────▶│ SalesforceCall  │
│  (processed)    │  syncs  │   Reporting     │
└─────────────────┘         └─────────────────┘
```

### State Flow

```
User Action
    │
    ▼
┌─────────────────┐
│  Redux Action   │
│   Dispatch      │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬────────────┐
    ▼         ▼            ▼            ▼
┌───────┐ ┌───────┐  ┌──────────┐ ┌──────────┐
│ Main  │ │ Call  │  │ Groups   │ │ Voicemail│
│ State │ │ State │  │  State   │ │  State   │
└───────┘ └───────┘  └──────────┘ └──────────┘
    │         │            │            │
    └────┬────┴────────────┴────────────┘
         │
         ▼
┌─────────────────┐
│   ReduxState    │
│   (combined)    │
└────────┬────────┘
         │
         ▼
    UI Components
```

---

## Model Naming Conventions

| Suffix | Purpose | Examples |
|--------|---------|----------|
| `State` | Redux store slice | `AuthState`, `MainState` |
| `Message` | WebSocket/Worker communication | `WebsocketStartMessage` |
| `Config` | Configuration objects | `CTIConfig`, `CallCenterConfig` |
| `Enum` | Enumeration constants | `CallStatusEnum`, `UserPresenceEnum` |
| `Action` | Redux action payload | `SalesforceQueryNamespaceAction` |
| `Data` | Data transfer objects | `UserPresenceData`, `ContactCardData` |
| `Item` | List/collection items | `PBXListItem`, `VoicemailItem` |
| `Types` | Type constant collections | `FooterTypes`, `ModalTypes` |

---

## Cross-Model Integration Points

### Authentication Flow

1. `CTIConfig` provides Salesforce session credentials
2. `LocalDetails` retrieves stored authentication data
3. `JWTExtracted` parses JWT for Natterbox identity
4. `AuthState` stores validated credentials in Redux
5. `WebsocketStartMessage` uses tokens for WebSocket auth

### Call Lifecycle

1. `WebSocketMessage` receives incoming call notification
2. `ActiveCall` created in Redux with initial state
3. `CallStatusEnum` tracks call through lifecycle
4. `CallDetails` populated with `LookupResult` data
5. `CallLog` created when call ends
6. `SalesforceCallReporting` synced to Salesforce

### License-Based Access

1. `CTIConfig` provides license flags
2. `LicenseType` constants define valid licenses
3. `ViewType` determines access level
4. `ViewTypes` applied to UI component visibility

---

## Quick Reference Index

| Category | Model Count | Documentation |
|----------|-------------|---------------|
| State Models | 15 | [state-models.md](models/state-models.md) |
| Call Models | 20 | [call-models.md](models/call-models.md) |
| WebSocket Models | 12 | [websocket-models.md](models/websocket-models.md) |
| Salesforce Models | 12 | [salesforce-models.md](models/salesforce-models.md) |
| Auth Models | 12 | [auth-models.md](models/auth-models.md) |
| **Total** | **71** | |

---

## Version Information

- **Total Models Documented:** 71
- **Documentation Version:** 1.0
- **Service:** platform-cti-client