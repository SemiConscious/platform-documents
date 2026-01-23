"""
Bash/Shell script analyzer.

Extracts functions, environment variables, and external commands
from shell scripts.
"""

import re
from pathlib import Path

from ..base import BaseLanguageAnalyzer
from ..factory import register_analyzer
from ..models import (
    ExtractedConfig,
    ExtractedEndpoint,
    ExtractedModel,
    ExtractedSideEffect,
    ModelType,
    SideEffectCategory,
)


@register_analyzer("bash")
class BashAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Bash/Shell scripts.
    
    Extracts:
    - Function definitions
    - Environment variable usage
    - External command calls (curl, aws, docker, etc.)
    - File operations
    """
    
    language = "bash"
    extensions = [".sh", ".bash", ".zsh"]
    
    # Function pattern
    FUNCTION_PATTERN = r'(?:function\s+)?(\w+)\s*\(\s*\)\s*\{'
    
    # Environment variable patterns
    ENV_PATTERNS = [
        r'\$\{?(\w+)\}?',
        r'export\s+(\w+)=',
        r'(\w+)=\$',
    ]
    
    # External command patterns
    COMMAND_PATTERNS = {
        "aws": [
            (r'aws\s+s3\s+', "AWS S3"),
            (r'aws\s+ec2\s+', "AWS EC2"),
            (r'aws\s+lambda\s+', "AWS Lambda"),
            (r'aws\s+sqs\s+', "AWS SQS"),
            (r'aws\s+dynamodb\s+', "AWS DynamoDB"),
            (r'aws-vault\s+', "AWS Vault"),
        ],
        "docker": [
            (r'docker\s+build\s+', "Docker Build"),
            (r'docker\s+run\s+', "Docker Run"),
            (r'docker\s+push\s+', "Docker Push"),
            (r'docker-compose\s+', "Docker Compose"),
        ],
        "kubernetes": [
            (r'kubectl\s+apply\s+', "Kubectl Apply"),
            (r'kubectl\s+get\s+', "Kubectl Get"),
            (r'kubectl\s+delete\s+', "Kubectl Delete"),
            (r'helm\s+', "Helm"),
        ],
        "http": [
            (r'curl\s+', "cURL"),
            (r'wget\s+', "wget"),
            (r'httpie\s+', "HTTPie"),
        ],
        "database": [
            (r'mysql\s+', "MySQL CLI"),
            (r'psql\s+', "PostgreSQL CLI"),
            (r'mongo\s+', "MongoDB CLI"),
            (r'redis-cli\s+', "Redis CLI"),
        ],
    }
    
    # File operation patterns
    FILE_PATTERNS = [
        (r'cat\s+', "Read File"),
        (r'echo\s+.*>\s*', "Write File"),
        (r'rm\s+', "Delete File"),
        (r'cp\s+', "Copy File"),
        (r'mv\s+', "Move File"),
        (r'mkdir\s+', "Create Directory"),
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract shell functions as models."""
        models = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract functions
            for match in re.finditer(self.FUNCTION_PATTERN, content):
                name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                models.append(ExtractedModel(
                    name=name,
                    model_type=ModelType.CLASS,
                    file=rel_path,
                    line=line,
                    decorators=["shell_function"],
                    github_url=self.github_link(rel_path, line),
                ))
        
        return models
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Shell scripts don't typically have endpoints."""
        return []
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract external command calls."""
        side_effects = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # External commands
            for category, patterns in self.COMMAND_PATTERNS.items():
                for pattern, operation in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        key = (category, operation)
                        if key not in seen:
                            seen.add(key)
                            
                            cat = SideEffectCategory.CLOUD_SERVICE
                            if category == "http":
                                cat = SideEffectCategory.HTTP
                            elif category == "database":
                                cat = SideEffectCategory.DATABASE
                            elif category in ("docker", "kubernetes"):
                                cat = SideEffectCategory.EXTERNAL_API
                            
                            side_effects.append(ExtractedSideEffect(
                                category=cat,
                                operation=operation,
                                target=category,
                                file=rel_path,
                                github_url=self.github_link(rel_path),
                            ))
            
            # File operations
            for pattern, operation in self.FILE_PATTERNS:
                if re.search(pattern, content):
                    key = ("file", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.FILE,
                            operation=operation,
                            target="Filesystem",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract environment variable usage."""
        configs = []
        seen = set()
        
        # Common variables to skip
        skip_vars = {'PATH', 'HOME', 'USER', 'PWD', 'SHELL', 'TERM', 
                     'LANG', 'LC_ALL', 'DISPLAY', 'EDITOR', 'PAGER',
                     '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                     '@', '*', '#', '?', '-', '$', '!', '_'}
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Skip comments
                if line.strip().startswith('#'):
                    continue
                
                # Find exported variables
                export_match = re.search(r'export\s+(\w+)(?:=(.*))?', line)
                if export_match:
                    var_name = export_match.group(1)
                    default = export_match.group(2)
                    
                    if var_name not in seen and var_name not in skip_vars:
                        seen.add(var_name)
                        configs.append(ExtractedConfig(
                            key=var_name,
                            source="export",
                            file=rel_path,
                            line=i + 1,
                            default=default.strip('"\'') if default else None,
                            github_url=self.github_link(rel_path, i + 1),
                        ))
                
                # Find variable references
                for match in re.finditer(r'\$\{?(\w+)\}?', line):
                    var_name = match.group(1)
                    if var_name not in seen and var_name not in skip_vars and not var_name.isdigit():
                        seen.add(var_name)
                        configs.append(ExtractedConfig(
                            key=var_name,
                            source="env",
                            file=rel_path,
                            line=i + 1,
                            github_url=self.github_link(rel_path, i + 1),
                        ))
        
        return configs
