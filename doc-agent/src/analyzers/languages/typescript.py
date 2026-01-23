"""
TypeScript/JavaScript language analyzer.

Extracts data models, API endpoints, side effects, and configuration
from TypeScript and JavaScript source code.

Supports:
- Express.js, NestJS, Fastify routes
- TypeScript interfaces, types, classes
- React components
- Zod/Yup schemas
- Next.js API routes
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


@register_analyzer("typescript")
@register_analyzer("javascript")
class TypeScriptAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for TypeScript and JavaScript source code.
    
    Extracts:
    - Interfaces, types, classes
    - Express/NestJS/Fastify routes
    - React components
    - Zod/Yup schemas
    - Database operations (Prisma, TypeORM, Sequelize)
    - HTTP client calls (fetch, axios)
    - Environment variable usage
    """
    
    language = "typescript"
    extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
    
    # Patterns for TypeScript interfaces
    INTERFACE_PATTERN = r'(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w,\s<>]+))?\s*\{'
    
    # Patterns for TypeScript types
    TYPE_PATTERN = r'(?:export\s+)?type\s+(\w+)(?:<[^>]+>)?\s*=\s*'
    
    # Patterns for classes
    CLASS_PATTERN = r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{'
    
    # Patterns for React components
    COMPONENT_PATTERNS = [
        # Function component
        r'(?:export\s+)?(?:const|function)\s+(\w+)\s*[=:]\s*(?:\([^)]*\)|[^=])*\s*=>\s*(?:\(|<)',
        # Class component
        r'class\s+(\w+)\s+extends\s+(?:React\.)?(?:Component|PureComponent)',
    ]
    
    # HTTP route patterns
    ROUTE_PATTERNS = {
        "express": [
            r'(?:app|router)\.(get|post|put|delete|patch|all)\s*\(\s*[\'"`]([^\'"]+)[\'"`]',
            r'@(Get|Post|Put|Delete|Patch)\s*\(\s*[\'"`]?([^\'"`)]*)[\'"`]?\s*\)',
        ],
        "fastify": [
            r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"]+)[\'"`]',
        ],
        "nextjs": [
            # Next.js API routes are file-based
            r'export\s+(?:default\s+)?(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)',
            r'export\s+(?:const|async\s+function)\s+(GET|POST|PUT|DELETE|PATCH)',
        ],
        "hono": [
            r'app\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"]+)[\'"`]',
        ],
    }
    
    # GraphQL patterns
    GRAPHQL_PATTERNS = [
        r'@Query\s*\(\s*\)',
        r'@Mutation\s*\(\s*\)',
        r'@Resolver\s*\(\s*\)',
        r'type\s+(Query|Mutation)\s*\{',
    ]
    
    # Zod schema patterns
    ZOD_PATTERNS = [
        r'(?:export\s+)?(?:const|let)\s+(\w+Schema)\s*=\s*z\.',
        r'z\.object\s*\(\s*\{',
    ]
    
    # Database operation patterns
    DB_PATTERNS = {
        "prisma": [
            (r'prisma\.\w+\.findMany', "FindMany"),
            (r'prisma\.\w+\.findUnique', "FindUnique"),
            (r'prisma\.\w+\.findFirst', "FindFirst"),
            (r'prisma\.\w+\.create', "Create"),
            (r'prisma\.\w+\.update', "Update"),
            (r'prisma\.\w+\.delete', "Delete"),
            (r'prisma\.\w+\.upsert', "Upsert"),
            (r'\$queryRaw', "RawQuery"),
        ],
        "typeorm": [
            (r'\.find\s*\(', "Find"),
            (r'\.findOne\s*\(', "FindOne"),
            (r'\.save\s*\(', "Save"),
            (r'\.remove\s*\(', "Remove"),
            (r'\.createQueryBuilder', "QueryBuilder"),
            (r'@Entity\s*\(', "Entity"),
        ],
        "sequelize": [
            (r'\.findAll\s*\(', "FindAll"),
            (r'\.findOne\s*\(', "FindOne"),
            (r'\.create\s*\(', "Create"),
            (r'\.update\s*\(', "Update"),
            (r'\.destroy\s*\(', "Destroy"),
        ],
        "mongoose": [
            (r'\.find\s*\(', "Find"),
            (r'\.findOne\s*\(', "FindOne"),
            (r'\.findById\s*\(', "FindById"),
            (r'\.save\s*\(', "Save"),
            (r'\.deleteOne\s*\(', "DeleteOne"),
            (r'mongoose\.model\s*\(', "Model"),
        ],
    }
    
    # HTTP client patterns
    HTTP_PATTERNS = [
        (r'fetch\s*\(\s*[\'"`]', "fetch"),
        (r'axios\.(get|post|put|delete|patch)', "axios"),
        (r'axios\s*\(\s*\{', "axios"),
        (r'\.request\s*\(\s*\{', "HTTP Request"),
        (r'http\.get\s*\(', "HTTP GET"),
        (r'http\.post\s*\(', "HTTP POST"),
    ]
    
    # Environment variable patterns
    ENV_PATTERNS = [
        r'process\.env\.(\w+)',
        r'process\.env\[[\'"]([\w]+)[\'"]\]',
        r'import\.meta\.env\.(\w+)',
        r'Deno\.env\.get\s*\(\s*[\'"](\w+)[\'"]',
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract TypeScript interfaces, types, and classes."""
        models = []
        
        for file_path in self.find_files():
            # Skip test files
            if ".test." in file_path.name or ".spec." in file_path.name:
                continue
            
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract interfaces
            models.extend(self._extract_interfaces(content, rel_path))
            
            # Extract type aliases
            models.extend(self._extract_types(content, rel_path))
            
            # Extract classes
            models.extend(self._extract_classes(content, rel_path))
            
            # Extract Zod schemas
            models.extend(self._extract_zod_schemas(content, rel_path))
        
        return models
    
    def _extract_interfaces(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract TypeScript interface definitions."""
        models = []
        
        for match in re.finditer(self.INTERFACE_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            extends = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract interface body
            interface_start = match.end()
            brace_count = 1
            interface_end = interface_start
            
            for i, char in enumerate(content[interface_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        interface_end = interface_start + i
                        break
            
            body = content[interface_start:interface_end]
            fields = self._extract_ts_fields(body)
            
            implements = []
            if extends:
                implements = [e.strip() for e in extends.split(',')]
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.INTERFACE,
                file=file_path,
                line=line,
                fields=fields,
                implements=implements,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_types(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract TypeScript type aliases."""
        models = []
        
        for match in re.finditer(self.TYPE_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Get the type definition
            type_start = match.end()
            # Find the end of the type (semicolon or newline without continuation)
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.TYPE_ALIAS,
                file=file_path,
                line=line,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_classes(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract class definitions."""
        models = []
        
        for match in re.finditer(self.CLASS_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            line = content[:match.start()].count('\n') + 1
            
            # Extract decorators from lines above
            decorators = []
            lines = content[:match.start()].split('\n')
            for prev_line in reversed(lines[-5:]):
                prev_line = prev_line.strip()
                if prev_line.startswith('@'):
                    dec_match = re.match(r'@(\w+)', prev_line)
                    if dec_match:
                        decorators.append(dec_match.group(1))
                elif prev_line and not prev_line.startswith('//'):
                    break
            
            implements_list = []
            if implements:
                implements_list = [i.strip() for i in implements.split(',')]
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                parent=extends,
                implements=implements_list,
                decorators=decorators,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_zod_schemas(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract Zod schema definitions."""
        models = []
        
        for pattern in self.ZOD_PATTERNS[:1]:  # Just named schemas
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                models.append(ExtractedModel(
                    name=name,
                    model_type=ModelType.SCHEMA,
                    file=file_path,
                    line=line,
                    decorators=["zod"],
                    github_url=self.github_link(file_path, line),
                ))
        
        return models
    
    def _extract_ts_fields(self, body: str) -> list[ExtractedField]:
        """Extract fields from TypeScript interface/type body."""
        fields = []
        
        # Pattern for interface fields: name: type or name?: type
        field_pattern = r'(\w+)\s*(\?)?:\s*([^;,\n]+)'
        
        for match in re.finditer(field_pattern, body):
            name = match.group(1)
            optional = match.group(2) == '?'
            field_type = match.group(3).strip()
            
            fields.append(ExtractedField(
                name=name,
                type=field_type,
                required=not optional,
            ))
        
        return fields
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract HTTP route definitions."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            # Check for framework-specific routes
            for framework, patterns in self.ROUTE_PATTERNS.items():
                for pattern in patterns:
                    for i, line in enumerate(lines):
                        for match in re.finditer(pattern, line, re.IGNORECASE):
                            groups = match.groups()
                            
                            if len(groups) >= 2:
                                method = groups[0].upper()
                                path = groups[1] if groups[1] else "/"
                            else:
                                method = groups[0].upper()
                                # For Next.js, path is based on file location
                                if framework == "nextjs" and "/api/" in rel_path:
                                    path = "/" + rel_path.replace(".ts", "").replace(".js", "")
                                    path = path.replace("/route", "").replace("/page", "")
                                else:
                                    path = "/"
                            
                            endpoints.append(ExtractedEndpoint(
                                method=method,
                                path=path,
                                file=rel_path,
                                line=i + 1,
                                decorators=[framework],
                                github_url=self.github_link(rel_path, i + 1),
                            ))
            
            # Check for GraphQL resolvers
            for pattern in self.GRAPHQL_PATTERNS:
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        endpoints.append(ExtractedEndpoint(
                            method="GRAPHQL",
                            path="/graphql",
                            file=rel_path,
                            line=i + 1,
                            decorators=["graphql"],
                            github_url=self.github_link(rel_path, i + 1),
                        ))
                        break  # Only add once per file
        
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
            
            for pattern in self.ENV_PATTERNS:
                for i, line in enumerate(lines):
                    for match in re.finditer(pattern, line):
                        env_var = match.group(1)
                        
                        if env_var not in seen:
                            seen.add(env_var)
                            configs.append(ExtractedConfig(
                                key=env_var,
                                source="env",
                                file=rel_path,
                                line=i + 1,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract dependencies from package.json."""
        dependencies = []
        
        package_json = self.repo_path / "package.json"
        if not package_json.exists():
            return dependencies
        
        content = self.read_file(package_json)
        if not content:
            return dependencies
        
        import json
        try:
            data = json.loads(content)
            
            # Extract dependencies
            for name, version in data.get("dependencies", {}).items():
                dependencies.append(ExtractedDependency(
                    name=name,
                    version=version,
                    file="package.json",
                ))
            
            # Extract devDependencies
            for name, version in data.get("devDependencies", {}).items():
                dependencies.append(ExtractedDependency(
                    name=name,
                    version=version,
                    file="package.json",
                ))
        except json.JSONDecodeError:
            pass
        
        return dependencies
