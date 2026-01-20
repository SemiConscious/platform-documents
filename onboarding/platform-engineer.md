# Platform Engineer Onboarding Guide

**Last Updated:** 2026-01-20  
**Target Audience:** New Platform Engineers / SRE team members  
**Source:** [SRE Training Plan](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937394177/SRE+Training+Plan)

---

## Overview

This guide covers onboarding for Platform Engineers (PE) / Site Reliability Engineers (SRE). Platform Engineering is responsible for infrastructure, deployments, monitoring, and operational excellence of the Natterbox platform.

---

## Training Plan Overview

The onboarding is structured in two phases:

**Phase 1: High-Level Training (6 days)**
- Product and architecture overview
- Monitoring and incident management
- Change management processes

**Phase 2: Detailed Training (5 days)**  
- Deep-dive architecture
- Emergency response
- Runbooks and procedures

---

## Week 1: High-Level Training

### Day 1: Product Overview

**Objective:** Understand what Natterbox does and its product offerings.

**Activities:**
- Product team overview session (1 hour)
- Review product videos and demos
- Understand customer use cases

**Key Products:**
- Voice services (PBX, call routing)
- Salesforce integration (AVS, SCV)
- Omnichannel (SMS, chat)
- Conversational AI
- Analytics and reporting

### Day 2: Architecture & Networking

**Objective:** Understand platform architecture and networking.

**Resources:**
- [Architecture Documentation](https://natterbox.atlassian.net/wiki/spaces/A)
- [Network Diagrams](https://natterbox.atlassian.net/wiki/display/CO/Natterbox+Network+Diagrams)
- [Onboarding Recordings](https://drive.google.com/drive/folders/15hZLellkxg_yreVRVEB0HyBHnhwk2wkA)

**Key Documents to Read:**
- [Global Architecture](/architecture/global-architecture.md)
- [Voice Routing Overview](/architecture/voice-routing/overview.md)

**Key Concepts:**
| Term | Description |
|------|-------------|
| RT | Real-Time regions (6 AWS regions) |
| SDC | Secondary Data Center (S01/S02) |
| LON | London infrastructure |
| GDC | Global Data Center |
| Nexus | Analytics platform |
| Territory | Logical customer grouping |

### Day 2 (cont): SRE Role Introduction

**Objective:** Understand day-to-day SRE responsibilities.

**Topics (30 mins):**
- On-call rotation
- Typical tasks and requests
- Team structure and collaboration
- Escalation paths

### Day 3: Monitoring

**Objective:** Learn the monitoring tools and alert systems.

**Monitoring Tools (30 mins):**
- [Monitoring Tools Documentation](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937197578/Monitoring+Tools)
- [Monitoring and Alerting Runbook](/operations/runbooks/monitoring-alerting.md)

**Tools to Access:**

| Tool | URL | Purpose |
|------|-----|---------|
| Nagios | https://nagios.redmatter.com | Infrastructure monitoring |
| Cacti | https://cacti.redmatter.com | Network graphs |
| OpsGenie | https://redmatterops.app.opsgenie.com | Alerting |
| CloudWatch | AWS Console | AWS metrics |
| Smokeping | https://smokeping.redmatter.com | Network latency |

**Frequent Alerts (1 hour):**
- [Platform Alerts](https://natterbox.atlassian.net/wiki/display/CO/Platform+Alerts)
- Common alert types and meanings
- Triage procedures

### Day 3 (cont): Internal Requests

**Objective:** Handle common internal support requests.

**Topics (30 mins):**
- Common request types
- Request handling workflow
- Documentation requirements

### Day 4: Incident Management

**Objective:** Understand incident response processes.

**Topics (30 mins):**
- Incident classification (P1-P4)
- Escalation process
- Communication procedures
- Post-incident reviews

**Key Channels:**
- #tech-team-incidents - Incident coordination
- #platform-engineering - Team communication

### Day 4 (cont): Change Management

**Objective:** Understand production change processes.

**Resources:**
- [Production Roll Out](https://natterbox.atlassian.net/wiki/display/CO/Production+Roll+Out)
- [Staging Roll Out](https://natterbox.atlassian.net/wiki/display/CO/Staging+Roll+Out)
- [Deployment Procedures Runbook](/operations/runbooks/deployment-procedures.md)
- [Onboarding Recordings](https://drive.google.com/drive/folders/15hZLellkxg_yreVRVEB0HyBHnhwk2wkA)

**Key Concepts:**
- Handover (HO) process
- Change Request (CR) workflow
- CCB (Change Control Board) meetings
- Rollback procedures

---

## Week 2: Detailed Training

### Day 5: Architecture Deep-Dive

**Objective:** Detailed understanding of platform architecture.

**Session (1.5 hours):**
- Walk through architecture diagrams
- Data flow patterns
- Regional deployments
- Failover mechanisms

**Resources:**
- [Architecture Documentation](https://natterbox.atlassian.net/wiki/spaces/A)
- [Onboarding Recordings](https://drive.google.com/drive/folders/15hZLellkxg_yreVRVEB0HyBHnhwk2wkA)

### Day 5 (cont): Emergency Response

**Objective:** Learn emergency response procedures.

**Resources:**
- [Emergency Responses](https://natterbox.atlassian.net/wiki/spaces/CO/pages/961150992/Emergency+Responses)
- [Dealing with Emergencies](https://natterbox.atlassian.net/wiki/spaces/CO/pages/679411680/Dealing+with+Emergencies)
- [Emergency Response Runbook](/operations/runbooks/emergency-response.md)

**Key Topics:**
- SDC failover procedures
- GeoDNS outage handling
- OOB (out-of-band) access
- Crisis management

### Day 5 (cont): Routine Procedures

**Objective:** Understand routine operational tasks.

**Topics (1.5 hours):**
- Backup verification
- Host restarts
- IPsec VPN creation
- Hard drive replacement
- Data center visits

### Day 6: Logging & Ops Development

**Objective:** Understand logging and coding practices.

**Logging (30 mins):**
- ELK stack usage
- Log aggregation
- Searching and analysis
- [Onboarding Recordings](https://drive.google.com/drive/folders/15hZLellkxg_yreVRVEB0HyBHnhwk2wkA)

**Ops Development (1 hour):**
- Coding practices for Ops
- Terraform module development
- Script development guidelines
- Testing requirements

### Day 6 (cont): Deployment Process

**Objective:** Deep understanding of deployment procedures.

**Topics (1 hour):**
- Production rollout process
- Staging rollout process
- RMHT (Release Management Helper Toolkit)
- Verification procedures

**Resources:**
- [Production Roll Out](https://natterbox.atlassian.net/wiki/display/CO/Production+Roll+Out)
- [Staging Roll Out](https://natterbox.atlassian.net/wiki/display/CO/Staging+Roll+Out)
- [Onboarding Recordings](https://drive.google.com/drive/folders/15hZLellkxg_yreVRVEB0HyBHnhwk2wkA)

### Day 7-10: Runbooks

**Objective:** Learn the 5 most frequent on-call scenarios.

**Structure:**
- 5 sessions × 30 minutes each
- Hands-on walkthrough of runbooks
- Practical exercises

**Key Runbooks:**
1. SDC failover
2. Service restart procedures
3. Database issues
4. Network troubleshooting
5. AWS resource issues

### Day 11: Q&A Session

**Objective:** Address remaining questions.

**Format (1 hour team session):**
- Prepare questions ahead of time
- Team discussion
- Knowledge gap identification

---

## Month 1-2: Practical Training

### Outage Scenario Roll-Plays

**Schedule:** One scenario per day for a month

**Format:**
1. Receive scenario description
2. Work through response
3. End-of-day review meeting
4. Document runbook improvements

**Focus Areas:**
- Start with the 5 most frequent on-call requests
- Progress to more complex scenarios
- Create/improve runbooks based on learnings

### Shadow On-Call

- Shadow an experienced PE on-call
- Observe incident handling
- Learn escalation patterns
- Understand communication protocols

---

## Key Skills Checklist

### Infrastructure

- [ ] Terraform module development
- [ ] AWS services (EC2, ECS, RDS, Lambda, etc.)
- [ ] Salt Stack configuration
- [ ] Docker and containerization
- [ ] Networking (VPC, VPN, DNS)

### Voice/Telephony

- [ ] FreeSWITCH basics
- [ ] SIP protocol understanding
- [ ] Call flow debugging
- [ ] Media troubleshooting

### Operations

- [ ] Monitoring tool proficiency
- [ ] Log analysis
- [ ] Incident response
- [ ] Change management
- [ ] Backup and recovery

### Tools

- [ ] RMHT usage
- [ ] AWS CLI
- [ ] Terraform CLI
- [ ] Salt commands
- [ ] Git workflow

---

## Important Repositories

### Infrastructure

| Repository | Purpose |
|------------|---------|
| `infrastructure-salt-stack` | Salt configuration |
| `infrastructure-versions` | Version management |
| `operations-rmht` | Release toolkit |

### Terraform Modules

| Repository | Purpose |
|------------|---------|
| `aws-terraform-network-rt` | RT networking |
| `aws-terraform-fsx8` | FreeSWITCH |
| `aws-terraform-rt-*` | RT services |

### Operations Tools

| Repository | Purpose |
|------------|---------|
| `operations-ops-scripts` | Ops scripts |
| `operations-rm-maintenancemode` | Maintenance mode |
| `aws-rm-rt-maintenance-agent` | RT maintenance |

---

## Access Requirements

### Day 1

| Access | Purpose |
|--------|---------|
| GitHub (redmatter) | Source code |
| Jira | Tickets |
| Confluence | Documentation |
| Slack | Communication |

### Week 1

| Access | Purpose |
|--------|---------|
| AWS SSO | Cloud access |
| Nagios | Monitoring |
| Cacti | Graphs |
| VPN | Network access |

### Week 2

| Access | Purpose |
|--------|---------|
| OpsGenie | Alerting |
| Production access | Controlled |
| Database access | Read-only initially |

---

## Review Checkpoints

### 3-Month Review

- Technical competency assessment
- Independent on-call readiness
- Goal setting

### 6-Month Review

- Full autonomy assessment
- Performance review
- Career development planning

---

## Related Documentation

- [Developer Onboarding](/onboarding/developer.md)
- [Emergency Response Runbook](/operations/runbooks/emergency-response.md)
- [Deployment Procedures](/operations/runbooks/deployment-procedures.md)
- [Monitoring and Alerting](/operations/runbooks/monitoring-alerting.md)
- [SRE Training Plan](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937394177/SRE+Training+Plan)
