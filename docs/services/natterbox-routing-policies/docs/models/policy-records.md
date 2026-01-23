# Policy and Record Models

This document covers the data models used for routing policies, records, and snapshots within the Natterbox Routing Policies service. These models handle the creation and management of Salesforce records, record type configuration, and associated metadata.

## Overview

The Policy and Record Models provide the foundation for integrating routing policies with Salesforce CRM data. They enable:

- Creation and updates of Salesforce records within routing workflows
- Record type selection and configuration
- Owner assignment and field mapping

## Entity Relationships

```
┌─────────────────────────┐
│  CreateRecordTypeProps  │
├─────────────────────────┤
│  - ownerId              │──────► Salesforce User
│  - sObject              │──────► Salesforce Object
│  - recordId             │──────► Salesforce Record (for updates)
│  - typeList[]           │
│    ├── label            │
│    └── name             │
└─────────────────────────┘
```

## Models

### CreateRecordTypeProps

Properties for the CreateRecordType React component, used to configure record creation within routing policies.

#### Purpose

This model defines the configuration required to create or update Salesforce records as part of a routing policy workflow. It enables dynamic record type selection, owner assignment, and supports both create and update operations.

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ownerId` | `string` | Yes | The Salesforce User ID that will own the created/updated record |
| `sObject` | `string` | Yes | The Salesforce object type (API name) for the record (e.g., `Case`, `Lead`, `Account`) |
| `typeList` | `array<{label: string, name: string}>` | Yes | List of available record types for the selected Salesforce object |
| `isUpdate` | `boolean` | Yes | Flag indicating whether this operation updates an existing record (`true`) or creates a new one (`false`) |
| `recordId` | `string` | Conditional | The Salesforce Record ID for update operations. Required when `isUpdate` is `true` |
| `showAPIName` | `boolean` | Yes | Controls display preference: `true` shows API names, `false` shows user-friendly labels |
| `handleChange` | `function` | Yes | Callback function invoked when any property value changes |

#### Type List Structure

The `typeList` array contains objects with the following structure:

| Field | Type | Description |
|-------|------|-------------|
| `label` | `string` | User-friendly display name for the record type |
| `name` | `string` | Salesforce API name for the record type |

#### Validation Rules

1. **ownerId**: Must be a valid 15 or 18-character Salesforce User ID
2. **sObject**: Must be a valid Salesforce object API name
3. **recordId**: Required only when `isUpdate` is `true`; must be a valid 15 or 18-character Salesforce Record ID
4. **typeList**: Must contain at least one record type option
5. **handleChange**: Must be a valid callable function

#### Example JSON

```json
{
  "ownerId": "005xx000001SvqAAAS",
  "sObject": "Case",
  "typeList": [
    {
      "label": "Support Case",
      "name": "Support_Case"
    },
    {
      "label": "Billing Inquiry",
      "name": "Billing_Inquiry"
    },
    {
      "label": "Technical Issue",
      "name": "Technical_Issue"
    }
  ],
  "isUpdate": false,
  "recordId": "",
  "showAPIName": false,
  "handleChange": "function(field, value) { /* callback logic */ }"
}
```

#### Update Operation Example

```json
{
  "ownerId": "005xx000001SvqAAAS",
  "sObject": "Case",
  "typeList": [
    {
      "label": "Support Case",
      "name": "Support_Case"
    },
    {
      "label": "Escalated Case",
      "name": "Escalated_Case"
    }
  ],
  "isUpdate": true,
  "recordId": "500xx000000bZ8YAAU",
  "showAPIName": true,
  "handleChange": "function(field, value) { /* callback logic */ }"
}
```

#### Common Use Cases

1. **Inbound Call Record Creation**
   - Create a new Case record when a customer calls in
   - Assign ownership based on routing rules
   - Select appropriate record type based on call context

2. **Record Update During Call**
   - Update an existing Case with call details
   - Change record type based on call outcome
   - Reassign ownership after escalation

3. **Lead Capture from Calls**
   - Create Lead records from sales calls
   - Set record type based on lead source or campaign

4. **Account Management**
   - Update Account records with interaction history
   - Create related child records (Contacts, Opportunities)

#### Integration Patterns

**With Routing Policies:**
```json
{
  "policyStep": "createRecord",
  "config": {
    "ownerId": "${assignedAgent.salesforceId}",
    "sObject": "Case",
    "typeList": "${org.caseRecordTypes}",
    "isUpdate": false,
    "showAPIName": false
  }
}
```

**Conditional Record Type Selection:**
```json
{
  "condition": "callerIntent === 'billing'",
  "createRecordConfig": {
    "ownerId": "005xx000001BillingQ",
    "sObject": "Case",
    "typeList": [
      {
        "label": "Billing Inquiry",
        "name": "Billing_Inquiry"
      }
    ],
    "isUpdate": false
  }
}
```

## Related Documentation

- [AI Routing Models](./ai-routing.md) - For AI-driven routing decisions that may trigger record creation
- [Messaging Models](./messaging.md) - For sending notifications after record operations
- [Routing Variables](./routing-variables.md) - For variable handling in record field mapping