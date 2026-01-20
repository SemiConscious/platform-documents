# Documentation Backlog

**Last Updated:** 2026-01-20  
**Current Focus:** Priority 4 - Modern Services

---

## Priority 1: Platform Core ✅ COMPLETE

### Foundation Documents ✅
- [x] `architecture/overview.md` - Architecture index and navigation
- [x] `architecture/global-architecture.md` - High-level system architecture
- [x] `services/repository-inventory.md` - Repository catalog with categorization
- [ ] Service dependency map (deferred - requires complex diagramming/research)

### Core Services ✅
- [x] `services/platform-core/platform-api.md` - CoreAPI documentation
- [x] `services/platform-core/platform-sapien.md` - Public API documentation

---

## Priority 2: Voice Routing Subsystem ✅ COMPLETE

### Voice Components ✅
- [x] `architecture/voice-routing/overview.md` - Voice subsystem overview
- [x] `architecture/voice-routing/fsxinetd.md` - fsxinetd service deep-dive
- [x] `architecture/voice-routing/cdr-processing.md` - CDR pipeline documentation
- [x] `architecture/voice-routing/tts-gateway.md` - TTS Gateway service
- [x] `architecture/voice-routing/dialplan.md` - Dialplan structure and logic
- [x] `architecture/voice-routing/pbx.md` - PBX component documentation
- [x] `architecture/voice-routing/routing-policies.md` - Routing policies documentation

---

## Priority 3: Salesforce & Omnichannel ⏳ PARTIAL

### Salesforce Integration
- [x] `architecture/salesforce-integration/overview.md` - Integration overview ✅
- [ ] `architecture/salesforce-integration/avs-package.md` - AVS deep-dive (deferred - complex)
- [ ] `architecture/salesforce-integration/scv-connector.md` - SCV connector details (deferred - complex)
- [ ] `architecture/salesforce-integration/cti-adapter.md` - CTI adapter (deferred - complex)

### Omnichannel
- [x] `architecture/omnichannel/overview.md` - Omnichannel overview ✅
- [ ] `architecture/omnichannel/omniservice.md` - Omniservice deep-dive (deferred - complex)
- [ ] `architecture/omnichannel/chat-widget.md` - Chat widget documentation (deferred - complex)
- [ ] `architecture/omnichannel/message-templates.md` - Message templates (deferred - complex)

---

## Priority 4: Modern Services ⏳ PARTIAL

### AI/Conversational AI
- [x] `architecture/ai-cai/overview.md` - AI/CAI overview ✅
- [ ] `architecture/ai-cai/bedrock-integration.md` - AWS Bedrock details (deferred - complex)
- [ ] `architecture/ai-cai/prompt-pipeline.md` - Prompt management (deferred - complex)
- [ ] `architecture/ai-cai/websocket-service.md` - WebSocket handling (deferred - complex)

### Observability (Lumina) ✅
- [x] `architecture/observability/overview.md` - Lumina observability platform ✅

### Permissions & Auth (NEXT UP)
- [ ] `architecture/permissions/overview.md` - NAPS/Gatekeeper overview
- [ ] `architecture/permissions/naps-service.md` - NAPS deep-dive
- [ ] `architecture/permissions/gatekeeper.md` - Gatekeeper documentation
- [ ] `architecture/permissions/auth0-integration.md` - Auth0 integration

---

## Priority 5: Infrastructure & Terraform ⏳ PARTIAL

### Infrastructure
- [x] `architecture/infrastructure/overview.md` - Infrastructure overview ✅
- [ ] `architecture/infrastructure/salt-stack.md` - Salt configuration (deferred - complex)
- [ ] `architecture/infrastructure/guardian.md` - Guardian firewall (deferred - complex)
- [ ] `architecture/infrastructure/networking.md` - Network architecture (deferred - complex)

### Database
- [x] `architecture/database/overview.md` - Database architecture ✅

### Terraform
- [x] `terraform-modules/catalog.md` - Module catalog ✅
- [ ] Module documentation for individual modules (deferred - very large scope)

---

## Priority 6: Operations ⏳ PARTIAL

### Runbooks ✅
- [x] `operations/runbooks/README.md` - Runbooks index ✅
- [x] `operations/runbooks/emergency-response.md` - Emergency procedures ✅
- [x] `operations/runbooks/deployment-procedures.md` - Deployment guide ✅
- [x] `operations/runbooks/monitoring-alerting.md` - Monitoring tools ✅

### CI/CD (NEXT UP after Permissions)
- [ ] `operations/ci-cd/github-actions.md` - GitHub Actions workflows
- [ ] `operations/ci-cd/rmht.md` - Release Management tool
- [ ] `operations/ci-cd/environments.md` - Environment management

---

## Priority 7: Onboarding ⏳ PARTIAL

- [x] `onboarding/README.md` - Onboarding index ✅
- [x] `onboarding/developer.md` - Developer guide ✅
- [x] `onboarding/platform-engineer.md` - PE/SRE guide ✅
- [ ] `onboarding/support.md` - Support team onboarding

---

## Deferred Items (Complex/Large Scope)

These items require significant research, complex diagramming, or access to specific resources:

1. **Service dependency map** - Requires mapping 450+ repos
2. **AVS package deep-dive** - Complex Salesforce managed package
3. **SCV connector details** - Complex AWS/Salesforce integration
4. **CTI adapter** - WebSocket adapter internals
5. **Omniservice deep-dive** - Large complex service
6. **Chat widget** - Frontend components and SDK
7. **Message templates** - Template system internals
8. **Bedrock integration** - AWS AI service integration
9. **Prompt pipeline** - Prompt management system
10. **WebSocket service** - Real-time communication layer
11. **Salt Stack** - Configuration management (legacy)
12. **Guardian firewall** - Custom firewall rules
13. **Networking deep-dive** - VPC, Transit Gateway, etc.
14. **Individual Terraform modules** - 100+ modules to document

---

## Quick Wins (Can be done quickly)

1. ~~Lumina observability overview~~ ✅ DONE
2. Permissions & Auth overview (NAPS/Gatekeeper) ← **NEXT**
3. CI/CD GitHub Actions documentation
4. Support team onboarding guide

---

## Notes

- Focus on completing overviews before deep-dives
- Use existing Confluence content as primary source
- GitHub READMEs provide good technical detail
- Terraform modules often have embedded documentation
- Some services lack documentation - may need code analysis

---

*Review and update this backlog at the start of each session*
