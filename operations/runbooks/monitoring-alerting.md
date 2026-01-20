# Monitoring and Alerting Runbook

**Last Updated:** 2026-01-20  
**Source:** [Confluence - Monitoring Tools](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937197578/Monitoring+Tools)

---

## Overview

This runbook covers the monitoring tools, alerting systems, and observability platforms used across the Natterbox platform.

---

## Monitoring Tools Quick Reference

### Tool Categories

| Category | Tools |
|----------|-------|
| Internal Monitoring | Nagios, hAPI, Cacti, Smokeping, Prometheus, AWS CloudWatch |
| External Monitoring | DotCom (SIP), StatusCake (Web) |
| Observability | ELK Stack (ElasticSearch, Logstash, Kibana) |
| Alerting | OpsGenie |

---

## Internal Monitoring Tools

### Nagios

**Purpose:** Infrastructure and application monitoring

| Environment | URL | Authentication |
|-------------|-----|----------------|
| Production | https://nagios.redmatter.com | LDAP credentials |
| Staging | https://nagios.stage.redmatter.com | LDAP credentials |
| QA01 | http://nagios.qa01.redmatter.com/ | LDAP credentials |
| QA02 | http://nagios.qa02.redmatter.com/ | LDAP credentials |

**Note:** QA01 and QA02 are separate QA environments for concurrent testing, not failover data centers.

### Cacti

**Purpose:** Network monitoring and graphing

| Environment | URL | Authentication |
|-------------|-----|----------------|
| Production | https://cacti.redmatter.com | LDAP credentials |
| Staging | https://cacti.stage.redmatter.com | LDAP credentials |

### Smokeping

**Purpose:** Network latency and packet loss monitoring

| Environment | URL |
|-------------|-----|
| Production | https://smokeping.redmatter.com |

See [SmokePing Documentation](https://natterbox.atlassian.net/wiki/display/CO/SmokePing) for usage details.

### AWS CloudWatch

**Purpose:** AWS resource and application monitoring

**Access:** Requires AWS SSO and prod view permissions (contact Platform team if needed)

**Dashboards:**
- [EU West 1 Dashboard](https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#home:)

### Prometheus

**Purpose:** Application and infrastructure metrics

**Integration:** Used for detailed application metrics alongside Nagios.

### hAPI

**Purpose:** Internal health API for platform services

---

## External Monitoring Tools

### DotCom Monitor

**Purpose:** SIP endpoint monitoring

| URL | Authentication |
|-----|----------------|
| [DotCom Monitor](https://user.dotcom-monitor.com/c18734/client/monitoring/devices/all) | Individual credentials |

### StatusCake

**Purpose:** Web application uptime monitoring

**Status:** Coming soon (as of last update)

---

## Observability Stack

### ELK Stack (ElasticSearch, Logstash, Kibana)

**Purpose:** Log aggregation, search, and visualization

**Components:**
- **ElasticSearch:** Log storage and search
- **Logstash:** Log ingestion and processing
- **Kibana:** Visualization and dashboards

---

## Alerting System

### OpsGenie

**Purpose:** Alert management, on-call scheduling, incident tracking

| URL | Authentication |
|-----|----------------|
| [OpsGenie Dashboard](https://redmatterops.app.opsgenie.com) | Dedicated user account (licensing) |

**Note:** Requires a dedicated user account due to licensing considerations.

---

## Utility Tools

### Toolbox

**Purpose:** Operational utility tools

| Environment | URL |
|-------------|-----|
| Production | https://toolbox.redmatter.com |
| Staging | https://toolbox.stage.redmatter.com |

---

## Slack Alert Channels

### Production Alerts

| Channel | Purpose |
|---------|---------|
| [#alerts-prod](https://natterbox.slack.com/archives/C02GT09SQNA) | Production system alerts |
| [#tech-team-incidents](https://natterbox.slack.com/archives/C022VLCL76X) | Incident coordination |

### Staging Alerts

| Channel | Purpose |
|---------|---------|
| [#alerts-stage](https://natterbox.slack.com/archives/C027LGBE3ML) | Staging system alerts |

### Third-Party Status

| Channel | Purpose |
|---------|---------|
| [#aws-health-reports](https://natterbox.slack.com/archives/C092Z8YAH7Z) | AWS service health |
| [#thirdparty-status](https://natterbox.slack.com/archives/C08TC5A54VD) | Third-party service status |

---

## Common Alert Categories

### Infrastructure Alerts

- CPU utilization thresholds
- Memory pressure
- Disk space warnings
- Network connectivity issues
- Service unavailability

### Application Alerts

- API response time degradation
- Error rate spikes
- Queue depth thresholds
- Database connection issues

### Voice/SIP Alerts

- Call failure rates
- SIP registration issues
- Media quality degradation
- Carrier connectivity problems

---

## Alert Response Workflow

### Initial Triage

1. **Check alert source and severity**
   - OpsGenie priority level
   - Affected system/service

2. **Verify alert validity**
   - Check monitoring dashboards
   - Confirm not a false positive

3. **Assess impact**
   - Production vs non-production
   - Customer-facing vs internal

### Escalation Path

```
L1: On-call Engineer
    ↓ (15 min no response or major incident)
L2: Platform Engineering Team Lead
    ↓ (critical incident)
L3: Engineering Leadership
```

### Communication

- Update [#tech-team-incidents](https://natterbox.slack.com/archives/C022VLCL76X) for active incidents
- Post status updates every 30 minutes during incidents
- Create post-incident review for P1/P2 incidents

---

## Dashboard Quick Access

### Key Dashboards

| Purpose | Location |
|---------|----------|
| Platform Overview | Nagios Production |
| Network Health | Cacti Production |
| AWS Resources | CloudWatch EU-West-1 |
| Log Analysis | Kibana |
| Alert Status | OpsGenie |

### Health Check URLs

```bash
# Quick health check commands
curl -s https://nagios.redmatter.com/health
curl -s https://toolbox.redmatter.com/api/health

# DNS resolution check
dig portal.redmatter.com

# SIP endpoint check
# (Use DotCom Monitor for detailed SIP checks)
```

---

## Requesting Access

### LDAP-based Tools (Nagios, Cacti)

- Use existing LDAP credentials
- Contact IT if credentials not working

### AWS CloudWatch

- Request AWS SSO access
- Contact Platform team for prod view permissions

### OpsGenie

- Dedicated user required (licensing)
- Request through Platform team lead

### Heroku

- Requires 2FA setup
- Contact Platform team for access

---

## Related Documentation

- [Emergency Response Runbook](/operations/runbooks/emergency-response.md)
- [Deployment Procedures](/operations/runbooks/deployment-procedures.md)
- [SRE Training Plan](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937394177/SRE+Training+Plan)
- [Platform Alerts](https://natterbox.atlassian.net/wiki/display/CO/Platform+Alerts)
