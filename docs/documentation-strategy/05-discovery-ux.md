# Discovery UX Design

## Overview

This document defines how users will discover and navigate the documentation for ~908 repositories. The goal is to enable any user to find what they need in under 30 seconds.

## User Personas & Journeys

### Persona 1: The Developer
**Goal:** Understand how to integrate with or modify a specific service

**Typical Questions:**
- "How do I call the routing policy API?"
- "What database tables does platform-api use?"
- "Where is the call recording stored?"

**Journey:**
1. Search for service name → Land on service README
2. Navigate to API docs or data model
3. Find code examples
4. Cross-reference to related services

### Persona 2: The Architect
**Goal:** Understand system design and plan changes

**Typical Questions:**
- "How does call routing work end-to-end?"
- "What would break if we change the CDR schema?"
- "What services are candidates for consolidation?"

**Journey:**
1. Start at domain overview → Understand domain architecture
2. Drill into data flows and dependencies
3. Review dependency graphs
4. Analyze impact of proposed changes

### Persona 3: The New Joiner
**Goal:** Get oriented and find where to start

**Typical Questions:**
- "What is this platform?"
- "What are the main components?"
- "Who owns what?"

**Journey:**
1. Start at platform overview → Understand high-level architecture
2. Browse domain catalog → Pick area of interest
3. Read onboarding guide for specific domain
4. Deep dive into assigned service

### Persona 4: The Operator
**Goal:** Diagnose issues and perform maintenance

**Typical Questions:**
- "How do I restart the FSX service?"
- "What are the alert thresholds?"
- "Where are the logs?"

**Journey:**
1. Search for service name → Go to operations runbook
2. Find specific procedure
3. Cross-reference to infrastructure docs
4. Check related monitoring dashboards

---

## Entry Points

### 1. Home Page (index.md)

**Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Natterbox Platform                        │
│              Documentation Portal                            │
├─────────────────────────────────────────────────────────────┤
│  🔍 [ Search documentation...                        ] [Go] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Quick Access                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Services │ │ Domains  │ │ API Ref  │ │ Schemas  │       │
│  │ Catalog  │ │ Overview │ │          │ │          │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  Getting Started                                             │
│  • Platform Overview                                         │
│  • Architecture Guide                                        │
│  • New Joiner Onboarding                                     │
│                                                              │
│  Browse by Domain                                            │
│  ┌────────────────┬────────────────┬────────────────┐       │
│  │ Telephony Core │ Integrations   │ AI & Convo     │       │
│  │ 98 repos       │ 34 repos       │ 49 repos       │       │
│  └────────────────┴────────────────┴────────────────┘       │
│  ┌────────────────┬────────────────┬────────────────┐       │
│  │ Analytics      │ Infrastructure │ Platform Svc   │       │
│  │ 43 repos       │ 280 repos      │ 91 repos       │       │
│  └────────────────┴────────────────┴────────────────┘       │
│                                                              │
│  Recently Updated                                            │
│  • omnichannel-omniservice - 2 hours ago                    │
│  • cai-service - 5 hours ago                                │
│  • platform-api - 1 day ago                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. Service Catalog

**Purpose:** Browse and filter all services

**Features:**
- Filter by domain
- Filter by language
- Filter by tier (critical, important, supporting, reference)
- Filter by status (active, maintenance, legacy, archived)
- Sort by name, activity, dependencies

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Service Catalog                           [🔍 Search]      │
├─────────────────────────────────────────────────────────────┤
│  Filters:                                                   │
│  Domain: [All ▼]  Language: [All ▼]  Tier: [All ▼]         │
│  Status: [All ▼]                                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ⭐ platform-api                           Tier 1 | PHP  ││
│  │ Core API - central hub for all integrations            ││
│  │ Domain: Core Platform | Last updated: 2 days ago       ││
│  │ Dependencies: 15 | Dependents: 45                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ⭐ platform-freeswitch                   Tier 1 | C     ││
│  │ Core FreeSWITCH with RM modules                        ││
│  │ Domain: Telephony Core | Last updated: 1 week ago      ││
│  │ Dependencies: 8 | Dependents: 32                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Showing 1-20 of 908 services            [< Prev] [Next >] │
└─────────────────────────────────────────────────────────────┘
```

### 3. Domain Overview

**Purpose:** Understand a business domain

**Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Domains                                          │
│                                                              │
│  Telephony Core                                             │
│  The foundation of all voice communications                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Overview                                                    │
│  This domain handles all aspects of voice call routing,    │
│  switching, and control through FreeSWITCH and OpenSIPS.   │
│                                                              │
│  Key Services                                                │
│  • platform-freeswitch - Core telephony switch             │
│  • platform-opensips - SIP proxy and routing               │
│  • platform-dialplan - Dial plan configuration             │
│  • platform-cdr2sgapi - CDR processing                     │
│                                                              │
│  Architecture                                                │
│  ┌──────────────────────────────────────┐                   │
│  │       [Mermaid Diagram Here]         │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
│  Data Flows                                                  │
│  • Inbound Call Flow                                        │
│  • Outbound Call Flow                                       │
│  • Call Recording Flow                                      │
│                                                              │
│  Related Domains                                             │
│  • Archiving & Compliance (CDR storage)                     │
│  • Integrations & CRM (Salesforce screen pop)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4. Service Detail

**Purpose:** Deep dive into a specific service

**Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Telephony Core                                   │
│                                                              │
│  platform-freeswitch                        ⭐ Tier 1       │
│  Core FreeSWITCH with RM custom modules                     │
├─────────────────────────────────────────────────────────────┤
│  Tabs: [Overview] [API] [Data] [Config] [Operations]       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Quick Info                                                  │
│  ┌─────────────┬────────────────────────────────────┐       │
│  │ Language    │ C                                  │       │
│  │ Repository  │ github.com/redmatter/platform-...  │       │
│  │ Ownership   │ Platform Team                      │       │
│  │ Last Commit │ 2025-01-20                         │       │
│  │ Status      │ 🟢 Active                          │       │
│  └─────────────┴────────────────────────────────────┘       │
│                                                              │
│  Architecture                                                │
│  [Mermaid diagram showing internal components]              │
│                                                              │
│  Dependencies                                                │
│  Services this depends on:                                  │
│  • platform-dialplan - Dial plan configuration             │
│  • platform-fscore - Scripts and XML config                │
│                                                              │
│  Dependents                                                  │
│  Services that depend on this:                              │
│  • platform-cdr2sgapi - Receives events                    │
│  • platform-archiving - Receives recordings                │
│  • lumina - Receives metrics                               │
│                                                              │
│  Database Schemas                                            │
│  • schema-freeswitch - FreeSWITCH state data               │
│  • schema-cdr - Call detail records                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Search Experience

### Search Types

#### 1. Full-Text Search
**Query:** "routing policy"
**Results:** All docs containing "routing policy"

#### 2. Service Search
**Query:** "service:platform-api"
**Results:** Jump directly to service

#### 3. API Search
**Query:** "api:POST /organizations"
**Results:** API endpoint documentation

#### 4. Code Search
**Query:** "code:CallController"
**Results:** Code references to CallController class

#### 5. Natural Language Search
**Query:** "how do I make a call"
**Results:** Semantic matches to call initiation docs

### Search Results Page

```
┌─────────────────────────────────────────────────────────────┐
│  Search Results for "routing policy"                        │
│  Found 47 results in 0.23 seconds                           │
├─────────────────────────────────────────────────────────────┤
│  Filter: [All Types ▼]  [All Domains ▼]                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Services (3)                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ natterbox-routing-policies                              ││
│  │ Routing Policies - React App                            ││
│  │ Domain: Telephony Core                                  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  API Endpoints (5)                                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ GET /api/v2/routing-policies                            ││
│  │ List all routing policies for an organization           ││
│  │ Service: platform-api                                   ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ PUT /api/v2/routing-policies/{id}                       ││
│  │ Update a routing policy                                 ││
│  │ Service: platform-api                                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Documentation (15)                                          │
│  • Routing Policy Configuration Guide                       │
│  • How Routing Policies are Evaluated                       │
│  • Routing Policy Best Practices                            │
│                                                              │
│  Code References (24)                                        │
│  • RoutingPolicyController.php                              │
│  • routing-policy.service.ts                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Navigation Patterns

### Breadcrumb Navigation
Every page includes breadcrumbs:
```
Home > Telephony Core > platform-freeswitch > API Reference
```

### Cross-References
Inline links to related content:
```markdown
The [platform-freeswitch](../platform-freeswitch/README.md) service
sends CDR events to [platform-cdr2sgapi](../platform-cdr2sgapi/README.md)
which stores them in [schema-cdr](../../schemas/schema-cdr/README.md).
```

### Related Content Section
Every page has "Related" section:
```markdown
## Related

### Services
- [platform-dialplan](link) - Dial plan configuration
- [platform-fscore](link) - FreeSWITCH scripts

### Documentation
- [Call Flow Overview](link)
- [FreeSWITCH Configuration Guide](link)

### External
- [Confluence: FreeSWITCH Operations](confluence-link)
- [Docs360: FreeSWITCH FAQ](docs360-link)
```

### Quick Navigation Sidebar
Sticky sidebar on service pages:
```
On This Page
├── Overview
├── Architecture
├── API Reference
│   ├── Endpoints
│   └── Authentication
├── Data Models
│   ├── Tables
│   └── Relationships
├── Configuration
└── Operations
    ├── Deployment
    ├── Monitoring
    └── Troubleshooting
```

---

## Implementation Approach

### Phase 1: Static Site Generation

**Technology:** MkDocs Material or Docusaurus

**Features:**
- Markdown rendering
- Navigation sidebar
- Search (built-in)
- Dark/light mode
- Mobile responsive

**Structure:**
```
docs/
├── index.md                    # Home page
├── getting-started/
│   ├── overview.md
│   ├── architecture.md
│   └── onboarding.md
├── domains/
│   ├── index.md               # Domain catalog
│   ├── telephony-core/
│   │   ├── index.md
│   │   └── data-flows.md
│   └── ...
├── services/
│   ├── index.md               # Service catalog
│   └── {service-name}/
│       ├── README.md
│       ├── api.md
│       ├── data.md
│       └── operations.md
├── schemas/
│   ├── index.md               # Schema catalog
│   └── {schema-name}/
│       └── README.md
└── search/
    └── index.json             # Search index
```

### Phase 2: Enhanced Search

**Add:**
- Elasticsearch/Algolia integration
- Faceted search (by domain, type, language)
- Search suggestions
- Recent searches

### Phase 3: Interactive Features

**Add:**
- Dependency graph visualization (D3.js)
- API playground (try endpoints)
- Code snippet copying
- Feedback collection

### Phase 4: Personalization

**Add:**
- Bookmarks
- Reading history
- Team dashboards
- Custom views

---

## Metrics & Success Criteria

### Quantitative
| Metric | Target |
|--------|--------|
| Time to find any service | < 30 seconds |
| Search success rate | > 90% |
| Page load time | < 2 seconds |
| Search response time | < 200ms |
| Documentation coverage | 100% Tier 1, 80% Tier 2 |

### Qualitative
- Users can answer common questions without asking colleagues
- New joiners onboard faster
- Architects can plan changes with confidence
- Operators can resolve issues independently

---

## Mockup: Mobile View

```
┌─────────────────────┐
│  ☰  Natterbox Docs  │
├─────────────────────┤
│ 🔍 Search...        │
├─────────────────────┤
│                     │
│ Quick Access        │
│ ┌─────┐ ┌─────┐    │
│ │Srvc │ │ API │    │
│ └─────┘ └─────┘    │
│                     │
│ Domains             │
│ ▶ Telephony Core    │
│ ▶ Integrations      │
│ ▶ AI & Convo        │
│ ▶ Analytics         │
│                     │
│ Recent              │
│ • platform-api      │
│ • cai-service       │
│                     │
└─────────────────────┘
```

---

## Next Steps

1. ✅ UX design complete
2. → Set up MkDocs Material or Docusaurus
3. → Generate docs for pilot services
4. → Build search index
5. → Deploy to internal hosting
6. → Gather user feedback
7. → Iterate
