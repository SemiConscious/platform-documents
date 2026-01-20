# Platform Core Services Troubleshooting Guide

> **Last Updated**: 2026-01-20  
> **Document Status**: Active  
> **Owner**: Platform Engineering

## Overview

This guide provides troubleshooting procedures for common issues with platform core services. Use this guide for diagnosing and resolving problems with platform-api, platform-sapien, CDRMunch, and archiving services.

---

## Table of Contents

1. [General Diagnostic Commands](#1-general-diagnostic-commands)
2. [Platform-API Issues](#2-platform-api-issues)
3. [Platform-Sapien Issues](#3-platform-sapien-issues)
4. [CDRMunch Issues](#4-cdrmunch-issues)
5. [Archiving Issues](#5-archiving-issues)
6. [Database Issues](#6-database-issues)
7. [Message Queue Issues](#7-message-queue-issues)
8. [Common Error Codes](#8-common-error-codes)

---

## 1. General Diagnostic Commands

### Check Service Status

```bash
# Systemd services
systemctl status core-api
systemctl status sapien-core
systemctl status rmdistiller
systemctl status rmcdrgateway
systemctl status rmarchived
systemctl status rmestuary
systemctl status rmhurler
systemctl status cdrmunch-task-executor

# Docker services
docker ps --filter "name=sapien"
docker ps --filter "name=core-api"
docker-compose ps
```

### View Service Logs

```bash
# Systemd journal
journalctl -u rmdistiller -f --since "1 hour ago"
journalctl -u rmarchived -f --since "30 minutes ago"

# Docker logs
docker logs sapien-core --tail 100 -f
docker logs core-api --tail 100 -f

# Application logs
tail -f /var/log/coreapi/api.log
tail -f /var/www/sapien/var/logs/prod.log
tail -f /var/log/cdrmunch/distiller.log
```

### Check System Resources

```bash
# CPU and memory
top -b -n 1 | head -20
free -h
vmstat 1 5

# Disk usage
df -h
du -sh /var/lib/archiving/cache
du -sh /var/spool/cdrtmp

# Open file handles
lsof -p $(pgrep rmarchived) | wc -l
cat /proc/$(pgrep rmdistiller)/fd | wc -l

# Network connections
ss -tuln | grep -E "(3306|5672|10001|10100)"
netstat -an | grep ESTABLISHED | wc -l
```

### Health Check Endpoints

```bash
# Core API
curl -s http://localhost/health

# Sapien
curl -s http://localhost/api/health

# CDR Gateway
curl -s http://localhost/health

# RabbitMQ
curl -s http://localhost:15672/api/healthchecks/node -u guest:guest
```

---

## 2. Platform-API Issues

### Issue: API Returns 500 Internal Server Error

**Symptoms**:
- API requests return HTTP 500
- Log shows PHP errors

**Diagnosis**:
```bash
# Check PHP error log
tail -100 /var/log/httpd/error_log
tail -100 /var/log/php-fpm/error.log

# Check CodeIgniter logs
tail -100 /var/log/coreapi/log-$(date +%Y-%m-%d).php

# Verify database connectivity
mysql -h core-sql-rw -u coreapi -p -e "SELECT 1"
```

**Common Causes**:
1. Database connection failure
2. Missing configuration file
3. PHP memory limit exceeded
4. Permission issues on cache directory

**Resolution**:
```bash
# 1. Database connection - check credentials
grep -E "hostname|username|database" /var/www/coreapi/application/config/database.php

# 2. Clear cache
rm -rf /tmp/db_cache/*
rm -rf /var/www/coreapi/application/cache/*

# 3. Fix permissions
chown -R apache:apache /var/www/coreapi/application/cache
chmod -R 755 /var/www/coreapi/application/cache

# 4. Restart services
systemctl restart php-fpm
systemctl restart httpd
```

### Issue: API Response Time Slow

**Symptoms**:
- API requests take >5 seconds
- Timeouts on client side

**Diagnosis**:
```bash
# Check slow query log
tail -100 /var/log/mysql/slow.log

# Profile a request
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost/api/users"

# Check database query time
mysql -h core-sql-rw -u coreapi -p -e "SHOW PROCESSLIST"
```

**Resolution**:
```bash
# 1. Enable query caching (if not already)
sed -i "s/'cache_on' => FALSE/'cache_on' => TRUE/" /var/www/coreapi/application/config/database.php

# 2. Check missing indexes
mysql -e "EXPLAIN SELECT * FROM users WHERE email='test@example.com'" API

# 3. Add index if needed
mysql -e "CREATE INDEX idx_users_email ON users(email)" API

# 4. Restart API
systemctl restart php-fpm
```

### Issue: Authentication Failures

**Symptoms**:
- Valid credentials return 401
- "Invalid token" errors

**Diagnosis**:
```bash
# Check API key format
echo "Authorization header format: base64(username:password_hash)"

# Test authentication manually
AUTH=$(echo -n "user:$(echo -n 'password' | md5sum | cut -d' ' -f1)" | base64)
curl -H "Authorization: $AUTH" http://localhost/api/users

# Check session table
mysql -h core-sql-rw -u coreapi -p API -e "SELECT * FROM sessions WHERE user_id=12345"
```

**Resolution**:
```bash
# 1. Clear expired sessions
mysql -h core-sql-rw -u coreapi -p API -e "DELETE FROM sessions WHERE expires_at < NOW()"

# 2. Reset user password if corrupted
mysql -h core-sql-rw -u coreapi -p API -e "UPDATE users SET password_hash=MD5('newpassword') WHERE id=12345"

# 3. Check API key validity
mysql -h core-sql-rw -u coreapi -p API -e "SELECT * FROM api_keys WHERE key_value='xxx'"
```

---

## 3. Platform-Sapien Issues

### Issue: OAuth Token Generation Fails

**Symptoms**:
- `/oauth/v2/token` returns 400/401
- "invalid_grant" or "invalid_client" errors

**Diagnosis**:
```bash
# Check OAuth client exists
docker exec sapien-core php bin/console doctrine:query:sql \
  "SELECT * FROM oauth_clients WHERE random_id='your_client_id'"

# Check OAuth logs
docker exec sapien-core tail -100 var/logs/prod.log | grep -i oauth

# Test token request
curl -X POST http://localhost/oauth/v2/token \
  -d "grant_type=password" \
  -d "client_id=xxx" \
  -d "client_secret=xxx" \
  -d "username=user" \
  -d "password=pass" \
  -v
```

**Resolution**:
```bash
# 1. Create new OAuth client
docker exec sapien-core php bin/console fos:oauth-server:create-client \
  --redirect-uri="https://app.example.com" \
  --grant-type="password" \
  --grant-type="refresh_token"

# 2. Clear expired tokens
docker exec sapien-core php bin/console doctrine:query:sql \
  "DELETE FROM oauth_access_tokens WHERE expires_at < NOW()"

# 3. Clear Symfony cache
docker exec sapien-core php bin/console cache:clear --env=prod
```

### Issue: RabbitMQ Consumer Not Processing

**Symptoms**:
- Messages piling up in queue
- Consumer appears stuck

**Diagnosis**:
```bash
# Check queue depth
curl -s http://localhost:15672/api/queues/%2F/user-events -u sapien:pass | jq '.messages'

# Check consumer status
curl -s http://localhost:15672/api/queues/%2F/user-events -u sapien:pass | jq '.consumers'

# Check consumer logs
docker logs sapien-consumer --tail 100 -f
```

**Resolution**:
```bash
# 1. Restart consumer
docker restart sapien-consumer

# 2. Purge queue if needed (caution - data loss)
curl -X DELETE http://localhost:15672/api/queues/%2F/user-events/contents -u sapien:pass

# 3. Check and fix dead letter queue
curl -s http://localhost:15672/api/queues/%2F/events.dlq -u sapien:pass | jq '.messages'
```

### Issue: File Upload Failures

**Symptoms**:
- Audio/recording uploads return errors
- S3/MinIO connection errors

**Diagnosis**:
```bash
# Check S3 connectivity
docker exec sapien-core aws s3 ls s3://${S3_BUCKET}/ --endpoint-url ${S3_ENDPOINT}

# Check credentials
docker exec sapien-core env | grep AWS

# Check upload directory permissions
docker exec sapien-core ls -la /tmp/uploads
```

**Resolution**:
```bash
# 1. Fix S3 credentials
docker exec sapien-core aws configure set aws_access_key_id ${AWS_ACCESS_KEY}
docker exec sapien-core aws configure set aws_secret_access_key ${AWS_SECRET_KEY}

# 2. Create bucket if missing
docker exec sapien-core aws s3 mb s3://${S3_BUCKET} --endpoint-url ${S3_ENDPOINT}

# 3. Fix upload directory
docker exec sapien-core mkdir -p /tmp/uploads
docker exec sapien-core chmod 777 /tmp/uploads
```

---

## 4. CDRMunch Issues

### Issue: CDRs Not Being Processed

**Symptoms**:
- CDRs not appearing in database
- Gateway returning errors

**Diagnosis**:
```bash
# Check distiller status
systemctl status rmdistiller
journalctl -u rmdistiller --since "10 minutes ago"

# Check gateway status  
systemctl status rmcdrgateway
journalctl -u rmcdrgateway --since "10 minutes ago"

# Check queue depth
# (Distiller has internal queue)
ss -tuln | grep 10001
```

**Resolution**:
```bash
# 1. Restart distiller
systemctl restart rmdistiller

# 2. Check database connectivity
mysql -h big-sql-rw -u cdrmunch -p CDRs -e "SELECT 1"

# 3. Clear cache if corrupted
rm -rf /var/spool/cdrtmp/cdrmunch-cache/*
systemctl restart rmdistiller
```

### Issue: Task Executor Not Running Tasks

**Symptoms**:
- Pending tasks piling up
- No emails/SMS being sent

**Diagnosis**:
```bash
# Check task executor
systemctl status cdrmunch-task-executor
journalctl -u cdrmunch-task-executor --since "10 minutes ago"

# Check pending tasks
mysql -h core-sql-rw -u cdrmunch -p API -e "SELECT task_type, COUNT(*) FROM tasks WHERE status='pending' GROUP BY task_type"

# Check failed tasks
mysql -h core-sql-rw -u cdrmunch -p API -e "SELECT * FROM tasks WHERE status='failed' ORDER BY created_at DESC LIMIT 10"
```

**Resolution**:
```bash
# 1. Restart task executor
systemctl restart cdrmunch-task-executor

# 2. Clear stuck tasks
mysql -h core-sql-rw -u cdrmunch -p API -e "UPDATE tasks SET status='pending', attempts=0 WHERE status='processing' AND updated_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)"

# 3. Check SMS provider credentials
grep -E "textmarketer|messagebird" /etc/cdrmunch/task-executor.conf
```

### Issue: Hurler Not Uploading to AWS

**Symptoms**:
- Call analysis tasks failing
- S3 upload errors in logs

**Diagnosis**:
```bash
# Check hurler status
systemctl status rmhurler
journalctl -u rmhurler --since "10 minutes ago" | grep -i error

# Test AWS connectivity
aws s3 ls s3://rm-call-analysis/ --region eu-west-1
```

**Resolution**:
```bash
# 1. Check AWS credentials
aws sts get-caller-identity

# 2. Test S3 bucket access
aws s3 cp test.txt s3://rm-call-analysis/test.txt
aws s3 rm s3://rm-call-analysis/test.txt

# 3. Restart hurler
systemctl restart rmhurler
```

---

## 5. Archiving Issues

### Issue: Recordings Not Being Archived

**Symptoms**:
- Recordings missing from S3
- `rmarchived` errors in syslog

**Diagnosis**:
```bash
# Check archived status
systemctl status rmarchived
journalctl -u rmarchived --since "30 minutes ago" | grep -i error

# Check queue watermark
# High watermark indicates backlog
cat /proc/$(pgrep rmarchived)/status | grep -E "VmRSS|Threads"

# Check disk space
df -h /var/lib/archiving/cache
df -h /mnt/rmfs/call-buffering
```

**Resolution**:
```bash
# 1. Check S3 connectivity
curl -I https://s3.eu-west-1.amazonaws.com

# 2. Clear cache if full
find /var/lib/archiving/cache -type f -mtime +7 -delete

# 3. Restart archived
systemctl restart rmarchived

# 4. Check file handles
ulimit -n
# If low, increase in /etc/security/limits.conf
```

### Issue: Recording Download Failures (Estuary)

**Symptoms**:
- Recording download returns 404
- Estuary errors in logs

**Diagnosis**:
```bash
# Check estuary status
systemctl status rmestuary
journalctl -u rmestuary --since "10 minutes ago"

# Test estuary directly
curl -I http://localhost:10102/recording/12345

# Check S3 file exists
aws s3 ls s3://recordings-bucket/path/to/recording.mp3
```

**Resolution**:
```bash
# 1. Clear estuary cache
rm -rf /var/lib/archiving/estuary-cache/*

# 2. Restart estuary
systemctl restart rmestuary

# 3. Check CoreAPI for recording metadata
curl http://cdr.coreapi.internal/recording/12345
```

---

## 6. Database Issues

### Issue: Database Connection Failures

**Symptoms**:
- "Can't connect to MySQL server" errors
- Services failing to start

**Diagnosis**:
```bash
# Check MySQL status
systemctl status mysqld
mysqladmin -u root -p status

# Check connections
mysql -e "SHOW STATUS LIKE 'Threads_connected'"
mysql -e "SHOW PROCESSLIST"

# Check max connections
mysql -e "SHOW VARIABLES LIKE 'max_connections'"
```

**Resolution**:
```bash
# 1. Restart MySQL
systemctl restart mysqld

# 2. Kill long-running queries
mysql -e "SELECT CONCAT('KILL ',id,';') FROM information_schema.processlist WHERE time > 300"

# 3. Increase max connections (temporary)
mysql -e "SET GLOBAL max_connections = 600"

# 4. Check for deadlocks
mysql -e "SHOW ENGINE INNODB STATUS\G" | grep -A 50 "LATEST DETECTED DEADLOCK"
```

### Issue: Replication Lag

**Symptoms**:
- Read-only queries returning stale data
- Replica behind master

**Diagnosis**:
```bash
# Check replica status
mysql -e "SHOW SLAVE STATUS\G" | grep -E "Seconds_Behind_Master|Slave_SQL_Running|Slave_IO_Running"

# Check replication errors
mysql -e "SHOW SLAVE STATUS\G" | grep -E "Last_Error|Last_SQL_Error"
```

**Resolution**:
```bash
# 1. Skip single error (if safe)
mysql -e "STOP SLAVE; SET GLOBAL SQL_SLAVE_SKIP_COUNTER = 1; START SLAVE;"

# 2. Rebuild replica from backup if needed
# (Major operation - contact DBA)

# 3. Temporarily route reads to master
# Update database.php to point *_ro to master
```

---

## 7. Message Queue Issues

### Issue: RabbitMQ Not Responding

**Symptoms**:
- Publishers failing to send
- Management UI not accessible

**Diagnosis**:
```bash
# Check RabbitMQ status
systemctl status rabbitmq-server
rabbitmqctl status

# Check cluster status
rabbitmqctl cluster_status

# Check memory/disk alarms
rabbitmqctl list_alarms
```

**Resolution**:
```bash
# 1. Clear memory alarm
rabbitmqctl set_vm_memory_high_watermark 0.7

# 2. Clear disk alarm
# Free up disk space on /var/lib/rabbitmq

# 3. Restart RabbitMQ
systemctl restart rabbitmq-server

# 4. Force boot single node (if cluster split)
rabbitmqctl stop_app
rabbitmqctl force_boot
rabbitmqctl start_app
```

### Issue: Messages Stuck in Dead Letter Queue

**Symptoms**:
- `events.dlq` growing
- Messages not being processed

**Diagnosis**:
```bash
# Check DLQ depth
rabbitmqctl list_queues name messages | grep dlq

# Get sample message
rabbitmqctl list_queues name messages --formatter json | jq '.[] | select(.name=="events.dlq")'

# Check why messages failed
# Look at x-death header in messages
```

**Resolution**:
```bash
# 1. Requeue messages for retry
# Use management UI to move messages from DLQ to original queue

# 2. Purge if messages are unrecoverable
rabbitmqctl purge_queue events.dlq

# 3. Fix underlying issue (check consumer logs)
docker logs sapien-consumer | grep -i error
```

---

## 8. Common Error Codes

### HTTP Error Codes

| Code | Service | Meaning | Action |
|------|---------|---------|--------|
| 400 | All | Bad request | Check request format |
| 401 | All | Unauthorized | Check credentials/token |
| 403 | All | Forbidden | Check permissions |
| 404 | All | Not found | Verify resource exists |
| 429 | All | Rate limited | Implement backoff |
| 500 | All | Server error | Check logs |
| 502 | Gateway | Bad gateway | Check upstream service |
| 503 | All | Service unavailable | Check service health |
| 504 | Gateway | Gateway timeout | Check service response time |

### Database Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 1040 | Too many connections | Increase max_connections |
| 1045 | Access denied | Check credentials |
| 1062 | Duplicate entry | Check unique constraints |
| 1205 | Lock wait timeout | Optimize queries, check locks |
| 1213 | Deadlock found | Retry transaction |
| 2002 | Can't connect | Check MySQL is running |
| 2003 | Can't connect to host | Check network/firewall |
| 2006 | MySQL server gone away | Increase wait_timeout |

### Application Error Codes

| Code | Service | Meaning |
|------|---------|---------|
| `AUTH_001` | API | Invalid credentials |
| `AUTH_002` | API | Token expired |
| `AUTH_003` | API | Insufficient permissions |
| `CDR_001` | CDRMunch | Invalid CDR format |
| `CDR_002` | CDRMunch | Database write failed |
| `ARC_001` | Archiving | S3 upload failed |
| `ARC_002` | Archiving | File not found |
| `MQ_001` | Sapien | Queue connection failed |
| `MQ_002` | Sapien | Message publish failed |

---

## Quick Reference: Log Locations

| Service | Log Location |
|---------|--------------|
| Core-API | `/var/log/coreapi/` |
| Sapien | `/var/www/sapien/var/logs/` |
| CDR Distiller | syslog or `/var/log/cdrmunch/distiller.log` |
| CDR Gateway | syslog |
| Archiving | syslog |
| Task Executor | `/var/log/cdrmunch/task-executor.log` |
| MySQL | `/var/log/mysql/` |
| RabbitMQ | `/var/log/rabbitmq/` |

---

## Emergency Contacts

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| Platform On-Call | platform-oncall@redmatter.com | Immediate |
| Database DBA | dba@redmatter.com | 15 min |
| Infrastructure | infra@redmatter.com | 30 min |
| Security | security@redmatter.com | Immediate for breaches |

---

## Related Documentation

- [Platform Core Services Inventory](platform-core.md)
- [Configuration Guide](platform-configuration-guide.md)
- [API Reference](platform-sapien-api-reference.md)
- [Monitoring & Alerting](../operations/monitoring.md)
