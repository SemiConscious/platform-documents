"""Persistent storage for knowledge graph and document registry."""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import aiofiles

from .graph import KnowledgeGraph
from .models import BaseEntity

logger = logging.getLogger("doc-agent.knowledge.store")


class DocumentRecord(dict):
    """Record tracking a generated document."""
    
    @property
    def path(self) -> str:
        return self.get("path", "")
    
    @property
    def source_hash(self) -> str:
        return self.get("source_hash", "")
    
    @property
    def generated_at(self) -> Optional[datetime]:
        ts = self.get("generated_at")
        if ts:
            return datetime.fromisoformat(ts)
        return None
    
    @property
    def agent_version(self) -> str:
        return self.get("agent_version", "")
    
    @property
    def entity_ids(self) -> list[str]:
        return self.get("entity_ids", [])


class KnowledgeStore:
    """
    Persistent storage for the knowledge graph and document registry.
    
    Provides:
    - Knowledge graph persistence with JSON serialization
    - Document registry for tracking generated documents
    - Change detection via content hashing
    - Incremental update support
    """
    
    def __init__(self, store_dir: Path):
        """
        Initialize the knowledge store.
        
        Args:
            store_dir: Directory for storing persistent data
        """
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        
        self.graph_path = self.store_dir / "knowledge-graph.json"
        self.registry_path = self.store_dir / "document-registry.json"
        self.checkpoints_dir = self.store_dir / "agent-checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        self._graph: Optional[KnowledgeGraph] = None
        self._registry: dict[str, DocumentRecord] = {}
        
    async def load(self) -> None:
        """Load the knowledge graph and document registry from disk."""
        await self._load_graph()
        await self._load_registry()
        logger.info(f"Loaded store: {self._graph.node_count} entities, {len(self._registry)} documents")
    
    async def _load_graph(self) -> None:
        """Load the knowledge graph from disk."""
        if self.graph_path.exists():
            try:
                async with aiofiles.open(self.graph_path, "r") as f:
                    data = json.loads(await f.read())
                self._graph = KnowledgeGraph.from_dict(data)
                logger.debug(f"Loaded knowledge graph with {self._graph.node_count} entities")
            except Exception as e:
                logger.warning(f"Failed to load knowledge graph: {e}")
                self._graph = KnowledgeGraph()
        else:
            self._graph = KnowledgeGraph()
    
    async def _load_registry(self) -> None:
        """Load the document registry from disk."""
        if self.registry_path.exists():
            try:
                async with aiofiles.open(self.registry_path, "r") as f:
                    data = json.loads(await f.read())
                self._registry = {
                    path: DocumentRecord(record) 
                    for path, record in data.items()
                }
                logger.debug(f"Loaded document registry with {len(self._registry)} entries")
            except Exception as e:
                logger.warning(f"Failed to load document registry: {e}")
                self._registry = {}
        else:
            self._registry = {}
    
    async def save(self) -> None:
        """Save the knowledge graph and document registry to disk."""
        await self._save_graph()
        await self._save_registry()
        logger.info("Saved knowledge store")
    
    async def _save_graph(self) -> None:
        """Save the knowledge graph to disk."""
        if self._graph:
            data = self._graph.to_dict()
            async with aiofiles.open(self.graph_path, "w") as f:
                await f.write(json.dumps(data, indent=2, default=str))
    
    async def _save_registry(self) -> None:
        """Save the document registry to disk."""
        async with aiofiles.open(self.registry_path, "w") as f:
            await f.write(json.dumps(self._registry, indent=2, default=str))
    
    @property
    def graph(self) -> KnowledgeGraph:
        """Get the knowledge graph, initializing if needed."""
        if self._graph is None:
            self._graph = KnowledgeGraph()
        return self._graph
    
    def register_document(
        self,
        path: str,
        source_hash: str,
        entity_ids: list[str],
        agent_version: str = "0.1.0",
    ) -> None:
        """
        Register a generated document in the registry.
        
        Args:
            path: Path to the generated document
            source_hash: Hash of the source data used to generate it
            entity_ids: IDs of entities documented
            agent_version: Version of the agent that generated it
        """
        self._registry[path] = DocumentRecord({
            "path": path,
            "source_hash": source_hash,
            "generated_at": datetime.utcnow().isoformat(),
            "agent_version": agent_version,
            "entity_ids": entity_ids,
        })
    
    def get_document_record(self, path: str) -> Optional[DocumentRecord]:
        """Get the record for a generated document."""
        return self._registry.get(path)
    
    def needs_regeneration(self, path: str, current_hash: str) -> bool:
        """
        Check if a document needs to be regenerated.
        
        Args:
            path: Path to the document
            current_hash: Hash of the current source data
            
        Returns:
            True if the document needs regeneration
        """
        record = self._registry.get(path)
        if record is None:
            return True
        return record.source_hash != current_hash
    
    def get_all_document_paths(self) -> list[str]:
        """Get all registered document paths."""
        return list(self._registry.keys())
    
    def get_documents_for_entity(self, entity_id: str) -> list[str]:
        """Get all documents that reference a specific entity."""
        return [
            path for path, record in self._registry.items()
            if entity_id in record.entity_ids
        ]
    
    async def save_checkpoint(self, agent_name: str, data: dict[str, Any]) -> None:
        """
        Save a checkpoint for an agent.
        
        Args:
            agent_name: Name of the agent
            data: Checkpoint data
        """
        checkpoint_path = self.checkpoints_dir / f"{agent_name}.json"
        async with aiofiles.open(checkpoint_path, "w") as f:
            await f.write(json.dumps({
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }, indent=2, default=str))
    
    async def load_checkpoint(self, agent_name: str) -> Optional[dict[str, Any]]:
        """
        Load a checkpoint for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Checkpoint data or None
        """
        checkpoint_path = self.checkpoints_dir / f"{agent_name}.json"
        if checkpoint_path.exists():
            try:
                async with aiofiles.open(checkpoint_path, "r") as f:
                    data = json.loads(await f.read())
                return data.get("data")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint for {agent_name}: {e}")
        return None
    
    async def clear_checkpoint(self, agent_name: str) -> None:
        """Clear a checkpoint for an agent."""
        checkpoint_path = self.checkpoints_dir / f"{agent_name}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
    
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the store."""
        return {
            "graph": self.graph.get_statistics() if self._graph else {},
            "documents": {
                "total": len(self._registry),
                "by_status": self._count_documents_by_status(),
            },
        }
    
    def _count_documents_by_status(self) -> dict[str, int]:
        """Count documents by their status based on age."""
        now = datetime.utcnow()
        counts = {"recent": 0, "stale": 0}
        
        for record in self._registry.values():
            if record.generated_at:
                age = now - record.generated_at
                if age.days < 7:
                    counts["recent"] += 1
                else:
                    counts["stale"] += 1
        
        return counts


def compute_content_hash(content: str) -> str:
    """Compute a hash for content to detect changes."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def compute_entity_hash(entities: list[BaseEntity]) -> str:
    """Compute a hash for a list of entities to detect changes."""
    content = json.dumps(
        [e.to_dict() for e in sorted(entities, key=lambda e: e.id)],
        sort_keys=True,
        default=str,
    )
    return compute_content_hash(content)
