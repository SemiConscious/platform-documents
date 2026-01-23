"""
Python language analyzer.

Extracts data models, API endpoints, side effects, and configuration
from Python source code.

Supports:
- Classes, dataclasses, Pydantic models
- Flask, FastAPI, Django routes
- SQLAlchemy models
- AWS Boto3 operations
- requests/httpx HTTP calls
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


@register_analyzer("python")
class PythonAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Python source code.
    
    Extracts:
    - Classes (regular, dataclasses, Pydantic)
    - Flask/FastAPI/Django routes
    - SQLAlchemy models
    - Database operations
    - HTTP client calls
    - AWS operations (boto3)
    - Environment variable usage
    """
    
    language = "python"
    extensions = [".py", ".pyw"]
    
    # Class patterns
    CLASS_PATTERN = r'class\s+(\w+)(?:\s*\(\s*([^)]*)\s*\))?\s*:'
    
    # Dataclass and Pydantic patterns
    DATACLASS_DECORATOR = r'@dataclass(?:\s*\([^)]*\))?'
    PYDANTIC_BASE = r'\(\s*(?:BaseModel|BaseSettings)\s*\)'
    
    # Function/method patterns
    FUNCTION_PATTERN = r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:'
    
    # Route patterns for different frameworks
    ROUTE_PATTERNS = {
        "flask": [
            r'@(?:app|bp|blueprint)\.(get|post|put|delete|patch|route)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@app\.route\s*\(\s*[\'"]([^\'"]+)[\'"](?:.*?methods\s*=\s*\[([^\]]+)\])?',
        ],
        "fastapi": [
            r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@app\.api_route\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ],
        "django": [
            r'path\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r're_path\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'url\s*\(\s*r?[\'"]([^\'"]+)[\'"]',
        ],
    }
    
    # SQLAlchemy patterns
    SQLALCHEMY_PATTERNS = [
        (r'class\s+\w+\s*\([^)]*Base[^)]*\)', "SQLAlchemy Model"),
        (r'Column\s*\(', "Column Definition"),
        (r'relationship\s*\(', "Relationship"),
        (r'ForeignKey\s*\(', "Foreign Key"),
    ]
    
    # Database operation patterns
    DB_PATTERNS = {
        "sqlalchemy": [
            (r'session\.query\s*\(', "Query"),
            (r'session\.add\s*\(', "Add"),
            (r'session\.delete\s*\(', "Delete"),
            (r'session\.commit\s*\(', "Commit"),
            (r'session\.execute\s*\(', "Execute"),
            (r'\.filter\s*\(', "Filter"),
            (r'\.all\s*\(\s*\)', "All"),
            (r'\.first\s*\(\s*\)', "First"),
        ],
        "django_orm": [
            (r'\.objects\.filter\s*\(', "Filter"),
            (r'\.objects\.get\s*\(', "Get"),
            (r'\.objects\.create\s*\(', "Create"),
            (r'\.objects\.all\s*\(\s*\)', "All"),
            (r'\.save\s*\(\s*\)', "Save"),
            (r'\.delete\s*\(\s*\)', "Delete"),
        ],
        "raw_sql": [
            (r'cursor\.execute\s*\(', "Execute"),
            (r'connection\.execute\s*\(', "Execute"),
        ],
    }
    
    # HTTP client patterns
    HTTP_PATTERNS = [
        (r'requests\.(get|post|put|delete|patch)\s*\(', "requests"),
        (r'httpx\.(get|post|put|delete|patch)\s*\(', "httpx"),
        (r'aiohttp\.ClientSession', "aiohttp"),
        (r'urllib\.request\.urlopen', "urllib"),
    ]
    
    # AWS Boto3 patterns
    BOTO3_PATTERNS = {
        "s3": [
            (r"boto3\.client\s*\(\s*['\"]s3['\"]", "S3 Client"),
            (r"\.upload_file\s*\(", "Upload File"),
            (r"\.download_file\s*\(", "Download File"),
            (r"\.put_object\s*\(", "Put Object"),
            (r"\.get_object\s*\(", "Get Object"),
            (r"\.delete_object\s*\(", "Delete Object"),
        ],
        "sqs": [
            (r"boto3\.client\s*\(\s*['\"]sqs['\"]", "SQS Client"),
            (r"\.send_message\s*\(", "Send Message"),
            (r"\.receive_message\s*\(", "Receive Message"),
        ],
        "dynamodb": [
            (r"boto3\.(?:client|resource)\s*\(\s*['\"]dynamodb['\"]", "DynamoDB Client"),
            (r"\.put_item\s*\(", "Put Item"),
            (r"\.get_item\s*\(", "Get Item"),
            (r"\.query\s*\(", "Query"),
        ],
        "lambda": [
            (r"boto3\.client\s*\(\s*['\"]lambda['\"]", "Lambda Client"),
            (r"\.invoke\s*\(", "Invoke"),
        ],
    }
    
    # Environment variable patterns
    ENV_PATTERNS = [
        r'os\.environ\.get\s*\(\s*[\'"](\w+)[\'"]',
        r'os\.environ\s*\[\s*[\'"](\w+)[\'"]',
        r'os\.getenv\s*\(\s*[\'"](\w+)[\'"]',
        r'env\s*\(\s*[\'"](\w+)[\'"]',  # django-environ
        r'config\s*\(\s*[\'"](\w+)[\'"]',  # decouple
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract Python classes, dataclasses, and Pydantic models."""
        models = []
        
        for file_path in self.find_files():
            # Skip test files
            if "test" in file_path.name.lower():
                continue
            
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract classes
            models.extend(self._extract_classes(content, rel_path))
        
        return models
    
    def _extract_classes(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract class definitions."""
        models = []
        lines = content.split('\n')
        
        for match in re.finditer(self.CLASS_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            bases = match.group(2) or ""
            line = content[:match.start()].count('\n') + 1
            
            # Check for decorators
            decorators = []
            model_type = ModelType.CLASS
            
            # Look at lines above for decorators
            for prev_line in reversed(lines[max(0, line-10):line-1]):
                prev_line = prev_line.strip()
                if prev_line.startswith('@'):
                    dec_match = re.match(r'@(\w+)', prev_line)
                    if dec_match:
                        decorators.append(dec_match.group(1))
                        if dec_match.group(1) == 'dataclass':
                            model_type = ModelType.DATACLASS
                elif prev_line and not prev_line.startswith('#'):
                    break
            
            # Check for Pydantic
            if 'BaseModel' in bases or 'BaseSettings' in bases:
                model_type = ModelType.PYDANTIC
                decorators.append('pydantic')
            
            # Check for SQLAlchemy
            if 'Base' in bases or 'DeclarativeBase' in bases:
                decorators.append('sqlalchemy')
            
            # Extract class body
            class_start = match.end()
            indent_level = None
            class_end = class_start
            
            for i, char in enumerate(content[class_start:]):
                if char == '\n':
                    # Check next line indentation
                    next_line_start = class_start + i + 1
                    if next_line_start < len(content):
                        next_line = content[next_line_start:].split('\n')[0]
                        if next_line.strip():
                            current_indent = len(next_line) - len(next_line.lstrip())
                            if indent_level is None:
                                indent_level = current_indent
                            elif current_indent < indent_level and current_indent > 0:
                                class_end = next_line_start
                                break
                            elif current_indent == 0 and not next_line.strip().startswith('#'):
                                class_end = next_line_start
                                break
            
            if class_end == class_start:
                # Get to end of file or next class
                next_class = re.search(r'\nclass\s+\w+', content[class_start:])
                if next_class:
                    class_end = class_start + next_class.start()
                else:
                    class_end = len(content)
            
            body = content[class_start:class_end]
            
            # Extract fields
            fields = self._extract_python_fields(body, model_type)
            
            # Extract methods
            methods = self._extract_python_methods(body)
            
            # Parse base classes
            implements = [b.strip() for b in bases.split(',') if b.strip()] if bases else []
            parent = implements[0] if implements else None
            
            models.append(ExtractedModel(
                name=name,
                model_type=model_type,
                file=file_path,
                line=line,
                fields=fields,
                methods=methods,
                parent=parent,
                implements=implements[1:] if len(implements) > 1 else [],
                decorators=decorators,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_python_fields(self, body: str, model_type: ModelType) -> list[ExtractedField]:
        """Extract fields from Python class body."""
        fields = []
        
        if model_type == ModelType.DATACLASS:
            # Dataclass field pattern: name: type = default
            pattern = r'(\w+)\s*:\s*([^\n=]+)(?:\s*=\s*([^\n]+))?'
        elif model_type == ModelType.PYDANTIC:
            # Pydantic field pattern
            pattern = r'(\w+)\s*:\s*([^\n=]+)(?:\s*=\s*([^\n]+))?'
        else:
            # SQLAlchemy Column pattern
            pattern = r'(\w+)\s*=\s*Column\s*\(\s*(\w+)'
        
        for match in re.finditer(pattern, body):
            name = match.group(1)
            field_type = match.group(2).strip() if match.group(2) else "Any"
            default = match.group(3).strip() if len(match.groups()) > 2 and match.group(3) else None
            
            # Skip methods and private attrs
            if name.startswith('_') or name in ('self', 'cls'):
                continue
            
            # Clean up type annotation
            field_type = field_type.split('#')[0].strip()  # Remove comments
            
            fields.append(ExtractedField(
                name=name,
                type=field_type,
                default=default,
                required=default is None,
            ))
        
        return fields[:20]  # Limit fields
    
    def _extract_python_methods(self, body: str) -> list[str]:
        """Extract method signatures."""
        methods = []
        
        for match in re.finditer(self.FUNCTION_PATTERN, body):
            name = match.group(1)
            params = match.group(2)
            return_type = match.group(3)
            
            sig = f"{name}({params})"
            if return_type:
                sig += f" -> {return_type.strip()}"
            
            methods.append(sig)
        
        return methods[:15]  # Limit methods
    
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
                            
                            if framework == "django":
                                # Django path patterns
                                path = groups[0]
                                method = "ANY"
                            elif len(groups) >= 2:
                                method = groups[0].upper()
                                path = groups[1]
                            else:
                                path = groups[0]
                                method = "GET"
                            
                            # For Flask @route with methods
                            if "route" in pattern.lower() and len(groups) > 1 and groups[1]:
                                methods_str = groups[1]
                                if "POST" in methods_str.upper():
                                    method = "POST"
                                elif "PUT" in methods_str.upper():
                                    method = "PUT"
                            
                            endpoints.append(ExtractedEndpoint(
                                method=method.upper(),
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
            for pattern, client in self.HTTP_PATTERNS:
                if re.search(pattern, content):
                    key = ("http", client)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.HTTP,
                            operation=client,
                            target="HTTP Client",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
            
            # AWS Boto3 operations
            for service, patterns in self.BOTO3_PATTERNS.items():
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
                            
                            # Try to extract default
                            default = None
                            default_match = re.search(rf'{env_var}[\'"],\s*[\'"]([^\'"]+)[\'"]', line)
                            if default_match:
                                default = default_match.group(1)
                            
                            configs.append(ExtractedConfig(
                                key=env_var,
                                source="env",
                                file=rel_path,
                                line=i + 1,
                                default=default,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract dependencies from requirements.txt or pyproject.toml."""
        dependencies = []
        
        # Try requirements.txt
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            content = self.read_file(req_file)
            if content:
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        # Parse package==version or package>=version
                        match = re.match(r'([a-zA-Z0-9_-]+)(?:[=<>!]+(.+))?', line)
                        if match:
                            dependencies.append(ExtractedDependency(
                                name=match.group(1),
                                version=match.group(2),
                                file="requirements.txt",
                            ))
        
        # Try pyproject.toml
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            content = self.read_file(pyproject)
            if content:
                # Simple parsing for dependencies
                in_deps = False
                for line in content.split('\n'):
                    if '[tool.poetry.dependencies]' in line or '[project.dependencies]' in line:
                        in_deps = True
                        continue
                    elif line.startswith('['):
                        in_deps = False
                    elif in_deps and '=' in line:
                        parts = line.split('=')
                        name = parts[0].strip().strip('"')
                        version = parts[1].strip().strip('"') if len(parts) > 1 else None
                        if name and name != 'python':
                            dependencies.append(ExtractedDependency(
                                name=name,
                                version=version,
                                file="pyproject.toml",
                            ))
        
        return dependencies
