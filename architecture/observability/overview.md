# Lumina - Observability Platform

> **Last Updated:** 2026-01-20  
> **Source:** Confluence, GitHub repository analysis, Terraform modules  
> **Status:** ✅ Complete

---

## Overview

**Lumina** is Natterbox's real-time observability and analytics platform. It provides dashboards, metrics visualization, and actionable insights across the telephony platform. Lumina operates with a global architecture that distributes data collection regionally while providing centralized aggregation and visualization.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Real-time Dashboards** | Live call metrics, queue stats, agent performance |
| **Custom Metrics** | Configurable customer-specific KPIs |
| **Historical Analytics** | Trend analysis and reporting |
| **Alerting** | Threshold-based alerts and notifications |
| **Multi-tenant** | Per-territory data isolation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LUMINA FRONTEND                                        │
│                    (React 19 + TypeScript + Vite)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│   │   Dashboard     │  │    Metrics      │  │    Charts       │                │
│   │   Components    │  │   Visualization │  │  (Recharts)     │                │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                │
│            └──────────────────┬─┴───────────────────┬┘                         │
│                               │ React Query         │                           │
│                               ▼                     │                           │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                    API Client (TanStack Query)                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ REST API
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       REGION DISTRIBUTOR                                         │
│              (AWS Lambda + API Gateway - Global Entry Point)                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                  Request Routing Logic                                  │  │
│   │  • Extracts region ID from request                                      │  │
│   │  • Maps region to backend URL                                           │  │
│   │  • Forwards request to regional Lumina API                              │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   EU-WEST-1         │  │   US-EAST-1         │  │   AP-SOUTHEAST-2    │
│   (Ireland)         │  │   (Virginia)        │  │   (Sydney)          │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │  Lumina API   │  │  │  │  Lumina API   │  │  │  │  Lumina API   │  │
│  │    (ECS)      │  │  │  │    (ECS)      │  │  │  │    (ECS)      │  │
│  └───────┬───────┘  │  │  └───────┬───────┘  │  │  └───────┬───────┘  │
│          │          │  │          │          │  │          │          │
│  ┌───────▼───────┐  │  │  ┌───────▼───────┐  │  │  ┌───────▼───────┐  │
│  │   Timestream  │  │  │  │   Timestream  │  │  │  │   Timestream  │  │
│  │   Database    │  │  │  │   Database    │  │  │  │   Database    │  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
              ▲                        ▲                        ▲
              │                        │                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│   │  Lumina        │  │    Kinesis      │  │   EventBridge   │                │
│   │  Ingestion     │◄─│    Streams      │◄─│   Integration   │                │
│   │  (ECS)         │  │                 │  │                 │                │
│   └────────────────┘  └─────────────────┘  └─────────────────┘                │
│            ▲                    ▲                    ▲                          │
│            │                    │                    │                          │
│   ┌────────┴────────┬──────────┴──────────┬────────┴────────┐                  │
│   │                 │                     │                 │                  │
│   ▼                 ▼                     ▼                 ▼                  │
│ ┌─────────┐    ┌─────────┐          ┌─────────┐      ┌─────────┐              │
│ │FreeSWITCH│    │ fsxinetd │          │Platform │      │   CAI   │              │
│ │ Events   │    │  Events │          │  API    │      │ Events  │              │
│ └─────────┘    └─────────┘          └─────────┘      └─────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Lumina Frontend

**Repository:** `redmatter/natterbox-lumina`

Modern React application providing the user interface for Lumina dashboards and analytics.

#### Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | Latest | Build tooling |
| TanStack Query | v5 | Data fetching & caching |
| Recharts | Latest | Charting library |
| Tailwind CSS | Latest | Styling |
| Zustand | Latest | State management |

#### Project Structure

```
src/
├── app/                    # Application shell and routing
│   ├── App.tsx            # Root component
│   ├── Router.tsx         # Route definitions
│   └── providers/         # Context providers
├── components/            # Reusable UI components
│   ├── charts/           # Chart components
│   ├── dashboard/        # Dashboard widgets
│   ├── layout/           # Layout components
│   └── ui/               # Base UI elements
├── hooks/                 # Custom React hooks
├── pages/                 # Page components
│   ├── DashboardList/    # Dashboard listing
│   ├── DashboardView/    # Dashboard viewer
│   ├── Login/            # Authentication
│   └── Settings/         # User settings
├── services/              # API services
├── stores/                # Zustand stores
├── types/                 # TypeScript definitions
└── utils/                 # Utility functions
```

#### Key Features

- **Dashboard Builder**: Visual dashboard creation with drag-and-drop
- **Widget Library**: Pre-built widgets for common metrics
- **Real-time Updates**: Live data via polling/WebSocket
- **Role-based Access**: Permission-controlled dashboards
- **Export**: PDF/CSV export capabilities
- **Theming**: Light/dark mode support

#### Development Setup

```bash
# Clone repository
git clone git@github.com:redmatter/natterbox-lumina.git
cd natterbox-lumina

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

---

### 2. Region Distributor

**Terraform:** `aws-terraform-lumina-region-distributor`

Global entry point that routes requests to the appropriate regional Lumina API based on the territory/region context.

#### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    CloudFront Distribution                       │
│               (Global Edge Distribution)                         │
└─────────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                    API Gateway (Regional)                        │
│                     api.lumina.natterbox.com                     │
└─────────────────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Lambda Function (Region Distributor)            │
├──────────────────────────────────────────────────────────────────┤
│  1. Extract region_id from request headers/JWT                   │
│  2. Look up region → backend URL mapping                         │
│  3. Forward request to regional Lumina API                       │
│  4. Return response to client                                    │
└──────────────────────────────────────────────────────────────────┘
```

#### Region Mapping

| Region ID | AWS Region | Backend URL |
|-----------|------------|-------------|
| 1 (UK) | eu-west-1 | lumina-api.eu-west-1.internal |
| 2 (US) | us-east-1 | lumina-api.us-east-1.internal |
| 3 (AU) | ap-southeast-2 | lumina-api.ap-southeast-2.internal |
| 4 (SG) | ap-southeast-1 | lumina-api.ap-southeast-1.internal |
| 5 (CA) | ca-central-1 | lumina-api.ca-central-1.internal |
| 6 (DE) | eu-central-1 | lumina-api.eu-central-1.internal |

---

### 3. Lumina API

**Repository:** `redmatter/lumina-api`  
**Terraform:** `aws-terraform-lumina-api`

Backend service providing REST endpoints for dashboard data, metric queries, and configuration management.

#### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboards` | GET | List available dashboards |
| `/api/dashboards/{id}` | GET | Get dashboard configuration |
| `/api/dashboards` | POST | Create new dashboard |
| `/api/metrics/query` | POST | Query metrics data |
| `/api/widgets` | GET | List widget templates |
| `/api/alerts` | GET/POST | Manage alerts |

#### Database: AWS Timestream

Lumina uses AWS Timestream for time-series metric storage:

**Tables:**
- `call_metrics` - Call volume, duration, outcomes
- `queue_metrics` - Queue statistics, wait times
- `agent_metrics` - Agent activity, availability
- `system_metrics` - Platform health metrics

**Query Example:**
```sql
SELECT 
    bin(time, 5m) as period,
    measure_name,
    AVG(measure_value::double) as avg_value
FROM "lumina"."call_metrics"
WHERE 
    time BETWEEN ago(1h) AND now()
    AND territory_id = '123'
GROUP BY bin(time, 5m), measure_name
ORDER BY period DESC
```

---

### 4. Lumina Pipeline (Data Ingestion)

**Terraform:** `aws-terraform-lumina-pipeline`

Processes events from platform services and writes metrics to Timestream.

#### Event Sources

| Source | Event Types | Description |
|--------|-------------|-------------|
| FreeSWITCH | Call start/end, DTMF, transfer | Core call events |
| fsxinetd | Routing decisions, IVR interactions | Call flow events |
| Platform API | Configuration changes, user actions | Admin events |
| CAI Service | AI conversation metrics | Conversational AI stats |

#### Pipeline Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Event Source   │────▶│  Kinesis Stream │────▶│   Lambda        │
│  (Platform)     │     │                 │     │  Processor      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │   Timestream    │
                                               │   Write         │
                                               └─────────────────┘
```

#### Event Processing

```typescript
// Example event structure
interface CallEvent {
  eventType: 'CALL_START' | 'CALL_END' | 'TRANSFER' | 'HOLD';
  timestamp: string;
  callId: string;
  territoryId: number;
  regionId: number;
  agentId?: string;
  queueId?: string;
  duration?: number;
  outcome?: string;
}

// Metric extraction
function processCallEvent(event: CallEvent): TimestreamRecord {
  return {
    Dimensions: [
      { Name: 'territory_id', Value: event.territoryId.toString() },
      { Name: 'region_id', Value: event.regionId.toString() },
      { Name: 'event_type', Value: event.eventType }
    ],
    MeasureName: 'call_metric',
    MeasureValue: event.duration?.toString() || '1',
    MeasureValueType: 'DOUBLE',
    Time: new Date(event.timestamp).getTime().toString(),
    TimeUnit: 'MILLISECONDS'
  };
}
```

---

### 5. Lumina Ingestion Service

**Terraform:** `aws-terraform-lumina-ingestion`

Dedicated ingestion service for high-volume metric collection.

#### Capabilities

- **Batch Processing**: Aggregates events before writing
- **Deduplication**: Handles duplicate events gracefully
- **Back-pressure**: Manages ingestion rate limits
- **Dead Letter Queue**: Failed events for retry/analysis

---

## Data Flow

### Real-time Metrics Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Call Event   │────▶│   Kinesis     │────▶│   Lambda      │────▶│  Timestream   │
│  (FreeSWITCH) │     │   Stream      │     │   Processor   │     │   Database    │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
                                                                           │
                                                                           │
┌───────────────┐     ┌───────────────┐     ┌───────────────┐              │
│   Lumina      │◀────│   Lumina      │◀────│   Region      │◀─────────────┘
│   Frontend    │     │   API         │     │  Distributor  │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Dashboard Query Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             USER REQUEST                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. Frontend sends query to Region Distributor                                   │
│    GET /api/metrics/query?dashboard=123&timeRange=1h                            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. Region Distributor extracts territory, routes to regional API               │
│    Header: X-Territory-Id: 456 → eu-west-1                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 3. Lumina API queries Timestream with territory filter                         │
│    SELECT ... FROM call_metrics WHERE territory_id = '456'                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 4. Response aggregated and returned to frontend                                 │
│    { "data": [...], "aggregations": {...} }                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Metric Categories

### Call Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `call_count` | Total calls in period | count |
| `call_duration` | Average call duration | seconds |
| `call_answer_rate` | Percentage of answered calls | percentage |
| `call_abandon_rate` | Percentage of abandoned calls | percentage |
| `call_wait_time` | Average time before answer | seconds |

### Queue Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `queue_depth` | Current calls in queue | count |
| `queue_wait_time` | Average queue wait | seconds |
| `queue_abandon_rate` | Queue abandonment rate | percentage |
| `queue_service_level` | SLA attainment | percentage |

### Agent Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `agent_available_count` | Agents in available state | count |
| `agent_busy_count` | Agents on calls | count |
| `agent_handle_time` | Average handle time | seconds |
| `agent_after_call_work` | Time in wrap-up | seconds |

### System Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `trunk_utilization` | SIP trunk usage | percentage |
| `api_latency` | API response times | milliseconds |
| `error_rate` | System error rate | percentage |

---

## Key Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| `natterbox-lumina` | Frontend application | React/TypeScript |
| `lumina-api` | Backend API service | TypeScript |
| `documentation-lumina` | Lumina documentation | Markdown |

---

## Terraform Modules

| Module | Description |
|--------|-------------|
| `aws-terraform-lumina-api` | Lumina API infrastructure |
| `aws-terraform-lumina-region-distributor` | Global request routing |
| `aws-terraform-lumina-pipeline` | Data ingestion pipeline |
| `aws-terraform-lumina-ingestion` | Metric ingestion service |

---

## Authentication & Authorization

### User Authentication

Lumina uses Auth0 for user authentication:

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│    User       │────▶│    Auth0      │────▶│   Lumina      │
│   Browser     │     │   Login       │     │   Frontend    │
└───────────────┘     └───────────────┘     └───────────────┘
                              │
                              │ JWT Token
                              ▼
                      ┌───────────────┐
                      │  Contains:    │
                      │  - user_id    │
                      │  - territory  │
                      │  - roles      │
                      │  - permissions│
                      └───────────────┘
```

### API Authorization

```typescript
// JWT claims used for authorization
interface JWTClaims {
  sub: string;           // User ID
  territory_id: number;  // Territory for data access
  region_id: number;     // AWS region
  roles: string[];       // User roles
  permissions: string[]; // Granular permissions
}
```

### Permission Model

| Role | Capabilities |
|------|--------------|
| **Viewer** | View dashboards, run queries |
| **Editor** | Create/edit dashboards, manage alerts |
| **Admin** | Full access, user management |
| **Super Admin** | Cross-territory access |

---

## Deployment

### Infrastructure

Lumina components are deployed across all Natterbox regions:

| Component | Deployment | Scaling |
|-----------|------------|---------|
| Frontend | CloudFront + S3 | Edge-cached |
| Region Distributor | Lambda@Edge | Auto-scaling |
| Lumina API | ECS Fargate | Service auto-scaling |
| Pipeline | Lambda | Concurrent executions |
| Timestream | Managed | Automatic |

### Environment Configuration

```bash
# Frontend environment variables
VITE_API_URL=https://api.lumina.natterbox.com
VITE_AUTH0_DOMAIN=natterbox.auth0.com
VITE_AUTH0_CLIENT_ID=<client_id>
VITE_AUTH0_AUDIENCE=https://api.lumina.natterbox.com
```

---

## Monitoring

### Key Dashboards

1. **Lumina Health** - Service health and API metrics
2. **Ingestion Pipeline** - Event processing rates and errors
3. **Query Performance** - Timestream query latencies
4. **User Activity** - Dashboard usage and engagement

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| API Error Rate | > 1% | PagerDuty alert |
| API Latency P99 | > 5s | PagerDuty alert |
| Pipeline Lag | > 5 min | Slack notification |
| Timestream Errors | > 0 | Investigation |

### Logging

- **Frontend**: Browser console, error boundary captures
- **API**: CloudWatch Logs with structured logging
- **Pipeline**: Lambda CloudWatch Logs
- **Traces**: AWS X-Ray for request tracing

---

## Development

### Local Development

```bash
# Frontend development
cd natterbox-lumina
npm install
npm run dev
# Access at http://localhost:5173

# API development (if local)
cd lumina-api
npm install
npm run dev
```

### Testing

```bash
# Frontend tests
npm test                 # Unit tests
npm run test:e2e        # E2E tests (Playwright)
npm run test:coverage   # Coverage report

# API tests
npm test
npm run test:integration
```

### Code Quality

- **ESLint**: Code linting
- **Prettier**: Code formatting
- **TypeScript**: Type checking
- **Husky**: Pre-commit hooks

---

## Future Roadmap

### Planned Enhancements

1. **Real-time Streaming**
   - WebSocket connections for live updates
   - Reduced polling overhead

2. **Advanced Analytics**
   - ML-powered anomaly detection
   - Predictive queue management

3. **Custom Alerting**
   - User-defined alert rules
   - Multiple notification channels

4. **Embedded Analytics**
   - Dashboard embedding in Salesforce
   - Public sharing capabilities

5. **Data Export**
   - Scheduled report generation
   - S3 export for data lake integration

---

## Related Documentation

- [Infrastructure Overview](../infrastructure/overview.md)
- [Voice Routing Overview](../voice-routing/overview.md)
- [AI/CAI Overview](../ai-cai/overview.md)
- [Confluence: Lumina Observability](https://natterbox.atlassian.net/wiki/spaces/DEV/pages/2173009923)
- [Confluence: Lumina Data Flow](https://natterbox.atlassian.net/wiki/spaces/DEV/pages/2364932108)

---

*Documentation compiled from Confluence, repository analysis, and Terraform modules*
