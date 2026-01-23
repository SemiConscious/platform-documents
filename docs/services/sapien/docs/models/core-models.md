# Core Entity Models

This document covers the primary business entities in the Sapien system, including Person, Pet, and Toy models along with their relationships.

## Overview

The core entity models represent the fundamental business objects within the Sapien application. These entities form the foundation of the domain model and are used throughout the system for managing people and their associated data.

> **Related Documentation:**
> - [Authentication Models](./authentication-models.md) - User sessions and OAuth tokens
> - [Infrastructure Models](./infrastructure-models.md) - System configuration and logging

## Entity Relationship Diagram

```
┌─────────────────┐
│     Person      │
├─────────────────┤
│ id (PK)         │
│ name            │
│ email           │
│ phoneNumber     │
│ dob             │
└─────────────────┘
```

> **Note:** Based on the provided model definitions, only the `Person` entity is explicitly defined in the codebase. The Pet and Toy entities mentioned in the topic description are not present in the current model set. This documentation focuses on the available Person entity.

---

## Person

The `Person` entity represents an individual with contact information in the system. This is a core domain entity used for storing personal details including contact methods and demographic information.

### Purpose

- Store and manage personal information for individuals
- Maintain contact details (email, phone) for communication
- Track demographic data such as date of birth
- Serve as a foundational entity for person-related business logic

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes (auto-generated) | Primary key identifier, auto-incremented |
| `name` | string | Yes | Person's full name |
| `email` | string | Yes | Person's email address for contact |
| `phoneNumber` | string | Yes | Person's phone number in E.164 international format |
| `dob` | DateTime | Yes | Person's date of birth |

### Validation Rules

| Field | Validation Rules |
|-------|------------------|
| `id` | Auto-generated, positive integer, unique |
| `name` | Non-empty string, typically 1-255 characters |
| `email` | Valid email format (RFC 5322 compliant) |
| `phoneNumber` | E.164 format (e.g., `+14155552671`), max 15 digits |
| `dob` | Valid date, must be in the past |

### E.164 Phone Number Format

The `phoneNumber` field follows the E.164 international standard:
- Starts with `+` followed by country code
- Maximum 15 digits (excluding the `+`)
- No spaces, dashes, or other formatting characters

**Examples:**
- US: `+14155552671`
- UK: `+442071234567`
- Australia: `+61412345678`

### Example JSON

```json
{
  "id": 12345,
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "phoneNumber": "+14155552671",
  "dob": "1985-03-15T00:00:00+00:00"
}
```

### Complete Example with All Fields

```json
{
  "id": 67890,
  "name": "John Doe",
  "email": "john.doe@company.org",
  "phoneNumber": "+442079876543",
  "dob": "1990-07-22T00:00:00+00:00"
}
```

### Collection Example

```json
{
  "persons": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice.johnson@example.com",
      "phoneNumber": "+14085551234",
      "dob": "1988-11-30T00:00:00+00:00"
    },
    {
      "id": 2,
      "name": "Bob Williams",
      "email": "bob.williams@example.com",
      "phoneNumber": "+61298765432",
      "dob": "1975-05-12T00:00:00+00:00"
    },
    {
      "id": 3,
      "name": "Carol Martinez",
      "email": "carol.martinez@example.com",
      "phoneNumber": "+33142567890",
      "dob": "1992-02-28T00:00:00+00:00"
    }
  ],
  "total": 3
}
```

### Relationships

The Person entity may have relationships with:

| Related Entity | Relationship Type | Description |
|----------------|-------------------|-------------|
| User | One-to-One | A Person may be associated with a system User account for authentication |
| EventLog | One-to-Many | Actions performed by or on a Person may be logged in EventLog |

### Common Use Cases

#### 1. Creating a New Person

```json
{
  "name": "New Contact",
  "email": "new.contact@example.com",
  "phoneNumber": "+15105559876",
  "dob": "1995-08-10T00:00:00+00:00"
}
```

#### 2. Updating Contact Information

```json
{
  "id": 12345,
  "email": "updated.email@newdomain.com",
  "phoneNumber": "+15105551111"
}
```

#### 3. Searching by Email

```
GET /api/persons?email=jane.smith@example.com
```

#### 4. Age Verification Pattern

The `dob` field enables age-related business logic:

```php
$person = $personRepository->find($id);
$age = $person->getDob()->diff(new DateTime())->y;

if ($age < 18) {
    throw new UnderageException();
}
```

### Database Mapping

| Entity Field | Database Column | Column Type |
|--------------|-----------------|-------------|
| `id` | `id` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `name` | `name` | `VARCHAR(255) NOT NULL` |
| `email` | `email` | `VARCHAR(255) NOT NULL` |
| `phoneNumber` | `phone_number` | `VARCHAR(20) NOT NULL` |
| `dob` | `dob` | `DATETIME NOT NULL` |

---

## Usage Patterns

### Repository Access

```php
// Find person by ID
$person = $personRepository->find(12345);

// Find by email
$person = $personRepository->findOneBy(['email' => 'jane.smith@example.com']);

// Find all persons
$persons = $personRepository->findAll();
```

### Creating a Person

```php
$person = new Person();
$person->setName('Jane Smith');
$person->setEmail('jane.smith@example.com');
$person->setPhoneNumber('+14155552671');
$person->setDob(new DateTime('1985-03-15'));

$entityManager->persist($person);
$entityManager->flush();
```

### API Response Format

When serialized via the API, a Person entity returns:

```json
{
  "data": {
    "type": "person",
    "id": "12345",
    "attributes": {
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "phoneNumber": "+14155552671",
      "dob": "1985-03-15T00:00:00+00:00"
    }
  }
}
```

---

## Error Handling

When working with Person entities, the following errors may occur:

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `PERSON_NOT_FOUND` | 404 | Person with specified ID does not exist |
| `INVALID_EMAIL` | 400 | Email address format is invalid |
| `INVALID_PHONE` | 400 | Phone number is not in E.164 format |
| `INVALID_DOB` | 400 | Date of birth is invalid or in the future |
| `DUPLICATE_EMAIL` | 409 | Email address already exists in system |