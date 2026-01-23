# Watson NLE Integration

## Overview

The nbtelemetry service integrates with IBM Watson Speech to Text and Natural Language Understanding (NLE) services to provide enterprise-grade transcription and analysis capabilities for call recordings. Watson's NLE integration serves as one of the primary transcription providers in the multi-provider architecture, offering high-accuracy speech-to-text conversion, speaker diarization, and advanced natural language analysis features.

### Why Watson NLE?

IBM Watson provides several advantages for call center analytics:

- **High Accuracy**: Watson's speech recognition models are trained on diverse audio datasets, providing excellent accuracy across different accents, industries, and audio qualities
- **Speaker Diarization**: Automatic identification and separation of multiple speakers in a conversation
- **Sentiment Analysis**: Built-in natural language understanding for sentiment scoring
- **Custom Language Models**: Ability to train custom models for industry-specific terminology
- **Enterprise Support**: SLA-backed enterprise support and compliance certifications

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      nbtelemetry Service                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │  Recording  │───▶│ NLE Router   │───▶│ Watson Provider │   │
│  │  Ingestion  │    │              │    └────────┬────────┘   │
│  └─────────────┘    └──────────────┘             │             │
│                                                   ▼             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │ Transcript  │◀───│   Results    │◀───│ Watson Cloud    │   │
│  │   Storage   │    │  Processor   │    │ Speech-to-Text  │   │
│  └─────────────┘    └──────────────┘    └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Supported Watson Services

| Service | Purpose | Required |
|---------|---------|----------|
| Speech to Text | Audio transcription | Yes |
| Natural Language Understanding | Sentiment & entity analysis | Optional |
| Tone Analyzer | Emotional tone detection | Optional |

---

## Configuration

### Prerequisites

Before configuring Watson NLE integration, ensure you have:

1. An IBM Cloud account with Watson services provisioned
2. API credentials (API Key and Service URL) for Watson Speech to Text
3. Optionally, credentials for Natural Language Understanding service
4. Network access from your nbtelemetry deployment to IBM Cloud endpoints

### Obtaining Watson Credentials

1. Log into [IBM Cloud Console](https://cloud.ibm.com)
2. Navigate to **Resource List** → **AI / Machine Learning**
3. Select your Speech to Text instance
4. Copy the **API Key** and **URL** from the Credentials section

### Environment Configuration

Configure Watson integration through environment variables in your Docker deployment or `.env` file:

```bash
# Watson Speech to Text Configuration
WATSON_STT_API_KEY=your_watson_api_key_here
WATSON_STT_URL=https://api.us-south.speech-to-text.watson.cloud.ibm.com
WATSON_STT_REGION=us-south

# Watson Natural Language Understanding (Optional)
WATSON_NLU_API_KEY=your_watson_nlu_api_key_here
WATSON_NLU_URL=https://api.us-south.natural-language-understanding.watson.cloud.ibm.com

# Provider Selection
NLE_DEFAULT_PROVIDER=watson
NLE_FALLBACK_PROVIDERS=google,voicebase

# Watson-specific Options
WATSON_MODEL=en-US_BroadbandModel
WATSON_SPEAKER_LABELS=true
WATSON_SMART_FORMATTING=true
WATSON_PROFANITY_FILTER=false
WATSON_WORD_CONFIDENCE=true
WATSON_TIMESTAMPS=true
```

### PHP Configuration File

Create or update the Watson configuration in your PHP configuration:

```php
<?php
// config/watson.php

return [
    'speech_to_text' => [
        'api_key' => env('WATSON_STT_API_KEY'),
        'url' => env('WATSON_STT_URL', 'https://api.us-south.speech-to-text.watson.cloud.ibm.com'),
        'version' => '2021-09-01',
        
        // Recognition settings
        'model' => env('WATSON_MODEL', 'en-US_BroadbandModel'),
        'speaker_labels' => env('WATSON_SPEAKER_LABELS', true),
        'smart_formatting' => env('WATSON_SMART_FORMATTING', true),
        'profanity_filter' => env('WATSON_PROFANITY_FILTER', false),
        'word_confidence' => env('WATSON_WORD_CONFIDENCE', true),
        'timestamps' => env('WATSON_TIMESTAMPS', true),
        
        // Timeout settings (in seconds)
        'connection_timeout' => 30,
        'request_timeout' => 300,
        
        // Retry configuration
        'max_retries' => 3,
        'retry_delay' => 1000, // milliseconds
    ],
    
    'natural_language_understanding' => [
        'api_key' => env('WATSON_NLU_API_KEY'),
        'url' => env('WATSON_NLU_URL'),
        'version' => '2021-08-01',
        
        'features' => [
            'sentiment' => true,
            'emotion' => true,
            'keywords' => true,
            'entities' => true,
        ],
    ],
];
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  nbtelemetry:
    image: nbtelemetry:latest
    environment:
      - WATSON_STT_API_KEY=${WATSON_STT_API_KEY}
      - WATSON_STT_URL=${WATSON_STT_URL}
      - WATSON_STT_REGION=${WATSON_STT_REGION}
      - WATSON_NLU_API_KEY=${WATSON_NLU_API_KEY}
      - WATSON_NLU_URL=${WATSON_NLU_URL}
      - NLE_DEFAULT_PROVIDER=watson
      - WATSON_MODEL=en-US_BroadbandModel
      - WATSON_SPEAKER_LABELS=true
    volumes:
      - ./config:/app/config
      - ./storage:/app/storage
    networks:
      - nbtelemetry-network

networks:
  nbtelemetry-network:
    driver: bridge
```

### Available Watson Models

| Model | Description | Use Case |
|-------|-------------|----------|
| `en-US_BroadbandModel` | US English, 16kHz+ audio | High-quality recordings |
| `en-US_NarrowbandModel` | US English, 8kHz audio | Phone calls, low-bandwidth |
| `en-US_Telephony` | Optimized for phone audio | Call center recordings |
| `en-US_Multimedia` | General purpose | Mixed content types |
| `en-GB_BroadbandModel` | British English | UK call centers |
| `es-ES_BroadbandModel` | Spanish (Spain) | Spanish language support |

---

## Usage

### Basic Transcription Request

Submit a call recording for Watson transcription using the API:

```bash
# Submit recording for transcription
curl -X POST "https://your-nbtelemetry-instance/api/transcriptions" \
  -H "Authorization: Bearer your_api_token" \
  -H "Content-Type: application/json" \
  -d '{
    "recording_url": "https://storage.example.com/recordings/call_12345.wav",
    "provider": "watson",
    "callback_url": "https://your-app.com/webhooks/transcription",
    "options": {
      "speaker_labels": true,
      "sentiment_analysis": true,
      "language": "en-US"
    }
  }'
```

### PHP SDK Usage

```php
<?php

use NBTelemetry\Providers\Watson\WatsonTranscriptionService;
use NBTelemetry\Models\Recording;
use NBTelemetry\Models\TranscriptionJob;

class CallAnalysisController
{
    private WatsonTranscriptionService $watsonService;
    
    public function __construct(WatsonTranscriptionService $watsonService)
    {
        $this->watsonService = $watsonService;
    }
    
    /**
     * Submit a recording for Watson transcription
     */
    public function transcribeRecording(Recording $recording): TranscriptionJob
    {
        // Configure transcription options
        $options = [
            'model' => 'en-US_Telephony',
            'speaker_labels' => true,
            'smart_formatting' => true,
            'word_confidence' => true,
            'timestamps' => true,
            'profanity_filter' => false,
            'inactivity_timeout' => -1, // Disable timeout for long recordings
        ];
        
        // Submit to Watson
        $job = $this->watsonService->createTranscriptionJob(
            $recording->getAudioUrl(),
            $options
        );
        
        // Store job reference for status tracking
        $recording->setTranscriptionJobId($job->getId());
        $recording->setTranscriptionProvider('watson');
        $recording->save();
        
        return $job;
    }
    
    /**
     * Process completed Watson transcription
     */
    public function processTranscriptionResult(TranscriptionJob $job): array
    {
        $result = $this->watsonService->getTranscriptionResult($job->getId());
        
        // Extract speaker-labeled transcript
        $transcript = $this->watsonService->formatSpeakerTranscript(
            $result['results'],
            $result['speaker_labels']
        );
        
        // Calculate talk time metrics
        $talkTimeAnalysis = $this->watsonService->analyzeTalkTime(
            $result['speaker_labels']
        );
        
        return [
            'transcript' => $transcript,
            'talk_time' => $talkTimeAnalysis,
            'confidence' => $result['results'][0]['alternatives'][0]['confidence'],
            'word_count' => count($result['results'][0]['alternatives'][0]['timestamps']),
        ];
    }
}
```

### Handling Webhooks

```php
<?php

use NBTelemetry\Http\Controllers\WebhookController;
use Illuminate\Http\Request;

class WatsonWebhookController extends WebhookController
{
    /**
     * Handle Watson transcription completion callback
     */
    public function handleTranscriptionComplete(Request $request)
    {
        $payload = $request->json()->all();
        
        // Validate webhook authenticity
        if (!$this->validateWatsonWebhook($request)) {
            return response()->json(['error' => 'Invalid signature'], 401);
        }
        
        $jobId = $payload['id'];
        $status = $payload['status'];
        
        if ($status === 'completed') {
            // Fetch full results
            $results = $this->watsonService->getTranscriptionResult($jobId);
            
            // Process and store transcript
            $this->processAndStoreTranscript($jobId, $results);
            
            // Trigger sentiment analysis if enabled
            if (config('watson.natural_language_understanding.features.sentiment')) {
                $this->queueSentimentAnalysis($jobId, $results);
            }
        } elseif ($status === 'failed') {
            $this->handleTranscriptionFailure($jobId, $payload['error']);
        }
        
        return response()->json(['status' => 'received']);
    }
}
```

### JavaScript Transcript Visualization

```javascript
// resources/js/components/TranscriptViewer.js

class WatsonTranscriptViewer {
    constructor(containerId, transcriptData) {
        this.container = document.getElementById(containerId);
        this.transcript = transcriptData;
        this.currentTime = 0;
    }
    
    /**
     * Render the transcript with speaker labels and timestamps
     */
    render() {
        const html = this.transcript.utterances.map((utterance, index) => `
            <div class="utterance" 
                 data-start="${utterance.start_time}" 
                 data-end="${utterance.end_time}"
                 data-speaker="${utterance.speaker}">
                <div class="speaker-label speaker-${utterance.speaker}">
                    Speaker ${utterance.speaker}
                    <span class="timestamp">${this.formatTime(utterance.start_time)}</span>
                </div>
                <div class="utterance-text">
                    ${this.renderWords(utterance.words)}
                </div>
                <div class="confidence-bar" style="width: ${utterance.confidence * 100}%"></div>
            </div>
        `).join('');
        
        this.container.innerHTML = html;
        this.attachEventListeners();
    }
    
    /**
     * Render individual words with confidence indicators
     */
    renderWords(words) {
        return words.map(word => {
            const confidenceClass = word.confidence > 0.9 ? 'high' : 
                                    word.confidence > 0.7 ? 'medium' : 'low';
            return `<span class="word confidence-${confidenceClass}" 
                         data-start="${word.start_time}"
                         title="Confidence: ${(word.confidence * 100).toFixed(1)}%">
                ${word.text}
            </span>`;
        }).join(' ');
    }
    
    /**
     * Highlight current utterance during audio playback
     */
    syncWithAudio(audioElement) {
        audioElement.addEventListener('timeupdate', () => {
            const currentTime = audioElement.currentTime;
            this.highlightCurrentUtterance(currentTime);
        });
    }
    
    highlightCurrentUtterance(time) {
        const utterances = this.container.querySelectorAll('.utterance');
        utterances.forEach(el => {
            const start = parseFloat(el.dataset.start);
            const end = parseFloat(el.dataset.end);
            
            if (time >= start && time <= end) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

// Usage
const viewer = new WatsonTranscriptViewer('transcript-container', transcriptData);
viewer.render();
viewer.syncWithAudio(document.getElementById('audio-player'));
```

### Sentiment Analysis Integration

```php
<?php

use NBTelemetry\Providers\Watson\WatsonNLUService;

class SentimentAnalysisService
{
    private WatsonNLUService $nluService;
    
    public function analyzeTranscriptSentiment(string $transcript): array
    {
        $analysis = $this->nluService->analyze($transcript, [
            'features' => [
                'sentiment' => [
                    'document' => true,
                    'targets' => ['service', 'product', 'agent'],
                ],
                'emotion' => [
                    'document' => true,
                ],
                'keywords' => [
                    'limit' => 10,
                    'sentiment' => true,
                    'emotion' => true,
                ],
            ],
        ]);
        
        return [
            'overall_sentiment' => $analysis['sentiment']['document'],
            'emotions' => $analysis['emotion']['document']['emotion'],
            'keywords' => $analysis['keywords'],
            'satisfaction_score' => $this->calculateSatisfactionScore($analysis),
        ];
    }
    
    private function calculateSatisfactionScore(array $analysis): float
    {
        $sentiment = $analysis['sentiment']['document']['score'];
        $emotions = $analysis['emotion']['document']['emotion'];
        
        // Weighted calculation based on sentiment and emotions
        $positiveEmotions = $emotions['joy'];
        $negativeEmotions = ($emotions['anger'] + $emotions['sadness'] + $emotions['fear']) / 3;
        
        return round(
            (($sentiment + 1) / 2 * 0.5) + 
            ($positiveEmotions * 0.3) - 
            ($negativeEmotions * 0.2),
            2
        ) * 100;
    }
}
```

---

## Troubleshooting

### Common Issues and Solutions

#### Authentication Failures

**Symptom**: `401 Unauthorized` or `403 Forbidden` errors when calling Watson APIs.

**Causes and Solutions**:

```bash
# Verify your API key is correctly set
echo $WATSON_STT_API_KEY

# Test authentication directly with Watson
curl -X GET \
  -u "apikey:${WATSON_STT_API_KEY}" \
  "${WATSON_STT_URL}/v1/models"
```

**Common causes**:
- API key has been rotated or expired
- Incorrect service URL for your region
- Service instance has been deleted
- IP restrictions on the IBM Cloud account

**Resolution**:
```php
// Verify configuration in your application
$config = config('watson.speech_to_text');
Log::debug('Watson config check', [
    'url' => $config['url'],
    'api_key_set' => !empty($config['api_key']),
    'api_key_length' => strlen($config['api_key']),
]);
```

#### Audio Format Issues

**Symptom**: `400 Bad Request` with message "Audio format not supported"

**Supported formats**:
| Format | Content-Type | Notes |
|--------|-------------|-------|
| WAV | `audio/wav` | 16-bit PCM recommended |
| MP3 | `audio/mp3` | Good compression/quality balance |
| FLAC | `audio/flac` | Lossless, larger files |
| OGG | `audio/ogg` | Open format |
| WebM | `audio/webm` | Browser recordings |

**Solution**:
```php
<?php

class AudioPreprocessor
{
    /**
     * Convert audio to Watson-compatible format
     */
    public function prepareForWatson(string $inputPath): string
    {
        $outputPath = storage_path('temp/' . uniqid() . '.wav');
        
        // Use FFmpeg to convert to 16kHz mono WAV
        $command = sprintf(
            'ffmpeg -i %s -ar 16000 -ac 1 -acodec pcm_s16le %s',
            escapeshellarg($inputPath),
            escapeshellarg($outputPath)
        );
        
        exec($command, $output, $returnCode);
        
        if ($returnCode !== 0) {
            throw new AudioConversionException("FFmpeg conversion failed");
        }
        
        return $outputPath;
    }
}
```

#### Rate Limiting

**Symptom**: `429 Too Many Requests` errors

**Solution**:
```php
<?php

use NBTelemetry\Providers\Watson\WatsonRateLimiter;

class RateLimitedWatsonClient
{
    private WatsonRateLimiter $limiter;
    
    public function transcribe(string $audioUrl): array
    {
        return $this->limiter->execute(function() use ($audioUrl) {
            return $this->watsonClient->recognize($audioUrl);
        }, [
            'max_attempts' => 3,
            'backoff_strategy' => 'exponential',
            'initial_delay' => 1000,
            'max_delay' => 30000,
        ]);
    }
}
```

#### Speaker Diarization Not Working

**Symptom**: All text attributed to single speaker or `speaker_labels` array is empty

**Requirements for speaker labels**:
- Audio must be longer than 30 seconds
- Must have at least 2 distinct speakers
- Audio quality must be sufficient for speaker differentiation

**Debug steps**:
```php
// Verify speaker labels are enabled in request
$options = [
    'speaker_labels' => true,
    'model' => 'en-US_Telephony', // Telephony model works better for calls
];

// Check response structure
$result = $this->watsonService->transcribe($audioUrl, $options);
Log::debug('Watson response', [
    'has_speaker_labels' => isset($result['speaker_labels']),
    'speaker_count' => count(array_unique(array_column($result['speaker_labels'] ?? [], 'speaker'))),
]);
```

### Logging and Debugging

Enable detailed Watson logging:

```php
// config/logging.php
'channels' => [
    'watson' => [
        'driver' => 'daily',
        'path' => storage_path('logs/watson.log'),
        'level' => env('WATSON_LOG_LEVEL', 'debug'),
        'days' => 14,
    ],
],
```

```php
<?php

use Illuminate\Support\Facades\Log;

class WatsonDebugMiddleware
{
    public function handle($request, $next)
    {
        $startTime = microtime(true);
        
        Log::channel('watson')->debug('Watson API Request', [
            'endpoint' => $request->getUri(),
            'method' => $request->getMethod(),
            'headers' => $request->getHeaders(),
        ]);
        
        $response = $next($request);
        
        Log::channel('watson')->debug('Watson API Response', [
            'status' => $response->getStatusCode(),
            'duration_ms' => (microtime(true) - $startTime) * 1000,
            'body_size' => strlen($response->getBody()),
        ]);
        
        return $response;
    }
}
```

### Health Check Endpoint

Implement a health check for Watson connectivity:

```php
<?php

class WatsonHealthCheck
{
    public function check(): array
    {
        $checks = [];
        
        // Test Speech to Text
        try {
            $models = $this->watsonSTT->listModels();
            $checks['speech_to_text'] = [
                'status' => 'healthy',
                'available_models' => count($models),
            ];
        } catch (\Exception $e) {
            $checks['speech_to_text'] = [
                'status' => 'unhealthy',
                'error' => $e->getMessage(),
            ];
        }
        
        // Test NLU if configured
        if (config('watson.natural_language_understanding.api_key')) {
            try {
                $this->watsonNLU->analyze('test', ['features' => ['sentiment' => []]]);
                $checks['nlu'] = ['status' => 'healthy'];
            } catch (\Exception $e) {
                $checks['nlu'] = [
                    'status' => 'unhealthy',
                    'error' => $e->getMessage(),
                ];
            }
        }
        
        return $checks;
    }
}
```

### Performance Optimization Tips

1. **Use appropriate audio models**: Select `en-US_Telephony` for phone recordings
2. **Enable smart formatting**: Reduces post-processing needs
3. **Batch small recordings**: Combine short recordings to reduce API calls
4. **Cache transcriptions**: Store results to avoid re-processing
5. **Use async processing**: Queue transcription jobs for background processing

```php
// Queue configuration for Watson jobs
'watson_transcription' => [
    'driver' => 'redis',
    'connection' => 'default',
    'queue' => 'watson-transcription',
    'retry_after' => 600, // 10 minutes for long recordings
    'block_for' => 5,
],
```