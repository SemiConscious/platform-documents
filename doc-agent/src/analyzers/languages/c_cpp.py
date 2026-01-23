"""
C/C++ language analyzer.

Extracts structs, classes, functions, and macros from C and C++ source code.
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


@register_analyzer("c")
@register_analyzer("cpp")
class CCppAnalyzer(BaseLanguageAnalyzer):
    """
    Analyzer for C and C++ source code.
    
    Extracts:
    - Structs and classes
    - Function declarations
    - #define macros
    - File and network operations
    """
    
    language = "cpp"
    extensions = [".c", ".h", ".cpp", ".cxx", ".cc", ".hpp", ".hxx"]
    
    # Type patterns
    STRUCT_PATTERN = r'(?:typedef\s+)?struct\s+(\w+)\s*\{'
    CLASS_PATTERN = r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?\s*\{'
    ENUM_PATTERN = r'enum(?:\s+class)?\s+(\w+)\s*\{'
    
    # Function patterns
    FUNCTION_PATTERN = r'(?:static\s+)?(?:inline\s+)?(?:virtual\s+)?(?:const\s+)?(\w+(?:\s*[*&])?)\s+(\w+)\s*\(([^)]*)\)'
    
    # Macro patterns
    DEFINE_PATTERN = r'#define\s+(\w+)(?:\s*\(([^)]*)\))?\s+(.+)?$'
    
    # File operation patterns
    FILE_PATTERNS = [
        (r'fopen\s*\(', "File Open"),
        (r'fread\s*\(', "File Read"),
        (r'fwrite\s*\(', "File Write"),
        (r'fclose\s*\(', "File Close"),
        (r'fprintf\s*\(', "File Print"),
        (r'fscanf\s*\(', "File Scan"),
    ]
    
    # Network operation patterns
    NETWORK_PATTERNS = [
        (r'socket\s*\(', "Socket Create"),
        (r'connect\s*\(', "Socket Connect"),
        (r'bind\s*\(', "Socket Bind"),
        (r'listen\s*\(', "Socket Listen"),
        (r'accept\s*\(', "Socket Accept"),
        (r'send\s*\(', "Socket Send"),
        (r'recv\s*\(', "Socket Receive"),
        (r'curl_easy_', "cURL"),
    ]
    
    # Memory operation patterns
    MEMORY_PATTERNS = [
        (r'malloc\s*\(', "Memory Alloc"),
        (r'calloc\s*\(', "Memory Calloc"),
        (r'realloc\s*\(', "Memory Realloc"),
        (r'free\s*\(', "Memory Free"),
        (r'new\s+', "C++ New"),
        (r'delete\s+', "C++ Delete"),
    ]
    
    def extract_models(self) -> list[ExtractedModel]:
        """Extract C/C++ structs, classes, and enums."""
        models = []
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
            # Extract structs
            models.extend(self._extract_structs(content, rel_path))
            
            # Extract classes (C++)
            if file_path.suffix in ('.cpp', '.cxx', '.cc', '.hpp', '.hxx'):
                models.extend(self._extract_classes(content, rel_path))
            
            # Extract enums
            models.extend(self._extract_enums(content, rel_path))
        
        return models
    
    def _extract_structs(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract struct definitions."""
        models = []
        
        for match in re.finditer(self.STRUCT_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract struct body
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
            fields = []
            field_pattern = r'(\w+(?:\s*[*&])*)\s+(\w+)(?:\s*\[\d*\])?\s*;'
            for field_match in re.finditer(field_pattern, body):
                fields.append(ExtractedField(
                    name=field_match.group(2),
                    type=field_match.group(1).strip(),
                ))
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.STRUCT,
                file=file_path,
                line=line,
                fields=fields,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_classes(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract C++ class definitions."""
        models = []
        
        for match in re.finditer(self.CLASS_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            parent = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            # Extract class body for methods
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
            
            # Parse methods
            methods = []
            for method_match in re.finditer(self.FUNCTION_PATTERN, body):
                return_type = method_match.group(1)
                method_name = method_match.group(2)
                params = method_match.group(3)
                methods.append(f"{return_type} {method_name}({params})")
            
            models.append(ExtractedModel(
                name=name,
                model_type=ModelType.CLASS,
                file=file_path,
                line=line,
                methods=methods[:15],
                parent=parent,
                github_url=self.github_link(file_path, line),
            ))
        
        return models
    
    def _extract_enums(self, content: str, file_path: str) -> list[ExtractedModel]:
        """Extract enum definitions."""
        models = []
        
        for match in re.finditer(self.ENUM_PATTERN, content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # Extract enum values
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
            
            # Parse values
            fields = []
            for value_match in re.finditer(r'(\w+)(?:\s*=\s*[^,\n]+)?', body):
                value = value_match.group(1)
                if value and not value.startswith('//'):
                    fields.append(ExtractedField(
                        name=value,
                        type="enum_value",
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
    
    def extract_endpoints(self) -> list[ExtractedEndpoint]:
        """C/C++ typically doesn't have HTTP endpoints in the same way."""
        return []
    
    def extract_side_effects(self) -> list[ExtractedSideEffect]:
        """Extract file, network, and memory operations."""
        side_effects = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            
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
            
            # Network operations
            for pattern, operation in self.NETWORK_PATTERNS:
                if re.search(pattern, content):
                    key = ("network", operation)
                    if key not in seen:
                        seen.add(key)
                        side_effects.append(ExtractedSideEffect(
                            category=SideEffectCategory.HTTP,
                            operation=operation,
                            target="Network",
                            file=rel_path,
                            github_url=self.github_link(rel_path),
                        ))
        
        return side_effects
    
    def extract_config(self) -> list[ExtractedConfig]:
        """Extract #define macros and environment variable usage."""
        configs = []
        seen = set()
        
        for file_path in self.find_files():
            content = self.read_file(file_path)
            if not content:
                continue
            
            rel_path = self.relative_path(file_path)
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # #define constants
                define_match = re.match(self.DEFINE_PATTERN, line.strip())
                if define_match:
                    name = define_match.group(1)
                    params = define_match.group(2)
                    value = define_match.group(3)
                    
                    # Skip function-like macros
                    if params is None and name not in seen:
                        seen.add(name)
                        configs.append(ExtractedConfig(
                            key=name,
                            source="define",
                            file=rel_path,
                            line=i + 1,
                            default=value.strip() if value else None,
                            github_url=self.github_link(rel_path, i + 1),
                        ))
                
                # getenv() calls
                for match in re.finditer(r'getenv\s*\(\s*"(\w+)"', line):
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
