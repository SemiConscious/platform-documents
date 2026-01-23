# Criticality Tier Framework

## Overview

With ~908 repositories, documentation depth must be prioritized. This framework defines four criticality tiers that determine the required documentation depth for each repository and service.

## Tier Definitions

### Tier 1: Critical (Mission-Critical)
**Documentation Depth: Maximum** | ~50-80 repos

#### Criteria (must meet 2+ of these)
- Direct revenue impact if unavailable (call routing, billing, API)
- Customer-facing production service
- Regulatory/compliance requirement (archiving, GDPR)
- Single point of failure (no redundancy)
- Foundation for 10+ downstream services

#### Required Documentation
- Full service documentation suite:
  - README with architecture overview
  - API reference (all endpoints documented)
  - Database schema with field-level descriptions
  - Data flow diagrams
  - Operations runbook
  - Incident response procedures
  - Configuration reference
  - Integration guide
- Cross-references to all dependencies
- Change impact analysis
- SLA documentation

---

### Tier 2: Important (Business-Critical)
**Documentation Depth: High** | ~100-150 repos

#### Criteria (must meet 2+ of these)
- Supports customer-facing functionality
- Internal tool used daily by multiple teams
- Dependency for Tier 1 services
- Actively maintained (commits in last 6 months)
- Contains business logic

#### Required Documentation
- Service README with purpose and ownership
- API reference for public endpoints
- Database schema overview
- Key configuration options
- Basic operations guide
- Primary integration points

---

### Tier 3: Supporting (Operational)
**Documentation Depth: Standard** | ~200-300 repos

#### Criteria
- Infrastructure automation
- Build/deployment tooling
- Libraries used by multiple services
- Internal utilities
- Maintained but not customer-facing

#### Required Documentation
- README with purpose
- Installation/usage instructions
- Key configuration options
- Changelog

---

### Tier 4: Reference (Indexed Only)
**Documentation Depth: Minimal** | ~400+ repos

#### Criteria (any of these)
- Archived or deprecated
- No commits in 12+ months
- Third-party forks
- Experimental/innovation projects
- One-off scripts or tools

#### Required Documentation
- Index entry with:
  - Name and description
  - Status (archived, deprecated, legacy)
  - Last meaningful activity date
  - Primary language
  - Original purpose (if known)

---

## Tier Assignment by Domain

### Domain: Telephony Core

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `platform-freeswitch` | Core telephony switch - all calls flow through |
| `platform-opensips` | SIP proxy - call routing foundation |
| `platform-dialplan` | Dial plan configuration - determines call handling |
| `platform-fscallcentermonitor` | Queue management - contact center operations |
| `platform-fsxinetdsocket` | CRM/scripting integration - customer workflows |
| `platform-cdr2sgapi` | CDR processing - billing and analytics |
| `platform-workflow-engine` | Workflow orchestration |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `platform-fscore` | FreeSWITCH scripts and config |
| `platform-fseventmonitor` | Event handling for call control |
| `platform-webphoned` | WebRTC softphone |
| `platform-cti-client` | CTI frontend |
| `natterbox-routing-policies` | Routing policy UI |
| `platform-callcontrol` | Web call control |
| `platform-dialplanscripts` | Dial plan scripts |

#### Tier 3 - Supporting
| Repository | Reason |
|------------|--------|
| `platform-fseventfilemonitor` | File event handling |
| `platform-fsconfig` | Config generation |
| `platform-fssounds` | Audio files |
| `platform-fsutils` | Development utilities |
| `platform-fsstatusmonitor` | Status monitoring |

---

### Domain: Core Platform Services

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `platform-api` | Core API - central hub for all integrations |
| `platform-service-gateway` | Service gateway - API routing |
| `go-gatekeeper-authoriser` | Authentication - security boundary |
| `platform-auth-scopes` | Authorization definitions |
| `sapien` | Admin portal - customer management |
| `schema-api` | Core API schema |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `platform-geoshim` | Latency optimization proxy |
| `platform-lasso` | SF session exchange |
| `naps` | Permissions service |
| `platform-billing-apps` | Billing applications |
| `lcr-service` | Least cost routing |

---

### Domain: Integrations & CRM

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `natterbox-avs-sfdx` | Primary Salesforce integration |
| `natterbox-nbcc` | Call Centre Salesforce package |
| `omnichannel-omniservice` | Omnichannel core service |
| `sfpbxproxy` | Salesforce PBX integration |
| `cdc-pipeline` | Change data capture - sync foundation |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `natterbox-scv-package` | Service Cloud Voice |
| `platform-scv-byot-connector` | SCV BYOT |
| `delta` | CRM integration API |
| `omnichannel-omnisettings` | Omnichannel configuration |
| `omniclient-v2` | Omnichannel UI |

---

### Domain: AI & Conversational

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `cai-service` | Conversational AI core |
| `aws-terraform-cai` | CAI infrastructure |
| `platform-transcribed` | Transcription service |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `aws-terraform-bedrock` | Bedrock configuration |
| `bedrock-metrics-aggregator` | Usage tracking |
| `internal-knowledge-vertex` | Knowledge base pipeline |
| `insight-transcription-analysis` | Transcription analysis |

---

### Domain: Analytics & Insight

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `lumina` | Core observability service |
| `natterbox-wallboards` | Real-time dashboards |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `natterbox-lumina` | Lumina frontend |
| `wallboards-service` | Wallboards backend |
| `aws-terraform-lumina-pipeline` | Data pipeline |
| `insight-search-fe` | Search interface |

---

### Domain: Archiving & Compliance

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `platform-archiving` | Policy-based archiving - regulatory requirement |
| `platform-cdrmunch` | CDR processing |
| `schema-archivingretention` | Retention schema |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `archiving-purge` | GDPR purge service |
| `terraform-nexus-archiving-purge` | Purge infrastructure |

---

### Domain: Database & Schema

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `schema-api` | Core API data |
| `schema-cdr` | CDR data |
| `schema-billing` | Billing data |
| `schema-archivingretention` | Compliance data |
| `platform-dbmigrate` | Migration tooling |

#### Tier 2 - Important
All other `schema-*` repos - required for complete data tracing

---

### Domain: Infrastructure

#### Tier 1 - Critical
| Repository | Reason |
|------------|--------|
| `aws-terraform-network-rt` | RT network foundation |
| `aws-terraform-rt-pbx` | RT PBX deployment |
| `aws-terraform-rt-sip` | SIP infrastructure |
| `aws-terraform-rt-ecs` | ECS platform |
| `aws-terraform-gatekeeper` | Auth infrastructure |

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `aws-terraform-api-gateway` | API Gateway config |
| `aws-terraform-fsx` / `aws-terraform-fsx8` | FSX infrastructure |
| `aws-terraform-omnichannel` | Omnichannel infrastructure |
| `aws-terraform-dns` | DNS management |
| `infrastructure-salt-stack` | Configuration management |
| `infrastructure-versions` | Version coordination |

#### Tier 3 - Supporting
Most `aws-terraform-*-territory-setup` repos - follow patterns from parent modules

---

### Domain: Libraries & SDKs

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `libraries-kohana` | Core PHP framework |
| `libraries-fscallmanagement` | Call management library |
| `libraries-restclient` | REST client used everywhere |
| `go-fsevents` | FreeSWITCH event handling |
| `go-gatekeeper-authoriser` | Auth library |
| `goesl` | FreeSWITCH ESL |

#### Tier 3 - Supporting
Most other `libraries-*` and `go-*` repos

---

### Domain: Mobile & Freedom

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `freedom-mobile` | Cross-platform app |
| `freedom-mobile-ios` | iOS app |
| `freedom-mobile-android` | Android app |
| `platform-mnoapi` | MNO integration |

---

### Domain: DevOps & Tooling

#### Tier 2 - Important
| Repository | Reason |
|------------|--------|
| `github-workflows` | Reusable CI/CD |
| `operations-rmht` | Release management |
| `aws-docker-terraform` | Terraform wrapper |

#### Tier 3 - Supporting
Most `github-action-*`, `operations-*`, `lego-*` repos

---

## Summary Statistics

| Tier | Count | Documentation Depth |
|------|-------|---------------------|
| Tier 1 - Critical | ~50-80 | Maximum |
| Tier 2 - Important | ~100-150 | High |
| Tier 3 - Supporting | ~200-300 | Standard |
| Tier 4 - Reference | ~400+ | Minimal (index only) |

---

## Automated Tier Assignment Criteria

For automated assignment, use these heuristics:

### Tier 1 Indicators
- In dependency path of 10+ other repos
- Has `schema-*` counterpart
- Name contains: `api`, `gateway`, `core`, `freeswitch`, `opensips`
- Terraform module deployed to production
- Has associated runbook or on-call rotation

### Tier 2 Indicators  
- Commits in last 6 months
- Referenced in Confluence/Docs360
- Name contains: `service`, `ui`, `frontend`, `backend`
- Has Dockerfile (deployed service)
- Multiple contributors

### Tier 3 Indicators
- Name contains: `terraform`, `infrastructure`, `library`, `tool`
- Supporting infrastructure
- Limited direct business impact

### Tier 4 Indicators
- No commits in 12+ months
- Name contains: `archived`, `deprecated`, `legacy`, `test`, `demo`
- Third-party fork
- Innovation/hackathon project

---

## Documentation Effort Estimates

| Tier | Docs Per Repo | Total Repos | Total Docs |
|------|--------------|-------------|------------|
| Tier 1 | 10-15 docs | ~65 | ~800 |
| Tier 2 | 5-8 docs | ~125 | ~750 |
| Tier 3 | 2-3 docs | ~250 | ~625 |
| Tier 4 | 1 doc (index) | ~470 | ~470 |
| **Total** | | **~910** | **~2,645** |

---

## Next Steps

1. ✅ Tier framework defined
2. ✅ Key services classified
3. → Select pilot services from Tier 1 for proof of concept
4. → Implement automated tier detection in doc-agent
5. → Create tier-specific documentation templates
