# Event Data Models

This document covers the data models used in the cai-service event system, including S3 event handlers, SQS message payloads, and event processing pipelines.

## Overview

The event system in cai-service processes various asynchronous events including:
- **S3 Events**: File upload/deletion triggers for document processing
- **Website Ingestion Events**: Crawling and content extraction events
- **Metadata Update Events**: Knowledge store metadata synchronization
- **Embedding Events**: SQS messages for vector embedding operations

## Entity Relationship Diagram

```
┌─────────────────────┐         ┌─────────────────────────┐
│   S3HandlerEvent    │         │  ExtendedWebsiteIngestion│
│  (S3 file events)   │         │   (crawl/ingest events) │
└─────────┬───────────┘         └───────────┬─────────────┘
          │                                 │
          │                                 │
          ▼                                 ▼
┌─────────────────────────────────────────────────────────┐
│                   UnprocessedEvents                      │
│            (Union of all event types)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
┌─────────────┐ ┌───────────┐ ┌─────────────────┐
│ GetS3Object │ │ WebsiteIn │ │  MetadataUpdate │
│             │ │  gestion  │ │                 │
└──────┬──────┘ └─────┬─────┘ └────────┬────────┘
       │              │                │
       ▼              ▼                ▼
┌─────────────────────────────────────────────────────────┐
│              SqsEmbeddingMessage                         │
│         (Document embedding queue)                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│        KnowledgeEmbedderEventPayload                     │
│           (Embedding processor)                          │
└─────────────────────────────────────────────────────────┘
```

---

## S3 Event Models

### S3HandlerEvent

Processed S3 event data structure used for handling file operations in knowledge stores.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `string` | Yes | Action type: `'Create'` or `'Delete'` |
| `bucket` | `string` | Yes | S3 bucket name containing the object |
| `key` | `string` | Yes | S3 object key in format `<prefix>/<orgId>/<knowledgeStoreId>/<fileName>` |
| `version` | `string` | Yes | S3 object version ID for versioned buckets |

**Validation Rules:**
- `action` must be either `'Create'` or `'Delete'`
- `key` must follow the hierarchical format with organization and knowledge store identifiers
- `version` is required for proper document versioning

**Example:**
```json
{
  "action": "Create",
  "bucket": "cai-knowledge-store-documents",
  "key": "documents/12345/ks-abc123/product-manual.pdf",
  "version": "3HL4kqtJvjVBH40Nrjfkd"
}
```

**Relationships:**
- Triggers creation of `GetS3Object` for file retrieval
- Ultimately produces `SqsEmbeddingMessage` for vector processing

---

### GetS3Object

Response structure from S3 object retrieval containing file content and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization identifier extracted from S3 key |
| `knowledgeStoreId` | `string` | Yes | Knowledge store identifier extracted from S3 key |
| `blob` | `unknown` | Yes | File content as binary blob |
| `metadata` | `Record<string, unknown>` | Yes | S3 object metadata including custom tags |
| `documentId` | `string` | Yes | Document identifier (typically the S3 key) |
| `documentVersion` | `string` | Yes | Document version from S3 versioning |

**Validation Rules:**
- `orgId` must be a positive integer
- `knowledgeStoreId` must be a valid UUID format
- `metadata` may contain user-defined tags from S3

**Example:**
```json
{
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123-def456-789",
  "blob": "<binary data>",
  "metadata": {
    "Content-Type": "application/pdf",
    "x-amz-meta-category": "product-documentation",
    "x-amz-meta-language": "en-US"
  },
  "documentId": "documents/12345/ks-abc123/product-manual.pdf",
  "documentVersion": "3HL4kqtJvjVBH40Nrjfkd"
}
```

**Relationships:**
- Created from `S3HandlerEvent` processing
- Passed to file processors (`PdfFile`, `TxtFile`, etc.)
- Metadata flows to `EnrichMetadataParams`

---

## Website Ingestion Event Models

### ExtendedWebsiteIngestion

Extended website ingestion event record with DynamoDB keys and processing metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `PK` | `string` | Yes | Partition key in format `ORG#<orgId>#WEBSITE_INGESTION` |
| `SK` | `string` | Yes | Sort key in format `KST_ID#<knowledgeStoreId>#WSI_ID#<uniqueId>` |
| `type` | `string` | Yes | Event type: `'websiteIngestion'` or `'websiteCrawl'` |
| `action` | `string` | Yes | Action to perform: `'create'`, `'delete'`, or `'resync'` |
| `processingNumber` | `number` | Yes | Counter for processing attempts (for retry logic) |
| `correlationId` | `string` | No | Correlation ID for distributed tracing |

**Validation Rules:**
- `PK` must follow the exact format with organization ID
- `SK` must include knowledge store ID and unique ingestion ID
- `type` must be one of the defined event types
- `action` must be a valid action string
- `processingNumber` starts at 0 and increments on retries

**Example:**
```json
{
  "PK": "ORG#12345#WEBSITE_INGESTION",
  "SK": "KST_ID#ks-abc123#WSI_ID#wsi-789xyz",
  "type": "websiteCrawl",
  "action": "create",
  "processingNumber": 0,
  "correlationId": "corr-123e4567-e89b-12d3"
}
```

**Relationships:**
- Part of `UnprocessedEvents` union type
- References `WebsiteIngestion` configuration
- Triggers creation of `IngestionPage` records

---

### WebsiteIngestion

Website ingestion configuration and status tracking record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `PK` | `string` | Yes | Partition key for DynamoDB |
| `SK` | `string` | Yes | Sort key for DynamoDB |
| `url` | `string` | Yes | Root URL of the website to ingest |
| `knowledgeStoreId` | `string` | Yes | Associated knowledge store identifier |
| `id` | `string` | Yes | Unique identifier for the ingestion job |
| `latestChunkIndex` | `number` | Yes | Index of the latest processed chunk |
| `metadata` | `Record<string, unknown>[]` | No | Custom metadata for the ingestion |
| `sitemapProcessed` | `boolean` | Yes | Whether sitemap has been processed |
| `sitemapUrls` | `number` | Yes | Number of URLs found in sitemap |

**Validation Rules:**
- `url` must be a valid URL format
- `latestChunkIndex` must be >= 0
- `sitemapUrls` must be >= 0

**Example:**
```json
{
  "PK": "ORG#12345#WEBSITE_INGESTION",
  "SK": "KST_ID#ks-abc123#WSI_ID#wsi-789xyz",
  "url": "https://docs.example.com",
  "knowledgeStoreId": "ks-abc123",
  "id": "wsi-789xyz",
  "latestChunkIndex": 42,
  "metadata": [
    { "key": "category", "value": "documentation" }
  ],
  "sitemapProcessed": true,
  "sitemapUrls": 156
}
```

**Relationships:**
- Referenced by `ExtendedWebsiteIngestion` events
- Parent of multiple `IngestionPage` records

---

### IngestionPage

Individual page within a website ingestion job.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `PK` | `string` | Yes | Partition key in format `ORG#<orgId>#WEBSITE_INGESTION_PAGE` |
| `SK` | `string` | Yes | Sort key in format `KST_ID#<knowledgeStoreId>#WSI_ID#<uniqueId>#PAGE#<url>` |
| `url` | `string` | Yes | URL of the page |
| `crawled` | `boolean` | Yes | Whether the page has been crawled |
| `ingested` | `boolean` | Yes | Whether the page has been ingested |
| `retries` | `number` | Yes | Number of retry attempts |
| `approximateCharacters` | `number` | Yes | Approximate character count of page content |
| `depth` | `number` | Yes | Depth level from root URL |
| `status` | `IngestionStatuses \| CrawlingStatuses` | Yes | Current status of the page |

**Validation Rules:**
- `retries` must be >= 0
- `depth` must be >= 0
- `approximateCharacters` must be >= 0
- `status` must be a valid status enum value

**Example:**
```json
{
  "PK": "ORG#12345#WEBSITE_INGESTION_PAGE",
  "SK": "KST_ID#ks-abc123#WSI_ID#wsi-789xyz#PAGE#https://docs.example.com/guide",
  "url": "https://docs.example.com/guide",
  "crawled": true,
  "ingested": false,
  "retries": 0,
  "approximateCharacters": 15420,
  "depth": 1,
  "status": "INGESTION_IN_PROGRESS"
}
```

**Relationships:**
- Child of `WebsiteIngestion`
- Updated by `CrawlWorkerResult` and `IngestionWorkerResult`

---

### CreateIngestionPageInput

Input parameters for creating a new ingestion page record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orgId` | `number` | Yes | Organization ID |
| `knowledgeStoreId` | `string` | Yes | Knowledge store identifier |
| `uniqueId` | `string` | Yes | Unique identifier for the website ingestion job |
| `url` | `string` | Yes | URL of the page to create |

**Validation Rules:**
- `orgId` must be a positive integer
- `url` must be a valid URL format
- `uniqueId` should be unique within the knowledge store

**Example:**
```json
{
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123",
  "uniqueId": "wsi-789xyz",
  "url": "https://docs.example.com/api-reference"
}
```

---

## Metadata Update Events

### MetadataUpdate

Event for updating metadata across knowledge store documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `string` | Yes | Event type, must be `'metadataUpdate'` |
| `action` | `string` | Yes | Action to perform |
| `orgId` | `number` | Yes | Organization ID |
| `knowledgeStoreId` | `string` | Yes | Knowledge store identifier |
| `existingMetadata` | `KnowledgeStoreMetadataInput[]` | No | Current metadata values |
| `newMetadata` | `KnowledgeStoreMetadataInput[]` | No | New metadata values to set |
| `addedParameters` | `MetadataParameter[]` | Yes | Parameters being added |
| `deletedParameters` | `MetadataParameter[]` | Yes | Parameters being removed |
| `correlationId` | `string` | No | Correlation ID for tracing |

**Validation Rules:**
- `type` must be exactly `'metadataUpdate'`
- `addedParameters` and `deletedParameters` are mutually exclusive operations

**Example:**
```json
{
  "type": "metadataUpdate",
  "action": "update",
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123",
  "existingMetadata": [
    { "metadataParameter": "category", "defaultValue": "general" }
  ],
  "newMetadata": [
    { "metadataParameter": "category", "defaultValue": "technical" },
    { "metadataParameter": "priority", "defaultValue": "high" }
  ],
  "addedParameters": [
    { "metadataParameter": "priority", "defaultValue": "high" }
  ],
  "deletedParameters": [],
  "correlationId": "corr-456def"
}
```

**Relationships:**
- Part of `UnprocessedEvents` union type
- Updates `EmbeddingDocument` metadata in OpenSearch

---

### MetadataParameter

A metadata parameter with key and default value.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadataParameter` | `string` | Yes | Name of the metadata parameter |
| `defaultValue` | `unknown` | Yes | Default value for the parameter |

**Example:**
```json
{
  "metadataParameter": "document_type",
  "defaultValue": "user_guide"
}
```

---

## SQS Embedding Events

### SqsEmbeddingMessage

Message structure for the SQS embedding queue that triggers vector embedding operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `knowledgeStoreId` | `string` | Yes | Knowledge store identifier |
| `opensearchCollectionUrl` | `string` | Yes | OpenSearch collection endpoint URL |
| `documents` | `Document[]` | Yes | Array of documents to embed |
| `markAsFinished` | `boolean` | Yes | Whether this is the final batch in the ingestion |
| `pk` | `string` | Yes | Partition key for the ingestion record |
| `sk` | `string` | Yes | Sort key for the ingestion record |
| `orgId` | `number` | Yes | Organization ID |
| `correlationId` | `string` | Yes | Correlation ID for distributed tracing |

**Validation Rules:**
- `documents` array must not be empty
- `opensearchCollectionUrl` must be a valid URL
- `markAsFinished` should be `true` only for the last batch

**Example:**
```json
{
  "knowledgeStoreId": "ks-abc123",
  "opensearchCollectionUrl": "https://collection-xyz.us-east-1.aoss.amazonaws.com",
  "documents": [
    {
      "pageContent": "This is the first chunk of content...",
      "metadata": {
        "source": "product-manual.pdf",
        "page": 1
      }
    }
  ],
  "markAsFinished": false,
  "pk": "ORG#12345#DOCUMENT_INGESTION",
  "sk": "DOC#product-manual.pdf#v1",
  "orgId": 12345,
  "correlationId": "corr-789ghi"
}
```

**Relationships:**
- Consumed by `KnowledgeEmbedderEventPayload` handler
- Contains `Document` objects with metadata

---

### KnowledgeEmbedderEventPayload

Payload structure for the knowledge embedder Lambda function triggered by SQS.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `knowledgeStoreId` | `string` | Yes | Knowledge store identifier |
| `opensearchCollectionUrl` | `string` | Yes | OpenSearch collection URL |
| `documents` | `unknown` | Yes | Documents to embed |
| `orgId` | `string \| number` | Yes | Organization identifier (accepts both types) |
| `markAsFinished` | `boolean` | Yes | Flag to mark ingestion as complete |
| `pk` | `string` | Yes | Primary key for DynamoDB tracking |
| `sk` | `string` | Yes | Sort key for DynamoDB tracking |
| `correlationId` | `string` | Yes | Correlation ID for tracing |

**Validation Rules:**
- `orgId` is normalized to number during processing
- `markAsFinished` triggers finalization logic when `true`

**Example:**
```json
{
  "knowledgeStoreId": "ks-abc123",
  "opensearchCollectionUrl": "https://collection-xyz.us-east-1.aoss.amazonaws.com",
  "documents": [
    {
      "pageContent": "Vector embeddings are...",
      "metadata": { "chunk": 5 }
    }
  ],
  "orgId": "12345",
  "markAsFinished": true,
  "pk": "ORG#12345#DOCUMENT_INGESTION",
  "sk": "DOC#manual.pdf#v2",
  "correlationId": "corr-abc123"
}
```

---

## Union Types

### UnprocessedEvents

Union type representing all event types that can be processed by the event handler system.

| Type | Description |
|------|-------------|
| `S3EventRecord` | Native AWS S3 event record |
| `ExtendedWebsiteIngestion` | Website crawling/ingestion event |
| `MetadataUpdate` | Metadata synchronization event |

**Usage Pattern:**
```typescript
function processEvent(event: UnprocessedEvents) {
  if ('bucket' in event) {
    // Handle S3 event
  } else if (event.type === 'websiteIngestion') {
    // Handle website ingestion
  } else if (event.type === 'metadataUpdate') {
    // Handle metadata update
  }
}
```

---

## Sitemap Models

### SitemapEntry

Entry in a sitemap file representing a single URL.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `loc` | `string` | Yes | URL location |
| `lastmod` | `string[]` | No | Last modification dates |
| `changefreq` | `string[]` | No | Change frequency values |
| `priority` | `string[]` | No | Priority values |

**Example:**
```json
{
  "loc": "https://docs.example.com/guide/getting-started",
  "lastmod": ["2024-01-15"],
  "changefreq": ["weekly"],
  "priority": ["0.8"]
}
```

---

### SitemapIndexEntry

Index entry containing multiple sitemap references.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sitemap` | `SitemapEntry[]` | Yes | Array of sitemap entries |

**Example:**
```json
{
  "sitemap": [
    { "loc": "https://docs.example.com/sitemap-docs.xml" },
    { "loc": "https://docs.example.com/sitemap-blog.xml" }
  ]
}
```

---

## Worker Result Models

### CrawlWorkerResult

Result returned from the `CrawlWorker.crawl()` method.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `CrawlingStatuses` | Yes | Crawling status result |
| `ingestionPage` | `IngestionPage` | Yes | Updated ingestion page record |
| `newLinks` | `string[]` | Yes | New links discovered on the page |
| `approximateCharacters` | `number` | Yes | Character count of page content |
| `finalUrl` | `string` | Yes | Final URL after any redirects |

**Example:**
```json
{
  "status": "CRAWLING_SUCCESS",
  "ingestionPage": {
    "PK": "ORG#12345#WEBSITE_INGESTION_PAGE",
    "SK": "KST_ID#ks-abc123#WSI_ID#wsi-789#PAGE#https://example.com",
    "url": "https://example.com",
    "crawled": true,
    "ingested": false,
    "retries": 0,
    "approximateCharacters": 8500,
    "depth": 0,
    "status": "CRAWLING_SUCCESS"
  },
  "newLinks": [
    "https://example.com/about",
    "https://example.com/products"
  ],
  "approximateCharacters": 8500,
  "finalUrl": "https://example.com/"
}
```

---

### IngestionWorkerResult

Result returned from the `IngestionWorker.ingest()` method.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `IngestionStatuses` | Yes | Ingestion status result |
| `ingestionPage` | `IngestionPage` | Yes | Updated ingestion page record |
| `content` | `string[]` | Yes | Extracted paragraph content |

**Example:**
```json
{
  "status": "INGESTION_SUCCESS",
  "ingestionPage": {
    "PK": "ORG#12345#WEBSITE_INGESTION_PAGE",
    "SK": "KST_ID#ks-abc123#WSI_ID#wsi-789#PAGE#https://example.com",
    "url": "https://example.com",
    "crawled": true,
    "ingested": true,
    "retries": 0,
    "approximateCharacters": 8500,
    "depth": 0,
    "status": "INGESTION_SUCCESS"
  },
  "content": [
    "Welcome to our documentation portal.",
    "This guide will help you get started with our API.",
    "For more information, see the API reference."
  ]
}
```

---

## Monitoring Models

### CrawlerMonitoring

Internal state tracking for the website crawling process.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rootUrl` | `string` | Yes | Root URL being crawled |
| `executionTimeExceeded` | `boolean` | Yes | Whether execution time limit was exceeded |
| `latestChunkIndex` | `number` | Yes | Latest chunk index processed |
| `allUrlsCrawled` | `boolean` | Yes | Whether all URLs have been crawled |
| `totalCharactersCounter` | `number` | Yes | Total characters found across all pages |
| `charactersLimitExceeded` | `boolean` | Yes | Whether character limit was exceeded |
| `blockedByClient` | `boolean` | Yes | Whether crawling was blocked by anti-bot measures |

**Example:**
```json
{
  "rootUrl": "https://docs.example.com",
  "executionTimeExceeded": false,
  "latestChunkIndex": 45,
  "allUrlsCrawled": false,
  "totalCharactersCounter": 1250000,
  "charactersLimitExceeded": false,
  "blockedByClient": false
}
```

---

### IngestionMonitoring

Internal state tracking for the website ingestion process.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rootUrl` | `string` | Yes | Root URL being ingested |
| `allUrlsIngested` | `boolean` | Yes | Whether all URLs have been ingested |
| `executionTimeExceeded` | `boolean` | Yes | Whether execution time limit was exceeded |
| `latestChunkIndex` | `number` | Yes | Latest chunk index processed |

**Example:**
```json
{
  "rootUrl": "https://docs.example.com",
  "allUrlsIngested": false,
  "executionTimeExceeded": false,
  "latestChunkIndex": 32
}
```

---

## Browser Result Models

### PageContentResult

Result structure from the `getPageContent` function.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | Yes | HTML content of the page |
| `finalUrl` | `string` | Yes | Final URL after redirects |

**Example:**
```json
{
  "text": "<!DOCTYPE html><html><head>...</head><body>...</body></html>",
  "finalUrl": "https://docs.example.com/guide/"
}
```

---

### BrowserInitResult

Result structure from browser initialization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `browser` | `Browser` | Yes | Playwright browser instance |
| `page` | `Page` | Yes | Playwright page instance |

---

### BrowserReinitResult

Result structure from browser reinitialization after failures.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `browser` | `Browser` | Yes | Playwright browser instance |
| `page` | `Page` | Yes | Playwright page instance |
| `successfullInitialization` | `boolean` | Yes | Whether initialization succeeded |

---

## Status Enumerations

### IngestionStatuses

Enumeration for ingestion status values.

| Value | Description |
|-------|-------------|
| `INGESTION_IN_PROGRESS` | Ingestion is currently processing |
| `INGESTION_SUCCESS` | Ingestion completed successfully |
| `INGESTION_FAILED` | Ingestion failed after retries |
| `INGESTION_BLOCKED` | Ingestion blocked due to complexity limits |
| `INGESTION_DELETED` | Ingestion was deleted |

---

### CrawlingStatuses

Enumeration for crawling status values.

| Value | Description |
|-------|-------------|
| `CRAWLING_STARTING` | Crawling is starting or pending retry |
| `CRAWLING_SUCCESS` | Crawling completed successfully |
| `CRAWLING_FAILED` | Crawling failed after max retries |
| `CRAWLING_BLOCKED` | Crawling blocked by anti-bot measures |

---

## Common Use Cases

### Processing S3 Upload Event

```typescript
// 1. Receive S3 event
const s3Event: S3HandlerEvent = {
  action: "Create",
  bucket: "cai-documents",
  key: "documents/12345/ks-abc/manual.pdf",
  version: "v1"
};

// 2. Retrieve object
const s3Object: GetS3Object = await getS3Object(s3Event);

// 3. Process and send to embedding queue
const embeddingMessage: SqsEmbeddingMessage = {
  knowledgeStoreId: s3Object.knowledgeStoreId,
  opensearchCollectionUrl: "https://...",
  documents: processedChunks,
  markAsFinished: true,
  pk: "ORG#12345#DOC",
  sk: "DOC#manual.pdf",
  orgId: s3Object.orgId,
  correlationId: "corr-123"
};
```

### Website Crawling Flow

```typescript
// 1. Receive crawl event
const event: ExtendedWebsiteIngestion = {
  PK: "ORG#12345#WEBSITE_INGESTION",
  SK: "KST_ID#ks-abc#WSI_ID#wsi-123",
  type: "websiteCrawl",
  action: "create",
  processingNumber: 0
};

// 2. Create page records
const pageInput: CreateIngestionPageInput = {
  orgId: 12345,
  knowledgeStoreId: "ks-abc",
  uniqueId: "wsi-123",
  url: "https://docs.example.com/page"
};

// 3. Process crawl result
const result: CrawlWorkerResult = await crawler.crawl(page);
```

---

## Related Documentation

- [Ingestion Models](./ingestion-models.md) - Document chunking and embedding models
- [Pipeline Models](./pipeline-models.md) - Pipeline configuration and execution models
- [Models Overview](./README.md) - Complete model reference