# Repository Layer

## Overview

The Repository Layer in the CDC Pipeline service provides a clean abstraction for data access operations against CoreDB tables. This documentation covers the repository pattern implementation, specific repository classes for key tables, and best practices for working with the data access layer in the CDC processing context.

The repository layer serves as the bridge between the CDC event processing logic and the underlying database operations, ensuring consistent data access patterns, proper error handling, and maintainable code architecture across all 12+ CoreDB tables that the pipeline monitors.

## Repository Pattern Overview

### What is the Repository Pattern?

The Repository Pattern is a design pattern that mediates between the domain/business logic layer and the data mapping layer. In the context of the CDC Pipeline service, repositories encapsulate the logic required to access data sources, providing a collection-like interface for accessing domain objects.

### Why Use Repositories in CDC Pipeline?

The CDC Pipeline processes changes from multiple CoreDB tables, each with its own schema and access requirements. The repository pattern provides several key benefits:

1. **Abstraction**: Isolates data access logic from business logic
2. **Testability**: Enables easy mocking for unit tests
3. **Consistency**: Provides uniform data access patterns across all tables
4. **Maintainability**: Centralizes query logic for easier updates
5. **Separation of Concerns**: Keeps CDC processing logic clean and focused

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CDC Event Handler                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Repository Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ GroupMapsLog│ │  Profiles   │ │       Channels          ││
│  │ Repository  │ │ Repository  │ │      Repository         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Agents    │ │   Queues    │ │     Other Tables...     ││
│  │ Repository  │ │ Repository  │ │      Repositories       ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      CoreDB (MySQL)                          │
└─────────────────────────────────────────────────────────────┘
```

### Base Repository Implementation

All repositories extend from a base repository class that provides common functionality:

```typescript
// src/repositories/base.repository.ts
import { Logger } from '@aws-lambda-powertools/logger';
import { Connection, RowDataPacket } from 'mysql2/promise';

export interface IBaseRepository<T> {
  findById(id: string | number): Promise<T | null>;
  findAll(limit?: number, offset?: number): Promise<T[]>;
  findByCondition(condition: Partial<T>): Promise<T[]>;
}

export abstract class BaseRepository<T> implements IBaseRepository<T> {
  protected readonly logger: Logger;
  protected readonly tableName: string;
  protected connection: Connection;

  constructor(connection: Connection, tableName: string) {
    this.connection = connection;
    this.tableName = tableName;
    this.logger = new Logger({ serviceName: 'cdc-pipeline', persistentLogAttributes: { repository: tableName } });
  }

  async findById(id: string | number): Promise<T | null> {
    const startTime = Date.now();
    try {
      const [rows] = await this.connection.execute<RowDataPacket[]>(
        `SELECT * FROM ${this.tableName} WHERE id = ?`,
        [id]
      );
      
      this.logger.debug('findById executed', { id, duration: Date.now() - startTime });
      return rows.length > 0 ? this.mapToEntity(rows[0]) : null;
    } catch (error) {
      this.logger.error('findById failed', { id, error });
      throw error;
    }
  }

  async findAll(limit: number = 100, offset: number = 0): Promise<T[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName} LIMIT ? OFFSET ?`,
      [limit, offset]
    );
    return rows.map(row => this.mapToEntity(row));
  }

  async findByCondition(condition: Partial<T>): Promise<T[]> {
    const keys = Object.keys(condition);
    const values = Object.values(condition);
    const whereClause = keys.map(key => `${key} = ?`).join(' AND ');
    
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName} WHERE ${whereClause}`,
      values
    );
    return rows.map(row => this.mapToEntity(row));
  }

  protected abstract mapToEntity(row: RowDataPacket): T;
}
```

## GroupMapsLog Repository

### Purpose

The GroupMapsLog Repository handles data access for the `group_maps_log` table, which tracks agent-to-group assignments and their history. This is critical for the Wallboards service to display accurate agent groupings in real-time.

### Entity Definition

```typescript
// src/entities/group-maps-log.entity.ts
export interface GroupMapsLogEntity {
  id: number;
  agentId: string;
  groupId: string;
  action: 'ADD' | 'REMOVE' | 'UPDATE';
  timestamp: Date;
  previousGroupId?: string;
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

export interface GroupMapsLogChangeEvent {
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  before: GroupMapsLogEntity | null;
  after: GroupMapsLogEntity | null;
  timestamp: Date;
  sequenceNumber: string;
}
```

### Repository Implementation

```typescript
// src/repositories/group-maps-log.repository.ts
import { BaseRepository } from './base.repository';
import { GroupMapsLogEntity, GroupMapsLogChangeEvent } from '../entities/group-maps-log.entity';
import { Connection, RowDataPacket } from 'mysql2/promise';
import { RedactionService } from '../services/redaction.service';

export class GroupMapsLogRepository extends BaseRepository<GroupMapsLogEntity> {
  private readonly redactionService: RedactionService;

  constructor(connection: Connection, redactionService: RedactionService) {
    super(connection, 'group_maps_log');
    this.redactionService = redactionService;
  }

  /**
   * Find all group mappings for a specific agent
   * @param agentId - The agent identifier
   * @returns Array of group mapping records
   */
  async findByAgentId(agentId: string): Promise<GroupMapsLogEntity[]> {
    this.logger.info('Finding group mappings by agent', { agentId });
    
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName} 
       WHERE agent_id = ? 
       ORDER BY timestamp DESC`,
      [agentId]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Find all agents currently assigned to a specific group
   * @param groupId - The group identifier
   * @returns Array of group mapping records for active assignments
   */
  async findActiveByGroupId(groupId: string): Promise<GroupMapsLogEntity[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT gml.* FROM ${this.tableName} gml
       INNER JOIN (
         SELECT agent_id, MAX(timestamp) as max_timestamp
         FROM ${this.tableName}
         WHERE group_id = ?
         GROUP BY agent_id
       ) latest ON gml.agent_id = latest.agent_id AND gml.timestamp = latest.max_timestamp
       WHERE gml.action != 'REMOVE'`,
      [groupId]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Process a CDC change event and transform for EventBridge publishing
   * @param changeEvent - The raw CDC change event
   * @returns Transformed event ready for publishing
   */
  async processChangeEvent(changeEvent: GroupMapsLogChangeEvent): Promise<Record<string, unknown>> {
    this.logger.info('Processing group maps log change event', {
      operation: changeEvent.operation,
      sequenceNumber: changeEvent.sequenceNumber
    });

    const entity = changeEvent.after || changeEvent.before;
    
    if (!entity) {
      throw new Error('Invalid change event: no entity data available');
    }

    // Apply data redaction rules
    const redactedEntity = await this.redactionService.redact(entity, 'group_maps_log');

    return {
      eventType: 'GROUP_MAPPING_CHANGED',
      operation: changeEvent.operation,
      entityId: entity.id,
      agentId: redactedEntity.agentId,
      groupId: redactedEntity.groupId,
      action: redactedEntity.action,
      timestamp: changeEvent.timestamp.toISOString(),
      metadata: {
        tableName: this.tableName,
        sequenceNumber: changeEvent.sequenceNumber,
        previousGroupId: redactedEntity.previousGroupId
      }
    };
  }

  /**
   * Get the change history for an agent within a time range
   * @param agentId - The agent identifier
   * @param startDate - Start of the time range
   * @param endDate - End of the time range
   * @returns Array of historical group mapping changes
   */
  async getAgentHistory(
    agentId: string,
    startDate: Date,
    endDate: Date
  ): Promise<GroupMapsLogEntity[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName}
       WHERE agent_id = ?
       AND timestamp BETWEEN ? AND ?
       ORDER BY timestamp ASC`,
      [agentId, startDate, endDate]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  protected mapToEntity(row: RowDataPacket): GroupMapsLogEntity {
    return {
      id: row.id,
      agentId: row.agent_id,
      groupId: row.group_id,
      action: row.action,
      timestamp: new Date(row.timestamp),
      previousGroupId: row.previous_group_id || undefined,
      metadata: row.metadata ? JSON.parse(row.metadata) : undefined,
      createdAt: new Date(row.created_at),
      updatedAt: new Date(row.updated_at)
    };
  }
}
```

### Usage Examples

```typescript
// Example: Processing a CDC event for group mapping change
import { GroupMapsLogRepository } from './repositories/group-maps-log.repository';
import { createConnection } from './database/connection';
import { RedactionService } from './services/redaction.service';

async function handleGroupMappingChange(cdcEvent: any) {
  const connection = await createConnection();
  const redactionService = new RedactionService();
  const repository = new GroupMapsLogRepository(connection, redactionService);

  try {
    // Get current active agents in the affected group
    const activeAgents = await repository.findActiveByGroupId(cdcEvent.groupId);
    
    // Process the change event for EventBridge
    const eventBridgePayload = await repository.processChangeEvent({
      operation: cdcEvent.operation,
      before: cdcEvent.beforeImage,
      after: cdcEvent.afterImage,
      timestamp: new Date(cdcEvent.timestamp),
      sequenceNumber: cdcEvent.sequenceNumber
    });

    return {
      payload: eventBridgePayload,
      affectedAgents: activeAgents.map(a => a.agentId)
    };
  } finally {
    await connection.end();
  }
}
```

## Profiles Repository

### Purpose

The Profiles Repository manages access to user profile data in CoreDB. This repository includes special handling for PII (Personally Identifiable Information) through the redaction service, ensuring compliance with data privacy requirements.

### Entity Definition

```typescript
// src/entities/profile.entity.ts
export interface ProfileEntity {
  id: string;
  externalId: string;
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber?: string;
  department?: string;
  role: string;
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  preferences: ProfilePreferences;
  createdAt: Date;
  updatedAt: Date;
  lastLoginAt?: Date;
}

export interface ProfilePreferences {
  timezone: string;
  language: string;
  notificationsEnabled: boolean;
  dashboardLayout?: Record<string, unknown>;
}

export interface ProfileChangeEvent {
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  before: ProfileEntity | null;
  after: ProfileEntity | null;
  changedFields: string[];
  timestamp: Date;
  sequenceNumber: string;
}
```

### Repository Implementation

```typescript
// src/repositories/profiles.repository.ts
import { BaseRepository } from './base.repository';
import { ProfileEntity, ProfileChangeEvent } from '../entities/profile.entity';
import { Connection, RowDataPacket } from 'mysql2/promise';
import { RedactionService, RedactionLevel } from '../services/redaction.service';
import { DynamoDBClient, PutItemCommand, GetItemCommand } from '@aws-sdk/client-dynamodb';

export class ProfilesRepository extends BaseRepository<ProfileEntity> {
  private readonly redactionService: RedactionService;
  private readonly dynamoClient: DynamoDBClient;
  private readonly stateTableName: string;

  // Fields that contain PII and require redaction
  private readonly piiFields = ['firstName', 'lastName', 'email', 'phoneNumber'];

  constructor(
    connection: Connection,
    redactionService: RedactionService,
    dynamoClient: DynamoDBClient,
    stateTableName: string
  ) {
    super(connection, 'profiles');
    this.redactionService = redactionService;
    this.dynamoClient = dynamoClient;
    this.stateTableName = stateTableName;
  }

  /**
   * Find a profile by external ID (commonly used for integrations)
   * @param externalId - External system identifier
   * @returns Profile entity or null
   */
  async findByExternalId(externalId: string): Promise<ProfileEntity | null> {
    this.logger.info('Finding profile by external ID', { externalId });
    
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName} WHERE external_id = ?`,
      [externalId]
    );
    
    return rows.length > 0 ? this.mapToEntity(rows[0]) : null;
  }

  /**
   * Find all profiles in a specific department
   * @param department - Department name
   * @param includeInactive - Whether to include inactive profiles
   * @returns Array of profile entities
   */
  async findByDepartment(
    department: string,
    includeInactive: boolean = false
  ): Promise<ProfileEntity[]> {
    const statusClause = includeInactive ? '' : "AND status = 'ACTIVE'";
    
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName} 
       WHERE department = ? ${statusClause}
       ORDER BY last_name, first_name`,
      [department]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Process a CDC change event with appropriate PII redaction
   * @param changeEvent - The raw CDC change event
   * @param redactionLevel - Level of redaction to apply
   * @returns Transformed and redacted event
   */
  async processChangeEvent(
    changeEvent: ProfileChangeEvent,
    redactionLevel: RedactionLevel = 'standard'
  ): Promise<Record<string, unknown>> {
    this.logger.info('Processing profile change event', {
      operation: changeEvent.operation,
      sequenceNumber: changeEvent.sequenceNumber,
      changedFields: changeEvent.changedFields
    });

    const entity = changeEvent.after || changeEvent.before;
    
    if (!entity) {
      throw new Error('Invalid change event: no entity data available');
    }

    // Check if any PII fields were changed
    const piiFieldsChanged = changeEvent.changedFields.some(
      field => this.piiFields.includes(field)
    );

    // Apply redaction based on level and changed fields
    const redactedEntity = await this.redactionService.redactProfile(
      entity,
      redactionLevel,
      piiFieldsChanged
    );

    // Store processing state in DynamoDB
    await this.updateProcessingState(changeEvent.sequenceNumber, entity.id);

    return {
      eventType: 'PROFILE_CHANGED',
      operation: changeEvent.operation,
      entityId: entity.id,
      externalId: redactedEntity.externalId,
      changedFields: this.filterRedactedFields(changeEvent.changedFields, redactionLevel),
      status: redactedEntity.status,
      role: redactedEntity.role,
      department: redactedEntity.department,
      timestamp: changeEvent.timestamp.toISOString(),
      metadata: {
        tableName: this.tableName,
        sequenceNumber: changeEvent.sequenceNumber,
        piiFieldsChanged
      }
    };
  }

  /**
   * Get profiles that have been recently updated
   * @param since - Timestamp to check updates from
   * @param limit - Maximum number of results
   * @returns Array of recently updated profiles
   */
  async findRecentlyUpdated(since: Date, limit: number = 100): Promise<ProfileEntity[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName}
       WHERE updated_at > ?
       ORDER BY updated_at DESC
       LIMIT ?`,
      [since, limit]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Update processing state in DynamoDB for idempotency
   */
  private async updateProcessingState(sequenceNumber: string, profileId: string): Promise<void> {
    try {
      await this.dynamoClient.send(new PutItemCommand({
        TableName: this.stateTableName,
        Item: {
          pk: { S: `PROFILE#${profileId}` },
          sk: { S: `SEQ#${sequenceNumber}` },
          processedAt: { S: new Date().toISOString() },
          ttl: { N: String(Math.floor(Date.now() / 1000) + 86400 * 7) } // 7 days TTL
        },
        ConditionExpression: 'attribute_not_exists(pk)'
      }));
    } catch (error: any) {
      if (error.name === 'ConditionalCheckFailedException') {
        this.logger.warn('Duplicate event detected', { sequenceNumber, profileId });
        throw new Error(`Duplicate event: ${sequenceNumber}`);
      }
      throw error;
    }
  }

  /**
   * Filter out redacted fields from the changed fields list
   */
  private filterRedactedFields(changedFields: string[], redactionLevel: RedactionLevel): string[] {
    if (redactionLevel === 'full') {
      return changedFields.filter(field => !this.piiFields.includes(field));
    }
    return changedFields;
  }

  protected mapToEntity(row: RowDataPacket): ProfileEntity {
    return {
      id: row.id,
      externalId: row.external_id,
      firstName: row.first_name,
      lastName: row.last_name,
      email: row.email,
      phoneNumber: row.phone_number || undefined,
      department: row.department || undefined,
      role: row.role,
      status: row.status,
      preferences: JSON.parse(row.preferences || '{}'),
      createdAt: new Date(row.created_at),
      updatedAt: new Date(row.updated_at),
      lastLoginAt: row.last_login_at ? new Date(row.last_login_at) : undefined
    };
  }
}
```

## Channels Repository

### Purpose

The Channels Repository handles data access for communication channels (voice, chat, email, etc.) in the contact center system. This repository is essential for tracking channel availability and routing configurations.

### Entity Definition

```typescript
// src/entities/channel.entity.ts
export interface ChannelEntity {
  id: string;
  name: string;
  type: 'VOICE' | 'CHAT' | 'EMAIL' | 'SMS' | 'SOCIAL';
  status: 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE';
  capacity: number;
  currentLoad: number;
  routingProfile: string;
  queueIds: string[];
  configuration: ChannelConfiguration;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChannelConfiguration {
  maxConcurrentContacts: number;
  autoAccept: boolean;
  wrapUpTime: number;
  skillRequirements?: string[];
  priority: number;
}

export interface ChannelChangeEvent {
  operation: 'INSERT' | 'UPDATE' | 'DELETE';
  before: ChannelEntity | null;
  after: ChannelEntity | null;
  timestamp: Date;
  sequenceNumber: string;
}
```

### Repository Implementation

```typescript
// src/repositories/channels.repository.ts
import { BaseRepository } from './base.repository';
import { ChannelEntity, ChannelChangeEvent } from '../entities/channel.entity';
import { Connection, RowDataPacket } from 'mysql2/promise';

export class ChannelsRepository extends BaseRepository<ChannelEntity> {
  constructor(connection: Connection) {
    super(connection, 'channels');
  }

  /**
   * Find all channels of a specific type
   * @param type - Channel type
   * @param activeOnly - Only return active channels
   * @returns Array of channel entities
   */
  async findByType(
    type: ChannelEntity['type'],
    activeOnly: boolean = true
  ): Promise<ChannelEntity[]> {
    const statusClause = activeOnly ? "AND status = 'ACTIVE'" : '';
    
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName}
       WHERE type = ? ${statusClause}
       ORDER BY priority DESC, name ASC`,
      [type]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Find channels by routing profile
   * @param routingProfile - Routing profile identifier
   * @returns Array of channel entities
   */
  async findByRoutingProfile(routingProfile: string): Promise<ChannelEntity[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName}
       WHERE routing_profile = ?
       AND status = 'ACTIVE'`,
      [routingProfile]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Find channels associated with a specific queue
   * @param queueId - Queue identifier
   * @returns Array of channel entities
   */
  async findByQueueId(queueId: string): Promise<ChannelEntity[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT c.* FROM ${this.tableName} c
       WHERE JSON_CONTAINS(c.queue_ids, ?)`,
      [JSON.stringify(queueId)]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  /**
   * Get channel capacity utilization
   * @param channelId - Channel identifier
   * @returns Utilization percentage
   */
  async getCapacityUtilization(channelId: string): Promise<number> {
    const channel = await this.findById(channelId);
    
    if (!channel) {
      throw new Error(`Channel not found: ${channelId}`);
    }

    if (channel.capacity === 0) {
      return 0;
    }

    return (channel.currentLoad / channel.capacity) * 100;
  }

  /**
   * Process a CDC change event for channels
   * @param changeEvent - The raw CDC change event
   * @returns Transformed event for EventBridge
   */
  async processChangeEvent(changeEvent: ChannelChangeEvent): Promise<Record<string, unknown>> {
    this.logger.info('Processing channel change event', {
      operation: changeEvent.operation,
      sequenceNumber: changeEvent.sequenceNumber
    });

    const entity = changeEvent.after || changeEvent.before;
    
    if (!entity) {
      throw new Error('Invalid change event: no entity data available');
    }

    // Detect significant changes
    const isCapacityChange = changeEvent.before && changeEvent.after &&
      changeEvent.before.capacity !== changeEvent.after.capacity;
    
    const isStatusChange = changeEvent.before && changeEvent.after &&
      changeEvent.before.status !== changeEvent.after.status;

    return {
      eventType: 'CHANNEL_CHANGED',
      operation: changeEvent.operation,
      entityId: entity.id,
      channelName: entity.name,
      channelType: entity.type,
      status: entity.status,
      capacity: entity.capacity,
      currentLoad: entity.currentLoad,
      routingProfile: entity.routingProfile,
      timestamp: changeEvent.timestamp.toISOString(),
      metadata: {
        tableName: this.tableName,
        sequenceNumber: changeEvent.sequenceNumber,
        isCapacityChange,
        isStatusChange,
        queueCount: entity.queueIds.length
      }
    };
  }

  /**
   * Get channels with high utilization
   * @param threshold - Utilization threshold (0-100)
   * @returns Array of high-utilization channels
   */
  async findHighUtilization(threshold: number = 80): Promise<ChannelEntity[]> {
    const [rows] = await this.connection.execute<RowDataPacket[]>(
      `SELECT * FROM ${this.tableName}
       WHERE status = 'ACTIVE'
       AND capacity > 0
       AND (current_load / capacity * 100) >= ?
       ORDER BY (current_load / capacity) DESC`,
      [threshold]
    );
    
    return rows.map(row => this.mapToEntity(row));
  }

  protected mapToEntity(row: RowDataPacket): ChannelEntity {
    return {
      id: row.id,
      name: row.name,
      type: row.type,
      status: row.status,
      capacity: row.capacity,
      currentLoad: row.current_load,
      routingProfile: row.routing_profile,
      queueIds: JSON.parse(row.queue_ids || '[]'),
      configuration: JSON.parse(row.configuration || '{}'),
      createdAt: new Date(row.created_at),
      updatedAt: new Date(row.updated_at)
    };
  }
}
```

## Common Repository Methods

### Method Reference

All repositories implement the following common methods from the base repository:

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `findById` | Find a single entity by primary key | `id: string \| number` | `Promise<T \| null>` |
| `findAll` | Find all entities with pagination | `limit?: number, offset?: number` | `Promise<T[]>` |
| `findByCondition` | Find entities matching conditions | `condition: Partial<T>` | `Promise<T[]>` |
| `processChangeEvent` | Process CDC change event | `changeEvent: ChangeEvent` | `Promise<Record<string, unknown>>` |

### Utility Methods

```typescript
// src/repositories/utils/repository-utils.ts

/**
 * Build a safe WHERE clause from conditions
 */
export function buildWhereClause(conditions: Record<string, unknown>): {
  clause: string;
  values: unknown[];
} {
  const keys = Object.keys(conditions).filter(k => conditions[k] !== undefined);
  const values = keys.map(k => conditions[k]);
  const clause = keys.length > 0 
    ? `WHERE ${keys.map(k => `${k} = ?`).join(' AND ')}`
    : '';
  
  return { clause, values };
}

/**
 * Parse JSON fields safely
 */
export function safeJsonParse<T>(json: string | null, defaultValue: T): T {
  if (!json) return defaultValue;
  try {
    return JSON.parse(json) as T;
  } catch {
    return defaultValue;
  }
}

/**
 * Convert snake_case to camelCase
 */
export function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Convert camelCase to snake_case
 */
export function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}
```

### Connection Management

```typescript
// src/database/connection-manager.ts
import { createPool, Pool, PoolConnection } from 'mysql2/promise';
import { Logger } from '@aws-lambda-powertools/logger';

const logger = new Logger({ serviceName: 'cdc-pipeline' });

let pool: Pool | null = null;

export interface ConnectionConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  connectionLimit: number;
  connectTimeout: number;
}

export async function getPool(config: ConnectionConfig): Promise<Pool> {
  if (!pool) {
    logger.info('Creating new connection pool');
    pool = createPool({
      ...config,
      waitForConnections: true,
      queueLimit: 0,
      enableKeepAlive: true,
      keepAliveInitialDelay: 10000
    });
  }
  return pool;
}

export async function getConnection(config: ConnectionConfig): Promise<PoolConnection> {
  const pool = await getPool(config);
  return pool.getConnection();
}

export async function closePool(): Promise<void> {
  if (pool) {
    logger.info('Closing connection pool');
    await pool.end();
    pool = null;
  }
}

/**
 * Execute a function within a transaction
 */
export async function withTransaction<T>(
  config: ConnectionConfig,
  fn: (connection: PoolConnection) => Promise<T>
): Promise<T> {
  const connection = await getConnection(config);
  try {
    await connection.beginTransaction();
    const result = await fn(connection);
    await connection.commit();
    return result;
  } catch (error) {
    await connection.rollback();
    throw error;
  } finally {
    connection.release();
  }
}
```

## Error Handling

### Repository Exception Hierarchy

```typescript
// src/repositories/exceptions/repository-exceptions.ts

export class RepositoryException extends Error {
  public readonly code: string;
  public readonly isRetryable: boolean;
  public readonly originalError?: Error;

  constructor(
    message: string,
    code: string,
    isRetryable: boolean = false,
    originalError?: Error
  ) {
    super(message);
    this.name = 'RepositoryException';
    this.code = code;
    this.isRetryable = isRetryable;
    this.originalError = originalError;
  }
}

export class EntityNotFoundException extends RepositoryException {
  constructor(entityType: string, identifier: string | number) {
    super(
      `${entityType} with identifier '${identifier}' was not found`,
      'ENTITY_NOT_FOUND',
      false
    );
    this.name = 'EntityNotFoundException';
  }
}

export class DuplicateEntityException extends RepositoryException {
  constructor(entityType: string, identifier: string | number) {
    super(
      `${entityType} with identifier '${identifier}' already exists`,
      'DUPLICATE_ENTITY',
      false
    );
    this.name = 'DuplicateEntityException';
  }
}

export class ConnectionException extends RepositoryException {
  constructor(message: string, originalError?: Error) {
    super(message, 'CONNECTION_ERROR', true, originalError);
    this.name = 'ConnectionException';
  }
}

export class QueryTimeoutException extends RepositoryException {
  constructor(query: string, timeout: number, originalError?: Error) {
    super(
      `Query timed out after ${timeout}ms`,
      'QUERY_TIMEOUT',
      true,
      originalError
    );
    this.name = 'QueryTimeoutException';
  }
}

export class ValidationException extends RepositoryException {
  public readonly validationErrors: Record<string, string[]>;

  constructor(entityType: string, validationErrors: Record<string, string[]>) {
    super(
      `Validation failed for ${entityType}`,
      'VALIDATION_ERROR',
      false
    );
    this.name = 'ValidationException';
    this.validationErrors = validationErrors;
  }
}
```

### Error Handling Patterns

```typescript
// src/repositories/error-handler.ts
import { Logger } from '@aws-lambda-powertools/logger';
import {
  RepositoryException,
  ConnectionException,
  QueryTimeoutException
} from './exceptions/repository-exceptions';

const logger = new Logger({ serviceName: 'cdc-pipeline' });

export interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
}

const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxRetries: 3,
  baseDelayMs: 100,
  maxDelayMs: 5000,
  backoffMultiplier: 2
};

/**
 * Wrap a repository operation with error handling and retry logic
 */
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  operationName: string,
  options: Partial<RetryOptions> = {}
): Promise<T> {
  const retryOptions = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: Error | undefined;
  let attempt = 0;

  while (attempt <= retryOptions.maxRetries) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;
      
      const repositoryError = translateError(error);
      
      logger.error('Repository operation failed', {
        operationName,
        attempt,
        errorCode: repositoryError.code,
        isRetryable: repositoryError.isRetryable,
        message: repositoryError.message
      });

      if (!repositoryError.isRetryable || attempt >= retryOptions.maxRetries) {
        throw repositoryError;
      }

      const delay = calculateBackoff(attempt, retryOptions);
      logger.info(`Retrying operation after ${delay}ms`, { operationName, attempt: attempt + 1 });
      await sleep(delay);
      attempt++;
    }
  }

  throw lastError;
}

/**
 * Translate database errors to repository exceptions
 */
function translateError(error: any): RepositoryException {
  // MySQL error codes
  if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
    return new ConnectionException('Database connection refused', error);
  }
  
  if (error.code === 'PROTOCOL_CONNECTION_LOST') {
    return new ConnectionException('Database connection lost', error);
  }
  
  if (error.code === 'ER_LOCK_WAIT_TIMEOUT') {
    return new QueryTimeoutException('Query', 30000, error);
  }
  
  if (error.errno === 1205) { // Lock wait timeout
    return new QueryTimeoutException('Lock acquisition', 50000, error);
  }

  // Default to generic repository exception
  return new RepositoryException(
    error.message || 'Unknown repository error',
    'UNKNOWN_ERROR',
    false,
    error
  );
}

/**
 * Calculate exponential backoff delay
 */
function calculateBackoff(attempt: number, options: RetryOptions): number {
  const delay = options.baseDelayMs * Math.pow(options.backoffMultiplier, attempt);
  const jitter = Math.random() * 0.1 * delay;
  return Math.min(delay + jitter, options.maxDelayMs);
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Usage Example with Error Handling

```typescript
// Example: Safe repository usage with error handling
import { GroupMapsLogRepository } from './repositories/group-maps-log.repository';
import { withErrorHandling } from './repositories/error-handler';
import { EntityNotFoundException } from './repositories/exceptions/repository-exceptions';

async function getAgentGroupMappings(
  repository: GroupMapsLogRepository,
  agentId: string
): Promise<void> {
  try {
    const mappings = await withErrorHandling(
      () => repository.findByAgentId(agentId),
      'findByAgentId',
      { maxRetries: 3 }
    );

    if (mappings.length === 0) {
      throw new EntityNotFoundException('GroupMapping', agentId);
    }

    console.log(`Found ${mappings.length} group mappings for agent ${agentId}`);
    return mappings;
  } catch (error) {
    if (error instanceof EntityNotFoundException) {
      console.log(`No group mappings found for agent: ${agentId}`);
      return [];
    }
    throw error;
  }
}
```

## Best Practices

### Repository Design Guidelines

1. **Single Responsibility**: Each repository should handle one entity type
2. **Immutability**: Return new objects from mapping functions, don't mutate input
3. **Logging**: Log all significant operations with appropriate context
4. **Metrics**: Track query execution times and error rates
5. **Connection Management**: Use connection pooling and proper cleanup

### Performance Considerations

- Use prepared statements for repeated queries
- Implement pagination for large result sets
- Consider caching for frequently accessed data
- Monitor and optimize slow queries
- Use appropriate indexes on CoreDB tables

### Testing Repositories

```typescript
// Example test setup
import { GroupMapsLogRepository } from './repositories/group-maps-log.repository';

describe('GroupMapsLogRepository', () => {
  let repository: GroupMapsLogRepository;
  let mockConnection: any;

  beforeEach(() => {
    mockConnection = {
      execute: jest.fn()
    };
    repository = new GroupMapsLogRepository(mockConnection, mockRedactionService);
  });

  it('should find group mappings by agent ID', async () => {
    mockConnection.execute.mockResolvedValue([[
      { id: 1, agent_id: 'agent-1', group_id: 'group-1', action: 'ADD' }
    ]]);

    const result = await repository.findByAgentId('agent-1');

    expect(result).toHaveLength(1);
    expect(result[0].agentId).toBe('agent-1');
  });
});
```

## Summary

The Repository Layer in the CDC Pipeline service provides a robust, maintainable abstraction for data access operations. By following the patterns and practices outlined in this documentation, developers can:

- Consistently access data from CoreDB tables
- Handle errors gracefully with retry logic
- Process CDC events with proper data redaction
- Maintain clean separation between data access and business logic

For additional support or questions about the repository layer, consult the CDC Pipeline team or refer to the internal architecture documentation.