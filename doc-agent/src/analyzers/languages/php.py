"""
PHP language analyzer.

Extracts data models, API endpoints, side effects, and configuration
from PHP source code using tree-sitter AST parsing with regex fallback.

Supports Kohana MVC framework patterns used in platform-api.
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


@register_analyzer("php")
class PHPAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for PHP source code.
    
    Extracts:
    - Classes (models, services, controllers)
    - Interfaces and traits
    - Controller action methods (endpoints)
    - Database operations (PDO, mysqli)
    - HTTP client calls (curl, Guzzle)
    - Environment variable usage
    - Config file references
    """
    
    language = "php"
    extensions = [".php"]
    
    # Patterns for class definitions
    CLASS_PATTERN = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{'
    INTERFACE_PATTERN = r'interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?\s*\{'
    TRAIT_PATTERN = r'trait\s+(\w+)\s*\{'
    
    # Patterns for methods (potential endpoints in controllers)
    METHOD_PATTERN = r'(?:public|protected|private)\s+(?:static\s+)?function\s+(\w+)\s*\(([^)]*)\)'
    
    # Patterns for properties
    PROPERTY_PATTERN = r'(?:public|protected|private)\s+(?:static\s+)?(?:\?)?(\$\w+)(?:\s*=\s*([^;]+))?;'
    TYPED_PROPERTY_PATTERN = r'(?:public|protected|private)\s+(?:static\s+)?(?:\?)?(\w+)\s+(\$\w+)(?:\s*=\s*([^;]+))?;'
    
    # Controller action patterns (for endpoint detection)
    CONTROLLER_ACTION_PATTERNS = [
        # Kohana-style action methods
        r'function\s+(action_(\w+))\s*\(',
        # RESTful controller methods
        r'function\s+(get|post|put|delete|patch)_(\w+)\s*\(',
        # Generic REST methods
        r'function\s+(index|show|create|store|edit|update|destroy)\s*\(',
    ]
    
    # Kohana REST validation rules pattern (defines REST endpoints)
    KOHANA_VALIDATION_RULES_PATTERN = r"'(\w+)'\s*=>\s*array\s*\(\s*'(get|post|put|delete)'\s*=>"
    
    # Route definition patterns
    ROUTE_PATTERNS = [
        # Laravel-style routes
        r'Route::(get|post|put|delete|patch|any)\s*\(\s*[\'"]([^\'"]+)[\'"]',
        # Symfony annotations
        r'@Route\s*\(\s*[\'"]([^\'"]+)[\'"]',
        # Kohana routes in config
        r'Route::set\s*\(\s*[\'"](\w+)[\'"].*?[\'"]([^\'"]+)[\'"]',
    ]
    
    # Database operation patterns
    DB_PATTERNS = {
        "pdo": [
            (r'\$\w+->query\s*\(', "Query"),
            (r'\$\w+->exec\s*\(', "Exec"),
            (r'\$\w+->prepare\s*\(', "Prepare"),
            (r'PDO::', "PDO"),
        ],
        "mysqli": [
            (r'mysqli_query\s*\(', "Query"),
            (r'mysqli_real_query\s*\(', "Query"),
            (r'\$\w+->query\s*\(', "Query"),
        ],
        "kohana_db": [
            (r'DB::query\s*\(', "Query"),
            (r'DB::select\s*\(', "Select"),
            (r'DB::insert\s*\(', "Insert"),
            (r'DB::update\s*\(', "Update"),
            (r'DB::delete\s*\(', "Delete"),
            (r'\$this->_\w*DB\[', "DB Access"),
        ],
    }
    
    # HTTP client patterns
    HTTP_PATTERNS = [
        (r'curl_init\s*\(', "cURL Init"),
        (r'curl_exec\s*\(', "cURL Execute"),
        (r'file_get_contents\s*\(\s*[\'"]https?:', "HTTP GET"),
        (r'->request\s*\(\s*[\'"]GET', "HTTP GET"),
        (r'->request\s*\(\s*[\'"]POST', "HTTP POST"),
        (r'->get\s*\(', "HTTP GET"),
        (r'->post\s*\(', "HTTP POST"),
        (r'GuzzleHttp', "Guzzle Client"),
    ]
    
    # File operation patterns
    FILE_PATTERNS = [
        (r'fopen\s*\(', "File Open"),
        (r'fwrite\s*\(', "File Write"),
        (r'file_put_contents\s*\(', "File Write"),
        (r'file_get_contents\s*\((?!\s*[\'"]https?:)', "File Read"),
        (r'unlink\s*\(', "File Delete"),
    ]
    
    # Config/env patterns
    ENV_PATTERNS = [
        r'\$_ENV\s*\[\s*[\'"]([^\'"]+)[\'"]',
        r'\$_SERVER\s*\[\s*[\'"]([^\'"]+)[\'"]',
        r'getenv\s*\(\s*[\'"]([^\'"]+)[\'"]',
        r'env\s*\(\s*[\'"]([^\'"]+)[\'"]',
        r'config::get\s*\(\s*[\'"]([^\'"]+)[\'"]',
        r'Config::get\s*\(\s*[\'"]([^\'"]+)[\'"]',
        r'Kohana::config\s*\(\s*[\'"]([^\'"]+)[\'"]',
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract PHP classes, interfaces, and traits."""
        models = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract classes
            models.extend(self._extract_classes(content, rel_path))
            
            # Extract interfaces
            models.extend(self._extract_interfaces(content, rel_path))
            
            # Extract traits
            models.extend(self._extract_traits(content, rel_path))
        
        return models
    
    def _extract_classes(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract class definitions."""
        models = []
        
        for match in re.finditer(self.CLASS_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            parent = match.group(2)
            implements = match.group(3)
            line = content[:match.start()].count('\n') + 1
            
            # Extract class body for fields and methods
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
            
            class_body = content[class_start:class_end]
            
            # Extract properties
            fields = self._extract_properties(class_body)
            
            # Extract methods
            methods = self._extract_methods(class_body)
            
            # Parse implements list
            implements_list = []
            if implements:
                implements_list = [i.strip() for i in implements.split(',')]
            
            # Determine if this is a model, service, controller, etc.
            decorators = []
            if "_Model" in name or name.endswith("Model"):
                decorators.append("model")
            if "_Controller" in name or name.endswith("Controller"):
                decorators.append("controller")
            if "Service" in name:
                decorators.append("service")
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                fields=fields,
                methods=methods,
                parent=parent,
                implements=implements_list,
                decorators=decorators,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_interfaces(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract interface definitions."""
        models = []
        
        for match in re.finditer(self.INTERFACE_PATTERN, content, re.MULTILINE):
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
            
            interface_body = content[interface_start:interface_end]
            methods = self._extract_methods(interface_body)
            
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
    
    def _extract_traits(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract trait definitions."""
        models = []
        
        for match in re.finditer(self.TRAIT_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract trait body
            trait_start = match.end()
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
            
            trait_body = content[trait_start:trait_end]
            fields = self._extract_properties(trait_body)
            methods = self._extract_methods(trait_body)
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.TRAIT,
                file=file_path,
                line=line,
                fields=fields,
                methods=methods,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_properties(self, body: str) -> list[ExtractedField]:
        """Extract class properties."""
        fields = []
        
        # Try typed properties first (PHP 7.4+)
        for match in re.finditer(self.TYPED_PROPERTY_PATTERN, body):
            prop_type = match.group(1)
            prop_name = match.group(2).lstrip('$')
            default = match.group(3)
            
            fields.append(ExtractedField(
                name=prop_name,
                type=prop_type,
                default=default.strip() if default else None,
            ))
        
        # Fall back to untyped properties
        for match in re.finditer(self.PROPERTY_PATTERN, body):
            prop_name = match.group(1).lstrip('$')
            default = match.group(2)
            
            # Skip if already found as typed
            if any(f.name == prop_name for f in fields):
                continue
            
            fields.append(ExtractedField(
                name=prop_name,
                type="mixed",
                default=default.strip() if default else None,
            ))
        
        return fields
    
    def _extract_methods(self, body: str) -> list[str]:
        """Extract method signatures."""
        methods = []
        
        for match in re.finditer(self.METHOD_PATTERN, body):
            method_name = match.group(1)
            params = match.group(2)
            methods.append(f"{method_name}({params})")
        
        return methods
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """Extract API endpoints from controllers and routes."""
        endpoints = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Check if this is a controller
            is_controller = "_Controller" in content or "Controller" in file_path.name
            
            if is_controller:
                # Extract controller actions
                endpoints.extend(self._extract_controller_actions(content, rel_path))
                
                # Extract Kohana REST validation rules (these define the REST API)
                endpoints.extend(self._extract_kohana_rest_endpoints(content, rel_path))
                
                # Extract __call switch-case patterns (common in Kohana REST controllers)
                endpoints.extend(self._extract_call_switch_endpoints(content, rel_path))
            
            # Also check for route definitions
            endpoints.extend(self._extract_routes(content, rel_path))
        
        return endpoints
    
    def _extract_controller_actions(self, content: str, file_path: str) -> list[ExtractedEndpoint]:
        """Extract action methods from controllers."""
        endpoints = []
        
        # Extract controller name
        controller_match = re.search(r'class\s+(\w+)_Controller', content)
        controller_name = controller_match.group(1).lower() if controller_match else "unknown"
        
        lines = content.split('\n')
        
        for pattern in self.CONTROLLER_ACTION_PATTERNS:
            for i, line in enumerate(lines):
                for match in re.finditer(pattern, line):
                    groups = match.groups()
                    
                    if len(groups) >= 2:
                        method_name = groups[0]
                        action = groups[1]
                    else:
                        method_name = groups[0]
                        action = groups[0]
                    
                    # Determine HTTP method from action name
                    http_method = "GET"
                    if method_name.startswith("post") or action in ("create", "store"):
                        http_method = "POST"
                    elif method_name.startswith("put") or action == "update":
                        http_method = "PUT"
                    elif method_name.startswith("delete") or action == "destroy":
                        http_method = "DELETE"
                    elif method_name.startswith("patch"):
                        http_method = "PATCH"
                    
                    # Construct path based on controller/action
                    path = f"/{controller_name}/{action}"
                    
                    endpoints.append(ExtractedEndpoint(
                        method=http_method,
                        path=path,
                        file=file_path,
                        line=i + 1,
                        handler=method_name,
                        github_url=self.github_link(file_path, i + 1),
                    ))
        
        return endpoints
    
    def _extract_kohana_rest_endpoints(self, content: str, file_path: str) -> list[ExtractedEndpoint]:
        """Extract REST endpoints from Kohana validation rules arrays.
        
        Parses patterns like:
            self::$_validationRules = array(
                'endpoint_name' => array(
                    'get' => array(...),
                    'post' => array(...),
                ),
                ...
            );
        """
        endpoints = []
        
        # Extract controller name
        controller_match = re.search(r'class\s+(\w+)_Controller', content)
        controller_name = controller_match.group(1).lower() if controller_match else "unknown"
        
        # First, find the $_validationRules array specifically
        validation_rules_match = re.search(
            r'self::\$_validationRules\s*=\s*array\s*\(',
            content
        )
        
        if not validation_rules_match:
            return endpoints
        
        # Find the closing of the validation rules array using bracket matching
        start_pos = validation_rules_match.end()
        paren_count = 1
        validation_rules_end = start_pos
        
        for i, char in enumerate(content[start_pos:]):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    validation_rules_end = start_pos + i
                    break
        
        validation_rules_content = content[start_pos:validation_rules_end]
        base_line = content[:validation_rules_match.start()].count('\n') + 1
        
        # Use a state machine approach to track nesting level
        # Level 0: inside the main $_validationRules array
        # Level 1: inside an entity array (e.g., 'provisioning' => array(...))
        # Level 2: inside a method array (e.g., 'get' => array(...))
        
        pos = 0
        current_level = 0
        current_entity = None
        current_entity_line = 0
        found_endpoints = {}  # entity -> set of methods
        
        while pos < len(validation_rules_content):
            char = validation_rules_content[pos]
            
            # Track array nesting
            if char == '(':
                current_level += 1
                pos += 1
                continue
            elif char == ')':
                current_level -= 1
                pos += 1
                continue
            
            # Look for key => array patterns
            # At level 0, these are entity names
            # At level 1, these are HTTP methods
            key_match = re.match(r"'(\w+)'\s*=>\s*array\s*\(", validation_rules_content[pos:])
            
            if key_match:
                key_name = key_match.group(1).lower()
                key_line = validation_rules_content[:pos].count('\n')
                
                if current_level == 0:
                    # This is an entity name (endpoint)
                    current_entity = key_name
                    current_entity_line = base_line + key_line
                    if current_entity not in found_endpoints:
                        found_endpoints[current_entity] = {'line': current_entity_line, 'methods': set()}
                    
                elif current_level == 1 and current_entity:
                    # This is an HTTP method
                    if key_name in ['get', 'post', 'put', 'delete', 'patch']:
                        found_endpoints[current_entity]['methods'].add(key_name)
                
                # Skip past the matched portion but not the opening paren (handled above)
                pos += len(key_match.group(0)) - 1  # -1 because we don't want to skip the (
                continue
            
            pos += 1
        
        # Generate endpoints from what we found
        for entity, data in found_endpoints.items():
            for method in data['methods']:
                path = f"/{controller_name}/{entity}"
                endpoints.append(ExtractedEndpoint(
                    method=method.upper(),
                    path=path,
                    file=file_path,
                    line=data['line'],
                    handler=f"{entity}_{method}",
                    decorators=["kohana_rest"],
                    github_url=self.github_link(file_path, data['line']),
                ))
        
        return endpoints
    
    def _extract_call_switch_endpoints(self, content: str, file_path: str) -> list[ExtractedEndpoint]:
        """Extract endpoints from __call method switch-case patterns.
        
        Parses patterns like:
            public function __call($entity, $params) {
                switch(strtolower($entity)) {
                    case 'users':
                        switch($this->method) {
                            case "get": ...
                            case "post": ...
                        }
                        break;
                }
            }
        """
        endpoints = []
        
        # Skip if we already found validation rules (to avoid duplicates)
        if 'self::$_validationRules' in content:
            return endpoints
        
        # Extract controller name
        controller_match = re.search(r'class\s+(\w+)_Controller', content)
        controller_name = controller_match.group(1).lower() if controller_match else "unknown"
        
        # Find __call method
        call_match = re.search(
            r'function\s+__call\s*\(\s*\$(\w+)',
            content
        )
        
        if not call_match:
            return endpoints
        
        # Find the switch on entity
        switch_entity_match = re.search(
            r'switch\s*\(\s*(?:strtolower\s*\(\s*)?\$(?:entity|' + call_match.group(1) + r')',
            content[call_match.end():]
        )
        
        if not switch_entity_match:
            return endpoints
        
        # Extract all case statements for entities
        case_pattern = r"case\s+['\"](\w+)['\"]"
        method_pattern = r"case\s+['\"]?(get|post|put|delete|patch)['\"]?"
        
        lines = content.split('\n')
        current_entity = None
        current_entity_line = 0
        found_endpoints = {}  # entity -> {'line': N, 'methods': set()}
        in_entity_switch = False
        
        for line_idx, line in enumerate(lines):
            stripped = line.strip().lower()
            
            # Look for entity case
            entity_match = re.search(case_pattern, line, re.IGNORECASE)
            if entity_match:
                entity_name = entity_match.group(1).lower()
                # Skip internal/meta entities
                if entity_name not in ['default', 'true', 'false', '1', '0']:
                    current_entity = entity_name
                    current_entity_line = line_idx + 1
                    if current_entity not in found_endpoints:
                        found_endpoints[current_entity] = {'line': current_entity_line, 'methods': set()}
            
            # Look for method cases within entity context
            if current_entity:
                method_match = re.search(method_pattern, stripped)
                if method_match:
                    method = method_match.group(1).lower()
                    found_endpoints[current_entity]['methods'].add(method)
        
        # Generate endpoints from what we found
        for entity, data in found_endpoints.items():
            # Filter out likely internal methods/entities
            if entity in ['index'] and not data['methods']:
                continue
            
            methods = data['methods'] if data['methods'] else {'get'}  # Default to GET
            for method in methods:
                path = f"/{controller_name}/{entity}"
                endpoints.append(ExtractedEndpoint(
                    method=method.upper(),
                    path=path,
                    file=file_path,
                    line=data['line'],
                    handler=f"{entity}_{method}",
                    decorators=["kohana_call"],
                    github_url=self.github_link(file_path, data['line']),
                ))
        
        return endpoints
    
    def _extract_routes(self, content: str, file_path: str) -> list[ExtractedEndpoint]:
        """Extract route definitions."""
        endpoints = []
        lines = content.split('\n')
        
        for pattern in self.ROUTE_PATTERNS:
            for i, line in enumerate(lines):
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    groups = match.groups()
                    
                    if len(groups) >= 2:
                        method = groups[0].upper()
                        path = groups[1]
                    else:
                        method = "ANY"
                        path = groups[0]
                    
                    endpoints.append(ExtractedEndpoint(
                        method=method,
                        path=path,
                        file=file_path,
                        line=i + 1,
                        github_url=self.github_link(file_path, i + 1),
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
        """Extract environment variable and config usage."""
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
                        config_key = match.group(1)
                        
                        if config_key not in seen:
                            seen.add(config_key)
                            
                            # Determine source type
                            source = "config"
                            if "$_ENV" in line or "getenv" in line or "env(" in line:
                                source = "env"
                            elif "$_SERVER" in line:
                                source = "server"
                            
                            configs.append(ExtractedConfig(
                                key=config_key,
                                source=source,
                                file=rel_path,
                                line=i + 1,
                                github_url=self.github_link(rel_path, i + 1),
                            ))
        
        return configs
    
    def extract_dependencies(self) -> list[ExtractedDependency]:
        """Extract dependencies from composer.json."""
        dependencies = []
        
        composer_json = self.repo_path / "composer.json"
        if not composer_json.exists():
            return dependencies
        
        content = self.read_file(composer_json)
        if not content:
            return dependencies
        
        import json
        try:
            data = json.loads(content)
            
            # Extract require dependencies
            for name, version in data.get("require", {}).items():
                if not name.startswith("php"):
                    dependencies.append(ExtractedDependency(
                        name=name,
                        version=version,
                        file="composer.json",
                    ))
            
            # Extract require-dev dependencies
            for name, version in data.get("require-dev", {}).items():
                dependencies.append(ExtractedDependency(
                    name=name,
                    version=version,
                    file="composer.json",
                ))
        except json.JSONDecodeError:
            pass
        
        return dependencies
