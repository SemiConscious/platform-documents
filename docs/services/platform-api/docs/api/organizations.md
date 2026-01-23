# Organizations API

The Organizations API provides endpoints for managing organizations, domains, and multi-tenant operations within the platform. This includes domain mapping for routing, organization IP address management, and billing profile access.

## Overview

Organizations in the platform represent tenants with their own users, configurations, and resources. Key organizational concepts include:

- **Domain Mappings**: Associate domains with organizations for call routing and identification
- **Organization IPs**: Manage IP addresses associated with organizations for SIP traffic
- **Billing Profiles**: Access billing configuration and settings per organization

## Base URL

All endpoints are relative to the platform API base URL:

```
https://api.example.com
```

---

## Domain Mappings

Domain mappings associate domain names with organizations, enabling proper routing of calls and identification of tenants.

### Get All Domain Mappings

Retrieve all domain mappings in the system.

```
GET /domains
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| Authorization | string | Header | Yes | Bearer token or API key |

#### Request Example

```bash
curl -X GET "https://api.example.com/domains" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": [
    {
      "id": "dom_123",
      "domain": "company1.voip.example.com",
      "orgId": "org_456",
      "orgName": "Company One",
      "type": "primary",
      "status": "active",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": "dom_124",
      "domain": "company2.voip.example.com",
      "orgId": "org_789",
      "orgName": "Company Two",
      "type": "primary",
      "status": "active",
      "createdAt": "2024-01-16T14:20:00Z",
      "updatedAt": "2024-01-16T14:20:00Z"
    }
  ],
  "meta": {
    "total": 2
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions to list domains |
| 500 | Internal Server Error | Server-side error occurred |

---

### Get Domain Mapping by ID

Retrieve a specific domain mapping by its identifier.

```
GET /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| id | string | Path | Yes | Domain mapping ID |
| Authorization | string | Header | Yes | Bearer token or API key |

#### Request Example

```bash
curl -X GET "https://api.example.com/domains/dom_123" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dom_123",
    "domain": "company1.voip.example.com",
    "orgId": "org_456",
    "orgName": "Company One",
    "type": "primary",
    "status": "active",
    "sipRealm": "company1.voip.example.com",
    "registrationEnabled": true,
    "tlsEnabled": true,
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "metadata": {
      "region": "us-east",
      "cluster": "prod-1"
    }
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions to view domain |
| 404 | Not Found | Domain mapping not found |
| 500 | Internal Server Error | Server-side error occurred |

---

### Create Domain Mapping

Create a new domain mapping for an organization.

```
POST /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| id | string | Path | Yes | Domain mapping ID to create |
| Authorization | string | Header | Yes | Bearer token or API key |
| domain | string | Body | Yes | Domain name to map |
| orgId | string | Body | Yes | Organization ID to associate |
| type | string | Body | No | Domain type: `primary`, `alias` (default: `primary`) |
| sipRealm | string | Body | No | SIP realm override |
| registrationEnabled | boolean | Body | No | Enable SIP registration (default: true) |
| tlsEnabled | boolean | Body | No | Enable TLS for domain (default: false) |
| metadata | object | Body | No | Additional metadata key-value pairs |

#### Request Example

```bash
curl -X POST "https://api.example.com/domains/dom_125" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "newcompany.voip.example.com",
    "orgId": "org_999",
    "type": "primary",
    "registrationEnabled": true,
    "tlsEnabled": true,
    "metadata": {
      "region": "us-west",
      "environment": "production"
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dom_125",
    "domain": "newcompany.voip.example.com",
    "orgId": "org_999",
    "type": "primary",
    "status": "active",
    "sipRealm": "newcompany.voip.example.com",
    "registrationEnabled": true,
    "tlsEnabled": true,
    "createdAt": "2024-01-20T09:15:00Z",
    "updatedAt": "2024-01-20T09:15:00Z",
    "metadata": {
      "region": "us-west",
      "environment": "production"
    }
  },
  "message": "Domain mapping created successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid domain format or missing required fields |
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions to create domain |
| 409 | Conflict | Domain already exists |
| 422 | Unprocessable Entity | Organization ID not found |
| 500 | Internal Server Error | Server-side error occurred |

---

### Update Domain Mapping

Update an existing domain mapping.

```
PUT /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| id | string | Path | Yes | Domain mapping ID to update |
| Authorization | string | Header | Yes | Bearer token or API key |
| domain | string | Body | No | New domain name |
| orgId | string | Body | No | New organization ID |
| type | string | Body | No | Domain type: `primary`, `alias` |
| status | string | Body | No | Status: `active`, `inactive`, `suspended` |
| sipRealm | string | Body | No | SIP realm override |
| registrationEnabled | boolean | Body | No | Enable/disable SIP registration |
| tlsEnabled | boolean | Body | No | Enable/disable TLS |
| metadata | object | Body | No | Updated metadata |

#### Request Example

```bash
curl -X PUT "https://api.example.com/domains/dom_123" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "inactive",
    "tlsEnabled": false,
    "metadata": {
      "region": "us-east",
      "maintenanceMode": true
    }
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "dom_123",
    "domain": "company1.voip.example.com",
    "orgId": "org_456",
    "type": "primary",
    "status": "inactive",
    "sipRealm": "company1.voip.example.com",
    "registrationEnabled": true,
    "tlsEnabled": false,
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-20T11:45:00Z",
    "metadata": {
      "region": "us-east",
      "maintenanceMode": true
    }
  },
  "message": "Domain mapping updated successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid field values |
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions to update domain |
| 404 | Not Found | Domain mapping not found |
| 409 | Conflict | Domain name conflict with existing mapping |
| 500 | Internal Server Error | Server-side error occurred |

---

### Delete Domain Mapping

Remove a domain mapping from the system.

```
DELETE /domains/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| id | string | Path | Yes | Domain mapping ID to delete |
| Authorization | string | Header | Yes | Bearer token or API key |
| force | boolean | Query | No | Force deletion even if in use (default: false) |

#### Request Example

```bash
curl -X DELETE "https://api.example.com/domains/dom_123?force=false" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "success": true,
  "message": "Domain mapping deleted successfully",
  "data": {
    "id": "dom_123",
    "deletedAt": "2024-01-20T12:00:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions to delete domain |
| 404 | Not Found | Domain mapping not found |
| 409 | Conflict | Domain is in use and force=false |
| 500 | Internal Server Error | Server-side error occurred |

---

## Organization IPs

Manage IP addresses associated with organizations for SIP traffic authorization and routing.

### Get All Organization IPs

Retrieve all IP addresses configured for organizations.

```
GET /orgips/index
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| Authorization | string | Header | Yes | Bearer token or API key |

#### Request Example

```bash
curl -X GET "https://api.example.com/orgips/index" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": [
    {
      "id": "ip_001",
      "orgId": "org_456",
      "ipAddress": "203.0.113.10",
      "cidr": 32,
      "type": "signaling",
      "description": "Primary PBX",
      "status": "active",
      "createdAt": "2024-01-10T08:00:00Z"
    },
    {
      "id": "ip_002",
      "orgId": "org_456",
      "ipAddress": "203.0.113.0",
      "cidr": 24,
      "type": "media",
      "description": "Media subnet",
      "status": "active",
      "createdAt": "2024-01-10T08:05:00Z"
    }
  ],
  "meta": {
    "total": 2
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 500 | Internal Server Error | Server-side error occurred |

---

### Get Organization IP by ID

Retrieve a specific organization IP configuration.

```
GET /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| entity | string | Path | Yes | IP configuration ID or organization ID |
| Authorization | string | Header | Yes | Bearer token or API key |

#### Request Example

```bash
curl -X GET "https://api.example.com/orgips/ip_001" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "ip_001",
    "orgId": "org_456",
    "orgName": "Company One",
    "ipAddress": "203.0.113.10",
    "cidr": 32,
    "type": "signaling",
    "description": "Primary PBX",
    "status": "active",
    "allowedPorts": [5060, 5061],
    "protocols": ["UDP", "TCP", "TLS"],
    "createdAt": "2024-01-10T08:00:00Z",
    "updatedAt": "2024-01-10T08:00:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | IP configuration not found |
| 500 | Internal Server Error | Server-side error occurred |

---

### Create Organization IP

Add a new IP address configuration for an organization.

```
POST /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| entity | string | Path | Yes | Organization ID or IP config ID |
| Authorization | string | Header | Yes | Bearer token or API key |
| orgId | string | Body | Yes | Organization ID |
| ipAddress | string | Body | Yes | IP address (IPv4 or IPv6) |
| cidr | integer | Body | No | CIDR notation (default: 32 for IPv4, 128 for IPv6) |
| type | string | Body | No | IP type: `signaling`, `media`, `both` (default: `both`) |
| description | string | Body | No | Human-readable description |
| allowedPorts | array | Body | No | List of allowed ports |
| protocols | array | Body | No | Allowed protocols: `UDP`, `TCP`, `TLS` |

#### Request Example

```bash
curl -X POST "https://api.example.com/orgips/org_456" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "orgId": "org_456",
    "ipAddress": "203.0.113.50",
    "cidr": 32,
    "type": "signaling",
    "description": "Backup PBX Server",
    "allowedPorts": [5060, 5061],
    "protocols": ["UDP", "TCP", "TLS"]
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "ip_003",
    "orgId": "org_456",
    "ipAddress": "203.0.113.50",
    "cidr": 32,
    "type": "signaling",
    "description": "Backup PBX Server",
    "status": "active",
    "allowedPorts": [5060, 5061],
    "protocols": ["UDP", "TCP", "TLS"],
    "createdAt": "2024-01-20T14:30:00Z",
    "updatedAt": "2024-01-20T14:30:00Z"
  },
  "message": "Organization IP created successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid IP address format or parameters |
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 409 | Conflict | IP address already configured |
| 422 | Unprocessable Entity | Organization not found |
| 500 | Internal Server Error | Server-side error occurred |

---

### Update Organization IP

Update an existing organization IP configuration.

```
PUT /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| entity | string | Path | Yes | IP configuration ID |
| Authorization | string | Header | Yes | Bearer token or API key |
| ipAddress | string | Body | No | Updated IP address |
| cidr | integer | Body | No | Updated CIDR notation |
| type | string | Body | No | Updated IP type |
| description | string | Body | No | Updated description |
| status | string | Body | No | Status: `active`, `inactive` |
| allowedPorts | array | Body | No | Updated allowed ports |
| protocols | array | Body | No | Updated protocols |

#### Request Example

```bash
curl -X PUT "https://api.example.com/orgips/ip_003" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Primary PBX Server (promoted)",
    "status": "active",
    "protocols": ["UDP", "TCP", "TLS", "WSS"]
  }'
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "id": "ip_003",
    "orgId": "org_456",
    "ipAddress": "203.0.113.50",
    "cidr": 32,
    "type": "signaling",
    "description": "Primary PBX Server (promoted)",
    "status": "active",
    "allowedPorts": [5060, 5061],
    "protocols": ["UDP", "TCP", "TLS", "WSS"],
    "createdAt": "2024-01-20T14:30:00Z",
    "updatedAt": "2024-01-20T15:00:00Z"
  },
  "message": "Organization IP updated successfully"
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | IP configuration not found |
| 409 | Conflict | IP address conflict |
| 500 | Internal Server Error | Server-side error occurred |

---

### Delete Organization IP

Remove an IP address configuration from an organization.

```
DELETE /orgips/:entity
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| entity | string | Path | Yes | IP configuration ID |
| Authorization | string | Header | Yes | Bearer token or API key |

#### Request Example

```bash
curl -X DELETE "https://api.example.com/orgips/ip_003" \
  -H "Authorization: Bearer {token}"
```

#### Response Example

```json
{
  "success": true,
  "message": "Organization IP deleted successfully",
  "data": {
    "id": "ip_003",
    "deletedAt": "2024-01-20T16:00:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | IP configuration not found |
| 409 | Conflict | IP is actively in use |
| 500 | Internal Server Error | Server-side error occurred |

---

## Billing Profiles

Access billing profile information for organizations.

### Get Billing Profile (Authenticated Organization)

Retrieve the billing profile for the currently authenticated organization.

```
GET /billingprofile
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| Authorization | string | Header | Yes | Bearer token or API key |

#### Request Example

```bash
curl -X GET "https://api.example.com/billingprofile" \
  -H "Authorization: Bearer {token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "orgId": "org_456",
    "orgName": "Company One",
    "billingPlan": "enterprise",
    "billingCycle": "monthly",
    "currency": "USD",
    "paymentMethod": "invoice",
    "billingContact": {
      "name": "John Smith",
      "email": "billing@company1.com",
      "phone": "+1-555-123-4567"
    },
    "billingAddress": {
      "street": "123 Business Ave",
      "city": "New York",
      "state": "NY",
      "postalCode": "10001",
      "country": "US"
    },
    "rateCard": {
      "id": "rc_standard",
      "name": "Standard Enterprise Rates"
    },
    "creditLimit": 10000.00,
    "currentBalance": 2500.00,
    "status": "active",
    "nextBillingDate": "2024-02-01T00:00:00Z",
    "createdAt": "2023-06-15T00:00:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Billing profile not configured |
| 500 | Internal Server Error | Server-side error occurred |

---

### Get Billing Profile by Organization ID

Retrieve the billing profile for a specific organization (admin access).

```
GET /billingprofile/:id
```

#### Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| id | string | Path | Yes | Organization ID |
| Authorization | string | Header | Yes | Bearer token or API key (admin) |

#### Request Example

```bash
curl -X GET "https://api.example.com/billingprofile/org_789" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Accept: application/json"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "orgId": "org_789",
    "orgName": "Company Two",
    "billingPlan": "professional",
    "billingCycle": "annual",
    "currency": "EUR",
    "paymentMethod": "credit_card",
    "billingContact": {
      "name": "Jane Doe",
      "email": "finance@company2.com",
      "phone": "+44-20-1234-5678"
    },
    "billingAddress": {
      "street": "456 Corporate Blvd",
      "city": "London",
      "postalCode": "EC1A 1BB",
      "country": "GB"
    },
    "rateCard": {
      "id": "rc_eu_pro",
      "name": "EU Professional Rates"
    },
    "creditLimit": 5000.00,
    "currentBalance": 750.00,
    "status": "active",
    "nextBillingDate": "2025-01-01T00:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

#### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Admin access required |
| 404 | Not Found | Organization or billing profile not found |
| 500 | Internal Server Error | Server-side error occurred |

---

## Related Documentation

- [Authentication](authentication.md) - API authentication methods
- [Users and Groups](users-and-groups.md) - User management within organizations
- [Billing](billing.md) - Detailed billing and invoicing operations
- [Telephony](telephony.md) - SIP trunk and telephony configuration