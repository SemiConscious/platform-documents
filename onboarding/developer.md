# Developer Onboarding Guide

**Last Updated:** 2026-01-20  
**Target Audience:** New developers joining Natterbox engineering teams

---

## Overview

Welcome to Natterbox! This guide will help you get started with the platform, understand our technology stack, and become productive as quickly as possible.

---

## Week 1: Foundation

### Day 1-2: Access & Tools Setup

#### Essential Accounts

| System | Purpose | Request From |
|--------|---------|--------------|
| GitHub (redmatter org) | Source code | IT via onboarding |
| Jira | Project tracking | IT via onboarding |
| Confluence | Documentation | IT via onboarding |
| Slack | Communication | IT via onboarding |
| Google Workspace | Email, Calendar | IT |
| AWS SSO | Cloud access | Platform team |
| Auth0 | Identity management | Platform team |

#### Development Environment

1. **Laptop Setup**
   - macOS or Linux recommended
   - Minimum 16GB RAM, 256GB SSD

2. **Required Software**
   ```bash
   # Package managers
   brew install git node nvm docker terraform awscli
   
   # Node.js (use nvm for version management)
   nvm install 18
   nvm use 18
   
   # Python (for some tools)
   brew install python@3.11
   
   # Go (for many services)
   brew install go
   ```

3. **AWS CLI Configuration**
   ```bash
   aws configure sso
   # Follow prompts for AWS SSO setup
   ```

4. **Git Configuration**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@natterbox.com"
   ```

### Day 3-4: Platform Overview

#### Product Understanding

**Watch these resources:**
- Product overview (get link from manager)
- [Onboarding recordings](https://drive.google.com/drive/folders/15hZLellkxg_yreVRVEB0HyBHnhwk2wkA)

**Key Products:**
- **AVS (Application for Voice in Salesforce):** CTI integration for Salesforce
- **Omnichannel:** Multi-channel communication (voice, SMS, chat)
- **CAI (Conversational AI):** AI-powered voice interactions
- **Lumina:** Observability and analytics platform
- **WebPhone:** Browser-based softphone

#### Architecture Overview

Read these documents in order:

1. [Global Architecture](/architecture/global-architecture.md) - Platform overview
2. [Voice Routing Overview](/architecture/voice-routing/overview.md) - Voice subsystem
3. [Repository Inventory](/services/repository-inventory.md) - All ~450 repositories

#### Key Architectural Concepts

| Concept | Description |
|---------|-------------|
| **RT (Real-Time)** | AWS regions for customer voice/real-time services |
| **SDC** | Secondary Data Center (legacy infrastructure) |
| **GDC** | Global Data Center (AWS global services) |
| **Nexus** | Analytics and non-real-time services |
| **Territory** | Logical customer grouping within a region |

### Day 5: Team Introduction

- Meet your team members
- Understand team responsibilities
- Review current sprint/projects
- Shadow a team member

---

## Week 2: Deep Dive

### Technology Stack

#### Languages by Domain

| Domain | Primary Languages |
|--------|-------------------|
| Core Platform | PHP (Kohana), TypeScript |
| Voice Routing | C/C++, Lua, PHP |
| Modern Services | TypeScript, Go |
| Infrastructure | Terraform (HCL), Python |
| Salesforce | Apex, JavaScript |
| Mobile | Swift (iOS), Kotlin (Android) |

#### Key Technologies

| Component | Technology |
|-----------|------------|
| Voice Switch | FreeSWITCH (C) |
| SIP Proxy | OpenSIPS |
| Message Queues | AWS SQS, RabbitMQ |
| Databases | MariaDB/MySQL, DynamoDB |
| Search | Elasticsearch |
| Cache | Redis |
| AI/ML | AWS Bedrock, Vertex AI |
| IaC | Terraform |
| Config Management | Salt Stack |

### Repository Navigation

#### Repository Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `platform-*` | Core platform services | `platform-api` |
| `aws-terraform-*` | Terraform modules | `aws-terraform-fsx8` |
| `infrastructure-*` | Infrastructure tools | `infrastructure-salt-stack` |
| `libraries-*` | Shared libraries | `libraries-kohana` |
| `natterbox-*` | Customer-facing apps | `natterbox-avs-sfdx` |
| `omnichannel-*` | Omni services | `omnichannel-omniservice` |
| `go-*` | Go services/libraries | `go-geoshim` |

#### High-Priority Repositories by Role

**Backend Developer:**
- `redmatter/platform-api` - Core API
- `redmatter/platform-sapien` - Platform services
- `redmatter/omnichannel-omniservice` - Omni pipeline

**Voice/Telephony Developer:**
- `redmatter/platform-freeswitch` - FreeSWITCH
- `redmatter/platform-fsxinetdsocket` - Call processing
- `redmatter/platform-dialplan` - Call routing

**Frontend Developer:**
- `redmatter/unified-settings` - Settings UI
- `redmatter/natterbox-routing-policies` - Routing policies UI
- `redmatter/portal-portal-web` - Portal frontend

**Salesforce Developer:**
- `redmatter/natterbox-avs-sfdx` - AVS package
- `redmatter/platform-scv-byot-connector` - SCV connector
- `redmatter/sf-internal-delta-connector` - Delta connector

**Infrastructure/Platform Engineer:**
- `redmatter/infrastructure-salt-stack` - Salt configuration
- `redmatter/aws-terraform-*` - Terraform modules
- `redmatter/operations-rmht` - Release toolkit

### Development Workflow

#### Git Workflow

```bash
# Clone a repository
git clone git@github.com:redmatter/<repo-name>.git

# Create feature branch
git checkout -b feature/<ticket-id>-description

# Make changes and commit
git add .
git commit -m "<TICKET-ID>: Brief description"

# Push and create PR
git push origin feature/<ticket-id>-description
```

#### Code Review Process

1. Create PR with linked Jira ticket
2. Request review from team members
3. Address feedback
4. Merge after approval

See [Pull Request Guidelines](https://natterbox.atlassian.net/wiki/spaces/~dino.korah/pages/2665087026/Pull+Request+Guidelines)

---

## Week 3-4: Practical Experience

### First Tasks

Your manager will assign starter tasks, typically:
- Bug fixes with clear scope
- Documentation improvements
- Small feature enhancements

### Environment Access

#### QA Environments

| Environment | Purpose |
|-------------|---------|
| QA01 | Testing environment 1 |
| QA02 | Testing environment 2 |
| Stage | Pre-production |

#### Monitoring Tools

Get familiar with:
- [Nagios (Stage)](https://nagios.stage.redmatter.com) - System monitoring
- [Cacti (Stage)](https://cacti.stage.redmatter.com) - Network graphs
- [Toolbox (Stage)](https://toolbox.stage.redmatter.com) - Utilities

See [Monitoring and Alerting Runbook](/operations/runbooks/monitoring-alerting.md)

### Understanding Release Process

Read the [Deployment Procedures Runbook](/operations/runbooks/deployment-procedures.md)

Key concepts:
- **Handover (HO):** Documentation for changes going to production
- **Change Request (CR):** Formal release ticket
- **CCB:** Change Control Board (Friday 11:15 GMT)

---

## Key Documentation

### Must-Read Documents

| Document | Location |
|----------|----------|
| Global Architecture | `/architecture/global-architecture.md` |
| Voice Routing | `/architecture/voice-routing/overview.md` |
| Repository Inventory | `/services/repository-inventory.md` |
| Emergency Response | `/operations/runbooks/emergency-response.md` |
| Deployment Procedures | `/operations/runbooks/deployment-procedures.md` |

### Confluence Spaces

| Space | Content |
|-------|---------|
| Architecture (A) | Technical architecture |
| Engineering (ENG) | Development guides |
| Release Management | Release process |
| Company Ops (CO) | Operational procedures |

### Useful Links

| Resource | URL |
|----------|-----|
| Jira (PLATFORM) | https://natterbox.atlassian.net/jira/software/c/projects/PLATFORM |
| Confluence | https://natterbox.atlassian.net/wiki |
| GitHub (redmatter) | https://github.com/redmatter |
| Document360 | https://docs.natterbox.com |

---

## Getting Help

### Communication Channels

| Channel | Purpose |
|---------|---------|
| #platform-engineering | Platform team questions |
| #dev-help | General development help |
| #tech-team-incidents | Active incidents |
| Your team channel | Team-specific |

### Key Contacts

Talk to your manager about who to contact for:
- Architecture questions
- Infrastructure access
- Salesforce development
- Voice/telephony questions

### Asking Good Questions

1. Search existing documentation first
2. Check Confluence and this repository
3. Provide context (what you've tried)
4. Include error messages/logs
5. Specify which environment

---

## 30/60/90 Day Goals

### 30 Days

- [ ] Complete all account setup
- [ ] Read architecture documentation
- [ ] Understand repository structure
- [ ] Complete first tasks
- [ ] Shadow deployments

### 60 Days

- [ ] Independently fix bugs
- [ ] Understand release process
- [ ] Contribute to code reviews
- [ ] Know team workflows
- [ ] Handle QA environment issues

### 90 Days

- [ ] Design and implement features
- [ ] Participate in on-call (if applicable)
- [ ] Mentor newer team members
- [ ] Contribute to documentation
- [ ] Propose process improvements

---

## Appendix: Common Tasks

### Running Local Development

Most services have README files with setup instructions. Common patterns:

**Node.js Services:**
```bash
npm install
npm run dev
```

**Go Services:**
```bash
go mod download
go run .
```

**PHP Services:**
```bash
composer install
# Follow specific service instructions
```

### Terraform Operations

```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply (only in approved contexts)
terraform apply
```

See [AWS Docker Terraform](https://github.com/redmatter/aws-docker-terraform) for the `tf` wrapper.

### Database Access

QA database access varies by service. Check with your team lead for:
- Connection strings
- Credentials (in AWS Secrets Manager)
- Which database serves which service

---

## Related Documentation

- [Platform Engineer Onboarding](/onboarding/platform-engineer.md)
- [Support Engineer Onboarding](/onboarding/support-engineer.md)
- [SRE Training Plan](https://natterbox.atlassian.net/wiki/spaces/CO/pages/937394177/SRE+Training+Plan)
