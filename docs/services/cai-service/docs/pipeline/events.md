# Event System

## Overview

The Event System in cai-service provides a robust, type-safe mechanism for handling asynchronous operations across the Conversational AI platform. Built on the EventFactory pattern, this system enables decoupled communication between services, facilitating knowledge ingestion pipelines, website crawling operations, S3 file processing, and metadata synchronization.

The event-driven architecture allows the system to scale horizontally while maintaining consistency across distributed operations. Whether you're processing uploaded documents, crawling websites for knowledge extraction, or updating metadata across services, the Event System provides a unified interface for all asynchronous workflows.

## EventFactory Pattern

### Understanding the EventFactory

The EventFactory pattern in cai-service serves as a centralized mechanism for creating, validating, and dispatching events throughout the system. This pattern ensures type safety, consistent event structure, and proper event routing.

```typescript
// src/events/EventFactory.ts
import { v4 as uuidv4 } from 'uuid';
import { EventType, BaseEvent, EventPayload } from './types';

export class EventFactory {
  private static instance: EventFactory;
  private eventHandlers: Map<EventType, EventHandler[]> = new Map();
  
  private constructor() {
    this.initializeHandlers();
  }
  
  public static getInstance(): EventFactory {
    if (!EventFactory.instance) {
      EventFactory.instance = new EventFactory();
    }
    return EventFactory.instance;
  }
  
  public createEvent<T extends EventPayload>(
    type: EventType,
    payload: T,
    metadata?: EventMetadata
  ): BaseEvent<T> {
    return {
      id: uuidv4(),
      type,
      payload,
      timestamp: new Date().toISOString(),
      version: '1.0',
      source: process.env.SERVICE_NAME || 'cai-service',
      correlationId: metadata?.correlationId || uuidv4(),
      metadata: {
        ...metadata,
        createdAt: Date.now(),
      },
    };
  }
  
  public async dispatch<T extends EventPayload>(
    event: BaseEvent<T>
  ): Promise<void> {
    const handlers = this.eventHandlers.get(event.type) || [];
    
    for (const handler of handlers) {
      try {
        await handler.handle(event);
      } catch (error) {
        console.error(`Event handler failed for ${event.type}:`, error);
        throw new EventDispatchError(event, error);
      }
    }
  }
  
  public registerHandler(type: EventType, handler: EventHandler): void {
    const existing = this.eventHandlers.get(type) || [];
    this.eventHandlers.set(type, [...existing, handler]);
  }
}
```

### Event Type Definitions

All events in the system extend from a base event interface that ensures consistency:

```typescript
// src/events/types.ts
export enum EventType {
  S3_OBJECT_CREATED = 's3.object.created',
  S3_OBJECT_DELETED = 's3.object.deleted',
  WEBSITE_CRAWL_STARTED = 'website.crawl.started',
  WEBSITE_CRAWL_COMPLETED = 'website.crawl.completed',
  WEBSITE_CRAWL_FAILED = 'website.crawl.failed',
  WEBSITE_INGESTION_STARTED = 'website.ingestion.started',
  WEBSITE_INGESTION_COMPLETED = 'website.ingestion.completed',
  METADATA_UPDATE_REQUESTED = 'metadata.update.requested',
  METADATA_UPDATE_COMPLETED = 'metadata.update.completed',
}

export interface BaseEvent<T extends EventPayload> {
  id: string;
  type: EventType;
  payload: T;
  timestamp: string;
  version: string;
  source: string;
  correlationId: string;
  metadata?: EventMetadata;
}

export interface EventMetadata {
  correlationId?: string;
  causationId?: string;
  userId?: string;
  tenantId?: string;
  retryCount?: number;
  maxRetries?: number;
  createdAt?: number;
}

export interface EventPayload {
  [key: string]: unknown;
}
```

### Using the EventFactory

```typescript
// Example: Creating and dispatching an event
import { EventFactory } from './events/EventFactory';
import { EventType } from './events/types';

const factory = EventFactory.getInstance();

// Create an event
const event = factory.createEvent(
  EventType.S3_OBJECT_CREATED,
  {
    bucket: 'knowledge-documents',
    key: 'uploads/document.pdf',
    size: 1024000,
    contentType: 'application/pdf',
  },
  {
    userId: 'user-123',
    tenantId: 'tenant-456',
  }
);

// Dispatch the event
await factory.dispatch(event);
```

## S3 Events

S3 events handle file operations within the knowledge ingestion pipeline. These events are triggered when documents are uploaded, modified, or deleted from S3 buckets.

### S3 Event Payloads

```typescript
// src/events/s3/S3EventPayload.ts
export interface S3ObjectCreatedPayload extends EventPayload {
  bucket: string;
  key: string;
  size: number;
  contentType: string;
  eTag?: string;
  versionId?: string;
  metadata?: Record<string, string>;
}

export interface S3ObjectDeletedPayload extends EventPayload {
  bucket: string;
  key: string;
  versionId?: string;
  deleteMarker?: boolean;
}
```

### Handling S3 Events

```typescript
// src/events/handlers/S3EventHandler.ts
import { EventHandler, BaseEvent } from '../types';
import { S3ObjectCreatedPayload } from '../s3/S3EventPayload';
import { DocumentProcessor } from '../../services/DocumentProcessor';
import { VectorEmbeddingService } from '../../services/VectorEmbeddingService';

export class S3ObjectCreatedHandler implements EventHandler {
  constructor(
    private documentProcessor: DocumentProcessor,
    private embeddingService: VectorEmbeddingService
  ) {}
  
  async handle(event: BaseEvent<S3ObjectCreatedPayload>): Promise<void> {
    const { bucket, key, contentType } = event.payload;
    
    console.log(`Processing S3 object: ${bucket}/${key}`);
    
    // Determine processor based on content type
    const processor = this.getProcessorForContentType(contentType);
    
    // Extract content from document
    const content = await processor.extract(bucket, key);
    
    // Generate vector embeddings
    const embeddings = await this.embeddingService.generateEmbeddings(content);
    
    // Store embeddings for knowledge indexing
    await this.embeddingService.storeEmbeddings({
      documentId: key,
      embeddings,
      metadata: {
        bucket,
        contentType,
        processedAt: new Date().toISOString(),
        correlationId: event.correlationId,
      },
    });
    
    console.log(`Successfully processed document: ${key}`);
  }
  
  private getProcessorForContentType(contentType: string) {
    const processors: Record<string, () => DocumentProcessor> = {
      'application/pdf': () => new PDFProcessor(),
      'text/csv': () => new CSVProcessor(),
      'application/json': () => new JSONProcessor(),
      'text/plain': () => new TextProcessor(),
    };
    
    return processors[contentType]?.() || new TextProcessor();
  }
}
```

### Registering S3 Event Handlers

```typescript
// src/events/bootstrap.ts
import { EventFactory } from './EventFactory';
import { EventType } from './types';
import { S3ObjectCreatedHandler } from './handlers/S3EventHandler';

export function bootstrapEventHandlers(): void {
  const factory = EventFactory.getInstance();
  
  // Register S3 handlers
  factory.registerHandler(
    EventType.S3_OBJECT_CREATED,
    new S3ObjectCreatedHandler(
      new DocumentProcessor(),
      new VectorEmbeddingService()
    )
  );
  
  factory.registerHandler(
    EventType.S3_OBJECT_DELETED,
    new S3ObjectDeletedHandler()
  );
}
```

## Website Crawl Events

Website crawl events manage the lifecycle of web scraping operations, from initiation through completion or failure.

### Crawl Event Payloads

```typescript
// src/events/crawl/CrawlEventPayload.ts
export interface WebsiteCrawlStartedPayload extends EventPayload {
  crawlId: string;
  targetUrl: string;
  maxDepth: number;
  maxPages: number;
  includePaths?: string[];
  excludePaths?: string[];
  respectRobotsTxt: boolean;
  userAgent?: string;
}

export interface WebsiteCrawlCompletedPayload extends EventPayload {
  crawlId: string;
  targetUrl: string;
  pagesProcessed: number;
  totalContentSize: number;
  duration: number;
  results: CrawlResultSummary;
}

export interface WebsiteCrawlFailedPayload extends EventPayload {
  crawlId: string;
  targetUrl: string;
  error: {
    code: string;
    message: string;
    stack?: string;
  };
  pagesProcessedBeforeFailure: number;
  recoverable: boolean;
}

export interface CrawlResultSummary {
  successfulPages: number;
  failedPages: number;
  skippedPages: number;
  totalLinks: number;
  contentTypes: Record<string, number>;
}
```

### Website Crawler Integration

```typescript
// src/services/WebsiteCrawler.ts
import { EventFactory } from '../events/EventFactory';
import { EventType } from '../events/types';
import { v4 as uuidv4 } from 'uuid';

export class WebsiteCrawler {
  private eventFactory: EventFactory;
  
  constructor() {
    this.eventFactory = EventFactory.getInstance();
  }
  
  async startCrawl(config: CrawlConfig): Promise<string> {
    const crawlId = uuidv4();
    
    // Emit crawl started event
    const startEvent = this.eventFactory.createEvent(
      EventType.WEBSITE_CRAWL_STARTED,
      {
        crawlId,
        targetUrl: config.url,
        maxDepth: config.maxDepth || 3,
        maxPages: config.maxPages || 100,
        includePaths: config.includePaths,
        excludePaths: config.excludePaths,
        respectRobotsTxt: config.respectRobotsTxt ?? true,
      }
    );
    
    await this.eventFactory.dispatch(startEvent);
    
    try {
      const results = await this.executeCrawl(crawlId, config);
      
      // Emit completion event
      const completedEvent = this.eventFactory.createEvent(
        EventType.WEBSITE_CRAWL_COMPLETED,
        {
          crawlId,
          targetUrl: config.url,
          pagesProcessed: results.totalPages,
          totalContentSize: results.totalSize,
          duration: results.duration,
          results: results.summary,
        },
        { correlationId: startEvent.correlationId }
      );
      
      await this.eventFactory.dispatch(completedEvent);
      
    } catch (error) {
      // Emit failure event
      const failedEvent = this.eventFactory.createEvent(
        EventType.WEBSITE_CRAWL_FAILED,
        {
          crawlId,
          targetUrl: config.url,
          error: {
            code: error.code || 'CRAWL_ERROR',
            message: error.message,
            stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
          },
          pagesProcessedBeforeFailure: this.getProcessedCount(crawlId),
          recoverable: this.isRecoverableError(error),
        },
        { correlationId: startEvent.correlationId }
      );
      
      await this.eventFactory.dispatch(failedEvent);
      throw error;
    }
    
    return crawlId;
  }
}
```

## Website Ingestion Events

Website ingestion events handle the processing of crawled content into the knowledge base, including content extraction, chunking, and vector embedding generation.

### Ingestion Event Payloads

```typescript
// src/events/ingestion/IngestionEventPayload.ts
export interface WebsiteIngestionStartedPayload extends EventPayload {
  ingestionId: string;
  crawlId: string;
  sourceUrl: string;
  totalPages: number;
  chunkingStrategy: ChunkingStrategy;
  embeddingModel: string;
}

export interface WebsiteIngestionCompletedPayload extends EventPayload {
  ingestionId: string;
  crawlId: string;
  sourceUrl: string;
  documentsCreated: number;
  chunksGenerated: number;
  embeddingsStored: number;
  processingTime: number;
  knowledgeBaseId: string;
}

export interface ChunkingStrategy {
  method: 'fixed' | 'semantic' | 'paragraph';
  maxChunkSize: number;
  overlapSize: number;
  preserveHeaders: boolean;
}
```

### Ingestion Pipeline Handler

```typescript
// src/events/handlers/IngestionHandler.ts
import { EventHandler, BaseEvent } from '../types';
import { WebsiteIngestionStartedPayload } from '../ingestion/IngestionEventPayload';

export class WebsiteIngestionHandler implements EventHandler {
  constructor(
    private contentExtractor: ContentExtractor,
    private chunkingService: ChunkingService,
    private embeddingService: VectorEmbeddingService,
    private knowledgeBaseService: KnowledgeBaseService
  ) {}
  
  async handle(event: BaseEvent<WebsiteIngestionStartedPayload>): Promise<void> {
    const { ingestionId, crawlId, chunkingStrategy, embeddingModel } = event.payload;
    
    // Retrieve crawled pages
    const crawledPages = await this.getCrawledPages(crawlId);
    
    let documentsCreated = 0;
    let chunksGenerated = 0;
    let embeddingsStored = 0;
    
    for (const page of crawledPages) {
      // Extract clean content
      const content = await this.contentExtractor.extract(page.html, {
        preserveStructure: true,
        removeNavigation: true,
        extractMetadata: true,
      });
      
      // Chunk content
      const chunks = await this.chunkingService.chunk(content, chunkingStrategy);
      chunksGenerated += chunks.length;
      
      // Generate embeddings
      for (const chunk of chunks) {
        const embedding = await this.embeddingService.generate(chunk.text, {
          model: embeddingModel,
        });
        
        await this.knowledgeBaseService.store({
          ingestionId,
          sourceUrl: page.url,
          content: chunk.text,
          embedding,
          metadata: {
            pageTitle: page.title,
            chunkIndex: chunk.index,
            headings: chunk.headings,
          },
        });
        
        embeddingsStored++;
      }
      
      documentsCreated++;
    }
    
    // Emit completion event
    const completedEvent = this.eventFactory.createEvent(
      EventType.WEBSITE_INGESTION_COMPLETED,
      {
        ingestionId,
        crawlId,
        sourceUrl: event.payload.sourceUrl,
        documentsCreated,
        chunksGenerated,
        embeddingsStored,
        processingTime: Date.now() - event.metadata.createdAt,
        knowledgeBaseId: await this.knowledgeBaseService.getKnowledgeBaseId(ingestionId),
      },
      { correlationId: event.correlationId }
    );
    
    await this.eventFactory.dispatch(completedEvent);
  }
}
```

## Metadata Update Events

Metadata update events synchronize metadata changes across the distributed system, ensuring consistency when document properties, tags, or configurations change.

### Metadata Event Payloads

```typescript
// src/events/metadata/MetadataEventPayload.ts
export interface MetadataUpdateRequestedPayload extends EventPayload {
  updateId: string;
  entityType: 'document' | 'knowledge_base' | 'crawl_config' | 'embedding';
  entityId: string;
  changes: MetadataChange[];
  triggeredBy: string;
  reason?: string;
}

export interface MetadataUpdateCompletedPayload extends EventPayload {
  updateId: string;
  entityType: string;
  entityId: string;
  appliedChanges: MetadataChange[];
  previousValues: Record<string, unknown>;
  updatedAt: string;
}

export interface MetadataChange {
  field: string;
  operation: 'set' | 'unset' | 'append' | 'remove';
  value?: unknown;
}
```

### Metadata Update Handler

```typescript
// src/events/handlers/MetadataUpdateHandler.ts
export class MetadataUpdateHandler implements EventHandler {
  private repositories: Map<string, MetadataRepository>;
  
  async handle(event: BaseEvent<MetadataUpdateRequestedPayload>): Promise<void> {
    const { updateId, entityType, entityId, changes } = event.payload;
    
    const repository = this.repositories.get(entityType);
    if (!repository) {
      throw new Error(`Unknown entity type: ${entityType}`);
    }
    
    // Get current state for audit
    const currentEntity = await repository.findById(entityId);
    const previousValues: Record<string, unknown> = {};
    
    // Apply changes
    const appliedChanges: MetadataChange[] = [];
    
    for (const change of changes) {
      previousValues[change.field] = currentEntity[change.field];
      
      switch (change.operation) {
        case 'set':
          await repository.setField(entityId, change.field, change.value);
          break;
        case 'unset':
          await repository.unsetField(entityId, change.field);
          break;
        case 'append':
          await repository.appendToField(entityId, change.field, change.value);
          break;
        case 'remove':
          await repository.removeFromField(entityId, change.field, change.value);
          break;
      }
      
      appliedChanges.push(change);
    }
    
    // Emit completion event
    const completedEvent = this.eventFactory.createEvent(
      EventType.METADATA_UPDATE_COMPLETED,
      {
        updateId,
        entityType,
        entityId,
        appliedChanges,
        previousValues,
        updatedAt: new Date().toISOString(),
      },
      { correlationId: event.correlationId }
    );
    
    await this.eventFactory.dispatch(completedEvent);
  }
}
```

## Creating Custom Events

The Event System is extensible, allowing you to create custom events for specific use cases within your application.

### Step 1: Define the Event Type

```typescript
// src/events/types.ts - Add to existing enum
export enum EventType {
  // ... existing types
  CUSTOM_AI_MODEL_SWITCHED = 'custom.ai_model.switched',
  CUSTOM_PROMPT_EXECUTED = 'custom.prompt.executed',
}
```

### Step 2: Create the Event Payload

```typescript
// src/events/custom/CustomEventPayload.ts
export interface AIModelSwitchedPayload extends EventPayload {
  previousModel: string;
  newModel: string;
  reason: string;
  affectedConversations: string[];
  switchedAt: string;
}

export interface PromptExecutedPayload extends EventPayload {
  promptId: string;
  modelUsed: string;
  inputTokens: number;
  outputTokens: number;
  executionTime: number;
  success: boolean;
  errorMessage?: string;
}
```

### Step 3: Create the Event Handler

```typescript
// src/events/handlers/CustomEventHandler.ts
import { EventHandler, BaseEvent } from '../types';
import { AIModelSwitchedPayload } from '../custom/CustomEventPayload';

export class AIModelSwitchedHandler implements EventHandler {
  constructor(
    private notificationService: NotificationService,
    private metricsService: MetricsService
  ) {}
  
  async handle(event: BaseEvent<AIModelSwitchedPayload>): Promise<void> {
    const { previousModel, newModel, affectedConversations } = event.payload;
    
    // Log metrics
    await this.metricsService.recordModelSwitch({
      from: previousModel,
      to: newModel,
      timestamp: event.timestamp,
    });
    
    // Notify affected users if necessary
    if (affectedConversations.length > 0) {
      await this.notificationService.notifyModelChange({
        conversationIds: affectedConversations,
        newModel,
        message: `AI model updated from ${previousModel} to ${newModel}`,
      });
    }
    
    console.log(`Model switch event processed: ${previousModel} -> ${newModel}`);
  }
}
```

### Step 4: Register the Handler

```typescript
// src/events/bootstrap.ts
import { AIModelSwitchedHandler } from './handlers/CustomEventHandler';

export function bootstrapEventHandlers(): void {
  const factory = EventFactory.getInstance();
  
  // ... existing handlers
  
  // Register custom handlers
  factory.registerHandler(
    EventType.CUSTOM_AI_MODEL_SWITCHED,
    new AIModelSwitchedHandler(
      new NotificationService(),
      new MetricsService()
    )
  );
}
```

### Step 5: Dispatch Custom Events

```typescript
// Usage in your service
const event = eventFactory.createEvent(
  EventType.CUSTOM_AI_MODEL_SWITCHED,
  {
    previousModel: 'gpt-4',
    newModel: 'claude-3-opus',
    reason: 'Performance optimization',
    affectedConversations: ['conv-1', 'conv-2', 'conv-3'],
    switchedAt: new Date().toISOString(),
  },
  {
    userId: 'admin-user',
    tenantId: 'tenant-123',
  }
);

await eventFactory.dispatch(event);
```

## Best Practices

1. **Always use correlation IDs**: Link related events together for distributed tracing
2. **Handle failures gracefully**: Implement retry logic and dead-letter queues for failed events
3. **Keep payloads serializable**: Avoid circular references and non-JSON-safe values
4. **Version your events**: Include version information for backward compatibility
5. **Log event dispatches**: Maintain audit trails for debugging and compliance
6. **Use idempotent handlers**: Design handlers to safely process duplicate events

## Related Documentation

- [Data Pipeline Configuration](./data-pipeline.md)
- [Vector Embedding Service](./vector-embeddings.md)
- [Knowledge Base Management](./knowledge-base.md)
- [WebSocket Events](./websocket-events.md)