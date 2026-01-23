# Widget Models

This document covers data models for dashboard widgets in the Natterbox Wallboards application, including agent status widgets, queue widgets, and their associated configurations.

## Overview

Widgets are the core display components of wallboards. Each widget type has its own configuration model that determines how data is displayed, filtered, and sorted. The main widget types include:

- **Agent Status Widget** - Displays agent status information
- **Agent List Widget** - Shows detailed agent information with call statistics
- **Queue List Widget** - Displays calls waiting in queues
- **Agent Login Widget** - Tracks agent login/logout events

## Entity Relationships

```
┌─────────────────────┐
│      Widget         │
│  (base component)   │
└──────────┬──────────┘
           │
    ┌──────┴──────────────────────────────┐
    │                  │                   │
    ▼                  ▼                   ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│AgentStatus  │  │ QueueList    │  │  AgentList   │
│   Widget    │  │   Widget     │  │   Widget     │
└──────┬──────┘  └──────┬───────┘  └──────┬───────┘
       │                │                  │
       ▼                ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│AgentStatus  │  │  QueueCall   │  │    Agent     │
│    User     │  │              │  │              │
└─────────────┘  └──────────────┘  └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │Availability  │
                                   │    State     │
                                   └──────────────┘
```

---

## Widget Base Model

### Widget

Base widget configuration that all widget types extend.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique widget identifier (UUID format) |

**Validation Rules:**
- `id` must be a valid UUID string
- Each widget ID must be unique within a wallboard

**Example JSON:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## Agent Status Widget Models

### AgentStatusWidget

Configuration for displaying agent status information in a tabular format.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Widget unique identifier |
| isShowStateName | boolean | No | Whether to show the internal state name column |
| isShowDisplayName | boolean | No | Whether to show the user-friendly state display name column |
| limitResult | object | No | Object containing `value` property for limiting displayed results |

**Validation Rules:**
- `id` must be a valid UUID
- `limitResult.value` should be a positive integer when specified
- At least one of `isShowStateName` or `isShowDisplayName` should be true for meaningful display

**Example JSON:**
```json
{
  "id": "widget-123e4567-e89b-12d3-a456-426614174000",
  "isShowStateName": true,
  "isShowDisplayName": true,
  "limitResult": {
    "value": 25
  }
}
```

**Relationships:**
- Contains multiple `AgentStatusUser` records
- Part of a parent `Wallboard`

**Common Use Cases:**
- Monitoring real-time agent availability
- Tracking how long agents have been in specific states
- Identifying agents who may need assistance

---

### AgentStatusUser

Data model representing individual rows in the agent status table.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Unique identifier for the user |
| name | string | Yes | Agent's display name |
| profile | string | No | Agent's assigned profile |
| stateName | string | Yes | Internal state name identifier |
| stateDisplayName | string | Yes | Human-readable state name |
| time | string | Yes | Date and time when status was set (ISO 8601 format) |
| elapsed | number | Yes | Elapsed time in current state (seconds) |
| isElapsedTimeStop | boolean | Yes | Whether the elapsed time counter should stop updating |

**Validation Rules:**
- `userId` must be a non-empty string
- `elapsed` must be a non-negative integer
- `time` should be a valid ISO 8601 date string

**Example JSON:**
```json
{
  "userId": "user-789",
  "name": "Jane Smith",
  "profile": "Sales Agent",
  "stateName": "available",
  "stateDisplayName": "Available",
  "time": "2024-01-15T09:30:00Z",
  "elapsed": 1847,
  "isElapsedTimeStop": false
}
```

**Relationships:**
- Belongs to `AgentStatusWidget`
- References user from authentication system

**Common Use Cases:**
- Display in agent status grid
- Real-time status monitoring
- Calculating time-based metrics

---

### AgentLoginUser

Data model for tracking agent login and logout events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | string | Yes | Unique identifier for the user |
| name | string | Yes | Agent's display name |
| groupName | string | No | Name of the agent's group |
| event | string | Yes | Event type description |
| isLogin | boolean | Yes | True for login events, false for logout |
| time | string | Yes | Date and time of the event (ISO 8601 format) |
| elapsed | number | Yes | Elapsed time since event (seconds) |
| isElapsedTimeStop | boolean | Yes | Whether to stop the elapsed time counter |

**Validation Rules:**
- `userId` must be a non-empty string
- `event` should be "Login" or "Logout"
- `isLogin` must align with `event` value

**Example JSON:**
```json
{
  "userId": "user-456",
  "name": "John Doe",
  "groupName": "Support Team",
  "event": "Login",
  "isLogin": true,
  "time": "2024-01-15T08:00:00Z",
  "elapsed": 7200,
  "isElapsedTimeStop": false
}
```

**Common Use Cases:**
- Tracking agent shift attendance
- Monitoring login patterns
- Compliance reporting

---

## Queue Widget Models

### QueueListWidget

Configuration for displaying calls waiting in queues.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Widget unique identifier |
| sortBy | string | No | Column key to sort by |
| columnsToViewOptions | object | No | Object with `selectedItems` array of column keys to display |
| interactivityOptions | object | No | Object with `selectedItems` array of enabled interactions |
| timeInQueueSLATime | number | No | SLA threshold in seconds for queue wait time highlighting |
| timeAtHeadOfQueueSLATime | number | No | SLA threshold in seconds for head-of-queue highlighting |
| isShowOnlyOnHover | boolean | No | Show skills tooltip only on hover |
| callQueue | object | No | Call queue configuration with `id` property |

**Validation Rules:**
- `id` must be a valid UUID
- `timeInQueueSLATime` and `timeAtHeadOfQueueSLATime` should be positive integers
- `sortBy` must match a valid column key

**Example JSON:**
```json
{
  "id": "queue-widget-abc123",
  "sortBy": "timeWaitingInQueue",
  "columnsToViewOptions": {
    "selectedItems": ["priority", "positionInQueue", "timeWaitingInQueue", "callerNumber", "status"]
  },
  "interactivityOptions": {
    "selectedItems": ["pickup", "transfer"]
  },
  "timeInQueueSLATime": 120,
  "timeAtHeadOfQueueSLATime": 30,
  "isShowOnlyOnHover": true,
  "callQueue": {
    "id": "queue-001"
  }
}
```

**Relationships:**
- Contains multiple `QueueCall` records
- References a specific call queue
- Part of a parent `Wallboard`

**Common Use Cases:**
- Monitoring queue performance
- Identifying SLA breaches
- Managing call distribution

---

### QueueCall

Individual call record within a queue.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| callUuid | string | Yes | Unique identifier for the call |
| priority | number | Yes | Call priority (1 = highest, 10+ = lowest) |
| positionInQueue | number | Yes | Current position in the queue |
| timeWaitingInQueue | number | Yes | Time waiting in queue (seconds) |
| callerNumber | string | Yes | Caller's phone number |
| timeAtHeadOfQueue | number | No | Time at head of queue (seconds) |
| nextCallbackAttempt | number | No | Timestamp for next callback attempt |
| callbackRequested | boolean | No | Whether caller requested a callback |
| callbackAttempts | number | No | Number of callback attempts made |
| skillsRequested | array | No | Array of requested skill names |
| skillsShortage | boolean | No | Indicates if required skills are unavailable |
| status | string | Yes | Call status (waiting, connected, etc.) |
| call | object | No | Nested call object with additional details |
| agent | object | No | Connected agent object (if applicable) |

**Validation Rules:**
- `callUuid` must be a valid UUID
- `priority` must be a positive integer
- `positionInQueue` must be a positive integer (1-indexed)
- `timeWaitingInQueue` must be a non-negative integer
- `status` must be one of: "waiting", "connected", "callback_pending"

**Example JSON:**
```json
{
  "callUuid": "call-uuid-12345",
  "priority": 1,
  "positionInQueue": 3,
  "timeWaitingInQueue": 245,
  "callerNumber": "+1-555-123-4567",
  "timeAtHeadOfQueue": 0,
  "nextCallbackAttempt": null,
  "callbackRequested": false,
  "callbackAttempts": 0,
  "skillsRequested": ["English", "Technical Support"],
  "skillsShortage": false,
  "status": "waiting",
  "call": {
    "direction": "inbound",
    "startTime": "2024-01-15T10:15:30Z"
  },
  "agent": null
}
```

**Relationships:**
- Belongs to `QueueListWidget`
- May reference an `Agent` when connected
- Contains `Skill` references in `skillsRequested`

**Common Use Cases:**
- Real-time queue monitoring
- Callback management
- Skills-based routing visualization

---

## Agent List Widget Models

### Agent

Comprehensive agent data model for detailed agent list displays.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Agent unique identifier |
| agentName | string | Yes | Agent display name |
| agentExtNo | string | No | Agent phone extension number |
| groupMembership | string | No | Group ID the agent belongs to |
| callUuid | string | No | UUID of current call (if on call) |
| callStatusKey | string | No | Key for determining call status color/styling |
| availabilityStateOrScvStatus | string | Yes | Current availability state or SCV status |
| isAvailabilityStateDropdownDisabled | boolean | No | Whether availability dropdown is disabled |
| filtredAvailabilityStatesList | array | No | List of available availability states for this agent |
| noCallsOffered | number | No | Number of calls offered to agent |
| noCallsAnswered | number | No | Number of calls answered by agent |
| noCallsMissed | number | No | Number of calls missed by agent |
| timeInCurrentPresenceState | number | No | Time in current presence state (seconds) |
| timeInCurrentAvailabilityState | number | No | Time in current availability state (seconds) |
| timeInCurrentCall | number | No | Time on current call (seconds) |

**Validation Rules:**
- `id` must be a non-empty string
- All numeric fields must be non-negative integers
- `availabilityStateOrScvStatus` should match a valid state

**Example JSON:**
```json
{
  "id": "agent-001",
  "agentName": "Sarah Johnson",
  "agentExtNo": "1234",
  "groupMembership": "group-sales-001",
  "callUuid": "call-active-789",
  "callStatusKey": "on_call",
  "availabilityStateOrScvStatus": "Available",
  "isAvailabilityStateDropdownDisabled": false,
  "filtredAvailabilityStatesList": [
    {
      "availabilityProfileId": "profile-1",
      "availabilityStateId": "state-avail",
      "availabilityStateName": "available",
      "availabilityStateDisplayName": "Available"
    }
  ],
  "noCallsOffered": 45,
  "noCallsAnswered": 42,
  "noCallsMissed": 3,
  "timeInCurrentPresenceState": 3600,
  "timeInCurrentAvailabilityState": 1800,
  "timeInCurrentCall": 325
}
```

**Relationships:**
- Has multiple `AvailabilityState` options
- Belongs to an `AgentGroup`
- May have an active `QueueCall`

---

### AgentTableColumns

Configuration model for controlling which columns are visible in the agent table.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isAgentNameColumn | boolean | No | Show agent name column |
| isCurrAvaiStateColumn | boolean | No | Show current availability state column |
| isAgentExtNoColumn | boolean | No | Show agent extension number column |
| isNoCallsOfferedColumn | boolean | No | Show calls offered column |
| isNoCallsAnsweredColumn | boolean | No | Show calls answered column |
| isNoCallsMissedColumn | boolean | No | Show calls missed column |
| isTimeInCurrentPresenceStateColumn | boolean | No | Show time in presence state column |
| isTimeInCurrentAvailabilityStateColumn | boolean | No | Show time in availability state column |
| isTimeInCurrentCallColumn | boolean | No | Show time on current call column |
| isTimeInCurrentWrapupColumn | boolean | No | Show time in wrapup column |
| isListOfSkillsColumn | boolean | No | Show skills column |
| isCurrPresStateColumn | boolean | No | Show current presence state column |

**Validation Rules:**
- All fields are boolean
- At least one column should be enabled for meaningful display

**Example JSON:**
```json
{
  "isAgentNameColumn": true,
  "isCurrAvaiStateColumn": true,
  "isAgentExtNoColumn": true,
  "isNoCallsOfferedColumn": true,
  "isNoCallsAnsweredColumn": true,
  "isNoCallsMissedColumn": true,
  "isTimeInCurrentPresenceStateColumn": false,
  "isTimeInCurrentAvailabilityStateColumn": true,
  "isTimeInCurrentCallColumn": true,
  "isTimeInCurrentWrapupColumn": false,
  "isListOfSkillsColumn": true,
  "isCurrPresStateColumn": false
}
```

**Common Use Cases:**
- Customizing agent list views for different roles
- Creating focused displays for specific metrics
- Optimizing screen real estate

---

### AgentGroup

Group model for organizing agents within widgets.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| groupId | string | Yes | Unique identifier for the group |
| groupName | string | Yes | Display name of the group |

**Validation Rules:**
- `groupId` must be a non-empty string
- `groupName` should be human-readable

**Example JSON:**
```json
{
  "groupId": "group-support-001",
  "groupName": "Technical Support Team"
}
```

**Relationships:**
- Contains multiple `Agent` records
- Used for filtering in widget configurations

---

### AvailabilityState

Availability state option available to agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| availabilityProfileId | string | Yes | Profile ID for the availability state |
| availabilityStateId | string | Yes | Unique state identifier |
| availabilityStateName | string | Yes | Internal state name |
| availabilityStateDisplayName | string | Yes | Human-readable display name |

**Validation Rules:**
- All fields must be non-empty strings
- `availabilityStateName` should be lowercase/snake_case
- `availabilityStateDisplayName` should be properly capitalized

**Example JSON:**
```json
{
  "availabilityProfileId": "profile-standard",
  "availabilityStateId": "state-lunch",
  "availabilityStateName": "lunch_break",
  "availabilityStateDisplayName": "Lunch Break"
}
```

**Relationships:**
- Belongs to an availability profile
- Referenced by `Agent` and `AgentCardProps`

**Common Use Cases:**
- Populating availability dropdowns
- State change validation
- Reporting and analytics

---

### AgentCardProps

Props and data model for the agent card component display.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string \| number | Yes | Agent unique identifier |
| name | string | Yes | Agent display name |
| ext | string | No | Agent extension number |
| callQueueId | string \| number | No | Current call queue ID |
| availabilityStateOrScvStatus | string | Yes | Current availability state |
| totalTime | number | No | Total time logged in (seconds) |
| callTime | number | No | Current call duration (seconds) |
| isCallbackCall | boolean | No | Whether this is a callback call |
| callUuid | string | No | UUID of current call |
| callStatusKey | string | No | Key for call status styling |
| canCallAgents | boolean | No | Permission to call other agents |
| canTerminateCall | boolean | No | Permission to terminate calls |
| canListenLive | boolean | No | Permission to listen to live calls |
| isAvailabilityStateDropdownDisabled | boolean | No | Whether availability dropdown is disabled |
| filtredAvailabilityStatesList | array | No | Filtered list of available states |

**Validation Rules:**
- `id` and `name` are required
- Numeric time fields must be non-negative
- Permission booleans default to false

**Example JSON:**
```json
{
  "id": "agent-card-001",
  "name": "Michael Brown",
  "ext": "5678",
  "callQueueId": "queue-main",
  "availabilityStateOrScvStatus": "On Call",
  "totalTime": 14400,
  "callTime": 892,
  "isCallbackCall": false,
  "callUuid": "call-current-456",
  "callStatusKey": "active_call",
  "canCallAgents": true,
  "canTerminateCall": true,
  "canListenLive": true,
  "isAvailabilityStateDropdownDisabled": true,
  "filtredAvailabilityStatesList": []
}
```

**Relationships:**
- Uses `AvailabilityState` for state options
- Part of agent grid displays

---

## Widget Configuration Models

### AgentListData

Modal configuration data for agent list widget setup.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isEditMode | boolean | Yes | Whether the widget is being edited |
| filterAlgorithm | string | No | Filter algorithm type (RELATIVE or ABSOLUTE) |
| skillsToView | SkillsSelection | No | Skills selection configuration |

**Example JSON:**
```json
{
  "isEditMode": true,
  "filterAlgorithm": "RELATIVE",
  "skillsToView": {
    "selectAll": false,
    "selectNone": false,
    "selectedItems": ["skill-001", "skill-002"]
  }
}
```

---

### QueueListData

Modal configuration data for queue list widget setup.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| isEditMode | boolean | Yes | Whether the widget is being edited |
| filterAlgorithm | string | No | Filter algorithm type |
| skillsToView | SkillsSelection | No | Skills selection configuration |

**Example JSON:**
```json
{
  "isEditMode": false,
  "filterAlgorithm": "ABSOLUTE",
  "skillsToView": {
    "selectAll": true,
    "selectNone": false,
    "selectedItems": []
  }
}
```

---

### QueueStatusData

Modal configuration data for queue status widget.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| filterAlgorithm | string | No | Filter algorithm type |
| skillsToView | SkillsSelection | No | Skills selection configuration |

**Example JSON:**
```json
{
  "filterAlgorithm": "RELATIVE",
  "skillsToView": {
    "selectAll": false,
    "selectNone": true,
    "selectedItems": []
  }
}
```

---

### SkillsSelection

State model for skills selection in widget configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| selectAll | boolean | No | Whether all skills are selected |
| selectNone | boolean | No | Whether no skills are selected |
| selectedItems | array | Yes | Array of selected skill IDs |

**Validation Rules:**
- `selectAll` and `selectNone` are mutually exclusive
- When `selectAll` is true, `selectedItems` may be empty
- `selectedItems` contains valid skill IDs

**Example JSON:**
```json
{
  "selectAll": false,
  "selectNone": false,
  "selectedItems": ["skill-english", "skill-spanish", "skill-technical"]
}
```

---

### Skill

Individual skill entity used in widget filtering.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | number \| string | Yes | Unique identifier for the skill |
| name | string | Yes | Skill name |
| description | string | No | Skill description |

**Example JSON:**
```json
{
  "id": "skill-technical-support",
  "name": "Technical Support",
  "description": "Ability to handle technical troubleshooting calls"
}
```

---

### FilterAlgorithmOption

Option model for filter algorithm dropdown.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| value | string | Yes | Option value (RELATIVE or ABSOLUTE) |
| label | string | Yes | Display label for the option |

**Example JSON:**
```json
{
  "value": "RELATIVE",
  "label": "Relative Filtering"
}
```

**Common Values:**
- `RELATIVE` - Filter based on relative criteria
- `ABSOLUTE` - Filter based on absolute/exact criteria

---

## Widget Grid Positioning

### GridComponent

Defines a widget's position and size within the wallboard grid.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier for the grid component |
| width | number | Yes | Width in pixels |
| widthProcent | number | Yes | Width as percentage of container |
| height | number | Yes | Height in pixels |
| heightProcent | number | Yes | Height as percentage of total height |
| startX | number | Yes | Starting X position in pixels |
| startXProcent | number | Yes | Starting X position as percentage |
| endX | number | Yes | Ending X position in pixels |
| endXProcent | number | Yes | Ending X position as percentage |
| startY | number | Yes | Starting Y position in pixels |
| startYProcent | number | Yes | Starting Y position as percentage |
| endY | number | Yes | Ending Y position in pixels |
| endYProcent | number | Yes | Ending Y position as percentage |

**Validation Rules:**
- All pixel values must be non-negative
- All percentage values must be between 0 and 100
- `startX` must be less than `endX`
- `startY` must be less than `endY`

**Example JSON:**
```json
{
  "id": "grid-widget-001",
  "width": 400,
  "widthProcent": 33.33,
  "height": 300,
  "heightProcent": 50,
  "startX": 0,
  "startXProcent": 0,
  "endX": 400,
  "endXProcent": 33.33,
  "startY": 0,
  "startYProcent": 0,
  "endY": 300,
  "endYProcent": 50
}
```

**Relationships:**
- Part of `Widget.size` property
- Used by wallboard layout engine

**Common Use Cases:**
- Responsive widget positioning
- Drag-and-drop resizing
- Export/import of layouts