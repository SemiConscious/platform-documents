# Dialplan API

The Dialplan API provides comprehensive management of dial plans, call routing policies, templates, and related configurations. These endpoints enable organizations to define how calls are routed, create reusable templates, manage policy rules, and track historical changes to dial plan configurations.

## Overview

Dial plans control how calls are processed and routed within the telephony platform. The API supports:

- **Templates**: Reusable dial plan configurations
- **Policies**: Rules that govern call routing behavior
- **Groups**: Logical groupings for dial plan organization
- **History/Archives**: Historical versions of dial plan configurations
- **Dependencies**: Relationships between dial plan components

## Base URL

All endpoints are relative to the Platform API base URL:

```
https://api.example.com/platform
```

## Authentication

All Dialplan API endpoints require authentication. Include your API token in the request headers:

```
Authorization: Bearer {token}
```

---

## Endpoints

### Get Dial Plan Template

Retrieves the dial plan template for the authenticated organization.

```
GET /dialplan/template
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `org_id` | integer | query | No | Organization ID (defaults to authenticated org) |
| `format` | string | query | No | Response format (`xml`, `json`) |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/template" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "template": {
    "id": "tpl_12345",
    "name": "Standard Office Template",
    "version": "2.1",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-02-20T14:45:00Z",
    "rules": [
      {
        "priority": 1,
        "pattern": "^9([0-9]{10})$",
        "action": "bridge",
        "destination": "sofia/gateway/pstn/$1"
      },
      {
        "priority": 2,
        "pattern": "^([2-8][0-9]{2})$",
        "action": "bridge",
        "destination": "user/$1@${domain}"
      }
    ],
    "variables": {
      "domain": "sip.example.com",
      "default_timeout": 30
    }
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - No template exists for organization |
| 500 | Internal Server Error |

---

### Get Dial Plan Policies

Retrieves all dial plan policies for the authenticated organization.

```
GET /dialplan/policies
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `org_id` | integer | query | No | Organization ID (defaults to authenticated org) |
| `status` | string | query | No | Filter by status (`active`, `inactive`, `draft`) |
| `limit` | integer | query | No | Maximum number of results (default: 50) |
| `offset` | integer | query | No | Pagination offset (default: 0) |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/policies?status=active&limit=25" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "total": 45,
  "limit": 25,
  "offset": 0,
  "policies": [
    {
      "id": "pol_001",
      "name": "International Calling Policy",
      "description": "Restricts international calls to authorized users",
      "status": "active",
      "priority": 100,
      "conditions": {
        "pattern": "^011[0-9]+$",
        "time_of_day": {
          "start": "08:00",
          "end": "18:00"
        },
        "user_groups": ["international_enabled"]
      },
      "actions": {
        "allow": true,
        "rate_limit": 10,
        "log": true
      },
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-02-15T11:30:00Z"
    },
    {
      "id": "pol_002",
      "name": "Emergency Services Policy",
      "description": "Always route emergency calls",
      "status": "active",
      "priority": 1,
      "conditions": {
        "pattern": "^(911|112|999)$"
      },
      "actions": {
        "allow": true,
        "gateway": "emergency_pstn",
        "bypass_restrictions": true
      },
      "created_at": "2024-01-05T08:00:00Z",
      "updated_at": "2024-01-05T08:00:00Z"
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 500 | Internal Server Error |

---

### Get Dial Plan Policy

Retrieves a specific dial plan policy.

```
GET /dialplan/policy
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `id` | string | query | Yes | Policy ID to retrieve |
| `org_id` | integer | query | No | Organization ID (defaults to authenticated org) |
| `include_history` | boolean | query | No | Include version history (default: false) |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/policy?id=pol_001&include_history=true" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "policy": {
    "id": "pol_001",
    "name": "International Calling Policy",
    "description": "Restricts international calls to authorized users",
    "status": "active",
    "priority": 100,
    "version": 3,
    "conditions": {
      "pattern": "^011[0-9]+$",
      "time_of_day": {
        "start": "08:00",
        "end": "18:00",
        "timezone": "America/New_York"
      },
      "user_groups": ["international_enabled"],
      "caller_id_required": true
    },
    "actions": {
      "allow": true,
      "rate_limit": 10,
      "max_duration": 3600,
      "log": true,
      "notify": ["billing@example.com"]
    },
    "metadata": {
      "created_by": "user_123",
      "last_modified_by": "user_456"
    },
    "created_at": "2024-01-10T09:00:00Z",
    "updated_at": "2024-02-15T11:30:00Z",
    "history": [
      {
        "version": 2,
        "changed_at": "2024-02-01T10:00:00Z",
        "changed_by": "user_456",
        "changes": ["Updated time_of_day restrictions"]
      },
      {
        "version": 1,
        "changed_at": "2024-01-10T09:00:00Z",
        "changed_by": "user_123",
        "changes": ["Initial creation"]
      }
    ]
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing required parameter `id` |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Policy does not exist |
| 500 | Internal Server Error |

---

### Create Dial Plan Policy

Creates a new dial plan policy.

```
PUT /dialplan/policy
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `name` | string | body | Yes | Policy name |
| `description` | string | body | No | Policy description |
| `status` | string | body | No | Initial status (`active`, `inactive`, `draft`). Default: `draft` |
| `priority` | integer | body | No | Execution priority (lower = higher priority). Default: 1000 |
| `conditions` | object | body | Yes | Conditions that trigger the policy |
| `conditions.pattern` | string | body | Yes | Regex pattern to match dialed numbers |
| `conditions.time_of_day` | object | body | No | Time-based restrictions |
| `conditions.user_groups` | array | body | No | User groups this policy applies to |
| `conditions.caller_id_required` | boolean | body | No | Require caller ID |
| `actions` | object | body | Yes | Actions to take when policy matches |
| `actions.allow` | boolean | body | Yes | Allow or deny the call |
| `actions.gateway` | string | body | No | Specific gateway to route through |
| `actions.rate_limit` | integer | body | No | Maximum calls per minute |
| `actions.max_duration` | integer | body | No | Maximum call duration in seconds |
| `actions.log` | boolean | body | No | Enable detailed logging |
| `org_id` | integer | body | No | Organization ID (defaults to authenticated org) |

#### Request Example

```bash
curl -X PUT "https://api.example.com/platform/dialplan/policy" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Toll-Free Routing Policy",
    "description": "Route toll-free calls through dedicated gateway",
    "status": "active",
    "priority": 50,
    "conditions": {
      "pattern": "^1(800|888|877|866|855|844|833)[0-9]{7}$",
      "caller_id_required": false
    },
    "actions": {
      "allow": true,
      "gateway": "tollfree_gateway",
      "log": true
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "message": "Policy created successfully",
  "policy": {
    "id": "pol_003",
    "name": "Toll-Free Routing Policy",
    "description": "Route toll-free calls through dedicated gateway",
    "status": "active",
    "priority": 50,
    "version": 1,
    "conditions": {
      "pattern": "^1(800|888|877|866|855|844|833)[0-9]{7}$",
      "caller_id_required": false
    },
    "actions": {
      "allow": true,
      "gateway": "tollfree_gateway",
      "log": true
    },
    "created_at": "2024-03-01T12:00:00Z",
    "updated_at": "2024-03-01T12:00:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid or missing required fields |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 409 | Conflict - Policy with same name already exists |
| 422 | Unprocessable Entity - Invalid pattern or configuration |
| 500 | Internal Server Error |

---

### Update Dial Plan Policy

Updates attributes of an existing dial plan policy.

```
POST /dialplan/policy
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `id` | string | body | Yes | Policy ID to update |
| `name` | string | body | No | Updated policy name |
| `description` | string | body | No | Updated description |
| `status` | string | body | No | Updated status |
| `priority` | integer | body | No | Updated priority |
| `conditions` | object | body | No | Updated conditions |
| `actions` | object | body | No | Updated actions |
| `org_id` | integer | body | No | Organization ID |

#### Request Example

```bash
curl -X POST "https://api.example.com/platform/dialplan/policy" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "pol_001",
    "priority": 90,
    "conditions": {
      "pattern": "^011[0-9]+$",
      "time_of_day": {
        "start": "07:00",
        "end": "20:00",
        "timezone": "America/New_York"
      },
      "user_groups": ["international_enabled", "executives"]
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "message": "Policy updated successfully",
  "policy": {
    "id": "pol_001",
    "name": "International Calling Policy",
    "description": "Restricts international calls to authorized users",
    "status": "active",
    "priority": 90,
    "version": 4,
    "conditions": {
      "pattern": "^011[0-9]+$",
      "time_of_day": {
        "start": "07:00",
        "end": "20:00",
        "timezone": "America/New_York"
      },
      "user_groups": ["international_enabled", "executives"],
      "caller_id_required": true
    },
    "actions": {
      "allow": true,
      "rate_limit": 10,
      "max_duration": 3600,
      "log": true,
      "notify": ["billing@example.com"]
    },
    "updated_at": "2024-03-01T14:30:00Z"
  }
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing required `id` field |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Policy does not exist |
| 422 | Unprocessable Entity - Invalid configuration |
| 500 | Internal Server Error |

---

### Delete Dial Plan Policy

Deletes a dial plan policy.

```
DELETE /dialplan/policy
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `id` | string | query | Yes | Policy ID to delete |
| `org_id` | integer | query | No | Organization ID |
| `force` | boolean | query | No | Force delete even if policy has dependencies (default: false) |

#### Request Example

```bash
curl -X DELETE "https://api.example.com/platform/dialplan/policy?id=pol_003" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "success": true,
  "message": "Policy deleted successfully",
  "deleted_policy_id": "pol_003"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing required `id` parameter |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Policy does not exist |
| 409 | Conflict - Policy has dependencies and `force` is not set |
| 500 | Internal Server Error |

---

### Get Dial Plan History

Retrieves archived/historical dial plan configurations.

```
GET /dialplan/history
```

> **Note**: This endpoint is also accessible via `/dialplan/historic`, `/dialplan/archive`, and `/dialplan/archived`.

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `org_id` | integer | query | No | Organization ID |
| `type` | string | query | No | Filter by type (`template`, `policy`) |
| `entity_id` | string | query | No | Filter by specific entity ID |
| `start_date` | string | query | No | Start date for history range (ISO 8601) |
| `end_date` | string | query | No | End date for history range (ISO 8601) |
| `limit` | integer | query | No | Maximum results (default: 50) |
| `offset` | integer | query | No | Pagination offset (default: 0) |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/history?type=policy&start_date=2024-01-01T00:00:00Z&limit=20" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "total": 156,
  "limit": 20,
  "offset": 0,
  "history": [
    {
      "id": "hist_001",
      "type": "policy",
      "entity_id": "pol_001",
      "entity_name": "International Calling Policy",
      "version": 3,
      "action": "update",
      "changed_by": {
        "user_id": "user_456",
        "username": "admin@example.com"
      },
      "changes": {
        "priority": {
          "old": 100,
          "new": 90
        },
        "conditions.user_groups": {
          "old": ["international_enabled"],
          "new": ["international_enabled", "executives"]
        }
      },
      "snapshot": {
        "name": "International Calling Policy",
        "priority": 90,
        "conditions": {
          "pattern": "^011[0-9]+$",
          "user_groups": ["international_enabled", "executives"]
        }
      },
      "archived_at": "2024-02-15T11:30:00Z"
    },
    {
      "id": "hist_002",
      "type": "policy",
      "entity_id": "pol_002",
      "entity_name": "After Hours Policy",
      "version": 1,
      "action": "create",
      "changed_by": {
        "user_id": "user_123",
        "username": "ops@example.com"
      },
      "changes": null,
      "snapshot": {
        "name": "After Hours Policy",
        "priority": 200,
        "conditions": {
          "pattern": ".*",
          "time_of_day": {
            "start": "18:00",
            "end": "08:00"
          }
        }
      },
      "archived_at": "2024-02-10T16:00:00Z"
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid date format |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 500 | Internal Server Error |

---

### Get Dial Plan Groups

Retrieves available groups for dial plan organization and policy assignment.

```
GET /dialplan/groups
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `org_id` | integer | query | No | Organization ID |
| `include_members` | boolean | query | No | Include group members (default: false) |
| `status` | string | query | No | Filter by status (`active`, `inactive`) |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/groups?include_members=true" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "groups": [
    {
      "id": "grp_001",
      "name": "international_enabled",
      "display_name": "International Calling Enabled",
      "description": "Users authorized for international calls",
      "status": "active",
      "member_count": 45,
      "members": [
        {
          "user_id": "usr_100",
          "username": "john.doe@example.com",
          "added_at": "2024-01-15T10:00:00Z"
        },
        {
          "user_id": "usr_101",
          "username": "jane.smith@example.com",
          "added_at": "2024-01-16T11:00:00Z"
        }
      ],
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "grp_002",
      "name": "executives",
      "display_name": "Executive Team",
      "description": "Executive level users with elevated privileges",
      "status": "active",
      "member_count": 12,
      "members": [
        {
          "user_id": "usr_050",
          "username": "ceo@example.com",
          "added_at": "2024-01-01T08:00:00Z"
        }
      ],
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "grp_003",
      "name": "restricted",
      "display_name": "Restricted Dialing",
      "description": "Users with restricted dial plan access",
      "status": "active",
      "member_count": 8,
      "members": [],
      "created_at": "2024-02-01T00:00:00Z"
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 500 | Internal Server Error |

---

### Search Dial Plan Policies

Searches dial plan policies with advanced filtering options.

```
GET /dialplan/search
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `q` | string | query | No | Search query string (searches name, description) |
| `org_id` | integer | query | No | Organization ID |
| `status` | string | query | No | Filter by status |
| `pattern` | string | query | No | Filter by matching pattern |
| `group` | string | query | No | Filter by group name |
| `priority_min` | integer | query | No | Minimum priority value |
| `priority_max` | integer | query | No | Maximum priority value |
| `created_after` | string | query | No | Created after date (ISO 8601) |
| `created_before` | string | query | No | Created before date (ISO 8601) |
| `sort` | string | query | No | Sort field (`name`, `priority`, `created_at`, `updated_at`) |
| `order` | string | query | No | Sort order (`asc`, `desc`). Default: `asc` |
| `limit` | integer | query | No | Maximum results (default: 50) |
| `offset` | integer | query | No | Pagination offset (default: 0) |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/search?q=international&status=active&sort=priority&order=asc" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "query": {
    "q": "international",
    "status": "active",
    "sort": "priority",
    "order": "asc"
  },
  "total": 3,
  "limit": 50,
  "offset": 0,
  "results": [
    {
      "id": "pol_001",
      "name": "International Calling Policy",
      "description": "Restricts international calls to authorized users",
      "status": "active",
      "priority": 90,
      "match_score": 0.95,
      "conditions": {
        "pattern": "^011[0-9]+$"
      },
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-02-15T11:30:00Z"
    },
    {
      "id": "pol_010",
      "name": "International Premium Rate Block",
      "description": "Blocks calls to international premium rate numbers",
      "status": "active",
      "priority": 95,
      "match_score": 0.88,
      "conditions": {
        "pattern": "^011(900|976)[0-9]+$"
      },
      "created_at": "2024-01-20T14:00:00Z",
      "updated_at": "2024-01-20T14:00:00Z"
    }
  ]
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid search parameters |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 500 | Internal Server Error |

---

### Get Dial Plan Dependencies

Retrieves dependencies and relationships for dial plan components.

```
GET /dialplan/dependencies
```

#### Parameters

| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| `id` | string | query | Yes | Entity ID to check dependencies for |
| `type` | string | query | Yes | Entity type (`template`, `policy`, `group`) |
| `org_id` | integer | query | No | Organization ID |
| `direction` | string | query | No | Dependency direction (`upstream`, `downstream`, `both`). Default: `both` |

#### Request Example

```bash
curl -X GET "https://api.example.com/platform/dialplan/dependencies?id=pol_001&type=policy&direction=both" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "entity": {
    "id": "pol_001",
    "type": "policy",
    "name": "International Calling Policy"
  },
  "dependencies": {
    "upstream": [
      {
        "id": "tpl_001",
        "type": "template",
        "name": "Standard Office Template",
        "relationship": "included_in"
      }
    ],
    "downstream": [
      {
        "id": "grp_001",
        "type": "group",
        "name": "international_enabled",
        "relationship": "references"
      },
      {
        "id": "grp_002",
        "type": "group",
        "name": "executives",
        "relationship": "references"
      },
      {
        "id": "gw_intl_01",
        "type": "gateway",
        "name": "International Gateway",
        "relationship": "routes_to"
      }
    ]
  },
  "dependency_count": {
    "upstream": 1,
    "downstream": 3,
    "total": 4
  },
  "can_delete": false,
  "delete_blocked_reason": "Policy is referenced by template 'Standard Office Template'"
}
```

#### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing required parameters |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Entity does not exist |
| 500 | Internal Server Error |

---

## Data Models

### Policy Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique policy identifier |
| `name` | string | Policy name |
| `description` | string | Policy description |
| `status` | string | Status: `active`, `inactive`, `draft` |
| `priority` | integer | Execution priority (lower = higher priority) |
| `version` | integer | Version number |
| `conditions` | object | Matching conditions |
| `actions` | object | Actions to execute |
| `created_at` | string | Creation timestamp (ISO 8601) |
| `updated_at` | string | Last update timestamp (ISO 8601) |

### Conditions Object

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | string | Regex pattern to match dialed numbers |
| `time_of_day` | object | Time-based restrictions |
| `time_of_day.start` | string | Start time (HH:MM) |
| `time_of_day.end` | string | End time (HH:MM) |
| `time_of_day.timezone` | string | Timezone identifier |
| `user_groups` | array | User groups this policy applies to |
| `caller_id_required` | boolean | Whether caller ID is required |

### Actions Object

| Field | Type | Description |
|-------|------|-------------|
| `allow` | boolean | Whether to allow the call |
| `gateway` | string | Gateway to route through |
| `rate_limit` | integer | Maximum calls per minute |
| `max_duration` | integer | Maximum duration in seconds |
| `log` | boolean | Enable detailed logging |
| `notify` | array | Email addresses to notify |
| `bypass_restrictions` | boolean | Bypass other restrictions |

---

## Common Patterns

### Pattern Examples

| Pattern | Description |
|---------|-------------|
| `^9([0-9]{10})$` | External calls (dial 9 + 10 digits) |
| `^([2-8][0-9]{2})$` | Internal extensions (3 digits starting with 2-8) |
| `^011[0-9]+$` | International calls |
| `^1(800\|888\|877)[0-9]{7}$` | Toll-free numbers |
| `^(911\|112\|999)$` | Emergency services |

---

## Related Documentation

- [Authentication](authentication.md) - API authentication
- [Users and Groups](users-and-groups.md) - User and group management
- [Telephony](telephony.md) - SIP trunks and telephony resources
- [Organizations](organizations.md) - Organization management