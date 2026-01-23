"""
Terraform/HCL language analyzer.

Extracts resources, variables, outputs, and modules from Terraform configurations.
Enhanced with resource dependency extraction and infrastructure diagram support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..base import BaseLanguageAnalyzer
from ..factory import register_analyzer
from ..models import (
    ExtractedConfig,
    ExtractedDependency,
    ExtractedEndpoint,
    ExtractedField,
    ExtractedModel,
    ExtractedSideEffect,
    ModelType,
    SideEffectCategory,
)


@dataclass
class TerraformResource:
    """Enhanced representation of a Terraform resource for diagramming."""
    resource_type: str
    resource_name: str
    full_name: str
    provider: str
    category: str
    file: str
    line: int
    attributes: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    
    @property
    def diagram_id(self) -> str:
        """ID safe for use in Mermaid diagrams."""
        return self.full_name.replace(".", "_").replace("-", "_")
    
    @property
    def diagram_label(self) -> str:
        """Label for diagram node."""
        return f"{self.resource_type}\\n{self.resource_name}"


@dataclass
class InfrastructureDiagram:
    """Infrastructure diagram data for Terraform modules."""
    resources: list[TerraformResource]
    connections: list[tuple[str, str, str]]  # (from, to, label)
    groups: dict[str, list[TerraformResource]]
    
    def to_mermaid(self, direction: str = "TB") -> str:
        """Generate Mermaid diagram."""
        lines = [f"```mermaid", f"flowchart {direction}"]
        
        # Generate subgraphs for each category
        for group_name, group_resources in sorted(self.groups.items()):
            if group_resources:
                safe_group = group_name.replace(" ", "_").replace("-", "_")
                display_name = group_name.replace("_", " ").title()
                lines.append(f"    subgraph {safe_group}[{display_name}]")
                for resource in group_resources:
                    lines.append(f'        {resource.diagram_id}["{resource.diagram_label}"]')
                lines.append("    end")
        
        # Add connections
        for from_id, to_id, label in self.connections:
            safe_from = from_id.replace(".", "_").replace("-", "_")
            safe_to = to_id.replace(".", "_").replace("-", "_")
            if label:
                lines.append(f"    {safe_from} -->|{label}| {safe_to}")
            else:
                lines.append(f"    {safe_from} --> {safe_to}")
        
        lines.append("```")
        return "\n".join(lines)


@register_analyzer("terraform")
@register_analyzer("hcl")
class TerraformAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Terraform/HCL configurations.
    
    Extracts:
    - Resources (AWS, GCP, Azure, etc.)
    - Data sources
    - Variables and locals
    - Outputs
    - Modules
    - Provider configurations
    """
    
    language = "hcl"
    extensions = [".tf", ".tfvars"]
    
    # Block patterns
    RESOURCE_PATTERN = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{'
    DATA_PATTERN = r'data\s+"([^"]+)"\s+"([^"]+)"\s*\{'
    VARIABLE_PATTERN = r'variable\s+"([^"]+)"\s*\{'
    OUTPUT_PATTERN = r'output\s+"([^"]+)"\s*\{'
    MODULE_PATTERN = r'module\s+"([^"]+)"\s*\{'
    LOCALS_PATTERN = r'locals\s*\{'
    PROVIDER_PATTERN = r'provider\s+"([^"]+)"\s*\{'
    
    # AWS resource categories for side effects
    AWS_RESOURCE_CATEGORIES = {
        "compute": ["aws_instance", "aws_launch_template", "aws_autoscaling_group", 
                   "aws_ecs_cluster", "aws_ecs_service", "aws_ecs_task_definition",
                   "aws_lambda_function", "aws_lambda_layer_version"],
        "storage": ["aws_s3_bucket", "aws_s3_bucket_object", "aws_s3_bucket_policy",
                   "aws_ebs_volume", "aws_efs_file_system"],
        "database": ["aws_db_instance", "aws_rds_cluster", "aws_dynamodb_table",
                    "aws_elasticache_cluster", "aws_elasticache_replication_group"],
        "networking": ["aws_vpc", "aws_subnet", "aws_security_group", "aws_route_table",
                      "aws_nat_gateway", "aws_internet_gateway", "aws_lb", "aws_lb_target_group",
                      "aws_route53_record", "aws_route53_zone", "aws_cloudfront_distribution"],
        "messaging": ["aws_sqs_queue", "aws_sns_topic", "aws_sns_topic_subscription",
                     "aws_kinesis_stream", "aws_kinesis_firehose_delivery_stream"],
        "iam": ["aws_iam_role", "aws_iam_policy", "aws_iam_role_policy_attachment",
               "aws_iam_user", "aws_iam_group"],
        "monitoring": ["aws_cloudwatch_log_group", "aws_cloudwatch_metric_alarm",
                      "aws_cloudwatch_dashboard"],
        "secrets": ["aws_secretsmanager_secret", "aws_ssm_parameter", "aws_kms_key"],
    }
    
    # GCP resource categories
    GCP_RESOURCE_CATEGORIES = {
        "compute": ["google_compute_instance", "google_cloud_run_service",
                   "google_cloudfunctions_function"],
        "storage": ["google_storage_bucket", "google_storage_bucket_object"],
        "database": ["google_sql_database_instance", "google_bigtable_instance",
                    "google_firestore_database"],
        "networking": ["google_compute_network", "google_compute_subnetwork",
                      "google_compute_firewall"],
    }
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract Terraform resources, data sources, and modules as models."""
        models = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract resources
            models.extend(self._extract_resources(content, rel_path))
            
            # Extract data sources
            models.extend(self._extract_data_sources(content, rel_path))
            
            # Extract modules
            models.extend(self._extract_modules(content, rel_path))
        
        return models
    
    def _extract_resources(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract resource blocks."""
        models = []
        
        for match in re.finditer(self.RESOURCE_PATTERN, content, re.MULTILINE):
            resource_type = match.group(1)
            resource_name = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract resource body
            block_start = content.find('{', match.start()) + 1
            block_body = self._extract_block_body(content, block_start)
            
            # Extract attributes
            fields = self._extract_attributes(block_body)
            
            # Determine provider from resource type
            provider = resource_type.split('_')[0] if '_' in resource_type else "unknown"
            
            models.append(ExtractedModel(
                name=f"{resource_type}.{resource_name}",
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                fields=fields,
                decorators=["resource", provider, resource_type],
                description=f"Terraform {resource_type} resource",
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_data_sources(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract data source blocks."""
        models = []
        
        for match in re.finditer(self.DATA_PATTERN, content, re.MULTILINE):
            data_type = match.group(1)
            data_name = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract body
            block_start = content.find('{', match.start()) + 1
            block_body = self._extract_block_body(content, block_start)
            
            # Extract attributes
            fields = self._extract_attributes(block_body)
            
            provider = data_type.split('_')[0] if '_' in data_type else "unknown"
            
            models.append(ExtractedModel(
                name=f"data.{data_type}.{data_name}",
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                fields=fields,
                decorators=["data_source", provider, data_type],
                description=f"Terraform data source for {data_type}",
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_modules(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract module blocks."""
        models = []
        
        for match in re.finditer(self.MODULE_PATTERN, content, re.MULTILINE):
            module_name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract body
            block_start = content.find('{', match.start()) + 1
            block_body = self._extract_block_body(content, block_start)
            
            # Extract source
            source_match = re.search(r'source\s*=\s*"([^"]+)"', block_body)
            source = source_match.group(1) if source_match else "unknown"
            
            # Extract attributes
            fields = self._extract_attributes(block_body)
            
            models.append(ExtractedModel(
                name=f"module.{module_name}",
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                fields=fields,
                decorators=["module"],
                description=f"Terraform module from {source}",
                parent=source,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_block_body(self, content: str, start: int) -> str:
        """Extract the body of a block (between { and })."""
        brace_count = 1
        end = start
        
        for i, char in enumerate(content[start:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = start + i
                    break
        
        return content[start:end]
    
    def _extract_attributes(self, body: str) -> list[ExtractedField]:
        """Extract attributes from a block body."""
        fields = []
        
        # Simple attribute pattern: name = value
        attr_pattern = r'^\s*(\w+)\s*=\s*(.+?)$'
        
        for match in re.finditer(attr_pattern, body, re.MULTILINE):
            name = match.group(1)
            value = match.group(2).strip()
            
            # Determine type from value
            if value.startswith('"'):
                attr_type = "string"
            elif value.startswith('['):
                attr_type = "list"
            elif value.startswith('{'):
                attr_type = "map"
            elif value in ('true', 'false'):
                attr_type = "bool"
            elif value.isdigit():
                attr_type = "number"
            else:
                attr_type = "expression"
            
            fields.append(ExtractedField(
                name=name,
                type=attr_type,
                default=value[:50] if len(value) < 50 else value[:47] + "...",
            ))
        
        return fields[:20]  # Limit fields
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract API Gateway and Load Balancer endpoints."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # API Gateway resources
            for match in re.finditer(r'resource\s+"aws_api_gateway_resource"\s+"([^"]+)"', content):
                name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                # Try to find path
                block_start = content.find('{', match.start()) + 1
                block_body = self._extract_block_body(content, block_start)
                path_match = re.search(r'path_part\s*=\s*"([^"]+)"', block_body)
                path = path_match.group(1) if path_match else name
                
                endpoints.append(ExtractedEndpoint(
                    method="ANY",
                    path=f"/{path}",
                    file=rel_path,
                    line=line,
                    handler=name,
                    decorators=["api_gateway"],
                    github_url=self.github_link(rel_path, line),
                ))
            
            # API Gateway methods
            for match in re.finditer(r'resource\s+"aws_api_gateway_method"\s+"([^"]+)"', content):
                name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                block_start = content.find('{', match.start()) + 1
                block_body = self._extract_block_body(content, block_start)
                
                method_match = re.search(r'http_method\s*=\s*"([^"]+)"', block_body)
                method = method_match.group(1) if method_match else "ANY"
                
                endpoints.append(ExtractedEndpoint(
                    method=method,
                    path=f"/{name}",
                    file=rel_path,
                    line=line,
                    handler=name,
                    decorators=["api_gateway_method"],
                    github_url=self.github_link(rel_path, line),
                ))
            
            # ALB/NLB listeners
            for match in re.finditer(r'resource\s+"aws_lb_listener"\s+"([^"]+)"', content):
                name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                block_start = content.find('{', match.start()) + 1
                block_body = self._extract_block_body(content, block_start)
                
                port_match = re.search(r'port\s*=\s*(\d+)', block_body)
                port = port_match.group(1) if port_match else "80"
                
                endpoints.append(ExtractedEndpoint(
                    method="LISTEN",
                    path=f":{port}",
                    file=rel_path,
                    line=line,
                    handler=name,
                    decorators=["lb_listener"],
                    github_url=self.github_link(rel_path, line),
                ))
        
        return endpoints
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract cloud resource provisioning as side effects."""
        side_effects = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Find all resources
            for match in re.finditer(self.RESOURCE_PATTERN, content):
                resource_type = match.group(1)
                
                # Categorize AWS resources
                for category, types in self.AWS_RESOURCE_CATEGORIES.items():
                    if resource_type in types:
                        key = (category, resource_type)
                        if key not in seen:
                            seen.add(key)
                            side_effects.append(ExtractedSideEffect(
                                category=SideEffectCategory.CLOUD_SERVICE,
                                operation=f"Provision {resource_type}",
                                target=f"AWS {category}",
                                file=rel_path,
                                github_url=self.github_link(rel_path),
                            ))
                        break
                
                # Categorize GCP resources
                for category, types in self.GCP_RESOURCE_CATEGORIES.items():
                    if resource_type in types:
                        key = (category, resource_type)
                        if key not in seen:
                            seen.add(key)
                            side_effects.append(ExtractedSideEffect(
                                category=SideEffectCategory.CLOUD_SERVICE,
                                operation=f"Provision {resource_type}",
                                target=f"GCP {category}",
                                file=rel_path,
                                github_url=self.github_link(rel_path),
                            ))
                        break
                
                # Generic cloud resources
                if resource_type.startswith(('aws_', 'google_', 'azurerm_', 'kubernetes_')):
                    provider = resource_type.split('_')[0]
                    key = ("cloud", resource_type)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.CLOUD_SERVICE,
                            operation=f"Provision {resource_type}",
                            target=provider.upper(),
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract Terraform variables and outputs."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract variables
            for match in re.finditer(self.VARIABLE_PATTERN, content):
                var_name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                if var_name not in seen:
                    seen.add(var_name)
                    
                    # Extract variable details
                    block_start = content.find('{', match.start()) + 1
                    block_body = self._extract_block_body(content, block_start)
                    
                    # Get type
                    type_match = re.search(r'type\s*=\s*(\w+)', block_body)
                    var_type = type_match.group(1) if type_match else "any"
                    
                    # Get default
                    default_match = re.search(r'default\s*=\s*"?([^"\n]+)"?', block_body)
                    default = default_match.group(1) if default_match else None
                    
                    # Get description
                    desc_match = re.search(r'description\s*=\s*"([^"]+)"', block_body)
                    description = desc_match.group(1) if desc_match else None
                    
                    configs.append(ExtractedConfig(
                        key=f"var.{var_name}",
                        source="terraform_variable",
                        file=rel_path,
                        line=line,
                        default=default,
                        description=description,
                        required=default is None,
                        github_url=self.github_link(rel_path, line),
                    ))
            
            # Extract outputs
            for match in re.finditer(self.OUTPUT_PATTERN, content):
                output_name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                key = f"output.{output_name}"
                if key not in seen:
                    seen.add(key)
                    
                    block_start = content.find('{', match.start()) + 1
                    block_body = self._extract_block_body(content, block_start)
                    
                    desc_match = re.search(r'description\s*=\s*"([^"]+)"', block_body)
                    description = desc_match.group(1) if desc_match else None
                    
                    configs.append(ExtractedConfig(
                        key=key,
                        source="terraform_output",
                        file=rel_path,
                        line=line,
                        description=description,
                        github_url=self.github_link(rel_path, line),
                    ))
            
            # Extract locals
            for match in re.finditer(self.LOCALS_PATTERN, content):
                line = content[:match.start()].count('\n') + 1
                
                block_start = content.find('{', match.start()) + 1
                block_body = self._extract_block_body(content, block_start)
                
                # Extract local values
                for local_match in re.finditer(r'(\w+)\s*=', block_body):
                    local_name = local_match.group(1)
                    key = f"local.{local_name}"
                    if key not in seen:
                        seen.add(key)
                        configs.append(ExtractedConfig(
                            key=key,
                            source="terraform_local",
                            file=rel_path,
                            line=line,
                            github_url=self.github_link(rel_path, line),
                        ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract Terraform providers and modules as dependencies."""
        dependencies = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            # Extract required providers
            req_providers = re.search(r'required_providers\s*\{([^}]+)\}', content, re.DOTALL)
            if req_providers:
                body = req_providers.group(1)
                for match in re.finditer(r'(\w+)\s*=\s*\{[^}]*source\s*=\s*"([^"]+)"[^}]*version\s*=\s*"([^"]+)"', body, re.DOTALL):
                    dependencies.append(ExtractedDependency(
                        name=match.group(1),
                        version=match.group(3),
                        import_path=match.group(2),
                        file=self.relative_path(file_path),
                    ))
            
            # Extract provider blocks
            for match in re.finditer(self.PROVIDER_PATTERN, content):
                provider_name = match.group(1)
                dependencies.append(ExtractedDependency(
                    name=provider_name,
                    file=self.relative_path(file_path),
                ))
            
            # Extract module sources
            for match in re.finditer(self.MODULE_PATTERN, content):
                block_start = content.find('{', match.start()) + 1
                block_body = self._extract_block_body(content, block_start)
                
                source_match = re.search(r'source\s*=\s*"([^"]+)"', block_body)
                version_match = re.search(r'version\s*=\s*"([^"]+)"', block_body)
                
                if source_match:
                    dependencies.append(ExtractedDependency(
                        name=match.group(1),
                        version=version_match.group(1) if version_match else None,
                        import_path=source_match.group(1),
                        file=self.relative_path(file_path),
                    ))
        
        return dependencies
    
    # ============================================================
    # Enhanced methods for infrastructure diagrams
    # ============================================================
    
    def extract_infrastructure_diagram(self) -> InfrastructureDiagram:
        """
        Extract complete infrastructure diagram data.
        
        Returns an InfrastructureDiagram with resources, connections, and groupings.
        """
        resources = []
        all_resources = {}  # full_name -> TerraformResource
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract all resources with their dependencies
            for match in re.finditer(self.RESOURCE_PATTERN, content, re.MULTILINE):
                resource_type = match.group(1)
                resource_name = match.group(2)
                full_name = f"{resource_type}.{resource_name}"
                line = content[:match.start()].count('\n') + 1
                
                # Extract block body for dependency analysis
                block_start = content.find('{', match.start()) + 1
                block_body = self._extract_block_body(content, block_start)
                
                # Determine provider and category
                provider = resource_type.split('_')[0] if '_' in resource_type else "unknown"
                category = self._get_resource_category(resource_type)
                
                # Extract dependencies from references
                deps = self._extract_resource_dependencies(block_body)
                
                # Extract key attributes
                attrs = self._extract_key_attributes(block_body, resource_type)
                
                resource = TerraformResource(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    full_name=full_name,
                    provider=provider,
                    category=category,
                    file=rel_path,
                    line=line,
                    attributes=attrs,
                    dependencies=deps,
                )
                
                resources.append(resource)
                all_resources[full_name] = resource
        
        # Build reverse dependency graph (dependents)
        for resource in resources:
            for dep_name in resource.dependencies:
                if dep_name in all_resources:
                    all_resources[dep_name].dependents.append(resource.full_name)
        
        # Build connections list
        connections = []
        for resource in resources:
            for dep_name in resource.dependencies:
                # Determine connection label based on attribute that created it
                label = ""
                connections.append((dep_name, resource.full_name, label))
        
        # Group resources by category
        groups = {}
        for resource in resources:
            if resource.category not in groups:
                groups[resource.category] = []
            groups[resource.category].append(resource)
        
        return InfrastructureDiagram(
            resources=resources,
            connections=connections,
            groups=groups,
        )
    
    def _get_resource_category(self, resource_type: str) -> str:
        """Get the category for a resource type."""
        # Check AWS categories
        for category, types in self.AWS_RESOURCE_CATEGORIES.items():
            if resource_type in types:
                return f"aws_{category}"
        
        # Check GCP categories
        for category, types in self.GCP_RESOURCE_CATEGORIES.items():
            if resource_type in types:
                return f"gcp_{category}"
        
        # Infer from resource type prefix
        if resource_type.startswith("aws_"):
            parts = resource_type.split('_')
            if len(parts) >= 2:
                return f"aws_{parts[1]}"
        elif resource_type.startswith("google_"):
            parts = resource_type.split('_')
            if len(parts) >= 2:
                return f"gcp_{parts[1]}"
        elif resource_type.startswith("azurerm_"):
            parts = resource_type.split('_')
            if len(parts) >= 2:
                return f"azure_{parts[1]}"
        elif resource_type.startswith("kubernetes_"):
            return "kubernetes"
        
        return "other"
    
    def _extract_resource_dependencies(self, block_body: str) -> list[str]:
        """Extract resource dependencies from reference expressions."""
        dependencies = []
        
        # Pattern for resource references: resource_type.resource_name.attribute
        # or ${resource_type.resource_name.attribute}
        ref_patterns = [
            r'(?<!["\'])\b([a-z_]+\.[a-z_][a-z0-9_]*)\.[a-z_]+',  # Direct reference
            r'\$\{([a-z_]+\.[a-z_][a-z0-9_]*)\.[a-z_]+\}',  # Interpolation
            r'=\s*([a-z_]+\.[a-z_][a-z0-9_]*)\s*$',  # Assignment to resource
        ]
        
        for pattern in ref_patterns:
            for match in re.finditer(pattern, block_body, re.MULTILINE | re.IGNORECASE):
                ref = match.group(1)
                # Filter out common non-resource references
                if not ref.startswith(('var.', 'local.', 'data.', 'module.', 'each.', 'count.', 'self.')):
                    if ref not in dependencies:
                        dependencies.append(ref)
        
        # Also check explicit depends_on
        depends_on_match = re.search(r'depends_on\s*=\s*\[([^\]]+)\]', block_body)
        if depends_on_match:
            deps_content = depends_on_match.group(1)
            for dep in re.finditer(r'([a-z_]+\.[a-z_][a-z0-9_]*)', deps_content):
                ref = dep.group(1)
                if ref not in dependencies:
                    dependencies.append(ref)
        
        return dependencies
    
    def _extract_key_attributes(self, block_body: str, resource_type: str) -> dict:
        """Extract key attributes relevant for diagramming."""
        attrs = {}
        
        # Common attributes to extract
        key_attrs = {
            'name': r'name\s*=\s*"([^"]+)"',
            'tags_name': r'Name\s*=\s*"([^"]+)"',
            'cidr_block': r'cidr_block\s*=\s*"([^"]+)"',
            'vpc_id': r'vpc_id\s*=\s*([^\s\n]+)',
            'subnet_id': r'subnet_id\s*=\s*([^\s\n]+)',
            'security_groups': r'security_groups\s*=\s*\[([^\]]+)\]',
            'ami': r'ami\s*=\s*"([^"]+)"',
            'instance_type': r'instance_type\s*=\s*"([^"]+)"',
            'engine': r'engine\s*=\s*"([^"]+)"',
            'port': r'port\s*=\s*(\d+)',
        }
        
        for attr_name, pattern in key_attrs.items():
            match = re.search(pattern, block_body)
            if match:
                attrs[attr_name] = match.group(1)
        
        return attrs
    
    def get_resource_summary(self) -> dict:
        """
        Get a summary of resources by type and category.
        
        Returns a dict with counts and categorizations for documentation.
        """
        summary = {
            "total": 0,
            "by_provider": {},
            "by_category": {},
            "by_type": {},
        }
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            for match in re.finditer(self.RESOURCE_PATTERN, content):
                resource_type = match.group(1)
                
                summary["total"] += 1
                
                # Count by type
                if resource_type not in summary["by_type"]:
                    summary["by_type"][resource_type] = 0
                summary["by_type"][resource_type] += 1
                
                # Count by provider
                provider = resource_type.split('_')[0] if '_' in resource_type else "other"
                if provider not in summary["by_provider"]:
                    summary["by_provider"][provider] = 0
                summary["by_provider"][provider] += 1
                
                # Count by category
                category = self._get_resource_category(resource_type)
                if category not in summary["by_category"]:
                    summary["by_category"][category] = 0
                summary["by_category"][category] += 1
        
        return summary
    
    def generate_mermaid_diagram(self, max_resources: int = 50) -> str:
        """
        Generate a Mermaid diagram for the Terraform configuration.
        
        Args:
            max_resources: Maximum resources to include (to prevent huge diagrams)
            
        Returns:
            Mermaid diagram as string
        """
        diagram = self.extract_infrastructure_diagram()
        
        # If too many resources, prioritize by category importance
        if len(diagram.resources) > max_resources:
            priority_categories = [
                "aws_networking", "aws_compute", "aws_database", "aws_storage",
                "gcp_networking", "gcp_compute", "gcp_database",
                "azure_networking", "azure_compute",
                "kubernetes",
            ]
            
            prioritized = []
            for category in priority_categories:
                prioritized.extend(diagram.groups.get(category, []))
                if len(prioritized) >= max_resources:
                    break
            
            # Rebuild diagram with limited resources
            limited_names = {r.full_name for r in prioritized[:max_resources]}
            diagram.resources = [r for r in diagram.resources if r.full_name in limited_names]
            diagram.connections = [
                (f, t, l) for f, t, l in diagram.connections
                if f in limited_names and t in limited_names
            ]
            diagram.groups = {
                k: [r for r in v if r.full_name in limited_names]
                for k, v in diagram.groups.items()
            }
            diagram.groups = {k: v for k, v in diagram.groups.items() if v}
        
        return diagram.to_mermaid()