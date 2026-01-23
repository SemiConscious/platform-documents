# Wallboard Configuration Models

This document covers the data models used for wallboard configuration, layouts, settings, and wallboard groups in the Natterbox Wallboards application.

## Overview

Wallboard configuration models define the structure and behavior of wallboards, including:
- Main wallboard structure and metadata
- Widget positioning and sizing on the grid
- Display and sharing settings
- Wallboard groups for cycling through multiple wallboards
- Step configurations for timed rotations

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WALLBOARD CONFIGURATION                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐         ┌─────────────────────┐                    │
│  │  WallboardGroup │────────▶│ WallboardGroupStep  │                    │
│  │                 │   1:N   │                     │                    │
│  │  - id           │         │  - stepId           │                    │
│  │  - name         │         │  - wallboardId      │                    │
│  │  - timeInterval │         │  - time             │                    │
│  │  - steps[]      │         └─────────┬───────────┘                    │
│  │  - settings     │                   │                                │
│  └────────┬────────┘                   │ references                     │
│           │                            ▼                                │
│           │              ┌─────────────────────────┐                    │
│           └─────────────▶│       Wallboard         │◀────────┐          │
│                          │                         │         │          │
│                          │  - id                   │         │          │
│                          │  - name                 │         │          │
│                          │  - widgets[]            │         │          │
│                          │  - settings             │         │          │
│                          │  - createdBy            │         │          │
│                          └───────────┬─────────────┘         │          │
│                                      │                       │          │
│                          ┌───────────┼───────────┐           │          │
│                          │           │           │           │          │
│                          ▼           ▼           ▼           │          │
│              ┌───────────────┐ ┌───────────┐ ┌────────────┐  │          │
│              │WallboardSettings│ │  Widget   │ │LinkSettings│  │          │
│              │               │ │           │ │            │  │          │
│              │  - display    │ │  - id     │ │-isReadOnly │  │          │
│              │  - link       │ │  - size   │ │ Enabled    │  │          │
│              └───────┬───────┘ └─────┬─────┘ └────────────┘  │          │
│                      │               │                       │          │
│                      ▼               ▼                       │          │
│              ┌───────────────┐ ┌─────────────┐               │          │
│              │DisplaySettings│ │GridComponent│               │          │
│              │               │ │             │               │          │
│              │-shrinkHeight  │ │  - width    │               │          │
│              │-shrinkWidth   │ │  - height   │               │          │
│              └───────────────┘ │  - startX   │               │          │
│                                │  - endX     │               │          │
│                                │  - startY   │               │          │
│                                │  - endY     │               │          │
│                                └─────────────┘               │          │
│                                                              │          │
│  ┌────────────────┐                                          │          │
│  │     Step       │──────────────────────────────────────────┘          │
│  │                │  references (wallboardFulData)                      │
│  │  - stepId      │                                                     │
│  │  - stepTime    │                                                     │
│  │  - wallboard   │                                                     │
│  │    Name        │                                                     │
│  └────────────────┘                                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Wallboard Models

### Wallboard

The main wallboard data model representing a complete wallboard configuration.

#### Purpose
Represents a single wallboard instance containing all widgets, settings, and metadata. This is the primary entity users create and manage.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique wallboard identifier (UUID) |
| `name` | string | Yes | Wallboard display name |
| `description` | string | No | Description of the wallboard |
| `widgets` | Widget[] | Yes | Array of widgets on the wallboard |
| `isNewWallboard` | boolean | No | Whether this is a newly created wallboard (not yet saved) |
| `createdBy` | string | No | Name of the creator |
| `createdByUserId` | string | No | User ID of the creator |
| `createdOn` | number | No | Timestamp when wallboard was created |
| `settings` | WallboardSettings | Yes | Wallboard settings object |

#### Validation Rules
- `id` must be a valid UUID
- `name` is required and must be non-empty
- `widgets` array can be empty but must be present
- `settings` object is required

#### Example JSON
```json
{
  "id": "wb-550e8400-e29b-41d4-a716-446655440000",
  "name": "Sales Team Dashboard",
  "description": "Real-time metrics for the sales team",
  "widgets": [
    {
      "id": "widget-123-456",
      "size": {
        "id": "widget-123-456",
        "width": 400,
        "widthProcent": 50,
        "height": 300,
        "heightProcent": 50,
        "startX": 0,
        "startXProcent": 0,
        "endX": 400,
        "endXProcent": 50,
        "startY": 0,
        "startYProcent": 0,
        "endY": 300,
        "endYProcent": 50
      }
    }
  ],
  "isNewWallboard": false,
  "createdBy": "John Smith",
  "createdByUserId": "user-789",
  "createdOn": 1699876543210,
  "settings": {
    "display": {
      "shrinkHeight": true,
      "shrinkWidth": true
    },
    "link": {
      "isReadOnlyEnabled": false
    }
  }
}
```

#### Relationships
- Contains multiple **Widget** objects
- Contains one **WallboardSettings** object
- Referenced by **WallboardGroupStep** via `wallboardId`
- Referenced by **Step** via `wallboardFulData`

---

### WallboardSettings

Settings container for a wallboard.

#### Purpose
Groups all configurable settings for a wallboard including display behavior and sharing options.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display` | DisplaySettings | Yes | Display-related settings |
| `link` | LinkSettings | Yes | Link/sharing settings |

#### Validation Rules
- Both `display` and `link` objects are required

#### Example JSON
```json
{
  "display": {
    "shrinkHeight": true,
    "shrinkWidth": false
  },
  "link": {
    "isReadOnlyEnabled": true
  }
}
```

#### Relationships
- Contained within **Wallboard**
- Contains **DisplaySettings** and **LinkSettings**

---

### DisplaySettings

Display configuration options for wallboard rendering.

#### Purpose
Controls how the wallboard adapts to different screen sizes and resolutions.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `shrinkHeight` | boolean | Yes | Whether to shrink height to fit the screen |
| `shrinkWidth` | boolean | Yes | Whether to shrink width to fit the screen |

#### Validation Rules
- Boolean values required for both fields

#### Example JSON
```json
{
  "shrinkHeight": true,
  "shrinkWidth": true
}
```

#### Common Use Cases
- **Both true**: Wallboard scales proportionally to fit any screen
- **Both false**: Fixed size wallboard, may require scrolling
- **shrinkHeight only**: Maintains width, adjusts vertical space
- **shrinkWidth only**: Maintains height, adjusts horizontal space

---

### LinkSettings

Link and sharing settings for a wallboard.

#### Purpose
Controls whether the wallboard can be shared via read-only links.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isReadOnlyEnabled` | boolean | Yes | Whether read-only link sharing is enabled |

#### Validation Rules
- Must be a boolean value

#### Example JSON
```json
{
  "isReadOnlyEnabled": true
}
```

#### Use Cases
- When `true`, generates a shareable read-only URL
- When `false`, wallboard can only be viewed by authenticated users with access

---

## Grid and Layout Models

### Widget

Widget configuration including positioning information.

#### Purpose
Represents a widget instance on a wallboard with its size and position data.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the widget |
| `size` | GridComponent | Yes | Size and position information for the widget |

#### Validation Rules
- `id` must be unique within the wallboard
- `size` object is required for layout positioning

#### Example JSON
```json
{
  "id": "widget-agent-list-001",
  "size": {
    "id": "widget-agent-list-001",
    "width": 600,
    "widthProcent": 75,
    "height": 400,
    "heightProcent": 66.67,
    "startX": 0,
    "startXProcent": 0,
    "endX": 600,
    "endXProcent": 75,
    "startY": 0,
    "startYProcent": 0,
    "endY": 400,
    "endYProcent": 66.67
  }
}
```

#### Relationships
- Contained within **Wallboard.widgets** array
- Contains one **GridComponent** for positioning

---

### GridComponent

Represents a widget's position and size on the wallboard grid.

#### Purpose
Defines the exact positioning and dimensions of a widget using both pixel values and percentages for responsive layouts.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the grid component (matches widget ID) |
| `width` | number | Yes | Width of the component in pixels |
| `widthProcent` | number | Yes | Width as percentage of container (0-100) |
| `height` | number | Yes | Height of the component in pixels |
| `heightProcent` | number | Yes | Height as percentage of total height (0-100) |
| `startX` | number | Yes | Starting X position in pixels |
| `startXProcent` | number | Yes | Starting X position as percentage (0-100) |
| `endX` | number | Yes | Ending X position in pixels |
| `endXProcent` | number | Yes | Ending X position as percentage (0-100) |
| `startY` | number | Yes | Starting Y position in pixels |
| `startYProcent` | number | Yes | Starting Y position as percentage (0-100) |
| `endY` | number | Yes | Ending Y position in pixels |
| `endYProcent` | number | Yes | Ending Y position as percentage (0-100) |

#### Validation Rules
- All percentage values must be between 0 and 100
- `endX` must be greater than `startX`
- `endY` must be greater than `startY`
- Pixel values must be non-negative
- `width` should equal `endX - startX`
- `height` should equal `endY - startY`

#### Example JSON
```json
{
  "id": "widget-queue-status-002",
  "width": 400,
  "widthProcent": 50,
  "height": 250,
  "heightProcent": 41.67,
  "startX": 400,
  "startXProcent": 50,
  "endX": 800,
  "endXProcent": 100,
  "startY": 0,
  "startYProcent": 0,
  "endY": 250,
  "endYProcent": 41.67
}
```

#### Use Cases
- **Drag and drop positioning**: Updated when widgets are moved
- **Resize operations**: Updated when widgets are resized
- **Responsive rendering**: Percentage values enable scaling across screen sizes

---

## Wallboard Group Models

### WallboardGroup

Configuration for a group of wallboards that cycle through automatically.

#### Purpose
Allows multiple wallboards to rotate on a display, useful for dashboards showing different views on a schedule.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Wallboard group unique identifier |
| `name` | string | Yes | Wallboard group display name |
| `createdByUserId` | string | No | User ID of the creator |
| `isNewWallboardGroup` | boolean | No | Whether this is a new unsaved wallboard group |
| `timeInterval` | number | Yes | Default time interval for rotating between wallboards (seconds) |
| `steps` | WallboardGroupStep[] | Yes | Array of step objects defining the rotation |
| `settings` | WallboardGroupSettings | Yes | Settings object containing link configuration |

#### Validation Rules
- `id` must be a valid UUID
- `name` is required and non-empty
- `timeInterval` must be positive (typically 10-300 seconds)
- `steps` array must contain at least one step

#### Example JSON
```json
{
  "id": "wbg-660e8400-e29b-41d4-a716-446655440001",
  "name": "Call Center Overview Rotation",
  "createdByUserId": "user-admin-001",
  "isNewWallboardGroup": false,
  "timeInterval": 30,
  "steps": [
    {
      "stepId": "step-001",
      "wallboardId": "wb-550e8400-e29b-41d4-a716-446655440000",
      "time": 45
    },
    {
      "stepId": "step-002",
      "wallboardId": "wb-550e8400-e29b-41d4-a716-446655440001",
      "time": 30
    },
    {
      "stepId": "step-003",
      "wallboardId": null,
      "time": 15
    }
  ],
  "settings": {
    "link": {
      "isReadOnlyEnabled": true
    }
  }
}
```

#### Relationships
- Contains multiple **WallboardGroupStep** objects
- Contains one **WallboardGroupSettings** object
- References **Wallboard** objects via steps

---

### WallboardGroupStep

Individual step in a wallboard group rotation.

#### Purpose
Defines a single step in the wallboard rotation sequence, specifying which wallboard to display and for how long.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stepId` | string | Yes | Step unique identifier |
| `wallboardId` | string \| null | No | ID of associated wallboard, null if empty step |
| `time` | number | Yes | Time duration for this step in seconds |

#### Validation Rules
- `stepId` must be unique within the group
- `wallboardId` can be null for placeholder/empty steps
- `time` must be a positive number

#### Example JSON
```json
{
  "stepId": "step-sales-dashboard",
  "wallboardId": "wb-550e8400-e29b-41d4-a716-446655440000",
  "time": 60
}
```

#### Use Cases
- **Standard step**: References a wallboard with custom display time
- **Empty step**: `wallboardId` is null, can be used as placeholder during configuration

---

### WallboardGroupSettings

Settings container for wallboard group.

#### Purpose
Groups all configurable settings for a wallboard group, primarily sharing options.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `link` | WallboardGroupLinkSettings | Yes | Link settings object |

#### Example JSON
```json
{
  "link": {
    "isReadOnlyEnabled": true
  }
}
```

---

### WallboardGroupLinkSettings

Link sharing settings for wallboard group.

#### Purpose
Controls whether the wallboard group can be shared via read-only links.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isReadOnlyEnabled` | boolean | Yes | Whether read-only link access is enabled |

#### Example JSON
```json
{
  "isReadOnlyEnabled": false
}
```

---

### WallboardGroupFetchState

Redux state for wallboard group data fetching.

#### Purpose
Tracks the status of wallboard group fetch operations in the Redux store.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fetchStatus` | string | Yes | Fetch status enum value (SUCCESS, FAIL, PENDING, etc.) |
| `fetchMessage` | string | No | Message associated with fetch result |
| `statusCode` | number | No | HTTP status code from fetch operation |
| `wallboardGroup` | WallboardGroup | No | The wallboard group data when successfully fetched |

#### Example JSON
```json
{
  "fetchStatus": "SUCCESS",
  "fetchMessage": "Wallboard group loaded successfully",
  "statusCode": 200,
  "wallboardGroup": {
    "id": "wbg-660e8400-e29b-41d4-a716-446655440001",
    "name": "Call Center Overview Rotation",
    "timeInterval": 30,
    "steps": [],
    "settings": {
      "link": {
        "isReadOnlyEnabled": false
      }
    }
  }
}
```

---

## Slider and Step Models

### SliderProps

Props for the Slider component that cycles through wallboard slides.

#### Purpose
Configuration for the slider component that handles automatic rotation between wallboards in a group.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slides` | SlideStep[] | Yes | Array of slide steps to display |
| `timeInterval` | number | Yes | Default time interval between slide transitions in seconds |
| `setStepsWithWallboard` | function | Yes | State setter function for updating slides |

#### Validation Rules
- `slides` array should contain at least one slide
- `timeInterval` must be positive

---

### SlideStep

Individual slide/step in a wallboard group with full data.

#### Purpose
Extended step model that includes the full wallboard data for rendering.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stepId` | string | Yes | Unique identifier for the step |
| `wallboardId` | string | No | ID of the associated wallboard |
| `wallboardFulData` | Wallboard | No | Full wallboard data for the step |
| `stepTime` | number | Yes | Custom display time for this step in seconds |

#### Example JSON
```json
{
  "stepId": "slide-001",
  "wallboardId": "wb-550e8400-e29b-41d4-a716-446655440000",
  "stepTime": 45,
  "wallboardFulData": {
    "id": "wb-550e8400-e29b-41d4-a716-446655440000",
    "name": "Sales Team Dashboard",
    "widgets": [],
    "settings": {
      "display": {
        "shrinkHeight": true,
        "shrinkWidth": true
      },
      "link": {
        "isReadOnlyEnabled": false
      }
    }
  }
}
```

---

### Step

Step configuration for wallboard groups including preview data.

#### Purpose
Extended step model used in the wallboard group editor, including preview images and full wallboard data.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stepId` | string | Yes | Unique identifier for the step |
| `stepTime` | number | Yes | Duration of the step in seconds |
| `wallboardName` | string | No | Name of the wallboard for this step |
| `wallboardDescription` | string | No | Description of the wallboard |
| `wallboardFulData` | WallboardFullData | No | Full wallboard data including preview |

#### Example JSON
```json
{
  "stepId": "step-preview-001",
  "stepTime": 30,
  "wallboardName": "Agent Performance",
  "wallboardDescription": "Real-time agent metrics and KPIs",
  "wallboardFulData": {
    "imageBase64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
  }
}
```

---

### WallboardFullData

Full wallboard data with preview image.

#### Purpose
Contains complete wallboard data plus a base64-encoded preview image for display in selection interfaces.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `imageBase64` | string | No | Base64 encoded preview image of the wallboard |

#### Example JSON
```json
{
  "imageBase64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```

---

### ScreenOption

Screen/wallboard option for step configuration dropdowns.

#### Purpose
Represents a selectable wallboard option when configuring steps in a wallboard group.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the option (wallboard ID) |
| `name` | string | Yes | Display name of the option (wallboard name) |

#### Example JSON
```json
{
  "id": "wb-550e8400-e29b-41d4-a716-446655440000",
  "name": "Sales Team Dashboard"
}
```

---

## Filtering and Sorting Models

### FilterOptions

Sorting and filtering options for wallboard list views.

#### Purpose
Controls how the wallboard list is sorted in the management interface.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sortBy` | string | Yes | Field to sort by (NAME, AUTHOR, DATE) |
| `isDescendent` | boolean | Yes | Sort direction - true for descending, false for ascending |

#### Validation Rules
- `sortBy` must be one of: "NAME", "AUTHOR", "DATE"

#### Example JSON
```json
{
  "sortBy": "DATE",
  "isDescendent": true
}
```

#### Use Cases
- **Sort by name A-Z**: `{ "sortBy": "NAME", "isDescendent": false }`
- **Sort by newest first**: `{ "sortBy": "DATE", "isDescendent": true }`
- **Sort by author A-Z**: `{ "sortBy": "AUTHOR", "isDescendent": false }`

---

## Visualization Models

### SVGData

SVG line configuration for wallboard group visualization.

#### Purpose
Defines SVG paths and arrows used to visualize the flow between steps in a wallboard group.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `svgSize` | object | Yes | SVG dimensions |
| `svgSize.x` | number | Yes | SVG width in pixels |
| `svgSize.y` | number | Yes | SVG height in pixels |
| `points` | string[] | Yes | Array of SVG path points |
| `arrowTranslate` | object | Yes | Arrow transformation settings |
| `arrowTranslate.x` | number | Yes | Arrow X translation |
| `arrowTranslate.y` | number | Yes | Arrow Y translation |
| `arrowTranslate.rotate` | number | Yes | Arrow rotation angle in degrees |

#### Example JSON
```json
{
  "svgSize": {
    "x": 800,
    "y": 200
  },
  "points": ["M 0 100", "L 400 100", "L 400 50", "L 800 50"],
  "arrowTranslate": {
    "x": 790,
    "y": 45,
    "rotate": 0
  }
}
```

---

### SvgLineData

Simple SVG line data for wallboard group visualization.

#### Purpose
Basic SVG path data for drawing connection lines between wallboard group steps.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `points` | array | Yes | Array of points for SVG path |

#### Example JSON
```json
{
  "points": [
    { "x": 0, "y": 50 },
    { "x": 100, "y": 50 },
    { "x": 100, "y": 100 },
    { "x": 200, "y": 100 }
  ]
}
```

---

### XarrowCoordinate

Coordinate configuration for Xarrow connector library.

#### Purpose
Defines connection lines between elements using the Xarrow library for visual flow representation.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | string | Yes | Starting element ID (DOM element reference) |
| `end` | string | Yes | Ending element ID (DOM element reference) |
| `endAnchor` | string | Yes | Anchor position for end element (top, bottom, left, right, middle) |

#### Validation Rules
- `start` and `end` must be valid DOM element IDs
- `endAnchor` must be a valid anchor position

#### Example JSON
```json
{
  "start": "step-card-001",
  "end": "step-card-002",
  "endAnchor": "left"
}
```

---

## Landing and Navigation Models

### LandingCategory

Sidebar navigation category for the landing page.

#### Purpose
Defines navigation categories and filter options in the wallboard management sidebar.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `NAME` | string | Yes | Category group name |
| `ELEMENTS` | string[] | Yes | Array of category filter options |

#### Example JSON
```json
{
  "NAME": "Filter by Type",
  "ELEMENTS": ["All Wallboards", "My Wallboards", "Shared with Me"]
}
```

---

## Complete Configuration Example

Here's a complete example showing a wallboard group with multiple wallboards:

```json
{
  "wallboardGroup": {
    "id": "wbg-complete-example",
    "name": "Call Center Daily Rotation",
    "createdByUserId": "user-admin-001",
    "isNewWallboardGroup": false,
    "timeInterval": 60,
    "steps": [
      {
        "stepId": "step-morning",
        "wallboardId": "wb-agent-performance",
        "time": 90
      },
      {
        "stepId": "step-queues",
        "wallboardId": "wb-queue-status",
        "time": 60
      },
      {
        "stepId": "step-kpis",
        "wallboardId": "wb-daily-kpis",
        "time": 45
      }
    ],
    "settings": {
      "link": {
        "isReadOnlyEnabled": true
      }
    }
  },
  "wallboards": [
    {
      "id": "wb-agent-performance",
      "name": "Agent Performance",
      "description": "Real-time agent metrics",
      "createdBy": "Admin User",
      "createdByUserId": "user-admin-001",
      "createdOn": 1699876543210,
      "widgets": [
        {
          "id": "widget-agent-list",
          "size": {
            "id": "widget-agent-list",
            "width": 800,
            "widthProcent": 100,
            "height": 600,
            "heightProcent": 100,
            "startX": 0,
            "startXProcent": 0,
            "endX": 800,
            "endXProcent": 100,
            "startY": 0,
            "startYProcent": 0,
            "endY": 600,
            "endYProcent": 100
          }
        }
      ],
      "settings": {
        "display": {
          "shrinkHeight": true,
          "shrinkWidth": true
        },
        "link": {
          "isReadOnlyEnabled": false
        }
      }
    }
  ]
}
```

---

## Related Documentation

- [Widget Models](./widget-models.md) - Detailed widget configuration models
- [Agent Models](./agent-models.md) - Agent data models used in widgets
- [Auth Models](./auth-models.md) - Authentication and user models
- [UI Models](./ui-models.md) - UI component prop models