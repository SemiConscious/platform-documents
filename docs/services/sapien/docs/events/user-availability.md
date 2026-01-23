# User Availability Events

## Overview

The `SapienEvent::UserAvailabilityUpdate` event is a core component of Sapien's ESL (Event Streaming Layer) system, designed to broadcast real-time updates about user availability status across connected services and clients. This event enables applications to maintain synchronized user presence information, power live status indicators, and trigger automated workflows based on availability changes.

This documentation provides comprehensive guidance for developers integrating with the User Availability Events system, including event structure, trigger conditions, payload schemas, and implementation examples across multiple programming languages.

---

## Event Description

### What is the UserAvailabilityUpdate Event?

The `SapienEvent::UserAvailabilityUpdate` event is fired whenever a user's availability status changes within the Sapien ecosystem. This event follows a publish-subscribe pattern, allowing multiple consumers to react to availability changes without tight coupling to the source system.

### Event Identifier

```
SapienEvent::UserAvailabilityUpdate
```

### Event Characteristics

| Property | Value |
|----------|-------|
| Event Type | `user.availability.update` |
| Channel | `sapien.events.availability` |
| Priority | High |
| Retention | 24 hours |
| Max Payload Size | 64 KB |
| Delivery Guarantee | At-least-once |

### Use Cases

- **Real-time presence indicators**: Display online/offline/busy status in user interfaces
- **Automated routing**: Route incoming requests to available team members
- **Notification systems**: Trigger alerts when specific users become available
- **Analytics**: Track user engagement patterns and availability metrics
- **Integration triggers**: Initiate third-party workflows based on status changes

---

## Trigger Conditions

The `SapienEvent::UserAvailabilityUpdate` event is emitted under the following conditions:

### Primary Triggers

| Trigger | Description | Example |
|---------|-------------|---------|
| **Explicit Status Change** | User manually updates their availability status | User sets status to "Away" |
| **Session Start** | User authenticates and begins a new session | User logs in via OAuth2 |
| **Session End** | User's session terminates (logout or expiration) | User logs out or token expires |
| **Idle Timeout** | User becomes inactive after configured threshold | No activity for 15 minutes |
| **Activity Resume** | User returns from idle state | Mouse movement after idle |
| **Schedule-based Change** | Automated status based on calendar/schedule | Working hours end at 6 PM |
| **System Override** | Administrative status change | Admin marks user as unavailable |

### Trigger Priority Rules

When multiple trigger conditions occur simultaneously, the following priority order applies:

1. **System Override** (highest priority)
2. **Explicit Status Change**
3. **Session Start/End**
4. **Schedule-based Change**
5. **Idle Timeout / Activity Resume** (lowest priority)

### Debouncing and Rate Limiting

To prevent event flooding, the following rules apply:

- **Minimum interval**: 5 seconds between events for the same user
- **Idle threshold**: Configurable (default: 900 seconds / 15 minutes)
- **Batch window**: Events within 100ms are consolidated
- **Organization rate limit**: Subject to standard API rate limits

---

## Payload Schema

### Full Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UserAvailabilityUpdate",
  "type": "object",
  "required": ["event_id", "event_type", "timestamp", "data"],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this event instance"
    },
    "event_type": {
      "type": "string",
      "const": "user.availability.update",
      "description": "Event type identifier"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when event was generated"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Event schema version"
    },
    "data": {
      "type": "object",
      "required": ["user_id", "organization_id", "availability"],
      "properties": {
        "user_id": {
          "type": "string",
          "format": "uuid",
          "description": "Unique identifier of the user"
        },
        "organization_id": {
          "type": "string",
          "format": "uuid",
          "description": "Organization the user belongs to"
        },
        "availability": {
          "type": "object",
          "required": ["status", "changed_at"],
          "properties": {
            "status": {
              "type": "string",
              "enum": ["available", "away", "busy", "do_not_disturb", "offline"],
              "description": "Current availability status"
            },
            "previous_status": {
              "type": "string",
              "enum": ["available", "away", "busy", "do_not_disturb", "offline", null],
              "description": "Previous availability status"
            },
            "changed_at": {
              "type": "string",
              "format": "date-time",
              "description": "When the status changed"
            },
            "expires_at": {
              "type": "string",
              "format": "date-time",
              "description": "When status will auto-revert (optional)"
            },
            "custom_message": {
              "type": "string",
              "maxLength": 256,
              "description": "Optional user-defined status message"
            }
          }
        },
        "trigger": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["manual", "session_start", "session_end", "idle_timeout", "activity_resume", "schedule", "system_override"],
              "description": "What triggered this event"
            },
            "source": {
              "type": "string",
              "description": "Source system or endpoint"
            },
            "actor_id": {
              "type": "string",
              "format": "uuid",
              "description": "User/system that initiated the change"
            }
          }
        },
        "metadata": {
          "type": "object",
          "properties": {
            "session_id": {
              "type": "string",
              "format": "uuid"
            },
            "device_type": {
              "type": "string",
              "enum": ["web", "mobile", "desktop", "api"]
            },
            "ip_address": {
              "type": "string",
              "format": "ipv4"
            },
            "user_agent": {
              "type": "string"
            }
          }
        }
      }
    }
  }
}
```

### Status Definitions

| Status | Description | Typical Use |
|--------|-------------|-------------|
| `available` | User is online and ready to engage | Active working state |
| `away` | User is temporarily unavailable | Short breaks, meetings |
| `busy` | User is occupied but may respond to urgent matters | Focused work time |
| `do_not_disturb` | User should not be contacted | Important tasks, presentations |
| `offline` | User is not connected | Logged out, session expired |

---

## Example Payloads

### Example 1: Manual Status Change

User explicitly sets their status to "busy" with a custom message:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440001",
  "event_type": "user.availability.update",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "version": "1.0.0",
  "data": {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "organization_id": "org-12345678-abcd-efgh-ijkl-mnopqrstuvwx",
    "availability": {
      "status": "busy",
      "previous_status": "available",
      "changed_at": "2024-01-15T14:30:00.000Z",
      "expires_at": "2024-01-15T16:00:00.000Z",
      "custom_message": "In a meeting until 4 PM"
    },
    "trigger": {
      "type": "manual",
      "source": "web_app",
      "actor_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    },
    "metadata": {
      "session_id": "sess-87654321-dcba-hgfe-lkji-xwvutsrqponm",
      "device_type": "web",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
  }
}
```

### Example 2: Session Start (Login)

User logs in and becomes available:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440002",
  "event_type": "user.availability.update",
  "timestamp": "2024-01-15T09:00:00.000Z",
  "version": "1.0.0",
  "data": {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "organization_id": "org-12345678-abcd-efgh-ijkl-mnopqrstuvwx",
    "availability": {
      "status": "available",
      "previous_status": "offline",
      "changed_at": "2024-01-15T09:00:00.000Z"
    },
    "trigger": {
      "type": "session_start",
      "source": "oauth2_auth_endpoint",
      "actor_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    },
    "metadata": {
      "session_id": "sess-new12345-abcd-efgh-ijkl-mnopqrstuvwx",
      "device_type": "desktop",
      "ip_address": "10.0.0.50"
    }
  }
}
```

### Example 3: Idle Timeout

User becomes idle after inactivity:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440003",
  "event_type": "user.availability.update",
  "timestamp": "2024-01-15T11:15:00.000Z",
  "version": "1.0.0",
  "data": {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "organization_id": "org-12345678-abcd-efgh-ijkl-mnopqrstuvwx",
    "availability": {
      "status": "away",
      "previous_status": "available",
      "changed_at": "2024-01-15T11:15:00.000Z"
    },
    "trigger": {
      "type": "idle_timeout",
      "source": "presence_monitor",
      "actor_id": null
    },
    "metadata": {
      "session_id": "sess-87654321-dcba-hgfe-lkji-xwvutsrqponm",
      "device_type": "web"
    }
  }
}
```

### Example 4: System Override by Administrator

Administrator forces a user offline:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440004",
  "event_type": "user.availability.update",
  "timestamp": "2024-01-15T17:00:00.000Z",
  "version": "1.0.0",
  "data": {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "organization_id": "org-12345678-abcd-efgh-ijkl-mnopqrstuvwx",
    "availability": {
      "status": "offline",
      "previous_status": "available",
      "changed_at": "2024-01-15T17:00:00.000Z",
      "custom_message": "Account suspended - contact support"
    },
    "trigger": {
      "type": "system_override",
      "source": "admin_panel",
      "actor_id": "admin-99999999-aaaa-bbbb-cccc-dddddddddddd"
    }
  }
}
```

---

## Handling Examples

### PHP (Symfony) - Event Subscriber

```php
<?php

namespace App\EventSubscriber;

use App\Event\SapienEvent;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Psr\Log\LoggerInterface;

class UserAvailabilitySubscriber implements EventSubscriberInterface
{
    private LoggerInterface $logger;
    private NotificationService $notificationService;
    private UserPresenceRepository $presenceRepository;

    public function __construct(
        LoggerInterface $logger,
        NotificationService $notificationService,
        UserPresenceRepository $presenceRepository
    ) {
        $this->logger = $logger;
        $this->notificationService = $notificationService;
        $this->presenceRepository = $presenceRepository;
    }

    public static function getSubscribedEvents(): array
    {
        return [
            SapienEvent::UserAvailabilityUpdate => [
                ['onUserAvailabilityUpdate', 10],
                ['logAvailabilityChange', -10],
            ],
        ];
    }

    public function onUserAvailabilityUpdate(UserAvailabilityUpdateEvent $event): void
    {
        $payload = $event->getPayload();
        $userId = $payload['data']['user_id'];
        $status = $payload['data']['availability']['status'];
        $previousStatus = $payload['data']['availability']['previous_status'] ?? null;

        // Update local presence cache
        $this->presenceRepository->updateUserPresence(
            $userId,
            $status,
            $payload['data']['availability']['custom_message'] ?? null
        );

        // Notify watchers if user becomes available
        if ($status === 'available' && $previousStatus === 'offline') {
            $this->notificationService->notifyWatchers(
                $userId,
                'User is now online'
            );
        }

        // Handle do-not-disturb escalation rules
        if ($status === 'do_not_disturb') {
            $this->handleDoNotDisturbMode($userId, $payload);
        }
    }

    public function logAvailabilityChange(UserAvailabilityUpdateEvent $event): void
    {
        $payload = $event->getPayload();
        
        $this->logger->info('User availability changed', [
            'event_id' => $payload['event_id'],
            'user_id' => $payload['data']['user_id'],
            'status' => $payload['data']['availability']['status'],
            'trigger_type' => $payload['data']['trigger']['type'] ?? 'unknown',
        ]);
    }

    private function handleDoNotDisturbMode(string $userId, array $payload): void
    {
        $expiresAt = $payload['data']['availability']['expires_at'] ?? null;
        
        if ($expiresAt) {
            // Schedule automatic status revert
            $this->presenceRepository->scheduleStatusRevert(
                $userId,
                new \DateTimeImmutable($expiresAt)
            );
        }
    }
}
```

### JavaScript/TypeScript - WebSocket Client

```typescript
import { EventEmitter } from 'events';

interface UserAvailabilityPayload {
  event_id: string;
  event_type: 'user.availability.update';
  timestamp: string;
  version: string;
  data: {
    user_id: string;
    organization_id: string;
    availability: {
      status: 'available' | 'away' | 'busy' | 'do_not_disturb' | 'offline';
      previous_status?: string;
      changed_at: string;
      expires_at?: string;
      custom_message?: string;
    };
    trigger: {
      type: string;
      source: string;
      actor_id?: string;
    };
    metadata?: {
      session_id?: string;
      device_type?: string;
    };
  };
}

class SapienEventClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private baseUrl: string, private accessToken: string) {
    super();
  }

  connect(): void {
    const wsUrl = `${this.baseUrl}/ws/events?token=${this.accessToken}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Connected to Sapien ESL');
      this.reconnectAttempts = 0;
      this.subscribe('user.availability.update');
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as UserAvailabilityPayload;
        this.handleEvent(payload);
      } catch (error) {
        console.error('Failed to parse event:', error);
      }
    };

    this.ws.onclose = () => {
      this.handleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private subscribe(eventType: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        channel: 'sapien.events.availability',
        event_types: [eventType]
      }));
    }
  }

  private handleEvent(payload: UserAvailabilityPayload): void {
    if (payload.event_type === 'user.availability.update') {
      this.emit('userAvailabilityUpdate', payload);
      
      // Emit specific status events
      const status = payload.data.availability.status;
      this.emit(`user:${status}`, payload);
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    } else {
      this.emit('connectionFailed');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage Example
const client = new SapienEventClient('wss://api.sapien.example.com', 'your-access-token');

client.on('userAvailabilityUpdate', (payload: UserAvailabilityPayload) => {
  const { user_id, availability } = payload.data;
  
  console.log(`User ${user_id} is now ${availability.status}`);
  
  if (availability.custom_message) {
    console.log(`Status message: ${availability.custom_message}`);
  }
  
  // Update UI
  updateUserPresenceIndicator(user_id, availability.status);
});

client.on('user:available', (payload: UserAvailabilityPayload) => {
  // Handle user coming online
  showToast(`${payload.data.user_id} is now available`);
});

client.connect();
```

### Python - Event Consumer

```python
import json
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import logging

logger = logging.getLogger(__name__)


class AvailabilityStatus(Enum):
    AVAILABLE = "available"
    AWAY = "away"
    BUSY = "busy"
    DO_NOT_DISTURB = "do_not_disturb"
    OFFLINE = "offline"


@dataclass
class UserAvailability:
    status: AvailabilityStatus
    previous_status: Optional[AvailabilityStatus]
    changed_at: datetime
    expires_at: Optional[datetime]
    custom_message: Optional[str]


@dataclass
class UserAvailabilityEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    user_id: str
    organization_id: str
    availability: UserAvailability
    trigger_type: str
    trigger_source: str

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "UserAvailabilityEvent":
        data = payload["data"]
        avail = data["availability"]
        
        return cls(
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            timestamp=datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")),
            user_id=data["user_id"],
            organization_id=data["organization_id"],
            availability=UserAvailability(
                status=AvailabilityStatus(avail["status"]),
                previous_status=AvailabilityStatus(avail["previous_status"]) if avail.get("previous_status") else None,
                changed_at=datetime.fromisoformat(avail["changed_at"].replace("Z", "+00:00")),
                expires_at=datetime.fromisoformat(avail["expires_at"].replace("Z", "+00:00")) if avail.get("expires_at") else None,
                custom_message=avail.get("custom_message")
            ),
            trigger_type=data.get("trigger", {}).get("type", "unknown"),
            trigger_source=data.get("trigger", {}).get("source", "unknown")
        )


class SapienEventConsumer:
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.access_token = access_token
        self.handlers: Dict[str, list[Callable]] = {}
        self._running = False

    def on_availability_update(self, handler: Callable[[UserAvailabilityEvent], None]):
        """Register a handler for availability update events."""
        event_type = "user.availability.update"
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        return handler

    async def connect(self):
        """Establish WebSocket connection and start consuming events."""
        self._running = True
        ws_url = f"{self.base_url}/ws/events"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, headers=headers) as ws:
                # Subscribe to availability events
                await ws.send_json({
                    "action": "subscribe",
                    "channel": "sapien.events.availability",
                    "event_types": ["user.availability.update"]
                })

                logger.info("Connected to Sapien ESL, listening for events...")

                async for msg in ws:
                    if not self._running:
                        break
                        
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._process_message(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break

    async def _process_message(self, message: str):
        """Process incoming WebSocket message."""
        try:
            payload = json.loads(message)
            event_type = payload.get("event_type")
            
            if event_type in self.handlers:
                event = UserAvailabilityEvent.from_payload(payload)
                for handler in self.handlers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")

    def stop(self):
        """Stop the event consumer."""
        self._running = False


# Usage Example
async def main():
    consumer = SapienEventConsumer(
        base_url="wss://api.sapien.example.com",
        access_token="your-access-token"
    )

    @consumer.on_availability_update
    async def handle_availability(event: UserAvailabilityEvent):
        logger.info(
            f"User {event.user_id} changed status: "
            f"{event.availability.previous_status} -> {event.availability.status}"
        )
        
        # React to specific status changes
        if event.availability.status == AvailabilityStatus.AVAILABLE:
            if event.availability.previous_status == AvailabilityStatus.OFFLINE:
                await notify_team_member_online(event.user_id)
        
        elif event.availability.status == AvailabilityStatus.DO_NOT_DISTURB:
            await pause_notifications_for_user(event.user_id)
        
        # Handle status expiration
        if event.availability.expires_at:
            logger.info(
                f"Status will expire at {event.availability.expires_at}"
            )

    await consumer.connect()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

### Event Handling

1. **Idempotency**: Design handlers to be idempotent since events may be delivered more than once
2. **Event Ordering**: Don't assume events arrive in order; use `changed_at` timestamp for sequencing
3. **Error Handling**: Implement retry logic with exponential backoff for failed processing
4. **Validation**: Always validate the `version` field to handle schema changes gracefully

### Performance Considerations

1. **Batch Processing**: For high-volume scenarios, batch database updates
2. **Caching**: Cache user presence locally and update asynchronously
3. **Connection Pooling**: Reuse WebSocket connections across components
4. **Selective Subscription**: Subscribe only to relevant organization channels

### Security

1. **Token Refresh**: Implement automatic access token refresh before expiration
2. **Audit Logging**: Log all status changes with `actor_id` for compliance
3. **Rate Limiting**: Respect rate limits to avoid service disruption

---

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Events not received | Invalid subscription | Verify channel name and event types |
| Duplicate events | At-least-once delivery | Implement idempotent handlers |
| Stale status | Cache not updated | Check event processing pipeline |
| Connection drops | Token expired | Implement token refresh mechanism |
| Missing fields | Schema version mismatch | Check `version` field and update handlers |

---

## Related Documentation

- [OAuth2 Authentication Guide](./oauth2-authentication.md)
- [ESL Event System Overview](./esl-overview.md)
- [Rate Limiting Configuration](./rate-limiting.md)
- [Person Entity API Reference](./api/person.md)