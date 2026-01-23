# Pipeline Package Overview

[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![API](https://img.shields.io/badge/API-REST%20%7C%20WebSocket-orange)](docs/api/)

> A TypeScript NodeJS monorepo providing Conversational AI services with REST API, WebSocket, and data pipeline capabilities for executing AI prompts across multiple models and services

---

## 📑 Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Processing Flow](#processing-flow)
- [Lambda Functions](#lambda-functions)
- [Supported File Types](#supported-file-types)
- [Component Index](#component-index)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Documentation](#documentation)

---

## Overview

The **cai-service** pipeline package is a comprehensive knowledge ingestion and processing system designed to power Conversational AI applications. It enables developers to ingest, process, and index content from multiple sources—including websites, documents, and structured data—transforming them into vector embeddings for semantic search and AI-powered interactions.

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-model AI Execution** | Execute prompts across multiple AI models and services with unified interface |
| **REST & WebSocket APIs** | Dual protocol support for synchronous and real-time communication |
| **Knowledge Ingestion Pipeline** | Automated web crawling and content extraction |
| **Document Processing** | Native support for PDF, CSV, JSON, and TXT formats |
| **Vector Embeddings** | Automatic generation and indexing for semantic search |
| **Sitemap Scraping** | Intelligent website discovery and content extraction |

---

## Pipeline Architecture

The cai-service pipeline follows an event-driven, serverless architecture built on AWS Lambda functions orchestrated through an event system. This design ensures scalability, fault tolerance, and efficient resource utilization.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INGESTION LAYER                                    │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Web Crawler    │  File Upload    │  API Ingestion  │  Sitemap Discovery    │
│  Service        │  Handler        │  Endpoint       │  Service              │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬────────────┘
         │                 │                 │                   │
         └─────────────────┴────────┬────────┴───────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVENT BUS (SQS/SNS)                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  Content        │  Document       │  Text           │  Metadata             │
│  Extractor      │  Parser         │  Chunker        │  Enricher             │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬────────────┘
         │                 │                 │                   │
         └─────────────────┴────────┬────────┴───────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EMBEDDING LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                    Vector Embedding Generator (Multi-Model)                  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                      │
├─────────────────┬─────────────────┬─────────────────────────────────────────┤
│  Vector Store   │  Document Store │  Metadata Index                         │
│  (Pinecone/     │  (S3/DynamoDB)  │  (Elasticsearch)                        │
│   Weaviate)     │                 │                                         │
└─────────────────┴─────────────────┴─────────────────────────────────────────┘
```

### Architecture Components

| Layer | Purpose | Technologies |
|-------|---------|--------------|
| **Ingestion** | Content acquisition from various sources | Lambda, API Gateway, Step Functions |
| **Event Bus** | Async message passing and orchestration | SQS, SNS, EventBridge |
| **Processing** | Content transformation and preparation | Lambda, ECS Tasks |
| **Embedding** | Vector generation for semantic indexing | OpenAI, Cohere, HuggingFace |
| **Storage** | Persistent storage for vectors and documents | Pinecone, S3, DynamoDB |

---

## Processing Flow

The pipeline processes content through a series of well-defined stages, each handled by specialized Lambda functions.

### Stage 1: Content Acquisition

```typescript
// Example: Triggering content ingestion via REST API
import axios from 'axios';

interface IngestionRequest {
  source: 'url' | 'file' | 'sitemap';
  target: string;
  options?: {
    depth?: number;
    includeImages?: boolean;
    followLinks?: boolean;
  };
}

const ingestContent = async (request: IngestionRequest) => {
  const response = await axios.post(
    'https://api.cai-service.com/v1/pipeline/ingest',
    request,
    {
      headers: {
        'Authorization': `Bearer ${process.env.CAI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  return response.data.jobId;
};

// Ingest from URL
const jobId = await ingestContent({
  source: 'url',
  target: 'https://example.com/documentation',
  options: {
    depth: 2,
    followLinks: true
  }
});
```

### Stage 2: Document Processing

```typescript
// Example: Custom document processor configuration
interface ProcessorConfig {
  chunkSize: number;
  chunkOverlap: number;
  preserveFormatting: boolean;
  extractMetadata: boolean;
}

const processorConfig: ProcessorConfig = {
  chunkSize: 1000,        // tokens per chunk
  chunkOverlap: 200,      // overlap between chunks
  preserveFormatting: true,
  extractMetadata: true
};
```

### Stage 3: Embedding Generation

```typescript
// Example: Embedding configuration
interface EmbeddingConfig {
  model: 'openai' | 'cohere' | 'huggingface';
  dimensions: number;
  batchSize: number;
}

const embeddingConfig: EmbeddingConfig = {
  model: 'openai',
  dimensions: 1536,
  batchSize: 100
};
```

### Processing Flow Diagram

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Ingest  │───▶│  Parse   │───▶│  Chunk   │───▶│  Embed   │───▶│  Index   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │              │               │               │               │
     ▼              ▼               ▼               ▼               ▼
  Job Queue    Raw Content     Text Chunks     Vectors        Searchable
  Created      Extracted       Generated       Created        Knowledge Base
```

---

## Lambda Functions

The pipeline leverages a suite of specialized Lambda functions, each responsible for a specific processing task.

| Function | Purpose | Trigger | Timeout |
|----------|---------|---------|---------|
| `ingest-handler` | Receives and validates ingestion requests | API Gateway | 30s |
| `crawler-worker` | Crawls web pages and extracts content | SQS | 5min |
| `sitemap-parser` | Discovers URLs from XML sitemaps | SQS | 2min |
| `document-parser` | Parses PDF, CSV, JSON, TXT files | S3 Event | 5min |
| `text-chunker` | Splits documents into semantic chunks | SQS | 1min |
| `embedding-generator` | Creates vector embeddings | SQS | 3min |
| `index-writer` | Writes vectors to storage | SQS | 1min |
| `job-orchestrator` | Manages pipeline state and flow | Step Functions | 15min |

### Lambda Function Example

```typescript
// packages/pipeline/src/lambdas/document-parser/handler.ts
import { S3Event, Context } from 'aws-lambda';
import { DocumentParser } from '../../services/document-parser';
import { EventPublisher } from '../../services/event-publisher';

export const handler = async (event: S3Event, context: Context) => {
  const parser = new DocumentParser();
  const publisher = new EventPublisher();
  
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key);
    
    try {
      // Parse the document
      const content = await parser.parse({ bucket, key });
      
      // Publish to next stage
      await publisher.publish('document.parsed', {
        jobId: extractJobId(key),
        content,
        metadata: {
          source: `s3://${bucket}/${key}`,
          parsedAt: new Date().toISOString()
        }
      });
      
    } catch (error) {
      console.error(`Failed to parse ${key}:`, error);
      await publisher.publish('document.failed', {
        key,
        error: error.message
      });
    }
  }
};
```

---

## Supported File Types

The cai-service pipeline supports a comprehensive range of file formats for knowledge ingestion.

### Document Formats

| Format | Extension | Parser | Max Size | Features |
|--------|-----------|--------|----------|----------|
| **PDF** | `.pdf` | `pdf-parse` | 50MB | Text extraction, OCR support, image extraction |
| **CSV** | `.csv` | `papaparse` | 100MB | Header detection, type inference, streaming |
| **JSON** | `.json` | Native | 25MB | Schema validation, nested structure flattening |
| **Plain Text** | `.txt` | Native | 10MB | Encoding detection, line normalization |
| **Markdown** | `.md` | `marked` | 10MB | Front matter parsing, link extraction |
| **HTML** | `.html` | `cheerio` | 25MB | DOM parsing, script removal, text extraction |

### Web Content

| Source Type | Handler | Features |
|-------------|---------|----------|
| **Single URL** | `url-crawler` | JavaScript rendering, dynamic content |
| **Sitemap** | `sitemap-parser` | XML parsing, priority filtering |
| **RSS Feed** | `feed-parser` | Atom/RSS support, date filtering |

### File Processing Example

```typescript
// Example: Processing different file types
import { FileProcessor } from '@cai-service/pipeline';

const processor = new FileProcessor();

// Process PDF
const pdfResult = await processor.process({
  type: 'pdf',
  source: './documents/manual.pdf',
  options: {
    extractImages: true,
    ocrEnabled: true
  }
});

// Process CSV
const csvResult = await processor.process({
  type: 'csv',
  source: './data/products.csv',
  options: {
    hasHeader: true,
    delimiter: ',',
    textColumns: ['description', 'features']
  }
});

// Process JSON
const jsonResult = await processor.process({
  type: 'json',
  source: './data/knowledge-base.json',
  options: {
    flattenDepth: 3,
    textPaths: ['$.articles[*].content']
  }
});
```

---

## Component Index

### Core Packages

| Package | Path | Description |
|---------|------|-------------|
| `@cai-service/pipeline-core` | `packages/pipeline/core` | Core pipeline orchestration and utilities |
| `@cai-service/crawlers` | `packages/pipeline/crawlers` | Web crawling and content extraction |
| `@cai-service/parsers` | `packages/pipeline/parsers` | Document parsing implementations |
| `@cai-service/embeddings` | `packages/pipeline/embeddings` | Vector embedding generation |
| `@cai-service/storage` | `packages/pipeline/storage` | Storage adapters (S3, Pinecone, etc.) |

### Service Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `ContentExtractor` | `core/extractors/` | Extracts text from various formats |
| `TextChunker` | `core/chunkers/` | Semantic text chunking |
| `MetadataEnricher` | `core/enrichers/` | Adds metadata to documents |
| `EmbeddingService` | `embeddings/services/` | Multi-model embedding generation |
| `VectorStore` | `storage/vector/` | Vector database operations |

### Lambda Handlers

| Handler | Path | Event Source |
|---------|------|--------------|
| `ingest-handler` | `lambdas/ingest/` | API Gateway |
| `crawler-worker` | `lambdas/crawler/` | SQS |
| `document-parser` | `lambdas/parser/` | S3 |
| `embedding-generator` | `lambdas/embeddings/` | SQS |

---

## Quick Start

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher
- Docker and Docker Compose
- AWS CLI configured (for deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/cai-service.git
cd cai-service

# Install dependencies
npm install

# Build all packages
npm run build

# Run tests
npm test
```

### Running Locally with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f pipeline

# Run specific service
docker-compose up pipeline-worker
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  pipeline-api:
    build:
      context: .
      dockerfile: packages/pipeline/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - AWS_REGION=us-east-1
    volumes:
      - ./packages:/app/packages

  pipeline-worker:
    build:
      context: .
      dockerfile: packages/pipeline/Dockerfile.worker
    environment:
      - NODE_ENV=development
      - QUEUE_URL=http://localstack:4566/queue/pipeline
    depends_on:
      - localstack

  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,sqs,sns,dynamodb
```

---

## Configuration

The pipeline supports 22 configuration variables for customizing behavior.

### Environment Variables

```bash
# Core Configuration
CAI_API_KEY=your-api-key
CAI_ENVIRONMENT=development
CAI_LOG_LEVEL=info

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Pipeline Configuration
PIPELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/pipeline
PIPELINE_BUCKET_NAME=cai-service-documents
PIPELINE_MAX_CONCURRENT=10

# Embedding Configuration
EMBEDDING_MODEL=openai
OPENAI_API_KEY=your-openai-key
EMBEDDING_BATCH_SIZE=100

# Vector Store Configuration
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=cai-knowledge

# Crawler Configuration
CRAWLER_MAX_DEPTH=3
CRAWLER_RATE_LIMIT=10
CRAWLER_USER_AGENT=CAI-Service-Bot/1.0
```

### Configuration File

```typescript
// config/pipeline.config.ts
export const pipelineConfig = {
  ingestion: {
    maxFileSize: 50 * 1024 * 1024, // 50MB
    allowedTypes: ['pdf', 'csv', 'json', 'txt', 'md', 'html'],
    timeout: 300000 // 5 minutes
  },
  processing: {
    chunkSize: 1000,
    chunkOverlap: 200,
    maxChunksPerDocument: 1000
  },
  embedding: {
    model: process.env.EMBEDDING_MODEL || 'openai',
    batchSize: parseInt(process.env.EMBEDDING_BATCH_SIZE || '100'),
    retryAttempts: 3
  },
  storage: {
    vectorStore: process.env.VECTOR_STORE_TYPE || 'pinecone',
    documentStore: 's3',
    metadataStore: 'dynamodb'
  }
};
```

---

## Documentation

For detailed information on specific components, refer to the following documentation:

| Document | Description |
|----------|-------------|
| [Lambda Functions](docs/pipeline/lambdas.md) | Detailed documentation for all Lambda function handlers |
| [Web Crawling Services](docs/pipeline/crawlers.md) | Guide to web crawling configuration and customization |
| [File Processing](docs/pipeline/file-processing.md) | In-depth file processing options and supported formats |
| [Event System](docs/pipeline/events.md) | Event-driven architecture and message schemas |

### Additional Resources

- [API Reference](docs/api/README.md) - REST and WebSocket API documentation
- [Deployment Guide](docs/deployment/README.md) - AWS deployment instructions
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Contributing](CONTRIBUTING.md) - Guidelines for contributors

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ETIMEOUT` on crawling | Rate limiting | Reduce `CRAWLER_RATE_LIMIT` |
| Empty embeddings | Invalid content | Check document parsing logs |
| Queue backlog | Processing bottleneck | Increase `PIPELINE_MAX_CONCURRENT` |
| Memory errors | Large documents | Enable streaming processing |

### Debug Mode

```bash
# Enable debug logging
export CAI_LOG_LEVEL=debug
npm run start:pipeline

# Run with verbose output
DEBUG=cai:* npm run start:pipeline
```

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/cai-service/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/cai-service/discussions)
- **Documentation**: [Full Documentation](https://docs.cai-service.com)

---

<p align="center">
  <sub>Built with ❤️ by the CAI Service Team</sub>
</p>