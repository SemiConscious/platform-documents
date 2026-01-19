# Project Decisions

Key decisions made during this documentation project, with rationale.

---

## Decision Log

### DEC-001: Documentation Repository Location
**Date:** 2026-01-19  
**Decision:** Create dedicated repo `SemiConscious/platform-documents`  
**Alternatives Considered:**
- Use existing `redmatter/dino-docs` or `redmatter/aws-docs`
- Store in Confluence only
- Distribute docs across individual service repos

**Rationale:**
- Dedicated repo provides clean separation
- GitHub markdown is easier to iterate on than Confluence
- Centralized location aids discoverability
- Can sync to Confluence for wider audience later
- Version control provides full history

---

### DEC-002: Primary Format - Markdown with Mermaid
**Date:** 2026-01-19  
**Decision:** Use Markdown as primary format, Mermaid for diagrams  
**Rationale:**
- Markdown renders natively on GitHub
- Mermaid diagrams are code-based, easy to version and edit
- No external tooling required
- Can be converted to other formats if needed

---

### DEC-003: Project Tracking Approach
**Date:** 2026-01-19  
**Decision:** Track project state in `.project/` directory within the repo  
**Rationale:**
- Provides "memory" between AI-assisted sessions
- Version controlled alongside documentation
- Transparent and auditable
- No external tools required

---

### DEC-004: Phased Approach Starting with Inventory
**Date:** 2026-01-19  
**Decision:** Start with discovery/inventory phase before deep documentation  
**Alternatives Considered:**
- Depth-first: fully document one subsystem first
- Event-driven: document as needs arise

**Rationale:**
- Need to understand scope before diving deep
- Inventory provides foundation for all other work
- Helps identify existing documentation to leverage
- Enables better prioritization

---

## Decision Template

```markdown
### DEC-XXX: [Title]
**Date:** YYYY-MM-DD  
**Decision:** [What was decided]  
**Alternatives Considered:**
- [Alternative 1]
- [Alternative 2]

**Rationale:**
[Why this decision was made]

**Consequences:**
[Any implications or follow-up needed]
```

---

*Add new decisions as they arise during the project*
