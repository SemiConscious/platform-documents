# Lumina Observability Platform

## Overview

Lumina is a comprehensive observability service that provides deep insight into voice communication systems. It measures latency, monitors call quality, analyzes routing behavior, and captures contextual data to explain system actions and support efficient troubleshooting.

The platform processes real-time events from the voice platform (GP - Global Platform and RT - RealTime components), transforms them into structured dialogue and metric records, and delivers them to both storage systems and real-time subscriber clients.

## Key Capabilities

- **Latency Measurement**: Track end-to-end call latency and component-level timing
- **Call Quality Monitoring**: Monitor call quality metrics in real-time
- **Routing Behavior Analysis**: Capture and explain voice routing decisions
- **Contextual Data Collection**: Gather comprehensive data for troubleshooting
- **Real-time Event Streaming**: Push live updates to subscribed clients
- **Historical Data Analysis**: Store and query historical metrics via OpenSearch

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                             EVENT SOURCES                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                               │
│  │      GP      │  │      RT      │  │    NEXUS     │                               │
│  │(Global Plat) │  │  (RealTime)  │  │   (Metrics)  │                               │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘                               │
└─────────┼─────────────────┼─────────────────┼───────────────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 │
┌─────────────────────────────────────────────┼───────────────────────────────────────┐
│                    INGESTION LAYER          │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                     Region Distributor Lambda                                │    │
│  │  • Receives events from GP and RT                                           │    │
│  │  • Routes events to home region Kinesis streams                             │    │
│  │  • Forwards metrics events to NEXUS                                         │    │
│  └───────────────────────────────┬─────────────────────────────────────────────┘    │
│                                  │                                                   │
│  ┌───────────────────────────────┼────────────────────────────────────────────┐     │
│  │         Region Distributor Retrier Lambda                                   │     │
│  │  • Handles failed events from Region Distributor                           │     │
│  │  • Retries for specified duration                                          │     │
│  │  • Sends persistent failures to DLQ                                        │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         STREAMING LAYER (Per Region)                                 │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                        Kinesis Data Stream                                   │    │
│  │  • Enhanced Fan-Out consumer support                                        │    │
│  │  • Batch processing (10 records/batch)                                      │    │
│  │  • Parallel processing (3x parallelization factor)                          │    │
│  └───────────────────────────────┬─────────────────────────────────────────────┘    │
│                                  │                                                   │
│                     ┌────────────┴────────────┐                                     │
│                     ▼                         ▼                                      │
│  ┌─────────────────────────────┐  ┌───────────────────────────────────────────┐    │
│  │  Dialogue Events Creator    │  │           Firehose Processor              │    │
│  │  Lambda                     │  │           Lambda                          │    │
│  │  • Creates Dialogue records │  │  • Transforms metrics events              │    │
│  │  • Writes to DynamoDB       │  │  • Partitions by date                     │    │
│  │  • Triggers DynamoDB Stream │  │  • Routes to S3 via Firehose              │    │
│  └──────────────┬──────────────┘  └───────────────────────────────────────────┘    │
│                 │                                                                    │
└─────────────────┼────────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                           │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                         DynamoDB Cache Table                                 │    │
│  │  • Stores Dialogue and Event records                                        │    │
│  │  • DynamoDB Streams enabled                                                 │    │
│  │  • KMS encryption at rest                                                   │    │
│  └───────────────────────────────┬─────────────────────────────────────────────┘    │
│                                  │                                                   │
│                                  │ (DynamoDB Stream)                                │
│                                  ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │               Subscription Updates Publisher Lambda                          │    │
│  │  • Consumes DynamoDB Stream events                                          │    │
│  │  • Publishes updates via AppSync mutations                                  │    │
│  │  • Handles retry logic for failed publishes                                 │    │
│  └───────────────────────────────┬─────────────────────────────────────────────┘    │
│                                  │                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │               OpenSearch Dialogue Updater Lambda                             │    │
│  │  • Updates OpenSearch indices with dialogue data                            │    │
│  │  • Enables historical search and analytics                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                               │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                          AWS AppSync                                         │    │
│  │  • GraphQL API for queries and mutations                                    │    │
│  │  • Real-time subscriptions via WebSocket                                    │    │
│  │  • Custom Lambda authorizer                                                 │    │
│  │  • Route53 custom domain with regional endpoints                            │    │
│  └───────────────────────────────┬─────────────────────────────────────────────┘    │
│                                  │                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                    AppSync Router Lambda                                     │    │
│  │  • Routes requests to correct regional AppSync instance                     │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                                │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                    Natterbox Lumina Frontend                                 │    │
│  │  • React 19 + TypeScript application                                        │    │
│  │  • Real-time subscription to dialogue events                                │    │
│  │  • Dashboard and monitoring views                                           │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| [redmatter/lumina](https://github.com/redmatter/lumina) | Core observability service with Lambda functions | TypeScript |
| [redmatter/aws-terraform-lumina-pipeline](https://github.com/redmatter/aws-terraform-lumina-pipeline) | Infrastructure as Code for AWS resources | HCL (Terraform) |
| [redmatter/natterbox-lumina](https://github.com/redmatter/natterbox-lumina) | Frontend React application | TypeScript |

## Lambda Functions

The Lumina pipeline consists of six primary Lambda functions:

### 1. Region Distributor (`regionDistributor`)

**Purpose**: Entry point for events from GP and RT systems.

**Responsibilities**:
- Receives events from GP (Global Platform) and RT (RealTime) components
- Routes events to their home region Kinesis streams based on tenant configuration
- Forwards metrics events to NEXUS for analytics processing
- Validates event schema using Zod validation

**Source**: `src/lambdas/regionDistributor.ts`

### 2. Region Distributor Retrier (`regionDistributorRetrier`)

**Purpose**: Handles failure recovery for the Region Distributor.

**Responsibilities**:
- Processes failed events from the Region Distributor Lambda
- Retries events for a configurable duration
- Routes persistent failures to Dead Letter Queue (DLQ)
- Tracks retry attempts and timing

**Source**: `src/lambdas/regionDistributorRetrier.ts`

### 3. AppSync Router (`appsyncRouter`)

**Purpose**: Routes API requests to regional AppSync instances.

**Responsibilities**:
- Receives incoming API requests
- Determines the correct regional AppSync endpoint
- Routes requests to appropriate AppSync instance
- Handles cross-region communication

**Source**: `src/lambdas/appsyncRouter.ts`

### 4. Dialogue Events Creator (`dialogueEventsCreator`)

**Purpose**: Creates dialogue records from incoming Kinesis events.

**Responsibilities**:
- Consumes events from Kinesis Data Stream (Enhanced Fan-Out consumer)
- Creates Dialogue and Event records in DynamoDB
- Handles batch processing (10 records per batch, 3x parallelization)
- Publishes end-of-dialogue events to SQS
- Triggers DynamoDB Stream for downstream processing

**Configuration**:
- Batch size: 10 records
- Starting position: LATEST
- Parallelization factor: 3
- Automatic batch bisection on error
- Reports batch item failures

**Source**: `src/lambdas/dialogueEventsCreator.ts`

### 5. Subscription Updates Publisher (`subscriptionUpdatesPublisher`)

**Purpose**: Publishes real-time updates to subscribed clients.

**Responsibilities**:
- Consumes events from DynamoDB Stream
- Transforms records to GraphQL mutation format
- Publishes updates through AppSync mutations
- Handles retry logic for failed publish attempts

**Source**: `src/lambdas/subscriptionUpdatesPublisher.ts`

### 6. Firehose Processor (`firehoseProcessor`)

**Purpose**: Transforms and routes metrics data for analytics storage.

**Responsibilities**:
- Processes records from Kinesis Firehose
- Transforms events using MetricFactory
- Normalizes metrics with date-based partitioning (year/month/day)
- Routes transformed data to S3 via Firehose
- Handles processing failures with appropriate error codes

**Source**: `src/lambdas/firehoseProcessor.ts`

### 7. OpenSearch Dialogue Updater (`openSearchDialogueUpdater`)

**Purpose**: Updates OpenSearch indices for historical analysis.

**Responsibilities**:
- Receives dialogue updates from SQS
- Updates OpenSearch indices with dialogue data
- Enables historical search and analytics queries

**Source**: `src/lambdas/openSearchDialogueUpdater.ts`

## Data Models

### Dialogue Model

The central data entity representing a voice communication session:

```typescript
interface Dialogue {
  // Primary identifiers
  PK: string;                    // Partition key (org/account)
  SK: string;                    // Sort key (dialogue ID)
  dialogueId: string;            // Unique dialogue identifier
  
  // Call identifiers
  callGuid: string;              // Global call GUID
  legGuid: string;               // Leg GUID for multi-party calls
  
  // Participants
  callerNumber: string;          // Caller phone number
  calledNumber: string;          // Called phone number
  
  // Timing
  startTime: string;             // ISO 8601 start timestamp
  endTime?: string;              // ISO 8601 end timestamp
  duration?: number;             // Call duration in seconds
  
  // Status
  status: DialogueStatus;        // Current dialogue state
  direction: CallDirection;      // INBOUND | OUTBOUND
  
  // Events
  events: Event[];               // Array of events in dialogue
  
  // Metadata
  organizationId: string;        // Organization identifier
  accountId: string;             // Account identifier
  createdAt: string;             // Record creation timestamp
  updatedAt: string;             // Last update timestamp
}
```

### Event Model

Events within a dialogue capturing specific actions:

```typescript
interface Event {
  eventId: string;               // Unique event identifier
  eventType: EventType;          // Type of event
  timestamp: string;             // When event occurred
  
  // Event-specific data
  data: Record<string, any>;     // Event payload
  
  // Source information
  source: EventSource;           // Which system generated event
}
```

### Event Types

Supported event types in the pipeline:

| Event Type | Description |
|------------|-------------|
| `CALL_STARTED` | Call initiation event |
| `CALL_ANSWERED` | Call answer event |
| `CALL_ENDED` | Call termination event |
| `CALL_TRANSFERRED` | Call transfer event |
| `CALL_HELD` | Call placed on hold |
| `CALL_RESUMED` | Call resumed from hold |
| `RECORDING_STARTED` | Recording initiation |
| `RECORDING_STOPPED` | Recording termination |
| `DTMF_RECEIVED` | DTMF digit received |
| `ROUTING_DECISION` | Routing decision made |

## GraphQL API

### Schema Overview

The GraphQL API exposes dialogues and events to clients:

```graphql
type Query {
  # Get a single dialogue by ID
  dialogue(dialogueId: ID!, organizationId: String!): Dialogue
  
  # List dialogues with filtering
  dialogues(
    organizationId: String!
    filter: DialogueFilter
    limit: Int
    nextToken: String
  ): DialogueConnection
  
  # Get events for a dialogue
  events(
    dialogueId: ID!
    organizationId: String!
    eventType: EventType
  ): [Event]
}

type Mutation {
  # Handle incoming event (used by pipeline)
  handleEvent(input: EventInput!): Event
}

type Subscription {
  # Subscribe to events for an organization
  onEvent(organizationId: String!): Event
  
  # Subscribe to dialogue updates
  onDialogueUpdate(organizationId: String!): Dialogue
}
```

### Key Types

```graphql
type Dialogue {
  dialogueId: ID!
  callGuid: String!
  legGuid: String
  callerNumber: String!
  calledNumber: String!
  startTime: AWSDateTime!
  endTime: AWSDateTime
  duration: Int
  status: DialogueStatus!
  direction: CallDirection!
  events: [Event]
  organizationId: String!
  accountId: String!
  createdAt: AWSDateTime!
  updatedAt: AWSDateTime!
}

type Event {
  eventId: ID!
  dialogueId: ID!
  eventType: EventType!
  timestamp: AWSDateTime!
  data: AWSJSON
  source: EventSource!
}

enum DialogueStatus {
  ACTIVE
  COMPLETED
  FAILED
  TRANSFERRED
}

enum CallDirection {
  INBOUND
  OUTBOUND
}
```

## Infrastructure Components

### AWS Kinesis Data Streams

**Configuration**:
- Provisioned capacity mode
- Enhanced Fan-Out consumers for low-latency processing
- Regional deployment (eu-west-1, us-east-1, etc.)

**Terraform Module**: `kinesis/kinesis.tf`

```hcl
resource "aws_kinesis_stream" "lumina_stream" {
  name             = "${var.project}-${var.environment}-stream"
  retention_period = 24  # Hours
  
  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
  
  shard_count = var.kinesis_shard_count
}
```

### AWS DynamoDB

**Cache Table Configuration**:
- Partition Key: `PK` (organization/account composite)
- Sort Key: `SK` (dialogue/event identifier)
- DynamoDB Streams enabled (NEW_AND_OLD_IMAGES)
- KMS encryption at rest
- On-demand capacity mode

**Terraform**: Managed via aws-terraform-lumina-pipeline

### AWS AppSync

**Configuration**:
- GraphQL API with LAMBDA authorization
- Real-time subscriptions via WebSocket
- Custom domain with Route53
- Regional deployment

**Terraform Module**: `appsync/appsync.tf`

Key features:
- Custom Lambda authorizer for authentication
- DynamoDB data source for queries
- None data source for mutations (passthrough to subscriptions)
- JavaScript resolvers for request/response mapping

### AWS SQS

**Queues**:
1. **End of Dialogue Queue**: Triggers OpenSearch updates
2. **Dead Letter Queue**: Captures failed events after retry exhaustion

**Terraform Module**: `sqs/sqs.tf`

### Route53 Custom Domains

Regional AppSync endpoints are exposed via custom domains:
- Pattern: `lumina-api-{region}.{domain}`
- SSL/TLS certificates via ACM
- Latency-based routing for optimal performance

## Frontend Application (natterbox-lumina)

### Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19 | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | Latest | Build tool |
| TanStack Query | Latest | Server state management |
| Apollo Client | Latest | GraphQL client |

### Project Structure

```
natterbox-lumina/
├── src/
│   ├── features/           # Feature-based modules
│   │   ├── dialogues/      # Dialogue list and detail views
│   │   ├── events/         # Event visualization
│   │   └── dashboard/      # Dashboard components
│   ├── components/         # Shared UI components
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API service layer
│   ├── types/              # TypeScript type definitions
│   └── utils/              # Utility functions
├── docs/
│   └── architecture.md     # Frontend architecture docs
└── package.json
```

### Key Features

1. **Real-time Updates**: Subscribes to AppSync subscriptions for live dialogue updates
2. **Dialogue Timeline**: Visual representation of call events
3. **Search & Filter**: Filter dialogues by various criteria
4. **Metrics Dashboard**: Display key performance indicators

## Deployment

### Infrastructure Deployment

The infrastructure is managed via Terraform with environment-specific workflows:

```bash
# GitHub Actions workflows
.github/workflows/tf-dev.yml     # Development environment
.github/workflows/tf-qa.yml      # QA environment
.github/workflows/tf-stage.yml   # Staging environment
.github/workflows/tf-prod.yml    # Production environment
```

### Lambda Code Deployment

Lambda code deployment process:
1. TypeScript code is built and bundled
2. Artifacts uploaded to S3 build bucket
3. Lambda layers (node_modules) uploaded separately
4. Terraform references S3 artifacts

**Local Deployment** (dev only):
```bash
# View available commands
make help

# Deploy specific Lambda
make deploy-lambda-region-distributor

# Deploy Lambda layer
make deploy-layer-distributor
```

### Multi-Region Deployment

Lumina supports multi-region deployment for:
- Data residency requirements
- Low-latency access
- High availability

Primary regions:
- `eu-west-1` (Ireland) - EMEA
- `us-east-1` (N. Virginia) - Americas
- `ap-southeast-2` (Sydney) - APAC

## Integration Points

### Event Sources

| Source | Event Types | Transport |
|--------|-------------|-----------|
| GP (Global Platform) | Call events, routing decisions | Direct Lambda invocation |
| RT (RealTime) | Real-time call state changes | Direct Lambda invocation |
| PBX | CDR events | API Gateway |

### Downstream Systems

| System | Purpose | Integration |
|--------|---------|-------------|
| NEXUS | Metrics analytics | Firehose → S3 → Athena |
| OpenSearch | Historical search | Lambda → OpenSearch API |
| natterbox-lumina | User interface | AppSync GraphQL |

## Monitoring & Observability

### CloudWatch Metrics

Key metrics monitored:
- Lambda invocation counts and errors
- Kinesis shard iterator age
- DynamoDB consumed capacity
- AppSync request latency

### Logging

All Lambda functions use structured logging via custom Logger library:
- Request IDs tracked via ContextManager
- Log levels: INFO, WARN, ERROR
- Sensitive data redaction

### Alarms

Recommended CloudWatch alarms:
- High Lambda error rate (>1%)
- Kinesis iterator age (>60 seconds)
- DynamoDB throttling events
- AppSync error rate

## Security

### Authentication

- AppSync uses custom Lambda authorizer
- JWT token validation
- Organization-level access control

### Encryption

- DynamoDB: KMS encryption at rest
- Kinesis: Server-side encryption
- S3: SSE-S3 or SSE-KMS
- AppSync: TLS 1.2+ in transit

### IAM Policies

Least-privilege IAM roles for each Lambda:
- DynamoDB: BatchGetItem, BatchWriteItem, Query, PutItem, UpdateItem
- Kinesis: GetRecords, GetShardIterator, DescribeStream
- SQS: SendMessage, GetQueueAttributes
- AppSync: GraphQL mutations

## Development Guide

### Prerequisites

- Node.js v22+
- npm
- AWS CLI configured
- Terraform 1.x

### Local Setup

```bash
# Clone repository
git clone git@github.com:redmatter/lumina.git
cd lumina

# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm run test

# Run linter
npm run lint

# Format code
npm run format
```

### GraphQL Type Generation

Generate TypeScript types from GraphQL schema:

```bash
npm run generate:gql-schema
```

### Testing

```bash
# Run all unit tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test -- path/to/test.spec.ts
```

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Resolution |
|-------|---------------|------------|
| Events not appearing | Kinesis consumer lag | Check shard iterator age, scale shards |
| Subscription timeout | AppSync authorizer failure | Check Lambda authorizer logs |
| Missing dialogues | DynamoDB write failure | Check Lambda error logs, DLQ |
| Slow queries | DynamoDB scan operation | Ensure proper key-based queries |

### Debug Logging

Enable debug logging in Lambda environment variables:
```
LOG_LEVEL=DEBUG
```

### DLQ Processing

Failed events can be reprocessed from the DLQ:
1. Review messages in DLQ
2. Fix underlying issue
3. Move messages back to main queue or reprocess via Lambda

## Future Roadmap

- **Enhanced Metrics**: Additional call quality metrics
- **AI Insights**: Machine learning for anomaly detection
- **Extended Retention**: Longer-term historical data storage
- **Custom Dashboards**: User-configurable monitoring views

## References

- [Confluence: Lumina - Observability, Metrics, Logs](https://natterbox.atlassian.net/wiki/spaces/DP/pages/2173009923)
- [GitHub: lumina Repository](https://github.com/redmatter/lumina)
- [GitHub: aws-terraform-lumina-pipeline](https://github.com/redmatter/aws-terraform-lumina-pipeline)
- [GitHub: natterbox-lumina](https://github.com/redmatter/natterbox-lumina)
