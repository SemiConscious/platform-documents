# Workflow Data Models

This document covers the data models used for workflow processing within the omnichannel-omniservice system. These models track workflow execution status, manage workflow step progression, and handle workflow responses throughout the message processing pipeline.

## Overview

Workflow data models are essential for managing the execution flow of messages through various processing stages. They enable:

- Tracking workflow step execution status
- Capturing workflow execution results
- Managing workflow activities and logging
- Coordinating workflow variables and session state

## Entity Relationship Diagram

```
┌─────────────────────┐
│   ServiceMessage    │
│                     │
│  ┌───────────────┐  │
│  │ workFlowSteps │──┼──────────────────────────────────┐
│  └───────────────┘  │                                  │
│  ┌───────────────┐  │                                  ▼
│  │ emittedEvents │  │                      ┌──────────────────────┐
│  └───────────────┘  │                      │    WorkFlowSteps     │
└─────────────────────┘                      │                      │
                                             │ - identityLookup     │
                                             │ - preRoutingWorkFlow │
                                             │ - inboundWorkFlow    │
                                             │ - outboundWorkFlow   │
                                             └──────────────────────┘
                                                        │
                                                        │ produces
                                                        ▼
┌──────────────────────┐                     ┌──────────────────────┐
│   WorkFlowResult     │◄────────────────────│   WorkFlowResponse   │
│                      │     result type     │                      │
│ - HTTP_SUCCESS       │                     │ - statusCode         │
│ - HTTP_NOT_FOUND     │                     │ - logActivity        │
│ - HTTP_BAD_REQUEST   │                     │ - customVariables    │
│ - HTTP_INTERNAL_...  │                     │ - sessionVariables   │
└──────────────────────┘                     └──────────────────────┘
```

## Core Workflow Models

### WorkFlowSteps

Tracks the execution status of various workflow steps during message processing. This model is embedded within `ServiceMessage` and provides visibility into which processing stages have been executed.

#### Purpose and Usage

- Track the completion status of each workflow phase
- Audit workflow execution for debugging and monitoring
- Enable conditional processing based on completed steps
- Support retry logic for failed workflow steps

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `identityLookup` | `string` | No | Status of the identity lookup step. Values: `REQUIRED`, `EXECUTED_OK`, `EXECUTED_FAILED` |
| `preRoutingWorkFlow` | `string` | No | Status of pre-routing workflow execution |
| `inboundWorkFlow` | `string` | No | Status of inbound message workflow execution |
| `outboundWorkFlow` | `string` | No | Status of outbound message workflow execution |

#### Validation Rules

- Status values must be one of the predefined states
- Steps are executed in sequence: `identityLookup` → `preRoutingWorkFlow` → `inboundWorkFlow`/`outboundWorkFlow`
- A step must be `EXECUTED_OK` before subsequent steps can execute

#### Example JSON

```json
{
  "identityLookup": "EXECUTED_OK",
  "preRoutingWorkFlow": "EXECUTED_OK",
  "inboundWorkFlow": "EXECUTED_OK",
  "outboundWorkFlow": "REQUIRED"
}
```

#### Workflow Step States

| State | Description |
|-------|-------------|
| `REQUIRED` | Step needs to be executed |
| `EXECUTED_OK` | Step completed successfully |
| `EXECUTED_FAILED` | Step execution failed |
| `SKIPPED` | Step was intentionally skipped |

---

### WorkFlowResponse

Response structure returned from workflow engine execution, containing execution results, activity logs, and variable state.

#### Purpose and Usage

- Capture detailed workflow execution results
- Provide activity logging for debugging and auditing
- Return custom and session variables from workflow execution
- Enable downstream processing based on workflow outcomes

#### Field Definitions

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `statusCode` | `string` | Yes | Workflow execution status code (e.g., `HTTP_SUCCESS`, `HTTP_NOT_FOUND`) |
| `logActivity` | `array` | No | Array of activity log entries documenting workflow execution |
| `customVariables` | `Record<string, any>[]` | No | Custom variables set during workflow execution |
| `sessionVariables` | `Record<string, any>[]` | No | Session-scoped variables from workflow execution |

#### Log Activity Entry Structure

Each entry in `logActivity` contains:

| Field | Type | Description |
|-------|------|-------------|
| `timeStamp` | `string` | ISO 8601 timestamp of the activity |
| `type` | `string` | Type of activity (e.g., `INFO`, `ERROR`, `DEBUG`) |
| `activity` | `string` | Activity name or action taken |
| `componentId` | `string` | ID of the workflow component |
| `componentName` | `string` | Human-readable component name |
| `description` | `string` | Detailed description of the activity |

#### Validation Rules

- `statusCode` must be a valid `WorkFlowResult` value
- `logActivity` entries must have valid timestamps
- Variable records must be valid JSON objects

#### Example JSON

```json
{
  "statusCode": "HTTP_SUCCESS",
  "logActivity": [
    {
      "timeStamp": "2024-01-15T10:30:00.000Z",
      "type": "INFO",
      "activity": "StartWorkflow",
      "componentId": "wf-001",
      "componentName": "InboundMessageRouter",
      "description": "Started inbound message routing workflow"
    },
    {
      "timeStamp": "2024-01-15T10:30:00.150Z",
      "type": "INFO",
      "activity": "RouteDecision",
      "componentId": "wf-002",
      "componentName": "ChannelRouter",
      "description": "Routed message to shared channel group DCG-12345"
    },
    {
      "timeStamp": "2024-01-15T10:30:00.200Z",
      "type": "INFO",
      "activity": "EndWorkflow",
      "componentId": "wf-001",
      "componentName": "InboundMessageRouter",
      "description": "Workflow completed successfully"
    }
  ],
  "customVariables": [
    {
      "routingPriority": "high",
      "assignedAgent": "user-456"
    }
  ],
  "sessionVariables": [
    {
      "conversationContext": "support_inquiry",
      "customerTier": "premium"
    }
  ]
}
```

#### Relationships

- Used in conjunction with `WorkFlowSteps` to update step status
- Variables may be passed to subsequent workflow executions
- Log activities are persisted for audit and debugging purposes

---

### WorkFlowResult

Enumeration defining possible workflow execution result types. Used to standardize workflow outcome reporting.

#### Purpose and Usage

- Standardize workflow execution outcome codes
- Enable consistent error handling across workflow types
- Support HTTP-compatible status reporting
- Facilitate monitoring and alerting on workflow failures

#### Enum Values

| Value | Description | HTTP Equivalent |
|-------|-------------|-----------------|
| `HTTP_SUCCESS` | Workflow executed successfully | 200 OK |
| `HTTP_NOT_FOUND` | Workflow policy not found for the given criteria | 404 Not Found |
| `HTTP_BAD_REQUEST` | Invalid request to workflow engine | 400 Bad Request |
| `HTTP_INTERNAL_SERVER_ERROR` | Internal workflow engine error | 500 Internal Server Error |

#### Example Usage

```json
{
  "result": "HTTP_SUCCESS"
}
```

```typescript
// In workflow execution logic
if (response.statusCode === WorkFlowResult.HTTP_SUCCESS) {
  // Continue processing
} else if (response.statusCode === WorkFlowResult.HTTP_NOT_FOUND) {
  // No workflow policy configured - use default behavior
} else {
  // Handle error condition
}
```

---

## Workflow Context in ServiceMessage

The `ServiceMessage` model contains workflow-related fields that track execution state throughout message processing.

### Workflow-Related Fields in ServiceMessage

| Field Name | Type | Description |
|------------|------|-------------|
| `workFlowSteps` | `WorkFlowSteps` | Current status of workflow step execution |
| `emittedEvents` | `object` | Events emitted during workflow processing |
| `conversationResolution` | `array<string>` | Audit trail of conversation routing decisions |

### Example ServiceMessage with Workflow Context

```json
{
  "correlationId": "corr-abc123-def456",
  "tenant": {
    "orgId": 1001,
    "userId": 5001
  },
  "direction": "INBOUND",
  "createdDateTime": "2024-01-15T10:30:00.000Z",
  "sqsGroupId": "org-1001-identity-+14155551234",
  "messagePayLoad": {
    "textMessage": {
      "text": "Hello, I need help with my order"
    }
  },
  "digitalChannel": {
    "carrier": "Twilio",
    "address": "+18005551234",
    "channelType": "SMS",
    "digitalChannelId": "dc-789"
  },
  "identity": {
    "channelType": "SMS",
    "address": "+14155551234",
    "displayName": "John Customer"
  },
  "workFlowSteps": {
    "identityLookup": "EXECUTED_OK",
    "preRoutingWorkFlow": "EXECUTED_OK",
    "inboundWorkFlow": "REQUIRED",
    "outboundWorkFlow": null
  },
  "emittedEvents": {
    "identityResolved": {
      "timestamp": "2024-01-15T10:30:00.050Z",
      "identityId": "identity-123"
    },
    "channelGroupResolved": {
      "timestamp": "2024-01-15T10:30:00.100Z",
      "digitalChannelGroupId": "dcg-456"
    }
  },
  "conversationResolution": [
    "IdentityLookup:identity-123",
    "ChannelGroupMapping:dcg-456",
    "FolderAssignment:folder-789"
  ],
  "conversationOnHold": false
}
```

---

## Workflow Processing Flow

### Inbound Message Workflow Sequence

```
1. Message Received
        │
        ▼
2. identityLookup: REQUIRED → EXECUTED_OK
   (Resolve contact identity)
        │
        ▼
3. preRoutingWorkFlow: REQUIRED → EXECUTED_OK
   (Apply pre-routing rules, channel mapping)
        │
        ▼
4. inboundWorkFlow: REQUIRED → EXECUTED_OK
   (Route to folder, assign owner, create interaction)
        │
        ▼
5. Message Delivered to Destination
```

### Outbound Message Workflow Sequence

```
1. Outbound Message Initiated
        │
        ▼
2. outboundWorkFlow: REQUIRED → EXECUTED_OK
   (Validate consent, apply templates, select carrier)
        │
        ▼
3. Carrier Publish
        │
        ▼
4. Delivery Status Tracking
```

---

## Common Use Cases

### 1. Checking Workflow Completion

```typescript
function isWorkflowComplete(workFlowSteps: WorkFlowSteps, direction: string): boolean {
  if (direction === 'INBOUND') {
    return workFlowSteps.identityLookup === 'EXECUTED_OK' &&
           workFlowSteps.preRoutingWorkFlow === 'EXECUTED_OK' &&
           workFlowSteps.inboundWorkFlow === 'EXECUTED_OK';
  } else {
    return workFlowSteps.outboundWorkFlow === 'EXECUTED_OK';
  }
}
```

### 2. Handling Workflow Failures

```typescript
function handleWorkflowResponse(response: WorkFlowResponse): void {
  switch (response.statusCode) {
    case 'HTTP_SUCCESS':
      // Process custom variables and continue
      processVariables(response.customVariables);
      break;
    case 'HTTP_NOT_FOUND':
      // No workflow policy - use default routing
      applyDefaultRouting();
      break;
    case 'HTTP_BAD_REQUEST':
    case 'HTTP_INTERNAL_SERVER_ERROR':
      // Log error and retry or escalate
      logWorkflowFailure(response.logActivity);
      break;
  }
}
```

### 3. Auditing Workflow Execution

```typescript
function generateWorkflowAuditLog(
  message: ServiceMessage,
  response: WorkFlowResponse
): AuditEntry {
  return {
    correlationId: message.correlationId,
    orgId: message.tenant.orgId,
    workflowSteps: message.workFlowSteps,
    activities: response.logActivity,
    resolutionPath: message.conversationResolution,
    timestamp: new Date().toISOString()
  };
}
```

---

## Related Documentation

- [Message Models](./message-models.md) - Core ServiceMessage structure
- [Channel Models](./channel-models.md) - Digital channel configurations
- [Contact Models](./contact-models.md) - Identity and contact resolution