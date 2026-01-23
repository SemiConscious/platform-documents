# nbtelemetry API Overview

## Introduction

The nbtelemetry API provides comprehensive telemetry services for transcription and call analysis. It integrates with multiple Natural Language Engine (NLE) providers including IBM Watson, Google Cloud Speech, and VoiceBase to process and analyze call recordings.

### Key Capabilities

- **Call Transcription**: Automated speech-to-text conversion using multiple NLE providers
- **Talk Time Analysis**: Detailed breakdown of conversation participants and speaking duration
- **Sentiment Analysis**: Emotional tone detection throughout calls
- **Recording Archive**: Secure storage and retrieval of call recordings
- **User & Organization Management**: Hierarchical access control and configuration

## Base URL

```
https://api.natterbox.com
```

## Authentication

The nbtelemetry API uses OAuth2 password grant flow for authentication. All API requests (except authentication endpoints) require a valid access token.

### Authentication Flow

1. Obtain an access token via `POST /auth/token`
2. Include the token in the `Authorization` header for subsequent requests
3. Revoke the token via `DELETE /auth/token` when finished

```bash
# Example: Include token in requests
Authorization: Bearer <access_token>
```

For complete authentication details, see [Authentication](authentication.md).

## API Versioning

The API uses URL-based versioning. Current version: **v1**

```
/v1/organisation/{orgid}/...
```

## Endpoint Categories

| Category | Description | Endpoints | Documentation |
|----------|-------------|-----------|---------------|
| **Authentication** | Token management and session control | 2 | [authentication.md](authentication.md) |
| **Users & Organizations** | User management, groups, and availability | 8 | [users-and-organizations.md](users-and-organizations.md) |
| **Call Analytics** | Transcription, talk time, and recording analysis | 6 | [call-analytics.md](call-analytics.md) |
| **Configuration** | Dial plans, SIP devices, and policies | 3 | [configuration.md](configuration.md) |

## Endpoint Index

### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/token` | Authenticate and obtain access token |
| `DELETE` | `/auth/token` | Revoke current session |

### User & Organization Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/user/me` | Get current user information |
| `GET` | `/v1/organisation/{orgid}/user` | List all users in organization |
| `GET` | `/v1/organisation/{orgid}/user/{userid}` | Get specific user details |
| `PATCH` | `/v1/organisation/{orgid}/user/{userid}` | Update user availability state |
| `GET` | `/v1/organisation/{orgid}/user-group` | List all user groups |
| `GET` | `/v1/organisation/{orgid}/user-group/{groupid}` | Get specific user group |
| `GET` | `/v1/organisation/{orgid}/availability/profile` | List availability profiles |
| `GET` | `/v1/organisation/{orgid}/availability/profile/{profileId}/state` | Get profile states |

### Call Analytics Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/organisation/{orgid}/call` | List all calls |
| `GET` | `/v1/organisation/{orgid}/log/call` | Get call logs with filtering |
| `GET` | `/v1/organisation/{orgid}/archive/recording/{uuid}` | Download recording file |
| `GET` | `/v1/organisation/{orgid}/archive/recording/{uuid}/analytics` | Get analytics metadata |
| `GET` | `/v1/organisation/{orgid}/archive/recording/{uuid}/analytics/transcription` | Get transcription data |
| `GET` | `/v1/organisation/{orgid}/archive/recording/{uuid}/analytics/talkTime` | Get talk time analysis |

### Configuration Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/organisation/{orgid}/dial-plan/policy` | List dial plan policies |
| `GET` | `/v1/organisation/{orgid}/sip-device` | List SIP devices |

## Common Request Patterns

### Path Parameters

Most endpoints require organizational context:

```
/v1/organisation/{orgid}/...
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `orgid` | integer | Organization identifier |
| `userid` | integer | User identifier |
| `uuid` | string | Recording unique identifier |
| `groupid` | integer | User group identifier |
| `profileId` | integer | Availability profile identifier |

### Query Parameters

List endpoints support common filtering parameters:

```bash
GET /v1/organisation/{orgid}/log/call?startDate=2024-01-01&endDate=2024-01-31&limit=100
```

## Response Format

All responses are returned in JSON format with consistent structure.

### Successful Response

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Collection Response

```json
{
  "data": [ ... ],
  "meta": {
    "total": 150,
    "limit": 50,
    "offset": 0
  }
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information.

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Human-readable error description",
    "details": { ... }
  }
}
```

### Common Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource does not exist |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side error |

## Rate Limiting

API requests are subject to rate limiting to ensure service stability.

| Tier | Requests | Window |
|------|----------|--------|
| Standard | 1000 | Per minute |
| Analytics | 100 | Per minute |

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705312200
```

## NLE Provider Integration

The telemetry service supports multiple Natural Language Engine providers for transcription and analysis:

| Provider | Capabilities |
|----------|--------------|
| **IBM Watson** | Speech-to-text, sentiment analysis |
| **Google Cloud Speech** | High-accuracy transcription, speaker diarization |
| **VoiceBase** | Transcription, keyword spotting, analytics |

Provider selection is configured at the organization level and applied automatically during call processing.

## Legacy Endpoints

> **Note**: The following endpoint pattern is available as an alternate access method but may be deprecated in future versions:

```
GET {NATTERBOX_ARCHIVING_INDEX_URL}/{orgid}/{uuid}
```

Direct AWS API Gateway access for analytics index retrieval. We recommend using the standard `/v1/` endpoints for all new integrations.

## Getting Started

1. **Authenticate**: Obtain an access token ([Authentication Guide](authentication.md))
2. **Explore Users**: List and manage organization users ([Users Guide](users-and-organizations.md))
3. **Access Analytics**: Retrieve call recordings and analysis ([Analytics Guide](call-analytics.md))
4. **Configure**: Manage dial plans and devices ([Configuration Guide](configuration.md))

## Support

For API support and questions:
- Technical Documentation: https://docs.natterbox.com
- Support Portal: https://support.natterbox.com