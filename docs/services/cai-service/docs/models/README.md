# Data Models Overview

## Introduction

The CAI Service (Conversational AI Service) utilizes a comprehensive set of data models organized across multiple domains to support document processing, AI-powered conversations, knowledge management, and real-time WebSocket communications. This document provides a high-level overview of the data architecture and serves as an index to detailed model documentation.

## Data Architecture Overview

The service's data models are organized into four primary domains:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CAI Service Data Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  Event Models    │───▶│ Pipeline Models  │───▶│ Ingestion Models │       │
│  │                  │    │                  │    │                  │        │
│  │  - S3 Events     │    │  - Processing    │    │  - Documents     │       │
│  │  - WebSocket     │    │  - Monitoring    │    │  - Embeddings    │       │
│  │  - Metadata      │    │  - File Types    │    │  - Knowledge     │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
│           │                      │                       │                   │
│           └──────────────────────┼───────────────────────┘                   │
│                                  ▼                                           │
│                    ┌──────────────────────────┐                              │
│                    │     AI Conversation      │                              │
│                    │        Models            │                              │
│                    │                          │                              │
│                    │  - Messages & Sessions   │                              │
│                    │  - Agent Configuration   │                              │
│                    │  - Tool Definitions      │                              │
│                    └──────────────────────────┘                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Model Categories

### 1. Pipeline Models
**Total Models: ~25** | [Detailed Documentation →](./pipeline-models.md)

Pipeline models handle the processing workflow for documents and website content, including file processing, chunking, and monitoring.

| Category | Description | Key Models |
|----------|-------------|------------|
| File Processing | Abstract and concrete file processors | `BaseFile`, `PdfFile`, `CsvFile`, `JsonFile`, `TxtFile` |
| Factory Pattern | File type creation and registration | `FileFactory`, `FileRegistry`, `FactoryFileTypes` |
| Monitoring | Pipeline execution tracking | `PipelineMetric`, `MetricDimension`, `CrawlerMonitoring`, `IngestionMonitoring` |
| Browser Automation | Web crawling infrastructure | `BrowserInitResult`, `BrowserReinitResult`, `PageContentResult` |
| Worker Results | Processing outcome structures | `CrawlWorkerResult`, `IngestionWorkerResult` |

### 2. Ingestion Models
**Total Models: ~30** | [Detailed Documentation →](./ingestion-models.md)

Ingestion models manage the flow of documents into the knowledge base, including website crawling, document embedding, and metadata management.

| Category | Description | Key Models |
|----------|-------------|------------|
| Website Ingestion | Website crawling and page tracking | `WebsiteIngestion`, `IngestionPage`, `ExtendedWebsiteIngestion` |
| Document Processing | Document chunking and enrichment | `Document`, `ChunkMetadata`, `EnrichMetadataParams`, `EnrichmentObject` |
| Embeddings | Vector storage structures | `EmbeddingDocument`, `EmbeddingDocumentMetadata`, `SqsEmbeddingMessage` |
| Sitemaps | Sitemap parsing structures | `SitemapEntry`, `SitemapIndexEntry` |
| Status Enums | Processing state tracking | `IngestionStatuses`, `CrawlingStatuses`, `ChunkingStrategies` |

### 3. Event Models
**Total Models: ~15** | [Detailed Documentation →](./event-models.md)

Event models define the structures for system events, including S3 triggers, SQS messages, and metadata update events.

| Category | Description | Key Models |
|----------|-------------|------------|
| S3 Events | S3 file operation triggers | `S3HandlerEvent`, `S3EventRecord`, `GetS3Object` |
| Queue Messages | SQS message structures | `KnowledgeEmbedderEventPayload`, `UnprocessedEvents` |
| Metadata Events | Metadata update operations | `MetadataUpdate`, `MetadataParameter`, `DocumentIngestionData` |

### 4. AI Conversation Models
**Total Models: ~35** | Documented below

AI conversation models power the real-time conversational AI features, including WebSocket communication, agent configuration, and chat history.

| Category | Description | Key Models |
|----------|-------------|------------|
| WebSocket | Real-time communication | `WebsocketCompletionSchema`, `WebsocketAuthPayload`, `AuthenticatedWebSocket` |
| Agent Configuration | AI agent setup | `AgentConfig`, `AgentOptions`, `RawAgentOptions`, `AgentCompletion` |
| Tools | Function calling definitions | `ToolRequest`, `ToolParameters`, `ToolProperty` |
| Messages | Chat history structures | `Message`, `ChatHistory`, `PreviewMessage`, `CreateMessageDTO` |
| AI Service Inputs | Service layer DTOs | `CompletionAIServiceInput`, `InferenceAIServiceInput`, `ConversationAIServiceInput` |
| Pricing | Model cost calculation | `ModelPricing`, `BEDROCK_PRICING_TABLE`, `OPENAI_PRICING_TABLE` |

## Key Enumerations

The service uses several critical enumerations across domains:

| Enumeration | Values | Used In |
|-------------|--------|---------|
| `AIModelProvider` | `OPENAI`, `BEDROCK` | AI service configuration |
| `AIModelRole` | `USER`, `ASSISTANT` | Message handling |
| `ToolType` | `REST_TOOL`, `MACRO_TOOL`, `SALESFORCE_TOOL`, `KNOWLEDGE_BASE_TOOL` | Agent tools |
| `IngestionStatuses` | `IN_PROGRESS`, `SUCCESS`, `FAILED`, `BLOCKED`, `DELETED` | Document processing |
| `CrawlingStatuses` | `STARTING`, `SUCCESS`, `FAILED`, `BLOCKED` | Website crawling |
| `EmbeddingLanguageType` | `ENGLISH_ONLY` | Knowledge base |

## Cross-Domain Relationships

### Event → Pipeline Flow
```
S3HandlerEvent ──────┐
                     ├──▶ UnprocessedEvents ──▶ FileFactory ──▶ BaseFile subclasses
ExtendedWebsiteIngestion─┘
```

### Pipeline → Ingestion Flow
```
BaseFile.toDocument() ──▶ Document ──▶ EnrichMetadataParams ──▶ ChunkMetadata
                                              │
                                              ▼
                                    SqsEmbeddingMessage ──▶ EmbeddingDocument
```

### Ingestion → AI Conversation Flow
```
EmbeddingDocument ──▶ KnowledgeBaseToolServiceInput ──▶ ToolRequest
                                                              │
                                                              ▼
                                                    WebsocketCompletionSchema
```

## Storage Patterns

### DynamoDB Key Structure
Most DynamoDB models follow a consistent key pattern:

| Model Type | PK Pattern | SK Pattern |
|------------|------------|------------|
| Website Ingestion | `ORG#<orgId>#WEBSITE_INGESTION` | `KST_ID#<knowledgeStoreId>#WSI_ID#<uniqueId>` |
| Ingestion Page | `ORG#<orgId>#WEBSITE_INGESTION_PAGE` | `KST_ID#<knowledgeStoreId>#WSI_ID#<uniqueId>#PAGE#<url>` |
| Message | `ORG#<orgId>#SESSION#<sessionId>` | `MSG#<epochTimestamp>` |

### S3 Key Structure
```
<prefix>/<orgId>/<knowledgeStoreId>/<fileName>
```

## Validation

The service uses Zod schemas for runtime validation of critical models:

- `WebsocketCompletionSchema` - Validates all WebSocket completion requests
- Tool parameter schemas - Validates function calling inputs
- Inference configuration - Validates AI model parameters

## Detailed Documentation

For complete field-level documentation, validation rules, and JSON examples, refer to the domain-specific documentation:

- **[Pipeline Models](./pipeline-models.md)** - File processing, monitoring, and worker models
- **[Ingestion Models](./ingestion-models.md)** - Document ingestion, embeddings, and knowledge base models
- **[Event Models](./event-models.md)** - S3 events, SQS messages, and metadata update models

## Model Count Summary

| Domain | Model Count |
|--------|-------------|
| Pipeline Models | ~25 |
| Ingestion Models | ~30 |
| Event Models | ~15 |
| AI Conversation Models | ~35 |
| **Total** | **~90** |