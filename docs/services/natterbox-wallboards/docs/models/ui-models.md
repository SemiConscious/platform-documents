# UI State Models

This document covers the data models used for UI state management in the Natterbox Wallboards application, including modal states, dropdown controls, error handling, and notification systems.

## Overview

The UI state models manage the interactive elements and user feedback systems throughout the application. These models are primarily used with Redux for centralized state management and React components for local state.

## Entity Relationships

```
┌─────────────────────┐
│    ModalState       │
│  (Redux Slice)      │
├─────────────────────┤
│ - warningMessage    │
│ - activeModalNames  │
└─────────────────────┘
         │
         │ controls
         ▼
┌─────────────────────┐      ┌─────────────────────┐
│   DropdownProps     │      │  NotificationState  │
│  (Component Props)  │      │   (Redux Slice)     │
├─────────────────────┤      ├─────────────────────┤
│ - isOpen            │      │ - status            │
│ - trigger           │      │ - notificationMsg   │
│ - children          │      │ - notificationTime  │
└─────────────────────┘      └─────────────────────┘
                                      │
                                      │ informs
                                      ▼
                             ┌─────────────────────┐
                             │   ErrorLogState     │
                             │   (Redux Slice)     │
                             ├─────────────────────┤
                             │ - requestIndex      │
                             │ - errors array      │
                             └─────────────────────┘
```

---

## Modal State Models

### ModalState

Redux state slice for managing modal dialogs and warning messages throughout the application.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `warningMessage` | `string` | No | Warning message to display in modal dialog |
| `activeModalNames` | `array` | No | Array of currently active modal names/identifiers |

**Validation Rules:**
- `warningMessage` should be a non-empty string when set
- `activeModalNames` should contain unique string identifiers
- Modal names should match predefined constants for consistency

**Example JSON:**
```json
{
  "warningMessage": "You have unsaved changes. Are you sure you want to leave?",
  "activeModalNames": ["CONFIRM_DELETE", "WIDGET_SETTINGS"]
}
```

**Relationships:**
- Controls visibility of modal components across the application
- Interacts with `Wallboard` and `Widget` models during edit operations
- Used by toolbar components for confirmation dialogs

**Common Use Cases:**
- Displaying confirmation dialogs before destructive actions
- Showing warning messages for unsaved changes
- Managing multiple modal layers simultaneously

---

### WarningMode

Configuration object for displaying warning states on agent cards and other components.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `className` | `string` | Yes | CSS class name for styling the warning state |
| `status` | `string` | Yes | Status text to display to the user |

**Validation Rules:**
- `className` must be a valid CSS class name (no spaces, starts with letter)
- `status` should be a human-readable string

**Example JSON:**
```json
{
  "className": "warning-mode--critical",
  "status": "Agent unavailable"
}
```

**Relationships:**
- Used by `AgentCardProps` for visual warning indicators
- Applied based on `AgentStatusUser` state changes

---

## Dropdown Controls

### DropdownProps

Props interface for the reusable Dropdown component, supporting multiple interaction modes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trigger` | `ReactNode` | Yes | Element that triggers the dropdown to open |
| `className` | `string` | No | CSS class for the dropdown wrapper element |
| `containerClassName` | `string` | No | CSS class for the dropdown container |
| `triggerClassName` | `string` | No | CSS class for the trigger element |
| `closeOnHover` | `boolean` | No | Close dropdown when mouse leaves (default: false) |
| `openOnHover` | `boolean` | No | Open dropdown on mouse enter (default: false) |
| `closeOnClick` | `boolean` | No | Close dropdown when clicking inside (default: true) |
| `openOnOverflowOnly` | `boolean` | No | Only open if trigger content overflows |
| `isDisable` | `boolean` | No | Disable all dropdown functionality |
| `isOpen` | `boolean` | No | Controlled open state for external management |
| `closeAllDropdownOnOpen` | `boolean` | No | Close all other dropdowns when this one opens |
| `children` | `ReactNode` | Yes | Content to render inside the dropdown |

**Validation Rules:**
- `trigger` must be a valid React node
- `children` must be a valid React node
- Boolean props default to `false` if not specified
- `isOpen` should be used with an external state management system

**Example JSON (as component usage):**
```json
{
  "trigger": "<Button>Select Option</Button>",
  "className": "dropdown--primary",
  "containerClassName": "dropdown-container",
  "closeOnHover": false,
  "openOnHover": true,
  "closeOnClick": true,
  "openOnOverflowOnly": false,
  "isDisable": false,
  "isOpen": false,
  "closeAllDropdownOnOpen": true
}
```

**Relationships:**
- Used by `AvailabilityState` dropdowns in agent components
- Integrated with `AgentCardProps` for status selection
- Used in filter and sorting controls

**Common Use Cases:**
- Agent availability state selection
- Column visibility toggles in tables
- Filter option menus
- Context menus for widget actions

---

## Error Handling

### ErrorLogState

Redux state slice for tracking API request errors and managing retry logic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestIntervalIndex` | `number` | Yes | Current index into the error log intervals array |
| `requestIndex` | `number` | Yes | Current sequential request identifier |
| `fetchWidgetData` | `function` | No | Function reference for fetching widget data |
| `requestsIndexesWithError` | `array` | Yes | Array of request indexes that encountered errors |

**Validation Rules:**
- `requestIntervalIndex` must be a non-negative integer
- `requestIndex` must be a non-negative integer
- `requestsIndexesWithError` should contain unique integers
- `fetchWidgetData` must be a callable function when set

**Example JSON:**
```json
{
  "requestIntervalIndex": 2,
  "requestIndex": 15,
  "fetchWidgetData": null,
  "requestsIndexesWithError": [3, 7, 12]
}
```

**Relationships:**
- Monitors requests from all widget data fetching operations
- Triggers retry logic based on error patterns
- Integrates with `NotificationState` to display error messages

**Common Use Cases:**
- Tracking failed API requests for retry
- Implementing exponential backoff for failed requests
- Logging errors for debugging purposes
- Determining when to show error notifications

---

## Notification System

### NotificationState

Redux state slice for managing user notifications and toast messages.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `string` | Yes | Notification status type (SUCCESS, WARN, ERROR, NULL) |
| `notificationMessage` | `string` | No | Message content to display in the notification |
| `notificationTime` | `number` | No | Duration to show notification in milliseconds |

**Validation Rules:**
- `status` must be one of: `SUCCESS`, `WARN`, `ERROR`, `NULL`
- `notificationMessage` should be non-empty when status is not `NULL`
- `notificationTime` should be a positive integer (typical range: 3000-10000ms)
- Setting status to `NULL` clears the notification

**Example JSON:**
```json
{
  "status": "SUCCESS",
  "notificationMessage": "Wallboard saved successfully",
  "notificationTime": 5000
}
```

**Status Values:**

| Status | Purpose | Styling |
|--------|---------|---------|
| `SUCCESS` | Positive confirmation messages | Green/success color |
| `WARN` | Warning messages requiring attention | Yellow/warning color |
| `ERROR` | Error messages for failed operations | Red/error color |
| `NULL` | Clear notification / no notification | Hidden |

**Relationships:**
- Triggered by `Wallboard` save/delete operations
- Updated based on `ErrorLogState` error patterns
- Used for feedback on `Widget` configuration changes

**Common Use Cases:**
- Confirming successful save operations
- Displaying API error messages to users
- Warning about potential issues
- Providing feedback for user actions

---

## Component Props Models

### TimeIntervalProps

Props for the TimeInterval component that displays an animated timer.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isStop` | `boolean` | No | Whether the timer is currently stopped |
| `isInfinit` | `boolean` | No | Whether the timer should run indefinitely |
| `seconds` | `number` | Yes | Initial seconds value to start the timer from |

**Validation Rules:**
- `seconds` must be a non-negative integer
- When `isStop` is true, the timer freezes at current value
- When `isInfinit` is true, timer counts up without limit

**Example JSON:**
```json
{
  "isStop": false,
  "isInfinit": true,
  "seconds": 145
}
```

**Relationships:**
- Used by `AgentStatusUser` to display elapsed time
- Integrated with `QueueCall` for wait time display
- Controlled by `Agent` call state changes

---

### TimePickerProps

Props for the TimePicker component used in configuration forms.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Input name attribute for form handling |
| `isOnTop` | `boolean` | No | Whether the picker popup appears above the input |
| `onChange` | `function` | Yes | Callback function when time value changes |
| `labelText` | `string` | No | Label text displayed above the picker |
| `placeholder` | `string` | No | Placeholder text when no value selected |
| `disabled` | `boolean` | No | Whether the picker is disabled |
| `value` | `string` | No | Current time value in HH:mm:ss format |

**Validation Rules:**
- `name` must be a valid HTML input name
- `value` must match format `HH:mm:ss` (e.g., "08:30:00")
- `onChange` must be a callable function

**Example JSON:**
```json
{
  "name": "slaThreshold",
  "isOnTop": false,
  "labelText": "SLA Threshold Time",
  "placeholder": "Select time",
  "disabled": false,
  "value": "00:05:00"
}
```

**Relationships:**
- Used in `QueueListWidget` for SLA configuration
- Integrated with wallboard scheduling features

---

### TimeOption

Individual time option used in TimePicker dropdown lists.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `string` | Yes | Unique key identifier for the option |
| `text` | `string` | Yes | Display text with leading zero formatting |
| `value` | `number` | Yes | Numeric value of the time unit |

**Validation Rules:**
- `key` must be unique within the options list
- `text` should have leading zeros for single digits (e.g., "05")
- `value` must be within valid range for time unit (0-23 for hours, 0-59 for minutes/seconds)

**Example JSON:**
```json
{
  "key": "minute-15",
  "text": "15",
  "value": 15
}
```

---

### ProgressBarProps

Props for the progress bar component used in various displays.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `width` | `number` | Yes | Progress percentage from 0 to 100 |
| `modifier` | `string` | No | CSS modifier class name for styling variants |

**Validation Rules:**
- `width` must be between 0 and 100 (inclusive)
- `modifier` should be a valid CSS class modifier

**Example JSON:**
```json
{
  "width": 75,
  "modifier": "progress-bar--success"
}
```

**Relationships:**
- Used in queue displays for SLA visualization
- Integrated with widget loading states

---

### CheckBoxProps

Props for the reusable CheckBox component.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | `string` | No | Label text displayed next to the checkbox |
| `className` | `string` | No | Additional CSS classes to apply |
| `isGrey` | `boolean` | No | Whether to use grey/muted styling |
| `disabled` | `boolean` | No | Whether the checkbox is disabled |

**Validation Rules:**
- Boolean props default to `false`
- `className` should be valid CSS class names

**Example JSON:**
```json
{
  "label": "Show elapsed time",
  "className": "checkbox--small",
  "isGrey": false,
  "disabled": false
}
```

**Relationships:**
- Used in `AgentTableColumns` configuration
- Integrated with widget settings forms
- Used for filter selections in modals

---

### AutoWidthInputProps

Props for an input component that automatically resizes based on content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | `string` | Yes | Input value that determines the width |

**Validation Rules:**
- `value` can be any string including empty
- Width calculation includes padding buffer

**Example JSON:**
```json
{
  "value": "My Custom Wallboard Name"
}
```

**Relationships:**
- Used for editable wallboard and widget names
- Integrated with inline editing features

---

### CustomAutosuggestProps

Props for the autosuggest/autocomplete component.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allTitles` | `string[]` | Yes | Array of all possible suggestion values |
| `value` | `string` | Yes | Current input value |
| `name` | `string` | Yes | Input name attribute |
| `placeholder` | `string` | No | Placeholder text when empty |
| `isSmallSize` | `boolean` | No | Whether to use smaller styling |
| `onChange` | `function` | Yes | Change handler callback function |
| `isSuggestionHidden` | `boolean` | No | Whether to hide suggestions list |

**Validation Rules:**
- `allTitles` must be an array of strings
- `onChange` must be a callable function
- `name` must be a valid HTML input name

**Example JSON:**
```json
{
  "allTitles": ["Sales Queue", "Support Queue", "Billing Queue"],
  "value": "Sales",
  "name": "queueSearch",
  "placeholder": "Search queues...",
  "isSmallSize": false,
  "isSuggestionHidden": false
}
```

**Relationships:**
- Used in wallboard and widget search features
- Integrated with queue and agent selection

---

### ToolbarProps

Props for the main Toolbar component.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template` | `string` | Yes | Toolbar template name from DEFAULTS.TOOLBAR.NAME |
| `wbName` | `string` | No | Wallboard name for read-only views |
| `children` | `ReactNode` | No | Child components to render in toolbar |

**Validation Rules:**
- `template` must match a predefined toolbar template constant
- `wbName` is required when in read-only mode

**Example JSON:**
```json
{
  "template": "WALLBOARD_VIEW",
  "wbName": "Sales Dashboard",
  "children": null
}
```

**Relationships:**
- Contains navigation and action controls
- Integrates with `Wallboard` for edit/save operations
- Uses `ModalState` for confirmation dialogs

---

## Selection State Models

### SkillsSelection

State model for managing skill selection in filter interfaces.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selectAll` | `boolean` | Yes | Whether all skills are selected |
| `selectNone` | `boolean` | Yes | Whether no skills are selected |
| `selectedItems` | `array` | Yes | Array of selected skill IDs |

**Validation Rules:**
- `selectAll` and `selectNone` should be mutually exclusive
- When `selectAll` is true, `selectedItems` should contain all skill IDs
- When `selectNone` is true, `selectedItems` should be empty

**Example JSON:**
```json
{
  "selectAll": false,
  "selectNone": false,
  "selectedItems": ["skill-1", "skill-3", "skill-7"]
}
```

**Relationships:**
- Used by `AgentListData` for filtering agents by skills
- Used by `QueueListData` for filtering queue calls
- Used by `QueueStatusData` for status filtering
- References `Skill` model for available options

---

### FilterAlgorithmOption

Option model for filter algorithm dropdown selections.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | `string` | Yes | Option value (RELATIVE or ABSOLUTE) |
| `label` | `string` | Yes | Display label shown to user |

**Validation Rules:**
- `value` must be either `RELATIVE` or `ABSOLUTE`
- `label` should be human-readable

**Example JSON:**
```json
{
  "value": "RELATIVE",
  "label": "Relative Time"
}
```

**Filter Algorithm Types:**

| Value | Description |
|-------|-------------|
| `RELATIVE` | Filters based on relative time periods |
| `ABSOLUTE` | Filters based on absolute timestamps |

---

## Modal Data Models

### AgentListData

Data model for agent list widget configuration modal.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isEditMode` | `boolean` | Yes | Whether the modal is in edit mode |
| `filterAlgorithm` | `string` | Yes | Filter algorithm type (RELATIVE or ABSOLUTE) |
| `skillsToView` | `SkillsSelection` | Yes | Skills selection configuration |

**Example JSON:**
```json
{
  "isEditMode": true,
  "filterAlgorithm": "RELATIVE",
  "skillsToView": {
    "selectAll": false,
    "selectNone": false,
    "selectedItems": ["skill-1", "skill-2"]
  }
}
```

---

### QueueListData

Data model for queue list widget configuration modal.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isEditMode` | `boolean` | Yes | Whether the modal is in edit mode |
| `filterAlgorithm` | `string` | Yes | Filter algorithm type (RELATIVE or ABSOLUTE) |
| `skillsToView` | `SkillsSelection` | Yes | Skills selection configuration |

**Example JSON:**
```json
{
  "isEditMode": false,
  "filterAlgorithm": "ABSOLUTE",
  "skillsToView": {
    "selectAll": true,
    "selectNone": false,
    "selectedItems": ["skill-1", "skill-2", "skill-3"]
  }
}
```

---

### QueueStatusData

Data model for queue status widget configuration modal.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filterAlgorithm` | `string` | Yes | Filter algorithm type (RELATIVE or ABSOLUTE) |
| `skillsToView` | `SkillsSelection` | Yes | Skills selection configuration |

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

## Drag and Drop

### DragDropElement

Element model for drag and drop list functionality.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique identifier for the draggable element |
| `isEnabled` | `boolean` | Yes | Whether the element can be dragged |
| `content` | `ReactNode` | Yes | Content to render inside the element |

**Validation Rules:**
- `id` must be unique within the drag/drop context
- `content` must be a valid React node

**Example JSON:**
```json
{
  "id": "column-agent-name",
  "isEnabled": true,
  "content": "<ColumnHeader>Agent Name</ColumnHeader>"
}
```

**Relationships:**
- Used for reordering `AgentTableColumns`
- Integrated with widget configuration panels
- Used in wallboard step reordering

---

## Related Documentation

- [Authentication Models](./auth-models.md) - Auth0 and login state models
- [Agent Models](./agent-models.md) - Agent data and status models
- [Wallboard Models](./wallboard-models.md) - Wallboard configuration models
- [Widget Models](./widget-models.md) - Widget configuration and display models