# EventBridge Health Check Lambda

## Overview

The EventBridge Health Check Lambda is a critical monitoring component of the CDC Pipeline service that continuously validates the health and availability of AWS EventBridge event bus connections. This function ensures that the CDC pipeline can reliably publish events to downstream consumers, such as the Wallboards service, by proactively detecting connectivity issues, permission problems, and event bus availability before they impact data flow.

In a Change Data Capture architecture where real-time event delivery is essential, the health check Lambda serves as an early warning system that can trigger alerts and automated remediation before downstream services experience data gaps or delays.

---

## Purpose

### Why EventBridge Health Checking Matters

The CDC Pipeline processes changes from 12+ CoreDB tables and publishes events to EventBridge for consumption by multiple downstream services. Any disruption in the EventBridge connection can result in:

- **Data Loss**: Events may fail to reach downstream consumers
- **Silent Failures**: Without health checks, EventBridge issues may go undetected
- **Cascading Failures**: Downstream services like Wallboards may display stale data
- **Debugging Complexity**: Root cause analysis becomes difficult without proactive monitoring

### Core Objectives

1. **Validate Event Bus Availability**: Confirm the target EventBridge event bus exists and is accessible
2. **Verify IAM Permissions**: Ensure the Lambda execution role has proper permissions to publish events
3. **Test End-to-End Connectivity**: Publish test events to validate the complete event flow
4. **Measure Latency**: Track EventBridge response times to detect performance degradation
5. **Report Health Status**: Provide standardized health check responses for monitoring systems

### Integration Points

The health check Lambda integrates with:

- **AWS EventBridge**: Primary target for health validation
- **Amazon CloudWatch**: Metrics and alarm publication
- **AWS Systems Manager Parameter Store**: Configuration retrieval
- **DynamoDB**: Health check history and state persistence

---

## Trigger Configuration

### CloudWatch Events Rule (Scheduled)

The health check Lambda is primarily triggered on a scheduled basis using CloudWatch Events (EventBridge Scheduler).

```yaml
# serverless.yml configuration
functions:
  eventBridgeHealthCheck:
    handler: src/handlers/healthCheck.handler
    name: ${self:service}-${self:provider.stage}-eventbridge-health-check
    description: Validates EventBridge connectivity for CDC Pipeline
    memorySize: 256
    timeout: 30
    events:
      - schedule:
          rate: rate(5 minutes)
          enabled: true
          input:
            checkType: "scheduled"
            includeLatencyTest: true
      - schedule:
          rate: rate(1 minute)
          enabled: ${self:custom.highFrequencyHealthCheck.${self:provider.stage}, false}
          input:
            checkType: "high-frequency"
            includeLatencyTest: false
```

### Manual Invocation

For on-demand health checks during deployments or incident response:

```typescript
// TypeScript - Manual invocation payload
interface HealthCheckInput {
  checkType: 'scheduled' | 'high-frequency' | 'manual' | 'deployment';
  includeLatencyTest: boolean;
  targetEventBus?: string;
  verbose?: boolean;
}

// Example invocation via AWS CLI
// aws lambda invoke --function-name cdc-pipeline-prod-eventbridge-health-check \
//   --payload '{"checkType":"manual","includeLatencyTest":true,"verbose":true}' \
//   response.json
```

### API Gateway Trigger (Optional)

For integration with external monitoring systems:

```yaml
# Additional trigger configuration
events:
  - http:
      path: /health/eventbridge
      method: get
      cors: true
      authorizer:
        type: AWS_IAM
```

### Environment Variables

```bash
# Required environment variables
EVENT_BUS_NAME=cdc-pipeline-events
EVENT_BUS_ARN=arn:aws:events:us-east-1:123456789012:event-bus/cdc-pipeline-events
HEALTH_CHECK_SOURCE=com.cdc-pipeline.health
HEALTH_CHECK_DETAIL_TYPE=HealthCheck
DDB_HEALTH_TABLE=cdc-pipeline-health-status
ALERT_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:cdc-pipeline-alerts
LATENCY_THRESHOLD_MS=500
```

---

## Health Check Logic

### Main Handler Implementation

```typescript
// src/handlers/healthCheck.ts
import { EventBridgeClient, PutEventsCommand, DescribeEventBusCommand } from '@aws-sdk/client-eventbridge';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { PublishCommand, SNSClient } from '@aws-sdk/client-sns';

interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: CheckResult[];
  latencyMs?: number;
  eventBusArn: string;
  executionDurationMs: number;
}

interface CheckResult {
  name: string;
  status: 'pass' | 'warn' | 'fail';
  message: string;
  duration?: number;
}

const eventBridgeClient = new EventBridgeClient({});
const ddbClient = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const snsClient = new SNSClient({});

export const handler = async (event: HealthCheckInput): Promise<HealthCheckResult> => {
  const startTime = Date.now();
  const checks: CheckResult[] = [];
  
  try {
    // Check 1: Verify Event Bus Exists
    const eventBusCheck = await checkEventBusExists();
    checks.push(eventBusCheck);
    
    // Check 2: Verify Permissions
    const permissionCheck = await checkPermissions();
    checks.push(permissionCheck);
    
    // Check 3: Test Event Publishing
    const publishCheck = await testEventPublishing();
    checks.push(publishCheck);
    
    // Check 4: Latency Test (if enabled)
    let latencyMs: number | undefined;
    if (event.includeLatencyTest) {
      const latencyCheck = await measurePublishLatency();
      checks.push(latencyCheck.check);
      latencyMs = latencyCheck.latencyMs;
    }
    
    // Determine overall status
    const overallStatus = determineOverallStatus(checks);
    
    const result: HealthCheckResult = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      checks,
      latencyMs,
      eventBusArn: process.env.EVENT_BUS_ARN!,
      executionDurationMs: Date.now() - startTime
    };
    
    // Persist health check result
    await persistHealthCheckResult(result);
    
    // Alert if unhealthy
    if (overallStatus === 'unhealthy') {
      await sendAlert(result);
    }
    
    return result;
    
  } catch (error) {
    const errorResult = handleHealthCheckError(error, startTime);
    await persistHealthCheckResult(errorResult);
    await sendAlert(errorResult);
    return errorResult;
  }
};
```

### Individual Health Check Functions

```typescript
// Check 1: Event Bus Existence
async function checkEventBusExists(): Promise<CheckResult> {
  const startTime = Date.now();
  
  try {
    const command = new DescribeEventBusCommand({
      Name: process.env.EVENT_BUS_NAME
    });
    
    const response = await eventBridgeClient.send(command);
    
    return {
      name: 'event_bus_exists',
      status: 'pass',
      message: `Event bus ${response.Name} is available`,
      duration: Date.now() - startTime
    };
  } catch (error: any) {
    if (error.name === 'ResourceNotFoundException') {
      return {
        name: 'event_bus_exists',
        status: 'fail',
        message: `Event bus ${process.env.EVENT_BUS_NAME} not found`,
        duration: Date.now() - startTime
      };
    }
    throw error;
  }
}

// Check 2: IAM Permissions
async function checkPermissions(): Promise<CheckResult> {
  const startTime = Date.now();
  
  try {
    // Attempt a dry-run style check by describing the event bus
    // Full permission validation happens during actual publish
    const command = new DescribeEventBusCommand({
      Name: process.env.EVENT_BUS_NAME
    });
    
    await eventBridgeClient.send(command);
    
    return {
      name: 'iam_permissions',
      status: 'pass',
      message: 'IAM permissions verified for EventBridge access',
      duration: Date.now() - startTime
    };
  } catch (error: any) {
    if (error.name === 'AccessDeniedException') {
      return {
        name: 'iam_permissions',
        status: 'fail',
        message: `Access denied: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
    throw error;
  }
}

// Check 3: Test Event Publishing
async function testEventPublishing(): Promise<CheckResult> {
  const startTime = Date.now();
  const healthCheckId = `health-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  try {
    const command = new PutEventsCommand({
      Entries: [{
        EventBusName: process.env.EVENT_BUS_NAME,
        Source: process.env.HEALTH_CHECK_SOURCE,
        DetailType: process.env.HEALTH_CHECK_DETAIL_TYPE,
        Detail: JSON.stringify({
          healthCheckId,
          timestamp: new Date().toISOString(),
          type: 'connectivity_test'
        })
      }]
    });
    
    const response = await eventBridgeClient.send(command);
    
    if (response.FailedEntryCount && response.FailedEntryCount > 0) {
      const failedEntry = response.Entries?.find(e => e.ErrorCode);
      return {
        name: 'event_publishing',
        status: 'fail',
        message: `Event publishing failed: ${failedEntry?.ErrorMessage}`,
        duration: Date.now() - startTime
      };
    }
    
    return {
      name: 'event_publishing',
      status: 'pass',
      message: `Test event ${healthCheckId} published successfully`,
      duration: Date.now() - startTime
    };
  } catch (error: any) {
    return {
      name: 'event_publishing',
      status: 'fail',
      message: `Event publishing error: ${error.message}`,
      duration: Date.now() - startTime
    };
  }
}

// Check 4: Latency Measurement
async function measurePublishLatency(): Promise<{ check: CheckResult; latencyMs: number }> {
  const iterations = 3;
  const latencies: number[] = [];
  
  for (let i = 0; i < iterations; i++) {
    const startTime = Date.now();
    
    const command = new PutEventsCommand({
      Entries: [{
        EventBusName: process.env.EVENT_BUS_NAME,
        Source: process.env.HEALTH_CHECK_SOURCE,
        DetailType: 'LatencyTest',
        Detail: JSON.stringify({
          iteration: i + 1,
          timestamp: new Date().toISOString()
        })
      }]
    });
    
    await eventBridgeClient.send(command);
    latencies.push(Date.now() - startTime);
  }
  
  const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
  const thresholdMs = parseInt(process.env.LATENCY_THRESHOLD_MS || '500');
  
  const status = avgLatency > thresholdMs * 2 ? 'fail' : avgLatency > thresholdMs ? 'warn' : 'pass';
  
  return {
    check: {
      name: 'publish_latency',
      status,
      message: `Average publish latency: ${avgLatency.toFixed(2)}ms (threshold: ${thresholdMs}ms)`,
      duration: avgLatency
    },
    latencyMs: avgLatency
  };
}
```

### Status Determination Logic

```typescript
function determineOverallStatus(checks: CheckResult[]): 'healthy' | 'degraded' | 'unhealthy' {
  const hasFailure = checks.some(c => c.status === 'fail');
  const hasWarning = checks.some(c => c.status === 'warn');
  
  if (hasFailure) return 'unhealthy';
  if (hasWarning) return 'degraded';
  return 'healthy';
}
```

---

## Response Format

### Successful Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": [
    {
      "name": "event_bus_exists",
      "status": "pass",
      "message": "Event bus cdc-pipeline-events is available",
      "duration": 45
    },
    {
      "name": "iam_permissions",
      "status": "pass",
      "message": "IAM permissions verified for EventBridge access",
      "duration": 12
    },
    {
      "name": "event_publishing",
      "status": "pass",
      "message": "Test event health-1705315800000-x7k9m2n published successfully",
      "duration": 78
    },
    {
      "name": "publish_latency",
      "status": "pass",
      "message": "Average publish latency: 82.33ms (threshold: 500ms)",
      "duration": 82.33
    }
  ],
  "latencyMs": 82.33,
  "eventBusArn": "arn:aws:events:us-east-1:123456789012:event-bus/cdc-pipeline-events",
  "executionDurationMs": 312
}
```

### Degraded Health Check Response

```json
{
  "status": "degraded",
  "timestamp": "2024-01-15T10:35:00.000Z",
  "checks": [
    {
      "name": "event_bus_exists",
      "status": "pass",
      "message": "Event bus cdc-pipeline-events is available",
      "duration": 52
    },
    {
      "name": "iam_permissions",
      "status": "pass",
      "message": "IAM permissions verified for EventBridge access",
      "duration": 15
    },
    {
      "name": "event_publishing",
      "status": "pass",
      "message": "Test event health-1705316100000-a3b4c5d published successfully",
      "duration": 156
    },
    {
      "name": "publish_latency",
      "status": "warn",
      "message": "Average publish latency: 623.67ms (threshold: 500ms)",
      "duration": 623.67
    }
  ],
  "latencyMs": 623.67,
  "eventBusArn": "arn:aws:events:us-east-1:123456789012:event-bus/cdc-pipeline-events",
  "executionDurationMs": 847
}
```

### Unhealthy Response

```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:40:00.000Z",
  "checks": [
    {
      "name": "event_bus_exists",
      "status": "pass",
      "message": "Event bus cdc-pipeline-events is available",
      "duration": 48
    },
    {
      "name": "iam_permissions",
      "status": "fail",
      "message": "Access denied: User is not authorized to perform events:PutEvents",
      "duration": 23
    },
    {
      "name": "event_publishing",
      "status": "fail",
      "message": "Event publishing error: Access denied",
      "duration": 0
    }
  ],
  "eventBusArn": "arn:aws:events:us-east-1:123456789012:event-bus/cdc-pipeline-events",
  "executionDurationMs": 71,
  "error": {
    "code": "ACCESS_DENIED",
    "message": "IAM permissions are insufficient for EventBridge operations"
  }
}
```

---

## Monitoring

### CloudWatch Metrics

The health check Lambda publishes custom metrics for comprehensive monitoring:

```typescript
// src/utils/metrics.ts
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

const cloudWatchClient = new CloudWatchClient({});

export async function publishHealthMetrics(result: HealthCheckResult): Promise<void> {
  const namespace = 'CDCPipeline/EventBridge';
  const timestamp = new Date();
  
  const metrics = [
    {
      MetricName: 'HealthCheckStatus',
      Value: result.status === 'healthy' ? 1 : result.status === 'degraded' ? 0.5 : 0,
      Unit: 'None',
      Timestamp: timestamp,
      Dimensions: [
        { Name: 'Environment', Value: process.env.STAGE || 'dev' },
        { Name: 'EventBus', Value: process.env.EVENT_BUS_NAME! }
      ]
    },
    {
      MetricName: 'PublishLatency',
      Value: result.latencyMs || 0,
      Unit: 'Milliseconds',
      Timestamp: timestamp,
      Dimensions: [
        { Name: 'Environment', Value: process.env.STAGE || 'dev' },
        { Name: 'EventBus', Value: process.env.EVENT_BUS_NAME! }
      ]
    },
    {
      MetricName: 'HealthCheckDuration',
      Value: result.executionDurationMs,
      Unit: 'Milliseconds',
      Timestamp: timestamp,
      Dimensions: [
        { Name: 'Environment', Value: process.env.STAGE || 'dev' }
      ]
    }
  ];
  
  // Add individual check metrics
  for (const check of result.checks) {
    metrics.push({
      MetricName: `Check_${check.name}`,
      Value: check.status === 'pass' ? 1 : check.status === 'warn' ? 0.5 : 0,
      Unit: 'None',
      Timestamp: timestamp,
      Dimensions: [
        { Name: 'Environment', Value: process.env.STAGE || 'dev' },
        { Name: 'CheckName', Value: check.name }
      ]
    });
  }
  
  const command = new PutMetricDataCommand({
    Namespace: namespace,
    MetricData: metrics
  });
  
  await cloudWatchClient.send(command);
}
```

### CloudWatch Alarms Configuration

```yaml
# CloudFormation/SAM template for alarms
Resources:
  EventBridgeHealthAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: ${self:service}-${self:provider.stage}-eventbridge-unhealthy
      AlarmDescription: EventBridge health check is failing
      MetricName: HealthCheckStatus
      Namespace: CDCPipeline/EventBridge
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 0.5
      ComparisonOperator: LessThanThreshold
      Dimensions:
        - Name: Environment
          Value: ${self:provider.stage}
        - Name: EventBus
          Value: ${self:custom.eventBusName}
      AlarmActions:
        - !Ref AlertSNSTopic
      OKActions:
        - !Ref AlertSNSTopic

  EventBridgeLatencyAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: ${self:service}-${self:provider.stage}-eventbridge-high-latency
      AlarmDescription: EventBridge publish latency is elevated
      MetricName: PublishLatency
      Namespace: CDCPipeline/EventBridge
      Statistic: Average
      Period: 300
      EvaluationPeriods: 3
      Threshold: 1000
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: Environment
          Value: ${self:provider.stage}
        - Name: EventBus
          Value: ${self:custom.eventBusName}
      AlarmActions:
        - !Ref AlertSNSTopic
```

### CloudWatch Dashboard Widget

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "EventBridge Health Status",
        "metrics": [
          ["CDCPipeline/EventBridge", "HealthCheckStatus", "Environment", "prod", "EventBus", "cdc-pipeline-events"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "yAxis": {
          "left": { "min": 0, "max": 1 }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "EventBridge Publish Latency",
        "metrics": [
          ["CDCPipeline/EventBridge", "PublishLatency", "Environment", "prod", "EventBus", "cdc-pipeline-events", { "stat": "Average" }],
          ["...", { "stat": "p99" }]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    }
  ]
}
```

### Log Insights Queries

```sql
-- Query for health check failures
fields @timestamp, @message
| filter @message like /status.*unhealthy/
| sort @timestamp desc
| limit 50

-- Query for latency trends
fields @timestamp, latencyMs
| filter @message like /HealthCheckResult/
| stats avg(latencyMs) as avgLatency, max(latencyMs) as maxLatency by bin(1h)
| sort @timestamp desc

-- Query for specific check failures
fields @timestamp, @message
| parse @message '"name":"*","status":"*","message":"*"' as checkName, checkStatus, checkMessage
| filter checkStatus = "fail"
| sort @timestamp desc
| limit 100
```

### Alerting and Notification

```typescript
// src/utils/alerting.ts
async function sendAlert(result: HealthCheckResult): Promise<void> {
  const message = {
    default: JSON.stringify(result, null, 2),
    email: formatEmailAlert(result),
    sms: `CDC Pipeline EventBridge Health: ${result.status.toUpperCase()}`,
    lambda: JSON.stringify(result)
  };
  
  const command = new PublishCommand({
    TopicArn: process.env.ALERT_SNS_TOPIC_ARN,
    Message: JSON.stringify(message),
    MessageStructure: 'json',
    Subject: `[${result.status.toUpperCase()}] CDC Pipeline EventBridge Health Check`,
    MessageAttributes: {
      severity: {
        DataType: 'String',
        StringValue: result.status === 'unhealthy' ? 'critical' : 'warning'
      }
    }
  });
  
  await snsClient.send(command);
}

function formatEmailAlert(result: HealthCheckResult): string {
  const failedChecks = result.checks.filter(c => c.status === 'fail');
  
  return `
CDC Pipeline EventBridge Health Check Alert

Status: ${result.status.toUpperCase()}
Timestamp: ${result.timestamp}
Event Bus: ${result.eventBusArn}

Failed Checks:
${failedChecks.map(c => `  - ${c.name}: ${c.message}`).join('\n')}

Full Results:
${JSON.stringify(result, null, 2)}
  `.trim();
}
```

---

## Best Practices

1. **Health Check Isolation**: Ensure health check events use a distinct `DetailType` to prevent them from being processed by production consumers
2. **Graceful Degradation**: Continue publishing CDC events even when health checks report degraded status
3. **Rate Limiting**: Avoid excessive health check frequency to prevent unnecessary EventBridge costs
4. **Correlation IDs**: Include unique identifiers in health check events for traceability
5. **Circuit Breaker Integration**: Use health check results to inform circuit breaker decisions in the main CDC processing logic

## Troubleshooting

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| `ResourceNotFoundException` | Event bus doesn't exist | Verify EVENT_BUS_NAME environment variable and event bus exists |
| `AccessDeniedException` | IAM permissions missing | Review Lambda execution role permissions for `events:PutEvents` |
| High latency warnings | Network issues or throttling | Check AWS Service Health Dashboard and EventBridge quotas |
| Intermittent failures | Cold starts or timeout | Increase Lambda memory or implement provisioned concurrency |