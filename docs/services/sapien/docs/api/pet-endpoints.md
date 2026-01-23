# Pet API Endpoints

Complete documentation for Pet entity CRUD operations.

> **Note:** Pet endpoints are currently defined but not yet implemented. All endpoints will return a `501 Not Implemented` response until the implementation is complete.

## Overview

The Pet API provides standard CRUD (Create, Read, Update, Delete) operations for managing pet records. Pets can be associated with Person records, allowing you to track pet ownership.

## Base URL

All Pet endpoints use the base path: `/pet`

---

## Endpoints

### GET /pet/{id}

Retrieve a pet by its unique identifier.

#### Description

Fetches a single pet record from the database based on the provided ID.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the pet |

#### Request Example

```bash
curl -X GET \
  'http://localhost:8080/pet/1' \
  -H 'Accept: application/json'
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": 1,
  "name": "Buddy",
  "species": "dog",
  "breed": "Golden Retriever",
  "age": 3,
  "owner_id": 1
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Pet found and returned successfully |
| `404` | Pet with the specified ID not found |
| `501` | Not implemented (current status) |

---

### POST /pet

Create a new pet record.

#### Description

Creates a new pet entry in the database. The pet can optionally be associated with an existing person (owner).

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `name` | body | string | Yes | The pet's name |
| `species` | body | string | Yes | The species of the pet (e.g., "dog", "cat") |
| `breed` | body | string | No | The breed of the pet |
| `age` | body | integer | No | The pet's age in years |
| `owner_id` | body | integer | No | The ID of the person who owns this pet |

#### Request Example

```bash
curl -X POST \
  'http://localhost:8080/pet' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "name": "Buddy",
    "species": "dog",
    "breed": "Golden Retriever",
    "age": 3,
    "owner_id": 1
  }'
```

#### Response Example

**Success (201 Created):**
```json
{
  "id": 1,
  "name": "Buddy",
  "species": "dog",
  "breed": "Golden Retriever",
  "age": 3,
  "owner_id": 1
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `201` | Pet created successfully |
| `400` | Invalid request body or validation error |
| `422` | Unprocessable entity (e.g., invalid owner_id reference) |
| `501` | Not implemented (current status) |

---

### PUT /pet/{id}

Fully update an existing pet record (replace all fields).

#### Description

Replaces all fields of an existing pet record with the provided values. All required fields must be included in the request body.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the pet to update |
| `name` | body | string | Yes | The pet's name |
| `species` | body | string | Yes | The species of the pet |
| `breed` | body | string | No | The breed of the pet |
| `age` | body | integer | No | The pet's age in years |
| `owner_id` | body | integer | No | The ID of the person who owns this pet |

#### Request Example

```bash
curl -X PUT \
  'http://localhost:8080/pet/1' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "name": "Buddy Jr.",
    "species": "dog",
    "breed": "Golden Retriever",
    "age": 4,
    "owner_id": 2
  }'
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": 1,
  "name": "Buddy Jr.",
  "species": "dog",
  "breed": "Golden Retriever",
  "age": 4,
  "owner_id": 2
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Pet updated successfully |
| `400` | Invalid request body or validation error |
| `404` | Pet with the specified ID not found |
| `422` | Unprocessable entity |
| `501` | Not implemented (current status) |

---

### PATCH /pet/{id}

Partially update an existing pet record.

#### Description

Updates only the specified fields of an existing pet record. Fields not included in the request body remain unchanged.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the pet to update |
| `name` | body | string | No | The pet's name |
| `species` | body | string | No | The species of the pet |
| `breed` | body | string | No | The breed of the pet |
| `age` | body | integer | No | The pet's age in years |
| `owner_id` | body | integer | No | The ID of the person who owns this pet |

#### Request Example

```bash
curl -X PATCH \
  'http://localhost:8080/pet/1' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "age": 4
  }'
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": 1,
  "name": "Buddy",
  "species": "dog",
  "breed": "Golden Retriever",
  "age": 4,
  "owner_id": 1
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Pet updated successfully |
| `400` | Invalid request body or validation error |
| `404` | Pet with the specified ID not found |
| `422` | Unprocessable entity |
| `501` | Not implemented (current status) |

---

### DELETE /pet/{id}

Delete a pet by its unique identifier.

#### Description

Permanently removes a pet record from the database.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `id` | path | integer | Yes | The unique identifier of the pet to delete |

#### Request Example

```bash
curl -X DELETE \
  'http://localhost:8080/pet/1' \
  -H 'Accept: application/json'
```

#### Response Example

**Success (204 No Content):**
```
(empty response body)
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `204` | Pet deleted successfully |
| `404` | Pet with the specified ID not found |
| `501` | Not implemented (current status) |

---

## Related Documentation

- [Person API Endpoints](person-endpoints.md) - Manage person records (potential pet owners)
- [Toy API Endpoints](toy-endpoints.md) - Manage toy records (can be associated with pets)
- [API Overview](README.md) - General API information and conventions