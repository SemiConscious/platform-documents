# Google NLE Integration

## Overview

The Google NLE (Natural Language Engine) Integration is a core component of the nbtelemetry service that enables powerful speech-to-text transcription capabilities using Google Cloud Speech-to-Text API. This integration allows the telemetry service to process call recordings, convert audio to text, and prepare transcripts for further analysis including sentiment analysis and talk time calculations.

### Purpose

The Google Speech-to-Text integration serves as one of three NLE providers supported by nbtelemetry (alongside Watson and VoiceBase). It provides:

- **High-accuracy transcription**: Leverages Google's machine learning models for accurate speech recognition
- **Multi-language support**: Process calls in numerous languages and dialects
- **Speaker diarization**: Distinguish between multiple speakers in a conversation
- **Automatic punctuation**: Adds punctuation marks to transcripts automatically
- **Word-level timestamps**: Precise timing information for interactive transcript visualization

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    nbtelemetry Service                          │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ Call        │───▶│ NLE Router   │───▶│ Google Speech    │  │
│  │ Recording   │    │              │    │ Adapter          │  │
│  └─────────────┘    └──────────────┘    └────────┬─────────┘  │
│                                                   │            │
└───────────────────────────────────────────────────┼────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────┐
                                    │ Google Cloud Speech-to-   │
                                    │ Text API                  │
                                    └───────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| Synchronous Recognition | For short audio files (< 1 minute) |
| Asynchronous Recognition | For longer audio files with polling support |
| Streaming Recognition | Real-time transcription capability |
| Enhanced Models | Phone call and video optimized models |
| Profanity Filtering | Optional filtering of inappropriate content |

---

## Configuration

### Prerequisites

Before configuring the Google NLE integration, ensure you have:

1. A Google Cloud Platform (GCP) account with billing enabled
2. A project created in GCP Console
3. Speech-to-Text API enabled for your project
4. A service account with appropriate permissions
5. Service account credentials (JSON key file)

### Google Cloud Setup

#### Step 1: Enable the Speech-to-Text API

Navigate to the Google Cloud Console and enable the API:

```bash
# Using gcloud CLI
gcloud services enable speech.googleapis.com --project=YOUR_PROJECT_ID
```

#### Step 2: Create a Service Account

```bash
# Create the service account
gcloud iam service-accounts create nbtelemetry-speech \
    --description="Service account for nbtelemetry speech transcription" \
    --display-name="NBTelemetry Speech Service"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:nbtelemetry-speech@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/speech.client"

# Generate and download the key file
gcloud iam service-accounts keys create ~/nbtelemetry-google-credentials.json \
    --iam-account=nbtelemetry-speech@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Application Configuration

#### Environment Variables

Configure the following environment variables in your Docker deployment or `.env` file:

```bash
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id

# NLE Provider Settings
NLE_PROVIDER=google
NLE_GOOGLE_ENABLED=true
NLE_GOOGLE_LANGUAGE_CODE=en-US
NLE_GOOGLE_SAMPLE_RATE=8000
NLE_GOOGLE_ENCODING=LINEAR16

# Advanced Settings
NLE_GOOGLE_ENABLE_DIARIZATION=true
NLE_GOOGLE_DIARIZATION_SPEAKER_COUNT=2
NLE_GOOGLE_ENABLE_PUNCTUATION=true
NLE_GOOGLE_PROFANITY_FILTER=false
NLE_GOOGLE_MODEL=phone_call
```

#### PHP Configuration File

Create or update the Google NLE configuration in your PHP config:

```php
<?php
// config/nle/google.php

return [
    'google' => [
        'enabled' => env('NLE_GOOGLE_ENABLED', true),
        'credentials_path' => env('GOOGLE_APPLICATION_CREDENTIALS'),
        'project_id' => env('GOOGLE_CLOUD_PROJECT'),
        
        'recognition' => [
            'encoding' => env('NLE_GOOGLE_ENCODING', 'LINEAR16'),
            'sample_rate_hertz' => (int) env('NLE_GOOGLE_SAMPLE_RATE', 8000),
            'language_code' => env('NLE_GOOGLE_LANGUAGE_CODE', 'en-US'),
            'model' => env('NLE_GOOGLE_MODEL', 'phone_call'),
            'use_enhanced' => true,
        ],
        
        'features' => [
            'enable_automatic_punctuation' => env('NLE_GOOGLE_ENABLE_PUNCTUATION', true),
            'enable_speaker_diarization' => env('NLE_GOOGLE_ENABLE_DIARIZATION', true),
            'diarization_speaker_count' => (int) env('NLE_GOOGLE_DIARIZATION_SPEAKER_COUNT', 2),
            'profanity_filter' => env('NLE_GOOGLE_PROFANITY_FILTER', false),
            'enable_word_time_offsets' => true,
        ],
        
        'timeout' => [
            'connection' => 30,
            'operation' => 300,
        ],
        
        'retry' => [
            'max_attempts' => 3,
            'delay_ms' => 1000,
        ],
    ],
];
```

#### Docker Configuration

Update your `docker-compose.yml` to include the credentials volume:

```yaml
version: '3.8'

services:
  nbtelemetry:
    image: nbtelemetry:latest
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/secrets/google-credentials.json
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - NLE_PROVIDER=google
    volumes:
      - ./credentials/google-credentials.json:/secrets/google-credentials.json:ro
    secrets:
      - google_credentials

secrets:
  google_credentials:
    file: ./credentials/google-credentials.json
```

### Supported Audio Formats

| Format | Encoding Value | Sample Rate | Notes |
|--------|---------------|-------------|-------|
| WAV (Linear PCM) | LINEAR16 | 8000-48000 Hz | Recommended for best quality |
| FLAC | FLAC | 8000-48000 Hz | Good compression |
| MP3 | MP3 | 8000-48000 Hz | Requires beta API |
| OGG Opus | OGG_OPUS | 8000-48000 Hz | Efficient streaming |
| μ-law | MULAW | 8000 Hz | Common in telephony |

---

## Usage

### Basic Transcription Request

#### Using the API Endpoint

Send a POST request to initiate transcription:

```bash
curl -X POST "https://your-nbtelemetry-instance/api/v1/transcriptions" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "call_12345",
    "audio_url": "https://storage.example.com/recordings/call_12345.wav",
    "provider": "google",
    "options": {
      "language_code": "en-US",
      "enable_diarization": true,
      "speaker_count": 2
    }
  }'
```

#### PHP SDK Usage

```php
<?php

use NBTelemetry\NLE\GoogleSpeechAdapter;
use NBTelemetry\NLE\TranscriptionRequest;
use NBTelemetry\NLE\TranscriptionConfig;

// Initialize the Google Speech adapter
$googleAdapter = new GoogleSpeechAdapter([
    'credentials_path' => '/path/to/credentials.json',
    'project_id' => 'your-project-id',
]);

// Configure the transcription request
$config = new TranscriptionConfig([
    'language_code' => 'en-US',
    'enable_automatic_punctuation' => true,
    'enable_speaker_diarization' => true,
    'diarization_speaker_count' => 2,
    'model' => 'phone_call',
]);

// Create the request
$request = new TranscriptionRequest([
    'audio_uri' => 'gs://your-bucket/recordings/call_12345.wav',
    'config' => $config,
]);

// Execute transcription
try {
    $result = $googleAdapter->transcribe($request);
    
    // Access transcript data
    foreach ($result->getTranscriptSegments() as $segment) {
        echo sprintf(
            "[%s] Speaker %d: %s\n",
            $segment->getTimestamp(),
            $segment->getSpeakerId(),
            $segment->getText()
        );
    }
    
    // Get word-level timestamps for visualization
    $wordTimings = $result->getWordTimings();
    
} catch (\NBTelemetry\Exceptions\TranscriptionException $e) {
    error_log("Transcription failed: " . $e->getMessage());
}
```

### Asynchronous Long-Running Operations

For audio files longer than 1 minute, use asynchronous transcription:

```php
<?php

use NBTelemetry\NLE\GoogleSpeechAdapter;
use NBTelemetry\Jobs\ProcessTranscriptionJob;

// Submit for async processing
$operationId = $googleAdapter->submitAsyncTranscription($request);

// Store operation ID for polling
$transcription->update([
    'provider_operation_id' => $operationId,
    'status' => 'processing',
]);

// Poll for completion (typically done via scheduled job)
$status = $googleAdapter->checkOperationStatus($operationId);

if ($status->isDone()) {
    $result = $status->getResult();
    // Process results...
}
```

### JavaScript Integration for Transcript Visualization

```javascript
// Frontend integration for interactive transcript display
class GoogleTranscriptViewer {
    constructor(containerId, transcriptData) {
        this.container = document.getElementById(containerId);
        this.transcript = transcriptData;
        this.currentTime = 0;
    }
    
    render() {
        const html = this.transcript.segments.map(segment => `
            <div class="transcript-segment" 
                 data-start="${segment.start_time}" 
                 data-end="${segment.end_time}"
                 data-speaker="${segment.speaker_id}">
                <span class="speaker-label">Speaker ${segment.speaker_id}</span>
                <span class="timestamp">${this.formatTime(segment.start_time)}</span>
                <p class="transcript-text">${this.renderWords(segment.words)}</p>
            </div>
        `).join('');
        
        this.container.innerHTML = html;
        this.bindEvents();
    }
    
    renderWords(words) {
        return words.map(word => 
            `<span class="word" 
                   data-start="${word.start_time}" 
                   data-end="${word.end_time}">${word.text}</span>`
        ).join(' ');
    }
    
    highlightCurrentWord(currentTime) {
        this.container.querySelectorAll('.word').forEach(wordEl => {
            const start = parseFloat(wordEl.dataset.start);
            const end = parseFloat(wordEl.dataset.end);
            wordEl.classList.toggle('active', currentTime >= start && currentTime <= end);
        });
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
```

### Talk Time Analysis Integration

```php
<?php

use NBTelemetry\Analysis\TalkTimeAnalyzer;

// After transcription completes
$analyzer = new TalkTimeAnalyzer();
$talkTimeResults = $analyzer->analyze($transcriptionResult);

// Results include:
// - Total talk time per speaker
// - Talk time percentage
// - Interruption count
// - Silence duration
// - Average speaking pace (words per minute)

$report = [
    'call_id' => $callId,
    'total_duration' => $talkTimeResults->getTotalDuration(),
    'speakers' => array_map(function ($speaker) {
        return [
            'id' => $speaker->getId(),
            'talk_time' => $speaker->getTalkTime(),
            'percentage' => $speaker->getTalkTimePercentage(),
            'word_count' => $speaker->getWordCount(),
            'wpm' => $speaker->getWordsPerMinute(),
        ];
    }, $talkTimeResults->getSpeakers()),
    'interruptions' => $talkTimeResults->getInterruptionCount(),
    'total_silence' => $talkTimeResults->getTotalSilenceDuration(),
];
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Authentication Errors

**Symptoms:**
```
Error: Could not load the default credentials
Error: Permission denied on resource project
```

**Solutions:**

1. **Verify credentials file exists and is readable:**
```bash
# Check file permissions
ls -la /path/to/credentials.json

# Validate JSON format
cat /path/to/credentials.json | jq .
```

2. **Ensure environment variable is set correctly:**
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should output the full path to your credentials file
```

3. **Verify service account permissions:**
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --filter="bindings.members:nbtelemetry-speech@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

#### Issue: Quota Exceeded Errors

**Symptoms:**
```
Error: Quota exceeded for quota metric 'speech.googleapis.com/default_requests'
```

**Solutions:**

1. **Check current quota usage:**
```bash
gcloud services list --available --filter="speech"
```

2. **Implement request throttling:**
```php
<?php
// Add rate limiting to your transcription queue
$rateLimiter = new RateLimiter([
    'max_requests' => 300,
    'time_window' => 60, // per minute
]);

if (!$rateLimiter->allowRequest()) {
    throw new RateLimitException('Google Speech API rate limit reached');
}
```

3. **Request quota increase** in GCP Console if needed.

#### Issue: Audio Format Not Supported

**Symptoms:**
```
Error: Invalid audio encoding type
Error: Sample rate must be between 8000 and 48000
```

**Solutions:**

1. **Convert audio to supported format:**
```bash
# Convert to LINEAR16 WAV
ffmpeg -i input.mp3 -acodec pcm_s16le -ar 8000 -ac 1 output.wav
```

2. **Verify audio properties:**
```bash
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels input.wav
```

#### Issue: Transcription Quality Issues

**Symptoms:**
- Low accuracy transcriptions
- Missing words or phrases
- Incorrect speaker attribution

**Solutions:**

1. **Use the appropriate model:**
```php
// For phone calls, use the phone_call model
$config['model'] = 'phone_call';

// For video content
$config['model'] = 'video';

// Enable enhanced models for better accuracy
$config['use_enhanced'] = true;
```

2. **Provide speech context for domain-specific terms:**
```php
$config['speech_contexts'] = [
    [
        'phrases' => ['nbtelemetry', 'call analytics', 'sentiment score'],
        'boost' => 20,
    ],
];
```

3. **Ensure correct language code:**
```php
// Use specific dialect codes for better accuracy
$config['language_code'] = 'en-US'; // American English
$config['language_code'] = 'en-GB'; // British English
$config['language_code'] = 'es-MX'; // Mexican Spanish
```

### Debugging Tips

#### Enable Verbose Logging

```php
<?php
// config/logging.php
'channels' => [
    'google_speech' => [
        'driver' => 'daily',
        'path' => storage_path('logs/google-speech.log'),
        'level' => env('GOOGLE_SPEECH_LOG_LEVEL', 'debug'),
        'days' => 14,
    ],
],
```

#### Test Connection

```php
<?php
// Test script: test_google_connection.php

use Google\Cloud\Speech\V1\SpeechClient;

try {
    $client = new SpeechClient([
        'credentials' => '/path/to/credentials.json',
    ]);
    
    echo "✓ Successfully connected to Google Speech API\n";
    echo "Project ID: " . $client->getProjectId() . "\n";
    
} catch (\Exception $e) {
    echo "✗ Connection failed: " . $e->getMessage() . "\n";
    exit(1);
}
```

### Error Code Reference

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `INVALID_ARGUMENT` | Malformed request or invalid parameters | Check audio format and config values |
| `PERMISSION_DENIED` | Insufficient permissions | Verify service account IAM roles |
| `RESOURCE_EXHAUSTED` | Quota exceeded | Implement backoff or request quota increase |
| `DEADLINE_EXCEEDED` | Operation timed out | Increase timeout or use async API |
| `INTERNAL` | Google internal error | Retry with exponential backoff |
| `UNAVAILABLE` | Service temporarily unavailable | Implement retry logic |

### Health Check Endpoint

Monitor Google NLE integration health:

```bash
curl -X GET "https://your-nbtelemetry-instance/api/v1/health/nle/google" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

Expected response:
```json
{
    "status": "healthy",
    "provider": "google",
    "latency_ms": 245,
    "quota_remaining": 2847,
    "last_successful_request": "2024-01-15T10:30:00Z"
}
```

---

## Best Practices

1. **Always use GCS URIs** for audio files larger than 10MB to avoid upload timeouts
2. **Implement retry logic** with exponential backoff for transient errors
3. **Cache transcription results** to avoid redundant API calls
4. **Use webhooks** for async operation completion instead of polling when possible
5. **Monitor quota usage** proactively to avoid service interruptions
6. **Sanitize transcripts** before storing to comply with data privacy regulations