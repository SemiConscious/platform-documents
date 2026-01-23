# Debugging Guide

## Overview

This comprehensive guide provides detailed instructions for using the debug toolkit task definition included in the `aws-terraform-ecs` Terraform module to troubleshoot containerized applications running on Amazon ECS. The debug toolkit is an essential component for operators who need to diagnose issues with ECS services, investigate network connectivity problems, inspect container filesystems, or debug application-level issues in a production-like environment.

---

## Overview of Debug Toolkit

### What is the Debug Toolkit?

The debug toolkit is a specialized ECS task definition provisioned by the `aws-terraform-ecs` module that provides a containerized environment pre-loaded with common debugging and troubleshooting utilities. Unlike production application containers that are typically stripped down for security and performance, the debug toolkit container includes a comprehensive set of diagnostic tools that enable operators to investigate issues within the ECS cluster environment.

### Key Characteristics

- **Ephemeral by Design**: Debug containers are meant to be run temporarily for troubleshooting, not as long-running services
- **Network Access**: Runs within the same VPC and security group context as your application containers
- **Pre-installed Tools**: Comes equipped with networking utilities, text editors, package managers, and system monitoring tools
- **IAM Integration**: Inherits appropriate IAM permissions for AWS service interactions
- **Resource Isolated**: Configured with dedicated CPU and memory allocations to prevent interference with production workloads

### Architecture Context

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS VPC                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   ECS Cluster                        │    │
│  │                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │    │
│  │  │ App Service  │  │ App Service  │  │  Debug    │  │    │
│  │  │   Task A     │  │   Task B     │  │  Toolkit  │  │    │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │    │
│  │         │                 │                │         │    │
│  │         └─────────────────┼────────────────┘         │    │
│  │                           │                          │    │
│  │                    Shared Subnets                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## When to Use the Debug Container

### Appropriate Use Cases

| Scenario | Description | Priority |
|----------|-------------|----------|
| **Network Connectivity Issues** | Diagnosing DNS resolution failures, connection timeouts, or security group misconfigurations | High |
| **Service Discovery Problems** | Verifying that services can locate and communicate with each other | High |
| **Database Connection Issues** | Testing connectivity to RDS, ElastiCache, or other data stores | High |
| **AWS Service Access** | Validating IAM permissions and connectivity to AWS services | Medium |
| **Application Log Investigation** | Accessing logs not available through CloudWatch | Medium |
| **Performance Diagnostics** | Investigating resource utilization and bottlenecks | Medium |
| **Configuration Verification** | Checking environment variables and secrets availability | Low |

### When NOT to Use the Debug Container

- **Production Traffic Handling**: Never route production traffic to debug containers
- **Long-running Processes**: Debug containers should be terminated after troubleshooting
- **Sensitive Data Processing**: Avoid processing production data in debug sessions
- **Automated Testing**: Use dedicated testing infrastructure instead

### Decision Flowchart

```
Is the issue related to container runtime?
├── YES → Use ECS Exec or CloudWatch Logs first
│         └── Still unresolved? → Use Debug Toolkit
└── NO → Is it a network/connectivity issue?
         ├── YES → Use Debug Toolkit
         └── NO → Is it an AWS service access issue?
                  ├── YES → Use Debug Toolkit with appropriate IAM role
                  └── NO → Consider application-level debugging
```

---

## Running Debug Tasks via AWS Console

### Step-by-Step Instructions

#### Step 1: Navigate to ECS Console

1. Sign in to the AWS Management Console
2. Navigate to **Amazon Elastic Container Service**
3. Select **Clusters** from the left navigation pane
4. Choose the cluster provisioned by your `aws-terraform-ecs` module

#### Step 2: Run a New Task

1. Click the **Tasks** tab within your cluster view
2. Click **Run new task** button
3. Configure the task as follows:

**Compute Configuration:**
- **Launch type**: Select `FARGATE` or `EC2` based on your cluster configuration
- **Platform version**: `LATEST` (for Fargate)

**Deployment Configuration:**
- **Application type**: `Task`
- **Family**: Select `{your-prefix}-debug-toolkit` from the dropdown
- **Revision**: `LATEST`
- **Desired tasks**: `1`

#### Step 3: Configure Networking

```
VPC:              Select your application VPC
Subnets:          Select private subnets (same as application tasks)
Security groups:  Select the debug toolkit security group
Auto-assign IP:   DISABLED (for private subnets)
```

#### Step 4: Review and Launch

1. Review all configuration settings
2. Click **Create** to launch the debug task
3. Wait for the task status to change to `RUNNING`

#### Step 5: Connect to the Container

1. Select the running debug task
2. Navigate to the **Logs** tab to verify startup
3. Use **ECS Exec** to connect (if enabled):
   - Select the task
   - Click **Execute command**
   - Enter `/bin/bash` as the command

---

## Running Debug Tasks via AWS CLI

### Prerequisites

Ensure you have the following configured:

```bash
# Verify AWS CLI installation
aws --version

# Verify credentials are configured
aws sts get-caller-identity

# Install Session Manager plugin (required for ECS Exec)
# macOS
brew install --cask session-manager-plugin

# Linux
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

### Running the Debug Task

```bash
# Set environment variables
export CLUSTER_NAME="your-ecs-cluster-name"
export TASK_DEFINITION="your-prefix-debug-toolkit"
export SUBNET_IDS="subnet-xxxxx,subnet-yyyyy"
export SECURITY_GROUP_ID="sg-zzzzz"
export REGION="us-east-1"

# Run the debug task
aws ecs run-task \
  --cluster "${CLUSTER_NAME}" \
  --task-definition "${TASK_DEFINITION}" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_IDS}],securityGroups=[${SECURITY_GROUP_ID}],assignPublicIp=DISABLED}" \
  --enable-execute-command \
  --region "${REGION}"
```

### Connecting to the Running Task

```bash
# Get the task ARN
TASK_ARN=$(aws ecs list-tasks \
  --cluster "${CLUSTER_NAME}" \
  --family "${TASK_DEFINITION}" \
  --query 'taskArns[0]' \
  --output text \
  --region "${REGION}")

# Connect to the container
aws ecs execute-command \
  --cluster "${CLUSTER_NAME}" \
  --task "${TASK_ARN}" \
  --container "debug-toolkit" \
  --command "/bin/bash" \
  --interactive \
  --region "${REGION}"
```

### Stopping the Debug Task

```bash
# Stop the task when debugging is complete
aws ecs stop-task \
  --cluster "${CLUSTER_NAME}" \
  --task "${TASK_ARN}" \
  --reason "Debugging session completed" \
  --region "${REGION}"
```

### Automation Script

Save this as `debug-session.sh` for convenient debugging:

```bash
#!/bin/bash
set -euo pipefail

# Configuration
CLUSTER_NAME="${1:-}"
REGION="${AWS_REGION:-us-east-1}"

if [[ -z "${CLUSTER_NAME}" ]]; then
    echo "Usage: $0 <cluster-name>"
    exit 1
fi

# Retrieve configuration from Terraform outputs
TASK_DEFINITION=$(terraform output -raw debug_toolkit_task_definition_arn 2>/dev/null || echo "")
SUBNET_IDS=$(terraform output -raw private_subnet_ids 2>/dev/null || echo "")
SECURITY_GROUP_ID=$(terraform output -raw debug_toolkit_security_group_id 2>/dev/null || echo "")

if [[ -z "${TASK_DEFINITION}" ]]; then
    echo "Error: Could not retrieve Terraform outputs. Ensure you're in the correct directory."
    exit 1
fi

echo "Starting debug task..."
TASK_ARN=$(aws ecs run-task \
    --cluster "${CLUSTER_NAME}" \
    --task-definition "${TASK_DEFINITION}" \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_IDS}],securityGroups=[${SECURITY_GROUP_ID}],assignPublicIp=DISABLED}" \
    --enable-execute-command \
    --region "${REGION}" \
    --query 'tasks[0].taskArn' \
    --output text)

echo "Waiting for task to start..."
aws ecs wait tasks-running \
    --cluster "${CLUSTER_NAME}" \
    --tasks "${TASK_ARN}" \
    --region "${REGION}"

echo "Connecting to debug container..."
aws ecs execute-command \
    --cluster "${CLUSTER_NAME}" \
    --task "${TASK_ARN}" \
    --container "debug-toolkit" \
    --command "/bin/bash" \
    --interactive \
    --region "${REGION}"

# Cleanup on exit
echo "Stopping debug task..."
aws ecs stop-task \
    --cluster "${CLUSTER_NAME}" \
    --task "${TASK_ARN}" \
    --reason "Debug session ended" \
    --region "${REGION}" > /dev/null

echo "Debug session complete."
```

---

## Common Debugging Scenarios

### Scenario 1: DNS Resolution Failures

**Symptoms**: Application cannot resolve hostnames for internal services or external endpoints.

```bash
# Test DNS resolution
nslookup my-service.local
dig my-service.local

# Check DNS configuration
cat /etc/resolv.conf

# Test AWS VPC DNS
nslookup internal-api.example.local 10.0.0.2

# Verify Route 53 private hosted zone resolution
dig +short my-service.internal
```

### Scenario 2: Database Connectivity Issues

**Symptoms**: Application cannot connect to RDS or other database services.

```bash
# Test TCP connectivity
nc -zv database-endpoint.rds.amazonaws.com 5432

# Test with timeout
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/database-endpoint.rds.amazonaws.com/5432' && echo "Success" || echo "Failed"

# PostgreSQL connectivity test
psql -h database-endpoint.rds.amazonaws.com -U username -d database -c "SELECT 1;"

# MySQL connectivity test
mysql -h database-endpoint.rds.amazonaws.com -u username -p -e "SELECT 1;"

# Check network path
traceroute database-endpoint.rds.amazonaws.com
```

### Scenario 3: Security Group Misconfiguration

**Symptoms**: Intermittent or complete connection failures between services.

```bash
# Check outbound connectivity
curl -v https://www.example.com

# Test specific port connectivity
for port in 80 443 5432 6379; do
    echo -n "Port ${port}: "
    nc -zv -w 3 target-host ${port} 2>&1 | grep -o 'succeeded\|failed'
done

# Verify security group metadata
curl http://169.254.169.254/latest/meta-data/security-groups

# Check network interfaces
ip addr show
ip route show
```

### Scenario 4: Service Discovery Issues

**Symptoms**: Services cannot find each other via Cloud Map or internal load balancers.

```bash
# List Cloud Map services
aws servicediscovery list-services --region ${REGION}

# Query service instances
aws servicediscovery discover-instances \
    --namespace-name your-namespace \
    --service-name your-service

# Test internal ALB
curl -v http://internal-alb.region.elb.amazonaws.com/health

# Check /etc/hosts for any overrides
cat /etc/hosts
```

### Scenario 5: IAM Permission Issues

**Symptoms**: Application receives `AccessDenied` errors when accessing AWS services.

```bash
# Check current identity
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket/

# Test Secrets Manager access
aws secretsmanager get-secret-value --secret-id your-secret

# Test SSM Parameter Store access
aws ssm get-parameter --name /your/parameter

# Check task role credentials
curl http://169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
```

---

## Available Tools in Toolkit Container

### Networking Tools

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `curl` | HTTP client for API testing | `curl -v https://api.example.com` |
| `wget` | File download and HTTP testing | `wget -O- https://example.com` |
| `netcat (nc)` | TCP/UDP connectivity testing | `nc -zv host 443` |
| `dig` | DNS lookup utility | `dig +short example.com` |
| `nslookup` | DNS query tool | `nslookup example.com` |
| `traceroute` | Network path analysis | `traceroute example.com` |
| `ping` | ICMP connectivity testing | `ping -c 4 example.com` |
| `tcpdump` | Packet capture | `tcpdump -i eth0 port 443` |
| `ip` | Network interface management | `ip addr show` |
| `ss` | Socket statistics | `ss -tuln` |

### System Tools

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `ps` | Process listing | `ps aux` |
| `top` | Resource monitoring | `top -bn1` |
| `htop` | Interactive process viewer | `htop` |
| `free` | Memory usage | `free -h` |
| `df` | Disk space | `df -h` |
| `lsof` | Open file listing | `lsof -i :8080` |

### AWS Tools

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `aws` | AWS CLI | `aws ecs list-tasks --cluster my-cluster` |
| `jq` | JSON processing | `aws ecs describe-tasks | jq '.tasks[].taskArn'` |

### Text Processing & Editors

| Tool | Purpose |
|------|---------|
| `vim` | Text editor |
| `nano` | Simple text editor |
| `grep` | Pattern searching |
| `awk` | Text processing |
| `sed` | Stream editor |

---

## Examples and Commands

### Complete Debugging Session Example

```bash
# 1. Start by checking basic connectivity
echo "=== Checking basic network connectivity ==="
ip addr show
ip route show
cat /etc/resolv.conf

# 2. Test DNS resolution for critical services
echo "=== Testing DNS resolution ==="
for host in "api.internal" "database.rds.amazonaws.com" "cache.elasticache.amazonaws.com"; do
    echo -n "${host}: "
    dig +short ${host} || echo "FAILED"
done

# 3. Test port connectivity
echo "=== Testing port connectivity ==="
declare -A endpoints=(
    ["database.rds.amazonaws.com"]="5432"
    ["cache.elasticache.amazonaws.com"]="6379"
    ["api.internal"]="8080"
)

for host in "${!endpoints[@]}"; do
    port=${endpoints[$host]}
    echo -n "${host}:${port} - "
    nc -zv -w 5 ${host} ${port} 2>&1 | tail -1
done

# 4. Verify AWS credentials and permissions
echo "=== Checking AWS credentials ==="
aws sts get-caller-identity
aws ecs list-tasks --cluster ${CLUSTER_NAME} --max-results 5

# 5. Check resource utilization
echo "=== Resource utilization ==="
free -h
df -h
```

### Network Troubleshooting One-liners

```bash
# Check all listening ports
ss -tuln

# Monitor network traffic to specific host
tcpdump -i any host database.example.com -n

# Check HTTP response headers
curl -I -s https://api.example.com | head -10

# Test SSL/TLS connectivity
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates

# Continuous connectivity test
while true; do
    nc -zv -w 2 database.example.com 5432 && echo "$(date): Connected" || echo "$(date): Failed"
    sleep 5
done
```

### AWS Service Debugging

```bash
# List all tasks in the cluster
aws ecs list-tasks --cluster ${CLUSTER_NAME} | jq -r '.taskArns[]'

# Describe a specific task
aws ecs describe-tasks \
    --cluster ${CLUSTER_NAME} \
    --tasks ${TASK_ARN} \
    | jq '.tasks[] | {status: .lastStatus, health: .healthStatus, startedAt: .startedAt}'

# Check CloudWatch logs
aws logs get-log-events \
    --log-group-name /ecs/${SERVICE_NAME} \
    --log-stream-name ecs/${CONTAINER_NAME}/${TASK_ID} \
    --limit 50 \
    | jq -r '.events[].message'

# Test access to Secrets Manager
aws secretsmanager list-secrets --query 'SecretList[].Name' --output table

# Verify Parameter Store access
aws ssm get-parameters-by-path \
    --path "/app/production/" \
    --recursive \
    --query 'Parameters[].Name'
```

---

## Best Practices

1. **Always clean up**: Stop debug tasks immediately after troubleshooting
2. **Document findings**: Record debugging steps and results for future reference
3. **Use least privilege**: Only request necessary IAM permissions for debug tasks
4. **Avoid production data**: Never process sensitive production data in debug containers
5. **Monitor costs**: Debug tasks incur compute costs; be mindful of long-running sessions
6. **Security awareness**: Debug containers have elevated access; treat sessions as privileged operations

---

## Troubleshooting the Debug Toolkit

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Task fails to start | Insufficient IAM permissions | Verify task execution role has required permissions |
| Cannot connect via ECS Exec | ECS Exec not enabled | Ensure `--enable-execute-command` flag is set |
| Network timeout | Security group misconfiguration | Verify debug toolkit security group rules |
| DNS resolution fails | VPC DNS not enabled | Check VPC DNS settings and DHCP options |

### Getting Help

If you encounter issues not covered in this guide:

1. Check CloudWatch Logs for the debug task
2. Review ECS task stopped reason in the console
3. Verify Terraform module outputs for correct resource IDs
4. Consult AWS ECS documentation for service-specific issues