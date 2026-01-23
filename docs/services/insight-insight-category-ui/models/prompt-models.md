# Prompt Data Models

This document covers all TypeScript interfaces and types related to prompt management in the insight-insight-category-ui service. Prompts are AI-driven configurations used for analyzing conversations and generating insights.

## Overview

The prompt system supports two main types of prompts:
- **Rating Prompts**: Generate numerical ratings with optional explanations
- **Free Text Prompts**: Generate open-ended text responses

Prompts can be focused on different conversation participants (human agents, AI agents, or both) and are managed through a complete CRUD lifecycle.

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PROMPT SYSTEM                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐         ┌────────────────────┐                │
│  │  PromptSliceState │────────▶│   PromptMinType[]  │                │
│  │  (Redux State)    │         │   (List View)      │                │
│  └────────┬─────────┘         └────────────────────┘                │
│           │                                                          │
│           │ selectedPrompt                                          │
│           ▼                                                          │
│  ┌──────────────────┐         ┌────────────────────┐                │
│  │     Prompt       │◀────────│   PromptFromApi    │                │
│  │  (Full Entity)   │  maps   │   (API Response)   │                │
│  └────────┬─────────┘         └────────────────────┘                │
│           │                                                          │
│           │ contains                                                 │
│           ▼                                                          │
│  ┌──────────────────┐         ┌────────────────────┐                │
│  │ PromptRatingType │    OR   │PromptFreeTextType  │                │
│  │ (Type-specific)  │         │ (Future expansion) │                │
│  └──────────────────┘         └────────────────────┘                │
│                                                                      │
│  ┌──────────────────┐         ┌────────────────────┐                │
│  │ CreatePromptBody │────────▶│      API           │                │
│  │ (Create Request) │         │                    │                │
│  └──────────────────┘         └────────────────────┘                │
│                                                                      │
│  ┌──────────────────┐         ┌────────────────────┐                │
│  │  EditPromptBody  │────────▶│      API           │                │
│  │ (Update Request) │         │                    │                │
│  └──────────────────┘         └────────────────────┘                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Enums and Constants

### PromptKind

Discriminator enum for prompt types.

| Value | Description |
|-------|-------------|
| `RATING` | Rating type prompt that generates numerical scores |
| `FREE_TEXT` | Free text prompt that generates open-ended responses |

```json
{
  "RATING": "RATING",
  "FREE_TEXT": "FREE_TEXT"
}
```

### PromptFocus

Enum defining which conversation participants the prompt analyzes.

| Value | Description |
|-------|-------------|
| `HUMAN` | Focus on human agent interactions only |
| `AI_AGENT` | Focus on AI agent interactions only |
| `HUMAN_AND_AI_AGENT` | Focus on both human and AI agent interactions |

### PromptErrorModalType

Enum for error modal types displayed in the prompt UI.

| Value | Description |
|-------|-------------|
| `SALESFORCE_ERROR` | Salesforce-related error |
| `METADATA_ERROR` | Metadata configuration error |
| `GENERAL_ERROR` | General error type |

### PromptsLimit

Constants for prompt limitations.

| Constant | Value | Description |
|----------|-------|-------------|
| `PROMPTS_LIMIT` | number | Maximum number of prompts allowed per organization |

---

## Core Entity Models

### Prompt

Full prompt model with all details for display and editing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique prompt identifier |
| `name` | `string` | Yes | Prompt name |
| `description` | `string` | Yes | Prompt description |
| `createdBy` | `number` | Yes | ID of user who created the prompt |
| `isActive` | `boolean` | Yes | Whether prompt is currently active |
| `createdOn` | `string` | Yes | ISO timestamp of creation |
| `modifiedAt` | `number` | Yes | Unix timestamp of last modification |
| `token` | `number` | Yes | Token count for the prompt |
| `focus` | `PromptFocus` | Yes | Focus type (HUMAN, AI_AGENT, HUMAN_AND_AI_AGENT) |
| `type` | `PromptKind.RATING` | Yes | Prompt type discriminator |
| `promptDetails` | `string` | Yes | The actual prompt content/instructions |
| `isIncludeExplanationChecked` | `boolean` | Yes | Whether to include explanation with rating |

**Validation Rules:**
- `name` must be non-empty and unique within the organization
- `promptDetails` must be non-empty
- `token` is calculated based on prompt content length
- `focus` field may be conditionally required based on `InsConfig.hasFocusField`

**Example:**
```json
{
  "id": "prompt_abc123",
  "name": "Customer Satisfaction Analysis",
  "description": "Analyzes customer sentiment and satisfaction throughout the conversation",
  "createdBy": 12345,
  "isActive": true,
  "createdOn": "2024-01-15T10:30:00Z",
  "modifiedAt": 1705312200000,
  "token": 150,
  "focus": "HUMAN_AND_AI_AGENT",
  "type": "RATING",
  "promptDetails": "Rate the customer's satisfaction level from 1-10 based on their tone, word choice, and expressed sentiment throughout the conversation.",
  "isIncludeExplanationChecked": true
}
```

**Relationships:**
- References `UserFromSalesforce` via `createdBy` field
- Stored in `PromptSliceState.selectedPrompt`

---

### PromptFromApi

Prompt model as returned directly from the API before transformation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique prompt identifier |
| `name` | `string` | Yes | Prompt name |
| `description` | `string` | Yes | Prompt description |
| `enabled` | `boolean` | Yes | Whether prompt is enabled (API terminology) |
| `createdBy` | `number` | Yes | ID of user who created the prompt |
| `createdOn` | `string` | Yes | ISO timestamp of creation |
| `modifiedOn` | `number` | Yes | Unix timestamp of last modification |
| `token` | `number` | Yes | Token count for the prompt |
| `focus` | `PromptFocus` | Yes | Focus type for the prompt |
| `type` | `PromptKind.RATING` | Yes | Prompt type discriminator |
| `prompt` | `string` | Yes | Prompt content (maps to `promptDetails`) |
| `reasoning` | `boolean` | Yes | Whether reasoning is enabled (maps to `isIncludeExplanationChecked`) |

**Transformation Notes:**
- `enabled` → `isActive`
- `modifiedOn` → `modifiedAt`
- `prompt` → `promptDetails`
- `reasoning` → `isIncludeExplanationChecked`

**Example:**
```json
{
  "id": "prompt_abc123",
  "name": "Customer Satisfaction Analysis",
  "description": "Analyzes customer sentiment and satisfaction",
  "enabled": true,
  "createdBy": 12345,
  "createdOn": "2024-01-15T10:30:00Z",
  "modifiedOn": 1705312200000,
  "token": 150,
  "focus": "HUMAN_AND_AI_AGENT",
  "type": "RATING",
  "prompt": "Rate the customer's satisfaction level from 1-10...",
  "reasoning": true
}
```

---

### PromptMinType

Minimal prompt model used for list views and selection interfaces.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique prompt identifier |
| `name` | `string` | Yes | Prompt name |
| `description` | `string` | Yes | Prompt description |
| `token` | `number` | Yes | Token count for the prompt |
| `isActive` | `boolean` | Yes | Whether prompt is active |
| `createdBy` | `number` | Yes | ID of user who created the prompt |
| `createdOn` | `string` | Yes | ISO timestamp of creation |
| `focus` | `PromptFocus` | Yes | Focus type for the prompt |

**Use Cases:**
- Displaying prompts in table/list views
- Prompt selection dropdowns
- Quick reference without loading full prompt details

**Example:**
```json
{
  "id": "prompt_abc123",
  "name": "Customer Satisfaction Analysis",
  "description": "Analyzes customer sentiment and satisfaction",
  "token": 150,
  "isActive": true,
  "createdBy": 12345,
  "createdOn": "2024-01-15T10:30:00Z",
  "focus": "HUMAN_AND_AI_AGENT"
}
```

---

### PromptMinTypeFromApi

Minimal prompt data as received directly from the API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Unique prompt identifier |
| `name` | `string` | Yes | Prompt name |
| `description` | `string` | Yes | Prompt description |
| `token` | `number` | Yes | Token count for the prompt |
| `enabled` | `boolean` | Yes | Whether prompt is enabled |
| `createdOn` | `string` | Yes | ISO timestamp of creation |
| `createdBy` | `number` | Yes | ID of user who created the prompt |
| `focus` | `PromptFocus` | Yes | Focus type for the prompt |

**Transformation:**
- `enabled` → `isActive`

---

## Type-Specific Models

### PromptRatingType

Configuration specific to rating-type prompts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `PromptKind.RATING` | Yes | Type discriminator, always "RATING" |
| `promptDetails` | `string` | Yes | Prompt content/instructions |
| `isIncludeExplanationChecked` | `boolean` | Yes | Whether to include explanation with rating |

**Example:**
```json
{
  "type": "RATING",
  "promptDetails": "Rate the agent's professionalism from 1-10 based on their language, tone, and adherence to protocol.",
  "isIncludeExplanationChecked": true
}
```

---

### PromptRatingTypeFromApi

Rating type configuration as received from API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `PromptKind.RATING` | Yes | Type discriminator, always "RATING" |
| `prompt` | `string` | Yes | Prompt text content |
| `reasoning` | `boolean` | Yes | Whether reasoning/explanation is enabled |

---

## Request Body Models

### CreatePromptBody

Request body for creating a new prompt via API.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Prompt name (must be unique) |
| `description` | `string` | Yes | Prompt description |
| `prompt` | `string` | Yes | Prompt content/instructions |
| `enabled` | `boolean` | Yes | Whether prompt should be active |
| `focus` | `PromptFocus` | Conditional | Focus type (required if `hasFocusField` is enabled) |
| `type` | `PromptKind` | Yes | Prompt type (RATING or FREE_TEXT) |
| `reasoning` | `boolean` | Conditional | Include explanation (only for RATING type) |

**Validation Rules:**
- `name` must be unique across all prompts
- `prompt` must be non-empty
- `focus` is only included when `InsConfig.hasFocusField` is truthy
- `reasoning` is only applicable when `type` is `RATING`

**Example (Rating Type):**
```json
{
  "name": "Agent Professionalism Score",
  "description": "Evaluates agent professionalism during customer interactions",
  "prompt": "Analyze the agent's communication and rate their professionalism from 1-10. Consider factors like: greeting, language clarity, empathy, and closure.",
  "enabled": true,
  "focus": "HUMAN",
  "type": "RATING",
  "reasoning": true
}
```

**Example (Free Text Type):**
```json
{
  "name": "Conversation Summary",
  "description": "Generates a summary of the conversation",
  "prompt": "Provide a concise summary of the main topics discussed and any action items identified.",
  "enabled": true,
  "focus": "HUMAN_AND_AI_AGENT",
  "type": "FREE_TEXT"
}
```

---

### EditPromptBody

Request body for updating an existing prompt.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | Yes | Prompt ID to edit |
| `name` | `string` | Yes | Updated prompt name |
| `description` | `string` | Yes | Updated prompt description |
| `prompt` | `string` | Yes | Updated prompt content |
| `enabled` | `boolean` | Yes | Updated active status |
| `focus` | `PromptFocus` | Conditional | Updated focus type |
| `type` | `PromptKind` | Yes | Prompt type (RATING or FREE_TEXT) |
| `reasoning` | `boolean` | Conditional | Include explanation (only for RATING type) |

**Example:**
```json
{
  "id": "prompt_abc123",
  "name": "Agent Professionalism Score v2",
  "description": "Updated evaluation criteria for agent professionalism",
  "prompt": "Analyze the agent's communication and rate their professionalism from 1-10. Consider: greeting quality, language clarity, emotional intelligence, problem resolution, and professional closure.",
  "enabled": true,
  "focus": "HUMAN",
  "type": "RATING",
  "reasoning": true
}
```

---

### PromptRatingTypeCreateBody

Discriminated type for creating rating prompts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `PromptKind.RATING` | Yes | Type discriminator |
| `reasoning` | `boolean` | Yes | Whether reasoning is enabled |

---

### PromptFreeTextTypeCreateBody

Discriminated type for creating free text prompts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `PromptKind.FREE_TEXT` | Yes | Type discriminator |

---

### EditIsPromptActiveThunk

Payload for Redux thunk to toggle prompt active status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `promptId` | `string` | Yes | ID of prompt to update |
| `newActiveStatus` | `boolean` | Yes | New active status value |

**Example:**
```json
{
  "promptId": "prompt_abc123",
  "newActiveStatus": false
}
```

---

## State Management Models

### PromptSliceState

Redux slice state for prompt entity management.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `allPrompts` | `PromptMinType[]` | Yes | Array of all prompts in minimal format |
| `selectedPrompt` | `Prompt \| null` | Yes | Currently selected prompt or null |
| `toolbarSearchByValue` | `string` | Yes | Search filter value for toolbar |
| `errorModalType` | `PromptErrorModalType \| null` | Yes | Type of error modal to display |

**Initial State:**
```json
{
  "allPrompts": [],
  "selectedPrompt": null,
  "toolbarSearchByValue": "",
  "errorModalType": null
}
```

**Use Cases:**
- Managing prompt list in the UI
- Tracking selected prompt for detail view/editing
- Filtering prompts via search
- Displaying error modals

---

### CreateEditPromptSliceState

Redux slice state for prompt creation/editing form.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `promptFormData` | `PromptFormDataFullType` | Yes | Form data with validation metadata |

---

### PromptFormDataType

Base form data structure for prompt creation/editing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Prompt name |
| `description` | `string` | Yes | Prompt description |
| `promptDetails` | `string` | Yes | Detailed prompt content |
| `promptType` | `PromptKind` | Yes | Type of prompt |
| `isIncludeExplanationChecked` | `boolean` | Yes | Whether to include explanation |
| `isActive` | `boolean` | Yes | Whether the prompt is active |
| `isSalesforceConsentChecked` | `boolean` | Yes | Salesforce consent flag |
| `focus` | `PromptFocus` | Yes | Focus area for the prompt |

---

### PromptFormDataFullType

Extended form data with validation messages and required flags.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `{ value: string, messages: InputMessageType[], isRequired: boolean }` | Yes | Name field with validation |
| `description` | `{ value: string, messages: InputMessageType[], isRequired: boolean }` | Yes | Description field with validation |
| `promptDetails` | `{ value: string, messages: InputMessageType[], isRequired: boolean }` | Yes | Prompt details with validation |
| `promptType` | `{ value: PromptKind, messages: InputMessageType[], isRequired: boolean }` | Yes | Type field with validation |
| `isIncludeExplanationChecked` | `{ value: boolean, messages: InputMessageType[], isRequired: boolean }` | Yes | Explanation checkbox with validation |
| `isActive` | `{ value: boolean, messages: InputMessageType[], isRequired: boolean }` | Yes | Active status with validation |
| `isSalesforceConsentChecked` | `{ value: boolean, messages: InputMessageType[], isRequired: boolean }` | Yes | Salesforce consent with validation |
| `focus` | `{ value: string, messages: InputMessageType[], isRequired: boolean }` | Yes | Focus field with validation |

**Example:**
```json
{
  "name": {
    "value": "Customer Satisfaction Analysis",
    "messages": [],
    "isRequired": true
  },
  "description": {
    "value": "Analyzes customer sentiment",
    "messages": [],
    "isRequired": true
  },
  "promptDetails": {
    "value": "Rate the customer's satisfaction from 1-10...",
    "messages": [],
    "isRequired": true
  },
  "promptType": {
    "value": "RATING",
    "messages": [],
    "isRequired": true
  },
  "isIncludeExplanationChecked": {
    "value": true,
    "messages": [],
    "isRequired": false
  },
  "isActive": {
    "value": true,
    "messages": [],
    "isRequired": false
  },
  "isSalesforceConsentChecked": {
    "value": true,
    "messages": [],
    "isRequired": true
  },
  "focus": {
    "value": "HUMAN_AND_AI_AGENT",
    "messages": [],
    "isRequired": true
  }
}
```

---

## Error Handling Models

### PromptSalesforceError

Error structure for Salesforce prompt operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | `number` | Yes | Error code |
| `message` | `string` | Yes | Error message |
| `isMetadataError` | `boolean` | Yes | Whether this is a metadata error |
| `isSalesforceException` | `boolean` | Yes | Whether this is a Salesforce exception |

**Example:**
```json
{
  "code": 403,
  "message": "Insufficient permissions to create prompt",
  "isMetadataError": false,
  "isSalesforceException": true
}
```

---

## UI Component Props

### CreatePromptModalProps

Props for the create/edit prompt modal component.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string \| null` | Yes | Prompt ID for editing, null for creating |
| `mode` | `OpenMode` | Yes | Modal open mode (create/edit/clone/view) |

**Example Usage:**
```typescript
// Creating a new prompt
<CreatePromptModal id={null} mode={OpenMode.CREATE} />

// Editing an existing prompt
<CreatePromptModal id="prompt_abc123" mode={OpenMode.EDIT} />

// Cloning a prompt
<CreatePromptModal id="prompt_abc123" mode={OpenMode.CLONE} />
```

---

## Common Use Cases and Patterns

### Creating a New Prompt

1. Initialize form with default `PromptFormDataFullType`
2. User fills in form fields
3. Validate all required fields
4. Transform `PromptFormDataFullType` to `CreatePromptBody`
5. Submit to API
6. Transform `PromptFromApi` response to `Prompt`
7. Update `PromptSliceState.allPrompts`

### Loading Prompt List

1. Fetch prompts from API (returns `PromptMinTypeFromApi[]`)
2. Transform to `PromptMinType[]`
3. Store in `PromptSliceState.allPrompts`
4. Display in table using `PromptMinType` fields

### Editing a Prompt

1. Load full prompt using ID (returns `PromptFromApi`)
2. Transform to `Prompt`
3. Populate `PromptFormDataFullType` from `Prompt`
4. User modifies form
5. Validate changes
6. Transform to `EditPromptBody`
7. Submit update to API

### Toggling Prompt Status

1. Dispatch `EditIsPromptActiveThunk` with `promptId` and `newActiveStatus`
2. API updates prompt
3. Update `PromptSliceState.allPrompts` with new status
4. If `selectedPrompt` matches, update `isActive`