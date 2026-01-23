# API Integration Overview

## Introduction

The Insight Category UI application integrates with backend services through Salesforce Remote Actions, providing a seamless interface for managing voice analytics categorization. This document provides an overview of the API integration patterns and serves as an index to detailed endpoint documentation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Insight Category UI                          │
│                  (React/TypeScript Frontend)                    │
├─────────────────────────────────────────────────────────────────┤
│                     Redux State Management                       │
├─────────────────────────────────────────────────────────────────┤
│                  Salesforce Remote Actions Layer                 │
├─────────────────────────────────────────────────────────────────┤
│                      Salesforce Backend                          │
└─────────────────────────────────────────────────────────────────┘
```

All API communication flows through Salesforce Remote Actions, which handle authentication, request routing, and response processing automatically within the Salesforce ecosystem.

## Authentication

The application uses JWT (JSON Web Token) authentication for secure API communication. Authentication is handled transparently through the Salesforce session context.

| Method | Description |
|--------|-------------|
| **Salesforce Session** | Primary authentication via active Salesforce user session |
| **JWT Token** | Obtained via `/jwt` endpoint for additional service authentication |

For detailed authentication implementation, see [Authentication Documentation](authentication.md).

## API Endpoints Summary

The API provides **9 endpoints** organized into four functional areas:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| [Authentication](authentication.md) | 2 | JWT token retrieval and namespace configuration |
| [Categories](categories.md) | 3 | Create, update, and delete voice analytics categories |
| [Prompts](prompts.md) | 3 | Manage AI prompt configurations for call analysis |
| [Users](users.md) | 1 | Retrieve user information for category assignment |

## Detailed Documentation Index

### Authentication & Configuration

| Endpoint | Method | Documentation |
|----------|--------|---------------|
| `/jwt` | GET | [authentication.md](authentication.md) |
| `/namespace` | GET | [authentication.md](authentication.md) |

### Category Management

| Endpoint | Method | Documentation |
|----------|--------|---------------|
| `/category` | POST | [categories.md](categories.md) |
| `/category` | PUT | [categories.md](categories.md) |
| `/category/:categoryIdFromAPI` | DELETE | [categories.md](categories.md) |

### Prompt Management

| Endpoint | Method | Documentation |
|----------|--------|---------------|
| `/prompt` | POST | [prompts.md](prompts.md) |
| `/prompt` | PUT | [prompts.md](prompts.md) |
| `/prompt/:promptIdFromAPI` | DELETE | [prompts.md](prompts.md) |

### User Management

| Endpoint | Method | Documentation |
|----------|--------|---------------|
| `/users` | GET | [users.md](users.md) |

## Common Integration Patterns

### Remote Action Invocation

All API calls are made through the `salesforceRemoteActions` service layer:

```typescript
import { salesforceRemoteActions } from '@/shared/api';

// Example pattern for API calls
const result = await salesforceRemoteActions.methodName(params);
```

### Redux Integration

API calls are typically dispatched through Redux async thunks:

```typescript
// Dispatch an API action
dispatch(fetchCategories());

// Handle loading states
const { loading, error, data } = useSelector(selectCategoriesState);
```

### Request/Response Flow

1. **UI Action** → User triggers an action in the interface
2. **Redux Dispatch** → Action is dispatched to the store
3. **Async Thunk** → Thunk calls the appropriate Remote Action
4. **Salesforce Processing** → Backend processes the request
5. **State Update** → Redux store is updated with the response
6. **UI Render** → Component re-renders with new data

## Error Handling

### Standard Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description"
  }
}
```

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `AUTH_EXPIRED` | Session has expired | Re-authenticate through Salesforce |
| `INVALID_INPUT` | Request validation failed | Check request parameters |
| `NOT_FOUND` | Resource does not exist | Verify resource ID |
| `PERMISSION_DENIED` | Insufficient permissions | Contact administrator |
| `SERVER_ERROR` | Internal server error | Retry or contact support |

### Error Handling Pattern

```typescript
try {
  const result = await salesforceRemoteActions.createCategory(categoryData);
  if (result.success) {
    // Handle success
  } else {
    // Handle API-level error
    console.error(result.error.message);
  }
} catch (error) {
  // Handle network/system error
  console.error('Request failed:', error);
}
```

## Rate Limiting

API requests are subject to Salesforce governor limits:

| Limit Type | Threshold | Scope |
|------------|-----------|-------|
| Remote Action calls | 10 per transaction | Per transaction |
| Concurrent requests | 25 | Per user |
| Daily API calls | Varies by org edition | Per organization |

### Best Practices

- **Batch Operations**: Combine multiple operations when possible
- **Caching**: Utilize Redux state to minimize redundant requests
- **Debouncing**: Implement debounce for user-triggered searches
- **Optimistic Updates**: Update UI immediately, rollback on failure

## Data Consistency

### Namespace Handling

The application operates within a Salesforce namespace context. Always retrieve the namespace configuration before making API calls that require namespaced object references:

```typescript
const namespace = await salesforceRemoteActions.getNamespace();
```

### ID Formats

| Entity | ID Format | Example |
|--------|-----------|---------|
| Category | Salesforce API ID | `a0B5g000001ABC123` |
| Prompt | Salesforce API ID | `a0C5g000002DEF456` |
| User | Salesforce User ID | `0055g000003GHI789` |

## Next Steps

- Review [Authentication](authentication.md) to understand the security model
- Explore [Categories](categories.md) for category management operations
- See [Prompts](prompts.md) for AI prompt configuration
- Check [Users](users.md) for user data retrieval