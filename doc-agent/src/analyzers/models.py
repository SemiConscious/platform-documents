"""
Shared data models for code analyzers.

These models represent the extracted information from source code
across all supported programming languages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ModelType(Enum):
    """Types of data models that can be extracted."""
    CLASS = "class"
    STRUCT = "struct"
    INTERFACE = "interface"
    TYPE_ALIAS = "type_alias"
    ENUM = "enum"
    TRAIT = "trait"
    PROTOCOL = "protocol"
    DATACLASS = "dataclass"
    PYDANTIC = "pydantic"
    SCHEMA = "schema"


class SideEffectCategory(Enum):
    """Categories of side effects."""
    DATABASE = "database"
    HTTP = "http"
    FILE = "file"
    QUEUE = "queue"
    CACHE = "cache"
    EMAIL = "email"
    NOTIFICATION = "notification"
    EXTERNAL_API = "external_api"
    CLOUD_SERVICE = "cloud_service"


@dataclass
class ExtractedField:
    """A field/property within a data model."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Optional[str] = None
    tags: Optional[str] = None  # Go struct tags, decorators, etc.


@dataclass
class ExtractedModel:
    """
    A data model extracted from source code.
    
    Represents classes, structs, interfaces, types, etc.
    """
    name: str
    model_type: ModelType
    file: str
    line: int
    fields: list[ExtractedField] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    description: Optional[str] = None
    parent: Optional[str] = None  # Inheritance/extends
    implements: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    github_url: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.model_type.value,
            "file": self.file,
            "line": self.line,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "description": f.description,
                    "required": f.required,
                    "default": f.default,
                    "tags": f.tags,
                }
                for f in self.fields
            ],
            "methods": self.methods,
            "description": self.description,
            "parent": self.parent,
            "implements": self.implements,
            "decorators": self.decorators,
            "github_url": self.github_url,
        }


@dataclass
class ExtractedEndpoint:
    """
    An API endpoint extracted from source code.
    
    Represents HTTP routes, GraphQL resolvers, RPC methods, etc.
    """
    method: str  # GET, POST, PUT, DELETE, QUERY, MUTATION, etc.
    path: str
    file: str
    line: int
    handler: Optional[str] = None  # Function/method name
    description: Optional[str] = None
    parameters: list[dict[str, Any]] = field(default_factory=list)
    response_type: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    github_url: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "method": self.method,
            "path": self.path,
            "file": self.file,
            "line": self.line,
            "handler": self.handler,
            "description": self.description,
            "parameters": self.parameters,
            "response_type": self.response_type,
            "decorators": self.decorators,
            "github_url": self.github_url,
        }


@dataclass
class ExtractedSideEffect:
    """
    A side effect extracted from source code.
    
    Represents database queries, HTTP calls, file operations, etc.
    """
    category: SideEffectCategory
    operation: str  # SELECT, INSERT, GET, POST, READ, WRITE, etc.
    target: Optional[str] = None  # Table name, URL, file path, etc.
    file: str = ""
    line: int = 0
    description: Optional[str] = None
    github_url: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "operation": self.operation,
            "target": self.target,
            "file": self.file,
            "line": self.line,
            "description": self.description,
            "github_url": self.github_url,
        }


@dataclass
class ExtractedConfig:
    """
    Configuration extracted from source code.
    
    Represents environment variables, config keys, constants, etc.
    """
    key: str
    source: str  # env, file, constant, etc.
    file: str
    line: int
    default: Optional[str] = None
    description: Optional[str] = None
    required: bool = False
    github_url: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "source": self.source,
            "file": self.file,
            "line": self.line,
            "default": self.default,
            "description": self.description,
            "required": self.required,
            "github_url": self.github_url,
        }


@dataclass
class ExtractedDependency:
    """
    A dependency/import extracted from source code.
    """
    name: str
    version: Optional[str] = None
    import_path: Optional[str] = None
    file: str = ""
    line: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "import_path": self.import_path,
            "file": self.file,
            "line": self.line,
        }


@dataclass
class AnalysisResult:
    """
    Complete analysis result from a language analyzer.
    """
    language: str
    models: list[ExtractedModel] = field(default_factory=list)
    endpoints: list[ExtractedEndpoint] = field(default_factory=list)
    side_effects: list[ExtractedSideEffect] = field(default_factory=list)
    config: list[ExtractedConfig] = field(default_factory=list)
    dependencies: list[ExtractedDependency] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "language": self.language,
            "models": [m.to_dict() for m in self.models],
            "endpoints": [e.to_dict() for e in self.endpoints],
            "side_effects": [s.to_dict() for s in self.side_effects],
            "config": [c.to_dict() for c in self.config],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "errors": self.errors,
        }
    
    def merge(self, other: "AnalysisResult") -> "AnalysisResult":
        """Merge another analysis result into this one."""
        return AnalysisResult(
            language=f"{self.language}+{other.language}" if self.language != other.language else self.language,
            models=self.models + other.models,
            endpoints=self.endpoints + other.endpoints,
            side_effects=self.side_effects + other.side_effects,
            config=self.config + other.config,
            dependencies=self.dependencies + other.dependencies,
            errors=self.errors + other.errors,
        )
