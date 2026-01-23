# Ingestion Data Models

This document covers the data models used for website ingestion, crawling, and content extraction in the CAI Service. These models handle the complete lifecycle of ingesting external content into knowledge stores, including sitemap processing, page crawling, content extraction, and file processing.

## Overview

The ingestion system processes content from two primary sources:
1. **Website Ingestion**: Crawling and extracting content from websites
2. **File Ingestion**: Processing uploaded files (PDF, CSV, JSON, TXT) from S3

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Ingestion Architecture                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐   │
│  │ S3 Events    │────▶│ File Processing   │────▶│ Document Chunks  │   │
│  │ (S3Handler   │     │ (FileFactory,     │     │ (EnrichMetadata  │   │
│  │  Event)      │     │  BaseFile, etc.)  │     │  Params)         │   │
│  └──────────────┘     └───────────────────┘     └────────┬─────────┘   │
│                                                          │             │
│  ┌──────────────┐     ┌───────────────────┐              │             │
│  │ Website      │────▶│ Page Crawling     │              ▼             │
│  │ Ingestion    │     │ (CrawlWorker,     │     ┌──────────────────┐   │
│  │ Events       │     │  IngestionPage)   │────▶│ SQS Embedding    │   │
│  └──────────────┘     └───────────────────┘     │ (SqsEmbedding    │   │
│         │                                       │  Message)        │   │
│         ▼                                       └────────┬─────────┘   │
│  ┌──────────────┐     ┌───────────────────┐              │             │
│  │ Sitemap      │────▶│ URL Discovery     │              ▼             │
│  │ Processing   │     │ (SitemapEntry,    │     ┌──────────────────┐   │
│  │              │     │  SitemapIndex)    │     │ OpenSearch       │   │
│  └──────────────┘     └───────────────────┘     │ (EmbeddingDoc)   │   │
│                                                 └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Website Ingestion Models

### WebsiteIngestion

Configuration and status tracking for a website ingestion job.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PK | string | Yes | Partition key for DynamoDB |
| SK | string | Yes | Sort key for DynamoDB |
| url | string | Yes | Root URL of the website to ingest |
| knowledgeStoreId | string | Yes | Associated knowledge store identifier |
| id | string | Yes | Unique identifier for the ingestion |
| latestChunkIndex | number | Yes | Index of the latest processed chunk |
| metadata | Record<string, unknown>[] | No | Custom metadata for the ingestion |
| sitemapProcessed | boolean | Yes | Whether sitemap has been processed |
| sitemapUrls | number | Yes | Number of URLs found in sitemap |

**Example:**
```json
{
  "PK": "ORG#12345#WEBSITE_INGESTION",
  "SK": "KST_ID#ks-abc123#WSI_ID#wsi-xyz789",
  "url": "https://docs.example.com",
  "knowledgeStoreId": "ks-abc123",
  "id": "wsi-xyz789",
  "latestChunkIndex": 156,
  "metadata": [
    { "source": "documentation" },
    { "department": "engineering" }
  ],
  "sitemapProcessed": true,
  "sitemapUrls": 342
}
```

---

### ExtendedWebsiteIngestion

Extended website ingestion event record with processing metadata for queue-based processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PK | string | Yes | Partition key in format `ORG#<orgId>#WEBSITE_INGESTION` |
| SK | string | Yes | Sort key in format `KST_ID#<knowledgeStoreId>#WSI_ID#<uniqueId>` |
| type | string | Yes | Event type, e.g., 'websiteIngestion' or 'websiteCrawl' |
| action | string | Yes | Action to perform: 'create', 'delete', or 'resync' |
| processingNumber | number | Yes | Counter for processing attempts |
| correlationId | string | No | Correlation ID for distributed tracing |

**Validation Rules:**
- `action` must be one of: `create`, `delete`, `resync`
- `type` must be one of: `websiteIngestion`, `websiteCrawl`
- `processingNumber` starts at 0 and increments with each retry

**Example:**
```json
{
  "PK": "ORG#12345#WEBSITE_INGESTION",
  "SK": "KST_ID#ks-abc123#WSI_ID#wsi-xyz789",
  "type": "websiteIngestion",
  "action": "create",
  "processingNumber": 0,
  "correlationId": "req-abc-123-def-456"
}
```

---

### IngestionPage

Individual page within a website ingestion job, tracking crawl and ingestion status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PK | string | Yes | Partition key in format `ORG#<orgId>#WEBSITE_INGESTION_PAGE` |
| SK | string | Yes | Sort key in format `KST_ID#<knowledgeStoreId>#WSI_ID#<uniqueId>#PAGE#<url>` |
| url | string | Yes | URL of the page |
| crawled | boolean | Yes | Whether the page has been crawled |
| ingested | boolean | Yes | Whether the page has been ingested |
| retries | number | Yes | Number of retry attempts |
| approximateCharacters | number | No | Approximate character count of page content |
| depth | number | Yes | Depth level from root URL |
| status | IngestionStatuses \| CrawlingStatuses | Yes | Current status of the page |

**Example:**
```json
{
  "PK": "ORG#12345#WEBSITE_INGESTION_PAGE",
  "SK": "KST_ID#ks-abc123#WSI_ID#wsi-xyz789#PAGE#https://docs.example.com/guide",
  "url": "https://docs.example.com/guide",
  "crawled": true,
  "ingested": false,
  "retries": 0,
  "approximateCharacters": 15420,
  "depth": 1,
  "status": "INGESTION_IN_PROGRESS"
}
```

---

### CreateIngestionPageInput

Input parameters for creating a new ingestion page record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| orgId | number | Yes | Organization ID |
| knowledgeStoreId | string | Yes | Knowledge store identifier |
| uniqueId | string | Yes | Unique identifier for the website ingestion |
| url | string | Yes | URL of the page to create |

**Example:**
```json
{
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123",
  "uniqueId": "wsi-xyz789",
  "url": "https://docs.example.com/api-reference"
}
```

---

## Sitemap Models

### SitemapEntry

Entry in a sitemap file containing URL and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| loc | string | Yes | URL location |
| lastmod | string[] | No | Last modification dates |
| changefreq | string[] | No | Change frequency values |
| priority | string[] | No | Priority values |

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

Index entry in a sitemap index file containing references to multiple sitemaps.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sitemap | SitemapEntry[] | Yes | Array of sitemap entries |

**Example:**
```json
{
  "sitemap": [
    { "loc": "https://docs.example.com/sitemap-docs.xml" },
    { "loc": "https://docs.example.com/sitemap-blog.xml" },
    { "loc": "https://docs.example.com/sitemap-api.xml" }
  ]
}
```

---

## Crawling Models

### CrawlWorkerResult

Result returned from the CrawlWorker.crawl() method after processing a page.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | CrawlingStatuses | Yes | Crawling status result |
| ingestionPage | IngestionPage | Yes | Updated ingestion page record |
| newLinks | string[] | Yes | New links discovered on the page |
| approximateCharacters | number | Yes | Character count of page content |
| finalUrl | string | Yes | Final URL after any redirects |

**Example:**
```json
{
  "status": "CRAWLING_SUCCESS",
  "ingestionPage": {
    "PK": "ORG#12345#WEBSITE_INGESTION_PAGE",
    "SK": "KST_ID#ks-abc123#WSI_ID#wsi-xyz789#PAGE#https://docs.example.com/guide",
    "url": "https://docs.example.com/guide",
    "crawled": true,
    "ingested": false,
    "retries": 0,
    "approximateCharacters": 15420,
    "depth": 1,
    "status": "CRAWLING_SUCCESS"
  },
  "newLinks": [
    "https://docs.example.com/guide/chapter-1",
    "https://docs.example.com/guide/chapter-2",
    "https://docs.example.com/api-reference"
  ],
  "approximateCharacters": 15420,
  "finalUrl": "https://docs.example.com/guide/"
}
```

---

### IngestionWorkerResult

Result returned from the IngestionWorker.ingest() method after extracting content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | IngestionStatuses | Yes | Ingestion status result |
| ingestionPage | IngestionPage | Yes | Updated ingestion page record |
| content | string[] | Yes | Extracted paragraph content |

**Example:**
```json
{
  "status": "INGESTION_SUCCESS",
  "ingestionPage": {
    "PK": "ORG#12345#WEBSITE_INGESTION_PAGE",
    "SK": "KST_ID#ks-abc123#WSI_ID#wsi-xyz789#PAGE#https://docs.example.com/guide",
    "url": "https://docs.example.com/guide",
    "crawled": true,
    "ingested": true,
    "retries": 0,
    "approximateCharacters": 15420,
    "depth": 1,
    "status": "INGESTION_SUCCESS"
  },
  "content": [
    "Welcome to our documentation guide...",
    "This section covers the basics of getting started...",
    "For advanced usage, see the API reference..."
  ]
}
```

---

### PageContentResult

Result structure from the getPageContent function containing raw HTML.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | Yes | HTML content of the page |
| finalUrl | string | Yes | Final URL after redirects |

**Example:**
```json
{
  "text": "<!DOCTYPE html><html><head><title>Guide</title></head><body>...</body></html>",
  "finalUrl": "https://docs.example.com/guide/"
}
```

---

### BrowserInitResult

Result structure from browser initialization for headless crawling.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| browser | Browser | Yes | Playwright browser instance |
| page | Page | Yes | Playwright page instance |

---

### BrowserReinitResult

Result structure from browser reinitialization after failures.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| browser | Browser | Yes | Playwright browser instance |
| page | Page | Yes | Playwright page instance |
| successfullInitialization | boolean | Yes | Whether initialization succeeded |

---

## Monitoring Models

### CrawlerMonitoring

Internal state tracking for the website crawling process.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| rootUrl | string | Yes | Root URL being crawled |
| executionTimeExceeded | boolean | Yes | Whether execution time limit was exceeded |
| latestChunkIndex | number | Yes | Latest chunk index processed |
| allUrlsCrawled | boolean | Yes | Whether all URLs have been crawled |
| totalCharactersCounter | number | Yes | Total characters found across all pages |
| charactersLimitExceeded | boolean | Yes | Whether character limit was exceeded |
| blockedByClient | boolean | Yes | Whether crawling was blocked by anti-bot measures |

**Example:**
```json
{
  "rootUrl": "https://docs.example.com",
  "executionTimeExceeded": false,
  "latestChunkIndex": 156,
  "allUrlsCrawled": false,
  "totalCharactersCounter": 2500000,
  "charactersLimitExceeded": false,
  "blockedByClient": false
}
```

---

### IngestionMonitoring

Internal state tracking for the website ingestion process.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| rootUrl | string | Yes | Root URL being ingested |
| allUrlsIngested | boolean | Yes | Whether all URLs have been ingested |
| executionTimeExceeded | boolean | Yes | Whether execution time limit was exceeded |
| latestChunkIndex | number | Yes | Latest chunk index processed |

**Example:**
```json
{
  "rootUrl": "https://docs.example.com",
  "allUrlsIngested": false,
  "executionTimeExceeded": false,
  "latestChunkIndex": 89
}
```

---

## S3 File Ingestion Models

### S3HandlerEvent

Processed S3 event data for file handling operations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| action | string | Yes | Action type: 'Create' or 'Delete' |
| bucket | string | Yes | S3 bucket name |
| key | string | Yes | S3 object key in format `<prefix>/<orgId>/<knowledgeStoreId>/<fileName>` |
| version | string | Yes | S3 object version ID |

**Validation Rules:**
- `action` must be either `Create` or `Delete`
- `key` must follow the format: `<prefix>/<orgId>/<knowledgeStoreId>/<fileName>`

**Example:**
```json
{
  "action": "Create",
  "bucket": "cai-knowledge-store-uploads",
  "key": "uploads/12345/ks-abc123/product-manual.pdf",
  "version": "abc123def456"
}
```

---

### GetS3Object

Response from S3 object retrieval including file content and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| orgId | number | Yes | Organization ID extracted from key |
| knowledgeStoreId | string | Yes | Knowledge store identifier extracted from key |
| blob | unknown | Yes | File content blob |
| metadata | Record<string, unknown> | Yes | S3 object metadata including tags |
| documentId | string | Yes | Document identifier (S3 key) |
| documentVersion | string | Yes | Document version |

**Example:**
```json
{
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123",
  "blob": "<binary data>",
  "metadata": {
    "Content-Type": "application/pdf",
    "x-amz-meta-source": "manual-upload",
    "x-amz-meta-department": "support"
  },
  "documentId": "uploads/12345/ks-abc123/product-manual.pdf",
  "documentVersion": "abc123def456"
}
```

---

## File Processing Models

### BaseFile

Abstract base class for file processing that converts files into LangChain Documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The binary file data to be processed |

**Methods:**
- `load(): Promise<Document[]>` - Converts file to array of LangChain Documents

---

### PdfFile

File processor for PDF documents, extends BaseFile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The PDF file data (inherited from BaseFile) |

**Supported MIME Types:** `application/pdf`

---

### CsvFile

File processor for CSV documents, extends BaseFile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The CSV file data (inherited from BaseFile) |

**Supported MIME Types:** `text/csv`, `application/csv`

---

### JsonFile

File processor for JSON documents, extends BaseFile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The JSON file data (inherited from BaseFile) |

**Supported MIME Types:** `application/json`

---

### TxtFile

File processor for plain text documents, extends BaseFile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The text file data (inherited from BaseFile) |

**Supported MIME Types:** `text/plain`

---

### FileFactory

Factory class for creating appropriate file processor instances based on MIME type.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileRegistry | FileRegistry | Yes (static) | Registry mapping MIME types to file processor classes |

**Usage:**
```typescript
const processor = FileFactory.create('application/pdf', fileBlob);
const documents = await processor.load();
```

**Supported File Types:**
| MIME Type | Processor Class |
|-----------|-----------------|
| `application/pdf` | PdfFile |
| `text/csv` | CsvFile |
| `application/csv` | CsvFile |
| `application/json` | JsonFile |
| `text/plain` | TxtFile |

---

### FileTypes

Union type for supported file processors.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | PdfFile \| TxtFile \| JsonFile \| CsvFile | Yes | One of the supported file type handlers |

---

## Document Processing Models

### Document

LangChain document structure for text processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pageContent | string | Yes | Text content of the document |
| metadata | Record<string, unknown> | No | Document metadata |

**Example:**
```json
{
  "pageContent": "This is the extracted text content from the document...",
  "metadata": {
    "source": "product-manual.pdf",
    "page": 1,
    "totalPages": 45
  }
}
```

---

### EnrichMetadataParams

Parameters for enriching chunk metadata during document processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chunk | Document | Yes | The document chunk to enrich |
| knowledgeStoreId | string | Yes | Identifier for the knowledge store |
| orgId | number | Yes | Organization identifier |
| chunkIndex | number | Yes | Index of the current chunk |
| chunksNumber | number | Yes | Total number of chunks |
| documentId | string | Yes | Document identifier |
| documentVersion | string | Yes | Version of the document |
| customMetadata | Record<string, unknown> | No | Custom metadata key-value pairs |
| websiteUrl | string | No | Optional website URL source |

**Example:**
```json
{
  "chunk": {
    "pageContent": "This section describes the API authentication...",
    "metadata": {}
  },
  "knowledgeStoreId": "ks-abc123",
  "orgId": 12345,
  "chunkIndex": 5,
  "chunksNumber": 42,
  "documentId": "uploads/12345/ks-abc123/api-docs.pdf",
  "documentVersion": "v1.2.3",
  "customMetadata": {
    "category": "api-documentation",
    "audience": "developers"
  },
  "websiteUrl": null
}
```

---

### ChunkMetadata

Metadata structure attached to document chunks after enrichment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| orgId | number | Yes | Organization identifier |
| knowledgeStoreId | string | Yes | Knowledge store identifier |
| documentId | string | Yes | Document identifier |
| documentVersion | string | Yes | Document version |
| chunkNumber | number | Yes | Index of the chunk |
| totalChunks | number | Yes | Total number of chunks in document |
| timeStamp | string | Yes | ISO timestamp of processing |
| chunk_text | string | Yes | Text content of the chunk |
| customerMetadata | Record<string, unknown> | No | Custom metadata object |
| websiteUrl | string \| null | No | Source website URL if applicable |

**Example:**
```json
{
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123",
  "documentId": "uploads/12345/ks-abc123/api-docs.pdf",
  "documentVersion": "v1.2.3",
  "chunkNumber": 5,
  "totalChunks": 42,
  "timeStamp": "2024-01-15T10:30:00.000Z",
  "chunk_text": "This section describes the API authentication...",
  "customerMetadata": {
    "category": "api-documentation",
    "audience": "developers"
  },
  "websiteUrl": null
}
```

---

## Embedding & Storage Models

### SqsEmbeddingMessage

Message structure for SQS embedding queue to process document batches.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knowledgeStoreId | string | Yes | Knowledge store identifier |
| opensearchCollectionUrl | string | Yes | OpenSearch collection URL |
| documents | Document[] | Yes | Array of documents to embed |
| markAsFinished | boolean | Yes | Whether this is the final batch |
| pk | string | Yes | Partition key for the ingestion record |
| sk | string | Yes | Sort key for the ingestion record |
| orgId | number | Yes | Organization ID |
| correlationId | string | No | Correlation ID for tracing |

**Example:**
```json
{
  "knowledgeStoreId": "ks-abc123",
  "opensearchCollectionUrl": "https://abc123.us-east-1.aoss.amazonaws.com",
  "documents": [
    {
      "pageContent": "Getting started with the API...",
      "metadata": {
        "chunkNumber": 0,
        "documentId": "https://docs.example.com/getting-started"
      }
    },
    {
      "pageContent": "Authentication is required for all endpoints...",
      "metadata": {
        "chunkNumber": 1,
        "documentId": "https://docs.example.com/getting-started"
      }
    }
  ],
  "markAsFinished": false,
  "pk": "ORG#12345#WEBSITE_INGESTION",
  "sk": "KST_ID#ks-abc123#WSI_ID#wsi-xyz789",
  "orgId": 12345,
  "correlationId": "req-abc-123"
}
```

---

### EmbeddingDocument

Document structure stored in OpenSearch with embeddings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metadata | EmbeddingDocumentMetadata | Yes | Document metadata including customer metadata |

---

### EmbeddingDocumentMetadata

Metadata structure for embedding documents in OpenSearch.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| customerMetadata | Record<string, unknown> | No | Custom metadata from customer |

**Example:**
```json
{
  "customerMetadata": {
    "category": "documentation",
    "department": "engineering",
    "version": "2.0"
  }
}
```

---

### KnowledgeEmbedderEventPayload

Payload structure for knowledge embedder SQS events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knowledgeStoreId | string | Yes | Knowledge store identifier |
| opensearchCollectionUrl | string | Yes | OpenSearch collection URL |
| documents | unknown | Yes | Documents to embed |
| orgId | string \| number | Yes | Organization identifier |
| markAsFinished | boolean | Yes | Flag to mark ingestion as complete |
| pk | string | Yes | Primary key for DynamoDB |
| sk | string | Yes | Sort key for DynamoDB |
| correlationId | string | No | Correlation ID for tracing |

---

## Metadata Update Models

### MetadataUpdate

Event for updating metadata across knowledge store documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Event type, must be 'metadataUpdate' |
| orgId | number | Yes | Organization ID |
| knowledgeStoreId | string | Yes | Knowledge store identifier |
| addedParameters | MetadataParameter[] | No | Parameters to add to metadata |
| deletedParameters | MetadataParameter[] | No | Parameters to remove from metadata |
| existingMetadata | KnowledgeStoreMetadataInput[] | No | Current metadata values |
| newMetadata | KnowledgeStoreMetadataInput[] | No | New metadata values to set |
| action | string | No | Action to perform |
| correlationId | string | No | Correlation ID for tracing |

**Example:**
```json
{
  "type": "metadataUpdate",
  "orgId": 12345,
  "knowledgeStoreId": "ks-abc123",
  "addedParameters": [
    {
      "metadataParameter": "department",
      "defaultValue": "general"
    }
  ],
  "deletedParameters": [
    {
      "metadataParameter": "legacy_field",
      "defaultValue": null
    }
  ],
  "correlationId": "req-abc-123"
}
```

---

### MetadataParameter

A metadata parameter definition with key and default value.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metadataParameter | string | Yes | Name of the metadata parameter |
| defaultValue | unknown | No | Default value for the parameter |

**Example:**
```json
{
  "metadataParameter": "category",
  "defaultValue": "uncategorized"
}
```

---

### DocumentIngestionData

Data structure for document metadata during bulk metadata updates.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| documentId | string | Yes | Document identifier (S3 key or URL) |
| metadata | Record<string, unknown>[] | Yes | Current metadata array |
| pk | string | Yes | Partition key |
| sk | string | Yes | Sort key |

**Example:**
```json
{
  "documentId": "https://docs.example.com/guide",
  "metadata": [
    { "category": "documentation" },
    { "audience": "developers" }
  ],
  "pk": "ORG#12345#DOCUMENT",
  "sk": "KST#ks-abc123#DOC#https://docs.example.com/guide"
}
```

---

### ProcessedDocument

Document prepared for bulk update in OpenSearch.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | OpenSearch document ID |
| embeddingDocument | EmbeddingDocument | Yes | Updated embedding document |

**Example:**
```json
{
  "id": "doc-abc123-chunk-5",
  "embeddingDocument": {
    "metadata": {
      "customerMetadata": {
        "category": "documentation",
        "department": "engineering"
      }
    }
  }
}
```

---

## Status Enumerations

### IngestionStatuses

Enumeration for ingestion status values.

| Value | Description |
|-------|-------------|
| `INGESTION_IN_PROGRESS` | Ingestion is currently processing |
| `INGESTION_SUCCESS` | Ingestion completed successfully |
| `INGESTION_FAILED` | Ingestion failed after processing |
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

### ChunkingStrategies

Enumeration for document chunking strategy options.

| Value | Description |
|-------|-------------|
| `RECURSIVE_STRATEGY` | Default recursive text splitting strategy |

---

### WebsiteIngestionModes

Enumeration for website ingestion mode options.

| Value | Description |
|-------|-------------|
| `DYNAMIC` | Dynamic website ingestion using headless browser |

---

## Union Types

### UnprocessedEvents

Union type for all unprocessed event types that can be handled by the ingestion system.

| Type | Description |
|------|-------------|
| S3EventRecord | S3 file upload/delete events |
| ExtendedWebsiteIngestion | Website ingestion events |
| MetadataUpdate | Metadata update events |

---

### FactoryFileTypes

Union type representing the class constructors for supported file types.

```typescript
type FactoryFileTypes = typeof PdfFile | typeof TxtFile | typeof JsonFile | typeof CsvFile;
```

---

### FileRegistry

Type definition for mapping MIME type strings to file processor classes.

```typescript
type FileRegistry = Record<string, FactoryFileTypes>;
```

---

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Ingestion Entity Relationships                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WebsiteIngestion (1) ─────────────────────────▶ (N) IngestionPage     │
│       │                                                  │              │
│       │ triggers                                        │ produces     │
│       ▼                                                  ▼              │
│  ExtendedWebsiteIngestion                          CrawlWorkerResult   │
│       │                                                  │              │
│       │ processes                                       │              │
│       ▼                                                  ▼              │
│  SitemapIndexEntry ────▶ SitemapEntry           IngestionWorkerResult  │
│                              │                           │              │
│                              │ contains URLs             │ contains    │
│                              ▼                           ▼              │
│                    CreateIngestionPageInput         Document[]         │
│                                                          │              │
│  S3HandlerEvent ──────────────────────────────────────┐  │              │
│       │                                               │  │              │
│       │ retrieves                                     │  │              │
│       ▼                                               │  │              │
│  GetS3Object ─────────────────────────────────────────┼──┤              │
│       │                                               │  │              │
│       │ processes via                                 │  │              │
│       ▼                                               │  │              │
│  FileFactory ────▶ BaseFile (PdfFile, CsvFile, etc.) │  │              │
│                         │                             │  │              │
│                         │ produces                    │  │              │
│                         ▼                             ▼  ▼              │
│                    Document[] ◀───────────────────────────┘             │
│                         │                                               │
│                         │ enriched via                                  │
│                         ▼                                               │
│                 EnrichMetadataParams ────▶ ChunkMetadata               │
│                                                  │                      │
│                                                  │ packaged into        │
│                                                  ▼                      │
│                                         SqsEmbeddingMessage            │
│                                                  │                      │
│                                                  │ stored as            │
│                                                  ▼                      │
│                                         EmbeddingDocument              │
│                                                                         │
│  MetadataUpdate ────────▶ MetadataParameter                            │
│       │                                                                 │
│       │ updates                                                         │
│       ▼                                                                 │
│  DocumentIngestionData ────▶ ProcessedDocument ────▶ EmbeddingDocument │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Common Use Cases

### 1. Website Ingestion Flow

```typescript
// Create website ingestion record
const ingestion: WebsiteIngestion = {
  PK: `ORG#${orgId}#WEBSITE_INGESTION`,
  SK: `KST_ID#${knowledgeStoreId}#WSI_ID#${uniqueId}`,
  url: "https://docs.example.com",
  knowledgeStoreId: "ks-abc123",
  id: uniqueId,
  latestChunkIndex: 0,
  metadata: [],
  sitemapProcessed: false,
  sitemapUrls: 0
};

// Queue extended event for processing
const event: ExtendedWebsiteIngestion = {
  ...ingestion,
  type: "websiteIngestion",
  action: "create",
  processingNumber: 0,
  correlationId: "req-123"
};
```

### 2. File Upload Processing

```typescript
// Handle S3 event
const s3Event: S3HandlerEvent = {
  action: "Create",
  bucket: "knowledge-uploads",
  key: "uploads/12345/ks-abc123/manual.pdf",
  version: "v1"
};

// Create appropriate processor
const processor = FileFactory.create("application/pdf", fileBlob);
const documents = await processor.load();

// Enrich chunks
const enrichedChunks = documents.map((chunk, index) => 
  enrichChunkMetadata({
    chunk,
    knowledgeStoreId: "ks-abc123",
    orgId: 12345,
    chunkIndex: index,
    chunksNumber: documents.length,
    documentId: s3Event.key,
    documentVersion: s3Event.version,
    customMetadata: {}
  })
);
```

### 3. Batch Embedding Queue

```typescript
// Prepare embedding message
const message: SqsEmbeddingMessage = {
  knowledgeStoreId: "ks-abc123",
  opensearchCollectionUrl: "https://collection.aoss.amazonaws.com",
  documents: enrichedChunks,
  markAsFinished: true,
  pk: ingestion.PK,
  sk: ingestion.SK,
  orgId: 12345,
  correlationId: "req-123"
};

// Send to SQS for processing
await sqsClient.send(new SendMessageCommand({
  QueueUrl: embeddingQueueUrl,
  MessageBody: JSON.stringify(message)
}));
```

---

## Related Documentation

- [Event Models](./event-models.md) - Event structures for S3 and SQS triggers
- [Pipeline Models](./pipeline-models.md) - Models for embedding and vector storage pipelines
- [Models Overview](./README.md) - Complete model reference index