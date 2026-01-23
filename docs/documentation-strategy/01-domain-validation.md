# Domain Validation Report

## Executive Summary

Analysis of **908 repositories** (891 redmatter + 17 natterbox) reveals a clear organizational structure that maps to **11 validated domains**. This document refines the original 7-domain proposal based on actual repository distribution.

## Repository Landscape

### Total Repositories: 908

| Organization | Count |
|-------------|-------|
| redmatter | 891 |
| natterbox | 17 |

### Repository Distribution by Primary Prefix

| Prefix | Count | Percentage | Domain Assignment |
|--------|-------|------------|-------------------|
| `aws-*` | 164 | 18.1% | Infrastructure |
| `platform-*` | 91 | 10.0% | Core Platform |
| `infrastructure-*` | 85 | 9.4% | Infrastructure |
| `go-*` | 77 | 8.5% | Libraries & SDKs |
| `libraries-*` | 53 | 5.8% | Libraries & SDKs |
| `terraform-*` | 34 | 3.7% | Infrastructure |
| `schema-*` | 30 | 3.3% | Database & Schema |
| `natterbox-*` | 23 | 2.5% | Various (product apps) |
| `third-*` | 21 | 2.3% | Third-Party Dependencies |
| `tools-*` | 20 | 2.2% | DevOps & Tooling |
| `operations-*` | 18 | 2.0% | DevOps & Tooling |
| `innovation-*` | 17 | 1.9% | Innovation/Experimental |
| `github-*` | 15 | 1.7% | DevOps & Tooling |
| Other | 260 | 28.6% | Various |

### Functional Category Analysis

| Category | Repo Count | Key Patterns |
|----------|-----------|--------------|
| Telephony Core | ~98 | freeswitch, opensips, sip, call, cti, dial, pbx, routing, voice |
| AI/Conversational | ~49 | cai, ai, bedrock, gpt, gemini, llm |
| Analytics/Insight | ~43 | insight, analytics, report, lumina, transcription |
| Integrations/CRM | ~34 | salesforce, crm, connector, omni, sf, avs, scv |
| Archiving/Compliance | ~15 | archiving, compliance, purge, retention, gdpr |
| Mobile | ~7 | mobile, freedom, mno, sim |

---

## Validated Domain Structure

### Domain 1: Telephony Core
**~100 repos** | The heart of the telecommunications platform

#### Subdomain: FreeSWITCH & SIP
- `platform-freeswitch` - Core FreeSWITCH with RM modules
- `platform-opensips` - OpenSIPS with custom module
- `platform-fscore` - FreeSWITCH scripts and config
- `platform-fsxinetdsocket` / `platform-fsxinetdsocket-php8` - CRM/scripting integration
- `platform-fseventmonitor` - Call control event handling
- `platform-fseventfilemonitor` - File-based event actions
- `platform-dialplan` - FreeSWITCH dial plan XML
- `platform-dialplanscripts` - Dial plan scripts

#### Subdomain: Call Control & Routing
- `platform-callcontrol` - Web-based SIP phone control
- `platform-fscallcentermonitor` - Queue/agent management
- `natterbox-routing-policies` - Routing policy UI (React)
- `aws-terraform-routing-policy` - Routing policy infrastructure
- `platform-cdr2sgapi` - CDR to Service Gateway workflow
- `platform-workflow-engine` - Workflow/payload injection

#### Subdomain: CTI & Softphone
- `platform-cti-client` - CTI frontend (CTI, CTI 2.0, FreedomCTI)
- `platform-webphoned` - WebRTC softphone daemon
- `platform-webphone-web` - Webphone frontend
- `platform-webphone-nginx` - Webphone nginx config

#### Key Databases
- `schema-freeswitch` - FreeSWITCH schema
- `schema-callcontrol` - Call control schema
- `schema-cdr` - CDR schema
- `schema-opensips` - OpenSIPS schema

---

### Domain 2: Archiving & Compliance
**~15 repos** | Recording storage, retention, GDPR

#### Core Services
- `platform-archiving` - Policy-based archiving (CDR, recordings, PCAP, SMS)
- `platform-cdrmunch` - CDR processing components
- `archiving-purge` - AWS-based purge and monitoring
- `terraform-nexus-archiving-purge` - Purge infrastructure
- `tools-archiving` - Archiving utilities
- `takeout-archiving` - Data export/takeout

#### Databases
- `schema-archivinginternal` - Internal archiving schema
- `schema-archivingretention` - Retention records, audit, usage

---

### Domain 3: Mobile & Freedom
**~7 repos** | Mobile applications and MNO integration

#### Mobile Apps
- `freedom-mobile` - React Native cross-platform app
- `freedom-mobile-ios` - iOS native (Swift)
- `freedom-mobile-android` - Android native (Kotlin)
- `freedom-freedom-web` - Web interface

#### MNO Integration
- `platform-mnoapi` - Mobile Network Operator API

---

### Domain 4: Integrations & CRM
**~34 repos** | Salesforce, CRM connectors, omnichannel

#### Salesforce Integration
- `natterbox-avs-sfdx` - AVS Salesforce package
- `natterbox-nbcc` - Natterbox Call Centre package (Apex)
- `natterbox-scv-package` - Service Cloud Voice package
- `platform-scv-byot-connector` - SCV BYOT integration
- `sfpbxproxy` - SF PBX proxy
- `nbinternal-salesforce` - Internal SF tools

#### Omnichannel
- `omnichannel-omniservice` - Omni Channel monorepo (TypeScript)
- `omnichannel-omnisettings` - Omnichannel settings
- `omnichannel-omniclient` - Omnichannel client
- `omniclient-v2` - React omnichannel UI

#### CRM Connectors
- `delta` - Delta API for CRM integration
- `delta-common` - Shared Delta infrastructure
- `cdc-pipeline` - Change Data Capture pipeline

---

### Domain 5: AI & Conversational
**~49 repos** | Conversational AI, LLM integration

#### CAI Services
- `cai-service` - Conversational AI service (TypeScript monorepo)
- `aws-terraform-cai` - CAI infrastructure
- `aws-terraform-cai-territory-setup` - CAI territory setup
- `aws-terraform-cai-region-setup` - CAI region setup
- `aws-terraform-rt-cai-websocket` - CAI WebSocket

#### AI Infrastructure
- `aws-terraform-bedrock` - AWS Bedrock config
- `bedrock-metrics-aggregator` - Cross-region usage aggregation
- `internal-knowledge-vertex` - Docs360 processing for Vertex AI
- `nbx-gemini-api` - Gemini API wrapper
- `nbx-ai-hub-api` - Internal AI API

#### Transcription
- `platform-transcribed` - BYOT transcribe service
- `aws-terraform-rt-transcribed` - Transcribed infrastructure
- `insight-transcription-analysis` - Transcription analysis lambda
- `insight-transcription-callback` - Transcription webhook handler

---

### Domain 6: Analytics & Insight
**~43 repos** | Observability, analytics, reporting

#### Lumina (Observability)
- `lumina` - Core observability service
- `natterbox-lumina` - Lumina frontend (React 19)
- `aws-terraform-lumina` - Lumina infrastructure
- `aws-terraform-lumina-pipeline` - Lumina data pipeline
- `aws-terraform-lumina-territory-setup` - Territory setup

#### Insight Services
- `insight-search-fe` - Insight search frontend
- `insight-insight-category-ui` - Category management UI
- `aws-insight-category-api` - Category API
- `insight-transcription-stats` - Transcription statistics
- `insight-analysis-notifier` - Analysis notifications

#### Wallboards
- `natterbox-wallboards` - Real-time dashboards
- `wallboards-service` - Wallboards backend
- `terraform-wallboards-service` - Wallboards infrastructure

---

### Domain 7: Core Platform Services
**~91 repos** | Core APIs, authentication, billing

#### Core API
- `platform-api` - Main API hub (PHP)
- `schema-api` - API schema migrations
- `platform-service-gateway` - Service gateway
- `platform-geoshim` - Core API proxy for latency optimization

#### Authentication & Authorization
- `platform-auth-scopes` - Auth scope definitions
- `go-auth-scopes` - Go auth scopes toolkit
- `go-gatekeeper-authoriser` - API Gateway authorizer
- `go-gatekeeper-jwt-creator` - JWT creation lambda
- `naps` - Natterbox Permissions Service

#### Billing
- `platform-billing-apps` - Billing applications
- `platform-billingapps-v2` - Billing v2 (TypeScript)
- `schema-billing` - Billing schema
- `schema-billingdata` - Billing data schema

#### Sapien (Admin Portal)
- `sapien` - Admin portal (natterbox org)
- `platform-sapien` - Platform Sapien

#### LCR (Least Cost Routing)
- `lcr-service` - LCR Service API
- `platform-lcr-tool` - LCR management tool
- `schema-lcr` - LCR schema

---

### Domain 8: Infrastructure
**~280 repos** | Terraform, networking, deployment

#### AWS Terraform (~131 repos)
Major categories:
- `aws-terraform-network-*` - Networking (VPC, subnets, etc.)
- `aws-terraform-rt-*` - RT (Real-Time) platform infrastructure
- `aws-terraform-*-ecs` - ECS deployments
- `aws-terraform-*-territory-setup` - Multi-tenant territory config

#### Salt Stack
- `infrastructure-salt-stack` - Salt configuration
- `infrastructure-versions` - Version management
- `salt` - Salt fork

#### Container Infrastructure
- `infrastructure-container-*` - Container stats and utilities
- `base-images-*` - Docker base images

#### CI/CD
- `terraform-hosted-runners-build` - GitHub self-hosted runners
- `github-workflows` - Reusable workflows
- `aws-terraform-build` - Build infrastructure

---

### Domain 9: Database & Schema
**30 repos** | Database schemas managed by dbmigrate

| Schema | Description |
|--------|-------------|
| `schema-api` | Core API data |
| `schema-apidata` | API data structures |
| `schema-archivinginternal` | Internal archiving |
| `schema-archivingretention` | Retention policies |
| `schema-billing` | Billing data |
| `schema-billingdata` | Billing transactions |
| `schema-cacti` | Monitoring (Cacti) |
| `schema-callcontrol` | Call control state |
| `schema-calldiagnostics` | Call diagnostics |
| `schema-cdr` | Call Detail Records |
| `schema-ddimap` | DDI mapping |
| `schema-e2etester` | E2E test data |
| `schema-eventlogs` | Event logs |
| `schema-freeswitch` | FreeSWITCH data |
| `schema-hapi` | HAPI data |
| `schema-lcr` | Least cost routing |
| `schema-logbuffer` | Log buffering |
| `schema-logsfinal` | Final log storage |
| `schema-notifier` | Notification data |
| `schema-numberplan` | Number planning |
| `schema-opensips` | OpenSIPS data |
| `schema-paratrooper` | Paratrooper data |
| `schema-replicationguard` | Replication guard |
| `schema-rsyslog` | Rsyslog data |
| `schema-sapientests` | Sapien test data |
| `schema-servicegateway` | Service gateway |
| `schema-skynet` | Skynet data |
| `schema-systemhealth` | System health |
| `schema-toolbox` | Toolbox data |
| `schema-webcallcontrol` | Web call control |

---

### Domain 10: Libraries & SDKs
**~130 repos** | Shared code, language-specific libraries

#### Go Libraries (~77 repos)
- `go-fs-to-aws` - FreeSWITCH events to AWS
- `go-fsevents` - FreeSWITCH event handler
- `go-cdr-import` - CDR import utilities
- `go-log` - Logging wrapper
- `go-jwt` - JWT utilities
- `go-retry` - Retry logic
- `go-monitoring` - Nagios integration
- `go-skyconf` - Cloud parameter loading
- `go-trie` - Trie data structure
- `goesl` - FreeSWITCH ESL wrapper

#### PHP Libraries (~53 repos)
- `libraries-kohana` - Kohana framework (2.3.4 + RM mods)
- `libraries-kohana-common` - Kohana common utilities
- `libraries-fscallmanagement` - Call management
- `libraries-restclient` - REST client
- `libraries-syslogger` - Syslog wrapper
- `libraries-php-esl-lib` - ESL library
- `libraries-csiplib` - C SIP/RTP library
- `libraries-numberrules` - Number normalization

---

### Domain 11: DevOps & Tooling
**~80 repos** | Operations, CI/CD, developer tools

#### GitHub Actions (~15 repos)
- `github-action-rpm-build` - RPM builder
- `github-action-go-build` - Go binary builder
- `github-action-apex-build` - Apex package builder
- `github-action-version-calculator` - Version calculation
- `github-workflows` - Reusable workflows

#### Operations (~18 repos)
- `operations-rmht` - Release Management Helper Toolkit
- `operations-ops-scripts` - Operations scripts
- `operations-hops` - Ops utilities
- `operations-failover-test-kit` - Failover testing

#### Build Tooling (lego-*)
- `lego-composer` - PHP Composer with SSH
- `lego-vulscan` - Vulnerability scanning
- `lego-sfdxbuilder` - Salesforce DX builder
- `lego-phpcs` - PHP CodeSniffer

---

## Domain Boundaries Validation

### Changes from Original Proposal

| Original Domain | Validated Domain | Changes |
|-----------------|------------------|---------|
| Telephony Core | Telephony Core | Expanded to include CTI, softphone |
| Mobile/SIM | Mobile & Freedom | Narrowed focus, removed SIM specifics |
| Compliance | Archiving & Compliance | More specific naming |
| Integrations | Integrations & CRM | Expanded to include omnichannel |
| Infrastructure | Infrastructure | Confirmed - largest domain |
| Frontend | *Distributed* | Frontends distributed to their domains |
| Platform Services | Core Platform Services | Clarified scope |
| *New* | AI & Conversational | Significant new capability area (~49 repos) |
| *New* | Analytics & Insight | Lumina, transcription, wallboards |
| *New* | Database & Schema | Critical for traceability |
| *New* | Libraries & SDKs | Foundation code |
| *New* | DevOps & Tooling | Build/deploy infrastructure |

### Cross-Domain Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Core Platform Services                     │
│                  (API, Auth, Service Gateway)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Telephony Core│ │ Integrations  │ │ AI & Convo    │
│ (FreeSWITCH,  │ │ (Salesforce,  │ │ (CAI, Trans-  │
│  SIP, Routing)│ │  Omnichannel) │ │  cription)    │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Analytics & Insight    │
              │   (Lumina, Wallboards)   │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  Archiving & Compliance  │
              │   (CDR, Recordings)      │
              └─────────────────────────┘
```

---

## Recommendations

### 1. Domain Documentation Structure

Each domain should have:
```
docs/domains/{domain-name}/
├── overview.md           # Domain purpose, stakeholders
├── architecture.md       # Domain architecture diagram
├── services.md          # Services within this domain
├── data-flows.md        # How data moves in/out
├── glossary.md          # Domain-specific terms
└── decision-records/    # ADRs for this domain
```

### 2. Priority Order for Documentation

Based on centrality and dependency analysis:

1. **Core Platform Services** - Foundation everything depends on
2. **Telephony Core** - Primary business capability
3. **Database & Schema** - Required for API-to-DB tracing
4. **Integrations & CRM** - Key customer-facing functionality
5. **AI & Conversational** - Growing strategic area
6. **Analytics & Insight** - Observability across system
7. **Archiving & Compliance** - Regulatory requirement
8. **Infrastructure** - Large but more self-documenting
9. **Libraries & SDKs** - Supporting code
10. **Mobile & Freedom** - Standalone capability
11. **DevOps & Tooling** - Internal tooling

### 3. Cross-Reference Requirements

For full API-to-Database tracing, document relationships between:
- `platform-api` ↔ `schema-api`
- `platform-fscallcentermonitor` ↔ `schema-callcontrol`
- `platform-cdrmunch` ↔ `schema-cdr`
- Each service ↔ its schema dependencies

---

## Next Steps

1. ✅ Domain boundaries validated
2. → Define criticality tiers within each domain
3. → Identify pilot services for deep documentation
4. → Gap analysis of doc-agent capabilities
5. → Design discovery UX
