"""
Go language analyzer.

Extracts data models, API endpoints, side effects, and configuration
from Go source code using tree-sitter AST parsing with regex fallback.
"""

import re
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


@register_analyzer("go")
class GoAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Go source code.
    
    Extracts:
    - Structs (data models, config types)
    - Interfaces
    - HTTP routes (Chi, Gorilla, Echo, Gin, net/http)
    - GraphQL types
    - Database operations (SQL, DynamoDB)
    - HTTP client calls
    - AWS SDK operations (S3, SQS, SNS, Lambda)
    - Environment variable usage
    """
    
    language = "go"
    extensions = [".go"]
    
    # Patterns for HTTP route detection
    HTTP_ROUTE_PATTERNS = [
        # Chi router
        r'(r|router|mux)\.(Get|Post|Put|Delete|Patch|Options|Head)\s*\(\s*["\']([^"\']+)["\']',
        # Gorilla mux
        r'(r|router|mux)\.(HandleFunc|Handle)\s*\(\s*["\']([^"\']+)["\']',
        # Standard library
        r'http\.(HandleFunc|Handle)\s*\(\s*["\']([^"\']+)["\']',
        # Echo
        r'(e|echo)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["\']([^"\']+)["\']',
        # Gin
        r'(r|router|g|gin)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["\']([^"\']+)["\']',
    ]
    
    # Patterns for database operations
    DB_PATTERNS = {
        "mysql": [
            (r"sql\.Open\s*\(\s*[\"']mysql[\"']", "Connect"),
            (r"\.Query\s*\(", "Query"),
            (r"\.QueryRow\s*\(", "QueryRow"),
            (r"\.Exec\s*\(", "Exec"),
            (r"\.Prepare\s*\(", "Prepare"),
        ],
        "postgres": [
            (r"sql\.Open\s*\(\s*[\"']postgres[\"']", "Connect"),
            (r"pgx\.", "Query"),
        ],
        "dynamodb": [
            (r"dynamodb\.New|dynamodb\.Client", "Connect"),
            (r"\.PutItem\s*\(", "PutItem"),
            (r"\.GetItem\s*\(", "GetItem"),
            (r"\.UpdateItem\s*\(", "UpdateItem"),
            (r"\.DeleteItem\s*\(", "DeleteItem"),
            (r"\.Query\s*\(", "Query"),
            (r"\.Scan\s*\(", "Scan"),
        ],
    }
    
    # Patterns for AWS service operations
    AWS_PATTERNS = {
        "s3": [
            (r"s3\.New|s3\.Client|s3manager", "S3 Client"),
            (r"\.PutObject\s*\(|PutObjectInput", "PutObject"),
            (r"\.GetObject\s*\(|GetObjectInput", "GetObject"),
            (r"\.DeleteObject\s*\(|DeleteObjectInput", "DeleteObject"),
            (r"\.ListObjects|ListObjectsV2", "ListObjects"),
            (r"PutObjectTagging|PutObjectTaggingInput", "TagObject"),
            (r"s3control\.CreateJob|CreateJobInput", "BatchJob"),
        ],
        "sqs": [
            (r"sqs\.New|sqs\.Client", "SQS Client"),
            (r"\.SendMessage\s*\(", "SendMessage"),
            (r"\.ReceiveMessage\s*\(", "ReceiveMessage"),
            (r"\.DeleteMessage\s*\(", "DeleteMessage"),
        ],
        "sns": [
            (r"sns\.New|sns\.Client", "SNS Client"),
            (r"\.Publish\s*\(", "Publish"),
        ],
        "lambda": [
            (r"lambda\.New|lambda\.Client", "Lambda Client"),
            (r"\.Invoke\s*\(", "Invoke"),
        ],
    }
    
    # Patterns for HTTP client operations
    HTTP_CLIENT_PATTERNS = [
        (r"http\.Get\s*\(", "GET"),
        (r"http\.Post\s*\(", "POST"),
        (r"http\.NewRequest\s*\(\s*[\"'](\w+)[\"']", "Request"),
        (r"\.Do\s*\(\s*req", "Execute"),
    ]
    
    # Patterns for environment variable access
    ENV_PATTERNS = [
        r'os\.Getenv\s*\(\s*["\']([^"\']+)["\']',
        r'os\.LookupEnv\s*\(\s*["\']([^"\']+)["\']',
        r'conf:"[^"]*env:([^,"]+)',  # ardanlabs/conf tags
        r'envconfig\.[^(]+\([^)]*["\']([^"\']+)["\']',
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract Go structs and interfaces."""
        models = []
        
        for file_path in self.find_files():
            # Skip test files
            if "_test.go" in file_path.name:
                continue
            
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract structs
            models.extend(self._extract_structs(content, rel_path))
            
            # Extract interfaces
            models.extend(self._extract_interfaces(content, rel_path))
        
        return models
    
    def _extract_structs(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract struct definitions from Go code."""
        models = []
        
        # Pattern to match struct definitions
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{([^}]+)\}'
        
        for match in re.finditer(struct_pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract fields
            fields = []
            field_pattern = r'(\w+)\s+([^\s`\n]+)(?:\s+`([^`]+)`)?'
            
            for field_match in re.finditer(field_pattern, body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                tags = field_match.group(3) or ""
                
                # Skip comments and embedded types without explicit type
                if field_name.startswith("//") or field_name.startswith("/*"):
                    continue
                
                # Extract description from conf tag if present
                description = None
                if "help:" in tags:
                    help_match = re.search(r'help:([^,"\'`]+)', tags)
                    if help_match:
                        description = help_match.group(1).strip()
                
                fields.append(ExtractedField(
                    name=field_name,
                    type=field_type,
                    tags=tags,
                    description=description,
                ))
            
            if fields:
                # Determine model type based on name
                is_config = "config" in name.lower()
                
                models.append(ExtractedModel(
                    name=name,
                    model_type=ModelType.STRUCT,
                    file=file_path,
                    line=line,
                    fields=fields,
                    decorators=["config"] if is_config else [],
                    github_url=self.github_link(file_path, line),
                ))
        
        return models
    
    def _extract_interfaces(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract interface definitions from Go code."""
        models = []
        
        # Pattern to match interface definitions
        interface_pattern = r'type\s+(\w+)\s+interface\s*\{([^}]+)\}'
        
        for match in re.finditer(interface_pattern, content, re.MULTILINE | re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract method signatures
            methods = []
            method_pattern = r'(\w+)\s*\([^)]*\)\s*[^\n]*'
            
            for method_match in re.finditer(method_pattern, body):
                methods.append(method_match.group(0).strip())
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.INTERFACE,
                file=file_path,
                line=line,
                methods=methods,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract HTTP route definitions."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            for pattern in self.HTTP_ROUTE_PATTERNS:
                for i, line in enumerate(lines):
                    for match in re.finditer(pattern, line, re.IGNORECASE):
                        groups = match.groups()
                        
                        # Extract method and path based on pattern match
                        if len(groups) >= 3:
                            method = groups[1].upper()
                            path = groups[2]
                        elif len(groups) >= 2:
                            method = groups[0].upper() if groups[0] in ("GET", "POST", "PUT", "DELETE", "PATCH") else "ANY"
                            path = groups[1]
                        else:
                            continue
                        
                        # Normalize method names
                        if method in ("HANDLEFUNC", "HANDLE"):
                            method = "ANY"
                        
                        endpoints.append(ExtractedEndpoint(
                            method=method,
                            path=path,
                            file=rel_path,
                            line=i + 1,
                            github_url=self.github_link(rel_path, i + 1),
                        ))
        
        return endpoints
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract database and external service operations."""
        side_effects = []
        seen = set()  # Avoid duplicates
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Database operations
            for db_type, patterns in self.DB_PATTERNS.items():
                for pattern, operation in patterns:
                    if re.search(pattern, content):
                        key = (db_type, operation)
                        if key not in seen:
                            seen.add(key)
                            side_effects.append(ExtractedSideEffect(
                                category=SideEffectCategory.DATABASE,
                                operation=operation,
                                target=db_type,
                                file=rel_path,
                                github_url=self.github_link(rel_path),
                            ))
            
            # AWS service operations
            for service, patterns in self.AWS_PATTERNS.items():
                for pattern, operation in patterns:
                    if re.search(pattern, content):
                        key = (service, operation)
                        if key not in seen:
                            seen.add(key)
                            side_effects.append(ExtractedSideEffect(
                                category=SideEffectCategory.CLOUD_SERVICE,
                                operation=operation,
                                target=f"AWS {service.upper()}",
                                file=rel_path,
                                github_url=self.github_link(rel_path),
                            ))
            
            # HTTP client operations
            for pattern, operation in self.HTTP_CLIENT_PATTERNS:
                if re.search(pattern, content):
                    key = ("http", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.HTTP,
                            operation=operation,
                            target="HTTP Client",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract environment variable usage and config patterns."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            for pattern in self.ENV_PATTERNS:
                for i, line in enumerate(lines):
                    for match in re.finditer(pattern, line):
                        env_var = match.group(1)
                        
                        if env_var not in seen:
                            seen.add(env_var)
                            
                            # Try to extract default value from conf tag
                            default = None
                            default_match = re.search(r'default:([^,"\'\s`]+)', line)
                            if default_match:
                                default = default_match.group(1)
                            
                            # Try to extract help text
                            description = None
                            help_match = re.search(r'help:([^,"\'`]+)', line)
                            if help_match:
                                description = help_match.group(1).strip()
                            
                            configs.append(ExtractedConfig(
                                key=env_var,
                                source="env",
                                file=rel_path,
                                line=i + 1,
                                default=default,
                                description=description,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract dependencies from go.mod."""
        dependencies = []
        
        go_mod = self.repo_path / "go.mod"
        if not go_mod.exists():
            return dependencies
        
        content = self.read_file(go_mod)
        if not content:
            return dependencies
        
        # Parse require block
        in_require = False
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line.startswith("require ("):
                in_require = True
                continue
            elif line == ")":
                in_require = False
                continue
            elif line.startswith("require "):
                # Single-line require
                parts = line[8:].strip().split()
                if len(parts) >= 2:
                    dependencies.append(ExtractedDependency(
                        name=parts[0],
                        version=parts[1],
                        file="go.mod",
                        line=i + 1,
                    ))
            elif in_require and line and not line.startswith("//"):
                # Multi-line require block
                parts = line.split()
                if len(parts) >= 2:
                    dependencies.append(ExtractedDependency(
                        name=parts[0],
                        version=parts[1],
                        file="go.mod",
                        line=i + 1,
                    ))
        
        return dependencies
