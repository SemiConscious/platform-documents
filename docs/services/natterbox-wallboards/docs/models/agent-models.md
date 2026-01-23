# Agent & Queue Models

This document covers the data models for agents, agent groups, queues, and call data in the Natterbox Wallboards application. These models are essential for real-time monitoring of contact center operations.

## Overview

The agent and queue models form the core of the wallboard's real-time monitoring capabilities. They track agent states, call queue status, and provide the data structures needed for supervisors to monitor contact center performance.

### Related Documentation

- [Authentication Models](./auth-models.md) - User authentication and permissions
- [Wallboard Models](./wallboard-models.md) - Wallboard configuration
- [Widget Models](./widget-models.md) - Widget-specific configurations
- [UI Models](./ui-models.md) - User interface components

---

## Agent Models

### Agent

The primary data model representing an agent in the contact center, used in agent list tables and real-time monitoring displays.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Agent unique identifier |
| `agentName` | string | Yes | Agent display name |
| `agentExtNo` | string | No | Agent phone extension number |
| `groupMembership` | string | No | Group ID the agent belongs to |
| `callUuid` | string | No | UUID of current call if on call |
| `callStatusKey` | string | No | Key for determining call status color/styling |
| `availabilityStateOrScvStatus` | string | No | Current availability state or SCV status |
| `isAvailabilityStateDropdownDisabled` | boolean | No | Whether availability dropdown is disabled |
| `filtredAvailabilityStatesList` | array | No | List of available availability states for this agent |
| `noCallsOffered` | number | No | Number of calls offered to agent |
| `noCallsAnswered` | number | No | Number of calls answered by agent |
| `noCallsMissed` | number | No | Number of calls missed by agent |
| `timeInCurrentPresenceState` | number | No | Time in current presence state (seconds) |
| `timeInCurrentAvailabilityState` | number | No | Time in current availability state (seconds) |
| `timeInCurrentCall` | number | No | Time on current call (seconds) |

#### Validation Rules

- `id` must be a non-empty unique string
- Numeric fields (`noCallsOffered`, `noCallsAnswered`, `noCallsMissed`) must be non-negative integers
- Time fields are measured in seconds and must be non-negative

#### Example

```json
{
  "id": "agent-12345",
  "agentName": "John Smith",
  "agentExtNo": "1001",
  "groupMembership": "group-sales-001",
  "callUuid": "call-uuid-abc123",
  "callStatusKey": "on-call",
  "availabilityStateOrScvStatus": "Available",
  "isAvailabilityStateDropdownDisabled": false,
  "filtredAvailabilityStatesList": [
    {
      "availabilityProfileId": "profile-1",
      "availabilityStateId": "state-available",
      "availabilityStateName": "available",
      "availabilityStateDisplayName": "Available"
    },
    {
      "availabilityProfileId": "profile-1",
      "availabilityStateId": "state-break",
      "availabilityStateName": "break",
      "availabilityStateDisplayName": "On Break"
    }
  ],
  "noCallsOffered": 45,
  "noCallsAnswered": 42,
  "noCallsMissed": 3,
  "timeInCurrentPresenceState": 3600,
  "timeInCurrentAvailabilityState": 1800,
  "timeInCurrentCall": 245
}
```

#### Relationships

- References `AgentGroup` via `groupMembership`
- Contains array of `AvailabilityState` in `filtredAvailabilityStatesList`
- Links to calls via `callUuid`

---

### AgentStatusUser

Data model for agent status table rows, providing a simplified view of agent state for status displays.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | string | Yes | Unique identifier for the user |
| `name` | string | Yes | Agent name |
| `profile` | string | No | Agent profile |
| `stateName` | string | No | Current state name (internal) |
| `stateDisplayName` | string | No | Display name for current state |
| `time` | string | No | Date and time of status change |
| `elapsed` | number | No | Elapsed time in seconds since status change |
| `isElapsedTimeStop` | boolean | No | Whether elapsed time counter should stop |

#### Example

```json
{
  "userId": "user-67890",
  "name": "Jane Doe",
  "profile": "Sales Agent",
  "stateName": "on_break",
  "stateDisplayName": "On Break",
  "time": "2024-01-15T10:30:00Z",
  "elapsed": 900,
  "isElapsedTimeStop": false
}
```

---

### AgentLoginUser

Data model for tracking agent login and logout events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | string | Yes | Unique identifier for the user |
| `name` | string | Yes | Agent name |
| `groupName` | string | No | Name of the group |
| `event` | string | Yes | Login or logout event type |
| `isLogin` | boolean | Yes | Whether event is login (true) or logout (false) |
| `time` | string | Yes | Date and time of event |
| `elapsed` | number | No | Elapsed time in seconds since event |
| `isElapsedTimeStop` | boolean | No | Whether elapsed time counter should stop |

#### Example

```json
{
  "userId": "user-11111",
  "name": "Bob Wilson",
  "groupName": "Customer Support",
  "event": "LOGIN",
  "isLogin": true,
  "time": "2024-01-15T08:00:00Z",
  "elapsed": 14400,
  "isElapsedTimeStop": false
}
```

---

### AgentCardProps

Props and data model for the agent card component, used for individual agent display cards on wallboards.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string \| number | Yes | Agent unique identifier |
| `name` | string | Yes | Agent name |
| `ext` | string | No | Agent extension number |
| `callQueueId` | string \| number | No | Current call queue ID |
| `availabilityStateOrScvStatus` | string | No | Current availability state or SCV status |
| `totalTime` | number | No | Total time in seconds |
| `callTime` | number | No | Current call time in seconds |
| `isCallbackCall` | boolean | No | Whether this is a callback call |
| `callUuid` | string | No | UUID of current call |
| `callStatusKey` | string | No | Key for call status styling |
| `canCallAgents` | boolean | No | Permission to call agents |
| `canTerminateCall` | boolean | No | Permission to terminate calls |
| `canListenLive` | boolean | No | Permission to listen live |
| `isAvailabilityStateDropdownDisabled` | boolean | No | Whether availability dropdown is disabled |
| `filtredAvailabilityStatesList` | array | No | List of filtered availability states |

#### Example

```json
{
  "id": "agent-22222",
  "name": "Sarah Johnson",
  "ext": "2001",
  "callQueueId": "queue-support-001",
  "availabilityStateOrScvStatus": "On Call",
  "totalTime": 28800,
  "callTime": 180,
  "isCallbackCall": false,
  "callUuid": "call-xyz-789",
  "callStatusKey": "active-call",
  "canCallAgents": true,
  "canTerminateCall": true,
  "canListenLive": true,
  "isAvailabilityStateDropdownDisabled": true,
  "filtredAvailabilityStatesList": []
}
```

---

## Agent Group Models

### AgentGroup

Model for organizing agents into logical groups for management and reporting.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `groupId` | string | Yes | Unique identifier for the group |
| `groupName` | string | Yes | Display name of the group |

#### Validation Rules

- `groupId` must be unique across the organization
- `groupName` should be descriptive and human-readable

#### Example

```json
{
  "groupId": "group-sales-001",
  "groupName": "Sales Team - North Region"
}
```

```json
{
  "groupId": "group-support-002",
  "groupName": "Technical Support"
}
```

#### Relationships

- Referenced by `Agent.groupMembership`
- Used for filtering and grouping in agent widgets

---

## Availability State Models

### AvailabilityState

Defines an availability state option that can be assigned to agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `availabilityProfileId` | string | Yes | Profile ID for the availability state |
| `availabilityStateId` | string | Yes | State ID |
| `availabilityStateName` | string | Yes | Internal state name |
| `availabilityStateDisplayName` | string | Yes | Display name for the state |

#### Example

```json
{
  "availabilityProfileId": "profile-default",
  "availabilityStateId": "state-001",
  "availabilityStateName": "available",
  "availabilityStateDisplayName": "Available"
}
```

```json
{
  "availabilityProfileId": "profile-default",
  "availabilityStateId": "state-002",
  "availabilityStateName": "lunch_break",
  "availabilityStateDisplayName": "Lunch Break"
}
```

#### Common Availability States

| State Name | Display Name | Description |
|------------|--------------|-------------|
| `available` | Available | Agent ready to receive calls |
| `on_break` | On Break | Agent on scheduled break |
| `lunch_break` | Lunch Break | Agent on lunch break |
| `meeting` | In Meeting | Agent in a meeting |
| `training` | Training | Agent in training |
| `wrap_up` | Wrap Up | Agent completing post-call work |
| `offline` | Offline | Agent logged out or unavailable |

---

### AvailabilityProfile

Agent availability profile configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Profile identifier |

#### Example

```json
{
  "id": "profile-sales-team"
}
```

---

## Queue Models

### QueueCall

Data model representing a call in a queue, used for queue list tables and real-time monitoring.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `callUuid` | string | Yes | Unique identifier for the call |
| `priority` | number | No | Call priority (1-10+, lower is higher priority) |
| `positionInQueue` | number | No | Current position in queue |
| `timeWaitingInQueue` | number | No | Time waiting in queue (seconds) |
| `callerNumber` | string | No | Caller phone number |
| `timeAtHeadOfQueue` | number | No | Time at head of queue (seconds) |
| `nextCallbackAttempt` | number | No | Timestamp for next callback attempt |
| `callbackRequested` | boolean | No | Whether callback was requested |
| `callbackAttempts` | number | No | Number of callback attempts made |
| `skillsRequested` | array | No | Array of requested skill names |
| `skillsShortage` | boolean | No | Whether there is a skills shortage |
| `status` | string | No | Call status (connected, waiting, etc.) |
| `call` | object | No | Nested call object with additional details |
| `agent` | object | No | Agent object if call is connected |

#### Validation Rules

- `callUuid` must be unique
- `priority` typically ranges from 1-10 (1 being highest priority)
- `positionInQueue` must be a positive integer
- Time fields are in seconds and must be non-negative

#### Example

```json
{
  "callUuid": "call-queue-12345",
  "priority": 2,
  "positionInQueue": 3,
  "timeWaitingInQueue": 120,
  "callerNumber": "+1-555-123-4567",
  "timeAtHeadOfQueue": 0,
  "nextCallbackAttempt": null,
  "callbackRequested": false,
  "callbackAttempts": 0,
  "skillsRequested": ["Sales", "Spanish"],
  "skillsShortage": false,
  "status": "waiting",
  "call": {
    "direction": "inbound",
    "startTime": "2024-01-15T14:30:00Z"
  },
  "agent": null
}
```

#### Callback Example

```json
{
  "callUuid": "callback-67890",
  "priority": 1,
  "positionInQueue": 1,
  "timeWaitingInQueue": 600,
  "callerNumber": "+1-555-987-6543",
  "timeAtHeadOfQueue": 45,
  "nextCallbackAttempt": 1705329600000,
  "callbackRequested": true,
  "callbackAttempts": 2,
  "skillsRequested": ["Technical Support"],
  "skillsShortage": true,
  "status": "callback_pending",
  "call": {
    "direction": "callback",
    "startTime": "2024-01-15T14:20:00Z"
  },
  "agent": null
}
```

#### Relationships

- May reference `Agent` via `agent` field when connected
- Contains skill references that relate to `Skill` model

---

## Skill Models

### Skill

Individual skill entity that can be assigned to agents and requested for calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | number \| string | Yes | Unique identifier for the skill |
| `name` | string | Yes | Skill name |
| `description` | string | No | Skill description |

#### Example

```json
{
  "id": "skill-001",
  "name": "Spanish",
  "description": "Spanish language proficiency"
}
```

```json
{
  "id": 42,
  "name": "Technical Support L2",
  "description": "Level 2 technical support for complex issues"
}
```

---

### SkillsSelection

State model for managing skill selection in agent and queue list configurations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selectAll` | boolean | No | Whether all skills are selected |
| `selectNone` | boolean | No | Whether no skills are selected |
| `selectedItems` | array | No | Array of selected skill IDs |

#### Validation Rules

- `selectAll` and `selectNone` should not both be true
- `selectedItems` should contain valid skill IDs

#### Example

```json
{
  "selectAll": false,
  "selectNone": false,
  "selectedItems": ["skill-001", "skill-003", "skill-007"]
}
```

---

## Widget Configuration Models

### AgentStatusWidget

Widget configuration for agent status display panels.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Widget unique identifier |
| `isShowStateName` | boolean | No | Whether to show state name column |
| `isShowDisplayName` | boolean | No | Whether to show state display name column |
| `limitResult` | object | No | Object containing value property for result limit |

#### Example

```json
{
  "id": "widget-agent-status-001",
  "isShowStateName": false,
  "isShowDisplayName": true,
  "limitResult": {
    "value": 25
  }
}
```

---

### AgentTableColumns

Configuration object defining which columns to display in agent list tables.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isAgentNameColumn` | boolean | No | Show agent name column |
| `isCurrAvaiStateColumn` | boolean | No | Show current availability state column |
| `isAgentExtNoColumn` | boolean | No | Show agent extension number column |
| `isNoCallsOfferedColumn` | boolean | No | Show calls offered column |
| `isNoCallsAnsweredColumn` | boolean | No | Show calls answered column |
| `isNoCallsMissedColumn` | boolean | No | Show calls missed column |
| `isTimeInCurrentPresenceStateColumn` | boolean | No | Show time in presence state column |
| `isTimeInCurrentAvailabilityStateColumn` | boolean | No | Show time in availability state column |
| `isTimeInCurrentCallColumn` | boolean | No | Show time on current call column |
| `isTimeInCurrentWrapupColumn` | boolean | No | Show time in wrapup column |
| `isListOfSkillsColumn` | boolean | No | Show skills column |
| `isCurrPresStateColumn` | boolean | No | Show current presence state column |

#### Example

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

---

### QueueListWidget

Widget configuration for queue list display panels.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Widget unique identifier |
| `sortBy` | string | No | Column to sort by |
| `columnsToViewOptions` | object | No | Object with `selectedItems` array of column keys |
| `interactivityOptions` | object | No | Object with `selectedItems` array of interactivity options |
| `timeInQueueSLATime` | number | No | SLA time threshold for queue wait time (seconds) |
| `timeAtHeadOfQueueSLATime` | number | No | SLA time threshold for head of queue (seconds) |
| `isShowOnlyOnHover` | boolean | No | Show skills only on hover |
| `callQueue` | object | No | Call queue object with `id` property |

#### Example

```json
{
  "id": "widget-queue-list-001",
  "sortBy": "timeWaitingInQueue",
  "columnsToViewOptions": {
    "selectedItems": ["callerNumber", "timeWaitingInQueue", "positionInQueue", "priority"]
  },
  "interactivityOptions": {
    "selectedItems": ["answerCall", "transferCall"]
  },
  "timeInQueueSLATime": 60,
  "timeAtHeadOfQueueSLATime": 30,
  "isShowOnlyOnHover": true,
  "callQueue": {
    "id": "queue-support-001"
  }
}
```

---

## Permission Models

### ListenInPermissions

Permissions configuration for the listen-in functionality that allows supervisors to monitor agent calls.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `availableListenInAgentIds` | object | No | Object mapping agent IDs to permission status |

#### Example

```json
{
  "availableListenInAgentIds": {
    "agent-001": true,
    "agent-002": true,
    "agent-003": false,
    "agent-004": true
  }
}
```

---

## Filter Configuration Models

### AgentListData

Modal data model for agent list widget configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isEditMode` | boolean | No | Whether in edit mode |
| `filterAlgorithm` | string | No | Filter algorithm (`RELATIVE` or `ABSOLUTE`) |
| `skillsToView` | SkillsSelection | No | Skills selection configuration |

#### Example

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

Modal data model for queue list widget configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isEditMode` | boolean | No | Whether in edit mode |
| `filterAlgorithm` | string | No | Filter algorithm (`RELATIVE` or `ABSOLUTE`) |
| `skillsToView` | SkillsSelection | No | Skills selection configuration |

#### Example

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

Modal data model for queue status widget configuration.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filterAlgorithm` | string | No | Filter algorithm |
| `skillsToView` | SkillsSelection | No | Skills selection configuration |

#### Example

```json
{
  "filterAlgorithm": "RELATIVE",
  "skillsToView": {
    "selectAll": false,
    "selectNone": false,
    "selectedItems": ["skill-005", "skill-006", "skill-007"]
  }
}
```

---

### FilterAlgorithmOption

Option model for filter algorithm dropdown selections.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | string | Yes | Option value (`RELATIVE` or `ABSOLUTE`) |
| `label` | string | Yes | Display label for option |

#### Example

```json
[
  {
    "value": "RELATIVE",
    "label": "Relative - Show agents with any matching skills"
  },
  {
    "value": "ABSOLUTE",
    "label": "Absolute - Show agents with all required skills"
  }
]
```

---

## Entity Relationships

```
┌─────────────────┐       ┌─────────────────┐
│   AgentGroup    │◄──────│     Agent       │
│                 │   1:N │                 │
│  - groupId      │       │  - id           │
│  - groupName    │       │  - agentName    │
└─────────────────┘       │  - groupMember- │
                          │    ship         │
                          │  - filtredAvai- │
                          │    labilityS... │
                          └────────┬────────┘
                                   │
                                   │ contains
                                   ▼
                          ┌─────────────────┐
                          │AvailabilityState│
                          │                 │
                          │  - availability-│
                          │    ProfileId    │
                          │  - availability-│
                          │    StateId      │
                          │  - availability-│
                          │    StateName    │
                          └─────────────────┘
                          
┌─────────────────┐       ┌─────────────────┐
│    QueueCall    │───────│     Skill       │
│                 │  N:M  │                 │
│  - callUuid     │       │  - id           │
│  - skillsReq... │       │  - name         │
│  - agent        │       │  - description  │
└────────┬────────┘       └─────────────────┘
         │                        ▲
         │ may connect to         │ referenced by
         ▼                        │
┌─────────────────┐       ┌─────────────────┐
│     Agent       │       │SkillsSelection  │
│                 │       │                 │
└─────────────────┘       │  - selectAll    │
                          │  - selectedItems│
                          └─────────────────┘

Widget Configuration Relationships:

┌─────────────────┐       ┌─────────────────┐
│AgentStatusWidget│       │AgentTableColumns│
│                 │       │                 │
│  - id           │       │  - isAgentName- │
│  - isShowState- │       │    Column       │
│    Name         │       │  - isCurrAvai-  │
│  - limitResult  │       │    StateColumn  │
└─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│ QueueListWidget │───────│SkillsSelection  │
│                 │       │                 │
│  - id           │       │                 │
│  - callQueue    │       │                 │
│  - timeInQueue- │       │                 │
│    SLATime      │       │                 │
└─────────────────┘       └─────────────────┘
```

---

## Common Use Cases

### Displaying Real-time Agent Status

```javascript
// Fetch and display agent status
const agentStatusData = {
  userId: "agent-001",
  name: "John Smith",
  stateDisplayName: "Available",
  elapsed: 300,
  isElapsedTimeStop: false
};

// Widget configuration
const widget = {
  id: "status-widget-1",
  isShowStateName: false,
  isShowDisplayName: true,
  limitResult: { value: 10 }
};
```

### Monitoring Queue Calls

```javascript
// Queue call with SLA tracking
const queueCall = {
  callUuid: "call-12345",
  positionInQueue: 1,
  timeWaitingInQueue: 45,
  callerNumber: "+1-555-0100",
  skillsRequested: ["Sales", "English"],
  status: "waiting"
};

// Check against SLA thresholds
const widget = {
  timeInQueueSLATime: 60,
  timeAtHeadOfQueueSLATime: 30
};

const isWithinSLA = queueCall.timeWaitingInQueue < widget.timeInQueueSLATime;
```

### Filtering Agents by Skills

```javascript
// Skills selection for filtering
const skillsFilter = {
  selectAll: false,
  selectNone: false,
  selectedItems: ["skill-spanish", "skill-sales"]
};

// Filter algorithm determines matching behavior
const filterConfig = {
  filterAlgorithm: "RELATIVE", // Match ANY skill
  skillsToView: skillsFilter
};
```