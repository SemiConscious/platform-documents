"""GraphQL schema parser for extracting types, queries, and mutations."""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

logger = logging.getLogger("doc-agent.parsers.graphql")


class GraphQLTypeKind(str, Enum):
    """Types of GraphQL definitions."""
    SCALAR = "scalar"
    OBJECT = "type"
    INTERFACE = "interface"
    UNION = "union"
    ENUM = "enum"
    INPUT = "input"
    QUERY = "Query"
    MUTATION = "Mutation"
    SUBSCRIPTION = "Subscription"


@dataclass
class GraphQLArgument:
    """A GraphQL field argument."""
    name: str
    type: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required,
        }


@dataclass
class GraphQLField:
    """A field in a GraphQL type."""
    name: str
    type: str
    description: Optional[str] = None
    arguments: list[GraphQLArgument] = field(default_factory=list)
    deprecated: bool = False
    deprecation_reason: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "deprecated": self.deprecated,
            "deprecation_reason": self.deprecation_reason,
        }


@dataclass
class GraphQLEnumValue:
    """A value in a GraphQL enum."""
    name: str
    description: Optional[str] = None
    deprecated: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "deprecated": self.deprecated,
        }


@dataclass
class GraphQLType:
    """A GraphQL type definition."""
    name: str
    kind: GraphQLTypeKind
    description: Optional[str] = None
    fields: list[GraphQLField] = field(default_factory=list)
    enum_values: list[GraphQLEnumValue] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    possible_types: list[str] = field(default_factory=list)  # For unions
    directives: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "kind": self.kind.value if isinstance(self.kind, GraphQLTypeKind) else self.kind,
            "description": self.description,
            "directives": self.directives,
        }
        if self.fields:
            result["fields"] = [f.to_dict() for f in self.fields]
        if self.enum_values:
            result["enum_values"] = [v.to_dict() for v in self.enum_values]
        if self.interfaces:
            result["interfaces"] = self.interfaces
        if self.possible_types:
            result["possible_types"] = self.possible_types
        return result


@dataclass
class GraphQLSchema:
    """A complete GraphQL schema."""
    types: list[GraphQLType] = field(default_factory=list)
    queries: list[GraphQLField] = field(default_factory=list)
    mutations: list[GraphQLField] = field(default_factory=list)
    subscriptions: list[GraphQLField] = field(default_factory=list)
    directives: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "types": [t.to_dict() for t in self.types],
            "queries": [q.to_dict() for q in self.queries],
            "mutations": [m.to_dict() for m in self.mutations],
            "subscriptions": [s.to_dict() for s in self.subscriptions],
            "directives": self.directives,
        }
    
    @property
    def type_count(self) -> int:
        return len(self.types)
    
    @property
    def query_count(self) -> int:
        return len(self.queries)
    
    @property
    def mutation_count(self) -> int:
        return len(self.mutations)


class GraphQLParser:
    """
    Parser for GraphQL Schema Definition Language (SDL).
    
    Extracts types, queries, mutations, and subscriptions from .graphql files.
    """
    
    # Regex patterns for parsing
    DESCRIPTION_PATTERN = re.compile(r'"""([\s\S]*?)"""|"([^"]*)"')
    TYPE_PATTERN = re.compile(
        r'(?:"""[\s\S]*?"""\s*)?'  # Optional description
        r'(type|interface|input|enum|union|scalar)\s+'
        r'(\w+)'  # Type name
        r'(?:\s+implements\s+([\w\s,&]+))?'  # Optional interfaces
        r'(?:\s*@\w+(?:\([^)]*\))?)*'  # Optional directives
        r'\s*\{([^}]*)\}',  # Body
        re.MULTILINE
    )
    FIELD_PATTERN = re.compile(
        r'(?:"""([\s\S]*?)"""\s*)?'  # Optional description
        r'"?([^"\n]*)"?\s*'  # Inline description (optional)
        r'(\w+)'  # Field name
        r'(?:\(([^)]*)\))?'  # Optional arguments
        r'\s*:\s*'
        r'([\w\[\]!]+)'  # Return type
        r'(?:\s*@(\w+)(?:\(([^)]*)\))?)?',  # Optional directive
        re.MULTILINE
    )
    ARGUMENT_PATTERN = re.compile(
        r'(\w+)\s*:\s*([\w\[\]!]+)(?:\s*=\s*([^\s,)]+))?'
    )
    ENUM_VALUE_PATTERN = re.compile(
        r'(?:"""([\s\S]*?)"""\s*)?'  # Optional description
        r'(\w+)'  # Value name
        r'(?:\s*@deprecated(?:\(reason:\s*"([^"]*)"\))?)?',  # Optional deprecation
        re.MULTILINE
    )
    UNION_PATTERN = re.compile(
        r'(?:"""[\s\S]*?"""\s*)?'
        r'union\s+(\w+)\s*=\s*([\w\s|]+)',
        re.MULTILINE
    )
    EXTEND_TYPE_PATTERN = re.compile(
        r'extend\s+(type|input)\s+(\w+)\s*\{([^}]*)\}',
        re.MULTILINE
    )
    
    def __init__(self):
        self.schema = GraphQLSchema()
        self._type_map: dict[str, GraphQLType] = {}
    
    def parse(self, content: str) -> GraphQLSchema:
        """
        Parse GraphQL SDL content and return a schema object.
        
        Args:
            content: GraphQL SDL content as a string
            
        Returns:
            GraphQLSchema object with all parsed types
        """
        self.schema = GraphQLSchema()
        self._type_map = {}
        
        # Remove comments (but keep descriptions)
        content = self._remove_comments(content)
        
        # Parse unions first (they have different syntax)
        self._parse_unions(content)
        
        # Parse all type definitions
        self._parse_types(content)
        
        # Parse extended types
        self._parse_extensions(content)
        
        # Extract Query, Mutation, Subscription operations
        self._extract_operations()
        
        logger.info(
            f"Parsed GraphQL schema: {self.schema.type_count} types, "
            f"{self.schema.query_count} queries, {self.schema.mutation_count} mutations"
        )
        
        return self.schema
    
    def parse_multiple(self, contents: list[str]) -> GraphQLSchema:
        """
        Parse multiple GraphQL files and merge them into one schema.
        
        Args:
            contents: List of GraphQL SDL content strings
            
        Returns:
            Merged GraphQLSchema object
        """
        combined = "\n\n".join(contents)
        return self.parse(combined)
    
    def _remove_comments(self, content: str) -> str:
        """Remove single-line comments but preserve descriptions."""
        lines = []
        for line in content.split("\n"):
            # Remove # comments that aren't in strings
            if "#" in line:
                # Simple heuristic: remove if not inside quotes
                in_string = False
                result = []
                for i, char in enumerate(line):
                    if char == '"' and (i == 0 or line[i-1] != "\\"):
                        in_string = not in_string
                    if char == "#" and not in_string:
                        break
                    result.append(char)
                line = "".join(result)
            lines.append(line)
        return "\n".join(lines)
    
    def _parse_unions(self, content: str) -> None:
        """Parse union type definitions."""
        for match in self.UNION_PATTERN.finditer(content):
            name = match.group(1)
            members = [m.strip() for m in match.group(2).split("|") if m.strip()]
            
            graphql_type = GraphQLType(
                name=name,
                kind=GraphQLTypeKind.UNION,
                possible_types=members,
            )
            self._type_map[name] = graphql_type
            self.schema.types.append(graphql_type)
    
    def _parse_types(self, content: str) -> None:
        """Parse type, interface, input, enum, and scalar definitions."""
        for match in self.TYPE_PATTERN.finditer(content):
            kind_str = match.group(1)
            name = match.group(2)
            implements = match.group(3)
            body = match.group(4)
            
            # Get description (look backwards from match)
            description = self._extract_description(content, match.start())
            
            # Map kind string to enum
            kind_map = {
                "type": GraphQLTypeKind.OBJECT,
                "interface": GraphQLTypeKind.INTERFACE,
                "input": GraphQLTypeKind.INPUT,
                "enum": GraphQLTypeKind.ENUM,
                "scalar": GraphQLTypeKind.SCALAR,
            }
            kind = kind_map.get(kind_str, GraphQLTypeKind.OBJECT)
            
            # Special handling for Query, Mutation, Subscription
            if name == "Query":
                kind = GraphQLTypeKind.QUERY
            elif name == "Mutation":
                kind = GraphQLTypeKind.MUTATION
            elif name == "Subscription":
                kind = GraphQLTypeKind.SUBSCRIPTION
            
            # Parse interfaces
            interfaces = []
            if implements:
                interfaces = [i.strip() for i in re.split(r'[,&]', implements) if i.strip()]
            
            graphql_type = GraphQLType(
                name=name,
                kind=kind,
                description=description,
                interfaces=interfaces,
            )
            
            # Parse body based on kind
            if kind == GraphQLTypeKind.ENUM:
                graphql_type.enum_values = self._parse_enum_values(body)
            elif kind != GraphQLTypeKind.SCALAR:
                graphql_type.fields = self._parse_fields(body)
            
            self._type_map[name] = graphql_type
            self.schema.types.append(graphql_type)
    
    def _parse_extensions(self, content: str) -> None:
        """Parse extend type definitions and merge with existing types."""
        for match in self.EXTEND_TYPE_PATTERN.finditer(content):
            name = match.group(2)
            body = match.group(3)
            
            if name in self._type_map:
                # Add fields to existing type
                new_fields = self._parse_fields(body)
                self._type_map[name].fields.extend(new_fields)
            else:
                # Create new type from extension
                graphql_type = GraphQLType(
                    name=name,
                    kind=GraphQLTypeKind.OBJECT,
                    fields=self._parse_fields(body),
                )
                self._type_map[name] = graphql_type
                self.schema.types.append(graphql_type)
    
    def _parse_fields(self, body: str) -> list[GraphQLField]:
        """Parse fields from a type body."""
        fields = []
        
        # Split body into lines and process each
        lines = body.strip().split("\n")
        current_description = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for multiline description
            if line.startswith('"""'):
                desc_match = re.search(r'"""([\s\S]*?)"""', line)
                if desc_match:
                    current_description = desc_match.group(1).strip()
                continue
            
            # Parse field
            field_match = re.match(
                r'(\w+)(?:\(([^)]*)\))?\s*:\s*([\w\[\]!]+)(?:\s*@(\w+)(?:\(([^)]*)\))?)?',
                line
            )
            if field_match:
                name = field_match.group(1)
                args_str = field_match.group(2)
                return_type = field_match.group(3)
                directive = field_match.group(4)
                directive_args = field_match.group(5)
                
                # Parse arguments
                arguments = []
                if args_str:
                    arguments = self._parse_arguments(args_str)
                
                # Check for deprecation
                deprecated = directive == "deprecated"
                deprecation_reason = None
                if deprecated and directive_args:
                    reason_match = re.search(r'reason:\s*"([^"]*)"', directive_args)
                    if reason_match:
                        deprecation_reason = reason_match.group(1)
                
                fields.append(GraphQLField(
                    name=name,
                    type=return_type,
                    description=current_description,
                    arguments=arguments,
                    deprecated=deprecated,
                    deprecation_reason=deprecation_reason,
                ))
                current_description = None
        
        return fields
    
    def _parse_arguments(self, args_str: str) -> list[GraphQLArgument]:
        """Parse field arguments."""
        arguments = []
        
        for match in self.ARGUMENT_PATTERN.finditer(args_str):
            name = match.group(1)
            arg_type = match.group(2)
            default_value = match.group(3)
            
            # Check if required (type ends with !)
            required = arg_type.endswith("!") and default_value is None
            
            arguments.append(GraphQLArgument(
                name=name,
                type=arg_type,
                default_value=default_value,
                required=required,
            ))
        
        return arguments
    
    def _parse_enum_values(self, body: str) -> list[GraphQLEnumValue]:
        """Parse enum values from an enum body."""
        values = []
        current_description = None
        
        for line in body.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # Check for description
            if line.startswith('"""'):
                desc_match = re.search(r'"""([\s\S]*?)"""', line)
                if desc_match:
                    current_description = desc_match.group(1).strip()
                continue
            
            # Parse enum value
            match = re.match(r'(\w+)(?:\s*@deprecated(?:\(reason:\s*"([^"]*)"\))?)?', line)
            if match:
                name = match.group(1)
                deprecation_reason = match.group(2)
                
                values.append(GraphQLEnumValue(
                    name=name,
                    description=current_description,
                    deprecated=deprecation_reason is not None or "@deprecated" in line,
                ))
                current_description = None
        
        return values
    
    def _extract_description(self, content: str, position: int) -> Optional[str]:
        """Extract a description comment before a type definition."""
        # Look backwards for a description
        before = content[:position].rstrip()
        
        if before.endswith('"""'):
            # Find the start of the description
            start = before.rfind('"""', 0, len(before) - 3)
            if start != -1:
                return before[start + 3:-3].strip()
        
        return None
    
    def _extract_operations(self) -> None:
        """Extract Query, Mutation, and Subscription operations from types."""
        for type_def in self.schema.types:
            if type_def.kind == GraphQLTypeKind.QUERY or type_def.name == "Query":
                self.schema.queries = type_def.fields
            elif type_def.kind == GraphQLTypeKind.MUTATION or type_def.name == "Mutation":
                self.schema.mutations = type_def.fields
            elif type_def.kind == GraphQLTypeKind.SUBSCRIPTION or type_def.name == "Subscription":
                self.schema.subscriptions = type_def.fields
