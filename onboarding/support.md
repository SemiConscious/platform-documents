# Support Team Onboarding Guide

**Last Updated:** 2026-01-20

---

## Welcome to Natterbox Support

This guide is specifically designed for new Support Team members. It provides a comprehensive overview of the platform from a support perspective, troubleshooting procedures, diagnostic tools, escalation processes, and integration with our ticketing systems.

---

## Table of Contents

1. [Platform Overview for Support](#platform-overview-for-support)
2. [Key Services & Health Indicators](#key-services--health-indicators)
3. [Monitoring & Alerting Systems](#monitoring--alerting-systems)
4. [Common Troubleshooting Procedures](#common-troubleshooting-procedures)
5. [Diagnostic Tools & Queries](#diagnostic-tools--queries)
6. [Log Locations & Analysis](#log-locations--analysis)
7. [Escalation Procedures](#escalation-procedures)
8. [Ticketing System Integration](#ticketing-system-integration)
9. [First Week Checklist](#first-week-checklist)

---

## Platform Overview for Support

### What is Natterbox?

Natterbox is a cloud-based telephony platform deeply integrated with Salesforce. The platform handles:

- **Voice Communications** - Inbound/outbound calls, call routing, queues
- **Omnichannel** - Chat, SMS, email integration
- **AI Services** - Conversational AI, transcription, sentiment analysis
- **Salesforce Integration** - CTI, screen pop, call logging

### Architecture at a Glance

```
                    ┌─────────────────┐
                    │   Salesforce    │
                    │   (CTI/AVS)     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐       ┌──────▼──────┐      ┌────▼────┐
    │ EMEA    │       │  Platform   │      │  AMER   │
    │ Region  │       │   API       │      │ Region  │
    │ (N01)   │       │             │      │ (N02)   │
    └────┬────┘       └─────────────┘      └────┬────┘
         │                                      │
    ┌────▼────┐                            ┌────▼────┐
    │FreeSWITCH│                           │FreeSWITCH│
    │  (PBX)   │                           │  (PBX)   │
    └─────────┘                            └─────────┘
```

### Regional Infrastructure

| Region | Designation | Primary Use | Data Centers |
|--------|-------------|-------------|--------------|
| EMEA | N01 | UK/Europe customers | eu-west-2 (London) |
| Americas | N02 | US/Canada customers | us-east-1 |
| APAC | N03 | Australia/Asia | ap-southeast-2 |

### Key Platform Components

| Component | Purpose | Support Relevance |
|-----------|---------|-------------------|
| **FreeSWITCH** | Core telephony switch | Call routing, quality issues |
| **Platform API** | REST/GraphQL interface | Feature functionality |
| **OpenSIPS** | SIP proxy/load balancer | Connection issues |
| **CDRMunch** | Call detail records | Billing queries, call history |
| **Notifier** | Real-time notifications | CTI updates, availability |
| **FSCallCenterMonitor** | Queue management | Queue routing, agent states |

---

## Key Services & Health Indicators

### Critical Services to Monitor

#### Tier 1 - Customer-Impacting (Immediate Response)

| Service | Health Check | Impact if Down |
|---------|--------------|----------------|
| FreeSWITCH (PBX) | `systemctl status freeswitch` | No calls possible |
| OpenSIPS | `systemctl status opensips` | SIP registration fails |
| Platform API | HTTP 200 on `/health` | No config changes, CTI broken |
| Notifier | `systemctl status rm-notifier` | No real-time updates |

#### Tier 2 - Feature-Impacting (30-min Response)

| Service | Health Check | Impact if Down |
|---------|--------------|----------------|
| CDRMunch | `systemctl status cdrmunch` | No CDR processing |
| FSCallCenterMonitor | Check process | Queue routing fails |
| Archiving | `systemctl status archiving` | Recording archival stops |
| Transcription | Service status | No transcriptions |

#### Tier 3 - Monitoring/Analytics (Business Hours)

| Service | Health Check | Impact if Down |
|---------|--------------|----------------|
| Lumina | AWS health check | No analytics |
| Insight | Service status | No call insights |
| Wallboards | Application check | No real-time dashboards |

### Health Check Dashboard URLs

| Dashboard | Purpose | URL |
|-----------|---------|-----|
| CloudWatch | AWS metrics | AWS Console → CloudWatch |
| Grafana | Platform metrics | Internal Grafana instance |
| Status Page | Customer-facing | status.natterbox.com |

### Key Metrics to Watch

```
┌─────────────────────────────────────────────────────────┐
│  CRITICAL METRICS                                        │
├─────────────────────────────────────────────────────────┤
│  • Call Success Rate      Target: > 99.5%               │
│  • API Response Time      Target: < 200ms               │
│  • SIP Registration Rate  Target: > 99%                 │
│  • Queue Wait Time        Alert: > 300 seconds          │
│  • Error Rate             Alert: > 1%                   │
└─────────────────────────────────────────────────────────┘
```

---

## Monitoring & Alerting Systems

### OpsGenie Integration

OpsGenie is our primary alerting platform. All platform alerts are routed through OpsGenie to the on-call engineer.

**Key OpsGenie Channels:**
- Platform alerts → `#incidents` Slack channel
- On-call notifications → Phone/SMS to duty engineer

**Alert Priority Levels:**

| Priority | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| P1 | Full service outage | Immediate | All calls failing |
| P2 | Severe degradation | 15 minutes | One region down |
| P3 | Partial impact | 1 hour | Feature unavailable |
| P4 | Minor issue | Business hours | Single customer |
| P5 | Informational | Next working day | Threshold warning |

### CloudWatch Alarms

Critical CloudWatch alarms include:

| Alarm | Threshold | Action |
|-------|-----------|--------|
| API Error Rate | > 5% for 5 min | Page on-call |
| Lambda Duration | > 10s average | Warning |
| SQS Queue Depth | > 1000 messages | Warning |
| EC2 CPU | > 80% for 10 min | Auto-scale/alert |
| RDS Connections | > 80% max | Alert |

### Grafana Dashboards

Key dashboards for support:

1. **Platform Overview** - High-level health
2. **Call Volume** - Real-time call statistics
3. **Queue Performance** - Wait times, abandonment
4. **API Performance** - Response times, errors
5. **SIP Performance** - Registration, errors

---

## Common Troubleshooting Procedures

### Call Quality Issues

#### Step 1: Gather Information
```
Required information from customer:
- Date/Time of call (with timezone)
- Caller number (From Number)
- Dialled number (To Number)
- Description of issue (one-way audio, choppy, dropped)
```

#### Step 2: Locate the Call
```bash
# On log server (s01log01), find the call
grep <phone_number> /var/log/app/freeswitch.log | logrep /var/log/app/*.log
```

#### Step 3: Analyze Call Flow
Look for:
- `New Channel` - Call initiated
- `NORMAL_CLEARING` - Normal hangup
- `ORIGINATOR_CANCEL` - Caller hung up
- `NO_ANSWER` - No answer from destination
- `USER_BUSY` - Destination busy

#### Step 4: Check RTCP Stats
```
Look for RTCP stats in the call summary:
RTCPSender: packets:lost:jitter
RTCPReceiver: packets:lost:jitter

High jitter (>30ms) or packet loss (>1%) indicates network issues
```

### Call Queue Issues

#### "Calls Not Routing to Agents"

**Common Causes:**
1. Agents not logged in
2. Skills mismatch
3. Availability state incorrect
4. Queue timeout reached

**Diagnostic Steps:**

```bash
# 1. Find the call UUID in freeswitch logs
grep <from_number> /var/log/app/freeswitch.log | logrep /var/log/app/*.log

# 2. Check queue routing with UUID
grep <UUID> /var/log/app/fscallcentermonitor.log

# 3. Look for agent availability
# Key log entries:
# - "No available agents on queue" = No agents ready
# - Skills list with P values = Agent skill matching
```

**Understanding Skills Based Routing (SBR):**

```json
// Example SBR data in logs
{"175993":{"P":5080,"T":0},"175995":{"P":5080,"T":0}}

// P = Preference (skill level): -1 to 10,000
//     -1 means agent skipped (no skills)
//     Higher number = more preferred
// T = Time delay in seconds before considering agent
```

#### Agent Availability Check

```bash
# Check agent availability state changes
for email in agent1@company.com agent2@company.com; do
  echo "$email"
  grep "$email" /var/log/app/rm-notifier.log | grep "Changed availability state ID"
done
```

**Availability States:**
- `Available` - Ready to receive calls
- `Away` - Temporarily unavailable
- `Busy` - On another call or task
- `Offline` - Logged out

### SIP Registration Issues

#### "Phone/Softphone Won't Register"

**Check Steps:**
1. Verify credentials in Natterbox portal
2. Check SIP server connectivity
3. Review OpenSIPS logs for registration attempts

```bash
# Check OpenSIPS registration logs
grep <sip_username> /var/log/opensips/opensips.log

# Common errors:
# 401 Unauthorized = Bad credentials
# 403 Forbidden = IP not allowed
# 408 Timeout = Network/firewall issue
```

### CTI (Computer Telephony Integration) Issues

#### "Screen Pop Not Working"

**Diagnostic Steps:**
1. Check notifier service status
2. Verify Salesforce CTI adapter version
3. Check browser console for errors
4. Verify user permissions in Natterbox

```bash
# Check notifier logs for user
grep <user_email> /var/log/app/rm-notifier.log | tail -50
```

---

## Diagnostic Tools & Queries

### Essential Bash Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `grep` | Search logs | `grep "error" /var/log/app/file.log` |
| `zgrep` | Search compressed logs | `zgrep "error" /var/log/app/file.log.gz` |
| `tail` | View end of file | `tail -100 /var/log/app/file.log` |
| `head` | View start of file | `head -50 /var/log/app/file.log` |
| `logrep` | Format RM logs | `grep UUID file.log \| logrep *.log` |
| `wc -l` | Count lines | `grep error file.log \| wc -l` |

### Using logrep (In-House Tool)

`logrep` is a custom log parser that formats and groups log output by call leg:

```bash
# Basic usage
grep <search_term> /var/log/app/freeswitch.log | /usr/sbin/logrep /var/log/app/*.log

# Output shows:
# - Separate "Entries for" blocks per call leg
# - Inbound leg, LCR lookup, outbound leg
# - Call summary with hangup cause
```

### CDR Analyzer

The CDR Analyzer in the Natterbox portal provides:
- Call history lookup
- Call flow visualization  
- Queue entry/exit times
- Recording playback

**Access:** Natterbox Portal → Tools → CDR Analyzer

### Common Queries

#### Find All Calls for a Number (Last 24 Hours)
```bash
grep <phone_number> /var/log/app/freeswitch.log | logrep /var/log/app/*.log
```

#### Check Agent State Changes
```bash
grep "<user_email>" /var/log/app/rm-notifier.log | grep "availability"
```

#### Count Errors in Time Period
```bash
grep "ERROR" /var/log/app/freeswitch.log | grep "2026-01-20T1[0-2]" | wc -l
```

#### Find Queue Timeout Calls
```bash
grep "No available agents on queue" /var/log/app/fscallcentermonitor.log | grep <date>
```

### API Diagnostic Endpoints

| Endpoint | Purpose | Access |
|----------|---------|--------|
| `/health` | Service health | Public |
| `/metrics` | Prometheus metrics | Internal |
| `/status` | Detailed status | Authenticated |

---

## Log Locations & Analysis

### Primary Log Servers

| Server | Region | Purpose |
|--------|--------|---------|
| s01log01 | N01 (EMEA) | EMEA logs |
| s02log01 | N02 (AMER) | Americas logs |

### Log File Locations

```
/var/log/app/
├── freeswitch.log          # Main telephony logs
├── fscallcentermonitor.log # Queue routing & SBR
├── rm-notifier.log         # Real-time notifications/CTI
├── rm-api.log              # Platform API
├── opensips/
│   └── opensips.log        # SIP proxy logs
└── cdrmunch/
    └── cdrmunch.log        # CDR processing
```

### Log Archive Pattern

> ⚠️ **Important:** Logs are archived at 04:00 AM. A call on the 10th may be in the file named 11th.

```
Log naming convention:
- freeswitch.log        # Current day
- freeswitch.log.1      # Yesterday
- freeswitch.log.2.gz   # 2 days ago (compressed)
```

### Log Entry Format

```
2026-01-20T10:30:15.123456+00:00 <server> <service>[<pid>]: [<level>] <message>

Example:
2026-01-20T10:30:15.123456+00:00 g01pbx01 freeswitch[23905]: [notice] New Channel sofia/external1/+447123456789@80.84.30.15
```

### Key Log Patterns to Know

| Pattern | Meaning |
|---------|---------|
| `New Channel sofia/` | Call initiated |
| `NORMAL_CLEARING` | Normal hangup |
| `NO_ANSWER` | No answer |
| `USER_BUSY` | Destination busy |
| `ORIGINATOR_CANCEL` | Caller hung up |
| `CALL_REJECTED` | Call rejected |
| `Changed availability state` | Agent state change |
| `No available agents on queue` | No agents to route to |

---

## Escalation Procedures

### Escalation Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESCALATION MATRIX                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 1: Support Team                                          │
│     ↓ Cannot resolve / P1-P2 incident                           │
│  Level 2: Network Operations (NetOps)                           │
│     ↓ R&D involvement needed                                    │
│  Level 3: Engineering Team                                      │
│     ↓ Critical escalation                                       │
│  Level 4: Senior Management                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Contact Methods

| Team | Primary | Emergency |
|------|---------|-----------|
| NetOps | #ops_support Slack | +44 1344 231 535 |
| Support On-Call | #support Slack | +44 2035 100 999 |
| Engineering | #rm_netops Slack | Via NetOps |

### Crisis Management Process

#### Scenario 1: Customer Impact During Business Hours (Internal Alert)

1. **Alert Received** - OpsGenie notifies on-call engineer
2. **Ticket Created** - NetOps creates Jira incident ticket
3. **Impact Assessment** - NetOps confirms customer impact
4. **Support Notification** - NetOps notifies Support via `#ops_support` Slack (within 5 minutes)
5. **Stakeholder Updates** - Support notifies (within 15 minutes):
   - Senior Management
   - Customer Success
   - Customers (via Service Status page)
6. **Collaboration** - Joint investigation via `#ops_support` or Google Meet
7. **Resolution** - NetOps notifies Support when resolved
8. **Communication** - Support updates all stakeholders

#### Scenario 2: Customer Impact During Business Hours (Customer Reported)

1. **Customer Contact** - Support receives report
2. **NetOps Notification** - Support contacts on-call via `#ops_support`
3. **Ticket Created** - Support creates Jira Bug ticket
4. **Validation** - NetOps confirms issue
5. **Follow standard incident process from Step 5 above**

#### Scenario 3: After Hours (Internal Alert)

1. **Alert Received** - OpsGenie notifies on-call via emergency number
2. **Ticket Created** - NetOps creates incident ticket
3. **Support Notification** - NetOps contacts Support on-call (+44 2035 100 999) within 15 minutes
4. **Duty Manager** - Escalate to duty manager for communications
5. **Follow standard process**

#### Scenario 4: After Hours (Customer Reported)

1. **Customer Contact** - Via emergency support line
2. **NetOps Notification** - Support contacts on-call via emergency number
3. **Follow Scenario 3 process**

### Supplier Escalations

For third-party/carrier issues, refer to:
- **Confluence:** Operations → Supplier Escalations
- Contains contact details for all carriers and SLAs

---

## Ticketing System Integration

### Jira Workflow

#### Ticket Types

| Type | Use Case | Example |
|------|----------|---------|
| Bug | Platform defects | Call routing broken |
| Incident | Service disruption | Region outage |
| Task | Work items | Config change request |
| Support | Customer issues | Billing query |

#### Ticket Lifecycle

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────┐
│  Open   │───►│ In Progress │───►│ In Review   │───►│ Closed │
└─────────┘    └─────────────┘    └─────────────┘    └────────┘
     │                                    │
     │         ┌──────────────┐           │
     └────────►│  Escalated   │───────────┘
               └──────────────┘
```

#### Required Information for Tickets

**For Call Issues:**
```
- Customer/Org Name:
- Date/Time (with timezone):
- From Number:
- To Number:
- Issue Description:
- Steps to Reproduce:
- Impact (users affected):
```

**For Configuration Issues:**
```
- Customer/Org Name:
- Feature/Area:
- Expected Behavior:
- Actual Behavior:
- Steps to Reproduce:
- Screenshots (if applicable):
```

### Slack Integration

Key support channels:

| Channel | Purpose | Usage |
|---------|---------|-------|
| `#ops_support` | NetOps/Support collaboration | Incident communication |
| `#incidents` | Platform alerts | Monitoring |
| `#support` | Support team | General support |
| `#rm_netops` | Engineering escalation | R&D involvement |

### Service Status Page

**URL:** status.natterbox.com

For customer-facing incidents:
1. Support creates status update
2. Updates at defined intervals (based on severity)
3. Resolution notice when fixed

---

## First Week Checklist

### Day 1: Setup & Access

- [ ] GitHub account added to redmatter organization
- [ ] Jira access verified
- [ ] Confluence access verified  
- [ ] Slack workspace joined
- [ ] Google Workspace setup
- [ ] VPN access configured
- [ ] Log server access granted (s01log01, s02log01)

### Day 2-3: Platform Understanding

- [ ] Read this onboarding guide completely
- [ ] Review [Global Architecture](/architecture/global-architecture.md)
- [ ] Review [Service Inventory](/services/inventory.md)
- [ ] Explore Natterbox portal (demo org)
- [ ] Understand Salesforce CTI basics

### Day 4-5: Tools & Processes

- [ ] Practice log analysis commands on test data
- [ ] Review CDR Analyzer usage
- [ ] Understand OpsGenie alerts
- [ ] Review existing incident tickets
- [ ] Shadow support calls/tickets

### Week 2: Hands-On Training

- [ ] Complete call diagnostics training
- [ ] Handle first tickets (with supervision)
- [ ] Participate in incident (if occurs)
- [ ] Practice escalation process
- [ ] Complete PCAP analysis basics

### Ongoing

- [ ] Regular knowledge base review
- [ ] Participate in team standups
- [ ] Continuous documentation feedback

---

## Quick Reference Card

### Emergency Contacts

| Role | Contact |
|------|---------|
| NetOps On-Call | +44 1344 231 535 |
| Support On-Call | +44 2035 100 999 |
| Slack (Priority) | #ops_support |

### Key URLs

| Resource | URL |
|----------|-----|
| Natterbox Portal | portal.natterbox.com |
| Service Status | status.natterbox.com |
| Jira | natterbox.atlassian.net |
| Confluence | natterbox.atlassian.net/wiki |
| Grafana | [Internal] |

### Log Server Quick Access

```bash
# EMEA
ssh s01log01

# Americas  
ssh s02log01

# Quick search
grep <term> /var/log/app/freeswitch.log | logrep /var/log/app/*.log
```

---

## Additional Resources

### Confluence Pages (Must Read)

- [Support Training Documentation](https://natterbox.atlassian.net/wiki/spaces/~chris.wilmott/pages/877363269/Support+Training+Documentation)
- [Crisis Management Process](https://natterbox.atlassian.net/wiki/spaces/CO/pages/691601249/Crisis+Management+Process2)
- [Supplier Escalations](https://natterbox.atlassian.net/wiki/spaces/CO/pages/679411452/Supplier+Escalations)
- [Call Queue Operation](https://natterbox.atlassian.net/wiki/spaces/ENG/pages/Call+Queue+Operation) (Skills Based Routing)

### Related Documentation

- [Operations Runbooks](/operations/runbooks/)
- [Emergency Response](/operations/runbooks/emergency-response.md)
- [Monitoring & Alerting](/operations/runbooks/monitoring-alerting.md)
- [Platform Engineer Onboarding](/onboarding/platform-engineer.md)

---

## Feedback

This guide is maintained by the Support and Platform teams. If you find errors or have suggestions:

1. Create a PR with your changes
2. Discuss with your team lead
3. Or post in #support Slack channel

Welcome to the team! 🎉

---

*Last updated: 2026-01-20*
*Document owner: Support Team*
