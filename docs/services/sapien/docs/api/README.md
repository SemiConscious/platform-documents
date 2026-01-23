# Sapien API Reference

Welcome to the Sapien API documentation. Sapien is a PHP-based REST API service built on Symfony, providing CRUD operations for core entities with real-time event updates via the ESL event system.

## Base URL

```
http://localhost:8080
```

For production environments, replace with your configured domain.

## API Overview

The Sapien API follows RESTful conventions, providing standard CRUD operations across multiple entity types. The API uses JSON for request and response bodies.

### Key Features

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **JSON-based**: All requests and responses use `application/json`
- **ESL Events**: Real-time updates via the Event System Layer
- **Cascade Deletes**: Foreign key relationships with automatic cascade deletion

## Authentication

For detailed authentication information, including token management and security best practices, see the [Authentication Guide](authentication.md).

### Quick Start

Most endpoints require authentication via Bearer token:

```bash
curl -X GET "http://localhost:8080/person/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

## Endpoint Categories

| Category | Description | Documentation |
|----------|-------------|---------------|
| **Person** | CRUD operations for person records | [Person Endpoints](person-endpoints.md) |
| **Pet** | CRUD operations for pet records | [Pet Endpoints](pet-endpoints.md) |
| **Toy** | CRUD operations for toy records | [Toy Endpoints](toy-endpoints.md) |
| **Utility** | Testing, diagnostics, and administrative endpoints | [Utility Endpoints](utility-endpoints.md) |

## Endpoints at a Glance

### Person Endpoints (5 endpoints)
Full CRUD support for managing person records.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/person/{id}` | Retrieve a person |
| POST | `/person` | Create a new person |
| PUT | `/person/{id}` | Fully update a person |
| PATCH | `/person/{id}` | Partially update a person |
| DELETE | `/person/{id}` | Delete a person |

→ [View Person Endpoints Documentation](person-endpoints.md)

### Pet Endpoints (5 endpoints)
CRUD operations for pet management. *Note: Currently not implemented.*

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pet/{id}` | Retrieve a pet |
| POST | `/pet` | Create a new pet |
| PUT | `/pet/{id}` | Update a pet |
| PATCH | `/pet/{id}` | Partially update a pet |
| DELETE | `/pet/{id}` | Delete a pet |

→ [View Pet Endpoints Documentation](pet-endpoints.md)

### Toy Endpoints (5 endpoints)
CRUD operations for toy management. *Note: Currently not implemented.*

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/toy/{id}` | Retrieve a toy |
| POST | `/toy` | Create a new toy |
| PUT | `/toy/{id}` | Update a toy |
| PATCH | `/toy/{id}` | Partially update a toy |
| DELETE | `/toy/{id}` | Delete a toy |

→ [View Toy Endpoints Documentation](toy-endpoints.md)

### Utility Endpoints (9 endpoints)
Administrative and testing utilities including error simulation and bulk operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| DELETE | `/all` | Delete all person records |
| GET | `/constant` | Returns constant response for testing |
| GET | `/rest-exception/{code}` | Trigger REST exception |
| GET | `/common-exception` | Trigger CommonException |
| GET | `/error/{level}` | Trigger PHP error |
| GET | `/out-of-memory` | Simulate OOM error |
| POST/PUT/PATCH | `/no-schema` | Test schema validation |

→ [View Utility Endpoints Documentation](utility-endpoints.md)

## Common Request/Response Patterns

### Request Headers

All API requests should include:

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Successful Response Format

```json
{
  "data": {
    "id": 1,
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request body is invalid",
    "details": [
      {
        "field": "name",
        "message": "This field is required"
      }
    ]
  }
}
```

## HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `204 No Content` | Request succeeded with no response body |
| `400 Bad Request` | Invalid request syntax or parameters |
| `401 Unauthorized` | Authentication required or failed |
| `403 Forbidden` | Authenticated but not authorized |
| `404 Not Found` | Resource does not exist |
| `405 Method Not Allowed` | HTTP method not supported for endpoint |
| `422 Unprocessable Entity` | Validation errors |
| `500 Internal Server Error` | Server-side error |
| `501 Not Implemented` | Endpoint exists but not yet implemented |

## Error Handling

The API uses consistent error responses across all endpoints:

### Validation Errors (422)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Not Found Errors (404)

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Person with ID 999 not found"
  }
}
```

### Server Errors (500)

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

| Limit Type | Value |
|------------|-------|
| Requests per minute | 60 |
| Requests per hour | 1000 |

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312800
```

When rate limited, you'll receive a `429 Too Many Requests` response.

## PUT vs PATCH

The API distinguishes between full and partial updates:

| Method | Behavior |
|--------|----------|
| **PUT** | Replaces the entire resource. All fields are updated; missing fields may be set to null/default |
| **PATCH** | Partial update. Only provided (non-null) fields are updated |

### Example

```bash
# PUT - Full replacement (all fields required)
curl -X PUT "http://localhost:8080/person/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "age": 30}'

# PATCH - Partial update (only email changes)
curl -X PATCH "http://localhost:8080/person/1" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'
```

## ESL Event System

Sapien integrates with the ESL (Event System Layer) for real-time updates. When resources are created, updated, or deleted, corresponding events are published.

### Event Types

- `person.created`
- `person.updated`
- `person.deleted`
- `pet.created` / `pet.updated` / `pet.deleted`
- `toy.created` / `toy.updated` / `toy.deleted`

## Development & Testing

### Docker Environment

The API runs in a Docker-based development environment. See the project README for setup instructions.

### Xdebug Integration

Xdebug is available for debugging. Configure your IDE to listen on the configured port.

### Test Endpoints

The [Utility Endpoints](utility-endpoints.md) include several routes specifically for testing:

- `/constant` - Returns a predictable response for acceptance tests
- `/rest-exception/{code}` - Simulates HTTP errors
- `/common-exception` - Triggers exception handling
- `/error/{level}` - Tests PHP error handling
- `/out-of-memory` - Tests OOM handling

## Quick Reference

### Complete Endpoint List

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/person/{id}` | ✅ Implemented |
| POST | `/person` | ✅ Implemented |
| PUT | `/person/{id}` | ✅ Implemented |
| PATCH | `/person/{id}` | ✅ Implemented |
| DELETE | `/person/{id}` | ✅ Implemented |
| GET | `/pet/{id}` | ⚠️ Not Implemented |
| POST | `/pet` | ⚠️ Not Implemented |
| PUT | `/pet/{id}` | ⚠️ Not Implemented |
| PATCH | `/pet/{id}` | ⚠️ Not Implemented |
| DELETE | `/pet/{id}` | ⚠️ Not Implemented |
| GET | `/toy/{id}` | ⚠️ Not Implemented |
| POST | `/toy` | ⚠️ Not Implemented |
| PUT | `/toy/{id}` | ⚠️ Not Implemented |
| PATCH | `/toy/{id}` | ⚠️ Not Implemented |
| DELETE | `/toy/{id}` | ⚠️ Not Implemented |
| DELETE | `/all` | ✅ Implemented |
| GET | `/constant` | ✅ Implemented |
| GET | `/rest-exception/{http_status_code}` | ✅ Implemented |
| GET | `/common-exception` | ✅ Implemented |
| GET | `/error/{error_level}` | ✅ Implemented |
| GET | `/out-of-memory` | ✅ Implemented |
| POST | `/no-schema` | ✅ Implemented |
| PUT | `/no-schema` | ✅ Implemented |
| PATCH | `/no-schema` | ✅ Implemented |

## Documentation Index

| Document | Description |
|----------|-------------|
| [Authentication](authentication.md) | Authentication methods, tokens, and security |
| [Person Endpoints](person-endpoints.md) | Full documentation for person CRUD operations |
| [Pet Endpoints](pet-endpoints.md) | Full documentation for pet CRUD operations |
| [Toy Endpoints](toy-endpoints.md) | Full documentation for toy CRUD operations |
| [Utility Endpoints](utility-endpoints.md) | Administrative and testing endpoints |