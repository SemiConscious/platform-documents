# Person API Endpoints

Complete documentation for Person entity CRUD operations in the Sapien API.

## Overview

The Person API provides full CRUD (Create, Read, Update, Delete) operations for managing person records. All endpoints follow RESTful conventions and return JSON responses.

**Base URL:** `/person`

## Endpoints

### GET /person/{id}

Retrieve a person by their unique identifier.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the person |

#### Request Example

```bash
curl -X GET \
  'http://localhost:8080/person/1' \
  -H 'Accept: application/json'
```

#### Response Example

**Status: 200 OK**

```json
{
  "id": 1,
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "age": 30,
  "createdAt": "2024-01-15T10:30:00+00:00",
  "updatedAt": "2024-01-15T10:30:00+00:00"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Person retrieved successfully |
| `404` | Person not found |
| `500` | Internal server error |

---

### POST /person

Create a new person record.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `firstName` | body | string | Yes | The person's first name |
| `lastName` | body | string | Yes | The person's last name |
| `email` | body | string | Yes | The person's email address |
| `age` | body | integer | No | The person's age |

#### Request Example

```bash
curl -X POST \
  'http://localhost:8080/person' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane.smith@example.com",
    "age": 28
  }'
```

#### Response Example

**Status: 201 Created**

```json
{
  "id": 2,
  "firstName": "Jane",
  "lastName": "Smith",
  "email": "jane.smith@example.com",
  "age": 28,
  "createdAt": "2024-01-15T11:00:00+00:00",
  "updatedAt": "2024-01-15T11:00:00+00:00"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `201` | Person created successfully |
| `400` | Invalid request body or validation error |
| `422` | Unprocessable entity (schema validation failed) |
| `500` | Internal server error |

---

### PUT /person/{id}

Fully update an existing person record. This operation replaces all fields with the provided values.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the person |
| `firstName` | body | string | Yes | The person's first name |
| `lastName` | body | string | Yes | The person's last name |
| `email` | body | string | Yes | The person's email address |
| `age` | body | integer | No | The person's age |

#### Request Example

```bash
curl -X PUT \
  'http://localhost:8080/person/1' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "firstName": "John",
    "lastName": "Updated",
    "email": "john.updated@example.com",
    "age": 31
  }'
```

#### Response Example

**Status: 200 OK**

```json
{
  "id": 1,
  "firstName": "John",
  "lastName": "Updated",
  "email": "john.updated@example.com",
  "age": 31,
  "createdAt": "2024-01-15T10:30:00+00:00",
  "updatedAt": "2024-01-15T12:00:00+00:00"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Person updated successfully |
| `400` | Invalid request body or validation error |
| `404` | Person not found |
| `422` | Unprocessable entity (schema validation failed) |
| `500` | Internal server error |

---

### PATCH /person/{id}

Partially update an existing person record. Only provided (non-null) fields will be updated; omitted fields retain their current values.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the person |
| `firstName` | body | string | No | The person's first name |
| `lastName` | body | string | No | The person's last name |
| `email` | body | string | No | The person's email address |
| `age` | body | integer | No | The person's age |

#### Request Example

```bash
curl -X PATCH \
  'http://localhost:8080/person/1' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "age": 32
  }'
```

#### Response Example

**Status: 200 OK**

```json
{
  "id": 1,
  "firstName": "John",
  "lastName": "Updated",
  "email": "john.updated@example.com",
  "age": 32,
  "createdAt": "2024-01-15T10:30:00+00:00",
  "updatedAt": "2024-01-15T13:00:00+00:00"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Person partially updated successfully |
| `400` | Invalid request body or validation error |
| `404` | Person not found |
| `422` | Unprocessable entity (schema validation failed) |
| `500` | Internal server error |

---

### DELETE /person/{id}

Delete a person by their unique identifier.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the person |

#### Request Example

```bash
curl -X DELETE \
  'http://localhost:8080/person/1' \
  -H 'Accept: application/json'
```

#### Response Example

**Status: 204 No Content**

```
(empty response body)
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `204` | Person deleted successfully |
| `404` | Person not found |
| `500` | Internal server error |

---

### DELETE /all

Delete all person records from the database. This operation uses foreign-key cascade, meaning all related records (pets, toys, etc.) will also be deleted.

> ⚠️ **Warning:** This is a destructive operation that cannot be undone. Use with caution.

#### Parameters

This endpoint accepts no parameters.

#### Request Example

```bash
curl -X DELETE \
  'http://localhost:8080/all' \
  -H 'Accept: application/json'
```

#### Response Example

**Status: 204 No Content**

```
(empty response body)
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `204` | All records deleted successfully |
| `500` | Internal server error |

---

## Related Documentation

- [Pet API Endpoints](pet-endpoints.md) - CRUD operations for pets
- [Toy API Endpoints](toy-endpoints.md) - CRUD operations for toys
- [Utility Endpoints](utility-endpoints.md) - Testing and utility endpoints
- [Authentication](authentication.md) - API authentication details