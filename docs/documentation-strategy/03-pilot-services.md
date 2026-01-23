# Pilot Services for Documentation Proof of Concept

## Selection Criteria

The pilot services were selected to:
1. **Cover multiple languages** - PHP, TypeScript, Go, C++, Terraform
2. **Include different service types** - API, monorepo, schema, infrastructure
3. **Enable cross-reference testing** - Services that call each other and share databases
4. **Represent different domains** - Core platform, integrations, AI, analytics
5. **Be Tier 1 critical** - Maximum documentation depth required

---

## Selected Pilot Services (10 repos)

### 1. platform-api (Core API)
**Domain:** Core Platform Services | **Language:** PHP | **Framework:** Kohana

#### Why Selected
- Central hub for all machine and human interfaces
- Talks to most databases
- Foundation service that most other services depend on
- Complex business logic
- Tests PHP code analysis

#### Documentation Goals
- [ ] Full API endpoint reference
- [ ] Database interactions (which tables, what operations)
- [ ] Authentication flow
- [ ] Rate limiting configuration
- [ ] Error codes and handling

#### Cross-References To Test
- `schema-api` - Primary database
- `platform-service-gateway` - Proxy layer
- `go-gatekeeper-authoriser` - Auth integration

---

### 2. schema-api (Core Database Schema)
**Domain:** Database & Schema | **Language:** PHP (migrations)

#### Why Selected
- Core data model for the platform
- Critical for API-to-database tracing
- Tests schema documentation generation
- Has 15+ years of migration history

#### Documentation Goals
- [ ] Table catalog with descriptions
- [ ] Column-level documentation
- [ ] Relationships/foreign keys
- [ ] Indexes and constraints
- [ ] Migration history timeline

#### Cross-References To Test
- `platform-api` - Primary consumer
- Other `schema-*` repos - Shared patterns

---

### 3. omnichannel-omniservice (Omnichannel Core)
**Domain:** Integrations & CRM | **Language:** TypeScript | **Framework:** Node.js Monorepo

#### Why Selected
- Modern TypeScript monorepo
- Multiple packages in one repo
- GraphQL and REST APIs
- Tests monorepo documentation patterns
- Customer-facing omnichannel functionality

#### Documentation Goals
- [ ] Package catalog and relationships
- [ ] API endpoints (REST and GraphQL)
- [ ] Message queue interactions
- [ ] Configuration options
- [ ] Deployment architecture

#### Cross-References To Test
- `aws-terraform-omnichannel` - Infrastructure
- `omnichannel-omnisettings` - Configuration service
- CRM connectors

---

### 4. cai-service (Conversational AI)
**Domain:** AI & Conversational | **Language:** TypeScript | **Framework:** Node.js Monorepo

#### Why Selected
- Emerging strategic capability (AI)
- Multiple AI model integrations
- WebSocket support
- Complex configuration
- Tests modern TypeScript patterns

#### Documentation Goals
- [ ] Supported AI models and configuration
- [ ] API reference for prompt execution
- [ ] Integration patterns (Bedrock, etc.)
- [ ] WebSocket protocol documentation
- [ ] Cost/usage tracking

#### Cross-References To Test
- `aws-terraform-cai` - Infrastructure
- `aws-terraform-bedrock` - AI backend
- `platform-transcribed` - Transcription integration

---

### 5. lumina (Observability)
**Domain:** Analytics & Insight | **Language:** TypeScript | **Framework:** Node.js

#### Why Selected
- Core observability service
- Real-time data processing
- Complex data pipelines
- Tests analytics domain documentation

#### Documentation Goals
- [ ] Metrics collected and format
- [ ] Data pipeline architecture
- [ ] Query interface
- [ ] Dashboard integration
- [ ] Alert configuration

#### Cross-References To Test
- `natterbox-lumina` - Frontend
- `aws-terraform-lumina-pipeline` - Infrastructure
- Telephony services (data sources)

---

### 6. platform-freeswitch (FreeSWITCH Core)
**Domain:** Telephony Core | **Language:** C (with RM modules)

#### Why Selected
- Foundation of all telephony
- Custom C modules
- Complex build process
- Tests C/C++ documentation

#### Documentation Goals
- [ ] Custom RM modules and their purpose
- [ ] Build and deployment process
- [ ] Configuration reference
- [ ] Integration points
- [ ] Debugging/troubleshooting

#### Cross-References To Test
- `platform-dialplan` - Dial plan configuration
- `platform-fscore` - Scripts and configs
- `go-fs-to-aws` - Event streaming

---

### 7. platform-archiving (Archiving Service)
**Domain:** Archiving & Compliance | **Language:** C++

#### Why Selected
- Regulatory requirement (compliance)
- Multiple storage backends
- Policy engine
- Tests C++ documentation

#### Documentation Goals
- [ ] Supported archiving types (CDR, recordings, PCAP, SMS)
- [ ] Policy configuration
- [ ] Storage backends
- [ ] Retention rules
- [ ] GDPR compliance features

#### Cross-References To Test
- `schema-archivingretention` - Retention database
- `archiving-purge` - Purge service
- `platform-cdrmunch` - CDR processing

---

### 8. aws-terraform-api-gateway (API Gateway Infrastructure)
**Domain:** Infrastructure | **Language:** HCL (Terraform)

#### Why Selected
- Representative Terraform module
- Critical infrastructure component
- Tests IaC documentation patterns

#### Documentation Goals
- [ ] Resources provisioned
- [ ] Input variables
- [ ] Output values
- [ ] Dependencies
- [ ] Usage examples

#### Cross-References To Test
- `platform-api` - Service it deploys
- `go-gatekeeper-authoriser` - Authorizer lambda
- `aws-terraform-network-*` - Network dependencies

---

### 9. natterbox-avs-sfdx (Salesforce AVS Package)
**Domain:** Integrations & CRM | **Language:** Apex/Salesforce

#### Why Selected
- Primary Salesforce integration
- Customer-facing package
- Tests Salesforce/Apex documentation

#### Documentation Goals
- [ ] Package components
- [ ] Apex classes and their purpose
- [ ] Lightning components
- [ ] Configuration options
- [ ] Installation guide

#### Cross-References To Test
- `platform-api` - Backend integration
- `sfpbxproxy` - PBX proxy
- Other Salesforce packages

---

### 10. go-gatekeeper-authoriser (Auth Lambda)
**Domain:** Core Platform Services | **Language:** Go

#### Why Selected
- Security-critical component
- Go codebase
- Lambda function
- Tests Go documentation

#### Documentation Goals
- [ ] Authorization logic
- [ ] JWT handling
- [ ] Scope validation
- [ ] Error responses
- [ ] Configuration

#### Cross-References To Test
- `platform-auth-scopes` - Scope definitions
- `aws-terraform-gatekeeper` - Infrastructure
- `platform-api` - Protected service

---

## Language/Framework Coverage

| Language | Pilot Repo | Type |
|----------|-----------|------|
| PHP (Kohana) | platform-api | Web API |
| PHP (migrations) | schema-api | Database |
| TypeScript (Monorepo) | omnichannel-omniservice | Service |
| TypeScript (Monorepo) | cai-service | AI Service |
| TypeScript | lumina | Analytics |
| C | platform-freeswitch | Telephony |
| C++ | platform-archiving | Storage |
| HCL (Terraform) | aws-terraform-api-gateway | Infrastructure |
| Apex (Salesforce) | natterbox-avs-sfdx | Integration |
| Go | go-gatekeeper-authoriser | Lambda |

---

## Cross-Reference Test Matrix

This matrix shows the cross-references that should be generated:

```
                        platform-api  schema-api  omniservice  cai-service  lumina  freeswitch  archiving  tf-api-gw  avs-sfdx  gatekeeper
platform-api                  -           ✓           ✓            ✓          ✓         ✓          ✓          ✓          ✓          ✓
schema-api                    ✓           -           -            -          -         -          -          -          -          -
omnichannel-omniservice       ✓           -           -            ✓          -         -          -          -          -          ✓
cai-service                   ✓           -           ✓            -          -         -          -          ✓          -          ✓
lumina                        ✓           -           -            -          -         ✓          -          -          -          -
platform-freeswitch           ✓           -           -            -          ✓         -          -          -          -          -
platform-archiving            ✓           -           -            -          -         ✓          -          -          -          -
aws-terraform-api-gateway     ✓           -           -            ✓          -         -          -          -          -          ✓
natterbox-avs-sfdx            ✓           -           -            -          -         -          -          -          -          -
go-gatekeeper-authoriser      ✓           -           ✓            ✓          -         -          -          ✓          -          -
```

---

## Success Criteria

### Documentation Quality
- [ ] Each pilot has complete service documentation
- [ ] API endpoints are fully documented with examples
- [ ] Database tables are documented with field descriptions
- [ ] Configuration options are documented
- [ ] Cross-references link correctly between repos

### Cross-Referencing
- [ ] API-to-database traces work for `platform-api` → `schema-api`
- [ ] Service-to-infrastructure links work for services → Terraform
- [ ] Dependency graphs are accurate

### Search & Discovery
- [ ] Can find any service by name
- [ ] Can find services by capability
- [ ] Can trace from API endpoint to database table

---

## Implementation Order

### Phase 1: Foundation (Week 1)
1. `platform-api` - Core API documentation
2. `schema-api` - Database schema documentation
3. Test API-to-database cross-referencing

### Phase 2: Modern Services (Week 2)
4. `omnichannel-omniservice` - TypeScript monorepo
5. `cai-service` - AI service
6. `lumina` - Analytics service

### Phase 3: Specialized (Week 3)
7. `platform-freeswitch` - C codebase
8. `platform-archiving` - C++ codebase
9. `natterbox-avs-sfdx` - Salesforce/Apex

### Phase 4: Infrastructure & Auth (Week 4)
10. `aws-terraform-api-gateway` - Terraform
11. `go-gatekeeper-authoriser` - Go Lambda

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Large codebases overwhelm LLM context | Use chunking and summarization |
| Cross-references miss connections | Implement dependency analysis pass |
| Schema migrations too numerous | Focus on current state + key changes |
| C/C++ parsing limitations | Leverage existing code comments |
| Apex/Salesforce unfamiliar syntax | Use specialized prompts |

---

## Next Steps

1. ✅ Pilot services selected
2. → Verify all pilot repos are in the repos directory
3. → Run doc-agent on first pilot (platform-api)
4. → Evaluate output against documentation requirements
5. → Iterate on prompts and templates
