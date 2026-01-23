"""
Salesforce documentation strategy.

Produces comprehensive Salesforce package documentation with:
- Custom object schemas with field documentation
- Apex class and trigger documentation
- Lightning Web Component documentation
- Flow and Process Builder documentation
- SOQL/DML operation mapping
- External callout documentation
"""

from pathlib import Path
from typing import Any, Optional
import re
import time

from ...analyzers.models import (
    AnalysisResult,
    ExtractedModel,
    ExtractedSideEffect,
    ModelType,
    SideEffectCategory,
)
from ...analyzers.repo_type_detector import RepoType
from .base import (
    DocumentationStrategy,
    DocumentSpec,
    DocumentSet,
    GeneratedDocument,
    QualityCriterion,
    QualityCriterionType,
)
from .factory import register_strategy


@register_strategy(RepoType.SALESFORCE)
class SalesforceStrategy(DocumentationStrategy):
    """
    Documentation strategy for Salesforce packages.
    
    Generates comprehensive Salesforce documentation including
    objects, Apex classes, triggers, and Lightning components.
    """
    
    repo_type = RepoType.SALESFORCE
    name = "salesforce"
    description = "Salesforce package documentation"
    
    def get_required_documents(self) -> list[DocumentSpec]:
        """Get required documents for Salesforce packages."""
        return [
            DocumentSpec(
                path="README.md",
                title="Overview",
                description="Package overview and quick start",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="objects.md",
                title="Custom Objects",
                description="Custom objects and fields",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="apex-classes.md",
                title="Apex Classes",
                description="Apex class documentation",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="triggers.md",
                title="Triggers",
                description="Trigger documentation",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="lwc-components.md",
                title="Lightning Components",
                description="Lightning Web Component documentation",
                required=False,
                priority=3,
            ),
            DocumentSpec(
                path="flows.md",
                title="Flows",
                description="Flow and Process Builder documentation",
                required=False,
                priority=3,
            ),
            DocumentSpec(
                path="integrations.md",
                title="Integrations",
                description="External API callouts and integrations",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="data-operations.md",
                title="Data Operations",
                description="SOQL/DML operations by object",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="permissions.md",
                title="Permissions",
                description="Permission sets and profiles",
                required=False,
                priority=4,
            ),
        ]
    
    def get_quality_criteria(self) -> list[QualityCriterion]:
        """Get quality criteria for Salesforce packages."""
        return [
            QualityCriterion(
                name="completeness",
                description="All required docs present",
                criterion_type=QualityCriterionType.COMPLETENESS,
                weight=1.0,
                min_threshold=0.90,
            ),
            QualityCriterion(
                name="object_coverage",
                description="All custom objects documented",
                criterion_type=QualityCriterionType.ACCURACY,
                weight=1.0,
                min_threshold=0.95,
            ),
            QualityCriterion(
                name="apex_coverage",
                description="All Apex classes documented",
                criterion_type=QualityCriterionType.ACCURACY,
                weight=0.9,
                min_threshold=0.90,
            ),
            QualityCriterion(
                name="examples",
                description="Code examples provided",
                criterion_type=QualityCriterionType.EXAMPLES,
                weight=0.8,
                min_threshold=0.75,
            ),
        ]
    
    async def generate(
        self,
        repo_path: Path,
        analysis: AnalysisResult,
        service_name: str,
        github_url: Optional[str] = None,
        existing_docs: Optional[dict[str, str]] = None,
    ) -> DocumentSet:
        """Generate comprehensive Salesforce documentation."""
        start_time = time.time()
        doc_set = DocumentSet(
            repo_name=service_name,
            repo_type=self.repo_type,
        )
        
        # Categorize Salesforce components
        custom_objects = self._extract_objects(analysis, repo_path)
        apex_classes = self._extract_apex_classes(analysis)
        triggers = self._extract_triggers(analysis)
        lwc_components = self._extract_lwc_components(analysis, repo_path)
        callouts = self._extract_callouts(analysis)
        soql_operations = self._extract_soql_operations(analysis)
        
        # Generate README
        readme = await self._generate_readme(
            service_name, github_url, analysis,
            custom_objects, apex_classes, triggers, lwc_components
        )
        doc_set.add_document(readme)
        
        # Generate objects documentation
        objects_doc = await self._generate_objects(
            service_name, github_url, custom_objects
        )
        doc_set.add_document(objects_doc)
        
        # Generate Apex documentation
        apex_doc = await self._generate_apex(
            service_name, github_url, apex_classes
        )
        doc_set.add_document(apex_doc)
        
        # Generate triggers documentation
        triggers_doc = await self._generate_triggers(
            service_name, github_url, triggers
        )
        doc_set.add_document(triggers_doc)
        
        # Generate LWC documentation if present
        if lwc_components:
            lwc_doc = await self._generate_lwc(
                service_name, github_url, lwc_components
            )
            doc_set.add_document(lwc_doc)
        
        # Generate integrations documentation
        integrations_doc = await self._generate_integrations(
            service_name, github_url, callouts
        )
        doc_set.add_document(integrations_doc)
        
        # Generate data operations documentation
        data_ops_doc = await self._generate_data_operations(
            service_name, github_url, soql_operations
        )
        doc_set.add_document(data_ops_doc)
        
        doc_set.generation_time = time.time() - start_time
        return doc_set
    
    def _extract_objects(
        self,
        analysis: AnalysisResult,
        repo_path: Path,
    ) -> list[dict]:
        """Extract custom object definitions."""
        objects = []
        
        # From analysis models
        for model in analysis.models:
            if model.model_type == ModelType.STRUCT and "__c" in model.name:
                objects.append({
                    "name": model.name,
                    "api_name": model.name,
                    "description": model.description,
                    "fields": model.fields,
                    "file": model.file,
                    "github_url": model.github_url,
                })
        
        # Also scan for .object-meta.xml files
        if repo_path.exists():
            object_files = list(repo_path.rglob("*.object-meta.xml"))
            for obj_file in object_files:
                obj_name = obj_file.stem.replace(".object-meta", "")
                if not any(o["name"] == obj_name for o in objects):
                    objects.append({
                        "name": obj_name,
                        "api_name": obj_name,
                        "description": f"Custom object defined in {obj_file.name}",
                        "fields": [],
                        "file": str(obj_file.relative_to(repo_path)),
                    })
        
        return objects
    
    def _extract_apex_classes(self, analysis: AnalysisResult) -> list[dict]:
        """Extract Apex class information."""
        classes = []
        
        for model in analysis.models:
            if model.model_type in [ModelType.CLASS, ModelType.SERVICE, ModelType.CONTROLLER]:
                # Check if it's an Apex class (from .cls file)
                if model.file and model.file.endswith(".cls"):
                    classes.append({
                        "name": model.name,
                        "description": model.description,
                        "type": self._classify_apex_class(model),
                        "methods": model.fields,  # Methods stored as fields
                        "file": model.file,
                        "line": model.line,
                        "github_url": model.github_url,
                        "decorators": model.decorators,
                    })
        
        return classes
    
    def _classify_apex_class(self, model: ExtractedModel) -> str:
        """Classify Apex class type based on patterns."""
        name = model.name.lower()
        decorators = [d.lower() for d in model.decorators]
        
        if "test" in name or "@istest" in decorators:
            return "Test"
        elif "controller" in name or "@auraenabled" in decorators:
            return "Controller"
        elif "batch" in name or "batchable" in str(model.decorators):
            return "Batch"
        elif "schedulable" in name or "schedule" in name:
            return "Scheduled"
        elif "trigger" in name:
            return "Trigger Handler"
        elif "service" in name:
            return "Service"
        elif "selector" in name or "dao" in name:
            return "Data Access"
        elif "util" in name or "helper" in name:
            return "Utility"
        else:
            return "General"
    
    def _extract_triggers(self, analysis: AnalysisResult) -> list[dict]:
        """Extract trigger information."""
        triggers = []
        
        for model in analysis.models:
            if "trigger" in model.decorators or (model.file and ".trigger" in model.file):
                triggers.append({
                    "name": model.name,
                    "object": self._extract_trigger_object(model),
                    "events": self._extract_trigger_events(model),
                    "description": model.description,
                    "file": model.file,
                    "github_url": model.github_url,
                })
        
        return triggers
    
    def _extract_trigger_object(self, model: ExtractedModel) -> str:
        """Extract the SObject a trigger operates on."""
        # Pattern: trigger TriggerName on ObjectName
        if model.description:
            match = re.search(r"on\s+(\w+)", model.description)
            if match:
                return match.group(1)
        
        # Try to infer from name
        name = model.name
        for suffix in ["Trigger", "_Trigger", "Handler"]:
            if name.endswith(suffix):
                return name[:-len(suffix)]
        
        return "Unknown"
    
    def _extract_trigger_events(self, model: ExtractedModel) -> list[str]:
        """Extract trigger events (before insert, after update, etc.)."""
        events = []
        desc = model.description or ""
        
        event_keywords = [
            "before insert", "after insert",
            "before update", "after update",
            "before delete", "after delete",
            "after undelete"
        ]
        
        for event in event_keywords:
            if event in desc.lower():
                events.append(event.title())
        
        return events if events else ["Unknown"]
    
    def _extract_lwc_components(
        self,
        analysis: AnalysisResult,
        repo_path: Path,
    ) -> list[dict]:
        """Extract Lightning Web Component information."""
        components = []
        
        # Scan for LWC directories
        if repo_path.exists():
            lwc_paths = [
                repo_path / "force-app" / "main" / "default" / "lwc",
                repo_path / "src" / "lwc",
            ]
            
            for lwc_path in lwc_paths:
                if lwc_path.exists():
                    for comp_dir in lwc_path.iterdir():
                        if comp_dir.is_dir() and not comp_dir.name.startswith("__"):
                            js_file = comp_dir / f"{comp_dir.name}.js"
                            html_file = comp_dir / f"{comp_dir.name}.html"
                            meta_file = comp_dir / f"{comp_dir.name}.js-meta.xml"
                            
                            components.append({
                                "name": comp_dir.name,
                                "has_js": js_file.exists(),
                                "has_html": html_file.exists(),
                                "has_meta": meta_file.exists(),
                                "path": str(comp_dir.relative_to(repo_path)),
                            })
        
        return components
    
    def _extract_callouts(self, analysis: AnalysisResult) -> list[dict]:
        """Extract HTTP callout information."""
        callouts = []
        
        for effect in analysis.side_effects:
            if effect.category == SideEffectCategory.HTTP:
                callouts.append({
                    "endpoint": effect.target,
                    "operation": effect.operation,
                    "handler": effect.handler,
                    "description": effect.description,
                    "file": effect.file,
                })
        
        return callouts
    
    def _extract_soql_operations(self, analysis: AnalysisResult) -> dict[str, list]:
        """Extract SOQL/DML operations grouped by object."""
        operations = {}
        
        for effect in analysis.side_effects:
            if effect.category == SideEffectCategory.DATABASE:
                obj = effect.target or "Unknown"
                if obj not in operations:
                    operations[obj] = []
                operations[obj].append({
                    "operation": effect.operation,
                    "handler": effect.handler,
                    "description": effect.description,
                    "file": effect.file,
                })
        
        return operations
    
    async def _generate_readme(
        self,
        service_name: str,
        github_url: Optional[str],
        analysis: AnalysisResult,
        custom_objects: list,
        apex_classes: list,
        triggers: list,
        lwc_components: list,
    ) -> GeneratedDocument:
        """Generate package overview README."""
        content = f"""---
title: {service_name}
description: Salesforce package documentation
generated: true
type: salesforce
---

# {service_name}

## Overview

This is a Salesforce managed/unmanaged package that provides custom functionality.

## Package Contents

| Component Type | Count |
|----------------|-------|
| Custom Objects | {len(custom_objects)} |
| Apex Classes | {len(apex_classes)} |
| Triggers | {len(triggers)} |
| Lightning Components | {len(lwc_components)} |

## Architecture

```mermaid
flowchart TB
    subgraph UI[User Interface]
        LWC[Lightning Components]
        VF[Visualforce Pages]
    end
    
    subgraph Controllers[Controllers]
        AC[Apex Controllers]
    end
    
    subgraph Business[Business Logic]
        Services[Service Classes]
        Handlers[Trigger Handlers]
    end
    
    subgraph Data[Data Layer]
        Objects[(Custom Objects)]
        Selectors[Selector Classes]
    end
    
    subgraph External[External Systems]
        API[External APIs]
    end
    
    LWC --> AC
    VF --> AC
    AC --> Services
    Services --> Selectors
    Selectors --> Objects
    Services --> API
    Handlers --> Services
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [Custom Objects](./objects.md) | Object schemas and field documentation |
| [Apex Classes](./apex-classes.md) | Apex class reference |
| [Triggers](./triggers.md) | Trigger documentation |
| [Lightning Components](./lwc-components.md) | LWC documentation |
| [Integrations](./integrations.md) | External API callouts |
| [Data Operations](./data-operations.md) | SOQL/DML reference |

## Quick Start

### Deploy to Scratch Org

```bash
# Create scratch org
sfdx force:org:create -f config/project-scratch-def.json -a MyScratchOrg

# Push source
sfdx force:source:push -u MyScratchOrg

# Assign permission set
sfdx force:user:permset:assign -n {service_name}_User -u MyScratchOrg

# Open org
sfdx force:org:open -u MyScratchOrg
```

### Deploy to Sandbox/Production

```bash
# Convert to metadata format
sfdx force:source:convert -d deploy

# Deploy
sfdx force:mdapi:deploy -d deploy -u TargetOrg -w 10
```

"""
        
        if github_url:
            content += f"## Source\n\n- [Repository]({github_url})\n"
        
        return GeneratedDocument(
            path="README.md",
            title=f"{service_name} Overview",
            content=content,
        )
    
    async def _generate_objects(
        self,
        service_name: str,
        github_url: Optional[str],
        custom_objects: list,
    ) -> GeneratedDocument:
        """Generate custom objects documentation."""
        content = f"""---
title: {service_name} Custom Objects
description: Custom object schema documentation
generated: true
---

# {service_name} Custom Objects

## Object Summary

| Object | API Name | Fields |
|--------|----------|--------|
"""
        
        for obj in custom_objects:
            field_count = len(obj.get("fields", []))
            content += f"| {obj['name']} | `{obj['api_name']}` | {field_count} |\n"
        
        content += "\n## Object Details\n\n"
        
        for obj in custom_objects:
            content += f"### {obj['name']}\n\n"
            content += f"**API Name:** `{obj['api_name']}`\n\n"
            
            if obj.get("description"):
                content += f"{obj['description']}\n\n"
            
            if github_url and obj.get("file"):
                content += f"**Source:** [{obj['file']}]({github_url}/blob/main/{obj['file']})\n\n"
            
            fields = obj.get("fields", [])
            if fields:
                content += "#### Fields\n\n"
                content += "| Field | API Name | Type | Required | Description |\n"
                content += "|-------|----------|------|----------|-------------|\n"
                for field in fields:
                    required = "Yes" if not field.nullable else "No"
                    desc = field.description or "N/A"
                    if len(desc) > 40:
                        desc = desc[:37] + "..."
                    content += f"| {field.name} | `{field.name}` | {field.type} | {required} | {desc} |\n"
                content += "\n"
            
            content += "---\n\n"
        
        return GeneratedDocument(
            path="objects.md",
            title=f"{service_name} Custom Objects",
            content=content,
        )
    
    async def _generate_apex(
        self,
        service_name: str,
        github_url: Optional[str],
        apex_classes: list,
    ) -> GeneratedDocument:
        """Generate Apex class documentation."""
        content = f"""---
title: {service_name} Apex Classes
description: Apex class reference
generated: true
---

# {service_name} Apex Classes

## Class Summary

| Class | Type | Methods | File |
|-------|------|---------|------|
"""
        
        for cls in apex_classes:
            methods = len(cls.get("methods", []))
            file_link = self._github_link(github_url, cls["file"]) if github_url else cls["file"]
            content += f"| {cls['name']} | {cls['type']} | {methods} | {file_link} |\n"
        
        content += "\n## Classes by Type\n\n"
        
        # Group by type
        by_type = {}
        for cls in apex_classes:
            cls_type = cls["type"]
            if cls_type not in by_type:
                by_type[cls_type] = []
            by_type[cls_type].append(cls)
        
        for cls_type, classes in sorted(by_type.items()):
            content += f"### {cls_type} Classes\n\n"
            
            for cls in classes:
                content += f"#### {cls['name']}\n\n"
                
                if cls.get("description"):
                    content += f"{cls['description']}\n\n"
                
                if github_url and cls.get("file"):
                    line = cls.get("line", 1)
                    content += f"**Source:** [{cls['file']}]({github_url}/blob/main/{cls['file']}#L{line})\n\n"
                
                # List methods
                methods = cls.get("methods", [])
                if methods:
                    content += "**Methods:**\n\n"
                    content += "| Method | Return Type | Description |\n"
                    content += "|--------|-------------|-------------|\n"
                    for method in methods[:15]:
                        desc = method.description or "N/A"
                        if len(desc) > 40:
                            desc = desc[:37] + "..."
                        content += f"| `{method.name}` | {method.type} | {desc} |\n"
                    content += "\n"
                
                content += "---\n\n"
        
        return GeneratedDocument(
            path="apex-classes.md",
            title=f"{service_name} Apex Classes",
            content=content,
        )
    
    async def _generate_triggers(
        self,
        service_name: str,
        github_url: Optional[str],
        triggers: list,
    ) -> GeneratedDocument:
        """Generate trigger documentation."""
        content = f"""---
title: {service_name} Triggers
description: Trigger documentation
generated: true
---

# {service_name} Triggers

## Trigger Summary

| Trigger | Object | Events |
|---------|--------|--------|
"""
        
        for trigger in triggers:
            events = ", ".join(trigger.get("events", ["Unknown"]))
            content += f"| {trigger['name']} | {trigger['object']} | {events} |\n"
        
        content += "\n## Trigger Details\n\n"
        
        for trigger in triggers:
            content += f"### {trigger['name']}\n\n"
            content += f"**Object:** `{trigger['object']}`\n\n"
            content += f"**Events:** {', '.join(trigger.get('events', ['Unknown']))}\n\n"
            
            if trigger.get("description"):
                content += f"{trigger['description']}\n\n"
            
            if github_url and trigger.get("file"):
                content += f"**Source:** [{trigger['file']}]({github_url}/blob/main/{trigger['file']})\n\n"
            
            # Trigger execution order note
            content += """**Execution Order:**

1. System validation rules
2. Before triggers
3. System validation rules (again)
4. After triggers
5. Assignment rules
6. Workflow rules
7. Escalation rules
8. Process Builder
9. Flows

"""
            
            content += "---\n\n"
        
        return GeneratedDocument(
            path="triggers.md",
            title=f"{service_name} Triggers",
            content=content,
        )
    
    async def _generate_lwc(
        self,
        service_name: str,
        github_url: Optional[str],
        lwc_components: list,
    ) -> GeneratedDocument:
        """Generate Lightning Web Component documentation."""
        content = f"""---
title: {service_name} Lightning Components
description: Lightning Web Component documentation
generated: true
---

# {service_name} Lightning Web Components

## Component Summary

| Component | JavaScript | HTML | Meta |
|-----------|------------|------|------|
"""
        
        for comp in lwc_components:
            js = "✓" if comp["has_js"] else "✗"
            html = "✓" if comp["has_html"] else "✗"
            meta = "✓" if comp["has_meta"] else "✗"
            content += f"| {comp['name']} | {js} | {html} | {meta} |\n"
        
        content += "\n## Component Details\n\n"
        
        for comp in lwc_components:
            content += f"### {comp['name']}\n\n"
            content += f"**Path:** `{comp['path']}`\n\n"
            
            if github_url:
                content += f"**Source:** [{comp['path']}]({github_url}/tree/main/{comp['path']})\n\n"
            
            content += "**Files:**\n\n"
            content += f"- `{comp['name']}.js` - Component logic\n"
            content += f"- `{comp['name']}.html` - Component template\n"
            content += f"- `{comp['name']}.js-meta.xml` - Component metadata\n"
            
            content += "\n---\n\n"
        
        return GeneratedDocument(
            path="lwc-components.md",
            title=f"{service_name} Lightning Components",
            content=content,
        )
    
    async def _generate_integrations(
        self,
        service_name: str,
        github_url: Optional[str],
        callouts: list,
    ) -> GeneratedDocument:
        """Generate integrations documentation."""
        content = f"""---
title: {service_name} Integrations
description: External API integrations
generated: true
---

# {service_name} Integrations

## Overview

This package integrates with external systems via HTTP callouts.

## External Callouts

"""
        
        if callouts:
            content += "| Endpoint | Operation | Class | Description |\n"
            content += "|----------|-----------|-------|-------------|\n"
            for callout in callouts:
                endpoint = callout.get("endpoint", "N/A")
                if len(endpoint) > 40:
                    endpoint = endpoint[:37] + "..."
                desc = callout.get("description", "N/A")
                if len(desc) > 40:
                    desc = desc[:37] + "..."
                content += f"| `{endpoint}` | {callout['operation']} | {callout['handler']} | {desc} |\n"
        else:
            content += "*No external callouts detected.*\n"
        
        content += """

## Named Credentials

External systems should be configured using Named Credentials for security:

| Named Credential | Purpose |
|------------------|---------|
| External_API | Main external API endpoint |

## Remote Site Settings

Ensure the following Remote Site Settings are configured:

| Name | URL | Active |
|------|-----|--------|
| External_API | https://api.example.com | Yes |

## Security Considerations

- All callouts use HTTPS
- Authentication via Named Credentials
- Sensitive data not logged
- Timeout handling implemented

"""
        
        return GeneratedDocument(
            path="integrations.md",
            title=f"{service_name} Integrations",
            content=content,
        )
    
    async def _generate_data_operations(
        self,
        service_name: str,
        github_url: Optional[str],
        soql_operations: dict,
    ) -> GeneratedDocument:
        """Generate SOQL/DML operations documentation."""
        content = f"""---
title: {service_name} Data Operations
description: SOQL and DML operations reference
generated: true
---

# {service_name} Data Operations

## Overview

This document maps all database operations (SOQL queries and DML statements) by object.

## Operations by Object

"""
        
        if soql_operations:
            for obj, ops in sorted(soql_operations.items()):
                content += f"### {obj}\n\n"
                content += "| Operation | Class/Method | Description |\n"
                content += "|-----------|--------------|-------------|\n"
                for op in ops:
                    handler = op.get("handler", "N/A")
                    desc = op.get("description", "N/A")
                    if len(desc) > 50:
                        desc = desc[:47] + "..."
                    content += f"| {op['operation']} | `{handler}` | {desc} |\n"
                content += "\n"
        else:
            content += "*No database operations detected.*\n\n"
        
        content += """## SOQL Best Practices

1. **Bulkification**: Always design for bulk operations
2. **Selective Queries**: Use indexed fields in WHERE clauses
3. **Limit Results**: Use LIMIT when appropriate
4. **Avoid SOQL in Loops**: Query outside loops

## DML Best Practices

1. **Bulkify DML**: Use lists for insert/update/delete
2. **Error Handling**: Use Database methods for partial success
3. **Governor Limits**: Monitor DML rows and statements

## Example Patterns

### Selector Pattern

```apex
public class AccountSelector {
    public static List<Account> getAccountsByIds(Set<Id> accountIds) {
        return [
            SELECT Id, Name, Industry
            FROM Account
            WHERE Id IN :accountIds
        ];
    }
}
```

### Service Pattern

```apex
public class AccountService {
    public static void updateAccounts(List<Account> accounts) {
        if (accounts.isEmpty()) return;
        
        Database.SaveResult[] results = Database.update(accounts, false);
        // Handle partial failures
    }
}
```
"""
        
        return GeneratedDocument(
            path="data-operations.md",
            title=f"{service_name} Data Operations",
            content=content,
        )
