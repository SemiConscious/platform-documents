# Development Guide

## bedrock-metrics-aggregator

This comprehensive guide provides developers with everything needed to contribute to, extend, and maintain the bedrock-metrics-aggregator Lambda function. Whether you're adding new metrics, extending inference profile detection capabilities, or fixing bugs, this document will walk you through the development workflow, project architecture, and best practices.

---

## Local Development Setup

### Prerequisites

Before setting up your local development environment, ensure you have the following tools installed:

| Tool | Minimum Version | Purpose |
|------|-----------------|---------|
| Node.js | 18.x LTS | Runtime environment |
| npm | 9.x | Package management |
| AWS CLI | 2.x | AWS service interaction |
| AWS SAM CLI | 1.x | Local Lambda testing |
| Docker | 20.x | SAM local invocation |
| Git | 2.x | Version control |

### Environment Setup

1. **Clone the Repository**

```bash
git clone https://github.com/your-org/bedrock-metrics-aggregator.git
cd bedrock-metrics-aggregator
```

2. **Install Dependencies**

```bash
npm install
```

3. **Configure AWS Credentials**

Set up your AWS credentials for local development. We recommend using named profiles:

```bash
# ~/.aws/credentials
[bedrock-dev]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

# ~/.aws/config
[profile bedrock-dev]
region = us-east-1
output = json
```

4. **Set Up Environment Variables**

Create a `.env.local` file in the project root:

```bash
# .env.local
AWS_PROFILE=bedrock-dev
AWS_REGION=us-east-1
LOG_LEVEL=debug
CLOUDWATCH_NAMESPACE=Custom/BedrockMetrics
METRICS_PUBLISH_ENABLED=false  # Disable for local testing
```

5. **Verify Installation**

```bash
npm run verify-setup
```

### Local Lambda Invocation

Use AWS SAM CLI to test the Lambda function locally:

```bash
# Start local Lambda environment
sam local invoke BedrockMetricsAggregator \
  --event events/sample-s3-event.json \
  --env-vars env.json

# For continuous development with hot reload
sam local start-lambda --warm-containers EAGER
```

Create a sample test event in `events/sample-s3-event.json`:

```json
{
  "Records": [
    {
      "eventSource": "aws:sqs",
      "body": "{\"Records\":[{\"s3\":{\"bucket\":{\"name\":\"bedrock-logs-bucket\"},\"object\":{\"key\":\"logs/2024/01/15/invocation-log.json.gz\"}}}]}"
    }
  ]
}
```

---

## Project Structure

The bedrock-metrics-aggregator follows a modular architecture designed for maintainability and extensibility:

```
bedrock-metrics-aggregator/
├── src/
│   ├── index.js                    # Lambda handler entry point
│   ├── handlers/
│   │   ├── sqsHandler.js           # SQS event processing
│   │   └── s3Handler.js            # S3 object retrieval
│   ├── processors/
│   │   ├── logProcessor.js         # Bedrock log parsing
│   │   ├── inferenceProfileDetector.js  # Profile detection logic
│   │   └── tokenAggregator.js      # Token usage aggregation
│   ├── publishers/
│   │   ├── cloudwatchPublisher.js  # CloudWatch metrics publishing
│   │   └── metricsFormatter.js     # Metric data formatting
│   ├── models/
│   │   ├── BedrockInvocationLog.js
│   │   ├── InferenceProfile.js
│   │   ├── AggregatedMetrics.js
│   │   └── index.js
│   ├── utils/
│   │   ├── logger.js               # Structured logging
│   │   ├── gzipHandler.js          # Compressed log handling
│   │   └── validators.js           # Input validation
│   └── config/
│       ├── constants.js            # Application constants
│       └── inferenceProfiles.js    # Profile configurations
├── tests/
│   ├── unit/
│   │   ├── processors/
│   │   ├── publishers/
│   │   └── utils/
│   ├── integration/
│   │   └── e2e.test.js
│   └── fixtures/
│       └── sample-logs/
├── scripts/
│   ├── deploy.sh
│   └── generate-test-data.js
├── events/
│   └── sample-s3-event.json
├── template.yaml                   # SAM template
├── package.json
├── .eslintrc.js
├── .prettierrc
├── jest.config.js
└── README.md
```

### Key Components

#### Entry Point (`src/index.js`)

The Lambda handler orchestrates the entire processing pipeline:

```javascript
const { processSQSEvent } = require('./handlers/sqsHandler');
const { publishMetrics } = require('./publishers/cloudwatchPublisher');
const logger = require('./utils/logger');

exports.handler = async (event, context) => {
  logger.info('Processing Bedrock metrics aggregation', { 
    requestId: context.awsRequestId,
    recordCount: event.Records?.length 
  });

  try {
    const aggregatedMetrics = await processSQSEvent(event);
    await publishMetrics(aggregatedMetrics);
    
    return {
      statusCode: 200,
      body: JSON.stringify({ 
        processed: aggregatedMetrics.length,
        requestId: context.awsRequestId 
      })
    };
  } catch (error) {
    logger.error('Failed to process metrics', { error: error.message });
    throw error;
  }
};
```

#### Inference Profile Detector (`src/processors/inferenceProfileDetector.js`)

Handles detection and classification of Bedrock inference profiles:

```javascript
const { PROFILE_TYPES } = require('../config/constants');

class InferenceProfileDetector {
  static detect(modelId, region) {
    if (this.isCrossRegionProfile(modelId)) {
      return {
        type: PROFILE_TYPES.CROSS_REGION,
        sourceRegion: this.extractSourceRegion(modelId),
        targetRegion: region
      };
    }
    
    if (this.isGlobalCrossRegionProfile(modelId)) {
      return {
        type: PROFILE_TYPES.GLOBAL_CROSS_REGION,
        regions: this.extractGlobalRegions(modelId)
      };
    }
    
    return { type: PROFILE_TYPES.STANDARD };
  }
  
  // Additional methods...
}
```

---

## Running Tests

The project uses Jest as the testing framework with comprehensive unit and integration tests.

### Running All Tests

```bash
# Run all tests
npm test

# Run tests with coverage report
npm run test:coverage

# Run tests in watch mode during development
npm run test:watch
```

### Running Specific Test Suites

```bash
# Unit tests only
npm run test:unit

# Integration tests only
npm run test:integration

# Run tests for a specific file
npm test -- --testPathPattern=inferenceProfileDetector

# Run tests matching a pattern
npm test -- --testNamePattern="should detect cross-region"
```

### Test Structure

Unit tests follow the Arrange-Act-Assert pattern:

```javascript
// tests/unit/processors/inferenceProfileDetector.test.js
const InferenceProfileDetector = require('../../../src/processors/inferenceProfileDetector');

describe('InferenceProfileDetector', () => {
  describe('detect()', () => {
    it('should identify CrossRegion inference profiles', () => {
      // Arrange
      const modelId = 'arn:aws:bedrock:us-east-1:123456789:inference-profile/cross-region-anthropic-claude';
      const region = 'us-west-2';

      // Act
      const result = InferenceProfileDetector.detect(modelId, region);

      // Assert
      expect(result.type).toBe('CROSS_REGION');
      expect(result.sourceRegion).toBe('us-east-1');
      expect(result.targetRegion).toBe('us-west-2');
    });

    it('should identify GlobalCrossRegion inference profiles', () => {
      // Arrange
      const modelId = 'arn:aws:bedrock::123456789:inference-profile/global-anthropic-claude';
      
      // Act
      const result = InferenceProfileDetector.detect(modelId, 'eu-west-1');

      // Assert
      expect(result.type).toBe('GLOBAL_CROSS_REGION');
      expect(result.regions).toContain('us-east-1');
      expect(result.regions).toContain('eu-west-1');
    });
  });
});
```

### Test Coverage Requirements

Maintain minimum coverage thresholds:

| Metric | Minimum |
|--------|---------|
| Statements | 80% |
| Branches | 75% |
| Functions | 80% |
| Lines | 80% |

---

## Linting & Code Style

### ESLint Configuration

The project uses ESLint with the Airbnb base configuration:

```javascript
// .eslintrc.js
module.exports = {
  env: {
    node: true,
    es2021: true,
    jest: true,
  },
  extends: [
    'airbnb-base',
    'plugin:jest/recommended',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    'no-console': 'error',
    'max-len': ['error', { code: 120 }],
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'import/prefer-default-export': 'off',
  },
};
```

### Running Linting

```bash
# Check for linting errors
npm run lint

# Auto-fix fixable issues
npm run lint:fix

# Check specific files
npx eslint src/processors/*.js
```

### Prettier Configuration

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 120,
  "tabWidth": 2,
  "useTabs": false
}
```

### Pre-commit Hooks

The project uses Husky for pre-commit hooks:

```bash
# Install hooks
npm run prepare

# Hooks automatically run:
# - Linting on staged files
# - Unit tests for changed files
# - Commit message validation
```

---

## Adding New Metrics

When extending the metrics aggregator to publish new CloudWatch metrics, follow this structured approach:

### Step 1: Define the Metric

Add the metric definition to `src/config/constants.js`:

```javascript
// src/config/constants.js
const METRICS = {
  // Existing metrics
  INPUT_TOKENS: 'InputTokenCount',
  OUTPUT_TOKENS: 'OutputTokenCount',
  TOTAL_TOKENS: 'TotalTokenCount',
  
  // Add your new metric
  INVOCATION_LATENCY: 'InvocationLatencyMs',
  ERROR_COUNT: 'ErrorCount',
  THROTTLE_COUNT: 'ThrottleCount',
};

const METRIC_UNITS = {
  [METRICS.INPUT_TOKENS]: 'Count',
  [METRICS.OUTPUT_TOKENS]: 'Count',
  [METRICS.TOTAL_TOKENS]: 'Count',
  [METRICS.INVOCATION_LATENCY]: 'Milliseconds',
  [METRICS.ERROR_COUNT]: 'Count',
  [METRICS.THROTTLE_COUNT]: 'Count',
};

module.exports = { METRICS, METRIC_UNITS };
```

### Step 2: Create an Aggregator

Create or extend an aggregator in `src/processors/`:

```javascript
// src/processors/latencyAggregator.js
const { METRICS } = require('../config/constants');

class LatencyAggregator {
  constructor() {
    this.latencies = new Map();
  }

  aggregate(logs) {
    for (const log of logs) {
      const key = this.buildKey(log);
      const current = this.latencies.get(key) || { sum: 0, count: 0 };
      
      current.sum += log.latencyMs;
      current.count += 1;
      
      this.latencies.set(key, current);
    }
  }

  getMetrics() {
    const metrics = [];
    
    for (const [key, data] of this.latencies) {
      const { modelId, region, profileType } = this.parseKey(key);
      
      metrics.push({
        MetricName: METRICS.INVOCATION_LATENCY,
        Value: data.sum / data.count,
        Dimensions: [
          { Name: 'ModelId', Value: modelId },
          { Name: 'Region', Value: region },
          { Name: 'ProfileType', Value: profileType },
        ],
        Timestamp: new Date(),
        StorageResolution: 60,
      });
    }
    
    return metrics;
  }

  buildKey(log) {
    return `${log.modelId}|${log.region}|${log.profileType}`;
  }

  parseKey(key) {
    const [modelId, region, profileType] = key.split('|');
    return { modelId, region, profileType };
  }
}

module.exports = LatencyAggregator;
```

### Step 3: Integrate with Publisher

Update the CloudWatch publisher to include your new metrics:

```javascript
// src/publishers/cloudwatchPublisher.js
const LatencyAggregator = require('../processors/latencyAggregator');

async function publishMetrics(logs) {
  const tokenMetrics = tokenAggregator.getMetrics(logs);
  const latencyMetrics = new LatencyAggregator().aggregate(logs).getMetrics();
  
  const allMetrics = [...tokenMetrics, ...latencyMetrics];
  
  // Batch metrics (CloudWatch accepts max 1000 per request)
  const batches = chunk(allMetrics, 1000);
  
  for (const batch of batches) {
    await cloudwatch.putMetricData({
      Namespace: process.env.CLOUDWATCH_NAMESPACE,
      MetricData: batch,
    }).promise();
  }
}
```

### Step 4: Write Tests

```javascript
// tests/unit/processors/latencyAggregator.test.js
describe('LatencyAggregator', () => {
  it('should calculate average latency per model and region', () => {
    const aggregator = new LatencyAggregator();
    const logs = [
      { modelId: 'claude-v2', region: 'us-east-1', profileType: 'CROSS_REGION', latencyMs: 100 },
      { modelId: 'claude-v2', region: 'us-east-1', profileType: 'CROSS_REGION', latencyMs: 200 },
    ];

    aggregator.aggregate(logs);
    const metrics = aggregator.getMetrics();

    expect(metrics[0].Value).toBe(150);
  });
});
```

---

## Extending Inference Profile Detection

The inference profile detection system is designed for extensibility. Here's how to add support for new profile types:

### Step 1: Add Profile Type Constant

```javascript
// src/config/constants.js
const PROFILE_TYPES = {
  STANDARD: 'Standard',
  CROSS_REGION: 'CrossRegion',
  GLOBAL_CROSS_REGION: 'GlobalCrossRegion',
  // Add new profile type
  CUSTOM_ENDPOINT: 'CustomEndpoint',
};
```

### Step 2: Update Profile Configuration

```javascript
// src/config/inferenceProfiles.js
const PROFILE_PATTERNS = {
  CROSS_REGION: /inference-profile\/cross-region-/,
  GLOBAL_CROSS_REGION: /inference-profile\/global-/,
  // Add pattern for new profile type
  CUSTOM_ENDPOINT: /inference-profile\/custom-endpoint-/,
};

const PROFILE_REGION_MAPPINGS = {
  // Existing mappings...
  
  // Custom endpoint mappings
  'custom-endpoint-private': {
    type: 'CUSTOM_ENDPOINT',
    regions: ['us-east-1'],
    vpcEndpoint: true,
  },
};

module.exports = { PROFILE_PATTERNS, PROFILE_REGION_MAPPINGS };
```

### Step 3: Extend the Detector

```javascript
// src/processors/inferenceProfileDetector.js
class InferenceProfileDetector {
  static detect(modelId, region) {
    // Existing detection logic...
    
    if (this.isCustomEndpointProfile(modelId)) {
      return {
        type: PROFILE_TYPES.CUSTOM_ENDPOINT,
        region,
        vpcEndpoint: this.extractVpcEndpoint(modelId),
        customConfig: this.getCustomConfig(modelId),
      };
    }
    
    return { type: PROFILE_TYPES.STANDARD };
  }

  static isCustomEndpointProfile(modelId) {
    return PROFILE_PATTERNS.CUSTOM_ENDPOINT.test(modelId);
  }

  static extractVpcEndpoint(modelId) {
    // Implementation for extracting VPC endpoint information
    const match = modelId.match(/vpce-[a-z0-9]+/);
    return match ? match[0] : null;
  }

  static getCustomConfig(modelId) {
    const profileName = this.extractProfileName(modelId);
    return PROFILE_REGION_MAPPINGS[profileName] || {};
  }
}
```

### Step 4: Update Data Models

```javascript
// src/models/InferenceProfile.js
class InferenceProfile {
  constructor(data) {
    this.type = data.type;
    this.sourceRegion = data.sourceRegion;
    this.targetRegion = data.targetRegion;
    this.regions = data.regions || [];
    this.vpcEndpoint = data.vpcEndpoint || null;
    this.customConfig = data.customConfig || {};
  }

  isCustomEndpoint() {
    return this.type === PROFILE_TYPES.CUSTOM_ENDPOINT;
  }

  getDimensions() {
    const dimensions = [
      { Name: 'ProfileType', Value: this.type },
    ];

    if (this.isCustomEndpoint() && this.vpcEndpoint) {
      dimensions.push({ Name: 'VpcEndpoint', Value: this.vpcEndpoint });
    }

    return dimensions;
  }
}
```

---

## Contributing Guidelines

### Branch Naming Convention

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<ticket-id>-<description>` | `feature/BDRK-123-add-latency-metrics` |
| Bug Fix | `fix/<ticket-id>-<description>` | `fix/BDRK-456-token-aggregation-error` |
| Hotfix | `hotfix/<description>` | `hotfix/critical-memory-leak` |
| Refactor | `refactor/<description>` | `refactor/improve-profile-detection` |

### Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(metrics): add invocation latency metric

- Implement LatencyAggregator class
- Add average latency calculation per model/region
- Include new metric dimensions for profile type

Closes BDRK-789
```

### Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] All tests pass (`npm test`)
- [ ] Code coverage meets minimum thresholds
- [ ] Linting passes (`npm run lint`)
- [ ] Documentation is updated (if applicable)
- [ ] New metrics have corresponding tests
- [ ] Changes are backward compatible
- [ ] PR description clearly explains the changes
- [ ] Related issues are linked

### Code Review Process

1. **Submit PR** to `develop` branch
2. **Automated checks** run (lint, test, coverage)
3. **Code review** by at least 2 team members
4. **Address feedback** and update as needed
5. **Final approval** and merge
6. **Delete feature branch** after merge

### Release Process

```bash
# Create release branch
git checkout -b release/v1.2.0 develop

# Update version
npm version minor

# Run final tests
npm run test:all

# Merge to main
git checkout main
git merge release/v1.2.0

# Tag release
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

---

## Troubleshooting Common Development Issues

### Issue: Tests Fail with AWS Credential Errors

**Solution:** Ensure mocks are properly configured:

```javascript
// tests/setup.js
jest.mock('aws-sdk', () => ({
  CloudWatch: jest.fn(() => ({
    putMetricData: jest.fn().mockReturnValue({
      promise: jest.fn().mockResolvedValue({}),
    }),
  })),
  S3: jest.fn(() => ({
    getObject: jest.fn().mockReturnValue({
      promise: jest.fn().mockResolvedValue({ Body: Buffer.from('{}') }),
    }),
  })),
}));
```

### Issue: Local Lambda Invocation Timeout

**Solution:** Increase timeout in `template.yaml`:

```yaml
Globals:
  Function:
    Timeout: 300
    MemorySize: 512
```

### Issue: Memory Issues with Large Log Files

**Solution:** Use streaming for large files:

```javascript
const { pipeline } = require('stream/promises');
const zlib = require('zlib');

async function processLargeLog(s3Stream) {
  const gunzip = zlib.createGunzip();
  const processor = new LogStreamProcessor();
  
  await pipeline(s3Stream, gunzip, processor);
}
```

---

## Additional Resources

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [CloudWatch Custom Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html)
- [Bedrock Inference Profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [Jest Testing Framework](https://jestjs.io/docs/getting-started)

For questions or support, reach out to the Platform Engineering team on Slack: `#bedrock-metrics-support`