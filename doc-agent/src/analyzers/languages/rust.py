"""
Rust language analyzer.

Extracts structs, enums, traits, and implementations from Rust source code.
"""

import re
from pathlib import Path

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


@register_analyzer("rust")
class RustAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Rust source code.
    
    Extracts:
    - Structs and enums
    - Traits and implementations
    - HTTP routes (Actix, Axum, Rocket)
    - Database operations
    """
    
    language = "rust"
    extensions = [".rs"]
    
    # Type patterns
    STRUCT_PATTERN = r'(?:#\[[\w\(\),\s="]+\]\s*)*(?:pub\s+)?struct\s+(\w+)(?:<[^>]+>)?\s*(?:\([^)]*\)|{)'
    ENUM_PATTERN = r'(?:#\[[\w\(\),\s="]+\]\s*)*(?:pub\s+)?enum\s+(\w+)(?:<[^>]+>)?\s*\{'
    TRAIT_PATTERN = r'(?:pub\s+)?trait\s+(\w+)(?:<[^>]+>)?\s*(?::\s*[\w\s+<>]+)?\s*\{'
    IMPL_PATTERN = r'impl(?:<[^>]+>)?\s+(?:(\w+)\s+for\s+)?(\w+)'
    
    # Route patterns
    ROUTE_PATTERNS = {
        "actix": [
            r'#\[(get|post|put|delete|patch)\s*\(\s*"([^"]+)"',
            r'\.route\s*\(\s*"([^"]+)"\s*,\s*web::(get|post|put|delete|patch)',
        ],
        "axum": [
            r'\.route\s*\(\s*"([^"]+)"\s*,\s*(get|post|put|delete|patch)',
        ],
        "rocket": [
            r'#\[(get|post|put|delete|patch)\s*\(\s*"([^"]+)"',
        ],
    }
    
    # Database patterns
    DB_PATTERNS = {
        "diesel": [
            (r'diesel::', "Diesel ORM"),
            (r'\.load::<', "Load Query"),
            (r'\.execute\s*\(', "Execute"),
            (r'\.get_result\s*\(', "Get Result"),
        ],
        "sqlx": [
            (r'sqlx::', "SQLx"),
            (r'query!\s*\(', "Compile-time Query"),
            (r'query_as!\s*\(', "Typed Query"),
        ],
        "sea_orm": [
            (r'sea_orm::', "SeaORM"),
            (r'\.find\s*\(', "Find"),
            (r'\.insert\s*\(', "Insert"),
        ],
    }
    
    # HTTP client patterns
    HTTP_PATTERNS = [
        (r'reqwest::', "reqwest"),
        (r'hyper::', "hyper"),
        (r'\.get\s*\(\s*"http', "HTTP GET"),
        (r'\.post\s*\(\s*"http', "HTTP POST"),
    ]
    
    # AWS SDK patterns
    AWS_PATTERNS = [
        (r'aws_sdk_s3::', "AWS S3"),
        (r'aws_sdk_dynamodb::', "AWS DynamoDB"),
        (r'aws_sdk_sqs::', "AWS SQS"),
        (r'aws_sdk_lambda::', "AWS Lambda"),
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract Rust structs, enums, and traits."""
        models = []
        
        for file_path in self.find_files():
            # Skip test files
            if "test" in file_path.name:
                continue
            
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract structs
            models.extend(self._extract_structs(content, rel_path))
            
            # Extract enums
            models.extend(self._extract_enums(content, rel_path))
            
            # Extract traits
            models.extend(self._extract_traits(content, rel_path))
        
        return models
    
    def _extract_structs(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract struct definitions."""
        models = []
        
        for match in re.finditer(self.STRUCT_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract decorators from derive macros
            decorators = []
            derive_match = re.search(r'#\[derive\(([^)]+)\)\]', content[max(0, match.start()-200):match.start()])
            if derive_match:
                decorators = [d.strip() for d in derive_match.group(1).split(',')]
            
            # Extract fields if it's a struct with braces
            fields = []
            if '{' in match.group(0):
                struct_start = content.find('{', match.start()) + 1
                brace_count = 1
                struct_end = struct_start
                
                for i, char in enumerate(content[struct_start:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            struct_end = struct_start + i
                            break
                
                body = content[struct_start:struct_end]
                
                # Parse fields
                field_pattern = r'(?:pub\s+)?(\w+)\s*:\s*([^,\n]+)'
                for field_match in re.finditer(field_pattern, body):
                    fields.append(ExtractedField(
                        name=field_match.group(1),
                        type=field_match.group(2).strip().rstrip(','),
                    ))
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.STRUCT,
                file=file_path,
                line=line,
                fields=fields,
                decorators=decorators,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_enums(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract enum definitions."""
        models = []
        
        for match in re.finditer(self.ENUM_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract variants
            enum_start = content.find('{', match.start()) + 1
            brace_count = 1
            enum_end = enum_start
            
            for i, char in enumerate(content[enum_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        enum_end = enum_start + i
                        break
            
            body = content[enum_start:enum_end]
            
            # Parse variants
            fields = []
            variant_pattern = r'(\w+)(?:\s*\{[^}]*\}|\s*\([^)]*\))?'
            for variant_match in re.finditer(variant_pattern, body):
                variant = variant_match.group(1)
                if variant and not variant.startswith('//'):
                    fields.append(ExtractedField(
                        name=variant,
                        type="enum_variant",
                    ))
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.ENUM,
                file=file_path,
                line=line,
                fields=fields,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_traits(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract trait definitions."""
        models = []
        
        for match in re.finditer(self.TRAIT_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract method signatures
            trait_start = content.find('{', match.start()) + 1
            brace_count = 1
            trait_end = trait_start
            
            for i, char in enumerate(content[trait_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        trait_end = trait_start + i
                        break
            
            body = content[trait_start:trait_end]
            
            # Parse methods
            methods = []
            method_pattern = r'fn\s+(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)'
            for method_match in re.finditer(method_pattern, body):
                methods.append(method_match.group(0))
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.TRAIT,
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
            
            for framework, patterns in self.ROUTE_PATTERNS.items():
                for pattern in patterns:
                    for i, line in enumerate(lines):
                        for match in re.finditer(pattern, line, re.IGNORECASE):
                            groups = match.groups()
                            
                            if len(groups) >= 2:
                                # Could be (method, path) or (path, method)
                                if groups[0].upper() in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'):
                                    method = groups[0].upper()
                                    path = groups[1]
                                else:
                                    path = groups[0]
                                    method = groups[1].upper()
                            else:
                                continue
                            
                            endpoints.append(ExtractedEndpoint(
                                method=method,
                                path=path,
                                file=rel_path,
                                line=i + 1,
                                decorators=[framework],
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return endpoints
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract database and HTTP operations."""
        side_effects = []
        seen = set()
        
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
            
            # HTTP operations
            for pattern, operation in self.HTTP_PATTERNS:
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
            
            # AWS operations
            for pattern, operation in self.AWS_PATTERNS:
                if re.search(pattern, content):
                    key = ("aws", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.CLOUD_SERVICE,
                            operation=operation,
                            target="AWS",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract environment variable usage."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            # Environment variable patterns
            env_patterns = [
                r'env::var\s*\(\s*"(\w+)"',
                r'std::env::var\s*\(\s*"(\w+)"',
                r'env!\s*\(\s*"(\w+)"',
            ]
            
            for pattern in env_patterns:
                for i, line in enumerate(lines):
                    for match in re.finditer(pattern, line):
                        var_name = match.group(1)
                        if var_name not in seen:
                            seen.add(var_name)
                            configs.append(ExtractedConfig(
                                key=var_name,
                                source="env",
                                file=rel_path,
                                line=i + 1,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract dependencies from Cargo.toml."""
        dependencies = []
        
        cargo_toml = self.repo_path / "Cargo.toml"
        if not cargo_toml.exists():
            return dependencies
        
        content = self.read_file(cargo_toml)
        if not content:
            return dependencies
        
        in_deps = False
        for line in content.split('\n'):
            if '[dependencies]' in line or '[dev-dependencies]' in line:
                in_deps = True
                continue
            elif line.startswith('['):
                in_deps = False
            elif in_deps and '=' in line:
                parts = line.split('=')
                name = parts[0].strip()
                version_part = parts[1].strip()
                
                # Parse version
                version = None
                if version_part.startswith('"'):
                    version = version_part.strip('"')
                elif version_part.startswith('{'):
                    version_match = re.search(r'version\s*=\s*"([^"]+)"', version_part)
                    if version_match:
                        version = version_match.group(1)
                
                if name:
                    dependencies.append(ExtractedDependency(
                        name=name,
                        version=version,
                        file="Cargo.toml",
                    ))
        
        return dependencies
