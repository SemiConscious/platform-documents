# ESL Events System

[![API Service](https://img.shields.io/badge/type-API%20Service-blue.svg)](/)
[![PHP](https://img.shields.io/badge/PHP-8.x-777BB4.svg?logo=php)](https://php.net)
[![Symfony](https://img.shields.io/badge/Symfony-Framework-black.svg?logo=symfony)](https://symfony.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker)](https://docker.com)
[![OAuth2](https://img.shields.io/badge/Auth-OAuth2-green.svg)](/docs/auth)

> **Sapien** is a PHP-based REST API service built on Symfony, providing CRUD operations for entities like Person, Pet, and Toy, with Docker-based development environment, Xdebug integration, and ESL event system for real-time updates.

---

## Table of Contents

- [Overview](#overview)
- [Event Architecture](#event-architecture)
- [Available Events](#available-events)
- [Subscribing to Events](#subscribing-to-events)
- [Event Payload Formats](#event-payload-formats)
- [Authentication & Authorization](#authentication--authorization)
- [Rate Limiting](#rate-limiting)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Overview

The **Event Service Layer (ESL)** is Sapien's real-time event notification system, designed to provide immediate updates when entities change within the system. Rather than polling the API repeatedly for changes, clients can subscribe to specific event channels and receive push notifications when relevant data is created, updated, or deleted.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Real-time Updates** | Receive instant notifications when entities change |
| **Granular Subscriptions** | Subscribe to specific event types or entity categories |
| **OAuth2 Integration** | Secure event delivery using access/refresh token authentication |
| **Organization Scoping** | Events are scoped to your organization's data boundaries |
| **Blob Storage Support** | Large payloads are stored and referenced via blob storage |
| **Rate Limited** | Fair usage policies applied per organization |

### Use Cases

- **Availability Tracking**: Monitor when users or resources become available/unavailable
- **Entity Synchronization**: Keep external systems in sync with Sapien data
- **Audit Logging**: Track all changes to entities for compliance purposes
- **Real-time Dashboards**: Power live dashboards with immediate data updates
- **Workflow Automation**: Trigger automated processes based on entity changes

---

## Event Architecture

The ESL follows a publish-subscribe pattern where Sapien acts as the publisher and your application acts as the subscriber. Events flow through a message broker, ensuring reliable delivery even during temporary network issues.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SAPIEN SERVICE                                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  Person  │    │   Pet    │    │   Toy    │    │  Other   │         │
│  │  Entity  │    │  Entity  │    │  Entity  │    │ Entities │         │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘         │
│       │               │               │               │                │
│       └───────────────┴───────────────┴───────────────┘                │
│                               │                                        │
│                       ┌───────▼───────┐                                │
│                       │  Event        │                                │
│                       │  Dispatcher   │                                │
│                       └───────┬───────┘                                │
└───────────────────────────────┼────────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │   Message     │
                        │   Broker      │
                        └───────┬───────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
   ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
   │ Subscriber  │       │ Subscriber  │       │ Subscriber  │
   │     A       │       │     B       │       │     C       │
   └─────────────┘       └─────────────┘       └─────────────┘
```

### Architecture Components

1. **Entity Layer**: Core domain objects (Person, Pet, Toy, etc.) that generate events on state changes
2. **Event Dispatcher**: Symfony-based dispatcher that captures entity lifecycle events
3. **Message Broker**: Handles event queuing, routing, and guaranteed delivery
4. **Subscriber Endpoints**: Your registered webhook URLs or WebSocket connections

---

## Available Events

Sapien ESL provides events across multiple entity types and lifecycle stages. Events follow a consistent naming convention: `{entity}.{action}`.

### Entity Events

| Event Name | Description | Trigger |
|------------|-------------|---------|
| `person.created` | A new Person entity was created | POST /api/persons |
| `person.updated` | A Person entity was modified | PUT/PATCH /api/persons/{id} |
| `person.deleted` | A Person entity was removed | DELETE /api/persons/{id} |
| `pet.created` | A new Pet entity was created | POST /api/pets |
| `pet.updated` | A Pet entity was modified | PUT/PATCH /api/pets/{id} |
| `pet.deleted` | A Pet entity was removed | DELETE /api/pets/{id} |
| `toy.created` | A new Toy entity was created | POST /api/toys |
| `toy.updated` | A Toy entity was modified | PUT/PATCH /api/toys/{id} |
| `toy.deleted` | A Toy entity was removed | DELETE /api/toys/{id} |

### Availability Events

| Event Name | Description | Trigger |
|------------|-------------|---------|
| `availability.changed` | User availability status changed | Availability toggle/schedule |
| `availability.profile.created` | New availability profile created | Profile creation |
| `availability.profile.updated` | Availability profile modified | Profile update |
| `availability.profile.deleted` | Availability profile removed | Profile deletion |
| `availability.schedule.triggered` | Scheduled availability change occurred | Cron/scheduler |

### System Events

| Event Name | Description | Trigger |
|------------|-------------|---------|
| `system.maintenance.scheduled` | Upcoming maintenance window | Admin action |
| `system.rate_limit.warning` | Approaching rate limit threshold | 80% of limit reached |
| `system.rate_limit.exceeded` | Rate limit exceeded | Limit reached |

---

## Subscribing to Events

### Webhook Subscriptions

Register a webhook endpoint to receive events via HTTP POST requests.

#### PHP Example (Using Guzzle)

```php
<?php

use GuzzleHttp\Client;

$client = new Client([
    'base_uri' => 'https://api.sapien.example.com',
    'headers' => [
        'Authorization' => 'Bearer ' . $accessToken,
        'Content-Type' => 'application/json',
    ],
]);

// Register a webhook subscription
$response = $client->post('/api/v1/subscriptions', [
    'json' => [
        'callback_url' => 'https://your-app.com/webhooks/sapien',
        'events' => [
            'person.created',
            'person.updated',
            'availability.changed',
        ],
        'secret' => 'your-webhook-secret-for-signature-verification',
        'active' => true,
    ],
]);

$subscription = json_decode($response->getBody(), true);
echo "Subscription ID: " . $subscription['id'] . "\n";
```

#### cURL Example

```bash
curl -X POST https://api.sapien.example.com/api/v1/subscriptions \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "callback_url": "https://your-app.com/webhooks/sapien",
    "events": ["person.created", "person.updated", "availability.changed"],
    "secret": "your-webhook-secret-for-signature-verification",
    "active": true
  }'
```

### Webhook Handler Implementation

```php
<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

class SapienWebhookController extends AbstractController
{
    private const WEBHOOK_SECRET = 'your-webhook-secret-for-signature-verification';

    #[Route('/webhooks/sapien', name: 'sapien_webhook', methods: ['POST'])]
    public function handleWebhook(Request $request): Response
    {
        // Verify the webhook signature
        $signature = $request->headers->get('X-Sapien-Signature');
        $payload = $request->getContent();
        
        if (!$this->verifySignature($payload, $signature)) {
            return new Response('Invalid signature', Response::HTTP_UNAUTHORIZED);
        }

        $event = json_decode($payload, true);
        
        // Route to appropriate handler based on event type
        match ($event['type']) {
            'person.created' => $this->handlePersonCreated($event),
            'person.updated' => $this->handlePersonUpdated($event),
            'availability.changed' => $this->handleAvailabilityChanged($event),
            default => $this->logUnhandledEvent($event),
        };

        return new Response('OK', Response::HTTP_OK);
    }

    private function verifySignature(string $payload, ?string $signature): bool
    {
        if ($signature === null) {
            return false;
        }
        
        $expectedSignature = hash_hmac('sha256', $payload, self::WEBHOOK_SECRET);
        return hash_equals($expectedSignature, $signature);
    }

    private function handlePersonCreated(array $event): void
    {
        $personData = $event['data'];
        // Process the new person...
        $this->logger->info('New person created', [
            'person_id' => $personData['id'],
            'name' => $personData['name'],
        ]);
    }

    private function handlePersonUpdated(array $event): void
    {
        $personData = $event['data'];
        $changes = $event['changes'] ?? [];
        // Process the update...
    }

    private function handleAvailabilityChanged(array $event): void
    {
        $availabilityData = $event['data'];
        // Update local availability cache, notify users, etc.
    }

    private function logUnhandledEvent(array $event): void
    {
        $this->logger->warning('Unhandled event type', ['type' => $event['type']]);
    }
}
```

### Managing Subscriptions

```php
<?php

// List all subscriptions
$response = $client->get('/api/v1/subscriptions');
$subscriptions = json_decode($response->getBody(), true);

// Update a subscription
$response = $client->patch('/api/v1/subscriptions/' . $subscriptionId, [
    'json' => [
        'events' => ['person.created', 'person.updated', 'person.deleted'],
        'active' => true,
    ],
]);

// Pause a subscription
$response = $client->patch('/api/v1/subscriptions/' . $subscriptionId, [
    'json' => ['active' => false],
]);

// Delete a subscription
$response = $client->delete('/api/v1/subscriptions/' . $subscriptionId);
```

---

## Event Payload Formats

All events follow a consistent JSON structure for predictable parsing.

### Standard Event Envelope

```json
{
  "id": "evt_01H8XYZABC123DEF456",
  "type": "person.updated",
  "version": "1.0",
  "timestamp": "2024-01-15T14:32:00.000Z",
  "organization_id": "org_01H8ABC123",
  "data": {
    // Entity-specific data
  },
  "metadata": {
    "correlation_id": "req_01H8XYZ789",
    "triggered_by": "user_01H8USER123",
    "source": "api"
  }
}
```

### Person Entity Payload

```json
{
  "id": "evt_01H8PERSON_UPDATED",
  "type": "person.updated",
  "version": "1.0",
  "timestamp": "2024-01-15T14:32:00.000Z",
  "organization_id": "org_01H8ABC123",
  "data": {
    "id": "person_01H8XYZ",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "status": "active",
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-15T14:32:00.000Z",
    "pets": [
      {
        "id": "pet_01H8ABC",
        "name": "Buddy",
        "type": "dog"
      }
    ]
  },
  "changes": {
    "name": {
      "old": "John Smith",
      "new": "John Doe"
    }
  },
  "metadata": {
    "correlation_id": "req_01H8XYZ789",
    "triggered_by": "user_01H8USER123",
    "source": "api"
  }
}
```

### Availability Changed Payload

```json
{
  "id": "evt_01H8AVAIL_CHANGED",
  "type": "availability.changed",
  "version": "1.0",
  "timestamp": "2024-01-15T14:32:00.000Z",
  "organization_id": "org_01H8ABC123",
  "data": {
    "user_id": "user_01H8ABC",
    "previous_status": "available",
    "current_status": "busy",
    "profile_id": "profile_01H8XYZ",
    "effective_until": "2024-01-15T18:00:00.000Z",
    "reason": "In meeting"
  },
  "metadata": {
    "correlation_id": "req_01H8XYZ789",
    "triggered_by": "user_01H8ABC",
    "source": "schedule"
  }
}
```

### Large Payload Handling (Blob Storage)

When event payloads exceed 256KB, they are stored in blob storage and referenced:

```json
{
  "id": "evt_01H8LARGE_PAYLOAD",
  "type": "person.updated",
  "version": "1.0",
  "timestamp": "2024-01-15T14:32:00.000Z",
  "organization_id": "org_01H8ABC123",
  "data_ref": {
    "type": "blob",
    "uri": "https://blob.sapien.example.com/events/evt_01H8LARGE_PAYLOAD",
    "expires_at": "2024-01-16T14:32:00.000Z",
    "size_bytes": 524288,
    "checksum": "sha256:abc123..."
  },
  "metadata": {
    "correlation_id": "req_01H8XYZ789",
    "triggered_by": "user_01H8USER123",
    "source": "api"
  }
}
```

Fetching the full payload:

```php
<?php

if (isset($event['data_ref'])) {
    $blobResponse = $client->get($event['data_ref']['uri']);
    $fullData = json_decode($blobResponse->getBody(), true);
} else {
    $fullData = $event['data'];
}
```

---

## Authentication & Authorization

ESL uses OAuth2 for authentication, consistent with all Sapien API endpoints.

### Obtaining Tokens

```php
<?php

$response = $client->post('/oauth/token', [
    'form_params' => [
        'grant_type' => 'client_credentials',
        'client_id' => 'your-client-id',
        'client_secret' => 'your-client-secret',
        'scope' => 'events:subscribe events:read',
    ],
]);

$tokens = json_decode($response->getBody(), true);
$accessToken = $tokens['access_token'];
$refreshToken = $tokens['refresh_token'];
```

### Required Scopes

| Scope | Permission |
|-------|------------|
| `events:subscribe` | Create and manage subscriptions |
| `events:read` | Read event history and subscription details |
| `events:admin` | Administrative access (org admins only) |

---

## Rate Limiting

Event subscriptions are rate-limited per organization to ensure fair usage.

| Tier | Subscriptions | Events/Hour | Retry Budget |
|------|---------------|-------------|--------------|
| Free | 5 | 1,000 | 3 retries |
| Standard | 25 | 10,000 | 5 retries |
| Enterprise | Unlimited | 100,000 | 10 retries |

Rate limit headers are included in API responses:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9542
X-RateLimit-Reset: 1705330800
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OAuth2 credentials for Sapien API
- A publicly accessible HTTPS endpoint for webhooks

### 1. Clone and Start the Service

```bash
git clone https://github.com/your-org/sapien.git
cd sapien
docker-compose up -d
```

### 2. Verify the Service is Running

```bash
curl http://localhost:8080/health
# Expected: {"status":"healthy","version":"1.0.0"}
```

### 3. Register Your First Subscription

```bash
# Obtain access token
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8080/oauth/token \
  -d "grant_type=client_credentials&client_id=YOUR_ID&client_secret=YOUR_SECRET" \
  | jq -r '.access_token')

# Create subscription
curl -X POST http://localhost:8080/api/v1/subscriptions \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "callback_url": "https://your-app.com/webhooks/sapien",
    "events": ["person.created"],
    "secret": "my-secret-123"
  }'
```

---

## Configuration

The following environment variables configure ESL behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `ESL_ENABLED` | Enable/disable the event system | `true` |
| `ESL_BROKER_URL` | Message broker connection URL | `amqp://localhost` |
| `ESL_RETRY_ATTEMPTS` | Max delivery retry attempts | `5` |
| `ESL_RETRY_DELAY_MS` | Delay between retries (ms) | `1000` |
| `ESL_MAX_PAYLOAD_SIZE` | Max inline payload size (bytes) | `262144` |
| `ESL_BLOB_STORAGE_URL` | Blob storage endpoint for large payloads | - |
| `ESL_SIGNATURE_ALGORITHM` | HMAC algorithm for signatures | `sha256` |
| `OAUTH_TOKEN_LIFETIME` | Access token lifetime (seconds) | `3600` |
| `OAUTH_REFRESH_LIFETIME` | Refresh token lifetime (seconds) | `86400` |
| `RATE_LIMIT_EVENTS_HOUR` | Events per hour limit | `10000` |
| `PROFILER_ENABLED` | Enable Symfony profiler | `false` |
| `XDEBUG_MODE` | Xdebug mode for development | `off` |

---

## Troubleshooting

### Common Issues

#### Events Not Being Delivered

1. **Check subscription status**: Ensure `active: true`
2. **Verify callback URL**: Must be HTTPS and publicly accessible
3. **Check rate limits**: Review `X-RateLimit-Remaining` header
4. **Inspect delivery logs**: `GET /api/v1/subscriptions/{id}/deliveries`

#### Signature Verification Failing

```php
// Ensure you're using raw payload, not parsed JSON
$payload = $request->getContent(); // ✅ Correct
$payload = json_encode($request->request->all()); // ❌ Wrong
```

#### Rate Limit Exceeded

```php
// Implement exponential backoff
$retryAfter = $response->getHeader('Retry-After')[0] ?? 60;
sleep((int) $retryAfter);
```

### Debug Mode

Enable profiler for detailed request/response inspection:

```yaml
# docker-compose.override.yml
services:
  sapien:
    environment:
      - PROFILER_ENABLED=true
      - XDEBUG_MODE=debug
```

Access profiler at: `http://localhost:8080/_profiler`

---

## Documentation

For detailed documentation on specific event types and advanced integration patterns, see:

- **[User Availability Events](docs/events/user-availability.md)** - Complete reference for user availability status changes, schedules, and real-time presence tracking
- **[Availability Profile Events](docs/events/availability-profile.md)** - Documentation for availability profile lifecycle events and configuration options

### Additional Resources

| Resource | Description |
|----------|-------------|
| [API Reference](/docs/api) | Complete REST API documentation |
| [Authentication Guide](/docs/auth) | OAuth2 setup and token management |
| [Docker Setup](/docs/docker) | Development environment configuration |
| [PhpStorm + Xdebug](/docs/debugging) | IDE integration for debugging |

---

## Support

- **Issues**: Report bugs via GitHub Issues
- **Security**: Report vulnerabilities to security@sapien.example.com
- **Community**: Join our Discord for discussions

---

<div align="center">

**Built with ❤️ using Symfony & PHP**

[Documentation](/) · [API Reference](/docs/api) · [Changelog](/CHANGELOG.md)

</div>