# TTS Gateway Service

> **Last Updated:** 2026-01-20  
> **Source:** Confluence Architecture Space, Engineering Pages  
> **Status:** ✅ Complete  
> **SME:** James Bravo

---

## Overview

The **tts-gateway** is a critical voice routing component responsible for processing Text-to-Speech (TTS) requests from FreeSWITCH PBX servers. It converts text into audio using cloud-based TTS services (Amazon Polly and Google Cloud TTS) and delivers the audio back to the PBX for playback to callers.

The service is invoked when:
- A customer's **routing policy** includes a Text-to-Speech element
- Built-in services such as **VoiceMail** need to speak phrases
- **IVR menus** need to announce options to callers

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TTS GATEWAY ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   PBX SERVERS                                                                    │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                       │
│   │ FreeSWITCH  │     │ FreeSWITCH  │     │ FreeSWITCH  │                       │
│   │   PBX 1     │     │   PBX 2     │     │   PBX n     │                       │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                       │
│          │ SIP/MRCP          │ SIP/MRCP          │ SIP/MRCP                     │
│          └─────────────┬─────┴─────────────┬─────┘                              │
│                        │                   │                                     │
│                        ▼                   ▼                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐     │
│   │                    NETWORK LOAD BALANCER (NLB)                        │     │
│   │                    • Port 5060 (SIP)                                  │     │
│   │                    • Port 5062 (MRCP)                                 │     │
│   │                    • Health checks via Lambda                         │     │
│   └───────────────────────────────┬───────────────────────────────────────┘     │
│                                   │                                              │
│                                   ▼                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐     │
│   │                         ECS FARGATE CLUSTER                           │     │
│   │                                                                       │     │
│   │   ┌─────────────────────────────────────────────────────────────────┐ │     │
│   │   │                    TTS-GATEWAY CONTAINERS                       │ │     │
│   │   │                                                                 │ │     │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │ │     │
│   │   │   │   Task 1    │  │   Task 2    │  │   Task 3    │  (Prod)    │ │     │
│   │   │   │             │  │             │  │             │            │ │     │
│   │   │   │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │            │ │     │
│   │   │   │ │  TTS    │ │  │ │  TTS    │ │  │ │  TTS    │ │            │ │     │
│   │   │   │ │ Gateway │ │  │ │ Gateway │ │  │ │ Gateway │ │            │ │     │
│   │   │   │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │            │ │     │
│   │   │   │ │  Stats  │ │  │ │  Stats  │ │  │ │  Stats  │ │            │ │     │
│   │   │   │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │            │ │     │
│   │   │   │ │ Syslog  │ │  │ │ Syslog  │ │  │ │ Syslog  │ │            │ │     │
│   │   │   │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │            │ │     │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘            │ │     │
│   │   └─────────────────────────────────────────────────────────────────┘ │     │
│   └───────────────────────────────────────────────────────────────────────┘     │
│                                   │                                              │
│                    ┌──────────────┴──────────────┐                              │
│                    │                             │                              │
│                    ▼                             ▼                              │
│   ┌─────────────────────────┐   ┌─────────────────────────┐                     │
│   │      Amazon Polly       │   │   Google Cloud TTS      │                     │
│   │    (Primary Provider)   │   │  (Secondary Provider)   │                     │
│   └─────────────────────────┘   └─────────────────────────┘                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Protocol Flow

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│ FreeSWITCH  │                    │ TTS Gateway │                    │  AWS Polly  │
│    PBX      │                    │             │                    │ Google TTS  │
└──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
       │                                  │                                  │
       │ 1. SIP INVITE (TTS request)      │                                  │
       │─────────────────────────────────►│                                  │
       │                                  │                                  │
       │                                  │ 2. Check local cache             │
       │                                  │◄──────────────────               │
       │                                  │                                  │
       │                                  │ [Cache Miss]                     │
       │                                  │ 3. REST API call                 │
       │                                  │─────────────────────────────────►│
       │                                  │                                  │
       │                                  │ 4. Audio file (MP3)              │
       │                                  │◄─────────────────────────────────│
       │                                  │                                  │
       │                                  │ 5. Convert to RTP format         │
       │                                  │◄──────────────────               │
       │                                  │                                  │
       │                                  │ 6. Cache audio                   │
       │                                  │◄──────────────────               │
       │                                  │                                  │
       │ 7. RTP Audio Stream              │                                  │
       │◄─────────────────────────────────│                                  │
       │                                  │                                  │
```

---

## Communication Protocols

### Service Inputs

| Source | Protocol | Description |
|--------|----------|-------------|
| FreeSWITCH | **SIP** (Port 5060) | Session initiation for TTS requests |
| FreeSWITCH | **MRCP** (Port 5062) | Media Resource Control Protocol for TTS fragment requests |

### Service Outputs

| Destination | Protocol | Description |
|-------------|----------|-------------|
| FreeSWITCH | **RTP** | Audio stream returned to PBX for playback |

### External Integrations

| Service | Protocol | Description |
|---------|----------|-------------|
| Amazon Polly | REST API | Submit text, receive MP3/PCM audio |
| Google Cloud TTS | REST API | Submit text, receive MP3 audio |

---

## Voice Providers

### Amazon Polly

The primary TTS provider offering high-quality neural and standard voices.

**Configuration:**
```
AWS_POLLY_KEY: Stored in SSM Parameter Store
AWS_POLLY_SECRET: Stored in SSM Parameter Store
```

**Voice Types:**
- **Standard**: Lower latency, suitable for simple announcements
- **Neural**: Higher quality, more natural-sounding, recommended for customer-facing IVRs

**Regional Failover:**
| TTS Gateway Region | Primary Polly Region | Failover Region |
|--------------------|---------------------|-----------------|
| eu-west-1 | eu-west-1 | eu-west-2 |
| eu-west-2 | eu-west-2 | eu-west-1 |
| eu-central-1 | eu-central-1 | eu-west-2 |
| us-east-1 | us-east-1 | ca-central-1 |
| us-east-2 | us-east-1 | ca-central-1 |
| us-west-2 | us-west-2 | ca-central-1 |
| ap-southeast-1 | ap-southeast-1 | ap-southeast-2 |
| ap-southeast-2 | ap-southeast-2 | ap-southeast-1 |

### Google Cloud TTS

Secondary provider offering additional voice options and languages.

**Configuration:**
```
GOOGLE_TTS_KEY: Stored in SSM Parameter Store
```

**Voice Types:**
- **Wavenet**: AI-enhanced conversational voices
- **Standard**: Basic synthesized voices

### Future Providers

The platform is being modernized to support additional providers:
- **ElevenLabs**: High-fidelity cloned and custom voices
- **Hume AI**: Emotionally expressive voices

---

## Voice Management

### Voice Naming Convention

Voices are identified using IETF BCP 47 language tags combined with voice names:

```
Format: <LANGUAGE>-<COUNTRY>_<VOICE_NAME>_<VARIANT>

Examples:
- EN-US_AMY_NEURAL     → US English, Amy voice, Neural variant
- DA-DK_ANNA_AI        → Danish Denmark, Anna voice, AI variant
- FR-CA_RAPHAEL_AI     → Canadian French, Raphael voice, AI variant
```

### Voice ID Mapping

The system maintains mapping between different voice ID formats:

| Format | Example | Usage |
|--------|---------|-------|
| Sapien (IETF BP47) | `DA-DK_ANNA_AI` | User interface, routing policies |
| Switch/DB Name | `da-anna-ai` | FreeSWITCH configuration, CoreDB |
| Provider Voice ID | `da-DK-Wavenet-A` | API calls to Google/Polly |

### Adding New Voices

**Important:** Adding new TTS voices requires updates to approximately **11 components**. The current process involves:

1. **Update Voice Sheet** (Google Sheets master list)
2. **TTS Gateway** configuration
3. **Sapien** - Voice maps and tests
4. **API Data Schema** - Migration files
5. **AVS** - Policy Builder and SFDX App
6. **FSCallManagement** - Test data
7. **FSCore** - Internationalization XML
8. **Dialplan** - dpSupport.xml
9. **FSxinetdSocket** - Test files
10. **CoreAPI** - Configuration
11. **Documentation** - README updates

> **Note:** A new architecture is being developed to dynamically manage voices via DynamoDB and the Delta API, eliminating the need to update multiple services. See [TTS Voices - New Architecture](#future-architecture-dynamodb-based) below.

---

## Caching Strategy

TTS Gateway implements aggressive caching to optimize performance and reduce costs:

### Why Caching Matters

| Factor | Without Cache | With Cache |
|--------|---------------|------------|
| **Cost** | Charged per character | One-time charge per unique phrase |
| **Latency** | 100-500ms per request | <10ms for cached items |
| **CPU Usage** | Audio conversion on every request | Cached audio served directly |

### Cache Implementation

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CACHE LOOKUP FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   TTS Request                                                       │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────┐                  │
│   │  Generate Cache Key                          │                  │
│   │  key = MD5(text + voice + language)          │                  │
│   └──────────────────┬──────────────────────────┘                  │
│                      │                                              │
│                      ▼                                              │
│   ┌─────────────────────────────────────────────┐                  │
│   │  Check Local Cache                           │                  │
│   └──────────────────┬──────────────────────────┘                  │
│                      │                                              │
│          ┌───────────┴───────────┐                                 │
│          │                       │                                 │
│     [Cache Hit]             [Cache Miss]                           │
│          │                       │                                 │
│          ▼                       ▼                                 │
│   ┌─────────────┐      ┌─────────────────────┐                     │
│   │ Return      │      │ Call TTS Provider   │                     │
│   │ Cached      │      │ Convert Audio       │                     │
│   │ Audio       │      │ Store in Cache      │                     │
│   └─────────────┘      └──────────┬──────────┘                     │
│                                   │                                 │
│                                   ▼                                 │
│                          Return Audio                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Cache Expiration

- Cache entries have a configurable TTL (Time To Live)
- Service degradation is gradual if TTS providers become unavailable
- Common phrases remain available from cache during outages

---

## Deployment

### Infrastructure (AWS)

TTS Gateway is deployed as a containerized service on AWS ECS Fargate:

| Component | Technology | Details |
|-----------|------------|---------|
| Compute | ECS Fargate | No EC2 management required |
| Load Balancer | NLB (Network Load Balancer) | TCP/UDP load balancing for SIP |
| Container Registry | ECR | Private Docker image storage |
| Secrets | SSM Parameter Store | API keys for Polly/Google |
| Logging | CloudWatch Logs | Container logs with 30-day retention |
| Monitoring | CloudWatch Metrics | CPU, memory, custom metrics |
| Alerting | SNS | Alarm notifications |
| DNS | Route53 | `mrcp.<region>.internal` |

### Task Configuration

| Environment | Task Count | CPU | Memory |
|-------------|------------|-----|--------|
| dev | 1 | 256 | 512 MB |
| qa | 1 | 256 | 512 MB |
| stage | 1 | 256 | 512 MB |
| **prod** | **3** | 256 | 512 MB |

### Container Composition

Each ECS task includes:

1. **tts-gateway** - Main TTS processing container
2. **stats-tts** - Metrics collection sidecar
3. **syslog-forwarder** - Log forwarding sidecar

### Terraform Module

**Repository:** `redmatter/aws-terraform-rt-tts`

The module provisions:
- ECS Service and Task Definition
- Network Load Balancer and Target Groups
- Security Groups (tts, tts-client)
- CloudWatch Log Groups and Alarms
- SSM Parameters for credentials
- Route53 DNS records
- IAM Roles for task execution
- Lambda for SIP health checks
- CloudWatch Dashboard

**Key Terraform Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `task_count` | 3 (prod) | Number of TTS Gateway containers |
| `task_cpu` | 256 | CPU units per task |
| `task_memory` | 512 | Memory (MB) per task |
| `port_sip` | 5060 | SIP signaling port |
| `port_mrcp` | 5062 | MRCP control port |
| `dns_name` | mrcp | DNS prefix for the service |
| `log_retention_days` | 30 | CloudWatch log retention |

---

## Monitoring & Alerting

### CloudWatch Alarms

| Alarm | Threshold | Description |
|-------|-----------|-------------|
| ECS CPU Utilization | >70% for 2 min | High CPU on containers |
| ECS Memory Utilization | >70% for 2 min | High memory on containers |
| ECS Tasks Running | <1 for 2 min | No healthy tasks |
| ECS Deployment | >2 for 7 min | Deployment stuck |
| Healthcheck Duration | >200ms for 3 of 10 min | Slow TTS responses |
| Healthcheck Error | >1 for 2 of 5 min | Health check failures |

### SIP Health Check Lambda

A custom Lambda function (`HealthcheckSIP`) performs active health checks:
- Runs every minute via CloudWatch Events
- Sends SIP requests to verify service availability
- Reports metrics to CloudWatch
- Triggers alerts on failures

### Key Metrics

| Metric | Description |
|--------|-------------|
| `TTS/RequestCount` | Number of TTS requests |
| `TTS/CacheHitRate` | Percentage of requests served from cache |
| `TTS/Latency` | Time to generate and return audio |
| `TTS/ProviderErrors` | Failures calling Polly/Google |
| `ECS/CPUUtilization` | Container CPU usage |
| `ECS/MemoryUtilization` | Container memory usage |

### CloudWatch Dashboard

A pre-configured dashboard shows:
- Request volume over time
- Cache hit/miss ratio
- Provider error rates
- Container resource utilization
- Health check status

---

## Operational Runbooks

### Service Not Responding

1. Check ECS task status in AWS Console
2. Review CloudWatch logs for errors
3. Verify NLB target health
4. Check security group rules
5. Restart tasks if necessary

### High Latency

1. Check cache hit rate (low rate = more provider calls)
2. Verify network connectivity to Polly/Google
3. Review CPU utilization
4. Consider scaling up task count

### Provider Failures

1. Check AWS Service Health Dashboard
2. Verify API credentials in SSM
3. Review provider-specific error messages
4. Consider failing over to alternate provider

### Cache Issues

1. Check disk space (if using local cache)
2. Review cache TTL settings
3. Monitor cache hit rate
4. Consider cache warm-up for common phrases

---

## Impact of Service Failure

| Scenario | Customer Impact |
|----------|-----------------|
| Complete TTS Gateway failure | No TTS announcements; callers cannot hear IVR options, may misroute calls |
| Provider unavailable (cache warm) | Minimal impact; cached phrases continue to work |
| Provider unavailable (cache cold) | New unique phrases fail; common phrases work from cache |
| Single task failure | No impact; NLB routes to healthy tasks |

---

## Future Architecture (DynamoDB-Based)

A new architecture is being developed to modernize TTS voice management:

### Key Changes

1. **Dynamic Voice Management**
   - Voice records stored in DynamoDB `RT_Settings` table
   - Global table replication across all RT regions
   - No code deployments required to add voices

2. **Delta API Integration**
   - New REST microservice for voice management
   - Accessible from Salesforce AVS via Apex
   - Accessible from Routing Policies via Graph API

3. **Caching Strategy**
   - Services cache voice IDs locally
   - Periodic refresh from DynamoDB
   - Invalid voice ID triggers cache refresh

4. **Voice Provider Profiles**
   - Providers defined as separate DynamoDB records
   - Regional availability tracked per provider
   - Easy addition of new providers (ElevenLabs, Hume, etc.)

### New DynamoDB Schema

```json
// Voice Record
{
  "PK": "VOICE_ORG#SYSTEM",
  "SK": "VOICE_ID#DA-DK_ANNA_AI",
  "SK2": "VOICE#da-dk#female",
  "serviceVoiceId": "da-anna-ai",
  "providerVoiceId": "da-DK-Wavenet-A",
  "providerProfile": "GoogleCloudNeural",
  "language": "DANISH",
  "country": "DENMARK",
  "friendlyName": "Anna",
  "userDescription": "An AI enhanced conversational Danish female voice",
  "gender": "FEMALE"
}

// Provider Profile
{
  "PK": "VOICE_PROVIDER",
  "SK": "VOICE_PROVIDER#GoogleCloudNeural",
  "providerProfile": "GoogleCloudNeural",
  "regions": ["use2", "usw2", "euw1", "euw2"],
  "description": "Neural voices for Google Cloud"
}
```

---

## Source Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| `platform-tts-gateway` (Bitbucket) | Main TTS gateway service | C |
| `aws-terraform-rt-tts` | Terraform deployment module | HCL |
| `infrastructure-container-stats-tts` | Metrics collection container | Shell |

---

## Related Documentation

- [Voice Routing Overview](./overview.md) - Voice routing subsystem
- [fsxinetd Service](./fsxinetd.md) - Call processing service
- [CDR Processing](./cdr-processing.md) - Call detail records
- [Infrastructure Overview](../infrastructure/overview.md) - AWS deployment
- **Confluence:** [TTS Voices](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/1394409483/TTS+Voices)
- **Confluence:** [TTS Gateway Service Overview](https://natterbox.atlassian.net/wiki/spaces/A/pages/1162674206/tts-gateway+Service+Overview)

---

## References

- [Amazon Polly Documentation](https://docs.aws.amazon.com/polly/)
- [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)
- [MRCP Protocol RFC 6787](https://datatracker.ietf.org/doc/html/rfc6787)
- [Voice Sheet (Google Sheets)](https://docs.google.com/spreadsheets/d/1_cMh63exuRzJetBB0OXcyH5Wqpr9WBTc0JRUjMG7EqA/)

---

*Migrated from Confluence Architecture Space - tts-gateway Service Overview & Component View*
