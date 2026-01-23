# Lambda Functions

## Overview

This document provides comprehensive documentation for the Lambda functions within the cai-service ecosystem. These serverless functions handle critical background processing tasks including knowledge embedding, indexing, and other asynchronous operations that power the Conversational AI service's knowledge management capabilities.

The cai-service utilizes AWS Lambda functions to process documents, generate vector embeddings, and maintain the knowledge index that enables semantic search and context-aware AI responses. Understanding these functions is essential for developers working on the knowledge ingestion pipeline, troubleshooting indexing issues, or extending the system's capabilities.

---

## Knowledge Embedder

### Purpose and Functionality

The Knowledge Embedder Lambda function is responsible for transforming processed documents into vector embeddings that can be stored and queried efficiently. This function serves as the bridge between raw textual content and the vector database that powers semantic search capabilities.

### Function Architecture

```typescript
// packages/lambda/knowledge-embedder/handler.ts

import { Handler, SQSEvent, SQSRecord } from 'aws-lambda';
import { EmbeddingService } from '@cai-service/embedding';
import { VectorStore } from '@cai-service/vector-store';
import { DocumentChunk, EmbeddingResult } from '@cai-service/types';

interface EmbedderConfig {
  modelName: string;
  batchSize: number;
  maxRetries: number;
  vectorDimensions: number;
}

const config: EmbedderConfig = {
  modelName: process.env.EMBEDDING_MODEL || 'text-embedding-ada-002',
  batchSize: parseInt(process.env.EMBEDDING_BATCH_SIZE || '100'),
  maxRetries: parseInt(process.env.MAX_RETRIES || '3'),
  vectorDimensions: parseInt(process.env.VECTOR_DIMENSIONS || '1536'),
};

export const handler: Handler<SQSEvent> = async (event) => {
  const embeddingService = new EmbeddingService(config.modelName);
  const vectorStore = new VectorStore();
  
  const results: EmbeddingResult[] = [];
  
  for (const record of event.Records) {
    try {
      const chunk: DocumentChunk = JSON.parse(record.body);
      const embedding = await embeddingService.generateEmbedding(chunk.content);
      
      await vectorStore.upsert({
        id: chunk.id,
        vector: embedding,
        metadata: {
          documentId: chunk.documentId,
          sourceUrl: chunk.sourceUrl,
          chunkIndex: chunk.chunkIndex,
          contentHash: chunk.contentHash,
          createdAt: new Date().toISOString(),
        },
      });
      
      results.push({ id: chunk.id, status: 'success' });
    } catch (error) {
      console.error(`Failed to embed chunk: ${record.messageId}`, error);
      results.push({ 
        id: record.messageId, 
        status: 'failed', 
        error: error.message 
      });
    }
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify({ processed: results.length, results }),
  };
};
```

### Input Schema

The Knowledge Embedder expects messages in the following format:

```json
{
  "id": "chunk_abc123",
  "documentId": "doc_xyz789",
  "content": "The processed text content to be embedded...",
  "sourceUrl": "https://example.com/document.pdf",
  "chunkIndex": 0,
  "contentHash": "sha256:abc123...",
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "contentType": "application/pdf"
  }
}
```

### Embedding Process Flow

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   SQS Queue     │────▶│   Lambda     │────▶│  OpenAI API     │
│  (Document      │     │  Knowledge   │     │  Embedding      │
│   Chunks)       │     │  Embedder    │     │  Endpoint       │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Vector     │
                        │   Database   │
                        │  (Pinecone)  │
                        └──────────────┘
```

### Error Handling and Retry Logic

```typescript
// packages/lambda/knowledge-embedder/retry-handler.ts

import { backOff } from 'exponential-backoff';

interface RetryConfig {
  numOfAttempts: number;
  startingDelay: number;
  maxDelay: number;
  timeMultiple: number;
}

const retryConfig: RetryConfig = {
  numOfAttempts: 3,
  startingDelay: 1000,
  maxDelay: 10000,
  timeMultiple: 2,
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  context: string
): Promise<T> {
  return backOff(operation, {
    ...retryConfig,
    retry: (error, attemptNumber) => {
      console.warn(`Retry attempt ${attemptNumber} for ${context}:`, error.message);
      
      // Don't retry on validation errors
      if (error.statusCode === 400) {
        return false;
      }
      
      // Retry on rate limits and server errors
      return error.statusCode === 429 || error.statusCode >= 500;
    },
  });
}
```

### Performance Optimization

The Knowledge Embedder implements several optimization strategies:

1. **Batch Processing**: Chunks are processed in configurable batch sizes to optimize API calls
2. **Connection Pooling**: Database connections are reused across invocations
3. **Memory Management**: Large documents are streamed rather than loaded entirely into memory

```typescript
// packages/lambda/knowledge-embedder/batch-processor.ts

export async function processBatch(
  chunks: DocumentChunk[],
  batchSize: number
): Promise<EmbeddingResult[]> {
  const results: EmbeddingResult[] = [];
  
  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize);
    const batchEmbeddings = await Promise.all(
      batch.map(chunk => generateEmbeddingWithRetry(chunk))
    );
    results.push(...batchEmbeddings);
    
    // Rate limiting between batches
    if (i + batchSize < chunks.length) {
      await sleep(100);
    }
  }
  
  return results;
}
```

---

## Knowledge Indexer

### Purpose and Functionality

The Knowledge Indexer Lambda function manages the metadata index that complements the vector store. While the Knowledge Embedder handles vector representations, the Indexer maintains searchable metadata, document relationships, and content summaries that enable hybrid search capabilities.

### Function Architecture

```typescript
// packages/lambda/knowledge-indexer/handler.ts

import { Handler, S3Event } from 'aws-lambda';
import { ElasticsearchClient } from '@cai-service/elasticsearch';
import { DocumentParser } from '@cai-service/document-parser';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';

interface IndexerConfig {
  elasticsearchEndpoint: string;
  indexName: string;
  documentBucketName: string;
}

const config: IndexerConfig = {
  elasticsearchEndpoint: process.env.ELASTICSEARCH_ENDPOINT!,
  indexName: process.env.INDEX_NAME || 'knowledge-documents',
  documentBucketName: process.env.DOCUMENT_BUCKET_NAME!,
};

const s3Client = new S3Client({});
const esClient = new ElasticsearchClient(config.elasticsearchEndpoint);

export const handler: Handler<S3Event> = async (event) => {
  const indexResults = [];
  
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key);
    
    try {
      // Retrieve document from S3
      const response = await s3Client.send(
        new GetObjectCommand({ Bucket: bucket, Key: key })
      );
      
      const content = await streamToString(response.Body);
      const document = JSON.parse(content);
      
      // Parse and extract metadata
      const parser = new DocumentParser();
      const metadata = await parser.extractMetadata(document);
      
      // Index in Elasticsearch
      await esClient.index({
        index: config.indexName,
        id: document.id,
        body: {
          documentId: document.id,
          title: metadata.title,
          summary: metadata.summary,
          keywords: metadata.keywords,
          sourceUrl: document.sourceUrl,
          contentType: document.contentType,
          chunkCount: document.chunks?.length || 0,
          wordCount: metadata.wordCount,
          language: metadata.detectedLanguage,
          createdAt: document.createdAt,
          indexedAt: new Date().toISOString(),
          lastModified: document.lastModified,
        },
      });
      
      indexResults.push({ id: document.id, status: 'indexed' });
    } catch (error) {
      console.error(`Failed to index document: ${key}`, error);
      indexResults.push({ key, status: 'failed', error: error.message });
    }
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify({ indexed: indexResults.length, results: indexResults }),
  };
};
```

### Index Schema Definition

```typescript
// packages/lambda/knowledge-indexer/schema.ts

export const knowledgeIndexMapping = {
  mappings: {
    properties: {
      documentId: { type: 'keyword' },
      title: { 
        type: 'text',
        analyzer: 'standard',
        fields: {
          keyword: { type: 'keyword' }
        }
      },
      summary: { type: 'text', analyzer: 'standard' },
      keywords: { type: 'keyword' },
      sourceUrl: { type: 'keyword' },
      contentType: { type: 'keyword' },
      chunkCount: { type: 'integer' },
      wordCount: { type: 'integer' },
      language: { type: 'keyword' },
      createdAt: { type: 'date' },
      indexedAt: { type: 'date' },
      lastModified: { type: 'date' },
      metadata: {
        type: 'object',
        dynamic: true
      }
    }
  },
  settings: {
    number_of_shards: 2,
    number_of_replicas: 1,
    analysis: {
      analyzer: {
        custom_analyzer: {
          type: 'custom',
          tokenizer: 'standard',
          filter: ['lowercase', 'stop', 'snowball']
        }
      }
    }
  }
};
```

### Document Processing Pipeline

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   S3 Bucket     │────▶│   Lambda     │────▶│  Elasticsearch  │
│  (Processed     │     │  Knowledge   │     │  Index          │
│   Documents)    │     │  Indexer     │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         └─────────────▶│   DynamoDB   │
                        │  (Document   │
                        │   Metadata)  │
                        └──────────────┘
```

---

## Event Triggers

### SQS Event Configuration

The Knowledge Embedder is triggered by SQS messages. Here's the complete trigger configuration:

```yaml
# infrastructure/serverless/knowledge-embedder.yml

functions:
  knowledgeEmbedder:
    handler: packages/lambda/knowledge-embedder/handler.handler
    runtime: nodejs18.x
    timeout: 300
    memorySize: 1024
    reservedConcurrency: 10
    events:
      - sqs:
          arn: !GetAtt KnowledgeChunksQueue.Arn
          batchSize: 10
          maximumBatchingWindow: 30
          functionResponseType: ReportBatchItemFailures

resources:
  Resources:
    KnowledgeChunksQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: ${self:service}-knowledge-chunks-${self:provider.stage}
        VisibilityTimeout: 360
        MessageRetentionPeriod: 1209600
        RedrivePolicy:
          deadLetterTargetArn: !GetAtt KnowledgeChunksDLQ.Arn
          maxReceiveCount: 3
    
    KnowledgeChunksDLQ:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: ${self:service}-knowledge-chunks-dlq-${self:provider.stage}
        MessageRetentionPeriod: 1209600
```

### S3 Event Configuration

The Knowledge Indexer responds to S3 object creation events:

```yaml
# infrastructure/serverless/knowledge-indexer.yml

functions:
  knowledgeIndexer:
    handler: packages/lambda/knowledge-indexer/handler.handler
    runtime: nodejs18.x
    timeout: 120
    memorySize: 512
    events:
      - s3:
          bucket: ${self:custom.documentBucket}
          event: s3:ObjectCreated:*
          rules:
            - prefix: processed/
            - suffix: .json
          existing: true

custom:
  documentBucket: ${self:service}-documents-${self:provider.stage}
```

### EventBridge Scheduled Events

For periodic maintenance and reindexing operations:

```yaml
# infrastructure/serverless/scheduled-tasks.yml

functions:
  indexHealthCheck:
    handler: packages/lambda/index-health-check/handler.handler
    events:
      - schedule:
          rate: rate(1 hour)
          enabled: true
          input:
            action: health_check
  
  reindexStale:
    handler: packages/lambda/reindex-stale/handler.handler
    events:
      - schedule:
          rate: cron(0 2 * * ? *)  # Daily at 2 AM UTC
          enabled: true
          input:
            staleThresholdDays: 30
```

### Event Schema Definitions

```typescript
// packages/lambda/shared/event-schemas.ts

export interface DocumentChunkEvent {
  id: string;
  documentId: string;
  content: string;
  sourceUrl: string;
  chunkIndex: number;
  totalChunks: number;
  contentHash: string;
  metadata: Record<string, unknown>;
  processingTimestamp: string;
}

export interface DocumentProcessedEvent {
  documentId: string;
  sourceUrl: string;
  contentType: string;
  chunkCount: number;
  processingDuration: number;
  s3Key: string;
  status: 'success' | 'partial' | 'failed';
  errors?: string[];
}

export interface IndexMaintenanceEvent {
  action: 'health_check' | 'reindex' | 'optimize' | 'cleanup';
  targetIndex?: string;
  parameters?: Record<string, unknown>;
}
```

---

## Configuration

### Environment Variables

All Lambda functions share a common set of environment variables, with function-specific additions:

#### Common Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NODE_ENV` | Runtime environment | `production` | Yes |
| `LOG_LEVEL` | Logging verbosity | `info` | No |
| `AWS_REGION` | AWS region for services | `us-east-1` | Yes |
| `SECRETS_ARN` | AWS Secrets Manager ARN | - | Yes |

#### Knowledge Embedder Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-ada-002` | No |
| `EMBEDDING_BATCH_SIZE` | Chunks per batch | `100` | No |
| `MAX_RETRIES` | Maximum retry attempts | `3` | No |
| `VECTOR_DIMENSIONS` | Embedding dimensions | `1536` | No |
| `PINECONE_API_KEY` | Pinecone API key | - | Yes |
| `PINECONE_ENVIRONMENT` | Pinecone environment | - | Yes |
| `PINECONE_INDEX_NAME` | Target index name | - | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |

#### Knowledge Indexer Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ELASTICSEARCH_ENDPOINT` | Elasticsearch cluster URL | - | Yes |
| `INDEX_NAME` | Target index name | `knowledge-documents` | No |
| `DOCUMENT_BUCKET_NAME` | S3 bucket for documents | - | Yes |
| `DYNAMODB_TABLE_NAME` | Metadata table name | - | Yes |

### Configuration File

```typescript
// packages/lambda/shared/config.ts

import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

interface LambdaConfig {
  embedding: {
    model: string;
    batchSize: number;
    maxRetries: number;
    dimensions: number;
  };
  vectorStore: {
    apiKey: string;
    environment: string;
    indexName: string;
  };
  elasticsearch: {
    endpoint: string;
    indexName: string;
  };
  storage: {
    documentBucket: string;
    dynamoTable: string;
  };
}

let cachedConfig: LambdaConfig | null = null;

export async function getConfig(): Promise<LambdaConfig> {
  if (cachedConfig) {
    return cachedConfig;
  }
  
  const secretsClient = new SecretsManagerClient({});
  const secretResponse = await secretsClient.send(
    new GetSecretValueCommand({ SecretId: process.env.SECRETS_ARN })
  );
  
  const secrets = JSON.parse(secretResponse.SecretString || '{}');
  
  cachedConfig = {
    embedding: {
      model: process.env.EMBEDDING_MODEL || 'text-embedding-ada-002',
      batchSize: parseInt(process.env.EMBEDDING_BATCH_SIZE || '100'),
      maxRetries: parseInt(process.env.MAX_RETRIES || '3'),
      dimensions: parseInt(process.env.VECTOR_DIMENSIONS || '1536'),
    },
    vectorStore: {
      apiKey: secrets.PINECONE_API_KEY,
      environment: secrets.PINECONE_ENVIRONMENT,
      indexName: process.env.PINECONE_INDEX_NAME!,
    },
    elasticsearch: {
      endpoint: process.env.ELASTICSEARCH_ENDPOINT!,
      indexName: process.env.INDEX_NAME || 'knowledge-documents',
    },
    storage: {
      documentBucket: process.env.DOCUMENT_BUCKET_NAME!,
      dynamoTable: process.env.DYNAMODB_TABLE_NAME!,
    },
  };
  
  return cachedConfig;
}
```

### IAM Permissions

```yaml
# infrastructure/serverless/iam-roles.yml

provider:
  iam:
    role:
      statements:
        # SQS Permissions
        - Effect: Allow
          Action:
            - sqs:ReceiveMessage
            - sqs:DeleteMessage
            - sqs:GetQueueAttributes
          Resource:
            - !GetAtt KnowledgeChunksQueue.Arn
        
        # S3 Permissions
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:PutObject
            - s3:DeleteObject
          Resource:
            - !Sub 'arn:aws:s3:::${DocumentBucket}/*'
        
        # DynamoDB Permissions
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:PutItem
            - dynamodb:UpdateItem
            - dynamodb:Query
          Resource:
            - !GetAtt DocumentMetadataTable.Arn
            - !Sub '${DocumentMetadataTable.Arn}/index/*'
        
        # Secrets Manager Permissions
        - Effect: Allow
          Action:
            - secretsmanager:GetSecretValue
          Resource:
            - !Ref LambdaSecrets
        
        # CloudWatch Logs
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
          Resource: '*'
```

---

## Deployment

### Prerequisites

Before deploying the Lambda functions, ensure you have:

1. **AWS CLI** configured with appropriate credentials
2. **Node.js 18.x** or later installed
3. **Serverless Framework** installed globally
4. Required AWS resources provisioned (VPC, subnets, security groups)

### Build Process

```bash
# Install dependencies
npm install

# Build all Lambda packages
npm run build:lambda

# Run tests
npm run test:lambda

# Package for deployment
npm run package:lambda
```

### Deployment Commands

```bash
# Deploy all Lambda functions to development
npm run deploy:lambda:dev

# Deploy specific function
npx serverless deploy function -f knowledgeEmbedder --stage dev

# Deploy to production
npm run deploy:lambda:prod

# Deploy with verbose output
npx serverless deploy --stage prod --verbose
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy-lambda.sh

set -e

STAGE=${1:-dev}
REGION=${2:-us-east-1}

echo "Deploying Lambda functions to ${STAGE} in ${REGION}..."

# Build TypeScript
echo "Building Lambda packages..."
npm run build:lambda

# Run tests
echo "Running tests..."
npm run test:lambda

# Package functions
echo "Packaging functions..."
npm run package:lambda

# Deploy with Serverless
echo "Deploying with Serverless Framework..."
npx serverless deploy --stage ${STAGE} --region ${REGION}

# Verify deployment
echo "Verifying deployment..."
aws lambda list-functions --region ${REGION} | grep "cai-service-${STAGE}"

echo "Deployment complete!"
```

### Serverless Configuration

```yaml
# serverless.yml

service: cai-service-lambda

frameworkVersion: '3'

provider:
  name: aws
  runtime: nodejs18.x
  stage: ${opt:stage, 'dev'}
  region: ${opt:region, 'us-east-1'}
  memorySize: 512
  timeout: 30
  
  environment:
    NODE_ENV: ${self:provider.stage}
    LOG_LEVEL: ${self:custom.logLevel.${self:provider.stage}, 'info'}
    SECRETS_ARN: !Ref LambdaSecrets
  
  vpc:
    securityGroupIds:
      - !Ref LambdaSecurityGroup
    subnetIds:
      - !Ref PrivateSubnet1
      - !Ref PrivateSubnet2

plugins:
  - serverless-plugin-typescript
  - serverless-offline
  - serverless-prune-plugin

custom:
  logLevel:
    dev: debug
    staging: info
    prod: warn
  
  prune:
    automatic: true
    number: 3

package:
  individually: true
  patterns:
    - '!node_modules/**'
    - '!test/**'
    - '!.git/**'

functions:
  knowledgeEmbedder:
    handler: packages/lambda/knowledge-embedder/handler.handler
    timeout: 300
    memorySize: 1024
    environment:
      EMBEDDING_MODEL: ${env:EMBEDDING_MODEL, 'text-embedding-ada-002'}
      PINECONE_INDEX_NAME: ${env:PINECONE_INDEX_NAME}
    events:
      - sqs:
          arn: !GetAtt KnowledgeChunksQueue.Arn
          batchSize: 10
  
  knowledgeIndexer:
    handler: packages/lambda/knowledge-indexer/handler.handler
    timeout: 120
    memorySize: 512
    environment:
      ELASTICSEARCH_ENDPOINT: ${env:ELASTICSEARCH_ENDPOINT}
      INDEX_NAME: knowledge-documents-${self:provider.stage}
    events:
      - s3:
          bucket: ${self:custom.documentBucket}
          event: s3:ObjectCreated:*
          rules:
            - prefix: processed/
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy-lambda.yml

name: Deploy Lambda Functions

on:
  push:
    branches: [main, develop]
    paths:
      - 'packages/lambda/**'
      - 'serverless.yml'
  workflow_dispatch:
    inputs:
      stage:
        description: 'Deployment stage'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm run test:lambda
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to AWS
        run: |
          STAGE=${{ github.event.inputs.stage || 'dev' }}
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            STAGE="prod"
          fi
          npx serverless deploy --stage $STAGE
```

### Monitoring and Observability

After deployment, configure CloudWatch alarms for critical metrics:

```typescript
// infrastructure/monitoring/alarms.ts

import { CloudWatchClient, PutMetricAlarmCommand } from '@aws-sdk/client-cloudwatch';

const alarms = [
  {
    AlarmName: 'KnowledgeEmbedder-Errors',
    MetricName: 'Errors',
    Namespace: 'AWS/Lambda',
    Dimensions: [{ Name: 'FunctionName', Value: 'cai-service-knowledgeEmbedder' }],
    Threshold: 5,
    EvaluationPeriods: 1,
    ComparisonOperator: 'GreaterThanThreshold',
  },
  {
    AlarmName: 'KnowledgeIndexer-Duration',
    MetricName: 'Duration',
    Namespace: 'AWS/Lambda',
    Dimensions: [{ Name: 'FunctionName', Value: 'cai-service-knowledgeIndexer' }],
    Threshold: 100000, // 100 seconds
    EvaluationPeriods: 3,
    ComparisonOperator: 'GreaterThanThreshold',
  },
];
```

---

## Troubleshooting

### Common Issues

#### 1. Embedding Rate Limits

**Symptom**: `429 Too Many Requests` errors from OpenAI API

**Solution**:
```typescript
// Implement exponential backoff and reduce batch size
const config = {
  batchSize: 50, // Reduced from 100
  rateLimitDelay: 1000, // 1 second between batches
};
```

#### 2. Memory Exceeded

**Symptom**: Lambda function times out or runs out of memory

**Solution**:
- Increase `memorySize` in serverless configuration
- Implement streaming for large documents
- Process documents in smaller chunks

#### 3. Elasticsearch Connection Timeouts

**Symptom**: Connection refused or timeout errors

**Solution**:
- Verify VPC configuration and security groups
- Check Elasticsearch domain status
- Ensure Lambda has proper IAM permissions

### Debug Logging

Enable detailed logging for troubleshooting:

```typescript
// packages/lambda/shared/logger.ts

import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: 'cai-service-lambda',
    environment: process.env.NODE_ENV,
  },
});

// Usage in handlers
logger.debug({ event }, 'Received event');
logger.info({ documentId, chunks: chunks.length }, 'Processing document');
logger.error({ error, context }, 'Failed to process');
```

---

## Best Practices

1. **Cold Start Optimization**: Keep Lambda packages small and use provisioned concurrency for latency-sensitive functions
2. **Error Handling**: Always implement dead-letter queues for failed messages
3. **Idempotency**: Design functions to be idempotent to handle retry scenarios
4. **Monitoring**: Set up CloudWatch alarms for errors, duration, and throttles
5. **Security**: Use IAM roles with least-privilege permissions and encrypt sensitive data

---

## Related Documentation

- [API Endpoints](./api-endpoints.md)
- [Data Models](./data-models.md)
- [Configuration Variables](./configuration.md)
- [Vector Store Integration](./vector-store.md)