"""OpenAPI/Swagger specification parser for extracting API details."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum

import yaml

logger = logging.getLogger("doc-agent.parsers.openapi")


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


@dataclass
class OpenAPIParameter:
    """An OpenAPI parameter."""
    name: str
    location: str  # path, query, header, cookie
    param_type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    enum: list[str] = field(default_factory=list)
    example: Optional[Any] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "in": self.location,
            "type": self.param_type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "enum": self.enum if self.enum else None,
            "example": self.example,
        }


@dataclass
class OpenAPIResponse:
    """An OpenAPI response definition."""
    status_code: str
    description: str
    schema: Optional[dict[str, Any]] = None
    examples: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "description": self.description,
            "schema": self.schema,
            "examples": self.examples if self.examples else None,
            "headers": self.headers if self.headers else None,
        }


@dataclass
class OpenAPIRequestBody:
    """An OpenAPI request body."""
    description: Optional[str] = None
    required: bool = False
    content_types: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "required": self.required,
            "content": self.content_types,
        }


@dataclass
class OpenAPIEndpoint:
    """An OpenAPI endpoint/operation."""
    path: str
    method: HTTPMethod
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    parameters: list[OpenAPIParameter] = field(default_factory=list)
    request_body: Optional[OpenAPIRequestBody] = None
    responses: list[OpenAPIResponse] = field(default_factory=list)
    security: list[dict[str, list[str]]] = field(default_factory=list)
    deprecated: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method.value,
            "operation_id": self.operation_id,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_body": self.request_body.to_dict() if self.request_body else None,
            "responses": [r.to_dict() for r in self.responses],
            "security": self.security if self.security else None,
            "deprecated": self.deprecated,
        }


@dataclass
class OpenAPISchema:
    """An OpenAPI schema/model definition."""
    name: str
    schema_type: str  # object, array, string, etc.
    description: Optional[str] = None
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    enum: list[str] = field(default_factory=list)
    items: Optional[dict[str, Any]] = None  # For array types
    all_of: list[dict[str, Any]] = field(default_factory=list)
    one_of: list[dict[str, Any]] = field(default_factory=list)
    example: Optional[Any] = None
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "type": self.schema_type,
            "description": self.description,
        }
        if self.properties:
            result["properties"] = self.properties
        if self.required:
            result["required"] = self.required
        if self.enum:
            result["enum"] = self.enum
        if self.items:
            result["items"] = self.items
        if self.all_of:
            result["allOf"] = self.all_of
        if self.one_of:
            result["oneOf"] = self.one_of
        if self.example is not None:
            result["example"] = self.example
        return result


@dataclass
class OpenAPISecurityScheme:
    """An OpenAPI security scheme."""
    name: str
    scheme_type: str  # apiKey, http, oauth2, openIdConnect
    description: Optional[str] = None
    location: Optional[str] = None  # For apiKey: header, query, cookie
    scheme: Optional[str] = None  # For http: bearer, basic
    bearer_format: Optional[str] = None
    flows: Optional[dict[str, Any]] = None  # For oauth2
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.scheme_type,
            "description": self.description,
            "in": self.location,
            "scheme": self.scheme,
            "bearer_format": self.bearer_format,
            "flows": self.flows,
        }


@dataclass
class OpenAPISpec:
    """A complete OpenAPI specification."""
    title: str
    version: str
    openapi_version: str = "3.0.0"
    description: Optional[str] = None
    servers: list[dict[str, str]] = field(default_factory=list)
    endpoints: list[OpenAPIEndpoint] = field(default_factory=list)
    schemas: list[OpenAPISchema] = field(default_factory=list)
    security_schemes: list[OpenAPISecurityScheme] = field(default_factory=list)
    tags: list[dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "version": self.version,
            "openapi_version": self.openapi_version,
            "description": self.description,
            "servers": self.servers,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "schemas": [s.to_dict() for s in self.schemas],
            "security_schemes": [s.to_dict() for s in self.security_schemes],
            "tags": self.tags,
        }
    
    @property
    def endpoint_count(self) -> int:
        return len(self.endpoints)
    
    @property
    def schema_count(self) -> int:
        return len(self.schemas)
    
    def get_endpoints_by_tag(self, tag: str) -> list[OpenAPIEndpoint]:
        """Get all endpoints with a specific tag."""
        return [e for e in self.endpoints if tag in e.tags]


class OpenAPIParser:
    """
    Parser for OpenAPI 3.x and Swagger 2.0 specifications.
    
    Extracts endpoints, schemas, and security schemes from OpenAPI specs.
    """
    
    def __init__(self):
        self.spec: Optional[OpenAPISpec] = None
        self._raw_spec: dict[str, Any] = {}
    
    def parse(self, content: str, format: str = "auto") -> OpenAPISpec:
        """
        Parse OpenAPI/Swagger content and return a spec object.
        
        Args:
            content: OpenAPI spec content as a string
            format: "json", "yaml", or "auto" (detect from content)
            
        Returns:
            OpenAPISpec object with all parsed details
        """
        # Parse content
        if format == "auto":
            format = self._detect_format(content)
        
        if format == "json":
            self._raw_spec = json.loads(content)
        else:
            self._raw_spec = yaml.safe_load(content)
        
        # Determine OpenAPI version
        is_swagger = "swagger" in self._raw_spec
        openapi_version = self._raw_spec.get("openapi", self._raw_spec.get("swagger", "3.0.0"))
        
        # Parse info section
        info = self._raw_spec.get("info", {})
        
        self.spec = OpenAPISpec(
            title=info.get("title", "Unknown API"),
            version=info.get("version", "1.0.0"),
            openapi_version=openapi_version,
            description=info.get("description"),
            servers=self._parse_servers(is_swagger),
            tags=self._raw_spec.get("tags", []),
        )
        
        # Parse components/definitions
        self._parse_schemas(is_swagger)
        
        # Parse security schemes
        self._parse_security_schemes(is_swagger)
        
        # Parse paths/endpoints
        self._parse_endpoints(is_swagger)
        
        logger.info(
            f"Parsed OpenAPI spec: {self.spec.endpoint_count} endpoints, "
            f"{self.spec.schema_count} schemas"
        )
        
        return self.spec
    
    def parse_file(self, filepath: str) -> OpenAPISpec:
        """Parse an OpenAPI spec from a file path."""
        with open(filepath, "r") as f:
            content = f.read()
        format = "json" if filepath.endswith(".json") else "yaml"
        return self.parse(content, format)
    
    def _detect_format(self, content: str) -> str:
        """Detect if content is JSON or YAML."""
        content = content.strip()
        if content.startswith("{"):
            return "json"
        return "yaml"
    
    def _parse_servers(self, is_swagger: bool) -> list[dict[str, str]]:
        """Parse server definitions."""
        if is_swagger:
            # Swagger 2.0 uses host, basePath, schemes
            host = self._raw_spec.get("host", "")
            base_path = self._raw_spec.get("basePath", "")
            schemes = self._raw_spec.get("schemes", ["https"])
            
            if host:
                return [{"url": f"{schemes[0]}://{host}{base_path}"}]
            return []
        else:
            # OpenAPI 3.x uses servers array
            return self._raw_spec.get("servers", [])
    
    def _parse_schemas(self, is_swagger: bool) -> None:
        """Parse schema/model definitions."""
        if is_swagger:
            schemas_dict = self._raw_spec.get("definitions", {})
        else:
            components = self._raw_spec.get("components", {})
            schemas_dict = components.get("schemas", {})
        
        for name, schema_data in schemas_dict.items():
            schema = self._parse_schema(name, schema_data)
            self.spec.schemas.append(schema)
    
    def _parse_schema(self, name: str, data: dict[str, Any]) -> OpenAPISchema:
        """Parse a single schema definition."""
        schema_type = data.get("type", "object")
        
        # Handle allOf, oneOf, anyOf
        all_of = data.get("allOf", [])
        one_of = data.get("oneOf", [])
        
        # Parse properties with their types and descriptions
        properties = {}
        for prop_name, prop_data in data.get("properties", {}).items():
            properties[prop_name] = {
                "type": self._get_property_type(prop_data),
                "description": prop_data.get("description"),
                "required": prop_name in data.get("required", []),
                "enum": prop_data.get("enum"),
                "format": prop_data.get("format"),
                "example": prop_data.get("example"),
            }
        
        return OpenAPISchema(
            name=name,
            schema_type=schema_type,
            description=data.get("description"),
            properties=properties,
            required=data.get("required", []),
            enum=data.get("enum", []),
            items=data.get("items"),
            all_of=all_of,
            one_of=one_of,
            example=data.get("example"),
        )
    
    def _get_property_type(self, prop_data: dict[str, Any]) -> str:
        """Get a readable type string for a property."""
        if "$ref" in prop_data:
            # Reference to another schema
            ref = prop_data["$ref"]
            return ref.split("/")[-1]
        
        prop_type = prop_data.get("type", "any")
        
        if prop_type == "array":
            items = prop_data.get("items", {})
            if "$ref" in items:
                item_type = items["$ref"].split("/")[-1]
            else:
                item_type = items.get("type", "any")
            return f"array[{item_type}]"
        
        format_str = prop_data.get("format")
        if format_str:
            return f"{prop_type}({format_str})"
        
        return prop_type
    
    def _parse_security_schemes(self, is_swagger: bool) -> None:
        """Parse security scheme definitions."""
        if is_swagger:
            schemes_dict = self._raw_spec.get("securityDefinitions", {})
        else:
            components = self._raw_spec.get("components", {})
            schemes_dict = components.get("securitySchemes", {})
        
        for name, scheme_data in schemes_dict.items():
            scheme = OpenAPISecurityScheme(
                name=name,
                scheme_type=scheme_data.get("type", ""),
                description=scheme_data.get("description"),
                location=scheme_data.get("in"),
                scheme=scheme_data.get("scheme"),
                bearer_format=scheme_data.get("bearerFormat"),
                flows=scheme_data.get("flows"),
            )
            self.spec.security_schemes.append(scheme)
    
    def _parse_endpoints(self, is_swagger: bool) -> None:
        """Parse path/endpoint definitions."""
        paths = self._raw_spec.get("paths", {})
        
        for path, path_data in paths.items():
            # Get path-level parameters
            path_params = path_data.get("parameters", [])
            
            for method in ["get", "post", "put", "patch", "delete", "options", "head"]:
                if method in path_data:
                    operation = path_data[method]
                    endpoint = self._parse_endpoint(path, method, operation, path_params, is_swagger)
                    self.spec.endpoints.append(endpoint)
    
    def _parse_endpoint(
        self,
        path: str,
        method: str,
        operation: dict[str, Any],
        path_params: list[dict],
        is_swagger: bool,
    ) -> OpenAPIEndpoint:
        """Parse a single endpoint/operation."""
        # Parse parameters (combine path-level and operation-level)
        all_params = path_params + operation.get("parameters", [])
        parameters = [self._parse_parameter(p, is_swagger) for p in all_params]
        
        # Parse request body
        request_body = None
        if is_swagger:
            # Swagger 2.0: body parameter
            body_params = [p for p in all_params if p.get("in") == "body"]
            if body_params:
                request_body = OpenAPIRequestBody(
                    description=body_params[0].get("description"),
                    required=body_params[0].get("required", False),
                    content_types={"application/json": {"schema": body_params[0].get("schema", {})}},
                )
            # Remove body params from parameters list
            parameters = [p for p in parameters if p.location != "body"]
        else:
            # OpenAPI 3.x: requestBody
            if "requestBody" in operation:
                rb = operation["requestBody"]
                request_body = OpenAPIRequestBody(
                    description=rb.get("description"),
                    required=rb.get("required", False),
                    content_types=rb.get("content", {}),
                )
        
        # Parse responses
        responses = []
        for status, response_data in operation.get("responses", {}).items():
            response = self._parse_response(status, response_data, is_swagger)
            responses.append(response)
        
        return OpenAPIEndpoint(
            path=path,
            method=HTTPMethod(method.upper()),
            operation_id=operation.get("operationId"),
            summary=operation.get("summary"),
            description=operation.get("description"),
            tags=operation.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            security=operation.get("security", []),
            deprecated=operation.get("deprecated", False),
        )
    
    def _parse_parameter(self, param: dict[str, Any], is_swagger: bool) -> OpenAPIParameter:
        """Parse a single parameter."""
        # Get type information
        if is_swagger:
            param_type = param.get("type", "string")
            if param_type == "array":
                items = param.get("items", {})
                param_type = f"array[{items.get('type', 'string')}]"
        else:
            schema = param.get("schema", {})
            param_type = self._get_property_type(schema)
        
        return OpenAPIParameter(
            name=param.get("name", ""),
            location=param.get("in", "query"),
            param_type=param_type,
            description=param.get("description"),
            required=param.get("required", False),
            default=param.get("default"),
            enum=param.get("enum", []),
            example=param.get("example"),
        )
    
    def _parse_response(
        self,
        status: str,
        data: dict[str, Any],
        is_swagger: bool,
    ) -> OpenAPIResponse:
        """Parse a response definition."""
        schema = None
        examples = {}
        
        if is_swagger:
            schema = data.get("schema")
            examples = data.get("examples", {})
        else:
            content = data.get("content", {})
            # Get first content type schema
            for content_type, content_data in content.items():
                if "schema" in content_data:
                    schema = content_data["schema"]
                if "examples" in content_data:
                    examples = content_data["examples"]
                break
        
        return OpenAPIResponse(
            status_code=status,
            description=data.get("description", ""),
            schema=schema,
            examples=examples,
            headers=data.get("headers", {}),
        )
