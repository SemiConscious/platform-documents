# Template Data Models

This document covers TypeScript interfaces and types related to reusable category templates in the Insight Category UI service. Templates provide pre-configured category definitions that users can quickly apply when creating new categories.

## Overview

Templates serve as blueprints for category creation, storing common patterns of words/phrases, channel configurations, and time period settings. They streamline the category creation workflow by providing tested, reusable configurations.

## Entity Relationship Diagram

```
┌─────────────────────────┐
│    TemplateSliceState   │
│─────────────────────────│
│ allTemplates: Template[]│
└───────────┬─────────────┘
            │ contains
            ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│       Template          │◄────────│    TemplateFromApi      │
│─────────────────────────│ mapped  │─────────────────────────│
│ id                      │  from   │ categoryKey             │
│ name                    │         │ name                    │
│ description             │         │ description             │
│ language                │         │ language                │
│ definitionString        │         │ definitionString        │
│ channel                 │         │ data                    │
│ periodStart             │         └─────────────────────────┘
│ periodEnd               │
└───────────┬─────────────┘
            │ uses
            ▼
┌─────────────────────────┐
│   ToWhomDoesItApply     │
│   (Enum)                │
│─────────────────────────│
│ SPEAKER                 │
│ AGENT                   │
│ CUSTOMER                │
└─────────────────────────┘
```

---

## State Models

### TemplateSliceState

Redux slice state for managing the collection of category templates.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allTemplates` | `Template[]` | Yes | Array containing all available category templates |

**Purpose**: Serves as the root state container for template-related data in the Redux store.

**Validation Rules**:
- `allTemplates` initializes as an empty array
- Templates are loaded asynchronously and populate this array

**Example JSON**:
```json
{
  "allTemplates": [
    {
      "id": "tmpl-greeting-001",
      "name": "Standard Greeting",
      "description": "Detects proper agent greeting at call start",
      "language": "en",
      "definitionString": "hello OR good morning OR good afternoon",
      "channel": "AGENT",
      "periodStart": 0,
      "periodEnd": 30000
    },
    {
      "id": "tmpl-closing-001",
      "name": "Call Closing",
      "description": "Verifies agent properly closes the call",
      "language": "en",
      "definitionString": "thank you for calling OR have a great day",
      "channel": "AGENT",
      "periodStart": -60000,
      "periodEnd": 0
    }
  ]
}
```

**Relationships**:
- Part of `StateSchema` as the `template` slice
- Contains array of `Template` entities

---

## Entity Models

### Template

The normalized template model used throughout the application for displaying and applying category templates.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique identifier for the template |
| `name` | `string` | Yes | Human-readable template name |
| `description` | `string` | Yes | Detailed description of template purpose |
| `language` | `Language` | Yes | Language enum value (e.g., ENGLISH, SPANISH) |
| `definitionString` | `string` | Yes | String representation of the search definition (words/phrases) |
| `channel` | `ToWhomDoesItApply` | Yes | Speaker channel: SPEAKER, AGENT, or CUSTOMER |
| `periodStart` | `number` | Yes | Start of the time period in milliseconds |
| `periodEnd` | `number` | Yes | End of the time period in milliseconds |

**Purpose**: Provides a client-friendly representation of category templates that can be applied during category creation.

**Validation Rules**:
- `id` must be a non-empty string
- `name` must be a non-empty string
- `language` must be a valid `Language` enum value
- `definitionString` should contain valid search syntax
- `channel` must be a valid `ToWhomDoesItApply` enum value
- `periodStart` and `periodEnd` are timestamps in milliseconds (can be negative for relative positioning)

**Example JSON**:
```json
{
  "id": "tmpl-compliance-disclosure",
  "name": "Compliance Disclosure",
  "description": "Ensures agent provides required legal disclosure during the first minute of the call",
  "language": "en",
  "definitionString": "(this call AND recorded) OR (monitoring AND quality)",
  "channel": "AGENT",
  "periodStart": 0,
  "periodEnd": 60000
}
```

**Relationships**:
- Mapped from `TemplateFromApi`
- Stored in `TemplateSliceState.allTemplates`
- Uses `Language` enum for language specification
- Uses `ToWhomDoesItApply` enum for channel specification
- Can be converted to `CategoryFormDataType` when creating a category from template

---

### TemplateFromApi

Template model as received directly from the API, before normalization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categoryKey` | `string` | Yes | Category key identifier (maps to `id` in normalized form) |
| `name` | `string` | Yes | Template name |
| `description` | `string` | Yes | Template description |
| `language` | `Language` | Yes | Language enum value |
| `definitionString` | `string` | Yes | String representation of the search definition |
| `data` | `object` | Yes | Nested object containing channel and period configuration |
| `data.channel` | `ToWhomDoesItApply` | Yes | Speaker channel configuration |
| `data.periodStart` | `number` | Yes | Start of the time period in milliseconds |
| `data.periodEnd` | `number` | No | End of the time period in milliseconds (optional) |

**Purpose**: Represents the raw API response structure for templates before transformation to the client-side model.

**Validation Rules**:
- `categoryKey` is the unique identifier from the backend
- `data` object must contain at least `channel` and `periodStart`
- `data.periodEnd` is optional and may be undefined

**Example JSON**:
```json
{
  "categoryKey": "tmpl-escalation-request",
  "name": "Escalation Request",
  "description": "Detects when customer requests to speak with a supervisor or manager",
  "language": "en",
  "definitionString": "supervisor OR manager OR escalate OR speak to someone else",
  "data": {
    "channel": "CUSTOMER",
    "periodStart": 0,
    "periodEnd": 0
  }
}
```

**Relationships**:
- Received from the Category API
- Transformed to `Template` for client-side use
- Uses `Language` and `ToWhomDoesItApply` enums

---

## Supporting Types

### CreateCategoryFromTemplateProps

Props interface for the component that handles creating a category from a selected template.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `className` | `string` | No | Optional CSS class name for styling |

**Purpose**: Defines the props accepted by the CreateCategoryFromTemplate component.

**Example Usage**:
```tsx
<CreateCategoryFromTemplate className="template-selector" />
```

**Relationships**:
- Used by the CreateCategoryFromTemplate component
- Works with `Template` entities to populate category form data

---

## Data Flow

### Template Loading Flow

```
API Response (TemplateFromApi[])
           │
           ▼
    Transformation
           │
           ▼
  Template[] (normalized)
           │
           ▼
  TemplateSliceState.allTemplates
           │
           ▼
    UI Components
```

### Template to Category Conversion

When a user selects a template to create a category, the template data maps to category form fields:

| Template Field | Category Form Field |
|---------------|---------------------|
| `name` | Used as suggestion for `name` |
| `description` | `description` |
| `language` | `language` |
| `definitionString` | `wordsOrPhrases` |
| `channel` | `toWhomDoesItApply` |
| `periodStart`/`periodEnd` | `whenShouldItHappen` + `howLongTime` |

---

## Common Use Cases

### 1. Loading Templates

```typescript
// Fetch all templates for display
const templates = useSelector((state: StateSchema) => state.template.allTemplates);
```

### 2. Transforming API Response

```typescript
function transformTemplateFromApi(apiTemplate: TemplateFromApi): Template {
  return {
    id: apiTemplate.categoryKey,
    name: apiTemplate.name,
    description: apiTemplate.description,
    language: apiTemplate.language,
    definitionString: apiTemplate.definitionString,
    channel: apiTemplate.data.channel,
    periodStart: apiTemplate.data.periodStart,
    periodEnd: apiTemplate.data.periodEnd ?? 0
  };
}
```

### 3. Applying Template to Category Creation

```typescript
function applyTemplate(template: Template): CategoryFormDataType {
  return {
    name: '',  // User provides new name
    description: template.description,
    language: template.language,
    wordsOrPhrases: template.definitionString,
    toWhomDoesItApply: template.channel,
    whenShouldItHappen: determineWhenFromPeriod(template.periodStart, template.periodEnd),
    howLongTime: calculateDuration(template.periodStart, template.periodEnd),
    whereNeedToHappen: WhereToHappen.ALL,
    users: [],
    groups: []
  };
}
```

### 4. Filtering Templates by Language

```typescript
const englishTemplates = templates.filter(
  (template) => template.language === Language.ENGLISH
);
```

---

## Related Documentation

- [Category Models](./category-models.md) - Category entities that templates help create
- [User Models](./user-models.md) - User context for template operations
- [Overview](./README.md) - Complete data model overview