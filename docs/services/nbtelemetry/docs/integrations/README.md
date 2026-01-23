# NLE Integrations Overview

[![API Service](https://img.shields.io/badge/type-API%20Service-blue.svg)](/)
[![Docker](https://img.shields.io/badge/docker-enabled-2496ED.svg?logo=docker)](/)
[![Multi-Language](https://img.shields.io/badge/language-multi-orange.svg)](/)
[![NLE Providers](https://img.shields.io/badge/NLE%20providers-3-green.svg)](/)

> **nbtelemetry** - A powerful telemetry service for transcription and call analysis, integrating with multiple Natural Language Engine (NLE) providers to process and analyze call recordings with advanced features like talk time analysis, sentiment analysis, and interactive transcript visualization.

---

## Table of Contents

- [Overview](#overview)
- [Documentation](#documentation)
- [Supported Providers](#supported-providers)
- [Provider Selection](#provider-selection)
- [Transcription Standardization](#transcription-standardization)
- [Integration Index](#integration-index)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The **nbtelemetry** service provides a unified interface for processing call recordings through multiple Natural Language Engine (NLE) providers. Whether you're analyzing customer service calls, sales conversations, or support interactions, nbtelemetry normalizes the output from various providers into a consistent format, enabling powerful analytics capabilities including:

- **Multi-Provider Transcription**: Seamlessly switch between Watson, Google, and VoiceBase
- **Talk Time Analysis**: Understand conversation dynamics with speaker-level metrics
- **Sentiment Analysis**: Gauge emotional tone throughout conversations
- **Interactive Visualization**: JavaScript UI components for transcript exploration
- **Organization Management**: Multi-tenant support with user and organization hierarchies

---

## Documentation

Detailed integration guides and reference documentation are available for each supported NLE provider:

| Document | Description |
|----------|-------------|
| [VoiceBase Integration](docs/integrations/voicebase.md) | Complete guide for VoiceBase NLE setup and configuration |
| [Google NLE Integration](docs/integrations/google.md) | Google Speech-to-Text integration documentation |
| [Watson NLE Integration](docs/integrations/watson.md) | IBM Watson Speech to Text integration guide |

---

## Supported Providers

nbtelemetry integrates with three major NLE providers, each offering unique strengths for different use cases:

### IBM Watson Speech to Text

| Feature | Support Level |
|---------|---------------|
| Real-time transcription | ✅ Full |
| Speaker diarization | ✅ Full |
| Sentiment analysis | ✅ Full |
| Custom language models | ✅ Full |
| Word-level timestamps | ✅ Full |

Watson excels in enterprise environments requiring custom vocabulary and domain-specific language models.

### Google Cloud Speech-to-Text

| Feature | Support Level |
|---------|---------------|
| Real-time transcription | ✅ Full |
| Speaker diarization | ✅ Full |
| Sentiment analysis | ⚠️ Via Natural Language API |
| Automatic punctuation | ✅ Full |
| Multi-language support | ✅ 125+ languages |

Google offers the broadest language support and excellent accuracy for general-purpose transcription.

### VoiceBase

| Feature | Support Level |
|---------|---------------|
| Real-time transcription | ✅ Full |
| Speaker diarization | ✅ Full |
| PCI/PII redaction | ✅ Full |
| Predictive analytics | ✅ Full |
| Call categorization | ✅ Full |

VoiceBase specializes in call center analytics with built-in compliance features.

---

## Provider Selection

Choosing the right NLE provider depends on your specific requirements. nbtelemetry allows dynamic provider selection through configuration or per-request specification.

### Configuration-Based Selection

Create or update your provider configuration in `config/nle.php`:

```php
<?php

return [
    'default_provider' => env('NLE_DEFAULT_PROVIDER', 'watson'),
    
    'providers' => [
        'watson' => [
            'api_key' => env('WATSON_API_KEY'),
            'service_url' => env('WATSON_SERVICE_URL'),
            'model' => env('WATSON_MODEL', 'en-US_BroadbandModel'),
            'enabled' => true,
        ],
        
        'google' => [
            'credentials_path' => env('GOOGLE_APPLICATION_CREDENTIALS'),
            'project_id' => env('GOOGLE_PROJECT_ID'),
            'language_code' => 'en-US',
            'enabled' => true,
        ],
        
        'voicebase' => [
            'api_token' => env('VOICEBASE_API_TOKEN'),
            'api_url' => env('VOICEBASE_API_URL', 'https://apis.voicebase.com/v3'),
            'enabled' => true,
        ],
    ],
    
    'fallback_chain' => ['watson', 'google', 'voicebase'],
];
```

### Per-Request Provider Selection

You can override the default provider on individual API requests:

```bash
curl -X POST "https://your-domain.com/api/v1/transcriptions" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_url": "https://storage.example.com/calls/recording-123.wav",
    "provider": "google",
    "options": {
      "speaker_diarization": true,
      "sentiment_analysis": true
    }
  }'
```

### Provider Selection Strategy

```php
<?php

namespace App\Services;

use App\Contracts\NLEProviderInterface;

class ProviderSelector
{
    public function selectProvider(array $requirements): NLEProviderInterface
    {
        // Priority-based selection logic
        if ($requirements['pci_redaction'] ?? false) {
            return $this->getProvider('voicebase');
        }
        
        if (count($requirements['languages'] ?? []) > 1) {
            return $this->getProvider('google');
        }
        
        if ($requirements['custom_model'] ?? false) {
            return $this->getProvider('watson');
        }
        
        return $this->getProvider(config('nle.default_provider'));
    }
}
```

---

## Transcription Standardization

One of nbtelemetry's core features is normalizing transcription output from different providers into a unified format. This ensures your application code remains provider-agnostic.

### Standardized Transcript Format

All providers return data conforming to this schema:

```json
{
  "id": "transcript_abc123",
  "provider": "watson",
  "status": "completed",
  "duration_seconds": 342,
  "created_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "recording_url": "https://storage.example.com/calls/recording-123.wav",
    "sample_rate": 16000,
    "channels": 2
  },
  "transcript": {
    "full_text": "Hello, thank you for calling...",
    "confidence": 0.94,
    "segments": [
      {
        "speaker": "agent",
        "speaker_id": 0,
        "start_time": 0.0,
        "end_time": 3.5,
        "text": "Hello, thank you for calling.",
        "confidence": 0.96,
        "words": [
          {
            "word": "Hello",
            "start_time": 0.0,
            "end_time": 0.4,
            "confidence": 0.98
          }
        ]
      }
    ]
  },
  "analytics": {
    "talk_time": {
      "agent": 180,
      "customer": 162,
      "silence": 45,
      "overlap": 12
    },
    "sentiment": {
      "overall": 0.72,
      "agent": 0.85,
      "customer": 0.58,
      "timeline": [
        {"time": 0, "score": 0.5},
        {"time": 60, "score": 0.65},
        {"time": 120, "score": 0.72}
      ]
    }
  }
}
```

### Normalization Service

The `TranscriptNormalizer` class handles provider-specific transformations:

```php
<?php

namespace App\Services\Normalization;

class TranscriptNormalizer
{
    protected array $normalizers = [
        'watson' => WatsonNormalizer::class,
        'google' => GoogleNormalizer::class,
        'voicebase' => VoiceBaseNormalizer::class,
    ];
    
    public function normalize(string $provider, array $rawResponse): StandardizedTranscript
    {
        $normalizer = app($this->normalizers[$provider]);
        
        return $normalizer->normalize($rawResponse);
    }
}
```

---

## Integration Index

### Available API Endpoints

nbtelemetry exposes **19 API endpoints** organized by functionality:

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Transcription** | `/api/v1/transcriptions` | POST | Submit recording for transcription |
| | `/api/v1/transcriptions/{id}` | GET | Retrieve transcript by ID |
| | `/api/v1/transcriptions/{id}/status` | GET | Check transcription status |
| **Analytics** | `/api/v1/analytics/talk-time/{id}` | GET | Get talk time analysis |
| | `/api/v1/analytics/sentiment/{id}` | GET | Get sentiment analysis |
| | `/api/v1/analytics/summary/{id}` | GET | Get call summary |
| **Organizations** | `/api/v1/organizations` | GET/POST | List/create organizations |
| | `/api/v1/organizations/{id}` | GET/PUT/DELETE | Manage organization |
| **Users** | `/api/v1/users` | GET/POST | List/create users |
| | `/api/v1/users/{id}` | GET/PUT/DELETE | Manage user |
| **Providers** | `/api/v1/providers` | GET | List available providers |
| | `/api/v1/providers/{name}/status` | GET | Check provider health |

### Webhook Events

Configure webhooks to receive real-time notifications:

```php
// Supported webhook events
$events = [
    'transcription.started',
    'transcription.completed',
    'transcription.failed',
    'analytics.ready',
    'provider.error',
];
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose (v2.0+)
- PHP 8.1+ (for local development)
- Composer 2.x
- At least one NLE provider API credentials

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-org/nbtelemetry.git
cd nbtelemetry
```

2. **Install dependencies with Composer**

```bash
composer install
```

3. **Configure environment**

```bash
cp .env.example .env

# Edit .env with your provider credentials
nano .env
```

4. **Set up provider credentials in `.env`**

```env
# Default NLE Provider
NLE_DEFAULT_PROVIDER=watson

# IBM Watson Credentials
WATSON_API_KEY=your_watson_api_key
WATSON_SERVICE_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com

# Google Cloud Credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_PROJECT_ID=your-project-id

# VoiceBase Credentials
VOICEBASE_API_TOKEN=your_voicebase_token
```

5. **Start with Docker**

```bash
docker-compose up -d
```

6. **Run database migrations**

```bash
docker-compose exec app php artisan migrate
```

7. **Verify installation**

```bash
curl http://localhost:8080/api/v1/health
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        nbtelemetry                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   REST API  │  │  Webhooks   │  │   JS UI Components      │ │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘ │
│         │                │                       │              │
│  ┌──────▼────────────────▼───────────────────────▼────────────┐│
│  │                   Service Layer                             ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        ││
│  │  │ Transcription│ │  Analytics   │ │    Users/    │        ││
│  │  │   Service    │ │   Service    │ │    Orgs      │        ││
│  │  └──────┬───────┘ └──────┬───────┘ └──────────────┘        ││
│  └─────────┼────────────────┼─────────────────────────────────┘│
│            │                │                                   │
│  ┌─────────▼────────────────▼─────────────────────────────────┐│
│  │              Provider Abstraction Layer                     ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  ││
│  │  │  Watson  │  │  Google  │  │VoiceBase │                  ││
│  │  │ Adapter  │  │ Adapter  │  │ Adapter  │                  ││
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘                  ││
│  └───────┼─────────────┼─────────────┼────────────────────────┘│
└──────────┼─────────────┼─────────────┼──────────────────────────┘
           │             │             │
     ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
     │   IBM     │ │  Google   │ │ VoiceBase │
     │  Watson   │ │  Cloud    │ │    API    │
     └───────────┘ └───────────┘ └───────────┘
```

---

## Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    environment:
      - NLE_DEFAULT_PROVIDER=watson
      - WATSON_API_KEY=${WATSON_API_KEY}
      - GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID}
    volumes:
      - ./storage:/var/www/html/storage
    depends_on:
      - redis
      - database

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  database:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: nbtelemetry
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

### Production Deployment

```bash
# Build production image
docker build -t nbtelemetry:latest --target production .

# Run with production settings
docker run -d \
  --name nbtelemetry \
  -p 8080:80 \
  --env-file .env.production \
  nbtelemetry:latest
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Provider timeout | Large audio file or slow network | Increase `NLE_TIMEOUT` in `.env` |
| Authentication failed | Invalid API credentials | Verify provider credentials |
| Transcription stuck | Provider queue backlog | Check provider status endpoint |
| Low confidence scores | Poor audio quality | Ensure 16kHz+ sample rate |

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# In .env
LOG_LEVEL=debug
NLE_DEBUG=true
```

### Health Check

```bash
# Check overall service health
curl http://localhost:8080/api/v1/health

# Check specific provider
curl http://localhost:8080/api/v1/providers/watson/status
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is proprietary software. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>nbtelemetry</strong> - Unified Call Analytics & Transcription
</p>