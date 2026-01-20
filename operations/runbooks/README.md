# Operations Runbooks

**Last Updated:** 2026-01-20

---

## Overview

This directory contains operational runbooks for the Natterbox platform. These documents provide step-by-step procedures for common operational tasks, incident response, and system maintenance.

---

## Runbook Index

| Runbook | Description |
|---------|-------------|
| [Emergency Response](./emergency-response.md) | Incident response, SDC failover, GeoDNS failover, OOB access |
| [Deployment Procedures](./deployment-procedures.md) | Release types, timelines, handover requirements, rollback |
| [Monitoring and Alerting](./monitoring-alerting.md) | Monitoring tools, alert channels, dashboards, escalation |

---

## Quick Reference

### Critical Contacts

| Contact | Purpose |
|---------|---------|
| [#platform-engineering](https://natterbox.slack.com/archives/C04A4S2R65V) | Platform issues |
| [#tech-team-incidents](https://natterbox.slack.com/archives/C022VLCL76X) | Active incidents |
| ops@redmatter.com | Email escalation |

### Key URLs

| Tool | URL |
|------|-----|
| Nagios (Prod) | https://nagios.redmatter.com |
| Cacti | https://cacti.redmatter.com |
| OpsGenie | https://redmatterops.app.opsgenie.com |
| Toolbox | https://toolbox.redmatter.com |

### Emergency Commands

```bash
# SDC Failover to S02
wget -O - hapi.redmatter.com/locations/swapsdc/S02

# SDC Failover to S01
wget -O - hapi.redmatter.com/locations/swapsdc/S01

# Monitor DNS propagation
watch "dig portal.redmatter.com"

# Regenerate DNS after hAPI change
curl http://hapi.redmatter.com/serials/generate/DNS
```

---

## Using These Runbooks

### When to Use

- **Emergency Response:** System outages, data center failures, critical incidents
- **Deployment Procedures:** Scheduled releases, emergency fixes, CAI deployments
- **Monitoring and Alerting:** Alert triage, dashboard access, escalation paths

### How to Contribute

1. Create a PR to update runbooks when procedures change
2. Include the date of last update in the document header
3. Reference source Confluence pages where applicable
4. Test commands and procedures before documenting

---

## Related Documentation

- [Architecture Documentation](/architecture/)
- [Service Documentation](/services/)
- [Onboarding Guides](/onboarding/)

---

## Confluence Sources

These runbooks consolidate information from:

- [Dealing with Emergencies](https://natterbox.atlassian.net/wiki/spaces/CO/pages/679411680/Dealing+with+Emergencies)
- [Release Types and Procedures](https://natterbox.atlassian.net/wiki/spaces/ReleaseManagement/pages/2694119427/Release+Types+and+Procedures)
- [Monitoring Tools](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937197578/Monitoring+Tools)
- [SRE Training Plan](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937394177/SRE+Training+Plan)
- [Emergency Responses](https://natterbox.atlassian.net/wiki/spaces/CO/pages/961150992/Emergency+Responses)
