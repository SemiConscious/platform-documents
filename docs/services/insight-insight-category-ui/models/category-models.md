# Category Data Models

This document covers the core category-related TypeScript interfaces used throughout the insight-insight-category-ui service. These models define the structure of categories, their query logic, and the state management patterns for category operations.

## Overview

Categories are the fundamental building blocks for analyzing conversation data. They define patterns of words, phrases, and conditions that trigger alerts, checkpoints, or concepts during call analysis. The category system supports complex boolean logic, temporal constraints, and speaker-specific targeting.

## Entity Relationship Diagram

```
┌─────────────────────┐     ┌──────────────────────┐
│  CategorySliceState │────▶│    CategoryMinType   │
│                     │     └──────────────────────┘
│  - allCategories[]  │              ▲
│  - selectedCategory │              │ minimal view
│  - toolbarSearch    │              │
└─────────────────────┘     ┌────────┴─────────────┐
         │                  │    CategoryMinType   │
         ▼                  │      FromApi         │
┌─────────────────────┐     └──────────────────────┘
│      Category       │
│                     │◀────transforms────┐
│  - id               │                   │
│  - name             │     ┌─────────────┴────────┐
│  - language         │     │   CategoryFromApi    │
│  - description      │     │                      │
│  - wordsOrPhrases   │     │   - categoryKey      │
│  - whoNeedsSay      │     │   - SK               │
│  - whenShouldHappen │     │   - data.Clause ─────┼──┐
│  - howLongTime      │     │   - definitionString │  │
│  - whereNeedToHappen│     └──────────────────────┘  │
└─────────────────────┘                               │
                                                      ▼
┌─────────────────────┐     ┌──────────────────────────┐
│  CreateCategoryBody │────▶│   CategoryQueryLogic     │
│                     │     │                          │
│  - categoryName     │     │   - Channel              │
│  - definition       │     │   - Operator             │
│  - definitionString │     │   - Scope                │
│  - language         │     │   - Negate               │
│  - description      │     │   - Clause[] (recursive) │
│  - enabled          │     │   - Terms[] ─────────────┼──┐
│  - type             │     │   - PeriodStart          │  │
│  - trigger          │     │   - PeriodEnd            │  │
│  - onlyAppliesTo    │     └──────────────────────────┘  │
└─────────────────────┘                                   │
         ▲                                                ▼
         │              ┌──────────────────────────────────┐
         │              │      CategoryQueryTerm           │
┌────────┴────────────┐ │                                  │
│   EditCategoryBody  │ │   - Term                         │
│                     │ │   - Proximity                    │
│   (extends Create   │ │   - Negate                       │
│    with id field)   │ │   - Fuzzy                        │
└─────────────────────┘ └──────────────────────────────────┘
```

---

## Core Category Models

### Category

The full category model containing all details for a category entity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier for the category |
| name | string | Yes | Human-readable category name |
| language | Language | Yes | Language enum value for the category |
| description | string | Yes | Detailed description of the category purpose |
| wordsOrPhrases | string | Yes | Words or phrases that define the category matching criteria |
| whoNeedsToSayOrNotSay | ToWhomDoesItApply | Yes | Specifies whether Agent, Customer, or either Speaker must say the phrase |
| whenShouldItHappen | WhenShouldHappen | Yes | Timing constraint (beginning, end, or anywhere in call) |
| howLongTime | number | Yes | Time duration in seconds for temporal constraints |
| whereNeedToHappen | WhereToHappen | Yes | Scope defining single turn or across multiple turns |
| createdBy | number | Yes | User ID of the category creator |
| isActive | boolean | Yes | Whether the category is currently active |
| isDeleted | boolean | Yes | Soft delete flag for logical deletion |
| latest | number | Yes | Latest version number for versioning support |
| createdAt | number | Yes | Unix timestamp of creation |
| modifiedAt | number | Yes | Unix timestamp of last modification |

**Validation Rules:**
- `name` must be unique within the tenant
- `howLongTime` must be a positive integer
- `language` must be a valid Language enum value

**Example:**
```json
{
  "id": "cat_abc123def456",
  "name": "Compliance Disclosure",
  "language": "ENGLISH",
  "description": "Detects when agent provides required compliance disclosure at call start",
  "wordsOrPhrases": "\"this call may be recorded\" OR \"call is being monitored\"",
  "whoNeedsToSayOrNotSay": "AGENT",
  "whenShouldItHappen": "BEGINNING",
  "howLongTime": 60,
  "whereNeedToHappen": "TURN",
  "createdBy": 12345,
  "isActive": true,
  "isDeleted": false,
  "latest": 3,
  "createdAt": 1698765432000,
  "modifiedAt": 1699012345000
}
```

---

### CategoryFromApi

Category model as received directly from the API, before transformation to the frontend `Category` model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| categoryKey | string | Yes | Category key identifier (maps to `id`) |
| SK | string | Yes | DynamoDB sort key for data partitioning |
| name | string | Yes | Category name |
| data | { Clause: CategoryQueryLogic } | Yes | Category query definition containing the logic tree |
| language | Language | Yes | Language enum value |
| description | string | Yes | Category description |
| enabled | boolean | Yes | Whether category is enabled (maps to `isActive`) |
| isDeleted | boolean | Yes | Soft delete flag |
| latest | number | Yes | Latest version number |
| createdBy | number | Yes | User ID who created the category |
| definitionString | string | Yes | String representation of the definition for display |
| type | CategoryCreateType | Yes | Category type: Alert, Checkpoint, or Concept |
| trigger | CategoryCreateTrigger | Yes | Trigger type: Expected, Unexpected, or Info |
| createdAt | number | Yes | Creation timestamp |
| modifiedAt | number | Yes | Last modification timestamp |

**Example:**
```json
{
  "categoryKey": "cat_abc123def456",
  "SK": "CATEGORY#cat_abc123def456#v3",
  "name": "Compliance Disclosure",
  "data": {
    "Clause": {
      "Channel": "AGENT",
      "Operator": "OR",
      "Scope": "TURN",
      "Negate": false,
      "Terms": [
        { "Term": "this call may be recorded", "Proximity": 0, "Negate": false, "Fuzzy": 0 },
        { "Term": "call is being monitored", "Proximity": 0, "Negate": false, "Fuzzy": 0 }
      ],
      "PeriodStart": 0,
      "PeriodEnd": 60000
    }
  },
  "language": "ENGLISH",
  "description": "Detects when agent provides required compliance disclosure at call start",
  "enabled": true,
  "isDeleted": false,
  "latest": 3,
  "createdBy": 12345,
  "definitionString": "\"this call may be recorded\" OR \"call is being monitored\"",
  "type": "CHECKPOINT",
  "trigger": "EXPECTED",
  "createdAt": 1698765432000,
  "modifiedAt": 1699012345000
}
```

**Relationships:**
- Transforms to `Category` model for frontend use
- Contains embedded `CategoryQueryLogic` in the `data.Clause` field

---

### CategoryMinType

Minimal category model optimized for list display and selection operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier |
| description | string | Yes | Category description |
| isActive | boolean | Yes | Whether category is active |
| language | Language | Yes | Language enum value |
| name | string | Yes | Category name |
| createdBy | number | Yes | User ID who created the category |

**Example:**
```json
{
  "id": "cat_abc123def456",
  "description": "Detects compliance disclosure statements",
  "isActive": true,
  "language": "ENGLISH",
  "name": "Compliance Disclosure",
  "createdBy": 12345
}
```

**Use Cases:**
- Category list views
- Dropdown selections
- Quick reference without loading full category details

---

### CategoryMinTypeFromApi

Minimal category model as received from the API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| categoryKey | string | Yes | Category key identifier |
| description | string | Yes | Category description |
| enabled | boolean | Yes | Whether category is enabled |
| language | Language | Yes | Language enum value |
| name | string | Yes | Category name |
| createdBy | number | Yes | User ID who created the category |

**Example:**
```json
{
  "categoryKey": "cat_abc123def456",
  "description": "Detects compliance disclosure statements",
  "enabled": true,
  "language": "ENGLISH",
  "name": "Compliance Disclosure",
  "createdBy": 12345
}
```

---

## Query Logic Models

### CategoryQueryLogic

Defines the recursive structure of a category query with nested clauses and boolean logic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Channel | ToWhomDoesItApply | No | Speaker channel: SPEAKER, AGENT, or CUSTOMER |
| Clause | CategoryQueryLogic[] | No | Nested array of query clauses for complex logic |
| Operator | CategoryQueryOperator | No | Boolean operator: 'AND' or 'OR' |
| Scope | WhereToHappen | No | Search scope: ALL (multiple turns) or TURN (single turn) |
| Negate | boolean | No | Whether to negate the entire clause/term |
| Terms | CategoryQueryTerm[] | No | Array of search terms for this clause |
| PeriodStart | number | No | Start of the search period in milliseconds |
| PeriodEnd | number | No | End of the search period in milliseconds |

**Validation Rules:**
- Either `Clause` or `Terms` should be populated, not both
- `Operator` is required when multiple terms or clauses exist
- `PeriodStart` must be less than `PeriodEnd` when both are specified

**Example - Simple Query:**
```json
{
  "Channel": "AGENT",
  "Operator": "OR",
  "Scope": "TURN",
  "Negate": false,
  "Terms": [
    { "Term": "thank you for calling", "Proximity": 0, "Negate": false, "Fuzzy": 0 }
  ],
  "PeriodStart": 0,
  "PeriodEnd": 30000
}
```

**Example - Complex Nested Query:**
```json
{
  "Operator": "AND",
  "Clause": [
    {
      "Channel": "AGENT",
      "Scope": "TURN",
      "Negate": false,
      "Terms": [
        { "Term": "how may I help", "Proximity": 2, "Negate": false, "Fuzzy": 1 }
      ]
    },
    {
      "Channel": "CUSTOMER",
      "Scope": "ALL",
      "Operator": "OR",
      "Negate": false,
      "Terms": [
        { "Term": "billing issue", "Proximity": 0, "Negate": false, "Fuzzy": 0 },
        { "Term": "account problem", "Proximity": 0, "Negate": false, "Fuzzy": 0 }
      ]
    }
  ],
  "PeriodStart": 0,
  "PeriodEnd": 120000
}
```

---

### CategoryQueryTerm

Individual term in a category query with matching options.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Term | string | Yes | The search term or phrase |
| Proximity | number | Yes | Word proximity value (0 = exact phrase) |
| Negate | boolean | Yes | Whether to negate this specific term |
| Fuzzy | number | Yes | Fuzzy matching tolerance (0 = exact match) |

**Validation Rules:**
- `Term` cannot be empty
- `Proximity` must be 0 or greater
- `Fuzzy` typically ranges from 0-2

**Example:**
```json
{
  "Term": "customer satisfaction",
  "Proximity": 3,
  "Negate": false,
  "Fuzzy": 1
}
```

**Use Cases:**
- Exact phrase matching: `Proximity: 0, Fuzzy: 0`
- Flexible word order: `Proximity: 5` (words within 5 positions)
- Spelling tolerance: `Fuzzy: 1` (allows minor variations)
- Exclusion patterns: `Negate: true` (must NOT contain term)

---

### CategoryQueryOperator

Type definition for query operators used in boolean logic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| value | 'OR' \| 'AND' | Yes | Logical operator between terms or clauses |

**Example:**
```json
{
  "value": "AND"
}
```

---

### WordsAndPhrasesConvertOptionsType

Options for converting words and phrases input into query logic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | The raw query string to convert |
| channel | ToWhomDoesItApply | Yes | Target speaker channel |
| scope | WhereToHappen | Yes | Search scope setting |
| periodOptions | WordsAndPhrasesPeriodOptions | Yes | Time period constraints |

**Example:**
```json
{
  "query": "\"thank you\" OR \"thanks for calling\" AND NOT \"please hold\"",
  "channel": "AGENT",
  "scope": "TURN",
  "periodOptions": {
    "PeriodStart": 0,
    "PeriodEnd": 60000
  }
}
```

---

### WordsAndPhrasesPeriodOptions

Period options for words and phrases search constraints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PeriodStart | number | Yes | Start of the search period in milliseconds |
| PeriodEnd | number | No | End of the search period in milliseconds (undefined = end of call) |

**Example:**
```json
{
  "PeriodStart": 0,
  "PeriodEnd": 120000
}
```

---

## API Request/Response Models

### CreateCategoryBody

Request body structure for creating a new category via API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| categoryName | string | Yes | Name of the category |
| definition | { Clause: CategoryQueryLogic } | Yes | Category query definition |
| definitionString | string | Yes | Human-readable string representation |
| language | string | Yes | Language code |
| description | string | Yes | Category description |
| enabled | boolean | Yes | Whether category is enabled on creation |
| type | CategoryCreateType | Yes | Category type: ALERT, CHECKPOINT, or CONCEPT |
| trigger | CategoryCreateTrigger | Yes | Trigger type: EXPECTED, UNEXPECTED, or INFO |
| onlyAppliesTo | { groups: string[], users: string[] } | Yes | Scope restrictions |

**Example:**
```json
{
  "categoryName": "Upsell Opportunity",
  "definition": {
    "Clause": {
      "Channel": "CUSTOMER",
      "Operator": "OR",
      "Scope": "ALL",
      "Negate": false,
      "Terms": [
        { "Term": "upgrade", "Proximity": 0, "Negate": false, "Fuzzy": 0 },
        { "Term": "premium plan", "Proximity": 2, "Negate": false, "Fuzzy": 0 }
      ]
    }
  },
  "definitionString": "\"upgrade\" OR \"premium plan\"",
  "language": "ENGLISH",
  "description": "Identifies customer interest in product upgrades",
  "enabled": true,
  "type": "ALERT",
  "trigger": "INFO",
  "onlyAppliesTo": {
    "groups": ["sales_team", "retention_team"],
    "users": []
  }
}
```

---

### EditCategoryBody

Request body structure for editing an existing category.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Category ID to edit |
| categoryName | string | Yes | Updated category name |
| definition | { Clause: CategoryQueryLogic } | Yes | Updated query definition |
| definitionString | string | Yes | Updated string representation |
| language | string | Yes | Language code |
| description | string | Yes | Updated description |
| enabled | boolean | Yes | Updated enabled status |
| type | CategoryCreateType | Yes | Category type |
| trigger | CategoryCreateTrigger | Yes | Trigger type |
| onlyAppliesTo | { groups: string[], users: string[] } | Yes | Updated scope restrictions |

**Example:**
```json
{
  "id": "cat_abc123def456",
  "categoryName": "Upsell Opportunity - Enhanced",
  "definition": {
    "Clause": {
      "Channel": "CUSTOMER",
      "Operator": "OR",
      "Scope": "ALL",
      "Negate": false,
      "Terms": [
        { "Term": "upgrade", "Proximity": 0, "Negate": false, "Fuzzy": 0 },
        { "Term": "premium plan", "Proximity": 2, "Negate": false, "Fuzzy": 0 },
        { "Term": "better package", "Proximity": 2, "Negate": false, "Fuzzy": 1 }
      ]
    }
  },
  "definitionString": "\"upgrade\" OR \"premium plan\" OR \"better package\"",
  "language": "ENGLISH",
  "description": "Identifies customer interest in product upgrades - enhanced detection",
  "enabled": true,
  "type": "ALERT",
  "trigger": "INFO",
  "onlyAppliesTo": {
    "groups": ["sales_team", "retention_team", "support_team"],
    "users": ["user_789"]
  }
}
```

---

### EditIsActiveCategoryThunk

Payload structure for changing a category's active status via Redux thunk.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| categoryId | string | Yes | Category ID to update |
| newActiveStatus | boolean | Yes | New active status value |

**Example:**
```json
{
  "categoryId": "cat_abc123def456",
  "newActiveStatus": false
}
```

---

## State Management Models

### CategorySliceState

Redux slice state structure for category management.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| allCategories | CategoryMinType[] | Yes | Array of all categories in minimal format |
| selectedCategory | Category \| null | Yes | Currently selected category or null |
| toolbarSearchByValue | string | Yes | Current search filter value for toolbar |

**Initial State:**
```json
{
  "allCategories": [],
  "selectedCategory": null,
  "toolbarSearchByValue": ""
}
```

**Example - Populated State:**
```json
{
  "allCategories": [
    {
      "id": "cat_abc123def456",
      "name": "Compliance Disclosure",
      "description": "Detects compliance statements",
      "isActive": true,
      "language": "ENGLISH",
      "createdBy": 12345
    },
    {
      "id": "cat_def456ghi789",
      "name": "Customer Complaint",
      "description": "Identifies customer complaints",
      "isActive": true,
      "language": "ENGLISH",
      "createdBy": 12346
    }
  ],
  "selectedCategory": {
    "id": "cat_abc123def456",
    "name": "Compliance Disclosure",
    "language": "ENGLISH",
    "description": "Detects compliance statements",
    "wordsOrPhrases": "\"this call may be recorded\"",
    "whoNeedsToSayOrNotSay": "AGENT",
    "whenShouldItHappen": "BEGINNING",
    "howLongTime": 60,
    "whereNeedToHappen": "TURN",
    "createdBy": 12345,
    "isActive": true,
    "isDeleted": false,
    "latest": 1,
    "createdAt": 1698765432000,
    "modifiedAt": 1698765432000
  },
  "toolbarSearchByValue": "compliance"
}
```

---

## Enums

### ToWhomDoesItApply

Enum defining the speaker channel for category matching.

| Value | Description |
|-------|-------------|
| SPEAKER | Matches any speaker (agent or customer) |
| AGENT | Matches only agent speech |
| CUSTOMER | Matches only customer speech |

**Example Usage:**
```typescript
const channel: ToWhomDoesItApply = ToWhomDoesItApply.AGENT;
```

---

### WhereToHappen

Enum defining the scope of where category matching applies.

| Value | Description |
|-------|-------------|
| ALL | Search across multiple speaker turns |
| TURN | Search within a single speaker turn only |

**Example Usage:**
```typescript
const scope: WhereToHappen = WhereToHappen.TURN;
```

---

### WhenShouldHappen

Enum defining when in the call the category should trigger.

| Value | Description |
|-------|-------------|
| ANYWHERE | Category can match anywhere in the call |
| BEGINNING | Category matches only at the call beginning |
| END | Category matches only at the call end |

**Example Usage:**
```typescript
const timing: WhenShouldHappen = WhenShouldHappen.BEGINNING;
```

---

### CategoryCreateType

Enum defining category types.

| Value | Description |
|-------|-------------|
| ALERT | Real-time alert category |
| CHECKPOINT | Compliance checkpoint category |
| CONCEPT | Concept detection category |

**Example Usage:**
```typescript
const type: CategoryCreateType = CategoryCreateType.CHECKPOINT;
```

---

### CategoryCreateTrigger

Enum defining category trigger types.

| Value | Description |
|-------|-------------|
| EXPECTED | Triggers when expected behavior is detected |
| UNEXPECTED | Triggers when unexpected behavior is detected |
| INFO | Informational trigger (no action required) |

**Example Usage:**
```typescript
const trigger: CategoryCreateTrigger = CategoryCreateTrigger.EXPECTED;
```

---

### Language

Enum for supported languages in category configuration.

| Value | Description |
|-------|-------------|
| CHINESE | Chinese language |
| DANISH | Danish language |
| DUTCH | Dutch language |
| ENGLISH | English language |
| FRENCH | French language |
| GERMAN | German language |
| HINDI | Hindi language |
| ITALIAN | Italian language |
| JAPANESE | Japanese language |
| KOREAN | Korean language |
| NORWEGIAN | Norwegian language |
| PORTUGUESE | Portuguese language |
| RUSSIAN | Russian language |
| SPANISH | Spanish language |
| SWEDISH | Swedish language |

**Example Usage:**
```typescript
const lang: Language = Language.ENGLISH;
```

---

## Common Patterns

### Category Creation Flow

1. User fills form data (`CategoryFormDataType`)
2. Form data is validated (`CategoryFormDataFullType`)
3. Valid data is converted to `CreateCategoryBody`
4. API returns `CategoryFromApi`
5. Response transforms to `Category` for state
6. `CategoryMinType` added to `allCategories` list

### Query Logic Building

1. Parse `wordsOrPhrases` string input
2. Apply `WordsAndPhrasesConvertOptionsType` options
3. Generate `CategoryQueryTerm[]` for each term
4. Wrap in `CategoryQueryLogic` with operator and scope
5. Nest clauses for complex boolean logic

### State Selection Pattern

```typescript
// Select all categories
const categories = useSelector(state => state.category.allCategories);

// Select currently selected category
const selected = useSelector(state => state.category.selectedCategory);

// Filter by search
const filtered = categories.filter(cat => 
  cat.name.toLowerCase().includes(state.category.toolbarSearchByValue.toLowerCase())
);
```