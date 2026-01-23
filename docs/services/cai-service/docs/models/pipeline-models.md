# Pipeline Data Models

This document covers the data models used in the cai-service pipeline processing system, including document embedding, chunking, indexing, and file processing operations.

## Overview

The pipeline data models support the document processing workflow from file ingestion through embedding generation and storage in OpenSearch. These models handle:

- Document chunking and metadata enrichment
- Embedding generation and storage
- File type processing
- Pipeline metrics and monitoring

## Entity Relationship Diagram

```
┌─────────────────────┐     ┌─────────────────────┐
│     BaseFile        │     │   EnrichmentObject  │
│  (PdfFile, CsvFile, │     │                     │
│   JsonFile, TxtFile)│     └──────────┬──────────┘
└─────────┬───────────┘                │
          │                            │
          ▼                            ▼
┌─────────────────────┐     ┌─────────────────────┐
│     Document        │────▶│   ChunkMetadata     │
│  (LangChain Doc)    │     │                     │
└─────────┬───────────┘     └─────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│ SqsEmbeddingMessage │────▶│  EmbeddingDocument  │
│                     │     │                     │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │EmbeddingDocumentMeta│
                            │                     │
                            └─────────────────────┘
```

---

## Document Chunking Models

### EnrichMetadataParams

Parameters for enriching chunk metadata during document processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chunk | Document | Yes | The document chunk to enrich |
| knowledgeStoreId | string | Yes | Identifier for the knowledge store |
| orgId | number | Yes | Organization identifier |
| chunkIndex | number | Yes | Index of the current chunk (0-based) |
| chunksNumber | number | Yes | Total number of chunks in the document |
| documentId | string | Yes | Document identifier (typically S3 key or URL) |
| documentVersion | string | Yes | Version of the document |
| customMetadata | Record<string, unknown> | Yes | Custom metadata key-value pairs |
| websiteUrl | string | No | Optional website URL source for web-ingested content |

**Validation Rules:**
- `chunkIndex` must be >= 0 and < `chunksNumber`
- `chunksNumber` must be > 0
- `knowledgeStoreId` must be a valid UUID format

**Example:**
```json
{
  "chunk": {
    "pageContent": "This is the text content of the chunk...",
    "metadata": {}
  },
  "knowledgeStoreId": "kst-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "orgId": 12345,
  "chunkIndex": 0,
  "chunksNumber": 15,
  "documentId": "documents/12345/kst-a1b2c3d4/quarterly-report.pdf",
  "documentVersion": "v1.2.3",
  "customMetadata": {
    "department": "Finance",
    "confidentiality": "Internal",
    "author": "John Smith"
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
| chunkNumber | number | Yes | Index of the chunk (0-based) |
| totalChunks | number | Yes | Total number of chunks in document |
| timeStamp | string | Yes | ISO timestamp of processing |
| chunk_text | string | Yes | Text content of the chunk |
| customerMetadata | Record<string, unknown> | Yes | Custom metadata object |
| websiteUrl | string \| null | No | Source website URL if applicable |

**Validation Rules:**
- `timeStamp` must be valid ISO 8601 format
- `chunk_text` must not be empty

**Example:**
```json
{
  "orgId": 12345,
  "knowledgeStoreId": "kst-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "documentId": "documents/12345/kst-a1b2c3d4/quarterly-report.pdf",
  "documentVersion": "v1.2.3",
  "chunkNumber": 0,
  "totalChunks": 15,
  "timeStamp": "2024-01-15T10:30:00.000Z",
  "chunk_text": "Q4 2023 Financial Results\n\nRevenue increased by 15% compared to the previous quarter...",
  "customerMetadata": {
    "department": "Finance",
    "confidentiality": "Internal"
  },
  "websiteUrl": null
}
```

---

### EnrichmentObject

Object used for enriching chunk metadata during pipeline processing. Alias for `EnrichMetadataParams`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chunk | Document | Yes | The document chunk |
| knowledgeStoreId | string | Yes | Knowledge store identifier |
| orgId | number | Yes | Organization ID |
| chunkIndex | number | Yes | Index of this chunk |
| chunksNumber | number | Yes | Total number of chunks |
| documentId | string | Yes | Parent document identifier |
| documentVersion | string | Yes | Document version |
| customMetadata | Record<string, unknown> | Yes | Custom metadata to include |
| websiteUrl | string | No | Source website URL for website ingestions |

**Example:**
```json
{
  "chunk": {
    "pageContent": "Introduction to Machine Learning...",
    "metadata": {
      "source": "chapter1.txt",
      "page": 1
    }
  },
  "knowledgeStoreId": "kst-ml-docs-001",
  "orgId": 99999,
  "chunkIndex": 5,
  "chunksNumber": 42,
  "documentId": "ml-handbook-v2.pdf",
  "documentVersion": "2.0.1",
  "customMetadata": {
    "category": "Technical Documentation",
    "topic": "Machine Learning"
  },
  "websiteUrl": "https://docs.example.com/ml-handbook"
}
```

---

### ChunkingStrategies

Enum for document chunking strategy options.

| Field | Value | Description |
|-------|-------|-------------|
| RECURSIVE_STRATEGY | "recursive" | Default recursive text splitting strategy |

**Usage:**
```typescript
const strategy = ChunkingStrategies.RECURSIVE_STRATEGY;
```

---

## Embedding Models

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

**Validation Rules:**
- `opensearchCollectionUrl` must be a valid HTTPS URL
- `documents` must be an array

**Example:**
```json
{
  "knowledgeStoreId": "kst-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "opensearchCollectionUrl": "https://abc123.us-east-1.aoss.amazonaws.com",
  "documents": [
    {
      "pageContent": "Document content here...",
      "metadata": {
        "chunkNumber": 0,
        "totalChunks": 5
      }
    }
  ],
  "orgId": 12345,
  "markAsFinished": false,
  "pk": "ORG#12345#INGESTION",
  "sk": "KST_ID#kst-a1b2c3d4#DOC#doc-001",
  "correlationId": "corr-xyz-789"
}
```

---

### EmbeddingDocument

Document structure stored in OpenSearch with embeddings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metadata | EmbeddingDocumentMetadata | Yes | Document metadata including customer metadata |

**Relationships:**
- Contains `EmbeddingDocumentMetadata`
- Stored in OpenSearch index

**Example:**
```json
{
  "metadata": {
    "customerMetadata": {
      "department": "Engineering",
      "project": "Alpha",
      "sensitivity": "Low"
    }
  }
}
```

---

### EmbeddingDocumentMetadata

Metadata structure for embedding documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| customerMetadata | Record<string, unknown> | Yes | Custom metadata from customer |

**Example:**
```json
{
  "customerMetadata": {
    "documentType": "Technical Specification",
    "version": "3.0",
    "reviewedBy": "Jane Doe",
    "lastUpdated": "2024-01-10"
  }
}
```

---

### SqsEmbeddingMessage

Message structure for SQS embedding queue.

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

**Validation Rules:**
- `documents` array must not be empty unless `markAsFinished` is true
- `opensearchCollectionUrl` must be valid OpenSearch Serverless URL format

**Example:**
```json
{
  "knowledgeStoreId": "kst-docs-production",
  "opensearchCollectionUrl": "https://xyz789.us-west-2.aoss.amazonaws.com",
  "documents": [
    {
      "pageContent": "Chapter 1: Introduction\n\nThis document covers...",
      "metadata": {
        "source": "handbook.pdf",
        "page": 1,
        "chunkNumber": 0
      }
    },
    {
      "pageContent": "Chapter 1 (continued)...",
      "metadata": {
        "source": "handbook.pdf",
        "page": 1,
        "chunkNumber": 1
      }
    }
  ],
  "markAsFinished": false,
  "pk": "ORG#12345#INGESTION",
  "sk": "KST_ID#kst-docs-production#DOC#handbook.pdf",
  "orgId": 12345,
  "correlationId": "batch-001-xyz"
}
```

---

### Document

LangChain document structure for text processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pageContent | string | Yes | Text content of the document |
| metadata | Record<string, unknown> | Yes | Document metadata |

**Example:**
```json
{
  "pageContent": "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet.",
  "metadata": {
    "source": "sample.txt",
    "page": 1,
    "author": "Unknown",
    "createdAt": "2024-01-15T00:00:00Z"
  }
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
  "id": "doc_kst-abc123_chunk_0_v1",
  "embeddingDocument": {
    "metadata": {
      "customerMetadata": {
        "category": "Support",
        "priority": "High"
      }
    }
  }
}
```

---

### EmbeddingLanguageType

Enumeration of embedding language types for knowledge base.

| Field | Value | Description |
|-------|-------|-------------|
| ENGLISH_ONLY | "english" | English only embeddings |

---

## File Processing Models

### BaseFile

Abstract base class for file processing that converts files into LangChain Documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The binary file data to be processed |

**Subclasses:** `PdfFile`, `TxtFile`, `JsonFile`, `CsvFile`

---

### PdfFile

File processor for PDF documents, converts PDF files to LangChain Documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The PDF file data (inherited from BaseFile) |

**Supported MIME Types:** `application/pdf`

**Usage:**
```typescript
const pdfProcessor = new PdfFile(pdfBlob);
const documents = await pdfProcessor.toDocuments();
```

---

### CsvFile

File processor for CSV documents, converts CSV files to LangChain Documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The CSV file data (inherited from BaseFile) |

**Supported MIME Types:** `text/csv`, `application/csv`

**Usage:**
```typescript
const csvProcessor = new CsvFile(csvBlob);
const documents = await csvProcessor.toDocuments();
```

---

### JsonFile

File processor for JSON documents, converts JSON files to LangChain Documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The JSON file data (inherited from BaseFile) |

**Supported MIME Types:** `application/json`

**Usage:**
```typescript
const jsonProcessor = new JsonFile(jsonBlob);
const documents = await jsonProcessor.toDocuments();
```

---

### TxtFile

File processor for plain text documents, converts text files to LangChain Documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileBlob | Blob | Yes | The text file data (inherited from BaseFile) |

**Supported MIME Types:** `text/plain`

**Usage:**
```typescript
const txtProcessor = new TxtFile(txtBlob);
const documents = await txtProcessor.toDocuments();
```

---

### FileTypes

Union type for supported file processors.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | PdfFile \| TxtFile \| JsonFile \| CsvFile | Yes | One of the supported file type handlers |

**Example:**
```typescript
type FileTypes = PdfFile | TxtFile | JsonFile | CsvFile;
```

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

**Example Registry:**
```typescript
const registry: FileRegistry = {
  'application/pdf': PdfFile,
  'text/plain': TxtFile,
  'text/csv': CsvFile,
  'application/json': JsonFile
};
```

---

### FileFactory

Factory class for creating appropriate file processor instances based on MIME type.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fileRegistry | FileRegistry | Yes (static) | Static registry mapping MIME types to file processor classes |

**Usage:**
```typescript
const processor = FileFactory.create('application/pdf', pdfBlob);
const documents = await processor.toDocuments();
```

**Supported MIME Types:**
- `application/pdf` → `PdfFile`
- `text/plain` → `TxtFile`
- `text/csv` → `CsvFile`
- `application/json` → `JsonFile`

---

## Pipeline Monitoring Models

### PipelineMetric

Metric structure for pipeline monitoring.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| value | number | Yes | Metric value |
| name | MetricType | Yes | Metric type name |
| unit | MetricsUnit | Yes | Unit of measurement |

**Example:**
```json
{
  "value": 1500,
  "name": "ChunksProcessed",
  "unit": "Count"
}
```

---

### MetricDimension

Dimension structure for metric categorization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ProcessingSource | KnowledgeBaseDimensions | Yes | Source of processing |
| Status | KnowledgeBaseDimensions | Yes | Status of the operation |

**Example:**
```json
{
  "ProcessingSource": "S3Upload",
  "Status": "Success"
}
```

---

### ProcessInfo

Process information structure for logging running processes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pid | number | Yes | Process ID |
| command | string | Yes | Process command line |

**Example:**
```json
{
  "pid": 12345,
  "command": "node /app/embedder/index.js"
}
```

---

### DocumentIngestionData

Data structure for document metadata during metadata updates.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| documentId | string | Yes | Document identifier (S3 key or URL) |
| metadata | Record<string, unknown>[] | Yes | Current metadata array |
| pk | string | Yes | Partition key |
| sk | string | Yes | Sort key |

**Example:**
```json
{
  "documentId": "uploads/12345/kst-abc/report.pdf",
  "metadata": [
    { "key": "department", "value": "Sales" },
    { "key": "year", "value": "2024" }
  ],
  "pk": "ORG#12345#DOCUMENT",
  "sk": "KST_ID#kst-abc#DOC#report.pdf"
}
```

---

## Common Use Cases

### Processing a New Document

1. File is received and identified by MIME type
2. `FileFactory` creates appropriate processor (`PdfFile`, `TxtFile`, etc.)
3. Processor converts file to `Document[]` array
4. Each document is chunked using `ChunkingStrategies.RECURSIVE_STRATEGY`
5. `EnrichMetadataParams` is created for each chunk
6. Chunks receive `ChunkMetadata` with full context
7. `SqsEmbeddingMessage` is sent to embedding queue
8. Embedder creates `EmbeddingDocument` entries in OpenSearch

### Batch Embedding Processing

```typescript
// Create embedding message for batch processing
const embeddingMessage: SqsEmbeddingMessage = {
  knowledgeStoreId: "kst-production",
  opensearchCollectionUrl: "https://search.example.com",
  documents: enrichedChunks,
  markAsFinished: isLastBatch,
  pk: "ORG#12345#INGESTION",
  sk: "KST_ID#kst-production#DOC#batch-001",
  orgId: 12345,
  correlationId: "batch-processing-001"
};

// Send to SQS for processing
await sqsClient.sendMessage({
  QueueUrl: embeddingQueueUrl,
  MessageBody: JSON.stringify(embeddingMessage)
});
```

### Monitoring Pipeline Health

```typescript
// Emit pipeline metric
const metric: PipelineMetric = {
  value: documentsProcessed,
  name: "DocumentsProcessed",
  unit: "Count"
};

const dimensions: MetricDimension = {
  ProcessingSource: "S3Upload",
  Status: "Success"
};
```

---

## Related Documentation

- [Ingestion Models](./ingestion-models.md) - Models for document and website ingestion
- [Event Models](./event-models.md) - S3 and SQS event structures
- [Models Overview](./README.md) - Complete model index