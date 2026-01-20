# Documentation Backlog

Prioritized list of documentation work. Items move to [COMPLETED.md](COMPLETED.md) when done.

---

## Priority 1: Foundation ✅ COMPLETE

### Project Setup ✅
- [ ] Create repository structure
- [ ] Set up project tracking files
- [ ] Create initial repository inventory
- [ ] Categorize repositories by domain

### High-Level Architecture ✅
- [ ] Create architecture overview document
- [ ] Pull existing diagrams from Confluence Architecture space
- [ ] Document global platform topology (6 AWS regions)
- [ ] Create service dependency map (deferred - complex)

---

## Priority 2: Core Platform ✅ MOSTLY COMPLETE

### Voice Routing Subsystem ✅
- [ ] FreeSWITCH overview and role
- [ ] Call flow documentation (inbound/outbound)
- [ ] fsxinetd service documentation
- [ ] Dialplan structure and logic
- [ ] PBX component documentation
- [ ] tts-gateway service documentation
- [ ] Routing policies documentation

### Platform Core Services
- [ ] platform-api documentation
- [ ] platform-sapien documentation
- [ ] Database architecture overview
- [ ] CDR processing pipeline (cdrmunch)

### Infrastructure ✅
- [ ] Infrastructure overview (AWS, networking, deployment)
- [ ] Salt Stack configuration management details
- [ ] Guardian system documentation
- [ ] Networking architecture deep-dive

---

## Priority 3: Key Integrations ✅ OVERVIEW COMPLETE

### Salesforce Integration ✅
- [ ] Salesforce integration overview (AVS, SCV, architecture)
- [ ] AVS package deep-dive
- [ ] SCV BYOT connector details
- [ ] Omni-Channel integration details
- [ ] Voice Call object usage

### Omnichannel ✅
- [ ] Omnichannel overview (architecture, components, flows)
- [ ] Omniservice deep-dive
- [ ] Chat widget integration details
- [ ] Message templates service
- [ ] Channel routing logic

---

## Priority 4: Modern Services ✅ OVERVIEW COMPLETE

### AI/CAI (Conversational AI) ✅
- [ ] CAI overview (architecture, components, integration)
- [ ] Bedrock integration deep-dive
- [ ] Prompt pipeline documentation
- [ ] WebSocket service details

### Observability (Lumina)
- [ ] Lumina architecture
- [ ] Metrics pipeline
- [ ] Event processing
- [ ] Frontend application

### Permissions & Auth
- [ ] NAPS (Natterbox Permissions Service)
- [ ] Gatekeeper authorizer
- [ ] Auth0 integration

---

## Priority 5: Infrastructure as Code (Partial)

### Terraform Module Catalog ✅
- [ ] Create module inventory (catalog.md)
- [ ] Document module dependencies
- [ ] Standardize module documentation format
- [ ] Key modules deep-dive:
  - [ ] aws-terraform-omnichannel
  - [ ] aws-terraform-network-rt
  - [ ] aws-terraform-fsx8
  - [ ] aws-terraform-cai
  - [ ] aws-terraform-bedrock
  - [ ] aws-terraform-lumina-pipeline

---

## Priority 6: Operations ✅ COMPLETE

### Runbooks ✅
- [ ] Consolidate existing runbooks from Confluence
- [ ] Incident response procedures (emergency-response.md)
- [ ] Deployment procedures
- [ ] Monitoring and alerting procedures

### CI/CD
- [ ] GitHub Actions workflows documentation
- [ ] Release management process (RMHT)
- [ ] Environment management

---

## Priority 7: Onboarding ✅ COMPLETE

### Developer Onboarding ✅
- [ ] Development environment setup
- [ ] Repository navigation guide
- [ ] Key technologies overview
- [ ] Common development tasks

### Support Onboarding
- [ ] Platform overview for support
- [ ] Troubleshooting basics
- [ ] Escalation procedures

### Platform Engineer Onboarding ✅
- [ ] Training plan overview
- [ ] Tools and access
- [ ] Operational procedures

---

## Priority 8: Tooling ✅ COMPLETE

### Documentation Agent ✅
- [ ] Agent framework for autonomous documentation updates
- [ ] Task configuration (tasks.yaml)
- [ ] Docker deployment setup

---

## Parking Lot

*Items to be prioritized later or determined out of scope:*

- Mobile apps (Freedom iOS/Android)
- Legacy system deep documentation
- Historical migration documentation
- Individual customer configurations
- Wallboard application

---

## Backlog Management

### Adding Items
- New items go to "Parking Lot" unless urgent
- Prioritize based on business need and dependencies

### Estimating
Items are roughly sized:
- 🟢 Small (< 1 hour)
- 🟡 Medium (1-4 hours)
- 🔴 Large (4+ hours, consider breaking down)

### Dependencies
Note dependencies in item descriptions. Don't start blocked items.

---

*Last reviewed: 2026-01-20*
