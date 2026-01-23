"""
ActionScript language analyzer.

Extracts classes, interfaces, and components from ActionScript/Flex source code.
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


@register_analyzer("actionscript")
class ActionScriptAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for ActionScript and Flex/MXML source code.
    
    Extracts:
    - ActionScript classes and interfaces
    - MXML components
    - Remote object calls
    - HTTP service calls
    """
    
    language = "actionscript"
    extensions = [".as", ".mxml"]
    
    # Class patterns
    CLASS_PATTERN = r'(?:public|internal)?\s*(?:final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{'
    INTERFACE_PATTERN = r'(?:public|internal)?\s*interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?\s*\{'
    
    # Property patterns
    PROPERTY_PATTERN = r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:var|const)\s+(\w+)\s*:\s*(\w+(?:<[^>]+>)?)'
    
    # Method patterns
    METHOD_PATTERN = r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:override\s+)?function\s+(?:get\s+|set\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?'
    
    # MXML component patterns
    MXML_COMPONENT_PATTERN = r'<([a-z]+):(\w+)'
    MXML_ID_PATTERN = r'id="(\w+)"'
    
    # Remote service patterns
    REMOTE_PATTERNS = [
        (r'RemoteObject', "Remote Object"),
        (r'HTTPService', "HTTP Service"),
        (r'WebService', "Web Service"),
        (r'\.send\s*\(', "Service Call"),
        (r'URLLoader', "URL Loader"),
        (r'URLRequest', "URL Request"),
    ]
    
    # Data binding patterns
    BINDING_PATTERNS = [
        (r'\[Bindable\]', "Bindable Property"),
        (r'\[Embed\(', "Embedded Asset"),
        (r'\[Event\(', "Event Declaration"),
        (r'\[RemoteClass\(', "Remote Class Mapping"),
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract ActionScript classes, interfaces, and MXML components."""
        models = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            if file_path.suffix == '.as':
                # ActionScript files
                models.extend(self._extract_classes(content, rel_path))
                models.extend(self._extract_interfaces(content, rel_path))
            elif file_path.suffix == '.mxml':
                # MXML files
                models.extend(self._extract_mxml_components(content, rel_path, file_path.stem))
        
        return models
    
    def _extract_classes(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract ActionScript class definitions."""
        models = []
        
        for match in re.finditer(self.CLASS_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            line = content[:match.start()].count('\n') + 1
            
            # Extract class body
            class_start = content.find('{', match.start()) + 1
            brace_count = 1
            class_end = class_start
            
            for i, char in enumerate(content[class_start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = class_start + i
                        break
            
            body = content[class_start:class_end]
            
            # Extract properties
            fields = []
            for prop_match in re.finditer(self.PROPERTY_PATTERN, body):
                fields.append(ExtractedField(
                    name=prop_match.group(1),
                    type=prop_match.group(2),
                ))
            
            # Extract methods
            methods = []
            for method_match in re.finditer(self.METHOD_PATTERN, body):
                method_name = method_match.group(1)
                params = method_match.group(2)
                return_type = method_match.group(3) or "void"
                methods.append(f"{method_name}({params}): {return_type}")
            
            # Extract decorators (metadata tags)
            decorators = []
            for pattern, _ in self.BINDING_PATTERNS:
                if re.search(pattern, content[:match.start()]):
                    dec_match = re.search(r'\[(\w+)', pattern)
                    if dec_match:
                        decorators.append(dec_match.group(1))
            
            implements_list = []
            if implements:
                implements_list = [i.strip() for i in implements.split(',')]
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                fields=fields,
                methods=methods[:15],
                parent=extends,
                implements=implements_list,
                decorators=decorators,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_interfaces(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract ActionScript interface definitions."""
        models = []
        
        for match in re.finditer(self.INTERFACE_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            extends = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract interface body
            interface_start = content.find('{', match.start()) + 1
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
            
            # Extract method signatures
            methods = []
            for method_match in re.finditer(r'function\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\w+)', body):
                method_name = method_match.group(1)
                params = method_match.group(2)
                return_type = method_match.group(3)
                methods.append(f"{method_name}({params}): {return_type}")
            
            implements_list = []
            if extends:
                implements_list = [e.strip() for e in extends.split(',')]
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.INTERFACE,
                file=file_path,
                line=line,
                methods=methods,
                implements=implements_list,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_mxml_components(self, content: str, file_path: str, component_name: str) -> list[ExtractedModel]:
        """Extract MXML component definitions."""
        models = []
        
        # Extract the root component
        root_match = re.search(r'<([a-z]+):(\w+)', content)
        if root_match:
            namespace = root_match.group(1)
            parent = root_match.group(2)
            
            # Extract child component IDs as fields
            fields = []
            for id_match in re.finditer(self.MXML_ID_PATTERN, content):
                # Find the component type
                id_pos = id_match.start()
                # Look backward to find the component tag
                tag_match = re.search(r'<([a-z]+:)?(\w+)[^>]*$', content[:id_pos])
                if tag_match:
                    comp_type = tag_match.group(2)
                    fields.append(ExtractedField(
                        name=id_match.group(1),
                        type=comp_type,
                    ))
            
            # Look for Script block to extract methods
            methods = []
            script_match = re.search(r'<[a-z]+:Script>.*?<!\[CDATA\[(.*?)\]\]>.*?</[a-z]+:Script>', content, re.DOTALL)
            if script_match:
                script_content = script_match.group(1)
                for method_match in re.finditer(self.METHOD_PATTERN, script_content):
                    method_name = method_match.group(1)
                    params = method_match.group(2)
                    return_type = method_match.group(3) or "void"
                    methods.append(f"{method_name}({params}): {return_type}")
            
            models.append(ExtractedModel(
                name=component_name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=1,
                fields=fields,
                methods=methods[:15],
                parent=parent,
                decorators=["mxml", namespace],
                github_url=self.github_link(file_path, 1),
            ))
        
        return models
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract remote service endpoints."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Look for RemoteObject destinations
            for match in re.finditer(r'destination\s*=\s*"(\w+)"', content):
                line = content[:match.start()].count('\n') + 1
                endpoints.append(ExtractedEndpoint(
                    method="AMF",
                    path=match.group(1),
                    file=rel_path,
                    line=line,
                    decorators=["RemoteObject"],
                    github_url=self.github_link(rel_path, line),
                ))
            
            # Look for HTTPService URLs
            for match in re.finditer(r'url\s*=\s*"([^"]+)"', content):
                url = match.group(1)
                if url.startswith('http') or url.startswith('/'):
                    line = content[:match.start()].count('\n') + 1
                    endpoints.append(ExtractedEndpoint(
                        method="HTTP",
                        path=url,
                        file=rel_path,
                        line=line,
                        decorators=["HTTPService"],
                        github_url=self.github_link(rel_path, line),
                    ))
        
        return endpoints
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract remote service and HTTP calls."""
        side_effects = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            for pattern, operation in self.REMOTE_PATTERNS:
                if re.search(pattern, content):
                    key = ("remote", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.HTTP,
                            operation=operation,
                            target="Remote Service",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract configuration constants and bindings."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            # Look for constants
            const_pattern = r'(?:public|private)\s+(?:static\s+)?const\s+(\w+)\s*:\s*\w+\s*=\s*([^;]+)'
            for i, line in enumerate(lines):
                for match in re.finditer(const_pattern, line):
                    name = match.group(1)
                    value = match.group(2).strip()
                    
                    if name not in seen:
                        seen.add(name)
                        configs.append(ExtractedConfig(
                            key=name,
                            source="const",
                            file=rel_path,
                            line=i + 1,
                            default=value.strip('"\''),
                            github_url=self.github_link(rel_path, i + 1),
                        ))
        
        return configs
