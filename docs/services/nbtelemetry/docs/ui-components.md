# UI Components Reference

## Overview

The nbtelemetry service provides a comprehensive suite of JavaScript visualization components designed to display call transcripts, analytics data, and interactive media controls. These components enable developers to build rich, interactive interfaces for call analysis and transcript visualization within their applications.

The UI component library follows a modular architecture, allowing you to use individual components independently or combine them to create full-featured call analysis dashboards. All components are designed to integrate seamlessly with the nbtelemetry API endpoints and support real-time data updates.

### Component Architecture

The component library is built around several core principles:

- **Modular Design**: Each component is self-contained and can be used independently
- **Event-Driven Communication**: Components communicate through a custom event system
- **Responsive Layout**: All components adapt to container dimensions
- **Theming Support**: Consistent styling through CSS custom properties
- **Accessibility**: WCAG 2.1 AA compliance for all interactive elements

### Installation and Setup

Include the nbtelemetry UI library in your project:

```html
<!-- CSS Styles -->
<link rel="stylesheet" href="/assets/css/nbtelemetry-ui.css">

<!-- Core Library -->
<script src="/assets/js/nbtelemetry-core.js"></script>

<!-- Individual Components -->
<script src="/assets/js/components/transcript-display.js"></script>
<script src="/assets/js/components/analytics-charts.js"></script>
<script src="/assets/js/components/timeline-player.js"></script>
<script src="/assets/js/components/data-grid.js"></script>
```

Initialize the component system:

```javascript
// Initialize nbtelemetry UI
NBTelemetry.init({
    apiBaseUrl: '/api/v1',
    authToken: 'your-auth-token',
    theme: 'light',
    locale: 'en-US'
});
```

---

## Transcript Display Components

The transcript display components provide interactive visualization of call transcripts with speaker identification, timestamp synchronization, and keyword highlighting.

### TranscriptViewer

The primary component for displaying call transcripts with full interactivity.

```javascript
// Create a transcript viewer instance
const transcriptViewer = new NBTelemetry.TranscriptViewer({
    container: '#transcript-container',
    callId: 'call_12345',
    options: {
        showTimestamps: true,
        showSpeakerLabels: true,
        highlightKeywords: true,
        enableSearch: true,
        syncWithPlayer: true
    }
});

// Load transcript data
transcriptViewer.load().then(() => {
    console.log('Transcript loaded successfully');
});
```

#### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `showTimestamps` | boolean | `true` | Display timestamps for each utterance |
| `showSpeakerLabels` | boolean | `true` | Show speaker identification labels |
| `highlightKeywords` | boolean | `true` | Enable keyword highlighting from analytics |
| `enableSearch` | boolean | `true` | Enable full-text search within transcript |
| `syncWithPlayer` | boolean | `false` | Sync scroll position with audio player |
| `speakerColors` | object | `{}` | Custom colors for speaker identification |

#### Event Handlers

```javascript
// Handle utterance click events
transcriptViewer.on('utteranceClick', (event) => {
    console.log('Clicked utterance:', event.utteranceId);
    console.log('Timestamp:', event.timestamp);
    // Seek audio player to this position
    player.seekTo(event.timestamp);
});

// Handle search results
transcriptViewer.on('searchComplete', (results) => {
    console.log(`Found ${results.count} matches`);
});

// Handle speaker selection
transcriptViewer.on('speakerFilter', (speaker) => {
    console.log('Filtering by speaker:', speaker.name);
});
```

### TranscriptSegment

Individual transcript segments for custom layouts:

```javascript
// Render individual segments
const segment = new NBTelemetry.TranscriptSegment({
    speaker: 'Agent',
    text: 'Thank you for calling. How may I assist you today?',
    startTime: 0.5,
    endTime: 4.2,
    confidence: 0.95,
    sentiment: 'positive'
});

document.getElementById('segment-container').appendChild(segment.render());
```

### Keyword Highlighter

Highlight specific keywords or phrases within transcripts:

```javascript
// Initialize keyword highlighter
const highlighter = new NBTelemetry.KeywordHighlighter({
    keywords: ['complaint', 'refund', 'cancel'],
    categories: {
        'negative': ['complaint', 'problem', 'issue'],
        'action': ['refund', 'cancel', 'transfer']
    },
    colors: {
        'negative': '#ff6b6b',
        'action': '#4dabf7'
    }
});

// Apply to transcript viewer
transcriptViewer.setHighlighter(highlighter);
```

---

## Analytics Visualization

Analytics visualization components render insights derived from call analysis, including sentiment scores, talk time metrics, and topic detection.

### SentimentGraph

Display sentiment analysis over the duration of a call:

```javascript
const sentimentGraph = new NBTelemetry.SentimentGraph({
    container: '#sentiment-container',
    data: sentimentData,
    options: {
        showMovingAverage: true,
        windowSize: 5,
        colorScheme: {
            positive: '#40c057',
            neutral: '#868e96',
            negative: '#fa5252'
        },
        height: 200,
        interactive: true
    }
});

sentimentGraph.render();
```

#### Sentiment Data Format

```javascript
const sentimentData = {
    callId: 'call_12345',
    duration: 342.5,
    segments: [
        { start: 0, end: 15.2, score: 0.65, label: 'positive' },
        { start: 15.2, end: 45.8, score: 0.12, label: 'neutral' },
        { start: 45.8, end: 89.3, score: -0.45, label: 'negative' },
        // ... additional segments
    ],
    overallScore: 0.23,
    overallLabel: 'neutral'
};
```

### TopicBubbles

Visualize detected topics and their relative prominence:

```javascript
const topicBubbles = new NBTelemetry.TopicBubbles({
    container: '#topics-container',
    topics: [
        { name: 'Billing', count: 12, relevance: 0.85 },
        { name: 'Technical Support', count: 8, relevance: 0.72 },
        { name: 'Account Changes', count: 5, relevance: 0.45 }
    ],
    options: {
        maxBubbles: 10,
        minRelevance: 0.3,
        clickable: true
    }
});

topicBubbles.on('topicClick', (topic) => {
    // Filter transcript to show only utterances containing this topic
    transcriptViewer.filterByTopic(topic.name);
});
```

---

## Timeline and Player Controls

The timeline and player components provide synchronized audio/video playback with transcript highlighting and annotation capabilities.

### AudioPlayer

Full-featured audio player with waveform visualization:

```javascript
const audioPlayer = new NBTelemetry.AudioPlayer({
    container: '#player-container',
    audioUrl: '/api/v1/calls/call_12345/audio',
    options: {
        waveform: true,
        waveformColor: '#228be6',
        progressColor: '#1971c2',
        showSpeakerRegions: true,
        showSentimentOverlay: true,
        controls: ['play', 'pause', 'seek', 'volume', 'speed', 'download']
    }
});

// Load and render
audioPlayer.load().then(() => {
    // Player ready
});
```

### Timeline Component

Interactive timeline with markers and regions:

```javascript
const timeline = new NBTelemetry.Timeline({
    container: '#timeline-container',
    duration: 342.5,
    markers: [
        { time: 45.2, label: 'Customer Complaint', type: 'warning' },
        { time: 120.8, label: 'Resolution Offered', type: 'success' },
        { time: 280.5, label: 'Call Wrap-up', type: 'info' }
    ],
    regions: [
        { start: 0, end: 45, speaker: 'Agent', color: '#4dabf7' },
        { start: 45, end: 120, speaker: 'Customer', color: '#69db7c' }
    ]
});

// Sync with audio player
audioPlayer.on('timeUpdate', (time) => {
    timeline.setCurrentTime(time);
});

timeline.on('seek', (time) => {
    audioPlayer.seekTo(time);
});
```

### PlaybackControls

Standalone playback control widget:

```javascript
const controls = new NBTelemetry.PlaybackControls({
    container: '#controls-container',
    player: audioPlayer,
    options: {
        speedOptions: [0.5, 0.75, 1, 1.25, 1.5, 2],
        showTimeDisplay: true,
        showDuration: true,
        compactMode: false
    }
});
```

---

## Chart Components (Pie, Balance Bars, Tag Cloud)

### PieChart

Display distribution data such as talk time ratios:

```javascript
const talkTimePie = new NBTelemetry.PieChart({
    container: '#pie-container',
    data: [
        { label: 'Agent', value: 180, color: '#4dabf7' },
        { label: 'Customer', value: 145, color: '#69db7c' },
        { label: 'Silence', value: 17, color: '#dee2e6' }
    ],
    options: {
        title: 'Talk Time Distribution',
        showLegend: true,
        showPercentages: true,
        donut: true,
        donutWidth: 60,
        animation: true,
        animationDuration: 800
    }
});

talkTimePie.render();
```

### BalanceBar

Visualize comparative metrics between two parties:

```javascript
const balanceBar = new NBTelemetry.BalanceBar({
    container: '#balance-container',
    metrics: [
        {
            label: 'Talk Time',
            leftValue: 180,
            rightValue: 145,
            leftLabel: 'Agent',
            rightLabel: 'Customer'
        },
        {
            label: 'Questions Asked',
            leftValue: 12,
            rightValue: 8,
            leftLabel: 'Agent',
            rightLabel: 'Customer'
        },
        {
            label: 'Interruptions',
            leftValue: 2,
            rightValue: 5,
            leftLabel: 'Agent',
            rightLabel: 'Customer'
        }
    ],
    options: {
        leftColor: '#4dabf7',
        rightColor: '#69db7c',
        showValues: true,
        showPercentages: true,
        animated: true
    }
});
```

### TagCloud

Display keyword frequency as a weighted tag cloud:

```javascript
const tagCloud = new NBTelemetry.TagCloud({
    container: '#tagcloud-container',
    words: [
        { text: 'billing', weight: 15 },
        { text: 'payment', weight: 12 },
        { text: 'invoice', weight: 10 },
        { text: 'refund', weight: 8 },
        { text: 'account', weight: 7 },
        { text: 'support', weight: 6 }
    ],
    options: {
        minFontSize: 12,
        maxFontSize: 48,
        colorRange: ['#74c0fc', '#1864ab'],
        shape: 'rectangular',
        clickable: true,
        rotationRange: [-15, 15]
    }
});

tagCloud.on('wordClick', (word) => {
    // Search transcript for this word
    transcriptViewer.search(word.text);
});
```

---

## Grid and Data Display

### DataGrid

Display tabular data with sorting, filtering, and pagination:

```javascript
const callsGrid = new NBTelemetry.DataGrid({
    container: '#grid-container',
    columns: [
        { field: 'callId', header: 'Call ID', width: 120, sortable: true },
        { field: 'date', header: 'Date', width: 150, sortable: true, type: 'date' },
        { field: 'duration', header: 'Duration', width: 100, sortable: true, type: 'duration' },
        { field: 'agent', header: 'Agent', width: 150, sortable: true, filterable: true },
        { field: 'sentiment', header: 'Sentiment', width: 120, type: 'sentiment' },
        { field: 'actions', header: 'Actions', width: 100, type: 'actions' }
    ],
    options: {
        pagination: true,
        pageSize: 25,
        pageSizeOptions: [10, 25, 50, 100],
        serverSide: true,
        apiEndpoint: '/api/v1/calls',
        selectable: true,
        selectMode: 'multiple',
        rowActions: [
            { icon: 'play', action: 'play', tooltip: 'Play Recording' },
            { icon: 'transcript', action: 'transcript', tooltip: 'View Transcript' },
            { icon: 'analytics', action: 'analytics', tooltip: 'View Analytics' }
        ]
    }
});

// Handle row actions
callsGrid.on('rowAction', (action, row) => {
    switch (action) {
        case 'play':
            openPlayer(row.callId);
            break;
        case 'transcript':
            openTranscript(row.callId);
            break;
        case 'analytics':
            openAnalytics(row.callId);
            break;
    }
});
```

### MetricsCard

Display key metrics in card format:

```javascript
const metricsCards = new NBTelemetry.MetricsCard({
    container: '#metrics-container',
    metrics: [
        {
            title: 'Total Calls',
            value: 1247,
            change: '+12%',
            changeDirection: 'up',
            icon: 'phone'
        },
        {
            title: 'Avg Duration',
            value: '4:32',
            change: '-8%',
            changeDirection: 'down',
            icon: 'clock'
        },
        {
            title: 'Positive Sentiment',
            value: '72%',
            change: '+5%',
            changeDirection: 'up',
            icon: 'smile'
        }
    ],
    layout: 'horizontal'
});
```

---

## Integration Guide

### Full Dashboard Example

Combine multiple components to create a comprehensive call analysis dashboard:

```javascript
// Initialize the nbtelemetry system
NBTelemetry.init({
    apiBaseUrl: '/api/v1',
    authToken: localStorage.getItem('auth_token'),
    theme: 'light'
});

// Create dashboard instance
const dashboard = new NBTelemetry.Dashboard({
    container: '#dashboard',
    callId: 'call_12345'
});

// Add components
dashboard.addComponent('transcript', new NBTelemetry.TranscriptViewer({
    container: '#transcript-panel',
    syncWithPlayer: true
}));

dashboard.addComponent('player', new NBTelemetry.AudioPlayer({
    container: '#player-panel',
    waveform: true
}));

dashboard.addComponent('sentiment', new NBTelemetry.SentimentGraph({
    container: '#sentiment-panel'
}));

dashboard.addComponent('talkTime', new NBTelemetry.PieChart({
    container: '#talktime-panel'
}));

// Load all data and render
dashboard.load().then(() => {
    console.log('Dashboard loaded');
});
```

### PHP Backend Integration

When using the components with the PHP backend:

```php
<?php
// In your controller
namespace App\Controllers;

use App\Services\TelemetryService;

class DashboardController
{
    public function getCallData($callId)
    {
        $service = new TelemetryService();
        
        return response()->json([
            'transcript' => $service->getTranscript($callId),
            'analytics' => $service->getAnalytics($callId),
            'audioUrl' => $service->getAudioUrl($callId)
        ]);
    }
}
```

### Error Handling

Implement comprehensive error handling:

```javascript
NBTelemetry.on('error', (error) => {
    console.error('NBTelemetry Error:', error);
    
    switch (error.code) {
        case 'AUTH_FAILED':
            // Redirect to login
            window.location.href = '/login';
            break;
        case 'NOT_FOUND':
            showNotification('Call not found', 'error');
            break;
        case 'TRANSCRIPTION_PENDING':
            showNotification('Transcription in progress...', 'info');
            break;
        default:
            showNotification('An error occurred', 'error');
    }
});
```

This completes the UI Components Reference for nbtelemetry. For additional support or to report issues, please consult the main documentation or contact the development team.