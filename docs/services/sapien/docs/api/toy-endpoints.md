# Toy API Endpoints

Complete documentation for Toy entity CRUD operations in the Sapien API.

> **Note:** The Toy endpoints are currently **not implemented**. The routes are defined but will return appropriate error responses until the implementation is completed. This documentation describes the intended API contract.

## Overview

The Toy API provides standard CRUD (Create, Read, Update, Delete) operations for managing toy resources. Toys can be associated with pets and persons within the system.

## Base URL

```
http://localhost:8080
```

---

## Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/toy/{id}` | Retrieve a toy by ID | Not Implemented |
| `POST` | `/toy` | Create a new toy | Not Implemented |
| `PUT` | `/toy/{id}` | Fully update a toy | Not Implemented |
| `PATCH` | `/toy/{id}` | Partially update a toy | Not Implemented |
| `DELETE` | `/toy/{id}` | Delete a toy | Not Implemented |

---

## GET /toy/{id}

Retrieve a toy by its unique identifier.

### Description

Fetches a single toy resource by ID. Returns the complete toy object if found.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the toy |

### Request Example

```bash
curl -X GET "http://localhost:8080/toy/1" \
  -H "Accept: application/json"
```

### Response Example

**Success (200 OK):**
```json
{
  "id": 1,
  "name": "Squeaky Ball",
  "type": "ball",
  "color": "red",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Toy retrieved successfully |
| `404` | Toy not found |
| `500` | Internal server error |
| `501` | Not implemented |

---

## POST /toy

Create a new toy record.

### Description

Creates a new toy in the system. All required fields must be provided in the request body.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `name` | body | string | Yes | The name of the toy |
| `type` | body | string | No | The type/category of toy |
| `color` | body | string | No | The color of the toy |

### Request Example

```bash
curl -X POST "http://localhost:8080/toy" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "Squeaky Ball",
    "type": "ball",
    "color": "red"
  }'
```

### Response Example

**Success (201 Created):**
```json
{
  "id": 1,
  "name": "Squeaky Ball",
  "type": "ball",
  "color": "red",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Error Codes

| Status Code | Description |
|-------------|-------------|
| `201` | Toy created successfully |
| `400` | Bad request - Invalid or missing required fields |
| `422` | Unprocessable entity - Validation error |
| `500` | Internal server error |
| `501` | Not implemented |

---

## PUT /toy/{id}

Fully update an existing toy record (replace all fields).

### Description

Replaces all fields of an existing toy with the provided values. Fields not included in the request will be set to their default values or null.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the toy |
| `name` | body | string | Yes | The name of the toy |
| `type` | body | string | No | The type/category of toy |
| `color` | body | string | No | The color of the toy |

### Request Example

```bash
curl -X PUT "http://localhost:8080/toy/1" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "Rubber Bone",
    "type": "chew toy",
    "color": "blue"
  }'
```

### Response Example

**Success (200 OK):**
```json
{
  "id": 1,
  "name": "Rubber Bone",
  "type": "chew toy",
  "color": "blue",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:45:00Z"
}
```

### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Toy updated successfully |
| `400` | Bad request - Invalid or missing required fields |
| `404` | Toy not found |
| `422` | Unprocessable entity - Validation error |
| `500` | Internal server error |
| `501` | Not implemented |

---

## PATCH /toy/{id}

Partially update an existing toy record (only specified fields).

### Description

Updates only the fields provided in the request body. Fields not included will retain their current values.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the toy |
| `name` | body | string | No | The name of the toy |
| `type` | body | string | No | The type/category of toy |
| `color` | body | string | No | The color of the toy |

### Request Example

```bash
curl -X PATCH "http://localhost:8080/toy/1" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "color": "green"
  }'
```

### Response Example

**Success (200 OK):**
```json
{
  "id": 1,
  "name": "Squeaky Ball",
  "type": "ball",
  "color": "green",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T16:20:00Z"
}
```

### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Toy updated successfully |
| `400` | Bad request - Invalid field values |
| `404` | Toy not found |
| `422` | Unprocessable entity - Validation error |
| `500` | Internal server error |
| `501` | Not implemented |

---

## DELETE /toy/{id}

Delete a toy by its unique identifier.

### Description

Permanently removes a toy record from the system. This action cannot be undone.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the toy to delete |

### Request Example

```bash
curl -X DELETE "http://localhost:8080/toy/1" \
  -H "Accept: application/json"
```

### Response Example

**Success (204 No Content):**
```
(empty response body)
```

**Alternative Success (200 OK):**
```json
{
  "message": "Toy deleted successfully",
  "id": 1
}
```

### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Toy deleted successfully (with response body) |
| `204` | Toy deleted successfully (no content) |
| `404` | Toy not found |
| `500` | Internal server error |
| `501` | Not implemented |

---

## Related Documentation

- [Person API Endpoints](person-endpoints.md) - CRUD operations for Person entities
- [Pet API Endpoints](pet-endpoints.md) - CRUD operations for Pet entities
- [Utility Endpoints](utility-endpoints.md) - Testing and maintenance endpoints
- [Authentication](authentication.md) - API authentication details
- [API Overview](README.md) - General API information