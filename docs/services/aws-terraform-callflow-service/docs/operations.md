# Operations Guide

## aws-terraform-callflow-service

### Overview

This Operations Guide provides comprehensive information for operating, monitoring, and troubleshooting the Callflow Service deployed on AWS. The Callflow Service is a serverless application that stores and retrieves call flow events using API Gateway, Lambda functions, and S3 storage. This guide is intended for DevOps engineers, Site Reliability Engineers (SREs), and system administrators responsible for maintaining the service in production environments.

The service architecture consists of:
- **API Gateway**: REST API with OpenAPI 3.0 specification for incoming requests
- **Lambda Authorizer**: Authentication and authorization of API requests
- **Event Storer Lambda**: Processes and stores call flow events to S3
- **Event Retriever Lambda**: Retrieves stored events from S3
- **S3 Storage Backend**: Durable storage for call flow event data
- **CloudWatch**: Logging, metrics, alarms, and dashboards

---

## Monitoring Overview

### Key Metrics to Monitor

Effective monitoring of the Callflow Service requires tracking several categories of metrics:

| Category | Key Metrics | Importance |
|----------|-------------|------------|
| API Gateway | Request count, latency, 4XX/5XX errors | High |
| Lambda Functions | Invocations, errors, duration, throttles | High |
| S3 Storage | Bucket size, request metrics | Medium |
| Authorization | Auth failures, latency | High |
| Overall Health | End-to-end latency, success rate | Critical |

### Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CloudWatch Monitoring                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Metrics    │  │    Logs      │  │   Alarms     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │              CloudWatch Dashboard                 │          │
│  └──────────────────────────────────────────────────┘          │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────┐          │
│  │                SNS Notifications                  │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Health Check Endpoints

Regularly verify service health by checking:

```bash
# Check API Gateway health
curl -X GET "https://your-api-endpoint/health" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json"

# Expected response for healthy service
# HTTP 200 OK
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
```

---

## CloudWatch Dashboard

### Dashboard Overview

The Callflow Service includes a pre-configured CloudWatch dashboard that provides real-time visibility into service health and performance. The dashboard is automatically provisioned by the Terraform module.

### Dashboard Widgets

#### 1. API Gateway Metrics Widget

Displays the following metrics:
- **Total Requests**: Count of all API requests
- **4XX Errors**: Client-side errors (authentication, validation)
- **5XX Errors**: Server-side errors
- **Latency (p50, p90, p99)**: Response time percentiles

#### 2. Lambda Function Metrics Widget

Shows metrics for all three Lambda functions:

```json
{
  "widget_type": "metric",
  "metrics": [
    ["AWS/Lambda", "Invocations", "FunctionName", "callflow-event-storer"],
    ["AWS/Lambda", "Invocations", "FunctionName", "callflow-event-retriever"],
    ["AWS/Lambda", "Invocations", "FunctionName", "callflow-authorizer"],
    ["AWS/Lambda", "Errors", "FunctionName", "callflow-event-storer"],
    ["AWS/Lambda", "Duration", "FunctionName", "callflow-event-storer"]
  ],
  "period": 60,
  "stat": "Sum"
}
```

#### 3. S3 Storage Metrics Widget

Monitors storage utilization:
- Bucket size over time
- Number of objects
- Request metrics (GET/PUT operations)

#### 4. Error Rate Widget

Calculates and displays error rates:

```
Error Rate = (5XX Errors / Total Requests) × 100
```

### Accessing the Dashboard

1. Navigate to AWS CloudWatch Console
2. Select "Dashboards" from the left navigation
3. Choose the dashboard named: `callflow-service-dashboard-{environment}`

### Customizing the Dashboard

To add custom widgets via Terraform:

```hcl
# Add to your Terraform configuration
resource "aws_cloudwatch_dashboard" "custom" {
  dashboard_name = "callflow-service-custom-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "callflow-event-storer"]
          ]
          period = 300
          stat   = "Maximum"
          region = var.aws_region
          title  = "Concurrent Executions"
        }
      }
    ]
  })
}
```

---

## Alarms and Notifications

### Pre-Configured Alarms

The Terraform module deploys the following CloudWatch alarms:

| Alarm Name | Metric | Threshold | Period | Action |
|------------|--------|-----------|--------|--------|
| `callflow-high-error-rate` | 5XX Errors | > 5% | 5 min | SNS Alert |
| `callflow-high-latency` | p99 Latency | > 3000ms | 5 min | SNS Alert |
| `callflow-lambda-errors` | Lambda Errors | > 10 | 5 min | SNS Alert |
| `callflow-lambda-throttles` | Lambda Throttles | > 0 | 1 min | SNS Alert |
| `callflow-auth-failures` | Auth 403 | > 50 | 5 min | SNS Alert |

### Alarm Configuration Details

#### High Error Rate Alarm

```hcl
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "callflow-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "This alarm monitors API Gateway 5XX errors"
  
  dimensions = {
    ApiName = "callflow-api"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}
```

#### Lambda Duration Alarm

```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "callflow-lambda-high-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p99"
  threshold           = 5000  # 5 seconds
  alarm_description   = "Lambda execution time exceeds threshold"
  
  dimensions = {
    FunctionName = "callflow-event-storer"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### Setting Up SNS Notifications

Configure SNS to receive alarm notifications:

```bash
# Subscribe email to SNS topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:callflow-alerts \
  --protocol email \
  --notification-endpoint ops-team@company.com

# Subscribe to Slack via Lambda (requires additional Lambda setup)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:callflow-alerts \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:slack-notifier
```

### Creating Custom Alarms

```bash
# Create custom alarm via AWS CLI
aws cloudwatch put-metric-alarm \
  --alarm-name "callflow-custom-alarm" \
  --alarm-description "Custom alarm for specific use case" \
  --metric-name "Invocations" \
  --namespace "AWS/Lambda" \
  --statistic "Sum" \
  --period 300 \
  --threshold 1000 \
  --comparison-operator "GreaterThanThreshold" \
  --dimensions "Name=FunctionName,Value=callflow-event-storer" \
  --evaluation-periods 2 \
  --alarm-actions "arn:aws:sns:us-east-1:123456789012:callflow-alerts"
```

---

## Log Analysis

### Log Structure

All Lambda functions emit logs in JSON format for easy parsing and analysis. Logs are stored in CloudWatch Log Groups:

- `/aws/lambda/callflow-event-storer`
- `/aws/lambda/callflow-event-retriever`
- `/aws/lambda/callflow-authorizer`
- `/aws/apigateway/callflow-api`

### CloudWatch Logs Insights Queries

#### Query: Find All Errors in Last Hour

```sql
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

#### Query: Analyze Lambda Cold Starts

```sql
fields @timestamp, @message, @duration, @billedDuration, @memorySize, @maxMemoryUsed
| filter @type = "REPORT"
| filter @message like /Init Duration/
| stats count() as coldStarts by bin(1h)
| sort @timestamp desc
```

#### Query: Track Request Latency by Endpoint

```sql
fields @timestamp, @message
| filter @message like /requestId/
| parse @message '{"requestId":"*","endpoint":"*","latency":*,' as requestId, endpoint, latency
| stats avg(latency) as avgLatency, max(latency) as maxLatency, count() as requests by endpoint
| sort avgLatency desc
```

#### Query: Identify Authorization Failures

```sql
fields @timestamp, @message
| filter @message like /Authorization failed/
| parse @message '{"requestId":"*","clientIp":"*","reason":"*"}' as requestId, clientIp, reason
| stats count() as failures by reason
| sort failures desc
```

#### Query: Event Processing Summary

```sql
fields @timestamp, @message
| filter @message like /Event processed/
| parse @message '{"eventId":"*","processingTime":*,"status":"*"}' as eventId, processingTime, status
| stats count() as total, avg(processingTime) as avgTime by status
```

### Log Retention Configuration

Configure log retention to manage costs:

```hcl
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/callflow-event-storer"
  retention_in_days = 30
  
  tags = {
    Environment = var.environment
    Service     = "callflow"
  }
}
```

### Exporting Logs to S3

For long-term retention and analysis:

```bash
# Create export task
aws logs create-export-task \
  --task-name "callflow-logs-export" \
  --log-group-name "/aws/lambda/callflow-event-storer" \
  --from 1704067200000 \
  --to 1704153600000 \
  --destination "s3-bucket-for-logs" \
  --destination-prefix "callflow-logs/"
```

---

## Log Field Reference

### Standard Log Fields

All logs include the following standard fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO8601 | UTC timestamp of the log event | `2024-01-15T10:30:00.000Z` |
| `level` | String | Log level (INFO, WARN, ERROR, DEBUG) | `INFO` |
| `requestId` | UUID | Unique identifier for the request | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `functionName` | String | Name of the Lambda function | `callflow-event-storer` |
| `functionVersion` | String | Lambda function version | `$LATEST` |
| `awsRequestId` | UUID | AWS-assigned request ID | `12345678-1234-1234-1234-123456789012` |

### Event Storer Log Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `eventId` | UUID | Unique call flow event ID | `evt-123456789` |
| `eventType` | String | Type of call flow event | `CALL_STARTED` |
| `callId` | String | Associated call identifier | `call-abc123` |
| `s3Key` | String | S3 object key where event is stored | `events/2024/01/15/evt-123.json` |
| `s3Bucket` | String | S3 bucket name | `callflow-events-prod` |
| `processingTimeMs` | Number | Time to process event in milliseconds | `45` |
| `eventSize` | Number | Size of event payload in bytes | `1024` |

### Event Retriever Log Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `query` | Object | Query parameters for retrieval | `{"startDate": "2024-01-15"}` |
| `resultCount` | Number | Number of events returned | `50` |
| `queryTimeMs` | Number | Time to execute query in milliseconds | `120` |
| `s3ObjectsScanned` | Number | Number of S3 objects scanned | `100` |

### Authorizer Log Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `authResult` | String | Result of authorization | `ALLOW` or `DENY` |
| `principalId` | String | Identified principal | `user-123` |
| `tokenType` | String | Type of token used | `Bearer` |
| `authLatencyMs` | Number | Time for auth check in milliseconds | `15` |
| `failureReason` | String | Reason for auth failure (if applicable) | `TOKEN_EXPIRED` |

### Sample Log Entries

**Successful Event Storage:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "requestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "functionName": "callflow-event-storer",
  "message": "Event stored successfully",
  "eventId": "evt-123456789",
  "eventType": "CALL_STARTED",
  "callId": "call-abc123",
  "s3Key": "events/2024/01/15/evt-123456789.json",
  "s3Bucket": "callflow-events-prod",
  "processingTimeMs": 45,
  "eventSize": 1024
}
```

**Authorization Failure:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "WARN",
  "requestId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "functionName": "callflow-authorizer",
  "message": "Authorization failed",
  "authResult": "DENY",
  "tokenType": "Bearer",
  "failureReason": "TOKEN_EXPIRED",
  "clientIp": "192.168.1.100",
  "authLatencyMs": 8
}
```

---

## Common Issues and Solutions

### Issue 1: High Lambda Cold Start Latency

**Symptoms:**
- Intermittent high latency spikes
- First requests after idle period are slow
- p99 latency significantly higher than p50

**Diagnosis:**
```sql
-- CloudWatch Logs Insights query
fields @timestamp, @message
| filter @type = "REPORT"
| filter @message like /Init Duration/
| parse @message 'Init Duration: * ms' as initDuration
| stats avg(initDuration) as avgColdStart, max(initDuration) as maxColdStart
```

**Solutions:**

1. **Enable Provisioned Concurrency:**
```hcl
resource "aws_lambda_provisioned_concurrency_config" "event_storer" {
  function_name                     = aws_lambda_function.event_storer.function_name
  provisioned_concurrent_executions = 5
  qualifier                         = aws_lambda_function.event_storer.version
}
```

2. **Optimize Lambda Package Size:**
   - Remove unused dependencies
   - Use Lambda layers for common libraries
   - Enable tree shaking for JavaScript functions

3. **Implement Warming Strategy:**
```bash
# CloudWatch Events rule for warming
aws events put-rule \
  --name "callflow-lambda-warmer" \
  --schedule-expression "rate(5 minutes)"
```

### Issue 2: S3 Access Denied Errors

**Symptoms:**
- Lambda functions failing with `AccessDenied` errors
- Events not being stored or retrieved
- Error message: `An error occurred (AccessDenied) when calling the PutObject operation`

**Diagnosis:**
```bash
# Check Lambda execution role
aws iam get-role-policy \
  --role-name callflow-event-storer-role \
  --policy-name s3-access-policy
```

**Solutions:**

1. **Verify IAM Permissions:**
```hcl
resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "s3-access-policy"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.events.arn,
          "${aws_s3_bucket.events.arn}/*"
        ]
      }
    ]
  })
}
```

2. **Check S3 Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/callflow-event-storer-role"
      },
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::callflow-events-prod/*"
    }
  ]
}
```

### Issue 3: API Gateway 429 Too Many Requests

**Symptoms:**
- Clients receiving `429 Too Many Requests` responses
- Burst traffic causing request failures
- CloudWatch showing throttling metrics

**Diagnosis:**
```bash
# Check current throttling settings
aws apigateway get-stage \
  --rest-api-id abc123xyz \
  --stage-name prod
```

**Solutions:**

1. **Increase Throttling Limits:**
```hcl
resource "aws_api_gateway_method_settings" "settings" {
  rest_api_id = aws_api_gateway_rest_api.callflow.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  method_path = "*/*"
  
  settings {
    throttling_burst_limit = 500
    throttling_rate_limit  = 1000
  }
}
```

2. **Request Quota Increase:**
```bash
# Request service quota increase
aws service-quotas request-service-quota-increase \
  --service-code apigateway \
  --quota-code L-8A5B8E43 \
  --desired-value 10000
```

### Issue 4: Lambda Timeout Errors

**Symptoms:**
- Functions timing out before completion
- `Task timed out after X seconds` in logs
- Partial event processing

**Diagnosis:**
```sql
fields @timestamp, @message, @duration
| filter @message like /Task timed out/
| stats count() as timeouts by bin(1h)
```

**Solutions:**

1. **Increase Timeout Configuration:**
```hcl
resource "aws_lambda_function" "event_storer" {
  # ... other configuration
  timeout = 30  # Increase from default 3 seconds
  
  environment {
    variables = {
      S3_OPERATION_TIMEOUT = "25000"
    }
  }
}
```

2. **Optimize Function Code:**
   - Use connection pooling
   - Implement batch operations
   - Add pagination for large retrievals

### Issue 5: Authentication Token Expiration

**Symptoms:**
- Sudden increase in 401/403 errors
- Valid users unable to access API
- Auth failures in authorizer logs

**Solutions:**

1. **Implement Token Refresh:**
```javascript
// Client-side token refresh
async function refreshTokenIfNeeded(token) {
  const decoded = jwt.decode(token);
  const expirationBuffer = 300; // 5 minutes
  
  if (decoded.exp - Date.now()/1000 < expirationBuffer) {
    return await refreshToken();
  }
  return token;
}
```

2. **Configure Authorizer Caching:**
```hcl
resource "aws_api_gateway_authorizer" "lambda" {
  name                             = "callflow-authorizer"
  rest_api_id                      = aws_api_gateway_rest_api.callflow.id
  authorizer_uri                   = aws_lambda_function.authorizer.invoke_arn
  authorizer_result_ttl_in_seconds = 300  # Cache for 5 minutes
  type                             = "TOKEN"
}
```

---

## Performance Tuning

### Lambda Memory Configuration

Memory allocation directly impacts CPU allocation and performance:

| Memory (MB) | CPU Allocation | Use Case |
|-------------|----------------|----------|
| 128-256 | Minimal | Simple authorizer |
| 512-1024 | Moderate | Event processing |
| 1024-2048 | High | Complex queries |
| 2048+ | Maximum | Large data processing |

**Finding Optimal Memory:**

```python
# Use AWS Lambda Power Tuning
# https://github.com/alexcasalboni/aws-lambda-power-tuning

# Configuration
{
  "lambdaARN": "arn:aws:lambda:us-east-1:123456789012:function:callflow-event-storer",
  "powerValues": [128, 256, 512, 1024, 2048],
  "num": 50,
  "payload": {"test": "event"},
  "parallelInvocation": true,
  "strategy": "balanced"
}
```

### S3 Performance Optimization

1. **Use S3 Transfer Acceleration for Global Access:**
```hcl
resource "aws_s3_bucket" "events" {
  bucket = "callflow-events-prod"
  
  acceleration_status = "Enabled"
}
```

2. **Implement Intelligent Key Naming:**
```javascript
// Add randomness to prevent hot partitions
const generateS3Key = (eventId, timestamp) => {
  const hash = crypto.createHash('md5').update(eventId).digest('hex').substring(0, 4);
  const date = new Date(timestamp).toISOString().split('T')[0].replace(/-/g, '/');
  return `${hash}/events/${date}/${eventId}.json`;
};
```

3. **Enable S3 Byte-Range Fetches for Large Objects:**
```javascript
const getEventRange = async (key, start, end) => {
  const params = {
    Bucket: process.env.S3_BUCKET,
    Key: key,
    Range: `bytes=${start}-${end}`
  };
  return await s3.getObject(params).promise();
};
```

### API Gateway Optimization

1. **Enable Caching for Read Operations:**
```hcl
resource "aws_api_gateway_method_settings" "caching" {
  rest_api_id = aws_api_gateway_rest_api.callflow.id
  stage_name  = aws_api_gateway_stage.prod.stage_name
  method_path = "events/GET"
  
  settings {
    caching_enabled      = true
    cache_ttl_in_seconds = 300
  }
}
```

2. **Enable Compression:**
```hcl
resource "aws_api_gateway_rest_api" "callflow" {
  name = "callflow-api"
  
  minimum_compression_size = 1024  # Compress responses > 1KB
}
```

---

## Scaling Considerations

### Horizontal Scaling

Lambda functions scale automatically, but consider these limits:

| Component | Default Limit | Recommended Action |
|-----------|---------------|-------------------|
| Lambda Concurrent Executions | 1,000 | Request increase for production |
| API Gateway Requests/Second | 10,000 | Enable throttling, request increase |
| S3 PUT Requests | 3,500/prefix | Use randomized key prefixes |
| CloudWatch Logs Ingestion | 5 MB/sec | Enable log streaming |

### Capacity Planning

**Estimate Required Capacity:**

```python
# Capacity estimation formula
daily_events = estimated_calls_per_day * average_events_per_call
peak_events_per_second = daily_events / (8 * 3600) * peak_multiplier  # 8 business hours
required_lambda_concurrency = peak_events_per_second * average_duration_seconds
required_s3_storage_per_month = daily_events * 30 * average_event_size_kb / 1024 / 1024  # GB
```

### Multi-Region Deployment

For high availability and disaster recovery:

```hcl
# Primary region
module "callflow_primary" {
  source = "./modules/callflow-service"
  
  providers = {
    aws = aws.primary
  }
  
  environment = "prod"
  region      = "us-east-1"
  
  s3_replication_enabled = true
  replication_region     = "us-west-2"
}

# Secondary region
module "callflow_secondary" {
  source = "./modules/callflow-service"
  
  providers = {
    aws = aws.secondary
  }
  
  environment = "prod"
  region      = "us-west-2"
  
  is_replica = true
}
```

### Auto-Scaling Reserved Concurrency

```hcl
# Configure reserved concurrency based on expected load
resource "aws_lambda_function" "event_storer" {
  # ... other configuration
  
  reserved_concurrent_executions = 100  # Reserve capacity
}

# Use Application Auto Scaling for provisioned concurrency
resource "aws_appautoscaling_target" "lambda" {
  max_capacity       = 50
  min_capacity       = 5
  resource_id        = "function:${aws_lambda_function.event_storer.function_name}:${aws_lambda_alias.live.name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_policy" "lambda" {
  name               = "callflow-lambda-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.lambda.resource_id
  scalable_dimension = aws_appautoscaling_target.lambda.scalable_dimension
  service_namespace  = aws_appautoscaling_target.lambda.service_namespace
  
  target_tracking_scaling_policy_configuration {
    target_value = 0.7
    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
  }
}
```

### Cost Optimization During Scaling

1. **Use Savings Plans for Consistent Workloads:**
   - Commit to Lambda compute usage for up to 66% savings

2. **Implement S3 Lifecycle Policies:**
```hcl
resource "aws_s3_bucket_lifecycle_configuration" "events" {
  bucket = aws_s3_bucket.events.id
  
  rule {
    id     = "transition-to-ia"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}
```

3. **Optimize Log Retention:**
   - Set appropriate retention periods
   - Export to S3 for long-term storage at lower cost
   - Use CloudWatch Logs Insights instead of third-party tools

---

## Emergency Procedures

### Incident Response Checklist

1. **Immediate Actions:**
   - [ ] Check CloudWatch Dashboard for anomalies
   - [ ] Review active alarms in CloudWatch
   - [ ] Check Lambda error rates and throttles
   - [ ] Verify API Gateway is responding

2. **Diagnostic Commands:**
```bash
# Quick health check
aws lambda invoke \
  --function-name callflow-event-storer \
  --payload '{"test": true}' \
  response.json

# Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/callflow-event-storer \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000)
```

3. **Rollback Procedure:**
```bash
# Rollback to previous Lambda version
aws lambda update-alias \
  --function-name callflow-event-storer \
  --name live \
  --function-version 5  # Previous stable version
```

---

## Support and Escalation

For issues not covered in this guide:

1. **Level 1**: Check CloudWatch logs and dashboards
2. **Level 2**: Review AWS Health Dashboard for service issues
3. **Level 3**: Open AWS Support case with collected diagnostics
4. **Level 4**: Engage architecture team for design-level issues

**Useful AWS Support Resources:**
- AWS Service Health Dashboard: https://status.aws.amazon.com/
- AWS Support Center: https://console.aws.amazon.com/support/
- AWS Documentation: https://docs.aws.amazon.com/