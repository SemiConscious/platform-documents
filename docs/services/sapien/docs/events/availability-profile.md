# Availability Profile Events

## Overview

The `SapienEvent::AvailabilityProfileUpdate` event is a critical component of Sapien's ESL (Event Streaming Layer) system, providing real-time notifications when availability profiles for entities (Person, Pet, Toy) are modified. This event enables downstream systems to react immediately to changes in entity availability, supporting use cases such as scheduling, resource allocation, and status synchronization across distributed systems.

This documentation provides comprehensive guidance on understanding, consuming, and handling availability profile events within your applications.

---

## Event Description

### What is an Availability Profile?

An availability profile represents the temporal availability status of an entity within the Sapien system. Each profile contains information about:

- **Entity identification**: The specific Person, Pet, or Toy the profile belongs to
- **Availability windows**: Time ranges during which the entity is available
- **Status indicators**: Current availability state (available, busy, offline, etc.)
- **Metadata**: Additional context such as location, capacity, or special conditions

### Event Purpose

The `SapienEvent::AvailabilityProfileUpdate` event serves several key purposes:

1. **Real-time Synchronization**: Keeps external systems synchronized with the latest availability data
2. **Event-Driven Architecture**: Enables loosely-coupled integrations without polling
3. **Audit Trail**: Provides a record of all availability changes for compliance and debugging
4. **Workflow Triggering**: Initiates automated workflows based on availability changes

### Event Characteristics

| Property | Value |
|----------|-------|
| Event Name | `SapienEvent::AvailabilityProfileUpdate` |
| Event Type | Domain Event |
| Delivery | At-least-once |
| Ordering | Per-entity guaranteed |
| Retention | 7 days (configurable) |
| Max Payload Size | 64KB |

---

## Trigger Conditions

The `AvailabilityProfileUpdate` event is emitted under the following conditions:

### Primary Triggers

#### 1. Direct Profile Modification

When an availability profile is explicitly updated through the API:

```php
// PHP - Sapien API endpoint that triggers the event
// PUT /api/v1/availability-profiles/{profileId}

$profile->setStatus('available');
$profile->setAvailabilityWindows($newWindows);
$entityManager->flush();

// Event is automatically dispatched after successful persistence
```

```python
# Python - External service making the API call
import requests

response = requests.put(
    "https://api.sapien.example.com/api/v1/availability-profiles/prof_12345",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "status": "available",
        "availability_windows": [
            {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T17:00:00Z"}
        ]
    }
)
```

#### 2. Entity Status Changes

When the parent entity (Person, Pet, or Toy) undergoes a status change that affects availability:

- Entity activation/deactivation
- Entity soft deletion
- Organization membership changes

#### 3. Scheduled Transitions

When automated processes trigger availability transitions:

- Calendar-based availability windows opening/closing
- Recurring schedule execution
- Time-based status expirations

#### 4. Cascading Updates

When related entities trigger availability recalculations:

- Group membership changes affecting individual availability
- Resource pool reallocation
- Dependency chain updates

### Trigger Matrix

| Action | Event Emitted | Condition |
|--------|---------------|-----------|
| Create availability profile | ✅ Yes | Always |
| Update availability windows | ✅ Yes | When windows change |
| Update status | ✅ Yes | When status changes |
| Delete availability profile | ✅ Yes | Emits with `deleted: true` |
| Read availability profile | ❌ No | Read operations don't trigger |
| No-op update (same values) | ❌ No | Deduplication prevents emission |

---

## Payload Schema

### JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://sapien.example.com/schemas/availability-profile-update-v1.json",
  "title": "AvailabilityProfileUpdate",
  "type": "object",
  "required": ["event_id", "event_type", "timestamp", "version", "data"],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this event instance"
    },
    "event_type": {
      "type": "string",
      "const": "SapienEvent::AvailabilityProfileUpdate",
      "description": "Event type identifier"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of when the event occurred"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$",
      "description": "Schema version for this event type"
    },
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Correlation ID for request tracing"
    },
    "data": {
      "type": "object",
      "required": ["profile_id", "entity_type", "entity_id", "organization_id", "current_state"],
      "properties": {
        "profile_id": {
          "type": "string",
          "pattern": "^prof_[a-zA-Z0-9]{24}$",
          "description": "Unique availability profile identifier"
        },
        "entity_type": {
          "type": "string",
          "enum": ["person", "pet", "toy"],
          "description": "Type of entity this profile belongs to"
        },
        "entity_id": {
          "type": "string",
          "description": "Identifier of the associated entity"
        },
        "organization_id": {
          "type": "string",
          "description": "Organization owning this profile"
        },
        "current_state": {
          "$ref": "#/definitions/ProfileState"
        },
        "previous_state": {
          "$ref": "#/definitions/ProfileState",
          "description": "Previous state (null for new profiles)"
        },
        "change_metadata": {
          "$ref": "#/definitions/ChangeMetadata"
        }
      }
    }
  },
  "definitions": {
    "ProfileState": {
      "type": "object",
      "required": ["status", "availability_windows"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["available", "busy", "offline", "pending", "blocked"]
        },
        "availability_windows": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/AvailabilityWindow"
          }
        },
        "capacity": {
          "type": "integer",
          "minimum": 0,
          "description": "Available capacity units"
        },
        "location": {
          "$ref": "#/definitions/Location"
        },
        "tags": {
          "type": "array",
          "items": {"type": "string"}
        },
        "custom_attributes": {
          "type": "object",
          "additionalProperties": true
        }
      }
    },
    "AvailabilityWindow": {
      "type": "object",
      "required": ["start", "end"],
      "properties": {
        "start": {
          "type": "string",
          "format": "date-time"
        },
        "end": {
          "type": "string",
          "format": "date-time"
        },
        "recurring": {
          "type": "boolean",
          "default": false
        },
        "recurrence_rule": {
          "type": "string",
          "description": "RRULE format recurrence specification"
        }
      }
    },
    "Location": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["physical", "virtual", "hybrid"]
        },
        "identifier": {
          "type": "string"
        },
        "coordinates": {
          "type": "object",
          "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"}
          }
        }
      }
    },
    "ChangeMetadata": {
      "type": "object",
      "properties": {
        "changed_by": {
          "type": "string",
          "description": "User or system identifier that made the change"
        },
        "change_reason": {
          "type": "string"
        },
        "source": {
          "type": "string",
          "enum": ["api", "scheduler", "sync", "admin", "system"]
        },
        "request_id": {
          "type": "string"
        }
      }
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID | Yes | Globally unique event identifier for deduplication |
| `event_type` | String | Yes | Always `SapienEvent::AvailabilityProfileUpdate` |
| `timestamp` | DateTime | Yes | UTC timestamp of event creation |
| `version` | String | Yes | Schema version (current: `1.0`) |
| `correlation_id` | UUID | No | Links related events across services |
| `data.profile_id` | String | Yes | Profile identifier with `prof_` prefix |
| `data.entity_type` | Enum | Yes | One of: `person`, `pet`, `toy` |
| `data.entity_id` | String | Yes | ID of the entity owning the profile |
| `data.organization_id` | String | Yes | Owning organization for multi-tenancy |
| `data.current_state` | Object | Yes | Current profile state after update |
| `data.previous_state` | Object | No | State before update (null for creates) |
| `data.change_metadata` | Object | No | Additional context about the change |

---

## Example Payloads

### Example 1: Status Update (Available → Busy)

```json
{
  "event_id": "e7b8c9d0-1234-5678-9abc-def012345678",
  "event_type": "SapienEvent::AvailabilityProfileUpdate",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "version": "1.0",
  "correlation_id": "req_abc123def456",
  "data": {
    "profile_id": "prof_5f8d3a2b1c9e7f6d4a3b2c1d",
    "entity_type": "person",
    "entity_id": "per_7a8b9c0d1e2f3a4b5c6d7e8f",
    "organization_id": "org_1234567890abcdef",
    "current_state": {
      "status": "busy",
      "availability_windows": [],
      "capacity": 0,
      "location": {
        "type": "physical",
        "identifier": "office-nyc-floor3"
      },
      "tags": ["senior", "developer", "team-alpha"]
    },
    "previous_state": {
      "status": "available",
      "availability_windows": [
        {
          "start": "2024-01-15T09:00:00.000Z",
          "end": "2024-01-15T17:00:00.000Z",
          "recurring": false
        }
      ],
      "capacity": 1,
      "location": {
        "type": "physical",
        "identifier": "office-nyc-floor3"
      },
      "tags": ["senior", "developer", "team-alpha"]
    },
    "change_metadata": {
      "changed_by": "user_9f8e7d6c5b4a3210",
      "change_reason": "Meeting scheduled",
      "source": "api",
      "request_id": "req_abc123def456"
    }
  }
}
```

### Example 2: New Profile Creation

```json
{
  "event_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "event_type": "SapienEvent::AvailabilityProfileUpdate",
  "timestamp": "2024-01-15T08:00:00.000Z",
  "version": "1.0",
  "data": {
    "profile_id": "prof_newprofile123456789012",
    "entity_type": "pet",
    "entity_id": "pet_fluffy123456789012345",
    "organization_id": "org_petcare_services_001",
    "current_state": {
      "status": "available",
      "availability_windows": [
        {
          "start": "2024-01-15T08:00:00.000Z",
          "end": "2024-01-15T18:00:00.000Z",
          "recurring": true,
          "recurrence_rule": "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
        }
      ],
      "capacity": 1,
      "location": {
        "type": "physical",
        "identifier": "shelter-main-kennel-12"
      },
      "tags": ["dog", "medium-size", "friendly", "vaccinated"],
      "custom_attributes": {
        "breed": "Golden Retriever",
        "age_years": 3,
        "special_needs": false
      }
    },
    "previous_state": null,
    "change_metadata": {
      "changed_by": "system",
      "change_reason": "Initial profile creation",
      "source": "sync"
    }
  }
}
```

### Example 3: Profile Deletion

```json
{
  "event_id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "event_type": "SapienEvent::AvailabilityProfileUpdate",
  "timestamp": "2024-01-15T23:59:59.000Z",
  "version": "1.0",
  "data": {
    "profile_id": "prof_deleted_profile_00001",
    "entity_type": "toy",
    "entity_id": "toy_blockset_premium_12345",
    "organization_id": "org_toy_rental_service",
    "current_state": {
      "status": "offline",
      "availability_windows": [],
      "deleted": true,
      "deleted_at": "2024-01-15T23:59:59.000Z"
    },
    "previous_state": {
      "status": "available",
      "availability_windows": [
        {
          "start": "2024-01-01T00:00:00.000Z",
          "end": "2024-12-31T23:59:59.000Z",
          "recurring": false
        }
      ],
      "capacity": 5,
      "tags": ["educational", "ages-5-plus", "building-blocks"]
    },
    "change_metadata": {
      "changed_by": "admin_inventory_manager",
      "change_reason": "Product discontinued",
      "source": "admin"
    }
  }
}
```

### Example 4: Recurring Schedule Update

```json
{
  "event_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
  "event_type": "SapienEvent::AvailabilityProfileUpdate",
  "timestamp": "2024-01-15T06:00:00.000Z",
  "version": "1.0",
  "data": {
    "profile_id": "prof_consultant_weekly_001",
    "entity_type": "person",
    "entity_id": "per_jane_smith_consultant",
    "organization_id": "org_consulting_firm_abc",
    "current_state": {
      "status": "available",
      "availability_windows": [
        {
          "start": "2024-01-15T09:00:00.000Z",
          "end": "2024-01-15T12:00:00.000Z",
          "recurring": true,
          "recurrence_rule": "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20241231T235959Z"
        },
        {
          "start": "2024-01-15T14:00:00.000Z",
          "end": "2024-01-15T17:00:00.000Z",
          "recurring": true,
          "recurrence_rule": "RRULE:FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=20241231T235959Z"
        }
      ],
      "capacity": 3,
      "location": {
        "type": "hybrid",
        "identifier": "remote-or-office-chicago"
      },
      "tags": ["consultant", "senior", "finance-specialty"],
      "custom_attributes": {
        "hourly_rate": 250,
        "timezone": "America/Chicago",
        "languages": ["en", "es"]
      }
    },
    "previous_state": {
      "status": "available",
      "availability_windows": [
        {
          "start": "2024-01-15T09:00:00.000Z",
          "end": "2024-01-15T17:00:00.000Z",
          "recurring": true,
          "recurrence_rule": "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
        }
      ],
      "capacity": 1,
      "location": {
        "type": "physical",
        "identifier": "office-chicago-main"
      },
      "tags": ["consultant", "senior", "finance-specialty"]
    },
    "change_metadata": {
      "changed_by": "user_jane_smith",
      "change_reason": "Updated schedule for Q1 2024",
      "source": "api",
      "request_id": "req_schedule_update_001"
    }
  }
}
```

---

## Handling Examples

### PHP (Symfony) Event Consumer

```php
<?php

namespace App\EventSubscriber;

use App\Event\SapienAvailabilityProfileUpdateEvent;
use App\Service\AvailabilityService;
use App\Service\NotificationService;
use Psr\Log\LoggerInterface;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

class AvailabilityProfileUpdateSubscriber implements EventSubscriberInterface
{
    private AvailabilityService $availabilityService;
    private NotificationService $notificationService;
    private LoggerInterface $logger;

    public function __construct(
        AvailabilityService $availabilityService,
        NotificationService $notificationService,
        LoggerInterface $logger
    ) {
        $this->availabilityService = $availabilityService;
        $this->notificationService = $notificationService;
        $this->logger = $logger;
    }

    public static function getSubscribedEvents(): array
    {
        return [
            SapienAvailabilityProfileUpdateEvent::NAME => [
                ['onAvailabilityProfileUpdate', 10],
                ['notifyStakeholders', 5],
            ],
        ];
    }

    public function onAvailabilityProfileUpdate(SapienAvailabilityProfileUpdateEvent $event): void
    {
        $payload = $event->getPayload();
        $data = $payload['data'];
        
        $this->logger->info('Processing availability profile update', [
            'event_id' => $payload['event_id'],
            'profile_id' => $data['profile_id'],
            'entity_type' => $data['entity_type'],
        ]);

        try {
            // Handle based on entity type
            match ($data['entity_type']) {
                'person' => $this->handlePersonAvailability($data),
                'pet' => $this->handlePetAvailability($data),
                'toy' => $this->handleToyAvailability($data),
            };

            // Check for deleted profiles
            if (isset($data['current_state']['deleted']) && $data['current_state']['deleted']) {
                $this->handleProfileDeletion($data);
                return;
            }

            // Process status transitions
            $this->processStatusTransition($data);
            
        } catch (\Exception $e) {
            $this->logger->error('Failed to process availability update', [
                'event_id' => $payload['event_id'],
                'error' => $e->getMessage(),
            ]);
            throw $e;
        }
    }

    private function handlePersonAvailability(array $data): void
    {
        $currentStatus = $data['current_state']['status'];
        $previousStatus = $data['previous_state']['status'] ?? null;

        if ($previousStatus === 'available' && $currentStatus === 'busy') {
            // Person became unavailable - update scheduling system
            $this->availabilityService->blockSchedulingSlots(
                $data['entity_id'],
                $data['current_state']['availability_windows']
            );
        }

        // Update capacity tracking
        if (isset($data['current_state']['capacity'])) {
            $this->availabilityService->updateCapacity(
                $data['entity_id'],
                $data['current_state']['capacity']
            );
        }
    }

    private function handlePetAvailability(array $data): void
    {
        // Pet-specific logic (e.g., adoption availability)
        $this->availabilityService->updatePetAvailability(
            $data['entity_id'],
            $data['current_state']
        );
    }

    private function handleToyAvailability(array $data): void
    {
        // Toy-specific logic (e.g., rental availability)
        $this->availabilityService->updateInventoryStatus(
            $data['entity_id'],
            $data['current_state']
        );
    }

    private function processStatusTransition(array $data): void
    {
        $transitions = [
            'available_to_busy' => fn() => $this->onBecomeBusy($data),
            'busy_to_available' => fn() => $this->onBecomeAvailable($data),
            'any_to_offline' => fn() => $this->onGoOffline($data),
        ];

        $currentStatus = $data['current_state']['status'];
        $previousStatus = $data['previous_state']['status'] ?? 'none';

        $transitionKey = "{$previousStatus}_to_{$currentStatus}";
        
        if (isset($transitions[$transitionKey])) {
            $transitions[$transitionKey]();
        } elseif ($currentStatus === 'offline') {
            $transitions['any_to_offline']();
        }
    }

    public function notifyStakeholders(SapienAvailabilityProfileUpdateEvent $event): void
    {
        $data = $event->getPayload()['data'];
        
        // Send notifications for significant changes
        if ($this->isSignificantChange($data)) {
            $this->notificationService->sendAvailabilityNotification(
                $data['organization_id'],
                $data['entity_type'],
                $data['entity_id'],
                $data['current_state']
            );
        }
    }

    private function isSignificantChange(array $data): bool
    {
        // Define what constitutes a "significant" change
        $previousStatus = $data['previous_state']['status'] ?? null;
        $currentStatus = $data['current_state']['status'];

        return $previousStatus !== $currentStatus 
            || isset($data['current_state']['deleted']);
    }
}
```

### Python Event Consumer (Using RabbitMQ)

```python
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

import pika
from pika.adapters.blocking_connection import BlockingChannel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityType(Enum):
    PERSON = "person"
    PET = "pet"
    TOY = "toy"


class AvailabilityStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    PENDING = "pending"
    BLOCKED = "blocked"


@dataclass
class AvailabilityWindow:
    start: datetime
    end: datetime
    recurring: bool = False
    recurrence_rule: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AvailabilityWindow":
        return cls(
            start=datetime.fromisoformat(data["start"].replace("Z", "+00:00")),
            end=datetime.fromisoformat(data["end"].replace("Z", "+00:00")),
            recurring=data.get("recurring", False),
            recurrence_rule=data.get("recurrence_rule"),
        )


@dataclass
class ProfileState:
    status: AvailabilityStatus
    availability_windows: List[AvailabilityWindow]
    capacity: Optional[int] = None
    location: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    deleted: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileState":
        return cls(
            status=AvailabilityStatus(data["status"]),
            availability_windows=[
                AvailabilityWindow.from_dict(w)
                for w in data.get("availability_windows", [])
            ],
            capacity=data.get("capacity"),
            location=data.get("location"),
            tags=data.get("tags"),
            custom_attributes=data.get("custom_attributes"),
            deleted=data.get("deleted", False),
        )


@dataclass
class AvailabilityProfileUpdateEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    version: str
    profile_id: str
    entity_type: EntityType
    entity_id: str
    organization_id: str
    current_state: ProfileState
    previous_state: Optional[ProfileState]
    correlation_id: Optional[str] = None
    change_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_json(cls, json_data: str) -> "AvailabilityProfileUpdateEvent":
        data = json.loads(json_data)
        payload = data["data"]
        
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")
            ),
            version=data["version"],
            correlation_id=data.get("correlation_id"),
            profile_id=payload["profile_id"],
            entity_type=EntityType(payload["entity_type"]),
            entity_id=payload["entity_id"],
            organization_id=payload["organization_id"],
            current_state=ProfileState.from_dict(payload["current_state"]),
            previous_state=(
                ProfileState.from_dict(payload["previous_state"])
                if payload.get("previous_state")
                else None
            ),
            change_metadata=payload.get("change_metadata"),
        )


class AvailabilityProfileEventHandler:
    """Handler for processing availability profile update events."""

    def __init__(self, db_session, notification_service):
        self.db_session = db_session
        self.notification_service = notification_service
        self._processed_events: set = set()

    def handle(self, event: AvailabilityProfileUpdateEvent) -> bool:
        """
        Process an availability profile update event.
        
        Returns True if processed successfully, False otherwise.
        """
        # Idempotency check
        if event.event_id in self._processed_events:
            logger.info(f"Skipping duplicate event: {event.event_id}")
            return True

        logger.info(
            f"Processing event {event.event_id} for profile {event.profile_id}"
        )

        try:
            # Handle deletion
            if event.current_state.deleted:
                return self._handle_deletion(event)

            # Handle based on entity type
            handlers = {
                EntityType.PERSON: self._handle_person_availability,
                EntityType.PET: self._handle_pet_availability,
                EntityType.TOY: self._handle_toy_availability,
            }

            handler = handlers.get(event.entity_type)
            if handler:
                handler(event)

            # Process status transition
            self._process_status_transition(event)

            # Mark as processed
            self._processed_events.add(event.event_id)
            
            return True

        except Exception as e:
            logger.error(
                f"Failed to process event {event.event_id}: {str(e)}",
                exc_info=True
            )
            return False

    def _handle_person_availability(
        self, event: AvailabilityProfileUpdateEvent
    ) -> None:
        """Handle person-specific availability logic."""
        logger.info(f"Updating person availability for {event.entity_id}")
        
        # Update scheduling system
        if event.current_state.status == AvailabilityStatus.AVAILABLE:
            self._update_available_slots(event)
        elif event.current_state.status == AvailabilityStatus.BUSY:
            self._block_slots(event)

    def _handle_pet_availability(
        self, event: AvailabilityProfileUpdateEvent
    ) -> None:
        """Handle pet-specific availability logic."""
        logger.info(f"Updating pet availability for {event.entity_id}")
        
        # Update adoption/foster availability
        custom_attrs = event.current_state.custom_attributes or {}
        if custom_attrs.get("special_needs"):
            self._flag_special_needs_pet(event)

    def _handle_toy_availability(
        self, event: AvailabilityProfileUpdateEvent
    ) -> None:
        """Handle toy-specific availability logic."""
        logger.info(f"Updating toy availability for {event.entity_id}")
        
        # Update inventory management
        capacity = event.current_state.capacity or 0
        if capacity == 0:
            self._mark_out_of_stock(event)

    def _process_status_transition(
        self, event: AvailabilityProfileUpdateEvent
    ) -> None:
        """Process status transitions and trigger side effects."""
        current = event.current_state.status
        previous = (
            event.previous_state.status
            if event.previous_state
            else None
        )

        if previous != current:
            logger.info(
                f"Status transition: {previous} -> {current} "
                f"for {event.entity_id}"
            )
            
            # Notify stakeholders of status change
            self.notification_service.send_status_change_notification(
                entity_id=event.entity_id,
                entity_type=event.entity_type.value,
                old_status=previous.value if previous else "none",
                new_status=current.value,
                organization_id=event.organization_id,
            )

    def _handle_deletion(
        self, event: AvailabilityProfileUpdateEvent
    ) -> bool:
        """Handle profile deletion."""
        logger.info(f"Processing deletion for profile {event.profile_id}")
        
        # Clean up related resources
        self._cleanup_scheduled_slots(event.entity_id)
        self._archive_profile_history(event.profile_id)
        
        return True


class AvailabilityEventConsumer:
    """RabbitMQ consumer for availability profile events."""

    QUEUE_NAME = "sapien.availability.profile.updates"
    EXCHANGE_NAME = "sapien.events"
    ROUTING_KEY = "availability.profile.#"

    def __init__(
        self,
        handler: AvailabilityProfileEventHandler,
        rabbitmq_url: str = "amqp://guest:guest@localhost:5672/",
    ):
        self.handler = handler
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None

    def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        parameters = pika.URLParameters(self.rabbitmq_url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declare exchange and queue
        self.channel.exchange_declare(
            exchange=self.EXCHANGE_NAME,
            exchange_type="topic",
            durable=True,
        )

        self.channel.queue_declare(
            queue=self.QUEUE_NAME,
            durable=True,
            arguments={
                "x-dead-letter-exchange": f"{self.EXCHANGE_NAME}.dlx",
                "x-message-ttl": 604800000,  # 7 days
            },
        )

        self.channel.queue_bind(
            exchange=self.EXCHANGE_NAME,
            queue=self.QUEUE_NAME,
            routing_key=self.ROUTING_KEY,
        )

        logger.info(f"Connected to RabbitMQ, consuming from {self.QUEUE_NAME}")

    def start_consuming(self) -> None:
        """Start consuming messages."""
        if not self.channel:
            self.connect()

        self.channel.basic_qos(prefetch_count=10)
        self.channel.basic_consume(
            queue=self.QUEUE_NAME,
            on_message_callback=self._on_message,
        )

        logger.info("Starting to consume availability profile events...")
        self.channel.start_consuming()

    def _on_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        body: bytes,
    ) -> None:
        """Process incoming message."""
        try:
            event = AvailabilityProfileUpdateEvent.from_json(body.decode())
            
            if self.handler.handle(event):
                channel.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # Requeue for retry
                channel.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=True,
                )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            # Don't requeue malformed messages
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )


# Usage example
if __name__ == "__main__":
    from your_app.services import get_db_session, get_notification_service

    db_session = get_db_session()
    notification_service = get_notification_service()

    handler = AvailabilityProfileEventHandler(db_session, notification_service)
    consumer = AvailabilityEventConsumer(handler)

    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
```

### JavaScript/TypeScript Event Consumer (Node.js)

```typescript
import { EventEmitter } from 'events';
import * as amqp from 'amqplib';

// Type definitions
interface AvailabilityWindow {
  start: string;
  end: string;
  recurring: boolean;
  recurrence_rule?: string;
}

interface Location {
  type: 'physical' | 'virtual' | 'hybrid';
  identifier: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

interface ProfileState {
  status: 'available' | 'busy' | 'offline' | 'pending' | 'blocked';
  availability_windows: AvailabilityWindow[];
  capacity?: number;
  location?: Location;
  tags?: string[];
  custom_attributes?: Record<string, unknown>;
  deleted?: boolean;
  deleted_at?: string;
}

interface ChangeMetadata {
  changed_by: string;
  change_reason?: string;
  source: 'api' | 'scheduler' | 'sync' | 'admin' | 'system';
  request_id?: string;
}

interface AvailabilityProfileUpdatePayload {
  event_id: string;
  event_type: 'SapienEvent::AvailabilityProfileUpdate';
  timestamp: string;
  version: string;
  correlation_id?: string;
  data: {
    profile_id: string;
    entity_type: 'person' | 'pet' | 'toy';
    entity_id: string;
    organization_id: string;
    current_state: ProfileState;
    previous_state?: ProfileState;
    change_metadata?: ChangeMetadata;
  };
}

// Event handler class
class AvailabilityProfileEventHandler extends EventEmitter {
  private processedEvents: Set<string> = new Set();
  private maxCacheSize: number = 10000;

  constructor(
    private readonly schedulingService: SchedulingService,
    private readonly notificationService: NotificationService,
    private readonly logger: Logger
  ) {
    super();
  }

  async handle(payload: AvailabilityProfileUpdatePayload): Promise<void> {
    const { event_id, data } = payload;

    // Idempotency check
    if (this.processedEvents.has(event_id)) {
      this.logger.debug(`Skipping duplicate event: ${event_id}`);
      return;
    }

    this.logger.info('Processing availability profile update', {
      event_id,
      profile_id: data.profile_id,
      entity_type: data.entity_type,
      status: data.current_state.status,
    });

    try {
      // Handle deletion
      if (data.current_state.deleted) {
        await this.handleDeletion(data);
        this.markProcessed(event_id);
        return;
      }

      // Route to entity-specific handler
      switch (data.entity_type) {
        case 'person':
          await this.handlePersonAvailability(data);
          break;
        case 'pet':
          await this.handlePetAvailability(data);
          break;
        case 'toy':
          await this.handleToyAvailability(data);
          break;
      }

      // Process status transitions
      await this.processStatusTransition(data);

      // Emit internal event for other listeners
      this.emit('availability:updated', {
        entityType: data.entity_type,
        entityId: data.entity_id,
        status: data.current_state.status,
        timestamp: payload.timestamp,
      });

      this.markProcessed(event_id);
    } catch (error) {
      this.logger.error('Failed to process availability update', {
        event_id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  private async handlePersonAvailability(
    data: AvailabilityProfileUpdatePayload['data']
  ): Promise<void> {
    const { entity_id, current_state, previous_state } = data;

    // Update scheduling slots based on availability windows
    if (current_state.availability_windows.length > 0) {
      await this.schedulingService.updateAvailableSlots(
        entity_id,
        current_state.availability_windows.map((w) => ({
          start: new Date(w.start),
          end: new Date(w.end),
          recurring: w.recurring,
          rrule: w.recurrence_rule,
        }))
      );
    }

    // Handle capacity changes
    if (
      current_state.capacity !== undefined &&
      current_state.capacity !== previous_state?.capacity
    ) {
      await this.schedulingService.updateCapacity(
        entity_id,
        current_state.capacity
      );
    }
  }

  private async handlePetAvailability(
    data: AvailabilityProfileUpdatePayload['data']
  ): Promise<void> {
    const { entity_id, current_state } = data;

    // Update adoption/foster availability
    if (current_state.status === 'available') {
      await this.notificationService.notifyAvailableForAdoption(
        entity_id,
        current_state.location,
        current_state.custom_attributes
      );
    }
  }

  private async handleToyAvailability(
    data: AvailabilityProfileUpdatePayload['data']
  ): Promise<void> {
    const { entity_id, current_state, organization_id } = data;

    // Update inventory status
    if (current_state.capacity === 0) {
      await this.notificationService.notifyOutOfStock(
        organization_id,
        entity_id
      );
    }
  }

  private async processStatusTransition(
    data: AvailabilityProfileUpdatePayload['data']
  ): Promise<void> {
    const currentStatus = data.current_state.status;
    const previousStatus = data.previous_state?.status;

    if (previousStatus && previousStatus !== currentStatus) {
      this.logger.info('Status transition detected', {
        entity_id: data.entity_id,
        from: previousStatus,
        to: currentStatus,
      });

      // Notify interested parties
      await this.notificationService.sendStatusChangeNotification({
        entityId: data.entity_id,
        entityType: data.entity_type,
        organizationId: data.organization_id,
        previousStatus,
        currentStatus,
        changedBy: data.change_metadata?.changed_by,
        reason: data.change_metadata?.change_reason,
      });
    }
  }

  private async handleDeletion(
    data: AvailabilityProfileUpdatePayload['data']
  ): Promise<void> {
    this.logger.info('Processing profile deletion', {
      profile_id: data.profile_id,
      entity_id: data.entity_id,
    });

    // Clean up scheduled slots
    await this.schedulingService.removeAllSlots(data.entity_id);

    // Archive for compliance
    this.emit('availability:deleted', {
      profileId: data.profile_id,
      entityId: data.entity_id,
      deletedAt: data.current_state.deleted_at,
    });
  }

  private markProcessed(eventId: string): void {
    this.processedEvents.add(eventId);

    // Prevent unbounded memory growth
    if (this.processedEvents.size > this.maxCacheSize) {
      const iterator = this.processedEvents.values();
      for (let i = 0; i < this.maxCacheSize / 2; i++) {
        this.processedEvents.delete(iterator.next().value);
      }
    }
  }
}

// RabbitMQ consumer
class AvailabilityEventConsumer {
  private connection?: amqp.Connection;
  private channel?: amqp.Channel;

  private readonly QUEUE_NAME = 'sapien.availability.profile.updates';
  private readonly EXCHANGE_NAME = 'sapien.events';
  private readonly ROUTING_KEY = 'availability.profile.#';

  constructor(
    private readonly handler: AvailabilityProfileEventHandler,
    private readonly rabbitmqUrl: string,
    private readonly logger: Logger
  ) {}

  async connect(): Promise<void> {
    this.connection = await amqp.connect(this.rabbitmqUrl);
    this.channel = await this.connection.createChannel();

    // Setup exchange and queue
    await this.channel.assertExchange(this.EXCHANGE_NAME, 'topic', {
      durable: true,
    });

    await this.channel.assertQueue(this.QUEUE_NAME, {
      durable: true,
      arguments: {
        'x-dead-letter-exchange': `${this.EXCHANGE_NAME}.dlx`,
        'x-message-ttl': 604800000, // 7 days
      },
    });

    await this.channel.bindQueue(
      this.QUEUE_NAME,
      this.EXCHANGE_NAME,
      this.ROUTING_KEY
    );

    // Set prefetch for controlled consumption
    await this.channel.prefetch(10);

    this.logger.info(`Connected to RabbitMQ, queue: ${this.QUEUE_NAME}`);
  }

  async startConsuming(): Promise<void> {
    if (!this.channel) {
      await this.connect();
    }

    this.logger.info('Starting to consume availability profile events...');

    await this.channel!.consume(
      this.QUEUE_NAME,
      async (msg) => {
        if (!msg) return;

        try {
          const payload: AvailabilityProfileUpdatePayload = JSON.parse(
            msg.content.toString()
          );

          await this.handler.handle(payload);
          this.channel!.ack(msg);
        } catch (error) {
          this.logger.error('Error processing message', {
            error: error instanceof Error ? error.message : 'Unknown',
          });

          // Requeue unless it's a parsing error
          const requeue = !(error instanceof SyntaxError);
          this.channel!.nack(msg, false, requeue);
        }
      },
      { noAck: false }
    );
  }

  async shutdown(): Promise<void> {
    await this.channel?.close();
    await this.connection?.close();
    this.logger.info('Consumer shut down gracefully');
  }
}

// Interfaces for dependencies
interface SchedulingService {
  updateAvailableSlots(
    entityId: string,
    slots: Array<{ start: Date; end: Date; recurring: boolean; rrule?: string }>
  ): Promise<void>;
  updateCapacity(entityId: string, capacity: number): Promise<void>;
  removeAllSlots(entityId: string): Promise<void>;
}

interface NotificationService {
  sendStatusChangeNotification(params: {
    entityId: string;
    entityType: string;
    organizationId: string;
    previousStatus: string;
    currentStatus: string;
    changedBy?: string;
    reason?: string;
  }): Promise<void>;
  notifyAvailableForAdoption(
    entityId: string,
    location?: Location,
    attributes?: Record<string, unknown>
  ): Promise<void>;
  notifyOutOfStock(organizationId: string, entityId: string): Promise<void>;
}

interface Logger {
  info(message: string, meta?: Record<string, unknown>): void;
  debug(message: string, meta?: Record<string, unknown>): void;
  error(message: string, meta?: Record<string, unknown>): void;
}

export {
  AvailabilityProfileEventHandler,
  AvailabilityEventConsumer,
  AvailabilityProfileUpdatePayload,
  ProfileState,
  AvailabilityWindow,
};
```

---

## Best Practices

### 1. Idempotency

Always implement idempotent event handling using the `event_id`:

```php
// PHP example
public function handle(array $event): void
{
    $eventId = $event['event_id'];
    
    if ($this->cache->has("processed:{$eventId}")) {
        return; // Already processed
    }
    
    // Process event...
    
    $this->cache->set("processed:{$eventId}", true, 86400);
}
```

### 2. Error Handling and Retries

Implement exponential backoff for transient failures:

```python
# Python example with tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def process_event(event: AvailabilityProfileUpdateEvent) -> None:
    # Processing logic here
    pass
```

### 3. Event Ordering

When processing events for the same entity, ensure proper ordering:

```typescript
// TypeScript example
class OrderedEventProcessor {
  private entityLocks: Map<string, Promise<void>> = new Map();

  async process(event: AvailabilityProfileUpdatePayload): Promise<void> {
    const entityKey = `${event.data.entity_type}:${event.data.entity_id}`;
    
    // Wait for previous event for this entity to complete
    const previousLock = this.entityLocks.get(entityKey) || Promise.resolve();
    
    const currentLock = previousLock.then(() => this.handleEvent(event));
    this.entityLocks.set(entityKey, currentLock);
    
    await currentLock;
  }
}
```

### 4. Monitoring and Alerting

Track key metrics for availability profile events:

- Event processing latency
- Failed event count
- Events per entity type
- Status transition frequencies

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Duplicate events processed | Missing idempotency check | Implement event ID tracking |
| Events arriving out of order | Network latency | Use event timestamps for ordering |
| Missing previous_state | New profile creation | Check for null before accessing |
| High latency in processing | Synchronous external calls | Use async processing with queues |

### Debug Logging

Enable detailed logging for troubleshooting:

```php
// PHP - Symfony monolog configuration
monolog:
    handlers:
        availability_events:
            type: stream
            path: '%kernel.logs_dir%/availability_events.log'
            level: debug
            channels: ['availability']
```

---

## Related Documentation

- [Sapien API Reference](/docs/api-reference)
- [Entity Management Guide](/docs/entities)
- [ESL Event System Overview](/docs/esl-events)
- [OAuth2 Authentication](/docs/authentication)
- [Rate Limiting](/docs/rate-limiting)