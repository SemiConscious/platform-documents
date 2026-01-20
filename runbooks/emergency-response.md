# Emergency Response Runbook

**Last Updated:** 2026-01-20  
**Source:** [Confluence - Dealing with Emergencies](https://natterbox.atlassian.net/wiki/spaces/CO/pages/679411680/Dealing+with+Emergencies)

---

## Overview

This runbook covers emergency response procedures for the Natterbox platform. It provides step-by-step guidance for handling system failures, data center outages, and critical incidents.

**Golden Rule:** Do not be scared of running these queries. It's better to take action on an SDC failure than to sit there for 30 minutes debugging whilst calls can't be made.

---

## Quick Reference: Reporting Issues

| Channel | Purpose |
|---------|---------|
| [#platform-engineering](https://natterbox.slack.com/archives/C04A4S2R65V) | Primary channel for platform issues |
| [PLATFORM Jira](https://natterbox.atlassian.net/jira/software/c/projects/PLATFORM/boards/473) | Platform Operations tickets |
| ops@redmatter.com | Email escalation |

---

## Identifying Issues

### Internal Monitoring Tools

| Tool | URL | Access |
|------|-----|--------|
| Cacti | https://cacti.redmatter.com | LDAP credentials |
| Nagios (Prod) | https://nagios.redmatter.com | LDAP credentials |
| Nagios (Stage) | https://nagios.stage.redmatter.com | LDAP credentials |
| AWS CloudWatch | [EU West 1 Dashboard](https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#home:) | AWS SSO required |

### Slack Alert Channels

| Channel | Purpose |
|---------|---------|
| [#alerts-prod](https://natterbox.slack.com/archives/C02GT09SQNA) | Production alerts |
| [#alerts-stage](https://natterbox.slack.com/archives/C027LGBE3ML) | Staging alerts |
| [#tech-team-incidents](https://natterbox.slack.com/archives/C022VLCL76X) | Incident coordination |

### Third-Party Status

| Resource | URL |
|----------|-----|
| AWS Global Health | [Health Dashboard](https://health.console.aws.amazon.com/health/home#/account/dashboard/open-issues) |
| [#aws-health-reports](https://natterbox.slack.com/archives/C092Z8YAH7Z) | AWS health alerts |
| [#thirdparty-status](https://natterbox.slack.com/archives/C08TC5A54VD) | Third-party service status |
| Heroku Dashboard | [Natterbox Apps](https://dashboard.heroku.com/teams/natterbox/apps) |

---

## SDC (Secondary Data Center) Failure Procedures

### S01 Failure

If S01 experiences a complete failure, it should recover automatically. However, if S01 is flapping (coming up and going back down frequently), manually switch the primary DC to S02.

**Manual Failover to S02:**

```bash
wget -O - hapi.redmatter.com/locations/swapsdc/S02
```

**Monitor DNS propagation:**

```bash
watch "dig portal.redmatter.com @1.1"
```

**Notes:**
- hAPI should swap DCs automatically, but DNS reload may take time
- If S01 is completely dead, s01mon01 (preferred monitoring node) will be offline
- The monitoring cluster will swap nodes and propagate through DNS in a few seconds

### S02 Failure

If S01 is the primary DC, no action is needed - monitoring should stay up as s01mon01 is the preferred monitoring node.

If running on S02 (and S02 is flapping), manually switch to S01:

**Manual Failover to S01:**

```bash
wget -O - hapi.redmatter.com/locations/swapsdc/S01
```

**Monitor DNS propagation:**

```bash
watch "dig portal.redmatter.com"
```

---

## GeoDNS Outage Procedures

### Webphone GeoDNS Failover

If AWS Route53 has a GeoDNS outage, use the MS Azure hot backup.

**Verify Azure backup is working:**

```bash
dig webphone-test.redmatter.com
# Should resolve to rmwebphone.trafficmanager.net
```

### Swap AWS to MS Azure

Run in hAPI DB:

```sql
BEGIN;
DELETE FROM hAPI.RecordDomainMap 
WHERE RecordID = (
  SELECT RecordID FROM hAPI.DNSRecords 
  WHERE RecordName = 'webphone' 
  AND RecordData = 'webphone.aws.redmatter.com.'
);
INSERT INTO hAPI.RecordDomainMap 
SET DomainID = (
  SELECT DomainID FROM hAPI.Domains 
  WHERE Domainname = 'redmatter.com'
), RecordID = (
  SELECT RecordID FROM hAPI.DNSRecords 
  WHERE RecordName = 'webphone' 
  AND RecordData = 'rmwebphone.trafficmanager.net.'
);
COMMIT;
```

Then regenerate DNS:

```bash
curl http://hapi.redmatter.com/serials/generate/DNS
```

### Swap MS Azure Back to AWS

Run in hAPI DB:

```sql
BEGIN;
DELETE FROM hAPI.RecordDomainMap 
WHERE RecordID = (
  SELECT RecordID FROM hAPI.DNSRecords 
  WHERE RecordName = 'webphone' 
  AND RecordData = 'rmwebphone.trafficmanager.net.'
);
INSERT INTO hAPI.RecordDomainMap 
SET DomainID = (
  SELECT DomainID FROM hAPI.Domains 
  WHERE Domainname = 'redmatter.com'
), RecordID = (
  SELECT RecordID FROM hAPI.DNSRecords 
  WHERE RecordName = 'webphone' 
  AND RecordData = 'webphone.aws.redmatter.com.'
);
COMMIT;
```

Then regenerate DNS:

```bash
curl http://hapi.redmatter.com/serials/generate/DNS
```

---

## Heroku Issues

### Common Issue Types

**Dyno Capacity Reached:**
- Alert will be sent to the platform team
- This shouldn't occur during normal operation - may indicate dynos not operating correctly

**Resolution:**
1. Visit [Heroku apps page](https://dashboard.heroku.com/teams/natterbox/apps)
2. Select the app in question
3. Select the production deployed version
4. Click "More"
5. Click "Restart all dynos"

**Out-of-date App Stack:**
- Heroku apps are EOL and won't receive updates
- Cannot be modified outside of stopping/starting
- If full support is dropped, escalate to Engineering leadership for stack update planning

---

## Out-of-Band (OOB) Data Center Access

All 7 DCs have OOB access to the GFW iDRAC for emergency situations when IPsec tunnels cannot be established.

### Troubleshooting Unreachable iDRAC

If the iDRAC web interface is unreachable, try:

**From the server's OS (if accessible):**

```bash
bmc-device --cold-reset
```

Wait 5+ minutes for iDRAC to become reachable again.

**If OS is unreachable but can SSH to iDRAC:**

```bash
# From jump host
ssh root@s02gfw01-era

# Once logged in, reset iDRAC
/admin1-> racadm racreset
```

Wait 5+ minutes for iDRAC to become reachable again.

### S01 OOB Access (When Locked Out)

1. Establish IPSec tunnel to S02 (if not already up)

2. SSH to s02gfw01 with SOCKS proxy:
   ```bash
   ssh -C -D 9999 s02gfw01
   ```

3. Configure browser SOCKS proxy:
   - Host: `localhost`
   - Port: `9999`
   - SOCKS v5

4. Access https://s01gfw01-era

5. **Remember to disable SOCKS proxy when finished**

### S02 OOB Access (When Locked Out)

S02 DRAC ACL is configured to allow access from lonjmp01.

1. **If not in Croydon office:** Establish IPSec tunnel to D01

2. **If not in Croydon office:** SSH to lonjmp01 with SOCKS proxy:
   ```bash
   ssh -C -D 9999 lonjmp01
   ```

3. Configure browser SOCKS proxy (as above)

4. Access https://s02gfw01-era

5. **Remember to disable SOCKS proxy when finished**

### T01 OOB Access

T01's DRAC is part of management subnet:

| Device | IP |
|--------|-----|
| Netgear switch | 192.168.255.1 |
| t01xen01 | 192.168.255.2 |
| t02xen01 | 192.168.255.3 |
| t01xen01-era | 192.168.255.4 |
| t02xen01-era | 192.168.255.5 |
| s02gfw01 | 192.168.255.6 |

Access t01xen01-era from t02xen01 or s02gfw01:

```bash
ssh -C -D 9999 t02xen01
# Then browse to https://192.168.255.4
```

### T02 OOB Access

Uses the same management subnet as T01.

Access t02xen01-era from t01xen01 or s02gfw01:

```bash
ssh -C -D 9999 t01xen01
# Then browse to https://192.168.255.5
```

---

## AWS Emergency Administrative Access

For AWS emergency administrative access procedures, see:
[AWS Emergency Administrative Access](https://github.com/redmatter/aws-docs/blob/develop/aws-emergency-administrative-access.md)

---

## Crisis Management Process

For full system outages, follow the Crisis Management Process:
[Crisis Management Process (Google Doc)](https://docs.google.com/document/d/1eJ6726I0HgZJHWINgYkLuHDEK2ScCM2SUezsQMFaDNQ/edit)

---

## Windows Java Issues (iDRAC Console)

If Java console doesn't work on Windows, try Java 1.8.161:
- Search for `jre-8u161-windows-x64.exe`

---

## Related Documentation

- [Monitoring Tools](/operations/runbooks/monitoring-alerting.md)
- [Deployment Procedures](/operations/runbooks/deployment-procedures.md)
- [Supplier Escalations](https://natterbox.atlassian.net/wiki/spaces/CO/pages/679411452/Supplier+Escalations)
