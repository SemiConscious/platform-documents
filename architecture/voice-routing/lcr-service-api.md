# LCR Service API Reference

## Overview

The LCR (Least Cost Routing) Service provides intelligent route selection for outbound calls, optimizing for cost, quality, and availability across multiple carrier gateways.

**Service URL:** `https://lcr-service.internal/api/v1`

**Authentication:** Internal service JWT token

---

## Endpoints

### POST /lcr/route

Get optimal routes for a destination number.

**Request Headers:**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Request-ID: <unique_request_id>
X-Organization-ID: <org_id>
```

**Request Body:**
```json
{
    "destination": "+442012345678",
    "organizationId": 12345,
    "userId": 67890,
    "callType": "voice",
    "options": {
        "maxRoutes": 5,
        "includeRates": true,
        "preferredCarriers": ["carrier_a", "carrier_b"],
        "excludeCarriers": ["carrier_c"],
        "minQualityScore": 70
    }
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `destination` | string | Yes | E.164 format destination number |
| `organizationId` | integer | Yes | Organization ID |
| `userId` | integer | No | User ID for user-specific routing |
| `callType` | enum | No | `voice` or `fax`. Default: `voice` |
| `options.maxRoutes` | integer | No | Maximum routes to return (1-10). Default: 5 |
| `options.includeRates` | boolean | No | Include rate information. Default: false |
| `options.preferredCarriers` | string[] | No | Prioritize specific carriers |
| `options.excludeCarriers` | string[] | No | Exclude specific carriers |
| `options.minQualityScore` | integer | No | Minimum quality score (0-100) |

**Response (200 OK):**
```json
{
    "success": true,
    "destination": "+442012345678",
    "normalizedDestination": "+442012345678",
    "countryCode": "44",
    "countryName": "United Kingdom",
    "numberType": "geographic",
    "routes": [
        {
            "rank": 1,
            "carrierId": 101,
            "carrierName": "BT Wholesale",
            "carrierCode": "bt_wholesale",
            "gatewayId": 201,
            "gatewayName": "bt_primary",
            "dialString": "sofia/gateway/bt_primary/+442012345678",
            "prefix": "4420",
            "prefixMatch": "longest",
            "rate": {
                "perMinute": 0.0125,
                "connectionFee": 0.0,
                "currency": "GBP",
                "billingIncrement": 60,
                "effectiveDate": "2026-01-01T00:00:00Z"
            },
            "quality": {
                "asr": 95.5,
                "acd": 245,
                "pdd": 1200,
                "mosScore": 4.2,
                "qualityScore": 92
            },
            "availability": {
                "maxChannels": 100,
                "activeChannels": 45,
                "availableChannels": 55,
                "status": "available"
            },
            "constraints": {
                "maxCallDuration": 7200,
                "timeRestrictions": null,
                "supportsCli": true,
                "supportsFax": false
            }
        },
        {
            "rank": 2,
            "carrierId": 102,
            "carrierName": "Vonage",
            "carrierCode": "vonage",
            "gatewayId": 202,
            "gatewayName": "vonage_uk",
            "dialString": "sofia/gateway/vonage_uk/+442012345678",
            "prefix": "44",
            "prefixMatch": "country",
            "rate": {
                "perMinute": 0.0150,
                "connectionFee": 0.0,
                "currency": "GBP",
                "billingIncrement": 60,
                "effectiveDate": "2026-01-01T00:00:00Z"
            },
            "quality": {
                "asr": 93.2,
                "acd": 220,
                "pdd": 1500,
                "mosScore": 4.0,
                "qualityScore": 88
            },
            "availability": {
                "maxChannels": 200,
                "activeChannels": 120,
                "availableChannels": 80,
                "status": "available"
            },
            "constraints": {
                "maxCallDuration": 7200,
                "timeRestrictions": null,
                "supportsCli": true,
                "supportsFax": false
            }
        }
    ],
    "metadata": {
        "cacheHit": false,
        "lookupTimeMs": 12,
        "profileId": 1001,
        "profileName": "default",
        "routingStrategy": "lowest_cost"
    }
}
```

**Error Responses:**

**400 Bad Request - Invalid destination:**
```json
{
    "success": false,
    "error": {
        "code": "INVALID_DESTINATION",
        "message": "The destination number format is invalid",
        "details": {
            "destination": "invalid_number",
            "reason": "Not a valid E.164 number"
        }
    }
}
```

**404 Not Found - No routes:**
```json
{
    "success": false,
    "error": {
        "code": "NO_ROUTES_FOUND",
        "message": "No routes available for the destination",
        "details": {
            "destination": "+88812345678",
            "normalizedDestination": "+88812345678",
            "countryCode": "888",
            "reason": "Destination not supported"
        }
    }
}
```

**503 Service Unavailable:**
```json
{
    "success": false,
    "error": {
        "code": "SERVICE_UNAVAILABLE",
        "message": "LCR service temporarily unavailable",
        "details": {
            "retryAfter": 5
        }
    }
}
```

---

### GET /lcr/profiles

List LCR profiles for an organization.

**Request:**
```http
GET /lcr/profiles?organizationId=12345
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "profiles": [
        {
            "id": 1001,
            "name": "default",
            "description": "Default routing profile",
            "organizationId": 12345,
            "priority": 0,
            "enabled": true,
            "routingStrategy": "lowest_cost",
            "settings": {
                "maxRetries": 3,
                "failoverEnabled": true,
                "qualityThreshold": 70
            },
            "createdAt": "2025-01-15T10:00:00Z",
            "updatedAt": "2026-01-10T14:30:00Z"
        },
        {
            "id": 1002,
            "name": "premium",
            "description": "Premium quality routing",
            "organizationId": 12345,
            "priority": 10,
            "enabled": true,
            "routingStrategy": "highest_quality",
            "settings": {
                "maxRetries": 5,
                "failoverEnabled": true,
                "qualityThreshold": 85
            },
            "createdAt": "2025-03-20T09:00:00Z",
            "updatedAt": "2026-01-05T11:15:00Z"
        }
    ]
}
```

---

### GET /lcr/profiles/{profileId}

Get details of a specific LCR profile.

**Response:**
```json
{
    "success": true,
    "profile": {
        "id": 1001,
        "name": "default",
        "description": "Default routing profile",
        "organizationId": 12345,
        "priority": 0,
        "enabled": true,
        "routingStrategy": "lowest_cost",
        "settings": {
            "maxRetries": 3,
            "failoverEnabled": true,
            "qualityThreshold": 70,
            "preferredCodecs": ["PCMA", "PCMU", "G729"],
            "maxChannelsPerCarrier": 50
        },
        "routes": [
            {
                "id": 5001,
                "carrierId": 101,
                "carrierName": "BT Wholesale",
                "gatewayId": 201,
                "prefix": "44",
                "priority": 1,
                "weight": 100,
                "enabled": true,
                "ratePerMinute": 0.0125
            },
            {
                "id": 5002,
                "carrierId": 102,
                "carrierName": "Vonage",
                "gatewayId": 202,
                "prefix": "44",
                "priority": 2,
                "weight": 80,
                "enabled": true,
                "ratePerMinute": 0.0150
            }
        ],
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": "2026-01-10T14:30:00Z"
    }
}
```

---

### POST /lcr/profiles

Create a new LCR profile.

**Request:**
```json
{
    "name": "international_premium",
    "description": "Premium international routing",
    "organizationId": 12345,
    "priority": 5,
    "enabled": true,
    "routingStrategy": "highest_quality",
    "settings": {
        "maxRetries": 5,
        "failoverEnabled": true,
        "qualityThreshold": 80
    }
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "profile": {
        "id": 1003,
        "name": "international_premium",
        "description": "Premium international routing",
        "organizationId": 12345,
        "priority": 5,
        "enabled": true,
        "routingStrategy": "highest_quality",
        "settings": {
            "maxRetries": 5,
            "failoverEnabled": true,
            "qualityThreshold": 80
        },
        "createdAt": "2026-01-20T10:30:00Z",
        "updatedAt": "2026-01-20T10:30:00Z"
    }
}
```

---

### GET /lcr/carriers

List available carriers.

**Request:**
```http
GET /lcr/carriers?enabled=true
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "carriers": [
        {
            "id": 101,
            "name": "BT Wholesale",
            "code": "bt_wholesale",
            "enabled": true,
            "maxChannels": 500,
            "currentChannels": 234,
            "capabilities": {
                "supportsCli": true,
                "supportsFax": true,
                "supportsSms": false,
                "supportsVideo": false
            },
            "failoverConfig": {
                "enabled": true,
                "threshold": 3,
                "window": 300
            },
            "gateways": [
                {
                    "id": 201,
                    "name": "bt_primary",
                    "hostname": "sip.bt.example.com",
                    "port": 5060,
                    "transport": "tcp",
                    "status": "active",
                    "maxChannels": 100,
                    "currentChannels": 45
                },
                {
                    "id": 202,
                    "name": "bt_secondary",
                    "hostname": "sip2.bt.example.com",
                    "port": 5060,
                    "transport": "tcp",
                    "status": "active",
                    "maxChannels": 100,
                    "currentChannels": 32
                }
            ],
            "quality": {
                "asr": 95.5,
                "acd": 245,
                "pdd": 1200
            }
        }
    ]
}
```

---

### GET /lcr/gateways/{gatewayId}/health

Get health status of a specific gateway.

**Response:**
```json
{
    "success": true,
    "gateway": {
        "id": 201,
        "name": "bt_primary",
        "carrierId": 101,
        "carrierName": "BT Wholesale"
    },
    "health": {
        "status": "healthy",
        "score": 95,
        "lastCheck": "2026-01-20T10:29:00Z",
        "metrics": {
            "sipOptionsResponseTime": 45,
            "asr": 96.2,
            "failureRate": 1.8,
            "activeChannels": 45,
            "availableChannels": 55,
            "channelUtilization": 0.45
        },
        "recentCalls": {
            "total": 1250,
            "successful": 1228,
            "failed": 22,
            "timeWindow": "5m"
        }
    }
}
```

---

### GET /lcr/rates

Get rate information for destinations.

**Request:**
```http
GET /lcr/rates?organizationId=12345&prefix=44&carrierId=101
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
    "success": true,
    "rates": [
        {
            "id": 10001,
            "carrierId": 101,
            "carrierName": "BT Wholesale",
            "prefix": "4420",
            "destination": "UK London",
            "ratePerMinute": 0.0125,
            "connectionFee": 0.0,
            "currency": "GBP",
            "billingIncrement": 60,
            "effectiveDate": "2026-01-01T00:00:00Z",
            "expiryDate": null
        },
        {
            "id": 10002,
            "carrierId": 101,
            "carrierName": "BT Wholesale",
            "prefix": "4421",
            "destination": "UK Sheffield",
            "ratePerMinute": 0.0125,
            "connectionFee": 0.0,
            "currency": "GBP",
            "billingIncrement": 60,
            "effectiveDate": "2026-01-01T00:00:00Z",
            "expiryDate": null
        },
        {
            "id": 10003,
            "carrierId": 101,
            "carrierName": "BT Wholesale",
            "prefix": "447",
            "destination": "UK Mobile",
            "ratePerMinute": 0.0450,
            "connectionFee": 0.0,
            "currency": "GBP",
            "billingIncrement": 60,
            "effectiveDate": "2026-01-01T00:00:00Z",
            "expiryDate": null
        }
    ],
    "pagination": {
        "page": 1,
        "pageSize": 100,
        "totalItems": 3,
        "totalPages": 1
    }
}
```

---

### POST /lcr/routes

Add a route to an LCR profile.

**Request:**
```json
{
    "profileId": 1001,
    "carrierId": 103,
    "gatewayId": 203,
    "prefix": "1",
    "priority": 3,
    "weight": 50,
    "enabled": true,
    "ratePerMinute": 0.0200,
    "connectionFee": 0.0,
    "currency": "GBP",
    "billingIncrement": 60,
    "constraints": {
        "maxCallDuration": 7200,
        "timeRestrictions": null
    }
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "route": {
        "id": 5003,
        "profileId": 1001,
        "carrierId": 103,
        "carrierName": "Twilio",
        "gatewayId": 203,
        "gatewayName": "twilio_us",
        "prefix": "1",
        "priority": 3,
        "weight": 50,
        "enabled": true,
        "ratePerMinute": 0.0200,
        "connectionFee": 0.0,
        "currency": "GBP",
        "billingIncrement": 60,
        "createdAt": "2026-01-20T10:35:00Z"
    }
}
```

---

### DELETE /lcr/routes/{routeId}

Delete a route from an LCR profile.

**Response (204 No Content):**
```
(empty body)
```

---

### POST /lcr/cache/invalidate

Invalidate LCR cache for an organization.

**Request:**
```json
{
    "organizationId": 12345,
    "scope": "all"  // or "prefix", "carrier"
}
```

**Response:**
```json
{
    "success": true,
    "invalidated": {
        "keys": 1250,
        "scope": "all"
    }
}
```

---

## Data Types

### Routing Strategy Enum

| Value | Description |
|-------|-------------|
| `lowest_cost` | Prioritize routes by lowest cost per minute |
| `highest_quality` | Prioritize routes by quality score (ASR, PDD) |
| `priority` | Use configured priority order |
| `round_robin` | Distribute calls evenly across carriers |
| `weighted` | Distribute based on weight configuration |

### Gateway Status Enum

| Value | Description |
|-------|-------------|
| `active` | Gateway is healthy and accepting calls |
| `degraded` | Gateway has reduced quality but operational |
| `maintenance` | Gateway in maintenance mode |
| `failed` | Gateway is not responding |
| `disabled` | Gateway manually disabled |

### Health Status Enum

| Value | Score Range | Description |
|-------|-------------|-------------|
| `healthy` | 70-100 | Gateway operating normally |
| `degraded` | 40-69 | Gateway has issues but operational |
| `unhealthy` | 0-39 | Gateway should not receive traffic |

---

## Webhooks

The LCR service can send webhooks for significant events.

### Route Change Webhook

**Event:** `lcr.route.changed`

```json
{
    "event": "lcr.route.changed",
    "timestamp": "2026-01-20T10:40:00Z",
    "data": {
        "profileId": 1001,
        "organizationId": 12345,
        "changeType": "route_disabled",
        "route": {
            "id": 5001,
            "carrierId": 101,
            "prefix": "44"
        },
        "reason": "manual_disable"
    }
}
```

### Gateway Status Webhook

**Event:** `lcr.gateway.status_changed`

```json
{
    "event": "lcr.gateway.status_changed",
    "timestamp": "2026-01-20T10:45:00Z",
    "data": {
        "gatewayId": 201,
        "gatewayName": "bt_primary",
        "carrierId": 101,
        "previousStatus": "active",
        "currentStatus": "degraded",
        "healthScore": 55,
        "reason": "high_failure_rate",
        "metrics": {
            "failureRate": 15.5,
            "asr": 72.3
        }
    }
}
```

---

## Rate Limiting

| Endpoint | Rate Limit |
|----------|------------|
| `POST /lcr/route` | 1000 requests/minute |
| `GET /lcr/profiles` | 100 requests/minute |
| `POST /lcr/cache/invalidate` | 10 requests/minute |

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705750800
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_DESTINATION` | 400 | Destination number format invalid |
| `INVALID_ORGANIZATION` | 400 | Organization ID invalid |
| `PROFILE_NOT_FOUND` | 404 | LCR profile not found |
| `ROUTE_NOT_FOUND` | 404 | LCR route not found |
| `NO_ROUTES_FOUND` | 404 | No routes for destination |
| `CARRIER_NOT_FOUND` | 404 | Carrier not found |
| `GATEWAY_NOT_FOUND` | 404 | Gateway not found |
| `DUPLICATE_ROUTE` | 409 | Route already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `DATABASE_ERROR` | 500 | Database connection error |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-20 | 1.0.0 | Initial API documentation |
