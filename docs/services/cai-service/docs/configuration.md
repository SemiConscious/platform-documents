# Configuration Reference

## Overview

The `cai-service` is a conversational AI service that integrates with AWS infrastructure, OpenSearch for knowledge retrieval, and various AI model providers. This document provides comprehensive configuration guidance for deploying and operating the service across different environments.

### Configuration Approach

The service follows a twelve-factor app methodology, using environment variables as the primary configuration mechanism. This approach enables:

- **Environment Isolation**: Clear separation between development, staging, and production configurations
- **Security**: Sensitive credentials are stored in AWS Systems Manager Parameter Store (SSM) rather than plaintext
- **Flexibility**: Easy configuration changes without code modifications
- **Container Compatibility**: Seamless deployment in Docker and Kubernetes environments

Configuration is loaded at service startup and validated against required variable constraints. Missing required variables will cause the service to fail fast with descriptive error messages.

---

## Environment Variables

### Core Service Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `ENV` | Environment name identifier used for logging, metrics, and environment-specific behavior | String | `Local` | No | `Local`, `Development`, `Staging`, `Production` |
| `REGION` | AWS region for primary service deployment and resource access | String | - | **Yes** | `us-east-1`, `eu-west-1`, `ap-southeast-2` |
| `AWS_REGION` | AWS region identifier used by AWS SDK clients | String | - | **Yes** | `us-east-1`, `eu-west-1` |

### API Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `REST_API_DOMAIN` | Base domain URL for the REST API endpoints. Used for generating callback URLs and self-referential links | URL | - | **Yes** | `https://api.example.com`, `http://localhost:8080` |
| `APIG_ENDPOINT` | AWS API Gateway endpoint URL for routing requests through the managed API layer | URL | - | **Yes** | `https://abc123.execute-api.us-east-1.amazonaws.com/prod` |
| `CORE_API_HOST` | Host URL for the Core API service that provides foundational business logic | URL | - | **Yes** | `https://core-api.internal.example.com`, `http://localhost:3000` |
| `WORKFLOW_ENGINE_ENDPOINT` | Endpoint URL for the workflow engine service handling complex multi-step AI operations | URL | - | No | `https://workflow.internal.example.com/api/v1`, `http://localhost:4000` |

### Authentication & API Keys

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `CAI_CORE_API_KEY` | API key for authenticating requests to the CAI Core service. Should be rotated regularly | String | - | **Yes** | `cai_core_k3y_abc123xyz789` |
| `CAI_AUTH_API_KEY` | API key for authenticating with the CAI Auth service for user/session validation | String | - | **Yes** | `cai_auth_k3y_def456uvw012` |
| `CAI_CORE_API_KEY_SSM_PATH` | AWS SSM Parameter Store path where the CAI Core API key is securely stored. Service will fetch the key at runtime | SSM Path | - | **Yes** | `/cai-service/prod/core-api-key`, `/cai/dev/secrets/core-key` |
| `OPENAI_API_KEY_SSM_PATH` | AWS SSM Parameter Store path for the OpenAI API key. Used when OpenAI models are configured for inference | SSM Path | - | No | `/cai-service/prod/openai-api-key`, `/cai/dev/secrets/openai` |

### AWS Credentials Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key ID for programmatic authentication. Prefer IAM roles over static credentials in production | String | - | No* | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key paired with the access key ID. Must be kept confidential | String | - | No* | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_SESSION_TOKEN` | AWS session token for temporary security credentials obtained via STS AssumeRole | String | - | No | `FwoGZXIvYXdzEBY...` (truncated) |
| `LOCAL_AWS_PROFILE` | AWS CLI profile name for local development. References profiles configured in `~/.aws/credentials` | String | - | No | `cai-dev-profile`, `default`, `sandbox` |
| `LOCAL_AWS_ROLE_ARN` | AWS IAM Role ARN to assume for local development. Enables role-based access simulation | ARN | - | No | `arn:aws:iam::123456789012:role/cai-dev-role` |

*Note: AWS credentials are typically provided via IAM roles in production (EC2 instance roles, ECS task roles, or EKS service accounts). Static credentials are primarily used for local development.

### DynamoDB Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `CAI_HISTORY_DYNAMODB` | DynamoDB table name for storing conversation history. Table must have appropriate partition/sort key schema | String | - | **Yes** | `cai-conversation-history-prod`, `cai-history-dev` |
| `CAI_SETTINGS_DYNAMODB` | DynamoDB table name for storing CAI configuration and user settings | String | - | **Yes** | `cai-settings-prod`, `cai-settings-dev` |

### OpenSearch Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `OPENSEARCH_GENERAL_COLLECTION_URL` | URL for the general OpenSearch Serverless collection used for knowledge retrieval and semantic search | URL | - | No | `https://abc123.us-east-1.aoss.amazonaws.com` |
| `OPENSEARCH_ACCESS_ROLE_ARN` | AWS IAM Role ARN that grants access to OpenSearch collections. Must have appropriate data-access policies | ARN | - | No | `arn:aws:iam::123456789012:role/opensearch-access-role` |

### AI Model Configuration

| Variable | Description | Type | Default | Required | Example |
|----------|-------------|------|---------|----------|---------|
| `GUARDRAILS_PROFILES` | JSON configuration defining AI guardrails and safety profiles. Controls content filtering, PII detection, and response boundaries | JSON | - | No | See AI Configuration section below |
| `INFERENCE_PROFILES` | JSON configuration defining AI model inference parameters including model selection, temperature, and token limits | JSON | - | No | See AI Configuration section below |

---

## AI Configuration Profiles

### Guardrails Profiles

The `GUARDRAILS_PROFILES` variable accepts a JSON object defining safety and content moderation rules:

```json
{
  "default": {
    "contentFiltering": {
      "enabled": true,
      "categories": ["hate", "violence", "sexual", "self-harm"],
      "threshold": "medium"
    },
    "piiDetection": {
      "enabled": true,
      "action": "redact",
      "types": ["email", "phone", "ssn", "credit_card"]
    },
    "topicRestrictions": {
      "blockedTopics": ["medical_advice", "legal_advice", "financial_advice"],
      "warningTopics": ["sensitive_personal"]
    }
  },
  "strict": {
    "contentFiltering": {
      "enabled": true,
      "categories": ["hate", "violence", "sexual", "self-harm", "profanity"],
      "threshold": "low"
    },
    "piiDetection": {
      "enabled": true,
      "action": "block",
      "types": ["email", "phone", "ssn", "credit_card", "address", "name"]
    }
  }
}
```

### Inference Profiles

The `INFERENCE_PROFILES` variable defines model-specific inference parameters:

```json
{
  "default": {
    "provider": "bedrock",
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "temperature": 0.7,
    "maxTokens": 4096,
    "topP": 0.9,
    "stopSequences": []
  },
  "creative": {
    "provider": "bedrock",
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "temperature": 0.9,
    "maxTokens": 8192,
    "topP": 0.95
  },
  "precise": {
    "provider": "openai",
    "model": "gpt-4-turbo",
    "temperature": 0.2,
    "maxTokens": 4096,
    "topP": 0.8
  }
}
```

---

## WebSocket Constants

The service uses WebSocket connections for real-time AI streaming responses. The following internal constants govern WebSocket behavior:

| Constant | Description | Default Value |
|----------|-------------|---------------|
| `WS_HEARTBEAT_INTERVAL` | Interval between heartbeat pings to maintain connection | `30000` (30 seconds) |
| `WS_CONNECTION_TIMEOUT` | Maximum time to establish WebSocket connection | `10000` (10 seconds) |
| `WS_MAX_RECONNECT_ATTEMPTS` | Maximum automatic reconnection attempts | `5` |
| `WS_RECONNECT_DELAY` | Initial delay between reconnection attempts (exponential backoff applied) | `1000` (1 second) |
| `WS_MAX_MESSAGE_SIZE` | Maximum WebSocket message size in bytes | `1048576` (1 MB) |

---

## Pipeline Configuration

The AI processing pipeline can be configured through internal settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `PIPELINE_MAX_CONCURRENT` | Maximum concurrent pipeline executions | `10` |
| `PIPELINE_TIMEOUT_MS` | Maximum pipeline execution time | `120000` (2 minutes) |
| `PIPELINE_RETRY_COUNT` | Number of retries for failed pipeline steps | `3` |
| `EMBEDDING_BATCH_SIZE` | Batch size for embedding generation | `100` |
| `RETRIEVAL_TOP_K` | Number of documents to retrieve for context | `5` |

---

## Environment-Specific Configurations

### Local Development

```env
# Environment
ENV=Local

# AWS Configuration (Local Development)
AWS_REGION=us-east-1
REGION=us-east-1
LOCAL_AWS_PROFILE=cai-dev-profile
LOCAL_AWS_ROLE_ARN=arn:aws:iam::123456789012:role/cai-local-dev-role

# API Configuration
REST_API_DOMAIN=http://localhost:8080
APIG_ENDPOINT=http://localhost:8080
CORE_API_HOST=http://localhost:3000
WORKFLOW_ENGINE_ENDPOINT=http://localhost:4000

# Authentication (Development Keys)
CAI_CORE_API_KEY=dev_core_key_12345
CAI_AUTH_API_KEY=dev_auth_key_67890
CAI_CORE_API_KEY_SSM_PATH=/cai-service/local/core-api-key

# DynamoDB (Local or Dev Tables)
CAI_HISTORY_DYNAMODB=cai-conversation-history-local
CAI_SETTINGS_DYNAMODB=cai-settings-local

# OpenSearch (Optional for Local)
OPENSEARCH_GENERAL_COLLECTION_URL=http://localhost:9200
# OPENSEARCH_ACCESS_ROLE_ARN= (not needed locally)

# AI Configuration
OPENAI_API_KEY_SSM_PATH=/cai-service/local/openai-api-key
GUARDRAILS_PROFILES={"default":{"contentFiltering":{"enabled":false}}}
INFERENCE_PROFILES={"default":{"provider":"bedrock","model":"anthropic.claude-3-haiku-20240307-v1:0","temperature":0.7,"maxTokens":2048}}
```

### Development Environment

```env
# Environment
ENV=Development

# AWS Configuration
AWS_REGION=us-east-1
REGION=us-east-1

# API Configuration
REST_API_DOMAIN=https://api-dev.cai.example.com
APIG_ENDPOINT=https://dev123.execute-api.us-east-1.amazonaws.com/dev
CORE_API_HOST=https://core-api-dev.internal.example.com
WORKFLOW_ENGINE_ENDPOINT=https://workflow-dev.internal.example.com

# Authentication
CAI_CORE_API_KEY=${SSM:/cai-service/dev/core-api-key}
CAI_AUTH_API_KEY=${SSM:/cai-service/dev/auth-api-key}
CAI_CORE_API_KEY_SSM_PATH=/cai-service/dev/core-api-key

# DynamoDB
CAI_HISTORY_DYNAMODB=cai-conversation-history-dev
CAI_SETTINGS_DYNAMODB=cai-settings-dev

# OpenSearch
OPENSEARCH_GENERAL_COLLECTION_URL=https://dev-collection.us-east-1.aoss.amazonaws.com
OPENSEARCH_ACCESS_ROLE_ARN=arn:aws:iam::123456789012:role/cai-opensearch-dev-role

# AI Configuration
OPENAI_API_KEY_SSM_PATH=/cai-service/dev/openai-api-key
GUARDRAILS_PROFILES={"default":{"contentFiltering":{"enabled":true,"threshold":"high"},"piiDetection":{"enabled":true,"action":"redact"}}}
INFERENCE_PROFILES={"default":{"provider":"bedrock","model":"anthropic.claude-3-sonnet-20240229-v1:0","temperature":0.7,"maxTokens":4096}}
```

### Staging Environment

```env
# Environment
ENV=Staging

# AWS Configuration
AWS_REGION=us-east-1
REGION=us-east-1

# API Configuration
REST_API_DOMAIN=https://api-staging.cai.example.com
APIG_ENDPOINT=https://staging456.execute-api.us-east-1.amazonaws.com/staging
CORE_API_HOST=https://core-api-staging.internal.example.com
WORKFLOW_ENGINE_ENDPOINT=https://workflow-staging.internal.example.com

# Authentication
CAI_CORE_API_KEY=${SSM:/cai-service/staging/core-api-key}
CAI_AUTH_API_KEY=${SSM:/cai-service/staging/auth-api-key}
CAI_CORE_API_KEY_SSM_PATH=/cai-service/staging/core-api-key

# DynamoDB
CAI_HISTORY_DYNAMODB=cai-conversation-history-staging
CAI_SETTINGS_DYNAMODB=cai-settings-staging

# OpenSearch
OPENSEARCH_GENERAL_COLLECTION_URL=https://staging-collection.us-east-1.aoss.amazonaws.com
OPENSEARCH_ACCESS_ROLE_ARN=arn:aws:iam::123456789012:role/cai-opensearch-staging-role

# AI Configuration
OPENAI_API_KEY_SSM_PATH=/cai-service/staging/openai-api-key
GUARDRAILS_PROFILES={"default":{"contentFiltering":{"enabled":true,"threshold":"medium"},"piiDetection":{"enabled":true,"action":"redact"}}}
INFERENCE_PROFILES={"default":{"provider":"bedrock","model":"anthropic.claude-3-sonnet-20240229-v1:0","temperature":0.7,"maxTokens":4096}}
```

### Production Environment

```env
# Environment
ENV=Production

# AWS Configuration
AWS_REGION=us-east-1
REGION=us-east-1

# API Configuration
REST_API_DOMAIN=https://api.cai.example.com
APIG_ENDPOINT=https://prod789.execute-api.us-east-1.amazonaws.com/prod
CORE_API_HOST=https://core-api.internal.example.com
WORKFLOW_ENGINE_ENDPOINT=https://workflow.internal.example.com

# Authentication (Retrieved from SSM at runtime)
CAI_CORE_API_KEY=${SSM:/cai-service/prod/core-api-key}
CAI_AUTH_API_KEY=${SSM:/cai-service/prod/auth-api-key}
CAI_CORE_API_KEY_SSM_PATH=/cai-service/prod/core-api-key

# DynamoDB
CAI_HISTORY_DYNAMODB=cai-conversation-history-prod
CAI_SETTINGS_DYNAMODB=cai-settings-prod

# OpenSearch
OPENSEARCH_GENERAL_COLLECTION_URL=https://prod-collection.us-east-1.aoss.amazonaws.com
OPENSEARCH_ACCESS_ROLE_ARN=arn:aws:iam::123456789012:role/cai-opensearch-prod-role

# AI Configuration
OPENAI_API_KEY_SSM_PATH=/cai-service/prod/openai-api-key
GUARDRAILS_PROFILES={"default":{"contentFiltering":{"enabled":true,"threshold":"medium"},"piiDetection":{"enabled":true,"action":"redact","types":["email","phone","ssn","credit_card"]}},"strict":{"contentFiltering":{"enabled":true,"threshold":"low"},"piiDetection":{"enabled":true,"action":"block"}}}
INFERENCE_PROFILES={"default":{"provider":"bedrock","model":"anthropic.claude-3-sonnet-20240229-v1:0","temperature":0.7,"maxTokens":4096},"high-capacity":{"provider":"bedrock","model":"anthropic.claude-3-opus-20240229-v1:0","temperature":0.5,"maxTokens":8192}}
```

---

## Docker Configuration

### Dockerfile Environment Setup

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy application files
COPY package*.json ./
RUN npm ci --only=production

COPY . .

# Set default environment variables
ENV ENV=Production \
    AWS_REGION=us-east-1 \
    NODE_ENV=production

# Expose service port
EXPOSE 8080

CMD ["node", "dist/main.js"]
```

### Docker Compose (Local Development)

```yaml
version: '3.8'

services:
  cai-service:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV=Local
      - AWS_REGION=us-east-1
      - REGION=us-east-1
      - REST_API_DOMAIN=http://localhost:8080
      - APIG_ENDPOINT=http://localhost:8080
      - CORE_API_HOST=http://core-api:3000
      - CAI_CORE_API_KEY=dev_core_key_12345
      - CAI_AUTH_API_KEY=dev_auth_key_67890
      - CAI_CORE_API_KEY_SSM_PATH=/cai-service/local/core-api-key
      - CAI_HISTORY_DYNAMODB=cai-conversation-history-local
      - CAI_SETTINGS_DYNAMODB=cai-settings-local
    volumes:
      - ~/.aws:/root/.aws:ro
    depends_on:
      - dynamodb-local
      - opensearch-local

  dynamodb-local:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"

  opensearch-local:
    image: opensearchproject/opensearch:2.11.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
```

---

## Kubernetes Configuration

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cai-service-config
  namespace: cai
data:
  ENV: "Production"
  AWS_REGION: "us-east-1"
  REGION: "us-east-1"
  REST_API_DOMAIN: "https://api.cai.example.com"
  APIG_ENDPOINT: "https://prod789.execute-api.us-east-1.amazonaws.com/prod"
  CORE_API_HOST: "https://core-api.internal.example.com"
  WORKFLOW_ENGINE_ENDPOINT: "https://workflow.internal.example.com"
  CAI_CORE_API_KEY_SSM_PATH: "/cai-service/prod/core-api-key"
  OPENAI_API_KEY_SSM_PATH: "/cai-service/prod/openai-api-key"
  CAI_HISTORY_DYNAMODB: "cai-conversation-history-prod"
  CAI_SETTINGS_DYNAMODB: "cai-settings-prod"
  OPENSEARCH_GENERAL_COLLECTION_URL: "https://prod-collection.us-east-1.aoss.amazonaws.com"
  OPENSEARCH_ACCESS_ROLE_ARN: "arn:aws:iam::123456789012:role/cai-opensearch-prod-role"
```

### Secret (for sensitive values)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cai-service-secrets
  namespace: cai
type: Opaque
stringData:
  CAI_CORE_API_KEY: "prod_core_key_encrypted"
  CAI_AUTH_API_KEY: "prod_auth_key_encrypted"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cai-service
  namespace: cai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cai-service
  template:
    metadata:
      labels:
        app: cai-service
    spec:
      serviceAccountName: cai-service-sa
      containers:
        - name: cai-service
          image: your-registry/cai-service:latest
          ports:
            - containerPort: 8080
          envFrom:
            - configMapRef:
                name: cai-service-config
            - secretRef:
                name: cai-service-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
```

---

## Security Considerations

### Sensitive Variables

The following variables contain sensitive information and require special handling:

| Variable | Risk Level | Recommendations |
|----------|------------|-----------------|
| `CAI_CORE_API_KEY` | **High** | Store in AWS SSM Parameter Store with SecureString type. Rotate every 90 days. |
| `CAI_AUTH_API_KEY` | **High** | Store in AWS SSM Parameter Store. Use separate keys per environment. |
| `AWS_ACCESS_KEY_ID` | **High** | Avoid in production. Use IAM roles instead. If required, rotate every 90 days. |
| `AWS_SECRET_ACCESS_KEY` | **Critical** | Never commit to source control. Use IAM roles in production. |
| `AWS_SESSION_TOKEN` | **Medium** | Temporary by nature. Ensure automatic refresh mechanisms are in place. |
| `OPENAI_API_KEY_SSM_PATH` | **Medium** | Path itself is not sensitive, but ensure SSM parameter has restricted access. |

### Best Practices

1. **Never commit secrets to version control**
   - Use `.env.example` with placeholder values
   - Add `.env` to `.gitignore`
   - Use secret scanning tools in CI/CD pipelines

2. **Use AWS SSM Parameter Store**
   - Store all API keys and secrets as SecureString parameters
   - Use KMS encryption for additional security
   - Implement least-privilege IAM policies for parameter access

3. **Implement secret rotation**
   - Rotate API keys every 90 days
   - Use AWS Secrets Manager for automatic rotation where supported
   - Implement zero-downtime rotation procedures

4. **Environment isolation**
   - Use separate AWS accounts for production
   - Implement network segmentation
   - Use different API keys per environment

5. **Audit and monitoring**
   - Enable CloudTrail for SSM parameter access
   - Set up alerts for unauthorized access attempts
   - Regularly review IAM permissions

---

## Troubleshooting Common Configuration Issues

### Issue: Service fails to start with "Missing required environment variable"

**Cause**: A required configuration variable is not set.

**Solution**:
1. Check the error message for the specific variable name
2. Verify the variable is set in your `.env` file or environment
3. Ensure variable names are spelled correctly (case-sensitive)
4. For containerized deployments, verify the ConfigMap/Secret is properly mounted

```bash
# Verify environment variables are set
printenv | grep -E "CAI_|AWS_|REGION"
```

### Issue: AWS authentication failures

**Cause**: Invalid or missing AWS credentials.

**Solution**:
1. For local development, verify your AWS profile exists and has valid credentials:
   ```bash
   aws sts get-caller-identity --profile your-profile-name
   ```
2. For ECS/EKS, verify the task/pod IAM role has appropriate permissions
3. Check that `AWS_REGION` matches the region where your resources are deployed

### Issue: DynamoDB table not found

**Cause**: Incorrect table name or region mismatch.

**Solution**:
1. Verify table names exactly match (case-sensitive):
   ```bash
   aws dynamodb list-tables --region us-east-1
   ```
2. Ensure `AWS_REGION` points to the correct region
3. Verify IAM permissions include `dynamodb:*` for the specified tables

### Issue: OpenSearch connection failures

**Cause**: Network, authentication, or configuration issues.

**Solution**:
1. Verify the collection URL is correct and accessible
2. Check that `OPENSEARCH_ACCESS_ROLE_ARN` has appropriate data-access policies
3. For VPC-based collections, ensure network connectivity from your deployment environment
4. Test connectivity:
   ```bash
   curl -XGET "${OPENSEARCH_GENERAL_COLLECTION_URL}/_cluster/health"
   ```

### Issue: SSM parameter retrieval failures

**Cause**: Missing permissions or incorrect parameter path.

**Solution**:
1. Verify the parameter exists:
   ```bash
   aws ssm get-parameter --name "/cai-service/prod/core-api-key" --with-decryption
   ```
2. Check IAM permissions include `ssm:GetParameter` for the specified paths
3. Ensure the parameter path matches exactly (including leading slash)

### Issue: API Gateway integration errors

**Cause**: Incorrect endpoint URL or authentication issues.

**Solution**:
1. Verify `APIG_ENDPOINT` includes the correct stage (e.g., `/prod`, `/dev`)
2. Check API Gateway logs for detailed error messages
3. Verify the API key or IAM authentication is properly configured

---

## Complete Example .env File

```env
# =============================================================================
# CAI Service Configuration
# =============================================================================
# Copy this file to .env and fill in the appropriate values for your environment
# Never commit the .env file to version control
# =============================================================================

# -----------------------------------------------------------------------------
# Environment Identification
# -----------------------------------------------------------------------------
ENV=Local

# -----------------------------------------------------------------------------
# AWS Configuration
# -----------------------------------------------------------------------------
AWS_REGION=us-east-1
REGION=us-east-1

# Local Development Only - Comment out for deployed environments
LOCAL_AWS_PROFILE=cai-dev-profile
LOCAL_AWS_ROLE_ARN=arn:aws:iam::123456789012:role/cai-local-dev-role

# Static credentials (NOT recommended for production)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_SESSION_TOKEN=

# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
REST_API_DOMAIN=http://localhost:8080
APIG_ENDPOINT=http://localhost:8080
CORE_API_HOST=http://localhost:3000
WORKFLOW_ENGINE_ENDPOINT=http://localhost:4000

# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------
CAI_CORE_API_KEY=your_core_api_key_here
CAI_AUTH_API_KEY=your_auth_api_key_here
CAI_CORE_API_KEY_SSM_PATH=/cai-service/local/core-api-key
OPENAI_API_KEY_SSM_PATH=/cai-service/local/openai-api-key

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
CAI_HISTORY_DYNAMODB=cai-conversation-history-local
CAI_SETTINGS_DYNAMODB=cai-settings-local

# -----------------------------------------------------------------------------
# OpenSearch Configuration
# -----------------------------------------------------------------------------
OPENSEARCH_GENERAL_COLLECTION_URL=http://localhost:9200
OPENSEARCH_ACCESS_ROLE_ARN=arn:aws:iam::123456789012:role/opensearch-access-role

# -----------------------------------------------------------------------------
# AI Model Configuration
# -----------------------------------------------------------------------------
GUARDRAILS_PROFILES={"default":{"contentFiltering":{"enabled":true,"threshold":"medium"},"piiDetection":{"enabled":true,"action":"redact"}}}
INFERENCE_PROFILES={"default":{"provider":"bedrock","model":"anthropic.claude-3-sonnet-20240229-v1:0","temperature":0.7,"maxTokens":4096}}
```

---

## Additional Resources

- [AWS Systems Manager Parameter Store Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [Amazon OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Amazon DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)