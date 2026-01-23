# Utility Endpoints

This document covers utility, debugging, and testing endpoints in the Sapien API. These endpoints are primarily used for development, testing error handling, and system verification.

> **⚠️ Warning**: Most endpoints in this section are designed for testing and debugging purposes. They should be disabled or restricted in production environments.

## Table of Contents

- [Testing Endpoints](#testing-endpoints)
  - [Get Constant Response](#get-constant-response)
  - [Delete All Records](#delete-all-records)
- [Error Testing Endpoints](#error-testing-endpoints)
  - [Trigger REST Exception](#trigger-rest-exception)
  - [Trigger Common Exception](#trigger-common-exception)
  - [Trigger PHP Error](#trigger-php-error)
  - [Trigger Out of Memory](#trigger-out-of-memory)
- [Schema Testing Endpoints](#schema-testing-endpoints)
  - [No Schema Routes](#no-schema-routes)

---

## Testing Endpoints

### Get Constant Response

Returns a constant, predictable response for acceptance testing and health checks.

```
GET /constant
```

#### Description

This endpoint returns a fixed response that never changes, making it ideal for:
- Acceptance testing to verify API connectivity
- Health check monitoring
- Baseline response time measurements

#### Request Parameters

This endpoint accepts no parameters.

#### Request Example

```bash
curl -X GET \
  http://localhost:8080/constant \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "ok",
  "message": "constant response"
}
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `200 OK` | Constant response returned successfully |

---

### Delete All Records

Deletes all person records from the database using foreign-key cascade.

```
DELETE /all
```

#### Description

This endpoint removes all person records from the database. Due to foreign-key cascade relationships, this will also delete all related pet and toy records. This is primarily intended for:
- Resetting test environments
- Cleaning up after integration tests
- Development database resets

> **⚠️ Danger**: This operation is destructive and irreversible. All data will be permanently deleted.

#### Request Parameters

This endpoint accepts no parameters.

#### Request Example

```bash
curl -X DELETE \
  http://localhost:8080/all \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "status": "success",
  "message": "All records deleted"
}
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `200 OK` | All records deleted successfully |
| `500 Internal Server Error` | Database error during deletion |

---

## Error Testing Endpoints

These endpoints are designed to test error handling, logging, and exception management in the API.

### Trigger REST Exception

Triggers a REST exception with a specified HTTP status code.

```
GET /rest-exception/{http_status_code}
```

#### Description

This endpoint intentionally throws a REST exception with the specified HTTP status code. Use it to:
- Test error handling middleware
- Verify error response formats
- Test client-side error handling

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `http_status_code` | path | integer | Yes | HTTP status code to return (e.g., 400, 404, 500) |

#### Request Example

```bash
# Trigger a 404 Not Found exception
curl -X GET \
  http://localhost:8080/rest-exception/404 \
  -H "Accept: application/json"

# Trigger a 500 Internal Server Error exception
curl -X GET \
  http://localhost:8080/rest-exception/500 \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "error": {
    "code": 404,
    "message": "REST Exception triggered with status code 404"
  }
}
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `{http_status_code}` | Returns the status code specified in the path parameter |

---

### Trigger Common Exception

Triggers a CommonException for testing exception handling.

```
GET /common-exception
```

#### Description

This endpoint throws a `CommonException`, which is the base exception type used throughout the application. Use it to test how the API handles and formats common application exceptions.

#### Request Parameters

This endpoint accepts no parameters.

#### Request Example

```bash
curl -X GET \
  http://localhost:8080/common-exception \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "error": {
    "code": 500,
    "message": "CommonException triggered for testing"
  }
}
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `500 Internal Server Error` | CommonException thrown as expected |

---

### Trigger PHP Error

Triggers a PHP error at the specified error level.

```
GET /error/{error_level}
```

#### Description

This endpoint intentionally triggers a PHP error at the specified level. Useful for testing:
- Error logging configuration
- Error-to-exception conversion
- Different error level handling

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `error_level` | path | integer | Yes | PHP error level constant (e.g., E_WARNING = 2, E_NOTICE = 8, E_USER_ERROR = 256) |

#### Common Error Levels

| Level | Constant | Description |
|-------|----------|-------------|
| `2` | E_WARNING | Runtime warnings |
| `8` | E_NOTICE | Runtime notices |
| `256` | E_USER_ERROR | User-generated error |
| `512` | E_USER_WARNING | User-generated warning |
| `1024` | E_USER_NOTICE | User-generated notice |

#### Request Example

```bash
# Trigger an E_USER_WARNING (512)
curl -X GET \
  http://localhost:8080/error/512 \
  -H "Accept: application/json"

# Trigger an E_USER_ERROR (256)
curl -X GET \
  http://localhost:8080/error/256 \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "error": {
    "code": 500,
    "message": "PHP error triggered at level 256"
  }
}
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `500 Internal Server Error` | Error triggered (for fatal error levels) |
| `200 OK` | Warning/notice triggered but execution continued |

---

### Trigger Out of Memory

Causes an out of memory error by exhausting available memory.

```
GET /out-of-memory
```

#### Description

This endpoint intentionally exhausts available memory to trigger an out-of-memory (OOM) fatal error. Use it to test:
- OOM error handling and recovery
- Memory limit configurations
- Monitoring and alerting systems

> **⚠️ Danger**: This endpoint will crash the PHP process. Use with extreme caution and only in isolated test environments.

#### Request Parameters

This endpoint accepts no parameters.

#### Request Example

```bash
curl -X GET \
  http://localhost:8080/out-of-memory \
  -H "Accept: application/json"
```

#### Response Example

The request will not return a normal response. Instead, PHP will terminate with a fatal error:

```
Fatal error: Allowed memory size of 134217728 bytes exhausted
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `500 Internal Server Error` | Memory exhausted (if error handling catches it) |
| Connection Reset | PHP process terminated due to OOM |

---

## Schema Testing Endpoints

### No Schema Routes

Routes intentionally configured without an associated schema to test schema validation error handling.

```
POST /no-schema
PUT /no-schema
PATCH /no-schema
```

#### Description

These endpoints have no associated request/response schemas configured. They are designed to test how the API handles missing schema definitions and to verify that appropriate "schema not found" exceptions are thrown and handled correctly.

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| (any) | body | object | No | Any JSON body (will fail schema validation) |

#### Request Examples

```bash
# POST request with no schema
curl -X POST \
  http://localhost:8080/no-schema \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"test": "data"}'

# PUT request with no schema
curl -X PUT \
  http://localhost:8080/no-schema \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"test": "data"}'

# PATCH request with no schema
curl -X PATCH \
  http://localhost:8080/no-schema \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"test": "data"}'
```

#### Response Example

```json
{
  "error": {
    "code": 500,
    "message": "Schema not found for route: /no-schema"
  }
}
```

#### Response Codes

| Status Code | Description |
|-------------|-------------|
| `500 Internal Server Error` | Schema not found exception thrown |

---

## Related Documentation

- [Person Endpoints](person-endpoints.md) - CRUD operations for Person entities
- [Pet Endpoints](pet-endpoints.md) - CRUD operations for Pet entities
- [Toy Endpoints](toy-endpoints.md) - CRUD operations for Toy entities
- [Authentication](authentication.md) - API authentication details