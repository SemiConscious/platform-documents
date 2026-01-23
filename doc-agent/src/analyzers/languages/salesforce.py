"""
Salesforce language analyzer.

Extracts data models, API endpoints, side effects, and configuration
from Salesforce Apex, Lightning Web Components (LWC), and Visualforce.

Supports:
- Apex classes, interfaces, triggers
- Lightning Web Components
- SOQL/SOSL queries
- DML operations
- @AuraEnabled methods (API endpoints)
- Custom Objects (from XML)
"""

import re
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

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


@register_analyzer("apex")
class SalesforceAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for Salesforce Apex, LWC, and Visualforce code.
    
    Extracts:
    - Apex classes, interfaces, enums
    - Apex triggers
    - @AuraEnabled methods (REST-like endpoints)
    - @RemoteAction methods
    - SOQL/SOSL queries
    - DML operations (insert, update, delete, upsert)
    - HTTP callouts
    - Custom Objects and Fields
    - Lightning Web Components
    """
    
    language = "apex"
    extensions = [".cls", ".trigger", ".page", ".component"]
    
    # Include LWC files
    EXTRA_EXTENSIONS = [".js", ".html"]
    
    # Apex class patterns
    CLASS_PATTERN = r'(?:public|private|global|protected)?\s*(?:virtual|abstract|with sharing|without sharing|inherited sharing)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{'
    INTERFACE_PATTERN = r'(?:public|private|global)?\s*interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?\s*\{'
    ENUM_PATTERN = r'(?:public|private|global)?\s*enum\s+(\w+)\s*\{'
    TRIGGER_PATTERN = r'trigger\s+(\w+)\s+on\s+(\w+)\s*\(([^)]+)\)\s*\{'
    
    # Method patterns
    METHOD_PATTERN = r'(?:public|private|protected|global)\s+(?:static\s+)?(?:override\s+)?(\w+(?:<[\w,\s<>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
    
    # Apex annotations for endpoints
    ENDPOINT_ANNOTATIONS = [
        r'@AuraEnabled(?:\s*\([^)]*\))?',
        r'@RemoteAction',
        r'@HttpGet',
        r'@HttpPost',
        r'@HttpPut',
        r'@HttpDelete',
        r'@HttpPatch',
        r'@RestResource\s*\(\s*urlMapping\s*=\s*[\'"]([^\'"]+)[\'"]',
    ]
    
    # SOQL/SOSL patterns
    SOQL_PATTERN = r'\[\s*SELECT\s+([^\]]+)\s+FROM\s+(\w+)'
    SOSL_PATTERN = r'\[\s*FIND\s+'
    
    # DML patterns
    DML_PATTERNS = [
        (r'\binsert\s+', "Insert"),
        (r'\bupdate\s+', "Update"),
        (r'\bdelete\s+', "Delete"),
        (r'\bupsert\s+', "Upsert"),
        (r'\bundelete\s+', "Undelete"),
        (r'Database\.insert\s*\(', "Database.insert"),
        (r'Database\.update\s*\(', "Database.update"),
        (r'Database\.delete\s*\(', "Database.delete"),
        (r'Database\.upsert\s*\(', "Database.upsert"),
    ]
    
    # HTTP Callout patterns
    HTTP_PATTERNS = [
        (r'Http\s+\w+\s*=\s*new\s+Http\s*\(', "HTTP Callout"),
        (r'HttpRequest\s+\w+\s*=', "HTTP Request"),
        (r'\.setMethod\s*\(\s*[\'"](\w+)[\'"]', "HTTP Method"),
        (r'\.setEndpoint\s*\(', "Set Endpoint"),
        (r'EncodingUtil\.urlEncode', "URL Encode"),
    ]
    
    # Custom metadata patterns
    CUSTOM_METADATA_PATTERNS = [
        (r'\w+__mdt', "Custom Metadata"),
        (r'\w+__c', "Custom Object/Field"),
    ]
    
    # LWC patterns
    LWC_PATTERNS = {
        "wire": r'@wire\s*\(\s*(\w+)',
        "api": r'@api\s+(\w+)',
        "track": r'@track\s+(\w+)',
        "import_apex": r"import\s+(\w+)\s+from\s+['\"]@salesforce/apex/(\w+)\.(\w+)['\"]",
    }
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract Apex classes, interfaces, enums, and triggers."""
        models = []
        
        # Find Apex files
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract classes
            models.extend(self._extract_classes(content, rel_path))
            
            # Extract interfaces
            models.extend(self._extract_interfaces(content, rel_path))
            
            # Extract enums
            models.extend(self._extract_enums(content, rel_path))
            
            # Extract triggers
            models.extend(self._extract_triggers(content, rel_path))
        
        # Find custom objects from metadata
        models.extend(self._extract_custom_objects())
        
        # Find LWC components
        models.extend(self._extract_lwc_components())
        
        return models
    
    def _extract_classes(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract Apex class definitions."""
        models = []
        
        for match in re.finditer(self.CLASS_PATTERN, content, re.MULTILINE | re.IGNORECASE):
            name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            line = content[:match.start()].count('\n') + 1
            
            # Extract class body
            class_start = match.end()
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
            
            # Extract fields (properties)
            fields = self._extract_apex_fields(body)
            
            # Extract methods
            methods = self._extract_apex_methods(body)
            
            # Extract decorators
            decorators = self._extract_annotations(content[:match.start()])
            
            implements_list = []
            if implements:
                implements_list = [i.strip() for i in implements.split(',')]
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                fields=fields,
                methods=methods,
                parent=extends,
                implements=implements_list,
                decorators=decorators,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_interfaces(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract Apex interface definitions."""
        models = []
        
        for match in re.finditer(self.INTERFACE_PATTERN, content, re.MULTILINE | re.IGNORECASE):
            name = match.group(1)
            extends = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract interface body for method signatures
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
            methods = self._extract_apex_methods(body)
            
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
    
    def _extract_enums(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract Apex enum definitions."""
        models = []
        
        for match in re.finditer(self.ENUM_PATTERN, content, re.MULTILINE | re.IGNORECASE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract enum values
            enum_start = match.end()
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
            
            body = content[enum_start:enum_end].strip()
            values = [v.strip() for v in body.split(',') if v.strip()]
            
            fields = [ExtractedField(name=v, type="enum_value") for v in values]
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.ENUM,
                file=file_path,
                line=line,
                fields=fields,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_triggers(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract Apex trigger definitions."""
        models = []
        
        for match in re.finditer(self.TRIGGER_PATTERN, content, re.MULTILINE | re.IGNORECASE):
            name = match.group(1)
            sobject = match.group(2)
            events = match.group(3)
            line = content[:match.start()].count('\n') + 1
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                decorators=["trigger", f"on:{sobject}", f"events:{events}"],
                description=f"Trigger on {sobject} for {events}",
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_custom_objects(self) -> list[ExtractedModel]:
        """Extract custom objects from Salesforce metadata."""
        models = []
        
        # Look for object definitions in metadata
        for xml_file in self.repo_path.rglob("*.object-meta.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Extract object name from filename
                name = xml_file.name.replace(".object-meta.xml", "")
                rel_path = self.relative_path(xml_file)
                
                # Extract fields from XML
                fields = []
                ns = {'sf': 'http://soap.sforce.com/2006/04/metadata'}
                
                for field_elem in root.findall('.//sf:fields', ns):
                    field_name = field_elem.find('sf:fullName', ns)
                    field_type = field_elem.find('sf:type', ns)
                    
                    if field_name is not None:
                        fields.append(ExtractedField(
                            name=field_name.text or "",
                            type=field_type.text if field_type is not None else "Unknown",
                        ))
                
                models.append(ExtractedModel(
                    name=name,
                    model_type=ModelType.CLASS,
                    file=rel_path,
                    line=1,
                    fields=fields,
                    decorators=["custom_object"],
                    github_url=self.github_link(rel_path, 1),
                ))
            except (ET.ParseError, Exception):
                continue
        
        return models
    
    def _extract_lwc_components(self) -> list[ExtractedModel]:
        """Extract Lightning Web Components."""
        models = []
        
        # Look for LWC JS files
        for js_file in self.repo_path.rglob("**/lwc/**/*.js"):
            content = self.read_file(js_file)
            if not content:
                continue
            
            rel_path = self.relative_path(js_file)
            
            # Check if it's a component (extends LightningElement)
            if "extends LightningElement" in content or "LightningElement" in content:
                name = js_file.stem
                
                # Extract @api properties
                fields = []
                for match in re.finditer(self.LWC_PATTERNS["api"], content):
                    fields.append(ExtractedField(
                        name=match.group(1),
                        type="@api",
                    ))
                
                # Extract @track properties
                for match in re.finditer(self.LWC_PATTERNS["track"], content):
                    fields.append(ExtractedField(
                        name=match.group(1),
                        type="@track",
                    ))
                
                models.append(ExtractedModel(
                    name=name,
                    model_type=ModelType.CLASS,
                    file=rel_path,
                    line=1,
                    fields=fields,
                    decorators=["lwc", "LightningElement"],
                    github_url=self.github_link(rel_path, 1),
                ))
        
        return models
    
    def _extract_apex_fields(self, body: str) -> list[ExtractedField]:
        """Extract fields from Apex class body."""
        fields = []
        
        # Pattern for Apex properties
        field_pattern = r'(?:public|private|protected|global)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[\w,\s<>]+>)?)\s+(\w+)\s*(?:=|;|\{)'
        
        for match in re.finditer(field_pattern, body):
            field_type = match.group(1)
            field_name = match.group(2)
            
            # Skip methods (they have parentheses after the name)
            if field_name + '(' in body[match.start():match.start() + len(match.group(0)) + 10]:
                continue
            
            fields.append(ExtractedField(
                name=field_name,
                type=field_type,
            ))
        
        return fields
    
    def _extract_apex_methods(self, body: str) -> list[str]:
        """Extract method signatures from Apex body."""
        methods = []
        
        for match in re.finditer(self.METHOD_PATTERN, body):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)
            methods.append(f"{return_type} {method_name}({params})")
        
        return methods
    
    def _extract_annotations(self, preceding_text: str) -> list[str]:
        """Extract annotations from text preceding a class/method."""
        annotations = []
        lines = preceding_text.split('\n')[-10:]  # Check last 10 lines
        
        for line in lines:
            line = line.strip()
            if line.startswith('@'):
                ann_match = re.match(r'@(\w+)', line)
                if ann_match:
                    annotations.append(ann_match.group(1))
        
        return annotations
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract @AuraEnabled and @Http* methods as endpoints."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            # Find @RestResource URL mapping
            rest_resource_url = None
            rest_match = re.search(r'@RestResource\s*\(\s*urlMapping\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if rest_match:
                rest_resource_url = rest_match.group(1)
            
            for i, line in enumerate(lines):
                for annotation_pattern in self.ENDPOINT_ANNOTATIONS:
                    if re.search(annotation_pattern, line, re.IGNORECASE):
                        # Find the method on the next few lines
                        method_text = '\n'.join(lines[i:i+5])
                        method_match = re.search(self.METHOD_PATTERN, method_text)
                        
                        if method_match:
                            return_type = method_match.group(1)
                            method_name = method_match.group(2)
                            
                            # Determine HTTP method
                            http_method = "POST"  # Default for @AuraEnabled
                            if "@HttpGet" in line:
                                http_method = "GET"
                            elif "@HttpPost" in line:
                                http_method = "POST"
                            elif "@HttpPut" in line:
                                http_method = "PUT"
                            elif "@HttpDelete" in line:
                                http_method = "DELETE"
                            elif "@HttpPatch" in line:
                                http_method = "PATCH"
                            
                            # Determine path
                            path = f"@AuraEnabled/{method_name}"
                            if rest_resource_url:
                                path = rest_resource_url
                            
                            endpoints.append(ExtractedEndpoint(
                                method=http_method,
                                path=path,
                                file=rel_path,
                                line=i + 1,
                                handler=method_name,
                                response_type=return_type,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return endpoints
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract SOQL queries, DML operations, and HTTP callouts."""
        side_effects = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # SOQL queries
            for match in re.finditer(self.SOQL_PATTERN, content, re.IGNORECASE):
                sobject = match.group(2)
                key = ("soql", sobject)
                if key not in seen:
                    seen.add(key)
                    side_effects.append(ExtractedSideEffect(
                        category=SideEffectCategory.DATABASE,
                        operation="SOQL Query",
                        target=sobject,
                        file=rel_path,
                        github_url=self.github_link(rel_path),
                    ))
            
            # SOSL queries
            if re.search(self.SOSL_PATTERN, content, re.IGNORECASE):
                key = ("sosl", "search")
                if key not in seen:
                    seen.add(key)
                    side_effects.append(ExtractedSideEffect(
                        category=SideEffectCategory.DATABASE,
                        operation="SOSL Search",
                        target="Multiple Objects",
                        file=rel_path,
                        github_url=self.github_link(rel_path),
                    ))
            
            # DML operations
            for pattern, operation in self.DML_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    key = ("dml", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.DATABASE,
                            operation=operation,
                            target="SObject",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
            
            # HTTP callouts
            for pattern, operation in self.HTTP_PATTERNS:
                if re.search(pattern, content):
                    key = ("http", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.HTTP,
                            operation=operation,
                            target="External Service",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract custom settings, custom metadata, and named credentials."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Custom metadata and custom settings references
            for pattern, config_type in self.CUSTOM_METADATA_PATTERNS:
                for match in re.finditer(pattern, content):
                    name = match.group(0)
                    if name not in seen:
                        seen.add(name)
                        configs.append(ExtractedConfig(
                            key=name,
                            source=config_type,
                            file=rel_path,
                            line=1,
                            github_url=self.github_link(rel_path),
                        ))
            
            # Named credentials
            named_cred_pattern = r'callout:(\w+)'
            for match in re.finditer(named_cred_pattern, content):
                name = match.group(1)
                if name not in seen:
                    seen.add(name)
                    configs.append(ExtractedConfig(
                        key=name,
                        source="Named Credential",
                        file=rel_path,
                        line=1,
                        github_url=self.github_link(rel_path),
                    ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract dependencies from sfdx-project.json."""
        dependencies = []
        
        sfdx_project = self.repo_path / "sfdx-project.json"
        if not sfdx_project.exists():
            return dependencies
        
        content = self.read_file(sfdx_project)
        if not content:
            return dependencies
        
        import json
        try:
            data = json.loads(content)
            
            # Extract package dependencies
            for pkg in data.get("packageDirectories", []):
                for dep in pkg.get("dependencies", []):
                    dependencies.append(ExtractedDependency(
                        name=dep.get("package", "Unknown"),
                        version=dep.get("versionNumber"),
                        file="sfdx-project.json",
                    ))
        except json.JSONDecodeError:
            pass
        
        return dependencies
