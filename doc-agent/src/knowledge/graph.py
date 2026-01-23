"""Knowledge graph implementation using NetworkX."""

import logging
from typing import Optional, Iterator, Any
from collections import defaultdict

import networkx as nx

from .models import (
    BaseEntity,
    Relation,
    EntityType,
    RelationType,
    entity_from_dict,
    Service,
    Domain,
    API,
)

logger = logging.getLogger("doc-agent.knowledge.graph")


class KnowledgeGraph:
    """
    Knowledge graph for storing and querying platform entities and relationships.
    
    Uses NetworkX for efficient graph operations with support for:
    - Entity storage with typed nodes
    - Relationship tracking with metadata
    - Graph traversal and querying
    - Serialization for persistence
    """
    
    def __init__(self):
        """Initialize an empty knowledge graph."""
        self._graph = nx.DiGraph()
        self._entities: dict[str, BaseEntity] = {}
        self._by_type: dict[EntityType, set[str]] = defaultdict(set)
        
    @property
    def node_count(self) -> int:
        """Number of entities in the graph."""
        return len(self._entities)
    
    @property
    def edge_count(self) -> int:
        """Number of relationships in the graph."""
        return self._graph.number_of_edges()
    
    def add_entity(self, entity: BaseEntity) -> None:
        """
        Add or update an entity in the graph.
        
        Args:
            entity: The entity to add
        """
        self._entities[entity.id] = entity
        self._by_type[entity.entity_type].add(entity.id)
        self._graph.add_node(entity.id, entity_type=entity.entity_type.value)
        logger.debug(f"Added entity: {entity.entity_type.value}/{entity.id}")
    
    def get_entity(self, entity_id: str) -> Optional[BaseEntity]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            The entity or None if not found
        """
        return self._entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> list[BaseEntity]:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: The type of entities to retrieve
            
        Returns:
            List of entities
        """
        return [
            self._entities[eid] 
            for eid in self._by_type.get(entity_type, set())
            if eid in self._entities
        ]
    
    def add_relation(self, relation: Relation) -> None:
        """
        Add a relationship between two entities.
        
        Args:
            relation: The relationship to add
        """
        if relation.source_id not in self._entities:
            logger.warning(f"Source entity not found: {relation.source_id}")
            return
        if relation.target_id not in self._entities:
            logger.warning(f"Target entity not found: {relation.target_id}")
            return
            
        self._graph.add_edge(
            relation.source_id,
            relation.target_id,
            relation_type=relation.relation_type.value,
            **relation.metadata,
        )
        logger.debug(
            f"Added relation: {relation.source_id} --[{relation.relation_type.value}]--> "
            f"{relation.target_id}"
        )
    
    def get_relations(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
    ) -> list[Relation]:
        """
        Query relationships with optional filters.
        
        Args:
            source_id: Filter by source entity
            target_id: Filter by target entity
            relation_type: Filter by relationship type
            
        Returns:
            List of matching relationships
        """
        relations = []
        
        if source_id:
            edges = self._graph.out_edges(source_id, data=True)
        elif target_id:
            edges = self._graph.in_edges(target_id, data=True)
        else:
            edges = self._graph.edges(data=True)
        
        for edge in edges:
            if len(edge) == 3:
                src, tgt, data = edge
            else:
                continue
                
            if source_id and src != source_id:
                continue
            if target_id and tgt != target_id:
                continue
                
            edge_type = data.get("relation_type")
            # Handle relation_type being either enum or string
            rel_type_str = relation_type.value if hasattr(relation_type, 'value') else str(relation_type) if relation_type else None
            if rel_type_str and edge_type != rel_type_str:
                continue
            
            metadata = {k: v for k, v in data.items() if k != "relation_type"}
            relations.append(Relation(
                source_id=src,
                target_id=tgt,
                relation_type=RelationType(edge_type),
                metadata=metadata,
            ))
        
        return relations
    
    def get_related_entities(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "outgoing",
    ) -> list[BaseEntity]:
        """
        Get entities related to a given entity.
        
        Args:
            entity_id: The source entity ID
            relation_type: Optional filter by relationship type
            direction: 'outgoing', 'incoming', or 'both'
            
        Returns:
            List of related entities
        """
        related_ids = set()
        
        if direction in ("outgoing", "both"):
            for relation in self.get_relations(source_id=entity_id, relation_type=relation_type):
                related_ids.add(relation.target_id)
                
        if direction in ("incoming", "both"):
            for relation in self.get_relations(target_id=entity_id, relation_type=relation_type):
                related_ids.add(relation.source_id)
        
        return [self._entities[rid] for rid in related_ids if rid in self._entities]
    
    def get_services(self) -> list[Service]:
        """Get all services in the graph."""
        return [e for e in self.get_entities_by_type(EntityType.SERVICE) if isinstance(e, Service)]
    
    def get_domains(self) -> list[Domain]:
        """Get all domains in the graph."""
        return [e for e in self.get_entities_by_type(EntityType.DOMAIN) if isinstance(e, Domain)]
    
    def get_service_apis(self, service_id: str) -> list[API]:
        """Get all APIs exposed by a service."""
        return [
            e for e in self.get_related_entities(service_id, RelationType.EXPOSES)
            if isinstance(e, API)
        ]
    
    def get_domain_services(self, domain_id: str) -> list[Service]:
        """Get all services belonging to a domain."""
        return [
            e for e in self.get_related_entities(domain_id, RelationType.CONTAINS, "incoming")
            if isinstance(e, Service)
        ]
    
    def get_service_dependencies(self, service_id: str) -> list[Service]:
        """Get services that a given service depends on."""
        return [
            e for e in self.get_related_entities(service_id, RelationType.DEPENDS_ON)
            if isinstance(e, Service)
        ]
    
    def get_service_dependents(self, service_id: str) -> list[Service]:
        """Get services that depend on a given service."""
        return [
            e for e in self.get_related_entities(service_id, RelationType.DEPENDS_ON, "incoming")
            if isinstance(e, Service)
        ]
    
    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
    ) -> list[list[str]]:
        """
        Find all paths between two entities.
        
        Args:
            source_id: Starting entity ID
            target_id: Ending entity ID
            max_length: Maximum path length
            
        Returns:
            List of paths (each path is a list of entity IDs)
        """
        try:
            paths = list(nx.all_simple_paths(
                self._graph, source_id, target_id, cutoff=max_length
            ))
            return paths
        except nx.NetworkXError:
            return []
    
    def get_subgraph(self, entity_ids: list[str]) -> "KnowledgeGraph":
        """
        Create a subgraph containing only the specified entities.
        
        Args:
            entity_ids: List of entity IDs to include
            
        Returns:
            New KnowledgeGraph with only the specified entities
        """
        subgraph = KnowledgeGraph()
        
        for eid in entity_ids:
            if eid in self._entities:
                subgraph.add_entity(self._entities[eid])
        
        # Add edges between included entities
        for src, tgt, data in self._graph.edges(data=True):
            if src in entity_ids and tgt in entity_ids:
                relation = Relation(
                    source_id=src,
                    target_id=tgt,
                    relation_type=RelationType(data["relation_type"]),
                    metadata={k: v for k, v in data.items() if k != "relation_type"},
                )
                subgraph.add_relation(relation)
        
        return subgraph
    
    def merge(self, other: "KnowledgeGraph") -> None:
        """
        Merge another knowledge graph into this one.
        
        Entities with the same ID are updated with the newer version.
        
        Args:
            other: The graph to merge in
        """
        for entity in other._entities.values():
            existing = self._entities.get(entity.id)
            if existing is None or entity.updated_at > existing.updated_at:
                self.add_entity(entity)
        
        # Merge relations
        for src, tgt, data in other._graph.edges(data=True):
            if not self._graph.has_edge(src, tgt):
                relation = Relation(
                    source_id=src,
                    target_id=tgt,
                    relation_type=RelationType(data["relation_type"]),
                    metadata={k: v for k, v in data.items() if k != "relation_type"},
                )
                self.add_relation(relation)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the graph to a dictionary.
        
        Returns:
            Dictionary representation of the graph
        """
        entities = [entity.to_dict() for entity in self._entities.values()]
        relations = []
        
        for src, tgt, data in self._graph.edges(data=True):
            relations.append({
                "source_id": src,
                "target_id": tgt,
                "relation_type": data["relation_type"],
                "metadata": {k: v for k, v in data.items() if k != "relation_type"},
            })
        
        return {
            "entities": entities,
            "relations": relations,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeGraph":
        """
        Deserialize a graph from a dictionary.
        
        Args:
            data: Dictionary representation of the graph
            
        Returns:
            New KnowledgeGraph instance
        """
        graph = cls()
        
        for entity_data in data.get("entities", []):
            entity = entity_from_dict(entity_data)
            graph.add_entity(entity)
        
        for relation_data in data.get("relations", []):
            relation = Relation(
                source_id=relation_data["source_id"],
                target_id=relation_data["target_id"],
                relation_type=RelationType(relation_data["relation_type"]),
                metadata=relation_data.get("metadata", {}),
            )
            graph.add_relation(relation)
        
        return graph
    
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the knowledge graph."""
        type_counts = {
            entity_type.value: len(ids) 
            for entity_type, ids in self._by_type.items()
        }
        
        return {
            "total_entities": self.node_count,
            "total_relations": self.edge_count,
            "entities_by_type": type_counts,
            "connected_components": nx.number_weakly_connected_components(self._graph),
        }
    
    def __repr__(self) -> str:
        return f"KnowledgeGraph(nodes={self.node_count}, edges={self.edge_count})"
