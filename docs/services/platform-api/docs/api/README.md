# Platform API Reference

## Overview

The Platform API is the core hub for the telecommunications and VoIP platform, providing centralized access to all platform resources. This RESTful API enables management of users, organizations, billing, dial plans, telephony resources, and more.

**Base URL:** `https://api.platform.example.com/v1`

**Total Endpoints:** 150

---

## Authentication

The Platform API supports multiple authentication methods depending on the use case.

### Authentication Methods

| Method | Use Case | Header/Parameter |
|--------|----------|------------------|
| **Bearer Token** | Standard API access | `Authorization: Bearer <token>` |
| **Temporary Auth** | Short-lived sessions | `POST /tempauth` |
| **Two-Factor Auth** | Enhanced security | `/auth/twofactor/*` endpoints |
| **Salesforce SSO** | Salesforce integration | `/auth/salesforce` endpoints |
| **Service Auth** | Service-to-service | `POST /auth/:entity` |

### Obtaining a Token

```bash
curl -X GET "https://api.platform.example.com/v1/auth/user" \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "your-password"}'
```

### Token Lifecycle

- **Create Token:** `GET /auth/:entity` or `POST /auth/:entity`
- **Temporary Token:** `POST /tempauth`
- **Destroy Token (Logout):** `DELETE /auth`

For complete authentication details, see [Authentication Documentation](docs/api/authentication.md).

---

## API Documentation Index

| Category | Description | Documentation |
|----------|-------------|---------------|
| **Authentication** | Token management, 2FA, SSO, and session handling | [authentication.md](docs/api/authentication.md) |
| **Users & Groups** | User management, permissions, foreign IDs, and client directories | [users-and-groups.md](docs/api/users-and-groups.md) |
| **Organizations** | Organization settings, IPs, domains, and client access | [organizations.md](docs/api/organizations.md) |
| **Telephony** | SIP trunks, devices, numbers, and gateway management | [telephony.md](docs/api/telephony.md) |
| **Dial Plan** | Routing policies, templates, and call flow configuration | [dialplan.md](docs/api/dialplan.md) |
| **Billing** | Billing profiles, CDR processing, and financial data | [billing.md](docs/api/billing.md) |
| **Messaging** | SMS, email, voicemail, and notification services | [messaging.md](docs/api/messaging.md) |
| **System** | Logs, events, archiving, files, and administrative functions | [system.md](docs/api/system.md) |

---

## Endpoint Categories

### Authentication & Authorization
Manage authentication tokens, two-factor authentication, and single sign-on integrations.
- Token creation and destruction
- Two-factor authentication setup (QR codes, secrets)
- Salesforce SSO integration
- Temporary authentication tokens

### Users & Groups
Comprehensive user and group management including permissions and external ID mapping.
- User foreign ID management
- Client directory operations
- Permission queries
- Subscription management (BLF)

### Organizations
Organization-level configuration including network settings and access controls.
- Domain mappings
- Organization IP management
- Client access controls
- Billing profile retrieval

### Telephony
Core telephony resource management for VoIP infrastructure.
- SIP trunk configuration and IP management
- Device provisioning (create, update, reboot, SIP NOTIFY)
- Number activation, search, and channel management
- Mobile/SIM management
- Gateway ping status monitoring

### Dial Plan
Call routing and policy management for directing telecommunications traffic.
- Dial plan templates and policies
- Policy groups and dependencies
- Historical/archived dial plans
- Policy search functionality

### Billing
Financial and billing-related operations.
- Billing profile queries
- CDR (Call Detail Record) processing
- Profit checking for numbers

### Messaging
Communication services beyond voice calls.
- SMS sending and logging
- Email template delivery
- Voicemail management
- Voicemail drop files

### System Administration
Platform maintenance, monitoring, and data management.
- Event logging and retrieval
- Call log management
- File management (sound files, voicemail drops)
- Archiving (provisioning, policies, legal holds, purging)
- Data connector configuration
- Sequence management
- QR code generation
- Bespoke data (queue monitoring, notifier)

---

## Common Patterns

### Request Format

All requests should include appropriate headers:

```bash
curl -X GET "https://api.platform.example.com/v1/endpoint" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json"
```

### Response Format

Successful responses return JSON (or XML for certain legacy endpoints):

```json
{
  "status": "success",
  "data": {
    // Response payload
  }
}
```

### URL Parameter Patterns

The API uses consistent URL patterns:

| Pattern | Example | Description |
|---------|---------|-------------|
| `/:id` | `/devices/123` | Single resource by ID |
| `/:entity` | `/auth/user` | Resource type specification |
| `/:orgId/:resourceId` | `/eventlog/100/500` | Scoped resources |
| `/search` | `/numbers/search` | Search operations (typically POST) |
| `/index` | `/orgips/index` | List all resources |

### HTTP Methods

| Method | Usage |
|--------|-------|
| `GET` | Retrieve resources |
| `POST` | Create resources or perform searches/updates |
| `PUT` | Create or fully update resources |
| `DELETE` | Remove resources |

> **Note:** Some endpoints accept multiple methods (e.g., both `PUT` and `POST` for creation/updates).

---

## Error Handling

### Error Response Format

Errors are returned in XML format via the errors controller:

```xml
<error>
  <code>401</code>
  <message>Authentication required</message>
</error>
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required or invalid |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource does not exist |
| `500` | Internal Server Error | Server-side error |

### Error Endpoint

The API provides a generic error handler at:
- `ANY /errors` - Returns standardized XML error responses

---

## Rate Limiting

API requests are subject to rate limiting to ensure platform stability. Rate limit details are returned in response headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

When rate limited, the API returns a `429 Too Many Requests` status.

---

## Pagination

For endpoints returning lists, pagination is typically supported via query parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `limit` | Maximum results to return | 50 |
| `offset` | Number of results to skip | 0 |
| `page` | Page number (alternative to offset) | 1 |

---

## Versioning

The API uses URL-based versioning. The current version is included in the base URL path. Breaking changes will result in a new version.

---

## Additional Resources

- **API Documentation Root:** `GET /documentation` - Returns API documentation
- **QR Code Generator:** `GET /qrcode/:data` - Generate QR codes for any string data
- **Health Monitoring:** `GET /sipgwping/:entity` - Check SIP gateway status

---

## Support

For API support, integration assistance, or to report issues, contact the platform support team.