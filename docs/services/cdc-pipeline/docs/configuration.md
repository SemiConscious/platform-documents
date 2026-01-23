# Configuration Guide

## CDC Pipeline Service

**Version:** 1.0.0  
**Last Updated:** 2024  
**Service Type:** Change Data Capture Pipeline

---

## Overview

The CDC (Change Data Capture) Pipeline service captures and streams database changes in real-time to downstream consumers. This configuration guide covers all aspects of setting up and configuring the pipeline for different environments, including source database connections, target streaming platforms, transformation rules, and operational parameters.

### Configuration Approach

The CDC Pipeline follows a layered configuration approach:

1. **Environment Variables** - Primary configuration method for containerized deployments
2. **AWS SSM Parameter Store** - Secure storage for sensitive credentials and environment-specific settings
3. **Configuration Files** - Static configuration for complex transformation rules and schema mappings
4. **Feature Flags** - Runtime toggleable features for gradual rollouts and A/B testing

Configuration precedence (highest to lowest):
1. Environment variables
2. SSM Parameter Store values
3. Configuration file values
4. Default values

---

## Environment Variables

### Core Service Configuration

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `SERVICE_NAME` | Unique identifier for this CDC pipeline instance | string | `cdc-pipeline` | Yes | `cdc-pipeline-orders` |
| `SERVICE_ENV` | Deployment environment | enum | `development` | Yes | `production` |
| `SERVICE_PORT` | HTTP port for health checks and metrics | integer | `8080` | No | `8080` |
| `SERVICE_HOST` | Bind address for the service | string | `0.0.0.0` | No | `0.0.0.0` |
| `LOG_LEVEL` | Logging verbosity level | enum | `info` | No | `debug`, `info`, `warn`, `error` |
| `LOG_FORMAT` | Log output format | enum | `json` | No | `json`, `text` |
| `ENABLE_METRICS` | Enable Prometheus metrics endpoint | boolean | `true` | No | `true` |
| `METRICS_PORT` | Port for metrics endpoint | integer | `9090` | No | `9090` |

### Source Database Configuration

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `SOURCE_DB_TYPE` | Type of source database | enum | - | Yes | `postgresql`, `mysql`, `mongodb` |
| `SOURCE_DB_HOST` | Database server hostname | string | - | Yes | `db-master.internal.example.com` |
| `SOURCE_DB_PORT` | Database server port | integer | varies by type | No | `5432` |
| `SOURCE_DB_NAME` | Name of the database to capture | string | - | Yes | `orders_production` |
| `SOURCE_DB_USER` | Database username for CDC connection | string | - | Yes | `cdc_reader` |
| `SOURCE_DB_PASSWORD` | Database password (use SSM in production) | string | - | Yes | `********` |
| `SOURCE_DB_SSL_MODE` | SSL/TLS connection mode | enum | `require` | No | `disable`, `require`, `verify-full` |
| `SOURCE_DB_SSL_CA_CERT` | Path to CA certificate file | string | - | Conditional | `/etc/ssl/certs/rds-ca.pem` |
| `SOURCE_DB_CONNECTION_TIMEOUT` | Connection timeout in seconds | integer | `30` | No | `30` |
| `SOURCE_DB_MAX_CONNECTIONS` | Maximum concurrent connections | integer | `5` | No | `10` |
| `SOURCE_DB_REPLICATION_SLOT` | PostgreSQL replication slot name | string | `cdc_slot` | Conditional | `cdc_orders_slot` |
| `SOURCE_DB_PUBLICATION` | PostgreSQL publication name | string | `cdc_publication` | Conditional | `orders_publication` |

### Target/Sink Configuration

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `SINK_TYPE` | Target sink type | enum | - | Yes | `kafka`, `kinesis`, `sqs`, `s3` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | string | - | Conditional | `kafka-1:9092,kafka-2:9092` |
| `KAFKA_TOPIC_PREFIX` | Prefix for CDC topics | string | `cdc` | No | `cdc.orders` |
| `KAFKA_SECURITY_PROTOCOL` | Kafka security protocol | enum | `PLAINTEXT` | No | `SASL_SSL` |
| `KAFKA_SASL_MECHANISM` | SASL authentication mechanism | enum | - | Conditional | `SCRAM-SHA-512` |
| `KAFKA_SASL_USERNAME` | SASL username | string | - | Conditional | `cdc-producer` |
| `KAFKA_SASL_PASSWORD` | SASL password | string | - | Conditional | `********` |
| `KAFKA_SCHEMA_REGISTRY_URL` | Schema Registry URL | string | - | No | `https://schema-registry:8081` |
| `KINESIS_STREAM_NAME` | AWS Kinesis stream name | string | - | Conditional | `cdc-orders-stream` |
| `KINESIS_REGION` | AWS region for Kinesis | string | `us-east-1` | Conditional | `us-west-2` |
| `S3_BUCKET_NAME` | S3 bucket for CDC data lake | string | - | Conditional | `cdc-data-lake-prod` |
| `S3_PREFIX` | S3 key prefix | string | `cdc/` | No | `cdc/orders/` |

### Transformation Configuration

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `TRANSFORM_ENABLED` | Enable message transformations | boolean | `true` | No | `true` |
| `TRANSFORM_CONFIG_PATH` | Path to transformation config file | string | `/etc/cdc/transforms.yaml` | No | `/config/transforms.yaml` |
| `SCHEMA_EVOLUTION_MODE` | How to handle schema changes | enum | `backward` | No | `none`, `backward`, `forward`, `full` |
| `INCLUDE_BEFORE_IMAGE` | Include previous row state in events | boolean | `true` | No | `true` |
| `INCLUDE_TRANSACTION_INFO` | Include transaction metadata | boolean | `false` | No | `true` |
| `TIMESTAMP_FORMAT` | Timestamp serialization format | enum | `iso8601` | No | `iso8601`, `epoch_ms`, `epoch_us` |
| `DECIMAL_HANDLING` | How to serialize decimal types | enum | `string` | No | `string`, `double`, `precise` |

### Performance Tuning

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `BATCH_SIZE` | Maximum events per batch | integer | `1000` | No | `5000` |
| `BATCH_TIMEOUT_MS` | Maximum wait time for batch | integer | `100` | No | `500` |
| `QUEUE_SIZE` | Internal event queue size | integer | `10000` | No | `50000` |
| `WORKER_THREADS` | Number of worker threads | integer | `4` | No | `8` |
| `MEMORY_LIMIT_MB` | Maximum memory usage | integer | `512` | No | `1024` |
| `CHECKPOINT_INTERVAL_MS` | How often to checkpoint position | integer | `30000` | No | `60000` |
| `MAX_RETRIES` | Maximum retry attempts for failures | integer | `10` | No | `20` |
| `RETRY_BACKOFF_MS` | Initial retry backoff | integer | `1000` | No | `2000` |
| `RETRY_BACKOFF_MAX_MS` | Maximum retry backoff | integer | `60000` | No | `120000` |

---

## SSM Parameter Store

Sensitive configuration values should be stored in AWS SSM Parameter Store with encryption enabled.

### Parameter Naming Convention

```
/cdc-pipeline/{environment}/{parameter-name}
```

### Required SSM Parameters

| Parameter Path | Description | Type | Encryption |
|----------------|-------------|------|------------|
| `/cdc-pipeline/{env}/source-db-password` | Source database password | SecureString | KMS |
| `/cdc-pipeline/{env}/kafka-sasl-password` | Kafka SASL password | SecureString | KMS |
| `/cdc-pipeline/{env}/schema-registry-credentials` | Schema Registry auth | SecureString | KMS |
| `/cdc-pipeline/{env}/encryption-key` | Data encryption key | SecureString | KMS |

### SSM Integration Configuration

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `SSM_ENABLED` | Enable SSM Parameter Store integration | boolean | `false` | No | `true` |
| `SSM_REGION` | AWS region for SSM | string | `us-east-1` | Conditional | `us-west-2` |
| `SSM_PREFIX` | Parameter path prefix | string | `/cdc-pipeline` | No | `/cdc-pipeline/prod` |
| `SSM_REFRESH_INTERVAL` | How often to refresh parameters (seconds) | integer | `300` | No | `600` |
| `SSM_DECRYPT` | Automatically decrypt SecureStrings | boolean | `true` | No | `true` |

---

## Database Configuration

### PostgreSQL CDC Setup

For PostgreSQL sources, the CDC pipeline uses logical replication. Required database configuration:

```sql
-- postgresql.conf settings
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10

-- Create replication user
CREATE ROLE cdc_reader WITH REPLICATION LOGIN PASSWORD 'secure_password';

-- Grant necessary permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cdc_reader;
GRANT USAGE ON SCHEMA public TO cdc_reader;

-- Create publication for CDC
CREATE PUBLICATION cdc_publication FOR ALL TABLES;

-- Or for specific tables
CREATE PUBLICATION cdc_publication FOR TABLE orders, customers, products;
```

### MySQL CDC Setup

For MySQL sources using binlog:

```sql
-- my.cnf settings
[mysqld]
server-id = 1
log_bin = mysql-bin
binlog_format = ROW
binlog_row_image = FULL
expire_logs_days = 3

-- Create CDC user
CREATE USER 'cdc_reader'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'cdc_reader'@'%';
FLUSH PRIVILEGES;
```

### Database-Specific Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `POSTGRES_DECODING_PLUGIN` | Logical decoding output plugin | enum | `pgoutput` | No | `pgoutput`, `wal2json` |
| `POSTGRES_SNAPSHOT_MODE` | Initial snapshot behavior | enum | `initial` | No | `initial`, `never`, `when_needed` |
| `MYSQL_SERVER_ID` | Unique server ID for replication | integer | `1` | Conditional | `223344` |
| `MYSQL_BINLOG_FILENAME` | Starting binlog file | string | - | No | `mysql-bin.000003` |
| `MYSQL_BINLOG_POSITION` | Starting binlog position | integer | - | No | `154` |
| `MYSQL_GTID_MODE` | Enable GTID-based replication | boolean | `true` | No | `true` |

---

## Redaction Configuration

The CDC pipeline supports automatic redaction of sensitive data fields before events are published downstream.

### Redaction Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `REDACTION_ENABLED` | Enable automatic field redaction | boolean | `false` | No | `true` |
| `REDACTION_CONFIG_PATH` | Path to redaction rules file | string | `/etc/cdc/redaction.yaml` | Conditional | `/config/redaction.yaml` |
| `REDACTION_MODE` | Redaction strategy | enum | `hash` | No | `mask`, `hash`, `remove`, `encrypt` |
| `REDACTION_HASH_ALGORITHM` | Hash algorithm for `hash` mode | enum | `sha256` | No | `sha256`, `sha512`, `blake2b` |
| `REDACTION_HASH_SALT` | Salt for hashing (use SSM) | string | - | Conditional | `********` |
| `REDACTION_MASK_CHAR` | Character for masking | string | `*` | No | `X` |
| `REDACTION_PRESERVE_LENGTH` | Maintain original field length | boolean | `true` | No | `false` |

### Redaction Configuration File Example

```yaml
# /etc/cdc/redaction.yaml
version: "1.0"

global_rules:
  # Redact any field matching these patterns across all tables
  - pattern: ".*password.*"
    mode: remove
  - pattern: ".*ssn.*"
    mode: hash
  - pattern: ".*credit_card.*"
    mode: mask
    mask_config:
      show_last: 4
      mask_char: "*"

table_rules:
  customers:
    - field: email
      mode: hash
    - field: phone_number
      mode: mask
      mask_config:
        show_last: 4
    - field: date_of_birth
      mode: generalize
      generalize_config:
        precision: year
    - field: address
      mode: remove
      
  orders:
    - field: billing_address
      mode: encrypt
      encrypt_config:
        key_id: "alias/cdc-encryption-key"
    - field: ip_address
      mode: hash

  employees:
    - field: salary
      mode: remove
    - field: bank_account
      mode: hash
```

---

## Feature Flags

Feature flags enable runtime control of pipeline behavior without redeployment.

### Feature Flag Variables

| Variable Name | Description | Type | Default | Required | Example |
|---------------|-------------|------|---------|----------|---------|
| `FF_PROVIDER` | Feature flag provider | enum | `env` | No | `env`, `launchdarkly`, `unleash`, `ssm` |
| `FF_LAUNCHDARKLY_SDK_KEY` | LaunchDarkly SDK key | string | - | Conditional | `sdk-xxx` |
| `FF_UNLEASH_URL` | Unleash server URL | string | - | Conditional | `https://unleash.example.com/api` |
| `FF_UNLEASH_TOKEN` | Unleash API token | string | - | Conditional | `*:production.xxx` |
| `FF_REFRESH_INTERVAL` | Flag refresh interval (seconds) | integer | `30` | No | `60` |

### Available Feature Flags

| Flag Name | Description | Default | Impact |
|-----------|-------------|---------|--------|
| `FF_ENABLE_SCHEMA_VALIDATION` | Validate events against schema | `true` | Performance impact when enabled |
| `FF_ENABLE_DEAD_LETTER_QUEUE` | Send failed events to DLQ | `true` | Prevents data loss |
| `FF_ENABLE_COMPRESSION` | Compress events before sending | `false` | Reduces bandwidth, increases CPU |
| `FF_ENABLE_DEDUPLICATION` | Deduplicate events in window | `false` | Memory overhead |
| `FF_ENABLE_RATE_LIMITING` | Rate limit event publishing | `false` | Prevents downstream overload |
| `FF_ENABLE_CIRCUIT_BREAKER` | Enable circuit breaker pattern | `true` | Improves resilience |
| `FF_ENABLE_PARALLEL_TABLES` | Process tables in parallel | `true` | Throughput improvement |
| `FF_ENABLE_AUDIT_LOG` | Log all configuration changes | `true` | Compliance requirement |

### Environment Variable Feature Flags

When using `FF_PROVIDER=env`, flags are read from environment variables:

```bash
FF_ENABLE_SCHEMA_VALIDATION=true
FF_ENABLE_DEAD_LETTER_QUEUE=true
FF_ENABLE_COMPRESSION=false
```

---

## Per-Environment Settings

### Development Environment

```bash
# .env.development
SERVICE_NAME=cdc-pipeline-dev
SERVICE_ENV=development
LOG_LEVEL=debug
LOG_FORMAT=text

# Source Database (local Docker)
SOURCE_DB_TYPE=postgresql
SOURCE_DB_HOST=localhost
SOURCE_DB_PORT=5432
SOURCE_DB_NAME=orders_dev
SOURCE_DB_USER=cdc_reader
SOURCE_DB_PASSWORD=dev_password
SOURCE_DB_SSL_MODE=disable
SOURCE_DB_REPLICATION_SLOT=cdc_dev_slot
SOURCE_DB_PUBLICATION=cdc_dev_publication

# Sink (local Kafka)
SINK_TYPE=kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=cdc.dev
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Reduced performance settings for development
BATCH_SIZE=100
BATCH_TIMEOUT_MS=1000
WORKER_THREADS=2
MEMORY_LIMIT_MB=256

# Feature Flags
FF_PROVIDER=env
FF_ENABLE_SCHEMA_VALIDATION=true
FF_ENABLE_COMPRESSION=false
FF_ENABLE_AUDIT_LOG=false

# Disable SSM in development
SSM_ENABLED=false

# Redaction disabled in development (use test data)
REDACTION_ENABLED=false
```

### Staging Environment

```bash
# .env.staging
SERVICE_NAME=cdc-pipeline-staging
SERVICE_ENV=staging
LOG_LEVEL=info
LOG_FORMAT=json

# Source Database (RDS)
SOURCE_DB_TYPE=postgresql
SOURCE_DB_HOST=orders-staging.cluster-xxx.us-east-1.rds.amazonaws.com
SOURCE_DB_PORT=5432
SOURCE_DB_NAME=orders_staging
SOURCE_DB_USER=cdc_reader
SOURCE_DB_SSL_MODE=require
SOURCE_DB_SSL_CA_CERT=/etc/ssl/certs/rds-ca-2019-root.pem
SOURCE_DB_REPLICATION_SLOT=cdc_staging_slot
SOURCE_DB_PUBLICATION=cdc_staging_publication
# Password from SSM

# Sink (MSK)
SINK_TYPE=kafka
KAFKA_BOOTSTRAP_SERVERS=b-1.msk-staging.xxx.kafka.us-east-1.amazonaws.com:9094,b-2.msk-staging.xxx.kafka.us-east-1.amazonaws.com:9094
KAFKA_TOPIC_PREFIX=cdc.staging
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=SCRAM-SHA-512
KAFKA_SASL_USERNAME=cdc-producer-staging
KAFKA_SCHEMA_REGISTRY_URL=https://schema-registry-staging.internal:8081
# Password from SSM

# Moderate performance settings
BATCH_SIZE=1000
BATCH_TIMEOUT_MS=500
WORKER_THREADS=4
MEMORY_LIMIT_MB=512

# SSM Configuration
SSM_ENABLED=true
SSM_REGION=us-east-1
SSM_PREFIX=/cdc-pipeline/staging

# Feature Flags (test new features here)
FF_PROVIDER=ssm
FF_ENABLE_SCHEMA_VALIDATION=true
FF_ENABLE_COMPRESSION=true
FF_ENABLE_AUDIT_LOG=true

# Redaction enabled with staging rules
REDACTION_ENABLED=true
REDACTION_CONFIG_PATH=/etc/cdc/redaction-staging.yaml
```

### Production Environment

```bash
# .env.production
SERVICE_NAME=cdc-pipeline-prod
SERVICE_ENV=production
LOG_LEVEL=warn
LOG_FORMAT=json

# Source Database (RDS Multi-AZ)
SOURCE_DB_TYPE=postgresql
SOURCE_DB_HOST=orders-prod.cluster-xxx.us-east-1.rds.amazonaws.com
SOURCE_DB_PORT=5432
SOURCE_DB_NAME=orders_production
SOURCE_DB_USER=cdc_reader_prod
SOURCE_DB_SSL_MODE=verify-full
SOURCE_DB_SSL_CA_CERT=/etc/ssl/certs/rds-ca-2019-root.pem
SOURCE_DB_CONNECTION_TIMEOUT=10
SOURCE_DB_MAX_CONNECTIONS=10
SOURCE_DB_REPLICATION_SLOT=cdc_prod_slot
SOURCE_DB_PUBLICATION=cdc_prod_publication
# Password from SSM with KMS encryption

# Sink (MSK Production Cluster)
SINK_TYPE=kafka
KAFKA_BOOTSTRAP_SERVERS=b-1.msk-prod.xxx.kafka.us-east-1.amazonaws.com:9094,b-2.msk-prod.xxx.kafka.us-east-1.amazonaws.com:9094,b-3.msk-prod.xxx.kafka.us-east-1.amazonaws.com:9094
KAFKA_TOPIC_PREFIX=cdc.prod
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=SCRAM-SHA-512
KAFKA_SASL_USERNAME=cdc-producer-prod
KAFKA_SCHEMA_REGISTRY_URL=https://schema-registry-prod.internal:8081
# Password from SSM with KMS encryption

# High-performance settings
BATCH_SIZE=5000
BATCH_TIMEOUT_MS=100
QUEUE_SIZE=100000
WORKER_THREADS=8
MEMORY_LIMIT_MB=2048
CHECKPOINT_INTERVAL_MS=10000
MAX_RETRIES=20

# SSM Configuration
SSM_ENABLED=true
SSM_REGION=us-east-1
SSM_PREFIX=/cdc-pipeline/production
SSM_REFRESH_INTERVAL=600

# Feature Flags (conservative settings)
FF_PROVIDER=launchdarkly
FF_LAUNCHDARKLY_SDK_KEY=sdk-xxx-production
FF_ENABLE_SCHEMA_VALIDATION=true
FF_ENABLE_DEAD_LETTER_QUEUE=true
FF_ENABLE_COMPRESSION=true
FF_ENABLE_CIRCUIT_BREAKER=true
FF_ENABLE_AUDIT_LOG=true

# Full redaction enabled
REDACTION_ENABLED=true
REDACTION_CONFIG_PATH=/etc/cdc/redaction-production.yaml
REDACTION_MODE=hash
REDACTION_HASH_ALGORITHM=sha256
# Salt from SSM
```

---

## Security Considerations

### Credential Management

1. **Never commit credentials to version control**
   - Use `.env.example` files with placeholder values
   - Add `.env*` to `.gitignore`

2. **Use SSM Parameter Store for production**
   ```bash
   # Store credentials in SSM
   aws ssm put-parameter \
     --name "/cdc-pipeline/production/source-db-password" \
     --value "actual-password" \
     --type SecureString \
     --key-id alias/cdc-pipeline-key
   ```

3. **Rotate credentials regularly**
   - Database passwords: Every 90 days
   - API keys: Every 180 days
   - Encryption keys: Annually

### Network Security

```bash
# Require SSL for database connections in production
SOURCE_DB_SSL_MODE=verify-full

# Use private subnets and VPC endpoints
# Configure security groups to allow only necessary traffic
```

### Encryption

| Data Type | Encryption Method |
|-----------|-------------------|
| Database passwords | SSM SecureString with KMS |
| Kafka credentials | SSM SecureString with KMS |
| Data in transit | TLS 1.2+ |
| Sensitive field values | Application-level encryption or hashing |
| Audit logs | S3 server-side encryption |

### IAM Permissions

Minimum required IAM permissions for the CDC pipeline:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/cdc-pipeline/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:*:*:key/cdc-pipeline-key-id"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:*:*:stream/cdc-*"
    }
  ]
}
```

---

## Complete Example .env File

```bash
# =============================================================================
# CDC Pipeline Configuration
# =============================================================================
# Copy this file to .env and customize for your environment
# DO NOT commit .env files with actual credentials to version control
# =============================================================================

# -----------------------------------------------------------------------------
# Core Service Configuration
# -----------------------------------------------------------------------------
SERVICE_NAME=cdc-pipeline
SERVICE_ENV=development
SERVICE_PORT=8080
SERVICE_HOST=0.0.0.0
LOG_LEVEL=info
LOG_FORMAT=json
ENABLE_METRICS=true
METRICS_PORT=9090

# -----------------------------------------------------------------------------
# Source Database Configuration
# -----------------------------------------------------------------------------
SOURCE_DB_TYPE=postgresql
SOURCE_DB_HOST=localhost
SOURCE_DB_PORT=5432
SOURCE_DB_NAME=your_database
SOURCE_DB_USER=cdc_reader
SOURCE_DB_PASSWORD=REPLACE_WITH_ACTUAL_PASSWORD
SOURCE_DB_SSL_MODE=require
SOURCE_DB_SSL_CA_CERT=/etc/ssl/certs/ca-cert.pem
SOURCE_DB_CONNECTION_TIMEOUT=30
SOURCE_DB_MAX_CONNECTIONS=5
SOURCE_DB_REPLICATION_SLOT=cdc_slot
SOURCE_DB_PUBLICATION=cdc_publication

# PostgreSQL-specific
POSTGRES_DECODING_PLUGIN=pgoutput
POSTGRES_SNAPSHOT_MODE=initial

# -----------------------------------------------------------------------------
# Sink Configuration (Kafka)
# -----------------------------------------------------------------------------
SINK_TYPE=kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=cdc
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
# Uncomment for SASL authentication:
# KAFKA_SECURITY_PROTOCOL=SASL_SSL
# KAFKA_SASL_MECHANISM=SCRAM-SHA-512
# KAFKA_SASL_USERNAME=your-username
# KAFKA_SASL_PASSWORD=REPLACE_WITH_ACTUAL_PASSWORD
# KAFKA_SCHEMA_REGISTRY_URL=http://localhost:8081

# -----------------------------------------------------------------------------
# Transformation Configuration
# -----------------------------------------------------------------------------
TRANSFORM_ENABLED=true
TRANSFORM_CONFIG_PATH=/etc/cdc/transforms.yaml
SCHEMA_EVOLUTION_MODE=backward
INCLUDE_BEFORE_IMAGE=true
INCLUDE_TRANSACTION_INFO=false
TIMESTAMP_FORMAT=iso8601
DECIMAL_HANDLING=string

# -----------------------------------------------------------------------------
# Performance Tuning
# -----------------------------------------------------------------------------
BATCH_SIZE=1000
BATCH_TIMEOUT_MS=100
QUEUE_SIZE=10000
WORKER_THREADS=4
MEMORY_LIMIT_MB=512
CHECKPOINT_INTERVAL_MS=30000
MAX_RETRIES=10
RETRY_BACKOFF_MS=1000
RETRY_BACKOFF_MAX_MS=60000

# -----------------------------------------------------------------------------
# SSM Parameter Store (Production)
# -----------------------------------------------------------------------------
SSM_ENABLED=false
SSM_REGION=us-east-1
SSM_PREFIX=/cdc-pipeline
SSM_REFRESH_INTERVAL=300
SSM_DECRYPT=true

# -----------------------------------------------------------------------------
# Redaction Configuration
# -----------------------------------------------------------------------------
REDACTION_ENABLED=false
REDACTION_CONFIG_PATH=/etc/cdc/redaction.yaml
REDACTION_MODE=hash
REDACTION_HASH_ALGORITHM=sha256
# REDACTION_HASH_SALT=REPLACE_WITH_SECRET_SALT

# -----------------------------------------------------------------------------
# Feature Flags
# -----------------------------------------------------------------------------
FF_PROVIDER=env
FF_ENABLE_SCHEMA_VALIDATION=true
FF_ENABLE_DEAD_LETTER_QUEUE=true
FF_ENABLE_COMPRESSION=false
FF_ENABLE_DEDUPLICATION=false
FF_ENABLE_RATE_LIMITING=false
FF_ENABLE_CIRCUIT_BREAKER=true
FF_ENABLE_PARALLEL_TABLES=true
FF_ENABLE_AUDIT_LOG=true

# LaunchDarkly (if using)
# FF_PROVIDER=launchdarkly
# FF_LAUNCHDARKLY_SDK_KEY=sdk-xxx

# Unleash (if using)
# FF_PROVIDER=unleash
# FF_UNLEASH_URL=https://unleash.example.com/api
# FF_UNLEASH_TOKEN=your-token
```

---

## Troubleshooting Common Configuration Issues

### Issue: Database Connection Failures

**Symptoms:** Service fails to start with connection timeout errors

**Solutions:**
```bash
# Verify database is reachable
pg_isready -h $SOURCE_DB_HOST -p $SOURCE_DB_PORT

# Check SSL certificate validity
openssl s_client -connect $SOURCE_DB_HOST:$SOURCE_DB_PORT -CAfile $SOURCE_DB_SSL_CA_CERT

# Verify replication slot exists
psql -h $SOURCE_DB_HOST -U $SOURCE_DB_USER -d $SOURCE_DB_NAME \
  -c "SELECT * FROM pg_replication_slots WHERE slot_name = 'cdc_slot';"
```

### Issue: Kafka Connection Errors

**Symptoms:** Events not being published, timeout errors

**Solutions:**
```bash
# Test Kafka connectivity
kafkacat -b $KAFKA_BOOTSTRAP_SERVERS -L

# Verify topic exists
kafka-topics.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS --describe --topic cdc.your_table

# Check SASL credentials (if applicable)
kafka-console-producer.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS \
  --producer.config /path/to/client.properties --topic test
```

### Issue: SSM Parameter Not Found

**Symptoms:** Service fails with "ParameterNotFound" error

**Solutions:**
```bash
# Verify parameter exists
aws ssm get-parameter --name "/cdc-pipeline/production/source-db-password" --with-decryption

# Check IAM permissions
aws sts get-caller-identity
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/your-role \
  --action-names ssm:GetParameter \
  --resource-arns "arn:aws:ssm:us-east-1:ACCOUNT:parameter/cdc-pipeline/*"
```

### Issue: High Memory Usage

**Symptoms:** OOM errors, service restarts

**Solutions:**
```bash
# Reduce batch and queue sizes
BATCH_SIZE=500
QUEUE_SIZE=5000

# Reduce worker threads
WORKER_THREADS=2

# Enable compression to reduce memory footprint
FF_ENABLE_COMPRESSION=true
```

### Issue: Replication Lag

**Symptoms:** Events delayed, high lag metrics

**Solutions:**
```bash
# Increase parallelism
WORKER_THREADS=8
FF_ENABLE_PARALLEL_TABLES=true

# Optimize batch settings
BATCH_SIZE=5000
BATCH_TIMEOUT_MS=50

# Check source database performance
SELECT * FROM pg_stat_replication;
```

---

## Related Documentation

- [CDC Pipeline Architecture Guide](./architecture.md)
- [Deployment Guide](./deployment.md)
- [Monitoring and Alerting](./monitoring.md)
- [Schema Evolution Guide](./schema-evolution.md)
- [Disaster Recovery](./disaster-recovery.md)