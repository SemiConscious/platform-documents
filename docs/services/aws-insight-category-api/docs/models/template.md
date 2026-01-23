# Template Models

This document covers the CategoryTemplate model and its associated response format used for managing category templates in the aws-insight-category-api.

> **Related Documentation**: For category models and request/response formats, see [Category Models](./category.md). For a complete overview, see the [Models Overview](./README.md).

## Overview

Category templates are pre-defined category configurations stored at the system level (orgId = 'category/0'). They serve as blueprints that organizations can use to create their own categories, ensuring consistency and reducing setup time.

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CategoryTemplate                          │
│  (stored with orgId = 'category/0')                         │
├─────────────────────────────────────────────────────────────┤
│  PK: string (partition key)                                 │
│  SK: string (sort key with version)                         │
│  name, description, language, type, trigger                 │
│  data, definitionString                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ transforms to
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   TemplateListResponse                       │
│  (API response format)                                       │
├─────────────────────────────────────────────────────────────┤
│  categoryKey (extracted from PK)                            │
│  name, description, language                                │
│  data, type, trigger, definitionString                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ used to create
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Category                              │
│  (organization-specific instance)                           │
│  See: category.md                                           │
└─────────────────────────────────────────────────────────────┘
```

## Models

### CategoryTemplate

Category templates are stored in the same DynamoDB table as categories but are distinguished by their special `orgId` value of `'category/0'`. This allows system-wide templates to be managed separately from organization-specific categories.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `PK` | string | Yes | Partition key containing the template identifier. Format: `category/0/{templateKey}` |
| `SK` | string | Yes | Sort key for versioning. Format: `v{version}/{unixTimestamp}` where `v0` represents the latest version |
| `name` | string | Yes | Human-readable template name displayed in the UI |
| `description` | string | Yes | Detailed description of what the template is used for |
| `language` | string | Yes | Language code for the template (e.g., 'en', 'es', 'fr') |
| `data` | any | Yes | Template configuration data object containing the category definition structure |
| `type` | string | Yes | Classification type of the template (e.g., 'sentiment', 'topic', 'intent') |
| `trigger` | string | Yes | Event or condition that triggers category evaluation |
| `definitionString` | string | Yes | Serialized string representation of the template definition |
| `orgId` | string | Yes | Always `'category/0'` for templates, distinguishing them from organization categories |

#### Validation Rules

- `PK` must follow the format `category/0/{templateKey}` where `templateKey` is a unique identifier
- `SK` must start with `v` followed by a version number and Unix timestamp
- `orgId` must always be exactly `'category/0'` for templates
- `name` should be descriptive and unique across templates
- `language` should be a valid ISO language code
- `data` object structure should be valid JSON and match the expected schema for the `type`

#### Example JSON

```json
{
  "PK": "category/0/customer-satisfaction-analysis",
  "SK": "v0/1699574400000",
  "name": "Customer Satisfaction Analysis",
  "description": "Analyzes customer interactions to determine satisfaction levels based on sentiment, tone, and explicit feedback indicators",
  "language": "en",
  "data": {
    "thresholds": {
      "positive": 0.7,
      "negative": 0.3
    },
    "indicators": [
      "thank you",
      "great service",
      "disappointed",
      "frustrated"
    ],
    "weights": {
      "sentiment": 0.4,
      "tone": 0.3,
      "keywords": 0.3
    }
  },
  "type": "sentiment",
  "trigger": "call_end",
  "definitionString": "{\"thresholds\":{\"positive\":0.7,\"negative\":0.3},\"indicators\":[\"thank you\",\"great service\",\"disappointed\",\"frustrated\"],\"weights\":{\"sentiment\":0.4,\"tone\":0.3,\"keywords\":0.3}}",
  "orgId": "category/0"
}
```

#### Versioned Template Example

```json
{
  "PK": "category/0/compliance-check",
  "SK": "v1/1699488000000",
  "name": "Compliance Check",
  "description": "Monitors calls for regulatory compliance requirements",
  "language": "en",
  "data": {
    "requiredPhrases": [
      "This call may be recorded",
      "Do you consent to continue?"
    ],
    "prohibitedTopics": [
      "competitor_pricing",
      "unauthorized_discounts"
    ]
  },
  "type": "compliance",
  "trigger": "call_start",
  "definitionString": "{\"requiredPhrases\":[\"This call may be recorded\",\"Do you consent to continue?\"],\"prohibitedTopics\":[\"competitor_pricing\",\"unauthorized_discounts\"]}",
  "orgId": "category/0"
}
```

---

### TemplateListResponse

This model represents the response format when listing available category templates. It transforms the internal `CategoryTemplate` storage format into a client-friendly response structure.

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categoryKey` | string | Yes | Unique template identifier extracted from the `PK` field (without the `category/0/` prefix) |
| `name` | string | Yes | Template display name |
| `description` | string | Yes | Template description |
| `language` | string | Yes | Language code of the template |
| `data` | any | Yes | Template configuration data object |
| `type` | string | Yes | Template classification type |
| `trigger` | string | Yes | Event that triggers the template |
| `definitionString` | string | Yes | Serialized definition string |

#### Transformation Logic

The `categoryKey` is derived from the `PK` by removing the `category/0/` prefix:

```
PK: "category/0/customer-satisfaction-analysis"
     └─────────────────────────────────────────┘
categoryKey: "customer-satisfaction-analysis"
```

#### Example JSON

**Single Template Response**
```json
{
  "categoryKey": "customer-satisfaction-analysis",
  "name": "Customer Satisfaction Analysis",
  "description": "Analyzes customer interactions to determine satisfaction levels based on sentiment, tone, and explicit feedback indicators",
  "language": "en",
  "data": {
    "thresholds": {
      "positive": 0.7,
      "negative": 0.3
    },
    "indicators": [
      "thank you",
      "great service",
      "disappointed",
      "frustrated"
    ],
    "weights": {
      "sentiment": 0.4,
      "tone": 0.3,
      "keywords": 0.3
    }
  },
  "type": "sentiment",
  "trigger": "call_end",
  "definitionString": "{\"thresholds\":{\"positive\":0.7,\"negative\":0.3},\"indicators\":[\"thank you\",\"great service\",\"disappointed\",\"frustrated\"],\"weights\":{\"sentiment\":0.4,\"tone\":0.3,\"keywords\":0.3}}"
}
```

**List Templates Response (Array)**
```json
[
  {
    "categoryKey": "customer-satisfaction-analysis",
    "name": "Customer Satisfaction Analysis",
    "description": "Analyzes customer interactions to determine satisfaction levels",
    "language": "en",
    "data": {
      "thresholds": {
        "positive": 0.7,
        "negative": 0.3
      }
    },
    "type": "sentiment",
    "trigger": "call_end",
    "definitionString": "{\"thresholds\":{\"positive\":0.7,\"negative\":0.3}}"
  },
  {
    "categoryKey": "compliance-check",
    "name": "Compliance Check",
    "description": "Monitors calls for regulatory compliance requirements",
    "language": "en",
    "data": {
      "requiredPhrases": [
        "This call may be recorded"
      ]
    },
    "type": "compliance",
    "trigger": "call_start",
    "definitionString": "{\"requiredPhrases\":[\"This call may be recorded\"]}"
  },
  {
    "categoryKey": "sales-opportunity-detector",
    "name": "Sales Opportunity Detector",
    "description": "Identifies upsell and cross-sell opportunities during customer interactions",
    "language": "en",
    "data": {
      "keywords": [
        "upgrade",
        "additional features",
        "premium"
      ],
      "confidenceThreshold": 0.65
    },
    "type": "intent",
    "trigger": "real_time",
    "definitionString": "{\"keywords\":[\"upgrade\",\"additional features\",\"premium\"],\"confidenceThreshold\":0.65}"
  }
]
```

## Common Use Cases

### 1. Listing Available Templates

Retrieve all system templates for display in a template picker:

```typescript
// GET /templates
// Returns: TemplateListResponse[]

const templates = await listTemplates();
// Use to populate a dropdown or grid of available templates
```

### 2. Creating a Category from a Template

Use a template's data to create an organization-specific category:

```typescript
// 1. Fetch template
const template: TemplateListResponse = await getTemplate('customer-satisfaction-analysis');

// 2. Create category request using template data
const createRequest: CategoryCreateRequest = {
  categoryName: `${template.name} - Custom`,
  description: template.description,
  definitionString: template.definitionString,
  definition: template.data,
  type: template.type,
  trigger: template.trigger,
  language: template.language,
  enabled: true
};

// 3. Create organization category
await createCategory(orgId, createRequest);
```

### 3. Multi-Language Template Support

Templates can be filtered or selected based on language:

```typescript
const templates: TemplateListResponse[] = await listTemplates();
const spanishTemplates = templates.filter(t => t.language === 'es');
```

## Relationships

| Model | Relationship | Description |
|-------|--------------|-------------|
| [Category](./category.md) | Parent/Blueprint | Templates serve as blueprints for creating organization-specific categories |
| [CategoryCreateRequest](./category.md#categorycreaterequestcategoryeventbody) | Used With | Template data can be used to populate category creation requests |
| [CategoryListResponse](./category.md#categorylistresponse) | Parallel Structure | Both share similar response patterns for API consistency |

## Storage Pattern

Templates use the same DynamoDB table as categories but with a reserved organization ID:

| Entity Type | orgId Value | PK Format |
|-------------|-------------|-----------|
| Template | `category/0` | `category/0/{templateKey}` |
| Category | `category/{orgId}` | `category/{orgId}/{categoryKey}` |

This pattern allows:
- Efficient queries for all templates using a single partition key prefix
- Clear separation between system templates and organization categories
- Reuse of existing category infrastructure for template storage