# Monitoring Configuration

## Overview

The `aws-terraform-bedrock` module provides comprehensive CloudWatch monitoring capabilities for AWS Bedrock models and inference profiles across multiple regions. This monitoring configuration enables operators to track model performance, detect anomalies, and ensure optimal operation of GenAI workloads.

Effective monitoring of Bedrock models is critical for:

- **Performance Optimization**: Track latency, throughput, and token consumption to optimize model selection and configuration
- **Cost Management**: Monitor invocation counts and token usage to control costs and forecast spending
- **Reliability**: Detect errors, throttling, and service degradation before they impact end users
- **Compliance**: Maintain audit trails and ensure guardrails are functioning correctly
- **Capacity Planning**: Understand usage patterns to plan for scaling and resource allocation

This documentation covers the complete monitoring setup for Bedrock models, including metrics collection, alarm configuration, dashboard creation, and procedures for adding monitoring to new models.

### Architecture Overview

The monitoring architecture follows AWS best practices for observability:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CloudWatch Monitoring                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Metrics    │  │    Alarms    │  │  Dashboards  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────┐       │
│  │              SNS Notification Topics                 │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  us-east-1    │  │  us-west-2    │  │  eu-west-1    │
│   Bedrock     │  │   Bedrock     │  │   Bedrock     │
│   Endpoint    │  │   Endpoint    │  │   Endpoint    │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Claude Sonnet v4.5 Monitoring

Claude Sonnet v4.5 (claude-sonnet-4-20250514) is a flagship model in the Bedrock deployment. Due to its widespread use and critical nature, it requires dedicated monitoring configuration.

### Model-Specific Metrics

Claude Sonnet v4.5 exposes several key metrics that should be monitored:

```hcl
# terraform/modules/bedrock-monitoring/claude_sonnet_v4.tf

locals {
  claude_sonnet_v4_model_id = "anthropic.claude-sonnet-4-20250514-v1:0"
  claude_sonnet_v4_regions  = ["us-east-1", "us-west-2", "eu-west-1"]
}

resource "aws_cloudwatch_metric_alarm" "claude_sonnet_v4_invocation_latency" {
  for_each = toset(local.claude_sonnet_v4_regions)

  alarm_name          = "bedrock-claude-sonnet-v4-latency-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "InvocationLatency"
  namespace           = "AWS/Bedrock"
  period              = 300
  statistic           = "Average"
  threshold           = 30000  # 30 seconds
  alarm_description   = "Claude Sonnet v4.5 invocation latency exceeds 30 seconds in ${each.key}"
  
  dimensions = {
    ModelId = local.claude_sonnet_v4_model_id
  }

  alarm_actions = [aws_sns_topic.bedrock_alerts[each.key].arn]
  ok_actions    = [aws_sns_topic.bedrock_alerts[each.key].arn]

  tags = {
    Model       = "claude-sonnet-v4"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "claude_sonnet_v4_error_rate" {
  for_each = toset(local.claude_sonnet_v4_regions)

  alarm_name          = "bedrock-claude-sonnet-v4-errors-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 5

  metric_query {
    id          = "error_rate"
    expression  = "(errors / invocations) * 100"
    label       = "Error Rate"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "InvocationClientErrors"
      namespace   = "AWS/Bedrock"
      period      = 300
      stat        = "Sum"
      dimensions = {
        ModelId = local.claude_sonnet_v4_model_id
      }
    }
  }

  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Bedrock"
      period      = 300
      stat        = "Sum"
      dimensions = {
        ModelId = local.claude_sonnet_v4_model_id
      }
    }
  }

  alarm_description = "Claude Sonnet v4.5 error rate exceeds 5% in ${each.key}"
  alarm_actions     = [aws_sns_topic.bedrock_alerts[each.key].arn]

  tags = {
    Model       = "claude-sonnet-v4"
    Environment = var.environment
  }
}
```

### Token Usage Monitoring

Monitor token consumption for cost control and capacity planning:

```hcl
# terraform/modules/bedrock-monitoring/token_monitoring.tf

resource "aws_cloudwatch_metric_alarm" "claude_sonnet_v4_input_tokens" {
  for_each = toset(local.claude_sonnet_v4_regions)

  alarm_name          = "bedrock-claude-sonnet-v4-input-tokens-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "InputTokenCount"
  namespace           = "AWS/Bedrock"
  period              = 3600  # 1 hour
  statistic           = "Sum"
  threshold           = var.claude_sonnet_v4_hourly_input_token_limit
  alarm_description   = "Claude Sonnet v4.5 input token usage exceeds hourly limit in ${each.key}"

  dimensions = {
    ModelId = local.claude_sonnet_v4_model_id
  }

  alarm_actions = [aws_sns_topic.bedrock_cost_alerts[each.key].arn]

  tags = {
    Model    = "claude-sonnet-v4"
    Category = "cost-management"
  }
}

resource "aws_cloudwatch_metric_alarm" "claude_sonnet_v4_output_tokens" {
  for_each = toset(local.claude_sonnet_v4_regions)

  alarm_name          = "bedrock-claude-sonnet-v4-output-tokens-${each.key}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "OutputTokenCount"
  namespace           = "AWS/Bedrock"
  period              = 3600
  statistic           = "Sum"
  threshold           = var.claude_sonnet_v4_hourly_output_token_limit
  alarm_description   = "Claude Sonnet v4.5 output token usage exceeds hourly limit in ${each.key}"

  dimensions = {
    ModelId = local.claude_sonnet_v4_model_id
  }

  alarm_actions = [aws_sns_topic.bedrock_cost_alerts[each.key].arn]

  tags = {
    Model    = "claude-sonnet-v4"
    Category = "cost-management"
  }
}
```

### Inference Profile Monitoring

When using application inference profiles for Claude Sonnet v4.5:

```hcl
# terraform/modules/bedrock-monitoring/inference_profile_monitoring.tf

resource "aws_cloudwatch_metric_alarm" "claude_sonnet_v4_profile_latency" {
  for_each = var.inference_profiles

  alarm_name          = "bedrock-profile-${each.key}-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "InvocationLatency"
  namespace           = "AWS/Bedrock"
  period              = 300
  statistic           = "p99"
  threshold           = each.value.latency_threshold_ms
  alarm_description   = "Inference profile ${each.key} p99 latency exceeds threshold"

  dimensions = {
    InferenceProfileArn = each.value.arn
  }

  alarm_actions = [aws_sns_topic.bedrock_alerts[each.value.primary_region].arn]

  tags = merge(var.common_tags, {
    InferenceProfile = each.key
  })
}
```

---

## CloudWatch Metrics

AWS Bedrock publishes metrics to CloudWatch under the `AWS/Bedrock` namespace. Understanding these metrics is essential for effective monitoring.

### Available Metrics Reference

| Metric Name | Description | Unit | Useful Statistics |
|-------------|-------------|------|-------------------|
| `Invocations` | Number of model invocations | Count | Sum, SampleCount |
| `InvocationLatency` | Time to process invocation | Milliseconds | Average, p50, p99 |
| `InvocationClientErrors` | Client-side errors (4xx) | Count | Sum |
| `InvocationServerErrors` | Server-side errors (5xx) | Count | Sum |
| `InvocationThrottles` | Throttled requests | Count | Sum |
| `InputTokenCount` | Input tokens processed | Count | Sum, Average |
| `OutputTokenCount` | Output tokens generated | Count | Sum, Average |
| `InvocationsPerMinute` | Rate of invocations | Count/Minute | Average |

### Custom Metrics Configuration

Define custom metrics for enhanced observability:

```hcl
# terraform/modules/bedrock-monitoring/custom_metrics.tf

resource "aws_cloudwatch_log_metric_filter" "bedrock_guardrail_interventions" {
  name           = "bedrock-guardrail-interventions"
  pattern        = "{ $.guardrailAction = \"INTERVENED\" }"
  log_group_name = aws_cloudwatch_log_group.bedrock_invocation_logs.name

  metric_transformation {
    name          = "GuardrailInterventions"
    namespace     = "Custom/Bedrock"
    value         = "1"
    default_value = "0"
    unit          = "Count"
    
    dimensions = {
      GuardrailId = "$.guardrailId"
      ModelId     = "$.modelId"
    }
  }
}

resource "aws_cloudwatch_log_metric_filter" "bedrock_content_blocked" {
  name           = "bedrock-content-blocked"
  pattern        = "{ $.guardrailAction = \"BLOCKED\" }"
  log_group_name = aws_cloudwatch_log_group.bedrock_invocation_logs.name

  metric_transformation {
    name          = "ContentBlocked"
    namespace     = "Custom/Bedrock"
    value         = "1"
    default_value = "0"
    unit          = "Count"
    
    dimensions = {
      GuardrailId = "$.guardrailId"
      BlockReason = "$.blockReason"
    }
  }
}

resource "aws_cloudwatch_log_metric_filter" "bedrock_cross_region_fallback" {
  name           = "bedrock-cross-region-fallback"
  pattern        = "{ $.crossRegionInference = true && $.fallbackUsed = true }"
  log_group_name = aws_cloudwatch_log_group.bedrock_invocation_logs.name

  metric_transformation {
    name      = "CrossRegionFallbacks"
    namespace = "Custom/Bedrock"
    value     = "1"
    unit      = "Count"
    
    dimensions = {
      SourceRegion = "$.sourceRegion"
      TargetRegion = "$.targetRegion"
    }
  }
}
```

### Metric Math Expressions

Use metric math for derived metrics:

```hcl
# terraform/modules/bedrock-monitoring/metric_math.tf

resource "aws_cloudwatch_dashboard" "bedrock_derived_metrics" {
  dashboard_name = "bedrock-derived-metrics-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Success Rate by Model"
          region = var.primary_region
          metrics = [
            [{ 
              expression = "100 - ((m1 + m2) / m3 * 100)"
              label      = "Success Rate %"
              id         = "success_rate"
            }],
            ["AWS/Bedrock", "InvocationClientErrors", "ModelId", local.claude_sonnet_v4_model_id, { id = "m1", visible = false }],
            ["AWS/Bedrock", "InvocationServerErrors", "ModelId", local.claude_sonnet_v4_model_id, { id = "m2", visible = false }],
            ["AWS/Bedrock", "Invocations", "ModelId", local.claude_sonnet_v4_model_id, { id = "m3", visible = false }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Average Tokens per Request"
          region = var.primary_region
          metrics = [
            [{
              expression = "(m1 + m2) / m3"
              label      = "Avg Total Tokens"
              id         = "avg_tokens"
            }],
            ["AWS/Bedrock", "InputTokenCount", "ModelId", local.claude_sonnet_v4_model_id, { id = "m1", visible = false }],
            ["AWS/Bedrock", "OutputTokenCount", "ModelId", local.claude_sonnet_v4_model_id, { id = "m2", visible = false }],
            ["AWS/Bedrock", "Invocations", "ModelId", local.claude_sonnet_v4_model_id, { id = "m3", visible = false }]
          ]
          period = 300
          stat   = "Sum"
        }
      }
    ]
  })
}
```

---

## Alarms Configuration

Proper alarm configuration ensures timely notification of issues while minimizing alert fatigue.

### Alarm Severity Levels

Define a tiered alarm structure:

```hcl
# terraform/modules/bedrock-monitoring/alarm_severity.tf

locals {
  alarm_severities = {
    critical = {
      evaluation_periods = 2
      datapoints_to_alarm = 2
      treat_missing_data = "breaching"
      sns_topic_suffix   = "critical"
    }
    high = {
      evaluation_periods = 3
      datapoints_to_alarm = 2
      treat_missing_data = "notBreaching"
      sns_topic_suffix   = "high"
    }
    medium = {
      evaluation_periods = 5
      datapoints_to_alarm = 3
      treat_missing_data = "notBreaching"
      sns_topic_suffix   = "medium"
    }
    low = {
      evaluation_periods = 6
      datapoints_to_alarm = 4
      treat_missing_data = "ignore"
      sns_topic_suffix   = "low"
    }
  }
}

# SNS Topics for each severity level
resource "aws_sns_topic" "bedrock_alerts" {
  for_each = local.alarm_severities

  name = "bedrock-alerts-${each.key}-${var.environment}"

  tags = {
    Severity    = each.key
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Example: PagerDuty integration for critical alerts
resource "aws_sns_topic_subscription" "critical_pagerduty" {
  topic_arn = aws_sns_topic.bedrock_alerts["critical"].arn
  protocol  = "https"
  endpoint  = var.pagerduty_endpoint
}

# Example: Slack integration for high/medium alerts
resource "aws_sns_topic_subscription" "high_slack" {
  topic_arn = aws_sns_topic.bedrock_alerts["high"].arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier.arn
}
```

### Comprehensive Alarm Set

```hcl
# terraform/modules/bedrock-monitoring/alarms.tf

variable "model_alarm_configs" {
  description = "Alarm configurations per model"
  type = map(object({
    model_id                    = string
    latency_threshold_ms        = number
    error_rate_threshold_pct    = number
    throttle_threshold          = number
    invocation_spike_threshold  = number
  }))
  
  default = {
    "claude-sonnet-v4" = {
      model_id                   = "anthropic.claude-sonnet-4-20250514-v1:0"
      latency_threshold_ms       = 30000
      error_rate_threshold_pct   = 5
      throttle_threshold         = 10
      invocation_spike_threshold = 1000
    }
    "claude-haiku" = {
      model_id                   = "anthropic.claude-3-haiku-20240307-v1:0"
      latency_threshold_ms       = 10000
      error_rate_threshold_pct   = 5
      throttle_threshold         = 50
      invocation_spike_threshold = 5000
    }
  }
}

# Latency Alarms
resource "aws_cloudwatch_metric_alarm" "model_latency" {
  for_each = var.model_alarm_configs

  alarm_name          = "bedrock-${each.key}-latency-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = local.alarm_severities["critical"].evaluation_periods
  metric_name         = "InvocationLatency"
  namespace           = "AWS/Bedrock"
  period              = 300
  statistic           = "p99"
  threshold           = each.value.latency_threshold_ms
  treat_missing_data  = local.alarm_severities["critical"].treat_missing_data

  dimensions = {
    ModelId = each.value.model_id
  }

  alarm_description = <<-EOT
    CRITICAL: ${each.key} p99 latency exceeds ${each.value.latency_threshold_ms}ms
    
    Runbook: https://wiki.example.com/runbooks/bedrock-latency
    Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=${var.primary_region}#dashboards:name=bedrock-${var.environment}
  EOT

  alarm_actions = [aws_sns_topic.bedrock_alerts["critical"].arn]
  ok_actions    = [aws_sns_topic.bedrock_alerts["critical"].arn]

  tags = {
    Model    = each.key
    Severity = "critical"
    Runbook  = "https://wiki.example.com/runbooks/bedrock-latency"
  }
}

# Throttling Alarms
resource "aws_cloudwatch_metric_alarm" "model_throttling" {
  for_each = var.model_alarm_configs

  alarm_name          = "bedrock-${each.key}-throttling-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = local.alarm_severities["high"].evaluation_periods
  metric_name         = "InvocationThrottles"
  namespace           = "AWS/Bedrock"
  period              = 300
  statistic           = "Sum"
  threshold           = each.value.throttle_threshold
  treat_missing_data  = local.alarm_severities["high"].treat_missing_data

  dimensions = {
    ModelId = each.value.model_id
  }

  alarm_description = <<-EOT
    HIGH: ${each.key} throttling detected - ${each.value.throttle_threshold} throttles in 5 minutes
    
    Actions:
    1. Check current usage against provisioned throughput
    2. Consider enabling cross-region inference
    3. Review application request patterns
    
    Runbook: https://wiki.example.com/runbooks/bedrock-throttling
  EOT

  alarm_actions = [aws_sns_topic.bedrock_alerts["high"].arn]

  tags = {
    Model    = each.key
    Severity = "high"
  }
}

# Anomaly Detection Alarm
resource "aws_cloudwatch_metric_alarm" "invocation_anomaly" {
  for_each = var.model_alarm_configs

  alarm_name          = "bedrock-${each.key}-invocation-anomaly"
  comparison_operator = "GreaterThanUpperThreshold"
  evaluation_periods  = 2
  threshold_metric_id = "ad1"
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "ad1"
    expression  = "ANOMALY_DETECTION_BAND(m1, 2)"
    label       = "Invocation Anomaly Band"
    return_data = true
  }

  metric_query {
    id          = "m1"
    return_data = true
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Bedrock"
      period      = 300
      stat        = "Sum"
      dimensions = {
        ModelId = each.value.model_id
      }
    }
  }

  alarm_description = "Unusual invocation pattern detected for ${each.key}"
  alarm_actions     = [aws_sns_topic.bedrock_alerts["medium"].arn]

  tags = {
    Model    = each.key
    Severity = "medium"
    Type     = "anomaly-detection"
  }
}
```

### Composite Alarms

Create composite alarms for complex conditions:

```hcl
# terraform/modules/bedrock-monitoring/composite_alarms.tf

resource "aws_cloudwatch_composite_alarm" "bedrock_service_degradation" {
  alarm_name = "bedrock-service-degradation-${var.environment}"
  
  alarm_rule = join(" OR ", [
    for key, config in var.model_alarm_configs : 
    "(ALARM(${aws_cloudwatch_metric_alarm.model_latency[key].alarm_name}) AND ALARM(${aws_cloudwatch_metric_alarm.model_throttling[key].alarm_name}))"
  ])

  alarm_description = <<-EOT
    CRITICAL: Multiple Bedrock service degradation indicators detected
    
    This alarm fires when both latency AND throttling alarms are active for any model.
    This indicates a significant service issue requiring immediate attention.
    
    Immediate Actions:
    1. Check AWS Health Dashboard for Bedrock service issues
    2. Verify cross-region inference is enabled and functioning
    3. Consider activating disaster recovery procedures
    
    Runbook: https://wiki.example.com/runbooks/bedrock-service-degradation
  EOT

  alarm_actions = [
    aws_sns_topic.bedrock_alerts["critical"].arn,
    var.incident_management_arn
  ]

  tags = {
    Severity    = "critical"
    Environment = var.environment
    Type        = "composite"
  }
}
```

---

## Dashboard Setup

Create comprehensive dashboards for operational visibility.

### Main Operations Dashboard

```hcl
# terraform/modules/bedrock-monitoring/dashboards.tf

resource "aws_cloudwatch_dashboard" "bedrock_operations" {
  dashboard_name = "bedrock-operations-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      # Header Row - Key Metrics
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# AWS Bedrock Operations Dashboard - ${upper(var.environment)}\n**Last Updated**: Auto-refresh enabled"
        }
      },
      
      # Invocations Overview
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 8
        height = 6
        properties = {
          title   = "Total Invocations by Model"
          region  = var.primary_region
          stacked = true
          metrics = [
            for key, config in var.model_alarm_configs :
            ["AWS/Bedrock", "Invocations", "ModelId", config.model_id, { label = key }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      
      # Latency Overview
      {
        type   = "metric"
        x      = 8
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "P99 Latency by Model"
          region = var.primary_region
          metrics = [
            for key, config in var.model_alarm_configs :
            ["AWS/Bedrock", "InvocationLatency", "ModelId", config.model_id, { label = key }]
          ]
          period = 300
          stat   = "p99"
          yAxis = {
            left = {
              label     = "Milliseconds"
              showUnits = false
            }
          }
        }
      },
      
      # Error Rate
      {
        type   = "metric"
        x      = 16
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Error Rate by Model"
          region = var.primary_region
          metrics = concat(
            [for idx, entry in flatten([
              for key, config in var.model_alarm_configs : [
                {
                  expression = "100 * (m${idx * 3 + 1} + m${idx * 3 + 2}) / m${idx * 3 + 3}"
                  label      = "${key} Error %"
                  id         = "e${idx}"
                }
              ]
            ]) : [{ expression = entry.expression, label = entry.label, id = entry.id }]],
            flatten([
              for idx, entry in [for key, config in var.model_alarm_configs : { key = key, config = config }] : [
                ["AWS/Bedrock", "InvocationClientErrors", "ModelId", entry.config.model_id, { id = "m${idx * 3 + 1}", visible = false }],
                ["AWS/Bedrock", "InvocationServerErrors", "ModelId", entry.config.model_id, { id = "m${idx * 3 + 2}", visible = false }],
                ["AWS/Bedrock", "Invocations", "ModelId", entry.config.model_id, { id = "m${idx * 3 + 3}", visible = false }]
              ]
            ])
          )
          period = 300
        }
      },
      
      # Token Usage
      {
        type   = "metric"
        x      = 0
        y      = 7
        width  = 12
        height = 6
        properties = {
          title   = "Token Usage (Input vs Output)"
          region  = var.primary_region
          stacked = false
          metrics = flatten([
            for key, config in var.model_alarm_configs : [
              ["AWS/Bedrock", "InputTokenCount", "ModelId", config.model_id, { label = "${key} Input" }],
              ["AWS/Bedrock", "OutputTokenCount", "ModelId", config.model_id, { label = "${key} Output" }]
            ]
          ])
          period = 3600
          stat   = "Sum"
        }
      },
      
      # Throttling
      {
        type   = "metric"
        x      = 12
        y      = 7
        width  = 12
        height = 6
        properties = {
          title  = "Throttled Requests"
          region = var.primary_region
          metrics = [
            for key, config in var.model_alarm_configs :
            ["AWS/Bedrock", "InvocationThrottles", "ModelId", config.model_id, { label = key }]
          ]
          period = 300
          stat   = "Sum"
          annotations = {
            horizontal = [
              {
                label = "Warning Threshold"
                value = 10
                color = "#ff7f0e"
              }
            ]
          }
        }
      },
      
      # Guardrails Section
      {
        type   = "text"
        x      = 0
        y      = 13
        width  = 24
        height = 1
        properties = {
          markdown = "## Guardrails Monitoring"
        }
      },
      
      {
        type   = "metric"
        x      = 0
        y      = 14
        width  = 12
        height = 6
        properties = {
          title   = "Guardrail Interventions"
          region  = var.primary_region
          metrics = [
            ["Custom/Bedrock", "GuardrailInterventions", { label = "Interventions" }],
            ["Custom/Bedrock", "ContentBlocked", { label = "Blocked" }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      
      # Cross-Region Inference
      {
        type   = "metric"
        x      = 12
        y      = 14
        width  = 12
        height = 6
        properties = {
          title   = "Cross-Region Fallbacks"
          region  = var.primary_region
          metrics = [
            ["Custom/Bedrock", "CrossRegionFallbacks", { label = "Fallbacks Used" }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      
      # Alarm Status
      {
        type   = "alarm"
        x      = 0
        y      = 20
        width  = 24
        height = 4
        properties = {
          title  = "Alarm Status"
          alarms = concat(
            [for key, _ in var.model_alarm_configs : aws_cloudwatch_metric_alarm.model_latency[key].arn],
            [for key, _ in var.model_alarm_configs : aws_cloudwatch_metric_alarm.model_throttling[key].arn]
          )
        }
      }
    ]
  })
}
```

### Regional Dashboard

```hcl
# terraform/modules/bedrock-monitoring/regional_dashboard.tf

resource "aws_cloudwatch_dashboard" "bedrock_regional" {
  for_each = toset(var.enabled_regions)

  dashboard_name = "bedrock-regional-${each.key}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# Bedrock Regional Dashboard - ${upper(each.key)}"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 24
        height = 8
        properties = {
          title  = "Regional Performance Overview"
          region = each.key
          metrics = [
            ["AWS/Bedrock", "Invocations", { label = "Invocations" }],
            [".", "InvocationLatency", { label = "Latency (ms)", stat = "p99", yAxis = "right" }]
          ]
          period = 60
        }
      }
    ]
  })
}
```

---

## Adding Monitoring for New Models

When adding new Bedrock models to the deployment, follow this procedure to ensure comprehensive monitoring coverage.

### Step 1: Define Model Configuration

Add the new model to the alarm configuration variable:

```hcl
# terraform/environments/production/bedrock.tfvars

model_alarm_configs = {
  # Existing models...
  "claude-sonnet-v4" = {
    model_id                   = "anthropic.claude-sonnet-4-20250514-v1:0"
    latency_threshold_ms       = 30000
    error_rate_threshold_pct   = 5
    throttle_threshold         = 10
    invocation_spike_threshold = 1000
  }
  
  # New model addition
  "claude-opus" = {
    model_id                   = "anthropic.claude-3-opus-20240229-v1:0"
    latency_threshold_ms       = 60000  # Opus is slower
    error_rate_threshold_pct   = 5
    throttle_threshold         = 5      # Lower throughput
    invocation_spike_threshold = 500
  }
}
```

### Step 2: Create Model-Specific Module (Optional)

For models requiring custom monitoring, create a dedicated module:

```hcl
# terraform/modules/bedrock-monitoring/models/claude_opus.tf

variable "enable_claude_opus_monitoring" {
  description = "Enable detailed monitoring for Claude Opus"
  type        = bool
  default     = true
}

locals {
  claude_opus_model_id = "anthropic.claude-3-opus-20240229-v1:0"
}

# Opus-specific: Extended thinking time monitoring
resource "aws_cloudwatch_metric_alarm" "claude_opus_extended_latency" {
  count = var.enable_claude_opus_monitoring ? 1 : 0

  alarm_name          = "bedrock-claude-opus-extended-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "InvocationLatency"
  namespace           = "AWS/Bedrock"
  period              = 300
  statistic           = "Maximum"
  threshold           = 120000  # 2 minutes max
  
  dimensions = {
    ModelId = local.claude_opus_model_id
  }

  alarm_description = "Claude Opus maximum latency exceeds 2 minutes - may indicate complex reasoning tasks"
  alarm_actions     = [var.notification_topic_arn]

  tags = {
    Model = "claude-opus"
    Type  = "extended-latency"
  }
}
```

### Step 3: Update Dashboard

Add the new model to existing dashboards:

```hcl
# Add to terraform/modules/bedrock-monitoring/dashboards.tf

# The for_each loop on model_alarm_configs automatically includes new models
# Verify the dashboard updates by running:
# terraform plan -target=aws_cloudwatch_dashboard.bedrock_operations
```

### Step 4: Validate Monitoring

Create a validation checklist as a Terraform output:

```hcl
# terraform/modules/bedrock-monitoring/outputs.tf

output "monitoring_validation_checklist" {
  description = "Checklist for validating monitoring setup"
  value = {
    for key, config in var.model_alarm_configs : key => {
      model_id           = config.model_id
      latency_alarm      = aws_cloudwatch_metric_alarm.model_latency[key].alarm_name
      throttling_alarm   = aws_cloudwatch_metric_alarm.model_throttling[key].alarm_name
      dashboard_included = true
      
      validation_steps = [
        "1. Verify alarm appears in CloudWatch console",
        "2. Test alarm by temporarily lowering threshold",
        "3. Confirm SNS notification delivery",
        "4. Verify model appears in dashboard widgets",
        "5. Generate test traffic and verify metrics appear"
      ]
    }
  }
}
```

### Step 5: Document the Addition

Update the model inventory:

```hcl
# terraform/modules/bedrock-monitoring/model_inventory.tf

locals {
  model_inventory = {
    for key, config in var.model_alarm_configs : key => {
      model_id          = config.model_id
      added_date        = try(var.model_metadata[key].added_date, "unknown")
      owner             = try(var.model_metadata[key].owner, "platform-team")
      use_case          = try(var.model_metadata[key].use_case, "general")
      cost_center       = try(var.model_metadata[key].cost_center, "shared")
      monitoring_status = "active"
    }
  }
}

output "model_inventory" {
  description = "Complete inventory of monitored models"
  value       = local.model_inventory
}
```

### Monitoring Checklist for New Models

When adding a new model, ensure the following monitoring components are in place:

| Component | Required | Description |
|-----------|----------|-------------|
| Latency Alarm | ✅ | P99 latency threshold alarm |
| Error Rate Alarm | ✅ | Client and server error rate alarm |
| Throttling Alarm | ✅ | Invocation throttle detection |
| Token Usage Alarm | ⚠️ | Recommended for cost control |
| Anomaly Detection | ⚠️ | Recommended for traffic analysis |
| Dashboard Widget | ✅ | Visibility in operations dashboard |
| SNS Integration | ✅ | Alert notification delivery |
| Runbook Link | ✅ | Documentation in alarm description |

### Testing New Model Monitoring

```bash
#!/bin/bash
# scripts/test-model-monitoring.sh

MODEL_KEY=$1
REGION=${2:-us-east-1}

echo "Testing monitoring for model: $MODEL_KEY in region: $REGION"

# Verify alarms exist
aws cloudwatch describe-alarms \
  --alarm-name-prefix "bedrock-${MODEL_KEY}" \
  --region $REGION \
  --query 'MetricAlarms[].AlarmName' \
  --output table

# Check recent alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name "bedrock-${MODEL_KEY}-latency-critical" \
  --region $REGION \
  --history-item-type StateUpdate \
  --max-records 5

# Verify metrics are being published
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --dimensions Name=ModelId,Value=$(terraform output -raw model_alarm_configs | jq -r ".\"${MODEL_KEY}\".model_id") \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region $REGION

echo "Monitoring validation complete for $MODEL_KEY"
```

---

## Best Practices

### 1. Alarm Tuning
- Start with conservative thresholds and adjust based on baseline data
- Use anomaly detection for traffic patterns that vary by time of day
- Implement alarm suppression during maintenance windows

### 2. Dashboard Organization
- Group related metrics together
- Use consistent time ranges across widgets
- Include alarm status widgets for quick assessment

### 3. Cost Optimization
- Use appropriate metric resolution (1-minute vs 5-minute)
- Archive metrics to S3 for long-term analysis
- Set up billing alarms for Bedrock usage

### 4. Incident Response
- Include runbook links in all alarm descriptions
- Set up on-call rotations with escalation paths
- Document common issues and resolutions