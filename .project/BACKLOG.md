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

## Priority 2: Core Platform (Partially Complete)

### Voice Routing Subsystem ✅
- [x] FreeSWITCH overview and role
- [x] Call flow documentation (inbound/outbound)
- [x] fsxinetd service documentation
- [ ] Dialplan structure and logic
- [ ] PBX component documentation
- [ ] tts-gateway service documentation
- [ ] Routing policies documentation

### Platform Core Services
- [ ] platform-api documentation
- [ ] platform-sapien documentation
- [ ] Database architecture overview
- [ ] CDR processing pipeline (cdrmunch)

### Infrastructure
- [ ] Salt Stack configuration management
- [ ] Guardian system documentation
- [ ] Networking architecture

---

## Priority 3: Key Integrations

### Salesforce Integration
- [ ] AVS package overview
- [ ] SCV BYOT connector
- [ ] Omni-Channel integration
- [ ] Voice Call object usage

### Omnichannel
- [ ] Omniservice architecture
- [ ] Chat widget integration
- [ ] Message templates service
- [ ] Channel routing

---

## Priority 4: Modern Services

### AI/CAI (Conversational AI)
- [ ] CAI service architecture
- [ ] Bedrock integration
- [ ] Prompt pipeline documentation
- [ ] WebSocket service

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

## Priority 5: Infrastructure as Code

### Terraform Module Catalog
- [ ] Create module inventory
- [ ] Document module dependencies
- [ ] Standardize module documentation format
- [ ] Key modules:
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

### CI/CD
- [ ] GitHub Actions workflows documentation
- [ ] Release management process (RMHT)
- [ ] Environment management

---

## Priority 7: Onboarding ✅ COMPLETE

### Developer Onboarding ✅
- [x] Development environment setup
- [x] Repository navigation guide
- [x] Key technologies overview
- [x] Common development tasks

### Support Onboarding
- [ ] Platform overview for support
- [ ] Troubleshooting basics
- [ ] Escalation procedures

### Platform Engineer Onboarding ✅
- [x] Training plan overview
- [x] Tools and access
- [x] Operational procedures

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
