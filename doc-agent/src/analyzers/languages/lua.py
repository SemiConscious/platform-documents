"""
Lua language analyzer.

Extracts functions, configurations, and side effects from Lua source code.

Supports:
- FreeSWITCH dialplan scripts
- Lua modules and functions
- Configuration tables
"""

import re
from pathlib import Path

from ..base import BaseLanguageAnalyzer
from ..factory import register_analyzer
from ..models import (
    ExtractedConfig,
    ExtractedEndpoint,
    ExtractedField,
    ExtractedModel,
    ExtractedSideEffect,
    ModelType,
    SideEffectCategory,
)


@register_analyzer("lua")
class LuaAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Lua source code.
    
    Extracts:
    - Functions and modules
    - FreeSWITCH API calls
    - Configuration tables
    - Database operations
    """
    
    language = "lua"
    extensions = [".lua"]
    
    # Function patterns
    FUNCTION_PATTERN = r'(?:local\s+)?function\s+(\w+(?:\.\w+)*)\s*\(([^)]*)\)'
    METHOD_PATTERN = r'function\s+(\w+):(\w+)\s*\(([^)]*)\)'
    
    # FreeSWITCH patterns
    FREESWITCH_PATTERNS = [
        (r'freeswitch\.API\s*\(\s*\)', "FreeSWITCH API"),
        (r'session:answer\s*\(', "Answer Call"),
        (r'session:hangup\s*\(', "Hangup Call"),
        (r'session:playAndGetDigits\s*\(', "Play and Get Digits"),
        (r'session:speak\s*\(', "Text to Speech"),
        (r'session:streamFile\s*\(', "Stream Audio File"),
        (r'session:execute\s*\(', "Execute Application"),
        (r'session:transfer\s*\(', "Transfer Call"),
        (r'session:bridge\s*\(', "Bridge Call"),
        (r'session:setVariable\s*\(', "Set Variable"),
        (r'session:getVariable\s*\(', "Get Variable"),
    ]
    
    # Database patterns
    DB_PATTERNS = [
        (r'require\s*\(\s*[\'"]luasql\.', "LuaSQL"),
        (r'env:connect\s*\(', "DB Connect"),
        (r'conn:execute\s*\(', "DB Execute"),
        (r'cursor:fetch\s*\(', "DB Fetch"),
    ]
    
    # HTTP patterns
    HTTP_PATTERNS = [
        (r'require\s*\(\s*[\'"]socket\.http', "LuaSocket HTTP"),
        (r'http\.request\s*\(', "HTTP Request"),
        (r'require\s*\(\s*[\'"]ltn12', "LTN12"),
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract Lua modules and classes."""
        models = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Look for module definitions
            module_match = re.search(r'local\s+(\w+)\s*=\s*\{\s*\}', content)
            if module_match:
                module_name = module_match.group(1)
                
                # Extract functions in this module
                methods = []
                for match in re.finditer(rf'{module_name}\.(\w+)\s*=\s*function', content):
                    methods.append(match.group(1))
                
                models.append(ExtractedModel(
                    name=module_name,
                    model_type=ModelType.CLASS,
                    file=rel_path,
                    line=1,
                    methods=methods,
                    decorators=["lua_module"],
                    github_url=self.github_link(rel_path, 1),
                ))
        
        return models
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract FreeSWITCH dialplan entry points."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Look for main dialplan functions
            for match in re.finditer(self.FUNCTION_PATTERN, content):
                func_name = match.group(1)
                line = content[:match.start()].count('\n') + 1
                
                # If this is a dialplan handler (common patterns)
                if any(name in func_name.lower() for name in ['handler', 'main', 'dialplan', 'ivr']):
                    endpoints.append(ExtractedEndpoint(
                        method="DIALPLAN",
                        path=func_name,
                        file=rel_path,
                        line=line,
                        handler=func_name,
                        decorators=["freeswitch"],
                        github_url=self.github_link(rel_path, line),
                    ))
        
        return endpoints
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract FreeSWITCH API calls and DB operations."""
        side_effects = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # FreeSWITCH operations
            for pattern, operation in self.FREESWITCH_PATTERNS:
                if re.search(pattern, content):
                    key = ("freeswitch", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.EXTERNAL_API,
                            operation=operation,
                            target="FreeSWITCH",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
            
            # Database operations
            for pattern, operation in self.DB_PATTERNS:
                if re.search(pattern, content):
                    key = ("db", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.DATABASE,
                            operation=operation,
                            target="Database",
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
        """Extract configuration from Lua files."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            # Look for configuration patterns
            config_patterns = [
                r'os\.getenv\s*\(\s*[\'"](\w+)[\'"]',
                r'config\s*\[\s*[\'"](\w+)[\'"]',
                r'settings\s*\[\s*[\'"](\w+)[\'"]',
            ]
            
            for pattern in config_patterns:
                for i, line in enumerate(lines):
                    for match in re.finditer(pattern, line):
                        key = match.group(1)
                        if key not in seen:
                            seen.add(key)
                            configs.append(ExtractedConfig(
                                key=key,
                                source="lua_config",
                                file=rel_path,
                                line=i + 1,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return configs
