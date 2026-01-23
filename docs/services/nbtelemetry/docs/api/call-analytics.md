# Call Analytics API

The Call Analytics API provides comprehensive endpoints for accessing call recordings, transcriptions, and detailed analytics data. These endpoints enable integration with NLE providers (Watson, Google, VoiceBase) for advanced call analysis including talk time breakdowns, sentiment analysis, and transcript visualization.

## Base URL

```
https://api.natterbox.com
```

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/organisation/{orgid}/call` | Get all calls for an organisation |
| GET | `/v1/organisation/{orgid}/log/call` | Get call logs with filtering options |
| GET | `/v1/organisation/{orgid}/archive/recording/{uuid}` | Get a recording file |
| GET | `/v1/organisation/{orgid}/archive/recording/{uuid}/analytics` | Get analytics metadata |
| GET | `/v1/organisation/{orgid}/archive/recording/{uuid}/analytics/transcription` | Get transcription data |
| GET | `/v1/organisation/{orgid}/archive/recording/{uuid}/analytics/talkTime` | Get talk time analytics |
| GET | `{NATTERBOX_ARCHIVING_INDEX_URL}/{orgid}/{uuid}` | Direct AWS analytics access |

---

## Get All Calls

Retrieve all calls for a specific organisation.

```
GET /v1/organisation/{orgid}/call
```

### Description

Returns a list of all calls associated with the specified organisation. This endpoint provides high-level call metadata useful for building call history views and generating reports.

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |

### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-12345/call" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

### Response Example

```json
{
  "data": [
    {
      "id": "call-abc123",
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "direction": "inbound",
      "status": "completed",
      "from": "+44207123456",
      "to": "+44207654321",
      "startTime": "2024-01-15T10:30:00Z",
      "endTime": "2024-01-15T10:45:32Z",
      "duration": 932,
      "userId": "user-789",
      "hasRecording": true,
      "hasTranscription": true
    },
    {
      "id": "call-def456",
      "uuid": "660e8400-e29b-41d4-a716-446655440001",
      "direction": "outbound",
      "status": "completed",
      "from": "+44207654321",
      "to": "+44207999888",
      "startTime": "2024-01-15T11:00:00Z",
      "endTime": "2024-01-15T11:12:45Z",
      "duration": 765,
      "userId": "user-456",
      "hasRecording": true,
      "hasTranscription": false
    }
  ],
  "pagination": {
    "total": 1250,
    "page": 1,
    "pageSize": 50,
    "totalPages": 25
  }
}
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Unauthorized` | Invalid or expired access token |
| 403 | `Forbidden` | User does not have access to this organisation |
| 404 | `NotFound` | Organisation not found |
| 500 | `InternalServerError` | Server error occurred |

---

## Get Call Logs

Retrieve detailed call logs for an organisation with advanced filtering options.

```
GET /v1/organisation/{orgid}/log/call
```

### Description

Returns comprehensive call logs with support for filtering by date range, user, call direction, and other criteria. Ideal for generating detailed reports and auditing call activity.

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `startDate` | string (ISO 8601) | query | No | Filter calls starting from this date |
| `endDate` | string (ISO 8601) | query | No | Filter calls up to this date |
| `userId` | string | query | No | Filter calls by specific user ID |
| `direction` | string | query | No | Filter by call direction (`inbound`, `outbound`) |
| `status` | string | query | No | Filter by call status (`completed`, `missed`, `voicemail`) |
| `page` | integer | query | No | Page number for pagination (default: 1) |
| `pageSize` | integer | query | No | Number of records per page (default: 50, max: 100) |

### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-12345/log/call?startDate=2024-01-01T00:00:00Z&endDate=2024-01-31T23:59:59Z&direction=inbound&pageSize=25" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

### Response Example

```json
{
  "data": [
    {
      "id": "log-12345",
      "callId": "call-abc123",
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "direction": "inbound",
      "status": "completed",
      "from": {
        "number": "+44207123456",
        "displayName": "John Smith",
        "contactId": "contact-001"
      },
      "to": {
        "number": "+44207654321",
        "displayName": "Support Queue",
        "userId": "user-789"
      },
      "timestamps": {
        "initiated": "2024-01-15T10:29:55Z",
        "ringing": "2024-01-15T10:29:58Z",
        "answered": "2024-01-15T10:30:00Z",
        "ended": "2024-01-15T10:45:32Z"
      },
      "duration": {
        "total": 937,
        "ringing": 5,
        "talking": 932
      },
      "recording": {
        "available": true,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "duration": 932
      },
      "analytics": {
        "transcriptionAvailable": true,
        "sentimentAnalysed": true,
        "talkTimeAnalysed": true
      }
    }
  ],
  "pagination": {
    "total": 450,
    "page": 1,
    "pageSize": 25,
    "totalPages": 18
  },
  "summary": {
    "totalCalls": 450,
    "totalDuration": 125400,
    "averageDuration": 278
  }
}
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `BadRequest` | Invalid query parameters or date format |
| 401 | `Unauthorized` | Invalid or expired access token |
| 403 | `Forbidden` | User does not have access to this organisation |
| 404 | `NotFound` | Organisation not found |
| 500 | `InternalServerError` | Server error occurred |

---

## Get Recording

Retrieve a call recording file from the archive.

```
GET /v1/organisation/{orgid}/archive/recording/{uuid}
```

### Description

Downloads the audio recording file for a specific call. The recording is returned as an audio file (typically MP3 or WAV format). Requires appropriate permissions to access recordings.

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `uuid` | string (UUID) | path | Yes | The unique identifier of the recording |

### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-12345/archive/recording/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer {access_token}" \
  -o recording.mp3
```

### Response

The response is a binary audio file with appropriate content headers.

**Response Headers:**
```
Content-Type: audio/mpeg
Content-Disposition: attachment; filename="recording-550e8400.mp3"
Content-Length: 4521984
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Unauthorized` | Invalid or expired access token |
| 403 | `Forbidden` | User does not have permission to access this recording |
| 404 | `NotFound` | Recording not found or has been deleted |
| 410 | `Gone` | Recording has expired and been removed from archive |
| 500 | `InternalServerError` | Server error occurred |

---

## Get Analytics Metadata

Retrieve analytics index and metadata for a specific recording.

```
GET /v1/organisation/{orgid}/archive/recording/{uuid}/analytics
```

### Description

Returns the analytics index and metadata for a recording, including available analysis types, processing status, and summary information. Use this endpoint to check what analytics data is available before requesting specific analytics.

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `uuid` | string (UUID) | path | Yes | The unique identifier of the recording |

### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-12345/archive/recording/550e8400-e29b-41d4-a716-446655440000/analytics" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

### Response Example

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "organisationId": "org-12345",
  "status": "completed",
  "processedAt": "2024-01-15T10:50:00Z",
  "provider": "watson",
  "duration": 932,
  "language": "en-GB",
  "availableAnalytics": {
    "transcription": {
      "available": true,
      "status": "completed",
      "wordCount": 1847,
      "confidence": 0.94
    },
    "talkTime": {
      "available": true,
      "status": "completed",
      "speakers": 2
    },
    "sentiment": {
      "available": true,
      "status": "completed",
      "overallScore": 0.72
    },
    "keywords": {
      "available": true,
      "status": "completed",
      "keywordCount": 15
    }
  },
  "metadata": {
    "callId": "call-abc123",
    "direction": "inbound",
    "participants": [
      {
        "role": "agent",
        "userId": "user-789",
        "name": "Sarah Johnson"
      },
      {
        "role": "customer",
        "number": "+44207123456",
        "name": "John Smith"
      }
    ]
  }
}
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Unauthorized` | Invalid or expired access token |
| 403 | `Forbidden` | User does not have permission to access analytics |
| 404 | `NotFound` | Recording or analytics not found |
| 422 | `UnprocessableEntity` | Analytics processing failed or is not available |
| 500 | `InternalServerError` | Server error occurred |

---

## Get Transcription Analytics

Retrieve the full transcription and associated analytics for a recording.

```
GET /v1/organisation/{orgid}/archive/recording/{uuid}/analytics/transcription
```

### Description

Returns the complete transcription of a call recording, including speaker identification, timestamps, confidence scores, and optional sentiment annotations. Transcriptions are processed using configured NLE providers (Watson, Google, or VoiceBase).

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `uuid` | string (UUID) | path | Yes | The unique identifier of the recording |

### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-12345/archive/recording/550e8400-e29b-41d4-a716-446655440000/analytics/transcription" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

### Response Example

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "watson",
  "language": "en-GB",
  "duration": 932,
  "overallConfidence": 0.94,
  "wordCount": 1847,
  "transcript": {
    "fullText": "Hello, thank you for calling Acme Support. My name is Sarah, how can I help you today? Hi Sarah, I'm having an issue with my account...",
    "segments": [
      {
        "id": 1,
        "speaker": "agent",
        "speakerLabel": "Sarah Johnson",
        "startTime": 0.5,
        "endTime": 5.2,
        "text": "Hello, thank you for calling Acme Support. My name is Sarah, how can I help you today?",
        "confidence": 0.96,
        "sentiment": {
          "score": 0.8,
          "label": "positive"
        },
        "words": [
          {
            "word": "Hello",
            "startTime": 0.5,
            "endTime": 0.9,
            "confidence": 0.99
          },
          {
            "word": "thank",
            "startTime": 1.0,
            "endTime": 1.3,
            "confidence": 0.98
          }
        ]
      },
      {
        "id": 2,
        "speaker": "customer",
        "speakerLabel": "John Smith",
        "startTime": 5.8,
        "endTime": 12.4,
        "text": "Hi Sarah, I'm having an issue with my account. I can't seem to log in anymore.",
        "confidence": 0.92,
        "sentiment": {
          "score": -0.3,
          "label": "negative"
        }
      }
    ]
  },
  "keywords": [
    {
      "keyword": "account",
      "count": 8,
      "relevance": 0.95
    },
    {
      "keyword": "login",
      "count": 5,
      "relevance": 0.88
    },
    {
      "keyword": "password reset",
      "count": 3,
      "relevance": 0.82
    }
  ],
  "sentimentSummary": {
    "overall": 0.72,
    "trend": "improving",
    "agentAverage": 0.85,
    "customerAverage": 0.58,
    "segments": [
      {
        "timeRange": "0-300",
        "score": 0.45
      },
      {
        "timeRange": "300-600",
        "score": 0.75
      },
      {
        "timeRange": "600-932",
        "score": 0.95
      }
    ]
  }
}
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Unauthorized` | Invalid or expired access token |
| 403 | `Forbidden` | User does not have permission to access transcriptions |
| 404 | `NotFound` | Recording not found or transcription not available |
| 422 | `UnprocessableEntity` | Transcription processing failed |
| 503 | `ServiceUnavailable` | NLE provider temporarily unavailable |

---

## Get Talk Time Analytics

Retrieve talk time analysis and speaker statistics for a recording.

```
GET /v1/organisation/{orgid}/archive/recording/{uuid}/analytics/talkTime
```

### Description

Returns detailed talk time analytics including speaker breakdown, talk/listen ratios, overlap detection, and silence analysis. This data is essential for evaluating call quality and agent performance.

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `uuid` | string (UUID) | path | Yes | The unique identifier of the recording |

### Request Example

```bash
curl -X GET "https://api.natterbox.com/v1/organisation/org-12345/archive/recording/550e8400-e29b-41d4-a716-446655440000/analytics/talkTime" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

### Response Example

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "duration": 932,
  "totalTalkTime": 845,
  "totalSilence": 87,
  "speakers": [
    {
      "id": "speaker-1",
      "role": "agent",
      "label": "Sarah Johnson",
      "userId": "user-789",
      "metrics": {
        "talkTime": 380,
        "talkTimePercentage": 40.77,
        "averageSegmentLength": 12.5,
        "longestSegment": 45,
        "shortestSegment": 2,
        "segmentCount": 31,
        "wordsPerMinute": 142
      }
    },
    {
      "id": "speaker-2",
      "role": "customer",
      "label": "John Smith",
      "metrics": {
        "talkTime": 465,
        "talkTimePercentage": 49.89,
        "averageSegmentLength": 15.8,
        "longestSegment": 62,
        "shortestSegment": 3,
        "segmentCount": 29,
        "wordsPerMinute": 128
      }
    }
  ],
  "interaction": {
    "talkOverlap": {
      "totalTime": 23,
      "percentage": 2.47,
      "instances": 8
    },
    "silenceGaps": {
      "totalTime": 87,
      "percentage": 9.33,
      "averageLength": 2.9,
      "instances": 30,
      "longestGap": 8
    },
    "turnTaking": {
      "totalTurns": 60,
      "averageTurnLength": 14.1,
      "agentInitiatedTurns": 28,
      "customerInitiatedTurns": 32
    }
  },
  "timeline": [
    {
      "startTime": 0,
      "endTime": 60,
      "agentTalkTime": 25,
      "customerTalkTime": 30,
      "silence": 5
    },
    {
      "startTime": 60,
      "endTime": 120,
      "agentTalkTime": 22,
      "customerTalkTime": 33,
      "silence": 5
    }
  ],
  "qualityIndicators": {
    "listenToTalkRatio": 1.22,
    "deadAirPercentage": 9.33,
    "interruptionRate": 0.13,
    "averageResponseTime": 1.8
  }
}
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `Unauthorized` | Invalid or expired access token |
| 403 | `Forbidden` | User does not have permission to access talk time analytics |
| 404 | `NotFound` | Recording not found or talk time analysis not available |
| 422 | `UnprocessableEntity` | Talk time analysis processing failed |
| 500 | `InternalServerError` | Server error occurred |

---

## Get Analytics (AWS Direct)

Direct AWS API Gateway endpoint for retrieving analytics index data.

```
GET {NATTERBOX_ARCHIVING_INDEX_URL}/{orgid}/{uuid}
```

### Description

An alternative method for accessing analytics data directly through AWS API Gateway. This legacy endpoint may offer better performance for high-volume analytics retrieval. The base URL is configured via the `NATTERBOX_ARCHIVING_INDEX_URL` environment variable.

### Request Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `orgid` | string | path | Yes | The unique identifier of the organisation |
| `uuid` | string (UUID) | path | Yes | The unique identifier of the recording |

### Request Example

```bash
curl -X GET "https://archiving.natterbox.aws.com/org-12345/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer {access_token}" \
  -H "x-api-key: {aws_api_key}" \
  -H "Content-Type: application/json"
```

### Response Example

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "orgId": "org-12345",
  "indexedAt": "2024-01-15T10:48:00Z",
  "status": "indexed",
  "storage": {
    "bucket": "natterbox-recordings-eu-west-1",
    "key": "org-12345/2024/01/15/550e8400-e29b-41d4-a716-446655440000.mp3",
    "size": 4521984,
    "contentType": "audio/mpeg"
  },
  "analytics": {
    "transcriptionKey": "org-12345/analytics/550e8400/transcription.json",
    "talkTimeKey": "org-12345/analytics/550e8400/talktime.json",
    "sentimentKey": "org-12345/analytics/550e8400/sentiment.json"
  },
  "metadata": {
    "duration": 932,
    "channels": 2,
    "sampleRate": 44100,
    "bitRate": 128000
  },
  "retention": {
    "policy": "standard",
    "expiresAt": "2025-01-15T10:48:00Z"
  }
}
```

### Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `BadRequest` | Invalid organisation ID or UUID format |
| 401 | `Unauthorized` | Invalid or missing API key |
| 403 | `Forbidden` | Access denied to this resource |
| 404 | `NotFound` | Index entry not found |
| 500 | `InternalServerError` | AWS service error |

---

## Data Models

### Call Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique call identifier |
| `uuid` | string | UUID for recording reference |
| `direction` | string | Call direction (`inbound`, `outbound`) |
| `status` | string | Call status (`completed`, `missed`, `voicemail`, `abandoned`) |
| `from` | string | Originating phone number |
| `to` | string | Destination phone number |
| `startTime` | string (ISO 8601) | Call start timestamp |
| `endTime` | string (ISO 8601) | Call end timestamp |
| `duration` | integer | Call duration in seconds |
| `userId` | string | Associated user ID |
| `hasRecording` | boolean | Whether recording is available |
| `hasTranscription` | boolean | Whether transcription is available |

### Transcription Segment Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Segment sequence number |
| `speaker` | string | Speaker role (`agent`, `customer`) |
| `speakerLabel` | string | Human-readable speaker name |
| `startTime` | number | Segment start time in seconds |
| `endTime` | number | Segment end time in seconds |
| `text` | string | Transcribed text content |
| `confidence` | number | Confidence score (0-1) |
| `sentiment` | object | Sentiment analysis for segment |

### Talk Time Metrics Object

| Field | Type | Description |
|-------|------|-------------|
| `talkTime` | integer | Total talk time in seconds |
| `talkTimePercentage` | number | Percentage of call duration |
| `averageSegmentLength` | number | Average segment length in seconds |
| `longestSegment` | integer | Longest segment in seconds |
| `shortestSegment` | integer | Shortest segment in seconds |
| `segmentCount` | integer | Number of speech segments |
| `wordsPerMinute` | integer | Speaking rate |

---

## Related Documentation

- [Authentication](authentication.md) - OAuth2 authentication and token management
- [Users and Organizations](users-and-organizations.md) - User and organisation management
- [Configuration](configuration.md) - Dial plans, SIP devices, and availability profiles