# AI & Conversational AI (CAI) Architecture

> **Last Updated:** 2026-01-19  
> **Source:** Repository analysis, Document360, Terraform modules  
> **Status:** ✅ Complete

---

## Overview

Natterbox provides Conversational AI (CAI) capabilities that enable intelligent voice bots and AI-powered call handling. The system integrates with AWS Bedrock for LLM capabilities and supports multiple AI providers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SALESFORCE / AVS UI                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                      Routing Policy Builder                              │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │ Natterbox   │  │   Agent     │  │  Knowledge  │  │   Router    │    │  │
│   │  │     AI      │  │             │  │    Base     │  │             │    │  │
│   │  │ Container   │  │             │  │             │  │             │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
└───────────────────────────────────────┼─────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────────┐
│                         VOICE ROUTING (FreeSWITCH)                               │
├───────────────────────────────────────┼─────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                          fsxinetd / Lua Scripts                          │  │
│   │                    Execute CAI routing policy components                 │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│                                       │ WebSocket                               │
│                                       ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        CAI WebSocket Service                             │  │
│   │              Real-time bidirectional audio streaming                     │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
└───────────────────────────────────────┼─────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────────┐
│                              CAI SERVICE                                         │
├───────────────────────────────────────┼─────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        cai-service (TypeScript)                          │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │   Speech    │  │    LLM      │  │  Knowledge  │  │   Speech    │    │  │
│   │  │   to Text   │  │  Reasoning  │  │   Lookup    │  │  Synthesis  │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
└───────────────────────────────────────┼─────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼─────────────────────────────────────────┐
│                            AI PROVIDERS                                          │
├───────────────────────────────────────┼─────────────────────────────────────────┤
│   ┌─────────────┐    ┌─────────────┐  │  ┌─────────────┐    ┌─────────────┐   │
│   │    AWS      │    │   Google    │  │  │   AWS       │    │  Deepgram   │   │
│   │   Bedrock   │    │ Vertex AI   │◄─┴─►│   Polly     │    │   (STT)     │   │
│   │   (LLM)     │    │   (LLM)     │     │   (TTS)     │    │             │   │
│   └─────────────┘    └─────────────┘     └─────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. CAI Service

**Repository:** `redmatter/cai-service`

Core conversational AI service handling:
- Real-time speech processing
- LLM integration (multi-model support)
- Conversation state management
- Intent recognition
- Response generation

**Technology:** TypeScript/Node.js

### 2. CAI WebSocket Service

**Terraform:** `aws-terraform-rt-cai-websocket`

Real-time bidirectional audio streaming between FreeSWITCH and CAI service:
- Low-latency audio transmission
- Session management
- Connection state handling

### 3. AI Prompt Pipeline

**Repository:** `redmatter/aws-ai-prompt-pipeline`

Manages AI prompts and configurations:
- Prompt templates
- Persona definitions
- System instructions
- Response formatting

### 4. Test Rig

**Repository:** `redmatter/test-rig`

Batch testing for AI prompts:
- Scenario-based testing
- Regression testing
- Performance benchmarking
- Quality evaluation

---

## AI Provider Integrations

### AWS Bedrock (Primary LLM)

**Terraform:** `aws-terraform-bedrock`

Supported models:
- Claude (Anthropic)
- Titan (Amazon)
- Other Bedrock-supported models

**Features:**
- Cross-region inference profiles
- Usage aggregation
- Cost management

**Repository:** `redmatter/bedrock-metrics-aggregator`

### Google Vertex AI

**Repository:** `redmatter/nbx-ai-hub-api`, `redmatter/nbx-gemini-api`

Alternative LLM provider:
- Gemini models
- Internal/customer use
- Knowledge base integration

### Speech Services

| Service | Provider | Use Case |
|---------|----------|----------|
| **Speech-to-Text** | Deepgram, AWS Transcribe | Real-time transcription |
| **Text-to-Speech** | AWS Polly, Google TTS | Voice synthesis |

---

## Routing Policy Integration

CAI is integrated into the AVS routing policy builder as the **Natterbox AI** container component.

### Available CAI Components

| Component | Description |
|-----------|-------------|
| **Agent** | AI agent personality and behavior |
| **Get** | Retrieve information from data sources |
| **Skills** | Specific capabilities (booking, lookup, etc.) |
| **Knowledge** | Knowledge base queries |
| **Persona** | AI personality configuration |
| **Response** | Custom response templates |
| **Router** | Intent-based routing decisions |
| **Voicemail** | Voicemail handling |
| **Human Escalation** | Transfer to live agent |

### Configuration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AVS Routing Policy                            │
│                                                                  │
│   ┌─────────┐     ┌─────────────────────────────────────────┐  │
│   │ Inbound │────►│          Natterbox AI Container          │  │
│   │  Call   │     │  ┌────────┐  ┌─────────┐  ┌──────────┐  │  │
│   └─────────┘     │  │ Agent  │──│Knowledge│──│  Router  │  │  │
│                   │  └────────┘  └─────────┘  └────┬─────┘  │  │
│                   └────────────────────────────────┼────────┘  │
│                                                    │            │
│                   ┌────────────────────────────────┼────────┐  │
│                   │                                ▼        │  │
│                   │   ┌─────────┐     ┌─────────────────┐   │  │
│                   │   │ Resolved│     │ Human Escalation│   │  │
│                   │   │ by AI   │     │ → Agent Queue   │   │  │
│                   │   └─────────┘     └─────────────────┘   │  │
│                   └─────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Voice Configuration

### CAI Voices

Voices are configured via Lua script before CAI components:

```lua
-- Set CAI Voice
session:setVariable("cai_voice_id", "en-US-Neural2-F")
```

Available voice providers:
- AWS Polly (Neural voices)
- Google Cloud TTS
- Custom voice options

---

## Knowledge Base Integration

**Repository:** `redmatter/internal-knowledge-vertex`

The CAI system can query knowledge bases for contextual information:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    CAI      │────►│  Knowledge  │────►│  Document   │
│   Service   │     │    Base     │     │   Store     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Document   │
                    │   360       │
                    └─────────────┘
```

**Features:**
- Article ingestion from Document360
- Vector embeddings
- Semantic search
- Context retrieval

---

## Key Repositories

| Repository | Description | Language |
|------------|-------------|----------|
| `cai-service` | Core CAI service | TypeScript |
| `aws-ai-prompt-pipeline` | Prompt management | JavaScript |
| `test-rig` | AI testing framework | TypeScript |
| `bedrock-metrics-aggregator` | Usage tracking | TypeScript |
| `nbx-ai-hub-api` | Vertex AI wrapper | Python |
| `nbx-gemini-api` | Gemini API wrapper | Python |
| `internal-knowledge-vertex` | Knowledge processing | Python |

---

## Terraform Modules

| Module | Description |
|--------|-------------|
| `aws-terraform-cai` | CAI service infrastructure |
| `aws-terraform-cai-territory-setup` | Territory setup |
| `aws-terraform-cai-region-setup` | Region dependencies |
| `aws-terraform-bedrock` | Bedrock GenAI config |
| `aws-terraform-rt-cai-websocket` | WebSocket service |
| `aws-terraform-prismatic-cai-kb-poc` | Knowledge base POC |

---

## Conversation Flow

### Typical AI Call Handling

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Caller    │     │ FreeSWITCH  │     │ CAI Service │     │   Bedrock   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ Call Inbound      │                   │                   │
       │──────────────────►│                   │                   │
       │                   │ Audio Stream      │                   │
       │                   │ (WebSocket)       │                   │
       │                   │──────────────────►│                   │
       │                   │                   │ Transcribe        │
       │                   │                   │──────────────────►│ (Deepgram)
       │                   │                   │                   │
       │                   │                   │ LLM Request       │
       │                   │                   │──────────────────►│
       │                   │                   │ Response          │
       │                   │                   │◄──────────────────│
       │                   │                   │                   │
       │                   │ TTS Audio         │                   │
       │                   │◄──────────────────│                   │
       │ AI Response       │                   │                   │
       │◄──────────────────│                   │                   │
       │                   │                   │                   │
       │ ...conversation continues...          │                   │
       │                   │                   │                   │
       │                   │ Human Escalation  │                   │
       │                   │◄──────────────────│                   │
       │ Transfer to Agent │                   │                   │
       │◄──────────────────│                   │                   │
       │                   │                   │                   │
```

---

## Monitoring & Analytics

### Key Metrics

- AI conversation count
- Resolution rate (AI vs human escalation)
- Average conversation duration
- Intent recognition accuracy
- Response latency
- Cost per conversation

### Logging

- Conversation transcripts
- Intent detection logs
- LLM request/response logs
- Error tracking

---

## Related Documentation

- [Voice Routing Overview](../voice-routing/overview.md)
- [fsxinetd Service](../voice-routing/fsxinetd.md)
- [Document360: Setting up CAI](https://docs.natterbox.com/docs/en/setting-up-cai)
- [Document360: CAI Deployment Guide](https://docs.natterbox.com/docs/en/conversational-ai-deployment-guide)

---

*Documentation compiled from repository analysis and Document360*
