# Data Models Overview

## Introduction

The Natterbox Wallboards application uses a comprehensive data model architecture to support real-time call center monitoring, agent management, and customizable dashboard displays. This document provides a high-level overview of all data models and their relationships within the system.

## Architecture Overview

The application's data models are organized into five primary categories:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Data Layer                          │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│    Auth     │   Agent     │  Wallboard  │   Widget    │       UI        │
│   Models    │   Models    │   Models    │   Models    │     Models      │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤
│ • Auth0     │ • Agent     │ • Wallboard │ • Grid      │ • Dropdown      │
│ • Login     │ • Status    │ • Groups    │ • Config    │ • TimePicker    │
│ • User      │ • Skills    │ • Steps     │ • Queue     │ • Slider        │
│ • Perms     │ • Queues    │ • Settings  │ • Status    │ • Toolbar       │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘
```

## Model Categories

### 1. Authentication Models
**Documentation:** [docs/models/auth-models.md](docs/models/auth-models.md)

Authentication models handle user identity, permissions, and session management through Auth0 integration.

| Model | Purpose |
|-------|---------|
| `AuthConfig` | OAuth configuration for Auth0 authentication flow |
| `Auth0Urls` | Auth0 domain, client, and audience configuration |
| `UserInfo` | Current user identity and organization membership |
| `LoginState` | Redux state slice for authentication status |
| `LoginData` | Utility object for API authentication |
| `ListenInPermissions` | Agent-level listen-in permissions mapping |

**Key Relationships:**
- `LoginState` contains `UserInfo` and `Auth0Urls`
- `UserInfo` determines access to organization resources
- `ListenInPermissions` controls agent monitoring capabilities

---

### 2. Agent Models
**Documentation:** [docs/models/agent-models.md](docs/models/agent-models.md)

Agent models represent call center agents, their states, skills, and real-time activity metrics.

| Model | Purpose |
|-------|---------|
| `Agent` | Complete agent profile with call statistics |
| `AgentStatusUser` | Agent state tracking for status displays |
| `AgentLoginUser` | Agent login/logout event records |
| `AgentGroup` | Logical groupings of agents |
| `AvailabilityState` | Agent availability options (Available, On Break, etc.) |
| `AvailabilityProfile` | Profile containing availability state configurations |
| `Skill` | Agent capability/skill definition |
| `SkillsSelection` | Multi-select state for skill filtering |
| `AgentCardProps` | Agent card display properties |
| `AgentTableColumns` | Column visibility configuration |

**Key Relationships:**
- `Agent` belongs to `AgentGroup`
- `Agent` has multiple `AvailabilityState` options via `AvailabilityProfile`
- `Agent` possesses multiple `Skill` entities
- `AgentStatusUser` tracks state changes for `Agent`

---

### 3. Wallboard Models
**Documentation:** [docs/models/wallboard-models.md](docs/models/wallboard-models.md)

Wallboard models define the dashboard configurations, including groups that cycle through multiple displays.

| Model | Purpose |
|-------|---------|
| `Wallboard` | Main dashboard configuration container |
| `WallboardSettings` | Display and sharing configuration |
| `DisplaySettings` | Screen sizing and scaling options |
| `LinkSettings` | Read-only sharing configuration |
| `WallboardGroup` | Collection of wallboards for rotation |
| `WallboardGroupStep` | Individual step in a wallboard group |
| `WallboardGroupSettings` | Group-level configuration |
| `WallboardGroupLinkSettings` | Group sharing settings |
| `WallboardGroupFetchState` | Redux fetch state for groups |
| `ActiveWallboardState` | Redux state for current wallboard |
| `Step` | Enhanced step with preview data |
| `WallboardFullData` | Wallboard with base64 preview image |
| `FilterOptions` | List sorting and filtering options |

**Key Relationships:**
- `Wallboard` contains multiple `Widget` entities
- `WallboardGroup` contains multiple `WallboardGroupStep` entries
- `WallboardGroupStep` references a `Wallboard`
- `WallboardSettings` contains `DisplaySettings` and `LinkSettings`

---

### 4. Widget Models
**Documentation:** [docs/models/widget-models.md](docs/models/widget-models.md)

Widget models define the individual components displayed on wallboards, including queues, agent lists, and statistics.

| Model | Purpose |
|-------|---------|
| `Widget` | Base widget configuration |
| `GridComponent` | Widget position and dimensions on grid |
| `AgentStatusWidget` | Agent status display configuration |
| `AgentListData` | Agent list modal configuration |
| `QueueCall` | Individual call in queue |
| `QueueListWidget` | Queue list display configuration |
| `QueueListData` | Queue list modal configuration |
| `QueueStatusData` | Queue status widget configuration |
| `FilterAlgorithmOption` | Filtering algorithm selection |

**Key Relationships:**
- `Widget` contains `GridComponent` for positioning
- `QueueListWidget` displays multiple `QueueCall` entries
- `AgentStatusWidget` displays `AgentStatusUser` data
- Widget data models connect to their respective modal configurations

---

### 5. UI Component Models
**Documentation:** [docs/models/ui-models.md](docs/models/ui-models.md)

UI models define props and state for reusable React components throughout the application.

| Model | Purpose |
|-------|---------|
| `DropdownProps` | Configurable dropdown menu component |
| `TimeIntervalProps` | Timer display component |
| `TimePickerProps` | Time selection input |
| `TimeOption` | Individual time option for pickers |
| `AutoWidthInputProps` | Self-sizing text input |
| `CustomAutosuggestProps` | Autocomplete input configuration |
| `ProgressBarProps` | Progress indicator component |
| `ToolbarProps` | Application toolbar configuration |
| `CheckBoxProps` | Checkbox input component |
| `SliderProps` | Wallboard slide rotator |
| `SlideStep` | Individual slide configuration |
| `DragDropElement` | Draggable list item |
| `ModalState` | Modal visibility management |
| `NotificationState` | Toast notification state |
| `WarningMode` | Warning display configuration |
| `LandingCategory` | Sidebar navigation structure |
| `ScreenOption` | Screen selection dropdown option |
| `SvgLineData` | SVG path data for connectors |
| `SVGData` | Full SVG configuration with transforms |
| `XarrowCoordinate` | Arrow connector positioning |

**Key Relationships:**
- `SliderProps` contains array of `SlideStep`
- `ModalState` controls visibility of all modals
- `NotificationState` managed globally via Redux
- UI models primarily serve as component interfaces

---

## Entity Relationship Diagram

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    LoginState    │────▶│     UserInfo     │────▶│  OrganizationId  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │
         │                        ▼
         │               ┌──────────────────┐
         │               │ListenInPermissions│
         │               └──────────────────┘
         ▼                        │
┌──────────────────┐              │
│    Auth0Urls     │              │
└──────────────────┘              │
                                  ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   WallboardGroup │────▶│WallboardGroupStep│────▶│    Wallboard     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                          │
                                                          │ contains
                                                          ▼
                                                 ┌──────────────────┐
                                                 │      Widget      │
                                                 └──────────────────┘
                                                          │
                          ┌───────────────────────────────┼───────────────────────────────┐
                          │                               │                               │
                          ▼                               ▼                               ▼
                 ┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
                 │ AgentStatusWidget│           │  QueueListWidget │           │  GridComponent   │
                 └──────────────────┘           └──────────────────┘           └──────────────────┘
                          │                               │
                          ▼                               ▼
                 ┌──────────────────┐           ┌──────────────────┐
                 │  AgentStatusUser │           │    QueueCall     │
                 └──────────────────┘           └──────────────────┘
                          │                               │
                          ▼                               │
                 ┌──────────────────┐                     │
                 │      Agent       │◀────────────────────┘
                 └──────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
 │  AgentGroup  │ │    Skill     │ │Availability  │
 │              │ │              │ │    State     │
 └──────────────┘ └──────────────┘ └──────────────┘
```

## Data Flow Patterns

### Authentication Flow
1. `AuthConfig` initializes Auth0 with `Auth0Urls`
2. Successful auth populates `LoginState` with `UserInfo`
3. `UserInfo.organisationId` scopes all subsequent API calls
4. `ListenInPermissions` loaded based on user roles

### Wallboard Loading Flow
1. `FilterOptions` determine list query parameters
2. `ActiveWallboardState` tracks fetch status
3. `Wallboard` loaded with `Widget` array
4. Each `Widget` contains `GridComponent` for layout

### Real-Time Data Flow
1. WebSocket/polling updates `Agent` data
2. `AgentStatusUser` records state transitions
3. `QueueCall` entries update queue displays
4. `TimeIntervalProps` handles elapsed time rendering

## Model Count Summary

| Category | Model Count |
|----------|-------------|
| Authentication | 6 |
| Agent | 10 |
| Wallboard | 12 |
| Widget | 9 |
| UI Components | 20 |
| **Total** | **74** |

## Redux State Structure

The application uses Redux for global state management with the following slices:

```typescript
interface RootState {
  login: LoginState;           // Authentication & user info
  modal: ModalState;           // Modal visibility
  errorLog: ErrorLogState;     // Error tracking
  notification: NotificationState; // Toast messages
  activeWallboard: ActiveWallboardState; // Current wallboard
  wallboardGroup: WallboardGroupFetchState; // Group data
}
```

## Detailed Documentation

For complete field listings, validation rules, and usage examples, refer to the category-specific documentation:

- **[Authentication Models](docs/models/auth-models.md)** - Auth0 integration, user sessions, permissions
- **[Agent Models](docs/models/agent-models.md)** - Agent profiles, states, skills, metrics
- **[Wallboard Models](docs/models/wallboard-models.md)** - Dashboard configurations, groups, settings
- **[Widget Models](docs/models/widget-models.md)** - Grid components, queue displays, widget configs
- **[UI Models](docs/models/ui-models.md)** - Component props, form state, visual elements