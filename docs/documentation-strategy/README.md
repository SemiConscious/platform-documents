# Documentation Strategy for Natterbox Platform

## Overview

This documentation strategy defines a comprehensive approach to documenting ~908 repositories across the Natterbox/RedMatter platform. The goal is to create beautiful, comprehensive, hierarchical, fully cross-referenced documentation that answers any question a curious mind might want to know.

## Strategy Documents

| Document | Purpose |
|----------|---------|
| [01-domain-validation.md](./01-domain-validation.md) | Validated domain boundaries based on actual repository analysis |
| [02-criticality-tiers.md](./02-criticality-tiers.md) | Four-tier framework for prioritizing documentation depth |
| [03-pilot-services.md](./03-pilot-services.md) | 10 pilot services for proof of concept across all languages |
| [04-gap-analysis.md](./04-gap-analysis.md) | doc-agent capabilities vs. strategic requirements |
| [05-discovery-ux.md](./05-discovery-ux.md) | Search and navigation user experience design |

## Key Numbers

| Metric | Value |
|--------|-------|
| Total Repositories | 908 |
| Validated Domains | 11 |
| Tier 1 (Critical) Services | ~65 |
| Tier 2 (Important) Services | ~125 |
| Pilot Services | 10 |
| Languages Covered | 12 |
| Estimated Total Documents | ~2,645 |

## Five-Layer Documentation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: DISCOVERY                                          │
│  Platform Overview | Capability Map | Service Catalog       │
│  Repository Index | Unified Search                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: DOMAIN                                             │
│  Telephony | Mobile | Compliance | Integrations | AI        │
│  Analytics | Platform | Infrastructure | Schema | DevOps    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: SERVICE                                            │
│  README | Architecture | API Reference | Data Models        │
│  Configuration | Operations Runbook                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: REPOSITORY                                         │
│  Structure | Dependencies | Activity | Health               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: CODE                                               │
│  Database Schemas | API Specs | Functions | Config          │
└─────────────────────────────────────────────────────────────┘
```

## Validated Domains (11)

| Domain | Repos | Description |
|--------|-------|-------------|
| Telephony Core | ~100 | FreeSWITCH, OpenSIPS, call routing, CTI |
| Archiving & Compliance | ~15 | Recording storage, retention, GDPR |
| Mobile & Freedom | ~7 | Mobile apps, MNO integration |
| Integrations & CRM | ~34 | Salesforce, omnichannel |
| AI & Conversational | ~49 | CAI, transcription, LLM |
| Analytics & Insight | ~43 | Lumina, wallboards, reporting |
| Core Platform Services | ~91 | API, auth, billing |
| Infrastructure | ~280 | Terraform, networking, deployment |
| Database & Schema | ~30 | All schema-* repos |
| Libraries & SDKs | ~130 | Go and PHP libraries |
| DevOps & Tooling | ~80 | CI/CD, operations |

## Criticality Tiers

| Tier | Count | Documentation Depth |
|------|-------|---------------------|
| **Tier 1: Critical** | ~65 | Maximum (10-15 docs per service) |
| **Tier 2: Important** | ~125 | High (5-8 docs per service) |
| **Tier 3: Supporting** | ~250 | Standard (2-3 docs per service) |
| **Tier 4: Reference** | ~470 | Minimal (index entry only) |

## Pilot Services (10)

Covering all major languages and service types:

| Service | Language | Domain | Type |
|---------|----------|--------|------|
| platform-api | PHP | Core Platform | Web API |
| schema-api | PHP | Database | Schema |
| omnichannel-omniservice | TypeScript | Integrations | Monorepo |
| cai-service | TypeScript | AI | Monorepo |
| lumina | TypeScript | Analytics | Service |
| platform-freeswitch | C | Telephony | Core |
| platform-archiving | C++ | Compliance | Storage |
| aws-terraform-api-gateway | HCL | Infrastructure | Terraform |
| natterbox-avs-sfdx | Apex | Integrations | Salesforce |
| go-gatekeeper-authoriser | Go | Core Platform | Lambda |

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Implement criticality tier assignment in doc-agent
- [ ] Add schema-to-code linking
- [ ] Integrate validated domain boundaries
- [ ] Generate docs for first 3 pilot services

### Phase 2: Pilot Completion (Weeks 3-4)
- [ ] Complete all 10 pilot services
- [ ] Test API-to-database tracing
- [ ] Validate cross-references
- [ ] Set up MkDocs/Docusaurus site

### Phase 3: Search & Discovery (Weeks 5-6)
- [ ] Implement SQLite FTS search
- [ ] Build search UI
- [ ] Add dependency graph visualization
- [ ] Deploy internal documentation site

### Phase 4: Scale (Weeks 7-12)
- [ ] Generate Tier 1 docs (65 services)
- [ ] Generate Tier 2 docs (125 services)
- [ ] Index Tier 3 and 4 repos
- [ ] Gather user feedback and iterate

### Phase 5: Enhancement (Ongoing)
- [ ] Add semantic search
- [ ] Implement activity analysis
- [ ] Build ownership mapping
- [ ] Create technical debt dashboard

## Success Metrics

| Metric | Target |
|--------|--------|
| Documentation Coverage (Tier 1) | 100% |
| Documentation Coverage (Tier 2) | 80% |
| Time to Find Any Service | < 30 seconds |
| Search Success Rate | > 90% |
| API-to-DB Trace Completion | 100% for Tier 1 |
| User Satisfaction | > 4/5 |

## Key Questions This Documentation Will Answer

### Operational
- "What API do I call to change a routing policy?"
- "What database tables does that affect?"
- "Who do I contact if this breaks?"
- "How do I deploy a fix?"

### Strategic
- "What repos can we retire?"
- "What capabilities are duplicated?"
- "What would a v2 architecture look like?"
- "What's our technical debt?"

### Learning
- "How does call routing work?"
- "What's the data model for X?"
- "Why was X built this way?"

## Getting Started

1. **Read the strategy docs** in order (01 through 05)
2. **Review the pilot services** to understand the target output
3. **Run doc-agent** on a pilot service to generate initial docs
4. **Provide feedback** to improve the documentation quality

## Contributing

Documentation is generated by `doc-agent` but contributions are welcome:

- **Domain experts**: Review and correct generated docs
- **Developers**: Improve code analysis accuracy
- **Writers**: Enhance templates and prose quality
- **Users**: Report gaps and inaccuracies

---

*Last updated: January 2026*
*Strategy version: 1.0*
