# Gap Analysis: doc-agent vs. Strategic Requirements

## Executive Summary

This analysis compares the current `doc-agent` capabilities against the strategic documentation requirements defined in the plan. **Of 15 strategic requirements, 6 are fully met, 5 are partially met, and 4 are not implemented.**

## Current Capabilities Overview

### Architecture
- **5-phase pipeline**: Discovery → Enrichment → Analysis → Generation → Quality
- **Knowledge graph**: NetworkX-based with entities (Service, Domain, API, Schema) and relations
- **Multi-language analysis**: 12 languages (PHP, TypeScript, Go, Python, C/C++, Terraform, Apex, etc.)
- **MCP integration**: Confluence, Docs360, GitHub, Jira via Natterbox MCP server
- **Local repo support**: Can analyze local clones to avoid API rate limits

### Agents
| Phase | Agents | Status |
|-------|--------|--------|
| Discovery | RepositoryScannerAgent, LocalCodeAnalyzer | ✅ Working |
| Enrichment | ConfluenceEnricherAgent, Docs360EnricherAgent | ✅ Working |
| Analysis | ArchitectureInferenceAgent, DomainMapperAgent | ✅ Working |
| Generation | TechnicalWriterAgent, APIDocumenterAgent, SchemaDocumenterAgent, StrategyDocumenterAgent | ✅ Working |
| Quality | CrossReferenceAgent, IndexGeneratorAgent, QualityCheckerAgent | ✅ Working |

---

## Strategic Requirements Assessment

### Layer 1: Discovery Layer

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| Platform Overview | ⚠️ Partial | OverviewWriterAgent generates high-level docs | Missing: Business capability mapping |
| Capability Map | ❌ Missing | Not implemented | Need: Business capability → Service → Repo mapping |
| Service Catalog | ✅ Complete | Knowledge graph stores services with metadata | - |
| Repository Index | ⚠️ Partial | Can list repos | Missing: Classification, activity metrics, health |
| Unified Search | ❌ Missing | No search implementation | Need: Full-text + semantic search across all sources |

### Layer 2: Domain Layer

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| Domain Organization | ⚠️ Partial | DomainMapperAgent creates domains | Missing: Validated domain boundaries from strategy doc |
| Domain Overviews | ⚠️ Partial | Can generate domain docs | Missing: Stakeholder info, decision records |
| Data Flow Diagrams | ✅ Complete | ArchitectureInferenceAgent generates Mermaid | - |
| Domain Glossaries | ❌ Missing | Not implemented | Need: Per-domain terminology extraction |

### Layer 3: Service Layer

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| Service README | ✅ Complete | TechnicalWriterAgent generates | - |
| Architecture Docs | ✅ Complete | Generated with Mermaid diagrams | - |
| API Reference | ✅ Complete | APIDocumenterAgent extracts endpoints | - |
| Data Models | ✅ Complete | SchemaDocumenterAgent documents models | - |
| Configuration Reference | ✅ Complete | Extracted from code analysis | - |
| Operations Runbook | ⚠️ Partial | Basic operations.md | Missing: Incident response, monitoring setup |

### Layer 4: Repository Layer

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| Repository README | ✅ Complete | RepositoryDocumenterAgent generates | - |
| Structure Explanation | ✅ Complete | Key files/directories documented | - |
| Dependencies | ⚠️ Partial | Package dependencies extracted | Missing: Service-level dependencies |
| Activity Metrics | ❌ Missing | No commit history analysis | Need: Last commit, frequency, contributor count |
| Health Status | ❌ Missing | No CI/CD integration | Need: Build status, test coverage, security scan |

### Layer 5: Code Layer

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| Database Schemas | ✅ Complete | SchemaDocumenterAgent | - |
| API Specifications | ✅ Complete | OpenAPI/GraphQL extraction | - |
| Configuration Reference | ✅ Complete | Env vars, config files extracted | - |
| Function Documentation | ⚠️ Partial | Key functions identified | Missing: Full AST-level docs for all functions |

### Cross-Cutting Requirements

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| API-to-Database Tracing | ⚠️ Partial | Knowledge graph has relations | Missing: Deep call-chain tracing |
| Dependency Graph | ⚠️ Partial | Relations in knowledge graph | Missing: Visualization, impact analysis |
| Data Lineage | ❌ Missing | Not implemented | Need: Track data flow across services |
| Technology Matrix | ❌ Missing | Languages detected but not aggregated | Need: Tech usage summary across all repos |
| Ownership Map | ❌ Missing | Not implemented | Need: Team/individual → Service → Repo mapping |

### Strategic Analysis Requirements

| Requirement | Status | Current State | Gap |
|-------------|--------|---------------|-----|
| Activity Analysis | ❌ Missing | No commit history | Need: Staleness detection, trend analysis |
| Criticality Assessment | ❌ Missing | Not implemented | Need: Tier assignment based on criteria |
| Consolidation Opportunities | ❌ Missing | Not implemented | Need: Duplicate detection, merge candidates |
| Technical Debt Index | ❌ Missing | Not implemented | Need: Framework currency, test coverage gaps |

---

## Detailed Gap Analysis

### Gap 1: Unified Search (Critical)

**Current State:**
- No search functionality
- Users must navigate folder structure

**Required:**
- Full-text search across all generated docs
- Semantic search for concept queries
- Code search (function names, classes)
- Cross-source search (includes Confluence, Docs360)

**Implementation Options:**
1. **Elasticsearch/OpenSearch** - Full-featured, requires infrastructure
2. **SQLite FTS** - Lightweight, file-based
3. **Vector database** - Semantic search via embeddings (Pinecone, Weaviate)
4. **MeiliSearch** - Modern, fast, easy to deploy

**Recommendation:** SQLite FTS for MVP, add vector search later

---

### Gap 2: API-to-Database Tracing (Critical)

**Current State:**
- Knowledge graph has `DEPENDS_ON`, `USES_SCHEMA` relations
- No deep code-level tracing

**Required:**
- Trace: API Endpoint → Handler Function → Database Query → Table/Field
- Show what fields are read vs. written
- Show validation logic applied

**Implementation:**
```python
# New agent: CodeTraceAgent
class CodeTraceAgent(BaseAgent):
    """Traces API calls through code to database operations."""
    
    async def trace_endpoint(self, endpoint: str) -> EndpointTrace:
        # 1. Find handler function from route
        # 2. AST analysis of handler
        # 3. Identify DB calls (ORM, raw SQL)
        # 4. Extract table/field references
        # 5. Build trace chain
        pass
```

**Schema repo linking:**
- Parse `schema-*` repos for table definitions
- Link `platform-api` code to schema tables
- Auto-detect ORM patterns (Kohana ORM, etc.)

---

### Gap 3: Activity Analysis (Important)

**Current State:**
- Repos cloned but commit history not analyzed

**Required:**
- Last meaningful commit (excluding dep bumps)
- Commit frequency (active vs. dormant)
- Contributor count and distribution
- PR/issue activity

**Implementation:**
```python
# New analyzer: ActivityAnalyzer
class ActivityAnalyzer:
    """Analyzes repository activity from git history."""
    
    def analyze(self, repo_path: Path) -> ActivityMetrics:
        # git log analysis
        # Classify: active, maintenance, legacy, dormant
        pass
```

---

### Gap 4: Criticality Tier Assignment (Important)

**Current State:**
- All repos treated equally
- No tiered documentation depth

**Required:**
- Auto-assign tiers based on criteria from strategy doc
- Generate different doc depth per tier
- Flag tier in generated docs

**Implementation:**
```python
# Extend DocumentationStrategy
class TieredDocumentationStrategy:
    """Assigns documentation depth based on criticality tier."""
    
    def assign_tier(self, service: Service) -> int:
        # Check dependency count
        # Check naming patterns
        # Check activity level
        # Return tier 1-4
        pass
    
    def get_required_docs(self, tier: int) -> list[str]:
        # Tier 1: Full suite (10-15 docs)
        # Tier 4: Index only (1 doc)
        pass
```

---

### Gap 5: Technology Matrix (Moderate)

**Current State:**
- Languages detected per repo
- No aggregated view

**Required:**
- Summary: "150 PHP repos, 120 TypeScript repos..."
- Framework breakdown
- Version tracking (PHP 7.4 vs 8.2)

**Implementation:**
```python
# New report generator
class TechnologyMatrixGenerator:
    """Generates technology usage summary."""
    
    def generate(self) -> TechnologyMatrix:
        # Aggregate language stats from all repos
        # Detect framework versions
        # Output markdown table
        pass
```

---

### Gap 6: Ownership Mapping (Moderate)

**Current State:**
- Not tracked

**Required:**
- Team → Services mapping
- Individual → Primary maintainer mapping
- CODEOWNERS integration

**Implementation:**
- Parse CODEOWNERS files
- GitHub team/org integration via MCP
- Manual mapping file for overrides

---

### Gap 7: Domain Glossary (Low)

**Current State:**
- Not implemented

**Required:**
- Per-domain terminology
- Acronym definitions
- Cross-domain term disambiguation

**Implementation:**
- LLM extraction of domain terms from docs
- Manual curation interface
- Auto-link terms in generated docs

---

## Implementation Roadmap

### Phase 1: Critical Gaps (Required for Pilot)

| Gap | Priority | Effort | Dependencies |
|-----|----------|--------|--------------|
| Criticality Tier Assignment | P0 | 2 days | None |
| Schema-to-Code Linking | P0 | 3 days | None |
| API-to-DB Tracing (Basic) | P0 | 5 days | Schema linking |

### Phase 2: Important Gaps (Required for Full Rollout)

| Gap | Priority | Effort | Dependencies |
|-----|----------|--------|--------------|
| Activity Analysis | P1 | 2 days | None |
| Technology Matrix | P1 | 1 day | None |
| Dependency Graph Visualization | P1 | 2 days | None |
| Domain Boundaries (from strategy) | P1 | 1 day | Domain validation doc |

### Phase 3: Search & Discovery (Required for UX)

| Gap | Priority | Effort | Dependencies |
|-----|----------|--------|--------------|
| Full-Text Search (SQLite FTS) | P2 | 3 days | Generated docs |
| Semantic Search (Embeddings) | P2 | 5 days | Vector DB |
| Search UI | P2 | 3 days | Search backend |

### Phase 4: Strategic Analysis (Required for V2 Planning)

| Gap | Priority | Effort | Dependencies |
|-----|----------|--------|--------------|
| Ownership Mapping | P3 | 2 days | GitHub teams |
| Technical Debt Index | P3 | 3 days | Activity analysis |
| Consolidation Opportunities | P3 | 3 days | Full dependency graph |

---

## Recommended Immediate Actions

### 1. Implement Tiered Documentation
```python
# In StrategyDocumenterAgent
def get_tier(self, service: Service) -> int:
    """Assign documentation tier based on criticality."""
    tier1_patterns = ['api', 'gateway', 'freeswitch', 'opensips']
    if any(p in service.name.lower() for p in tier1_patterns):
        return 1
    # ... more logic
```

### 2. Add Schema Repository Linking
```python
# In LocalCodeAnalyzer
def link_schemas(self, service: Service, schemas: list[Schema]):
    """Link service to database schemas it uses."""
    # Parse imports/requires for schema-* packages
    # Add USES_SCHEMA relations to knowledge graph
```

### 3. Integrate Domain Boundaries
```python
# Load validated domains from strategy doc
VALIDATED_DOMAINS = {
    "telephony-core": ["platform-freeswitch", "platform-opensips", ...],
    "integrations-crm": ["natterbox-avs-sfdx", "omnichannel-omniservice", ...],
    # ...
}
```

### 4. Add Basic Search
```python
# New module: search/index.py
class SearchIndex:
    """SQLite FTS-based search index."""
    
    def index_document(self, path: Path, content: str):
        # Add to FTS index
        pass
    
    def search(self, query: str) -> list[SearchResult]:
        # FTS query with ranking
        pass
```

---

## Summary

| Category | Complete | Partial | Missing | Total |
|----------|----------|---------|---------|-------|
| Discovery Layer | 1 | 2 | 2 | 5 |
| Domain Layer | 1 | 2 | 1 | 4 |
| Service Layer | 5 | 1 | 0 | 6 |
| Repository Layer | 2 | 1 | 2 | 5 |
| Code Layer | 3 | 1 | 0 | 4 |
| Cross-Cutting | 0 | 2 | 3 | 5 |
| Strategic | 0 | 0 | 4 | 4 |
| **Total** | **12** | **9** | **12** | **33** |

**Overall Readiness: 36% Complete, 27% Partial, 36% Missing**

The most critical gaps for the pilot are:
1. **Criticality Tier Assignment** - Needed to prioritize documentation effort
2. **Schema-to-Code Linking** - Required for API-to-DB tracing
3. **Domain Integration** - Use validated domains from strategy

The search functionality can be deferred until after initial documentation is generated.
