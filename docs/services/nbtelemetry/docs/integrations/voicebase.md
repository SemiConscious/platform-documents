# VoiceBase Integration

## Overview

VoiceBase is one of the core Natural Language Engine (NLE) providers integrated into the nbtelemetry service, offering advanced speech-to-text transcription and call analysis capabilities. This integration enables organizations to process call recordings, extract meaningful insights through sentiment analysis, and generate detailed transcripts with speaker diarization.

### What is VoiceBase?

VoiceBase is a cloud-based speech analytics platform that provides:

- **Automatic Speech Recognition (ASR)**: High-accuracy transcription of audio recordings
- **Speaker Separation**: Identification and labeling of different speakers in a conversation
- **Sentiment Analysis**: Detection of emotional tone and sentiment throughout conversations
- **Keyword Spotting**: Identification of specific terms and phrases
- **Analytics APIs**: Programmatic access to processed results

### Why Use VoiceBase with nbtelemetry?

The nbtelemetry service abstracts the complexity of working directly with VoiceBase APIs, providing:

1. **Unified Interface**: Consistent API patterns across Watson, Google, and VoiceBase providers
2. **Sapien Format Conversion**: Automatic conversion of VoiceBase results to the standardized Sapien format
3. **Talk Time Analysis**: Enhanced metrics beyond raw VoiceBase output
4. **Retry Logic and Error Handling**: Robust handling of API failures and rate limits
5. **Result Caching**: Efficient storage and retrieval of processed transcripts

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     nbtelemetry Service                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ API Layer   │───▶│ NLE Manager │───▶│ VoiceBase Provider  │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                │                 │
│                                                ▼                 │
│                           ┌─────────────────────────────────┐   │
│                           │    Sapien Format Converter      │   │
│                           └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   VoiceBase API     │
                              │   (External)        │
                              └─────────────────────┘
```

---

## Configuration

### Environment Variables

Configure the VoiceBase integration by setting the following environment variables in your deployment configuration:

```bash
# VoiceBase API Credentials
VOICEBASE_API_KEY=your_voicebase_api_key
VOICEBASE_API_SECRET=your_voicebase_api_secret

# VoiceBase API Endpoint (optional, defaults to production)
VOICEBASE_API_URL=https://apis.voicebase.com/v3

# VoiceBase Configuration Options
VOICEBASE_TIMEOUT=300
VOICEBASE_RETRY_ATTEMPTS=3
VOICEBASE_RETRY_DELAY=5

# Provider Selection
NLE_DEFAULT_PROVIDER=voicebase
```

### PHP Configuration

For PHP-based components, configure VoiceBase in your configuration file:

```php
<?php
// config/voicebase.php

return [
    'voicebase' => [
        'enabled' => env('VOICEBASE_ENABLED', true),
        'api_key' => env('VOICEBASE_API_KEY'),
        'api_secret' => env('VOICEBASE_API_SECRET'),
        'api_url' => env('VOICEBASE_API_URL', 'https://apis.voicebase.com/v3'),
        
        'options' => [
            'timeout' => env('VOICEBASE_TIMEOUT', 300),
            'retry_attempts' => env('VOICEBASE_RETRY_ATTEMPTS', 3),
            'retry_delay' => env('VOICEBASE_RETRY_DELAY', 5),
        ],
        
        'transcription' => [
            'language' => 'en-US',
            'enable_speaker_separation' => true,
            'enable_sentiment' => true,
            'enable_keywords' => true,
            'vocabulary' => [], // Custom vocabulary terms
        ],
        
        'callbacks' => [
            'enabled' => env('VOICEBASE_CALLBACKS_ENABLED', true),
            'url' => env('VOICEBASE_CALLBACK_URL'),
        ],
    ],
];
```

### JavaScript Configuration

For JavaScript UI components that interact with VoiceBase results:

```javascript
// config/voicebase.config.js

const voicebaseConfig = {
    provider: 'voicebase',
    
    // Display settings for transcript visualization
    visualization: {
        showSpeakerLabels: true,
        showTimestamps: true,
        showSentiment: true,
        sentimentColors: {
            positive: '#4CAF50',
            neutral: '#9E9E9E',
            negative: '#F44336'
        },
        highlightKeywords: true
    },
    
    // API endpoints
    endpoints: {
        submit: '/api/transcription/submit',
        status: '/api/transcription/status',
        results: '/api/transcription/results'
    }
};

export default voicebaseConfig;
```

### Docker Configuration

When deploying with Docker, include VoiceBase configuration in your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  nbtelemetry:
    build: .
    environment:
      - VOICEBASE_API_KEY=${VOICEBASE_API_KEY}
      - VOICEBASE_API_SECRET=${VOICEBASE_API_SECRET}
      - VOICEBASE_API_URL=https://apis.voicebase.com/v3
      - VOICEBASE_TIMEOUT=300
      - NLE_DEFAULT_PROVIDER=voicebase
    volumes:
      - ./config:/app/config
```

### Obtaining VoiceBase Credentials

1. **Create a VoiceBase Account**: Visit [VoiceBase Developer Portal](https://developer.voicebase.com)
2. **Generate API Keys**: Navigate to Settings → API Keys
3. **Select Appropriate Plan**: Ensure your plan supports required features (sentiment, speaker separation)
4. **Configure Callback URLs**: If using asynchronous processing, register your callback endpoint

---

## Analysis Features

### Transcription Processing

Submit audio files for transcription using the VoiceBase provider:

```php
<?php
// Example: Submitting a call recording for transcription

use App\Services\NLE\VoiceBaseProvider;
use App\Models\CallRecording;

class TranscriptionService
{
    protected $voicebaseProvider;
    
    public function __construct(VoiceBaseProvider $provider)
    {
        $this->voicebaseProvider = $provider;
    }
    
    public function processRecording(CallRecording $recording): array
    {
        // Configure transcription options
        $options = [
            'language' => 'en-US',
            'speakers' => [
                'enable' => true,
                'speakerCount' => 2  // Agent and customer
            ],
            'analytics' => [
                'sentiment' => true,
                'topics' => true
            ],
            'vocabulary' => [
                'terms' => $this->getCustomVocabulary($recording->organization_id)
            ]
        ];
        
        // Submit for processing
        $mediaId = $this->voicebaseProvider->submit(
            $recording->file_path,
            $options
        );
        
        // Store the media ID for later retrieval
        $recording->update([
            'voicebase_media_id' => $mediaId,
            'processing_status' => 'submitted'
        ]);
        
        return [
            'media_id' => $mediaId,
            'status' => 'submitted'
        ];
    }
    
    protected function getCustomVocabulary(int $organizationId): array
    {
        // Return organization-specific vocabulary terms
        return Organization::find($organizationId)
            ->vocabularyTerms()
            ->pluck('term')
            ->toArray();
    }
}
```

### Sentiment Analysis

VoiceBase provides segment-level sentiment analysis. The nbtelemetry service processes and aggregates this data:

```php
<?php
// Example: Processing sentiment analysis results

class SentimentAnalyzer
{
    public function analyzeSentiment(array $voicebaseResults): array
    {
        $segments = $voicebaseResults['media']['analytics']['sentiment'] ?? [];
        
        $analysis = [
            'overall_sentiment' => null,
            'agent_sentiment' => [],
            'customer_sentiment' => [],
            'sentiment_timeline' => [],
            'statistics' => [
                'positive_percentage' => 0,
                'negative_percentage' => 0,
                'neutral_percentage' => 0
            ]
        ];
        
        foreach ($segments as $segment) {
            $sentimentData = [
                'start_time' => $segment['s'],
                'end_time' => $segment['e'],
                'sentiment' => $segment['v'],
                'confidence' => $segment['c'] ?? null
            ];
            
            // Categorize by speaker
            if ($segment['speaker'] === 'agent') {
                $analysis['agent_sentiment'][] = $sentimentData;
            } else {
                $analysis['customer_sentiment'][] = $sentimentData;
            }
            
            $analysis['sentiment_timeline'][] = $sentimentData;
        }
        
        // Calculate statistics
        $analysis['statistics'] = $this->calculateStatistics(
            $analysis['sentiment_timeline']
        );
        
        $analysis['overall_sentiment'] = $this->determineOverallSentiment(
            $analysis['statistics']
        );
        
        return $analysis;
    }
    
    protected function calculateStatistics(array $timeline): array
    {
        $total = count($timeline);
        if ($total === 0) {
            return ['positive_percentage' => 0, 'negative_percentage' => 0, 'neutral_percentage' => 0];
        }
        
        $counts = ['positive' => 0, 'negative' => 0, 'neutral' => 0];
        
        foreach ($timeline as $segment) {
            $sentiment = $segment['sentiment'];
            if ($sentiment > 0.3) {
                $counts['positive']++;
            } elseif ($sentiment < -0.3) {
                $counts['negative']++;
            } else {
                $counts['neutral']++;
            }
        }
        
        return [
            'positive_percentage' => round(($counts['positive'] / $total) * 100, 2),
            'negative_percentage' => round(($counts['negative'] / $total) * 100, 2),
            'neutral_percentage' => round(($counts['neutral'] / $total) * 100, 2)
        ];
    }
}
```

### Talk Time Analysis

Calculate detailed talk time metrics from VoiceBase speaker separation data:

```php
<?php
// Example: Talk time analysis

class TalkTimeAnalyzer
{
    public function analyze(array $transcript): array
    {
        $speakers = [];
        $totalDuration = 0;
        $overlaps = [];
        $silences = [];
        
        $words = $transcript['media']['transcripts']['latest']['words'] ?? [];
        
        foreach ($words as $word) {
            $speakerId = $word['m'] ?? 'unknown';
            $startTime = $word['s'] / 1000; // Convert to seconds
            $endTime = $word['e'] / 1000;
            $duration = $endTime - $startTime;
            
            if (!isset($speakers[$speakerId])) {
                $speakers[$speakerId] = [
                    'total_time' => 0,
                    'word_count' => 0,
                    'segments' => []
                ];
            }
            
            $speakers[$speakerId]['total_time'] += $duration;
            $speakers[$speakerId]['word_count']++;
            
            $totalDuration = max($totalDuration, $endTime);
        }
        
        // Calculate percentages
        $analysis = [
            'total_duration' => $totalDuration,
            'speakers' => []
        ];
        
        foreach ($speakers as $speakerId => $data) {
            $analysis['speakers'][$speakerId] = [
                'talk_time' => round($data['total_time'], 2),
                'talk_percentage' => round(($data['total_time'] / $totalDuration) * 100, 2),
                'word_count' => $data['word_count'],
                'words_per_minute' => round(($data['word_count'] / $data['total_time']) * 60, 2)
            ];
        }
        
        // Detect silence periods
        $analysis['silence_time'] = $totalDuration - array_sum(
            array_column($speakers, 'total_time')
        );
        $analysis['silence_percentage'] = round(
            ($analysis['silence_time'] / $totalDuration) * 100, 2
        );
        
        return $analysis;
    }
}
```

### JavaScript Visualization

Display VoiceBase results in the interactive transcript viewer:

```javascript
// components/TranscriptViewer.js

class TranscriptViewer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            showSentiment: true,
            showTalkTime: true,
            ...options
        };
        this.transcript = null;
    }
    
    async loadTranscript(recordingId) {
        try {
            const response = await fetch(`/api/transcription/results/${recordingId}`);
            this.transcript = await response.json();
            this.render();
        } catch (error) {
            console.error('Failed to load transcript:', error);
            this.renderError(error);
        }
    }
    
    render() {
        if (!this.transcript) return;
        
        const html = `
            <div class="transcript-viewer">
                ${this.renderHeader()}
                ${this.renderTalkTimeChart()}
                ${this.renderTranscript()}
                ${this.renderSentimentTimeline()}
            </div>
        `;
        
        this.container.innerHTML = html;
        this.attachEventListeners();
    }
    
    renderTalkTimeChart() {
        const talkTime = this.transcript.talk_time_analysis;
        
        return `
            <div class="talk-time-chart">
                <h3>Talk Time Distribution</h3>
                <div class="chart-bars">
                    ${Object.entries(talkTime.speakers).map(([speaker, data]) => `
                        <div class="speaker-bar">
                            <span class="speaker-label">${this.formatSpeakerName(speaker)}</span>
                            <div class="bar" style="width: ${data.talk_percentage}%"></div>
                            <span class="percentage">${data.talk_percentage}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderTranscript() {
        const words = this.transcript.words || [];
        let currentSpeaker = null;
        let segments = [];
        let currentSegment = [];
        
        words.forEach(word => {
            if (word.speaker !== currentSpeaker) {
                if (currentSegment.length > 0) {
                    segments.push({
                        speaker: currentSpeaker,
                        words: currentSegment,
                        sentiment: this.getSegmentSentiment(currentSegment)
                    });
                }
                currentSpeaker = word.speaker;
                currentSegment = [];
            }
            currentSegment.push(word);
        });
        
        // Don't forget the last segment
        if (currentSegment.length > 0) {
            segments.push({
                speaker: currentSpeaker,
                words: currentSegment,
                sentiment: this.getSegmentSentiment(currentSegment)
            });
        }
        
        return `
            <div class="transcript-content">
                ${segments.map(segment => `
                    <div class="transcript-segment speaker-${segment.speaker}"
                         data-sentiment="${segment.sentiment}">
                        <div class="speaker-name">${this.formatSpeakerName(segment.speaker)}</div>
                        <div class="segment-text">
                            ${segment.words.map(w => `
                                <span class="word" 
                                      data-start="${w.start}" 
                                      data-end="${w.end}">${w.text}</span>
                            `).join(' ')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    formatSpeakerName(speakerId) {
        const speakerNames = {
            'S1': 'Agent',
            'S2': 'Customer',
            'agent': 'Agent',
            'customer': 'Customer'
        };
        return speakerNames[speakerId] || `Speaker ${speakerId}`;
    }
}

export default TranscriptViewer;
```

---

## Sapien Format Conversion

### Overview

The Sapien format is nbtelemetry's standardized transcript format that normalizes output from all NLE providers (VoiceBase, Watson, Google). This ensures consistent data structures regardless of the underlying provider.

### Sapien Format Structure

```json
{
    "version": "2.0",
    "provider": "voicebase",
    "recording_id": "rec_abc123",
    "duration": 342.5,
    "language": "en-US",
    "confidence": 0.94,
    "speakers": [
        {
            "id": "S1",
            "label": "Agent",
            "talk_time": 156.3,
            "talk_percentage": 45.6
        },
        {
            "id": "S2", 
            "label": "Customer",
            "talk_time": 142.8,
            "talk_percentage": 41.7
        }
    ],
    "segments": [
        {
            "id": "seg_001",
            "speaker_id": "S1",
            "start_time": 0.0,
            "end_time": 5.2,
            "text": "Thank you for calling support, how can I help you today?",
            "confidence": 0.96,
            "sentiment": {
                "score": 0.7,
                "label": "positive"
            },
            "words": [
                {
                    "text": "Thank",
                    "start": 0.0,
                    "end": 0.3,
                    "confidence": 0.98
                }
            ]
        }
    ],
    "analytics": {
        "sentiment": {
            "overall": 0.35,
            "by_speaker": {
                "S1": 0.65,
                "S2": 0.05
            }
        },
        "keywords": ["support", "account", "billing"],
        "topics": ["account_inquiry", "billing_question"]
    },
    "metadata": {
        "processed_at": "2024-01-15T10:30:00Z",
        "voicebase_media_id": "vb_xyz789"
    }
}
```

### Conversion Implementation

```php
<?php
// Services/SapienConverter.php

namespace App\Services;

class SapienConverter
{
    /**
     * Convert VoiceBase API response to Sapien format
     */
    public function fromVoiceBase(array $voicebaseResponse, string $recordingId): array
    {
        $media = $voicebaseResponse['media'] ?? [];
        $transcript = $media['transcripts']['latest'] ?? [];
        $analytics = $media['analytics'] ?? [];
        
        return [
            'version' => '2.0',
            'provider' => 'voicebase',
            'recording_id' => $recordingId,
            'duration' => $this->extractDuration($media),
            'language' => $transcript['language'] ?? 'en-US',
            'confidence' => $this->calculateOverallConfidence($transcript['words'] ?? []),
            'speakers' => $this->convertSpeakers($transcript, $analytics),
            'segments' => $this->convertSegments($transcript, $analytics),
            'analytics' => $this->convertAnalytics($analytics),
            'metadata' => [
                'processed_at' => now()->toIso8601String(),
                'voicebase_media_id' => $media['mediaId'] ?? null,
                'voicebase_status' => $media['status'] ?? null
            ]
        ];
    }
    
    protected function convertSegments(array $transcript, array $analytics): array
    {
        $words = $transcript['words'] ?? [];
        $sentiments = $this->indexSentimentsByTime($analytics['sentiment'] ?? []);
        
        $segments = [];
        $currentSegment = null;
        $segmentIndex = 0;
        
        foreach ($words as $word) {
            $speakerId = $this->normalizeSpeakerId($word['m'] ?? 'unknown');
            
            // Start new segment on speaker change
            if ($currentSegment === null || $currentSegment['speaker_id'] !== $speakerId) {
                if ($currentSegment !== null) {
                    $segments[] = $this->finalizeSegment($currentSegment);
                }
                
                $segmentIndex++;
                $currentSegment = [
                    'id' => 'seg_' . str_pad($segmentIndex, 3, '0', STR_PAD_LEFT),
                    'speaker_id' => $speakerId,
                    'start_time' => $word['s'] / 1000,
                    'end_time' => $word['e'] / 1000,
                    'words' => [],
                    'confidences' => []
                ];
            }
            
            // Add word to current segment
            $currentSegment['words'][] = [
                'text' => $word['w'],
                'start' => $word['s'] / 1000,
                'end' => $word['e'] / 1000,
                'confidence' => $word['c'] ?? null
            ];
            
            $currentSegment['end_time'] = $word['e'] / 1000;
            
            if (isset($word['c'])) {
                $currentSegment['confidences'][] = $word['c'];
            }
        }
        
        // Don't forget the last segment
        if ($currentSegment !== null) {
            $segments[] = $this->finalizeSegment($currentSegment);
        }
        
        // Add sentiment to segments
        return $this->addSentimentToSegments($segments, $sentiments);
    }
    
    protected function finalizeSegment(array $segment): array
    {
        $text = implode(' ', array_column($segment['words'], 'text'));
        $avgConfidence = !empty($segment['confidences']) 
            ? array_sum($segment['confidences']) / count($segment['confidences'])
            : null;
        
        return [
            'id' => $segment['id'],
            'speaker_id' => $segment['speaker_id'],
            'start_time' => $segment['start_time'],
            'end_time' => $segment['end_time'],
            'text' => $text,
            'confidence' => $avgConfidence ? round($avgConfidence, 4) : null,
            'words' => $segment['words']
        ];
    }
    
    protected function normalizeSpeakerId(string $voicebaseId): string
    {
        // VoiceBase uses various formats; normalize to S1, S2, etc.
        $mapping = [
            'Speaker 1' => 'S1',
            'Speaker 2' => 'S2',
            'agent' => 'S1',
            'customer' => 'S2'
        ];
        
        return $mapping[$voicebaseId] ?? $voicebaseId;
    }
    
    protected function convertAnalytics(array $analytics): array
    {
        return [
            'sentiment' => [
                'overall' => $this->calculateOverallSentiment($analytics['sentiment'] ?? []),
                'by_speaker' => $this->calculateSentimentBySpeaker($analytics['sentiment'] ?? [])
            ],
            'keywords' => $this->extractKeywords($analytics['keywords'] ?? []),
            'topics' => $this->extractTopics($analytics['topics'] ?? [])
        ];
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptoms**: 401 Unauthorized errors when submitting recordings

**Solutions**:
```php
// Verify credentials are properly set
if (empty(config('voicebase.api_key')) || empty(config('voicebase.api_secret'))) {
    throw new ConfigurationException('VoiceBase credentials not configured');
}

// Test authentication
$client = new VoiceBaseClient();
try {
    $client->testAuthentication();
} catch (AuthenticationException $e) {
    Log::error('VoiceBase authentication failed', [
        'error' => $e->getMessage()
    ]);
}
```

**Checklist**:
- [ ] Verify `VOICEBASE_API_KEY` environment variable is set
- [ ] Verify `VOICEBASE_API_SECRET` environment variable is set
- [ ] Ensure credentials are not expired
- [ ] Check for whitespace in credential values

#### 2. Transcription Timeouts

**Symptoms**: Jobs timing out before completion

**Solutions**:
```php
// Increase timeout for large files
$options = [
    'timeout' => 600, // 10 minutes for large files
    'async' => true,  // Use callbacks instead of polling
];

// Implement exponential backoff for status checks
$attempt = 0;
$maxAttempts = 10;
$baseDelay = 5;

while ($attempt < $maxAttempts) {
    $status = $this->voicebase->getStatus($mediaId);
    
    if ($status === 'finished') {
        return $this->voicebase->getResults($mediaId);
    }
    
    if ($status === 'failed') {
        throw new TranscriptionException('VoiceBase processing failed');
    }
    
    $delay = $baseDelay * pow(2, $attempt);
    sleep(min($delay, 60)); // Cap at 60 seconds
    $attempt++;
}
```

#### 3. Speaker Separation Issues

**Symptoms**: All text attributed to single speaker, incorrect speaker labels

**Solutions**:
```php
// Ensure speaker separation is enabled
$options = [
    'speakers' => [
        'enable' => true,
        'speakerCount' => 2,  // Specify expected number of speakers
        'model' => 'default'
    ]
];

// For stereo recordings, specify channel mapping
$options['channels'] = [
    [
        'speaker' => 'Agent',
        'channel' => 'left'
    ],
    [
        'speaker' => 'Customer', 
        'channel' => 'right'
    ]
];
```

#### 4. Missing Sentiment Data

**Symptoms**: Sentiment analysis returns empty results

**Checklist**:
- [ ] Verify sentiment is enabled in request options
- [ ] Ensure VoiceBase plan includes sentiment analysis
- [ ] Check that transcript has sufficient content for analysis

```php
// Debug sentiment configuration
$options = [
    'analytics' => [
        'sentiment' => [
            'enable' => true,
            'granularity' => 'turn'  // or 'word', 'segment'
        ]
    ]
];

// Log the full response for debugging
Log::debug('VoiceBase response', [
    'has_sentiment' => isset($response['media']['analytics']['sentiment']),
    'sentiment_count' => count($response['media']['analytics']['sentiment'] ?? [])
]);
```

### Error Reference

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `VB_AUTH_001` | Invalid API credentials | Verify API key and secret |
| `VB_MEDIA_001` | Unsupported media format | Convert to supported format (WAV, MP3, FLAC) |
| `VB_MEDIA_002` | File too large | Compress or split file (max 500MB) |
| `VB_PROC_001` | Processing failed | Check audio quality, retry submission |
| `VB_RATE_001` | Rate limit exceeded | Implement backoff, check quota |

### Logging and Debugging

Enable detailed logging for troubleshooting:

```php
// config/logging.php
'channels' => [
    'voicebase' => [
        'driver' => 'daily',
        'path' => storage_path('logs/voicebase.log'),
        'level' => env('VOICEBASE_LOG_LEVEL', 'debug'),
        'days' => 14,
    ],
],

// Usage in VoiceBase provider
Log::channel('voicebase')->info('Submitting recording', [
    'recording_id' => $recordingId,
    'file_size' => filesize($filePath),
    'options' => $options
]);
```

### Support Resources

- **VoiceBase Documentation**: https://developer.voicebase.com/docs
- **API Status Page**: https://status.voicebase.com
- **nbtelemetry Issues**: Contact your system administrator
- **Rate Limits**: Check your VoiceBase dashboard for current usage and limits