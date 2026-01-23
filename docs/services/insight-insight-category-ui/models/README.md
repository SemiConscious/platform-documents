# Data Models Overview

> **Service:** insight-insight-category-ui
> **Total Models:** 82

## Overview

The insight-insight-category-ui application uses a comprehensive set of TypeScript interfaces and types to manage categories, prompts, templates, users, and dictionaries. The data architecture follows a Redux-based state management pattern with clear separation between API response types, normalized application types, and form data types.

## Data Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Redux Store                                     │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│   category   │    prompt    │   template   │     user     │       ui       │
│    slice     │    slice     │    slice     │    slice     │     slice      │
├──────────────┴──────────────┴──────────────┴──────────────┴────────────────┤
│                           Feature Slices                                     │
├───────────────────────┬───────────────────────┬────────────────────────────┤
│    createCategory     │     createPrompt      │      createDictionary      │
└───────────────────────┴───────────────────────┴────────────────────────────┘
```

## Model Categories

### 1. Category Models
**File:** [models/category-models.md](models/category-models.md)

Models for managing conversation analysis categories that define rules for detecting specific words, phrases, or patterns in call transcripts.

| Model | Purpose |
|-------|---------|
| `Category` | Full category entity with all properties |
| `CategoryFromApi` | Raw API response format |
| `CategoryMinType` | Lightweight list display format |
| `CategoryQueryLogic` | Nested query definition structure |
| `CategoryQueryTerm` | Individual search term configuration |
| `CreateCategoryBody` | API request for category creation |
| `EditCategoryBody` | API request for category updates |
| `CategorySliceState` | Redux slice state shape |

---

### 2. Template Models
**File:** [models/template-models.md](models/template-models.md)

Models for pre-configured category templates that users can use as starting points.

| Model | Purpose |
|-------|---------|
| `Template` | Full template entity |
| `TemplateFromApi` | Raw API response format |
| `TemplateSliceState` | Redux slice state shape |

---

### 3. User Models
**File:** [models/user-models.md](models/user-models.md)

Models for user management from multiple sources (Salesforce and Sapien systems).

| Model | Purpose |
|-------|---------|
| `UserFromSalesforce` | Normalized Salesforce user data |
| `UserFromSalesforceRequest` | Raw Salesforce API response |
| `UserFromSapien` | Sapien system user data |
| `AvailabilityProfile` | User availability configuration |
| `AvailabilityState` | Current user availability status |
| `UserSliceState` | Redux slice state shape |

---

### 4. Prompt Models
**File:** [models/prompt-models.md](models/prompt-models.md)

Models for AI prompt configuration used in conversation analysis.

| Model | Purpose |
|-------|---------|
| `Prompt` | Full prompt entity |
| `PromptFromApi` | Raw API response format |
| `PromptMinType` | Lightweight list display format |
| `PromptRatingType` | Rating-type prompt configuration |
| `CreatePromptBody` | API request for prompt creation |
| `EditPromptBody` | API request for prompt updates |
| `PromptSliceState` | Redux slice state shape |

---

## Enumeration Types

The application uses several enumerations to enforce consistent values across the system:

### Language Support
```typescript
enum Language {
  CHINESE, DANISH, DUTCH, ENGLISH, FRENCH, GERMAN,
  HINDI, ITALIAN, JAPANESE, KOREAN, NORWEGIAN,
  PORTUGUESE, RUSSIAN, SPANISH, SWEDISH
}
```

### Category Configuration Enums
| Enum | Values | Purpose |
|------|--------|---------|
| `ToWhomDoesItApply` | SPEAKER, AGENT, CUSTOMER | Speaker channel targeting |
| `WhereToHappen` | ALL, TURN | Scope of category matching |
| `WhenShouldHappen` | ANYWHERE, BEGINNING, END | Timing conditions |
| `CategoryCreateType` | ALERT, CHECKPOINT, CONCEPT | Category type classification |
| `CategoryCreateTrigger` | EXPECTED, UNEXPECTED, INFO | Trigger behavior |
| `CategoryQueryOperator` | AND, OR | Logical operators for queries |

### Prompt Configuration Enums
| Enum | Values | Purpose |
|------|--------|---------|
| `PromptKind` | RATING, FREE_TEXT | Prompt response type |
| `PromptFocus` | HUMAN, AI_AGENT, HUMAN_AND_AI_AGENT | Target focus area |

### UI/Modal Enums
| Enum | Values | Purpose |
|------|--------|---------|
| `OpenMode` | EDIT, CLONE, VIEW, CREATE, TEMPLATES_LIST, CREATE_FROM_TEMPLATE, HISTORY, EXPAND | Modal operation modes |
| `FetchStatus` | (varies) | API request status tracking |

---

## State Management Models

### Root State Schema
```typescript
interface StateSchema {
  ui: UiSliceState;
  category: CategorySliceState;
  user: UserSliceState;
  template: TemplateSliceState;
  prompt: PromptSliceState;
  createCategory: CreateEditCategorySliceState;
  createPrompt: CreateEditPromptSliceState;
  createDictionary: CreateDictionarySliceState;
}
```

### Thunk Configuration
| Type | Purpose |
|------|---------|
| `ThunkExtraArg` | API instances injected into thunks |
| `ThunkValue<T>` | Wrapper for thunk payloads with notifications |
| `ThunkConfig<T>` | Full thunk configuration type |

---

## Form Data Patterns

The application follows a consistent pattern for form data management:

### Base Form Type
Simple key-value interface for form fields.

### Full Form Type
Wraps each field with validation metadata:
```typescript
{
  value: T;           // Actual field value
  messages: InputMessageType[];  // Validation messages
  isRequired: boolean;           // Required field flag
}
```

### Form Data Types
| Entity | Base Type | Full Type |
|--------|-----------|-----------|
| Category | `CategoryFormDataType` | `CategoryFormDataFullType` |
| Prompt | `PromptFormDataType` | `PromptFormDataFullType` |
| Dictionary | `DictionaryFormDataType` | `DictionaryFormDataFullType` |

---

## API Integration Patterns

### Response Transformation
API responses are normalized from `*FromApi` types to application types:

```
CategoryFromApi → Category
PromptFromApi → Prompt
TemplateFromApi → Template
UserFromSalesforceRequest → UserFromSalesforce
```

### Request Bodies
Dedicated types for API mutations:
- `CreateCategoryBody` / `EditCategoryBody`
- `CreatePromptBody` / `EditPromptBody`

---

## Configuration Models

### InsConfig
Global application configuration including:
- API endpoints (Sapien, Category, Prompt)
- License configuration
- Feature flags (hasFocusField)

---

## Model Relationships

```
┌─────────────┐         ┌─────────────┐
│  Category   │◄────────│  Template   │
│             │ created │             │
│             │  from   │             │
└──────┬──────┘         └─────────────┘
       │
       │ applies to
       ▼
┌─────────────┐
│    User     │
│  (groups)   │
└─────────────┘

┌─────────────┐
│   Prompt    │─────────► AI Analysis
│             │
└─────────────┘

┌─────────────┐
│ Dictionary  │─────────► Term Weighting
│             │
└─────────────┘
```

---

## Quick Reference

| Model Group | Count | Primary Use |
|-------------|-------|-------------|
| Category Models | 12 | Conversation analysis rules |
| Template Models | 3 | Reusable category templates |
| User Models | 8 | User management & auth |
| Prompt Models | 14 | AI prompt configuration |
| State Models | 10 | Redux state management |
| Form Models | 9 | Form validation & state |
| Enum Types | 12 | Consistent value constraints |
| Config/Utility | 14 | App configuration & helpers |

---

## Detailed Documentation

For complete field-level documentation, validation rules, and examples, see:

- **[Category Models](models/category-models.md)** - Category, query logic, and template models
- **[Template Models](models/template-models.md)** - Template entity and API models
- **[User Models](models/user-models.md)** - User entities from Salesforce and Sapien
- **[Prompt Models](models/prompt-models.md)** - AI prompt configuration models