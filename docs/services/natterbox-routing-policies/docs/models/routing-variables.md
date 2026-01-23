# Routing Variable Models

This document covers the variable types used in routing policy rules within the Natterbox routing system. Variables enable dynamic data collection, validation, and routing decisions based on caller input and AI-processed information.

## Overview

Routing variables are fundamental building blocks for intelligent call routing. They define the structure and constraints for information collected during customer interactions, enabling validation, formatting, and conditional routing based on captured data.

## Variable Type Hierarchy

```
BaseVariable (abstract)
├── StringVariable
├── NumberVariable
├── DateVariable
├── BooleanVariable
├── SelectionVariable
└── MultiSelectionVariable
```

All variable types extend from `BaseVariable` and share common fields (`name`, `description`, `type`) while adding type-specific validation and formatting options.

---

## Core Models

### BaseVariable

The foundation schema for all routing variables. This abstract model defines the common structure that all variable types inherit.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern. Must be a valid identifier for use in routing expressions |
| `description` | string | Yes | Human-readable description of the variable's purpose (minimum 1 character) |
| `type` | enum | Yes | Variable type discriminator from `AI_GET_INFO.TYPE_SELECT` values |

**Validation Rules:**
- `name` must match the system's variable naming pattern (typically alphanumeric with underscores)
- `description` cannot be empty
- `type` must be one of: `STRING`, `NUMBER`, `DATE`, `BOOLEAN`, `SELECTION`, `MULTI_SELECTION`

---

### StringVariable

Captures text input with optional regex pattern validation. Extends `BaseVariable`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern |
| `description` | string | Yes | Variable description (minimum 1 character) |
| `type` | literal | Yes | Must be `"STRING"` |
| `pattern` | string | No | Regular expression pattern for input validation. Must be a valid regex |

**Validation Rules:**
- If `pattern` is provided, it must be a syntactically valid regular expression
- Input values will be validated against the pattern if specified

**Example:**
```json
{
  "name": "customer_email",
  "description": "Customer's email address for follow-up communication",
  "type": "STRING",
  "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
}
```

**Common Use Cases:**
- Email address collection with format validation
- Phone number formatting
- Reference number/ticket ID capture
- Free-text input with character restrictions

---

### NumberVariable

Captures numeric input with optional range constraints. Extends `BaseVariable`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern |
| `description` | string | Yes | Variable description (minimum 1 character) |
| `type` | literal | Yes | Must be `"NUMBER"` |
| `minimum` | number | No | Minimum acceptable value. Must be less than or equal to `maximum` if both specified |
| `maximum` | number | No | Maximum acceptable value |

**Validation Rules:**
- If both `minimum` and `maximum` are provided, `minimum` must be ≤ `maximum`
- Input values must fall within the specified range (inclusive)

**Example:**
```json
{
  "name": "order_quantity",
  "description": "Number of items the customer wishes to order",
  "type": "NUMBER",
  "minimum": 1,
  "maximum": 100
}
```

**Common Use Cases:**
- Quantity selection
- Rating/satisfaction scores
- Account number validation
- Age verification

---

### DateVariable

Captures date input with configurable output formatting. Extends `BaseVariable`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern |
| `description` | string | Yes | Variable description (minimum 1 character) |
| `type` | literal | Yes | Must be `"DATE"` |
| `outputFormat` | string | No | Date output format string (e.g., `YYYY-MM-DD`, `DD/MM/YYYY`) |

**Validation Rules:**
- `outputFormat` should follow standard date formatting conventions
- The AI will interpret natural language dates and convert to the specified format

**Example:**
```json
{
  "name": "appointment_date",
  "description": "Preferred appointment date for the service call",
  "type": "DATE",
  "outputFormat": "YYYY-MM-DD"
}
```

**Common Use Cases:**
- Appointment scheduling
- Birth date collection
- Event date capture
- Delivery date preferences

---

### BooleanVariable

Captures yes/no or true/false input with configurable output formatting. Extends `BaseVariable`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern |
| `description` | string | Yes | Variable description (minimum 1 character) |
| `type` | literal | Yes | Must be `"BOOLEAN"` |
| `outputFormat` | string | No | Boolean output format (e.g., `true/false`, `yes/no`, `1/0`) |

**Validation Rules:**
- The AI interprets various affirmative/negative responses
- Output is formatted according to `outputFormat` specification

**Example:**
```json
{
  "name": "has_existing_account",
  "description": "Whether the caller already has an account with us",
  "type": "BOOLEAN",
  "outputFormat": "yes/no"
}
```

**Common Use Cases:**
- Confirmation prompts
- Eligibility checks
- Preference toggles
- Consent capture

---

### SelectionVariable

Captures single-choice selection from a predefined list. Extends `BaseVariable`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern |
| `description` | string | Yes | Variable description (minimum 1 character) |
| `type` | literal | Yes | Must be `"SELECTION"` |
| `enum` | string | Yes | JSON array as string containing valid selection options |

**Validation Rules:**
- `enum` must be a valid JSON array serialized as a string
- Caller input must match one of the enumerated values
- The AI will interpret natural language and map to the closest valid option

**Example:**
```json
{
  "name": "department",
  "description": "Which department the caller needs to reach",
  "type": "SELECTION",
  "enum": "[\"Sales\", \"Support\", \"Billing\", \"Technical\"]"
}
```

**Common Use Cases:**
- Department selection
- Product category choice
- Service tier selection
- Priority level assignment

---

### MultiSelectionVariable

Captures multiple selections from a predefined list. Extends `BaseVariable`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name matching the `variableNameRegex` pattern |
| `description` | string | Yes | Variable description (minimum 1 character) |
| `type` | literal | Yes | Must be `"MULTI_SELECTION"` |
| `enum` | string | Yes | JSON array as string containing valid selection options |

**Validation Rules:**
- `enum` must be a valid JSON array serialized as a string
- Caller can select one or more options from the list
- All selections must match enumerated values

**Example:**
```json
{
  "name": "issue_categories",
  "description": "Categories of issues the caller is experiencing",
  "type": "MULTI_SELECTION",
  "enum": "[\"Login Problems\", \"Payment Issues\", \"Shipping Delays\", \"Product Defects\", \"Other\"]"
}
```

**Common Use Cases:**
- Multi-symptom issue reporting
- Interest area selection
- Feature preference capture
- Service bundle selection

---

## AI Routing Variable

### AIRoutingVariable

A specialized variable type used specifically within the [AIRouting](./ai-routing.md#airouting) component to define routing destinations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Route name (must start with letter, maximum 257 characters) |
| `description` | string | Yes | Description of when this route should be selected |
| `targetNode` | string | Yes | Target node identifier matching `targetNameRegex` pattern |

**Validation Rules:**
- `name` must begin with a letter
- `name` maximum length is 257 characters
- `targetNode` must reference a valid node in the routing policy

**Example:**
```json
{
  "name": "sales_inquiry",
  "description": "Customer wants to learn about products, pricing, or make a purchase",
  "targetNode": "sales_queue"
}
```

**Relationship to AIRouting:**
- Used exclusively within the `variables` array of `AIRouting` component
- Each variable represents a possible routing outcome
- The AI analyzes caller intent and selects the appropriate route based on descriptions

---

## Variable Collections in Context

### Usage in AIGetInfo

Variables are collected as an array in the [AIGetInfo](./ai-routing.md#aigetinfo) component:

```json
{
  "agentInstanceName": "info_collector_1",
  "goalPrompt": "Collect customer details for account lookup",
  "systemPrompt": "You are a helpful assistant collecting customer information...",
  "userGreetingPrompt": "Hello! I'll help you with your inquiry. First, I need some information.",
  "infoCollectedConfirmPrompt": "Thank you, I have all the information I need.",
  "variables": [
    {
      "name": "customer_name",
      "description": "The customer's full name",
      "type": "STRING"
    },
    {
      "name": "account_number",
      "description": "Customer's 8-digit account number",
      "type": "STRING",
      "pattern": "^[0-9]{8}$"
    },
    {
      "name": "callback_preferred",
      "description": "Whether the customer prefers a callback",
      "type": "BOOLEAN",
      "outputFormat": "yes/no"
    }
  ]
}
```

### Usage in AIRouting

Route variables define possible routing outcomes:

```json
{
  "userGreetingPrompt": "Welcome to Acme Corp. How can I help you today?",
  "goalPrompt": "Determine the best department to handle the caller's request",
  "systemPrompt": "You are a routing assistant...",
  "variables": [
    {
      "name": "new_sales",
      "description": "Caller wants to buy new products or services",
      "targetNode": "sales_team"
    },
    {
      "name": "existing_support",
      "description": "Caller has issues with existing products or services",
      "targetNode": "support_team"
    },
    {
      "name": "billing_inquiry",
      "description": "Caller has questions about invoices or payments",
      "targetNode": "billing_team"
    }
  ]
}
```

---

## Related Documentation

- [AI Routing Components](./ai-routing.md) - Full documentation on AIGetInfo, AIRouting, and other AI components that use these variables
- [Policy Records](./policy-records.md) - How variables integrate with routing policy configurations
- [Models Overview](./README.md) - Complete model reference index