"""Entity models for the knowledge graph."""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    SERVICE = "service"
    DOMAIN = "domain"
    API = "api"
    ENDPOINT = "endpoint"
    SCHEMA = "schema"
    DOCUMENT = "document"
    PERSON = "person"
    REPOSITORY = "repository"
    INTEGRATION = "integration"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    BELONGS_TO = "belongs_to"
    CALLS = "calls"
    EXPOSES = "exposes"
    OWNS = "owns"
    DOCUMENTS = "documents"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    IMPLEMENTS = "implements"
    USES = "uses"


class BaseEntity(BaseModel):
    """Base class for all entities in the knowledge graph."""
    id: str
    name: str
    entity_type: EntityType
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode="json")
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEntity":
        """Create from dictionary."""
        return cls(**data)


class Service(BaseEntity):
    """A microservice or application component."""
    entity_type: EntityType = EntityType.SERVICE
    repository: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    status: str = "active"  # active, deprecated, planned
    team: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    documentation_status: str = "pending"  # pending, partial, complete


class Domain(BaseEntity):
    """A logical domain grouping related services."""
    entity_type: EntityType = EntityType.DOMAIN
    services: list[str] = Field(default_factory=list)
    parent_domain: Optional[str] = None
    sub_domains: list[str] = Field(default_factory=list)


class API(BaseEntity):
    """An API exposed by a service."""
    entity_type: EntityType = EntityType.API
    service_id: str
    api_type: str = "rest"  # rest, graphql, grpc, websocket
    version: Optional[str] = None
    base_url: Optional[str] = None
    auth_type: Optional[str] = None
    spec_file: Optional[str] = None
    endpoints: list[str] = Field(default_factory=list)


class Endpoint(BaseEntity):
    """An individual API endpoint."""
    entity_type: EntityType = EntityType.ENDPOINT
    api_id: str
    path: str
    method: str = "GET"
    request_schema: Optional[str] = None
    response_schema: Optional[str] = None
    auth_required: bool = True
    deprecated: bool = False
    examples: list[dict[str, Any]] = Field(default_factory=list)


class Schema(BaseEntity):
    """A data schema (database, event, API, or GraphQL type)."""
    entity_type: EntityType = EntityType.SCHEMA
    # Schema types: database, event, request, response, graphql, openapi
    schema_type: str
    service_id: Optional[str] = None
    definition: Optional[dict[str, Any]] = None
    # Fields with structure: {name, type, description, required, ...}
    fields: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, str]] = Field(default_factory=list)
    # For GraphQL types: type, input, enum, interface, union, scalar
    graphql_kind: Optional[str] = None


class Document(BaseEntity):
    """An existing document from Confluence, GitHub, or Jira."""
    entity_type: EntityType = EntityType.DOCUMENT
    source_type: str  # confluence, github, jira
    url: str
    content: Optional[str] = None
    content_hash: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    linked_services: list[str] = Field(default_factory=list)
    last_modified: Optional[datetime] = None
    # Trust level for source reliability
    trust_level: str = "high"  # high, medium, low, reference
    disclaimer: Optional[str] = None  # Warning message for low-trust content


class Person(BaseEntity):
    """A person (owner, contributor)."""
    entity_type: EntityType = EntityType.PERSON
    email: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    owned_services: list[str] = Field(default_factory=list)


class Repository(BaseEntity):
    """A GitHub repository."""
    entity_type: EntityType = EntityType.REPOSITORY
    url: str
    default_branch: str = "main"
    language: Optional[str] = None
    languages: dict[str, int] = Field(default_factory=dict)
    topics: list[str] = Field(default_factory=list)
    readme_content: Optional[str] = None
    has_ci: bool = False
    has_docs: bool = False
    last_commit: Optional[datetime] = None


class Integration(BaseEntity):
    """A third-party integration."""
    entity_type: EntityType = EntityType.INTEGRATION
    integration_type: str  # salesforce, teams, etc.
    services: list[str] = Field(default_factory=list)
    config_options: dict[str, Any] = Field(default_factory=dict)
    api_mappings: list[dict[str, Any]] = Field(default_factory=list)


class Relation(BaseModel):
    """A relationship between two entities."""
    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode="json")


# Type mapping for deserialization
ENTITY_TYPE_MAP: dict[EntityType, type[BaseEntity]] = {
    EntityType.SERVICE: Service,
    EntityType.DOMAIN: Domain,
    EntityType.API: API,
    EntityType.ENDPOINT: Endpoint,
    EntityType.SCHEMA: Schema,
    EntityType.DOCUMENT: Document,
    EntityType.PERSON: Person,
    EntityType.REPOSITORY: Repository,
    EntityType.INTEGRATION: Integration,
}


def entity_from_dict(data: dict[str, Any]) -> BaseEntity:
    """Create the appropriate entity type from a dictionary."""
    entity_type = EntityType(data.get("entity_type"))
    entity_class = ENTITY_TYPE_MAP.get(entity_type, BaseEntity)
    return entity_class(**data)
