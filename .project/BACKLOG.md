# Documentation Backlog

Prioritized list of documentation work. Items move to [COMPLETED.md](COMPLETED.md) when done.

---

## Priority 1: Foundation ✅ COMPLETE

### Project Setup ✅
- [x] Create repository structure
- [x] Set up project tracking files
- [x] Create initial repository inventory
- [x] Categorize repositories by domain

### High-Level Architecture ✅
- [x] Create architecture overview document
- [x] Pull existing diagrams from Confluence Architecture space
- [x] Document global platform topology (6 AWS regions)
- [ ] Create service dependency map (deferred - complex)

---

## Priority 2: Core Platform ✅ COMPLETE

### Voice Routing Subsystem ✅
- [x] FreeSWITCH overview and role
- [x] Call flow documentation (inbound/outbound)
- [x] fsxinetd service documentation
- [x] **Dialplan structure and logic** ✅ COMPLETE (2026-01-20)
- [x] **PBX component documentation** ✅ COMPLETE (2026-01-20)
- [ ] tts-gateway service documentation
- [ ] Routing policies documentation

### Platform Core Services ✅
- [x] **platform-api documentation** ✅ COMPLETE (2026-01-20)
- [x] **platform-sapien documentation** ✅ COMPLETE (2026-01-20)
- [x] **Database architecture overview** ✅ COMPLETE (2026-01-20)
- [x] **CDRMunch (Post-Call Processing) documentation** ✅ COMPLETE (2026-01-20)

### Infrastructure ✅
- [x] Infrastructure overview (AWS, networking, deployment)
- [x] **Salt Stack configuration management** ✅ COMPLETE (2026-01-20)
- [x] **Guardian system documentation** ✅ COMPLETE (2026-01-20)
- [x] **Networking architecture deep-dive** ✅ COMPLETE (2026-01-20)

---

## Priority 3: Key Integrations ✅ OVERVIEW COMPLETE

### Salesforce Integration ✅
- [x] Salesforce integration overview (AVS, SCV, architecture)
- [ ] AVS package deep-dive
- [ ] SCV BYOT connector details
- [ ] Omni-Channel integration details
- [ ] Voice Call object usage

### Omnichannel ✅
- [x] Omnichannel overview (architecture, components, flows)
- [ ] Omniservice deep-dive
- [ ] Chat widget integration details
- [ ] Message templates service
- [ ] Channel routing logic

---

## Priority 4: Modern Services ✅ OVERVIEW COMPLETE

### AI/CAI (Conversational AI) ✅
- [x] CAI overview (architecture, components, integration)
- [ ] Bedrock integration deep-dive
- [ ] Prompt pipeline documentation
- [ ] WebSocket service details

### Observability (Lumina) ✅ COMPLETE
- [x] **Lumina architecture** ✅ COMPLETE (2026-01-20)
- [x] **Metrics pipeline** ✅ COMPLETE (2026-01-20)
- [x] **Event processing** ✅ COMPLETE (2026-01-20)
- [x] **Frontend application** ✅ COMPLETE (2026-01-20)

### Permissions & Auth ✅ COMPLETE
- [x] **NAPS (Natterbox Permissions Service)** ✅ COMPLETE (2026-01-20)
- [x] **Gatekeeper authorizer** ✅ COMPLETE (2026-01-20)
- [x] **Auth0 integration** ✅ COMPLETE (2026-01-20)

---

## Priority 5: Infrastructure as Code (Partial)

### Terraform Module Catalog ✅
- [x] Create module inventory (catalog.md)
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
- [x] Consolidate existing runbooks from Confluence
- [x] Incident response procedures (emergency-response.md)
- [x] Deployment procedures
- [x] Monitoring and alerting procedures

### CI/CD ✅ COMPLETE
- [x] **GitHub Actions workflows documentation** ✅ COMPLETE (2026-01-20)
- [x] **Release management process (RMHT)** ✅ COMPLETE (2026-01-20)
- [x] **Environment management** ✅ COMPLETE (2026-01-20)

---

## Priority 7: Onboarding ✅ COMPLETE

### Developer Onboarding ✅
- [x] Development environment setup
- [x] Repository navigation guide
- [x] Key technologies overview
- [x] Common development tasks

### Support Onboarding ✅ COMPLETE
- [x] **Platform overview for support** ✅ COMPLETE (2026-01-20)
- [x] **Troubleshooting basics** ✅ COMPLETE (2026-01-20)
- [x] **Escalation procedures** ✅ COMPLETE (2026-01-20)

### Platform Engineer Onboarding ✅
- [x] Training plan overview
- [x] Tools and access
- [x] Operational procedures

---

## Priority 8: Tooling ✅ COMPLETE

### Documentation Agent ✅
- [x] Agent framework for autonomous documentation updates
- [x] Task configuration (tasks.yaml)
- [x] Docker deployment setup

---

## Parking Lot

*Items to be prioritized later or determined out of scope:*

- Mobile apps (Freedom iOS/Android)
- Legacy system deep documentation
- Historical migration documentation
- Individual customer configurations
- Wallboard application
- tts-gateway service documentation
- Routing policies documentation
- Terraform module deep-dives (6 modules)
- Salesforce deep-dive documentation (4 items)
- Omnichannel deep-dive documentation (4 items)
- AI/CAI deep-dive documentation (3 items)

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
