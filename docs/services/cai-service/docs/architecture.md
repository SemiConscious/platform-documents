# System Architecture

## Overview

The cai-service is a sophisticated TypeScript NodeJS monorepo that provides Conversational AI services through multiple interfaces: REST API, WebSocket connections, and data pipeline capabilities. This architecture enables multi-model AI prompt execution across various providers while supporting knowledge ingestion, document processing, and vector-based semantic search.

This document provides a comprehensive view of how the system's components interact, the dependencies between packages, data flow patterns, and the underlying AWS infrastructure that powers the service.

## System Overview

### Architectural Philosophy

The cai-service follows a **modular monorepo architecture** designed around the principles of:

1. **Separation of Concerns**: Each package handles a specific domain (API, real-time communication, data processing)
2. **Shared Core Logic**: Common functionality is abstracted into reusable packages
3. **Interface Flexibility**: Multiple entry points (REST, WebSocket, Pipeline) for different use cases
4. **Scalability**: Independent scaling of components based on workload characteristics

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              External Clients                                │
│                    (Web Apps, Mobile Apps, Third-party Services)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS API Gateway / ALB                              │
│                    (Load Balancing, Rate Limiting, Auth)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                    │                    │
                    ▼                    ▼                    ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│     REST Package     │  │   WebSocket Package  │  │   Pipeline Package   │
│  (Synchronous API)   │  │   (Real-time Comm)   │  │   (Batch Processing) │
│                      │  │                      │  │                      │
│  • POST /prompt      │  │  • Connection Mgmt   │  │  • Web Crawling      │
│  • GET /knowledge    │  │  • Streaming AI      │  │  • Document Ingestion│
│  • POST /ingest      │  │  • Live Updates      │  │  • Vector Generation │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Core Package                                    │
│         (Business Logic, AI Model Adapters, Prompt Execution Engine)        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Common Package                                   │
│      (Shared Types, Utilities, Database Clients, External API Wrappers)     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    PostgreSQL/RDS    │  │   Vector Database    │  │   AI Model APIs      │
│   (Structured Data)  │  │   (Embeddings)       │  │   (OpenAI, Claude,   │
│                      │  │                      │  │    Anthropic, etc.)  │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

### Package Responsibilities

| Package | Primary Function | Interface Type | Scaling Pattern |
|---------|-----------------|----------------|-----------------|
| REST | Synchronous API requests | HTTP/HTTPS | Horizontal (Lambda/ECS) |
| WebSocket | Real-time bidirectional communication | WSS | Connection-based (API Gateway) |
| Pipeline | Batch data processing and ingestion | Event-driven | Queue-based (SQS/Lambda) |
| Core | Business logic and AI orchestration | Internal | Shared across packages |
| Common | Utilities and shared infrastructure | Internal | Bundled with consumers |

## Package Dependencies

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                        packages/rest                            │
│  Dependencies:                                                  │
│    ├── @cai-service/core                                       │
│    ├── @cai-service/common                                     │
│    ├── express / fastify                                       │
│    └── AWS SDK (Lambda, API Gateway)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ imports
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      packages/websocket                         │
│  Dependencies:                                                  │
│    ├── @cai-service/core                                       │
│    ├── @cai-service/common                                     │
│    ├── ws / socket.io                                          │
│    └── AWS SDK (API Gateway WebSocket)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ imports
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      packages/pipeline                          │
│  Dependencies:                                                  │
│    ├── @cai-service/core                                       │
│    ├── @cai-service/common                                     │
│    ├── cheerio / puppeteer (web crawling)                      │
│    ├── pdf-parse, csv-parse (document processing)              │
│    └── AWS SDK (S3, SQS, Lambda)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ imports
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        packages/core                            │
│  Dependencies:                                                  │
│    ├── @cai-service/common                                     │
│    ├── openai / anthropic SDK                                  │
│    ├── langchain (optional orchestration)                      │
│    └── tiktoken (token counting)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ imports
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       packages/common                           │
│  Dependencies:                                                  │
│    ├── pg / typeorm (PostgreSQL)                               │
│    ├── ioredis (caching)                                       │
│    ├── winston / pino (logging)                                │
│    ├── zod (validation)                                        │
│    └── AWS SDK core                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Package.json Structure

```json
{
  "name": "@cai-service/root",
  "private": true,
  "workspaces": [
    "packages/common",
    "packages/core",
    "packages/rest",
    "packages/websocket",
    "packages/pipeline"
  ],
  "scripts": {
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "dev:rest": "turbo run dev --filter=@cai-service/rest",
    "dev:websocket": "turbo run dev --filter=@cai-service/websocket",
    "dev:pipeline": "turbo run dev --filter=@cai-service/pipeline"
  }
}
```

### Internal Package References

```json
// packages/rest/package.json
{
  "name": "@cai-service/rest",
  "dependencies": {
    "@cai-service/core": "workspace:*",
    "@cai-service/common": "workspace:*"
  }
}

// packages/core/package.json
{
  "name": "@cai-service/core",
  "dependencies": {
    "@cai-service/common": "workspace:*"
  }
}
```

## Data Flow

### REST API Flow (Synchronous Prompt Execution)

```
Client Request                Processing                      Response
─────────────────────────────────────────────────────────────────────────

POST /api/v1/prompt    ──►   REST Handler         ──►   JSON Response
{                             │
  "prompt": "...",            ▼
  "model": "gpt-4",     Validate Request
  "context": {...}            │
}                             ▼
                        Core.executePrompt()
                              │
                        ┌─────┴─────┐
                        ▼           ▼
                   Load Context   Select Model
                   from Vector DB  Adapter
                        │           │
                        └─────┬─────┘
                              ▼
                        Compose Prompt
                        with Context
                              │
                              ▼
                        Call AI Provider
                        (OpenAI/Anthropic)
                              │
                              ▼
                        Process Response
                              │
                              ▼
                        Store in Database
                        (conversation history)
                              │
                              ▼
                        Return Response ────────────►  {
                                                        "response": "...",
                                                        "tokens_used": 150,
                                                        "model": "gpt-4"
                                                      }
```

### WebSocket Flow (Streaming Response)

```
┌─────────┐          ┌──────────────┐          ┌─────────┐          ┌──────────┐
│ Client  │          │  WebSocket   │          │  Core   │          │ AI Model │
│         │          │   Handler    │          │ Package │          │   API    │
└────┬────┘          └──────┬───────┘          └────┬────┘          └────┬─────┘
     │                      │                       │                     │
     │ WS Connect           │                       │                     │
     │─────────────────────►│                       │                     │
     │                      │                       │                     │
     │ Auth Token           │                       │                     │
     │─────────────────────►│                       │                     │
     │                      │ Validate Session      │                     │
     │                      │──────────────────────►│                     │
     │                      │                       │                     │
     │ Connection Ack       │                       │                     │
     │◄─────────────────────│                       │                     │
     │                      │                       │                     │
     │ Send Prompt          │                       │                     │
     │─────────────────────►│                       │                     │
     │                      │ executePromptStream() │                     │
     │                      │──────────────────────►│                     │
     │                      │                       │ Stream Request      │
     │                      │                       │────────────────────►│
     │                      │                       │                     │
     │                      │                       │ Token 1             │
     │ Stream Chunk 1       │     Chunk 1          │◄────────────────────│
     │◄─────────────────────│◄──────────────────────│                     │
     │                      │                       │ Token 2             │
     │ Stream Chunk 2       │     Chunk 2          │◄────────────────────│
     │◄─────────────────────│◄──────────────────────│                     │
     │                      │                       │ Token N             │
     │ Stream Chunk N       │     Chunk N          │◄────────────────────│
     │◄─────────────────────│◄──────────────────────│                     │
     │                      │                       │ [DONE]              │
     │ Stream Complete      │   Complete           │◄────────────────────│
     │◄─────────────────────│◄──────────────────────│                     │
     │                      │                       │                     │
```

### Pipeline Flow (Knowledge Ingestion)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE INGESTION PIPELINE                        │
└───────────────────────────────────────────────────────────────────────────┘

 Source Input              Processing Stages                Output
─────────────────────────────────────────────────────────────────────────────

 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 │   Website   │────►│ Web Crawler │────►│  Content    │────►│   Text      │
 │   (URL)     │     │  (Sitemap)  │     │  Extractor  │     │  Chunks     │
 └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                    │
 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
 │   PDF       │────►│ PDF Parser  │────►│   Text      │────────────┤
 │  Document   │     │             │     │  Extraction │            │
 └─────────────┘     └─────────────┘     └─────────────┘            │
                                                                    │
 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
 │   CSV/JSON  │────►│ Data Parser │────►│  Structured │────────────┤
 │   Files     │     │             │     │  to Text    │            │
 └─────────────┘     └─────────────┘     └─────────────┘            │
                                                                    │
 ┌─────────────┐     ┌─────────────┐                                │
 │   Plain     │────►│   Direct    │─────────────────────────────────┤
 │   Text      │     │   Input     │                                │
 └─────────────┘     └─────────────┘                                │
                                                                    ▼
                     ┌─────────────────────────────────────────────────────┐
                     │              Text Chunking Engine                    │
                     │   • Semantic chunking (paragraph boundaries)        │
                     │   • Fixed-size chunks with overlap                  │
                     │   • Token-aware splitting                           │
                     └─────────────────────────────────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │           Vector Embedding Generation               │
                     │   • OpenAI text-embedding-ada-002                   │
                     │   • Batch processing for efficiency                 │
                     │   • 1536-dimensional vectors                        │
                     └─────────────────────────────────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │              Storage & Indexing                      │
                     │   ┌────────────────┐    ┌────────────────┐          │
                     │   │  PostgreSQL    │    │ Vector Store   │          │
                     │   │  (Metadata)    │    │ (Embeddings)   │          │
                     │   └────────────────┘    └────────────────┘          │
                     └─────────────────────────────────────────────────────┘
```

## AWS Infrastructure

### Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         VPC (10.0.0.0/16)                            │   │
│  │                                                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Public Subnets                              │  │   │
│  │  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │  │   │
│  │  │  │     ALB     │   │API Gateway  │   │API Gateway  │          │  │   │
│  │  │  │  (REST API) │   │  (REST)     │   │ (WebSocket) │          │  │   │
│  │  │  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │  │   │
│  │  └─────────┼─────────────────┼─────────────────┼──────────────────┘  │   │
│  │            │                 │                 │                     │   │
│  │  ┌─────────┼─────────────────┼─────────────────┼──────────────────┐  │   │
│  │  │         │        Private Subnets           │                   │  │   │
│  │  │         ▼                 ▼                 ▼                   │  │   │
│  │  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │  │   │
│  │  │  │    ECS      │   │   Lambda    │   │   Lambda    │          │  │   │
│  │  │  │  Fargate    │   │   (REST)    │   │ (WebSocket) │          │  │   │
│  │  │  │  (REST)     │   │             │   │             │          │  │   │
│  │  │  └─────────────┘   └─────────────┘   └─────────────┘          │  │   │
│  │  │                                                                │  │   │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │   │
│  │  │  │                    Pipeline Infrastructure               │ │  │   │
│  │  │  │                                                          │ │  │   │
│  │  │  │   ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐          │ │  │   │
│  │  │  │   │ SQS  │───►│Lambda│───►│ SQS  │───►│Lambda│          │ │  │   │
│  │  │  │   │Queue │    │Crawl │    │Queue │    │Embed │          │ │  │   │
│  │  │  │   └──────┘    └──────┘    └──────┘    └──────┘          │ │  │   │
│  │  │  │       ▲                                    │             │ │  │   │
│  │  │  │       │                                    ▼             │ │  │   │
│  │  │  │   ┌──────┐                           ┌──────┐           │ │  │   │
│  │  │  │   │  S3  │                           │Vector│           │ │  │   │
│  │  │  │   │Bucket│                           │  DB  │           │ │  │   │
│  │  │  │   └──────┘                           └──────┘           │ │  │   │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │   │
│  │  │                                                                │  │   │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │   │
│  │  │  │                    Data Layer                            │ │  │   │
│  │  │  │   ┌──────────┐   ┌──────────┐   ┌──────────┐            │ │  │   │
│  │  │  │   │   RDS    │   │ ElastiC. │   │  Secrets │            │ │  │   │
│  │  │  │   │PostgreSQL│   │  Redis   │   │  Manager │            │ │  │   │
│  │  │  │   └──────────┘   └──────────┘   └──────────┘            │ │  │   │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Supporting Services                                │  │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐         │  │
│  │   │CloudWatch│   │  X-Ray   │   │   IAM    │   │   KMS    │         │  │
│  │   │  Logs    │   │ Tracing  │   │  Roles   │   │  Keys    │         │  │
│  │   └──────────┘   └──────────┘   └──────────┘   └──────────┘         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Configuration

```typescript
// infrastructure/config/services.ts

export const infrastructureConfig = {
  rest: {
    deployment: 'ECS_FARGATE', // or 'LAMBDA'
    scaling: {
      minInstances: 2,
      maxInstances: 10,
      targetCPUUtilization: 70,
    },
    resources: {
      cpu: 512,
      memory: 1024,
    },
  },
  
  websocket: {
    deployment: 'API_GATEWAY_WEBSOCKET',
    connectionTimeout: 600, // 10 minutes
    idleTimeout: 300, // 5 minutes
    maxConnections: 10000,
  },
  
  pipeline: {
    crawlQueue: {
      name: 'cai-crawl-queue',
      visibilityTimeout: 300,
      maxReceiveCount: 3,
    },
    embeddingQueue: {
      name: 'cai-embedding-queue',
      visibilityTimeout: 600,
      batchSize: 10,
    },
    lambdaConfig: {
      crawlFunction: {
        timeout: 300,
        memory: 1024,
      },
      embeddingFunction: {
        timeout: 600,
        memory: 2048,
      },
    },
  },
  
  database: {
    rds: {
      engine: 'postgres',
      version: '14.7',
      instanceClass: 'db.r6g.large',
      multiAZ: true,
    },
    redis: {
      nodeType: 'cache.r6g.large',
      numCacheNodes: 2,
    },
  },
};
```

### Terraform Module Structure

```hcl
# infrastructure/terraform/main.tf

module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  environment = var.environment
}

module "rest_api" {
  source = "./modules/rest-api"
  
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  deployment_type = var.rest_deployment_type # "ecs" or "lambda"
}

module "websocket_api" {
  source = "./modules/websocket-api"
  
  vpc_id = module.vpc.vpc_id
  lambda_function_arn = module.websocket_lambda.function_arn
}

module "pipeline" {
  source = "./modules/pipeline"
  
  vpc_id = module.vpc.vpc_id
  s3_bucket_arn = module.storage.bucket_arn
  embedding_model = var.embedding_model
}

module "database" {
  source = "./modules/database"
  
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

## Core vs Common Packages

### Common Package (`@cai-service/common`)

The Common package provides foundational utilities and infrastructure components used across all other packages.

#### Responsibilities

```typescript
// packages/common/src/index.ts

// Database Clients
export { DatabaseClient, createDatabaseConnection } from './database';
export { RedisClient, createRedisConnection } from './cache';
export { VectorStoreClient } from './vector-store';

// Shared Types
export * from './types/models';
export * from './types/api';
export * from './types/events';

// Utilities
export { Logger, createLogger } from './logging';
export { validateSchema, schemas } from './validation';
export { encrypt, decrypt, hashApiKey } from './security';

// Configuration
export { loadConfig, ConfigurationManager } from './config';

// Error Handling
export { 
  AppError, 
  ValidationError, 
  AuthenticationError,
  RateLimitError 
} from './errors';
```

#### Key Components

```typescript
// packages/common/src/database/client.ts

import { Pool, PoolClient } from 'pg';

export class DatabaseClient {
  private pool: Pool;
  
  constructor(config: DatabaseConfig) {
    this.pool = new Pool({
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      max: config.maxConnections || 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
  }
  
  async query<T>(sql: string, params?: unknown[]): Promise<T[]> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(sql, params);
      return result.rows as T[];
    } finally {
      client.release();
    }
  }
  
  async transaction<T>(
    callback: (client: PoolClient) => Promise<T>
  ): Promise<T> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }
}
```

### Core Package (`@cai-service/core`)

The Core package contains all business logic for AI operations, model management, and prompt execution.

#### Responsibilities

```typescript
// packages/core/src/index.ts

// AI Model Adapters
export { OpenAIAdapter } from './adapters/openai';
export { AnthropicAdapter } from './adapters/anthropic';
export { ModelAdapterFactory } from './adapters/factory';

// Prompt Execution
export { PromptExecutor } from './execution/prompt-executor';
export { StreamingExecutor } from './execution/streaming-executor';
export { ContextBuilder } from './execution/context-builder';

// Knowledge Retrieval
export { KnowledgeRetriever } from './knowledge/retriever';
export { SemanticSearch } from './knowledge/semantic-search';
export { RankingEngine } from './knowledge/ranking';

// Services
export { ConversationService } from './services/conversation';
export { ModelService } from './services/model';
export { UsageService } from './services/usage';
```

#### Prompt Execution Engine

```typescript
// packages/core/src/execution/prompt-executor.ts

import { 
  DatabaseClient, 
  VectorStoreClient, 
  Logger 
} from '@cai-service/common';

export class PromptExecutor {
  private modelAdapterFactory: ModelAdapterFactory;
  private contextBuilder: ContextBuilder;
  private knowledgeRetriever: KnowledgeRetriever;
  
  constructor(
    private db: DatabaseClient,
    private vectorStore: VectorStoreClient,
    private logger: Logger
  ) {
    this.modelAdapterFactory = new ModelAdapterFactory();
    this.contextBuilder = new ContextBuilder(vectorStore);
    this.knowledgeRetriever = new KnowledgeRetriever(vectorStore);
  }
  
  async execute(request: PromptRequest): Promise<PromptResponse> {
    // 1. Retrieve relevant context
    const context = await this.knowledgeRetriever.retrieve({
      query: request.prompt,
      knowledgeBaseId: request.knowledgeBaseId,
      maxResults: request.contextSize || 5,
    });
    
    // 2. Build the complete prompt with context
    const enrichedPrompt = await this.contextBuilder.build({
      userPrompt: request.prompt,
      systemPrompt: request.systemPrompt,
      context: context,
      conversationHistory: request.conversationId 
        ? await this.getConversationHistory(request.conversationId)
        : [],
    });
    
    // 3. Get the appropriate model adapter
    const adapter = this.modelAdapterFactory.create(request.model);
    
    // 4. Execute the prompt
    const response = await adapter.complete({
      messages: enrichedPrompt.messages,
      temperature: request.temperature || 0.7,
      maxTokens: request.maxTokens || 1000,
    });
    
    // 5. Store the interaction
    await this.storeInteraction(request, response);
    
    // 6. Return the response
    return {
      response: response.content,
      model: request.model,
      tokensUsed: response.usage,
      contextChunks: context.map(c => c.id),
    };
  }
  
  async *executeStream(
    request: PromptRequest
  ): AsyncGenerator<StreamChunk> {
    // Similar to execute, but yields chunks
    const context = await this.knowledgeRetriever.retrieve({
      query: request.prompt,
      knowledgeBaseId: request.knowledgeBaseId,
    });
    
    const enrichedPrompt = await this.contextBuilder.build({
      userPrompt: request.prompt,
      context: context,
    });
    
    const adapter = this.modelAdapterFactory.create(request.model);
    
    for await (const chunk of adapter.streamComplete({
      messages: enrichedPrompt.messages,
    })) {
      yield {
        type: 'content',
        content: chunk.content,
        index: chunk.index,
      };
    }
    
    yield {
      type: 'done',
      usage: await adapter.getLastUsage(),
    };
  }
}
```

### Package Interaction Summary

| From Package | To Package | Interaction Type | Purpose |
|--------------|------------|------------------|---------|
| REST | Core | Direct import | Execute prompts, manage conversations |
| REST | Common | Direct import | Database access, validation, logging |
| WebSocket | Core | Direct import | Streaming prompt execution |
| WebSocket | Common | Direct import | Connection state, authentication |
| Pipeline | Core | Direct import | Embedding generation |
| Pipeline | Common | Direct import | File parsing, storage access |
| Core | Common | Direct import | Data persistence, utilities |

## Best Practices

### 1. Package Boundaries

- **Never import "up"**: Common should never import from Core; Core should never import from REST/WebSocket/Pipeline
- **Keep interfaces stable**: Changes to Core's public API should be backward-compatible
- **Use dependency injection**: Pass dependencies rather than creating them internally

### 2. Error Handling

```typescript
// Consistent error handling across packages
try {
  const result = await core.executePrompt(request);
  return res.json(result);
} catch (error) {
  if (error instanceof ValidationError) {
    return res.status(400).json({ error: error.message });
  }
  if (error instanceof RateLimitError) {
    return res.status(429).json({ 
      error: 'Rate limit exceeded',
      retryAfter: error.retryAfter 
    });
  }
  logger.error('Unexpected error', { error });
  return res.status(500).json({ error: 'Internal server error' });
}
```

### 3. Configuration Management

```typescript
// Use environment-specific configuration
const config = loadConfig({
  environment: process.env.NODE_ENV,
  secretsManager: process.env.AWS_SECRETS_ARN,
});

// Access configuration consistently
const dbConfig = config.get('database');
const aiConfig = config.get('ai.openai');
```

## Troubleshooting

### Common Architecture Issues

| Issue | Possible Cause | Resolution |
|-------|---------------|------------|
| Circular dependency errors | Package A imports B, B imports A | Extract shared code to Common |
| WebSocket disconnections | Lambda cold starts | Use provisioned concurrency |
| Pipeline bottlenecks | Sequential processing | Increase SQS batch size |
| High latency | Vector search timeout | Add Redis caching layer |
| Memory issues | Large document processing | Stream file processing |

---

This architecture documentation provides the foundation for understanding how cai-service operates. For specific implementation details, refer to the individual package documentation and API references.