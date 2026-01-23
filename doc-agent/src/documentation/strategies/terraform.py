"""
Terraform/Infrastructure documentation strategy.

Produces beautiful infrastructure documentation with:
- Infrastructure diagrams showing all resources
- Variable documentation with descriptions and defaults
- Output documentation for consumers
- Data flow diagrams for network paths
- Consumer tracking (who depends on this module)
"""

from pathlib import Path
from typing import Any, Optional
import re
import time

from ...analyzers.models import AnalysisResult, ExtractedModel, ModelType
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


# AWS service groupings for diagram organization
AWS_SERVICE_GROUPS = {
    "compute": ["aws_instance", "aws_launch_template", "aws_autoscaling_group", "aws_ecs", "aws_lambda", "aws_batch"],
    "networking": ["aws_vpc", "aws_subnet", "aws_route", "aws_security_group", "aws_network", "aws_lb", "aws_alb", "aws_nlb", "aws_elb", "aws_nat_gateway", "aws_internet_gateway", "aws_vpn", "aws_transit_gateway"],
    "storage": ["aws_s3", "aws_ebs", "aws_efs", "aws_fsx", "aws_glacier"],
    "database": ["aws_rds", "aws_dynamodb", "aws_elasticache", "aws_redshift", "aws_aurora", "aws_docdb", "aws_neptune"],
    "security": ["aws_iam", "aws_kms", "aws_secretsmanager", "aws_acm", "aws_waf", "aws_shield"],
    "messaging": ["aws_sqs", "aws_sns", "aws_kinesis", "aws_eventbridge", "aws_mq"],
    "monitoring": ["aws_cloudwatch", "aws_cloudtrail", "aws_config", "aws_guardduty"],
    "api": ["aws_api_gateway", "aws_appsync"],
    "dns": ["aws_route53"],
    "cdn": ["aws_cloudfront"],
    "other": [],
}


@register_strategy(RepoType.TERRAFORM)
class TerraformStrategy(DocumentationStrategy):
    """
    Documentation strategy for Terraform/Infrastructure repositories.
    
    Generates comprehensive infrastructure documentation including
    architecture diagrams, variable docs, and data flow visualizations.
    """
    
    repo_type = RepoType.TERRAFORM
    name = "terraform"
    description = "Infrastructure as Code documentation"
    
    def get_required_documents(self) -> list[DocumentSpec]:
        """Get required documents for Terraform repos."""
        return [
            DocumentSpec(
                path="README.md",
                title="Overview",
                description="Module overview and quick start",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="architecture.md",
                title="Architecture",
                description="Infrastructure architecture diagram",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="resources.md",
                title="Resources",
                description="All resources created by this module",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="variables.md",
                title="Variables",
                description="Input variables and their descriptions",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="outputs.md",
                title="Outputs",
                description="Outputs available for consumers",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="data-flows.md",
                title="Data Flows",
                description="Network and data flow diagrams",
                required=False,
                priority=3,
            ),
            DocumentSpec(
                path="consumers.md",
                title="Consumers",
                description="Who depends on this module",
                required=False,
                priority=3,
            ),
            DocumentSpec(
                path="operations.md",
                title="Operations",
                description="How to plan, apply, and manage state",
                required=False,
                priority=3,
            ),
        ]
    
    def get_quality_criteria(self) -> list[QualityCriterion]:
        """Get quality criteria for Terraform repos."""
        return [
            QualityCriterion(
                name="completeness",
                description="All required docs present",
                criterion_type=QualityCriterionType.COMPLETENESS,
                weight=1.0,
                min_threshold=0.90,
            ),
            QualityCriterion(
                name="diagrams",
                description="Infrastructure diagrams present",
                criterion_type=QualityCriterionType.DIAGRAMS,
                weight=1.0,
                min_threshold=0.85,
            ),
            QualityCriterion(
                name="variables_documented",
                description="All variables have descriptions",
                criterion_type=QualityCriterionType.ACCURACY,
                weight=0.9,
                min_threshold=0.95,
            ),
            QualityCriterion(
                name="examples",
                description="Usage examples provided",
                criterion_type=QualityCriterionType.EXAMPLES,
                weight=0.8,
                min_threshold=0.80,
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
        """Generate comprehensive Terraform documentation."""
        start_time = time.time()
        doc_set = DocumentSet(
            repo_name=service_name,
            repo_type=self.repo_type,
        )
        
        # Parse Terraform-specific data from analysis
        resources = self._extract_resources(analysis)
        variables = self._extract_variables(analysis)
        outputs = self._extract_outputs(analysis)
        data_sources = self._extract_data_sources(analysis)
        modules = self._extract_modules(analysis)
        providers = self._extract_providers(analysis)
        
        # Generate README with overview
        readme = await self._generate_readme(
            repo_path, service_name, github_url,
            resources, variables, outputs, modules, providers
        )
        doc_set.add_document(readme)
        
        # Generate architecture diagram
        arch = await self._generate_architecture(
            service_name, github_url, resources, data_sources, modules
        )
        doc_set.add_document(arch)
        
        # Generate resources documentation
        resources_doc = await self._generate_resources(
            service_name, github_url, resources
        )
        doc_set.add_document(resources_doc)
        
        # Generate variables documentation
        vars_doc = await self._generate_variables(
            service_name, github_url, variables
        )
        doc_set.add_document(vars_doc)
        
        # Generate outputs documentation
        outputs_doc = await self._generate_outputs(
            service_name, github_url, outputs
        )
        doc_set.add_document(outputs_doc)
        
        # Generate data flows if we have network resources
        if self._has_network_resources(resources):
            flows_doc = await self._generate_data_flows(
                service_name, github_url, resources
            )
            doc_set.add_document(flows_doc)
        
        # Generate operations guide
        ops_doc = await self._generate_operations(
            service_name, github_url, providers
        )
        doc_set.add_document(ops_doc)
        
        doc_set.generation_time = time.time() - start_time
        return doc_set
    
    def _extract_resources(self, analysis: AnalysisResult) -> list[dict]:
        """Extract Terraform resources from analysis."""
        resources = []
        for model in analysis.models:
            if model.model_type == ModelType.STRUCT and "resource" in model.decorators:
                # Parse resource type from name (e.g., "aws_instance.main")
                parts = model.name.split(".")
                if len(parts) >= 2:
                    resource_type = parts[0]
                    resource_name = parts[1]
                else:
                    resource_type = model.name
                    resource_name = "main"
                
                resources.append({
                    "type": resource_type,
                    "name": resource_name,
                    "full_name": model.name,
                    "file": model.file,
                    "line": model.line,
                    "description": model.description,
                    "fields": model.fields,
                    "github_url": model.github_url,
                })
        
        return resources
    
    def _extract_variables(self, analysis: AnalysisResult) -> list[dict]:
        """Extract Terraform variables from analysis config."""
        variables = []
        for config in analysis.config:
            if config.source == "terraform_variable":
                variables.append({
                    "name": config.key.replace("var.", ""),
                    "description": config.description,
                    "default": config.default,
                    "required": config.required,
                    "file": config.file,
                    "line": config.line,
                    "github_url": config.github_url,
                })
        
        return variables
    
    def _extract_outputs(self, analysis: AnalysisResult) -> list[dict]:
        """Extract Terraform outputs from analysis."""
        outputs = []
        for model in analysis.models:
            if "output" in model.decorators:
                outputs.append({
                    "name": model.name.replace("output.", ""),
                    "description": model.description,
                    "file": model.file,
                    "line": model.line,
                    "github_url": model.github_url,
                })
        
        return outputs
    
    def _extract_data_sources(self, analysis: AnalysisResult) -> list[dict]:
        """Extract Terraform data sources."""
        data_sources = []
        for model in analysis.models:
            if "data_source" in model.decorators:
                data_sources.append({
                    "type": model.name,
                    "description": model.description,
                    "file": model.file,
                    "github_url": model.github_url,
                })
        
        return data_sources
    
    def _extract_modules(self, analysis: AnalysisResult) -> list[dict]:
        """Extract module calls from analysis."""
        modules = []
        for dep in analysis.dependencies:
            if dep.import_path and ("module" in dep.name or dep.import_path.startswith("git::")):
                modules.append({
                    "name": dep.name,
                    "source": dep.import_path,
                    "version": dep.version,
                    "file": dep.file,
                })
        
        return modules
    
    def _extract_providers(self, analysis: AnalysisResult) -> list[dict]:
        """Extract provider configurations."""
        providers = []
        for model in analysis.models:
            if "provider" in model.decorators:
                providers.append({
                    "name": model.name,
                    "file": model.file,
                })
        
        return providers
    
    def _get_service_group(self, resource_type: str) -> str:
        """Get the AWS service group for a resource type."""
        for group, prefixes in AWS_SERVICE_GROUPS.items():
            for prefix in prefixes:
                if resource_type.startswith(prefix):
                    return group
        return "other"
    
    def _has_network_resources(self, resources: list[dict]) -> bool:
        """Check if there are network resources worth diagramming."""
        network_types = ["aws_vpc", "aws_subnet", "aws_security_group", "aws_lb", "aws_nat"]
        return any(
            any(r["type"].startswith(nt) for nt in network_types)
            for r in resources
        )
    
    async def _generate_readme(
        self,
        repo_path: Path,
        service_name: str,
        github_url: Optional[str],
        resources: list[dict],
        variables: list[dict],
        outputs: list[dict],
        modules: list[dict],
        providers: list[dict],
    ) -> GeneratedDocument:
        """Generate README with overview and quick start."""
        content = f"""---
title: {service_name}
description: Terraform module for {service_name}
generated: true
type: terraform
---

# {service_name}

## Overview

This Terraform module provisions infrastructure for {service_name}.

"""
        
        # Add summary table
        content += "## Summary\n\n"
        content += "| Component | Count |\n"
        content += "|-----------|-------|\n"
        content += f"| Resources | {len(resources)} |\n"
        content += f"| Variables | {len(variables)} |\n"
        content += f"| Outputs | {len(outputs)} |\n"
        content += f"| Module Dependencies | {len(modules)} |\n"
        content += f"| Providers | {len(providers)} |\n\n"
        
        # Group resources by service
        if resources:
            content += "## Resources by Service\n\n"
            grouped = {}
            for r in resources:
                group = self._get_service_group(r["type"])
                if group not in grouped:
                    grouped[group] = []
                grouped[group].append(r)
            
            content += "| Service | Count | Resource Types |\n"
            content += "|---------|-------|---------------|\n"
            for group, group_resources in sorted(grouped.items()):
                types = set(r["type"] for r in group_resources)
                content += f"| {group.title()} | {len(group_resources)} | {', '.join(sorted(types)[:5])} |\n"
            content += "\n"
        
        # Quick start
        content += "## Quick Start\n\n"
        content += "```hcl\n"
        content += f'module "{service_name.replace("-", "_")}" {{\n'
        content += f'  source = "{github_url or "."}"\n\n'
        
        # Show required variables
        required_vars = [v for v in variables if v.get("required")]
        for var in required_vars[:5]:
            content += f'  {var["name"]} = "<value>"\n'
        
        content += "}\n"
        content += "```\n\n"
        
        # Documentation links
        content += "## Documentation\n\n"
        content += "| Document | Description |\n"
        content += "|----------|-------------|\n"
        content += "| [Architecture](./architecture.md) | Infrastructure diagram |\n"
        content += "| [Resources](./resources.md) | All resources created |\n"
        content += "| [Variables](./variables.md) | Input variables |\n"
        content += "| [Outputs](./outputs.md) | Available outputs |\n"
        content += "| [Operations](./operations.md) | How to manage this module |\n\n"
        
        if github_url:
            content += f"## Source\n\n- [Repository]({github_url})\n"
        
        return GeneratedDocument(
            path="README.md",
            title=f"{service_name} Overview",
            content=content,
        )
    
    async def _generate_architecture(
        self,
        service_name: str,
        github_url: Optional[str],
        resources: list[dict],
        data_sources: list[dict],
        modules: list[dict],
    ) -> GeneratedDocument:
        """Generate architecture diagram."""
        content = f"""---
title: {service_name} Architecture
description: Infrastructure architecture diagram
generated: true
---

# {service_name} Architecture

## Infrastructure Diagram

"""
        
        # Generate Mermaid diagram grouped by service
        if resources:
            content += "```mermaid\nflowchart TB\n"
            
            # Group resources
            grouped = {}
            for r in resources:
                group = self._get_service_group(r["type"])
                if group not in grouped:
                    grouped[group] = []
                grouped[group].append(r)
            
            # Create subgraphs for each service group
            for group, group_resources in sorted(grouped.items()):
                if group_resources:
                    safe_group = group.replace("-", "_")
                    content += f"    subgraph {safe_group}[{group.title()}]\n"
                    for r in group_resources:
                        safe_name = r["full_name"].replace(".", "_").replace("-", "_")
                        label = f"{r['type']}\\n{r['name']}"
                        content += f'        {safe_name}["{label}"]\n'
                    content += "    end\n"
            
            # Add connections (infer from common patterns)
            # VPC -> Subnets
            vpcs = [r for r in resources if r["type"] == "aws_vpc"]
            subnets = [r for r in resources if r["type"] == "aws_subnet"]
            for vpc in vpcs:
                for subnet in subnets:
                    vpc_name = vpc["full_name"].replace(".", "_").replace("-", "_")
                    subnet_name = subnet["full_name"].replace(".", "_").replace("-", "_")
                    content += f"    {vpc_name} --> {subnet_name}\n"
            
            # Subnets -> Instances/ECS/Lambda
            compute = [r for r in resources if any(r["type"].startswith(p) for p in ["aws_instance", "aws_ecs", "aws_lambda"])]
            for subnet in subnets[:1]:  # Limit to first subnet for simplicity
                for c in compute:
                    subnet_name = subnet["full_name"].replace(".", "_").replace("-", "_")
                    compute_name = c["full_name"].replace(".", "_").replace("-", "_")
                    content += f"    {subnet_name} --> {compute_name}\n"
            
            content += "```\n\n"
        else:
            content += "*No resources found to diagram.*\n\n"
        
        # List data sources
        if data_sources:
            content += "## External Data Sources\n\n"
            content += "| Type | Description |\n"
            content += "|------|-------------|\n"
            for ds in data_sources:
                content += f"| `{ds['type']}` | {ds.get('description', 'N/A')} |\n"
            content += "\n"
        
        # List module dependencies
        if modules:
            content += "## Module Dependencies\n\n"
            content += "| Module | Source | Version |\n"
            content += "|--------|--------|--------|\n"
            for mod in modules:
                content += f"| {mod['name']} | {mod['source']} | {mod.get('version', 'N/A')} |\n"
            content += "\n"
        
        return GeneratedDocument(
            path="architecture.md",
            title=f"{service_name} Architecture",
            content=content,
        )
    
    async def _generate_resources(
        self,
        service_name: str,
        github_url: Optional[str],
        resources: list[dict],
    ) -> GeneratedDocument:
        """Generate resources documentation."""
        content = f"""---
title: {service_name} Resources
description: All resources created by this module
generated: true
---

# {service_name} Resources

This document lists all resources created by this Terraform module.

## Resource Summary

| Type | Name | File |
|------|------|------|
"""
        
        for r in resources:
            file_link = f"[{r['file']}]({github_url}/blob/main/{r['file']})" if github_url else r["file"]
            content += f"| `{r['type']}` | {r['name']} | {file_link} |\n"
        
        content += "\n## Resources by Type\n\n"
        
        # Group by type
        by_type = {}
        for r in resources:
            if r["type"] not in by_type:
                by_type[r["type"]] = []
            by_type[r["type"]].append(r)
        
        for resource_type, type_resources in sorted(by_type.items()):
            content += f"### {resource_type}\n\n"
            for r in type_resources:
                content += f"**{r['name']}**"
                if r.get("description"):
                    content += f": {r['description']}"
                content += "\n\n"
                
                # Show key fields
                if r.get("fields"):
                    content += "| Attribute | Type | Description |\n"
                    content += "|-----------|------|-------------|\n"
                    for field in r["fields"][:10]:
                        content += f"| `{field.name}` | {field.type} | {field.description or 'N/A'} |\n"
                    content += "\n"
            
            content += "---\n\n"
        
        return GeneratedDocument(
            path="resources.md",
            title=f"{service_name} Resources",
            content=content,
        )
    
    async def _generate_variables(
        self,
        service_name: str,
        github_url: Optional[str],
        variables: list[dict],
    ) -> GeneratedDocument:
        """Generate variables documentation."""
        content = f"""---
title: {service_name} Variables
description: Input variables for this module
generated: true
---

# {service_name} Variables

## Required Variables

"""
        
        required = [v for v in variables if v.get("required")]
        optional = [v for v in variables if not v.get("required")]
        
        if required:
            content += "| Name | Description |\n"
            content += "|------|-------------|\n"
            for v in required:
                content += f"| `{v['name']}` | {v.get('description', 'No description')} |\n"
            content += "\n"
        else:
            content += "*No required variables.*\n\n"
        
        content += "## Optional Variables\n\n"
        
        if optional:
            content += "| Name | Description | Default |\n"
            content += "|------|-------------|--------|\n"
            for v in optional:
                default = v.get("default", "N/A")
                if isinstance(default, str) and len(default) > 30:
                    default = default[:27] + "..."
                content += f"| `{v['name']}` | {v.get('description', 'No description')} | `{default}` |\n"
            content += "\n"
        else:
            content += "*No optional variables.*\n\n"
        
        # Detailed variable documentation
        content += "## Variable Details\n\n"
        for v in variables:
            content += f"### {v['name']}\n\n"
            content += f"{v.get('description', 'No description provided.')}\n\n"
            content += f"- **Required:** {'Yes' if v.get('required') else 'No'}\n"
            if v.get("default"):
                content += f"- **Default:** `{v['default']}`\n"
            if github_url:
                content += f"- **Defined in:** [{v['file']}]({github_url}/blob/main/{v['file']}#L{v.get('line', 1)})\n"
            content += "\n"
        
        return GeneratedDocument(
            path="variables.md",
            title=f"{service_name} Variables",
            content=content,
        )
    
    async def _generate_outputs(
        self,
        service_name: str,
        github_url: Optional[str],
        outputs: list[dict],
    ) -> GeneratedDocument:
        """Generate outputs documentation."""
        content = f"""---
title: {service_name} Outputs
description: Outputs available for consumers
generated: true
---

# {service_name} Outputs

These outputs are available for other modules or configurations to consume.

## Available Outputs

| Name | Description |
|------|-------------|
"""
        
        for o in outputs:
            content += f"| `{o['name']}` | {o.get('description', 'No description')} |\n"
        
        content += "\n## Usage Example\n\n"
        content += "```hcl\n"
        content += f'module "{service_name.replace("-", "_")}" {{\n'
        content += f'  source = "<module-source>"\n'
        content += "  # ... variables ...\n"
        content += "}\n\n"
        content += "# Access outputs:\n"
        for o in outputs[:3]:
            content += f'# module.{service_name.replace("-", "_")}.{o["name"]}\n'
        content += "```\n\n"
        
        return GeneratedDocument(
            path="outputs.md",
            title=f"{service_name} Outputs",
            content=content,
        )
    
    async def _generate_data_flows(
        self,
        service_name: str,
        github_url: Optional[str],
        resources: list[dict],
    ) -> GeneratedDocument:
        """Generate data flow diagrams for network resources."""
        content = f"""---
title: {service_name} Data Flows
description: Network and data flow diagrams
generated: true
---

# {service_name} Data Flows

## Network Architecture

"""
        
        # Build network diagram
        content += "```mermaid\nflowchart LR\n"
        
        # Internet -> Load Balancer -> Compute -> Database pattern
        has_lb = any(r["type"].startswith("aws_lb") or r["type"].startswith("aws_alb") for r in resources)
        has_compute = any(r["type"].startswith("aws_instance") or r["type"].startswith("aws_ecs") for r in resources)
        has_db = any(r["type"].startswith("aws_rds") or r["type"].startswith("aws_dynamodb") for r in resources)
        has_s3 = any(r["type"].startswith("aws_s3") for r in resources)
        
        content += "    Internet((Internet))\n"
        
        if has_lb:
            content += "    LB[Load Balancer]\n"
            content += "    Internet --> LB\n"
        
        if has_compute:
            content += "    Compute[Compute Layer]\n"
            if has_lb:
                content += "    LB --> Compute\n"
            else:
                content += "    Internet --> Compute\n"
        
        if has_db:
            content += "    DB[(Database)]\n"
            if has_compute:
                content += "    Compute --> DB\n"
        
        if has_s3:
            content += "    S3[(S3 Storage)]\n"
            if has_compute:
                content += "    Compute --> S3\n"
        
        content += "```\n\n"
        
        # Security groups section
        sgs = [r for r in resources if r["type"] == "aws_security_group"]
        if sgs:
            content += "## Security Groups\n\n"
            content += "| Name | Description |\n"
            content += "|------|-------------|\n"
            for sg in sgs:
                content += f"| {sg['name']} | {sg.get('description', 'N/A')} |\n"
            content += "\n"
        
        return GeneratedDocument(
            path="data-flows.md",
            title=f"{service_name} Data Flows",
            content=content,
        )
    
    async def _generate_operations(
        self,
        service_name: str,
        github_url: Optional[str],
        providers: list[dict],
    ) -> GeneratedDocument:
        """Generate operations guide."""
        content = f"""---
title: {service_name} Operations
description: How to manage this infrastructure
generated: true
---

# {service_name} Operations

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- Appropriate IAM permissions

## Providers

"""
        
        if providers:
            content += "| Provider | Configuration |\n"
            content += "|----------|---------------|\n"
            for p in providers:
                content += f"| {p['name']} | See {p['file']} |\n"
            content += "\n"
        
        content += """## Common Operations

### Initialize

```bash
terraform init
```

### Plan Changes

```bash
terraform plan -out=tfplan
```

### Apply Changes

```bash
terraform apply tfplan
```

### Destroy Infrastructure

```bash
terraform destroy
```

## State Management

### View Current State

```bash
terraform state list
terraform state show <resource>
```

### Import Existing Resource

```bash
terraform import <resource_type>.<name> <id>
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| State lock | Use `terraform force-unlock <lock-id>` |
| Provider auth | Check AWS credentials |
| Resource conflicts | Review state with `terraform state list` |

### Useful Commands

```bash
# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Show resource dependencies
terraform graph | dot -Tpng > graph.png
```
"""
        
        return GeneratedDocument(
            path="operations.md",
            title=f"{service_name} Operations",
            content=content,
        )
